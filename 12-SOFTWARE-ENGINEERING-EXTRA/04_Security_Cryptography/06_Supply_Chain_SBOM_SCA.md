# Module 4.5: Supply Chain Security — SBOM, SCA, SLSA, Signing & Provenance

> **Last updated:** 2026-05-22

## Guiding ideas

1. **SBOM (Software Bill of Materials): manifest of all dependencies.**
2. **SCA (Software Composition Analysis): scan SBOM for CVEs.**
3. **SLSA framework: supply-chain integrity levels.**
4. **CycloneDX + SPDX: standard SBOM formats.**
5. **Sigstore (cosign + Rekor): keyless signing + transparency log.**
6. **Reproducible builds: same source → same binary, verifiable.**
7. **Provenance attestation: who built what, from which source, in what environment.**
8. **Lock file integrity: tamper detection at the dependency resolution layer.**

---

## Table of Contents

1. [Why Supply Chain Security Matters](#1-why-supply-chain-security-matters)
2. [Attack Taxonomy](#2-attack-taxonomy)
3. [SBOM Fundamentals](#3-sbom-fundamentals)
4. [SBOM Formats: SPDX vs CycloneDX](#4-sbom-formats-spdx-vs-cyclonedx)
5. [SBOM Generation Tools](#5-sbom-generation-tools)
6. [Software Composition Analysis (SCA)](#6-software-composition-analysis-sca)
7. [SCA Tools Deep Dive](#7-sca-tools-deep-dive)
8. [SLSA Framework](#8-slsa-framework)
9. [Sigstore Ecosystem](#9-sigstore-ecosystem)
10. [Reproducible Builds](#10-reproducible-builds)
11. [Provenance Attestation](#11-provenance-attestation)
12. [Lock File Security](#12-lock-file-security)
13. [Typosquatting & Dependency Confusion](#13-typosquatting--dependency-confusion)
14. [CI/CD Integration Patterns](#14-cicd-integration-patterns)
15. [Container Supply Chain](#15-container-supply-chain)
16. [Policy Engines & Admission Control](#16-policy-engines--admission-control)
17. [Compliance & Regulatory Landscape](#17-compliance--regulatory-landscape)
18. [Incident Response for Supply Chain Attacks](#18-incident-response-for-supply-chain-attacks)
19. [Exercises](#19-exercises)
20. [References](#20-references)
21. [Glossary](#21-glossary)

---

## 1. Why Supply Chain Security Matters

Modern software is mostly assembled, not written. A typical Node.js application
pulls 800-1500 transitive dependencies. A Go binary vendoring a web framework
may include 200+ modules. Each of those is an attack surface.

High-profile incidents that reshaped the industry:

| Incident | Year | Impact |
|---|---|---|
| **SolarWinds (SUNBURST)** | 2020 | Build system compromised; trojanized updates to 18,000+ orgs including US government agencies |
| **Codecov bash uploader** | 2021 | CI script tampered; exfiltrated environment variables (tokens, keys) from thousands of repos |
| **ua-parser-js** | 2021 | npm maintainer account hijacked; cryptominer + credential stealer injected into package with 8M weekly downloads |
| **Log4Shell (CVE-2021-44228)** | 2021 | JNDI lookup in Log4j 2.x allowed RCE via crafted log messages. Affected virtually every Java shop |
| **colors / faker** | 2022 | Maintainer self-sabotaged packages to protest open-source exploitation. Broke thousands of CI pipelines |
| **xz-utils backdoor (CVE-2024-3094)** | 2024 | Multi-year social-engineering campaign planted backdoor in sshd via build-system manipulation |
| **tj-actions/changed-files** | 2025 | GitHub Action compromised, leaking CI secrets across repos using the action |

The xz-utils case is the canonical cautionary tale: a determined attacker spent
two years gaining maintainer trust, then inserted obfuscated payload into the
build system — not the source. The source code looked clean. Only the binary
was compromised. This is why build provenance and reproducible builds matter.

### 1.1 The Dependency Graph Problem

```
your-app
├── framework-x@3.2.1
│   ├── logger@1.0.0
│   │   └── string-utils@2.1.0    ← you never chose this
│   └── http-client@4.0.0
│       ├── tls-wrapper@1.2.3     ← who audited this?
│       └── url-parser@0.9.0      ← last updated 2019
└── auth-lib@2.0.0
    └── crypto-shim@0.4.0         ← 1 maintainer, no 2FA
```

You control your direct dependencies. You do not control their dependencies.
Transitive deps are where most supply chain attacks land because:

1. They are rarely audited by consumers.
2. They often have single-maintainer governance.
3. Version constraints may auto-upgrade them without review.

### 1.2 Defense in Depth Model

Supply chain security is not one tool — it is layered:

```
Layer 0: Source         → code review, signed commits, branch protection
Layer 1: Dependencies   → SBOM, SCA, lock files, typosquatting detection
Layer 2: Build          → hermetic builds, SLSA provenance, reproducibility
Layer 3: Distribution   → artifact signing (cosign), transparency logs (Rekor)
Layer 4: Deployment     → admission control (OPA/Kyverno), signature verification
Layer 5: Runtime        → SBOM-informed vulnerability scanning of running workloads
```

No single layer is sufficient. An attacker who compromises the build (Layer 2)
bypasses all dependency scanning (Layer 1). An attacker who substitutes an
artifact after build (between Layer 2 and 3) bypasses reproducibility checks.

---

## 2. Attack Taxonomy

### 2.1 Dependency Confusion / Substitution

Public registry serves a package with the same name as a private internal
package. Package managers that check public registries first (or at all) may
pull the attacker's version.

**Mechanism:**
```
Internal registry:  @company/utils  v1.0.0
Public npm:         @company/utils  v99.0.0   ← attacker publishes this

npm install → sees v99.0.0 on public > v1.0.0 on private → installs attacker's
```

**Mitigations:**
- Scope all internal packages under an org scope you own on the public registry.
- Configure `.npmrc` / `pip.conf` / `settings.xml` to restrict registries per scope.
- Use `--registry` flags in CI to pin the source.
- npm: set `@company:registry=https://internal.registry.example.com` in `.npmrc`.
- pip: use `--index-url` and `--extra-index-url` carefully; prefer `--index-url` only.

### 2.2 Typosquatting

Attacker publishes `co1ors` (digit one, not letter L) hoping someone mistypes
`colors`. The package runs a postinstall script that exfiltrates `.env`.

**Detection approaches:**
- Levenshtein distance analysis against popular package names.
- Registry-side defenses (npm/PyPI now flag suspicious name similarities).
- `socket.dev` — commercial service that flags typosquat candidates in PRs.
- Manual: always copy-paste package names from official docs, never type from memory.

### 2.3 Maintainer Account Takeover

Attacker compromises the npm/PyPI/crates.io account of a legitimate maintainer
(credential stuffing, phishing, SIM swap). Publishes a new patch version with
malicious code. Downstream consumers auto-upgrade.

**Mitigations:**
- Mandatory 2FA on registries (npm enforces for top-500 packages since 2022).
- Pin exact versions in lock files.
- Monitor for unexpected version bumps (Renovate/Dependabot show diffs).

### 2.4 Build System Compromise

Attacker modifies the build pipeline (CI config, build scripts, Makefiles) so
the built artifact differs from what the source would produce.

**Examples:**
- xz-utils: malicious `.m4` macro injected test fixture data into the binary.
- SolarWinds: build server itself was compromised; legitimate source produced
  trojanized binaries.

**Mitigations:**
- Hermetic builds (no network access during build).
- Reproducible builds (anyone can rebuild from source and get identical output).
- SLSA provenance (cryptographic attestation of build inputs/outputs).

### 2.5 Malicious Lifecycle Scripts

Package managers allow scripts to run during install:

| Ecosystem | Script hook | Example |
|---|---|---|
| npm | `preinstall`, `postinstall`, `prepare` | Crypto miners, env exfiltration |
| pip | `setup.py` execution | Arbitrary Python at install time |
| cargo | `build.rs` | Arbitrary Rust at compile time |
| Go | (none — compile only) | Safer by design |

**Mitigations:**
- npm: `--ignore-scripts` in CI, selectively allow via `.npmrc` `ignore-scripts=true` + per-package overrides.
- pip: prefer wheels over sdists (wheels don't run `setup.py`).
- Review `postinstall` scripts of new dependencies before adding them.

### 2.6 Protestware / Self-Sabotage

Maintainer intentionally breaks their own package. Not a vulnerability — a
supply chain integrity failure.

**Examples:** colors v1.4.1, faker v6.6.6 (infinite loop inserted).

**Mitigations:** Pin exact versions. Review changelogs before upgrading. Monitor
for maintainer behavior changes (large code deletions, license changes).

---

## 3. SBOM Fundamentals

An SBOM is a machine-readable inventory of every component in a software
artifact. Think of it as a nutritional label for software.

### 3.1 What Goes Into an SBOM

| Field | Description | Example |
|---|---|---|
| Component name | Package identifier | `lodash` |
| Version | Exact version string | `4.17.21` |
| Supplier | Who published it | `lodash team` |
| Package URL (purl) | Universal identifier | `pkg:npm/lodash@4.17.21` |
| License | SPDX license expression | `MIT` |
| Hashes | Integrity verification | `SHA-256: abc123...` |
| Dependencies | Transitive relationship graph | `lodash` depends on nothing |
| External references | Source repo, advisories | `https://github.com/lodash/lodash` |

### 3.2 SBOM Use Cases

1. **Vulnerability management:** When a new CVE drops, query your SBOM database:
   "which of our services use log4j-core < 2.17.1?" Answer in seconds, not days.

2. **License compliance:** Legal needs to know if any AGPL code is in the
   proprietary product. SBOM query answers this.

3. **Procurement / vendor risk:** Before buying SaaS, request their SBOM.
   Evaluate their dependency hygiene.

4. **Incident response:** "We just learned library X is backdoored. Which
   production systems are affected?" SBOM turns this from a week of grep into
   a database query.

5. **Regulatory compliance:** US Executive Order 14028 (May 2021) requires
   SBOMs for software sold to the US federal government. EU Cyber Resilience
   Act has similar requirements.

### 3.3 SBOM Lifecycle

```
Source Analysis ──→ Build-time SBOM ──→ Deploy-time Enrichment ──→ Runtime Monitoring
     │                    │                       │                        │
  Manifest-based    Binary analysis        Add deployment          Continuous
  (package.json,    + build metadata       context (env,          vulnerability
   go.sum, etc.)                           cluster, team)         correlation
```

**Source SBOM:** Generated from manifests. Knows what you declared, may miss
vendored or compiled-in dependencies.

**Build SBOM:** Generated during or after build. Captures what actually ended up
in the artifact. More accurate for compiled languages.

**Runtime SBOM:** Enriched with deployment context. Enables queries like "which
running pods in production-eu-west contain CVE-2024-XXXX?"

---

## 4. SBOM Formats: SPDX vs CycloneDX

### 4.1 SPDX (Software Package Data Exchange)

- **Origin:** Linux Foundation, ISO/IEC 5962:2021 international standard.
- **Focus:** License compliance (originated in legal/compliance community).
- **Formats:** JSON, XML, RDF, YAML, tag-value (plain text).
- **Versioning:** Current spec is SPDX 2.3; SPDX 3.0 (2024) adds security
  profile, build profile, AI/ML profile.
- **Strengths:** ISO standardized, broad tooling support, fine-grained license
  expression language.
- **Weaknesses:** Verbose, complex data model, historically weaker on
  vulnerability correlation.

SPDX 2.3 JSON snippet:

```json
{
  "spdxVersion": "SPDX-2.3",
  "dataLicense": "CC0-1.0",
  "SPDXID": "SPDXRef-DOCUMENT",
  "name": "my-app-sbom",
  "documentNamespace": "https://example.com/my-app-v1.0.0",
  "packages": [
    {
      "SPDXID": "SPDXRef-Package-lodash",
      "name": "lodash",
      "versionInfo": "4.17.21",
      "downloadLocation": "https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz",
      "licenseConcluded": "MIT",
      "licenseDeclared": "MIT",
      "externalRefs": [
        {
          "referenceCategory": "PACKAGE-MANAGER",
          "referenceType": "purl",
          "referenceLocator": "pkg:npm/lodash@4.17.21"
        }
      ],
      "checksums": [
        {
          "algorithm": "SHA256",
          "checksumValue": "2c5a0..."
        }
      ]
    }
  ],
  "relationships": [
    {
      "spdxElementId": "SPDXRef-DOCUMENT",
      "relationshipType": "DESCRIBES",
      "relatedSpdxElement": "SPDXRef-Package-lodash"
    }
  ]
}
```

### 4.2 CycloneDX

- **Origin:** OWASP, purpose-built for security.
- **Focus:** Vulnerability management, dependency tracking.
- **Formats:** JSON, XML, Protocol Buffers.
- **Versioning:** Current spec is CycloneDX 1.6 (2024). Supports BOM types:
  software, hardware, SaaSBOM, MLBOM, CBOM (crypto), operations.
- **Strengths:** Simpler data model, first-class vulnerability correlation
  (VEX — Vulnerability Exploitability eXchange), composability (BOM of BOMs).
- **Weaknesses:** Not ISO standardized (ECMA-424 standardization in progress),
  newer ecosystem.

CycloneDX 1.6 JSON snippet:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.6",
  "serialNumber": "urn:uuid:3e671687-395b-41f5-a30f-a58921a69b79",
  "version": 1,
  "metadata": {
    "timestamp": "2026-05-22T10:00:00Z",
    "component": {
      "type": "application",
      "name": "my-app",
      "version": "1.0.0"
    }
  },
  "components": [
    {
      "type": "library",
      "name": "lodash",
      "version": "4.17.21",
      "purl": "pkg:npm/lodash@4.17.21",
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "2c5a0..."
        }
      ],
      "licenses": [
        {
          "license": {
            "id": "MIT"
          }
        }
      ]
    }
  ],
  "dependencies": [
    {
      "ref": "my-app@1.0.0",
      "dependsOn": ["lodash@4.17.21"]
    }
  ]
}
```

### 4.3 Comparison

| Aspect | SPDX 2.3 / 3.0 | CycloneDX 1.6 |
|---|---|---|
| **Governance** | Linux Foundation, ISO | OWASP, ECMA (pending) |
| **Primary use** | License compliance | Security / vuln management |
| **VEX support** | Via external VEX doc | Native `vulnerabilities[]` |
| **BOM composability** | Relationships model | `externalReferences` + BOM links |
| **Ecosystem** | sbom-tool, syft, trivy | cyclonedx-cli, cdxgen, syft, trivy |
| **Learning curve** | Steeper (richer model) | Shallower |
| **US government** | NTIA minimum elements covered | NTIA minimum elements covered |

**Recommendation:** Use CycloneDX if your primary goal is vulnerability
management. Use SPDX if license compliance is the driver or if your supply
chain partners require ISO standardization. Most SBOM generators (syft, trivy)
produce both.

### 4.4 Package URL (purl)

Both formats use the purl spec for universal package identification:

```
scheme:type/namespace/name@version?qualifiers#subpath
pkg:npm/%40angular/core@16.2.0
pkg:pypi/requests@2.31.0
pkg:golang/github.com/gin-gonic/gin@v1.9.1
pkg:maven/org.apache.logging.log4j/log4j-core@2.17.1
pkg:deb/debian/curl@7.88.1-10+deb12u5
pkg:oci/alpine@sha256:abcdef...
```

Purls enable cross-format, cross-tool correlation. A CVE database entry
referencing `pkg:maven/org.apache.logging.log4j/log4j-core` can be matched
against any SBOM that uses purls, regardless of SPDX vs CycloneDX.

### 4.5 VEX (Vulnerability Exploitability eXchange)

VEX is a companion document to an SBOM that states whether a known vulnerability
in a component actually affects the product.

**Status values:**
- `not_affected` — "Yes, we include log4j, but we don't use JNDI lookups."
- `affected` — "This vulnerability impacts us."
- `fixed` — "We patched/upgraded."
- `under_investigation` — "We're evaluating."

**Why VEX matters:** Without VEX, every SBOM scan produces hundreds of findings
that may be false positives (the vulnerable code path is unreachable in your
usage). VEX lets you document those triage decisions machine-readably, so
downstream consumers don't re-investigate the same false positives.

```json
{
  "vulnerabilities": [
    {
      "id": "CVE-2021-44228",
      "analysis": {
        "state": "not_affected",
        "justification": "code_not_reachable",
        "detail": "JNDI lookups disabled via log4j2.formatMsgNoLookups=true"
      },
      "affects": [
        {
          "ref": "pkg:maven/org.apache.logging.log4j/log4j-core@2.14.1"
        }
      ]
    }
  ]
}
```

---

## 5. SBOM Generation Tools

### 5.1 Syft (Anchore)

The most widely adopted open-source SBOM generator. Works across ecosystems.

```bash
# Generate CycloneDX JSON from a container image
syft alpine:3.19 -o cyclonedx-json > sbom.cdx.json

# Generate SPDX from a directory (source analysis)
syft dir:./my-project -o spdx-json > sbom.spdx.json

# Generate from a built Go binary (binary analysis)
syft file:./my-binary -o cyclonedx-json > sbom.cdx.json

# Supported output formats
# cyclonedx-json, cyclonedx-xml, spdx-json, spdx-tag-value,
# github-json (for GitHub dependency graph), syft-json (native)
```

**Supported ecosystems:** apk, deb, rpm, npm, pip, Go modules, Java (JAR/WAR
manifest), Rust (Cargo), Ruby (Gemfile), .NET (NuGet), PHP (Composer), Haskell,
Dart, Swift (CocoaPods, SPM), and binary analysis (Go, Rust ELF binaries).

**How it works:**
- **Source analysis:** Parses lock files and manifests (`package-lock.json`,
  `go.sum`, `requirements.txt`, `Cargo.lock`, etc.).
- **Image analysis:** Inspects container image layers, detects package managers,
  reads installed package databases (`/var/lib/dpkg`, `/var/lib/rpm`).
- **Binary analysis:** Scans ELF/Mach-O binaries for embedded dependency info
  (Go build info, Rust dep metadata).

### 5.2 cdxgen (CycloneDX Generator)

CycloneDX's official multi-ecosystem generator.

```bash
# Install
npm install -g @cyclonedx/cdxgen

# Generate SBOM for a Node.js project
cdxgen -o sbom.json --type node .

# Generate for Java/Maven
cdxgen -o sbom.json --type java .

# Generate for Python
cdxgen -o sbom.json --type python .

# With vulnerability data enrichment
cdxgen -o sbom.json --type node --deep .
```

**Strengths:** Understands build systems deeply (Maven dependency trees,
Gradle configurations, pip resolution), can resolve transitive deps that
manifest-only analysis misses.

### 5.3 Trivy (Aqua Security)

Primarily a vulnerability scanner, but has excellent SBOM generation built in.

```bash
# Generate SBOM for a container image
trivy image --format cyclonedx --output sbom.cdx.json alpine:3.19

# Generate SBOM for a filesystem / source tree
trivy fs --format spdx-json --output sbom.spdx.json ./my-project

# Generate + scan in one pass
trivy image --format json --output results.json alpine:3.19
```

### 5.4 Ecosystem-Native Tools

```bash
# npm (built-in since npm 9)
npm sbom --sbom-format cyclonedx

# pip (via cyclonedx-python)
pip install cyclonedx-bom
cyclonedx-py environment -o sbom.cdx.json

# cargo (via cargo-cyclonedx)
cargo install cargo-cyclonedx
cargo cyclonedx --format json

# Go (via cyclonedx-gomod)
cyclonedx-gomod mod -json -output sbom.cdx.json

# .NET
dotnet tool install --global CycloneDX
dotnet CycloneDX ./MyProject.csproj -o sbom.cdx.json

# Microsoft sbom-tool (SPDX-focused, used for Microsoft products)
sbom-tool generate -b ./build -bc ./src -pn MyApp -pv 1.0.0 -ps MyOrg
```

### 5.5 SBOM Quality Validation

Not all SBOMs are equal. A low-quality SBOM (missing hashes, no purls, incomplete
dependency graph) is worse than no SBOM — it creates false confidence.

**NTIA Minimum Elements (2021):**
- Supplier name
- Component name
- Component version
- Unique identifier (purl)
- Dependency relationship
- Author of SBOM data
- Timestamp

**Validation tools:**
```bash
# Validate CycloneDX SBOM
cyclonedx-cli validate --input-file sbom.cdx.json --fail-on-errors

# Validate SPDX
java -jar tools-java-*.jar Verify sbom.spdx.json

# SBOM quality score (sbomqs by Interlynk)
sbomqs score sbom.cdx.json
# Output: Structural: 8.5/10, Semantic: 7.0/10, Quality: 6.5/10
```

---

## 6. Software Composition Analysis (SCA)

SCA is the process of scanning your dependencies against known vulnerability
databases and license policies.

### 6.1 How SCA Works

```
SBOM / Lock File / Manifest
        │
        ▼
  ┌─────────────┐
  │ Parse deps   │ → extract (name, version, ecosystem)
  └─────┬───────┘
        │
        ▼
  ┌─────────────────┐
  │ Match against    │ → NVD, OSV, GitHub Advisory DB, vendor DBs
  │ vuln databases   │
  └─────┬───────────┘
        │
        ▼
  ┌─────────────────┐
  │ Enrich findings  │ → CVSS score, EPSS probability, exploit availability
  └─────┬───────────┘
        │
        ▼
  ┌─────────────────┐
  │ Policy engine    │ → fail CI on CRITICAL, warn on HIGH, suppress known FP
  └─────┬───────────┘
        │
        ▼
  Report / PR comment / SARIF / dashboard
```

### 6.2 Vulnerability Databases

| Database | Coverage | Access |
|---|---|---|
| **NVD (NIST)** | All ecosystems via CPE | Free, REST API |
| **OSV (Google)** | Ecosystem-native IDs (GHSA, PYSEC, RUSTSEC) | Free, API + OSV-Scanner |
| **GitHub Advisory Database** | npm, pip, Maven, Go, Rust, etc. | Free, GraphQL API |
| **Snyk Vulnerability DB** | Curated, proprietary enrichment | Commercial |
| **VulnDB (Risk Based Security)** | Widest CVE coverage | Commercial |

**CPE vs purl matching:** NVD uses CPE (Common Platform Enumeration) identifiers,
which are notoriously imprecise for open-source packages. A single CPE may map
to multiple packages or miss version ranges. OSV uses ecosystem-native package
identifiers (purl-compatible), giving much more accurate matching.

### 6.3 EPSS and Exploit Prioritization

CVSS tells you severity. EPSS (Exploit Prediction Scoring System) tells you
probability of exploitation in the wild within 30 days.

```
CVSS 9.8 + EPSS 0.001 → severe but unlikely to be exploited
CVSS 6.5 + EPSS 0.85  → moderate but actively exploited RIGHT NOW
```

Prioritize by EPSS > CVSS when both are available. A CVSS 6.5 with EPSS 0.85
should be patched before a CVSS 9.8 with EPSS 0.001.

**KEV (CISA Known Exploited Vulnerabilities):** Catalog of CVEs confirmed
exploited in the wild. If a CVE is on KEV, it gets top priority regardless of
CVSS score.

### 6.4 Reachability Analysis

Not every vulnerable dependency is actually exploitable. If your code never
calls the vulnerable function, the CVE may not affect you.

**Static reachability:** Build a call graph from your code. Trace whether any
execution path reaches the vulnerable function in the dependency.

**Tools:**
- Snyk: reachability analysis for Java, JavaScript.
- Semgrep Supply Chain: taint-based reachability for Python, Java, JS.
- Eclipse Steady (formerly SAP Vulas): Java reachability via instrumentation.

**Limitations:** Static analysis is conservative (overapproximates). Dynamic
analysis is precise but coverage-limited. Reachability analysis reduces noise
by ~70-80% but should not be the sole triage signal.

---

## 7. SCA Tools Deep Dive

### 7.1 Trivy

```bash
# Scan a container image
trivy image --severity CRITICAL,HIGH myapp:latest

# Scan a source tree
trivy fs --severity CRITICAL ./src

# Scan a lock file directly
trivy fs --scanners vuln package-lock.json

# Scan with SARIF output for GitHub Code Scanning
trivy image --format sarif --output results.sarif myapp:latest

# Scan Kubernetes manifests for misconfigurations + vulns
trivy k8s --report summary cluster

# Ignore unfixed vulnerabilities
trivy image --ignore-unfixed myapp:latest

# Use .trivyignore for suppression
# File: .trivyignore
# CVE-2023-12345  # False positive: code path unreachable
# CVE-2023-67890  # Accepted risk: no fix available, mitigated by WAF
```

**Databases:** Uses OSV, NVD, Red Hat OVAL, Alpine SecDB, Debian tracker,
Ubuntu OVAL, Amazon ALAS, and more. Updates via `trivy-db` OCI artifact.

**Strengths:** Single binary, no daemon, fast, supports images + filesystems +
repos + K8s + SBOM input. Active development.

**Weaknesses:** No reachability analysis. No centralized dashboard (use
third-party integrations or Trivy Operator for K8s).

### 7.2 Grype (Anchore)

```bash
# Scan an SBOM (pairs with syft)
syft myapp:latest -o syft-json | grype

# Scan a container image directly
grype myapp:latest --fail-on high

# Scan a directory
grype dir:./my-project

# Custom output template
grype myapp:latest -o template -t ./my-template.tmpl
```

**Syft + Grype is the open-source pipeline:** syft generates the SBOM, grype
scans it. This separation of concerns allows you to store the SBOM, share it,
and rescan it later against updated vulnerability databases without re-analyzing
the artifact.

### 7.3 Snyk

```bash
# Authenticate
snyk auth

# Test dependencies
snyk test

# Test a container image
snyk container test myapp:latest

# Monitor (continuous, reports to Snyk dashboard)
snyk monitor

# Test infrastructure as code
snyk iac test ./terraform/

# Fix: generate upgrade PRs
snyk fix
```

**Differentiators:**
- Proprietary vulnerability database with faster-than-NVD disclosure.
- Reachability analysis (Java, JavaScript).
- Auto-fix PRs (upgrade to non-vulnerable version, or apply Snyk patches).
- IDE plugins (VS Code, IntelliJ).
- License compliance policies.
- SBOM export.

**Pricing model:** Free tier (limited tests/month), Team, Enterprise.

### 7.4 Dependabot (GitHub)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
      day: "monday"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
    labels:
      - "dependencies"
      - "security"
    # Group minor/patch updates to reduce PR noise
    groups:
      production-deps:
        patterns:
          - "*"
        exclude-patterns:
          - "@types/*"
        update-types:
          - "minor"
          - "patch"

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "weekly"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

**Key features:**
- Security updates (triggered by GitHub Advisory Database).
- Version updates (scheduled, keeps deps fresh).
- Grouped updates (reduces PR noise).
- GitHub Actions ecosystem (catches compromised actions like tj-actions).

**Limitation:** GitHub-only. No reachability analysis. No centralized dashboard
across orgs (use GitHub Security Overview for that).

### 7.5 Renovate

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": [
    "config:recommended",
    ":automergeMinor",
    ":automergePatch",
    "group:allNonMajor"
  ],
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "automerge": false
    },
    {
      "matchPackagePatterns": ["eslint", "prettier"],
      "groupName": "lint tooling",
      "automerge": true
    },
    {
      "matchDepTypes": ["devDependencies"],
      "automerge": true,
      "automergeType": "branch"
    }
  ],
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"]
  }
}
```

**vs Dependabot:** Renovate is more configurable (grouping, scheduling,
automerge rules, monorepo support). Works on GitHub, GitLab, Bitbucket,
Azure DevOps, Gitea. Self-hosted option.

### 7.6 OSV-Scanner (Google)

```bash
# Scan a directory
osv-scanner -r ./my-project

# Scan a lock file
osv-scanner --lockfile=package-lock.json

# Scan an SBOM
osv-scanner --sbom=sbom.cdx.json

# Guided remediation (find minimal upgrade set)
osv-scanner fix --lockfile=package-lock.json --strategy=in-place

# Output in JSON
osv-scanner --format json -r ./my-project
```

**Strengths:** Uses OSV.dev database (aggregates GHSA, PYSEC, RUSTSEC, Go
vulndb). Guided remediation finds the minimal set of version bumps to fix all
known vulns. Free, open-source, maintained by Google.

### 7.7 Tool Comparison

| Feature | Trivy | Grype | Snyk | Dependabot | Renovate | OSV-Scanner |
|---|---|---|---|---|---|---|
| **OSS** | Yes | Yes | Freemium | Free (GitHub) | Yes | Yes |
| **Container scan** | Yes | Yes | Yes | No | No | No |
| **SBOM generation** | Yes | No (syft) | Yes | No | No | No |
| **Reachability** | No | No | Yes (partial) | No | No | No |
| **Auto-fix PRs** | No | No | Yes | Yes | Yes | Yes (guided) |
| **License check** | Yes | No | Yes | No | No | No |
| **IaC scanning** | Yes | No | Yes | No | No | No |
| **CI integration** | GitHub/GitLab/etc | Any | GitHub/GitLab/etc | GitHub only | Multi-platform | Any |
| **Vuln DB** | OSV + NVD + distro | OSV + NVD | Proprietary + NVD | GitHub Advisory | NVD + ecosystems | OSV.dev |

---

## 8. SLSA Framework

SLSA (Supply-chain Levels for Software Artifacts, pronounced "salsa") is a
framework by Google for ensuring the integrity of software artifacts throughout
the supply chain.

### 8.1 The Problem SLSA Solves

SCA answers: "does this artifact contain known vulnerabilities?"
SLSA answers: "was this artifact built from the source I think, by a builder
I trust, without tampering?"

These are orthogonal. A vulnerability-free artifact is useless if it was built
from tampered source. A provenance-verified artifact is useless if it contains
Log4Shell.

### 8.2 SLSA Levels (v1.0)

| Level | Requirement | What it prevents |
|---|---|---|
| **Build L0** | No provenance | Nothing — baseline |
| **Build L1** | Provenance exists, documents the build process | Ad-hoc builds with no records |
| **Build L2** | Provenance is generated by a hosted build service, signed | Tampering after build, forged provenance |
| **Build L3** | Hardened build platform, hermetic, non-falsifiable provenance | Insider threats on the build platform itself |

**L1:** "We wrote down how we built it."
**L2:** "A trusted CI system built it and signed the receipt."
**L3:** "Even the CI system's admins can't tamper with the artifact or its provenance."

### 8.3 Provenance Schema

SLSA provenance follows the in-toto attestation framework:

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "my-app",
      "digest": {
        "sha256": "abc123..."
      }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://github.com/slsa-framework/slsa-github-generator/...",
      "externalParameters": {
        "source": {
          "uri": "git+https://github.com/myorg/my-app@refs/heads/main",
          "digest": {
            "sha1": "def456..."
          }
        }
      }
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.0.0"
      },
      "metadata": {
        "invocationId": "https://github.com/myorg/my-app/actions/runs/123456789"
      }
    }
  }
}
```

### 8.4 SLSA on GitHub Actions

```yaml
# .github/workflows/release.yml
name: Release with SLSA L3 Provenance

on:
  push:
    tags:
      - "v*"

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    steps:
      - uses: actions/checkout@v4
      - run: |
          go build -o my-app .
          sha256sum my-app > digest.txt
      - id: hash
        run: echo "digest=$(cat digest.txt | awk '{print $1}')" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: my-app
          path: my-app

  provenance:
    needs: build
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.0.0
    with:
      base64-subjects: ${{ needs.build.outputs.digest }}
      upload-assets: true

  verify:
    needs: [build, provenance]
    runs-on: ubuntu-latest
    steps:
      - uses: slsa-framework/slsa-verifier/actions/installer@v2.6.0
      - run: |
          slsa-verifier verify-artifact my-app \
            --provenance-path multiple.intoto.jsonl \
            --source-uri github.com/myorg/my-app
```

### 8.5 SLSA for Container Images

```yaml
# Using ko (Go container builder) with SLSA provenance
jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: ko-build/setup-ko@v0.7
      - run: |
          ko build ./cmd/server \
            --image-refs=.digest \
            --bare
      - uses: sigstore/cosign-installer@v3
      - run: |
          cosign sign $(cat .digest) \
            --yes
```

---

## 9. Sigstore Ecosystem

Sigstore solves the key management problem for artifact signing. Traditional
signing (GPG) requires maintaining long-lived keys, which are operationally
expensive and a juicy target for attackers.

### 9.1 Components

```
┌─────────────┐     ┌──────────┐     ┌───────────┐
│   cosign     │────→│  Fulcio   │────→│   Rekor    │
│  (signer)    │     │  (CA)     │     │  (log)     │
└─────────────┘     └──────────┘     └───────────┘
      │                   │                 │
      │    OIDC token     │   Certificate   │  Signed entry
      │    (GitHub, Google)│   (short-lived) │  (immutable)
```

**Fulcio:** Certificate authority that issues short-lived (10-minute) signing
certificates based on OIDC identity. No key management needed.

**Rekor:** Append-only transparency log. Every signing event is recorded.
Immutable, publicly auditable. Similar concept to Certificate Transparency
logs for TLS.

**cosign:** CLI tool for signing and verifying container images and blobs.

### 9.2 Keyless Signing with cosign

```bash
# Sign a container image (keyless — uses OIDC identity)
cosign sign myregistry.io/myapp@sha256:abc123

# What happens:
# 1. cosign requests OIDC token from your identity provider
#    (GitHub Actions OIDC, Google, Microsoft, etc.)
# 2. Fulcio issues a short-lived certificate binding your identity to a key pair
# 3. cosign signs the image digest with the ephemeral private key
# 4. Signature + certificate are uploaded to Rekor transparency log
# 5. Private key is discarded (never stored)

# Verify a signed image
cosign verify myregistry.io/myapp@sha256:abc123 \
  --certificate-identity="https://github.com/myorg/my-app/.github/workflows/release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Sign a blob (non-container artifact)
cosign sign-blob --bundle my-app.bundle my-app

# Verify a signed blob
cosign verify-blob --bundle my-app.bundle my-app \
  --certificate-identity="..." \
  --certificate-oidc-issuer="..."

# Attach an SBOM to a signed image
cosign attach sbom --sbom sbom.cdx.json myregistry.io/myapp@sha256:abc123

# Sign the attached SBOM
cosign sign --attachment sbom myregistry.io/myapp@sha256:abc123

# Attest provenance (in-toto attestation)
cosign attest --predicate provenance.json --type slsaprovenance \
  myregistry.io/myapp@sha256:abc123

# Verify attestation
cosign verify-attestation --type slsaprovenance \
  --certificate-identity="..." \
  --certificate-oidc-issuer="..." \
  myregistry.io/myapp@sha256:abc123
```

### 9.3 Key-based Signing (When Needed)

Keyless signing requires an OIDC provider. For air-gapped environments or
environments without OIDC, use key-based signing:

```bash
# Generate a key pair
cosign generate-key-pair

# Sign with the key
cosign sign --key cosign.key myregistry.io/myapp@sha256:abc123

# Verify with the public key
cosign verify --key cosign.pub myregistry.io/myapp@sha256:abc123
```

**Key management considerations:**
- Store the private key in a KMS (AWS KMS, GCP KMS, Azure Key Vault, HashiCorp Vault).
- cosign supports KMS URIs directly: `cosign sign --key awskms:///<key-id> ...`
- Never store signing keys in the repository or CI environment variables.

### 9.4 Rekor Transparency Log

```bash
# Search Rekor for entries related to an artifact
rekor-cli search --sha sha256:abc123

# Get a specific log entry
rekor-cli get --uuid <entry-uuid>

# Verify inclusion in the log
rekor-cli verify --artifact my-app --signature my-app.sig
```

Rekor provides:
- **Tamper evidence:** If someone modifies a log entry, the Merkle tree root
  hash changes, detectable by monitors.
- **Non-repudiation:** The signer cannot deny having signed (recorded in
  public log).
- **Discovery:** Anyone can search for signatures on any artifact.

---

## 10. Reproducible Builds

### 10.1 Definition

A build is reproducible if, given the same source code, build environment, and
build instructions, any party can independently produce bit-for-bit identical
output.

### 10.2 Why Reproducibility Matters

Without reproducible builds, you cannot verify that a binary was actually
produced from the claimed source code. This is exactly how the xz-utils
backdoor worked — the source looked clean, but the build process injected
malicious code.

```
Reproducible:
  Source A + Build env B → Binary X  (always)
  Anyone can verify: rebuild from A+B, compare hash to X

Non-reproducible:
  Source A + Build env B → Binary X₁ (Tuesday)
  Source A + Build env B → Binary X₂ (Wednesday)
  X₁ ≠ X₂ → cannot verify if either matches source
```

### 10.3 Common Sources of Non-Reproducibility

| Source | Problem | Fix |
|---|---|---|
| **Timestamps** | Build date embedded in binary | Use `SOURCE_DATE_EPOCH` env var |
| **File ordering** | Filesystem enumeration order varies | Sort file lists explicitly |
| **Randomness** | Random UUIDs, hash seeds | Seed PRNG deterministically |
| **Paths** | Absolute build paths in debug info | Use relative paths, strip debug |
| **Locale** | String sorting depends on locale | Set `LC_ALL=C` |
| **Timezone** | Affects embedded timestamps | Set `TZ=UTC` |
| **Compiler version** | Different codegen | Pin compiler in build env |
| **Parallel build** | Link order varies with parallelism | Deterministic link order |

### 10.4 Ecosystem-Specific Approaches

**Go:** Reproducible by default for `go build` (since Go 1.13 with modules).
Binary embeds module info but not timestamps. `CGO_ENABLED=0` eliminates
C-library linking variance.

**Rust:** `cargo build` is mostly reproducible with some caveats (file paths,
features). The `cargo-reproducible` project tracks remaining issues.

**Debian:** The Reproducible Builds project has made >95% of Debian packages
reproducible. Uses `SOURCE_DATE_EPOCH`, `strip-nondeterminism`, and
`diffoscope` for comparison.

**Docker/OCI images:**
```bash
# Non-reproducible (timestamp, layer ordering)
docker build -t myapp .

# More reproducible: use BuildKit with reproducible output
docker buildx build --output type=oci,dest=myapp.tar .

# Best: use tools designed for reproducibility
# ko (Go), jib (Java), apko (Alpine), nixpacks
ko build ./cmd/server  # no Dockerfile, reproducible Go container
```

### 10.5 Diffoscope

When two builds produce different output, `diffoscope` provides a detailed
recursive diff that identifies exactly where the non-determinism crept in.

```bash
# Compare two builds
diffoscope build-tuesday/myapp build-wednesday/myapp

# Output shows:
# - Timestamp difference at offset 0x4A80
# - Path string difference at offset 0x8C00
# - Metadata difference in ELF section .comment
```

---

## 11. Provenance Attestation

Provenance answers: "Where did this artifact come from?"

### 11.1 in-toto Framework

in-toto (Latin: "as a whole") is a framework for securing the entire software
supply chain — from source to deployment.

**Concepts:**
- **Layout:** Defines the expected steps in the supply chain, who performs them,
  and what artifacts flow between them.
- **Link:** A signed record of a step's execution (inputs, outputs, command,
  performer).
- **Inspection:** Automated verification rules run at verification time.

```
Layout (signed by project owner):
  Step 1: "clone" by developer-key-A
    expected command: git clone ...
    expected products: match("*.py")

  Step 2: "build" by ci-key-B
    expected materials: match Step 1 products
    expected products: match("dist/*.whl")

  Step 3: "sign" by release-key-C
    expected materials: match Step 2 products

  Inspection: verify SBOM covers all products of Step 2
```

### 11.2 SLSA Provenance vs in-toto

SLSA provenance is a specific predicate type within the in-toto attestation
framework. SLSA focuses on the build step. in-toto can model the entire
pipeline (source → build → test → package → deploy).

### 11.3 GitHub Artifact Attestations

GitHub provides native attestation support:

```yaml
# In GitHub Actions workflow
- uses: actions/attest-build-provenance@v1
  with:
    subject-path: ./build/my-app

# Verify locally
gh attestation verify my-app --owner myorg
```

This generates in-toto attestations with SLSA provenance, signed with Sigstore,
and stored in GitHub's attestation registry.

### 11.4 Attestation Storage

Attestations need to be stored and discoverable:

- **OCI registry:** Attached to container images via cosign/ORAS.
- **Rekor:** Public transparency log.
- **GitHub Attestation Store:** For GitHub-built artifacts.
- **In-repo:** For source attestations (signed commits, tags).

---

## 12. Lock File Security

Lock files pin exact dependency versions and integrity hashes. They are the
first line of defense against supply chain attacks.

### 12.1 Lock File Formats

| Ecosystem | Lock file | Integrity hash |
|---|---|---|
| npm | `package-lock.json` | SHA-512 in `integrity` field |
| Yarn | `yarn.lock` | SHA-512 |
| pnpm | `pnpm-lock.yaml` | SHA-512 |
| pip | `requirements.txt` (with hashes) | `--hash=sha256:...` |
| Poetry | `poetry.lock` | SHA-256 |
| Go | `go.sum` | SHA-256 of module zip + `go.mod` |
| Cargo | `Cargo.lock` | SHA-256 `checksum` |
| Bundler | `Gemfile.lock` | (no native hashes; use `bundle lock --checksums`) |
| Composer | `composer.lock` | (no native hashes) |
| Gradle | `gradle.lockfile` or Dependency Verification `.xml` | SHA-256/SHA-512 |

### 12.2 Lock File Best Practices

**1. Always commit lock files to version control.**

Without a committed lock file, every developer and CI run may resolve to
different dependency versions. This is non-deterministic and prevents
reproducibility.

**2. Use `--frozen-lockfile` / `--ci` in CI.**

```bash
# npm: fail if lock file would change
npm ci

# Yarn: fail if lock file would change
yarn install --frozen-lockfile

# pnpm: fail if lock file would change
pnpm install --frozen-lockfile

# pip: install only from hashed requirements
pip install --require-hashes -r requirements.txt

# cargo: (Cargo.lock is always respected for binaries)
```

This prevents CI from silently upgrading dependencies. If a lock file update is
needed, it should happen in a dedicated PR with diff review.

**3. Review lock file diffs in PRs.**

Lock file changes should be reviewed with the same scrutiny as source code.
A malicious dependency addition hides in the lock file diff.

```diff
# Suspicious: new dependency you didn't add
+ "node_modules/totally-legit-package": {
+   "version": "1.0.0",
+   "resolved": "https://registry.npmjs.org/totally-legit-package/-/...",
+   "integrity": "sha512-...",
```

**4. Pin integrity hashes.**

pip with hashes is the gold standard:

```
# requirements.txt
requests==2.31.0 \
    --hash=sha256:942c5a758f98d790eaed1a29cb6eefc7f0edf3fcb0fce8aea3fbd5951d... \
    --hash=sha256:fc06670dd0ed212426dfeb94fc1b983d917c4f9...
```

If the package at that version changes (supply chain attack), the hash won't
match and installation fails.

### 12.3 Lock File Attacks

**Registry substitution:** Attacker compromises the registry and serves a
different tarball for the same version. Integrity hashes prevent this.

**Lock file injection:** Attacker submits a PR that modifies the lock file to
add a malicious dependency. Code review of lock file diffs prevents this.

**Lock file deletion:** A PR that "cleans up" by removing the lock file.
Branch protection rules should prevent this.

---

## 13. Typosquatting & Dependency Confusion

### 13.1 Typosquatting Techniques

| Technique | Legitimate | Typosquat |
|---|---|---|
| Character swap | `requests` | `reqeusts` |
| Homoglyph | `colors` | `co1ors` (digit 1) |
| Hyphen/underscore | `python-dateutil` | `python_dateutil` |
| Scope confusion | `@babel/core` | `babel-core` |
| Namespace squatting | (internal `@company/utils`) | (public `@company/utils`) |
| Combosquatting | `lodash` | `lodash-utils`, `lodash-es-extra` |

### 13.2 Registry Defenses

**npm:**
- Blocks publish of packages too similar to popular packages.
- Mandatory 2FA for maintainers of top-500 packages.
- `npm audit signatures` verifies registry-signed packages.

**PyPI:**
- Malware detection scanning on upload.
- Trusted Publisher workflow (no stored credentials needed).
- Name similarity checking.

**crates.io:**
- Prevents squatting (packages cannot be empty placeholder publishes).
- Requires GitHub authentication.

### 13.3 Detection Tools

```bash
# socket.dev — real-time supply chain analysis in PRs
# Detects: typosquats, install scripts, obfuscated code, network access,
# filesystem access, shell access, environment access

# Phylum — automated policy engine
phylum analyze package-lock.json

# npm audit signatures (verify registry signing)
npm audit signatures

# pip-audit (Google)
pip-audit -r requirements.txt
```

### 13.4 Dependency Confusion Prevention

```
# .npmrc — scope pinning
@mycompany:registry=https://npm.mycompany.com/
registry=https://registry.npmjs.org/

# pip.conf — index pinning
[global]
index-url = https://pypi.mycompany.com/simple/
extra-index-url = https://pypi.org/simple/
# WARNING: extra-index-url checks BOTH registries. Attacker can win.
# Safer: use --index-url only (single source of truth)
# Or: use a proxy registry (Artifactory, Nexus) that merges internal + public

# Maven settings.xml — mirror configuration
<mirrors>
  <mirror>
    <id>company-mirror</id>
    <mirrorOf>*</mirrorOf>
    <url>https://nexus.mycompany.com/repository/maven-public/</url>
  </mirror>
</mirrors>
```

**Best practice:** Use a proxy/caching registry (JFrog Artifactory, Sonatype
Nexus, AWS CodeArtifact, GitHub Packages) as the single source for all
dependencies. The proxy fetches from public registries and caches. You configure
clients to only talk to the proxy. The proxy can enforce policies (block
packages without SBOMs, block packages with known vulns, block unsigned packages).

---

## 14. CI/CD Integration Patterns

### 14.1 Full Supply Chain Pipeline

```yaml
# .github/workflows/supply-chain.yml
name: Supply Chain Security

on:
  pull_request:
  push:
    branches: [main]
    tags: ["v*"]

permissions:
  contents: read
  security-events: write
  id-token: write

jobs:
  # Stage 1: Dependency scan on every PR
  sca-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: fs
          scan-ref: .
          severity: CRITICAL,HIGH
          exit-code: 1
          format: sarif
          output: trivy-results.sarif

      - name: Upload SARIF to GitHub Security
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif

  # Stage 2: SBOM generation on main branch
  sbom:
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: anchore/sbom-action@v0
        with:
          format: cyclonedx-json
          output-file: sbom.cdx.json
          artifact-name: sbom

      - name: Validate SBOM quality
        run: |
          sbomqs score sbom.cdx.json

  # Stage 3: Build + sign + attest on tag
  release:
    if: startsWith(github.ref, 'refs/tags/')
    needs: [sca-scan, sbom]
    runs-on: ubuntu-latest
    permissions:
      contents: write
      packages: write
      id-token: write
      attestations: write
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: go build -o my-app .

      - name: Generate SBOM for binary
        run: syft file:./my-app -o cyclonedx-json > sbom.cdx.json

      - name: Build container image
        run: |
          docker build -t ghcr.io/${{ github.repository }}:${{ github.ref_name }} .
          docker push ghcr.io/${{ github.repository }}:${{ github.ref_name }}

      - name: Sign container image
        uses: sigstore/cosign-installer@v3
      - run: |
          cosign sign ghcr.io/${{ github.repository }}@${{ steps.push.outputs.digest }} --yes

      - name: Attest provenance
        uses: actions/attest-build-provenance@v1
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.push.outputs.digest }}

      - name: Attest SBOM
        uses: actions/attest-sbom@v1
        with:
          subject-name: ghcr.io/${{ github.repository }}
          subject-digest: ${{ steps.push.outputs.digest }}
          sbom-path: sbom.cdx.json
```

### 14.2 Pre-Commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks
        name: Detect hardcoded secrets

  - repo: local
    hooks:
      - id: lockfile-lint
        name: Lint lock file integrity
        entry: lockfile-lint --path package-lock.json --type npm --allowed-hosts npm
        language: node
        files: package-lock\.json$

      - id: check-lockfile-committed
        name: Ensure lock file is committed
        entry: bash -c 'git diff --name-only --cached | grep -q "package-lock.json" || echo "WARNING: package.json changed but lock file not staged"'
        language: system
        files: package\.json$
```

### 14.3 Dependency Review on PRs

```yaml
# .github/workflows/dependency-review.yml
name: Dependency Review

on: pull_request

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/dependency-review-action@v4
        with:
          fail-on-severity: high
          deny-licenses: AGPL-3.0, GPL-3.0
          comment-summary-in-pr: always
```

This action analyzes the diff between the PR and the base branch, identifies
new dependencies, checks them against the GitHub Advisory Database, and flags
vulnerabilities or license violations.

---

## 15. Container Supply Chain

### 15.1 Base Image Selection

```
Risk spectrum (high → low):
  ubuntu:latest       ← mutable tag, 100+ MB, hundreds of packages
  ubuntu:24.04        ← pinned to release, still large attack surface
  alpine:3.19         ← 5 MB, musl, fewer packages, fewer CVEs
  distroless/static   ← no shell, no package manager, minimal attack surface
  scratch             ← empty, only your binary (Go, Rust static builds)
  chainguard/static   ← hardened, SBOM included, signed, FIPS options
```

**Best practices:**
- Pin base images by digest, not tag: `FROM alpine@sha256:abc123...`
- Rebuild periodically to pick up base image security patches.
- Multi-stage builds: build in a fat image, copy binary to a minimal runtime image.

### 15.2 Image Signing and Verification

```bash
# Sign all images in your release pipeline
cosign sign ghcr.io/myorg/myapp@sha256:abc123 --yes

# In Kubernetes: verify signatures before admission (see section 16)

# In Docker: Content Trust (DCT) — Notary v1
export DOCKER_CONTENT_TRUST=1
docker pull myregistry.io/myapp:latest  # fails if not signed
```

### 15.3 Distroless and Minimal Images

Google's distroless images contain only the runtime (e.g., JRE, Python
interpreter) and your app — no shell, no package manager, no utilities.

```dockerfile
# Multi-stage build: build in full image, run in distroless
FROM golang:1.22 AS builder
WORKDIR /app
COPY . .
RUN CGO_ENABLED=0 go build -o /server .

FROM gcr.io/distroless/static-debian12
COPY --from=builder /server /server
ENTRYPOINT ["/server"]
```

**Chainguard Images:** Go further than distroless — hardened, SBOM included,
vulnerability scanned, signed with cosign, rebuilt nightly.

### 15.4 Image Scanning in CI

```yaml
# Scan before push
- name: Scan image
  run: |
    trivy image --exit-code 1 --severity CRITICAL \
      myapp:${{ github.sha }}

# Scan in registry (continuous)
# Most registries (ECR, GCR, ACR, Harbor) support automatic scanning
# Harbor: Trivy built-in
# ECR: Amazon Inspector
# GCR: Artifact Analysis
```

---

## 16. Policy Engines & Admission Control

### 16.1 Kubernetes Admission Control

Admission controllers intercept API requests before persistence. Use them to
enforce supply chain policies on every deployment.

```
kubectl apply -f deployment.yaml
        │
        ▼
  ┌──────────────────┐
  │ API Server        │
  │                   │
  │  Mutating Webhook │ → (modify request)
  │  Validating Hook  │ → (accept/reject)
  └──────────────────┘
        │
        ▼
  Persisted to etcd (only if admitted)
```

### 16.2 Kyverno (Policy-as-YAML)

```yaml
# Require cosign signature on all images
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-signature
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-cosign-signature
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestors:
            - entries:
                - keyless:
                    issuer: "https://token.actions.githubusercontent.com"
                    subject: "https://github.com/myorg/*"

---
# Require SBOM attestation
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-sbom
spec:
  validationFailureAction: Enforce
  rules:
    - name: verify-sbom-attestation
      match:
        any:
          - resources:
              kinds:
                - Pod
      verifyImages:
        - imageReferences:
            - "ghcr.io/myorg/*"
          attestations:
            - type: https://cyclonedx.org/bom
              conditions:
                - all:
                    - key: "{{ components[].name }}"
                      operator: NotEquals
                      value: ""
```

### 16.3 OPA Gatekeeper

```yaml
# Constraint: all images must come from trusted registries
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sAllowedRegistries
metadata:
  name: trusted-registries
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    registries:
      - "ghcr.io/myorg/"
      - "gcr.io/myproject/"
```

### 16.4 Connaisseur

Dedicated Kubernetes admission controller for container image signature
verification. Simpler than Kyverno for signature-only use cases.

---

## 17. Compliance & Regulatory Landscape

### 17.1 US Executive Order 14028 (May 2021)

Requires software vendors selling to the US federal government to:
- Provide SBOMs for their products.
- Attest to secure software development practices.
- Implement vulnerability disclosure programs.

### 17.2 NIST SSDF (Secure Software Development Framework, SP 800-218)

Defines practices for secure SDLC. Categories:
- **Prepare the Organization (PO):** policies, roles, training.
- **Protect the Software (PS):** source integrity, build integrity.
- **Produce Well-Secured Software (PW):** design, code review, testing.
- **Respond to Vulnerabilities (RV):** monitoring, disclosure, patching.

### 17.3 EU Cyber Resilience Act (CRA)

Applies to products with digital elements sold in the EU. Requires:
- SBOM for all products.
- Vulnerability handling processes.
- Security updates for the product's expected lifetime.
- Incident reporting to ENISA within 24 hours.

### 17.4 NIST SP 800-161r1 (Supply Chain Risk Management)

Framework for managing cybersecurity supply chain risks. Covers:
- Supplier assessment.
- Acquisition controls.
- Continuous monitoring.
- Incident response for supply chain events.

### 17.5 FedRAMP SBOM Requirements

FedRAMP-authorized cloud services must provide SBOMs. The SBOM must be
machine-readable (SPDX or CycloneDX), include all components including
transitive dependencies, and be refreshed with each release.

---

## 18. Incident Response for Supply Chain Attacks

### 18.1 Detection Signals

| Signal | Tool | Example |
|---|---|---|
| New CVE on a dep | SCA (Trivy, Snyk) | CVE-2024-3094 on xz-utils |
| Unexpected version bump | Renovate/Dependabot diff | `colors` 1.4.0 → 1.4.1 with sabotage |
| Maintainer change | GitHub watch | New maintainer on critical dep |
| Anomalous install script | socket.dev / Phylum | `postinstall` with `curl | sh` |
| Hash mismatch | `npm audit signatures` | Registry-served tarball differs from expected |
| Unusual network access | Runtime eBPF monitoring | Library making unexpected DNS queries |

### 18.2 Response Playbook

```
1. IDENTIFY
   - Which artifact is compromised?
   - Which version(s)?
   - What is the attack vector?

2. SCOPE
   - Query SBOM database: which services/images include the compromised component?
   - Which environments? (dev, staging, production)
   - Which customers are affected?

3. CONTAIN
   - Block the compromised version in your proxy registry.
   - Roll back to last known-good version.
   - Revoke any secrets that may have been exfiltrated.

4. ERADICATE
   - Remove the compromised dependency.
   - Upgrade to a patched version or switch to an alternative.
   - Rebuild and redeploy all affected artifacts.

5. RECOVER
   - Verify the fix with SCA scan.
   - Verify artifact signatures and provenance.
   - Monitor for residual compromise (backdoor persistence).

6. LESSONS LEARNED
   - Update detection rules.
   - Tighten policies (e.g., require 2FA on all dep maintainers).
   - Update VEX documents.
   - File incident report.
```

### 18.3 Communication

- **Internal:** Notify security team, affected service owners, SRE.
- **External:** If customer data affected, follow breach notification laws
  (GDPR 72h, state laws vary).
- **Upstream:** Report to the compromised project's maintainers and the
  relevant CVE numbering authority.

---

## 19. Exercises

### Exercise 1: Full SBOM Pipeline

Build a complete SBOM pipeline for a sample application:
1. Create a sample Node.js/Go/Python application with 10+ dependencies.
2. Generate an SBOM using syft in CycloneDX format.
3. Validate the SBOM quality using sbomqs.
4. Scan the SBOM for vulnerabilities using grype.
5. Generate a VEX document for any false positives.
6. Store the SBOM alongside the built artifact.

### Exercise 2: SLSA Level 2 on GitHub

1. Fork a sample Go project.
2. Set up GitHub Actions to build the project.
3. Integrate `slsa-github-generator` to produce SLSA L2 provenance.
4. Use `slsa-verifier` to verify the provenance locally.
5. Modify the source and rebuild. Verify the provenance reflects the new source.

### Exercise 3: cosign Signing + Admission Control

1. Build a container image and push to a registry (GitHub Container Registry).
2. Sign the image with cosign (keyless).
3. Deploy a Kubernetes cluster (kind/minikube).
4. Install Kyverno.
5. Create a policy requiring cosign signatures from your GitHub Actions workflow.
6. Attempt to deploy an unsigned image. Verify it is rejected.
7. Deploy the signed image. Verify it is admitted.

### Exercise 4: Dependency Confusion Simulation

1. Create an internal npm package `@yourname/utils`.
2. Publish a public npm package with the same name but higher version.
3. Configure a project that depends on `@yourname/utils`.
4. Demonstrate the confusion attack (public version is installed).
5. Fix the `.npmrc` configuration to prevent the attack.

### Exercise 5: Lock File Tamper Detection

1. Take a project with `package-lock.json`.
2. Manually modify one dependency's integrity hash.
3. Run `npm ci`. Observe the failure.
4. Set up a CI job that fails on lock file integrity violations.

### Exercise 6: Typosquatting Analysis

1. Write a script that takes a list of your project's dependencies.
2. For each dependency, generate potential typosquat names (character swaps,
   homoglyphs, hyphen/underscore variants).
3. Check if any of those names exist on the public registry.
4. Flag any matches for manual review.

### Exercise 7: Reproducible Build Verification

1. Build a Go binary twice from the same source.
2. Compare the SHA-256 hashes. They should match.
3. Introduce a non-determinism source (embed timestamp). Rebuild.
4. Compare hashes. They should differ.
5. Fix the non-determinism. Verify hashes match again.
6. Use diffoscope to analyze a non-reproducible build.

### Exercise 8: End-to-End Supply Chain Policy

1. Set up a complete pipeline: source → SBOM → build → sign → deploy.
2. Deploy a Kyverno policy requiring both signature and SBOM attestation.
3. Deploy a Dependency Review action on PRs blocking high-severity vulns.
4. Simulate a compromised dependency. Verify the pipeline catches it.
5. Simulate an unsigned image. Verify admission control rejects it.

---

## 20. References

- SLSA specification. https://slsa.dev/
- CycloneDX specification. https://cyclonedx.org/
- SPDX specification. https://spdx.dev/
- Sigstore documentation. https://docs.sigstore.dev/
- in-toto specification. https://in-toto.io/
- Package URL specification. https://github.com/package-url/purl-spec
- NIST SSDF (SP 800-218). https://csrc.nist.gov/pubs/sp/800/218/final
- US EO 14028. https://www.whitehouse.gov/briefing-room/presidential-actions/2021/05/12/executive-order-on-improving-the-nations-cybersecurity/
- Reproducible Builds. https://reproducible-builds.org/
- OpenSSF Scorecard. https://scorecard.dev/
- CISA KEV Catalog. https://www.cisa.gov/known-exploited-vulnerabilities-catalog
- EPSS. https://www.first.org/epss/
- VEX specification. https://www.cisa.gov/sites/default/files/publications/VEX_Use_Cases_Aprill2022.pdf

---

## 21. Glossary

| Term | Definition |
|---|---|
| **SBOM** | Software Bill of Materials — machine-readable inventory of all components in a software artifact |
| **SCA** | Software Composition Analysis — scanning dependencies for known vulnerabilities |
| **SLSA** | Supply-chain Levels for Software Artifacts — framework for build integrity levels |
| **Sigstore** | Open-source project for keyless signing and verification of software artifacts |
| **cosign** | CLI tool for signing and verifying container images and other artifacts |
| **Fulcio** | Certificate authority in the Sigstore ecosystem, issues short-lived certificates via OIDC |
| **Rekor** | Append-only transparency log in the Sigstore ecosystem |
| **CycloneDX** | OWASP SBOM standard focused on security use cases |
| **SPDX** | Linux Foundation SBOM standard (ISO 5962), focused on license compliance |
| **purl** | Package URL — universal identifier for software packages across ecosystems |
| **VEX** | Vulnerability Exploitability eXchange — machine-readable document stating whether a vulnerability affects a product |
| **in-toto** | Framework for securing the entire software supply chain via signed attestations |
| **SSDF** | Secure Software Development Framework (NIST SP 800-218) |
| **KEV** | Known Exploited Vulnerabilities — CISA catalog of confirmed-exploited CVEs |
| **EPSS** | Exploit Prediction Scoring System — probability of exploitation within 30 days |
| **CPE** | Common Platform Enumeration — naming scheme for IT products (used by NVD) |
| **NVD** | National Vulnerability Database (NIST) |
| **OSV** | Open Source Vulnerabilities — Google's ecosystem-native vulnerability database |
| **Hermetic build** | A build that has no network access and uses only declared inputs |
| **Reproducible build** | A build where the same inputs always produce bit-identical output |
| **Dependency confusion** | Attack where a public package substitutes for an intended internal package |
| **Typosquatting** | Publishing malicious packages with names similar to popular packages |
| **Provenance** | Metadata describing the origin, build process, and inputs of an artifact |
| **Attestation** | Cryptographically signed statement about an artifact's properties |
