# 14 — Security Findings & Remediation Plan

## Finding Summary by Severity

```
┌──────────────────────────────────────────────────────────┐
│              FINDINGS BY SEVERITY                         │
│                                                          │
│  CRITICAL  ████████  4 findings                         │
│  HIGH      █████████████  6 findings                    │
│  MEDIUM    ████████████████  8 findings                 │
│  LOW       ██████████  5 findings                       │
│  INFO      ████████  4 findings                         │
│                                                          │
│  Total: 27 findings                                      │
└──────────────────────────────────────────────────────────┘
```

---

## CRITICAL Findings

### C1 — SMBv1 Protocol Enabled

| Field | Detail |
|-------|--------|
| Severity | **CRITICAL** |
| Category | Protocol Security |
| Location | SMB Server Configuration |
| CVE Reference | MS17-010 (EternalBlue), CVE-2017-0144 |
| Current State | `EnableSMB1Protocol = True` |
| Impact | Remote Code Execution without authentication |
| Exploitability | High — public exploits widely available (Metasploit, etc.) |

**Description:** SMBv1 is the protocol exploited by WannaCry and NotPetya. It should never be enabled on any system. Combined with the machine being on a network-shared Wi-Fi segment, any attacker on the guest network could attempt exploitation.

**Remediation:**
```powershell
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
# Also disable the client:
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart
```

---

### C2 — Network Segmentation Failure (Guest → LAN)

| Field | Detail |
|-------|--------|
| Severity | **CRITICAL** |
| Category | Network Architecture |
| Evidence | 50+ TCP connections from 192.168.192.61 to 192.168.1.x on port 7680 |
| Impact | Guest network clients can reach internal LAN hosts |
| Scope | At minimum port 7680; possibly other ports |

**Description:** The guest Wi-Fi network (192.168.192.0/24) has TCP connectivity to the main LAN (192.168.1.0/24). Delivery Optimization traffic confirms bidirectional communication. While ICMP and SMB appear blocked, the segmentation is incomplete.

**Remediation:**
- Audit the gateway/firewall rules between VLANs
- Implement strict VLAN ACLs — guest should reach ONLY the internet
- Block all inter-VLAN traffic from the guest segment
- Use a proper captive portal for guest access

---

### C3 — Administrator Account Without Password

| Field | Detail |
|-------|--------|
| Severity | **CRITICAL** |
| Category | Authentication |
| Account | sandro (active local admin) |
| Current State | `PasswordRequired = False`, no password set |
| Impact | Anyone with network access can authenticate as full administrator |

**Description:** The primary user account `sandro` has local administrator privileges and no password. Combined with exposed SMB shares and no account lockout policy, this means any network-adjacent attacker gets instant SYSTEM-level access.

**Remediation:**
```powershell
# Set a strong password immediately:
net user sandro *
# Then enforce password policy via local security policy (secpol.msc)
```

---

### C4 — "Users" Share Grants Everyone Full Control

| Field | Detail |
|-------|--------|
| Severity | **CRITICAL** |
| Category | Data Exposure |
| Share | \\PCFRANCESCA\Users (C:\Users) |
| Permission | Everyone = Full Control |
| Impact | All user data readable/writable by any network user |

**Description:** The entire C:\Users directory is shared on the network with Everyone having Full access. This exposes documents, downloads, application data, browser profiles, cached credentials, and any sensitive files stored in user profiles.

**Remediation:**
```powershell
Remove-SmbShare -Name "Users" -Force
# Or restrict permissions:
Revoke-SmbShareAccess -Name "Users" -AccountName "Everyone" -Force
Grant-SmbShareAccess -Name "Users" -AccountName "BUILTIN\Administrators" -AccessRight Full -Force
```

---

## HIGH Findings

### H1 — AnyDesk Always-On Remote Access

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Remote Access |
| Service | AnyDesk Service (Automatic start) |
| Ports | TCP 7070, UDP 50001 (listening on 0.0.0.0) |
| External Connection | 162.19.204.173 (relay-83fd48c2.net.anydesk.com) — OVH, EU |
| Firewall | 5 inbound allow rules, all profiles |

**Description:** AnyDesk is installed as a system service with automatic startup. It maintains a persistent connection to an external relay server and accepts inbound connections from any network. If an attacker obtains the AnyDesk ID and password (or exploits a vulnerability), they get interactive desktop access.

**Remediation:**
- If AnyDesk is business-required: set a strong unattended access password, restrict to specific IPs, enable 2FA
- If not required: `Stop-Service AnyDesk; Set-Service AnyDesk -StartupType Disabled`
- Remove inbound firewall rules for AnyDesk on Public profile

---

### H2 — LLMNR + NetBIOS Broadcast Poisoning

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Name Resolution |
| Protocols | LLMNR (UDP 5355), NetBIOS-NS (UDP 137), mDNS (UDP 5353) |
| GPO Config | None (all enabled by default) |
| Combined With | No SMB signing → relay attacks fully viable |

**Remediation:** See [10-BROADCAST-PROTOCOLS.md](10-BROADCAST-PROTOCOLS.md) for disable commands.

---

### H3 — SMB Signing Not Required

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Protocol Security |
| Current State | `RequireSecuritySignature = False`, `EnableSecuritySignature = False` |
| Impact | NTLM relay attacks, man-in-the-middle of SMB traffic |

---

### H4 — SMB Encryption Disabled

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Data Protection |
| Current State | `EncryptData = False` |
| Impact | All SMB traffic (file shares, admin shares) transmitted in cleartext |

---

### H5 — Windows Defender Fully Disabled

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Endpoint Protection |
| Current State | All Defender features OFF, signatures never updated |
| Impact | No fallback protection if Avast is disabled, tampered with, or bypassed |

---

### H6 — ASPNET Account Enabled Without Password

| Field | Detail |
|-------|--------|
| Severity | **HIGH** |
| Category | Authentication |
| Account | ASPNET (enabled, no password, created 2022-02-09) |
| Impact | Unnecessary attack surface — dormant account with no authentication |

---

## MEDIUM Findings

### M1 — Avast TLS Interception (MITM by Design)

All HTTPS and encrypted email traffic is decrypted, inspected, and re-encrypted by Avast using a locally-generated root CA. This breaks certificate pinning and creates a single point of trust. If the Avast private key is extracted from this machine, all intercepted traffic can be decrypted.

### M2 — Corporate Machine on Guest Network Without VPN

The machine has a corporate DNS suffix (adamitrasporti.local) but is connected to the guest Wi-Fi segment with ISP DNS. No VPN is configured. Corporate services requiring internal DNS or direct network access are unreachable.

### M3 — No BitLocker Disk Encryption

The disk is not encrypted. Physical theft or loss of the laptop results in complete data compromise.

### M4 — Distrusted Root CAs (WoSign, StartCom)

The certificate store contains root CAs that have been distrusted by all major browsers since 2016 due to mis-issuance incidents.

### M5 — Guest Account Login History

The disabled Guest account shows a last login date of 2023-05-12. Guest accounts should never be used for interactive login. This may indicate unauthorized access or policy violation.

### M6 — No Egress Firewall Filtering

All outbound traffic is allowed by default. No application whitelisting or port restrictions for outbound connections.

### M7 — WHEA Hardware Errors

System log shows continuous hardware errors (Event ID 17, every 5-30 seconds). This indicates potential hardware failure that could cause data corruption or system instability.

### M8 — Short DHCP Lease on Persistent Workstation

4-hour DHCP lease is typical for guest hotspots but problematic for a workstation that needs stable network connectivity. IP changes can break persistent connections and confuse monitoring tools.

---

## LOW Findings

### L1 — PowerShell Execution Policy Bypass
Current session runs with Bypass policy. No execution restrictions at any scope level.

### L2 — Multiple Redundant PDF Applications
4 PDF tools installed (PDFCreator, PDF Architect 8, PDF Architect 9, PDF-XChange). Each is additional attack surface.

### L3 — Wi-Fi Channel Congestion
All 5 GHz APs share channel 40, causing co-channel interference.

### L4 — Firewall Audit Policies Disabled
`AuditSmb1Access`, `AuditClientDoesNotSupportEncryption`, `AuditInsecureGuestLogon` all disabled. No visibility into insecure SMB access attempts.

### L5 — Intel Management Engine Active
Intel ME is running with JHI service on local port 49672. ME has had multiple critical CVEs (INTEL-SA-00086, INTEL-SA-00112).

---

## INFO Findings

### I1 — Hostname Mismatch
Machine named PCFRANCESCA but used by sandro. Suggests machine reassignment.

### I2 — Delivery Optimization Cross-Subnet Peering
Windows Update Delivery Optimization serves content to 13+ hosts on the main LAN, inadvertently leaking host enumeration data.

### I3 — SoftLanding Scheduled Task
Windows built-in TwinUI component, not malware. False alarm cleared.

### I4 — Python Development Environment
Python 3.12.10 installed on business workstation. Verify this is needed.

---

## Remediation Priority Matrix

```
┌──────────────────────────────────────────────────────────────┐
│   URGENCY                                                     │
│   ▲                                                          │
│   │                                                          │
│   │  C1 (SMBv1)      C3 (No Password)                       │
│   │  C4 (Users Share) H1 (AnyDesk)                          │
│   │                                                          │ 
│   │  C2 (Segmentation) H2 (LLMNR)                           │
│   │  H3 (SMB Sign)     H5 (Defender)                        │
│   │  H6 (ASPNET)                                            │
│   │                                                          │
│   │  M1 (TLS MITM)   M3 (BitLocker)                        │
│   │  M2 (No VPN)     M4 (Bad CAs)                          │
│   │                                                          │
│   │  L1-L5           I1-I4                                  │
│   │                                                          │
│   └───────────────────────────────────────────►  EFFORT      │
│       Quick Fix          Moderate        Infrastructure      │
└──────────────────────────────────────────────────────────────┘
```

## Quick Wins (< 5 minutes each)

```powershell
# 1. Disable SMBv1
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force

# 2. Set password on sandro
net user sandro *

# 3. Disable ASPNET account
net user ASPNET /active:no

# 4. Remove Users share
Remove-SmbShare -Name "Users" -Force

# 5. Enable SMB signing
Set-SmbServerConfiguration -RequireSecuritySignature $true -Force
Set-SmbServerConfiguration -EnableSecuritySignature $true -Force

# 6. Enable SMB encryption
Set-SmbServerConfiguration -EncryptData $true -Force

# 7. Disable LLMNR
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" `
  -Name "EnableMulticast" -Value 0 -Type DWord

# 8. Disable NetBIOS
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True"
$adapters | ForEach-Object { $_.SetTcpipNetbios(2) }

# 9. Disable admin shares
Set-SmbServerConfiguration -AutoShareWorkstation $false -Force

# 10. Enable SMB auditing
Set-SmbServerConfiguration -AuditSmb1Access $true -Force
```
