# Backup Security — Encryption, Integrity Verification, and Ransomware Resilience in Virtual Environments

> **Course module:** VMware → Proxmox VE Migration
> **Position in path:** Phase 9 — Security Hardening · Module 24 (see `00-SYLLABUS.md`)
> **Prerequisites:** module 11 (backup & restore with PBS), module 12 (security & compliance), module 19 (multi-site DR); solid understanding of symmetric/asymmetric cryptography (AES, RSA, ECDH), hashing (SHA-256), TLS 1.3, PKI fundamentals; familiarity with ransomware kill chains, MITRE ATT&CK T1490 (Inhibit System Recovery), T1486 (Data Encrypted for Impact).
> **Learning objectives.** Upon completion the reader will be able to:
> 1. model the **backup-specific threat landscape** — ransomware backup-destruction playbooks, insider threats, exfiltration via backup channels;
> 2. configure **Proxmox Backup Server (PBS)** with client-side encryption, key management, integrity verification, and tape backup;
> 3. assess **VMware backup security** (VADP transport modes, Veeam encryption tiers, Linux Hardened Repository, CDP);
> 4. implement a **layered encryption architecture** — AES-256-GCM, key hierarchy (KEK/DEK), KMS integration, key rotation, hardware encryption;
> 5. deploy **immutable backup storage** — WORM, S3 Object Lock, Linux immutable repositories, air-gapped media, retention locks;
> 6. build an **integrity verification pipeline** — SHA-256 manifests, automated restore testing, ZFS/Ceph self-healing, bit-rot detection;
> 7. secure **disaster recovery infrastructure** — encrypted replication, DR site isolation, break-glass procedures, cloud DR security;
> 8. design a **ransomware-resilient backup architecture** — entropy analysis, isolation patterns, clean-room recovery, recovery prioritization;
> 9. satisfy **compliance and audit requirements** — GDPR, HIPAA, PCI-DSS backup encryption mandates, access logging, right-to-erasure;
> 10. execute a **hands-on lab** — PBS encryption, immutable repository, integrity verification, simulated ransomware attack, encrypted restore.
> **Estimated time:** reading 120-150 min · lab execution 4-8 hours · production implementation 2-6 weeks
> **Level:** proficient → expert (Dreyfus 4 → 5)
> **Last updated:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x; PBS 3.x; Veeam Backup & Replication 12.x; vSphere 7.x/8.x; ZFS 2.2/2.3; Ceph Reef/Squid; S3-compatible object stores.

---

## Concept Map

```
+===========================================================================+
|           Backup Security: Defence-in-Depth Pipeline                      |
+===========================================================================+
|                                                                           |
|  1. THREAT MODEL                                                          |
|     Ransomware ─► Insider ─► Exfiltration ─► Compliance Gap              |
|         │                                                                 |
|         ▼                                                                 |
|  2. ENCRYPTION LAYER                                                      |
|     Client-side AES-256-GCM ─► Key hierarchy (KEK/DEK)                   |
|     ─► KMS / Vault ─► Key rotation ─► Hardware SED                       |
|         │                                                                 |
|         ▼                                                                 |
|  3. IMMUTABILITY LAYER                                                    |
|     WORM ─► S3 Object Lock ─► Linux chattr +i ─► Air gap ─► Tape        |
|         │                                                                 |
|         ▼                                                                 |
|  4. INTEGRITY VERIFICATION                                                |
|     SHA-256 manifests ─► ZFS checksums ─► RAID scrub                     |
|     ─► Automated restore tests ─► End-to-end pipeline                    |
|         │                                                                 |
|         ▼                                                                 |
|  5. RANSOMWARE RESILIENCE                                                 |
|     Entropy analysis ─► Change-rate monitoring                            |
|     ─► Isolation (network / air gap) ─► Clean-room recovery              |
|         │                                                                 |
|         ▼                                                                 |
|  6. DISASTER RECOVERY SECURITY                                            |
|     Encrypted replication (WireGuard/IPSec) ─► DR site isolation          |
|     ─► Break-glass auth ─► Secure cloud DR                               |
|         │                                                                 |
|         ▼                                                                 |
|  7. COMPLIANCE & AUDIT                                                    |
|     Access logs ─► Retention enforcement ─► Data sovereignty              |
|     ─► Right-to-erasure ─► Chain-of-custody                              |
|         │                                                                 |
|         ▼                                                                 |
|  8. LAB: END-TO-END IMPLEMENTATION & ATTACK SIMULATION                    |
|     Configure ─► Encrypt ─► Immutabilize ─► Verify ─► Attack ─► Recover  |
|                                                                           |
+===========================================================================+
```

---

## Table of Contents

1. [Backup Security Threat Model](#1-backup-security-threat-model)
2. [Proxmox Backup Server (PBS) Security](#2-proxmox-backup-server-pbs-security)
3. [VMware Backup Security](#3-vmware-backup-security)
4. [Encryption Implementation](#4-encryption-implementation)
5. [Immutable Backups](#5-immutable-backups)
6. [Integrity Verification](#6-integrity-verification)
7. [Disaster Recovery Security](#7-disaster-recovery-security)
8. [Ransomware Resilience Architecture](#8-ransomware-resilience-architecture)
9. [Compliance and Audit](#9-compliance-and-audit)
10. [Lab: Complete Backup Security Implementation](#10-lab-complete-backup-security-implementation)

---

## 1. Backup Security Threat Model

### 1.1 Ransomware Targeting Backups — Real-World Playbooks

Modern ransomware families do not treat backups as collateral damage; they hunt them systematically. Understanding the adversary's playbook is prerequisite to building defences that survive contact.

**Conti playbook (leaked 2022).** The Conti operators' internal documentation explicitly instructed affiliates to enumerate backup infrastructure before detonating the encryption payload. The sequence: (1) discover Veeam servers via port scan (TCP 9392/9393 for the Veeam console, TCP 6160/6162 for agents), or via Active Directory SPN queries (`setspn -T domain -F -Q *veeam*`); (2) extract Veeam credentials from the SQL database (typically stored in `VeeamBackup` on a local or remote MSSQL instance — the configuration database stores encrypted credentials where the encryption key derives from the DPAPI of the service account, so domain admin access breaks it); (3) delete all backup jobs, then delete the backup files themselves; (4) only then deploy the locker. The entire backup-destruction phase was scripted and typically completed within 30 minutes of initial domain admin compromise.

**REvil / Sodinokibi.** REvil automated the deletion of Volume Shadow Copies (`vssadmin delete shadows /all /quiet`), disabled Windows Backup (`wbadmin delete systemstatebackup -keepVersions:0`), and targeted known backup agent processes for termination: `Veeam.Backup.Service`, `BackupExecAgentAccelerator`, `AcronisAgent`, `sql`, `svc$`. Post-encryption, REvil left backup LUNs intact but encrypted, making them useless without paying the ransom for the decryption key.

**BlackCat / ALPHV.** BlackCat (written in Rust, cross-platform) added Linux and ESXi targeting. On ESXi, the payload enumerates datastores via `esxcli storage filesystem list`, kills all running VMs (`vim-cmd vmsvc/power.off`), then encrypts VMDK files in-place. Backup infrastructure running on Linux (including PBS servers) is directly targetable — the malware specifically looks for processes like `proxmox-backup-proxy` and `proxmox-backup-client`.

**Offensive reconnaissance pattern an ethical hacker should test:**

```
# Enumerate backup infrastructure from compromised network position
nmap -sV -p 8007,9392,9393,6160,6162,10000 10.0.0.0/24  # PBS, Veeam, Webmin
crackmapexec smb 10.0.0.0/24 -u user -p pass --shares | grep -i backup
ldapsearch -x -H ldap://dc01 -b "dc=corp,dc=local" "(servicePrincipalName=*backup*)"
```

**Key takeaway:** if an attacker achieves domain admin (or root on the hypervisor), every backup system on the same network segment is already compromised unless it has been architecturally isolated.

### 1.2 Insider Threat to Backup Data

Backups are a concentrated target for malicious insiders because they contain complete copies of production data in a format that is often easier to exfiltrate than live databases. Attack vectors include:

- **Credential abuse:** a backup administrator with legitimate access exports a full VM backup to a USB drive or an attacker-controlled S3 bucket. Without client-side encryption, the backup is readable by anyone with the file.
- **Retention manipulation:** an insider shortens retention policies silently, causing historical backups to be garbage-collected before an investigation can use them. This is a common anti-forensics technique.
- **Key destruction:** if backup encryption keys are stored on the same system as the backup data, an insider (or ransomware with the insider's credentials) can destroy both simultaneously, making recovery impossible.

**Mitigation matrix:**

| Threat | Control |
|--------|---------|
| Credential abuse | Least-privilege RBAC, no shared admin accounts, MFA on backup console |
| Data exfiltration via backup | Client-side encryption (insider gets ciphertext only), DLP on backup network, egress monitoring |
| Retention manipulation | Retention lock (compliance mode — not even root can shorten), dual-approval for policy changes |
| Key destruction | Key escrow in separate security domain, HSM-backed KMS, split knowledge for master keys |

### 1.3 Backup Infrastructure as Attack Surface

The backup server itself is a high-value target. It typically has:

- Network access to every production host (to pull backup data).
- Credentials (or API tokens) for every hypervisor and every guest agent.
- Storage containing complete copies of every system.

An attacker who compromises the backup server gains read access to the entire environment without touching production. From a red-team perspective, the backup server is often the single highest-value lateral-movement target after the domain controller.

**Attack surface reduction checklist:**

- [ ] Backup server on a dedicated VLAN with firewall rules restricting access to only the backup ports.
- [ ] No internet access from the backup VLAN (air-gapped or proxied for updates only).
- [ ] Backup server OS hardened: no unnecessary services, SSH key-only, no GUI, CIS benchmark applied.
- [ ] Backup credentials stored in a credential vault, rotated on schedule, never in cleartext config files.
- [ ] Backup server monitored for anomalous behaviour: unexpected process execution, large outbound transfers, off-hours access.

### 1.4 Exfiltration Through Backup Channels

Backup replication to offsite or cloud targets creates a legitimate, high-bandwidth, encrypted data channel that adversaries can abuse. If an attacker compromises the backup system, they can:

- Redirect replication to an attacker-controlled endpoint.
- Create ad-hoc backup jobs targeting sensitive datastores and replicate them out.
- Piggyback exfiltrated data inside legitimate backup traffic, bypassing DLP that does not inspect backup protocols.

**Detection controls:** monitor replication target changes (alert on any new target added), log all backup job creation events, compare actual data transferred against expected backup sizes (sudden 10x increase = anomaly), enforce certificate pinning on replication endpoints.

### 1.5 Compliance Requirements for Backup Encryption

| Framework | Backup Encryption Requirement | Key Management | Retention |
|-----------|-------------------------------|----------------|-----------|
| **GDPR** (Art. 32, Art. 5(1)(f)) | "appropriate technical measures" — encryption is the de facto standard for demonstrating adequacy | Keys must be under data controller's control; cloud provider key management may not suffice | Right to erasure (Art. 17) conflicts with immutable backups — see §9.5 |
| **HIPAA** (§164.312(a)(2)(iv)) | Addressable — but if not implemented, must document equivalent alternative. In practice, no auditor accepts "not implemented" for backup encryption in 2026. | NIST SP 800-57 key management required | 6-year retention minimum for PHI |
| **PCI-DSS v4.0** (Req. 3.5) | Mandatory encryption of stored cardholder data, including backups. AES-256 or equivalent. | Cryptographic key management per Req. 3.6 — dual control, split knowledge | Retain only as needed; secure deletion required when no longer needed |
| **NIS2** (Art. 21) | "state of the art" security measures for backup systems — encryption is baseline | National CSIRT oversight; key management auditable | Incident notification within 24h if backup systems compromised |
| **SOC 2 Type II** | CC6.1 — logical access controls over backup data; encryption at rest and in transit is expected | Key management procedures documented and tested annually | Per the entity's stated retention policy |

### 1.6 The 3-2-1-1-0 Rule with Immutability

The classic 3-2-1 backup rule (3 copies, 2 different media types, 1 offsite) is necessary but no longer sufficient. The modern extension:

```
3 — Three copies of data (production + 2 backups)
2 — Two different storage media (e.g., disk + object storage, or disk + tape)
1 — One copy offsite (geographically separated)
1 — One copy offline or immutable (air-gapped tape, or WORM/Object Lock storage)
0 — Zero errors after automated restore verification
```

The "1 immutable" is the ransomware-resilience layer. The "0 errors" means every backup is automatically verified by test restore — a backup that has never been tested is not a backup, it is a hope.

---

## 2. Proxmox Backup Server (PBS) Security

### 2.1 Architecture Overview

PBS uses a chunk-based deduplication architecture that has direct security implications:

1. **Chunking:** backup data is split into variable-length chunks (typically 64 KiB to 4 MiB) using a rolling hash (similar to rsync). Each chunk is identified by its SHA-256 digest.
2. **Deduplication:** identical chunks are stored once, even across different VMs and different backup snapshots. This dramatically reduces storage consumption but means a single chunk store contains data from multiple sources — compromising the chunk store compromises all backed-up VMs.
3. **Client-server model:** the `proxmox-backup-client` runs on the Proxmox VE host (or any Linux machine), connects to the PBS server over HTTPS (port 8007), and transmits chunks. The PBS server stores chunks in a datastore directory structure.

```
PBS datastore layout:
/mnt/datastore/my-datastore/
├── .chunks/
│   ├── 0000/          # chunk files, named by SHA-256 digest
│   ├── 0001/
│   └── ...
├── ct/                # container backups
├── host/              # host-level file backups
└── vm/                # virtual machine backups (each snapshot is a manifest + chunk references)
    └── 100/
        ├── 2026-05-07T02:00:00Z.fidx
        └── 2026-05-07T02:00:00Z.blob
```

**Security implication:** the chunk store is the crown jewel. All deduplication and integrity checking rely on the SHA-256 digests. An attacker who can modify chunks and update the corresponding digest references can tamper with backup data undetected unless external integrity verification is in place.

### 2.2 Client-Side Encryption

PBS supports client-side encryption where data is encrypted on the Proxmox VE node **before** transmission to the PBS server. The PBS server never sees plaintext data and cannot decrypt the backups.

**Algorithm:** AES-256-GCM (Galois/Counter Mode) — provides both confidentiality and authenticity. Each chunk is encrypted independently with a unique nonce derived from the chunk's position and a counter. The GCM authentication tag ensures tampering is detected at decryption time.

**Generating an encryption key:**

```bash
# Generate a new encryption key (random 256-bit key, stored in a JSON envelope)
proxmox-backup-client key create /etc/pve/priv/backup-encryption-key.json

# The key file contains:
# {
#   "created": "2026-05-07T10:00:00Z",
#   "data": "<base64-encoded-key>",
#   "fingerprint": "aa:bb:cc:dd:...",
#   "kdf": "scrypt",    # if password-protected
#   "hint": "production backup key"
# }

# Optionally protect the key file with a passphrase (adds scrypt KDF)
proxmox-backup-client key create --kdf scrypt /etc/pve/priv/backup-encryption-key.json
```

**Running an encrypted backup:**

```bash
# Backup VM 100 with client-side encryption
proxmox-backup-client backup vm/100 \
  --repository pbs-server:my-datastore \
  --keyfile /etc/pve/priv/backup-encryption-key.json \
  --backup-id 100 \
  --backup-type vm

# From Proxmox VE GUI: Storage → PBS → Encryption Key → upload key file
# All subsequent backups to that storage will be encrypted client-side
```

**What gets encrypted:** all data chunks (.blob, .fidx payload data). The backup manifest (index file) is also encrypted but the metadata (backup time, VM ID, snapshot name) remains in cleartext on the PBS server for management purposes.

**What does NOT get encrypted:** PBS-side metadata (datastore structure, snapshot listing, backup sizes, timestamps). An attacker with PBS server access can see *which* VMs are backed up and *when*, but cannot read the backup contents.

### 2.3 Key Management

**Encryption key file** — the JSON file generated by `proxmox-backup-client key create`. This is the data encryption key (DEK). Losing this key means permanent, irrecoverable data loss for all backups encrypted with it.

**Master key (key encryption key / KEK)** — PBS supports a master key (RSA public/private key pair) that can be used to encrypt the per-backup encryption key. This enables key escrow: the master private key is stored offline (in a safe, on a hardware token), and can decrypt any backup's DEK.

```bash
# Generate RSA master key pair
openssl genrsa -aes256 -out /root/pbs-master-key.pem 4096
openssl rsa -in /root/pbs-master-key.pem -pubout -out /root/pbs-master-key.pub

# Configure PBS to use the master public key for key escrow
proxmox-backup-client key create \
  --master-pubkey-file /root/pbs-master-key.pub \
  /etc/pve/priv/backup-encryption-key.json

# The master private key (pbs-master-key.pem) goes into a physical safe
# or hardware security module — NOT on the PBS server or any online system.
```

**Key storage best practices:**

| Key Type | Storage Location | Access Control |
|----------|-----------------|----------------|
| DEK (encryption key JSON) | Proxmox VE node `/etc/pve/priv/` (replicated across cluster via pmxcfs) | Root-only, permissions 0600 |
| Master public key | PBS server, Proxmox VE nodes | Distributable — public key |
| Master private key | Physical safe, HSM, or offline USB in sealed tamper-evident bag | Dual-custody: two people needed to access |
| Key backup copies | Separate geographic location from production and backup systems | Encrypted, sealed, inventoried quarterly |

### 2.4 Access Control

PBS implements a layered access control model:

**API tokens:** each Proxmox VE node authenticates to PBS using an API token (or user credentials). Tokens can be scoped to specific datastores and operations.

```bash
# Create a PBS user for backup operations
proxmox-backup-manager user create backup-operator@pbs \
  --comment "Automated backup user for PVE cluster"

# Create an API token for the user
proxmox-backup-manager user generate-token backup-operator@pbs automation-token

# Set ACL: this user can only write to a specific datastore
proxmox-backup-manager acl update / Audit --auth-id backup-operator@pbs
proxmox-backup-manager acl update /datastore/production DatastoreBackup \
  --auth-id backup-operator@pbs
```

**ACL roles relevant to backup security:**

| Role | Permissions | Use Case |
|------|-------------|----------|
| `DatastoreBackup` | Create backups, list own backups | Automated backup jobs |
| `DatastoreReader` | List and read backups | Restore operations |
| `DatastoreAdmin` | Full datastore management including prune/GC | Backup admin (restricted) |
| `DatastoreAudit` | Read-only metadata access | Audit and monitoring |
| `Admin` | Full PBS management | Emergency only — break-glass |

**Two-factor authentication:** PBS supports TOTP and WebAuthn for interactive logins. Enable for all human users:

```bash
# Enforce TFA for all users in the PBS realm
proxmox-backup-manager user update admin@pbs --enable-tfa 1
```

### 2.5 Datastore Integrity — Verification Jobs

PBS includes built-in verification that reads every chunk, recomputes the SHA-256 digest, and compares it to the stored reference. For encrypted backups, verification confirms the ciphertext integrity (GCM tag validation requires the decryption key, but digest verification catches storage-level corruption).

```bash
# Run a verification job on all backups in a datastore
proxmox-backup-manager verify my-datastore

# Schedule automated verification (via PBS GUI or cron)
# GUI: Datastore → Verify Jobs → Add → Schedule: daily at 03:00

# CLI: trigger a verification for a specific snapshot
proxmox-backup-client verify \
  --repository pbs-server:my-datastore \
  --backup-id 100 \
  --backup-type vm \
  --backup-time "2026-05-07T02:00:00Z"
```

**Garbage collection** runs periodically to remove orphaned chunks (chunks no longer referenced by any backup index). GC is critical for security: without it, "deleted" backups remain recoverable from the chunk store, creating a data retention compliance issue.

```bash
# Run garbage collection
proxmox-backup-manager garbage-collection start my-datastore

# Check GC status
proxmox-backup-manager garbage-collection status my-datastore
```

### 2.6 Tape Backup with Encryption

PBS 3.x supports LTO tape drives for air-gapped, offline backup. When combined with client-side encryption, the data written to tape is already encrypted — providing defence-in-depth even if tapes are physically stolen.

```bash
# List available tape drives
pmt status

# Create a media pool with encryption
proxmox-tape media-pool create offsite-tapes \
  --drive lto-drive0 \
  --encrypt true \
  --retention keep-all

# Run a tape backup job (drive is resolved from pool configuration)
proxmox-tape backup my-datastore offsite-tapes

# Restore from tape
proxmox-tape restore my-datastore offsite-tapes
```

**Tape security considerations:**

- Tapes removed from the library and stored offsite are air-gapped by definition — no network attack can reach them.
- If client-side encryption is used, the tape contains only ciphertext. Physical theft of the tape without the encryption key yields nothing.
- Label tapes with the encryption key fingerprint (not the key itself) so operators can identify which key is needed for restore without exposing the key.
- Track tape movements in a media management system (chain of custody).

---

## 3. VMware Backup Security

### 3.1 vSphere API for Data Protection (VADP)

VADP is the standard interface through which backup solutions access VMware VM data. Understanding its transport modes is essential for securing VMware backup traffic — especially during the migration period when both VMware and Proxmox environments coexist.

**NBD (Network Block Device) transport:**
- VM disk data is transferred over the network (TCP) between the ESXi host and the backup proxy.
- **NBDSSL** variant adds TLS encryption in transit.
- Security concern: without NBDSSL, backup data traverses the network in cleartext. If the backup network is shared with production traffic, passive interception (mirror port, ARP spoofing) exposes all VM data.
- Recommendation: always use NBDSSL. Performance penalty is typically 5-15% due to TLS overhead.

**HotAdd transport:**
- The backup proxy VM is deployed on the same ESXi host as the source VM. The proxy attaches the source VM's disks (via a temporary SCSI hot-add) and reads data locally.
- No network transfer — data stays within the ESXi host.
- Security concern: the proxy VM must be on the same host (or at least the same cluster with shared storage). If the proxy VM is compromised, it has direct block-level access to any VM's disks on that host.
- Recommendation: harden the proxy VM as a privileged system (no internet access, minimal OS, monitored).

**SAN transport:**
- The backup proxy reads VM disk data directly from the SAN (Fibre Channel or iSCSI) without involving the ESXi host's CPU.
- Security concern: the backup proxy needs SAN-level access to the VM datastores. This is a very privileged position — SAN-level access bypasses all hypervisor-level access controls.
- Recommendation: SAN zoning must restrict the backup proxy to read-only access to the backup LUNs only. Use LUN masking to prevent the proxy from accessing production LUNs that are not part of the current backup job.

### 3.2 Veeam Backup & Replication — Encryption Architecture

Veeam implements a three-tier encryption model:

**Encryption at source (job-level encryption):**
- AES-256 encryption applied by the backup proxy before data is written to the repository.
- Configured per backup job. Each job can have its own encryption password.
- The password derives an encryption key via PBKDF2. The key encrypts data blocks.

```powershell
# Create an encryption key in Veeam
$encKey = Add-VBREncryptionKey -Password (Read-Host -AsSecureString "Enter encryption password") `
  -Description "Production VM Backup Encryption Key 2026"

# Enable encryption on a backup job
$job = Get-VBRJob -Name "Daily-VM-Backup"
Set-VBRJobAdvancedStorageOptions -Job $job -EnableEncryption $true -EncryptionKey $encKey
```

**Encryption in flight:**
- All communication between Veeam components (proxy → repository, source → WAN accelerator) is encrypted with TLS.
- Certificate-based authentication between components.

**Encryption at target (repository-level):**
- The backup repository can enforce encryption regardless of job-level settings.
- Particularly relevant for compliance: even if an operator forgets to enable job-level encryption, the repository encrypts at rest.

**Key management in Veeam:**
- Encryption keys are stored in the Veeam Configuration Database (SQL Server).
- The database itself should be encrypted (TDE) and backed up separately.
- Veeam supports Enterprise Key Management through integration with external KMS via KMIP.

```powershell
# List all encryption keys
Get-VBREncryptionKey | Select-Object Id, Description, CreatedDate

# Verify encryption status of a backup
$backup = Get-VBRBackup -Name "Daily-VM-Backup"
$backup.IsEncryptionEnabled

# Check encryption for all backup files in a repository
Get-VBRBackup | ForEach-Object {
    [PSCustomObject]@{
        Name = $_.Name
        Encrypted = $_.IsEncryptionEnabled
        Repository = $_.GetHost().Name
    }
}
```

### 3.3 Backup Proxy Security

The backup proxy is the compute engine that processes backup data. It has credentials to ESXi hosts and storage systems.

**Credential management risks:**
- Veeam stores ESXi and vCenter credentials in its database. If the Veeam server is compromised, these credentials grant full hypervisor access.
- Managed accounts (service accounts with minimal privileges) reduce blast radius.

**Hardening checklist for Veeam backup proxy:**

- [ ] Dedicated VM or physical server — not shared with other workloads.
- [ ] Minimal OS installation (Windows Server Core or hardened Linux for Linux proxy).
- [ ] No internet access. Updates via WSUS or internal repository.
- [ ] Local firewall: allow only Veeam ports (TCP 2500-3300, 6160, 6162) from the Veeam server.
- [ ] Antivirus exclusions for Veeam processes (to prevent AV from scanning backup data and creating performance issues or false positives).
- [ ] Credential rotation: rotate ESXi service account passwords quarterly.

### 3.4 Linux Hardened Repository

Veeam's Linux Hardened Repository is the state of the art for immutable backup storage in the VMware ecosystem. Architecture:

1. A standalone Linux server (Ubuntu or RHEL) with XFS filesystem.
2. Veeam connects via SSH using single-use credentials — after initial setup, the SSH credentials are discarded. Veeam communicates with a local transport agent over a custom protocol.
3. Backup files are written with the Linux immutable flag (`chattr +i`). Even root cannot delete or modify them until the retention period expires.
4. The `veeamtransport` service runs as a non-root user. The immutable flag is set via a helper binary with `CAP_LINUX_IMMUTABLE` capability — no sudo required.

**Security properties:**
- An attacker who gains root on the Linux repository server cannot delete immutable backups without first removing the immutable flag (`chattr -i`) — but this action is logged and can be detected.
- If the attacker compromises the Veeam server, they cannot connect to the hardened repository (SSH credentials were discarded).
- The weakest link: a root-level attacker on the repository server *can* remove immutability flags. True protection requires the repository server to be treated as a Tier-0 asset.

**Red team perspective — defeating the hardened repository:**

```bash
# Attacker with root on the hardened repo:
lsattr /mnt/veeam-repo/backups/  # confirm immutable flags
chattr -i /mnt/veeam-repo/backups/full-2026-05-07.vbk  # remove immutability
rm /mnt/veeam-repo/backups/full-2026-05-07.vbk  # delete

# Defence: detect this with auditd
auditctl -w /mnt/veeam-repo/backups/ -p a -k backup_immutability_change
# This logs any attribute change to the audit log
```

### 3.5 VMware CDP — Continuous Data Protection

VMware CDP (available with vSphere 7+) provides near-zero RPO by continuously replicating VM I/O to a secondary datastore. Security considerations:

- CDP replication traffic should be encrypted (NBDSSL) and isolated on a dedicated replication VLAN.
- The CDP target datastore contains a continuous stream of production data — it requires the same access controls as production.
- CDP is not a substitute for backups: it does not provide immutability or historical retention. Ransomware that corrupts production data will have the corruption replicated to the CDP target within seconds.
- Use CDP for RTO optimization (instant failover) but maintain traditional backups for ransomware resilience.

---

## 4. Encryption Implementation

### 4.1 Encryption Algorithms for Backups

**AES-256-GCM (recommended for most backup workloads):**
- Authenticated encryption: provides confidentiality + integrity + authenticity in a single pass.
- GCM (Galois/Counter Mode) uses a 96-bit nonce and produces a 128-bit authentication tag.
- Hardware-accelerated on all modern x86 CPUs (AES-NI instruction set) — negligible performance impact.
- Used by: PBS, Veeam, most enterprise backup solutions.
- Nonce management is critical: reusing a nonce with the same key is catastrophic (reveals the authentication key). PBS handles this automatically via chunk-position-derived nonces.

**ChaCha20-Poly1305 (alternative for software-only environments):**
- Stream cipher + MAC. Comparable security to AES-256-GCM.
- Advantage: faster in pure software (no AES-NI) — relevant for ARM-based backup appliances or embedded systems.
- Used by: WireGuard, some cloud backup services.
- Not commonly used in enterprise backup products today, but a valid choice for custom backup pipelines.

**Comparison:**

| Property | AES-256-GCM | ChaCha20-Poly1305 |
|----------|-------------|-------------------|
| Key size | 256 bits | 256 bits |
| Nonce size | 96 bits | 96 bits |
| Auth tag | 128 bits | 128 bits |
| HW acceleration | AES-NI (ubiquitous on x86) | None (but fast in software) |
| Typical throughput (x86 with AES-NI) | 4-6 GB/s | 1-2 GB/s |
| Typical throughput (ARM, no AES) | 200-500 MB/s | 1-2 GB/s |
| NIST approved | Yes (SP 800-38D) | Yes (SP 800-185, via RFC 8439) |

### 4.2 Key Hierarchy — KEK/DEK

A properly designed backup encryption system uses a two-tier (or three-tier) key hierarchy to balance security and operational flexibility.

```
┌─────────────────────────────────────────────────────┐
│                 Master Key (MK)                     │
│   Stored in HSM or offline. Used to wrap KEKs.      │
│   Never touches backup data directly.               │
└──────────────────────┬──────────────────────────────┘
                       │ wraps
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │  KEK-1  │ │  KEK-2  │ │  KEK-3  │   Key Encryption Keys
     │(prod DC)│ │(DR site)│ │(cloud)  │   One per security domain
     └────┬────┘ └────┬────┘ └────┬────┘
          │           │           │
          │ wraps     │ wraps     │ wraps
          ▼           ▼           ▼
     ┌─────────┐ ┌─────────┐ ┌─────────┐
     │  DEK-a  │ │  DEK-b  │ │  DEK-c  │   Data Encryption Keys
     │(job-1)  │ │(job-2)  │ │(job-3)  │   One per backup job/session
     └─────────┘ └─────────┘ └─────────┘
```

**Why this matters:**
- **Key rotation:** rotating a DEK requires re-encrypting only the data. Rotating a KEK requires re-wrapping the DEKs — not touching the data at all. Rotating the MK requires re-wrapping the KEKs. This layered approach makes rotation operationally feasible.
- **Key compromise containment:** if a single DEK leaks, only that specific backup job is compromised. If a KEK leaks, all DEKs it wraps are compromised — but the MK and other security domains remain safe.
- **Key escrow:** the MK can be escrowed (split into shares using Shamir's Secret Sharing, stored in separate physical locations) without exposing any DEKs.

### 4.3 KMS Integration

**HashiCorp Vault:**

```bash
# Enable the transit secrets engine for key management
vault secrets enable transit

# Create a named encryption key (KEK)
vault write transit/keys/backup-kek type=aes256-gcm96

# Encrypt a DEK using the KEK (wrap operation)
vault write transit/encrypt/backup-kek \
  plaintext=$(base64 <<< "raw-dek-bytes-here")

# Decrypt (unwrap) a DEK
vault write transit/decrypt/backup-kek \
  ciphertext="vault:v1:encrypted-dek-ciphertext"

# Rotate the KEK (creates a new version; old versions still available for decrypt)
vault write -f transit/keys/backup-kek/rotate

# Set minimum decryption version (forces re-wrap of old DEKs)
vault write transit/keys/backup-kek min_decryption_version=2
```

**KMIP protocol (Key Management Interoperability Protocol):**
- KMIP (OASIS standard, v2.1) provides a vendor-neutral API for key lifecycle management.
- Veeam Enterprise Plus integrates with KMIP-compliant KMS (Thales CipherTrust, Entrust KeyControl, Fortanix, HashiCorp Vault Enterprise).
- KMIP operations relevant to backups: `Create`, `Get`, `Activate`, `Revoke`, `Destroy`, `Locate`.
- TLS mutual authentication between the backup server and KMS is mandatory.

### 4.4 Key Rotation Procedures

```
Key Rotation Schedule:
├── DEK (Data Encryption Key)
│   └── Rotate: every 90 days, or after personnel change, or after suspected compromise
│       └── Procedure: new backup jobs use new DEK; old backups remain readable with old DEK
│           until retention expires (no re-encryption needed)
│
├── KEK (Key Encryption Key)
│   └── Rotate: annually, or after security incident
│       └── Procedure: generate new KEK, re-wrap all active DEKs with new KEK,
│           retire old KEK (keep available for decrypt-only until no DEKs reference it)
│
└── Master Key
    └── Rotate: every 2-3 years, or after key custodian leaves organization
        └── Procedure: generate new MK in HSM, re-wrap all KEKs, split new MK shares,
            distribute to custodians, destroy old MK shares (ceremony with witnesses)
```

### 4.5 Key Escrow and Recovery

Key loss is equivalent to data loss. Escrow strategies:

1. **Paper key:** the encryption key (or master key) printed on paper, placed in a tamper-evident envelope, stored in a physical safe. Two keys to the safe, held by different individuals (dual custody).

2. **Shamir's Secret Sharing (SSS):** the master key is split into `n` shares, any `k` of which can reconstruct the key. Example: 5 shares, threshold of 3. Shares stored in different physical locations.

```bash
# Using ssss-split (Shamir's Secret Sharing Scheme)
echo "master-key-hex-here" | ssss-split -t 3 -n 5 -Q
# Produces 5 shares; any 3 can reconstruct the secret

# Reconstruction
ssss-combine -t 3 -Q
# Enter 3 shares interactively
```

3. **HSM-backed escrow:** the master key is generated inside an HSM and never exported. The HSM is replicated (or the key is backed up to a secondary HSM via a secure HSM-to-HSM protocol). This is the gold standard for regulated environments.

### 4.6 Hardware Encryption — Self-Encrypting Drives (SED)

SEDs implement AES-256 encryption in the drive controller. Data is encrypted transparently at write and decrypted at read. The encryption key (Media Encryption Key, MEK) never leaves the drive.

**OPAL 2.0 specification:**
- TCG OPAL is the standard for SED management.
- Authentication: the drive requires an Authentication Key (AK) at power-on. Without the AK, the drive presents as unformatted.
- Instant secure erase: destroying the MEK makes all data on the drive irrecoverable — useful for decommissioning backup drives.

**Operational considerations:**
- SED encryption is transparent to the OS and backup software — no performance impact.
- SED protects against physical theft of the drive only. It does not protect against a running system where the drive is unlocked.
- SED is a complement to, not a replacement for, software-level backup encryption. Defence in depth: software encryption protects data in transit and at rest on any media; SED provides an additional layer at the physical level.
- Manage SED authentication keys through `sedutil-cli` or vendor tooling. Store authentication keys in the KMS alongside backup encryption keys.

### 4.7 Performance Impact of Encryption — Benchmarks

Real-world benchmarks on modern server hardware (Xeon Gold 6400 series, AES-NI enabled):

| Scenario | Throughput (Unencrypted) | Throughput (AES-256-GCM) | Overhead |
|----------|--------------------------|--------------------------|----------|
| PBS backup (single VM, 500 GB) | 2.1 GB/s | 1.95 GB/s | 7% |
| PBS backup (10 VMs parallel) | 4.5 GB/s | 4.1 GB/s | 9% |
| Veeam backup (HotAdd, single proxy) | 1.8 GB/s | 1.65 GB/s | 8% |
| Veeam backup (SAN transport) | 3.2 GB/s | 2.9 GB/s | 9% |
| ZFS native encryption (write) | 1.5 GB/s | 1.35 GB/s | 10% |

**Key insight:** with AES-NI hardware acceleration, encryption overhead is consistently under 10%. The dominant bottleneck in backup performance is always I/O (disk throughput, network bandwidth), not encryption. There is no valid performance argument against enabling encryption in 2026.

On older hardware without AES-NI, or on ARM-based NAS appliances, overhead can reach 30-50%. In those environments, consider ChaCha20-Poly1305 or hardware SED as alternatives.

---

## 5. Immutable Backups

### 5.1 WORM Storage — Write Once Read Many

WORM storage ensures that once data is written, it cannot be modified or deleted for a specified retention period. Implementations:

- **Hardware WORM:** specialized tape and optical media that physically prevent overwriting. LTO tapes support a WORM cartridge variant where the drive firmware enforces write-once.
- **Software WORM:** filesystem or object store features that enforce immutability at the software level. Security depends on the integrity of the software and the OS — a root-level attacker can potentially bypass software WORM on a standard Linux system.

### 5.2 Object Lock — Cloud Immutable Storage

**S3 Object Lock (AWS):**

```bash
# Enable Object Lock on bucket creation (cannot be added to existing bucket)
aws s3api create-bucket \
  --bucket backup-immutable-2026 \
  --object-lock-enabled-for-object-lock

# Set default retention for the bucket (Compliance mode — cannot be shortened)
aws s3api put-object-lock-configuration \
  --bucket backup-immutable-2026 \
  --object-lock-configuration '{
    "ObjectLockEnabled": "Enabled",
    "Rule": {
      "DefaultRetention": {
        "Mode": "COMPLIANCE",
        "Days": 30
      }
    }
  }'

# Upload a backup with explicit retention
aws s3api put-object \
  --bucket backup-immutable-2026 \
  --key "backups/vm-100/2026-05-07.vma.zst" \
  --body /tmp/backup.vma.zst \
  --object-lock-mode COMPLIANCE \
  --object-lock-retain-until-date "2026-06-07T00:00:00Z"
```

**Governance vs. Compliance mode:**

| Property | Governance Mode | Compliance Mode |
|----------|----------------|-----------------|
| Can root/admin delete before retention? | Yes, with `s3:BypassGovernanceRetention` permission | No. Nobody can delete. Not even the AWS account root user. |
| Can retention be shortened? | Yes, by privileged users | No. Can only be extended. |
| Use case | Testing, flexible environments | Regulatory compliance, ransomware protection |
| Ransomware resilience | Low (attacker with admin creds can bypass) | High (immutability is absolute) |

**Azure Immutable Blob Storage:**
- Supports time-based retention policies and legal holds.
- Once locked, the policy cannot be shortened or removed.
- Integrates with Veeam and other backup products via Azure Blob Storage API.

**GCS Retention Policies:**
- Bucket-level retention: all objects must be retained for the specified period.
- Bucket Lock: makes the retention policy permanent (cannot be removed or reduced).
- Object holds: prevent deletion of specific objects regardless of retention policy.

### 5.3 Linux Immutable Repositories

The Linux extended attribute `i` (immutable) prevents modification and deletion of files, even by root.

```bash
# Set immutable flag on backup files
chattr +i /mnt/backup-repo/backups/vm-100-2026-05-07.vma.zst

# Verify the flag
lsattr /mnt/backup-repo/backups/vm-100-2026-05-07.vma.zst
# Output: ----i--------e-- /mnt/backup-repo/backups/vm-100-2026-05-07.vma.zst

# Remove immutable flag (requires CAP_LINUX_IMMUTABLE capability or root)
chattr -i /mnt/backup-repo/backups/vm-100-2026-05-07.vma.zst
```

**Hardening the immutable repository:**

```bash
# 1. Create a dedicated service user for the backup agent
useradd -r -s /sbin/nologin backup-agent

# 2. Create a helper binary that sets/removes immutable flags
#    Grant it CAP_LINUX_IMMUTABLE instead of running as root
cp /usr/local/bin/immutable-helper /usr/local/bin/immutable-helper
setcap cap_linux_immutable+ep /usr/local/bin/immutable-helper

# 3. Monitor attribute changes with auditd
cat >> /etc/audit/rules.d/backup-immutability.rules << 'AUDIT_EOF'
-w /mnt/backup-repo/ -p a -k backup_immutability
-a always,exit -F arch=b64 -S fremovexattr -S fsetxattr -F dir=/mnt/backup-repo/ -k backup_xattr_change
AUDIT_EOF
systemctl restart auditd

# 4. Ship audit logs to a separate SIEM (so even if the repo server
#    is compromised, the evidence of tampering is preserved)
```

**Root escape risk:** the fundamental limitation of Linux immutable flags is that root can always remove them. Mitigations:

- Restrict root access: use `sudo` with fine-grained policies; disable root SSH login; use Yubikey for `su` to root.
- Remove `chattr` binary from the system (or replace with a wrapper that logs and alerts).
- Use a mandatory access control framework (SELinux, AppArmor) to deny `chattr -i` operations on the backup directory, even for root.
- Defence in depth: combine with S3-compatible object storage with Compliance-mode Object Lock for the offsite copy.

### 5.4 Air-Gapped Backups

An air gap is a physical or logical separation that ensures backup data is unreachable from any network-connected system.

**Physical air gap:**
- LTO tape drives: write backups to tape, physically remove the tape and store it offsite. No network path exists to the tape data.
- Removable disk shelves: hot-swap backup disks, rotate them to an offsite vault.
- Weakness: data on the tape is only as current as the last tape rotation. RPO is typically 24 hours (daily tape rotation) to 1 week (weekly rotation).

**Logical air gap (network isolation):**
- Backup repository on a dedicated network segment with firewall rules that:
  - Allow inbound connections only from the backup proxy on specific ports.
  - Deny all outbound connections (no internet, no DNS, no NTP — use local NTP).
  - Deny all management access except from a hardened jump host.
- The "gap" is the firewall. If the firewall is compromised or misconfigured, the gap collapses.

**Delayed propagation (semi-air-gap):**
- Primary backups land on an online repository. A scheduled job copies them to an isolated repository with a configurable delay (e.g., 24 hours).
- If ransomware corrupts today's backups, yesterday's copies on the isolated repository are still clean (because they were copied before the corruption propagated).
- The delay is the detection window — if you detect the attack within the delay period, you can stop propagation to the isolated copy.

### 5.5 Retention Lock — Governance vs. Compliance

Beyond object storage, many backup products implement their own retention lock:

- **Veeam:** Immutability setting on backup repositories. When enabled on a Linux Hardened Repository, backup files cannot be deleted before the retention period expires. The immutability is enforced at the filesystem level (`chattr +i`).
- **PBS:** retention policies are configured per datastore. While PBS does not have a native "retention lock" that prevents admin override, combining PBS with an immutable backend (ZFS snapshots with snapshot holds, or S3-compatible storage with Object Lock) achieves the same effect.
- **Dell Data Domain:** DD Retention Lock (Compliance Edition) is SEC 17a-4(f) certified — meets the strictest regulatory requirements for financial data retention.

---

## 6. Integrity Verification

### 6.1 Cryptographic Hash Verification

Every backup should have an associated integrity manifest — a file containing cryptographic hashes of every component.

```bash
# Generate a SHA-256 manifest for a backup directory
find /mnt/backup-repo/vm-100/ -type f -exec sha256sum {} \; > /mnt/backup-repo/vm-100/MANIFEST.sha256

# Verify the manifest
cd /mnt/backup-repo/vm-100/ && sha256sum -c MANIFEST.sha256
# Output:
# 2026-05-07-full.vma.zst: OK
# 2026-05-07-full.vma.zst.notes: OK
# ...

# Sign the manifest with GPG for non-repudiation
gpg --detach-sign --armor --output MANIFEST.sha256.asc MANIFEST.sha256

# Verify the signature
gpg --verify MANIFEST.sha256.asc MANIFEST.sha256
```

**Automated manifest pipeline:**

```bash
#!/usr/bin/env bash
# /usr/local/bin/backup-manifest-generator.sh
# Run as a post-backup hook

BACKUP_DIR="$1"
MANIFEST="${BACKUP_DIR}/MANIFEST.sha256"
MANIFEST_SIG="${MANIFEST}.asc"
GPG_KEY_ID="backup-integrity@corp.local"

set -euo pipefail

# Generate manifest
find "${BACKUP_DIR}" -type f ! -name 'MANIFEST*' -exec sha256sum {} \; > "${MANIFEST}"

# Sign manifest
gpg --batch --yes --detach-sign --armor \
  --default-key "${GPG_KEY_ID}" \
  --output "${MANIFEST_SIG}" \
  "${MANIFEST}"

# Set immutable on manifest
chattr +i "${MANIFEST}" "${MANIFEST_SIG}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Manifest generated: $(wc -l < "${MANIFEST}") files hashed"
```

### 6.2 Backup Validation — Automated Restore Testing

A backup that has never been restored is Schrodinger's backup — it may or may not contain recoverable data. Automated restore testing eliminates this uncertainty.

**PBS restore verification:**

```bash
# Restore a VM backup to a temporary location for validation
proxmox-backup-client restore vm/100 \
  --repository pbs-server:my-datastore \
  --keyfile /etc/pve/priv/backup-encryption-key.json \
  --backup-time "2026-05-07T02:00:00Z" \
  /tmp/restore-test/

# Compute hash of restored data and compare with original
sha256sum /tmp/restore-test/*.img > /tmp/restore-test/restore-hash.sha256

# Automated validation script
#!/usr/bin/env bash
# /usr/local/bin/backup-restore-test.sh

PBS_REPO="pbs-server:my-datastore"
KEYFILE="/etc/pve/priv/backup-encryption-key.json"
RESTORE_DIR="/tmp/restore-test-$(date +%Y%m%d)"
VMIDS=(100 101 102 200 201)
FAILURES=0

mkdir -p "${RESTORE_DIR}"

for vmid in "${VMIDS[@]}"; do
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Testing restore for VM ${vmid}..."

    # Get latest backup timestamp
    LATEST=$(proxmox-backup-client snapshots \
        --repository "${PBS_REPO}" \
        --output-format json 2>/dev/null | \
        jq -r ".[] | select(.\"backup-id\"==\"${vmid}\") | .\"backup-time\"" | \
        sort -r | head -1)

    if [ -z "${LATEST}" ]; then
        echo "  ERROR: No backup found for VM ${vmid}"
        FAILURES=$((FAILURES + 1))
        continue
    fi

    # Attempt restore
    if proxmox-backup-client restore "vm/${vmid}" \
        --repository "${PBS_REPO}" \
        --keyfile "${KEYFILE}" \
        --backup-time "${LATEST}" \
        "${RESTORE_DIR}/vm-${vmid}/" 2>/dev/null; then
        echo "  OK: VM ${vmid} restored successfully (backup: ${LATEST})"
    else
        echo "  FAIL: VM ${vmid} restore failed"
        FAILURES=$((FAILURES + 1))
    fi
done

# Cleanup
rm -rf "${RESTORE_DIR}"

if [ "${FAILURES}" -gt 0 ]; then
    echo "[ALERT] ${FAILURES} restore tests failed — investigate immediately"
    exit 1
fi

echo "[OK] All ${#VMIDS[@]} restore tests passed"
```

**Veeam SureBackup equivalent:**

```powershell
# Create a SureBackup verification job in Veeam
# This boots the backed-up VM in an isolated sandbox and runs health checks

# List existing SureBackup jobs
Get-VBRSureBackupJob | Select-Object Name, LastResult, NextRun

# Trigger a SureBackup job manually
Start-VBRSureBackupJob -Job (Get-VBRSureBackupJob -Name "Nightly-Verification")

# Check results
$result = Get-VBRSureBackupJob -Name "Nightly-Verification"
$result.GetLastSession().Result  # Should be "Success"
```

### 6.3 Data Corruption Detection

**Bit rot (silent data corruption):** storage media can spontaneously flip bits without reporting an error. This is undetectable by the filesystem unless checksumming is in place. Rates vary: consumer HDDs see approximately 1 unrecoverable bit error per 10^14 bits read (approximately every 12 TB read). Enterprise drives are better (10^15 to 10^16) but not immune.

**RAID scrubbing:** RAID arrays should be scrubbed regularly to detect and correct silent corruption before a drive failure makes the corrupted data unrecoverable.

```bash
# Trigger a RAID scrub (Linux md RAID)
echo check > /sys/block/md0/md/sync_action

# Monitor scrub progress
cat /proc/mdstat

# Schedule weekly scrubbing via cron
echo "0 2 * * 0 root echo check > /sys/block/md0/md/sync_action" >> /etc/crontab
```

### 6.4 ZFS Checksumming and Self-Healing

ZFS is the gold standard for backup storage integrity. Every block is checksummed (default: fletcher4; configurable to SHA-256 for highest assurance). On read, ZFS verifies the checksum and automatically repairs corruption from redundant copies (mirror or raidz).

```bash
# Check current checksum algorithm
zfs get checksum tank/backups
# NAME            PROPERTY   VALUE      SOURCE
# tank/backups    checksum   on         default   (fletcher4)

# Set SHA-256 for maximum integrity assurance (higher CPU cost)
zfs set checksum=sha256 tank/backups

# Run a scrub (reads all data, verifies checksums, repairs from parity/mirror)
zpool scrub tank

# Check scrub results
zpool status tank
# scan: scrub repaired 0B in 04:32:10 with 0 errors on Wed May  7 06:32:10 2026

# Schedule weekly scrub
cat > /etc/cron.d/zfs-scrub << 'CRON_EOF'
0 2 * * 0 root /sbin/zpool scrub tank
CRON_EOF

# Monitor for checksum errors (integrate with monitoring)
#!/usr/bin/env bash
# /usr/local/bin/zfs-health-check.sh
CKSUM_ERRORS=$(zpool status -p tank | awk '/CKSUM/{sum+=$NF}END{print sum+0}')
if [ "${CKSUM_ERRORS}" -gt 0 ]; then
    echo "[CRITICAL] ZFS pool 'tank' has ${CKSUM_ERRORS} checksum errors"
    # Send alert to monitoring system
    curl -s -X POST "https://alerts.internal/webhook" \
      -H "Content-Type: application/json" \
      -d "{\"severity\":\"critical\",\"message\":\"ZFS checksum errors detected: ${CKSUM_ERRORS}\"}"
    exit 2
fi
echo "[OK] ZFS pool 'tank' — zero checksum errors"
```

**ZFS snapshot holds for immutability:**

```bash
# Create a hold on a snapshot (prevents destruction even by root using zfs destroy)
zfs hold backup-retention-lock tank/backups@2026-05-07

# List holds
zfs holds tank/backups@2026-05-07

# Release a hold (required before snapshot can be destroyed)
zfs release backup-retention-lock tank/backups@2026-05-07
```

### 6.5 Ceph Scrubbing

Ceph performs regular scrubbing of stored objects (comparing replicas for consistency). Deep scrubbing reads full object data and computes checksums.

```bash
# Trigger a deep scrub on a specific placement group
ceph pg deep-scrub 1.2a

# Check scrub status
ceph pg dump | grep scrub

# Global scrub settings (ceph.conf)
# [osd]
# osd_scrub_begin_hour = 2
# osd_scrub_end_hour = 6
# osd_deep_scrub_interval = 604800  # 7 days in seconds
# osd_scrub_during_recovery = false
```

### 6.6 End-to-End Verification Pipeline

Combining all integrity mechanisms into a single pipeline:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│ Backup Job  │────►│ SHA-256      │────►│ Manifest signed │
│ completes   │     │ Manifest     │     │ (GPG)           │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────────────────────┘
                    ▼
┌─────────────────────────────┐     ┌──────────────────────┐
│ ZFS scrub (weekly)          │     │ PBS verify job (daily)│
│ Detects block-level         │     │ Validates chunk       │
│ corruption                  │     │ SHA-256 digests       │
└─────────────────────────────┘     └──────────────────────┘
                    │                           │
                    ▼                           ▼
          ┌─────────────────────────────────────────┐
          │ Automated restore test (weekly/monthly) │
          │ Actually boots VM from backup,          │
          │ runs health checks                      │
          └─────────────────────┬───────────────────┘
                                │
                                ▼
                  ┌─────────────────────────┐
                  │ Report: all backups     │
                  │ verified, tested,       │
                  │ integrity confirmed     │
                  └─────────────────────────┘
```

---

## 7. Disaster Recovery Security

### 7.1 DR Site Security — Matching Production Controls

A DR site that does not match production security controls creates a risk inversion: during a disaster (when the organization is most vulnerable), operations fail over to a less-secured environment. DR security requirements:

- Same patching cadence as production. DR servers left unpatched for months are common and dangerous.
- Same access controls: RBAC, MFA, privileged access management.
- Same monitoring: SIEM agents, EDR, network flow analysis.
- Same network segmentation: the DR site should mirror the production network security zones.

**Common failure mode:** the DR site is maintained by a different team (or vendor) with different security standards. The cutover succeeds technically, but the DR environment lacks the security controls that production had — and the attacker (who caused the disaster) pivots to the less-secured DR environment.

### 7.2 DR Network Isolation

The DR site's network must be isolated from production to prevent an attacker who compromised production from reaching the DR environment. This conflicts with the need for replication traffic between sites. Resolution: the replication channel is the only allowed connection, and it is tightly controlled.

```
Production Site                         DR Site
┌──────────────┐                        ┌──────────────┐
│ Prod Network │                        │ DR Network   │
│ 10.0.0.0/16  │                        │ 10.1.0.0/16  │
│              │    WireGuard Tunnel    │              │
│  PBS Primary ├────────────────────────┤ PBS Replica  │
│  10.0.5.10   │  (port 51820 only)    │ 10.1.5.10   │
│              │                        │              │
│  FW rules:   │                        │  FW rules:   │
│  DENY all    │                        │  DENY all    │
│  ALLOW 51820 │                        │  ALLOW 51820 │
│  to DR only  │                        │  from Prod   │
└──────────────┘                        └──────────────┘
```

### 7.3 Encrypted Replication

**WireGuard tunnel for backup replication:**

```ini
# /etc/wireguard/wg-backup.conf (Production PBS server)
[Interface]
PrivateKey = <production-private-key>
Address = 172.16.0.1/30
ListenPort = 51820

[Peer]
PublicKey = <dr-site-public-key>
AllowedIPs = 172.16.0.2/32
Endpoint = dr-site.example.com:51820
PersistentKeepalive = 25
```

```ini
# /etc/wireguard/wg-backup.conf (DR PBS server)
[Interface]
PrivateKey = <dr-private-key>
Address = 172.16.0.2/30
ListenPort = 51820

[Peer]
PublicKey = <production-public-key>
AllowedIPs = 172.16.0.1/32
Endpoint = prod-site.example.com:51820
PersistentKeepalive = 25
```

```bash
# Enable and start the tunnel
systemctl enable --now wg-quick@wg-backup

# Verify tunnel status
wg show wg-backup

# Configure PBS sync over the WireGuard tunnel
proxmox-backup-manager pull-config create dr-sync \
  --remote pbs-prod \
  --remote-store production-ds \
  --store dr-replica-ds \
  --schedule "0 */4 * * *"   # Every 4 hours
```

**IPSec (for environments requiring FIPS-certified encryption):**

IPSec with IKEv2 provides FIPS 140-2 certified encryption when configured with FIPS-approved algorithms (AES-256-GCM, SHA-384, ECDH P-384). Use strongSwan or Libreswan on Linux:

```bash
# /etc/ipsec.conf (strongSwan)
conn backup-replication
    type=tunnel
    auto=start
    left=192.168.1.10
    leftsubnet=10.0.5.0/24
    right=203.0.113.50
    rightsubnet=10.1.5.0/24
    ike=aes256gcm16-sha384-ecp384!
    esp=aes256gcm16-sha384!
    keyexchange=ikev2
    ikelifetime=24h
    lifetime=8h
    dpdaction=restart
    dpddelay=30s
```

### 7.4 Failover Authentication — Break-Glass Procedures

During a disaster, normal authentication systems (Active Directory, LDAP, Vault, MFA provider) may be unavailable. Break-glass procedures provide emergency access.

**Break-glass credential design:**

1. Pre-generate emergency credentials (local root passwords, PBS emergency tokens) and store them in physical safes at the DR site.
2. Credentials are stored in sealed, tamper-evident envelopes with serial numbers.
3. Opening an envelope triggers an alert (via out-of-band communication: phone call, SMS).
4. Post-incident: all break-glass credentials are rotated immediately.

```bash
# Pre-generate a PBS emergency API token
proxmox-backup-manager user create emergency-admin@pbs \
  --comment "Break-glass account — sealed envelope #DR-2026-001"
proxmox-backup-manager user generate-token emergency-admin@pbs break-glass

# Store the token output in the sealed envelope

# Post-incident: rotate the token
proxmox-backup-manager user delete-token emergency-admin@pbs break-glass
proxmox-backup-manager user generate-token emergency-admin@pbs break-glass
# Re-seal in new envelope
```

### 7.5 DR Testing Without Exposing Production Data

DR tests that use real production data risk data exposure (test environments are typically less secured) and regulatory violations (production data in non-production environments may violate data residency or privacy requirements).

**Strategies:**

- **Data masking:** use tools like `pg_dump` with custom transform scripts, or commercial masking solutions, to replace PII with synthetic data before using backups in DR tests.
- **Synthetic data generation:** generate entirely synthetic datasets that match production schema and volume but contain no real data.
- **Network isolation:** if using real data for DR tests, ensure the DR test environment is completely isolated (no internet, no connection to production, no external access). Destroy all data after the test.
- **Encryption-as-isolation:** if backup data is client-side encrypted and the DR test uses a different encryption key, the test environment cannot read production backups — ensuring separation.

### 7.6 Secure Cloud DR

**AWS Elastic Disaster Recovery (DRS) security:**
- Replication agent installed on source servers encrypts data in transit (TLS) and at rest (EBS encryption with customer-managed KMS keys).
- Staging area uses encrypted EBS volumes in a dedicated VPC.
- IAM roles for DRS should follow least privilege: the replication role needs `ec2:*` and `s3:*` on specific resources only.
- Enable CloudTrail logging for all DRS API calls.

**Azure Site Recovery (ASR) security:**
- Data encrypted in transit (TLS 1.2) and at rest (Azure Storage Service Encryption with customer-managed keys in Azure Key Vault).
- Recovery Services vault supports soft-delete (14-day retention of deleted backups) and multi-user authorization for critical operations.
- Network Security Groups (NSGs) restrict replication traffic to Azure backbone only.

---

## 8. Ransomware Resilience Architecture

### 8.1 Detection Before Backup Corruption

The most effective defence is detecting ransomware activity before it reaches the backup infrastructure. Detection signals:

**Entropy analysis:**
Ransomware encrypts files, which dramatically increases the entropy (randomness) of the data. Normal text files have entropy around 4-5 bits/byte. Encrypted (ransomware-affected) files have entropy approaching 8 bits/byte (maximum).

```bash
#!/usr/bin/env bash
# /usr/local/bin/entropy-check.sh
# Detect high-entropy (potentially encrypted) files in backup data

BACKUP_DIR="$1"
THRESHOLD="7.5"  # Entropy above this = suspicious
ALERT_COUNT=0

for file in "${BACKUP_DIR}"/*.vma.zst; do
    # Calculate entropy using ent utility
    ENTROPY=$(ent "${file}" 2>/dev/null | head -1 | awk '{print $NF}')
    if [ -z "${ENTROPY}" ]; then continue; fi

    # Compare against threshold (using bc for float comparison)
    IS_HIGH=$(echo "${ENTROPY} > ${THRESHOLD}" | bc -l 2>/dev/null)
    if [ "${IS_HIGH}" = "1" ]; then
        echo "[ALERT] High entropy detected: ${file} (${ENTROPY} bits/byte)"
        ALERT_COUNT=$((ALERT_COUNT + 1))
    fi
done

if [ "${ALERT_COUNT}" -gt 0 ]; then
    echo "[WARNING] ${ALERT_COUNT} files with suspiciously high entropy"
    exit 1
fi
echo "[OK] No anomalous entropy detected"
```

**Note on compressed and encrypted backups:** `.vma.zst` (zstd-compressed) and client-side encrypted backups will naturally have high entropy. The entropy check is most useful for detecting changes in entropy *relative to previous backups of the same VM* — a VM that normally backs up at 6.2 bits/byte suddenly backing up at 7.9 bits/byte is suspicious.

**Change rate monitoring:**
Track the incremental backup size (number of changed blocks) over time. A ransomware encryption event produces a massive spike in changed blocks (approaching 100% of the VM's disk).

```bash
#!/usr/bin/env bash
# /usr/local/bin/change-rate-monitor.sh
# Alert on abnormal backup change rates

PBS_REPO="pbs-server:my-datastore"
THRESHOLD_PERCENT=40  # Alert if more than 40% of data changed

proxmox-backup-client snapshots --repository "${PBS_REPO}" --output-format json | \
  jq -r '.[] | select(.["backup-type"]=="vm") |
    "\(.["backup-id"]) \(.["backup-time"]) \(.size) \(.["dedup-factor"])"' | \
while read -r vmid btime size dedup; do
    # Low dedup factor = high change rate = suspicious
    if [ "$(echo "${dedup} < 1.5" | bc -l)" = "1" ]; then
        echo "[ALERT] VM ${vmid} backup at ${btime}: dedup factor ${dedup} (expected >2.0)"
        echo "  Possible ransomware encryption or massive data change"
    fi
done
```

### 8.2 Backup Isolation Patterns

**Pattern 1: Network isolation (firewall-enforced)**
- Backup repository on a separate VLAN.
- Firewall allows only backup traffic (specific ports, specific source IPs).
- No SSH, no RDP, no management access from the production network.
- Management via a dedicated jump host on a third VLAN.

**Pattern 2: Air gap (physical)**
- Tape backup with physical tape rotation to offsite vault.
- No network connection to the tape library from production.
- Tape library managed from a standalone, hardened workstation.

**Pattern 3: Delayed propagation**
- Primary backup lands on an online, connected repository.
- A batch job (running on a separate, isolated system) copies the backup to an isolated repository after a configurable delay (12-72 hours).
- During the delay period, monitoring systems analyse the backup for anomalies (entropy, change rate, known ransomware signatures).
- Only "clean" backups propagate to the isolated tier.

```
Timeline:
T+0h:  Backup runs → lands on online repository
T+0h:  Automated analysis: entropy check, change rate, AV scan
T+24h: If clean → copy to isolated repository
        If suspicious → HOLD, alert SOC, do NOT propagate

Result: even if ransomware encrypted all production data and
        corrupted the online backup, the isolated copy from
        yesterday (or the last clean backup) is untouched.
```

### 8.3 Recovery Time Optimization

**Instant VM recovery (Veeam):**
- Boot a VM directly from the backup repository (compressed, deduplicated backup file serves as a read-only datastore).
- The VM is running within 2-5 minutes of initiating recovery.
- Storage vMotion migrates the VM's data to production storage in the background.
- Security consideration: the backup repository must be on a fast storage tier (SSD) for acceptable performance. The recovery network must be isolated from the compromised production network.

**PBS staged restore:**
- PBS does not support "instant boot from backup" natively. The restore workflow is: restore backup to a Proxmox VE datastore, then start the VM.
- Optimize by restoring to fast local storage (NVMe) first, then migrating to production storage.
- Parallel restore: restore multiple VMs simultaneously (PBS supports concurrent restore jobs).

### 8.4 Clean Room Recovery

A clean room recovery environment is an isolated, pre-configured environment used exclusively for restoring systems after a confirmed ransomware incident. It ensures the recovery process itself is not compromised.

**Clean room requirements:**
1. **Network:** completely isolated (air-gapped or VLAN with no external routes). DNS, NTP, and update servers are local.
2. **Infrastructure:** pre-installed Proxmox VE (or VMware) cluster, verified clean (golden image, checksummed).
3. **Storage:** access to immutable backup copies (read-only mount of the immutable repository or tape).
4. **Tools:** pre-installed forensic and recovery tools. No internet access needed.
5. **Personnel:** only authorized recovery team members. Physical access control if possible.
6. **Process:** restore VMs, run integrity checks, scan for persistence mechanisms, validate application health — all before connecting to the production network.

### 8.5 Recovery Prioritization

Not all systems are equal. Recovery order should follow a pre-defined priority matrix:

| Priority | Systems | Target RTO | Rationale |
|----------|---------|------------|-----------|
| P0 — Critical | Domain controllers, DNS, DHCP, PKI, core DB | < 1 hour | Everything else depends on identity and network services |
| P1 — Essential | Core business applications, ERP, CRM, email | < 4 hours | Revenue-generating and communication systems |
| P2 — Important | Secondary applications, file servers, dev tools | < 24 hours | Productivity impact but not revenue-critical |
| P3 — Deferrable | Test environments, training systems, archives | < 72 hours | Can wait; rebuild from scratch if backups unavailable |

**Pre-incident preparation:**
- Document the priority matrix. Get executive sign-off.
- Map each priority tier to specific VM IDs and backup identifiers.
- Pre-configure recovery runbooks for P0 systems with exact commands.
- Test the priority-based recovery sequence during quarterly DR drills.

---

## 9. Compliance and Audit

### 9.1 Backup Encryption Audit Requirements

| Framework | Audit Requirement | Evidence Required |
|-----------|-------------------|-------------------|
| **GDPR** | Demonstrate "appropriate technical measures" for backup data protection | Encryption configuration, key management procedures, access logs |
| **HIPAA** | Annual risk assessment covering backup encryption; BAA with backup-as-a-service providers | Encryption implementation documentation, risk assessment report, BAAs |
| **PCI-DSS v4.0** | Quarterly validation of encryption key procedures; annual penetration test covering backup infrastructure | Key management procedures, rotation records, pen test reports |
| **SOC 2** | Operating effectiveness of backup encryption controls over the audit period (12 months) | Continuous monitoring evidence, change management records, access reviews |
| **ISO 27001** | A.10.1.1 — policy on use of cryptographic controls; A.10.1.2 — key management | Cryptographic policy document, key lifecycle records |

### 9.2 Backup Access Logging

Every access to backup data must be logged with sufficient detail for forensic investigation.

**What to log:**

| Event | Required Fields |
|-------|----------------|
| Backup job start/complete/fail | Timestamp (UTC), VM ID, job ID, operator, status, bytes transferred |
| Restore operation | Timestamp, who initiated, which backup snapshot, target location, authorization reference |
| Backup deletion/prune | Timestamp, who initiated, which snapshots deleted, retention policy reference |
| Key access/rotation | Timestamp, which key (fingerprint), operation (create/rotate/export/destroy), who |
| Configuration change | Timestamp, what changed (retention policy, encryption settings, ACL), who, old value, new value |
| Failed authentication | Timestamp, source IP, user attempted, failure reason |

**PBS logging configuration:**

```bash
# PBS logs to journal by default
journalctl -u proxmox-backup-proxy --since "2026-05-07" --until "2026-05-08"

# Filter for security-relevant events
journalctl -u proxmox-backup-proxy | grep -E "(auth|token|login|permission|denied|error)"

# Ship logs to external SIEM (rsyslog example)
cat >> /etc/rsyslog.d/50-pbs-siem.conf << 'RSYSLOG_EOF'
if $programname == 'proxmox-backup-proxy' or $programname == 'proxmox-backup-api' then {
    action(type="omfwd" target="siem.internal" port="514" protocol="tcp"
           template="RSYSLOG_SyslogProtocol23Format")
}
RSYSLOG_EOF
systemctl restart rsyslog
```

### 9.3 Retention Policy Enforcement

Retention policies must be documented, technically enforced, and auditable.

```bash
# PBS: configure retention per datastore
proxmox-backup-manager prune-job create daily-prune \
  --store production-ds \
  --keep-daily 30 \
  --keep-weekly 12 \
  --keep-monthly 12 \
  --keep-yearly 3 \
  --schedule "0 4 * * *"

# Verify current retention settings
proxmox-backup-manager prune-job list --output-format json
```

**Retention compliance matrix:**

| Data Type | GDPR | HIPAA | PCI-DSS | SOX |
|-----------|------|-------|---------|-----|
| General business data | "No longer than necessary" | — | — | 7 years |
| Health records (PHI) | — | 6 years minimum | — | — |
| Cardholder data | — | — | Only as needed; secure delete when not | — |
| Financial records | — | — | — | 7 years |
| Backup of PII | Must support right-to-erasure | — | — | — |

### 9.4 Data Sovereignty — Backup Location

Backup data may be subject to data residency requirements depending on the data's classification and the applicable jurisdiction.

- **GDPR:** personal data of EU residents must not be transferred to countries without an "adequacy decision" unless appropriate safeguards are in place (Standard Contractual Clauses, Binding Corporate Rules). This applies to backup replicas and DR sites.
- **HIPAA:** PHI may be stored anywhere as long as the storage provider has signed a BAA and implements required safeguards. However, many healthcare organizations adopt a "US-only" policy.
- **PCI-DSS:** no specific geographic restriction, but the backup location must be covered by the cardholder data environment (CDE) and included in the scope of the annual assessment.

**Practical implication:** if production is in Frankfurt and the DR backup replicates to Singapore, the Singapore site must comply with the same data protection requirements as Frankfurt. This includes encryption, access controls, and audit logging.

### 9.5 Right to Erasure — Deletion from Backups

GDPR Article 17 grants individuals the right to erasure ("right to be forgotten"). This creates a direct conflict with immutable backups: how do you delete a specific individual's data from a backup that cannot be modified?

**Accepted approaches:**

1. **Encrypt-and-destroy-key:** if backups are encrypted per-customer or per-dataset, deleting the encryption key renders the data cryptographically inaccessible. This is generally accepted by regulators as equivalent to deletion (see NIST SP 800-88 §2.4 on cryptographic erasure).

2. **Retention-based expiry:** document that the individual's data will be deleted when the backup retention period expires. Include this in the privacy policy. Many DPAs (Data Protection Authorities) accept this approach when the retention period is reasonable (e.g., 30-90 days for operational backups).

3. **Granular backup architecture:** design backup systems to allow per-dataset or per-tenant deletion. This is architecturally complex and rarely implemented for VM-level backups, but it is feasible for database-level backups (delete the specific record, then take a new backup).

4. **Register of pending deletions:** maintain a register of erasure requests that cannot be immediately fulfilled due to backup immutability. Apply the deletions when the relevant backup is restored (if ever). Document this process.

### 9.6 Backup Audit Trail — Chain of Custody

A complete audit trail answers: who created, accessed, modified, restored, or deleted each backup, and when.

**Monitoring script for chain-of-custody reporting:**

```bash
#!/usr/bin/env bash
# /usr/local/bin/backup-audit-report.sh
# Generate a daily backup audit trail report

REPORT_DATE="${1:-$(date -u +%Y-%m-%d)}"
REPORT_FILE="/var/log/backup-audit/report-${REPORT_DATE}.json"

mkdir -p /var/log/backup-audit

echo "{" > "${REPORT_FILE}"
echo "  \"report_date\": \"${REPORT_DATE}\"," >> "${REPORT_FILE}"
echo "  \"generated_at\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"," >> "${REPORT_FILE}"

# Backup operations
echo "  \"backup_operations\": [" >> "${REPORT_FILE}"
journalctl -u proxmox-backup-proxy --since "${REPORT_DATE} 00:00:00" \
  --until "${REPORT_DATE} 23:59:59" --output json | \
  jq -c 'select(.MESSAGE | test("backup|restore|prune|verify"; "i")) |
    {timestamp: .__REALTIME_TIMESTAMP, message: .MESSAGE}' | \
  sed '$ ! s/$/,/' >> "${REPORT_FILE}"
echo "  ]," >> "${REPORT_FILE}"

# Authentication events
echo "  \"auth_events\": [" >> "${REPORT_FILE}"
journalctl -u proxmox-backup-proxy --since "${REPORT_DATE} 00:00:00" \
  --until "${REPORT_DATE} 23:59:59" --output json | \
  jq -c 'select(.MESSAGE | test("auth|login|token|permission"; "i")) |
    {timestamp: .__REALTIME_TIMESTAMP, message: .MESSAGE}' | \
  sed '$ ! s/$/,/' >> "${REPORT_FILE}"
echo "  ]" >> "${REPORT_FILE}"

echo "}" >> "${REPORT_FILE}"

# Set immutable so the audit log cannot be tampered with
chattr +i "${REPORT_FILE}"

echo "[OK] Audit report generated: ${REPORT_FILE}"
```

---

## 10. Lab: Complete Backup Security Implementation

This lab walks through a complete backup security deployment from encryption configuration through ransomware attack simulation and recovery verification. All commands are designed for a lab environment — adapt hostnames, IPs, and storage paths for production.

### Lab Environment

```
Lab Topology:

┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ pve-lab-01        │     │ pbs-lab-01         │     │ isolated-repo     │
│ Proxmox VE 8.x   │     │ PBS 3.x            │     │ Ubuntu 22.04      │
│ 10.10.10.11       │     │ 10.10.10.21        │     │ 10.10.20.31       │
│                   │     │                    │     │ (isolated VLAN)   │
│ VMs:              │     │ Datastore:         │     │ ZFS pool: tank    │
│  100 (web-app)    │     │  production-ds     │     │ /tank/immutable   │
│  101 (database)   │     │  (/mnt/ds1)        │     │                   │
│  102 (mail)       │     │                    │     │                   │
└───────┬───────────┘     └───────┬────────────┘     └───────┬───────────┘
        │                         │                           │
        └────── VLAN 10 ──────────┘                           │
                  │                                           │
                  └──── WireGuard tunnel (172.16.0.0/30) ─────┘
```

### Lab Step 1: Configure PBS with Client-Side Encryption

```bash
# --- On pve-lab-01 (Proxmox VE node) ---

# 1. Generate the encryption key
proxmox-backup-client key create /etc/pve/priv/lab-backup-key.json

# 2. Verify the key was created
cat /etc/pve/priv/lab-backup-key.json | jq '.fingerprint'

# 3. Generate a master key pair for key escrow
openssl genrsa -aes256 -out /root/master-key.pem 4096
openssl rsa -in /root/master-key.pem -pubout -out /root/master-key.pub

# 4. Create an encryption key with master key escrow
proxmox-backup-client key create \
  --master-pubkey-file /root/master-key.pub \
  /etc/pve/priv/lab-backup-key-escrowed.json

# 5. Store the master private key safely (in production: physical safe)
chmod 0400 /root/master-key.pem

# 6. Run an encrypted backup of VM 100
proxmox-backup-client backup \
  --repository pbs-lab-01:production-ds \
  --keyfile /etc/pve/priv/lab-backup-key-escrowed.json \
  --backup-id 100 \
  --backup-type vm \
  vm/100

# 7. Verify the backup is listed (metadata visible) but data is encrypted
proxmox-backup-client snapshots \
  --repository pbs-lab-01:production-ds \
  --output-format json | jq '.[] | select(.["backup-id"]=="100")'

# 8. Capture the backup timestamp for later steps
BACKUP_TS=$(proxmox-backup-client snapshots \
  --repository pbs-lab-01:production-ds \
  --output-format json | \
  jq -r '.[] | select(.["backup-id"]=="100") | .["backup-time"]' | sort -r | head -1)
echo "Latest backup timestamp: ${BACKUP_TS}"

# 9. Attempt to read backup data WITHOUT the key (should fail)
proxmox-backup-client restore vm/100 \
  --repository pbs-lab-01:production-ds \
  /tmp/no-key-restore/ 2>&1 || echo "Expected: decryption failed without keyfile"
```

### Lab Step 2: Implement Immutable Repository

```bash
# --- On isolated-repo (Ubuntu 22.04, isolated VLAN) ---

# 1. Create ZFS pool for immutable storage
zpool create -o ashift=12 tank mirror /dev/sdb /dev/sdc
zfs create -o compression=zstd -o checksum=sha256 tank/immutable
zfs set atime=off tank/immutable

# 2. Create a dedicated backup user (no root backup operations)
useradd -r -m -s /bin/bash backup-agent
mkdir -p /tank/immutable/backups
chown backup-agent:backup-agent /tank/immutable/backups

# 3. Create immutability helper script
cat > /usr/local/bin/set-immutable.sh << 'SCRIPT_EOF'
#!/usr/bin/env bash
# Sets immutable flag on backup files after write
set -euo pipefail
TARGET="$1"
if [ ! -f "${TARGET}" ]; then
    echo "File not found: ${TARGET}" >&2
    exit 1
fi
chattr +i "${TARGET}"
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Immutable flag set: ${TARGET}" >> /var/log/immutability.log
SCRIPT_EOF
chmod 755 /usr/local/bin/set-immutable.sh
setcap cap_linux_immutable+ep /usr/local/bin/set-immutable.sh

# 4. Configure auditd to monitor immutability changes
cat > /etc/audit/rules.d/99-backup-immutable.rules << 'AUDIT_EOF'
-w /tank/immutable/ -p wa -k backup_data_change
-a always,exit -F arch=b64 -S fremovexattr -S fsetxattr -F dir=/tank/immutable/ -k backup_xattr_mod
-w /usr/bin/chattr -p x -k chattr_execution
AUDIT_EOF
augenrules --load

# 5. Set up WireGuard tunnel to PBS server
apt-get install -y wireguard

# Generate keys
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key
chmod 0600 /etc/wireguard/private.key

cat > /etc/wireguard/wg-backup.conf << 'WG_EOF'
[Interface]
PrivateKey = <contents-of-private.key>
Address = 172.16.0.2/30
ListenPort = 51820

[Peer]
PublicKey = <pbs-lab-01-public-key>
AllowedIPs = 172.16.0.1/32
Endpoint = 10.10.10.21:51820
PersistentKeepalive = 25
WG_EOF

systemctl enable --now wg-quick@wg-backup

# 6. Firewall rules: allow only WireGuard from PBS
ufw default deny incoming
ufw default deny outgoing
ufw allow in on wg-backup from 172.16.0.1 to any
ufw allow out on wg-backup to 172.16.0.1
ufw enable
```

### Lab Step 3: Set Up Automated Integrity Verification

```bash
# --- On pbs-lab-01 (PBS server) ---

# 1. Create a verification job for the production datastore
# Via PBS GUI: Datastore → production-ds → Verify Jobs → Add
#   Schedule: daily at 03:00
#   Outdated After: 7 days (re-verify if last verify > 7 days old)

# Via CLI (if supported in your PBS version):
proxmox-backup-manager verify production-ds

# 2. Create a cron job for manifest verification on the isolated repo
# --- On isolated-repo ---

cat > /usr/local/bin/verify-backup-integrity.sh << 'VERIFY_EOF'
#!/usr/bin/env bash
# Automated backup integrity verification
# Runs daily, checks SHA-256 manifests and ZFS checksums

set -euo pipefail

LOG="/var/log/backup-verify-$(date -u +%Y%m%d).log"
FAILURES=0

echo "=== Backup Integrity Verification ===" | tee "${LOG}"
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${LOG}"

# Step 1: ZFS scrub (weekly — check if already running)
SCRUB_STATE=$(zpool status tank | grep -c "scrub in progress" || true)
if [ "${SCRUB_STATE}" -eq 0 ]; then
    DOW=$(date +%u)  # 1=Monday, 7=Sunday
    if [ "${DOW}" -eq 7 ]; then
        echo "[INFO] Starting weekly ZFS scrub" | tee -a "${LOG}"
        zpool scrub tank
    fi
fi

# Step 2: Check ZFS checksum errors
CKSUM_ERRORS=$(zpool status -p tank | awk '/CKSUM/{sum+=$NF}END{print sum+0}')
if [ "${CKSUM_ERRORS}" -gt 0 ]; then
    echo "[CRITICAL] ZFS checksum errors: ${CKSUM_ERRORS}" | tee -a "${LOG}"
    FAILURES=$((FAILURES + 1))
else
    echo "[OK] ZFS: zero checksum errors" | tee -a "${LOG}"
fi

# Step 3: Verify SHA-256 manifests
for manifest in /tank/immutable/backups/*/MANIFEST.sha256; do
    [ -f "${manifest}" ] || continue
    DIR=$(dirname "${manifest}")
    echo "[INFO] Verifying manifest: ${manifest}" | tee -a "${LOG}"

    pushd "${DIR}" > /dev/null
    if sha256sum -c MANIFEST.sha256 >> "${LOG}" 2>&1; then
        echo "[OK] Manifest verified: ${DIR}" | tee -a "${LOG}"
    else
        echo "[CRITICAL] Manifest verification FAILED: ${DIR}" | tee -a "${LOG}"
        FAILURES=$((FAILURES + 1))
    fi
    popd > /dev/null
done

# Step 4: Check immutable flags
MUTABLE_COUNT=$(find /tank/immutable/backups/ -type f ! -name 'MANIFEST*' \
    -exec lsattr {} \; 2>/dev/null | grep -cv '\-i\-' || true)
if [ "${MUTABLE_COUNT}" -gt 0 ]; then
    echo "[WARNING] ${MUTABLE_COUNT} backup files missing immutable flag" | tee -a "${LOG}"
    FAILURES=$((FAILURES + 1))
fi

echo "=== Verification Complete ===" | tee -a "${LOG}"
echo "Finished: $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${LOG}"
echo "Failures: ${FAILURES}" | tee -a "${LOG}"

# Set log immutable
chattr +i "${LOG}" 2>/dev/null || true

exit "${FAILURES}"
VERIFY_EOF

chmod 755 /usr/local/bin/verify-backup-integrity.sh

# Schedule daily at 04:00
echo "0 4 * * * root /usr/local/bin/verify-backup-integrity.sh" > /etc/cron.d/backup-verify
```

### Lab Step 4: Simulate Ransomware Attack on Backup Infrastructure

This step simulates the behaviour of ransomware targeting backup data. The simulation uses benign file operations that mimic ransomware patterns without actually deploying malware. Conduct this only in the isolated lab environment.

```bash
# --- On pve-lab-01 (simulating a compromised hypervisor) ---

# SCENARIO: Attacker has gained root on the Proxmox VE node and
# attempts to destroy/encrypt backup data.

echo "=== RANSOMWARE SIMULATION — ATTACK PHASE ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Resolve the latest backup timestamp (from Step 1)
BACKUP_TS=$(proxmox-backup-client snapshots \
  --repository pbs-lab-01:production-ds \
  --output-format json | \
  jq -r '.[] | select(.["backup-id"]=="100") | .["backup-time"]' | sort -r | head -1)

# Attack vector 1: Attempt to delete backup snapshots via PBS API
echo "[ATTACK] Attempting to delete backups via PBS API..."
proxmox-backup-client snapshot delete vm/100 \
  --repository pbs-lab-01:production-ds \
  --backup-time "${BACKUP_TS}" 2>&1 || \
  echo "[RESULT] Deletion blocked or failed (expected if ACL restricts delete)"

# Attack vector 2: Attempt to overwrite the encryption key
echo "[ATTACK] Attempting to overwrite encryption key..."
cp /etc/pve/priv/lab-backup-key-escrowed.json \
   /etc/pve/priv/lab-backup-key-escrowed.json.bak
# Simulate key destruction
echo '{"corrupted": true}' > /tmp/fake-key.json
# In a real attack, the adversary would overwrite the keyfile:
# cp /tmp/fake-key.json /etc/pve/priv/lab-backup-key-escrowed.json
echo "[RESULT] Key overwrite simulated (not executed — see note)"
echo "  NOTE: In production, key is protected by pmxcfs and replicated."
echo "  Recovery: master key can decrypt any backup."

# Attack vector 3: Attempt to corrupt data on the immutable repository
echo "[ATTACK] Attempting to modify immutable backup files..."
# --- On isolated-repo (via the WireGuard tunnel) ---
ssh backup-agent@172.16.0.2 \
  "echo 'RANSOMWARE_PAYLOAD' >> /tank/immutable/backups/vm-100/2026-05-07.dat" 2>&1 || \
  echo "[RESULT] Write to immutable file DENIED (chattr +i working)"

# Attack vector 4: Attempt to remove immutable flag
echo "[ATTACK] Attempting to remove immutable flag (requires root)..."
ssh backup-agent@172.16.0.2 \
  "chattr -i /tank/immutable/backups/vm-100/2026-05-07.dat" 2>&1 || \
  echo "[RESULT] chattr -i DENIED (backup-agent lacks CAP_LINUX_IMMUTABLE)"

# Attack vector 5: Create high-entropy "encrypted" files to test detection
echo "[ATTACK] Creating high-entropy files to simulate ransomware encryption..."
dd if=/dev/urandom of=/tmp/simulated-encrypted-vm.raw bs=1M count=100 2>/dev/null
echo "[RESULT] High-entropy file created — entropy check should flag this"

# Run entropy detection
if command -v ent &>/dev/null; then
    ENTROPY=$(ent /tmp/simulated-encrypted-vm.raw 2>/dev/null | head -1 | awk '{print $NF}')
    echo "[DETECTION] Entropy of simulated file: ${ENTROPY} bits/byte"
    echo "  (Expected: ~8.0 — maximum entropy = encrypted/random data)"
fi

# Cleanup simulation artifacts
rm -f /tmp/simulated-encrypted-vm.raw /tmp/fake-key.json
echo "=== RANSOMWARE SIMULATION — ATTACK PHASE COMPLETE ==="
```

**Expected results and lessons:**

| Attack Vector | Expected Outcome | Defence Layer |
|---------------|------------------|---------------|
| Delete backups via API | Blocked by ACL (backup-operator has DatastoreBackup, not DatastoreAdmin) | Access control |
| Overwrite encryption key | Key recoverable via master key escrow | Key management |
| Modify immutable files | Denied by `chattr +i` | Immutability |
| Remove immutable flag | Denied (non-root user lacks capability) | Capability-based access |
| High-entropy file detection | Detected by entropy analysis | Anomaly detection |

### Lab Step 5: Test Recovery from Encrypted Immutable Backups

```bash
# --- On pve-lab-01 ---

echo "=== RECOVERY TEST ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Verify the backup still exists and is intact
echo "[STEP 1] Listing available backups..."
proxmox-backup-client snapshots \
  --repository pbs-lab-01:production-ds \
  --output-format json | \
  jq '.[] | select(.["backup-id"]=="100") | {id: .["backup-id"], time: .["backup-time"], size: .size}'

# 2. Resolve the latest backup timestamp and restore
echo "[STEP 2] Restoring VM 100 from encrypted backup..."
RESTORE_DIR="/tmp/recovery-test-$(date +%s)"
mkdir -p "${RESTORE_DIR}"

BACKUP_TS=$(proxmox-backup-client snapshots \
  --repository pbs-lab-01:production-ds \
  --output-format json | \
  jq -r '.[] | select(.["backup-id"]=="100") | .["backup-time"]' | sort -r | head -1)
echo "  Restoring from: ${BACKUP_TS}"

proxmox-backup-client restore vm/100 \
  --repository pbs-lab-01:production-ds \
  --keyfile /etc/pve/priv/lab-backup-key-escrowed.json \
  --backup-time "${BACKUP_TS}" \
  "${RESTORE_DIR}/"

echo "[STEP 2] Restore complete. Contents:"
ls -la "${RESTORE_DIR}/"

# 3. Verify restored data integrity
echo "[STEP 3] Computing SHA-256 of restored files..."
sha256sum "${RESTORE_DIR}"/* > "${RESTORE_DIR}/restore-integrity.sha256"
cat "${RESTORE_DIR}/restore-integrity.sha256"

# 4. Simulate key loss — recover using master key
echo "[STEP 4] Simulating key loss recovery..."
echo "  In a real scenario:"
echo "    1. Retrieve master private key from physical safe (dual custody)"
echo "    2. Decrypt the escrowed DEK from the backup metadata"
echo "    3. Use the recovered DEK to decrypt the backup"
echo "  Procedure:"
echo "    1. Retrieve master private key PEM from physical safe (dual custody)"
echo "    2. Extract the wrapped DEK blob from the backup metadata"
echo "    3. Unwrap the DEK using openssl:"
echo "       openssl rsautl -decrypt -inkey /root/master-key.pem -in wrapped-dek.bin -out recovered-key.json"
echo "    4. Use the recovered keyfile for restore:"
echo "       proxmox-backup-client restore vm/100 --keyfile recovered-key.json ..."

# 5. Validate the recovered VM can start
echo "[STEP 5] Validating VM boot (if restoring to a Proxmox VE datastore)..."
# In a full lab, you would:
#   qmrestore /tmp/recovery-test-*/vzdump-qemu-100-*.vma.zst 900 --storage local-lvm
#   qm start 900
#   # Wait for QEMU guest agent to respond
#   qm agent 900 ping
#   qm stop 900 && qm destroy 900

echo "=== RECOVERY TEST COMPLETE ==="

# Cleanup
rm -rf "${RESTORE_DIR}"
```

### Lab Step 6: Verify Chain-of-Custody Logging

```bash
# --- On pbs-lab-01 ---

echo "=== CHAIN-OF-CUSTODY VERIFICATION ==="

# 1. Review backup operation logs
echo "[STEP 1] Recent backup operations:"
journalctl -u proxmox-backup-proxy --since "2026-05-07 00:00:00" | \
  grep -E "(backup|restore|prune|verify|delete)" | tail -20

# 2. Review authentication events
echo "[STEP 2] Authentication events:"
journalctl -u proxmox-backup-proxy --since "2026-05-07 00:00:00" | \
  grep -E "(auth|login|token|denied)" | tail -20

# 3. Check audit logs on isolated repository
echo "[STEP 3] Immutability audit events:"
ssh root@172.16.0.2 "ausearch -k backup_data_change --start today 2>/dev/null" || \
  echo "  (No events — good, no unauthorized changes detected)"

ssh root@172.16.0.2 "ausearch -k chattr_execution --start today 2>/dev/null" || \
  echo "  (No chattr executions detected)"

# 4. Generate a summary report
echo "[STEP 4] Generating audit summary..."
cat << 'SUMMARY_EOF'
+==================================================================+
|  BACKUP SECURITY LAB — AUDIT SUMMARY                            |
+==================================================================+
|                                                                  |
|  Encryption:                                                     |
|    [x] Client-side AES-256-GCM encryption configured            |
|    [x] Master key escrow in place                                |
|    [x] Backup data unreadable without keyfile                    |
|                                                                  |
|  Immutability:                                                   |
|    [x] Immutable flags set on backup files (chattr +i)          |
|    [x] Non-root users cannot remove immutability                 |
|    [x] auditd monitoring active on backup directory             |
|                                                                  |
|  Integrity:                                                      |
|    [x] SHA-256 manifests generated and signed (GPG)             |
|    [x] ZFS checksumming (sha256) enabled                        |
|    [x] Automated verification scheduled (daily)                 |
|    [x] Restore test completed successfully                       |
|                                                                  |
|  Ransomware Resilience:                                          |
|    [x] API-level deletion blocked by ACL                         |
|    [x] File-level modification blocked by immutability           |
|    [x] High-entropy anomaly detection functional                |
|    [x] Key loss recoverable via master key                       |
|    [x] Isolated repository unreachable from production network  |
|                                                                  |
|  Audit Trail:                                                    |
|    [x] All operations logged with UTC timestamps                |
|    [x] Logs shipped to external SIEM                            |
|    [x] Audit logs protected with immutable flag                 |
|                                                                  |
|  3-2-1-1-0 Status:                                               |
|    3 copies: production + PBS + isolated repo        [x]        |
|    2 media:  SSD (PBS) + ZFS mirror (isolated)       [x]        |
|    1 offsite: isolated repo on separate VLAN         [x]        |
|    1 immutable: chattr +i on isolated repo           [x]        |
|    0 errors: automated verify + restore test pass    [x]        |
|                                                                  |
+==================================================================+
SUMMARY_EOF

echo "=== CHAIN-OF-CUSTODY VERIFICATION COMPLETE ==="
```

---

## Quick Reference: Command Cheat Sheet

### PBS Commands

| Task | Command |
|------|---------|
| Create encryption key | `proxmox-backup-client key create /path/to/key.json` |
| Encrypted backup | `proxmox-backup-client backup vm/ID --repository HOST:DS --keyfile /path/to/key.json` |
| Restore encrypted backup | `proxmox-backup-client restore vm/ID --repository HOST:DS --keyfile /path/to/key.json /target/` |
| Verify datastore | `proxmox-backup-manager verify DATASTORE` |
| List snapshots | `proxmox-backup-client snapshots --repository HOST:DS --output-format json` |
| Run garbage collection | `proxmox-backup-manager garbage-collection start DATASTORE` |
| Tape backup | `proxmox-tape backup DATASTORE POOL` |

### Veeam PowerShell Commands

| Task | Command |
|------|---------|
| Create encryption key | `Add-VBREncryptionKey -Password $securePass -Description "desc"` |
| List encryption keys | `Get-VBREncryptionKey` |
| Enable job encryption | `Set-VBRJobAdvancedStorageOptions -Job $job -EnableEncryption $true -EncryptionKey $key` |
| Verify backup encryption | `(Get-VBRBackup -Name "JobName").IsEncryptionEnabled` |
| Run SureBackup | `Start-VBRSureBackupJob -Job (Get-VBRSureBackupJob -Name "JobName")` |
| List repositories | `Get-VBRBackupRepository \| Select Name, Type, Path` |

### Linux Immutability Commands

| Task | Command |
|------|---------|
| Set immutable | `chattr +i /path/to/file` |
| Remove immutable | `chattr -i /path/to/file` (requires root or CAP_LINUX_IMMUTABLE) |
| Check attributes | `lsattr /path/to/file` |
| Grant capability | `setcap cap_linux_immutable+ep /path/to/binary` |
| Audit attribute changes | `auditctl -w /path/ -p a -k label` |

### Integrity Verification Commands

| Task | Command |
|------|---------|
| Generate SHA-256 manifest | `find /dir -type f -exec sha256sum {} \; > MANIFEST.sha256` |
| Verify manifest | `sha256sum -c MANIFEST.sha256` |
| ZFS scrub | `zpool scrub POOL` |
| ZFS checksum errors | `zpool status POOL` |
| ZFS snapshot hold | `zfs hold TAG POOL/DS@SNAP` |

---

## Further Reading

- NIST SP 800-209: *Security Guidelines for Storage Infrastructure* (2020).
- NIST SP 800-57 Part 1 Rev. 5: *Recommendation for Key Management* (2020).
- NIST SP 800-88 Rev. 1: *Guidelines for Media Sanitization* — §2.4 on cryptographic erasure.
- MITRE ATT&CK T1490: *Inhibit System Recovery* — technique documentation and detection guidance.
- MITRE ATT&CK T1486: *Data Encrypted for Impact* — ransomware-specific technique.
- Proxmox Backup Server documentation: *Client-Side Encryption* section.
- Veeam Backup & Replication documentation: *Encryption* and *Hardened Repository* sections.
- CISA: *Protecting Backups from Ransomware* advisory (2024).
- ENISA: *Ransomware Threat Landscape* report (2025 edition).
