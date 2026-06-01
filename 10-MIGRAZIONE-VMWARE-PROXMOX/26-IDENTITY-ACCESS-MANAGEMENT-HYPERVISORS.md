# Identity and Access Management for Hypervisor Environments

> **Course Module:** VMware → Proxmox VE Migration
> **Path Position:** Phase 9 — Security Hardening · Module 26 (extends Module 12 Security & Compliance)
> **Prerequisites:** Module 12.1 (TLS/certificates), Module 12.2 (LDAP/AD authentication), Module 14 (Automation/IaC); working knowledge of AD/LDAP, SAML 2.0, OIDC, PAM systems, RBAC theory, and audit log analysis.
> **Learning Objectives.** Upon completing this module the reader will be able to:
> 1. Design end-to-end IAM architectures for vSphere and Proxmox VE environments — selecting identity sources, federation protocols, and privilege models appropriate to organizational risk posture;
> 2. Configure vCenter SSO with multiple identity sources, custom roles, object-level permissions, and Trust Authority;
> 3. Implement Proxmox RBAC with path-based ACLs, pool delegation, API token scoping, and multi-factor authentication;
> 4. Integrate LDAP/AD with both platforms including LDAPS, group mapping, nested group resolution, and failover;
> 5. Deploy SAML 2.0 federation for vCenter and OIDC for Proxmox with conditional access and MFA enforcement;
> 6. Apply least-privilege models, separation of duties, JIT access, and break-glass procedures;
> 7. Secure service accounts with rotation, monitoring, certificate-based auth, and API token lifecycle management;
> 8. Configure audit logging, SIEM integration, and detection rules for IAM-related attacks;
> 9. Execute attack scenarios (credential stuffing, token theft, privilege escalation, LDAP injection) and verify detection;
> 10. Build a lab implementing secure IAM with AD integration, TOTP MFA, scoped API tokens, and SIEM forwarding.
> **Estimated Time:** reading 120-150 min · lab 480-600 min (AD setup + federation + attack/detect cycles)
> **Level:** proficient → expert (Dreyfus 4 → 5)
> **Last Updated:** 2026-05-07
> **Reference Versions:** Proxmox VE 8.x; VMware vSphere 8.0 U3; vCenter 8.0; Active Directory 2022/2025; Keycloak 24.x; Azure Entra ID; OpenLDAP 2.6+; FreeIPA 4.12+.

---

## Table of Contents

1. [IAM Architecture for Virtual Infrastructure](#1-iam-architecture-for-virtual-infrastructure)
2. [VMware vSphere IAM](#2-vmware-vsphere-iam)
3. [Proxmox VE IAM](#3-proxmox-ve-iam)
4. [LDAP/AD Integration](#4-ldapad-integration)
5. [SAML/OIDC Federation](#5-samloidc-federation)
6. [Privilege Escalation Prevention](#6-privilege-escalation-prevention)
7. [Service Account Security](#7-service-account-security)
8. [Audit and Monitoring](#8-audit-and-monitoring)
9. [Attack Scenarios and Detection](#9-attack-scenarios-and-detection)
10. [Lab: Implementing Secure IAM](#10-lab-implementing-secure-iam)

---

## 1. IAM Architecture for Virtual Infrastructure

### 1.1 Authentication Flow Overview

Hypervisor management planes present a high-value target: compromise of a single privileged session yields control over every workload hosted on that infrastructure. IAM for virtual environments must therefore satisfy stricter requirements than application-tier IAM:

- **No implicit trust.** Every management session — GUI, API, CLI — must authenticate against a verified identity source.
- **Short-lived credentials.** Token lifetimes measured in hours, not days.
- **Strong binding.** Sessions bound to source IP, client certificate, or hardware attestation where feasible.
- **Auditability.** Every authentication event, privilege change, and administrative action emits a durable log entry forwarded to a centralized SIEM.

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTHENTICATION FLOW                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User/Service ──► [IdP / Auth Source] ──► [Token/Ticket]        │
│       │                                         │               │
│       │          ┌─────────────────────┐        │               │
│       └─────────►│  Management Plane   │◄───────┘               │
│                  │  (vCenter / PVE API) │                        │
│                  └──────────┬──────────┘                        │
│                             │                                   │
│                  ┌──────────▼──────────┐                        │
│                  │  Authorization Engine │                       │
│                  │  (Roles → Privileges) │                       │
│                  └──────────┬──────────┘                        │
│                             │                                   │
│                  ┌──────────▼──────────┐                        │
│                  │  Audit Logger        │                        │
│                  │  (SIEM-forwarded)    │                        │
│                  └─────────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

**vCenter/ESXi authentication flow:**
1. Client connects to vCenter HTTPS (443).
2. vCenter SSO receives credentials (username/password, SAML assertion, or session token).
3. SSO validates against configured identity source (embedded, AD/LDAP, SAML IdP).
4. SSO issues a SAML 2.0 bearer token (HoK or bearer, depending on client type).
5. Client presents token to vCenter API/SDK endpoint.
6. vCenter maps authenticated identity to roles/permissions on inventory objects.
7. Action performed; event logged to `vpxd-*` and `vpxd-profiler-*` logs.

**Proxmox VE authentication flow:**
1. Client connects to PVE API (HTTPS 8006) or `pvesh`/`pveum` CLI.
2. PVE `pveauth` validates credentials against the configured realm (PAM, PVE, AD, LDAP, OpenID Connect).
3. On success, PVE issues a ticket (cookie `PVEAuthCookie`) and a CSRF prevention token.
4. Subsequent API calls carry ticket + CSRF token (or API token for programmatic access).
5. PVE authorization engine evaluates ACLs (path-based) against the authenticated user's effective roles.
6. Action performed; event logged to `/var/log/pveproxy/access.log` and task log.

### 1.2 Identity Sources

| Source Type | vCenter Support | Proxmox Support | Use Case |
|---|---|---|---|
| Local Accounts | ESXi local, SSO `vsphere.local` | `pve` realm | Break-glass, initial setup |
| Active Directory | AD as LDAP identity source in SSO | `ad` realm | Enterprise environments |
| Generic LDAP | LDAP identity source in SSO | `ldap` realm | Non-AD directories (OpenLDAP, FreeIPA) |
| SAML 2.0 | External IdP federation | Not natively supported | SSO with enterprise IdP (ADFS, Okta, Azure) |
| OpenID Connect | Limited (via workarounds) | `openid` realm | Modern IdP (Keycloak, Azure Entra, Google) |
| PAM (Linux) | N/A | `pam` realm | OS-level auth for node access |
| Certificate-Based | ESXi host certs, VMCA | Client certs via reverse proxy | Mutual TLS for service auth |

### 1.3 Centralized vs Federated Identity

**Centralized model:** Single authoritative directory (e.g., AD forest) serves as identity source for all hypervisor management planes. Advantages: unified credential policy, single revocation point, consolidated audit. Disadvantages: single point of failure (mitigated with multi-DC), blast radius of directory compromise.

**Federated model:** Each platform trusts an IdP that federates identity across organizational boundaries. Advantages: cross-organization access (MSP managing customer hypervisors), protocol-level isolation (compromise of federation metadata does not yield directory credentials). Disadvantages: complexity, token lifetime management, IdP availability dependency.

**Recommendation for most enterprises:** Centralized AD as the identity authority, with SAML/OIDC federation as the *access protocol* (not as a separate identity source). This provides the audit simplicity of centralization with the security benefits of token-based access (no passwords crossing management plane boundaries).

### 1.4 Service Account Lifecycle Management

Service accounts for hypervisors fall into categories:

| Category | Examples | Credential Type | Rotation Period |
|---|---|---|---|
| Backup agents | Veeam, PBS service user | Password or API token | 90 days max |
| Monitoring agents | Zabbix, PRTG, Prometheus exporters | API token (read-only) | 180 days |
| Automation | Ansible, Terraform, Packer | API token or cert | 30-90 days |
| Inter-platform | vCenter-to-ESXi, PVE cluster join | Certificate | 1-2 years (auto-renewed) |
| Integration | CMDB sync, ticketing, orchestration | API token | 90 days |

Lifecycle requirements:
1. **Creation** — Documented owner, purpose, minimum privilege set, expiry date.
2. **Provisioning** — Credential stored in vault (HashiCorp Vault, CyberArk, AWS Secrets Manager), never in plaintext config.
3. **Rotation** — Automated via PAM tool or scheduled script. Zero-downtime rotation (create new → validate → retire old).
4. **Monitoring** — Alert on anomalous usage (off-hours, unusual source IP, unexpected privilege escalation).
5. **Decommissioning** — Disable on project end, delete after 30-day grace period, audit trail retained.

### 1.5 API Authentication Methods

**vCenter REST API:**
```bash
# Session-based (cookie)
curl -sk -X POST \
  "https://vcenter.lab.local/api/session" \
  -u "administrator@vsphere.local:P@ssw0rd" \
  -H "Content-Type: application/json"
# Returns: session ID (use as vmware-api-session-id header)

# Token-based with SSO token (SAML)
# Requires obtaining SAML token from STS endpoint first
```

**Proxmox REST API:**
```bash
# Ticket-based authentication
curl -sk -X POST \
  "https://pve.lab.local:8006/api2/json/access/ticket" \
  -d "username=admin@pam&password=SecurePass123"
# Returns: ticket + CSRFPreventionToken

# API Token authentication (no ticket needed, no 2FA prompt)
curl -sk -X GET \
  "https://pve.lab.local:8006/api2/json/nodes" \
  -H "Authorization: PVEAPIToken=automation@pve!monitoring=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

**Security considerations for API auth:**
- API tokens bypass 2FA by design (Proxmox) — scope them tightly.
- vCenter session cookies have configurable timeout (`vpxd.cfg` → `SessionTimeout`); default 30 minutes.
- Rotate API tokens on a schedule even if they have no built-in expiry.
- Log all API authentication events separately from GUI logins for anomaly detection.

---

## 2. VMware vSphere IAM

### 2.1 vCenter Single Sign-On (SSO) Architecture

vCenter SSO is the authentication cornerstone of vSphere. Since vSphere 6.x, SSO is embedded in the vCenter Server Appliance (VCSA) via the Platform Services Controller (PSC) — as of vSphere 7.0+, PSC is always embedded.

**SSO Components:**
- **Security Token Service (STS):** Issues SAML tokens after credential validation.
- **Identity Management Service:** Manages identity sources (directories).
- **Directory Service (vmdir):** Stores the `vsphere.local` domain (internal SSO accounts).
- **Certificate Authority (VMCA):** Issues certificates for ESXi hosts and solution users.

**Authentication sequence:**
```
Client                    vCenter SSO (STS)              Identity Source
  │                            │                              │
  │── POST /sts/STSService ──►│                              │
  │   (username + password)    │                              │
  │                            │── LDAP bind ───────────────►│
  │                            │◄── bind result ─────────────│
  │                            │                              │
  │                            │── validate MFA (if cfg) ──► │
  │                            │                              │
  │◄── SAML Bearer Token ─────│                              │
  │                            │                              │
  │── API call + token ──────►│ vCenter Service              │
  │                            │── validate token ──►STS      │
  │                            │◄── token valid ────          │
  │◄── API response ──────────│                              │
```

**Identity sources configurable in SSO:**
1. `vsphere.local` (embedded vmdir) — always present, contains `administrator@vsphere.local`.
2. Active Directory (Integrated Windows Authentication) — joins vCenter to AD domain.
3. Active Directory as LDAP — LDAP bind without machine account.
4. OpenLDAP — generic LDAP.

**PowerCLI: List identity sources:**
```powershell
Connect-VIServer -Server vcenter.lab.local -User administrator@vsphere.local
Get-IdentitySource | Select-Object Name, Type, DomainName, PrimaryUrl
```

**PowerCLI: Add AD identity source (LDAP mode):**
```powershell
Add-IdentitySource -Name "CORP AD" `
  -Type ActiveDirectory `
  -DomainName "corp.example.com" `
  -DomainAlias "CORP" `
  -PrimaryUrl "ldaps://dc01.corp.example.com:636" `
  -BaseDNUsers "OU=Users,DC=corp,DC=example,DC=com" `
  -BaseDNGroups "OU=Groups,DC=corp,DC=example,DC=com" `
  -Username "svc-vcenter-ldap@corp.example.com" `
  -Password (ConvertTo-SecureString "SvcP@ss!" -AsPlainText -Force) `
  -ServerCertificates (Get-Content ./dc01-cert.pem -Raw)
```

### 2.2 vSphere Roles and Permissions

**Permission model:** vSphere uses a role-based system where permissions are assigned as `(User/Group, Role, Object, Propagate)` tuples.

**Predefined roles:**

| Role | Description | Typical Assignment |
|---|---|---|
| Administrator | Full control over all objects | Emergency/break-glass only |
| Read-Only | View state without modification | Monitoring accounts |
| No Access | Explicitly deny all access | Override inherited permissions |
| Virtual Machine Power User | VM console, power ops, snapshot, media | Helpdesk/L1 operators |
| Network Administrator | Network configuration | Network engineering team |
| Datastore Consumer | Allocate space, browse datastore | VM provisioning automation |
| Resource Pool Administrator | Manage resource pools and child VMs | Department leads |

**Custom role creation (PowerCLI):**
```powershell
# Create a role for backup operators
$backupPrivileges = @(
    "VirtualMachine.State.CreateSnapshot",
    "VirtualMachine.State.RemoveSnapshot",
    "VirtualMachine.State.RenameSnapshot",
    "VirtualMachine.Provisioning.GetVmFiles",
    "VirtualMachine.Provisioning.DiskRandomRead",
    "VirtualMachine.Provisioning.DiskRandomAccess",
    "Datastore.Browse",
    "Datastore.FileManagement",
    "Global.DisableMethods",
    "Global.EnableMethods"
)
New-VIRole -Name "Backup Operator" -Privilege (Get-VIPrivilege -Id $backupPrivileges)
```

**Object-level permissions and propagation:**

Permissions are applied at any inventory level: Datacenter, Cluster, Resource Pool, Host, VM Folder, VM, Network, Datastore. When `Propagate = $true`, the permission applies to the object and all children.

```powershell
# Grant "Backup Operator" role to svc-backup@corp on Datacenter "DC-PROD" with propagation
$dc = Get-Datacenter "DC-PROD"
$principal = "CORP\svc-backup"
New-VIPermission -Entity $dc -Principal $principal -Role "Backup Operator" -Propagate $true
```

**Global permissions vs inventory permissions:**
- **Global permissions:** Apply to the entire vCenter (all objects in all solutions — vCenter, ESXi, vSAN, NSX). Configured via `Administration > Access Control > Global Permissions`.
- **Inventory permissions:** Scoped to specific objects in the inventory tree.
- **Precedence:** More specific permissions override inherited ones. Explicit "No Access" at child overrides inherited "Administrator" from parent.

### 2.3 VMware Identity Manager Integration

VMware Identity Manager (now Workspace ONE Access) provides:
- Conditional access policies (device posture, location, risk score).
- MFA enforcement before vCenter SSO token issuance.
- Self-service password reset for `vsphere.local` users (limited utility in practice).
- Unified application catalog (vCenter alongside other enterprise apps).

Integration flow:
1. Configure Workspace ONE Access as SAML IdP.
2. In vCenter SSO configuration, add external SAML IdP.
3. Map IdP groups to vCenter SSO groups (which then map to roles/permissions).
4. Users redirected to Workspace ONE login → MFA → SAML assertion → vCenter session.

### 2.4 vSphere Trust Authority

vSphere Trust Authority (vTA) introduces hardware attestation to the access model:
- **Trusted hosts** must prove integrity (TPM 2.0 attestation, Secure Boot) before being allowed to decrypt VM encryption keys.
- **Attested hosts** receive access to Key Provider credentials only after Trust Authority validates their boot measurements.
- **Separation of roles:** Trust Authority cluster administrators (who configure attestation policy) are distinct from workload cluster administrators (who run VMs).

This mitigates:
- Rogue hypervisor injection (host added by compromised admin cannot decrypt existing VMs without passing attestation).
- Insider threat (admin cannot exfiltrate encrypted VM data even with hypervisor root access on non-attested host).

```powershell
# PowerCLI: Get Trust Authority cluster state
Get-TrustAuthorityCluster -TrustAuthorityVMHost $taHost | Format-List
Get-TrustAuthorityKeyProvider -TrustAuthorityCluster $cluster
```

---

## 3. Proxmox VE IAM

### 3.1 User/Group/Pool Model

Proxmox uses a hierarchical access control model:

- **Users:** Identified as `username@realm` (e.g., `admin@pam`, `john@ad`).
- **Groups:** Named collections of users for bulk permission assignment.
- **Pools:** Named collections of VMs/containers and storage for delegation boundaries.
- **Tokens:** API-only credentials tied to a user but with independently scoped privileges.

```
┌──────────────────────────────────────────────────────┐
│               PROXMOX IAM MODEL                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  USER ──► belongs to ──► GROUP                       │
│    │                        │                        │
│    │                        │                        │
│    ▼                        ▼                        │
│  ACL (path, role)       ACL (path, role)             │
│                                                      │
│  POOL ──► contains ──► VMs + Storage                 │
│    │                                                 │
│    ▼                                                 │
│  ACL: group gets role on /pool/{poolname}            │
│                                                      │
│  API TOKEN ──► subset of ──► user privileges         │
│  (no 2FA required for token auth)                    │
│                                                      │
└──────────────────────────────────────────────────────┘
```

**Create user, group, pool, assign permissions:**
```bash
# Create a user in the PVE realm
pveum user add deploy-operator@pve --comment "CI/CD deployment operator"
pveum user modify deploy-operator@pve --password "Str0ngP@ss!"

# Create a group
pveum group add vm-operators --comment "VM lifecycle operators"
pveum user modify deploy-operator@pve --group vm-operators

# Create a pool
pveum pool add pool-production --comment "Production workloads"
# Add VMs to pool (via GUI or qm/pct set commands)
qm set 100 --pool pool-production

# Assign role to group on pool path
pveum acl modify /pool/pool-production --roles PVEVMAdmin --groups vm-operators
```

### 3.2 Authentication Realms

Proxmox supports five realm types, each serving different use cases:

**PAM realm (`pam`):**
- Authenticates against Linux PAM (system users in `/etc/passwd`, `/etc/shadow`).
- `root@pam` is the default superuser — always available.
- Use case: break-glass access, node-level administration.

**PVE realm (`pve`):**
- Proxmox-internal user database (stored in `/etc/pve/user.cfg`).
- Passwords hashed and stored in cluster filesystem.
- Use case: small environments without external directory, dedicated service accounts.

**AD realm (`ad`):**
- Connects to Active Directory using LDAP protocol with AD-specific defaults.
- Supports `sAMAccountName` or `userPrincipalName` for login.
- Auto-detects AD schema for group sync (`memberOf` attribute).
- Use case: enterprise environments with existing AD infrastructure.

**LDAP realm (`ldap`):**
- Generic LDAP against any LDAPv3 directory (OpenLDAP, FreeIPA, 389DS).
- Requires explicit configuration of user/group object classes and attributes.
- Use case: non-AD environments, FreeIPA deployments.

**OpenID Connect realm (`openid`):**
- Delegates authentication to an external OIDC provider (Keycloak, Azure Entra, Google).
- Browser-based redirect flow; not usable for CLI/API without token exchange.
- Use case: modern enterprise SSO, MFA-enforced access, Azure-centric environments.

**Realm configuration (CLI examples):**
```bash
# AD realm
pveum realm add CORP --type ad \
  --server1 dc01.corp.example.com \
  --server2 dc02.corp.example.com \
  --port 636 \
  --secure 1 \
  --base-dn "DC=corp,DC=example,DC=com" \
  --bind-dn "CN=svc-proxmox,OU=Service Accounts,DC=corp,DC=example,DC=com" \
  --default 0 \
  --tfa "type=totp" \
  --comment "Corporate Active Directory"

# LDAP realm (OpenLDAP)
pveum realm add OPENLDAP --type ldap \
  --server1 ldap.internal.example.com \
  --port 636 \
  --secure 1 \
  --base-dn "dc=internal,dc=example,dc=com" \
  --user-attr uid \
  --bind-dn "cn=svc-proxmox,ou=services,dc=internal,dc=example,dc=com" \
  --filter "(&(objectClass=posixAccount)(memberOf=cn=pve-users,ou=groups,dc=internal,dc=example,dc=com))" \
  --group-dn "ou=groups,dc=internal,dc=example,dc=com" \
  --group-filter "(objectClass=groupOfNames)" \
  --group-name-attr cn \
  --sync-defaults-options "scope=sub,enable-new=1,full=1"

# OpenID Connect realm (Keycloak)
pveum realm add KEYCLOAK --type openid \
  --issuer-url "https://keycloak.example.com/realms/infrastructure" \
  --client-id "proxmox-ve" \
  --client-key "client-secret-here" \
  --username-claim "preferred_username" \
  --scopes "openid profile email groups" \
  --autocreate 1 \
  --comment "Keycloak OIDC"
```

### 3.3 RBAC: Roles, Privileges, ACLs, Path-Based Permissions

**Privileges** are atomic operations (e.g., `VM.PowerMgmt`, `VM.Snapshot`, `Datastore.Allocate`).

**Roles** are named sets of privileges. Predefined roles:

| Role | Key Privileges | Use Case |
|---|---|---|
| `Administrator` | All privileges | Break-glass only |
| `PVEAdmin` | All except hardware modification and system | General admin |
| `PVEVMAdmin` | VM lifecycle (create, delete, migrate, snapshot, console) | VM operators |
| `PVEVMUser` | VM console, power, USB | End users with VM access |
| `PVEDatastoreAdmin` | Storage management and allocation | Storage team |
| `PVEDatastoreUser` | Storage allocation only (no management) | Provisioning |
| `PVEPoolAdmin` | Pool management | Multi-tenant delegation |
| `PVEPoolUser` | Use pool resources | Tenant users |
| `PVEAuditor` | Read-only access everywhere | Security/compliance |
| `PVESDNAdmin` | SDN zone/vnet management | Network team |
| `NoAccess` | No privileges | Explicit deny |

**Custom role creation:**
```bash
# Create backup-operator role with minimum privileges
pveum role add BackupOperator --privs "VM.Backup,VM.Snapshot,VM.Snapshot.Rollback,VM.Audit,Datastore.AllocateSpace,Datastore.Audit"

# Create network-viewer role
pveum role add NetworkViewer --privs "SDN.Audit,Sys.Audit"
```

**ACL structure:**

ACLs in Proxmox follow the pattern: `path, user/group/@token, role, propagate`

Paths correspond to the object hierarchy:
```
/                          → root (entire cluster)
/nodes/{node}              → specific node
/vms/{vmid}                → specific VM/container
/pool/{poolname}           → resource pool
/storage/{storageid}       → storage
/sdn/zones/{zone}          → SDN zone
/access/groups             → group management
```

**ACL examples:**
```bash
# Group "vm-operators" gets PVEVMAdmin on all VMs in pool "production"
pveum acl modify /pool/production --roles PVEVMAdmin --groups vm-operators --propagate 1

# User john@ad gets PVEAuditor on the entire cluster
pveum acl modify / --roles PVEAuditor --users john@ad --propagate 1

# Token gets read-only access to specific node
pveum acl modify /nodes/pve01 --roles PVEAuditor --tokens 'monitoring@pve!zabbix' --propagate 1

# Deny access to specific VM (override inherited permissions)
pveum acl modify /vms/200 --roles NoAccess --users intern@ad --propagate 0
```

### 3.4 API Tokens

API tokens are the preferred authentication method for automation and monitoring against Proxmox. They provide:

- **No 2FA bypass needed:** Tokens authenticate directly without TOTP/WebAuthn prompts.
- **Privilege separation:** Tokens can have fewer privileges than their parent user.
- **Independent revocation:** Revoking a token does not affect the user's other sessions.
- **Audit trail:** Token usage is logged separately, identifiable by token ID.

**Token structure:** `<user>@<realm>!<tokenid>=<secret-uuid>`

```bash
# Create API token for automation user
pveum user token add automation@pve ci-deploy --privsep 1 --expire 0 --comment "CI/CD pipeline token"
# Output: full-tokenid = automation@pve!ci-deploy, value = xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# Create token with privilege separation DISABLED (inherits all user privs - DANGEROUS)
pveum user token add admin@pam emergency-token --privsep 0 --expire 1735689600

# List tokens for a user
pveum user token list automation@pve

# Remove token
pveum user token remove automation@pve ci-deploy
```

**Privilege separation (`--privsep`):**
- `privsep=1` (default, RECOMMENDED): Token starts with NO privileges; you must explicitly assign ACLs to the token.
- `privsep=0` (DANGEROUS): Token inherits all privileges of the parent user. Use only for break-glass scenarios.

```bash
# Assign specific ACL to a privilege-separated token
pveum acl modify /pool/ci-vms --roles PVEVMAdmin --tokens 'automation@pve!ci-deploy'
pveum acl modify /storage/local-lvm --roles PVEDatastoreUser --tokens 'automation@pve!ci-deploy'
```

### 3.5 Two-Factor Authentication

Proxmox supports three 2FA methods:

**TOTP (Time-based One-Time Password):**
```bash
# Enable TOTP requirement for a realm
pveum realm modify CORP --tfa "type=totp,step=30,digits=6"

# User self-enrolls via GUI: Datacenter > Permissions > Two Factor > Add > TOTP
# Or via API:
curl -sk -X PUT "https://pve:8006/api2/json/access/tfa/john@CORP" \
  -H "Authorization: PVEAPIToken=admin@pam!mgmt=xxx" \
  -d "type=totp&description=YubiKey_TOTP&secret=BASE32SECRET"
```

**YubiKey (Yubico OTP):**
```bash
# Configure YubiKey validation server
pveum realm modify CORP --tfa "type=yubico,id=YOUR_CLIENT_ID,key=YOUR_API_KEY,url=https://api.yubico.com/wsapi/2.0/verify"
```

**WebAuthn (FIDO2):**
```bash
# Configure WebAuthn (requires valid TLS certificate)
pveum realm modify CORP --tfa "type=webauthn"
# WebAuthn RP configuration in /etc/pve/datacenter.cfg:
# webauthn: rp=pve.example.com,origin=https://pve.example.com:8006,id=pve.example.com
```

**Critical note:** API tokens bypass 2FA entirely. This is by design (automation cannot enter TOTP codes). Mitigate by:
1. Always using `privsep=1` for tokens.
2. Assigning minimum-necessary ACLs to tokens.
3. Monitoring token usage for anomalies.
4. Rotating tokens on a schedule.

### 3.6 Pool-Based Delegation for Multi-Tenancy

Pools enable multi-tenant delegation without granting node-level access:

```bash
# Create tenant pools
pveum pool add tenant-alpha --comment "Alpha Corp tenant"
pveum pool add tenant-beta --comment "Beta Inc tenant"

# Create tenant admin groups
pveum group add alpha-admins --comment "Alpha Corp administrators"
pveum group add beta-admins --comment "Beta Inc administrators"

# Assign roles — each tenant admin only sees/manages their own pool
pveum acl modify /pool/tenant-alpha --roles PVEPoolAdmin,PVEVMAdmin --groups alpha-admins
pveum acl modify /pool/tenant-beta --roles PVEPoolAdmin,PVEVMAdmin --groups beta-admins

# Tenant admins CANNOT see other tenant's VMs, storage, or configurations
# Verify isolation:
pveum user permissions alpha-admin@ad --path /pool/tenant-beta
# Should return: no permissions
```

---

## 4. LDAP/AD Integration

### 4.1 Configuring ESXi/vCenter for AD Authentication

**ESXi direct AD join (for standalone hosts):**
```bash
# Via ESXi Shell
esxcli system account add -i svc-esxi-ad -p 'P@ssw0rd!' -c 'P@ssw0rd!' -d "AD join account"
# Better: join via Host Client or vCenter management

# Via vSphere Client: Host > Configure > Authentication Services > Join Domain
```

**vCenter AD configuration (as LDAP identity source):**

In vCenter 8.0, navigate to: Administration > Single Sign-On > Configuration > Identity Providers > Add.

Key parameters:
- **Domain name:** `corp.example.com`
- **Domain alias:** `CORP`
- **Primary Server URL:** `ldaps://dc01.corp.example.com:636`
- **Failover Server URL:** `ldaps://dc02.corp.example.com:636`
- **Base DN (users):** `DC=corp,DC=example,DC=com`
- **Base DN (groups):** `DC=corp,DC=example,DC=com`
- **Bind user:** `CN=svc-vcenter,OU=Service Accounts,DC=corp,DC=example,DC=com`
- **Server certificates:** Upload DC's CA certificate chain (PEM format)

**PowerCLI full script:**
```powershell
$ssoAdminConn = Connect-SsoAdminServer -Server vcenter.lab.local `
  -User administrator@vsphere.local -Password 'AdminP@ss!'

# Get current identity sources
Get-IdentitySource -Server $ssoAdminConn

# Add AD with LDAPS
$caCert = Get-Content "C:\certs\corp-ca-chain.pem" -Raw
Add-IdentitySource -Server $ssoAdminConn `
  -Name "CORP" `
  -Type ActiveDirectoryLDAP `
  -DomainName "corp.example.com" `
  -DomainAlias "CORP" `
  -PrimaryUrl "ldaps://dc01.corp.example.com:636" `
  -FailoverUrl "ldaps://dc02.corp.example.com:636" `
  -BaseDNUsers "OU=Users,DC=corp,DC=example,DC=com" `
  -BaseDNGroups "OU=Groups,DC=corp,DC=example,DC=com" `
  -Username "svc-vcenter@corp.example.com" `
  -Password (ConvertTo-SecureString 'SvcLdapP@ss!' -AsPlainText -Force) `
  -ServerCertificates $caCert

# Set as default identity source
Set-IdentitySource -IdentitySource "CORP" -Server $ssoAdminConn -Default

# Map AD group to vCenter Administrators
$adminGroup = Get-SsoGroup -Name "vcenter-admins" -Domain "corp.example.com"
$ssoAdminsGroup = Get-SsoGroup -Name "Administrators" -Domain "vsphere.local"
Add-GroupMember -Group $ssoAdminsGroup -Member $adminGroup
```

### 4.2 Proxmox LDAP Realm Configuration

**Full AD realm with group sync:**
```bash
# Create the realm
pveum realm add CORP --type ad \
  --server1 dc01.corp.example.com \
  --server2 dc02.corp.example.com \
  --port 636 \
  --secure 1 \
  --base-dn "DC=corp,DC=example,DC=com" \
  --bind-dn "CN=svc-proxmox,OU=Service Accounts,DC=corp,DC=example,DC=com" \
  --comment "Corporate AD" \
  --default 0 \
  --filter "(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:=CN=pve-users,OU=Groups,DC=corp,DC=example,DC=com))" \
  --group-classes "group" \
  --group-dn "OU=Proxmox Groups,DC=corp,DC=example,DC=com" \
  --group-filter "(objectClass=group)" \
  --group-name-attr cn \
  --sync-defaults-options "scope=sub,enable-new=1,full=1,purge=1"

# Set the bind password (prompted interactively or via stdin)
pveum realm set CORP --password "LdapB1ndP@ss!"

# Verify connectivity
pveum realm sync CORP --dry-run 1

# Execute sync
pveum realm sync CORP

# Schedule automatic sync (cron-style in /etc/pve/jobs.cfg)
# Or via GUI: Datacenter > Permissions > Realms > CORP > Sync Jobs
```

**Important filter explanation:**
- The OID `1.2.840.113556.1.4.1941` is the LDAP_MATCHING_RULE_IN_CHAIN (AD-specific) — it resolves nested group membership recursively.
- Without this, users in nested groups (e.g., `pve-users` ← `department-IT` ← `john`) would not be found.

### 4.3 Group-Based Role Mapping

After sync, map AD groups to Proxmox roles:

```bash
# Sync brings in groups as Proxmox groups (prefixed or not depending on config)
# Map groups to ACLs:

# Infrastructure admins get full cluster access
pveum acl modify / --roles PVEAdmin --groups CORP-infra-admins --propagate 1

# VM operators get VM management on production pool
pveum acl modify /pool/production --roles PVEVMAdmin --groups CORP-vm-operators --propagate 1

# Network team gets SDN access
pveum acl modify /sdn --roles PVESDNAdmin --groups CORP-network-team --propagate 1

# Monitoring team gets read-only everywhere
pveum acl modify / --roles PVEAuditor --groups CORP-monitoring --propagate 1

# Storage team
pveum acl modify /storage --roles PVEDatastoreAdmin --groups CORP-storage-team --propagate 1
```

### 4.4 Nested Group Resolution Issues

**Problem:** Standard LDAP `memberOf` queries only return direct group membership. Users in nested groups are invisible.

**Solutions by platform:**

| Platform | Solution | Configuration |
|---|---|---|
| vCenter SSO | Uses AD GC (port 3268/3269) + token groups | Automatic when AD identity source configured |
| Proxmox (AD realm) | LDAP_MATCHING_RULE_IN_CHAIN filter | Use OID `1.2.840.113556.1.4.1941` in filter |
| Proxmox (LDAP realm) | Not natively supported for non-AD | Use `memberOf` overlay in OpenLDAP or flatten groups |

**Proxmox nested group filter (AD):**
```bash
# Filter that resolves nested membership
--filter "(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:=CN=pve-allowed,OU=Groups,DC=corp,DC=example,DC=com))"
```

**OpenLDAP workaround (memberOf overlay):**
```ldif
# Enable memberOf overlay in OpenLDAP (slapd.d)
dn: olcOverlay=memberof,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcMemberOf
olcOverlay: memberof
olcMemberOfRefInt: TRUE
olcMemberOfDangling: ignore
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf

# Also add refint overlay for referential integrity
dn: olcOverlay=refint,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
olcOverlay: refint
olcRefintAttribute: member memberOf
```

### 4.5 LDAPS/StartTLS Configuration

**Certificate validation is NON-NEGOTIABLE in production.** Never set `verify=0` or `verify_cert=false`.

**Proxmox LDAPS setup:**
```bash
# Import CA certificate into Proxmox trust store
cp corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt
update-ca-certificates

# Alternatively, specify cert directly in realm config
pveum realm modify CORP --capath /etc/pve/priv/corp-ca.pem

# Test LDAPS connectivity
openssl s_client -connect dc01.corp.example.com:636 -CAfile /etc/pve/priv/corp-ca.pem </dev/null 2>/dev/null | openssl x509 -noout -dates -subject
```

**StartTLS (port 389 with upgrade to TLS):**
```bash
# StartTLS is supported via --secure 1 --port 389 combination
# However, LDAPS (port 636) is preferred because:
# 1. StartTLS can be stripped by MITM (downgrade attack)
# 2. Some firewalls mishandle StartTLS negotiation
# 3. LDAPS establishes TLS before any LDAP traffic

pveum realm modify CORP --port 389 --secure 1
# This enables StartTLS. BUT prefer:
pveum realm modify CORP --port 636 --secure 1
# This uses LDAPS (TLS wrapping from connection start)
```

### 4.6 Service Account Security for LDAP Bind

The bind account is the weakest link in LDAP integration. If compromised, the attacker can:
1. Enumerate all users and groups in the directory.
2. Potentially modify directory objects (if over-privileged).
3. Perform offline password attacks against LDAP responses.

**Hardening requirements:**
```
Active Directory — Service Account for Proxmox LDAP Bind:
- Account: CN=svc-proxmox,OU=Service Accounts,DC=corp,DC=example,DC=com
- Password: 25+ chars, randomly generated, rotated every 90 days
- Group membership: NONE (no Domain Admins, no admin groups)
- Delegated permissions (minimal):
  - Read access to user objects (for authentication lookup)
  - Read access to group objects (for group sync)
  - NO write permissions anywhere
  - NO replication permissions (prevents DCSync attack if compromised)
- Account options:
  - "Cannot change password" = false (allow rotation)
  - "Password never expires" = false (enforce rotation)
  - "Account is sensitive and cannot be delegated" = true
  - "This account supports Kerberos AES 256 bit encryption" = true
- Logon restrictions:
  - "Log on to" = restrict to Proxmox node IPs only (if feasible)
  - Logon hours = 24x7 (needed for auth)
- Protected Users group: Yes (prevents NTLM, enforces Kerberos)
```

**PowerShell to configure AD service account:**
```powershell
# Create dedicated OU
New-ADOrganizationalUnit -Name "Service Accounts" -Path "DC=corp,DC=example,DC=com"

# Create service account
$svcPw = ConvertTo-SecureString (New-Guid).Guid.Replace('-','') + '!Aa1' -AsPlainText -Force
New-ADUser -Name "svc-proxmox" `
  -Path "OU=Service Accounts,DC=corp,DC=example,DC=com" `
  -AccountPassword $svcPw `
  -PasswordNeverExpires $false `
  -CannotChangePassword $false `
  -Enabled $true `
  -Description "Proxmox VE LDAP bind account - DO NOT ADD TO PRIVILEGED GROUPS"

# Set "Account is sensitive and cannot be delegated"
Set-ADUser "svc-proxmox" -AccountNotDelegated $true

# Add to Protected Users group (prevents NTLM, forces Kerberos AES)
Add-ADGroupMember -Identity "Protected Users" -Members "svc-proxmox"

# Delegate read-only permissions (DSACLS or AD delegation wizard)
# Minimum: Read userAccountControl, sAMAccountName, memberOf, displayName, mail
```

### 4.7 AD Sites and Subnets for DC Selection

When multiple domain controllers exist across sites, ensure Proxmox connects to the nearest DC:

```bash
# Option 1: Explicit server list (preferred for Proxmox)
pveum realm modify CORP --server1 dc01.local-site.corp.example.com --server2 dc02.local-site.corp.example.com

# Option 2: SRV record-based (Proxmox AD realm can use DNS SRV)
# Proxmox resolves _ldap._tcp.corp.example.com by default if no server specified
# Ensure DNS returns site-appropriate DCs (AD Sites & Services configured correctly)

# Verify SRV records from Proxmox node
dig +short _ldap._tcp.Default-First-Site-Name._sites.corp.example.com SRV
```

### 4.8 Fallback Authentication When LDAP Unavailable

**Scenario:** AD is down (network partition, DC failure, credential compromise requiring emergency lockout of AD integration).

**Mitigation strategy:**
```bash
# 1. ALWAYS maintain a local break-glass account
pveum user add breakglass@pve --comment "Emergency access when AD unavailable"
pveum user modify breakglass@pve --password "VeryStr0ngBreakGl@ssP@ss!"
pveum acl modify / --roles Administrator --users breakglass@pve

# 2. Document the break-glass procedure:
#    a. Connect to any cluster node via SSH as root (pam realm)
#    b. Or use breakglass@pve via web UI (if PVE realm still functional)
#    c. All break-glass usage MUST be logged and reviewed

# 3. Store break-glass credentials in:
#    - Physical safe (printed, sealed envelope)
#    - Offline password manager (KeePassXC on air-gapped USB)
#    - NOT in the same AD/vault that might be unavailable

# 4. root@pam is always available via local console/SSH
#    Ensure SSH key or password is securely stored offline
```

---

## 5. SAML/OIDC Federation

### 5.1 SAML 2.0 for vCenter SSO

vCenter natively supports SAML 2.0 as an external identity provider for SSO.

**IdP Configuration (ADFS example):**

1. In ADFS Management, add a Relying Party Trust:
   - Identifier: `https://vcenter.lab.local/websso/SAML2/Metadata`
   - Assertion consumer URL: `https://vcenter.lab.local/websso/SAML2/SSO/vsphere.local`
   
2. Configure claim rules:
```
Rule 1: Send LDAP Attributes as Claims
  - LDAP attribute: SAM-Account-Name → outgoing: Name ID
  - LDAP attribute: Token-Groups (Unqualified Names) → outgoing: Group
  - LDAP attribute: E-Mail-Addresses → outgoing: E-Mail Address
  - LDAP attribute: Given-Name → outgoing: Given Name
  - LDAP attribute: Surname → outgoing: Surname

Rule 2: Transform Name ID
  - Incoming: Name ID (Unspecified)
  - Outgoing: Name ID (Email or Persistent, per vCenter requirements)
```

3. Export IdP metadata XML from ADFS.
4. In vCenter: Administration > SSO > Configuration > Identity Provider > Change Identity Provider > SAML.
5. Upload ADFS metadata XML.
6. Map SAML groups to vCenter roles.

**Attribute mapping for vCenter SSO:**

| SAML Attribute | vCenter Field | Required |
|---|---|---|
| `NameID` | User principal name | Yes |
| `Groups` or custom attribute | Group membership for role mapping | Yes |
| `email` | Email address | Optional |
| `firstName` | First name | Optional |
| `lastName` | Last name | Optional |

**Assertion signing requirements:**
- Assertions MUST be signed (SHA-256 minimum).
- Enable assertion encryption for defense-in-depth (encrypts attribute values in transit).
- Validate assertion lifetime (MaxSessionAge / NotOnOrAfter). Recommended: 5-15 minutes for assertion, 8 hours for session.

**Keycloak as SAML IdP for vCenter:**
```json
// Keycloak client configuration (SAML)
{
  "clientId": "https://vcenter.lab.local/websso/SAML2/Metadata",
  "protocol": "saml",
  "frontchannelLogout": true,
  "attributes": {
    "saml.assertion.signature": "true",
    "saml.server.signature": "true",
    "saml.signature.algorithm": "RSA_SHA256",
    "saml.force.post.binding": "true",
    "saml_assertion_consumer_url_post": "https://vcenter.lab.local/websso/SAML2/SSO/vsphere.local",
    "saml_single_logout_service_url_post": "https://vcenter.lab.local/websso/SAML2/SLO/vsphere.local"
  }
}
```

### 5.2 OIDC for Proxmox

Proxmox VE supports OpenID Connect natively since version 6.2.

**Keycloak OIDC configuration:**

1. Create a client in Keycloak:
```json
{
  "clientId": "proxmox-ve",
  "protocol": "openid-connect",
  "publicClient": false,
  "standardFlowEnabled": true,
  "directAccessGrantsEnabled": false,
  "rootUrl": "https://pve.example.com:8006",
  "validRedirectUris": ["https://pve.example.com:8006/*"],
  "attributes": {
    "pkce.code.challenge.method": "S256"
  }
}
```

2. Create a client scope for group claims:
```json
{
  "name": "groups",
  "protocol": "openid-connect",
  "protocolMappers": [{
    "name": "groups",
    "protocol": "openid-connect",
    "protocolMapper": "oidc-group-membership-mapper",
    "config": {
      "full.path": "false",
      "claim.name": "groups",
      "id.token.claim": "true",
      "access.token.claim": "true",
      "userinfo.token.claim": "true"
    }
  }]
}
```

3. Configure Proxmox realm:
```bash
pveum realm add KEYCLOAK --type openid \
  --issuer-url "https://keycloak.example.com/realms/infrastructure" \
  --client-id "proxmox-ve" \
  --client-key "YOUR_CLIENT_SECRET_HERE" \
  --username-claim "preferred_username" \
  --scopes "openid profile email groups" \
  --autocreate 1 \
  --default 0 \
  --comment "Keycloak OIDC Federation"
```

**Azure Entra ID (formerly Azure AD) OIDC:**
```bash
# App Registration in Azure:
# - Redirect URI: https://pve.example.com:8006 (Web type)
# - API Permissions: openid, profile, email
# - Token configuration: Add "groups" claim (Security groups)

pveum realm add AZURE --type openid \
  --issuer-url "https://login.microsoftonline.com/TENANT_ID/v2.0" \
  --client-id "APPLICATION_CLIENT_ID" \
  --client-key "CLIENT_SECRET_VALUE" \
  --username-claim "preferred_username" \
  --scopes "openid profile email" \
  --autocreate 1 \
  --comment "Azure Entra ID"
```

### 5.3 Conditional Access Policies

Conditional access adds context-aware enforcement to hypervisor access:

**Azure Entra Conditional Access policy for Proxmox:**
- **Assignment:** Include group "Hypervisor-Admins"
- **Cloud apps:** Target the Proxmox app registration
- **Conditions:**
  - Device platforms: Windows, macOS (block mobile/unknown)
  - Locations: Named locations only (office IPs, VPN egress)
  - Client apps: Browser only (block legacy auth)
  - Sign-in risk: Block high-risk sign-ins
- **Grant:** Require MFA + compliant device + approved app

**Keycloak equivalent (Authentication Flow customization):**
```
Browser Flow → Custom:
  ├── Cookie (check existing session)
  ├── IP Allowlist Condition (custom authenticator)
  │     → Reject if source IP not in infrastructure-mgmt subnet
  ├── Username/Password Form
  ├── OTP Form (TOTP/WebAuthn)
  └── Script Authenticator: deny if user not in "hypervisor-access" group
```

### 5.4 MFA Enforcement Through Federation

When using OIDC/SAML federation, MFA is enforced at the IdP level — Proxmox/vCenter never sees the raw password; they only receive the assertion/token after MFA has been completed.

**Advantages:**
- Centralized MFA policy (single pane for all apps, not per-hypervisor config).
- Support for advanced MFA methods (push notifications, hardware FIDO2 keys, biometrics).
- Risk-based MFA (step-up authentication for sensitive operations).
- MFA fatigue monitoring at IdP level.

**Proxmox-side verification that MFA was performed:**
- Check token claims for `amr` (Authentication Methods References) claim.
- Keycloak maps MFA completion to `amr: ["mfa"]` in the ID token.
- Currently Proxmox does not enforce `amr` claim validation — defense relies on IdP policy enforcement.

### 5.5 Session Management and Token Lifetime

| Parameter | vCenter Default | Proxmox Default | Recommended |
|---|---|---|---|
| Session timeout (inactivity) | 30 min | 2 hours | 15-30 min |
| Maximum session duration | 10 hours | No max | 8 hours |
| API token lifetime | Cookie-based (session) | Indefinite (until revoked) | 90-day rotation |
| SAML assertion validity | 5 min | N/A | 5 min |
| OIDC ID token lifetime | N/A | Per IdP (1 hour typical) | 1 hour, refresh via refresh_token |

**Proxmox session timeout configuration:**
```bash
# Set ticket lifetime in /etc/pve/datacenter.cfg
# max_age: maximum ticket lifetime in seconds (default: 7200 = 2 hours)
# Edit via GUI or directly:
echo "ticket: max_age=3600" >> /etc/pve/datacenter.cfg
# Note: Changes require pveproxy restart to take effect
systemctl restart pveproxy
```

**vCenter session timeout (vpxd config):**
```xml
<!-- /etc/vmware-vpx/vpxd.cfg -->
<vpxd>
  <httpClientSessionTimeout>1800</httpClientSessionTimeout>
  <!-- 1800 seconds = 30 minutes -->
</vpxd>
```

---

## 6. Privilege Escalation Prevention

### 6.1 Principle of Least Privilege — Role Mapping

Map job functions to minimum required hypervisor permissions:

| Job Role | vCenter Role | Proxmox Role | Scope |
|---|---|---|---|
| L1 Help Desk | Virtual Machine Power User (custom: no snapshot delete) | PVEVMUser | Specific VM folders/pools |
| VM Administrator | VM Admin (custom) | PVEVMAdmin | Department pools |
| Network Engineer | Network Administrator | PVESDNAdmin | Network objects only |
| Storage Engineer | Datastore Administrator (custom) | PVEDatastoreAdmin | Storage objects only |
| Backup Operator | Custom (snapshot + disk read) | BackupOperator (custom) | All VMs read-only + snapshot |
| Security Auditor | Read-Only | PVEAuditor | Entire cluster |
| Platform Admin | Administrator (time-limited) | PVEAdmin (time-limited) | Cluster-wide |
| Break-Glass | Administrator | Administrator | Cluster-wide (emergency only) |

**Implementation principle:** Start with NoAccess/zero permissions; add only what the role demonstrably needs. Document each permission grant with a business justification.

### 6.2 Separation of Duties

No single administrator should have the combination of privileges that enables:
- Creating a VM + assigning it network access + disabling firewall rules.
- Managing storage + accessing backup data + restoring VMs to unauthorized locations.
- Modifying IAM configuration + creating their own elevated access.

**Separation model:**

```bash
# In Proxmox, enforce separation through non-overlapping ACLs:

# VM Admin cannot manage networking
pveum acl modify /sdn --roles NoAccess --groups CORP-vm-admins

# Network Admin cannot manage VMs
pveum acl modify /vms --roles NoAccess --groups CORP-network-team

# Storage Admin cannot access VM consoles
# (No direct block needed — PVEDatastoreAdmin doesn't include VM.Console)

# IAM Admin (can manage users/permissions) cannot directly manage VMs
pveum role add IAMAdmin --privs "User.Modify,Group.Allocate,Realm.Allocate,Realm.AllocateUser,Permissions.Modify,Sys.Audit"
pveum acl modify /access --roles IAMAdmin --users iam-admin@ad
pveum acl modify /vms --roles NoAccess --users iam-admin@ad
pveum acl modify /storage --roles NoAccess --users iam-admin@ad
```

### 6.3 Just-In-Time Access

**Azure PIM (Privileged Identity Management) for vCenter:**

Azure PIM enables time-bounded elevation for vCenter administrator roles:
1. AD group `vcenter-admins-eligible` is configured as PIM-eligible.
2. User requests activation via Azure portal (provides justification, selects duration 1-8 hours).
3. Approval workflow triggers (peer admin or manager approval).
4. Upon approval, user is added to `vcenter-admins-active` group (which maps to vCenter Administrator role).
5. After time expires, membership is automatically revoked.

**Manual JIT workflow for Proxmox (when no PIM tool available):**
```bash
#!/usr/bin/env bash
# jit-elevate.sh — Grant temporary admin access with audit trail
# Usage: ./jit-elevate.sh <username@realm> <hours> <justification>

set -euo pipefail

USER="$1"
HOURS="${2:-4}"
JUSTIFICATION="$3"
EXPIRY_EPOCH=$(date -d "+${HOURS} hours" +%s)
EXPIRY_HUMAN=$(date -d "+${HOURS} hours" --iso-8601=seconds)
REQUEST_ID=$(uuidgen)

# Log the elevation request
logger -t jit-access "REQUEST_ID=${REQUEST_ID} USER=${USER} HOURS=${HOURS} JUSTIFICATION='${JUSTIFICATION}' EXPIRY=${EXPIRY_HUMAN}"

# Grant elevated access
pveum acl modify / --roles PVEAdmin --users "${USER}" --propagate 1
echo "GRANTED: ${USER} elevated to PVEAdmin until ${EXPIRY_HUMAN} (REQUEST_ID: ${REQUEST_ID})"

# Schedule revocation
at "now + ${HOURS} hours" <<EOF
pveum acl delete / --roles PVEAdmin --users "${USER}"
logger -t jit-access "REVOKED: REQUEST_ID=${REQUEST_ID} USER=${USER} PVEAdmin revoked (auto-expiry)"
EOF

echo "Revocation scheduled for ${EXPIRY_HUMAN}"
```

### 6.4 Privileged Access Workstations (PAW)

Hypervisor management MUST only be performed from dedicated Privileged Access Workstations:

**PAW requirements:**
- Dedicated hardware (not a general-purpose workstation with management VM).
- Hardened OS image (minimal software, no email, no web browsing except management UIs).
- Outbound network restricted to management plane IPs only.
- MFA for OS login (smart card or FIDO2).
- Monitored: all keystrokes, screen captures (for privileged session recording), and network traffic logged.
- Separate admin credentials (Tier 0/1) that NEVER authenticate on standard workstations.

**Network enforcement:**
```
# Firewall rules: Only PAW VLAN can reach management interfaces
# PAW VLAN: 10.99.0.0/24
# vCenter: 10.10.0.5
# Proxmox nodes: 10.10.0.10-10.10.0.15

# iptables on Proxmox (or via SDN firewall rules):
-A INPUT -p tcp --dport 8006 -s 10.99.0.0/24 -j ACCEPT
-A INPUT -p tcp --dport 8006 -j DROP
-A INPUT -p tcp --dport 22 -s 10.99.0.0/24 -j ACCEPT
-A INPUT -p tcp --dport 22 -j DROP
```

### 6.5 Break-Glass Procedures

**Requirements:**
1. Documented procedure stored offline (printed, sealed, in a physical safe).
2. Dedicated account (`breakglass@pve`, `administrator@vsphere.local`) with credentials stored outside normal secret management.
3. Alerts fire immediately when break-glass account authenticates.
4. All actions during break-glass session are recorded (screen recording + command history + audit log).
5. Post-incident review within 24 hours of any break-glass usage.

**Detection rule for break-glass usage:**
```yaml
# SIEM rule (Sigma format)
title: Break-Glass Account Used
status: production
level: critical
logsource:
  product: proxmox
  service: authentication
detection:
  selection:
    user:
      - "breakglass@pve"
      - "root@pam"
      - "administrator@vsphere.local"
    event_type: "login_success"
  condition: selection
falsepositives:
  - Legitimate emergency access (must be documented within 24h)
tags:
  - attack.initial_access
  - attack.t1078
```

---

## 7. Service Account Security

### 7.1 Service Account Inventory and Ownership

Every service account must have:

```
┌──────────────────────────────────────────────────────────────┐
│               SERVICE ACCOUNT REGISTRY                        │
├──────────────┬───────────────────────────────────────────────┤
│ Account ID   │ svc-backup-veeam@ad                           │
│ Purpose      │ Veeam backup agent for VM snapshot + data read│
│ Owner        │ Backup Team Lead (jane.doe@corp.example.com)  │
│ Created      │ 2025-03-15                                    │
│ Last Rotated │ 2026-02-28                                    │
│ Next Rotation│ 2026-05-29                                    │
│ Permissions  │ VM.Backup, VM.Snapshot, Datastore.Browse (all)│
│ Auth Method  │ API token (privsep=1)                         │
│ Source IPs   │ 10.10.5.20 (Veeam server)                    │
│ Monitoring   │ Alert if used from other IP or off-hours      │
│ Review Date  │ Quarterly (next: 2026-07-01)                  │
│ Justification│ TICKET-4521: Veeam deployment for PVE cluster │
└──────────────┴───────────────────────────────────────────────┘
```

**Inventory script (Proxmox):**
```bash
#!/usr/bin/env bash
# inventory-service-accounts.sh — List all service accounts and their permissions
echo "=== Service Accounts (non-interactive users) ==="
pveum user list --output-format json | jq -r '.[] | select(.comment | test("(?i)svc|service|automation|backup|monitor")) | "\(.userid)\t\(.comment)\t\(.enable)\t\(.expire)"'

echo ""
echo "=== API Tokens ==="
for user in $(pveum user list --output-format json | jq -r '.[].userid'); do
  tokens=$(pveum user token list "$user" --output-format json 2>/dev/null)
  if [ "$tokens" != "[]" ] && [ -n "$tokens" ]; then
    echo "User: $user"
    echo "$tokens" | jq -r '.[] | "  Token: \(.tokenid)\tPrivsep: \(.privsep)\tExpire: \(.expire)\tComment: \(.comment)"'
  fi
done

echo ""
echo "=== ACLs for Service Accounts ==="
pveum acl list --output-format json | jq -r '.[] | select(.ugid | test("(?i)svc|automation|backup|monitor")) | "\(.path)\t\(.ugid)\t\(.roleid)\t\(.propagate)"'
```

### 7.2 Credential Rotation

**Automated rotation script (Proxmox API tokens):**
```bash
#!/usr/bin/env bash
# rotate-api-token.sh — Zero-downtime API token rotation
# Usage: ./rotate-api-token.sh <user@realm> <tokenid> <config-file-to-update>
set -euo pipefail

USER="$1"
TOKENID="$2"
CONFIG_FILE="$3"
BACKUP_FILE="${CONFIG_FILE}.bak.$(date +%s)"

echo "[$(date -Iseconds)] Starting token rotation for ${USER}!${TOKENID}"

# Step 1: Generate new token (old one still valid)
NEW_TOKEN_OUTPUT=$(pveum user token add "${USER}" "${TOKENID}-new" --privsep 1 --output-format json)
NEW_TOKEN_SECRET=$(echo "$NEW_TOKEN_OUTPUT" | jq -r '.value')
NEW_TOKEN_FULL="${USER}!${TOKENID}-new"

echo "[$(date -Iseconds)] New token created: ${NEW_TOKEN_FULL}"

# Step 2: Copy ACLs from old token to new token
OLD_ACLS=$(pveum acl list --output-format json | jq -r ".[] | select(.ugid == \"${USER}!${TOKENID}\") | \"\(.path) \(.roleid) \(.propagate)\"")
while IFS=' ' read -r path role propagate; do
  [ -z "$path" ] && continue
  pveum acl modify "$path" --roles "$role" --tokens "${NEW_TOKEN_FULL}" --propagate "$propagate"
  echo "[$(date -Iseconds)] ACL copied: ${path} ${role}"
done <<< "$OLD_ACLS"

# Step 3: Update configuration file with new token
cp "$CONFIG_FILE" "$BACKUP_FILE"
sed -i "s|${USER}!${TOKENID}=[^ ]*|${NEW_TOKEN_FULL}=${NEW_TOKEN_SECRET}|g" "$CONFIG_FILE"
echo "[$(date -Iseconds)] Config updated: ${CONFIG_FILE}"

# Step 4: Validate new token works
HTTP_CODE=$(curl -sk -o /dev/null -w "%{http_code}" \
  -H "Authorization: PVEAPIToken=${NEW_TOKEN_FULL}=${NEW_TOKEN_SECRET}" \
  "https://localhost:8006/api2/json/version")

if [ "$HTTP_CODE" = "200" ]; then
  echo "[$(date -Iseconds)] Validation OK (HTTP ${HTTP_CODE}). Removing old token."
  # Step 5: Remove old token
  pveum user token remove "${USER}" "${TOKENID}"
  # Step 6: Rename new token (by creating final + removing -new)
  # Note: Proxmox doesn't support token rename. Accept the new name or plan accordingly.
  echo "[$(date -Iseconds)] Rotation complete. New token ID: ${NEW_TOKEN_FULL}"
else
  echo "[$(date -Iseconds)] VALIDATION FAILED (HTTP ${HTTP_CODE}). Rolling back."
  cp "$BACKUP_FILE" "$CONFIG_FILE"
  pveum user token remove "${USER}" "${TOKENID}-new"
  exit 1
fi

logger -t token-rotation "SUCCESS: ${USER}!${TOKENID} rotated to ${NEW_TOKEN_FULL}"
```

### 7.3 Removing Unnecessary Service Accounts

**Audit script — find unused accounts:**
```bash
#!/usr/bin/env bash
# find-stale-accounts.sh — Identify accounts with no recent login
STALE_DAYS=90
CUTOFF=$(date -d "-${STALE_DAYS} days" +%s)

echo "=== Accounts with no login in ${STALE_DAYS} days ==="
echo "Checking auth.log and pveproxy access.log..."

# Get all non-root users
ALL_USERS=$(pveum user list --output-format json | jq -r '.[].userid' | grep -v '^root@pam$')

for user in $ALL_USERS; do
  # Check last successful auth in journal
  LAST_AUTH=$(journalctl -u pvedaemon -u pveproxy --since "${STALE_DAYS} days ago" 2>/dev/null | grep -c "successful auth for user '${user}'" || true)
  if [ "$LAST_AUTH" -eq 0 ]; then
    CREATED=$(pveum user list --output-format json | jq -r ".[] | select(.userid==\"${user}\") | .comment")
    echo "  STALE: ${user} (${CREATED:-no comment}) — 0 logins in ${STALE_DAYS} days"
  fi
done
```

### 7.4 Monitoring Service Account Usage

**Key indicators of service account compromise:**
- Authentication from unexpected source IPs.
- Usage outside normal hours (for accounts tied to business-hours automation).
- Privilege escalation (account attempting actions beyond its role).
- Excessive failed authentication attempts.
- Sudden spike in API calls (credential stuffing or data exfiltration).

**Detection query (Elasticsearch/OpenSearch):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event.category": "authentication" } },
        { "term": { "event.outcome": "success" } },
        { "wildcard": { "user.name": "svc-*" } }
      ],
      "must_not": [
        { "terms": { "source.ip": ["10.10.5.20", "10.10.5.21", "10.10.5.22"] } }
      ]
    }
  }
}
```

### 7.5 Machine Identity — Certificate-Based Service Auth

For inter-node communication and high-security automation, certificate-based authentication provides stronger guarantees than passwords or API tokens:

**Proxmox cluster certificates:**
- Each node has a certificate signed by the cluster CA (`/etc/pve/pve-root-ca.pem`).
- Inter-node communication (corosync, pmxcfs) uses mutual TLS.
- Custom solution: reverse proxy with client cert authentication before Proxmox API.

**mTLS for API access (via reverse proxy):**
```nginx
# nginx reverse proxy enforcing client certificates for API access
server {
    listen 8443 ssl;
    server_name pve-api.example.com;

    ssl_certificate     /etc/nginx/certs/server.crt;
    ssl_certificate_key /etc/nginx/certs/server.key;
    ssl_client_certificate /etc/nginx/certs/client-ca.crt;
    ssl_verify_client on;
    ssl_verify_depth 2;

    # Map client cert CN to Proxmox API token
    map $ssl_client_s_dn_cn $pve_token {
        "svc-backup"      "backup@pve!agent=TOKEN_SECRET_HERE";
        "svc-monitoring"  "monitoring@pve!zabbix=TOKEN_SECRET_HERE";
        default           "";
    }

    location /api2/ {
        if ($pve_token = "") {
            return 403;
        }
        proxy_pass https://127.0.0.1:8006;
        proxy_set_header Authorization "PVEAPIToken=$pve_token";
        proxy_ssl_verify off;  # Internal connection to localhost
    }
}
```

### 7.6 API Token Security — Scoping, Rotation, Monitoring

**Token security checklist:**

| Control | Implementation |
|---|---|
| Privilege separation | Always `privsep=1`; assign explicit ACLs |
| Minimum scope | Grant access to specific paths only (not `/`) |
| Expiration | Set `--expire` to epoch timestamp (rotate before expiry) |
| Source IP restriction | Firewall rules limiting API port access to known IPs |
| Monitoring | Alert on token usage from unexpected IPs |
| Rotation schedule | Automated rotation every 90 days maximum |
| Secret storage | Vault/secret manager, never in Git or plaintext configs |
| Revocation readiness | Document which systems use each token for rapid revocation |

---

## 8. Audit and Monitoring

### 8.1 vCenter Event Log Analysis

**Key events to monitor:**

| Event ID | Description | Severity | MITRE Technique |
|---|---|---|---|
| `vim.event.UserLoginSessionEvent` | Successful login | Info | T1078 |
| `vim.event.UserLogoutSessionEvent` | Session end | Info | — |
| `vim.event.EventEx` (com.vmware.sso.LoginFailure) | Failed login | Warning | T1110 |
| `vim.event.PermissionAddedEvent` | Permission granted | High | T1098 |
| `vim.event.PermissionRemovedEvent` | Permission revoked | Medium | — |
| `vim.event.RoleAddedEvent` | Custom role created | Medium | T1098 |
| `vim.event.AccountCreatedEvent` | Account created | High | T1136 |
| `vim.event.VmPoweredOnEvent` + unusual user | VM started by unexpected user | High | T1059 |

**PowerCLI: Query authentication events:**
```powershell
# Get all login events in the last 24 hours
$start = (Get-Date).AddHours(-24)
Get-VIEvent -Start $start -MaxSamples 10000 | Where-Object {
    $_.GetType().Name -match "UserLoginSession|BadUsernameSessionEvent"
} | Select-Object CreatedTime, UserName, @{N='IP';E={$_.IpAddress}}, 
    @{N='Type';E={$_.GetType().Name}}, FullFormattedMessage |
    Sort-Object CreatedTime -Descending |
    Export-Csv "C:\audit\vcenter-logins-$(Get-Date -Format 'yyyyMMdd').csv"

# Get permission changes
Get-VIEvent -Start $start -MaxSamples 10000 | Where-Object {
    $_.GetType().Name -match "Permission|RoleAdded|RoleRemoved|AccountCreated"
} | ForEach-Object {
    [PSCustomObject]@{
        Time = $_.CreatedTime
        User = $_.UserName
        Type = $_.GetType().Name
        Message = $_.FullFormattedMessage
    }
} | Export-Csv "C:\audit\vcenter-permission-changes-$(Get-Date -Format 'yyyyMMdd').csv"
```

### 8.2 Proxmox Audit Log

Proxmox maintains several log sources:

| Log | Location | Content |
|---|---|---|
| Auth log | `/var/log/pveproxy/access.log` | All API access with auth details |
| Task log | `/var/log/pve/tasks/` | All task executions (VM operations, backups) |
| Syslog | `/var/log/syslog` | System-level auth via PAM |
| Journal | `journalctl -u pvedaemon -u pveproxy` | Service-level auth events |
| Audit trail | `/var/log/pve/pvedaemon.log` | Daemon operations |
| Firewall log | `/var/log/pve-firewall.log` | Firewall rule matches |

**Parse authentication events:**
```bash
#!/usr/bin/env bash
# parse-pve-auth.sh — Extract authentication events from Proxmox logs
# Usage: ./parse-pve-auth.sh [hours-back]

HOURS="${1:-24}"
SINCE=$(date -d "-${HOURS} hours" '+%Y-%m-%d %H:%M')

echo "=== Authentication Events (last ${HOURS} hours) ==="

# Successful authentications
echo "--- Successful Logins ---"
journalctl -u pvedaemon --since "$SINCE" 2>/dev/null | \
  grep "successful auth for user" | \
  awk '{print $1, $2, $3, $NF}' | \
  sort | uniq -c | sort -rn

# Failed authentications
echo ""
echo "--- Failed Logins ---"
journalctl -u pvedaemon --since "$SINCE" 2>/dev/null | \
  grep -i "authentication failure\|auth failed\|login failed" | \
  awk '{print $1, $2, $3, $NF}' | \
  sort | uniq -c | sort -rn

# API token usage
echo ""
echo "--- API Token Access ---"
if [ -f /var/log/pveproxy/access.log ]; then
  grep "PVEAPIToken" /var/log/pveproxy/access.log | \
    awk -v since="$SINCE" '$0 > since {print $1, $4, $6, $7}' | \
    sort | uniq -c | sort -rn | head -20
fi

# Permission changes
echo ""
echo "--- Permission/ACL Changes ---"
journalctl -u pvedaemon --since "$SINCE" 2>/dev/null | \
  grep -i "acl\|permission\|role\|user.*add\|user.*remove\|token" | \
  tail -50
```

### 8.3 SIEM Integration

**Proxmox → rsyslog → SIEM (Splunk/Elastic/Wazuh):**

```bash
# /etc/rsyslog.d/50-pve-siem.conf
# Forward PVE auth events to SIEM

# Template for structured syslog (RFC 5424)
template(name="PVESIEMFormat" type="string"
  string="<%PRI%>1 %TIMESTAMP:::date-rfc3339% %HOSTNAME% proxmox-auth - - - %msg%\n")

# Forward auth-related messages
if ($programname == 'pvedaemon' or $programname == 'pveproxy') and
   ($msg contains 'auth' or $msg contains 'login' or $msg contains 'permission'
    or $msg contains 'token' or $msg contains 'acl') then {
    action(type="omfwd"
           target="siem.example.com"
           port="514"
           protocol="tcp"
           template="PVESIEMFormat"
           queue.type="LinkedList"
           queue.filename="pve_siem_fwd"
           queue.maxDiskSpace="100m"
           queue.saveOnShutdown="on"
           action.resumeRetryCount="-1")
}
```

**Filebeat configuration for Proxmox logs:**
```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    id: pve-access
    paths:
      - /var/log/pveproxy/access.log
    fields:
      log_type: pve_access
    fields_under_root: true
    multiline.pattern: '^[0-9]{1,3}\.'
    multiline.negate: true
    multiline.match: after

  - type: journald
    id: pve-auth
    include_matches:
      - _SYSTEMD_UNIT=pvedaemon.service
      - _SYSTEMD_UNIT=pveproxy.service
    fields:
      log_type: pve_auth
    fields_under_root: true

output.elasticsearch:
  hosts: ["https://elastic.example.com:9200"]
  index: "proxmox-security-%{+yyyy.MM.dd}"
  ssl:
    certificate_authorities: ["/etc/filebeat/ca.pem"]
    certificate: "/etc/filebeat/filebeat.crt"
    key: "/etc/filebeat/filebeat.key"

processors:
  - dissect:
      tokenizer: '%{source_ip} - %{user} [%{timestamp}] "%{method} %{uri} %{protocol}" %{status} %{bytes}'
      field: "message"
      target_prefix: "pve"
      when:
        equals:
          log_type: "pve_access"
```

**PowerCLI: Forward vCenter events to syslog:**
```powershell
# Configure vCenter syslog forwarding (in addition to built-in logging)
# vCenter > Configure > Advanced Settings
Get-AdvancedSetting -Entity $vcenter -Name "vpxd.event.syslog.enabled" |
  Set-AdvancedSetting -Value "true" -Confirm:$false

# For ESXi host syslog
Get-VMHost | ForEach-Object {
    $_ | Get-AdvancedSetting -Name "Syslog.global.logHost" |
      Set-AdvancedSetting -Value "tcp://siem.example.com:514" -Confirm:$false
}
```

### 8.4 Detecting Suspicious Access Patterns

**Brute force detection (Sigma rule):**
```yaml
title: Brute Force Against Proxmox Web UI
status: production
level: high
logsource:
  product: proxmox
  service: authentication
detection:
  selection:
    event_type: "auth_failure"
  timeframe: 5m
  condition: selection | count(source_ip) by target_user > 5
falsepositives:
  - Misconfigured monitoring agent
tags:
  - attack.credential_access
  - attack.t1110.001
```

**Impossible travel detection (Elasticsearch query):**
```json
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event.outcome": "success" } },
        { "term": { "event.category": "authentication" } },
        { "range": { "@timestamp": { "gte": "now-1h" } } }
      ]
    }
  },
  "aggs": {
    "by_user": {
      "terms": { "field": "user.name" },
      "aggs": {
        "unique_geos": {
          "cardinality": { "field": "source.geo.country_iso_code" }
        },
        "filter_impossible": {
          "bucket_selector": {
            "buckets_path": { "geo_count": "unique_geos" },
            "script": "params.geo_count > 1"
          }
        }
      }
    }
  }
}
```

**Privilege escalation detection:**
```yaml
title: Privilege Escalation in Proxmox
status: production
level: critical
logsource:
  product: proxmox
  service: system
detection:
  selection_acl_change:
    message|contains:
      - "acl modify"
      - "role add"
      - "user token add"
  selection_target:
    message|contains:
      - "Administrator"
      - "PVEAdmin"
      - "privsep=0"
  condition: selection_acl_change and selection_target
falsepositives:
  - Legitimate administrative changes (must correlate with change ticket)
tags:
  - attack.privilege_escalation
  - attack.t1098
```

### 8.5 Access Review Procedures

**Quarterly access certification workflow:**

```bash
#!/usr/bin/env bash
# quarterly-access-review.sh — Generate access review report
# Run quarterly; output goes to security team for review

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_FILE="/var/reports/access-review-${REPORT_DATE}.txt"

{
echo "============================================"
echo "  QUARTERLY ACCESS REVIEW — ${REPORT_DATE}"
echo "============================================"
echo ""

echo "=== 1. All Users with Administrative Roles ==="
pveum acl list --output-format json | jq -r '.[] | select(.roleid | test("Admin|Administrator")) | "\(.ugid)\t\(.roleid)\t\(.path)"'

echo ""
echo "=== 2. Users with Cluster-Wide Access (path=/) ==="
pveum acl list --output-format json | jq -r '.[] | select(.path == "/") | "\(.ugid)\t\(.roleid)\t\(.propagate)"'

echo ""
echo "=== 3. API Tokens with privsep=0 (DANGEROUS) ==="
for user in $(pveum user list --output-format json | jq -r '.[].userid'); do
  pveum user token list "$user" --output-format json 2>/dev/null | \
    jq -r ".[] | select(.privsep == 0) | \"DANGER: ${user}!\(.tokenid) privsep=0\""
done

echo ""
echo "=== 4. Accounts with No Login in 90 Days ==="
# (call find-stale-accounts.sh logic here)

echo ""
echo "=== 5. Service Accounts Without Expiry ==="
pveum user list --output-format json | jq -r '.[] | select(.expire == 0 and (.comment // "" | test("(?i)svc|service|auto"))) | "\(.userid)\t\(.comment)\tNO EXPIRY SET"'

echo ""
echo "=== 6. Groups and Membership ==="
pveum group list --output-format json | jq -r '.[].groupid' | while read -r group; do
  members=$(pveum group members "$group" --output-format json 2>/dev/null | jq -r '.[].userid' | tr '\n' ', ')
  echo "  ${group}: ${members}"
done

echo ""
echo "=== REVIEW ACTIONS REQUIRED ==="
echo "1. Validate each admin-level assignment has current business justification"
echo "2. Remove stale accounts (no login > 90 days)"
echo "3. Rotate tokens older than 90 days"
echo "4. Verify service account ownership is current"
echo "5. Sign off: Security Lead + IT Director"

} | tee "$REPORT_FILE"

echo ""
echo "Report saved to: ${REPORT_FILE}"
```

---

## 9. Attack Scenarios and Detection

### 9.1 Credential Stuffing Against vCenter/Proxmox Web UI

**Attack description:** Attacker uses leaked credential databases (from breaches of unrelated services) to attempt logins against hypervisor management interfaces.

**Attack execution:**
```bash
# Attacker's perspective (for understanding — use only in authorized testing)
# Tool: Hydra against Proxmox API
hydra -L users.txt -P passwords.txt -s 8006 pve.target.com https-post-form \
  "/api2/json/access/ticket:username=^USER^@pam&password=^PASS^:F=authentication failure"

# Tool: Custom script against vCenter
# POST https://vcenter.target.com/api/session with different creds
```

**Detection:**
```yaml
# Sigma rule
title: Credential Stuffing Against Hypervisor Management
status: production
level: high
logsource:
  product: proxmox
  service: authentication
detection:
  selection:
    event_type: "auth_failure"
  timeframe: 10m
  condition: selection | count() by source_ip > 10
  # 10+ failures from single IP in 10 minutes
tags:
  - attack.credential_access
  - attack.t1110.004
```

**Mitigation:**
```bash
# Proxmox: Configure fail2ban for PVE
# /etc/fail2ban/jail.d/proxmox.conf
cat <<'EOF' > /etc/fail2ban/jail.d/proxmox.conf
[proxmox]
enabled = true
port = https,8006
filter = proxmox
backend = systemd
maxretry = 3
findtime = 600
bantime = 3600
action = iptables-multiport[name=proxmox, port=https,8006]
EOF

# /etc/fail2ban/filter.d/proxmox.conf
cat <<'EOF' > /etc/fail2ban/filter.d/proxmox.conf
[Definition]
failregex = pvedaemon\[.*authentication failure; rhost=<HOST> user=.* msg=.*
ignoreregex =
journalmatch = _SYSTEMD_UNIT=pvedaemon.service
EOF

systemctl restart fail2ban
```

### 9.2 LDAP Injection Against Hypervisor Auth

**Attack description:** If hypervisor login forms or APIs pass user input directly into LDAP filters without sanitization, attackers can inject LDAP metacharacters to bypass authentication or extract information.

**Vulnerable pattern (conceptual):**
```
# If Proxmox built filter like:
(&(sAMAccountName=USER_INPUT)(objectClass=user))
# And user submits: admin)(objectClass=*))(|(cn=
# Result: (&(sAMAccountName=admin)(objectClass=*))(|(cn=)(objectClass=user))
# This could return results even without valid password in some configurations
```

**Reality check:** Modern Proxmox VE (8.x) and vCenter properly sanitize LDAP filter inputs. This attack is more relevant to:
- Custom authentication scripts that query LDAP directly.
- Older/unpatched versions.
- Custom API wrappers that construct LDAP queries from user input.

**Detection:**
```yaml
title: LDAP Injection Attempt Against Hypervisor
status: production
level: medium
logsource:
  product: proxmox
  service: authentication
detection:
  selection:
    user.name|contains:
      - ")(objectClass="
      - ")(|(cn="
      - "*)(uid="
      - "\\00"
      - "\\2a"
  condition: selection
tags:
  - attack.credential_access
  - attack.t1556
```

### 9.3 Token Theft and Replay

**Attack description:** Attacker intercepts or extracts a valid PVE ticket (cookie) or API token and replays it to gain authenticated access.

**Attack vectors:**
1. XSS on a management-adjacent web application that can read `PVEAuthCookie`.
2. Log file exposure containing API tokens.
3. Memory dump of a management workstation (tokens in browser memory).
4. Network interception (only if TLS is misconfigured or downgraded).
5. Compromised automation server with stored API tokens.

**Detection:**
```bash
# Detect token usage from multiple IPs simultaneously
# Elasticsearch query:
cat <<'EOF'
{
  "query": {
    "bool": {
      "must": [
        { "term": { "event.category": "authentication" } },
        { "term": { "event.outcome": "success" } },
        { "wildcard": { "http.request.header.Authorization": "PVEAPIToken*" } },
        { "range": { "@timestamp": { "gte": "now-5m" } } }
      ]
    }
  },
  "aggs": {
    "by_token": {
      "terms": { "field": "user.name" },
      "aggs": {
        "unique_ips": { "cardinality": { "field": "source.ip" } },
        "filter_multi_ip": {
          "bucket_selector": {
            "buckets_path": { "ip_count": "unique_ips" },
            "script": "params.ip_count > 1"
          }
        }
      }
    }
  }
}
EOF
```

**Mitigation:**
- Bind sessions to source IP where feasible (PVE tickets are IP-bound by default).
- Set short ticket lifetimes.
- Monitor for concurrent sessions from different IPs.
- Use API tokens (harder to intercept than cookies, but require proper storage).

### 9.4 Session Hijacking of Management Interfaces

**Attack description:** Attacker compromises an active management session through:
- Cookie theft via XSS (if management interface has XSS vulnerability).
- Browser extension malware on admin workstation.
- Session prediction (weak randomness — unlikely in modern implementations).
- Man-in-the-browser attacks on compromised admin workstations.

**Detection (SIEM correlation rule):**
```yaml
title: Session Hijacking Indicator - IP Change Mid-Session
status: production
level: critical
logsource:
  product: proxmox
  service: access
detection:
  # Same session ticket used from different IP within short window
  selection:
    event.category: "session"
  condition: selection | near(source.ip != source.ip, timeframe=60s, by=session.id)
tags:
  - attack.credential_access
  - attack.t1539
```

### 9.5 Exploiting Overprivileged Service Accounts

**Attack description:** Attacker compromises a service account (via exposed credentials, compromised automation server, or lateral movement) and leverages its excessive permissions.

**Common overprivilege scenarios:**

| Scenario | Risk | Exploitation |
|---|---|---|
| Monitoring account with VM.PowerMgmt | Can shut down production VMs | DoS via mass power-off |
| Backup account with VM.Config.* | Can modify VM configs | Inject malicious devices, change boot order |
| Automation token with privsep=0 | Full user privileges | Complete cluster takeover |
| Service account in Domain Admins | AD compromise | DCSync, Golden Ticket |

**Detection — service account anomaly:**
```json
{
  "rule": {
    "name": "Service Account Performing Unusual Actions",
    "query": {
      "bool": {
        "must": [
          { "wildcard": { "user.name": "svc-*" } },
          { "terms": { "event.action": [
            "vm.power.off", "vm.destroy", "acl.modify",
            "user.add", "token.add", "node.shutdown"
          ]}}
        ]
      }
    },
    "severity": "critical",
    "response": "Immediately disable the service account and investigate the source system"
  }
}
```

### 9.6 Pass-the-Hash/Ticket for vCenter Access Through AD

**Attack description:** If vCenter uses AD authentication (Integrated Windows Authentication or LDAP bind), an attacker with NTLM hashes or Kerberos tickets from an AD compromise can authenticate to vCenter without knowing the plaintext password.

**Attack chain:**
1. Attacker compromises a workstation (phishing, exploit).
2. Dumps NTLM hashes or Kerberos tickets (Mimikatz, Rubeus).
3. Uses Pass-the-Hash (PtH) to authenticate LDAP bind to vCenter SSO.
4. Or uses Kerberos ticket (Pass-the-Ticket) if vCenter uses IWA.
5. Gains access with the privileges of the compromised account.

**If the compromised account is a vCenter admin → full infrastructure compromise.**

**Detection:**
```yaml
title: Pass-the-Hash Indicators for vCenter Authentication
status: production
level: critical
logsource:
  product: windows
  service: security
detection:
  selection_logon:
    EventID: 4624
    LogonType: 3  # Network
    AuthenticationPackageName: "NTLM"
    TargetServerName|contains: "vcenter"
  filter_legitimate:
    IpAddress|cidr:
      - "10.99.0.0/24"  # PAW subnet
  condition: selection_logon and not filter_legitimate
tags:
  - attack.lateral_movement
  - attack.t1550.002
```

```yaml
title: Kerberos Ticket Abuse for vCenter
status: production
level: critical
logsource:
  product: windows
  service: security
detection:
  selection:
    EventID: 4769  # Kerberos service ticket request
    ServiceName|contains: "vcenter"
    TicketEncryptionType: "0x17"  # RC4 = often indicates pass-the-ticket
  condition: selection
tags:
  - attack.credential_access
  - attack.t1558.003
```

**Mitigation:**
- Enforce AES-only Kerberos (disable RC4/DES in AD policy).
- Place vCenter service accounts in "Protected Users" group (no NTLM, no delegation, no credential caching).
- Implement Credential Guard on all admin workstations.
- Monitor for Event 4769 with RC4 encryption targeting vCenter SPNs.
- Consider vSphere Trust Authority to add hardware attestation layer independent of AD trust.

### 9.7 Detection Rules Summary

| Attack | Primary Detection | MITRE Technique | Log Source |
|---|---|---|---|
| Credential stuffing | >10 failures/IP/10min | T1110.004 | pvedaemon journal |
| LDAP injection | Metacharacters in username | T1556 | pvedaemon journal |
| Token replay | Same token, different IP | T1539 | pveproxy access.log |
| Session hijacking | IP change mid-session | T1539 | pveproxy access.log |
| Service account abuse | Unusual actions from svc-* | T1078.001 | pvedaemon journal + task log |
| Pass-the-Hash | NTLM auth to vCenter from non-PAW | T1550.002 | Windows Security Event Log |
| Pass-the-Ticket | RC4 Kerberos ticket for vCenter SPN | T1558.003 | Windows Security Event Log |
| Privilege escalation | Admin role assigned outside change window | T1098 | pvedaemon journal |

---

## 10. Lab: Implementing Secure IAM

### 10.1 Lab Objectives

Build a production-representative IAM implementation with:
1. Proxmox VE cluster (3 nodes) with AD integration.
2. TOTP MFA enforced for all AD users.
3. RBAC model with least-privilege roles and pool-based delegation.
4. Scoped API tokens for automation.
5. Audit logging forwarded to SIEM.
6. Attack testing and detection verification.

### 10.2 Prerequisites

- Proxmox VE 8.x cluster (3 nodes, functional).
- Windows Server 2022 AD domain controller (pre-configured domain: `lab.internal`).
- SIEM instance (Wazuh, Elastic Security, or Splunk — this lab uses Wazuh).
- Attacker workstation (Kali Linux or ParrotOS) for authorized testing.
- Network connectivity between all systems.

### 10.3 Step 1: AD Integration

```bash
# 1.1 — Import AD CA certificate
scp admin@dc01.lab.internal:/certs/lab-ca.crt /tmp/lab-ca.crt
cp /tmp/lab-ca.crt /usr/local/share/ca-certificates/lab-internal-ca.crt
update-ca-certificates

# 1.2 — Verify LDAPS connectivity
openssl s_client -connect dc01.lab.internal:636 -CAfile /usr/local/share/ca-certificates/lab-internal-ca.crt </dev/null 2>/dev/null | head -5

# 1.3 — Create AD realm
pveum realm add LAB --type ad \
  --server1 dc01.lab.internal \
  --port 636 \
  --secure 1 \
  --base-dn "DC=lab,DC=internal" \
  --bind-dn "CN=svc-proxmox,OU=Service Accounts,DC=lab,DC=internal" \
  --default 0 \
  --comment "Lab AD Domain" \
  --group-dn "OU=Proxmox Groups,DC=lab,DC=internal" \
  --group-filter "(objectClass=group)" \
  --group-name-attr cn \
  --filter "(&(objectClass=user)(memberOf:1.2.840.113556.1.4.1941:=CN=pve-users,OU=Proxmox Groups,DC=lab,DC=internal))" \
  --sync-defaults-options "scope=sub,enable-new=1,full=1"

# 1.4 — Set bind password
pveum realm set LAB --password "LabSvcP@ss2026!"

# 1.5 — Test sync (dry run first)
pveum realm sync LAB --dry-run 1
# Verify expected users/groups appear

# 1.6 — Execute sync
pveum realm sync LAB
pveum user list | grep "@LAB"
```

### 10.4 Step 2: TOTP MFA Configuration

```bash
# 2.1 — Enable TOTP for the LAB realm
pveum realm modify LAB --tfa "type=totp,step=30,digits=6"

# 2.2 — Verify WebAuthn is configured as alternative (optional)
# In /etc/pve/datacenter.cfg, ensure webauthn section exists:
grep -q "^webauthn:" /etc/pve/datacenter.cfg || \
  echo "webauthn: rp=pve.lab.internal,origin=https://pve.lab.internal:8006,id=pve.lab.internal" >> /etc/pve/datacenter.cfg

# 2.3 — Users must enroll TOTP on first login via GUI
# Datacenter > Permissions > Two Factor > Add > TOTP
# Scan QR code with authenticator app (FreeOTP, Aegis, etc.)

# 2.4 — Verify MFA enforcement (API test — should fail without TFA for ticket-based auth)
curl -sk -X POST "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=testuser@LAB&password=TestP@ss123"
# Expected: 401 or prompt for TFA code

# With TOTP:
curl -sk -X POST "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=testuser@LAB&password=TestP@ss123&otp=123456"
```

### 10.5 Step 3: RBAC Model Implementation

```bash
# 3.1 — Create custom roles
pveum role add BackupOperator --privs "VM.Backup,VM.Snapshot,VM.Snapshot.Rollback,VM.Audit,Datastore.AllocateSpace,Datastore.Audit,Sys.Audit"
pveum role add VMOperator --privs "VM.PowerMgmt,VM.Console,VM.Monitor,VM.Audit,VM.Snapshot,VM.Snapshot.Rollback"
pveum role add NetworkViewer --privs "SDN.Audit,Sys.Audit"
pveum role add SecurityAuditor --privs "Sys.Audit,VM.Audit,Datastore.Audit,SDN.Audit,Pool.Audit,User.Modify"

# 3.2 — Create resource pools
pveum pool add pool-production --comment "Production workloads"
pveum pool add pool-staging --comment "Staging/test environment"
pveum pool add pool-dmz --comment "DMZ-facing services"

# 3.3 — Map AD groups to roles on specific paths
# Infrastructure admins — full admin but NOT cluster-wide; scoped to specific pools
pveum acl modify /pool/pool-production --roles PVEVMAdmin --groups LAB-infra-admins --propagate 1
pveum acl modify /pool/pool-staging --roles PVEAdmin --groups LAB-infra-admins --propagate 1

# VM operators — power/console only on production
pveum acl modify /pool/pool-production --roles VMOperator --groups LAB-vm-operators --propagate 1

# Backup team — backup-specific role cluster-wide
pveum acl modify / --roles BackupOperator --groups LAB-backup-team --propagate 1

# Security team — audit everywhere
pveum acl modify / --roles SecurityAuditor --groups LAB-security-team --propagate 1

# 3.4 — Verify effective permissions
pveum user permissions testuser@LAB
pveum user permissions backup-svc@LAB --path /vms/100
```

### 10.6 Step 4: API Token Scoping

```bash
# 4.1 — Create automation user
pveum user add automation@pve --comment "CI/CD automation account"

# 4.2 — Create scoped tokens
# Token for VM provisioning (can create/destroy VMs in staging only)
pveum user token add automation@pve ci-staging --privsep 1 --comment "CI pipeline - staging deploys"
pveum acl modify /pool/pool-staging --roles PVEVMAdmin --tokens 'automation@pve!ci-staging'

# Token for monitoring (read-only everywhere)
pveum user token add automation@pve monitoring --privsep 1 --comment "Monitoring system read-only"
pveum acl modify / --roles PVEAuditor --tokens 'automation@pve!monitoring' --propagate 1

# Token for backup execution
pveum user token add automation@pve backup-agent --privsep 1 --comment "Backup agent snapshots"
pveum acl modify / --roles BackupOperator --tokens 'automation@pve!backup-agent' --propagate 1

# 4.3 — Verify token permissions
# This should succeed (staging pool):
curl -sk -H "Authorization: PVEAPIToken=automation@pve!ci-staging=TOKEN_SECRET" \
  "https://pve.lab.internal:8006/api2/json/pools/pool-staging"

# This should fail (production pool — no access):
curl -sk -H "Authorization: PVEAPIToken=automation@pve!ci-staging=TOKEN_SECRET" \
  "https://pve.lab.internal:8006/api2/json/pools/pool-production"
# Expected: 403 Forbidden

# 4.4 — Document tokens in registry
cat <<'EOF' > /etc/pve/notes/token-registry.txt
# API Token Registry — Last Updated: 2026-05-07
# Token                          | Purpose              | Scope            | Owner    | Rotation
# automation@pve!ci-staging      | CI/CD deployments    | pool-staging     | DevOps   | 90 days
# automation@pve!monitoring      | Metrics collection   | / (read-only)    | SRE      | 180 days
# automation@pve!backup-agent    | Backup snapshots     | / (BackupOp)     | Backup   | 90 days
EOF
```

### 10.7 Step 5: Audit Logging and SIEM Forwarding

```bash
# 5.1 — Configure rsyslog forwarding
cat <<'EOF' > /etc/rsyslog.d/60-pve-to-wazuh.conf
# Forward Proxmox auth and system events to Wazuh manager
template(name="WazuhFormat" type="string"
  string="<%PRI%>1 %TIMESTAMP:::date-rfc3339% %HOSTNAME% %PROGRAMNAME% %PROCID% - - %msg%\n")

if ($programname == 'pvedaemon' or $programname == 'pveproxy' or
    $programname == 'pvestatd' or $programname == 'spiceproxy') then {
    action(type="omfwd"
           target="wazuh-mgr.lab.internal"
           port="1514"
           protocol="tcp"
           template="WazuhFormat"
           queue.type="LinkedList"
           queue.filename="wazuh_fwd"
           queue.maxDiskSpace="200m"
           queue.saveOnShutdown="on"
           action.resumeRetryCount="-1")
}
EOF
systemctl restart rsyslog

# 5.2 — Install Wazuh agent on Proxmox nodes
wget -qO - https://packages.wazuh.com/key/GPG-KEY-WAZUH | gpg --dearmor -o /usr/share/keyrings/wazuh.gpg
echo "deb [signed-by=/usr/share/keyrings/wazuh.gpg] https://packages.wazuh.com/4.x/apt stable main" > /etc/apt/sources.list.d/wazuh.list
apt-get update && apt-get install -y wazuh-agent
# Configure /var/ossec/etc/ossec.conf with manager IP

# 5.3 — Add local log monitoring rules for Wazuh
cat <<'EOF' > /var/ossec/etc/rules/local_rules.xml
<group name="proxmox,authentication">
  <rule id="100100" level="5">
    <decoded_as>pvedaemon</decoded_as>
    <match>authentication failure</match>
    <description>Proxmox authentication failure</description>
  </rule>

  <rule id="100101" level="10" frequency="5" timeframe="120">
    <if_matched_sid>100100</if_matched_sid>
    <same_source_ip />
    <description>Proxmox brute force detected (5+ failures in 2 min)</description>
  </rule>

  <rule id="100102" level="12">
    <decoded_as>pvedaemon</decoded_as>
    <match>acl modify|role add|user token add</match>
    <match>Administrator|PVEAdmin|privsep=0</match>
    <description>Proxmox privilege escalation detected</description>
  </rule>

  <rule id="100103" level="14">
    <decoded_as>pvedaemon</decoded_as>
    <match>successful auth for user</match>
    <match>breakglass@pve|root@pam</match>
    <description>Break-glass account used - immediate review required</description>
  </rule>
</group>
EOF
systemctl restart wazuh-agent

# 5.4 — Verify log forwarding
logger -t pvedaemon "TEST: authentication failure; rhost=192.168.1.100 user=testuser@LAB msg=invalid credentials"
# Check Wazuh dashboard for alert
```

### 10.8 Step 6: Attack Scenario Testing

**IMPORTANT:** Only execute these tests against lab infrastructure you own and control. Document authorization scope before testing.

```bash
# ===== TEST 1: Brute Force =====
# From attacker workstation:
for i in $(seq 1 20); do
  curl -sk -X POST "https://pve.lab.internal:8006/api2/json/access/ticket" \
    -d "username=admin@LAB&password=wrong_password_${i}" 2>/dev/null
  sleep 0.5
done
# Expected: fail2ban bans after 3 attempts; SIEM alert fires after 5

# Verify ban:
ssh root@pve01 "fail2ban-client status proxmox"
# Expected: Banned IP visible

# ===== TEST 2: Privilege Escalation Attempt =====
# Authenticate as low-privilege user (vm-operator)
TICKET=$(curl -sk -X POST "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=vmoperator@LAB&password=OpP@ss123&otp=123456" | jq -r '.data.ticket')
CSRF=$(curl -sk -X POST "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=vmoperator@LAB&password=OpP@ss123&otp=123456" | jq -r '.data.CSRFPreventionToken')

# Attempt to modify ACLs (should fail — no Permissions.Modify privilege)
curl -sk -X PUT "https://pve.lab.internal:8006/api2/json/access/acl" \
  -H "Cookie: PVEAuthCookie=$TICKET" \
  -H "CSRFPreventionToken: $CSRF" \
  -d "path=/&roles=Administrator&users=vmoperator@LAB"
# Expected: 403 Forbidden

# Verify SIEM logged the attempt
# Check Wazuh for rule 100102 alert

# ===== TEST 3: API Token Abuse (Scope Violation) =====
# Use ci-staging token to attempt production access
curl -sk -H "Authorization: PVEAPIToken=automation@pve!ci-staging=TOKEN_SECRET" \
  "https://pve.lab.internal:8006/api2/json/nodes/pve01/qemu/100/status/current"
# Expected: 403 (VM 100 is in production pool)

# Attempt to create a user (should fail)
curl -sk -X POST \
  -H "Authorization: PVEAPIToken=automation@pve!ci-staging=TOKEN_SECRET" \
  "https://pve.lab.internal:8006/api2/json/access/users" \
  -d "userid=hacker@pve&password=Pwn3d!"
# Expected: 403

# ===== TEST 4: Token Replay from Different IP =====
# Record a valid token and attempt to use it from a different network
# (simulate by SSHing to a different host and using the same token)
ssh other-host "curl -sk -H 'Authorization: PVEAPIToken=automation@pve!monitoring=TOKEN' \
  https://pve.lab.internal:8006/api2/json/version"
# This will succeed (tokens are not IP-bound), but SIEM should flag
# the different source IP for the same token

# ===== TEST 5: Stale Account Discovery =====
# Verify the stale account detection script works:
./find-stale-accounts.sh
```

### 10.9 Step 7: Verification Checklist

```bash
# Run verification checks after lab setup:

echo "=== VERIFICATION CHECKLIST ==="

# V1: AD authentication works
echo -n "[V1] AD Auth: "
RESULT=$(curl -sk -o /dev/null -w "%{http_code}" -X POST \
  "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=testuser@LAB&password=ValidP@ss1&otp=VALID_OTP")
[ "$RESULT" = "200" ] && echo "PASS" || echo "FAIL (HTTP $RESULT)"

# V2: MFA is enforced (login without OTP should fail)
echo -n "[V2] MFA Enforced: "
RESULT=$(curl -sk -o /dev/null -w "%{http_code}" -X POST \
  "https://pve.lab.internal:8006/api2/json/access/ticket" \
  -d "username=testuser@LAB&password=ValidP@ss1")
[ "$RESULT" != "200" ] && echo "PASS (correctly rejected)" || echo "FAIL (accepted without MFA)"

# V3: RBAC isolation works
echo -n "[V3] RBAC Isolation: "
RESULT=$(curl -sk -o /dev/null -w "%{http_code}" \
  -H "Authorization: PVEAPIToken=automation@pve!ci-staging=TOKEN" \
  "https://pve.lab.internal:8006/api2/json/pools/pool-production")
[ "$RESULT" = "403" ] && echo "PASS" || echo "FAIL (HTTP $RESULT)"

# V4: fail2ban active
echo -n "[V4] fail2ban: "
fail2ban-client status proxmox >/dev/null 2>&1 && echo "PASS (active)" || echo "FAIL (not running)"

# V5: Syslog forwarding
echo -n "[V5] Syslog forward: "
logger -t pvedaemon "VERIFICATION TEST"
sleep 2
# Check if Wazuh received it (requires API call to Wazuh manager)
echo "CHECK MANUALLY in Wazuh dashboard"

# V6: Break-glass account exists and alerts fire
echo -n "[V6] Break-glass: "
pveum user list --output-format json | jq -r '.[].userid' | grep -q "breakglass@pve" && echo "PASS" || echo "FAIL (account missing)"

echo ""
echo "=== Lab Implementation Complete ==="
echo "Remaining manual verifications:"
echo "  - Check Wazuh dashboard for test alerts"
echo "  - Verify TOTP enrollment works via GUI"
echo "  - Test break-glass procedure end-to-end"
echo "  - Run quarterly-access-review.sh and review output"
```

### 10.10 Lab Cleanup (Optional)

```bash
# Remove test artifacts (run only when lab is no longer needed)
# WARNING: Destructive — confirm before executing

# Remove realms
pveum realm remove LAB

# Remove custom roles
pveum role remove BackupOperator
pveum role remove VMOperator
pveum role remove NetworkViewer
pveum role remove SecurityAuditor

# Remove pools
pveum pool remove pool-production
pveum pool remove pool-staging
pveum pool remove pool-dmz

# Remove automation user and tokens
pveum user token remove automation@pve ci-staging
pveum user token remove automation@pve monitoring
pveum user token remove automation@pve backup-agent
pveum user delete automation@pve
pveum user delete breakglass@pve

# Remove SIEM configuration
rm -f /etc/rsyslog.d/60-pve-to-wazuh.conf
rm -f /etc/fail2ban/jail.d/proxmox.conf
rm -f /etc/fail2ban/filter.d/proxmox.conf
systemctl restart rsyslog fail2ban
```

---

## Appendix A: Quick Reference — pveum Commands

| Command | Purpose |
|---|---|
| `pveum user add <user@realm>` | Create user |
| `pveum user modify <user@realm> --group <group>` | Add user to group |
| `pveum user token add <user@realm> <tokenid> --privsep 1` | Create API token |
| `pveum user permissions <user@realm>` | Show effective permissions |
| `pveum group add <name>` | Create group |
| `pveum pool add <name>` | Create resource pool |
| `pveum role add <name> --privs "<priv1,priv2>"` | Create custom role |
| `pveum acl modify <path> --roles <role> --users <user>` | Assign permission |
| `pveum acl modify <path> --roles <role> --groups <group>` | Group permission |
| `pveum acl modify <path> --roles <role> --tokens '<user!token>'` | Token permission |
| `pveum acl list` | List all ACLs |
| `pveum realm add <name> --type ad\|ldap\|openid` | Add auth realm |
| `pveum realm sync <name>` | Sync realm users/groups |
| `pveum realm modify <name> --tfa "type=totp"` | Enable 2FA on realm |

## Appendix B: PowerCLI IAM Scripts

```powershell
# === Comprehensive vCenter IAM Audit ===
function Get-VCenterIAMAudit {
    param(
        [string]$VCServer = "vcenter.lab.local"
    )

    Connect-VIServer -Server $VCServer

    # 1. List all permissions
    $permissions = Get-VIPermission | Select-Object @{N='Entity';E={$_.Entity.Name}},
        @{N='EntityType';E={$_.Entity.GetType().Name}},
        Principal, Role, Propagate

    # 2. List all roles (including custom)
    $roles = Get-VIRole | Select-Object Name, IsSystem,
        @{N='PrivilegeCount';E={($_ | Get-VIPrivilege).Count}}

    # 3. List identity sources
    $idSources = Get-IdentitySource | Select-Object Name, Type, DomainName

    # 4. Recent login events (last 7 days)
    $logins = Get-VIEvent -Start (Get-Date).AddDays(-7) -MaxSamples 5000 |
        Where-Object { $_.GetType().Name -match "UserLoginSession" } |
        Group-Object UserName | Select-Object Name, Count |
        Sort-Object Count -Descending

    # Output
    [PSCustomObject]@{
        Permissions   = $permissions
        Roles         = $roles
        IdentitySources = $idSources
        RecentLogins  = $logins
        AuditDate     = Get-Date -Format 'yyyy-MM-dd'
    }
}

# === Remove stale permissions ===
function Remove-StalePermissions {
    param(
        [int]$DaysInactive = 90
    )

    $cutoff = (Get-Date).AddDays(-$DaysInactive)
    $allPerms = Get-VIPermission

    foreach ($perm in $allPerms) {
        # Check if user has logged in recently
        $lastLogin = Get-VIEvent -Start $cutoff -MaxSamples 10000 |
            Where-Object { $_.UserName -eq $perm.Principal -and
                          $_.GetType().Name -eq "UserLoginSessionEvent" } |
            Select-Object -First 1

        if (-not $lastLogin) {
            Write-Warning "STALE: $($perm.Principal) on $($perm.Entity.Name) - no login in ${DaysInactive} days"
            # Uncomment to remove:
            # Remove-VIPermission -Permission $perm -Confirm:$false
        }
    }
}

# === Enforce least privilege — find over-privileged accounts ===
function Find-OverPrivilegedAccounts {
    $adminRole = Get-VIRole -Name "Admin"
    $adminPerms = Get-VIPermission | Where-Object { $_.Role -eq "Admin" }

    Write-Host "=== Accounts with Administrator Role ===" -ForegroundColor Red
    $adminPerms | ForEach-Object {
        $entity = $_.Entity.Name
        $scope = if ($_.Propagate) { "PROPAGATING" } else { "LOCAL ONLY" }
        Write-Host "  $($_.Principal) on [$entity] ($scope)" -ForegroundColor Yellow
    }

    Write-Host "`n=== Recommendation ===" -ForegroundColor Cyan
    Write-Host "  - Remove Admin role from day-to-day accounts"
    Write-Host "  - Use specific roles (VM Admin, Network Admin, etc.)"
    Write-Host "  - Reserve Admin for break-glass accounts only"
}
```

## Appendix C: SIEM Detection Queries (Elasticsearch DSL)

```json
// === Query 1: Failed login spike ===
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "authentication failure" } },
        { "term": { "service.name": "pvedaemon" } },
        { "range": { "@timestamp": { "gte": "now-15m" } } }
      ]
    }
  },
  "aggs": {
    "by_source": {
      "terms": { "field": "source.ip", "min_doc_count": 5 }
    }
  }
}

// === Query 2: Admin actions outside change window ===
{
  "query": {
    "bool": {
      "must": [
        { "terms": { "event.action": ["acl.modify", "user.add", "role.add", "token.add"] } },
        { "term": { "service.name": "pvedaemon" } }
      ],
      "must_not": [
        {
          "range": {
            "@timestamp": {
              "gte": "08:00",
              "lte": "18:00",
              "format": "HH:mm",
              "time_zone": "Europe/Rome"
            }
          }
        }
      ]
    }
  }
}

// === Query 3: Service account acting as human ===
{
  "query": {
    "bool": {
      "must": [
        { "wildcard": { "user.name": "svc-*" } },
        { "terms": { "event.action": ["vm.console", "gui.login", "vnc.connect"] } }
      ]
    }
  }
}

// === Query 4: Multiple realm auth failures (password spray) ===
{
  "query": {
    "bool": {
      "must": [
        { "match": { "message": "authentication failure" } },
        { "range": { "@timestamp": { "gte": "now-10m" } } }
      ]
    }
  },
  "aggs": {
    "by_ip": {
      "terms": { "field": "source.ip" },
      "aggs": {
        "unique_users": {
          "cardinality": { "field": "user.name" }
        },
        "spray_indicator": {
          "bucket_selector": {
            "buckets_path": { "user_count": "unique_users" },
            "script": "params.user_count > 3"
          }
        }
      }
    }
  }
}
```

## Appendix D: Compliance Mapping

| Control | Framework | IAM Requirement | Implementation |
|---|---|---|---|
| AC-2 | NIST 800-53 | Account management | User lifecycle, stale account removal |
| AC-3 | NIST 800-53 | Access enforcement | RBAC with path-based ACLs |
| AC-5 | NIST 800-53 | Separation of duties | Non-overlapping role assignments |
| AC-6 | NIST 800-53 | Least privilege | Custom roles with minimum privileges |
| AC-7 | NIST 800-53 | Unsuccessful logon attempts | fail2ban + account lockout |
| AC-12 | NIST 800-53 | Session termination | Ticket lifetime + inactivity timeout |
| IA-2 | NIST 800-53 | MFA for privileged access | TOTP/WebAuthn on all admin realms |
| IA-4 | NIST 800-53 | Identifier management | Unique user@realm identifiers |
| IA-5 | NIST 800-53 | Authenticator management | Password policy + token rotation |
| AU-2 | NIST 800-53 | Audit events | Login, permission change, privilege escalation |
| AU-6 | NIST 800-53 | Audit review | Quarterly access certification |
| Article 5.1 | NIS2 | Risk management measures | MFA, least privilege, monitoring |
| Article 21 | NIS2 | Cybersecurity risk management | IAM as part of risk management framework |
| Req. 7 | PCI DSS 4.0 | Restrict access to system components | Role-based access per business need |
| Req. 8 | PCI DSS 4.0 | Identify and authenticate access | MFA for admin access, unique IDs |

---

## Key Takeaways

1. **Identity is the new perimeter.** With hypervisor management planes accessible over the network, authentication and authorization are the primary defense — not just network segmentation.

2. **Centralized identity + federated access** is the optimal model for most enterprises. AD provides the authoritative identity; SAML/OIDC provides the access protocol with token-based security.

3. **API tokens are powerful and dangerous.** Always use `privsep=1`, assign explicit ACLs, monitor usage, and rotate on a schedule.

4. **Service accounts are the attacker's preferred persistence mechanism.** Inventory them, restrict them, monitor them, rotate them. An unused service account with admin privileges is a ticking time bomb.

5. **Detection must match attack sophistication.** Credential stuffing is easy to detect (volume-based). Pass-the-hash and token theft require correlation across multiple log sources and behavioral baselines.

6. **Break-glass procedures must exist AND be tested.** When the IdP is down and the LDAP servers are unreachable, your only path to recovery is a pre-staged local account with offline-stored credentials.

7. **Quarterly access reviews are not optional.** Privilege creep is inevitable in any environment. Automated reporting + human review catches the drift that technical controls miss.

---

*End of Module 26 — Identity and Access Management for Hypervisor Environments*
