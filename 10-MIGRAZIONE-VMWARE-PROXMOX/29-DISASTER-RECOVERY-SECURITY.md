# Disaster Recovery Security — Secure DR Architecture, Failover Protection, and Recovery Integrity

> **Course module:** VMware to Proxmox VE Migration
> **Position in curriculum:** Phase 9 — Advanced Security · Module 29
> **Prerequisites:** Module 10 (HA cluster), Module 11 (backup and PBS), Module 12 (security and compliance), Module 19 (multi-site DR Proxmox — topology, replication, RTO/RPO), Module 20 (hypervisor security hardening), Module 22 (network segmentation); familiarity with BCP/DR lifecycle, PKI/TLS, WireGuard/IPSec, key management concepts, compliance frameworks (ISO 22301, PCI-DSS, HIPAA).
> **Learning objectives.** Upon completion the student will be able to:
> 1. Construct a threat model specific to DR infrastructure — identifying why attackers target backups, replication channels, and DR sites.
> 2. Design isolated DR network architectures with credential separation, encrypted replication, and hardware-rooted trust.
> 3. Secure VMware Site Recovery Manager (now VMware Live Site Recovery post-Broadcom) and vSphere Replication with encryption, authentication, and NSX-T cross-site policy consistency.
> 4. Harden Proxmox Backup Server remote sync, Ceph cross-site replication, ZFS send/receive over SSH, and WAN cluster links against interception and tampering.
> 5. Execute failover procedures with embedded security checks — credential readiness, firewall activation, split-brain mitigation.
> 6. Verify recovery integrity through hash verification, digital signatures, malware scanning, and clean-room restore workflows.
> 7. Conduct security-focused DR tests including penetration testing of DR procedures and tabletop exercises.
> 8. Secure cloud-based DR with AWS Elastic Disaster Recovery, Azure Site Recovery, and GCP patterns while maintaining compliance.
> 9. Satisfy DR compliance requirements across PCI-DSS v4.0, HIPAA, SOX, and ISO 22301:2019 with auditable evidence.
> 10. Implement a complete secure DR lab — encrypted replication, automated failover with security validation, ransomware recovery drill.
> **Estimated time:** Reading 150-200 min · Implementation 4-8 weeks · Quarterly DR security drill
> **Level:** Expert (Dreyfus 5); offensive security awareness required
> **Last updated:** 2026-05-07
> **Reference versions:** Proxmox VE 8.x; PBS 3.x; VMware vSphere 8.0 U3; VMware Live Site Recovery 9.x; NSX-T 4.x; Ceph Reef/Squid; ZFS 2.2/2.3; WireGuard 1.x; HashiCorp Vault 1.17+; AWS Elastic DR; Azure Site Recovery; ISO 22301:2019; PCI-DSS v4.0.

---

## Conceptual Map

```
+=================================================================+
|     Disaster Recovery Security: Defense Layers                   |
+=================================================================+
|                                                                 |
|  LAYER 1: THREAT MODEL                                          |
|    Backups as target, DR site lateral movement, insider risk     |
|                                                                 |
|  LAYER 2: SECURE DR ARCHITECTURE                                |
|    Isolated networks, credential separation, encrypted channels  |
|                                                                 |
|  LAYER 3: PLATFORM-SPECIFIC DR SECURITY                         |
|    VMware SRM/Replication + Proxmox PBS/Ceph/ZFS hardening       |
|                                                                 |
|  LAYER 4: FAILOVER SECURITY                                     |
|    Pre-flight checks, auth during emergency, split-brain         |
|                                                                 |
|  LAYER 5: RECOVERY INTEGRITY                                    |
|    Hash verification, signature checks, malware scan, clean room |
|                                                                 |
|  LAYER 6: DR TESTING + SECURITY VALIDATION                      |
|    Pen testing DR, tabletop exercises, gap documentation         |
|                                                                 |
|  LAYER 7: CLOUD DR + COMPLIANCE                                 |
|    AWS/Azure/GCP security, data residency, audit trail           |
|                                                                 |
+=================================================================+
```

---

## Table of Contents

1. [DR Security Threat Model](#1-dr-security-threat-model)
2. [Secure DR Architecture](#2-secure-dr-architecture)
3. [VMware DR Security](#3-vmware-dr-security)
4. [Proxmox DR Security](#4-proxmox-dr-security)
5. [Failover Security Procedures](#5-failover-security-procedures)
6. [Recovery Integrity Verification](#6-recovery-integrity-verification)
7. [DR Testing Security](#7-dr-testing-security)
8. [Cloud DR Security](#8-cloud-dr-security)
9. [Compliance and Audit](#9-compliance-and-audit)
10. [Lab: Secure DR Implementation](#10-lab-secure-dr-implementation)

---

## 1. DR Security Threat Model

Disaster recovery infrastructure occupies a paradoxical position in organizational security: it is simultaneously the last line of defense against catastrophic data loss and one of the most attractive targets for sophisticated adversaries. Understanding why and how attackers target DR is the foundation for every control in this module.

### 1.1 DR as Attack Target — Why Attackers Target Backups and DR Sites

Ransomware operators learned early that encrypting production data is insufficient if the victim can restore from backups within hours. Modern ransomware playbooks — documented in MITRE ATT&CK under T1490 (Inhibit System Recovery) — explicitly include a backup destruction phase:

1. **Credential harvesting for backup systems.** Attackers enumerate backup service accounts (e.g., `pbs@pam`, `svc-veeam`, `srm-admin`) through LDAP queries, Kerberos ticket analysis, or credential dumping. These accounts often have static passwords, excessive privileges, and no MFA.

2. **Backup deletion or encryption.** Once backup credentials are obtained, adversaries delete backup repositories, corrupt backup indexes, or encrypt backup storage volumes. If the DR site shares credentials with production, a single compromised account grants access to both.

3. **Replication channel poisoning.** If replication runs over an unencrypted or weakly authenticated channel, an attacker with network position can inject corrupted data into the replication stream. The DR site faithfully stores the corrupted payload, and the organization discovers the problem only at restore time.

4. **Timing attacks on backup windows.** Sophisticated actors monitor backup schedules and trigger destructive payloads immediately after a backup completes, maximizing the time until the next clean backup and increasing RPO impact.

### 1.2 Supply Chain Through DR Providers

Organizations using managed DR services (DRaaS) introduce a supply chain dependency. The DR provider's staff, infrastructure, and software become part of the trust boundary:

- **Provider-side compromise** — a breach at the DRaaS provider exposes all tenant DR data. The 2023 Acronis source code leak and the 2021 Kaseya VSA attack demonstrate this vector.
- **Shared infrastructure** — multi-tenant DR platforms may allow lateral movement between tenants if isolation is insufficient.
- **API credential exposure** — DR automation requires API keys to the provider; these keys often have broad permissions (create/delete/restore VMs) and are stored in configuration management tools with inadequate protection.

**Red team perspective:** During an authorized engagement, test whether DR provider API keys are stored in plaintext in configuration management (Ansible vaults, Terraform state, CI/CD variables). Check whether those keys grant permissions beyond what DR automation requires. Verify that the provider supports IP allowlisting for API access.

### 1.3 DR Site as Lateral Movement Path

The DR site is connected to production via replication channels, VPN tunnels, and management networks. These connections create lateral movement paths:

- **VPN tunnels between sites** often permit unrestricted traffic between subnets. An attacker who compromises the DR site can traverse back to production — or vice versa.
- **Management plane sharing** — if vCenter, Proxmox web UI, or monitoring systems span both sites with single-sign-on, compromise of one management credential grants access to both sites.
- **DNS and routing** — DR failover typically involves DNS changes or BGP announcements. An attacker who compromises the DR automation system can redirect traffic to attacker-controlled infrastructure.

### 1.4 DR Data as Exfiltration Target

DR sites aggregate copies of all critical data in a concentrated location. This makes them high-value exfiltration targets:

- **Backup repositories** contain complete VM images including databases, application data, credentials, and certificates.
- **Replication traffic** traversing WAN links contains the delta of all production changes — effectively a real-time data stream.
- **DR test environments** may have relaxed security controls (no DLP, reduced monitoring) while containing production data.

### 1.5 DR Process as Availability Attack Vector

The DR process itself can be weaponized:

- **Triggering false failover** — if DR automation monitoring is compromised, an attacker can simulate a primary site failure, triggering failover. The resulting confusion, partial service availability, and operational chaos serve as cover for other attack activities.
- **Preventing legitimate failover** — corrupting DR automation, deleting failover scripts, or disabling monitoring prevents the organization from executing DR when genuinely needed.
- **Split-brain exploitation** — triggering conditions where both primary and DR sites believe they are active creates data divergence, consistency violations, and potential data loss during reconciliation.

### 1.6 Insider Threats to DR

DR systems have unique insider threat exposure:

- **DR administrators** typically have elevated privileges across both sites — root/Administrator access, backup encryption keys, and knowledge of failover procedures.
- **DR testing** requires periodic full-access operations that can mask malicious activity.
- **DR documentation** contains the complete blueprint for organizational infrastructure, network architecture, credentials, and recovery procedures — a comprehensive intelligence document.

**Control:** Apply need-to-know segmentation to DR documentation. Separate operational runbooks (what to do) from security architecture documents (how it works). Require dual authorization for DR operations that involve credential access or data restore.

### 1.7 Ransomware Resilience Through DR

A properly secured DR architecture is the most effective ransomware countermeasure:

- **Immutable backups** — backups that cannot be modified or deleted within a retention window, regardless of credential compromise.
- **Air-gapped or logically isolated DR** — replication targets that are unreachable from production networks except during scheduled replication windows.
- **Out-of-band recovery** — the ability to rebuild infrastructure from DR without depending on any production system, including identity providers and DNS.
- **Clean restore verification** — scanning recovered VMs for malware before bringing them online prevents re-infection from compromised backups.

The remainder of this module provides the concrete controls, configurations, and procedures to achieve each of these properties.

---

## 2. Secure DR Architecture

### 2.1 Isolated DR Network Design

The DR site network must be architecturally distinct from production. Shared flat networks between sites are the single largest DR security failure pattern.

**Reference architecture — three-zone DR network:**

```
                    PRODUCTION SITE                          DR SITE
                   ┌──────────────────┐                    ┌──────────────────┐
                   │   Production     │                    │   DR Recovery    │
                   │   Workloads      │                    │   Workloads      │
                   │   10.1.0.0/16    │                    │   10.2.0.0/16    │
                   └────────┬─────────┘                    └────────┬─────────┘
                            │                                       │
                   ┌────────┴─────────┐                    ┌────────┴─────────┐
                   │   Prod Mgmt      │                    │   DR Mgmt        │
                   │   172.16.1.0/24  │                    │   172.16.2.0/24  │
                   └────────┬─────────┘                    └────────┴─────────┘
                            │                                       │
                   ┌────────┴─────────┐                    ┌────────┴─────────┐
                   │  Replication DMZ │◄═══ WireGuard ════►│  Replication DMZ │
                   │  192.168.100.0/30│   (encrypted)      │  192.168.100.0/30│
                   └──────────────────┘                    └──────────────────┘
```

Key principles:

1. **Replication traffic traverses a dedicated DMZ.** No production workload traffic shares the replication path.
2. **Management planes are separate.** DR management network (172.16.2.0/24) is not routable from production management (172.16.1.0/24) except through an explicit jump host with MFA.
3. **Workload networks use distinct address spaces.** This prevents accidental routing loops during failover and makes firewall rules unambiguous.
4. **The replication tunnel carries only replication protocol traffic** — PBS sync, ZFS send/receive, or Ceph RBD mirror. No SSH management, no API calls, no monitoring traverse this link.

### 2.2 Management Plane Separation

Each site must have an independent management plane:

| Component | Production Site | DR Site |
|---|---|---|
| Identity provider | Primary AD/LDAP | Replica or independent IdP |
| Certificate authority | Primary PKI | Subordinate CA or independent root |
| Proxmox/vCenter auth | pam + LDAP bind | pam + local LDAP replica |
| Monitoring | Primary Prometheus/Zabbix | Independent DR Prometheus |
| DNS | Primary DNS servers | DR DNS servers (separate zone files) |
| NTP | Stratum 2 from stratum 1 | Independent stratum 2 |
| Syslog/SIEM | Primary SIEM | DR SIEM collector (forwarding to primary if available) |

**The DR site must be able to operate with zero dependency on production infrastructure.** If the DR site requires production AD for authentication, a production failure that destroys AD also destroys DR access.

### 2.3 Credential Isolation Between Primary and DR

This is the most critical DR security control and the most frequently violated:

**Rule:** No credential must grant access to both production and DR sites simultaneously.

Implementation:

- **Separate service accounts** for replication. The account that writes to the DR PBS is not the same account that manages production PBS.
- **Separate root/admin passwords** per site. Use a password manager with separate vaults or compartments.
- **Separate SSH key pairs** for each site. The private key used to SSH into DR hosts must not exist on production hosts.
- **Separate API tokens** for automation. Terraform, Ansible, and CI/CD pipelines targeting DR use distinct credentials stored in separate secret backends.

```bash
# Example: separate Vault mounts for production and DR credentials
vault secrets enable -path=prod/proxmox kv-v2
vault secrets enable -path=dr/proxmox kv-v2

# Production replication service account — can PUSH to DR
vault kv put prod/proxmox/replication \
  user="repl-push@pbs" \
  token="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" \
  fingerprint="aa:bb:cc:dd:..."

# DR administrative account — separate, never stored on production
vault kv put dr/proxmox/admin \
  user="admin@pam" \
  password="$(openssl rand -base64 32)"
```

### 2.4 Encryption in Transit for Replication

All replication traffic between sites must be encrypted. Three options, ranked by operational simplicity:

#### WireGuard (Recommended for Proxmox-to-Proxmox)

```ini
# /etc/wireguard/wg-repl.conf — PRODUCTION SIDE
[Interface]
PrivateKey = <PROD_PRIVATE_KEY>
Address = 192.168.100.1/30
ListenPort = 51820

# Restrict to replication traffic only
PostUp = iptables -A FORWARD -i wg-repl -o eth0 -j DROP
PostUp = iptables -A FORWARD -i wg-repl -d 172.16.2.10 -p tcp --dport 8007 -j ACCEPT
PostDown = iptables -D FORWARD -i wg-repl -o eth0 -j DROP
PostDown = iptables -D FORWARD -i wg-repl -d 172.16.2.10 -p tcp --dport 8007 -j ACCEPT

[Peer]
PublicKey = <DR_PUBLIC_KEY>
Endpoint = dr-site.example.com:51820
AllowedIPs = 192.168.100.2/32
PersistentKeepalive = 25
```

```ini
# /etc/wireguard/wg-repl.conf — DR SIDE
[Interface]
PrivateKey = <DR_PRIVATE_KEY>
Address = 192.168.100.2/30
ListenPort = 51820

PostUp = iptables -A FORWARD -i wg-repl -o eth0 -j DROP
PostUp = iptables -A INPUT -i wg-repl -p tcp --dport 8007 -j ACCEPT
PostDown = iptables -D FORWARD -i wg-repl -o eth0 -j DROP
PostDown = iptables -D INPUT -i wg-repl -p tcp --dport 8007 -j ACCEPT

[Peer]
PublicKey = <PROD_PUBLIC_KEY>
Endpoint = prod-site.example.com:51820
AllowedIPs = 192.168.100.1/32
PersistentKeepalive = 25
```

```bash
# Enable and start on both sides
systemctl enable --now wg-quick@wg-repl
# Verify tunnel
wg show wg-repl
```

#### IPSec (StrongSwan — for environments requiring FIPS compliance)

```bash
# /etc/ipsec.conf — production side
conn prod-to-dr
    type=tunnel
    auto=start
    keyexchange=ikev2
    ike=aes256gcm16-sha384-ecp384!
    esp=aes256gcm16-sha384!
    left=203.0.113.10
    leftsubnet=192.168.100.1/32
    leftcert=prod-ipsec.pem
    right=198.51.100.20
    rightsubnet=192.168.100.2/32
    rightcert=dr-ipsec.pem
    dpdaction=restart
    dpddelay=30s
    dpdtimeout=120s
```

#### TLS (For application-layer replication — PBS sync, vSphere Replication)

PBS sync and vSphere Replication already use TLS. The key control is certificate validation:

```bash
# Verify PBS remote uses TLS with fingerprint pinning
proxmox-backup-manager remote list --output-format json | \
  jq '.[] | {name, server, fingerprint}'
```

### 2.5 Encryption at Rest at DR Site

DR storage must be encrypted at rest. If the DR site is physically less secure than production (colocation vs. owned datacenter), at-rest encryption is non-negotiable.

```bash
# LUKS encryption for PBS datastore volume
cryptsetup luksFormat --type luks2 \
  --cipher aes-xts-plain64 \
  --key-size 512 \
  --hash sha512 \
  --iter-time 5000 \
  /dev/sdb1

cryptsetup luksOpen /dev/sdb1 pbs-dr-store

mkfs.ext4 /dev/mapper/pbs-dr-store
mount /dev/mapper/pbs-dr-store /mnt/pbs-dr-datastore

# For automated unlock at boot, use a KMIP/Vault-managed key via clevis
clevis luks bind -d /dev/sdb1 tang '{"url":"http://tang.dr-site.internal:7500"}'
```

For ZFS:

```bash
# ZFS native encryption on DR pool
zpool create -o ashift=12 \
  -O encryption=aes-256-gcm \
  -O keyformat=passphrase \
  -O keylocation=file:///etc/zfs/dr-pool.key \
  dr-pool mirror /dev/sdc /dev/sdd

# Key file must be protected
chmod 400 /etc/zfs/dr-pool.key
chown root:root /etc/zfs/dr-pool.key
```

### 2.6 Key Management Across Sites — KMIP and Vault Replication

Key management is the hardest problem in multi-site encryption. Keys must be available at the DR site for decryption during recovery, but must not be compromised if either site is breached.

**HashiCorp Vault Performance Replication (recommended):**

```bash
# Primary Vault (production site)
vault write sys/replication/performance/primary/enable \
  primary_cluster_addr="https://vault.prod.internal:8201"

# Generate secondary token
vault write sys/replication/performance/primary/secondary-token \
  id="dr-site" \
  ttl="30m"

# DR site Vault — activate as performance secondary
vault write sys/replication/performance/secondary/enable \
  token="<TOKEN_FROM_PRIMARY>"

# Verify replication status
vault read sys/replication/performance/status
```

**KMIP for storage encryption keys (vSphere, LUKS):**

```bash
# Vault KMIP secrets engine
vault secrets enable kmip
vault write kmip/config listen_addrs=0.0.0.0:5696

# Create scope for DR storage
vault write kmip/scope/dr-storage -f
vault write kmip/scope/dr-storage/role/server \
  operation_activate=true \
  operation_get=true \
  operation_locate=true \
  operation_create=true

# Generate client certificate for DR storage systems
vault write kmip/scope/dr-storage/role/server/credential/generate \
  format=pem
```

### 2.7 Hardware Security at DR Site

Physical security at the DR site must match or exceed production:

- **TPM 2.0** on all DR hypervisors for measured boot and key sealing.
- **UEFI Secure Boot** enabled, preventing boot-level rootkits on DR hosts that sit idle for extended periods.
- **IPMI/BMC on isolated management VLAN** — out-of-band management must be on a separate network segment with MFA, not accessible from the replication DMZ.
- **Tamper-evident chassis** — DR hardware that is infrequently visited is vulnerable to physical tampering. Use chassis intrusion detection and log alerts.
- **Controlled physical access** — if colocation, require escorted access with photographic logging. Verify the colo provider's SOC 2 Type II report annually.

---

## 3. VMware DR Security

### 3.1 Site Recovery Manager (VMware Live Site Recovery) — Architecture and Security Configuration

VMware Site Recovery Manager (SRM), rebranded as VMware Live Site Recovery following the Broadcom acquisition, orchestrates DR failover between vCenter instances. Its security architecture requires attention at several layers.

**Architecture overview:**

```
Protected Site                           Recovery Site
┌────────────┐                          ┌────────────┐
│  vCenter   │◄════ TLS (port 443) ════►│  vCenter   │
│  Server    │                          │  Server    │
└─────┬──────┘                          └─────┬──────┘
      │                                       │
┌─────┴──────┐                          ┌─────┴──────┐
│    SRM      │◄═══ TLS (port 9086) ═══►│    SRM      │
│  Appliance  │                         │  Appliance  │
└─────┬──────┘                          └─────┬──────┘
      │                                       │
┌─────┴──────┐                          ┌─────┴──────┐
│  vSphere   │◄═══ TLS replication ════►│  vSphere   │
│ Replication│                          │ Replication│
└────────────┘                          └────────────┘
```

**Security configuration checklist:**

1. **SRM appliance hardening:**
   - Change default root password immediately after deployment.
   - Disable SSH access; enable only during maintenance windows.
   - Configure NTP to prevent time skew (critical for certificate validation).
   - Apply latest SRM patches — SRM has had critical CVEs (CVE-2021-21981: local privilege escalation, CVE-2022-31697: credential exposure in log files).

2. **vCenter trust relationship:**
   - Use Enhanced Linked Mode with separate SSO domains per site (not the same SSO domain for both sites).
   - Each vCenter must have its own Platform Services Controller (PSC) or embedded PSC.
   - Certificate trust: import the recovery site vCenter's CA certificate into the protected site's trust store, and vice versa. Do not use thumbprint-only trust for production.

3. **SRM service account:**
   ```
   # Minimal required permissions for SRM service account
   - VirtualMachine.Inventory.Create
   - VirtualMachine.Inventory.Delete
   - VirtualMachine.Config.Settings
   - Resource.AssignVMToPool
   - Datastore.AllocateSpace
   - Network.Assign
   - VirtualMachine.State.CreateSnapshot
   - VirtualMachine.State.RemoveSnapshot
   # Do NOT grant Administrator role — violates least privilege
   ```

4. **Recovery plan security:**
   - Recovery plans can execute arbitrary scripts (pre/post power-on callouts). Validate that these scripts are stored in a version-controlled, integrity-verified repository.
   - Limit who can create/modify recovery plans via vCenter permissions.
   - Audit recovery plan changes through vCenter event logs.

### 3.2 vSphere Replication — Encryption and Authentication

vSphere Replication transfers VM disk data between sites. Security considerations:

- **In-transit encryption:** vSphere Replication supports TLS encryption. Enable it in the vSphere Replication appliance configuration: `Administration → vSphere Replication → Configuration → Enable encryption for replication traffic`.
- **Certificate-based authentication:** Each VR appliance authenticates to the remote site using certificates signed by the vCenter CA. Verify certificate chains are intact after any CA rotation.
- **Network isolation:** vSphere Replication traffic should traverse a dedicated VLAN/subnet. Never run replication over the management network — a compromise of the management plane would expose replication data.
- **Bandwidth throttling:** Configure replication bandwidth limits to prevent a compromised or misconfigured replication from saturating the WAN link (potential DoS vector).

### 3.3 NSX-T Cross-Site Security — Consistent Firewall Policies

When both sites run NSX-T, firewall policies must be consistent across sites. A VM that is protected by microsegmentation at the primary site must retain equivalent protection at the DR site.

**NSX Federation** provides this through Global Manager:

- **Global Manager** pushes distributed firewall (DFW) rules to both Local Managers.
- **Security Groups** defined in Global Manager apply at both sites.
- **Rule precedence:** Global rules take precedence over local rules, ensuring DR site cannot have weaker policies.

**Without NSX Federation** (common during migration), manually synchronize:

```powershell
# PowerCLI: export DFW rules from primary NSX Manager
$rules = Get-NsxFirewallSection | Get-NsxFirewallRule
$rules | Export-Csv -Path "dfw-rules-export.csv" -NoTypeInformation

# Import on DR NSX Manager after validation
# Manual review required — IP addresses may differ between sites
```

**Critical gap:** If the DR site uses standard vSwitch or vDS without NSX, all microsegmentation is lost upon failover. Document this gap and implement compensating controls (host-based firewalls, perimeter firewall rules).

### 3.4 VM Encryption Key Management During Recovery

VMs encrypted with vSphere VM Encryption use keys from a KMS (KMIP-compliant). During DR recovery:

1. **Both sites must have access to the same KMS cluster** or a replicated KMS instance.
2. **KMS trust must be established at the DR vCenter** before a disaster occurs. During an emergency is too late.
3. **Key IDs travel with the VM** via the `.vmx` configuration file. The DR vCenter requests the key from KMS using the key ID.
4. **If KMS is unavailable at DR site:** encrypted VMs cannot be powered on. This is a complete recovery failure. Mitigate by deploying a KMS replica at the DR site with independent network access.

```
# Verify KMS connectivity at DR vCenter
Connect-VIServer dr-vcenter.example.com
Get-KeyProvider | Select Name, Status, Type
# Status must be "Connected" and "Healthy"
```

### 3.5 Storage Replication Security — SRDF, RecoverPoint, Zerto

Array-based replication (Dell EMC SRDF, RecoverPoint; Zerto) handles encryption differently:

| Solution | Encryption in Transit | Authentication | Key Management |
|---|---|---|---|
| SRDF/Metro | IPSec or FC encryption | Symmetrix service account | Symmetrix key manager |
| RecoverPoint | IPSec tunnels | Certificate-based | RecoverPoint internal |
| Zerto | TLS 1.2+ | ZVM pairing token | Zerto key manager |

**Common vulnerability across all:** the management interface. Zerto Virtual Manager (ZVM), RecoverPoint management, and SRDF Operations Console all provide web interfaces that, if compromised, grant the ability to delete replicas, pause replication, or restore to arbitrary points in time. Harden these interfaces with MFA, IP allowlisting, and audit logging.

---

## 4. Proxmox DR Security

### 4.1 Proxmox Backup Server — Remote Sync Security and Encryption

PBS remote sync is the primary Proxmox-native DR mechanism. Security configuration:

```bash
# On DR PBS: create a dedicated datastore for remote sync
proxmox-backup-manager datastore create dr-incoming \
  --path /mnt/pbs-dr-datastore/dr-incoming \
  --gc-schedule "daily 03:00" \
  --prune-schedule "daily 04:00" \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 6

# Create a dedicated API token for replication (least privilege)
proxmox-backup-manager user create repl-push@pbs
proxmox-backup-manager acl update / DatastoreBackup --auth-id repl-push@pbs
proxmox-backup-manager user generate-token repl-push@pbs repl-token

# Note: record the token value and the server fingerprint
# Token format: repl-push@pbs!repl-token=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```bash
# On PRODUCTION PBS: configure remote target
proxmox-backup-manager remote create dr-site \
  --host 192.168.100.2 \
  --port 8007 \
  --auth-id repl-push@pbs!repl-token \
  --password "<API_TOKEN_SECRET>" \
  --fingerprint "aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99:aa:bb:cc:dd:ee:ff:00:11:22:33:44:55:66:77:88:99"

# Create sync job
proxmox-backup-manager sync-job create prod-to-dr \
  --remote dr-site \
  --remote-store dr-incoming \
  --store production-backups \
  --schedule "hourly" \
  --remove-vanished false
```

**Security controls for PBS sync:**

1. **Fingerprint pinning** — the `--fingerprint` parameter pins the DR PBS server's TLS certificate fingerprint. This prevents MITM attacks even if the CA is compromised.
2. **`--remove-vanished false`** — prevents replication from deleting backups at the DR site that have been deleted (or deleted by an attacker) at the production site. This is essential for ransomware resilience.
3. **Client-side encryption** — PBS supports client-side encryption where the backup data is encrypted before leaving the production site. The DR site stores only ciphertext.

```bash
# Generate encryption key for client-side encrypted backups
proxmox-backup-client key create --kdf scrypt /etc/pbs-encryption-key.json

# Backup with encryption
proxmox-backup-client backup vm/100.img:/dev/vg/vm-100 \
  --repository repl-push@pbs!repl-token@192.168.100.2:dr-incoming \
  --keyfile /etc/pbs-encryption-key.json \
  --encrypt

# CRITICAL: store encryption key separately from PBS
# Recommended: Vault, HSM, or offline cold storage
# The DR site CANNOT decrypt without this key
```

4. **Immutable backups (datastore-level protection):**

```bash
# PBS 3.x: configure verification and protection
# Set namespace protection to prevent deletion
proxmox-backup-manager datastore update dr-incoming \
  --verify-new true \
  --notification-mode notification-system
```

### 4.2 Ceph Replication Across Sites — Security Configuration

Ceph RBD mirroring enables block-level replication for Proxmox VMs. Security configuration for cross-site Ceph:

```bash
# === PRODUCTION CEPH CLUSTER ===

# Enable journaling on the pool (required for journal-based mirroring)
# Snapshot-based mirroring is preferred for cross-WAN — lower bandwidth
rbd mirror pool enable prod-pool image

# Create a dedicated Ceph user for mirroring with minimal capabilities
ceph auth get-or-create client.rbd-mirror.dr-site \
  mon 'profile rbd-mirror' \
  osd 'profile rbd' \
  mgr 'profile rbd' \
  -o /etc/ceph/ceph.client.rbd-mirror.dr-site.keyring

# Restrict keyring file permissions
chmod 600 /etc/ceph/ceph.client.rbd-mirror.dr-site.keyring
```

```bash
# === DR CEPH CLUSTER ===

# Bootstrap peer (exchange credentials between clusters)
# Export the peer token from production
rbd mirror pool peer bootstrap create \
  --site-name production \
  prod-pool > /tmp/prod-bootstrap-token

# Import on DR side (token contains credentials — transfer securely)
rbd mirror pool peer bootstrap import \
  --site-name dr-site \
  --direction rx-only \
  dr-pool < /tmp/prod-bootstrap-token

# IMPORTANT: delete the bootstrap token file after import
shred -u /tmp/prod-bootstrap-token

# Verify mirror status
rbd mirror pool status dr-pool --verbose
```

**Ceph cross-site security controls:**

1. **Encrypted messenger v2 (msgr2):** Ceph Reef+ supports on-wire encryption. Enable it:
   ```ini
   # /etc/ceph/ceph.conf — both clusters
   [global]
   ms_cluster_mode = secure
   ms_service_mode = secure
   ms_client_mode = secure
   ms_mon_cluster_mode = secure
   ms_mon_service_mode = secure
   ms_mon_client_mode = secure
   ```
2. **Separate Ceph keyring for mirroring** — the mirror daemon must not use the `client.admin` keyring.
3. **rx-only direction** — the DR cluster should only receive; it should never push data back to production during normal operation.
4. **Monitor mirror lag** — if lag increases unexpectedly, it may indicate network compromise or data manipulation:
   ```bash
   rbd mirror image status dr-pool/vm-100-disk-0 | grep -E "state|last_update|bytes_per_second"
   ```

### 4.3 ZFS Send/Receive Over SSH — Key Management

ZFS send/receive is the simplest and most commonly used Proxmox replication method for cross-site DR. Security hardening:

```bash
# Generate a dedicated SSH key pair for ZFS replication
ssh-keygen -t ed25519 -f /root/.ssh/zfs-repl-key -N "" -C "zfs-repl-prod-to-dr"

# Install public key on DR host with forced command restriction
# On DR host: /root/.ssh/authorized_keys
cat >> /root/.ssh/authorized_keys << 'AUTHKEY'
command="/usr/local/bin/zfs-recv-wrapper.sh",no-port-forwarding,no-X11-forwarding,no-agent-forwarding,no-pty ssh-ed25519 AAAA... zfs-repl-prod-to-dr
AUTHKEY
```

```bash
# /usr/local/bin/zfs-recv-wrapper.sh — on DR host
#!/bin/bash
# Restrict the SSH key to only receive ZFS streams into the DR pool
set -euo pipefail

ALLOWED_POOL="dr-pool"

# Parse the original command from SSH_ORIGINAL_COMMAND
case "${SSH_ORIGINAL_COMMAND}" in
    "zfs receive"*"${ALLOWED_POOL}"*)
        exec ${SSH_ORIGINAL_COMMAND}
        ;;
    *)
        logger -t zfs-recv-wrapper "DENIED: ${SSH_ORIGINAL_COMMAND} from ${SSH_CLIENT}"
        echo "ERROR: command not allowed" >&2
        exit 1
        ;;
esac
```

```bash
# Replication script — production host
#!/bin/bash
# /usr/local/bin/zfs-dr-replicate.sh
set -euo pipefail

SRC_DATASET="rpool/data"
DST_HOST="192.168.100.2"
DST_DATASET="dr-pool/data"
SSH_KEY="/root/.ssh/zfs-repl-key"
SNAP_PREFIX="dr-repl"
LOG="/var/log/zfs-dr-repl.log"

CURRENT_SNAP="${SRC_DATASET}@${SNAP_PREFIX}-$(date +%Y%m%d-%H%M%S)"
LAST_SNAP=$(zfs list -t snapshot -o name -s creation "${SRC_DATASET}" | \
  grep "${SNAP_PREFIX}" | tail -1)

# Create new snapshot
zfs snapshot -r "${CURRENT_SNAP}"

if [ -n "${LAST_SNAP}" ]; then
  # Incremental send with raw (preserves encryption) and compressed
  zfs send -R -w -i "${LAST_SNAP}" "${CURRENT_SNAP}" | \
    mbuffer -s 128k -m 1G -q 2>/dev/null | \
    ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=yes \
        -o ConnectTimeout=30 \
        -c aes256-gcm@openssh.com \
        root@"${DST_HOST}" \
        "zfs receive -F ${DST_DATASET}" \
    2>&1 | tee -a "${LOG}"
else
  # Full initial send
  zfs send -R -w "${CURRENT_SNAP}" | \
    mbuffer -s 128k -m 1G -q 2>/dev/null | \
    ssh -i "${SSH_KEY}" -o StrictHostKeyChecking=yes \
        -o ConnectTimeout=30 \
        -c aes256-gcm@openssh.com \
        root@"${DST_HOST}" \
        "zfs receive -F ${DST_DATASET}" \
    2>&1 | tee -a "${LOG}"
fi

# Verify snapshot arrived at DR
ssh -i "${SSH_KEY}" root@"${DST_HOST}" \
  "zfs list -t snapshot ${DST_DATASET} | tail -3" | tee -a "${LOG}"

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Replication completed: ${CURRENT_SNAP}" >> "${LOG}"
```

**Key security properties of this script:**

- `-w` flag sends raw encrypted ZFS data — the DR site stores ciphertext if the source dataset is encrypted.
- `StrictHostKeyChecking=yes` — refuses to connect if the DR host key has changed (prevents MITM).
- `-c aes256-gcm@openssh.com` — forces a specific cipher, preventing downgrade attacks.
- Forced command on the receiving side — even if the SSH key is stolen, the attacker can only pipe data into `zfs receive`, not execute arbitrary commands.
- `mbuffer` prevents stalls on high-latency links; its `-q` flag suppresses progress output to avoid log noise.

### 4.4 Proxmox Cluster Across WAN — Corosync Security

Stretching a Proxmox cluster across WAN is generally discouraged (see Module 19) but occasionally necessary for warm standby. Corosync security:

```bash
# /etc/corosync/corosync.conf — security-relevant settings
totem {
    version: 2
    secauth: on
    crypto_cipher: aes256
    crypto_hash: sha256
    transport: knet

    # knet allows unicast — REQUIRED for WAN (multicast doesn't cross WAN)
    # Each node is defined with its address
}

nodelist {
    node {
        ring0_addr: 172.16.1.10
        name: pve-prod-01
        nodeid: 1
    }
    node {
        ring0_addr: 172.16.2.10
        name: pve-dr-01
        nodeid: 2
    }
}

quorum {
    provider: corosync_votequorum
    # With 2 nodes, need external vote
    # QDevice provides the tiebreaker
}
```

```bash
# Configure QDevice for quorum tiebreaker
# QDevice host should be at a THIRD site (neutral location)
apt install corosync-qdevice  # on cluster nodes
apt install corosync-qnetd    # on QDevice host

# Initialize QNet daemon on the third-site host
corosync-qnetd-certutil -i

# Add QDevice to cluster
pvecm qdevice setup <QDEVICE_HOST_IP>
```

**Security considerations for WAN cluster:**

1. **Corosync authkey** — the `/etc/corosync/authkey` file is the symmetric key for cluster communication. If compromised, an attacker can inject false cluster state. Rotate it periodically and transport it only via encrypted channels.
2. **knet encryption** — with `crypto_cipher: aes256` and `secauth: on`, all corosync traffic is encrypted. Verify with `corosync-cmapctl | grep crypto`.
3. **Firewall rules** — restrict corosync ports (5405-5412 for knet) to only the cluster node IPs. Never expose corosync to the public internet.
4. **QDevice trust** — the QDevice host influences quorum decisions. If compromised, it can force a partition that causes the DR site to fence production or vice versa. Harden the QDevice host as a critical infrastructure component.

### 4.5 Custom Replication Scripts — Security Considerations

Custom scripts (bash, Python) for DR replication introduce unique risks:

1. **Credential embedding** — scripts that contain passwords, API tokens, or SSH key paths inline. Store credentials in Vault, environment variables, or restricted files (`chmod 600`).
2. **Injection attacks** — scripts that construct ZFS commands, API calls, or SSH commands from variables without sanitization. Always quote variables and validate inputs.
3. **Error handling** — scripts that fail silently, leaving replication in an inconsistent state. Use `set -euo pipefail` and log all operations.
4. **Log exposure** — scripts that log full commands including credentials. Sanitize log output.
5. **Cron execution context** — cron jobs run with minimal environment. Ensure `PATH`, key agent, and Vault tokens are properly set.

### 4.6 Third-Party DR — Veeam and Nakivo for Proxmox

Veeam Backup & Replication and Nakivo Backup & Replication both support Proxmox VE:

**Veeam for Proxmox security controls:**

- Deploy the Veeam Backup & Replication server on a hardened, dedicated host — not on a Proxmox node.
- Use dedicated Proxmox API tokens (not root) with minimal permissions: `PVEAuditor` + `PVEDatastoreUser` roles.
- Enable Veeam encryption for backup files at the repository level with per-job encryption keys.
- Configure immutable repository (Linux hardened repository) at the DR site — Veeam uses a dedicated service account with time-limited `sudo` permissions for immutability enforcement.
- Disable Veeam console access from production networks — the backup server should be reachable only from an isolated management segment.

**Nakivo for Proxmox security controls:**

- Similar principle: dedicated deployment, API token authentication, encrypted repositories.
- Nakivo supports Amazon S3 Object Lock for immutable offsite copies — configure with Compliance mode (not Governance mode, which can be overridden by root).

---

## 5. Failover Security Procedures

### 5.1 Pre-Failover Security Checks

Before initiating failover, automated checks must validate security readiness at the DR site:

```bash
#!/bin/bash
# /usr/local/bin/dr-preflight-security.sh
# Run BEFORE triggering DR failover
set -euo pipefail

CHECKS_PASSED=0
CHECKS_FAILED=0
LOG="/var/log/dr-preflight.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG}"; }

check() {
    local description="$1"
    local command="$2"

    if eval "${command}" > /dev/null 2>&1; then
        log "PASS: ${description}"
        ((CHECKS_PASSED++))
    else
        log "FAIL: ${description}"
        ((CHECKS_FAILED++))
    fi
}

log "=== DR Pre-flight Security Checks Starting ==="

# 1. Credential readiness
check "DR PBS admin account accessible" \
  "proxmox-backup-manager user list 2>/dev/null | grep -q admin@pam"

check "DR Proxmox API reachable" \
  "curl -sk https://172.16.2.10:8006/api2/json/version | grep -q release"

check "DR SSH host key unchanged" \
  "ssh-keygen -F 172.16.2.10 | grep -q 172.16.2.10"

# 2. Network configuration
check "WireGuard tunnel up" \
  "wg show wg-repl | grep -q 'latest handshake'"

check "DR management network reachable" \
  "ping -c 1 -W 2 172.16.2.10"

check "DR DNS resolution working" \
  "dig @172.16.2.1 +short dr-pve01.internal | grep -q 172.16.2.10"

# 3. Firewall rules
check "DR firewall active" \
  "ssh -o ConnectTimeout=5 root@172.16.2.10 'pve-firewall status | grep -q running'"

check "DR iptables rules loaded" \
  "ssh -o ConnectTimeout=5 root@172.16.2.10 'iptables -L -n | wc -l' | awk '{exit (\$1 > 5) ? 0 : 1}'"

# 4. Storage readiness
check "DR datastore mounted and writable" \
  "ssh root@172.16.2.10 'test -w /mnt/pbs-dr-datastore/dr-incoming'"

check "DR ZFS pool healthy" \
  "ssh root@172.16.2.10 'zpool status dr-pool | grep -q ONLINE'"

# 5. Time synchronization
check "DR NTP synchronized" \
  "ssh root@172.16.2.10 'chronyc tracking | grep -q \"Leap status     : Normal\"'"

# 6. Last backup freshness
LAST_BACKUP_AGE=$(ssh root@172.16.2.10 \
  "proxmox-backup-client snapshot list --repository localhost:dr-incoming 2>/dev/null | \
   tail -1 | awk '{print \$3}'")
check "Last backup within RPO window" \
  "test -n '${LAST_BACKUP_AGE}'"

# Summary
log "=== Results: ${CHECKS_PASSED} passed, ${CHECKS_FAILED} failed ==="

if [ "${CHECKS_FAILED}" -gt 0 ]; then
    log "WARNING: ${CHECKS_FAILED} pre-flight checks failed. Review before proceeding."
    exit 1
fi

log "All pre-flight checks passed. Failover may proceed."
exit 0
```

### 5.2 Automated vs. Manual Failover — Security Tradeoffs

| Aspect | Automated Failover | Manual Failover |
|---|---|---|
| Speed | RTO minimized (minutes) | RTO increased (hours) |
| False positive risk | High — monitoring false alarm triggers unnecessary failover | None — human validates |
| Attack surface | Automation system is an attack target — compromise = control over failover | Requires human access to DR during emergency |
| Split-brain risk | Higher — automated systems may disagree | Lower — human coordinates |
| Auditability | Full automation log | Depends on operator discipline |
| Recommendation | Use for well-understood, frequently tested scenarios | Use for ambiguous situations, first-time events |

**Hybrid approach (recommended):** automated detection with human-confirmed execution. The monitoring system detects failure and pages the on-call team, pre-stages the failover (runs pre-flight checks, pre-warms DNS TTLs), but requires a human to authorize the actual failover command.

### 5.3 Failover Authentication — Ensuring Access During Emergency

The most common DR failure mode is not infrastructure — it is authentication. When production AD/LDAP is down, teams cannot log in to DR systems if those systems depend on the same directory.

**Controls:**

1. **Break-glass accounts** — local accounts on DR Proxmox hosts and PBS with strong, unique passwords stored in a physical safe or offline password manager.

```bash
# Create break-glass local account on DR Proxmox
pveum user add dr-breakglass@pam
pveum passwd dr-breakglass@pam  # set strong password, store offline
pveum acl modify / --roles Administrator --users dr-breakglass@pam

# Document and seal in tamper-evident envelope
# Store in physical safe accessible to DR team
# Test quarterly that the account works
```

2. **Offline MFA** — if MFA is enforced, use TOTP (not push-based MFA that requires cloud connectivity). Pre-enroll TOTP seeds for break-glass accounts.

3. **Pre-positioned SSH keys** — SSH keys for DR hosts, stored on encrypted USB drives in the DR team's possession. Test that these keys authenticate before every DR drill.

4. **VPN fallback** — if the primary VPN concentrator is at the production site, ensure a fallback VPN endpoint exists at the DR site or via a cloud-hosted bastion.

### 5.4 Network Security During Failover

Failover involves DNS changes, routing changes, and firewall rule activation — each a potential attack vector:

**DNS failover security:**

```bash
# Use low TTL on records that will change during failover
# Pre-configure but do NOT activate DR records
# Example: Cloudflare API to switch DNS (use API token, not global key)

#!/bin/bash
# /usr/local/bin/dr-dns-failover.sh
set -euo pipefail

CF_API_TOKEN="${CF_API_TOKEN:?Must set CF_API_TOKEN}"
ZONE_ID="your-zone-id"
RECORD_ID="your-record-id"
DR_IP="198.51.100.20"

curl -s -X PUT \
  "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records/${RECORD_ID}" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data "{\"type\":\"A\",\"name\":\"app.example.com\",\"content\":\"${DR_IP}\",\"ttl\":60,\"proxied\":false}" \
  | jq '.success'
```

**Firewall activation during failover:**

```bash
# DR site firewall rules — pre-configured but DISABLED until failover
# /etc/pve/firewall/cluster.fw on DR site

[RULES]
# Production-equivalent rules — activated during failover
IN ACCEPT -source 0.0.0.0/0 -dest +webservers -p tcp -dport 443 -log nolog
IN ACCEPT -source 10.2.0.0/24 -dest +dbservers -p tcp -dport 5432 -log nolog
IN DROP -log warning
```

### 5.5 Partial Failover — Security of Split-Brain Scenarios

Partial failover — where some services run at the primary site and others at the DR site — creates security complexity:

1. **Data consistency risk** — a database at the DR site and an application server at the primary site require cross-site database connections. These connections must be encrypted and authenticated.
2. **Firewall complexity** — temporary firewall rules allowing cross-site application traffic may be overly permissive.
3. **Identity fragmentation** — users authenticating against primary-site AD access DR-hosted applications, creating cross-site authentication dependencies.

**Mitigation:** design failover as all-or-nothing for each service tier. If the database fails over, all application servers consuming that database fail over together.

### 5.6 Communication Security During DR Event

During a DR event, normal communication channels (corporate email, Slack, Teams) may be unavailable:

- **Out-of-band communication** — pre-establish a communication channel that does not depend on production infrastructure: personal mobile phones with Signal, a pre-configured Matrix/Element server at the DR site, or a satellite phone for catastrophic scenarios.
- **War room access** — physical or virtual war room with pre-positioned credentials and documentation. If virtual, host it outside both production and DR infrastructure (a separate cloud region).
- **Status page** — a static status page hosted on a separate provider (e.g., GitHub Pages, Cloudflare Pages) that the team can update during the event.
- **Encrypt sensitive communications** — DR event communications contain infrastructure details, credentials, and recovery procedures. Use encrypted channels.

---

## 6. Recovery Integrity Verification

### 6.1 Verifying Backup Integrity Before Restore

Never restore a backup without first verifying its integrity. A corrupted or tampered backup may contain malware, missing data, or altered configurations.

```bash
#!/bin/bash
# /usr/local/bin/verify-backup-integrity.sh
# Verify PBS backup integrity before restore
set -euo pipefail

REPOSITORY="localhost:dr-incoming"
BACKUP_ID="$1"  # e.g., "vm/100/2026-05-07T03:00:00Z"
LOG="/var/log/dr-verify.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG}"; }

log "=== Verifying backup integrity: ${BACKUP_ID} ==="

# 1. PBS built-in verification (checks chunk checksums)
log "Running PBS verify..."
proxmox-backup-client verify \
  --repository "${REPOSITORY}" \
  "${BACKUP_ID}" 2>&1 | tee -a "${LOG}"

VERIFY_EXIT=$?
if [ ${VERIFY_EXIT} -ne 0 ]; then
    log "CRITICAL: PBS verify FAILED for ${BACKUP_ID}"
    exit 1
fi
log "PBS verify passed."

# 2. Check backup manifest signature
log "Checking manifest..."
proxmox-backup-client snapshot show \
  --repository "${REPOSITORY}" \
  "${BACKUP_ID}" 2>&1 | tee -a "${LOG}"

# 3. Test restore to temporary location (does not overwrite anything)
log "Performing test restore to /tmp/dr-test-restore..."
mkdir -p /tmp/dr-test-restore

proxmox-backup-client restore \
  --repository "${REPOSITORY}" \
  "${BACKUP_ID}" \
  "vm/100/disk-0.img.fidx" \
  /tmp/dr-test-restore/test-disk.raw 2>&1 | tee -a "${LOG}"

# 4. Verify restored image is mountable
log "Verifying disk image structure..."
if file /tmp/dr-test-restore/test-disk.raw | grep -q "QEMU QCOW"; then
    qemu-img check /tmp/dr-test-restore/test-disk.raw 2>&1 | tee -a "${LOG}"
elif file /tmp/dr-test-restore/test-disk.raw | grep -q "data"; then
    # Raw image — try to detect partition table
    fdisk -l /tmp/dr-test-restore/test-disk.raw 2>&1 | tee -a "${LOG}"
fi

# 5. Clean up
rm -rf /tmp/dr-test-restore
log "=== Verification complete for ${BACKUP_ID} ==="
```

### 6.2 Detecting Tampered Backups — Digital Signatures and Audit Trail

PBS uses SHA-256 checksums for chunk-level integrity, but this protects against corruption, not targeted tampering by an attacker who controls the storage layer. For tamper detection:

**Digital signatures on backup manifests:**

```bash
#!/bin/bash
# Sign backup manifests after creation
# Run on production PBS after each backup job completes
set -euo pipefail

SIGNING_KEY="/etc/pbs-signing-key.pem"
MANIFEST_DIR="/mnt/datastore/production-backups"

# Find most recent manifest
LATEST_MANIFEST=$(find "${MANIFEST_DIR}" -name "index.json.blob" -mmin -30 | head -1)

if [ -z "${LATEST_MANIFEST}" ]; then
    echo "No recent manifest found"
    exit 1
fi

# Create detached signature
openssl dgst -sha256 -sign "${SIGNING_KEY}" \
  -out "${LATEST_MANIFEST}.sig" \
  "${LATEST_MANIFEST}"

echo "Signed: ${LATEST_MANIFEST}"
echo "Signature: ${LATEST_MANIFEST}.sig"
```

```bash
# Verify signature at DR site before restore
VERIFY_KEY="/etc/pbs-signing-public.pem"
MANIFEST="$1"

openssl dgst -sha256 -verify "${VERIFY_KEY}" \
  -signature "${MANIFEST}.sig" \
  "${MANIFEST}"
# Output: "Verified OK" or "Verification Failure"
```

**Immutable audit trail:**

```bash
# Append-only audit log for backup operations
# /etc/rsyslog.d/30-pbs-audit.conf
:programname, isequal, "proxmox-backup" /var/log/pbs-audit.log
& stop

# Configure log shipping to WORM storage or remote syslog
# that production admins cannot modify
```

### 6.3 Malware Scanning Recovered VMs Before Bringing Online

This is the most frequently skipped step in DR recovery — and the one that determines whether you recover from ransomware or re-infect yourself.

```bash
#!/bin/bash
# /usr/local/bin/dr-malware-scan.sh
# Scan recovered VM disk image before bringing online
set -euo pipefail

DISK_IMAGE="$1"  # Path to restored raw/qcow2 disk
MOUNT_POINT="/mnt/dr-scan"
SCAN_LOG="/var/log/dr-malware-scan.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${SCAN_LOG}"; }

log "=== Scanning disk image: ${DISK_IMAGE} ==="

# 1. Mount the disk image read-only
mkdir -p "${MOUNT_POINT}"

# Detect partitions
PARTS=$(kpartx -av "${DISK_IMAGE}" 2>/dev/null | awk '{print $3}')

for PART in ${PARTS}; do
    PART_DEV="/dev/mapper/${PART}"
    PART_MOUNT="${MOUNT_POINT}/${PART}"
    mkdir -p "${PART_MOUNT}"

    mount -o ro,noexec,nosuid "${PART_DEV}" "${PART_MOUNT}" 2>/dev/null || {
        log "Could not mount ${PART_DEV} (may be swap/LVM)"
        continue
    }

    log "Mounted ${PART_DEV} at ${PART_MOUNT}"

    # 2. Run ClamAV scan
    clamscan -r --infected --no-summary "${PART_MOUNT}" 2>&1 | tee -a "${SCAN_LOG}"
    CLAM_EXIT=${PIPESTATUS[0]}

    if [ ${CLAM_EXIT} -eq 1 ]; then
        log "CRITICAL: Malware detected in ${PART_DEV}"
        # Do NOT proceed with recovery — quarantine this backup
    elif [ ${CLAM_EXIT} -eq 0 ]; then
        log "CLEAN: No malware detected in ${PART_DEV}"
    fi

    # 3. Check for known ransomware artifacts
    log "Checking for ransomware indicators..."
    # Look for ransom notes
    find "${PART_MOUNT}" -maxdepth 3 \( \
        -iname "readme.txt" -o -iname "decrypt*" -o \
        -iname "how_to_recover*" -o -iname "ransom*" -o \
        -iname "restore_files*" \) \
        -newer "${PART_MOUNT}/etc/hostname" 2>/dev/null | tee -a "${SCAN_LOG}"

    # Look for mass-encrypted files (high entropy file extensions)
    SUSPICIOUS_EXTS=$(find "${PART_MOUNT}" -maxdepth 4 -type f | \
        awk -F. '{print $NF}' | sort | uniq -c | sort -rn | \
        head -5 | awk '$1 > 100 && length($2) > 5 {print $2}')

    if [ -n "${SUSPICIOUS_EXTS}" ]; then
        log "WARNING: Unusual file extensions with high count: ${SUSPICIOUS_EXTS}"
    fi

    # 4. Unmount
    umount "${PART_MOUNT}" 2>/dev/null
done

kpartx -d "${DISK_IMAGE}" 2>/dev/null
log "=== Scan complete ==="
```

### 6.4 Clean Room Recovery — Isolated Network for Verification

Recovered VMs must be brought online in an isolated network before connecting to production or DR workload networks. This prevents a compromised VM from attacking other recovered systems or the DR infrastructure.

**Clean room network architecture:**

```
DR Site Network
┌───────────────────────────────────────────┐
│                                           │
│  DR Workload Network (10.2.0.0/16)       │
│  ┌─────────┐  ┌─────────┐               │
│  │ Verified │  │ Verified │               │
│  │   VMs    │  │   VMs    │   ← Move here │
│  └─────────┘  └─────────┘     AFTER scan  │
│        ▲                                  │
│        │ (manual network move)            │
│        │                                  │
│  Clean Room Network (10.99.0.0/24)       │
│  ┌─────────┐  ┌─────────┐               │
│  │ Restored │  │ Restored │   ← Restore   │
│  │  VM (!)  │  │  VM (!)  │     HERE first │
│  └─────────┘  └─────────┘               │
│  No internet │ No access to DR workloads  │
│  Only scan   │ server has access          │
└───────────────────────────────────────────┘
```

```bash
# Create clean room VLAN on DR Proxmox
# /etc/network/interfaces (on DR host)
auto vmbr99
iface vmbr99 inet static
    address 10.99.0.1/24
    bridge-ports none
    bridge-stp off
    bridge-fd 0
    # This bridge has NO uplink — fully isolated

# Firewall rules for clean room
# /etc/pve/firewall/cleanroom.fw
[RULES]
# Allow only the scan server to reach clean room VMs
IN ACCEPT -source 10.99.0.254/32 -p tcp -dport 22
IN ACCEPT -source 10.99.0.254/32 -p tcp -dport 443
# Block everything else
IN DROP
OUT DROP
```

### 6.5 Configuration Validation Post-Recovery

After restoring VMs, validate that security baselines are still enforced. Configuration drift during recovery is common — especially when restoring from older backups.

```bash
#!/bin/bash
# /usr/local/bin/dr-config-validate.sh
# Validate security configuration of recovered VM
set -euo pipefail

VM_IP="$1"
LOG="/var/log/dr-config-validate.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG}"; }

log "=== Validating security configuration for ${VM_IP} ==="

# 1. Check SSH hardening
ssh root@"${VM_IP}" 'sshd -T' | while IFS= read -r line; do
    case "${line}" in
        "permitrootlogin yes")
            log "FAIL: Root login permitted" ;;
        "passwordauthentication yes")
            log "WARN: Password authentication enabled" ;;
        "protocol 1")
            log "CRITICAL: SSH protocol 1 enabled" ;;
    esac
done

# 2. Check firewall status
ssh root@"${VM_IP}" 'systemctl is-active firewalld ufw iptables 2>/dev/null' | \
    tee -a "${LOG}"

# 3. Check for unexpected listening services
log "Listening services:"
ssh root@"${VM_IP}" 'ss -tlnp' | tee -a "${LOG}"

# 4. Check patch level
ssh root@"${VM_IP}" 'apt list --upgradable 2>/dev/null | wc -l' | \
    xargs -I{} log "Pending updates: {}"

# 5. Verify critical file permissions
ssh root@"${VM_IP}" '
    stat -c "%a %U %G %n" /etc/shadow /etc/sudoers /root/.ssh 2>/dev/null
' | tee -a "${LOG}"

# 6. Check for unauthorized SSH keys
ssh root@"${VM_IP}" '
    for user_home in /home/* /root; do
        if [ -f "${user_home}/.ssh/authorized_keys" ]; then
            echo "=== ${user_home}/.ssh/authorized_keys ==="
            cat "${user_home}/.ssh/authorized_keys"
        fi
    done
' | tee -a "${LOG}"

# 7. Verify TLS certificates are not expired
ssh root@"${VM_IP}" '
    for cert in /etc/ssl/certs/*.pem /etc/pki/tls/certs/*.pem; do
        [ -f "${cert}" ] || continue
        expiry=$(openssl x509 -enddate -noout -in "${cert}" 2>/dev/null | cut -d= -f2)
        if [ -n "${expiry}" ]; then
            exp_epoch=$(date -d "${expiry}" +%s 2>/dev/null)
            now_epoch=$(date +%s)
            if [ "${exp_epoch}" -lt "${now_epoch}" ]; then
                echo "EXPIRED: ${cert} (${expiry})"
            fi
        fi
    done
'| tee -a "${LOG}"

log "=== Validation complete for ${VM_IP} ==="
```

---

## 7. DR Testing Security

### 7.1 Penetration Testing DR Procedures

DR infrastructure should be included in annual penetration testing scope. Specific test scenarios:

1. **Attempt to access DR site from production using production credentials.** This validates credential isolation. If the penetration tester can SSH into DR hosts using production SSH keys or authenticate to DR Proxmox using production LDAP credentials, credential isolation has failed.

2. **Attempt to delete or corrupt backups from a compromised production host.** Simulate an attacker who has root on a production node and test whether they can reach the DR PBS, authenticate, and delete backups.

3. **Attempt to intercept replication traffic.** Position a packet capture on the WAN link between sites (or the WireGuard tunnel) and verify that traffic is encrypted and that cleartext data is not visible.

4. **Attempt to trigger false failover.** If monitoring systems trigger automated failover, test whether injecting false health-check failures triggers an actual failover event.

5. **Attempt to access break-glass credentials.** Test the physical security of break-glass credential storage — can the pen tester social-engineer access to the sealed envelope?

### 7.2 Tabletop Exercises — Security-Focused Scenarios

Tabletop exercises validate decision-making and procedures without infrastructure impact. Security-focused scenarios:

**Scenario 1: Ransomware with backup destruction**
> At 02:00 UTC, the SOC detects ransomware encrypting production file servers. Investigation reveals the attacker has been present for 14 days. The attacker has deleted all backups from the production PBS. Replication to the DR PBS ran during the 14-day dwell time, meaning some replicated backups may contain the attacker's persistence mechanisms. The AD domain controller shows signs of compromise. Walk through: Which backups are safe to restore? How do you authenticate to DR systems without AD? How do you verify recovery integrity?

**Scenario 2: DR site compromise**
> During a routine DR test, the DR team discovers that the DR Proxmox web UI shows an unauthorized user account with Administrator privileges, created 30 days ago. The DR PBS shows backup verification jobs that were not scheduled by the team. Walk through: Is the DR site compromised? Can you trust any data at the DR site? How do you rebuild DR trust?

**Scenario 3: Insider threat — DR administrator**
> A DR administrator who is being terminated has root access to both production and DR systems. They have copies of the DR runbook, network diagrams, and know the break-glass credentials. Walk through: What immediate actions are needed? How do you rotate credentials across both sites without causing an outage?

### 7.3 Technical DR Tests — Failover/Failback with Security Validation

Every DR test must include a security validation phase. The test is not complete until security is verified at the DR site:

```
DR Test Checklist (Security Sections):
═══════════════════════════════════════

Pre-Failover:
□ Run dr-preflight-security.sh — all checks pass
□ Verify break-glass credentials work (test login)
□ Verify out-of-band communication works

During Failover:
□ Document exact credential used for each step
□ Verify firewall rules active at DR site
□ Verify monitoring and alerting active at DR site
□ Check for unauthorized processes/connections on DR hosts

Post-Failover:
□ Run dr-config-validate.sh on all recovered VMs
□ Run dr-malware-scan.sh on all recovered disk images
□ Verify network segmentation at DR site matches production policy
□ Test that production-site credentials do NOT work at DR site
□ Verify SIEM/syslog collection at DR site
□ Run vulnerability scan of DR-hosted services

Post-Failback:
□ Verify all temporary firewall rules removed
□ Verify all break-glass sessions terminated
□ Verify no data remained at DR site after failback
□ Rotate any credentials used during the test
□ Document security findings
```

### 7.4 Testing Credential Rotation During DR

During DR tests, validate that credential rotation procedures work under pressure:

```bash
#!/bin/bash
# /usr/local/bin/dr-credential-rotation.sh
# Rotate DR credentials after a DR event or test
set -euo pipefail

LOG="/var/log/dr-credential-rotation.log"
log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG}"; }

log "=== Starting DR credential rotation ==="

# 1. Rotate Proxmox root password on DR hosts
for host in pve-dr-01 pve-dr-02; do
    NEW_PASS=$(openssl rand -base64 24)
    ssh root@"${host}" "echo 'root:${NEW_PASS}' | chpasswd"
    log "Rotated root password on ${host}"
    # Store in Vault
    vault kv put "dr/proxmox/hosts/${host}" password="${NEW_PASS}"
done

# 2. Rotate PBS API tokens
NEW_TOKEN_SECRET=$(proxmox-backup-manager user generate-token repl-push@pbs repl-token --force 2>&1 | \
    grep "value:" | awk '{print $2}')
log "Rotated PBS replication token"
vault kv put dr/pbs/replication token="${NEW_TOKEN_SECRET}"

# 3. Rotate SSH keys
ssh-keygen -t ed25519 -f /root/.ssh/zfs-repl-key-new -N "" -C "zfs-repl-$(date +%Y%m%d)"
for host in pve-dr-01 pve-dr-02; do
    ssh-copy-id -i /root/.ssh/zfs-repl-key-new.pub root@"${host}"
done
mv /root/.ssh/zfs-repl-key /root/.ssh/zfs-repl-key.old
mv /root/.ssh/zfs-repl-key-new /root/.ssh/zfs-repl-key
mv /root/.ssh/zfs-repl-key-new.pub /root/.ssh/zfs-repl-key.pub
log "Rotated ZFS replication SSH key"

# 4. Rotate WireGuard keys
NEW_PRIV=$(wg genkey)
NEW_PUB=$(echo "${NEW_PRIV}" | wg pubkey)
log "Generated new WireGuard keypair — manual config update required"
log "New public key: ${NEW_PUB}"

# 5. Rotate break-glass passwords
for account in dr-breakglass@pam; do
    NEW_BG_PASS=$(openssl rand -base64 32)
    pveum passwd "${account}" <<< "${NEW_BG_PASS}"
    log "Rotated break-glass account: ${account}"
    log "ACTION REQUIRED: Update physical safe with new password"
done

log "=== Credential rotation complete ==="
log "ACTION REQUIRED: Update DR runbook with new credential references"
```

### 7.5 Testing Detection Capabilities at DR Site

Verify that security monitoring works at the DR site:

- **SIEM collection** — generate test events and verify they appear in the DR SIEM.
- **IDS/IPS** — run controlled scans against DR-hosted services and verify alerts fire.
- **File integrity monitoring** — modify a monitored file and verify the alert.
- **Log forwarding** — verify that DR host logs reach the central log aggregator.

### 7.6 Documenting Security Gaps Found During DR Tests

Every DR test should produce a security findings report. Template:

```markdown
# DR Test Security Findings Report

**Test date:** YYYY-MM-DD
**Test type:** Full failover / Partial failover / Tabletop
**Participants:** [names]

## Findings

### Finding 1: [Title]
- **Severity:** CRITICAL / HIGH / MEDIUM / LOW
- **Description:** [What was found]
- **Impact:** [What could happen if exploited]
- **Affected systems:** [System list]
- **Recommendation:** [Fix]
- **Remediation deadline:** [Date based on severity]
- **Owner:** [Person responsible]

## Statistics
- Total findings: X
- CRITICAL: X (remediate within 48h)
- HIGH: X (remediate within 2 weeks)
- MEDIUM: X (remediate within 30 days)
- LOW: X (remediate within 90 days)

## Comparison to Previous Test
- New findings: X
- Resolved since last test: X
- Recurring findings: X (list with escalation note)
```

---

## 8. Cloud DR Security

### 8.1 AWS Elastic Disaster Recovery — Security Configuration

AWS Elastic Disaster Recovery (AWS DRS, formerly CloudEndure DR) replicates on-premises servers to AWS for failover. Security configuration:

**IAM policy for DRS (least privilege):**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "DRSReplicationMinimal",
            "Effect": "Allow",
            "Action": [
                "drs:*",
                "ec2:CreateSecurityGroup",
                "ec2:CreateTags",
                "ec2:DescribeInstances",
                "ec2:DescribeSecurityGroups",
                "ec2:DescribeSubnets",
                "ec2:DescribeVpcs",
                "ec2:RunInstances",
                "ec2:StopInstances",
                "ec2:TerminateInstances",
                "ec2:CreateVolume",
                "ec2:AttachVolume",
                "ec2:DetachVolume",
                "ec2:DeleteVolume",
                "ec2:CreateSnapshot",
                "ec2:DeleteSnapshot",
                "ec2:DescribeSnapshots",
                "ec2:DescribeVolumes"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:RequestedRegion": "eu-west-1"
                }
            }
        },
        {
            "Sid": "DRSKMSAccess",
            "Effect": "Allow",
            "Action": [
                "kms:CreateGrant",
                "kms:Decrypt",
                "kms:DescribeKey",
                "kms:Encrypt",
                "kms:GenerateDataKey*",
                "kms:ReEncrypt*"
            ],
            "Resource": "arn:aws:kms:eu-west-1:ACCOUNT:key/KEY-ID"
        }
    ]
}
```

**Network security for DRS:**

- **Replication subnet:** Dedicated private subnet in the DR VPC. No internet gateway. Replication traffic flows over AWS PrivateLink or VPN.
- **Staging area:** The staging area (where replication data lands before failover) must be in a private subnet with no inbound access.
- **Security groups:** Staging instances should have security groups allowing only the DRS replication agent port (TCP 1500) from the source IP range.
- **EBS encryption:** Enable default EBS encryption in the DR region. All replicated volumes are encrypted with a customer-managed KMS key (CMK), not the AWS-managed default key.

```bash
# Enable default EBS encryption in DR region
aws ec2 enable-ebs-encryption-by-default --region eu-west-1

# Set default KMS key
aws ec2 modify-ebs-default-kms-key-id \
  --kms-key-id arn:aws:kms:eu-west-1:ACCOUNT:key/KEY-ID \
  --region eu-west-1
```

**CloudTrail and GuardDuty:**

```bash
# Enable CloudTrail in DR region
aws cloudtrail create-trail \
  --name dr-region-trail \
  --s3-bucket-name dr-audit-logs \
  --is-multi-region-trail \
  --enable-log-file-validation \
  --kms-key-id arn:aws:kms:eu-west-1:ACCOUNT:key/TRAIL-KEY-ID

aws cloudtrail start-logging --name dr-region-trail

# Enable GuardDuty in DR region
aws guardduty create-detector \
  --enable \
  --finding-publishing-frequency FIFTEEN_MINUTES \
  --region eu-west-1
```

### 8.2 Azure Site Recovery — Network Security and Identity Management

Azure Site Recovery (ASR) provides DR for on-premises VMs to Azure and Azure-to-Azure:

**Identity security:**

- Use a dedicated Azure AD (Entra ID) service principal for ASR with a custom role — not the built-in Contributor role.
- Enable Conditional Access policies requiring MFA for any identity accessing the DR resource group.
- Use Managed Identity for the ASR configuration server where possible to eliminate stored credentials.

**Network security:**

- Deploy recovered VMs into a dedicated VNet with NSG rules mirroring on-premises firewall policies.
- Use Azure Private Link for the Recovery Services vault — no public endpoint.
- If replicating over the internet (not ExpressRoute/VPN), verify that ASR uses TLS for all data transfer (it does by default, but verify with network captures during DR tests).
- Enable Azure DDoS Protection Standard on the DR VNet if recovered services will be internet-facing.

**Encryption:**

- Recovery Services vault supports customer-managed keys (CMK) for encryption at rest. Configure during vault creation — changing later requires re-protecting all VMs.
- Use Azure Disk Encryption (ADE) or server-side encryption with CMK for all recovered VM disks.

### 8.3 GCP Cloud DR Patterns

GCP does not have a direct equivalent to AWS DRS or Azure ASR. DR patterns involve:

- **Persistent Disk snapshots** replicated across regions with CMEK (Customer-Managed Encryption Keys).
- **VM image export/import** with Compute Engine — secure the image storage bucket with IAM and CMEK.
- **Actifio GO** (Google-acquired) for backup and DR — configure with GCP IAM service accounts and VPC Service Controls.
- **GKE multi-cluster** for containerized workloads — use Anthos Config Management for consistent security policies across clusters in different regions.

**VPC Service Controls** for DR data protection:

```bash
# Create a service perimeter around DR resources
gcloud access-context-manager perimeters create dr-perimeter \
  --title="DR Resources Perimeter" \
  --resources="projects/DR-PROJECT-NUMBER" \
  --restricted-services="compute.googleapis.com,storage.googleapis.com" \
  --access-levels="accessPolicies/POLICY/accessLevels/dr-team-only" \
  --policy=POLICY_ID
```

### 8.4 Hybrid DR — On-Premises to Cloud Security Considerations

When DR targets a cloud provider while production remains on-premises:

1. **Data in transit:** Replication traffic traverses the internet (even with VPN). Ensure encryption is end-to-end, not just VPN-layer. If the VPN terminates at a cloud gateway and traffic is cleartext within the cloud VPC, an attacker with cloud-side access sees replication data in plaintext.

2. **Identity boundary:** On-premises AD and cloud IAM are separate identity systems. Plan for identity federation (AD FS, Azure AD Connect, Google Cloud Directory Sync) at the DR site, or use local cloud IAM accounts with pre-provisioned access.

3. **Key management boundary:** On-premises KMS keys must be available in the cloud for decryption during recovery. Options: replicate keys to cloud KMS (AWS KMS, Azure Key Vault, GCP Cloud KMS) or use BYOK (Bring Your Own Key). Understand that BYOK keys are still wrapped by the cloud provider's key hierarchy — they are not truly independent.

4. **Compliance boundary:** Data replicated to a cloud provider is subject to that provider's data processing agreement. Verify that the cloud region satisfies data residency requirements (GDPR Article 44-49 for EU data, LGPD for Brazil, PIPL for China).

### 8.5 Multi-Cloud DR — Avoiding Vendor Lock-in While Maintaining Security

Multi-cloud DR (e.g., production on AWS, DR on Azure) adds complexity without proportional benefit unless the threat model explicitly includes cloud provider failure or government seizure:

- **Security policy translation:** AWS Security Groups, Azure NSGs, and GCP firewall rules use different models. A direct translation is error-prone. Use infrastructure-as-code (Terraform) with provider-specific modules validated by security tests.
- **Identity mapping:** IAM policies across clouds are fundamentally different. Maintain separate, independently managed identity configurations per cloud.
- **Encryption key portability:** Keys in AWS KMS cannot be exported to Azure Key Vault. Design encryption so that data can be decrypted with keys available at the DR cloud. This may mean encrypting at the application layer with portable keys (e.g., Vault Transit engine).

### 8.6 Cloud DR Compliance — Data Residency and Regulatory Requirements

| Regulation | DR Requirement | Cloud Consideration |
|---|---|---|
| GDPR (EU) | Data processor agreement required; transfer safeguards per Chapter V | Cloud region must be in EU/EEA or have adequacy decision; Standard Contractual Clauses (SCCs) for non-EU regions |
| HIPAA (US) | Business Associate Agreement (BAA) with cloud provider | AWS, Azure, GCP all offer BAAs; verify DR-specific services are covered |
| PCI-DSS v4.0 | DR environment in scope if it stores/processes/transmits cardholder data | Cloud DR environment must pass PCI-DSS assessment; SAQ or QSA audit |
| LGPD (Brazil) | Data transfer restrictions per Art. 33 | Brazilian cloud region required for DR of LGPD-covered data |
| NIS2 (EU) | Business continuity management per Art. 21(2)(c) | Cloud DR must be documented in the BCP; notification obligations apply to DR events |

---

## 9. Compliance and Audit

### 9.1 DR Compliance Requirements by Framework

**PCI-DSS v4.0 — Requirement 12.10 (Incident Response):**
- Requirement 12.10.2: DR plan must be reviewed at least annually and updated after significant changes.
- Requirement 12.10.4: Personnel with DR responsibilities must be trained at least annually.
- Requirement 12.10.5: DR plan must include response to detection of unauthorized activity.
- Requirement 9.5.1: Backup media must be stored securely with access limited to authorized personnel. This applies to DR site physical media.

**HIPAA — 45 CFR §164.308(a)(7) (Contingency Plan):**
- §164.308(a)(7)(i): Establish and implement policies and procedures for responding to an emergency.
- §164.308(a)(7)(ii)(A): Data backup plan (required).
- §164.308(a)(7)(ii)(B): Disaster recovery plan (required).
- §164.308(a)(7)(ii)(C): Emergency mode operation plan (required).
- §164.308(a)(7)(ii)(D): Testing and revision procedures (addressable).
- §164.308(a)(7)(ii)(E): Applications and data criticality analysis (addressable).
- Note: "Addressable" does not mean "optional" — it means you must implement or document why an equivalent alternative is used.

**SOX Section 404 — Internal Controls Over Financial Reporting:**
- DR plans for systems that process financial data must be documented and tested.
- Auditors require evidence that DR tests were conducted, including dates, participants, results, and remediation of findings.
- IT General Controls (ITGC) audits examine backup procedures, off-site storage, and recovery testing.

**ISO 22301:2019 — Business Continuity Management Systems:**
- Clause 8.4: Business continuity plans and procedures.
- Clause 8.5: Exercise and testing — requires exercising at planned intervals with post-exercise reports.
- Clause 8.6: Evaluation of BCP documentation after exercises.
- Clause 9.1: Monitoring, measurement, analysis, and evaluation — DR metrics must be tracked.
- Clause 10.1: Nonconformity and corrective action — DR test failures must trigger corrective action.

### 9.2 DR Testing Documentation for Auditors

Auditors need specific documentation from each DR test. Organize DR test evidence into an auditable package:

```
DR-Test-YYYY-MM-DD/
├── 01-test-plan.pdf              # Pre-approved test plan with scope and objectives
├── 02-pre-test-checklist.pdf      # Completed pre-flight checks
├── 03-test-execution-log.pdf      # Timestamped log of all actions taken
├── 04-screenshots/                # Evidence of successful failover
│   ├── dr-site-vms-running.png
│   ├── dns-cutover-verified.png
│   └── monitoring-active.png
├── 05-rto-rpo-measurements.pdf    # Actual RTO/RPO vs. targets
├── 06-security-validation.pdf     # Output of security validation scripts
├── 07-findings-report.pdf         # Findings with severity and remediation
├── 08-remediation-tracking.xlsx   # Status of remediation items
├── 09-participant-sign-off.pdf    # Signatures confirming test completion
└── 10-lessons-learned.pdf         # Post-test review notes
```

### 9.3 Evidence Collection During DR Events

During an actual DR event (not a test), evidence collection serves both compliance and forensic purposes:

- **Preserve timeline** — all actions must be logged with UTC ISO 8601 timestamps.
- **Preserve original state** — before modifying any system, capture its current state (screenshots, configuration dumps, network captures).
- **Maintain chain of custody** — if the DR event is triggered by a security incident, digital evidence must be handled per forensic standards (ISO/IEC 27037).
- **Separate evidence storage** — store evidence on systems independent from both production and DR infrastructure.

### 9.4 Chain of Custody During Recovery

When restoring from backups during a DR event, maintain chain of custody:

1. **Record which backup was selected for restore** — snapshot ID, timestamp, storage location.
2. **Record who authorized the restore** — name, role, timestamp.
3. **Record integrity verification results** — hash values, verification script output.
4. **Record any modifications made to restored data** — configuration changes, credential updates.
5. **Hash all restored artifacts** — SHA-256 of restored disk images before and after any modification.

```bash
# Generate chain-of-custody manifest
sha256sum /mnt/pbs-dr-datastore/dr-incoming/vm/100/*.blob > \
  /var/log/dr-evidence/restore-manifest-$(date +%Y%m%d-%H%M%S).sha256
```

### 9.5 Regulatory Notification During DR Events

Some regulations require notification during DR events:

- **NIS2 (EU):** Significant incidents must be reported to the competent authority within 24 hours (early warning), 72 hours (incident notification), and 1 month (final report). A DR failover triggered by a cyber incident may qualify.
- **GDPR:** If a DR event involves a personal data breach, notify the supervisory authority within 72 hours per Article 33. If the breach is likely to result in high risk to individuals, notify affected data subjects per Article 34.
- **HIPAA:** Notify HHS within 60 days of discovering a breach affecting 500+ individuals. For breaches affecting fewer than 500, log and report annually.
- **PCI-DSS:** Notify the payment card brands and acquiring bank per the incident response plan.

### 9.6 DR Plan Review and Approval Process

The DR plan must be a living document with a formal review cycle:

- **Annual review** — minimum. More frequently if significant infrastructure changes occur.
- **Review triggers** — major infrastructure change, significant security incident, organizational restructuring, new compliance requirement, DR test failure.
- **Approval authority** — DR plan changes must be approved by the CISO or delegated security authority, not solely by the infrastructure team.
- **Version control** — DR plans should be version-controlled (git), with change history and signed-off diffs.
- **Distribution control** — DR plans contain sensitive information (network diagrams, credentials, procedures). Limit distribution and track copies.

---

## 10. Lab: Secure DR Implementation

This lab implements a complete secure DR environment with Proxmox VE, encrypted replication, automated failover with security validation, and a ransomware recovery drill.

### 10.1 Lab Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                        LAB ENVIRONMENT                            │
│                                                                   │
│  PRODUCTION SITE                    DR SITE                       │
│  ┌────────────────┐                ┌────────────────┐             │
│  │ pve-prod-01    │                │ pve-dr-01      │             │
│  │ 172.16.1.10    │                │ 172.16.2.10    │             │
│  │ Proxmox VE 8.x │                │ Proxmox VE 8.x │             │
│  │                │                │                │             │
│  │ VMs:           │                │ VMs (standby): │             │
│  │  web-01 (100)  │                │  (restored     │             │
│  │  db-01  (101)  │                │   during DR)   │             │
│  │  app-01 (102)  │                │                │             │
│  └───────┬────────┘                └───────┬────────┘             │
│          │                                  │                     │
│  ┌───────┴────────┐                ┌───────┴────────┐             │
│  │ pbs-prod       │                │ pbs-dr         │             │
│  │ 172.16.1.20    │═══WireGuard═══►│ 172.16.2.20    │             │
│  │ PBS 3.x        │  192.168.100   │ PBS 3.x        │             │
│  │ Datastore:     │  .1/30 ↔ .2/30│ Datastore:     │             │
│  │  production    │                │  dr-incoming   │             │
│  └────────────────┘                └────────────────┘             │
│                                                                   │
│  CLEAN ROOM (DR Site)                                             │
│  ┌────────────────┐                                               │
│  │ vmbr99         │  10.99.0.0/24 — isolated scan network        │
│  │ scan-server    │  10.99.0.254 — ClamAV, verification tools    │
│  └────────────────┘                                               │
└───────────────────────────────────────────────────────────────────┘
```

### 10.2 Step 1 — Configure WireGuard Tunnel Between Sites

```bash
# === ON pbs-prod (172.16.1.20) ===
apt install wireguard -y

# Generate keypair
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key
chmod 600 /etc/wireguard/private.key

PROD_PRIVKEY=$(cat /etc/wireguard/private.key)
PROD_PUBKEY=$(cat /etc/wireguard/public.key)
```

```bash
# === ON pbs-dr (172.16.2.20) ===
apt install wireguard -y

wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key
chmod 600 /etc/wireguard/private.key

DR_PRIVKEY=$(cat /etc/wireguard/private.key)
DR_PUBKEY=$(cat /etc/wireguard/public.key)
```

```ini
# /etc/wireguard/wg-repl.conf — pbs-prod
[Interface]
PrivateKey = <PROD_PRIVKEY>
Address = 192.168.100.1/30
ListenPort = 51820

PostUp = iptables -A INPUT -i wg-repl -p tcp --dport 8007 -j DROP
PostUp = iptables -A OUTPUT -o wg-repl -p tcp --dport 8007 -j ACCEPT
PostDown = iptables -D INPUT -i wg-repl -p tcp --dport 8007 -j DROP
PostDown = iptables -D OUTPUT -o wg-repl -p tcp --dport 8007 -j ACCEPT

[Peer]
PublicKey = <DR_PUBKEY>
Endpoint = <DR_PUBLIC_IP>:51820
AllowedIPs = 192.168.100.2/32
PersistentKeepalive = 25
```

```ini
# /etc/wireguard/wg-repl.conf — pbs-dr
[Interface]
PrivateKey = <DR_PRIVKEY>
Address = 192.168.100.2/30
ListenPort = 51820

PostUp = iptables -A INPUT -i wg-repl -p tcp --dport 8007 -j ACCEPT
PostUp = iptables -A INPUT -i wg-repl -p tcp ! --dport 8007 -j DROP
PostDown = iptables -D INPUT -i wg-repl -p tcp --dport 8007 -j ACCEPT
PostDown = iptables -D INPUT -i wg-repl -p tcp ! --dport 8007 -j DROP

[Peer]
PublicKey = <PROD_PUBKEY>
Endpoint = <PROD_PUBLIC_IP>:51820
AllowedIPs = 192.168.100.1/32
PersistentKeepalive = 25
```

```bash
# Start on both sides
systemctl enable --now wg-quick@wg-repl

# Verify
ping -c 3 192.168.100.2  # from prod
wg show wg-repl           # check handshake timestamp
```

### 10.3 Step 2 — Configure PBS Encrypted Replication

```bash
# === ON pbs-dr ===

# Create encrypted datastore
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
  --key-size 512 --hash sha512 /dev/sdb1
cryptsetup luksOpen /dev/sdb1 pbs-dr-encrypted
mkfs.ext4 /dev/mapper/pbs-dr-encrypted
mkdir -p /mnt/pbs-dr-datastore
mount /dev/mapper/pbs-dr-encrypted /mnt/pbs-dr-datastore

# Create PBS datastore
proxmox-backup-manager datastore create dr-incoming \
  --path /mnt/pbs-dr-datastore \
  --gc-schedule "daily 03:00" \
  --prune-schedule "daily 04:00" \
  --keep-daily 7 --keep-weekly 4 --keep-monthly 12 \
  --verify-new true

# Create replication user with minimal permissions
proxmox-backup-manager user create repl-push@pbs
proxmox-backup-manager acl update /datastore/dr-incoming \
  DatastoreBackup --auth-id repl-push@pbs

# Generate API token (save the output securely)
proxmox-backup-manager user generate-token repl-push@pbs repl-token
# Output: value: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Get server fingerprint
proxmox-backup-manager cert info | grep Fingerprint
# Output: Fingerprint (sha256): aa:bb:cc:...
```

```bash
# === ON pbs-prod ===

# Configure remote target (via WireGuard tunnel IP)
proxmox-backup-manager remote create dr-site \
  --host 192.168.100.2 \
  --port 8007 \
  --auth-id "repl-push@pbs!repl-token" \
  --password "<API_TOKEN_SECRET>" \
  --fingerprint "<DR_PBS_FINGERPRINT>"

# Create sync job — hourly, do NOT remove vanished
proxmox-backup-manager sync-job create prod-to-dr \
  --remote dr-site \
  --remote-store dr-incoming \
  --store production \
  --schedule "hourly" \
  --remove-vanished false

# Generate client-side encryption key
proxmox-backup-client key create --kdf scrypt \
  /etc/pbs-encryption/master-key.json

# CRITICAL: copy encryption key to offline storage
# This key is NOT stored on the DR site
# Without it, DR backups are unrecoverable

# Trigger initial sync
proxmox-backup-manager sync-job run prod-to-dr
```

### 10.4 Step 3 — Implement Failover Automation with Security Checks

```bash
#!/bin/bash
# /usr/local/bin/dr-failover.sh
# Complete DR failover procedure with embedded security validation
set -euo pipefail

DR_PVE_HOST="172.16.2.10"
DR_PBS_HOST="192.168.100.2"
DR_PBS_STORE="dr-incoming"
CLEAN_ROOM_BRIDGE="vmbr99"
PROD_BRIDGE="vmbr0"
LOG="/var/log/dr-failover-$(date +%Y%m%d-%H%M%S).log"
VMS_TO_RESTORE=(100 101 102)

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${LOG}"; }

die() { log "FATAL: $1"; exit 1; }

# ============================
# PHASE 1: PRE-FLIGHT SECURITY
# ============================
log "=== PHASE 1: Pre-flight Security Checks ==="

# Run pre-flight script
/usr/local/bin/dr-preflight-security.sh || \
    die "Pre-flight security checks failed. Aborting failover."

# Verify break-glass credentials
log "Testing break-glass account..."
curl -sk -X POST "https://${DR_PVE_HOST}:8006/api2/json/access/ticket" \
    -d "username=dr-breakglass@pam&password=${DR_BREAKGLASS_PASS}" | \
    jq -e '.data.ticket' > /dev/null || \
    die "Break-glass account authentication failed"
log "Break-glass account verified."

# ============================
# PHASE 2: RESTORE VMs
# ============================
log "=== PHASE 2: Restoring VMs to Clean Room ==="

for VMID in "${VMS_TO_RESTORE[@]}"; do
    log "Identifying latest backup for VM ${VMID}..."

    # Find latest backup snapshot
    LATEST_SNAP=$(ssh root@"${DR_PVE_HOST}" \
        "proxmox-backup-client snapshot list \
            --repository localhost:${DR_PBS_STORE} \
            --output-format json 2>/dev/null" | \
        jq -r "[.[] | select(.\"backup-id\" == \"${VMID}\")] | sort_by(.\"backup-time\") | last | .\"backup-id\" + \"/\" + (.\"backup-time\" | tostring)")

    log "Restoring VM ${VMID} from snapshot: ${LATEST_SNAP}"

    # Restore to clean room network (vmbr99)
    ssh root@"${DR_PVE_HOST}" \
        "qmrestore /mnt/pbs-dr-datastore/${DR_PBS_STORE}/vm/${VMID}/ ${VMID} \
            --storage local-zfs \
            --force true \
            --unique true" 2>&1 | tee -a "${LOG}"

    # Move to clean room bridge
    ssh root@"${DR_PVE_HOST}" \
        "qm set ${VMID} --net0 virtio,bridge=${CLEAN_ROOM_BRIDGE}"

    log "VM ${VMID} restored to clean room network."
done

# ============================
# PHASE 3: INTEGRITY SCAN
# ============================
log "=== PHASE 3: Integrity Verification and Malware Scan ==="

for VMID in "${VMS_TO_RESTORE[@]}"; do
    log "Scanning VM ${VMID}..."

    # Get disk path
    DISK_PATH=$(ssh root@"${DR_PVE_HOST}" \
        "pvesm path local-zfs:vm-${VMID}-disk-0 2>/dev/null")

    # Run malware scan (using scan server in clean room)
    ssh root@"${DR_PVE_HOST}" \
        "/usr/local/bin/dr-malware-scan.sh '${DISK_PATH}'" 2>&1 | tee -a "${LOG}"

    SCAN_RESULT=$?
    if [ ${SCAN_RESULT} -ne 0 ]; then
        log "CRITICAL: Malware detected in VM ${VMID}. Quarantining."
        ssh root@"${DR_PVE_HOST}" "qm set ${VMID} --lock backup"
        continue
    fi

    log "VM ${VMID} scan clean."
done

# ============================
# PHASE 4: MOVE TO PRODUCTION
# ============================
log "=== PHASE 4: Moving Clean VMs to DR Production Network ==="

for VMID in "${VMS_TO_RESTORE[@]}"; do
    # Check if VM is locked (quarantined)
    IS_LOCKED=$(ssh root@"${DR_PVE_HOST}" \
        "qm config ${VMID} | grep -c '^lock:'" || true)

    if [ "${IS_LOCKED}" -gt 0 ]; then
        log "SKIPPING VM ${VMID} — quarantined (malware detected)"
        continue
    fi

    # Move to production bridge
    ssh root@"${DR_PVE_HOST}" \
        "qm set ${VMID} --net0 virtio,bridge=${PROD_BRIDGE}"

    # Start VM
    ssh root@"${DR_PVE_HOST}" "qm start ${VMID}"
    log "VM ${VMID} started on DR production network."
done

# ============================
# PHASE 5: POST-FAILOVER SECURITY
# ============================
log "=== PHASE 5: Post-Failover Security Validation ==="

sleep 60  # Allow VMs to boot

for VMID in "${VMS_TO_RESTORE[@]}"; do
    VM_IP=$(ssh root@"${DR_PVE_HOST}" \
        "qm guest cmd ${VMID} network-get-interfaces | \
         jq -r '.[].\"ip-addresses\"[]? | select(.\"ip-address-type\"==\"ipv4\") | .\"ip-address\"' | \
         grep -v '^127\.' | head -1")

    if [ -n "${VM_IP}" ]; then
        log "Validating security config for VM ${VMID} (${VM_IP})..."
        /usr/local/bin/dr-config-validate.sh "${VM_IP}" 2>&1 | tee -a "${LOG}"
    else
        log "WARNING: Could not determine IP for VM ${VMID}"
    fi
done

# ============================
# PHASE 6: NETWORK CUTOVER
# ============================
log "=== PHASE 6: DNS and Network Cutover ==="

# Activate DR firewall rules
ssh root@"${DR_PVE_HOST}" "pve-firewall start"
log "DR firewall activated."

# DNS failover (example with Cloudflare)
/usr/local/bin/dr-dns-failover.sh 2>&1 | tee -a "${LOG}"
log "DNS cutover complete."

log "========================================"
log "DR FAILOVER COMPLETE"
log "Review log: ${LOG}"
log "Next steps:"
log "  1. Verify all services accessible"
log "  2. Enable monitoring/alerting at DR site"
log "  3. Notify stakeholders"
log "  4. Begin root cause analysis of primary site failure"
log "========================================"
```

### 10.5 Step 4 — Ransomware Recovery Drill

This drill simulates a ransomware attack on production, validates detection, and walks through secure recovery from DR backups.

```bash
#!/bin/bash
# /usr/local/bin/dr-ransomware-drill.sh
# EXERCISE ONLY — do NOT run in production
# Simulates ransomware impact and validates recovery procedure
set -euo pipefail

LOG="/var/log/dr-ransomware-drill-$(date +%Y%m%d-%H%M%S).log"
DRILL_ID="DRILL-$(date +%Y%m%d)"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] [$DRILL_ID] $1" | tee -a "${LOG}"; }

log "=== RANSOMWARE RECOVERY DRILL START ==="
log "This is an EXERCISE. No production systems will be affected."

# ---- SIMULATE: Detection ----
log "--- PHASE: Detection ---"
log "SCENARIO: SOC alerts on mass file encryption on vm-100 (web-01)"
log "SCENARIO: Ransomware note detected in /var/www/html/README_DECRYPT.txt"
log "SCENARIO: Production PBS reports backup deletion attempts (blocked by ACL)"
log "SCENARIO: Timeline: attacker present for 7 days, encryption began 30 min ago"

read -p "Acknowledge scenario and proceed? (yes/no): " CONFIRM
[ "${CONFIRM}" = "yes" ] || { log "Drill aborted by operator."; exit 0; }

# ---- DECISION: Select backup for recovery ----
log "--- PHASE: Backup Selection ---"
log "Listing available backups at DR site..."

ssh root@172.16.2.20 \
    "proxmox-backup-client snapshot list \
        --repository localhost:dr-incoming \
        --output-format json 2>/dev/null" | \
    jq -r '.[] | select(.["backup-id"] == "100") |
        "  Backup: \(.["backup-id"]) Time: \(.["backup-time"] | todate) Size: \(.size)"' | \
    tee -a "${LOG}"

log "Attacker dwell time: 7 days. Select backup OLDER than 7 days."
log "Recommended: choose backup from 8+ days ago."

read -p "Enter backup timestamp to restore (YYYY-MM-DDTHH:MM:SSZ): " RESTORE_TS
log "Selected backup: ${RESTORE_TS}"

# ---- EXECUTE: Failover with security ----
log "--- PHASE: Secure Failover ---"
log "Running pre-flight security checks..."
/usr/local/bin/dr-preflight-security.sh | tee -a "${LOG}"

log "Initiating restore of VM 100 from ${RESTORE_TS}..."
# In a real drill, this would call the actual restore
# For safety, we log the command that WOULD be executed
log "WOULD EXECUTE: qmrestore ... vm/100/${RESTORE_TS} --storage local-zfs --force"

# ---- VERIFY: Integrity check ----
log "--- PHASE: Integrity Verification ---"
log "WOULD EXECUTE: /usr/local/bin/dr-malware-scan.sh <disk-path>"
log "WOULD EXECUTE: /usr/local/bin/verify-backup-integrity.sh vm/100/${RESTORE_TS}"
log "WOULD EXECUTE: /usr/local/bin/dr-config-validate.sh <vm-ip>"

# ---- VALIDATE: Security posture ----
log "--- PHASE: Security Posture Validation ---"
log "Checklist:"
log "  [ ] Recovered VM scanned for malware — CLEAN"
log "  [ ] No ransomware artifacts in restored filesystem"
log "  [ ] SSH hardening intact"
log "  [ ] Firewall rules active"
log "  [ ] No unauthorized user accounts"
log "  [ ] TLS certificates valid"
log "  [ ] Application functional test passed"
log "  [ ] DR monitoring and alerting active"

# ---- RECORD: Evidence and metrics ----
log "--- PHASE: Metrics and Evidence ---"
log "RTO target: 4 hours"
log "RTO actual: [MEASURE FROM DRILL START TO SERVICE RESTORATION]"
log "RPO target: 1 hour"
log "RPO actual: [MEASURE FROM SELECTED BACKUP TO INCIDENT TIME]"

log "=== RANSOMWARE RECOVERY DRILL COMPLETE ==="
log "Post-drill actions:"
log "  1. Complete DR Test Security Findings Report"
log "  2. Rotate all credentials used during drill"
log "  3. Review and update DR runbook based on findings"
log "  4. Schedule remediation for any security gaps found"
log "  5. File evidence package for compliance"
```

### 10.6 DR Security Runbook Template

```
╔══════════════════════════════════════════════════════════════════╗
║              DR SECURITY RUNBOOK — CONFIDENTIAL                  ║
║                                                                  ║
║  Document ID: DR-SEC-RB-001                                      ║
║  Version: 1.0                                                    ║
║  Classification: CONFIDENTIAL — Limited Distribution             ║
║  Last reviewed: 2026-05-07                                       ║
║  Next review: 2026-08-07                                         ║
║  Approved by: [CISO NAME]                                        ║
╚══════════════════════════════════════════════════════════════════╝

SECTION 1: CONTACTS AND ESCALATION
═══════════════════════════════════

DR Team Lead:          [Name] — [Phone] — [Signal]
Security Lead:         [Name] — [Phone] — [Signal]
Infrastructure Lead:   [Name] — [Phone] — [Signal]
CISO:                  [Name] — [Phone] — [Signal]
Legal (for breach):    [Name] — [Phone]
PR (for public comms): [Name] — [Phone]
Cloud provider support:[AWS/Azure emergency contact]

Escalation path:
  0-15 min: DR Team Lead assesses
  15-30 min: Security Lead engaged
  30-60 min: CISO notified
  60+ min: Legal/PR if breach confirmed

SECTION 2: DR ACTIVATION DECISION MATRIX
═════════════════════════════════════════

  Scenario                    Action            Approver
  ─────────────────────────   ───────────────   ──────────────
  Single host failure         HA handles        Automatic
  Storage failure (single)    HA handles        Automatic
  Multiple host failure       Assess DR need    DR Team Lead
  Full site loss              Activate DR       CISO
  Ransomware (prod only)      Activate DR       Security Lead
  Ransomware (prod + DR)      Rebuild from      CISO + Legal
                              offline backups
  DR site compromise          Rebuild DR,       Security Lead
                              do NOT failover

SECTION 3: PRE-FAILOVER SECURITY PROCEDURE
═══════════════════════════════════════════

  □ Confirm nature of incident (availability vs. security)
  □ If security incident: engage Security Lead FIRST
  □ Run /usr/local/bin/dr-preflight-security.sh
  □ Verify break-glass credentials
  □ Verify out-of-band communication channel
  □ Notify on-call team via Signal
  □ Begin logging all actions with UTC timestamps

SECTION 4: FAILOVER EXECUTION
══════════════════════════════

  □ Execute: /usr/local/bin/dr-failover.sh
  □ Monitor each phase for errors
  □ If malware detected: STOP, quarantine, select older backup
  □ If integrity check fails: STOP, escalate to Security Lead
  □ After successful VM restore: wait for config validation
  □ After validation: proceed with DNS cutover
  □ After DNS: verify external access to services
  □ Enable monitoring and alerting at DR site

SECTION 5: POST-FAILOVER SECURITY
══════════════════════════════════

  □ Verify all DR firewall rules active
  □ Verify SIEM collecting from DR hosts
  □ Verify IDS/IPS active at DR site
  □ Change all service account passwords at DR site
  □ Verify no production credentials work at DR site
  □ Monitor for indicators of compromise at DR site
  □ Document all actions taken with timestamps

SECTION 6: FAILBACK PROCEDURE
══════════════════════════════

  □ Confirm primary site restored and clean
  □ Run security scan of primary site infrastructure
  □ Re-establish replication from DR to production
  □ Verify data consistency
  □ Plan maintenance window for failback
  □ Execute DNS cutover back to production
  □ Verify all services at production site
  □ Disable DR workloads (but keep DR infrastructure ready)
  □ Rotate ALL credentials at both sites
  □ Remove any temporary firewall rules
  □ Complete DR event report

SECTION 7: COMPLIANCE NOTIFICATIONS
════════════════════════════════════

  If DR event caused by security breach:
  □ GDPR: Notify supervisory authority within 72h
  □ NIS2: Early warning within 24h, notification within 72h
  □ HIPAA: Notify HHS within 60 days (500+ records)
  □ PCI-DSS: Notify acquirer and card brands per IRP
  □ SOX: Notify audit committee if material impact

  Document:
  □ Timeline of events (UTC)
  □ Systems affected
  □ Data potentially exposed
  □ Containment actions taken
  □ Recovery actions taken
  □ Root cause (if known)
  □ Remediation plan
```

### 10.7 Verification Script — End-to-End DR Security Validation

```bash
#!/bin/bash
# /usr/local/bin/dr-security-full-validation.sh
# Comprehensive post-DR security validation
# Run after any DR failover (real or drill)
set -euo pipefail

DR_PVE_HOST="${1:-172.16.2.10}"
REPORT="/var/log/dr-security-validation-$(date +%Y%m%d-%H%M%S).txt"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $1" | tee -a "${REPORT}"; }
pass() { log "PASS: $1"; }
fail() { log "FAIL: $1"; }
warn() { log "WARN: $1"; }

log "=== DR Security Full Validation Report ==="
log "DR Host: ${DR_PVE_HOST}"
log ""

# 1. Network segmentation
log "--- Network Segmentation ---"
ssh root@"${DR_PVE_HOST}" 'ip route show' | tee -a "${REPORT}"
# Verify no route to production management network
if ssh root@"${DR_PVE_HOST}" 'ip route show | grep -q "172.16.1.0"'; then
    fail "Route to production management network exists"
else
    pass "No route to production management network"
fi

# 2. Firewall status
log "--- Firewall Status ---"
if ssh root@"${DR_PVE_HOST}" 'pve-firewall status | grep -q "running"'; then
    pass "PVE firewall running"
else
    fail "PVE firewall NOT running"
fi

# 3. Credential isolation
log "--- Credential Isolation ---"
# Test that production SSH key does NOT work
if ssh -o BatchMode=yes -o ConnectTimeout=5 \
    -i /root/.ssh/id_ed25519 root@"${DR_PVE_HOST}" 'exit' 2>/dev/null; then
    fail "Production SSH key accepted at DR site — credential isolation violated"
else
    pass "Production SSH key rejected at DR site"
fi

# 4. Encryption at rest
log "--- Encryption at Rest ---"
if ssh root@"${DR_PVE_HOST}" 'lsblk -o NAME,TYPE,CRYPT | grep -q crypt'; then
    pass "Encrypted volume detected at DR site"
else
    warn "No encrypted volume detected — verify storage encryption"
fi

# 5. WireGuard tunnel status
log "--- WireGuard Tunnel ---"
if wg show wg-repl 2>/dev/null | grep -q "latest handshake"; then
    pass "WireGuard tunnel active"
    HANDSHAKE_AGE=$(wg show wg-repl | grep "latest handshake" | \
        awk -F': ' '{print $2}')
    log "  Last handshake: ${HANDSHAKE_AGE}"
else
    warn "WireGuard tunnel status unknown"
fi

# 6. PBS datastore verification
log "--- PBS Datastore ---"
if ssh root@"${DR_PVE_HOST}" \
    'proxmox-backup-manager datastore list 2>/dev/null | grep -q dr-incoming'; then
    pass "DR PBS datastore 'dr-incoming' exists"
else
    fail "DR PBS datastore 'dr-incoming' not found"
fi

# 7. NTP sync
log "--- Time Synchronization ---"
if ssh root@"${DR_PVE_HOST}" 'chronyc tracking 2>/dev/null | grep -q "Normal"'; then
    pass "NTP synchronized"
else
    warn "NTP synchronization issue"
fi

# 8. Monitoring
log "--- Monitoring ---"
if ssh root@"${DR_PVE_HOST}" \
    'systemctl is-active prometheus-node-exporter 2>/dev/null | grep -q active'; then
    pass "Node exporter running"
else
    warn "Node exporter not running — monitoring may be degraded"
fi

# 9. Clean room isolation
log "--- Clean Room Network ---"
if ssh root@"${DR_PVE_HOST}" 'ip link show vmbr99 2>/dev/null | grep -q UP'; then
    pass "Clean room bridge (vmbr99) exists"

    # Verify no uplink
    UPLINK=$(ssh root@"${DR_PVE_HOST}" 'bridge link show | grep vmbr99' || true)
    if [ -z "${UPLINK}" ]; then
        pass "Clean room bridge has no physical uplink (isolated)"
    else
        fail "Clean room bridge has physical uplink — NOT isolated"
    fi
else
    warn "Clean room bridge not found"
fi

# 10. Audit logging
log "--- Audit Logging ---"
if ssh root@"${DR_PVE_HOST}" 'test -f /var/log/pbs-audit.log'; then
    pass "PBS audit log exists"
else
    warn "PBS audit log not found"
fi

# Summary
log ""
log "=== Validation Summary ==="
PASS_COUNT=$(grep -c "PASS:" "${REPORT}")
FAIL_COUNT=$(grep -c "FAIL:" "${REPORT}")
WARN_COUNT=$(grep -c "WARN:" "${REPORT}")

log "PASS: ${PASS_COUNT}"
log "FAIL: ${FAIL_COUNT}"
log "WARN: ${WARN_COUNT}"

if [ "${FAIL_COUNT}" -gt 0 ]; then
    log "STATUS: FAILED — address FAIL items before declaring DR operational"
    exit 1
else
    log "STATUS: PASSED (${WARN_COUNT} warnings to review)"
    exit 0
fi
```

---

## Cross-References

- **Module 10:** HA cluster fundamentals — single-site high availability, which this module extends to cross-site DR.
- **Module 11:** Backup and restore with PBS — backup operations, prune policies, and verification; this module adds security controls on top.
- **Module 12:** Security and compliance — general security framework; this module applies it specifically to DR infrastructure.
- **Module 19:** Multi-site DR Proxmox — DR topology, replication mechanisms, RTO/RPO calculations; this module adds the security dimension.
- **Module 20:** Hypervisor security hardening — hardening controls that must be applied at both production and DR sites.
- **Module 22:** Network segmentation and virtual firewalls — segmentation principles applied to DR network design.

---

## Further Reading

- NIST SP 800-34 Rev. 1: Contingency Planning Guide for Federal Information Systems (2010, still authoritative for DR planning methodology).
- ISO 22301:2019: Security and resilience — Business continuity management systems — Requirements.
- MITRE ATT&CK: T1490 (Inhibit System Recovery), T1486 (Data Encrypted for Impact), T1070.004 (Indicator Removal: File Deletion).
- CISA: Ransomware Guide (Sept 2020, updated 2023) — specifically the backup best practices section.
- PCI-DSS v4.0: Requirements 9.5 (media protection), 12.10 (incident response), 12.10.2 (DR plan review).
- HIPAA: 45 CFR §164.308(a)(7) — Contingency Plan standard.
- Proxmox Backup Server Administration Guide: Remote Sync and Encryption — https://pbs.proxmox.com/docs/
- Ceph Documentation: RBD Mirroring — https://docs.ceph.com/en/latest/rbd/rbd-mirroring/
- WireGuard Protocol Documentation — https://www.wireguard.com/protocol/
- HashiCorp Vault: Performance Replication and KMIP — https://developer.hashicorp.com/vault/docs/enterprise/replication
