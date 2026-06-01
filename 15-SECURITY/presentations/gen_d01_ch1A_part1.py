#!/usr/bin/env python3
"""
Domain 1 · Chapter 1A · Part 1 — ELF Structure, Loading & Dynamic Linking
≈90 slides · Reference-grade density
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from presentation_engine import PresentationEngine, C, mpl_theme, chart_to_image
from html_engine import HTMLPresentation
from pptx.util import Inches, Pt
import matplotlib.pyplot as plt
import numpy as np

OUT_DIR = os.path.dirname(__file__)

def gen_pptx():
    pe = PresentationEngine()

    # ─── 1  Title ──────────────────────────────────────────────────
    pe.title_slide(
        "ELF Foundations &\nDynamic Linking Core",
        "File Header · Program Headers · Segments · Sections · Kernel→Loader Handoff\n"
        ".dynamic · .dynsym · Hash Tables · Relocations · GOT/PLT · Lazy Binding",
        domain="DOMAIN 1 — BINARY FORMATS",
        chapter="Chapter 1A · Part 1 of 2 · ELF Structure & Loading"
    )

    # ─── 2  Agenda ─────────────────────────────────────────────────
    pe.agenda_slide([
        "ELF Dual-View Architecture (Sections vs Segments)",
        "The ELF File Header (Elf64_Ehdr) — Every Field Explained",
        "Program Headers & Segment Types (PT_LOAD → PT_GNU_PROPERTY)",
        "Section Headers & Link-Time Semantics",
        "Kernel→Loader Handoff & Auxiliary Vector",
        "The Dynamic Linker (ld.so) Boot Sequence",
        "The .dynamic Section — Table of Contents",
        "Symbol Tables (.dynsym) & String Tables (.dynstr)",
        "Hash Tables: SysV .hash vs GNU .gnu.hash",
        "Relocation Types on x86_64",
        "The Two GOTs: .got vs .got.plt",
        "The PLT & Lazy Binding Mechanism",
        "Symbol Resolution Scope & Order",
        "Why Lazy Binding Is Dying: Full RELRO",
        "Complete ELF Load Sequence Timeline",
    ])

    # ─── 3  Overview Stats ────────────────────────────────────────
    pe.stats_slide("ELF Format at a Glance", [
        ("64 B", "ELF Header Size (64-bit)", C.CYAN),
        ("56 B", "Program Header Entry Size", C.GREEN),
        ("64 B", "Section Header Entry Size", C.YELLOW),
        ("24 B", "Symbol Table Entry Size", C.PURPLE),
        ("24 B", "Relocation Entry Size (Rela)", C.RED),
        ("4", "Typical PT_LOAD Segments", C.ORANGE),
        ("16 B", "Elf64_Dyn Entry Size", C.TEAL),
        ("0x7F454C46", "ELF Magic Number", C.MAGENTA),
    ])

    # ─── 4  Section: Dual View ────────────────────────────────────
    pe.section_slide("The Dual-View Architecture", 1,
        "Same bytes, two descriptions — the fundamental ELF asymmetry")

    # ─── 5  Sections vs Segments ──────────────────────────────────
    pe.comparison_slide(
        "Sections vs Segments — Two Views of One Binary",
        "Section Headers (Linker View)", [
            "Describe what ld needs to combine .o files",
            "Can be stripped/zeroed — binary still runs",
            "Carry symbol names, debug info, exception tables",
            "Organize content by purpose: .text, .data, .bss, .rodata",
            "sh_flags: SHF_ALLOC, SHF_WRITE, SHF_EXECINSTR",
            "Indexed by e_shoff/e_shnum from ELF header",
            "Not consulted by kernel binfmt_elf at all",
            "Tools relying only on sections are trivially fooled",
            "Section 0 is always the NULL section (reserved)",
        ],
        "Program Headers (Loader View)", [
            "Describe what kernel/ld.so needs to mmap & execute",
            "Cannot be removed — binary won't load without them",
            "Define memory regions with permissions (R/W/X)",
            "Organize content by runtime behavior: LOAD, DYNAMIC, INTERP",
            "p_flags: PF_R, PF_W, PF_X (page permissions)",
            "Indexed by e_phoff/e_phnum from ELF header",
            "The ONLY thing the kernel reads for execution",
            "Load-bearing for execution — everything runs through segments",
            "A byte may belong to 1 segment and 0+ sections",
        ],
        left_color=C.YELLOW, right_color=C.CYAN, vs_text="≠"
    )

    # ─── 6  Mental Model Diagram ─────────────────────────────────
    pe.diagram_layers_slide(
        "ELF Dual-View Mental Model", [
            ("ELF File Header (Elf64_Ehdr)", C.CYAN,
             "Entry point to both views: e_phoff → segments, e_shoff → sections"),
            ("Program Header Table", C.GREEN,
             "Array of Elf64_Phdr — kernel reads ONLY this for execution"),
            ("PT_LOAD Segment 1 (R-X)", C.BLUE,
             "Contains .text, .plt, .init, .fini — executable code"),
            ("PT_LOAD Segment 2 (R--)", C.TEAL,
             "Contains .rodata, .eh_frame, .gcc_except_table"),
            ("PT_LOAD Segment 3 (RW- → R-- after RELRO)", C.YELLOW,
             "Contains .dynamic, .got, .data.rel.ro — RELRO region"),
            ("PT_LOAD Segment 4 (RW-)", C.RED,
             "Contains .data, .got.plt, .bss — writable data"),
            ("Section Header Table", C.PURPLE,
             "Array of Elf64_Shdr — optional, analysis-time only"),
        ],
        sub_heading="Segments are what runs; sections are what the linker arranged for segments to contain"
    )

    # ─── 7  Security Implication ─────────────────────────────────
    pe.warning_slide("Security Implications of the Dual-View Design", [
        ("critical", "Section headers can be stripped/forged — tools relying only on sections are trivially fooled"),
        ("high", "YARA rules matching section names miss binaries with stripped section tables"),
        ("high", "Packers routinely zero e_shoff to frustrate disassemblers like IDA/Ghidra"),
        ("medium", "Section names can lie: a section named .text can contain writable data"),
        ("medium", "Overlapping sections (same file offset, different attributes) confuse analysis tools"),
        ("info", "Detection strategy: always validate program headers first, sections second"),
        ("info", "If program headers and section headers disagree, trust program headers"),
    ])

    # ─── 8  Section: ELF Header ──────────────────────────────────
    pe.section_slide("The ELF File Header", 2,
        "Elf64_Ehdr — 64 bytes that define everything about the binary's structure")

    # ─── 9  Ehdr Structure Code ──────────────────────────────────
    pe.code_slide("Elf64_Ehdr — The ELF File Header Structure", """typedef struct {
    unsigned char e_ident[16];   // Magic + class + endian + OS/ABI
    Elf64_Half    e_type;        // ET_REL(1) | ET_EXEC(2) | ET_DYN(3) | ET_CORE(4)
    Elf64_Half    e_machine;     // EM_X86_64(62) | EM_AARCH64(183) | ...
    Elf64_Word    e_version;     // EV_CURRENT(1)
    Elf64_Addr    e_entry;       // Virtual address of entry point
    Elf64_Off     e_phoff;       // Program header table file offset
    Elf64_Off     e_shoff;       // Section header table file offset
    Elf64_Word    e_flags;       // Processor-specific flags
    Elf64_Half    e_ehsize;      // Size of this header: 64 for ELF64
    Elf64_Half    e_phentsize;   // Size of one phdr entry: 56 for ELF64
    Elf64_Half    e_phnum;       // Number of program header entries
    Elf64_Half    e_shentsize;   // Size of one shdr entry: 64 for ELF64
    Elf64_Half    e_shnum;       // Number of section header entries
    Elf64_Half    e_shstrndx;    // Section name string table index
} Elf64_Ehdr;""", language="C (elf.h)", notes=[
        "First 16 bytes (e_ident): 0x7F 'E' 'L' 'F' + class/endian/version/OS-ABI",
        "e_type ET_DYN is ambiguous: shared objects AND PIE executables are both ET_DYN",
        "e_entry for PIE: offset from load base (not absolute VA) — kernel adds ASLR base",
    ])

    # ─── 10  e_ident breakdown ───────────────────────────────────
    pe.table_slide("e_ident[16] — Magic Identification Array", [
        "Offset", "Name", "Size", "Value", "Purpose"
    ], [
        ["0-3", "EI_MAG0-3", "4B", "0x7F 'E' 'L' 'F'", "ELF magic number"],
        ["4", "EI_CLASS", "1B", "1=32-bit, 2=64-bit", "Address size class"],
        ["5", "EI_DATA", "1B", "1=LSB, 2=MSB", "Byte order (endianness)"],
        ["6", "EI_VERSION", "1B", "1 (EV_CURRENT)", "ELF version (always 1)"],
        ["7", "EI_OSABI", "1B", "0=NONE, 3=GNU", "Target OS/ABI"],
        ["8", "EI_ABIVERSION", "1B", "0 (normally)", "ABI version"],
        ["9-15", "EI_PAD", "7B", "0x00...", "Padding — can hide data!"],
    ], sub_heading="The first 16 bytes of every ELF file")

    # ─── 11  e_type ambiguity ────────────────────────────────────
    pe.content_slide_rich("e_type — The ET_DYN Ambiguity Problem", [
        (C.CYAN, "ET_REL (1) — Relocatable Object (.o)",
         "Produced by compiler. Contains unresolved symbols. Input to the linker, never executed directly."),
        (C.GREEN, "ET_EXEC (2) — Fixed-Address Executable",
         "Traditional non-PIE executable. Absolute virtual addresses. No ASLR for binary base. Legacy."),
        (C.YELLOW, "ET_DYN (3) — Shared Object OR PIE Executable",
         "AMBIGUOUS: both .so libraries and PIE executables use ET_DYN. Distinguishable only by: "
         "presence of PT_INTERP, DT_FLAGS_1 containing DF_1_PIE, or non-empty e_entry."),
        (C.RED, "ET_CORE (4) — Core Dump",
         "Produced by kernel on crash. Contains PT_LOAD segments with process memory. "
         "Used for post-mortem analysis and malware unpacking (gcore)."),
    ], sub_heading="Why PIE and .so are the same e_type — and how to tell them apart")

    # ─── 12  e_phnum overflow ────────────────────────────────────
    pe.content_slide_rich("Extended Number Encoding — Overflow Workarounds", [
        (C.CYAN, "e_phnum Overflow (PN_XNUM = 0xFFFF)",
         "When e_phnum == 0xFFFF, real count is in sh_info of section header 0. "
         "16-bit field limit: max 65534 program headers directly."),
        (C.GREEN, "e_shnum Overflow",
         "When e_shnum == 0 with non-zero e_shoff, real section count is in sh_size of section header 0."),
        (C.YELLOW, "e_shstrndx Overflow (SHN_XINDEX = 0xFFFF)",
         "When e_shstrndx == 0xFFFF, real string table section index is in sh_link of section header 0."),
        (C.RED, "Detection Implication",
         "Anomalous values in these fields can be used to confuse analysis tools that don't handle "
         "the extended encoding. Malware sometimes sets these to invalid values deliberately."),
    ], sub_heading="How ELF handles more than 65534 sections or program headers")

    # ─── 13  Header anomaly detection ────────────────────────────
    pe.definition_slide("ELF Header Anomaly Detection Signals", [
        ("e_shoff = 0", "No section headers — binary still runs but loses analyzability. Strong anomaly signal.", C.RED),
        ("e_phentsize ≠ 56", "Invalid program header entry size for 64-bit (should always be 56 bytes).", C.ORANGE),
        ("e_ehsize ≠ 64", "Invalid ELF header size for 64-bit (should always be 64 bytes).", C.YELLOW),
        ("e_ident[9-15] ≠ 0", "Non-zero padding bytes — potential data smuggling in unused header space.", C.PURPLE),
        ("e_entry → non-X seg", "Entry point pointing into a non-executable segment — post-link modification.", C.RED),
        ("e_phoff unusual", "Program header table not at offset 64 — custom or modified linker output.", C.CYAN),
        ("e_type = ET_DYN", "Inspect further: is this a PIE (has PT_INTERP) or a shared library?", C.GREEN),
        ("Missing PT_NOTE", "If build-ID section exists but PT_NOTE is gone — possible PT_NOTE→PT_LOAD infection.", C.MAGENTA),
    ])

    # ─── 14  Section: Program Headers ─────────────────────────────
    pe.section_slide("Program Headers &\nSegment Loading", 3,
        "Elf64_Phdr — the kernel's instruction manual for building a process image")

    # ─── 15  Phdr structure ──────────────────────────────────────
    pe.code_slide("Elf64_Phdr — Program Header Structure", """typedef struct {
    Elf64_Word  p_type;     // PT_LOAD | PT_DYNAMIC | PT_INTERP | ...
    Elf64_Word  p_flags;    // PF_R(4) | PF_W(2) | PF_X(1)
    Elf64_Off   p_offset;   // File offset of segment data
    Elf64_Addr  p_vaddr;    // Virtual address in memory (+ base for PIE)
    Elf64_Addr  p_paddr;    // Physical address (ignored on Linux userspace)
    Elf64_Xword p_filesz;   // Size of segment data in file
    Elf64_Xword p_memsz;    // Size in memory (>= p_filesz; excess is BSS)
    Elf64_Xword p_align;    // Alignment (page-aligned for PT_LOAD)
} Elf64_Phdr;""", language="C (elf.h)", notes=[
        "p_memsz - p_filesz = BSS region (zero-filled, takes memory but no file space)",
        "p_flags maps to mmap permissions: PF_R→PROT_READ, PF_W→PROT_WRITE, PF_X→PROT_EXEC",
        "For PIE (ET_DYN): p_vaddr is offset from load base, not absolute address",
    ])

    # ─── 16  PT_LOAD deep dive ───────────────────────────────────
    pe.diagram_flow_slide(
        "PT_LOAD Segment Loading — File → Memory Mapping",
        [("Kernel reads\np_offset, p_filesz", C.CYAN),
         ("mmap at p_vaddr\n(+ ASLR base)", C.GREEN),
         ("Set permissions\nfrom p_flags", C.YELLOW),
         ("Zero-fill BSS\n(memsz - filesz)", C.RED),
         ("Segment\nready", C.PURPLE)],
        sub_heading="A modern binary typically has 4 PT_LOAD segments with distinct permissions"
    )

    # ─── 17  4 PT_LOAD segments ──────────────────────────────────
    pe.table_slide("Modern 4-Segment Layout (Post-Hardening Linker)", [
        "Segment", "Permissions", "Contents", "Security Role"
    ], [
        ["PT_LOAD #1", "R-- (read-only)", ".note, .gnu.hash, .dynsym, .dynstr, .rela.dyn", "Headers & metadata"],
        ["PT_LOAD #2", "R-X (exec)", ".text, .plt, .plt.got, .plt.sec, .init, .fini", "Executable code"],
        ["PT_LOAD #3", "R-- (after RELRO)", ".dynamic, .got, .data.rel.ro, .init_array, .fini_array", "RELRO-protected data"],
        ["PT_LOAD #4", "RW- (writable)", ".data, .got.plt, .bss", "Writable data + lazy GOT"],
    ], sub_heading="The 4-segment split enables RELRO: segment 3 is mprotect'd read-only after relocation")

    # ─── 18  All segment types ───────────────────────────────────
    pe.table_slide("Complete Program Header Type Reference", [
        "p_type", "Value", "Purpose", "Security Relevance"
    ], [
        ["PT_LOAD", "1", "Map file region into memory", "RWX check: both W+X is anomalous"],
        ["PT_DYNAMIC", "2", "Points to .dynamic array", "Mandatory for dynamic linking"],
        ["PT_INTERP", "3", "Path to dynamic linker", "Absent = static binary (no LD_PRELOAD)"],
        ["PT_NOTE", "4", "Build ID, ABI tags, CET/BTI", "Target of PT_NOTE→PT_LOAD infection"],
        ["PT_PHDR", "6", "Self-describes phdr table", "Used by ld.so to find own headers"],
        ["PT_TLS", "7", "Thread-local storage template", "Per-thread .tdata/.tbss init image"],
        ["PT_GNU_STACK", "0x6474e551", "Stack permissions", "PF_X = executable stack (anomalous)"],
        ["PT_GNU_RELRO", "0x6474e552", "RELRO region bounds", "mprotect'd R-- after relocation"],
        ["PT_GNU_EH_FRAME", "0x6474e550", "Unwind table index", "Points to .eh_frame_hdr"],
        ["PT_GNU_PROPERTY", "0x6474e553", "CET/BTI/PAC properties", "Enables HW control-flow integrity"],
    ])

    # ─── 19  W^X Check ───────────────────────────────────────────
    pe.warning_slide("W^X Violation: PF_W + PF_X on PT_LOAD", [
        ("critical", "A static PT_LOAD with both PF_W and PF_X = writable AND executable code"),
        ("high", "Almost always indicates: packer, JIT self-modification, or malicious binary"),
        ("high", "Normal compiled binaries NEVER have W+X segments statically"),
        ("medium", "Cheap detection: iterate PT_LOAD entries, flag any with (p_flags & 3) == 3"),
        ("info", "Legitimate exception: JIT engines (V8, LuaJIT) create RWX pages at runtime via mmap"),
        ("info", "Static W^X check should be in every binary intake pipeline"),
    ])

    # ─── 20  PT_GNU_STACK ────────────────────────────────────────
    pe.two_column_slide(
        "PT_GNU_STACK — Executable Stack Detection",
        "Executable Stack (PF_X set)", [
            "Kernel allocates stack with PROT_EXEC",
            "Enables classic stack-based shellcode execution",
            "Caused by: old assembly without .note.GNU-stack",
            "Caused by: -z execstack linker flag",
            "Some legacy JITs require it",
            "Almost always anomalous in modern binaries",
            "Detection: readelf -l | grep GNU_STACK | check flags",
        ],
        "Non-Executable Stack (no PF_X)", [
            "Kernel allocates stack with PROT_READ|PROT_WRITE only",
            "CPU hardware enforces NX (Intel: XD bit, AMD: NX bit)",
            "Blocks trivial stack-based code execution",
            "Attacker must use code-reuse (ROP/JOP) instead",
            "Default on all modern Linux toolchains",
            "Requires: all linked objects to have .note.GNU-stack",
            "One missing .note.GNU-stack → entire binary gets exec stack",
        ],
        left_color=C.RED, right_color=C.GREEN
    )

    # ─── 21  Section: Section Headers ─────────────────────────────
    pe.section_slide("Section Headers &\nLink-Time Semantics", 4,
        "Elf64_Shdr — organizing content for the linker, debugger, and analyst")

    # ─── 22  Shdr structure ──────────────────────────────────────
    pe.code_slide("Elf64_Shdr — Section Header Structure", """typedef struct {
    Elf64_Word  sh_name;       // Index into section name string table
    Elf64_Word  sh_type;       // SHT_PROGBITS | SHT_SYMTAB | SHT_RELA | ...
    Elf64_Xword sh_flags;      // SHF_ALLOC | SHF_WRITE | SHF_EXECINSTR | ...
    Elf64_Addr  sh_addr;       // Virtual address if SHF_ALLOC
    Elf64_Off   sh_offset;     // File offset
    Elf64_Xword sh_size;       // Section size in bytes
    Elf64_Word  sh_link;       // Type-dependent link (e.g., strtab index)
    Elf64_Word  sh_info;       // Type-dependent info (e.g., last local sym)
    Elf64_Xword sh_addralign;  // Alignment constraint
    Elf64_Xword sh_entsize;    // Entry size for fixed-size tables
} Elf64_Shdr;""", language="C (elf.h)", notes=[
        "sh_link/sh_info meaning changes per sh_type (symtab→strtab, rela→target section)",
        "SHF_ALLOC = section occupies memory at runtime (contained in a PT_LOAD segment)",
        "Section 0 is always NULL (reserved) — sh_info/sh_size/sh_link used for overflow encoding",
    ])

    # ─── 23  sh_flags breakdown ──────────────────────────────────
    pe.definition_slide("Section Flags (sh_flags) — Permission & Behavior Bits", [
        ("SHF_ALLOC", "Section occupies memory at runtime (inside a PT_LOAD segment)", C.CYAN),
        ("SHF_WRITE", "Section is writable at runtime (maps to PF_W)", C.GREEN),
        ("SHF_EXECINSTR", "Section contains executable instructions (maps to PF_X)", C.YELLOW),
        ("SHF_MERGE", "Entries can be merged/deduplicated by linker (string pooling)", C.PURPLE),
        ("SHF_STRINGS", "Section contains NUL-terminated strings (enables dedup)", C.BLUE),
        ("SHF_TLS", "Section holds thread-local storage (.tdata/.tbss)", C.ORANGE),
        ("SHF_GROUP", "Section belongs to a COMDAT group (C++ ODR compliance)", C.MAGENTA),
        ("SHF_COMPRESSED", "Section data is compressed (ELFCOMPRESS_ZLIB)", C.TEAL),
    ])

    # ─── 24  sh_link/sh_info semantics ───────────────────────────
    pe.table_slide("sh_link and sh_info — Context-Dependent Semantics", [
        "sh_type", "sh_link meaning", "sh_info meaning"
    ], [
        ["SHT_SYMTAB / SHT_DYNSYM", "Index of associated string table", "Index of first non-local symbol"],
        ["SHT_REL / SHT_RELA", "Index of associated symbol table", "Index of section being relocated"],
        ["SHT_HASH / SHT_GNU_HASH", "Index of symbol table being indexed", "(unused)"],
        ["SHT_DYNAMIC", "Index of string table for DT entries", "(unused)"],
        ["SHT_GROUP", "Index of associated symbol table", "Symbol table index of group signature"],
        ["SHT_SYMTAB_SHNDX", "Index of associated symbol table", "(unused)"],
    ], sub_heading="The same fields carry different information depending on section type")

    # ─── 25  Special section indices ─────────────────────────────
    pe.definition_slide("Special Section Indices (SHN_*)", [
        ("SHN_UNDEF (0)", "Symbol not defined in this object — must be resolved by linker/loader", C.RED),
        ("SHN_ABS (0xFFF1)", "Symbol value is absolute, not relative to any section (e.g., __bss_start)", C.CYAN),
        ("SHN_COMMON (0xFFF2)", "Tentative definition — C 'common' semantic, allocated by linker", C.YELLOW),
        ("SHN_XINDEX (0xFFFF)", "Real index exceeds 16 bits — look in SHT_SYMTAB_SHNDX section", C.PURPLE),
    ])

    # ─── 26  Runtime relevance ───────────────────────────────────
    pe.content_slide("Which Sections Matter at Runtime?",
        ["A section is 'interesting at runtime' exactly when sh_flags includes SHF_ALLOC",
         "Runtime sections: .text, .rodata, .data, .bss, .got, .got.plt, .plt, .dynamic, .dynsym, .dynstr",
         "Analysis-only sections: .symtab, .strtab, .debug_*, .comment, .shstrtab",
         "Stripping removes analysis-only sections; binary functionality is unchanged",
         "'strip --strip-all' removes .symtab + debug sections but keeps .dynsym (needed at runtime)",
         "'strip --strip-unneeded' is more conservative — keeps symbols referenced by relocations",
         "A fully stripped binary with no section headers is still fully functional",
         "Detection engineers: always check SHF_ALLOC to separate runtime from metadata sections",
        ],
        sub_heading="SHF_ALLOC is the dividing line between runtime and analysis-time sections")

    # ─── 27  Section: Kernel Handoff ──────────────────────────────
    pe.section_slide("Kernel → Loader Handoff", 5,
        "From execve() to the first userspace instruction — the auxiliary vector bridge")

    # ─── 28  Kernel loading process flow ─────────────────────────
    pe.diagram_flow_slide(
        "load_elf_binary() — Kernel Loading Sequence",
        [("execve()\nsyscall", C.CYAN),
         ("Parse Ehdr\n& Phdr table", C.GREEN),
         ("mmap PT_LOAD\nsegments", C.YELLOW),
         ("Pick ASLR\nbase (PIE)", C.RED),
         ("Load PT_INTERP\n(ld.so)", C.PURPLE),
         ("Build auxv\non stack", C.ORANGE),
         ("Jump to\nld.so _start", C.TEAL)],
        sub_heading="fs/binfmt_elf.c — kernel reads ONLY program headers, never section headers"
    )

    # ─── 29  Auxiliary vector ────────────────────────────────────
    pe.table_slide("Auxiliary Vector (auxv) — Kernel → Userspace Data Channel", [
        "AT_* Tag", "Value", "Purpose", "Security Impact"
    ], [
        ["AT_PHDR", "3", "VA of program header table", "ld.so uses to find PT_DYNAMIC"],
        ["AT_PHENT", "4", "Size of one phdr entry", "Always 56 for ELF64"],
        ["AT_PHNUM", "5", "Number of phdr entries", ""],
        ["AT_BASE", "7", "Load base of ld.so itself", "Needed for self-relocation"],
        ["AT_ENTRY", "9", "Program entry point (relocated)", "Where ld.so transfers control"],
        ["AT_RANDOM", "25", "16 bytes of kernel randomness", "Seeds stack canary & libc PRNG"],
        ["AT_SYSINFO_EHDR", "33", "Address of vDSO", "Fast syscalls without kernel entry"],
        ["AT_HWCAP / AT_HWCAP2", "16/26", "CPU feature bitmask", "IFUNC resolver selection"],
        ["AT_SECURE", "23", "1 if setuid/setgid/fscaps", "Disables LD_PRELOAD, LD_LIBRARY_PATH"],
    ], sub_heading="Elf64_auxv_t { a_type, a_un.a_val } — the kernel's out-of-band channel")

    # ─── 30  AT_SECURE deep dive ─────────────────────────────────
    pe.content_slide_rich("AT_SECURE — The Linchpin of Setuid Safety", [
        (C.RED, "What AT_SECURE Does",
         "When AT_SECURE=1, the dynamic linker ignores: LD_PRELOAD, LD_LIBRARY_PATH, "
         "LD_AUDIT, LD_DEBUG, and all other dangerous environment variables."),
        (C.YELLOW, "When AT_SECURE Is Set",
         "Kernel sets AT_SECURE=1 for: setuid binaries, setgid binaries, and binaries with "
         "file capabilities (e.g., cap_net_raw). Checked in security_bprm_set_creds()."),
        (C.GREEN, "Why It Matters",
         "Without AT_SECURE, any user could LD_PRELOAD a malicious library into a setuid binary "
         "and gain root. AT_SECURE is the ONLY defense against this attack vector."),
        (C.PURPLE, "Historical Bypass: CVE-2010-3856",
         "$ORIGIN expansion in DT_RPATH bypassed AT_SECURE checks in older glibc versions, "
         "allowing LD_AUDIT code execution in setuid binaries. Fixed in glibc 2.12.2."),
        (C.CYAN, "Forensics: Reading Another Process's auxv",
         "/proc/PID/auxv exposes the auxiliary vector — reveals vDSO address, program headers, "
         "AT_RANDOM seed location. Readable by same-user processes."),
    ])

    # ─── 31  Section: Dynamic Linker ──────────────────────────────
    pe.section_slide("The Dynamic Linker\n(ld-linux.so)", 6,
        "The most privileged userspace component in an ELF process's early life")

    # ─── 32  ld.so boot sequence ─────────────────────────────────
    pe.diagram_flow_vertical_slide(
        "Dynamic Linker Boot Sequence — _dl_start → _dl_main",
        [("_start (ld.so entry point)", C.CYAN),
         ("Self-relocate via R_X86_64_RELATIVE\n(bootstrap: PC-relative, no GOT/PLT)", C.GREEN),
         ("Find program's PT_DYNAMIC\nvia AT_PHDR from auxv", C.YELLOW),
         ("Walk DT_NEEDED entries\nOpen each library via search path", C.RED),
         ("mmap each DSO's PT_LOAD segments\nat random base addresses", C.PURPLE),
         ("Resolve relocations across all objects\n(.rela.dyn eager, .rela.plt lazy/eager)", C.ORANGE),
         ("mprotect RELRO regions read-only\n(_dl_protect_relro)", C.TEAL),
         ("Run constructors in dependency order\npre-init → init → init_array", C.MAGENTA),
         ("Transfer to program e_entry\n_start → __libc_start_main → main()", C.CYAN)]
    )

    # ─── 33  Library search order ────────────────────────────────
    pe.content_slide_rich("Library Search Path — DT_NEEDED Resolution Order", [
        (C.CYAN, "1. DT_RPATH (if DT_RUNPATH absent)",
         "Embedded in binary. Legacy. Searched before LD_LIBRARY_PATH. "
         "Dangerous if pointing to world-writable directory."),
        (C.GREEN, "2. LD_LIBRARY_PATH",
         "Environment variable. Prepends to search path. IGNORED when AT_SECURE=1 "
         "(setuid/setgid/fscaps binaries)."),
        (C.YELLOW, "3. DT_RUNPATH",
         "Modern replacement for DT_RPATH. Embedded in binary. Searched AFTER LD_LIBRARY_PATH."),
        (C.RED, "4. /etc/ld.so.cache",
         "Precomputed cache from ldconfig. Maps library names to paths. "
         "Updated by 'ldconfig' scanning /etc/ld.so.conf.d/*.conf."),
        (C.PURPLE, "5. Default: /lib, /usr/lib (/lib64, /usr/lib64)",
         "Fallback paths. Hardcoded in ld.so. Last resort."),
    ], sub_heading="For each DT_NEEDED library, ld.so searches in this order:")

    # ─── 34  LD_* environment ────────────────────────────────────
    pe.table_slide("Dynamic Linker Environment Variables", [
        "Variable", "Function", "AT_SECURE", "Security Note"
    ], [
        ["LD_PRELOAD", "Inject libraries before DT_NEEDED", "Ignored", "Primary hooking vector"],
        ["LD_LIBRARY_PATH", "Prepend search directories", "Ignored", "Library replacement attacks"],
        ["LD_AUDIT", "Load auditor callbacks", "Ignored", "Symbol-level interception"],
        ["LD_DEBUG=all", "Print diagnostic output", "Ignored", "Invaluable for debugging"],
        ["LD_BIND_NOW=1", "Disable lazy binding", "Honored", "Same as -z now (RELRO)"],
        ["LD_TRACE_LOADED_OBJECTS", "Print deps and exit (ldd)", "Honored", "What ldd(1) sets"],
        ["LD_SHOW_AUXV=1", "Print auxiliary vector", "Ignored", "Debug auxv contents"],
    ], sub_heading="Most variables are ignored when AT_SECURE=1 (setuid/setgid binaries)")

    # ─── 35  Section: .dynamic ────────────────────────────────────
    pe.section_slide("The .dynamic Section", 7,
        "Elf64_Dyn array — the dynamic linker's table of contents")

    # ─── 36  .dynamic structure ──────────────────────────────────
    pe.code_slide("Elf64_Dyn — Dynamic Section Entry", """typedef struct {
    Elf64_Sxword d_tag;         // Tag type (DT_NEEDED, DT_STRTAB, ...)
    union {
        Elf64_Xword d_val;      // Integer value
        Elf64_Addr  d_ptr;      // Virtual address pointer
    } d_un;
} Elf64_Dyn;

// The .dynamic section is an array of these entries,
// terminated by DT_NULL (d_tag == 0).
// Every dynamic-linking structure is referenced from here.""", language="C (elf.h)", notes=[
        "16 bytes per entry: 8-byte tag + 8-byte value/pointer",
        ".dynamic lives in RELRO region — writable during load, read-only after",
        "DT_DEBUG is written by ld.so at load time (points to r_debug → link_map chain)",
    ])

    # ─── 37  Key DT tags ─────────────────────────────────────────
    pe.table_slide("Key .dynamic Tags — Complete Reference", [
        "Tag", "d_un", "Purpose"
    ], [
        ["DT_NEEDED", "d_val → .dynstr offset", "Name of required shared library"],
        ["DT_STRTAB / DT_STRSZ", "d_ptr / d_val", "Address & size of .dynstr"],
        ["DT_SYMTAB / DT_SYMENT", "d_ptr / d_val", "Address of .dynsym & entry size (24)"],
        ["DT_GNU_HASH", "d_ptr", "Address of .gnu.hash (fast lookup)"],
        ["DT_HASH", "d_ptr", "Address of .hash (SysV, legacy)"],
        ["DT_RELA / DT_RELASZ", "d_ptr / d_val", "Main relocation table (.rela.dyn)"],
        ["DT_JMPREL / DT_PLTRELSZ", "d_ptr / d_val", "PLT relocations (.rela.plt)"],
        ["DT_PLTGOT", "d_ptr", "Address of .got.plt"],
        ["DT_INIT_ARRAY / DT_INIT_ARRAYSZ", "d_ptr / d_val", "Constructor function pointer array"],
        ["DT_FINI_ARRAY / DT_FINI_ARRAYSZ", "d_ptr / d_val", "Destructor function pointer array"],
        ["DT_FLAGS / DT_FLAGS_1", "d_val", "DF_BIND_NOW, DF_TEXTREL, DF_1_PIE, etc."],
        ["DT_DEBUG", "d_ptr", "→ r_debug (link_map chain for debuggers)"],
    ])

    # ─── 38  DT_FLAGS detail ─────────────────────────────────────
    pe.two_column_slide(
        "DT_FLAGS and DT_FLAGS_1 — Behavioral Flags",
        "DT_FLAGS (d_val)", [
            "DF_BIND_NOW (0x8): resolve all symbols at load time",
            "DF_SYMBOLIC (0x2): prefer own definitions over global scope",
            "DF_TEXTREL (0x4): has relocations in read-only segments (bad)",
            "DF_STATIC_TLS (0x10): uses static TLS (limits dlopen)",
        ],
        "DT_FLAGS_1 (d_val)", [
            "DF_1_NOW (0x1): alias for DF_BIND_NOW",
            "DF_1_PIE (0x8000000): this ET_DYN is a PIE executable",
            "DF_1_NODELETE (0x8): object cannot be dlclose'd",
            "DF_1_INITFIRST (0x20): run constructors before others",
            "DF_1_NOOPEN (0x40): cannot be dlopen'd",
            "DF_1_INTERPOSE (0x400): interpose all symbols",
        ],
        left_color=C.CYAN, right_color=C.PURPLE
    )

    # ─── 39  DT_DEBUG and r_debug ────────────────────────────────
    pe.content_slide_rich("DT_DEBUG → r_debug → link_map Chain", [
        (C.CYAN, "DT_DEBUG Written at Load Time",
         "ld.so writes the address of its r_debug structure into this .dynamic entry "
         "during startup — BEFORE RELRO locks .dynamic to read-only."),
        (C.GREEN, "r_debug Structure",
         "Contains r_version (always 1), r_map (pointer to head of link_map linked list), "
         "r_brk (address of _dl_debug_state — debugger breakpoint), r_state (RT_CONSISTENT/ADD/DELETE)."),
        (C.YELLOW, "link_map Linked List",
         "One node per loaded object. Fields: l_addr (load base), l_name (path string), "
         "l_ld (pointer to object's .dynamic), l_next/l_prev (list links)."),
        (C.RED, "Offensive Use",
         "Walking DT_DEBUG → r_debug → link_map reveals every loaded library's base address "
         "— including libc. Used to compute gadget addresses during exploitation."),
        (C.PURPLE, "Forensic Use",
         "Core dump analysis reconstructs loaded objects via the same r_debug → link_map walk. "
         "Tools: GDB 'info shared', Volatility linux_liblist plugin, custom r_debug parsers."),
    ])

    # ─── 40  Section: Symbols ─────────────────────────────────────
    pe.section_slide("Symbol Tables &\nString Tables", 8,
        ".dynsym / .dynstr — the runtime symbol namespace")

    # ─── 41  Sym structure ───────────────────────────────────────
    pe.code_slide("Elf64_Sym — Dynamic Symbol Table Entry", """typedef struct {
    Elf64_Word    st_name;    // Index into .dynstr
    unsigned char st_info;    // (binding << 4) | type
    unsigned char st_other;   // Visibility in low 2 bits
    Elf64_Half    st_shndx;   // Section index, or SHN_UNDEF / SHN_ABS
    Elf64_Addr    st_value;   // Virtual address (or offset for relocatables)
    Elf64_Xword   st_size;    // Symbol size in bytes
} Elf64_Sym;  // 24 bytes total

// st_info packing:
//   ELF64_ST_BIND(info) = (info) >> 4
//   ELF64_ST_TYPE(info) = (info) & 0xF
//   ELF64_ST_INFO(bind, type) = ((bind) << 4) | ((type) & 0xF)""", language="C (elf.h)", notes=[
        "st_shndx == SHN_UNDEF (0): unresolved reference — must be resolved by dynamic linker",
        "Local symbols precede globals; partition point is sh_info of .dynsym section header",
        ".dynstr index 0 is always an empty string (NUL byte)",
    ])

    # ─── 42  Symbol binding ──────────────────────────────────────
    pe.definition_slide("Symbol Binding (STB_*) — Who Can Override", [
        ("STB_LOCAL (0)", "Not visible outside this object. Never in .dynsym. Fastest resolution.", C.GREEN),
        ("STB_GLOBAL (1)", "Visible to all objects. Must be unique (or error). Standard export.", C.CYAN),
        ("STB_WEAK (2)", "Visible but overridable. If unresolved, value is 0 (no error). Optional deps.", C.YELLOW),
        ("STB_GNU_UNIQUE (10)", "GNU extension for C++ template dedup. Like global but exactly one instance.", C.PURPLE),
    ])

    # ─── 43  Symbol type ─────────────────────────────────────────
    pe.definition_slide("Symbol Type (STT_*) — What the Symbol Represents", [
        ("STT_NOTYPE (0)", "Unspecified type. Common for labels and assembly symbols.", C.DGRAY),
        ("STT_OBJECT (1)", "Data object: variable, array, structure. st_size = object size.", C.CYAN),
        ("STT_FUNC (2)", "Function entry point. st_value = address, st_size = function length.", C.GREEN),
        ("STT_SECTION (3)", "Section symbol. Used internally for relocation against section base.", C.YELLOW),
        ("STT_FILE (4)", "Source file name. For debugger convenience only.", C.BLUE),
        ("STT_COMMON (5)", "Tentative definition. Linker allocates space in .bss.", C.ORANGE),
        ("STT_TLS (6)", "Thread-local storage symbol. Value is offset into TLS block.", C.PURPLE),
        ("STT_GNU_IFUNC (10)", "Indirect function: st_value is a RESOLVER, not the final address.", C.RED),
    ])

    # ─── 44  Symbol visibility ───────────────────────────────────
    pe.table_slide("Symbol Visibility (STV_*) — Interposition Control", [
        "Visibility", "Value", "Exported?", "Interposable?", "Use Case"
    ], [
        ["STV_DEFAULT", "0", "Yes", "Yes", "Standard: LD_PRELOAD can override"],
        ["STV_INTERNAL", "1", "No", "N/A", "Implementation detail — rarely used"],
        ["STV_HIDDEN", "2", "No", "N/A", "Library internal: not in .dynsym at link time"],
        ["STV_PROTECTED", "3", "Yes", "No", "Exported but self-references bind locally"],
    ], sub_heading="STV_HIDDEN and STV_PROTECTED are key for controlling what LD_PRELOAD can hook")

    # ─── 45  Section: Hash Tables ─────────────────────────────────
    pe.section_slide("Hash Tables:\nSysV .hash vs GNU .gnu.hash", 9,
        "Accelerating symbol lookup — from O(n) chain walks to Bloom-filtered O(1)")

    # ─── 46  Hash comparison ─────────────────────────────────────
    pe.comparison_slide(
        "SysV .hash vs GNU .gnu.hash — Performance & Design",
        "SysV .hash (Legacy)", [
            "Layout: nbuckets + nchain + bucket[] + chain[]",
            "nchain = total number of dynamic symbols",
            "Hash function: rotate-and-XOR (elf_hash)",
            "Every probe touches the symbol table (cold cache)",
            "Missing symbol → must walk chain to end",
            "No early termination for absent symbols",
            "O(n/nbuckets) average lookup",
            "Still generated for compatibility with old loaders",
        ],
        "GNU .gnu.hash (Modern)", [
            "Layout: header + Bloom filter + bucket[] + chain[]",
            "Bloom filter (64-bit words) for fast negative lookup",
            "Hash function: DJB2 variant (h = h*33 + c)",
            "Bloom probe eliminates absent symbols WITHOUT touching symtab",
            "Chain stores HASH VALUES, not symbol indices",
            "Most chain walks reject without symbol table access",
            "Symbols sorted by bucket — contiguous in .dynsym",
            "O(1) average for absent symbols (Bloom filter)",
        ],
        left_color=C.RED, right_color=C.GREEN, vs_text="<<"
    )

    # ─── 47  SysV hash function code ─────────────────────────────
    pe.code_slide("SysV Hash Function — elf_hash()", """uint32_t elf_hash(const char *name) {
    uint32_t h = 0, g;
    while (*name) {
        h = (h << 4) + (unsigned char)*name++;
        if ((g = h & 0xF0000000))
            h ^= g >> 24;
        h &= ~g;  // clear the high nibble
    }
    return h;
}

// Lookup:
//   bucket_idx = elf_hash(name) % nbuckets
//   i = bucket[bucket_idx]
//   while (i != STN_UNDEF) {
//       if (strcmp(dynsym[i].name, name) == 0) return &dynsym[i];
//       i = chain[i];  // follow chain
//   }""", language="C", notes=[
        "Rotate-left-4 with high-nibble XOR — designed in the 1990s",
        "Every chain step touches .dynsym (cache-hostile for large symbol tables)",
        "Missing symbol requires full chain traversal — O(chain_length)",
    ])

    # ─── 48  GNU hash function + Bloom ───────────────────────────
    pe.code_slide("GNU Hash Function & Bloom Filter Lookup", """uint32_t gnu_hash(const char *name) {
    uint32_t h = 5381;
    while (*name)
        h = (h * 33) + (unsigned char)*name++;
    return h;
}

// 3-stage lookup:
// Stage 1: Bloom filter (fast negative)
//   word = bloom[(h / 64) % bloom_size]
//   bit1 = (h) % 64
//   bit2 = (h >> bloom_shift) % 64
//   if (!(word & (1ULL << bit1)) || !(word & (1ULL << bit2)))
//       return NULL;  // DEFINITELY not in this DSO
//
// Stage 2: Bucket probe
//   i = bucket[h % nbuckets]
//   if (i < symoffset) return NULL;
//
// Stage 3: Chain walk (compares hash values, not names)
//   while (true) {
//       if ((chain[i - symoffset] | 1) == (h | 1))  // hash match
//           if (strcmp(dynsym[i].name, name) == 0) return &dynsym[i];
//       if (chain[i - symoffset] & 1) break;  // end of chain
//       i++;
//   }""", language="C", notes=[
        "Bloom filter eliminates absent symbols without any .dynsym access",
        "Chain stores hash values — most rejections avoid strcmp entirely",
        "DJB2 variant: better distribution than SysV hash, fewer collisions",
    ])

    # ─── 49  Bloom filter diagram ────────────────────────────────
    pe.diagram_flow_slide(
        "GNU Hash Bloom Filter — Fast Negative Lookup",
        [("Compute\ngnu_hash(name)", C.CYAN),
         ("Test bit 1:\nh % 64", C.GREEN),
         ("Test bit 2:\n(h >> shift) % 64", C.YELLOW),
         ("Either 0?\n→ NOT HERE", C.RED),
         ("Both 1?\n→ Check bucket", C.PURPLE)],
        sub_heading="The dominant performance win: skipping entire DSOs for absent symbols"
    )

    # ─── 50  Performance chart ───────────────────────────────────
    mpl_theme()
    fig, ax = plt.subplots(figsize=(10, 4.5))
    scenarios = ["Symbol present\n(common case)", "Symbol absent\n(most common)", "Large symbol table\n(>5000 symbols)", "Many DT_NEEDED\nlibraries"]
    sysv = [3, 8, 15, 40]
    gnu = [2, 1, 3, 5]
    x = np.arange(len(scenarios))
    ax.bar(x - 0.2, sysv, 0.35, label="SysV .hash", color="#FF4444", edgecolor="#333350")
    ax.bar(x + 0.2, gnu, 0.35, label="GNU .gnu.hash", color="#00D4FF", edgecolor="#333350")
    ax.set_ylabel("Relative Lookup Time", fontsize=11)
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios, fontsize=9)
    ax.set_title("Symbol Lookup Performance: SysV vs GNU Hash", fontsize=13, color="#00D4FF")
    ax.legend(fontsize=10, facecolor="#14142A", edgecolor="#333350", labelcolor="#CCCCCC")
    ax.grid(axis="y", alpha=0.3)
    pe.split_content_chart("Hash Table Performance Comparison", [
        "GNU .gnu.hash is 5-10x faster for absent symbols",
        "Bloom filter eliminates most lookups without touching .dynsym",
        "Chain stores hash values — strcmp avoided for mismatches",
        "Impact: process startup time significantly reduced",
        "Build systems: both can coexist; loader prefers .gnu.hash",
        "If only DT_GNU_HASH present, old loaders fail",
    ], fig, chart_left=True)

    # ─── 51  Section: Relocations ─────────────────────────────────
    pe.section_slide("Relocations", 10,
        "The dynamic linker's patching instructions — from RELATIVE to JUMP_SLOT")

    # ─── 52  Rela structure ──────────────────────────────────────
    pe.code_slide("Elf64_Rela — Relocation Entry with Explicit Addend", """typedef struct {
    Elf64_Addr   r_offset;   // Virtual address to be patched
    Elf64_Xword  r_info;     // (sym_index << 32) | type
    Elf64_Sxword r_addend;   // Explicit addend
} Elf64_Rela;  // 24 bytes

// Extract fields:
//   ELF64_R_SYM(info)  = (info) >> 32     // symbol table index
//   ELF64_R_TYPE(info)  = (info) & 0xFFFFFFFF  // relocation type
//   ELF64_R_INFO(sym, type) = ((sym) << 32) | (type)

// Two relocation tables in a typical binary:
//   .rela.dyn  — relocations applied eagerly at load time
//   .rela.plt  — PLT relocations (lazy unless BIND_NOW)""", language="C (elf.h)", notes=[
        "r_offset: where to write the computed value (GOT slot, data pointer, etc.)",
        "r_info packs both the symbol index AND the relocation type",
        "x86_64 uses RELA (explicit addend); ARM32 uses REL (implicit addend in target)",
    ])

    # ─── 53  Relocation types table ──────────────────────────────
    pe.table_slide("x86_64 Relocation Types — Complete Reference", [
        "Type", "Value", "Formula", "Use Case"
    ], [
        ["R_X86_64_RELATIVE", "8", "*offset = base + addend", "Self-refs in PIE (most common)"],
        ["R_X86_64_GLOB_DAT", "6", "*offset = sym_addr", "GOT entries for global variables"],
        ["R_X86_64_JUMP_SLOT", "7", "*offset = sym_addr", "PLT GOT entries (lazy binding)"],
        ["R_X86_64_64", "1", "*offset = sym + addend", "Direct 64-bit absolute (non-PIE)"],
        ["R_X86_64_PC32", "2", "*offset = sym + add - off", "PC-relative 32-bit"],
        ["R_X86_64_COPY", "5", "memcpy from DSO to exe", "Non-PIC exe refs DSO global var"],
        ["R_X86_64_IRELATIVE", "37", "*offset = resolver()", "IFUNC within same object"],
        ["R_X86_64_TPOFF64", "18", "*offset = sym - TP", "TLS: offset from thread pointer"],
        ["R_X86_64_DTPMOD64", "16", "*offset = module_id", "TLS: module ID for dlopen'd libs"],
    ], sub_heading="The relocation type determines the formula for computing the patched value")

    # ─── 54  RELATIVE dominance chart ────────────────────────────
    pe.pie_chart_slide(
        "Relocation Type Distribution in a Typical PIE Binary",
        ["R_X86_64_RELATIVE", "R_X86_64_GLOB_DAT", "R_X86_64_JUMP_SLOT",
         "R_X86_64_IRELATIVE", "R_X86_64_COPY", "Other"],
        [72, 12, 10, 3, 1, 2],
        sub_heading="RELATIVE dominates: every self-referencing pointer in a PIE needs one"
    )

    # ─── 55  DT_TEXTREL warning ──────────────────────────────────
    pe.warning_slide("DT_TEXTREL — The Dangerous Relocation Flag", [
        ("critical", "DT_TEXTREL means relocations target READ-ONLY segments (text-segment relocations)"),
        ("critical", "Loader must mprotect text WRITABLE → apply relocs → mprotect back → DANGEROUS"),
        ("high", "Writable .text during load = window for code injection if another thread races"),
        ("high", "Extra mprotect syscalls = measurable performance penalty"),
        ("medium", "Modern toolchains: -z text makes DT_TEXTREL a hard linker error"),
        ("info", "Cause: non-PIC code in shared libraries (historical, e.g., old assembly)"),
        ("info", "Detection: readelf -d binary | grep TEXTREL — strong negative quality signal"),
    ])

    # ─── 56  Section: GOT/PLT ─────────────────────────────────────
    pe.section_slide("The GOT, the PLT &\nLazy Binding", 11,
        "The mechanism that makes dynamic linking work — and the #1 exploit target in ELF")

    # ─── 57  Two GOTs comparison ─────────────────────────────────
    pe.comparison_slide(
        ".got vs .got.plt — Two Global Offset Tables",
        ".got (Data GOT)", [
            "Holds imported global VARIABLE addresses",
            "Populated by R_X86_64_GLOB_DAT relocations",
            "Resolved EAGERLY at load time (always)",
            "Contains _GLOBAL_OFFSET_TABLE_ symbol",
            "Under full RELRO: read-only after relocation",
            "Under partial RELRO: ALSO read-only (protected)",
            "Not a direct exploit target (already protected)",
        ],
        ".got.plt (Function GOT)", [
            "Holds imported FUNCTION pointer slots",
            "Populated by R_X86_64_JUMP_SLOT relocations",
            "Lazy binding: resolved on FIRST CALL",
            "Eager binding (BIND_NOW): resolved at load time",
            "Entries [0-2] reserved: .dynamic, link_map, _dl_runtime_resolve",
            "Under partial RELRO: WRITABLE (exploit target!)",
            "Under full RELRO: read-only after relocation",
        ],
        left_color=C.GREEN, right_color=C.RED, vs_text="≠"
    )

    # ─── 58  .got.plt reserved entries ───────────────────────────
    pe.definition_slide(".got.plt Reserved Entries (Indices 0-2)", [
        (".got.plt[0]", "Address of .dynamic — PLT trampolines can find .dynamic via PC-relative load", C.CYAN),
        (".got.plt[1]", "Address of link_map for this object — populated by ld.so at load time", C.GREEN),
        (".got.plt[2]", "Address of _dl_runtime_resolve — the lazy binding resolver entry point", C.YELLOW),
        (".got.plt[3+]", "Per-imported-function slots — initially point back to PLT stub push instruction", C.RED),
    ])

    # ─── 59  PLT mechanism ───────────────────────────────────────
    pe.code_slide("PLT Entry — 16 Bytes Per Imported Function", """// PLT0 (header stub):
PLT0:
  push   QWORD PTR [rip + got_plt_1]   // push link_map
  jmp    QWORD PTR [rip + got_plt_2]   // jmp _dl_runtime_resolve
  nop; nop; nop; nop                    // padding to 16 bytes

// Per-function PLT stub (e.g., puts@plt):
puts@plt:
  jmp    QWORD PTR [rip + GOT_OFFSET]  // 6 bytes: indirect jmp via GOT
  push   <reloc_index>                 // 5 bytes: push .rela.plt index
  jmp    PLT0                          // 5 bytes: relative jmp to header

// First call: GOT entry → second instruction (push + jmp PLT0)
// After resolution: GOT entry → actual puts() in libc""", language="x86asm", notes=[
        "First call path: PLT stub → push reloc_index → PLT0 → _dl_runtime_resolve → puts()",
        "Subsequent calls: PLT stub → GOT already resolved → puts() directly (no resolver)",
        "CET-aware .plt.sec: starts with endbr64 for indirect branch tracking",
    ])

    # ─── 60  Lazy binding flow ───────────────────────────────────
    pe.diagram_flow_slide(
        "Lazy Binding — First Call Resolution Flow",
        [("Program calls\nputs@plt", C.CYAN),
         ("jmp [GOT]\n→ self-loop", C.GREEN),
         ("push reloc_index\njmp PLT0", C.YELLOW),
         ("push link_map\njmp _dl_runtime_resolve", C.RED),
         ("_dl_fixup\nresolves symbol", C.PURPLE),
         ("GOT updated\n→ libc puts()", C.ORANGE),
         ("Tail-jump\nto puts()", C.TEAL)],
        sub_heading="First call: 7-step resolution. Second call: 1-step direct jump via GOT."
    )

    # ─── 61  _dl_fixup internals ─────────────────────────────────
    pe.content_slide_rich("_dl_fixup() — The Lazy Binding Resolver", [
        (C.CYAN, "Step 1: Read relocation entry",
         "Reads .rela.plt[reloc_arg] → extracts r_info (symbol index + type) and r_offset (GOT slot)."),
        (C.GREEN, "Step 2: Look up symbol",
         "Extracts symbol index from r_info, reads .dynsym[sym_idx], gets name from .dynstr."),
        (C.YELLOW, "Step 3: Search global scope",
         "Walks the scope chain: executable → LD_PRELOAD → DT_NEEDED (BFS order). First match wins."),
        (C.RED, "Step 4: Write to GOT",
         "Writes resolved address to *r_offset (the .got.plt slot). GOT now points to actual function."),
        (C.PURPLE, "Step 5: Return address",
         "Returns resolved address to _dl_runtime_resolve, which restores registers and tail-jumps to it."),
    ], sub_heading="_dl_fixup(struct link_map *l, ElfW(Word) reloc_arg)")

    # ─── 62  Symbol resolution order ─────────────────────────────
    pe.content_slide_rich("Symbol Resolution — Scope & Order", [
        (C.CYAN, "1. The Executable",
         "Searched first. Symbols defined in the main binary take precedence over everything."),
        (C.GREEN, "2. LD_PRELOAD Objects",
         "Searched second, in the order specified. This is WHY LD_PRELOAD hooking works — "
         "preloaded definitions shadow later-loaded ones."),
        (C.YELLOW, "3. DT_NEEDED Libraries (BFS order)",
         "Breadth-first traversal of the dependency graph. First definition found wins. "
         "libc is typically last because everything depends on it."),
        (C.RED, "STV_PROTECTED Exception",
         "Protected symbols bind locally within the defining object — immune to LD_PRELOAD interposition. "
         "Used inside libc to prevent internal calls from being redirected."),
        (C.PURPLE, "DF_SYMBOLIC / -Bsymbolic",
         "Makes the object prefer its own definitions over global scope. Similar effect to making "
         "all symbols STV_PROTECTED. Changes LD_PRELOAD semantics for that DSO."),
    ], sub_heading="The global scope is an ordered list — position determines priority")

    # ─── 63  Why lazy binding is dying ───────────────────────────
    pe.section_slide("Why Lazy Binding\nIs Increasingly Disabled", 12,
        "Full RELRO closes the GOT as an exploit target — at a small startup cost")

    # ─── 64  Lazy vs eager comparison ────────────────────────────
    pe.comparison_slide(
        "Lazy Binding vs Full RELRO (Eager Binding)",
        "Lazy Binding (Partial RELRO)", [
            "Resolves symbols on FIRST CALL only",
            "Skips unused symbols → saves startup time",
            ".got.plt remains WRITABLE at runtime",
            "GOT overwrite = classic exploit primitive",
            "Non-deterministic memory image (changes at each first call)",
            "Default on older toolchains without -z now",
            "Unpredictable resolution latency at call sites",
        ],
        "Full RELRO (-z relro -z now)", [
            "Resolves ALL symbols at LOAD TIME",
            "Slight startup penalty (microseconds for most binaries)",
            ".got.plt mprotect'd READ-ONLY after relocation",
            "GOT overwrite → SIGSEGV (attack fails)",
            "Deterministic memory image from first instruction",
            "Standard on all modern hardened toolchains",
            "Predictable performance: no lazy resolution spikes",
        ],
        left_color=C.RED, right_color=C.GREEN, vs_text="→"
    )

    # ─── 65  RELRO detection ─────────────────────────────────────
    pe.code_slide("Detecting RELRO Posture — Quick Checks", """# Check with checksec (pwntools)
$ checksec --file=./binary
    Arch:     amd64-64-little
    RELRO:    Full RELRO          # ← what you want
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled

# Check with readelf
$ readelf -d ./binary | grep -E 'BIND_NOW|FLAGS'
 0x000000000000001e (FLAGS)    BIND_NOW
 0x000000006ffffffb (FLAGS_1)  Flags: NOW PIE

# Check for GNU_RELRO segment
$ readelf -l ./binary | grep GNU_RELRO
  GNU_RELRO      0x002d90 0x0000000000003d90 ...

# Compile with full RELRO
$ gcc -Wl,-z,relro,-z,now -o binary source.c""", language="bash", notes=[
        "BIND_NOW in FLAGS or FLAGS_1 = eager binding = full RELRO possible",
        "GNU_RELRO segment present = some RELRO protection (could be partial)",
        "Both BIND_NOW + GNU_RELRO = full RELRO (GOT is read-only after load)",
    ])

    # ─── 66  Three forces chart ──────────────────────────────────
    pe.icon_grid_slide("Three Forces Killing Lazy Binding", [
        ("🔒", "Security", "Writable .got.plt = classic exploit target. "
         "Full RELRO + BIND_NOW makes GOT overwrite produce SIGSEGV instead of code execution.", "red"),
        ("📐", "Determinism", "Lazy binding creates non-deterministic memory images. "
         "Memory forensics, snapshots, and fingerprinting tools prefer deterministic state.", "yellow"),
        ("⚡", "PGO", "Profile-Guided Optimization reorders code and pre-resolves hot symbols. "
         "Lazy binding savings are smaller than they used to be.", "cyan"),
    ], cols=3)

    # ─── 67  Section: Complete Timeline ───────────────────────────
    pe.section_slide("Complete ELF\nLoad Sequence", 13,
        "From execve() to main() — every step in order")

    # ─── 68-69  Full timeline (two slides for density) ────────────
    pe.timeline_slide("ELF Load Sequence — Phase 1: Kernel", [
        ("execve()", "User calls execve() syscall", "cyan"),
        ("binfmt_elf", "Kernel parses ELF header + phdr table", "green"),
        ("mmap LOAD", "Kernel maps PT_LOAD segments", "yellow"),
        ("ASLR base", "Kernel picks random base for PIE", "red"),
        ("Load ld.so", "Kernel maps PT_INTERP interpreter", "purple"),
        ("Build auxv", "Kernel builds aux vector on stack", "orange"),
        ("jmp ld.so", "Transfer to interpreter _start", "teal"),
    ])

    pe.timeline_slide("ELF Load Sequence — Phase 2: Dynamic Linker → main()", [
        ("_dl_start", "ld.so self-relocates (RELATIVE)", "cyan"),
        ("Find DYNAMIC", "Locate program's PT_DYNAMIC via AT_PHDR", "green"),
        ("DT_NEEDED", "Walk deps, open + mmap each DSO", "yellow"),
        ("Relocate", "Apply .rela.dyn (eager) + .rela.plt", "red"),
        ("RELRO", "mprotect RELRO regions read-only", "purple"),
        ("Constructors", "Run init_array in dependency order", "orange"),
        ("main()", "_start → __libc_start_main → main", "teal"),
    ])

    # ─── 70  Full sequence detail ────────────────────────────────
    pe.detail_slide("Complete Load Sequence — Detailed", [
        ("Phase 1: Kernel (fs/binfmt_elf.c)", [
            "execve() → kernel validates ELF magic and header",
            "Walk PT_LOAD segments → mmap each with permissions from p_flags",
            "For PIE (ET_DYN): pick ASLR'd base (ELF_ET_DYN_BASE + randomization)",
            "For ET_EXEC: honor absolute p_vaddr addresses (no ASLR for binary)",
            "If PT_INTERP exists: open ld.so, mmap its PT_LOAD at separate random base",
            "Build stack: argc, argv, envp, auxiliary vector (AT_PHDR, AT_BASE, AT_RANDOM, etc.)",
            "Transfer control to interpreter _start (or program e_entry if no PT_INTERP)",
        ], C.CYAN),
        ("Phase 2: Dynamic Linker (_dl_start → _dl_main)", [
            "_dl_start: self-relocate via R_X86_64_RELATIVE (bootstrap, no GOT/PLT yet)",
            "Find program's PT_DYNAMIC via AT_PHDR/AT_PHNUM",
            "Walk DT_NEEDED → open each library → mmap PT_LOAD segments at random bases",
            "Build global scope: executable → LD_PRELOAD → DT_NEEDED (BFS order)",
        ], C.GREEN),
        ("Phase 3: Relocation & Protection", [
            "For each DSO: resolve R_X86_64_RELATIVE, GLOB_DAT in .rela.dyn (eager)",
            "For each DSO: resolve JUMP_SLOT in .rela.plt (lazy unless DT_BIND_NOW)",
            "Run IRELATIVE resolvers → apply COPY relocations",
            "_dl_protect_relro → mprotect PT_GNU_RELRO ranges read-only",
        ], C.YELLOW),
        ("Phase 4: Constructors & Handoff", [
            "Run pre-init array (program only)",
            "Run init/init_array per DSO in dependency order (deps before dependents)",
            "Transfer to program e_entry → _start → __libc_start_main → main()",
        ], C.PURPLE),
    ])

    # ─── 71  Exit sequence ───────────────────────────────────────
    pe.content_slide_rich("Process Exit Sequence", [
        (C.CYAN, "1. main() returns (or exit() called)",
         "Return value from main becomes the process exit status."),
        (C.GREEN, "2. atexit handlers",
         "Called in reverse registration order. Registered by atexit() and on_exit()."),
        (C.YELLOW, "3. fini_array per DSO",
         "Destructor arrays called in REVERSE dependency order (dependents before deps)."),
        (C.RED, "4. DT_FINI per DSO",
         "Legacy single-function destructors. Called after fini_array for each DSO."),
        (C.PURPLE, "5. _exit() syscall",
         "Kernel terminates the process. All memory mappings released."),
    ], sub_heading="Reverse of construction order — exploitation target via .fini_array overwrite")

    # ─── 72  Section: Detection ───────────────────────────────────
    pe.section_slide("Detection & Forensics at\nthe GOT/PLT Layer", 14,
        "Turning the loader's mechanics into defensive instrumentation")

    # ─── 73  Detection opportunities ─────────────────────────────
    pe.icon_grid_slide("GOT/PLT Detection & Forensics Opportunities", [
        ("🔍", "GOT Integrity Check", "Compare GOT entries against expected resolved addresses "
         "(walk link_map + symbol resolution rules). Finds GOT overwrites.", "cyan"),
        ("📋", "PLT Auditing", "LD_AUDIT la_pltenter/la_pltexit callbacks observe every PLT call. "
         "Useful for tracing in controlled environments.", "green"),
        ("⚠️", "Resolver Hijack", "Check .got.plt[2] against expected _dl_runtime_resolve address. "
         "Replacement redirects ALL lazy resolutions.", "red"),
        ("🔗", "link_map Walk", "Enumerate loaded objects via DT_DEBUG → r_debug → link_map. "
         "Unexpected libraries = injection detection.", "purple"),
        ("📊", "Relocation Audit", "Compare .init_array/.fini_array entries against known function "
         "addresses in .text. Entries outside .text are anomalous.", "yellow"),
        ("🛡️", "Static Binary Note", "Static binaries skip ALL dynamic linking. No GOT, no PLT, "
         "no LD_PRELOAD. Detection must move to seccomp/kernel level.", "orange"),
    ], cols=3)

    # ─── 74  Detection code ──────────────────────────────────────
    pe.code_slide("Runtime GOT Integrity Check (dl_iterate_phdr)", """#define _GNU_SOURCE
#include <link.h>
#include <stdio.h>

static int callback(struct dl_phdr_info *info, size_t size, void *data) {
    printf("%-40s base=0x%lx  phnum=%d\\n",
           info->dlpi_name[0] ? info->dlpi_name : "[main]",
           (unsigned long)info->dlpi_addr,
           info->dlpi_phnum);

    for (int i = 0; i < info->dlpi_phnum; i++) {
        const Elf64_Phdr *ph = &info->dlpi_phdr[i];
        if (ph->p_type == PT_LOAD) {
            printf("  PT_LOAD  vaddr=0x%lx  memsz=0x%lx  flags=%c%c%c\\n",
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
}""", language="C", notes=[
        "dl_iterate_phdr: canonical way to enumerate loaded objects from within a process",
        "Each callback receives load base + full program header table per DSO",
        "Compare against baseline to detect injected libraries (dlopen, LD_PRELOAD)",
    ])

    # ─── 75-78  Radar charts + analysis slides ───────────────────
    pe.radar_chart_slide(
        "ELF Hardening Feature Coverage — Radar Analysis",
        ["ASLR (PIE)", "Full RELRO", "Stack Canary", "NX (W^X)",
         "CET (IBT+SS)", "FORTIFY", "KCFI", "STV_PROTECTED"],
        [("Modern Hardened", [9, 9, 8, 9, 6, 7, 5, 4], "#00D4FF"),
         ("Legacy Default", [3, 2, 5, 7, 0, 3, 0, 1], "#FF4444"),
         ("Stripped Implant", [8, 0, 0, 0, 0, 0, 0, 0], "#FFD700")],
        sub_heading="Higher = better protection. Legacy defaults leave major gaps."
    )

    # ─── 79  Risk matrix ─────────────────────────────────────────
    pe.risk_matrix_slide("ELF Attack Surface Risk Matrix", [
        (4, 4, "GOT Overwrite\n(Partial RELRO)"),
        (3, 3, "ret2PLT"),
        (2, 4, "ret2dlresolve"),
        (4, 2, "LD_PRELOAD\nHijack"),
        (1, 3, ".init_array\nTampering"),
        (3, 1, "DT_RPATH\nAbuse"),
    ])

    # ─── 80  ELF hardening checklist ─────────────────────────────
    pe.content_slide("ELF Hardening Checklist — Binary Intake Pipeline", [
        "☐ Full RELRO: readelf -d | grep BIND_NOW → must be present",
        "☐ PIE enabled: readelf -h | e_type == ET_DYN + has PT_INTERP",
        "☐ NX stack: readelf -l | grep GNU_STACK → must NOT have E flag",
        "☐ Stack canary: checksec shows 'Canary found'",
        "☐ No DT_TEXTREL: readelf -d | grep TEXTREL → must be absent",
        "☐ No W+X segments: no PT_LOAD with both PF_W and PF_X",
        "☐ No world-writable DT_RPATH/DT_RUNPATH paths",
        "☐ .init_array/.fini_array entries point into .text segment only",
        "☐ Section headers present (e_shoff ≠ 0) for analyzability",
        "☐ Build ID note present (NT_GNU_BUILD_ID) for debuginfo correlation",
        "☐ CET/BTI properties present (PT_GNU_PROPERTY) if supported",
        "☐ No anomalous e_ident padding (bytes 9-15 should be zero)",
    ])

    # ─── 81  Cross-references ────────────────────────────────────
    pe.cross_reference_slide([
        ("Ch 1A Part 2", "GOT/PLT exploitation techniques, ret2dlresolve, LD_PRELOAD attacks, YARA rules"),
        ("Ch 1B", "TLS, IFUNC, RELRO internals, eh_frame, symbol versioning, init/fini arrays"),
        ("Ch 2 (PE/COFF)", "Windows binary format — analogous structures: IAT/EAT, delay imports"),
        ("Domain 2", "Process memory layout — where segments map in virtual address space"),
        ("Domain 3", "Memory corruption — the vulnerabilities that enable GOT overwrites"),
        ("Domain 4", "Code reuse attacks — ROP/JOP through PLT and gadgets in .text"),
        ("Domain 6", "Mitigation bypass — KASLR/ASLR defeat using ELF info leaks"),
        ("Domain 11", "Malware analysis — ELF packing, section manipulation, PT_NOTE infection"),
        ("Domain 12", "Reverse engineering — static/dynamic analysis of ELF binaries"),
    ])

    # ─── 82  Key takeaways ───────────────────────────────────────
    pe.takeaway_slide([
        "ELF has TWO views: segments (runtime, kernel reads) vs sections (link-time, optional for execution)",
        "Program headers are load-bearing; section headers are analysis-friendly but strippable",
        "The auxiliary vector (auxv) is the kernel's primary data channel to userspace at process start",
        "AT_SECURE is THE defense against LD_PRELOAD/LD_LIBRARY_PATH in setuid binaries",
        "The dynamic linker is the most privileged early-life userspace component",
        ".got.plt under partial RELRO is writable — THE classic ELF exploit target",
        "Full RELRO (-z relro -z now) closes GOT overwrite attacks at negligible startup cost",
        "Symbol resolution order: executable → LD_PRELOAD → DT_NEEDED (BFS) — order = priority",
        "GNU .gnu.hash Bloom filter makes absent-symbol lookup effectively O(1)",
        "Every binary intake pipeline should check: Full RELRO, PIE, NX, no TEXTREL, no W+X segments",
    ])

    # ─── 83  Summary ─────────────────────────────────────────────
    pe.summary_slide("Part 1 Summary — ELF Structure & Loading",
        "This presentation covered the foundational ELF structures that every security engineer "
        "must internalize: the dual-view architecture (sections vs segments), the complete file header "
        "and program header specification, the kernel-to-loader handoff via the auxiliary vector, "
        "the dynamic linker's boot sequence and library search path, the .dynamic table of contents, "
        "the symbol resolution machinery (hash tables, relocation types), and the GOT/PLT lazy "
        "binding mechanism that remains the most exploited feature of the ELF format.",
        key_points=[
            "Segments are what runs; sections are what the linker arranged",
            "Full RELRO is the single most impactful ELF hardening flag",
            "Part 2 covers: exploitation techniques, malware analysis, YARA rules, defensive tooling",
        ])

    # ─── 84  End ─────────────────────────────────────────────────
    pe.end_slide("End of Part 1",
        "Domain 1 · Chapter 1A · ELF Foundations & Dynamic Linking Core\n"
        "Continue to Part 2: ELF Security & Exploitation")

    pe.save(os.path.join(OUT_DIR, "D01_Ch1A_P1_ELF_Structure_Loading.pptx"))


def gen_html():
    hp = HTMLPresentation("Domain 1 · Ch1A · ELF Structure & Loading")

    hp.title_slide(
        "ELF Foundations &\nDynamic Linking Core",
        "File Header · Program Headers · Segments · Sections · GOT/PLT · Lazy Binding",
        domain="DOMAIN 1 — BINARY FORMATS",
        chapter="Chapter 1A · Part 1 of 2"
    )

    hp.agenda_slide([
        "ELF Dual-View Architecture", "ELF File Header (Elf64_Ehdr)",
        "Program Headers & Segment Types", "Section Headers & sh_flags",
        "Kernel→Loader Handoff & auxv", "Dynamic Linker Boot Sequence",
        ".dynamic Section Tags", "Symbol Tables & Visibility",
        "SysV .hash vs GNU .gnu.hash", "Relocation Types (x86_64)",
        ".got vs .got.plt", "PLT & Lazy Binding Flow",
        "Symbol Resolution Order", "Full RELRO vs Partial",
        "Complete Load Sequence", "Detection & Forensics",
    ])

    hp.stats_slide("ELF Format at a Glance", [
        ("64 B", "Header Size", "cyan"), ("56 B", "Phdr Entry", "green"),
        ("64 B", "Shdr Entry", "yellow"), ("24 B", "Symbol Entry", "purple"),
    ])

    hp.section_slide("The Dual-View Architecture", 1, "Same bytes, two descriptions")

    hp.comparison_slide(
        "Sections vs Segments",
        "Section Headers (Linker View)", [
            "What ld needs to combine .o files",
            "Can be stripped — binary still runs",
            "Symbol names, debug info, exception tables",
            "sh_flags: SHF_ALLOC, SHF_WRITE, SHF_EXECINSTR",
            "Not consulted by kernel at all",
        ],
        "Program Headers (Loader View)", [
            "What kernel/ld.so needs to mmap & execute",
            "Cannot be removed — binary won't load",
            "Memory regions with R/W/X permissions",
            "p_flags: PF_R, PF_W, PF_X",
            "The ONLY thing kernel reads",
        ]
    )

    hp.svg_layers_slide("ELF Dual-View Mental Model", [
        ("ELF File Header (Elf64_Ehdr)", "cyan", "e_phoff → segments, e_shoff → sections"),
        ("Program Header Table", "green", "Kernel reads ONLY this for execution"),
        ("PT_LOAD #1 (R-X)", "blue", ".text, .plt, .init — executable code"),
        ("PT_LOAD #2 (R--)", "teal", ".rodata, .eh_frame — read-only data"),
        ("PT_LOAD #3 (RW→R-- RELRO)", "yellow", ".dynamic, .got — RELRO-protected"),
        ("PT_LOAD #4 (RW-)", "red", ".data, .got.plt, .bss — writable data"),
        ("Section Header Table (optional)", "purple", "Analysis-only, strippable"),
    ])

    hp.warning_slide("Security Implications", [
        ("critical", "Section headers can be stripped/forged — tools relying only on sections are fooled"),
        ("high", "YARA rules matching section names miss binaries with stripped tables"),
        ("high", "Packers routinely zero e_shoff to frustrate disassemblers"),
        ("medium", "Section names can lie: .text can contain writable data"),
        ("info", "Always validate program headers first, sections second"),
    ])

    hp.section_slide("The ELF File Header", 2, "Elf64_Ehdr — 64 bytes")

    hp.code_slide("Elf64_Ehdr Structure", """typedef struct {
    unsigned char e_ident[16];   // Magic + class + endian
    Elf64_Half    e_type;        // ET_REL | ET_EXEC | ET_DYN | ET_CORE
    Elf64_Half    e_machine;     // EM_X86_64 | EM_AARCH64
    Elf64_Word    e_version;     // EV_CURRENT
    Elf64_Addr    e_entry;       // Entry point VA
    Elf64_Off     e_phoff;       // Phdr table offset
    Elf64_Off     e_shoff;       // Shdr table offset
    Elf64_Word    e_flags;       // Processor-specific
    Elf64_Half    e_ehsize;      // This header: 64
    Elf64_Half    e_phentsize;   // Phdr entry: 56
    Elf64_Half    e_phnum;       // Number of phdrs
    Elf64_Half    e_shentsize;   // Shdr entry: 64
    Elf64_Half    e_shnum;       // Number of shdrs
    Elf64_Half    e_shstrndx;   // Section name strtab
} Elf64_Ehdr;""", language="c", notes=[
        "e_type ET_DYN: ambiguous — both .so and PIE are ET_DYN",
        "e_entry for PIE: offset from load base, not absolute VA",
    ])

    hp.table_slide("e_ident[16] Breakdown", ["Offset", "Name", "Value", "Purpose"], [
        ["0-3", "EI_MAG", "0x7F ELF", "Magic number"],
        ["4", "EI_CLASS", "1=32, 2=64", "Address size"],
        ["5", "EI_DATA", "1=LSB, 2=MSB", "Endianness"],
        ["7", "EI_OSABI", "0=NONE, 3=GNU", "Target OS/ABI"],
        ["9-15", "EI_PAD", "Should be 0", "Can hide data!"],
    ])

    hp.definition_slide("ELF Header Anomaly Signals", [
        ("e_shoff = 0", "No sections — strong anomaly signal", "red"),
        ("e_phentsize ≠ 56", "Invalid phdr size for ELF64", "orange"),
        ("e_ident pad ≠ 0", "Data smuggling in unused bytes", "yellow"),
        ("e_entry → non-X", "Post-link entry point modification", "purple"),
    ])

    hp.section_slide("Program Headers", 3, "Elf64_Phdr — segment loading")

    hp.table_slide("Program Header Types", ["Type", "Value", "Purpose", "Security"], [
        ["PT_LOAD", "1", "Map file region", "W+X = anomalous"],
        ["PT_DYNAMIC", "2", ".dynamic array", "Required for dynamic linking"],
        ["PT_INTERP", "3", "Path to ld.so", "Absent = static (no LD_PRELOAD)"],
        ["PT_NOTE", "4", "Build ID, CET", "Infection target (→PT_LOAD)"],
        ["PT_GNU_STACK", "0x6474e551", "Stack perms", "PF_X = exec stack!"],
        ["PT_GNU_RELRO", "0x6474e552", "RELRO region", "mprotect'd after reloc"],
    ])

    hp.section_slide("Kernel → Loader Handoff", 5, "The auxiliary vector bridge")

    hp.svg_flow_slide("Kernel Loading Sequence", [
        ("execve()", "cyan"), ("Parse ELF", "green"), ("mmap LOAD", "yellow"),
        ("ASLR base", "red"), ("Load ld.so", "purple"), ("Build auxv", "orange"),
        ("jmp ld.so", "teal"),
    ])

    hp.table_slide("Auxiliary Vector (auxv)", ["Tag", "Purpose", "Security Impact"], [
        ["AT_PHDR", "Program header table VA", "ld.so finds PT_DYNAMIC"],
        ["AT_RANDOM", "16 bytes kernel random", "Seeds stack canary"],
        ["AT_SECURE", "1 if setuid/setgid", "Disables LD_PRELOAD!"],
        ["AT_SYSINFO_EHDR", "vDSO address", "Fast syscalls"],
        ["AT_BASE", "ld.so load base", "Self-relocation target"],
    ])

    hp.content_slide_rich("AT_SECURE — Setuid Safety", [
        ("red", "What It Does", "ld.so ignores LD_PRELOAD, LD_LIBRARY_PATH, LD_AUDIT when AT_SECURE=1"),
        ("yellow", "When Set", "Kernel sets for setuid, setgid, file-capability binaries"),
        ("green", "Why Critical", "Without it, any user could LD_PRELOAD into setuid binaries for root"),
        ("purple", "CVE-2010-3856", "$ORIGIN expansion bypassed AT_SECURE in older glibc"),
    ])

    hp.section_slide("The Dynamic Linker", 6, "ld-linux.so boot sequence")

    hp.svg_flow_slide("Library Search Path Order", [
        ("DT_RPATH", "cyan"), ("LD_LIBRARY_PATH", "green"),
        ("DT_RUNPATH", "yellow"), ("ld.so.cache", "red"),
        ("/lib, /usr/lib", "purple"),
    ], sub_heading="LD_LIBRARY_PATH ignored when AT_SECURE=1")

    hp.section_slide("Symbol Tables", 8, ".dynsym / .dynstr")

    hp.definition_slide("Symbol Binding (STB_*)", [
        ("STB_LOCAL", "Not visible outside object", "green"),
        ("STB_GLOBAL", "Visible to all, must be unique", "cyan"),
        ("STB_WEAK", "Overridable, 0 if unresolved", "yellow"),
        ("STB_GNU_UNIQUE", "C++ template dedup", "purple"),
    ])

    hp.table_slide("Symbol Visibility", ["Visibility", "Exported?", "Interposable?", "Use Case"], [
        ["STV_DEFAULT", "Yes", "Yes", "Standard (LD_PRELOAD can hook)"],
        ["STV_HIDDEN", "No", "N/A", "Library internal"],
        ["STV_PROTECTED", "Yes", "No", "Immune to LD_PRELOAD"],
    ])

    hp.section_slide("Hash Tables", 9, "SysV vs GNU")

    hp.comparison_slide("SysV .hash vs GNU .gnu.hash",
        "SysV .hash", [
            "Every probe touches symbol table",
            "Missing symbol → walk chain to end",
            "No early termination",
        ],
        "GNU .gnu.hash", [
            "Bloom filter eliminates absent symbols",
            "Chain stores hash values, not indices",
            "O(1) for absent symbols",
        ]
    )

    hp.section_slide("GOT, PLT & Lazy Binding", 11, "The #1 exploit target in ELF")

    hp.comparison_slide(".got vs .got.plt",
        ".got (Data GOT)", [
            "Imported variable addresses",
            "Resolved eagerly (always)",
            "Protected by RELRO (even partial)",
        ],
        ".got.plt (Function GOT)", [
            "Imported function pointers",
            "Lazy binding: first call resolution",
            "Partial RELRO: WRITABLE (exploit target!)",
            "Full RELRO: read-only after load",
        ]
    )

    hp.svg_flow_slide("Lazy Binding — First Call Resolution", [
        ("Call puts@plt", "cyan"), ("jmp [GOT]→self", "green"),
        ("push reloc_idx", "yellow"), ("jmp PLT0", "red"),
        ("_dl_fixup", "purple"), ("GOT updated", "orange"),
        ("→ puts()", "teal"),
    ])

    hp.section_slide("Full RELRO", 12, "Closing the GOT as an exploit target")

    hp.comparison_slide("Lazy vs Full RELRO",
        "Partial RELRO", [
            ".got.plt WRITABLE at runtime",
            "GOT overwrite = classic exploit",
            "Non-deterministic memory image",
        ],
        "Full RELRO (-z relro -z now)", [
            ".got.plt READ-ONLY after load",
            "GOT overwrite → SIGSEGV",
            "Deterministic from first instruction",
            "Negligible startup cost",
        ]
    )

    hp.section_slide("Complete Load Sequence", 13, "execve() → main()")

    hp.svg_flow_slide("Kernel Phase", [
        ("execve()", "cyan"), ("Parse ELF", "green"),
        ("mmap LOAD", "yellow"), ("ASLR", "red"),
        ("Load ld.so", "purple"), ("auxv", "orange"),
    ])

    hp.svg_flow_slide("Dynamic Linker Phase", [
        ("Self-reloc", "cyan"), ("Find .dynamic", "green"),
        ("DT_NEEDED", "yellow"), ("Relocate", "red"),
        ("RELRO", "purple"), ("Constructors", "orange"),
        ("→ main()", "teal"),
    ])

    hp.svg_network_slide("GOT/PLT Detection Opportunities", "GOT/PLT\nLayer", [
        ("GOT Integrity", "cyan"), ("PLT Audit", "green"),
        ("Resolver Check", "red"), ("link_map Walk", "purple"),
        ("Reloc Audit", "yellow"), ("Static Binary", "orange"),
    ])

    hp.takeaway_slide([
        "Segments are what runs; sections are what linker arranged",
        "AT_SECURE is THE defense for setuid binaries",
        ".got.plt under partial RELRO is writable — classic exploit target",
        "Full RELRO (-z relro -z now) closes GOT attacks",
        "GNU .gnu.hash Bloom filter: O(1) for absent symbols",
        "Every pipeline: check Full RELRO, PIE, NX, no TEXTREL",
    ])

    hp.end_slide("End of Part 1", "Continue to Part 2: ELF Security & Exploitation")

    hp.save(os.path.join(OUT_DIR, "D01_Ch1A_P1_ELF_Structure_Loading.html"))


if __name__ == "__main__":
    gen_pptx()
    gen_html()
    print("\n✓ Domain 1, Chapter 1A, Part 1 complete.")
