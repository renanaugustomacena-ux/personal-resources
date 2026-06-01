# Glossary — Cybersecurity Masterclass

> **Last updated:** 2026-05-29

100 security terms used across this library's 31 domains. Definitions are operational, not textbook abstractions.

---

| Term | Definition | Domain(s) |
|------|-----------|-----------|
| **ACE** (Arbitrary Code Execution) | Attacker gains the ability to run chosen instructions in the target process or kernel context. | 3, 4, 5, 6, 26 |
| **ACL** (Access Control List) | Ordered set of rules that grants or denies access to resources; in Active Directory, DACLs on objects control who can read, write, or delegate. | 14, 27 |
| **Address Space Layout Randomization (ASLR)** | OS-level mitigation that randomizes base addresses of stack, heap, libraries, and the executable to hinder reliable exploitation. | 6 |
| **Adversarial Example** | Input crafted to cause a machine learning model to produce an incorrect output while appearing benign to humans. | 18 |
| **AES** (Advanced Encryption Standard) | Symmetric block cipher (128-bit block, 128/192/256-bit keys) standardized by NIST; the de facto standard for bulk encryption. | 13 |
| **APT** (Advanced Persistent Threat) | State-sponsored or highly resourced threat actor group conducting long-duration, targeted intrusions. | 25, 29 |
| **AS-REP Roasting** | Kerberos attack extracting TGTs for accounts without pre-authentication, enabling offline password cracking. | 14 |
| **ATT&CK** | MITRE knowledge base cataloging adversary tactics, techniques, and procedures observed in real-world intrusions. | 25, 27, 31 |
| **Backdoor** | Covert mechanism giving unauthorized persistent access; can exist in software, firmware, hardware, or ML models. | 11, 17, 18, 19 |
| **BEC** (Business Email Compromise) | Social engineering attack where the adversary impersonates an executive or vendor to authorize fraudulent transactions. | 23 |
| **BLE** (Bluetooth Low Energy) | Short-range wireless protocol used in IoT; attack surface includes GATT enumeration, key negotiation flaws, and relay. | 28 |
| **BOF** (Buffer Overflow) | Writing data past a buffer boundary, overwriting adjacent memory (stack frames, heap metadata, vtables). | 3 |
| **C2** (Command and Control) | Infrastructure and protocol an attacker uses to communicate with implants inside a compromised network. | 11, 30 |
| **CAN Bus** | Controller Area Network; broadcast serial bus in vehicles with no authentication, enabling injection and replay attacks. | 21 |
| **Canary** (Stack) | Random value placed between local variables and the saved return address; overwrite detection terminates the process. | 6 |
| **CFI** (Control Flow Integrity) | Security policy enforcing that indirect branches target only valid destinations, mitigating code-reuse attacks. | 4 |
| **Chain of Custody** | Documented chronological record of evidence handling from collection to court presentation. | 24 |
| **CIS Benchmarks** | Consensus-based secure configuration guides maintained by the Center for Internet Security. | 27, 31 |
| **Container Escape** | Exploiting kernel or runtime vulnerabilities to break out of a container's isolation into the host. | 10 |
| **CORS** (Cross-Origin Resource Sharing) | Browser mechanism controlling which origins can read responses from a server; misconfiguration enables data theft. | 8 |
| **Credential Stuffing** | Automated reuse of leaked username-password pairs against other services. | 8, 14 |
| **CSRF** (Cross-Site Request Forgery) | Attack that tricks a user's browser into performing authenticated state-changing requests on another origin. | 8 |
| **CVSS** (Common Vulnerability Scoring System) | Standardized framework for rating the severity of software vulnerabilities (0.0--10.0 scale). | 26 |
| **CWE** (Common Weakness Enumeration) | MITRE-maintained catalog of software and hardware weakness types, referenced in vulnerability reports. | 26 |
| **Data Poisoning** | Manipulating training data to degrade or backdoor a machine learning model. | 18 |
| **DEP / NX** (Data Execution Prevention / No-eXecute) | Hardware-enforced mitigation marking data pages non-executable, preventing direct shellcode execution on the stack/heap. | 6 |
| **Diamond Model** | Threat intelligence analysis model relating adversary, infrastructure, capability, and victim. | 25 |
| **DNS Rebinding** | Attack that manipulates DNS TTLs to redirect a browser's same-origin requests to an attacker-controlled IP. | 9 |
| **DNP3** (Distributed Network Protocol 3) | SCADA protocol used in electric utilities; lacks built-in authentication in legacy deployments. | 16 |
| **DP-SGD** (Differentially Private SGD) | Training algorithm that clips per-sample gradients and adds calibrated noise to provide formal privacy guarantees. | 18 |
| **Dwell Time** | Duration an attacker remains undetected inside a compromised network, measured from initial access to discovery. | 24, 29 |
| **eBPF** (extended Berkeley Packet Filter) | Linux in-kernel virtual machine for programmable tracing, networking, and runtime security enforcement. | 31 |
| **EDR** (Endpoint Detection and Response) | Agent-based security tool that monitors endpoint telemetry (process creation, file writes, network connections) for threat detection. | 11, 31 |
| **ELF** (Executable and Linkable Format) | Standard binary format for executables, shared libraries, and core dumps on Linux/Unix systems. | 1 |
| **EMV** | Chip-based payment card standard (Europay, Mastercard, Visa) implementing cryptographic card authentication. | 22 |
| **ETW** (Event Tracing for Windows) | Windows kernel-level tracing framework; patching ETW providers is a common EDR evasion technique. | 11 |
| **Exploit Primitive** | A building-block capability (arbitrary read, arbitrary write, info leak) that can be chained into full exploitation. | 3, 4, 5, 26 |
| **Fault Injection** | Inducing transient hardware errors (voltage glitch, EM pulse, laser) to bypass security checks or leak secrets. | 17 |
| **FGSM** (Fast Gradient Sign Method) | White-box adversarial attack that perturbs input along the gradient sign direction in a single step. | 18 |
| **Format String Bug** | Vulnerability where user-controlled data is passed as a format argument, enabling arbitrary reads/writes. | 3 |
| **Fuzzing** | Automated testing technique that feeds mutated or generated inputs to a program to discover crashes and bugs. | 26 |
| **GOT / PLT** (Global Offset Table / Procedure Linkage Table) | ELF dynamic linking structures that resolve function addresses at runtime; GOT overwrites are a classic exploit target. | 1 |
| **Hardware Trojan** | Malicious modification to an integrated circuit during design or manufacturing, enabling covert functionality. | 19 |
| **Heap Spray** | Technique that fills the heap with attacker-controlled data to make exploitation of dangling pointers predictable. | 3 |
| **HIDS / NIDS** | Host-based / Network-based Intrusion Detection System; monitors system or network events for indicators of compromise. | 27, 31 |
| **ICS** (Industrial Control System) | Systems controlling physical industrial processes (PLCs, RTUs, HMIs); includes SCADA and DCS. | 16 |
| **Indicator of Compromise (IOC)** | Observable artifact (hash, IP, domain, registry key) indicating a security incident has occurred. | 24, 25 |
| **Indirect Syscall** | Evasion technique invoking system calls from ntdll code rather than from the caller's module to avoid userland hooks. | 11 |
| **IoT** (Internet of Things) | Network-connected embedded devices (sensors, actuators, cameras) typically running constrained firmware. | 28 |
| **JOP** (Jump-Oriented Programming) | Code-reuse attack chaining indirect jump gadgets, bypassing return-address-based defenses. | 4 |
| **Kerberoasting** | Active Directory attack requesting service tickets for SPNs, then cracking the ticket's encryption key offline. | 14 |
| **Kill Chain** | Phased model of an intrusion (recon, weaponize, deliver, exploit, install, C2, actions on objectives). | 29 |
| **Lateral Movement** | Post-compromise technique where attackers traverse between hosts using stolen credentials or exploits. | 14, 29, 30 |
| **LLM Guard Rails** | Runtime filters (NeMo Guardrails, LLM Guard) that constrain LLM outputs to prevent injection, PII leakage, or harmful content. | 18 |
| **LSASS** (Local Security Authority Subsystem Service) | Windows process holding logon session credentials in memory; primary target for credential dumping (Mimikatz). | 30 |
| **Malleable C2** | Cobalt Strike feature allowing operators to reshape Beacon's network traffic to mimic legitimate protocols. | 30 |
| **MEV** (Maximal Extractable Value) | Profit miners/validators can extract by reordering, inserting, or censoring transactions in a block. | 22 |
| **MITRE ATLAS** | Adversarial Threat Landscape for AI Systems; knowledge base of adversary tactics and techniques targeting ML. | 18 |
| **Modbus** | Serial/TCP SCADA protocol with no authentication; widely deployed in industrial environments. | 16 |
| **MQTT** | Lightweight publish-subscribe messaging protocol used in IoT; commonly lacks TLS and authentication in deployments. | 28 |
| **NIST CSF** | Cybersecurity Framework providing a taxonomy of security outcomes organized into Govern, Identify, Protect, Detect, Respond, Recover. | 27 |
| **NTDS.DIT** | Active Directory database file containing all domain password hashes; offline extraction enables mass credential compromise. | 14, 30 |
| **OCSF** (Open Cybersecurity Schema Framework) | Vendor-neutral telemetry schema for normalizing security event data across tools. | 31 |
| **Opcode** | Machine-level instruction encoding; relevant in shellcode construction, gadget scanning, and binary analysis. | 1, 3, 4 |
| **OSINT** (Open-Source Intelligence) | Intelligence derived from publicly available data (social media, DNS records, public filings, code repositories). | 23 |
| **OT** (Operational Technology) | Hardware and software controlling physical processes in industrial environments, distinct from IT systems. | 16 |
| **OWASP** | Open Worldwide Application Security Project; maintains the Top 10 web vulnerability list and testing guides. | 8 |
| **Padding Oracle** | Side-channel attack exploiting error messages in CBC-mode decryption to recover plaintext byte-by-byte. | 13 |
| **PE/COFF** | Portable Executable / Common Object File Format; the standard binary format on Windows. | 1 |
| **Pickle Deserialization** | Python-specific RCE vector where untrusted pickle streams execute arbitrary code during unpickling; major ML supply chain risk. | 18 |
| **PLC** (Programmable Logic Controller) | Industrial controller executing ladder logic or structured text to control physical processes. | 16 |
| **Post-Quantum Cryptography** | Cryptographic algorithms designed to resist quantum computing attacks (lattice-based, hash-based, code-based). | 13 |
| **Prompt Injection** | Attack that embeds adversarial instructions in LLM input to override system prompts or exfiltrate data. | 18 |
| **ptmalloc2** | glibc's heap allocator; understanding its bin/chunk/tcache structures is essential for heap exploitation. | 3 |
| **Purple Team** | Collaborative exercise where red team attacks and blue team defends simultaneously, sharing real-time feedback. | 27 |
| **RaaS** (Ransomware-as-a-Service) | Business model where ransomware developers lease their tooling to affiliates for a revenue share. | 29 |
| **Reentrancy** | Smart contract vulnerability where an external call re-enters the calling contract before state updates complete. | 22 |
| **RELRO** (RELocation Read-Only) | ELF hardening that makes the GOT read-only after relocation, preventing GOT overwrite attacks. | 1 |
| **ROP** (Return-Oriented Programming) | Code-reuse attack chaining short instruction sequences ending in `ret` to build arbitrary computation without injecting code. | 4 |
| **Rowhammer** | Hardware vulnerability exploiting DRAM charge leakage between adjacent rows to flip bits, enabling privilege escalation. | 7 |
| **SBOM** (Software Bill of Materials) | Machine-readable inventory of components, libraries, and dependencies in a software artifact. | 19 |
| **Seccomp** | Linux kernel facility restricting the system calls a process can invoke; used for sandboxing (seccomp-bpf). | 2, 5 |
| **SGX** (Software Guard Extensions) | Intel CPU feature providing hardware-enforced enclaves for confidential computation; subject to side-channel attacks. | 7 |
| **SIEM** (Security Information and Event Management) | Platform that aggregates, correlates, and analyzes security logs for threat detection and compliance. | 31 |
| **Sigma** | Vendor-agnostic detection rule format for SIEM systems, enabling portable threat detection logic. | 31 |
| **Smart Contract** | Self-executing program deployed on a blockchain; vulnerabilities include reentrancy, integer overflow, and access control flaws. | 22 |
| **SOAR** (Security Orchestration, Automation, and Response) | Platform automating incident response workflows via playbooks, enrichment, and orchestrated tool integration. | 31 |
| **Spectre** | Class of speculative execution side-channel vulnerabilities enabling cross-process and cross-privilege data leaks. | 7 |
| **SSRF** (Server-Side Request Forgery) | Attack inducing the server to make HTTP requests to unintended destinations, often targeting cloud metadata services. | 8, 10 |
| **STIX / TAXII** | Structured Threat Information Expression / Trusted Automated Exchange of Intelligence Information; OASIS standards for sharing threat intel. | 25 |
| **Supply Chain Attack** | Compromise of a software/hardware vendor, dependency, or build pipeline to distribute malware to downstream consumers. | 19 |
| **TLS** (Transport Layer Security) | Cryptographic protocol providing confidentiality, integrity, and authentication for network communications. | 9, 13 |
| **Type Confusion** | Bug where a program treats a memory region as a different type than intended, enabling controlled corruption. | 3, 8 |
| **UAF** (Use-After-Free) | Accessing memory after it has been freed; if the freed region is reallocated with attacker-controlled data, exploitation follows. | 3 |
| **V2X** (Vehicle-to-Everything) | Communication framework for vehicles interacting with infrastructure, pedestrians, and other vehicles. | 21 |
| **Vulnerability Disclosure** | Process of reporting, coordinating, and publishing security vulnerabilities (responsible/coordinated disclosure). | 26 |
| **XSS** (Cross-Site Scripting) | Injection of malicious scripts into web content viewed by other users; variants: reflected, stored, DOM-based. | 8 |
| **Zero Day** | Vulnerability unknown to the vendor with no available patch; highest value in exploit markets. | 26 |
| **Zero Trust** | Security model assuming no implicit trust; every access request is verified regardless of network location. | 27, 31 |
