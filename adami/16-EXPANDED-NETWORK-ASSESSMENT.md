# 16 — Expanded Network Assessment & Methodology Deep-Dive

**Assessment Date (expansion):** 2026-05-26
**Original Assessment Date:** 2026-05-19
**Machine:** PCFRANCESCA (HP ProBook 450 G7)
**Current IP:** 192.168.192.61 (Adami_Guest Wi-Fi)
**Assessor:** sandro / macena IT Security

---

## Purpose of This Document

This document expands the original 15-document assessment with:
- **New findings** from live data collected on 2026-05-26
- **Methodology explanations** — how each finding was derived, what commands were used, and why the result matters
- **Logic chains** — connecting individual data points into actionable conclusions
- **Teaching notes** — so the IT team can reproduce this assessment on other machines

Cross-references to original documents are marked as `→ See [XX-DOCUMENT.md]`.

---

## Part 1 — Network Topology Update

### What Changed Since 2026-05-19

The original assessment identified 3 subnets and 13 hosts on the main LAN. Live data from 2026-05-26 reveals:

```
NEW HOSTS DISCOVERED:

  192.168.1.105  — NOT in original host list
                    Seen: Delivery Optimization (TCP 7680) TimeWait
                    Method: Get-NetTCPConnection on live machine

  192.168.60.55  — FIRST HOST on infrastructure subnet beyond DNS!
                    Seen: Delivery Optimization (TCP 7680) TimeWait
                    Method: Get-NetTCPConnection on live machine

  ORIGINAL 13 HOSTS (192.168.1.x): .56, .58, .75, .76, .77, .79,
                                     .81, .103, .144, .147, .155,
                                     .162, .193

  UPDATED HOST COUNT: 15+ hosts across 2 subnets
```

### Why 192.168.60.55 Is Critical

The original assessment concluded that the infrastructure subnet (192.168.60.x) was **completely unreachable** from the guest network. DNS (TCP/53) and ICMP were both blocked. The only known hosts were 192.168.60.2 and 192.168.60.3 (DNS servers, from the Ethernet adapter config).

**The discovery of 192.168.60.55 changes this picture entirely.**

```
LOGIC CHAIN:

  1. Delivery Optimization (DO) runs on port 7680
  2. DO is a Windows peer-to-peer update sharing service
  3. 192.168.60.55 connected TO this machine on port 7680
  4. This means a host in the INFRASTRUCTURE subnet initiated
     a TCP connection to a host on the GUEST subnet
  5. The connection was in TimeWait state (recently completed)

  CONCLUSION:
  ─────────────────────────────────────────────────────────
  The infrastructure subnet (192.168.60.x) can reach the
  guest subnet (192.168.192.x) — at minimum on TCP 7680.

  This is a BIDIRECTIONAL segmentation failure:
    Guest → Main LAN (192.168.1.x) on 7680  ← already known
    Infra → Guest (192.168.192.x) on 7680   ← NEW FINDING

  The firewall/router allows Delivery Optimization traffic
  to cross ALL VLAN boundaries — not just Guest ↔ Main LAN.
  ─────────────────────────────────────────────────────────
```

### Updated Topology Diagram

```
═══════════════════════════════════════════════════════════════════
                        INTERNET
                   Welcome Italia ISP
                 ┌───────────────────┐
                 │ DNS: 80.93.143.42 │
                 │       80.93.143.44│
                 └─────────┬─────────┘
                           │
                           │
                 ┌─────────┴─────────┐    External VPN Endpoint:
                 │                   │    45.151.15.58 :1194/UDP
                 │  EDGE GATEWAY     │    (pfSense OpenVPN)
                 │  192.168.192.1    │
                 │  MAC: 80:61:5f:   │
                 │       06:19:cb    │
                 │                   │
                 │  DO(7680) crosses │
                 │  ALL VLANs ← BUG │
                 └──┬──────┬─────┬───┘
                    │      │     │
      ┌─────────────┘      │     └──────────────┐
      │                    │                    │
      ▼                    ▼                    ▼
┌──────────────┐   ┌────────────────┐   ┌────────────────────┐
│ GUEST WI-FI  │   │  MAIN LAN      │   │ INFRASTRUCTURE     │
│ 192.168.192  │   │  192.168.1     │   │ 192.168.60         │
│ .0/24        │   │  .0/24         │   │ .0/??              │
│              │   │                │   │                    │
│ ★ THIS PC   │   │ 14+ hosts:     │   │ Known hosts:       │
│ .192.61     │   │ .56  .58  .75  │   │ .60.2  (DNS/DC?)   │
│              │   │ .76  .77  .79  │   │ .60.3  (DNS/DC?)   │
│ Wi-Fi PSK:   │   │ .81  .103     │   │ .60.55 (NEW - DO)  │
│ 1DfGhYu53   │   │ .105 ← NEW    │   │                    │
│              │   │ .144 .147     │   │ DO traffic reaches │
│ 7 APs       │   │ .155 .162     │   │ guest subnet !!    │
│              │   │ .193          │   │                    │
│              │   │                │   │                    │
│              │   │ DNS inside VPN:│   │                    │
│              │   │ .1.146        │   │                    │
└──────────────┘   └────────────────┘   └────────────────────┘
```

### How We Discovered Each Subnet

| Subnet | Method | Command | Logic |
|--------|--------|---------|-------|
| 192.168.192.0/24 | Direct connection | `ipconfig /all` | Machine is on this subnet; DHCP from .192.1 |
| 192.168.1.0/24 | Delivery Optimization peers | `Get-NetTCPConnection` filtering RemoteAddress `192.168.1.*` | Windows DO shares updates peer-to-peer; these connections leak which hosts exist on other subnets |
| 192.168.60.0/x | Ethernet DNS config + live DO | `Get-DnsClientServerAddress` (static DNS .60.2/.60.3) + live `Get-NetTCPConnection` showing .60.55 | The Ethernet adapter retained DNS servers from when it was plugged into corporate LAN; live DO connection confirms reachability |

### How We Know the VPN Architecture

The OpenVPN configuration file at `C:\Users\CHIARA\OpenVPN\config\pfSense-UDP4-1194-francescav.ovpn` reveals:

```
WHAT THE VPN CONFIG TELLS US:

  remote 45.151.15.58 1194 udp4
  ├── Adami's public VPN endpoint is 45.151.15.58
  ├── pfSense firewall/router is the VPN concentrator
  └── UDP 1194 = standard OpenVPN port

  dhcp-option DNS 192.168.1.146
  ├── When connected via VPN, DNS goes to 192.168.1.146
  ├── This is a NEW host not seen via DO peering
  └── Likely an internal DNS server or DC on the main LAN

  redirect-gateway def1
  ├── Full tunnel — ALL traffic routes through VPN
  └── This is a security-conscious config (good)

  block-outside-dns
  ├── Prevents DNS leaks outside the tunnel
  └── Also security-conscious (good)

  VPN tunnel: 10.37.169.0/24
  ├── Client IP: 10.37.169.2
  └── DHCP server inside tunnel: 10.37.169.254

  Server cert: OpenVpnServerCert2021
  └── Certificate was created in 2021, still valid
```

---

## Part 2 — Host Identity Deep-Dive

### Machine History Reconstruction

By cross-referencing user profiles, SIDs, VPN certificates, OneDrive folders, and scheduled tasks, we can reconstruct how this machine was used over time:

```
MACHINE TIMELINE: PCFRANCESCA (HP ProBook 450 G7)
═══════════════════════════════════════════════════

  2020-05-05  Machine setup
              ├── Windows installed (Build 26200 today, upgraded over time)
              ├── Built-in Administrator password set
              └── Original user: likely "Francesca" (→ hostname PCFRANCESCA)

  ~2021       VPN server certificate created ("OpenVpnServerCert2021")

  2022-01-13  OpenVPN certificate issued for user "francescav"
              ├── Issuer: CN=Internal CA
              ├── Valid until 2032-01-11
              └── Installed globally in C:\Program Files\OpenVPN\config\

  2022-02-01  AnyDesk installed and configured
              └── First remote connections from massimo-it@ad (IT support)

  2022-02-09  ASPNET account created (IIS/ASP.NET worker)
              └── Never used, still enabled, no password

  ~2022       Local account CHIARA created (SID -1001, before ASPNET -1002)
              ├── Used as primary user
              ├── OpenVPN config duplicated to profile
              ├── GoSign (digital signature) installed
              ├── Dropbox syncing "GRUPPO ADAMI QUALITA'"
              ├── OneDrive syncing "ADAMI TRASPORTI SPA"
              ├── Firefox, Chrome, Edge all had saved passwords
              └── Android development tools (.android folder)

  2023-03-22  Multiple AnyDesk connections from ID 905591417 begin
              └── Regular IT support pattern continues through 2024

  2023-05-12  Guest account logged in (unusual — should never happen)

  2023-05-31  AnyDesk connection from laptop-014t20a2@ad (ID 227837777)

  2023-06-27  OpenVPN config updated in CHIARA's profile

  2024-04-10  AnyDesk: REJECTED connection from 619901193
              └── Followed immediately by accepted connection from 905591417

  2024-12-18  Last VPN connection from this machine
              ├── Connected 12:24 → 13:58 (1.5 hours)
              ├── Got IP 10.37.169.2 inside tunnel
              └── OpenVPN 2.5.0 (2020 build — outdated)

  2025-03-01  elena.malini (domain account) first login
              ├── Domain SID: S-1-5-21-3521058280-4105139221-2070416120-1247
              ├── Created profile with OpenVPN, .ms-ad folders
              └── Chrome and Edge credential stores created

  2025-03-04  AnyDesk connection from 419761499 (likely elena setup)

  2025-11-03  sandro account created (SID -1003)
              ├── Password set (later removed or expired to "not required")
              ├── CHIARA account DELETED (but profile remains)
              ├── GoSign last ran under CHIARA profile
              └── Dropbox, OneDrive sync may still have cached data

  2026-05-19  Original security assessment

  2026-05-26  This expanded assessment (today)
              ├── sandro is active user, local admin, NO password
              ├── 3 user profiles on disk (sandro, CHIARA, elena.malini)
              ├── All credentials still on disk
              └── DO traffic to infrastructure subnet confirmed
```

### Why This Timeline Matters

```
SECURITY IMPLICATIONS:

  1. CREDENTIAL ACCUMULATION
     Three different users' credentials are on this machine:
     - CHIARA: Browser passwords (Chrome 135KB, Edge 61KB, Firefox),
               VPN certs, GoSign digital signature data,
               OneDrive/Dropbox corporate data
     - elena.malini: Browser passwords (Chrome, Edge),
                     Domain cached credentials
     - sandro: Browser passwords (Chrome 40KB, Edge 53KB)

     NONE of these were cleaned up during user transitions.

  2. ORPHANED SCHEDULED TASKS
     12+ tasks still run as CHIARA's deleted SID:
     - OneDrive Reporting/Startup tasks
     - TrackerAutoUpdate
     - Dropbox Updater
     - Firefox Background Update + Default Browser Agent
     These tasks run with unknown privilege since the account is deleted.

  3. DOMAIN CREDENTIAL EXPOSURE
     elena.malini's domain SID proves this machine once authenticated
     to the AD domain (adamitrasporti.local). Cached domain credentials
     may be extractable from the registry (SECURITY hive).
     The machine is now on the guest network — if compromised,
     those cached creds could be used against the domain.
```

→ See [02-HOST-IDENTITY.md] for original findings.

---

## Part 3 — Network Services Expanded Analysis

### What "Listening on 0.0.0.0" Means and Why It Matters

When a service listens on `0.0.0.0` (or `::` for IPv6), it accepts connections on **every network interface**. This means:

```
SERVICE ON 0.0.0.0:445 (SMB):
├── Reachable from Wi-Fi (192.168.192.x) — the guest network
├── Reachable from Ethernet (if plugged in) — the corporate LAN
├── Reachable from VPN tunnel (10.37.169.x) — if VPN is active
├── Reachable from localhost (127.0.0.1) — always
└── Reachable from Bluetooth PAN — if paired

vs.

SERVICE ON 127.0.0.1:10107 (Avast BCC):
└── Reachable ONLY from localhost
    No network exposure at all
```

### Current Listening Services (2026-05-26 Live Snapshot)

**Network-exposed services (0.0.0.0):**

| Port | Process | PID | Risk | Why This Matters |
|------|---------|-----|------|-----------------|
| 135/TCP | svchost (RPC) | - | MEDIUM | RPC Endpoint Mapper — allows service enumeration, prerequisite for WMI/DCOM attacks |
| 139/TCP | System | 4 | HIGH | NetBIOS Session Service — legacy file sharing, allows null session enumeration |
| 445/TCP | System | 4 | CRITICAL | SMB — file sharing, admin shares. Combined with no password = instant compromise |
| 2000/TCP | WUDFHost | - | LOW | User-Mode Driver Framework — typically for USB devices, low attack surface |
| 5040/TCP | svchost | - | LOW | Windows service — internal use |
| 7070/TCP | AnyDesk | 8628 | HIGH | Remote desktop — always-on, accepts connections from any network |
| 7680/TCP | svchost (DO) | 4424 | MEDIUM | Delivery Optimization — crosses VLAN boundaries, leaks host info |
| 49664+/TCP | lsass, wininit, etc. | - | MEDIUM-HIGH | Dynamic RPC ports — LSASS is particularly sensitive (credential extraction target) |

**Localhost-only services (127.0.0.1):**

| Port | Process | Purpose | Concern |
|------|---------|---------|---------|
| 10107 | bcc (Avast Console) | Management | None — local only |
| 12025 | AvastSvc | SMTP proxy (port 25 intercept) | Avast reads all email |
| 12110 | AvastSvc | POP3 proxy (port 110 intercept) | Avast reads all email |
| 12143 | AvastSvc | IMAP proxy (port 143 intercept) | Avast reads all email |
| 12465 | AvastSvc | SMTPS proxy (port 465 intercept) | Avast reads encrypted email |
| 12993 | AvastSvc | IMAPS proxy (port 993 intercept) | Avast reads encrypted email |
| 12995 | AvastSvc | POP3S proxy (port 995 intercept) | Avast reads encrypted email |
| 14108 | agentsvc (Avast Agent) | Agent comms | None — local only |
| 49672 | jhi_service (Intel ME) | Management Engine | ME has had critical CVEs; local only reduces risk |

### Current Active Connections (2026-05-26)

```
OUTBOUND CONNECTION MAP (Live):

  PCFRANCESCA (.192.61)
       │
       ├── Claude Code (3 connections)
       │   ├── 160.79.104.10:443 (×2)   — Anthropic direct
       │   └── 34.149.66.137:443        — Anthropic via GCP
       │
       ├── Google Chrome (13 connections)
       │   ├── 142.251.x.x (Google)     — Search/Services
       │   ├── 192.178.x.x (Google)     — Services
       │   ├── 95.100-101.x.x (Akamai)  — CDN content
       │   ├── 151.101.241.91 (Fastly)  — CDN/Reddit
       │   ├── 185.199.109.153 (GitHub) — GitHub Pages
       │   └── 216.239.36.223 (Google)  — DNS/Services
       │
       ├── Avast (3 connections)
       │   ├── 34.98.110.65:443         — Avast cloud
       │   ├── 34.148.222.171:443       — Avast cloud
       │   └── 95.100.171.40:443        — Avast via Akamai
       │
       ├── Avast Agent (2 connections)
       │   ├── 34.22.130.91:7500        — Business console
       │   └── 34.102.255.163:443       — Business console
       │
       ├── AnyDesk (1 connection)
       │   └── 51.178.91.234:443        — Relay server (OVH)
       │       (was 162.19.204.173 on 05-19, relay rotated)
       │
       ├── Microsoft (OneDrive, Teams, Edge)
       │   ├── 4.207.247.138-139:443    — Azure/OneDrive
       │   ├── 52.108/123.x.x:443      — M365 services
       │   ├── 72.144.122.179:443       — Teams
       │   ├── 74.248.73.245:443        — Edge services
       │   └── 150.171.70.254:443       — Edge/Bing
       │
       ├── Windows Update / Store
       │   ├── 23.60.189-190.x:443      — Akamai CDN
       │   └── 150.171.27.10:443        — Store
       │
       └── CROSS-SUBNET (Delivery Optimization)
           ├── 192.168.1.193:53514      — Established (active!)
           ├── 192.168.1.105:51420      — TimeWait (recent)
           └── 192.168.60.55:58468      — TimeWait (recent)  ← NEW!!
```

### How We Know Segmentation Is Broken (Step-by-Step)

```
METHODOLOGY:

Step 1: Run Get-NetTCPConnection and filter for internal IPs
  → Found connections to 192.168.1.x (main LAN) — expected
  → Found connection to 192.168.60.55 — UNEXPECTED

Step 2: Identify the service
  → Port 7680 = Windows Delivery Optimization
  → Process: svchost (DoSvc)

Step 3: Determine direction
  → Local port 7680 (this machine is serving content)
  → Remote ports 51420, 53514, 58468 (ephemeral — clients connecting IN)
  → Direction: INBOUND — hosts from other subnets are connecting to us

Step 4: Analyze implications
  → If hosts on 192.168.60.x can reach us on TCP 7680,
     the firewall permits at least SOME cross-VLAN TCP traffic
  → ICMP is blocked (ping fails) — this is selective filtering
  → The firewall operator likely created a blanket rule for
     Delivery Optimization without restricting it per-VLAN

Step 5: Assess risk
  → Delivery Optimization itself is low-risk (Windows Update sharing)
  → BUT: The fact that TCP traffic crosses VLANs means
     other ports may also be reachable
  → An attacker who modifies their machine's DO port binding
     or uses the same port number could potentially bypass
     the VLAN segmentation

WHY THIS MATTERS FOR IT:
  The gateway/firewall needs a rule audit. The current ACL
  likely has a port-based allow rule for 7680 that applies
  across all interfaces/VLANs instead of being scoped to
  same-subnet traffic only.
```

→ See [01-NETWORK-TOPOLOGY.md] and [08-OUTBOUND-CONNECTIONS.md] for original findings.

---

## Part 4 — Firewall Analysis Expanded

### The 576 Enabled Rules Problem

The Windows Firewall has **576 enabled rules**. This is far too many for a clean, auditable configuration. Many are duplicates or leftover from uninstalled applications.

**Key inbound ALLOW rules active on Public profile (current network):**

```
DANGEROUS INBOUND ALLOWS ON PUBLIC PROFILE:

  ┌─ AnyDesk (TCP+UDP, all profiles, any address)
  │  5+ rules allowing inbound from ANYWHERE
  │  → Remote desktop access from untrusted networks
  │
  ├─ SMB / File Sharing (TCP 445, NetBIOS 137-139)
  │  Active on Public profile
  │  → File sharing accessible from guest Wi-Fi
  │
  ├─ LLMNR (UDP 5355)
  │  Active on Public profile
  │  → Broadcast poisoning attack vector
  │
  ├─ mDNS (UDP 5353)
  │  Active on Public profile (Chrome, Edge, Copilot all have rules)
  │  → Local name spoofing
  │
  ├─ Delivery Optimization (TCP+UDP 7680)
  │  Active on ANY profile
  │  → Cross-VLAN traffic vector
  │
  ├─ UPnP/SSDP (UDP 1900, TCP 2869)
  │  Active on Public
  │  → Device discovery, potential for UPnP exploits
  │
  ├─ ZebraDesigner Proxy Service
  │  Inbound allow on Public
  │  → Label printer service accessible from guest network
  │
  ├─ GoSign Desktop
  │  Inbound TCP+UDP allow
  │  → Digital signature app accessible from network
  │
  ├─ Zoom Video Meeting + Airhost
  │  Inbound allow
  │  → Video conferencing ports
  │
  └─ Microsoft Lync/Skype
     Inbound allow
     → Legacy communication (Lync may be unused)
```

### Why "Public Profile" Should Be Locked Down

```
EXPLANATION FOR IT:

  Windows Firewall has 3 profiles: Domain, Private, Public.

  "Public" is meant for untrusted networks (coffee shops, airports).
  The Adami_Guest Wi-Fi is correctly classified as Public.

  BUT: Many inbound rules are active on Public that should NOT be:
  - File sharing (SMB) is a corporate feature, not needed on guest Wi-Fi
  - AnyDesk is set to ALL profiles — should be Private/Domain only
  - LLMNR is enabled on Public — poisoning is trivial on shared Wi-Fi
  - GoSign, Zoom, Lync all have Public profile rules

  RECOMMENDATION:
  Review all 576 rules. Disable any inbound allow rule on the
  Public profile that is not strictly required for the application
  to function on untrusted networks.
```

→ See [06-FIREWALL-AND-FILTERING.md] for original findings.

---

## Part 5 — SMB Deep-Dive: Why This Is the #1 Risk

### The Attack Chain Explained for IT

```
STEP-BY-STEP: How an attacker compromises this machine via SMB

  PREREQUISITES (all TRUE for this machine):
  ✓ SMBv1 enabled
  ✓ Admin account (sandro) has no password
  ✓ SMB signing not required
  ✓ SMB encryption disabled
  ✓ "Users" share grants Everyone Full Control
  ✓ Admin shares (C$, ADMIN$) accessible
  ✓ No account lockout policy
  ✓ Machine is on shared Wi-Fi (guest network)

  ATTACK:

  1. Attacker connects to Adami_Guest Wi-Fi (password: 1DfGhYu53)
     → Now on same subnet as this machine

  2. Attacker scans 192.168.192.0/24 for port 445
     → Finds PCFRANCESCA at 192.168.192.61

  3. Attacker tries SMB authentication:
     smbclient //192.168.192.61/C$ -U sandro -N
     → SUCCESS — no password, full admin access to C: drive

  4. Attacker can now:
     a. Read ALL files on C: drive via admin share
     b. Read all user profiles via "Users" share
     c. Execute commands via PsExec/WMI
     d. Extract browser passwords, VPN certs, Wi-Fi keys
     e. Install backdoor/ransomware
     f. Pivot to main LAN via DO port 7680

  TIME TO FULL COMPROMISE: < 60 seconds
  TOOLS NEEDED: smbclient (built into Kali Linux)
  SKILL LEVEL: Beginner

  WHY SMBv1 IS WORSE:
  Even if the password WAS set, SMBv1 has the EternalBlue
  vulnerability (MS17-010) which allows REMOTE CODE EXECUTION
  without any credentials at all. This is what WannaCry used.
```

### Current SMB Configuration (Verified 2026-05-26)

| Setting | Value | Should Be | Status |
|---------|-------|-----------|--------|
| EnableSMB1Protocol | **True** | False | CRITICAL |
| EnableSMB2Protocol | True | True | OK |
| RequireSecuritySignature | **False** | True | CRITICAL |
| EnableSecuritySignature | **False** | True | HIGH |
| EncryptData | **False** | True | HIGH |
| AuditSmb1Access | **False** | True | No visibility |
| AutoShareWorkstation | True | False | Admin shares exposed |
| RejectUnencryptedAccess | True | True | OK |

### What "SMB Signing" Means and Why It Matters

```
WITHOUT SIGNING (current state):

  Client ────── [SMB request] ──────► Server
                     ▲
                     │ ATTACKER
                     │ can modify
                     │ the packet
                     │ in transit

  → Man-in-the-middle can alter file contents
  → NTLM relay attacks are possible (capture auth, replay it)

WITH SIGNING (recommended):

  Client ────── [SMB request + HMAC signature] ──────► Server
                     ▲
                     │ ATTACKER
                     │ cannot modify
                     │ without the
                     │ signing key
                     │ (tied to auth)

  → Packet tampering is detected and rejected
  → Relay attacks fail because the signature is session-bound
```

→ See [09-SMB-FILE-SHARING.md] for original findings.

---

## Part 6 — Broadcast Protocol Poisoning Explained

### Why LLMNR/NetBIOS Are Dangerous on This Machine Specifically

```
THE UNIQUE DANGER:

  This machine uses ISP DNS (80.93.143.42) — external.
  The DHCP suffix is "adamitrasporti.local" — internal.

  When a user types \\fileserver or \\printserver:
  1. Windows appends suffix → fileserver.adamitrasporti.local
  2. Queries ISP DNS → NXDOMAIN (ISP doesn't know internal names)
  3. Falls back to LLMNR broadcast → "Who is fileserver?"
  4. Any host on the subnet can answer

  Because DNS ALWAYS fails for internal names, LLMNR is used
  for EVERY internal hostname lookup. This makes poisoning
  attacks nearly 100% reliable on this machine.

  On a domain-joined machine with internal DNS, LLMNR is rarely
  triggered because DNS resolves most names. But here, LLMNR
  is the PRIMARY name resolution for anything corporate.
```

→ See [10-BROADCAST-PROTOCOLS.md] for original findings.

---

## Part 7 — AnyDesk Exposure Analysis

### AnyDesk Configuration Extracted (2026-05-26)

```
ANYDESK IDENTITY:
  ID:           325232966
  Alias:        desktop-q8qvcf4@ad
  Fingerprint:  ca3f08c330e8a7e6df1d3e843ff08e0428ff6273
  License:      free-1 (FREE LICENSE!)
  Last relay:   relay-086fcbb1.net.anydesk.com
  Current relay: 51.178.91.234 (OVH, EU)

SECURITY CONFIG:
  Unattended access:     ENABLED (password hash stored)
  Clipboard sharing:     ENABLED
  Clipboard files:       ENABLED
  Send Ctrl+Alt+Del:     ALLOWED (both default and unattended profiles)

UNATTENDED ACCESS CREDENTIALS:
  Password hash:  68d71c8c2a6fe4cb41cddcab961fba36608bf81449f51b22d416339399f601f8
  Salt:           ced3b533b45d3d69ef3467d4e01e06c1
  (SHA-256 based — can be brute-forced offline if password is weak)
```

### AnyDesk Connection History

```
DATE         TYPE      SOURCE                      ID
──────────── ───────── ─────────────────────────── ──────────
2022-02-03   User      massimo-it@ad               988685941
2022-02-03   User      massimo-it@ad               988685941
2022-02-03   User      massimo-it@ad               988685941
2023-03-22   Passwd    (unnamed)                   905591417
2023-03-22   Passwd    (unnamed)                   905591417
2023-03-22   Passwd    (unnamed)                   905591417
2023-05-31   Passwd    laptop-014t20a2@ad          227837777
2023-05-31   Passwd    laptop-014t20a2@ad          227837777
2023-05-31   User      laptop-014t20a2@ad          227837777
2023-05-31   User      laptop-014t20a2@ad          227837777
2023-06-06   Passwd    (unnamed)                   905591417
2023-06-06   Passwd    (unnamed)                   905591417
2023-06-06   Passwd    (unnamed)                   905591417
2023-09-27   Passwd    (unnamed)                   905591417
2023-10-24   Passwd    (unnamed)                   905591417
2023-11-10   Passwd    (unnamed)                   905591417
2023-11-29   Passwd    (unnamed)                   905591417
2024-04-10   REJECTED  (unknown)                   619901193  ← WHO?
2024-04-10   User      (unnamed)                   905591417
2024-04-10   User      (unnamed)                   905591417
2024-04-22   User      (unnamed)                   905591417
2024-04-26   Passwd    (unnamed)                   905591417
2024-05-02   User      (unnamed)                   905591417
2024-05-02   Passwd    (unnamed)                   905591417
2024-05-09   User      (unnamed)                   905591417
2025-03-04   User      (unnamed)                   419761499

ANALYSIS:
  "massimo-it@ad" (988685941) = IT technician Massimo, used early on
  "905591417" (unnamed) = Most frequent connector (14 sessions, 2023-2024)
                          This is likely the primary IT support person
  "laptop-014t20a2@ad" (227837777) = Another Adami machine
  "619901193" = REJECTED — unauthorized attempt, needs investigation
  "419761499" = Connected once on 2025-03-04, close to elena.malini
                profile creation (2025-03-01) — likely setup session
```

### Why Free-License AnyDesk Is a Problem

```
RISK:

  1. Free AnyDesk has NO access logging to a central console
  2. Anyone who knows the ID (325232966) can attempt connection
  3. The unattended password hash can be brute-forced offline
  4. AnyDesk relay is hosted by OVH — traffic goes through
     a third-party cloud provider outside Adami's control
  5. The REJECTED connection from 619901193 could be:
     - A wrong number
     - An attacker scanning AnyDesk IDs
     - An ex-employee's machine
     IT should identify this ID.
```

→ See [08-OUTBOUND-CONNECTIONS.md] and [07-LISTENING-SERVICES.md] for original findings.

---

## Part 8 — Certificate Store Findings

### Expired Root CAs Still Trusted

These certificates have expired but remain in the machine trust store. While modern browsers maintain their own trust lists, legacy applications (Outlook, business software, PowerShell) use the Windows store:

| Certificate | Expired | Risk |
|-------------|---------|------|
| QuoVadis Root CA | 2021-03-17 | LOW — should clean up |
| DST Root CA X3 (Let's Encrypt legacy) | 2021-09-30 | LOW — only legacy cross-sign |
| SECOM Trust RootCA1 | 2023-09-30 | LOW — should clean up |
| AddTrust External CA Root | 2020-05-30 | LOW — should clean up |

### Distrusted CAs Still Trusted

| Certificate | Issue | Risk |
|-------------|-------|------|
| **WoSign** (CN=Certification Authority of WoSign, C=CN) | Distrusted by all browsers since 2016 for mis-issuing certificates | **MEDIUM** — could validate forged certificates |
| **StartCom** (CN=StartCom Certification Authority, C=IL) | Same entity as WoSign, same distrust | **MEDIUM** — should be removed |

### Avast TLS Interception CA

```
CN=Avast Web/Mail Shield Root
Valid: 2010-01-01 to 2040-01-01
Thumbprint: C6747020A29DB3D41D5FB4ABF0E6FA86E709B594

This CA is used by Avast to decrypt ALL HTTPS traffic.
Every TLS connection is terminated by Avast, inspected,
then re-encrypted with a new certificate signed by this CA.

IMPACT:
- Avast sees the plaintext of all encrypted traffic
- If this CA private key is compromised, an attacker can
  impersonate any HTTPS site to this machine
- Certificate pinning is broken for all applications
- Some applications may reject the re-signed certificates
```

→ See [11-SECURITY-SOFTWARE.md] for original findings.

---

## Part 9 — Patch Status & Software Concerns

### Windows Update Status (2026-05-26)

| Update | Type | Installed |
|--------|------|-----------|
| KB5089549 | Security Update | 2026-05-18 |
| KB5092762 | Security Update | 2026-05-18 |
| KB5087051 | Update | 2026-05-18 |
| KB5054156 | Update | 2025-11-04 |

Recent security updates were installed 8 days ago. Patch cadence appears reasonable.

### OpenVPN Version Concern

The VPN log shows `OpenVPN 2.5.0` built on `Oct 28 2020`. This version is **over 5 years old** and has known vulnerabilities. The current stable version is 2.6.x.

### Non-System Services Running

| Service | Binary Path | Start | Run As | Concern |
|---------|-------------|-------|--------|---------|
| AnyDesk | `C:\Program Files (x86)\AnyDesk\AnyDesk.exe` | Auto | SYSTEM | Free license, persistent relay, no central management |
| Adobe ARM | `C:\...\Adobe\ARM\1.0\armsvc.exe` | Auto | LocalSystem | Auto-updater, acceptable |
| Avast (8 services) | `C:\Program Files\Avast Software\...` | Auto | LocalSystem | Expected — primary AV |
| Claude | CoworkVMService | Auto | ? | Assessment tool |

---

## Part 10 — Assessment Methodology Reference

### Commands Used (IT Can Reproduce on Other Machines)

```powershell
# === IDENTITY ===
Get-LocalUser | Format-List *
Get-LocalGroup | ForEach-Object { Get-LocalGroupMember -Group $_.Name }
net accounts
Get-WmiObject -Class Win32_UserProfile | Select-Object LocalPath, SID, LastUseTime

# === CREDENTIALS ===
cmdkey /list
netsh wlan show profile name="SSID" key=clear
# Browser credential DBs at: %LocalAppData%\Google\Chrome\User Data\Default\Login Data

# === NETWORK ===
Get-NetTCPConnection -State Established | Select-Object LocalAddress, LocalPort, RemoteAddress, RemotePort, OwningProcess
Get-NetTCPConnection -State Listen | Select-Object LocalAddress, LocalPort, OwningProcess
Get-NetNeighbor -AddressFamily IPv4
ipconfig /all
route print
Get-DnsClientServerAddress

# === SMB ===
Get-SmbServerConfiguration
Get-SmbShare
Get-SmbShareAccess -Name "ShareName"

# === FIREWALL ===
Get-NetFirewallRule -Enabled True | Measure-Object
Get-NetFirewallRule -Enabled True -Direction Inbound -Action Allow

# === SERVICES ===
Get-Service | Where-Object { $_.Status -eq 'Running' }
Get-WmiObject Win32_Service | Where-Object { $_.State -eq 'Running' }

# === CERTIFICATES ===
Get-ChildItem Cert:\LocalMachine\Root

# === ANYDESK ===
Get-Content "C:\ProgramData\AnyDesk\system.conf"
Get-Content "C:\ProgramData\AnyDesk\connection_trace.txt"

# === VPN ===
Get-ChildItem "C:\Program Files\OpenVPN\config" -Recurse
Get-ChildItem "C:\Users\*\OpenVPN\config" -Recurse
```

---

## Summary of New Findings (vs. Original Assessment)

| # | Finding | Original Doc | This Update |
|---|---------|-------------|-------------|
| 1 | 192.168.60.55 reachable from guest | Not found | **NEW** — infrastructure subnet is NOT fully isolated |
| 2 | 192.168.1.105 new host | Not in host list | **NEW** — main LAN has 14+ hosts |
| 3 | CHIARA ghost profile with credentials | Not analyzed | **NEW** — VPN certs, browser passwords, corporate data on disk |
| 4 | elena.malini domain account cached | Not analyzed | **NEW** — domain SID proves AD authentication occurred |
| 5 | VPN endpoint at 45.151.15.58 | Not found | **NEW** — pfSense VPN infrastructure identified |
| 6 | Internal DNS at 192.168.1.146 | Not found | **NEW** — DNS server inside VPN tunnel |
| 7 | AnyDesk ID, hash, connection history | Partially | **EXPANDED** — full connection log, all IDs, password hash |
| 8 | Wi-Fi passwords extracted | Not extracted | **NEW** — plaintext PSKs for both networks |
| 9 | Expired/distrusted root CAs | 2 mentioned | **EXPANDED** — 4 expired + 2 distrusted identified |
| 10 | 576 firewall rules | Count not given | **NEW** — excessive rule count identified |
| 11 | HP ProBook 450 G7 model | Not identified | **NEW** — exact hardware model |
| 12 | Logon auditing disabled | Not checked | **NEW** — no user logon events in security log |
| 13 | itgroup@adamitrasporti.com cached | Not found | **NEW** — shared IT account in credential manager |
| 14 | AnyDesk REJECTED connection | Not found | **NEW** — unauthorized attempt from 619901193 |
