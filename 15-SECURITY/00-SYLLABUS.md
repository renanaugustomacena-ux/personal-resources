# Syllabus — Cybersecurity Masterclass

> **Last updated:** 2026-05-29

This syllabus covers **31 security domains** across **70 chapter files** and **25 tutorial labs** (domains 1-11). Domains are sequenced from low-level foundations upward: binary formats, OS internals, memory corruption, exploit primitives, then defensive and applied security disciplines.

---

## Learning Path Overview

| # | Domain | Chapters | Tutorials | Est. Hours | Difficulty |
|---|--------|----------|-----------|------------|------------|
| 1 | Binary Analysis (ELF & PE) | 3 | 3 | 30 | Intermediate |
| 2 | OS Internals & Memory Management | 3 | 3 | 25 | Intermediate |
| 3 | Memory Corruption | 2 | 2 | 30 | Advanced |
| 4 | Code Reuse & Control Flow Attacks | 2 | 2 | 25 | Advanced |
| 5 | Kernel Exploitation | 2 | 2 | 35 | Expert |
| 6 | Mitigation Bypass | 2 | 2 | 30 | Expert |
| 7 | Side Channels & Hardware Vulnerabilities | 2 | 2 | 25 | Expert |
| 8 | Web Security | 3 | 3 | 30 | Intermediate-Advanced |
| 9 | Network Security | 2 | 2 | 20 | Intermediate |
| 10 | Cloud Security | 2 | 2 | 25 | Intermediate-Advanced |
| 11 | Malware & EDR Evasion | 2 | 2 | 30 | Advanced |
| 12 | Reverse Engineering | 2 | -- | 25 | Advanced |
| 13 | Cryptography | 2 | -- | 25 | Advanced |
| 14 | Active Directory & Windows | 2 | -- | 25 | Advanced |
| 15 | Mobile Security | 2 | -- | 20 | Intermediate-Advanced |
| 16 | ICS/OT Security | 2 | -- | 20 | Advanced |
| 17 | Physical & Hardware Security | 4 | -- | 30 | Advanced-Expert |
| 18 | Adversarial ML | 1 | -- | 20 | Advanced |
| 19 | Supply Chain Security | 3 | -- | 20 | Advanced |
| 20 | RF & Software-Defined Radio | 2 | -- | 20 | Advanced |
| 21 | Automotive Security | 2 | -- | 15 | Advanced |
| 22 | Fintech & Blockchain Security | 4 | -- | 30 | Advanced |
| 23 | Social Engineering & OSINT | 2 | -- | 15 | Intermediate |
| 24 | Digital Forensics & Incident Response | 2 | -- | 25 | Intermediate-Advanced |
| 25 | Threat Intelligence | 2 | -- | 20 | Intermediate-Advanced |
| 26 | Exploit Development | 2 | -- | 30 | Expert |
| 27 | Secure Architecture & Defense Engineering | 3 | -- | 25 | Intermediate-Advanced |
| 28 | IoT Security | 2 | -- | 20 | Intermediate-Advanced |
| 29 | Ransomware Operations | 2 | -- | 15 | Advanced |
| 30 | C2 Frameworks & Credential Theft | 2 | -- | 20 | Advanced |
| 31 | SIEM/SOAR & Detection Engineering | 2 | -- | 25 | Advanced |
| | **TOTAL** | **70** | **25** | **~770** | |

---

## Domain 1 — Binary Analysis (ELF & PE)

| Chapter | File | Description |
|---------|------|-------------|
| 1A | [ELF Foundations](domain1_chapter1A_elf_foundations.md) | ELF header, program/section headers, dynamic linking, GOT/PLT, lazy binding |
| 1B | [ELF Advanced](domain1_chapter1B_elf_advanced.md) | TLS, IFUNC, security segments, unwinding, symbol versioning |
| 2 | [PE/COFF](domain1_chapter2_pe_coff.md) | Windows PE/COFF binary format internals |

**Tutorials:**
- [ELF Foundations Lab](tutorials/tutorial_domain1_ch1A_elf_lab.md)
- [ELF Advanced Lab](tutorials/tutorial_domain1_ch1B_elf_advanced_lab.md)
- [PE/COFF Lab](tutorials/tutorial_domain1_ch2_pe_coff_lab.md)

---

## Domain 2 — OS Internals & Memory Management

| Chapter | File | Description |
|---------|------|-------------|
| 2A | [Process Address Space](domain2_chapter2A_process_memory.md) | Process memory layout, virtual memory management |
| 2B | [Syscall, Seccomp, Ptrace](domain2_chapter2B_syscall_seccomp_ptrace.md) | System call dispatch, seccomp filters, process interaction primitives |
| 2C | [Capabilities, Namespaces, LSMs](domain2_chapter2C_caps_ns_lsm.md) | Linux capabilities, namespaces, cgroups, LSMs, kernel memory security |

**Tutorials:**
- [Process Memory Lab](tutorials/tutorial_domain2_ch2A_process_memory_lab.md)
- [Syscall/Seccomp Lab](tutorials/tutorial_domain2_ch2B_syscall_seccomp_lab.md)
- [Capabilities/Namespaces/LSM Lab](tutorials/tutorial_domain2_ch2C_caps_ns_lsm_lab.md)

---

## Domain 3 — Memory Corruption

| Chapter | File | Description |
|---------|------|-------------|
| 3A | [Stack, Format Strings, Integers](domain3_chapter3A_stack_format_integer.md) | Stack buffer overflows, format string bugs, integer errors |
| 3B | [Heap Exploitation](domain3_chapter3B_heap_uaf.md) | ptmalloc2 internals, use-after-free, type confusion |

**Tutorials:**
- [Stack Exploits Lab](tutorials/tutorial_domain3_ch3A_stack_exploits_lab.md)
- [Heap/UAF Lab](tutorials/tutorial_domain3_ch3B_heap_uaf_lab.md)

---

## Domain 4 — Code Reuse & Control Flow Attacks

| Chapter | File | Description |
|---------|------|-------------|
| 4A | [Code Reuse Attacks](domain4_code_reuse_attacks.md) | ROP, JOP, code reuse and control flow attack foundations |
| 4B | [CFI & Hardware Bypass](domain4_chapter4B_cfi_hardware_bypass.md) | Hardware-enforced CFI internals, bypass techniques, detection engineering |

**Tutorials:**
- [ROP/JOP Lab](tutorials/tutorial_domain4_ch4A_rop_jop_lab.md)
- [CFI Bypass Lab](tutorials/tutorial_domain4_ch4B_cfi_bypass_lab.md)

---

## Domain 5 — Kernel Exploitation

| Chapter | File | Description |
|---------|------|-------------|
| 5A | [Kernel Heap & Exploitation Primitives](domain5_chapter5A_kernel_exploitation.md) | Kernel heap, exploitation primitives, hardware mitigations |
| 5B | [Subsystem Attack Surfaces](domain5_chapter5B_subsystem_seccomp.md) | Subsystem attack surfaces, seccomp, constrained exploitation |

**Tutorials:**
- [Kernel Exploit Lab](tutorials/tutorial_domain5_ch5A_kernel_exploit_lab.md)
- [Subsystem Lab](tutorials/tutorial_domain5_ch5B_subsystem_lab.md)

---

## Domain 6 — Mitigation Bypass

| Chapter | File | Description |
|---------|------|-------------|
| 6A | [Mitigation Bypass Techniques](domain6_mitigation_bypass.md) | ASLR, DEP, stack canary, and RELRO bypass techniques |
| 6B | [Kernel Mitigation Bypass](domain6_chapter6B_kernel_mitigation_bypass.md) | Kernel mitigation bypass and combined exploit primitive chains |

**Tutorials:**
- [Mitigation Bypass Lab](tutorials/tutorial_domain6_ch6A_mitigation_bypass_lab.md)
- [Kernel Bypass Lab](tutorials/tutorial_domain6_ch6B_kernel_bypass_lab.md)

---

## Domain 7 — Side Channels & Hardware Vulnerabilities

| Chapter | File | Description |
|---------|------|-------------|
| 7A | [Spectre & Side Channels](domain7_chapter7A_spectre_sidechannels.md) | Spectre variants and microarchitectural side channels |
| 7B | [SGX, Rowhammer, Hardware](domain7_chapter7B_sgx_rowhammer_hw.md) | SGX security, Rowhammer, hardware vulnerability taxonomy |

**Tutorials:**
- [Spectre Lab](tutorials/tutorial_domain7_ch7A_spectre_lab.md)
- [SGX/Rowhammer Lab](tutorials/tutorial_domain7_ch7B_sgx_rowhammer_lab.md)

---

## Domain 8 — Web Security

| Chapter | File | Description |
|---------|------|-------------|
| 8A | [Client-Side & Auth](domain8_chapter8A_clientside_auth.md) | XSS, CSRF, authentication and session security |
| 8B | [Server-Side & API](domain8_chapter8B_serverside_api.md) | SSRF, injection, API security, deserialization |
| 8C | [Browser Internals](domain8_chapter8C_browser_internals.md) | V8 engine, browser sandbox architecture, renderer exploitation |

**Tutorials:**
- [XSS/CSRF/Auth Lab](tutorials/tutorial_domain8_ch8A_xss_csrf_auth_lab.md)
- [Server-Side/API Lab](tutorials/tutorial_domain8_ch8B_serverside_api_lab.md)
- [Browser Internals Lab](tutorials/tutorial_domain8_ch8C_browser_internals_lab.md)

---

## Domain 9 — Network Security

| Chapter | File | Description |
|---------|------|-------------|
| 9A | [TCP/IP, DNS, TLS](domain9_chapter9A_tcp_dns_tls.md) | Protocol-level security for TCP/IP, DNS, and TLS |
| 9B | [L2, Wireless, Telecom, SDN](domain9_chapter9B_l2_wireless_telecom_sdn.md) | Layer 2 attacks, wireless, telecom, and SDN security |

**Tutorials:**
- [TCP/DNS/TLS Lab](tutorials/tutorial_domain9_ch9A_tcp_dns_tls_lab.md)
- [L2/Wireless Lab](tutorials/tutorial_domain9_ch9B_l2_wireless_lab.md)

---

## Domain 10 — Cloud Security

| Chapter | File | Description |
|---------|------|-------------|
| 10A | [Cloud Providers](domain10_chapter10A_cloud_providers.md) | AWS, GCP, Azure security — IAM, metadata, misconfigurations |
| 10B | [Containers, K8s, Serverless](domain10_chapter10B_container_k8s_serverless.md) | Container escapes, Kubernetes RBAC, serverless attack surfaces |

**Tutorials:**
- [Cloud Attack Lab](tutorials/tutorial_domain10_ch10A_cloud_attack_lab.md)
- [Container/K8s Lab](tutorials/tutorial_domain10_ch10B_container_k8s_lab.md)

---

## Domain 11 — Malware & EDR Evasion

| Chapter | File | Description |
|---------|------|-------------|
| 11A | [Malware Architecture & C2](domain11_chapter11A_malware_c2.md) | Injection, rootkits, shellcode, C2 protocols |
| 11B | [EDR Evasion](domain11_chapter11B_edr_evasion_platform.md) | EDR evasion and platform-specific malware tradecraft |

**Tutorials:**
- [Malware/C2 Lab](tutorials/tutorial_domain11_ch11A_malware_c2_lab.md)
- [EDR Evasion Lab](tutorials/tutorial_domain11_ch11B_edr_evasion_lab.md)

---

## Domain 12 — Reverse Engineering

| Chapter | File | Description |
|---------|------|-------------|
| 12A | [Static & Dynamic Analysis](domain12_chapter12A_static_dynamic_analysis.md) | Disassembly, decompilation, dynamic analysis workflows |
| 12B | [Firmware & Embedded RE](domain12_chapter12B_firmware_embedded.md) | Firmware extraction, embedded and hardware reverse engineering |

*No tutorials yet.*

---

## Domain 13 — Cryptography

| Chapter | File | Description |
|---------|------|-------------|
| 13A | [Symmetric, Asymmetric, Post-Quantum](domain13_chapter13A_cryptography.md) | AES, RSA, ECC, lattice-based post-quantum schemes |
| 13B | [Protocol Attacks](domain13_chapter13B_protocol_attacks.md) | TLS downgrade, padding oracles, nonce reuse, protocol-level attacks |

*No tutorials yet.*

---

## Domain 14 — Active Directory & Windows

| Chapter | File | Description |
|---------|------|-------------|
| 14A | [Active Directory Attacks](domain14_chapter14A_active_directory.md) | Kerberoasting, AS-REP roasting, delegation abuse, AD ACL attacks |
| 14B | [Windows Internals & Exchange](domain14_chapter14B_windows_exchange.md) | Windows internals, Exchange exploitation, Microsoft 365 |

*No tutorials yet.*

---

## Domain 15 — Mobile Security

| Chapter | File | Description |
|---------|------|-------------|
| 15A | [Android Security](domain15_chapter15A_android.md) | Android app analysis, root detection bypass, kernel |
| 15B | [iOS & Mobile Networks](domain15_chapter15B_ios_mobile_network.md) | iOS security model, mobile network architecture |

*No tutorials yet.*

---

## Domain 16 — ICS/OT Security

| Chapter | File | Description |
|---------|------|-------------|
| 16A | [ICS/OT Foundations](domain16_ics_ot_security.md) | Industrial control systems, OT security fundamentals |
| 16B | [ICS Attacks & Defense](domain16_chapter16B_ics_attacks_defense.md) | ICS/OT attack case studies, network architecture, defense strategies |

*No tutorials yet.*

---

## Domain 17 — Physical & Hardware Security

| Chapter | File | Description |
|---------|------|-------------|
| 17A | [Physical & Hardware Foundations](domain17_physical_hardware_security.md) | Physical security, hardware attack surfaces, side-channel overview |
| 17B | [Fault Injection](domain17_chapter17B_fault_injection.md) | Voltage glitching, EM fault injection, laser FI, countermeasures |
| 17C | [PCB RE & Chip Analysis](domain17_chapter17C_pcb_re_chip_analysis.md) | PCB reverse engineering and chip-level analysis |
| 17D | [Debug & Secure Boot Bypass](domain17_chapter17D_debug_secureboot_bypass.md) | JTAG/SWD, secure boot architectures and bypass techniques |

*No tutorials yet.*

---

## Domain 18 — Adversarial Machine Learning

| Chapter | File | Description |
|---------|------|-------------|
| 18 | [Adversarial ML](domain18_adversarial_ml.md) | Evasion, poisoning, model extraction, LLM security, deepfakes, ML supply chain |

*No tutorials yet.*

---

## Domain 19 — Supply Chain Security

| Chapter | File | Description |
|---------|------|-------------|
| 19A | [Supply Chain Foundations](domain19_supply_chain.md) | Software supply chain attack taxonomy, SBOMs, dependency risks |
| 19B | [Supply Chain Defense](domain19_chapter19B_supply_chain_defense.md) | xz backdoor analysis, CI/CD hardening, software supply chain defenses |
| 19C | [Hardware Supply Chain](domain19_chapter19C_hardware_supply_chain.md) | Counterfeit ICs, hardware trojans, trust architectures |

*No tutorials yet.*

---

## Domain 20 — RF & Software-Defined Radio

| Chapter | File | Description |
|---------|------|-------------|
| 20A | [RF/SDR Foundations](domain20_rf_sdr.md) | Radio frequency fundamentals, SDR tooling, signal analysis |
| 20B | [RF Exploitation](domain20_chapter20B_rf_attacks_exploitation.md) | RF protocol exploitation, SIGINT, RF defense |

*No tutorials yet.*

---

## Domain 21 — Automotive Security

| Chapter | File | Description |
|---------|------|-------------|
| 21A | [Vehicle Networks](domain21_chapter21A_vehicle_networks.md) | CAN bus, LIN, FlexRay, Automotive Ethernet protocols |
| 21B | [Vehicle Attacks](domain21_chapter21B_vehicle_attacks.md) | Vehicle-level attacks, sensor security, V2X exploitation |

*No tutorials yet.*

---

## Domain 22 — Fintech & Blockchain Security

| Chapter | File | Description |
|---------|------|-------------|
| 22A | [EMV Payment Security](domain22_chapter22A_emv.md) | EMV protocol, chip authentication, relay attacks |
| 22B | [ATM & POS Security](domain22_chapter22B_atm_pos.md) | ATM jackpotting, POS skimming, payment infrastructure |
| 22C | [Bitcoin, Ethereum, Smart Contracts](domain22_chapter22C_crypto_blockchain.md) | Cryptocurrency fundamentals, smart contract vulnerabilities |
| 22D | [Advanced Blockchain](domain22_chapter22D_advanced_blockchain.md) | Privacy coins, Layer 2, bridges, MEV exploitation |

*No tutorials yet.*

---

## Domain 23 — Social Engineering & OSINT

| Chapter | File | Description |
|---------|------|-------------|
| 23A | [Social Engineering & OSINT](domain23_social_engineering_osint.md) | Phishing, pretexting, vishing, open-source intelligence gathering |
| 23B | [Advanced OSINT & SE Defense](domain23_chapter23B_osint_tradecraft_se_defense.md) | OSINT tradecraft, counter-intelligence, social engineering defense |

*No tutorials yet.*

---

## Domain 24 — Digital Forensics & Incident Response

| Chapter | File | Description |
|---------|------|-------------|
| 24A | [DFIR Foundations](domain24_dfir.md) | Disk forensics, memory forensics, evidence handling, chain of custody |
| 24B | [Cloud & Container IR](domain24_chapter24B_cloud_forensics_ir.md) | Cloud forensics, container IR, enterprise IR playbooks |

*No tutorials yet.*

---

## Domain 25 — Threat Intelligence

| Chapter | File | Description |
|---------|------|-------------|
| 25A | [Threat Intelligence Foundations](domain25_threat_intelligence.md) | Intelligence cycle, diamond model, adversary tracking |
| 25B | [Operationalizing TI](domain25_chapter25B_operationalizing_ti.md) | Indicator lifecycle, STIX/TAXII, TI platform integration |

*No tutorials yet.*

---

## Domain 26 — Exploit Development

| Chapter | File | Description |
|---------|------|-------------|
| 26A | [Vulnerability Discovery](domain26_chapter26A_vuln_discovery.md) | Fuzzing, static analysis, variant analysis, bug hunting |
| 26B | [Exploit Development](domain26_chapter26B_exploit_dev.md) | Exploit primitives, weaponization, reliability engineering |

*No tutorials yet.*

---

## Domain 27 — Secure Architecture & Defense Engineering

| Chapter | File | Description |
|---------|------|-------------|
| 27A | [Secure Architecture Foundations](domain27_secure_architecture_detection.md) | Defense-in-depth, security architecture principles |
| 27B | [Zero Trust & Defensive Design](domain27_chapter27B_zero_trust_defense.md) | Zero trust architecture, defensive system design |
| 27C | [Detection Engineering & SecOps](domain27_chapter27C_detection_engineering_secops.md) | Detection engineering, security operations, purple teaming |

*No tutorials yet.*

---

## Domain 28 — IoT Security

| Chapter | File | Description |
|---------|------|-------------|
| 28A | [IoT Protocols](domain28_chapter28A_iot_protocols.md) | MQTT, CoAP, Zigbee, BLE protocol security |
| 28B | [IoT Device Security](domain28_chapter28B_iot_device_security.md) | Firmware analysis, device hardening, IoT-specific attack surfaces |

*No tutorials yet.*

---

## Domain 29 — Ransomware Operations

| Chapter | File | Description |
|---------|------|-------------|
| 29A | [Ransomware Operations](domain29_chapter29A_ransomware_operations.md) | Ransomware kill chain, enterprise attack chains, RaaS economics |
| 29B | [Campaign Dissections](domain29_chapter29B_campaign_dissections.md) | Real-world ransomware campaign analysis and post-mortems |

*No tutorials yet.*

---

## Domain 30 — C2 Frameworks & Credential Theft

| Chapter | File | Description |
|---------|------|-------------|
| 30A | [C2 Framework Internals](domain30_chapter30A_c2_framework_internals.md) | Cobalt Strike, Mythic, Sliver — C2 protocol design and detection |
| 30B | [Credential Theft & Identity Attacks](domain30_chapter30B_credential_theft_identity_attacks.md) | LSASS dumping, Kerberos ticket extraction, identity attack chains |

*No tutorials yet.*

---

## Domain 31 — SIEM/SOAR & Detection Engineering

| Chapter | File | Description |
|---------|------|-------------|
| 31A | [SIEM/SOAR Pipeline Design](domain31_chapter31A_siem_soar_detection_engineering.md) | Log pipeline, Sigma rules, Detection-as-Code, SOAR playbooks |
| 31B | [Runtime Security & Zero Trust](domain31_chapter31B_runtime_security_zero_trust.md) | eBPF runtime security, zero trust enforcement at scale |

*No tutorials yet.*

---

## Supplementary Materials

| Resource | Location |
|----------|----------|
| [Continuation Prompt](CONTINUATION_PROMPT.md) | Library architecture and expansion instructions |
| [Syllabus](00-SYLLABUS.md) | This file |
| [Alphabetical Index](00-INDEX.md) | Topic cross-reference |
| [Glossary](00-GLOSSARY.md) | 100 key security terms |
| [Bibliography](00-BIBLIOGRAPHY.md) | Authoritative sources |
| [Capstone Project](00-CAPSTONE.md) | Multi-domain security assessment |
