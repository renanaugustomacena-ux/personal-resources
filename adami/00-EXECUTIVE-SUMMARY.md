# Network Infrastructure Assessment — Executive Summary

**Target:** Adami Trasporti corporate network  
**Assessment Date:** 2026-05-19  
**Assessor:** sandro (Senior Cybersecurity)  
**Machine:** PCFRANCESCA (192.168.192.61)  
**Assessment Type:** Non-aggressive internal reconnaissance from guest Wi-Fi segment  

---

## Scope

Passive and low-impact enumeration from a single Windows 11 endpoint connected to the `Adami_Guest` Wi-Fi network. No active scanning, exploitation, or traffic interception was performed.

## Network Overview

```
                              ┌─────────────────┐
                              │    INTERNET      │
                              │  Welcome Italia  │
                              │  ISP DNS:        │
                              │  80.93.143.42    │
                              │  80.93.143.44    │
                              └────────┬─────────┘
                                       │
                              ┌────────┴─────────┐
                              │  GATEWAY/ROUTER  │
                              │  192.168.192.1   │
                              │  MAC: 80:61:5f:  │
                              │  06:19:cb        │
                              │  (DHCP + GW)     │
                              └──┬─────┬─────┬───┘
                                 │     │     │
                ┌────────────────┤     │     ├────────────────┐
                │                │     │     │                │
     ┌──────────┴──────┐  ┌─────┴─────┴┐  ┌┴──────────────┐  │
     │  GUEST WI-FI    │  │  MAIN LAN  │  │ INFRASTRUCTURE│  │
     │  192.168.192.0  │  │ 192.168.1  │  │  192.168.60   │  │
     │  /24            │  │ .0/24      │  │  .0/x         │  │
     │                 │  │            │  │               │  │
     │ ★ THIS MACHINE │  │ 12+ hosts  │  │ DNS .60.2     │  │
     │ .192.61        │  │ observed   │  │ DNS .60.3     │  │
     │                 │  │            │  │ (likely DCs)  │  │
     │ 7 Enterprise   │  │            │  │               │  │
     │ Access Points   │  │            │  │               │  │
     └─────────────────┘  └────────────┘  └───────────────┘  │
                                                              │
                                                    Saved SSID:
                                                    "montresor"
```

**3 subnets discovered** through passive observation:

| Subnet | Role | Discovery Method |
|--------|------|-----------------|
| 192.168.192.0/24 | Guest Wi-Fi | Direct connection |
| 192.168.1.0/24 | Main LAN (~12+ hosts) | Delivery Optimization peer traffic |
| 192.168.60.0/x | Infrastructure/servers | Ethernet adapter DNS config |

## Critical Findings Summary

| # | Severity | Finding | Risk |
|---|----------|---------|------|
| 1 | **CRITICAL** | SMB1 enabled, signing not required, no encryption | EternalBlue, relay attacks, traffic sniffing |
| 2 | **CRITICAL** | Guest-to-LAN traffic allowed (port 7680) | Network segmentation failure |
| 3 | **HIGH** | Admin account has no password | Instant local/remote compromise |
| 4 | **HIGH** | AnyDesk auto-start with external relay | Persistent remote access backdoor |
| 5 | **HIGH** | LLMNR + NetBIOS enabled | Broadcast poisoning (Responder) |
| 6 | **HIGH** | C:\Users shared to Everyone with Full access | Sensitive data exposure |
| 7 | **HIGH** | Windows Defender fully disabled | Reduced defense-in-depth |
| 8 | **MEDIUM** | Avast TLS interception active | Breaks cert pinning, trust bottleneck |
| 9 | **MEDIUM** | No VPN from guest to corporate | No secure tunnel to corp resources |
| 10 | **MEDIUM** | No BitLocker encryption | Physical theft = data compromise |
| 11 | **MEDIUM** | WHEA hardware errors flooding system log | Hardware reliability concern |
| 12 | **LOW** | PowerShell Bypass execution policy | Script execution unrestricted |

## Expanded Assessment (2026-05-26)

A second-pass assessment on 2026-05-26 deepened the original findings with live data extraction, full credential inventories, and methodology documentation. Key additions:

| # | New Finding | Severity |
|---|-------------|----------|
| 1 | Infrastructure subnet (192.168.60.55) reachable from guest Wi-Fi | **CRITICAL** |
| 2 | CHIARA ghost user profile with VPN certs, browser passwords still on disk | **HIGH** |
| 3 | elena.malini domain account cached with DCC2 hashes | **HIGH** |
| 4 | VPN certificate (CN=francescav) + TLS key extracted — no PKCS12 password | **CRITICAL** |
| 5 | AnyDesk private key + password hash + full connection log extracted | **CRITICAL** |
| 6 | Wi-Fi PSKs extracted in plaintext for both Adami_Guest and montresor | **HIGH** |
| 7 | itgroup@adamitrasporti.com shared IT account cached in credential manager | **HIGH** |
| 8 | No user logon auditing configured — zero forensic trail | **HIGH** |
| 9 | AnyDesk REJECTED connection from unknown ID 619901193 | **MEDIUM** |
| 10 | 576 firewall rules, many allowing inbound on Public profile | **MEDIUM** |

**Total findings after expansion: 27 original + 14 new = 41 findings.**

See [16-EXPANDED-NETWORK-ASSESSMENT.md](16-EXPANDED-NETWORK-ASSESSMENT.md) and [17-IDENTITY-ACCESS-INVENTORY.md](17-IDENTITY-ACCESS-INVENTORY.md) for full details.

## Live Enumeration (2026-05-28)

A third assessment pass from a Linux workstation (192.168.192.129) on Adami_Guest validated and extended prior findings:

| # | New Finding | Severity |
|---|-------------|----------|
| 1 | No AP client isolation — 16 devices visible on guest network | **CRITICAL** |
| 2 | Bticino building automation device on guest Wi-Fi | **HIGH** |
| 3 | Cross-VLAN traffic is directional — main LAN CAN reach guest hosts | **HIGH** |
| 4 | Guest→LAN TCP fully blocked (all 65535 ports verified) | INFO (positive) |
| 5 | Guest→Infrastructure TCP fully blocked (all 65535 ports verified) | INFO (positive) |
| 6 | Tenda Wi-Fi extender with 3 IPs on guest — investigate for bridging | **MEDIUM** |

**Total findings after all three passes: 41 original + 10 new = 51 findings.**

See [18-LIVE-ENUMERATION-2026-05-28.md](18-LIVE-ENUMERATION-2026-05-28.md) for full details.

---

## Document Index

| File | Contents |
|------|----------|
| [01-NETWORK-TOPOLOGY.md](01-NETWORK-TOPOLOGY.md) | Full network topology, subnets, routing |
| [02-HOST-IDENTITY.md](02-HOST-IDENTITY.md) | Machine identity, OS, domain status |
| [03-NETWORK-INTERFACES.md](03-NETWORK-INTERFACES.md) | All NICs, MACs, IPs, configurations |
| [04-ROUTING-AND-DNS.md](04-ROUTING-AND-DNS.md) | Routing tables, DNS servers, cache |
| [05-WIFI-INFRASTRUCTURE.md](05-WIFI-INFRASTRUCTURE.md) | SSIDs, APs, channels, security |
| [06-FIREWALL-AND-FILTERING.md](06-FIREWALL-AND-FILTERING.md) | Firewall profiles and rules |
| [07-LISTENING-SERVICES.md](07-LISTENING-SERVICES.md) | TCP/UDP ports and process mapping |
| [08-OUTBOUND-CONNECTIONS.md](08-OUTBOUND-CONNECTIONS.md) | External connections inventory |
| [09-SMB-FILE-SHARING.md](09-SMB-FILE-SHARING.md) | SMB config, shares, permissions |
| [10-BROADCAST-PROTOCOLS.md](10-BROADCAST-PROTOCOLS.md) | LLMNR, NetBIOS, mDNS, WPAD analysis |
| [11-SECURITY-SOFTWARE.md](11-SECURITY-SOFTWARE.md) | Avast, Defender, certificates |
| [12-USER-ACCOUNTS.md](12-USER-ACCOUNTS.md) | Local accounts, privileges, policy |
| [13-INSTALLED-SOFTWARE.md](13-INSTALLED-SOFTWARE.md) | Software inventory and versions |
| [14-SECURITY-FINDINGS.md](14-SECURITY-FINDINGS.md) | Full vulnerability report with remediation |
| [15-ATTACK-SURFACE-MAP.md](15-ATTACK-SURFACE-MAP.md) | Attack surface diagram and analysis |
| [16-EXPANDED-NETWORK-ASSESSMENT.md](16-EXPANDED-NETWORK-ASSESSMENT.md) | **NEW** — Deep-dive network reassessment, methodology, 14 new findings |
| [17-IDENTITY-ACCESS-INVENTORY.md](17-IDENTITY-ACCESS-INVENTORY.md) | **NEW** — Complete credential dump: accounts, passwords, VPN keys, AnyDesk keys, Wi-Fi PSKs |
| [18-LIVE-ENUMERATION-2026-05-28.md](18-LIVE-ENUMERATION-2026-05-28.md) | **NEW** — Live nmap/active scanning from Linux on guest Wi-Fi: client isolation disproven, full cross-VLAN port verification, guest device inventory |
