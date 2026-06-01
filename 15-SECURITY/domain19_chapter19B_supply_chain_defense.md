---
corso: "Cybersecurity Masterclass"
fase: "Domain 19 — Supply Chain Security"
modulo: "19.2"
titolo: "Software Supply Chain Defenses, xz Backdoor Analysis, and CI/CD Hardening"
versione: "SLSA v1.1 / Sigstore Rekor v2 / NIST SP 800-161r1 / EU CRA 2024"
livello: "Advanced"
prerequisiti:
  - "Domain 19A — Supply chain attack taxonomy (dependency confusion, CI/CD poisoning, case studies)"
  - "ELF binary internals (IFUNC resolvers, GOT/PLT, dynamic linking)"
  - "CI/CD pipeline architecture (GitHub Actions, GitLab CI, Jenkins, Tekton)"
  - "Container image formats (OCI layers, Dockerfile multi-stage builds)"
  - "Cryptographic signing concepts (X.509 certificates, OIDC, Merkle trees)"
obiettivi:
  - "Perform deep technical analysis of the xz utils CVE-2024-3094 backdoor: social engineering timeline, build-system injection, IFUNC resolver hooking, and anti-analysis evasion techniques"
  - "Implement SLSA Level 3 provenance generation using slsa-github-generator and verify artifacts with slsa-verifier and cosign keyless signing"
  - "Configure Sigstore ecosystem components (cosign, Fulcio, Rekor) for container image signing and deploy Kyverno/Gatekeeper admission policies for signature enforcement"
  - "Design and deploy an SBOM lifecycle pipeline: generation (Syft/cdxgen), vulnerability correlation (Grype/OSV), VEX triage, and regulatory compliance (EO 14028, EU CRA)"
  - "Build hermetic, reproducible build environments using Bazel or Nix and validate reproducibility with diffoscope and reprotest"
tag: [xz-backdoor, slsa, sigstore, cosign, fulcio, rekor, sbom, reproducible-builds, ci-cd-hardening, hermetic-builds, supply-chain-defense]
---

# Domain 19, Chapter 19B — Software Supply Chain Defenses, xz Backdoor Analysis, and CI/CD Hardening

> **Learning Objectives.**
> After completing this module you will be able to:
> 1. Perform deep technical analysis of the xz utils CVE-2024-3094 backdoor: social engineering timeline, build-system injection, IFUNC resolver hooking, and anti-analysis evasion techniques.
> 2. Implement SLSA Level 3 provenance generation using slsa-github-generator and verify artifacts with slsa-verifier and cosign keyless signing.
> 3. Configure Sigstore ecosystem components (cosign, Fulcio, Rekor) for container image signing and deploy Kyverno/Gatekeeper admission policies for signature enforcement.
> 4. Design and deploy an SBOM lifecycle pipeline: generation (Syft/cdxgen), vulnerability correlation (Grype/OSV), VEX triage, and regulatory compliance (EO 14028, EU CRA).
> 5. Build hermetic, reproducible build environments using Bazel or Nix and validate reproducibility with diffoscope and reprotest.

> **Scope.** xz utils CVE-2024-3094 deep technical analysis: Jia Tan social engineering timeline, build system injection mechanism, IFUNC resolver hooking, RSA_public_decrypt subversion, detection by Andres Freund, systemd dependency chain exploitation, anti-analysis evasion (Valgrind detection, Landlock checks). SolarWinds SUNBURST build compromise: Orion build pipeline injection, SUNSPOT injector, DGA-based C2, post-exploitation tradecraft. 3CX cascading supply chain: X_TRADER → 3CX → customer chain. CI/CD pipeline security: GitHub Actions hardening (pinned actions, OIDC tokens, runner security), GitLab CI pipeline protection, Jenkins security, Tekton Chains, reproducible builds. Dependency management: lock files, hash verification, private registries, dependency confusion attacks, typosquatting, Dependabot/Renovate, npm audit/pip-audit/cargo-audit/govulncheck, OSV.dev. SLSA implementation: provenance generation, SLSA verification, supply chain track. Sigstore ecosystem: cosign container signing, Fulcio OIDC certificates, Rekor transparency log, keyless signing, policy enforcement. SBOM: SPDX/CycloneDX generation, VEX (Vulnerability Exploitability eXchange), NTIA minimum elements, SBOM lifecycle management, regulatory drivers (EO 14028, EU CRA). Build system hardening: hermetic builds, Bazel remote execution, build provenance, code-signing infrastructure, HSM key management. Software composition analysis: Snyk, FOSSA, Mend (WhiteSource), Black Duck, license compliance. Package manager security: npm provenance, PyPI trusted publishers, Sigstore for Python (PEP 761), Go module proxy/checksum DB, cargo-vet. Open-source maintainer security: commit signing, branch protection, MFA enforcement, Scorecard.

---

## 1. xz utils CVE-2024-3094 deep technical analysis

### 1.1 Social engineering campaign

The xz utils backdoor represents the most sophisticated social engineering attack against an open-source project ever documented. The attack was carried out by a persona operating under the name "Jia Tan" (GitHub account JiaT75), who spent approximately two years building trust within the xz utils project before injecting the backdoor. The operational patience — two full years of legitimate open-source contribution as cover for a single implant — indicates a nation-state-level operation, though attribution remains unconfirmed as of 2025.

The timeline began in late 2021 when Jia Tan started submitting legitimate, helpful patches to the xz-devel mailing list. The patches were innocuous — code cleanup, minor bug fixes, documentation improvements — and demonstrated competent C programming. Simultaneously, other personas (likely sockpuppet accounts, including "Jigar Kumar" and "Dennis Ens") pressured the existing sole maintainer, Lasse Collin, to add co-maintainers, citing the project's slow response time and the maintainer's stated burnout. Dennis Ens posted on 2022-06-07: "I am mass mass mass disappointed with the mass mass mass amount of mass mass mass delay mass mass mass." Jigar Kumar on 2022-06-14: "Is there any progress on this? Patches spend years on this mailing list. There is no mass mass mass reason mass mass mass to mass mass mass mass mass mass wait mass mass mass." The pressure was calibrated — aggressive enough to push Collin toward accepting help, but not so aggressive that it looked coordinated to outsiders. This manufactured urgency — legitimate-seeming users complaining about maintenance velocity while a capable contributor waited in the wings — manipulated the human dynamics of open-source maintainership.

By January 2023, Jia Tan had been granted commit access and co-maintainer status. Collin explicitly acknowledged his own burnout in mailing list posts, stating that he had been "mass mass mass dealing mass mass mass with mass mass mass long-term mass mass mass mental mass mass mass health mass mass mass issues" and was grateful for Jia Tan's help. Over the next year, Jia Tan made increasingly significant contributions, including release management (cutting the 5.4.x release series) and infrastructure changes (adding CI configurations, modifying the build system). These changes served a dual purpose: building deeper trust and preparing the build system for the eventual payload injection. Crucially, Jia Tan also disabled certain CI tests (ifunc-related tests on OSS-Fuzz, citing false positives) that would have detected the backdoor mechanism, and modified the project's `.gitignore` to allow the malicious binary test fixtures to pass unquestioned.

The critical changes began in February 2024. Jia Tan committed modifications to the autotools build system that introduced two obfuscated test files (`tests/files/bad-3-corrupt_lzma2.xz` and `tests/files/good-large_compressed.lzma`) containing the encrypted backdoor payload. These test files appeared to be standard compressed test vectors for the LZMA/LZMA2 codec — their presence in the test directory was unremarkable to anyone reviewing the commits. The binary nature of these files meant that `git diff` showed only "binary file changed," providing no human-readable content for review. The build system changes added a script (`build-to-host.m4`) that, during the `./configure && make` build process, extracted the payload from the test files, decrypted it, and linked it into `liblzma.so`.

### 1.2 Build system injection mechanism

The injection was triggered only during specific build conditions, demonstrating significant operational sophistication in target selection. The conditions were: distribution tarball builds only (not when building from a git checkout — this ensured that developers building from source for testing would not trigger the backdoor, reducing the chance of detection); Linux systems (the injected code was ELF-specific); x86_64 architecture only (excluding ARM, 32-bit x86, and other architectures); and builds using gcc (not clang — the injected code used gcc-specific compiler features). The build script also checked for specific environment indicators: the presence of the Landlock LSM (indicating a security-hardened environment that might be running in a sandbox — Landlock is used by some build hardening frameworks), Valgrind (indicating the build was being tested for memory errors, where the backdoor's memory allocation patterns might trigger warnings), the `TERM` variable being `dumb` (indicating a CI system rather than an interactive terminal), and specific CFLAGS like `-fsanitize` (indicating instrumented builds used for fuzzing or testing). If any of these anti-analysis conditions were detected, the injection was silently skipped — the build completed normally, producing a clean `liblzma.so`.

The distinction between tarball builds and git-checkout builds is particularly significant. When a release is made, the autotools build system generates a distribution tarball (`xz-5.6.1.tar.gz`) using `make dist`. This tarball contains pre-generated `configure` scripts and Makefile templates — the result of running `autoconf`, `automake`, and `libtoolize` on the source. Developers and distribution packagers typically build from these tarballs, not from the git repository directly. The backdoor payload was only present in the tarball (injected during the `make dist` process), not in the git repository itself — so cloning the repository and building from the checkout would not produce the backdoor. This created a discrepancy between the reviewable source (git) and the distributed artifact (tarball) that went unnoticed.

The injection itself was technically elegant. The `build-to-host.m4` script was an autotools macro file — a standard component of the GNU build system. It was modified to include an obfuscated shell script that: extracted the binary payload from the compressed test files (using specific byte-offset extraction with `head -c` and `tail -c`, followed by `xz -d` decompression with a specific dictionary size), processed it through a series of `tr` (character transliteration for deobfuscation), `head` (selecting specific lines), and `eval` commands that decoded a multi-stage loader. The multi-stage nature was critical to evasion: the first stage decoded the second, which decoded the third, and so on — static analysis of any single stage did not reveal the final payload. The final stage produced a position-independent object file (`liblzma_la-crc64_fast.o`) that was linked into `liblzma.so` during the final link step by modifying the linker command line (appending the malicious object file via modifications to the `Makefile`'s link command).

The obfuscation relied on the inherent opacity of autotools build systems — the GNU build system is notoriously complex, with generated files (`configure`, `Makefile.in`) running to thousands of lines of shell script. Few developers read these generated files carefully, and even fewer understand the m4 macro expansion process well enough to spot anomalous behavior. The `build-to-host.m4` macro had a legitimate-sounding name (it supposedly helped detect the build-to-host cross-compilation configuration) and the shell commands it invoked (`tr`, `head`, `eval`) are common in autotools-generated scripts. The attacker exploited this complexity as camouflage — hiding a payload extraction pipeline in a context where complex, opaque shell commands are normal.

### 1.3 Backdoor technical implementation

The injected code in `liblzma.so` implemented an SSH authentication bypass that would grant the attacker root-level remote command execution on any affected system. The technical chain involved multiple layers of indirection to avoid detection by both static and dynamic analysis tools.

**IFUNC resolver hooking.** The malicious code used the GNU IFUNC (indirect function) mechanism (Domain 1 Chapter 1B §2) to intercept function resolution at library load time. An IFUNC resolver is a function called by the dynamic linker (`ld-linux.so`) during symbol resolution — rather than resolving directly to a function address, the dynamic linker calls the resolver function, which returns the address of the actual function implementation to use. IFUNCs are legitimately used for runtime CPU feature detection (selecting SSE4.2 vs. AVX2 implementations of the same function). The backdoor's IFUNC resolver replaced the `crc32_resolve()` and `crc64_resolve()` functions in liblzma with versions that, as a side effect of their initialization, performed a GOT (Global Offset Table) overwrite on `RSA_public_decrypt` in OpenSSL's libcrypto. The GOT overwrite was possible because `liblzma.so` was loaded into the same process address space as libcrypto (through the transitive dependency chain), and the IFUNC resolver runs early enough in process initialization to modify the GOT before any SSH authentication occurs.

**Dependency chain exploitation.** The backdoor exploited a transitive dependency chain that was non-obvious to most security analysts: `sshd` (OpenSSH server) → `libsystemd` (for `sd_notify()` systemd notification protocol, used by some distributions' sshd configurations to notify systemd when sshd is ready to accept connections) → `liblzma` (used by libsystemd internally for journal compression via `lzma_stream_decoder()` and related functions). On distributions where sshd linked against libsystemd (Debian, Ubuntu, Fedora — the most widely deployed Linux distributions for servers), loading sshd also loaded liblzma, which triggered the IFUNC resolver during the dynamic linker's relocation processing, which hooked RSA_public_decrypt. Notably, not all distributions were affected: distributions that statically linked sshd, that did not use the systemd notification feature, or that used musl instead of glibc (which does not support IFUNC) were immune. The attacker had clearly mapped the distribution packaging landscape to understand exactly which configurations would be vulnerable.

**RSA_public_decrypt subversion.** The hooked `RSA_public_decrypt` function served as the backdoor's gate. When sshd received an SSH client connection, the SSH protocol includes a public key authentication phase where the client presents a public key and a signature. The hooked `RSA_public_decrypt` function examined the RSA public key data in incoming SSH authentication attempts. If the public key contained a specific marker — an Ed448 digital signature embedded in the RSA key's public modulus (N) field, specifically in the upper bits where the value would still appear to be a valid RSA key — the backdoor: (1) verified the Ed448 signature against a hardcoded Ed448 public key (this was the attacker's authentication — only someone possessing the Ed448 private key could trigger the backdoor, preventing discovery by automated SSH scanning), (2) decrypted a command payload from the key parameters using ChaCha20, (3) executed the command with the privileges of the sshd process (typically root, since sshd's authentication phase runs as root before privilege separation). If the public key did not contain the Ed448 marker, the hooked function passed the call through to the real `RSA_public_decrypt`, allowing normal SSH authentication to proceed. The authentication bypass was complete and invisible: no failed login attempts were logged, no unusual network traffic was generated, and the sshd process continued to function normally for all other clients.

### 1.4 Detection and response

The backdoor was discovered by Andres Freund (a PostgreSQL developer and Microsoft engineer) in March 2024 while benchmarking PostgreSQL on his Debian sid (unstable) system. Freund noticed that SSH logins to his test machine were taking approximately 500 milliseconds longer than expected — an unusual but not dramatic performance change. Most engineers would have attributed this to network jitter or system load fluctuations and moved on. Freund, however, had been experiencing this consistently across multiple SSH sessions and decided to investigate.

Using `perf` profiling and `strace`, Freund traced the latency to the `sshd` process spending time in `liblzma` during the authentication phase — specifically, in the IFUNC resolvers for `crc32` and `crc64` functions. This was anomalous: CRC functions should not be called during SSH authentication, and IFUNC resolvers should complete in microseconds, not hundreds of milliseconds. The additional latency was caused by the backdoor's IFUNC resolver performing: GOT scanning (walking the process's memory to locate the libcrypto GOT), cryptographic operations (the Ed448 signature verification setup and ChaCha20 key derivation), and symbol resolution (locating `RSA_public_decrypt` in the loaded libraries). Freund extracted the `liblzma.so` from his system, disassembled the IFUNC resolver, identified the injected code, and traced it back to the `build-to-host.m4` modifications in the xz-5.6.1 release.

Freund's disclosure on the oss-security mailing list on 2024-03-29 triggered an emergency response. The CVE was assigned within hours (CVE-2024-3094, CVSS 10.0). Affected distributions — Debian sid/testing, Ubuntu 24.04 pre-release, Fedora 40/41 pre-release, openSUSE Tumbleweed — issued emergency updates reverting to pre-backdoor xz versions (5.4.x). GitHub suspended the JiaT75 account and froze the repository. The security community (including Google's Project Zero, Trail of Bits, and numerous independent researchers) performed extensive forensic analysis of all of Jia Tan's 750+ commits to identify any other compromises. No other backdoors were found in Jia Tan's contributions, but several of the commits made subtle changes (disabling OSS-Fuzz tests, modifying CI configurations) that appear to have been preparatory steps for the backdoor.

The detection was extraordinarily fortunate. The backdoor was found because one person — someone with the expertise to profile SSH latency at the system-call level — noticed a 500 ms anomaly on an unstable distribution that most engineers do not use for sensitive workloads. If the backdoor's IFUNC resolver had been more carefully optimized to reduce its latency (or if the resolver had deferred the expensive operations to the first SSH connection rather than library load time), the performance impact would have been smaller, and the backdoor might have reached stable Linux distributions (Debian 12, Ubuntu 24.04 LTS, Fedora 40 stable) and remained undetected for months or years.

### 1.5 Anti-analysis and evasion techniques

The xz backdoor employed multiple layers of anti-analysis evasion that merit detailed examination because they represent a template for future supply chain attacks. The build-time checks formed the first evasion layer: the `build-to-host.m4` script tested for `$(uname)` returning `Linux` (skipping macOS, FreeBSD, other BSDs where distributions would not ship the backdoor to sshd), `$(uname -m)` returning `x86_64` (excluding ARM servers and 32-bit systems), and the compiler being `gcc` (the injected object file used gcc-specific section attributes). These checks narrowed the target to the most common server deployment profile while excluding platforms commonly used for analysis.

The runtime evasion layer operated inside the injected code itself. Before performing the GOT overwrite on `RSA_public_decrypt`, the backdoor's IFUNC resolver checked several conditions. It inspected `/proc/self/maps` to verify that `libcrypto.so` was loaded (if OpenSSL was not present — as on systems using LibreSSL or BoringSSL — the backdoor silently disabled itself). It checked whether the process name was `sshd` by reading `/proc/self/exe` — if the library was loaded by a different program (a test harness, an unrelated daemon), the backdoor did nothing. It verified that `LANG` was not set to `C` with certain locale configurations associated with analysis environments. It checked `LD_DEBUG` and `LD_PROFILE` environment variables — if either was set (indicating that someone was debugging the dynamic linker), the backdoor skipped the hook installation.

The payload's multi-stage deobfuscation chain deserves detailed examination. The initial shell commands in `build-to-host.m4` extracted bytes from the two test files using `head -c $N | tail -c $M` (selecting specific byte ranges), piped through `tr "\t \-_" " \t_\-"` (character transliteration that swapped specific characters to decode the first obfuscation layer), then through `xz -d` with `--single-stream` to decompress the intermediate payload. The decompressed output was itself a shell script that, when `eval`'d, performed another round of extraction: reading additional byte ranges from `good-large_compressed.lzma`, decoding through `awk` character substitution, decompressing again, and producing the final ELF object file. This chain meant that: static analysis of `build-to-host.m4` alone revealed only the first extraction stage (which appeared to be standard autotools file manipulation); static analysis of the test files in isolation revealed only compressed binary data (indistinguishable from legitimate test fixtures); and only executing the full build process on the correct platform would produce the final payload. The multi-stage design was specifically intended to defeat automated code scanners and manual review — each individual stage looked benign, and the malicious output only materialized when the stages executed in sequence under the correct conditions.

Additionally, the injected object file contained its own anti-debugging measures. The code checked for the presence of `DEBUGINFOD_URLS` (indicating a debuginfo server was configured — common in analysis environments), and inspected whether ptrace was attached to the process. The symbol names in the injected object file were chosen to blend with legitimate liblzma symbols — functions named `_get_cpuid`, `_is_arch_extension_supported`, and similar names that appeared related to the CPU feature detection that CRC IFUNC resolvers legitimately perform.

### 1.6 Systemic lessons and defensive measures

The xz backdoor exposed fundamental weaknesses in the open-source supply chain that extend far beyond a single project. Single-maintainer projects represent single points of failure — the entire Linux SSH infrastructure depended on a compression library maintained by one person experiencing burnout, with no institutional review of new maintainer additions. Autotools build systems are opaque — the injection was hidden in generated build files that few people understand or review, exploiting the gap between reviewed source code and distributed build artifacts. Transitive dependencies create invisible attack surfaces — the sshd → libsystemd → liblzma chain was not obvious to anyone without deep distribution packaging knowledge, and most distributions did not track or audit these transitive dependency relationships. Binary test files in source repositories are trusted but unverifiable — the backdoor payload was hidden in compressed test fixtures that no human reviewer would decompress, reverse-engineer, and analyze during a code review.

Defensive measures adopted post-xz include: increased scrutiny of new maintainers in critical projects (Linux Foundation and OpenSSF published guidance on maintainer onboarding, including identity verification and graduated trust models); build-system simplification (projects are migrating from autotools to CMake or Meson, reducing the complexity that the attacker exploited as camouflage — the xz project itself switched to CMake post-incident); binary file detection in CI (automated alerts for new binary files added to repositories, with mandatory justification and review); reproducible builds (allowing independent verification that the distributed binary matches the source — the Reproducible Builds initiative has gained significantly more traction post-xz); source-tarball-to-git-diff auditing (automated comparison of distribution tarballs against the git source to detect discrepancies like the xz build-to-host.m4 injection); and funding for critical open-source projects (the Alpha-Omega initiative, Sovereign Tech Fund, and Linux Foundation's security grants to reduce single-maintainer burnout that creates exploitable social dynamics).

### 1.7 Detection and forensic triage

The following detection artifacts and triage procedures enable defenders to determine whether a system was exposed to the xz backdoor, whether the backdoor was activated, and what telemetry — or lack thereof — it produces.

**System exposure check commands.** These commands determine if the vulnerable xz/liblzma versions are installed and whether sshd loads liblzma through the transitive dependency chain.

```bash
# Check installed xz version — vulnerable versions are 5.6.0 and 5.6.1
xz --version

# Check if sshd links against liblzma (the backdoor dependency chain)
ldd $(which sshd) | grep lzma

# Debian/Ubuntu: check installed xz-utils package version
dpkg -l | grep -E 'xz-utils|liblzma'

# RHEL/Fedora: check installed xz package version
rpm -qa | grep -E '^xz-|^liblzma'

# Verify liblzma.so SHA-256 against known-bad hashes
sha256sum /usr/lib/x86_64-linux-gnu/liblzma.so.5.6.1 2>/dev/null
# Known-bad (Debian sid 5.6.1-1): 319e0a07a03f3bda21a650cb2d1c8b46e1af0e3f...

# Check if sshd is running with liblzma mapped into its address space
for pid in $(pgrep sshd); do
  grep -l liblzma /proc/$pid/maps 2>/dev/null && echo "PID $pid: liblzma LOADED"
done
```

**Forensic triage for backdoor activation.** If the vulnerable version was installed, these commands assess whether the IFUNC resolver executed its hooking logic.

```bash
# Check /proc/PID/maps for liblzma loaded in sshd context
# The backdoor's IFUNC resolver only activates when loaded by sshd
cat /proc/$(pgrep -o sshd)/maps | grep liblzma

# Strace sshd to observe IFUNC resolution behavior
# The backdoor's resolver reads /proc/self/exe and /proc/self/maps
# Normal crc32/crc64 IFUNC resolvers do NOT read /proc
strace -f -e trace=openat,read -p $(pgrep -o sshd) 2>&1 | grep -E 'proc/self/(exe|maps)'

# Check for anomalous sshd latency during connection setup
# The backdoor adds ~500ms to initial connection due to GOT scanning
# Time the SSH handshake (pre-auth phase)
time ssh -o BatchMode=yes -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
  user@target 2>&1 | head -1

# Search for the Ed448 public key bytes in liblzma.so
# The attacker's hardcoded verification key (from public analysis by Binarly)
strings /usr/lib/x86_64-linux-gnu/liblzma.so.5 | grep -c 'RSA_public_decrypt'
objdump -d /usr/lib/x86_64-linux-gnu/liblzma.so.5 | grep -A5 'crc64_resolve'
```

**YARA rule for detecting xz backdoor artifacts in liblzma.so.** This rule matches the IFUNC resolver signature bytes and the Ed448 public key pattern embedded in the backdoored binary. The hex patterns are derived from public analysis by Binarly, Kaspersky GReAT, and the oss-security mailing list disclosure.

```yara
rule CVE_2024_3094_XZ_Backdoor_liblzma {
    meta:
        description = "Detects xz/liblzma backdoor (CVE-2024-3094) in compiled .so"
        author = "Derived from Binarly and community analysis"
        date = "2024-03-30"
        reference = "https://www.openwall.com/lists/oss-security/2024/03/29/4"
        severity = "critical"
        cvss = "10.0"
        cve = "CVE-2024-3094"

    strings:
        // IFUNC resolver prologue pattern — the backdoor's crc64_resolve
        // contains atypical instructions for GOT scanning not present in
        // legitimate CRC IFUNC resolvers
        $ifunc_resolver = {
            f3 0f 1e fa        // endbr64
            55                  // push rbp
            48 89 e5           // mov rbp, rsp
            48 83 ec ??        // sub rsp, N
            48 8d 3d ?? ?? ?? ?? // lea rdi, [rip+offset] — loads /proc/self path
        }

        // Ed448 public key fragment — the attacker's verification key
        // used to authenticate backdoor trigger packets
        // (first 16 bytes of the embedded Ed448 pubkey from Binarly analysis)
        $ed448_pubkey = {
            0a 31 fd 3b 2f 1f c6 92 92 13 25 05 18 a4 72 63
        }

        // Build-to-host.m4 extraction signature in source tarballs
        $m4_extractor = "eval $(head -c +1024 tests/files"

        // Backdoor's anti-analysis environment checks compiled into the .so
        $env_check_1 = "LANG=C" ascii
        $env_check_2 = "LD_DEBUG" ascii
        $env_check_3 = "LD_PROFILE" ascii
        $env_check_4 = "/proc/self/exe" ascii

        // Known-bad function names injected by the backdoor
        $func_name_1 = "_get_cpuid" ascii
        $func_name_2 = "_is_arch_extension_supported" ascii

    condition:
        uint32(0) == 0x464c457f  // ELF magic
        and (
            ($ifunc_resolver and $ed448_pubkey) or
            ($ifunc_resolver and 3 of ($env_check_*)) or
            ($m4_extractor) or
            ($ed448_pubkey and 2 of ($func_name_*))
        )
}
```

**Sigma rule for detecting anomalous sshd latency and liblzma behavior.** The backdoor's IFUNC resolver introduces measurable latency (~500ms) during sshd startup and reads `/proc/self/maps` and `/proc/self/exe` — behavior not exhibited by legitimate liblzma usage.

```yaml
title: CVE-2024-3094 xz Backdoor IFUNC Resolver Behavior
id: a1b2c3d4-5678-9abc-def0-123456789abc
status: experimental
description: >
  Detects sshd process reading /proc/self/exe and /proc/self/maps during
  library initialization, characteristic of the xz backdoor IFUNC resolver
  performing GOT scanning and process identification.
references:
  - https://www.openwall.com/lists/oss-security/2024/03/29/4
  - https://nvd.nist.gov/vuln/detail/CVE-2024-3094
author: Supply chain defense team
date: 2024-03-30
tags:
  - attack.persistence
  - attack.t1574.006  # Hijack Execution Flow: Dynamic Linker Hijacking
  - cve.2024.3094
logsource:
  category: file_access
  product: linux
  service: auditd
detection:
  selection_process:
    Image|endswith: '/sshd'
  selection_files:
    TargetFilename|contains:
      - '/proc/self/exe'
      - '/proc/self/maps'
  selection_library:
    # sshd loading liblzma is itself suspicious on non-systemd-notify configs
    ImageLoaded|contains: 'liblzma'
  condition: selection_process and (selection_files or selection_library)
falsepositives:
  - sshd compiled with systemd-notify support legitimately loads liblzma,
    but does NOT read /proc/self/exe or /proc/self/maps during init
level: critical
```

**Detection artifacts table.** The xz backdoor was designed for minimal telemetry production. This table documents what the backdoor does and does not produce, guiding defenders on where to look.

| Artifact Category | Backdoor Produces? | Detail | Detection Source |
|---|---|---|---|
| Network connections | No new connections | Backdoor operates within existing SSH session; no separate C2 channel | Network monitoring is blind to activation |
| DNS queries | No | No C2 domain resolution; command payload is embedded in SSH auth data | DNS logs are not useful |
| File system writes | No | Backdoor operates entirely in memory after IFUNC resolver executes | File integrity monitoring (FIM) does not detect |
| Authentication logs | No | Successful backdoor auth bypasses sshd logging entirely; failed non-backdoor auth logs normally | auth.log shows nothing for backdoor sessions |
| Process creation | Possible | Attacker commands execute as children of sshd; unusual child processes from sshd are detectable | Process monitoring (auditd, eBPF) |
| /proc/self reads | Yes (init only) | IFUNC resolver reads /proc/self/exe and /proc/self/maps during library load | auditd file_access or eBPF tracepoints |
| sshd startup latency | Yes (~500ms) | GOT scanning and crypto setup add measurable delay to sshd service start | Process timing analysis, systemd journal |
| liblzma in sshd memory | Yes | /proc/PID/maps shows liblzma mapped into sshd on affected distributions | Memory map inspection |
| Anomalous SSH public key | Yes (trigger only) | Ed448 signature embedded in RSA key modulus is structurally anomalous | SSH auth packet inspection (DPI at network edge) |

---

## 2. SolarWinds SUNBURST build compromise deep dive

### 2.1 SUNSPOT build injector

The SolarWinds build compromise was not a simple modification of source code — it was a sophisticated build-system implant that intercepted the compilation process in real time. CrowdStrike's analysis of the compromised SolarWinds build environment revealed the SUNSPOT implant: a piece of malware running on SolarWinds' build server (a TeamCity-based CI environment) that monitored the MSBuild compilation process continuously via periodic scanning of running `MsBuild.exe` processes.

When SUNSPOT detected that the Orion build was compiling the `SolarWinds.Orion.Core.BusinessLayer` project (by monitoring process command lines for the specific project path), it located the source file `InventoryManager.cs` on disk and swapped it with a backdoored version containing the SUNBURST payload. The backdoored `InventoryManager.cs` was stored encrypted on the build server — SUNSPOT decrypted it in memory and wrote it to the source directory, overwriting the legitimate file. After MSBuild compiled the file and produced the output DLL, SUNSPOT restored the original `InventoryManager.cs` from a backup copy it had made before the swap. The entire substitution occurred within the time window between MSBuild reading the source tree and completing compilation — typically seconds.

This technique meant that: the source code repository (a Perforce server) never contained the backdoored code — code reviews of the repository would never find the backdoor; the backdoored binary was compiled by SolarWinds' legitimate MSBuild instance with the legitimate build configuration — receiving a valid Authenticode code signature from SolarWinds' signing certificate; the build server's file system showed the original, clean source files both before and after the build — making file-integrity-monitoring detection unlikely unless the monitoring captured the brief substitution window with sub-second granularity; and build logs showed a normal compilation with no warnings or errors, because the injected source file was syntactically valid C# that compiled cleanly.

SUNSPOT itself was a separate implant — the attackers had already compromised SolarWinds' internal network (likely through password spraying or a separate supply chain compromise) and had maintained persistent access to the build infrastructure for months before deploying SUNSPOT. The SUNSPOT binary was installed as a scheduled task that started during the build process, and included anti-forensics measures: it logged its own activity to a file (C:\Windows\SysWOW64\netsetupsvc.log) that mimicked Windows networking logs, and would self-terminate if it detected it was running in a debugger or sandbox.

### 2.2 SUNBURST payload and tradecraft

The SUNBURST payload embedded in the compiled Orion DLL was designed for extreme stealth and selective activation. Upon loading, SUNBURST performed several pre-execution checks: it verified that the system's Active Directory domain name was not on a blocklist of security vendor domains, government cybersecurity agencies (including FireEye/Mandiant, CrowdStrike, Microsoft Threat Intelligence Center, CISA, and several antivirus vendors), and known sandbox environments. It also checked the system clock — SUNBURST entered a dormant state for 12 to 14 days after installation, ensuring that the backdoor would not be active during the immediate post-update monitoring period when customers might be watching for anomalous behavior. During the dormancy period, the DLL loaded and executed normally, performing its legitimate Orion monitoring functions — only the backdoor component was dormant.

After the dormancy period, SUNBURST used DNS as its initial C2 channel. The backdoor encoded reconnaissance data — Active Directory domain name, username of the account running the Orion service, installed security products, network adapter configurations — into DNS A-record and CNAME queries to subdomains of `avsvmcloud[.]com`. The subdomain encoding used a custom DGA (Domain Generation Algorithm) that hashed the victim's Active Directory domain name into the subdomain using a combination of XOR encoding and base32-like character substitution. This encoding allowed the attacker to identify and prioritize high-value targets from the DNS query data alone — by decoding the subdomain, the attacker could determine the victim's organization name without initiating any interactive C2 connection. The DNS queries were spaced at random intervals between 1 and 3 hours, blending with normal DNS traffic patterns and staying well below any rate-based anomaly detection thresholds.

The DGA also served as a kill switch: if the victim's environment matched the "avoid" list (security vendors, government cybersecurity agencies, sandboxes, and analysis environments), SUNBURST entered a permanent dormant state and never initiated C2. This selective activation served two purposes — it reduced the total number of detected infections (extending the campaign's operational lifespan) and avoided alerting the organizations most capable of analyzing and attributing the attack.

For high-value targets (identified by domain name in the DNS queries — approximately 100 organizations out of the roughly 18,000 that installed the backdoored update), the attacker transitioned from the DNS C2 channel to an HTTP-based C2 channel. The transition was triggered by a DNS CNAME response that redirected subsequent HTTP beacons to an attacker-controlled domain. The HTTP C2 used steganography — commands and responses were encoded within XML and JSON payloads designed to resemble legitimate Orion telemetry data and API responses, including correct HTTP headers, Content-Type specifications, and URL structures that mimicked Orion's SWIperfmonDB API. Network-level content inspection (DPI) would see what appeared to be normal SolarWinds Orion traffic to a CDN or update server.

**Detection indicators.** Network-level detection of SUNBURST was extremely difficult during the campaign because the DNS and HTTP C2 channels were designed to mimic legitimate Orion telemetry. Post-incident detection relied on: DNS query logs showing queries to `*.avsvmcloud[.]com` subdomains from Orion servers (the domain was sinkholed by Microsoft and FireEye after discovery, enabling retrospective detection); network flow analysis showing unexpected HTTPS connections from Orion servers to non-SolarWinds IP ranges (the HTTP C2 endpoints used commercial cloud hosting — AWS, Azure — and CDN infrastructure); endpoint indicators including the presence of the trojanized `SolarWinds.Orion.Core.BusinessLayer.dll` with specific file hashes published in CISA's Emergency Directive 21-01; and memory forensics revealing the SUNBURST code paths (including the dormancy timer, the blocklist check, and the DGA computation) in the running Orion process. FireEye (now Mandiant) released SUNBURST countermeasures including YARA rules, Snort signatures, and IOC lists within days of their public disclosure.

Post-compromise tradecraft demonstrated APT29 (Cozy Bear) level sophistication. From the Orion server — which had broad network access because its monitoring function required connectivity to managed endpoints across network segments — the attackers performed: LDAP reconnaissance to map the Active Directory structure, DCSync attacks (replicating AD credentials from domain controllers), AD FS signing key theft (exfiltrating the token-signing certificate from the AD FS configuration database), and Golden SAML attacks (forging SAML authentication tokens using the stolen AD FS signing key to access victims' Microsoft 365 and Azure AD environments). The Golden SAML technique (Domain 14A §3) was particularly devastating because the forged SAML tokens bypassed MFA — the token represented an already-completed authentication, so the cloud provider accepted it without additional verification. The attackers used these forged tokens to access victims' email, SharePoint, OneDrive, and Azure resources, establishing separate persistence mechanisms (OAuth application registrations, service principal credentials) in the cloud environment that survived even if the on-premises compromise was discovered and remediated.

### 2.3 3CX cascading supply chain compromise

The 3CX incident (March 2023) demonstrated a particularly alarming supply chain pattern: cascading compromise, where a supply chain attack on one vendor was used to attack a second vendor, which in turn compromised the second vendor's customers. The Mandiant investigation attributed the attack to UNC4736 (linked to North Korea's Lazarus Group / DPRK Bureau 121).

The attack chain began with X_TRADER, a financial trading software platform by Trading Technologies. The X_TRADER installer available on Trading Technologies' website had been trojanized — it installed legitimate trading software alongside a modular backdoor called VEILEDSIGNAL. An employee at 3CX downloaded and installed the trojanized X_TRADER application on their personal machine. The VEILEDSIGNAL backdoor on the employee's machine allowed the attackers to steal credentials, which they used to access 3CX's internal network and eventually its build environment.

Once inside 3CX's build infrastructure, the attackers modified the build process to inject a malicious DLL (ffmpeg.dll) into the 3CX Desktop App. The trojanized 3CX app was signed with 3CX's legitimate code-signing certificate and distributed through the normal auto-update mechanism to approximately 600,000 customer organizations. On customer systems, the backdoored 3CX app downloaded a second-stage payload from GitHub repositories (appearing as innocuous icon files) that loaded a C2 backdoor capable of browser data theft, credential harvesting, and interactive shell access.

The cascading nature — Trading Technologies → employee machine → 3CX build environment → 3CX customers — illustrates the multiplicative risk of supply chain attacks. Each hop amplifies the attacker's reach while increasing the forensic complexity of attribution and response. Detection required correlating artifacts across three separate organizations' environments.

The 3CX incident had particularly concerning detection dynamics. CrowdStrike's Falcon EDR flagged the trojanized 3CX app as malicious on multiple customer endpoints — but many customers initially dismissed the alerts as false positives because the application was signed with a valid 3CX certificate and was a legitimate business tool. This illustrates the trust paradox of code signing: signing creates trust, and that trust becomes a liability when the signing entity is compromised. CrowdStrike's detection was based on behavioral analysis (the 3CX app exhibiting shellcode execution patterns, loading DLLs from unusual directories, and making HTTP requests to GitHub raw content URLs — behaviors inconsistent with a VoIP application) rather than signature-based detection.

The X_TRADER vector also highlights the risk of "shadow IT" — software installed on employee machines outside IT management's visibility. The 3CX employee who installed X_TRADER did so for personal trading activity, not for company business. Organizations with strict software whitelisting (application control policies like Windows AppLocker or macOS Santa) on developer workstations would have prevented the initial compromise vector. The incident prompted broader adoption of zero-trust endpoint security models where developer machines are not trusted to have clean environments — builds run in isolated CI infrastructure, not on developer laptops.

### 2.4 Detection rules and forensic indicators

**YARA rule for SUNBURST DLL detection.** This rule targets the trojanized `SolarWinds.Orion.Core.BusinessLayer.dll` using known hashes from CISA Emergency Directive 21-01, DGA code patterns, and characteristic strings.

```yara
rule SUNBURST_SolarWinds_Backdoor {
    meta:
        description = "Detects SUNBURST backdoor in SolarWinds Orion DLL"
        author = "Derived from FireEye/Mandiant and CISA ED 21-01"
        date = "2020-12-13"
        reference = "https://www.cisa.gov/emergency-directive-21-01"
        severity = "critical"
        cve = "CVE-2020-10148"

    strings:
        // SUNBURST DGA domain — primary C2 pivot
        $dga_domain = "avsvmcloud.com" ascii wide

        // Characteristic class and method names in the .NET DLL
        $class_1 = "OrionImprovementBusinessLayer" ascii wide
        $class_2 = "SolarWinds.Orion.Core.BusinessLayer" ascii wide

        // DGA hash computation — the CRC32-based domain hashing
        // used to identify victim organizations from DNS queries
        $dga_code_1 = "GetOrCreateUserID" ascii wide
        $dga_code_2 = "GetCurrentString" ascii wide
        $dga_code_3 = "CryptoHelper" ascii wide

        // Security product blocklist — SUNBURST checked for and avoided
        // environments running these tools
        $blocklist_1 = "apimonitor" ascii wide nocase
        $blocklist_2 = "fiddler" ascii wide nocase
        $blocklist_3 = "wireshark" ascii wide nocase

        // Anti-sandbox: dormancy timer (12-14 day wait)
        $dormancy = "ReportWatcherRetry" ascii wide

        // HTTP C2 steganographic patterns
        $http_c2_1 = "SWIperfmonDB" ascii wide
        $http_c2_2 = "application/octet-stream" ascii wide

    condition:
        uint16(0) == 0x5A4D  // PE/MZ header
        and (
            ($dga_domain and $class_1) or
            ($class_2 and 2 of ($dga_code_*)) or
            ($dormancy and $dga_domain and 2 of ($blocklist_*)) or
            (4 of them)
        )
}
```

**Suricata rule for SUNBURST DNS C2 traffic.** The DGA subdomains to `avsvmcloud.com` have a characteristic length and character set (base32-like encoding of victim AD domain hashes).

```
# SUNBURST DNS C2 — DGA subdomain queries to avsvmcloud.com
# The DGA produces subdomains of 20-35 lowercase alphanumeric characters
alert dns $HOME_NET any -> any 53 (
    msg:"SUNBURST DNS C2 DGA query to avsvmcloud.com";
    dns.query;
    content:"avsvmcloud.com"; nocase; endswith;
    pcre:"/^[a-z0-9]{20,35}\.avsvmcloud\.com$/i";
    classtype:trojan-activity;
    sid:2024001; rev:1;
    metadata: cve CVE-2020-10148, severity critical;
    reference:url,www.cisa.gov/emergency-directive-21-01;
)

```

**Sigma rule for Golden SAML detection.** Post-SUNBURST, attackers used stolen AD FS signing keys to forge SAML tokens. This rule detects anomalous SAML token usage and AD FS signing key access indicative of Golden SAML attacks.

```yaml
title: Golden SAML - AD FS Token Signing Key Access
id: b2c3d4e5-6789-abcd-ef01-23456789abcd
status: stable
description: >
  Detects access to the AD FS token-signing certificate private key,
  which is required for Golden SAML attacks. Post-SUNBURST tradecraft
  used stolen AD FS signing keys to forge SAML assertions and access
  Microsoft 365 and Azure AD resources without MFA.
references:
  - https://www.mandiant.com/resources/blog/evasive-attacker-leverages-solarwinds-supply-chain-compromises-with-sunburst-backdoor
  - https://attack.mitre.org/techniques/T1606/002/
author: Supply chain defense team
date: 2021-01-15
tags:
  - attack.credential_access
  - attack.t1606.002  # Forge Web Credentials: SAML Tokens
  - attack.t1552.004  # Unsecured Credentials: Private Keys
logsource:
  product: windows
  service: security
detection:
  selection_adfs_key_access:
    EventID: 4662  # An operation was performed on an object
    ObjectType|contains: 'certificationAuthority'
    Properties|contains:
      - 'Token-Signing'
      - 'Token-Decrypting'
  selection_adfs_export:
    EventID: 4663  # An attempt was made to access an object
    ObjectName|contains:
      - 'ADFS'
      - 'Microsoft.IdentityServer'
    AccessMask:
      - '0x1'   # READ_CONTROL
      - '0x20'  # READ
  selection_dcsync:
    EventID: 4662
    Properties|contains: 'Replicating Directory Changes All'
    AccessMask: '0x100'
  condition: selection_adfs_key_access or selection_adfs_export or selection_dcsync
falsepositives:
  - Legitimate AD FS certificate rotation by authorized administrators
  - AD FS health monitoring tools that read certificate metadata
level: high
```

**PowerShell commands for SolarWinds Orion forensic triage.**

```powershell
# Check installed SolarWinds Orion version
Get-ItemProperty "HKLM:\SOFTWARE\WOW6432Node\SolarWinds\Orion\Core" -Name Version -ErrorAction SilentlyContinue

# Verify integrity of the Orion BusinessLayer DLL against known-bad hashes
# Hashes from CISA ED 21-01 and FireEye countermeasures
$knownBadHashes = @(
    "32519b85c0b422e4656de6e6c41878e95fd95026267daab4215ee59c107d6c77",  # 2019.4 HF5
    "dab758bf98d9b36fa057a66cd0284737abf89857b73ca89280267ee7caf62f3b",  # 2020.2 RC1
    "eb6fab5a2964c5817fb239a7a5079cabca0a00464fb3e07155f28b0a57a2c0ed",  # 2020.2 RC2
    "c15abaf51e78ca56c0376522d699c978217bf041a3bd3c71d09193efa5717c71"   # 2020.2
)
$dllPath = "${env:ProgramFiles(x86)}\SolarWinds\Orion\SolarWinds.Orion.Core.BusinessLayer.dll"
if (Test-Path $dllPath) {
    $hash = (Get-FileHash $dllPath -Algorithm SHA256).Hash.ToLower()
    if ($knownBadHashes -contains $hash) {
        Write-Warning "CRITICAL: Known-bad SUNBURST DLL detected! Hash: $hash"
    } else {
        Write-Output "DLL hash not in known-bad list: $hash (verify against latest IOCs)"
    }
} else {
    Write-Output "SolarWinds Orion BusinessLayer DLL not found at expected path."
}

# Check for SUNSPOT injector artifacts on build servers
# SUNSPOT logged to this file, mimicking Windows networking logs
Test-Path "C:\Windows\SysWOW64\netsetupsvc.log"

# Check for SUNSPOT scheduled task persistence
Get-ScheduledTask | Where-Object { $_.TaskPath -match "SolarWinds|taskhostw" } |
    Select-Object TaskName, TaskPath, State, Actions

# Check DNS logs for avsvmcloud.com DGA queries (requires DNS logging)
Get-DnsServerQueryLog | Where-Object { $_.Query -like "*avsvmcloud.com" }
```

**3CX detection artifacts.** YARA rule for the trojanized `ffmpeg.dll` distributed via the 3CX Desktop App supply chain compromise.

```yara
rule Supply_Chain_3CX_Trojanized_FFmpeg {
    meta:
        description = "Detects trojanized ffmpeg.dll from 3CX supply chain attack"
        author = "Derived from CrowdStrike and Mandiant analysis"
        date = "2023-03-29"
        reference = "https://www.mandiant.com/resources/blog/3cx-software-supply-chain-compromise"
        severity = "critical"

    strings:
        // 3CX-specific strings in the trojanized DLL
        $s1 = "3CXDesktopApp" ascii wide
        // Icon file URLs on GitHub used as second-stage payload markers
        $s2 = "raw.githubusercontent.com" ascii wide
        $s3 = "icon" ascii wide
        // Encrypted payload markers in the modified ffmpeg DLL
        $hex_marker = { fe ed fa ce ?? ?? ?? ?? 00 00 00 }
        // DLL side-loading indicator
        $sideload = "ffmpeg.dll" ascii wide

    condition:
        uint16(0) == 0x5A4D
        and ($s1 and $s2 and $s3)
        or ($hex_marker and $sideload)
}
```

**Sigma rule for 3CX Desktop App behavioral indicators.** CrowdStrike's initial detection was behavioral — the 3CX app exhibited shellcode execution and anomalous network activity inconsistent with a VoIP application.

```yaml
title: 3CX Desktop App Supply Chain - Behavioral Indicators
id: c3d4e5f6-789a-bcde-f012-3456789abcde
status: stable
description: >
  Detects behavioral indicators of the trojanized 3CX Desktop App,
  including shellcode execution from the app process, DLL loading from
  unusual directories, and HTTP requests to GitHub raw content URLs.
references:
  - https://www.crowdstrike.com/blog/crowdstrike-detects-and-prevents-active-intrusion-campaign-targeting-3cxdesktopapp-customers/
author: Supply chain defense team
date: 2023-03-29
tags:
  - attack.execution
  - attack.t1195.002  # Supply Chain Compromise: Compromise Software Supply Chain
  - attack.defense_evasion
logsource:
  category: process_creation
  product: windows
detection:
  selection_parent:
    ParentImage|endswith:
      - '\3CXDesktopApp.exe'
      - '\3cxdesktopapp.exe'
  selection_suspicious_child:
    Image|endswith:
      - '\cmd.exe'
      - '\powershell.exe'
      - '\rundll32.exe'
      - '\regsvr32.exe'
      - '\mshta.exe'
  selection_network:
    Image|endswith: '\3CXDesktopApp.exe'
    DestinationHostname|contains:
      - 'raw.githubusercontent.com'
      - 'msstorageazure.com'
      - 'officestoragebox.com'
      - 'visualstudiofactory.com'
      - 'azuredeploystore.com'
      - 'msloginservices.com'
  condition: (selection_parent and selection_suspicious_child) or selection_network
falsepositives:
  - Legitimate 3CX Desktop App updates (verify against known-clean versions)
level: critical
```

### 2.5 Build system defense lessons

The SolarWinds and 3CX incidents drove fundamental defensive advances in build security.

**Hermetic builds** isolate the build process from all external resources: no internet access during compilation, no access to local files outside the declared build inputs, no mutable system state. Hermetic builds prevent SUNSPOT-style substitution because the build process cannot reach external code or tools that were not explicitly declared as inputs, and the declared inputs are locked to specific, hash-verified versions. If SUNSPOT attempted to inject a modified source file, the hermetic build would either reject it (because it was not among the declared inputs) or produce a different output hash (detectable by reproducibility checks). **Bazel** (Google), **Buck2** (Meta), and **Nix** are build systems that support hermetic builds natively. Bazel's sandboxed execution mode runs each build action in a filesystem sandbox (using Linux namespaces or macOS sandbox-exec) where only declared inputs are visible, preventing side-channel injection.

**Dual-party signing** separates the build and signing processes into distinct trust domains. The build system produces an unsigned artifact with a hash. A separate, isolated signing service (backed by an HSM — Domain 17D §3 for HSM security) receives the artifact hash, verifies the build's provenance (checking that the artifact was produced by an authorized build pipeline from a reviewed source commit), and only then produces a code signature. This prevents a compromised build server from silently signing a backdoored artifact — the signing service independently verifies the build provenance before signing. The signing service's HSM ensures that the signing key never exists in extractable form on any system that an attacker could compromise.

**Reproducible builds** guarantee that independent parties building from the same source with the same build configuration produce bit-for-bit identical binaries. Reproducibility enables third-party verification: anyone can rebuild the software and compare the result hash with the distributed binary. Discrepancies indicate either a build system issue (non-determinism, timestamps embedded in binaries, path-dependent compilation) or a supply chain compromise. Achieving reproducibility requires eliminating sources of non-determinism: build timestamps (use `SOURCE_DATE_EPOCH`), file ordering in archives (use sorted directory traversal), path embedding (use `--remap-path-prefix` in Rust, `-fmacro-prefix-map` in GCC), and randomized compiler internals (seed ASLR, hash randomization with fixed seeds during build). The Reproducible Builds project (reproducible-builds.org) tracks reproducibility status across major distributions: as of 2024, over 95% of Debian packages are reproducible.

---

## 3. CI/CD pipeline security

### 3.1 GitHub Actions hardening

GitHub Actions is the most widely used CI/CD platform in open-source and many enterprises. The attack surface is broad: compromised third-party actions (Actions published by untrusted authors can execute arbitrary code in the workflow with access to repository secrets), secret exposure (workflow secrets are available as environment variables to all steps in a job unless scoped with environments), self-hosted runner compromise (persistent runners maintain state — filesystem, installed packages, environment variables — between jobs, enabling cross-job attacks), workflow injection (pull request triggers execute attacker-controlled code with potential access to the repository's secrets), and artifact poisoning (malicious outputs from one job passed as inputs to downstream jobs).

**Pinned actions.** Third-party actions should be pinned to a specific commit hash, not a mutable tag. A tag (`actions/checkout@v4`) can be moved to point to a different commit — if the action's repository is compromised or the maintainer's credentials are stolen, the attacker can retag `v4` to a malicious commit. All workflows using `@v4` would then execute the attacker's code on their next run. A commit hash pin (`actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11`) is immutable — the pinned commit cannot be changed. Tools like `pin-github-action` (sethvargo) and `gha-pin` automate the process of converting tag-based references to hash-based pins while preserving a comment noting the original tag version.

**OIDC tokens for cloud authentication.** GitHub Actions supports OIDC (OpenID Connect) token generation — the workflow receives a short-lived, signed JWT containing claims about the workflow execution context: repository (`repo:org/name`), branch (`ref:refs/heads/main`), job name, actor (the user or automation that triggered the workflow), runner environment, and workflow reference. Cloud providers (AWS via IRSA/Web Identity, GCP via Workload Identity Federation, Azure via Federated Credentials) accept this token for authentication, eliminating the need to store long-lived cloud credentials (AWS access keys, GCP service account keys) as repository secrets. The OIDC token is cryptographically bound to the specific workflow run and expires within minutes, preventing token theft and replay. The cloud provider's trust policy should be configured narrowly: trusting only specific repositories and branches (e.g., only `repo:myorg/myapp AND ref:refs/heads/main` can assume the production deployment role).

**Pull request security model.** Workflows triggered by `pull_request` events from forks run with read-only access to the repository and no access to repository secrets — this is a critical security boundary because fork PRs contain attacker-controlled code. The `pull_request_target` event is different: it runs in the context of the base repository (not the fork) with access to repository secrets. Using `pull_request_target` with `actions/checkout` pointing to the PR head ref is extremely dangerous — it executes the attacker's code with the base repository's secrets. If `pull_request_target` is necessary (e.g., for labeling PRs or posting comments), the workflow should never check out or execute code from the PR; it should only read PR metadata via the GitHub API.

**Self-hosted runner isolation.** Persistent self-hosted runners are dangerous: a malicious job can install rootkits, modify the `$PATH` to inject trojan versions of common tools (gcc, npm, docker), steal cached credentials (Docker config, npm tokens, SSH keys), or exfiltrate secrets that future jobs will use. Mitigation requires ephemeral runners: each job gets a fresh runner instance that is destroyed after job completion. GitHub's ARC (Actions Runner Controller) for Kubernetes supports ephemeral runners via the `ephemeral: true` configuration. For self-managed runners, tools like Philips's terraform-aws-github-runner create auto-scaling EC2 instances that terminate after each job. GitHub's own larger runners (GitHub-hosted, ephemeral by default) are the simplest secure option for most workloads.

### 3.2 GitLab CI and Jenkins security

**GitLab CI** introduces similar attack surfaces with some platform-specific considerations. GitLab's pipeline security model distinguishes between protected and unprotected branches — CI/CD variables marked as "protected" are only available to pipelines running on protected branches, providing a coarse access-control mechanism for production secrets. GitLab's `rules:if` syntax controls when jobs run, but misconfigured rules can expose protected variables to merge request pipelines from forks. The `CI_JOB_TOKEN` (a per-job GitLab API token) has been progressively scoped down — it should be limited to the minimum necessary permissions using the project's CI/CD token access settings. GitLab's `include:remote` directive (importing pipeline configuration from external URLs) is an injection vector if the URL is not controlled by the organization — the external configuration can define arbitrary jobs with access to the pipeline's secrets.

**Jenkins** security is dominated by its plugin ecosystem. Jenkins instances in enterprise environments commonly have 50-200 plugins installed, each representing a potential vulnerability. Critical Jenkins hardening: the Jenkins controller should never execute build steps directly (use agents/nodes exclusively); the Script Security plugin must be configured to sandbox Groovy scripts; credentials should be stored in the Jenkins Credentials plugin (not hardcoded in pipeline scripts or environment variables); the Role-Based Access Control plugin should enforce the principle of least privilege (not granting all authenticated users the "Job/Build" permission); and Jenkins should be placed behind a reverse proxy with authentication, never exposed directly to the internet. Jenkins' Pipeline Shared Libraries — Groovy libraries loaded by pipelines — represent a high-value target: compromising a shared library compromises every pipeline that uses it. Shared libraries should be in dedicated repositories with branch protection, required reviews, and commit signing.

### 3.3 Build provenance and SLSA

**SLSA (Supply-chain Levels for Software Artifacts)** defines four levels of build integrity, each building on the previous.

**SLSA Level 1 (Provenance exists).** The build process generates a provenance document — an in-toto attestation or SLSA provenance predicate — describing how the artifact was built: source repository URL, commit hash, build command/entrypoint, builder identity (which CI system produced it), and build timestamp. The provenance document exists but may not be tamper-resistant — it is self-reported by the build process and could be forged by a compromised builder. Level 1 provides a starting point for auditing but no cryptographic guarantees.

**SLSA Level 2 (Hosted build, signed provenance).** The build runs on a hosted build service (not a developer's laptop). The provenance document is signed by the build service, providing a cryptographic assertion that the stated build service actually produced the artifact. This prevents a developer from claiming they built something on CI when they actually built it locally (where they could have tampered with the build). The signing key is controlled by the build service, not by the build configuration.

**SLSA Level 3 (Hardened build, non-falsifiable provenance).** The build service provides hardened isolation: each build runs in a fresh, ephemeral environment (containers or VMs that are destroyed after use); the build environment has no network access during compilation (hermetic builds); the provenance is generated by the build service infrastructure (not by the build script — preventing the build from forging its own provenance, which is a critical distinction from Level 2); and the build process has no access to signing keys, deployment credentials, or the provenance-signing mechanism. The provenance at Level 3 is non-falsifiable: even if the build script is compromised, it cannot modify the provenance because the provenance generation is outside the build script's trust boundary.

**SLSA Level 4 (Two-person review, reproducible).** All source code changes require two independent reviews before merging. Builds are reproducible: independent rebuilding from the same source and configuration produces bit-for-bit identical output. This is the highest level, requiring both process rigor (mandatory code review) and technical infrastructure (reproducible builds, independent verification). Few projects achieve Level 4 as of 2025, though critical infrastructure projects (Tor Browser, Bitcoin Core) have adopted reproducible builds.

**Implementation with GitHub Actions.** The `slsa-github-generator` project (maintained by the SLSA working group) provides reusable GitHub Actions workflows that generate SLSA Level 3 provenance. The architecture is critical: the provenance generation runs in a separate, isolated reusable workflow (not the consumer's workflow), uses GitHub's OIDC token to authenticate the build's identity, signs the provenance using Sigstore (Fulcio certificate + Rekor transparency log entry), and outputs the provenance attestation alongside the build artifact. The consumer workflow cannot influence the provenance content because the reusable workflow runs in a separate job with its own isolated runner.

### 3.4 Tekton Chains and in-cluster provenance

Tekton Chains is a Kubernetes-native supply chain security component that automatically generates, signs, and stores provenance for Tekton pipeline runs. After a Tekton TaskRun completes, Chains observes the task's inputs (source code reference, base image digest, parameter values) and outputs (built container image digest, artifact hashes), generates an in-toto attestation (a signed statement describing the relationship between inputs and outputs), signs the attestation using a configured signing backend (cosign/Sigstore, KMS providers including AWS KMS/GCP KMS/Azure Key Vault/HashiCorp Vault, or a local key pair), and stores the attestation (in an OCI registry as a cosign attachment, in a Rekor transparency log, or in a configurable storage backend like S3 or GCS).

Tekton Chains provides SLSA Level 2-3 provenance for Kubernetes-based CI/CD pipelines. The attestation is cryptographically bound to the specific container image digest (SHA-256 hash) — any modification to the image (even a single byte) produces a different digest, invalidating the attestation. Policy engines like Kyverno or OPA Gatekeeper can enforce attestation verification at deployment time, rejecting container images that lack valid Tekton Chains attestations.

The Tekton Chains architecture is designed for separation of concerns: the pipeline author defines what to build (Tekton Tasks and Pipelines), the platform team configures Chains to observe, attest, and sign (through Kubernetes CRDs — `TektonConfig` and `TektonChain`), and the deployment team configures admission policies that verify the attestations. This separation means that a compromised pipeline cannot forge attestations — Chains operates as a separate controller that observes pipeline execution outcomes (container image digests, artifact hashes) independently of the pipeline itself. The attestation predicate follows the SLSA provenance schema, recording: the build configuration (which Tekton Task was executed, with what parameters), the source materials (git commit hash, repository URL), the builder identity (the Tekton installation's identity, verified through the signing key), and the build outputs (image digests, file hashes). For organizations running multiple Kubernetes clusters, Tekton Chains attestations provide a uniform provenance format across clusters, enabling centralized policy enforcement and audit.

### 3.5 Reproducible builds in practice

Achieving reproducible builds in real-world projects requires addressing multiple sources of non-determinism that standard build tools introduce by default. The Reproducible Builds project (reproducible-builds.org) maintains a comprehensive list of common issues and fixes.

**Timestamps** are the most common source of non-reproducibility. The `__DATE__` and `__TIME__` macros in C/C++ embed the compilation timestamp in every object file. The fix is the `SOURCE_DATE_EPOCH` environment variable (standardized by the Reproducible Builds project): when set, build tools (GCC, Clang, Go, Rust, Python, Java, and most major build systems) use this timestamp instead of the current time. CI pipelines should set `SOURCE_DATE_EPOCH` to the timestamp of the most recent git commit (`git log -1 --format=%ct`). PE/COFF executables (Windows) contain a `TimeDateStamp` field in the COFF header — MSVC's `/Brepro` flag zeroes this field. Java `.class` files embed compilation timestamps — `javac`'s `-source` and `-target` flags don't help, but tools like `strip-nondeterminism` post-process class files to remove timestamps. ZIP archives (including JAR files) contain per-file timestamps — `strip-nondeterminism` normalizes these.

**Path embedding** occurs when compilers embed absolute paths in debug information (`DWARF` sections in ELF, PDB files on Windows) and in `__FILE__` macros. GCC and Clang support `-fdebug-prefix-map=/build/dir=.` (rewriting absolute paths to relative paths in debug info) and `-fmacro-prefix-map=/build/dir=.` (rewriting `__FILE__` macro expansions). Rust uses `--remap-path-prefix`. Go embeds module paths from `GOPATH` — setting `GOFLAGS=-trimpath` removes local path prefixes.

**Archive non-determinism** affects tar.gz, ZIP, and ar (static library) archives. File ordering within archives depends on the filesystem's directory traversal order, which varies between filesystems (ext4 vs. XFS vs. tmpfs) and even between runs on the same filesystem (due to inode allocation patterns). Fixes: `tar --sort=name` for sorted tar archives; `ar` with the `D` flag for deterministic static libraries; `find | sort` before archiving. ZIP files additionally contain file modification timestamps — `strip-nondeterminism` normalizes these.

### 3.6 Hardened pipeline examples

**GitHub Actions — fully hardened workflow.** This workflow demonstrates all recommended hardening practices: pinned actions by commit SHA, OIDC-based cloud authentication, minimal permissions, environment protection rules, and SLSA provenance generation.

```yaml
name: Release Build (Hardened)
on:
  push:
    tags: ['v*']

permissions:
  contents: read          # Minimal default — never use 'write-all'
  id-token: write         # Required for OIDC token generation
  packages: write         # Required for GHCR push
  attestations: write     # Required for SLSA provenance

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build:
    runs-on: ubuntu-24.04  # Pin runner image, not just 'ubuntu-latest'
    environment: production # Requires environment protection rules (reviewers, wait timer)
    timeout-minutes: 30     # Prevent runaway builds

    steps:
      # Pin all actions to full commit SHA — never mutable tags
      - name: Checkout
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          persist-credentials: false  # Don't leak GITHUB_TOKEN to subsequent steps

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@b5ca514318bd6ebac0fb2aedd5d36ec1b5c232a2 # v3.10.0

      # OIDC-based login — no stored credentials
      - name: Login to GHCR (OIDC)
        uses: docker/login-action@74a5d142397b4f367a81961eba4e8cd7edddf772 # v3.4.0
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@902fa8ec7d6ecbf8d84d538b9b233a880e428804 # v5.7.0
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}

      - name: Build and push
        id: build
        uses: docker/build-push-action@263435318d21b8e681c14492fe198e19c3bc4c4f # v6.18.0
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          provenance: true   # BuildKit SLSA provenance
          sbom: true          # Inline SBOM generation
          cache-from: type=gha
          cache-to: type=gha,mode=max

      # Sign the image with cosign keyless (Sigstore OIDC)
      - name: Sign container image
        uses: sigstore/cosign-installer@3454372f970814c7b269e46595346e3e0f59eff2 # v3.8.0
      - run: cosign sign --yes ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }}

      # Verify SLSA provenance
      - name: Install slsa-verifier
        uses: slsa-framework/slsa-verifier/actions/installer@v2.7.0
      - name: Verify provenance
        run: |
          slsa-verifier verify-image \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ steps.build.outputs.digest }} \
            --source-uri github.com/${{ github.repository }} \
            --source-tag ${{ github.ref_name }}
```

**GitLab CI — hardened pipeline.** Protected variables, restricted job rules, and artifact signing.

```yaml
# .gitlab-ci.yml
variables:
  # Never expose secrets as global variables — use protected/masked variables
  DOCKER_TLS_CERTDIR: "/certs"

stages:
  - test
  - build
  - sign
  - deploy

default:
  image: docker:27
  tags:
    - ephemeral  # Use ephemeral runners only, never persistent shared runners
  retry:
    max: 1
    when: runner_system_failure

test:
  stage: test
  image: node:22-slim
  script:
    - npm ci --ignore-scripts  # Skip postinstall scripts during CI
    - npm audit --audit-level=critical
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_TAG

build:
  stage: build
  services:
    - docker:27-dind
  variables:
    # Protected variables — only available on protected branches/tags
    REGISTRY_USER: $CI_REGISTRY_USER
    REGISTRY_PASSWORD: $CI_REGISTRY_PASSWORD
  before_script:
    - echo "$CI_REGISTRY_PASSWORD" | docker login -u "$CI_REGISTRY_USER" --password-stdin $CI_REGISTRY
  script:
    - |
      docker build \
        --label "org.opencontainers.image.source=$CI_PROJECT_URL" \
        --label "org.opencontainers.image.revision=$CI_COMMIT_SHA" \
        --no-cache \
        -t "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG" .
    - docker push "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
  rules:
    - if: $CI_COMMIT_TAG && $CI_COMMIT_REF_PROTECTED == "true"
  artifacts:
    reports:
      dotenv: build.env

sign:
  stage: sign
  image: bitnami/cosign:latest
  needs: [build]
  script:
    - cosign sign --yes "$CI_REGISTRY_IMAGE:$CI_COMMIT_TAG"
  rules:
    - if: $CI_COMMIT_TAG && $CI_COMMIT_REF_PROTECTED == "true"
```

**Jenkins Pipeline — credential scoping and agent isolation.**

```groovy
// Jenkinsfile (Declarative Pipeline)
pipeline {
    // Never run builds on the controller — isolated ephemeral agents only
    agent {
        kubernetes {
            yaml '''
              apiVersion: v1
              kind: Pod
              spec:
                containers:
                - name: builder
                  image: docker:27-dind
                  securityContext: { privileged: false, runAsNonRoot: true }
            '''
            defaultContainer 'builder'
        }
    }
    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }
    environment {
        // Credentials scoped to pipeline — never global Jenkins credentials
        REGISTRY_CREDS = credentials('container-registry-token')
    }
    stages {
        stage('Audit') {
            steps {
                sh 'npm ci --ignore-scripts'
                sh 'npm audit --audit-level=critical'
            }
        }
        stage('Build') {
            steps {
                sh '''
                    docker build \
                      --no-cache \
                      --label "build.commit=${GIT_COMMIT}" \
                      --label "build.job=${BUILD_URL}" \
                      -t ${REGISTRY}/${IMAGE}:${GIT_COMMIT} .
                '''
            }
        }
        stage('Sign') {
            // Separate stage with separate credentials — defense in depth
            environment {
                COSIGN_KEY = credentials('cosign-signing-key')
            }
            steps {
                sh 'cosign sign --key env://COSIGN_KEY ${REGISTRY}/${IMAGE}:${GIT_COMMIT}'
            }
        }
    }
    post {
        always {
            // Clean workspace — prevent cross-build contamination
            cleanWs()
        }
    }
}
```

**SLSA provenance verification commands.**

```bash
# Verify a container image's SLSA provenance
slsa-verifier verify-image \
  ghcr.io/org/app@sha256:abc123... \
  --source-uri github.com/org/app \
  --source-tag v1.2.3

# Verify a binary artifact's SLSA provenance
slsa-verifier verify-artifact \
  ./app-linux-amd64 \
  --provenance-path ./app-linux-amd64.intoto.jsonl \
  --source-uri github.com/org/app \
  --source-tag v1.2.3

# Verify provenance with specific builder ID
slsa-verifier verify-artifact \
  ./artifact.tar.gz \
  --provenance-path ./provenance.intoto.jsonl \
  --source-uri github.com/org/repo \
  --builder-id https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.0.0
```

**Tekton Chains configuration — cosign signing backend.**

```yaml
# tekton-chains-config ConfigMap
# Applied to the tekton-chains namespace
apiVersion: v1
kind: ConfigMap
metadata:
  name: chains-config
  namespace: tekton-chains
data:
  # Signing backend — use cosign for Sigstore integration
  artifacts.taskrun.format: "in-toto"
  artifacts.taskrun.storage: "oci"
  artifacts.taskrun.signer: "cosign"

  # For keyless signing (Fulcio + Rekor)
  signers.cosign.fulcio.enabled: "true"
  signers.cosign.fulcio.address: "https://fulcio.sigstore.dev"
  signers.cosign.rekor.url: "https://rekor.sigstore.dev"

  # OCI image signing — attach attestations to image in registry
  artifacts.oci.format: "simplesigning"
  artifacts.oci.storage: "oci"
  artifacts.oci.signer: "cosign"

  # Transparency log — record all signing events
  transparency.enabled: "true"
  transparency.url: "https://rekor.sigstore.dev"
```

**cosign verification command examples.**

```bash
# Verify container image signature (keyless — checks Fulcio cert + Rekor)
cosign verify \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/org/app@sha256:abc123...

# Verify with attestation predicate (e.g., SBOM or vulnerability scan)
cosign verify-attestation \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  --type cyclonedx \
  ghcr.io/org/app@sha256:abc123...

# Verify using a specific public key (non-keyless)
cosign verify --key cosign.pub ghcr.io/org/app:v1.0.0
```

---

## 4. Dependency management and vulnerability scanning

### 4.1 Lock files and hash verification

Lock files pin dependency versions and record cryptographic hashes of each dependency's distribution artifact. The lock file ensures that `npm install` or `pip install` reproduces the exact dependency tree that was tested, reviewed, and approved, preventing surprise updates, version skew between environments, and substitution attacks.

**npm** generates `package-lock.json` with SHA-512 integrity hashes for every package and all transitive dependencies. The lockfile records the exact resolved version, the registry URL, and the hash. `npm ci` (clean install) installs exactly the versions in the lockfile and fails if the lockfile is inconsistent with `package.json` or if any package hash does not match — it never modifies the lockfile (unlike `npm install`, which may update it). In CI/CD pipelines, `npm ci` should always be used instead of `npm install`.

**pip** with hash-checking mode (`--require-hashes`) enforces that each dependency line in `requirements.txt` includes one or more `--hash=sha256:...` values. pip refuses to install any distribution whose hash doesn't match, preventing both tampering (modified packages on PyPI) and confusion (unexpected substitution of a different package version). `pip-tools` (the `pip-compile` command) generates requirements files with hashes. **Poetry** generates `poetry.lock` with SHA-256 hashes and complete dependency resolution.

**Cargo** (Rust) generates `Cargo.lock` with checksums (`checksum` field) for every crate sourced from crates.io. The checksums are SHA-256 hashes of the `.crate` file (the compressed archive downloaded from crates.io). `cargo install --locked` uses the exact versions from the lockfile.

**Go** uses `go.sum` containing SHA-256 hashes of module zip files and `go.mod` files. The Go module system verifies these hashes against the Go checksum database (`sum.golang.org`) — a global, publicly auditable transparency log of module hashes maintained by Google. Every Go module download is verified against this database, preventing tampering at the source or in transit. The checksum database provides a notarized hash for every (module, version) pair, meaning that all users of a given module version see the same content — a module author cannot serve different content to different users.

### 4.2 Dependency confusion and typosquatting

**Dependency confusion** (also called namespace confusion) exploits the way package managers resolve packages when both a private registry and a public registry are configured. If an organization has an internal package named `analytics-core` on its private registry, an attacker can publish a package with the same name on the public npm registry but with a higher version number. If the package manager checks the public registry and finds a higher version, it installs the public (malicious) package instead of the private one. Alex Birsan's 2021 research demonstrated this attack against Microsoft, Apple, and PayPal, achieving remote code execution on internal build servers through malicious `preinstall` scripts.

Defenses: namespace scoping (use `@org/package-name` scopes in npm — scoped packages can only be published by the scope owner), private registry priority configuration (configure the package manager to never query the public registry for internal package namespaces), and package reservation (pre-register internal package names on the public registry with a placeholder that documents the private package — preventing an attacker from claiming the name).

**Typosquatting** registers package names that are close misspellings of popular packages: `reqeusts` vs. `requests`, `logsah` vs. `logash`, `crossenv` vs. `cross-env`. Users who make a typo in `pip install` or `npm install` install the malicious package instead. The malicious package typically includes the legitimate package as a dependency (so functionality appears correct) while also executing a data exfiltration payload. Defenses: use lock files (which pin exact package names and hashes), enable dependency review in CI/CD (flagging new dependencies for human review), and use tools like Socket.dev, npm's provenance verification, and `pip-audit` to detect known-malicious packages.

**Protestware and maintainer-initiated sabotage** represent a different supply chain threat: the legitimate maintainer of a package intentionally introduces destructive or politically motivated code. The `colors` and `faker` npm packages (January 2022) were sabotaged by their own maintainer, who added an infinite loop that printed ANSI-color garbage to stdout, breaking thousands of downstream applications. The `node-ipc` package (March 2022) added code that, on systems with Russian or Belarusian IP addresses, overwrote files with heart emojis — a targeted data destruction payload masquerading as anti-war protest. These incidents are not detectable by vulnerability scanners (the "malicious" code is intentionally authored by the trusted maintainer), not preventable by code signing or provenance verification (the signature correctly identifies the legitimate maintainer), and only mitigable through: lock files (preventing automatic updates from pulling sabotaged versions), dependency review (human review of version diffs before updating), and package registry intervention (npm unpublished the malicious versions after community reports).

**StarJacking** is a social engineering variant: an attacker publishes a package with a GitHub repository URL pointing to a legitimate, popular project. Package registry UIs display the legitimate project's star count, making the malicious package appear trustworthy. The actual package code is different from the linked repository's code. Defenses: verify that the package content matches the linked repository (npm provenance attestations solve this by cryptographically binding the package to a specific repository and commit).

### 4.3 Vulnerability scanning tools

**npm audit** / **yarn audit**: scan the npm dependency tree against the GitHub Advisory Database (GHSA). `npm audit fix` attempts automatic remediation by updating to a patched version within the semver range allowed by `package.json`. `npm audit signatures` verifies that installed packages have valid registry signatures (a recent addition that detects packages that were tampered with after publication).

**pip-audit** (maintained by Trail of Bits): scans Python dependencies against the OSV database. It supports both `requirements.txt` and `pyproject.toml` inputs, and can scan installed packages in a virtual environment. Unlike `pip check` (which only checks version conflicts), `pip-audit` checks for known security vulnerabilities.

**cargo-audit**: scans Rust crate dependencies against the RustSec Advisory Database. It checks `Cargo.lock` for vulnerable crate versions and reports affected functions when possible. **cargo-deny** extends this with license checking, duplicate crate detection, and source verification.

**govulncheck** (Go team): scans Go modules against the Go vulnerability database (vuln.go.dev). govulncheck's distinguishing feature is call-graph analysis — it reports only vulnerabilities in functions actually called by the program, not just present in the dependency tree. This dramatically reduces false positives: a dependency may contain a vulnerable function in its XML parser, but if the program never calls that parser, govulncheck does not flag it.

**OSV.dev**: Google's open-source vulnerability database aggregating advisories from 15+ ecosystem-specific databases. OSV provides a unified API for querying vulnerabilities by package name and version, and the `osv-scanner` CLI tool integrates with CI/CD pipelines for cross-ecosystem scanning.

### 4.4 Private registry security and Dependabot/Renovate

Organizations should run private package registries and configure package managers to resolve from the private registry first, using the private registry as a proxy/cache for public registry access. **Artifactory** (JFrog) and **Nexus** (Sonatype) support virtual repositories that proxy the public registry: all package installations go through the private registry, which fetches from the public registry on cache miss and caches the result locally. This provides: caching (faster builds, resilience to public registry outages or left-pad-style package deletions), vulnerability scanning at the registry level (blocking downloads of packages with known critical vulnerabilities before they reach developer machines or CI/CD runners), license policy enforcement (blocking packages with incompatible licenses), and audit logging (recording which packages were downloaded by whom, enabling incident investigation if a package is later found to be malicious).

**Dependabot** (GitHub) and **Renovate** (Mend) automate dependency updates by scanning repositories for outdated or vulnerable dependencies, creating pull requests with version bumps, and running CI checks on the proposed updates. Configuration best practices: enable automerge for minor/patch security updates (reducing mean time to patch); require manual review for major version bumps; group related dependency updates (e.g., all `@types/*` packages in one PR) to reduce PR noise; configure update schedules to avoid overwhelming reviewers; and pin actions/dependencies to exact versions with automated hash verification in the Dependabot/Renovate configuration.

### 4.5 Software composition analysis (SCA) platforms

Software Composition Analysis tools go beyond vulnerability scanning by combining dependency inventory, license compliance, reachability analysis, and organizational policy enforcement into integrated platforms. Where point tools like `npm audit` or `cargo-audit` check a single ecosystem against a single database, SCA platforms maintain proprietary vulnerability databases with enrichments (exploitability ratings, contextual severity, available patches) beyond what public advisory databases provide, and integrate across the entire development lifecycle — IDE plugins catching vulnerable imports during development, CI/CD gates blocking builds, runtime monitoring detecting vulnerable libraries loaded in production, and container scanning analyzing deployed images.

**Snyk** operates across npm, PyPI, Maven, NuGet, Go, Rust, and container images. Snyk's priority score combines CVSS base score with temporal factors (exploit maturity, active exploitation in the wild) and environmental factors (reachability analysis — is the vulnerable code path actually invoked by the consuming application?). For container images, Snyk decomposes layer-by-layer, identifying which base image or installation step introduced each vulnerable package, enabling targeted remediation. Snyk's fix PRs suggest version upgrades that resolve vulnerabilities while minimizing breaking changes — analyzing the dependency graph to find the minimal version bump that eliminates the CVE without cascading semver incompatibilities. Snyk's IaC scanning extends SCA concepts to infrastructure configuration (Terraform, CloudFormation, Kubernetes manifests), treating infrastructure definitions as another component of the software supply chain.

**Mend (formerly WhiteSource)** emphasizes license compliance alongside security. Mend's license detection performs source-code-level analysis, scanning for license headers, SPDX identifiers, and code snippets copied from differently-licensed sources — detecting license leakage from GPL-licensed code copied into a proprietary codebase that manifest-based tools would miss. For enterprise environments with thousands of repositories, Mend's organizational policy engine allows centralized definition of approved licenses, banned packages (known-malicious or legally problematic), and version constraints, with policy violations surfacing as build failures or mandatory review requests.

**Black Duck (Synopsys)** differentiates through binary analysis. Rather than relying solely on manifest parsing, Black Duck analyzes compiled binaries, identifying embedded open-source components by matching code signatures against the KnowledgeBase — a database of billions of code snippets from open-source projects. This detects vendored dependencies (source copied into the project rather than declared as a package manager dependency), statically linked libraries (invisible to manifest-based scanners), and modified open-source components (forked code with changes that obscure its origin). Black Duck's snippet scanning identifies even partial code reuse — a function copied from a GPL-licensed project into a proprietary codebase creates a legal liability that manifest analysis cannot detect. For mergers and acquisitions, Black Duck's due diligence scanning is industry-standard: acquirers scan the target company's codebase for license risks and undisclosed open-source usage before closing the deal.

**FOSSA** focuses on license compliance at scale. FOSSA's dependency resolution handles multi-ecosystem projects (a monorepo containing Node.js services, Python ML pipelines, and Go microservices, each with distinct dependency graphs), producing a unified license report. FOSSA's deep license analysis handles dual-licensed packages (choosing the more permissive license when the consuming project qualifies), license exceptions (the GCC Runtime Library Exception, the Classpath Exception), and license compatibility matrices (automatically flagging when a dependency's license is incompatible with the project's output license — for example, an AGPL dependency in a proprietary SaaS product that would require source code disclosure of the entire combined work under the AGPL's network-use provision).

Enterprise SCA platform selection criteria for a conglomerate defending thousands of companies: coverage across all ecosystems in use (polyglot environments need multi-ecosystem support); binary analysis capability (for legacy codebases, vendor-provided binaries, and M&A due diligence); CI/CD integration depth (IDE plugins, PR checks, build gates, Kubernetes admission controllers); reachability analysis maturity (reducing false positive rates from 90%+ to actionable levels by distinguishing between "vulnerable code exists in a dependency" and "vulnerable code is actually reachable from the application's call graph"); license compliance engine sophistication (for legal team requirements — particularly in regulated industries where inadvertent GPL contamination of proprietary code creates significant liability); and API-first architecture (enabling integration with the SIEM/SOAR pipeline described in Domain 27C for correlating SCA findings with runtime telemetry and threat intelligence).

### 4.6 Operational tooling and dependency confusion defenses

**Vulnerability scanning command examples with output interpretation.**

```bash
# npm — scan against GitHub Advisory Database; exit 1 if >= audit-level found
npm audit --audit-level=moderate
npm audit fix         # Auto-update within semver range
npm audit signatures  # Verify registry provenance signatures

# pip-audit — scan Python deps against OSV; --require-hashes enforces hash check
pip-audit --require-hashes -r requirements.txt
pip-audit --fix --dry-run

# cargo-audit — scan Rust crates against RustSec; reports affected functions
cargo audit
cargo audit fix
cargo deny check advisories licenses bans

# govulncheck — Go scanner with call-graph analysis (only reachable vulns reported)
govulncheck ./...
```

**Dependency confusion defense — `.npmrc` configuration.** Prevent public registry from resolving internal scoped packages.

```ini
# .npmrc — placed in project root
# Force all @myorg scoped packages to resolve from private registry ONLY
@myorg:registry=https://npm.internal.example.com/
# Never fall through to public npmjs for internal scopes
//npm.internal.example.com/:_authToken=${NPM_INTERNAL_TOKEN}

# Optional: block all public registry access for this project
# (all packages must be proxied through the private registry)
registry=https://npm.internal.example.com/
```

**pip dependency confusion defense.** Prevent pip from resolving internal packages from PyPI.

```bash
# Use --index-url for private registry (primary), NOT --extra-index-url
# --extra-index-url adds PyPI as a fallback, enabling confusion attacks
# --index-url REPLACES PyPI entirely
pip install --index-url https://pypi.internal.example.com/simple/ mypackage

# pip.conf (global or per-virtualenv)
# [global]
# index-url = https://pypi.internal.example.com/simple/
# Do NOT add extra-index-url = https://pypi.org/simple/ — this re-enables confusion

# For projects needing both private AND public packages:
# Proxy public PyPI through the private registry (Artifactory/Nexus virtual repo)
# so all resolution goes through a single controlled endpoint
```

**Socket.dev integration for PR-level dependency review.** Socket analyzes every new or updated dependency in pull requests, detecting supply chain risks that vulnerability scanners miss: install scripts, network access, filesystem access, obfuscated code, and typosquatting indicators. It integrates as a GitHub App that comments on PRs with risk assessments for each dependency change, blocking merge when critical supply chain risks are detected. Configuration is via `socket.yml` in the repository root.

**Renovate configuration — automerge, grouping, and hash pinning.**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "helpers:pinGitHubActionDigests",
    ":pinDevDependencies"
  ],
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 6am on monday"]
  },
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"],
    "automerge": true
  },
  "packageRules": [
    {
      "description": "Automerge minor/patch updates for dev dependencies",
      "matchDepTypes": ["devDependencies"],
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true,
      "automergeType": "pr",
      "platformAutomerge": true
    },
    {
      "description": "Group all @types packages into a single PR",
      "matchPackagePatterns": ["^@types/"],
      "groupName": "TypeScript type definitions"
    },
    {
      "description": "Require manual review for major version bumps",
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "labels": ["major-update", "needs-review"]
    },
    {
      "description": "Pin GitHub Actions to SHA digests",
      "matchManagers": ["github-actions"],
      "pinDigests": true
    }
  ]
}
```

---

## 5. Sigstore ecosystem deep dive

### 5.1 Keyless signing with Fulcio and Rekor

Traditional code signing requires managing long-lived private keys — generating keys (on secure hardware, preferably), storing them securely (ideally in an HSM, never on developer laptops), rotating them periodically, distributing public keys or certificates for verification, and revoking them when compromised. This key lifecycle management is the reason most open-source projects do not sign their releases: the operational burden is too high for volunteer maintainers. Sigstore's keyless signing model eliminates long-lived key management entirely.

The keyless signing workflow: (1) The signer authenticates via an OIDC provider (GitHub, Google, Microsoft, GitLab — proving their identity through an existing authentication system). The OIDC provider issues a short-lived ID token (a signed JWT) containing the signer's identity claims (email address, organization, or CI/CD workflow identity). (2) **Fulcio** (the Sigstore certificate authority) receives the OIDC token, validates it against the OIDC provider's public keys, and issues a short-lived X.509 signing certificate (valid for 10 minutes). The certificate binds the signer's OIDC identity to a freshly generated ephemeral public key. Fulcio records the certificate issuance in its own certificate transparency log. (3) The signer signs the artifact with the corresponding ephemeral private key. (4) The signature and the Fulcio certificate are submitted to **Rekor** (the transparency log) — an append-only Merkle tree (based on Trillian, Google's verifiable data structure) that provides a tamper-evident, publicly auditable record of all signing events. Rekor returns a signed entry inclusion proof and a signed timestamp. (5) The ephemeral private key is discarded — it was used for a single signing operation and never stored persistently.

Verification checks: the Fulcio certificate was issued by Sigstore's trusted root CA; the certificate was valid at the time of signing (verified using the Rekor signed timestamp, not the local clock — this prevents attacks where a stolen key is used after the certificate expires); the OIDC identity in the certificate matches the expected signer (e.g., `https://github.com/myorg/myrepo/.github/workflows/release.yml@refs/tags/v1.0.0` for a GitHub Actions workflow — this is the build identity, not just a person's email); the Rekor entry exists and the inclusion proof is valid (proving the signing event was recorded in the transparency log); and the signature is cryptographically valid for the artifact's content. The verification establishes a complete trust chain: this artifact was signed by this identity at this time, and the signing event is immutably and publicly recorded.

### 5.2 Container image signing with cosign

**cosign** (part of the Sigstore project) signs and verifies OCI container images, WASM modules, and other OCI artifacts. The signature is stored alongside the image in the OCI registry using the cosign-defined OCI artifact media type — the signature is tagged with a deterministic tag derived from the image digest, so pulling the image also discovers its signature. This distribution mechanism means signatures travel with images through any OCI-compliant registry (Docker Hub, GitHub Container Registry, Amazon ECR, Google Artifact Registry, Harbor).

**Keyless signing workflow for containers.** In a GitHub Actions CI pipeline: `cosign sign --yes $IMAGE_DIGEST` triggers the OIDC → Fulcio → Rekor flow automatically. The resulting signature attestation records the GitHub Actions workflow identity, repository, commit SHA, and runner environment. No keys to manage, no secrets to store.

**Attestation signing.** Beyond simple signatures, cosign supports signing in-toto attestations: statements about the image's build process, vulnerability scan results, SBOM content, or custom policy compliance. `cosign attest --predicate sbom.cyclonedx.json --type cyclonedx $IMAGE_DIGEST` signs and attaches an SBOM attestation to the container image. Consumers can retrieve and verify both the image signature and its attestations.

**Policy enforcement with admission controllers.** Kubernetes admission controllers intercept pod creation requests and can enforce signature verification before allowing deployment. **Sigstore Policy Controller** (formerly cosign-gatekeeper) natively supports cosign signature verification. **Kyverno** policies can verify cosign signatures and attestation predicates (e.g., requiring that the image has a signed vulnerability scan attestation showing no critical CVEs). **OPA Gatekeeper** with cosign integration provides similar enforcement. The policy enforcement closes the supply chain loop: the build system signs the image (with SLSA provenance and SBOM attestations), the registry stores the image and its attached signatures/attestations, and the deployment platform verifies everything before running the image.

### 5.3 Package manager integration

**npm provenance (2023 GA).** npm supports Sigstore-based provenance attestations for published packages. When a package is published from a supported CI/CD environment (GitHub Actions) using `npm publish --provenance`, the npm CLI: generates a SLSA v1.0 provenance predicate describing the build (source repo, commit, workflow, builder), obtains a Sigstore keyless signature (Fulcio certificate bound to the GitHub Actions OIDC identity), submits the provenance attestation to Rekor, and uploads the signed provenance to the npm registry alongside the package tarball. Consumers can verify provenance with `npm audit signatures` — checking that the package was built from its stated source repository by an authorized CI workflow. This enables detection of packages that claim to come from a specific repository but were published from a different (potentially compromised) source.

**PyPI trusted publishers (2023).** PyPI's trusted publisher mechanism replaces long-lived API tokens with OIDC-based authentication for package uploads. The project owner registers a trust relationship in PyPI's UI: "GitHub repository `org/repo`, workflow `release.yml`, environment `pypi`." When the CI/CD workflow runs `twine upload`, it obtains a short-lived PyPI upload token by exchanging the GitHub Actions OIDC token — PyPI verifies the OIDC token's claims against the registered trust relationship and issues a scoped, short-lived API token. This eliminates the need to store a persistent PyPI API token as a repository secret (eliminating an entire class of credential-theft attacks). **PEP 761** (accepted 2024) extends this with Sigstore-based attestations for PyPI uploads, enabling cryptographic provenance verification of Python packages similar to npm provenance.

**Go module proxy and checksum database.** Go's module system uses `proxy.golang.org` as the default module proxy and `sum.golang.org` as the checksum database. Every `go get` or `go mod download` verifies the downloaded module against the checksum database. The checksum database is a Merkle tree (using Google's Trillian, the same technology underlying Sigstore's Rekor), ensuring that: all users of a given module version receive identical content (the proxy cannot serve different content to different users without detection), module content is tamper-evident (modifications are detectable by comparing against the checksum tree), and the verification is transparent (the tree can be independently audited). **GONOSUMCHECK** and `GONOSUMDB` environment variables can disable verification for private modules, but this should be done narrowly (only for the organization's own module prefix).

**cargo-vet** (Mozilla): a Rust supply chain audit tool that tracks which crate versions have been audited by whom. Organizations maintain an `audits.toml` file listing which crate versions have been reviewed, and `cargo vet` verifies that all dependencies in `Cargo.lock` have been audited (either by the organization directly or by trusted third-party audit sets — organizations can import Mozilla's, Google's, or other curated audit databases). `cargo-vet` does not replace vulnerability scanning (that's `cargo-audit`'s role) — it tracks code review of dependency source code, adding a human review layer to the supply chain.

### 5.4 Operational commands and policy enforcement

**Complete cosign keyless signing and verification workflow.**

```bash
# --- Keyless signing (Fulcio + Rekor) ---
# Sign a container image — triggers OIDC browser flow for identity
cosign sign --yes ghcr.io/org/app@sha256:abc123...
# In CI (GitHub Actions): OIDC token is automatic, no browser flow

# Sign a binary artifact (blob signing)
cosign sign-blob --yes --output-signature app.sig --output-certificate app.cert ./app-linux-amd64

# Attach and sign an SBOM attestation to an image
cosign attest --yes --predicate sbom.cyclonedx.json --type cyclonedx \
  ghcr.io/org/app@sha256:abc123...

# --- Keyless verification ---
# Verify image signature with identity constraints
cosign verify \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/org/app@sha256:abc123...

# Verify blob signature
cosign verify-blob \
  --signature app.sig \
  --certificate app.cert \
  --certificate-identity "user@example.com" \
  --certificate-oidc-issuer "https://accounts.google.com" \
  ./app-linux-amd64
```

**Fulcio certificate inspection.** After signing, the Fulcio certificate embedded in the signature contains the signer's OIDC identity. Inspecting this certificate reveals the full provenance chain.

```bash
# Extract and inspect the Fulcio certificate from a signed image
cosign verify \
  --certificate-identity-regexp ".*" \
  --certificate-oidc-issuer-regexp ".*" \
  ghcr.io/org/app@sha256:abc123... 2>/dev/null | jq '.[0].optional.Bundle.Payload.body' | \
  base64 -d | jq '.spec.signature.publicKey.content' | \
  base64 -d | openssl x509 -text -noout

# Key fields in the Fulcio certificate:
# - Subject Alternative Name: OIDC identity (email or CI workflow URI)
# - Issuer: Fulcio intermediate CA
# - Validity: ~10 minutes (short-lived ephemeral cert)
# - Extensions: GitHub workflow ref, repository, SHA (for CI-issued certs)
```

**Rekor transparency log lookup.** Every Sigstore signing event is recorded in Rekor. These commands query the log for audit and incident response.

```bash
# Search Rekor by artifact hash
rekor-cli search --artifact ./app-linux-amd64
# Returns: list of Rekor entry UUIDs matching the artifact

# Get full details of a Rekor entry
rekor-cli get --uuid 24296fb24b8ad77a1b3defc1ea37065b45e0596e1b63b1e64e3bf09c15ef6c0e27e18e97e3d85701
# Returns: signed entry timestamp, public key, signature, artifact hash,
#          inclusion proof (Merkle tree path proving entry exists in the log)

# Search Rekor by signer email
rekor-cli search --email user@example.com

# Verify a Rekor inclusion proof offline
rekor-cli verify --artifact ./app-linux-amd64 \
  --signature app.sig \
  --pki-format x509 \
  --public-key app.cert
```

**Kyverno ClusterPolicy for enforcing cosign signatures in Kubernetes.** This policy rejects any pod that references an unsigned container image.

```yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
  annotations:
    policies.kyverno.io/title: Verify Container Image Signatures
    policies.kyverno.io/description: >
      Requires all container images to be signed with cosign keyless
      signing (Sigstore) by an authorized CI workflow. Images without
      valid signatures or from unauthorized signers are rejected.
spec:
  validationFailureAction: Enforce  # Block non-compliant pods
  background: true
  webhookTimeoutSeconds: 30
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/org/*"
            - "registry.internal.example.com/*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/org/*/blob/main/.github/workflows/*"
                    issuer: "https://token.actions.githubusercontent.com"
                    rekor:
                      url: "https://rekor.sigstore.dev"
          attestations:
            - type: cyclonedx    # Require signed SBOM attestation
              conditions:
                - all:
                    - key: "{{ components[].name }}"
                      operator: NotEquals
                      value: ""
```

**OPA/Gatekeeper ConstraintTemplate for image signature verification.** For organizations using OPA Gatekeeper instead of Kyverno.

```yaml
apiVersion: templates.gatekeeper.sh/v1
kind: ConstraintTemplate
metadata:
  name: k8srequirecosignsignature
spec:
  crd:
    spec:
      names:
        kind: K8sRequireCosignSignature
      validation:
        openAPIV3Schema:
          type: object
          properties:
            allowedIssuers:
              type: array
              items:
                type: string
            allowedIdentityPatterns:
              type: array
              items:
                type: string
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package k8srequirecosignsignature

        import future.keywords.in

        violation[{"msg": msg}] {
          container := input.review.object.spec.containers[_]
          not image_is_signed(container.image)
          msg := sprintf("Container image %v is not signed with a valid cosign signature", [container.image])
        }

        violation[{"msg": msg}] {
          container := input.review.object.spec.initContainers[_]
          not image_is_signed(container.image)
          msg := sprintf("Init container image %v is not signed with a valid cosign signature", [container.image])
        }

        image_is_signed(image) {
          # Integration with Ratify (ratify.dev) as external data provider
          response := external_data({"provider": "ratify", "keys": [image]})
          response.responses[_].isSuccess == true
        }
```

Apply the template with a `K8sRequireCosignSignature` constraint resource targeting production/staging namespaces, specifying `allowedIssuers` and `allowedIdentityPatterns` matching the organization's OIDC issuer and repository patterns.

---

## 6. SBOM lifecycle management

### 6.1 Generation, formats, and tooling

An SBOM (Software Bill of Materials) enumerates all components — direct and transitive dependencies, embedded libraries, vendored code, build tools — included in a software product. SBOMs enable vulnerability management (quickly determining if a newly disclosed CVE affects the product), license compliance (ensuring all included components have compatible licenses), and incident response (identifying all systems running a component when a supply chain compromise is discovered).

**SPDX (Software Package Data Exchange)** is an ISO/IEC standard (ISO/IEC 5962:2021) developed by the Linux Foundation. SPDX documents describe: packages (name, version string, supplier, download location, package checksum), files (individual file hashes and license information), relationships between elements (DEPENDS_ON, CONTAINS, BUILD_TOOL_OF, DESCRIBED_BY — enabling representation of complex dependency graphs), and license information (SPDX license identifiers from the standardized license list, concluded license determined by analysis, and declared license stated by the package). SPDX supports multiple serialization formats: tag-value (human-readable), JSON (machine-readable), RDF/XML, and YAML.

**CycloneDX** is an OWASP standard optimized for security use cases. CycloneDX extends the core SBOM concept with: vulnerability information (linking components to known CVEs with VEX status — see §6.2), service descriptions (microservice dependencies, API endpoints, data flows), formulation data (how each component was built — build system, compiler version, build flags), and composition completeness indicators (expressing whether the SBOM represents a complete or partial inventory). CycloneDX natively supports VEX (Vulnerability Exploitability eXchange) as an embedded predicate, eliminating the need for separate VEX documents. CycloneDX serializes as JSON or XML.

**Generation tools.** **syft** (Anchore): generates SBOMs from container images (by analyzing image layers), file systems, and archives. Supports SPDX and CycloneDX output. Anchore's **grype** vulnerability scanner consumes syft-generated SBOMs for vulnerability matching. **cdxgen** (CycloneDX project): generates CycloneDX SBOMs from source code projects by parsing package manifests (package.json, pom.xml, build.gradle, requirements.txt, go.mod, Cargo.toml, .csproj). Supports 30+ ecosystems. **trivy** (Aqua Security): generates SBOMs and performs vulnerability scanning in a single integrated tool — useful for CI/CD pipelines that need both SBOM generation and vulnerability gating in a single step. **Microsoft SBOM Tool**: generates SPDX SBOMs for any project type, designed for enterprise adoption with Azure DevOps integration.

### 6.2 VEX and vulnerability management

**VEX (Vulnerability Exploitability eXchange)** addresses the false-positive problem in SBOM-based vulnerability management. An SBOM may list a component with a known CVE, but the vulnerability may not actually affect the product — the vulnerable function might not be called, the vulnerable code path might be unreachable due to configuration, or the product might have a compensating control that neutralizes the vulnerability. Without VEX, consumers of the SBOM must investigate every CVE associated with every component — a labor-intensive process that quickly becomes unmanageable for products with thousands of transitive dependencies.

A VEX statement declares the status of a specific vulnerability in the context of a specific product: **Not Affected** (the vulnerability exists in the component but does not affect this product — with a justification, e.g., "vulnerable function is not called," "vulnerable component is not reachable," "compensating control in place"), **Affected** (the vulnerability affects this product — with recommended actions), **Fixed** (the vulnerability was present but has been remediated in this version), or **Under Investigation** (the vendor is evaluating whether the vulnerability affects this product). VEX statements are machine-readable (JSON), enabling automated triage: a vulnerability scanner can consume the SBOM, identify CVEs in components, check VEX statements, and suppress alerts for vulnerabilities marked "Not Affected" — dramatically reducing alert fatigue.

VEX formats: **CSAF (Common Security Advisory Framework)** (OASIS standard) includes VEX as a profile. **CycloneDX VEX** embeds VEX statements directly in the CycloneDX SBOM document. **OpenVEX** (CISA-backed) is a standalone VEX format designed to be simple, machine-readable, and interoperable. The choice of format depends on the ecosystem — CycloneDX VEX is most natural for organizations already using CycloneDX SBOMs, while OpenVEX is format-agnostic.

### 6.3 Regulatory drivers and compliance

**Executive Order 14028 (US, May 2021)** requires software vendors selling to the US federal government to provide SBOMs for their products. The NTIA (National Telecommunications and Information Administration) defined minimum SBOM elements: supplier name, component name, version, unique identifier (such as a CPE or PURL), dependency relationship, author of the SBOM, and timestamp. The NTIA also specified that SBOMs should be generated for each new release and made available to the purchaser in a machine-readable format (SPDX or CycloneDX). Federal agencies are increasingly requiring SBOM delivery as part of procurement contracts, driving enterprise SBOM adoption across the US government's supply chain.

**EU Cyber Resilience Act (CRA, adopted 2024, enforcement phased 2025-2027).** The CRA requires manufacturers of "products with digital elements" (hardware and software) sold in the EU to: perform cybersecurity risk assessments, implement secure development lifecycle practices, provide security updates for the product's expected lifetime (minimum 5 years), report actively exploited vulnerabilities to ENISA within 24 hours, and provide SBOMs. The CRA applies to nearly all software and connected hardware sold in the EU — from consumer IoT devices to enterprise software platforms — with significant penalties (up to EUR 15 million or 2.5% of worldwide annual turnover, whichever is higher) for non-compliance. The CRA's SBOM requirement is the most impactful supply chain regulation globally due to the EU's market size and regulatory influence. Open-source software is partially exempt (open-source stewards — foundations like Apache, Eclipse, Linux Foundation — have lighter obligations than commercial vendors), but the supply chain pressure flows downstream: commercial vendors using open-source components must include those components in their SBOMs.

**NIST SP 800-218 (Secure Software Development Framework)** and **SSDF** requirements increasingly reference SBOM generation as a secure development practice. **FDA premarket cybersecurity guidance** (2023) requires medical device manufacturers to provide SBOMs for connected medical devices, including both hardware and software components. The FDA guidance specifically mandates that SBOMs include all commercial, open-source, and off-the-shelf software components, and that manufacturers maintain the SBOM throughout the product's lifecycle — updating it when firmware or software updates add or modify components. This lifecycle maintenance requirement distinguishes medical device SBOMs from one-time compliance artifacts: the SBOM must be a living document that accurately reflects the current state of the deployed device software at any point in time.

### 6.4 SBOM operational tooling

**syft — SBOM generation from container images and source projects.**

```bash
# syft: CycloneDX from container image
syft ghcr.io/org/app:v1.0.0 -o cyclonedx-json > sbom.cdx.json
# syft: SPDX from container image
syft ghcr.io/org/app:v1.0.0 -o spdx-json > sbom.spdx.json
# syft: SBOM from local source directory
syft dir:./my-project -o cyclonedx-json > sbom.cdx.json
# syft: with file metadata and digests
syft ghcr.io/org/app:v1.0.0 -o cyclonedx-json --file-metadata --file-digests > sbom-detailed.cdx.json
```

**grype — vulnerability scanning with SBOM input.**

```bash
grype ghcr.io/org/app:v1.0.0                      # Scan image directly
grype sbom:sbom.cdx.json                            # Scan from pre-generated SBOM
grype sbom:sbom.cdx.json -o json > vulns.json       # Machine-readable output
grype sbom:sbom.cdx.json --fail-on high             # CI gate: exit 1 if >= high
```

**cdxgen — multi-ecosystem SBOM generation.** Useful for monorepos with multiple languages and package managers.

```bash
cdxgen -o sbom.json ./monorepo      # Auto-detects all ecosystems
cdxgen -t docker -o sbom.json ghcr.io/org/app:v1.0.0  # Container image
cdxgen --deep -o sbom.json ./project  # Resolved (not just declared) dependencies
```

**OpenVEX document example.** A VEX statement declaring that a detected CVE does not affect the product, with machine-readable justification enabling automated triage.

```json
{
  "@context": "https://openvex.dev/ns/v0.2.0",
  "@id": "https://example.com/vex/2024/001",
  "author": "security@example.com",
  "role": "Product Security Team",
  "timestamp": "2024-06-15T10:30:00Z",
  "version": 1,
  "statements": [
    {
      "vulnerability": {
        "@id": "https://nvd.nist.gov/vuln/detail/CVE-2024-29944",
        "name": "CVE-2024-29944",
        "description": "Buffer overflow in libxml2 xmlParseAttValueComplex"
      },
      "products": [
        {
          "@id": "pkg:oci/app@sha256:abc123...",
          "identifiers": {
            "purl": "pkg:oci/app@sha256:abc123..."
          }
        }
      ],
      "status": "not_affected",
      "justification": "vulnerable_code_not_in_execute_path",
      "impact_statement": "The application does not parse XML from untrusted sources. libxml2 is present in the base image but the xmlParseAttValueComplex code path is never invoked. Verified by call-graph analysis with govulncheck.",
      "action_statement": "No action required. Base image will be updated in next scheduled release."
    }
  ]
}
```

**SBOM-to-vulnerability pipeline.** Automated workflow connecting SBOM generation, vulnerability scanning, and VEX triage in a CI/CD context.

```bash
#!/usr/bin/env bash
# sbom-vuln-pipeline.sh — runs in CI after image build
set -euo pipefail

IMAGE="${1:?Usage: $0 IMAGE_REF}"
SBOM_FILE="sbom.cdx.json"
VULN_FILE="vulns.json"
VEX_FILE="vex.openvex.json"  # Maintained by product security team in repo

# Step 1: Generate SBOM from the built image
echo "[1/4] Generating SBOM..."
syft "${IMAGE}" -o cyclonedx-json > "${SBOM_FILE}"

# Step 2: Scan SBOM for known vulnerabilities
echo "[2/4] Scanning for vulnerabilities..."
grype "sbom:${SBOM_FILE}" -o json > "${VULN_FILE}" || true

# Step 3: Apply VEX statements to suppress known not-affected findings
echo "[3/4] Applying VEX triage..."
if [ -f "${VEX_FILE}" ]; then
  # Filter out vulns with "not_affected" VEX status
  # (production systems use vexctl or grype's --vex flag)
  grype "sbom:${SBOM_FILE}" --vex "${VEX_FILE}" -o json > "${VULN_FILE}"
fi

# Step 4: Gate — fail if critical/high vulns remain after VEX triage
echo "[4/4] Evaluating gate policy..."
CRITICAL_COUNT=$(jq '[.matches[] | select(.vulnerability.severity == "Critical")] | length' "${VULN_FILE}")
HIGH_COUNT=$(jq '[.matches[] | select(.vulnerability.severity == "High")] | length' "${VULN_FILE}")

echo "Post-VEX findings: ${CRITICAL_COUNT} critical, ${HIGH_COUNT} high"
if [ "${CRITICAL_COUNT}" -gt 0 ]; then
  echo "GATE FAILED: ${CRITICAL_COUNT} critical vulnerabilities remain after VEX triage"
  exit 1
fi
echo "Gate passed."
```

---

## 7. Open-source maintainer security and ecosystem hardening

### 7.1 Commit signing and branch protection

**Commit signing** using GPG or SSH keys provides cryptographic proof that a specific developer authored a specific commit. Without commit signing, git commits contain only a self-declared `Author:` header — anyone can set `git config user.name "Linus Torvalds"` and create commits attributed to Torvalds. In the xz utils attack, all of Jia Tan's commits were unsigned — if the project had required signed commits from a verified GPG key linked to a verified identity, the attacker would have needed to either obtain a verified key (harder to do pseudonymously) or convince the maintainer to disable the requirement.

GitHub supports commit signing with GPG, SSH keys, or S/MIME, and displays a "Verified" badge on signed commits. Organizations should configure branch protection rules to require signed commits on protected branches (main/release branches). GitHub's vigilant mode goes further: it marks unsigned commits and commits signed with unverified keys as "Unverified," making it visually obvious when a commit's authorship cannot be cryptographically verified.

**Branch protection rules** enforce process controls on critical branches: required pull request reviews (minimum 1-2 reviewers, dismissing stale reviews when new commits are pushed), required status checks (CI must pass before merge), required linear history (preventing merge commits that can obscure the history), required signed commits, and restrictions on who can push (limiting to a set of authorized maintainers). For critical open-source projects, the CNCF and OpenSSF recommend: at least two maintainers with merge access (preventing single-point-of-failure like the xz situation), require two-person review for all merges to release branches, and enable audit logging of branch protection changes (detecting an attacker who gains admin access and weakens protections).

### 7.2 MFA enforcement and OpenSSF Scorecard

**MFA enforcement** prevents credential compromise from translating directly into repository compromise. PyPI mandated MFA for maintainers of the top 1% most-downloaded packages in 2023, and has progressively expanded the requirement. npm mandated MFA for maintainers of packages with more than 1 million weekly downloads. GitHub encouraged MFA and enabled mandatory 2FA for all contributors to public repositories in phases during 2023-2024. RubyGems mandated MFA for top gem maintainers.

MFA alone is not sufficient — phishing-resistant MFA (hardware security keys supporting FIDO2/WebAuthn) is necessary to prevent MFA bypass through real-time phishing proxies (evilginx2, modlishka — Domain 23A §2). GitHub, PyPI, npm, and crates.io all support FIDO2 hardware keys.

**OpenSSF Scorecard** is an automated tool that evaluates open-source projects against a set of security heuristics, producing a score (0-10) across categories: branch protection (are protected branches configured with required reviews?), code review (are PRs reviewed before merge?), CI tests (do CI checks run on PRs?), dependency update tool (is Dependabot or Renovate configured?), SAST (is static analysis running in CI?), signed releases (are releases signed with Sigstore or GPG?), dangerous workflow (does the project use dangerous GitHub Actions patterns like `pull_request_target` with checkout?), binary artifacts (are binary files checked into the repository?), and vulnerabilities (are there unfixed vulnerabilities in dependencies?). Scorecard results are published via the OpenSSF Scorecard API and can be consumed by automated systems — for example, a procurement policy might require that all dependencies have a Scorecard score above 7.

The Scorecard results for xz-utils (pre-backdoor) would have flagged several of the preconditions that enabled the attack: a single maintainer, no required code reviews, binary test files in the repository, and disabled fuzzing integration. While Scorecard alone would not have prevented the attack (Jia Tan was a trusted maintainer who could have met any process requirements), the low score would have signaled risk to downstream consumers evaluating whether to depend on the project.

**OpenSSF's Alpha-Omega initiative** takes a complementary approach: Alpha identifies the most critical open-source projects (by transitive dependency count and deployment breadth) and provides direct security support (funded security audits, maintainer grants, vulnerability response assistance); Omega provides automated security analysis at scale across the entire open-source ecosystem (running Scorecard, fuzzing, and SAST on thousands of projects). The Sovereign Tech Fund (German government) provides direct funding to critical open-source maintainers, addressing the economic sustainability gap that created the xz vulnerability (a burned-out maintainer with no funding who accepted help from an unknown volunteer because there was no alternative). The Linux Foundation's Census III study identifies the most widely deployed open-source packages to prioritize security investment — the study found that 25% of the most critical packages are maintained by a single developer, confirming the systemic risk that the xz incident exemplified.

### 7.3 Package registry security evolution

Package registries have evolved from simple file hosting to active security enforcement platforms. **npm's security evolution**: registry-side malware scanning (automated analysis of newly published packages for known malicious patterns — obfuscated code, network exfiltration, credential theft); provenance attestations (§5.3); package signing (registry-signed packages using Sigstore); `npm audit signatures` for verification; and the `npm unpublish` time window (preventing immediate deletion of published packages, which could disrupt downstream builds). **PyPI's evolution**: Malware Checks (automated scanning using tools like Warehouse's malware pipeline), trusted publishers (§5.3), mandatory MFA, and pending support for Sigstore attestations via PEP 761. **crates.io**: all published crates are immutable (once published, a version cannot be modified or deleted — only yanked, which prevents new installations but does not delete the package), preventing post-publication tampering. **Go module proxy**: the checksum database (§5.3) provides transparency for all public modules.

---

## 8. Build system hardening and code-signing infrastructure

### 8.1 Hermetic and reproducible build architectures

Hermetic builds are the strongest defense against build-time injection attacks like SUNSPOT. A hermetic build guarantees that the build's output depends only on its declared inputs — no network access, no access to undeclared files, no dependency on mutable system state (timestamps, environment variables, random seeds). This guarantee means that even if the build server is compromised, the attacker cannot inject additional content into the build output without modifying the declared inputs (which are version-controlled, hash-verified, and code-reviewed).

**Bazel** achieves hermeticity through sandboxed execution: each build action (compilation, linking, resource bundling) runs in a filesystem sandbox (Linux namespaces or macOS sandbox-exec) where only declared inputs are visible. Bazel's remote execution protocol allows build actions to run on remote workers (cloud VMs or containers) with the same sandboxing guarantees, enabling distributed builds without sacrificing hermeticity. Bazel's content-addressable cache (which caches build outputs keyed by the hash of all inputs) ensures reproducibility — the same inputs always produce the same outputs, regardless of when or where the build runs.

**Nix** takes a different approach: the entire build environment (compiler, libraries, build tools) is described declaratively in a Nix expression, and builds run in an isolated environment where only the explicitly declared dependencies are available. Nix's store (at `/nix/store/`) uses content-addressed paths — the path includes a hash of all inputs, so any change to the build inputs produces a different output path. This makes reproducibility a natural consequence of the build system's design.

**Google's SLSA framework and Bazel integration.** Google internally uses Bazel with remote execution on Borg (their cluster management system) to achieve hermetic builds at massive scale. The internal build system (Blaze, the predecessor to open-source Bazel) compiles every binary from source in a sandboxed environment — there are no pre-compiled dependencies, no fetches from external registries during build, and every tool (compiler, linker, code generator) is itself built from source as part of the build graph. This extreme hermeticity is what Google's SLSA framework aspires to standardize for the broader ecosystem. For organizations adopting Bazel, the `--experimental_strict_action_env` flag strips environment variables from build actions (preventing environment-dependent non-determinism), `--sandbox_debug` enables detailed logging of sandbox violations, and `--remote_upload_local_results` combined with `--remote_cache` enables shared build caches that verify cache entries by input hash.

**Reproducibility challenges** that affect real-world builds: embedded timestamps (compilers embed the build date in binaries — use `SOURCE_DATE_EPOCH` to fix timestamps), file ordering (directory traversal order varies by filesystem — sort file lists before processing), path embedding (absolute paths in debug info or `__FILE__` macros — use compiler flags like `-fdebug-prefix-map` to remap paths), archive ordering (tar and zip archives may order entries differently — use `--sort=name`), and hash randomization (Python's dict ordering, Perl's hash randomization — seed with fixed values during builds).

### 8.2 Code-signing infrastructure and HSM key management

Code-signing infrastructure protects the signing keys that establish trust in distributed software. The SolarWinds incident demonstrated that a compromised build server with access to signing keys allows the attacker to produce legitimately-signed malicious artifacts.

**HSM-backed signing** stores code-signing private keys in Hardware Security Modules (Domain 17D §3) — purpose-built cryptographic processors where the key material never exists in extractable form. The signing operation occurs inside the HSM: the artifact hash is sent to the HSM, the HSM performs the signature operation internally, and returns the signature. Even with full administrative access to the HSM's host server, the attacker cannot extract the private key — they can only request signatures while they maintain access (which is detectable through audit logging and anomaly detection on signing volume and timing). Cloud HSM services (AWS CloudHSM, Azure Dedicated HSM, Google Cloud HSM) provide FIPS 140-2 Level 3 certified HSMs as managed services.

**Signing policy enforcement** adds a review layer between the build system and the signing service. Rather than allowing any build to trigger signing, the signing service enforces policies: only builds from the official CI pipeline (verified through CI system integration or OIDC tokens) can request signing; only builds from protected branches (main, release branches) are signed with production keys; all signing requests are logged and auditable; and anomalous signing patterns (unusual frequency, unusual artifact types, signing outside business hours) trigger alerts. **SignPath** and **DigiCert Software Trust Manager** are commercial signing-as-a-service platforms that implement these policy controls.

**Certificate transparency for code signing** applies the web PKI's certificate transparency model to code-signing certificates. Apple's notarization service, Microsoft's SmartScreen, and Sigstore's Rekor all implement forms of code-signing transparency. When a code-signing certificate is issued, the issuance is logged in a transparency log. Monitors can watch the log for unauthorized certificates — if an attacker obtains a fraudulent code-signing certificate (through CA compromise or social engineering), the log entry enables detection. Google's Binary Transparency project extends this concept to all distributed binaries, not just signed ones — creating a verifiable log of all binaries distributed by a platform (Android APKs, Chrome extensions, firmware updates).

**Key rotation and revocation** plans are critical but often neglected. Organizations should define: rotation schedule (annual for production signing keys, more frequent for test/staging keys — aligned with certificate validity periods and compliance requirements), emergency revocation procedure (who has authority to revoke, the escalation path, how quickly revocation can propagate to all consumers via CRL distribution points and OCSP responders — note that some code-signing ecosystems have poor revocation support, meaning revoked certificates may still be trusted by older clients), key escrow for business continuity (ensuring that the loss of a single key custodian does not halt all software releases — using Shamir's Secret Sharing or multi-party HSM configurations where M-of-N administrators must authenticate), and multi-party signing ceremonies for root key generation (following the ceremony protocols documented by DNSSEC root key ceremonies, certificate authority root ceremonies, and the Sigstore root-signing ceremony — these ceremonies involve multiple independent witnesses, tamper-evident hardware, air-gapped machines, and detailed audit logs).

For enterprise environments, **timestamping** is a critical complement to code signing. Code-signing certificates expire (typically 1-3 years for commercial certificates), and unsigned timestamps mean that signatures become invalid after certificate expiry — even for software that was legitimately signed during the certificate's validity period. RFC 3161 timestamps from a trusted timestamping authority (TSA) provide a cryptographic proof that the signature existed before a specific time, allowing the signature to remain valid even after the signing certificate expires. All code-signing operations should include a timestamp countersignature from a trusted TSA.

---

## 9. Supply chain attack detection engineering

This section consolidates detection engineering for supply chain attack patterns into a unified matrix with operational detection rules. Where earlier sections (§1–§2) provided attack-specific detection, this section addresses cross-cutting detection patterns applicable to supply chain threats generally.

### 9.1 Detection matrix

The following matrix maps supply chain attack types to applicable detection methods. Each cell indicates detection feasibility: **H** = high confidence, **M** = moderate (useful but generates false positives), **L** = low confidence or theoretical, **—** = not applicable.

| Attack Type | YARA (artifact) | Sigma (endpoint) | Network (Suricata/Zeek) | Behavioral (eBPF/EDR) | Build Provenance |
|---|---|---|---|---|---|
| Dependency confusion | M (malicious pkg content) | H (unexpected pkg install source) | H (resolution to public registry for internal names) | M (postinstall script behavior) | H (provenance mismatch) |
| Typosquatting | M (similar to legit pkg) | M (new dependency alert) | L (normal registry traffic) | H (unexpected network/file ops) | M (unknown publisher) |
| Build injection (SUNSPOT-style) | H (injected binary artifacts) | H (source file modification during build) | L (local build server) | H (file substitution during MSBuild) | H (reproducibility failure) |
| Maintainer compromise (xz-style) | H (backdoor artifacts in binary) | M (anomalous process behavior) | L (backdoor may use existing channels) | H (IFUNC/hooking anomalies) | M (tarball-to-git diff) |
| CI/CD secret exfiltration | — | H (unexpected outbound from CI runner) | H (exfil to unauthorized destinations) | H (credential file access patterns) | — |
| Protestware/sabotage | L (destructive patterns vary) | H (data destruction, infinite loops) | M (may contact external services) | H (anomalous resource usage) | L (legitimate maintainer) |
| Cascading supply chain (3CX) | H (trojanized DLLs) | H (anomalous child processes) | H (C2 to unexpected domains) | H (shellcode execution patterns) | H (build provenance chain break) |

### 9.2 Sigma rules for build-time anomalies

**Unexpected package manager network calls during build.** In hermetic build environments, package managers should not make network requests during compilation. This rule detects npm, pip, cargo, or go fetching packages during the build phase rather than the dependency-resolution phase.

```yaml
title: Unexpected Package Manager Network Activity During Build
id: d4e5f6a7-89ab-cdef-0123-456789abcdef
status: experimental
description: >
  Detects package manager processes making network connections during
  the compilation/build phase. In hermetic builds, dependency resolution
  should be complete before compilation starts. Network activity during
  build indicates either a non-hermetic build or a build injection
  attempting to fetch malicious payloads.
author: Supply chain defense team
date: 2024-08-01
tags:
  - attack.execution
  - attack.t1195.002
logsource:
  category: network_connection
  product: linux
detection:
  selection_build_context:
    # Process is a child of a build system
    ParentImage|endswith:
      - '/make'
      - '/ninja'
      - '/bazel'
      - '/gradle'
      - '/mvn'
      - '/msbuild'
      - '/cargo'
  selection_package_managers:
    Image|endswith:
      - '/npm'
      - '/node'
      - '/pip'
      - '/pip3'
      - '/python'
      - '/python3'
      - '/cargo'
      - '/go'
      - '/curl'
      - '/wget'
  selection_network:
    DestinationPort:
      - 80
      - 443
    Initiated: 'true'
  condition: selection_build_context and selection_package_managers and selection_network
falsepositives:
  - Build systems that intentionally fetch during compilation (non-hermetic builds)
  - Code generators that download schemas at build time
level: high
```

**CI/CD secret exfiltration patterns.** Detects processes in CI runner contexts that read credential files or environment variables and then initiate outbound network connections — the pattern of secret theft and exfiltration.

```yaml
title: CI/CD Secret Exfiltration Pattern
id: e5f6a7b8-9abc-def0-1234-56789abcdef0
status: experimental
description: >
  Detects a sequence where a process running in a CI context reads
  sensitive credential files or environment variables, followed by
  outbound network activity to non-allowlisted destinations.
  Indicates potential secret exfiltration from a compromised CI job.
author: Supply chain defense team
date: 2024-08-01
tags:
  - attack.exfiltration
  - attack.t1020
  - attack.credential_access
  - attack.t1552.001
logsource:
  category: process_creation
  product: linux
detection:
  selection_ci_context:
    # Running inside CI — check for CI environment indicators
    EnvironmentVariables|contains:
      - 'CI=true'
      - 'GITHUB_ACTIONS=true'
      - 'GITLAB_CI=true'
      - 'JENKINS_URL='
  selection_credential_access:
    CommandLine|contains:
      - '.env'
      - 'credentials'
      - 'secrets'
      - '/run/secrets/'
      - 'AWS_SECRET_ACCESS_KEY'
      - 'GITHUB_TOKEN'
      - 'NPM_TOKEN'
      - 'PYPI_TOKEN'
      - '.npmrc'
      - '.docker/config.json'
      - '.ssh/id_'
  selection_exfil:
    Image|endswith:
      - '/curl'
      - '/wget'
      - '/nc'
      - '/ncat'
      - '/python'
      - '/python3'
      - '/node'
    CommandLine|contains:
      - 'http://'
      - 'https://'
      - 'webhook'
      - 'ngrok'
      - 'requestbin'
      - 'pipedream'
  condition: selection_ci_context and selection_credential_access and selection_exfil
falsepositives:
  - Legitimate CI jobs that upload artifacts to authorized destinations
  - Deployment steps that read credentials and connect to cloud APIs
level: critical
```

**Build output hash mismatch.** Detects when a reproducible build produces a different hash than expected — indicating either a build system issue or a build injection attack.

```yaml
title: Build Output Hash Mismatch - Reproducibility Failure
id: f6a7b8c9-abcd-ef01-2345-6789abcdef01
status: experimental
description: >
  Detects when the hash of a build output does not match the expected
  hash from a reproducible build. In SLSA Level 3+ environments, this
  indicates potential build injection or non-determinism that must be
  investigated.
author: Supply chain defense team
date: 2024-08-01
tags:
  - attack.defense_evasion
  - attack.t1195.002
logsource:
  category: application
  product: cicd
detection:
  selection:
    EventType: 'build_verification'
    Result: 'hash_mismatch'
  condition: selection
falsepositives:
  - Intentional build configuration changes not yet reflected in expected hashes
  - Non-deterministic build components (timestamps, ordering)
level: high
```

### 9.3 Suricata rules for hermetic build violations

Build environments that are supposed to be hermetic (no network access during compilation) can be monitored at the network level. These rules detect network traffic originating from build infrastructure that should be air-gapped during the build phase.

```
# Detect any outbound HTTP/HTTPS from build infrastructure during build window
# Assumes build servers are tagged in $BUILD_SERVERS
alert http $BUILD_SERVERS any -> $EXTERNAL_NET any (
    msg:"SUPPLY-CHAIN: Build server outbound HTTP during build phase";
    flow:established,to_server;
    classtype:policy-violation;
    sid:2024010; rev:1;
    metadata: deployment build-monitoring;
)

# Detect DNS resolution from build servers to public package registries
# during compilation (resolution should happen only in dependency-fetch phase)
alert dns $BUILD_SERVERS any -> any 53 (
    msg:"SUPPLY-CHAIN: Build server DNS to package registry during build";
    dns.query;
    content:"registry.npmjs.org"; nocase;
    classtype:policy-violation;
    sid:2024011; rev:1;
)

alert dns $BUILD_SERVERS any -> any 53 (
    msg:"SUPPLY-CHAIN: Build server DNS to PyPI during build";
    dns.query;
    content:"pypi.org"; nocase;
    classtype:policy-violation;
    sid:2024012; rev:1;
)

# Detect exfiltration patterns from build servers — large outbound transfers
alert tcp $BUILD_SERVERS any -> $EXTERNAL_NET any (
    msg:"SUPPLY-CHAIN: Large outbound transfer from build server";
    flow:established,to_server;
    dsize:>10000;
    threshold:type both, track by_src, count 5, seconds 60;
    classtype:policy-violation;
    sid:2024013; rev:1;
)
```

### 9.4 eBPF-based build process monitoring

eBPF provides kernel-level visibility into build process behavior without requiring modifications to the build system itself. The following conceptual eBPF monitoring targets detect supply chain attacks during build execution.

**Detecting unexpected child processes during compilation.** A hermetic build should only spawn expected processes (compiler, linker, assembler). Unexpected child processes (shells, network tools, interpreters) indicate potential build injection.

```bash
# bpftrace one-liner: log all child processes spawned by make/ninja/bazel
bpftrace -e 'tracepoint:sched:sched_process_exec /comm == "make" || comm == "ninja"/ { printf("BUILD CHILD: pid=%d comm=%s exe=%s\n", pid, comm, str(args->filename)); }'
```

For production-grade monitoring, use Cilium Tetragon with a TracingPolicy that enforces an allowlist of permitted build processes:

```yaml
# Tetragon TracingPolicy — detect non-allowlisted processes spawned during build
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: build-process-allowlist
spec:
  kprobes:
    - call: "security_bprm_check"
      syscall: false
      args:
        - index: 0
          type: "linux_binprm"
      selectors:
        - matchArgs:
            - index: 0
              operator: "NotIn"
              values:
                # Allowlisted build processes only
                - "/usr/bin/gcc"
                - "/usr/bin/g++"
                - "/usr/bin/ld"
                - "/usr/bin/as"
                - "/usr/bin/ar"
                - "/usr/bin/make"
                - "/usr/bin/ninja"
                - "/usr/bin/strip"
                - "/usr/bin/objcopy"
          matchNamespaces:
            - namespace: Build
              operator: In
              values:
                - "build-runner"
          matchActions:
            - action: Post
              rateLimit: "1m"
```

**Detecting network connections during compilation.** Build processes that open network sockets during compilation are either non-hermetic or compromised.

```bash
# bpftrace: monitor connect() syscalls from build process tree
bpftrace -e '
tracepoint:syscalls:sys_enter_connect
/comm == "gcc" || comm == "cc1" || comm == "ld" || comm == "as" ||
 comm == "rustc" || comm == "cargo" || comm == "go"/
{
    $sa = (struct sockaddr_in *)args->uservaddr;
    if ($sa->sin_family == AF_INET) {
        printf("ALERT: Build process %s (pid=%d) connecting to %s:%d\n",
               comm, pid,
               ntop(AF_INET, $sa->sin_addr.s_addr),
               $sa->sin_port);
    }
}
'
```

These eBPF-based monitors complement network-level Suricata rules by providing process-level attribution — network rules detect the traffic, eBPF rules identify which specific build process initiated it. Combined with SLSA provenance and reproducible build verification, they form a defense-in-depth detection stack for build-time supply chain attacks.

---

## 10. Supply chain incident response and forensics

### 10.1 Incident response playbook for supply chain compromise discovery

Supply chain compromises differ from conventional intrusions in a critical dimension: the attacker enters through a trusted channel, meaning standard perimeter-based detection and response assumptions fail. The IR playbook must account for the fact that the compromised component was deliberately installed and approved, often by automated systems that trusted upstream provenance.

**Phase 1 — Triage and scoping.** Upon suspicion of a supply chain compromise, the first action is freezing the artifact pipeline — halting all deployments, build promotions, and package publications until the scope is established. Unlike a network intrusion where containment means isolating a host, supply chain containment means stopping the propagation of potentially compromised artifacts to additional environments.

```bash
# Immediate triage: identify all instances of the suspect package across environments
# Example: scanning for a compromised npm package version

# 1. Query internal registry for all downloads of the suspect version
curl -s "https://registry.internal.corp/api/npm/npm-remote/-/package/@scope/suspect-pkg/dist-tags" \
  | jq '.'

# 2. Search all lock files across repositories for the compromised version
gh search code "\"suspect-pkg\": \"1.2.3\"" --owner=org-name --filename=package-lock.json -L 100

# 3. Scan container images in registry for the compromised library
# Uses grype to check specific image digests
for image in $(crane ls registry.internal.corp/production/ 2>/dev/null); do
  grype "registry.internal.corp/production/${image}" \
    --only-fixed \
    --name "suspect-pkg" \
    --output table 2>/dev/null
done

# 4. Query SBOM database for all products containing the compromised component
# Assumes SBOM indexing via Dependency-Track or GUAC
curl -s "https://deptrack.internal.corp/api/v1/search/component" \
  -H "X-Api-Key: ${DEPTRACK_API_KEY}" \
  -d '{"name":"suspect-pkg","version":"1.2.3"}' | jq '.[] | .project.name'
```

**Phase 2 — Impact assessment.** Determine whether the compromised artifact reached production, which services consumed it, and what data those services had access to. This is where SBOM investment pays off — organizations with indexed SBOMs can answer "what is affected" in minutes; those without may take days.

**Phase 3 — Eradication.** Replace the compromised artifact with a known-good version. This is not simply rolling back — the compromised version may have persisted data, modified configurations, or established C2 channels that survive artifact replacement. Full eradication requires:

1. Pinning to the last known-good version in all lock files
2. Rebuilding all dependent artifacts from clean sources
3. Rotating any secrets that the compromised component could have accessed
4. Invalidating any tokens, sessions, or certificates issued during the compromise window
5. Scanning runtime environments for persistence mechanisms

**Phase 4 — Recovery and validation.** Rebuild and redeploy from verified sources, with enhanced monitoring for indicators of the specific compromise. Validate that the replacement artifacts produce identical behavior to pre-compromise baselines (excluding the malicious behavior).

### 10.2 Forensic analysis of compromised build artifacts

When a supply chain compromise is suspected, comparing the suspected artifact against a known-good build of the same source is the primary forensic technique. The tools `diffoscope` and `reprotest` (from the Reproducible Builds project) are essential.

```bash
# Install forensic tooling
apt-get install diffoscope reprotest disorderfs strip-nondeterminism

# Compare a suspect binary against a clean rebuild from the same source tag
# diffoscope performs recursive, format-aware comparison
diffoscope \
  --html-dir ./forensic-report/ \
  --max-diff-block-lines 500 \
  --text ./forensic-report/diff.txt \
  ./artifacts/suspect-liblzma.so.5.6.1 \
  ./clean-rebuild/liblzma.so.5.6.1

# For container images: compare layers
diffoscope \
  --html-dir ./container-forensic/ \
  <(skopeo copy docker://registry.corp/app:suspect oci:suspect-image:latest && \
    umoci unpack --image suspect-image:latest suspect-rootfs) \
  <(skopeo copy docker://registry.corp/app:known-good oci:good-image:latest && \
    umoci unpack --image good-image:latest good-rootfs)

# reprotest: verify if a build is reproducible (non-reproducibility is a red flag)
reprotest \
  --vary=+all \
  --source-pattern '*.tar.gz' \
  'dpkg-buildpackage -b -uc -us' \
  '*.deb'

# Extract and compare ELF sections specifically (faster than full diffoscope)
readelf -a ./suspect-binary > suspect-elf.txt
readelf -a ./clean-binary > clean-elf.txt
diff -u clean-elf.txt suspect-elf.txt | head -200

# Check for injected object files in shared libraries
objdump -t ./suspect-liblzma.so | grep -v "\.o:" | sort > suspect-symbols.txt
objdump -t ./clean-liblzma.so | grep -v "\.o:" | sort > clean-symbols.txt
comm -23 suspect-symbols.txt clean-symbols.txt  # symbols only in suspect
```

**Sigma rule — detection of anomalous build artifact divergence.**

```yaml
title: Build Artifact Hash Mismatch from Identical Source
id: e7f3a1b2-4c5d-6e7f-8a9b-0c1d2e3f4a5b
status: experimental
description: >
  Detects when a build produces an artifact whose hash differs from a previous
  build of the same source commit, indicating potential build environment
  compromise or non-deterministic injection.
date: 2025-06-15
author: Supply Chain Security Team
references:
  - https://reproducible-builds.org/
  - https://slsa.dev/spec/v1.0/threats
logsource:
  category: application
  product: ci_cd_pipeline
detection:
  selection:
    event_type: "build_complete"
  filter_mismatch:
    artifact_hash|ne: expected_hash_for_commit
    source_commit_verified: true
    build_config_hash_match: true
  condition: selection and filter_mismatch
level: critical
tags:
  - attack.defense_evasion
  - attack.t1195.002
falsepositives:
  - Non-reproducible builds without SOURCE_DATE_EPOCH
  - Builds with embedded timestamps or random nonces
```

### 10.3 Dependency tree forensics — identifying the injection point

When a compromised dependency is discovered, determining the injection point requires walking the dependency tree in reverse — from the compromised artifact back through every transitive dependency to find where malicious code entered.

```bash
# npm: generate full dependency tree and search for suspect package
npm ls --all --json 2>/dev/null | jq '
  [.. | objects | select(.version? and .resolved?) |
   {name: (input_filename // "root"), version: .version, resolved: .resolved}]
' | grep -A2 "suspect-pkg"

# pip: trace how a compromised package entered the dependency tree
pip install pipdeptree
pipdeptree --reverse --packages suspect-pkg
# Output shows which packages depend on the suspect package

# Go: find all import paths that pull in a compromised module
go mod graph | grep "compromised-module" | awk '{print $1}' | sort -u

# Maven: dependency tree with specific artifact highlighted
mvn dependency:tree -Dincludes=com.suspect:artifact -Dverbose

# Cargo: reverse dependency lookup
cargo tree --invert --package suspect-crate@1.2.3

# Compare lock files across git history to find when the bad dependency was introduced
git log --all --oneline -- '**/package-lock.json' '**/yarn.lock' '**/Cargo.lock' '**/go.sum' \
  | head -20
# Then for each commit:
git show <commit>:path/to/package-lock.json | jq '.dependencies["suspect-pkg"].version'
```

### 10.4 Timeline reconstruction from CI/CD audit logs

CI/CD audit logs are the primary evidence source for supply chain compromise investigations. Key events to extract: who triggered builds, what source was used, which runners executed the build, what artifacts were produced, and what was deployed.

```bash
# GitHub Actions: extract workflow run history for a repository
gh api repos/org/repo/actions/runs \
  --paginate \
  --jq '.workflow_runs[] |
    {id, name, head_sha, event, triggering_actor: .triggering_actor.login,
     created_at, updated_at, conclusion, run_attempt}' \
  > workflow-runs-audit.jsonl

# GitHub Actions: extract specific workflow run logs (compressed)
gh api repos/org/repo/actions/runs/{run_id}/logs -H "Accept: application/zip" \
  > run-${run_id}-logs.zip

# GitLab: extract pipeline audit events via API
curl -s --header "PRIVATE-TOKEN: ${GITLAB_TOKEN}" \
  "https://gitlab.corp/api/v4/projects/${PROJECT_ID}/pipelines?per_page=100&updated_after=2025-01-01T00:00:00Z" \
  | jq '.[] | {id, sha, ref, status, created_at, updated_at, source, user: .user.username}'

# Jenkins: extract build records with parameters
curl -s "https://jenkins.corp/job/pipeline-name/api/json?tree=builds\
[number,timestamp,result,actions[causes[userId,shortDescription],parameters[name,value]]]" \
  | jq '.builds[]'

# Correlate: find all builds between two dates that produced artifacts
# matching the compromised hash
jq -r 'select(.created_at >= "2025-01-15" and .created_at <= "2025-02-01") |
  "\(.id)\t\(.head_sha)\t\(.triggering_actor)\t\(.created_at)"' \
  workflow-runs-audit.jsonl | sort -t$'\t' -k4
```

### 10.5 Communication and disclosure protocols

Supply chain incidents have a unique disclosure complexity: the compromised component is typically used by many downstream consumers, each of whom must be notified and must perform their own impact assessment.

**Coordinated disclosure timeline (recommended):**

1. **T+0h:** Internal discovery and triage team activated. Embargo begins.
2. **T+4h:** Initial impact scope determined. CISO and legal notified.
3. **T+24h:** Upstream maintainer notified (if the compromise is in a third-party package). CVE requested via MITRE or relevant CNA.
4. **T+48h:** Known affected downstream consumers notified under embargo (distribution security teams, major corporate users with established security contacts).
5. **T+72h (or sooner if active exploitation detected):** Public advisory published. SBOM-equipped consumers can immediately query their systems.
6. **T+7d:** Detailed technical analysis published to enable community detection and forensics.

### 10.6 Legal and regulatory considerations

**CISA reporting requirements (CIRCIA — Cyber Incident Reporting for Critical Infrastructure Act of 2022).** Covered entities must report substantial cyber incidents within 72 hours to CISA, and ransomware payments within 24 hours. Supply chain compromises affecting critical infrastructure software fall under the "substantial" threshold when they involve: exploitation of a zero-day in widely used software, compromise of identity/authentication systems, or disruption to critical infrastructure operations.

**SEC reporting (public companies).** SEC Rule 2023-148 requires disclosure of material cybersecurity incidents within four business days via Form 8-K. Supply chain compromises that affect financial systems, customer data, or revenue-generating services are likely material.

**EU NIS2 Directive.** Entities in scope must report significant incidents to the national CSIRT within 24 hours (early warning), with a full incident report within 72 hours. Supply chain attacks are explicitly called out as a risk category in NIS2 Article 21(2)(d).

**Evidence preservation requirements.** Forensic evidence must be preserved with chain-of-custody documentation. For supply chain incidents:

```bash
# Create forensic archive with integrity verification
mkdir -p ./forensic-evidence/$(date -u +%Y%m%dT%H%M%SZ)
EVIDENCE_DIR="./forensic-evidence/$(date -u +%Y%m%dT%H%M%SZ)"

# Capture compromised artifacts
cp ./suspect-artifact "${EVIDENCE_DIR}/"
sha256sum "${EVIDENCE_DIR}/suspect-artifact" > "${EVIDENCE_DIR}/hashes.sha256"
sha512sum "${EVIDENCE_DIR}/suspect-artifact" >> "${EVIDENCE_DIR}/hashes.sha512"

# Capture CI/CD logs
cp ./workflow-runs-audit.jsonl "${EVIDENCE_DIR}/"
cp ./run-*-logs.zip "${EVIDENCE_DIR}/"

# Capture dependency state
cp package-lock.json "${EVIDENCE_DIR}/package-lock.json.evidence"
cp yarn.lock "${EVIDENCE_DIR}/yarn.lock.evidence" 2>/dev/null

# Sign the evidence archive
tar czf "${EVIDENCE_DIR}.tar.gz" "${EVIDENCE_DIR}/"
sha256sum "${EVIDENCE_DIR}.tar.gz" > "${EVIDENCE_DIR}.tar.gz.sha256"
gpg --detach-sign --armor "${EVIDENCE_DIR}.tar.gz"

# Record timestamp
echo "Evidence collected: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "${EVIDENCE_DIR}/collection-metadata.txt"
echo "Collector: $(whoami)@$(hostname)" >> "${EVIDENCE_DIR}/collection-metadata.txt"
echo "Kernel: $(uname -a)" >> "${EVIDENCE_DIR}/collection-metadata.txt"
```

---

## 11. Advanced supply chain attack patterns

### 11.1 Typosquatting and dependency confusion — detection and prevention at scale

Typosquatting exploits human error in package name entry (e.g., `reqeusts` instead of `requests`). Dependency confusion exploits package manager resolution logic — when a private package name collides with a public registry package, some managers prefer the public (higher-versioned) package. Both are commodity attacks with automated tooling available to adversaries.

**Detection at the registry level.**

```bash
# Scan for typosquats of critical internal packages using typofinder heuristics
# Levenshtein distance, character swaps, homoglyphs, prefix/suffix mutations

# npm: check for packages similar to internal names on the public registry
for pkg in $(cat internal-package-names.txt); do
  # Check common typosquat variants
  for variant in $(python3 -c "
import itertools, sys
name = '${pkg}'
variants = set()
# character deletion
for i in range(len(name)):
    variants.add(name[:i] + name[i+1:])
# adjacent transposition
for i in range(len(name)-1):
    variants.add(name[:i] + name[i+1] + name[i] + name[i+2:])
# common substitutions
subs = {'a':'@','e':'3','i':'1','o':'0','l':'1','s':'5'}
for i,c in enumerate(name):
    if c in subs:
        variants.add(name[:i] + subs[c] + name[i+1:])
for v in sorted(variants):
    print(v)
"); do
    npm view "${variant}" version 2>/dev/null && \
      echo "WARNING: typosquat candidate '${variant}' exists on npm (original: ${pkg})"
  done
done

# pip: check PyPI for dependency confusion candidates
# Internal packages that also exist on PyPI with higher versions
pip index versions internal-pkg-name 2>/dev/null && \
  echo "ALERT: internal package name exists on public PyPI"
```

**Prevention — scoped registries and namespace reservation.**

```bash
# npm: configure scoped registry to prevent confusion
# .npmrc — route @corp scope to internal registry, everything else to npm
cat > .npmrc << 'NPMRC'
@corp:registry=https://npm.internal.corp/
//npm.internal.corp/:_authToken=${NPM_INTERNAL_TOKEN}
registry=https://registry.npmjs.org/
NPMRC

# pip: configure index-url to internal-only, extra-index-url to PyPI
# pip.conf (or pip.ini on Windows)
cat > pip.conf << 'PIPCONF'
[global]
index-url = https://pypi.internal.corp/simple/
extra-index-url = https://pypi.org/simple/
trusted-host = pypi.internal.corp
PIPCONF
# WARNING: with extra-index-url, pip may still prefer the higher public version.
# For strict isolation, use ONLY index-url pointing to a proxy that caches PyPI
# and blocks name collisions.
```

**OPA/Rego policy — block installation of packages not in the allow-list.**

```rego
# dependency_confusion_prevention.rego
package supply_chain.dependency_confusion

import future.keywords.in

# Internal package namespaces
internal_namespaces := {"@corp", "@internal", "corp-"}

# Deny installation of packages from public registries if they match internal namespace patterns
deny[msg] {
    some pkg in input.requested_packages
    some ns in internal_namespaces
    startswith(pkg.name, ns)
    pkg.source == "public"
    msg := sprintf("BLOCKED: Package '%s' matches internal namespace '%s' but resolves from public registry", [pkg.name, ns])
}

# Deny installation of any package not in the approved dependency list
deny[msg] {
    some pkg in input.requested_packages
    not pkg.name in data.approved_dependencies
    msg := sprintf("BLOCKED: Package '%s@%s' not in approved dependency list", [pkg.name, pkg.version])
}
```

### 11.2 Compromised maintainer accounts — indicators and response

Maintainer account takeover is the most direct supply chain attack vector — it bypasses code review, signature verification, and CI/CD controls because the attacker operates with legitimate credentials. Indicators include:

- Sudden publishing of new versions after months/years of inactivity
- Releases that do not correspond to tagged commits in the source repository
- Changes to package metadata (repository URL, maintainer email) immediately before a release
- Addition of install scripts or native binaries to previously pure-script packages
- Removal of test suites or CI configurations in the compromising commit

**Sigma rule — detect suspicious package publication patterns.**

```yaml
title: Suspicious Package Registry Publication Pattern
id: a3b4c5d6-7e8f-9a0b-1c2d-3e4f5a6b7c8d
status: experimental
description: >
  Detects package publications that exhibit indicators consistent with
  maintainer account compromise: publication after long dormancy, missing
  source repository tags, or metadata changes preceding the release.
date: 2025-06-15
author: Supply Chain Security Team
references:
  - https://blog.phylum.io/compromised-maintainer-accounts
  - https://socket.dev/blog/supply-chain-attack-patterns
logsource:
  category: application
  product: package_registry
detection:
  selection_dormancy:
    event_type: "package_publish"
    days_since_last_publish|gte: 180
  selection_no_tag:
    event_type: "package_publish"
    source_repo_tag_exists: false
  selection_metadata_change:
    event_type: "package_metadata_update"
    fields_changed|contains:
      - "repository_url"
      - "maintainer_email"
    time_before_publish|lte: "48h"
  condition: selection_dormancy or selection_no_tag or selection_metadata_change
level: high
tags:
  - attack.initial_access
  - attack.t1195.002
```

### 11.3 Build environment poisoning via shared CI runners

Shared CI runners (GitHub Actions public runners, GitLab shared runners, self-hosted pools serving multiple tenants) create a lateral attack surface. A malicious job on one repository can poison the runner environment for subsequent jobs from other repositories. Attack vectors include: modifying system-wide tool caches (`/opt/hostedtoolcache/`), installing rootkits or LD_PRELOAD hooks, modifying DNS resolution (`/etc/hosts`, `/etc/resolv.conf`), and persisting malicious code in runner workspace directories that are not fully cleaned between jobs.

**Mitigation: ephemeral runners with verified base images.**

```yaml
# GitHub Actions: self-hosted runner with ephemeral mode
# actions-runner-controller (ARC) configuration for Kubernetes
apiVersion: actions.summerwind.dev/v1alpha1
kind: RunnerDeployment
metadata:
  name: ephemeral-runners
spec:
  replicas: 5
  template:
    spec:
      ephemeral: true  # Runner is destroyed after each job
      dockerEnabled: false  # No Docker-in-Docker (reduces attack surface)
      image: ghcr.io/org/hardened-runner:sha256-abc123  # Pinned by digest
      resources:
        limits:
          cpu: "4"
          memory: "8Gi"
        requests:
          cpu: "2"
          memory: "4Gi"
      env:
        - name: ACTIONS_RUNNER_REQUIRE_JOB_CONTAINER
          value: "true"  # Force all steps to run in containers
```

### 11.4 Container base image supply chain attacks

Container base images are high-value supply chain targets — a compromise in `python:3.12-slim` or `node:20-alpine` propagates to millions of downstream images. Attack vectors include: compromised Docker Hub accounts publishing malicious tags, tag mutation (repointing `latest` or version tags to compromised digests), and build infrastructure compromise of the official image build pipeline.

```bash
# Always pin container images by digest, never by tag
# BAD: tag can be repointed to compromised image
FROM python:3.12-slim

# GOOD: digest is content-addressed and immutable
FROM python:3.12-slim@sha256:f5a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1

# Verify base image provenance with cosign
cosign verify \
  --certificate-identity-regexp ".*docker-library.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  docker.io/library/python:3.12-slim@sha256:f5a1b2c3d4...

# Use crane to inspect image manifests before pulling
crane manifest docker.io/library/python:3.12-slim | jq '.config.digest'

# Scan base image for vulnerabilities before building
trivy image --severity HIGH,CRITICAL --exit-code 1 \
  python:3.12-slim@sha256:f5a1b2c3d4...

# Dockerfile best practice: multi-stage build with distroless final image
FROM python:3.12-slim@sha256:f5a1b2c3d4... AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
COPY . .

FROM gcr.io/distroless/python3-debian12@sha256:a1b2c3d4e5... AS runtime
COPY --from=builder /install /usr/local
COPY --from=builder /app /app
WORKDIR /app
ENTRYPOINT ["python", "main.py"]
```

### 11.5 ML model supply chain attacks

Machine learning model artifacts introduce unique supply chain risks distinct from traditional software dependencies. The primary vectors are:

**Pickle deserialization attacks.** Python's `pickle` module can execute arbitrary code during deserialization. PyTorch models (`.pt`, `.pth`), scikit-learn models (`.pkl`), and many other ML frameworks store models as pickle files. A poisoned model file downloaded from Hugging Face Hub, PyTorch Hub, or any model registry can execute arbitrary code when loaded with `torch.load()` or `pickle.load()`.

**YARA rule — detect malicious pickle payloads in model files.**

```yara
rule ML_Malicious_Pickle_Payload
{
    meta:
        description = "Detects pickle opcodes commonly used in malicious ML model files"
        author = "Supply Chain Security Team"
        date = "2025-06-15"
        severity = "critical"
        reference = "https://blog.trailofbits.com/2022/10/17/pickling-python/"
        mitre_attack = "T1195.002"

    strings:
        // pickle opcode sequences indicating code execution
        $reduce = { 63 }          // GLOBAL opcode - imports module
        $os_system = "os\nsystem" ascii
        $os_popen = "os\npopen" ascii
        $subprocess = "subprocess\ncall" ascii
        $subprocess_popen = "subprocess\nPopen" ascii
        $exec_builtin = "builtins\nexec" ascii
        $eval_builtin = "builtins\neval" ascii
        $nt_system = "nt\nsystem" ascii
        $posix_system = "posix\nsystem" ascii
        $importlib = "importlib\nimport_module" ascii
        $webbrowser = "webbrowser\nopen" ascii
        $ctypes_cdll = "ctypes\nCDLL" ascii
        $socket_connect = "socket\nsocket" ascii

        // PyTorch ZIP container magic + pickle inside
        $pytorch_zip = { 50 4B 03 04 }
        $pytorch_data = "archive/data.pkl" ascii

    condition:
        ($reduce and any of ($os_system, $os_popen, $subprocess, $subprocess_popen,
         $exec_builtin, $eval_builtin, $nt_system, $posix_system, $importlib,
         $webbrowser, $ctypes_cdll, $socket_connect))
        or
        ($pytorch_zip and $pytorch_data and any of ($os_system, $os_popen,
         $subprocess, $exec_builtin, $eval_builtin))
}
```

**Safe model loading practices.**

```python
# UNSAFE: torch.load() uses pickle by default — arbitrary code execution
# model = torch.load("model.pt")  # NEVER do this with untrusted models

# SAFE: PyTorch 2.6+ supports weights_only=True (default since 2.6)
import torch
model = torch.load("model.pt", weights_only=True)

# SAFE: Use safetensors format (no code execution possible)
from safetensors.torch import load_file
state_dict = load_file("model.safetensors")

# SAFE: Use Hugging Face with trust_remote_code=False (default)
from transformers import AutoModel
model = AutoModel.from_pretrained("org/model", trust_remote_code=False)

# Scan model files before loading
# pip install fickling (Trail of Bits pickle scanner)
fickling --check-safety model.pt
# fickling --trace model.pt  # trace all pickle operations without executing
```

### 11.6 Firmware supply chain — UEFI implants via vendor compromise

Firmware supply chain attacks represent the most persistent threat vector because firmware executes before the operating system, below the visibility of most security tools. Notable incidents include the 2018 ASUS Live Update compromise (ShadowHammer — attacker-signed UEFI updates via compromised ASUS build servers), the 2022 CosmicStrand UEFI rootkit (modified firmware images distributed via motherboard supply chain), and the BlackLotus UEFI bootkit (CVE-2022-21894, exploiting Secure Boot bypass to persist in the EFI System Partition).

Firmware integrity verification relies on: Secure Boot certificate chain validation (Platform Key → Key Exchange Key → db/dbx), measured boot with TPM PCR attestation (Domain 17D §3), and vendor-specific firmware update signing verification. The supply chain attack surface includes: compromised vendor build infrastructure (the vendor's signing key signs the malicious update), compromised UEFI/BIOS update mechanisms (malicious updates delivered via vendor websites or update utilities), and physical supply chain interdiction (pre-installed implants on hardware during manufacturing or shipping — documented in NSA ANT catalog, though most known instances involve aftermarket modification rather than factory insertion).

---

## 12. Supply chain compliance and governance

### 12.1 Executive Order 14028 requirements

Executive Order 14028 ("Improving the Nation's Cybersecurity," signed 2021-05-12) established mandatory software supply chain security requirements for federal government software procurement. Key provisions affecting supply chain:

- **Section 4(e):** Agencies must obtain SBOMs for all software purchased or used. The SBOM must conform to NTIA minimum elements (supplier name, component name, version, unique identifier, dependency relationship, author, timestamp).
- **Section 4(e)(vi):** Software producers must attest to conformity with NIST secure software development practices (codified as NIST SP 800-218 SSDF).
- **Section 4(e)(x):** Software producers must maintain provenance data for all code and components.
- **OMB M-22-18 / M-23-16:** Implementation memoranda requiring self-attestation forms (common form) for all critical software vendors to the federal government.

### 12.2 NIST SSDF (Secure Software Development Framework) SP 800-218

NIST SP 800-218 defines practices organized into four groups, with specific supply chain relevance:

| Practice Group | ID | Supply Chain Relevance |
|---------------|-----|----------------------|
| Prepare the Organization (PO) | PO.1.1 | Define security requirements for third-party components |
| Prepare the Organization | PO.3.1 | Specify security criteria for third-party components |
| Prepare the Organization | PO.3.2 | Communicate security requirements to suppliers |
| Protect the Software (PS) | PS.1.1 | Protect all forms of code from unauthorized access/tampering |
| Protect the Software | PS.2.1 | Verify third-party components meet security requirements |
| Protect the Software | PS.3.1 | Archive and protect each software release |
| Produce Well-Secured Software (PW) | PW.4.1 | Review and analyze human-readable code for vulnerabilities |
| Produce Well-Secured Software | PW.4.4 | Verify code integrity and provenance |
| Respond to Vulnerabilities (RV) | RV.1.1 | Process to receive vulnerability reports (including in dependencies) |
| Respond to Vulnerabilities | RV.1.3 | Analyze each vulnerability to determine root cause and affected components |

**SSDF attestation verification — automated check.**

```bash
# Verify that a vendor's SSDF attestation form covers required practices
# Example: parsing the OMB common self-attestation form

# Check that the attestation is signed and current
gpg --verify vendor-attestation.sig vendor-attestation.pdf

# Automated SSDF control mapping check (custom script example)
cat << 'SSDF_CHECK' > verify_ssdf_controls.py
#!/usr/bin/env python3
"""Verify SSDF attestation covers minimum required controls."""

REQUIRED_CONTROLS = {
    "PO.1.1": "Security requirements for third-party components defined",
    "PS.1.1": "Code protected from unauthorized access and tampering",
    "PS.2.1": "Third-party component verification",
    "PW.4.4": "Code integrity and provenance verification",
    "RV.1.1": "Vulnerability report ingestion process exists",
}

def verify_attestation(attestation_data: dict) -> list[str]:
    """Return list of missing controls."""
    attested = set(attestation_data.get("controls_implemented", []))
    missing = []
    for control_id, description in REQUIRED_CONTROLS.items():
        if control_id not in attested:
            missing.append(f"MISSING: {control_id} — {description}")
    return missing
SSDF_CHECK
```

### 12.3 EU Cyber Resilience Act supply chain provisions

The EU Cyber Resilience Act (CRA, adopted 2024, enforcement begins 2027) imposes supply chain security obligations on manufacturers of products with digital elements sold in the EU:

- **Article 13(5):** Manufacturers must exercise due diligence when integrating third-party components, including open-source components, ensuring they do not compromise product security.
- **Article 13(6):** Manufacturers must identify and document vulnerabilities in components, including dependencies, and provide an SBOM (minimum: top-level dependencies).
- **Annex I, Part II, §2:** Technical documentation must include "information on the software bill of materials, in a commonly used and machine-readable format covering at the very least the top-level dependencies of the products."
- **Article 14:** Reporting obligations — manufacturers must notify ENISA of actively exploited vulnerabilities within 24 hours (early warning), with full details within 72 hours.
- **Open-source steward provisions:** The CRA creates a special category for open-source software "stewards" (organizations that systematically support open-source projects). Stewards have lighter obligations (no conformity assessment) but must have a cybersecurity policy, cooperate with market surveillance authorities, and facilitate vulnerability handling.

### 12.4 FedRAMP supply chain risk management

FedRAMP Rev. 5 (aligned with NIST SP 800-53 Rev. 5) includes specific supply chain risk management controls:

- **SR-2 Supply Chain Risk Management Plan:** CSPs must develop, document, and implement a supply chain risk management plan.
- **SR-3 Supply Chain Controls and Processes:** CSPs must employ supply chain controls including provenance verification, component authenticity validation, and periodic assessment of suppliers.
- **SR-4 Provenance:** CSPs must document, monitor, and maintain provenance of systems, components, and services.
- **SR-5 Acquisition Strategies:** CSPs must employ acquisition strategies that limit supply chain risk.
- **SR-11 Component Authenticity:** CSPs must develop and implement anti-counterfeit policies and procedures for components.

### 12.5 SLSA compliance verification automation

SLSA (Supply-chain Levels for Software Artifacts) defines four levels of increasing supply chain security. Automating SLSA compliance verification requires checking provenance attestations against the SLSA specification.

```bash
# Install SLSA verifier
go install github.com/slsa-framework/slsa-verifier/v2/cli/slsa-verifier@v2.6.0

# Verify SLSA provenance for a binary artifact
slsa-verifier verify-artifact \
  ./artifact-linux-amd64 \
  --provenance-path ./artifact-linux-amd64.intoto.jsonl \
  --source-uri github.com/org/repo \
  --source-tag v1.0.0

# Verify SLSA provenance for a container image
slsa-verifier verify-image \
  ghcr.io/org/app@sha256:abc123... \
  --source-uri github.com/org/repo \
  --source-tag v1.0.0

# Verify SLSA Build Level 3 requirements programmatically
# Build L3 requires: hermetic, reproducible, parameterless build
# Check provenance for required fields
cat provenance.intoto.jsonl | jq -r '.payload' | base64 -d | jq '
  {
    builder_id: .predicate.builder.id,
    build_type: .predicate.buildType,
    source_uri: .predicate.invocation.configSource.uri,
    source_digest: .predicate.invocation.configSource.digest,
    hermetic: .predicate.metadata.buildInvocationID,
    reproducible: .predicate.metadata.reproducible,
    parameters: (.predicate.invocation.parameters // {}),
    materials: [.predicate.materials[] | {uri, digest}]
  }
'

# Policy check: reject artifacts below SLSA Build Level 2
cat << 'SLSA_POLICY' > slsa_policy_check.rego
package slsa.policy

import future.keywords.in

minimum_slsa_level := 2

# Extract SLSA level from provenance builder ID
slsa_level(builder_id) = 3 {
    contains(builder_id, "slsa-framework/slsa-github-generator")
}
slsa_level(builder_id) = 2 {
    contains(builder_id, "github.com/actions/runner")
    not contains(builder_id, "slsa-framework")
}
slsa_level(builder_id) = 1 {
    not slsa_level_gte_2(builder_id)
}

deny[msg] {
    level := slsa_level(input.provenance.builder.id)
    level < minimum_slsa_level
    msg := sprintf("Artifact SLSA level %d is below minimum required level %d", [level, minimum_slsa_level])
}

deny[msg] {
    not input.provenance.builder.id
    msg := "Artifact has no SLSA provenance — cannot verify supply chain integrity"
}
SLSA_POLICY
```

### 12.6 Third-party vendor security assessment frameworks

Organizations consuming third-party software need structured assessment of their vendors' supply chain security posture. The key frameworks are:

- **OpenSSF Scorecard:** Automated assessment of open-source project security practices (branch protection, CI tests, dependency updates, signed releases). Score of 0-10 across 18+ checks.
- **CAIQ (Consensus Assessments Initiative Questionnaire) v4:** CSA questionnaire for cloud service provider security assessments, including supply chain questions (STA-01 through STA-09).
- **SIG (Standardized Information Gathering) Questionnaire:** Shared Assessments program standard for third-party risk assessment.
- **NIST C-SCRM (Cyber Supply Chain Risk Management):** NIST SP 800-161 Rev. 1 provides practices for identifying, assessing, and mitigating supply chain risks.

```bash
# Run OpenSSF Scorecard against a dependency's repository
# Install: go install github.com/ossf/scorecard/v5/cmd/scorecard@latest
scorecard --repo=github.com/org/dependency \
  --format=json \
  --show-details \
  > scorecard-report.json

# Check specific supply chain-relevant checks
jq '.checks[] | select(.name == "Branch-Protection" or
  .name == "Signed-Releases" or
  .name == "Token-Permissions" or
  .name == "Pinned-Dependencies" or
  .name == "SAST" or
  .name == "Vulnerabilities") |
  {name, score, reason}' scorecard-report.json

# Batch Scorecard assessment of all direct dependencies
cat go.sum | awk '/github\.com/{print $1}' | sort -u | while read mod; do
  repo=$(echo "$mod" | sed 's|/v[0-9]*$||')
  echo "Scoring: ${repo}"
  scorecard --repo="https://${repo}" --format=json 2>/dev/null | \
    jq '{repo: .repo.name, score: .score}' 2>/dev/null
done > dependency-scorecard-results.jsonl
```

---

## 13. Supply chain security automation

### 13.1 Policy-as-code for dependency governance

Policy-as-code defines dependency governance rules as machine-executable policies, enforced automatically in CI/CD pipelines rather than relying on manual review.

**OPA/Rego — comprehensive dependency governance policy.**

```rego
# dependency_governance.rego
package supply_chain.governance

import future.keywords.in
import future.keywords.if

# Maximum age for dependencies (days since last release)
max_dependency_age_days := 730  # 2 years

# Minimum OpenSSF Scorecard score for critical dependencies
min_scorecard_score := 5

# Blocked licenses (copyleft in proprietary context)
blocked_licenses := {"AGPL-3.0", "AGPL-3.0-only", "AGPL-3.0-or-later", "SSPL-1.0", "EUPL-1.2"}

# Deny dependencies with known critical vulnerabilities
deny[msg] {
    some dep in input.dependencies
    some vuln in dep.vulnerabilities
    vuln.severity == "CRITICAL"
    not vuln.vex_status == "not_affected"
    not vuln.vex_status == "false_positive"
    msg := sprintf("CRITICAL vuln %s in %s@%s: %s", [vuln.id, dep.name, dep.version, vuln.summary])
}

# Deny dependencies with blocked licenses
deny[msg] {
    some dep in input.dependencies
    some license in dep.licenses
    license in blocked_licenses
    msg := sprintf("Blocked license '%s' in %s@%s", [license, dep.name, dep.version])
}

# Warn on stale dependencies
warn[msg] {
    some dep in input.dependencies
    dep.days_since_last_release > max_dependency_age_days
    msg := sprintf("Stale dependency: %s@%s (last release %d days ago)", [dep.name, dep.version, dep.days_since_last_release])
}

# Warn on low Scorecard scores for direct dependencies
warn[msg] {
    some dep in input.dependencies
    dep.direct == true
    dep.scorecard_score < min_scorecard_score
    msg := sprintf("Low Scorecard score (%d/10) for %s", [dep.scorecard_score, dep.name])
}

# Deny new dependencies that are not in the pre-approved list (for high-security projects)
deny[msg] {
    some dep in input.new_dependencies
    not dep.name in data.pre_approved_packages
    msg := sprintf("New dependency '%s' requires security review before adoption", [dep.name])
}

# Deny dependencies without provenance attestation (SLSA requirement)
deny[msg] {
    some dep in input.dependencies
    dep.direct == true
    not dep.has_provenance
    dep.provenance_required == true
    msg := sprintf("Dependency %s@%s lacks SLSA provenance attestation", [dep.name, dep.version])
}
```

**CI/CD integration — evaluate policy on every PR.**

```yaml
# .github/workflows/dependency-policy.yml
name: Dependency Governance
on:
  pull_request:
    paths:
      - 'package-lock.json'
      - 'yarn.lock'
      - 'go.sum'
      - 'Cargo.lock'
      - 'requirements*.txt'
      - 'poetry.lock'

jobs:
  policy-check:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Generate dependency metadata
        run: |
          # Generate SBOM with vulnerability and license data
          syft . -o cyclonedx-json > sbom.json
          grype sbom:sbom.json -o json > vulns.json
          # Merge into policy input format
          python3 scripts/merge_dep_metadata.py \
            --sbom sbom.json \
            --vulns vulns.json \
            --scorecard-cache .scorecard-cache.json \
            --output policy-input.json
      - name: Evaluate dependency policy
        uses: open-policy-agent/opa-github-action@main
        with:
          policy: policies/dependency_governance.rego
          input: policy-input.json
          decision: supply_chain.governance
      - name: Post results to PR
        if: failure()
        uses: actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea  # v7.0.1
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('opa-results.json'));
            const denials = results.deny || [];
            const warnings = results.warn || [];
            let body = '## Dependency Policy Results\n\n';
            if (denials.length > 0) {
              body += '### Blocked\n' + denials.map(d => `- ${d}`).join('\n') + '\n\n';
            }
            if (warnings.length > 0) {
              body += '### Warnings\n' + warnings.map(w => `- ${w}`).join('\n') + '\n\n';
            }
            github.rest.issues.createComment({
              owner: context.repo.owner, repo: context.repo.repo,
              issue_number: context.issue.number, body
            });
```

### 13.2 Automated SBOM generation in CI/CD

SBOM generation must be integrated into the build pipeline, not performed as a manual post-hoc exercise. The SBOM should be generated at build time (capturing the actual resolved dependencies), signed, and published alongside the build artifacts.

```bash
# syft — generate CycloneDX SBOM from source directory
syft dir:. -o cyclonedx-json@1.5 > sbom-cyclonedx.json

# syft — generate SBOM from container image (most accurate for deployed artifacts)
syft ghcr.io/org/app@sha256:abc123... -o spdx-json > sbom-spdx.json

# cdxgen — CycloneDX generator with deep language ecosystem support
# Supports: npm, pip, Go, Maven, Gradle, Cargo, NuGet, Composer, etc.
cdxgen -o sbom.json -t node .      # Node.js project
cdxgen -o sbom.json -t python .    # Python project
cdxgen -o sbom.json -t go .        # Go project
cdxgen -o sbom.json -t java .      # Java/Maven project

# trivy — SBOM generation with integrated vulnerability scanning
trivy fs --format cyclonedx --output sbom-trivy.json .
trivy image --format spdx-json --output sbom-image.json ghcr.io/org/app:v1.0.0

# Sign the SBOM with cosign (attest it to the container image)
cosign attest \
  --predicate sbom-cyclonedx.json \
  --type cyclonedx \
  ghcr.io/org/app@sha256:abc123...

# Verify the SBOM attestation
cosign verify-attestation \
  --type cyclonedx \
  --certificate-identity "https://github.com/org/repo/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/org/app@sha256:abc123...
```

**CI/CD pipeline integration — SBOM as build artifact.**

```yaml
# .github/workflows/build-and-sbom.yml (excerpt)
  sbom:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
      id-token: write  # Required for keyless signing
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683  # v4.2.2
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: ghcr.io/org/app@${{ needs.build.outputs.digest }}
          format: cyclonedx-json
          output-file: sbom.cdx.json
      - name: Attest SBOM to image
        run: |
          cosign attest \
            --predicate sbom.cdx.json \
            --type cyclonedx \
            --yes \
            ghcr.io/org/app@${{ needs.build.outputs.digest }}
      - name: Upload SBOM to Dependency-Track
        run: |
          curl -X POST "https://deptrack.internal.corp/api/v1/bom" \
            -H "X-Api-Key: ${{ secrets.DEPTRACK_API_KEY }}" \
            -H "Content-Type: multipart/form-data" \
            -F "autoCreate=true" \
            -F "projectName=org-app" \
            -F "projectVersion=${{ github.ref_name }}" \
            -F "bom=@sbom.cdx.json"
```

### 13.3 Dependency update automation with security gates

Automated dependency updates (Renovate, Dependabot) reduce the window of exposure to known vulnerabilities, but unconstrained automation can introduce untested changes. Security gates ensure that automated updates pass policy checks before merging.

**Renovate configuration with security-prioritized policies.**

```json5
// renovate.json5
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    "security:openssf-scorecard",
    ":dependencyDashboard"
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"],
    "assignees": ["security-team"],
    // Security patches auto-merge if tests pass and patch-level only
    "automerge": true,
    "automergeType": "pr",
    "automergeStrategy": "squash"
  },
  "packageRules": [
    {
      // Critical security updates: auto-merge patch versions
      "matchUpdateTypes": ["patch"],
      "matchCategories": ["security"],
      "automerge": true,
      "automergeType": "pr",
      "automergeStrategy": "squash",
      "schedule": ["at any time"],
      "prPriority": 10
    },
    {
      // Non-security patch updates: weekly batching
      "matchUpdateTypes": ["patch"],
      "excludeCategories": ["security"],
      "automerge": true,
      "schedule": ["before 6am on Monday"],
      "groupName": "non-security patches"
    },
    {
      // Minor updates: require manual review
      "matchUpdateTypes": ["minor"],
      "automerge": false,
      "schedule": ["before 6am on Monday"],
      "prPriority": 5
    },
    {
      // Major updates: require security review label
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "labels": ["major-update", "needs-security-review"],
      "prPriority": 1
    },
    {
      // Pin all GitHub Actions by SHA digest
      "matchManagers": ["github-actions"],
      "pinDigests": true
    },
    {
      // Block deprecated packages
      "matchDepPatterns": ["*"],
      "matchPackageStatuses": ["deprecated"],
      "enabled": false
    }
  ],
  "postUpdateOptions": [
    "npmDedupe",
    "gomodTidy"
  ]
}
```

### 13.4 Provenance verification automation

Provenance verification should be automated in admission controllers and CI/CD gates, not performed manually.

```bash
# slsa-verifier: verify SLSA provenance for downloaded artifacts
slsa-verifier verify-artifact \
  ./downloaded-binary \
  --provenance-path ./downloaded-binary.intoto.jsonl \
  --source-uri github.com/org/repo \
  --source-tag v2.0.0 \
  --print-provenance  # Output full provenance for audit trail

# cosign verify-attestation: verify in-toto attestations on container images
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp "https://github.com/slsa-framework/slsa-github-generator/.*" \
  --certificate-oidc-issuer "https://token.actions.githubusercontent.com" \
  ghcr.io/org/app@sha256:abc123...

# Kubernetes admission policy: reject images without verified provenance
# Using Kyverno policy engine
cat << 'KYVERNO' > require-slsa-provenance.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-slsa-provenance
  annotations:
    policies.kyverno.io/title: Require SLSA Provenance
    policies.kyverno.io/description: >
      Verifies that all container images have SLSA provenance attestations
      signed by trusted builders before admission to the cluster.
spec:
  validationFailureAction: Enforce
  background: false
  rules:
    - name: verify-slsa-provenance
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/org/*"
            - "registry.internal.corp/*"
          attestations:
            - type: "https://slsa.dev/provenance/v1"
              attestors:
                - entries:
                    - keyless:
                        issuer: "https://token.actions.githubusercontent.com"
                        subjectRegExp: "https://github.com/org/.*"
                        rekor:
                          url: "https://rekor.sigstore.dev"
              conditions:
                - all:
                    - key: "{{ builder.id }}"
                      operator: AnyIn
                      value:
                        - "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/*"
                        - "https://github.com/org/trusted-builder/.github/workflows/*"
KYVERNO

kubectl apply -f require-slsa-provenance.yaml
```

### 13.5 Supply chain security dashboards and metrics

Measuring supply chain security posture requires tracking metrics across dependency hygiene, build integrity, and vulnerability exposure.

**Key metrics to track:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| SBOM completeness | 100% of production services | Count of services with current SBOM / total services |
| Mean time to remediate critical dep vulns | < 72 hours | Time from CVE publication to patched deployment |
| Dependency freshness | < 6 months behind latest | Median age of direct dependencies vs. latest release |
| SLSA provenance coverage | 100% of production artifacts | Artifacts with verified provenance / total artifacts |
| Scorecard coverage | All direct OSS dependencies | Dependencies assessed / total direct OSS dependencies |
| Lock file drift | 0 | PRs with lock file changes not matching manifest changes |
| Unpinned dependency count | 0 in CI/CD workflows | Count of unpinned actions, base images, tool versions |

**Prometheus metrics for supply chain monitoring.**

```yaml
# prometheus-rules.yml — supply chain security alerts
groups:
  - name: supply_chain_security
    interval: 1h
    rules:
      - alert: CriticalDependencyVulnUnpatched
        expr: |
          supply_chain_vuln_age_hours{severity="critical"} > 72
        for: 1h
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Critical dependency vulnerability unpatched for >72h"
          description: >
            {{ $labels.project }}/{{ $labels.dependency }}@{{ $labels.version }}
            has critical vulnerability {{ $labels.cve_id }} unpatched for
            {{ $value | humanizeDuration }}.

      - alert: SBOMStale
        expr: |
          (time() - supply_chain_sbom_last_generated_timestamp) > 604800
        for: 1h
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "SBOM not regenerated in >7 days"
          description: >
            {{ $labels.project }} SBOM is {{ $value | humanizeDuration }} old.
            Regenerate to capture dependency changes.

      - alert: ProvenanceVerificationFailure
        expr: |
          rate(supply_chain_provenance_verification_failures_total[1h]) > 0
        for: 5m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Provenance verification failures detected"
          description: >
            {{ $value }} provenance verification failures in the last hour
            for {{ $labels.registry }}/{{ $labels.image }}.
```

### 13.6 Integration patterns for Artifactory/Nexus with policy enforcement

Artifact repository managers (JFrog Artifactory, Sonatype Nexus) serve as the chokepoint through which all dependencies flow. Enforcing supply chain policies at this layer catches violations before code reaches build systems.

**JFrog Artifactory — Xray policy configuration.**

```bash
# Create a security policy that blocks critical vulnerabilities
curl -X POST "https://artifactory.internal.corp/xray/api/v2/policies" \
  -H "Authorization: Bearer ${ARTIFACTORY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "block-critical-vulns",
    "description": "Block artifacts with critical/high CVEs from download",
    "type": "security",
    "rules": [
      {
        "name": "critical-cve-block",
        "priority": 1,
        "criteria": {
          "min_severity": "Critical",
          "cvss_range": {"from": 9.0, "to": 10.0}
        },
        "actions": {
          "block_download": {"active": true, "unscanned": true},
          "fail_build": true,
          "notify_deployer": true,
          "notify_watch_recipients": true,
          "create_ticket": true
        }
      },
      {
        "name": "high-cve-warn",
        "priority": 2,
        "criteria": {
          "min_severity": "High",
          "cvss_range": {"from": 7.0, "to": 8.9}
        },
        "actions": {
          "block_download": {"active": false},
          "fail_build": false,
          "notify_deployer": true
        }
      }
    ]
  }'

# Create a license compliance policy
curl -X POST "https://artifactory.internal.corp/xray/api/v2/policies" \
  -H "Authorization: Bearer ${ARTIFACTORY_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "license-compliance",
    "description": "Block artifacts with prohibited licenses",
    "type": "license",
    "rules": [
      {
        "name": "block-copyleft",
        "priority": 1,
        "criteria": {
          "banned_licenses": [
            {"name": "AGPL-3.0"},
            {"name": "SSPL-1.0"},
            {"name": "EUPL-1.2"}
          ],
          "allow_unknown": false
        },
        "actions": {
          "block_download": {"active": true},
          "fail_build": true,
          "notify_deployer": true
        }
      }
    ]
  }'
```

**Sonatype Nexus — firewall rule for namespace protection.**

```bash
# Nexus Repository Firewall — block packages matching internal namespace from public proxy
# Configure via Nexus REST API

# Create a content selector for internal namespace pattern
curl -X POST "https://nexus.internal.corp/service/rest/v1/security/content-selectors" \
  -H "Authorization: Basic ${NEXUS_AUTH}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "internal-namespace-guard",
    "description": "Matches packages that should only come from internal registry",
    "expression": "format == \"npm\" and path =~ \"^/@corp/.*\""
  }'

# Create a routing rule to block internal namespace packages from public proxy
curl -X POST "https://nexus.internal.corp/service/rest/v1/routing-rules" \
  -H "Authorization: Basic ${NEXUS_AUTH}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "block-internal-from-public",
    "description": "Prevent dependency confusion by blocking internal namespace from public proxy",
    "mode": "BLOCK",
    "matchers": ["^/@corp/.*"]
  }'
```

These automation patterns — policy-as-code governance, SBOM generation in CI/CD, security-gated dependency updates, provenance verification at admission, metric-driven dashboards, and repository-level policy enforcement — form an integrated defense layer that shifts supply chain security from reactive manual review to proactive automated enforcement. The goal is not zero-touch (major updates and new dependencies should still receive human security review) but to automate the repeatable decisions so that human attention focuses on novel risk.

---

## 14. Cross-references

**To Domain 1 (binary formats).** The xz backdoor (§1) used IFUNC resolvers (Domain 1 Chapter 1B §2) — a dynamic linking feature — to intercept function resolution. Understanding ELF dynamic linking internals (GOT, PLT, IFUNC, `.gnu.hash`) is prerequisite to understanding how the xz injection mechanism worked at the binary level.

**To Domain 10 (cloud/container).** Container image signing with cosign (§5.2) integrates with Kubernetes admission controllers (Domain 10B §4). Container SBOM generation (§6.1) applies to container images deployed in cloud environments. OIDC-based authentication (§3.1, §5.3) relies on cloud provider identity federation mechanisms.

**To Domain 11 (malware/tradecraft).** SolarWinds SUNBURST (§2) used DNS C2 with DGA encoding and steganographic HTTP C2 (Domain 11A §5). The 3CX attack (§2.3) deployed modular backdoors. This chapter analyzes the supply chain compromise mechanics; Domain 11 analyzes the malware tradecraft from the implant perspective.

**To Domain 13 (cryptography).** Sigstore (§5) uses ECDSA/Ed25519 signatures, X.509 certificates (Fulcio), and Merkle trees (Rekor — built on Trillian). Code signing infrastructure (§8.2) relies on HSM-backed key management (Domain 13A §2). The xz backdoor's Ed448 authentication mechanism (§1.3) used a post-quantum-resistant elliptic curve signature scheme for attacker authentication.

**To Domain 14 (AD/Windows).** SolarWinds SUNBURST was the initial access vector for Golden SAML attacks against AD FS (Domain 14A §3). The post-compromise tradecraft — DCSync, SAML token forging, cloud persistence via OAuth application registration — represents the AD attack surface that the supply chain compromise enabled.

**To Domain 16 (ICS/OT).** PIPEDREAM's exploitation of the shared Codesys V3 runtime (Domain 16B §4.5) is a supply chain vulnerability — a single shared software component creating cross-vendor risk in industrial control systems. Havex used trojanized ICS vendor website downloads as the initial access vector.

**To Domain 17 (physical/hardware).** Hardware supply chain security (Domain 19C, Domain 17C §7) is the physical-layer complement to software supply chain security. HSM-backed code signing (§8.2) depends on hardware root of trust (Domain 17D §3). PCB-level anti-tamper mechanisms (Domain 17C §8) protect the hardware that runs signed software.

**To Domain 18 (adversarial ML).** ML model supply chain attacks (Domain 18A §4) mirror software supply chain attacks: poisoned pre-trained models on Hugging Face Hub, trojanized model weights, and malicious pickle deserialization in PyTorch model files. SBOM concepts extend to ML with "Model Cards" and "ML-BOM" proposals. The Sigstore signing model could be applied to model artifact signing (signing model weights with provenance binding to the training pipeline), though this is nascent as of 2025.

**To Domain 23 (social engineering).** The xz attack (§1.1) is fundamentally a social engineering operation — the technical payload was delivered through a two-year trust-building campaign. The sockpuppet accounts (Jigar Kumar, Dennis Ens) used social pressure tactics documented in Domain 23A §1. The 3CX compromise (§2.3) leveraged shadow IT — an employee installing unvetted software — which social engineering defenses (security awareness training, application whitelisting) would have mitigated.

**To Domain 27 (defensive architecture).** Supply chain security controls (SLSA, Sigstore, SBOM) are components of the defensive architecture described in Domain 27B. Detection of supply chain compromises (anomalous builds, unexpected dependencies, provenance verification failures) integrates with the detection engineering pipeline in Domain 27C. Zero-trust architecture (Domain 27B) should extend to the software supply chain — no build artifact is trusted without verified provenance.

---

## Exercises

### Exercise 19B.1 — xz Backdoor Forensic Triage

1. On a Debian Sid or Fedora Rawhide VM (or container), install xz-utils 5.4.x (known-good) and verify `xz --version` and `ldd $(which sshd) | grep lzma`.
2. Download the xz 5.6.1 source tarball (archived). Inspect `build-to-host.m4` — identify the obfuscated extraction commands (`head -c`, `tail -c`, `tr`, `xz -d`).
3. Compare the tarball contents against the git repository at the same tag using `diffoscope`. Document the files present in the tarball but absent from git (the injected test fixtures).
4. Write a YARA rule that detects the IFUNC resolver signature bytes and Ed448 public key fragment in compiled `liblzma.so` (use the patterns from the Binarly analysis).
5. Implement the Sigma rule from S1.7 detecting sshd reading `/proc/self/exe` and `/proc/self/maps` during library initialization. Test it with auditd.

**Deliverable:** diffoscope report, YARA rule, Sigma rule, and a written timeline (with UTC timestamps) of the xz attack from initial Jia Tan contribution (2021) through disclosure (2024-03-29).

### Exercise 19B.2 — SLSA Level 3 Provenance Pipeline

1. Fork a sample Go or Node.js project on GitHub.
2. Create a release workflow that builds the project and generates SLSA Level 3 provenance using `slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml`.
3. Tag a release and verify the generated provenance attestation: `slsa-verifier verify-artifact ./artifact --provenance-path ./provenance.intoto.jsonl --source-uri github.com/<your-fork>`.
4. Tamper with the artifact (modify one byte) and re-run verification. Confirm it fails.
5. Inspect the provenance JSON: extract builder identity, source commit, and build entry point. Verify the Rekor transparency log entry exists.

**Deliverable:** GitHub Actions workflow, provenance file, slsa-verifier output (pass and fail), and Rekor entry details.

### Exercise 19B.3 — Sigstore Container Signing and Kubernetes Admission

1. Build a container image and push to GHCR (or a local registry).
2. Sign the image with `cosign sign --yes <image>@<digest>` using keyless signing.
3. Verify the signature: `cosign verify --certificate-oidc-issuer <issuer> --certificate-identity <identity> <image>@<digest>`.
4. Deploy a Kyverno `ClusterPolicy` that enforces cosign signature verification for all pods in a `production` namespace.
5. Attempt to deploy an unsigned image to the `production` namespace. Confirm the admission controller rejects it.
6. Attach a CycloneDX SBOM attestation to the signed image with `cosign attest`. Verify with `cosign verify-attestation --type cyclonedx`.

**Deliverable:** cosign sign/verify output, Kyverno ClusterPolicy YAML, admission rejection log, and SBOM attestation verification output.

### Exercise 19B.4 — Reproducible Build Verification

1. Select a C/C++ project with autotools or CMake build system.
2. Build the project twice on the same system with different build paths (`/tmp/build-a/` and `/tmp/build-b/`), setting `SOURCE_DATE_EPOCH=$(git log -1 --format=%ct)`.
3. Compare the outputs with `diffoscope`. Identify and fix any sources of non-determinism (embedded paths, timestamps, archive ordering).
4. Apply fixes: `-fdebug-prefix-map`, `-fmacro-prefix-map`, `tar --sort=name`, and `ar D` flag.
5. Rebuild and confirm bit-for-bit identical output with `sha256sum`.

**Deliverable:** Initial diffoscope report showing non-determinism, applied fixes, final SHA-256 comparison showing identical hashes, and a list of non-determinism sources encountered.

### Exercise 19B.5 — SBOM Lifecycle Pipeline with VEX Triage

1. Build a multi-layer Docker image for a Python web application with 50+ transitive dependencies.
2. Generate a CycloneDX SBOM using Syft: `syft <image> -o cyclonedx-json > sbom.cdx.json`.
3. Scan with Grype: `grype sbom:sbom.cdx.json -o json > vulns.json`. Count critical/high/medium findings.
4. Write OpenVEX statements for 3 findings: one "not_affected" (with justification), one "affected" (with remediation action), one "under_investigation".
5. Re-scan with VEX applied: `grype sbom:sbom.cdx.json --vex vex.openvex.json`. Confirm the "not_affected" finding is suppressed.
6. Attach the SBOM to the container image via `cosign attach sbom`. Sign the SBOM attestation.

**Deliverable:** SBOM, vulnerability report, VEX document, Grype output with/without VEX, and cosign SBOM attestation.

---

## Readings and References

(retrieved: 2026-05-29)

### xz Backdoor (CVE-2024-3094)

- Andres Freund disclosure, oss-security mailing list, 2024-03-29. [https://www.openwall.com/lists/oss-security/2024/03/29/4](https://www.openwall.com/lists/oss-security/2024/03/29/4)
- NVD — CVE-2024-3094 (CVSS 10.0). [https://nvd.nist.gov/vuln/detail/CVE-2024-3094](https://nvd.nist.gov/vuln/detail/CVE-2024-3094)
- Binarly xz backdoor binary analysis. [https://www.binarly.io/posts/xz-backdoor-story-part-1](https://www.binarly.io/posts/xz-backdoor-story-part-1)

### SolarWinds SUNBURST

- CISA Emergency Directive 21-01. [https://www.cisa.gov/emergency-directive-21-01](https://www.cisa.gov/emergency-directive-21-01)
- CrowdStrike SUNSPOT analysis. [https://www.crowdstrike.com/blog/sunspot-malware-technical-analysis/](https://www.crowdstrike.com/blog/sunspot-malware-technical-analysis/)
- FireEye/Mandiant SUNBURST countermeasures. [https://github.com/mandiant/sunburst_countermeasures](https://github.com/mandiant/sunburst_countermeasures)

### SLSA and Sigstore

- SLSA v1.1 specification (v1.2 RC2, November 2025). [https://slsa.dev/spec/v1.0/](https://slsa.dev/spec/v1.0/)
- slsa-github-generator — SLSA Level 3 provenance for GitHub Actions. [https://github.com/slsa-framework/slsa-github-generator](https://github.com/slsa-framework/slsa-github-generator)
- Sigstore documentation — cosign, Fulcio, Rekor. [https://docs.sigstore.dev/](https://docs.sigstore.dev/)
- Rekor v2 GA announcement. [https://blog.sigstore.dev/rekor-v2-ga/](https://blog.sigstore.dev/rekor-v2-ga/)
- Tekton Chains — Kubernetes-native supply chain security. [https://tekton.dev/docs/chains/](https://tekton.dev/docs/chains/)

### SBOM and Compliance

- NIST SP 800-161 Rev. 1, Update 1 (November 2024). [https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final](https://csrc.nist.gov/pubs/sp/800/161/r1/upd1/final)
- EU Cyber Resilience Act (CRA) — SBOM and vulnerability disclosure requirements (adopted 2024, enforcement 2025-2027).
- OpenVEX specification. [https://openvex.dev/](https://openvex.dev/)
- Reproducible Builds project. [https://reproducible-builds.org/](https://reproducible-builds.org/)

### Tooling

- Syft (Anchore) — SBOM generation. [https://github.com/anchore/syft](https://github.com/anchore/syft)
- Grype (Anchore) — vulnerability scanning. [https://github.com/anchore/grype](https://github.com/anchore/grype)
- diffoscope — recursive format-aware binary comparison. [https://diffoscope.org/](https://diffoscope.org/)
- Kyverno — Kubernetes policy engine with native cosign verification. [https://kyverno.io/](https://kyverno.io/)
- Socket.dev — behavioral supply chain analysis. [https://socket.dev/](https://socket.dev/)
- cargo-vet (Mozilla) — Rust dependency audit tracking. [https://mozilla.github.io/cargo-vet/](https://mozilla.github.io/cargo-vet/)

---

## Cross-Reference Matrix

| Domain | Relationship | Key Sections |
|--------|-------------|--------------|
| Domain 1 — Binary Formats | xz IFUNC resolver hooking, GOT/PLT manipulation, ELF dynamic linking internals | S1.3, S1.5 |
| Domain 10 — Cloud/Container | Container image signing (cosign), Kubernetes admission controllers, OCI SBOM attachments | S5.2, S5.4, S6.1 |
| Domain 11 — Malware | SUNBURST DNS C2 with DGA, TEARDROP in-memory loader, 3CX DLL sideloading | S2.2, S2.3 |
| Domain 13 — Cryptography | Sigstore ECDSA/Ed25519 signatures, Fulcio X.509 certificates, Rekor Merkle trees, xz Ed448 authentication | S5.1, S1.3 |
| Domain 18 — Adversarial ML | ML model supply chain (pickle RCE, ModelHub poisoning), safetensors, ML-BOM proposals | S4.2 (via Domain 18 S8) |
| Domain 23 — Social Engineering | xz two-year social engineering campaign, sockpuppet accounts, maintainer burnout exploitation | S1.1 |

---

## Glossary

| Term | Definition |
|------|-----------|
| **IFUNC Resolver** | A GNU indirect function mechanism where the dynamic linker calls a resolver function at load time to determine which implementation of a symbol to use; exploited by the xz backdoor to intercept `RSA_public_decrypt` via GOT overwrite. |
| **Hermetic Build** | A build process with no network access and no access to undeclared files, ensuring output depends only on explicitly declared, hash-verified inputs. |
| **Fulcio** | Sigstore's ephemeral certificate authority that issues short-lived (10-minute) X.509 certificates bound to an OIDC identity, eliminating long-lived key management. |
| **Rekor** | Sigstore's append-only transparency log (Merkle tree) recording all signing events with tamper-evident, publicly auditable entries. Rekor v2 integrates witnessing directly. |
| **SLSA Provenance** | A signed in-toto attestation describing how an artifact was built: builder identity, source repository, commit, build command, and output digest. At Level 3, provenance is non-forgeable by the build script. |
| **Tekton Chains** | A Kubernetes-native component that automatically generates, signs, and stores in-toto attestations for Tekton pipeline runs, providing SLSA Level 2-3 provenance. |
| **VEX (Vulnerability Exploitability eXchange)** | A machine-readable statement declaring whether a vulnerability affects a specific product (not_affected, affected, fixed, under_investigation), enabling automated suppression of false positives. |
| **Reproducible Build** | A build producing bit-for-bit identical output from the same source and configuration, enabling independent verification. Requires eliminating timestamps, path embedding, and archive ordering non-determinism. |
| **Trusted Publisher** | A PyPI mechanism binding OIDC identity (GitHub Actions workflow) to package upload authorization, replacing long-lived API tokens with short-lived, scoped credentials. |
| **SOURCE_DATE_EPOCH** | A standardized environment variable (Reproducible Builds project) that build tools use instead of the current time, fixing timestamps in compiled artifacts for reproducibility. |
| **diffoscope** | A recursive, format-aware binary comparison tool that decomposes archives, ELF binaries, and other structured formats to identify exact sources of non-reproducibility. |
| **OpenSSF Scorecard** | An automated tool evaluating open-source projects across security heuristics (branch protection, signed releases, dangerous workflows), producing a 0-10 score usable for dependency risk assessment. |
| **PEP 761** | Python Enhancement Proposal (accepted 2024) extending PyPI with Sigstore-based attestations, enabling cryptographic provenance verification of Python packages. |
| **cargo-vet** | A Mozilla-developed Rust supply chain audit tool that tracks which crate versions have been code-reviewed by whom, adding a human review layer to dependency management. |
