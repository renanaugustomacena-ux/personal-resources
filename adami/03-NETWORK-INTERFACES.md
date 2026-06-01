# 03 — Network Interfaces

## Interface Summary

```
┌──────────────────────────────────────────────────────────────┐
│                    NETWORK ADAPTERS                           │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [ACTIVE] Wi-Fi                             │              │
│  │ Intel(R) Wi-Fi 6 AX201 160MHz             │              │
│  │ MAC: E8:84:A5:E2:17:D3                    │              │
│  │ Status: Connected @ 650 Mbps              │              │
│  │ IP: 192.168.192.61/24                     │              │
│  │ GW: 192.168.192.1                         │              │
│  │ DHCP: Yes (from 192.168.192.1)            │              │
│  │ DNS: 80.93.143.42, 80.93.143.44           │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [DISCONNECTED] Ethernet                    │              │
│  │ Realtek PCIe GbE Family Controller         │              │
│  │ MAC: 6C:02:E0:9A:FA:48                    │              │
│  │ Status: Media disconnected                 │              │
│  │ IP: APIPA (169.254.56.113)                │              │
│  │ Configured DNS: 192.168.60.2, 192.168.60.3│              │
│  │ DHCP: Yes (suffix: adamitrasporti.local)  │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [DISCONNECTED] Wi-Fi Direct #3             │              │
│  │ Microsoft Wi-Fi Direct Virtual Adapter #3  │              │
│  │ MAC: E8:84:A5:E2:17:D4                    │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [DISCONNECTED] Wi-Fi Direct #4             │              │
│  │ Microsoft Wi-Fi Direct Virtual Adapter #4  │              │
│  │ MAC: EA:84:A5:E2:17:D3                    │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [DISCONNECTED] Bluetooth PAN               │              │
│  │ Bluetooth Device (Personal Area Network)   │              │
│  │ MAC: E8:84:A5:E2:17:D7                    │              │
│  │ Link Speed: 3 Mbps (max)                  │              │
│  └────────────────────────────────────────────┘              │
│                                                              │
│  ┌────────────────────────────────────────────┐              │
│  │ [VIRTUAL] Kernel Debug Network Adapter     │              │
│  │ No MAC / No IP                             │              │
│  │ (Debug interface — inactive)               │              │
│  └────────────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────┘
```

## Active Interface — Wi-Fi Detail

| Property | Value |
|----------|-------|
| Adapter | Intel(R) Wi-Fi 6 AX201 160MHz |
| MAC Address | E8:84:A5:E2:17:D3 |
| Status | Connected |
| Link Speed | 650 Mbps (capable of 866.7 Mbps) |
| IPv4 Address | 192.168.192.61 |
| Subnet Mask | 255.255.255.0 (/24) |
| Default Gateway | 192.168.192.1 |
| DHCP Server | 192.168.192.1 |
| DHCP Enabled | Yes |
| Lease Obtained | 2026-05-19 08:38:46 |
| Lease Expires | 2026-05-19 12:38:46 (4-hour lease) |
| DNS Servers | 80.93.143.42, 80.93.143.44 |
| DNS Suffix | adamitrasporti.local |
| IPv6 Link-Local | fe80::d991:b4e6:89db:e6ab%8 |
| NetBIOS over TCP/IP | **Enabled** |
| Node Type | Hybrid |
| WINS Servers | None configured |

## Ethernet Interface — Dormant Config

The Ethernet adapter is disconnected but retains its previous DHCP-learned configuration:

| Property | Value |
|----------|-------|
| Adapter | Realtek PCIe GbE Family Controller |
| MAC Address | 6C:02:E0:9A:FA:48 |
| Status | **Disconnected** |
| Static DNS | 192.168.60.2, 192.168.60.3 |
| DHCP Suffix | adamitrasporti.local |

**This is critical intelligence** — the Ethernet DNS servers (192.168.60.2/3) point to the infrastructure subnet, strongly suggesting these are Active Directory domain controllers that host the `adamitrasporti.local` DNS zone.

## MAC Address Analysis

All wireless adapters share the same OUI base (E8:84:A5 = Intel Corporation):

| Interface | MAC | OUI | Notes |
|-----------|-----|-----|-------|
| Wi-Fi | E8:84:A5:E2:17:D3 | Intel | Physical radio |
| Wi-Fi Direct #3 | E8:84:A5:E2:17:D4 | Intel | Virtual (+1) |
| Wi-Fi Direct #4 | EA:84:A5:E2:17:D3 | Intel (LAA) | Locally administered |
| Bluetooth | E8:84:A5:E2:17:D7 | Intel | Shared radio (+4) |
| Ethernet | 6C:02:E0:9A:FA:48 | Realtek | Separate NIC |

## ARP Neighbor Table

Only one neighbor is known — the gateway:

| IP | MAC | Type | Interface |
|----|-----|------|-----------|
| 192.168.192.1 | 80:61:5F:06:19:CB | Dynamic | Wi-Fi |
| 192.168.192.255 | FF:FF:FF:FF:FF:FF | Static (broadcast) | Wi-Fi |

**The sparse ARP table suggests this machine is the only active host on the guest Wi-Fi segment**, or that other guest clients are isolated from each other (client isolation on the AP).
