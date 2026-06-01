# Capstone Project — Cybersecurity Masterclass

> **Last updated:** 2026-05-29

A multi-phase security assessment engagement integrating knowledge from across the library's 31 domains. This project simulates a realistic enterprise engagement for a mid-size conglomerate with on-premises Active Directory, multi-cloud infrastructure (AWS + Azure), public-facing web applications, and OT/IoT segments.

---

## Engagement Overview

**Scenario:** You have been retained to conduct a comprehensive security assessment of **Nexus Industries**, a fictional conglomerate operating manufacturing facilities (with ICS/SCADA), corporate offices, SaaS products, and a fintech payment processing subsidiary. The engagement covers the full lifecycle: reconnaissance through report delivery.

**Rules of Engagement:**
- Authorized scope covers all Nexus-owned IP ranges, domains, cloud tenants, and internal networks
- Social engineering (phishing) is authorized against corporate email with prior HR notification
- Physical access testing is out of scope
- Critical production ICS systems are observe-only (no active exploitation)
- All findings timestamped in UTC ISO 8601

**Duration:** 4 weeks active engagement + 1 week reporting

---

## Phase 1 — Reconnaissance & OSINT (Week 1, Days 1-3)

**Domains exercised:** 23 (Social Engineering & OSINT), 9 (Network Security), 25 (Threat Intelligence)

### Objectives

1. Map the external attack surface of Nexus Industries
2. Identify employees, email patterns, credential leaks
3. Profile the technology stack from public indicators
4. Enumerate threat actors historically targeting the sector

### Tasks

- [ ] Passive DNS enumeration: subdomain discovery via Certificate Transparency logs, DNS brute-forcing, passive DNS databases
- [ ] OSINT on key personnel: LinkedIn, GitHub, conference talks, document metadata (FOCA-style analysis)
- [ ] Credential breach search: check corporate email domains against known breach datasets
- [ ] Technology fingerprinting: Wappalyzer-style analysis of public web properties, Shodan/Censys for exposed services
- [ ] Cloud tenant discovery: enumerate Azure AD tenant, AWS S3 bucket naming patterns, GCP project IDs
- [ ] Threat intelligence review: query ATT&CK for techniques used against manufacturing and fintech sectors; map to detection coverage

### Deliverable

External attack surface report with prioritized entry points and a threat model specific to Nexus Industries' sector exposure.

**Reference chapters:**
- [Social Engineering & OSINT](domain23_social_engineering_osint.md)
- [Advanced OSINT Tradecraft](domain23_chapter23B_osint_tradecraft_se_defense.md)
- [Threat Intelligence Foundations](domain25_threat_intelligence.md)
- [TCP/IP, DNS, TLS Security](domain9_chapter9A_tcp_dns_tls.md)

---

## Phase 2 — Network Penetration Testing (Week 1, Days 3-5)

**Domains exercised:** 9 (Network), 6 (Mitigation Bypass), 2 (OS Internals)

### Objectives

1. Identify externally exploitable services
2. Pivot from DMZ to internal network segments
3. Map internal network topology and trust boundaries

### Tasks

- [ ] External port scanning and service enumeration (full TCP + top 1000 UDP)
- [ ] TLS configuration audit: protocol versions, cipher suites, certificate validation
- [ ] VPN/remote access endpoint testing
- [ ] Wireless network assessment: WPA2/3 handshake capture, evil twin, PMKID attacks
- [ ] Layer 2 attacks (if internal access obtained): ARP spoofing, VLAN hopping, LLMNR/NBT-NS poisoning
- [ ] Internal pivot: establish foothold, enumerate reachable subnets, identify segmentation gaps
- [ ] Identify ICS/OT network boundaries and any IT/OT convergence points (observe-only on ICS)

### Deliverable

Network penetration test findings with topology diagrams, exploited vulnerabilities (CVSS scored), and segmentation analysis.

**Reference chapters:**
- [TCP/IP, DNS, TLS](domain9_chapter9A_tcp_dns_tls.md)
- [L2, Wireless, Telecom, SDN](domain9_chapter9B_l2_wireless_telecom_sdn.md)
- [Mitigation Bypass Techniques](domain6_mitigation_bypass.md)
- [Process Address Space](domain2_chapter2A_process_memory.md)

---

## Phase 3 — Web Application Testing (Week 2, Days 1-3)

**Domains exercised:** 8 (Web Security), 13 (Cryptography)

### Objectives

1. Assess all public-facing web applications and APIs
2. Identify authentication, authorization, and session management flaws
3. Test the fintech payment processing API for business logic vulnerabilities

### Tasks

- [ ] Spider/crawl all in-scope web applications; map endpoints and parameters
- [ ] Authentication testing: brute force, credential stuffing, MFA bypass, session fixation
- [ ] Injection testing: SQLi, XSS (reflected/stored/DOM), SSRF, XXE, template injection
- [ ] API security: BOLA/IDOR, mass assignment, rate limiting, JWT validation
- [ ] Business logic: payment API flow manipulation, race conditions, price tampering
- [ ] Client-side: CSP review, CORS misconfiguration, postMessage abuse
- [ ] Cryptographic review: token entropy, key management, padding oracle tests
- [ ] Deserialization testing on any Java/.NET backends

### Deliverable

Web application security assessment with vulnerability details, proof-of-concept exploits, and remediation recommendations mapped to OWASP Top 10.

**Reference chapters:**
- [Client-Side Attacks & Auth](domain8_chapter8A_clientside_auth.md)
- [Server-Side & API Security](domain8_chapter8B_serverside_api.md)
- [Browser Internals](domain8_chapter8C_browser_internals.md)
- [Protocol Attacks](domain13_chapter13B_protocol_attacks.md)

---

## Phase 4 — Active Directory Exploitation (Week 2, Days 3-5)

**Domains exercised:** 14 (AD & Windows), 30 (C2 & Credential Theft)

### Objectives

1. Enumerate the AD forest and trust relationships
2. Escalate privileges from domain user to Domain Admin
3. Demonstrate lateral movement and persistence techniques

### Tasks

- [ ] AD enumeration: BloodHound collection, ACL analysis, GPO review, trust mapping
- [ ] Kerberos attacks: AS-REP roasting, Kerberoasting, delegation abuse (constrained/RBCD)
- [ ] Credential harvesting: LSASS dumping (avoiding EDR detection), NTDS.DIT extraction, DCSync
- [ ] Lateral movement: Pass-the-Hash, Pass-the-Ticket, DCOM/WMI/WinRM
- [ ] Persistence: Golden/Silver/Diamond Ticket, AdminSDHolder abuse, machine account manipulation
- [ ] Exchange/Microsoft 365: mailbox access, OAuth token abuse, cross-tenant pivot attempts
- [ ] C2 deployment: demonstrate malleable C2 profile, evaluate detection coverage

### Deliverable

AD attack path documentation with BloodHound graphs, exploited privilege escalation chains, and remediation priorities.

**Reference chapters:**
- [Active Directory Attacks](domain14_chapter14A_active_directory.md)
- [Windows Internals & Exchange](domain14_chapter14B_windows_exchange.md)
- [C2 Framework Internals](domain30_chapter30A_c2_framework_internals.md)
- [Credential Theft & Identity Attacks](domain30_chapter30B_credential_theft_identity_attacks.md)

---

## Phase 5 — Cloud Security Review (Week 3, Days 1-3)

**Domains exercised:** 10 (Cloud), 19 (Supply Chain)

### Objectives

1. Audit IAM policies and privilege escalation paths in AWS and Azure
2. Assess container and Kubernetes security posture
3. Review CI/CD pipeline for supply chain risks

### Tasks

- [ ] IAM review: over-permissioned roles, cross-account access, instance profile abuse
- [ ] Metadata service exploitation: IMDSv1 detection, SSRF-to-credential chains
- [ ] S3/Blob storage audit: public buckets, misconfigured ACLs, object versioning for data recovery
- [ ] Kubernetes assessment: RBAC misconfigurations, pod escape, secrets management, network policies
- [ ] Serverless review: Lambda/Azure Functions execution role over-privilege, event injection
- [ ] CI/CD pipeline review: GitHub Actions secrets exposure, supply chain dependency audit, SLSA compliance
- [ ] Container image scanning: base image vulnerabilities, embedded credentials, Dockerfile hardening

### Deliverable

Cloud security posture report covering IAM, infrastructure, container, and pipeline risks with CIS Benchmark gap analysis.

**Reference chapters:**
- [Cloud Provider Security](domain10_chapter10A_cloud_providers.md)
- [Container, K8s, Serverless](domain10_chapter10B_container_k8s_serverless.md)
- [Supply Chain Foundations](domain19_supply_chain.md)
- [Supply Chain Defense](domain19_chapter19B_supply_chain_defense.md)

---

## Phase 6 — Malware Analysis & Threat Simulation (Week 3, Days 3-5)

**Domains exercised:** 11 (Malware), 12 (Reverse Engineering), 29 (Ransomware), 18 (Adversarial ML)

### Objectives

1. Analyze a simulated malware sample dropped during the engagement
2. Evaluate EDR detection coverage against common evasion techniques
3. Simulate a ransomware tabletop scenario

### Tasks

- [ ] Static analysis: PE/ELF header inspection, string extraction, import analysis, packer detection
- [ ] Dynamic analysis: sandbox execution, API call tracing, network C2 decoding
- [ ] EDR evasion assessment: test direct syscalls, unhooking, ETW patching, AMSI bypass against deployed EDR
- [ ] Ransomware simulation: deploy benign encryption test against isolated test share; validate backup restoration
- [ ] If ML-based detection is deployed: test adversarial evasion against the ML model (feature-space perturbation)
- [ ] IOC extraction: document file hashes, C2 domains, mutex names, registry keys

### Deliverable

Malware analysis report with IOCs, MITRE ATT&CK technique mapping, EDR gap analysis, and ransomware readiness assessment.

**Reference chapters:**
- [Malware Architecture & C2](domain11_chapter11A_malware_c2.md)
- [EDR Evasion](domain11_chapter11B_edr_evasion_platform.md)
- [Static & Dynamic Analysis](domain12_chapter12A_static_dynamic_analysis.md)
- [Ransomware Operations](domain29_chapter29A_ransomware_operations.md)
- [Adversarial ML](domain18_adversarial_ml.md)

---

## Phase 7 — Incident Response Exercise (Week 4, Days 1-3)

**Domains exercised:** 24 (DFIR), 31 (SIEM/SOAR), 25 (Threat Intelligence)

### Objectives

1. Validate the client's incident response procedures against a simulated breach
2. Test SIEM detection coverage for the attack techniques used in prior phases
3. Assess forensic readiness

### Tasks

- [ ] Purple team exercise: replay attack techniques from Phases 2-6 with blue team observing
- [ ] SIEM detection audit: verify which techniques generated alerts, identify gaps, write Sigma rules for misses
- [ ] Log pipeline review: validate log sources, retention, normalization (ECS/OCSF), and query performance
- [ ] SOAR playbook test: trigger automated playbooks, measure MTTR (Mean Time to Respond)
- [ ] Forensic readiness: verify disk image acquisition procedures, memory dump capability, chain of custody forms
- [ ] Cloud forensics: test CloudTrail/Azure Activity Log preservation, container forensic snapshot procedures
- [ ] Threat intel integration: validate STIX/TAXII feed ingestion, IOC matching against collected telemetry

### Deliverable

Incident response maturity assessment, detection coverage heatmap (mapped to ATT&CK), and prioritized SIEM/SOAR improvement roadmap.

**Reference chapters:**
- [DFIR Foundations](domain24_dfir.md)
- [Cloud Forensics & IR](domain24_chapter24B_cloud_forensics_ir.md)
- [SIEM/SOAR Pipeline Design](domain31_chapter31A_siem_soar_detection_engineering.md)
- [Runtime Security & Zero Trust](domain31_chapter31B_runtime_security_zero_trust.md)
- [Operationalizing TI](domain25_chapter25B_operationalizing_ti.md)

---

## Phase 8 — Report Writing & Debrief (Week 4, Days 3-5)

**Domains exercised:** All

### Report Structure

```
1. Executive Summary (1-2 pages)
   - Business risk impact in non-technical language
   - Top 5 critical findings
   - Strategic recommendations

2. Methodology
   - Scope, tools, techniques, rules of engagement
   - ATT&CK technique coverage matrix

3. Findings (per phase)
   - Each finding: Title, CVSS score, CWE ID, description,
     evidence (screenshots, logs), exploitation steps,
     business impact, remediation (specific + strategic)
   - Findings sorted by severity within each phase

4. Attack Narrative
   - End-to-end kill chain from initial access to objectives
   - BloodHound graphs, network diagrams, timeline

5. Detection Coverage Analysis
   - ATT&CK heatmap: detected vs. undetected techniques
   - Sigma rules for detection gaps
   - SIEM/SOAR maturity score

6. Remediation Roadmap
   - Prioritized by risk (CVSS) and implementation effort
   - Quick wins (< 1 week), short-term (1-3 months), strategic (3-12 months)

7. Appendices
   - Full IOC list
   - Raw scan data
   - Tool configuration and versions
   - Evidence chain of custody log
```

### Quality Criteria

- [ ] Every finding has a reproducible proof-of-concept
- [ ] All timestamps in UTC ISO 8601
- [ ] Artifacts hashed (SHA-256) with hashes documented
- [ ] Credentials, PII, and internal hostnames redacted in any externally shared version
- [ ] Report reviewed by a second assessor before delivery

---

## Grading Rubric

| Criterion | Weight | Passing Threshold |
|-----------|--------|-------------------|
| Attack surface coverage (phases completed) | 25% | All 7 assessment phases |
| Finding quality (CVSS + CWE + PoC + remediation) | 25% | Every finding fully documented |
| Detection coverage analysis (ATT&CK mapping) | 20% | Heatmap with gap analysis |
| Report professionalism (structure, evidence, redaction) | 15% | Follows report structure above |
| Operational security during engagement | 15% | No scope violations, proper evidence handling |

---

## Domains Integrated

This capstone draws on **20 of 31 domains** in the library:

| Phase | Primary Domains |
|-------|----------------|
| 1 — Recon & OSINT | 9, 23, 25 |
| 2 — Network Pentest | 2, 6, 9 |
| 3 — Web App Testing | 8, 13 |
| 4 — AD Exploitation | 14, 30 |
| 5 — Cloud Security | 10, 19 |
| 6 — Malware Analysis | 11, 12, 18, 29 |
| 7 — Incident Response | 24, 25, 31 |
| 8 — Report Writing | All |

Remaining domains (1, 3, 4, 5, 7, 15, 16, 17, 20, 21, 22, 26, 27, 28) provide supporting knowledge. The assessor is expected to draw on these as needed -- binary analysis for exploit understanding, cryptography for protocol review, ICS awareness for OT boundary assessment, and so on.
