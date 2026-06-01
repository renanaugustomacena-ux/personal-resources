# Privileged Access Management (PAM) — Architettura, Implementazione e Attacco/Difesa

> **Modulo 32** · **Tempo:** 180 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Privileged accounts are the crown jewels.** Every major breach in the past decade traces back to compromised privileged credentials. Protect them or lose everything.
2. **Vault first, then session management, then JIT.** A phased approach that delivers incremental security gains without breaking production services.
3. **PAM is not a product — it is a discipline.** Technology alone fails without process: credential rotation policies, approval workflows, break-glass procedures, and continuous monitoring.
4. **Red team your PAM.** If you deploy a vault but never test whether an attacker can bypass it, you have compliance theater, not security.


## Indice

1. [Fondamenti PAM](#fondamenti-pam)
   - [Tassonomia degli Account Privilegiati](#tassonomia-degli-account-privilegiati)
   - [Perche' gli Account Privilegiati Sono il Target Primario](#perche-gli-account-privilegiati-sono-il-target-primario)
   - [Credential Theft Attack Chain](#credential-theft-attack-chain)
   - [MITRE ATT&CK Techniques Targeting Privileged Access](#mitre-attck-techniques-targeting-privileged-access)
2. [Architettura PAM](#architettura-pam)
   - [Session Management](#session-management)
   - [Credential Vaulting](#credential-vaulting)
   - [Just-in-Time (JIT) Access](#just-in-time-jit-access)
   - [Just-Enough-Access (JEA)](#just-enough-access-jea)
   - [Privilege Elevation and Delegation Management (PEDM)](#privilege-elevation-and-delegation-management-pedm)
3. [Piattaforme Enterprise](#piattaforme-enterprise)
   - [CyberArk Privileged Access Security](#cyberark-privileged-access-security)
   - [BeyondTrust](#beyondtrust)
   - [Delinea](#delinea)
   - [HashiCorp Vault](#hashicorp-vault)
   - [Open-Source Alternatives](#open-source-alternatives)
4. [Implementazione PAM](#implementazione-pam)
   - [Discovery Phase](#discovery-phase)
   - [Risk Assessment and Prioritization](#risk-assessment-and-prioritization)
   - [Phased Rollout Strategy](#phased-rollout-strategy)
   - [Vault Migration](#vault-migration)
   - [Session Management Deployment](#session-management-deployment)
   - [Workflow Approval Chains](#workflow-approval-chains)
   - [Break-Glass Procedures](#break-glass-procedures)
5. [PAM per Ambienti Specifici](#pam-per-ambienti-specifici)
   - [Windows / Active Directory](#windows--active-directory)
   - [Linux / Unix](#linux--unix)
   - [Cloud (AWS, Azure, GCP)](#cloud-aws-azure-gcp)
   - [Database](#database)
   - [Network Devices](#network-devices)
   - [Kubernetes](#kubernetes)
6. [Attacchi al PAM — Red Team Perspective](#attacchi-al-pam--red-team-perspective)
   - [PAM Vault Exploitation](#pam-vault-exploitation)
   - [Credential Harvesting Before Vaulting](#credential-harvesting-before-vaulting)
   - [Session Hijacking and Recording Bypass](#session-hijacking-and-recording-bypass)
   - [MFA Fatigue Attacks on PAM](#mfa-fatigue-attacks-on-pam)
   - [Kerberoasting Service Accounts Before Rotation](#kerberoasting-service-accounts-before-rotation)
   - [Pass-the-Hash on Cached Credentials](#pass-the-hash-on-cached-credentials)
   - [Targeting PAM Administrators](#targeting-pam-administrators)
   - [Supply Chain Attacks on PAM Software](#supply-chain-attacks-on-pam-software)
7. [Monitoraggio e Detection](#monitoraggio-e-detection)
   - [Anomalous Privileged Session Detection](#anomalous-privileged-session-detection)
   - [Lateral Movement with Privileged Credentials](#lateral-movement-with-privileged-credentials)
   - [Unusual Privilege Elevation Patterns](#unusual-privilege-elevation-patterns)
   - [PAM Bypass Attempt Detection](#pam-bypass-attempt-detection)
   - [SIEM Integration](#siem-integration)
   - [Behavioral Analytics for Privileged Users](#behavioral-analytics-for-privileged-users)
8. [PAM e Zero Trust Integration](#pam-e-zero-trust-integration)
   - [PAM as Zero Trust Enabler](#pam-as-zero-trust-enabler)
   - [Continuous Verification During Privileged Sessions](#continuous-verification-during-privileged-sessions)
   - [Device Trust for Privileged Access](#device-trust-for-privileged-access)
   - [Network Segmentation for PAM Infrastructure](#network-segmentation-for-pam-infrastructure)
   - [API Security for PAM](#api-security-for-pam)
   - [Secrets Management in CI/CD Pipelines](#secrets-management-in-cicd-pipelines)
9. [Compliance e Governance](#compliance-e-governance)
   - [PCI-DSS Requirement 8](#pci-dss-requirement-8)
   - [SOX IT Controls](#sox-it-controls)
   - [HIPAA Minimum Necessary Access](#hipaa-minimum-necessary-access)
   - [ISO 27001 A.9 Access Control](#iso-27001-a9-access-control)
   - [NIST CSF PR.AC](#nist-csf-prac)
   - [Audit Reporting and Attestation](#audit-reporting-and-attestation)
   - [Access Certification Campaigns](#access-certification-campaigns)
10. [Laboratorio](#laboratorio)
    - [Lab 1: Deploy HashiCorp Vault + Teleport](#lab-1-deploy-hashicorp-vault--teleport)
    - [Lab 2: Vault SSH Credentials](#lab-2-vault-ssh-credentials)
    - [Lab 3: Dynamic Database Credentials](#lab-3-dynamic-database-credentials)
    - [Lab 4: JIT Access Implementation](#lab-4-jit-access-implementation)
    - [Lab 5: Credential Theft Attack Testing](#lab-5-credential-theft-attack-testing)
    - [Lab 6: Detection and Logging Verification](#lab-6-detection-and-logging-verification)
    - [Lab 7: Access Review Audit](#lab-7-access-review-audit)

---

## Fondamenti PAM

### Tassonomia degli Account Privilegiati

Privileged accounts are not a monolith. Each category carries distinct risk profiles, rotation requirements, and monitoring strategies. A mature PAM program treats each type differently.

**Domain Administrator Accounts**

Domain Admins in Active Directory hold unrestricted control over every object in the forest. A compromised DA account means total domain compromise — the attacker can create accounts, modify Group Policy, reset any password, extract the NTDS.dit, and deploy ransomware to every domain-joined machine within minutes. These accounts must never be used for daily operations. The expected count in a healthy environment: fewer than five, ideally two (primary + break-glass).

Key controls: tiered administration model, separate admin workstations (PAWs), no interactive logon except on Tier 0 systems, credential stored in a PAM vault with dual-approval checkout.

**Local Administrator Accounts**

Every Windows machine ships with a local administrator (RID 500). When the same password is reused across endpoints — which is the default unless LAPS or a PAM solution intervenes — an attacker who compromises one machine can move laterally to every machine sharing that credential. This is the single most common lateral movement vector in enterprise environments.

Key controls: Microsoft LAPS (Local Administrator Password Solution) for automatic rotation, or PAM-managed rotation via CyberArk CPM or similar. Disable the built-in Administrator account where possible and use named local admin accounts for accountability.

**Service Accounts**

Service accounts run background processes: SQL Server services, IIS application pools, scheduled tasks, backup agents, monitoring agents. They often hold elevated privileges and their passwords rarely change — some environments have service accounts with passwords unchanged for years. They are prime targets for Kerberoasting (when registered with an SPN in AD) and credential harvesting from memory.

Key controls: Group Managed Service Accounts (gMSA) where supported, PAM-managed rotation with service restart orchestration, elimination of interactive logon rights, and removal of unnecessary SPNs.

**Application Accounts**

Application-to-application credentials — database connection strings, API keys, cloud access keys — are frequently hardcoded in configuration files, environment variables, or source code. These are the credentials that appear in breach dumps, Git repositories, and Docker images. They lack human owners, making accountability difficult.

Key controls: centralized secrets management (HashiCorp Vault, AWS Secrets Manager), dynamic credential generation with automatic expiration, and CI/CD pipeline integration that never writes secrets to disk or logs.

**Emergency / Break-Glass Accounts**

Break-glass accounts provide access when the PAM system itself is unavailable — vault outage, network partition, or disaster recovery scenario. They must exist, but they are extremely dangerous because they bypass every control the PAM program enforces.

Key controls: sealed envelopes in a physical safe (yes, still), dual-custody retrieval, immediate alerting on any use, mandatory password change after every use, and periodic testing (at least quarterly) to verify the break-glass procedure actually works.

### Perche' gli Account Privilegiati Sono il Target Primario

The economics are simple. An attacker with a regular user account must spend weeks or months escalating privileges, chaining exploits, and moving laterally. An attacker with a domain admin credential achieves the same result in minutes. Every sophisticated threat actor — APT groups, ransomware operators, insider threats — prioritizes credential theft over exploit development because it is faster, stealthier, and more reliable.

Empirical data supports this. According to the Verizon DBIR (2024 and 2025 editions), over 60% of breaches involving system intrusion used stolen credentials as the initial access or privilege escalation vector. CrowdStrike's annual threat report consistently identifies credential access as the most prevalent MITRE ATT&CK tactic observed in real intrusions.

The attacker's calculus: why burn a zero-day (which has a short shelf life and costs hundreds of thousands on the market) when you can phish an admin, dump LSASS, or Kerberoast a service account?

### Credential Theft Attack Chain

A typical credential theft attack chain in an enterprise environment proceeds through predictable stages:

1. **Initial Access** — Phishing email delivers a payload or steals credentials via a convincing login portal. Alternatively: exploitation of a public-facing application, supply chain compromise, or insider threat.

2. **Local Privilege Escalation** — The attacker lands as a standard user and escalates to local admin using unpatched kernel vulnerabilities (e.g., PrintNightmare, HiveNightmare), misconfigured services, or DLL hijacking.

3. **Credential Harvesting** — With local admin, the attacker dumps credentials from memory using tools like Mimikatz, extracts cached credentials from the registry (SAM database), or reads credentials stored in browser password managers, RDP credential caches, or configuration files.

4. **Lateral Movement** — Using harvested credentials, the attacker authenticates to additional systems via SMB, WMI, PowerShell Remoting, RDP, or SSH. Each new system yields more credentials.

5. **Domain Escalation** — The attacker finds a path to Domain Admin: Kerberoasting a service account with a weak password, exploiting unconstrained delegation, abusing AD Certificate Services (ESC1-ESC8 attack paths), or finding a DA credential in memory on a compromised server.

6. **Objective Execution** — With DA-level access, the attacker achieves their objective: data exfiltration, ransomware deployment, persistent backdoor installation, or destructive attack.

PAM interrupts this chain at stages 3-5 by removing credentials from memory, rotating them before they can be cracked, and requiring MFA + approval for privileged session initiation.

### MITRE ATT&CK Techniques Targeting Privileged Access

**T1078 — Valid Accounts**

Adversaries obtain and abuse credentials of existing accounts to gain initial access, persistence, privilege escalation, or defense evasion. Sub-techniques include T1078.001 (Default Accounts — factory credentials on network appliances), T1078.002 (Domain Accounts — harvested or purchased AD credentials), T1078.003 (Local Accounts), and T1078.004 (Cloud Accounts — compromised AWS IAM keys or Azure AD tokens).

PAM countermeasure: eliminate default credentials during onboarding, vault all domain/local/cloud privileged credentials, enforce MFA on every checkout, and monitor for use outside the PAM session.

**T1003 — OS Credential Dumping**

The attacker extracts credentials from OS memory or storage. Sub-techniques include T1003.001 (LSASS Memory — Mimikatz, comsvcs.dll, ProcDump), T1003.002 (SAM — registry extraction), T1003.003 (NTDS — domain controller database extraction via ntdsutil or Volume Shadow Copy), T1003.004 (LSA Secrets), T1003.005 (Cached Domain Credentials — DCC2 hashes), and T1003.006 (DCSync — replicating credentials from AD using replication protocol).

PAM countermeasure: Credential Guard (Windows 10+), Protected Users security group, disabling WDigest, LSASS protection (RunAsPPL), limiting DCSync rights to actual DCs, and PAM-enforced credential rotation that invalidates dumped hashes before they can be used.

**T1098 — Account Manipulation**

The attacker modifies account attributes to maintain persistence: adding credentials to service principals, modifying user permissions, adding users to privileged groups, or creating new accounts. This is the technique used to survive credential rotation — the attacker creates a backdoor account or grants their compromised account additional access paths.

PAM countermeasure: real-time monitoring of privileged group membership changes (Event ID 4728, 4732, 4756), alerting on new account creation in Tier 0 OUs, and periodic access certification to detect unauthorized permissions.

**T1134 — Access Token Manipulation**

Adversaries manipulate access tokens to operate under a different user or system security context. Sub-techniques include T1134.001 (Token Impersonation/Theft — using tokens from other processes), T1134.002 (Create Process with Token), and T1134.005 (SID-History Injection — abusing the SID-History attribute to gain unauthorized access across trusts).

PAM countermeasure: enable SID filtering on trust boundaries, monitor for SID-History modifications (Event ID 4765, 4766), restrict SeImpersonatePrivilege and SeAssignPrimaryTokenPrivilege, and use Credential Guard to protect token material.

---

## Architettura PAM

### Session Management

Session management is the PAM component that provides visibility into what privileged users actually do during their sessions. Without it, a vaulted credential with MFA checkout is still a black box — you know who checked it out, but not what they did with it.

**Session Recording**

All privileged sessions — RDP, SSH, database console, web portal — are recorded as video-like playback files. The recording happens at the proxy layer (the PAM session manager brokers the connection) so the end user cannot disable or tamper with the recording. Storage requirements are non-trivial: a typical RDP session generates 5-15 MB/hour; SSH sessions are smaller (text-based). Plan for petabyte-scale storage in large enterprises with a 90-day hot retention and 7-year cold archive for compliance.

**Keystroke Logging**

Beyond video recording, keystroke and command logging captures the exact text input/output of terminal sessions. This enables full-text search across all privileged sessions — crucial for incident response ("did anyone run `DROP TABLE` in the last 30 days?") and compliance auditing. Sensitive data masking should be applied to prevent PAM logs from becoming a credential exposure vector themselves.

**Command Filtering**

Real-time command filtering intercepts and blocks dangerous commands before execution. Example policies:

- Block `rm -rf /` and variants on production Linux servers
- Block `DROP DATABASE`, `TRUNCATE TABLE` without approval on production databases
- Block `net user /add` on domain controllers
- Block `Stop-Service` for critical services without change ticket reference

Implementation is non-trivial — command filtering in SSH requires parsing the terminal protocol in real time, which can introduce latency. Most enterprise PAM platforms support regex-based command filters with configurable actions (block, alert, require approval).

### Credential Vaulting

The vault is the core of any PAM architecture. It is a hardened, encrypted repository for privileged credentials with strict access controls, audit logging, and automated rotation capabilities.

**Encryption at Rest**

Credentials stored in the vault must be encrypted using strong symmetric encryption (AES-256 is the industry standard). The encryption keys themselves require protection — typically using a Hardware Security Module (HSM) or a key hierarchy where the master key never leaves the HSM. CyberArk uses a proprietary vault with a server-level encryption key stored in a dedicated hardware appliance. HashiCorp Vault uses an unseal key mechanism with Shamir's Secret Sharing — the master key is split into N shares, and K of N shares are required to unseal the vault (typically 3 of 5).

**Rotation Policies**

Automated credential rotation ensures that even if a credential is compromised, it has a limited useful lifetime. Rotation frequencies depend on the account type and risk:

| Account Type | Recommended Rotation | Notes |
|---|---|---|
| Domain Admin | Every use (one-time password) | Check-in triggers immediate rotation |
| Local Admin | Every 24 hours | LAPS default; PAM can go more aggressive |
| Service Account | Every 30-90 days | Must coordinate with service restart |
| Application/API | Every 1-24 hours | Dynamic secrets preferred |
| Emergency/Break-glass | After every use | Manual rotation + verification |

**Check-In / Check-Out Workflow**

The fundamental PAM interaction model:

1. User requests access to a specific credential via the PAM portal
2. PAM verifies user identity (MFA), authorization (RBAC policy), and optionally requires manager approval
3. PAM checks out the credential — the user receives a time-limited session or one-time password
4. User completes their work
5. User checks in the credential (or it auto-expires)
6. PAM rotates the credential to invalidate the checked-out copy
7. Full audit trail: who, when, why, what they did (if session-recorded)

### Just-in-Time (JIT) Access

JIT access eliminates standing privileges — no one has permanent admin access. Instead, privileges are granted on demand for a limited duration and automatically revoked.

The concept: a database administrator does not have permanent `DBA` privileges. When they need to perform a maintenance task, they request JIT access through the PAM portal. After approval (automated policy or manual manager), they receive temporary DBA rights for 2 hours. After 2 hours, the rights are automatically revoked regardless of session state.

Implementation approaches:

- **Group membership manipulation**: Add the user to a privileged AD group temporarily, remove after the time window. Azure AD PIM uses this approach.
- **Temporary account provisioning**: Create a temporary privileged account, provide credentials, and delete the account after expiry.
- **Session brokering**: The user never receives credentials at all. The PAM system brokers the connection, injecting stored credentials transparently. When the session ends, the user has no credential to reuse.

### Just-Enough-Access (JEA)

JEA limits what a privileged user can do, not just when they can do it. In PowerShell environments, JEA uses constrained runspaces to expose only specific cmdlets and parameters.

Example JEA configuration for a DNS administrator who should be able to manage DNS records but not access the underlying OS:

```powershell
# DNSAdmin.psrc - Role Capability File
@{
    VisibleCmdlets = @(
        'DnsServer\Add-DnsServerResourceRecord',
        'DnsServer\Remove-DnsServerResourceRecord',
        'DnsServer\Set-DnsServerResourceRecord',
        'DnsServer\Get-DnsServerResourceRecord',
        'DnsServer\Get-DnsServerZone'
    )
    VisibleFunctions    = @()
    VisibleExternalCommands = @()
    VisibleProviders    = @()
    # No access to filesystem, registry, or arbitrary commands
}
```

```powershell
# DNSAdmin.pssc - Session Configuration File
@{
    SessionType            = 'RestrictedRemoteServer'
    RunAsVirtualAccount    = $true
    RoleDefinitions        = @{
        'DOMAIN\DNS-Operators' = @{ RoleCapabilities = 'DNSAdmin' }
    }
    TranscriptDirectory    = 'C:\PAM\Transcripts\DNS'
    LanguageMode           = 'NoLanguage'
}
```

Register the endpoint:

```powershell
Register-PSSessionConfiguration -Name 'DNSAdmin' `
    -Path 'C:\PAM\JEA\DNSAdmin.pssc' `
    -Force
```

The user connects via `Enter-PSSession -ComputerName dc01 -ConfigurationName DNSAdmin` and can only run the five DNS cmdlets. No filesystem access, no arbitrary PowerShell, no escape.

### Privilege Elevation and Delegation Management (PEDM)

PEDM addresses the endpoint privilege problem: users who need admin rights on their workstations to install software, modify network settings, or run specific applications. Instead of granting blanket local admin, PEDM solutions allow specific applications or actions to run elevated while the user remains a standard user.

Key capabilities:

- **Application whitelisting with elevation**: specific executables (e.g., the corporate VPN client installer) can run as admin without the user being admin.
- **Child process control**: even if an application runs elevated, its child processes can be restricted.
- **File integrity monitoring**: detect unauthorized modifications to elevated binaries.
- **Least privilege enforcement**: automatically remove admin rights from users who have them and provide PEDM as the replacement.

Enterprise implementations: BeyondTrust Privilege Management, CyberArk Endpoint Privilege Manager, Delinea Privilege Manager.

---

## Piattaforme Enterprise

### CyberArk Privileged Access Security

CyberArk is the dominant enterprise PAM platform and the benchmark against which alternatives are measured. Its architecture consists of several interconnected components:

**Digital Vault**

The vault is a hardened Windows server with a proprietary encrypted file system. All credentials, recordings, and policies are stored in the vault. It communicates via a proprietary protocol (not HTTP/HTTPS) on port 1858. The vault has no GUI — all interaction goes through PVWA or the API. The vault server should be isolated in its own network segment with strict firewall rules: only PVWA, CPM, and PSM servers should be able to reach it.

**Central Policy Manager (CPM)**

The CPM handles automated credential rotation. It connects to target systems (via SMB, SSH, LDAP, API) and changes passwords according to defined policies. CPM rotation flow: verify current password → generate new password → change password on target → update vault → verify new password works. If any step fails, CPM logs the failure and retries. CPM supports hundreds of target platforms via plugins.

**Privileged Session Manager (PSM)**

PSM is the session proxy. Users connect to PSM, which brokers the connection to the target system using vaulted credentials. The user never sees the actual password. PSM records the entire session (RDP as video, SSH as text log). PSM runs on Windows Server with RDS (for RDP proxying) or uses PSM for SSH (a separate component or integrated capability) for SSH session brokering.

**Privileged Threat Analytics (PTA)**

PTA provides behavioral analytics for privileged sessions. It consumes logs from the vault, PSM, and SIEM to detect anomalies: sessions at unusual times, commands never previously used, lateral movement patterns, and potential credential theft indicators.

**Password Vault Web Access (PVWA)**

PVWA is the web-based management interface where administrators configure policies, users request credentials, and auditors review session recordings. PVWA is the primary attack surface of the CyberArk deployment — it must be hardened, patched, and protected with WAF rules.

**CyberArk REST API Example — Retrieve Account Details**

```bash
# Authenticate to CyberArk
CYBERARK_TOKEN=$(curl -s -X POST \
  "https://pvwa.corp.local/PasswordVault/API/Auth/CyberArk/Logon" \
  -H "Content-Type: application/json" \
  -d '{"username":"apiuser","password":"'"${CYBERARK_API_PASS}"'"}' \
  | tr -d '"')

# Search for accounts matching a keyword
curl -s -X GET \
  "https://pvwa.corp.local/PasswordVault/API/Accounts?search=sqlprod&filter=safeName%20eq%20DatabaseAccounts" \
  -H "Authorization: ${CYBERARK_TOKEN}" | python3 -m json.tool

# Retrieve a specific account's password
curl -s -X POST \
  "https://pvwa.corp.local/PasswordVault/API/Accounts/42_8/Password/Retrieve" \
  -H "Authorization: ${CYBERARK_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"reason":"Scheduled maintenance CR-20260507"}' \
  | tr -d '"'

# Verify credential rotation
curl -s -X POST \
  "https://pvwa.corp.local/PasswordVault/API/Accounts/42_8/Verify" \
  -H "Authorization: ${CYBERARK_TOKEN}"

# Change credential immediately
curl -s -X POST \
  "https://pvwa.corp.local/PasswordVault/API/Accounts/42_8/Change" \
  -H "Authorization: ${CYBERARK_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"ChangeEntireGroup": false}'
```

### BeyondTrust

BeyondTrust offers two key products:

**Password Safe** — credential vaulting and session management. Comparable to CyberArk's vault + PSM. Supports credential rotation for Windows, Linux, databases, network devices, and cloud platforms. Session recording with keystroke logging and real-time monitoring.

**Privilege Management** — endpoint PEDM solution. Removes admin rights from endpoints and provides granular application elevation. Integrates with Password Safe for a unified platform. Strengths: strong endpoint privilege management and a unified agent for PEDM + application control.

### Delinea

Formerly Thycotic + Centrify. Two main products:

**Secret Server** — credential vault with a focus on ease of deployment. Web-based interface, SQL Server backend, distributed engine architecture for multi-site deployments. Notably simpler to deploy than CyberArk for mid-market organizations.

**Privilege Manager** — endpoint PEDM. Application control, privilege elevation, and local admin removal. Policy-based rules define which applications can run elevated.

### HashiCorp Vault

Vault takes a fundamentally different approach: instead of storing static secrets and rotating them, it generates dynamic, short-lived credentials on demand. This is the preferred approach for cloud-native and DevOps environments.

**Core Architecture**

Vault uses a client-server architecture. The server stores encrypted secrets and handles authentication/authorization. The storage backend is pluggable: Consul (HA), PostgreSQL, MySQL, Raft (integrated storage — recommended for production since Vault 1.4+). All data is encrypted with AES-256-GCM before it reaches the storage backend. Vault must be unsealed after every restart using Shamir's Secret Sharing or auto-unseal via cloud KMS (AWS KMS, Azure Key Vault, GCP Cloud KMS).

**Dynamic Secrets**

Vault generates unique credentials per request with automatic lease expiration:

```bash
# Enable the database secrets engine
vault secrets enable database

# Configure PostgreSQL connection
vault write database/config/production \
    plugin_name="postgresql-database-plugin" \
    allowed_roles="readonly","readwrite" \
    connection_url="postgresql://{{username}}:{{password}}@db.corp.local:5432/production?sslmode=require" \
    username="vault_admin" \
    password="${VAULT_DB_ADMIN_PASS}"

# Create a role that generates read-only credentials with 1-hour TTL
vault write database/roles/readonly \
    db_name="production" \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="DROP ROLE IF EXISTS \"{{name}}\";" \
    default_ttl="1h" \
    max_ttl="24h"

# Generate a dynamic credential
vault read database/creds/readonly
# Returns:
# Key                Value
# ---                -----
# lease_id           database/creds/readonly/abc123...
# lease_duration     1h
# username           v-token-readonly-xyz789
# password           A1B2-C3D4-E5F6-randomized

# Revoke a credential early
vault lease revoke database/creds/readonly/abc123...
```

**Auth Methods**

Vault supports numerous authentication methods — each appropriate for different use cases:

| Auth Method | Use Case |
|---|---|
| `userpass` | Human users (dev/test only) |
| `ldap` | Integration with Active Directory |
| `oidc` | SSO via Okta, Azure AD, etc. |
| `approle` | Application/service authentication |
| `kubernetes` | Pods authenticating via service account JWT |
| `aws` | EC2 instances / Lambda functions |
| `azure` | Azure VMs / managed identities |
| `cert` | mTLS certificate-based auth |

**Policies**

Vault policies use HCL (HashiCorp Configuration Language) to define path-based access control:

```hcl
# policy: dba-production.hcl
# Allows generating database credentials for production

path "database/creds/readonly" {
  capabilities = ["read"]
}

path "database/creds/readwrite" {
  capabilities = ["read"]
}

# Deny access to vault configuration
path "sys/*" {
  capabilities = ["deny"]
}

# Allow self-service token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}
```

```bash
# Apply the policy
vault policy write dba-production dba-production.hcl

# Create a token with the policy attached
vault token create -policy="dba-production" -ttl="8h" -display-name="dba-oncall"
```

### Open-Source Alternatives

**Teleport**

Teleport provides certificate-based access to SSH, Kubernetes, databases, and web applications. Instead of vaulting passwords, Teleport issues short-lived certificates (typically 8-12 hours) that grant access to specific resources. Architecture: Auth Server (CA + RBAC), Proxy Server (user-facing), Agents (installed on target machines). Session recording is built in — all SSH sessions are captured as events and can be replayed.

**HashiCorp Boundary**

Boundary provides identity-based access to infrastructure. It does not vault credentials — instead it manages the network path, brokering connections through a managed tunnel. When integrated with Vault, Boundary can inject dynamic credentials into brokered sessions. Think of it as a modern replacement for VPN-based access to internal resources.

Both solutions are open-core: the community editions are open source (Apache 2.0 for Teleport, MPL 2.0 for Boundary), with enterprise editions adding features like SSO integration, compliance controls, and hardware-backed CAs.

---

## Implementazione PAM

### Discovery Phase

You cannot protect what you do not know exists. The discovery phase catalogs every privileged account in the environment. This is consistently the most labor-intensive and politically difficult phase of a PAM implementation.

**Automated Discovery Methods**

```powershell
# PowerShell: Find all members of privileged AD groups
$privilegedGroups = @(
    'Domain Admins',
    'Enterprise Admins',
    'Schema Admins',
    'Administrators',
    'Account Operators',
    'Backup Operators',
    'Server Operators',
    'Print Operators'
)

$results = foreach ($group in $privilegedGroups) {
    Get-ADGroupMember -Identity $group -Recursive -ErrorAction SilentlyContinue |
    Select-Object @{N='Group';E={$group}},
                  Name,
                  SamAccountName,
                  objectClass,
                  @{N='Enabled';E={
                      (Get-ADUser $_.SamAccountName -Properties Enabled).Enabled
                  }},
                  @{N='LastLogon';E={
                      [datetime]::FromFileTime(
                          (Get-ADUser $_.SamAccountName -Properties LastLogonTimestamp).LastLogonTimestamp
                      )
                  }},
                  @{N='PasswordLastSet';E={
                      (Get-ADUser $_.SamAccountName -Properties PasswordLastSet).PasswordLastSet
                  }}
}

$results | Export-Csv -Path "C:\PAM\Discovery\PrivilegedAccounts.csv" -NoTypeInformation
```

```powershell
# Find service accounts (accounts with SPNs registered)
Get-ADUser -Filter {ServicePrincipalName -like "*"} -Properties `
    ServicePrincipalName, PasswordLastSet, Enabled, LastLogonDate |
Select-Object SamAccountName, Enabled,
    @{N='SPNs';E={$_.ServicePrincipalName -join '; '}},
    PasswordLastSet, LastLogonDate |
Export-Csv -Path "C:\PAM\Discovery\ServiceAccounts.csv" -NoTypeInformation
```

```bash
# Linux: Find all accounts with UID 0 (root equivalents)
awk -F: '$3 == 0 { print $1 }' /etc/passwd

# Find all sudoers
grep -rh '^[^#]' /etc/sudoers /etc/sudoers.d/ 2>/dev/null | \
    grep -v '^$' | sort -u

# Find SSH keys for all users
for home in /home/* /root; do
    user=$(basename "$home")
    if [ -d "${home}/.ssh" ]; then
        echo "=== ${user} ==="
        ls -la "${home}/.ssh/" 2>/dev/null
        # Check for authorized_keys (inbound access)
        if [ -f "${home}/.ssh/authorized_keys" ]; then
            echo "  authorized_keys entries: $(wc -l < "${home}/.ssh/authorized_keys")"
        fi
        # Check for private keys (outbound access)
        find "${home}/.ssh/" -name "id_*" ! -name "*.pub" -exec echo "  private key: {}" \;
    fi
done
```

**Ansible Discovery Playbook**

```yaml
# pam-discovery.yml - Inventory privileged accounts across Linux fleet
---
- name: PAM Discovery - Privileged Account Inventory
  hosts: all
  become: true
  gather_facts: true
  vars:
    discovery_output: "/tmp/pam_discovery_{{ inventory_hostname }}.json"

  tasks:
    - name: Gather root-equivalent accounts
      ansible.builtin.shell: |
        awk -F: '$3 == 0 { printf "{\"user\":\"%s\",\"uid\":%d,\"shell\":\"%s\"}\n", $1, $3, $7 }' /etc/passwd
      register: root_accounts
      changed_when: false

    - name: Gather sudo privileges
      ansible.builtin.shell: |
        grep -rh '^[^#]' /etc/sudoers /etc/sudoers.d/ 2>/dev/null | grep -v '^$'
      register: sudo_entries
      changed_when: false

    - name: Count authorized SSH keys per user
      ansible.builtin.shell: |
        for home in /home/* /root; do
          user=$(basename "$home")
          if [ -f "${home}/.ssh/authorized_keys" ]; then
            count=$(wc -l < "${home}/.ssh/authorized_keys")
            echo "${user}:${count}"
          fi
        done
      register: ssh_keys
      changed_when: false

    - name: Check for password age (shadow file)
      ansible.builtin.shell: |
        awk -F: '{ if ($2 != "!" && $2 != "*" && $2 != "!!") {
          last_change = $3;
          if (last_change > 0) {
            age_days = (systime()/86400) - last_change;
            printf "%s:%d\n", $1, age_days
          }
        }}' /etc/shadow
      register: password_age
      changed_when: false

    - name: Compile discovery report
      ansible.builtin.copy:
        content: |
          {
            "hostname": "{{ inventory_hostname }}",
            "timestamp": "{{ ansible_date_time.iso8601 }}",
            "root_accounts": {{ root_accounts.stdout_lines | to_json }},
            "sudo_entries": {{ sudo_entries.stdout_lines | to_json }},
            "ssh_key_counts": {{ ssh_keys.stdout_lines | to_json }},
            "password_ages": {{ password_age.stdout_lines | to_json }}
          }
        dest: "{{ discovery_output }}"
      delegate_to: localhost

    - name: Fetch discovery report
      ansible.builtin.fetch:
        src: "{{ discovery_output }}"
        dest: "./pam_discovery/"
        flat: false
```

### Risk Assessment and Prioritization

After discovery, prioritize accounts by risk. A simple risk scoring matrix:

| Factor | Weight | Scoring |
|---|---|---|
| Account type | 30% | DA=10, Service=7, Local Admin=5, App=4 |
| Password age | 25% | >365d=10, >180d=7, >90d=5, <90d=2 |
| System criticality | 25% | Tier 0=10, Tier 1=7, Tier 2=4, Tier 3=2 |
| Current controls | 20% | None=10, Partial=5, MFA+vault=1 |

Accounts scoring above 7.0 composite are Phase 1 targets. Domain Admins with old passwords on Tier 0 systems with no current controls will always top this list.

### Phased Rollout Strategy

PAM implementations that try to vault everything on day one fail. A proven phased approach:

**Phase 1 (Month 1-2): Quick Wins**
- Vault all Domain Admin and Enterprise Admin credentials
- Implement LAPS for local admin passwords
- Enable MFA on all existing privileged access portals
- Deploy break-glass procedures

**Phase 2 (Month 3-4): Service Accounts**
- Vault Tier 0 service accounts (DC services, PKI, Exchange)
- Implement session recording for DA sessions
- Begin credential rotation for vaulted accounts
- Deploy PAM on Privileged Access Workstations

**Phase 3 (Month 5-8): Expand Coverage**
- Vault Tier 1 service accounts (databases, application servers)
- Implement JIT access for database administrators
- Deploy session management for SSH access
- Integrate PAM with ticketing system for approval workflows

**Phase 4 (Month 9-12): Full Coverage**
- Vault application credentials and API keys
- Deploy dynamic secrets for CI/CD pipelines
- Implement PEDM on endpoints
- Full behavioral analytics deployment

### Vault Migration

Migrating passwords to a PAM vault without service disruption requires coordination:

1. **Pre-migration verification**: Verify the current password works. If it does not, reset it in a maintenance window before onboarding.
2. **Onboard to vault**: Store the current password in the vault with metadata (owner, platform, dependencies, rotation schedule).
3. **First managed rotation**: PAM rotates the password. Verify all dependent services still function. This is where service accounts cause problems — if three services use the same credential and PAM rotates it, all three must be updated. Map dependencies during discovery.
4. **Reconciliation**: If rotation fails (password changed on target but vault has old value, or vice versa), PAM reconciliation uses a privileged reconciliation account to force-reset the target password to match the vault.

### Session Management Deployment

Deploy session management in audit-only mode first. Record sessions but do not enforce command filtering. Review recordings for one month to establish baseline behavior. Then gradually enable command filtering policies based on observed patterns, starting with the most dangerous commands (rm -rf, DROP DATABASE) and expanding.

### Workflow Approval Chains

Define approval workflows based on risk:

| Risk Level | Access Type | Approval Required |
|---|---|---|
| Critical | Domain Admin, root on Tier 0 | Dual approval: team lead + CISO/security team |
| High | Service account modification, Tier 1 root | Single approval: team lead |
| Medium | Database DBA, application admin | Auto-approved with notification |
| Low | Read-only access, monitoring | Auto-approved, logged |

### Break-Glass Procedures

Break-glass procedures must be documented, tested, and available offline (printed, in a safe):

1. Two authorized personnel (dual custody) open the physical safe
2. Retrieve the sealed envelope containing break-glass credentials
3. Both personnel sign the retrieval log with date, time, and reason
4. Use the credentials to resolve the emergency
5. Immediately after resolution: change the break-glass password
6. Reseal new credentials in a new envelope, return to safe
7. File an incident report documenting the break-glass use
8. Security team reviews the incident within 24 hours

Test break-glass procedures quarterly. Untested procedures fail when needed.

---

## PAM per Ambienti Specifici

### Windows / Active Directory

**LAPS (Local Administrator Password Solution)**

LAPS (now "Windows LAPS" in Windows Server 2025 / Windows 11 24H2+) stores unique local admin passwords in Active Directory, encrypted and automatically rotated. Legacy LAPS stored passwords in a confidential AD attribute in plaintext; Windows LAPS encrypts passwords using DPAPI-NG and supports password backup to Azure AD.

```powershell
# Deploy Windows LAPS via Group Policy
# 1. Install the LAPS CSE on all managed machines (built-in on modern Windows)
# 2. Configure via GPO:
#    Computer Configuration > Administrative Templates > System > LAPS

# Retrieve LAPS password for a specific computer
Get-LapsADPassword -Identity "WORKSTATION-042" -AsPlainText

# Trigger immediate rotation
Reset-LapsPassword -Identity "WORKSTATION-042"

# Audit LAPS coverage - find computers WITHOUT LAPS passwords
Get-ADComputer -Filter * -Properties ms-Laps-Password |
    Where-Object { $_.'ms-Laps-Password' -eq $null } |
    Select-Object Name, DistinguishedName
```

**Group Managed Service Accounts (gMSA)**

gMSAs provide automatic password management for service accounts. The password is 240 characters, automatically rotated every 30 days, and managed entirely by AD. No human ever knows the password.

```powershell
# Create a KDS root key (one-time, per domain)
Add-KdsRootKey -EffectiveImmediately
# In production, use: Add-KdsRootKey -EffectiveTime ((Get-Date).AddHours(-10))

# Create the gMSA
New-ADServiceAccount -Name "gMSA-SQLSvc" `
    -DNSHostName "gmsa-sqlsvc.corp.local" `
    -PrincipalsAllowedToRetrieveManagedPassword "SQL-Servers-Group" `
    -ServicePrincipalNames "MSSQLSvc/sql01.corp.local:1433","MSSQLSvc/sql01.corp.local" `
    -KerberosEncryptionType AES128,AES256

# Install on target server
Install-ADServiceAccount -Identity "gMSA-SQLSvc"

# Test
Test-ADServiceAccount -Identity "gMSA-SQLSvc"
# Returns True if working correctly
```

**Protected Users Security Group**

Members of the Protected Users group receive hardened credential protections: no NTLM authentication, no DES or RC4 Kerberos encryption, no credential delegation, no caching of plaintext credentials. Add all privileged human accounts to this group.

```powershell
# Add all Domain Admins to Protected Users
Get-ADGroupMember "Domain Admins" |
    ForEach-Object { Add-ADGroupMember "Protected Users" -Members $_ }
```

Caveat: service accounts cannot be in Protected Users because they often require NTLM or credential delegation. Use gMSA for those instead.

**Authentication Policies and Silos (AD 2012 R2+)**

Authentication Policies restrict where privileged accounts can authenticate. Combined with Authentication Silos, they enforce that Domain Admin accounts can only authenticate to Tier 0 systems (domain controllers, PAM servers).

```powershell
# Create an Authentication Policy
New-ADAuthenticationPolicy -Name "Tier0-DomainAdmins" `
    -UserTGTLifetimeMins 60 `
    -UserAllowedToAuthenticateFrom (
        New-ADAuthenticationPolicySilo -Name "Tier0-Silo" `
            -UserAuthenticationPolicy "Tier0-DomainAdmins" `
            -ComputerAuthenticationPolicy "Tier0-DomainAdmins" `
            -Enforce
    )
```

### Linux / Unix

**Sudo Management**

Centralized sudo management is critical. Without it, each Linux server has its own `/etc/sudoers` with potentially different (and drifting) configurations.

```bash
# /etc/sudoers.d/pam-managed (deployed via Ansible/Puppet)
# Principle: named users, specific commands, full logging

# DBA team - database operations only
%dba-team ALL=(postgres) NOPASSWD: /usr/bin/psql, /usr/bin/pg_dump, /usr/bin/pg_restore
%dba-team ALL=(root) NOPASSWD: /usr/bin/systemctl status postgresql*, \
                                /usr/bin/systemctl restart postgresql*

# App team - application deployment only
%app-deploy ALL=(appuser) NOPASSWD: /opt/deploy/scripts/*.sh
%app-deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart app-*.service

# Monitoring team - read-only system inspection
%monitoring ALL=(root) NOPASSWD: /usr/bin/journalctl, /usr/bin/ss, \
                                 /usr/bin/top -bn1, /usr/bin/df, /usr/bin/free

# Full logging for all sudo usage
Defaults    log_output
Defaults    log_input
Defaults    logfile="/var/log/sudo.log"
Defaults    timestamp_timeout=0
```

**SSH Key Management**

Unmanaged SSH keys are a critical risk. A single private key copied to a developer laptop provides persistent access that survives password resets and PAM vault rotation.

Best practices:
- Use SSH Certificate Authority (CA) instead of static keys. Teleport implements this natively.
- Set key expiry dates using `ssh-keygen -V +52w` (52-week validity).
- Audit `authorized_keys` files across the fleet (the Ansible discovery playbook above does this).
- Disable password authentication entirely: `PasswordAuthentication no` in `sshd_config`.
- Use PAM session brokering so users never need direct SSH key access.

**Certificate-Based SSH Authentication**

```bash
# Generate an SSH CA key pair (do this once, protect the private key)
ssh-keygen -t ed25519 -f /etc/ssh/ca_key -C "SSH CA for corp.local"

# Sign a user's public key with the CA, granting 8-hour access
ssh-keygen -s /etc/ssh/ca_key \
    -I "jdoe-oncall-20260507" \
    -n "jdoe,root" \
    -V +8h \
    -z $(date +%s) \
    /home/jdoe/.ssh/id_ed25519.pub

# On target servers, trust the CA
echo "TrustedUserCAKeys /etc/ssh/ca_key.pub" >> /etc/ssh/sshd_config
systemctl reload sshd
```

### Cloud (AWS, Azure, GCP)

**AWS IAM Roles**

IAM Roles provide temporary credentials via STS (Security Token Service). No long-lived access keys required.

```bash
# Assume a role for privileged operations (returns temporary credentials)
aws sts assume-role \
    --role-arn "arn:aws:iam::123456789012:role/DatabaseAdmin" \
    --role-session-name "maintenance-20260507" \
    --duration-seconds 3600

# Use role chaining for cross-account access
# Account A trusts Account B's admin role
# Account B admin assumes role in Account A for maintenance
```

Integrate with Vault:

```bash
# Vault generates dynamic AWS credentials
vault secrets enable aws

vault write aws/config/root \
    access_key="${AWS_ACCESS_KEY}" \
    secret_key="${AWS_SECRET_KEY}" \
    region="eu-west-1"

vault write aws/roles/s3-readonly \
    credential_type="iam_user" \
    policy_document=-<<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject", "s3:ListBucket"],
      "Resource": ["arn:aws:s3:::production-data", "arn:aws:s3:::production-data/*"]
    }
  ]
}
EOF

# Generate temporary AWS credentials
vault read aws/creds/s3-readonly
```

**Azure Privileged Identity Management (PIM)**

Azure PIM provides JIT access for Azure AD roles and Azure resource roles. Users activate their eligible role assignments through the Azure portal with MFA + justification. The assignment automatically expires after a configured duration.

**GCP IAM Conditions**

GCP supports IAM Conditions for time-bound, attribute-based access:

```json
{
  "role": "roles/cloudsql.admin",
  "members": ["user:dba@corp.local"],
  "condition": {
    "title": "Maintenance window only",
    "expression": "request.time.getHours('Europe/Rome') >= 2 && request.time.getHours('Europe/Rome') <= 6 && request.time.getDayOfWeek('Europe/Rome') == 'SUNDAY'"
  }
}
```

### Database

**DBA Access Management**

Database administrators typically have the most powerful access in an organization — they can read, modify, and delete all data. PAM for databases involves:

- **Session brokering**: DBA connects through PAM proxy. PAM injects database credentials. DBA never knows the password.
- **Query auditing**: Every SQL statement is logged. Suspicious patterns (bulk SELECT on PII tables, DDL on production) generate alerts.
- **Dynamic credentials**: Vault generates short-lived database accounts with specific privileges per task.

**Query Auditing with PAM Session Recording**

When database sessions are brokered through PSM or Teleport, every query is captured. Pair this with SIEM integration to detect:

- `SELECT *` on tables containing PII
- DDL statements (`ALTER TABLE`, `DROP`) during non-maintenance windows
- Large data exports (`SELECT INTO OUTFILE`, `COPY TO`)
- Privilege escalation (`GRANT ALL`, `ALTER ROLE`)

### Network Devices

**TACACS+ Integration**

TACACS+ provides centralized AAA (Authentication, Authorization, Accounting) for network devices. Integrate PAM with TACACS+ so that network device credentials are vaulted and sessions are recorded.

Flow: Network engineer requests access via PAM portal → PAM authenticates user, checks authorization → PAM brokers SSH/Telnet session to network device using vaulted TACACS+ service account → TACACS+ authorizes commands per user profile → All commands logged to TACACS+ accounting and PAM session recording.

**RADIUS Integration**

RADIUS provides similar functionality with a focus on network access. PAM integrates with RADIUS to manage the credentials used by RADIUS for administrative device access, ensuring rotation and auditing.

### Kubernetes

**RBAC and Service Accounts**

Kubernetes RBAC controls access to API resources. PAM integration ensures that cluster-admin access is JIT and audited:

```yaml
# ClusterRole for emergency operations (bound via JIT)
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: emergency-cluster-admin
  labels:
    pam.corp.local/jit: "true"
rules:
  - apiGroups: ["*"]
    resources: ["*"]
    verbs: ["*"]
---
# ClusterRoleBinding created by PAM automation during JIT grant
# and deleted after the JIT window expires
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: jit-admin-jdoe-20260507
  annotations:
    pam.corp.local/expires: "2026-05-07T10:00:00Z"
    pam.corp.local/ticket: "INC-20260507-001"
subjects:
  - kind: User
    name: jdoe@corp.local
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: emergency-cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

**Secrets Management**

Never store secrets in Kubernetes Secrets (base64-encoded, not encrypted by default). Use:

- **Vault Agent Sidecar Injector**: automatically injects secrets from Vault into pod filesystem or environment.
- **External Secrets Operator**: syncs secrets from Vault/AWS Secrets Manager/Azure Key Vault into Kubernetes Secrets with encryption and rotation.
- **Sealed Secrets**: encrypt secrets client-side; only the cluster can decrypt them. Suitable for GitOps workflows.

```yaml
# Vault Agent Injector annotations on a pod
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        vault.hashicorp.com/agent-inject: "true"
        vault.hashicorp.com/role: "my-app"
        vault.hashicorp.com/agent-inject-secret-db-creds: "database/creds/readonly"
        vault.hashicorp.com/agent-inject-template-db-creds: |
          {{- with secret "database/creds/readonly" -}}
          PGUSER={{ .Data.username }}
          PGPASSWORD={{ .Data.password }}
          {{- end -}}
    spec:
      serviceAccountName: my-app
      containers:
        - name: app
          image: my-app:latest
```

---

## Attacchi al PAM — Red Team Perspective

This section covers attack techniques against PAM infrastructure itself. Understanding these is essential for both red team operators testing PAM deployments and blue team defenders hardening them.

### PAM Vault Exploitation

The vault is the highest-value target in the entire PAM infrastructure. If the attacker compromises the vault, they have every privileged credential in the organization.

**Attack vectors against the vault:**
- **Exploit vulnerabilities in the vault software itself.** CyberArk has had CVEs (e.g., CVE-2021-31796 — XML External Entity injection in PVWA). Keep PAM software patched as aggressively as production OS patches.
- **Compromise the vault server's OS.** If the attacker gains OS-level access to the vault server, they can access the vault data files, memory, or encryption keys. The vault server must be hardened to the same standard as a domain controller.
- **Steal the unseal keys.** For HashiCorp Vault, the attacker needs K of N unseal keys (or access to the auto-unseal KMS key). Social engineering, insider threat, or compromising the KMS account can achieve this.
- **Access the vault backup.** Vault backups contain all secrets. If backups are stored unencrypted or with weak access controls, the attacker takes the backup instead of attacking the live vault.

**Defense:**
- Isolate the vault in its own network segment with strict firewall rules
- Harden the vault OS: remove unnecessary services, disable remote desktop (CyberArk), use host-based firewall
- Monitor vault server for any unauthorized access
- Encrypt backups with a separate key and store offline
- For HashiCorp Vault: use auto-unseal with cloud KMS + restrict KMS access to the vault service account

### Credential Harvesting Before Vaulting

The most effective time to steal credentials is before they are vaulted. During a PAM implementation (which takes months), many credentials remain unprotected. Attackers who know a PAM rollout is underway may accelerate their timeline to harvest credentials before the protection is in place.

**Techniques:**
- Dump LSASS memory on servers before session recording is enabled
- Extract service account passwords from scripts, configuration files, and scheduled tasks before they are migrated to the vault
- Harvest SSH private keys from user home directories before certificate-based auth replaces them
- Kerberoast service accounts before gMSA migration eliminates their passwords

**Defense:**
- Prioritize the highest-risk credentials (DA, Tier 0 service accounts) in the first phase
- During the migration period, increase monitoring on not-yet-vaulted credentials
- Assume credentials discovered during the PAM implementation may already be compromised — rotate them during onboarding, not after

### Session Hijacking and Recording Bypass

**RDP Session Hijacking (tscon.exe)**

If the attacker has SYSTEM on a server where a privileged user has an active (or disconnected) RDP session, they can hijack it:

```cmd
# As SYSTEM — enumerate sessions
query user

# Hijack session 2 (no password needed when running as SYSTEM)
tscon 2 /dest:console
```

This bypasses PAM session recording because the attacker is connecting to an already-established session, not initiating a new one through the PAM proxy.

**Defense:** Disable disconnected sessions via GPO. Set session time limits. Monitor for `tscon.exe` execution (Event ID 4688 with suspicious parent process). Alert on session reconnection events.

**SSH Session Multiplexing Bypass**

If a user initiates a PAM-brokered SSH session and then opens additional sessions through SSH multiplexing (`ControlMaster`), the additional sessions may not be recorded.

**Defense:** Disable SSH multiplexing on PAM-managed connections. Configure `MaxSessions 1` per connection on critical servers.

### MFA Fatigue Attacks on PAM

MFA fatigue (also called MFA bombing or push notification spam) targets PAM systems that use push-based MFA. The attacker, who already has the user's primary credentials, repeatedly triggers MFA push notifications until the user approves one out of fatigue or confusion.

**Attack flow:**
1. Attacker obtains a PAM user's AD credentials (phishing, credential stuffing)
2. Attacker repeatedly attempts to log in to the PAM portal
3. Each attempt triggers an MFA push to the user's phone
4. User, receiving dozens of notifications, eventually approves one
5. Attacker gains PAM access

**Defense:**
- Use number-matching MFA (FIDO2, Microsoft Authenticator number match, Duo verified push) instead of simple push approval
- Rate-limit MFA attempts (block after 3 denied pushes within 5 minutes)
- Alert the security team on MFA denial patterns
- Prefer FIDO2/WebAuthn hardware keys for PAM access — phishing-resistant by design

### Kerberoasting Service Accounts Before Rotation

Kerberoasting requests a Kerberos TGS ticket for a service account with an SPN, then cracks the ticket offline to recover the plaintext password. This works against any AD account with an SPN and a weak password.

```bash
# Kerberoasting with Impacket (red team tool)
# This extracts TGS tickets for all accounts with SPNs
GetUserSPNs.py -request -dc-ip 10.10.10.1 \
    corp.local/lowprivuser:'Password123'

# Crack the ticket offline with hashcat
hashcat -m 13100 -a 0 kerberoast_hashes.txt wordlist.txt -r rules/best64.rule
```

**The PAM relevance:** If service accounts are being migrated to gMSA but have not been converted yet, their current passwords are vulnerable to Kerberoasting. An attacker who Kerberoasts the account before the gMSA migration has a password that may remain valid until the migration completes.

**Defense:**
- During the PAM migration, immediately rotate passwords for all service accounts with SPNs to 128+ character random strings
- Monitor for Kerberoasting indicators (Event ID 4769 with ticket encryption type 0x17 for RC4, requesting TGS for unusual SPNs)
- Accelerate gMSA migration for accounts with SPNs

### Pass-the-Hash on Cached Credentials

Even with PAM in place, if privileged accounts log in interactively to non-Tier-0 systems, their NTLM hash is cached in LSASS memory. An attacker who compromises that system can extract the hash and use it to authenticate to other systems.

```bash
# Mimikatz - extract NTLM hashes from LSASS
# (requires local admin or SYSTEM on the target)
sekurlsa::logonpasswords

# Pass-the-hash with Impacket
psexec.py -hashes :aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117a... \
    corp.local/admin@target-server.corp.local
```

**Defense:**
- Enable Credential Guard on all Windows 10+ / Server 2016+ systems to protect LSASS
- Add privileged accounts to the Protected Users group (disables NTLM, prevents credential caching)
- Enforce the tiered administration model: DA accounts only log on to DCs, never to workstations or member servers
- Enable RunAsPPL for LSASS to prevent userspace tools from reading its memory

### Targeting PAM Administrators

PAM administrators (the humans who manage the PAM platform) have access to configure policies, manage the vault, and potentially extract credentials. They are high-value social engineering targets.

**Attack vectors:**
- Phishing PAM admins to steal their credentials
- Compromising their workstations to capture keystrokes during PAM administration
- Bribing or coercing PAM admins (insider threat)
- Exploiting their elevated access during PAM maintenance windows

**Defense:**
- PAM admins must use dedicated PAWs (Privileged Access Workstations) for PAM administration
- Dual-admin approval for sensitive vault operations (adding new safes, modifying master policies)
- Background checks and periodic clearance reviews for PAM admin personnel
- Session recording for PAM admin sessions (yes, record the admins too)
- Separation of duties: the person who creates a policy should not be the person who approves it

### Supply Chain Attacks on PAM Software

The PAM platform itself is software with a supply chain. If an attacker compromises the PAM vendor's update mechanism, they can push a malicious update that exfiltrates all vaulted credentials.

Historical precedent: the SolarWinds Orion compromise (2020) demonstrated that enterprise management software is a viable supply chain attack vector. PAM software is an even higher-value target.

**Defense:**
- Verify integrity of PAM software updates (checksums, GPG signatures)
- Test updates in a staging environment before production deployment
- Monitor PAM software behavior for unexpected network connections
- Maintain an air-gapped backup of all vaulted credentials
- Have a PAM vendor incident response plan: what do you do if your PAM vendor announces a breach?

---

## Monitoraggio e Detection

### Anomalous Privileged Session Detection

Baseline normal privileged session behavior, then alert on deviations:

| Indicator | Normal | Anomalous |
|---|---|---|
| Session time | Business hours | 03:00 AM on a Saturday |
| Session duration | 15-60 minutes | 8+ hours continuous |
| Commands executed | Service restarts, config changes | `net user /add`, `mimikatz`, `psexec` |
| Source IP | Corporate VPN / PAW subnet | Unknown IP, TOR exit node |
| Geographic location | Expected country | New country, impossible travel |

### Lateral Movement with Privileged Credentials

Detect lateral movement by correlating logon events across systems:

**Splunk SPL — Detect Privileged Account Used on Multiple Hosts**

```spl
index=wineventlog sourcetype=WinEventLog:Security EventCode=4624 LogonType=10
| eval Account=mvindex(Account_Name, 1)
| where Account IN ("admin","svc-sql","da-jdoe")
| stats dc(ComputerName) as host_count values(ComputerName) as hosts
        earliest(_time) as first_seen latest(_time) as last_seen by Account
| where host_count > 3
| eval time_span=last_seen - first_seen
| where time_span < 3600
| table Account host_count hosts first_seen last_seen time_span
```

**KQL (Microsoft Sentinel) — Impossible Travel for Privileged Accounts**

```kql
let privileged_users = dynamic(["admin@corp.local", "da-jdoe@corp.local"]);
SigninLogs
| where UserPrincipalName in (privileged_users)
| where ResultType == 0
| project TimeGenerated, UserPrincipalName, IPAddress, Location,
          Latitude = toreal(LocationDetails.geoCoordinates.latitude),
          Longitude = toreal(LocationDetails.geoCoordinates.longitude)
| sort by UserPrincipalName, TimeGenerated asc
| extend PrevTime = prev(TimeGenerated, 1),
         PrevLat = prev(Latitude, 1),
         PrevLon = prev(Longitude, 1),
         PrevUser = prev(UserPrincipalName, 1)
| where UserPrincipalName == PrevUser
| extend TimeDiffHours = datetime_diff('hour', TimeGenerated, PrevTime)
| extend DistanceKm = geo_distance_2points(Longitude, Latitude, PrevLon, PrevLat) / 1000
| extend SpeedKmH = DistanceKm / TimeDiffHours
| where SpeedKmH > 900
| project TimeGenerated, UserPrincipalName, IPAddress, Location,
          DistanceKm, TimeDiffHours, SpeedKmH
```

### Unusual Privilege Elevation Patterns

**Splunk SPL — Detect Unusual Sudo Usage**

```spl
index=linux sourcetype=syslog "sudo:" NOT "pam_unix"
| rex "sudo:\s+(?<user>\S+)\s+:\s+.*COMMAND=(?<command>.*)"
| stats count by user command host
| eventstats avg(count) as avg_count stdev(count) as stdev_count by user
| where count > avg_count + (2 * stdev_count)
| table user host command count avg_count
| sort - count
```

### PAM Bypass Attempt Detection

Detect when users attempt to access privileged systems without going through the PAM proxy:

**Splunk SPL — Direct SSH to Servers Bypassing PAM**

```spl
index=linux sourcetype=syslog "sshd" "Accepted"
| rex "Accepted\s+(?<auth_method>\S+)\s+for\s+(?<user>\S+)\s+from\s+(?<src_ip>\S+)"
| where NOT src_ip IN ("10.10.50.10", "10.10.50.11")
  ```| `comment("10.10.50.10/11 are the PAM proxy servers")`
| stats count by user src_ip host auth_method
| table user src_ip host auth_method count
| sort - count
```

Complementary firewall rule: block SSH (port 22) from all sources except PAM proxy servers on production hosts. Then this detection becomes a canary — any hit means the firewall was bypassed or misconfigured.

### SIEM Integration

Key events to forward from PAM to SIEM:

| Event | Source | Priority |
|---|---|---|
| Failed vault login | PAM audit log | High |
| Credential checkout | PAM audit log | Medium |
| Credential check-in | PAM audit log | Low |
| Password rotation failure | CPM log | High |
| Session start/stop | PSM log | Medium |
| Blocked command | Command filter log | High |
| Break-glass account use | PAM audit log | Critical |
| Policy modification | PAM admin audit log | High |
| New account onboarded | PAM audit log | Medium |
| MFA failure | PAM auth log | High |

### Behavioral Analytics for Privileged Users

UEBA (User and Entity Behavior Analytics) for privileged accounts tracks:

- **Baseline establishment**: Normal working hours, typical systems accessed, common commands run, average session duration
- **Deviation scoring**: Each deviation from baseline increases a risk score. Multiple deviations compound.
- **Peer comparison**: If one DBA is behaving differently from all other DBAs, investigate.
- **Temporal patterns**: Privileged access that suddenly shifts to nights/weekends may indicate credential compromise.

Implementations: CyberArk PTA (native), Splunk UBA, Microsoft Sentinel UEBA, Exabeam.

---

## PAM e Zero Trust Integration

### PAM as Zero Trust Enabler

Zero Trust mandates "never trust, always verify." PAM is the enforcement point for this principle on privileged access. Without PAM, a zero trust architecture has a massive gap: privileged accounts that authenticate once and then operate with unchecked trust.

PAM enforces zero trust for privileged access by:
- **Eliminating standing privileges** (JIT): no permanent admin access = no implicit trust
- **Continuous authentication**: MFA at checkout, re-authentication during long sessions
- **Session monitoring**: continuous verification that the privileged session matches expected behavior
- **Least privilege enforcement**: JEA and PEDM ensure users can only do what they need

### Continuous Verification During Privileged Sessions

Static authentication (login once, trusted forever) is incompatible with zero trust. PAM implements continuous verification through:

- **Session heartbeats**: The PAM proxy periodically re-verifies that the user's session token is still valid.
- **Behavioral monitoring**: Real-time analysis of commands against the user's baseline. Anomalous behavior triggers step-up authentication or session termination.
- **Time-bound sessions**: Maximum session duration enforced regardless of activity. The user must re-authenticate through PAM to continue.
- **Risk-adaptive policies**: If the organization's threat level increases (e.g., active incident), PAM policies can dynamically shorten session durations, require additional approvers, or disable certain access paths.

### Device Trust for Privileged Access

Privileged access should only originate from trusted devices (PAWs — Privileged Access Workstations) with verified security posture:

- Device certificate issued by the corporate PKI
- Endpoint detection and response (EDR) agent running and healthy
- OS patches within SLA (e.g., critical patches applied within 72 hours)
- Full disk encryption enabled
- No unauthorized software installed

PAM integration: the PAM portal checks device posture before granting credential checkout. If the workstation fails posture checks, the request is denied even if the user's credentials and MFA are valid.

### Network Segmentation for PAM Infrastructure

PAM infrastructure must be isolated in its own network segment (Tier 0 management VLAN):

```
                    Internet
                       |
                   [Firewall]
                       |
                 [DMZ / User VLAN]
                       |
              [PAM Proxy / PVWA] ← users connect here
                       |
              [PAM Management VLAN] ← restricted access
              /        |         \
         [Vault]    [CPM]     [PSM]
                       |
              [Target Systems]
```

Firewall rules:
- Users → PVWA: HTTPS (443) only
- PVWA → Vault: proprietary protocol (1858) only
- CPM → Target systems: per-platform protocol (SMB, SSH, LDAP, API)
- PSM → Target systems: per-platform protocol (RDP, SSH)
- Everything else: DENY

### API Security for PAM

PAM platforms expose REST APIs for automation. These APIs are extremely sensitive — they can retrieve credentials programmatically.

Security requirements:
- Mutual TLS (mTLS) for all API connections
- API keys stored in a separate secrets manager (not in the PAM vault itself — circular dependency)
- Rate limiting: max 100 requests/minute per API client
- IP allowlisting: only automation servers can reach the PAM API
- Audit logging of every API call with source IP, client identity, and requested resource
- Segregated API accounts: each automation workflow gets its own API account with minimum required permissions

### Secrets Management in CI/CD Pipelines

Hardcoded credentials in CI/CD pipelines are one of the most common security findings. PAM-integrated secrets management eliminates this:

**Vault Agent in CI/CD (GitLab CI Example)**

```yaml
# .gitlab-ci.yml
deploy_production:
  stage: deploy
  image: hashicorp/vault:latest
  variables:
    VAULT_ADDR: "https://vault.corp.local:8200"
  id_tokens:
    VAULT_ID_TOKEN:
      aud: "https://vault.corp.local"
  script:
    # Authenticate to Vault using GitLab JWT
    - export VAULT_TOKEN=$(vault write -field=token auth/jwt/login \
        role="deploy-production" \
        jwt="${VAULT_ID_TOKEN}")

    # Retrieve database credentials dynamically
    - export DB_CREDS=$(vault read -format=json database/creds/deploy)
    - export DB_USER=$(echo $DB_CREDS | jq -r '.data.username')
    - export DB_PASS=$(echo $DB_CREDS | jq -r '.data.password')

    # Deploy (credentials are ephemeral, never stored)
    - ./deploy.sh --db-user="${DB_USER}" --db-pass="${DB_PASS}"

    # Credentials auto-expire after Vault lease TTL
  after_script:
    # Explicitly revoke the lease (belt + suspenders)
    - vault lease revoke -prefix database/creds/deploy/ 2>/dev/null || true
```

**Vault Policy for CI/CD**

```hcl
# ci-deploy-production.hcl
# Only allows reading deployment credentials, nothing else

path "database/creds/deploy" {
  capabilities = ["read"]
}

path "secret/data/deploy/production/*" {
  capabilities = ["read"]
}

# Deny everything else explicitly
path "sys/*" {
  capabilities = ["deny"]
}

path "auth/*" {
  capabilities = ["deny"]
}
```

---

## Compliance e Governance

### PCI-DSS Requirement 8

PCI-DSS v4.0 Requirement 8 (Identify Users and Authenticate Access) directly mandates PAM controls:

- **8.2.1**: All users must be assigned a unique ID. No shared/generic privileged accounts.
- **8.2.2**: Group, shared, or generic accounts are not used for administration of system components.
- **8.3.6**: Passwords must be a minimum of 12 characters (or 8 if system does not support 12). PAM-generated passwords should be 30+ characters.
- **8.3.9**: Passwords changed at least once every 90 days. PAM credential rotation satisfies this.
- **8.4.2**: MFA for all access into the CDE (Cardholder Data Environment). PAM enforces MFA on privileged access to CDE systems.
- **8.6.1**: Interactive login for application and system accounts is managed — PAM vaults these credentials and prevents interactive use.

### SOX IT Controls

Sarbanes-Oxley (SOX) requires controls over IT systems that impact financial reporting. PAM provides:

- **Access management**: Demonstrable control over who can access financial systems with privileged rights.
- **Segregation of duties**: Approval workflows ensure no single person can both initiate and approve privileged access.
- **Audit trail**: Complete record of all privileged actions on systems in scope for SOX.
- **Access reviews**: Periodic certification that privileged access is appropriate and authorized.

SOX auditors will ask: "Show me who has admin access to the ERP system, how they got it, and what they did." PAM provides a single source of truth for all three answers.

### HIPAA Minimum Necessary Access

HIPAA's Minimum Necessary Standard requires that access to Protected Health Information (PHI) be limited to the minimum necessary for the task. For privileged access:

- DBAs should not have standing access to tables containing PHI
- JIT access with time limits for PHI-containing databases
- Session recording to demonstrate that only necessary data was accessed
- Automatic revocation of access after the maintenance task is complete

### ISO 27001 A.9 Access Control

ISO 27001:2022 Annex A, Control A.9 (Access Control) maps directly to PAM:

- **A.9.1** — Access control policy: Documented PAM policies and procedures
- **A.9.2** — User access management: Credential vaulting, JIT provisioning, access reviews
- **A.9.3** — User responsibilities: MFA enforcement, session time limits
- **A.9.4** — System and application access control: PEDM, JEA, command filtering

### NIST CSF PR.AC

NIST Cybersecurity Framework PR.AC (Access Control) subcategories relevant to PAM:

- **PR.AC-1**: Identities and credentials are issued, managed, verified, revoked, and audited.
- **PR.AC-3**: Remote access is managed. PAM brokers and records all remote privileged access.
- **PR.AC-4**: Access permissions and authorizations are managed, incorporating least privilege and separation of duties.
- **PR.AC-6**: Identities are proofed and bound to credentials and asserted in interactions.
- **PR.AC-7**: Users, devices, and other assets are authenticated commensurate with the risk of the transaction.

### Audit Reporting and Attestation

PAM generates several report categories for auditors:

| Report | Content | Frequency |
|---|---|---|
| Privileged Account Inventory | All vaulted accounts, owners, rotation status | Monthly |
| Access Activity | Who checked out which credentials, when, for how long | On demand |
| Session Recordings | Video/text recordings of privileged sessions | Retained per policy |
| Policy Compliance | Accounts not meeting rotation/complexity policies | Weekly |
| Failed Operations | Rotation failures, authentication failures | Daily |
| Break-Glass Usage | Every use of emergency accounts | Per occurrence |

### Access Certification Campaigns

Periodic access certification (also called access review or entitlement review) ensures that privileged access remains appropriate over time. Without it, privilege accumulates — users change roles but retain their old access (privilege creep).

Campaign workflow:

1. PAM system generates a list of all users with privileged access, grouped by manager
2. Each manager reviews their direct reports' access and certifies (approve) or revokes (remove)
3. Uncertified access is automatically revoked after the review deadline
4. Results are logged for audit evidence
5. Frequency: quarterly for high-risk access, semi-annually for medium-risk

**PowerShell — Generate Access Certification Report**

```powershell
# Generate a certification report for all privileged group memberships
$privilegedGroups = @(
    'Domain Admins', 'Enterprise Admins', 'Schema Admins',
    'Administrators', 'Account Operators', 'Backup Operators'
)

$report = foreach ($groupName in $privilegedGroups) {
    $members = Get-ADGroupMember -Identity $groupName -Recursive -ErrorAction SilentlyContinue
    foreach ($member in $members) {
        $user = Get-ADUser $member.SamAccountName -Properties `
            Manager, Department, Title, LastLogonDate, Enabled -ErrorAction SilentlyContinue
        if ($user) {
            $manager = if ($user.Manager) {
                (Get-ADUser $user.Manager -Properties DisplayName).DisplayName
            } else { "NO MANAGER ASSIGNED" }

            [PSCustomObject]@{
                Group           = $groupName
                SamAccountName  = $user.SamAccountName
                DisplayName     = $user.Name
                Title           = $user.Title
                Department      = $user.Department
                Manager         = $manager
                Enabled         = $user.Enabled
                LastLogon       = $user.LastLogonDate
                CertifiedBy     = ""
                CertifiedDate   = ""
                Decision        = ""  # APPROVE / REVOKE
            }
        }
    }
}

$timestamp = Get-Date -Format "yyyyMMdd"
$report | Export-Csv -Path "C:\PAM\Reports\AccessCertification_${timestamp}.csv" -NoTypeInformation
Write-Host "Certification report generated: $($report.Count) entitlements to review"
```

---

## Laboratorio

### Lab 1: Deploy HashiCorp Vault + Teleport

**Prerequisites:** Docker, Docker Compose, a Linux workstation.

**Vault Deployment**

```bash
# Create the lab directory structure
mkdir -p ~/pam-lab/{vault/{config,data,logs},teleport/{config,data}}

# Vault server configuration
cat > ~/pam-lab/vault/config/vault.hcl <<'VAULTCFG'
ui            = true
disable_mlock = true

storage "raft" {
  path    = "/vault/data"
  node_id = "vault-lab-01"
}

listener "tcp" {
  address         = "0.0.0.0:8200"
  tls_disable     = true  # Lab only — production MUST use TLS
}

api_addr     = "http://127.0.0.1:8200"
cluster_addr = "https://127.0.0.1:8201"

telemetry {
  disable_hostname = true
  prometheus_retention_time = "12h"
}
VAULTCFG

# Docker Compose for the lab
cat > ~/pam-lab/docker-compose.yml <<'COMPOSE'
version: "3.8"
services:
  vault:
    image: hashicorp/vault:1.18
    container_name: pam-vault
    cap_add:
      - IPC_LOCK
    ports:
      - "8200:8200"
    volumes:
      - ./vault/config:/vault/config:ro
      - ./vault/data:/vault/data
      - ./vault/logs:/vault/logs
    environment:
      VAULT_ADDR: "http://127.0.0.1:8200"
    command: vault server -config=/vault/config/vault.hcl

  postgres:
    image: postgres:16
    container_name: pam-postgres
    environment:
      POSTGRES_USER: vault_admin
      POSTGRES_PASSWORD: VaultLabP@ss2026
      POSTGRES_DB: production
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  target-ssh:
    image: ubuntu:24.04
    container_name: pam-target-ssh
    command: >
      bash -c "apt-get update && apt-get install -y openssh-server sudo &&
      mkdir /run/sshd &&
      echo 'root:TargetRoot2026' | chpasswd &&
      echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config &&
      /usr/sbin/sshd -D"
    ports:
      - "2222:22"

volumes:
  pgdata:
COMPOSE

# Start the lab
cd ~/pam-lab && docker compose up -d

# Initialize Vault
export VAULT_ADDR="http://127.0.0.1:8200"

vault operator init -key-shares=3 -key-threshold=2 \
    -format=json > ~/pam-lab/vault-init.json

# CRITICAL: In production, distribute these keys to separate custodians
# In the lab, we unseal immediately
UNSEAL_KEY_1=$(jq -r '.unseal_keys_b64[0]' ~/pam-lab/vault-init.json)
UNSEAL_KEY_2=$(jq -r '.unseal_keys_b64[1]' ~/pam-lab/vault-init.json)
ROOT_TOKEN=$(jq -r '.root_token' ~/pam-lab/vault-init.json)

vault operator unseal "$UNSEAL_KEY_1"
vault operator unseal "$UNSEAL_KEY_2"

export VAULT_TOKEN="$ROOT_TOKEN"
vault status
```

**Teleport Deployment**

```bash
# Teleport configuration
cat > ~/pam-lab/teleport/config/teleport.yaml <<'TELECFG'
version: v3
teleport:
  nodename: teleport-lab
  data_dir: /var/lib/teleport
  log:
    output: stderr
    severity: INFO

auth_service:
  enabled: true
  listen_addr: 0.0.0.0:3025
  cluster_name: pam-lab.local
  tokens:
    - proxy,node,db:lab-join-token-2026

proxy_service:
  enabled: true
  listen_addr: 0.0.0.0:3023
  web_listen_addr: 0.0.0.0:3080
  public_addr: localhost:3080

ssh_service:
  enabled: true
  labels:
    env: lab
    role: teleport-server

db_service:
  enabled: true
  databases:
    - name: production-db
      protocol: postgres
      uri: pam-postgres:5432
      static_labels:
        env: lab
TELECFG

# Add Teleport to docker-compose.yml (append to services section)
cat >> ~/pam-lab/docker-compose.yml <<'TELEPORT'

  teleport:
    image: public.ecr.aws/gravitational/teleport-distroless:16
    container_name: pam-teleport
    ports:
      - "3023:3023"
      - "3024:3024"
      - "3025:3025"
      - "3080:3080"
    volumes:
      - ./teleport/config:/etc/teleport:ro
      - ./teleport/data:/var/lib/teleport
    command: start --config=/etc/teleport/teleport.yaml
TELEPORT

docker compose up -d teleport
```

### Lab 2: Vault SSH Credentials

```bash
export VAULT_ADDR="http://127.0.0.1:8200"
export VAULT_TOKEN="$ROOT_TOKEN"

# Enable the SSH secrets engine
vault secrets enable ssh

# Configure the Signed Certificates mode (recommended over OTP)
vault write ssh/config/ca generate_signing_key=true

# Get the public key and distribute to target servers
vault read -field=public_key ssh/config/ca > ~/pam-lab/vault-ssh-ca.pub

# On the target SSH server, trust the CA
docker exec pam-target-ssh bash -c \
    "echo '$(cat ~/pam-lab/vault-ssh-ca.pub)' > /etc/ssh/trusted-user-ca-keys.pubs"
docker exec pam-target-ssh bash -c \
    "echo 'TrustedUserCAKeys /etc/ssh/trusted-user-ca-keys.pubs' >> /etc/ssh/sshd_config"
docker exec pam-target-ssh bash -c "kill -HUP \$(cat /run/sshd.pid)"

# Create a role for SSH access (8-hour certificates)
vault write ssh/roles/admin-access \
    key_type=ca \
    default_user=root \
    allowed_users="root,ubuntu" \
    ttl=8h \
    max_ttl=24h \
    allow_user_certificates=true \
    default_extensions='{"permit-pty":"","permit-agent-forwarding":""}'

# Sign a user's SSH key
vault write -field=signed_key ssh/sign/admin-access \
    public_key=@~/.ssh/id_ed25519.pub \
    valid_principals="root" > ~/.ssh/id_ed25519-cert.pub

# Test the connection
ssh -p 2222 -o StrictHostKeyChecking=no root@localhost

# Verify the certificate details
ssh-keygen -L -f ~/.ssh/id_ed25519-cert.pub
# Shows: Valid from/to, principals, extensions
```

### Lab 3: Dynamic Database Credentials

```bash
# Enable the database secrets engine
vault secrets enable database

# Configure the PostgreSQL connection
vault write database/config/production \
    plugin_name="postgresql-database-plugin" \
    allowed_roles="lab-readonly","lab-readwrite" \
    connection_url="postgresql://{{username}}:{{password}}@localhost:5432/production?sslmode=disable" \
    username="vault_admin" \
    password="VaultLabP@ss2026"

# Create a read-only role (15-minute TTL for the lab)
vault write database/roles/lab-readonly \
    db_name="production" \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="DROP ROLE IF EXISTS \"{{name}}\";" \
    default_ttl="15m" \
    max_ttl="1h"

# Create a read-write role (30-minute TTL)
vault write database/roles/lab-readwrite \
    db_name="production" \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
        GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\";" \
    revocation_statements="DROP ROLE IF EXISTS \"{{name}}\";" \
    default_ttl="30m" \
    max_ttl="2h"

# Generate dynamic credentials
vault read database/creds/lab-readonly
# Output:
# Key                Value
# ---                -----
# lease_id           database/creds/lab-readonly/...
# lease_duration     15m
# username           v-root-lab-read-xxxx
# password           random-generated-password

# Test the credentials
PGPASSWORD=$(vault read -field=password database/creds/lab-readonly) \
    psql -h localhost -U $(vault read -field=username database/creds/lab-readonly) \
    -d production -c "SELECT current_user, now();"

# List active leases
vault list sys/leases/lookup/database/creds/lab-readonly

# Revoke a specific lease
vault lease revoke database/creds/lab-readonly/LEASE_ID_HERE

# Revoke ALL leases for a role (emergency rotation)
vault lease revoke -prefix database/creds/lab-readonly
```

### Lab 4: JIT Access Implementation

Implement JIT access using Vault policies and time-limited tokens:

```bash
# Create a standard DBA policy (no direct credential access)
cat > ~/pam-lab/dba-standard.hcl <<'POLICY'
# DBA standard access - read-only credentials only
path "database/creds/lab-readonly" {
  capabilities = ["read"]
}

# Allow listing available roles
path "database/roles/*" {
  capabilities = ["list"]
}

# Self-service token management
path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
POLICY

# Create an elevated DBA policy (read-write, time-limited)
cat > ~/pam-lab/dba-elevated.hcl <<'POLICY'
# DBA elevated access - read-write credentials
# This policy should only be attached to tokens with short TTL

path "database/creds/lab-readwrite" {
  capabilities = ["read"]
}

path "database/creds/lab-readonly" {
  capabilities = ["read"]
}

path "database/roles/*" {
  capabilities = ["list"]
}

path "auth/token/renew-self" {
  capabilities = ["update"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
POLICY

vault policy write dba-standard ~/pam-lab/dba-standard.hcl
vault policy write dba-elevated ~/pam-lab/dba-elevated.hcl

# Simulate JIT: create a short-lived token with elevated access
# In production, this would be triggered by an approval workflow
JIT_TOKEN=$(vault token create \
    -policy="dba-elevated" \
    -ttl="30m" \
    -display-name="jit-dba-maintenance-20260507" \
    -metadata="ticket=INC-20260507-001" \
    -metadata="approver=security-team" \
    -format=json | jq -r '.auth.client_token')

echo "JIT token created: ${JIT_TOKEN}"
echo "Valid for 30 minutes. Use it to get database credentials."

# Use the JIT token
VAULT_TOKEN="$JIT_TOKEN" vault read database/creds/lab-readwrite

# Verify token metadata and expiry
VAULT_TOKEN="$JIT_TOKEN" vault token lookup

# After 30 minutes, the token auto-expires.
# Demonstrate revocation (manual early termination):
vault token revoke "$JIT_TOKEN"
```

### Lab 5: Credential Theft Attack Testing

**WARNING: Only perform these exercises in the lab environment. Unauthorized use of these techniques on production systems is illegal.**

```bash
# --- Attack 1: Attempt to read Vault secrets without authentication ---
# This should fail with 403
curl -s http://127.0.0.1:8200/v1/database/creds/lab-readonly | jq .
# Expected: {"errors":["permission denied"]}

# --- Attack 2: Attempt token enumeration ---
# Try to use an expired/revoked token
FAKE_TOKEN="hvs.faketoken123456789"
curl -s -H "X-Vault-Token: ${FAKE_TOKEN}" \
    http://127.0.0.1:8200/v1/database/creds/lab-readonly | jq .
# Expected: {"errors":["permission denied"]}

# --- Attack 3: Check for credential leakage in Vault audit log ---
vault audit enable file file_path=/vault/logs/audit.log

# Now perform a credential read
vault read database/creds/lab-readonly

# Check the audit log - passwords should be HMAC'd, not plaintext
docker exec pam-vault cat /vault/logs/audit.log | \
    python3 -m json.tool | grep -i password
# Should show HMAC hashes, not actual passwords

# --- Attack 4: Attempt to access Vault storage directly ---
# If someone accesses the Raft storage files, they should be encrypted
docker exec pam-vault ls -la /vault/data/
# Data is AES-256-GCM encrypted at rest

# --- Attack 5: Test credential expiry enforcement ---
# Get credentials, wait for TTL, try to use them
CREDS=$(vault read -format=json database/creds/lab-readonly)
DB_USER=$(echo $CREDS | jq -r '.data.username')
DB_PASS=$(echo $CREDS | jq -r '.data.password')
LEASE_ID=$(echo $CREDS | jq -r '.lease_id')

echo "Got user: ${DB_USER} - waiting for lease to expire..."
# Force-revoke the lease (simulating expiry)
vault lease revoke "$LEASE_ID"

# Now try to use the revoked credentials
PGPASSWORD="$DB_PASS" psql -h localhost -U "$DB_USER" -d production \
    -c "SELECT 1;" 2>&1
# Expected: FATAL: role "v-root-lab-read-xxxx" does not exist
# (Vault dropped the role when the lease was revoked)
```

### Lab 6: Detection and Logging Verification

```bash
# Verify Vault audit logging captures all operations
vault audit list
# Should show: file/ enabled

# Check audit log for our lab activities
docker exec pam-vault cat /vault/logs/audit.log | \
    python3 -c "
import sys, json
for line in sys.stdin:
    entry = json.loads(line)
    req = entry.get('request', {})
    resp = entry.get('response', {})
    auth = entry.get('auth', {})
    print(f'{entry[\"time\"]} | {req.get(\"operation\",\"?\")} | {req.get(\"path\",\"?\")} | accessor={auth.get(\"accessor\",\"?\")} | remote={req.get(\"remote_address\",\"?\")}')
"

# Verify that sensitive data is masked in logs
docker exec pam-vault cat /vault/logs/audit.log | \
    python3 -c "
import sys, json
for line in sys.stdin:
    entry = json.loads(line)
    resp_data = entry.get('response', {}).get('data', {})
    if 'password' in str(resp_data):
        print('WARNING: Possible password in audit log!')
        print(json.dumps(resp_data, indent=2))
    else:
        # Verify HMAC masking
        if resp_data:
            for k, v in resp_data.items():
                if 'hmac' in str(v).lower():
                    print(f'GOOD: {k} is HMAC-masked')
"

# Test alert on failed authentication (monitor this)
for i in {1..5}; do
    curl -s -H "X-Vault-Token: bad-token-attempt-${i}" \
        http://127.0.0.1:8200/v1/sys/health > /dev/null 2>&1
done

# Check for the failed attempts in audit log
docker exec pam-vault cat /vault/logs/audit.log | \
    grep -c '"error"' | xargs -I{} echo "Failed operations in audit log: {}"
```

### Lab 7: Access Review Audit

```bash
# Generate a Vault access review report

# List all auth methods
vault auth list -format=json | jq 'keys[]'

# List all policies
vault policy list

# Read each policy to understand granted access
for policy in $(vault policy list | grep -v root | grep -v default); do
    echo "=== Policy: ${policy} ==="
    vault policy read "$policy"
    echo ""
done

# List all active tokens (requires root token)
vault list auth/token/accessors 2>/dev/null

# For each accessor, look up token metadata
for accessor in $(vault list -format=json auth/token/accessors 2>/dev/null | jq -r '.[]'); do
    vault token lookup -accessor "$accessor" -format=json 2>/dev/null | \
        jq '{
            display_name: .data.display_name,
            policies: .data.policies,
            creation_time: (.data.creation_time | todate),
            expire_time: .data.expire_time,
            ttl: .data.ttl,
            metadata: .data.meta
        }'
done

# List all active database credential leases
vault list -format=json sys/leases/lookup/database/creds/lab-readonly 2>/dev/null | \
    jq -r '.[]' | while read lease; do
    vault lease lookup "database/creds/lab-readonly/${lease}" 2>/dev/null | \
        grep -E "issue_time|expire_time|ttl"
    echo "---"
done

# Generate summary report
cat <<'REPORT'
=== PAM Lab Access Review Summary ===
Date: 2026-05-07

1. Authentication Methods: [list from vault auth list]
2. Policies Defined: [list from vault policy list]
3. Active Tokens: [count from accessor list]
4. Active Database Leases: [count from lease list]
5. Audit Logging: [enabled/disabled]

Review Actions:
- [ ] Verify all tokens have appropriate TTLs
- [ ] Confirm no orphan tokens exist
- [ ] Validate policies follow least privilege
- [ ] Check for unused policies (candidates for removal)
- [ ] Verify audit log integrity
REPORT
```

**Lab Cleanup**

```bash
# Stop and remove all lab containers
cd ~/pam-lab && docker compose down -v

# Remove lab data (contains sensitive initialization data)
rm -rf ~/pam-lab/vault/data/*
rm -f ~/pam-lab/vault-init.json

echo "Lab environment cleaned up."
```

---

## Appendice A: Quick Reference — Vault CLI Commands

| Command | Purpose |
|---|---|
| `vault status` | Check seal status and HA mode |
| `vault operator init` | Initialize a new Vault cluster |
| `vault operator unseal` | Provide an unseal key shard |
| `vault operator seal` | Seal the vault (emergency) |
| `vault secrets list` | List enabled secrets engines |
| `vault secrets enable <engine>` | Enable a secrets engine |
| `vault auth list` | List enabled auth methods |
| `vault auth enable <method>` | Enable an auth method |
| `vault policy list` | List all policies |
| `vault policy write <name> <file>` | Create/update a policy |
| `vault token create` | Generate a new token |
| `vault token revoke <token>` | Revoke a token |
| `vault lease revoke <id>` | Revoke a lease |
| `vault lease revoke -prefix <path>` | Revoke all leases under a path |
| `vault audit enable file` | Enable file audit logging |
| `vault read <path>` | Read a secret or generate dynamic cred |
| `vault write <path>` | Write data or configure an engine |
| `vault kv get <path>` | Read from KV v2 secrets engine |
| `vault kv put <path>` | Write to KV v2 secrets engine |

## Appendice B: PAM Implementation Checklist

- [ ] Privileged account inventory completed (all types)
- [ ] Risk assessment and prioritization matrix created
- [ ] Break-glass procedures documented and tested
- [ ] PAM vault deployed and hardened
- [ ] Domain Admin credentials vaulted with MFA checkout
- [ ] Local admin passwords managed (LAPS or PAM rotation)
- [ ] Service accounts inventoried and migration plan created
- [ ] gMSA deployed for eligible service accounts
- [ ] Session recording enabled for Tier 0 access
- [ ] Credential rotation policies defined and tested
- [ ] Approval workflows configured by risk level
- [ ] PAM integrated with SIEM
- [ ] Detection rules deployed for PAM bypass and credential theft
- [ ] PEDM deployed on privileged workstations
- [ ] CI/CD pipelines migrated to dynamic secrets
- [ ] Access certification campaign scheduled (quarterly)
- [ ] PAM admin access hardened (PAWs, dual approval, session recording)
- [ ] Break-glass procedure tested (quarterly drill)
- [ ] Compliance mapping documented (PCI-DSS, SOX, HIPAA, ISO 27001)
- [ ] Disaster recovery plan for PAM infrastructure tested

## Appendice C: Ansible Playbook — PAM Credential Rotation Verification

```yaml
# pam-rotation-verify.yml
# Verifies that PAM-managed credentials on Linux hosts
# match the expected rotation state
---
- name: PAM Credential Rotation Verification
  hosts: all
  become: true
  gather_facts: false
  vars:
    max_password_age_days: 90
    alert_email: "security-team@corp.local"

  tasks:
    - name: Check password ages for local accounts
      ansible.builtin.shell: |
        awk -F: '{
          if ($2 != "!" && $2 != "*" && $2 != "!!" && $1 != "root") {
            last_change = $3;
            if (last_change > 0) {
              age_days = int((systime()/86400) - last_change);
              if (age_days > {{ max_password_age_days }}) {
                printf "VIOLATION:%s:%d\n", $1, age_days
              } else {
                printf "OK:%s:%d\n", $1, age_days
              }
            }
          }
        }' /etc/shadow
      register: password_check
      changed_when: false

    - name: Report violations
      ansible.builtin.debug:
        msg: "{{ item }}"
      loop: "{{ password_check.stdout_lines | select('match', '^VIOLATION:') | list }}"
      when: password_check.stdout_lines | select('match', '^VIOLATION:') | list | length > 0

    - name: Verify SSH authorized_keys have not been modified outside PAM
      ansible.builtin.find:
        paths: ["/home", "/root"]
        patterns: "authorized_keys"
        recurse: true
        age: "-1d"
        file_type: file
      register: recent_authkeys

    - name: Alert on recently modified authorized_keys
      ansible.builtin.debug:
        msg: "ALERT: authorized_keys modified in last 24h: {{ item.path }} ({{ item.mtime }})"
      loop: "{{ recent_authkeys.files }}"
      when: recent_authkeys.files | length > 0

    - name: Verify no unauthorized SSH keys exist
      ansible.builtin.shell: |
        for home in /home/* /root; do
          user=$(basename "$home")
          if [ -f "${home}/.ssh/authorized_keys" ]; then
            while IFS= read -r key; do
              echo "${user}:${key}"
            done < "${home}/.ssh/authorized_keys"
          fi
        done
      register: all_ssh_keys
      changed_when: false

    - name: Output SSH key inventory for review
      ansible.builtin.debug:
        msg: "SSH key found: {{ item }}"
      loop: "{{ all_ssh_keys.stdout_lines }}"
```

## Appendice D: Detection Rules Summary

| Rule Name | Data Source | Condition | Severity |
|---|---|---|---|
| PAM Bypass - Direct SSH | Linux syslog | SSH accepted from non-PAM IP | High |
| Credential Theft - LSASS Access | Windows Security | Process accessing LSASS (Event 10) | Critical |
| Privilege Escalation - Group Mod | AD Security | Event 4728/4732/4756 on privileged groups | Critical |
| Kerberoasting Attempt | AD Security | Event 4769 with RC4 encryption (0x17) | High |
| Break-Glass Account Use | PAM audit log | Break-glass credential checkout | Critical |
| MFA Fatigue | PAM auth log | >3 MFA denials in 5 minutes | High |
| Session Hijacking - tscon | Windows Security | tscon.exe execution (Event 4688) | Critical |
| Password Rotation Failure | CPM log | Rotation failed for >24 hours | High |
| Impossible Travel | Sign-in logs | >900 km/h between logins | High |
| Unusual Sudo Usage | Linux syslog | Sudo commands outside baseline | Medium |
