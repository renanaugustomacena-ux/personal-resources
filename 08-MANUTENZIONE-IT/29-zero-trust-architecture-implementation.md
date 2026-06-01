# 29 — Zero Trust Architecture: Principles, Implementation, and Operations

> Documento tecnico enciclopedico per professionisti IT senior e penetration tester.
> Copre i framework NIST SP 800-207, Forrester ZTX, Google BeyondCorp e implementazioni operative end-to-end.

---

## Indice

1. [Fondamenti Zero Trust](#1-fondamenti-zero-trust)
2. [Componenti Architetturali](#2-componenti-architetturali)
3. [Identity-Centric Security](#3-identity-centric-security)
4. [Device Trust](#4-device-trust)
5. [Network Microsegmentation](#5-network-microsegmentation)
6. [Data Protection in Zero Trust](#6-data-protection-in-zero-trust)
7. [Implementazione Pratica](#7-implementazione-pratica)
8. [Zero Trust per Cloud e Hybrid](#8-zero-trust-per-cloud-e-hybrid)
9. [Monitoraggio e Analytics](#9-monitoraggio-e-analytics)
10. [Penetration Testing Zero Trust](#10-penetration-testing-zero-trust)
11. [Zero Trust per OT/IoT e Sistemi Industriali](#11-zero-trust-per-otiot-e-sistemi-industriali)
12. [Conformità Normativa e Zero Trust](#12-conformità-normativa-e-zero-trust)
13. [AI e Machine Learning nella Zero Trust Architecture](#13-ai-e-machine-learning-nella-zero-trust-architecture)
14. [Confronto Vendor e Ecosistema Commerciale](#14-confronto-vendor-e-ecosistema-commerciale)
15. [Strategia Governativa e Militare](#15-strategia-governativa-e-militare)

---

## 1. Fondamenti Zero Trust

### 1.1 Evoluzione dal Modello Perimetrale

The castle-and-moat security model assumed that anything inside the network perimeter was trustworthy. This assumption collapsed under the weight of:

- **Lateral movement** — once an attacker breaches the perimeter, they move freely east-west
- **Cloud migration** — resources no longer reside within a single physical boundary
- **Remote workforce** — users connect from untrusted networks on unmanaged devices
- **Supply chain attacks** — trusted third-party software becomes a vector (SolarWinds, Codecov, 3CX)
- **Insider threats** — malicious or compromised insiders operate within the trusted zone

Zero Trust eliminates implicit trust entirely. Every access request is evaluated in real-time, regardless of network location.

### 1.2 Principi Fondamentali

| Principio | Descrizione |
|-----------|-------------|
| **Never Trust, Always Verify** | No entity (user, device, service) receives implicit trust based on network position or prior authentication |
| **Least Privilege Access** | Grant minimum permissions required for the specific task, scoped in time and scope |
| **Assume Breach** | Design systems assuming the adversary is already inside the environment |
| **Micro-segmentation** | Create granular security boundaries around individual workloads and resources |
| **Continuous Verification** | Authentication and authorization are not one-time events but ongoing evaluations |
| **Explicit Verification** | All access decisions are made based on all available data points — identity, device, location, behavior, threat intel |

### 1.3 NIST SP 800-207 Framework

NIST Special Publication 800-207 (August 2020, updated 2023) defines the U.S. federal government's canonical Zero Trust architecture. It identifies three core logical components and three deployment approaches.

**Core Tenets (NIST):**

1. All data sources and computing services are considered resources
2. All communication is secured regardless of network location
3. Access to individual enterprise resources is granted on a per-session basis
4. Access to resources is determined by dynamic policy — including client identity, application/service, requesting asset state, behavioral and environmental attributes
5. The enterprise monitors and measures the integrity and security posture of all owned and associated assets
6. All resource authentication and authorization are dynamic and strictly enforced before access is allowed
7. The enterprise collects as much information as possible about the current state of assets, network infrastructure, and communications and uses it to improve its security posture

**Deployment Models (NIST):**

| Model | Description | Use Case |
|-------|-------------|----------|
| Enhanced Identity Governance | Identity as the primary policy component | Organizations with strong IdP maturity |
| Micro-segmentation | Network-level isolation per workload | Data center and cloud-native environments |
| Software-Defined Perimeter | Overlay network hiding infrastructure | Legacy environments with phased migration |

### 1.4 Forrester ZTX (Zero Trust eXtended) Model

Forrester's ZTX Ecosystem extends the original Kindervag model into a comprehensive framework mapping security capabilities to Zero Trust pillars:

```
┌─────────────────────────────────────────────────────────────────┐
│                    VISIBILITY & ANALYTICS                        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│  DATA    │ NETWORKS │WORKLOADS │  PEOPLE  │ DEVICES  │AUTOMATE │
│          │          │          │          │          │& ORCH.  │
├──────────┴──────────┴──────────┴──────────┴──────────┴─────────┤
│                    GOVERNANCE & COMPLIANCE                       │
└─────────────────────────────────────────────────────────────────┘
```

Each pillar requires:
- **Data**: Classification, encryption, DLP, rights management
- **Networks**: Segmentation, encryption, traffic inspection
- **Workloads**: Secure CI/CD, runtime protection, vulnerability management
- **People**: Identity verification, MFA, behavioral analytics
- **Devices**: Inventory, health assessment, endpoint protection
- **Automation & Orchestration**: SOAR, policy-as-code, automated response

### 1.5 Google BeyondCorp Architecture

Google's BeyondCorp (published 2014, operational since 2011) pioneered Zero Trust at scale for 100k+ employees. Key architectural decisions:

1. **No VPN required** — all applications are Internet-facing behind an identity-aware proxy
2. **Device inventory as trust signal** — every device is tracked in a database with security posture
3. **Access tiers** — resources assigned trust tiers; devices must meet minimum tier requirements
4. **User + device = access** — neither alone is sufficient
5. **Encryption everywhere** — all traffic encrypted regardless of network segment

**BeyondCorp Components:**

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  User/Device │────▶│  Access Proxy    │────▶│   Application   │
│              │     │  (Front End)     │     │   (Backend)     │
└──────────────┘     └────────┬─────────┘     └─────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Access Control    │
                    │      Engine        │
                    ├────────────────────┤
                    │ • User Groups DB   │
                    │ • Device Inventory │
                    │ • Trust Inferences │
                    │ • Access Policies  │
                    └────────────────────┘
```

**Trust Tier Model:**

| Tier | Requirements | Access Level |
|------|--------------|--------------|
| Untrusted | No device certificate, unknown device | Public resources only |
| Basic | Valid device certificate, in inventory | Low-sensitivity applications |
| Managed | Corporate-managed device, up-to-date patches | Standard business applications |
| Fully Trusted | Managed + verified firmware + locked screen + current EDR | Sensitive data and admin consoles |

---

## 2. Componenti Architetturali

### 2.1 Control Plane vs Data Plane

Zero Trust architecture mandates strict separation between the control plane (where access decisions are made) and the data plane (where traffic flows). Compromise of the data plane must not compromise policy decisions.

```
                    ┌─────────────────────────────────┐
                    │         CONTROL PLANE            │
                    │                                  │
                    │  ┌────────┐    ┌─────────────┐  │
                    │  │ Policy │◀──▶│   Policy    │  │
                    │  │ Engine │    │Administrator│  │
                    │  │  (PE)  │    │    (PA)     │  │
                    │  └────┬───┘    └──────┬──────┘  │
                    │       │               │         │
                    └───────┼───────────────┼─────────┘
                            │               │
                    ┌───────┼───────────────┼─────────┐
                    │       ▼               ▼         │
                    │  ┌──────────────────────────┐   │
                    │  │  Policy Enforcement      │   │
                    │  │       Point (PEP)        │   │
                    │  └──────────────────────────┘   │
                    │         DATA PLANE              │
                    │                                  │
                    │  Subject ─────────▶ Resource    │
                    └─────────────────────────────────┘
```

### 2.2 Policy Engine (PE)

The Policy Engine is the brain of ZTA. It evaluates access requests against policy rules and produces an allow/deny decision. Inputs include:

- **Subject identity** — authenticated user or service principal
- **Device posture** — compliance state, patch level, EDR status
- **Resource sensitivity** — classification level, data type
- **Environmental context** — time, geolocation, network, impossible travel detection
- **Behavioral analytics** — deviation from baseline, risk score
- **Threat intelligence** — known compromised credentials, active campaigns, IOCs

**Decision Logic (Simplified):**

```python
def evaluate_access(request: AccessRequest) -> Decision:
    identity_score = assess_identity(request.user, request.auth_factors)
    device_score = assess_device(request.device_posture)
    context_score = assess_context(request.geo, request.time, request.network)
    behavior_score = assess_behavior(request.user, request.action_history)
    threat_score = assess_threat_intel(request.user, request.device, request.source_ip)

    composite_trust = weighted_average(
        identity_score * 0.30,
        device_score * 0.25,
        context_score * 0.15,
        behavior_score * 0.20,
        threat_score * 0.10
    )

    required_trust = get_resource_trust_requirement(request.resource)

    if composite_trust >= required_trust:
        return Decision.ALLOW(
            scope=minimum_permissions(request.resource, request.action),
            ttl=session_duration(composite_trust),
            conditions=continuous_evaluation_params(request)
        )
    elif composite_trust >= required_trust * 0.7:
        return Decision.STEP_UP(required_factors=additional_auth_needed(composite_trust))
    else:
        return Decision.DENY(reason=lowest_scoring_factor(scores))
```

### 2.3 Policy Administrator (PA)

The Policy Administrator operationalizes PE decisions:

- **Establishes** the communication path between subject and resource
- **Issues** session tokens, credentials, or certificates (short-lived)
- **Configures** PEP to allow or deny the specific traffic
- **Revokes** sessions when continuous evaluation fails
- **Logs** all decisions for audit and forensics

The PA is the single point of orchestration — if it is compromised, the entire ZTA fails. Therefore:

- PA should run in a hardened, isolated environment
- All PA-to-PEP communication must be authenticated and encrypted
- PA must be air-gapped from the data plane
- PA configuration must be immutable and version-controlled
- PA itself requires multi-party authorization for changes

### 2.4 Policy Enforcement Point (PEP)

The PEP is the gatekeeper — it sits in the data path and enforces PA directives:

- **Inline deployment** — reverse proxy, API gateway, or network firewall
- **Agent-based** — endpoint agent that controls local access
- **Service mesh sidecar** — Envoy proxy in Kubernetes

PEP must enforce:
- Session token validity
- Traffic encryption (mTLS)
- Request-level authorization (not just connection-level)
- Rate limiting and abuse prevention
- Session termination on revocation

### 2.5 Trust Algorithm — Input Signals

The trust algorithm continuously evaluates confidence in the access context. Key signal categories:

```
┌─────────────────────────────────────────────────────────────────────┐
│                       TRUST ALGORITHM INPUTS                         │
├─────────────────┬───────────────────────────────────────────────────┤
│ USER IDENTITY   │ • Authentication strength (password vs FIDO2)     │
│                 │ • Account age and history                          │
│                 │ • Privilege level                                  │
│                 │ • Group memberships and roles                      │
│                 │ • Risk indicators (impossible travel, leaked creds)│
├─────────────────┼───────────────────────────────────────────────────┤
│ DEVICE HEALTH   │ • OS patch level and currency                     │
│                 │ • EDR agent running and reporting                  │
│                 │ • Disk encryption enabled                          │
│                 │ • Firewall active                                  │
│                 │ • Device certificate validity                      │
│                 │ • TPM attestation                                  │
│                 │ • Jailbreak/root detection                         │
├─────────────────┼───────────────────────────────────────────────────┤
│ BEHAVIOR        │ • Access time patterns                            │
│ ANALYTICS       │ • Resource access patterns                        │
│                 │ • Data volume anomalies                            │
│                 │ • Session behavior (typing, mouse movement)        │
│                 │ • Peer group deviation                             │
├─────────────────┼───────────────────────────────────────────────────┤
│ THREAT          │ • Source IP reputation                             │
│ INTELLIGENCE    │ • Known compromised credentials                    │
│                 │ • Active threat campaigns targeting industry       │
│                 │ • Malware signatures on device                     │
│                 │ • Dark web credential exposure                     │
├─────────────────┼───────────────────────────────────────────────────┤
│ CONTEXT         │ • Geolocation and travel velocity                  │
│                 │ • Network type (corporate, home, public WiFi)      │
│                 │ • Time of day vs typical patterns                  │
│                 │ • Request sensitivity vs historical access          │
│                 │ • Concurrent sessions                              │
└─────────────────┴───────────────────────────────────────────────────┘
```

---

## 3. Identity-Centric Security

### 3.1 Principio: L'Identita come Nuovo Perimetro

In Zero Trust, identity replaces the network perimeter as the primary security boundary. If you cannot strongly verify who (or what) is requesting access, all other controls are meaningless.

### 3.2 Strong Authentication — FIDO2, WebAuthn, Passkeys

**FIDO2/WebAuthn** eliminates phishable credentials:

| Property | Passwords | TOTP/SMS | FIDO2/Passkeys |
|----------|-----------|----------|----------------|
| Phishing resistant | No | No | Yes |
| Replay resistant | No | Partially | Yes |
| Server-side secret stored | Yes (hash) | Yes (seed) | No (public key only) |
| MitM resistant | No | No | Yes (origin-bound) |
| User friction | High (memorization) | Medium (code entry) | Low (biometric/PIN) |

**WebAuthn Registration Flow:**

```
User                    Relying Party           Authenticator
  │                          │                       │
  │──── Register request ───▶│                       │
  │                          │──── Challenge ────────▶│
  │                          │                       │
  │                          │◀─── Attestation ──────│
  │                          │     (public key,      │
  │                          │      credential ID,   │
  │                          │      attestation)     │
  │◀── Registration OK ─────│                       │
```

**Platform vs Roaming Authenticators:**
- **Platform**: Built into device (Touch ID, Windows Hello, Android biometric)
- **Roaming**: External hardware key (YubiKey 5, Titan Key)
- **Synced Passkeys**: Platform keys synced via iCloud Keychain, Google Password Manager, 1Password — balance security/usability

**Deployment Recommendation for ZTA:**
- Enforce FIDO2 for all privileged access (Tier 0 and Tier 1 accounts)
- Offer synced passkeys for general workforce
- Require hardware keys for break-glass and admin scenarios
- Disable SMS/voice OTP entirely — it is SIM-swappable and not phishing-resistant

### 3.3 Continuous Authentication

Traditional authentication is binary: authenticated or not. Zero Trust requires continuous evaluation:

- **Session risk scoring** — recalculate trust every N minutes or on suspicious signals
- **Step-up challenges** — require re-authentication for sensitive operations mid-session
- **Behavioral biometrics** — typing cadence, mouse dynamics, touchscreen pressure (passive, continuous)
- **Token binding** — bind session tokens to device characteristics (DPoP for OAuth)
- **Impossible travel detection** — flag when authentication occurs from geographically impossible locations

### 3.4 Risk-Based Adaptive Authentication

Adaptive authentication adjusts requirements dynamically:

```
IF risk_score < 20:
    → Single factor (passkey) sufficient
    → Full session (8 hours)

IF risk_score 20-50:
    → Second factor required
    → Reduced session (4 hours)
    → Sensitive actions require step-up

IF risk_score 50-75:
    → MFA with hardware key required
    → Short session (1 hour)
    → Restricted access scope
    → Real-time monitoring enabled

IF risk_score > 75:
    → Block access
    → Alert SOC
    → Require in-person verification or admin override
```

### 3.5 Identity Providers — Enterprise IdP Landscape

| Provider | Strengths | Zero Trust Features |
|----------|-----------|---------------------|
| **Microsoft Entra ID** (Azure AD) | Deep M365 integration, Conditional Access | Continuous Access Evaluation (CAE), Token Protection, Cross-tenant access |
| **Okta** | IdP-agnostic, extensive app catalog | Device Trust, Adaptive MFA, Identity Threat Protection |
| **Ping Identity** | Hybrid deployment, API security | PingOne Authorize for fine-grained authz, DaVinci orchestration |
| **Google Workspace** | BeyondCorp native integration | Context-Aware Access, endpoint verification |
| **CyberArk Identity** | Privileged access focus | Combined IdP + PAM in single platform |

### 3.6 Identity Governance — Joiner/Mover/Leaver

Zero Trust requires that access is always current:

- **Joiner**: Provision minimum-required access based on role. No standing privileges.
- **Mover**: Immediately revoke old-role access, provision new-role access. Audit for accumulation.
- **Leaver**: Revoke all access within minutes. Kill active sessions. Rotate shared secrets the user had access to.

**Governance Controls:**
- Access certifications (quarterly manager reviews)
- Automated access reviews with revocation on non-response
- Orphaned account detection
- Service account ownership tracking
- Entitlement analytics — identify over-provisioned users

### 3.7 Privileged Access Management (PAM)

PAM is critical in ZTA because privileged accounts can bypass micro-segmentation:

| Solution | Architecture | Key ZTA Feature |
|----------|--------------|-----------------|
| **CyberArk Privilege Cloud** | SaaS vault + PSM + EPM | Just-in-Time elevation, session recording, credential rotation |
| **BeyondTrust** | Agent + jump server | Privilege elevation and delegation management (PEDM) |
| **Delinea (Thycotic + Centrify)** | Secret Server + privilege elevation | Cloud-native vault, DevOps secrets integration |
| **HashiCorp Vault** | API-first secrets engine | Dynamic secrets, short-lived credentials, PKI engine |

**PAM in Zero Trust — Requirements:**
- No standing admin privileges (Just-in-Time access only)
- All privileged sessions recorded and searchable
- Credential rotation after every use or on schedule
- Break-glass procedures with multi-party approval
- Service account credentials rotated automatically, never embedded in code

### 3.8 Service-to-Service Identity — SPIFFE/SPIRE

Workload identity is as important as user identity. SPIFFE (Secure Production Identity Framework For Everyone) provides:

- **SPIFFE ID**: `spiffe://trust-domain/workload-identifier` — a URI-based identity for workloads
- **SVID (SPIFFE Verifiable Identity Document)**: X.509 certificate or JWT encoding the SPIFFE ID
- **SPIRE**: Reference implementation of SPIFFE, providing workload attestation

```
┌───────────────────────────────────────────────────────┐
│                   SPIRE Server                         │
│  • Registration API (defines workload identities)     │
│  • Node attestation (verifies infrastructure)         │
│  • Workload attestation (verifies software)           │
│  • SVID issuance (short-lived X.509 or JWT)          │
└────────────────────────┬──────────────────────────────┘
                         │
              ┌──────────▼───────────┐
              │    SPIRE Agent       │
              │  (per-node daemon)   │
              │  • Unix domain socket│
              │  • Workload API      │
              └──────────┬───────────┘
                         │
         ┌───────────────▼────────────────┐
         │       Workload (Pod/Container) │
         │  • Receives X.509 SVID         │
         │  • Auto-rotated (1-hour TTL)   │
         │  • Used for mTLS to peers      │
         └────────────────────────────────┘
```

**mTLS Everywhere Pattern:**
Every service-to-service call must be mutually authenticated. Neither side trusts the other based on network position:

```yaml
# SPIFFE registration entry example
spiffe_id: "spiffe://prod.example.com/payment-service"
parent_id: "spiffe://prod.example.com/k8s-node/worker-03"
selectors:
  - k8s:pod-label:app=payment-service
  - k8s:ns:production
  - k8s:sa:payment-service-sa
ttl: 3600  # 1 hour
```

---

## 4. Device Trust

### 4.1 Principio: Il Dispositivo come Fattore di Fiducia

A device is not merely a viewport — it is a trust signal. An authenticated user on a compromised device is a threat actor with valid credentials. Device posture assessment is non-negotiable in ZTA.

### 4.2 Device Posture Assessment

Comprehensive device health checks must evaluate:

| Category | Checks | Risk if Failed |
|----------|--------|----------------|
| **OS Patch Level** | Current vs. required minimum, critical CVEs | Exploitable vulnerabilities |
| **Disk Encryption** | BitLocker/FileVault/LUKS enabled | Data exposure on theft |
| **EDR Status** | Agent running, definitions current, no tamper | Undetected malware |
| **Firewall** | Host firewall active, rules compliant | Unnecessary exposure |
| **Screen Lock** | Auto-lock configured, timeout ≤ 5 minutes | Physical access risk |
| **Jailbreak/Root** | Not rooted, no jailbreak indicators | OS security bypass |
| **Certificate** | Valid device certificate, not expired/revoked | Identity unverifiable |
| **Secure Boot** | UEFI Secure Boot enabled, no violations | Boot-level malware |
| **TPM** | TPM 2.0 present and operational | Cannot attest device integrity |

### 4.3 MDM Integration

Mobile Device Management provides the device posture signal pipeline:

**Microsoft Intune (Cross-platform):**

```json
{
  "compliancePolicy": {
    "displayName": "ZTA-Corporate-Windows",
    "platform": "windows10",
    "settings": {
      "osMinimumVersion": "10.0.22631",
      "bitLockerEnabled": true,
      "secureBootEnabled": true,
      "tpmRequired": true,
      "defenderEnabled": true,
      "defenderVersion": "4.18.24040",
      "firewallEnabled": true,
      "passwordRequired": true,
      "passwordMinimumLength": 12,
      "storageRequireEncryption": true,
      "deviceThreatProtectionEnabled": true,
      "deviceThreatProtectionRequiredSecurityLevel": "medium"
    },
    "scheduledActionsForRule": [
      {
        "ruleName": "NonCompliant",
        "scheduledActionConfigurations": [
          {
            "actionType": "block",
            "gracePeriodHours": 0,
            "notificationTemplateId": "zt-noncompliant-alert"
          }
        ]
      }
    ]
  }
}
```

**Jamf Pro (macOS/iOS):**
- Smart Groups define compliance criteria
- Compliance integration with Azure AD/Okta via Jamf Connect or Device Trust connector
- Automated remediation via policies (force FileVault, install updates)

**VMware Workspace ONE:**
- Unified endpoint management across platforms
- Sensors for custom compliance checks (PowerShell, Bash scripts)
- Trust Network integration with third-party security tools

### 4.4 Certificate-Based Device Identity

Device certificates provide cryptographic proof of device identity:

```
Enterprise CA (offline root)
    └── Issuing CA (online, hardware-backed)
         └── Device Certificate (auto-enrolled via MDM/SCEP/EST)
              • Subject: CN=device-hostname
              • SAN: URI:spiffe://corp.example.com/device/{device-id}
              • Key: RSA 4096 or ECDSA P-384 (TPM-backed)
              • Validity: 1 year, auto-renewed 30 days before expiry
              • Extensions: Device ID, Compliance Status OID
```

**TPM-Backed Keys:**
- Private key generated inside the TPM — never exportable
- Attestation proves the key truly resides in hardware
- Platform Configuration Registers (PCRs) prove boot integrity

### 4.5 Device Health Attestation

Windows Device Health Attestation (DHA) and similar mechanisms:

1. Device boots with Measured Boot (each component measured into TPM PCRs)
2. TCG log and AIK-signed quote sent to Health Attestation Service
3. Service validates boot integrity: Secure Boot, BitLocker, ELAM driver, kernel code integrity
4. Returns a health token consumed by the PE in access decisions

**Attack Surface:**
- An attacker who controls a device below the OS cannot be detected by OS-level agents
- Hardware attestation (TPM quotes) detects boot-level compromise
- This is why Zero Trust architectures value TPM attestation as a high-weight signal

### 4.6 BYOD vs Corporate Device Policies

| Policy | BYOD | Corporate Managed |
|--------|------|-------------------|
| Access scope | Limited (email, chat, SaaS only) | Full enterprise resource access |
| Posture checks | App-level container compliance | Full device compliance |
| Data protection | App containerization (MAM) | Full device encryption + DLP |
| Session duration | Short (2 hours max) | Standard (8 hours) |
| Network access | Internet-only, no east-west | Segmented per role |
| Wipe capability | App-level selective wipe | Full device wipe |

---

## 5. Network Microsegmentation

### 5.1 Principio: Eliminare la Fiducia Implicita nella Rete

Traditional flat networks allow unrestricted lateral movement. Micro-segmentation creates enforcement boundaries at the workload level — each workload communicates only with explicitly authorized peers.

### 5.2 Software-Defined Perimeter (SDP)

SDP (Cloud Security Alliance specification) implements "dark cloud" architecture:

1. **Single Packet Authorization (SPA)** — services are invisible until a cryptographic knock is received
2. **Controller validates** — checks user identity, device posture, and authorization
3. **Gateway opens** — temporary, narrow connection path created for that specific session
4. **Mutual TLS** — both client and server authenticate

```
┌──────────────┐                    ┌─────────────────┐
│   SDP Client │── SPA Packet ─────▶│  SDP Controller │
│              │                    │  (validates)    │
│              │◀── Session Token ──│                 │
│              │                    └─────────────────┘
│              │
│              │── mTLS connection ─▶┌─────────────────┐
│              │   (port now open)   │   SDP Gateway   │
└──────────────┘                    │   (App access)  │
                                    └─────────────────┘
```

Services protected by SDP are invisible to port scanners. No TCP handshake completes without prior authorization.

### 5.3 Identity-Aware Proxy (IAP)

IAP solutions provide application-level zero trust without requiring VPN:

| Solution | Deployment | Key Feature |
|----------|-----------|-------------|
| **Google IAP** | GCP-native, Cloud Run/GKE | BeyondCorp integration, context-aware |
| **Cloudflare Access** | Edge-deployed, any origin | WARP client, device posture via Cloudflare One |
| **Zscaler Private Access (ZPA)** | Cloud connector, inside-out | No inbound connections, app segmentation |
| **Tailscale / Headscale** | WireGuard mesh overlay | ACL-based, identity-aware, no infra change |
| **Palo Alto Prisma Access** | SASE platform | Full traffic inspection + ZTNA |

**Cloudflare Access Policy Example:**

```json
{
  "name": "admin-panel-access",
  "decision": "allow",
  "include": [
    {"group": {"id": "platform-engineers-group-uuid"}}
  ],
  "require": [
    {"login_method": {"id": "hardware-key-idp-uuid"}},
    {"device_posture": {"integration_uid": "crowdstrike-integration-uuid"}}
  ],
  "exclude": [
    {"geo": {"country_code": "RU"}},
    {"geo": {"country_code": "CN"}}
  ],
  "session_duration": "1h",
  "purpose_justification_required": true
}
```

### 5.4 Lateral Movement Prevention

Techniques to contain east-west movement:

1. **Default-deny between workloads** — no communication unless explicitly allowed
2. **Per-flow encryption** — even within the same VLAN, mTLS is required
3. **Break-glass detection** — alert on any communication not in the allow-list
4. **Honeypots/deception** — deploy canary services that should never receive traffic
5. **Time-bounded access** — service-to-service communication tokens expire rapidly

### 5.5 Service Mesh Zero Trust — Istio

Istio provides transparent mTLS and fine-grained authorization for Kubernetes workloads:

**Istio PeerAuthentication — enforce mTLS:**

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # All traffic must be mTLS — no exceptions
```

**Istio AuthorizationPolicy — workload-level access control:**

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: payment-service-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
          - "cluster.local/ns/production/sa/order-service"
          - "cluster.local/ns/production/sa/refund-service"
    to:
    - operation:
        methods: ["POST"]
        paths: ["/api/v1/charge", "/api/v1/refund"]
  - from:
    - source:
        principals:
          - "cluster.local/ns/monitoring/sa/prometheus"
    to:
    - operation:
        methods: ["GET"]
        paths: ["/metrics", "/healthz"]
```

**Istio deny-all baseline (apply first, then allow incrementally):**

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}  # Empty spec = deny all traffic to all workloads in namespace
```

### 5.6 Kubernetes Network Policies

Native Kubernetes NetworkPolicy provides L3/L4 segmentation:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payment-service-netpol
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: payment-service
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: order-service
        - podSelector:
            matchLabels:
              app: refund-service
      ports:
        - protocol: TCP
          port: 8443
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: postgres
              tier: database
      ports:
        - protocol: TCP
          port: 5432
    - to:  # DNS resolution
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
```

**Calico NetworkPolicy (extends native with L7 and DNS rules):**

```yaml
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: payment-egress-restrict
  namespace: production
spec:
  selector: app == 'payment-service'
  egress:
    - action: Allow
      protocol: TCP
      destination:
        selector: app == 'postgres' && tier == 'database'
        ports: [5432]
    - action: Allow
      protocol: TCP
      destination:
        domains:
          - "stripe.com"
          - "api.stripe.com"
        ports: [443]
    - action: Deny
```

### 5.7 DNS-Based Traffic Control

DNS is a powerful segmentation lever:

- **Split DNS** — internal resources resolve only from authorized networks/devices
- **DNS filtering** — block known malicious domains at resolver level
- **Encrypted DNS** — DoH/DoT prevents network-level DNS snooping and manipulation
- **DNS as canary** — resolution of non-existent internal names indicates reconnaissance

---

## 6. Data Protection in Zero Trust

### 6.1 Principio: Proteggere il Dato, Non Solo il Contenitore

Zero Trust recognizes that data is the ultimate target. Network and identity controls exist to protect data — but data must also protect itself through encryption, classification, and access governance.

### 6.2 Data Classification and Labeling

| Level | Label | Examples | ZTA Control |
|-------|-------|----------|-------------|
| Public | `PUBLIC` | Marketing materials, docs | Minimal access control |
| Internal | `INTERNAL` | Company policies, org charts | Authenticated user required |
| Confidential | `CONFIDENTIAL` | Customer data, financials | Role-based + device trust |
| Restricted | `RESTRICTED` | PII, PHI, payment data | MFA + managed device + logging + DLP |
| Top Secret | `TOP-SECRET` | Cryptographic keys, M&A plans | Hardware token + PAM + air-gapped workstation |

**Automated Classification:**
- Microsoft Purview (trainable classifiers, regex, exact data match)
- Google Cloud DLP (infoTypes: CREDIT_CARD, SSN, EMAIL_ADDRESS)
- Custom ML models for domain-specific sensitive data

### 6.3 DLP Integration

Data Loss Prevention in ZTA operates at multiple enforcement points:

```
┌──────────────────────────────────────────────────────┐
│                  DLP Enforcement Points               │
├──────────────────────────────────────────────────────┤
│  Endpoint DLP    → Agent prevents copy/print/upload  │
│  Network DLP     → Proxy inspects egress traffic     │
│  Cloud DLP       → API inspects SaaS data flows      │
│  Email DLP       → Gateway scans attachments/body    │
│  Storage DLP     → Periodic scan of repos/shares     │
└──────────────────────────────────────────────────────┘
```

In Zero Trust, DLP policies are context-aware:
- Same user on a managed device can download — on BYOD, only view in browser
- Same data at `CONFIDENTIAL` level can be shared internally — but DLP blocks external sharing
- Step-up verification before bulk data export

### 6.4 Encryption Strategy

**In Transit:**
- TLS 1.3 minimum for all external communication
- mTLS for all internal service-to-service
- IPsec or WireGuard for legacy inter-site links
- Certificate pinning for mobile apps connecting to API backends

**At Rest:**
- AES-256-GCM for application-level encryption
- Storage-level encryption (dm-crypt/LUKS, BitLocker, Cloud KMS)
- Database column-level encryption for highly sensitive fields (TDE is not sufficient)
- Client-side encryption for zero-knowledge requirements

**In Use (emerging):**
- Confidential Computing (Intel SGX, AMD SEV-SNP, ARM CCA)
- Homomorphic encryption (limited practical use currently)
- Secure enclaves for processing sensitive data

### 6.5 Key Management

```
┌─────────────────────────────────────────────────────┐
│              Key Hierarchy                            │
├─────────────────────────────────────────────────────┤
│  Root Key (HSM-stored, rarely used)                  │
│    └── Master KEK (Key Encryption Key)               │
│         └── DEK (Data Encryption Key, per-object)    │
│              └── Wrapped DEK stored with ciphertext  │
└─────────────────────────────────────────────────────┘
```

**Cloud KMS Solutions:**
- AWS KMS — HSM-backed, automatic rotation, CloudTrail audit
- Azure Key Vault — HSM or software keys, RBAC + access policies
- GCP Cloud KMS — Hardware and software protection levels, EKM for external keys
- HashiCorp Vault Transit — API-driven encrypt/decrypt, key versioning

**Key Management Policies:**
- Automatic rotation every 90 days (DEKs) to 365 days (KEKs)
- Separation of duties: key admin ≠ data admin
- Key material never leaves HSM boundary for root/master keys
- Audit log every key operation
- Disaster recovery: key escrow with M-of-N ceremony

### 6.6 Tokenization

Replace sensitive data with non-reversible tokens:

- **Format-preserving tokenization** — token maintains the format (e.g., credit card number format)
- **Vault-based tokenization** — centralized mapping in a hardened vault
- **Use cases**: PCI-DSS scope reduction, minimizing PII in analytics pipelines

### 6.7 Rights Management

Microsoft Azure Information Protection (AIP) / Purview Information Protection:
- Persistent encryption tied to the document
- Access policy travels with the file
- Revocation possible even after file leaves the organization
- Watermarking, copy/print restrictions, expiry dates

---

## 7. Implementazione Pratica

### 7.1 Modello di Maturita Zero Trust

```
┌─────────────────────────────────────────────────────────────────┐
│  MATURITY LEVEL        │ CHARACTERISTICS                         │
├────────────────────────┼─────────────────────────────────────────┤
│  1. Traditional        │ Perimeter-based, flat network,          │
│                        │ password-only auth, implicit trust       │
├────────────────────────┼─────────────────────────────────────────┤
│  2. Initial            │ MFA deployed, basic segmentation,       │
│                        │ some visibility, manual policies         │
├────────────────────────┼─────────────────────────────────────────┤
│  3. Advanced           │ Risk-based auth, device trust,          │
│                        │ automated policies, UEBA, micro-seg     │
│                        │ for critical workloads                   │
├────────────────────────┼─────────────────────────────────────────┤
│  4. Optimal            │ Continuous verification, ML-driven      │
│                        │ risk, full micro-seg, automated         │
│                        │ response, ZTA for all resources          │
└────────────────────────┴─────────────────────────────────────────┘
```

### 7.2 Phase 1: Identity Foundation (Mesi 1-3)

**Objective:** Establish strong, verified identity for all users.

**Deliverables:**
- [ ] Deploy centralized IdP (Entra ID, Okta, or equivalent)
- [ ] Enforce MFA for 100% of users (FIDO2 for privileged, push notification minimum for standard)
- [ ] Implement SSO for all SaaS applications
- [ ] Disable legacy authentication protocols (NTLM, Basic Auth, IMAP plain)
- [ ] Deploy Conditional Access baseline policies
- [ ] Implement PAM for all admin accounts
- [ ] Establish identity governance processes (joiner/mover/leaver automation)
- [ ] Configure impossible travel and leaked credential detection

**Azure Conditional Access — Baseline Policy Example:**

```json
{
  "displayName": "ZTA-Phase1-RequireMFA-AllUsers",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"],
      "excludeUsers": ["breakGlassAccount1-uuid", "breakGlassAccount2-uuid"]
    },
    "applications": {
      "includeApplications": ["All"]
    },
    "clientAppTypes": ["browser", "mobileAppsAndDesktopClients"]
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["mfa"]
  },
  "sessionControls": {
    "signInFrequency": {
      "value": 8,
      "type": "hours",
      "isEnabled": true
    },
    "persistentBrowser": {
      "mode": "never",
      "isEnabled": true
    }
  }
}
```

**Conditional Access — Block Legacy Auth:**

```json
{
  "displayName": "ZTA-Phase1-BlockLegacyAuth",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"]
    },
    "applications": {
      "includeApplications": ["All"]
    },
    "clientAppTypes": ["exchangeActiveSync", "other"]
  },
  "grantControls": {
    "operator": "OR",
    "builtInControls": ["block"]
  }
}
```

### 7.3 Phase 2: Device Trust (Mesi 3-6)

**Objective:** Ensure only healthy, known devices access enterprise resources.

**Deliverables:**
- [ ] Deploy MDM (Intune/Jamf/Workspace ONE) to 100% of corporate devices
- [ ] Define compliance policies per platform (Windows, macOS, iOS, Android)
- [ ] Integrate device compliance with Conditional Access (deny non-compliant)
- [ ] Deploy certificate-based device authentication
- [ ] Enable TPM attestation for Windows fleet
- [ ] Define BYOD policies and MAM containers
- [ ] Implement EDR integration with access decisions (CrowdStrike ZTA score, Defender for Endpoint)

**Conditional Access — Require Compliant Device:**

```json
{
  "displayName": "ZTA-Phase2-RequireCompliantDevice",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeUsers": ["All"],
      "excludeGroups": ["BYOD-Users-Group"]
    },
    "applications": {
      "includeApplications": ["All"],
      "excludeApplications": ["Office365Exchange-uuid"]
    },
    "platforms": {
      "includePlatforms": ["windows", "macOS"]
    }
  },
  "grantControls": {
    "operator": "AND",
    "builtInControls": ["mfa", "compliantDevice"]
  }
}
```

### 7.4 Phase 3: Network Segmentation (Mesi 6-9)

**Objective:** Eliminate implicit trust in network connectivity.

**Deliverables:**
- [ ] Map all application communication flows (east-west traffic analysis)
- [ ] Deploy identity-aware proxy for all internal web applications
- [ ] Implement micro-segmentation for Tier 0 assets (DC, AD, PKI)
- [ ] Replace VPN with ZTNA for remote access
- [ ] Deploy service mesh in Kubernetes environments
- [ ] Implement default-deny network policies
- [ ] Enable encrypted DNS (DoH/DoT) enterprise-wide

### 7.5 Phase 4: Workload Protection (Mesi 9-12)

**Objective:** Secure workload-to-workload communication and runtime.

**Deliverables:**
- [ ] Deploy SPIFFE/SPIRE for workload identity
- [ ] Enforce mTLS for all service-to-service communication
- [ ] Implement runtime protection (Falco, Sysdig, Aqua)
- [ ] Secure CI/CD pipeline (signed images, provenance, SBOM)
- [ ] Implement Kubernetes admission controllers (OPA Gatekeeper)
- [ ] Deploy workload firewalls (Calico Enterprise, Cilium)

### 7.6 Phase 5: Data Protection (Mesi 12-15)

**Objective:** Protect data at every stage of its lifecycle.

**Deliverables:**
- [ ] Complete data classification for all repositories
- [ ] Deploy DLP at endpoint, network, and cloud layers
- [ ] Implement rights management for sensitive documents
- [ ] Enable column-level encryption for PII/PHI in databases
- [ ] Deploy tokenization for payment data
- [ ] Implement data access governance (who accessed what, when)

### 7.7 Phase 6: Visibility and Analytics (Mesi 15-18)

**Objective:** Achieve continuous monitoring with automated response.

**Deliverables:**
- [ ] Deploy UEBA with baseline establishment (30-day learning period)
- [ ] Integrate all ZTA signals into SIEM (identity, device, network, data)
- [ ] Implement automated playbooks for common ZTA alerts
- [ ] Build executive dashboards for ZTA maturity metrics
- [ ] Conduct tabletop exercises simulating ZTA bypass attempts
- [ ] Establish continuous improvement cycle (quarterly maturity assessment)

### 7.8 Migration Strategy — From Perimeter to Zero Trust

**Parallel Operation Model:**
Never rip-and-replace. Run Zero Trust in parallel with existing perimeter:

1. **Shadow mode** — ZTA evaluates but does not enforce; log what would be blocked
2. **Pilot groups** — Enforce ZTA for volunteer teams first (IT, security)
3. **Incremental enforcement** — Application by application, team by team
4. **Perimeter retirement** — Only remove perimeter controls when ZTA covers 100% of the access paths to that resource

**Common Migration Pitfalls:**
- Trying to do everything at once — leads to user revolt and rollback
- Ignoring legacy applications that cannot support modern auth
- Not measuring baseline before enforcement (no visibility = no enforcement)
- Underestimating the cultural change required (developers hate friction)
- Not having break-glass procedures tested before enforcement

---

## 8. Zero Trust per Cloud e Hybrid

### 8.1 Multi-Cloud Zero Trust Strategy

Multi-cloud requires a unified policy layer above individual cloud controls:

```
┌─────────────────────────────────────────────────────────┐
│              Unified Policy Layer                         │
│  (Okta/Entra ID + Hashicorp Vault + Terraform)          │
├────────────────┬─────────────────┬──────────────────────┤
│      AWS       │      Azure      │        GCP           │
│  VPC + IAM     │  VNet + RBAC    │  VPC + IAM           │
│  PrivateLink   │  Private Link   │  Private Service     │
│  Verified Acc. │  Cond. Access   │  BeyondCorp Ent.     │
└────────────────┴─────────────────┴──────────────────────┘
```

### 8.2 AWS Zero Trust Implementation

**IAM Policy — Least Privilege with Conditions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowS3ReadOnlyFromVPC",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::production-data-bucket",
        "arn:aws:s3:::production-data-bucket/*"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceVpc": "vpc-0abc123def456"
        },
        "Bool": {
          "aws:MultiFactorAuthPresent": "true"
        },
        "IpAddress": {
          "aws:SourceIp": ["10.0.0.0/8"]
        },
        "StringLike": {
          "aws:PrincipalTag/department": "engineering"
        },
        "NumericLessThan": {
          "aws:MultiFactorAuthAge": "3600"
        }
      }
    },
    {
      "Sid": "DenyWithoutEncryption",
      "Effect": "Deny",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::production-data-bucket/*",
      "Condition": {
        "StringNotEquals": {
          "s3:x-amz-server-side-encryption": "aws:kms"
        }
      }
    }
  ]
}
```

**AWS Verified Access (ZTNA for internal apps):**
- Evaluates user identity (from IdP) and device posture (from endpoint verification)
- No VPN required — users connect directly via browser
- Cedar policy language for fine-grained access rules
- Integration with AWS WAF for application-layer protection

**AWS PrivateLink:**
- Keep traffic off the public internet
- Service consumers access resources via private ENIs in their VPC
- No internet gateway, NAT, or public IP needed
- Combined with VPC endpoints for AWS service access

### 8.3 Azure Zero Trust

**Conditional Access — Complete Zero Trust Policy Set:**

```json
{
  "displayName": "ZTA-FullStack-SensitiveApps",
  "state": "enabled",
  "conditions": {
    "users": {
      "includeGroups": ["all-employees-group-uuid"]
    },
    "applications": {
      "includeApplications": ["hr-system-uuid", "finance-portal-uuid"]
    },
    "locations": {
      "includeLocations": ["All"],
      "excludeLocations": ["corporate-offices-named-location"]
    },
    "devices": {
      "deviceFilter": {
        "mode": "include",
        "rule": "device.isCompliant -eq True -and device.trustType -eq \"AzureAD\""
      }
    },
    "signInRiskLevels": ["none", "low"],
    "userRiskLevels": ["none", "low"]
  },
  "grantControls": {
    "operator": "AND",
    "builtInControls": ["mfa", "compliantDevice"],
    "authenticationStrength": {
      "id": "phishing-resistant-mfa-strength-uuid"
    }
  },
  "sessionControls": {
    "signInFrequency": {
      "value": 4,
      "type": "hours",
      "isEnabled": true,
      "frequencyInterval": "everyTime"
    },
    "cloudAppSecurity": {
      "isEnabled": true,
      "cloudAppSecurityType": "monitorOnly"
    },
    "continuousAccessEvaluation": {
      "mode": "strictEnforcement"
    }
  }
}
```

**Azure Private Link + Private Endpoints:**
- PaaS services (SQL, Storage, Key Vault) accessible only via private IP
- Network Security Groups restrict source traffic
- No public endpoint exposure

**Azure Front Door with Private Origin:**
- Global load balancing + WAF + DDoS protection
- Backend applications not internet-routable
- Combined with Conditional Access for end-to-end ZTA

### 8.4 GCP Zero Trust — BeyondCorp Enterprise

Google's commercial BeyondCorp offering:

- **IAP (Identity-Aware Proxy)**: Authenticates and authorizes every request to GCP applications
- **VPC Service Controls**: Create security perimeters around GCP resources (prevent data exfiltration)
- **Access Context Manager**: Define access levels based on device, network, identity attributes
- **Endpoint Verification**: Chrome extension that reports device posture

**Access Context Manager — Custom Access Level:**

```yaml
# access-level.yaml
- name: accessPolicies/123456789/accessLevels/trusted_device_corporate
  title: "Trusted Corporate Device"
  basic:
    combiningFunction: AND
    conditions:
      - devicePolicy:
          requireScreenlock: true
          allowedEncryptionStatuses:
            - ENCRYPTED
          requireCorpOwned: true
          osConstraints:
            - osType: DESKTOP_CHROME_OS
              minimumVersion: "110.0"
            - osType: DESKTOP_WINDOWS
              minimumVersion: "10.0.22631"
            - osType: DESKTOP_MAC
              minimumVersion: "14.0"
      - ipSubnetworks:
          - "203.0.113.0/24"
          - "198.51.100.0/24"
      - members:
          - "user:*@example.com"
      - regions:
          - "US"
          - "EU"
```

### 8.5 Kubernetes Zero Trust

Kubernetes is inherently multi-tenant and requires defense-in-depth:

**Layer 1 — Pod Security Standards:**

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/warn: restricted
```

**Layer 2 — OPA Gatekeeper Constraint (deny privileged containers):**

```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPPrivilegedContainer
metadata:
  name: deny-privileged
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
    namespaces: ["production", "staging"]
  parameters:
    exemptImages:
      - "gcr.io/company/init-container:*"
```

**Layer 3 — Network Policy (deny-all baseline):**

```yaml
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
```

**Layer 4 — Service Mesh mTLS (Linkerd):**

```yaml
apiVersion: policy.linkerd.io/v1beta3
kind: Server
metadata:
  name: payment-service
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: payment-service
  port: 8443
  proxyProtocol: TLS

---
apiVersion: policy.linkerd.io/v1beta3
kind: ServerAuthorization
metadata:
  name: payment-allow-order-service
  namespace: production
spec:
  server:
    name: payment-service
  client:
    meshTLS:
      serviceAccounts:
        - name: order-service
          namespace: production
```

**Layer 5 — RBAC (minimal ClusterRole):**

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: developer-readonly
  namespace: production
spec:
  rules:
    - apiGroups: [""]
      resources: ["pods", "services", "configmaps"]
      verbs: ["get", "list", "watch"]
    - apiGroups: [""]
      resources: ["pods/log"]
      verbs: ["get"]
    # Explicitly NO access to secrets, exec, port-forward
```

---

## 9. Monitoraggio e Analytics

### 9.1 Continuous Monitoring Requirements

Zero Trust demands real-time visibility across all pillars. Monitoring must be:

- **Comprehensive** — cover identity, device, network, application, and data events
- **Correlated** — link events across pillars (user X on device Y accessing resource Z)
- **Real-time** — detection within seconds, not hours
- **Actionable** — alerts trigger automated responses or clear human playbooks
- **Contextual** — provide enough context for rapid triage without alert fatigue

### 9.2 UEBA — User and Entity Behavior Analytics

UEBA establishes behavioral baselines and detects anomalies:

**Baseline Construction:**
- Login patterns (time, location, device, frequency)
- Resource access patterns (which systems, how much data, what actions)
- Network behavior (internal destinations, data volume, protocols)
- Peer group comparison (deviate from team norms)

**Anomaly Categories:**

| Category | Examples | ZTA Response |
|----------|----------|--------------|
| **Temporal** | Login at 3 AM when baseline is 9-6 | Step-up auth, reduced session |
| **Volumetric** | Download 10GB when baseline is 100MB/day | Block, alert, force re-auth |
| **Geographic** | Login from new country, impossible travel | Block, require admin verification |
| **Behavioral** | Access 50 new resources not previously used | Reduce scope, investigate |
| **Privilege** | Lateral movement pattern (multiple systems in sequence) | Terminate session, alert SOC |

### 9.3 Risk Scoring Algorithm

```python
class ZTARiskEngine:
    """Continuous risk assessment for Zero Trust sessions."""

    WEIGHTS = {
        'identity_confidence': 0.25,
        'device_trust': 0.25,
        'behavior_score': 0.20,
        'context_risk': 0.15,
        'threat_intel': 0.15,
    }

    def calculate_session_risk(self, session: Session) -> float:
        """
        Returns risk score 0-100.
        0 = lowest risk, 100 = highest risk.
        Inverse of trust score.
        """
        scores = {
            'identity_confidence': self._assess_identity(session),
            'device_trust': self._assess_device(session),
            'behavior_score': self._assess_behavior(session),
            'context_risk': self._assess_context(session),
            'threat_intel': self._assess_threats(session),
        }

        weighted_risk = sum(
            scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS
        )

        # Apply multiplicative penalty for critical signals
        if session.credentials_leaked:
            weighted_risk = min(100, weighted_risk * 2.0)
        if session.device_compromised:
            weighted_risk = min(100, weighted_risk * 2.5)

        return round(weighted_risk, 2)

    def _assess_identity(self, session: Session) -> float:
        risk = 0.0
        if session.auth_method == 'password_only':
            risk += 40
        if session.mfa_type == 'sms':
            risk += 15
        if session.account_age_days < 7:
            risk += 20
        if session.failed_logins_24h > 3:
            risk += 25
        return min(100, risk)

    def _assess_device(self, session: Session) -> float:
        risk = 0.0
        if not session.device_managed:
            risk += 30
        if not session.disk_encrypted:
            risk += 20
        if session.os_patch_age_days > 30:
            risk += 25
        if not session.edr_active:
            risk += 35
        if session.device_jailbroken:
            risk = 100
        return min(100, risk)

    def _assess_behavior(self, session: Session) -> float:
        risk = 0.0
        if session.access_time_deviation > 2.0:  # standard deviations
            risk += 20
        if session.resource_access_anomaly > 0.7:
            risk += 30
        if session.data_volume_ratio > 5.0:  # vs 30-day average
            risk += 35
        if session.lateral_movement_indicators > 0:
            risk += 50
        return min(100, risk)

    def _assess_context(self, session: Session) -> float:
        risk = 0.0
        if session.network_type == 'public_wifi':
            risk += 25
        if session.geo_new_location:
            risk += 20
        if session.impossible_travel:
            risk += 60
        if session.tor_exit_node:
            risk += 50
        return min(100, risk)

    def _assess_threats(self, session: Session) -> float:
        risk = 0.0
        if session.ip_reputation == 'malicious':
            risk += 50
        if session.credentials_in_breach_db:
            risk += 60
        if session.active_campaign_targeting_org:
            risk += 30
        return min(100, risk)
```

### 9.4 Session Risk Re-evaluation

Sessions are not static — risk must be continuously re-evaluated:

```
┌──────────────────────────────────────────────────────────────────┐
│  Event Type                │ Re-evaluation Trigger                │
├────────────────────────────┼──────────────────────────────────────┤
│  Time-based                │ Every 15 minutes for standard        │
│                            │ Every 5 minutes for privileged       │
├────────────────────────────┼──────────────────────────────────────┤
│  Action-based              │ On sensitive resource access          │
│                            │ On privilege escalation attempt       │
│                            │ On bulk data operation                │
├────────────────────────────┼──────────────────────────────────────┤
│  Signal-based              │ Device compliance state change        │
│                            │ Threat intel update (IP/user/cred)    │
│                            │ Anomalous behavior detected           │
│                            │ Concurrent session from new location  │
├────────────────────────────┼──────────────────────────────────────┤
│  Response Actions          │ • Reduce session scope (read-only)    │
│                            │ • Force re-authentication             │
│                            │ • Terminate session                   │
│                            │ • Block and alert SOC                 │
└────────────────────────────┴──────────────────────────────────────┘
```

### 9.5 SIEM Integration for ZTA Telemetry

Zero Trust generates massive telemetry. SIEM must be configured to:

**High-Value Data Sources:**
- Identity provider logs (authentication, token issuance, policy evaluation)
- Conditional Access / adaptive auth decisions
- Device compliance state changes
- Network flow logs (VPC Flow, NSG Flow)
- Service mesh access logs (Envoy access log)
- API gateway request/response metadata
- DLP alerts and data classification events
- EDR telemetry correlated with access decisions

**Detection Rules (SIEM Pseudocode):**

```
# Detect trust boundary violation attempt
RULE: lateral_movement_attempt
  WHEN source.workload NOT IN authorized_peers(destination.workload)
  AND event.action = "connection_established"
  THEN severity = HIGH
  AND action = terminate_session(source.session_id)
  AND alert = soc_tier2

# Detect device posture downgrade during active session
RULE: device_posture_degraded
  WHEN device.compliance_state CHANGED FROM "compliant" TO "non-compliant"
  AND session.active = true
  THEN action = force_reauthentication(session.user)
  AND reduce_scope(session, "read-only")

# Detect impossible travel with active session
RULE: impossible_travel_active_session
  WHEN auth.new_location.distance(session.established_location) > 500km
  AND time_delta(auth.new_time, session.last_activity) < 1h
  THEN severity = CRITICAL
  AND action = terminate_all_sessions(user)
  AND action = lock_account(user, duration="until_verified")
```

### 9.6 SOC Workflow Adaptation for ZTA

Zero Trust changes how SOC analysts work:

**Traditional SOC:** "Is this traffic malicious?"
**ZTA SOC:** "Did the trust evaluation correctly permit/deny this access?"

**New SOC Responsibilities:**
1. Monitor trust score distributions — drift indicates misconfiguration
2. Investigate step-up authentication failures — may indicate targeted attack
3. Audit access denials — false positives degrade user experience and lead to workarounds
4. Correlate trust signals — a single low signal may be noise; multiple low signals across pillars indicate compromise
5. Respond to policy gaps — access that succeeded despite insufficient trust score

**Metrics:**
- Mean time to detect trust violation (MTTD)
- Mean time to revoke compromised session (MTTR)
- False positive rate for adaptive auth challenges
- Percentage of access evaluated by ZTA vs. legacy paths
- Trust score distribution by population (identify outlier groups)

---

## 10. Penetration Testing Zero Trust

### 10.1 Principio: Testare i Confini della Fiducia

Penetration testing in a Zero Trust environment requires a fundamentally different approach than traditional network pentesting. The goal is not to breach a perimeter — there is no perimeter. The goal is to test whether trust decisions can be manipulated, bypassed, or exploited.

### 10.2 Testing Trust Boundaries

**Scope Definition for ZTA Pentests:**

| Test Area | Objective | Success Criteria |
|-----------|-----------|------------------|
| Identity layer | Bypass or weaken authentication | Obtain session without required factors |
| Device trust | Spoof compliant device posture | Access resources with non-compliant device |
| Network segmentation | Cross segmentation boundary | Establish communication between unauthorized workloads |
| Data controls | Exfiltrate classified data | Move RESTRICTED data outside approved channels |
| Policy engine | Manipulate trust score | Achieve higher trust than warranted |
| Continuous evaluation | Maintain access after posture change | Keep session after device becomes non-compliant |

### 10.3 Attempting Lateral Movement in ZTA

In a mature ZTA environment, lateral movement should be impossible. Testing methodology:

**Phase 1 — Initial Foothold:**
1. Compromise a single workload (assume breach — start from this position)
2. Enumerate visible services from the compromised workload
3. Attempt connections to services outside the allow-list

**Phase 2 — Service Mesh Bypass:**
1. Attempt direct pod-to-pod communication bypassing the sidecar proxy
2. Test for init container vulnerabilities that execute before mesh proxy starts
3. Check for services with mesh exclusion annotations
4. Attempt to forge or replay SVID certificates
5. Test mTLS downgrade by connecting on non-standard ports

**Phase 3 — Privilege Escalation:**
1. Attempt to access Kubernetes API with the workload's service account
2. Test for overly permissive RBAC bindings
3. Check for mounted service account tokens with cluster-wide access
4. Attempt to access cloud metadata services (169.254.169.254)
5. Test for IAM role assumption chains

**Phase 4 — Segmentation Escape:**
1. Test DNS-based exfiltration (does DNS egress respect network policies?)
2. Attempt ICMP tunneling
3. Test for allowed egress ports that can tunnel other protocols
4. Check if network policies enforce on all pod network interfaces

### 10.4 Identity Attack Vectors in ZTA

**Token Theft and Replay:**
- Primary Access Token (PAT) theft from browser storage
- PRT (Primary Refresh Token) extraction from device (mimikatz, ROADtools)
- Steal OAuth refresh tokens from token cache
- Session cookie theft via XSS or malware

**Mitigation Testing:**
- Verify that stolen tokens are bound to the original device (token binding, DPoP)
- Test Continuous Access Evaluation (CAE) — does revoking a user immediately kill active sessions?
- Verify that step-up auth is triggered when token is used from a new device/location

**Identity Provider Attacks:**
- SAML response manipulation (signature wrapping, XML injection)
- OAuth redirect URI manipulation
- Consent phishing (illicit consent grant)
- IdP administration compromise (golden SAML / golden ticket equivalent)

**Testing FIDO2 Implementations:**
- Can a non-FIDO2 method be downgraded to during registration?
- Is credential ID validation performed correctly?
- Can backup eligibility flags be manipulated?
- Test for implementation-specific vulnerabilities (origin validation, RP ID handling)

### 10.5 Device Spoofing and Posture Bypass

**Intune Compliance Bypass Testing:**
1. Register a VM as a "compliant" device via Graph API manipulation
2. Modify device compliance attributes after registration
3. Test delay between device non-compliance and access revocation
4. Attempt to present stale compliance attestation

**Certificate Theft:**
- Extract device certificates from endpoints (DPAPI, Keychain)
- Clone device identity to another machine
- Test if certificate revocation is checked in real-time
- Attempt to use extracted certificate from a non-TPM-bound platform

**TPM Attestation Bypass:**
- Present fabricated PCR values (requires compromised firmware — theoretical)
- Test for relay attacks on attestation protocols
- Verify that the attestation service validates TPM manufacturer certificates
- Check if software TPM (vTPM) is accepted with same trust level as hardware TPM

### 10.6 Certificate Theft and Replay

**SPIFFE/SPIRE Attack Scenarios:**

1. **Workload impersonation**: Can a rogue process obtain an SVID by claiming to be another workload?
   - Test node attestation weakness
   - Test workload attestation selector specificity
   - Attempt to run a malicious process with the same attributes as the target workload

2. **SVID theft**: Extract short-lived certificates from memory
   - Check SVID TTL — shorter is better (1 hour recommended, test with shorter)
   - Verify that stolen SVID becomes useless after rotation
   - Test if the SPIRE agent socket is accessible to non-authorized processes

3. **CA compromise**: If the SPIRE Server root CA is compromised, all trust is broken
   - Test CA key storage (should be in HSM or KMS)
   - Verify CA certificate rotation procedures
   - Test upstream CA chain validation

### 10.7 Evaluating Segmentation Effectiveness

**Microsegmentation Test Matrix:**

```
┌──────────────────────────────────────────────────────────────────┐
│  FROM \ TO    │ Payment │ Database │ Frontend │ Monitoring │ DNS │
├───────────────┼─────────┼──────────┼──────────┼────────────┼─────┤
│ Payment       │   N/A   │  ALLOW   │  DENY    │   ALLOW    │ALLOW│
│ Database      │  DENY   │   N/A    │  DENY    │   ALLOW    │ALLOW│
│ Frontend      │ ALLOW   │  DENY    │   N/A    │   ALLOW    │ALLOW│
│ Monitoring    │ ALLOW   │  ALLOW   │  ALLOW   │    N/A     │ALLOW│
│ Attacker Pod  │  DENY   │  DENY    │  DENY    │   DENY     │ ?   │
└───────────────┴─────────┴──────────┴──────────┴────────────┴─────┘

Test: Can an attacker pod communicate with ANY production service?
Expected: ALL DENY (including DNS, which is a common gap)
```

**Tooling for Segmentation Testing:**
- `nmap` / `masscan` for port discovery from within segments
- `kubectl exec` into pods to test connectivity
- Custom tools that attempt mTLS with stolen/forged certificates
- `tcpdump` on pod interfaces to verify encryption
- DNS exfiltration tools (iodine, dnscat2) to test DNS policy gaps

### 10.8 Red Team Methodology for ZTA Environments

**Objective-Based Red Team Approach:**

The red team should pursue realistic adversary objectives, not just technical exploits:

**Scenario 1 — Credential Theft → Lateral Movement:**
1. Phish a developer (test phishing resistance of FIDO2)
2. Compromise their workstation (test EDR + device trust revocation)
3. Extract session tokens (test token binding)
4. Use tokens from attacker infrastructure (test impossible travel + CAE)
5. Access source code repository (test data classification + DLP)
6. Inject backdoor in CI/CD (test supply chain controls)

**Scenario 2 — Supply Chain → Internal:**
1. Compromise a third-party integration (test vendor access controls)
2. Use vendor's API credentials (test scope restrictions)
3. Enumerate internal services reachable via vendor path (test segmentation)
4. Attempt to escalate from limited vendor access to broad internal access
5. Test whether vendor sessions are monitored with same UEBA as internal

**Scenario 3 — Insider Threat:**
1. Operate as a legitimate user with valid credentials and managed device
2. Slowly escalate access requests (test identity governance reviews)
3. Accumulate permissions over time (test periodic access certifications)
4. Attempt bulk data export (test DLP and volumetric anomaly detection)
5. Test exfiltration via approved channels (email, cloud storage, USB)

**Reporting for ZTA Red Teams:**

```markdown
## Finding: Session Token Not Device-Bound

**CVSS**: 7.5 (High)
**CWE**: CWE-384 (Session Fixation) / CWE-294 (Authentication Bypass by Capture-replay)

**Description**: OAuth access tokens issued by the corporate IdP are not bound
to the device that performed authentication. A stolen token can be replayed
from an attacker-controlled device.

**Reproduction**:
1. Authenticate on managed device (Device-A, compliant)
2. Extract access token from browser process memory
3. Replay token from unmanaged device (Device-B, non-compliant)
4. Observe: access succeeds on Device-B without device posture check

**Impact**: An attacker who steals a session token (via malware, XSS, or
physical access) can bypass device trust controls entirely.

**Remediation**:
- Implement DPoP (Demonstrating Proof-of-Possession) for all OAuth flows
- Enable Continuous Access Evaluation (CAE) with token binding
- Reduce token lifetime to 15 minutes with silent refresh
- Detect token use from non-originating device IP/fingerprint

**Evidence**: [screenshot, packet capture, log entries — UTC timestamps]
```

---

## 11. Zero Trust per OT/IoT e Sistemi Industriali

### 11.1 La Sfida della Convergenza IT/OT

L'integrazione crescente tra reti IT e ambienti di tecnologia operativa (OT) ha dissolto il tradizionale isolamento dei sistemi industriali. Impianti SCADA, PLC (Programmable Logic Controller), HMI (Human-Machine Interface), DCS (Distributed Control System) e sensori IIoT (Industrial Internet of Things) sono ora interconnessi con reti aziendali, cloud e servizi remoti di manutenzione. Questa convergenza espande enormemente la superficie di attacco, rendendo obsoleta la strategia tradizionale basata sull'air gap.

Le peculiarità dell'ambiente OT rendono l'adozione del modello Zero Trust significativamente più complessa rispetto all'IT tradizionale:

- **Priorità alla disponibilità**: nei sistemi industriali, l'uptime è critico. Un blocco di accesso errato può causare arresti di produzione con danni economici enormi o rischi per la sicurezza fisica
- **Sistemi legacy**: molti dispositivi OT operano con sistemi operativi obsoleti (Windows XP, Windows CE, firmware proprietari) che non supportano agenti di sicurezza moderni, protocolli di autenticazione contemporanei o crittografia aggiornata
- **Cicli di vita estesi**: i dispositivi OT hanno cicli di vita di 15-25 anni, molto più lunghi rispetto ai 3-5 anni tipici dell'IT. La sostituzione per motivi di sicurezza è spesso economicamente proibitiva
- **Protocolli proprietari**: Modbus, DNP3, OPC UA, PROFINET e altri protocolli industriali non sono stati progettati con la sicurezza in mente e non supportano nativamente autenticazione o crittografia
- **Mancanza di inventario**: la maggior parte delle organizzazioni non dispone di un inventario completo e aggiornato degli asset OT, rendendo impossibile applicare politiche Zero Trust senza una fase preliminare di discovery

### 11.2 Modello Purdue e Micro-Segmentazione Industriale

Il modello Purdue (ISA-95/IEC 62443) definisce una gerarchia a livelli per le reti industriali. L'applicazione della micro-segmentazione Zero Trust segue questa struttura, con zone di fiducia granulari a ogni livello:

```
┌─────────────────────────────────────────────────────────────────────┐
│  LIVELLO 5 — Rete Aziendale (Enterprise Zone)                       │
│  ERP, email, servizi cloud                                          │
├─────────────────────────────────────────────────────────────────────┤
│  LIVELLO 4 — DMZ IT/OT (Industrial DMZ)                             │
│  Data historian mirror, jump server, patch management                │
│  *** PUNTO DI SEPARAZIONE CRITICO — FIREWALL BIDIREZIONALE ***      │
├─────────────────────────────────────────────────────────────────────┤
│  LIVELLO 3 — Operations Management                                   │
│  MES, data historian, application server OT                          │
├─────────────────────────────────────────────────────────────────────┤
│  LIVELLO 2 — Supervisory Control                                     │
│  SCADA, HMI, Engineering Workstation                                 │
├─────────────────────────────────────────────────────────────────────┤
│  LIVELLO 1 — Basic Control                                           │
│  PLC, RTU, DCS controller                                            │
├─────────────────────────────────────────────────────────────────────┤
│  LIVELLO 0 — Process                                                 │
│  Sensori, attuatori, dispositivi di campo                            │
└─────────────────────────────────────────────────────────────────────┘
```

**Strategia di micro-segmentazione per livello:**

| Livello | Strategia Zero Trust | Strumenti |
|---------|---------------------|-----------|
| Livello 5-4 | Micro-segmentazione standard IT, IAP, ZTNA | Zscaler, Palo Alto Prisma, Cloudflare Access |
| Livello 3 | Gateway applicativo con ispezione protocolli OT, allow-list rigorosa | Claroty, Nozomi Networks, Fortinet FortiGate |
| Livello 2 | Firewall industriale con deep packet inspection per protocolli SCADA, segmentazione per cella | Cisco ISA-3000, Fortinet FortiGate Rugged |
| Livello 1-0 | Segmentazione fisica e logica per cella, monitoraggio passivo (non inline) | Network TAP, Nozomi Guardian, Claroty CTD |

### 11.3 Guida CISA: Adattamento dei Principi Zero Trust all'OT

Nel 2025, CISA ha pubblicato la guida "Adapting Zero Trust Principles to Operational Technology", che delinea un approccio pragmatico per applicare i principi Zero Trust in ambienti con vincoli legacy, visibilità limitata e requisiti stringenti di uptime.

**Principi chiave della guida CISA per OT:**

1. **Inventario e visibilità passiva**: prima di qualsiasi enforcement, stabilire un inventario completo degli asset OT e mappare tutti i flussi di comunicazione. Utilizzare tecnologie passive (port mirroring, network TAP) per evitare impatti sulla produzione
2. **Segmentazione progressiva**: iniziare con macro-segmentazione (separazione IT/OT) e procedere gradualmente verso la micro-segmentazione per cella produttiva
3. **Autenticazione dove possibile**: applicare MFA e autenticazione forte per l'accesso remoto ai sistemi OT (jump server, VPN industriali). Per i dispositivi legacy che non supportano autenticazione moderna, utilizzare gateway di mediazione
4. **Monitoraggio continuo senza enforcement inline**: nei livelli 0-2, preferire il monitoraggio passivo con alerting rispetto al blocco attivo, per evitare impatti sulla produzione
5. **Incident response specifico per OT**: i playbook di risposta devono considerare la sicurezza fisica e i processi industriali, non solo la sicurezza informatica

### 11.4 Accesso Remoto Zero Trust per OT

L'accesso remoto ai sistemi OT è uno dei vettori di attacco più critici. La sostituzione delle VPN tradizionali con soluzioni ZTNA specifiche per OT è una priorità:

**Architettura di accesso remoto sicuro per OT:**

```
┌──────────────┐                    ┌─────────────────────┐
│  Tecnico     │                    │  Broker ZTNA OT     │
│  Remoto      │── Autenticazione ─▶│  (Claroty SRA,      │
│  (con MFA)   │   forte + device   │   Dispel, Cyolo)    │
│              │   posture check    │                     │
└──────────────┘                    └─────────┬───────────┘
                                              │
                                    ┌─────────▼───────────┐
                                    │  Session Recording   │
                                    │  + Granular ACL      │
                                    │  (solo asset         │
                                    │   autorizzati)       │
                                    └─────────┬───────────┘
                                              │
                                    ┌─────────▼───────────┐
                                    │  Asset OT target    │
                                    │  (PLC, HMI, SCADA)  │
                                    └─────────────────────┘
```

**Requisiti per l'accesso remoto ZT in OT:**
- Autenticazione multi-fattore obbligatoria con token hardware per operazioni critiche
- Registrazione completa della sessione (video recording) con ricerca per parole chiave
- Limitazione temporale dell'accesso (Just-in-Time, massimo 4 ore per sessione)
- Approvazione multi-livello per accesso a sistemi Safety Instrumented Systems (SIS)
- Verifica della postura del dispositivo del tecnico remoto prima dell'accesso
- Isolamento del traffico OT dal traffico IT durante le sessioni remote
- Kill switch immediato per terminare sessioni in caso di anomalie

### 11.5 IoT e Zero Trust: Dispositivi a Risorse Limitate

I dispositivi IoT presentano sfide uniche per l'implementazione Zero Trust, a causa delle risorse computazionali limitate e della diversità di protocolli:

**Strategie di mitigazione per IoT:**

| Sfida IoT | Approccio Zero Trust | Implementazione |
|-----------|---------------------|-----------------|
| CPU/RAM limitata (nessun agente) | Gateway di mediazione | IoT gateway con profilo SPIFFE per ogni dispositivo dietro il gateway |
| Protocolli non standard (MQTT, CoAP, ZigBee) | Protocol broker con policy enforcement | AWS IoT Core, Azure IoT Hub con regole di routing |
| Volume elevato di dispositivi | Identità basata su certificati X.509 con provisioning automatico | PKI dedicata IoT, EST (Enrollment over Secure Transport) |
| Firmware non aggiornabile | Segmentazione di rete rigorosa | VLAN dedicata per dispositivi legacy, regole di comunicazione allow-list |
| Comunicazione machine-to-machine | Autenticazione reciproca leggera | TLS-PSK (Pre-Shared Key), DTLS per protocolli UDP |

### 11.6 Casi di Studio: Attacchi a Infrastrutture OT

L'urgenza dell'adozione Zero Trust in OT è evidenziata da incidenti reali:

| Incidente | Anno | Vettore | Impatto | Controllo ZT che avrebbe mitigato |
|-----------|------|---------|---------|-----------------------------------|
| Colonial Pipeline | 2021 | VPN compromessa, password riutilizzata | Arresto distribuzione carburante East Coast USA, 5 giorni | MFA su VPN, segmentazione IT/OT, ZTNA |
| Oldsmar Water Treatment | 2021 | TeamViewer non protetto, accesso remoto | Tentativo di avvelenamento acqua potabile (NaOH) | Accesso remoto ZT con MFA, approvazione multi-livello |
| TRITON/TRISIS | 2017 | Movimento laterale IT→OT, firmware SIS modificato | Compromissione Safety Instrumented System | Micro-segmentazione IT/OT, monitoraggio SIS dedicato |
| Industroyer2 | 2022 | Spear phishing → movimento laterale verso sottostazioni | Tentativo di blackout rete elettrica ucraina | Segmentazione per sottostazione, monitoraggio IEC 104 |
| MOVEit + OT exposure | 2023 | Supply chain via file transfer | Esfiltrazione dati industriali sensibili | ZTNA per file transfer, DLP, segmentazione dati |

---

## 12. Conformità Normativa e Zero Trust

### 12.1 Panorama Regolatorio Europeo

Il quadro normativo europeo in materia di cybersecurity ha subito una trasformazione radicale nel periodo 2024-2026, con l'entrata in vigore di molteplici regolamenti e direttive che convergono verso i principi fondamentali del modello Zero Trust. L'architettura Zero Trust non è più solo una best practice raccomandata, ma sta diventando un requisito implicito o esplicito di conformità normativa.

**Timeline normativa chiave:**

```
2024        2025                    2026
 │           │                       │
 ├── NIS2    ├── DORA applicabile    ├── NIS2 compliance
 │  recepimento  (17 gen 2025)      │  deadline (ott 2026)
 │  nazionale    │                   │
 │           ├── EU AI Act           ├── CRA (Cyber Resilience
 │           │  (parziale)           │  Act) piena applicazione
 │           │                       │
 │           ├── CISA ZTA            ├── DoD ZT Strategy 2.0
 │           │  Implementation       │
 │           │  report               │
```

### 12.2 NIS2 e Zero Trust

La Direttiva NIS2 (Network and Information Security Directive 2) estende significativamente l'ambito della cybersecurity obbligatoria nell'UE, coprendo 18 settori critici e imponendo requisiti tecnici e organizzativi stringenti. I principi Zero Trust si allineano direttamente con i requisiti NIS2:

| Requisito NIS2 (Art. 21) | Principio Zero Trust Corrispondente | Implementazione ZTA |
|---------------------------|-------------------------------------|---------------------|
| Politiche di analisi dei rischi | Assume Breach, valutazione continua | Risk scoring engine, UEBA |
| Gestione degli incidenti | Monitoraggio continuo, risposta automatizzata | SIEM/SOAR integrato con segnali ZTA |
| Continuità operativa | Fail-closed con break-glass, ridondanza PA/PE | HA del control plane, cache decisionale locale |
| Sicurezza della supply chain | Accesso vendor Zero Trust, SPIFFE per workload | ZTNA per terze parti, attestazione workload |
| Sicurezza acquisizione e sviluppo | CI/CD sicuro, SBOM, signed images | Pipeline hardening, admission controller |
| Pratiche di igiene informatica | MFA, least privilege, segmentazione | Identity foundation, device trust, micro-seg |
| Crittografia | Encryption at rest/in transit/in use | mTLS everywhere, KMS, confidential computing |
| Controllo degli accessi | Identity-centric security, PAM | IdP centralizzato, JIT access, access review |
| Autenticazione multi-fattore | FIDO2, passkey, adaptive auth | Phishing-resistant MFA, continuous auth |

**Sanzioni NIS2 per non conformità:**
- Entità essenziali: fino a 10 milioni di euro o 2% del fatturato mondiale annuo
- Entità importanti: fino a 7 milioni di euro o 1,4% del fatturato mondiale annuo
- Responsabilità personale del management per mancata supervisione

### 12.3 DORA e Zero Trust per il Settore Finanziario

Il Digital Operational Resilience Act (DORA) è applicabile dal 17 gennaio 2025 e impone requisiti specifici di resilienza digitale a banche, compagnie assicurative, società di investimento, FinTech e i loro fornitori ICT critici.

**Mapping DORA → Zero Trust:**

| Pilastro DORA | Requisito Specifico | Controllo Zero Trust |
|---------------|--------------------|--------------------|
| ICT Risk Management (Cap. II) | Framework di gestione del rischio ICT con politiche di sicurezza | Policy Engine con trust algorithm, risk scoring continuo |
| Incident Reporting (Cap. III) | Classificazione e notifica incidenti entro tempi definiti | SIEM con correlazione segnali ZTA, alerting automatizzato |
| Resilience Testing (Cap. IV) | TLPT (Threat-Led Penetration Testing) obbligatorio | Pentest specifico per trust boundary (Sezione 10 di questo documento) |
| Third-Party Risk (Cap. V) | Gestione dei rischi da fornitori ICT critici | ZTNA per vendor, segmentazione accesso terze parti, audit trail |
| Information Sharing (Cap. VI) | Condivisione intelligence sulle minacce | Threat intel feed integrato nel trust algorithm |

**Requisiti DORA specifici che richiedono controlli Zero Trust:**
- Identificazione e classificazione di tutti gli asset e le funzioni ICT critiche (inventario completo richiesto per ZTA)
- Meccanismi di autenticazione forte per tutti gli accessi ai sistemi critici
- Crittografia per dati in transito e a riposo
- Capacità di rilevamento anomalie in tempo reale
- Procedure di risposta agli incidenti con tempi di notifica di 4 ore (iniziale) e 72 ore (intermedia)
- Test di resilienza basati su scenari di minaccia realistici (TLPT), che devono includere test dei confini di fiducia Zero Trust

### 12.4 GDPR e Zero Trust: Protezione dei Dati per Design

Il GDPR (Regolamento Generale sulla Protezione dei Dati, in vigore dal 2018) richiede esplicitamente la "protezione dei dati by design e by default" (Articolo 25). L'architettura Zero Trust è l'implementazione naturale di questo principio:

**Allineamento GDPR-ZTA:**

- **Minimizzazione dei dati (Art. 5.1.c)**: il principio del least privilege ZTA garantisce che ogni soggetto acceda solo ai dati strettamente necessari per la funzione svolta
- **Limitazione dell'accesso (Art. 25)**: la micro-segmentazione e l'autorizzazione granulare a livello di risorsa implementano il controllo di accesso richiesto
- **Registrazione degli accessi (Art. 30)**: il logging completo di ogni decisione di accesso del Policy Engine fornisce l'audit trail richiesto dal GDPR
- **Diritto alla portabilità e cancellazione (Art. 17, 20)**: la classificazione dei dati ZTA e il data governance supportano l'identificazione e la gestione dei dati personali
- **Notifica violazione (Art. 33-34)**: il monitoraggio continuo e la correlazione UEBA consentono il rilevamento tempestivo delle violazioni
- **Trasferimenti internazionali (Art. 44-49)**: la crittografia end-to-end e il controllo granulare degli accessi supportano la conformità per i trasferimenti verso paesi terzi

### 12.5 EU AI Act e Zero Trust per Sistemi di Intelligenza Artificiale

L'EU AI Act, parzialmente applicabile dal 2025, introduce classificazioni di rischio per i sistemi AI e impone requisiti di sicurezza che si intersecano con l'architettura Zero Trust:

**Sfide emergenti — Agenti AI e Zero Trust:**

La proliferazione di sistemi AI agentici nel 2025-2026 introduce sfide di sicurezza nuove. Gli agenti autonomi possono eseguire catene di tool call, generare sub-agenti o interagire con sistemi esterni in modi che aggirano i confini tradizionali di identità utente.

**Principi Zero Trust per sistemi AI:**

| Aspetto AI | Rischio | Controllo Zero Trust |
|-----------|---------|---------------------|
| Identità dell'agente | Agente che opera con credenziali dell'utente dopo la disconnessione | Identità workload dedicata per ogni agente AI (SPIFFE), TTL breve |
| Catena di tool call | Escalation di privilegi attraverso chiamate concatenate | Autorizzazione per-call, non per-sessione; scope limitato per tool |
| Dati di training | Accesso a dati sensibili per fine-tuning | Data classification + DLP prima dell'ingestion nel modello |
| Output del modello | Generazione di dati sensibili o credenziali | Output filtering, sanitizzazione, sandbox per esecuzione codice |
| Supply chain AI | Modelli pre-addestrati con backdoor o avvelenamento dei dati | Attestazione modello, SBOM per modelli ML, verifica provenienza |

### 12.6 Matrice di Conformità Integrata

La seguente matrice mostra come un'implementazione Zero Trust completa soddisfi simultaneamente i requisiti di molteplici framework normativi:

```
┌────────────────────────┬───────┬──────┬──────┬────────┬─────────┐
│  Controllo Zero Trust  │ NIS2  │ DORA │ GDPR │ AI Act │ISO27001 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ MFA per tutti gli      │  ✓    │  ✓   │  ✓   │   —    │  A.8.5  │
│ accessi                │       │      │      │        │         │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Micro-segmentazione    │  ✓    │  ✓   │  —   │   —    │  A.8.22 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Crittografia E2E       │  ✓    │  ✓   │  ✓   │   ✓    │  A.8.24 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Monitoraggio continuo  │  ✓    │  ✓   │  ✓   │   ✓    │  A.8.16 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Logging e audit trail  │  ✓    │  ✓   │  ✓   │   ✓    │  A.8.15 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Gestione incidenti     │  ✓    │  ✓   │  ✓   │   —    │  A.5.24 │
│ automatizzata          │       │      │      │        │         │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Classificazione dati   │  —    │  ✓   │  ✓   │   ✓    │  A.5.12 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Test di penetrazione   │  ✓    │  ✓   │  —   │   —    │  A.8.8  │
│ dei confini di fiducia │       │      │      │        │         │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ Gestione terze parti   │  ✓    │  ✓   │  ✓   │   ✓    │  A.5.19 │
├────────────────────────┼───────┼──────┼──────┼────────┼─────────┤
│ PAM e JIT access       │  ✓    │  ✓   │  ✓   │   —    │  A.8.2  │
└────────────────────────┴───────┴──────┴──────┴────────┴─────────┘
```

---

## 13. AI e Machine Learning nella Zero Trust Architecture

### 13.1 Evoluzione verso la Zero Trust Guidata dall'AI

L'integrazione dell'intelligenza artificiale e del machine learning nell'architettura Zero Trust rappresenta l'evoluzione più significativa del modello nel periodo 2025-2026. I sistemi tradizionali di valutazione della fiducia basati su regole statiche non possono scalare con la complessità crescente degli ambienti moderni. L'AI trasforma il trust algorithm da un sistema deterministico a un sistema adattivo in tempo reale.

**Evoluzione dell'approccio di valutazione:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  GENERAZIONE 1 (2014-2019): Rule-Based                              │
│  • Regole statiche IF/THEN nel Policy Engine                        │
│  • Soglie fisse per risk score                                      │
│  • Alta percentuale di falsi positivi                               │
│  • Aggiornamento manuale delle policy                               │
├─────────────────────────────────────────────────────────────────────┤
│  GENERAZIONE 2 (2019-2024): ML-Augmented                           │
│  • Baseline comportamentale per utente (UEBA)                       │
│  • Anomaly detection con modelli statistici                         │
│  • Risk scoring semi-dinamico                                       │
│  • Riduzione falsi positivi del 40-60%                              │
├─────────────────────────────────────────────────────────────────────┤
│  GENERAZIONE 3 (2024-2026): AI-Native                              │
│  • Policy Engine con modelli ML integrati                           │
│  • Analisi comportamentale in tempo reale multi-pilastro            │
│  • Risk scoring continuo con aggiornamento sub-secondo              │
│  • Risposta automatizzata guidata dall'AI                           │
│  • Adaptive access control con personalizzazione per utente         │
│  • Riduzione falsi positivi del 76% rispetto a Gen 1                │
├─────────────────────────────────────────────────────────────────────┤
│  GENERAZIONE 4 (2026+): Autonomous ZTA                              │
│  • Self-healing security policies                                   │
│  • Generative AI per threat simulation e red team                   │
│  • Digital twin della rete per policy testing                       │
│  • Zero-shot anomaly detection                                      │
│  • Continuous compliance verification automatizzata                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.2 Machine Learning per il Trust Algorithm

L'applicazione del ML al trust algorithm migliora ogni pilastro della valutazione:

**Identity Analytics con ML:**
- **Rilevamento credenziali compromesse**: modelli di classificazione addestrati su pattern di utilizzo anomalo delle credenziali, con capacità di identificare account compromessi entro minuti dall'uso iniziale da parte dell'attaccante
- **Adaptive authentication**: il livello di autenticazione richiesto si adatta dinamicamente al profilo di rischio calcolato dal modello ML, riducendo la frizione per utenti a basso rischio e intensificando i controlli per sessioni anomale
- **Rilevamento insider threat**: analisi longitudinale del comportamento con modelli di serie temporali che identificano la transizione graduale dal comportamento normale a quello malevolo

**Device Trust con ML:**
- **Predizione compliance drift**: modelli predittivi che identificano dispositivi a rischio di non conformità prima che diventino effettivamente non conformi, consentendo la remediation proattiva
- **Anomaly detection su traffico di rete del dispositivo**: analisi del traffico generato dal dispositivo con autoencoders per identificare comportamenti indicativi di compromissione (beaconing, data staging, C2 communication)
- **Firmware integrity scoring**: valutazione continua dell'integrità del firmware basata su confronto con baseline conosciute

**Behavioral Analytics con Deep Learning:**

```python
class DeepBehaviorAnalyzer:
    """
    Analizzatore comportamentale basato su deep learning
    per la valutazione continua della fiducia nelle sessioni Zero Trust.
    """

    def __init__(self):
        # Autoencoder per rilevamento anomalie
        self.behavior_autoencoder = load_model("behavior_ae_v3.h5")
        # Modello di serie temporali per pattern analysis
        self.temporal_model = load_model("lstm_behavior_v2.h5")
        # Soglia di anomalia adattiva per utente
        self.anomaly_thresholds = load_user_thresholds()

    def evaluate_session_behavior(
        self, session: SessionData
    ) -> BehaviorScore:
        """
        Valuta il comportamento della sessione in tempo reale.
        Restituisce un punteggio 0-100 (0 = normale, 100 = altamente anomalo).
        """
        # Feature extraction dalla sessione corrente
        features = self._extract_features(session)

        # Ricostruzione con autoencoder
        reconstruction = self.behavior_autoencoder.predict(features)
        reconstruction_error = calculate_mse(features, reconstruction)

        # Analisi temporale con LSTM
        temporal_features = self._get_temporal_context(
            session.user_id, window_hours=24
        )
        temporal_anomaly = self.temporal_model.predict(temporal_features)

        # Confronto con peer group
        peer_baseline = self._get_peer_baseline(session.user_role)
        peer_deviation = calculate_deviation(features, peer_baseline)

        # Score composito con pesi adattivi
        user_threshold = self.anomaly_thresholds.get(
            session.user_id, DEFAULT_THRESHOLD
        )

        composite_score = weighted_combine(
            reconstruction_error * 0.40,
            temporal_anomaly * 0.35,
            peer_deviation * 0.25
        )

        return BehaviorScore(
            value=normalize(composite_score, user_threshold),
            confidence=self._calculate_confidence(session),
            contributing_factors=self._explain_score(
                reconstruction_error, temporal_anomaly, peer_deviation
            )
        )

    def _extract_features(self, session: SessionData) -> np.ndarray:
        """Estrae feature dal comportamento della sessione."""
        return np.array([
            session.resources_accessed_count,
            session.unique_resource_types,
            session.data_volume_bytes,
            session.time_since_last_access_seconds,
            session.actions_per_minute,
            session.read_write_ratio,
            session.privilege_escalation_attempts,
            session.failed_access_count,
            session.geo_distance_from_baseline_km,
            session.network_type_risk_score,
            session.hour_of_day_normalized,
            session.day_of_week_normalized,
        ])
```

### 13.3 AI per la Risposta Automatizzata agli Incidenti

La risposta automatizzata guidata dall'AI è fondamentale per operare alla velocità degli attacchi moderni. I tempi di risposta manuale (minuti o ore) non sono accettabili quando un attaccante può esfiltrare dati critici in secondi:

**Pipeline di risposta automatizzata ZTA:**

```
┌─────────────────────────────────────────────────────────────────────┐
│  1. DETECTION (< 1 secondo)                                         │
│     ML anomaly detection → trust score drop                         │
│     Segnale: utente admin, accesso bulk a database HR               │
│     Trust score: 85 → 25 (soglia = 50)                              │
├─────────────────────────────────────────────────────────────────────┤
│  2. TRIAGE (< 5 secondi)                                            │
│     AI classifier: probabilità insider threat = 0.78                │
│     Confronto con pattern noti: match con data exfiltration         │
│     Confidence: alta                                                │
├─────────────────────────────────────────────────────────────────────┤
│  3. CONTAINMENT (< 10 secondi)                                      │
│     Azione automatica:                                              │
│     • Riduzione scope sessione a read-only                          │
│     • Blocco download e copia dati                                  │
│     • Attivazione DLP enhanced monitoring                           │
│     • Step-up auth con hardware token                               │
├─────────────────────────────────────────────────────────────────────┤
│  4. ESCALATION (< 30 secondi)                                       │
│     • Alert SOC Tier 2 con contesto completo                        │
│     • Timeline automatica degli eventi                              │
│     • Raccomandazione AI per azioni aggiuntive                      │
│     • Apertura ticket con severity calcolata                        │
├─────────────────────────────────────────────────────────────────────┤
│  5. FEEDBACK LOOP (continuo)                                         │
│     • Analista SOC conferma/rivede la decisione AI                  │
│     • Il modello ML si aggiorna con il feedback (reinforcement)     │
│     • Le soglie si calibrano automaticamente                        │
│     • I falsi positivi riducono la fiducia nel modello              │
└─────────────────────────────────────────────────────────────────────┘
```

### 13.4 Sicurezza dell'AI all'Interno della ZTA

Non solo l'AI potenzia la ZTA, ma la ZTA deve proteggere i sistemi AI stessi. I modelli AI sono asset di alto valore che richiedono controlli Zero Trust dedicati:

**Framework di protezione per workload AI:**

- **Accesso ai dati di training**: classificazione automatica dei dataset, accesso least privilege, audit trail completo di ogni accesso ai dati utilizzati per l'addestramento
- **Protezione del modello**: i pesi del modello sono asset critici. Accesso tramite PAM, storage crittografato, integrità verificata con hash firmati
- **Inferenza sicura**: le richieste al modello devono essere autenticate e autorizzate. Rate limiting per prevenire model extraction e membership inference attacks
- **Pipeline MLOps Zero Trust**: ogni fase della pipeline (data ingestion, training, validation, deployment) è un confine di fiducia con autenticazione e autorizzazione granulare

### 13.5 Sfide e Rischi dell'AI nella ZTA

L'adozione dell'AI nella ZTA introduce rischi specifici che devono essere gestiti:

| Rischio | Descrizione | Mitigazione |
|---------|-------------|-------------|
| Avvelenamento del modello (model poisoning) | Un attaccante manipola i dati di training per alterare le decisioni del trust algorithm | Validazione dei dati di training, anomaly detection sui dati di input, modelli ensemble |
| Evasione adversariale | L'attaccante modifica il proprio comportamento per rimanere sotto le soglie di detection | Modelli robusti con adversarial training, feature engineering resistente all'evasione |
| Bias nei dati | Il modello penalizza sistematicamente certi gruppi di utenti legittimi | Audit regolare per bias, diverse team nel development, fairness constraints |
| Opacità delle decisioni | Le decisioni AI non sono spiegabili, rendendo difficile l'audit e il debugging | Explainable AI (SHAP, LIME), logging dei fattori contributivi per ogni decisione |
| Dipendenza eccessiva | L'organizzazione si affida completamente all'AI senza supervisione umana | Human-in-the-loop per decisioni critiche, override manuale sempre disponibile |
| Latenza computazionale | I modelli complessi introducono latenza inaccettabile nel flusso di accesso | Edge inference, model optimization (quantization, pruning), caching delle decisioni |

---

## 14. Confronto Vendor e Ecosistema Commerciale

### 14.1 Panoramica del Mercato Zero Trust 2025-2026

Il mercato globale della sicurezza Zero Trust ha raggiunto 38,6 miliardi di dollari nel 2025, con una crescita annuale prevista del 16-18% fino al 2030. L'adozione dell'architettura Zero Trust nelle aziende è passata dal 24% nel 2023 al 41% nel 2025, con il restante 59% che rappresenta un ciclo di deployment pluriennale.

I fattori di crescita principali includono:
- Obblighi normativi (NIS2, DORA, mandati federali USA)
- Migrazione verso ambienti cloud ibridi e multi-cloud
- Crescita del lavoro remoto e ibrido come modello permanente
- Aumento della sofisticazione degli attacchi (ransomware as a service, AI-powered attacks)
- Obsolescenza delle VPN tradizionali come meccanismo di accesso remoto

### 14.2 Confronto Platform ZTNA e SASE

Le piattaforme ZTNA (Zero Trust Network Access) e SASE (Secure Access Service Edge) rappresentano la convergenza di networking e sicurezza in un'unica architettura cloud-delivered:

| Vendor | Piattaforma | Architettura | Punti di Forza | Limitazioni | Prezzo Indicativo |
|--------|-------------|-------------|----------------|-------------|-------------------|
| **Zscaler** | Zero Trust Exchange | Cloud-native proxy, 150+ data center globali | SSE leader da 15+ anni, 40% Fortune 500, eccellente per traffico web/SaaS | Non gestisce endpoint, richiede integrazione EDR separata | $$$$ |
| **Palo Alto Networks** | Prisma Access + Prisma Cloud | SASE completo con SD-WAN integrato | Piattaforma più completa (ZTNA + CASB + DLP + FWaaS), forte AI/ML | Complessità di configurazione, costo elevato | $$$$ |
| **Cloudflare** | Cloudflare One | Edge network globale, L3-L7 | Deployment rapido, eccellente per applicazioni web, pricing competitivo | Meno maturo per OT/legacy, funzionalità enterprise in evoluzione | $$ |
| **Microsoft** | Entra ID + Defender + Intune | Nativo M365/Azure, Conditional Access | Integrazione profonda con ecosistema Microsoft, bundle licensing vantaggioso | Lock-in Microsoft, meno efficace in ambienti multi-cloud | $$-$$$ |
| **CrowdStrike** | Falcon Zero Trust | Endpoint-centric con identity protection | Best-in-class EDR, threat intelligence superiore, Falcon Identity Threat Detection | Non è un broker ZTNA per app private da solo, richiede partnership | $$$ |
| **Cisco** | Secure Access (ex-Duo + Umbrella) | Hybrid (on-prem + cloud) | Forte in ambienti enterprise legacy, integrazione networking Cisco | Transizione in corso da prodotti legacy, UX frammentata | $$$ |
| **Netskope** | Netskope One | Cloud-native SASE | Leader CASB, eccellente protezione dati e DLP, inline decryption | Minor copertura endpoint rispetto ai competitor | $$$ |

### 14.3 Confronto Piattaforme di Micro-Segmentazione

La micro-segmentazione è il pilastro della rete nella ZTA. Il mercato si è evoluto significativamente con l'emergere di approcci agentless accanto alle soluzioni agent-based tradizionali:

| Vendor | Prodotto | Approccio | Copertura | Differenziatori |
|--------|----------|-----------|-----------|-----------------|
| **Illumio** | Zero Trust Segmentation Platform | Agent-based (VEN) | Data center, cloud, endpoint | Mappatura dipendenze real-time, policy generation automatica, visualizzazione Illumination |
| **Akamai (Guardicore)** | Guardicore Segmentation | Agent-based | Data center, cloud | Deep process-level visibility, threat hunting integrato, policy staging avanzato |
| **Cisco** | Secure Workload (ex-Tetration) | Agent-based | Data center, cloud, OT | Enforcement su OS firewall nativo (nftables, WFP), integrazione networking Cisco |
| **Elisity** | Identity-Based Microsegmentation | Agentless (network-based) | Campus, IoT, OT | Non richiede agente, ideale per dispositivi unmanaged, discovery automatica |
| **ColorTokens** | Xshield | Agent + agentless hybrid | Multi-cloud, data center | Approccio ibrido, forte in ambienti eterogenei, compliance mapping integrato |
| **Zero Networks** | Segment | Agentless (MFA-based) | Data center, cloud | MFA per connessioni admin, approccio innovativo Just-in-Time, zero agent |
| **Zscaler** | Workload Segmentation | Agent-based | Cloud-native | Integrazione con Zscaler Zero Trust Exchange, ideale per carichi cloud-native |

### 14.4 Confronto Identity Provider per Zero Trust

| Provider | Punti di Forza ZTA | Continuous Access Evaluation | Device Trust Nativo | PAM Integrato |
|----------|--------------------|------------------------------|--------------------|----|
| **Microsoft Entra ID** | Conditional Access engine più maturo, CAE, token protection, cross-tenant | Sì (CAE nativo) | Sì (Intune + Endpoint Manager) | No (richiede CyberArk/BeyondTrust) |
| **Okta** | IdP-agnostic, catalogo app esteso, Identity Threat Protection with Okta AI | Sì (Continuous Auth) | Sì (Okta Device Trust) | Parziale (Okta Privileged Access) |
| **Ping Identity** | Deployment ibrido, orchestrazione DaVinci, API security | Sì (PingOne Authorize) | Tramite integrazioni | No |
| **CyberArk Identity** | Combinazione IdP + PAM in un'unica piattaforma | Parziale | Tramite integrazioni | Sì (nativo) |
| **Google Workspace** | BeyondCorp nativo, Context-Aware Access, endpoint verification | Sì | Sì (Chrome Enterprise) | No |

### 14.5 Architettura SASE e Convergenza con Zero Trust

SASE (Secure Access Service Edge) rappresenta la convergenza di networking wide-area e sicurezza di rete in un unico servizio cloud-delivered. Nel 2025-2026, la convergenza SASE-ZTA è diventata il modello dominante per le organizzazioni che modernizzano la propria infrastruttura:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ARCHITETTURA SASE + ZERO TRUST                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              SSE (Security Service Edge)                    │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐ │     │
│  │  │  ZTNA   │ │  CASB   │ │  SWG    │ │  FWaaS          │ │     │
│  │  │ (accesso│ │ (cloud  │ │ (web    │ │ (firewall       │ │     │
│  │  │ privato)│ │ broker) │ │ gateway)│ │  as a service)  │ │     │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────────────┘ │     │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────────────────────────┐ │     │
│  │  │  DLP    │ │ Sandbox │ │  Threat Intelligence        │ │     │
│  │  └─────────┘ └─────────┘ └─────────────────────────────┘ │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              WAN Edge (SD-WAN)                              │     │
│  │  Ottimizzazione routing, QoS, traffic steering             │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
│  ┌───────────────────────────────────────────────────────────┐     │
│  │              Identity & Device Trust Layer                  │     │
│  │  IdP, MFA, device posture, continuous evaluation           │     │
│  └───────────────────────────────────────────────────────────┘     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 14.6 Criteri di Selezione Vendor

La scelta del vendor Zero Trust deve essere guidata da criteri oggettivi. La seguente checklist supporta il processo di valutazione:

**Criteri tecnici:**
- [ ] Supporto multi-cloud (AWS, Azure, GCP) senza lock-in
- [ ] Integrazione con IdP esistente (SAML 2.0, OIDC, SCIM)
- [ ] Granularità delle policy (L3/L4 e L7, per utente/dispositivo/applicazione)
- [ ] Performance e latenza (SLA documentati, PoP globali)
- [ ] Supporto per protocolli legacy e applicazioni non-web
- [ ] API-first per automazione e integrazione IaC (Terraform, Pulumi)
- [ ] Capacità di deployment agentless per dispositivi IoT/OT

**Criteri operativi:**
- [ ] Time-to-value (PoC in settimane, non mesi)
- [ ] Complessità operativa (quanti FTE per gestione quotidiana)
- [ ] Qualità documentazione e supporto tecnico
- [ ] Roadmap prodotto e frequenza di rilascio
- [ ] Community e ecosistema di integrazioni

**Criteri di business:**
- [ ] Modello di pricing (per utente, per workload, per bandwidth)
- [ ] TCO su 3 e 5 anni (includendo migrazione e formazione)
- [ ] Compliance certificazioni del vendor (SOC 2 Type II, ISO 27001, FedRAMP)
- [ ] Solidità finanziaria e rischio vendor (acquisizioni, market share)

---

## 15. Strategia Governativa e Militare

### 15.1 Strategia Zero Trust del Dipartimento della Difesa USA

Il Dipartimento della Difesa degli Stati Uniti (DoD) ha pubblicato la propria strategia Zero Trust nel novembre 2022, stabilendo la roadmap più ambiziosa a livello governativo per l'adozione del modello. Il DoD ha definito 152 capability outcome organizzati in 7 pilastri, con l'obiettivo di raggiungere il livello "Target" per tutti i sistemi entro il FY2027 e il livello "Advanced" entro il FY2032.

**I 7 Pilastri della Strategia ZT del DoD:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DoD ZERO TRUST PILLARS                            │
├─────────────────────────────────────────────────────────────────────┤
│  1. USER         │ Identità forte, MFA, continuous auth             │
│  2. DEVICE       │ Inventario, compliance, health attestation       │
│  3. APPLICATION  │ App security, SBOM, secure development           │
│  & WORKLOAD      │                                                  │
│  4. DATA         │ Classification, encryption, DLP, DRM             │
│  5. NETWORK      │ Macro/micro segmentation, SDN, encrypted DNS     │
│  & ENVIRONMENT   │                                                  │
│  6. AUTOMATION   │ SOAR, policy-as-code, ML-driven response         │
│  & ORCHESTRATION │                                                  │
│  7. VISIBILITY   │ SIEM, UEBA, threat hunting, log aggregation      │
│  & ANALYTICS     │                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 15.2 DTM 25-003: Direttiva di Implementazione 2025

Il Directive-Type Memorandum (DTM) 25-003, "Implementing the DoD Zero Trust Strategy", è entrato in vigore il 17 luglio 2025 e ha stabilito strutture organizzative e scadenze vincolanti:

**Elementi chiave del DTM 25-003:**

- **Istituzione del Zero Trust Portfolio Management Office (PfMO)**: ufficio dedicato con responsabilità di coordinamento, sincronizzazione e accelerazione dell'adozione ZT nell'intero enterprise DoD
- **Creazione del ruolo di Chief Zero Trust Officer**: responsabile dell'orchestrazione dell'esecuzione ZT a livello DoD, con autorità di direzione strategica e allineamento degli sforzi
- **Requisito Target Level ZT**: tutti i componenti DoD devono raggiungere il livello minimo Target ZT su tutti i sistemi non classificati e classificati, inclusi sistemi di controllo e tecnologia operativa (OT)
- **61 capability outcome avanzati**: requisiti aggiuntivi per livelli avanzati di Zero Trust, con scadenza FY2032 per tutti i componenti DoD
- **Estensione a OT e sistemi d'arma**: per la prima volta, la direttiva copre esplicitamente infrastrutture OT come reti elettriche, idriche, energetiche e sistemi d'arma moderni (carri armati, droni, sistemi navali)

### 15.3 DoD Zero Trust Strategy 2.0 (2026)

La versione aggiornata della strategia (ZT Strategy 2.0) è prevista per la pubblicazione nel primo trimestre 2026. Le aree di espansione attese includono:

- Overlay specifici per OT e IoT in contesti militari
- Integrazione con i requisiti del Cyber Command per le operazioni
- Estensione ai sistemi di comunicazione tattica e in campo
- Requisiti per la supply chain della base industriale della difesa (DIB)
- Linee guida per la Zero Trust in ambienti disconnessi, intermittenti e a bassa larghezza di banda (DIL — Disconnected, Intermittent, Low-bandwidth)

### 15.4 CISA Zero Trust Maturity Model v2.0 — Analisi Approfondita

Il CISA ZTMM v2.0, pubblicato nell'aprile 2023, fornisce il framework di riferimento per le agenzie federali civili USA. Il modello definisce quattro livelli di maturità attraverso cinque pilastri, con tre capacità trasversali:

**Livelli di maturità CISA ZTMM:**

| Livello | Caratteristiche | Esempi |
|---------|-----------------|--------|
| **Traditional** | Assegnazione manuale degli attributi, policy statiche, dipendenza dal perimetro | Password-only auth, network-based access, silo di sicurezza |
| **Initial** | Inizio automazione, visibilità parziale, prime integrazioni cross-pillar | MFA parziale, segmentazione macro, logging centralizzato iniziale |
| **Advanced** | Automazione diffusa, integrazione cross-pillar, policy basate su rischio | Risk-based auth, micro-segmentazione avanzata, UEBA attiva |
| **Optimal** | Automazione completa, orchestrazione dinamica, risposta in tempo reale | Continuous verification, policy AI-driven, threat response automatizzato |

**I 5 Pilastri del CISA ZTMM con capacità trasversali:**

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CISA ZTMM v2.0 FRAMEWORK                        │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────────┤
│          │          │          │          │          │  CAPACITÀ   │
│ IDENTITY │ DEVICES  │ NETWORKS │   DATA   │  APPS &  │ TRASVERSALI │
│          │          │          │          │WORKLOADS │             │
│          │          │          │          │          │ • Visibility│
│          │          │          │          │          │   & Analytics│
│          │          │          │          │          │ • Automation│
│          │          │          │          │          │   & Orch.   │
│          │          │          │          │          │ • Governance│
├──────────┴──────────┴──────────┴──────────┴──────────┤             │
│  Traditional → Initial → Advanced → Optimal          │             │
└──────────────────────────────────────────────────────┴─────────────┘
```

### 15.5 SDP Architecture Guide v3.0 (CSA)

La Cloud Security Alliance ha rilasciato nel 2026 la terza versione della guida architetturale per il Software-Defined Perimeter, con aggiornamenti significativi rispetto alle versioni precedenti:

**Novità principali della v3.0:**

- **Spostamento dal network al servizio**: l'oggetto della policy non è più la posizione nella rete ma il servizio specifico. L'accesso non è ereditato dall'appartenenza a una subnet o VPN, ma creato esplicitamente per un'identità nominativa verso un servizio nominativo, sotto condizioni definite
- **Supporto per identità machine e AI**: il framework ora copre esplicitamente identità per utenti umani, identità machine e sistemi emergenti come workload AI/ML, IoT e tecnologia operativa
- **Architettura a tre componenti aggiornata**: i tre componenti core (Controller, Gateway, Client) sono stati ridefiniti per supportare architetture cloud-native e service mesh
- **Integrazione con SPIFFE/SPIRE**: supporto nativo per workload identity standard
- **Policy-as-Code**: enfasi sulla definizione delle policy in formato dichiarativo, version-controlled e testabile

**Architettura SDP v3 aggiornata:**

```
┌──────────────────────────────────────────────────────────────────┐
│                     SDP v3.0 ARCHITECTURE                         │
│                                                                   │
│  ┌─────────────┐    ┌──────────────────┐    ┌────────────────┐  │
│  │  SDP Client  │    │  SDP Controller   │    │  SDP Gateway   │  │
│  │             │    │                  │    │               │  │
│  │ • User/     │◄──►│ • Authentication │◄──►│ • Service     │  │
│  │   Machine   │    │ • Authorization  │    │   proxy       │  │
│  │   identity  │    │ • Policy eval    │    │ • mTLS term   │  │
│  │ • Device    │    │ • Service        │    │ • L7 enforce  │  │
│  │   posture   │    │   discovery      │    │ • Audit log   │  │
│  │ • SPA knock │    │ • Trust engine   │    │ • DLP inspect │  │
│  └─────────────┘    └──────────────────┘    └────────────────┘  │
│                                                                   │
│  Flusso:                                                          │
│  1. Client invia SPA (Single Packet Authorization) al Controller  │
│  2. Controller valida identità + device + contesto                │
│  3. Controller istruisce Gateway ad aprire connessione per Client │
│  4. Client stabilisce mTLS con Gateway (connessione temporanea)   │
│  5. Gateway proxy verso il servizio backend                       │
│  6. Connessione terminata allo scadere della sessione             │
└──────────────────────────────────────────────────────────────────┘
```

### 15.6 Lezioni Apprese dall'Implementazione Federale USA

L'implementazione Zero Trust nelle agenzie federali USA (oltre 100 agenzie, mandato dall'Executive Order 14028 del 2021) ha prodotto lezioni preziose applicabili a qualsiasi organizzazione di grandi dimensioni:

**Lezioni positive:**

1. **L'identità è il punto di partenza più efficace**: le agenzie che hanno iniziato dal pilastro Identity (MFA, SSO, governance) hanno ottenuto il ROI più rapido e la riduzione più significativa degli incidenti
2. **La visibilità precede l'enforcement**: le agenzie che hanno saltato la fase di discovery e mapping dei flussi hanno subito interruzioni operative significative durante l'enforcement
3. **I piloti con team volontari accelerano l'adozione**: iniziare con team IT e security che comprendono il modello riduce la resistenza e genera champion interni
4. **La policy-as-code è essenziale per la scalabilità**: le agenzie che hanno gestito le policy manualmente hanno raggiunto i limiti di scala entro 6 mesi
5. **Il break-glass testato previene le crisi**: ogni agenzia che ha subito un'interruzione significativa durante il rollout aveva procedure di break-glass non testate o incomplete

**Lezioni critiche (errori da evitare):**

1. **Non tentare il "big bang"**: le agenzie che hanno tentato di implementare ZTA su tutti i sistemi simultaneamente hanno tutte subito rollback parziali
2. **Non sottovalutare il change management**: la resistenza culturale degli utenti è il principale ostacolo, non la tecnologia. Budget per la formazione e la comunicazione
3. **Non ignorare le applicazioni legacy**: il 30-40% delle applicazioni in ambiente federale non supporta autenticazione moderna. Serve una strategia di wrapping o mediazione
4. **Non fidarsi solo del vendor**: nessun vendor singolo copre tutti i pilastri ZTA. La strategia multi-vendor è complessa ma necessaria
5. **Non dimenticare il dato**: molte agenzie hanno implementato identity e network ZT ma hanno trascurato la classificazione e protezione dei dati, lasciando un gap critico

### 15.7 Zero Trust in Ambienti Militari e Tattici

L'applicazione del modello Zero Trust in contesti militari operativi presenta sfide uniche legate alla natura degli ambienti tattici:

**Sfide specifiche:**

| Scenario | Sfida | Approccio ZT |
|----------|-------|-------------|
| Operazioni in ambienti DIL | Connettività intermittente con il control plane | Cache decisionale locale con trust ridotto, sincronizzazione quando connessione disponibile |
| Sistemi d'arma | Latenza di accesso deve essere sub-millisecondo | Policy pre-caricate, validazione hardware-based (TPM), decisioni locali |
| Reti tattiche mobili | Topologia di rete cambia continuamente | Service mesh con mTLS, discovery dinamica, identity-based routing |
| Interoperabilità alleati | Trust tra domini con policy diverse | Federation con IdP NATO, trust boundary esplicito, data sharing granulare |
| Classificazione multi-livello | Dati SECRET e TOP SECRET nella stessa infrastruttura | Cross-Domain Solutions (CDS) con ZTA, segmentazione crittografica |
| Anti-tamper | Dispositivi catturati dal nemico | Auto-wipe su tamper detection, revoca remota certificati, zero stored secrets |

---

## Appendice F: Matrice Normativa-Pilastro ZTA

La seguente matrice dettaglia come ogni pilastro Zero Trust soddisfa requisiti specifici di ciascun framework normativo, fornendo una guida pratica per la prioritizzazione degli investimenti:

```
┌───────────────────────────────────────────────────────────────────────────┐
│              MAPPING NORMATIVA → PILASTRO ZERO TRUST                      │
├───────────────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│                   │ IDENTITY │ DEVICES  │ NETWORK  │   DATA   │ WORKLOAD │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ NIS2 Art.21(a)    │  ●●●     │  ●●      │  ●●      │  ●●●     │  ●●      │
│ Risk Analysis     │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ NIS2 Art.21(b)    │  ●●      │  ●       │  ●●●     │  ●●      │  ●●●     │
│ Incident Handling │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ NIS2 Art.21(d)    │  ●●●     │  ●●      │  ●       │  ●●●     │  ●       │
│ Supply Chain      │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ DORA Art.6        │  ●●●     │  ●●●     │  ●●      │  ●●●     │  ●●      │
│ ICT Risk Mgmt     │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ DORA Art.8        │  ●●      │  ●●●     │  ●●●     │  ●       │  ●●●     │
│ Protection        │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ DORA Art.26       │  ●●●     │  ●       │  ●●      │  ●●●     │  ●●      │
│ Third-Party Risk  │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ GDPR Art.25       │  ●●      │  ●       │  ●       │  ●●●     │  ●       │
│ Data Protection   │          │          │          │          │          │
│ by Design         │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ GDPR Art.32       │  ●●●     │  ●●      │  ●●●     │  ●●●     │  ●●      │
│ Security of       │          │          │          │          │          │
│ Processing        │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ ISO 27001 A.8     │  ●●●     │  ●●●     │  ●●●     │  ●●●     │  ●●●     │
│ Technical Ctrls   │          │          │          │          │          │
├───────────────────┼──────────┼──────────┼──────────┼──────────┼──────────┤
│ CISA ZTMM v2     │  ●●●     │  ●●●     │  ●●●     │  ●●●     │  ●●●     │
│ (tutti i livelli) │          │          │          │          │          │
└───────────────────┴──────────┴──────────┴──────────┴──────────┴──────────┘

Legenda: ● = rilevanza bassa, ●● = rilevanza media, ●●● = rilevanza alta
```

---

## Appendice G: Tabella Comparativa Dettagliata Vendor

### G.1 Funzionalità ZTNA per Vendor

```
┌────────────────────┬────────┬────────┬────────┬────────┬────────┬────────┐
│ Funzionalità       │Zscaler │ Palo   │ Cloud  │ Micro  │ Crowd  │ Cisco  │
│                    │        │ Alto   │ flare  │ soft   │ Strike │        │
├────────────────────┼────────┼────────┼────────┼────────┼────────┼────────┤
│ ZTNA clientless    │   ✓    │   ✓    │   ✓    │   ✓    │   —    │   ✓    │
│ ZTNA agent-based   │   ✓    │   ✓    │   ✓    │   ✓    │   —    │   ✓    │
│ CASB inline        │   ✓    │   ✓    │   ✓    │   ✓    │   —    │   ✓    │
│ SWG                │   ✓    │   ✓    │   ✓    │   —    │   —    │   ✓    │
│ FWaaS              │   ✓    │   ✓    │   ✓    │   ✓    │   —    │   ✓    │
│ DLP                │   ✓    │   ✓    │   ✓    │   ✓    │   —    │   ✓    │
│ Sandbox/threat     │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│ SD-WAN integrato   │   —    │   ✓    │   ✓    │   —    │   —    │   ✓    │
│ EDR nativo         │   —    │   ✓    │   —    │   ✓    │   ✓    │   ✓    │
│ Identity protection│   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│ IoT/OT support     │   ✓    │   ✓    │   ●    │   ●    │   ●    │   ✓    │
│ Data center segm.  │   ✓    │   ✓    │   —    │   —    │   —    │   ✓    │
│ FedRAMP            │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │
│ API-first/IaC      │   ✓    │   ✓    │   ✓    │   ✓    │   ✓    │   ●    │
└────────────────────┴────────┴────────┴────────┴────────┴────────┴────────┘

Legenda: ✓ = disponibile e maturo, ● = disponibile ma limitato, — = non disponibile
```

### G.2 Benchmark Prestazionale

| Metrica | Zscaler | Palo Alto | Cloudflare | Netskope |
|---------|---------|-----------|------------|----------|
| PoP globali | 150+ | 100+ | 310+ | 75+ |
| Latenza media (ms) | 8-15 | 10-20 | 3-8 | 10-18 |
| Uptime SLA (%) | 99.999 | 99.99 | 99.99 | 99.999 |
| Throughput max per utente | 200 Mbps | 300 Mbps | Unlimited | 150 Mbps |
| Tempo deployment pilota | 2-4 settimane | 4-8 settimane | 1-2 settimane | 3-6 settimane |

---

## Appendice A: Zero Trust Implementation Checklist

### Quick Reference — Validation per Fase

```
PHASE 1 — IDENTITY
├── [ ] 100% MFA coverage
├── [ ] FIDO2 for privileged accounts
├── [ ] Legacy auth disabled
├── [ ] SSO for all applications
├── [ ] PAM for admin accounts
├── [ ] JML automation operational
└── [ ] Impossible travel detection active

PHASE 2 — DEVICE
├── [ ] MDM coverage 100% corporate devices
├── [ ] Compliance policies enforced
├── [ ] Device certificate enrollment complete
├── [ ] EDR integrated with access decisions
├── [ ] BYOD MAM policies active
└── [ ] TPM attestation for sensitive access

PHASE 3 — NETWORK
├── [ ] Default-deny network policies
├── [ ] ZTNA replacing VPN
├── [ ] Identity-aware proxy for internal apps
├── [ ] East-west encryption verified
├── [ ] DNS security controls active
└── [ ] Traffic flow mapping complete

PHASE 4 — WORKLOAD
├── [ ] SPIFFE/SPIRE deployed
├── [ ] mTLS enforced all services
├── [ ] Runtime protection active
├── [ ] CI/CD pipeline hardened
├── [ ] Admission controllers enforced
└── [ ] Workload firewall policies applied

PHASE 5 — DATA
├── [ ] Classification complete for critical repos
├── [ ] DLP operational at all enforcement points
├── [ ] Rights management for sensitive docs
├── [ ] Column-level encryption for PII/PHI
├── [ ] Key rotation automated
└── [ ] Data access governance logging

PHASE 6 — VISIBILITY
├── [ ] UEBA baselines established
├── [ ] All ZTA signals in SIEM
├── [ ] Automated playbooks active
├── [ ] Executive dashboards operational
├── [ ] Tabletop exercises completed
└── [ ] Quarterly maturity assessment scheduled
```

---

## Appendice B: Architecture Decision Records (ADR)

### ADR-001: Identity Provider Selection

**Status**: Accepted
**Context**: Organization requires a centralized IdP supporting FIDO2, SCIM provisioning, and conditional access integration.
**Decision**: Microsoft Entra ID selected for organizations already invested in M365; Okta for multi-cloud/multi-IdP environments.
**Rationale**: Native integration reduces friction; Conditional Access + Continuous Access Evaluation is the most mature implementation.
**Consequences**: Tight coupling to Microsoft ecosystem. Mitigated by standardizing on OIDC/SAML for app integration.

### ADR-002: Network Segmentation Approach

**Status**: Accepted
**Context**: Must segment east-west traffic in Kubernetes without requiring application changes.
**Decision**: Istio service mesh with STRICT mTLS and AuthorizationPolicy.
**Rationale**: Transparent to applications (sidecar injection), supports L7 policies, integrates with SPIFFE for workload identity.
**Consequences**: Added latency (~1-3ms per hop), increased resource consumption (~100MB per sidecar), operational complexity.

### ADR-003: Token Binding Strategy

**Status**: Proposed
**Context**: Stolen OAuth tokens can bypass device trust controls.
**Decision**: Implement DPoP (RFC 9449) for all OAuth 2.0 flows.
**Rationale**: Binds tokens to sender's key pair; token is useless without the private key. Standardized, supported by major IdPs.
**Consequences**: Requires client library updates, token validation logic changes in resource servers.

---

## Appendice C: Zero Trust Threat Model

### STRIDE Analysis per ZTA Components

| Component | Spoofing | Tampering | Repudiation | Info Disclosure | DoS | Elevation |
|-----------|----------|-----------|-------------|-----------------|-----|-----------|
| **Policy Engine** | Auth bypass → full compromise | Policy manipulation → unauthorized access | Missing audit → undetectable breach | Decision logic exposure → targeted bypass | PE overload → access denied/allowed-all | Config change → admin access |
| **Policy Admin** | PA impersonation → control all PEPs | Token injection → fake sessions | PA log gap → ghost sessions | PA-PEP protocol sniffing | PA crash → all sessions terminated | PA admin account takeover |
| **PEP** | Client spoofing → bypass checks | Traffic manipulation in transit | Session log gap → invisible access | mTLS key theft → impersonation | PEP overload → bypass (fail-open?) | PEP config change → allow-all |
| **Identity Provider** | Credential theft → user impersonation | SAML/OIDC response tampering | Auth log gap → unattributed access | User enumeration, metadata leaks | IdP DoS → org-wide lockout | Admin compromise → golden tickets |
| **Device Posture** | Fake compliance signal | Attestation data manipulation | Missing posture logs | Device fingerprint exposure | Posture service DoS → stale data | Root/jailbreak → full device control |

### Critical Failure Modes

**Fail-Open vs Fail-Closed:**
Every ZTA component must be configured to fail-closed. If the PE is unavailable, access must be denied — not granted. Test this explicitly:
- Kill the PE and attempt access → should be denied
- Kill the PA and attempt new sessions → should be denied
- Kill the PEP and attempt direct access → network-level deny must be in place

**Single Points of Failure:**
- IdP outage → break-glass accounts must exist (tested quarterly)
- PA outage → existing sessions continue but new sessions fail
- Internet outage → local decision cache with reduced trust level

---

## Appendice D: Riferimenti e Standard

| Standard / Publication | Scope |
|----------------------|-------|
| NIST SP 800-207 | Zero Trust Architecture |
| NIST SP 800-207A | Zero Trust Maturity Model (CISA) |
| CISA Zero Trust Maturity Model v2.0 | Federal agency implementation guide |
| DoD Zero Trust Reference Architecture v2.0 | Military/defense ZTA |
| Forrester ZTX Framework | Commercial ZTA ecosystem |
| Google BeyondCorp Papers (1-6) | Production ZTA at scale |
| RFC 9449 (DPoP) | OAuth token binding |
| SPIFFE Standards | Workload identity |
| CSA SDP Specification v2.0 | Software-defined perimeter |
| OWASP ASVS v4.0 | Application security verification |
| CIS Controls v8 | Security controls mapping |
| ISO 27001:2022 Annex A | Information security controls |

---

## Appendice E: Glossario Zero Trust

| Termine | Definizione |
|---------|-------------|
| **CAE** | Continuous Access Evaluation — real-time session revocation |
| **DPoP** | Demonstrating Proof-of-Possession — token binding mechanism |
| **IAP** | Identity-Aware Proxy — authenticates/authorizes per-request |
| **mTLS** | Mutual TLS — both client and server present certificates |
| **PA** | Policy Administrator — operationalizes access decisions |
| **PAM** | Privileged Access Management — controls admin access |
| **PE** | Policy Engine — brain of ZTA, evaluates trust |
| **PEP** | Policy Enforcement Point — enforces access decisions in data path |
| **PRT** | Primary Refresh Token — device-bound Azure AD token |
| **SDP** | Software-Defined Perimeter — hide-and-connect architecture |
| **SPA** | Single Packet Authorization — cryptographic port knock |
| **SPIFFE** | Secure Production Identity Framework For Everyone |
| **SPIRE** | SPIFFE Runtime Environment |
| **SVID** | SPIFFE Verifiable Identity Document |
| **UEBA** | User and Entity Behavior Analytics |
| **ZTNA** | Zero Trust Network Access — VPN replacement |
| **ZTX** | Zero Trust eXtended — Forrester's ecosystem framework |

---

*Documento creato: 2025-05-07*
*Classificazione: INTERNAL — per uso formativo e operativo*
