# Compliance Auditing, Evidence Collection e Regulatory Framework Implementation — Guida Completa

> **Modulo 43** · **Tempo:** ~180 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Compliance is not security, but security enables compliance.** A compliant system can still be insecure; a truly secure system makes compliance trivial. Never confuse checkbox exercise with actual risk reduction.
2. **Evidence is the currency of audits.** Without timely, accurate, complete evidence, even perfect controls are worthless to an auditor. Automate evidence collection or drown in manual toil.
3. **Framework overlap is massive.** 60-70% of controls across PCI-DSS, ISO 27001, SOC 2, and NIST CSF are functionally identical. Map once, implement once, evidence once, satisfy many.
4. **Continuous compliance beats point-in-time.** Annual audits catch drift too late. Real-time control monitoring with automated alerting is the only defensible posture.
5. **The auditor is not the enemy.** Understanding what auditors look for, how they think, and what constitutes sufficient evidence transforms adversarial engagements into collaborative ones.

## Indice

1. [Panoramica Framework di Compliance](#1-panoramica-framework-di-compliance)
2. [PCI-DSS 4.0 Deep Dive](#2-pci-dss-40-deep-dive)
3. [ISO 27001:2022 Implementation](#3-iso-270012022-implementation)
4. [SOC 2 Type II](#4-soc-2-type-ii)
5. [Audit Evidence Collection](#5-audit-evidence-collection)
6. [Automazione Compliance](#6-automazione-compliance)
7. [Security Testing per Compliance](#7-security-testing-per-compliance)
8. [Audit Preparation e Gestione](#8-audit-preparation-e-gestione)
9. [Risk Management](#9-risk-management)
10. [Laboratorio Pratico](#10-laboratorio-pratico)
11. [GDPR — Raccolta Evidenze e Documentazione](#11-gdpr--raccolta-evidenze-e-documentazione)
12. [NIS2 — Preparazione Audit e Requisiti Probatori](#12-nis2--preparazione-audit-e-requisiti-probatori)
13. [Matrice di Mappatura Cross-Framework](#13-matrice-di-mappatura-cross-framework)
14. [AI e Machine Learning nell'Auditing di Compliance](#14-ai-e-machine-learning-nellauditing-di-compliance)
15. [Piattaforme GRC e Strumenti di Automazione Avanzata](#15-piattaforme-grc-e-strumenti-di-automazione-avanzata)
16. [Template Operativi e Checklist di Raccolta Evidenze](#16-template-operativi-e-checklist-di-raccolta-evidenze)

---

## 1. Panoramica Framework di Compliance

### 1.1 Framework Landscape

The regulatory compliance landscape for IT operations is a dense ecosystem of overlapping requirements, each originating from different motivations: industry self-regulation (PCI-DSS), international standards bodies (ISO 27001), market-driven assurance (SOC 2), government regulation (GDPR, HIPAA, NIS2), and best-practice frameworks (NIST CSF, CIS Controls). A senior IT professional must understand not only what each framework demands, but how they interrelate, overlap, and where choosing one can satisfy obligations in another.

**Framework Classification by Origin and Obligation:**

| Framework | Origin | Legal Obligation | Scope | Certification |
|-----------|--------|-----------------|-------|---------------|
| PCI-DSS 4.0 | Payment Card Industry (PCI SSC) | Contractual (card brands) | Card data environment | Yes (QSA/ISA) |
| ISO 27001:2022 | ISO/IEC | Voluntary (contractual) | Entire ISMS scope | Yes (accredited CB) |
| SOC 2 Type II | AICPA | Voluntary (market) | In-scope trust criteria | Attestation report |
| HIPAA | US HHS | Legal (US healthcare) | PHI systems | No formal cert |
| GDPR | European Parliament | Legal (EU data subjects) | Personal data processing | No formal cert |
| NIS2 Directive | European Parliament | Legal (EU essential/important entities) | Network/information systems | No formal cert |
| NIST CSF 2.0 | US NIST | Voluntary (mandatory for US federal) | Organization-wide | Self-assessment |
| CIS Controls v8 | CIS | Voluntary | IT infrastructure | CIS benchmarks |

### 1.2 Control Overlap Analysis

The critical insight for any compliance program managing multiple frameworks: **most controls are the same requirement expressed in different language**. A mature organization implements controls once, maps them to multiple frameworks, and collects evidence once that satisfies all applicable auditors.

**High-Overlap Control Domains:**

| Control Domain | PCI-DSS | ISO 27001 | SOC 2 | NIST CSF | CIS v8 |
|---------------|---------|-----------|-------|----------|--------|
| Access Control | Req 7, 8 | A.5.15-5.18, A.8.2-8.5 | CC6.1-6.3 | PR.AC | CIS 5, 6 |
| Encryption | Req 3, 4 | A.8.24 | CC6.1, CC6.7 | PR.DS | CIS 3 |
| Logging/Monitoring | Req 10 | A.8.15-8.16 | CC7.1-7.3 | DE.CM, DE.AE | CIS 8 |
| Vulnerability Mgmt | Req 6, 11 | A.8.8 | CC7.1 | ID.RA, PR.IP | CIS 7 |
| Incident Response | Req 12.10 | A.5.24-5.28 | CC7.3-7.5 | RS.* | CIS 17 |
| Change Management | Req 6.5 | A.8.32 | CC8.1 | PR.IP | CIS 2 |
| Network Security | Req 1, 2 | A.8.20-8.23 | CC6.6 | PR.AC, PR.PT | CIS 12, 13 |
| Physical Security | Req 9 | A.7.1-7.14 | CC6.4 | PR.AC | CIS — |
| Vendor Management | Req 12.8 | A.5.19-5.23 | CC9.2 | ID.SC | CIS 15 |
| Security Awareness | Req 12.6 | A.6.3 | CC1.4 | PR.AT | CIS 14 |

### 1.3 Choosing Framework Based on Business Requirements

**Decision Matrix:**

```
IF processes card payments → PCI-DSS 4.0 (mandatory)
IF handles US healthcare data → HIPAA (mandatory)
IF processes EU personal data → GDPR (mandatory)
IF provides essential/important services in EU → NIS2 (mandatory)
IF selling to enterprise B2B → SOC 2 Type II (market expectation)
IF operating internationally → ISO 27001 (universal credibility)
IF US government contractor → NIST 800-53 / CMMC (mandatory)
IF need internal framework → NIST CSF 2.0 (structure) + CIS v8 (tactical)
```

**Common Combinations:**

- SaaS company selling to enterprise: SOC 2 + ISO 27001 + GDPR
- E-commerce platform: PCI-DSS + GDPR + SOC 2
- Healthcare SaaS (US): HIPAA + SOC 2 + ISO 27001
- European essential services: NIS2 + ISO 27001 + GDPR
- Financial services: PCI-DSS + SOC 2 + ISO 27001 + local regulations

### 1.4 NIST CSF 2.0

NIST Cybersecurity Framework 2.0 (released February 2024) introduces a sixth function — **Govern** — alongside the existing five: Identify, Protect, Detect, Respond, Recover. CSF 2.0 is explicitly designed for all organization sizes (not just critical infrastructure) and includes:

- Organizational profiles (current vs target state)
- Tiers (1-4) measuring implementation maturity
- Informative references mapping to other frameworks
- Supply chain risk management emphasis

**The six functions:**

| Function | Purpose | Key Categories |
|----------|---------|----------------|
| Govern (GV) | Cybersecurity strategy, risk management, roles | GV.OC, GV.RM, GV.RR, GV.PO, GV.OV, GV.SC |
| Identify (ID) | Asset, risk, improvement discovery | ID.AM, ID.RA, ID.IM |
| Protect (PR) | Safeguards implementation | PR.AA, PR.AT, PR.DS, PR.PS, PR.IR |
| Detect (DE) | Anomaly/event detection | DE.CM, DE.AE |
| Respond (RS) | Incident handling | RS.MA, RS.AN, RS.CO, RS.MI |
| Recover (RC) | Restoration | RC.RP, RC.CO |

### 1.5 CIS Controls v8 — Implementation Groups

CIS Controls v8 organizes 18 control families into three Implementation Groups (IGs), providing a prioritized path:

- **IG1** (Essential Cyber Hygiene): 56 safeguards. Minimum baseline for every organization.
- **IG2**: IG1 + 74 additional safeguards. For organizations with moderate risk.
- **IG3**: IG1 + IG2 + 23 additional safeguards. For organizations with significant risk.

### 1.6 NIS2 Directive Key Requirements

NIS2 (Directive 2022/2555) significantly expands the scope of EU cybersecurity obligations. Key requirements for essential and important entities:

- Risk analysis and information system security policies
- Incident handling (24h early warning, 72h incident notification, 1 month final report)
- Business continuity and crisis management
- Supply chain security
- Security in network and information systems acquisition
- Policies for assessing cybersecurity risk-management measures
- Cyber hygiene practices and cybersecurity training
- Cryptography and encryption policies
- Human resource security, access control, asset management
- Multi-factor authentication (MFA) and secured communications

**Penalties under NIS2:**
- Essential entities: up to EUR 10 million or 2% of total annual worldwide turnover
- Important entities: up to EUR 7 million or 1.4% of total annual worldwide turnover
- Personal liability for management bodies

---

## 2. PCI-DSS 4.0 Deep Dive

### 2.1 The 12 Requirements

PCI-DSS 4.0 (effective March 2024, mandatory March 2025 with some requirements deferred to March 2025) restructures the familiar 12 requirements with expanded flexibility through the "customized approach."

**Requirement 1: Install and Maintain Network Security Controls**

Replaces the old "firewall" language. Now encompasses any network security control (NSC): traditional firewalls, cloud security groups, SDN policies, micro-segmentation, zero-trust network access. Key sub-requirements:

- 1.2: NSCs configured and maintained
- 1.3: Network access to/from CDE restricted (inbound and outbound rules)
- 1.4: Network connections between trusted and untrusted networks controlled
- 1.5: Risks to CDE from other networks mitigated

**Requirement 2: Apply Secure Configurations to All System Components**

Default passwords eliminated, unnecessary services disabled, system hardening applied per vendor/industry baselines (CIS Benchmarks, DISA STIGs). Applies to all components, not just in-scope.

**Requirement 3: Protect Stored Account Data**

Encryption (AES-256, TDES), tokenization, truncation, hashing. PAN storage minimized. Key management lifecycle (generation, distribution, storage, rotation, destruction). New in 4.0: expanded requirements for SAD (Sensitive Authentication Data) after authorization for issuers.

**Requirement 4: Protect Cardholder Data with Strong Cryptography During Transmission**

TLS 1.2 minimum (TLS 1.3 recommended). Certificate validation enforced. Applies to transmissions over open, public networks AND internal networks where PAN traverses.

**Requirement 5: Protect All Systems and Networks from Malicious Software**

Anti-malware deployed on all systems commonly affected. Periodic evaluations of systems not commonly affected. Phishing mechanisms addressed (new in 4.0). Removable media scanning.

**Requirement 6: Develop and Maintain Secure Systems and Software**

- 6.2: Bespoke/custom software developed securely (secure SDLC)
- 6.3: Security vulnerabilities identified and addressed (patch management)
- 6.4: Public-facing web applications protected (WAF or code review)
- 6.5: Changes managed securely (change control)

**Requirement 7: Restrict Access to System Components and Cardholder Data by Business Need to Know**

Role-based access control. Access limited to least privilege. All access explicitly authorized. Access reviews at least every six months.

**Requirement 8: Identify Users and Authenticate Access**

- 8.2: User identification
- 8.3: Strong authentication (MFA for all access to CDE — new mandate for 4.0)
- 8.4: MFA for all non-console administrative access
- 8.5: MFA systems properly configured
- 8.6: Application/service account management

**Requirement 9: Restrict Physical Access to Cardholder Data**

Facility entry controls, visitor management, media destruction, POI (point-of-interaction) device protection.

**Requirement 10: Log and Monitor All Access to System Components and Cardholder Data**

- 10.2: Audit logs enabled and capture defined events
- 10.3: Audit logs protected from destruction/modification
- 10.4: Audit logs reviewed (automated mechanisms)
- 10.5: Audit log history retained (12 months minimum, 3 months immediately available)
- 10.6: Time synchronization (NTP)
- 10.7: Failures of critical security control systems detected and reported

**Requirement 11: Test Security of Systems and Networks Regularly**

- 11.2: Wireless access points managed
- 11.3: External/internal vulnerabilities identified and addressed (ASV quarterly scans)
- 11.4: External/internal penetration testing (at least annually, after significant changes)
- 11.5: Network intrusions detected and responded to
- 11.6: Changes to payment pages detected (new: client-side script integrity monitoring)

**Requirement 12: Support Information Security with Organizational Policies and Programs**

Security policy, acceptable use, risk assessment, security awareness training, incident response plan, third-party service provider management.

### 2.2 Scope Reduction Techniques

Reducing PCI-DSS scope is the single most effective cost-reduction strategy:

- **Network Segmentation**: Isolate CDE from corporate network. Validated by penetration testing every 6 months (for service providers) or annually.
- **Tokenization**: Replace PAN with non-reversible token. Token vault may remain in scope but the rest of the environment exits scope.
- **P2PE (Point-to-Point Encryption)**: PCI-validated P2PE solutions remove the entire transmission path from scope.
- **Cloud/SaaS delegation**: Using PCI-compliant service providers (e.g., Stripe, Adyen) shifts scope to the provider. You remain responsible for what you control (iframe integration, redirect configuration).

### 2.3 Self-Assessment Questionnaires (SAQ)

| SAQ Type | Merchant Type | Questions |
|----------|--------------|-----------|
| SAQ A | Card-not-present, fully outsourced | ~20 |
| SAQ A-EP | E-commerce, partial outsourcing | ~140 |
| SAQ B | Imprint machines or standalone dial-out terminals | ~40 |
| SAQ B-IP | Standalone IP-connected terminals (P2PE) | ~80 |
| SAQ C | Payment application systems connected to internet | ~160 |
| SAQ C-VT | Virtual terminal, one transaction at a time | ~80 |
| SAQ D (Merchant) | All others | ~330 |
| SAQ D (SP) | Service providers | ~400+ |
| SAQ P2PE | Hardware P2PE terminal merchants | ~30 |

### 2.4 Defined Approach vs Customized Approach

PCI-DSS 4.0 introduces two validation paths:

**Defined Approach** (traditional):
- Meet the specific requirement as stated
- Use testing procedures defined in the standard
- Compensating controls for situations where a requirement cannot be met as stated

**Customized Approach** (new in 4.0):
- Meet the customized approach objective (stated for each requirement)
- Entity designs its own control to meet the objective
- Targeted risk analysis documents why the custom control is effective
- Must be validated by a QSA (not available for SAQ self-assessment)
- Cannot use for requirements that already offer flexibility

### 2.5 Key Changes from v3.2.1 to 4.0

| Area | v3.2.1 | v4.0 |
|------|--------|------|
| MFA | Admin access only | All CDE access |
| Passwords | 7 chars minimum | 12 chars minimum (or 8 if system doesn't support 12) |
| Script integrity | — | Payment page script monitoring (Req 6.4.3, 11.6.1) |
| Encryption | — | Disk-level encryption no longer acceptable for PAN at rest |
| Risk assessment | Annual | Targeted risk analyses for specific requirements |
| Authentication | — | 8.3.6: 12-char passwords, 8.6: system/service accounts managed |
| Validation | Defined only | Defined or Customized approach |
| Log review | Daily manual | Automated mechanisms |
| Phishing | — | Anti-phishing mechanisms (Req 5.4) |

### 2.6 Compensating Controls

When a requirement cannot be met as stated in the defined approach:

1. Document the business/technical constraint preventing compliance
2. Define the compensating control that addresses the risk
3. The compensating control must: address the risk the original requirement reduces, provide a similar level of defense, be above and beyond other requirements, be commensurate with additional risk
4. Document in Compensating Control Worksheet (Appendix B/C)
5. QSA validates annually

---

## 3. ISO 27001:2022 Implementation

### 3.1 ISMS Lifecycle

The Information Security Management System operates on the Plan-Do-Check-Act (PDCA) cycle:

```
┌─────────────────────────────────────────────────┐
│                   PLAN                           │
│  • Define scope and context                     │
│  • Risk assessment and treatment                │
│  • Statement of Applicability                   │
│  • Objectives and plans                         │
├─────────────────────────────────────────────────┤
│                    DO                            │
│  • Implement controls                           │
│  • Security awareness and training              │
│  • Operational procedures                       │
│  • Resource management                          │
├─────────────────────────────────────────────────┤
│                   CHECK                          │
│  • Internal audits                              │
│  • Management review                            │
│  • Performance measurement                      │
│  • Monitoring and evaluation                    │
├─────────────────────────────────────────────────┤
│                    ACT                           │
│  • Corrective actions                           │
│  • Continual improvement                        │
│  • Preventive actions                           │
│  • Management decisions                         │
└─────────────────────────────────────────────────┘
```

### 3.2 Risk Assessment Methodology

**Qualitative Risk Assessment:**

Uses descriptive scales (Low/Medium/High/Critical) for likelihood and impact. Faster but subjective. Appropriate for initial assessments and organizations with less mature data.

```
Risk = Likelihood × Impact

Likelihood Scale:
1 - Rare      (< once per 5 years)
2 - Unlikely  (once per 2-5 years)
3 - Possible  (once per 1-2 years)
4 - Likely    (multiple times per year)
5 - Almost Certain (monthly or more)

Impact Scale:
1 - Negligible  (< $10K, no reputation impact)
2 - Minor       ($10K-100K, limited reputation)
3 - Moderate    ($100K-1M, sector reputation)
4 - Major       ($1M-10M, national reputation)
5 - Catastrophic (> $10M, existential threat)
```

**Quantitative Risk Assessment (FAIR - Factor Analysis of Information Risk):**

Uses monetary values and probability distributions. More objective but requires data:

```
Annualized Loss Expectancy (ALE) = 
    Single Loss Expectancy (SLE) × Annual Rate of Occurrence (ARO)

SLE = Asset Value × Exposure Factor (EF)

Example:
  Asset Value: $5,000,000 (customer database)
  Exposure Factor: 40% (partial breach)
  SLE: $2,000,000
  ARO: 0.1 (once per 10 years)
  ALE: $200,000/year

  → If a control costs < $200,000/year, it's justified
```

### 3.3 Statement of Applicability (SoA)

The SoA is the master document linking your risk assessment to Annex A controls. For each of the 93 controls:

| Column | Content |
|--------|---------|
| Control Reference | A.5.1 through A.8.34 |
| Control Title | Official name |
| Applicable | Yes/No |
| Justification | Why applicable or why excluded |
| Implementation Status | Implemented / Partially / Planned / Not started |
| Control Owner | Responsible person/team |
| Evidence Reference | Where evidence is stored |
| Risk Treatment Reference | Link to risk register entry |

### 3.4 Annex A Controls — ISO 27001:2022

The 2022 revision restructured 114 controls (from 2013) into 93 controls across 4 themes:

**Theme 5: Organizational Controls (37 controls)**

| Control | Title | Key Requirement |
|---------|-------|-----------------|
| A.5.1 | Policies for information security | Approved, published, communicated |
| A.5.2 | Information security roles | Defined and allocated |
| A.5.3 | Segregation of duties | Conflicting duties separated |
| A.5.7 | Threat intelligence | Collect and analyze |
| A.5.8 | Information security in project management | Integrated into PM |
| A.5.15 | Access control | Need-to-know, least privilege |
| A.5.19 | Information security in supplier relationships | Agree requirements |
| A.5.23 | Information security for cloud services | Manage cloud risks |
| A.5.24 | Incident management planning | Defined procedures |
| A.5.29 | ICT readiness for business continuity | ICT continuity plans |
| A.5.30 | ICT readiness for business continuity | Requirements identified |

**Theme 6: People Controls (8 controls)**

A.6.1 through A.6.8: Screening, employment terms, awareness/training, disciplinary process, post-employment responsibilities, confidentiality agreements, remote working, information security event reporting.

**Theme 7: Physical Controls (14 controls)**

A.7.1 through A.7.14: Physical perimeters, physical entry, offices/rooms/facilities, physical security monitoring, environmental threats, secure areas, clear desk/screen, equipment siting, asset security off-premises, storage media, supporting utilities, cabling security, equipment maintenance, secure disposal/reuse.

**Theme 8: Technological Controls (34 controls)**

| Control | Title | Key Requirement |
|---------|-------|-----------------|
| A.8.1 | User endpoint devices | Security policy for BYOD/corporate |
| A.8.2 | Privileged access rights | Restricted and managed |
| A.8.5 | Secure authentication | MFA, password policy |
| A.8.7 | Protection against malware | Anti-malware deployed |
| A.8.8 | Technical vulnerability management | Scan, assess, patch |
| A.8.9 | Configuration management | Baselines defined and maintained |
| A.8.15 | Logging | Logs produced, stored, protected |
| A.8.16 | Monitoring activities | Anomaly detection |
| A.8.20 | Networks security | Segmentation, controls |
| A.8.23 | Web filtering | Access to malicious URLs prevented |
| A.8.24 | Use of cryptography | Encryption policy and management |
| A.8.25 | Secure development lifecycle | SDLC rules applied |
| A.8.28 | Secure coding | Coding standards applied |
| A.8.31 | Separation of environments | Dev/test/prod separated |
| A.8.32 | Change management | Changes controlled |
| A.8.33 | Test information | Test data protected |
| A.8.34 | Audit system protection | Audit systems protected from tampering |

**New controls in 2022** (not present in 2013):

- A.5.7: Threat intelligence
- A.5.23: Information security for use of cloud services
- A.5.30: ICT readiness for business continuity
- A.7.4: Physical security monitoring
- A.8.9: Configuration management
- A.8.10: Information deletion
- A.8.11: Data masking
- A.8.12: Data leakage prevention
- A.8.16: Monitoring activities
- A.8.23: Web filtering
- A.8.28: Secure coding

### 3.5 Certification Process and Timeline

```
Month 1-2:   Gap analysis, scope definition, project planning
Month 3-4:   Risk assessment, SoA development, policy creation
Month 5-8:   Control implementation, awareness training
Month 9-10:  Internal audit, management review
Month 11:    Remediation of findings
Month 12:    Stage 1 audit (documentation review)
Month 13:    Stage 2 audit (implementation effectiveness)
Month 14:    Certification decision, certificate issued

Ongoing:
  Year 1-2: Surveillance audits (annual)
  Year 3: Re-certification audit (full)
```

**Stage 1 Audit** (documentation adequacy): Auditor reviews ISMS documentation, scope, risk assessment, SoA, policies, and procedures. Identifies areas of concern for Stage 2.

**Stage 2 Audit** (implementation effectiveness): On-site (or remote) assessment of actual implementation. Interviews staff, reviews evidence, tests controls. Typically 5-15 auditor-days depending on scope.

### 3.6 Internal Audit Program

ISO 27001 clause 9.2 mandates internal audits. Requirements:

- Planned intervals (at least annually, typically more frequent)
- Covers all ISMS clauses and applicable Annex A controls over audit cycle
- Auditor independence (cannot audit own work)
- Documented audit criteria, scope, methods
- Results reported to management
- Nonconformities tracked to closure

**Audit Schedule Template:**

```yaml
internal_audit_schedule:
  cycle: 12_months
  approach: risk_based  # higher risk areas more frequently
  coverage:
    - quarter: Q1
      areas:
        - Access Control (A.5.15-5.18, A.8.2-8.5)
        - Cryptography (A.8.24)
        - Network Security (A.8.20-8.22)
    - quarter: Q2
      areas:
        - Incident Management (A.5.24-5.28)
        - Logging and Monitoring (A.8.15-8.16)
        - Vulnerability Management (A.8.8)
    - quarter: Q3
      areas:
        - Supplier Management (A.5.19-5.23)
        - Change Management (A.8.32)
        - Secure Development (A.8.25-8.28)
    - quarter: Q4
      areas:
        - Physical Security (A.7.1-7.14)
        - HR Security (A.6.1-6.8)
        - Business Continuity (A.5.29-5.30)
  resources:
    lead_auditor: internal_certified
    audit_team: 2-3_people
    budget: allocated_annually
```

---

## 4. SOC 2 Type II

### 4.1 Trust Services Criteria (TSC)

SOC 2 is built on five Trust Services Criteria. Only **Security** (Common Criteria) is mandatory; the others are included based on service commitments:

**Security (Common Criteria — CC Series):**

| Series | Domain | Key Controls |
|--------|--------|--------------|
| CC1 | Control Environment | Integrity, ethics, board oversight, structure |
| CC2 | Communication and Information | Internal/external communication |
| CC3 | Risk Assessment | Risk identification, fraud risk, change impact |
| CC4 | Monitoring Activities | Ongoing/separate evaluations, deficiency communication |
| CC5 | Control Activities | Selection, technology controls, policies |
| CC6 | Logical and Physical Access | Access security, registration, authentication, physical |
| CC7 | System Operations | Detection, monitoring, incident response |
| CC8 | Change Management | Changes authorized, tested, approved |
| CC9 | Risk Mitigation | Risk mitigation, vendor management |

**Availability (A Series):**
- A1.1: Current processing capacity and usage maintained
- A1.2: Environmental protections and recovery
- A1.3: Recovery testing performed

**Processing Integrity (PI Series):**
- PI1.1: Processing objectives defined
- PI1.2: Processing inputs complete and accurate
- PI1.3: Processing performed per specifications
- PI1.4: Outputs complete and accurate
- PI1.5: Inputs/outputs stored securely

**Confidentiality (C Series):**
- C1.1: Confidential information identified
- C1.2: Confidential information disposed

**Privacy (P Series):**
- Based on GAPP (Generally Accepted Privacy Principles)
- Notice, choice/consent, collection, use/retention/disposal, access, disclosure, security, quality

### 4.2 Type I vs Type II

| Aspect | Type I | Type II |
|--------|--------|---------|
| Evaluation | Design of controls at a point in time | Operating effectiveness over a period |
| Period | Single date (snapshot) | Minimum 6 months (typically 12) |
| Evidence | Control design documentation | Evidence of consistent operation |
| Value | Limited assurance | Strong assurance |
| Common use | Initial report, stepping stone | Standard for enterprise sales |
| Cost | Lower | Higher (ongoing evidence collection) |
| Timeline | 1-2 months audit | 6-12 month observation + 1-2 month audit |

### 4.3 Readiness Assessment

Before engaging an auditor for the actual SOC 2 examination:

1. **Scope determination**: Which TSC apply? Which systems are in scope?
2. **Control identification**: Map existing controls to TSC criteria
3. **Gap analysis**: What controls are missing or insufficient?
4. **Evidence assessment**: Can you demonstrate 6+ months of consistent operation?
5. **Remediation planning**: Timeline and resources for gap closure
6. **Tool selection**: Compliance platform (Vanta, Drata, etc.) or manual

### 4.4 Evidence Collection Requirements by Criteria

| Criteria | Evidence Types | Frequency |
|----------|--------------|-----------|
| CC6.1 (Access) | User access listings, access request tickets, quarterly reviews | Quarterly |
| CC6.2 (Registration) | Onboarding/offboarding tickets, provisioning logs | Per event |
| CC6.3 (RBAC) | Role definitions, permission matrices, access reviews | Quarterly |
| CC6.6 (Boundaries) | Firewall rules, network diagrams, pen test reports | Annual + changes |
| CC7.1 (Detection) | SIEM alerts, monitoring configurations, dashboards | Continuous |
| CC7.2 (Monitoring) | Alert response evidence, escalation logs | Per event |
| CC7.3 (Evaluation) | Incident tickets, root cause analysis, remediation | Per incident |
| CC8.1 (Changes) | Change tickets, approval workflows, deployment logs | Per change |
| CC9.2 (Vendors) | Vendor assessments, SOC reports, contracts | Annual |

### 4.5 Complementary User Entity Controls (CUECs)

SOC 2 reports often include CUECs — controls that the service organization assumes the user entity (customer) has in place. Common CUECs:

- User entity responsible for provisioning/deprovisioning their own users
- User entity responsible for securing their own endpoint accessing the service
- User entity responsible for classifying data before ingestion
- User entity responsible for backup of data extracted from the service
- User entity responsible for monitoring their own usage patterns

### 4.6 Bridge Letters

When a SOC 2 report period ends and the new report is not yet available, a **bridge letter** (or gap letter) provides assertion that:
- No material changes to controls since the report period ended
- No known control deficiencies or failures during the gap period
- Signed by management of the service organization

Typically covers 3-6 months between report periods.

---

## 5. Audit Evidence Collection

### 5.1 Evidence Types and Quality

**Evidence Taxonomy:**

| Type | Examples | Strength |
|------|----------|----------|
| Policy Documents | Security policy, acceptable use policy, SDLC policy | Low (intent only) |
| Procedures | Runbooks, SOPs, work instructions | Low-Medium |
| Configurations | Firewall rules, IAM policies, encryption settings | High |
| Logs | Audit trails, access logs, change logs | High |
| Screenshots | System settings, dashboard states, configurations | Medium |
| Reports | Vulnerability scan results, pen test reports, audit reports | High |
| Tickets | Change requests, incident tickets, access requests | High |
| Interviews | Staff attestation of understanding and practice | Medium |
| Observations | Walk-throughs, physical inspections | Medium |
| Automated Outputs | Compliance platform exports, API-pulled evidence | High |

**Evidence Quality Attributes (CART):**

- **Completeness**: Evidence covers the full audit period, not just a snapshot
- **Accuracy**: Evidence reflects the actual state (not fabricated/staged)
- **Relevance**: Evidence directly addresses the control requirement
- **Timeliness**: Evidence is current and covers the appropriate time period

### 5.2 Chain of Custody for Digital Evidence

When evidence may be used in legal proceedings (breach notification, litigation, regulatory enforcement):

```
Evidence Chain of Custody Record
================================
Evidence ID: EVD-2026-0042
Description: Firewall rule export showing CDE segmentation
Collection Date: 2026-05-07T14:30:00Z
Collected By: Renan A. Macena (Security Operations)
Collection Method: API export via Palo Alto Panorama REST API
Hash (SHA-256): a3f2b8c91d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a
Storage Location: Evidence vault /compliance/2026/Q2/network/
Access Controls: Read-only to compliance team, audit committee
Integrity Verification: Daily hash comparison via cron job

Transfer Log:
  2026-05-07 14:30 UTC - Collected by R. Macena
  2026-05-07 14:35 UTC - Uploaded to evidence vault
  2026-05-08 09:00 UTC - Accessed by QSA (read-only)
  2026-05-08 15:00 UTC - Hash verified (match confirmed)
```

### 5.3 Automated Evidence Collection Scripts

**AWS Configuration Evidence (Python + boto3):**

```python
#!/usr/bin/env python3
"""
Automated evidence collection for AWS environments.
Collects: IAM policies, Security Groups, encryption status,
          CloudTrail config, S3 bucket policies, KMS keys.
"""

import boto3
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path


class AWSEvidenceCollector:
    def __init__(self, output_dir: str = "/evidence/aws"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.manifest = []

    def _save_evidence(self, category: str, name: str, data: dict) -> str:
        """Save evidence with integrity hash."""
        filepath = self.output_dir / category / f"{name}.json"
        filepath.parent.mkdir(parents=True, exist_ok=True)

        content = json.dumps(data, indent=2, default=str)
        sha256 = hashlib.sha256(content.encode()).hexdigest()

        filepath.write_text(content)

        record = {
            "file": str(filepath),
            "category": category,
            "name": name,
            "collected_at": self.timestamp,
            "sha256": sha256,
            "size_bytes": len(content),
        }
        self.manifest.append(record)
        return sha256

    def collect_iam_policies(self):
        """CC6.1, CC6.3 - Access control policies."""
        iam = boto3.client("iam")

        # Password policy
        try:
            password_policy = iam.get_account_password_policy()
            self._save_evidence("iam", "password_policy", password_policy)
        except iam.exceptions.NoSuchEntityException:
            self._save_evidence("iam", "password_policy", {"status": "NOT_CONFIGURED"})

        # MFA status for all users
        users = iam.list_users()["Users"]
        mfa_report = []
        for user in users:
            mfa_devices = iam.list_mfa_devices(UserName=user["UserName"])
            mfa_report.append({
                "user": user["UserName"],
                "mfa_enabled": len(mfa_devices["MFADevices"]) > 0,
                "mfa_devices": len(mfa_devices["MFADevices"]),
                "created": user["CreateDate"],
                "password_last_used": user.get("PasswordLastUsed"),
            })
        self._save_evidence("iam", "mfa_status", {"users": mfa_report})

        # Privileged policies (admin access)
        admin_users = []
        for user in users:
            policies = iam.list_attached_user_policies(UserName=user["UserName"])
            for policy in policies["AttachedPolicies"]:
                if "AdministratorAccess" in policy["PolicyName"]:
                    admin_users.append(user["UserName"])
        self._save_evidence("iam", "admin_users", {"admin_users": admin_users})

    def collect_encryption_status(self):
        """CC6.1, Req 3/4 - Encryption at rest and in transit."""
        # S3 bucket encryption
        s3 = boto3.client("s3")
        buckets = s3.list_buckets()["Buckets"]
        encryption_report = []
        for bucket in buckets:
            try:
                enc = s3.get_bucket_encryption(Bucket=bucket["Name"])
                encryption_report.append({
                    "bucket": bucket["Name"],
                    "encrypted": True,
                    "rules": enc["ServerSideEncryptionConfiguration"]["Rules"],
                })
            except s3.exceptions.ClientError:
                encryption_report.append({
                    "bucket": bucket["Name"],
                    "encrypted": False,
                })
        self._save_evidence("encryption", "s3_encryption", {"buckets": encryption_report})

        # EBS volume encryption
        ec2 = boto3.client("ec2")
        volumes = ec2.describe_volumes()["Volumes"]
        ebs_report = [
            {
                "volume_id": v["VolumeId"],
                "encrypted": v["Encrypted"],
                "kms_key_id": v.get("KmsKeyId"),
                "state": v["State"],
                "size_gb": v["Size"],
            }
            for v in volumes
        ]
        self._save_evidence("encryption", "ebs_encryption", {"volumes": ebs_report})

        # RDS encryption
        rds = boto3.client("rds")
        instances = rds.describe_db_instances()["DBInstances"]
        rds_report = [
            {
                "db_identifier": db["DBInstanceIdentifier"],
                "encrypted": db["StorageEncrypted"],
                "engine": db["Engine"],
                "kms_key_id": db.get("KmsKeyId"),
            }
            for db in instances
        ]
        self._save_evidence("encryption", "rds_encryption", {"instances": rds_report})

    def collect_network_security(self):
        """CC6.6, Req 1 - Network segmentation and security groups."""
        ec2 = boto3.client("ec2")

        # Security groups
        sgs = ec2.describe_security_groups()["SecurityGroups"]
        overly_permissive = []
        for sg in sgs:
            for rule in sg.get("IpPermissions", []):
                for ip_range in rule.get("IpRanges", []):
                    if ip_range.get("CidrIp") == "0.0.0.0/0":
                        overly_permissive.append({
                            "sg_id": sg["GroupId"],
                            "sg_name": sg["GroupName"],
                            "port": rule.get("FromPort"),
                            "protocol": rule.get("IpProtocol"),
                        })
        self._save_evidence("network", "security_groups", {"groups": sgs})
        self._save_evidence("network", "overly_permissive_rules", {"rules": overly_permissive})

        # VPC flow logs
        vpcs = ec2.describe_vpcs()["Vpcs"]
        flow_logs = ec2.describe_flow_logs()["FlowLogs"]
        vpc_flow_status = []
        for vpc in vpcs:
            has_flow_log = any(
                fl["ResourceId"] == vpc["VpcId"] for fl in flow_logs
            )
            vpc_flow_status.append({
                "vpc_id": vpc["VpcId"],
                "flow_logs_enabled": has_flow_log,
            })
        self._save_evidence("network", "vpc_flow_logs", {"vpcs": vpc_flow_status})

    def collect_logging_config(self):
        """CC7.1, Req 10 - Logging and monitoring configuration."""
        # CloudTrail
        ct = boto3.client("cloudtrail")
        trails = ct.describe_trails()["trailList"]
        trail_status = []
        for trail in trails:
            status = ct.get_trail_status(Name=trail["TrailARN"])
            trail_status.append({
                "name": trail["Name"],
                "is_multi_region": trail.get("IsMultiRegionTrail"),
                "is_logging": status["IsLogging"],
                "has_log_file_validation": trail.get("LogFileValidationEnabled"),
                "s3_bucket": trail.get("S3BucketName"),
                "kms_key": trail.get("KmsKeyId"),
            })
        self._save_evidence("logging", "cloudtrail_config", {"trails": trail_status})

    def generate_manifest(self):
        """Generate evidence manifest with integrity hashes."""
        manifest_data = {
            "collection_timestamp": self.timestamp,
            "total_evidence_files": len(self.manifest),
            "evidence": self.manifest,
        }
        manifest_path = self.output_dir / "MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest_data, indent=2))
        return manifest_path


if __name__ == "__main__":
    collector = AWSEvidenceCollector()
    collector.collect_iam_policies()
    collector.collect_encryption_status()
    collector.collect_network_security()
    collector.collect_logging_config()
    manifest = collector.generate_manifest()
    print(f"Evidence collection complete. Manifest: {manifest}")
```

### 5.4 Evidence Management Platforms

**Platform Comparison:**

| Platform | Strengths | Limitations | Best For |
|----------|-----------|-------------|----------|
| Vanta | 300+ integrations, mature, large partner network | Higher cost, enterprise focus | Series B+ SaaS |
| Drata | Modern UI, strong automation, custom frameworks | Newer, fewer integrations | Growth-stage startups |
| Secureframe | AI-powered, fast onboarding, good for SOC 2 | Smaller than Vanta/Drata | Early-stage startups |
| Tugboat Logic | Policy templates, risk management | Acquired by OneTrust | Policy-heavy orgs |
| Sprinto | Cost-effective, good for ISO 27001 | Smaller ecosystem | International companies |
| Thoropass (Laika) | Combined platform + audit firm | Less flexibility in auditor choice | One-stop-shop |
| Anecdotes | Enterprise GRC, custom frameworks | Complex, expensive | Large enterprises |

**Integration Architecture (Vanta example):**

```
┌─────────────────────────────────────────────────────────┐
│                    Vanta Platform                         │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  AWS     │  GCP     │  Azure   │  GitHub  │  Okta       │
│  Config  │  SCC     │  Policy  │  Repos   │  Users      │
├──────────┼──────────┼──────────┼──────────┼─────────────┤
│  Jira    │  Slack   │ Datadog  │  Jamf    │ CrowdStrike │
│  Tickets │  Comms   │  Logs    │  MDM     │  EDR        │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│           Continuous Control Monitoring                    │
│           Real-time Test Execution                        │
│           Automated Evidence Collection                   │
│           Alert on Control Failure                        │
├──────────────────────────────────────────────────────────┤
│  Dashboard │ Evidence Vault │ Audit Portal │ Reports     │
└──────────────────────────────────────────────────────────┘
```

### 5.5 Manual Evidence Collection

Not all evidence can be automated. Manual collection processes:

**Interviews:**
- Structured questions aligned to control objectives
- Document responses contemporaneously
- Have interviewee sign off on notes
- Record date, participants, topics covered, key findings

**Observations:**
- Physical walk-throughs of data centers, offices
- Watch personnel perform security procedures
- Document what was observed vs what policy states
- Photograph physical controls (badges, locks, cameras)

**Walk-throughs:**
- Follow a transaction end-to-end through the system
- Document each control point encountered
- Note where manual intervention is required
- Identify single points of failure

---

## 6. Automazione Compliance

### 6.1 Continuous Compliance Monitoring

Real-time compliance monitoring replaces periodic manual checks with automated, continuous validation:

```yaml
# Continuous compliance monitoring architecture
monitoring_stack:
  data_sources:
    - cloud_apis: [aws_config, azure_policy, gcp_scc]
    - identity: [okta_logs, azure_ad_audit]
    - endpoints: [crowdstrike_api, jamf_api]
    - code: [github_api, gitlab_api]
    - infrastructure: [terraform_state, ansible_facts]
    - tickets: [jira_api, servicenow_api]

  processing:
    - stream_processor: kafka_streams
    - rule_engine: custom_opa_policies
    - storage: postgresql + s3

  outputs:
    - dashboard: grafana
    - alerts: pagerduty_for_critical, slack_for_warning
    - evidence: auto_archived_to_compliance_vault
    - reports: weekly_summary, monthly_executive
```

### 6.2 Compliance-as-Code with InSpec

Chef InSpec allows you to express compliance requirements as executable code:

**PCI-DSS Requirement 2 — Secure Configuration Profile:**

```ruby
# pci_dss_req2.rb - InSpec profile for PCI-DSS Requirement 2
# Secure configurations for all system components

title 'PCI-DSS 4.0 Requirement 2 - Secure Configurations'

control 'pci-2.2.1' do
  title 'System hardening standards applied'
  desc 'Verify system components have hardening standards applied'
  impact 1.0
  tag framework: 'PCI-DSS'
  tag requirement: '2.2.1'
  tag severity: 'high'

  # Verify unnecessary services disabled
  describe service('telnet') do
    it { should_not be_enabled }
    it { should_not be_running }
  end

  describe service('rsh') do
    it { should_not be_enabled }
  end

  describe service('rlogin') do
    it { should_not be_enabled }
  end

  # Verify only necessary ports open
  describe port(23) do
    it { should_not be_listening }
  end

  describe port(21) do
    it { should_not be_listening }
  end
end

control 'pci-2.2.2' do
  title 'Vendor default accounts managed'
  desc 'Default accounts removed, disabled, or passwords changed'
  impact 1.0
  tag framework: 'PCI-DSS'
  tag requirement: '2.2.2'

  # Check no default passwords in common services
  describe file('/etc/shadow') do
    its('content') { should_not match(/^(admin|root|test|guest):([^!*])/) }
  end

  # MySQL default accounts
  if service('mysql').running?
    describe command("mysql -u root --password='' -e 'SELECT 1' 2>&1") do
      its('exit_status') { should_not eq 0 }
    end
  end
end

control 'pci-2.2.4' do
  title 'Security parameters configured'
  desc 'System security parameters configured to prevent misuse'
  impact 0.7
  tag framework: 'PCI-DSS'
  tag requirement: '2.2.4'

  # SSH hardening
  describe sshd_config do
    its('Protocol') { should eq '2' }
    its('PermitRootLogin') { should eq 'no' }
    its('PermitEmptyPasswords') { should eq 'no' }
    its('MaxAuthTries') { should cmp <= 4 }
    its('ClientAliveInterval') { should cmp <= 300 }
    its('ClientAliveCountMax') { should cmp <= 3 }
    its('LoginGraceTime') { should cmp <= 60 }
    its('Ciphers') { should_not include 'arcfour' }
    its('Ciphers') { should_not include '3des-cbc' }
    its('MACs') { should_not include 'hmac-md5' }
  end

  # Kernel hardening
  describe kernel_parameter('net.ipv4.ip_forward') do
    its('value') { should eq 0 }
  end

  describe kernel_parameter('net.ipv4.conf.all.accept_redirects') do
    its('value') { should eq 0 }
  end

  describe kernel_parameter('net.ipv4.conf.all.send_redirects') do
    its('value') { should eq 0 }
  end
end

control 'pci-2.2.5' do
  title 'Non-console administrative access encrypted'
  desc 'All non-console admin access uses strong cryptography'
  impact 1.0
  tag framework: 'PCI-DSS'
  tag requirement: '2.2.5'

  describe sshd_config do
    it { should exist }
    its('Protocol') { should eq '2' }
  end

  # No unencrypted admin protocols
  %w[telnet rsh rlogin].each do |svc|
    describe service(svc) do
      it { should_not be_running }
    end
  end

  # HTTPS for web admin interfaces
  describe port(80) do
    it { should_not be_listening }
  end
end
```

**ISO 27001 A.8.8 — Vulnerability Management Profile:**

```ruby
# iso27001_a8_8.rb - Vulnerability Management Controls

title 'ISO 27001:2022 A.8.8 - Technical Vulnerability Management'

control 'iso-a.8.8-patch-currency' do
  title 'Systems are patched within defined timelines'
  desc 'Critical patches applied within 14 days, high within 30 days'
  impact 0.9
  tag framework: 'ISO27001'
  tag control: 'A.8.8'

  # Check OS patch level (Ubuntu/Debian)
  if os.debian?
    describe command('apt list --upgradable 2>/dev/null | grep -c security') do
      its('stdout.strip.to_i') { should cmp <= 5 }
    end

    # No critical security updates pending > 14 days
    describe command('stat -c %Y /var/lib/apt/periodic/update-stamp 2>/dev/null || echo 0') do
      its('stdout.strip.to_i') { should cmp >= (Time.now.to_i - 86400 * 7) }
    end
  end

  # Check OS patch level (RHEL/CentOS)
  if os.redhat?
    describe command('yum check-update --security 2>/dev/null | grep -c "^[a-zA-Z]"') do
      its('stdout.strip.to_i') { should cmp <= 5 }
    end
  end
end

control 'iso-a.8.8-vuln-scanning' do
  title 'Vulnerability scanning is active and current'
  desc 'Evidence that vulnerability scanning runs at least weekly'
  impact 0.8
  tag framework: 'ISO27001'
  tag control: 'A.8.8'

  # Check if vulnerability scanner agent is running
  describe.one do
    describe service('qualys-cloud-agent') do
      it { should be_running }
    end
    describe service('nessus') do
      it { should be_running }
    end
    describe service('amazon-ssm-agent') do
      it { should be_running }
    end
  end
end

control 'iso-a.8.8-auto-updates' do
  title 'Automatic security updates configured'
  desc 'Unattended security updates enabled for critical patches'
  impact 0.7
  tag framework: 'ISO27001'
  tag control: 'A.8.8'

  if os.debian?
    describe file('/etc/apt/apt.conf.d/50unattended-upgrades') do
      it { should exist }
      its('content') { should match(/Unattended-Upgrade::Allowed-Origins/) }
      its('content') { should match(/-security/) }
    end

    describe service('unattended-upgrades') do
      it { should be_enabled }
    end
  end
end
```

### 6.3 AWS Config Rules for Compliance

```json
{
  "ConfigRules": [
    {
      "ConfigRuleName": "pci-iam-password-policy",
      "Description": "PCI-DSS 8.3.6 - Password complexity requirements",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "IAM_PASSWORD_POLICY"
      },
      "InputParameters": {
        "RequireUppercaseCharacters": "true",
        "RequireLowercaseCharacters": "true",
        "RequireSymbols": "true",
        "RequireNumbers": "true",
        "MinimumPasswordLength": "12",
        "PasswordReusePrevention": "4",
        "MaxPasswordAge": "90"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "8.3.6"}
      ]
    },
    {
      "ConfigRuleName": "pci-encryption-at-rest-s3",
      "Description": "PCI-DSS Req 3 - S3 buckets encrypted at rest",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "3.5.1"}
      ]
    },
    {
      "ConfigRuleName": "pci-encryption-at-rest-ebs",
      "Description": "PCI-DSS Req 3 - EBS volumes encrypted",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "ENCRYPTED_VOLUMES"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "3.5.1"}
      ]
    },
    {
      "ConfigRuleName": "pci-encryption-at-rest-rds",
      "Description": "PCI-DSS Req 3 - RDS instances encrypted",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RDS_STORAGE_ENCRYPTED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "3.5.1"}
      ]
    },
    {
      "ConfigRuleName": "soc2-cloudtrail-enabled",
      "Description": "SOC 2 CC7.1 - CloudTrail logging enabled",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "CLOUD_TRAIL_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "SOC2"},
        {"Key": "Criteria", "Value": "CC7.1"}
      ]
    },
    {
      "ConfigRuleName": "soc2-multi-region-cloudtrail",
      "Description": "SOC 2 CC7.1 - Multi-region CloudTrail",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "MULTI_REGION_CLOUD_TRAIL_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "SOC2"},
        {"Key": "Criteria", "Value": "CC7.1"}
      ]
    },
    {
      "ConfigRuleName": "iso27001-mfa-enabled",
      "Description": "ISO 27001 A.8.5 - MFA for IAM users",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "IAM_USER_MFA_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "ISO27001"},
        {"Key": "Control", "Value": "A.8.5"}
      ]
    },
    {
      "ConfigRuleName": "iso27001-root-mfa",
      "Description": "ISO 27001 A.8.2 - Root account MFA",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "ROOT_ACCOUNT_MFA_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "ISO27001"},
        {"Key": "Control", "Value": "A.8.2"}
      ]
    },
    {
      "ConfigRuleName": "pci-vpc-flow-logs",
      "Description": "PCI-DSS Req 10 - VPC flow logs enabled",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "VPC_FLOW_LOGS_ENABLED"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "10.2"}
      ]
    },
    {
      "ConfigRuleName": "pci-no-public-access-sg",
      "Description": "PCI-DSS Req 1 - No unrestricted SSH/RDP",
      "Source": {
        "Owner": "AWS",
        "SourceIdentifier": "RESTRICTED_INCOMING_TRAFFIC"
      },
      "InputParameters": {
        "blockedPort1": "22",
        "blockedPort2": "3389"
      },
      "Tags": [
        {"Key": "Framework", "Value": "PCI-DSS-4.0"},
        {"Key": "Requirement", "Value": "1.3.2"}
      ]
    }
  ]
}
```

### 6.4 Compliance-as-Code with Open Policy Agent (OPA)

```rego
# policy/pci_network.rego
# PCI-DSS Requirement 1 - Network Security Controls

package pci.network

import future.keywords.in

# Deny security groups with unrestricted inbound access to CDE
deny[msg] {
    sg := input.security_groups[_]
    rule := sg.ip_permissions[_]
    range := rule.ip_ranges[_]
    range.cidr_ip == "0.0.0.0/0"
    sg.tags.environment == "cde"
    msg := sprintf(
        "VIOLATION: Security group %s in CDE allows unrestricted access on port %d from 0.0.0.0/0",
        [sg.group_id, rule.from_port]
    )
}

# Deny CDE resources without encryption
deny[msg] {
    resource := input.ec2_instances[_]
    resource.tags.environment == "cde"
    volume := resource.block_device_mappings[_]
    not volume.ebs.encrypted
    msg := sprintf(
        "VIOLATION: Instance %s in CDE has unencrypted volume %s",
        [resource.instance_id, volume.device_name]
    )
}

# Require VPC flow logs for CDE VPCs
deny[msg] {
    vpc := input.vpcs[_]
    vpc.tags.environment == "cde"
    not vpc_has_flow_logs(vpc.vpc_id)
    msg := sprintf(
        "VIOLATION: CDE VPC %s does not have flow logs enabled",
        [vpc.vpc_id]
    )
}

vpc_has_flow_logs(vpc_id) {
    fl := input.flow_logs[_]
    fl.resource_id == vpc_id
    fl.flow_log_status == "ACTIVE"
}

# Require network segmentation between CDE and non-CDE
deny[msg] {
    route := input.route_tables[_]
    route.vpc_tags.environment == "cde"
    destination := route.routes[_]
    destination.destination_cidr_block == "0.0.0.0/0"
    destination.gateway_id != null
    msg := sprintf(
        "VIOLATION: CDE route table %s has default route to internet gateway %s",
        [route.route_table_id, destination.gateway_id]
    )
}
```

### 6.5 Automated Reporting and Dashboard Configuration

**Grafana Dashboard for Compliance Status (JSON model):**

```json
{
  "dashboard": {
    "title": "Compliance Control Status",
    "tags": ["compliance", "pci-dss", "soc2", "iso27001"],
    "panels": [
      {
        "title": "Overall Compliance Score",
        "type": "gauge",
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "sum(compliance_control_passing) / sum(compliance_control_total) * 100",
            "legendFormat": "Compliance %"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 80, "color": "yellow"},
                {"value": 95, "color": "green"}
              ]
            },
            "min": 0,
            "max": 100
          }
        }
      },
      {
        "title": "Controls by Framework",
        "type": "barchart",
        "gridPos": {"h": 8, "w": 10, "x": 6, "y": 0},
        "targets": [
          {
            "expr": "compliance_control_passing{framework=~\".*\"}",
            "legendFormat": "{{framework}} - Passing"
          },
          {
            "expr": "compliance_control_failing{framework=~\".*\"}",
            "legendFormat": "{{framework}} - Failing"
          }
        ]
      },
      {
        "title": "Critical Control Failures",
        "type": "table",
        "gridPos": {"h": 10, "w": 16, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "compliance_control_status{status=\"failing\", severity=\"critical\"}",
            "format": "table",
            "instant": true
          }
        ],
        "transformations": [
          {
            "id": "organize",
            "options": {
              "includeByName": {
                "control_id": true,
                "framework": true,
                "description": true,
                "last_check": true,
                "remediation": true
              }
            }
          }
        ]
      },
      {
        "title": "Evidence Collection Status",
        "type": "stat",
        "gridPos": {"h": 4, "w": 16, "x": 0, "y": 18},
        "targets": [
          {
            "expr": "evidence_collection_last_success_timestamp",
            "legendFormat": "Last Collection"
          },
          {
            "expr": "evidence_items_collected_total",
            "legendFormat": "Total Items"
          },
          {
            "expr": "evidence_items_stale",
            "legendFormat": "Stale Items"
          }
        ]
      }
    ]
  }
}
```

---

## 7. Security Testing per Compliance

### 7.1 PCI-DSS Requirement 11 — Security Testing

Requirement 11 mandates regular security testing:

**11.3 — Vulnerability Scanning:**

| Scan Type | Frequency | Scope | Tool | Output |
|-----------|-----------|-------|------|--------|
| Internal vulnerability scan | Quarterly minimum | All in-scope systems | Nessus, Qualys, OpenVAS | Scan report |
| External vulnerability scan (ASV) | Quarterly minimum | All external-facing IPs/URLs | ASV-approved vendor | Passing ASV report |
| Rescan after remediation | After fix | Affected systems | Same tool | Confirmation scan |
| After significant change | After change | Changed systems | Same tool | Scan report |

**ASV (Approved Scanning Vendor) Requirements:**

- Vendor must be PCI SSC-approved (listed on PCI SSC website)
- External scans must achieve a "passing" result (no CVSS >= 4.0 vulnerabilities)
- Exceptions require documented compensating controls
- False positives must be disputed and documented with ASV
- Scans must cover all external-facing IP addresses and domains

**11.4 — Penetration Testing:**

| Aspect | PCI-DSS Requirement |
|--------|-------------------|
| Frequency | At least annually AND after significant changes |
| Scope | CDE and connected-to systems, external perimeter |
| Methodology | Industry-accepted (PTES, OWASP, NIST SP 800-115) |
| Coverage | Network layer AND application layer |
| Segmentation testing | Every 6 months (service providers) / annually (merchants) |
| Remediation | All exploitable vulnerabilities addressed and retested |
| Tester qualifications | Organizational independence (internal or external) |

**11.5 — Intrusion Detection:**

- IDS/IPS at CDE perimeter and critical points
- All traffic monitored for suspicious activity
- Alerts generated and investigated
- Signatures/rules kept current

**11.6 — Payment Page Integrity (New in 4.0):**

- Mechanism to detect unauthorized changes to HTTP headers and script content on payment pages
- Detect modifications to payment page scripts
- Alert on unauthorized changes
- Examples: Content Security Policy reporting, script integrity monitoring (SRI), file integrity monitoring for web content

### 7.2 ISO 27001 A.8.8 — Vulnerability Management

ISO 27001 A.8.8 requires:

- Regular identification of technical vulnerabilities in systems
- Evaluation of exposure to identified vulnerabilities
- Timely remediation based on risk
- Defined patch management timelines:

```yaml
vulnerability_sla:
  critical:
    cvss: "9.0-10.0"
    patch_timeline: "72 hours"
    interim_mitigation: "24 hours (if patch unavailable)"
  high:
    cvss: "7.0-8.9"
    patch_timeline: "14 days"
    interim_mitigation: "72 hours"
  medium:
    cvss: "4.0-6.9"
    patch_timeline: "30 days"
    interim_mitigation: "As needed"
  low:
    cvss: "0.1-3.9"
    patch_timeline: "90 days"
    interim_mitigation: "None required"
```

### 7.3 SOC 2 CC4.1 — Monitoring Activities

CC4.1 requires that ongoing evaluations and separate evaluations determine whether components of internal control are present and functioning. Evidence requirements:

- Security monitoring tool configurations
- Alert rules and escalation procedures
- Evidence of alert investigation (tickets, timelines)
- Metrics: alert volume, response time, false positive rate
- Regular review of monitoring effectiveness

### 7.4 Internal vs External Scanning

| Aspect | Internal Scan | External Scan |
|--------|--------------|---------------|
| Perspective | Inside the network | Internet-facing |
| Targets | All in-scope internal IPs | All public IPs/URLs |
| Credentials | Authenticated (deeper) | Unauthenticated (attacker view) |
| Tools | Nessus, Qualys, OpenVAS | ASV-validated vendor |
| Passing criteria | All high/critical remediated OR risk-accepted | No CVSS >= 4.0 (PCI ASV) |
| Run by | Internal team or consultant | ASV (for PCI), internal or external (others) |

### 7.5 Remediation Tracking

```yaml
# remediation_tracker.yaml - Template for tracking vulnerability remediation

finding:
  id: "VULN-2026-0142"
  source: "Q2 Internal Vulnerability Scan"
  discovered: "2026-04-15"
  scanner: "Nessus Professional 10.x"

vulnerability:
  title: "OpenSSL CVE-2026-XXXX Buffer Overflow"
  cvss_score: 9.1
  cvss_vector: "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
  cwe: "CWE-120"
  affected_systems:
    - "web-prod-01 (10.0.1.10)"
    - "web-prod-02 (10.0.1.11)"
    - "api-prod-01 (10.0.2.10)"
  frameworks_impacted:
    - "PCI-DSS 4.0 Req 6.3.3"
    - "ISO 27001 A.8.8"
    - "SOC 2 CC7.1"

remediation:
  sla_deadline: "2026-04-18"  # 72h for critical
  owner: "platform-engineering"
  status: "remediated"
  actions:
    - date: "2026-04-15"
      action: "Interim mitigation: WAF rule blocking exploit pattern"
      by: "security-ops"
    - date: "2026-04-16"
      action: "Patch tested in staging environment"
      by: "platform-engineering"
    - date: "2026-04-17"
      action: "Rolling deployment to production"
      by: "platform-engineering"
    - date: "2026-04-17"
      action: "Rescan confirms remediation"
      by: "security-ops"

verification:
  rescan_date: "2026-04-17"
  rescan_result: "PASS - vulnerability not detected"
  evidence_location: "/evidence/2026/Q2/vuln-scans/rescan-2026-04-17.pdf"
```

---

## 8. Audit Preparation e Gestione

### 8.1 Audit Readiness Assessment

**Gap Analysis Process:**

```
Phase 1: Scope Definition (Week 1)
  ├── Identify applicable framework requirements
  ├── Define system boundaries
  ├── Identify data flows
  └── Document shared responsibilities (cloud/SaaS)

Phase 2: Current State Assessment (Weeks 2-4)
  ├── Interview control owners
  ├── Review existing documentation
  ├── Test control effectiveness (sample testing)
  └── Map existing controls to requirements

Phase 3: Gap Identification (Week 5)
  ├── Document missing controls
  ├── Identify partially implemented controls
  ├── Note inadequate evidence
  └── Assess evidence collection capability

Phase 4: Remediation Planning (Week 6)
  ├── Prioritize gaps (critical → low)
  ├── Estimate effort and resources
  ├── Create project plan with milestones
  └── Assign ownership and deadlines

Phase 5: Remediation Execution (Weeks 7-20)
  ├── Implement missing controls
  ├── Enhance partial controls
  ├── Establish evidence collection
  └── Validate remediation effectiveness
```

### 8.2 Working with Auditors

**What Auditors Expect:**

- Prompt, organized responses to information requests
- Single point of contact (audit coordinator)
- Pre-organized evidence indexed to control requirements
- Honest disclosure of known issues (better from you than their discovery)
- Documented compensating controls for any gaps
- Management support and engagement

**What NOT to Do:**

- Do not provide evidence outside the scope (invites additional scrutiny)
- Do not volunteer information about out-of-scope systems
- Do not explain away findings — acknowledge and present remediation
- Do not delay evidence delivery (creates suspicion)
- Do not provide draft/unofficial documents as evidence
- Do not argue with auditors during fieldwork (discuss in close-out)

**Audit Communication Protocol:**

```yaml
audit_communication:
  coordinator: "IT Compliance Manager"
  backup: "CISO"

  information_requests:
    response_sla: "3 business days"
    format: "Structured response with evidence reference"
    tracking: "Shared tracker (e.g., Excel, Jira board)"

  meetings:
    kickoff: "Before fieldwork begins"
    daily_standup: "15 min during fieldwork"
    weekly_status: "During extended audits"
    close_out: "After fieldwork, before report draft"

  escalation:
    disagreement_on_finding: "Discuss with audit manager"
    scope_dispute: "Escalate to engagement partner"
    timeline_issue: "Escalate to coordinator → CISO"
```

### 8.3 Common Audit Findings

**Top 10 Most Frequent Findings (by framework):**

| # | Finding | PCI-DSS | ISO 27001 | SOC 2 |
|---|---------|---------|-----------|-------|
| 1 | Incomplete access reviews | Req 7.2.5 | A.5.18 | CC6.2 |
| 2 | Missing/outdated policies | Req 12.1 | A.5.1 | CC1.3 |
| 3 | Insufficient logging | Req 10.2 | A.8.15 | CC7.1 |
| 4 | Patch management gaps | Req 6.3.3 | A.8.8 | CC7.1 |
| 5 | Weak password policy | Req 8.3.6 | A.8.5 | CC6.1 |
| 6 | Missing MFA | Req 8.4.2 | A.8.5 | CC6.1 |
| 7 | No formal change management | Req 6.5 | A.8.32 | CC8.1 |
| 8 | Vendor management gaps | Req 12.8 | A.5.19 | CC9.2 |
| 9 | Security awareness deficiency | Req 12.6 | A.6.3 | CC1.4 |
| 10 | Inadequate incident response | Req 12.10 | A.5.24 | CC7.3 |

### 8.4 Corrective Action Plans (CAP)

```yaml
# Corrective Action Plan Template
cap:
  id: "CAP-2026-007"
  audit: "ISO 27001 Surveillance Audit - April 2026"
  finding:
    id: "NC-003"
    type: "Minor Non-Conformity"
    clause: "ISO 27001:2022 Clause 9.2 (Internal Audit)"
    description: |
      Internal audit program does not cover all Annex A controls
      over the three-year certification cycle. Evidence shows that
      A.7.x (Physical Controls) and A.8.31 (Separation of environments)
      have not been audited in the current cycle.
    auditor: "External CB Auditor"
    date_raised: "2026-04-22"

  root_cause_analysis:
    method: "5 Whys"
    analysis: |
      Why 1: Physical controls not audited → Audit schedule only covers IT controls
      Why 2: Schedule only covers IT → Designed by IT team without facilities input
      Why 3: No facilities input → Audit program ownership unclear
      Why 4: Ownership unclear → No RACI matrix for internal audit program
      Why 5: No RACI → ISMS roles and responsibilities not fully defined for audit
    root_cause: "Incomplete RACI definition for internal audit program"

  corrective_actions:
    - action: "Define RACI matrix for internal audit program"
      owner: "ISMS Manager"
      deadline: "2026-05-15"
      status: "completed"
    - action: "Revise audit schedule to include all Annex A controls"
      owner: "Internal Audit Lead"
      deadline: "2026-05-30"
      status: "completed"
    - action: "Conduct makeup audits for A.7.x and A.8.31"
      owner: "Internal Audit Team"
      deadline: "2026-06-30"
      status: "in_progress"
    - action: "Implement annual audit schedule review with all stakeholders"
      owner: "ISMS Manager"
      deadline: "2026-05-30"
      status: "completed"

  effectiveness_review:
    date: "2026-07-15"
    method: "Verify revised schedule covers all controls; verify makeup audits completed"
    reviewer: "CISO"
    result: "pending"

  closure:
    date: null
    approved_by: null
    evidence_location: "/evidence/2026/caps/CAP-2026-007/"
```

### 8.5 Post-Audit Activities

After the audit report is received:

1. **Findings Categorization**: Classify by severity (critical, major, minor, observation)
2. **Root Cause Analysis**: For each finding, perform 5-Whys or fishbone analysis
3. **Remediation Planning**: CAP for each finding with owner, deadline, success criteria
4. **Remediation Execution**: Implement fixes, collect evidence of remediation
5. **Effectiveness Verification**: After fix, verify it actually addresses the finding
6. **Evidence Archival**: Archive all audit artifacts (report, evidence provided, CAPs)
7. **Lessons Learned**: Update procedures to prevent recurrence
8. **Management Reporting**: Brief management on outcomes, risks, and investment needs

---

## 9. Risk Management

### 9.1 Risk Assessment Methodology — ISO 27005 Aligned

```
┌────────────────────────────────────────────────────┐
│              RISK MANAGEMENT PROCESS                │
├────────────────────────────────────────────────────┤
│                                                    │
│  1. CONTEXT ESTABLISHMENT                          │
│     └── Scope, criteria, risk appetite             │
│                                                    │
│  2. RISK IDENTIFICATION                            │
│     ├── Asset identification                       │
│     ├── Threat identification                      │
│     ├── Vulnerability identification               │
│     └── Existing control identification            │
│                                                    │
│  3. RISK ANALYSIS                                  │
│     ├── Consequence assessment                     │
│     ├── Likelihood assessment                      │
│     └── Risk level determination                   │
│                                                    │
│  4. RISK EVALUATION                                │
│     ├── Compare against risk criteria              │
│     └── Prioritize for treatment                   │
│                                                    │
│  5. RISK TREATMENT                                 │
│     ├── Avoid (eliminate the activity)             │
│     ├── Reduce (implement controls)               │
│     ├── Transfer (insurance, outsource)            │
│     └── Accept (within appetite, documented)       │
│                                                    │
│  6. MONITORING AND REVIEW                          │
│     ├── Key Risk Indicators (KRIs)                 │
│     ├── Periodic reassessment                      │
│     └── Trigger-based reassessment                 │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 9.2 Risk Register Template

```yaml
# risk_register.yaml - Enterprise Risk Register

metadata:
  version: "3.2"
  last_review: "2026-05-01"
  next_review: "2026-08-01"
  owner: "CISO"
  approved_by: "Risk Committee"

risk_appetite:
  statement: |
    The organization accepts moderate risk in pursuit of business objectives.
    No single risk should threaten organizational viability.
  quantitative_threshold:
    annual_loss_expectancy_max: 2000000  # EUR
    single_loss_max: 5000000  # EUR
  qualitative_threshold:
    inherent_risk_max: "High"  # Critical risks must be treated
    residual_risk_max: "Medium"  # After treatment

risks:
  - id: "RISK-001"
    title: "Ransomware attack on production systems"
    category: "Cybersecurity"
    description: |
      Threat actor gains initial access via phishing or unpatched vulnerability,
      deploys ransomware across production systems including databases and file servers.
    asset: "Production infrastructure"
    threat_source: "Organized cybercrime"
    vulnerability: "Phishing susceptibility, patching delays"

    inherent_risk:
      likelihood: 4  # Likely
      impact: 5  # Catastrophic
      score: 20  # Critical
      rationale: "Industry data shows 1 in 3 organizations hit annually"

    existing_controls:
      - "EDR on all endpoints (CrowdStrike Falcon)"
      - "Email security gateway (Proofpoint)"
      - "Network segmentation (CDE isolated)"
      - "Immutable backups (Veeam + air-gapped copy)"
      - "Security awareness training (quarterly)"
      - "Patch management (14-day critical SLA)"

    residual_risk:
      likelihood: 2  # Unlikely (with controls)
      impact: 3  # Moderate (with backups and IR plan)
      score: 6  # Medium
      rationale: "Controls significantly reduce likelihood and impact through defense-in-depth"

    treatment:
      option: "Reduce + Transfer"
      actions:
        - "Maintain and enhance existing controls"
        - "Cyber insurance policy (EUR 5M coverage)"
        - "Quarterly tabletop exercises"
        - "Annual red team exercise"
      residual_acceptable: true
      accepted_by: "Risk Committee"
      acceptance_date: "2026-03-15"

    kris:
      - metric: "Phishing click rate"
        threshold: "< 5%"
        current: "3.2%"
        frequency: "Monthly"
      - metric: "Mean time to patch critical"
        threshold: "< 72 hours"
        current: "48 hours"
        frequency: "Monthly"
      - metric: "Backup restoration success rate"
        threshold: "> 99%"
        current: "99.7%"
        frequency: "Weekly"

    review_history:
      - date: "2026-03-15"
        reviewer: "Risk Committee"
        outcome: "Accepted at current residual level"
      - date: "2025-12-10"
        reviewer: "CISO"
        outcome: "Added immutable backup control"

  - id: "RISK-002"
    title: "Data breach of customer PII via cloud misconfiguration"
    category: "Data Protection"
    description: |
      Cloud storage or database exposed to internet due to misconfiguration,
      resulting in unauthorized access to customer personal data.
    asset: "Customer database (500K records)"
    threat_source: "Opportunistic attacker, automated scanners"
    vulnerability: "Cloud configuration errors, insufficient CSPM"

    inherent_risk:
      likelihood: 4
      impact: 4  # Major (GDPR fines + reputation)
      score: 16  # High

    existing_controls:
      - "CSPM tool (Wiz) with real-time alerting"
      - "IaC scanning (tfsec, checkov) in CI/CD"
      - "S3 Block Public Access (account-level)"
      - "Quarterly access reviews"
      - "Data classification policy enforced"
      - "Encryption at rest and in transit"

    residual_risk:
      likelihood: 1  # Rare
      impact: 3  # Moderate (encryption limits exposure)
      score: 3  # Low
      rationale: "Multiple preventive and detective controls minimize both probability and impact"

    treatment:
      option: "Reduce"
      actions:
        - "Maintain CSPM with auto-remediation"
        - "Enforce IaC-only infrastructure changes"
        - "DLP monitoring on data egress"
      residual_acceptable: true
      accepted_by: "CISO"
      acceptance_date: "2026-04-01"

    kris:
      - metric: "CSPM critical findings"
        threshold: "0"
        current: "0"
        frequency: "Real-time"
      - metric: "Public-facing resources count"
        threshold: "< 10 (known, approved)"
        current: "7"
        frequency: "Daily"

  - id: "RISK-003"
    title: "Third-party vendor compromise (supply chain)"
    category: "Supply Chain"
    description: |
      Critical SaaS vendor or library dependency compromised,
      leading to unauthorized access to our systems or data.
    asset: "Production environment, customer data"
    threat_source: "Nation-state, organized crime (targeting vendors)"
    vulnerability: "Dependency on third-party code and services"

    inherent_risk:
      likelihood: 3
      impact: 4
      score: 12  # High

    existing_controls:
      - "Vendor security assessments (annual)"
      - "SCA tooling in CI/CD (Snyk)"
      - "Vendor SOC 2 reports reviewed annually"
      - "Software bill of materials (SBOM) maintained"
      - "Critical vendor monitoring (SecurityScorecard)"

    residual_risk:
      likelihood: 2
      impact: 3
      score: 6  # Medium

    treatment:
      option: "Reduce + Transfer"
      actions:
        - "Expand vendor monitoring to continuous"
        - "Implement vendor incident notification SLAs in contracts"
        - "Maintain incident response playbook for vendor compromise"
        - "Cyber insurance covers supply chain incidents"
      residual_acceptable: true
      accepted_by: "Risk Committee"
      acceptance_date: "2026-03-15"
```

### 9.3 Key Risk Indicators (KRIs)

KRIs are forward-looking metrics that provide early warning of increasing risk:

| KRI Category | Metric | Threshold (Green) | Threshold (Amber) | Threshold (Red) |
|-------------|--------|-------------------|-------------------|-----------------|
| Access Control | Orphaned accounts | 0 | 1-5 | > 5 |
| Access Control | Failed login attempts/hour | < 100 | 100-500 | > 500 |
| Vulnerability | Critical unpatched > SLA | 0 | 1-3 | > 3 |
| Vulnerability | Mean days to patch critical | < 3 | 3-7 | > 7 |
| Incident | Security incidents/month | < 5 | 5-15 | > 15 |
| Incident | Mean time to respond | < 1h | 1-4h | > 4h |
| Compliance | Failed controls | 0 | 1-3 | > 3 |
| Compliance | Overdue evidence items | 0 | 1-5 | > 5 |
| Vendor | Vendors without current assessment | 0 | 1-2 | > 2 |
| Vendor | Vendor security score decline | None | 5-10 pts | > 10 pts |
| Data | DLP alerts/week | < 10 | 10-50 | > 50 |
| Data | Unclassified sensitive data | 0 | 1-5 files | > 5 files |

### 9.4 Third-Party Risk Management

**Vendor Assessment Tiers:**

| Tier | Data Access | Business Impact | Assessment Frequency | Depth |
|------|------------|-----------------|---------------------|-------|
| Critical | Customer data / PII | Business cannot operate without | Annual full + continuous monitoring | On-site, pen test, SOC 2 required |
| High | Internal data | Significant operational impact | Annual questionnaire + SOC 2 review | Detailed questionnaire, SOC 2 |
| Medium | Limited/no data | Moderate impact | Biennial questionnaire | Standard questionnaire |
| Low | No data access | Minimal impact | Risk-based | Lightweight review |

**Vendor Assessment Questionnaire (SIG-Lite aligned):**

```yaml
vendor_assessment:
  general:
    - "Does the vendor have ISO 27001 certification?"
    - "Does the vendor provide SOC 2 Type II reports?"
    - "When was the last independent security assessment?"
    - "Does the vendor have cyber insurance?"

  data_protection:
    - "Where is data stored geographically?"
    - "Is data encrypted at rest (AES-256 or equivalent)?"
    - "Is data encrypted in transit (TLS 1.2+)?"
    - "What is the data retention and deletion policy?"
    - "Can data be exported/deleted on request?"

  access_control:
    - "Is MFA enforced for all administrative access?"
    - "Are access reviews performed at least quarterly?"
    - "Is privileged access managed (PAM solution)?"
    - "How is our data logically separated from other tenants?"

  incident_response:
    - "What is the SLA for notifying customers of a breach?"
    - "Does the vendor have a documented incident response plan?"
    - "Has the plan been tested in the last 12 months?"
    - "Will the vendor provide forensic details upon request?"

  business_continuity:
    - "What is the RTO and RPO for the service?"
    - "Is DR testing performed at least annually?"
    - "Are backups performed and tested regularly?"
    - "What is the vendor's uptime SLA?"

  security_operations:
    - "Does the vendor perform vulnerability scanning (weekly+)?"
    - "Does the vendor perform penetration testing (annually+)?"
    - "Is a SIEM/SOC in operation?"
    - "Are security patches applied within defined SLAs?"
```

### 9.5 Risk Acceptance Process

Risk acceptance is a formal decision, not a default state:

```
Risk Acceptance Workflow:
========================

1. Risk Owner identifies risk that cannot be further reduced
   (cost exceeds benefit, technical impossibility, timeline constraint)

2. Risk Owner documents:
   - Risk description and current residual score
   - Why further treatment is not feasible/justified
   - Potential business impact if risk materializes
   - Duration of acceptance (time-bound, max 12 months)
   - Conditions that would trigger re-evaluation

3. Approval Authority (based on risk level):
   - Low risk: Risk Owner + Line Manager
   - Medium risk: CISO
   - High risk: Risk Committee
   - Critical risk: Board/Executive Committee (cannot be accepted indefinitely)

4. Documentation:
   - Formal risk acceptance form signed
   - Added to risk register with acceptance status
   - Calendar reminder for re-evaluation date
   - KRIs defined to monitor accepted risk

5. Monitoring:
   - KRIs tracked per normal schedule
   - Risk re-evaluated at defined intervals
   - Acceptance revoked if conditions change
```

---

## 10. Laboratorio Pratico

### 10.1 Exercise 1 — Implement a Compliance Program from Scratch

**Scenario:** You are the first security hire at a Series A SaaS company (50 employees, AWS-hosted, processing customer data for EU and US clients). Sales needs SOC 2 Type II within 12 months. GDPR compliance is legally required. ISO 27001 is a future goal (18 months).

**Steps:**

```
Week 1-2: Framework Selection and Scope
├── Choose SOC 2 TSC: Security (mandatory) + Availability + Confidentiality
├── Map GDPR technical requirements to SOC 2 criteria
├── Define system boundaries (AWS accounts, SaaS tools, data flows)
├── Select compliance platform (Vanta recommended for speed)
└── Deliverable: Scope document + data flow diagram

Week 3-4: Gap Assessment
├── Connect compliance platform to AWS, GitHub, Okta, etc.
├── Run initial automated assessment
├── Identify gaps (expect 40-60% compliance on first scan)
├── Categorize: Quick wins (< 1 week), Medium (1-4 weeks), Long (1-3 months)
└── Deliverable: Gap report + remediation plan

Week 5-12: Remediation
├── Quick wins first: Enable MFA, enable encryption defaults, 
│   configure log retention, deploy endpoint security
├── Medium: Write policies, configure access reviews,
│   implement change management, set up vulnerability scanning
├── Long: Implement incident response program, vendor management,
│   security awareness training, BCP/DR
└── Deliverable: All critical/high gaps closed

Week 13-16: Evidence Collection Stabilization
├── Verify automated evidence collection working
├── Establish manual evidence collection cadence
├── Run internal mock audit
├── Address mock audit findings
└── Deliverable: Clean mock audit

Week 17-24: Observation Period
├── SOC 2 Type II requires 6+ months of evidence
├── Maintain continuous compliance monitoring
├── Document any exceptions/incidents
├── Monthly compliance review meetings
└── Deliverable: 6 months of consistent evidence

Week 25-28: External Audit
├── Select auditor (CPA firm with SOC 2 experience)
├── Prepare audit package
├── Support auditor fieldwork
├── Address any findings
└── Deliverable: SOC 2 Type II report
```

### 10.2 Exercise 2 — Automate Evidence Collection with InSpec

**Objective:** Create an InSpec profile that validates controls across PCI-DSS, ISO 27001, and SOC 2, and generates evidence packages.

```ruby
# compliance_profile/inspec.yml
name: multi-framework-compliance
title: Multi-Framework Compliance Profile
version: 1.0.0
maintainer: Security Operations
copyright: 2026
license: Proprietary
summary: Validates controls for PCI-DSS 4.0, ISO 27001:2022, SOC 2
supports:
  - platform: aws
  - os-family: linux

depends:
  - name: linux-baseline
    url: https://github.com/dev-sec/linux-baseline
    version: "~> 4.0"
```

```ruby
# compliance_profile/controls/access_control.rb

# Covers: PCI-DSS 7/8, ISO A.5.15/A.8.2/A.8.5, SOC 2 CC6.1-CC6.3

control 'access-001' do
  title 'Password policy enforces complexity'
  desc 'Verify system password policy meets multi-framework requirements'
  impact 1.0
  tag pci_dss: ['8.3.6']
  tag iso27001: ['A.8.5']
  tag soc2: ['CC6.1']

  describe file('/etc/security/pwquality.conf') do
    it { should exist }
    its('content') { should match(/minlen\s*=\s*1[2-9]|[2-9]\d/) }
    its('content') { should match(/dcredit\s*=\s*-[1-9]/) }
    its('content') { should match(/ucredit\s*=\s*-[1-9]/) }
    its('content') { should match(/lcredit\s*=\s*-[1-9]/) }
    its('content') { should match(/ocredit\s*=\s*-[1-9]/) }
  end

  describe file('/etc/login.defs') do
    its('content') { should match(/PASS_MAX_DAYS\s+90/) }
    its('content') { should match(/PASS_MIN_DAYS\s+[1-9]/) }
    its('content') { should match(/PASS_MIN_LEN\s+1[2-9]|[2-9]\d/) }
  end
end

control 'access-002' do
  title 'No users without password expiry'
  desc 'All interactive user accounts have password expiration configured'
  impact 0.8
  tag pci_dss: ['8.3.9']
  tag iso27001: ['A.8.5']
  tag soc2: ['CC6.1']

  # Get all users with UID >= 1000 (interactive users)
  passwd_entries = command("awk -F: '$3 >= 1000 && $7 != \"/sbin/nologin\" && $7 != \"/bin/false\" {print $1}' /etc/passwd").stdout.strip.split("\n")

  passwd_entries.each do |user|
    describe shadow.where(user: user) do
      its('max_days.first') { should cmp <= 90 }
      its('min_days.first') { should cmp >= 1 }
    end
  end
end

control 'access-003' do
  title 'SSH key-based authentication enforced'
  desc 'Password authentication disabled for SSH; key-based only'
  impact 0.9
  tag pci_dss: ['8.3']
  tag iso27001: ['A.8.5']
  tag soc2: ['CC6.1']

  describe sshd_config do
    its('PasswordAuthentication') { should eq 'no' }
    its('PubkeyAuthentication') { should eq 'yes' }
    its('ChallengeResponseAuthentication') { should eq 'no' }
  end
end

control 'access-004' do
  title 'Privileged accounts are limited'
  desc 'Minimal users in sudo/wheel group'
  impact 0.9
  tag pci_dss: ['7.2.1']
  tag iso27001: ['A.8.2']
  tag soc2: ['CC6.3']

  describe group('sudo') do
    its('members.length') { should cmp <= 5 }
  end

  describe group('wheel') do
    its('members.length') { should cmp <= 5 }
  end

  # No UID 0 accounts besides root
  describe command("awk -F: '$3 == 0 && $1 != \"root\"' /etc/passwd") do
    its('stdout') { should be_empty }
  end
end
```

```ruby
# compliance_profile/controls/encryption.rb

# Covers: PCI-DSS 3/4, ISO A.8.24, SOC 2 CC6.1/CC6.7

control 'crypto-001' do
  title 'TLS 1.2+ enforced for all services'
  desc 'No SSL or TLS < 1.2 accepted by listening services'
  impact 1.0
  tag pci_dss: ['4.2.1']
  tag iso27001: ['A.8.24']
  tag soc2: ['CC6.7']

  # Check nginx configuration
  if file('/etc/nginx/nginx.conf').exist?
    describe file('/etc/nginx/nginx.conf') do
      its('content') { should match(/ssl_protocols\s+TLSv1\.2\s+TLSv1\.3/) }
      its('content') { should_not match(/SSLv[23]/) }
      its('content') { should_not match(/TLSv1\.0/) }
      its('content') { should_not match(/TLSv1\.1/) }
    end
  end

  # Check OpenSSL default minimum
  describe command('openssl ciphers -v "ALL:eNULL" | grep -i "SSLv[23]\\|TLSv1\\.0\\|TLSv1\\.1"') do
    its('stdout') { should be_empty }
  end
end

control 'crypto-002' do
  title 'Disk encryption enabled'
  desc 'All data partitions use LUKS or equivalent encryption'
  impact 0.9
  tag pci_dss: ['3.5.1']
  tag iso27001: ['A.8.24']
  tag soc2: ['CC6.1']

  # Check for LUKS encrypted volumes
  data_partitions = command("lsblk -o NAME,MOUNTPOINT,TYPE | grep 'part\\|lvm' | awk '{print $1}'").stdout.strip.split("\n")

  data_partitions.each do |partition|
    describe command("cryptsetup isLuks /dev/#{partition.strip.gsub(/[^a-zA-Z0-9\/]/, '')} 2>/dev/null; echo $?") do
      # Either LUKS encrypted or a logical volume on encrypted physical volume
      its('stdout.strip') { should be_in ['0', '4'] }  # 0=LUKS, 4=not block device (LVM)
    end
  end
end

control 'crypto-003' do
  title 'Strong cipher suites only'
  desc 'Weak ciphers disabled across all TLS-enabled services'
  impact 0.8
  tag pci_dss: ['4.2.1']
  tag iso27001: ['A.8.24']
  tag soc2: ['CC6.7']

  describe sshd_config do
    its('Ciphers') { should_not include 'arcfour' }
    its('Ciphers') { should_not include '3des' }
    its('Ciphers') { should_not include 'blowfish' }
    its('Ciphers') { should_not include 'cast128' }
  end

  # Verify no RC4, DES, or export ciphers in TLS
  if port(443).listening?
    describe command("echo | openssl s_client -connect localhost:443 -cipher 'RC4:DES:EXPORT' 2>&1") do
      its('stdout') { should match(/handshake failure|no ciphers/) }
    end
  end
end
```

### 10.3 Exercise 3 — Prepare Audit Package

**Objective:** Assemble a complete audit evidence package for SOC 2 Type II readiness.

```bash
#!/usr/bin/env bash
# prepare_audit_package.sh
# Assembles evidence package for SOC 2 Type II audit

set -euo pipefail

AUDIT_DIR="/evidence/audit-package/$(date +%Y-%m)"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

mkdir -p "${AUDIT_DIR}"/{policies,access-control,change-management,incident-response,monitoring,vendor-management,infrastructure,encryption}

echo "[${TIMESTAMP}] Starting audit package preparation..."

# ===== SECTION 1: POLICIES (CC1.3) =====
echo "[INFO] Collecting policy documents..."
cp /docs/policies/information-security-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/acceptable-use-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/access-control-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/change-management-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/incident-response-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/data-classification-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/vendor-management-policy.pdf "${AUDIT_DIR}/policies/"
cp /docs/policies/business-continuity-policy.pdf "${AUDIT_DIR}/policies/"

# ===== SECTION 2: ACCESS CONTROL (CC6.1-CC6.3) =====
echo "[INFO] Collecting access control evidence..."

# Current user listings from identity provider
curl -s -H "Authorization: SSWS ${OKTA_API_TOKEN}" \
  "https://${OKTA_DOMAIN}/api/v1/users?limit=200" \
  | jq '.' > "${AUDIT_DIR}/access-control/okta-users-current.json"

# Access review evidence (last 4 quarterly reviews)
for quarter in Q1 Q2 Q3 Q4; do
  cp "/evidence/access-reviews/2025-${quarter}-review.pdf" \
    "${AUDIT_DIR}/access-control/" 2>/dev/null || true
  cp "/evidence/access-reviews/2026-${quarter}-review.pdf" \
    "${AUDIT_DIR}/access-control/" 2>/dev/null || true
done

# Terminated user deprovisioning evidence
jira_query='project = "IT" AND type = "Offboarding" AND status = "Done" AND resolved >= -365d'
curl -s -H "Authorization: Bearer ${JIRA_TOKEN}" \
  -G --data-urlencode "jql=${jira_query}" \
  "https://${JIRA_DOMAIN}/rest/api/3/search" \
  | jq '.' > "${AUDIT_DIR}/access-control/offboarding-tickets.json"

# AWS IAM policy evidence
aws iam get-account-authorization-details \
  > "${AUDIT_DIR}/access-control/aws-iam-full-export.json"
aws iam generate-credential-report
sleep 5
aws iam get-credential-report --output text --query Content \
  | base64 --decode > "${AUDIT_DIR}/access-control/aws-credential-report.csv"

# ===== SECTION 3: CHANGE MANAGEMENT (CC8.1) =====
echo "[INFO] Collecting change management evidence..."

# GitHub PRs (sample of last 90 days)
gh api "repos/${GITHUB_ORG}/${GITHUB_REPO}/pulls?state=closed&per_page=100&sort=updated&direction=desc" \
  | jq '[.[] | select(.merged_at != null) | {number, title, merged_at, user: .user.login, reviewers: [.requested_reviewers[].login]}]' \
  > "${AUDIT_DIR}/change-management/merged-prs-sample.json"

# Deployment logs
kubectl get events -n production --sort-by='.lastTimestamp' \
  -o json > "${AUDIT_DIR}/change-management/k8s-deployment-events.json"

# ===== SECTION 4: MONITORING (CC7.1-CC7.3) =====
echo "[INFO] Collecting monitoring evidence..."

# Alert configuration export
curl -s -H "DD-API-KEY: ${DATADOG_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
  "https://api.datadoghq.com/api/v1/monitor" \
  | jq '.' > "${AUDIT_DIR}/monitoring/datadog-monitors-config.json"

# Incident tickets (last 12 months)
jira_query='project = "SEC" AND type = "Incident" AND created >= -365d'
curl -s -H "Authorization: Bearer ${JIRA_TOKEN}" \
  -G --data-urlencode "jql=${jira_query}" \
  "https://${JIRA_DOMAIN}/rest/api/3/search?maxResults=100" \
  | jq '.' > "${AUDIT_DIR}/incident-response/security-incidents.json"

# ===== SECTION 5: ENCRYPTION (CC6.1, CC6.7) =====
echo "[INFO] Collecting encryption evidence..."

# S3 encryption status
aws s3api list-buckets --query 'Buckets[].Name' --output text | tr '\t' '\n' | while read bucket; do
  aws s3api get-bucket-encryption --bucket "${bucket}" 2>/dev/null || echo "{\"bucket\": \"${bucket}\", \"encrypted\": false}"
done | jq -s '.' > "${AUDIT_DIR}/encryption/s3-encryption-status.json"

# RDS encryption
aws rds describe-db-instances \
  --query 'DBInstances[].{ID:DBInstanceIdentifier,Encrypted:StorageEncrypted,Engine:Engine}' \
  > "${AUDIT_DIR}/encryption/rds-encryption-status.json"

# TLS certificate inventory
aws acm list-certificates \
  --query 'CertificateSummaryList[].{Domain:DomainName,Status:Status,Expiry:NotAfter}' \
  > "${AUDIT_DIR}/encryption/tls-certificates.json"

# ===== SECTION 6: VENDOR MANAGEMENT (CC9.2) =====
echo "[INFO] Collecting vendor management evidence..."
cp /evidence/vendor-assessments/*.pdf "${AUDIT_DIR}/vendor-management/" 2>/dev/null || true
cp /evidence/vendor-soc2-reports/*.pdf "${AUDIT_DIR}/vendor-management/" 2>/dev/null || true

# ===== GENERATE MANIFEST =====
echo "[INFO] Generating evidence manifest..."

find "${AUDIT_DIR}" -type f | while read -r file; do
  sha256=$(sha256sum "${file}" | cut -d' ' -f1)
  size=$(stat -c%s "${file}")
  echo "{\"file\": \"${file}\", \"sha256\": \"${sha256}\", \"size\": ${size}, \"collected\": \"${TIMESTAMP}\"}"
done | jq -s '.' > "${AUDIT_DIR}/MANIFEST.json"

echo "[${TIMESTAMP}] Audit package preparation complete."
echo "Location: ${AUDIT_DIR}"
echo "Files: $(find "${AUDIT_DIR}" -type f | wc -l)"
echo "Total size: $(du -sh "${AUDIT_DIR}" | cut -f1)"
```

### 10.4 Exercise 4 — Conduct Mock Audit

**Mock Audit Checklist Template:**

```yaml
# mock_audit_checklist.yaml
# Use this to simulate an auditor's examination

mock_audit:
  metadata:
    date: "2026-05-07"
    scope: "SOC 2 Type II - Security + Availability"
    period: "2025-11-01 to 2026-04-30"
    auditor: "Internal compliance team"

  cc1_control_environment:
    - check: "Board/management oversight documented"
      evidence_needed: "Board meeting minutes, security committee charter"
      status: null  # pass/fail/partial
      notes: ""
    - check: "Organizational structure defined"
      evidence_needed: "Org chart, RACI matrix, job descriptions"
      status: null
    - check: "Code of conduct/ethics policy exists and acknowledged"
      evidence_needed: "Policy document, signed acknowledgments"
      status: null
    - check: "Competency requirements defined for security roles"
      evidence_needed: "Job descriptions, training records, certifications"
      status: null

  cc6_logical_physical_access:
    - check: "User provisioning follows approval workflow"
      evidence_needed: "Sample of 25 access request tickets with approvals"
      status: null
    - check: "Terminated users deprovisioned within 24 hours"
      evidence_needed: "Offboarding tickets with timestamps, system logs"
      status: null
    - check: "Quarterly access reviews completed"
      evidence_needed: "4 quarterly reviews with evidence of action taken"
      status: null
    - check: "MFA enforced for all production access"
      evidence_needed: "IdP configuration showing MFA policy, enforcement logs"
      status: null
    - check: "Privileged access limited and monitored"
      evidence_needed: "PAM logs, admin account listing, justification"
      status: null
    - check: "Network segmentation between environments"
      evidence_needed: "Network diagram, firewall rules, pen test scope"
      status: null

  cc7_system_operations:
    - check: "Security monitoring active and alerts configured"
      evidence_needed: "SIEM/monitoring tool configuration, alert rules"
      status: null
    - check: "Alerts investigated within SLA"
      evidence_needed: "Sample of 25 alerts with response timestamps"
      status: null
    - check: "Vulnerability scanning performed regularly"
      evidence_needed: "Scan schedules, 4 quarterly scan reports"
      status: null
    - check: "Penetration testing performed annually"
      evidence_needed: "Pen test report, remediation evidence"
      status: null
    - check: "Incidents detected, responded to, and documented"
      evidence_needed: "Incident tickets, post-mortems, timeline"
      status: null

  cc8_change_management:
    - check: "All production changes follow approval process"
      evidence_needed: "Sample of 25 change tickets with approval evidence"
      status: null
    - check: "Changes tested before deployment"
      evidence_needed: "Test results, staging environment evidence"
      status: null
    - check: "Emergency changes documented retrospectively"
      evidence_needed: "Emergency change policy, sample emergency tickets"
      status: null
    - check: "Rollback procedures exist and tested"
      evidence_needed: "Rollback documentation, rollback evidence"
      status: null

  cc9_risk_mitigation:
    - check: "Risk assessment performed and current"
      evidence_needed: "Risk register, last assessment date"
      status: null
    - check: "Vendor risk assessments performed"
      evidence_needed: "Vendor assessment questionnaires, SOC 2 reviews"
      status: null
    - check: "Business continuity plan exists and tested"
      evidence_needed: "BCP document, DR test results"
      status: null

  a1_availability:
    - check: "Capacity monitoring and alerting active"
      evidence_needed: "Monitoring dashboards, capacity alerts"
      status: null
    - check: "Backup procedures documented and tested"
      evidence_needed: "Backup policy, restoration test results"
      status: null
    - check: "SLA/uptime commitments defined and met"
      evidence_needed: "SLA documentation, uptime reports"
      status: null
    - check: "Disaster recovery tested within last 12 months"
      evidence_needed: "DR test plan, execution report, lessons learned"
      status: null

  sampling_guidance:
    population_size_25_to_50: "Sample all"
    population_size_50_to_250: "Sample 25-40 items"
    population_size_250_plus: "Sample 40-60 items"
    rule: "One exception in sample = expand sample size or investigate control failure"
```

### 10.5 Exercise 5 — Maintain Continuous Compliance

**Compliance Maintenance Runbook:**

```yaml
# continuous_compliance_runbook.yaml

daily_tasks:
  automated:
    - task: "Run InSpec compliance scan"
      tool: "InSpec + cron"
      time: "02:00 UTC"
      alert_on: "Any critical/high control failure"
    - task: "Check compliance platform status"
      tool: "Vanta/Drata API health check"
      time: "08:00 UTC"
      alert_on: "Any test going from pass to fail"
    - task: "Monitor CSPM findings"
      tool: "Wiz/Prisma Cloud"
      time: "Real-time"
      alert_on: "New critical/high findings"

  manual:
    - task: "Review overnight security alerts"
      owner: "Security on-call"
      time: "09:00 local"
    - task: "Check for new vendor security advisories"
      owner: "Security operations"
      time: "10:00 local"

weekly_tasks:
  - task: "Review compliance dashboard"
    owner: "Compliance manager"
    day: "Monday"
  - task: "Update remediation tracker"
    owner: "Control owners"
    day: "Wednesday"
  - task: "Verify backup restoration (sample)"
    owner: "Platform engineering"
    day: "Thursday"
  - task: "Review access request queue"
    owner: "IT operations"
    day: "Friday"

monthly_tasks:
  - task: "Compliance metrics report to management"
    owner: "Compliance manager"
    deliverable: "Monthly compliance scorecard"
  - task: "Vendor security monitoring review"
    owner: "Third-party risk"
    deliverable: "Vendor risk update"
  - task: "Security awareness metric review"
    owner: "Security awareness lead"
    deliverable: "Training completion rates, phishing sim results"
  - task: "Patch compliance report"
    owner: "Platform engineering"
    deliverable: "Patch status across fleet"

quarterly_tasks:
  - task: "Access review execution"
    owner: "All system owners"
    deliverable: "Signed access review evidence"
  - task: "Vulnerability scan + ASV scan (if PCI)"
    owner: "Security operations"
    deliverable: "Scan reports, remediation evidence"
  - task: "Policy review and update"
    owner: "Policy owners"
    deliverable: "Updated policies if needed, review sign-off"
  - task: "Risk register review"
    owner: "Risk committee"
    deliverable: "Updated risk register, new/closed risks"
  - task: "Internal audit (per schedule)"
    owner: "Internal audit team"
    deliverable: "Audit report, findings"
  - task: "BC/DR tabletop exercise"
    owner: "BC/DR coordinator"
    deliverable: "Exercise report, lessons learned"

annual_tasks:
  - task: "Full risk assessment"
    owner: "CISO + Risk committee"
    deliverable: "Complete risk assessment report"
  - task: "Penetration testing"
    owner: "Security operations (external firm)"
    deliverable: "Pen test report, remediation plan"
  - task: "Management review (ISO 27001)"
    owner: "CISO, presented to executive team"
    deliverable: "Management review minutes"
  - task: "Security awareness training refresh"
    owner: "HR + Security"
    deliverable: "Training completion records"
  - task: "External audit (SOC 2/ISO 27001)"
    owner: "Compliance manager"
    deliverable: "Audit report"
  - task: "Insurance renewal assessment"
    owner: "Finance + CISO"
    deliverable: "Updated policy"
  - task: "BCP/DR full test"
    owner: "BC/DR coordinator"
    deliverable: "Full test report with RTO/RPO validation"
```

### 10.6 Exercise 6 — Prometheus Metrics for Compliance Monitoring

```yaml
# prometheus/compliance_rules.yml
# Prometheus alerting rules for compliance control monitoring

groups:
  - name: compliance_controls
    rules:
      # Alert when any critical compliance control fails
      - alert: CriticalComplianceControlFailure
        expr: compliance_control_status{severity="critical"} == 0
        for: 5m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Critical compliance control failing: {{ $labels.control_id }}"
          description: |
            Control {{ $labels.control_id }} ({{ $labels.framework }}) has been 
            failing for 5+ minutes. Framework: {{ $labels.framework }}, 
            Requirement: {{ $labels.requirement }}
          runbook: "https://wiki.internal/runbooks/compliance-control-failure"

      # Alert when compliance score drops below threshold
      - alert: ComplianceScoreBelowThreshold
        expr: |
          (sum(compliance_control_status{status="passing"}) / 
           sum(compliance_control_status)) * 100 < 95
        for: 15m
        labels:
          severity: warning
          team: compliance
        annotations:
          summary: "Overall compliance score below 95%"
          description: "Current compliance score: {{ $value }}%"

      # Alert on stale evidence (not collected within expected window)
      - alert: StaleComplianceEvidence
        expr: |
          (time() - evidence_last_collection_timestamp_seconds) > 86400 * 7
        for: 1h
        labels:
          severity: warning
          team: compliance
        annotations:
          summary: "Evidence collection stale for {{ $labels.evidence_type }}"
          description: |
            Evidence {{ $labels.evidence_type }} has not been collected 
            in over 7 days. Last collection: {{ $value | humanizeTimestamp }}

      # Alert on access review overdue
      - alert: AccessReviewOverdue
        expr: |
          (time() - access_review_last_completed_timestamp_seconds) > 86400 * 95
        for: 1h
        labels:
          severity: high
          team: it-operations
        annotations:
          summary: "Quarterly access review overdue for {{ $labels.system }}"
          description: "Last review was {{ $value | humanizeDuration }} ago"

      # Alert on unpatched critical vulnerabilities past SLA
      - alert: CriticalVulnerabilityPastSLA
        expr: |
          vulnerability_days_open{severity="critical"} > 3
        for: 0m
        labels:
          severity: critical
          team: platform-engineering
        annotations:
          summary: "Critical vulnerability past 72h SLA: {{ $labels.cve_id }}"
          description: |
            CVE {{ $labels.cve_id }} on {{ $labels.host }} has been open 
            for {{ $value }} days (SLA: 3 days)

      # Track compliance control pass rate by framework
      - record: compliance:control_pass_rate:by_framework
        expr: |
          sum by (framework) (compliance_control_status{status="passing"}) /
          sum by (framework) (compliance_control_status) * 100

      # Track mean time to remediate by severity
      - record: compliance:mttr_hours:by_severity
        expr: |
          avg by (severity) (vulnerability_remediation_hours)
```

### 10.7 Quick Reference — Audit Readiness Checklist

Before any audit engagement, verify:

```
PRE-AUDIT CHECKLIST
===================

[ ] Scope documentation current and approved
[ ] All policies reviewed within last 12 months
[ ] Risk register current (reviewed within 90 days)
[ ] Access reviews completed for all quarters in period
[ ] Vulnerability scans current (no overdue scans)
[ ] Penetration test completed and findings remediated
[ ] Incident response plan tested (tabletop/exercise)
[ ] Security awareness training completion > 95%
[ ] Vendor assessments current for critical vendors
[ ] Change management tickets properly approved (sample check)
[ ] Backup restoration tested within last quarter
[ ] BC/DR plan tested within last 12 months
[ ] Compliance platform showing > 95% pass rate
[ ] No outstanding critical/high findings from previous audit
[ ] Evidence vault organized and indexed to controls
[ ] Audit coordinator identified and available
[ ] Management briefed on audit scope and timeline
[ ] Known exceptions documented with compensating controls
```

---

## Riferimenti Normativi e Risorse

| Resource | URL/Reference |
|----------|--------------|
| PCI-DSS 4.0 Standard | PCI SSC Document Library |
| ISO/IEC 27001:2022 | ISO Standards Catalog |
| ISO/IEC 27005:2022 | Information Security Risk Management |
| AICPA SOC 2 Guide | AICPA.org/SOC |
| NIST CSF 2.0 | NIST.gov/cyberframework |
| CIS Controls v8 | CISecurity.org/controls |
| NIS2 Directive | EUR-Lex 2022/2555 |
| GDPR | EUR-Lex 2016/679 |
| HIPAA Security Rule | 45 CFR Part 164 |
| Chef InSpec Documentation | docs.chef.io/inspec |
| AWS Config Managed Rules | AWS Documentation |
| Open Policy Agent | openpolicyagent.org |
| FAIR Risk Model | fairinstitute.org |

---

## Riepilogo Operativo

This module provides the complete knowledge framework for implementing, maintaining, and demonstrating compliance across multiple regulatory frameworks simultaneously. The key operational takeaways:

1. **Map once, implement once, evidence once.** Never build parallel control implementations for different frameworks when a single control satisfies multiple requirements.

2. **Automate relentlessly.** Manual evidence collection does not scale. Invest in compliance platforms and custom scripts early; they pay for themselves within one audit cycle.

3. **Treat compliance as a continuous process.** Point-in-time assessments create a false sense of security. Continuous monitoring with real-time alerting catches drift before auditors do.

4. **Evidence quality matters more than quantity.** A small, well-organized evidence package with clear traceability to control objectives beats a massive, disorganized document dump.

5. **Risk management drives everything.** The risk register is the foundation of your compliance program. Controls exist to treat risks. Evidence demonstrates controls work. Audits verify the whole chain.

6. **Build relationships with auditors.** Transparent, well-prepared organizations get smoother audits, fewer findings, and more benefit from the process.

7. **For the ethical hacker:** your penetration tests, vulnerability scans, and security assessments directly feed compliance evidence. Understand which framework requirements your work satisfies, structure your reporting accordingly, and make the compliance team's job easier by mapping findings to control references.
