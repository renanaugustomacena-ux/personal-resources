# DevSecOps — Securing the Entire Software Development Lifecycle and CI/CD Pipeline

## Table of Contents

1. [DevSecOps Philosophy and Maturity](#1-devsecops-philosophy-and-maturity)
2. [Threat Modeling in SDLC](#2-threat-modeling-in-sdlc)
3. [Source Code Security](#3-source-code-security)
4. [Static Application Security Testing (SAST)](#4-static-application-security-testing-sast)
5. [Software Composition Analysis (SCA)](#5-software-composition-analysis-sca)
6. [Dynamic Application Security Testing (DAST)](#6-dynamic-application-security-testing-dast)
7. [Container and Infrastructure Security in Pipeline](#7-container-and-infrastructure-security-in-pipeline)
8. [Secrets Management in CI/CD](#8-secrets-management-in-cicd)
9. [Supply Chain Security](#9-supply-chain-security)
10. [Pipeline Security Architecture](#10-pipeline-security-architecture)

---

## 1. DevSecOps Philosophy and Maturity

### 1.1 Shift-Left Security

The foundational principle of DevSecOps is temporal displacement of security activities toward the earliest possible phase of software development. Traditional security review occurs at the tail end — after code is written, integrated, and staged for deployment. This model is inherently flawed because the cost of fixing a vulnerability grows exponentially as it moves downstream. A SQL injection caught during code review costs minutes; the same flaw discovered in production costs weeks of incident response, potential breach notification, and regulatory scrutiny.

Shift-left means embedding security checks, tooling, and mindset into:

- **IDE phase**: Real-time SAST feedback, secrets scanning on file save.
- **Pre-commit phase**: Hooks that block commits containing hardcoded credentials or known-vulnerable patterns.
- **Pull request phase**: Automated scanning gates that annotate PRs with findings.
- **Build phase**: SCA, container scanning, IaC validation.
- **Deploy phase**: DAST, runtime protection, policy enforcement.

The goal is not to eliminate late-stage security review but to ensure that by the time code reaches production, the overwhelming majority of security defects have already been caught and remediated at a fraction of the downstream cost.

### 1.2 DevSecOps vs Traditional Security Review

| Dimension | Traditional Security | DevSecOps |
|-----------|---------------------|-----------|
| Timing | Pre-release gate | Continuous, every commit |
| Ownership | Dedicated security team | Shared — dev, sec, ops |
| Tooling | Manual pen tests, periodic scans | Automated, CI/CD integrated |
| Feedback loop | Weeks to months | Minutes to hours |
| Coverage | Sampled (critical releases only) | Universal (every change) |
| Culture | Adversarial (sec says no) | Collaborative (sec enables) |
| Scalability | Does not scale with velocity | Scales with pipeline |

Traditional security review creates a bottleneck. A team of five security engineers cannot manually review the output of 200 developers shipping multiple times per day. DevSecOps resolves this by automating the repeatable checks and reserving human expertise for architectural review, threat modeling, and novel attack surface analysis.

### 1.3 Security as Code

Security-as-code treats security policies, configurations, and checks as version-controlled, peer-reviewed, testable artifacts. This includes:

- **Policy as code**: OPA Rego policies defining what container images, network configurations, or IAM bindings are acceptable.
- **Compliance as code**: CIS benchmarks encoded as Checkov rules or InSpec profiles.
- **Detection as code**: Semgrep rules, YARA rules, Sigma rules checked into the same repository as the application.
- **Infrastructure as code**: Terraform, CloudFormation, Pulumi modules with security defaults baked in.

When security rules live in code, they gain the same lifecycle benefits as application code: version history, branching, PR review, automated testing, and rollback capability.

### 1.4 DevSecOps Maturity Model

#### Level 1 — Ad Hoc

- No formal security integration in CI/CD.
- Security testing performed manually, if at all.
- Developers unaware of common vulnerability classes.
- No metrics, no tracking of security debt.

#### Level 2 — Repeatable

- Basic SAST tool integrated in CI (runs but does not block).
- Dependency scanning enabled with alert notifications.
- Some developers trained in secure coding.
- Vulnerability reports generated but not systematically triaged.

#### Level 3 — Defined

- Security gates block merges on critical/high findings.
- Threat modeling performed for major features.
- Security champions identified in each team.
- SLA defined for vulnerability remediation by severity.
- SBOM generated for every release.

#### Level 4 — Managed

- Comprehensive toolchain: SAST, SCA, DAST, IaC scanning, container scanning.
- Metrics tracked: MTTR, vulnerability escape rate, false positive rate.
- Automated compliance evidence generation.
- Security team operates as enablement function, not gate.
- Supply chain controls (signed artifacts, provenance).

#### Level 5 — Optimizing

- Continuous improvement driven by metrics and threat intelligence.
- Custom detection rules authored by developers.
- Automated remediation (auto-merge dependency updates, autofix patterns).
- Red team exercises inform pipeline hardening.
- Security findings drive architectural decisions proactively.

### 1.5 Cultural Transformation

#### Security Champions

A security champion is a developer embedded within a feature team who takes on additional responsibility for security awareness and advocacy. They are not security specialists — they are developers with enhanced security training who serve as the first line of defense and the bridge between the development team and the central security organization.

Responsibilities:
- Triage security tool findings for their team.
- Conduct lightweight threat modeling during sprint planning.
- Advocate for secure defaults in architectural decisions.
- Escalate complex findings to the central security team.
- Mentor peers on secure coding practices.

Champion programs succeed when they include explicit time allocation (10-20% of sprint capacity), career incentives, continuous training, and a community of practice across champions.

#### Threat Modeling in Sprints

Integrating threat modeling into agile sprints requires adaptation. Traditional STRIDE sessions spanning multiple days do not fit two-week iterations. The pragmatic approach:

1. **Feature kickoff**: 15-minute threat identification during story refinement. "What could go wrong? What data does this touch? What trust boundaries does this cross?"
2. **Lightweight DFD**: Sketch data flows on a whiteboard or Miro. Identify external entities, data stores, processes, and trust boundaries.
3. **Abuse stories**: Write negative user stories — "As an attacker, I want to enumerate user accounts via the password reset endpoint."
4. **Mitigation tasks**: Convert identified threats into backlog items with acceptance criteria.

### 1.6 Measuring DevSecOps Effectiveness

#### Mean Time to Remediate (MTTR)

MTTR measures the average elapsed time from vulnerability discovery to deployed fix. Track by severity:

| Severity | Target MTTR |
|----------|-------------|
| Critical | < 24 hours |
| High | < 7 days |
| Medium | < 30 days |
| Low | < 90 days |

#### Percentage of Vulnerabilities Caught Pre-Production

This metric measures the efficacy of shift-left. Calculate as:

```
pre_prod_catch_rate = vulns_found_in_ci_cd / (vulns_found_in_ci_cd + vulns_found_in_prod) * 100
```

A mature DevSecOps program targets > 95% pre-production catch rate.

#### Additional Metrics

- **Vulnerability escape rate**: Number of vulnerabilities found in production per release.
- **False positive rate**: Percentage of tool findings that are not actual vulnerabilities — impacts developer trust.
- **Security debt**: Total open vulnerability count weighted by severity and age.
- **Coverage ratio**: Percentage of repositories/services with full scanning enabled.
- **Time to onboard**: How quickly a new service gets full DevSecOps tooling.

---

## 2. Threat Modeling in SDLC

### 2.1 STRIDE Methodology with Practical Application

STRIDE is a threat classification framework developed at Microsoft. Each letter represents a category of threat that maps to a violated security property:

| Threat | Violated Property | Example |
|--------|------------------|---------|
| **S**poofing | Authentication | Attacker impersonates another user via stolen JWT |
| **T**ampering | Integrity | Attacker modifies request payload to change order amount |
| **R**epudiation | Non-repudiation | User denies performing a financial transaction, no audit log exists |
| **I**nformation Disclosure | Confidentiality | API returns full user objects including hashed passwords |
| **D**enial of Service | Availability | Attacker sends unbounded query causing OOM |
| **E**levation of Privilege | Authorization | Regular user accesses admin endpoint via IDOR |

**Practical Application — User Authentication Service:**

1. Draw the DFD: Browser → API Gateway → Auth Service → User Database.
2. Enumerate trust boundaries: Internet/DMZ, DMZ/Internal, Service/Database.
3. Apply STRIDE per element:
   - API Gateway: Spoofing (forged headers), DoS (rate limiting bypass).
   - Auth Service: Tampering (modified tokens), Information Disclosure (timing attacks on password comparison).
   - Database: Elevation of Privilege (SQL injection from auth service), Information Disclosure (unencrypted PII at rest).

4. For each identified threat, define:
   - Likelihood (1-5 scale).
   - Impact (1-5 scale).
   - Existing mitigations.
   - Residual risk and required additional controls.

### 2.2 PASTA — Process for Attack Simulation and Threat Analysis

PASTA is a seven-stage, risk-centric threat modeling methodology that emphasizes attacker perspective:

1. **Define Objectives**: Align with business risk appetite. What are the crown jewels?
2. **Define Technical Scope**: Enumerate components, technologies, protocols, data stores.
3. **Application Decomposition**: DFDs, use cases, entry points, assets.
4. **Threat Analysis**: Intelligence gathering — known CVEs affecting the stack, threat actor TTPs.
5. **Vulnerability Analysis**: Map known weaknesses to components (CVE databases, prior pen test findings).
6. **Attack Modeling**: Build attack trees. Model multi-step attack chains.
7. **Risk and Impact Analysis**: Quantify residual risk. Prioritize mitigations by cost-benefit ratio.

PASTA suits organizations that need business-aligned threat modeling. Its output maps directly to risk registers and executive reporting.

### 2.3 Attack Trees for Software Components

An attack tree models the hierarchical decomposition of an attacker's goal into sub-goals and leaf-level attack steps. Each node can be annotated with probability, cost, and required skill level.

```
Root: Exfiltrate Customer PII
├── [OR] Compromise Application Layer
│   ├── [AND] SQL Injection in Search Endpoint
│   │   ├── Find injectable parameter
│   │   └── Extract data via UNION-based or blind technique
│   ├── [OR] Exploit Broken Access Control
│   │   ├── IDOR on /api/users/{id}
│   │   └── Missing authorization check on export endpoint
│   └── [OR] Exploit Deserialization Flaw
├── [OR] Compromise Infrastructure
│   ├── [AND] Credential Stuffing on Admin Panel
│   │   ├── Obtain leaked credential list
│   │   └── Bypass rate limiting
│   └── [OR] Exploit Unpatched CVE on Edge Service
└── [OR] Supply Chain Attack
    ├── Compromise CI/CD pipeline
    └── Inject malicious dependency
```

Attack trees are particularly valuable for prioritizing security investments. If multiple leaf nodes are easy/cheap for an attacker and converge on the same root goal, the root goal requires architectural mitigation, not just patching individual leaves.

### 2.4 Data Flow Diagrams for Threat Identification

A DFD for threat modeling uses four element types:

- **External Entity** (rectangle): Users, external services, third-party APIs.
- **Process** (circle): Application logic, microservices, functions.
- **Data Store** (parallel lines): Databases, caches, file stores, queues.
- **Data Flow** (arrow): Communication between elements, annotated with protocol and data classification.
- **Trust Boundary** (dashed line): Separates zones of different trust levels.

Every data flow crossing a trust boundary is a candidate for threat analysis. Questions to ask:
- Is the flow authenticated? (Spoofing)
- Is the flow integrity-protected? (Tampering)
- Is the data encrypted in transit? (Information Disclosure)
- Can the flow be flooded? (DoS)
- Does the receiving process validate authorization? (Elevation of Privilege)

### 2.5 Tool-Assisted Threat Modeling

#### Microsoft Threat Modeling Tool

- Free, Windows-based GUI.
- Template-driven (Azure, generic, custom).
- Auto-generates threats based on DFD elements and stencil properties.
- Exports to HTML report for review.
- Limitation: Windows-only, enterprise focus, limited extensibility.

#### OWASP Threat Dragon

- Open source, cross-platform web application.
- JSON-based threat model storage (version-controllable).
- Supports STRIDE per-element and LINDDUN (privacy threats).
- Integration with GitHub for model storage.
- Suitable for teams wanting lightweight, code-adjacent threat models.

#### IriusRisk

- Commercial platform with extensive threat library.
- Integrates with Jira for automatic security requirement generation.
- Supports compliance mapping (PCI-DSS, HIPAA, SOC2).
- Questionnaire-driven approach for non-security practitioners.
- API for CI/CD integration — can fail builds if threat model is outdated.

### 2.6 Threat Modeling for Microservices, APIs, and Serverless

**Microservices challenges:**
- Explosion of inter-service trust boundaries.
- East-west traffic often implicitly trusted (violation of zero trust).
- Service mesh sidecars introduce new attack surface.
- Solution: Model each service boundary, enforce mTLS, apply STRIDE per service pair.

**API-specific threats:**
- Broken Object Level Authorization (BOLA/IDOR) — the #1 API vulnerability per OWASP API Top 10.
- Mass assignment — accepting unexpected fields in request bodies.
- Excessive data exposure — returning full objects when only subset needed.
- Rate limiting bypass — distributed attacks across multiple API keys.

**Serverless threats:**
- Event injection (malicious payloads in SQS, S3 events, API Gateway).
- Overprivileged execution roles.
- Shared tenancy risks in execution environment.
- Cold start timing attacks.
- Third-party dependency risks amplified (large node_modules in Lambda).

---

## 3. Source Code Security

### 3.1 Pre-Commit Hooks

Pre-commit hooks intercept `git commit` locally, allowing enforcement of security checks before code ever leaves the developer's machine.

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.6.0
    hooks:
      - id: detect-private-key
      - id: check-added-large-files
        args: ['--maxkb=500']

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts|tsx)$
        args: ['--fix']

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v3.1.0
    hooks:
      - id: prettier
        files: \.(js|ts|tsx|json|yaml|md)$
```

**Secrets detection** at pre-commit is critical because once a secret is committed, it exists in git history indefinitely (even after removal from HEAD). Tools like gitleaks use regex patterns and entropy analysis to catch:
- AWS access keys (`AKIA[0-9A-Z]{16}`)
- Private keys (PEM headers)
- Generic high-entropy strings resembling tokens
- Known secret formats for specific services (Stripe, Slack, GitHub)

### 3.2 Branch Protection Rules

Branch protection is the server-side enforcement counterpart to client-side pre-commit hooks. On GitHub:

- **Required reviews**: Minimum N approving reviews before merge. Dismiss stale reviews on new pushes.
- **Required status checks**: CI pipelines (SAST, SCA, tests) must pass. Specific check names can be required.
- **Signed commits**: Require GPG or SSH signature verification. Proves commit authorship.
- **Linear history**: Require rebase or squash merge. Prevents merge commits that can obscure malicious changes.
- **Code owner review**: CODEOWNERS file enforces that changes to security-sensitive paths require security team approval.
- **Restrict push access**: Only CI bots and specific maintainers can push to protected branches.

```
# .github/CODEOWNERS
# Security team must review these paths
/src/auth/                @org/security-team
/src/crypto/              @org/security-team
/infrastructure/          @org/platform-team @org/security-team
/.github/workflows/       @org/security-team
/Dockerfile               @org/security-team
*.tf                      @org/platform-team @org/security-team
```

### 3.3 Git Secrets Scanning

#### Gitleaks

The de facto standard for CI/CD secrets scanning. Scans git history, staged changes, or arbitrary directories.

```bash
# Scan entire repository history
gitleaks detect --source . --report-format json --report-path gitleaks-report.json

# Scan only staged changes (pre-commit)
gitleaks protect --staged

# Custom config
gitleaks detect --config .gitleaks.toml
```

Custom `.gitleaks.toml` rule:

```toml
[[rules]]
id = "internal-api-key"
description = "Internal API key pattern"
regex = '''INTERNAL_KEY_[A-Za-z0-9]{32,}'''
tags = ["internal", "key"]

[rules.allowlist]
paths = [
  '''(.*?)(test|spec|mock)(.*?)''',
]
```

#### TruffleHog

Specializes in finding secrets with high entropy and verified credentials. TruffleHog v3 can verify found credentials against live services (e.g., test if an AWS key is active).

```bash
# Scan git repo
trufflehog git file://. --only-verified --json

# Scan GitHub org
trufflehog github --org=myorg --only-verified
```

#### detect-secrets (Yelp)

Uses a baseline approach — generates a baseline file of known secrets (intentional test values), then alerts only on new additions.

```bash
# Generate baseline
detect-secrets scan > .secrets.baseline

# Audit baseline interactively
detect-secrets audit .secrets.baseline

# Check for new secrets in CI
detect-secrets scan --baseline .secrets.baseline
```

### 3.4 Monorepo vs Polyrepo Security Considerations

**Monorepo security:**
- Single CODEOWNERS file covers entire codebase — simpler governance.
- Secret leakage in one module exposes entire repo's CI secrets.
- Build system must scope permissions per module (Bazel, Nx).
- Dependency versions unified — single upgrade fixes all consumers.
- Larger blast radius from compromised contributor access.

**Polyrepo security:**
- Natural isolation — compromise of one repo does not expose others.
- Per-repo secrets scoping in CI (each repo has only its own credentials).
- CODEOWNERS per repo is simpler but harder to enforce organization-wide consistency.
- Dependency drift — different repos may pin different (vulnerable) versions.
- Cross-repo dependency management requires more tooling (Renovate multi-repo).

### 3.5 Dependency Management

#### Dependabot (GitHub Native)

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "org/security-team"
    labels:
      - "dependencies"
      - "security"
    ignore:
      - dependency-name: "aws-sdk"
        update-types: ["version-update:semver-major"]

  - package-ecosystem: "docker"
    directory: "/"
    schedule:
      interval: "daily"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### Renovate

More powerful than Dependabot — supports automerge for patch updates, grouping related dependencies, custom versioning schemes, and complex merge strategies.

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "security:openssf-scorecard"],
  "vulnerabilityAlerts": { "enabled": true },
  "packageRules": [
    {
      "matchUpdateTypes": ["patch"],
      "matchCurrentVersion": "!/^0/",
      "automerge": true
    },
    {
      "matchPackagePatterns": ["eslint", "prettier", "typescript"],
      "groupName": "linting and tooling"
    },
    {
      "matchPackagePatterns": ["*"],
      "matchUpdateTypes": ["major"],
      "reviewers": ["team:security"]
    }
  ]
}
```

---

## 4. Static Application Security Testing (SAST)

### 4.1 Semgrep

Semgrep is an open-source, multi-language static analysis engine that uses pattern-matching rules written in a YAML-based DSL. Its strength lies in the ability to write custom rules that encode organization-specific security requirements.

#### Custom Rule Writing

```yaml
rules:
  - id: dangerous-exec-from-user-input
    patterns:
      - pattern: |
          $FUNC(..., request.$METHOD(...), ...)
      - metavariable-regex:
          metavariable: $FUNC
          regex: (exec|spawn|execSync|spawnSync)
    message: >
      User input from request is passed directly to a shell execution function.
      This is a command injection vulnerability (CWE-78).
    severity: ERROR
    languages: [javascript, typescript]
    metadata:
      cwe: "CWE-78"
      owasp: "A03:2021"
      confidence: HIGH

  - id: hardcoded-jwt-secret
    pattern: |
      jwt.sign($PAYLOAD, "...", ...)
    message: >
      JWT is signed with a hardcoded secret string. Use environment variable or KMS.
    severity: ERROR
    languages: [javascript, typescript]
    fix: |
      jwt.sign($PAYLOAD, process.env.JWT_SECRET, ...)
```

#### Taint Tracking

Semgrep Pro supports taint analysis — tracking data flow from untrusted sources to dangerous sinks across function boundaries.

```yaml
rules:
  - id: sql-injection-taint
    mode: taint
    pattern-sources:
      - patterns:
          - pattern: req.query.$PARAM
      - patterns:
          - pattern: req.body.$PARAM
      - patterns:
          - pattern: req.params.$PARAM
    pattern-sinks:
      - patterns:
          - pattern: $DB.query($SINK, ...)
    pattern-sanitizers:
      - patterns:
          - pattern: $DB.escape(...)
    message: "Tainted user input reaches SQL query without sanitization"
    severity: ERROR
    languages: [javascript, typescript]
```

#### CI Integration (GitHub Actions)

```yaml
name: Semgrep SAST
on:
  pull_request: {}
  push:
    branches: [main]

jobs:
  semgrep:
    runs-on: ubuntu-latest
    container:
      image: semgrep/semgrep:latest
    steps:
      - uses: actions/checkout@v4
      - run: semgrep ci
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}
          SEMGREP_RULES: >-
            p/default
            p/owasp-top-ten
            p/javascript
            .semgrep/
```

### 4.2 CodeQL

CodeQL treats code as data — it compiles source into a relational database, then allows querying using the QL language (a Datalog variant). GitHub code scanning uses CodeQL as its backend.

#### QL Query Language

```ql
/**
 * @name SQL injection from user input
 * @description Building SQL queries from user-controlled input enables SQL injection.
 * @kind path-problem
 * @problem.severity error
 * @security-severity 9.8
 * @id js/sql-injection
 * @tags security
 *       external/cwe/cwe-089
 */

import javascript
import semmle.javascript.security.dataflow.SqlInjectionQuery
import DataFlow::PathGraph

from SqlInjection::Configuration cfg, DataFlow::PathNode source, DataFlow::PathNode sink
where cfg.hasFlowPath(source, sink)
select sink.getNode(), source, sink,
  "This SQL query depends on a $@.", source.getNode(), "user-provided value"
```

#### Custom Queries

Organizations write custom CodeQL queries for business-specific patterns:

```ql
/**
 * @name Direct database access outside repository layer
 * @description All database access must go through repository classes
 * @kind problem
 * @problem.severity warning
 */

import javascript

from MethodCallExpr call
where
  call.getMethodName().regexpMatch("(find|save|delete|update|query).*") and
  call.getReceiver().getType().getName().regexpMatch(".*Repository.*").not() and
  call.getFile().getRelativePath().regexpMatch(".*/(service|controller|handler)/.*")
select call, "Direct database access outside repository layer"
```

#### GitHub Code Scanning Integration

```yaml
name: CodeQL Analysis
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Weekly full scan

jobs:
  analyze:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
    strategy:
      matrix:
        language: ['javascript', 'python', 'go']
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
          queries: +security-extended,security-and-quality
          config-file: .github/codeql/codeql-config.yml
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
        with:
          category: "/language:${{ matrix.language }}"
```

### 4.3 SonarQube

SonarQube provides comprehensive code quality and security analysis with a web dashboard, quality gates, and project-level configuration.

**Quality Gates for Security:**

A quality gate defines the pass/fail criteria for a pipeline. Security-focused gate:

- Zero new critical vulnerabilities.
- Zero new high vulnerabilities.
- Security hotspots reviewed > 80%.
- No new security debt introduced.
- Coverage on new code > 80%.

**Custom Security Profiles:**

SonarQube allows creation of custom quality profiles that activate specific security rules per language. Organizations typically start with the "Sonar way" profile and add:
- Custom taint analysis rules for their frameworks.
- Organization-specific banned functions.
- Compliance-mapped rules (PCI-DSS requirement 6.5.x).

### 4.4 False Positive Management

False positives are the primary reason developers lose trust in SAST tooling. A tool with a 50% false positive rate will be ignored. Management strategies:

1. **Inline suppression with justification**: `// nosemgrep: rule-id -- reason: false positive, input is validated by middleware`
2. **Centralized suppression file**: Track all suppressions in a reviewable file.
3. **Triage workflow**:
   - Finding appears → Triaged by security champion.
   - Marked as: True Positive (fix), False Positive (suppress with reason), Accepted Risk (document and track).
4. **Rule tuning**: Adjust patterns to reduce noise. A rule that produces >30% FP needs refinement.
5. **Severity adjustment**: Lower confidence findings can be set to warning rather than blocker.

### 4.5 Language-Specific Tools

| Language | Tool | Key Capability |
|----------|------|----------------|
| Python | Bandit | AST-based, configurable severity, plugin architecture |
| Ruby | Brakeman | Rails-specific, confidence scoring, fingerprinting |
| Go | gosec | Go AST analysis, CWE mapping, sarif output |
| PHP | Psalm | Type inference, taint analysis, custom annotations |
| Java | SpotBugs + FindSecBugs | Bytecode analysis, security bug patterns |
| C/C++ | Flawfinder, cppcheck | Buffer overflow, format string, integer overflow |
| Rust | cargo-audit + clippy | Memory safety (already strong), logic bugs |

---

## 5. Software Composition Analysis (SCA)

### 5.1 Dependency Vulnerability Scanning

Modern applications comprise 70-90% third-party code. SCA tools identify known vulnerabilities (CVEs) in these dependencies.

#### Snyk

```bash
# Test for vulnerabilities
snyk test --all-projects --severity-threshold=high

# Monitor continuously (pushes to Snyk dashboard)
snyk monitor --all-projects

# Generate SBOM
snyk sbom --format=cyclonedx-json > sbom.json
```

#### npm audit

```bash
# Standard audit
npm audit --omit=dev

# JSON output for CI parsing
npm audit --json | jq '.vulnerabilities | to_entries[] | select(.value.severity == "critical")'

# Auto-fix where possible
npm audit fix --force  # Use cautiously — may introduce breaking changes
```

#### pip-audit

```bash
# Scan requirements
pip-audit -r requirements.txt --format json --output audit-results.json

# Scan installed packages
pip-audit --strict --desc on

# Fix automatically
pip-audit --fix
```

#### cargo-audit

```bash
# Scan Rust dependencies
cargo audit

# With advisory database update
cargo audit --deny warnings

# JSON output
cargo audit --json
```

### 5.2 License Compliance

License compliance is a legal requirement often overlooked in security programs. Using a GPL-licensed library in proprietary software without compliance can trigger legal action.

#### SPDX (Software Package Data Exchange)

SPDX is an ISO standard (ISO/IEC 5962:2021) for communicating software bill of materials including licensing.

#### CycloneDX SBOM

CycloneDX is an OWASP standard for SBOM, focused on security use cases:

```json
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "components": [
    {
      "type": "library",
      "name": "express",
      "version": "4.18.2",
      "purl": "pkg:npm/express@4.18.2",
      "licenses": [
        { "license": { "id": "MIT" } }
      ],
      "hashes": [
        {
          "alg": "SHA-256",
          "content": "a1b2c3d4..."
        }
      ]
    }
  ]
}
```

Generate SBOM in CI:

```yaml
- name: Generate SBOM
  run: |
    syft packages dir:. -o cyclonedx-json > sbom.json
    grype sbom:sbom.json --fail-on critical
```

### 5.3 Transitive Dependency Risks

Direct dependencies are visible in `package.json` or `requirements.txt`. Transitive dependencies (dependencies of dependencies) are often invisible yet equally dangerous. The `event-stream` incident (2018) demonstrated that a malicious actor can inject code several levels deep in the dependency tree.

Mitigation strategies:
- **Lock files**: Always commit lock files (`package-lock.json`, `poetry.lock`, `Cargo.lock`). Pin exact versions.
- **Flat dependency visualization**: Use `npm ls --all` or `pipdeptree` to visualize the full tree.
- **SCA on resolved tree**: Scan the lock file, not just the manifest.
- **Prune unused dependencies**: Regularly audit for unused packages (`depcheck`, `deptry`).
- **Shrink attack surface**: Prefer packages with fewer transitive dependencies.

### 5.4 Vulnerability Prioritization

Not all CVEs are equal. A critical CVE in a library function your code never calls presents zero practical risk. Prioritization strategies:

#### Reachability Analysis

Determine whether the vulnerable function is actually invoked by your code path:

```
CVE-2023-XXXXX in lodash@4.17.20 → _.template() function
Is _.template() reachable from your code? 
  NO → Low priority (still update, but not urgent)
  YES → Critical priority
```

Tools: Snyk reachability analysis, Endor Labs reachable vulnerabilities.

#### Exploit Prediction Scoring System (EPSS)

EPSS provides a probability score (0-1) that a CVE will be exploited in the wild within the next 30 days. Combine with CVSS for practical prioritization:

- CVSS Critical + EPSS > 0.5 → Immediate action
- CVSS Critical + EPSS < 0.1 → Within SLA
- CVSS Low + EPSS < 0.01 → Backlog

### 5.5 Automated PR Creation for Dependency Updates

Configure automation to create PRs for vulnerable dependencies:

```yaml
# GitHub Actions: Auto-merge Dependabot security patches
name: Auto-merge Dependabot
on:
  pull_request:
    types: [opened, synchronize]

permissions:
  pull-requests: write
  contents: write

jobs:
  auto-merge:
    runs-on: ubuntu-latest
    if: github.actor == 'dependabot[bot]'
    steps:
      - uses: actions/checkout@v4
      - name: Fetch Dependabot metadata
        id: metadata
        uses: dependabot/fetch-metadata@v2
        with:
          github-token: ${{ secrets.GITHUB_TOKEN }}
      - name: Auto-merge patch updates
        if: steps.metadata.outputs.update-type == 'version-update:semver-patch'
        run: gh pr merge --auto --squash "$PR_URL"
        env:
          PR_URL: ${{ github.event.pull_request.html_url }}
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### 5.6 Policy Enforcement

Block builds when critical vulnerabilities are present:

```yaml
# GitLab CI dependency scanning with policy
dependency_scanning:
  stage: test
  image: registry.gitlab.com/gitlab-org/security-products/analyzers/gemnasium:latest
  script:
    - /analyzer run
  artifacts:
    reports:
      dependency_scanning: gl-dependency-scanning-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

# Fail pipeline on critical findings
check_vulnerabilities:
  stage: verify
  script: |
    CRITICAL=$(jq '[.vulnerabilities[] | select(.severity == "Critical")] | length' gl-dependency-scanning-report.json)
    if [ "$CRITICAL" -gt 0 ]; then
      echo "ERROR: $CRITICAL critical vulnerabilities found. Pipeline blocked."
      exit 1
    fi
```

---

## 6. Dynamic Application Security Testing (DAST)

### 6.1 OWASP ZAP

ZAP (Zed Attack Proxy) is the most widely used open-source DAST tool. It performs automated scanning against running applications, identifying runtime vulnerabilities that SAST cannot detect (misconfigured headers, authentication flaws, CORS issues).

#### CI/CD Integration

```yaml
name: DAST with ZAP
on:
  push:
    branches: [main]

jobs:
  zap-scan:
    runs-on: ubuntu-latest
    services:
      app:
        image: myapp:${{ github.sha }}
        ports:
          - 8080:8080
    steps:
      - uses: actions/checkout@v4
      - name: ZAP Full Scan
        uses: zaproxy/action-full-scan@v0.10.0
        with:
          target: 'http://app:8080'
          rules_file_name: '.zap/rules.tsv'
          cmd_options: '-a -j -l WARN'
      - name: Upload Report
        uses: actions/upload-artifact@v4
        with:
          name: zap-report
          path: report_html.html
```

#### API Scanning

```yaml
# ZAP API scan with OpenAPI spec
- name: ZAP API Scan
  uses: zaproxy/action-api-scan@v0.7.0
  with:
    target: 'http://app:8080/openapi.json'
    format: openapi
    cmd_options: >-
      -c .zap/api-scan.conf
      -r api-scan-report.html
      -x api-scan-report.xml
```

#### Authentication Configuration

```yaml
# .zap/context.yaml
contexts:
  - name: "Authenticated Scan"
    urls:
      - "http://app:8080"
    authentication:
      method: "json"
      parameters:
        loginUrl: "http://app:8080/api/auth/login"
        loginRequestData: '{"email":"{%username%}","password":"{%password%}"}'
      verification:
        method: "response"
        loggedInRegex: "\\Qaccess_token\\E"
    users:
      - name: "test-user"
        credentials:
          username: "testuser@example.com"
          password: "${ZAP_AUTH_PASSWORD}"
```

### 6.2 Nuclei

Nuclei is a template-based vulnerability scanner designed for speed and extensibility. It excels at checking for known misconfigurations, exposed panels, default credentials, and CVE-specific exploits.

#### Template-Based Scanning

```yaml
# Custom Nuclei template for internal security check
id: internal-debug-endpoint-exposed
info:
  name: Debug Endpoint Exposed
  author: internal-security
  severity: high
  tags: internal,misconfiguration
  description: Application debug endpoints should not be accessible in production

http:
  - method: GET
    path:
      - "{{BaseURL}}/debug/pprof/"
      - "{{BaseURL}}/_debug/vars"
      - "{{BaseURL}}/actuator/env"
      - "{{BaseURL}}/__debug"
    matchers-condition: or
    matchers:
      - type: status
        status:
          - 200
      - type: word
        words:
          - "goroutine"
          - "heap"
          - "activeProfiles"
        condition: or
```

#### CI Integration

```yaml
- name: Run Nuclei
  run: |
    nuclei -u http://app:8080 \
      -t nuclei-templates/http/misconfiguration/ \
      -t .nuclei/custom-templates/ \
      -severity critical,high \
      -json-export nuclei-results.json \
      -silent
    
    # Fail if critical findings
    CRITICAL=$(jq '[.[] | select(.info.severity == "critical")] | length' nuclei-results.json)
    if [ "$CRITICAL" -gt 0 ]; then
      echo "Critical vulnerabilities found"
      exit 1
    fi
```

### 6.3 Burp Suite Enterprise

Burp Suite Enterprise is the CI/CD-integrated version of Burp Suite Professional. It provides:
- Scheduled recurring scans against staging environments.
- CI/CD API for triggering scans on deployment.
- Vulnerability deduplication across scans.
- Confidence-based severity that reduces false positives.
- Integration with Jira for automatic ticket creation.

### 6.4 DAST for APIs

API-specific DAST requires schema awareness:

- **OpenAPI/Swagger**: Scanner generates requests based on endpoint definitions, parameter types, and example values.
- **GraphQL**: Introspection-based scanning, testing for excessive query depth, batch attacks, and field-level authorization.
- **gRPC**: Protocol buffer definition parsing, reflection API abuse testing.

Authentication handling is critical for API DAST — scanner must maintain valid sessions, handle token refresh, and test authorization boundaries (attempt to access resources belonging to other users).

### 6.5 IAST — Interactive Application Security Testing

IAST instruments the running application (via agent) to observe code execution during testing. It combines the precision of SAST (exact code location) with the runtime context of DAST (real exploitation paths).

**Contrast Security** is the leading IAST platform:
- Agent deployed alongside application (Java, .NET, Node.js, Python, Go, Ruby).
- Observes data flow through the application in real-time during functional testing.
- Zero false positives for taint-based findings (data actually flows from source to sink).
- Identifies vulnerabilities during normal QA testing — no separate security scan needed.
- Reports exact stack trace and data flow path.

IAST limitations:
- Requires agent deployment (performance overhead, deployment complexity).
- Only finds vulnerabilities in code paths exercised during testing.
- Not suitable for third-party applications without source access.

---

## 7. Container and Infrastructure Security in Pipeline

### 7.1 Dockerfile Linting

#### Hadolint

```bash
# Lint Dockerfile
hadolint Dockerfile --format json

# With custom ignore rules
hadolint --ignore DL3008 --ignore DL3009 Dockerfile

# Trusted registries only
hadolint --trusted-registry docker.io --trusted-registry ghcr.io Dockerfile
```

Key rules enforced:
- `DL3007`: Use specific tag, not `latest`.
- `DL3008`: Pin package versions in apt-get.
- `DL3002`: Do not run as root (last USER should not be root).
- `DL3018`: Pin package versions in apk.
- `DL4006`: Set `SHELL` option for pipefail.

#### Dockle

Dockle scans built images for CIS Docker Benchmark compliance:

```bash
dockle --exit-code 1 --exit-level fatal myimage:latest
```

Checks include: no credentials in environment variables, no SETUID binaries, appropriate file permissions, health check defined.

### 7.2 Container Image Scanning in CI

#### Trivy

Trivy is the most comprehensive open-source container scanner, covering OS packages, language dependencies, IaC misconfigurations, and secrets in a single tool.

```yaml
name: Container Security
on:
  push:
    branches: [main]
  pull_request:

jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t myapp:${{ github.sha }} .
      
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: 'myapp:${{ github.sha }}'
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
          ignore-unfixed: true
      
      - name: Upload Trivy scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
```

#### Trivy CLI Commands

```bash
# Scan container image
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:latest

# Scan filesystem (IaC + dependencies)
trivy fs --scanners vuln,misconfig,secret .

# Scan Kubernetes cluster
trivy k8s --report summary cluster

# Generate SBOM from image
trivy image --format cyclonedx --output sbom.json myapp:latest

# Scan with custom policy
trivy image --policy ./policies/ --exit-code 1 myapp:latest
```

#### Grype

```bash
# Scan image
grype myapp:latest --fail-on critical

# Scan SBOM
grype sbom:./sbom.json

# Output formats
grype myapp:latest -o json > grype-results.json
grype myapp:latest -o sarif > grype-results.sarif
```

### 7.3 Infrastructure as Code Scanning

#### Checkov

```bash
# Scan Terraform
checkov -d ./terraform/ --framework terraform --output json --compact

# Scan Kubernetes manifests
checkov -d ./k8s/ --framework kubernetes

# Scan Dockerfile
checkov --file Dockerfile --framework dockerfile

# Custom policy
checkov -d . --external-checks-dir ./custom-policies/
```

Custom Checkov policy (Python):

```python
from checkov.terraform.checks.resource.base_resource_check import BaseResourceCheck
from checkov.common.models.enums import CheckResult, CheckCategories

class S3BucketEncryption(BaseResourceCheck):
    def __init__(self):
        name = "Ensure S3 bucket has server-side encryption enabled"
        id = "CUSTOM_AWS_001"
        supported_resources = ['aws_s3_bucket']
        categories = [CheckCategories.ENCRYPTION]
        super().__init__(name=name, id=id, categories=categories,
                        supported_resources=supported_resources)

    def scan_resource_conf(self, conf):
        if 'server_side_encryption_configuration' in conf:
            return CheckResult.PASSED
        return CheckResult.FAILED

check = S3BucketEncryption()
```

#### tfsec (now part of Trivy)

```bash
# Scan Terraform directory
tfsec ./terraform/ --format json --out results.json

# With custom check severity overrides
tfsec ./terraform/ --tfvars-file terraform.tfvars --minimum-severity HIGH
```

#### KICS (Keeping Infrastructure as Code Secure)

```bash
# Multi-framework scan
kics scan -p ./infrastructure/ \
  --type Terraform,Kubernetes,Dockerfile,CloudFormation \
  --output-path ./results/ \
  --report-formats json,sarif \
  --fail-on high,critical
```

### 7.4 Kubernetes Manifest Scanning

#### kubesec

```bash
# Scan deployment manifest
kubesec scan deployment.yaml

# Returns score with recommendations
# Score < 0 indicates critical security issues
```

#### kube-linter

```bash
# Lint all manifests in directory
kube-linter lint ./k8s/

# With custom checks config
kube-linter lint ./k8s/ --config .kube-linter.yaml
```

```yaml
# .kube-linter.yaml
checks:
  addAllBuiltIn: true
  exclude:
    - "unset-cpu-requirements"  # Accept for dev environments
customChecks:
  - name: "require-security-context"
    template: "required-annotation"
    params:
      key: "security.example.com/reviewed"
```

### 7.5 Policy Enforcement — OPA/Gatekeeper/Kyverno

#### OPA (Open Policy Agent) in CI

OPA Rego policies can be evaluated during CI to enforce organizational standards before deployment:

```rego
# policy/kubernetes/deny-privileged.rego
package kubernetes.admission

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container '%v' must not run as privileged", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.securityContext.runAsNonRoot
    msg := sprintf("Container '%v' must set runAsNonRoot: true", [container.name])
}

deny[msg] {
    input.kind == "Deployment"
    container := input.spec.template.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container '%v' must set memory limits", [container.name])
}
```

CI integration:

```yaml
- name: Evaluate OPA policies
  run: |
    for manifest in k8s/*.yaml; do
      RESULT=$(opa eval --input "$manifest" --data policy/ "data.kubernetes.admission.deny" --format pretty)
      if [ "$RESULT" != "[]" ]; then
        echo "Policy violation in $manifest: $RESULT"
        exit 1
      fi
    done
```

#### Kyverno in CI (pre-admission validation)

```yaml
# kyverno-policy.yaml
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-labels
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-required-labels
      match:
        any:
          - resources:
              kinds:
                - Deployment
                - StatefulSet
      validate:
        message: "The label 'app.kubernetes.io/managed-by' is required."
        pattern:
          metadata:
            labels:
              app.kubernetes.io/managed-by: "?*"

    - name: restrict-image-registries
      match:
        any:
          - resources:
              kinds:
                - Pod
      validate:
        message: "Images must come from approved registries"
        pattern:
          spec:
            containers:
              - image: "ghcr.io/* | registry.internal.example.com/*"
```

```bash
# Validate manifests against Kyverno policies in CI
kyverno apply ./policies/ --resource ./k8s/deployment.yaml
```

### 7.6 Cloud Security Posture in Pipeline

#### Prowler (AWS)

```yaml
- name: Run Prowler
  run: |
    prowler aws \
      --severity critical high \
      --compliance cis_2.0_aws \
      --output-formats json-ocsf \
      --output-directory ./prowler-results/ \
      --status FAIL
```

#### ScoutSuite (Multi-cloud)

```bash
# Assess AWS account
scout aws --report-dir ./scout-results/ --no-browser

# Assess Azure subscription  
scout azure --report-dir ./scout-results/ --no-browser

# Assess GCP project
scout gcp --report-dir ./scout-results/ --no-browser
```

---

## 8. Secrets Management in CI/CD

### 8.1 Secrets in CI Systems

#### GitHub Actions Secrets

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Environment-scoped secrets
    steps:
      - name: Deploy
        env:
          DB_PASSWORD: ${{ secrets.DB_PASSWORD }}
          API_KEY: ${{ secrets.API_KEY }}
        run: ./deploy.sh
```

Security properties:
- Secrets are encrypted at rest (libsodium sealed box).
- Masked in logs (but partial exposure possible via careful string manipulation).
- Not available to forked repository PR workflows by default.
- Environment secrets require deployment approval.

#### GitLab CI Variables

```yaml
deploy:
  stage: deploy
  environment:
    name: production
  variables:
    DB_PASSWORD: $DB_PASSWORD  # From CI/CD settings
  script:
    - echo "Deploying with credentials"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

GitLab variable protections:
- **Protected**: Only available on protected branches/tags.
- **Masked**: Hidden in job logs.
- **Environment scope**: Limited to specific environments.

### 8.2 Secrets Management Platforms

#### HashiCorp Vault Integration

```yaml
# GitHub Actions with Vault
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Import Secrets from Vault
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.example.com
          method: jwt
          role: github-actions-role
          jwtGithubAudience: https://github.com/my-org
          secrets: |
            secret/data/production/db password | DB_PASSWORD ;
            secret/data/production/api key | API_KEY ;
            secret/data/production/tls cert | TLS_CERT

      - name: Use secrets
        run: |
          # Secrets are now available as environment variables
          echo "Connecting to database..."
```

Vault policy for CI/CD:

```hcl
# vault-policy.hcl
path "secret/data/production/*" {
  capabilities = ["read"]
}

path "pki/issue/service-cert" {
  capabilities = ["create", "update"]
}

path "database/creds/app-readonly" {
  capabilities = ["read"]
}

# Deny access to admin paths
path "secret/data/admin/*" {
  capabilities = ["deny"]
}
```

#### AWS Secrets Manager

```yaml
- name: Get secrets from AWS
  uses: aws-actions/aws-secretsmanager-get-secrets@v2
  with:
    secret-ids: |
      prod/database
      prod/api-keys
    parse-json-secrets: true
```

#### Dynamic Secrets with Vault

Dynamic secrets are generated on-demand with automatic expiration. No long-lived credentials exist in any system:

```bash
# Generate short-lived database credentials
vault read database/creds/app-readonly
# Returns: username=v-github-app-readonly-abc123, password=<random>, lease_duration=1h

# Generate short-lived AWS credentials
vault read aws/creds/deploy-role
# Returns: access_key=AKIA..., secret_key=..., lease_duration=30m
```

### 8.3 OIDC Federation — Keyless Authentication

OIDC federation eliminates the need to store cloud credentials in CI/CD systems entirely. The CI system's identity token is exchanged for short-lived cloud credentials.

#### GitHub Actions → AWS (OIDC)

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/github-actions-deploy
          aws-region: us-east-1
          # No access key or secret key needed!
```

AWS trust policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:my-org/my-repo:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

#### GitHub Actions → GCP (Workload Identity Federation)

```yaml
- uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/123456/locations/global/workloadIdentityPools/github/providers/my-repo'
    service_account: 'deploy@my-project.iam.gserviceaccount.com'
```

### 8.4 Detecting Hardcoded Secrets

Detection approaches:
- **Regex patterns**: Match known secret formats (AWS keys, GitHub tokens, Stripe keys).
- **Entropy analysis**: Flag strings with high Shannon entropy (random-looking strings).
- **Keyword proximity**: Secret-like strings near variable names like `password`, `secret`, `token`, `key`.
- **Known formats**: Base64-encoded structures, JWT format, PEM headers.
- **Verified secrets**: Attempt to validate the secret against the service (TruffleHog verified scanning).

### 8.5 Secret Rotation Automation

```yaml
# Automated secret rotation via scheduled pipeline
name: Rotate Secrets
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly rotation

jobs:
  rotate:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Authenticate to Vault
        uses: hashicorp/vault-action@v3
        with:
          url: https://vault.example.com
          method: jwt
          role: secret-rotator

      - name: Rotate database credentials
        run: |
          vault write -f database/rotate-root/production-db
          echo "Database root credentials rotated"

      - name: Rotate API keys
        run: |
          # Generate new key, update service, revoke old key
          NEW_KEY=$(vault write -format=json transit/datakey/plaintext/api-key | jq -r '.data.plaintext')
          # Update the service configuration
          vault kv put secret/production/api-key value="$NEW_KEY"
```

---

## 9. Supply Chain Security

### 9.1 SLSA Framework (Supply-chain Levels for Software Artifacts)

SLSA (pronounced "salsa") defines a graduated framework for supply chain integrity:

#### Level 1 — Documentation of Build Process

- Build process is documented.
- Provenance is generated (though unsigned).
- Minimal protection — establishes baseline.

#### Level 2 — Signed Provenance

- Build service generates authenticated provenance.
- Provenance is tamper-evident (signed).
- Consumer can verify who built the artifact and from what source.

#### Level 3 — Hardened Build Platform

- Build runs on an isolated, ephemeral environment.
- Build platform prevents secret exfiltration.
- Source integrity verified (e.g., from VCS tag, not arbitrary input).
- Provenance is non-falsifiable — build service is trusted to report accurately.

#### Level 4 — Hermetic, Reproducible Builds

- Build is hermetic — no network access during build, all inputs declared.
- Build is reproducible — same inputs produce bit-for-bit identical outputs.
- Two-party review required for source changes.
- Highest assurance level.

#### SLSA Provenance in GitHub Actions

```yaml
name: Build with SLSA Provenance
on:
  push:
    tags: ['v*']

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      hashes: ${{ steps.hash.outputs.hashes }}
    steps:
      - uses: actions/checkout@v4
      - name: Build artifact
        run: |
          go build -o myapp ./cmd/myapp
      - name: Generate hash
        id: hash
        run: |
          HASH=$(sha256sum myapp | base64 -w0)
          echo "hashes=$HASH" >> "$GITHUB_OUTPUT"
      - uses: actions/upload-artifact@v4
        with:
          name: myapp
          path: myapp

  provenance:
    needs: [build]
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.0.0
    with:
      base64-subjects: "${{ needs.build.outputs.hashes }}"
      upload-assets: true
```

### 9.2 Sigstore

Sigstore provides keyless code signing infrastructure — developers sign artifacts using their OIDC identity (e.g., GitHub OIDC token) without managing long-lived signing keys.

#### Cosign — Container Image Signing

```bash
# Sign container image (keyless, uses OIDC)
cosign sign ghcr.io/my-org/myapp@sha256:abc123...

# Verify signature
cosign verify ghcr.io/my-org/myapp@sha256:abc123... \
  --certificate-identity='https://github.com/my-org/myapp/.github/workflows/release.yml@refs/tags/v1.0.0' \
  --certificate-oidc-issuer='https://token.actions.githubusercontent.com'

# Sign with key (traditional)
cosign sign --key cosign.key ghcr.io/my-org/myapp@sha256:abc123...

# Attach SBOM to image
cosign attach sbom --sbom sbom.json ghcr.io/my-org/myapp@sha256:abc123...

# Verify SBOM attachment
cosign verify-attestation ghcr.io/my-org/myapp@sha256:abc123... \
  --type cyclonedx \
  --certificate-identity-regexp='.*' \
  --certificate-oidc-issuer='https://token.actions.githubusercontent.com'
```

#### Rekor Transparency Log

Rekor is an immutable, append-only transparency log for software supply chain metadata. All Sigstore operations are recorded in Rekor, providing:
- Public auditability of all signing events.
- Tamper-evident record — if an entry is modified, Merkle tree verification fails.
- Timestamp authority — proves artifact was signed at a specific time.

```bash
# Search Rekor for entries related to an artifact
rekor-cli search --sha sha256:abc123...

# Get entry details
rekor-cli get --uuid <entry-uuid> --format json
```

#### Fulcio Certificate Authority

Fulcio issues short-lived code signing certificates bound to OIDC identities. The certificate is valid for ~10 minutes — just long enough to sign the artifact. This eliminates the key management problem: there are no long-lived signing keys to protect, rotate, or revoke.

### 9.3 Software Attestation

#### in-toto

in-toto is a framework for securing the software supply chain by verifying that each step in the pipeline was performed as intended by the authorized party.

```json
{
  "_type": "https://in-toto.io/Statement/v1",
  "subject": [
    {
      "name": "myapp",
      "digest": { "sha256": "abc123..." }
    }
  ],
  "predicateType": "https://slsa.dev/provenance/v1",
  "predicate": {
    "buildDefinition": {
      "buildType": "https://github.com/slsa-framework/slsa-github-generator/generic@v1",
      "externalParameters": {
        "workflow": {
          "ref": "refs/tags/v1.0.0",
          "repository": "https://github.com/my-org/myapp"
        }
      }
    },
    "runDetails": {
      "builder": {
        "id": "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@refs/tags/v2.0.0"
      },
      "metadata": {
        "invocationId": "https://github.com/my-org/myapp/actions/runs/12345",
        "startedOn": "2025-01-15T10:30:00Z",
        "finishedOn": "2025-01-15T10:35:00Z"
      }
    }
  }
}
```

### 9.4 Dependency Confusion Attacks

Dependency confusion exploits the resolution order of package managers. If an internal package name is also registered on a public registry with a higher version number, the package manager may pull the malicious public version.

**Prevention:**

```ini
# .npmrc — scope internal packages to private registry
@my-org:registry=https://npm.internal.example.com/
//npm.internal.example.com/:_authToken=${NPM_INTERNAL_TOKEN}

# Prevent public fallback for scoped packages
@my-org:always-auth=true
```

```toml
# pip.conf — restrict index for internal packages
[global]
index-url = https://pypi.internal.example.com/simple/
extra-index-url = https://pypi.org/simple/

# Better: Use --no-deps and explicit requirements
```

```yaml
# Artifactory virtual repository configuration
# Priority: internal repo checked first, public fallback second
# Block external packages matching internal namespace patterns
```

Additional defenses:
- Register placeholder packages on public registries for all internal package names.
- Use scoped packages (`@org/package-name`) which cannot be confused with unscoped public packages.
- Configure package manager to require explicit registry per scope.
- Monitor public registries for packages matching internal naming patterns.

### 9.5 Typosquatting Detection

Typosquatting creates malicious packages with names similar to popular packages (`lodahs` instead of `lodash`, `reqeusts` instead of `requests`).

Detection strategies:
- Levenshtein distance comparison against popular package lists.
- Creation date correlation — newly created packages with names similar to established packages are suspicious.
- Download count anomalies — legitimate packages have organic growth curves.
- Maintainer analysis — single-maintainer packages mimicking team-maintained popular packages.
- Content analysis — minimal code with post-install scripts executing network calls.

Tools: `socket.dev`, `npm-audit-resolver`, `pip-audit` with typosquatting checks.

### 9.6 CI/CD System Hardening

#### Runner Isolation

```yaml
# GitHub Actions: Use ephemeral self-hosted runners
jobs:
  build:
    runs-on: [self-hosted, ephemeral, linux, x64]
    # Runner is destroyed after job completion
    # No state persists between jobs
    # Network access restricted to necessary endpoints
```

#### Approval Gates

```yaml
# Require manual approval for production deployments
jobs:
  deploy-prod:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://myapp.example.com
    # Environment configured with:
    # - Required reviewers
    # - Wait timer (e.g., 15 minutes)
    # - Deployment branch restrictions (main only)
    steps:
      - name: Deploy
        run: ./deploy-production.sh
```

#### Prevent Poisoned Pipeline Execution

```yaml
# Only run workflows from the default branch, not from PR author's fork
on:
  pull_request_target:  # Runs in context of base branch, not PR branch
    types: [opened, synchronize]

jobs:
  # Safe: checkout base branch code for workflow logic
  # Dangerous: never checkout PR head for untrusted execution
  safe-job:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.base.sha }}  # Base branch, not PR
```

---

## 10. Pipeline Security Architecture

### 10.1 Secure CI/CD Design Principles

#### Ephemeral Runners

Runners should be stateless and destroyed after each job. This prevents:
- Credential persistence from previous jobs.
- Malware persistence across builds.
- Data exfiltration via cached artifacts.
- Cross-tenant contamination in shared runners.

Implementation: Use container-based runners (each job gets a fresh container) or VM-based runners with automatic teardown.

#### Network Isolation

```
┌─────────────────────────────────────────┐
│ CI/CD Network Zone                       │
│                                          │
│  ┌──────────┐    ┌──────────────────┐   │
│  │  Runner   │    │  Artifact Store   │   │
│  │ (Ephemeral)│   │  (Internal only)  │   │
│  └──────────┘    └──────────────────┘   │
│       │                    │             │
│       ▼                    ▼             │
│  ┌──────────────────────────────┐       │
│  │    Internal Network Only      │       │
│  │  - Package registries         │       │
│  │  - Vault                      │       │
│  │  - Container registry         │       │
│  └──────────────────────────────┘       │
│                                          │
└──────────────┬───────────────────────────┘
               │ Egress filtered
               ▼
         ┌───────────┐
         │  Internet  │ (Only specific URLs allowed)
         └───────────┘
```

#### Credential Scoping

- Each pipeline step should receive only the credentials it needs (principle of least privilege).
- Use step-scoped environment variables, not job-wide or workflow-wide.
- Credentials for production should only be accessible from production environment pipelines.
- Read-only credentials for build steps; write credentials only for deploy steps.

### 10.2 GitHub Actions Security

#### Reusable Workflows

Centralize security-critical logic in reusable workflows controlled by the security team:

```yaml
# .github/workflows/secure-deploy.yml (in a shared org repo)
name: Secure Deployment
on:
  workflow_call:
    inputs:
      environment:
        required: true
        type: string
      image-ref:
        required: true
        type: string
    secrets:
      DEPLOY_TOKEN:
        required: true

jobs:
  verify-and-deploy:
    runs-on: ubuntu-latest
    environment: ${{ inputs.environment }}
    steps:
      - name: Verify image signature
        run: |
          cosign verify ${{ inputs.image-ref }} \
            --certificate-identity-regexp='https://github.com/my-org/.*' \
            --certificate-oidc-issuer='https://token.actions.githubusercontent.com'

      - name: Scan image before deploy
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: ${{ inputs.image-ref }}
          exit-code: '1'
          severity: 'CRITICAL'

      - name: Deploy
        run: |
          kubectl set image deployment/app app=${{ inputs.image-ref }}
```

Consuming repository:

```yaml
jobs:
  deploy:
    uses: my-org/shared-workflows/.github/workflows/secure-deploy.yml@v1.0.0
    with:
      environment: production
      image-ref: ghcr.io/my-org/myapp@sha256:abc123
    secrets:
      DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
```

#### Pinned Actions

Never use `@main` or floating tags for third-party actions. Pin to specific commit SHAs:

```yaml
# DANGEROUS: Tag can be moved to point to malicious code
- uses: actions/checkout@v4

# SAFE: Pinned to immutable commit SHA
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
```

Use Dependabot or Renovate to manage action version updates:

```yaml
# .github/dependabot.yml
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
```

#### GITHUB_TOKEN Permissions

Apply least privilege to the automatic GITHUB_TOKEN:

```yaml
# Workflow-level (restrictive default)
permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write  # Only this job needs package write
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
```

Organization-level: Set default GITHUB_TOKEN permission to `read` for all repositories. Jobs that need write must explicitly request it.

### 10.3 GitLab CI Security

#### Protected Variables and Runners

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - security
  - deploy

variables:
  # Non-sensitive defaults
  DOCKER_BUILDKIT: "1"

build:
  stage: build
  tags:
    - shared-runner  # Non-privileged runner
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

security_scan:
  stage: security
  tags:
    - security-runner  # Dedicated security runner with scanning tools
  script:
    - trivy image --exit-code 1 --severity CRITICAL,HIGH $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy_production:
  stage: deploy
  tags:
    - deploy-runner  # Privileged runner with production access
  environment:
    name: production
    url: https://app.example.com
  variables:
    KUBE_CONTEXT: production-cluster  # Protected variable
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual  # Manual trigger for production
  resource_group: production  # Prevents concurrent deploys
```

#### GitLab Protected Environments

- **Protected variables**: Only injected into jobs running on protected branches or tags.
- **Protected runners**: Dedicated runners that only execute jobs from protected refs.
- **Environment approvals**: Require specific users/groups to approve deployments.
- **Deployment freeze windows**: Block deployments during maintenance windows.

### 10.4 Jenkins Hardening

Jenkins, while legacy by modern standards, remains widely deployed. Its security surface is large and requires explicit hardening.

#### Controller Isolation

- Run Jenkins controller with minimal plugins (reduce attack surface).
- Never execute builds on the controller node — use agent nodes exclusively.
- Isolate controller network from the internet (reverse proxy with authentication).
- Enable CSRF protection (crumb issuer).
- Disable CLI over remoting (common attack vector).
- Disable script console for non-admin users.

#### Agent Security

```groovy
// Jenkinsfile with security controls
pipeline {
    agent {
        kubernetes {
            yaml '''
                apiVersion: v1
                kind: Pod
                spec:
                  containers:
                    - name: build
                      image: build-tools:pinned-sha256
                      securityContext:
                        runAsNonRoot: true
                        readOnlyRootFilesystem: true
                        allowPrivilegeEscalation: false
                        capabilities:
                          drop: [ALL]
                      resources:
                        limits:
                          memory: "2Gi"
                          cpu: "2"
                  serviceAccountName: jenkins-build-sa
                  automountServiceAccountToken: false
            '''
        }
    }
    
    environment {
        // Credentials from Jenkins credential store
        DB_CREDS = credentials('production-db-credentials')
        // Short-lived token from Vault
        VAULT_TOKEN = vault path: 'secret/data/ci', key: 'token'
    }
    
    stages {
        stage('Build') {
            steps {
                sh 'make build'
            }
        }
        stage('Security Scan') {
            steps {
                sh 'trivy fs --exit-code 1 --severity CRITICAL .'
                sh 'semgrep --config auto --error .'
            }
        }
        stage('Deploy') {
            when {
                branch 'main'
            }
            input {
                message "Deploy to production?"
                submitter "deploy-approvers"
            }
            steps {
                sh './deploy.sh'
            }
        }
    }
}
```

#### Credential Management

- Use Jenkins Credentials Plugin with folder-scoped credentials.
- Never store credentials in Jenkinsfile or job configuration.
- Use credential binding to inject secrets as environment variables scoped to specific steps.
- Mask secrets in console output.
- Audit credential usage via CloudBees Audit Trail plugin.

### 10.5 Pipeline as Code Security

#### Preventing Malicious PRs from Executing Dangerous Workflows

The fundamental tension: CI must build PR code to validate it, but building arbitrary code grants code execution on CI infrastructure. Attack scenario: attacker submits a PR that modifies the CI workflow to exfiltrate secrets.

**GitHub Actions mitigations:**

1. **`pull_request` vs `pull_request_target`**: 
   - `pull_request` runs in the context of the merge commit with read-only access. Workflow changes in the PR are executed. Safe for untrusted PRs if secrets are not exposed.
   - `pull_request_target` runs in the context of the base branch. Workflow from base branch executes. Secrets available. Dangerous if you checkout PR code and execute it.

2. **Restrict workflow modifications**: Require CODEOWNERS approval for `.github/workflows/` changes.

3. **Separate build from deploy**: Build jobs (untrusted code) run with no secrets. Deploy jobs (trusted code from main) run with secrets after merge.

```yaml
# Secure pattern: build on PR, deploy on merge
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  build:
    # Runs for both PRs and pushes to main
    # No secrets needed for build/test
    runs-on: ubuntu-latest
    permissions:
      contents: read
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - run: make build
      - run: make test
      - run: make security-scan

  deploy:
    # Only runs after merge to main
    needs: build
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    environment: production
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - name: Authenticate to cloud
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/deploy
          aws-region: us-east-1
      - run: make deploy
```

**GitLab CI mitigations:**

```yaml
# Restrict who can trigger production pipelines
deploy_production:
  stage: deploy
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: never  # Never deploy from MR pipeline
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
  environment:
    name: production
    deployment_tier: production
  # Protected environment requires specific role/group approval
```

#### Immutable Pipeline Definitions

For maximum security, pipeline definitions should be:
- Stored in a separate, restricted repository.
- Referenced by applications but not modifiable by application developers.
- Versioned and tagged — applications pin to specific versions.
- Changes require security team review.

```yaml
# Application repo references shared pipeline
include:
  - project: 'platform/ci-templates'
    ref: 'v2.3.1'  # Pinned version
    file: '/templates/secure-build-deploy.yml'
```

---

## Appendix A: Complete DevSecOps Pipeline Example (GitHub Actions)

```yaml
name: Complete DevSecOps Pipeline
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

permissions:
  contents: read
  security-events: write
  pull-requests: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  # ─── Stage 1: Source Security ─────────────────────────
  secrets-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
        with:
          fetch-depth: 0
      - name: Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

  # ─── Stage 2: Static Analysis ────────────────────────
  sast:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - name: Semgrep
        uses: semgrep/semgrep-action@v1
        with:
          config: >-
            p/default
            p/owasp-top-ten
            p/security-audit
        env:
          SEMGREP_APP_TOKEN: ${{ secrets.SEMGREP_APP_TOKEN }}

  codeql:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - uses: github/codeql-action/init@v3
        with:
          languages: javascript
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3

  # ─── Stage 3: Dependency Analysis ────────────────────
  sca:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - name: Install dependencies
        run: npm ci
      - name: npm audit
        run: npm audit --audit-level=high
      - name: Snyk test
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
        with:
          args: --severity-threshold=high

  # ─── Stage 4: Build & Container Security ─────────────
  build-and-scan:
    needs: [secrets-scan, sast, sca]
    runs-on: ubuntu-latest
    outputs:
      image-digest: ${{ steps.build.outputs.digest }}
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build image
        id: build
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          load: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

      - name: Trivy image scan
        uses: aquasecurity/trivy-action@0.24.0
        with:
          image-ref: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'

      - name: Upload scan results
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Push image (main only)
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }}

  # ─── Stage 5: IaC Security ──────────────────────────
  iac-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - name: Checkov IaC scan
        uses: bridgecrewio/checkov-action@master
        with:
          directory: ./infrastructure/
          framework: terraform,kubernetes,dockerfile
          output_format: sarif
          download_external_modules: false
          soft_fail: false

  # ─── Stage 6: DAST (main branch only) ───────────────
  dast:
    needs: [build-and-scan]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11
      - name: Deploy to staging
        run: ./scripts/deploy-staging.sh
      - name: ZAP API Scan
        uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: 'https://staging.example.com/openapi.json'
          format: openapi
          cmd_options: '-r zap-report.html'

  # ─── Stage 7: Sign and Deploy ───────────────────────
  sign-and-deploy:
    needs: [build-and-scan, iac-scan, dast]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      packages: write
    environment: production
    steps:
      - uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11

      - name: Install cosign
        uses: sigstore/cosign-installer@v3

      - name: Sign image
        run: |
          cosign sign --yes ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build-and-scan.outputs.image-digest }}

      - name: Generate SBOM
        run: |
          syft ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ github.sha }} -o cyclonedx-json > sbom.json
          cosign attest --yes --predicate sbom.json --type cyclonedx \
            ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}@${{ needs.build-and-scan.outputs.image-digest }}

      - name: Deploy to production
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/deploy
          aws-region: us-east-1
      - run: ./scripts/deploy-production.sh
```

---

## Appendix B: Complete GitLab CI DevSecOps Pipeline

```yaml
stages:
  - secrets
  - build
  - test
  - security
  - package
  - deploy

variables:
  DOCKER_BUILDKIT: "1"
  TRIVY_SEVERITY: "CRITICAL,HIGH"
  SEMGREP_RULES: "p/default p/owasp-top-ten"

# ─── Secrets Detection ────────────────────────────────
gitleaks:
  stage: secrets
  image: zricethezav/gitleaks:latest
  script:
    - gitleaks detect --source . --report-format json --report-path gitleaks.json
  artifacts:
    paths:
      - gitleaks.json
    when: always

# ─── Build ────────────────────────────────────────────
build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

# ─── Unit Tests ───────────────────────────────────────
test:
  stage: test
  image: node:20-slim
  script:
    - npm ci
    - npm test -- --coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

# ─── SAST ─────────────────────────────────────────────
semgrep:
  stage: security
  image: semgrep/semgrep:latest
  script:
    - semgrep ci --json --output semgrep-results.json
  artifacts:
    reports:
      sast: semgrep-results.json

# ─── SCA ──────────────────────────────────────────────
dependency_scan:
  stage: security
  image: node:20-slim
  script:
    - npm ci
    - npm audit --audit-level=high --json > npm-audit.json
    - |
      CRITICAL=$(jq '.metadata.vulnerabilities.critical' npm-audit.json)
      HIGH=$(jq '.metadata.vulnerabilities.high' npm-audit.json)
      if [ "$CRITICAL" -gt 0 ] || [ "$HIGH" -gt 0 ]; then
        echo "Critical: $CRITICAL, High: $HIGH vulnerabilities found"
        exit 1
      fi
  artifacts:
    paths:
      - npm-audit.json

# ─── Container Scan ──────────────────────────────────
trivy:
  stage: security
  image:
    name: aquasec/trivy:latest
    entrypoint: [""]
  script:
    - trivy image --exit-code 1 --severity $TRIVY_SEVERITY $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  needs:
    - build

# ─── IaC Scan ─────────────────────────────────────────
checkov:
  stage: security
  image:
    name: bridgecrew/checkov:latest
    entrypoint: [""]
  script:
    - checkov -d ./infrastructure/ --output json --compact > checkov-results.json
  artifacts:
    paths:
      - checkov-results.json
  allow_failure: false

# ─── Deploy ──────────────────────────────────────────
deploy_production:
  stage: deploy
  image: bitnami/kubectl:latest
  environment:
    name: production
    url: https://app.example.com
  script:
    - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual
  needs:
    - semgrep
    - dependency_scan
    - trivy
    - checkov
    - test
  resource_group: production
```

---

## Appendix C: Metrics Dashboard Queries

### Prometheus/Grafana Queries for DevSecOps Metrics

```promql
# Mean Time to Remediate (by severity)
avg(
  vulnerability_remediation_time_seconds{severity="critical"}
) by (team)

# Vulnerability escape rate (found in prod vs total)
sum(vulnerabilities_found_total{environment="production"}) /
sum(vulnerabilities_found_total) * 100

# Pre-production catch rate
(1 - (
  sum(vulnerabilities_found_total{environment="production"}) /
  sum(vulnerabilities_found_total)
)) * 100

# Pipeline security gate pass rate
sum(rate(pipeline_security_gate_result{result="pass"}[7d])) /
sum(rate(pipeline_security_gate_result[7d])) * 100

# False positive rate
sum(vulnerability_findings_total{disposition="false_positive"}) /
sum(vulnerability_findings_total) * 100

# Open vulnerability count by severity and age
sum(open_vulnerabilities{severity=~"critical|high"}) by (severity, age_bucket)
```

---

## Appendix D: Quick Reference — Tool Selection Matrix

| Security Concern | Recommended Tools | Pipeline Stage |
|-----------------|-------------------|----------------|
| Secrets in code | Gitleaks, TruffleHog, detect-secrets | Pre-commit, PR |
| Code vulnerabilities | Semgrep, CodeQL, SonarQube | PR, Build |
| Dependency vulns | Snyk, npm audit, pip-audit, cargo-audit | PR, Build |
| License compliance | Syft, Trivy SBOM, FOSSA | Build |
| Container vulns | Trivy, Grype, Snyk Container | Build |
| IaC misconfig | Checkov, tfsec, KICS, Terrascan | PR, Build |
| K8s policy | OPA/Gatekeeper, Kyverno, kube-linter | Build, Deploy |
| Runtime vulns | OWASP ZAP, Nuclei, Burp Enterprise | Post-deploy |
| API security | ZAP API scan, Nuclei, schema validation | Post-deploy |
| Supply chain | Cosign, SLSA provenance, in-toto | Build, Release |
| Cloud posture | Prowler, ScoutSuite, Checkov | Scheduled |
| Secrets management | Vault, AWS SM, OIDC federation | Runtime |

---

## Appendix E: DevSecOps Maturity Assessment Checklist

### Level 1 → Level 2 (Foundation)

- [ ] At least one SAST tool integrated in CI (non-blocking).
- [ ] Dependency scanning enabled with notifications.
- [ ] Branch protection requiring at least one review.
- [ ] Basic secrets scanning in pre-commit or CI.
- [ ] Security training provided to all developers (annual).

### Level 2 → Level 3 (Standardization)

- [ ] Security gates block merges on critical findings.
- [ ] Threat modeling performed for all new features.
- [ ] Security champions identified (one per team).
- [ ] SBOM generated for every release.
- [ ] Container images scanned before deployment.
- [ ] IaC scanning enforced for infrastructure changes.
- [ ] Vulnerability SLAs defined and tracked.
- [ ] Centralized vulnerability dashboard.

### Level 3 → Level 4 (Measurement)

- [ ] Full toolchain coverage: SAST, SCA, DAST, IaC, container.
- [ ] MTTR tracked and improving quarter-over-quarter.
- [ ] False positive rate < 20%.
- [ ] Pre-production catch rate > 90%.
- [ ] Automated compliance evidence generation.
- [ ] Supply chain controls: signed artifacts, provenance.
- [ ] OIDC federation eliminating static CI credentials.
- [ ] Policy-as-code enforcement at deploy time.

### Level 4 → Level 5 (Optimization)

- [ ] Custom detection rules authored by development teams.
- [ ] Automated remediation (auto-merge safe patches, autofix).
- [ ] Red team exercises inform pipeline hardening.
- [ ] Vulnerability prediction and proactive patching.
- [ ] Mean Time to Remediate: Critical < 24h, High < 7d.
- [ ] Pre-production catch rate > 97%.
- [ ] Zero static long-lived credentials in any system.
- [ ] Hermetic, reproducible builds with SLSA Level 3+.

---

## References and Standards

- **NIST SP 800-218**: Secure Software Development Framework (SSDF)
- **OWASP DevSecOps Guideline**: https://owasp.org/www-project-devsecops-guideline/
- **SLSA Framework**: https://slsa.dev/
- **Sigstore**: https://www.sigstore.dev/
- **CIS Software Supply Chain Security Guide**
- **CNCF Supply Chain Best Practices**: https://github.com/cncf/tag-security/tree/main/supply-chain-security
- **OpenSSF Scorecard**: https://securityscorecards.dev/
- **OWASP SAMM (Software Assurance Maturity Model)**: https://owaspsamm.org/
- **ISO/IEC 27034**: Application Security
- **NIST SP 800-190**: Application Container Security Guide
