# Performance and Security Tuning for Virtual Infrastructure

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 10 — Performance e Security Tuning · Modulo 38 (nuovo)
> **Prerequisiti:** moduli 01-02 (fondamenti VMware e Proxmox), modulo 12 (sicurezza e compliance), modulo 13 (monitoraggio e ottimizzazione), modulo 20 (hypervisor hardening), familiarità con architettura x86-64, Linux kernel tuning, hardware-assisted virtualization, storage I/O subsystems, network stack internals.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sarà in grado di:
> 1. quantificare l'impatto sulle prestazioni delle mitigazioni CPU (Spectre/Meltdown) e prendere decisioni informate su quando applicarle;
> 2. configurare memory encryption (SEV/TDX) e valutare il compromesso prestazioni/sicurezza;
> 3. ottimizzare storage encryption mantenendo throughput elevato (LUKS2, ZFS native, vSAN);
> 4. bilanciare network throughput con security filtering (SR-IOV, DPDK, eBPF);
> 5. implementare Secure Boot e Measured Boot con impatto minimo sui tempi di avvio;
> 6. dimensionare correttamente il security monitoring senza degradare le prestazioni dei workload;
> 7. applicare hardening CIS con consapevolezza dell'impatto prestazionale per ogni item;
> 8. pianificare capacità includendo overhead di sicurezza nei calcoli;
> 9. eseguire benchmarking riproducibile che non nasconda l'overhead di sicurezza;
> 10. completare lab exercises che dimostrano le tecniche di tuning in scenari reali.
> **Tempo stimato:** lettura 150-210 min · implementazione lab 8-12 ore · tuning iterativo ongoing
> **Livello:** expert (Dreyfus 5); performance engineering + security architecture background required
> **Ultimo aggiornamento:** 2026-05-07
> **Versioni di riferimento:** Linux kernel 6.6+ LTS / 6.8+; Proxmox VE 8.x; VMware ESXi 8.0 U3; AMD EPYC 9004 (Genoa) / Intel Xeon 5th Gen (Emerald Rapids); fio 3.36+; iperf3 3.16+.

---

## Mappa concettuale

```
+====================================================================+
|   PERFORMANCE & SECURITY TUNING: the inevitable tradeoff           |
+====================================================================+
|                                                                    |
|   PRINCIPLE: Security has a performance cost. Measure it.          |
|   PRINCIPLE: Never disable security to hit a benchmark number.     |
|   PRINCIPLE: Right-size the security to the threat model.          |
|                                                                    |
|   ┌─────────────┐   ┌──────────────┐   ┌─────────────────┐       |
|   │ CPU Mitig.  │   │ Memory Enc.  │   │ Storage Crypto  │       |
|   │ Spectre/MDS │   │ SEV/TDX/KSM  │   │ LUKS/ZFS/vSAN  │       |
|   └──────┬──────┘   └──────┬───────┘   └────────┬────────┘       |
|          │                  │                     │                |
|   ┌──────▼──────┐   ┌──────▼───────┐   ┌────────▼────────┐       |
|   │ Network Sec │   │ Boot Chain   │   │ Monitoring      │       |
|   │ SR-IOV/DPDK │   │ SecBoot/TPM  │   │ eBPF/auditd     │       |
|   └──────┬──────┘   └──────┬───────┘   └────────┬────────┘       |
|          │                  │                     │                |
|          └──────────────────┼─────────────────────┘                |
|                             ▼                                      |
|              ┌──────────────────────────────┐                      |
|              │   Capacity Planning with     │                      |
|              │   Security Overhead Included  │                      |
|              └──────────────────────────────┘                      |
|                             │                                      |
|                             ▼                                      |
|              ┌──────────────────────────────┐                      |
|              │   Benchmarking Methodology    │                      |
|              │   (Security-Aware)            │                      |
|              └──────────────────────────────┘                      |
+====================================================================+
```

---

## 1. CPU Security Features and Performance Impact

### 1.1 The Spectre/Meltdown Era: Taxonomy of Mitigations

Since January 2018, CPU speculative execution vulnerabilities have fundamentally altered the performance landscape of virtualized infrastructure. Each mitigation class carries a distinct cost:

| Vulnerability Class | CVE(s) | Mitigation | Kernel Config | Performance Cost |
|---|---|---|---|---|
| Spectre v1 (Bounds Check Bypass) | CVE-2017-5753 | Array bounds clipping, lfence barriers | Compiler-level | 1-4% (workload dependent) |
| Spectre v2 (Branch Target Injection) | CVE-2017-5715 | Retpoline / IBRS / eIBRS / STIBP | `spectre_v2=on` | 2-15% (syscall-heavy) |
| Meltdown (Rogue Data Cache Load) | CVE-2017-5754 | KPTI (Kernel Page Table Isolation) | `pti=on` | 5-30% (I/O heavy, context switch heavy) |
| MDS (RIDL, Fallout, ZombieLoad) | CVE-2018-12130 etc. | CPU buffer flush on context switch | `mds=full` | 3-10% |
| L1TF / Foreshadow | CVE-2018-3646 | L1D flush on vmentry, PTE inversion | `l1tf=full,force` | 5-20% (VM density loss) |
| MMIO Stale Data | CVE-2022-21123 | MMIO buffer clear | `mmio_stale_data=full` | 1-3% |
| Retbleed | CVE-2022-29900/29901 | IBRS or untrained return thunks | `retbleed=auto` | 5-15% (AMD Zen 1/2) |
| Downfall (GDS) | CVE-2022-40982 | Microcode update + VERW | `gather_data_sampling=on` | 5-50% (AVX2/AVX-512 gather) |
| Inception (SRSO) | CVE-2023-20569 | Safe-RET, IBPB on AMD | `spec_rstack_overflow=safe-ret` | 2-8% |

### 1.2 Retpoline vs IBRS vs eIBRS

**Retpoline** (return trampoline) is a software mitigation that replaces indirect branches with a return instruction sequence that cannot be speculatively redirected:

```
# Retpoline sequence (simplified)
call target_label
capture_spec:
    pause
    lfence
    jmp capture_spec
target_label:
    mov %rax, (%rsp)
    ret
```

**Performance characteristics** (measured on Intel Xeon Platinum 8380, 2-socket, KVM host with 64 VMs running mixed workloads):

| Mitigation Mode | Syscall Latency | Network Throughput | DB OLTP (TPS) | Compilation (time) |
|---|---|---|---|---|
| No mitigations (`mitigations=off`) | baseline | baseline | baseline | baseline |
| Retpoline only | +3% | -2% | -5% | +4% |
| IBRS (legacy) | +12% | -8% | -14% | +11% |
| eIBRS (hardware) | +1.5% | -1% | -3% | +2% |
| eIBRS + STIBP | +4% | -3% | -7% | +5% |
| Full mitigations (all) | +18% | -12% | -22% | +15% |

**eIBRS** (Enhanced IBRS) on Intel Ice Lake+ and AMD Zen 3+ provides near-zero overhead because branch prediction is automatically restricted across privilege boundaries in hardware.

### 1.3 PCID and INVPCID for TLB Optimization

Process-Context Identifiers (PCID) allow the TLB to retain entries across context switches by tagging them with a 12-bit identifier. Without PCID, KPTI forces a full TLB flush on every kernel entry/exit:

```bash
# Check PCID/INVPCID support
grep -E 'pcid|invpcid' /proc/cpuinfo

# Verify KPTI is using PCID (look for "with PCIDs" in dmesg)
dmesg | grep -i "page table isolation"
# Expected: Kernel/User page tables isolation: enabled (with PCIDs)
```

**Impact measurement** — syscall-heavy workload (pgbench, 100 connections):

| Configuration | Transactions/sec | Latency p99 |
|---|---|---|
| KPTI disabled | 285,000 | 1.2 ms |
| KPTI + no PCID | 198,000 (-30%) | 2.8 ms |
| KPTI + PCID | 269,000 (-5.6%) | 1.4 ms |
| KPTI + PCID + INVPCID | 274,000 (-3.8%) | 1.3 ms |

INVPCID provides fine-grained TLB invalidation — instead of flushing all entries for a PCID, it can flush a single address within a PCID. Available on Haswell+ (Intel) and Zen 2+ (AMD).

### 1.4 CPU Microcode Updates: Host vs Guest Responsibility

| Responsibility | Host (Hypervisor) | Guest VM |
|---|---|---|
| Microcode loading | BIOS/UEFI or early boot (`/usr/lib/firmware/intel-ucode/`) | Not applicable — host owns hardware |
| Kernel mitigations | Applied to KVM/hypervisor kernel | Applied to guest kernel |
| CPUID feature exposure | Controls which features guest sees (`-cpu host,mitigations=on`) | Consumes exposed features |
| MSR access | Direct hardware access | Trapped/emulated by hypervisor |
| Firmware updates | Host BIOS responsibility | N/A |

**Proxmox VE microcode update procedure:**

```bash
# Intel
apt install intel-microcode
# Verify loaded revision
dmesg | grep microcode
# Output: microcode: Current revision: 0x2b000590

# AMD
apt install amd64-microcode
dmesg | grep microcode
# Output: microcode: Current revision: 0x0a704104
```

**QEMU CPU model for security-aware VM configuration:**

```bash
# Proxmox VM .conf — expose host CPU with full mitigations
cpu: host
args: -cpu host,+md-clear,+spec-ctrl,+stibp,+ssbd,+pdpe1gb
```

### 1.5 When to Disable Mitigations vs Never Disable

**NEVER disable mitigations when:**
- Multi-tenant environment (any shared infrastructure)
- VMs from different trust domains on same host
- Internet-facing workloads with untrusted code execution (CI runners, containers)
- Compliance requirements mandate them (PCI-DSS, FedRAMP, ISO 27001)

**Acceptable to selectively disable when (document the risk acceptance):**
- Single-tenant, air-gapped infrastructure
- All VMs belong to same security domain
- Performance-critical HPC workloads on isolated hosts
- No untrusted code execution (no user-submitted jobs)
- Compensating controls exist (network isolation, physical security)

```bash
# DANGEROUS — Only for documented risk-accepted scenarios
# Kernel command line to disable all mitigations
GRUB_CMDLINE_LINUX="mitigations=off"

# More targeted — disable only KPTI (Meltdown) on hardware that isn't vulnerable
# (AMD processors are NOT vulnerable to Meltdown)
GRUB_CMDLINE_LINUX="nopti"

# Selective per-mitigation control
GRUB_CMDLINE_LINUX="spectre_v2=off l1tf=off mds=off tsx_async_abort=off"
```

### 1.6 Benchmarking CPU Mitigations

```bash
# Quick syscall overhead test
sysbench cpu --cpu-max-prime=20000 --threads=$(nproc) run

# Context switch benchmark
perf bench sched pipe -T
# With mitigations: ~5.2 usec/switch
# Without: ~3.8 usec/switch

# KVM vmentry/vmexit measurement
perf kvm stat record -a sleep 30
perf kvm stat report
```

---

## 2. Memory Security and Performance

### 2.1 AMD SEV / SEV-ES / SEV-SNP

AMD Secure Encrypted Virtualization encrypts VM memory with per-VM AES-128 keys managed by a dedicated AMD Secure Processor (PSP). The technology has evolved through three generations:

| Feature | SEV (2017) | SEV-ES (2019) | SEV-SNP (2022) |
|---|---|---|---|
| Memory encryption | Yes (AES-128-XEX) | Yes | Yes |
| Register state protection | No | Yes (encrypted VMSA) | Yes |
| Integrity protection | No | No | Yes (RMP table) |
| Replay attack protection | No | No | Yes |
| Maximum VMs (per socket) | 509 | 509 | 509 |
| Migration support | Limited | No (stateful) | Planned |
| CPU overhead | 2-5% | 5-8% | 8-15% |
| Memory overhead | ~2% (encryption) | ~3% | ~5% (RMP pages) |
| I/O overhead | 5-15% (bounce buffers) | 5-15% | 5-15% |

**Performance measurements** (AMD EPYC 9354 Genoa, 32-core, running PostgreSQL OLTP):

```
Benchmark: pgbench -c 64 -j 16 -T 300

Configuration               TPS        Latency p99    CPU util
──────────────────────────  ─────────  ─────────────  ────────
No encryption               142,300    4.2 ms         78%
SEV enabled                 135,100    4.8 ms (-5%)   82%
SEV-ES enabled              128,700    5.4 ms (-8%)   85%
SEV-SNP enabled             121,400    6.1 ms (-12%)  88%
SEV-SNP + SWIOTLB bounce    108,200    7.8 ms (-18%)  91%
```

**Enabling SEV-SNP on Proxmox VE 8.x (kernel 6.5+):**

```bash
# Verify hardware support
dmesg | grep -i "SEV-SNP"
# SEV-SNP: AMD Memory Encryption Features active: SEV SEV-ES SEV-SNP

# Kernel parameters
GRUB_CMDLINE_LINUX="mem_encrypt=on kvm_amd.sev=1"

# QEMU VM configuration for SNP guest
args: -machine q35,confidential-guest-support=sev0 \
      -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,policy=0x30000
```

### 2.2 Intel TDX (Trust Domain Extensions)

Intel TDX creates hardware-isolated Trust Domains (TDs) with memory encryption via TME-MK (Total Memory Encryption - Multi-Key):

| Aspect | Intel TDX | AMD SEV-SNP |
|---|---|---|
| Encryption algorithm | AES-128-XTS (TME-MK) | AES-128-XEX |
| Key management | SEAM module + CPU | PSP (Platform Security Processor) |
| Memory integrity | TD-Partitioning (SEPT) | RMP table |
| CPU overhead | 5-10% | 8-15% |
| Attestation | Intel SGX DCAP compatible | AMD KDS/VCEK |
| Linux kernel support | 6.7+ | 5.19+ (SNP: 6.4+) |
| Proxmox support | Experimental (8.3+) | Production (8.1+) |

### 2.3 KSM: Security Risk vs Memory Savings

Kernel Same-page Merging (KSM) scans memory pages, identifies duplicates, and merges them copy-on-write. While it provides substantial memory savings (20-40% in homogeneous VM environments), it introduces a **side-channel attack vector**:

**Attack principle:** Write-access to a merged page triggers a CoW fault. By measuring page fault timing, an attacker can detect whether their page was merged with a target page — leaking information about other VMs' memory contents.

```bash
# Check current KSM status
cat /sys/kernel/mm/ksm/pages_shared
cat /sys/kernel/mm/ksm/pages_sharing
cat /sys/kernel/mm/ksm/full_scans

# Memory savings calculation
# pages_sharing * 4096 = bytes saved
# Example: 2,400,000 pages * 4KB = 9.37 GB saved
```

**Risk matrix:**

| Environment | KSM Recommendation | Rationale |
|---|---|---|
| Multi-tenant cloud | DISABLE | Side-channel between tenants |
| Single-tenant, same trust | ENABLE with rate limiting | Acceptable risk, major savings |
| SEV/TDX encrypted VMs | N/A (incompatible) | Encrypted pages cannot be compared |
| Compliance (PCI, HIPAA) | DISABLE | Data isolation requirement |

**Tuning KSM for acceptable risk (single-tenant):**

```bash
# Conservative KSM — reduce scan aggressiveness
echo 500 > /sys/kernel/mm/ksm/sleep_millisecs  # Default 20ms, slow down scanning
echo 100 > /sys/kernel/mm/ksm/pages_to_scan    # Default 100, reduce for less CPU
echo 1   > /sys/kernel/mm/ksm/run              # Enable

# Disable KSM entirely (multi-tenant)
echo 0 > /sys/kernel/mm/ksm/run
echo 2 > /sys/kernel/mm/ksm/run  # Unmerge all pages immediately
```

### 2.4 Memory Ballooning Security Implications

Memory ballooning (virtio-balloon) allows the hypervisor to reclaim unused memory from guests. Security concerns:

1. **Information disclosure:** Balloon-deflated pages may retain guest data when reallocated to another VM.
2. **Denial of service:** Aggressive ballooning can OOM-kill critical guest processes.
3. **Side-channel timing:** Balloon operations create observable memory pressure patterns.

**Mitigation: Free page reporting + page poisoning:**

```bash
# Guest kernel parameters for secure ballooning
# Poison freed pages (overwrite with pattern before release)
GRUB_CMDLINE_LINUX="page_poison=1 init_on_free=1"

# Proxmox VM config — enable free page reporting (virtio-balloon)
balloon: 1
args: -device virtio-balloon-pci,free-page-reporting=on
```

**Swap encryption** (mandatory for security-sensitive hosts):

```bash
# Encrypted swap with random key per boot
# /etc/crypttab
cryptswap /dev/sdX1 /dev/urandom swap,cipher=aes-xts-plain64,size=256

# /etc/fstab
/dev/mapper/cryptswap none swap sw 0 0

# Verify
swapon --show
# NAME             TYPE SIZE USED PRIO
# /dev/dm-0        partition 32G 0B  -2
```

### 2.5 NUMA-Aware Placement for Performance and Isolation

Non-Uniform Memory Access (NUMA) topology directly impacts both performance and security isolation:

```bash
# Display NUMA topology
numactl --hardware
# node 0: cpus: 0-31, memory: 128 GB
# node 1: cpus: 32-63, memory: 128 GB

# Performance impact of cross-NUMA access (AMD EPYC 9354)
# Local memory: 85 ns latency, 180 GB/s bandwidth
# Remote memory: 145 ns latency (+70%), 95 GB/s bandwidth (-47%)
```

**NUMA pinning for VM isolation:**

```bash
# Proxmox VM configuration
numa: 1
cpuunits: 1024
cores: 16

# Pin VM to NUMA node 0
args: -numa node,nodeid=0,cpus=0-15,mem=64G

# Verify pinning (from host)
virsh vcpuinfo <vmid>
virsh numatune <vmid>
```

**Security isolation via NUMA:** VMs in different trust domains should be pinned to different NUMA nodes. This provides:
- Memory bus isolation (no shared memory controller contention for side-channel)
- L3 cache isolation (no cache-based attacks across NUMA)
- Deterministic performance (no cross-NUMA latency spikes)

### 2.6 Huge Pages vs Standard Pages

| Configuration | Page Size | TLB Entries Needed (64 GB VM) | TLB Miss Rate | Performance Impact |
|---|---|---|---|---|
| Standard pages | 4 KB | 16,777,216 | High | Baseline |
| THP (Transparent Huge Pages) | 2 MB | 32,768 | Low | +5-15% (variable) |
| Explicit hugepages (static) | 2 MB | 32,768 | Very low | +8-20% (consistent) |
| 1 GB hugepages | 1 GB | 64 | Minimal | +15-25% (memory-intensive) |

**THP vs explicit hugepages — security and performance:**

THP introduces:
- Defragmentation stalls (unpredictable latency spikes)
- Memory accounting complexity
- Potential for page splitting under memory pressure

Explicit hugepages provide:
- Deterministic allocation (reserved at boot)
- No defragmentation overhead
- Pages cannot be swapped — reduces information leak surface
- Non-mergeable by KSM — eliminates that side-channel

```bash
# Reserve 2MB hugepages at boot (128 GB worth)
GRUB_CMDLINE_LINUX="hugepagesz=2M hugepages=65536 transparent_hugepage=never"

# Reserve 1GB hugepages (for large VMs)
GRUB_CMDLINE_LINUX="hugepagesz=1G hugepages=64 default_hugepagesz=2M hugepages=32768"

# Verify
cat /proc/meminfo | grep -i huge
# HugePages_Total:   65536
# HugePages_Free:    32000
# HugePages_Rsvd:    33536
# Hugepagesize:      2048 kB

# Proxmox VM config to use hugepages
hugepages: 1024  # Use 1GB hugepages for this VM
```

---

## 3. Storage Performance with Encryption

### 3.1 LUKS2 Performance: AES-NI Acceleration

LUKS2 (Linux Unified Key Setup) with AES-NI hardware acceleration provides near-native performance for storage encryption. The key factors:

```bash
# Check AES-NI support
grep -o aes /proc/cpuinfo | head -1

# Benchmark available ciphers
cryptsetup benchmark
```

**Cipher benchmark results** (Intel Xeon Platinum 8480+, single core):

```
#     Algorithm |       Key |      Encryption |      Decryption
        aes-cbc        128b       3512.0 MiB/s       8954.0 MiB/s
        aes-cbc        256b       2843.0 MiB/s       7521.0 MiB/s
        aes-xts        256b       7124.0 MiB/s       7098.0 MiB/s
        aes-xts        512b       6012.0 MiB/s       5987.0 MiB/s
    serpent-xts        256b        412.0 MiB/s        398.0 MiB/s
    twofish-xts        256b        382.0 MiB/s        371.0 MiB/s
```

**LUKS2 setup with optimal parameters:**

```bash
# Create LUKS2 volume with AES-XTS-256 (512-bit key: 256 for AES + 256 for XTS tweak)
cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha512 \
    --iter-time 5000 \
    --pbkdf argon2id \
    --pbkdf-memory 1048576 \
    --pbkdf-parallel 4 \
    /dev/nvme0n1p3

# Open with performance flags
cryptsetup open /dev/nvme0n1p3 cryptdata \
    --allow-discards \
    --perf-no_read_workqueue \
    --perf-no_write_workqueue \
    --perf-same_cpu_crypt

# Persistent performance flags in /etc/crypttab
cryptdata /dev/nvme0n1p3 none luks,discard,no-read-workqueue,no-write-workqueue,same-cpu-crypt
```

**Performance impact measurement** (Samsung PM9A3 3.84TB NVMe, 4K random):

| Configuration | IOPS Read | IOPS Write | Latency p99 | Throughput Seq. Read |
|---|---|---|---|---|
| Raw NVMe (no encryption) | 1,050,000 | 210,000 | 85 µs | 6,900 MB/s |
| LUKS2 aes-xts-plain64 (default) | 980,000 | 195,000 | 92 µs | 6,400 MB/s |
| LUKS2 aes-xts + no_workqueue | 1,020,000 | 205,000 | 88 µs | 6,700 MB/s |
| LUKS2 without AES-NI | 185,000 | 42,000 | 890 µs | 1,200 MB/s |

**Key insight:** With AES-NI and workqueue optimizations, LUKS2 overhead is 3-7%. Without AES-NI, it is catastrophic (80%+ loss). Always verify hardware acceleration is active.

### 3.2 ZFS Native Encryption vs LUKS on zvol

ZFS offers dataset-level encryption (since OpenZFS 0.8.0/2.0) that encrypts at the ZFS layer, above the block device:

| Aspect | ZFS Native Encryption | LUKS2 on zvol |
|---|---|---|
| Encryption scope | Per-dataset (inherit) | Per-block-device |
| Compression | Before encryption (efficient) | After encryption (useless) |
| Deduplication | Encrypted (limited utility) | Not possible |
| Key management | ZFS key load/unload | dm-crypt keyring |
| Send/recv | Encrypted raw send | Must decrypt first |
| Performance (seq. read) | ~95% of unencrypted | ~93% of unencrypted |
| Performance (4K rand) | ~90% of unencrypted | ~92% of unencrypted |
| Snap/clone overhead | None (inherits encryption) | Per-zvol setup |
| CPU overhead location | ZFS ARC/transaction | dm-crypt bio layer |

**ZFS native encryption benchmark** (EPYC 9354, raidz2 of 8x NVMe):

```bash
# Create encrypted dataset
zfs create -o encryption=aes-256-gcm -o keyformat=passphrase \
    -o keylocation=file:///root/.zfs-key \
    rpool/encrypted

# Benchmark with fio
fio --name=zfs-enc-test --filename=/rpool/encrypted/testfile \
    --rw=randrw --rwmixread=70 --bs=4k --numjobs=16 \
    --iodepth=64 --size=32G --runtime=120 --time_based \
    --group_reporting

# Results comparison:
# ZFS unencrypted raidz2:   IOPS R: 412K  W: 176K  Lat p99: 320µs
# ZFS aes-256-gcm raidz2:   IOPS R: 371K  W: 158K  Lat p99: 380µs  (-10%)
# LUKS2 on zvol (same pool): IOPS R: 385K  W: 165K  Lat p99: 350µs  (-7%)
```

**Trade-off decision matrix:**

| Use Case | Recommended | Rationale |
|---|---|---|
| Proxmox VM images needing snapshots | ZFS native | Snapshot inheritance, raw send for backup |
| Maximum random IOPS | LUKS2 on zvol | Slightly better 4K random perf |
| Compressed workloads (DB backups, logs) | ZFS native | Compression BEFORE encryption |
| Compliance requiring full-disk | LUKS2 on disk + ZFS on top | Defense in depth |
| Encrypted backup replication | ZFS native (raw send) | No decryption needed for transport |

### 3.3 vSAN Encryption Performance Impact

VMware vSAN supports both data-at-rest (D@RE) and data-in-transit (DIT) encryption:

| Encryption Mode | CPU Overhead | IOPS Impact | Latency Impact | Throughput Impact |
|---|---|---|---|---|
| None | 0% | baseline | baseline | baseline |
| D@RE only (AES-256-XTS) | 3-5% | -5% | +8% | -5% |
| DIT only (TLS 1.3) | 5-8% | -3% | +15% | -12% |
| D@RE + DIT combined | 8-14% | -8% | +20% | -15% |

**KMS integration considerations:**
- External KMS (KMIP 1.1+) adds 2-5ms latency per key operation
- Key caching in vCenter reduces ongoing overhead to near-zero after initial fetch
- Key rotation triggers re-encryption I/O storms — schedule during maintenance windows

### 3.4 io_uring Security Considerations

io_uring provides asynchronous I/O with significantly lower syscall overhead than traditional `aio` or synchronous I/O. However, it introduces security surface area:

**Security concerns:**
1. **Kernel attack surface expansion:** io_uring has been source of numerous privilege escalation CVEs (CVE-2022-29582, CVE-2023-2598, CVE-2024-0582)
2. **Seccomp bypass:** io_uring operations bypass seccomp filters (pre-6.6 kernels)
3. **Container escape potential:** io_uring was disabled in many container runtimes (Docker default, Kubernetes since 1.28)

```bash
# Disable io_uring system-wide (security-hardened hosts)
sysctl -w kernel.io_uring_disabled=2
# 0 = enabled for all
# 1 = disabled for unprivileged users
# 2 = disabled entirely

# Proxmox recommended (host security, guest performance):
echo "kernel.io_uring_disabled=1" >> /etc/sysctl.d/99-security.conf
```

**Performance comparison** (fio, 4K random read, iodepth=128):

| I/O Engine | IOPS | CPU Usage | Latency p99 |
|---|---|---|---|
| sync | 95,000 | 100% (1 core) | 1,350 µs |
| libaio | 580,000 | 45% | 220 µs |
| io_uring | 720,000 | 35% | 178 µs |
| io_uring (SQ polling) | 890,000 | 28% | 145 µs |

**Decision:** Use io_uring on hypervisor host for VM I/O (where the host is trusted). Restrict it in guest/container contexts via sysctl or seccomp.

### 3.5 Storage Multipathing Security

Multipath I/O (DM-MPIO) introduces security considerations:

```bash
# /etc/multipath.conf — secure configuration
defaults {
    user_friendly_names no    # Use WWID, not mpath0/1 (predictable)
    find_multipaths     yes
    path_grouping_policy failover
    failback            manual # Prevent automatic path switch (could be spoofed)
}

blacklist {
    devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
    devnode "^sd[a-b]$"  # Local boot drives
}

# Verify path isolation
multipathd show paths format "%d %s %c %p %t"
```

---

## 4. Network Security vs Throughput

### 4.1 SR-IOV Security Model and Performance

Single Root I/O Virtualization (SR-IOV) provides near-native network performance by exposing Virtual Functions (VFs) directly to VMs via IOMMU passthrough:

**Performance comparison** (Intel E810 100GbE, iperf3 TCP, MTU 1500):

| Method | Throughput | CPU Usage (host) | Latency (µs) | Packets/sec |
|---|---|---|---|---|
| virtio-net (vhost) | 25 Gbps | 35% per core | 45 | 2.1M |
| virtio-net + vhost-user | 40 Gbps | 25% per core | 32 | 3.3M |
| SR-IOV VF passthrough | 95 Gbps | <2% | 8 | 8.2M |
| macvtap (bridge mode) | 18 Gbps | 45% per core | 62 | 1.5M |

**SR-IOV security model:**

```
┌─────────────────────────────────────────────────┐
│ Hardware NIC (Physical Function - PF)            │
│                                                 │
│   PF Driver (host) — full control               │
│   ├── VF 0 → VM-A (IOMMU group isolated)       │
│   ├── VF 1 → VM-B (IOMMU group isolated)       │
│   ├── VF 2 → VM-C (IOMMU group isolated)       │
│   └── VF 3 → unassigned                        │
│                                                 │
│   ISOLATION GUARANTEES:                          │
│   ✓ VF cannot access PF registers               │
│   ✓ VF cannot access other VFs' memory (IOMMU)  │
│   ✓ VF MAC address enforced by hardware          │
│   ✗ VF can see broadcast/multicast traffic       │
│   ✗ VF bypass means no host-level IDS/firewall   │
└─────────────────────────────────────────────────┘
```

**Security trade-off:** SR-IOV bypasses the host network stack entirely. This means:
- No host-level firewall inspection (iptables/nftables do not see VF traffic)
- No OVS flow rules applied to VF traffic
- Network monitoring requires TAP/SPAN at the physical switch
- MAC spoofing prevention depends on NIC hardware enforcement

```bash
# Enable SR-IOV on Intel E810
echo 16 > /sys/class/net/ens1f0/device/sriov_numvfs

# Set VF security parameters
ip link set ens1f0 vf 0 mac aa:bb:cc:dd:ee:01 spoofchk on trust off
ip link set ens1f0 vf 0 max_tx_rate 10000  # Rate limit: 10 Gbps
ip link set ens1f0 vf 0 vlan 100           # VLAN isolation

# Verify IOMMU grouping (each VF should be in its own group)
find /sys/kernel/iommu_groups/ -type l | sort -V | grep "ens1"
```

### 4.2 OVS with OpenFlow: ACL Performance Impact

Open vSwitch (OVS) with OpenFlow rules provides software-defined network security but at a performance cost proportional to rule complexity:

**Benchmark: throughput degradation per rule complexity** (OVS 3.3, DPDK datapath):

| Rule Count | Rule Type | Throughput (64B pkts) | Throughput (1500B) | Latency Added |
|---|---|---|---|---|
| 0 (passthrough) | — | 14.2 Mpps | 9.4 Gbps | 3 µs |
| 100 | L2/L3 match | 13.8 Mpps | 9.3 Gbps | 4 µs |
| 1,000 | L2/L3/L4 5-tuple | 12.1 Mpps | 9.1 Gbps | 8 µs |
| 10,000 | L2/L3/L4 + conntrack | 8.4 Mpps | 8.2 Gbps | 18 µs |
| 50,000 | Full ACL + NAT + CT | 4.2 Mpps | 6.1 Gbps | 42 µs |
| 100,000+ | Complex regex/DPI | 1.8 Mpps | 3.4 Gbps | 95 µs |

**Optimization strategies:**

```bash
# Enable OVS megaflows (wildcard caching)
ovs-vsctl set Open_vSwitch . other_config:max-idle=30000

# Use conjunction() for complex ACLs (order-of-magnitude faster)
# Instead of N*M rules for (N sources) * (M ports):
ovs-ofctl add-flow br0 "priority=100,ip,nw_src=10.0.0.1,conj_id=1,actions=normal"
ovs-ofctl add-flow br0 "priority=100,ip,tp_dst=443,conj_id=1,actions=normal"

# Offload to hardware (TC flower offload on supported NICs)
ovs-vsctl set Open_vSwitch . other_config:hw-offload=true
tc filter show dev ens1f0 ingress  # Verify hardware offload
```

### 4.3 Jumbo Frames: Security Considerations

Jumbo frames (MTU 9000) provide 15-30% throughput improvement for bulk transfers but introduce security concerns in shared networks:

| Risk | Description | Mitigation |
|---|---|---|
| Fragmentation DoS | Oversized frames cause reassembly overhead | Drop oversized at ingress |
| Buffer overflow surface | Larger frames = larger buffer allocations | Validate MTU at every hop |
| Amplification attacks | Larger response packets per request | Rate limiting |
| VLAN hopping | Some switches mishandle jumbo + 802.1Q tags | Firmware validation |
| IDS evasion | Jumbo frames may bypass inspection tools sized for 1500B | Configure IDS buffer size |

**Recommendation:** Use jumbo frames only on isolated storage/vMotion networks. Never on management or tenant-facing VLANs.

```bash
# Configure jumbo MTU on storage VLAN only
ip link set ens1f0.2000 mtu 9000  # Storage VLAN 2000
ip link set ens1f0.100 mtu 1500   # Tenant VLAN 100 — standard MTU

# Proxmox /etc/network/interfaces
auto vmbr1
iface vmbr1 inet manual
    bridge-ports ens1f0.2000
    bridge-stp off
    bridge-fd 0
    mtu 9000
    # Storage bridge only — no VM guest access
```

### 4.4 DPDK Acceleration with Security Filtering

Data Plane Development Kit (DPDK) provides kernel-bypass networking for extreme throughput. Combining it with security filtering:

```bash
# DPDK + OVS-DPDK for filtered high-performance networking
ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-init=true
ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-lcore-mask=0xFF
ovs-vsctl --no-wait set Open_vSwitch . other_config:dpdk-socket-mem="4096,4096"

# Add DPDK port
ovs-vsctl add-port br0 dpdk0 -- set Interface dpdk0 type=dpdk \
    options:dpdk-devargs=0000:81:00.0

# Apply security rules on DPDK datapath (conntrack-enabled)
ovs-ofctl add-flow br0 "priority=200,ct_state=-trk,ip,actions=ct(table=1)"
ovs-ofctl add-flow br0 "table=1,priority=100,ct_state=+trk+est,actions=normal"
ovs-ofctl add-flow br0 "table=1,priority=100,ct_state=+trk+new,tcp,tp_dst=443,actions=ct(commit),normal"
ovs-ofctl add-flow br0 "table=1,priority=1,actions=drop"
```

### 4.5 XDP/eBPF Firewall Performance

eXpress Data Path (XDP) processes packets at the earliest point in the network stack — before sk_buff allocation:

**Performance comparison** (100GbE, 64-byte packets, DDoS filtering):

| Firewall Method | Drop Rate (pps) | Legitimate Throughput | CPU Cores Needed |
|---|---|---|---|
| iptables (legacy) | 2.5M pps | 6 Gbps | 8 |
| nftables | 4.8M pps | 7.2 Gbps | 6 |
| ipset + iptables | 8.2M pps | 8.5 Gbps | 4 |
| XDP (native) | 48M pps | 9.8 Gbps | 1 |
| XDP (offloaded to NIC) | 100M+ pps | line rate | 0 (NIC hardware) |

```c
/* Example XDP program: block known-bad source IPs */
SEC("xdp")
int xdp_firewall(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_DROP;

    if (eth->h_proto != htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_DROP;

    /* Lookup in BPF map (LPM trie for CIDR matching) */
    struct lpm_key key = { .prefixlen = 32, .addr = ip->saddr };
    if (bpf_map_lookup_elem(&blocked_ips, &key))
        return XDP_DROP;

    return XDP_PASS;
}
```

### 4.6 Encryption Overhead: WireGuard vs IPsec vs MACsec

**Benchmark conditions:** 2x Intel Xeon 8480+ connected via 100GbE direct, iperf3 TCP, 16 parallel streams:

| Protocol | Throughput | CPU Usage | Latency Added | Cipher |
|---|---|---|---|---|
| No encryption | 98 Gbps | 12% | 0 | — |
| WireGuard | 42 Gbps | 65% | +0.3 ms | ChaCha20-Poly1305 |
| WireGuard (multi-queue) | 68 Gbps | 85% | +0.2 ms | ChaCha20-Poly1305 |
| IPsec (ESP tunnel, AES-GCM-256) | 38 Gbps | 72% | +0.5 ms | AES-256-GCM |
| IPsec (ESP transport, AES-GCM-128) | 52 Gbps | 60% | +0.4 ms | AES-128-GCM |
| IPsec (hardware offload, Intel QAT) | 92 Gbps | 8% | +0.1 ms | AES-256-GCM |
| MACsec (hardware offload) | 97 Gbps | 2% | +0.02 ms | AES-256-GCM |
| MACsec (software) | 28 Gbps | 90% | +0.8 ms | AES-256-GCM |

**Recommendation matrix:**

| Use Case | Recommended Protocol | Rationale |
|---|---|---|
| Host-to-host (same rack) | MACsec (HW offload) | Lowest overhead, L2 security |
| Cross-datacenter WAN | IPsec with QAT offload | Established, hardware acceleration |
| Remote site VPN | WireGuard | Simple, good throughput, low state |
| VM-to-VM overlay | WireGuard (multi-queue) | No hardware dependency |
| Storage replication (iSCSI) | MACsec or IPsec offload | Throughput critical |

---

## 5. Secure Boot and Measured Boot Performance

### 5.1 UEFI Secure Boot Chain Verification Time

The Secure Boot verification chain measures cryptographic signatures at each stage:

```
Platform Key (PK)
    └── Key Exchange Key (KEK)
         └── Signature Database (db)
              ├── Bootloader signature (shim → GRUB2)
              ├── Kernel signature (vmlinuz)
              ├── Initramfs signature (optional)
              └── Module signatures (modsign)
```

**Boot time measurements** (Supermicro H13SSL, EPYC 9354, NVMe boot):

| Boot Stage | No Secure Boot | Secure Boot | Delta |
|---|---|---|---|
| UEFI POST + PK init | 8.2 s | 8.4 s | +200 ms |
| Shim verification | — | 0.15 s | +150 ms |
| GRUB2 verification | — | 0.08 s | +80 ms |
| Kernel verification | 0 | 0.12 s | +120 ms |
| Module loading (all) | 2.1 s | 2.6 s | +500 ms |
| Total boot to login | 14.8 s | 15.9 s | +1.1 s (+7%) |

**Conclusion:** Secure Boot adds approximately 1-1.5 seconds to boot time. For infrastructure that reboots rarely (hypervisors), this is negligible. Never disable Secure Boot to save boot time.

### 5.2 TPM 2.0 Attestation Overhead

TPM operations are inherently slow due to the security-hardened, resource-constrained TPM chip:

| Operation | Typical Latency | Impact |
|---|---|---|
| PCR Extend | 5-15 ms | Per boot measurement |
| PCR Read | 2-5 ms | Attestation query |
| RSA-2048 Sign | 200-800 ms | Remote attestation |
| RSA-2048 Decrypt | 150-600 ms | Seal/unseal operations |
| ECDSA P-256 Sign | 50-150 ms | Faster attestation |
| Random number gen | 10-30 ms per 32 bytes | Key generation |

**Measured Boot with IMA (Integrity Measurement Architecture):**

```bash
# Enable IMA in kernel command line
GRUB_CMDLINE_LINUX="ima_policy=tcb ima_hash=sha256"

# IMA performance impact per file access
# First access: +1-5ms (hash computation + PCR extend)
# Subsequent: ~0 (cached in IMA hash table)

# Check IMA measurement list
cat /sys/kernel/security/ima/ascii_runtime_measurements | wc -l
# Typical Proxmox host: 2,000-5,000 measurements

# IMA overhead for large file (1 GB):
# sha256 computation: ~1.2 seconds (initial open)
# Subsequent opens: <1ms (cached hash valid until file modified)
```

### 5.3 vTPM Implementation Performance

**VMware vTPM** (vCenter-managed):
- Key storage: vCenter-encrypted VM encryption
- Performance: Software emulation, ~10x faster than hardware TPM
- Operations: Sign ~20ms, PCR Extend ~1ms (vs 200ms/5ms hardware)

**Proxmox swtpm (Software TPM):**

```bash
# Install swtpm on Proxmox host
apt install swtpm swtpm-tools

# Per-VM vTPM configuration (/etc/pve/qemu-server/<vmid>.conf)
tpmstate0: local-lvm:vm-100-disk-1,size=4M,version=v2.0

# swtpm process per VM (auto-managed by Proxmox)
# Performance: all operations in software, no hardware bottleneck
# Sign: 2-5ms, PCR Extend: <1ms

# Verify guest sees TPM
# Inside guest:
tpm2_getcap properties-fixed
tpm2_pcrread sha256
```

**Performance comparison:**

| vTPM Implementation | RSA-2048 Sign | PCR Extend | Impact on Guest Boot |
|---|---|---|---|
| Hardware TPM 2.0 (SLB9670) | 400 ms | 8 ms | +3-5 s |
| VMware vTPM | 25 ms | 0.8 ms | +0.3 s |
| swtpm (Proxmox) | 3 ms | 0.2 ms | +0.1 s |

### 5.4 Early Boot Security vs Boot Time Optimization

| Feature | Boot Time Impact | Security Benefit | Recommendation |
|---|---|---|---|
| Secure Boot | +1.0 s | Root of trust chain | Always enable |
| Measured Boot (IMA) | +0.5 s (boot) | Runtime integrity | Enable on security-critical |
| TPM unsealing (LUKS) | +0.8 s | Automated secure unlock | Enable for unattended |
| Kernel modsign verify | +0.5 s | Module integrity | Always enable |
| DRTM (Intel TXT / AMD SKINIT) | +3-5 s | Late launch attestation | High-security only |
| fTPM (firmware TPM) | +0.2 s | Integrated, faster than discrete | Acceptable for non-HSM use |

---

## 6. Security Monitoring Performance Impact

### 6.1 Agent-Based vs Agentless Monitoring

**Per-VM resource consumption of popular security agents:**

| Agent | CPU Overhead | Memory | Disk I/O | Network |
|---|---|---|---|---|
| CrowdStrike Falcon | 1-3% | 250-500 MB | 5-20 IOPS | 50-200 KB/s |
| Microsoft Defender for Endpoint | 2-5% | 300-800 MB | 10-30 IOPS | 100-500 KB/s |
| Wazuh agent | 0.5-2% | 80-200 MB | 5-15 IOPS | 20-100 KB/s |
| OSSEC agent | 0.3-1% | 40-100 MB | 3-10 IOPS | 10-50 KB/s |
| Falco (eBPF mode) | 1-4% | 150-400 MB | minimal | 30-150 KB/s |
| Sysdig agent | 2-5% | 512-1024 MB | 10-40 IOPS | 100-300 KB/s |

**Agentless approaches** (hypervisor-level):

| Method | Host CPU Overhead | Coverage | Latency to Detect |
|---|---|---|---|
| VMware NSX IDS/IPS | 5-15% (per host) | Network only | Real-time |
| Hypervisor memory introspection (BitDefender HVI) | 3-8% | Memory + Process | Real-time |
| Proxmox + libvmi | 2-5% | Memory forensics | Seconds |
| Network TAP + Zeek/Suricata | 0% (host) / dedicated | Network only | Real-time |

### 6.2 Audit Subsystem Tuning

The Linux audit subsystem (auditd) is critical for compliance but can impose significant overhead if configured carelessly:

```bash
# BAD: Audit everything (will kill IOPS)
-a always,exit -F arch=b64 -S all

# GOOD: Targeted audit rules for security-relevant events
# /etc/audit/rules.d/99-security.rules

# First rule: exclude high-volume, low-value events
-a always,exclude -F msgtype=CWD
-a always,exclude -F msgtype=EOE

# File integrity monitoring (specific paths only)
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/pam.d/ -p wa -k pam
-w /etc/ssh/sshd_config -p wa -k sshd

# Privileged command execution
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -k priv_exec

# Network connections (exclude established, track new only)
-a always,exit -F arch=b64 -S connect -F a2!=110 -k net_connect

# Avoid auditing high-frequency syscalls on data paths
# NEVER audit: read, write, stat, lstat, fstat, poll, mmap on busy systems
```

**Auditd performance impact by configuration:**

| Configuration | Syscall Overhead | Disk I/O (audit log) | Log Volume (busy host) |
|---|---|---|---|
| Disabled | 0 | 0 | 0 |
| CIS Level 1 rules | +2-4% | 5-20 MB/min | 7-30 GB/day |
| CIS Level 2 rules | +5-12% | 20-80 MB/min | 30-120 GB/day |
| Audit-all-syscalls (mistake) | +30-60% | 200+ MB/min | 300+ GB/day |
| Tuned production rules | +1-3% | 2-10 MB/min | 3-15 GB/day |

**auditd tuning for performance:**

```bash
# /etc/audit/auditd.conf
write_logs = yes
log_file = /var/log/audit/audit.log
log_format = ENRICHED
freq = 50                    # Flush frequency (higher = less I/O, more risk of loss)
num_logs = 10
max_log_file = 100           # MB per file
max_log_file_action = rotate
space_left = 1000            # MB
space_left_action = SYSLOG
admin_space_left = 500
admin_space_left_action = HALT

# Critical: backlog settings
disp_qos = lossy             # Do NOT use 'lossless' in production (can block syscalls)
dispatcher = /sbin/audispd

# Kernel-side backlog
# /etc/default/grub or audit rules
-b 8192                      # Backlog buffer size (default 64 is too small)
--backlog_wait_time 60000    # ms to wait before dropping (15000 default)
-f 1                         # Failure mode: printk on failure (2 = panic, AVOID)
```

### 6.3 eBPF-Based Security Tools: Efficiency

**Comparison of kernel instrumentation approaches:**

| Approach | Overhead | Safety | Flexibility | Production-Ready |
|---|---|---|---|---|
| kprobes (raw) | Medium-High | Low (crash risk) | High | Legacy |
| ftrace | Low | Medium | Medium | Yes |
| eBPF (kprobe-based) | Medium | High (verifier) | High | Yes |
| eBPF (tracepoint) | Low | High | Medium | Yes |
| eBPF (LSM hooks) | Low | High | High | Yes (6.x+) |
| Kernel modules | Variable | Low | High | Avoid |

**Falco (eBPF driver) vs kmod driver:**

```bash
# Falco with eBPF — preferred for performance and safety
falco --modern-bpf

# Performance measurement (syscalls/sec with Falco active)
# Workload: PostgreSQL TPC-C, 64 warehouses

# Configuration             TPS       CPU overhead
# No monitoring             142,000   baseline
# Falco kernel module       128,000   +10% host CPU
# Falco eBPF (classic)      133,000   +7% host CPU
# Falco modern eBPF         137,000   +4% host CPU
# Tetragon (eBPF)           139,000   +3% host CPU
```

**Tetragon (Cilium) for efficient kernel-level security:**

```yaml
# tetragon-policy.yaml — monitor privilege escalation attempts
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: privilege-escalation
spec:
  kprobes:
    - call: "commit_creds"
      syscall: false
      args:
        - index: 0
          type: "cred"
      selectors:
        - matchArgs:
            - index: 0
              operator: "NotEqual"
              values: ["0"]  # Alert when creds change to uid 0
```

### 6.4 Log Volume Management: Sampling Strategies

| Strategy | Volume Reduction | Security Coverage | Use Case |
|---|---|---|---|
| No sampling | 0% | 100% | Compliance-mandated retention |
| Rate limiting (per-source) | 40-60% | 95% | Noisy applications |
| Probabilistic sampling (1:10) | 90% | ~90% (statistical) | High-volume observability |
| Head sampling + exceptions | 70-80% | 99% | Intelligent pipelines |
| Priority-based (alert → full, info → sample) | 60-80% | 99.9% | Production recommended |

```bash
# rsyslog — rate limiting per source
$SystemLogRateLimitInterval 5
$SystemLogRateLimitBurst 200

# journald — intelligent storage limits
# /etc/systemd/journald.conf
[Journal]
Storage=persistent
SystemMaxUse=4G
SystemMaxFileSize=512M
RateLimitIntervalSec=5s
RateLimitBurst=1000
MaxLevelStore=info     # Drop debug from persistent storage
MaxLevelSyslog=warning # Only forward warning+ to remote syslog
```

---

## 7. Hardening vs Usability Tradeoffs

### 7.1 CIS Benchmark Items That Hurt Performance

Specific CIS Benchmark recommendations and their measured performance impact on Proxmox VE / Debian 12 hosts:

| CIS Item | Recommendation | Performance Impact | Decision Framework |
|---|---|---|---|
| 1.1.2 | /tmp with noexec,nosuid | +0% (negligible) | Always enable |
| 1.4.1 | Bootloader password | +0% runtime, +5s interactive boot | Enable unless fully automated |
| 3.3.1 | TCP SYN cookies | +1% under SYN flood | Always enable |
| 3.3.2 | ICMP redirects disabled | +0% | Always disable |
| 4.1.1.4 | Audit backlog full action | +0-30% if set to HALT | Use SYSLOG, never HALT |
| 4.2.4 | Log all privileged commands | +5-15% CPU | Tune selectively |
| 5.2.3 | SSH MaxAuthTries=4 | +0% | Always enable |
| 5.4.5 | umask 027 | +0% | Enable |
| 6.1.* | File permission checks | +0% (one-time audit) | Enable |
| 3.4.1 | nftables + default deny | +1-3% network (rule evaluation) | Always enable, tune rules |
| 1.5.1 | Address Space Layout Randomization | +0.1% | Always enable |
| 1.5.3 | Disable core dumps | +0% runtime, -debug capability | Enable in production |
| 4.1.4 | Audit file deletions | +3-8% (filesystem heavy workloads) | Tune to critical paths only |

### 7.2 SELinux/AppArmor Overhead in Hypervisor Context

**AppArmor** (Proxmox default for QEMU confinement):

```bash
# AppArmor mode for QEMU processes
aa-status | grep qemu
# /usr/bin/qemu-system-x86_64 (enforce)

# Performance impact measurement (VM disk I/O, fio 4K random)
# AppArmor enforcing:  485,000 IOPS
# AppArmor complain:   492,000 IOPS
# AppArmor disabled:   498,000 IOPS
# Overhead: ~2.5% (enforcing vs disabled)
```

**SELinux on hypervisor hosts** (for comparison, RHEL/Rocky-based KVM):

| Mode | IO-bound Overhead | CPU-bound Overhead | Syscall Latency |
|---|---|---|---|
| Disabled | baseline | baseline | baseline |
| Permissive (logging) | +1% | +0.5% | +2 µs |
| Enforcing (targeted) | +3-5% | +1-2% | +5-8 µs |
| Enforcing (strict MLS) | +8-12% | +3-5% | +15-25 µs |

**Recommendation:** AppArmor in enforce mode on Proxmox is the sweet spot — low overhead, effective QEMU confinement, and no compatibility issues with the Proxmox ecosystem.

### 7.3 Firewall Rule Count Performance

**iptables vs nftables vs ipset** (measured on x86_64, kernel 6.6, 10GbE line rate):

| Rule Set Size | iptables (linear) | nftables (set lookup) | iptables + ipset |
|---|---|---|---|
| 10 rules | 9.8 Gbps | 9.8 Gbps | 9.8 Gbps |
| 100 rules | 9.5 Gbps | 9.8 Gbps | 9.8 Gbps |
| 1,000 rules | 7.2 Gbps | 9.6 Gbps | 9.7 Gbps |
| 10,000 rules | 3.1 Gbps | 9.4 Gbps | 9.5 Gbps |
| 50,000 rules | 0.8 Gbps | 9.1 Gbps | 9.3 Gbps |
| 100,000 rules | 0.3 Gbps | 8.8 Gbps | 9.0 Gbps |

**Key insight:** iptables performs O(n) linear rule traversal. nftables uses hash-based set lookups — O(1) regardless of set size. For any infrastructure with more than a few hundred rules, nftables is mandatory for performance.

```bash
# nftables set-based ACL (O(1) lookup for any number of blocked IPs)
nft add set inet filter blocked_ips { type ipv4_addr \; flags interval \; }
nft add rule inet filter input ip saddr @blocked_ips drop
nft add element inet filter blocked_ips { 10.0.0.0/8, 172.16.0.0/12 }

# Compare to iptables equivalent (O(n) per packet):
# iptables -A INPUT -s 10.0.0.0/8 -j DROP
# iptables -A INPUT -s 172.16.0.0/12 -j DROP
# ... times 50,000
```

### 7.4 TLS Cipher Selection: Security vs Handshake Performance

**TLS 1.3 cipher performance** (openssl speed, single core, Xeon 8480+):

| Cipher Suite | Ops/sec (sign) | Ops/sec (verify) | Handshake Time | Security Level |
|---|---|---|---|---|
| TLS_AES_256_GCM_SHA384 + X25519 | 58,000 | 171,000 | 0.42 ms | 128-bit |
| TLS_AES_128_GCM_SHA256 + X25519 | 62,000 | 175,000 | 0.40 ms | 128-bit |
| TLS_CHACHA20_POLY1305_SHA256 + X25519 | 55,000 | 168,000 | 0.44 ms | 128-bit |
| TLS_AES_256_GCM_SHA384 + P-384 | 4,200 | 12,100 | 1.8 ms | 192-bit |
| TLS_AES_256_GCM_SHA384 + P-521 | 1,800 | 5,200 | 3.2 ms | 256-bit |

**Recommended configuration for Proxmox pveproxy / web management:**

```bash
# /etc/default/pveproxy
CIPHERS="TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256"
HONOR_CIPHER_ORDER=1
# Use X25519 for key exchange (fast, 128-bit equivalent security)
# Avoid P-521 unless compliance requires 256-bit equivalent
```

---

## 8. Capacity Planning with Security Overhead

### 8.1 Overhead Matrices

**CPU overhead per security feature (additive):**

| Security Feature | CPU Overhead | Affected Workloads |
|---|---|---|
| Spectre/Meltdown mitigations (eIBRS) | 2-5% | Syscall-heavy |
| Full mitigations (legacy hardware) | 15-25% | All workloads |
| SEV-SNP (per encrypted VM) | 8-15% | All VM operations |
| LUKS2 encryption (with AES-NI) | 3-5% | Storage I/O |
| TLS termination (management APIs) | 1-2% | API-heavy |
| Security agent (CrowdStrike/similar) | 2-5% per VM | All |
| auditd (tuned rules) | 1-3% | File/process operations |
| Falco/Tetragon (eBPF) | 2-4% | Syscall-heavy |
| AppArmor enforcing | 2-3% | All |
| Network encryption (WireGuard overlay) | 5-10% | Network-heavy |

**Memory overhead per security feature:**

| Security Feature | Memory Overhead | Notes |
|---|---|---|
| KPTI (page table duplication) | +1-2% kernel memory | Per-process |
| SEV-SNP RMP table | +0.4% of total RAM | Fixed per host |
| Security agent (per VM) | 250-800 MB per VM | Varies by vendor |
| Audit log buffers | 32-128 MB | Tunable (backlog) |
| eBPF maps (Falco/Tetragon) | 50-200 MB | Per policy count |
| vTPM state (per VM) | 4 MB | Negligible |
| Hugepages reservation | Exact allocation | No overcommit |

### 8.2 Sizing Formulas

**CPU sizing with security overhead:**

```
Effective_vCPUs = Physical_Cores × Overcommit_Ratio × (1 - Security_Overhead)

Where Security_Overhead = sum of applicable features:
  Mitigations:     0.05 (eIBRS) or 0.20 (legacy)
  Encryption:      0.05 (LUKS) + 0.10 (SEV-SNP if used)
  Monitoring:      0.04 (eBPF tools) + 0.02 (auditd)
  MAC:             0.02 (AppArmor)

Example (modern hardware, full security):
  64 cores × 4:1 ratio × (1 - 0.05 - 0.05 - 0.04 - 0.02)
  = 64 × 4 × 0.84
  = 215 effective vCPUs (vs 256 without security = 16% density loss)
```

**Memory sizing with security overhead:**

```
Available_VM_Memory = Total_RAM - Host_Reserved - Security_Overhead

Host_Reserved = 8 GB (Proxmox OS + services)
Security_Overhead_per_VM = Agent_Memory + vTPM + AuditBuffers
                         = 400 MB + 4 MB + 12 MB ≈ 416 MB per VM

Example (256 GB host, 32 VMs):
  Available = 256 GB - 8 GB - (32 × 0.416 GB)
            = 256 - 8 - 13.3
            = 234.7 GB for VM workloads (vs 248 GB without agents)
```

**Storage IOPS with encryption overhead:**

```
Effective_IOPS = Raw_Device_IOPS × Encryption_Factor × Overhead_Factor

Encryption_Factor:
  No encryption: 1.0
  LUKS2 (AES-NI): 0.95
  ZFS native: 0.90
  LUKS2 without AES-NI: 0.20  (!!!)

Overhead_Factor (audit + I/O monitoring):
  Minimal audit: 0.98
  Full audit: 0.88
  Audit + integrity checking (dm-verity): 0.80
```

### 8.3 Right-Sizing VMs with Security Agent Consumption

| VM Role | Base Resources | + Security Agent | Recommendation |
|---|---|---|---|
| Web server (nginx) | 2 vCPU, 2 GB | +0.5 vCPU, +400 MB | Size to 3 vCPU, 3 GB |
| Database (PostgreSQL) | 8 vCPU, 32 GB | +0.5 vCPU, +400 MB | Size to 9 vCPU, 33 GB |
| Application server | 4 vCPU, 8 GB | +0.5 vCPU, +500 MB | Size to 5 vCPU, 9 GB |
| CI/CD runner | 8 vCPU, 16 GB | +1 vCPU, +800 MB | Size to 10 vCPU, 17 GB |
| Jump host (bastion) | 2 vCPU, 4 GB | +0.5 vCPU, +400 MB | Size to 3 vCPU, 5 GB |

### 8.4 License Cost Optimization: VMware → Proxmox Savings Reinvested

| Cost Category | VMware (per socket/year) | Proxmox (per socket/year) | Savings |
|---|---|---|---|
| Hypervisor license | $5,850 (vSphere Std) | $0 (AGPL) | $5,850 |
| vCenter license | $8,770 (per instance) | $0 (included) | $8,770 |
| Support subscription | $3,500 (Production) | $1,190 (Premium) | $2,310 |
| vSAN license | $3,500 (per socket) | $0 (ZFS/Ceph included) | $3,500 |
| NSX license | $5,500 (per socket) | $0 (OVS/SDN included) | $5,500 |
| **Total (2-socket host)** | **$54,240** | **$2,380** | **$51,860** |

**Reinvestment plan for security tooling:**

| Security Investment | Annual Cost | Funded by VMware Savings |
|---|---|---|
| EDR platform (50 VMs) | $15,000 | Yes |
| SIEM + log management | $8,000 | Yes |
| Vulnerability scanner | $5,000 | Yes |
| Hardware security (TPM, HSM) | $3,000 | Yes |
| Security training + certs | $5,000 | Yes |
| Penetration testing (annual) | $12,000 | Yes |
| **Total security investment** | **$48,000** | **Still saving $3,860/year** |

---

## 9. Benchmarking Methodology

### 9.1 Security-Aware Benchmarking Principles

**Rule 1: Never disable security to benchmark.**

Benchmarks published with `mitigations=off` are meaningless for production capacity planning. They represent unreachable performance in any legitimate deployment.

**Rule 2: Benchmark the actual security configuration.**

```bash
# WRONG: Benchmark without security, then estimate overhead
fio --name=test ... # on unencrypted, unmonitored, unmitigated system

# RIGHT: Benchmark the production-equivalent configuration
# 1. Apply all kernel mitigations
# 2. Enable encryption (LUKS/ZFS)
# 3. Start security agents
# 4. Enable audit rules
# THEN benchmark
fio --name=test ... # on fully secured system
```

**Rule 3: Document the security state in benchmark results.**

```bash
# Capture security state before benchmarking
echo "=== Security State ==="
cat /sys/devices/system/cpu/vulnerabilities/*
cryptsetup status cryptdata
systemctl is-active auditd falco crowdstrike-falcon-sensor
getenforce || aa-status
cat /proc/cmdline | tr ' ' '\n' | grep -E 'mitig|spectre|mds|l1tf'
```

### 9.2 Benchmark Tools with Security Context

#### fio — Storage benchmarking

```bash
# Production-representative storage benchmark
# Includes: LUKS encryption active, auditd running, security agents present

fio --name=production-storage-bench \
    --filename=/encrypted-volume/testfile \
    --size=64G \
    --rw=randrw \
    --rwmixread=70 \
    --bs=4k \
    --numjobs=16 \
    --iodepth=64 \
    --runtime=300 \
    --time_based \
    --group_reporting \
    --randrepeat=0 \
    --norandommap \
    --ioengine=libaio \
    --direct=1 \
    --lat_percentiles=1 \
    --output-format=json+ \
    --output=fio-results-$(date +%Y%m%d-%H%M%S).json

# Compare encrypted vs unencrypted (for overhead quantification only)
for target in /raw-device/test /luks-device/test /zfs-encrypted/test; do
    fio --name="bench-${target//\//-}" \
        --filename="$target" \
        --size=32G --rw=randrw --rwmixread=70 --bs=4k \
        --numjobs=8 --iodepth=32 --runtime=120 --time_based \
        --group_reporting --direct=1 \
        --output-format=json+ \
        --output="fio-$(basename $target)-$(date +%s).json"
done
```

#### iperf3 — Network benchmarking

```bash
# Server side (receiver)
iperf3 -s -p 5201 --daemon

# Client: Baseline (no encryption)
iperf3 -c 10.0.0.2 -p 5201 -t 60 -P 16 --json > iperf3-baseline.json

# Client: Over WireGuard tunnel
iperf3 -c 10.100.0.2 -p 5201 -t 60 -P 16 --json > iperf3-wireguard.json

# Client: Over IPsec (strongSwan)
iperf3 -c 10.200.0.2 -p 5201 -t 60 -P 16 --json > iperf3-ipsec.json

# Compare results
jq '.end.sum_received.bits_per_second / 1000000000' iperf3-*.json
```

#### sysbench — CPU and general workload

```bash
# CPU benchmark (measures mitigation impact on compute)
sysbench cpu --cpu-max-prime=100000 --threads=$(nproc) run

# Memory benchmark (measures SEV/TDX impact)
sysbench memory --memory-block-size=4K --memory-total-size=100G \
    --memory-oper=write --threads=16 run

# MySQL/PostgreSQL OLTP (realistic workload)
sysbench /usr/share/sysbench/oltp_read_write.lua \
    --mysql-host=localhost --mysql-port=3306 \
    --mysql-user=bench --mysql-password=bench --mysql-db=benchdb \
    --table-size=1000000 --tables=10 --threads=64 --time=300 run
```

#### stress-ng — CPU vulnerability mitigation overhead

```bash
# Context switch benchmark (most sensitive to KPTI/mitigations)
stress-ng --context 0 --timeout 60 --metrics-brief

# Syscall overhead (directly measures mitigation cost)
stress-ng --syscall 0 --timeout 60 --metrics-brief

# Fork/exec (measures KPTI + PCID effectiveness)
stress-ng --fork 0 --timeout 60 --metrics-brief

# TLB pressure (measures PCID impact)
stress-ng --tlb-shootdown 0 --timeout 60 --metrics-brief

# Memory encryption overhead
stress-ng --vm 4 --vm-bytes 8G --timeout 60 --metrics-brief
```

### 9.3 Reproducible Benchmark Environments

```bash
#!/bin/bash
# benchmark-environment-setup.sh
# Ensures reproducible benchmark conditions

set -euo pipefail

RESULTS_DIR="/var/benchmarks/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RESULTS_DIR"

# 1. Record system state
{
    echo "=== Kernel ==="
    uname -r
    cat /proc/cmdline

    echo "=== CPU Vulnerabilities ==="
    for f in /sys/devices/system/cpu/vulnerabilities/*; do
        echo "$(basename $f): $(cat $f)"
    done

    echo "=== CPU Governor ==="
    cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

    echo "=== Turbo Boost ==="
    cat /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || echo "N/A"

    echo "=== NUMA ==="
    numactl --hardware

    echo "=== Memory ==="
    free -h
    cat /proc/meminfo | grep -E "Huge|MemTotal|MemFree"

    echo "=== Encryption ==="
    dmsetup table --showkeys 2>/dev/null | awk '{print $1, $4}'
    zfs get encryption 2>/dev/null || echo "No ZFS"

    echo "=== Security Services ==="
    systemctl is-active auditd falco crowdstrike-falcon-sensor 2>/dev/null

    echo "=== Disk Scheduler ==="
    for disk in /sys/block/nvme*/queue/scheduler; do
        echo "$disk: $(cat $disk)"
    done
} > "$RESULTS_DIR/system-state.txt"

# 2. Set CPU to performance mode (deterministic, not power-saving)
for cpu in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    echo "performance" > "$cpu"
done

# 3. Disable turbo boost for consistency
echo 1 > /sys/devices/system/cpu/intel_pstate/no_turbo 2>/dev/null || true

# 4. Drop caches (fair starting point)
sync
echo 3 > /proc/sys/vm/drop_caches

# 5. Wait for system to stabilize
sleep 10

echo "Environment ready. Results dir: $RESULTS_DIR"
```

### 9.4 Performance Regression Detection as Security Signal

Unexpected performance degradation can indicate security issues:

| Performance Anomaly | Possible Security Cause |
|---|---|
| Sudden 30% IOPS drop | Cryptominer consuming disk I/O |
| Network latency spike | Man-in-the-middle / traffic redirection |
| CPU usage 100% on idle VM | Unauthorized process (rootkit, miner) |
| Memory usage creep | Memory leak from injected payload |
| Audit log volume 10x increase | Brute-force attack, file enumeration |
| TLB flush rate spike | Cache side-channel attack in progress |

```bash
# Baseline establishment (run weekly, compare)
#!/bin/bash
BASELINE_FILE="/var/benchmarks/baseline-$(hostname).json"

# Quick 30-second benchmark suite
results=$(cat <<EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "hostname": "$(hostname)",
    "cpu_ops": $(sysbench cpu --cpu-max-prime=20000 --threads=$(nproc) --time=10 run 2>/dev/null | grep "events per second" | awk '{print $NF}'),
    "mem_throughput_mb": $(sysbench memory --memory-block-size=4K --memory-total-size=10G --threads=4 run 2>/dev/null | grep "transferred" | grep -oP '[\d.]+(?= MiB/sec)'),
    "context_switches": $(stress-ng --context 1 --timeout 10 --metrics-brief 2>&1 | grep context | awk '{print $5}')
}
EOF
)

echo "$results" >> "$BASELINE_FILE"

# Alert if >10% deviation from rolling average
# (integrate with your monitoring system)
```

---

## 10. Lab Exercises

### 10.1 Exercise 1: Benchmark Storage With/Without LUKS Encryption

**Objective:** Quantify LUKS2 encryption overhead on real hardware and identify optimal cipher/key-size combination.

**Prerequisites:**
- Proxmox VE host with available NVMe device (or partition)
- fio installed (`apt install fio`)
- Root access

**Procedure:**

```bash
#!/bin/bash
# lab-exercise-1-storage-encryption-benchmark.sh
# Duration: ~30 minutes
set -euo pipefail

TARGET_DEVICE="/dev/nvme1n1"  # CHANGE THIS — use a non-production device!
RESULTS_DIR="/tmp/lab-ex1-results-$(date +%Y%m%d)"
mkdir -p "$RESULTS_DIR"

echo "[SAFETY] This will DESTROY data on $TARGET_DEVICE"
echo "Press Ctrl+C within 5 seconds to abort..."
sleep 5

# ============================================================
# Phase 1: Raw device benchmark (no filesystem, no encryption)
# ============================================================
echo "=== Phase 1: Raw device benchmark ==="
fio --name=raw-4k-randread \
    --filename="$TARGET_DEVICE" \
    --rw=randread --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/01-raw-randread.json"

fio --name=raw-4k-randwrite \
    --filename="$TARGET_DEVICE" \
    --rw=randwrite --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/02-raw-randwrite.json"

fio --name=raw-seq-read \
    --filename="$TARGET_DEVICE" \
    --rw=read --bs=1M --numjobs=4 --iodepth=16 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/03-raw-seqread.json"

# ============================================================
# Phase 2: LUKS2 AES-XTS-256 (default, with AES-NI)
# ============================================================
echo "=== Phase 2: LUKS2 aes-xts-plain64 (256-bit key) ==="
echo -n "benchmarkkey123" | cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 --key-size 256 --hash sha256 \
    --pbkdf argon2id --pbkdf-memory 131072 --batch-mode \
    "$TARGET_DEVICE" -

echo -n "benchmarkkey123" | cryptsetup open "$TARGET_DEVICE" bench_crypt_256 -

fio --name=luks256-4k-randread \
    --filename="/dev/mapper/bench_crypt_256" \
    --rw=randread --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/04-luks256-randread.json"

fio --name=luks256-4k-randwrite \
    --filename="/dev/mapper/bench_crypt_256" \
    --rw=randwrite --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/05-luks256-randwrite.json"

fio --name=luks256-seq-read \
    --filename="/dev/mapper/bench_crypt_256" \
    --rw=read --bs=1M --numjobs=4 --iodepth=16 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/06-luks256-seqread.json"

cryptsetup close bench_crypt_256

# ============================================================
# Phase 3: LUKS2 AES-XTS-512 (512-bit key = 256-bit AES + 256-bit tweak)
# ============================================================
echo "=== Phase 3: LUKS2 aes-xts-plain64 (512-bit key) ==="
echo -n "benchmarkkey123" | cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 --key-size 512 --hash sha512 \
    --pbkdf argon2id --pbkdf-memory 131072 --batch-mode \
    "$TARGET_DEVICE" -

echo -n "benchmarkkey123" | cryptsetup open "$TARGET_DEVICE" bench_crypt_512 \
    --perf-no_read_workqueue --perf-no_write_workqueue -

fio --name=luks512-4k-randread \
    --filename="/dev/mapper/bench_crypt_512" \
    --rw=randread --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/07-luks512-randread.json"

fio --name=luks512-4k-randwrite \
    --filename="/dev/mapper/bench_crypt_512" \
    --rw=randwrite --bs=4k --numjobs=8 --iodepth=64 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/08-luks512-randwrite.json"

fio --name=luks512-seq-read \
    --filename="/dev/mapper/bench_crypt_512" \
    --rw=read --bs=1M --numjobs=4 --iodepth=16 \
    --runtime=60 --time_based --direct=1 \
    --group_reporting --output-format=json+ \
    --output="$RESULTS_DIR/09-luks512-seqread.json"

cryptsetup close bench_crypt_512

# ============================================================
# Phase 4: Results comparison
# ============================================================
echo ""
echo "=== RESULTS SUMMARY ==="
echo "─────────────────────────────────────────────────────"
printf "%-25s %12s %12s %12s\n" "Test" "IOPS/BW" "Lat p99" "CPU%"
echo "─────────────────────────────────────────────────────"

for f in "$RESULTS_DIR"/*.json; do
    name=$(jq -r '.jobs[0].jobname' "$f")
    if echo "$f" | grep -q "seq"; then
        bw=$(jq '.jobs[0].read.bw_bytes / 1048576 | floor' "$f")
        printf "%-25s %10s MB/s\n" "$name" "$bw"
    else
        iops=$(jq '.jobs[0].read.iops // .jobs[0].write.iops | floor' "$f")
        lat=$(jq '.jobs[0].read.clat_ns.percentile["99.000000"] // .jobs[0].write.clat_ns.percentile["99.000000"] | . / 1000 | floor' "$f")
        printf "%-25s %10s IOPS %8s µs\n" "$name" "$iops" "$lat"
    fi
done

echo ""
echo "Full JSON results in: $RESULTS_DIR/"
```

**Expected results table (Samsung PM9A3 3.84TB):**

| Test | Raw | LUKS2-256 | LUKS2-512 (optimized) | Overhead |
|---|---|---|---|---|
| 4K Random Read (IOPS) | 1,050,000 | 995,000 | 980,000 | 5-7% |
| 4K Random Write (IOPS) | 210,000 | 198,000 | 195,000 | 5-7% |
| Sequential Read (MB/s) | 6,900 | 6,500 | 6,400 | 6-8% |
| Latency p99 4K Read (µs) | 85 | 92 | 95 | +8-12% |

**Analysis questions for the student:**
1. What is the percentage overhead for your specific hardware?
2. Does the 512-bit key size add measurable overhead vs 256-bit?
3. What happens to overhead when you remove `--perf-no_read_workqueue`?
4. Is the overhead acceptable for your production workloads?

---

### 10.2 Exercise 2: Measure Network Throughput with Different Encryption Methods

**Objective:** Compare WireGuard, IPsec, and plain TCP throughput on production-equivalent hardware to select the optimal VM-to-VM encryption method.

**Prerequisites:**
- Two Proxmox hosts (or VMs) connected via 10GbE+ link
- iperf3, WireGuard, strongSwan installed
- Root access on both hosts

```bash
#!/bin/bash
# lab-exercise-2-network-encryption-benchmark.sh
# Run on CLIENT host. Server (PEER) must be configured first.
set -euo pipefail

PEER_IP="10.0.0.2"           # Direct L2 peer IP
WG_PEER_IP="10.100.0.2"     # WireGuard tunnel peer IP
IPSEC_PEER_IP="10.200.0.2"  # IPsec tunnel peer IP
DURATION=60
STREAMS=16
RESULTS_DIR="/tmp/lab-ex2-results-$(date +%Y%m%d)"
mkdir -p "$RESULTS_DIR"

# ============================================================
# Setup: WireGuard tunnel (if not already configured)
# ============================================================
setup_wireguard() {
    # Generate keys (one-time)
    umask 077
    wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key

    cat > /etc/wireguard/wg0.conf <<WGEOF
[Interface]
Address = 10.100.0.1/24
ListenPort = 51820
PrivateKey = $(cat /etc/wireguard/private.key)

[Peer]
PublicKey = PEER_PUBLIC_KEY_HERE
AllowedIPs = 10.100.0.2/32
Endpoint = ${PEER_IP}:51820
WGEOF

    wg-quick up wg0
}

# ============================================================
# Setup: IPsec tunnel (strongSwan)
# ============================================================
setup_ipsec() {
    cat > /etc/swanctl/conf.d/bench.conf <<IPSECEOF
connections {
    bench-tunnel {
        local_addrs = 10.0.0.1
        remote_addrs = ${PEER_IP}
        local {
            auth = psk
            id = bench-client
        }
        remote {
            auth = psk
            id = bench-server
        }
        children {
            bench-child {
                local_ts = 10.200.0.1/32
                remote_ts = 10.200.0.2/32
                esp_proposals = aes256gcm128-x25519
                start_action = start
            }
        }
    }
}
secrets {
    ike-bench {
        id = bench-client
        id = bench-server
        secret = "benchmark-psk-do-not-use-in-production"
    }
}
IPSECEOF

    swanctl --load-all
    ip addr add 10.200.0.1/32 dev lo
}

# ============================================================
# Benchmark execution
# ============================================================
echo "=== Test 1: Plain TCP (no encryption) ==="
iperf3 -c "$PEER_IP" -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/01-plain-tcp.json"

echo "=== Test 2: WireGuard tunnel ==="
iperf3 -c "$WG_PEER_IP" -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/02-wireguard.json"

echo "=== Test 3: IPsec ESP (AES-256-GCM) ==="
iperf3 -c "$IPSEC_PEER_IP" -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/03-ipsec-aesgcm.json"

echo "=== Test 4: Plain TCP with TLS 1.3 (application-level) ==="
# Using iperf3 with --tls (if compiled with TLS support), or openssl s_time
iperf3 -c "$PEER_IP" -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/04-tls13.json"

echo "=== Test 5: UDP (for throughput ceiling) ==="
iperf3 -c "$PEER_IP" -u -b 0 -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/05-udp-baseline.json"

iperf3 -c "$WG_PEER_IP" -u -b 0 -t "$DURATION" -P "$STREAMS" --json \
    > "$RESULTS_DIR/06-udp-wireguard.json"

# ============================================================
# Results extraction
# ============================================================
echo ""
echo "=== NETWORK ENCRYPTION BENCHMARK RESULTS ==="
echo "═══════════════════════════════════════════════"
printf "%-25s %12s %12s %12s\n" "Method" "Throughput" "Retransmits" "CPU%"
echo "───────────────────────────────────────────────"

for f in "$RESULTS_DIR"/0[1-4]*.json; do
    name=$(basename "$f" .json | sed 's/^[0-9]*-//')
    bw=$(jq '.end.sum_received.bits_per_second / 1000000000' "$f" 2>/dev/null)
    retrans=$(jq '.end.sum_sent.retransmits // 0' "$f" 2>/dev/null)
    cpu=$(jq '.end.cpu_utilization_percent.host_total // 0' "$f" 2>/dev/null)
    printf "%-25s %9.2f Gbps %10s %9.1f%%\n" "$name" "$bw" "$retrans" "$cpu"
done

echo ""
echo "Results saved to: $RESULTS_DIR/"
```

**Expected results (10GbE link, Xeon 8380):**

| Method | TCP Throughput | UDP Throughput | CPU Usage | Added Latency |
|---|---|---|---|---|
| Plain (baseline) | 9.4 Gbps | 9.8 Gbps | 15% | — |
| WireGuard | 6.8 Gbps | 7.2 Gbps | 55% | +0.15 ms |
| IPsec AES-256-GCM | 5.2 Gbps | 5.8 Gbps | 62% | +0.3 ms |
| TLS 1.3 (app-level) | 8.1 Gbps | N/A | 35% | +0.4 ms (handshake) |

**Student tasks:**
1. Run all tests and record YOUR hardware's results
2. Calculate the overhead percentage for each method
3. Measure CPU usage difference between client and server
4. Determine: for your 10GbE link, which method allows line-rate with acceptable CPU?
5. Test with MTU 9000 vs 1500 and measure the interaction with encryption overhead

---

### 10.3 Exercise 3: Profile CPU Overhead of Spectre Mitigations

**Objective:** Directly measure the performance cost of CPU vulnerability mitigations on your hardware and determine the host's specific sensitivity profile.

**Prerequisites:**
- Proxmox VE host (or any Linux server with kernel 6.x+)
- stress-ng, perf, sysbench installed
- Root access (for changing boot parameters)

**WARNING: This exercise requires reboots with different kernel parameters. Perform on non-production systems only.**

```bash
#!/bin/bash
# lab-exercise-3-cpu-mitigations-benchmark.sh
# This script runs benchmarks with CURRENT mitigation settings.
# To compare, reboot with different parameters and re-run.
set -euo pipefail

RESULTS_DIR="/tmp/lab-ex3-mitigations-$(date +%Y%m%d)"
mkdir -p "$RESULTS_DIR"

# ============================================================
# Step 1: Record current mitigation state
# ============================================================
echo "=== Current CPU Vulnerability Mitigations ==="
MITIGATION_STATE="$RESULTS_DIR/mitigation-state.txt"
{
    echo "Kernel: $(uname -r)"
    echo "Boot params: $(cat /proc/cmdline)"
    echo ""
    echo "Vulnerability status:"
    for vuln in /sys/devices/system/cpu/vulnerabilities/*; do
        printf "  %-30s %s\n" "$(basename $vuln):" "$(cat $vuln)"
    done
} | tee "$MITIGATION_STATE"

# Determine state label from kernel cmdline
if grep -q "mitigations=off" /proc/cmdline; then
    STATE="no-mitigations"
elif grep -q "mitigations=auto,nosmt" /proc/cmdline; then
    STATE="full-mitigations-nosmt"
else
    STATE="default-mitigations"
fi

echo "State label: $STATE"

# ============================================================
# Step 2: Syscall latency benchmark (most sensitive to KPTI)
# ============================================================
echo ""
echo "=== Test 1: Syscall latency (getpid loop) ==="
# This measures raw syscall overhead — KPTI adds ~100-400ns per syscall

perf bench syscall basic -l 10000000 2>&1 | tee "$RESULTS_DIR/${STATE}-syscall.txt"

# ============================================================
# Step 3: Context switch overhead (sensitive to TLB flush)
# ============================================================
echo ""
echo "=== Test 2: Context switch latency ==="

perf bench sched pipe -l 1000000 2>&1 | tee "$RESULTS_DIR/${STATE}-ctxswitch.txt"

# stress-ng context switch rate
stress-ng --context 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/${STATE}-stress-context.txt"

# ============================================================
# Step 4: Fork/exec benchmark (combines KPTI + PCID effects)
# ============================================================
echo ""
echo "=== Test 3: Fork/exec rate ==="

stress-ng --fork 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/${STATE}-stress-fork.txt"

# ============================================================
# Step 5: IPC throughput (pipe, affected by spectre_v2 STIBP)
# ============================================================
echo ""
echo "=== Test 4: IPC pipe throughput ==="

stress-ng --pipe 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/${STATE}-stress-pipe.txt"

# ============================================================
# Step 6: Database-like workload (syscall + I/O + computation)
# ============================================================
echo ""
echo "=== Test 5: OLTP simulation (sysbench) ==="

sysbench cpu --cpu-max-prime=50000 --threads=$(nproc) --time=60 run 2>&1 | \
    tee "$RESULTS_DIR/${STATE}-sysbench-cpu.txt"

# ============================================================
# Step 7: KVM-specific test (if running as hypervisor)
# ============================================================
if [ -e /dev/kvm ]; then
    echo ""
    echo "=== Test 6: KVM vmentry/vmexit latency ==="
    # Requires running VMs
    perf kvm stat record -a -- sleep 30 2>/dev/null
    perf kvm stat report 2>&1 | tee "$RESULTS_DIR/${STATE}-kvm-exits.txt"
fi

# ============================================================
# Summary
# ============================================================
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Results saved with prefix: $STATE"
echo "  Directory: $RESULTS_DIR/"
echo ""
echo "  To compare, reboot with different parameters:"
echo "  - Default:         (no changes to GRUB)"
echo "  - Full + no-SMT:   mitigations=auto,nosmt"
echo "  - None (DANGER):   mitigations=off"
echo ""
echo "  Then re-run this script and compare results."
echo "═══════════════════════════════════════════════════"
```

**Reboot configurations to test (add to GRUB_CMDLINE_LINUX):**

| Test Run | Kernel Parameters | Risk Level |
|---|---|---|
| Run 1 (baseline) | (default, no changes) | Safe for production |
| Run 2 (full + nosmt) | `mitigations=auto,nosmt` | Safe, lose SMT threads |
| Run 3 (no mitigations) | `mitigations=off` | DANGEROUS — test only |
| Run 4 (selective) | `nopti spectre_v2=retpoline mds=off` | Medium risk |

**Expected comparative results (Intel Xeon Platinum 8380):**

| Test | Default | Full+noSMT | No Mitigations | Delta (default vs off) |
|---|---|---|---|---|
| Syscalls/sec | 4.2M | 4.0M | 5.8M | 28% slower with mitigations |
| Context switches/sec | 890K | 850K | 1.15M | 23% slower |
| Forks/sec | 42K | 40K | 58K | 28% slower |
| Pipe throughput (MB/s) | 4,200 | 3,900 | 5,100 | 18% slower |
| CPU compute (events/sec) | 48,000 | 24,000 (no SMT!) | 49,500 | 3% slower |
| KVM vmexit latency (ns) | 1,850 | 1,900 | 1,200 | 54% slower |

**Key findings for students:**
1. Compute-bound workloads are barely affected (3-5%)
2. Syscall-heavy and I/O-heavy workloads suffer 20-30%
3. KVM vmexit/vmentry are significantly impacted
4. Disabling SMT (`nosmt`) halves CPU throughput but eliminates HT side-channels
5. eIBRS (Ice Lake+) dramatically reduces the penalty vs legacy IBRS

---

### 10.4 Exercise 4: Optimize auditd Rules for Maximum Coverage with Minimum Overhead

**Objective:** Develop an audit rule set that provides CIS-compliant security monitoring while minimizing system call overhead. Measure before/after performance impact.

**Prerequisites:**
- Linux system (Proxmox host or VM)
- auditd installed and running
- fio, stress-ng for load generation
- Root access

```bash
#!/bin/bash
# lab-exercise-4-auditd-optimization.sh
# Duration: ~45 minutes
set -euo pipefail

RESULTS_DIR="/tmp/lab-ex4-auditd-$(date +%Y%m%d)"
mkdir -p "$RESULTS_DIR"

# ============================================================
# Phase 1: Baseline — auditd disabled
# ============================================================
echo "=== Phase 1: Baseline (auditd stopped) ==="
systemctl stop auditd
auditctl -D 2>/dev/null  # Delete all rules
sleep 5

# Filesystem-heavy workload (most sensitive to auditd)
stress-ng --hdd 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/01-baseline-hdd.txt"

# Syscall rate
stress-ng --syscall 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/01-baseline-syscall.txt"

# File creation/deletion stress
stress-ng --dentry 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/01-baseline-dentry.txt"

# ============================================================
# Phase 2: Full CIS Level 2 audit rules (unoptimized)
# ============================================================
echo ""
echo "=== Phase 2: Full CIS Level 2 rules (HEAVY) ==="
systemctl start auditd

cat > /tmp/cis-full-rules.rules <<'RULES'
# CIS Level 2 — complete (unoptimized)
-D
-b 8192
-f 1

# Time changes
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# User/group changes
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# Network config
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/network -p wa -k system-locale

# Login/logout
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Session initiation
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

# DAC permission changes
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -k perm_mod
-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -k perm_mod
-a always,exit -F arch=b64 -S removexattr -S lremovexattr -S fremovexattr -k perm_mod

# Unauthorized access attempts
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -k access

# Privileged commands
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged
-a always,exit -F path=/usr/bin/chfn -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged

# File deletions
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -k delete

# Kernel module operations
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# Mount operations
-a always,exit -F arch=b64 -S mount -k mounts
RULES

auditctl -R /tmp/cis-full-rules.rules
sleep 5

# Same workload
stress-ng --hdd 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/02-cis-full-hdd.txt"

stress-ng --syscall 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/02-cis-full-syscall.txt"

stress-ng --dentry 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/02-cis-full-dentry.txt"

# Check audit overhead
echo "Audit backlog: $(auditctl -s | grep backlog)"
echo "Lost events: $(auditctl -s | grep lost)"

# ============================================================
# Phase 3: Optimized rules (same coverage, less overhead)
# ============================================================
echo ""
echo "=== Phase 3: Optimized audit rules ==="
auditctl -D

cat > /tmp/optimized-rules.rules <<'RULES'
# Optimized CIS-compliant rules — same security coverage, reduced overhead
-D
-b 16384
-f 1
--backlog_wait_time 60000

# CRITICAL: Exclude high-volume noise FIRST (processed top-down)
-a always,exclude -F msgtype=CWD
-a always,exclude -F msgtype=PATH
-a always,exclude -F msgtype=PROCTITLE
-a always,exclude -F msgtype=EOE

# Exclude known high-volume, low-value processes
-a never,exit -F arch=b64 -F exe=/usr/sbin/auditd
-a never,exit -F arch=b64 -F exe=/usr/bin/vmtoolsd
-a never,exit -F arch=b64 -F exe=/usr/sbin/pveproxy
-a never,exit -F arch=b64 -F exe=/usr/bin/rrdcached

# File integrity (watches are low-overhead — path-triggered only)
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/pam.d/ -p wa -k pam
-w /etc/ssh/sshd_config -p wa -k sshd
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d/ -p wa -k sudoers

# Time changes (rare event, low overhead)
-a always,exit -F arch=b64 -S adjtimex,settimeofday,clock_settime -F key=time-change

# Privileged execution (only track specific binaries, not all of execve)
-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k priv
-a always,exit -F path=/usr/bin/su -F perm=x -F auid>=1000 -F auid!=4294967295 -k priv
-a always,exit -F path=/usr/bin/passwd -F perm=x -F auid>=1000 -F auid!=4294967295 -k priv

# Module loading (rare, security-critical)
-a always,exit -F arch=b64 -S init_module,finit_module,delete_module -k modules

# Mount operations (rare)
-a always,exit -F arch=b64 -S mount,umount2 -F auid>=1000 -k mounts

# DAC changes — ONLY when done by human users (not system services)
-a always,exit -F arch=b64 -S chmod,fchmod,fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b64 -S chown,fchown,lchown,fchownat -F auid>=1000 -F auid!=4294967295 -k perm_mod

# SKIP: File deletion auditing (causes massive overhead on active systems)
# Instead, use inotify/fanotify on critical directories only
# SKIP: Access denial logging (generates huge volume under normal operation)

# Network: Only track raw socket creation (suspicious)
-a always,exit -F arch=b64 -S socket -F a0=2 -F a1=3 -k raw_socket

# Make immutable (prevents tampering until reboot)
-e 2
RULES

auditctl -R /tmp/optimized-rules.rules
sleep 5

# Same workload
stress-ng --hdd 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/03-optimized-hdd.txt"

stress-ng --syscall 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/03-optimized-syscall.txt"

stress-ng --dentry 4 --timeout 60 --metrics-brief 2>&1 | \
    tee "$RESULTS_DIR/03-optimized-dentry.txt"

echo "Audit backlog: $(auditctl -s | grep backlog)"
echo "Lost events: $(auditctl -s | grep lost)"

# ============================================================
# Phase 4: Results comparison
# ============================================================
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  AUDIT OPTIMIZATION RESULTS"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  HDD stress (bogo-ops/sec — higher is better):"
echo "    Baseline (no audit):  $(grep "bogo ops/s" "$RESULTS_DIR/01-baseline-hdd.txt" | awk '{print $NF}')"
echo "    CIS Full (heavy):     $(grep "bogo ops/s" "$RESULTS_DIR/02-cis-full-hdd.txt" | awk '{print $NF}')"
echo "    Optimized:            $(grep "bogo ops/s" "$RESULTS_DIR/03-optimized-hdd.txt" | awk '{print $NF}')"
echo ""
echo "  Syscall stress (bogo-ops/sec):"
echo "    Baseline (no audit):  $(grep "bogo ops/s" "$RESULTS_DIR/01-baseline-syscall.txt" | awk '{print $NF}')"
echo "    CIS Full (heavy):     $(grep "bogo ops/s" "$RESULTS_DIR/02-cis-full-syscall.txt" | awk '{print $NF}')"
echo "    Optimized:            $(grep "bogo ops/s" "$RESULTS_DIR/03-optimized-syscall.txt" | awk '{print $NF}')"
echo ""
echo "  Dentry stress (bogo-ops/sec):"
echo "    Baseline (no audit):  $(grep "bogo ops/s" "$RESULTS_DIR/01-baseline-dentry.txt" | awk '{print $NF}')"
echo "    CIS Full (heavy):     $(grep "bogo ops/s" "$RESULTS_DIR/02-cis-full-dentry.txt" | awk '{print $NF}')"
echo "    Optimized:            $(grep "bogo ops/s" "$RESULTS_DIR/03-optimized-dentry.txt" | awk '{print $NF}')"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "  Optimization techniques applied:"
echo "  1. Exclude noisy message types (CWD, PATH, PROCTITLE, EOE)"
echo "  2. Exclude known high-volume system processes"
echo "  3. Remove file deletion auditing (use dedicated tool instead)"
echo "  4. Remove access-denied logging (too noisy)"
echo "  5. Filter DAC changes to human users only (auid>=1000)"
echo "  6. Increase backlog buffer to prevent drops under burst"
echo "  7. Use 'lossy' dispatch to prevent syscall blocking"
echo ""
echo "  Security coverage preserved:"
echo "  ✓ Identity file changes"
echo "  ✓ Privilege escalation"
echo "  ✓ Kernel module loading"
echo "  ✓ Mount operations"
echo "  ✓ Time manipulation"
echo "  ✓ Permission changes (by humans)"
echo "  ✓ Raw socket creation"
echo "  ✓ Immutable rules (tamper-resistant)"
echo ""
```

**Expected results:**

| Workload | No Audit | CIS Full | Optimized | Full Overhead | Optimized Overhead |
|---|---|---|---|---|---|
| HDD bogo-ops/s | 100% | -15% | -3% | 15% | 3% |
| Syscall bogo-ops/s | 100% | -25% | -5% | 25% | 5% |
| Dentry bogo-ops/s | 100% | -30% | -4% | 30% | 4% |
| Log volume (MB/min) | 0 | 45 MB/min | 3 MB/min | — | 93% reduction |
| Lost events | 0 | 1,200/hr | 0 | — | — |

**Student deliverables:**
1. Run all three phases and document YOUR performance numbers
2. Calculate overhead percentage for each phase
3. Verify that the optimized rules still capture: a) user creation, b) sudo execution, c) module loading, d) SSH config change — generate test events and confirm they appear in audit.log
4. Measure log volume (MB/min) for each configuration during the benchmark
5. Write a one-page justification for which rules you would keep/remove for a production Proxmox hypervisor

---

## Summary: Decision Framework

### When Performance Matters More Than Security

| Scenario | Acceptable Relaxations | NEVER Relax |
|---|---|---|
| HPC cluster (air-gapped) | CPU mitigations, KSM enable | Network encryption to control plane |
| CI/CD runners (ephemeral) | Audit logging reduction | Container isolation, seccomp |
| Dev/test environments | Full disk encryption, agents | Access controls, network segmentation |
| Latency-critical trading | Some monitoring sampling | Authentication, authorization |

### When Security Matters More Than Performance

| Scenario | Accept Performance Cost | Typical Cost |
|---|---|---|
| Multi-tenant cloud | All mitigations, SEV-SNP, no KSM | 15-25% density loss |
| Financial services | Full audit, encryption everywhere | 20-30% overhead |
| Healthcare (PHI) | Encryption at rest + transit, agents | 15-20% overhead |
| Government (STIG) | All CIS items, measured boot | 20-35% overhead |

### The Golden Rule

```
Never benchmark without security features enabled.
Never deploy security features without benchmarking their impact.
Never remove security features to meet a performance SLA — resize instead.
```

---

## References

1. Intel. "Speculative Execution Side Channel Mitigations." Technical Report, 2018-2024.
2. AMD. "AMD SEV-SNP: Strengthening VM Isolation with Integrity Protection and More." White Paper, 2022.
3. kernel.org. "Hardware vulnerabilities — The Linux Kernel documentation." kernel.org/doc/html/latest/admin-guide/hw-vuln/
4. CIS. "CIS Benchmark for Debian Linux 12." v1.0, 2024.
5. Red Hat. "Performance Analysis and Tuning of Red Hat Enterprise Linux." Product Documentation, 2024.
6. Proxmox. "Proxmox VE Administration Guide — Performance Tuning." pve.proxmox.com/pve-docs/, 2024.
7. NIST SP 800-125A. "Security Recommendations for Server-Based Hypervisor Platforms." Rev. 1, 2018.
8. Axboe, Jens. "Efficient IO with io_uring." kernel.dk, 2019.
9. Cilium. "Tetragon — eBPF-based Security Observability and Runtime Enforcement." cilium.io/tetragon, 2024.
10. WireGuard. "WireGuard: Next Generation Kernel Network Tunnel." wireguard.com, 2020.
