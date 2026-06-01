# Storage Encryption and Data-at-Rest Protection in Virtual Environments

> **Course module:** VMware to Proxmox VE Migration
> **Position in path:** Phase 9 — Security Hardening - Module 30 (see `00-SYLLABUS.md`)
> **Prerequisites:** modules 01-02 (VMware and Proxmox fundamentals), module 03 (advanced storage), module 12 (security and compliance), module 20 (hypervisor hardening), module 24 (backup encryption and integrity); solid understanding of symmetric/asymmetric cryptography (AES, RSA, ECDH), hashing (SHA-256/SHA-512), block device architecture (dm, LVM, ZFS, Ceph), TPM 2.0 architecture, Linux kernel crypto subsystem, KMIP protocol basics.
> **Learning objectives.** Upon completion the reader will be able to:
> 1. explain **encryption fundamentals for storage** — symmetric ciphers, key hierarchies, key derivation functions, hardware acceleration, and quantify performance impact;
> 2. configure **VM disk encryption** on both VMware (VM Encryption, encrypted vMotion) and Proxmox (LUKS2, dm-crypt, qcow2 native encryption, TPM auto-unlock);
> 3. implement **storage backend encryption** across ZFS, Ceph, LVM, NFS, iSCSI, and vSAN;
> 4. design and operate a **key management infrastructure** — KMIP, HashiCorp Vault, cloud KMS, key lifecycle, key ceremony, disaster recovery;
> 5. evaluate **self-encrypting drives** — OPAL 2.0, TCG Enterprise, firmware vulnerabilities (Radboud research), and compare with software encryption;
> 6. secure **backup and replication** with encryption — PBS client-side encryption, Veeam, tape, cloud backup, encrypted DR channels;
> 7. execute and defend against **encryption attacks** — cold boot, evil maid, DMA, key extraction from memory, side-channel, implementation flaws;
> 8. perform **secure data destruction** — cryptographic erasure, ATA Secure Erase, NVMe format, NIST SP 800-88 guidance, physical destruction;
> 9. satisfy **compliance and audit** requirements — PCI-DSS, HIPAA, GDPR, SOX, FedRAMP encryption mandates, key management audit;
> 10. execute a **hands-on lab** — complete encryption stack from ZFS pool through Vault KMS to encrypted PBS backups, with offensive verification.
> **Estimated time:** reading 120-180 min - lab execution 6-10 hours - production implementation 4-8 weeks
> **Level:** expert (Dreyfus 5); offensive security awareness required
> **Last updated:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x; PBS 3.x; vSphere 7.x/8.x; ZFS 2.2/2.3; Ceph Reef/Squid; cryptsetup 2.7+; LUKS2; HashiCorp Vault 1.17+; dm-crypt 1.7+; Linux kernel 6.x; KMIP 2.0; OPAL 2.0; NIST SP 800-88 Rev.1.

---

## Concept Map

```
+===========================================================================+
|      Storage Encryption & Data-at-Rest: Defence-in-Depth Stack            |
+===========================================================================+
|                                                                           |
|  1. ENCRYPTION FUNDAMENTALS                                               |
|     AES-256-XTS (disk) / AES-256-GCM (network/auth)                      |
|     Key hierarchy: DEK -> KEK -> Master Key                               |
|     KDF: PBKDF2 / Argon2id / HKDF                                        |
|     Hardware: AES-NI -> ~3.5 GB/s/core                                    |
|         |                                                                 |
|         v                                                                 |
|  2. VM DISK ENCRYPTION                                                    |
|     VMware VM Encryption (vCenter + KMS)                                  |
|     Proxmox: LUKS2 + dm-crypt + TPM auto-unlock                          |
|     qcow2 LUKS format / Guest FDE (BitLocker, LUKS, FileVault)           |
|         |                                                                 |
|         v                                                                 |
|  3. STORAGE BACKEND ENCRYPTION                                            |
|     ZFS native / Ceph OSD+RBD / LVM+LUKS patterns                        |
|     NFS krb5p / iSCSI IPSec / vSAN DAR+DIT                               |
|         |                                                                 |
|         v                                                                 |
|  4. KEY MANAGEMENT                                                        |
|     KMIP / Vault Transit / Cloud KMS                                      |
|     Key lifecycle / Ceremony / HSM / Shamir m-of-n                        |
|         |                                                                 |
|         v                                                                 |
|  5. SELF-ENCRYPTING DRIVES                                                |
|     OPAL 2.0 / TCG Enterprise / sedutil                                   |
|     Firmware attacks (Radboud) / SED vs software encryption               |
|         |                                                                 |
|         v                                                                 |
|  6. BACKUP & REPLICATION ENCRYPTION                                       |
|     PBS AES-256-GCM / Veeam / Tape LTO / Cloud                           |
|     Encrypted DR channels                                                 |
|         |                                                                 |
|         v                                                                 |
|  7. ENCRYPTION ATTACKS & WEAKNESSES                                       |
|     Cold boot / Evil maid / DMA / Side-channel                            |
|     Key extraction / Implementation bugs                                  |
|         |                                                                 |
|         v                                                                 |
|  8. SECURE DATA DESTRUCTION                                               |
|     Crypto erase / ATA Secure Erase / NVMe Format                        |
|     NIST 800-88 / Physical destruction / Cloud verification               |
|         |                                                                 |
|         v                                                                 |
|  9. COMPLIANCE & AUDIT                                                    |
|     PCI-DSS / HIPAA / GDPR / SOX / FedRAMP                               |
|     Key access logs / Rotation / Separation of duties                     |
|         |                                                                 |
|         v                                                                 |
| 10. LAB: COMPLETE ENCRYPTION STACK                                        |
|     ZFS + LUKS + TPM + Vault + PBS + DR + Attack tests                    |
|                                                                           |
+===========================================================================+
```

---

## Table of Contents

1. [Encryption Fundamentals for Storage](#1-encryption-fundamentals-for-storage)
2. [VM Disk Encryption](#2-vm-disk-encryption)
3. [Storage Backend Encryption](#3-storage-backend-encryption)
4. [Key Management](#4-key-management)
5. [Self-Encrypting Drives](#5-self-encrypting-drives)
6. [Encryption for Backup and Replication](#6-encryption-for-backup-and-replication)
7. [Encryption Attacks and Weaknesses](#7-encryption-attacks-and-weaknesses)
8. [Secure Data Destruction](#8-secure-data-destruction)
9. [Compliance and Audit](#9-compliance-and-audit)
10. [Lab: Implement Complete Encryption Stack](#10-lab-implement-complete-encryption-stack)

---

## 1. Encryption Fundamentals for Storage

### 1.1 Symmetric Encryption for Block Devices

Storage encryption operates almost exclusively with symmetric ciphers because asymmetric algorithms (RSA, ECDH) are orders of magnitude too slow for the throughput demands of disk I/O. The two dominant modes in storage contexts are AES-256-XTS and AES-256-GCM.

**AES-256-XTS — the disk encryption standard.** XTS (XEX-based Tweaked-codebook mode with ciphertext Stealing) is defined in IEEE 1619-2007 and is the mode of choice for full-disk and partition-level encryption. It is a tweakable block cipher that operates on 16-byte blocks with a 512-bit key (two 256-bit keys: one for AES encryption, one for the tweak function). The tweak incorporates the sector number and block offset within the sector, ensuring that identical plaintext blocks at different disk locations produce different ciphertext — critical for preventing pattern leakage across a disk image.

XTS properties relevant to storage:

| Property | Implication |
|---|---|
| No authentication | XTS does not provide integrity. An attacker with write access to the ciphertext can flip bits and produce controlled (though somewhat unpredictable) changes in plaintext. This is acceptable for disk encryption because the threat model assumes the attacker has physical access to a powered-off disk, not live write access. |
| Sector-level random access | Any sector can be decrypted independently without reading adjacent sectors. This is essential for random I/O patterns in databases and VM images. |
| Ciphertext same size as plaintext | No expansion — a 512-byte sector encrypts to exactly 512 bytes. This avoids alignment and capacity overhead. |
| Two keys | The tweak key and encryption key are independent. If one is compromised, the other still provides partial protection. LUKS2 derives both from a single master key via key stretching. |

**AES-256-GCM — authenticated encryption for network and backup.** GCM (Galois/Counter Mode) provides both confidentiality and authentication (AEAD — Authenticated Encryption with Associated Data). It produces a 128-bit authentication tag alongside the ciphertext, allowing the receiver to verify that the ciphertext has not been tampered with. GCM is the standard for network encryption (TLS 1.3), backup encryption (PBS), and any scenario where integrity verification is as important as confidentiality.

GCM critical constraints:

- **IV uniqueness is catastrophic if violated.** GCM uses a 96-bit IV (initialization vector). Reusing an IV with the same key allows an attacker to recover the authentication key via XOR of the two ciphertext streams and then forge arbitrary authenticated messages. This is not a theoretical concern — real-world IV reuse bugs have been found in TLS implementations and in custom backup encryption schemes.
- **Performance.** GCM is slightly faster than XTS for sequential I/O because it uses a single key and simpler arithmetic (GHASH over GF(2^128)), but it requires strict sequential processing of the authentication tag chain, making random-access decryption of individual blocks impossible without recomputing from the start of the authenticated segment. This is why GCM is not used for disk encryption.

### 1.2 Key Hierarchy — DEK, KEK, Master Key

Production encryption systems never use a single key. They implement a hierarchy that separates the key that touches data from the key that protects that key:

```
                    +------------------+
                    |   MASTER KEY     |
                    | (HSM / KMS root) |
                    +--------+---------+
                             |
                    wraps    |
                             v
                    +------------------+
                    | KEY ENCRYPTING   |
                    | KEY (KEK)        |
                    | per-tenant or    |
                    | per-cluster      |
                    +--------+---------+
                             |
                    wraps    |
                             v
                    +------------------+
                    | DATA ENCRYPTING  |
                    | KEY (DEK)        |
                    | per-disk or      |
                    | per-dataset      |
                    +------------------+
                             |
                    encrypts |
                             v
                    +------------------+
                    |   DISK DATA      |
                    +------------------+
```

**DEK (Data Encrypting Key).** The symmetric key that directly encrypts/decrypts data on the storage device. In LUKS2, this is the "volume key" (also called the "master key" in older LUKS1 documentation — confusingly). The DEK is generated randomly at volume creation time and never leaves the kernel crypto subsystem in plaintext during normal operation.

**KEK (Key Encrypting Key).** Wraps (encrypts) the DEK. In LUKS2, each keyslot stores a copy of the DEK encrypted with a key derived from a passphrase or token. In enterprise KMS deployments, the KEK is stored in Vault or an HSM and is used to wrap/unwrap DEKs via API calls.

**Master Key.** The root key in a KMS or HSM. It protects all KEKs. In HashiCorp Vault's Transit engine, this is the "root key" that encrypts the Transit engine's internal keys. In AWS KMS, it is the "Customer Master Key" (CMK). The master key should never be exportable and ideally resides in FIPS 140-2 Level 3 (or higher) hardware.

**Why this hierarchy matters operationally:**

- **Key rotation without re-encrypting data.** To rotate a KEK, you decrypt the DEK with the old KEK, re-encrypt the DEK with the new KEK, and store the new wrapped DEK. The actual disk data is untouched. This operation takes milliseconds regardless of disk size.
- **Key escrow.** You can escrow the KEK (or an additional copy of the wrapped DEK) in a geographically separate location without exposing the plaintext DEK.
- **Access revocation.** Destroying a KEK renders all DEKs it protected unrecoverable, effectively performing cryptographic erasure of all associated data.

### 1.3 Key Derivation — PBKDF2, Argon2, HKDF

When encryption keys are derived from human-chosen passphrases, a Key Derivation Function (KDF) transforms the low-entropy passphrase into a high-entropy key while making brute-force attacks computationally expensive.

**PBKDF2 (Password-Based Key Derivation Function 2).** Defined in RFC 8018. Iterates a PRF (typically HMAC-SHA256) a configurable number of times. LUKS1 used PBKDF2 exclusively. The weakness: PBKDF2 is trivially parallelizable on GPUs because it is memory-light. A modern GPU can compute billions of PBKDF2-HMAC-SHA256 iterations per second across many candidate passwords simultaneously.

**Argon2id.** Winner of the 2015 Password Hashing Competition (PHC). Argon2id is the hybrid variant combining Argon2i (data-independent memory access — side-channel resistant) and Argon2d (data-dependent — GPU-resistant). LUKS2 defaults to argon2id since cryptsetup 2.4. Argon2id has three tunable parameters:

| Parameter | Meaning | LUKS2 default (cryptsetup 2.7) |
|---|---|---|
| `-t` (time) | Number of iterations over memory | Benchmarked at format time to target ~2 seconds |
| `-m` (memory) | Memory cost in KiB | 1 GiB (1048576 KiB) |
| `-p` (parallelism) | Number of threads | 4 |

The memory cost is what makes Argon2id GPU-resistant: a GPU with 10,000 cores but limited per-core memory cannot run 10,000 parallel Argon2id evaluations each requiring 1 GiB of RAM.

```bash
# Verify the KDF configuration of an existing LUKS2 volume
cryptsetup luksDump /dev/sda3 | grep -A 10 "PBKDF:"
# Output example:
#   PBKDF:      argon2id
#   Time cost:  4
#   Memory:     1048576
#   Threads:    4
```

**HKDF (HMAC-based Key Derivation Function).** Defined in RFC 5869. Unlike PBKDF2/Argon2, HKDF is not a password-based KDF — it is designed to derive multiple cryptographic keys from a single high-entropy input key material (IKM). ZFS encryption uses HKDF internally to derive per-block encryption keys from the dataset wrapping key. HKDF is fast (single HMAC pass) because it assumes the input already has sufficient entropy.

### 1.4 Hardware Acceleration — AES-NI

AES-NI (Advanced Encryption Standard New Instructions) is an x86/x86_64 instruction set extension present in virtually all Intel CPUs since Westmere (2010) and all AMD CPUs since Bulldozer (2011). It provides hardware-accelerated AES operations via six instructions: AESENC, AESENCLAST, AESDEC, AESDECLAST, AESKEYGENASSIST, AESIMC.

**Performance benchmarks (cryptsetup benchmark on Xeon Silver 4310):**

```bash
$ cryptsetup benchmark
# Tests are approximate using memory only (no storage IO).
PBKDF2-sha1      2553012 iterations per second for 256-bit key
PBKDF2-sha256    3456204 iterations per second for 256-bit key
PBKDF2-sha512    1423076 iterations per second for 256-bit key
   argon2id       8 iterations, 1048576 memory, 4 parallel threads
                  (benchmark takes ~2.1 seconds)

#  Algorithm |       Key |      Encryption |      Decryption
     aes-cbc        256b      3546.2 MiB/s      3812.4 MiB/s
 serpent-cbc        256b       112.6 MiB/s       542.3 MiB/s
 twofish-cbc        256b       215.4 MiB/s       278.1 MiB/s
     aes-xts        256b      3421.8 MiB/s      3498.5 MiB/s
 serpent-xts        256b       508.3 MiB/s       498.7 MiB/s
 twofish-xts        256b       265.2 MiB/s       269.8 MiB/s
```

Key observations:

- AES-XTS with AES-NI achieves approximately **3.4 GB/s per core**. This exceeds the throughput of a single NVMe SSD (typical sequential write: 3-7 GB/s), meaning encryption is not the bottleneck on single-drive configurations.
- Without AES-NI, AES throughput drops to approximately 200-400 MiB/s — a 10x penalty that makes encryption the limiting factor on fast storage.
- Alternative ciphers (Serpent, Twofish) are dramatically slower even with constant-time implementations. There is no practical reason to use them unless post-quantum concerns drive algorithm diversity (speculative at this time).

**Verify AES-NI support:**

```bash
grep -m1 aes /proc/cpuinfo
# flags : ... aes ...

# Verify the kernel is using AES-NI accelerated modules
lsmod | grep aesni
# aesni_intel  ...
```

### 1.5 Performance Impact of Encryption

Encryption is not free even with AES-NI. The overhead varies by workload pattern:

| Workload | Overhead (AES-NI) | Overhead (no AES-NI) | Bottleneck |
|---|---|---|---|
| Sequential read/write (large blocks) | 1-3% throughput loss | 40-60% throughput loss | CPU (without AES-NI) |
| Random 4K IOPS | 3-8% IOPS loss | 15-30% IOPS loss | CPU context switches for crypto operations |
| Database OLTP | 5-10% latency increase | 25-50% latency increase | Per-IO crypto overhead |
| VM boot (many small reads) | 5-15% longer boot | 30-80% longer boot | KDF computation at unlock + random read overhead |
| Deduplication + encryption | Encryption breaks dedup entirely | Same | Encrypted blocks are pseudorandom — no dedup possible |
| Compression + encryption | Encryption breaks compression (post-encryption) | Same | Encrypted data is incompressible; compress before encrypting |

**Critical architectural note:** Encryption and deduplication are fundamentally incompatible when encryption occurs first. If you encrypt a block and then attempt deduplication, every block is pseudorandom and unique — dedup ratio approaches 1:1. ZFS handles this correctly by compressing and deduplicating before encrypting. Ceph does not support deduplication with encryption at the OSD level.

**Latency impact on VM I/O path:** In a Proxmox environment with LUKS2 on top of ZFS, every VM I/O request traverses: guest filesystem -> virtio-blk/scsi -> QEMU -> host kernel -> dm-crypt (LUKS) -> ZFS (compress + checksum) -> physical disk. The dm-crypt layer adds a kernel crypto operation per I/O, which on a busy host with 40+ VMs can consume 5-15% of total CPU capacity. Monitor with `perf top` and look for `crypto_*` and `crypt_convert` functions.

---

## 2. VM Disk Encryption

### 2.1 VMware VM Encryption

VMware VM Encryption was introduced in vSphere 6.5 and is an encryption layer managed by vCenter Server. It encrypts VM files (VMDK, VMX, NVRAM, logs, snapshots) using AES-256-XTS for disk data and AES-256-GCM for non-disk VM files.

**Architecture:**

```
  vCenter Server
       |
       |  KMIP (TCP 5696)
       v
  +----------+       +------------------+
  | KMS       | <---> | HSM (optional)   |
  | (Vault,   |       | FIPS 140-2 L3    |
  |  Thales,  |       +------------------+
  |  HyTrust) |
  +-----+-----+
        |
        | KEK (wrapped)
        v
  +-----------+
  | vCenter   |
  | stores    |
  | key IDs   |
  +-----+-----+
        |
        | DEK pushed to ESXi host
        v
  +-----------+
  | ESXi Host |
  | encrypts  |
  | VM I/O    |
  +-----------+
```

**vCenter KMS integration:**

1. vCenter connects to an external KMIP 1.1+ compliant KMS (Key Management Interoperability Protocol).
2. vCenter requests the KMS to generate a KEK. The KMS returns a KEK identifier (key ID) and the wrapped key material.
3. When a VM is encrypted, vCenter generates a random DEK locally, encrypts it with the KEK, and stores the encrypted DEK in the VM's configuration.
4. At VM power-on, vCenter retrieves the KEK from the KMS, unwraps the DEK, and pushes the plaintext DEK to the ESXi host via a secure channel.
5. The ESXi host's I/O filter (`iofilter-crypto`) performs AES-256-XTS encryption/decryption on all disk I/O.

**Policy-based encryption:** VM encryption can be applied via VM Storage Policies. A storage policy with the "VM Encryption" component can be assigned to a VM, a specific VMDK, or an entire datastore. This allows granular control — encrypt only the VMDK containing PII while leaving the OS disk unencrypted for performance.

**Encrypted vMotion:** When a VM is encrypted, vMotion of that VM uses encrypted vMotion automatically (AES-256-GCM for the migration data stream). Unencrypted VMs can also use encrypted vMotion if configured in the VM settings (set to "Opportunistic" or "Required"). Encrypted vMotion protects memory contents in transit between hosts.

**Limitations and operational gotchas:**

- VM Encryption requires a functioning KMS. If the KMS is unreachable, encrypted VMs cannot power on. This is a single point of failure that must be addressed with KMS clustering and geographic redundancy.
- Snapshots of encrypted VMs are encrypted, but the snapshot delta files use independent DEKs. Reverting a snapshot does not change the base DEK.
- VM Encryption is not compatible with Storage I/O Control (SIOC) resource management and some backup solutions that require direct VMDK access (SAN transport mode in VADP). HotAdd transport mode works with encrypted VMs.
- vTPM (Virtual Trusted Platform Module) for VM Encryption requires vSphere 7.0+ and is distinct from guest-level TPM — it provides a cryptographic anchor for the VM's encryption keys within the ESXi host's memory.

### 2.2 Proxmox — LUKS2 for VM Disks

Proxmox VE does not provide a built-in "click to encrypt VM" feature comparable to VMware's VM Encryption. Instead, encryption is implemented at the storage layer using Linux's dm-crypt/LUKS2, giving the administrator more control but requiring explicit configuration.

**LUKS2 for VM disk images on LVM-Thin:**

```bash
# Create a LUKS2-encrypted logical volume for a VM disk
lvcreate -n vm-100-disk-0 -L 50G pve/data-thin

# Format with LUKS2 (argon2id KDF, AES-256-XTS)
cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --pbkdf argon2id \
  --pbkdf-memory 1048576 \
  --pbkdf-parallel 4 \
  --label vm-100-disk-0-crypt \
  /dev/pve/vm-100-disk-0

# Open the encrypted volume
cryptsetup luksOpen /dev/pve/vm-100-disk-0 vm-100-disk-0-crypt

# The decrypted block device is now at /dev/mapper/vm-100-disk-0-crypt
# Point the VM's disk configuration to this device
```

**dm-crypt configuration for Proxmox VMs:**

The VM configuration file (`/etc/pve/qemu-server/100.conf`) references the decrypted device:

```
scsi0: /dev/mapper/vm-100-disk-0-crypt,size=50G
```

Alternatively, for ZFS-backed storage, encryption is applied at the ZFS dataset level (see section 3.1), which is transparent to the VM.

### 2.3 TPM Auto-Unlock

Manual passphrase entry at boot is impractical for hypervisor hosts with dozens of encrypted volumes. Clevis + Tang or Clevis + TPM2 provides automated unlock tied to hardware state.

**Clevis + TPM2 auto-unlock for LUKS2:**

```bash
# Install clevis and TPM2 support
apt install clevis clevis-luks clevis-tpm2 tpm2-tools

# Bind LUKS volume to TPM2 PCR policy
# PCR 7 = Secure Boot state, PCR 0 = firmware, PCR 1 = firmware config
clevis luks bind -d /dev/pve/vm-100-disk-0 tpm2 '{"pcr_bank":"sha256","pcr_ids":"0,1,7"}'

# Verify binding
clevis luks list -d /dev/pve/vm-100-disk-0
# 1: tpm2 '{"hash":"sha256","key":"ecc","pcr_bank":"sha256","pcr_ids":"0,1,7"}'

# Enable automatic unlock at boot via initramfs
# For Debian/Proxmox:
apt install clevis-initramfs
update-initramfs -u -k all
```

**Security properties of TPM auto-unlock:**

- The LUKS keyslot is sealed to specific TPM PCR (Platform Configuration Register) values. If the firmware, bootloader, or Secure Boot configuration changes, the PCR values change, and the TPM refuses to unseal the key.
- This protects against evil maid attacks (section 7.2): an attacker who modifies the bootloader will change PCR values, preventing auto-unlock and forcing manual passphrase entry (which alerts the administrator).
- TPM auto-unlock does **not** protect against an attacker who has both physical access to the powered-on machine and the ability to extract keys from memory (cold boot attack). The key is in RAM once unsealed.

**Clevis + Tang (network-bound disk encryption):**

For environments where TPM is unavailable or where you want to bind decryption to network presence (the disk only decrypts when the server is on the correct network and can reach the Tang server):

```bash
# On Tang server (separate machine, minimal attack surface)
apt install tang
systemctl enable --now tangd.socket
# Tang listens on TCP 80 by default; firewall accordingly

# On Proxmox host
clevis luks bind -d /dev/pve/vm-100-disk-0 tang '{"url":"http://tang.internal:80"}'
update-initramfs -u -k all
```

### 2.4 qcow2 Encryption — LUKS Format

QEMU's qcow2 image format supports built-in encryption via the LUKS format (not the deprecated qcow2 AES encryption, which was weak and is removed in modern QEMU).

```bash
# Create a LUKS-encrypted qcow2 image
qemu-img create -f qcow2 \
  --object secret,id=sec0,data=MyPassphrase \
  -o encrypt.format=luks,encrypt.key-secret=sec0 \
  /var/lib/vz/images/100/vm-100-disk-0.qcow2 50G

# Convert an existing unencrypted qcow2 to encrypted
qemu-img convert -f qcow2 -O qcow2 \
  --object secret,id=sec0,data=MyPassphrase \
  -o encrypt.format=luks,encrypt.key-secret=sec0 \
  source.qcow2 encrypted.qcow2

# Verify encryption
qemu-img info --object secret,id=sec0,data=MyPassphrase encrypted.qcow2
```

The qcow2 LUKS format uses AES-256-XTS with a LUKS header embedded within the qcow2 file. Key management follows the standard LUKS keyslot model — up to 32 keyslots per image.

**When to use qcow2 encryption vs LUKS on the block device:**

| Criterion | qcow2 LUKS | Block-level LUKS2 |
|---|---|---|
| Portability | Encrypted image is a single file, easy to copy | Tied to block device; requires `cryptsetup` to access |
| Snapshots | qcow2 snapshots work transparently | LVM/ZFS snapshots operate on ciphertext |
| Performance | Slight overhead from qcow2 metadata layer | Direct block I/O, minimal overhead |
| Key management | Key in qcow2 header; must be provided at VM start | Integrated with system keyring, Clevis, TPM |
| Proxmox integration | Limited GUI support | Better integration with systemd-cryptsetup |

### 2.5 Full Disk Encryption Inside Guest — BitLocker, LUKS, FileVault

Guest-level FDE (Full Disk Encryption) encrypts the virtual disk from within the guest OS. This provides defence in depth: even if the hypervisor host is compromised and the host-level encryption keys are extracted, the guest's data remains protected by a separate key that the hypervisor never sees.

**BitLocker with virtual TPM (vTPM):**

Proxmox VE 8.x supports vTPM 2.0 via QEMU's `tpm-crb` device backed by `swtpm`. Configuration in the VM:

```
# In /etc/pve/qemu-server/100.conf
tpmstate0: local-lvm:vm-100-tpmstate-disk-0,size=4M,version=v2.0
```

Windows guests with vTPM can enable BitLocker with TPM auto-unlock. The vTPM state is stored as a disk on the Proxmox storage backend — encrypt this storage to avoid exposing the vTPM's secrets.

**LUKS inside a Linux guest:**

A Linux guest can use LUKS2 on its virtual disk. The guest's initramfs handles key entry (or Clevis for automation). This is orthogonal to host-level encryption and provides an independent encryption domain.

**FileVault on macOS guests:**

macOS guests (where legally permitted) can use FileVault 2 (AES-256-XTS). macOS requires a virtual Secure Enclave or equivalent mechanism for key storage, which is not natively provided by QEMU/KVM. FileVault in VMs typically falls back to password-based unlock.

**Layering considerations:**

Encrypting at both host level and guest level means double encryption — each I/O passes through two AES-XTS operations. With AES-NI, the CPU overhead is approximately 2-5% additional, which is acceptable for sensitive workloads. The security benefit is a separate trust domain: the guest encryption key is unknown to the hypervisor administrator.

---

## 3. Storage Backend Encryption

### 3.1 ZFS Encryption

ZFS native encryption (available since OpenZFS 0.8.0, mature in 2.0+) encrypts data at the dataset level. It operates between the ZFS logical layer (after compression and deduplication) and the physical write layer (before checksumming at the disk level).

**Key properties:**

- **Encryption algorithms:** `aes-256-ccm` (default), `aes-256-gcm` (available, recommended for new deployments due to better performance with AES-NI).
- **Encryption scope:** Data blocks and most metadata are encrypted. Dataset names, snapshot names, pool layout, and storage utilization statistics are **not** encrypted — they are visible to anyone with access to the pool.
- **Compression before encryption:** ZFS compresses data (lz4, zstd) before encrypting, preserving compression ratios. This is a significant advantage over block-level encryption where compression operates on ciphertext (useless).
- **Deduplication before encryption:** ZFS deduplicates before encrypting, so identical blocks across datasets with the same encryption key can still be deduplicated. Blocks across different keys cannot be deduplicated.

**Creating an encrypted ZFS pool:**

```bash
# Create an encrypted pool with a passphrase
zpool create -O encryption=aes-256-gcm \
  -O keylocation=prompt \
  -O keyformat=passphrase \
  -O compression=zstd \
  -O atime=off \
  encrypted-pool raidz2 /dev/sd{a,b,c,d,e,f}

# Create an encrypted dataset with a keyfile (for automation)
dd if=/dev/urandom bs=32 count=1 of=/root/.zfs-keys/dataset1.key
chmod 600 /root/.zfs-keys/dataset1.key

zfs create -o encryption=aes-256-gcm \
  -o keylocation=file:///root/.zfs-keys/dataset1.key \
  -o keyformat=raw \
  encrypted-pool/vm-disks

# Verify encryption status
zfs get encryption,keystatus,keyformat encrypted-pool/vm-disks
# NAME                         PROPERTY      VALUE         SOURCE
# encrypted-pool/vm-disks      encryption    aes-256-gcm   -
# encrypted-pool/vm-disks      keystatus     available     -
# encrypted-pool/vm-disks      keyformat     raw           -
```

**Key management for ZFS encryption:**

```bash
# Load a key for a locked dataset
zfs load-key encrypted-pool/vm-disks

# Load all keys (useful at boot)
zfs load-key -a

# Unload a key (lock the dataset — unmounts it)
zfs unload-key encrypted-pool/vm-disks

# Change the wrapping key (does not re-encrypt data — just re-wraps the DEK)
zfs change-key -o keylocation=file:///root/.zfs-keys/dataset1-new.key \
  -o keyformat=raw \
  encrypted-pool/vm-disks

# Inherit encryption from parent (child datasets use parent's key by default)
zfs create encrypted-pool/vm-disks/vm-100
# vm-100 inherits aes-256-gcm and the parent's key
```

**Performance of ZFS encryption (AES-256-GCM vs AES-256-CCM):**

| Operation | AES-256-CCM | AES-256-GCM | No encryption |
|---|---|---|---|
| Sequential write (128K records) | 1.82 GB/s | 2.14 GB/s | 2.21 GB/s |
| Sequential read (128K records) | 1.95 GB/s | 2.31 GB/s | 2.38 GB/s |
| Random 4K write IOPS | 48,200 | 51,600 | 53,100 |
| Random 4K read IOPS | 62,100 | 67,400 | 69,800 |
| CPU overhead (% of single core) | 12-18% | 8-14% | baseline |

GCM outperforms CCM because AES-NI has specific PCLMULQDQ instructions that accelerate the GHASH polynomial multiplication used in GCM.

### 3.2 Ceph Encryption

Ceph provides multiple encryption layers depending on where in the stack you apply it.

**OSD Encryption (dm-crypt on OSD devices):**

The most common approach is encrypting each OSD's underlying block device with LUKS2/dm-crypt. Ceph itself is unaware of the encryption — it writes to what it thinks is a raw block device, and dm-crypt transparently encrypts/decrypts.

```bash
# When deploying OSDs with ceph-volume, enable dm-crypt:
ceph-volume lvm create --data /dev/sdb --dmcrypt

# This creates a LUKS2 volume, opens it, and creates the OSD on the decrypted device.
# The LUKS key is stored in the Ceph cluster's key-value store (ceph config-key).
# Automatic unlock at OSD start requires the key to be retrievable from the monitor.

# Verify OSD encryption
ceph-volume lvm list
# Output shows: encrypted = True, type = block
```

**RBD Encryption (client-side, since Ceph Pacific 16.2):**

Ceph RBD (RADOS Block Device) supports client-side encryption where the librbd client encrypts data before sending it to the OSD. This provides end-to-end encryption even when the OSD nodes are untrusted.

```bash
# Format an RBD image with LUKS2 encryption
rbd encryption format pool/image luks2 /path/to/passphrase-file

# Map with encryption (QEMU/libvirt integration)
# In libvirt XML:
# <disk type='network' device='disk'>
#   <source protocol='rbd' name='pool/image'>
#     <encryption format='luks2'>
#       <secret type='passphrase' uuid='...'/>
#     </encryption>
#   </source>
# </disk>
```

**Client-side encryption:** Ceph also supports client-side encryption at the RADOS gateway (RGW) level for S3-compatible object storage. Objects are encrypted before storage using SSE-C (Server-Side Encryption with Customer-Provided Keys) or SSE-KMS (integrated with Vault or KMIP).

### 3.3 LVM Encryption Patterns

Three common patterns for combining LVM with LUKS:

**Pattern 1: LUKS on LVM (encrypt individual logical volumes)**

```
Physical Volume -> Volume Group -> Logical Volume -> LUKS -> Filesystem/VM
```

Each LV is independently encrypted. Pros: granular key management, selective encryption. Cons: each LV needs its own key/passphrase; more complex boot process.

**Pattern 2: LVM on LUKS (encrypt the entire physical volume)**

```
Physical Device -> LUKS -> Physical Volume -> Volume Group -> Logical Volume -> Filesystem/VM
```

The entire block device is encrypted with a single LUKS key. LVM operates on the decrypted block device. Pros: single key for the entire disk, simplest boot. Cons: no per-LV key granularity; all data shares one encryption domain.

```bash
# LVM on LUKS setup (typical for Proxmox host disk)
cryptsetup luksFormat --type luks2 /dev/sda3
cryptsetup luksOpen /dev/sda3 cryptroot
pvcreate /dev/mapper/cryptroot
vgcreate pve /dev/mapper/cryptroot
lvcreate -L 100G -n root pve
lvcreate -l 100%FREE -n data pve
```

**Pattern 3: dm-crypt on LVM (no LUKS header)**

Uses dm-crypt without LUKS metadata. The key must be provided directly (no keyslots, no passphrase derivation). Used in specific scenarios where the key is managed entirely by an external KMS and LUKS headers are undesirable (e.g., to avoid information leakage about encrypted volumes).

### 3.4 NFS Encryption — Kerberos with Privacy

NFSv4.1 supports three Kerberos security flavors:

| Flavor | Authentication | Integrity | Encryption |
|---|---|---|---|
| `krb5` | Yes | No | No |
| `krb5i` | Yes | Yes (HMAC) | No |
| `krb5p` | Yes | Yes | Yes (AES-256-CTS) |

Only `krb5p` (privacy) provides data-in-transit encryption. Configuration:

```bash
# On NFS server (/etc/exports)
/exports/vm-storage *(sec=krb5p,rw,sync,no_subtree_check)

# On NFS client (mount)
mount -t nfs4 -o sec=krb5p,vers=4.1 nfs-server:/exports/vm-storage /mnt/nfs

# Performance impact: krb5p adds 15-30% overhead vs krb5 or sys
# because every NFS RPC payload is encrypted with the session key
```

Note: `krb5p` encrypts data in transit only. Data at rest on the NFS server's filesystem is unencrypted unless the server's underlying storage is separately encrypted (e.g., ZFS encryption or LUKS).

### 3.5 iSCSI Encryption — IPSec and TLS Overlay

iSCSI transmits SCSI commands over TCP/IP and has no built-in encryption. Two approaches:

**IPSec tunnel for iSCSI traffic:**

```bash
# Using strongSwan to create an IPSec tunnel between iSCSI initiator and target
# /etc/ipsec.conf on both ends:
conn iscsi-tunnel
    left=10.0.10.1
    right=10.0.10.2
    leftsubnet=10.0.10.1/32
    rightsubnet=10.0.10.2/32
    ike=aes256-sha256-modp2048
    esp=aes256-sha256
    auto=start
    type=tunnel
```

**TLS overlay (iSER or custom):** iSCSI Extensions for RDMA (iSER) can leverage TLS at the transport layer. However, TLS on iSCSI is not widely deployed in production due to the CPU overhead of TLS handshakes per connection and the availability of IPSec as a simpler alternative.

### 3.6 vSAN Encryption

VMware vSAN supports both data-at-rest (DAR) and data-in-transit (DIT) encryption.

**Data-at-rest encryption:** vSAN DAR encryption uses the same vCenter KMS integration as VM Encryption. The encryption is applied at the disk group level on each ESXi host. A DEK is generated per disk group and wrapped with a KEK from the KMS. All data written to the vSAN disk group is encrypted with AES-256-XTS.

**Data-in-transit encryption:** vSAN DIT encryption encrypts inter-host traffic (replication, resync, read from remote) using AES-256-GCM. It can be enabled independently of DAR encryption. DIT encryption adds approximately 10-15% CPU overhead on busy clusters.

---

## 4. Key Management

### 4.1 KMS Architecture

**KMIP (Key Management Interoperability Protocol):** OASIS standard (current version 2.0) that defines a client-server protocol for key management operations. KMIP messages are serialized in TTLV (Tag-Type-Length-Value) format and transported over mutual-TLS on TCP 5696. Operations include Create, Get, Activate, Revoke, Destroy, Register, Locate, and attribute management.

KMS implementations relevant to virtual environments:

| KMS | KMIP Support | Integration | Notes |
|---|---|---|---|
| HashiCorp Vault (Transit + KMIP) | Vault Enterprise KMIP secrets engine | vCenter, ESXi, ZFS (via scripts) | Open-source core; KMIP requires Enterprise license |
| AWS KMS | Via proxy (CloudHSM + KMIP adapter) | vCenter (via adapter), direct API | Regional; keys do not leave AWS |
| Azure Key Vault | Via adapter | vCenter (via adapter), direct API | HSM-backed option available |
| GCP Cloud KMS | Via adapter | vCenter (via adapter), direct API | Regional; CMEK for GCE |
| Thales CipherTrust | Native KMIP | vCenter, Ceph, direct | On-premises or cloud; FIPS 140-2 L3 |
| HyTrust KeyControl | Native KMIP | vCenter (designed for vSphere) | Purpose-built for VMware; acquired by Entrust |

**HashiCorp Vault Transit engine for envelope encryption:**

```bash
# Enable Transit secrets engine
vault secrets enable transit

# Create a named encryption key
vault write -f transit/keys/proxmox-vm-keys \
  type=aes256-gcm96 \
  auto_rotate_period=90d

# Encrypt a DEK (the DEK is base64-encoded plaintext)
DEK_PLAINTEXT=$(openssl rand -base64 32)
vault write transit/encrypt/proxmox-vm-keys \
  plaintext=$(echo -n "$DEK_PLAINTEXT" | base64)
# Returns: ciphertext = vault:v1:xxxxx

# Decrypt the DEK
vault write transit/decrypt/proxmox-vm-keys \
  ciphertext="vault:v1:xxxxx"
# Returns: plaintext = <base64-encoded DEK>

# Rotate the KEK (data keys remain accessible via versioned keys)
vault write -f transit/keys/proxmox-vm-keys/rotate
```

### 4.2 Key Lifecycle

A cryptographic key passes through defined lifecycle states:

```
Generation --> Activation --> Usage --> Deactivation --> Destruction
                                |            |
                                v            v
                           Rotation      Revocation
                                |            |
                                v            v
                           New key      Archive/Escrow
```

**Generation:** Keys must be generated using a cryptographically secure random number generator (CSPRNG). On Linux, `/dev/urandom` is acceptable for most uses; for FIPS-validated environments, use an HSM's RNG. Never generate keys from predictable sources (timestamps, PIDs, sequential counters).

```bash
# Generate a 256-bit key using the kernel CSPRNG
openssl rand 32 > /root/.keys/dek-vm100.key
chmod 600 /root/.keys/dek-vm100.key
```

**Distribution:** Keys should be distributed over authenticated and encrypted channels only. KMIP over mutual TLS, Vault's authenticated API, or physical ceremony are acceptable. Sending keys via email, Slack, or unencrypted file transfer is a finding in any audit.

**Rotation:** Regular rotation limits the blast radius of key compromise. Rotation frequency depends on data sensitivity and compliance requirements:

| Framework | Key rotation requirement |
|---|---|
| PCI-DSS 4.0 | Annually for DEKs; immediately if compromise suspected |
| HIPAA | Not prescribed but required as part of access management; annually recommended |
| FedRAMP | Per NIST SP 800-57 — annually for symmetric keys in most contexts |
| GDPR | Not prescribed but "appropriate technical measures" implies regular rotation |

**Revocation:** When a key is suspected compromised, it must be immediately revoked (set to "deactivated" or "compromised" state in the KMS). Data encrypted with revoked keys must be re-encrypted with new keys — there is no shortcut. The KMS must log the revocation event with timestamp and operator identity.

**Destruction:** Key destruction must be cryptographically irreversible. In a KMS, this means the key material is overwritten and the key ID is tombstoned. In LUKS, `cryptsetup erase` destroys all keyslot material. NIST SP 800-57 Section 8.3 defines key destruction methods.

### 4.3 Key Escrow and Recovery Procedures

Key escrow is the practice of storing a copy of encryption keys with a trusted third party (or a geographically separate location) to enable recovery if the primary keys are lost.

**LUKS header backup as escrow:**

```bash
# Backup the LUKS header (contains all keyslots and encrypted DEK)
cryptsetup luksHeaderBackup /dev/sda3 \
  --header-backup-file /secure-offsite/luks-header-sda3.backup

# Verify the backup is valid
cryptsetup luksHeaderRestore /dev/sda3 \
  --header-backup-file /secure-offsite/luks-header-sda3.backup --test

# CRITICAL: the LUKS header backup contains everything needed to decrypt
# the volume (given any valid passphrase). Store it with the same security
# as the data itself — encrypted, access-controlled, geographically separate.
```

**ZFS key escrow:**

```bash
# Backup the raw key file
cp /root/.zfs-keys/dataset1.key /secure-offsite/zfs-key-dataset1.backup
sha256sum /root/.zfs-keys/dataset1.key /secure-offsite/zfs-key-dataset1.backup
# Verify checksums match
```

### 4.4 Key Ceremony — HSM, Shamir Secret Sharing, M-of-N Key Holders

A key ceremony is a formal, witnessed, documented procedure for generating, distributing, or destroying cryptographic keys. It is required for root/master keys in high-security environments.

**HSM usage in key ceremonies:**

The HSM (Hardware Security Module, e.g., Thales Luna, Utimaco, YubiHSM) generates the master key internally using its hardware RNG. The key never exists in plaintext outside the HSM's tamper-evident boundary. The HSM is initialized in a ceremony involving:

1. Multiple administrators (no single person has complete access)
2. Physical presence at the HSM (cannot be done remotely)
3. Audit log (every operation is logged with timestamp and operator smart card identity)
4. Witness(es) who attest to the procedure but do not have key material

**Shamir's Secret Sharing (SSS) for master key distribution:**

Shamir's scheme splits a secret into `n` shares such that any `m` of the `n` shares can reconstruct the secret, but `m-1` or fewer shares reveal no information. This is used to distribute the master key (or HSM activation PIN) across multiple custodians.

```
Example: 5-of-8 Shamir scheme

Master Key
    |
    v
Shamir Split (m=5, n=8)
    |
    +---> Share 1 --> Custodian A (sealed envelope in safe A)
    +---> Share 2 --> Custodian B (sealed envelope in safe B)
    +---> Share 3 --> Custodian C (different geographic location)
    +---> Share 4 --> Custodian D (different geographic location)
    +---> Share 5 --> Custodian E (CEO/CTO)
    +---> Share 6 --> Custodian F (legal counsel)
    +---> Share 7 --> Custodian G (external auditor)
    +---> Share 8 --> Custodian H (disaster recovery site)

Any 5 custodians can assemble to reconstruct the master key.
No 4 or fewer custodians can recover any information about the key.
```

HashiCorp Vault uses Shamir's Secret Sharing for its unseal keys:

```bash
# Initialize Vault with 5-of-8 Shamir scheme
vault operator init -key-shares=8 -key-threshold=5

# Unseal requires 5 of the 8 key holders
vault operator unseal  # Provide share 1
vault operator unseal  # Provide share 2
vault operator unseal  # Provide share 3
vault operator unseal  # Provide share 4
vault operator unseal  # Provide share 5
# Vault is now unsealed
```

**Key ceremony documentation checklist:**

- Date, time, location (all in UTC ISO 8601)
- Identities of all participants (ceremony operators, witnesses, key holders)
- Serial number of HSM(s) used
- Hash of generated key material (SHA-256 of the public portion or key ID — never the key itself)
- Number of shares generated and threshold
- Tamper-evident seal numbers on envelopes containing shares
- Signatures of all participants
- Secure destruction of any temporary media used during the ceremony

### 4.5 Disaster Recovery for Encryption Keys

If all copies of an encryption key are lost, the encrypted data is permanently unrecoverable. DR planning for encryption keys is therefore as critical as DR planning for the data itself.

**Key backup strategies:**

| Strategy | RPO | RTO | Risk |
|---|---|---|---|
| KMS replication (Vault replication, AWS KMS multi-region) | Near-zero | Minutes | Network partition during failover |
| LUKS header backup on encrypted USB in safe | Point of last backup | Hours (physical retrieval) | USB degradation, physical loss |
| Shamir shares distributed geographically | Point of ceremony | Hours-days (coordinate holders) | Insufficient holders available |
| HSM backup to secondary HSM | Near-zero (paired HSMs) | Minutes | Cost of duplicate HSM |
| Paper key (QR code or hex) in safe | Point of printing | Hours | Paper degradation, transcription errors |

**Geographic distribution:** At minimum, keys should exist in two physically separate locations, at least 100 km apart, in facilities with independent power, network, and physical security. The LUKS header backup, the ZFS keyfile copy, and the Vault unseal shares should never all reside in the same building.

**Testing key recovery:** Key recovery procedures must be tested at least annually. A ceremony to reconstruct the master key from Shamir shares, unseal Vault from backup shares, and decrypt a test volume validates that the recovery chain is functional.

---

## 5. Self-Encrypting Drives

### 5.1 SED Architecture — OPAL 2.0 and TCG Enterprise

Self-Encrypting Drives (SEDs) implement encryption in the drive controller's hardware. Every write is encrypted with AES-256 before reaching the storage media (NAND flash for SSD, platters for HDD). Every read is decrypted transparently. The encryption is always on — even without a user-set password, data is encrypted with a default key.

**TCG OPAL 2.0:** Designed for client/consumer and enterprise workstations. Features:

- Multiple locking ranges (different areas of the disk can have different keys/credentials)
- Pre-Boot Authentication (PBA) — a shadow MBR presents a minimal OS for password entry before the real OS boots
- Admin SP (Security Provider) and Locking SP manage credentials and locking state
- Band-based encryption: each band has its own Media Encryption Key (MEK)

**TCG Enterprise:** Designed for servers and data centers. Differences from OPAL:

- No PBA (server environments use BMC/IPMI for pre-boot interaction)
- Key management delegated to an external KMS via KMIP
- Simpler protocol optimized for high-density deployments (100s of drives per rack)

### 5.2 SED Management — sedutil and msed

```bash
# Install sedutil (open-source OPAL management)
# https://github.com/Drive-Trust-Alliance/sedutil

# Query drive capabilities
sedutil-cli --scan
# Scanning for Opal compliant disks
# /dev/sda   2  Samsung SSD 860 EVO       RVT02B6Q  Opal 2.0

# Take ownership (set SID password)
sedutil-cli --initialSetup MySecurePassword /dev/sda

# Enable locking
sedutil-cli --enableLockingRange 0 MySecurePassword /dev/sda

# Set up Pre-Boot Authentication (PBA)
sedutil-cli --loadPBAimage MySecurePassword /path/to/UEFI64-n.n.img /dev/sda
sedutil-cli --setMBRDone off MySecurePassword /dev/sda
sedutil-cli --setMBREnable on MySecurePassword /dev/sda

# Verify locking state
sedutil-cli --query /dev/sda
```

### 5.3 Pre-Boot Authentication

The SED's shadow MBR contains a minimal boot environment (typically a Linux kernel + initramfs or a UEFI application) that prompts for the drive password. Upon correct authentication, the drive unlocks, the shadow MBR is bypassed, and the real OS boots from the now-decrypted drive.

In virtualized environments, SEDs are used on the hypervisor's physical drives. VMs do not interact with SED authentication — they see normal block devices. The hypervisor host must handle PBA during physical boot.

### 5.4 SED Limitations

**Wear leveling on SSD:** SSDs internally remap logical blocks to physical NAND pages for wear leveling. When a logical block is overwritten, the old physical page may not be immediately erased (it becomes a "stale page" in the spare area). With software encryption, this is a non-issue because only ciphertext was ever written to the media. With SED, the concern is that the SED controller might have a bug that writes plaintext to stale pages — this requires trusting the controller firmware completely.

**Controller trust:** The SED's encryption implementation is a black box. The encryption algorithm, key generation, key storage, and IV handling are all inside the controller's firmware. You cannot audit it, and you cannot verify its correctness independently (unlike dm-crypt, which is open-source and kernel-auditable).

### 5.5 SED vs Software Encryption Comparison

| Criterion | SED (OPAL 2.0) | Software (LUKS2/dm-crypt) |
|---|---|---|
| Performance overhead | Zero (dedicated hardware) | 1-5% with AES-NI |
| Key visibility to host | Key never in host RAM | Key in kernel memory while volume is open |
| Auditability | Closed firmware | Open-source, kernel-auditable |
| Key management integration | KMIP (TCG Enterprise), manual (OPAL) | Clevis, TPM, Vault, systemd-cryptsetup |
| Cold boot resistance | Yes (key in drive controller, not RAM) | No (key in RAM) |
| Proven vulnerabilities | Radboud (CVE-2018-12037/12038) | None equivalent in dm-crypt |
| Instant secure erase | Yes (destroy MEK) | Yes (destroy LUKS header/keyslots) |
| Multi-OS support | Transparent to OS | Requires OS-specific driver (dm-crypt, BitLocker) |

### 5.6 Firmware Attacks on SED — Radboud University Research

In November 2018, researchers Carlo Meijer and Bernard van Gastel at Radboud University Nijmegen published "Self-encrypting deception: weaknesses in the encryption of solid state drives" (IEEE S&P 2019). Their findings:

**CVE-2018-12037 (Crucial MX100/MX200/MX300):**
- The DEK (Data Encryption Key) was protected by a key derived from the user password, but in some firmware versions, the DEK was also accessible without the password through a manufacturer backdoor.
- The AES-256 implementation used an empty key in some configurations (the password was not actually used to derive the encryption key).

**CVE-2018-12038 (Samsung 840 EVO, 850 EVO, T3 Portable, T5 Portable):**
- The wear-leveling area contained unencrypted copies of the DEK in some firmware revisions.
- The password verification and the key derivation were separate processes — an attacker could bypass password verification while still obtaining the correct DEK.

**Impact on BitLocker:** By default (until Microsoft advisory ADV180028 in November 2018), BitLocker on Windows would defer encryption to the SED's hardware if an OPAL-capable drive was detected (called "hardware-based encryption" mode). This meant BitLocker provided no protection on affected Crucial and Samsung drives — the data was effectively unencrypted despite BitLocker reporting "encrypted."

**Post-ADV180028 remediation:** Microsoft changed BitLocker's default to software-based encryption (`EncryptionMethodWithXtsFull` = AES-256-XTS in software) unless an administrator explicitly configures Group Policy to trust hardware encryption after verifying the specific drive firmware.

**Lesson for ethical hackers:** When assessing encrypted storage, always verify whether the encryption is software-based or SED-based. If SED-based, check the drive model and firmware version against the Radboud CVE list. For Samsung 840/850 EVO drives, firmware update alone does not re-encrypt data that was already "encrypted" with the vulnerable firmware — the drive must be securely erased and data restored from backup.

### 5.7 Instant Secure Erase — Cryptographic Erase

SEDs support instant secure erase (ISE) by destroying the MEK (Media Encryption Key). Since all data on the media is encrypted with the MEK, destroying it renders all data unrecoverable in milliseconds regardless of drive capacity.

```bash
# Cryptographic erase via sedutil (destroys all data!)
sedutil-cli --revertTPer MySecurePassword /dev/sda
# This resets the drive to factory state — new MEK generated,
# old data irrecoverable

# For TCG Enterprise drives managed via KMIP:
# The KMS can issue a key destruction command, and the drive
# generates a new MEK internally
```

This is the preferred data destruction method for SEDs in decommissioning scenarios — it is fast (< 1 second), complete, and does not require physical destruction.

---

## 6. Encryption for Backup and Replication

### 6.1 Proxmox Backup Server Encryption

PBS implements client-side encryption using AES-256-GCM. The encryption key is generated on the PBS client (the Proxmox VE host), and the PBS server never sees the plaintext data or the encryption key. This is a zero-knowledge architecture — a compromised PBS server cannot decrypt backup data.

**Key management:**

```bash
# Generate an encryption key
proxmox-backup-client key create /etc/pve/priv/pbs-encryption-key.json
# Generates a random 256-bit key, stored in JSON format

# Optionally encrypt the key with an RSA master key for escrow
proxmox-backup-client key create-master-key
# Generates an RSA-4096 key pair:
#   master-public.pem  (used to encrypt backup keys for escrow)
#   master-private.pem (stored securely offline — this is the recovery key)

# Show key fingerprint
proxmox-backup-client key show /etc/pve/priv/pbs-encryption-key.json
```

**Encrypted backup execution:**

```bash
# Backup a VM with encryption
proxmox-backup-client backup \
  vm/100:/path/to/vm-100-disk.raw \
  --keyfile /etc/pve/priv/pbs-encryption-key.json \
  --repository pbs-server:store1

# Backup with master key escrow (the encryption key is also encrypted
# with the RSA master public key and stored alongside the backup)
proxmox-backup-client backup \
  vm/100:/path/to/vm-100-disk.raw \
  --keyfile /etc/pve/priv/pbs-encryption-key.json \
  --master-pubkey-file /etc/pve/priv/master-public.pem \
  --repository pbs-server:store1
```

**Key recovery from master key:**

If the original encryption key is lost but the RSA master private key is available, the encryption key can be recovered from the backup's metadata:

```bash
proxmox-backup-client key recover-key \
  --master-keyfile master-private.pem \
  --repository pbs-server:store1 \
  --backup-id vm/100
```

### 6.2 Veeam Encryption

Veeam Backup & Replication provides encryption at multiple levels:

**Job-level encryption:** Each backup job can be configured to encrypt backup data with AES-256. The user provides a password, and Veeam derives the encryption key using PBKDF2 with SHA-256 (64,000 iterations). The encrypted backup files (`.vbk`, `.vib`, `.vrb`) contain the encrypted data and an encrypted copy of the DEK wrapped with the password-derived key.

**File-level encryption:** Individual files within a backup can be encrypted when using Veeam Agent for file-level backups. This uses the same AES-256 + PBKDF2 scheme.

**Key management:** Veeam Enterprise Manager provides centralized password/key management. It stores a database of encryption passwords (encrypted with the Enterprise Manager's certificate). If a backup password is lost, Enterprise Manager can recover it — this is a convenience feature that introduces a centralized point of compromise. In high-security environments, disable Enterprise Manager password recovery and manage keys externally.

**Enterprise key hierarchy:**

```
Enterprise Manager Certificate
    |
    wraps
    v
Backup Job Password (PBKDF2 derived)
    |
    wraps
    v
Session Key (random per backup session)
    |
    encrypts
    v
Backup Data (AES-256)
```

### 6.3 Replication Encryption — Encrypted Channels and Storage at DR

Replication between sites must be encrypted both in transit and at rest at the DR site.

**In-transit encryption for replication:**

```bash
# WireGuard tunnel between primary and DR site
# Primary site: 10.0.0.1, DR site: 10.0.1.1
# WireGuard endpoint: wg0

# /etc/wireguard/wg0.conf on primary
[Interface]
PrivateKey = <primary-private-key>
Address = 172.16.0.1/30
ListenPort = 51820

[Peer]
PublicKey = <dr-public-key>
AllowedIPs = 172.16.0.2/32, 10.0.1.0/24
Endpoint = dr-site-public-ip:51820
PersistentKeepalive = 25

# All PBS/ZFS replication traffic routed through WireGuard
# PBS replication: proxmox-backup-client uses HTTPS (port 8007)
# already encrypted by TLS, but WireGuard adds a second layer
# and isolates the traffic from the public internet
```

**At-rest encryption at DR site:** The DR site's storage must be encrypted independently of the primary site. If the primary site's keys are compromised, the DR site remains protected by its own key set.

### 6.4 Tape Encryption — LTO Hardware Encryption

LTO (Linear Tape-Open) generations 4 and later support hardware AES-256-GCM encryption in the tape drive. The drive encrypts data before writing to the tape media.

**Key management for tape:**

- Keys are provided to the tape drive by the backup application (Veeam, Bacula, Amanda) or by a tape library's encryption-capable firmware.
- KMIP integration allows the tape library to fetch keys from a central KMS.
- Each tape typically uses a unique DEK, and the KEK is in the KMS.
- Tape key management is critical for long-term retention: a tape encrypted in 2024 may need to be read in 2034. The KEK (and the KMS that manages it) must remain available for the entire retention period.

**Tape-specific risk:** If a tape is lost or stolen, its data is protected only if the encryption key is not compromised. Unlike disk encryption where the key is in a known KMS, tape keys can become orphaned if the KMS is decommissioned. Maintain a key inventory that maps each tape barcode to its key ID in the KMS.

### 6.5 Cloud Backup Encryption

**Client-side encryption before upload (recommended):**

Encrypt data before it leaves the premises. The cloud provider (AWS S3, Azure Blob, GCP Cloud Storage) receives only ciphertext. This provides protection against:

- Cloud provider access (insider threat at the provider)
- Legal/regulatory access (government demands to the provider)
- Cloud storage breach

```bash
# Example: encrypt a backup file before S3 upload
# Using age (modern, simple encryption tool)
age -r age1recipient... backup-2026-05-07.tar.zst > backup-2026-05-07.tar.zst.age
aws s3 cp backup-2026-05-07.tar.zst.age s3://dr-backups/

# Or with GPG
gpg --symmetric --cipher-algo AES256 backup-2026-05-07.tar.zst
aws s3 cp backup-2026-05-07.tar.zst.gpg s3://dr-backups/
```

**Server-side encryption (SSE):**

- **SSE-S3:** AWS manages keys entirely. Simplest, least control. AWS rotates keys automatically.
- **SSE-KMS:** AWS KMS manages keys. You control key policies, rotation, and audit via CloudTrail. Keys are regional and do not leave AWS.
- **SSE-C (Customer-Provided Keys):** You provide the encryption key with each PUT/GET request. AWS uses it for the operation but does not store it. You are fully responsible for key management.

For compliance-sensitive workloads, client-side encryption + SSE-KMS provides defence in depth: even if SSE-KMS is somehow bypassed (e.g., AWS internal compromise), the client-side encryption layer remains.

---

## 7. Encryption Attacks and Weaknesses

### 7.1 Cold Boot Attack — DRAM Remanence

**The attack (Halderman et al., "Lest We Remember: Cold Boot Attacks on Encryption Keys," USENIX Security 2008):**

DRAM retains its contents for seconds to minutes after power is removed, depending on temperature. At room temperature (20-25 C), most DRAM loses data within 2-5 seconds. At -50 C (achievable with a can of compressed air held upside down), data persists for 10+ minutes. At liquid nitrogen temperatures (-196 C), data persists indefinitely.

**Attack procedure:**

1. Attacker gains physical access to a running machine with encrypted disks (keys are in RAM).
2. Attacker sprays DRAM modules with compressed air to cool them.
3. Attacker either: (a) performs a hard reset and boots a minimal OS from USB that dumps memory; or (b) physically removes the DRAM modules and inserts them in another machine for imaging.
4. Attacker scans the memory dump for AES key schedules using `aeskeyfind` or `findaes`:

```bash
# Using aeskeyfind (from Princeton's cold boot attack toolkit)
aeskeyfind memory.dump
# Output: potential AES-128 keys and AES-256 keys found
# Each found key can be tested against the encrypted volume

# Using findaes (alternative tool)
findaes memory.dump
```

5. The recovered AES key is the LUKS volume key (DEK). With it, the attacker can decrypt the volume directly, bypassing all passphrases and keyslots:

```bash
# Decrypt using recovered volume key (bypasses LUKS entirely)
dmsetup create decrypted-volume --table "0 $(blockdev --getsz /dev/sda3) crypt aes-xts-plain64 <recovered-hex-key> 0 /dev/sda3 0"
```

**Countermeasures:**

| Countermeasure | Effectiveness | Limitation |
|---|---|---|
| TRESOR (kernel patch — keys in CPU debug registers) | High — keys never in RAM | Performance penalty; limited to 1-2 key slots; not mainlined |
| SED instead of software encryption | High — key in drive controller | SED firmware vulnerabilities (see 5.6) |
| TPM + measured boot | Medium — detects tampered boot | Does not protect against memory imaging |
| DDR5 memory encryption (Intel TME / AMD SME) | High — RAM contents encrypted by CPU | Requires modern platform; key still in CPU |
| Physical security (locked cages, intrusion detection) | High — prevents physical access | Does not help if attacker has insider access |
| Fast RAM overwrite on shutdown/panic | Medium — reduces window | Attackable during normal operation |

**DDR4/DDR5 and modern mitigations:** Modern DDR4 and DDR5 modules have shorter remanence windows (sub-second at room temperature) due to smaller cell capacitance, but the attack remains viable with cooling. Intel TME (Total Memory Encryption) and AMD SME/SEV encrypt memory contents with a CPU-internal key, making cold boot dumps yield only ciphertext.

### 7.2 Evil Maid Attack — Bootloader Tampering

**The attack:** An "evil maid" (someone with brief unsupervised physical access to a powered-off or suspended machine) modifies the bootloader or early boot components to capture the encryption passphrase.

**Attack variants:**

1. **Bootloader replacement:** Replace GRUB/systemd-boot with a modified version that logs the passphrase before passing it to `cryptsetup`. The user sees a normal-looking password prompt, types the passphrase, and the modified bootloader records it (to a hidden disk sector, USB, or network exfiltration) before continuing the normal boot.

2. **Hardware keylogger:** Insert a USB or PS/2 hardware keylogger between the keyboard and the machine. Captures the passphrase on next boot.

3. **Firmware rootkit:** Flash modified UEFI firmware that intercepts the encryption key before the OS boots. Persistent across OS reinstalls.

**Countermeasures:**

| Countermeasure | Protection |
|---|---|
| UEFI Secure Boot + measured boot (TPM PCRs) | Modified bootloader changes PCR values, TPM refuses to unseal the LUKS key (Clevis/TPM binding breaks) |
| Physical tamper-evident seals on chassis | Detects physical intrusion (but can be replicated by sophisticated attacker) |
| Remote attestation | TPM-based attestation reports boot state to a remote verifier before unlock |
| Full disk encryption including /boot | Requires an intermediate decryption step (GRUB with LUKS support) |
| UEFI firmware password + chassis lock | Prevents unauthorized firmware modification |

### 7.3 Key Extraction from Memory

Even without a cold boot attack, an attacker with root access to a running system can extract encryption keys from kernel memory:

```bash
# Using Volatility framework on a memory dump
vol.py -f memory.dump linux.aeskeyfind
# Or using the linux.pslist + linux.proc_maps plugins to locate
# cryptsetup/dm-crypt kernel structures

# Direct memory read (requires root)
dd if=/dev/mem bs=1M count=4096 of=memdump.raw 2>/dev/null
findaes memdump.raw

# On Linux 5.4+, /dev/mem is restricted by default
# (CONFIG_STRICT_DEVMEM=y). Attackers may use /proc/kcore instead:
dd if=/proc/kcore bs=1M count=4096 of=kcore.raw 2>/dev/null
findaes kcore.raw
```

**Mitigations:** `CONFIG_STRICT_DEVMEM=y` (default on most distributions) prevents userspace from reading arbitrary physical memory. `CONFIG_LOCKDOWN_LSM=y` (enabled with Secure Boot on modern kernels) further restricts `/dev/mem` and `/proc/kcore` access. `lockdown=confidentiality` kernel parameter provides the strongest protection.

### 7.4 DMA Attacks — FireWire, Thunderbolt, PCIe

**The attack:** DMA (Direct Memory Access) -capable interfaces allow external devices to read and write host memory directly, bypassing the CPU. An attacker connects a malicious device to a FireWire, Thunderbolt, or ExpressCard/PCIe slot and reads memory contents (including encryption keys).

**Tools:**

- **PCILeech:** Open-source DMA attack framework. Supports FPGA-based hardware (Screamer M.2, AC701) that connects via PCIe/M.2 and provides full DMA access.
- **Inception:** Tool for DMA-based password bypass against locked screens (reads/patches memory via FireWire/Thunderbolt).
- **Thunderclap (NDSS 2019):** Research demonstrating that Thunderbolt peripherals (even legitimate-looking ones) can perform arbitrary DMA on many systems.

**Countermeasures:**

| Countermeasure | Configuration |
|---|---|
| IOMMU (VT-d / AMD-Vi) | Enable in BIOS; set `intel_iommu=on iommu=pt` in kernel cmdline |
| Thunderbolt security level | Set to "user" or "secure" (requires user approval for new devices) |
| Disable unused DMA ports | Disable FireWire, ExpressCard in BIOS; `blacklist firewire-ohci` in modprobe |
| Kernel DMA protection | `CONFIG_DMA_RESTRICT_POOL=y`; Windows Kernel DMA Protection (available since 1803) |

```bash
# Verify IOMMU is active
dmesg | grep -i iommu
# [ 0.123456] DMAR: IOMMU enabled

# Verify kernel DMA protection
cat /sys/bus/thunderbolt/devices/*/security
# Should show "user" or "secure", not "none"
```

### 7.5 Rubber-Hose Cryptanalysis

The term "rubber-hose cryptanalysis" (attributed to the cypherpunk community, popularized by XKCD #538) refers to extracting encryption keys through coercion — physical force, legal compulsion, or threats against the key holder.

**Technical countermeasures:**

- **Plausible deniability (hidden volumes):** VeraCrypt supports hidden volumes where a second encrypted volume is concealed within the free space of an outer volume. Under coercion, the user reveals the outer volume's password, which appears to decrypt the drive and shows innocuous data. The hidden volume is cryptographically indistinguishable from free space. LUKS does not natively support hidden volumes.
- **Duress passwords (kill switches):** Some FDE implementations support a "duress password" that, when entered, destroys the real encryption keys while appearing to unlock the system. This is a niche feature not present in mainstream LUKS/BitLocker.
- **Jurisdictional considerations:** In some jurisdictions (UK under RIPA Part III, Australia under Assistance and Access Act 2018), failure to provide an encryption key when compelled by legal order is a criminal offense. In other jurisdictions (US under Fifth Amendment protections, with evolving case law), forced decryption may be restricted.

From a technical standpoint, the best defence against compelled disclosure is architectural: if the key holder genuinely cannot decrypt the data (because the key is split via Shamir's scheme and no single person has enough shares), then coercion of one individual is insufficient.

### 7.6 Implementation Vulnerabilities

**Padding oracle attacks:** Relevant to CBC-mode encryption (used in older TLS versions, some legacy storage). A padding oracle exists when the system reveals whether decrypted ciphertext has valid padding. The attacker submits modified ciphertext and observes the error response. Over thousands of queries, the entire plaintext can be recovered without the key. XTS mode (used in disk encryption) is not vulnerable to padding oracles because it does not use padding.

**IV reuse in AES-GCM:** If the same IV (nonce) is used twice with the same key in GCM, the authentication key (GHASH key H) can be recovered. This allows an attacker to forge authenticated ciphertexts. In storage contexts, IV reuse can happen if a backup system reuses a counter after restart without persisting the counter state.

**Weak KDF parameters:** LUKS2 volumes formatted with insufficient Argon2id memory cost (e.g., `-m 64000` instead of `-m 1048576`) are vulnerable to GPU-based brute force. Always verify KDF parameters after formatting:

```bash
cryptsetup luksDump /dev/sda3 | grep -A 5 "PBKDF:"
# Memory should be >= 1048576 (1 GiB)
```

### 7.7 Side-Channel Attacks on Encryption

**Timing attacks:** If the encryption implementation's execution time varies based on the key or plaintext, an attacker measuring execution time over many operations can recover the key. AES-NI hardware instructions are constant-time, making them inherently resistant. Software AES implementations using lookup tables (T-tables) are vulnerable to cache-timing attacks (Bernstein 2005, Osvik-Shamir-Tromer 2006).

**Power analysis (SPA/DPA):** Relevant to embedded/IoT devices and smart cards. The power consumption of a device during encryption correlates with the key bits being processed. In virtualized environments, power analysis is generally not a practical attack vector unless the attacker has physical access to the host and can measure power at the CPU level.

**Electromagnetic emanation (TEMPEST):** Cryptographic operations produce electromagnetic emissions that correlate with key material. This is an intelligence-agency-level attack (NSA TEMPEST program). In data center environments, EM shielding (Faraday cages) is the countermeasure, but it is rarely deployed outside classified facilities.

**VM-level side channels:** In a shared-tenancy environment (public cloud), a malicious VM on the same physical host can observe cache access patterns (Flush+Reload, Prime+Probe) of a co-resident VM performing encryption. This is mitigated by: (1) AES-NI (no table lookups to observe), (2) cache partitioning (Intel CAT), (3) not co-locating sensitive workloads with untrusted tenants.

---

## 8. Secure Data Destruction

### 8.1 Cryptographic Erasure

Cryptographic erasure renders data unrecoverable by destroying the encryption key rather than the ciphertext. The ciphertext remains on the media, but without the key, it is computationally infeasible to decrypt (assuming AES-256 with no implementation flaws).

```bash
# LUKS: destroy all keyslots (irreversible!)
cryptsetup erase /dev/sda3
# This overwrites all keyslot areas with zeros.
# The encrypted data remains on disk but is irrecoverable.

# ZFS: unload key and destroy keyfile
zfs unload-key encrypted-pool/dataset
shred -vfz -n 3 /root/.zfs-keys/dataset.key
# Without the key, the dataset's data is irrecoverable.
# The dataset still exists but cannot be mounted or read.

# Vault: destroy the transit key
vault delete transit/keys/proxmox-vm-keys
# All data encrypted with this key is now irrecoverable
```

**Advantages over physical destruction:** Cryptographic erasure is instant (milliseconds), does not require physical destruction of expensive hardware (the drive can be reused), and can be performed remotely. It is the recommended method for decommissioning individual datasets or VMs while keeping the underlying storage hardware in service.

### 8.2 ATA Secure Erase

ATA Secure Erase is a firmware-level command defined in the ATA specification that instructs the drive to overwrite all user-accessible and hidden areas (including reallocated sectors, HPA, and DCO).

```bash
# Check if the drive supports Secure Erase
hdparm -I /dev/sda | grep -i erase
# Security:
#   supported: enhanced erase
#   estimated time for: security erase: 240min
#                       enhanced security erase: 480min

# Set a temporary password (required before issuing erase)
hdparm --user-master u --security-set-pass Erase1234 /dev/sda

# Standard erase (writes zeros to all sectors)
hdparm --user-master u --security-erase Erase1234 /dev/sda

# Enhanced erase (vendor-specific — may use pattern writes or crypto-erase)
hdparm --user-master u --security-erase-enhanced Erase1234 /dev/sda
```

**Standard vs enhanced:** Standard Secure Erase writes a single pattern to all sectors. Enhanced Secure Erase is vendor-defined and on SEDs typically performs a cryptographic erase (new MEK generated). Enhanced erase is faster on SEDs because it only regenerates the key rather than overwriting all media.

### 8.3 NVMe Format — User Data Erase and Cryptographic Erase

NVMe drives use the `nvme format` command instead of ATA Secure Erase:

```bash
# Install nvme-cli
apt install nvme-cli

# Check supported sanitize/format operations
nvme id-ctrl /dev/nvme0 -H | grep -i "Format NVM"

# User Data Erase (SES=1: writes zeros or ones to all user data)
nvme format /dev/nvme0 --ses=1

# Cryptographic Erase (SES=2: destroys encryption key)
nvme format /dev/nvme0 --ses=2
# This is equivalent to SED cryptographic erase — instant and complete

# NVMe Sanitize (more thorough than format, includes hidden areas)
nvme sanitize /dev/nvme0 --sanact=4
# sanact=4 = Crypto Erase via sanitize command
# sanact=2 = Block Erase (overwrite all blocks)
# sanact=3 = Overwrite (pattern write, configurable passes)
```

**NVMe Sanitize vs Format:** The Sanitize command (introduced in NVMe 1.3) is more comprehensive than Format. Sanitize processes all user data areas, all internal copies (wear-leveled pages, over-provisioning space), and reports completion status. Format only handles the logical namespace.

### 8.4 Overwrite Methods — NIST SP 800-88 Rev.1

NIST SP 800-88 Rev.1 "Guidelines for Media Sanitization" (December 2014) defines three categories:

| Category | Method | Verification | Media types |
|---|---|---|---|
| **Clear** | Overwrite with a single pass of zeros or ones | Read back and verify | HDD, SSD (with caveats), tape |
| **Purge** | ATA Secure Erase (enhanced), NVMe Sanitize, cryptographic erase, degaussing (HDD) | Vendor certification or sampling verification | HDD, SSD, tape |
| **Destroy** | Physical destruction (shredding, incineration, disintegration, melting) | Certificate of destruction | All media types |

**The retirement of DoD 5220.22-M:** The once-popular DoD 3-pass overwrite standard (DoD 5220.22-M) was removed from DSS guidelines in 2007. NIST SP 800-88 Rev.1 supersedes it. For modern media (SSD, NVMe), a single-pass overwrite (Clear) or cryptographic erase (Purge) is sufficient — multiple overwrite passes provide no additional security benefit on flash media due to the way NAND flash cells store data.

### 8.5 Physical Destruction

When cryptographic or logical erasure is insufficient (e.g., for classified data, or when media is damaged and cannot accept erase commands):

| Method | Media | Standard |
|---|---|---|
| **Degaussing** | HDD (magnetic), tape | NSA/CSS EPL; ineffective on SSD |
| **Shredding** | All (particle size < 2mm for classified) | NIST Purge/Destroy; NSA/CSS PM 9-12 |
| **Incineration** | All | Local environmental regulations apply |
| **Disintegration** | All | NSA-evaluated disintegrators reduce to < 2mm particles |
| **Chemical dissolution** | Flash/NAND | Dissolves NAND dies; used in some military contexts |

**SSD-specific note:** Degaussing does not work on SSDs — flash memory is not magnetic. SSDs must be shredded, incinerated, or cryptographically erased.

### 8.6 Cloud Data Destruction — Challenges and Verification

Destroying data in cloud environments presents unique challenges:

- **No physical access:** You cannot degauss or shred cloud storage. You must rely on the provider's deletion mechanisms plus your own cryptographic erasure.
- **Replication and caching:** Cloud storage typically replicates data across multiple physical locations and caches it at multiple layers (CDN, edge, regional replicas). Deleting an object from S3 does not immediately erase all replicas — they are garbage-collected asynchronously.
- **Backups and snapshots:** The cloud provider's internal backup systems may retain copies of your data beyond your deletion request.

**Verification approach:**

1. Client-side encrypt all data before upload (you control the key).
2. To destroy data, destroy the client-side encryption key.
3. Also delete the cloud objects/buckets.
4. Request a data deletion certificate from the provider if available.
5. For compliance, document the key destruction with timestamp and operator identity.

### 8.7 Compliance Requirements for Data Destruction

| Framework | Requirement |
|---|---|
| PCI-DSS 4.0 (Req. 9.4) | Media containing cardholder data must be rendered unrecoverable. Quarterly process review. |
| HIPAA (164.310(d)(2)(i)) | ePHI media must be cleared, purged, or destroyed before reuse or disposal. Policies must be documented. |
| GDPR (Art. 17) | Right to erasure ("right to be forgotten"). Data must be erased "without undue delay." Destruction must be verifiable. |
| SOX (Section 802) | Financial records must be retained for prescribed periods. Destruction before retention expiry is prohibited. |
| FedRAMP (via NIST 800-88) | Media sanitization per NIST SP 800-88 Rev.1. Sanitization records retained for system lifetime. |

---

## 9. Compliance and Audit

### 9.1 Encryption Requirements per Framework

**PCI-DSS 4.0:**
- Requirement 3.5: Render PAN (Primary Account Number) unreadable anywhere it is stored. Acceptable methods: strong one-way hash, truncation, index tokens with securely stored pads, or strong cryptography with associated key-management processes.
- Requirement 3.6: Cryptographic keys used to protect stored cardholder data must be protected against disclosure and misuse. Key custodians must formally acknowledge their responsibilities.
- Requirement 3.7: Key management procedures documented: generation, distribution, storage, rotation, retirement, destruction.
- Requirement 4.2: PAN transmitted over open networks must be encrypted with strong cryptography (TLS 1.2+).

**HIPAA (Security Rule):**
- 164.312(a)(2)(iv): Encryption of ePHI is an addressable implementation specification. "Addressable" does not mean optional — it means the organization must implement it or document why an equivalent alternative is used.
- 164.312(e)(2)(ii): Encryption of ePHI in transit is addressable. In practice, OCR (Office for Civil Rights) has interpreted encryption as effectively mandatory for any organization without a compelling documented reason.
- Safe harbor: under the Breach Notification Rule (164.402), if breached ePHI was encrypted per NIST guidelines, the breach is not reportable. This makes encryption a de facto compliance requirement.

**GDPR:**
- Article 32: "Appropriate technical and organisational measures to ensure a level of security appropriate to the risk, including pseudonymisation and encryption of personal data."
- Article 34(3)(a): If breached data was encrypted and the key was not compromised, notification to affected individuals is not required.
- Encryption is not explicitly mandated, but practically required to avoid notification obligations and to demonstrate "appropriate measures."

**SOX (Sarbanes-Oxley):**
- Section 302/404: Internal controls over financial reporting must protect data integrity. Encryption of financial databases, backup data, and data in transit is an expected control.
- No specific encryption algorithm or key length is mandated — the standard is "effective internal controls."

**FedRAMP:**
- Encryption requirements follow NIST SP 800-53 SC-28 (Protection of Information at Rest) and SC-8 (Transmission Confidentiality and Integrity).
- FIPS 140-2 (or 140-3) validated cryptographic modules are required for all cryptographic operations in FedRAMP-authorized systems.
- AES-256 is required for data at rest. TLS 1.2+ with approved cipher suites for data in transit.
- Key management must comply with NIST SP 800-57.

### 9.2 Key Management Audit

Auditors verify key management by requesting evidence in several categories:

**Key access logs:** Every access to a KEK or DEK must be logged with timestamp, operator identity, operation type (create, read, rotate, destroy), and source IP. In Vault, this is the audit log:

```bash
# Enable Vault audit logging
vault audit enable file file_path=/var/log/vault/audit.log

# Audit log entries include:
# - Timestamp (UTC)
# - Request/response details
# - Token accessor (who)
# - Operation path (e.g., transit/encrypt/proxmox-vm-keys)
# - Client IP address
```

**Rotation compliance:** Auditors verify that keys are rotated per policy. Evidence includes:

```bash
# Vault: show key version history (proves rotation occurred)
vault read transit/keys/proxmox-vm-keys
# Key: proxmox-vm-keys
# Type: aes256-gcm96
# Latest version: 4
# Versions:
#   1: created 2025-08-15T10:00:00Z
#   2: created 2025-11-15T10:00:00Z
#   3: created 2026-02-15T10:00:00Z
#   4: created 2026-05-07T10:00:00Z
```

**Separation of duties:** No single administrator should have the ability to both access encryption keys and access encrypted data. This is enforced via:

- Vault policies that restrict key access to specific roles
- LUKS keyslot management restricted to a dedicated security team
- KMS administrators separate from system administrators
- Shamir share holders are from different departments

### 9.3 Encryption Verification — Proving Encryption Is Effective

Auditors require evidence that encryption is actually protecting data, not just configured:

**Evidence collection for audit:**

```bash
# 1. Prove LUKS volume is encrypted (examine raw device)
xxd /dev/sda3 | head -20
# Should show LUKS header magic (LUKS\xba\xbe for LUKS1, SKUL for LUKS2)
# followed by random-looking data (ciphertext)

# 2. Prove dm-crypt is active
dmsetup table --showkeys
# WARNING: --showkeys exposes the volume key in hex. Use only for audit.
# In production, use: dmsetup table (without --showkeys)
# Shows: 0 <size> crypt aes-xts-plain64 :64:logon:cryptsetup:<uuid>... 0 /dev/sda3 0

# 3. Prove ZFS encryption is active
zfs get encryption,keystatus encrypted-pool/vm-disks
# encryption = aes-256-gcm, keystatus = available

# 4. Prove PBS backup is encrypted
proxmox-backup-client catalog dump --repository pbs-server:store1
# Encrypted backups show "(encrypted)" in the catalog listing

# 5. Attempt to read ciphertext directly (negative test)
# If you can mount a volume without providing a key, encryption is not effective
cryptsetup status vm-100-disk-0-crypt
# Shows cipher, keysize, device, offset — confirms active encryption
```

### 9.4 Data Classification for Encryption

Not all data requires the same level of encryption. A data classification framework guides encryption decisions:

| Classification | Examples | Encryption requirement | Key management |
|---|---|---|---|
| **Restricted/Secret** | PCI cardholder data, ePHI, PII, encryption keys | Mandatory at rest and in transit | HSM-backed, Shamir split, annual rotation |
| **Confidential** | Financial reports, source code, internal credentials | Mandatory at rest and in transit | KMS-managed, automated rotation |
| **Internal** | Internal documentation, non-sensitive configs | Recommended at rest, mandatory in transit | Standard key management |
| **Public** | Marketing materials, public APIs, open-source | Not required | N/A |

### 9.5 Data Residency and Encryption — Cross-Border Considerations

Encryption interacts with data residency requirements in several ways:

- **GDPR data transfers (Chapter V):** Transferring personal data outside the EU/EEA requires adequate safeguards. Encryption with EU-managed keys is one safeguard (Schrems II implications: if the key is accessible to non-EU entities, the protection is undermined).
- **Data sovereignty laws:** Some jurisdictions (Russia, China, India) require data to be stored within national borders. Encrypting data and storing it abroad may not satisfy residency requirements — the data (even encrypted) is still physically located abroad.
- **Key residency:** Even if data is encrypted at rest in a foreign jurisdiction, if the encryption key is also in that jurisdiction (e.g., in a cloud KMS in the same region), a local government can potentially compel both data and key disclosure. Keeping keys in a separate jurisdiction from the encrypted data provides a legal (not just technical) barrier.

---

## 10. Lab: Implement Complete Encryption Stack

### 10.0 Lab Environment

| Component | Specification |
|---|---|
| Proxmox VE host | 2x physical nodes, PVE 8.x, TPM 2.0 module |
| Storage | 6x SSD per node (ZFS pool) |
| Vault server | Dedicated VM or container, Vault 1.17+ |
| PBS server | Dedicated host/VM, PBS 3.x |
| DR site | Second location with PVE node + PBS |
| Network | Isolated management VLAN, WireGuard tunnel to DR |
| Test VMs | Linux (Debian 12) and Windows Server 2022 guests |

### 10.1 Configure ZFS Encrypted Pool

```bash
# On each Proxmox node:

# Generate a 256-bit raw encryption key
mkdir -p /root/.zfs-keys
dd if=/dev/urandom bs=32 count=1 of=/root/.zfs-keys/tank.key 2>/dev/null
chmod 600 /root/.zfs-keys/tank.key

# Create encrypted ZFS pool (RAIDZ2 across 6 drives)
zpool create -f \
  -O encryption=aes-256-gcm \
  -O keylocation=file:///root/.zfs-keys/tank.key \
  -O keyformat=raw \
  -O compression=zstd \
  -O atime=off \
  -O recordsize=64K \
  -O xattr=sa \
  -O acltype=posixacl \
  tank raidz2 /dev/sd{a,b,c,d,e,f}

# Create encrypted datasets for VM storage
zfs create tank/vm-disks
zfs create tank/ct-volumes
zfs create tank/backups

# Verify encryption
zfs get encryption,keystatus,keyformat tank/vm-disks
# NAME             PROPERTY      VALUE         SOURCE
# tank/vm-disks    encryption    aes-256-gcm   -
# tank/vm-disks    keystatus     available     -
# tank/vm-disks    keyformat     raw           inherited from tank

# Add to Proxmox as storage
pvesm add zfspool tank-encrypted \
  --pool tank/vm-disks \
  --content images,rootdir \
  --sparse 1
```

### 10.2 Configure LUKS VM Disks with TPM Auto-Unlock

```bash
# Create a LUKS2-encrypted LV for a specific VM's sensitive data disk
lvcreate -n vm-200-secure -L 100G pve/data

# Format with LUKS2 (strong Argon2id parameters)
cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --pbkdf argon2id \
  --pbkdf-memory 1048576 \
  --pbkdf-parallel 4 \
  --label vm-200-secure-crypt \
  /dev/pve/vm-200-secure

# Open the volume
cryptsetup luksOpen /dev/pve/vm-200-secure vm-200-secure-crypt

# Bind to TPM2 for auto-unlock
apt install -y clevis clevis-luks clevis-tpm2 tpm2-tools clevis-initramfs

clevis luks bind -d /dev/pve/vm-200-secure tpm2 \
  '{"pcr_bank":"sha256","pcr_ids":"0,1,7"}'

# Verify binding
clevis luks list -d /dev/pve/vm-200-secure
# 1: tpm2 '{"hash":"sha256","key":"ecc","pcr_bank":"sha256","pcr_ids":"0,1,7"}'

# Rebuild initramfs for auto-unlock at boot
update-initramfs -u -k all

# Add to /etc/crypttab for systemd integration
echo "vm-200-secure-crypt /dev/pve/vm-200-secure none tpm2-device=auto" >> /etc/crypttab

# Point VM 200's secure disk to the decrypted device
# In /etc/pve/qemu-server/200.conf:
# scsi1: /dev/mapper/vm-200-secure-crypt,size=100G
```

### 10.3 Configure Vault KMS

```bash
# On Vault VM/container:

# Initialize Vault with Shamir secret sharing (5-of-8)
vault operator init \
  -key-shares=8 \
  -key-threshold=5

# Unseal (requires 5 of 8 key holders)
vault operator unseal  # Share 1
vault operator unseal  # Share 2
vault operator unseal  # Share 3
vault operator unseal  # Share 4
vault operator unseal  # Share 5

# Login
vault login <root-token>

# Enable Transit secrets engine
vault secrets enable transit

# Create encryption keys for different purposes
vault write -f transit/keys/pve-node1-zfs \
  type=aes256-gcm96 \
  auto_rotate_period=90d

vault write -f transit/keys/pve-node2-zfs \
  type=aes256-gcm96 \
  auto_rotate_period=90d

vault write -f transit/keys/backup-encryption \
  type=aes256-gcm96 \
  auto_rotate_period=180d

# Enable audit logging
vault audit enable file \
  file_path=/var/log/vault/audit.log

# Create a policy for Proxmox hosts
cat <<'POLICY' | vault policy write proxmox-encryption -
path "transit/encrypt/pve-*" {
  capabilities = ["update"]
}
path "transit/decrypt/pve-*" {
  capabilities = ["update"]
}
path "transit/keys/pve-*" {
  capabilities = ["read"]
}
POLICY

# Create AppRole for Proxmox hosts
vault auth enable approle
vault write auth/approle/role/proxmox-host \
  token_policies="proxmox-encryption" \
  token_ttl=1h \
  token_max_ttl=4h \
  secret_id_ttl=0 \
  secret_id_num_uses=0

# Get RoleID and SecretID for each Proxmox host
vault read auth/approle/role/proxmox-host/role-id
vault write -f auth/approle/role/proxmox-host/secret-id
```

### 10.4 Encrypted Backups to PBS

```bash
# On Proxmox host:

# Generate PBS encryption key
proxmox-backup-client key create \
  /etc/pve/priv/pbs-encryption-key.json

# Generate master key pair for escrow
proxmox-backup-client key create-master-key
# Produces: master-public.pem, master-private.pem

# Secure the master private key (store offline/in safe)
cp master-private.pem /secure-offsite/pbs-master-private.pem
shred -vfz master-private.pem  # Remove from online system

# Copy master public key to /etc/pve/priv/ for automated backups
cp master-public.pem /etc/pve/priv/pbs-master-public.pem

# Configure PBS datastore in Proxmox GUI or CLI
pvesm add pbs pbs-encrypted \
  --server pbs-server.internal \
  --datastore store1 \
  --username backup@pbs \
  --password <password> \
  --encryption-key /etc/pve/priv/pbs-encryption-key.json \
  --master-pubkey-file /etc/pve/priv/pbs-master-public.pem \
  --fingerprint <pbs-server-tls-fingerprint>

# Test encrypted backup
proxmox-backup-client backup \
  vm/100:tank/vm-disks/vm-100-disk-0 \
  --keyfile /etc/pve/priv/pbs-encryption-key.json \
  --master-pubkey-file /etc/pve/priv/pbs-master-public.pem \
  --repository pbs-server.internal:store1

# Verify backup is encrypted
proxmox-backup-client snapshot list \
  --repository pbs-server.internal:store1
# Shows encryption status per snapshot
```

### 10.5 Encrypted Replication to DR

```bash
# Set up WireGuard tunnel to DR site
apt install wireguard

# Generate keys on primary
wg genkey | tee /etc/wireguard/primary-private.key | wg pubkey > /etc/wireguard/primary-public.key

# /etc/wireguard/wg-dr.conf
cat <<'WG' > /etc/wireguard/wg-dr.conf
[Interface]
PrivateKey = $(cat /etc/wireguard/primary-private.key)
Address = 172.16.100.1/30
ListenPort = 51820

[Peer]
PublicKey = <dr-site-public-key>
AllowedIPs = 172.16.100.2/32, 10.1.0.0/24
Endpoint = dr-site.example.com:51820
PersistentKeepalive = 25
WG

systemctl enable --now wg-quick@wg-dr

# ZFS encrypted send/receive to DR site
# (ZFS sends raw encrypted blocks — DR site never sees plaintext)
zfs snapshot tank/vm-disks@repl-$(date +%Y%m%d)
zfs send -w tank/vm-disks@repl-$(date +%Y%m%d) | \
  ssh -o "ProxyCommand=nc -X connect -x 172.16.100.2:1080 %h %p" \
  root@dr-pve-host "zfs recv dr-tank/vm-disks"
# The -w flag sends the raw encrypted stream.
# DR site stores ciphertext — cannot decrypt without the ZFS key.

# PBS replication (encrypted backup data replicated to DR PBS)
# Configure on PBS server:
# Datastore -> Sync Jobs -> Add
# Remote: dr-pbs-server.internal:store1
# Schedule: daily at 02:00
# Encrypted data is replicated as-is (ciphertext)
```

### 10.6 Test: Cold Boot Attack Simulation

**WARNING:** This test must be performed on a dedicated lab machine, never on production. It involves reading kernel memory contents.

```bash
# On a test Proxmox host with an open LUKS volume:

# 1. Verify LUKS volume is open and key is in kernel memory
dmsetup table vm-200-secure-crypt
# Shows crypt target is active

# 2. Attempt memory dump (requires disabling kernel lockdown for test)
# This simulates what an attacker would do after a cold boot
# In production, CONFIG_STRICT_DEVMEM=y and lockdown=confidentiality
# prevent this — we temporarily disable for testing:

# Boot test kernel with: lockdown=none
# Then:
dd if=/dev/mem bs=1M count=4096 of=/tmp/memdump.raw 2>/dev/null

# 3. Search for AES key schedules
# Install aeskeyfind (build from source: https://citp.princeton.edu/our-work/memory/)
git clone https://github.com/makomk/aeskeyfind.git
cd aeskeyfind && make
./aeskeyfind /tmp/memdump.raw
# If keys are found, they can be used to decrypt the volume:
# dmsetup create test-decrypt --table "0 <size> crypt aes-xts-plain64 <found-key-hex> 0 /dev/pve/vm-200-secure 0"

# 4. Verify countermeasure: with lockdown=confidentiality
# Re-enable lockdown and repeat:
# dd if=/dev/mem bs=1M count=4096 of=/tmp/memdump2.raw
# Expected: "Operation not permitted"

# 5. Clean up
shred -vfz /tmp/memdump.raw
```

### 10.7 Test: DMA Attack Simulation

```bash
# Verify IOMMU is enabled (countermeasure)
dmesg | grep -i "IOMMU enabled\|DMAR"
# Expected: DMAR: IOMMU enabled
# or: AMD-Vi: AMD IOMMUv2 enabled

# Verify Thunderbolt security level
cat /sys/bus/thunderbolt/devices/*/security 2>/dev/null
# Expected: "user" or "secure"

# Verify kernel DMA protection
dmesg | grep -i "kernel DMA"
# Expected: Kernel DMA protection enabled

# If using PCILeech for authorized testing:
# PCILeech with FPGA hardware (Screamer M.2) connected via M.2
# On attacker machine:
# pcileech probe
# pcileech dump -min 0x0 -max 0x100000000 -out memdump-dma.raw
# pcileech search -s aes-schedule -in memdump-dma.raw

# With IOMMU enabled, PCILeech DMA reads should fail:
# "Failed to read memory: IOMMU blocked DMA access"
```

### 10.8 Verify Encryption Effectiveness

```bash
# === Verification checklist ===

# 1. Data at rest is encrypted
echo "=== ZFS Encryption ==="
zfs get encryption,keystatus tank/vm-disks
# Expected: aes-256-gcm, available

echo "=== LUKS Status ==="
cryptsetup status vm-200-secure-crypt
# Expected: cipher: aes-xts-plain64, keysize: 512 bits

echo "=== Raw disk read test ==="
# Read raw bytes from encrypted ZFS pool member
dd if=/dev/sda bs=1M count=1 2>/dev/null | xxd | head -5
# Expected: random-looking data (ciphertext)

# 2. Data in transit is encrypted
echo "=== WireGuard tunnel status ==="
wg show wg-dr
# Expected: active peer with recent handshake

echo "=== PBS TLS verification ==="
openssl s_client -connect pbs-server.internal:8007 < /dev/null 2>/dev/null | \
  openssl x509 -noout -subject -dates
# Expected: valid TLS certificate

# 3. Data in backup is encrypted
echo "=== PBS backup encryption ==="
proxmox-backup-client snapshot list \
  --repository pbs-server.internal:store1 2>/dev/null | grep -i encrypt
# Expected: encryption indicators on all snapshots

# 4. Key management is functional
echo "=== Vault key status ==="
vault read transit/keys/pve-node1-zfs
# Expected: shows key versions, rotation dates

echo "=== Vault audit log sample ==="
tail -5 /var/log/vault/audit.log | python3 -m json.tool | \
  grep -E '"type"|"path"|"remote_address"'
# Expected: audit entries for recent key operations
```

### 10.9 Audit Evidence Collection

```bash
# Collect evidence for compliance review

AUDIT_DIR="/root/encryption-audit-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$AUDIT_DIR"

# 1. ZFS encryption configuration
zfs get all tank/vm-disks | grep -E "encryption|key" > "$AUDIT_DIR/zfs-encryption.txt"

# 2. LUKS configuration (no keys — only metadata)
cryptsetup luksDump /dev/pve/vm-200-secure > "$AUDIT_DIR/luks-dump.txt"

# 3. Vault key metadata (no key material)
vault read transit/keys/pve-node1-zfs > "$AUDIT_DIR/vault-keys-node1.txt"
vault read transit/keys/backup-encryption > "$AUDIT_DIR/vault-keys-backup.txt"

# 4. Vault audit log (last 30 days of key operations)
grep "transit" /var/log/vault/audit.log | \
  python3 -c "
import sys, json
for line in sys.stdin:
    entry = json.loads(line)
    ts = entry.get('time', '')
    req = entry.get('request', {})
    print(f'{ts} {req.get(\"operation\",\"\")} {req.get(\"path\",\"\")} from {req.get(\"remote_address\",\"\")}')
" > "$AUDIT_DIR/vault-key-access-log.txt"

# 5. TPM PCR values (prove Secure Boot chain integrity)
tpm2_pcrread sha256:0,1,7 > "$AUDIT_DIR/tpm-pcr-values.txt"

# 6. PBS encryption key fingerprint (not the key itself)
proxmox-backup-client key show /etc/pve/priv/pbs-encryption-key.json > \
  "$AUDIT_DIR/pbs-key-fingerprint.txt"

# 7. Network encryption evidence
wg show wg-dr > "$AUDIT_DIR/wireguard-status.txt"

# 8. System configuration
cat /etc/crypttab > "$AUDIT_DIR/crypttab.txt"
dmsetup table | grep crypt > "$AUDIT_DIR/dmsetup-crypt.txt"

# 9. Generate checksums for evidence integrity
cd "$AUDIT_DIR"
sha256sum * > SHA256SUMS
echo "Audit evidence collected at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "Evidence directory: $AUDIT_DIR"
echo "Files collected: $(ls -1 | wc -l)"
```

### 10.10 Lab Debrief — Expected Outcomes

After completing this lab, verify:

| Test | Expected result | If result differs |
|---|---|---|
| ZFS pool encryption | `aes-256-gcm`, keystatus `available` | Re-create pool with `-O encryption=aes-256-gcm` |
| LUKS volume encryption | `aes-xts-plain64`, 512-bit key | Re-format with correct cipher parameters |
| TPM auto-unlock | Boot completes without passphrase prompt | Check PCR binding, rebuild initramfs |
| Vault KMS | Keys listed with rotation history | Verify Transit engine enabled, key created |
| PBS encrypted backup | Backup completes, shows "(encrypted)" | Verify `--keyfile` parameter, key file permissions |
| ZFS raw send to DR | Data transferred as ciphertext | Use `-w` flag for raw encrypted send |
| Cold boot memory dump | Keys found (without lockdown) | Confirms attack viability; verify lockdown blocks it |
| DMA attack | Blocked by IOMMU | Enable VT-d/AMD-Vi in BIOS, verify `intel_iommu=on` |
| WireGuard tunnel | Active with recent handshake | Check firewall rules, endpoint configuration |
| Audit evidence | Complete set of files with checksums | Re-run collection script |

---

## References

- NIST SP 800-88 Rev.1: "Guidelines for Media Sanitization" (December 2014)
- NIST SP 800-57 Part 1 Rev.5: "Recommendation for Key Management" (May 2020)
- NIST SP 800-111: "Guide to Storage Encryption Technologies for End User Devices" (November 2007)
- IEEE 1619-2018: "Standard for Cryptographic Protection of Data on Block-Oriented Storage Devices"
- Halderman, J.A. et al.: "Lest We Remember: Cold Boot Attacks on Encryption Keys" (USENIX Security 2008)
- Meijer, C. and van Gastel, B.: "Self-encrypting deception: weaknesses in the encryption of solid state drives" (IEEE S&P 2019)
- CVE-2018-12037, CVE-2018-12038: Self-encrypting drive vulnerabilities in Crucial and Samsung SSDs
- Microsoft Security Advisory ADV180028: "Guidance for configuring BitLocker to enforce software encryption"
- TCG Storage Architecture Core Specification, Version 2.01
- TCG Storage Security Subsystem Class: Opal, Version 2.02
- OASIS KMIP Specification Version 2.0
- RFC 8018: PKCS #5 Password-Based Cryptography Specification Version 2.1
- RFC 5869: HMAC-based Extract-and-Expand Key Derivation Function (HKDF)
- Thunderclap: "Thunderclap: Exploring the Security of Thunderbolt Peripherals" (NDSS 2019)
- Proxmox VE Administration Guide (Chapter: Disk Encryption, Storage, Backup)
- Proxmox Backup Server Administration Guide (Chapter: Encryption)
- VMware vSphere Security Guide (VM Encryption, vSAN Encryption)
- HashiCorp Vault Documentation (Transit Secrets Engine, KMIP Secrets Engine)
- OpenZFS Documentation (Native Encryption)
- cryptsetup / LUKS2 documentation (GitLab: cryptsetup/cryptsetup)
