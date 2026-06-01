---
corso: "Cybersecurity Masterclass"
fase: "Domain 15 — Mobile Security"
modulo: "15.B"
titolo: "iOS Security and Mobile Network Architecture"
versione: "iOS 18, Xcode 16, Frida 16.x, objection 1.12+, checkm8/palera1n, 5G SA Release 18"
livello: "Advanced"
prerequisiti:
  - "ARM64 architecture fundamentals (registers, calling convention, PAC)"
  - "Mach-O binary format, code signing, and entitlements"
  - "TLS 1.2/1.3 and X.509 certificate validation"
  - "Kerberos and EAP-AKA authentication protocols"
  - "TCP/IP networking, IKEv2/IPsec, and SIP signaling basics"
obiettivi:
  - "Explain the iOS trusted boot chain, AMFI enforcement, and Trust Cache mechanism, and identify where each jailbreak type subverts them"
  - "Perform iOS app security testing using Frida and objection: hook Objective-C/Swift methods, bypass jailbreak detection, and dump Keychain items"
  - "Bypass SSL certificate pinning on iOS using Frida scripts targeting SecTrustEvaluateWithError, TrustKit, and custom NSURLSession delegates"
  - "Analyze zero-click exploit chains (FORCEDENTRY, PWNYOURHOME) and evaluate Lockdown Mode's mitigation coverage"
  - "Describe the 5G SBA security architecture including SUCI/ECIES, 5G-AKA, SEPP/N32 PRINS, and network-slicing isolation threats"
tag: [ios, frida, objection, jailbreak, checkm8, ssl-pinning, pegasus, 5g-security, mobile-network, forensics]
---

# Domain 15, Chapter 15B — iOS Security and Mobile Network Architecture

> **Learning Objectives.**
> After completing this chapter, the practitioner will be able to:
> 1. Trace the iOS trusted boot chain from BootROM through iBSS/iBEC to XNU kernel, and explain how checkm8, PPL, KTRR, and PAC constrain exploitation.
> 2. Perform runtime analysis of an iOS app using Frida and objection: extract Keychain items, hook authentication methods, bypass jailbreak detection, and intercept network requests.
> 3. Bypass SSL certificate pinning on iOS apps using at least three methods (Frida SecTrust hooks, objection automated bypass, SSL Kill Switch 2) and validate interception with Burp Suite.
> 4. Conduct iOS forensic acquisition using checkm8-based tools and sysdiagnose analysis, extracting KnowledgeC timelines, PowerLog data, and crash-log exploitation indicators.
> 5. Explain the 5G Service-Based Architecture security model including SUCI concealment, 5G-AKA mutual authentication, SEPP inter-operator protection, and network-slicing isolation requirements.

> **Scope.** iOS security model (sandbox, entitlements, trusted boot chain). Code signing (amfid, CoreTrust, AMFI). iOS sandbox internals. Jailbreak techniques (IOKit vulns, checkm8 BootROM, PAC bypass). Runtime protections (PPL, KTRR, APRR, W^X). Secure Enclave (SEP, SepOS, effaceable storage, keychain). Data Protection classes. Trust Cache. Kernel exploitation (IOKit UAF, XPC deserialization, MIG). Userland exploitation (WebKit JIT, iMessage zero-click). Spyware analysis (NSO Pegasus, Predator, QuaDream). App security testing (Frida, objection, MobSF). SSL/TLS pinning attack/defense. Data storage forensics. IPC/URL scheme security. MDM and enterprise. iOS forensics (checkm8 acquisition, sysdiagnose, KnowledgeC). 5G architecture (AUSF, UDM, AMF, SMF, UPF, SBA, N32/SEPP, SUCI/ECIES, 5G-AKA, network slicing, gNB security, O-RAN). IMS/VoLTE/VoNR. VoWiFi/ePDG. SMS interception across generations. Mobile network attacks (SS7/Diameter, baseband, SIM/eSIM).

---

## 1. iOS security model

### 1.1 Trusted boot chain

iOS devices boot through a hardware-rooted chain of trust: **BootROM** (immutable, burned into silicon -- the root of trust; verifies iBSS), **iBSS** (Low-Level Bootloader, verifies iBEC), **iBEC** (verifies the kernel/kernelcache), and the **kernel** (verifies all userspace code via AMFI). Each stage verifies the next using Apple's public key embedded in the BootROM. A failure at any stage halts boot (DFU mode).

**Boot stages in detail:**

1. **BootROM** (SecureROM): executes from read-only memory on the application processor. Initializes the hardware, loads iBSS from NOR/NAND, and verifies its IMG4 signature against the RSA public key fused into silicon. On A12+, BootROM enforces that iBSS was built for the specific device's ECID (Exclusive Chip Identification) via APTicket (personalized signing).
2. **iBSS** (iBootStage1): minimal bootloader that initializes DRAM and loads iBEC. Verifies iBEC's IMG4 signature.
3. **iBEC** (iBootStage2): loads the kernelcache and devicetree. Verifies both against Apple's signing chain. Sets up boot-args, initializes hardware controllers. Passes control to the XNU kernel.
4. **XNU kernel**: initializes the Mach/BSD subsystems, loads the Trust Cache (precomputed list of CDHashes for system binaries), and launches `launchd` (PID 1).

**APTicket and personalized signing**: since iOS 6+, Apple personalizes firmware signatures per device. The SHSH blob (Signed Hash) ties the firmware version to the device's ECID. This prevents downgrade attacks -- an older, vulnerable firmware cannot be installed unless Apple is still signing it (TSS -- Ticket Signing Server). Tools like `tsschecker` query Apple's TSS for signing status.

The checkm8 exploit (section 2.5) targets the BootROM -- the only component that cannot be patched by software update.

### 1.2 Code signing and AMFI

All executable code on iOS must be signed by Apple (or by a developer certificate constrained by a provisioning profile). Enforcement is layered:

**AMFI (Apple Mobile File Integrity)**: a kernel extension (`com.apple.driver.AppleMobileFileIntegrity`) that intercepts `execve()`, `mmap(PROT_EXEC)`, and `mprotect()` system calls. AMFI verifies code signatures by delegating to **amfid** (a userspace daemon running as root). amfid calls into **CoreTrust** (Apple's certificate validation framework) to validate the CMS signature and certificate chain embedded in the code directory (CodeDirectory) of the Mach-O binary.

**Enforcement flow:**

```
Process calls execve() or mmap(PROT_EXEC)
  -> Kernel traps to AMFI.kext
  -> AMFI sends message to amfid via Mach port
  -> amfid extracts CodeDirectory, verifies CMS signature via CoreTrust
  -> CoreTrust validates certificate chain up to Apple Root CA
  -> amfid returns result to AMFI.kext
  -> AMFI allows or kills the process
```

**CDHash (Code Directory Hash)**: a SHA-256 hash of the CodeDirectory that uniquely identifies a signed binary. The Trust Cache (section 1.7) contains CDHashes of all system binaries.

**Key entitlements for AMFI bypass (Apple-internal):**
- `com.apple.private.amfi.can-load-cdhash` -- allows loading binaries by CDHash without full signature verification
- `com.apple.private.amfi.can-execute-cdhash` -- allows execution by CDHash
- `com.apple.private.security.no-container` -- escapes sandbox container
- `platform-application` -- grants access to private frameworks

Only Apple's App Store signing or enterprise-distribution signing produces signatures that AMFI accepts on non-jailbroken devices. Ad-hoc signing (`ldid -S`) works only with AMFI disabled (jailbroken). [MSTG-RESILIENCE-1, MSTG-RESILIENCE-3]

### 1.3 Sandbox

Every third-party app runs in a sandbox defined by a Sandbox profile. The profile (compiled from the Sandbox Profile Language, SBPL, into a binary format) restricts:

- **File access**: apps can only read/write their own container (`/var/mobile/Containers/Data/Application/<UUID>/`). Subdirectories: `Documents/`, `Library/`, `tmp/`.
- **Network access**: most apps can make outbound connections but not listen on arbitrary ports.
- **IPC**: restricted Mach port access. Apps cannot look up arbitrary Mach services.
- **Hardware**: camera, microphone, location, contacts, photos -- each requires a corresponding entitlement and user consent (TCC -- Transparency, Consent, and Control framework).

**System processes** have more permissive profiles but are still sandboxed. The kernel enforces the sandbox via `Sandbox.kext` (the MACF -- Mandatory Access Control Framework -- policy module). Sandbox extensions (`sandbox_extension_issue_file()`) allow temporary, scoped permission grants -- e.g., a file picker grants the app read access to a specific path via an extension token.

**Container structure:**

```
/var/mobile/Containers/
  Data/Application/<UUID>/          # App data container
    Documents/                       # User-visible documents
    Library/Caches/                  # Cache (may be purged)
    Library/Preferences/             # NSUserDefaults plists
    tmp/                             # Temporary files
  Bundle/Application/<UUID>/         # App bundle (read-only)
    AppName.app/
      AppName                        # Mach-O executable
      embedded.mobileprovision       # Provisioning profile
      Info.plist                     # App metadata
```

**Sandbox escape**: requires a kernel vulnerability (the sandbox is enforced at the kernel level). Common vectors: IOKit driver bugs exposing kernel attack surface from within the sandbox, XPC service vulnerabilities in privileged daemons, and Mach message parsing bugs.

### 1.4 Data Protection classes

iOS encrypts every file on the filesystem with a per-file key, which is wrapped by a class key tied to the device state. Four classes exist:

**NSFileProtectionComplete** (`Class A`): file is accessible only when the device is unlocked. The class key is derived from the user's passcode and the device UID key. When the device locks, the class key is purged from memory. Use case: sensitive user data (health records, financial data, authentication tokens). This is the recommended default for app data.

**NSFileProtectionCompleteUnlessOpen** (`Class B`): file can be created while locked (the file key is wrapped with an asymmetric key -- the public half remains in memory for wrapping new file keys), but can only be read when unlocked. Use case: mail attachments downloading in background, photo captures from background processes.

**NSFileProtectionCompleteUntilFirstUserAuthentication** (`Class C`): file is accessible after the user unlocks the device once after boot. The class key remains in memory until the device restarts. This is the **default** class for files that do not specify a protection level. Use case: app databases that need background access, push notification data.

**NSFileProtectionNone** (`Class D`): file is always accessible. The class key is protected only by the device UID -- no passcode derivation. Use case: system files required during boot before any user authentication. Apps should never use this class for sensitive data.

**Exploitation**: on a jailbroken device with BFU (Before First Unlock) access, only Class D files are readable. After first unlock (AFU state), Classes C and D are accessible. Full filesystem dumps (checkm8-based acquisition) capture the encrypted files; decryption requires the class keys, which in turn require the passcode (for Class A/B) or AFU state (for Class C).

**Setting the class programmatically:**

```swift
// Swift -- setting protection on file creation
try data.write(to: fileURL, options: .completeFileProtection)

// Or via FileManager attributes
try FileManager.default.setAttributes(
    [.protectionKey: FileProtectionType.complete],
    ofItemAtPath: filePath
)
```

[MSTG-STORAGE-1, MSTG-STORAGE-2]

### 1.5 Keychain and access controls

**Keychain Services** stores credentials, keys, and small secrets encrypted by the SEP's hardware key hierarchy. Each Keychain item has:

- **Access group** (`kSecAttrAccessGroup`): defines which apps can access the item. Apps in the same Keychain Access Group (configured via the `keychain-access-groups` entitlement in the app's provisioning profile) can share items. The group ID format: `<TeamID>.<group-name>`.
- **Accessibility attribute**: controls when the item is decryptable:
  - `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` -- accessible only when unlocked, not included in backups
  - `kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly` -- accessible after first unlock, not in backups
  - `kSecAttrAccessibleWhenUnlocked` -- when unlocked, migrates with backups
  - `kSecAttrAccessibleAfterFirstUnlock` -- after first unlock, migrates with backups
  - `kSecAttrAccessibleAlways` -- deprecated, equivalent to None protection
- **Access control** (`SecAccessControl`): additional constraints including biometric (`kSecAccessControlBiometryCurrentSet`, `kSecAccessControlBiometryAny`), passcode (`kSecAccessControlDevicePasscode`), and combinations.

**Hardware-backed items**: on devices with SEP, items marked with `kSecAttrTokenIDSecureEnclave` have their cryptographic operations performed inside the SEP. The key material never leaves the SEP. Even a full filesystem dump cannot extract these keys.

**Keychain dumping** (jailbroken device):

```bash
# Using keychain-dumper (requires root on jailbroken device)
./keychain-dumper -a  # Dump all accessible keychain items

# Using objection
objection -g com.example.app explore
# Inside objection REPL:
ios keychain dump
ios keychain dump --json  # JSON output for processing
```

[MSTG-STORAGE-1]

### 1.6 Secure Enclave Processor (SEP)

The SEP is a separate ARM-based processor (with its own L4-based microkernel, **SepOS**) running in an isolated security domain with its own encrypted memory bus (the AP cannot read SEP memory even with kernel access). The SEP handles:

- **Biometric processing**: Touch ID / Face ID template matching runs entirely within the SEP. Biometric templates are encrypted and stored in a dedicated region accessible only to SepOS.
- **Key management**: the device's UID key (fused during manufacturing, unknown to Apple) is accessible only to the SEP's AES engine. All Data Protection class keys are derived from the UID key. The SEP performs key derivation and unwrapping for file decryption.
- **Passcode verification**: the SEP enforces passcode attempt limits and escalating delays. After 10 failed attempts (if configured), the SEP triggers effaceable-storage wipe. The AP cannot bypass these limits.
- **Apple Pay**: Secure Element (SE) communication for payment tokenization routes through the SEP.
- **Secure Neural Engine** (A14+): on newer SoCs, the Neural Engine has a secure mode where Face ID processing runs with hardware isolation.

**Effaceable storage**: a dedicated NAND region that the SEP can erase atomically. Contains the wrapped filesystem key hierarchy. Erasing it ("effacing") renders all user data cryptographically unrecoverable in milliseconds -- this is the mechanism behind "Erase All Content and Settings."

**SEP attack surface**: the SEP communicates with the AP via a hardware mailbox (shared memory region with interrupt-based signaling). The SEPOS system calls exposed to the AP (via the `sep-filter` driver) represent the attack surface. Research by Pangu and others has demonstrated SEP vulnerabilities (e.g., the `sepos` exploit used in some jailbreaks to bypass biometric checks), but exploitation requires first achieving kernel code execution on the AP side.

**SEP firmware analysis**: SEP firmware (SEPOS) is encrypted and signed separately. The `img4tool` and `sepsplit` utilities can extract the SEP firmware from IPSW files for analysis. The SEP firmware blob is located in the `Firmware/all_flash/` directory of the IPSW.

### 1.7 Trust Cache

The Trust Cache is a precomputed list of CDHashes (Code Directory Hashes) for all Apple-signed system binaries. It is loaded into kernel memory during boot and is used by AMFI for fast signature verification of system processes -- instead of performing full CMS signature verification for every system binary, AMFI checks if the CDHash appears in the Trust Cache.

**Static Trust Cache**: embedded in the kernelcache, contains CDHashes of binaries in the root filesystem. Loaded at boot, immutable at runtime.

**Loadable Trust Cache**: introduced in iOS 12, allows dynamically loading additional CDHashes (used for cryptex -- the sealed mount volumes for rapid security updates). The `trustcache` tool can parse and inspect Trust Cache files.

**Exploitation relevance**: jailbreaks that patch the Trust Cache can add CDHashes of unsigned binaries, allowing them to pass AMFI checks without disabling code signing entirely. This is the mechanism used by rootless jailbreaks like Dopamine -- instead of patching AMFI, they inject CDHashes into the Trust Cache.

### 1.8 Runtime protections

**PPL (Page Protection Layer)**: on A12+, PPL is a hardware-enforced separation between the kernel and page-table management. The kernel cannot modify page tables directly -- it must invoke PPL routines (running at a higher privilege level within EL1) that validate all page-table modifications. PPL ensures:
- No writable+executable pages can be created (W^X enforcement at the page-table level)
- Code signing cannot be bypassed by remapping pages
- The kernel's own code pages remain immutable

PPL is enforced by APRR (see below) register locks that the kernel itself cannot modify.

**APRR (Alternative Page-table Root Register)**: Apple's custom page-table permission remapping hardware. APRR allows the kernel to have different effective permissions than what the page tables specify, controlled by a register that only PPL can modify. This creates a privilege split within EL1: the kernel runs with APRR-restricted permissions, while PPL code runs with full page-table access.

**KTRR (Kernel Text Read-only Region)**: on A10+, KTRR locks the kernel's text segment read-only at the hardware level after boot. The memory controller enforces this -- not page tables. Even a kernel exploit cannot modify kernel code in memory. The KTRR range is configured by iBoot and locked before kernel execution.

**W^X enforcement**: iOS strictly enforces that no page is simultaneously writable and executable. The only exception is the JIT region for Safari's JavaScriptCore (which has the `dynamic-codesigning` entitlement and `com.apple.private.security.jit` entitlement). Third-party apps cannot JIT. The `MAP_JIT` flag for `mmap()` is available but only creates a region that can toggle between writable and executable (never both simultaneously), and only for apps with the JIT entitlement.

**PAC (Pointer Authentication Codes)**: on A12+, ARM's Pointer Authentication extension signs and verifies pointers using a device-specific key. Implementation:
- Return addresses on the stack are signed with the `PACIA` instruction (A-key, instruction context)
- Function pointers are signed with context (typically the storage address)
- vtable pointers are signed
- The `AUTIA`/`AUTIB` instructions verify signatures before use
- On A15+/M2+, FEAT_FPAC raises a synchronous fault on authentication failure (earlier chips silently corrupt the pointer, which crashes later -- a timing side-channel)
- Keys: APIA/APIB (instruction), APDA/APDB (data), APGA (generic) -- each is a 128-bit key stored in system registers

---

## 2. iOS exploitation

### 2.1 Kernel exploitation techniques

**IOKit attack surface**: IOKit is the driver framework for iOS/macOS. Drivers expose userspace-accessible interfaces via `IOConnectCallMethod()`, `IOConnectCallScalarMethod()`, and related APIs. The IOKit object hierarchy (IOService -> IOUserClient -> driver-specific subclasses) provides a large attack surface because:
- Many IOKit drivers process complex structured input from userspace
- Type confusion between IOUserClient subclasses is common
- Use-after-free in IOKit object lifecycle management is a recurring bug class

**Common kernel exploit patterns:**

1. **IOKit UAF (Use-After-Free)**: the most common iOS kernel exploit class. An IOKit driver's `IOUserClient` subclass frees an object while a reference still exists. The attacker reallocates the freed memory with controlled content (heap spray via `IOSurface`, `OSData`, or Mach messages), achieving type confusion and eventually kernel read/write. Example: CVE-2021-30883 (IOMobileFrameBuffer UAF, exploited in the wild by NSO Group).

2. **XPC deserialization**: XPC (the IPC mechanism for Apple services) deserializes structured messages. Bugs in XPC message parsing in privileged daemons (running as root or with entitlements) can lead to memory corruption. The attacker sends a malformed XPC message from a sandboxed app to a privileged XPC service.

3. **MIG (Mach Interface Generator) vulnerabilities**: MIG generates stub code for Mach message processing. The generated code is notoriously error-prone in handling complex message types. Out-of-bounds reads/writes in MIG-generated message parsing have been a source of kernel vulnerabilities.

4. **Mach message heap spray**: Mach messages (`mach_msg()`) can carry OOL (out-of-line) data that is allocated in the kernel heap. By sending many Mach messages with controlled OOL data sizes, the attacker can groom the kernel heap to position controlled data adjacent to a vulnerable object (heap feng shui). The `kalloc` zones (segregated by size) require precise control of allocation sizes.

**Kernel read/write primitives**: once an initial corruption (UAF, overflow) is achieved, the attacker typically:
1. Achieves an arbitrary read by corrupting an `OSData` or `IOSurface` property object to point to the target address
2. Achieves an arbitrary write via the same mechanism or through `copyin`/`copyout` confusion
3. Finds the kernel slide (KASLR defeat) by reading known kernel addresses
4. Locates the current process's `proc` structure and `ucred` structure
5. Patches `ucred` to set UID 0 (root) and clear sandbox flags

### 2.2 PAC bypass techniques

**PACMAN (CVE-2022-32894 context)**: researchers demonstrated that PAC can be bypassed via speculative execution. The attack uses a timing side-channel to brute-force PAC values: speculatively execute `AUT*` instructions with candidate PAC values and measure cache timing to determine which succeeded. On pre-FEAT_FPAC chips (A12-A14), a failed PAC authentication silently corrupts the pointer (no fault), enabling speculative execution to continue with the corrupted pointer. The speculative execution window reveals whether the PAC was correct via cache side-channels.

**Signing gadgets**: PAC signs pointers with a context value (typically the pointer's storage address). If the attacker can find a code sequence ("gadget") that:
1. Loads a pointer from an attacker-controlled address
2. Authenticates it with a context the attacker knows
3. Uses the authenticated pointer (call, branch)

...then the attacker can forge PAC-signed pointers. The exploit: find a kernel code path that authenticates and uses a pointer stored at a known address, replace the stored pointer with an attacker-chosen value signed with the correct key and context.

**PAC key reuse**: in some kernel versions, the A-key (APIA) used for return-address signing is the same across all kernel threads. If the attacker can leak the key (e.g., from a different vulnerability), they can forge PAC signatures for any kernel pointer.

**FEAT_FPAC mitigation** (A15+, M2+): PAC authentication failure raises a synchronous fault immediately, closing the speculative-execution window. This renders PACMAN-style attacks infeasible on newer hardware.

### 2.3 KTRR/APRR bypass

**KTRR bypass**: KTRR protects the kernel text segment from modification. Bypass strategies:
- **Data-only attacks**: instead of modifying kernel code, modify kernel data structures (process credentials, page tables, Trust Cache entries). This is the dominant modern approach.
- **JIT page abuse**: if the attacker can gain access to the JIT page-mapping mechanism (normally restricted to `com.apple.WebKit.WebContent`), they can map writable pages as executable outside the KTRR-protected region.
- **Return-oriented programming (ROP)**: chain existing kernel code sequences to perform arbitrary operations without modifying kernel text.

**APRR bypass**: APRR prevents the kernel from modifying page-table permissions (only PPL code can). Modern jailbreaks typically do not bypass APRR directly -- instead, they use data-only attacks that do not require page-table modification:
- Patch the Trust Cache to add new CDHashes (rootless jailbreaks)
- Patch process credentials for privilege escalation
- Modify MAC policy data structures to relax sandbox restrictions

### 2.4 Userland exploitation

**WebKit JIT bugs**: Safari's JavaScriptCore JIT compiler is the primary userland attack surface because:
- It is the only component allowed to generate executable code at runtime (JIT entitlement)
- It processes untrusted input (JavaScript from the web)
- JIT compilation is inherently complex, creating optimization bugs (type confusion, bounds-check elimination, register allocation errors)
- Successful WebKit exploitation provides code execution in the `com.apple.WebKit.WebContent` process, which is sandboxed but has the JIT entitlement

**iMessage zero-click exploitation**: iMessage processes complex media without user interaction, making it the highest-value zero-click attack surface:
1. **NSKeyedArchiver deserialization**: iMessage attachments are deserialized using `NSKeyedUnarchiver`, which instantiates Objective-C objects from serialized data. Malformed archives can trigger use-after-free, type confusion, or integer overflow in the deserialization process.
2. **Image/media parsing**: PDF, GIF, HEIF, and other media parsers run in `imagent` or `IMTranscoderAgent`. Memory corruption in these parsers provides code execution.
3. **BlastDoor** (iOS 14+): Apple introduced BlastDoor, a tightly sandboxed service (`BlastDoor.framework`) that pre-processes iMessage content in a restricted sandbox before it reaches the main iMessage process. BlastDoor is written in Swift (reducing memory-safety bugs) and runs in a minimal sandbox profile.

**PDF parsing (CVE-2021-30860 -- FORCEDENTRY)**: NSO Group's FORCEDENTRY exploit used a malicious PDF containing a JBIG2-encoded image. The JBIG2 decoder in CoreGraphics had an integer overflow vulnerability that allowed the attacker to construct a Turing-complete virtual machine within JBIG2's logical operations, achieving arbitrary code execution from a single PDF attachment -- bypassing BlastDoor by targeting `IMTranscoderAgent` (which processes attachments before BlastDoor in the delivery pipeline).

### 2.5 Jailbreak taxonomy

**Untethered**: survives reboot without external tools. The exploit is persisted on the device (typically in a system daemon or boot script). Rare in modern iOS. Example: untethered jailbreaks for older iOS versions (evasi0n for iOS 6/7).

**Semi-tethered**: requires a computer to re-jailbreak after each reboot, but the device can boot into a non-jailbroken state without a computer. Example: checkra1n (uses checkm8 BootROM exploit, requires connecting to a computer in DFU mode to re-exploit after reboot).

**Semi-untethered**: the device boots normally, and the user re-runs a jailbreak app (sideloaded or installed via TrollStore) to re-exploit. No computer needed after initial installation. Examples:
- **unc0ver** (iOS 11-14): used various kernel vulnerabilities (different exploits per iOS version), patched AMFI, sandbox, and installed Cydia/Substitute
- **Taurine** (iOS 14): kernel exploit with libhooker for tweak injection
- **Dopamine** (iOS 15, A12+): rootless jailbreak using kernel vulnerabilities. Does not remount the system partition writable -- uses a separate overlay and Trust Cache injection for code signing bypass

**Rootful vs rootless**: rootful jailbreaks remount `/` as read-write and modify the system partition. Rootless jailbreaks (Dopamine, modern palera1n configurations) leave the system partition intact and operate from `/var/jb/` -- modifying only the data partition and injecting into the Trust Cache.

### 2.6 Bootrom exploits

**checkm8 (CVE-2019-8900)**: a use-after-free vulnerability in the USB DFU (Device Firmware Update) mode handler of the BootROM on A5 through A11 chips. The vulnerability:

1. During DFU mode, the device receives a firmware image over USB in chunks
2. The DFU handler allocates a buffer for the image data
3. If the transfer is aborted (USB reset) at a specific point, the buffer is freed but the pointer is not cleared
4. A subsequent DFU request reuses the freed buffer (use-after-free)
5. The attacker sends crafted data that overlaps with the freed allocation, achieving code execution in the BootROM context

**Implications**: because the BootROM is in read-only silicon, checkm8 is unpatchable on affected devices. It provides:
- Permanent tethered code execution at boot time (highest privilege level)
- Ability to boot unsigned/modified kernels
- Foundation for checkra1n and palera1n jailbreaks
- Used by forensic tools (Cellebrite, GrayKey, palera1n-based acquisition) for full filesystem extraction

**palera1n**: combines checkm8 (BootROM entry on A8-A11) with kernel exploits for a semi-tethered jailbreak on iOS 15+. Process: DFU mode -> checkm8 exploit -> boot patched kernel -> achieve kernel r/w -> install jailbreak environment. Supports both rootful and rootless modes.

---

## 3. iOS app security testing

### 3.1 IPA extraction and analysis

An iOS app is distributed as an IPA (a ZIP archive). Contents: the Mach-O executable (ARM64, encrypted with FairPlay DRM for App Store apps), `Frameworks/` (embedded frameworks), `embedded.mobileprovision`, `Info.plist`, and asset bundles.

**Decryption methods** (requires jailbroken device):

```bash
# frida-ios-dump -- dumps decrypted IPA from memory
# Setup: pip3 install frida-tools, install frida-server on device
python3 dump.py com.example.targetapp

# bfdecrypt -- Cydia/Sileo tweak, writes decrypted binary to disk
# Install via package manager on jailbroken device
# Decrypted IPA appears in /var/mobile/Containers/Data/Application/<UUID>/Documents/

# CrackerXI+ -- GUI tool on jailbroken device
# Tap the app in CrackerXI, select "Full IPA"
```

**Binary analysis after decryption:**

```bash
# class-dump -- extract Objective-C class interfaces
class-dump -H TargetApp -o headers/

# class-dump-z -- faster alternative with Swift partial support
class-dump-z TargetApp > classes.txt

# jtool2 -- Mach-O analysis
jtool2 --ent TargetApp              # Extract entitlements
jtool2 -l TargetApp                 # Load commands
jtool2 -S TargetApp                 # Symbol table
jtool2 -d __DATA.__objc_classlist TargetApp  # ObjC class list

# otool -- Apple's Mach-O tool
otool -L TargetApp                  # Linked libraries
otool -l TargetApp | grep -A2 LC_ENCRYPTION  # Check encryption
```

**MobSF (Mobile Security Framework)**: automated static/dynamic analysis.

```bash
# Static analysis (no jailbreak required -- works on decrypted IPA)
# Upload IPA to MobSF web interface (default: http://localhost:8000)
# MobSF extracts: Info.plist analysis, binary security flags (PIE, stack
# canary, ARC), URL schemes, permissions, hardcoded strings, API keys

# Checks performed:
# - Binary protections: PIE, stack canary, ARC, stripped symbols
# - Transport security: ATS configuration, cleartext traffic
# - Embedded secrets: API keys, tokens in strings/plists
# - URL scheme registration: potential hijacking vectors
# - Entitlement analysis: excessive permissions
```

[MSTG-CODE-1, MSTG-CODE-2, MSTG-RESILIENCE-1]

### 3.2 Frida on iOS

**Setup on jailbroken device:**

```bash
# Install Frida server via Sileo/Cydia (palera1n or Dopamine jailbreak)
# Add Frida repository: https://build.frida.re
# Install "Frida" package

# Verify from host machine
frida-ls-devices                     # List connected devices
frida-ps -U                          # List running processes on USB device
frida-ps -Uai                        # List all installed apps
```

**Hooking Objective-C methods:**

```javascript
// Frida script: hook NSURLSession to log all HTTP requests
// Save as log_requests.js, run with: frida -U -f com.example.app -l log_requests.js

var NSURLSession = ObjC.classes.NSURLSession;

Interceptor.attach(
  NSURLSession['- dataTaskWithRequest:completionHandler:'].implementation,
  {
    onEnter: function(args) {
      var request = new ObjC.Object(args[2]);
      console.log('[NSURLSession] ' + request.HTTPMethod() + ' ' + request.URL().absoluteString());
      var headers = request.allHTTPHeaderFields();
      if (headers) {
        console.log('  Headers: ' + headers.toString());
      }
      var body = request.HTTPBody();
      if (body) {
        var bodyStr = ObjC.classes.NSString.alloc().initWithData_encoding_(body, 4); // NSUTF8
        console.log('  Body: ' + bodyStr.toString());
      }
    }
  }
);
```

**Hooking Swift methods:**

```javascript
// Swift methods are name-mangled. Find them first:
// frida-trace -U -f com.example.app -m "*[ClassName *]"

// Or search with Module.enumerateExports:
Module.enumerateExports("TargetApp", {
  onMatch: function(exp) {
    if (exp.name.indexOf("LoginManager") !== -1) {
      console.log("Found: " + exp.name + " at " + exp.address);
    }
  },
  onComplete: function() {}
});

// Hook by address after finding the mangled name:
var targetAddr = Module.findExportByName("TargetApp", "$s9TargetApp12LoginManagerC12authenticateySbSSF");
if (targetAddr) {
  Interceptor.attach(targetAddr, {
    onEnter: function(args) {
      console.log("[LoginManager.authenticate] called");
      // args[0] = self, args[1] = password (Swift String)
    },
    onLeave: function(retval) {
      console.log("[LoginManager.authenticate] returned: " + retval);
      // Bypass: retval.replace(ptr(1));  // Force return true
    }
  });
}
```

**Bypassing jailbreak detection:**

```javascript
// Common jailbreak detection checks and bypasses
// Hook NSFileManager to hide jailbreak artifacts

var NSFileManager = ObjC.classes.NSFileManager;

Interceptor.attach(
  NSFileManager['- fileExistsAtPath:'].implementation,
  {
    onEnter: function(args) {
      this.path = new ObjC.Object(args[2]).toString();
    },
    onLeave: function(retval) {
      var dominated = [
        '/Applications/Cydia.app',
        '/Applications/Sileo.app',
        '/usr/sbin/sshd',
        '/usr/bin/ssh',
        '/var/jb',
        '/private/var/jb',
        '/usr/libexec/cydia',
        '/etc/apt',
        '/private/var/lib/apt'
      ];
      for (var i = 0; i < dominated.length; i++) {
        if (this.path.indexOf(dominated[i]) !== -1) {
          retval.replace(ptr(0x0));  // Return NO
          console.log('[JB Bypass] Hidden: ' + this.path);
          break;
        }
      }
    }
  }
);
```

[MSTG-RESILIENCE-1, MSTG-RESILIENCE-2]

### 3.3 SSL/TLS pinning

**App Transport Security (ATS)**: iOS 9+ enforces HTTPS by default via ATS. Configuration in `Info.plist`:

```xml
<!-- Strict ATS (recommended) -- no exceptions -->
<key>NSAppTransportSecurity</key>
<dict/>

<!-- Common misconfiguration -- disabling ATS globally -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>  <!-- INSECURE: allows all cleartext HTTP -->
</dict>

<!-- Per-domain exception (acceptable for legacy APIs) -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSExceptionDomains</key>
    <dict>
        <key>legacy-api.example.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.2</string>
        </dict>
    </dict>
</dict>
```

**Implementing certificate pinning (NSURLSession):**

```swift
class PinnedSessionDelegate: NSObject, URLSessionDelegate {
    let pinnedCertificateHash = "sha256/XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX="

    func urlSession(_ session: URLSession,
                    didReceive challenge: URLAuthenticationChallenge,
                    completionHandler: @escaping (URLSession.AuthChallengeDisposition, URLCredential?) -> Void) {
        guard let serverTrust = challenge.protectionSpace.serverTrust,
              let serverCert = SecTrustGetCertificateAtIndex(serverTrust, 0) else {
            completionHandler(.cancelAuthenticationChallenge, nil)
            return
        }
        let serverCertData = SecCertificateCopyData(serverCert) as Data
        let serverHash = sha256(data: serverCertData)
        if serverHash == pinnedCertificateHash {
            completionHandler(.useCredential, URLCredential(trust: serverTrust))
        } else {
            completionHandler(.cancelAuthenticationChallenge, nil)
        }
    }
}
```

**TrustKit integration** (production-grade pinning library):

```swift
// AppDelegate -- configure TrustKit
let trustKitConfig: [String: Any] = [
    kTSKSwizzleNetworkDelegates: true,
    kTSKPinnedDomains: [
        "api.example.com": [
            kTSKEnforcePinning: true,
            kTSKIncludeSubdomains: true,
            kTSKPublicKeyHashes: [
                "sha256/primary-pin-hash-base64==",
                "sha256/backup-pin-hash-base64=="
            ],
            kTSKReportUris: ["https://report.example.com/pinning"]
        ]
    ]
]
TrustKit.initSharedInstance(withConfiguration: trustKitConfig)
```

**SSL pinning bypass methods:**

```bash
# Method 1: objection (automated, covers most implementations)
objection -g com.example.app explore
# Inside REPL:
ios sslpinning disable

# Method 2: Frida script -- bypass SecTrustEvaluate family
# Save as ssl_bypass.js
```

```javascript
// ssl_bypass.js -- comprehensive SSL pinning bypass
// Hooks multiple pinning implementations

// Bypass SecTrustEvaluateWithError (iOS 12+)
var SecTrustEvaluateWithError = Module.findExportByName("Security", "SecTrustEvaluateWithError");
if (SecTrustEvaluateWithError) {
  Interceptor.attach(SecTrustEvaluateWithError, {
    onLeave: function(retval) {
      retval.replace(ptr(1));  // Return true (trusted)
      console.log("[SSL Bypass] SecTrustEvaluateWithError -> true");
    }
  });
}

// Bypass SecTrustEvaluate (legacy)
var SecTrustEvaluate = Module.findExportByName("Security", "SecTrustEvaluate");
if (SecTrustEvaluate) {
  Interceptor.attach(SecTrustEvaluate, {
    onLeave: function(retval) {
      retval.replace(ptr(0));  // errSecSuccess
    }
  });
}

// Bypass NSURLSession delegate pinning
var resolver = ObjC.classes.NSURLSession;
if (resolver) {
  var orig = resolver['- dataTaskWithRequest:completionHandler:'];
  // Hook URLSession:didReceiveChallenge:completionHandler:
  try {
    var NSURLSessionDelegateClass = ObjC.classes.__NSCFURLSessionConnection;
    // Additional hooks as needed for the app's specific implementation
  } catch(e) {}
}
```

```bash
# Method 3: SSL Kill Switch 2 (jailbreak tweak)
# Install via Cydia/Sileo repository
# Hooks all TLS validation at the Security.framework level
# Toggle per-app in Settings.app

# Method 4: Manual proxy configuration with Burp/mitmproxy
# Export Burp CA -> install on device via Settings -> Profile
# Set device proxy to host machine IP:8080
# ATS exceptions or ssl bypass needed for pinned apps
```

[MSTG-NETWORK-1, MSTG-NETWORK-2, MSTG-NETWORK-3]

### 3.4 Data storage analysis

**Keychain dumping:**

```bash
# objection
objection -g com.example.app explore
ios keychain dump
ios keychain dump --json

# keychain-dumper (requires root on jailbroken device)
# Clone: https://github.com/ptoomey3/Keychain-Dumper
./keychain-dumper -a        # All accessible items
./keychain-dumper -e         # Entitlement-filtered dump
```

**Plist file analysis:**

```bash
# Locate app's plist files
find /var/mobile/Containers/Data/Application/ -name "*.plist" 2>/dev/null

# Read NSUserDefaults (stored as plist)
# Path: <AppContainer>/Library/Preferences/com.example.app.plist
plutil -p com.example.app.plist

# Using objection
objection -g com.example.app explore
ios plist cat com.example.app.plist
env  # Shows container paths
```

**SQLite database extraction:**

```bash
# Locate databases
find /var/mobile/Containers/Data/Application/<UUID>/ -name "*.sqlite" -o -name "*.db" 2>/dev/null

# Copy and analyze
scp root@<device>:/path/to/database.sqlite ./
sqlite3 database.sqlite
.tables
.schema <table_name>
SELECT * FROM <table_name> LIMIT 10;

# Using objection
objection -g com.example.app explore
sqlite connect /var/mobile/Containers/Data/Application/<UUID>/Library/database.sqlite
```

**Core Data inspection**: Core Data uses SQLite as the persistent store by default. The database file (typically `<AppName>.sqlite` with `-wal` and `-shm` companion files) is in the app's `Library/Application Support/` directory. Schema is discoverable via the `.sqlite` file; managed-object-model entities map to tables.

**Realm database:**

```bash
# Realm databases are stored as .realm files
find /var/mobile/Containers/Data/Application/<UUID>/ -name "*.realm" 2>/dev/null

# If unencrypted, open with Realm Studio (desktop app)
# If encrypted, the 64-byte key may be stored in:
#   - Keychain (best practice)
#   - Hardcoded in binary (common mistake -- extract via strings/Frida)
#   - NSUserDefaults (insecure)
```

**NSUserDefaults secrets** (common vulnerability):

```javascript
// Frida script: dump all NSUserDefaults for the app
var defaults = ObjC.classes.NSUserDefaults.standardUserDefaults();
var dict = defaults.dictionaryRepresentation();
console.log(dict.toString());
// Look for: api_key, token, secret, password, session, auth
```

**Binary cookies:**

```bash
# Safari and WKWebView cookies stored in binary format
find /var/mobile/Containers/Data/Application/<UUID>/ -name "Cookies.binarycookies" 2>/dev/null
# Parse with BinaryCookieReader.py or objection
```

[MSTG-STORAGE-1, MSTG-STORAGE-2, MSTG-STORAGE-3, MSTG-STORAGE-4, MSTG-STORAGE-5]

---

## 4. IPC and URL schemes

### 4.1 Universal Links vs custom URL schemes

**Custom URL schemes** (`myapp://`): registered in `Info.plist` under `CFBundleURLTypes`. Security issue: **URL scheme hijacking** -- if multiple apps register the same scheme, iOS does not guarantee which app handles the URL. A malicious app can register a victim's URL scheme and intercept sensitive data (OAuth callbacks, deep links with tokens).

```xml
<!-- Info.plist -- URL scheme registration -->
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>myapp</string>
        </array>
    </dict>
</array>
```

**Universal Links** (iOS 9+): associate a domain with the app via an `apple-app-site-association` (AASA) file hosted at `https://example.com/.well-known/apple-app-site-association`. Universal Links are verified by Apple (the AASA file must be served over HTTPS from the verified domain), preventing hijacking. Universal Links should be used instead of custom URL schemes for OAuth callbacks and sensitive deep links.

```json
// apple-app-site-association
{
  "applinks": {
    "details": [{
      "appIDs": ["TEAMID.com.example.app"],
      "components": [
        { "/": "/auth/callback", "comment": "OAuth callback" },
        { "/": "/invite/*", "comment": "Invitation links" }
      ]
    }]
  }
}
```

### 4.2 URL scheme hijacking attack

**Attack**: attacker publishes a malicious app that registers the same URL scheme as the target app. When a web page or another app calls `openURL:` with the scheme, iOS may route the request to the malicious app, which receives the full URL including query parameters (OAuth tokens, reset codes, session identifiers).

**Detection**: `ios url-scheme list` in objection enumerates registered URL schemes. `ideviceinstaller -l -o list_all` lists installed apps and their schemes.

**Defense**: use Universal Links for all security-sensitive flows (OAuth redirects, password resets). Validate the source of incoming URLs. Use `UIApplication.open(_:options:completionHandler:)` with `universalLinksOnly: true` when opening links.

[MSTG-PLATFORM-1, MSTG-PLATFORM-3]

### 4.3 App Extensions and App Groups

**App Extensions** (Today widgets, Share extensions, keyboard extensions, notification extensions) run in separate processes with their own sandbox. Data sharing between the host app and extensions uses **App Groups** -- a shared container identified by a group ID (format: `group.com.example.app`).

**Security implications**:
- Data written to the App Group container is accessible to all apps/extensions in the group
- A compromised extension can read/write the shared container
- Keyboard extensions with `RequestsOpenAccess` can access the network (data exfiltration risk from keystrokes)
- Notification Service Extensions can modify push notification content before display -- a compromised extension could alter financial alerts, 2FA codes, or suppress security notifications

```bash
# Inspect App Group containers
# Container path: /var/mobile/Containers/Shared/AppGroup/<UUID>/
find /var/mobile/Containers/Shared/AppGroup/ -maxdepth 2 -type f 2>/dev/null
```

### 4.4 XPC service exploitation

XPC services on iOS are identified by Mach service names (registered in `launchd`). Privileged system XPC services (running as root or with platform entitlements) are high-value targets:

- **Missing entitlement checks**: if a privileged XPC service does not verify the caller's entitlements, any sandboxed app can connect to it
- **Serialization vulnerabilities**: XPC message parsing bugs (type confusion, OOB reads) in privileged services
- **TOCTOU (Time-of-Check-Time-of-Use)**: race conditions in entitlement verification

```javascript
// Frida: enumerate available XPC/Mach services
var bootstrap = ObjC.classes.NSXPCConnection;
// List launchd-registered services accessible from the app's sandbox
var machPorts = ObjC.classes.NSMachPort;
console.log("[XPC] Enumerating accessible services...");
```

### 4.5 Pasteboard data leakage

`UIPasteboard.generalPasteboard` is shared across all apps. Sensitive data copied to the clipboard (passwords, tokens, credit card numbers) is accessible to any foreground app.

**iOS 14+ mitigation**: apps receive a notification banner ("App pasted from OtherApp") when accessing the pasteboard, and iOS 16+ restricts pasteboard access to the active app unless the user explicitly pastes.

**Detection:**

```javascript
// Frida: monitor pasteboard access
Interceptor.attach(
  ObjC.classes.UIPasteboard['- string'].implementation,
  {
    onLeave: function(retval) {
      if (retval.isNull()) return;
      var str = new ObjC.Object(retval).toString();
      console.log('[Pasteboard READ] ' + str);
    }
  }
);

Interceptor.attach(
  ObjC.classes.UIPasteboard['- setString:'].implementation,
  {
    onEnter: function(args) {
      var str = new ObjC.Object(args[2]).toString();
      console.log('[Pasteboard WRITE] ' + str);
    }
  }
);
```

[MSTG-PLATFORM-4, MSTG-STORAGE-10]

---

## 5. Network security on iOS

### 5.1 ATS configuration analysis

**Auditing ATS settings:**

```bash
# Extract Info.plist from IPA
unzip -o target.ipa -d extracted/
plutil -p extracted/Payload/TargetApp.app/Info.plist | grep -A 20 "NSAppTransportSecurity"

# Using objection on running app
objection -g com.example.app explore
ios info plist
```

**Common ATS misconfigurations:**
- `NSAllowsArbitraryLoads: true` -- disables ATS globally (allows cleartext HTTP everywhere)
- `NSAllowsLocalNetworking: true` -- allows cleartext to local (RFC 1918) addresses
- `NSExceptionMinimumTLSVersion: TLSv1.0` -- allows deprecated TLS versions
- `NSExceptionAllowsInsecureHTTPLoads: true` per domain -- allows cleartext to specific domains without justification

[MSTG-NETWORK-1, MSTG-NETWORK-2]

### 5.2 Proxy detection and bypass

Some apps implement proxy detection to prevent traffic interception:

```javascript
// Frida: bypass proxy detection
// Hook CFNetworkCopySystemProxySettings to return empty dict
var CFNetworkCopySystemProxySettings = Module.findExportByName(
  "CFNetwork", "CFNetworkCopySystemProxySettings"
);
if (CFNetworkCopySystemProxySettings) {
  Interceptor.attach(CFNetworkCopySystemProxySettings, {
    onLeave: function(retval) {
      // Replace with empty dictionary (no proxy configured)
      var empty = ObjC.classes.NSDictionary.dictionary();
      retval.replace(empty.handle);
      console.log("[Proxy Bypass] CFNetworkCopySystemProxySettings -> empty");
    }
  });
}
```

### 5.3 VPN API abuse

The `NEVPNManager` API (Network Extension framework) allows apps to configure and control VPN connections. Security concerns:
- Apps with the `com.apple.networking.vpn.api` entitlement can install VPN profiles
- A malicious VPN app routes all device traffic through its server (full traffic interception)
- `NEFilterDataProvider` (content filter) can inspect all HTTP/HTTPS traffic (if the user grants permission)
- Personal VPN apps do not require MDM -- any App Store app with the entitlement can install a VPN configuration

### 5.4 Wi-Fi and location harvesting

**CL Framework and SSID/BSSID access**:
- iOS 13+ restricts `CNCopyCurrentNetworkInfo()` to apps with the `com.apple.developer.networking.wifi-info` entitlement AND location permission
- Before iOS 13, any app could read the current Wi-Fi SSID and BSSID without user consent
- BSSID can be used for Wi-Fi-based geolocation without GPS (via databases like WiGLE)
- Apps cannot scan for nearby networks without the `com.apple.developer.networking.wifi-info` entitlement (private API on non-jailbroken devices)

### 5.5 Bonjour/mDNS service discovery

**`NSNetServiceBrowser`** and its replacement `NWBrowser` (Network framework) allow apps to discover services on the local network. iOS 14+ requires a `NSLocalNetworkUsageDescription` and user consent for local network access. Before iOS 14, apps could silently scan the local network via mDNS/Bonjour, discovering:
- Other devices and their services
- Printer names (organizational info)
- Smart home devices (occupancy inference)
- Development services (revealing debug/staging endpoints)

---

## 6. Spyware and zero-click exploitation

### 6.1 NSO Group Pegasus

Pegasus is a state-sponsored spyware platform targeting iOS and Android. Notable exploit chains:

**KISMET (2020)**: zero-click exploit targeting iMessage on iOS 13.x. Exploited a vulnerability in the iMessage media processing pipeline. Delivered via an invisible iMessage -- no notification displayed to the target. Discovered by Citizen Lab in attacks against journalists and activists.

**FORCEDENTRY (CVE-2021-30860)**: zero-click exploit targeting iOS 14.x. Mechanism:
1. Attacker sends an iMessage containing a malicious PDF attachment
2. The PDF contains a JBIG2-encoded image stream
3. The JBIG2 decoder in CoreGraphics (ImageIO framework) has an integer overflow in segment reference processing
4. The overflow is used to construct a logical circuit within JBIG2's region combination operations
5. This logical circuit implements a small virtual machine that achieves arbitrary read/write in the `IMTranscoderAgent` process
6. The exploit escapes the process sandbox via a kernel vulnerability
7. Pegasus implant is installed with full device access

FORCEDENTRY bypassed BlastDoor because `IMTranscoderAgent` (which performs media transcoding) processes attachments before they reach BlastDoor's sandbox. Apple patched CVE-2021-30860 in iOS 14.8 (September 2021).

**PWNYOURHOME (2022)**: zero-click exploit targeting HomeKit. Exploited a vulnerability in the HomeKit daemon (`homed`). The attacker sends a crafted HomeKit invitation that triggers a vulnerability in the daemon's image processing. This was notable because it targeted a different attack surface than the traditional iMessage vector.

**FINDMYPWN (2022)**: zero-click exploit targeting the Find My network. Exploited a vulnerability in the Find My daemon. Combined with a second exploit for privilege escalation and Pegasus installation.

**Pegasus capabilities** (post-exploitation):
- Full filesystem access (contacts, messages, emails, photos, call history)
- Real-time microphone and camera activation
- GPS location tracking
- Keychain credential extraction
- End-to-end-encrypted messaging content (reads from the device, bypassing E2E encryption)
- WhatsApp, Signal, Telegram message extraction (from the app's sandbox)
- iCloud credential theft (accessing cloud backups)

### 6.2 Predator/Cytrox

Predator (by Cytrox, part of the Intellexa alliance) is another commercial spyware platform. Delivery methods include:
- One-click links (SMS/WhatsApp phishing) exploiting WebKit vulnerabilities
- Documented use of CVE-2021-30883 (IOMobileFrameBuffer OOB write) and CVE-2021-30884 (WebKit vulnerability) in a multi-stage chain

Predator's loader is an automation-focused framework ("Alien") that sets up persistence and loads the main spyware payload. Unlike Pegasus, Predator has been documented using one-click delivery more frequently than zero-click.

### 6.3 QuaDream REIGN

QuaDream (Israeli company) developed the REIGN spyware platform. Used a zero-click iCalendar exploit (ENDOFDAYS) that exploited iCloud calendar invitation processing on iOS 14. The exploit:
1. Sends a backdated iCalendar invitation (set in the past so no notification is displayed)
2. The invitation triggers a vulnerability in the calendar processing daemon
3. Achieves code execution and installs the spyware payload

QuaDream shut down in 2023, but the techniques demonstrate that iMessage is not the only zero-click vector -- any daemon processing incoming data (calendar, HomeKit, Find My, AirDrop) is a potential attack surface.

### 6.4 iMessage zero-click methodology

**Attack surface**: iMessage processes incoming data through multiple daemons:
1. `apsd` (Apple Push Service daemon) receives the push notification
2. `imagent` (iMessage agent) processes the message metadata
3. `IMTranscoderAgent` transcodes media attachments
4. `BlastDoor` (iOS 14+) pre-processes message content in a restricted sandbox
5. `SpringBoard` renders the notification

**NSKeyedArchiver deserialization**: iMessage uses `NSKeyedUnarchiver` to deserialize message payloads. The serialization format allows specifying arbitrary Objective-C classes to instantiate. Attack: craft a serialized object graph that triggers a vulnerability during deserialization (type confusion, use-after-free in `initWithCoder:` implementations, unexpected side effects in property setters).

**BlastDoor protections**:
- Runs in a tight sandbox (no network access, limited filesystem access)
- Written primarily in Swift (reduces memory-safety vulnerabilities)
- Processes messages before they reach `imagent`
- Content passes through BlastDoor's parsing -- malformed content is rejected

**BlastDoor bypass**: FORCEDENTRY bypassed BlastDoor by targeting `IMTranscoderAgent`, which runs outside BlastDoor's sandbox and processes media attachments in a parallel pipeline. Apple subsequently moved more processing into BlastDoor-protected paths.

### 6.5 Lockdown Mode

**Lockdown Mode** (iOS 16+): an extreme protection mode designed to protect high-risk users from targeted spyware. When enabled:

- **Messages**: blocks most attachment types (only images allowed). Disables link previews. Blocks rich content rendering.
- **Web browsing**: disables JIT compilation in WebKit (significant performance impact but closes the JIT attack surface). Blocks WebRTC, WebGL, and other complex web features.
- **Apple services**: blocks incoming FaceTime calls from unknown contacts. Blocks HomeKit invitations from unknown sources. Blocks configuration profile installation. Blocks MDM enrollment.
- **Connectivity**: blocks wired connections (USB/Lightning) when the device is locked.
- **Network**: blocks certain 2G cellular capabilities on supported devices.
- **Shared albums**: disabled. Blocks incoming Find My requests from unknown devices.

**What Lockdown Mode does NOT block**: standard phone calls and SMS (these use the cellular baseband, not the application processor's attack surface), iMessage from known contacts (but with reduced functionality), standard app usage.

**Effectiveness analysis**: Lockdown Mode would have prevented FORCEDENTRY (blocks PDF attachments in iMessage), KISMET (blocks rich content), PWNYOURHOME (blocks HomeKit invitations from unknown sources), and ENDOFDAYS (blocks calendar invitations from unknown sources). It represents a significant reduction in zero-click attack surface at the cost of functionality.

---

## 7. MDM and enterprise security

### 7.1 Supervised vs unsupervised devices

**Unsupervised** (default consumer devices): MDM can enforce a subset of policies. The user must consent to MDM enrollment. The user can remove the MDM profile at any time (losing managed apps and configurations). MDM cannot: prevent profile removal, restrict App Store usage, enable global proxy, or perform remote wipe without consent.

**Supervised** (enrolled via Apple Configurator or DEP/ABM): MDM has full control. The device is marked as supervised during initial setup (activation). MDM can: prevent profile removal, restrict App Store, enforce global proxy, install/remove apps silently, enforce per-app VPN, restrict pasteboard between managed/unmanaged apps, enable content filtering, block specific websites, control system settings. Most enterprise security policies require supervision.

### 7.2 MDM profile analysis

MDM configuration profiles (`.mobileconfig`) are XML-format plist files that can be inspected:

```bash
# On macOS: inspect a mobileconfig profile
security cms -D -i profile.mobileconfig > decoded_profile.plist
plutil -p decoded_profile.plist

# On a jailbroken iOS device: examine installed profiles
ls /var/containers/Shared/SystemGroup/*/Library/ConfigurationProfiles/
# Or: /var/db/ConfigurationProfiles/
find / -name "*.mobileconfig" 2>/dev/null
```

**Example restrictive MDM profile (XML):**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>PayloadContent</key>
    <array>
        <!-- Restrictions payload -->
        <dict>
            <key>PayloadType</key>
            <string>com.apple.applicationaccess</string>
            <key>allowCamera</key>
            <false/>
            <key>allowScreenShot</key>
            <false/>
            <key>forceEncryptedBackup</key>
            <true/>
            <key>allowManagedAppsCloudSync</key>
            <false/>
            <key>allowOpenFromManagedToUnmanaged</key>
            <false/>
            <key>allowOpenFromUnmanagedToManaged</key>
            <false/>
            <key>allowUSBRestrictedMode</key>
            <true/>
        </dict>
        <!-- Passcode policy -->
        <dict>
            <key>PayloadType</key>
            <string>com.apple.mobiledevice.passwordpolicy</string>
            <key>minLength</key>
            <integer>8</integer>
            <key>requireAlphanumeric</key>
            <true/>
            <key>maxGracePeriod</key>
            <integer>0</integer>
            <key>maxFailedAttempts</key>
            <integer>5</integer>
            <key>minComplexChars</key>
            <integer>1</integer>
        </dict>
        <!-- Wi-Fi payload (WPA3 Enterprise) -->
        <dict>
            <key>PayloadType</key>
            <string>com.apple.wifi.managed</string>
            <key>SSID_STR</key>
            <string>CorpNet</string>
            <key>EncryptionType</key>
            <string>WPA3</string>
            <key>EAPClientConfiguration</key>
            <dict>
                <key>AcceptEAPTypes</key>
                <array><integer>13</integer></array>
                <key>TLSMinimumVersion</key>
                <string>1.2</string>
            </dict>
        </dict>
    </array>
    <key>PayloadType</key>
    <string>Configuration</string>
    <key>PayloadDisplayName</key>
    <string>Enterprise Security Policy</string>
    <key>PayloadIdentifier</key>
    <string>com.example.enterprise.security</string>
    <key>PayloadUUID</key>
    <string>A1B2C3D4-E5F6-7890-ABCD-EF1234567890</string>
    <key>PayloadVersion</key>
    <integer>1</integer>
</dict>
</plist>
```

### 7.3 DEP/ABM hijacking

**Device Enrollment Program (DEP)**, now **Apple Business Manager (ABM)**, automates MDM enrollment during device activation. A device is assigned to an organization by its serial number. During activation, the device contacts Apple's enrollment server, which directs it to the organization's MDM server.

**DEP hijacking attack** (documented by Duo Security research): if an attacker obtains a device serial number (from shipping records, physical access, or corporate asset databases) and the organization's MDM enrollment is not properly secured:
1. Attacker acquires a device with a known serial number assigned to the target organization
2. During activation, the device enrolls with the organization's MDM
3. If the MDM does not require additional authentication (certificate, user credential), the attacker's device receives the full MDM configuration including: Wi-Fi credentials, VPN configurations, certificates, managed app configurations (which may contain API keys or internal URLs)
4. The attacker now has credentials for the corporate network

**Mitigation**: require user authentication during MDM enrollment (SAML, LDAP integration), use client certificate authentication, monitor for unexpected enrollments.

### 7.4 Managed app configuration extraction

MDM-delivered app configurations (`com.apple.ManagedConfiguration`) can contain sensitive data:

```bash
# On jailbroken device: extract managed app config
# Managed configurations stored in:
# /var/containers/Shared/SystemGroup/*/Library/ConfigurationProfiles/MCProfileDataEntries/

# Using objection
objection -g com.example.managedapp explore
ios plist cat /path/to/managed-config.plist
```

**Common secrets found in managed app configs**: internal API endpoints, OAuth client secrets, certificate passphrases, VPN pre-shared keys, feature flags exposing debug/admin functionality.

### 7.5 Per-app VPN and content filtering

**Per-app VPN**: MDM can configure VPN tunnels that activate only for specific managed apps. This prevents corporate app traffic from traversing untrusted networks while allowing personal app traffic to flow directly.

**Content filter (NEFilterDataProvider)**: supervised devices can have MDM-installed content filters that inspect all HTTP/HTTPS traffic. The filter runs as a Network Extension and can see decrypted HTTPS content (because iOS routes traffic through the filter after TLS termination at the application layer). This is a privacy concern for personal devices with MDM.

---

## 8. iOS forensics

### 8.1 checkm8-based acquisition

For A5-A11 devices, checkm8 provides the most complete forensic acquisition:

```bash
# Using palera1n for forensic acquisition
# Step 1: Put device in DFU mode
# Step 2: Run palera1n to exploit BootROM and boot modified ramdisk
palera1n -D  # DFU helper

# Step 3: With SSH access to the device, extract filesystem
# Port forward via iproxy
iproxy 2222 22 &

# Step 4: Extract full filesystem
ssh -p 2222 root@localhost 'tar -cf - /var/mobile/' > mobile_data.tar
# Or use dedicated forensic agents (e.g., checkm8-agent scripts)
```

**Forensic implications of checkm8**:
- Provides access to BFU (Before First Unlock) data (Class D files, some system databases)
- After passcode entry (AFU): full filesystem access to Class A/B/C/D files
- Keychain extraction requires AFU state for most items
- Does not help with A12+ devices (checkm8 does not affect A12+)
- Cellebrite UFED Premium and GrayKey use checkm8 for supported devices

### 8.2 Logical acquisition

**libimobiledevice**: open-source library for communicating with iOS devices over USB. Key tools:

```bash
# ideviceinfo -- device information
ideviceinfo -u <UDID>
ideviceinfo -k DeviceName
ideviceinfo -k ProductVersion

# idevicebackup2 -- iTunes-style backup (logical acquisition)
# Unencrypted backup (if no backup password is set):
idevicebackup2 backup --full /path/to/output/

# Encrypted backup (preserves more data including Keychain):
idevicebackup2 backup --full /path/to/output/
# Note: encrypted backups include Keychain items marked with
# kSecAttrAccessibleWhenUnlocked (without ThisDeviceOnly flag)

# idevicecrashreport -- pull crash reports
idevicecrashreport -e /path/to/output/

# idevicesyslog -- real-time syslog
idevicesyslog

# ideviceprovision -- list provisioning profiles
ideviceprovision list
```

**Backup contents**: an iOS backup includes contacts, messages (SMS/iMessage), call history, photos, app data (for apps that allow backup), Safari bookmarks/history, Wi-Fi passwords (encrypted backups), Health data (encrypted backups), Keychain subset (encrypted backups).

**Backup encryption password**: if set, the backup password is stored as a hash in the device's Keychain (ironically, protected by the device passcode). Tools like `idevicebackup2` require the password. Forensic tools (Elcomsoft Phone Breaker) can attempt to crack backup passwords.

### 8.3 sysdiagnose analysis

`sysdiagnose` is a comprehensive diagnostic dump that can be triggered by:
- Pressing Volume Up + Volume Down + Power simultaneously for 1-2 seconds
- MDM command
- `sysdiagnose` command on jailbroken device

The resulting `.tar.gz` archive (typically 200-500 MB) contains:

- **system_logs.logarchive**: unified logging data (months of logs on modern devices)
- **ps.txt**: process list at time of collection
- **spindump/**: process stack traces
- **WiFi/**: Wi-Fi connection history, SSID list, BSSID associations
- **crashes/**: crash reports for all processes
- **logs/MobileInstallation/**: app installation/removal history
- **SystemConfiguration/**: network configuration, VPN profiles
- **powerlog/**: battery and power usage data (see section 8.6)

```bash
# Extract and analyze sysdiagnose on macOS/Linux
tar xzf sysdiagnose_*.tar.gz
# Parse unified log
log show --archive system_logs.logarchive --predicate 'process == "imagent"' --info
log show --archive system_logs.logarchive --predicate 'eventMessage CONTAINS "failed"' --info
```

### 8.4 Crash log interpretation

Crash reports (`*.ips` files) contain:
- Process name and PID
- Exception type (EXC_BAD_ACCESS, EXC_CRASH, EXC_BREAKPOINT)
- Faulting instruction address
- Thread backtraces (symbolicated if symbols are available)
- Register state at crash
- Binary images loaded (with UUIDs for symbolication)

**Forensic relevance**: crash reports can indicate:
- Exploitation attempts (EXC_BAD_ACCESS in media parsers, WebKit, iMessage)
- Jailbreak artifacts (crashes in `amfid`, `Sandbox`, or kernel-related processes)
- Malware activity (unexpected crashes in system daemons)

```bash
# Pull crash reports
idevicecrashreport -e /path/to/crashes/

# Search for exploitation indicators
grep -r "EXC_BAD_ACCESS" /path/to/crashes/ | grep -i "imagent\|IMTranscoderAgent\|mediaserverd"
grep -r "SIGABRT" /path/to/crashes/ | grep -i "BlastDoor\|WebKit"
```

### 8.5 KnowledgeC database

**KnowledgeC** (`/private/var/mobile/Library/CoreDuet/Knowledge/knowledgeC.db`) is a SQLite database containing detailed user activity data collected by Siri intelligence:

- App usage timestamps (when each app was in foreground, duration)
- Device lock/unlock events
- Battery level over time
- Now Playing (media being played)
- Safari browsing activity
- Device activity state (screen on/off, plugged in)

```sql
-- Query app usage from KnowledgeC
SELECT
    ZOBJECT.ZVALUESTRING AS "App Bundle ID",
    datetime(ZOBJECT.ZSTARTDATE + 978307200, 'unixepoch') AS "Start Time",
    datetime(ZOBJECT.ZENDDATE + 978307200, 'unixepoch') AS "End Time",
    (ZOBJECT.ZENDDATE - ZOBJECT.ZSTARTDATE) AS "Duration (seconds)"
FROM ZOBJECT
WHERE ZSTREAMNAME = "/app/usage"
ORDER BY ZOBJECT.ZSTARTDATE DESC
LIMIT 100;

-- Query device lock/unlock events
SELECT
    datetime(ZOBJECT.ZSTARTDATE + 978307200, 'unixepoch') AS "Timestamp",
    ZOBJECT.ZVALUEINTEGER AS "Locked (0=unlocked, 1=locked)"
FROM ZOBJECT
WHERE ZSTREAMNAME = "/device/isLocked"
ORDER BY ZOBJECT.ZSTARTDATE DESC;
```

**Forensic value**: KnowledgeC provides a detailed timeline of user activity on the device. The Apple epoch offset (978307200) converts Core Data timestamps to Unix timestamps.

### 8.6 PowerLog

**PowerLog** (`/private/var/containers/Shared/SystemGroup/*/Library/BatteryLife/CurrentPowerlog.PLSQL`) tracks:
- Process-level battery usage
- Network interface activity (cellular, Wi-Fi)
- Location service usage per app
- Camera/microphone usage per app
- Push notification delivery

**Forensic value**: PowerLog can reveal:
- Spyware activity (unexpected processes using camera, microphone, location, network in background)
- Timeline of network connections (correlating with exfiltration)
- Battery drain anomalies indicating surveillance

```sql
-- Query process network activity from PowerLog
SELECT
    datetime(timestamp, 'unixepoch') AS "Time",
    BundleID,
    cellin AS "Cellular In (bytes)",
    cellout AS "Cellular Out (bytes)",
    wifiin AS "WiFi In (bytes)",
    wifiout AS "WiFi Out (bytes)"
FROM PLProcessNetworkAgent_EventPoint_ProcessNetworkUsage
ORDER BY timestamp DESC
LIMIT 50;
```

---

## 9. Mobile network attacks

### 9.1 SS7/Diameter attacks (reference Domain 9B)

**SS7** (Signaling System 7): the signaling protocol for 2G/3G networks. Documented attack vectors (detailed in Domain 9 Chapter 9B section 3):
- **Location tracking**: `SendRoutingInfo` / `ProvideSubscriberInfo` queries to HLR reveal the subscriber's serving MSC/VLR (cell-level location)
- **SMS interception**: `UpdateLocation` spoofing redirects SMS to attacker's MSC; `ForwardSM` intercepts in transit
- **Call interception**: `InsertSubscriberData` modifies call-forwarding settings
- **DoS**: `CancelLocation` / `PurgeMS` deregisters the subscriber

**Diameter** (4G equivalent): similar attacks via Diameter commands (S6a interface to HSS). `Update-Location-Request`, `Authentication-Information-Request` spoofing.

**Defense**: SS7 firewalls (category-based filtering), Diameter Edge Agents (DEA), GSMA IR.82 guidelines, network monitoring for anomalous signaling.

### 9.2 SIM cloning and eSIM security

**Physical SIM cloning**: requires access to the SIM card and knowledge of the Ki (subscriber authentication key). Modern USIM (3G+) uses stronger algorithms (MILENAGE) and the Ki cannot be extracted via known side-channel attacks on current-generation SIMs. Historical attacks used weak COMP128v1 to extract Ki via chosen-challenge attacks.

**SIM swap attack**: social-engineering the carrier to transfer the victim's number to an attacker-controlled SIM. Does not require physical SIM access. Enables SMS interception (2FA bypass), call interception, and account takeover.

**eSIM security**: the eSIM (embedded SIM, eUICC) stores profiles in a tamper-resistant secure element. The SM-DP+ (Subscription Manager - Data Preparation) server provisions profiles over TLS. Attack vectors:
- Compromise of the SM-DP+ server
- QR code interception/replacement during eSIM provisioning
- SIM swap attacks remain possible (the carrier can reprovision the eSIM remotely)

### 9.3 Baseband vulnerability research

The cellular baseband processor (Qualcomm Snapdragon modem on most iPhones through iPhone 13; Intel modem on some models; Apple's own modem starting with iPhone 16e) runs a separate RTOS that processes radio signaling from cell towers. The baseband is a high-value target because:
- It processes untrusted input from the radio interface (any nearby transmitter)
- It runs a separate OS with its own attack surface (independent of iOS kernel protections)
- Compromise provides: IMSI/IMEI access, call/SMS interception, location tracking, potential DMA access to application processor memory (on some architectures)

**Research approach**: baseband firmware can be extracted from IPSW files (the baseband firmware image). Binary analysis with Ghidra/IDA Pro targeting the ARM Cortex-R/M architecture used by Qualcomm/Intel modems. Shannon (Samsung's baseband) has been more extensively researched due to its use in Samsung devices; similar vulnerability classes (stack overflows, heap corruption in protocol parsers) apply to Qualcomm modems.

**OTA (Over-The-Air) attacks**: a rogue base station (using open-source projects like srsRAN/Open5GS for 4G/5G or OsmocomBB for 2G) can send malformed RRC (Radio Resource Control), NAS (Non-Access Stratum), or RLC messages targeting parsing bugs in the baseband firmware.

### 9.4 VoLTE/VoWiFi attacks

**VoLTE interception**: VoLTE calls use SIP signaling over the IMS infrastructure and RTP/SRTP for media. If SRTP is not enforced (some carriers use RTP without encryption), call audio can be intercepted by an attacker with access to the transport network. Even with SRTP, the key exchange (typically in SDP within SIP INVITE) may be interceptable if the P-CSCF does not enforce IPsec/TLS for SIP signaling.

**VoWiFi (Wi-Fi Calling)**: the UE establishes an IKEv2/IPsec tunnel to the ePDG (evolved Packet Data Gateway). Authentication uses EAP-AKA' with USIM credentials. Attack vectors:
- Rogue Wi-Fi AP combined with a fake ePDG (requires matching the carrier's ePDG domain and certificate -- difficult with proper certificate pinning)
- If the device falls back to unencrypted SIP (implementation bug), the call signaling is exposed
- IKEv2 implementation vulnerabilities in the device's VPN client

### 9.5 Carrier bundle exploitation

**Carrier bundles** (`*.bundle` in `/System/Library/Carrier Bundles/`) define carrier-specific configurations: APN settings, VoLTE/VoWiFi parameters, visual voicemail endpoints, tethering restrictions. On jailbroken devices, modifying carrier bundles can:
- Enable hidden features (VoLTE on unsupported carriers)
- Change APN settings (traffic routing manipulation)
- Bypass tethering restrictions
- Modify carrier-specific entitlement checks

---

## 10. 5G security architecture

### 10.1 Service-Based Architecture (SBA)

5G's control plane uses a Service-Based Architecture: network functions (NFs) communicate via HTTP/2-based APIs over a service mesh. Key NFs:

**AMF (Access and Mobility Management Function)**: handles UE registration, connection management, and mobility. The first point of contact for the UE on the control plane. Receives NAS messages from the gNB and terminates NAS security (ciphering and integrity protection).

**SMF (Session Management Function)**: manages PDU (Protocol Data Unit) sessions -- the data connectivity. Interacts with UPF for user-plane path setup.

**UPF (User Plane Function)**: the data-plane anchor -- routes and forwards user traffic. Analogous to the PGW in 4G. Performs traffic detection and enforcement (DPI, QoS).

**AUSF (Authentication Server Function)**: handles 5G-AKA and EAP-AKA' authentication. Communicates with the UDM for subscriber credentials.

**UDM (Unified Data Management)**: stores subscriber data (SUPI, authentication vectors). The 5G equivalent of the HSS. Contains the SIDF (Subscription Identifier De-concealing Function) that decrypts SUCI to SUPI.

**UDR (Unified Data Repository)**: the underlying data store for UDM, PCF, and other NFs.

**NRF (Network Repository Function)**: the service registry -- NFs register their capabilities and discover other NFs via NRF. A compromised NRF could redirect NF traffic to malicious endpoints.

**NSSF (Network Slice Selection Function)**: selects the appropriate network slice for the UE based on its subscription and the requested service.

**NEF (Network Exposure Function)**: exposes network capabilities to external applications (via APIs) in a controlled manner. API gateway for third-party access.

**PCF (Policy Control Function)**: manages policy rules for sessions (QoS, charging, access control).

**SBA security concerns**: all NF-to-NF communication uses HTTP/2 over TLS 1.2+ (or mTLS). The OAuth 2.0-based NF authorization framework (using NRF as the authorization server) controls which NFs can access which services. A compromised NF with a valid OAuth token can access other NFs within its authorized scope. The flat service-mesh architecture (vs. the point-to-point interfaces of 4G) means a single compromised NF has broader lateral movement potential.

### 10.2 SUCI and authentication

**SUPI (Subscription Permanent Identifier)**: the subscriber's permanent identity (equivalent to IMSI). **SUCI (Subscription Concealed Identifier)**: the SUPI encrypted with the home network's public key using ECIES (Elliptic Curve Integrated Encryption Scheme, using Profile A: Curve25519 or Profile B: secp256r1). The UE sends SUCI (not SUPI) over the air, preventing passive IMSI catching.

**5G-AKA**: mutual authentication between the UE and the network. Process:
1. UE sends Registration Request with SUCI to AMF
2. AMF forwards SUCI to AUSF
3. AUSF sends to UDM/SIDF for SUCI decryption -> SUPI
4. UDM generates authentication vector (RAND, AUTN, XRES*, KAUSF)
5. AUSF sends RAND, AUTN to UE (via AMF)
6. UE verifies AUTN (authenticates the network)
7. UE computes RES* and sends to AMF
8. AMF computes HRES* and compares with HXRES*
9. AMF forwards RES* to AUSF for final verification
10. AUSF derives anchor key KAUSF; AMF derives KAMF

**EAP-AKA'**: used for non-3GPP access (Wi-Fi calling via ePDG). Uses EAP framework with AKA' (improved key derivation binding to the access network name).

**Residual IMSI-catching risk**: while SUCI prevents passive IMSI catching, an active attacker can force the UE to reveal its SUPI in specific scenarios: during emergency calls (SUPI is sent in cleartext), in certain roaming configurations, or via implementation bugs in the UE's NAS layer.

### 10.3 Network slicing

5G supports multiple virtual networks (slices) on shared physical infrastructure. Each slice has: dedicated or shared AMF/SMF/UPF instances, specific QoS parameters, and independent security policies.

**NSSAI (Network Slice Selection Assistance Information)**: identifies the slice(s) the UE is authorized to use. Contains S-NSSAI (Single NSSAI) elements, each with SST (Slice/Service Type) and optional SD (Slice Differentiator).

**Slice isolation threats**:
- Shared RAN resources: a DoS attack on one slice (radio resource exhaustion) can impact other slices sharing the same gNB
- Shared transport network: without proper traffic isolation (e.g., VLAN/VxLAN segmentation), cross-slice traffic leakage is possible
- Shared UPF: if multiple slices share a UPF instance without proper data-plane isolation, a compromised slice could access another slice's traffic
- Management plane: a compromised O&M (Operations & Maintenance) system with access to all slices breaks isolation

### 10.4 Inter-operator security (SEPP and N32)

**SEPP (Security Edge Protection Proxy)**: secures the N32 interface between operators for roaming. Two modes:
- **TLS**: full message encryption -- all control-plane messages between SEPPs are encrypted end-to-end
- **PRINS (Protection of Information Elements in N32 messages)**: selective encryption of sensitive IEs (SUPI, authentication vectors) while leaving routing information in cleartext for intermediate IPX proxies. PRINS uses a data-type encryption policy (DTEP) to specify which IEs to protect.

### 10.5 RAN security

**gNB (next-generation Node B)**: the 5G base station. Split architecture:
- **gNB-CU-CP** (Central Unit - Control Plane): handles RRC and PDCP-C
- **gNB-CU-UP** (Central Unit - User Plane): handles PDCP-U and SDAP
- **gNB-DU** (Distributed Unit): handles RLC, MAC, PHY layers
- Interfaces: **F1** (CU-DU), **E1** (CU-CP - CU-UP). These should be encrypted (IPsec recommended but not mandated by 3GPP).

**O-RAN (Open RAN)**: disaggregates the RAN into interoperable components from multiple vendors. Security concerns:
- **RIC (RAN Intelligent Controller)**: runs third-party xApps/rApps that influence radio resource management. A compromised xApp could manipulate radio scheduling, cause denial of service, or intercept traffic.
- **Open Fronthaul**: the interface between O-DU and O-RU carries I/Q samples. If unencrypted, raw radio data is exposed.
- **A1/O1/O2 interfaces**: management and orchestration interfaces. Compromise provides control over RAN configuration.

### 10.6 IMS, VoLTE, and VoWiFi

**IMS (IP Multimedia Subsystem)**: provides voice and video services over LTE (VoLTE) and 5G (VoNR). Key components:
- **P-CSCF** (Proxy-CSCF): entry point for IMS signaling. Enforces SIP security (IPsec/TLS).
- **I-CSCF** (Interrogating-CSCF): routes to the correct S-CSCF based on subscriber data.
- **S-CSCF** (Serving-CSCF): handles SIP registration and session control. The "brain" of IMS.

**VoWiFi (Voice over Wi-Fi)**: the UE tunnels IMS signaling and media over IPsec to an **ePDG** which connects to the core network. IKEv2/IPsec tunnel with EAP-AKA' authentication. The ePDG terminates the IPsec tunnel and forwards traffic to the P-CSCF.

### 10.7 SMS interception across generations

**2G (SS7)**: SMS is transported in MAP messages. Interception via SS7 `ForwardSM` or `UpdateLocation` (Domain 9 Chapter 9B section 3.1).

**4G (Diameter)**: SMS can be transported via SGs interface (to the MSC) or via IP (SMS over IMS). Diameter-based interception targets the SGs or the SMSC.

**5G**: SMS can be transported over NAS (Non-Access Stratum -- directly between UE and AMF, encrypted with NAS security) or over IMS. SUCI prevents passive identification, but an active attacker with access to the core network (compromised NF, rogue operator) can still intercept SMS at the SMSC or AMF.

**Defense**: SMS-based 2FA is inherently insecure across all generations. FIDO2/WebAuthn or TOTP authenticators should replace SMS OTP for high-security applications.

---

## 11. iOS Detection Engineering

Detection engineering for iOS requires a different sensor model than Android. There is no equivalent of custom SELinux audit logs or `logcat`-based instrumentation on non-jailbroken devices. Detection relies on MDM telemetry, network anomaly analysis, endpoint agents with supervised-mode access, and Apple's own attestation APIs.

### 11.1 Jailbreak indicator detection

Jailbreak detection operates at multiple layers. No single check is sufficient; a defense-in-depth approach combines file existence checks, runtime behavior tests, and attestation.

**Filesystem indicators** (detectable by MDM compliance checks or app-level checks):

```
# Cydia and package manager artifacts
/Applications/Cydia.app
/Applications/Sileo.app
/Applications/Zebra.app
/usr/bin/cydia
/var/lib/dpkg/status
/var/lib/apt/
/etc/apt/sources.list.d/

# Jailbreak toolchain remnants
/usr/bin/ssh
/usr/sbin/sshd
/usr/bin/cycript
/usr/local/bin/cycript
/usr/lib/libcycript.dylib
/private/var/stash
/private/var/lib/cydia
/private/var/mobile/Library/SBSettings/Themes
/Library/MobileSubstrate/MobileSubstrate.dylib
/Library/MobileSubstrate/DynamicLibraries/
/usr/lib/substrate
/usr/lib/TweakInject/
/var/binpack/
/var/jb/                    # rootless jailbreaks (Dopamine, palera1n rootless)

# checkra1n / palera1n specific
/var/checkra1n.dmg
/cores/binpack/.installed_palera1n

# Procursus bootstrap (modern jailbreaks)
/var/jb/usr/bin/apt
/var/jb/usr/bin/dpkg
/var/jb/Library/dpkg/status
```

**Runtime behavior checks**:

```swift
// Swift: multi-layered jailbreak detection
import Foundation
import MachO

struct JailbreakDetector {

    /// Check if known jailbreak paths exist
    static func suspiciousFilesExist() -> Bool {
        let paths = [
            "/Applications/Cydia.app",
            "/Applications/Sileo.app",
            "/var/jb/usr/bin/dpkg",
            "/Library/MobileSubstrate/MobileSubstrate.dylib",
            "/usr/sbin/sshd",
            "/etc/apt",
            "/private/var/lib/apt/"
        ]
        return paths.contains { FileManager.default.fileExists(atPath: $0) }
    }

    /// Attempt to write outside the sandbox
    static func canWriteOutsideSandbox() -> Bool {
        let testPath = "/private/jailbreak_test_\(UUID().uuidString)"
        do {
            try "test".write(toFile: testPath, atomically: true, encoding: .utf8)
            try FileManager.default.removeItem(atPath: testPath)
            return true  // should not succeed on stock iOS
        } catch {
            return false
        }
    }

    /// Check if fork() succeeds (blocked by sandbox on stock iOS)
    static func canFork() -> Bool {
        let pid = fork()
        if pid >= 0 {
            if pid > 0 { kill(pid, SIGTERM) }
            return true
        }
        return false
    }

    /// Detect Frida by checking for frida-server port or loaded dylibs
    static func fridaDetected() -> Bool {
        // Check if frida default port is open
        var addr = sockaddr_in()
        addr.sin_family = sa_family_t(AF_INET)
        addr.sin_port = CFSwapInt16HostToBig(27042)
        addr.sin_addr.s_addr = inet_addr("127.0.0.1")
        let sock = socket(AF_INET, SOCK_STREAM, 0)
        guard sock >= 0 else { return false }
        let result = withUnsafePointer(to: &addr) {
            $0.withMemoryRebound(to: sockaddr.self, capacity: 1) {
                connect(sock, $0, socklen_t(MemoryLayout<sockaddr_in>.size))
            }
        }
        close(sock)
        if result == 0 { return true }

        // Check loaded dylibs for frida signatures
        let count = _dyld_image_count()
        for i in 0..<count {
            if let name = _dyld_get_image_name(i) {
                let dylib = String(cString: name)
                if dylib.contains("frida") || dylib.contains("FridaGadget") {
                    return true
                }
            }
        }
        return false
    }

    /// Detect substrate/TweakInject hooking frameworks
    static func hookingFrameworkDetected() -> Bool {
        let suspiciousDylibs = [
            "MobileSubstrate", "substrate", "TweakInject",
            "CydiaSubstrate", "libhooker", "SubstrateLoader"
        ]
        let count = _dyld_image_count()
        for i in 0..<count {
            if let name = _dyld_get_image_name(i) {
                let dylib = String(cString: name)
                for suspicious in suspiciousDylibs {
                    if dylib.contains(suspicious) { return true }
                }
            }
        }
        return false
    }
}
```

**YARA rule -- jailbreak artifacts on device image**:

```yara
rule iOS_Jailbreak_Indicators
{
    meta:
        description = "Detects jailbreak remnants in iOS filesystem dump"
        author      = "iOS Detection Engineering"
        date        = "2025-01-15"
        severity    = "HIGH"

    strings:
        $cydia_app       = "/Applications/Cydia.app" ascii
        $sileo_app       = "/Applications/Sileo.app" ascii
        $substrate       = "MobileSubstrate.dylib" ascii
        $tweak_inject    = "/usr/lib/TweakInject" ascii
        $dpkg_status     = "/var/lib/dpkg/status" ascii
        $sshd            = "/usr/sbin/sshd" ascii
        $rootless_jb     = "/var/jb/" ascii
        $palera1n        = ".installed_palera1n" ascii
        $libhooker       = "libhooker.dylib" ascii
        $substitute      = "libsubstitute.dylib" ascii

    condition:
        3 of them
}
```

### 11.2 Malicious MDM profile detection

Rogue MDM profiles are a primary vector for corporate espionage and surveillance. A malicious MDM profile grants the MDM server capabilities including remote wipe, app installation, certificate injection (enabling TLS interception), VPN configuration, and full device management.

**Detection indicators**:

- Profiles installed outside of the organization's official enrollment flow (no DEP/ABM association)
- Profiles with overly broad `PayloadType` entries (`com.apple.security.root` for CA certificate injection, `com.apple.vpn.managed` for traffic routing, `com.apple.wifi.managed` with proxy settings)
- Enrollment profiles pointing to unknown or suspicious MDM server URLs
- Profiles with `PayloadRemovalDisallowed` set to `true` that the user did not expect
- Multiple configuration profiles from different organizations on a single device

**MDM compliance query for detection** (server-side):

```python
# MDM server: query installed profiles and flag anomalies
# Uses Apple's MDM protocol -- ProfileList command

mdm_command = {
    "CommandUUID": "profile-audit-001",
    "Command": {
        "RequestType": "ProfileList"
    }
}

# Response analysis -- flag profiles not in the approved whitelist
def analyze_profiles(response, approved_identifiers):
    """Flag unauthorized MDM/configuration profiles."""
    alerts = []
    for profile in response.get("ProfileList", []):
        identifier = profile.get("PayloadIdentifier", "")
        org = profile.get("PayloadOrganization", "")
        has_root_cert = any(
            p.get("PayloadType") == "com.apple.security.root"
            for p in profile.get("PayloadContent", [])
        )
        has_vpn = any(
            p.get("PayloadType") == "com.apple.vpn.managed"
            for p in profile.get("PayloadContent", [])
        )

        if identifier not in approved_identifiers:
            severity = "CRITICAL" if has_root_cert else "HIGH"
            alerts.append({
                "severity": severity,
                "identifier": identifier,
                "organization": org,
                "has_root_cert": has_root_cert,
                "has_vpn": has_vpn,
                "description": f"Unauthorized profile from '{org}'"
            })
    return alerts
```

### 11.3 URL scheme abuse detection

Suspicious URL scheme invocation patterns indicate exploitation attempts or data exfiltration:

- Repeated `openURL:` calls to custom schemes with long query strings (credential theft)
- URL scheme calls from apps that have no legitimate reason to invoke the target scheme
- Rapid sequential scheme invocations (fuzzing attempts)
- Schemes invoked from web content (Safari/WebView) targeting banking or authentication apps

**Detection via unified logging** (sysdiagnose or MDM-collected logs):

```bash
# Search for URL scheme invocations in unified log
log show --archive system_logs.logarchive \
    --predicate 'process == "SpringBoard" AND eventMessage CONTAINS "openURL"' \
    --style compact --info

# Detect rapid scheme invocations (potential fuzzing)
log show --archive system_logs.logarchive \
    --predicate 'process == "SpringBoard" AND eventMessage CONTAINS "openURL"' \
    --style compact --info | \
    awk -F'[ .]' '{print $1" "$2}' | uniq -c | sort -rn | head -20
```

### 11.4 Enterprise certificate abuse detection

Enterprise Distribution Certificates (Apple Developer Enterprise Program) allow organizations to deploy apps outside the App Store. Abuse patterns:

- **Sideloaded surveillance apps**: commercial spyware (e.g., FlexiSPY, mSpy) distributed via enterprise certificates
- **Piracy stores**: unauthorized app marketplaces using enterprise certificates
- **Malware distribution**: enterprise-signed trojans targeting specific organizations

**Detection approach**:

```bash
# On jailbroken device or forensic image: enumerate provisioning profiles
find /var/mobile/Library/ConfigurationProfiles/ -name "*.mobileprovision" -exec \
    security cms -D -i {} \; 2>/dev/null

# On managed device via MDM: InstalledApplicationList command
# Flag apps with unexpected Team IDs or provisioning profiles
# not matching the organization's Apple Developer Team ID

# ideviceprovision: list all provisioning profiles
ideviceprovision list

# Parse profile details
ideviceprovision dump <profile-uuid> | grep -E "TeamIdentifier|TeamName|ExpirationDate"
```

**MDM-based detection**: use the `InstalledApplicationList` MDM command with `ManagedAppsOnly=false` to enumerate all apps. Flag apps where:
- The signing Team ID does not match the organization's known Team IDs
- The app is enterprise-distributed but not in the organization's approved catalog
- The provisioning profile is expired or about to expire (attackers rarely renew)

### 11.5 Network anomaly detection from compromised iOS devices

Compromised iOS devices exhibit distinctive network behaviors detectable at the network perimeter:

- **Beaconing to C2 infrastructure**: periodic HTTPS connections to domains with high entropy or recently registered domains, often on non-standard ports
- **DNS anomalies**: DNS-over-HTTPS to non-corporate resolvers, DNS tunneling (long subdomain labels, high query frequency to a single domain)
- **Certificate anomalies**: connections to servers with self-signed or unusual CA chains (spyware infrastructure)
- **Data exfiltration patterns**: large outbound transfers during device idle time (screen off, overnight)
- **iMessage-based exploitation**: abnormal `imagent` or `apsd` (Apple Push Service daemon) traffic patterns -- high-frequency push notification processing, connections to unexpected Apple relay endpoints

**Snort/Suricata rule -- detect Pegasus-like C2 beaconing pattern**:

```
# Detect high-entropy domain lookups typical of spyware C2
alert dns $HOME_NET any -> any 53 (msg:"MOBILE-MALWARE Possible spyware C2 DNS query - high entropy domain"; \
    dns.query; content:"."; pcre:"/^[a-z0-9]{16,}\.(com|net|org|info|xyz)/i"; \
    threshold:type both, track by_src, count 5, seconds 60; \
    classtype:trojan-activity; sid:2025001; rev:1;)

# Detect iOS device connecting to known MVNO/VPN infrastructure used by spyware
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"MOBILE-MALWARE iOS device TLS to suspicious infrastructure"; \
    tls.sni; content:".amazonaws.com"; pcre:"/^[a-f0-9]{8,}\./"; \
    flow:to_server,established; \
    classtype:trojan-activity; sid:2025002; rev:1;)
```

### 11.6 YARA rules for iOS malware families

**Pegasus (NSO Group) indicators**:

```yara
rule iOS_Pegasus_Indicators
{
    meta:
        description = "Detects NSO Pegasus implant artifacts on iOS"
        reference   = "Amnesty International / Citizen Lab reports"
        date        = "2025-03-10"
        severity    = "CRITICAL"
        mitre_att   = "T1437.001, T1437"

    strings:
        // Process names and paths observed in Pegasus infections
        $proc_bh     = "bh" ascii           // Pegasus bridgehead process
        $proc_roleab = "roleaboutd" ascii   // masquerades as system daemon
        $proc_pcscd  = "pcabordd" ascii
        $path_cache  = "/private/var/tmp/.libcache" ascii
        $path_store  = "/private/var/tmp/PlugInCache" ascii

        // Pegasus Validation Server domains (historical)
        $domain1 = "c.appanalytics.space" ascii
        $domain2 = "php.info-ede.com" ascii
        $domain3 = "rebranchermarketplace.com" ascii

        // FORCEDENTRY exploit chain artifacts (CVE-2021-30860)
        $gif_magic   = { 47 49 46 38 39 61 }  // GIF89a header
        $pdf_xref    = "%%EOF" ascii
        // FORCEDENTRY used a .gif file containing a PDF with JBIG2 exploit
        $jbig2_seg   = { 00 00 00 01 30 00 01 00 00 00 }

    condition:
        (2 of ($proc_*, $path_*)) or
        (any of ($domain*)) or
        ($gif_magic at 0 and $pdf_xref and $jbig2_seg)
}
```

**LightSpy indicators**:

```yara
rule iOS_LightSpy_Implant
{
    meta:
        description = "Detects LightSpy modular iOS implant"
        reference   = "Kaspersky/ThreatFabric analysis 2024"
        date        = "2025-01-20"
        severity    = "CRITICAL"

    strings:
        $framework  = "CoreFoundation.framework" ascii
        $lightspy1  = "/tmp/lsd/" ascii
        $lightspy2  = "lightriver" ascii
        $lightspy3  = "EnvironmentLight" ascii
        $plugin_loc = "/Library/Frameworks/Light.framework" ascii
        $sqlite_db  = "lightspy.db" ascii
        $config_url = "/api/v1/config" ascii
        $ws_path    = "/ws/client" ascii

    condition:
        $framework and (3 of ($lightspy*, $plugin_loc, $sqlite_db, $config_url, $ws_path))
}
```

**TriangleDB (Operation Triangulation) artifacts**:

```yara
rule iOS_TriangleDB
{
    meta:
        description = "Detects TriangleDB implant from Operation Triangulation"
        reference   = "Kaspersky GReAT analysis 2023"
        date        = "2025-02-15"
        severity    = "CRITICAL"
        cve         = "CVE-2023-32434, CVE-2023-32435, CVE-2023-38606"

    strings:
        // TriangleDB characteristic strings
        $db_name     = "persistent.db" ascii
        $module_mgr  = "CRConfig" ascii
        $location_mod = "CRLocRec" ascii
        $mic_mod     = "CRMicRec" ascii
        $keychain_mod = "CRKCExt" ascii

        // Exploitation chain artifacts
        $imessage_attach = "com.apple.imagent" ascii
        $backupagent     = "BackupAgent" ascii
        // Hardware MMIO addresses used in CVE-2023-38606 (undocumented HW feature)
        $mmio_addr1  = { 00 00 00 06 10 20 00 00 }
        $mmio_addr2  = { 00 00 00 06 10 20 00 04 }

    condition:
        (3 of ($db_name, $module_mgr, $location_mod, $mic_mod, $keychain_mod)) or
        ($imessage_attach and $backupagent and any of ($mmio_addr*))
}
```

### 11.7 MDM-based attestation (DeviceCheck and App Attest)

**DeviceCheck** (iOS 11+): server-to-Apple API that associates two bits of data per device per developer. Cannot detect jailbreak directly, but allows servers to flag devices that have exhibited suspicious behavior.

**App Attest** (iOS 14+): hardware-backed attestation using the Secure Enclave. The device generates an attestation key pair inside the SEP, and Apple's attestation server certifies that the key was generated on a genuine Apple device running an unmodified OS.

**Attestation verification flow**:

```swift
// Client-side: generate attestation key and request attestation
import DeviceCheck

let service = DCAppAttestService.shared

// 1. Check availability
guard service.isSupported else { return }

// 2. Generate key (stored in Secure Enclave)
service.generateKey { keyId, error in
    guard let keyId = keyId else { return }

    // 3. Get server challenge (nonce)
    fetchChallengeFromServer { challenge in
        let hash = Data(SHA256.hash(data: challenge))

        // 4. Attest the key with Apple's servers
        service.attestKey(keyId, clientDataHash: hash) { attestation, error in
            guard let attestation = attestation else { return }
            // 5. Send attestation to server for verification
            sendAttestationToServer(keyId: keyId, attestation: attestation)
        }
    }
}
```

**Server-side verification** validates that:
- The attestation certificate chains to Apple's App Attest root CA
- The `rpIdHash` matches the app's App ID
- The `clientDataHash` matches the challenge
- The counter is non-zero and incrementing
- The `credCert` contains the expected `aaguid` for App Attest (not a software emulator)

A jailbroken device with a compromised SEP or a patched `DCAppAttestService` can potentially forge attestations, but this requires advanced exploitation beyond simple jailbreaks. App Attest significantly raises the cost of device-integrity spoofing.

---

## 12. Advanced iOS and Mobile Network Exploitation

### 12.1 iMessage zero-click exploitation: FORCEDENTRY chain analysis

**FORCEDENTRY (CVE-2021-30860)** represents the most sophisticated publicly documented zero-click iOS exploit chain. Developed by NSO Group, it targeted iMessage and required zero user interaction.

**Exploit chain summary**:

1. **Delivery**: attacker sends an iMessage containing a file with a `.gif` extension (parsed by `IMTranscoderAgent`). Despite the extension, the file contains a PDF.
2. **PDF parsing**: iOS's ImageIO framework auto-renders the attachment. The PDF contains embedded JBIG2 streams.
3. **JBIG2 exploitation (CVE-2021-30860)**: the JBIG2 decoder in CoreGraphics contains an integer overflow vulnerability. The attacker crafted JBIG2 segment headers to achieve a constrained arbitrary write primitive. Crucially, JBIG2's logical operators (AND, OR, XOR, XNOR) on bitmap segments were weaponized as a Turing-complete computation engine -- the exploit implemented a small virtual architecture within JBIG2 to bootstrap the next stage.
4. **Sandbox escape**: the JBIG2-based computation generates a second-stage payload that escapes the `IMTranscoderAgent` sandbox (which runs with the restrictive `BlastDoor` sandbox profile on iOS 14+).
5. **BlastDoor bypass**: on iOS 14+, Apple introduced BlastDoor -- a tightly sandboxed process (`IMTranscoderAgent`) that pre-validates iMessage attachments. FORCEDENTRY bypassed BlastDoor by exploiting the JBIG2 vulnerability in a code path that executes before BlastDoor's checks apply.
6. **Kernel exploit**: the sandbox escape leads to a kernel vulnerability (separate CVE) that achieves code execution with kernel privileges.
7. **PAC bypass**: on A12+ devices, the chain includes a PAC bypass to execute arbitrary kernel code.
8. **Persistence**: Pegasus installs via the exploited chain, surviving reboot on older iOS versions through LaunchDaemon plists or, on modern iOS, operating in a "zero-persistence" mode that must re-exploit after reboot.

**Forensic detection of FORCEDENTRY**:

```bash
# Search for suspicious iMessage attachments in backup
find ~/Library/Application\ Support/MobileSync/Backup/ \
    -name "*.gif" -exec file {} \; | grep -i "pdf"

# MVT (Mobile Verification Toolkit) check for Pegasus indicators
# Install: pip install mvt
mvt-ios check-backup --indicators pegasus_indicators.stix2 \
    --output /path/to/results/ /path/to/backup/

# Check for FORCEDENTRY-style attachment in iMessage database
sqlite3 sms.db "SELECT rowid, guid, text, cache_has_attachments \
    FROM message WHERE cache_has_attachments = 1 \
    ORDER BY date DESC LIMIT 50;"
```

### 12.2 Kernel exploitation on modern iOS

**PAC (Pointer Authentication Codes) bypass techniques**:

PAC (introduced A12) adds cryptographic signatures to pointers. Bypass strategies documented in public research:

- **PACMAN (MIT CSAIL, June 2022; no CVE assigned -- Apple considers it a defense-in-depth concern)**: speculative execution attack. The attacker uses speculative execution to test PAC guesses without triggering a fault. The CPU speculatively dereferences a signed pointer; if the PAC is wrong, the speculation is squashed. By measuring microarchitectural side channels (cache timing), the attacker determines whether the PAC guess was correct. This defeats PAC's brute-force resistance (which relies on the pointer authentication failure triggering a fault).
- **Signing gadget reuse**: find existing signed pointers in memory that point to useful gadgets. Instead of forging a PAC, reuse legitimately signed pointers from the kernel heap or stack.
- **PAC context confusion**: PAC uses a "context" value (typically the storage address) mixed into the signature. If the attacker can control where a signed pointer is stored, they can sign a pointer under one context and use it in another if both contexts produce the same PAC.
- **Thread state forgery**: on some iOS versions, the `thread_set_state()` Mach trap allows setting thread register state including PAC-signed registers. If the kernel does not fully re-sign the saved state, the attacker can inject unsigned pointers into the thread context.

**PPL (Page Protection Layer) bypass**:

PPL protects page tables from kernel code. Bypass approaches:

- **PPL code reuse**: PPL routines themselves are legitimate code that can modify page tables. If the attacker can control the arguments to a PPL entry point (via a kernel vulnerability that can manipulate the PPL call stack), they can trick PPL into making attacker-desired page-table modifications.
- **DMA attacks**: on devices where DMA controllers are not fully locked down by DART (Device Address Resolution Table), a compromised co-processor (e.g., Wi-Fi chip) could directly modify physical memory including page tables, bypassing PPL. Apple has progressively hardened DART to close this vector.
- **MMIO manipulation (CVE-2023-38606)**: Operation Triangulation exploited undocumented hardware MMIO registers in the Apple SoC GPU to write to physical memory without going through the CPU's page-table checks, completely circumventing PPL. This vulnerability relied on undocumented hardware features, suggesting deep knowledge of Apple silicon internals.

**kASLR defeat**:

Kernel Address Space Layout Randomization slides the kernel base by a random offset at boot. Defeat methods:

```
1. Information disclosure (kernel pointer leak):
   - IOKit: userClient->getExternalTrapForIndex() may leak kernel pointers
   - Mach messages: some kernel MIG routines return uninitialized stack data
   - Timing side channels: measuring kernel operation latency to infer addresses

2. Hardware-based:
   - KTRR bounds leak: KTRR register values (readable from EL0 on some SoCs)
     reveal the kernel text region boundaries
   - Prefetch side channel: ARM prefetch instruction timing varies based on
     whether the target address is in the TLB (kernel addresses resident
     from recent syscalls)

3. Brute force (limited):
   - iOS kASLR entropy is ~8 bits on some versions (256 possible slides)
   - Repeated exploitation attempts with different offsets until success
   - Effective only with a vulnerability that does not crash on failure
```

### 12.3 Baseband exploitation

The baseband processor (modem) runs a separate RTOS and handles all cellular communication. It represents a high-value pre-authentication remote attack surface.

**Baseband processors in Apple devices**:
- **Qualcomm MDM/SDX series**: used in iPhone 7 through iPhone 13 (and some later models). The Qualcomm baseband runs a proprietary RTOS (AMSS/QuRT). Firmware blobs are in the IPSW under `Firmware/`.
- **Intel XMM series**: used in some iPhone models (iPhone 8, X, XS, XR -- region-dependent). Known for higher latency and less mature security than Qualcomm.
- **Apple Silicon modem**: Apple's custom 5G modem (first deployed in iPhone SE 4, iPhone 16e). Details remain limited, but it integrates more tightly with the Secure Enclave and runs on Apple-designed silicon.

**Attack surface**:

- **OTA (Over-The-Air) protocol stack**: the baseband processes RRC (Radio Resource Control), NAS (Non-Access Stratum), and SIP/IMS messages received from the radio network. Malformed messages can trigger parsing vulnerabilities.
- **SMS/MMS parsing**: the baseband handles SMS PDU decoding. Malformed SMS (especially concatenated multi-part SMS or WAP Push) has historically triggered vulnerabilities.
- **RRC reconfiguration**: the base station sends RRC Reconfiguration messages to the UE. A rogue base station (IMSI catcher or femtocell) can craft malicious RRC messages.

**Baseband fuzzing approach** (research-level):

```bash
# OTA baseband fuzzing requires specialized hardware
# Approach 1: Software-defined radio (SDR) with srsRAN
# Set up a rogue eNodeB that sends crafted NAS/RRC messages

# Install srsRAN (open-source LTE stack)
# Requires USRP B210 or similar SDR
sudo apt install srsran

# Configure rogue eNodeB
cat > enb.conf << 'CONF'
[enb]
enb_id = 0x19B
mcc = 001
mnc = 01
n_prb = 50
[rf]
device_name = UHD
device_args = auto
CONF

# Approach 2: Emulation-based fuzzing
# BaseSpec (Samsung Shannon) or similar framework
# Extracts the baseband firmware state machine and fuzzes
# protocol handlers in emulation (QEMU-based)

# Approach 3: libimobiledevice + AT commands for basic probing
# Some diagnostic commands are accessible via the baseband
idevicediagnostics diagnostics All | grep -i baseband
```

**Real-world baseband CVEs**:
- **CVE-2020-0069** (MediaTek): buffer overflow in the MediaTek baseband command handler, allowing code execution from an app without root
- **CVE-2023-24033** (Samsung Shannon): Internet-to-baseband RCE via malformed SIP INVITE. Affected Samsung Exynos modems, demonstrating that baseband RCE is achievable over the air
- **CVE-2022-20170** (Qualcomm): buffer overflow in the Qualcomm NAS message parser, triggerable by a rogue base station

### 12.4 SS7 and Diameter exploitation for mobile surveillance

SS7 (Signaling System 7) and its 4G successor Diameter remain the backbone of inter-carrier signaling. Exploitation provides location tracking, SMS interception, and call interception without touching the target device.

**SS7 attack categories** (extends Domain 9 Chapter 9B section 3):

```
Attack                  SS7 Operation                  Impact
─────────────────────── ────────────────────────────── ──────────────────────────
Location tracking       SendRoutingInfoForSM (SRI-SM)  Returns serving MSC/VLR
                        ProvideSubscriberInfo (PSI)     Returns Cell ID + LAC
                        AnyTimeInterrogation (ATI)      Returns GPS (if available)

SMS interception        UpdateLocation                  Registers fake MSC
                        SendRoutingInfoForSM            Routes SMS to attacker
                        ForwardSM                       Intercepts in transit

Call interception       InsertSubscriberData (ISD)      Sets call forwarding
                        RegisterSS                      Activates CF at HLR
                        SendRoutingInfo (SRI)           Returns MSRN for call

DoS                     CancelLocation                  De-registers subscriber
                        PurgeMS                         Removes from VLR
                        DeleteSubscriberData            Removes services
```

**Diameter attacks** (4G equivalent):

- **S6a interface**: subscriber data exchange between MME and HSS. A compromised S6a link allows `Update-Location-Request` to hijack a subscriber's session.
- **Rx interface**: policy and charging. Manipulating QoS parameters or session binding.
- **SWx interface**: non-3GPP access authentication (Wi-Fi calling). Intercepting authentication vectors.

**Detection and defense**:

- **SS7 firewall**: deploy a Signaling Transfer Point (STP) with filtering rules that block unauthorized `SRI-SM`, `PSI`, `ATI`, and `UpdateLocation` operations from non-trusted originating point codes
- **GSMA FS.11 / FS.19**: recommended filtering rules for SS7 and Diameter
- **Home Routing for SMS**: ensure all SMS delivery routes through the home SMSC rather than allowing foreign networks to redirect

### 12.5 IMSI catcher detection and defense

IMSI catchers (cell-site simulators, Stingrays) impersonate legitimate cell towers to force target devices to connect, enabling identification (IMSI/IMEI capture), location tracking, and traffic interception.

**Detection methods**:

- **Signal anomaly analysis**: unexpected cell tower changes, base station with abnormally strong signal, tower broadcasting unusual parameters (unusually low frequency, high power, MCC/MNC mismatch)
- **2G downgrade detection**: if the device is forced from LTE/5G to GSM (to defeat encryption), this is a strong IMSI catcher indicator
- **LAC/TAC anomalies**: the Location Area Code or Tracking Area Code does not match expected values for the geographic location
- **Cell tower database comparison**: compare observed Cell IDs against known tower databases (OpenCelliD, Mozilla Location Service)

**On-device detection** (limited on stock iOS):

```
iOS does not expose raw cell tower parameters to third-party apps.
Detection on iOS requires:
1. MDM-managed devices: use the CellularPlan and Network managed queries
   to detect unexpected carrier changes
2. External RF monitoring: dedicated hardware (e.g., Crocodile Hunter,
   AIMSICD on Android companion device, ESD Overwatch)
3. Network-side: operators deploy IMSI catcher detection at the RAN level
   by monitoring for rogue eNodeBs/gNBs with known operator parameters
```

**5G improvements**: SUCI (Subscription Concealed Identifier) replaces IMSI over the air, preventing passive IMSI capture. However, active attacks that impersonate a legitimate gNB can still force the UE to reveal its SUCI (which the attacker cannot decrypt without the HPLMN's private key) or downgrade to 4G/2G where IMSI is exposed.

### 12.6 SIM cloning and eSIM security

**Physical SIM cloning**:

- Requires physical access to the SIM card
- Ki (authentication key) extraction: historically possible via side-channel attacks on SIM card crypto (DPA -- Differential Power Analysis on the SIM's DES/3DES/AES operations). Modern USIM cards with AES-based Milenage algorithm and hardware countermeasures make Ki extraction significantly harder.
- Cloned SIM receives the subscriber's calls and SMS until the network detects two registrations from the same IMSI (which triggers security procedures in most modern networks)

**eSIM security model**:

- **SM-DP+ (Subscription Manager - Data Preparation)**: securely delivers eSIM profiles to devices. Communication is mutually authenticated (TLS + GSMA RSP certificate chain).
- **eUICC**: the embedded UICC hardware element. On Apple devices, the eUICC is a dedicated secure element (separate from the Secure Enclave). Profile isolation is enforced at the hardware level -- each profile runs in its own security domain.
- **Profile download security**: the eSIM profile (containing Ki, IMSI, and operator configuration) is encrypted end-to-end between the SM-DP+ and the eUICC. The device's AP never has access to the Ki.
- **Attack surface**: compromising the SM-DP+ server would allow injecting malicious profiles. QR code interception could redirect profile download to an attacker-controlled SM-DP+ if the activation code is not protected by a confirmation code.

---

## 13. Mobile Infrastructure Hardening

### 13.1 iOS enterprise deployment hardening

**Supervised mode** (available via DEP/ABM or Apple Configurator): grants organizations full control over the device. Supervised-only restrictions include:

- Disable AirDrop, iMessage, FaceTime, App Store
- Prevent VPN removal or profile removal
- Configure always-on VPN (IKEv2)
- Restrict USB accessories (USB Restricted Mode enforcement)
- App lock (Single App Mode / Autonomous Single App Mode)
- Content filter (managed via NEFilterDataProvider)
- Global HTTP proxy enforcement

**Always-on VPN configuration** (MDM profile):

```xml
<!-- IKEv2 Always-On VPN payload -->
<dict>
    <key>PayloadType</key>
    <string>com.apple.vpn.managed</string>
    <key>VPNType</key>
    <string>IKEv2</string>
    <key>IKEv2</key>
    <dict>
        <key>RemoteAddress</key>
        <string>vpn.corp.example.com</string>
        <key>LocalIdentifier</key>
        <string>device@corp.example.com</string>
        <key>RemoteIdentifier</key>
        <string>vpn.corp.example.com</string>
        <key>AuthenticationMethod</key>
        <string>Certificate</string>
        <key>PayloadCertificateUUID</key>
        <string>CERT-UUID-HERE</string>
        <key>EnablePFS</key>
        <true/>
        <key>IKESecurityAssociationParameters</key>
        <dict>
            <key>EncryptionAlgorithm</key>
            <string>AES-256-GCM</string>
            <key>IntegrityAlgorithm</key>
            <string>SHA2-384</string>
            <key>DiffieHellmanGroup</key>
            <integer>20</integer>
        </dict>
        <key>ChildSecurityAssociationParameters</key>
        <dict>
            <key>EncryptionAlgorithm</key>
            <string>AES-256-GCM</string>
            <key>IntegrityAlgorithm</key>
            <string>SHA2-384</string>
            <key>DiffieHellmanGroup</key>
            <integer>20</integer>
        </dict>
    </dict>
    <key>AlwaysOn</key>
    <dict>
        <key>CellularAllowCaptiveWebSheet</key>
        <false/>
        <key>WiFiAllowCaptiveWebSheet</key>
        <false/>
        <key>CellularAllowAllCaptiveNetworkPlugins</key>
        <false/>
        <key>WiFiAllowAllCaptiveNetworkPlugins</key>
        <false/>
        <key>AllowedCaptiveNetworkPlugins</key>
        <array/>
        <key>CellularServiceExceptions</key>
        <dict/>
        <key>WiFiServiceExceptions</key>
        <dict/>
        <key>TunnelConfigurations</key>
        <array>
            <dict>
                <key>ProtocolType</key>
                <string>IKEv2</string>
                <key>Interfaces</key>
                <array>
                    <string>Cellular</string>
                    <string>WiFi</string>
                </array>
            </dict>
        </array>
    </dict>
</dict>
```

### 13.2 Mobile Threat Defense (MTD) architecture

MTD solutions provide continuous threat detection on managed mobile devices. The architecture consists of:

**On-device agent**:
- App-level sensor: inspects installed apps, provisioning profiles, OS configuration
- Network sensor: monitors DNS queries, TLS connections, detects MitM (certificate validation)
- Device posture: jailbreak detection, OS version, security patch level, encryption status
- Behavioral analysis: anomalous app behavior, unusual process execution patterns (limited on non-jailbroken iOS)

**Cloud analysis engine**:
- App binary analysis (static + dynamic): decompiles uploaded apps, runs in sandboxed environment
- Threat intelligence correlation: maps observed indicators against known threat feeds
- Machine learning models: detect zero-day malware from behavioral patterns
- Policy decision engine: determines risk score and enforcement action

**UEM/MDM integration**:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  iOS Device  │     │  MTD Cloud   │     │  UEM/MDM     │
│              │     │              │     │  Server      │
│ MTD Agent ───┼────>│ Threat       │     │              │
│              │     │ Analysis ────┼────>│ Compliance   │
│              │     │              │     │ Engine       │
│ MDM Agent <──┼─────┼──────────────┼─────┤              │
│              │     │              │     │ Enforcement: │
│              │     │              │     │ - Block apps │
│              │     │              │     │ - Wipe device│
│              │     │              │     │ - Revoke VPN │
│              │     │              │     │ - Quarantine │
└──────────────┘     └──────────────┘     └──────────────┘
```

When the MTD agent detects a threat (jailbreak, malicious app, network attack), it reports to the cloud engine, which updates the device's compliance status in the UEM. The UEM then enforces the appropriate policy (conditional access denial, selective wipe, VPN certificate revocation).

**Key MTD products**: Lookout, Zimperium (zIPS), Check Point Harmony Mobile, Microsoft Defender for Endpoint (mobile), CrowdStrike Falcon for Mobile, Jamf Threat Defense (formerly Wandera).

### 13.3 Carrier-level defenses

**STIR/SHAKEN (Secure Telephone Identity Revisited / Signature-based Handling of Asserted information using toKENs)**:

A framework for authenticating caller ID to combat robocalling and caller ID spoofing:

- **STIR**: the originating carrier signs the SIP INVITE with a certificate (X.509 from an authorized CA, the STI-CA). The signature (PASSporT -- Personal Assertion Token) attests that the carrier has verified the calling number belongs to the caller.
- **SHAKEN**: the terminating carrier verifies the PASSporT signature and assigns an attestation level:
  - **A (Full)**: carrier has authenticated the caller and verified they are authorized to use the number
  - **B (Partial)**: carrier has authenticated the caller but cannot verify number authorization
  - **C (Gateway)**: carrier received the call from a gateway or international source

**SMS filtering**:

- iOS 11+ supports `ILMessageFilterExtension` -- a Message Filter Extension that apps can provide to classify SMS from unknown senders
- Carrier-level SMS firewalls (e.g., Proofpoint/Cloudmark, Adaptive Mobile) filter at the SMSC before delivery
- Apple's built-in "Filter Unknown Senders" feature sorts messages from non-contacts into a separate tab

**RCS (Rich Communication Services) security**:

- RCS Universal Profile does not include end-to-end encryption by default (messages are encrypted in transit between device and carrier, but the carrier has access)
- Google Messages implements E2E encryption for RCS in direct messages (proprietary extension, not part of GSMA spec)
- Apple adopted RCS in iOS 18 but without E2E encryption (fallback to carrier-level encryption only)
- Security implication: RCS messages between iOS and Android are not E2E encrypted, unlike iMessage-to-iMessage or Signal-to-Signal

### 13.4 Private 5G/LTE network security

Organizations deploying private cellular networks (CBRS band in the US, or licensed spectrum) face unique security considerations:

**Architecture options**:
- **Standalone private network**: fully isolated core and RAN, no connection to public PLMN. Highest security but requires full infrastructure management.
- **Shared RAN**: private spectrum with RAN shared between public and private network. MOCN (Multi-Operator Core Network) or MORAN (Multi-Operator RAN) architecture.
- **Network slicing**: a dedicated slice on a public operator's 5G network, with logical isolation. Security depends on the operator's slicing implementation.

**Hardening checklist**:

```
- [ ] USIM/eSIM provisioning: use organization-controlled SIM profiles
      with strong Ki/OPc keys (256-bit AES for 5G)
- [ ] Mutual authentication: ensure 5G-AKA or EAP-TLS between UE and
      private core network (AMF/AUSF/UDM)
- [ ] User plane encryption: enforce NEA2 (AES-128) or NEA3 (SNOW3G)
      on the air interface; NIA2/NIA3 for integrity
- [ ] Backhaul encryption: IPsec between gNB and core network functions
- [ ] Physical security: tamper-evident enclosures for small cells,
      surveillance of antenna sites
- [ ] Access control: whitelist allowed IMSIs/SUPIs; reject unknown UEs
- [ ] Monitoring: deploy signaling firewall between private and any
      interconnected public network
- [ ] Firmware management: keep gNB and core NFs patched; track CVEs
      for OpenRAN components (O-DU, O-CU, O-RU)
- [ ] Network slicing isolation: if using slicing, verify that slice
      isolation is enforced at UPF level (separate PDU sessions,
      separate QoS flows, no cross-slice data leakage)
```

### 13.5 Mobile application vetting pipeline

Automated security vetting of mobile apps before enterprise deployment:

**Pipeline stages**:

```
┌─────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ 1. Ingest   │──>│ 2. Static    │──>│ 3. Dynamic   │──>│ 4. Report &  │
│             │   │    Analysis   │   │    Analysis   │   │    Gate      │
│ IPA upload  │   │ SAST         │   │ DAST         │   │              │
│ or MDM pull │   │ Binary scan  │   │ Runtime test │   │ Pass/Fail    │
│             │   │ Entitlements │   │ Network mon  │   │ Risk score   │
└─────────────┘   └──────────────┘   └──────────────┘   └──────────────┘
```

**Static analysis** (SAST for iOS):

```bash
# Extract IPA and analyze
unzip -o target.ipa -d extracted/
cd extracted/Payload/TargetApp.app/

# 1. Check binary protections
otool -hv TargetApp                    # Check PIE flag
otool -Iv TargetApp | grep _objc_      # ObjC method calls
otool -l TargetApp | grep -A2 LC_ENCRYPTION  # Encryption info

# 2. Check entitlements
codesign -d --entitlements :- TargetApp 2>/dev/null
# Or on Linux with ldid:
ldid -e TargetApp

# 3. Scan for hardcoded secrets
strings TargetApp | grep -iE "(api[_-]?key|secret|password|token|aws)" | head -20

# 4. Check ATS configuration
plutil -p Info.plist | grep -A 30 "NSAppTransportSecurity"

# 5. Check for dangerous APIs
strings TargetApp | grep -E "(UIPasteboard|NSLog|canOpenURL:)" | head -10

# 6. MobSF automated scan
# docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest
# Upload IPA via web interface at http://localhost:8000
```

**Dynamic analysis** (DAST):

```bash
# Frida-based runtime analysis
frida -U -f com.target.app --no-pause -l dast_checks.js

# dast_checks.js content:
# - Hook NSURLSession to log all network requests
# - Hook UIPasteboard to detect clipboard usage
# - Hook CCCrypt to detect weak crypto (DES, 3DES, ECB mode)
# - Hook NSFileManager to detect insecure file storage
# - Hook NSUserDefaults to detect sensitive data in defaults

# Network interception (via mitmproxy or Burp Suite)
mitmproxy --mode transparent --ssl-insecure \
    --set block_global=false \
    -s analyze_mobile_traffic.py
```

---

## 14. Mobile Forensics Deep Dive

This section extends the device-level forensics covered in section 8 (checkm8 acquisition, libimobiledevice, sysdiagnose, crash logs, KnowledgeC) with cloud acquisition, app-level database forensics, mobile network forensics, evidence handling procedures, and timeline reconstruction.

### 14.1 iOS acquisition method matrix

| Method | Scope | Device State | Tool Examples | A12+ Support |
|--------|-------|-------------|---------------|-------------|
| Logical (iTunes backup) | App data, contacts, messages, photos | AFU, passcode known | `idevicebackup2`, iTunes | Yes |
| Advanced logical | Logical + crash logs, sysdiagnose, profiles | AFU, passcode known | `libimobiledevice`, `idevicecrashreport` | Yes |
| Full filesystem (checkm8) | Complete filesystem | DFU mode (BFU/AFU) | palera1n, checkra1n | No (A5-A11 only) |
| Full filesystem (exploit agent) | Complete filesystem | AFU, passcode known | Cellebrite UFED, GrayKey | Yes (vendor-dependent) |
| Cloud (iCloud backup) | Backup data from iCloud | N/A (remote) | Elcomsoft Phone Breaker, `icloudpd` | N/A |
| Cloud (iCloud sync data) | Photos, Keychain, Messages, Health | N/A (remote) | Elcomsoft Phone Extractor | N/A |

### 14.2 Cloud acquisition: iCloud

**iCloud backup extraction** requires the Apple ID credentials (or an authentication token) and, if enabled, must pass two-factor authentication.

```bash
# icloudpd (open-source iCloud Photos downloader)
# Install: pip install icloudpd
icloudpd --username target@icloud.com \
    --directory /path/to/output/ \
    --auto-delete \
    --log-level info

# For full iCloud backup extraction (not just photos):
# Commercial tools: Elcomsoft Phone Breaker, Oxygen Forensic Cloud Extractor
# These tools use Apple's documented (and undocumented) iCloud APIs to pull:
# - Full backup snapshots
# - iCloud Keychain (if escrow key is available)
# - Messages in iCloud
# - iCloud Drive files
# - Health data
# - Safari history/bookmarks

# Authentication token extraction from macOS Keychain
# (if examiner has access to a macOS machine logged into the target Apple ID)
security find-generic-password -s "com.apple.account.AppleIDAuthentication.token" \
    -w ~/Library/Keychains/login.keychain-db 2>/dev/null
```

**Forensic considerations for iCloud acquisition**:
- Two-factor authentication requires access to a trusted device or phone number
- Apple notifies the account owner of new device sign-ins (detection risk in covert operations)
- iCloud backups do not include: data from apps that opted out of backup, Keychain items marked `ThisDeviceOnly`, Face ID/Touch ID data, Apple Pay data
- iCloud data is encrypted at rest on Apple's servers with keys partially managed by Apple (except for Advanced Data Protection, which is E2E encrypted with user-held keys -- if ADP is enabled, cloud acquisition is not possible without the device passcode or recovery key)

### 14.3 App-level database forensics

**WhatsApp**:

WhatsApp on iOS stores messages in a SQLite database (`ChatStorage.sqlite`) within the app's sandbox. In an iTunes backup, it is located by its file hash.

```bash
# Locate WhatsApp database in iTunes backup
# The database domain: AppDomainGroup-group.net.whatsapp.WhatsApp.shared
# Manifest.db maps domains/paths to file hashes

sqlite3 Manifest.db "SELECT fileID, relativePath FROM Files \
    WHERE domain LIKE '%whatsapp%' AND relativePath LIKE '%ChatStorage%';"

# WhatsApp encrypts the database with a key stored in the Keychain
# For encrypted backups: the Keychain items are included, and the key
# can be extracted from the backup's Keychain plist

# Once decrypted, query messages:
sqlite3 ChatStorage.sqlite << 'SQL'
SELECT
    ZWAMESSAGE.ZTEXT,
    ZWAMESSAGE.ZMESSAGEDATE + 978307200 AS timestamp_unix,
    datetime(ZWAMESSAGE.ZMESSAGEDATE + 978307200, 'unixepoch') AS timestamp_human,
    ZWACHATSESSION.ZCONTACTJID AS contact,
    CASE ZWAMESSAGE.ZISFROMME
        WHEN 1 THEN 'Sent'
        ELSE 'Received'
    END AS direction
FROM ZWAMESSAGE
LEFT JOIN ZWACHATSESSION ON ZWAMESSAGE.ZCHATSESSION = ZWACHATSESSION.Z_PK
ORDER BY ZWAMESSAGE.ZMESSAGEDATE DESC
LIMIT 50;
SQL

# Note: WhatsApp uses Core Data (NSManagedObject), so dates are stored as
# seconds since 2001-01-01 (Core Data epoch). Add 978307200 to convert to Unix epoch.
```

**Signal**:

Signal on iOS uses SQLCipher to encrypt its database (`signal.sqlite`). The encryption key is stored in the iOS Keychain under the app's access group.

```bash
# Signal database location in backup:
# AppDomainGroup-group.org.whispersystems.signal.group/
# Database: grdb/signal.sqlite

# The SQLCipher key is stored in the Keychain as:
# Service: org.whispersystems.signal
# Account: GRDBDatabaseCipherKeySpec
# The key is a 64-byte hex string (32-byte key)

# With the key extracted from an encrypted backup's Keychain:
sqlcipher signal.sqlite
sqlite> PRAGMA key = "x'<64-hex-char-key>'";
sqlite> PRAGMA cipher_page_size = 4096;
sqlite> SELECT * FROM model_TSInteraction ORDER BY timestamp DESC LIMIT 20;
```

**Telegram**:

Telegram stores cached messages in a custom binary format and SQLite databases. Unlike WhatsApp and Signal, Telegram's "Cloud Chats" are not stored locally long-term (they are fetched from Telegram's servers). However, "Secret Chats" are device-local.

```bash
# Telegram database locations in backup:
# AppDomain-ph.telegra.Telegraph/
# Documents/telegram-data/db_sqlite (account database)
# Documents/telegram-data/postbox/ (message cache, binary format)

# The postbox database uses a custom binary serialization format
# Tools: Oxygen Forensic Detective, Belkasoft Evidence Center can parse it
# Manual analysis requires reverse-engineering the serialization schema

# Basic account info from the SQLite layer:
sqlite3 db_sqlite "SELECT key, value FROM t1 WHERE key LIKE '%user%' LIMIT 10;"
```

### 14.4 Mobile network forensics

Mobile network forensics operates on carrier-side data and is typically obtained via legal process (court order, warrant, national security letter).

**Call Detail Records (CDR) analysis**:

CDRs contain metadata for every call, SMS, and data session:

```
CDR fields (typical):
─────────────────────────────────────────────────────────
Field               Description
─────────────────────────────────────────────────────────
calling_number      MSISDN of originating party
called_number       MSISDN of terminating party
start_time          UTC timestamp of call/SMS initiation
duration            Call duration in seconds (0 for SMS)
record_type         MO-Call, MT-Call, MO-SMS, MT-SMS, Data
cell_id             Serving cell at time of event
lac_tac             Location Area Code / Tracking Area Code
imei                Device identifier
imsi                Subscriber identifier
```

**Cell tower triangulation**:

```python
# Simplified cell tower triangulation from CDR data
# Requires cell tower location database (OpenCelliD format)

import math
from dataclasses import dataclass

@dataclass(frozen=True)
class CellTower:
    cell_id: str
    lat: float
    lon: float
    range_m: float  # estimated coverage radius

@dataclass(frozen=True)
class CDREvent:
    timestamp: str
    cell_id: str
    event_type: str

def estimate_location(events: list[CDREvent],
                      towers: dict[str, CellTower]) -> tuple[float, float]:
    """Estimate device location from CDR events using centroid method.
    
    For a single cell: location is the tower's coordinates with
    uncertainty equal to the cell's coverage radius.
    For multiple cells in a short time window: centroid of towers
    weighted by inverse coverage radius (smaller cells = higher precision).
    """
    lats, lons, weights = [], [], []
    for event in events:
        tower = towers.get(event.cell_id)
        if tower is None:
            continue
        weight = 1.0 / max(tower.range_m, 100)
        lats.append(tower.lat * weight)
        lons.append(tower.lon * weight)
        weights.append(weight)

    if not weights:
        raise ValueError("No matching towers found")

    total_weight = sum(weights)
    return (sum(lats) / total_weight, sum(lons) / total_weight)
```

**IMEI tracking**: the IMEI (International Mobile Equipment Identity) persists across SIM changes. If a suspect swaps SIM cards, CDR analysis can track the IMEI across different MSISDNs/IMSIs. Carrier systems log IMEI in every CDR. A warrant for "all CDRs associated with IMEI 35-XXXXXX-XXXXXX-X" reveals every subscriber identity used with that device.

### 14.5 Evidence handling procedures

**Faraday isolation**:

```
CRITICAL: Immediately upon seizure, place the device in a Faraday bag
or Faraday enclosure to prevent:
- Remote wipe commands (MDM, Find My iPhone, iCloud wipe)
- Network-triggered data destruction
- Additional data being written (new messages, location updates)
- Evidence tampering via remote access

Faraday bag procedure:
1. Do NOT power off the device (preserves volatile RAM, maintains AFU state)
2. Enable airplane mode BEFORE placing in Faraday bag (if screen accessible)
   - If screen is locked: place directly in Faraday bag
3. Connect external battery pack to prevent shutdown (maintains AFU state)
4. Seal Faraday bag and verify RF isolation with test device
5. Document: device model, serial number, IMEI, current time (UTC),
   screen state (locked/unlocked), battery level
```

**Chain of custody documentation**:

```
Evidence Item:     Apple iPhone 15 Pro, Gold, 256GB
Serial Number:     DNXXXXXXXXX
IMEI:             35-XXXXXX-XXXXXX-X
UDID:             <40-hex-char>
Condition:         Screen intact, powered on, screen locked
Battery Level:     72%
Seizure DateTime:  2025-01-15T14:32:00Z
Seized By:         [Examiner name, badge/ID]
Location:          [Address, room, specific location]
Faraday Sealed:    2025-01-15T14:33:00Z
Transferred To:    [Lab name, examiner]
Transfer DateTime: 2025-01-15T16:00:00Z
SHA-256 of Image:  [computed after acquisition]
```

**Forensic imaging procedure**:

```bash
# 1. Document device state
ideviceinfo -u <UDID> > device_info.txt

# 2. Create logical acquisition (if passcode available)
mkdir -p /evidence/case_2025_001/backup/
idevicebackup2 backup --full /evidence/case_2025_001/backup/

# 3. Verify backup integrity
idevicebackup2 info /evidence/case_2025_001/backup/

# 4. Hash the backup for chain of custody
find /evidence/case_2025_001/backup/ -type f -exec sha256sum {} \; \
    > /evidence/case_2025_001/backup_hashes.sha256

# 5. Pull crash reports and sysdiagnose separately
idevicecrashreport -e /evidence/case_2025_001/crashes/
# Trigger sysdiagnose: Vol Up + Vol Down + Power (1-2 sec)
# Then extract via: idevicecrashreport (sysdiagnose appears in crash dir)

# 6. Create forensic container (E01 or AFF4 for disk images)
# For logical backups, tar + hash is standard practice
cd /evidence/case_2025_001/
tar cf case_2025_001_backup.tar backup/
sha256sum case_2025_001_backup.tar > case_2025_001_backup.tar.sha256
```

### 14.6 Timeline reconstruction from mobile artifacts

Timeline reconstruction correlates artifacts from multiple sources into a unified chronological view. Key data sources and their timestamp formats:

```
Source                  Location                               Timestamp Format
──────────────────────  ─────────────────────────────────────  ─────────────────────
KnowledgeC              knowledgeC.db                          Core Data (s since 2001-01-01)
Call History            CallHistory.storedata                  Core Data epoch
SMS/iMessage            sms.db                                Core Data epoch (ZDATE)
Safari History          History.db                             Core Data epoch
Location (Significant)  cache_encryptedB.db                   Core Data epoch
Health Data             healthdb_secure.sqlite                 Core Data epoch
Wi-Fi Connections       com.apple.wifi.known-networks.plist   Core Data epoch
Photos (EXIF)           Photos.sqlite (ZDATECREATED)          Core Data epoch
App Install/Remove      MobileInstallation logs               Unified log timestamp
Crash Reports           *.ips files                           ISO 8601
CDR (carrier-side)      Carrier database                      UTC (format varies)
```

**Reconstruction approach**:

```python
# Unified timeline builder for iOS forensic analysis
import sqlite3
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

CORE_DATA_EPOCH = datetime(2001, 1, 1, tzinfo=timezone.utc)

@dataclass(frozen=True)
class TimelineEvent:
    timestamp: datetime
    source: str
    event_type: str
    detail: str

def core_data_to_utc(cd_timestamp: float) -> datetime:
    """Convert Core Data timestamp to UTC datetime."""
    return CORE_DATA_EPOCH + timedelta(seconds=cd_timestamp)

def extract_sms_events(sms_db_path: str) -> list[TimelineEvent]:
    """Extract SMS/iMessage events from sms.db."""
    conn = sqlite3.connect(sms_db_path)
    cursor = conn.execute("""
        SELECT ZDATE, ZTEXT, ZISFROMME, ZHANDLE.ZUNCANONICALIZED_ID
        FROM ZMESSAGE
        LEFT JOIN ZHANDLE ON ZMESSAGE.ZHANDLE = ZHANDLE.Z_PK
        WHERE ZDATE IS NOT NULL
        ORDER BY ZDATE
    """)
    events = []
    for row in cursor:
        ts = core_data_to_utc(row[0])
        direction = "Sent" if row[2] == 1 else "Received"
        contact = row[3] or "Unknown"
        events.append(TimelineEvent(
            timestamp=ts,
            source="sms.db",
            event_type=f"iMessage/{direction}",
            detail=f"{direction} message to/from {contact}: {(row[1] or '')[:80]}"
        ))
    conn.close()
    return events

def extract_knowledgec_events(kc_db_path: str) -> list[TimelineEvent]:
    """Extract app usage events from KnowledgeC."""
    conn = sqlite3.connect(kc_db_path)
    cursor = conn.execute("""
        SELECT ZOBJECT.ZSTARTDATE, ZOBJECT.ZENDDATE,
               ZOBJECT.ZSTREAMNAME, ZOBJECT.ZVALUESTRING
        FROM ZOBJECT
        WHERE ZSTREAMNAME = '/app/usage'
        AND ZSTARTDATE IS NOT NULL
        ORDER BY ZSTARTDATE
    """)
    events = []
    for row in cursor:
        start_ts = core_data_to_utc(row[0])
        end_ts = core_data_to_utc(row[1]) if row[1] else None
        duration = (end_ts - start_ts).total_seconds() if end_ts else 0
        events.append(TimelineEvent(
            timestamp=start_ts,
            source="knowledgeC.db",
            event_type="App Usage",
            detail=f"{row[3]} used for {duration:.0f}s"
        ))
    conn.close()
    return events

def build_unified_timeline(*event_lists: list[TimelineEvent]) -> list[TimelineEvent]:
    """Merge multiple event lists into a single sorted timeline."""
    all_events: list[TimelineEvent] = []
    for event_list in event_lists:
        all_events.extend(event_list)
    return sorted(all_events, key=lambda e: e.timestamp)
```

**Correlating device-side and network-side data**:

The unified timeline becomes most powerful when device artifacts (extracted per section 8 and above) are merged with carrier CDRs (section 14.4). For example:
- A KnowledgeC "device unlock" event at 14:32:15 UTC correlated with a CDR showing an outbound call at 14:32:18 from Cell ID 12345 places the suspect at a specific location at a specific time, with two independent evidence sources.
- An iMessage delivery timestamp correlated with the absence of a CDR (no SMS/call via carrier) confirms the message was sent over data (Wi-Fi or cellular data) rather than the traditional SMS path.
- Gaps in device activity (no KnowledgeC events, no app usage) correlated with CDR data showing continued cell tower registrations suggest the device was powered on but unused -- consistent with the device being in a Faraday bag, lost, or in the possession of someone who does not know the passcode.

---

## 15. Cross-references

**To Chapter 15A:** Android and iOS share the same mobile network infrastructure. The 5G security architecture (section 10) applies equally to both platforms. Android's Play Integrity (Chapter 15A section 8) and iOS's Secure Enclave attestation (section 1.6) are the device-integrity mechanisms that network operators can use to verify device trustworthiness.

**To Domain 9 Chapter 9B section 3:** SS7 and Diameter attacks are covered there. This chapter extends with 5G-specific architecture (SBA, SUCI, SEPP, network slicing) and the cross-generational SMS interception comparison.

**To Domain 5:** iOS kernel exploitation (section 2.1) uses the same primitives as Domain 5 (kernel UAF, heap spray, code execution). PAC bypass (section 2.2) and PPL circumvention (section 2.3) are the iOS-specific hardening layers that the attacker must defeat beyond generic kernel-exploitation techniques.

**To Domain 4:** PAC (section 1.8) is the ARM backward-edge CFI described in Domain 4 section 11. PPL (section 1.8) is an iOS-specific W^X enforcement layer that prevents kernel exploits from disabling code signing via page-table manipulation.

**To Domain 7 Chapter 7B:** The PACMAN speculative PAC bypass (section 2.2) is the ARM-specific variant of speculative execution attacks covered in Domain 7.

**OWASP MASTG mapping:** sections 3-5 align with OWASP Mobile Application Security Testing Guide categories: MSTG-STORAGE (data storage, section 3.4), MSTG-NETWORK (transport security, sections 3.3, 5), MSTG-PLATFORM (IPC/URL schemes, section 4), MSTG-CODE (binary protections, section 3.1), MSTG-RESILIENCE (anti-tampering and jailbreak detection, section 3.2).

---

## 16. Exercises

### Exercise 15B-1 — iOS app reverse engineering and Keychain extraction

**Objective.** Extract and decrypt an iOS IPA, analyze the binary for security weaknesses, and dump Keychain items using objection.

**Steps.**

1. On a jailbroken device (palera1n or Dopamine), dump the decrypted IPA using `frida-ios-dump`: `python3 dump.py com.target.app`. Transfer the IPA to the analysis workstation.
2. Extract the Mach-O binary from the IPA. Run `jtool2 --ent TargetApp` to extract entitlements. Run `otool -L TargetApp` to list linked frameworks. Check binary protections: PIE (`-fPIC`), stack canary (`___stack_chk_fail`), ARC (presence of `objc_release`).
3. Run `class-dump -H TargetApp -o headers/` to extract Objective-C class interfaces. Search headers for authentication, crypto, and storage classes.
4. Connect with objection: `objection -g com.target.app explore`. Run `ios keychain dump --json`. Identify: accessibility attributes, access groups, and any plaintext secrets.
5. Run `env` to find the app container path. Navigate to `Library/Preferences/` and dump NSUserDefaults: `ios plist cat com.target.app.plist`. Search for tokens, session IDs, and API keys.

**Deliverable.** Binary protection checklist, entitlements analysis, Keychain dump (redacted), NSUserDefaults secrets found, and a severity-rated findings report.

### Exercise 15B-2 — Frida hooking on iOS: authentication bypass and request logging

**Objective.** Write Frida scripts to hook iOS authentication methods, log all HTTP requests, and bypass a jailbreak detection implementation.

**Steps.**

1. Identify the target app's login method via class-dump or `frida-trace -U -f com.target.app -m "*[*Login*]"`.
2. Write a Frida script hooking `NSURLSession dataTaskWithRequest:completionHandler:` to log all HTTP method, URL, headers, and body for every network request (use the ObjC bridge as shown in §3.2).
3. Write a Frida script hooking `NSFileManager fileExistsAtPath:` to hide jailbreak artifacts (`/var/jb`, `/Applications/Cydia.app`, `/usr/sbin/sshd`). Test by launching the app with the script — verify it passes the jailbreak check.
4. For Swift apps: use `Module.enumerateExports` to find mangled method names. Hook the authentication method by address, log parameters, and force-return `true` to bypass authentication.
5. Compare Frida-based bypass with objection's automated `ios jailbreak disable` command. Document which checks each approach defeats.

**Deliverable.** Three Frida scripts (request logger, jailbreak bypass, auth bypass) with annotated console output, and a comparison table of Frida vs objection coverage.

### Exercise 15B-3 — SSL certificate pinning bypass on iOS

**Objective.** Bypass SSL certificate pinning on an iOS app implementing three different pinning mechanisms: SecTrustEvaluateWithError, TrustKit, and custom NSURLSession delegate.

**Steps.**

1. Configure Burp Suite proxy. Install Burp CA on the device via Settings > Profile. Set device proxy to the Burp host.
2. Launch the target app. Confirm pinning blocks traffic (Burp shows no HTTPS requests; app shows connection error).
3. **Method 1 — Frida script.** Load the `ssl_bypass.js` script from §3.3 targeting `SecTrustEvaluateWithError` and `SecTrustEvaluate`. Launch: `frida -U -f com.target.app -l ssl_bypass.js`. Verify traffic appears in Burp.
4. **Method 2 — objection.** Connect: `objection -g com.target.app explore`. Run `ios sslpinning disable`. Document which hooks are applied (AFNetworking, NSURLSession, TrustKit).
5. **Method 3 — SSL Kill Switch 2.** Install via Cydia/Sileo on the jailbroken device. Enable for the target app in Settings. Verify traffic interception.
6. Test against a TrustKit-pinned app. If generic bypass fails, write a targeted Frida script hooking `TrustKit`'s `evaluateTrust:forHostname:` method.

**Deliverable.** Burp traffic captures per bypass method, Frida/objection console output, a comparison matrix of bypass method vs pinning implementation, and recommendations for pinning hardening.

### Exercise 15B-4 — iOS forensic acquisition and sysdiagnose analysis

**Objective.** Perform forensic acquisition of an iOS device using checkm8-based tools and analyze sysdiagnose data to reconstruct a user-activity timeline.

**Steps.**

1. For an A8-A11 device: put into DFU mode and use palera1n to exploit checkm8 and establish SSH access. For A12+ (no checkm8): use `idevicebackup2` for logical acquisition with an encrypted backup.
2. Extract the filesystem: `ssh -p 2222 root@localhost 'tar -cf - /var/mobile/' > mobile_data.tar`. Hash the archive: `sha256sum mobile_data.tar`.
3. Trigger sysdiagnose on the device (Volume Up + Volume Down + Power, 1-2 seconds). Pull via: `idevicecrashreport -e /path/to/output/`. Extract the `.tar.gz`.
4. Parse KnowledgeC: `sqlite3 knowledgeC.db` — query app usage timestamps, device lock/unlock events, and media playback. Build a timeline for a 24-hour window.
5. Parse PowerLog: query process network activity to identify apps with unexpected background data usage (potential spyware indicator).
6. Search crash reports for exploitation indicators: `grep -r "EXC_BAD_ACCESS" crashes/ | grep -i "imagent\|IMTranscoderAgent\|mediaserverd"`.

**Deliverable.** SHA256-verified acquisition log, KnowledgeC activity timeline, PowerLog network-usage report, crash-report analysis, and a unified forensic timeline in CSV format.

### Exercise 15B-5 — 5G security architecture assessment

**Objective.** Map the 5G Service-Based Architecture security controls and identify attack surfaces in a lab or simulated 5G core deployment.

**Steps.**

1. Using Open5GS or free5GC as a lab 5G core, deploy the SBA network functions: AMF, SMF, UPF, AUSF, UDM, NRF. Configure TLS 1.3 for inter-NF communication.
2. Register a test UE (simulated with UERANSIM). Capture the registration flow. Verify SUCI is sent (not SUPI) over the N1 interface. Decode the SUCI ECIES encryption using the home-network private key.
3. Examine the 5G-AKA authentication exchange: capture RAND, AUTN, RES* messages between AMF and AUSF. Verify mutual authentication (UE authenticates the network via AUTN verification).
4. Test NRF authorization: attempt to query the NRF for NF discovery without a valid OAuth 2.0 token. Verify the request is rejected. Then use a valid token and confirm discovery succeeds.
5. Assess network-slicing isolation: configure two slices with different SST values. Verify that a UE authorized for Slice A cannot access Slice B resources. Test shared-UPF scenarios for data-plane isolation.

**Deliverable.** Network diagram of the lab 5G core, SUCI decryption walkthrough, 5G-AKA message trace, NRF authorization test results, and a slicing-isolation assessment with identified gaps.

---

## 17. Readings and References

> All URLs verified and retrieved: 2026-05-29.

### Standards and specifications

- Apple, "Apple Platform Security" (2025): https://support.apple.com/guide/security/welcome/web
- 3GPP TS 33.501 v18 — "Security architecture and procedures for 5G System" (2025): https://www.3gpp.org/DynaReport/33501.htm
- 3GPP TS 33.510 — "Security Assurance Specification for 5G" (2025): https://www.3gpp.org/DynaReport/33510.htm
- OWASP, "Mobile Application Security Testing Guide (MASTG) v2" (2025): https://mas.owasp.org/MASTG/

### Vulnerability advisories and spyware research

- CVE-2021-30860 — FORCEDENTRY (CoreGraphics JBIG2 integer overflow, NSO Pegasus). Citizen Lab (September 2021): https://citizenlab.ca/2021/09/forcedentry-nso-group-imessage-zero-click-exploit-captured-in-the-wild/
- CVE-2019-8900 — checkm8 (BootROM UAF, A5-A11). axi0mX (September 2019): https://nvd.nist.gov/vuln/detail/CVE-2019-8900
- Citizen Lab, "PWNYOURHOME: iMessage zero-click HomeKit exploit" (2023): https://citizenlab.ca/2023/04/nso-group-zero-click-homekit-exploit/
- Citizen Lab, "QuaDream REIGN spyware analysis" (2023): https://citizenlab.ca/2023/04/spyware-vendor-quadream-exploits-victims-governments/
- Google TAG, "Predator / Cytrox spyware analysis" (2023): https://blog.google/threat-analysis-group/

### Tools and frameworks

- Frida, "Dynamic Instrumentation Toolkit" (2026): https://frida.re/
- objection, "Runtime Mobile Exploration" (2026, v1.12.4): https://github.com/sensepost/objection
- palera1n, "iOS 15-17 jailbreak (checkm8 + KPF)" (2025): https://palera.in/
- libimobiledevice, "Cross-platform iOS device tools" (2025): https://libimobiledevice.org/
- TrustKit, "iOS/macOS SSL pinning library" (2025): https://github.com/datatheorem/TrustKit
- Open5GS, "Open-source 5G Core" (2025): https://open5gs.org/
- UERANSIM, "Open-source 5G UE/gNB simulator" (2025): https://github.com/aligungr/UERANSIM
- MobSF, "Mobile Security Framework" (2025): https://github.com/MobSF/Mobile-Security-Framework-MobSF

### MITRE ATT&CK references

- T1437 — Application Layer Protocol (Mobile): https://attack.mitre.org/techniques/T1437/
- T1630.002 — Indicator Removal: File Deletion (Mobile): https://attack.mitre.org/techniques/T1630/002/
- T1636.004 — SMS Interception: https://attack.mitre.org/techniques/T1636/004/
- T1404 — Exploitation for Privilege Escalation (Mobile): https://attack.mitre.org/techniques/T1404/
- T1398 — Boot or Logon Initialization Scripts (Mobile): https://attack.mitre.org/techniques/T1398/

---

## 18. Cross-References (table)

| Section | Related Chapter | Topic | Relationship |
|---------|----------------|-------|-------------|
| §1 Boot chain / AMFI | Domain 4 §11, Domain 5 Ch. 5B | ARM CFI (PAC), kernel exploitation | PAC and PPL are the iOS-specific hardening layers constraining kernel exploits |
| §2 Exploitation | Domain 7 Ch. 7B | Speculative execution | PACMAN is the ARM-specific variant of speculative side-channel attacks |
| §3 App testing (Frida) | Chapter 15A §5 | Android Frida / objection | Same Frida runtime, different platform hooks (ObjC/Swift vs Java/JNI) |
| §6 Spyware (Pegasus) | Domain 12 Ch. 12A | Reverse engineering, exploit analysis | Zero-click chains require the same RE pipeline (disassembly, heap analysis) |
| §9-10 Mobile network / 5G | Domain 9 Ch. 9B §3 | SS7/Diameter signaling attacks | 5G SBA extends and replaces the signaling attack surface of SS7/Diameter |
| §8 Forensics | Chapter 15A §12 | Android forensics | Same evidence categories (storage, network, timeline) on different platform |

---

## 19. Glossary

| Term | Definition |
|------|-----------|
| **AMFI (Apple Mobile File Integrity)** | Kernel extension that intercepts code execution and delegates signature verification to the userspace `amfid` daemon via CoreTrust; the enforcement layer for iOS code signing. |
| **checkm8** | Unpatchable BootROM use-after-free vulnerability (CVE-2019-8900) affecting A5-A11 chips; the foundation for palera1n jailbreaks and forensic acquisition tools. |
| **Trust Cache** | Kernel-loaded list of CDHashes (Code Directory Hashes) for Apple-signed binaries; rootless jailbreaks inject CDHashes to allow unsigned code without disabling AMFI. |
| **PAC (Pointer Authentication Codes)** | ARM hardware feature (A12+) that signs and verifies pointers using device-specific keys; protects return addresses, vtable pointers, and function pointers from corruption. |
| **PPL (Page Protection Layer)** | Hardware-enforced separation within EL1 on A12+; only PPL code can modify page tables, preventing kernel exploits from creating W+X mappings or bypassing code signing. |
| **KTRR (Kernel Text Read-only Region)** | Hardware lock (A10+) that makes the kernel text segment immutable after boot; enforced by the memory controller, not page tables, preventing in-memory kernel code modification. |
| **Secure Enclave (SEP)** | Separate ARM processor running SepOS with its own encrypted memory bus; handles biometric processing, key management, passcode verification, and Apple Pay tokenization. |
| **Data Protection Classes** | iOS file encryption tiers (Complete, CompleteUnlessOpen, CompleteUntilFirstUserAuthentication, None) controlling when file decryption keys are available based on device lock state. |
| **FORCEDENTRY** | NSO Group's zero-click exploit (CVE-2021-30860) using a malicious PDF with JBIG2-encoded content to achieve code execution via CoreGraphics integer overflow in `IMTranscoderAgent`. |
| **Lockdown Mode** | iOS 16+ extreme protection mode that disables JIT, blocks most iMessage attachment types, restricts HomeKit/FaceTime from unknown contacts, and disables wired connections when locked. |
| **SUCI (Subscription Concealed Identifier)** | 5G subscriber identity concealment using ECIES encryption of the SUPI with the home network's public key, preventing passive IMSI catching over the air interface. |
| **5G-AKA** | 5G Authentication and Key Agreement protocol providing mutual authentication between the UE and network via AUSF/UDM, with anchor key derivation for NAS/AS security. |
| **SEPP (Security Edge Protection Proxy)** | 5G inter-operator security gateway on the N32 interface; supports TLS (full encryption) or PRINS (selective IE encryption) for roaming control-plane messages. |
| **Network Slicing** | 5G capability to create multiple virtual networks (slices) on shared infrastructure, each with dedicated NF instances, QoS parameters, and security policies; isolation is a key security concern. |
| **ePDG (evolved Packet Data Gateway)** | Gateway terminating IKEv2/IPsec tunnels for VoWiFi (Wi-Fi Calling); authenticates the UE via EAP-AKA' using USIM credentials and connects to the IMS core. |
