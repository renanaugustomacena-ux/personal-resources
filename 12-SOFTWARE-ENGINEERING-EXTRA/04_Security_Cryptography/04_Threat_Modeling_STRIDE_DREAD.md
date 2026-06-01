# Module 4.4: Threat Modeling — STRIDE, DREAD, Attack Trees

> **Module 04.4** · **Last updated:** 2026-04-27

## Guiding ideas
1. **STRIDE: Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation.**
2. **DREAD: Damage, Reproducibility, Exploitability, Affected users, Discoverability.**
3. **Attack tree: hierarchical attack scenarios.**
4. **Threat model session: multi-discipline (PM, dev, security).**


**Date:** 2026-04-22
**Status:** Completed

## 1. The Threat Modeling Workflow

Shostack's four-question frame:
1.  **What are we building?** (Decompose)
2.  **What can go wrong?** (Identify threats)
3.  **What are we going to do about it?** (Mitigate)
4.  **Did we do a good job?** (Validate)

Output is a *living artifact*, refreshed every architecture change. Cheaper than penetration testing because it shifts left.

## 2. Decomposition: Data Flow Diagrams

### 2.1 DFD Levels
*   **Level 0 — Context diagram:** System as a single process; external entities and trust boundaries.
*   **Level 1:** Major subsystems (auth, API, DB, queue).
*   **Level 2:** Per-subsystem internals (e.g., login flow inside auth).

### 2.2 DFD Elements
| Symbol | Element | STRIDE classes that apply |
| :--- | :--- | :--- |
| Square | External entity | S, R |
| Circle | Process | S, T, R, I, D, E |
| Double line | Data store | T, R, I, D |
| Arrow | Data flow | T, I, D |

**Trust boundaries** (dashed lines): privilege/identity transitions (browser ↔ server, app ↔ DB, container ↔ host). Almost every interesting threat sits on one.

## 3. STRIDE per Element

Microsoft taxonomy. Each letter maps to a violated security property.

| Letter | Threat | Violates | Examples |
| :--- | :--- | :--- | :--- |
| **S** | Spoofing | Authentication | Stolen token, forged JWT, ARP spoofing |
| **T** | Tampering | Integrity | Param tampering, MITM rewrite, IDOR write |
| **R** | Repudiation | Non-repudiation | Missing audit log, unsigned actions |
| **I** | Information disclosure | Confidentiality | SQLi data exfil, verbose errors, S3 bucket public |
| **D** | Denial of service | Availability | Slowloris, ReDoS, billion laughs, fork bomb |
| **E** | Elevation of privilege | Authorization | Sandbox escape, privilege confusion, sudo bug |

### 3.1 STRIDE-per-Element Heuristic
*   External entity → S, R
*   Process → all six
*   Data flow → T, I, D
*   Data store → T, R (audit), I, D

Mechanically walk every element × applicable letters; rejecting "not applicable" is also documentation.

## 4. DREAD Scoring

For prioritization once threats are listed. Each axis 1–10.

*   **D — Damage:** worst-case impact (data loss, RCE, downtime).
*   **R — Reproducibility:** how reliably it works (10 = always).
*   **E — Exploitability:** skill/tooling required (10 = script kiddie).
*   **A — Affected users:** % of user base or systems.
*   **D — Discoverability:** how easily an attacker finds it.

$$\text{Risk} = \frac{D + R + E + A + D}{5}$$

Critique: subjective; Microsoft itself moved away from DREAD in favor of CVSS. Still useful inside a single team for relative ranking. For external reports use **CVSS v3.1/v4.0** + **CWE**.

## 5. Attack Trees

Schneier's structured "what could go wrong".

*   **Root:** attacker's goal (e.g., "Read CEO email").
*   **Internal nodes:** subgoals.
*   **Leaves:** concrete attack steps.
*   **AND nodes:** all children required.
*   **OR nodes:** any child suffices.
*   Annotate leaves with cost, time, skill, detection probability → propagate up (min for OR, sum for AND).

Example:

```
Goal: Steal customer DB
├── OR
│   ├── Compromise DBA laptop          [cost: 5k, skill: med]
│   ├── SQL injection on /search       [cost: 0, skill: low]
│   └── AND
│       ├── Phish ops engineer
│       └── Bypass MFA via SIM swap
```

## 6. PASTA (Process for Attack Simulation and Threat Analysis)

Risk-centric, 7 stages:
1.  Define business objectives.
2.  Define technical scope.
3.  Application decomposition (DFD).
4.  Threat analysis (intel feeds, ATT&CK).
5.  Vulnerability & weakness analysis (CWE/CVE).
6.  Attack modeling (attack trees).
7.  Risk and impact analysis (residual risk, mitigations).

Heavier than STRIDE; suited to high-stakes systems (fintech, health, ICS).

## 7. LINDDUN (Privacy)

GDPR-aligned counterpart to STRIDE for **privacy threats**:

*   **L** — Linkability
*   **I** — Identifiability
*   **N** — Non-repudiation (here a *threat*, not a property)
*   **D** — Detectability
*   **D** — Disclosure of information
*   **U** — Unawareness
*   **N** — Non-compliance

Use alongside STRIDE when handling PII or regulated data (Article 35 DPIA evidence).

## 8. Tooling

*   **Microsoft Threat Modeling Tool** — Visio-style DFD, auto-STRIDE per element.
*   **OWASP Threat Dragon** — open-source, JSON-backed, runs in browser/Electron.
*   **IriusRisk**, **ThreatModeler** — commercial, integrate with Jira/CI.
*   **pytm** — threats-as-code in Python; diffable in git.

## 9. MITRE ATT&CK Mapping

After identifying threats, map mitigations to tactics/techniques (e.g., `T1110 Brute Force`, `T1059 Command and Scripting Interpreter`). Provides shared vocabulary with SOC/IR and aligns detections (Sigma rules, EDR queries) with the threat model.

## 10. Worked Example: Web Login Flow

Elements: Browser (entity), `POST /login` (flow), AuthService (process), UserDB (store).

Selected threats:

| ID | Element | STRIDE | Threat | Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| T1 | Flow | S | Credential stuffing with leaked passwords | Rate limit + Have-I-Been-Pwned k-anonymity check + MFA |
| T2 | Flow | T | Session token tampering | Signed JWT (Ed25519) + short TTL + refresh rotation |
| T3 | Process | I | Username enumeration via timing | Constant-time compare; uniform error message |
| T4 | Process | D | Login storm exhausting bcrypt CPU | WAF rate limit; queue + circuit breaker; cost-tuned Argon2id |
| T5 | Store | I | Plaintext password leak via backup | Argon2id hash; encrypted backups; KMS-managed keys |
| T6 | Process | E | Privilege escalation via role in JWT claim | Server-side role lookup; never trust client claims |
| T7 | Flow | R | User denies action ("I didn't log in") | Append-only audit log; signed events; IP+UA capture |

Each row gets a CVSS score, owner, and a tracked ticket. Re-review on every auth change.
