# Secure Configuration Baselines — CIS Benchmarks, STIG e Hardening Automation

> **Modulo 40** · **Tempo:** ~480 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Default is vulnerable.** Every OS, service, and appliance ships with convenience over security — your first job is to close what the vendor left open.
2. **Configuration drift is a silent breach.** A system hardened on day one and never checked again is a system you cannot trust on day ninety.
3. **Compliance is a floor, not a ceiling.** CIS and STIG give you a defensible baseline; your threat model dictates what you add on top.
4. **Automate or accept failure.** Manual hardening does not scale past ten machines; Ansible, OpenSCAP, and InSpec turn policy into executable truth.
5. **Scan, fix, re-scan — close the loop.** A finding without remediation is a known risk; a remediation without verification is an assumption.

---

## Indice

1. [Fondamenti Configuration Management Security](#1-fondamenti-configuration-management-security)
2. [CIS Benchmarks Deep Dive](#2-cis-benchmarks-deep-dive)
3. [Implementazione Linux Hardening](#3-implementazione-linux-hardening)
4. [Implementazione Windows Hardening](#4-implementazione-windows-hardening)
5. [Automazione Hardening](#5-automazione-hardening)
6. [Compliance Scanning e Reporting](#6-compliance-scanning-e-reporting)
7. [STIG Implementation](#7-stig-implementation)
8. [Hardening per Ambienti Specifici](#8-hardening-per-ambienti-specifici)
9. [Continuous Compliance](#9-continuous-compliance)
10. [Laboratorio Pratico](#10-laboratorio-pratico)
11. [CIS Controls v8.1 — Approfondimento Safeguard 4](#11-cis-controls-v81--approfondimento-safeguard-4)
12. [Hardening Avanzato per Piattaforme Moderne](#12-hardening-avanzato-per-piattaforme-moderne)
13. [Security Automation Framework e Pipeline CI/CD](#13-security-automation-framework-e-pipeline-cicd)
14. [Zero Trust e Configuration Baselines](#14-zero-trust-e-configuration-baselines)
15. [Gestione Baselines per Dispositivi di Rete](#15-gestione-baselines-per-dispositivi-di-rete)
16. [Casi di Studio e Scenari Operativi](#16-casi-di-studio-e-scenari-operativi)

---

## 1. Fondamenti Configuration Management Security

### 1.1 Why Defaults Are Insecure

Operating systems and applications ship with defaults tuned for broad compatibility and ease of first use, not for security. A fresh Ubuntu Server installation listens on SSH with password authentication enabled, permits root login depending on version, enables IPv6 on all interfaces, mounts `/tmp` on the root filesystem without `noexec`, and runs `cron` with permissive access. A fresh Windows Server 2022 has SMBv1 available as an optional feature, NTLMv1 not explicitly blocked, PowerShell execution policy set to `Restricted` only by convention (trivially bypassed), and audit policies covering almost nothing useful.

These defaults exist because vendors optimize for a successful first boot across millions of deployment scenarios. Security teams must close the gap between "it boots" and "it resists attack." This gap is the configuration baseline problem.

From an attacker's perspective, default configurations are free intelligence. A penetration tester landing on a default-configured Linux box immediately checks: is `/tmp` mounted `noexec`? Is ASLR enabled? Are kernel modules like `cramfs`, `freevxfs`, `udf` loadable? Each permissive default is a potential foothold or lateral movement enabler.

### 1.2 Configuration Drift as Security Risk

Configuration drift occurs when a system's actual state diverges from its intended state over time. Sources of drift include:

- **Ad-hoc troubleshooting**: an engineer disables SELinux to fix an application error and forgets to re-enable it.
- **Uncontrolled software installation**: a developer installs a convenience tool that opens a listening port.
- **Patch side effects**: a kernel update resets sysctl parameters to their defaults.
- **Shadow IT**: a container runtime installed outside change management brings its own network configuration.
- **Incomplete automation**: an Ansible role applies 90% of controls but the remaining 10% are manual — and never get done.

Drift is insidious because it is silent. The system appeared hardened at deployment; nothing in monitoring alerts that a sysctl value reverted. The only reliable countermeasure is continuous compliance scanning that compares desired state to actual state on a schedule.

### 1.3 Desired State Configuration

Desired State Configuration (DSC) is the paradigm where you declare "what the system should look like" and an engine converges reality to that declaration. The key frameworks:

| Framework | Platform | Language | Model |
|-----------|----------|----------|-------|
| Ansible | Linux, Windows, Network | YAML | Push (agentless via SSH/WinRM) |
| Puppet | Linux, Windows | Puppet DSL | Pull (agent-based) |
| Chef | Linux, Windows | Ruby DSL | Pull (agent-based) |
| Salt | Linux, Windows | YAML | Push or Pull |
| PowerShell DSC | Windows | PowerShell/MOF | Push or Pull |
| Terraform (for cloud) | Cloud | HCL | Push (API-driven) |

DSC ensures that configuration is idempotent (applying the same configuration twice produces the same result), versionable (infrastructure as code in Git), auditable (diff between desired and actual state is a compliance report), and testable (you can validate configuration in CI before deploying).

### 1.4 CIS — Center for Internet Security

The Center for Internet Security is a nonprofit that produces:

- **CIS Benchmarks**: prescriptive, consensus-driven secure configuration guides for 100+ technologies. Developed by volunteer communities of security practitioners, auditors, and vendors. Free PDF download; machine-readable formats (XCCDF, OVAL) available to CIS SecureSuite members.
- **CIS Controls (v8.1)**: a prioritized set of 18 security control families (formerly the "Top 20"). Implementation Groups (IG1/IG2/IG3) map controls to organizational maturity. CIS Control 4 — "Secure Configuration of Enterprise Assets and Software" — is the control family most directly relevant to this document.
- **CIS-CAT Pro**: assessment tool that scans systems against CIS Benchmarks and generates compliance reports.
- **CIS Hardened Images**: pre-hardened virtual machine images for AWS, Azure, GCP, Oracle Cloud, conforming to CIS Level 1.

### 1.5 DISA STIG — Security Technical Implementation Guide

The Defense Information Systems Agency (DISA) publishes STIGs for every technology approved for use in U.S. Department of Defense networks. STIGs are mandatory for DoD systems and widely adopted outside government as a rigorous hardening standard.

Key characteristics:

- **Granularity**: a single STIG contains hundreds of individual rules (called "checks" or "findings").
- **Severity categories**: CAT I (high — direct/immediate loss of confidentiality, integrity, or availability), CAT II (medium — potential for degraded security), CAT III (low — administrative or minor risk).
- **Machine-readable**: STIGs ship in XCCDF format, consumable by SCAP-compliant scanners.
- **STIG Viewer**: free Java application from DISA for browsing STIGs, creating checklists, and tracking remediation status.
- **Relationship to CIS**: STIGs and CIS Benchmarks overlap substantially but are independently developed. STIGs tend to be stricter (more DoD-specific requirements around banner text, FIPS 140-2 validated crypto, etc.).

### 1.6 Vendor-Specific Baselines

**Microsoft Security Baselines** — distributed via the Security Compliance Toolkit (SCT). Includes GPO backups, PolicyAnalyzer for comparing baselines across versions, and LGPO.exe for local policy application. Baselines exist for Windows Server 2022, Windows 11, Microsoft Edge, Microsoft 365 Apps. These represent Microsoft's own recommended secure configuration — not identical to CIS or STIG, but informed by the same threat landscape.

**Red Hat STIG/CIS Content** — Red Hat packages SCAP content via `scap-security-guide` (upstream: ComplianceAsCode). During RHEL installation, the Anaconda installer can apply a SCAP profile (CIS, STIG, HIPAA, PCI-DSS) at install time via the Security Policy spoke.

**VMware Security Configuration Guides** — hardening guides for vSphere, NSX, vSAN. Available as PDFs and PowerCLI scripts.

**Cisco STIG/CIS** — IOS, NX-OS, ASA benchmarks. Network device hardening follows the same principle: disable unused services, enforce encrypted management protocols, restrict management plane access.

---

## 2. CIS Benchmarks Deep Dive

### 2.1 Benchmark Levels

CIS Benchmarks define two implementation levels:

**Level 1** — intended for most environments. Controls are practical to implement without significant performance impact or loss of functionality. They represent a baseline that every organization should achieve. Example: ensure SSH `MaxAuthTries` is set to 4 or less.

**Level 2** — extends Level 1 with controls that may reduce functionality or require more careful planning. Intended for high-security environments. Example: ensure DCCP kernel module is disabled (may break niche applications), ensure nftables or iptables firewall is active with deny-all default.

An organization should implement Level 1 across all systems and apply Level 2 selectively based on asset criticality and risk appetite.

### 2.2 Benchmark Structure

Each CIS Benchmark follows a consistent structure:

- **Profile Applicability**: Level 1, Level 2, or both.
- **Description**: what the control does and why it matters.
- **Rationale**: threat model justification — what attack or misconfiguration this prevents.
- **Impact**: what might break if you apply this control.
- **Audit**: how to check if the control is in place (commands, registry keys, config file checks).
- **Remediation**: how to apply the control (commands, configuration changes).
- **Scored vs Not Scored** (renamed to "Automated" vs "Manual" in newer benchmarks): scored/automated controls can be machine-checked; manual controls require human judgment (e.g., "ensure local login warning banner is configured properly" — the tool can check the banner exists but not whether the legal text is correct).
- **CIS Control Mapping**: links each benchmark recommendation to one or more CIS Controls v8 safeguards.
- **Default Value**: what the setting is out of the box.

### 2.3 CIS Ubuntu Linux 22.04/24.04 — Critical Controls

1. **Separate /tmp partition with noexec,nosuid,nodev** — prevents attackers from writing and executing payloads in world-writable temp. (1.1.2.x)
2. **Ensure cramfs, freevxfs, jffs2, hfs, hfsplus, udf kernel modules disabled** — eliminates attack surface from unused filesystems. (1.1.1.x)
3. **Ensure ASLR is enabled** (`kernel.randomize_va_space = 2`) — makes memory corruption exploitation significantly harder. (1.5.2)
4. **Ensure SSH root login is disabled** (`PermitRootLogin no`) — forces use of named accounts for accountability. (5.2.x)
5. **Ensure SSH idle timeout** (`ClientAliveInterval 300`, `ClientAliveCountMax 0`) — prevents abandoned sessions from being hijacked. (5.2.x)
6. **Ensure auditd is installed and enabled** — without audit trails, incident response is blind. (4.1.1.x)
7. **Ensure password creation requirements** (minlen=14, complexity via pam_pwquality) — mitigates brute force and credential stuffing. (5.4.x)
8. **Ensure access to su is restricted** (pam_wheel.so, `use_uid` group restriction) — prevents lateral privilege escalation. (5.6)
9. **Ensure UFW/nftables default deny** — zero-trust network posture at the host level. (3.5.x)
10. **Ensure rsyslog is configured to send logs to a remote host** — exfiltrating logs defeats local log tampering. (4.2.x)

### 2.4 CIS RHEL 8/9 — Critical Controls

1. **Ensure GRUB bootloader password** — prevents single-user mode boot bypass and kernel parameter tampering at physical console. (1.4.1)
2. **Ensure SELinux is enforcing with targeted policy** — mandatory access control limits damage even after root compromise. (1.6.x)
3. **Ensure core dumps are restricted** (`fs.suid_dumpable = 0`, limits.conf `hard core 0`) — prevents credential leakage from process memory. (1.5.x)
4. **Ensure firewalld is running with default zone drop** — host-level firewall with explicit allow rules only. (3.4.x)
5. **Ensure SSH protocol 2 only, strong ciphers, MACs, KEX algorithms** — eliminates weak crypto that enables MITM or session hijack. (5.2.x)
6. **Ensure password hashing algorithm is yescrypt/SHA-512** — increases offline brute-force cost. (5.5.x)
7. **Ensure audit rules for privileged commands** (`-a always,exit -F path=/usr/bin/sudo -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged`) — tracks every sudo, passwd, chsh invocation. (4.1.3.x)
8. **Ensure chrony is configured for NTP** — accurate timestamps are critical for log correlation and forensic timelines. (2.1.x)
9. **Ensure AIDE is installed and configured** — file integrity monitoring detects unauthorized changes to binaries and configs. (1.3.x)
10. **Ensure rsyslog default file permissions are 0640** — prevents unauthorized users from reading sensitive log content. (4.2.x)

### 2.5 CIS Windows Server 2022 — Critical Controls

1. **Account Policies: password length ≥14, complexity enabled, lockout after 5 attempts** — fundamental brute-force protection. (1.1.x, 1.2.x)
2. **Audit Policy: Logon/Logoff Success+Failure, Account Management Success+Failure, Policy Change Success** — enables detection of credential attacks and unauthorized changes. (17.x)
3. **Network Access: restrict anonymous access to Named Pipes and Shares** — prevents null session enumeration used by tools like enum4linux. (2.3.10.x)
4. **Ensure Windows Firewall is enabled for all profiles with default deny inbound** — host-based firewall as defense-in-depth. (9.x)
5. **Ensure WDigest Authentication is disabled** — prevents cleartext credential storage in LSASS memory, which Mimikatz harvests. (18.3.x)
6. **Ensure LSA protection is enabled** (`RunAsPPL = 1`) — protects LSASS from memory dumping. (18.3.x)
7. **Ensure SMBv1 is disabled** — eliminates EternalBlue attack surface (MS17-010). (18.3.x)
8. **Ensure BitLocker or device encryption is enabled** — protects data at rest from offline attacks (stolen disk). (18.x)
9. **Ensure 'Deny log on through Remote Desktop Services' includes Guests** — restricts RDP surface. (2.2.x)
10. **Ensure PowerShell script block logging and module logging are enabled** — provides visibility into PowerShell-based attacks (fileless malware, Living off the Land). (18.9.x)

### 2.6 CIS Windows 11 Enterprise — Critical Controls

1. **Credential Guard enabled** — virtualizes credential storage, defeats pass-the-hash and Mimikatz even with admin access. (18.x)
2. **Windows Defender Exploit Guard: ASR rules enabled** — blocks Office macro abuse, credential stealing from LSASS, executable content from email. (18.9.x)
3. **Controlled Folder Access enabled** — ransomware protection for designated folders. (18.9.x)
4. **Application Control via WDAC or AppLocker** — prevents execution of unauthorized binaries. (18.9.x)
5. **BitLocker with TPM+PIN** — boot integrity plus data-at-rest protection. (18.x)
6. **Secure Boot and UEFI configuration** — prevents bootkit persistence. (1.x)
7. **Network protection enabled** — blocks connections to known malicious domains. (18.9.x)
8. **Audit logon events: Success and Failure** — detects brute-force, pass-the-ticket, lateral movement. (17.x)
9. **Disable autorun/autoplay for all drives** — eliminates USB-based initial access vector. (18.9.x)
10. **Enhanced Phishing Protection in SmartScreen** — detects password entry on phishing sites and password reuse. (18.9.x)

### 2.7 CIS Docker — Critical Controls

1. **Ensure a separate partition for /var/lib/docker** — prevents container storage exhaustion from crashing the host OS. (1.1)
2. **Ensure auditing is configured for Docker daemon** (`-w /usr/bin/dockerd -k docker`) — tracks all Docker management operations. (1.5-1.13)
3. **Ensure Docker daemon runs rootless or with user namespace remapping** — limits blast radius of container escape. (2.8)
4. **Ensure Content Trust is enabled** (`DOCKER_CONTENT_TRUST=1`) — prevents deployment of unsigned/tampered images. (4.5)
5. **Ensure containers run as non-root user** (`USER` directive in Dockerfile) — limits in-container privilege. (4.1)
6. **Ensure `--privileged` flag is not used** — privileged containers have full host access, nullifying containerization. (5.4)
7. **Ensure AppArmor/SELinux profile is applied to containers** — MAC enforcement at container level. (5.2)
8. **Ensure host network mode is not used** — sharing host network namespace exposes all host services. (5.10)
9. **Ensure memory limits are set** (`--memory`) — prevents denial-of-service via memory exhaustion. (5.12)
10. **Ensure Docker socket is not mounted inside containers** — mounting `/var/run/docker.sock` gives full Docker API access, equivalent to root. (5.31)

### 2.8 CIS Kubernetes — Critical Controls

1. **Ensure anonymous authentication is disabled on API server** (`--anonymous-auth=false`) — prevents unauthenticated API access. (1.2.1)
2. **Ensure RBAC is enabled** — authorization must be explicit, not default-allow. (1.2.8)
3. **Ensure audit logging is enabled** (`--audit-policy-file`) — Kubernetes audit logs are the only record of API calls. (1.2.22)
4. **Ensure etcd is encrypted at rest** (`--encryption-provider-config`) — etcd contains all cluster secrets. (1.2.34)
5. **Ensure kubelet authentication uses certificates, not anonymous** (`--anonymous-auth=false` on kubelet) — prevents lateral movement via unauthenticated kubelet API. (4.2.1)
6. **Ensure PodSecurity admission is configured** (enforce restricted) — replaces deprecated PodSecurityPolicy. (5.1.x)
7. **Ensure network policies are configured** — default Kubernetes networking is flat; without NetworkPolicy, every pod can reach every other pod. (5.3.2)
8. **Ensure secrets are not stored in environment variables** — use volume mounts from Secret objects; env vars leak into process lists and crash dumps. (5.4.1)
9. **Ensure containers are not running as root** (`runAsNonRoot: true` in securityContext) — same principle as Docker non-root. (5.2.6)
10. **Ensure service account tokens are not auto-mounted** (`automountServiceAccountToken: false`) — prevents compromised pods from abusing the default service account. (5.1.6)

### 2.9 CIS AWS Foundations — Critical Controls

1. **Ensure MFA is enabled for the root account** — root is the God account; MFA is the only meaningful control. (1.5)
2. **Ensure CloudTrail is enabled in all regions with log file validation** — the audit trail for every API call. (3.1, 3.2)
3. **Ensure S3 buckets are not publicly accessible** (Block Public Access at account level) — data exposure via misconfigured buckets is the #1 cloud breach vector. (2.1.x)
4. **Ensure no root access keys exist** — programmatic root access is unnecessary and catastrophic if compromised. (1.4)
5. **Ensure IAM password policy meets CIS requirements** (14+ chars, expiry, reuse prevention) — defense against credential stuffing. (1.8-1.11)
6. **Ensure VPC flow logs are enabled** — network visibility for incident response. (3.7)
7. **Ensure default security groups restrict all traffic** — default SGs should have no inbound/outbound rules. (5.4)
8. **Ensure EBS encryption is enabled by default** — data at rest protection. (2.2.1)
9. **Ensure AWS Config is enabled in all regions** — configuration recording for drift detection. (3.5)
10. **Ensure GuardDuty is enabled** — threat detection for reconnaissance, compromised instances, and credential abuse. (N/A in some benchmark versions, recommended add-on)

### 2.10 CIS Microsoft Azure Foundations — Critical Controls

1. **Ensure MFA is enabled for all users, especially admins** — Azure AD conditional access with MFA enforcement. (1.1.1)
2. **Ensure Security Defaults or Conditional Access block legacy authentication** — legacy auth bypasses MFA. (1.1.3)
3. **Ensure Azure Activity Log alerts exist for key operations** (create policy assignment, create/update NSG, delete NSG) — audit trail for security-critical changes. (5.2.x)
4. **Ensure diagnostic logs are enabled for all services** — without logging, Azure resources are invisible to SIEM. (5.1.x)
5. **Ensure storage accounts require HTTPS-only transfer** — prevents cleartext data in transit. (3.1)
6. **Ensure default network access rule for storage accounts is deny** — storage accounts default to allow-all; lock them down. (3.7)
7. **Ensure Azure Key Vault is used to store secrets** — avoid hardcoding credentials in app settings. (8.x)
8. **Ensure NSGs are configured for all subnets** — Azure does not auto-apply firewall rules to subnets. (6.x)
9. **Ensure SQL Server auditing is enabled** — database activity monitoring for compliance and breach detection. (4.1.1)
10. **Ensure Azure Defender (Microsoft Defender for Cloud) is enabled for all resource types** — threat detection and security posture management. (2.1.x)

---

## 3. Implementazione Linux Hardening

### 3.1 Filesystem Hardening

#### Separate Partitions

Filesystem layout directly impacts security posture. Critical mount points should be separate partitions with restrictive mount options:

| Mount Point | Mount Options | Rationale |
|-------------|--------------|-----------|
| `/tmp` | `noexec,nosuid,nodev` | Prevents execution of uploaded payloads in world-writable temp |
| `/var` | `nosuid,nodev` | Contains logs, spools, caches — no need for SUID binaries |
| `/var/tmp` | `noexec,nosuid,nodev` | Same as /tmp; often overlooked |
| `/var/log` | `nosuid,nodev,noexec` | Logs should never be executable |
| `/var/log/audit` | `nosuid,nodev,noexec` | Audit logs require integrity; separate partition prevents fillup attacks |
| `/home` | `nosuid,nodev` | User home directories should not contain SUID binaries |
| `/dev/shm` | `noexec,nosuid,nodev` | Shared memory is a common payload staging area |

Implementation in `/etc/fstab`:

```
tmpfs           /tmp        tmpfs   defaults,noexec,nosuid,nodev,size=2G  0 0
tmpfs           /dev/shm    tmpfs   defaults,noexec,nosuid,nodev          0 0
/dev/vg0/var    /var        ext4    defaults,nosuid,nodev                 0 2
/dev/vg0/log    /var/log    ext4    defaults,nosuid,nodev,noexec          0 2
/dev/vg0/audit  /var/log/audit ext4 defaults,nosuid,nodev,noexec         0 2
/dev/vg0/home   /home       ext4    defaults,nosuid,nodev                 0 2
```

#### File Permissions

Key permission checks that every CIS audit flags:

```bash
# Find world-writable files (excluding proc/sys)
find / -xdev -type f -perm -0002 -print 2>/dev/null

# Find SUID/SGID binaries — each one is a potential privesc path
find / -xdev -type f \( -perm -4000 -o -perm -2000 \) -print 2>/dev/null

# Ensure no unowned files exist
find / -xdev -nouser -o -nogroup 2>/dev/null

# Ensure permissions on critical files
chmod 644 /etc/passwd
chmod 000 /etc/shadow
chmod 644 /etc/group
chmod 000 /etc/gshadow
chmod 600 /boot/grub/grub.cfg
```

### 3.2 Boot Security

#### GRUB Password

Without a GRUB password, anyone with physical or console access can boot into single-user mode (adding `init=/bin/bash` to kernel command line) and gain root without credentials.

```bash
# Generate GRUB password hash
grub-mkpasswd-pbkdf2
# Output: PBKDF2 hash of your password is grub.pbkdf2.sha512.10000.XXXX...

# Add to /etc/grub.d/40_custom:
cat <<'GRUBCFG'
set superusers="grubadmin"
password_pbkdf2 grubadmin grub.pbkdf2.sha512.10000.XXXX...
GRUBCFG

# Regenerate GRUB config
update-grub    # Debian/Ubuntu
grub2-mkconfig -o /boot/grub2/grub.cfg  # RHEL/CentOS
```

#### Secure Boot

Ensure UEFI Secure Boot is enabled to prevent bootkit attacks. Verify status:

```bash
mokutil --sb-state
# Expected: SecureBoot enabled
```

### 3.3 Network Hardening — Sysctl Parameters

The following sysctl parameters should be in `/etc/sysctl.d/99-cis-hardening.conf`:

```ini
# IP Forwarding — disable unless the host is a router
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Source routing — prevent source-routed packets (used in routing attacks)
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# ICMP redirects — prevent route hijacking
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Secure ICMP redirects — only accept from gateways in default gateway list
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0

# Log Martians — log impossible source addresses
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# SYN flood protection
net.ipv4.tcp_syncookies = 1

# Reverse path filtering — drop packets with source address that wouldn't be
# routable via the interface they arrived on
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP broadcast requests (Smurf attack mitigation)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# IPv6 — disable router advertisements if IPv6 is not in use
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0

# ASLR — critical for exploitation mitigation
kernel.randomize_va_space = 2

# Restrict ptrace — prevents process memory inspection by non-parent processes
kernel.yama.ptrace_scope = 1

# Restrict kernel log access
kernel.dmesg_restrict = 1

# Restrict access to kernel pointers in /proc
kernel.kptr_restrict = 2
```

Apply without reboot: `sysctl --system`

#### Disabling IPv6 (When Not Needed)

If your network does not use IPv6, disable it to reduce attack surface:

```ini
# /etc/sysctl.d/99-disable-ipv6.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
net.ipv6.conf.lo.disable_ipv6 = 1
```

### 3.4 Access Control

#### PAM Configuration — Password Policy

In `/etc/security/pwquality.conf`:

```ini
minlen = 14
minclass = 4
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1
maxrepeat = 3
maxclassrepeat = 3
gecoscheck = 1
dictcheck = 1
```

#### Account Lockout

```
# /etc/pam.d/common-auth (Debian) or /etc/pam.d/system-auth (RHEL)
auth    required    pam_faillock.so preauth silent deny=5 unlock_time=900 fail_interval=900
auth    [default=die] pam_faillock.so authfail deny=5 unlock_time=900 fail_interval=900
auth    sufficient  pam_faillock.so authsucc
```

#### Restricting su

Only members of group `wheel` (RHEL) or `sudo` (Debian) should be able to use `su`:

```
# /etc/pam.d/su
auth    required    pam_wheel.so use_uid group=wheel
```

#### SSH Hardening

`/etc/ssh/sshd_config` critical parameters:

```
Protocol 2
PermitRootLogin no
MaxAuthTries 4
MaxSessions 10
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
ChallengeResponseAuthentication no
UsePAM yes
X11Forwarding no
AllowTcpForwarding no
ClientAliveInterval 300
ClientAliveCountMax 0
LoginGraceTime 60
Banner /etc/issue.net
AllowUsers deployer admin
# Strong cryptography only
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

### 3.5 Audit Configuration

#### Auditd Rules

The `/etc/audit/rules.d/cis.rules` file should contain at minimum:

```bash
# Ensure events that modify date/time are collected
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change

# Ensure events that modify user/group are collected
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity

# Ensure events that modify network environment are collected
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/sysconfig/network -p wa -k system-locale

# Ensure login/logout events are collected
-w /var/log/lastlog -p wa -k logins
-w /var/run/faillock/ -p wa -k logins

# Ensure session initiation is collected
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k session
-w /var/log/btmp -p wa -k session

# Ensure discretionary access control changes are collected
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -k perm_mod
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -k perm_mod

# Ensure unsuccessful file access attempts are collected
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access
-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access

# Ensure privileged commands are audited
# Generate dynamically:
# find / -xdev \( -perm -4000 -o -perm -2000 \) -type f | \
#   awk '{print "-a always,exit -F path="$1" -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged"}'

# Ensure kernel module loading/unloading is collected
-w /sbin/insmod -p x -k modules
-w /sbin/rmmod -p x -k modules
-w /sbin/modprobe -p x -k modules
-a always,exit -F arch=b64 -S init_module -S delete_module -k modules

# Ensure the audit configuration is immutable (must be last rule)
-e 2
```

#### Log Protection

```bash
# Ensure audit log storage size is configured
# /etc/audit/auditd.conf
max_log_file = 25
max_log_file_action = keep_logs
space_left_action = email
action_mail_acct = root
admin_space_left_action = halt
```

### 3.6 Service Hardening

#### Disable Unused Services

```bash
# Identify listening services
ss -tulnp

# Disable common unnecessary services
systemctl --now disable avahi-daemon
systemctl --now disable cups
systemctl --now disable rpcbind
systemctl --now disable vsftpd
systemctl --now mask rpcbind

# Disable unused kernel modules
cat > /etc/modprobe.d/cis-hardening.conf <<'EOF'
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install udf /bin/true
install usb-storage /bin/true
install dccp /bin/true
install sctp /bin/true
install rds /bin/true
install tipc /bin/true
EOF
```

#### Systemd Sandboxing

For custom services, apply systemd sandboxing directives in the unit file:

```ini
[Service]
# Filesystem
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/myapp

# Network
PrivateNetwork=no
RestrictAddressFamilies=AF_INET AF_INET6

# Capabilities
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
NoNewPrivileges=yes

# Security
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
```

### 3.7 Mandatory Access Control

#### SELinux (RHEL/Fedora/CentOS)

```bash
# Verify SELinux status
getenforce           # Should return "Enforcing"
sestatus             # Detailed status

# If permissive, switch to enforcing
setenforce 1         # Runtime (non-persistent)
# Persistent: edit /etc/selinux/config → SELINUX=enforcing

# Troubleshoot denials
ausearch -m avc -ts recent | audit2why
# Generate custom policy for legitimate denials
ausearch -m avc -ts recent | audit2allow -M myapp
semodule -i myapp.pp
```

#### AppArmor (Debian/Ubuntu)

```bash
# Check AppArmor status
aa-status

# Enforce all profiles
aa-enforce /etc/apparmor.d/*

# Generate a profile for a new application
aa-genprof /usr/sbin/myapp
# Run the application through its paces while aa-genprof monitors
# Then finalize the profile
```

---

## 4. Implementazione Windows Hardening

### 4.1 Local Security Policy

#### Account Policies

Configure via `secpol.msc` → Account Policies or GPO:

| Setting | CIS Recommended Value | Rationale |
|---------|----------------------|-----------|
| Minimum password length | 14 characters | Resistance to offline brute force |
| Password complexity | Enabled | Requires uppercase, lowercase, digit, special |
| Maximum password age | 365 days | Balance between rotation fatigue and exposure time |
| Minimum password age | 1 day | Prevents immediate password cycling |
| Password history | 24 passwords | Prevents reuse of recent passwords |
| Account lockout threshold | 5 invalid attempts | Mitigates online brute force |
| Account lockout duration | 15 minutes | Auto-unlock after cooldown |
| Reset lockout counter after | 15 minutes | Aligns with lockout duration |

#### Audit Policies (Advanced)

Use Advanced Audit Policy Configuration (`auditpol`) rather than basic audit policies — they offer granularity:

```powershell
# Enable critical audit categories
auditpol /set /subcategory:"Logon" /success:enable /failure:enable
auditpol /set /subcategory:"Logoff" /success:enable
auditpol /set /subcategory:"Account Lockout" /success:enable /failure:enable
auditpol /set /subcategory:"Special Logon" /success:enable
auditpol /set /subcategory:"Other Logon/Logoff Events" /success:enable /failure:enable
auditpol /set /subcategory:"Security Group Management" /success:enable
auditpol /set /subcategory:"User Account Management" /success:enable /failure:enable
auditpol /set /subcategory:"Computer Account Management" /success:enable
auditpol /set /subcategory:"Process Creation" /success:enable
auditpol /set /subcategory:"Audit Policy Change" /success:enable /failure:enable
auditpol /set /subcategory:"Authentication Policy Change" /success:enable
auditpol /set /subcategory:"Sensitive Privilege Use" /success:enable /failure:enable
auditpol /set /subcategory:"Security System Extension" /success:enable

# Include command line in process creation events (critical for forensics)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" /v ProcessCreationIncludeCmdLine_Enabled /t REG_DWORD /d 1 /f
```

### 4.2 Windows Firewall Advanced Configuration

```powershell
# Enable firewall for all profiles
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True

# Set default deny inbound, allow outbound
Set-NetFirewallProfile -Profile Domain,Public,Private `
    -DefaultInboundAction Block `
    -DefaultOutboundAction Allow

# Log dropped packets (critical for incident response)
Set-NetFirewallProfile -Profile Domain,Public,Private `
    -LogBlocked True `
    -LogMaxSizeKilobytes 16384 `
    -LogFileName "%systemroot%\system32\LogFiles\Firewall\pfirewall.log"

# Example: allow only specific RDP source
New-NetFirewallRule -DisplayName "Allow RDP from Admin VLAN" `
    -Direction Inbound -Protocol TCP -LocalPort 3389 `
    -RemoteAddress 10.10.50.0/24 -Action Allow -Profile Domain
```

### 4.3 Windows Defender Configuration

#### Attack Surface Reduction (ASR) Rules

ASR rules are the single most impactful Defender feature for preventing common attack techniques:

```powershell
# Block Office apps from creating executable content
Set-MpPreference -AttackSurfaceReductionRules_Ids D4F940AB-401B-4EFC-AADC-AD5F3C50688A `
    -AttackSurfaceReductionRules_Actions Enabled

# Block Office apps from injecting code into other processes
Set-MpPreference -AttackSurfaceReductionRules_Ids 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 `
    -AttackSurfaceReductionRules_Actions Enabled

# Block credential stealing from LSASS
Set-MpPreference -AttackSurfaceReductionRules_Ids 9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2 `
    -AttackSurfaceReductionRules_Actions Enabled

# Block executable content from email client and webmail
Set-MpPreference -AttackSurfaceReductionRules_Ids BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550 `
    -AttackSurfaceReductionRules_Actions Enabled

# Block Win32 API calls from Office macros
Set-MpPreference -AttackSurfaceReductionRules_Ids 92E97FA1-2EDF-4476-BDD6-9DD0B4DDDC7B `
    -AttackSurfaceReductionRules_Actions Enabled

# Block process creations from PSExec and WMI commands
Set-MpPreference -AttackSurfaceReductionRules_Ids D1E49AAC-8F56-4280-B9BA-993A6D77406C `
    -AttackSurfaceReductionRules_Actions Enabled
```

#### Controlled Folder Access

```powershell
Set-MpPreference -EnableControlledFolderAccess Enabled
Add-MpPreference -ControlledFolderAccessProtectedFolders "C:\CriticalData"
# Allow specific trusted applications
Add-MpPreference -ControlledFolderAccessAllowedApplications "C:\Program Files\TrustedApp\app.exe"
```

#### Network Protection

```powershell
Set-MpPreference -EnableNetworkProtection Enabled
# Blocks connections to known malicious IPs/domains based on Microsoft threat intelligence
```

### 4.4 BitLocker Deployment

```powershell
# Check TPM availability
Get-Tpm

# Enable BitLocker with TPM + PIN
Enable-BitLocker -MountPoint "C:" -EncryptionMethod XtsAes256 `
    -UsedSpaceOnly -TpmAndPinProtector -Pin (ConvertTo-SecureString "123456" -AsPlainText -Force)

# Add recovery key backup to AD
Backup-BitLockerKeyProtector -MountPoint "C:" `
    -KeyProtectorId ((Get-BitLockerVolume -MountPoint "C:").KeyProtector | Where-Object {$_.KeyProtectorType -eq "RecoveryPassword"}).KeyProtectorId

# Verify status
Get-BitLockerVolume | Select-Object MountPoint, VolumeStatus, EncryptionMethod, ProtectionStatus
```

### 4.5 Application Control — AppLocker and WDAC

#### AppLocker (Enterprise and Education SKUs)

```powershell
# Create default rules (baseline)
Set-AppLockerPolicy -XMLPolicy (
    Get-AppLockerPolicy -Effective -Xml |
    Set-AppLockerPolicy -PolicyObject $_ -Merge
)

# Example: block executables from user-writable paths
# Create rule via GUI: secpol.msc → Application Control Policies → AppLocker
# Or via PowerShell XML policy

# Test in Audit mode first (critical — enforcing without testing = outage)
# Event Log: Applications and Services Logs → Microsoft → Windows → AppLocker
```

#### Windows Defender Application Control (WDAC)

WDAC is the successor to AppLocker and operates at kernel level:

```powershell
# Create a WDAC policy from a known-good reference system
New-CIPolicy -FilePath "C:\Policies\InitialScan.xml" `
    -Level Publisher -Fallback Hash -UserPEs

# Audit mode first
Set-RuleOption -FilePath "C:\Policies\InitialScan.xml" -Option 3  # Audit mode

# Convert to binary
ConvertFrom-CIPolicy -XmlFilePath "C:\Policies\InitialScan.xml" `
    -BinaryFilePath "C:\Windows\System32\CodeIntegrity\SIPolicy.p7b"
```

### 4.6 LSA Protection

```powershell
# Enable RunAsPPL (Protected Process Light for LSASS)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v RunAsPPL /t REG_DWORD /d 1 /f

# Enable Credential Guard (requires UEFI, Secure Boot, Virtualization)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 1 /f
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v LsaCfgFlags /t REG_DWORD /d 1 /f

# Verify Credential Guard is running
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard |
    Select-Object -ExpandProperty SecurityServicesRunning
# Value 1 = Credential Guard running
```

### 4.7 SMB Hardening

```powershell
# Disable SMBv1 — EternalBlue and its variants
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# Require SMB signing (prevents relay attacks)
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

# Require SMB encryption (SMB 3.0+)
Set-SmbServerConfiguration -EncryptData $true -Force

# Disable SMB null session access
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name RestrictNullSessAccess -Value 1
```

### 4.8 PowerShell Hardening

```powershell
# Enable Script Block Logging (logs every script block executed)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging" /v EnableScriptBlockLogging /t REG_DWORD /d 1 /f

# Enable Module Logging
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging" /v EnableModuleLogging /t REG_DWORD /d 1 /f
# Log all modules
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ModuleLogging\ModuleNames" /v "*" /t REG_SZ /d "*" /f

# Enable Transcription Logging (full session transcript to file)
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" /v EnableTranscripting /t REG_DWORD /d 1 /f
reg add "HKLM\SOFTWARE\Policies\Microsoft\Windows\PowerShell\Transcription" /v OutputDirectory /t REG_SZ /d "C:\PSTranscripts" /f

# Constrained Language Mode (via WDAC policy — cannot be reliably set standalone)
# When WDAC is active, PowerShell automatically enters Constrained Language Mode
# for scripts not allowed by the policy

# Just Enough Administration (JEA) — role-based PowerShell remoting
# Create session configuration:
New-PSSessionConfigurationFile -Path "C:\JEA\HelpDesk.pssc" `
    -SessionType RestrictedRemoteServer `
    -RoleDefinitions @{
        'DOMAIN\HelpDesk' = @{ RoleCapabilities = 'PasswordReset', 'ServiceRestart' }
    }
Register-PSSessionConfiguration -Name HelpDesk -Path "C:\JEA\HelpDesk.pssc"
```

---

## 5. Automazione Hardening

### 5.1 Ansible — ansible-lockdown Roles

The `ansible-lockdown` GitHub organization maintains CIS and STIG hardening roles for major platforms. These are the most widely deployed open-source hardening automation.

#### Role Installation

```bash
# Install from Ansible Galaxy (community roles)
ansible-galaxy install ansible-lockdown.UBUNTU22-CIS
ansible-galaxy install ansible-lockdown.RHEL9-CIS
ansible-galaxy install ansible-lockdown.RHEL9-STIG
ansible-galaxy install ansible-lockdown.Windows-2022-CIS
```

#### Playbook — CIS Hardening for Ubuntu 22.04

```yaml
---
# playbook: cis-harden-ubuntu.yml
- name: Apply CIS Benchmark to Ubuntu 22.04
  hosts: ubuntu_servers
  become: true
  vars:
    # Section 1: Initial Setup
    ubtu22cis_rule_1_1_1_1: true   # Disable cramfs
    ubtu22cis_rule_1_1_1_2: true   # Disable freevxfs
    ubtu22cis_rule_1_1_2_1: true   # /tmp on separate partition
    ubtu22cis_rule_1_5_2: true     # ASLR enabled

    # Section 5: Access, Authentication, Authorization
    ubtu22cis_rule_5_2_1: true     # SSH permissions on /etc/ssh/sshd_config
    ubtu22cis_rule_5_2_4: true     # SSH root login disabled
    ubtu22cis_rule_5_2_5: true     # SSH PermitEmptyPasswords no
    ubtu22cis_sshd_max_auth_tries: 4
    ubtu22cis_sshd_client_alive_interval: 300
    ubtu22cis_sshd_client_alive_count_max: 0

    # Section 4: Logging and Auditing
    ubtu22cis_rule_4_1_1_1: true   # auditd installed
    ubtu22cis_rule_4_1_1_2: true   # auditd enabled
    ubtu22cis_rule_4_2_1_1: true   # rsyslog installed

    # Tagging controls — skip specific rules if needed
    ubtu22cis_skip_rules:
      - "1.1.10"  # Skip if /var/log/audit separate partition breaks layout

    # Password policy
    ubtu22cis_pwquality:
      minlen: 14
      minclass: 4

  roles:
    - ansible-lockdown.UBUNTU22-CIS
```

#### Playbook — CIS Hardening for RHEL 9

```yaml
---
- name: Apply CIS Benchmark to RHEL 9
  hosts: rhel9_servers
  become: true
  vars:
    rhel9cis_selinux_state: enforcing
    rhel9cis_selinux_policy: targeted
    rhel9cis_firewall_service: firewalld
    rhel9cis_time_sync_tool: chrony
    rhel9cis_sshd:
      log_level: VERBOSE
      max_auth_tries: 4
      permit_root_login: "no"
      client_alive_interval: 300
      client_alive_count_max: 0
      login_grace_time: 60
      allow_tcp_forwarding: "no"
      x11_forwarding: "no"
      ciphers: "chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com"
      macs: "hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com"
      kex_algorithms: "curve25519-sha256,curve25519-sha256@libssh.org"
    rhel9cis_aide_cron:
      user: root
      cron_file: aide-check
      job: "/usr/sbin/aide --check"
      hour: "5"
      minute: "0"
  roles:
    - ansible-lockdown.RHEL9-CIS
```

#### Running Hardening Playbooks

```bash
# Dry run — check what would change without modifying anything
ansible-playbook cis-harden-ubuntu.yml --check --diff

# Apply with verbose output
ansible-playbook cis-harden-ubuntu.yml -v

# Apply only specific CIS sections via tags
ansible-playbook cis-harden-ubuntu.yml --tags "section5"

# Apply to a single host for testing
ansible-playbook cis-harden-ubuntu.yml --limit test-server-01
```

### 5.2 OpenSCAP — Scanner and Remediation

OpenSCAP is the reference implementation for SCAP (Security Content Automation Protocol). It evaluates systems against XCCDF/OVAL content and can generate remediation scripts.

```bash
# Install on RHEL/CentOS
dnf install openscap-scanner scap-security-guide

# Install on Ubuntu/Debian
apt install libopenscap8 ssg-debian ssg-ubuntu

# List available profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Evaluate CIS Level 1 profile
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --results /tmp/cis-results.xml \
    --report /tmp/cis-report.html \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Evaluate STIG profile
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_stig \
    --results /tmp/stig-results.xml \
    --report /tmp/stig-report.html \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Generate remediation script from results (Bash)
oscap xccdf generate fix \
    --fix-type bash \
    --result-id "" \
    /tmp/cis-results.xml > /tmp/cis-remediation.sh

# Generate Ansible remediation from results
oscap xccdf generate fix \
    --fix-type ansible \
    --result-id "" \
    /tmp/cis-results.xml > /tmp/cis-remediation.yml

# Tailoring — customize a profile without modifying the upstream datastream
oscap xccdf generate tailoring \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --select xccdf_org.ssgproject.content_rule_ensure_gpgcheck_globally_activated \
    --output /tmp/cis-tailored.xml \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

### 5.3 InSpec — Compliance as Code

Chef InSpec allows expressing compliance checks as executable Ruby DSL. The `dev-sec` project maintains community hardening baselines.

```ruby
# profiles/cis-linux/controls/filesystem.rb

control 'cis-1.1.1.1' do
  impact 1.0
  title 'Ensure cramfs kernel module is not available'
  desc 'The cramfs filesystem type is a compressed read-only Linux
        filesystem. Removing support reduces the attack surface.'

  describe kernel_module('cramfs') do
    it { should_not be_loaded }
    it { should be_disabled }    # via modprobe.d blacklist
  end
end

control 'cis-1.1.2.1' do
  impact 1.0
  title 'Ensure /tmp is a separate mount with noexec'
  desc 'Mounting /tmp separately with noexec prevents execution of
        scripts dropped by attackers.'

  describe mount('/tmp') do
    it { should be_mounted }
    its('options') { should include 'noexec' }
    its('options') { should include 'nosuid' }
    its('options') { should include 'nodev' }
  end
end

control 'cis-1.5.2' do
  impact 1.0
  title 'Ensure ASLR is enabled'

  describe kernel_parameter('kernel.randomize_va_space') do
    its('value') { should eq 2 }
  end
end

control 'cis-5.2.4' do
  impact 1.0
  title 'Ensure SSH root login is disabled'

  describe sshd_config do
    its('PermitRootLogin') { should eq 'no' }
  end
end

control 'cis-5.2.13' do
  impact 1.0
  title 'Ensure only strong ciphers are used'

  describe sshd_config do
    its('Ciphers') { should_not include 'arcfour' }
    its('Ciphers') { should_not include '3des' }
    its('Ciphers') { should_not include 'aes128-cbc' }
    its('Ciphers') { should_not include 'aes192-cbc' }
    its('Ciphers') { should_not include 'aes256-cbc' }
  end
end
```

Running InSpec:

```bash
# Execute against local system
inspec exec profiles/cis-linux/ --reporter cli html:/tmp/inspec-report.html

# Execute against remote host
inspec exec profiles/cis-linux/ -t ssh://admin@target-host -i ~/.ssh/id_ed25519

# Use community profile
inspec exec https://github.com/dev-sec/linux-baseline -t ssh://admin@target

# Execute SSH baseline
inspec exec https://github.com/dev-sec/ssh-baseline -t ssh://admin@target
```

### 5.4 PowerShell DSC for Windows

```powershell
# Configuration: CIS-aligned Windows Server hardening
Configuration CISWindowsBaseline {
    Import-DscResource -ModuleName SecurityPolicyDsc
    Import-DscResource -ModuleName AuditPolicyDsc
    Import-DscResource -ModuleName NetworkingDsc

    Node 'localhost' {

        # Password Policy
        AccountPolicy AccountPolicies {
            Name                                  = 'PasswordPolicies'
            Enforce_password_history              = 24
            Maximum_Password_Age                  = 365
            Minimum_Password_Age                  = 1
            Minimum_Password_Length               = 14
            Password_must_meet_complexity_requirements = 'Enabled'
        }

        # Account Lockout
        AccountPolicy LockoutPolicies {
            Name                             = 'LockoutPolicies'
            Account_lockout_threshold        = 5
            Account_lockout_duration         = 15
            Reset_account_lockout_counter_after = 15
        }

        # Audit Policies
        AuditPolicySubcategory LogonAudit {
            Name      = 'Logon'
            AuditFlag = 'Success'
            Ensure    = 'Present'
        }

        AuditPolicySubcategory LogonFailureAudit {
            Name      = 'Logon'
            AuditFlag = 'Failure'
            Ensure    = 'Present'
        }

        AuditPolicySubcategory AccountManagement {
            Name      = 'User Account Management'
            AuditFlag = 'Success'
            Ensure    = 'Present'
        }

        # Firewall Profile
        Firewall DomainProfile {
            Name      = 'Domain'
            Ensure    = 'Present'
            Enabled   = 'True'
            Direction = 'Inbound'
            Action    = 'Block'
        }

        # Registry: Disable SMBv1
        Registry DisableSMBv1 {
            Ensure    = 'Present'
            Key       = 'HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters'
            ValueName = 'SMB1'
            ValueData = '0'
            ValueType = 'Dword'
        }

        # Registry: Enable LSA RunAsPPL
        Registry EnableRunAsPPL {
            Ensure    = 'Present'
            Key       = 'HKLM:\SYSTEM\CurrentControlSet\Control\Lsa'
            ValueName = 'RunAsPPL'
            ValueData = '1'
            ValueType = 'Dword'
        }

        # Registry: PowerShell Script Block Logging
        Registry PSScriptBlockLogging {
            Ensure    = 'Present'
            Key       = 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell\ScriptBlockLogging'
            ValueName = 'EnableScriptBlockLogging'
            ValueData = '1'
            ValueType = 'Dword'
        }
    }
}

# Compile and apply
CISWindowsBaseline
Start-DscConfiguration -Path .\CISWindowsBaseline -Wait -Verbose -Force

# Test compliance
Test-DscConfiguration -Detailed
```

### 5.5 Custom Hardening Scripts

#### Bash — Linux Quick Hardening

```bash
#!/usr/bin/env bash
# cis-quick-harden.sh — Applies high-impact CIS controls for Ubuntu/RHEL
# Run as root. This covers critical controls only; use a full CIS role for production.

set -euo pipefail

echo "[*] Disabling unused kernel modules..."
for mod in cramfs freevxfs jffs2 hfs hfsplus udf dccp sctp rds tipc; do
    printf "install %s /bin/true\nblacklist %s\n" "$mod" "$mod" \
        > "/etc/modprobe.d/disable-${mod}.conf"
    modprobe -r "$mod" 2>/dev/null || true
done

echo "[*] Applying sysctl hardening..."
cat > /etc/sysctl.d/99-cis.conf <<'SYSCTL'
net.ipv4.ip_forward = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.tcp_syncookies = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_ra = 0
kernel.randomize_va_space = 2
kernel.yama.ptrace_scope = 1
kernel.dmesg_restrict = 1
kernel.kptr_restrict = 2
fs.suid_dumpable = 0
SYSCTL
sysctl --system

echo "[*] Hardening SSH..."
sed -i \
    -e 's/^#\?PermitRootLogin.*/PermitRootLogin no/' \
    -e 's/^#\?MaxAuthTries.*/MaxAuthTries 4/' \
    -e 's/^#\?PermitEmptyPasswords.*/PermitEmptyPasswords no/' \
    -e 's/^#\?X11Forwarding.*/X11Forwarding no/' \
    -e 's/^#\?AllowTcpForwarding.*/AllowTcpForwarding no/' \
    /etc/ssh/sshd_config

echo "ClientAliveInterval 300" >> /etc/ssh/sshd_config
echo "ClientAliveCountMax 0"   >> /etc/ssh/sshd_config
systemctl restart sshd

echo "[*] Setting file permissions..."
chmod 644 /etc/passwd
chmod 000 /etc/shadow
chmod 644 /etc/group
chmod 000 /etc/gshadow

echo "[+] Quick hardening complete. Run a CIS scan to verify."
```

#### PowerShell — Windows Quick Hardening

```powershell
# cis-quick-harden.ps1 — High-impact CIS controls for Windows Server
# Run as Administrator

Write-Host "[*] Disabling SMBv1..."
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue

Write-Host "[*] Enabling LSA Protection..."
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa" -Name RunAsPPL -Value 1 -Type DWord

Write-Host "[*] Disabling WDigest..."
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\WDigest" -Name UseLogonCredential -Value 0 -Type DWord

Write-Host "[*] Enabling PowerShell logging..."
$psLogPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\PowerShell"
New-Item -Path "$psLogPath\ScriptBlockLogging" -Force | Out-Null
Set-ItemProperty -Path "$psLogPath\ScriptBlockLogging" -Name EnableScriptBlockLogging -Value 1 -Type DWord
New-Item -Path "$psLogPath\ModuleLogging" -Force | Out-Null
Set-ItemProperty -Path "$psLogPath\ModuleLogging" -Name EnableModuleLogging -Value 1 -Type DWord

Write-Host "[*] Enabling Windows Firewall (all profiles)..."
Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled True -DefaultInboundAction Block

Write-Host "[*] Requiring SMB signing..."
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbClientConfiguration -RequireSecuritySignature $true -Force

Write-Host "[*] Enabling process creation auditing with command line..."
auditpol /set /subcategory:"Process Creation" /success:enable | Out-Null
Set-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System\Audit" `
    -Name ProcessCreationIncludeCmdLine_Enabled -Value 1 -Type DWord

Write-Host "[+] Quick hardening complete. Run CIS-CAT or Nessus compliance scan to verify."
```

---

## 6. Compliance Scanning e Reporting

### 6.1 CIS-CAT Pro

CIS-CAT Pro Assessor is the official CIS benchmark scanning tool, available to CIS SecureSuite members.

**Architecture:**
- **CIS-CAT Pro Assessor v4**: Java-based CLI tool that evaluates local or remote systems against CIS Benchmarks bundled as XCCDF/OVAL datastreams.
- **CIS-CAT Pro Dashboard**: web application (Grails-based) that aggregates scan results from multiple systems, tracks compliance over time, and provides remediation reports.
- **CIS-CAT Lite**: free version with limited benchmark coverage (approximately 10 benchmarks).

**Usage:**

```bash
# Local assessment (Linux)
./Assessor-CLI.sh \
    -b benchmarks/CIS_Ubuntu_Linux_22.04_LTS_Benchmark_v2.0.0-xccdf.xml \
    -p "Level 1 - Server" \
    -r /opt/cis-reports/ \
    -html -csv -json

# Remote assessment via SSH
./Assessor-CLI.sh \
    -b benchmarks/CIS_Red_Hat_Enterprise_Linux_9_Benchmark_v1.0.0-xccdf.xml \
    -p "Level 2 - Server" \
    --sessions sessions.properties \
    -html

# sessions.properties format:
# session.1.type=ssh
# session.1.host=10.10.20.5
# session.1.port=22
# session.1.user=cisadmin
# session.1.identity=/opt/cis/.ssh/id_ed25519
```

**Report Interpretation:**

CIS-CAT generates a score as percentage of passed controls. The industry target varies by maturity:

| Maturity | Target Score | Context |
|----------|-------------|---------|
| Initial  | 70%+ | First scan of existing infrastructure |
| Managed  | 85%+ | After first remediation cycle |
| Defined  | 92%+ | Hardened golden image |
| Optimized | 97%+ | Continuous compliance with automated remediation |

### 6.2 OpenSCAP Reporting

```bash
# Generate HTML report from existing results
oscap xccdf generate report /tmp/cis-results.xml > /tmp/cis-report.html

# ARF (Asset Reporting Format) — machine-readable for dashboards
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --results-arf /tmp/cis-arf.xml \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# Check specific rule result
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis \
    --rule xccdf_org.ssgproject.content_rule_sshd_disable_root_login \
    --results /tmp/ssh-root-check.xml \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml
```

### 6.3 Nessus Compliance Scanning

Nessus Professional and Tenable.sc support compliance scanning via audit files — policy checks separate from vulnerability checks.

**Key audit file families:**
- `CIS_Ubuntu_22.04_LTS_v2.0.0_L1_Server.audit`
- `CIS_Red_Hat_EL_9_v1.0.0_L1_Server.audit`
- `CIS_MS_Windows_Server_2022_v2.0.0_L1.audit`
- `DISA_STIG_RHEL_9_v1r1.audit`

These are Tenable's proprietary `.audit` format — not SCAP. They check the same controls but via Nessus plugins rather than OVAL definitions.

**Scan configuration:**
1. Create a policy compliance scan template in Nessus.
2. Select the appropriate audit file(s).
3. Configure credentials (SSH key for Linux, WinRM/NTLM for Windows).
4. Schedule recurring scans (weekly is typical).
5. Review results: PASS, FAIL, WARNING, ERROR.

### 6.4 Qualys Policy Compliance

Qualys PC (Policy Compliance) module evaluates systems against CIS, STIG, and custom policies. Cloud-hosted with agent or agentless scanning. Strong integration with Qualys VMDR for combined vulnerability + compliance posture. Exports to CSV, PDF, and API for dashboard integration.

### 6.5 Lynis — Linux Security Auditing

Lynis is an open-source security auditing tool for Linux/Unix:

```bash
# Install
apt install lynis   # Debian/Ubuntu
dnf install lynis   # RHEL/Fedora

# Full system audit
lynis audit system

# Pentest mode (additional checks for ethical hackers)
lynis audit system --pentest

# Specific category only
lynis audit system --tests-from-group "firewalls"

# Custom profile
lynis audit system --profile /etc/lynis/custom.prf

# Generate report
# Default report: /var/log/lynis-report.dat
# Parse with:
grep "suggestion\[\]" /var/log/lynis-report.dat
grep "warning\[\]" /var/log/lynis-report.dat
```

Lynis produces a Hardening Index (0-100). Scores above 80 indicate good baseline hardening.

### 6.6 Custom Compliance Checking with InSpec

For organization-specific controls beyond CIS/STIG:

```ruby
# profiles/org-specific/controls/company_policy.rb

control 'org-sec-001' do
  impact 1.0
  title 'Ensure NTP points to internal time servers only'
  desc 'Per corporate policy, all systems must sync time from
        internal NTP servers for log correlation integrity.'

  describe ntp_conf do
    its('server') { should_not include '0.pool.ntp.org' }
    its('server') { should_not include '1.pool.ntp.org' }
  end

  describe file('/etc/chrony.conf') do
    its('content') { should match(/^server\s+ntp1\.corp\.internal/) }
    its('content') { should match(/^server\s+ntp2\.corp\.internal/) }
  end
end

control 'org-sec-002' do
  impact 0.7
  title 'Ensure corporate banner is displayed at SSH login'

  describe file('/etc/issue.net') do
    its('content') { should match(/AUTHORIZED ACCESS ONLY/) }
    its('content') { should match(/monitored and recorded/) }
  end
end

control 'org-sec-003' do
  impact 1.0
  title 'Ensure no users have password age greater than 90 days'

  shadow.users.each do |user|
    next if %w[root nobody].include?(user)
    next if shadow.where(user: user).max_days.first.nil?

    describe shadow.where(user: user) do
      its('max_days.first') { should cmp <= 90 }
    end
  end
end
```

---

## 7. STIG Implementation

### 7.1 STIG Viewer Workflow

DISA STIG Viewer (now replaced by STIG Manager for enterprise use) is the standard tool for tracking STIG compliance:

1. **Import STIG**: load the XCCDF file for the relevant technology (e.g., `U_RHEL_9_V1R1_STIG.zip`).
2. **Create Checklist**: generate a `.ckl` (checklist) file for each system being assessed.
3. **Evaluate**: for each STIG rule, assess the system and mark the finding as:
   - **Not a Finding (NaF)**: the system is compliant.
   - **Open**: the system is non-compliant.
   - **Not Applicable (N/A)**: the control does not apply (e.g., STIG requires IIS hardening on a Linux system).
   - **Not Reviewed (NR)**: not yet assessed.
4. **Document**: for each Open finding, record the actual configuration and the plan to remediate.
5. **Export**: generate reports for auditors, POA&M tracking, and remediation teams.

### 7.2 CAT Severity Mapping

| Category | Severity | CVSS Equivalent | Impact | Action |
|----------|----------|-----------------|--------|--------|
| CAT I | High | 7.0-10.0 | Direct, immediate loss of CIA. System compromise, data breach, complete DoS. | **Must fix immediately.** No exceptions without AO (Authorizing Official) approval. |
| CAT II | Medium | 4.0-6.9 | Degraded security posture. Attack surface expansion, insufficient logging, weak authentication. | **Must fix within 90 days.** May require POA&M if delayed. |
| CAT III | Low | 0.1-3.9 | Administrative or minor risk. Missing banners, minor permission issues, informational gaps. | **Should fix within 180 days.** Lowest priority but still tracked. |

### 7.3 Common STIGs

**Operating System STIGs:**
- RHEL 8/9 STIG — covers everything from boot loader to audit subsystem.
- Ubuntu 20.04/22.04 STIG — relatively newer; canonical collaboration with DISA.
- Windows Server 2019/2022 STIG — tightly integrated with GPO; Microsoft publishes GPO backups for each STIG version.
- Windows 10/11 STIG — endpoint hardening including Credential Guard, BitLocker, AppLocker.

**Application STIGs:**
- Apache 2.4 STIG — TLS configuration, directory listing, server tokens, request limits.
- IIS 10.0 STIG — request filtering, logging, authentication settings.
- Microsoft SQL Server STIG — audit configuration, encryption, least-privilege database roles.
- Oracle Database 19c STIG — listener hardening, role separation, audit trail.

**Network Device STIGs:**
- Cisco IOS XE Router STIG — AAA, management plane hardening, control plane policing.
- Palo Alto STIG — security profiles, decryption policy, admin access restrictions.
- Juniper SRX STIG — zone-based firewall, screen protections, management access.

**Middleware/Platform STIGs:**
- Docker Enterprise STIG — overlaps significantly with CIS Docker Benchmark.
- Kubernetes STIG — API server, etcd, kubelet, network policy requirements.
- VMware vSphere STIG — ESXi host hardening, vCenter configuration, virtual machine isolation.

### 7.4 SCAP Content for Automated STIG Checking

DISA publishes STIG content in SCAP format (XCCDF + OVAL). The ComplianceAsCode (scap-security-guide) project also provides STIG profiles:

```bash
# Check available STIG profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml | grep -i stig

# Run STIG assessment
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_stig \
    --results /tmp/stig-results.xml \
    --report /tmp/stig-report.html \
    --oval-results \
    /usr/share/xml/scap/ssg/content/ssg-rhel9-ds.xml

# DISA-published SCC (SCAP Compliance Checker) — official DoD tool
# Download from: https://public.cyber.mil/stigs/scap/
# Usage is similar to oscap but with DISA-specific content
```

### 7.5 POA&M — Plan of Action and Milestones

When a STIG finding cannot be immediately remediated, a POA&M documents the risk acceptance and remediation timeline:

**POA&M Entry Structure:**

| Field | Content |
|-------|---------|
| Weakness/Finding | STIG rule ID + description (e.g., V-257844: RHEL 9 must disable SSH root login) |
| Severity | CAT I / II / III |
| Risk Assessment | Impact if not remediated (what can an attacker do) |
| Compensating Controls | Mitigations in place while the finding remains open |
| Scheduled Completion | Target date for remediation |
| Milestones | Intermediate steps (e.g., "Test in staging by 2026-06-01, deploy to production by 2026-06-15") |
| Resources Required | Budget, personnel, change window |
| Status | Open / In Progress / Completed / Risk Accepted |
| Responsible Party | Name and role of the person accountable |

### 7.6 STIG Exception Process

Exceptions (risk acceptances) follow a formal process:

1. **Document**: describe the finding, why remediation is not feasible (technical limitation, operational impact, vendor constraint).
2. **Compensating Controls**: identify mitigations that reduce residual risk (e.g., "SSH root login cannot be disabled because vendor appliance requires it; compensating control: SSH restricted to management VLAN, access logged and alerted, root SSH key rotated every 30 days").
3. **Approval**: the Authorizing Official (AO) or designated risk authority reviews and approves or rejects the exception.
4. **Duration**: exceptions have an expiration date and must be re-evaluated (typically annually).
5. **Tracking**: exceptions are tracked in the POA&M alongside open findings.

### 7.7 ACAS Integration

The Assured Compliance Assessment Solution (ACAS) — Tenable SecurityCenter deployed across DoD — combines vulnerability scanning with STIG compliance checking:

- Nessus scanners execute STIG audit files alongside vulnerability plugins.
- Results flow into SecurityCenter dashboards.
- STIG findings correlate with CVE-based vulnerabilities (a missing STIG control may correspond to an exploitable vulnerability).
- Dashboard views show compliance posture by STIG, by severity, by organizational unit.

---

## 8. Hardening per Ambienti Specifici

### 8.1 Network Devices

#### Cisco IOS/IOS-XE

Key hardening controls:

```
! Disable unused services
no ip http server
no ip http secure-server
no service pad
no ip bootp server
no ip source-route
no cdp run                  ! or limit to specific interfaces
no lldp run

! Management plane hardening
service password-encryption
enable secret 0 <strong-password>
username admin privilege 15 algorithm-type scrypt secret <password>

! AAA
aaa new-model
aaa authentication login default group tacacs+ local
aaa authorization exec default group tacacs+ local
aaa accounting exec default start-stop group tacacs+

! SSH only, no telnet
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
line vty 0 15
  transport input ssh
  access-class MGMT-ACL in

! NTP authentication
ntp authentication-key 1 md5 <key>
ntp trusted-key 1
ntp server 10.10.1.1 key 1

! Logging
logging buffered 16384 informational
logging host 10.10.5.5 transport udp port 514
service timestamps log datetime msec localtime show-timezone
```

#### Palo Alto Networks

Key hardening areas: admin access (MFA, role-based admin accounts, separate management interface), security profiles (antivirus, anti-spyware, vulnerability protection, URL filtering on all rules), decryption policy for TLS inspection, and strict zone-based policy with deny-all default.

#### Juniper SRX

Similar pattern: disable unnecessary services, enforce SSH-only management, configure screen protections (SYN flood, ICMP flood, port scan detection), apply security policies with default deny, enable structured syslog to SIEM.

### 8.2 Database Servers

#### PostgreSQL Hardening

```
# postgresql.conf
listen_addresses = '10.10.20.5'           # Not '*' — bind to specific interface
ssl = on
ssl_min_protocol_version = 'TLSv1.2'
ssl_cert_file = '/etc/ssl/certs/pg.crt'
ssl_key_file = '/etc/ssl/private/pg.key'
password_encryption = scram-sha-256       # Not md5
log_connections = on
log_disconnections = on
log_statement = 'ddl'                      # Log all DDL; 'all' for high-security
log_line_prefix = '%m [%p] %q%u@%d '
```

```
# pg_hba.conf — enforce SSL and scram-sha-256
hostssl all  all  10.10.20.0/24  scram-sha-256
host    all  all  0.0.0.0/0      reject
```

#### MySQL/MariaDB

```sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';
-- Remove test database
DROP DATABASE IF EXISTS test;
-- Disable remote root login
DELETE FROM mysql.user WHERE User='root' AND Host NOT IN ('localhost', '127.0.0.1', '::1');
FLUSH PRIVILEGES;
```

Key `my.cnf` hardening:

```ini
[mysqld]
bind-address = 10.10.20.5
local-infile = 0
skip-symbolic-links = yes
log-error = /var/log/mysql/error.log
general-log = 0
slow-query-log = 1
# TLS
require-secure-transport = ON
ssl-ca = /etc/mysql/certs/ca.pem
ssl-cert = /etc/mysql/certs/server-cert.pem
ssl-key = /etc/mysql/certs/server-key.pem
tls-version = TLSv1.2,TLSv1.3
```

### 8.3 Web Servers

#### Apache Hardening

```apache
# Hide server version
ServerTokens Prod
ServerSignature Off

# Disable directory listing
<Directory /var/www/html>
    Options -Indexes -FollowSymLinks
    AllowOverride None
</Directory>

# Disable unnecessary modules
# a2dismod autoindex status cgi

# Security headers
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
Header always set X-XSS-Protection "0"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'"
Header always set Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"

# TLS — modern configuration
SSLProtocol all -SSLv3 -TLSv1 -TLSv1.1
SSLCipherSuite ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384
SSLHonorCipherOrder off

# Request limits
LimitRequestBody 10485760
LimitRequestFields 50
LimitRequestFieldSize 8190
LimitRequestLine 8190
TimeOut 60
```

#### Nginx Hardening

```nginx
# Hide version
server_tokens off;

# Security headers
add_header X-Content-Type-Options "nosniff" always;
add_header X-Frame-Options "DENY" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# TLS
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# Request limits
client_max_body_size 10m;
client_body_timeout 12;
client_header_timeout 12;
send_timeout 10;

# Rate limiting
limit_req_zone $binary_remote_addr zone=req_limit:10m rate=10r/s;
```

### 8.4 Container Hosts

Beyond the CIS Docker benchmark controls covered in section 2.7, container host hardening requires:

- **Runtime security**: deploy Falco or Sysdig for runtime threat detection (syscall monitoring).
- **Image scanning**: integrate Trivy, Grype, or Snyk Container into CI/CD pipeline — no image with CRITICAL CVE reaches production.
- **Registry security**: private registry with signed images, vulnerability scanning on push, pull-through cache to avoid direct DockerHub dependency.
- **Rootless containers**: Docker rootless mode or Podman (rootless by default) eliminates the container-escape-to-root threat.
- **Read-only root filesystem**: `--read-only` flag forces containers to use tmpfs or volumes for writes, preventing persistent modification.

### 8.5 Cloud Instances — Golden AMI Pipeline

Golden images (AMI on AWS, managed image on Azure, custom image on GCP) are the standard approach for deploying pre-hardened systems in cloud environments. The pipeline:

1. **Base OS**: start from vendor-published image (Ubuntu, RHEL, Windows Server).
2. **Harden**: apply CIS/STIG controls via Ansible or Packer provisioner.
3. **Scan**: validate with OpenSCAP or CIS-CAT.
4. **Fix**: remediate remaining findings.
5. **Re-scan**: confirm compliance threshold met (target: 95%+).
6. **Bake**: create immutable image (AMI, managed image).
7. **Register**: tag with compliance metadata (benchmark version, scan date, score).
8. **Deploy**: launch instances only from approved golden images.
9. **Rotate**: rebuild golden images monthly or when new benchmark versions release.

### 8.6 IoT and Embedded Devices

Constrained devices require a pragmatic subset of hardening:

- **Disable unused services and protocols**: if the device doesn't need Telnet, HTTP management, SNMP — disable them.
- **Change default credentials**: the Mirai botnet spread via 60 default username/password combinations.
- **Enable encrypted management**: TLS for web admin, SSH instead of Telnet, SNMPv3 instead of v1/v2c.
- **Network segmentation**: IoT devices on dedicated VLANs with strict firewall rules — no direct access to corporate network.
- **Firmware updates**: maintain an inventory, subscribe to vendor advisories, patch within defined SLAs.
- **Certificate-based authentication**: for device-to-cloud communication, use X.509 certificates provisioned during manufacturing or onboarding.

---

## 9. Continuous Compliance

### 9.1 Configuration Monitoring

#### Wazuh SCA (Security Configuration Assessment)

Wazuh agents ship with SCA policies (YAML format) that continuously check system configuration against CIS benchmarks:

```yaml
# /var/ossec/ruleset/sca/cis_ubuntu22-04.yml (excerpt)
policy:
  id: "cis_ubuntu22_04"
  file: "cis_ubuntu22-04.yml"
  name: "CIS Ubuntu Linux 22.04 LTS Benchmark"
  description: "Checks for CIS Ubuntu 22.04 hardening"
  references:
    - https://www.cisecurity.org/benchmark/ubuntu_linux

checks:
  - id: 1001
    title: "Ensure /tmp is a separate partition"
    description: "The /tmp directory is a world-writable directory..."
    rationale: "Isolating /tmp prevents resource exhaustion and noexec enforcement"
    remediation: "Configure /tmp as a separate partition with noexec,nosuid,nodev"
    condition: all
    rules:
      - 'c:findmnt --kernel /tmp -> r:^/tmp'

  - id: 1002
    title: "Ensure noexec option set on /tmp partition"
    condition: all
    rules:
      - 'c:findmnt --kernel /tmp -> r:noexec'

  - id: 5001
    title: "Ensure SSH root login is disabled"
    condition: all
    rules:
      - 'f:/etc/ssh/sshd_config -> r:^\s*PermitRootLogin\s+no'
```

Wazuh SCA runs checks at configurable intervals (default: every 12 hours) and reports results to the Wazuh manager, where they appear in the dashboard with pass/fail status and remediation guidance.

#### AIDE (Advanced Intrusion Detection Environment)

```bash
# Initialize AIDE database
aide --init
mv /var/lib/aide/aide.db.new /var/lib/aide/aide.db

# Run check
aide --check

# Cron job for daily integrity check
echo "0 5 * * * root /usr/sbin/aide --check | mail -s 'AIDE Report' security@corp.internal" \
    >> /etc/crontab
```

#### Tripwire

Commercial (Tripwire Enterprise) or open-source (Open Source Tripwire). Same concept as AIDE — file integrity monitoring with cryptographic database of known-good file hashes. Tripwire Enterprise adds policy-based configuration assessment, real-time change detection, and integration with ITSM platforms.

### 9.2 Drift Detection and Alerting

Effective drift detection requires:

1. **Baseline definition**: the desired state (Ansible playbook, DSC configuration, InSpec profile).
2. **Continuous scanning**: scheduled runs of compliance tools (OpenSCAP daily, InSpec in CI/CD, Wazuh SCA continuous).
3. **Alerting on drift**: integration with alerting platforms when a previously compliant system drops below threshold.
4. **Severity classification**: not all drift is equal — `PermitRootLogin yes` is CAT I drift; a missing login banner is CAT III.

Example Wazuh alert rule for SCA failure:

```xml
<rule id="100201" level="10">
  <if_sid>19100</if_sid>
  <field name="sca.check.result">failed</field>
  <field name="sca.check.title">SSH root login</field>
  <description>CIS CRITICAL: SSH root login is enabled — drift detected</description>
</rule>
```

### 9.3 Auto-Remediation

Automated remediation is powerful but dangerous. Risk assessment before enabling:

| Factor | Auto-Remediate | Manual Review |
|--------|---------------|---------------|
| Low-risk controls (banners, permissions) | Yes | - |
| Network configuration (firewall, sysctl) | Carefully — test first | Preferred |
| Authentication settings (PAM, SSH) | No — risk of lockout | Required |
| Service state (enable/disable) | Case-by-case | Preferred for production |
| Kernel parameters (sysctl) | Idempotent ones only | Required for new parameters |

Implementation pattern with Ansible:

```yaml
# cis-auto-remediate.yml — runs from cron, fixes low-risk drift
- name: Auto-remediate low-risk CIS drift
  hosts: all
  become: true
  vars:
    auto_remediate_only: true  # Flag that limits scope to safe controls
  tasks:
    - name: Ensure file permissions on /etc/passwd
      file:
        path: /etc/passwd
        owner: root
        group: root
        mode: '0644'

    - name: Ensure file permissions on /etc/shadow
      file:
        path: /etc/shadow
        owner: root
        group: shadow
        mode: '0000'

    - name: Ensure login banner
      copy:
        dest: /etc/issue.net
        content: |
          ******************************************************************
          AUTHORIZED ACCESS ONLY. All activity is monitored and recorded.
          Unauthorized access is prohibited and will be prosecuted.
          ******************************************************************
        owner: root
        group: root
        mode: '0644'

    - name: Ensure kernel modules are disabled
      copy:
        dest: "/etc/modprobe.d/disable-{{ item }}.conf"
        content: |
          install {{ item }} /bin/true
          blacklist {{ item }}
      loop:
        - cramfs
        - freevxfs
        - jffs2
        - hfs
        - hfsplus
        - udf
```

### 9.4 Compliance Dashboards

#### Grafana with OpenSCAP/Wazuh Data

Architecture: Wazuh → Elasticsearch/OpenSearch → Grafana data source → compliance dashboards.

Key panels:
- **Compliance score over time** (line chart, per-host and aggregate).
- **Failed controls by severity** (bar chart, CAT I/II/III or CIS Level 1/2).
- **Top 10 most frequently failing controls** (table with host count).
- **Drift events** (time series of compliance score changes).
- **Host compliance heatmap** (matrix of hosts vs control families).

#### Kibana with Wazuh

Wazuh provides pre-built Kibana dashboards for SCA. The "Security Configuration Assessment" dashboard shows:
- Global compliance percentage.
- Per-agent compliance breakdown.
- Failed check details with remediation steps.
- Trend analysis over configurable time ranges.

### 9.5 Integration with Change Management

Hardening is not a one-time project — it must integrate with ITIL change management:

- **Standard changes**: routine hardening updates (quarterly benchmark updates, monthly golden image rebuilds) should be pre-approved standard changes.
- **Normal changes**: new hardening controls that may impact applications require CAB review, testing in staging, rollback plan.
- **Emergency changes**: critical STIG finding (CAT I) discovered during incident response — document but fast-track remediation.
- **Post-implementation review**: every hardening change should include a compliance scan before and after to validate the change achieved its goal.

### 9.6 Compliance Evidence for Audits

Auditors (PCI QSA, ISO 27001 certification body, FedRAMP 3PAO) require evidence that controls are implemented and maintained. For configuration baselines, the evidence package includes:

- **Scan reports**: timestamped CIS-CAT/OpenSCAP/Nessus compliance reports showing assessment date, scope, and score.
- **Remediation records**: tickets or POA&M entries showing that failed controls were addressed.
- **Trend data**: compliance scores over time demonstrating sustained compliance (not point-in-time cleanup before audit).
- **Golden image documentation**: build process, scan results at bake time, image version inventory.
- **Exception register**: formally approved risk acceptances with compensating controls.

### 9.7 Regulatory Mapping

CIS Benchmarks map to multiple regulatory frameworks. Key mappings:

| CIS Control / Benchmark Area | PCI-DSS v4.0 | HIPAA | SOC 2 | ISO 27001:2022 |
|------------------------------|-------------|-------|-------|----------------|
| Configuration standards | Req. 2.2 | §164.312(a)(1) | CC6.1, CC7.1 | A.8.9 |
| Access control (SSH, PAM) | Req. 7, 8 | §164.312(a)(1), (d) | CC6.1-6.3 | A.8.2-8.5 |
| Audit logging | Req. 10 | §164.312(b) | CC7.2 | A.8.15-8.16 |
| Firewall configuration | Req. 1 | §164.312(e)(1) | CC6.6 | A.8.20-8.22 |
| Encryption at rest | Req. 3.5 | §164.312(a)(2)(iv) | CC6.1 | A.8.24 |
| Malware protection | Req. 5 | §164.308(a)(5)(ii)(B) | CC6.8 | A.8.7 |
| Patch management | Req. 6.3 | §164.308(a)(5)(ii)(B) | CC7.1 | A.8.8 |

This mapping allows a single CIS hardening effort to provide evidence for multiple compliance obligations simultaneously.

---

## 10. Laboratorio Pratico

### 10.1 Obiettivo

Build a golden image pipeline that takes a base OS, applies CIS hardening via Ansible, scans with OpenSCAP and CIS-CAT, remediates remaining findings, re-scans to confirm compliance, and produces a deployment-ready template. Then validate the hardened system resists common exploitation techniques.

### 10.2 Lab Environment

| Component | Specification |
|-----------|--------------|
| Hypervisor | KVM/QEMU, VirtualBox, or VMware Workstation |
| Base OS | Ubuntu Server 22.04 LTS (minimal install) |
| Ansible Controller | Any Linux host with Ansible 2.14+ |
| Scanning Tools | OpenSCAP (oscap), Lynis |
| Attack Tools | Kali Linux with Nmap, Nikto, LinPEAS, Metasploit |

### 10.3 Phase 1 — Base OS Installation

```bash
# Install Ubuntu Server 22.04 minimal
# During installation:
# - Create separate /tmp, /var, /var/log, /home partitions (LVM recommended)
# - Set strong root password
# - Create non-root admin user
# - Enable SSH server

# Post-install: update packages
apt update && apt upgrade -y

# Install required packages
apt install -y openssh-server auditd libpam-pwquality aide ufw
```

### 10.4 Phase 2 — CIS Hardening with Ansible

```bash
# On Ansible controller:
pip install ansible
ansible-galaxy install ansible-lockdown.UBUNTU22-CIS

# Create inventory
cat > inventory.ini <<'INV'
[golden_image]
10.10.100.50 ansible_user=admin ansible_become=yes
INV

# Create playbook (use the one from section 5.1 as baseline)
# Then apply:
ansible-playbook -i inventory.ini cis-harden-ubuntu.yml -v
```

### 10.5 Phase 3 — Initial Scan with OpenSCAP

```bash
# On the target system
apt install -y libopenscap8 ssg-ubuntu

# Run CIS assessment
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --results /root/cis-scan-1.xml \
    --report /root/cis-report-1.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

echo "First scan complete. Review /root/cis-report-1.html"

# Also run Lynis
lynis audit system --pentest | tee /root/lynis-scan-1.txt
```

### 10.6 Phase 4 — Remediate Remaining Findings

After reviewing the OpenSCAP report, identify controls that the Ansible role missed or that require manual intervention. Common remaining findings:

```bash
# Example: GRUB password not set by Ansible (requires interactive hash generation)
grub-mkpasswd-pbkdf2
# Apply the hash to /etc/grub.d/40_custom as shown in section 3.2
update-grub

# Example: Audit rules need regeneration for privileged commands
find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | \
    awk '{print "-a always,exit -F path="$1" -F perm=x -F auid>=1000 -F auid!=4294967295 -k privileged"}' \
    >> /etc/audit/rules.d/privileged.rules
augenrules --load

# Example: Ensure no world-writable directories without sticky bit
find / -xdev -type d \( -perm -0002 -a ! -perm -1000 \) 2>/dev/null | \
    while read dir; do chmod +t "$dir"; done
```

### 10.7 Phase 5 — Re-Scan and Validate

```bash
# Re-scan with OpenSCAP
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --results /root/cis-scan-2.xml \
    --report /root/cis-report-2.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# Compare scores
echo "=== Score Comparison ==="
echo "Scan 1:"
oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml 2>&1 | tail -5
echo "---"
echo "Scan 2: (should show improvement)"

# Run InSpec for additional validation
inspec exec https://github.com/dev-sec/linux-baseline --reporter cli html:/root/inspec-report.html
inspec exec https://github.com/dev-sec/ssh-baseline --reporter cli html:/root/ssh-inspec-report.html
```

### 10.8 Phase 6 — Template for Deployment

```bash
# Clean up before templating
# Remove SSH host keys (will regenerate on first boot)
rm -f /etc/ssh/ssh_host_*

# Remove machine-specific identifiers
truncate -s 0 /etc/machine-id

# Clean logs
find /var/log -type f -exec truncate -s 0 {} \;

# Clean bash history
unset HISTFILE
rm -f /root/.bash_history /home/*/.bash_history

# Remove temporary files
rm -rf /tmp/* /var/tmp/*

# Shut down and create template
shutdown -h now
# Then snapshot/clone the VM as golden image
```

For AWS, use Packer:

```hcl
# golden-image.pkr.hcl
source "amazon-ebs" "ubuntu_cis" {
  ami_name      = "ubuntu-2204-cis-{{timestamp}}"
  instance_type = "t3.medium"
  region        = "eu-west-1"
  source_ami_filter {
    filters = {
      name                = "ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"
      root-device-type    = "ebs"
      virtualization-type = "hvm"
    }
    owners      = ["099720109477"]  # Canonical
    most_recent = true
  }
  ssh_username = "ubuntu"
}

build {
  sources = ["source.amazon-ebs.ubuntu_cis"]

  provisioner "ansible" {
    playbook_file = "cis-harden-ubuntu.yml"
  }

  provisioner "shell" {
    inline = [
      "sudo oscap xccdf eval --profile xccdf_org.ssgproject.content_profile_cis_level1_server --report /tmp/cis-report.html /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml || true",
      "sudo cat /tmp/cis-report.html"
    ]
  }
}
```

### 10.9 Phase 7 — Attack Validation

From a Kali Linux attacker box, test that hardening actually blocks common exploitation:

```bash
# 1. Port scan — verify minimal attack surface
nmap -sS -sV -O -p- 10.10.100.50

# Expected: only SSH (22) open, no other services
# Verify: no version disclosure, OS fingerprinting should be uncertain

# 2. SSH enumeration — verify hardening resists common attacks
nmap --script ssh-auth-methods,ssh-brute -p 22 10.10.100.50

# Expected: password auth disabled (key-only), no root login

# 3. Brute force test — verify account lockout
hydra -l admin -P /usr/share/wordlists/rockyou.txt ssh://10.10.100.50 -t 4

# Expected: lockout after 5 attempts (PAM faillock)

# 4. Privilege escalation check — run LinPEAS on the target
# (requires initial access via SSH key)
curl -sL https://github.com/carlospolop/PEASS-ng/releases/latest/download/linpeas.sh | sh

# Expected results on hardened system:
# - No SUID abuse vectors (common SUID binaries are expected, not exploitable)
# - No world-writable files in sensitive locations
# - No kernel module loading possible (modules loading audited)
# - No /tmp execution (noexec mount blocks payload execution)
# - ptrace restricted (prevents process injection)
# - ASLR enabled (makes memory exploitation unreliable)

# 5. Docker socket check (if Docker is installed)
# Verify socket is not world-accessible
ls -la /var/run/docker.sock
# Expected: srw-rw---- root docker (not world-readable)

# 6. Network-level attacks — verify sysctl hardening
# From attacker: attempt ICMP redirect
# Expected: dropped (accept_redirects = 0)

# From attacker: attempt source-routed packet
# Expected: dropped (accept_source_route = 0)
```

### 10.10 Phase 8 — Continuous Monitoring Setup

```bash
# Install Wazuh agent on the golden image
curl -sO https://packages.wazuh.com/4.x/apt/pool/main/w/wazuh-agent/wazuh-agent_4.9.0-1_amd64.deb
dpkg -i wazuh-agent_4.9.0-1_amd64.deb

# Configure manager connection
cat > /var/ossec/etc/ossec.conf <<'WAZUH'
<ossec_config>
  <client>
    <server>
      <address>wazuh-manager.corp.internal</address>
      <port>1514</port>
      <protocol>tcp</protocol>
    </server>
  </client>
  <sca>
    <enabled>yes</enabled>
    <scan_on_start>yes</scan_on_start>
    <interval>12h</interval>
    <policies>
      <policy>/var/ossec/ruleset/sca/cis_ubuntu22-04.yml</policy>
    </policies>
  </sca>
  <syscheck>
    <frequency>43200</frequency>
    <directories check_all="yes" report_changes="yes">/etc,/usr/bin,/usr/sbin</directories>
    <directories check_all="yes" report_changes="yes">/boot</directories>
  </syscheck>
</ossec_config>
WAZUH

systemctl enable wazuh-agent
systemctl start wazuh-agent

# Verify SCA is running
cat /var/ossec/logs/ossec.log | grep -i sca
```

### 10.11 Deliverables Checklist

At the end of this lab, you should have:

- [ ] A golden image with CIS Level 1 Server controls applied.
- [ ] OpenSCAP HTML report showing ≥92% compliance score.
- [ ] Lynis report with Hardening Index ≥80.
- [ ] InSpec report confirming `dev-sec/linux-baseline` and `ssh-baseline` pass.
- [ ] Nmap scan output confirming minimal attack surface.
- [ ] LinPEAS output confirming no trivial privilege escalation paths.
- [ ] Wazuh SCA dashboard showing the system as compliant.
- [ ] Documented POA&M for any controls that could not be implemented (with compensating controls).
- [ ] Packer template or equivalent for reproducible golden image builds.
- [ ] Ansible playbook version-controlled in Git for repeatable hardening.

---

## 11. CIS Controls v8.1 — Approfondimento Safeguard 4

### 11.1 Struttura del CIS Control 4 — Secure Configuration of Enterprise Assets and Software

Il CIS Control 4 nella versione 8.1 (rilasciata a giugno 2024) rappresenta il cuore operativo della gestione delle configurazioni sicure. Contiene 12 safeguard specifiche, organizzate per Implementation Group (IG), che coprono l'intero ciclo di vita della configurazione — dall'inventario iniziale alla verifica continua. Ogni safeguard e' classificata in base alla maturita' organizzativa richiesta per l'implementazione.

I tre Implementation Groups riflettono livelli crescenti di capacita' e risorse:

- **IG1 (Cyber Hygiene di Base)**: rappresenta il minimo indispensabile per qualsiasi organizzazione. Include la definizione di processi di configurazione sicura, il blocco automatico delle sessioni inattive e la gestione di firewall su endpoint.
- **IG2 (Organizzazioni con Risorse Moderate)**: estende IG1 con gestione centralizzata dei firewall, disabilitazione di servizi non necessari, configurazione sicura di DNS e eliminazione di account predefiniti.
- **IG3 (Organizzazioni ad Alto Rischio)**: aggiunge sandboxing per navigazione web, filtraggio URL avanzato e controllo granulare degli accessi alle applicazioni.

### 11.2 Tabella Completa dei 12 Safeguard

| ID Safeguard | Titolo | IG1 | IG2 | IG3 | Descrizione Operativa |
|---|---|---|---|---|---|
| 4.1 | Establish and Maintain a Secure Configuration Process | X | X | X | Definire un processo formale per creare, documentare e mantenere configurazioni sicure per tutti gli asset aziendali. Revisionare almeno annualmente. |
| 4.2 | Establish and Maintain a Secure Configuration Process for Network Infrastructure | X | X | X | Applicare configurazioni sicure a router, switch, firewall, access point. Include ACL, protocolli di gestione cifrati, disabilitazione servizi inutili. |
| 4.3 | Configure Automatic Session Locking on Enterprise Assets | X | X | X | Blocco automatico dello schermo dopo massimo 15 minuti di inattivita'. Riduce il rischio di accesso fisico non autorizzato. |
| 4.4 | Implement and Manage a Firewall on Servers | X | X | X | Firewall attivo su ogni server con policy deny-all in ingresso. Solo porte/servizi esplicitamente necessari sono aperti. |
| 4.5 | Implement and Manage a Firewall on End-User Devices | X | X | X | Firewall attivo su ogni endpoint (workstation, laptop). Default deny inbound su tutte le interfacce. |
| 4.6 | Securely Manage Enterprise Assets and Software | | X | X | Gestione centralizzata delle configurazioni tramite strumenti come Ansible, Puppet, SCCM, Intune. Non permettere configurazioni manuali ad hoc. |
| 4.7 | Manage Default Accounts on Enterprise Assets and Software | | X | X | Disabilitare, rinominare o cambiare le credenziali degli account predefiniti (admin, root, sa, guest) su tutti i sistemi e software. |
| 4.8 | Uninstall or Disable Unnecessary Services on Enterprise Assets and Software | | X | X | Rimuovere servizi, daemon e protocolli non richiesti dal ruolo del sistema. Ogni servizio in ascolto e' una superficie di attacco. |
| 4.9 | Configure Trusted DNS Servers on Enterprise Assets | | X | X | Configurare tutti gli asset per utilizzare DNS interni aziendali con DNSSEC validation. Impedisce DNS hijacking e phishing. |
| 4.10 | Enforce Automatic Device Lockout on Portable End-User Devices | | X | X | Dispositivi mobili si bloccano automaticamente dopo massimo 5 minuti di inattivita'. Richiede PIN/biometria per lo sblocco. |
| 4.11 | Enforce Remote Wipe Capability on Portable End-User Devices | | | X | Capacita' di cancellazione remota per dispositivi mobili smarriti o rubati tramite MDM (Mobile Device Management). |
| 4.12 | Separate Enterprise Workspaces on Mobile End-User Devices | | | X | Separazione tra dati aziendali e personali su dispositivi BYOD tramite containerizzazione (Android Work Profile, iOS Managed Apps). |

### 11.3 Mappatura CIS Control 4 verso NIST SP 800-53 Rev. 5

La correlazione tra CIS Controls v8.1 e NIST SP 800-53 Rev. 5 e' fondamentale per le organizzazioni che devono soddisfare requisiti federali statunitensi o framework derivati:

| CIS Safeguard | NIST 800-53 Controls | Descrizione NIST |
|---|---|---|
| 4.1 | CM-1, CM-2, CM-6 | Configuration Management Policy, Baseline Configuration, Configuration Settings |
| 4.2 | CM-6, CM-7, SC-7 | Configuration Settings, Least Functionality, Boundary Protection |
| 4.3 | AC-11, AC-12 | Session Lock, Session Termination |
| 4.4, 4.5 | SC-7, CM-7 | Boundary Protection, Least Functionality |
| 4.6 | CM-3, CM-5 | Configuration Change Control, Access Restrictions for Change |
| 4.7 | IA-5, CM-6 | Authenticator Management, Configuration Settings |
| 4.8 | CM-7, CM-11 | Least Functionality, User-Installed Software |
| 4.9 | SC-20, SC-21, SC-22 | Secure Name/Address Resolution, Secure Resolution Service, Architecture and Provisioning for DNS |
| 4.10, 4.11, 4.12 | AC-19, MP-6 | Access Control for Mobile Devices, Media Sanitization |

### 11.4 Assessment Specification per CIS Control 4

Il CIS Controls Assessment Specification (CAS) fornisce metriche precise per misurare l'implementazione di ogni safeguard. Per il Control 4, le metriche chiave sono:

**Per Safeguard 4.1 — Secure Configuration Process:**
- Numero di asset con configurazione baseline documentata vs. totale asset in inventario
- Percentuale di asset conformi alla baseline nell'ultimo ciclo di scansione
- Data dell'ultima revisione del processo di configurazione sicura

**Per Safeguard 4.8 — Unnecessary Services:**
- Numero di servizi in ascolto per host (target: solo servizi documentati nel ruolo del sistema)
- Frequenza di scansione per servizi non autorizzati (target: settimanale)
- Tempo medio di remediation per servizi non autorizzati scoperti

**Formula di compliance aggregata:**

```
Compliance Score = (Numero asset conformi / Numero totale asset) x 100

Target per IG:
  IG1: >= 80%
  IG2: >= 90%
  IG3: >= 95%
```

### 11.5 Relazione tra CIS Controls e CIS Benchmarks

E' essenziale distinguere tra CIS Controls e CIS Benchmarks — i due prodotti CIS sono complementari ma servono scopi diversi:

| Aspetto | CIS Controls v8.1 | CIS Benchmarks |
|---|---|---|
| Scopo | Framework strategico di 18 famiglie di controlli per la sicurezza aziendale | Guide prescriptive per la configurazione sicura di una specifica tecnologia |
| Granularita' | Alta (safeguard generali applicabili a qualsiasi tecnologia) | Molto alta (centinaia di impostazioni specifiche per OS/software) |
| Esempio | "4.4: Implement and Manage a Firewall on Servers" | "CIS Ubuntu 22.04 3.5.1.1: Ensure UFW is installed" |
| Formato | PDF, Excel, navigatore online | PDF, XCCDF/OVAL (machine-readable), SCAP datastream |
| Implementazione | Processo organizzativo + strumenti | Configurazione tecnica diretta su sistemi |

Nella pratica, il flusso e': CIS Controls definiscono _cosa_ deve essere protetto → CIS Benchmarks specificano _come_ configurare ogni tecnologia per raggiungere quel livello di protezione → strumenti di automazione (Ansible, OpenSCAP) implementano e verificano le configurazioni.

---

## 12. Hardening Avanzato per Piattaforme Moderne

### 12.1 Windows Server 2025 — Nuove Funzionalita' di Sicurezza e CIS Benchmark

Windows Server 2025, rilasciato a novembre 2024 con CIS Benchmark disponibile da marzo 2025, introduce significative innovazioni nella sicurezza che impattano le configuration baselines:

**Virtualization-Based Security (VBS) Migliorata:**
VBS utilizza l'hypervisor Hyper-V per creare regioni di memoria isolate dal sistema operativo principale. In Windows Server 2025, VBS e' abilitata per default nelle installazioni con hardware compatibile, proteggendo:
- Credential Guard (isolamento credenziali in un enclave sicuro)
- Kernel-mode Code Integrity (HVCI) — verifica che solo codice firmato esegua nel kernel
- Secure Kernel — kernel secondario protetto dall'hypervisor

**Hotpatch:**
Aggiornamenti di sicurezza applicati senza riavvio del sistema, riducendo drasticamente la finestra di esposizione tra rilascio patch e applicazione. Per le configuration baselines, questo significa che la policy di patching puo' essere piu' aggressiva senza impatto sulla disponibilita'.

**OSConfig — Strumento Nativo per Baselines:**
Microsoft ha introdotto OSConfig come strumento nativo per applicare e verificare security baselines su Windows Server 2025:

```powershell
# Verificare lo stato delle baselines con OSConfig
Get-OSConfigDesiredConfiguration

# Applicare la baseline di sicurezza Microsoft
Set-OSConfigDesiredConfiguration -Scenario SecurityBaseline

# Verificare la compliance dopo l'applicazione
Get-OSConfigDesiredConfiguration | Where-Object { $_.Status -ne 'Compliant' }

# Applicare la baseline CIS Level 1
Set-OSConfigDesiredConfiguration -Scenario CISLevel1

# Applicare la baseline STIG
Set-OSConfigDesiredConfiguration -Scenario STIG
```

**CIS Benchmark Windows Server 2025 — Controlli Chiave Nuovi:**

```powershell
# Abilitare HVCI (Hypervisor-protected Code Integrity)
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" `
    /v Enabled /t REG_DWORD /d 1 /f

# Abilitare Hotpatch (richiede Azure Arc o subscription appropriata)
# Configurazione via Azure Policy o Intune

# Configurare Windows Firewall con logging avanzato
Set-NetFirewallProfile -Profile Domain,Public,Private `
    -LogBlocked True -LogAllowed True `
    -LogMaxSizeKilobytes 32768 `
    -LogFileName "%systemroot%\system32\LogFiles\Firewall\pfirewall.log"

# Abilitare protezione avanzata contro relay NTLM
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa\MSV1_0" `
    /v RestrictSendingNTLMTraffic /t REG_DWORD /d 2 /f

# Disabilitare TLS 1.0 e 1.1 completamente
$protocols = @('TLS 1.0', 'TLS 1.1')
foreach ($protocol in $protocols) {
    $serverPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Server"
    $clientPath = "HKLM:\SYSTEM\CurrentControlSet\Control\SecurityProviders\SCHANNEL\Protocols\$protocol\Client"
    New-Item -Path $serverPath -Force | Out-Null
    New-Item -Path $clientPath -Force | Out-Null
    Set-ItemProperty -Path $serverPath -Name Enabled -Value 0 -Type DWord
    Set-ItemProperty -Path $serverPath -Name DisabledByDefault -Value 1 -Type DWord
    Set-ItemProperty -Path $clientPath -Name Enabled -Value 0 -Type DWord
    Set-ItemProperty -Path $clientPath -Name DisabledByDefault -Value 1 -Type DWord
}
```

### 12.2 Kubernetes Avanzato — CIS Benchmark e kube-bench

Il CIS Kubernetes Benchmark (versione corrente 1.9+, con oltre 200 raccomandazioni) copre cinque aree principali: control plane, worker nodes, policies, network, e managed services. Lo strumento open-source `kube-bench` di Aqua Security automatizza la verifica di conformita'.

**Installazione e Utilizzo di kube-bench:**

```bash
# Esecuzione come Job Kubernetes
kubectl apply -f https://raw.githubusercontent.com/aquasecurity/kube-bench/main/job.yaml

# Visualizzare i risultati
kubectl logs job/kube-bench

# Esecuzione diretta su un nodo del control plane
kube-bench run --targets master

# Esecuzione su un worker node
kube-bench run --targets node

# Output in formato JSON per integrazione con SIEM
kube-bench run --json --outputfile /tmp/kube-bench-results.json

# Filtrare per specifiche sezioni CIS
kube-bench run --targets master --check 1.2.1,1.2.2,1.2.3
```

**Pod Security Standards (PSS) — Sostituto di PodSecurityPolicy:**

Dalla versione 1.25 di Kubernetes, PodSecurityPolicy e' stata rimossa. I Pod Security Standards definiscono tre profili:

```yaml
# Applicare Pod Security Standards a livello di namespace
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Enforce: rifiuta pod che violano il profilo "restricted"
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest
    # Warn: avvisa per violazioni del profilo "restricted"
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: latest
    # Audit: registra violazioni nel log di audit
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: latest
```

**Profilo "restricted" — Configurazione di sicurezza completa per Pod:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secure-app
  namespace: production
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 65534
    fsGroup: 65534
    seccompProfile:
      type: RuntimeDefault
  automountServiceAccountToken: false
  containers:
    - name: app
      image: registry.corp.internal/app:v1.2.3@sha256:abc123...
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop:
            - ALL
        runAsNonRoot: true
      resources:
        limits:
          memory: "256Mi"
          cpu: "500m"
        requests:
          memory: "128Mi"
          cpu: "250m"
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir:
        sizeLimit: "100Mi"
```

**Kubescape — Scanner CIS Avanzato per Kubernetes:**

```bash
# Installazione
curl -s https://raw.githubusercontent.com/kubescape/kubescape/master/install.sh | bash

# Scansione CIS Benchmark completa
kubescape scan framework cis-v1.23-t1.0.1

# Scansione NSA-CISA hardening
kubescape scan framework nsa

# Scansione MITRE ATT&CK
kubescape scan framework mitre

# Scansione specifica per un namespace
kubescape scan framework cis-v1.23-t1.0.1 --include-namespaces production

# Export risultati in formato SARIF (per integrazione IDE/CI)
kubescape scan framework cis-v1.23-t1.0.1 --format sarif --output results.sarif

# Scansione di manifest YAML prima del deploy (shift-left)
kubescape scan *.yaml --format json --output pre-deploy-scan.json
```

**Network Policies — Implementazione Zero-Trust Networking:**

```yaml
# Default deny all ingress ed egress per un namespace
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress

---
# Permettere solo traffico specifico verso il database
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-to-db
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: postgres
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - protocol: TCP
          port: 5432
```

### 12.3 Cloud-Native Hardening — Terraform Compliance as Code

L'approccio moderno alla sicurezza delle configurazioni cloud prevede l'integrazione della compliance direttamente nella pipeline Infrastructure as Code. Terraform, combinato con strumenti di policy enforcement, permette di bloccare configurazioni insicure prima che raggiungano la produzione.

**OPA (Open Policy Agent) con Conftest per Terraform:**

```rego
# policy/aws_security.rego
package main

# Bloccare bucket S3 pubblici
deny[msg] {
    resource := input.resource.aws_s3_bucket[name]
    not resource.server_side_encryption_configuration
    msg := sprintf("S3 bucket '%s' deve avere la crittografia server-side abilitata (CIS AWS 2.1.1)", [name])
}

deny[msg] {
    resource := input.resource.aws_s3_bucket_public_access_block[name]
    not resource.block_public_acls
    msg := sprintf("S3 bucket '%s' deve bloccare ACL pubbliche (CIS AWS 2.1.5)", [name])
}

# Bloccare security group con ingress 0.0.0.0/0 su porte sensibili
deny[msg] {
    resource := input.resource.aws_security_group[name]
    ingress := resource.ingress[_]
    ingress.cidr_blocks[_] == "0.0.0.0/0"
    ingress.from_port <= 22
    ingress.to_port >= 22
    msg := sprintf("Security group '%s' permette SSH da qualsiasi IP (CIS AWS 5.2)", [name])
}

deny[msg] {
    resource := input.resource.aws_security_group[name]
    ingress := resource.ingress[_]
    ingress.cidr_blocks[_] == "0.0.0.0/0"
    ingress.from_port <= 3389
    ingress.to_port >= 3389
    msg := sprintf("Security group '%s' permette RDP da qualsiasi IP (CIS AWS 5.3)", [name])
}

# Richiedere crittografia EBS
deny[msg] {
    resource := input.resource.aws_ebs_volume[name]
    not resource.encrypted
    msg := sprintf("EBS volume '%s' deve essere crittografato (CIS AWS 2.2.1)", [name])
}
```

**Esecuzione della validazione in CI/CD:**

```bash
# Generare il piano Terraform in formato JSON
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Validare con Conftest
conftest test tfplan.json --policy policy/ --output json

# Integrazione con Checkov (scanner IaC completo)
checkov -d . --framework terraform --check CIS --output json > checkov-results.json

# Integrazione con tfsec (scanner specifico Terraform)
tfsec . --format json --out tfsec-results.json

# Prowler per scansione account AWS esistente
prowler aws --compliance cis_2.0 --output-formats json-asff --output-directory ./prowler-reports/
```

**Modulo Terraform per S3 conforme CIS:**

```hcl
# modules/secure-s3/main.tf
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "this" {
  bucket = aws_s3_bucket.this.id
  versioning_configuration {
    status = "Enabled"  # CIS AWS 2.1.3
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"  # CIS AWS 2.1.1
      kms_master_key_id = var.kms_key_id
    }
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "this" {
  bucket                  = aws_s3_bucket.this.id
  block_public_acls       = true   # CIS AWS 2.1.5
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "this" {
  bucket        = aws_s3_bucket.this.id
  target_bucket = var.logging_bucket_id  # CIS AWS 2.1.2
  target_prefix = "s3-access-logs/${var.bucket_name}/"
}

resource "aws_s3_bucket_lifecycle_configuration" "this" {
  bucket = aws_s3_bucket.this.id
  rule {
    id     = "transition-to-glacier"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "GLACIER"
    }
  }
}
```

---

## 13. Security Automation Framework e Pipeline CI/CD

### 13.1 MITRE SAF (Security Automation Framework)

Il MITRE Security Automation Framework (SAF) rappresenta l'evoluzione piu' significativa nella gestione automatizzata della compliance STIG. Il framework comprende quattro componenti principali:

**Componenti del SAF:**

| Componente | Funzione | Tecnologia |
|---|---|---|
| **Vulcan** | Authoring di contenuti STIG in formato InSpec | Web application Ruby on Rails |
| **InSpec Profiles** | Validazione automatizzata dei requisiti STIG | Chef InSpec (Ruby DSL) |
| **SAF CLI** | Conversione formati (InSpec → CKL, XCCDF, CSV) e aggregazione risultati | Node.js CLI |
| **Heimdall** | Visualizzazione e analisi dei risultati di compliance | Vue.js web application |

**Flusso operativo del SAF:**

```
Documentazione STIG (PDF/XCCDF)
       ↓
    Vulcan (authoring)
       ↓
  InSpec Profile (codice di validazione)
       ↓
  Esecuzione su target (locale/remoto/container)
       ↓
  Output JSON (risultati InSpec)
       ↓
    SAF CLI (conversione)
       ↓
  CKL per STIG Viewer / XCCDF per SCAP / CSV per analisi
       ↓
    Heimdall (dashboard)
```

**Utilizzo del SAF CLI:**

```bash
# Installazione SAF CLI
npm install -g @mitre/saf

# Convertire risultati InSpec in formato CKL (per STIG Viewer)
saf convert hdf2ckl -i inspec-results.json -o stig-checklist.ckl

# Convertire risultati InSpec in XCCDF
saf convert hdf2xccdf -i inspec-results.json -o xccdf-results.xml

# Aggregare risultati da piu' profili InSpec
saf view summary -i results1.json results2.json results3.json

# Generare report di compliance con soglie
saf validate threshold -i inspec-results.json \
    --templateFile threshold.yml

# Confrontare risultati tra due scan (drift detection)
saf compare -i baseline-results.json current-results.json \
    --output drift-report.json
```

**File di soglia per validazione automatica:**

```yaml
# threshold.yml — Soglie di accettazione per CI/CD
compliance:
  min: 85.0  # Percentuale minima di controlli conformi
failed:
  critical:
    max: 0   # Zero controlli critici in stato "failed"
  high:
    max: 3   # Massimo 3 controlli "high" in stato "failed"
error:
  max: 5     # Massimo 5 errori di esecuzione (es. controlli non eseguibili)
skipped:
  max: 10    # Massimo 10 controlli saltati
```

### 13.2 Pipeline CI/CD per Compliance Continua

L'integrazione della compliance nelle pipeline CI/CD trasforma il controllo delle configurazioni da attivita' periodica a validazione continua. La pipeline tipo prevede la verifica in ogni fase: build, test, staging, produzione.

**Pipeline GitLab CI per Hardening e Compliance:**

```yaml
# .gitlab-ci.yml
stages:
  - build
  - harden
  - scan
  - validate
  - deploy

variables:
  COMPLIANCE_THRESHOLD: "85"
  TARGET_HOST: "10.10.100.50"
  INSPEC_PROFILE: "https://github.com/dev-sec/linux-baseline"

build-golden-image:
  stage: build
  image: hashicorp/packer:latest
  script:
    - packer validate golden-image.pkr.hcl
    - packer build golden-image.pkr.hcl
  artifacts:
    paths:
      - manifest.json

apply-hardening:
  stage: harden
  image: willhallonline/ansible:latest
  script:
    - ansible-playbook -i inventory.ini cis-harden-ubuntu.yml --check --diff
    - ansible-playbook -i inventory.ini cis-harden-ubuntu.yml
  when: on_success

openscap-scan:
  stage: scan
  script:
    - ssh admin@${TARGET_HOST} "oscap xccdf eval
        --profile xccdf_org.ssgproject.content_profile_cis_level1_server
        --results /tmp/cis-results.xml
        --report /tmp/cis-report.html
        /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml || true"
    - scp admin@${TARGET_HOST}:/tmp/cis-report.html ./cis-report.html
    - scp admin@${TARGET_HOST}:/tmp/cis-results.xml ./cis-results.xml
  artifacts:
    paths:
      - cis-report.html
      - cis-results.xml

inspec-scan:
  stage: scan
  image: chef/inspec:latest
  script:
    - inspec exec ${INSPEC_PROFILE}
        -t ssh://admin@${TARGET_HOST}
        --reporter json:inspec-results.json cli
  artifacts:
    paths:
      - inspec-results.json
  allow_failure: true

validate-compliance:
  stage: validate
  image: node:lts
  script:
    - npm install -g @mitre/saf
    - saf validate threshold -i inspec-results.json
        --templateFile threshold.yml
    - saf convert hdf2ckl -i inspec-results.json -o checklist.ckl
  artifacts:
    paths:
      - checklist.ckl

deploy-if-compliant:
  stage: deploy
  script:
    - echo "Sistema conforme — procedi con il deploy"
    - ./deploy.sh
  when: on_success
  only:
    - main
```

**Pipeline GitHub Actions Equivalente:**

```yaml
# .github/workflows/compliance-scan.yml
name: Compliance Scan
on:
  push:
    branches: [main]
  schedule:
    - cron: '0 6 * * 1'  # Ogni lunedi alle 06:00 UTC

jobs:
  hardening-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install scanning tools
        run: |
          sudo apt-get install -y libopenscap8 ssg-ubuntu
          curl https://omnitruck.chef.io/install.sh | sudo bash -s -- -P inspec

      - name: Run OpenSCAP CIS scan
        run: |
          sudo oscap xccdf eval \
            --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
            --results cis-results.xml \
            --report cis-report.html \
            /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml || true

      - name: Run InSpec linux-baseline
        run: |
          sudo inspec exec https://github.com/dev-sec/linux-baseline \
            --reporter json:inspec-results.json cli || true

      - name: Validate compliance threshold
        run: |
          npm install -g @mitre/saf
          saf validate threshold -i inspec-results.json \
            --templateFile threshold.yml

      - name: Upload compliance artifacts
        uses: actions/upload-artifact@v4
        with:
          name: compliance-reports
          path: |
            cis-report.html
            cis-results.xml
            inspec-results.json
```

### 13.3 Goss — Validazione Leggera delle Configurazioni

Goss e' un validatore di configurazione leggero, ideale per verifiche rapide senza la complessita' di InSpec o OpenSCAP. Ansible-lockdown lo utilizza come componente di audit nei suoi ruoli.

```yaml
# goss.yaml — Validazione CIS rapida
file:
  /etc/ssh/sshd_config:
    exists: true
    mode: "0600"
    owner: root
    contains:
      - "PermitRootLogin no"
      - "MaxAuthTries 4"
      - "X11Forwarding no"
      - "PasswordAuthentication no"
      - "ClientAliveInterval 300"

  /etc/modprobe.d/disable-cramfs.conf:
    exists: true
    contains:
      - "install cramfs /bin/true"

  /etc/sysctl.d/99-cis.conf:
    exists: true
    contains:
      - "net.ipv4.ip_forward = 0"
      - "kernel.randomize_va_space = 2"
      - "net.ipv4.conf.all.accept_redirects = 0"

service:
  auditd:
    enabled: true
    running: true
  ufw:
    enabled: true
    running: true

port:
  tcp:22:
    listening: true
  tcp:23:
    listening: false  # Telnet non deve essere attivo

kernel-param:
  kernel.randomize_va_space:
    value: "2"
  net.ipv4.ip_forward:
    value: "0"
  kernel.yama.ptrace_scope:
    value: "1"

command:
  check-world-writable:
    exec: "find / -xdev -type f -perm -0002 2>/dev/null | wc -l"
    exit-status: 0
    stdout:
      - "0"

  check-shadow-perms:
    exec: "stat -c '%a' /etc/shadow"
    exit-status: 0
    stdout:
      - "0"

  check-selinux-or-apparmor:
    exec: "aa-status --enabled 2>/dev/null && echo 'enabled' || getenforce 2>/dev/null || echo 'none'"
    exit-status: 0
    stdout:
      - "/enabled|Enforcing/"
```

```bash
# Esecuzione di Goss
goss validate --format tap
goss validate --format json > goss-results.json
goss validate --format rspecish

# Validazione remota via SSH
goss -g goss.yaml render | ssh admin@target "goss validate --gossfile -"

# Server mode per health check continuo
goss serve --format json --listen-addr :8080
# Poi: curl http://target:8080/healthz
```

### 13.4 Continuous Authority to Operate (cATO)

Il Dipartimento della Difesa degli Stati Uniti sta migrando dal modello tradizionale ATO (Authority to Operate) — rinnovo ogni 3 anni con valutazione manuale — al modello cATO (Continuous ATO). Questo richiede:

1. **Monitoraggio continuo**: scansioni di compliance automatizzate almeno giornaliere, non piu' trimestrali
2. **Pipeline di validazione**: risultati STIG integrati nella pipeline CI/CD, con gate automatici che bloccano il deploy se la compliance scende sotto soglia
3. **Dashboard in tempo reale**: visibilita' continua sullo stato di conformita' per l'Authorizing Official (AO)
4. **Auto-remediation controllata**: correzione automatica dei drift per controlli a basso rischio, con approvazione per controlli critici

Il cATO trasforma la compliance da un evento puntuale ("prepariamo tutto per l'audit") a un processo continuo ("il sistema e' sempre conforme, e possiamo dimostrarlo in ogni momento").

**Implicazioni per le Configuration Baselines:**
- Le baseline non sono piu' documenti statici ma codice eseguibile (InSpec, Ansible, Goss)
- I risultati di compliance sono trattati come metriche di produzione (uptime, latenza, throughput → compliance score)
- Il drift non e' piu' scoperto durante l'audit ma in tempo reale, con alert automatici
- Le eccezioni (POA&M) hanno scadenze piu' brevi e controlli compensativi verificati automaticamente

---

## 14. Zero Trust e Configuration Baselines

### 14.1 Ruolo delle Configuration Baselines in un'Architettura Zero Trust

In un'architettura Zero Trust, la fiducia non e' mai implicita — ogni richiesta di accesso viene valutata in base a molteplici fattori, tra cui la postura di sicurezza del dispositivo richiedente. Le configuration baselines sono il meccanismo con cui si misura e si applica questa postura.

I principi fondamentali dello Zero Trust secondo NIST SP 800-207 e il CISA Zero Trust Maturity Model v2.0 si collegano direttamente alla gestione delle configurazioni:

| Principio Zero Trust | Collegamento alle Configuration Baselines |
|---|---|
| Verify explicitly | La conformita' del dispositivo alla baseline CIS/STIG e' un segnale di autenticazione (device health attestation) |
| Least privilege access | Le baseline riducono i servizi e le capability al minimo necessario (CIS Safeguard 4.8) |
| Assume breach | L'hardening limita il blast radius post-compromissione (firewall host, SELinux/AppArmor, segmentazione) |
| Never trust, always verify | La compliance non e' verificata una volta sola ma continuamente (Wazuh SCA, InSpec schedulato) |

### 14.2 Device Health Attestation e Conditional Access

In un deployment Zero Trust, l'accesso alle risorse aziendali e' condizionato alla conformita' del dispositivo. Il flusso tipico:

```
1. Utente richiede accesso a risorsa aziendale
2. Identity Provider verifica l'identita' (MFA, certificato)
3. Policy Engine interroga MDM/EDR per la postura del dispositivo:
   - Firewall attivo? (CIS 4.4/4.5) → SI/NO
   - Disco crittografato? (CIS Windows 18.x) → SI/NO
   - Antivirus aggiornato? → SI/NO
   - Compliance score CIS >= 85%? → SI/NO
   - Patch critiche applicate entro 48h? → SI/NO
4. Se tutti i controlli passano → accesso concesso
5. Se un controllo fallisce → accesso negato o limitato (quarantena)
```

**Implementazione con Azure Conditional Access e Intune:**

```powershell
# Policy di compliance Intune che verifica la baseline CIS
# Configurazione via Microsoft Graph API
$compliancePolicy = @{
    displayName = "CIS Baseline Compliance"
    description = "Verifica conformita' CIS Level 1 per Windows endpoints"
    platformType = "windows10"
    settings = @(
        @{
            settingName = "BitLockerEnabled"
            operator = "IsEquals"
            value = "true"
        },
        @{
            settingName = "SecureBootEnabled"
            operator = "IsEquals"
            value = "true"
        },
        @{
            settingName = "CodeIntegrityEnabled"
            operator = "IsEquals"
            value = "true"
        },
        @{
            settingName = "FirewallEnabled"
            operator = "IsEquals"
            value = "true"
        },
        @{
            settingName = "AntivirusEnabled"
            operator = "IsEquals"
            value = "true"
        }
    )
    scheduledActionsForRule = @(
        @{
            actionType = "block"
            gracePeriodHours = 24
            notificationTemplateId = "default"
        }
    )
}
```

### 14.3 Microsegmentazione e Configuration Baselines

La microsegmentazione e' l'applicazione dei principi Zero Trust alla rete interna. Ogni carico di lavoro (workload) comunica solo con i servizi esplicitamente autorizzati, eliminando il concetto di "rete fidata interna". Le configuration baselines supportano la microsegmentazione in tre modi:

1. **Firewall host-level** (CIS Safeguard 4.4): ogni server ha un firewall locale con regole specifiche per il suo ruolo. Un database accetta connessioni solo dall'application server, non dalla rete generica.

2. **Disabilitazione servizi non necessari** (CIS Safeguard 4.8): meno servizi in ascolto = meno vettori di attacco laterale.

3. **Network policies in Kubernetes**: il default e' "deny all"; solo il traffico esplicitamente autorizzato passa.

**Esempio di architettura microsegmentata con iptables/nftables:**

```bash
#!/usr/bin/env bash
# microseg-database.sh — Regole firewall per un server database PostgreSQL
# Solo l'application server 10.10.30.5 puo' connettersi alla porta 5432

set -euo pipefail

# Flush regole esistenti
nft flush ruleset

# Creare tabella e catene
nft add table inet filter
nft add chain inet filter input { type filter hook input priority 0 \; policy drop \; }
nft add chain inet filter forward { type filter hook forward priority 0 \; policy drop \; }
nft add chain inet filter output { type filter hook output priority 0 \; policy accept \; }

# Permettere loopback
nft add rule inet filter input iif lo accept

# Permettere connessioni stabilite
nft add rule inet filter input ct state established,related accept

# SSH solo dalla management VLAN
nft add rule inet filter input ip saddr 10.10.50.0/24 tcp dport 22 accept

# PostgreSQL solo dall'application server
nft add rule inet filter input ip saddr 10.10.30.5 tcp dport 5432 accept

# Monitoraggio (Prometheus node_exporter) solo dal monitoring server
nft add rule inet filter input ip saddr 10.10.40.10 tcp dport 9100 accept

# ICMP limitato (per diagnostica)
nft add rule inet filter input icmp type echo-request limit rate 5/second accept

# Logging dei pacchetti droppati (ultimi 10/minuto per evitare log flood)
nft add rule inet filter input limit rate 10/minute log prefix \"[DROPPED] \" drop

echo "[+] Microsegmentazione applicata per database server"
```

### 14.4 Hardening e ZTNA (Zero Trust Network Access)

La configurazione dei client per l'accesso ZTNA richiede baseline specifiche:

- **Certificato dispositivo**: ogni endpoint deve avere un certificato X.509 emesso dalla PKI aziendale, verificato ad ogni connessione
- **Agent di compliance**: un agent locale (CrowdStrike, SentinelOne, Intune) verifica continuamente la postura del dispositivo
- **DNS sicuro**: tutti i dispositivi devono usare DNS aziendali con filtraggio (CIS Safeguard 4.9)
- **VPN replacement**: il client ZTNA sostituisce la VPN tradizionale, fornendo accesso granulare per applicazione anziché accesso alla rete
- **Patching enforcement**: dispositivi non aggiornati entro la finestra definita perdono l'accesso alle risorse sensibili

---

## 15. Gestione Baselines per Dispositivi di Rete

### 15.1 CIS Benchmark per Firewall — Framework di Valutazione

I CIS Benchmark per firewall e dispositivi di rete seguono una struttura specifica che copre sei aree di controllo:

| Area | Controlli Principali | Impatto Sicurezza |
|---|---|---|
| Management Plane | SSH v2, HTTPS management, SNMP v3, NTP autenticato, banner legale | Impedisce intercettazione delle credenziali di amministrazione |
| Control Plane | Routing authentication (OSPF MD5/SHA, BGP MD5), rate limiting, CoPP | Previene attacchi di routing hijack e DoS al control plane |
| Data Plane | ACL, stateful inspection, IPS/IDS, URL filtering, SSL inspection | Filtra traffico malevolo, rileva intrusioni |
| Logging e Audit | Syslog remoto, flow logs, session logging, admin action logging | Tracciabilita' completa per incident response |
| High Availability | Failover configuration, session sync, configuration sync | Garantisce continuita' della protezione durante guasti |
| Updates | Firmware aggiornato, signature aggiornate, certificate management | Protegge da vulnerabilita' note |

### 15.2 Palo Alto Networks — CIS Benchmark v1.2.0 (Firewall 11)

```
# Controlli critici CIS per Palo Alto NGFW

# 1. Management Access
# Limitare l'accesso al management interface a IP specifici
set deviceconfig system permitted-ip 10.10.50.0/24

# Disabilitare HTTP management (solo HTTPS)
set deviceconfig system service disable-http yes

# Configurare timeout sessione admin
set deviceconfig setting management idle-timeout 15

# 2. Logging
# Inviare log a Panorama o SIEM esterno
set deviceconfig system log-settings syslog syslog-server1 server 10.10.5.5
set deviceconfig system log-settings syslog syslog-server1 transport UDP
set deviceconfig system log-settings syslog syslog-server1 port 514
set deviceconfig system log-settings syslog syslog-server1 facility LOG_AUTH

# 3. Security Profiles — applicare a TUTTE le regole di security policy
# Antivirus profile
set profiles virus default-action reset-both

# Anti-Spyware profile con DNS sinkhole
set profiles spyware strict dns-security sinkhole ipv4 72.5.65.111
set profiles spyware strict dns-security sinkhole ipv6 2600:5200::1

# Vulnerability Protection profile
set profiles vulnerability strict action reset-both

# URL Filtering profile
set profiles url-filtering default block-list gambling malware phishing

# File Blocking profile
set profiles file-blocking strict rules block-dangerous-files application any
set profiles file-blocking strict rules block-dangerous-files file-type bat exe dll

# 4. Decryption Policy
# Decriptare TLS per ispezione (escluse categorie sensibili come sanita'/finanza)
set rulebase decryption rules decrypt-all-except-sensitive
set rulebase decryption rules decrypt-all-except-sensitive action decrypt
set rulebase decryption rules decrypt-all-except-sensitive category-exclude health-and-medicine financial-services

# 5. Zone Protection Profile
set network profiles zone-protection-profile strict
set network profiles zone-protection-profile strict flood tcp-syn enable yes
set network profiles zone-protection-profile strict flood tcp-syn rate 10000
set network profiles zone-protection-profile strict flood icmp enable yes
set network profiles zone-protection-profile strict flood icmp rate 1000
set network profiles zone-protection-profile strict reconnaissance port-scan action block-ip
set network profiles zone-protection-profile strict reconnaissance host-sweep action block-ip
```

### 15.3 Fortinet FortiGate — Hardening Checklist

```
# Hardening FortiGate — Controlli CIS critici

# 1. Accesso amministrativo
config system admin
    edit "admin"
        set accprofile "super_admin"
        set force-password-change enable
        set password-expire 90
    next
end

# Limitare accesso management a interfaccia dedicata
config system interface
    edit "mgmt"
        set allowaccess https ssh
        set trust-ip 10.10.50.0 255.255.255.0
    next
end

# 2. Disabilitare accessi non sicuri
config system global
    set admin-telnet disable
    set admin-http-redirect disable
    set admin-https-redirect enable
    set admin-ssh-password enable
    set admin-ssh-v1 disable
    set admin-lockout-threshold 5
    set admin-lockout-duration 300
    set strong-crypto enable
    set ssl-min-proto-version TLSv1.2
end

# 3. Logging centralizzato
config log syslogd setting
    set status enable
    set server "10.10.5.5"
    set port 514
    set facility local7
    set source-ip 10.10.1.1
end

config log setting
    set log-invalid-packet enable
    set local-in-allow enable
    set local-in-deny-unicast enable
    set local-out enable
end

# 4. NTP autenticato
config system ntp
    set ntpsync enable
    set type custom
    config ntpserver
        edit 1
            set server "ntp1.corp.internal"
            set ntpv3 enable
            set authentication enable
            set key-id 1
        next
    end
end

# 5. Session timeout e hardening protocollo
config system global
    set admintimeout 15
    set tcp-halfclose-timer 120
    set tcp-halfopen-timer 10
    set tcp-timewait-timer 1
    set udp-idle-timer 60
end
```

### 15.4 Automazione Hardening Rete con Ansible

```yaml
---
# network-hardening.yml — Hardening Cisco IOS-XE via Ansible
- name: Apply CIS Baseline to Cisco IOS-XE Devices
  hosts: cisco_switches
  gather_facts: no
  connection: network_cli

  vars:
    management_acl_name: "MGMT-ACCESS"
    management_vlan: "10.10.50.0 0.0.0.255"
    ntp_server: "10.10.1.1"
    syslog_server: "10.10.5.5"
    banner_text: |
      ******************************************************************
      AUTHORIZED ACCESS ONLY. All activity is monitored and recorded.
      Unauthorized access is prohibited and subject to legal action.
      ******************************************************************

  tasks:
    - name: Configure login banner
      cisco.ios.ios_banner:
        banner: login
        text: "{{ banner_text }}"
        state: present

    - name: Disable unnecessary services
      cisco.ios.ios_config:
        lines:
          - no ip http server
          - no ip http secure-server
          - no service pad
          - no ip bootp server
          - no ip source-route
          - no cdp run
          - no lldp run
          - service password-encryption
          - service timestamps log datetime msec localtime show-timezone

    - name: Configure SSH version 2 only
      cisco.ios.ios_config:
        lines:
          - ip ssh version 2
          - ip ssh time-out 60
          - ip ssh authentication-retries 3

    - name: Configure management ACL
      cisco.ios.ios_config:
        lines:
          - "permit {{ management_vlan }}"
          - deny any log
        parents: "ip access-list standard {{ management_acl_name }}"

    - name: Apply ACL to VTY lines
      cisco.ios.ios_config:
        lines:
          - transport input ssh
          - "access-class {{ management_acl_name }} in"
          - exec-timeout 15 0
          - login local
        parents: "line vty 0 15"

    - name: Configure NTP
      cisco.ios.ios_config:
        lines:
          - "ntp server {{ ntp_server }}"
          - ntp authentication-key 1 md5 NtP-S3cur3-K3y
          - ntp trusted-key 1

    - name: Configure logging
      cisco.ios.ios_config:
        lines:
          - "logging host {{ syslog_server }}"
          - logging buffered 16384 informational
          - logging trap informational
          - logging source-interface Loopback0

    - name: Disable unused interfaces
      cisco.ios.ios_config:
        lines:
          - shutdown
          - description UNUSED-PORT-DISABLED
        parents: "interface {{ item }}"
      loop: "{{ unused_interfaces | default([]) }}"

    - name: Save configuration
      cisco.ios.ios_config:
        save_when: always
```

### 15.5 Confronto Baselines tra Vendor di Rete

| Controllo | Cisco IOS-XE | Palo Alto | Fortinet | Juniper SRX |
|---|---|---|---|---|
| SSH v2 only | `ip ssh version 2` | Default | `set admin-ssh-v1 disable` | `set system services ssh protocol-version v2` |
| Disable Telnet | `transport input ssh` | N/A (no telnet) | `set admin-telnet disable` | `delete system services telnet` |
| Admin timeout | `exec-timeout 15 0` | `idle-timeout 15` | `admintimeout 15` | `set system login idle-timeout 15` |
| Syslog remoto | `logging host X.X.X.X` | `log-settings syslog` | `log syslogd setting` | `set system syslog host X.X.X.X` |
| NTP auth | `ntp authentication-key` | `ntp-server-address auth` | `ntp ntpserver auth` | `set system ntp authentication-key` |
| Password encryption | `service password-encryption` | Default (hashed) | `strong-crypto enable` | `set system login password format sha256` |
| Login banner | `banner login` | `login-banner` | `admin-banner enable` | `set system login message` |
| SNMP v3 only | `snmp-server view/group/user` | `snmp-trap-server v3` | `snmpv3` | `set snmp v3` |

---

## 16. Casi di Studio e Scenari Operativi

### 16.1 Caso di Studio: Migrazione da Baseline Manuale a Hardening Automatizzato

**Contesto:** Azienda manifatturiera italiana con 200 server Linux (mix RHEL 8, Ubuntu 20.04/22.04), 50 server Windows (2019/2022), e 30 dispositivi di rete Cisco. Hardening gestito manualmente con checklist Excel aggiornata semestralmente. Tempo medio di hardening per server: 4 ore. Compliance score medio: 62%.

**Problemi Identificati:**
- Drift costante: il 35% dei server mostrava deviazioni significative dalla baseline entro 30 giorni dall'hardening
- Assenza di visibilita': nessun dashboard centralizzato per lo stato di compliance
- Costi elevati: 200 server x 4 ore x 2 volte/anno = 1.600 ore/anno di lavoro manuale
- Inconsistenza: due tecnici applicavano la stessa checklist con risultati diversi

**Soluzione Implementata:**

Fase 1 (Mese 1-2): Infrastruttura di automazione
- Installazione Ansible Automation Platform (AAP) con controller centralizzato
- Installazione Wazuh manager + agent su tutti i server
- Configurazione repository Git per playbook e profili InSpec

Fase 2 (Mese 3-4): Sviluppo playbook e profili
- Adozione ruoli ansible-lockdown per RHEL 9 CIS e Ubuntu 22.04 CIS
- Personalizzazione delle variabili per l'ambiente specifico (esclusione regole incompatibili con applicazioni legacy)
- Sviluppo profili InSpec custom per controlli aziendali aggiuntivi
- Test in ambiente staging su 10 server rappresentativi

Fase 3 (Mese 5-6): Rollout e monitoraggio
- Applicazione progressiva: 20 server/settimana, partendo dai meno critici
- Scansione post-hardening con OpenSCAP e InSpec
- Configurazione Wazuh SCA per monitoraggio continuo
- Creazione dashboard Grafana per visualizzazione compliance

**Risultati Dopo 6 Mesi:**

| Metrica | Prima | Dopo | Miglioramento |
|---|---|---|---|
| Compliance score medio | 62% | 94% | +32 punti |
| Tempo hardening per server | 4 ore | 15 minuti (automatizzato) | -93.75% |
| Ore/anno per hardening | 1.600 | 120 | -92.5% |
| Drift a 30 giorni | 35% server deviati | 3% server deviati | -91.4% |
| Tempo rilevamento drift | 180 giorni (prossimo audit) | < 12 ore (Wazuh SCA) | -99.7% |
| Visibilita' compliance | Nessuna (Excel manuale) | Dashboard real-time | Qualitativo |

### 16.2 Caso di Studio: Incident Response e Baseline Verification

**Scenario:** Durante un'esercitazione di red team, il team offensivo ottiene accesso iniziale tramite phishing e stabilisce persistenza su un server Linux. L'analisi post-incidente rivela che il server era stato "hardened" sei mesi prima ma aveva subito drift significativo.

**Drift Rilevato durante l'analisi forense:**

```bash
# Controllo che il red team ha sfruttato:
# 1. SSH PermitRootLogin era tornato a "yes" dopo un aggiornamento di openssh-server
grep PermitRootLogin /etc/ssh/sshd_config
# Output attuale: PermitRootLogin yes
# Baseline CIS: PermitRootLogin no

# 2. Un tecnico aveva disabilitato SELinux per far funzionare un'applicazione
getenforce
# Output attuale: Disabled
# Baseline CIS: Enforcing

# 3. /tmp era stato rimontato senza noexec dopo un riavvio
mount | grep /tmp
# Output: /dev/sda3 on /tmp type ext4 (rw,relatime)
# Baseline CIS: tmpfs on /tmp type tmpfs (rw,noexec,nosuid,nodev)

# 4. Auditd era stato fermato perche' "consumava troppo disco"
systemctl status auditd
# Output: inactive (dead)
# Baseline CIS: active (running)
```

**Lezione Appresa:** L'hardening senza monitoraggio continuo e' un'illusione di sicurezza. Il server aveva un compliance score del 95% al momento dell'hardening e del 58% al momento dell'incidente — sei mesi dopo — senza che nessuno se ne fosse accorto.

**Contromisure Implementate:**
1. Wazuh SCA con policy CIS attiva su tutti i server (scansione ogni 6 ore)
2. Alert automatico per drift su controlli CAT I/critici (PermitRootLogin, SELinux, auditd)
3. Auto-remediation per controlli a basso rischio (permessi file, banner, moduli kernel)
4. Revisione mensile del drift report da parte del security team
5. Aggiunta di test InSpec nella pipeline CI/CD per gli aggiornamenti di pacchetti

### 16.3 Scenario Operativo: Hardening di un Cluster PostgreSQL Critico

**Requisiti:** Cluster PostgreSQL 16 in alta disponibilita' (primary + 2 replica streaming) per un'applicazione finanziaria. Conformita' richiesta: PCI-DSS v4.0 Requisiti 2.2, 3.5, 6.3, 8, 10.

**Checklist di Hardening Completa:**

```ini
# postgresql.conf — Hardening CIS + PCI-DSS

# 1. Network — solo interfacce necessarie
listen_addresses = '10.10.20.5'
port = 5432

# 2. Autenticazione
password_encryption = scram-sha-256
authentication_timeout = 60

# 3. TLS obbligatorio
ssl = on
ssl_min_protocol_version = 'TLSv1.3'
ssl_cert_file = '/etc/ssl/certs/pg-server.crt'
ssl_key_file = '/etc/ssl/private/pg-server.key'
ssl_ca_file = '/etc/ssl/certs/ca-chain.crt'
ssl_crl_file = '/etc/ssl/certs/ca.crl'
ssl_ciphers = 'HIGH:!aNULL:!MD5:!3DES:!DES:!RC4:!IDEA:!SEED:!aDSS:!SRP:!PSK'

# 4. Logging completo (PCI-DSS Req. 10)
log_destination = 'syslog'
syslog_facility = 'LOCAL0'
syslog_ident = 'postgres'
log_connections = on
log_disconnections = on
log_statement = 'ddl'
log_duration = on
log_line_prefix = '%m [%p] user=%u db=%d app=%a host=%h '
log_checkpoints = on
log_lock_waits = on
log_temp_files = 0
log_min_error_statement = 'error'
log_min_duration_statement = 1000

# 5. Limiti risorse
max_connections = 200
superuser_reserved_connections = 3
statement_timeout = 300000
idle_in_transaction_session_timeout = 600000

# 6. Row-Level Security per dati sensibili
# Abilitato per tabella (ALTER TABLE ... ENABLE ROW LEVEL SECURITY)
row_security = on
```

```
# pg_hba.conf — Solo connessioni TLS con SCRAM-SHA-256
# TYPE   DATABASE   USER        ADDRESS            METHOD
local    all        postgres                       peer
hostssl  app_db     app_user    10.10.30.5/32      scram-sha-256
hostssl  app_db     app_user    10.10.30.6/32      scram-sha-256
hostssl  replication repl_user  10.10.20.6/32      scram-sha-256 clientcert=verify-full
hostssl  replication repl_user  10.10.20.7/32      scram-sha-256 clientcert=verify-full
host     all        all         0.0.0.0/0          reject
```

**Profilo InSpec per validazione PostgreSQL:**

```ruby
# profiles/postgres-hardening/controls/postgres.rb

control 'pg-001' do
  impact 1.0
  title 'PostgreSQL deve ascoltare solo su interfacce specifiche'
  desc 'Impedisce connessioni da reti non autorizzate'

  describe postgres_conf('/etc/postgresql/16/main/postgresql.conf') do
    its('listen_addresses') { should_not eq '*' }
    its('listen_addresses') { should_not eq '0.0.0.0' }
  end
end

control 'pg-002' do
  impact 1.0
  title 'TLS deve essere abilitato con versione minima 1.3'

  describe postgres_conf('/etc/postgresql/16/main/postgresql.conf') do
    its('ssl') { should eq 'on' }
    its('ssl_min_protocol_version') { should eq 'TLSv1.3' }
  end
end

control 'pg-003' do
  impact 1.0
  title 'Password hashing deve usare scram-sha-256'

  describe postgres_conf('/etc/postgresql/16/main/postgresql.conf') do
    its('password_encryption') { should eq 'scram-sha-256' }
  end
end

control 'pg-004' do
  impact 1.0
  title 'Logging delle connessioni deve essere attivo'

  describe postgres_conf('/etc/postgresql/16/main/postgresql.conf') do
    its('log_connections') { should eq 'on' }
    its('log_disconnections') { should eq 'on' }
    its('log_statement') { should be_in ['ddl', 'mod', 'all'] }
  end
end

control 'pg-005' do
  impact 0.7
  title 'Nessun utente deve avere password vuota'

  describe sql.query("SELECT usename FROM pg_shadow WHERE passwd IS NULL OR passwd = '';") do
    its('output') { should eq '' }
  end
end

control 'pg-006' do
  impact 1.0
  title 'pg_hba.conf non deve contenere regole trust o md5'

  describe file('/etc/postgresql/16/main/pg_hba.conf') do
    its('content') { should_not match(/^\s*host.*trust/) }
    its('content') { should_not match(/^\s*host.*md5/) }
  end
end
```

### 16.4 Scenario Operativo: Risposta a Nuovo CIS Benchmark Release

Quando CIS rilascia una nuova versione del benchmark (tipicamente ogni 6-12 mesi per le tecnologie principali), l'organizzazione deve seguire un processo strutturato per aggiornare le proprie baseline:

**Processo di Aggiornamento Baseline:**

```
1. NOTIFICA (Giorno 0)
   - Monitorare RSS feed CIS (https://www.cisecurity.org/cis-benchmarks)
   - Scaricare il nuovo benchmark PDF e il datastream XCCDF/OVAL
   - Identificare le differenze con la versione precedente (delta analysis)

2. ANALISI IMPATTO (Giorno 1-5)
   - Catalogare nuovi controlli aggiunti
   - Identificare controlli rimossi o modificati
   - Valutare l'impatto dei nuovi controlli sulle applicazioni in produzione
   - Classificare i cambiamenti per rischio: breaking / non-breaking

3. AGGIORNAMENTO AUTOMAZIONE (Giorno 6-15)
   - Aggiornare i ruoli Ansible (ansible-lockdown pubblica aggiornamenti
     entro 30-60 giorni dal rilascio CIS)
   - Aggiornare i profili InSpec
   - Aggiornare le policy Wazuh SCA
   - Aggiornare il contenuto OpenSCAP (scap-security-guide)

4. TEST IN STAGING (Giorno 16-25)
   - Applicare le nuove baseline in ambiente staging
   - Eseguire test di regressione applicativa
   - Verificare che le nuove regole non causino downtime o degradazione
   - Documentare eccezioni necessarie

5. ROLLOUT PRODUZIONE (Giorno 26-40)
   - Applicazione progressiva (canary → 10% → 50% → 100%)
   - Scansione post-applicazione
   - Aggiornamento documentazione e POA&M
   - Comunicazione ai team applicativi

6. VERIFICA (Giorno 41-45)
   - Scansione completa con OpenSCAP/CIS-CAT versione aggiornata
   - Verifica compliance score >= threshold
   - Aggiornamento dashboard e report
   - Chiusura del ciclo di change management
```

### 16.5 Tabella Comparativa: CIS Benchmarks vs DISA STIGs vs Microsoft Security Baselines

| Caratteristica | CIS Benchmarks | DISA STIGs | Microsoft Security Baselines |
|---|---|---|---|
| Ente emittente | Center for Internet Security (nonprofit) | Defense Information Systems Agency (U.S. DoD) | Microsoft Corporation |
| Obbligatorieta' | Volontario (best practice) | Obbligatorio per DoD; volontario altrove | Volontario (raccomandazione vendor) |
| Copertura tecnologica | 100+ tecnologie (OS, DB, cloud, container, rete) | Tecnologie approvate per uso DoD | Solo prodotti Microsoft |
| Livelli | Level 1 (standard), Level 2 (high security) | CAT I (high), CAT II (medium), CAT III (low) | N/A (baseline unica per versione OS) |
| Formati machine-readable | XCCDF, OVAL (CIS SecureSuite) | XCCDF, OVAL | GPO backup, Policy Analyzer, OSConfig |
| Frequenza aggiornamento | Con ogni major release + revisioni periodiche | Trimestrale (quarterly STIG updates) | Con ogni major release OS |
| Strumenti di scanning | CIS-CAT Pro, OpenSCAP, Nessus, Qualys | SCC, OpenSCAP, Nessus, ACAS | Microsoft Defender, Intune, OSConfig |
| Costo | PDF gratuito; formati SCAP richiedono CIS SecureSuite (a pagamento) | Gratuito (pubblico) | Gratuito (incluso nel SCT) |
| Comunita' | Contributo volontario di esperti globali | Sviluppo interno DISA con input vendor | Sviluppo interno Microsoft |
| Approccio alla compliance | Prescriptivo con giustificazione per ogni controllo | Molto prescriptivo con classificazione severita' | Prescriptivo con focus su prodotti Microsoft |
| Tailoring | Profili personalizzabili via XCCDF tailoring | Eccezioni via POA&M con approvazione AO | Personalizzabile via GPO/Intune |
| Integrazione cloud | CIS Benchmarks per AWS, Azure, GCP, Oracle Cloud | Limitata (STIGs per EC2, Azure VM) | Nativa per Azure e Microsoft 365 |

### 16.6 Metriche e KPI per il Programma di Configuration Baseline

Un programma maturo di gestione delle configuration baselines richiede metriche quantitative per misurare l'efficacia e giustificare gli investimenti:

**KPI Operativi:**

| KPI | Formula | Target IG1 | Target IG2 | Target IG3 |
|---|---|---|---|---|
| Compliance Score | (Controlli conformi / Controlli totali) x 100 | >= 80% | >= 90% | >= 95% |
| Drift Rate | (Sistemi con drift / Sistemi totali) x 100 al mese | <= 15% | <= 8% | <= 3% |
| Mean Time to Detect Drift (MTTD) | Tempo medio tra insorgenza drift e rilevamento | <= 7 giorni | <= 24 ore | <= 6 ore |
| Mean Time to Remediate (MTTR) | Tempo medio tra rilevamento e correzione | <= 30 giorni | <= 14 giorni | <= 72 ore |
| Baseline Coverage | (Sistemi con baseline applicata / Sistemi totali) x 100 | >= 85% | >= 95% | >= 99% |
| Exception Rate | (Eccezioni attive / Controlli totali) x 100 | <= 10% | <= 5% | <= 2% |
| Automation Rate | (Controlli automatizzati / Controlli totali) x 100 | >= 60% | >= 80% | >= 95% |

**KPI Strategici:**

- **Costo per sistema hardened**: misura l'efficienza dell'automazione (target: < EUR 50/server/anno con automazione completa vs. EUR 500+/server/anno manualmente)
- **Tempo di onboarding nuovo sistema**: dal provisioning al raggiungimento della compliance (target: < 30 minuti con golden image + automazione)
- **Riduzione superficie di attacco**: numero di servizi in ascolto, porte aperte, account attivi prima e dopo hardening
- **Correlazione con incidenti**: percentuale di incidenti di sicurezza su sistemi non conformi vs. conformi (tipicamente 5-10x maggiore su sistemi non conformi)

### 16.7 Errori Comuni e Anti-Pattern nella Gestione delle Baselines

| Anti-Pattern | Descrizione | Conseguenza | Soluzione |
|---|---|---|---|
| "Harden and Forget" | Applicare l'hardening una volta e non monitorare | Drift silenzioso, falsa sicurezza | Monitoraggio continuo (Wazuh SCA, InSpec schedulato) |
| "One Baseline Fits All" | Stessa baseline per tutti i sistemi senza considerare il ruolo | Conflitti con applicazioni, eccezioni non gestite | Baseline per ruolo (web server, DB, app server, jump host) |
| "Compliance Score Worship" | Ottimizzare per il punteggio ignorando il contesto di rischio | Controlli CAT III al 100% ma CAT I al 70% | Prioritizzare per severita', non per numero |
| "Manual Exception Tracking" | Eccezioni in documenti Word/Excel senza scadenza | Eccezioni permanenti, rischio accumulato | POA&M con scadenze, revisione trimestrale, alert automatici |
| "Big Bang Rollout" | Applicare l'hardening a tutti i sistemi simultaneamente | Outage massivo se un controllo causa problemi | Rollout progressivo: canary → 10% → 50% → 100% |
| "Audit-Driven Hardening" | Hardening solo prima degli audit, ignorato il resto dell'anno | Sicurezza illusoria, costi concentrati | Processo continuo integrato nelle operazioni quotidiane |
| "Copy-Paste from PDF" | Applicare le raccomandazioni CIS/STIG manualmente dal PDF | Errori umani, inconsistenza, non ripetibile | Automazione (Ansible, DSC, OpenSCAP remediation) |
| "Skip Testing" | Applicare l'hardening in produzione senza test in staging | Downtime applicativo, rollback d'emergenza | Test completo in staging con regressione applicativa |

---

## Riferimenti e Risorse

- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks
- CIS Controls v8.1: https://www.cisecurity.org/controls
- DISA STIGs: https://public.cyber.mil/stigs/
- ComplianceAsCode (scap-security-guide): https://github.com/ComplianceAsCode/content
- ansible-lockdown: https://github.com/ansible-lockdown
- dev-sec Hardening Framework: https://dev-sec.io/
- OpenSCAP: https://www.open-scap.org/
- Wazuh SCA: https://documentation.wazuh.com/current/user-manual/capabilities/sec-config-assessment/
- Microsoft Security Compliance Toolkit: https://www.microsoft.com/en-us/download/details.aspx?id=55319
- Lynis: https://cisofy.com/lynis/
- NIST SP 800-128 (Guide for Security-Focused Configuration Management): https://csrc.nist.gov/pubs/sp/800/128/final
- NIST SP 800-70 (National Checklist Program): https://csrc.nist.gov/pubs/sp/800/70/r4/final
- NIST SP 800-207 (Zero Trust Architecture): https://csrc.nist.gov/pubs/sp/800/207/final
- CISA Zero Trust Maturity Model: https://www.cisa.gov/zero-trust-maturity-model
- MITRE SAF (Security Automation Framework): https://saf.mitre.org/
- kube-bench (Aqua Security): https://github.com/aquasecurity/kube-bench
- Kubescape: https://github.com/kubescape/kubescape
- CIS Controls v8.1 Navigator: https://www.cisecurity.org/controls/cis-controls-navigator
- CIS Controls Assessment Specification: https://controls-assessment-specification.readthedocs.io/
- Prowler (AWS/Azure/GCP Security Scanner): https://github.com/prowler-cloud/prowler
- Conftest (OPA Policy Testing): https://www.conftest.dev/
- Checkov (IaC Security Scanner): https://www.checkov.io/
- Goss (Server Validation): https://github.com/goss-org/goss
- CIS Benchmark Windows Server 2025: https://www.cisecurity.org/benchmark/microsoft_windows_server
- CIS Benchmark Palo Alto Networks: https://www.cisecurity.org/benchmark/palo_alto_networks
- OSConfig (Microsoft): https://learn.microsoft.com/en-us/windows-server/security/osconfig/osconfig-overview
- Lockdown Enterprise (Ansible Lockdown): https://www.lockdownenterprise.com/
