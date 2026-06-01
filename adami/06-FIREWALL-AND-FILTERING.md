# 06 — Firewall & Packet Filtering

## Windows Firewall Profiles

```
┌─────────────────────────────────────────────────────────────┐
│                WINDOWS DEFENDER FIREWALL                      │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────┐       │
│  │   DOMAIN     │  │   PRIVATE   │  │   PUBLIC ★   │       │
│  │   Profile    │  │   Profile   │  │   Profile    │       │
│  │              │  │             │  │  (ACTIVE)    │       │
│  │  Enabled: ✓  │  │  Enabled: ✓ │  │  Enabled: ✓  │       │
│  │  Inbound:    │  │  Inbound:   │  │  Inbound:    │       │
│  │  NotConfig'd │  │  NotConfig'd│  │  NotConfig'd │       │
│  │  (=Block)    │  │  (=Block)   │  │  (=Block)    │       │
│  │              │  │             │  │              │       │
│  │  Outbound:   │  │  Outbound:  │  │  Outbound:   │       │
│  │  NotConfig'd │  │  NotConfig'd│  │  NotConfig'd │       │
│  │  (=Allow)    │  │  (=Allow)   │  │  (=Allow)    │       │
│  └─────────────┘  └─────────────┘  └──────────────┘       │
│                                                             │
│  ★ Current network "Adami_Guest" uses PUBLIC profile       │
│    (most restrictive default behavior)                      │
└─────────────────────────────────────────────────────────────┘
```

## Active Profile Analysis

The `Adami_Guest` network is classified as **Public**, which means:
- Default inbound: **Block** (unless explicitly allowed)
- Default outbound: **Allow** (all outbound traffic permitted)
- File/printer sharing: Restricted
- Network discovery: Limited

## Inbound Allow Rules (Active on Public Profile)

Key rules allowing inbound connections on the Public profile:

### Network Infrastructure Rules
| Rule | Protocol | Port | Profile | Risk |
|------|----------|------|---------|------|
| DHCP (DHCPv4/v6) | UDP | 67-68 | Any | Required — low risk |
| IPv6 basic | IPv6 | - | Any | Required — low risk |
| IGMP | IGMP | - | Any | Multicast — low risk |
| Router Discovery (ICMPv6) | ICMPv6 | - | Any | Required — low risk |
| Fragmentation Needed (ICMPv4) | ICMPv4 | - | Any | PMTUD — low risk |

### Application Rules (Public Profile)
| Rule | Direction | Notes |
|------|-----------|-------|
| **AnyDesk** (×5 rules) | Inbound Allow | **All profiles** — remote access from any network |
| LLMNR (UDP) | Inbound Allow | Public — broadcast name resolution |
| NetBIOS Name (NB-Name-In) | Inbound Allow | Public — NetBIOS discovery |
| SSDP (UPnP) | Inbound Allow | Public — device discovery |
| Delivery Optimization (TCP+UDP) | Inbound Allow | **Any profile** — update peering |
| File/Printer Sharing (ICMP) | Inbound Allow | Echo request — ping |
| File/Printer Sharing (SMB) | Inbound Allow | TCP 445 — **file sharing** |
| File/Printer Sharing (NB-*) | Inbound Allow | NetBIOS — file sharing |
| File/Printer Sharing (Spooler) | Inbound Allow | RPC — print services |
| Wi-Fi Direct | Inbound Allow | TCP+UDP — direct connections |
| Microsoft Teams | Inbound Allow | UDP — call signaling |
| Skype | Inbound Allow | Multiple rules |
| WhatsApp | Inbound Allow | App rule |
| Microsoft Office (OneNote, Groove, Outlook) | Inbound Allow | Office networking |

### Critical Concern: AnyDesk Firewall Rules

```
⚠ AnyDesk has FIVE inbound allow rules
  covering ALL firewall profiles (Domain, Private, Public).
  This means AnyDesk accepts inbound connections
  from ANY network, including untrusted public networks.

  ┌─────────────────────────────────────┐
  │  AnyDesk Inbound Allow:            │
  │  - Rule 1: Inbound TCP (All)       │
  │  - Rule 2: Inbound TCP (All)       │
  │  - Rule 3: Inbound UDP (All)       │
  │  - Rule 4: Inbound TCP (All)       │
  │  - Rule 5: Inbound UDP (All)       │
  │                                     │
  │  Profile: Domain, Private, Public  │
  │  Remote Address: Any               │
  └─────────────────────────────────────┘
```

## Outbound Rules

Default outbound action is **Allow** for all profiles, meaning:
- All applications can initiate outbound connections freely
- No application-level egress filtering
- Data exfiltration paths are unrestricted

## Gateway-Level Filtering (Observed Behavior)

The gateway at 192.168.192.1 performs additional filtering beyond the Windows firewall:

| Test | Result | Implication |
|------|--------|-------------|
| ICMP to gateway | **Blocked** | Gateway drops ping even to itself |
| ICMP to 192.168.1.x | **Blocked** | No cross-VLAN ICMP |
| ICMP to 192.168.60.x | **Blocked** | No cross-VLAN ICMP |
| TCP 7680 to 192.168.1.x | **Allowed** | Delivery Optimization crosses VLANs |
| TCP 445 to 192.168.1.1 | **Blocked** | SMB cross-VLAN blocked |
| TCP 53 to 192.168.60.2 | **Blocked** | DNS to internal servers blocked |

## Firewall Effectiveness Assessment

```
INBOUND PROTECTION SCORE: ██████░░░░ 6/10

+ Public profile active (restrictive)
+ Default inbound block
- AnyDesk allows inbound from ANY
- SMB/file sharing rules active on Public
- LLMNR/NetBIOS inbound allowed on Public
- No custom hardening rules

OUTBOUND PROTECTION SCORE: ██░░░░░░░░ 2/10

- Default outbound allow (no filtering)
- No application whitelisting
- No egress restrictions
- Any process can reach any external host
- Data exfiltration trivially possible
```
