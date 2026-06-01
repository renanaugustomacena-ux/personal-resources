---
corso: "Cybersecurity Masterclass"
fase: "Domain 27 — Secure Architecture and Defense Engineering"
modulo: "27.A"
titolo: "Secure Architecture and Defense Engineering"
versione: "NIST CSF 2.0 / MITRE ATT&CK v16 / NIST SP 800-207"
livello: "Advanced"
prerequisiti:
  - "Network architecture and TCP/IP fundamentals (Domain 9)"
  - "Cryptographic primitives and key management (Domain 13)"
  - "Operating system internals — process, memory, boot (Domain 2)"
  - "Active Directory and identity attack paths (Domain 14)"
  - "Threat intelligence frameworks and ATT&CK (Domain 25)"
obiettivi:
  - "Construct a complete STRIDE-based threat model for a multi-tier application, producing a risk-scored threat register mapped to MITRE ATT&CK techniques"
  - "Evaluate UEFI Secure Boot and measured boot chains, identifying single-points-of-failure such as dbx update lag and test-key supply-chain risks"
  - "Implement TPM 2.0 sealing/unsealing workflows using tpm2-tools, binding disk-encryption keys to specific PCR policies"
  - "Design detection-as-code pipelines that version-control Sigma rules, enforce CI/CD validation, and deploy to multi-SIEM environments"
  - "Analyze confidential-computing architectures (Intel TDX, AMD SEV-SNP, Arm CCA) and assess their TCB boundaries, attestation mechanisms, and known attack classes"
tag: [security, threat-modeling, secure-boot, tpm, confidential-computing, detection-engineering, siem, edr, deception, sigma, yara]
---

# Domain 27 — Secure Architecture and Defense Engineering

> **After completing this chapter, you will be able to:** (1) perform systematic threat modeling using STRIDE, attack trees, and PASTA against real-world system architectures; (2) trace the UEFI Secure Boot and measured boot chain from PK through dbx, identifying where BlackLotus-class bootkits subvert the trust model; (3) seal and unseal secrets with TPM 2.0 PCR policies and execute remote attestation with tpm2-tools; (4) write production-grade Sigma rules with value modifiers and aggregation conditions, convert them to Splunk SPL and Elastic KQL via pySigma, and deploy through a detection-as-code CI/CD pipeline; (5) compare the isolation granularity, TCB composition, and attestation mechanisms of Intel SGX/TDX, AMD SEV-SNP, and Arm CCA, and evaluate known attacks against each.

> **Scope.** Threat modeling (STRIDE, attack trees, PASTA, Trike). Security design principles (Saltzer-Schroeder). Secure boot (SRTM, DRTM with Intel TXT/AMD SKINIT, UEFI Secure Boot flow, measured boot into TPM PCRs). TPM 2.0 (PCR banks, hierarchy, sealing/unsealing, key attestation). Confidential computing (Intel SGX/TDX, AMD SEV/SEV-ES/SEV-SNP, Arm CCA/RME/RMM). Detection engineering lifecycle. SIEM (Splunk SPL, Elastic KQL/EQL, Microsoft Sentinel KQL/UEBA, Chronicle YARA-L). EDR telemetry and bypass detection. Deception (honey tokens/accounts/files/services, Canary tokens, cloud honey credentials). Network detection (Zeek logs, Suricata/Snort, ET rulesets, full-packet capture with Arkime).

---

## 1. Threat modeling

### 1.1 STRIDE

STRIDE (Microsoft) categorizes threats against system components by property violated:

**Spoofing** (authenticity): impersonating another user, process, or system. Example: forging the `From` header in an email, presenting a stolen credential, DNS spoofing. Mitigation: authentication (MFA, mutual TLS, DKIM).

**Tampering** (integrity): modifying data in transit or at rest without authorization. Example: modifying a database record, altering a configuration file, MitM modifying HTTP traffic. Mitigation: integrity controls (HMAC, digital signatures, file-integrity monitoring, WAF).

**Repudiation** (non-repudiation): denying having performed an action. Example: a user claims they never authorized a transaction. Mitigation: logging and audit trails (tamper-evident logs, digitally-signed audit records, blockchain-based timestamping).

**Information Disclosure** (confidentiality): exposing data to unauthorized parties. Example: an SSRF leaking cloud metadata credentials, a directory traversal exposing `/etc/passwd`, a side-channel leaking encryption keys. Mitigation: encryption (at rest and in transit), access control, data classification and DLP.

**Denial of Service** (availability): rendering a service unavailable. Example: SYN flood, resource exhaustion, algorithmic complexity attack (regex DoS). Mitigation: rate limiting, load balancing, CDN, resource quotas, input validation.

**Elevation of Privilege** (authorization): gaining higher privileges than authorized. Example: SQL injection to admin, kernel exploit to root, RBCD attack to domain admin. Mitigation: least privilege, sandboxing, input validation, hardened configurations.

STRIDE is applied to Data Flow Diagrams (DFDs): each element in the DFD (process, data store, data flow, external entity, trust boundary) is analyzed against the relevant STRIDE categories (processes are susceptible to all six; data flows to Tampering, Information Disclosure, and DoS; data stores to Tampering, Information Disclosure, Repudiation, and DoS; external entities to Spoofing and Repudiation).

#### 1.1.1 STRIDE worked example: e-commerce web application

Consider a typical e-commerce application with four DFD elements: the user's browser (external entity), a web frontend (process), an API backend (process), and a PostgreSQL database (data store), separated by two trust boundaries (internet-to-DMZ and DMZ-to-internal). Applying STRIDE systematically to each element produces a concrete threat register.

The browser (external entity) faces Spoofing: an attacker uses stolen session cookies or phished credentials to impersonate a legitimate customer. It also faces Repudiation: a customer disputes a purchase, claiming they never placed the order. The data flow from the browser to the web frontend crosses the internet trust boundary and faces Tampering (MitM proxy modifying request parameters such as price or quantity fields), Information Disclosure (eavesdropping on unencrypted traffic to capture payment card data), and Denial of Service (volumetric DDoS flooding the frontend).

The web frontend process is susceptible to all six STRIDE categories. Spoofing manifests as a forged `X-Forwarded-For` header tricking rate-limiting or geo-restriction logic. Tampering appears when an attacker modifies client-side JavaScript to bypass input validation and submit crafted payloads directly to the backend. Repudiation arises if the frontend fails to log sufficient detail about which user performed which action at what time. Information Disclosure occurs through verbose error messages revealing stack traces, internal IP addresses, or database schema. Denial of Service targets the frontend through slowloris-style connection exhaustion. Elevation of Privilege materializes through a server-side template injection (SSTI) in the rendering engine that achieves remote code execution.

The API backend faces the same six categories within the internal trust boundary. The critical Elevation of Privilege threat here is an Insecure Direct Object Reference (IDOR) vulnerability: the API accepts `/api/orders/{order_id}` and returns order details without verifying that the authenticated user owns the requested order (OWASP API1:2023). Tampering targets the API through mass assignment: the API deserializes the full JSON request body into an ORM object, allowing the attacker to set the `role` or `discount_percentage` fields that should be server-controlled. Information Disclosure appears when the API returns the full user object including hashed passwords and internal IDs in responses that should only contain display-name and email.

The database data store faces Tampering (SQL injection through the API bypassing parameterized queries), Information Disclosure (a database dump through a SQLi UNION-based extraction or an exposed backup file on an object store), Repudiation (no audit log on delete operations, allowing an insider to remove records without trace), and Denial of Service (a resource-exhaustion query consuming all available connections through an unindexed search endpoint).

Each identified threat receives a risk score (DREAD or CVSS-based), maps to a specific MITRE ATT&CK technique where applicable (the IDOR maps to T1078.004 Valid Accounts: Cloud Accounts if the API is cloud-hosted, or more precisely to the access-control weakness exploited during T1530 Data from Cloud Storage Object), and receives a treatment plan: accept, mitigate (with a specific control), transfer (via insurance or SLA), or avoid (by redesigning the component).

### 1.2 Attack trees

A hierarchical decomposition of an attacker's goal into sub-goals and attack steps. The root node is the attacker's objective (e.g., "steal customer database"). Child nodes represent alternative or required steps to achieve the parent goal. Each leaf node is a concrete attack action (e.g., "exploit SQLi in the login form," "phish an admin's credentials," "bribe an insider"). Nodes are connected by AND (all children must succeed) or OR (any child suffices).

Attack trees enable: cost/difficulty analysis (assigning cost, skill level, or probability to each leaf and computing the overall attack cost), prioritization (focusing defenses on the cheapest/easiest attack paths), and completeness checking (ensuring the model covers all known attack vectors).

#### 1.2.1 Construction methodology

Building an attack tree follows a top-down decomposition. Begin with the root node representing the adversary's strategic objective. Then iteratively decompose each node into child nodes representing the prerequisite conditions or alternative approaches. For each leaf node, assign quantitative attributes: estimated cost in USD, required skill level (low/medium/high/nation-state), probability of success given current defenses, and time to execute.

As an example, consider the root goal "Compromise administrator credentials for the production environment." This root has three OR children representing distinct attack paths.

Path 1: Credential phishing. The attacker sends a targeted phishing email containing a link to a cloned SSO page. The attack requires: reconnaissance to identify the admin target (cost: $200, skill: low, success probability: 0.9), crafting the phishing infrastructure (cost: $500, skill: medium, success probability: 0.95), the target clicking the link and entering credentials (probability: 0.15 for a security-aware admin), and bypassing MFA via real-time AiTM proxy (cost: $1000, skill: high, success probability: 0.6 against TOTP, 0.01 against FIDO2). These are AND-connected: all four must succeed. The compound probability is 0.9 * 0.95 * 0.15 * 0.6 = 0.077 (7.7% for TOTP-protected admin), total cost approximately $1700.

Path 2: Credential stuffing from breach data. The attacker obtains the admin's personal email/password combo from a public breach database, hoping the admin reused the password. This requires: obtaining the breach data (cost: $50, skill: low, success probability: 0.99), identifying the admin's personal email (cost: $100, skill: low, success probability: 0.7), and the admin having reused the password (probability: 0.12 based on industry reuse rates for technical staff). These are AND-connected: compound probability 0.99 * 0.7 * 0.12 = 0.083 (8.3%), total cost approximately $150.

Path 3: Insider threat. A disgruntled employee or bribed contractor with legitimate access exfiltrates credentials. This requires: identifying a susceptible insider (cost: $5000, skill: medium, success probability: 0.3), the insider actually carrying out the exfiltration (probability: 0.5 after agreement). Compound probability: 0.15, total cost approximately $5000 plus the bribe.

The cheapest attack path is Path 2 ($150, 8.3% success), which directs defensive investment toward credential-monitoring services (detecting the admin's credentials in breach databases) and mandatory unique-password policies enforced through enterprise password managers. The highest-probability path depends on the MFA type deployed: if FIDO2 is enforced for admins, Path 1 drops to near-zero probability, making Path 2 the dominant threat.

### 1.3 PASTA

**PASTA (Process for Attack Simulation and Threat Analysis)** is a seven-stage risk-centric methodology that integrates business context, technical decomposition, and threat intelligence into a unified threat model. Each stage produces specific outputs that feed the next.

**Stage 1: Define objectives.** Identify the business objectives the application supports, the regulatory requirements it must meet, and the risk appetite of the organization. Output: a business context document listing the application's criticality classification, the data types it processes (PII, PCI, PHI), the compliance frameworks it falls under (SOC 2, PCI DSS, HIPAA), and the maximum acceptable risk levels for confidentiality, integrity, and availability impacts.

**Stage 2: Define the technical scope.** Enumerate all technical components: application tiers (web frontend, API, database, message queue, cache), infrastructure (cloud provider, region, VPC topology, CDN), third-party dependencies (payment gateway, email provider, analytics SDK), and external integrations (partner APIs, SSO providers). Output: a component inventory and a network topology diagram showing all trust boundaries.

**Stage 3: Application decomposition.** Build Data Flow Diagrams at multiple levels of detail. Identify trust boundaries (internet, DMZ, internal network, inter-service, database boundary). Map data flows to specific protocols, ports, and authentication mechanisms. Identify where sensitive data enters, is processed, is stored, and leaves the system. Output: DFDs at context, container, and component levels (C4 model alignment), annotated with data classification labels and authentication mechanisms.

**Stage 4: Threat analysis.** Using the DFDs from Stage 3 and external intelligence sources (ATT&CK framework, vulnerability databases such as NVD/CVE, sector-specific threat intelligence from ISACs, and the organization's own incident history), identify threats to each component and data flow. This is where STRIDE is applied per-element, but PASTA enriches STRIDE with real-world threat intelligence rather than relying solely on theoretical categorization. Output: a threat enumeration document listing each threat, the DFD element it targets, the ATT&CK technique it maps to, and references to known vulnerabilities or historical incidents demonstrating the threat.

**Stage 5: Vulnerability analysis.** Assess the system's current exposure to the identified threats through vulnerability scanning (DAST, SAST, SCA), penetration testing results, configuration audits, and code review findings. The goal is to determine which of the theoretical threats from Stage 4 have actual attack surface in the implementation. Output: a vulnerability assessment linking each identified vulnerability to the threats from Stage 4, with CVSS scores and exploit availability data.

**Stage 6: Attack modeling.** Construct attack trees (Section 1.2) for the highest-risk threat-vulnerability pairings. Simulate the attack paths to estimate the effort required and the impact achieved. This stage benefits from red-team exercises or tabletop simulations that walk through the attack steps against the actual system. Output: attack trees with probability and cost annotations, and a prioritized list of the most exploitable attack paths.

**Stage 7: Risk analysis and countermeasure prioritization.** Combine the business impact from Stage 1 with the attack probability from Stage 6 to compute risk scores for each threat. Prioritize countermeasures by risk reduction per dollar invested. Output: the final threat register, a risk matrix (likelihood vs. impact), and a treatment plan for each risk: mitigate (with a specific control, implementation owner, and deadline), accept (with documented risk acceptance by a named authority), transfer (with the specific transfer mechanism such as cyber insurance or SLA), or avoid (with the design change that eliminates the risk).

### 1.4 Trike

**Trike** is a threat-modeling methodology rooted in risk management rather than attack enumeration. Where STRIDE asks "what attacks are possible?" Trike asks "what risks does the system create for each stakeholder, and are those risks acceptable?"

The Trike process begins with a **requirements model** that defines the system's actors, their permitted actions on each asset, and the rules governing those actions. An actor-asset-action matrix catalogs every interaction: for example, the actor "Customer" can "read" and "create" the asset "Order," but cannot "delete" or "modify after submission." The actor "Admin" can "read," "create," "modify," and "delete" the asset "Order." Each cell in the matrix represents either an intended action (legitimate use), or an unintended action (a threat). Threats arise at the boundary between intended and unintended actions: if the system permits the "Customer" actor to "modify after submission" due to an access-control flaw, that unintended action constitutes a threat.

The **implementation model** maps the requirements model to the actual system design. Data Flow Diagrams trace how each actor-asset-action tuple is implemented: which API endpoint, which database query, which authorization check. The threat enumeration identifies every path through the DFD where an unintended action could occur. Each threat is assigned a risk value based on the asset's value (business impact) and the likelihood that the unintended action can be performed (attack feasibility).

Trike's strength is its focus on the gap between "what should happen" and "what can happen." It produces outputs naturally aligned with compliance requirements, because the requirements model maps directly to access-control policies and the threat enumeration documents where those policies might fail. Its weakness is the effort required to build the actor-asset-action matrix for complex systems with many actors and assets — the matrix grows as O(actors * assets * actions), which can become unwieldy for large-scale microservice architectures.

### 1.5 MITRE ATT&CK integration with threat modeling

Threat modeling outputs become significantly more actionable when mapped to the MITRE ATT&CK framework. Each STRIDE-identified threat or each attack-tree leaf node is annotated with the corresponding ATT&CK technique ID, enabling direct linkage to defensive controls.

From the e-commerce worked example in Section 1.1.1: the phishing threat against the admin maps to T1566.002 (Spearphishing Link). The IDOR vulnerability maps to T1530 (Data from Cloud Storage Object) or more generically to the tactic collection via application-layer exploitation. The SQL injection threat maps to T1190 (Exploit Public-Facing Application). The insider threat maps to T1078 (Valid Accounts). This mapping serves three purposes. First, it connects the threat model to the detection engineering lifecycle (Section 6): for each mapped ATT&CK technique, the SOC can verify whether a detection rule exists (Domain 27B §7.4 detection coverage ratio). Second, it enables threat-informed defense prioritization: the organization cross-references mapped techniques against threat intelligence on active adversaries targeting its sector (Domain 25) to prioritize mitigations for the techniques most likely to be used. Third, it provides a common language between the architecture team (who builds the threat model), the security engineering team (who implements controls), and the SOC (who operates detections).

### 1.6 Threat model output format

A production threat model produces three deliverables. The **threat register** is a structured table containing: threat ID, description, STRIDE category, affected DFD element, ATT&CK technique ID, CVSS base score, risk level (critical/high/medium/low), current controls, residual risk, treatment decision (mitigate/accept/transfer/avoid), and the responsible owner. The **risk heatmap** plots threats on a likelihood-vs-impact matrix, providing executive visibility into the risk landscape. The **treatment plan** details each mitigation control: what it is, who implements it, by what date, how its effectiveness will be verified, and what residual risk remains after implementation. The threat model is a living document — reviewed quarterly, updated when the system architecture changes, when new threat intelligence emerges, or when a security incident reveals a previously unmodeled threat.

---

## 2. Security design principles

The Saltzer-Schroeder principles (1975), foundational to secure system design:

**Least privilege.** Every component operates with the minimum privileges necessary for its function. A web server runs as an unprivileged user, not root. A microservice has IAM permissions only for the specific APIs it calls. A container runs with a minimal capability set (Domain 10 Chapter 10B §1.2).

**Defense in depth.** Multiple independent security layers: if one layer fails, the next layer provides protection. Example: WAF (blocks known attack patterns) + input validation (rejects malformed input) + parameterized queries (prevents SQL injection even if validation is bypassed) + database access control (limits damage even if injection succeeds) + network segmentation (contains the breach).

**Fail-safe defaults.** The default configuration denies access; access must be explicitly granted. A firewall's default policy is DROP. An IAM policy defaults to deny. A new user has no permissions until roles are assigned.

**Economy of mechanism.** The security mechanism should be simple enough to verify. Complex systems have more bugs; simple systems are more auditable. This principle argues for: small TCBs (Trusted Computing Bases), minimal API surfaces, and simple authorization logic.

**Complete mediation.** Every access to every object is checked against the access-control policy. No caching of authorization decisions (a cached "allowed" result may be stale if the policy changed). This principle is violated by: permission caching (JWT tokens that remain valid after the user's permissions are revoked), and by systems that check permissions at the front door but not at internal API boundaries.

**Open design.** The security of the system does not depend on the secrecy of its design (Kerckhoffs's principle extended to system architecture). The design can be public; security depends on the keys, credentials, and configuration — not on the attacker's ignorance of the mechanism.

**Separation of privilege.** Access requires multiple conditions (multi-factor authentication, dual-control for key management, multi-party approval for sensitive operations). No single credential or single compromise should grant full access.

**Least common mechanism.** Minimize shared resources between users/components. Shared resources (shared filesystems, shared memory, shared network segments) create information-leakage and interference channels. Process isolation, containers, and VM-based isolation implement this principle.

**Psychological acceptability.** The security mechanism should not make the system harder to use than necessary. If security is too burdensome, users circumvent it (writing passwords on sticky notes, disabling MFA, granting overly-broad permissions to avoid access-request delays).

---

## 3. Secure boot and measured boot

### 3.1 UEFI Secure Boot

UEFI Secure Boot verifies the digital signature of each boot component before executing it. The signature databases are stored in UEFI variables:

**PK (Platform Key).** The root of trust: the PK holder (typically the OEM) controls what can modify the other key databases. Only one PK is allowed.

**KEK (Key Exchange Key).** Keys authorized to modify the db and dbx. Typically includes the OEM's key and Microsoft's key (Microsoft's key allows Windows Update to add entries to db and dbx).

**db (Signature Database).** The allowlist: certificates and hashes of authorized EFI binaries. The UEFI firmware will only execute EFI binaries whose signature chains to a certificate in db or whose hash is in db. Microsoft's UEFI CA certificate is in db on most PCs (enabling any Microsoft-signed bootloader to execute).

**dbx (Forbidden Signature Database).** The denylist: hashes and certificates that are explicitly blocked. Used to revoke known-vulnerable bootloaders (e.g., the shim bootloader versions vulnerable to CVE-2023-40547 are added to dbx).

**MOK (Machine Owner Key).** A supplementary key database managed by the shim bootloader on Linux systems. When the Linux shim bootloader (signed by Microsoft's UEFI Third Party Marketplace CA) executes, it checks its own key database (the MOK list) in addition to the UEFI db. This allows Linux distributions to enroll distribution-specific signing keys without requiring changes to the OEM-controlled UEFI db. The `mokutil` utility manages MOK entries from the running OS, and changes take effect on next boot after user confirmation at the shim MOK management console. This is how Fedora, Ubuntu, and other distributions boot on Secure Boot-enabled hardware: Microsoft's third-party CA signs the shim, the shim's MOK list contains the distribution's GRUB and kernel signing key, and the shim verifies GRUB and the kernel against the MOK list.

**Boot flow.** The UEFI firmware verifies the first-stage bootloader (e.g., the Windows Boot Manager, or the Linux shim bootloader) against db. The first-stage bootloader verifies the next stage (the OS kernel or GRUB). Each stage verifies the next, forming a chain of trust rooted in the UEFI firmware's PK.

#### 3.1.1 Secure Boot attacks

**BootHole (CVE-2020-10713).** A buffer overflow vulnerability in GRUB2's configuration file parser. The `grub.cfg` file is not signed by GRUB2; only the GRUB2 binary itself is signature-verified. An attacker with write access to the filesystem containing `grub.cfg` (root privileges on a running system, or physical access to an unencrypted boot partition) could craft a malicious `grub.cfg` entry that overflowed a buffer in GRUB2's parser, achieving arbitrary code execution during the boot process — after Secure Boot verified GRUB2 but before the OS loaded. This bypassed Secure Boot without requiring a bootloader signature: the signed-and-verified GRUB2 binary itself contained the vulnerability. Remediation required: patching GRUB2, re-signing all affected GRUB2 binaries, adding the old vulnerable GRUB2 hashes to dbx (to prevent rollback to the vulnerable version), and updating the shim and kernel to maintain the chain of trust — a coordination problem across every Linux distribution and every OEM firmware.

**BlackLotus (CVE-2022-21894).** The BlackLotus bootkit exploited a vulnerability in an older, legitimately-signed Windows Boot Manager. Even though the boot manager was signed by Microsoft (and therefore allowed by db), it contained a vulnerability that allowed arbitrary code execution during boot. The bootkit leveraged the CVE-2022-21894 Secure Boot bypass to load an unsigned kernel driver, disable Hypervisor-protected Code Integrity (HVCI), BitLocker, and Windows Defender, and establish persistence that survived OS reinstallation. Microsoft revoked the vulnerable boot manager's hash (adding it to dbx), but the dbx update process is slow and incomplete across the installed base (Domain 11 Chapter 11A §3.5). BlackLotus was the first known in-the-wild UEFI bootkit capable of bypassing Secure Boot on fully patched Windows 11 systems — demonstrating that the Secure Boot revocation mechanism (dbx updates distributed through Windows Update) is a single point of failure when OEMs and cloud providers do not apply dbx updates promptly.

**dbx update failures as systemic risk.** The Secure Boot security model depends on timely dbx updates to revoke vulnerable bootloaders. In practice, dbx updates lag significantly: OEMs must test updates against their firmware before shipping them (to avoid bricking devices), cloud providers must validate updates across their VM fleet, and enterprises must schedule maintenance windows. The 2024 PKfail vulnerability (CVE-2024-8105) revealed that hundreds of device models from major OEMs shipped with a known test Platform Key ("DO NOT SHIP" / "DO NOT TRUST") rather than a production key, effectively disabling Secure Boot's entire trust chain on those devices. This was not a software bug but a supply-chain process failure — test keys intended for development leaked into production firmware images and were never replaced.

### 3.2 Measured boot and TPM

**Measured boot** extends Secure Boot by recording (measuring) each boot component into the TPM's Platform Configuration Registers (PCRs). A measurement is: `PCR_new = SHA-256(PCR_old || SHA-256(component))` — the PCR value is extended (not overwritten), creating a hash chain of all measured components. The PCR values reflect the exact sequence of boot components loaded.

**TPM PCR allocation.** PCR 0: UEFI firmware code. PCR 1: UEFI firmware configuration. PCR 2: option ROMs. PCR 3: option ROM configuration. PCR 4: MBR/boot manager. PCR 5: MBR/boot manager configuration. PCR 7: Secure Boot policy (db, dbx, KEK values). PCR 8–15: OS-defined (Linux IMA uses PCR 10).

The PCR allocation has direct implications for sealed-secret policies. Sealing a disk-encryption key to PCR 0+2+4+7 binds the key to the firmware code, option ROMs, boot manager, and Secure Boot policy. A firmware update changes PCR 0, invalidating the sealed secret until the secret is re-sealed to the new PCR values. Operators must plan for this: re-seal secrets before applying firmware updates, or use a recovery mechanism (PCR 7-only sealing plus BitLocker recovery key, or LUKS Tang/Clevis network-based unsealing as a fallback).

**Measured boot vs. Secure Boot: complementary roles.** Secure Boot is a preventive control: it refuses to execute code that lacks a valid signature, stopping unsigned malware from loading during boot. Measured boot is a detective control: it records exactly what loaded but does not stop anything from loading. The two are complementary. Secure Boot prevents known-bad code from executing; measured boot detects when the boot chain deviates from baseline. Measured boot catches scenarios that Secure Boot cannot: a legitimately signed-but-vulnerable bootloader (BlackLotus), a legitimately signed-but-outdated firmware with known vulnerabilities, or a firmware rootkit that subverts the Secure Boot verification itself (since a rootkit in the reset vector controls the Secure Boot process). Remote attestation based on measured boot values (Section 4.3) enables a remote verifier to detect these deviations even when the local Secure Boot check passes.

**Remote attestation.** A remote verifier requests a TPM quote: the TPM signs the current PCR values with the Attestation Key (AK — a key certified by the Endorsement Key, which is burned into the TPM at manufacturing). The verifier: validates the AK certificate chain (rooted in the TPM manufacturer's CA), verifies the quote signature, compares the PCR values against known-good values (from a golden-image baseline), and determines whether the platform has been tampered with. If PCR values don't match the baseline, the platform may be running modified firmware, an unauthorized bootloader, or a bootkit.

### 3.3 SRTM vs DRTM

**SRTM (Static Root of Trust for Measurement).** The root of trust is the platform reset vector: the first code executed after power-on (the UEFI firmware). The entire boot chain from reset to OS is measured. The firmware executes, measures itself into PCR 0, then loads and measures the boot manager into PCR 4, which loads and measures the OS kernel, and so on. The critical dependency: if the UEFI firmware itself is compromised (a firmware rootkit flashed into the SPI flash chip), SRTM is defeated — the compromised firmware controls the measurement process and can lie about its own measurements. SRTM's Trusted Computing Base includes the entire firmware, which on modern platforms can exceed 16 MB of complex C code — a large attack surface.

**DRTM (Dynamic Root of Trust for Measurement).** The root of trust is established dynamically during runtime, bypassing the boot firmware entirely. **Intel TXT (Trusted Execution Technology)**: the CPU executes the `GETSEC[SENTER]` instruction, which performs the following atomic sequence: puts all other CPU cores into a known quiescent state (preventing interference from potentially compromised code running on other cores), resets the TPM's dynamic PCRs (PCR 17–22) to their initial values, loads and verifies the SINIT ACM (Authenticated Code Module) — a signed binary provided by Intel whose signature is verified against a hash fused into the CPU's microcode (not by the firmware), then the SINIT ACM takes control, measures the Measured Launch Environment (MLE — typically a hypervisor, an OS kernel, or a tboot trusted boot module) into the dynamic PCRs, and transfers control to the MLE. Because the SINIT ACM is verified by the CPU microcode itself, even a fully compromised firmware cannot tamper with the DRTM measurement chain. The MLE's measurement in PCR 17/18 reflects only the MLE's code and configuration — not the firmware — providing a trustworthy measurement even on a platform with a firmware rootkit.

**AMD SKINIT**: similar mechanism using the `SKINIT` instruction. When a CPU core executes `SKINIT`, the processor: disables interrupts on all cores, resets the TPM dynamic PCRs, hashes the 64 KB Secure Loader Block (SLB) pointed to by the EAX register into PCR 17, and transfers control to the SLB. The SLB (analogous to Intel's SINIT ACM + MLE combination) then measures and launches the secure environment. AMD SKINIT differs from Intel TXT in that the SLB is not signed by AMD — the CPU simply measures it into the PCR without verifying a signature. The security guarantee is integrity-based (the PCR value reveals exactly what SLB was loaded), not authenticity-based (the CPU does not verify who wrote the SLB). Remote attestation verifies the SLB's measurement against known-good values, achieving the same end goal through a different mechanism.

DRTM provides a trustworthy measurement even on a platform with compromised firmware — as long as the CPU and TPM hardware are genuine.

---

## 4. TPM 2.0

### 4.1 Architecture and hierarchy

TPM 2.0 defines three authorization hierarchies:

**Platform hierarchy.** Controlled by the platform manufacturer/OEM. Used during manufacturing and firmware management. Typically disabled after provisioning.

**Storage hierarchy (Owner).** Controlled by the platform owner (the organization or user). Used for general-purpose key management, sealing, and application-level TPM operations.

**Endorsement hierarchy.** Contains the Endorsement Key (EK — a unique, permanent key burned into the TPM during manufacturing). The EK is used for: TPM identity (the EK certificate, signed by the TPM manufacturer, proves the TPM is genuine), attestation (the AK is certified by the EK), and decryption (the EK can decrypt data sent to this specific TPM — used in credential provisioning).

Each hierarchy has its own authorization value (a password or policy) and its own Storage Root Key (SRK in the case of the storage hierarchy, or a primary key generated under the hierarchy). Keys created under a hierarchy are bound to that hierarchy's SRK and cannot be used under a different hierarchy. The PCR banks in TPM 2.0 support multiple hash algorithms simultaneously — SHA-1 and SHA-256 are mandatory, with SHA-384 and SHA-512 optional. Each PCR exists independently in each bank, so PCR 7 in the SHA-256 bank has a different (independently computed) value from PCR 7 in the SHA-1 bank. Modern attestation and sealing operations should reference the SHA-256 bank; the SHA-1 bank is maintained for backward compatibility.

### 4.2 Sealing and unsealing

**TPM2_Create** with a policy: creates a key (or a sealed data blob) that can only be used (unsealed) when specific conditions are met. The most common condition: **PCR policy** — the sealed data can only be decrypted when the TPM's PCRs match specified values. This binds the data to a specific platform state: if the boot chain changes (indicating tampering or a different boot configuration), the PCRs change, and the sealed data is inaccessible.

Use case: Full-Disk Encryption (BitLocker, LUKS with `clevis`/`tang`). The disk-encryption key is sealed to the TPM with a PCR policy. At boot, the TPM unseals the key only if the PCR values match — proving the boot chain is unmodified. If the platform is tampered with (a bootkit, a different OS), the PCR values change, and the key is not released — the disk remains encrypted.

The following `tpm2-tools` sequence demonstrates sealing a secret to PCR 7 (Secure Boot policy):

```bash
# Create a primary key under the storage hierarchy
tpm2_createprimary -C o -g sha256 -G rsa2048 -c primary.ctx

# Read current PCR 7 value (SHA-256 bank) for the seal policy
tpm2_pcrread sha256:7 -o pcr7.bin

# Create a policy session requiring PCR 7 to match current value
tpm2_startauthsession -S session.ctx
tpm2_policypcr -S session.ctx -l sha256:7 -f pcr7.bin -L pcr7.policy
tpm2_flushcontext session.ctx

# Seal a secret (e.g., a LUKS passphrase) under the PCR policy
echo "my-disk-encryption-key" > secret.txt
tpm2_create -C primary.ctx -g sha256 -u seal.pub -r seal.priv \
    -L pcr7.policy -i secret.txt

# Load the sealed object
tpm2_load -C primary.ctx -u seal.pub -r seal.priv -c seal.ctx

# Unseal — this succeeds only if PCR 7 still matches the policy
tpm2_startauthsession -S session.ctx --policy-session
tpm2_policypcr -S session.ctx -l sha256:7 -f pcr7.bin
tpm2_unseal -c seal.ctx -p session:session.ctx -o unsealed.txt
tpm2_flushcontext session.ctx
```

If the Secure Boot policy changes between sealing and unsealing (for example, a dbx update changes the Secure Boot policy, altering PCR 7), the `tpm2_unseal` command fails with `TPM2_RC_POLICY_FAIL`, and the secret remains inaccessible. This is the intended behavior — the secret is released only when the boot state matches the state at sealing time.

### 4.3 Key attestation and remote attestation

**TPM2_Certify** allows one TPM key to certify (sign a statement about) another TPM key. The statement includes: the certified key's public portion, the key's attributes (whether it was generated by the TPM, whether it is non-exportable, whether it is sealed to specific PCRs). A remote party can verify the certificate and trust that the key has the claimed properties — because the certification was performed inside the TPM hardware (the certifying key never leaves the TPM).

Remote attestation with `tpm2-tools`:

```bash
# Generate an Attestation Key (AK) under the endorsement hierarchy
tpm2_createek -c ek.ctx -G rsa2048 -u ek.pub
tpm2_createak -C ek.ctx -c ak.ctx -G rsa2048 -u ak.pub -n ak.name

# Generate a quote signing the current PCR values with the AK
# The nonce is provided by the remote verifier to prevent replay
tpm2_quote -c ak.ctx -l sha256:0,1,2,3,4,7 \
    -q "verifier-nonce-hex" -m quote.msg -s quote.sig -o pcrs.out

# The verifier receives: quote.msg, quote.sig, pcrs.out, ak.pub
# and validates:
# 1. AK certificate chain roots in a trusted TPM manufacturer CA
# 2. Quote signature verifies under the AK public key
# 3. Nonce in the quote matches the verifier's nonce (anti-replay)
# 4. PCR values in the quote match known-good baseline
```

### 4.4 TPM attacks and defenses

**TPM reset attack (physical).** On some hardware, the TPM's LPC or SPI bus can be physically probed. An attacker with physical access and a logic analyzer can sniff the TPM bus during boot, capturing the unsealed secret (e.g., the BitLocker VMK) as it is transmitted from the TPM to the CPU in plaintext over the LPC/SPI bus. This was demonstrated against BitLocker TPM-only configurations on Lenovo ThinkPads and Microsoft Surface devices by researchers at Pulse Security and Dolos Group. The attack requires: removing the laptop's case, attaching a logic analyzer or bus interposer to the TPM's LPC/SPI pins, rebooting the laptop, and capturing the VMK from the bus traffic. Cost: approximately $200 in hardware (a Saleae logic analyzer or a custom SPI interposer).

**Defense: TPM + PIN.** Configuring BitLocker (or LUKS) to require both a TPM unseal and a user-provided PIN at boot. The TPM seals the encryption key to a compound policy: PCR values AND PIN. The PIN is not transmitted over the TPM bus — it is combined with the TPM's output in the CPU. Even if the attacker captures the bus traffic, they obtain only one factor of a two-factor requirement. Microsoft strongly recommends TPM + PIN for high-security deployments. Group Policy: `Computer Configuration > Administrative Templates > Windows Components > BitLocker Drive Encryption > Operating System Drives > Require additional authentication at startup` — set to Enabled with "Require startup PIN with TPM."

**Discrete TPM vs. firmware TPM (fTPM).** Discrete TPMs are separate physical chips connected to the CPU via the LPC or SPI bus — they are vulnerable to the bus-sniffing attack described above. Firmware TPMs (Intel PTT, AMD fTPM) run TPM 2.0 logic inside the CPU's trusted execution environment (Intel ME or AMD PSP). Because the fTPM communicates with the CPU through internal, on-die channels rather than an external bus, the bus-sniffing attack does not apply. However, fTPMs inherit the attack surface of the CPU's management engine: the 2023 faulTPM attack demonstrated that AMD's fTPM could be compromised by injecting voltage glitches into the AMD PSP's SPI bus during startup, allowing extraction of fTPM-sealed secrets. The attack required approximately $200 in equipment and physical access for several hours. Discrete TPMs with physical tamper resistance (FIPS 140-2 Level 3 certification) remain the strongest option for high-assurance deployments.

---

## 5. Confidential computing

### 5.1 Intel SGX and TDX

**SGX (Software Guard Extensions).** Creates isolated memory regions (enclaves) that are encrypted and integrity-protected by the CPU hardware. The enclave's memory (stored in the Enclave Page Cache — EPC) is decrypted only inside the CPU's caches; in DRAM, it is encrypted with a per-enclave key. Even the OS, hypervisor, and firmware cannot read or modify enclave memory.

SGX attestation: the enclave generates a **report** (a signed measurement of the enclave's code and configuration, signed by a CPU-specific key). The report is sent to the Intel Attestation Service (IAS) or a DCAP (Data Center Attestation Primitives) verifier, which validates the CPU's signature and returns an attestation result. Remote parties can then trust that the enclave is running the expected code on genuine Intel hardware.

SGX has been deprecated on consumer CPUs (12th gen+) and is now positioned for server-side confidential computing via TDX.

**TDX (Trust Domain Extensions).** Intel's VM-level confidential computing: an entire VM (Trust Domain — TD) is encrypted and integrity-protected. The TD's memory is inaccessible to the hypervisor, the host OS, and other VMs. TDX introduces the TDX Module — a firmware component loaded by the CPU microcode that mediates all interactions between the TD and the untrusted VMM. The TD communicates with the VMM through TDCALL (a TD-to-TDX-Module instruction) and the VMM communicates with the TDX Module through SEAMCALL (a VMM-to-TDX-Module instruction). Neither the VMM nor the TD can bypass the TDX Module. TDX provides a virtual TPM (vTPM) within the TD, enabling the TD's guest OS to perform measured boot and key attestation using standard TPM interfaces — but backed by hardware-protected TDX state rather than a physical TPM chip. Remote attestation for TDX uses the TD Quote: the TD generates a report via TDCALL[TDG.MR.REPORT], the TDX Module signs it with a platform attestation key, and the quote is verified against Intel's attestation infrastructure (similar to SGX DCAP attestation but at the VM granularity).

### 5.2 AMD SEV, SEV-ES, SEV-SNP

**SEV (Secure Encrypted Virtualization).** Each VM's memory is encrypted with a per-VM key managed by the AMD Secure Processor (AMD-SP, an ARM-based co-processor). The hypervisor cannot read VM memory in plaintext.

**SEV-ES (Encrypted State).** Extends SEV by encrypting the VM's CPU register state during VM exits (when the VM transfers control to the hypervisor for I/O or other operations). Without SEV-ES, the hypervisor can read the VM's registers during a VM exit — leaking data.

**SEV-SNP (Secure Nested Paging).** Adds integrity protection: the AMD-SP maintains a Reverse Map Table (RMP) that tracks which VM owns each physical page. The hypervisor cannot remap pages between VMs (preventing page-swap attacks where the hypervisor substitutes one VM's page for another's) or replay old page contents. The VMSA (Virtual Machine Save Area) — containing the VM's CPU register state — is encrypted and integrity-protected by SEV-SNP, preventing the hypervisor from tampering with the VM's execution state.

SEV-SNP attestation: the VM requests an attestation report from the AMD-SP. The report contains: the VM's launch measurement (hash of the initial firmware/OS), the AMD-SP's firmware version, and the VM's policy (whether debugging is allowed, minimum firmware version). The report is signed by the AMD-SP's attestation key (certified by AMD's CA).

### 5.3 Arm CCA (Confidential Compute Architecture)

**Realm Management Extension (RME).** Introduces a fourth security state: **Realm** (in addition to Secure, Non-Secure, and Root). A Realm is a confidential VM whose memory is isolated from both the Non-Secure world (the hypervisor, normal OS) and the Secure world (TrustZone). The Realm Management Monitor (RMM) runs at EL2 in the Realm world, managing Realm VMs. The Monitor (at EL3, Root world) mediates transitions between Realm, Secure, and Non-Secure worlds.

The **Granule Protection Table (GPT)** enforces memory isolation at the physical address level. Each 4 KB memory granule is tagged in the GPT with its owning world (Non-Secure, Secure, Realm, or Root). Hardware enforces these tags on every memory access: a Non-Secure access to a Realm-tagged granule faults, regardless of page table mappings. This is the hardware-level mechanism that prevents the hypervisor from reading Realm memory.

CCA provides: memory encryption and integrity for Realms (hardware-enforced, per-Realm keys), attestation (the RMM produces an attestation token signed by a platform key, certifying the Realm's initial state), and hypervisor isolation (the hypervisor in the Non-Secure world cannot read or modify Realm memory).

### 5.4 Comparison and known attacks

| Property | Intel SGX | Intel TDX | AMD SEV-SNP | Arm CCA |
|---|---|---|---|---|
| Isolation granularity | Process (enclave) | VM (Trust Domain) | VM (SNP guest) | VM (Realm) |
| Trust boundary excludes | OS, hypervisor, firmware | Hypervisor, host OS, other VMs | Hypervisor, host OS, other VMs | Hypervisor, Normal OS, Secure world |
| TCB includes | CPU, SGX microcode | CPU, TDX Module (CPU-loaded firmware) | CPU, AMD-SP firmware | CPU, RMM, Monitor (EL3) |
| Memory encryption | MEE (128-bit key per enclave) | TME-MK (per-TD AES-XTS keys) | SME (per-VM AES-128 keys) | Per-Realm keys (implementation-specific) |
| Integrity protection | Yes (Merkle tree in MEE) | Yes (hardware MAC per cache line) | Yes (RMP-enforced) | Yes (GPT-enforced) |
| Max protected memory | EPC size (128-512 MB typical) | Full VM memory (no EPC limit) | Full VM memory | Full VM memory |
| Attestation mechanism | EPID or DCAP quote | TD Quote (DCAP-based) | AMD-SP attestation report | CCA attestation token |

**Known attacks on confidential VMs.** The **SEVered** attack (2018) targeted AMD SEV (pre-SNP) by exploiting the hypervisor's ability to remap guest-physical-to-host-physical page mappings. The hypervisor modified the nested page tables to map a guest's network-accessible page to a different guest-physical page containing sensitive data. When the guest's web server served the page, it unknowingly transmitted the sensitive data to the attacker. SEV-SNP's RMP (Reverse Map Table) prevents this attack by ensuring that each host-physical page has a single, verified mapping to a guest-physical address.

The **CipherLeaks** attack (2021) exploited the fact that AMD SEV's memory encryption (AES in ECB mode for early SEV versions) leaked information through ciphertext patterns. Identical plaintext blocks produce identical ciphertext blocks in ECB mode, enabling the attacker to detect repeated memory patterns without decrypting the data. AMD addressed this in subsequent SEV versions by moving to AES-XTS mode with tweaking based on the physical address, eliminating the ECB-mode weakness.

**Voltage glitching attacks** against Intel SGX (the Plundervolt/VoltPillager attacks) demonstrated that manipulating the CPU's voltage rail during SGX enclave execution could induce computational faults that leak enclave secrets. These attacks require physical access to the voltage regulator on the motherboard. Cloud providers mitigate this by controlling physical access to server hardware, but colocation and edge-deployment scenarios remain exposed.

**Use cases for confidential computing** include: multi-tenant cloud isolation (a tenant's workload is protected from a compromised hypervisor or a malicious cloud administrator), confidential AI training (training ML models on sensitive data that must not be visible to the cloud operator), secure enclaves for cryptographic key management (running an HSM-equivalent inside an SGX enclave or a TDX TD, where key material is never exposed to the host), and privacy-preserving data analytics (multiple parties contribute encrypted data to a computation inside a confidential VM, where the data is decrypted, processed, and the results are returned — no party sees another's raw data).

---

## 6. Detection engineering

### 6.1 The detection lifecycle

**Requirements.** What threats must be detected? Driven by: the organization's threat model (which ATT&CK techniques are relevant — Domain 25), regulatory requirements (PCI DSS requires monitoring of cardholder-data access), and incident history (previous incidents reveal detection gaps).

**Data source identification.** Each detection requires specific telemetry: process creation (Sysmon Event 1, EDR process telemetry), network connections (firewall logs, Zeek conn.log, EDR network telemetry), authentication events (Windows Security log 4624/4625, cloud provider sign-in logs), file modifications (Sysmon Event 11, auditd), registry changes (Sysmon Event 13), DNS queries (Sysmon Event 22, passive DNS).

**Rule development.** Write the detection logic in the target SIEM's query language (SPL, KQL, EQL, YARA-L) or in a portable format (Sigma — translated to each SIEM's native language). The rule specifies: the data source (log type), the filter conditions (field-value matches, regex patterns, statistical thresholds), and the alert metadata (severity, ATT&CK mapping, false-positive notes).

**Testing and validation.** Replay historical logs through the rule (does it trigger on known-bad events?). Red-team testing (execute the technique in a lab and verify the rule fires). Validate the false-positive rate (run against production logs for a burn-in period — a rule that generates 1000 alerts/day with 99% false positives is useless).

**Deployment and tuning.** Deploy to production SIEM. Tune: add exclusions for known-benign activity (the specific admin tool that legitimately accesses LSASS, the monitoring agent that legitimates creates remote threads), adjust thresholds, and refine field conditions. Tuning is continuous — new false positives emerge as the environment changes.

**Detection health monitoring.** Verify that detections are still firing: a detection that hasn't triggered in 6 months may be: working perfectly (no attacks), broken (the log source changed format, the SIEM index was renamed, the rule has a typo), or blind (the attacker is evading it). Detection health checks: periodic red-team validation, canary events (inject known-bad test events and verify the rule fires), and data-source monitoring (alert if the expected log source stops sending data).

### 6.2 Detection-as-Code

Production detection engineering treats detection rules as code artifacts, subject to the same version control, peer review, testing, and CI/CD pipeline disciplines as application code.

The Detection-as-Code workflow stores all Sigma rules, SIEM queries, and SOAR playbooks in a Git repository. Each rule file includes: the detection logic, metadata (author, date, severity, ATT&CK mapping, known false positives), and automated test cases (sample log events that should and should not trigger the rule). A CI pipeline validates each rule on push: syntax checking (the Sigma rule parses correctly), compilation (the Sigma rule converts to the target SIEM's native query language via `sigma-cli`), unit testing (the rule triggers on the positive test events and does not trigger on the negative test events), and quality gates (the rule has all required metadata fields, the severity is justified, the ATT&CK mapping is valid). After passing CI, the rule is deployed to the SIEM through an automated deployment pipeline — for Splunk, this means pushing SPL savedsearches.conf to the search head cluster; for Elastic, it means pushing detection rules via the Elastic Security API; for Sentinel, it means deploying KQL analytics rules via ARM templates or Terraform.

This pipeline eliminates the manual, error-prone process of creating rules through SIEM GUIs, ensures all rules are reviewed before deployment, and enables rollback (reverting a detection rule is a `git revert`).

### 6.3 Sigma rule deep dive

Sigma is a generic and open signature format for SIEM rules. A complete Sigma rule contains the following fields:

```yaml
title: LSASS Memory Access by Non-System Process
id: 0d894093-71bc-43c3-8985-4513b67d1a4a
status: stable
description: >
    Detects processes accessing lsass.exe memory with read permissions,
    which may indicate credential dumping using tools like Mimikatz,
    ProcDump, or direct NTAPI calls (NtReadVirtualMemory).
references:
    - https://attack.mitre.org/techniques/T1003/001/
    - https://docs.microsoft.com/en-us/sysinternals/downloads/sysmon
author: Security Engineering Team
date: 2025-03-15
modified: 2025-04-20
tags:
    - attack.credential_access
    - attack.t1003.001
logsource:
    category: process_access
    product: windows
detection:
    selection:
        TargetImage|endswith: '\lsass.exe'
        GrantedAccess|contains:
            - '0x1010'   # PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION
            - '0x1410'   # PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
            - '0x1438'   # Full access commonly used by Mimikatz
            - '0x143a'
    filter_system:
        SourceImage|startswith:
            - 'C:\Windows\System32\'
            - 'C:\Windows\SysWOW64\'
    filter_av:
        SourceImage|contains:
            - '\MsMpEng.exe'
            - '\csfalconservice.exe'
    condition: selection and not (filter_system or filter_av)
falsepositives:
    - Legitimate security tools performing memory scanning
    - Vulnerability scanners with credential collection capabilities
level: high
```

The `logsource` field abstracts the log source: `category: process_access` with `product: windows` maps to Sysmon Event 10 (ProcessAccess) or equivalent EDR telemetry. The Sigma converter (sigma-cli) translates this abstraction to the concrete SIEM query. The `detection` section uses selection/filter/condition logic: the `selection` defines what to match, `filter_*` sections define exclusions, and the `condition` combines them with boolean logic. The `tags` field uses the ATT&CK taxonomy (attack.tactic, attack.technique_id).

#### 6.3.1 Sigma rule: DCSync detection

```yaml
title: DCSync Attack via DRS Replication
id: 2a7e5b3d-9f1a-4e8c-b6d2-1c3a5f7e9b0d
status: stable
description: >
    Detects replication requests from non-domain-controller sources,
    indicating a DCSync attack using Mimikatz lsadump::dcsync or
    Impacket secretsdump.py. DCSync abuses the MS-DRSR protocol
    to replicate password hashes from a domain controller.
references:
    - https://attack.mitre.org/techniques/T1003/006/
author: Security Engineering Team
date: 2025-02-10
tags:
    - attack.credential_access
    - attack.t1003.006
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4662
        AccessMask: '0x100'
        Properties|contains:
            - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes
            - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes-All
    filter_dc:
        SubjectUserName|endswith: '$'
        # Filter domain controller machine accounts
        # This filter requires tuning: add your DC machine account names
    condition: selection and not filter_dc
falsepositives:
    - Azure AD Connect synchronization service accounts
    - Legitimate replication monitoring tools
level: critical
```

#### 6.3.2 Sigma rule: lateral movement via PsExec

```yaml
title: PsExec Service Installation
id: 3b8e6c4f-a21d-4f9e-c7e3-2d4b6f8a0c1e
status: stable
description: >
    Detects the installation of the PSEXESVC service, which is created
    when PsExec executes commands on a remote system. PsExec copies
    its service binary to the ADMIN$ share and installs it as a service.
references:
    - https://attack.mitre.org/techniques/T1021/002/
    - https://attack.mitre.org/techniques/T1569/002/
author: Security Engineering Team
date: 2025-01-20
tags:
    - attack.lateral_movement
    - attack.t1021.002
    - attack.execution
    - attack.t1569.002
logsource:
    product: windows
    service: system
detection:
    selection:
        EventID: 7045
        ServiceName|contains:
            - 'PSEXESVC'
            - 'psexec'
    condition: selection
falsepositives:
    - Legitimate administrative use of PsExec by IT operations
level: high
```

#### 6.3.3 Sigma rule: defense evasion via event log clearing

```yaml
title: Windows Event Log Cleared
id: 4c9f7d50-b32e-5a0f-d8f4-3e5c7a9b1d2f
status: stable
description: >
    Detects clearing of Windows event logs, a common defense evasion
    technique used by attackers to cover their tracks after compromise.
    Event ID 1102 is logged in the Security log when it is cleared;
    Event ID 104 is logged in the System log for any log clearing.
references:
    - https://attack.mitre.org/techniques/T1070/001/
author: Security Engineering Team
date: 2025-03-01
tags:
    - attack.defense_evasion
    - attack.t1070.001
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 1102
    condition: selection
falsepositives:
    - Legitimate log rotation by system administrators (rare on Security log)
level: high
```

#### 6.3.4 Sigma rule: persistence via scheduled task creation

```yaml
title: Suspicious Scheduled Task Creation
id: 5d0a8e61-c43f-6b1a-e9a5-4f6d8b0c2e3a
status: stable
description: >
    Detects creation of scheduled tasks with suspicious characteristics:
    tasks running from temp directories, AppData, or public folders,
    which commonly indicate malware persistence or C2 callbacks.
references:
    - https://attack.mitre.org/techniques/T1053/005/
author: Security Engineering Team
date: 2025-04-05
tags:
    - attack.persistence
    - attack.t1053.005
    - attack.execution
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4698
    filter_suspicious_paths:
        TaskContent|contains:
            - '\AppData\Local\Temp\'
            - '\AppData\Roaming\'
            - '\Users\Public\'
            - '\ProgramData\'
            - '\Windows\Temp\'
            - 'powershell -e'
            - 'cmd /c'
            - 'mshta'
            - 'wscript'
            - 'cscript'
    condition: selection and filter_suspicious_paths
falsepositives:
    - Legitimate software installers creating scheduled tasks in AppData
    - IT automation tools
level: medium
```

### 6.4 Detection quality metrics

Detection quality is measured across five dimensions. The **true positive rate** (sensitivity) measures the proportion of actual attacks that the detection correctly identifies — a rule with 60% true positive rate misses 40% of the attacks it is designed to detect. The **false positive rate** measures benign events that incorrectly trigger the detection — the single most impactful metric for SOC operational efficiency, because every false positive consumes analyst time. A well-tuned rule targets a false positive rate below 10%; rules above 50% should be redesigned or retired. The **mean time to detect (MTTD)** for each rule measures latency from technique execution to alert generation — this includes log collection delay, SIEM ingestion and parsing time, and rule evaluation frequency. The **detection coverage heatmap** maps active rules to ATT&CK techniques using the ATT&CK Navigator, producing a visual representation of which techniques have detections and which have gaps. The **rule health score** combines data-source availability (is the rule's log source still feeding data?), trigger recency (when did the rule last fire — either on an attack or a canary event?), and false positive trend (is the FP rate increasing, indicating environmental drift?).

---

## 7. SIEM platforms

### 7.1 Splunk SPL

Splunk's Search Processing Language operates on field-value pairs extracted from indexed data. For threat hunting and detection, SPL combines filtering, statistical analysis, and time-series correlation.

Credential dumping detection (LSASS access with specific access masks):

```spl
index=sysmon EventCode=10 TargetImage="*\\lsass.exe"
    GrantedAccess IN ("0x1010", "0x1410", "0x1438", "0x143a")
    NOT SourceImage IN ("C:\\Windows\\System32\\*", "C:\\Program Files\\*")
| stats count values(SourceImage) as tools values(GrantedAccess) as access_flags
    by Computer SourceProcessGUID
| where count > 0
| lookup asset_inventory host AS Computer OUTPUT business_unit criticality
| sort - count
```

Lateral movement detection using `eventstats` for baseline deviation:

```spl
index=wineventlog EventCode=4624 Logon_Type=3
| bin _time span=1h
| stats dc(host) as unique_hosts_accessed by Account_Name _time
| eventstats avg(unique_hosts_accessed) as avg_hosts
    stdev(unique_hosts_accessed) as stdev_hosts by Account_Name
| eval threshold = avg_hosts + (3 * stdev_hosts)
| where unique_hosts_accessed > threshold AND unique_hosts_accessed > 5
| table _time Account_Name unique_hosts_accessed avg_hosts threshold
```

This query baselines each account's normal lateral-movement pattern (how many unique hosts they authenticate to per hour) and alerts when activity exceeds 3 standard deviations above the mean — detecting an account being used for network-wide reconnaissance or lateral movement without hardcoded thresholds.

### 7.2 Elastic KQL and EQL

Elastic Security's KQL provides ad-hoc search, while EQL enables sequence-based detections that correlate ordered events.

KQL for suspicious PowerShell with encoded commands:

```
process.name: "powershell.exe" and process.args: ("-enc" or "-encodedcommand" or "-e ") and not process.parent.name: ("sccm*" or "intune*")
```

EQL sequence detecting command execution followed by credential access:

```eql
sequence by host.id with maxspan=5m
  [process where event.type == "start" and
   process.name in ("cmd.exe", "powershell.exe") and
   process.parent.name != "explorer.exe"]
  [process where event.type == "start" and
   process.name in ("mimikatz.exe", "procdump.exe", "rundll32.exe") and
   process.args : ("*sekurlsa*", "*lsass*", "*comsvcs*")]
```

EQL sequence detecting lateral movement through WMI:

```eql
sequence by source.ip with maxspan=2m
  [authentication where event.outcome == "success" and
   winlog.logon.type == "Network"]
  [process where event.type == "start" and
   process.parent.name == "WmiPrvSE.exe"]
```

### 7.3 Microsoft Sentinel KQL

Sentinel uses Kusto Query Language with operators designed for security analytics.

Entity behavior anomaly detection for unusual sign-in patterns:

```kql
let lookback = 14d;
let threshold = 3;
SigninLogs
| where TimeGenerated > ago(lookback)
| where ResultType == 0  // Successful sign-ins only
| summarize DistinctCountries = dcount(LocationDetails_dynamic.countryOrRegion),
            Countries = make_set(LocationDetails_dynamic.countryOrRegion),
            SignInCount = count()
    by UserPrincipalName, bin(TimeGenerated, 1d)
| where DistinctCountries > threshold
| project TimeGenerated, UserPrincipalName, DistinctCountries, Countries
```

Sentinel's UEBA (User and Entity Behavior Analytics) builds behavioral baselines for users and entities automatically, using ML to establish normal patterns for sign-in location, sign-in time, accessed resources, and data volume. Deviations generate anomaly scores that feed into analytics rules. UEBA entity pages provide an aggregated timeline showing all of an entity's activities, anomalies, and associated alerts — enabling an analyst to understand the full scope of a potentially compromised identity without manually correlating across multiple log sources.

### 7.4 Chronicle YARA-L

Google Chronicle's YARA-L (YARA-Like Language) operates on UDM (Unified Data Model) events with temporal operators.

```
rule dcsync_detection {
    meta:
        author = "Security Engineering"
        description = "Detects DCSync replication from non-DC hosts"
        severity = "CRITICAL"
        mitre_attack = "T1003.006"

    events:
        $e.metadata.event_type = "GENERIC_EVENT"
        $e.metadata.product_event_type = "4662"
        $e.security_result.action_details = "0x100"
        (
            $e.target.resource.attribute.labels["Properties"] = /.*1131f6aa.*/ or
            $e.target.resource.attribute.labels["Properties"] = /.*1131f6ad.*/
        )
        // Exclude domain controller machine accounts
        not $e.principal.user.userid = /.*\$$/

    condition:
        $e
}
```

### 7.5 SIEM architecture and log source priority

A production SIEM deployment has four layers: collection (agents, forwarders, and API pollers that gather logs from sources), parsing and normalization (transforming raw logs into a common schema with extracted fields), enrichment (adding context: asset inventory data, GeoIP, threat intelligence, user identity), and correlation/alerting (applying detection rules to enriched events).

Log source priority by detection value per ATT&CK tactic:

| Tactic | Highest-value log sources |
|---|---|
| Initial Access | Email gateway logs, web proxy logs, VPN/SSO authentication logs |
| Execution | Process creation (Sysmon 1 / EDR), PowerShell script block logging (4104), command-line auditing (4688) |
| Persistence | Scheduled task creation (4698), service installation (7045), registry modification (Sysmon 13) |
| Privilege Escalation | Process creation with parent-child analysis, token manipulation events, Sysmon 10 (process access) |
| Defense Evasion | Sysmon image load (7), file creation in system directories (Sysmon 11), event log clearing (1102/104) |
| Credential Access | LSASS access (Sysmon 10), Kerberos TGS requests (4769), NTLM authentication (4776), DCSync (4662) |
| Lateral Movement | Network logon (4624 type 3), SMB session setup, remote service creation (7045 on targets), RDP (4624 type 10) |
| Exfiltration | Network connection logs (Zeek conn.log, firewall), DNS query logs, HTTP POST volume anomaly, cloud storage API logs |
| Command and Control | DNS query logs (Sysmon 22, Zeek dns.log), TLS metadata (JA3/JA3S), HTTP request patterns, proxy logs |

Process creation logging (Sysmon Event 1 or EDR equivalent) provides the single highest detection-value data source across the most ATT&CK tactics. Organizations that can deploy only one telemetry source should start with process creation with full command-line capture.

---

## 8. EDR telemetry and bypass detection

### 8.1 EDR telemetry sources

EDR agents collect: process creation (with full command line, parent process, user, hashes), network connections (source/dest IP:port, process, protocol), file operations (create, modify, delete, rename — with path and hash), registry operations (create key, set value, delete), image loads (DLL loads with path, hash, signature status), and in-memory events (ETW-sourced: AMSI scan results, PowerShell script blocks, .NET assembly loads).

The telemetry depth varies by EDR product. CrowdStrike Falcon captures direct syscalls and kernel callbacks, recording process creation via the `PsSetCreateProcessNotifyRoutine` kernel callback, image loads via `PsSetLoadImageNotifyRoutine`, and thread creation via `PsSetCreateThreadNotifyRoutine`. Microsoft Defender for Endpoint combines kernel-level ETW providers (Microsoft-Windows-Kernel-Process, Microsoft-Windows-Kernel-File) with user-mode hooks in ntdll.dll. SentinelOne uses a kernel driver with inline hooks on critical system calls. Each approach has distinct evasion implications: EDR products that rely primarily on user-mode ntdll hooks are more susceptible to unhooking attacks than those with kernel-level visibility.

### 8.2 EDR bypass detection

When attackers evade EDR (Domain 11 Chapter 11B), the evasion itself creates detectable anomalies: **syscall frequency analysis** (a process making an unusual number of `NtAllocateVirtualMemory` or `NtWriteVirtualMemory` calls — indicative of injection), **call-stack anomalies** (a syscall originating from unbacked memory or from mid-function in ntdll — indicative of direct/indirect syscalls), **image-load patterns** (a process that loads `ntdll.dll` twice — indicative of unhooking via KnownDlls remapping), and **PEB inconsistency** (a process whose PEB `ImageBaseAddress` doesn't match the loaded image — indicative of process hollowing).

Sigma rule for detecting ntdll unhooking (double ntdll.dll load):

```yaml
title: Potential ntdll.dll Unhooking via Double Load
id: 6e1b9f72-d54a-7c2b-fa06-5a7e9c1d3f4b
status: experimental
description: >
    Detects a process loading ntdll.dll from an unusual path
    (not System32), which may indicate an EDR bypass technique
    where the attacker maps a fresh copy of ntdll from disk
    to overwrite the hooked in-memory copy.
tags:
    - attack.defense_evasion
    - attack.t1562.001
logsource:
    category: image_load
    product: windows
detection:
    selection:
        ImageLoaded|endswith: '\ntdll.dll'
    filter_normal:
        ImageLoaded|startswith:
            - 'C:\Windows\System32\'
            - 'C:\Windows\SysWOW64\'
    condition: selection and not filter_normal
falsepositives:
    - .NET runtime loading ntdll from WinSxS in specific scenarios
level: high
```

Sigma rule for detecting ETW patching (NtTraceEvent modification):

```yaml
title: Potential ETW Bypass via NtTraceEvent Patching
id: 7f2c0a83-e65b-8d3c-ab17-6b8f0d2e4a5c
status: experimental
description: >
    Detects process access to ntdll.dll with write permissions
    that may indicate patching of ETW-related functions
    (EtwEventWrite, NtTraceEvent) to blind EDR telemetry.
tags:
    - attack.defense_evasion
    - attack.t1562.001
logsource:
    category: process_access
    product: windows
detection:
    selection:
        TargetImage|endswith: '\ntdll.dll'
        GrantedAccess|contains:
            - '0x0020'  # PROCESS_VM_WRITE
            - '0x1fffff'  # PROCESS_ALL_ACCESS
    condition: selection
falsepositives:
    - Debuggers (WinDbg, Visual Studio debugger)
    - Certain anti-cheat software
level: high
```

### 8.3 MITRE ATT&CK Evaluations

The MITRE ATT&CK Evaluations assess EDR products against emulated adversary behavior. The evaluation methodology runs a multi-day attack simulation (emulating a specific threat actor's TTPs, such as Wizard Spider + Sandworm for the 2022 round, Turla for the 2023 round, and DPRK-attributed groups for 2024) against each participating EDR product. Each attack step is mapped to an ATT&CK technique and the EDR's response is categorized: None (no detection), Telemetry (the event was logged but no alert was raised), General (an alert was raised with general information), Tactic (the alert identified the ATT&CK tactic), and Technique (the alert identified the specific ATT&CK technique — the highest-fidelity detection).

Interpreting the results requires nuance. A product with high Technique-level detections has strong analytic rules but may also have a high false-positive rate in production (MITRE evaluations run in a clean lab, not a noisy enterprise). A product with high Telemetry but low Technique detections captures the raw data but lacks analytic rules to surface threats — the data is available for hunting but does not generate automated alerts. Configuration changes (detection sensitivity settings, custom rules) are not permitted during the evaluation, so results reflect the vendor's out-of-box detection capabilities, not a tuned production deployment.

---

## 9. Deception technology

### 9.1 Honey tokens

**Honey tokens** are fake credentials (API keys, passwords, tokens) planted in locations an attacker would find them: environment variables, configuration files, internal wikis, source-code repositories. Any use of the honey token triggers an alert — proving the attacker accessed the planted location and attempted to use the credential.

**AWS IAM honey access keys**: create a functional IAM user with no permissions but with CloudTrail monitoring. Generate access keys for this user and plant them in locations an attacker conducting post-exploitation reconnaissance would search: `.env` files on web servers, `~/.aws/credentials` files on developer workstations, configuration management systems, internal documentation wikis, and source code repositories (in a `config.example` file). Any `sts:GetCallerIdentity`, `s3:ListBuckets`, or any other API call using these keys generates a CloudTrail event that triggers an alarm.

```bash
# Create honey IAM user with no permissions
aws iam create-user --user-name honey-service-account-prod

# Create access keys (plant these as bait)
aws iam create-access-key --user-name honey-service-account-prod

# Create CloudWatch alarm for any API call by this user
# (via CloudTrail + EventBridge rule)
aws events put-rule --name "HoneyTokenAlert" \
    --event-pattern '{
        "source": ["aws.iam"],
        "detail": {
            "userIdentity": {
                "userName": ["honey-service-account-prod"]
            }
        }
    }'
```

**DNS canary tokens.** A hostname that exists only as a honey token — any DNS resolution of the hostname indicates compromise. Plant the hostname in configuration files, internal documents, or as a fake API endpoint. When the attacker resolves the hostname (during reconnaissance or by attempting to connect to the fake endpoint), the DNS query hits the canary DNS server, which logs the query source and triggers an alert. The `canarytokens.org` service provides hosted DNS canary tokens with email and webhook alerting: generate a token via their web interface, receive a unique `*.canarytokens.com` hostname, plant it in the target location, and receive an alert with the source IP when it is resolved.

**Web bug tokens.** Unique URLs embedded in documents (Word, PDF, HTML) that trigger an HTTP request when the document is opened. The URL contains a unique token identifying which document was opened and, depending on the document type, can capture: the opener's IP address, User-Agent, and referrer. Canarytokens supports generating Word documents (`.docx`) that make a callback when opened, PDFs with embedded URLs, and Excel files with external data connections.

**Database honey records.** Insert fake but realistic-looking records into database tables alongside real data — a fake customer record with a unique name that, if it ever appears in a search query, an API response, or a data export, indicates unauthorized database access or data exfiltration. The challenge is monitoring for the honey record's appearance: this typically requires DLP rules that flag the specific fake name, email, or identifier.

### 9.2 Honey accounts and Active Directory deception

**Honey accounts** are fake user accounts (in AD, in cloud IAM) with attractive names (`svc_backup_admin`, `sql_admin_prod`) but no real permissions. Any authentication attempt against the honey account is malicious.

**Active Directory deception** extends honey accounts to exploit the specific attack tools and techniques used against AD.

**Deceptive computer objects.** Create computer objects in AD that appear to be high-value targets (e.g., `YOURDC03`, `YOUREXCHANGE02`, `YOURCA01`) but do not correspond to real machines. Attackers running BloodHound, ADRecon, or manual LDAP queries will enumerate these objects and may attempt to authenticate to them or exploit them. Monitoring for authentication events (Kerberos TGS requests, NTLM authentication) targeting these fake computer names provides a high-confidence intrusion indicator.

**SPN honey tokens.** Create AD accounts with attractive Service Principal Names (e.g., `MSSQLSvc/sql-prod.domain.local:1433`) that would appear as high-value Kerberoasting targets. Set a strong password (preventing the attacker from cracking the TGS ticket) and monitor for TGS requests (Event ID 4769) for the honey SPN. Any Kerberoasting attempt against the honey SPN proves the attacker is conducting Kerberoasting against the domain — a technique-specific alarm that triggers before any real account is compromised.

**AdminSDHolder honey.** Create a honey account and add it to a group protected by AdminSDHolder (e.g., Domain Admins, then immediately remove it). Attackers who modify the AdminSDHolder container to inject backdoor permissions (a common persistence technique — Domain 14 Chapter 14A §3) will inadvertently apply those permissions to the honey account. Monitor the honey account's ACL for unexpected changes: any modification indicates AdminSDHolder tampering.

### 9.3 Honey services

**Canary services** are fake services (SSH servers, RDP endpoints, web applications, database listeners) deployed on the internal network. Any connection to a canary service is anomalous (no legitimate traffic should reach it) — a reliable intrusion indicator with near-zero false positives.

**SSH honeypots.** Deploy a lightweight SSH honeypot (e.g., Cowrie) on internal network segments, bound to an IP address that appears in the organization's DNS or asset inventory but is not used by any real service. Cowrie records authentication attempts (username, password), session commands (the attacker's post-login activity), and file transfers (malware uploads). The mere occurrence of an SSH connection to the honeypot IP is an alarm; the session content provides threat intelligence about the attacker's objectives and tooling.

**RDP honeypots.** Deploy a fake RDP service (e.g., YOURRDP honeypot or a locked-down Windows VM with monitoring) on a segment where RDP should not be accessed. Attackers conducting internal network scanning will discover the RDP service and attempt authentication. Monitor for: RDP connection attempts (network flow to the honeypot port 3389), NLA authentication events, and any successful logon (indicating brute-forced or sprayed credentials).

**Internal web application honeypots.** Deploy a fake internal web application (e.g., a fake admin portal at `admin.internal.example.com`) with attractive-sounding content (login page titled "Production Database Admin") that logs all requests. Any access to this application is suspicious; any authentication attempt is a high-confidence indicator.

### 9.4 Detection rules for deception triggers

The value of deception technology depends on reliable, immediate alerting when honey tokens, accounts, or services are triggered. For AD honey accounts, the detection monitors authentication events:

```yaml
title: Authentication Attempt Against Honey Account
id: 8a3d1b94-f76c-9e4d-bc28-7c9a0e3f5b6d
status: stable
description: >
    Detects any authentication attempt (successful or failed) against
    a designated honey account. Any such attempt is a confirmed indicator
    of compromise — no legitimate authentication should target this account.
tags:
    - attack.credential_access
    - attack.discovery
    - attack.t1110
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID:
            - 4624   # Successful logon
            - 4625   # Failed logon
            - 4768   # Kerberos TGT request
            - 4769   # Kerberos TGS request
        TargetUserName|contains:
            - 'svc_backup_admin'
            - 'sql_admin_prod'
            # Add all honey account names
    condition: selection
falsepositives: []   # No false positives expected by design
level: critical
```

---

## 10. Network detection

### 10.1 Zeek

**Zeek (formerly Bro)** is a network-security monitoring platform that parses network protocols and produces structured logs: `conn.log` (connection summaries: source/dest IP:port, protocol, duration, bytes), `dns.log` (DNS queries and responses), `http.log` (HTTP requests: method, URI, host, user-agent, referrer, response code), `ssl.log` (TLS handshake details: server name, cipher suite, JA3/JA4 hash, certificate chain), `x509.log` (certificate details: subject, issuer, validity, SANs), `files.log` (file transfers: MIME type, hash, size), and `notice.log` (alerts from Zeek's built-in detection scripts and custom scripts).

Zeek scripts (written in the Zeek scripting language) enable custom behavioral detections. A Zeek script for detecting DNS tunneling based on query entropy and volume:

```zeek
@load base/frameworks/notice

module DNSTunnel;

export {
    redef enum Notice::Type += {
        DNS_Tunneling_Suspected
    };

    const query_length_threshold = 50 &redef;
    const queries_per_minute_threshold = 60 &redef;
}

global dns_query_count: table[addr, string] of count &create_expire=60sec;

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
{
    local src = c$id$orig_h;
    local parts = split_string(query, /\./);
    local domain = "";
    if ( |parts| >= 2 )
        domain = parts[|parts|-2] + "." + parts[|parts|-1];

    # Check for unusually long query names (potential encoded data)
    if ( |query| > query_length_threshold )
    {
        if ( [src, domain] !in dns_query_count )
            dns_query_count[src, domain] = 0;
        ++dns_query_count[src, domain];

        if ( dns_query_count[src, domain] > queries_per_minute_threshold )
        {
            NOTICE([$note=DNS_Tunneling_Suspected,
                    $msg=fmt("High volume of long DNS queries to %s from %s (%d queries/min)",
                             domain, src, dns_query_count[src, domain]),
                    $src=src,
                    $identifier=cat(src, domain)]);
        }
    }
}
```

**C2 beaconing detection** uses Zeek's `conn.log` to identify periodic communication patterns. C2 beacons (such as Cobalt Strike's default beacon with jitter) produce network connections with characteristic timing patterns: regular intervals (e.g., every 60 seconds with 10% jitter). Detection approaches include: computing the standard deviation of inter-connection intervals to the same destination (low standard deviation indicates regular beaconing), analyzing JA3 fingerprints (the TLS client hello parameters produce a fingerprint that identifies the C2 framework — Cobalt Strike's default JA3 hash is well-known, though operators can customize it), and JARM fingerprinting (active TLS fingerprinting that identifies the server-side TLS stack — many C2 frameworks produce distinctive JARM fingerprints regardless of domain fronting or other evasion).

### 10.2 Suricata

**Suricata** is a signature-based network IDS/IPS with deep packet inspection and protocol parsing. Rules follow a structured syntax:

```
action protocol source_ip source_port -> dest_ip dest_port (rule options)
```

Suricata rule detecting Cobalt Strike default beacon HTTP profile:

```
alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"ET TROJAN Cobalt Strike Beacon Activity (GET)";
    flow:established,to_server;
    http.method; content:"GET";
    http.uri; content:"/activity";
    http.header; content:"Cookie:";
    pcre:"/Cookie:\s[a-zA-Z0-9+/]{32,}/";
    classtype:trojan-activity;
    sid:2035789;
    rev:1;
    metadata:attack_target Client_Endpoint,
        deployment Perimeter,
        mitre_tactic_id TA0011,
        mitre_technique_id T1071.001;
)
```

Suricata rule detecting DNS tunneling via long TXT queries:

```
alert dns $HOME_NET any -> any any (
    msg:"ET DNS Potential DNS Tunneling - Long TXT Query";
    dns.query; content:"."; offset:50;
    dns.query; pcre:"/^[a-zA-Z0-9+\-]{50,}\./";
    threshold:type both, track by_src, count 10, seconds 60;
    classtype:bad-unknown;
    sid:2035790;
    rev:1;
    metadata:mitre_tactic_id TA0011,
        mitre_technique_id T1071.004;
)
```

Suricata rule detecting exfiltration via HTTP POST with large body:

```
alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"CUSTOM Potential Data Exfiltration - Large HTTP POST";
    flow:established,to_server;
    http.method; content:"POST";
    http.content_len; content:!"0";
    urilen:>0;
    dsize:>500000;
    threshold:type both, track by_src, count 5, seconds 300;
    classtype:policy-violation;
    sid:9000001;
    rev:1;
)
```

The **Emerging Threats (ET)** ruleset (open-source via `rules.emergingthreats.net`) and **ET Pro** (commercial via Proofpoint) provide categories including: emerging threats (newly identified malware families), command and control (C2 traffic patterns for known RATs and frameworks), exploit kits (drive-by download infrastructure), credentials (credential theft over the wire), and policy (organizational policy violations such as TOR usage, cryptocurrency mining, P2P traffic). Update workflow: Suricata's `suricata-update` tool fetches and applies ruleset updates, handling rule-state management (enabling/disabling rules by SID, classtype, or metadata) and source management (combining multiple ruleset sources).

### 10.3 Full-packet capture with Arkime

**Arkime (formerly Moloch)** provides full-packet capture with indexed metadata and a web UI for session search and PCAP retrieval. The architecture consists of three components: the capture daemon (`capture`) reads packets from the network interface, parses protocol headers, indexes session metadata into Elasticsearch/OpenSearch, and writes raw packets to PCAP files on local storage; the viewer (`viewer`) provides a web UI for searching sessions by metadata fields (IP, port, protocol, country, bytes transferred, tags, JA3 hash, TLS server name), displaying session details, and reassembling and exporting PCAP files for specific sessions; and the Elasticsearch/OpenSearch cluster stores the session metadata index.

Arkime's value for security operations is retrospective analysis: when a threat intelligence report identifies a new C2 domain or IP address, analysts can search Arkime for any historical connections to that indicator across the full retention period. When an incident investigation identifies a compromised host, analysts can retrieve all network sessions for that host, reconstruct the attacker's network activity, and identify exfiltrated data, additional C2 channels, or lateral-movement connections — capabilities that log-only monitoring (Zeek, firewall logs) cannot fully replicate because they lack the raw packet payload.

Storage considerations: at 1 Gbps average throughput, full-packet capture generates approximately 10 TB/day; at 10 Gbps, approximately 100 TB/day. Organizations typically: capture at key network boundaries (internet egress, DMZ, inter-segment gateways), apply BPF filters to exclude high-volume, low-value traffic (streaming media, CDN downloads, OS update traffic), implement tiered storage (recent captures on fast NVMe storage for immediate access, older captures on high-density SATA or object storage), and set retention periods based on compliance requirements and storage budget (30-90 days of full PCAP is common; some organizations retain metadata indefinitely with 7-day full PCAP).

### 10.4 Network detection for specific attack patterns

**C2 beaconing detection.** Beyond Zeek scripting, network-level beaconing detection combines multiple signals. **JA3/JA3S fingerprinting** hashes the TLS client hello (JA3) and server hello (JA3S) parameters to create a fingerprint that identifies the TLS implementation. Known C2 frameworks have documented JA3/JA3S signatures, but sophisticated operators customize them. **JARM** (active TLS fingerprinting by John Althouse/Salesforce) sends multiple crafted TLS client hellos to a server and hashes the server's responses, producing a 62-character fingerprint that identifies the server's TLS stack. JARM fingerprints are harder to evade because they characterize the server's implementation rather than a single hello message. **Timing analysis** computes inter-connection intervals: regular beacons produce low-jitter intervals that stand out against the irregular timing of human-driven browsing. Statistical methods (standard deviation, Fourier transform, entropy analysis) can detect beaconing even when the beacon uses jitter to randomize timing.

**DNS tunneling detection.** C2 tools such as iodine, dnscat2, and Cobalt Strike's DNS beacon encode data in DNS query names and TXT records. Detection signals: unusually long query names (base32/base64-encoded data produces 50-200 character labels), high query volume to a single domain (hundreds or thousands of queries per minute versus the normal ~1/minute for legitimate domains), high entropy in query name labels (random-looking strings versus the dictionary-word structure of legitimate hostnames), and unusual query types (TXT, NULL, CNAME, or MX records used for data return channels when the legitimate use case only warrants A/AAAA records).

**Data exfiltration detection.** Network-based exfiltration detection monitors for: unusual outbound data volume (a host that normally transfers 100 MB/day suddenly transfers 10 GB), connections to newly registered domains or domains with no established browsing history, large HTTP POST or PUT requests to cloud storage APIs (S3, Azure Blob, GCS), ICMP tunneling (unusually large ICMP payloads carrying encoded data), and encrypted channel anomalies (long-duration TLS sessions with sustained high throughput to a single destination, or TLS connections to IP addresses without valid certificate chains).

---

## 11A. Threat modeling tools

### 11A.1 STRIDE with Microsoft Threat Modeling Tool

**Microsoft Threat Modeling Tool** (free, Windows) — visual DFD editor with automated STRIDE-per-element threat generation. Workflow: draw DFD → **View > Analysis View** (auto-generates threats per element/boundary) → set Status/Priority per threat → **Reports > Full Report** (HTML threat register per Section 1.6). Limitations: mechanical generation only; threat intelligence, CVSS, and ATT&CK mapping are manual enrichments.

### 11A.2 Threagile (code-based threat model)

**Threagile** (open-source, Go binary) defines the architecture and threat model in YAML, enabling version-controlled threat models that evolve with the codebase.

```yaml
# threagile-model.yaml — minimal e-commerce example (abbreviated)
threagile_version: 1.0.0
title: E-Commerce Platform Threat Model
date: 2026-05-09
business_criticality: critical

data_assets:
  customer-pii:
    id: customer-pii
    description: Customer PII (name, email, address, phone)
    usage: business
    confidentiality: confidential
    integrity: critical
    availability: operational

technical_assets:
  web-frontend:
    id: web-frontend
    description: Next.js SSR frontend
    type: process
    technologies: [web-application]
    internet: true
    machine: container
    data_assets_processed: [customer-pii]
    communication_links:
      api-backend-call:
        target: api-backend
        protocol: https
        authentication: token
  # api-backend and postgres-db follow the same structure
  # (omitted for brevity — full model in Git)

trust_boundaries:
  internet-boundary:
    id: internet-boundary
    type: network-cloud-security-group
    technical_assets_inside: [web-frontend]
```

```bash
docker run --rm -v "$(pwd)":/app/work threagile/threagile \
    -model /app/work/threagile-model.yaml -output /app/work/output
# Outputs: report.pdf, risks.json, data-flow-diagram.png
```

Threagile auto-generates STRIDE-mapped risks based on technology type, data sensitivity, encryption, internet exposure, and trust boundary crossings. The `risks.json` is machine-parseable for CI integration (fail the build if unmitigated critical risks exist).

### 11A.3 Attack tree construction

**ADTool** (Attack-Defense Tree Tool, University of Luxembourg) provides a GUI for constructing attack-defense trees with AND/OR/SAND (sequential AND) operators and computable attributes. Exports XML for programmatic analysis and LaTeX for documentation. Attribute domains: boolean, probability, cost, and skill. Bottom-up computation propagates leaf-node attributes to the root (OR → minimum cost path; AND → costs summed). See Section 1.2.1 for a fully worked probability analysis.

**Attack tree in text notation (Schneier notation):**

```
Goal: Exfiltrate customer database
  OR
  ├── 1. SQL injection via web frontend [cost=$0, skill=medium, p=0.224]
  │     AND
  │     ├── 1.1 Identify injectable parameter [p=0.7]
  │     ├── 1.2 Bypass WAF rules [p=0.4]
  │     └── 1.3 Extract data via UNION/blind SQLi [p=0.8]
  ├── 2. Compromise admin credentials [cost=$150, skill=low, p=0.08]
  └── 3. Exploit exposed S3 backup [cost=$0, skill=low, p=0.05]
        AND: discover bucket (p=0.2) × publicly readable (p=0.25)
```

### 11A.4 DREAD scoring vs CVSS comparison

**DREAD** (Microsoft, deprecated but still referenced in legacy threat models) scores five factors on a 1–10 scale:

| Factor | Definition | Scale |
|---|---|---|
| **D**amage potential | Impact if exploited | 1=minimal → 10=full system compromise |
| **R**eproducibility | Ease of reproducing the attack | 1=near-impossible → 10=every time |
| **E**xploitability | Effort to launch the attack | 1=requires nation-state → 10=script kiddie |
| **A**ffected users | Proportion of users impacted | 1=single user → 10=all users |
| **D**iscoverability | Ease of finding the vulnerability | 1=requires source access → 10=visible in URL |

DREAD risk = (D + R + E + A + D) / 5. Score ranges: 1–3 low, 4–6 medium, 7–10 high.

**CVSS 3.1** provides three metric groups: Base (AV/AC/PR/UI/S/CIA), Temporal (exploit maturity, remediation, report confidence), Environmental (modified base for org context).

| Aspect | DREAD | CVSS 3.1 |
|---|---|---|
| Standardization | Informal, subjective | FIRST-standardized, NVD-used |
| Scoring range | 1–10 (averaged) | 0.0–10.0 (computed via formula) |
| Subjectivity | High (each factor is manually rated) | Moderate (structured choices, but scope/impact require judgment) |
| Industry adoption | Deprecated by Microsoft (2008) | Universal (CVE entries, NVD, vendor advisories) |
| Temporal/environmental | Not included | Explicit temporal and environmental metric groups |
| Recommended use | Legacy threat model triage only | All vulnerability scoring, compliance reporting |

Recommendation: use CVSS 3.1 (or 4.0 when tooling matures) for all new threat models. Map legacy DREAD scores to CVSS qualitative ranges (DREAD 7–10 ≈ CVSS High/Critical) during migration.

---

## 11B. Detection engineering deep dive

### 11B.1 Sigma rules — five additional detections

Rules below target sub-techniques not covered in Sections 6.3–6.3.4 or 8.2.

```yaml
# Rule 1: Brute force (T1110.003)
title: Brute Force - Multiple Failed Logon Attempts
description: High volume of failed logons (4625) indicating password spraying or brute force.
tags: [attack.credential_access, attack.t1110.003]
logsource: {product: windows, service: security}
detection:
    selection: {EventID: 4625, LogonType: [3, 10]}
    timeframe: 5m
    condition: selection | count(TargetUserName) by IpAddress > 15
falsepositives: [Misconfigured service accounts, vulnerability scanners]
level: high
---
# Rule 2: WMI lateral movement (T1047)
title: Remote Process Creation via WMI
description: WmiPrvSE.exe spawning suspicious children indicating WMI lateral movement.
tags: [attack.lateral_movement, attack.t1047]
logsource: {category: process_creation, product: windows}
detection:
    selection:
        ParentImage|endswith: '\WmiPrvSE.exe'
        Image|endswith: ['\cmd.exe', '\powershell.exe', '\pwsh.exe', '\mshta.exe', '\rundll32.exe']
    condition: selection
falsepositives: [SCCM/MECM WMI execution, WMI monitoring agents]
level: high
---
# Rule 3: SAM registry export (T1003.002)
title: SAM Registry Hive Export via reg.exe
description: reg.exe saving SAM/SYSTEM/SECURITY hives for offline hash extraction.
tags: [attack.credential_access, attack.t1003.002]
logsource: {category: process_creation, product: windows}
detection:
    selection:
        Image|endswith: '\reg.exe'
        CommandLine|contains|all: ['save']
        CommandLine|contains: ['hklm\sam', 'hklm\system', 'hklm\security']
    condition: selection
falsepositives: [System backup scripts exporting registry hives]
level: critical
---
# Rule 4: Registry Run key persistence (T1547.001)
title: Persistence via Registry Run Key Modification
description: Run/RunOnce registry key modification with suspicious values indicating persistence.
tags: [attack.persistence, attack.t1547.001]
logsource: {category: registry_set, product: windows}
detection:
    selection:
        TargetObject|contains: ['\CurrentVersion\Run\', '\CurrentVersion\RunOnce\']
        Details|contains: ['powershell', 'cmd.exe', 'mshta', 'wscript', '\AppData\', '\Temp\']
    filter_legitimate:
        Image|startswith: ['C:\Program Files\', 'C:\Program Files (x86)\', 'C:\Windows\System32\']
    condition: selection and not filter_legitimate
falsepositives: [Legitimate software installers]
level: high
---
# Rule 5: C2 beaconing (T1071.001)
title: Potential C2 Beaconing - Regular Outbound Connections
description: Regular outbound connections to same destination indicating C2 beaconing (Sysmon Event 3).
tags: [attack.command_and_control, attack.t1071.001]
logsource: {category: network_connection, product: windows}
detection:
    selection: {Initiated: 'true', DestinationIsIpv6: 'false'}
    filter_internal: {DestinationIp|cidr: ['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']}
    filter_browsers: {Image|endswith: ['\chrome.exe', '\firefox.exe', '\msedge.exe']}
    timeframe: 1h
    condition: selection and not filter_internal and not filter_browsers | count() by Image, DestinationIp, DestinationPort > 20
falsepositives: [Update agents, monitoring agents with fixed schedules]
level: medium
```

### 11B.2 YARA rules — five malware/artifact detections

```yara
rule CobaltStrike_Beacon_Reflective {
    meta: description = "Cobalt Strike beacon reflective DLL loader" severity = "critical"
    strings:
        $reflective = { 4D 5A 41 52 53 48 }        // MZARSH modified MZ
        $config  = "%s as %s\\%s: %d" ascii
        $pipe    = "\\\\.\\pipe\\msagent_" ascii
        $get     = "/activity" ascii
        $post    = "/submit.php" ascii
        $xor     = { 8A 04 ?? 34 ?? 88 04 ?? 4? FF C? }
    condition:
        uint16(0) == 0x5A4D and filesize < 1MB and
        (($reflective and 1 of ($config, $pipe)) or (3 of ($get, $post, $pipe, $config, $xor)))
}

rule Mimikatz_Strings {
    meta: description = "Mimikatz string artifacts" severity = "critical"
    strings:
        $s1 = "mimikatz" ascii wide nocase  $s2 = "gentilkiwi" ascii wide
        $s3 = "sekurlsa::" ascii wide       $s4 = "lsadump::dcsync" ascii wide
        $s5 = "privilege::debug" ascii wide
        $fn1 = "kuhl_m_sekurlsa" ascii      $fn2 = "kuhl_m_lsadump" ascii
    condition:
        (uint16(0) == 0x5A4D and 3 of ($s*)) or (2 of ($fn*)) or (4 of ($s*))
}

rule Webshell_Generic_PHP_ASP {
    meta: description = "PHP/ASP webshell patterns" severity = "high"
    strings:
        $php_eval   = /eval\s*\(\s*(base64_decode|gzinflate|str_rot13)\s*\(/ nocase
        $php_system = /\b(system|passthru|shell_exec|proc_open)\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $php_assert = /assert\s*\(\s*\$_(GET|POST|REQUEST)/ nocase
        $asp_exec   = "WScript.Shell" ascii nocase
        $asp_fso    = "Scripting.FileSystemObject" ascii nocase
        $aspx_proc  = "System.Diagnostics.Process" ascii nocase
        $aspx_comp  = "CompileAssemblyFromSource" ascii nocase
    condition:
        filesize < 500KB and ((2 of ($php*)) or (2 of ($asp*)) or ($aspx_proc and $aspx_comp))
}

rule Packed_PE_Suspicious {
    meta: description = "PE files with packing indicators" severity = "medium"
    strings:
        $upx0 = "UPX0" ascii  $upx1 = "UPX1" ascii
        $themida = ".themida" ascii  $vmp = ".vmp0" ascii
        $s1 = ".packed" ascii  $s2 = ".crypted" ascii
    condition:
        uint16(0) == 0x5A4D and filesize < 10MB and
        ((1 of ($upx*, $themida, $vmp)) or (1 of ($s*) and pe.number_of_sections < 4) or
         (math.entropy(pe.sections[0].raw_data_offset, pe.sections[0].raw_data_size) > 7.0 and
          pe.imports("kernel32.dll", "VirtualAlloc") and pe.imports("kernel32.dll", "VirtualProtect")))
}

rule Suspicious_PowerShell_Script {
    meta: description = "PowerShell obfuscation or offensive tooling" severity = "high"
    strings:
        $enc1 = "-EncodedCommand" nocase  $enc2 = "[Convert]::FromBase64String" nocase
        $obf1 = "Invoke-Obfuscation" nocase  $obf2 = /\-join\s*\(\s*['"][^'"]{0,5}['"]\s*\+/ nocase
        $off1 = "Invoke-Mimikatz" nocase  $off2 = "Invoke-ReflectivePEInjection" nocase
        $off3 = "Invoke-Kerberoast" nocase  $off4 = "PowerView" nocase
        $amsi1 = "AmsiScanBuffer" nocase  $amsi2 = "amsi.dll" nocase
    condition:
        filesize < 5MB and ((1 of ($off*)) or (2 of ($amsi*)) or (2 of ($enc*) and 2 of ($obf*)))
}
```

### 11B.3 Suricata rules — three additional detections

```
# Rule 1: DNS tunneling — high-entropy subdomain labels (differs from §10.2 TXT-query rule)
alert dns $HOME_NET any -> any any (msg:"CUSTOM DNS Tunneling - High Entropy Subdomain Labels"; flow:to_server; dns.query; pcre:"/^[a-z0-9]{30,}\.[a-z0-9]{10,}\./i"; threshold:type both, track by_src, count 30, seconds 60; classtype:bad-unknown; sid:9000010; rev:1; metadata:mitre_technique_id T1071.004;)

# Rule 2: TLS C2 — known JA3 hashes (72a589...=CS4.x, a0e9f5...=Meterpreter HTTPS)
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"CUSTOM TLS C2 - Known Malicious JA3"; flow:established,to_server; ja3.hash; content:"72a589da586844d7f0818ce684948eea"; ja3.hash; content:"a0e9f5d64349fb13191bc781f81f42e1"; classtype:trojan-activity; sid:9000011; rev:1; metadata:mitre_technique_id T1573.002;)

# Rule 3: HTTP beacon timing — 30+ GETs to short random URIs in 30m
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"CUSTOM HTTP Beacon - Regular Callbacks"; flow:established,to_server; http.method; content:"GET"; http.uri; pcre:"/^\/[a-zA-Z0-9_\-]{4,20}$/"; flowbits:set,beacon_candidate; threshold:type both, track by_src, count 30, seconds 1800; classtype:trojan-activity; sid:9000012; rev:1; metadata:mitre_technique_id T1071.001;)
```

Maintain JA3 hash lists from Abuse.ch JA3 Fingerprint Database.

### 11B.4 Sigma rule lifecycle

1. **Creation.** Triggered by: threat intel, incident post-mortem, ATT&CK coverage gap, or red team findings. Author writes Sigma YAML with metadata, test cases, and FP documentation.
2. **Testing.** Validate against known-bad (replay attack logs), known-good (production log burn-in), syntax (`sigma-cli check`), and cross-platform compilation (`sigma-cli convert` to all target SIEMs).
3. **Deployment.** After peer review + CI approval, deploy via Detection-as-Code pipeline (Section 6.2). Initial 2-week burn-in in monitoring-only mode.
4. **Tuning.** During burn-in, classify every alert. Add filter clauses, adjust thresholds, narrow field conditions. Each tuning change = Git commit with justification.
5. **Retirement.** When technique becomes irrelevant, data source is decommissioned, or rule is superseded. Move to `archive/` in Git (preserve institutional knowledge).

### 11B.5 False positive management methodology

**Classification:** True Positive (TP), Benign True Positive (BTP — authorized activity matching the detection pattern), False Positive (FP — unrelated benign activity).

**FP root causes:** (1) broad field match overlapping with legitimate tools, (2) missing context filter, (3) environmental noise from monitoring/automation agents, (4) threshold miscalibration.

**Resolution priority:** >30% FP rate → immediately tune or pause. 10–30% → tune within one sprint. <10% → tune during maintenance cycles.

**FP tracking.** Maintain a false-positive register per rule (in the rule's YAML `falsepositives` field and in a companion `tuning_log.md` in the detection repository) documenting: the FP source (which process/user/host), the FP root cause, the tuning action taken, and the date. This register prevents re-introducing previously resolved FPs during rule updates and provides onboarding material for new analysts.

---

## 11C. SIEM query examples

### 11C.1 Splunk SPL — five detection queries

Queries below target patterns not covered in Section 7.1.

**Failed logon threshold (brute force / password spraying):**

```spl
index=wineventlog EventCode=4625 Logon_Type IN (3, 10)
| bin _time span=5m
| stats count dc(TargetUserName) as unique_accounts values(TargetUserName) as targeted_accounts
    by src_ip _time
| where count > 15 OR unique_accounts > 5
| lookup threat_intel_ip ip AS src_ip OUTPUT threat_category
| table _time src_ip count unique_accounts targeted_accounts threat_category
```

**Process injection detection (CreateRemoteThread):**

```spl
index=sysmon EventCode=8
    NOT SourceImage IN ("C:\\Windows\\System32\\csrss.exe","C:\\Windows\\System32\\lsass.exe","C:\\Windows\\System32\\services.exe")
| where SourceImage!=TargetImage
| stats count values(TargetImage) as targets values(StartFunction) as functions by SourceImage Computer
| lookup known_injectors process AS SourceImage OUTPUT legitimate
| where isnull(legitimate)
| table Computer SourceImage targets functions count
```

**Lateral movement via pass-the-hash (NTLM type 9 logon):**

```spl
index=wineventlog EventCode=4624 Logon_Type=9 AuthenticationPackageName="Negotiate"
| eval is_pth = if(LogonProcessName="seclogo" AND ImpersonationLevel="%%1833", "true", "false")
| where is_pth="true"
| stats count values(TargetServerName) as targets
    by SubjectUserName WorkstationName src_ip
| where count > 0
| table SubjectUserName WorkstationName src_ip targets count
```

**Data exfiltration — outbound byte volume anomaly:**

```spl
index=firewall action=allowed direction=outbound
| bin _time span=1h
| stats sum(bytes_out) as total_bytes by src_ip _time
| eventstats avg(total_bytes) as avg_bytes stdev(total_bytes) as stdev_bytes by src_ip
| where total_bytes > (avg_bytes + 4*stdev_bytes) AND total_bytes > 1073741824
| eval total_gb=round(total_bytes/1073741824,2), avg_gb=round(avg_bytes/1073741824,2)
| table _time src_ip total_gb avg_gb
```

**Privilege escalation — service creation with SYSTEM context:**

```spl
index=wineventlog EventCode=7045
| where ServiceType="user mode service" OR ServiceType="kernel driver"
| regex ServiceFileName="(cmd\.exe|powershell|mshta|regsvr32|\\\\AppData|\\\\Temp|\\\\ProgramData)"
| eval runs_as_system = if(match(ServiceStartType, "auto"), "likely", "manual")
| stats count values(ServiceFileName) as svc_paths values(ServiceName) as svc_names
    by Computer
| where count > 0
| table Computer svc_names svc_paths runs_as_system count
```

### 11C.2 Elastic KQL — three detection queries

**Suspicious parent-child process relationship:**

```
process.parent.name:("winword.exe" or "excel.exe" or "powerpnt.exe" or "outlook.exe") and process.name:("cmd.exe" or "powershell.exe" or "pwsh.exe" or "mshta.exe" or "wscript.exe" or "cscript.exe" or "certutil.exe")
```

**Service creation with suspicious binary path:**

```
event.code:"7045" and winlog.event_data.ImagePath:(*\\Temp\\* or *\\AppData\\* or *cmd* or *powershell* or *\\ProgramData\\*)
```

**Registry persistence in Run keys:**

```
event.code:"13" and registry.path:(*\\CurrentVersion\\Run\\* or *\\CurrentVersion\\RunOnce\\*) and process.name:(not ("msiexec.exe" or "setup.exe" or "update.exe"))
```

### 11C.3 Microsoft Sentinel KQL — three detection queries

**Impossible travel (sign-in from geographically distant locations):**

```kql
let time_threshold = 60m; let distance_km = 500;
SigninLogs | where ResultType == 0
| extend Lat = todouble(LocationDetails.geoCoordinates.latitude),
         Lon = todouble(LocationDetails.geoCoordinates.longitude)
| sort by UserPrincipalName asc, TimeGenerated asc
| extend PrevLat=prev(Lat,1), PrevLon=prev(Lon,1), PrevTime=prev(TimeGenerated,1), PrevUser=prev(UserPrincipalName,1)
| where UserPrincipalName == PrevUser
| extend TimeDiff=datetime_diff('minute',TimeGenerated,PrevTime), Dist=geo_distance_2points(Lon,Lat,PrevLon,PrevLat)/1000
| where TimeDiff > 0 and TimeDiff < time_threshold and Dist > distance_km
| project TimeGenerated, UserPrincipalName, Dist, TimeDiff
```

**Mass file download from SharePoint (potential exfiltration):**

```kql
OfficeActivity
| where Operation in ("FileDownloaded", "FileSyncDownloadedFull")
| where TimeGenerated > ago(1h)
| summarize DownloadCount = count(), Files = make_set(OfficeObjectId, 20)
    by UserId, ClientIP
| where DownloadCount > 50
| project TimeGenerated = now(), UserId, ClientIP, DownloadCount, Files
```

**Suspicious Azure AD application consent (OAuth phishing):**

```kql
AuditLogs | where OperationName == "Consent to application"
| extend App=tostring(TargetResources[0].displayName), User=tostring(InitiatedBy.user.userPrincipalName),
         Perms=tostring(TargetResources[0].modifiedProperties)
| where Perms has_any ("Mail.Read","Files.ReadWrite.All","User.ReadBasic.All","offline_access")
| project TimeGenerated, User, App, Perms
```

### 11C.4 Query optimization techniques

| Platform | Technique | Rationale |
|---|---|---|
| Splunk | Filter early (`index=`, `sourcetype=`) before `stats`/`eval` | Reduces dataset before expensive transforms |
| Splunk | `tstats` for indexed fields | Orders of magnitude faster than `stats` on large datasets |
| Splunk | Avoid leading wildcards (`*\\lsass.exe`); use `IN (...)` | Leading wildcards force full-index scan |
| Splunk | Summary indexing for dashboards | Pre-computes expensive queries on schedule |
| Elastic | Prefer EQL sequences over KQL for multi-event correlation | Engine-optimized sequence operator |
| Elastic | ILM hot-tier = detection window (24–72h) | Keeps alerting-critical data on fast storage |
| Elastic | Detection rules API for bulk management | Avoids manual Kibana UI; enables CI/CD |
| Sentinel | `materialized_view` for frequent aggregations | Avoids recomputing at query time |
| Sentinel | `let` for thresholds; `hint.strategy=shuffle` for high cardinality | Readability + partition optimization |

---

## 11D. Honeypot deployment

### 11D.1 Cowrie SSH honeypot (Docker)

```bash
docker run -d --name cowrie -p 2222:2222 \
    -v cowrie-data:/cowrie/var -v cowrie-config:/cowrie/etc cowrie/cowrie:latest
iptables -t nat -A PREROUTING -p tcp --dport 22 -j REDIRECT --to-port 2222
# Logs: /cowrie/var/log/cowrie/cowrie.json | Downloads: /cowrie/var/lib/cowrie/downloads/
```

Key `cowrie.json` fields: `cowrie.login.success`/`failed` (credentials), `cowrie.command.input` (post-login commands), `cowrie.session.file_download` (malware captures with hashes), `src_ip` (attacker source). Forward via Filebeat or Splunk UF to SIEM for deception alert correlation.

### 11D.2 HoneyDB HTTP honeypot

**HoneyDB** (agent-based) deploys lightweight protocol emulators reporting to the HoneyDB API for threat intelligence aggregation.

```bash
pip install honeydb-agent
# Configure ~/.honeydb/agent.conf with api_id, api_key, and service ports (http=8080, ftp=2121, etc.)
honeydb-agent --config ~/.honeydb/agent.conf
```

### 11D.3 Canary tokens — deployment script

```bash
#!/usr/bin/env bash
# canary_deploy.sh — canarytokens.org API (requires curl, jq)
API="https://canarytokens.org/generate"; EMAIL="soc-alerts@example.com"

# DNS token
curl -s -X POST "$API" -d "type=dns&email=$EMAIL&memo=CANARY-dns" | jq -r '.Hostname'
# HTTP web bug
curl -s -X POST "$API" -d "type=web_image&email=$EMAIL&memo=CANARY-http" | jq -r '.Url'
# MS Word document token
curl -s -X POST "$API" -d "type=doc-msword&email=$EMAIL&memo=CANARY-doc" -o canary.docx
# AWS API key token
curl -s -X POST "$API" -d "type=aws-keys&email=$EMAIL&memo=CANARY-aws" | jq '.aws_access_key_id,.aws_secret_access_key'
```

Token types and placement strategy:

| Token Type | Placement | Trigger Condition |
|---|---|---|
| DNS | Server config files, internal docs | Any DNS resolution of the hostname |
| HTTP (web bug) | Internal wiki pages, HTML docs | Image/URL loaded (captures IP, User-Agent) |
| MS Word/Excel | File shares, SharePoint, email | Document opened (callback on open) |
| AWS keys | `.env` files, `~/.aws/credentials`, source repos | Any AWS API call using the key (CloudTrail alert) |
| Cloned website | Internal portals | Credential submission to cloned login page |

### 11D.4 OpenCanary multi-protocol honeypot

```bash
pip install opencanary
opencanaryd --copyconfig   # generates ~/.opencanary.conf
# Enable services: ftp(21), http(80), ssh(22), smb(445), mysql(3306), rdp(3389), mssql(1433)
# Configure syslog alerting to SIEM in the logger section
opencanaryd --start
```

Deploy one instance per network segment on an unused IP that appears in the asset inventory — multi-protocol deception from a single binary (same principle as Section 9.3).

### 11D.5 Active Directory deception objects with monitoring

**Honey user accounts** (expand on Section 9.2 with monitoring automation):

```powershell
# Honey user with Kerberoasting bait SPN
New-ADUser -Name "svc_sql_backup" -SamAccountName "svc_sql_backup" `
    -AccountPassword (ConvertTo-SecureString "P@ssw0rdH0n3y!2026xK9mZ" -AsPlainText -Force) `
    -Enabled $true -PasswordNeverExpires $true -Path "OU=ServiceAccounts,DC=corp,DC=example,DC=com"
Set-ADUser "svc_sql_backup" -ServicePrincipalNames @{Add="MSSQLSvc/sql-backup.corp.example.com:1433"}
# Honey group + computer object
New-ADGroup -Name "Tier0-Admins-Legacy" -GroupScope Global -Path "OU=AdminGroups,DC=corp,DC=example,DC=com"
New-ADComputer -Name "YOURFILESVR03" -Path "OU=Servers,DC=corp,DC=example,DC=com" -Enabled $true
```

**Monitoring:** alert on Event ID 4769 (TGS) matching honey SPN, 4624/4625 targeting honey user, and 4662 (Directory Service Access) on honey computer object.

---

## 11E. TPM 2.0 commands

### 11E.1 Key operations (sign and verify)

Sealing, unsealing, primary key creation, and attestation are covered in Sections 4.2–4.3. The following demonstrates signing and verification — operations used for code signing, document integrity, and custom attestation workflows.

```bash
# Create a signing key under the storage hierarchy
tpm2_createprimary -C o -g sha256 -G rsa2048 -c primary.ctx
tpm2_create -C primary.ctx -G rsa2048:rsassa-sha256 -u sign.pub -r sign.priv -a "sign|fixedtpm|fixedparent|sensitivedataorigin"
tpm2_load -C primary.ctx -u sign.pub -r sign.priv -c sign.ctx

# Sign a file
sha256sum firmware.bin | awk '{print $1}' | xxd -r -p > firmware.digest
tpm2_sign -c sign.ctx -g sha256 -o firmware.sig firmware.digest

# Verify the signature
tpm2_verifysignature -c sign.ctx -g sha256 -m firmware.digest -s firmware.sig
# Exit code 0 = valid signature
```

### 11E.2 PCR reading

```bash
tpm2_pcrread sha256              # all SHA-256 PCRs
tpm2_pcrread sha256:0,4,7        # firmware + boot manager + secure boot policy
tpm2_pcrread sha1:0,4,7          # SHA-1 bank (legacy)
```

### 11E.3 Sealed secret with PCR policy

Section 4.2 covers basic sealing. **Compound policy** adds an authorization value (password) alongside PCR binding:

```bash
# Compound policy: PCR 0+7 AND password
tpm2_startauthsession -S session.ctx
tpm2_policypcr -S session.ctx -l sha256:0,7
tpm2_policypassword -S session.ctx
tpm2_policygetdigest -S session.ctx -o compound.policy
tpm2_flushcontext session.ctx
# Seal
tpm2_create -C primary.ctx -g sha256 -u seal.pub -r seal.priv -L compound.policy -i secret.dat -p "pin"
# Unseal (requires correct PCRs AND password)
tpm2_load -C primary.ctx -u seal.pub -r seal.priv -c seal.ctx
tpm2_startauthsession -S session.ctx --policy-session
tpm2_policypcr -S session.ctx -l sha256:0,7 && tpm2_policypassword -S session.ctx
tpm2_unseal -c seal.ctx -p session:session.ctx+"pin" -o unsealed.dat
```

### 11E.4 Remote attestation workflow

Attestee-side quote generation: see Section 4.3. Verifier-side validation:

```bash
NONCE=$(openssl rand -hex 16)
# Attestee runs: tpm2_quote -c ak.ctx -l sha256:0,1,2,3,4,7 -q "$NONCE" -m quote.msg -s quote.sig -o pcrs.out
tpm2_checkquote -u ak.pub -m quote.msg -s quote.sig -f pcrs.out -q "$NONCE"
diff <(tpm2_pcrread sha256:0,1,2,3,4,7 -o - | xxd) golden_pcrs.hex
```

### 11E.5 IMA + TPM integration

**IMA** extends measured boot into runtime. Every executed file (binaries, libraries, kernel modules) is measured into PCR 10.

```bash
cat /sys/kernel/security/ima/ascii_runtime_measurements | head -5
tpm2_pcrread sha256:10            # IMA aggregate PCR
evmctl ima_measurement /sys/kernel/security/ima/binary_runtime_measurements

# Enforce mode: kernel cmdline ima_policy=tcb ima_appraise=enforce
# Sign a file for IMA appraisal
evmctl ima_sign --key /etc/keys/privkey_ima.pem /usr/bin/example_binary
# Writes security.ima xattr containing the RSA/EC signature over the file digest
```

A remote verifier reconstructs PCR 10 from the event log and compares against the TPM quote — detecting tampering with files or the event log itself.

---

## 11F. Secure Boot verification

### 11F.1 Linux verification

```bash
mokutil --sb-state                          # SecureBoot enabled / disabled
sbverify --cert /path/to/db-cert.pem /boot/efi/EFI/ubuntu/shimx64.efi
pesign -S -i /boot/efi/EFI/ubuntu/grubx64.efi   # list embedded signatures
efivar -l | grep -i secureboot                    # UEFI variable names
efivar -d -n 8be4df61-93ca-11d2-aa0d-00e098032b8c-SecureBoot  # 01=on 00=off
mokutil --list-enrolled                     # enrolled MOK keys
mokutil --db                                # UEFI db (allowlist)
mokutil --dbx                               # UEFI dbx (denylist)
```

### 11F.2 Measured boot event log analysis

```bash
tpm2_eventlog /sys/kernel/security/tpm0/binary_bios_measurements
# Per-PCR records: PCRIndex, EventType (EV_S_CRTM_VERSION, EV_EFI_BOOT_SERVICES_APPLICATION, etc.), Digest

# Filter Secure Boot policy events (PCR 7)
tpm2_eventlog /sys/kernel/security/tpm0/binary_bios_measurements | grep -A5 "PCRIndex: 7"
```

### 11F.3 Windows verification

```powershell
Confirm-SecureBootUEFI                    # True / False
bcdedit /enum {current}                   # boot path, device partition
bcdedit /enum {bootmgr}                   # isolatedcontext = HVCI active
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard
# VirtualizationBasedSecurityStatus: 2 (Running), CodeIntegrityPolicyEnforcementStatus: 2 (Enforced)
Get-SecureBootPolicy
```

---

## 11G. CVE reference table

| CVE | Component | CVSS 3.1 | Description | Impact | Remediation |
|---|---|---|---|---|---|
| CVE-2023-1017 | TPM 2.0 (reference impl.) | 7.8 High | Out-of-bounds write in CryptParameterDecryption | Arbitrary code execution in TPM context; sealed secrets at risk | Update TPM firmware; vendor-specific patches |
| CVE-2023-1018 | TPM 2.0 (reference impl.) | 5.5 Medium | Out-of-bounds read in CryptParameterDecryption | Information disclosure from TPM-protected memory | Update TPM firmware; vendor-specific patches |
| CVE-2020-10713 | GRUB2 (BootHole) | 8.2 High | Buffer overflow in GRUB2 config parser | Secure Boot bypass via crafted grub.cfg; arbitrary code at boot | Patch GRUB2 + update dbx + re-sign shim/kernel |
| CVE-2023-24932 | Windows Boot Manager (BlackLotus) | 6.7 Medium | Secure Boot bypass via signed-but-vulnerable bootmgr | UEFI bootkit; HVCI/BitLocker/Defender disabled; survives reinstall | Apply KB5025885; dbx revocation of old bootmgr hash |
| CVE-2022-21894 | Windows Boot Manager | 4.4 Medium | Secure Boot bypass (prerequisite for BlackLotus) | Boot-time code execution below OS security boundary | dbx update revoking vulnerable bootmgr versions |
| CVE-2024-8105 | UEFI (PKfail) | 8.8 High | Test Platform Keys ("DO NOT SHIP") in production firmware | Entire Secure Boot chain untrustworthy on affected devices | OEM firmware update replacing test PK with production PK |
| CVE-2020-0551 | Intel SGX (LVI) | 5.6 Medium | Load Value Injection — speculative execution attack on enclaves | Enclave secret leakage via injected micro-architectural values | Microcode update + SDK recompilation with LVI mitigations |
| CVE-2022-21233 | Intel (ÆPIC Leak) | 6.0 Medium | Architecturally uninitialized APIC MMIO read leaks SGX enclave data | Enclave secrets (attestation keys, sealed data) disclosed | Microcode update; Intel SGX SDK patch |
| CVE-2021-26708 | Linux kernel (AF_VSOCK) | 7.0 High | Race condition in vsock; exploitable from confidential VM guest | Guest-to-host escape undermining SEV/TDX isolation | Kernel update (5.11+); backported patches |
| CVE-2023-20569 | AMD (Inception/SRSO) | 5.6 Medium | Speculative Return Stack Overflow affecting SEV-SNP guests | Guest data leakage via transient execution in host context | AMD microcode update + kernel mitigations |
| CVE-2023-46747 | F5 BIG-IP (Splunk forwarder) | 9.8 Critical | Authentication bypass in BIG-IP Traffic Management UI | Remote unauthenticated code execution on SIEM log forwarder | Patch to fixed version; restrict mgmt interface access |
| CVE-2024-23897 | Jenkins (SIEM infra co-deployed) | 9.8 Critical | Arbitrary file read in Jenkins CLI; impacts CI/CD pipelines deploying SIEM rules | SIEM detection-pipeline credential theft; rule tampering | Upgrade Jenkins; restrict CLI access; rotate credentials |
| CVE-2019-15846 | Cowrie honeypot (Exim vuln) | 9.8 Critical | If Cowrie host runs Exim MTA, RCE via TLS SNI buffer overflow | Honeypot host compromise; attacker detects deception | Patch Exim; isolate honeypot hosts; do not co-locate services |

**Honeypot detection.** Attackers fingerprint honeypots via default shell responses, SSH version strings, and response timing (Shodan honeypot tags). Mitigation: customize Cowrie's `honeyfs/`, `txtcmds/`, and `userdb` to match production profiles; randomize SSH banners and ciphers.

---

## 12. Advanced Threat Modeling

### 12.1 STRIDE-per-element systematic enumeration

Where Section 1.1 introduces STRIDE categories and applies them narratively to a DFD, STRIDE-per-element is the tool-assisted variant that enumerates threats mechanically for every element in a Data Flow Diagram. The Microsoft Threat Modeling Tool and OWASP Threat Dragon both implement this approach: the analyst draws the DFD (processes, data stores, data flows, external entities, trust boundaries), and the tool generates one threat entry per applicable STRIDE category per element.

**DFD decomposition levels.** A production threat model decomposes across three DFD levels:

- **Context diagram (Level 0):** The system as a single process, all external entities, and the trust boundaries between them. This level identifies the attack surface perimeter.
- **Level 1:** Decompose the system into its major subsystems (e.g., web tier, API tier, queue, database, object store, identity provider). Each subsystem becomes a process node. Data flows between subsystems and across trust boundaries are drawn explicitly.
- **Level 2:** Decompose each Level 1 process into internal components. For a web tier, this might separate the reverse proxy, the application server, the session store, and the static asset CDN. Level 2 is where most actionable threats emerge.

**Microsoft Threat Modeling Tool automation.** The tool reads a `.tm7` model file and produces a threat report:

```bash
# Export threat model from CLI (Windows)
TMT7.exe /threat-model "ecommerce-platform.tm7" /report "threats-report.html"

# The generated report contains one row per element-STRIDE combination:
# Element: "API Gateway" | Category: Elevation of Privilege | Description: auto-generated
# Element: "API Gateway" | Category: Tampering | Description: auto-generated
# ...
```

Each auto-generated threat requires analyst triage: confirm (real threat, assign mitigation), mitigate (already controlled, document the control), or not applicable (justify exclusion). The tool tracks triage state and exports to CSV for integration with issue trackers.

**OWASP Threat Dragon.** Open-source alternative with JSON-based model files suitable for version control:

```bash
# Install Threat Dragon desktop
npm install -g owasp-threat-dragon
threat-dragon --version

# Model files are JSON — diff-friendly in git
git diff HEAD -- models/payment-service.json
# Shows added/removed elements, new trust boundaries, changed threat states
```

Threat Dragon models store threats inline with their parent element. Each threat object includes: `type` (STRIDE category), `status` (Open / Mitigated / Not Applicable), `severity` (High / Medium / Low), `description`, and `mitigation`. This structure enables detection engineers to query open threats programmatically and generate detection requirements.

### 12.2 PASTA methodology

PASTA (Process for Attack Simulation and Threat Analysis) is a seven-stage, risk-centric methodology that connects business objectives to technical threat analysis. Unlike STRIDE's per-element enumeration, PASTA works top-down from business impact to attack simulation.

**Stage 1 — Define objectives.** Identify business-critical assets and the risk appetite of stakeholders. Output: asset inventory ranked by business value, acceptable risk thresholds per asset class.

**Stage 2 — Define technical scope.** Document the application architecture: technology stack, network topology, data flows, third-party integrations, cloud services. Output: architecture diagram with component inventory.

**Stage 3 — Application decomposition.** Decompose the application into components, trust boundaries, entry points, and data assets. This stage produces DFDs similar to STRIDE but explicitly tags each data asset with its classification level (public, internal, confidential, restricted).

**Stage 4 — Threat analysis.** Identify threat actors and their capabilities using threat intelligence (MITRE ATT&CK groups, industry-specific threat reports). Map each actor to the components they would target. Output: threat actor profiles correlated to attack surface elements.

**Stage 5 — Vulnerability analysis.** Identify known vulnerabilities (CVE database, SAST/DAST findings, penetration test results) and map them to the components from Stage 3. Correlate with threat actors from Stage 4 to determine which vulnerabilities are likely to be exploited.

**Stage 6 — Attack modeling and simulation.** Build attack trees (Section 1.2) for the highest-risk threat-actor/vulnerability combinations. Simulate attack paths using tools such as MITRE ATT&CK Navigator to visualize coverage:

```bash
# Generate ATT&CK Navigator layer from attack tree leaf nodes
# Input: JSON mapping leaf nodes to ATT&CK technique IDs
cat << 'LAYER' > pasta-stage6-layer.json
{
  "name": "PASTA Stage 6 — Payment Service",
  "versions": { "attack": "15", "navigator": "5.1", "layer": "4.5" },
  "domain": "enterprise-attack",
  "techniques": [
    { "techniqueID": "T1190", "score": 100, "comment": "Exploit public-facing app — SQLi in search endpoint" },
    { "techniqueID": "T1078.004", "score": 80, "comment": "Valid cloud accounts — stolen service account key" },
    { "techniqueID": "T1567.002", "score": 60, "comment": "Exfil over web service — data to attacker-controlled S3" },
    { "techniqueID": "T1059.004", "score": 70, "comment": "Unix shell — post-exploit command execution" }
  ]
}
LAYER
# Import into ATT&CK Navigator: https://mitre-attack.github.io/attack-navigator/
```

**Stage 7 — Risk and impact analysis.** Quantify residual risk for each attack path. Calculate: `Risk = Likelihood x Impact`, where likelihood incorporates threat actor capability, vulnerability exploitability (CVSS exploitability metrics), and existing control effectiveness. Output: prioritized risk register with treatment decisions.

### 12.3 Attack tree automated generation and quantitative analysis

Section 1.2 covers manual attack tree construction. This section extends that with automated generation and formal quantitative methods.

**Automated generation from threat intelligence.** ATT&CK-based attack trees can be generated programmatically by traversing technique chains:

```python
#!/usr/bin/env python3
"""Generate attack tree from ATT&CK technique chains."""
import json
from dataclasses import dataclass, field

@dataclass
class AttackNode:
    technique_id: str
    name: str
    gate: str = "OR"  # OR = any child suffices, AND = all required
    cost_usd: int = 0
    skill_level: str = "medium"
    probability: float = 0.5
    children: list = field(default_factory=list)

def build_tree_from_chain(chain: list[dict]) -> AttackNode:
    """Build an AND-gate tree from a sequential ATT&CK chain."""
    root = AttackNode(
        technique_id="GOAL",
        name="Exfiltrate customer PII",
        gate="OR",
    )
    sequential_path = AttackNode(
        technique_id="PATH-1",
        name="Web app exploitation chain",
        gate="AND",
    )
    for step in chain:
        sequential_path.children.append(AttackNode(
            technique_id=step["tid"],
            name=step["name"],
            cost_usd=step.get("cost", 0),
            skill_level=step.get("skill", "medium"),
            probability=step.get("prob", 0.5),
        ))
    root.children.append(sequential_path)
    return root

def compute_path_probability(node: AttackNode) -> float:
    """Compute aggregate probability for AND/OR gates."""
    if not node.children:
        return node.probability
    child_probs = [compute_path_probability(c) for c in node.children]
    if node.gate == "AND":
        result = 1.0
        for p in child_probs:
            result *= p
        return result
    else:  # OR gate — probability of at least one succeeding
        result = 1.0
        for p in child_probs:
            result *= (1 - p)
        return 1 - result

# Example chain: initial access -> execution -> exfiltration
chain = [
    {"tid": "T1190", "name": "Exploit Public-Facing Application", "cost": 5000, "skill": "high", "prob": 0.4},
    {"tid": "T1059.004", "name": "Unix Shell", "cost": 0, "skill": "medium", "prob": 0.9},
    {"tid": "T1567.002", "name": "Exfiltration to Cloud Storage", "cost": 100, "skill": "low", "prob": 0.8},
]
tree = build_tree_from_chain(chain)
path_prob = compute_path_probability(tree)
print(f"Attack path probability: {path_prob:.3f}")
# AND gate: 0.4 * 0.9 * 0.8 = 0.288
```

**Quantitative analysis methods.** Beyond simple probability multiplication:

- **Monte Carlo simulation:** Assign probability distributions (beta distributions for success rates, log-normal for cost) to each leaf node. Run 10,000+ iterations to produce a probability density function for the overall attack cost and likelihood. This reveals the variance — a path with 0.3 mean probability might have a 95th percentile of 0.6 under certain parameter distributions.
- **Return on Attack (ROA):** `ROA = (Expected Gain x Probability of Success) / Attack Cost`. Paths with ROA > 1.0 are economically rational for the attacker and must be prioritized for defense.
- **Pareto analysis of attack paths:** Rank all paths by risk (probability x impact). Typically, 20% of paths account for 80% of total risk. Focus mitigation budget on those paths first.

### 12.4 Threat modeling for cloud-native and microservices

Cloud-native architectures introduce threat modeling challenges absent from monolithic DFDs: dynamic service discovery, ephemeral container lifetimes, east-west traffic volumes, shared infrastructure (Kubernetes API server, etcd, service mesh control plane), and multi-tenant isolation boundaries.

**Kubernetes-specific DFD elements.** A Kubernetes threat model adds these elements beyond traditional DFDs:

| Element | STRIDE applicability | Key threats |
|---------|---------------------|-------------|
| Kubernetes API server | All 6 | Unauthenticated access (misconfigured RBAC), SSRF via webhook configs |
| etcd | T, I, D | Unencrypted etcd; secrets stored in plaintext; snapshot exfiltration |
| kubelet | S, T, E | Kubelet API exposed without authn; container escape via CVE |
| Service mesh sidecar | S, T, I | Sidecar injection bypass; mTLS downgrade; proxy misconfiguration |
| Container registry | S, T, I, E | Image poisoning; unsigned images; registry credential theft |
| Pod (workload) | All 6 | Privileged container escape; secrets in env vars; SSRF to metadata |

**Microservices inter-service trust boundaries.** In a monolith, function calls are intra-process and trusted. In microservices, every inter-service call crosses a network boundary. Threat modeling must treat each service-to-service data flow as crossing a trust boundary unless mutual authentication (mTLS via service mesh) is enforced and verified.

```yaml
# Istio PeerAuthentication: enforce mTLS across namespace
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: production
spec:
  mtls:
    mode: STRICT
---
# Istio AuthorizationPolicy: restrict which services can call the payment service
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payment-service-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/production/sa/order-service"
        - "cluster.local/ns/production/sa/billing-service"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/charges", "/api/v1/refunds"]
```

### 12.5 AI/ML system threat modeling: ATLAS framework

MITRE ATLAS (Adversarial Threat Landscape for AI Systems) extends ATT&CK to ML/AI-specific attack surfaces. ATLAS defines tactics and techniques specific to the ML lifecycle: reconnaissance of model APIs, resource development of adversarial examples, initial access via model supply chain, evasion via adversarial inputs, and exfiltration of training data or model weights.

**ATLAS threat categories for a model-serving pipeline:**

| ATLAS Tactic | Technique example | Threat to model-serving pipeline |
|---|---|---|
| ML Model Access | AML.T0040 — ML Model Inference API Access | Attacker queries prediction API to extract model behavior |
| Evasion | AML.T0015 — Evade ML Model | Adversarial inputs crafted to cause misclassification |
| Exfiltration | AML.T0024 — Exfiltration via ML Inference API | Model inversion attack recovering training data PII |
| Poisoning | AML.T0020 — Poison Training Data | Backdoor injection via compromised training dataset |
| Supply Chain | AML.T0010 — ML Supply Chain Compromise | Trojanized model weights in public model hub (HuggingFace, etc.) |

**Threat model checklist for ML deployments:**

1. **Model provenance.** Are model weights signed and verified before deployment? Is the training pipeline auditable (data lineage, hyperparameter tracking)?
2. **Input validation.** Are inference inputs validated against expected schemas and value ranges before reaching the model? Are adversarial input detectors deployed (statistical distance checks, input reconstruction error thresholds)?
3. **Output sanitization.** Are model outputs validated before being acted upon by downstream systems? A classification model returning unexpected labels must be caught before triggering automated actions.
4. **API rate limiting.** Are prediction APIs rate-limited to prevent model extraction attacks (Tramer et al., 2016)? Typical threshold: 1,000 queries/hour per API key for non-batch endpoints.
5. **Training data isolation.** Is training data stored with the same access controls as production secrets? Training data containing PII is subject to GDPR/CCPA; its exfiltration is a data breach.

---

## 13. Detection Architecture Patterns

### 13.1 Detection-in-depth: layering detection surfaces

Detection-in-depth mirrors defense-in-depth but focuses specifically on observability layers. An attacker who evades one detection surface must still face others. The canonical stack, from outermost to innermost:

**Layer 1 — Network detection.** Zeek/Suricata (Section 10) monitoring north-south and east-west traffic. Detects: C2 beaconing patterns, DNS tunneling, lateral movement via SMB/RPC, data exfiltration volume anomalies.

**Layer 2 — Identity detection.** Authentication and authorization log analysis. Sources: Active Directory event logs (4624/4625/4768/4769), Okta system log, Entra ID sign-in logs, RADIUS accounting. Detects: credential stuffing, impossible travel, privilege escalation via group modification, OAuth consent phishing.

**Layer 3 — Endpoint detection.** EDR telemetry (Section 8). Process creation trees, file system modifications, registry changes, loaded DLLs, kernel callbacks. Detects: living-off-the-land binaries (LOLBins), fileless malware in memory, persistence mechanisms, credential dumping.

**Layer 4 — Application detection.** Application-layer audit logs: WAF logs, API gateway access logs, database audit logs, SaaS audit trails (Google Workspace, M365). Detects: IDOR exploitation, mass data export, privilege escalation within applications, API abuse patterns.

**Layer 5 — Cloud control plane detection.** Cloud provider audit logs: AWS CloudTrail, GCP Audit Logs, Azure Activity Log. Detects: IAM policy modification, security group changes, S3 bucket policy modification, Lambda function creation by unexpected principals.

**Coverage matrix.** Map each detection layer against ATT&CK tactics to identify blind spots:

```
                    | Network | Identity | Endpoint | Application | Cloud CP |
--------------------|---------|----------|----------|-------------|----------|
Initial Access      |    X    |    X     |    X     |      X      |    X     |
Execution           |         |          |    X     |      X      |    X     |
Persistence         |    X    |    X     |    X     |      X      |    X     |
Privilege Escalation|         |    X     |    X     |      X      |    X     |
Defense Evasion     |    X    |          |    X     |             |    X     |
Credential Access   |    X    |    X     |    X     |             |          |
Discovery           |    X    |    X     |    X     |      X      |    X     |
Lateral Movement    |    X    |    X     |    X     |             |    X     |
Collection          |         |          |    X     |      X      |    X     |
Exfiltration        |    X    |          |    X     |      X      |    X     |
C2                  |    X    |          |    X     |             |          |
Impact              |    X    |          |    X     |      X      |    X     |
```

Cells without `X` are detection gaps that require compensating controls or acceptance of residual risk.

### 13.2 Alert correlation and fusion

Raw alerts from individual detection surfaces produce noise. Correlation aggregates related alerts into incidents and reduces false-positive burden.

**Temporal correlation.** Group alerts occurring within a sliding time window (typically 5-30 minutes) that share a common entity (source IP, username, hostname). Example: a failed VPN login (identity layer) followed by a successful login from the same username 3 minutes later from a different IP, followed by suspicious PowerShell execution on the endpoint 2 minutes after that — these three alerts correlate into a single credential-compromise incident.

**Graph-based correlation.** Model entities (users, hosts, IPs, processes) as nodes and alerts as edges in a graph. Connected components in the alert graph represent potential incidents. Weight edges by temporal proximity and threat severity. Clusters above a threshold score trigger incident creation.

**Splunk Risk-Based Alerting (RBA) pattern:**

```spl
| tstats summariesonly=true count from datamodel=Risk.All_Risk
  where All_Risk.risk_object_type="system"
  by All_Risk.risk_object, All_Risk.risk_score, _time
  span=1h
| stats sum(risk_score) as total_risk, dc(source) as distinct_sources,
  values(source) as contributing_rules
  by risk_object
| where total_risk > 100 AND distinct_sources >= 3
| sort -total_risk
```

This query aggregates risk scores assigned by individual detection rules onto entities (hosts, users). An entity accumulating risk from three or more distinct rule sources within an hour exceeding a threshold of 100 points triggers a high-confidence alert — dramatically reducing false positives compared to individual rule alerting.

**Elastic SIEM correlation rule:**

```yaml
# .elastic/detection-rules/correlation/credential_compromise_chain.toml
[rule]
name = "Credential Compromise Chain"
type = "eql"
language = "eql"
query = '''
sequence by user.name with maxspan=15m
  [authentication where event.outcome == "failure" and event.action == "logon-failed"
   and source.geo.country_iso_code != null]
  [authentication where event.outcome == "success"
   and source.geo.country_iso_code != null]
  [process where event.type == "start"
   and process.name in ("powershell.exe", "cmd.exe", "bash", "python3")
   and process.args : ("*-enc*", "*base64*", "*invoke-expression*", "*wget*", "*curl*")]
'''
risk_score = 85
severity = "high"
```

### 13.3 Detection coverage mapping to MITRE ATT&CK

Mapping detection rules to ATT&CK techniques exposes gaps and measures program maturity.

**DeTT&CT framework.** DeTT&CT (Detect Tactics, Techniques & Combat Threats) provides a structured methodology for scoring detection coverage:

```bash
# Clone DeTT&CT
git clone https://github.com/rabobank-cdc/DeTTECT.git
cd DeTTECT
pip install -r requirements.txt

# Generate data source coverage layer
python dettect.py ds -fd data_sources.yaml -l data_source_coverage.json

# Generate detection coverage layer
python dettect.py d -fd detections.yaml -l detection_coverage.json

# Generate visibility coverage layer
python dettect.py v -fd data_sources.yaml -l visibility_coverage.json
```

**Detection scoring methodology.** For each ATT&CK technique, assign:

| Score | Meaning | Criteria |
|-------|---------|----------|
| 0 | No detection | No rule exists; no relevant data source ingested |
| 1 | Basic | Data source ingested but no rule; manual hunting only |
| 2 | Fair | Rule exists but high false-positive rate or narrow coverage |
| 3 | Good | Tuned rule with acceptable FP rate; covers primary sub-techniques |
| 4 | Excellent | Multiple correlated rules; validated via purple team; covers all sub-techniques |

**Gap identification workflow:**

1. Export current detection rules with ATT&CK technique tags
2. Import into DeTT&CT or ATT&CK Navigator as a coverage layer
3. Overlay with threat-intelligence-driven priority layer (which techniques do threat actors targeting your sector actually use?)
4. Gaps where priority is high but coverage is 0-1 become the detection engineering backlog

### 13.4 Purple team integration for continuous detection validation

Purple teaming closes the loop between detection engineering and adversary emulation. The red team executes techniques; the blue team validates that detections fire correctly.

**Atomic Red Team execution and validation:**

```bash
# Install Atomic Red Team
IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
Install-AtomicRedTeam -getAtomics

# Execute a specific technique test (T1003.001 — LSASS Memory Dump)
Invoke-AtomicTest T1003.001 -TestNumbers 1 -GetPrereqs
Invoke-AtomicTest T1003.001 -TestNumbers 1

# After execution, validate in SIEM:
# Expected: alert fires for "Credential Dumping via LSASS" within 5 minutes
# If no alert: detection gap identified → create or tune Sigma rule
```

**Purple team detection validation checklist per technique:**

1. Execute the atomic test in a controlled environment
2. Record the timestamp of execution (UTC ISO 8601)
3. Wait for the SIEM ingestion pipeline latency (typically 1-5 minutes)
4. Query the SIEM for the expected alert
5. If alert fires: validate alert fields are correct (technique ID, severity, affected host)
6. If alert does not fire: triage root cause — missing data source, rule logic error, or parser issue
7. Document result in the detection coverage tracker
8. If gap found: create Sigma rule, test in staging, deploy to production

### 13.5 Detection as Code

Detection as Code (DaC) treats detection rules as software artifacts: version-controlled, peer-reviewed, tested, and deployed via CI/CD pipelines.

**Repository structure:**

```
detection-rules/
├── sigma/
│   ├── credential_access/
│   │   ├── lsass_memory_dump.yml
│   │   ├── dcsync_attack.yml
│   │   └── kerberoasting.yml
│   ├── lateral_movement/
│   │   ├── psexec_service_creation.yml
│   │   └── wmi_remote_execution.yml
│   └── exfiltration/
│       ├── dns_tunneling.yml
│       └── large_upload_to_cloud.yml
├── splunk/
│   ├── correlation/
│   └── notable/
├── elastic/
│   ├── detection-rules/
│   └── ml-jobs/
├── tests/
│   ├── test_sigma_syntax.py
│   ├── test_rule_coverage.py
│   └── test_false_positive_rate.py
├── .github/
│   └── workflows/
│       ├── validate-sigma.yml
│       └── deploy-rules.yml
└── README.md
```

**CI/CD pipeline for detection rules:**

```yaml
# .github/workflows/validate-sigma.yml
name: Validate and Deploy Sigma Rules
on:
  push:
    paths: ['sigma/**']
  pull_request:
    paths: ['sigma/**']

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Install sigma-cli
      run: pip install sigma-cli pySigma-backend-splunk pySigma-backend-elasticsearch
    - name: Validate Sigma syntax
      run: |
        sigma check sigma/**/*.yml --fail-on-error
    - name: Convert to Splunk SPL (dry run)
      run: |
        sigma convert -t splunk -p sysmon sigma/**/*.yml > /dev/null
    - name: Convert to Elastic EQL (dry run)
      run: |
        sigma convert -t elasticsearch -p ecs_windows sigma/**/*.yml > /dev/null
    - name: Run unit tests
      run: pytest tests/ -v

  deploy:
    needs: validate
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Deploy to Splunk
      run: |
        sigma convert -t splunk -p sysmon sigma/**/*.yml | \
        python scripts/deploy_to_splunk.py --url "$SPLUNK_URL" --token "$SPLUNK_HEC_TOKEN"
      env:
        SPLUNK_URL: ${{ secrets.SPLUNK_URL }}
        SPLUNK_HEC_TOKEN: ${{ secrets.SPLUNK_HEC_TOKEN }}
```

**Testing framework for detection rules.** Beyond syntax validation, detection rules need functional testing against known-good log samples:

```python
#!/usr/bin/env python3
"""Test Sigma rules against sample log events."""
import yaml
import pytest
from sigma.collection import SigmaCollection
from sigma.backends.splunk import SplunkBackend
from sigma.pipelines.sysmon import sysmon_pipeline

def load_sigma_rule(path: str) -> SigmaCollection:
    return SigmaCollection.from_yaml(open(path))

def test_lsass_dump_rule_matches_known_event():
    """Rule must match a known LSASS dump event."""
    rule = load_sigma_rule("sigma/credential_access/lsass_memory_dump.yml")
    backend = SplunkBackend(processing_pipeline=sysmon_pipeline())
    spl_query = backend.convert_rule(rule)[0]
    # Verify the SPL contains expected field filters
    assert "TargetImage" in spl_query or "TargetFilename" in spl_query
    assert "lsass" in spl_query.lower()

def test_all_rules_have_mitre_tags():
    """Every rule must map to at least one ATT&CK technique."""
    import glob
    for rule_path in glob.glob("sigma/**/*.yml", recursive=True):
        with open(rule_path) as f:
            rule_data = yaml.safe_load(f)
        tags = rule_data.get("tags", [])
        attack_tags = [t for t in tags if t.startswith("attack.")]
        assert len(attack_tags) > 0, f"{rule_path} missing ATT&CK tags"
```

---

## 14. Secure Architecture Assessment

### 14.1 Architecture review methodology

A security architecture review evaluates whether the system's design decisions adequately address the threat landscape identified during threat modeling. The review is conducted against a structured checklist, not ad hoc.

**Security architecture review checklist:**

| Domain | Review question | Evidence required |
|--------|----------------|-------------------|
| Authentication | Is MFA enforced for all human access? Are service-to-service calls mutually authenticated? | IdP configuration export; service mesh mTLS policy |
| Authorization | Is authorization enforced at the API gateway AND the service level (defense-in-depth)? | OPA/Rego policies; AuthorizationPolicy manifests |
| Data protection | Is data encrypted at rest (AES-256 or equivalent) and in transit (TLS 1.2+)? | KMS key policies; TLS cipher suite config; certificate inventory |
| Network segmentation | Are workloads segmented by sensitivity? Is east-west traffic filtered? | NetworkPolicy manifests; firewall rule exports; VPC flow logs |
| Secrets management | Are secrets injected at runtime (not baked into images or env vars in manifests)? | Vault/CSI driver configuration; pod security admission policies |
| Logging and monitoring | Are security-relevant events logged, forwarded, and retained per policy? | Log pipeline architecture diagram; retention policy; SIEM ingestion confirmation |
| Incident response | Is there a documented IR plan with defined roles, communication channels, and runbooks? | IR plan document; tabletop exercise results |
| Supply chain | Are container images signed and verified? Are dependencies pinned and scanned? | Cosign/Notation policies; Trivy/Grype scan results; SBOM |
| Resilience | Are failover and disaster recovery mechanisms tested? | DR test results; RTO/RPO documentation |

**Conducting the review.** The reviewer obtains the architecture documentation (C4 model, DFDs, deployment diagrams), the threat model, and the current security control inventory. For each checklist item, the reviewer assigns a status:

- **Implemented:** Control exists and evidence confirms correct configuration.
- **Partial:** Control exists but has gaps (e.g., mTLS enforced on 80% of services).
- **Missing:** No control in place. This becomes a finding with a severity rating.
- **Not Applicable:** Justified exclusion (e.g., no human access to a fully-automated pipeline).

### 14.2 Threat model validation via attack simulation

A threat model on paper is a hypothesis. Validation requires testing whether the identified threats are actually mitigated by the implemented controls.

**Methodology:**

1. Select the top 10 threats from the threat model ranked by risk score.
2. For each threat, define an attack simulation scenario that exercises the identified attack path.
3. Execute the simulation in a staging environment that mirrors production architecture.
4. Record whether the attack succeeds or fails, and whether detection alerts fire.
5. For each successful attack: the threat model is validated but the mitigation is insufficient — escalate to remediation.
6. For each failed attack with detection: the control and detection are both effective — document and close.
7. For each failed attack without detection: the control works but the organization is blind — add detection.

**Automated validation with Caldera:**

```bash
# Deploy MITRE Caldera server
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip install -r requirements.txt
python server.py --insecure

# Create an adversary profile matching the threat model
# Navigate to http://localhost:8888
# Adversaries → Create → Add abilities matching top 10 threat model techniques
# Operations → Create → Select adversary profile → Run against staging agents

# After operation completes, export the operation report
curl -s http://localhost:8888/api/v2/operations/{operation_id}/report \
  -H "KEY: ADMIN123" | python -m json.tool > validation_report.json
```

### 14.3 Security control effectiveness measurement

Measuring whether security controls actually reduce risk requires quantitative metrics, not subjective assessments.

**Key metrics:**

| Metric | Formula | Target | Measurement source |
|--------|---------|--------|--------------------|
| Mean Time to Detect (MTTD) | Avg(time_detected - time_of_attack) | < 24 hours | SIEM alert timestamps vs. red team execution timestamps |
| Mean Time to Respond (MTTR) | Avg(time_contained - time_detected) | < 4 hours | Incident tracking system |
| Detection coverage ratio | (Techniques with score >= 3) / (Total techniques in scope) | > 70% | DeTT&CT coverage layer |
| False positive rate | FP_alerts / Total_alerts per rule | < 5% per rule | SIEM alert analytics |
| Alert-to-incident ratio | Incidents / Total_alerts | > 10% | SIEM + incident tracker |
| Patching cadence (critical) | Avg(time_patched - time_CVE_published) | < 72 hours | Vulnerability management platform |
| Control drift rate | Misconfigured_controls / Total_controls per audit cycle | < 5% | CSPM/SSPM scan results |

**Continuous measurement pipeline.** Export metrics from the SIEM, vulnerability scanner, and incident tracker into a time-series database (Prometheus, InfluxDB) and visualize on a security operations dashboard. Alert on metric degradation — if MTTD increases above the 24-hour threshold for two consecutive weeks, trigger a detection engineering sprint.

### 14.4 Compliance mapping

Security architecture decisions must map to compliance frameworks. A single control often satisfies requirements across multiple frameworks.

**Multi-framework control mapping example:**

| Control | NIST CSF 2.0 | ISO 27001:2022 | CIS Controls v8 |
|---------|-------------|----------------|-----------------|
| MFA for all human access | PR.AA-02 | A.8.5 | 6.3 |
| Encryption at rest (AES-256) | PR.DS-01 | A.8.24 | 3.11 |
| Network segmentation | PR.IR-01 | A.8.22 | 12.2 |
| Centralized logging | DE.CM-01 | A.8.15 | 8.2 |
| Vulnerability scanning | ID.RA-01 | A.8.8 | 7.5 |
| Incident response plan | RS.MA-01 | A.5.24 | 17.1 |
| Secure SDLC | PR.DS-08 | A.8.25 | 16.1 |
| Backup and recovery | PR.DS-11 | A.8.13 | 11.2 |

**Automation with compliance-as-code.** Use Open Policy Agent (OPA) to codify compliance checks against infrastructure configuration:

```rego
# policy/cis_controls_v8/control_3_11_encryption_at_rest.rego
package cis.v8.control_3_11

import rego.v1

# Deny S3 buckets without default encryption
deny contains msg if {
    some bucket in input.aws_s3_buckets
    not bucket.server_side_encryption_configuration
    msg := sprintf(
        "CIS v8 3.11 violation: S3 bucket '%s' lacks default encryption at rest",
        [bucket.name],
    )
}

# Deny RDS instances without storage encryption
deny contains msg if {
    some db in input.aws_rds_instances
    db.storage_encrypted == false
    msg := sprintf(
        "CIS v8 3.11 violation: RDS instance '%s' storage is not encrypted",
        [db.db_instance_identifier],
    )
}
```

### 14.5 Architecture Decision Records for security

Architecture Decision Records (ADRs) document the rationale behind security-significant design choices. When a future engineer asks "why did we choose Vault over AWS Secrets Manager?" or "why is mTLS enforced at the sidecar and not at the application?", the ADR provides the answer.

**ADR template for security decisions:**

```markdown
# ADR-0042: Use HashiCorp Vault for secrets management

## Status
Accepted (2025-01-15)

## Context
The platform requires a secrets management solution for storing database credentials,
API keys, TLS certificates, and encryption keys. Options evaluated: AWS Secrets Manager,
HashiCorp Vault, CyberArk Conjur.

## Decision
Adopt HashiCorp Vault (self-hosted, Raft storage backend) as the centralized secrets
management platform.

## Rationale
- Multi-cloud requirement: the platform runs on AWS and GCP; Vault is cloud-agnostic.
- Dynamic secrets: Vault generates short-lived database credentials, reducing blast
  radius of credential compromise.
- Transit engine: Vault provides encryption-as-a-service without exposing raw keys
  to applications.
- Audit logging: Vault produces detailed audit logs of every secret access, satisfying
  ISO 27001 A.8.15 and NIST CSF DE.CM-01.

## Consequences
- Operational overhead: the team must manage Vault HA cluster, upgrades, and unsealing.
- Dependency risk: Vault unavailability blocks application deployment (mitigated by
  HA + caching agent).

## Alternatives Rejected
- AWS Secrets Manager: single-cloud; no dynamic secrets for GCP-hosted databases.
- CyberArk Conjur: higher license cost; smaller community for Kubernetes integration.
```

ADRs are stored in the repository alongside the code they govern (typically `docs/adr/` or `architecture/decisions/`). They are immutable once accepted — superseded decisions get a new ADR referencing the old one.

---

## 15. Emerging Architecture Patterns

### 15.1 Confidential computing deployment patterns

Section 5 covers the hardware foundations of confidential computing (SGX, TDX, SEV-SNP, Arm CCA). This section addresses deployment patterns for production workloads.

**Pattern 1 — Confidential containers.** Run unmodified container workloads inside confidential VMs. The guest OS and all containers run within the hardware-encrypted memory boundary.

```bash
# Azure Confidential Containers with Kata Containers + SEV-SNP
# Deploy a confidential container group on AKS
az aks create \
  --resource-group cc-rg \
  --name cc-aks-cluster \
  --node-vm-size Standard_DC4as_v5 \
  --os-sku AzureLinux \
  --workload-runtime KataCcIsolation

# Deploy a pod with confidential computing runtime class
cat << 'EOF' | kubectl apply -f -
apiVersion: v1
kind: Pod
metadata:
  name: confidential-workload
spec:
  runtimeClassName: kata-cc-isolation
  containers:
  - name: app
    image: myregistry.azurecr.io/confidential-app:v1.2
    resources:
      limits:
        memory: "4Gi"
        cpu: "2"
    securityContext:
      readOnlyRootFilesystem: true
      allowPrivilegeEscalation: false
EOF
```

**Pattern 2 — Attestation-gated secret delivery.** Secrets are released to a workload only after remote attestation verifies the workload's integrity. The attestation flow:

1. Workload boots inside a confidential VM (TDX/SEV-SNP).
2. Workload requests an attestation report from the hardware (includes measurement of firmware, kernel, initrd, and workload hash).
3. Workload sends the attestation report to a relying party (e.g., Azure Attestation, Intel Trust Authority, or a self-hosted MAA).
4. The relying party verifies the report against a policy: is the firmware version current? Is the workload measurement in the allow-list? Is the security version number (SVN) above the minimum?
5. On success, the relying party issues a short-lived token. The workload presents this token to Vault/KMS to retrieve secrets.

```bash
# Verify AMD SEV-SNP attestation report (Linux guest)
sevtool --ofolder /tmp/attestation_output \
        --validate_guest_report

# Fields in the report:
# MEASUREMENT: SHA-384 of VMSA + firmware + kernel + initrd
# POLICY: flags (debug=0, migration=0, single-socket=1)
# REPORT_DATA: 64-byte nonce (set by workload to bind to TLS session)
```

**Pattern 3 — Multi-party computation coordination.** Multiple organizations contribute data to a joint computation without revealing their individual datasets. Each party runs their portion inside a confidential enclave. The orchestrator verifies all enclaves via remote attestation before initiating the computation.

### 15.2 Hardware root of trust for cloud workloads

TPM attestation (Section 4) traditionally targets physical servers. Extending it to cloud VMs requires virtual TPMs (vTPMs) backed by the cloud provider's hardware security infrastructure.

**GCP Shielded VMs with vTPM attestation:**

```bash
# Create a Shielded VM with vTPM and integrity monitoring
gcloud compute instances create secure-vm \
  --zone=us-central1-a \
  --machine-type=n2d-standard-4 \
  --shielded-secure-boot \
  --shielded-vtpm \
  --shielded-integrity-monitoring \
  --image-family=ubuntu-2404-lts-amd64 \
  --image-project=ubuntu-os-cloud

# Query integrity monitoring results
gcloud compute instances get-shielded-instance-identity secure-vm \
  --zone=us-central1-a --format=json

# The response includes signed EK certificate chain and boot integrity events
# Late launch events track kernel and initrd measurements
```

**AWS Nitro Enclaves.** AWS Nitro Enclaves provide an isolated compute environment with cryptographic attestation. The enclave has no persistent storage, no network access, and no administrator access — the only communication channel is a local vsock to the parent EC2 instance.

```bash
# Build an enclave image
nitro-cli build-enclave \
  --docker-uri myregistry/enclave-app:latest \
  --output-file enclave-app.eif

# The build output includes PCR values:
# PCR0: hash of enclave image
# PCR1: hash of Linux kernel in enclave
# PCR2: hash of application in enclave

# Run the enclave
nitro-cli run-enclave \
  --eif-path enclave-app.eif \
  --cpu-count 2 \
  --memory 4096

# Attach KMS key policy conditioned on enclave PCR values
# This ensures only a specific enclave build can decrypt secrets
```

**KMS policy conditioned on attestation:**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::123456789012:role/enclave-role" },
    "Action": "kms:Decrypt",
    "Resource": "*",
    "Condition": {
      "StringEqualsIgnoreCase": {
        "kms:RecipientAttestation:PCR0": "abc123def456..."
      }
    }
  }]
}
```

### 15.3 Service mesh security architecture

Service meshes (Istio, Linkerd, Cilium) provide a uniform security layer for microservices communication. The key security capabilities: automatic mTLS, fine-grained authorization, and observability — all without modifying application code.

**mTLS lifecycle in Istio.** Istio's control plane (istiod) acts as the certificate authority. Each sidecar proxy (Envoy) receives a short-lived X.509 SVID (SPIFFE Verifiable Identity Document) via the SDS (Secret Discovery Service) API. Certificate rotation occurs automatically before expiry (default: 24 hours).

**Authorization policy defense-in-depth.** Layer authorization at three levels:

```yaml
# Level 1: Namespace isolation — deny all cross-namespace traffic by default
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-cross-namespace
  namespace: istio-system  # root namespace = mesh-wide
spec:
  action: DENY
  rules:
  - from:
    - source:
        notNamespaces: ["istio-system"]
    to:
    - operation:
        notPorts: ["15014"]  # allow Istio telemetry port
---
# Level 2: Service-level allow — explicit allow for known callers
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-api
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/frontend"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
---
# Level 3: Request-level conditions — JWT claim validation
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: admin-endpoints
  namespace: production
spec:
  selector:
    matchLabels:
      app: admin-service
  action: ALLOW
  rules:
  - from:
    - source:
        requestPrincipals: ["https://auth.example.com/*"]
    when:
    - key: request.auth.claims[role]
      values: ["admin"]
```

### 15.4 Supply chain security architecture

Software supply chain attacks (SolarWinds, Codecov, xz-utils) target the build and distribution pipeline. A secure supply chain architecture enforces provenance verification at every stage.

**SLSA (Supply-chain Levels for Software Artifacts) framework.** SLSA defines four levels of supply chain integrity:

| SLSA Level | Requirements | Protects against |
|------------|-------------|------------------|
| L1 | Build process exists and produces provenance | Ad hoc builds; no audit trail |
| L2 | Hosted build service; signed provenance | Tampered build scripts |
| L3 | Hardened build platform; non-falsifiable provenance | Compromised build environment |
| L4 | Two-party review; hermetic builds; reproducible | Insider threats; dependency confusion |

**Generating and verifying SLSA provenance with SLSA GitHub Generator:**

```yaml
# .github/workflows/slsa-build.yml
name: SLSA Build
on: [push]
permissions:
  id-token: write   # OIDC token for signing
  contents: read
  actions: read

jobs:
  build:
    runs-on: ubuntu-latest
    outputs:
      digest: ${{ steps.hash.outputs.digest }}
    steps:
    - uses: actions/checkout@v4
    - name: Build artifact
      run: |
        go build -o myapp ./cmd/myapp
    - name: Generate digest
      id: hash
      run: |
        DIGEST=$(sha256sum myapp | cut -d ' ' -f 1)
        echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"

  provenance:
    needs: build
    permissions:
      actions: read
      id-token: write
      contents: write
    uses: slsa-framework/slsa-github-generator/.github/workflows/generator_generic_slsa3.yml@v2.1.0
    with:
      base64-subjects: "${{ needs.build.outputs.digest }}"
```

**In-toto layout for multi-step supply chain verification:**

```bash
# Define the supply chain layout: which steps, performed by whom, producing what
in-toto-run --step-name clone --products git-repo/ -- git clone https://github.com/org/repo.git git-repo/
in-toto-run --step-name build --materials git-repo/ --products dist/myapp -- make -C git-repo/ build
in-toto-run --step-name test --materials dist/myapp -- make -C git-repo/ test
in-toto-run --step-name sign --materials dist/myapp --products dist/myapp.sig -- cosign sign-blob dist/myapp

# Verify the full supply chain
in-toto-verify --layout supply-chain-layout.json --layout-keys layout-key.pub
```

**Container image signing with Cosign and admission control:**

```bash
# Sign a container image with keyless signing (Fulcio + Rekor)
cosign sign --yes myregistry.example.com/myapp:v1.2.3

# Verify the signature
cosign verify myregistry.example.com/myapp:v1.2.3 \
  --certificate-identity="https://github.com/org/repo/.github/workflows/build.yml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com"

# Enforce signature verification at admission with Kyverno
cat << 'EOF' | kubectl apply -f -
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-image-signatures
spec:
  validationFailureAction: Enforce
  background: false
  rules:
  - name: verify-cosign-signature
    match:
      any:
      - resources:
          kinds: ["Pod"]
    verifyImages:
    - imageReferences: ["myregistry.example.com/*"]
      attestors:
      - entries:
        - keyless:
            subject: "https://github.com/org/repo/*"
            issuer: "https://token.actions.githubusercontent.com"
            rekor:
              url: https://rekor.sigstore.dev
EOF
```

### 15.5 AI security architecture

Securing AI/ML inference pipelines requires controls at the model, data, API, and infrastructure layers. This section covers the deployment-time security architecture (threat modeling of AI systems is covered in Section 12.5).

**Model serving security architecture.** A production model-serving pipeline has these security-relevant components:

```
Client → API Gateway (authn, authz, rate limit, input validation)
       → Inference Service (model loaded from signed artifact store)
       → Feature Store (read-only access; no raw training data exposure)
       → Model Registry (signed model artifacts; version pinning)
       → Monitoring (drift detection, adversarial input detection, output anomaly)
```

**Input validation for inference APIs.** Validate inference inputs against a strict schema before they reach the model:

```python
from pydantic import BaseModel, Field, field_validator
import numpy as np

class InferenceRequest(BaseModel):
    features: list[float] = Field(..., min_length=10, max_length=10)
    model_version: str = Field(..., pattern=r"^v\d+\.\d+\.\d+$")

    @field_validator("features")
    @classmethod
    def validate_feature_range(cls, v: list[float]) -> list[float]:
        arr = np.array(v)
        if np.any(np.isnan(arr)) or np.any(np.isinf(arr)):
            raise ValueError("Features must not contain NaN or Inf")
        if np.any(np.abs(arr) > 1e6):
            raise ValueError("Feature values out of expected range [-1e6, 1e6]")
        return v
```

**Adversarial input detection.** Deploy a statistical detector that flags inputs far from the training distribution:

```python
from scipy.spatial.distance import mahalanobis
import numpy as np

class AdversarialDetector:
    def __init__(self, training_mean: np.ndarray, training_cov_inv: np.ndarray, threshold: float):
        self.mean = training_mean
        self.cov_inv = training_cov_inv
        self.threshold = threshold  # calibrated at 99th percentile of training set distances

    def is_adversarial(self, input_vector: np.ndarray) -> bool:
        distance = mahalanobis(input_vector, self.mean, self.cov_inv)
        return distance > self.threshold
```

**Model artifact integrity.** Sign model artifacts at training time and verify before loading:

```bash
# Sign model artifact with Cosign
cosign sign-blob --yes --output-signature model-v1.2.3.sig model-v1.2.3.onnx

# Verify before loading in inference service
cosign verify-blob \
  --certificate-identity="https://github.com/org/ml-pipeline/.github/workflows/train.yml@refs/heads/main" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  --signature model-v1.2.3.sig \
  model-v1.2.3.onnx

# On verification failure: refuse to load; alert SecOps; block deployment
```

**Output guardrails for generative AI.** When serving LLMs or generative models, enforce output filtering to prevent prompt injection, PII leakage, and harmful content:

1. **Output schema enforcement:** Constrain the model output to a strict JSON schema using guided generation (Outlines, LMFE) rather than relying on post-hoc parsing.
2. **PII scanning:** Run model output through a PII detector (Presidio, custom regex + NER) before returning to the client. Redact or block responses containing detected PII.
3. **Content classification:** Pass output through a safety classifier (separate model) that flags harmful, off-topic, or policy-violating responses.
4. **Rate limiting per user.** Prevent automated jailbreak attempts by enforcing per-user rate limits on the generation endpoint: 60 requests/minute for standard tier, 10 requests/minute for free tier.

---

## 16. Cross-references

**To Domain 2 (OS primitives):** Secure boot (Section 3) builds on the boot process described in Domain 2 Chapter 2A. TPM PCR measurements (Section 3.2) extend the kernel-integrity concepts from Domain 2 Chapter 2C (IMA/EVM §5.7). Confidential computing (Section 5) uses hardware-enforced isolation — the VM-level equivalent of namespaces and capabilities.

**To Domain 7 (hardware):** SGX attacks (Chapter 7B §1) target the confidential-computing technologies described here (Section 5.1). Secure boot bypass via fault injection (Domain 17 §4) directly attacks the UEFI Secure Boot flow (Section 3.1). TPM side-channel attacks (extracting sealed keys via power analysis of the TPM chip) use Domain 17 §1 techniques.

**To Domain 24 (DFIR):** Detection engineering (Section 6) produces the rules that DFIR teams use: Sigma rules (Domain 24 §4.5) are written in the detection-engineering lifecycle (Section 6.1). SIEM queries (Section 7) are the tools DFIR analysts use during incidents. Zeek logs (Section 10.1) are a primary data source for network-forensic analysis.

**To Domain 25 (threat intel):** ATT&CK (Section 1.5, expanded in Domain 25 §1.3) drives detection requirements (Section 6.1). Threat-actor profiles (Domain 25 §2-3) inform which detections to prioritize. TI indicator feeds (STIX/TAXII, MISP) are consumed by the SIEM (Section 7) for correlation.

**To Domain 11 (tradecraft):** EDR bypass detection (Section 8.2) is the defensive response to the evasion techniques from Chapter 11B. Deception technology (Section 9) detects attackers who have bypassed all other controls — the last line of defense when prevention and detection have failed.

---

## Exercises

1. **STRIDE threat model with DFD.** Given a three-tier web application (React SPA, Node.js API, PostgreSQL) deployed behind an AWS ALB with Cognito authentication, draw a Level-1 Data Flow Diagram identifying all trust boundaries. Apply STRIDE to every DFD element, produce a threat register with at least 15 threats, assign CVSS 3.1 base scores, map each to an ATT&CK technique, and propose a treatment (mitigate/accept/transfer/avoid) with a specific control for each mitigation. Deliver the register as a structured table.

2. **TPM 2.0 sealing lab.** On a Linux workstation with a TPM 2.0 (hardware or swtpm emulator), use `tpm2-tools` to: (a) create a primary key under the storage hierarchy, (b) read the current SHA-256 PCR 7 value, (c) create a policy session requiring PCR 7, (d) seal a 32-byte secret to that policy, (e) unseal successfully, (f) extend PCR 7 with an arbitrary measurement and demonstrate that unseal now fails with `TPM2_RC_POLICY_FAIL`. Document each command with output and explain the security implications of each step.

3. **Sigma rule development and CI pipeline.** Write three Sigma rules: one targeting LSASS credential dumping via `comsvcs.dll MiniDump` (T1003.001), one targeting DCSync via Event 4662 with DS-Replication GUIDs (T1003.006), and one targeting scheduled task persistence with encoded payloads (T1053.005). For each rule, provide a true-positive and a true-negative JSON test event. Convert all three to Splunk SPL and Elastic ECS queries using `sigma-cli`. Write a GitHub Actions workflow (`sigma-ci.yml`) that lints, validates metadata, and runs unit tests on every pull request.

4. **Confidential computing comparison.** Research and produce a comparison table of Intel TDX, AMD SEV-SNP, and Arm CCA across the following dimensions: isolation granularity, TCB components, memory encryption algorithm, integrity protection mechanism, attestation flow, maximum protected memory, and at least one published attack per technology with CVE (where available). For the AMD SEV-SNP entry, explain how the RMP (Reverse Map Table) prevents the SEVered page-remap attack that affected pre-SNP SEV.

5. **Deception deployment and detection.** Design an Active Directory deception layer comprising: (a) two honey accounts with attractive names and SPNs, (b) one deceptive computer object resembling a domain controller, (c) three canary files placed in network shares likely to be accessed during reconnaissance, and (d) a DNS canary token embedded in an internal wiki page. For each deception element, write the Sigma detection rule that fires when the element is triggered. Deploy the honey accounts in a lab AD environment and validate that Kerberoasting the honey SPN generates Event 4769 that matches your Sigma rule.

---

## Readings and References

- NIST SP 800-207 — Zero Trust Architecture (August 2020): <https://csrc.nist.gov/pubs/sp/800/207/final> (retrieved: 2026-05-29)
- NIST Cybersecurity Framework (CSF) 2.0 (February 2024): <https://www.nist.gov/cyberframework> (retrieved: 2026-05-29)
- MITRE ATT&CK Framework — Enterprise Matrix: <https://attack.mitre.org/matrices/enterprise/> (retrieved: 2026-05-29)
- SigmaHQ — Main Sigma Rule Repository: <https://github.com/SigmaHQ/sigma> (retrieved: 2026-05-29)
- SigmaHQ — Sigma Rule Specification: <https://github.com/SigmaHQ/sigma-specification/> (retrieved: 2026-05-29)
- Shostack, A. — *Threat Modeling: Designing for Security* (Wiley, 2014) — canonical STRIDE reference
- Microsoft Threat Modeling Tool: <https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool> (retrieved: 2026-05-29)
- Intel TDX Architecture Specification: <https://www.intel.com/content/www/us/en/developer/tools/trust-domain-extensions/documentation.html> (retrieved: 2026-05-29)
- AMD SEV-SNP ABI Specification: <https://www.amd.com/en/developer/sev.html> (retrieved: 2026-05-29)
- Arm Confidential Compute Architecture (CCA): <https://www.arm.com/architecture/security-features/arm-confidential-compute-architecture> (retrieved: 2026-05-29)
- tpm2-tools Documentation: <https://github.com/tpm2-software/tpm2-tools> (retrieved: 2026-05-29)
- Thinkst Canary Tokens: <https://canarytokens.org/> (retrieved: 2026-05-29)

---

## Cross-Reference Matrix

| Section | Related Domain | Topic | Reference |
|---|---|---|---|
| §1 Threat modeling | Domain 25 — Threat Intelligence | ATT&CK technique mapping for threat registers | Domain 25 §1.3 |
| §3 Secure boot | Domain 2 — OS Internals | Boot process, IMA/EVM kernel integrity | Domain 2 Ch.2A, Ch.2C §5.7 |
| §4 TPM 2.0 | Domain 17 — Physical Security | TPM side-channel attacks, fault injection | Domain 17 §1, §4 |
| §5 Confidential computing | Domain 7 — Hardware Security | SGX side-channel attacks, voltage glitching | Domain 7B §1 |
| §6–7 Detection / SIEM | Domain 24 — DFIR | Sigma rules in forensic workflows, log analysis | Domain 24 §4.5 |
| §8–9 EDR / Deception | Domain 11 — Tradecraft | EDR bypass techniques that detection rules target | Domain 11B |

---

## Glossary

| Term | Definition |
|---|---|
| **STRIDE** | Microsoft threat-modeling framework categorizing threats as Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege |
| **PASTA** | Process for Attack Simulation and Threat Analysis — a seven-stage risk-centric threat-modeling methodology |
| **PCR** | Platform Configuration Register — TPM register that accumulates hash-chain measurements of boot components |
| **DRTM** | Dynamic Root of Trust for Measurement — establishes a trusted measurement point at runtime, bypassing potentially compromised firmware |
| **SRTM** | Static Root of Trust for Measurement — trust chain rooted in the platform reset vector (UEFI firmware) |
| **EPC** | Enclave Page Cache — Intel SGX protected memory region encrypted by the Memory Encryption Engine |
| **RMP** | Reverse Map Table — AMD SEV-SNP hardware structure tracking guest-physical-to-host-physical page ownership |
| **Sigma** | Generic, open, YAML-based signature format for SIEM detection rules, portable across platforms via pySigma |
| **YARA-L** | Google Chronicle's YARA-Like Language operating on UDM (Unified Data Model) events with temporal operators |
| **SPL** | Search Processing Language — Splunk's query language for log search, statistical analysis, and alerting |
| **KQL** | Kusto Query Language — used by Microsoft Sentinel and Azure Data Explorer for log analytics |
| **EQL** | Event Query Language — Elastic's sequence-based query language for correlating ordered events |
| **Honey token** | Fake credential (API key, password, token) planted as bait; any use proves unauthorized access and triggers an alert |
| **SVID** | SPIFFE Verifiable Identity Document — an X.509 certificate or JWT binding a SPIFFE ID to a cryptographic key pair |
| **Detection-as-Code** | Engineering discipline treating SIEM detection rules as versioned code artifacts with CI/CD, peer review, and automated testing |
