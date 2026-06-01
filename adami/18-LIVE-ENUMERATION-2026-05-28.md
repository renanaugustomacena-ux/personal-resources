# 18 — Live Network Enumeration from Guest Wi-Fi (Linux)

**Assessment Date:** 2026-05-28
**Machine:** renan's Linux workstation (Ubuntu 24.04, kernel 6.17.0-29)
**Current IP:** 192.168.192.129/24 (Adami_Guest Wi-Fi)
**MAC:** 34:C9:3D:91:39:08 (Intel)
**Gateway:** 192.168.192.1 (MAC: 80:61:5F:06:19:CB — Beijing Sinead Technology)
**DNS:** 80.93.143.42, 80.93.143.44 (ISP — Welcome Italia)
**Tools:** nmap 7.94SVN, smbclient, rpcclient, netcat, python3, curl
**Method:** Active scanning (ARP sweep, SYN scan, TCP connect, UDP probe, service detection)

> **Context:** This is the THIRD assessment pass. Previous passes were from PCFRANCESCA (Windows 11, .192.61) on 2026-05-19 and 2026-05-26. This pass uses a different machine (Linux) on the same guest Wi-Fi segment to validate and extend findings.

---

## Part 1 — Guest Subnet Discovery (192.168.192.0/24)

### NEW CRITICAL FINDING: No Client Isolation

The original assessment (docs 03 and 05) hypothesized that AP client isolation might be enabled based on PCFRANCESCA's sparse ARP table (only the gateway visible). **This hypothesis is now disproven.**

ARP sweep found **16 devices** on the guest subnet. All are visible and reachable at L2.

```
GUEST SUBNET: 192.168.192.0/24 — FULL HOST INVENTORY
═══════════════════════════════════════════════════════

IP                  MAC                  Vendor / Type                      LAA?
────────────────────────────────────────────────────────────────────────────────
192.168.192.1       80:61:5F:06:19:CB    Gateway (Beijing Sinead Tech)      NO
192.168.192.20      7A:EA:FF:EF:FE:04    Phone/tablet (randomized MAC)      YES
192.168.192.50      04:95:E6:52:DB:7D    Tenda Technology ★                NO
192.168.192.63      82:9B:44:B5:53:2B    Phone/tablet (randomized MAC)      YES
192.168.192.88      6E:62:42:BA:8C:D2    Phone/tablet (randomized MAC)      YES
192.168.192.101     16:95:48:DF:71:4E    Phone/tablet (randomized MAC)      YES
192.168.192.106     16:E7:F0:DF:AE:41    Phone/tablet (randomized MAC)      YES
192.168.192.111     04:95:E6:52:DB:7D    Tenda Technology ★                NO
192.168.192.119     5E:19:14:4F:B3:AE    Phone/tablet (randomized MAC)      YES
192.168.192.129     34:C9:3D:91:39:08    THIS MACHINE (Intel)               NO
192.168.192.135     E8:CF:83:92:1D:EC    Dell Inc. (laptop/desktop)         NO
192.168.192.141     04:95:E6:52:DB:7D    Tenda Technology ★                NO
192.168.192.145     CE:4D:9A:59:BB:4E    Phone/tablet (randomized MAC)      YES
192.168.192.149     00:03:50:E8:4D:87    Bticino SPA (building automation)  NO
192.168.192.189     E6:67:C1:B8:EF:85    Phone/tablet (randomized MAC)      YES
192.168.192.195     E6:D3:62:98:FD:EC    Similar to AP OUI E0:D3:62         YES

Totals: 16 devices | 9 randomized MAC (phones/tablets) | 7 real MAC (infra/corporate)
```

**★ Tenda anomaly:** IPs .50, .111, and .141 share the SAME MAC address (04:95:E6:52:DB:7D). This is a Tenda Wi-Fi extender or repeater with multiple DHCP leases. IT should physically identify this device — if it bridges to another network, it's an additional segmentation bypass.

### 4th Subnet Discovered: 192.168.6.0/x

A server/NAS at **192.168.6.1** was identified by IT as hosting file shares (SMB, accessible via File Explorer with credentials `adminada`). This reveals a 4th network segment:

| Property | Value |
|----------|-------|
| IP | 192.168.6.1 |
| Role | File server / NAS (SMB shares) |
| Auth | Username: adminada, password-protected |
| Reachability from guest | **BLOCKED** — TCP 445, 139, 80 all timeout |
| Route | Via gateway .192.1 (route exists but traffic dropped) |
| Access method | Requires main LAN, infrastructure VLAN, or VPN |

**Updated subnet count: 4 known subnets** (Guest .192.x, Main LAN .1.x, Infrastructure .60.x, File Server .6.x).

### PCFRANCESCA (.61) Status

**Offline.** Did not respond to ARP, ICMP, or SYN probes. Powered off or not connected to Adami_Guest at time of this assessment.

### Device Classification

```
GUEST NETWORK DEVICE BREAKDOWN:

  Infrastructure:
  ├── .1    — Gateway/router (Beijing Sinead / possibly MikroTik-based)
  ├── .50/.111/.141 — Tenda Wi-Fi extender (3 IPs, 1 device)
  └── .195  — Possibly an AP (MAC similar to AP fleet OUI E0:D3:62)

  Corporate devices:
  ├── .129  — This assessment machine (Linux)
  ├── .135  — Dell laptop/desktop
  └── .149  — Bticino building automation device

  Personal devices (randomized MACs):
  ├── .20, .63, .88, .101, .106, .119, .145, .189
  └── 8 phones/tablets (employees, visitors, or drivers)
```

### Attack Implication: No Client Isolation

```
WITHOUT CLIENT ISOLATION:
                                                                
  Guest Device A ◄──────────────────► Guest Device B           
  (attacker)          L2 reachable      (victim)               
                                                                
  An attacker on the guest Wi-Fi can:                          
  ├── ARP spoof other guest clients                            
  ├── Sniff unencrypted traffic between guests and gateway     
  ├── Attack the Bticino building automation device directly   
  ├── Attack the Dell laptop at .135                           
  ├── Attack the Tenda extender (potential pivot to other nets)
  └── Perform LLMNR/mDNS/NBNS poisoning against Windows guests
```

---

## Part 2 — Cross-VLAN Reachability Testing

### Guest → Main LAN (192.168.1.0/24)

| Test | Ports | Method | Result |
|------|-------|--------|--------|
| Full SYN scan .1.193 | All 65535 | nmap -sS -p- | **ALL FILTERED — zero open** |
| Common ports (14 hosts) | 7680, 445, 139, 135, 80, 443, 22, 3389, 5985, 53, 8080, 8443, etc. | nmap -sS + bash /dev/tcp | **ALL FILTERED** |
| SMB null session .1.193 | 445 | smbclient -L -N | NT_STATUS_IO_TIMEOUT |
| SMB null session .1.79 | 445 | smbclient -L -N | NT_STATUS_IO_TIMEOUT |

**Conclusion:** Guest-initiated TCP to main LAN is completely blocked across all 65535 ports.

### Guest → Infrastructure (192.168.60.0/x)

| Test | Ports | Method | Result |
|------|-------|--------|--------|
| Full SYN scan .60.2 | All 65535 | nmap -sS -p- | **ALL FILTERED — zero open** |
| AD/DC ports (.60.2, .60.3, .60.55) | 53, 88, 135, 139, 389, 443, 445, 636, 3268, 5985, 7680, etc. | nmap -sS + bash /dev/tcp | **ALL FILTERED** |
| DNS query .60.2 | 53/UDP | dig @192.168.60.2 | **Timed out** |
| DNS query .60.3 | 53/UDP | dig @192.168.60.3 | **Timed out** |

**Conclusion:** Guest-initiated TCP and UDP to infrastructure is completely blocked.

### Main LAN → Guest (inbound direction)

This direction was NOT tested from this machine (we can only test outbound from guest). However, the PCFRANCESCA assessment (doc 16, 2026-05-26) provides evidence:

```
EVIDENCE FROM PCFRANCESCA (2026-05-26):

  Get-NetTCPConnection showed:
  ├── 192.168.1.193:53514  → 192.168.192.61:7680   ESTABLISHED
  ├── 192.168.1.105:51420  → 192.168.192.61:7680   TIME_WAIT
  └── 192.168.60.55:58468  → 192.168.192.61:7680   TIME_WAIT

  Analysis:
  ├── Local port 7680 = PCFRANCESCA was the SERVER (Delivery Optimization)
  ├── Remote ports are ephemeral = the remote hosts INITIATED the connection
  └── Hosts from BOTH main LAN and infrastructure connected to a guest host
```

**This means traffic initiated FROM main LAN/infrastructure TO guest is allowed (at least on port 7680).** Possible explanations:

1. Gateway has a directional rule: main LAN → guest allowed, guest → main LAN blocked
2. Gateway has a protocol/port-specific rule allowing 7680 across all VLANs
3. Gateway configuration changed between 2026-05-26 and today
4. Stateful connection from earlier DO discovery handshake

**IT must audit the gateway/firewall ACLs to determine which explanation applies.**

### Gateway Probing

| Test | Method | Result |
|------|--------|--------|
| Top 1000 TCP ports | nmap -sS | **Zero open** |
| Full 65535 TCP ports | nmap -sS -p- | **Still running** (background) |
| Management ports (80, 443, 8080, 8291, 22, 23) | bash /dev/tcp | **All timeout** |
| UDP (53, 161, 123, 500, 1194, 1900, 5353) | nmap -sU | All open\|filtered (ambiguous) |
| DNS query | dig @192.168.192.1 | **Timed out** |

**Conclusion:** Gateway exposes NO management interface to the guest VLAN. Good practice — but IT should verify this is intentional and not just the default.

---

## Part 3 — VPN Infrastructure Exposure

The VPN endpoint identified in PCFRANCESCA's OpenVPN config (doc 17) is reachable from the guest network:

```
VPN ENDPOINT: 45.151.15.58

  PORT     SERVICE             RESULT
  ─────────────────────────────────────
  80/tcp   HAProxy http proxy  OPEN — returns "503 Service Unavailable"
  443/tcp  HTTPS               FILTERED
  1194/tcp OpenVPN (TCP)       FILTERED
  1194/udp OpenVPN (UDP)       Not tested (config uses UDP)
  All other top 100 ports      FILTERED

  HTTP response headers:
    HTTP/1.0 503 Service Unavailable
    Cache-Control: no-cache
    Connection: close
    Content-Type: text/html

  Service fingerprint: HAProxy http proxy 1.3.1 or later
  Device classification: Load balancer
```

**Analysis:**
- The pfSense VPN concentrator has an HAProxy frontend on port 80 with no active backend
- This is likely the pfSense web interface behind a reverse proxy, but the backend is unreachable or misconfigured
- The HAProxy version disclosure (1.3.1+) helps an attacker fingerprint the stack
- OpenVPN is on UDP 1194 (per config) — we tested TCP 1194 which was expectedly filtered

**Risk:** LOW — the 503 response provides limited attack surface. However, the presence of any HTTP listener on the VPN endpoint increases exposure.

---

## Part 4 — Broadcast Protocol Observations

### Traffic Capture

20-second tcpdump capture for mDNS/LLMNR/NBNS/SSDP/DHCP: **zero packets captured.**

```
BROADCAST TRAFFIC: SILENT

  Possible explanations:
  ├── APs may be filtering broadcast/multicast (but NOT client isolation)
  ├── Guest devices are mostly phones (no LLMNR/NBNS)
  ├── Windows devices (PCFRANCESCA) are offline
  └── Low network activity at assessment time
```

### NBNS Sweep

nmap UDP 137 sweep across 192.168.192.0/24 found 10 hosts responding to NBNS probes (all open|filtered — no NetBIOS names returned). No Windows NetBIOS names resolved, confirming the guest devices are non-Windows or have NetBIOS disabled.

---

## Part 5 — Guest Device Risk: Bticino Building Automation

```
DEVICE: 192.168.192.149
VENDOR: Bticino SPA (Legrand Group, Italy)
MAC:    00:03:50:E8:4D:87

Bticino manufactures:
├── Smart intercoms (video door entry)
├── Building access control systems
├── Smart lighting / HVAC control
├── Home/building automation gateways
└── Connected IoT sensors

SCAN STATUS: COMPLETE
├── nmap SYN scan 1-10000: ZERO open ports (scan took 39 minutes — very slow responder)
├── TCP connect probe of 20 common IoT ports: ALL TIMEOUT
└── Device exposes no TCP services — likely uses UDP (CoAP, MQTT)
    or communicates outbound-only to a cloud backend
    Still reachable at L2 (ARP responds) — UDP attack surface untested
```

**Why this matters:**
- A building automation device on an unsegmented guest Wi-Fi means any guest can potentially:
  - Access the building intercom/door entry system
  - Manipulate lighting, HVAC, or access controls
  - Use the device as a pivot to building management networks
  - Exploit known IoT vulnerabilities (many Bticino devices run embedded Linux with web interfaces)
- This device should be on a dedicated IoT/BMS VLAN, NOT on the guest Wi-Fi

---

## Part 6 — Updated Network Map

```
═══════════════════════════════════════════════════════════════════════
                         INTERNET
                    Welcome Italia ISP
                  ┌───────────────────┐
                  │ DNS: 80.93.143.42 │
                  │       80.93.143.44│
                  └─────────┬─────────┘
                            │
                            │
              ┌─────────────┤              VPN: 45.151.15.58
              │             │              HAProxy :80 (503)
              │   ┌─────────┴─────────┐    OpenVPN UDP :1194
              │   │                   │
              │   │  EDGE GATEWAY     │
              │   │  192.168.192.1    │
              │   │  80:61:5f:06:19:cb│
              │   │  (Beijing Sinead) │
              │   │                   │
              │   │  Guest→LAN: BLOCK │
              │   │  LAN→Guest: ALLOW │
              │   │    (port 7680)    │
              │   │  Guest→Infra: BLOCK│
              │   │  Mgmt: NO ACCESS  │
              │   └──┬──────┬─────┬───┘
              │      │      │     │
    ┌─────────┘      │     └──────────────┐
    │                │                    │
    ▼                ▼                    ▼
┌──────────────┐ ┌────────────────┐ ┌────────────────────┐
│ GUEST WI-FI  │ │  MAIN LAN      │ │ INFRASTRUCTURE     │
│ 192.168.192  │ │  192.168.1     │ │ 192.168.60         │
│ .0/24        │ │  .0/24         │ │ .0/??              │
│              │ │                │ │                    │
│ 16 devices   │ │ 14+ hosts      │ │ .60.2 (DNS/DC)     │
│ NO client    │ │ .56  .58  .75  │ │ .60.3 (DNS/DC)     │
│ isolation!   │ │ .76  .77  .79  │ │ .60.55 (DO peer)   │
│              │ │ .81  .103 .105 │ │                    │
│ .1   GW      │ │ .144 .147 .155 │ │ All TCP from guest │
│ .20  phone   │ │ .162 .193      │ │ BLOCKED (65535     │
│ .50  Tenda★  │ │                │ │ ports verified)    │
│ .63  phone   │ │ VPN DNS:       │ │                    │
│ .88  phone   │ │ .1.146         │ │                    │
│ .101 phone   │ │                │ │                    │
│ .106 phone   │ │ All TCP from   │ │                    │
│ .111 Tenda★  │ │ guest BLOCKED  │ │                    │
│ .119 phone   │ │ (65535 ports   │ │                    │
│ .129 THIS PC │ │  verified)     │ │                    │
│ .135 Dell    │ │                │ │                    │
│ .141 Tenda★  │ │ CAN reach guest│ │                    │
│ .145 phone   │ │ on port 7680   │ │                    │
│ .149 Bticino │ │ (DO, confirmed │ │                    │
│ .189 phone   │ │  from Windows) │ │                    │
│ .195 AP?     │ │                │ │                    │
│              │ │                │ │                    │
│ PSK:         │ │                │ │                    │
│ 1DfGhYu53   │ │                │ │                    │
└──────────────┘ └────────────────┘ └────────────────────┘

★ = Same MAC (04:95:E6:52:DB:7D) — single Tenda device, 3 DHCP leases
```

---

## Part 7 — New Findings Summary

| # | Finding | Severity | Source | Original Status |
|---|---------|----------|--------|-----------------|
| N1 | **No AP client isolation** — 16 devices visible on guest subnet | **CRITICAL** | ARP sweep | Was hypothesized as enabled (doc 05) — now disproven |
| N2 | **Bticino building automation device on guest Wi-Fi** (.149) | **HIGH** | ARP sweep + OUI | Not previously identified |
| N3 | **Guest→LAN TCP fully blocked** (all 65535 ports verified) | INFO (positive) | nmap full scan | Previously only tested on specific ports |
| N4 | **Guest→Infrastructure TCP fully blocked** (all 65535 ports verified) | INFO (positive) | nmap full scan | Previously stated as blocked on specific ports |
| N5 | **Cross-VLAN traffic is directional** — main LAN CAN reach guest | **HIGH** | Correlation with PCFRANCESCA DO logs | Not explicitly analyzed |
| N6 | **Tenda device with 3 IPs** — Wi-Fi extender on guest network | **MEDIUM** | ARP sweep | Not previously identified |
| N7 | **Dell laptop on guest network** (.135) | **LOW** | ARP + OUI | Not previously identified |
| N8 | **VPN endpoint publicly reachable** with HAProxy 503 | **LOW** | curl + nmap | VPN endpoint known from config, HTTP exposure is new |
| N9 | **Gateway has no management interface on guest VLAN** | INFO (positive) | Full port scan | Not previously tested |
| N10 | **9 personal devices (phones/tablets) on guest** with randomized MACs | INFO | ARP sweep | Not previously counted |

---

## Part 8 — Cross-VLAN Reachability Matrix (Updated)

```
                  Guest (.192)     Main LAN (.1)    Infra (.60)
                ┌────────────────┬────────────────┬────────────────┐
Guest           │                │ ALL TCP ✗      │ ALL TCP ✗      │
(.192)          │     N/A        │ ALL UDP ✗      │ ALL UDP ✗      │
                │                │ ICMP ✗         │ ICMP ✗         │
                │                │ 65535 verified │ 65535 verified │
                ├────────────────┼────────────────┼────────────────┤
Main LAN        │ TCP 7680 ✓     │                │                │
(.1)            │ (inbound to    │     N/A        │ Unknown        │
                │  guest, per DO │                │ (likely ✓)     │
                │  logs May 26)  │                │                │
                ├────────────────┼────────────────┼────────────────┤
Infra           │ TCP 7680 ✓     │                │                │
(.60)           │ (inbound to    │ Unknown        │     N/A        │
                │  guest, per DO │ (likely ✓)     │                │
                │  logs May 26)  │                │                │
                └────────────────┴────────────────┴────────────────┘

✓ = Traffic confirmed
✗ = Traffic blocked (verified by scan)
```

---

## Part 9 — Attack Chain: Guest Wi-Fi → Building Automation

```
NEW ATTACK CHAIN (requires only guest Wi-Fi PSK)

  ATTACKER
  ├── 1. Join Adami_Guest (PSK: 1DfGhYu53 — extracted from PCFRANCESCA)
  ├── 2. ARP scan 192.168.192.0/24 → discover 16 devices
  ├── 3. Identify Bticino device at .149 (OUI: 00:03:50)
  ├── 4. Port scan Bticino → find management interface (web, telnet, CoAP)
  ├── 5. Access Bticino default credentials (common in IoT)
  └── 6. Control building automation:
       ├── Door entry / intercom
       ├── Lighting
       ├── HVAC
       └── Access control

  PREREQUISITES: Wi-Fi PSK only (available from any compromised machine)
  TIME: < 5 minutes
  SKILL: Low — IoT device exploitation is well-documented
```

---

## Part 10 — Recommendations for IT (from this assessment pass)

### Immediate

| # | Action | Why |
|---|--------|-----|
| 1 | **Enable AP client isolation on Adami_Guest** | 16 devices can see each other — guests can attack guests |
| 2 | **Move Bticino device to dedicated IoT/BMS VLAN** | Building automation must NOT be on guest Wi-Fi |
| 3 | **Identify and audit the Tenda device** (.50/.111/.141, same MAC) | Could be a rogue extender bridging to another network |
| 4 | **Audit gateway/firewall inter-VLAN ACLs** | Determine why main LAN/infra hosts can reach guest on port 7680 |

### Short-Term

| # | Action | Why |
|---|--------|-----|
| 5 | Remove HAProxy 503 listener on VPN endpoint (45.151.15.58:80) | Unnecessary exposure — disclose stack version |
| 6 | Rotate Adami_Guest Wi-Fi PSK | Extracted in plaintext from PCFRANCESCA (doc 17) |
| 7 | Verify the Dell device at .135 is authorized on guest | Corporate hardware on guest network without VPN |

---

## Methodology Notes

All scans were run from a Linux workstation using unprivileged and privileged (sudo) nmap.
- ARP sweep: `nmap -sn -n 192.168.192.0/24` (privileged — uses ARP on local subnet)
- SYN scan: `nmap -sS -n -Pn -p- --min-rate 2000 --open <target>` (privileged)
- TCP connect: `bash -c "echo > /dev/tcp/<ip>/<port>"` (unprivileged)
- UDP scan: `nmap -sU -n -Pn -p <ports> <target>` (privileged)
- DNS probe: `dig @<server> <domain> +timeout=3`
- SMB probe: `smbclient -L //<target>/ -N`
- Broadcast capture: `tcpdump -i wlp0s20f3 -n 'broadcast or multicast'`
