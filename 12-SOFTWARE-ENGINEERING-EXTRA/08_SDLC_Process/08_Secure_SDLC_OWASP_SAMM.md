---
corso: "SWE Masterclass"
fase: "8 — SDLC & Process"
modulo: "08.8"
titolo: "Secure SDLC — OWASP SAMM"
versione: "OWASP SAMM 2.0 / ASVS 5.0"
livello: "Advanced"
prerequisiti:
  - "Working knowledge of the software development lifecycle (waterfall, agile, CI/CD)"
  - "Familiarity with OWASP Top 10 vulnerability categories"
  - "Basic understanding of threat modeling concepts"
  - "Experience integrating security tooling into build pipelines"
obiettivi:
  - "Map the five OWASP SAMM business functions to concrete SDLC phases"
  - "Perform a SAMM self-assessment and score an organization across all 15 practices"
  - "Execute a STRIDE-based threat model and translate findings into security requirements"
  - "Design a 12-month secure-SDLC maturity roadmap advancing at least 3 practices to Level 2"
  - "Integrate SAST, DAST, and SCA gates into a CI/CD pipeline aligned with SAMM Verification"
tag: [secure-SDLC, OWASP-SAMM, threat-modeling, STRIDE, SAST, DAST, SCA, ASVS, DevSecOps, shift-left, NIST-SSDF]
---

# Module 8.8 (NEW): Secure SDLC — OWASP SAMM

> **Learning objectives — by the end of this module you will be able to:**
>
> 1. Map the five OWASP SAMM business functions (Governance, Design, Implementation, Verification, Operations) to concrete SDLC phases and team responsibilities.
> 2. Perform a SAMM self-assessment, score an organization across all 15 practices (maturity 0-3), and identify the highest-impact gaps.
> 3. Execute a STRIDE-based threat model on a realistic system, translating each identified threat into security requirements with test criteria.
> 4. Design a 12-month secure-SDLC maturity roadmap that advances at least 3 practices from Level 1 to Level 2.
> 5. Integrate SAST, DAST, and SCA security gates into a CI/CD pipeline, aligned with SAMM Verification practices and OWASP ASVS verification levels.

> **Last updated:** 2026-04-27

## Guiding ideas

1. **OWASP SAMM (Software Assurance Maturity Model): 5 business functions × 3 practices.**
2. **Maturity level 1-3 per practice; 0 = not addressed.**
3. **Shift-left: security earlier in lifecycle = cheaper fix.**
4. **Threat model + secure design > "fix at end".**

## SAMM business functions

| Function | Practices |
|---|---|
| Governance | Strategy & Metrics, Policy & Compliance, Education & Guidance |
| Design | Threat Assessment, Security Requirements, Security Architecture |
| Implementation | Secure Build, Secure Deployment, Defect Management |
| Verification | Architecture Assessment, Requirements-driven Testing, Security Testing |
| Operations | Incident Management, Environment Management, Operational Management |

## Esercizi

1. **Lab — SAMM self-assessment.** Score your team across all practices.
2. **Stretch — 12-month roadmap.** Pick 3 practices to advance to L2.

## Letture

- OWASP SAMM. https://owaspsamm.org/
- BSIMM (Building Security In Maturity Model) alternative.

## Glossary

| Term | Definition |
|---|---|
| **SAMM** | Software Assurance Maturity Model. |
| **BSIMM** | Building Security In Maturity Model. |
| **Shift-left** | Security earlier in SDLC. |
| **Threat model** | Pre-implementation security analysis. |
| **DevSecOps** | Security integrated in DevOps pipeline. |
| **STRIDE** | Threat-modeling mnemonic: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| **DREAD** | Risk-rating model: Damage, Reproducibility, Exploitability, Affected users, Discoverability |
| **ASVS** | Application Security Verification Standard — OWASP standard providing testable security requirements at three levels |
| **SAST** | Static Application Security Testing — analysis of source code or bytecode without executing the application |
| **DAST** | Dynamic Application Security Testing — testing the running application for vulnerabilities via simulated attacks |
| **SCA** | Software Composition Analysis — identifying known vulnerabilities and license issues in third-party dependencies |
| **SBOM** | Software Bill of Materials — machine-readable inventory of all components in a software artifact |
| **SSDF** | Secure Software Development Framework — NIST SP 800-218 practice groups for secure software production |
| **Trust boundary** | A line in a data-flow diagram where data crosses between different privilege or trust levels |
| **Security gate** | An automated checkpoint in CI/CD that blocks progression when security criteria are not met |

---

## SAMM Business Functions — Deep Dive

### Governance

Governance ensures the organization has a coherent software-security strategy,
compliant policies, and educated teams. It spans three practices:

| Practice | Focus | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| **Strategy & Metrics** | Define and measure the security program | Identify business risk profile; define basic security KPIs | Align security strategy with business strategy; track progress per BU | Continuously improve strategy based on metrics and industry benchmarks |
| **Policy & Compliance** | Organizational security policies | Document a baseline set of security policies | Map policies to regulatory requirements; audit compliance | Automated compliance verification integrated into SDLC |
| **Education & Guidance** | Developer security training | Ad-hoc security awareness training | Role-based training program (devs, architects, ops) | Continuous learning with hands-on labs, CTFs, and knowledge-sharing |

### Design

Design embeds security before code is written. The three practices ensure
threats are identified, requirements are defined, and architecture is hardened.

| Practice | Focus | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| **Threat Assessment** | Identify and quantify threats | Basic risk-based threat identification per project | Structured threat modeling (STRIDE/PASTA) for all critical apps | Continuous threat modeling integrated into design reviews |
| **Security Requirements** | Define what the software must enforce | Derive requirements from OWASP Top 10 and compliance mandates | Use ASVS as a structured requirements source; trace to tests | Requirements linked to threat model findings; automated verification |
| **Security Architecture** | Secure-by-design patterns | Apply standard security patterns (input validation, auth) | Maintain a reference architecture with approved components | Architecture review gate in SDLC; automated architecture conformance checks |

### Implementation

Implementation ensures that the build and deployment pipeline enforces security
controls and manages defects systematically.

| Practice | Focus | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| **Secure Build** | Build-time security controls | Use dependency management; basic SAST in CI | Enforce SAST quality gates; reproducible builds; SBOM generation | Hermetic builds; automated supply-chain verification; signed artifacts |
| **Secure Deployment** | Deployment-time controls | Manual security review before production deploy | Automated security checks in CD pipeline; canary deployments | Immutable infrastructure; runtime policy enforcement; deployment attestation |
| **Defect Management** | Track and fix security defects | Centralized security bug tracker; SLA per severity | Correlate defects to root causes; trend analysis | Predictive defect analysis; automated defect triage and assignment |

### Verification

Verification validates that the software meets its security requirements through
architecture review, requirements-driven testing, and security testing.

| Practice | Focus | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| **Architecture Assessment** | Review architecture against threats | Ad-hoc architecture reviews for high-risk apps | Structured reviews using threat model output | Continuous architecture verification; automated conformance checks |
| **Requirements-driven Testing** | Test against security requirements | Derive test cases from security requirements | Automate security requirement tests in CI; traceability matrix | Full coverage of ASVS requirements in automated test suite |
| **Security Testing** | DAST, SAST, penetration testing | Run SAST and basic DAST on critical apps | Integrate DAST into CI/CD; annual penetration tests | Continuous security testing; bug bounty program; red-team exercises |

### Operations

Operations covers the security posture of running software — incident response,
environment hardening, and operational management.

| Practice | Focus | Level 1 | Level 2 | Level 3 |
|---|---|---|---|---|
| **Incident Management** | Detect and respond to security incidents | Defined incident response process; severity classification | Structured postmortems; cross-team coordination; SIEM integration | Automated detection and response playbooks; threat-intelligence feeds |
| **Environment Management** | Harden runtime environments | Baseline hardening standards; patch management | Configuration-as-code; automated compliance scanning | Continuous drift detection; immutable infrastructure enforcement |
| **Operational Management** | Day-to-day security operations | Asset inventory; basic vulnerability scanning | Risk-based vulnerability prioritization; SLA-driven remediation | Continuous assurance; automated risk scoring per service |

---

## Threat Modeling with STRIDE

STRIDE is a structured threat-modeling methodology developed at Microsoft. Each
letter represents a category of threat that maps to a security property.

### STRIDE categories

| Threat | Security property violated | Example |
|---|---|---|
| **S**poofing | Authentication | Attacker impersonates a legitimate user via stolen credentials |
| **T**ampering | Integrity | Attacker modifies data in transit (man-in-the-middle) |
| **R**epudiation | Non-repudiation | User denies performing an action because audit logs are missing |
| **I**nformation Disclosure | Confidentiality | Sensitive data exposed through verbose error messages or logs |
| **D**enial of Service | Availability | Attacker floods an endpoint, exhausting resources |
| **E**levation of Privilege | Authorization | User escalates from read-only to admin via parameter tampering |

### Threat-modeling workflow

```
1. DECOMPOSE the system
   - Draw a data-flow diagram (DFD) with trust boundaries
   - Identify entry points, assets, and data stores

2. ENUMERATE threats
   - Apply STRIDE to each element crossing a trust boundary
   - Use threat-per-element or threat-per-interaction approach

3. RATE threats
   - Use DREAD (Damage, Reproducibility, Exploitability, Affected users, Discoverability)
   - Or use risk = likelihood × impact scoring

4. MITIGATE threats
   - Map each threat to a security control or requirement
   - Prioritize by risk score

5. VALIDATE mitigations
   - Verify controls via security testing (SAST, DAST, pen-test)
   - Close the loop: threat → requirement → test → verified
```

### Example STRIDE analysis for a web application

| Element | Threat category | Threat description | Mitigation |
|---|---|---|---|
| Login form | Spoofing | Credential stuffing attack | Rate limiting, MFA, CAPTCHA after N failures |
| API ↔ DB channel | Tampering | SQL injection modifies data | Parameterized queries, ORM, input validation |
| Audit log store | Repudiation | Admin deletes logs to cover tracks | Append-only log store, WORM storage, integrity hashing |
| Error response | Info Disclosure | Stack trace leaks internal paths | Generic error messages in production; detailed logs server-side only |
| Public API | Denial of Service | Volumetric flood on unprotected endpoint | WAF, rate limiting, auto-scaling, CDN |
| User role parameter | Elevation of Privilege | User sets `role=admin` in request body | Server-side role enforcement; ignore client-supplied role fields |

---

## OWASP ASVS Integration

The OWASP Application Security Verification Standard (ASVS) provides testable
security requirements organized into three levels of rigor.

### ASVS verification levels

| Level | Intended use | Depth |
|---|---|---|
| **L1** | All applications | Baseline security; automated checks can cover most |
| **L2** | Applications handling sensitive data | In-depth verification; most organizations should target L2 |
| **L3** | Critical applications (financial, healthcare, infrastructure) | Maximum assurance; formal verification, penetration testing |

### Mapping ASVS to SAMM

| ASVS chapter | Relevant SAMM practice |
|---|---|
| V1: Architecture | Design → Security Architecture |
| V2: Authentication | Design → Security Requirements |
| V3: Session Management | Design → Security Requirements |
| V4: Access Control | Design → Security Requirements |
| V5: Validation | Implementation → Secure Build |
| V10: Malicious Code | Verification → Security Testing |
| V14: Configuration | Operations → Environment Management |

---

## NIST SSDF (SP 800-218) Alignment

The NIST Secure Software Development Framework (SSDF) defines four practice
groups that complement SAMM. Mapping between them helps organizations satisfy
both OWASP and US federal requirements.

| SSDF practice group | Description | SAMM equivalent |
|---|---|---|
| **PO — Prepare the Organization** | Define security requirements, roles, tooling | Governance (Strategy & Metrics, Education & Guidance) |
| **PS — Protect the Software** | Protect code, builds, and releases from tampering | Implementation (Secure Build, Secure Deployment) |
| **PW — Produce Well-Secured Software** | Design, code, test with security controls | Design + Verification (Threat Assessment, Security Testing) |
| **RV — Respond to Vulnerabilities** | Detect, triage, remediate, disclose vulnerabilities | Operations (Incident Management, Defect Management) |

---

## CI/CD Security Gates

Integrating security testing into the CI/CD pipeline operationalizes the SAMM
Verification function. The goal is to fail builds on security regressions before
they reach production.

### Pipeline integration pattern

```
┌─────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Commit      │───▶│  SAST    │───▶│  SCA     │───▶│  Build   │───▶│  DAST    │
│  (pre-commit │    │  (Semgrep│    │  (Trivy, │    │  + SBOM  │    │  (ZAP,   │
│   hooks)     │    │   CodeQL)│    │   Snyk)  │    │  generate│    │   Nuclei)│
└─────────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                        │                │                               │
                   Fail on HIGH+    Fail on CRITICAL          Fail on HIGH+
                   findings          CVEs in deps              findings
```

### Security gate thresholds

| Gate | Tool category | Block deploy when |
|---|---|---|
| Pre-commit | Secret scanners (gitleaks, detect-secrets) | Any secret detected |
| CI — SAST | Static analysis (Semgrep, CodeQL, SonarQube) | HIGH or CRITICAL findings |
| CI — SCA | Dependency scanning (Trivy, Snyk, Dependabot) | CRITICAL CVE in direct dependency |
| CI — SBOM | SBOM generation (Syft, CycloneDX) | SBOM not generated (compliance gate) |
| CD — DAST | Dynamic testing (OWASP ZAP, Nuclei) | HIGH findings on staging |
| CD — Image scan | Container scanning (Trivy, Grype) | CRITICAL CVE in base image |

---

## Maturity Assessment Methodology

### Running a SAMM self-assessment

```
Step 1: Assemble the assessment team
  - Representatives from development, security, operations, and management
  - 2-4 hours for initial assessment

Step 2: Score each practice (0-3)
  - For each of the 15 practices, evaluate both streams
  - Use the OWASP SAMM Toolbox (spreadsheet or online tool)
  - Score based on evidence, not aspiration

Step 3: Identify gaps
  - Compare current scores against your target maturity profile
  - Prioritize practices where the gap is largest AND business risk is highest

Step 4: Build a roadmap
  - Select 3-5 practices to advance per 12-month cycle
  - Define specific activities, owners, and milestones for each
  - Budget for tooling, training, and process changes

Step 5: Measure progress
  - Re-assess every 6-12 months
  - Track movement per practice; celebrate advances
  - Benchmark against SAMM community data
```

### Example maturity scorecard

```
Business Function: Design
┌────────────────────────┬──────────┬──────────┬──────┐
│ Practice               │ Current  │ Target   │ Gap  │
├────────────────────────┼──────────┼──────────┼──────┤
│ Threat Assessment      │ 0.5      │ 2.0      │ 1.5  │
│ Security Requirements  │ 1.0      │ 2.0      │ 1.0  │
│ Security Architecture  │ 1.0      │ 2.0      │ 1.0  │
└────────────────────────┴──────────┴──────────┴──────┘

Business Function: Verification
┌────────────────────────┬──────────┬──────────┬──────┐
│ Practice               │ Current  │ Target   │ Gap  │
├────────────────────────┼──────────┼──────────┼──────┤
│ Architecture Assessment│ 0.0      │ 1.0      │ 1.0  │
│ Requirements Testing   │ 0.5      │ 2.0      │ 1.5  │
│ Security Testing       │ 1.0      │ 2.0      │ 1.0  │
└────────────────────────┴──────────┴──────────┴──────┘
```

---

## Exercises

1. **Lab — STRIDE threat model.** Pick a system you work on (or a reference
   architecture such as a three-tier web application with a public API, internal
   microservices, and a database). Draw a data-flow diagram with trust
   boundaries. Apply STRIDE to every element crossing a trust boundary. Produce
   a threat table with at least 10 threats, a risk rating per threat, and a
   proposed mitigation for each. Verify that every HIGH-rated threat maps to at
   least one test case.

2. **Lab — OWASP SAMM maturity assessment.** Download the OWASP SAMM Toolbox
   from https://owaspsamm.org. Score your team or a reference organization across
   all 15 practices (both streams). Identify the 3 practices with the largest
   gap between current and target maturity. For each, write a one-page
   improvement plan with specific activities, responsible owners, tool
   requirements, and a 6-month milestone.

3. **Lab — CI/CD security gate integration.** Set up a pipeline (GitHub Actions,
   GitLab CI, or equivalent) that includes: (a) a pre-commit secret scanner
   (gitleaks or detect-secrets), (b) SAST via Semgrep or CodeQL with a quality
   gate blocking on HIGH findings, (c) SCA via Trivy or Snyk blocking on
   CRITICAL CVEs, and (d) SBOM generation via Syft. Commit a known-vulnerable
   dependency and a test secret to verify the gates fire correctly.

4. **Lab — security requirements from ASVS.** Select an application and choose
   ASVS Level 2 as the target. Pick three ASVS chapters (e.g., V2 Authentication,
   V4 Access Control, V5 Validation). Extract 5 specific requirements per
   chapter. For each requirement, write a test case (unit or integration) and
   verify it passes or identify the implementation gap.

5. **Stretch — 12-month roadmap.** Using the results from Exercise 2, build a
   12-month secure-SDLC maturity roadmap. Structure it in quarterly phases.
   Phase 1: quick wins (Level 0 → 1). Phase 2: foundational practices (Level 1
   → 2 for 3 high-priority practices). Phase 3-4: consolidation and measurement.
   Include estimated effort (person-days), tooling costs, and training needs.
   Present the roadmap to a peer for review and incorporate their feedback.

---

## Readings and References

| # | Source | URL | Retrieved |
|---|--------|-----|-----------|
| 1 | OWASP SAMM — The Model (v2.0) | https://owaspsamm.org/model/ | 2026-05-29 |
| 2 | OWASP SAMM — Quick Start Guide | https://owaspsamm.org/guidance/quick-start-guide/ | 2026-05-29 |
| 3 | OWASP SAMM | OWASP Foundation | https://owasp.org/www-project-samm/ | 2026-05-29 |
| 4 | OWASP Application Security Verification Standard (ASVS) | https://owasp.org/www-project-application-security-verification-standard/ | 2026-05-29 |
| 5 | OWASP ASVS — GitHub repository | https://github.com/OWASP/ASVS | 2026-05-29 |
| 6 | NIST SP 800-218 — Secure Software Development Framework (SSDF) v1.1 | https://csrc.nist.gov/pubs/sp/800/218/final | 2026-05-29 |
| 7 | NIST SP 800-218 — SSDF (CISA resource page) | https://www.cisa.gov/resources-tools/resources/nist-sp-800-218-secure-software-development-framework-v11-recommendations-mitigating-risk-software | 2026-05-29 |
| 8 | OWASP Top 10:2025 — Establishing a Modern Application Security Program | https://owasp.org/Top10/2025/0x03_2025-Establishing_a_Modern_Application_Security_Program/ | 2026-05-29 |
| 9 | Codific — Building your SSDLC with OWASP SAMM | https://codific.com/owasp-sdlc-owasp-samm/ | 2026-05-29 |
| 10 | Practical DevSecOps — STRIDE Threat Model Explained | https://www.practical-devsecops.com/what-is-stride-threat-model/ | 2026-05-29 |
| 11 | McGraw. *Software Security: Building Security In* (Addison-Wesley, 2006) | — | — |
| 12 | Shostack. *Threat Modeling: Designing for Security* (Wiley, 2014) | — | — |

---

## Cross-References

| Module / Folder | Relevance |
|---|---|
| [03_Code_Quality_Static_Analysis.md](./03_Code_Quality_Static_Analysis.md) | SAST tooling and quality-gate configuration; static-analysis practices mapped to SAMM Verification |
| [02_Testing_Strategies.md](./02_Testing_Strategies.md) | Requirements-driven testing and security test-case derivation from ASVS |
| [04_Documentation_ADR_C4.md](./04_Documentation_ADR_C4.md) | Architectural Decision Records documenting security design choices; C4 diagrams as DFD input for threat models |
| [06_Code_Review_Rubrics.md](./06_Code_Review_Rubrics.md) | Security-focused review checklists aligned with SAMM Implementation → Secure Build |
| [07_Incident_Response_Postmortems.md](./07_Incident_Response_Postmortems.md) | SAMM Operations → Incident Management practice; postmortem-driven security improvements |
| [../04_Security_Cryptography/](../04_Security_Cryptography/) | Cryptographic requirements and key management mapped to SAMM Design → Security Architecture |
