# 01 — Network Topology

## Overview

The Adami Trasporti network uses a multi-subnet architecture behind a single gateway device. Three distinct network segments were identified through passive observation from the guest Wi-Fi segment.

## Topology Diagram

```
═══════════════════════════════════════════════════════════════════════
                         INTERNET
                    Welcome Italia ISP
                  ┌───────────────────┐
                  │ DNS Primary:      │
                  │ 80.93.143.42      │
                  │ (dnsunico.        │
                  │  welcomeitalia.it)│
                  │                   │
                  │ DNS Secondary:    │
                  │ 80.93.143.44      │
                  └─────────┬─────────┘
                            │
═══════════════════════════════════════════════════════════════════════
                            │ WAN Uplink
                            │
                  ┌─────────┴─────────┐
                  │                   │
                  │  EDGE GATEWAY     │
                  │  192.168.192.1    │
                  │                   │
                  │  MAC: 80:61:5f:   │
                  │       06:19:cb    │
                  │                   │
                  │  Roles:           │
                  │  - Default GW     │
                  │  - DHCP Server    │
                  │  - Inter-VLAN     │
                  │    routing        │
                  │  - Firewall       │
                  │    (ICMP blocked, │
                  │     some TCP      │
                  │     allowed)      │
                  │                   │
                  └──┬──────┬─────┬───┘
                     │      │     │
       ┌─────────────┘      │     └─────────────┐
       │                    │                   │
       ▼                    ▼                   ▼
┌──────────────┐   ┌───────────────┐   ┌───────────────┐
│ VLAN/SUBNET  │   │ VLAN/SUBNET   │   │ VLAN/SUBNET   │
│    GUEST     │   │   MAIN LAN    │   │ INFRASTRUCTURE│
│              │   │               │   │               │
│ 192.168.192  │   │ 192.168.1     │   │ 192.168.60    │
│ .0/24        │   │ .0/24         │   │ .0/??         │
│              │   │               │   │               │
│ SSID:        │   │ Wired +       │   │ Servers       │
│ Adami_Guest  │   │ Corporate     │   │ Domain Ctrlrs │
│              │   │ Wi-Fi?        │   │               │
│ Profile:     │   │               │   │               │
│ Public       │   │               │   │               │
│              │   │               │   │               │
│ Security:    │   │               │   │               │
│ WPA3-Personal│   │               │   │               │
└──────┬───────┘   └───────┬───────┘   └───────┬───────┘
       │                   │                   │
       │                   │                   │
   ┌───┴────┐        ┌─────┴──────┐      ┌────┴─────┐
   │THIS PC │        │ Known hosts│      │ Known    │
   │.192.61 │        │ (observed  │      │ hosts    │
   │        │        │  via DO):  │      │          │
   │PCFRAN- │        │            │      │ .60.2    │
   │CESCA   │        │ .1.56      │      │ (DNS #1) │
   │        │        │ .1.58      │      │          │
   └────────┘        │ .1.75      │      │ .60.3    │
                     │ .1.76      │      │ (DNS #2) │
                     │ .1.77      │      │          │
                     │ .1.79      │      └──────────┘
                     │ .1.81      │
                     │ .1.103     │
                     │ .1.144     │
                     │ .1.147     │
                     │ .1.155     │
                     │ .1.162     │
                     │ .1.193     │
                     └────────────┘
```

## Subnet Details

### Subnet 1: Guest Wi-Fi — 192.168.192.0/24

| Property | Value |
|----------|-------|
| Network | 192.168.192.0/24 |
| Mask | 255.255.255.0 |
| Gateway | 192.168.192.1 |
| DHCP Server | 192.168.192.1 (same device as GW) |
| DHCP Lease | 4 hours |
| DNS Servers | 80.93.143.42, 80.93.143.44 (ISP — external) |
| DNS Suffix | adamitrasporti.local |
| SSID | Adami_Guest |
| Wi-Fi Security | WPA3-Personal / CCMP |
| Windows Profile | **Public** |
| Known Hosts | 1 (this machine) |
| Access Points | 7 (see [05-WIFI-INFRASTRUCTURE.md](05-WIFI-INFRASTRUCTURE.md)) |

### Subnet 2: Main LAN — 192.168.1.0/24

| Property | Value |
|----------|-------|
| Network | 192.168.1.0/24 (assumed /24) |
| Discovery Method | Windows Delivery Optimization peer connections (port 7680) |
| Known Hosts | 12+ unique IPs observed |
| Reachability | TCP port 7680 confirmed; ICMP blocked; SMB (445) blocked from guest |
| Host List | .56, .58, .75, .76, .77, .79, .81, .103, .144, .147, .155, .162, .193 |

### Subnet 3: Infrastructure — 192.168.60.0/x

| Property | Value |
|----------|-------|
| Network | 192.168.60.0 (mask unknown) |
| Discovery Method | Ethernet adapter static DNS configuration |
| Known Hosts | 192.168.60.2 (DNS), 192.168.60.3 (DNS) |
| Likely Role | AD Domain Controllers for adamitrasporti.local |
| Reachability from Guest | **NOT reachable** (TCP/53 and ICMP both fail) |

## Inter-Subnet Communication Matrix

```
                  Guest           Main LAN        Infrastructure
                  192.168.192.x   192.168.1.x     192.168.60.x
                ┌───────────────┬───────────────┬───────────────┐
Guest           │               │               │               │
192.168.192.x   │     N/A       │ TCP 7680 ✓    │    ALL ✗      │
                │               │ ICMP ✗        │               │
                │               │ TCP 445 ✗     │               │
                ├───────────────┼───────────────┼───────────────┤
Main LAN        │               │               │               │
192.168.1.x     │ TCP 7680 ✓    │     N/A       │  Unknown      │
                │ (inbound seen)│               │  (likely ✓)   │
                ├───────────────┼───────────────┼───────────────┤
Infrastructure  │               │               │               │
192.168.60.x    │    ALL ✗      │   Unknown     │     N/A       │
                │               │  (likely ✓)   │               │
                └───────────────┴───────────────┴───────────────┘

✓ = Traffic observed/confirmed
✗ = Traffic blocked/unreachable
```

## Gateway Analysis

The device at 192.168.192.1 serves multiple roles:

```
┌─────────────────────────────────────────────┐
│              GATEWAY DEVICE                  │
│           192.168.192.1                      │
│           MAC: 80:61:5f:06:19:cb            │
│                                              │
│  ┌──────────────┐  ┌──────────────────┐     │
│  │  DHCP Server │  │  Default Gateway │     │
│  │              │  │                  │     │
│  │ Pool: .0/24  │  │  Routes traffic  │     │
│  │ Lease: 4hrs  │  │  to internet     │     │
│  │ Suffix:      │  │  and between     │     │
│  │ adamitrasporti│  │  VLANs          │     │
│  │ .local       │  │                  │     │
│  └──────────────┘  └──────────────────┘     │
│                                              │
│  ┌──────────────┐  ┌──────────────────┐     │
│  │  Firewall    │  │  Inter-VLAN      │     │
│  │              │  │  Router          │     │
│  │ Blocks ICMP  │  │                  │     │
│  │ cross-VLAN   │  │ Allows specific  │     │
│  │              │  │ TCP (7680) cross │     │
│  │ Blocks SMB   │  │ VLAN             │     │
│  │ cross-VLAN   │  │                  │     │
│  └──────────────┘  └──────────────────┘     │
│                                              │
│  MAC OUI: 80:61:5f = unknown/custom         │
│  Possible: enterprise router/firewall       │
│  (FortiGate, Sophos, MikroTik, etc.)        │
└─────────────────────────────────────────────┘
```

## Key Observations

1. **Segmentation is partial** — Guest cannot reach infrastructure (60.x) or main LAN (1.x) on most ports, but Delivery Optimization traffic (7680) crosses from guest to main LAN. This is a policy gap.

2. **DNS architecture mismatch** — Guest network gets ISP DNS (Welcome Italia) instead of internal DNS. The Ethernet adapter is configured for internal DNS (192.168.60.2/3), suggesting the machine was originally on the wired network.

3. **No VPN tunnel** — There is no VPN configured to bridge the guest segment back to corporate resources. The machine is effectively isolated from corporate services that require internal DNS resolution.

4. **DHCP lease is short** (4 hours) — typical for guest networks but aggressive for a machine that should maintain persistent connections.

5. **ICMP is blocked cross-VLAN** — tracert to both 192.168.1.x and the gateway itself times out, suggesting ICMP is filtered at the gateway level.
