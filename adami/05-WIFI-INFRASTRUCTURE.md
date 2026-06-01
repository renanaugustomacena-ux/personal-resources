# 05 — Wi-Fi Infrastructure

## Current Connection

| Property | Value |
|----------|-------|
| SSID | Adami_Guest |
| Connected BSSID | 8E:DC:97:19:9F:AB |
| Band | 5 GHz |
| Channel | 40 |
| Radio Type | 802.11ac (Wi-Fi 5) |
| Authentication | WPA3-Personal |
| Encryption | CCMP (AES) |
| Signal Strength | 83% (-58 dBm) |
| Rx Speed | 866.7 Mbps |
| Tx Speed | 866.7 Mbps |
| Connection Mode | Automatic |

## Access Point Map

7 BSSIDs broadcasting `Adami_Guest` were detected — this is an enterprise-grade multi-AP deployment:

```
                         FLOOR COVERAGE MAP (conceptual)
         ┌────────────────────────────────────────────────────────┐
         │                                                        │
         │   AP1 (5f:ab)        AP2 (3d:a7)        AP3 (6b:a6)  │
         │   ★ 83% 5GHz        26% 5GHz            43% 5GHz     │
         │   ○ 81% 2.4GHz      ○ 33% 2.4GHz        ○ 81% 2.4GHz│
         │                                                        │
         │         ┌──────┐                                       │
         │         │ YOU  │  ← PCFRANCESCA                       │
         │         │ HERE │                                       │
         │         └──────┘                                       │
         │                                                        │
         │                       AP4 (fd:ec)                      │
         │                       29% 2.4GHz only                  │
         │                       (different vendor)               │
         │                                                        │
         └────────────────────────────────────────────────────────┘

         ★ = Connected AP       ○ = Visible but not connected
```

## Full BSSID Inventory

| # | BSSID | Signal | Band | Channel | Radio | OUI Analysis |
|---|-------|--------|------|---------|-------|--------------|
| 1 | 8E:DC:97:19:9F:AB | **83%** | 5 GHz | 40 | 802.11ac | **Connected** — LAA (8E = locally administered) |
| 2 | 8E:DC:97:19:9F:AA | 81% | 2.4 GHz | 11 | 802.11ac | Same AP as #1 (dual-band, last octet ±1) |
| 3 | 8E:DC:97:13:6B:A6 | 43% | 5 GHz | 40 | 802.11ac | LAA — enterprise AP |
| 4 | 8E:DC:97:13:6B:A5 | 81% | 2.4 GHz | 1 | 802.11ac | Same AP as #3 (dual-band) |
| 5 | 8E:DC:97:50:3D:A7 | 26% | 5 GHz | 40 | 802.11ac | LAA — enterprise AP (far) |
| 6 | 8E:DC:97:50:3D:A6 | 33% | 2.4 GHz | 11 | 802.11ac | Same AP as #5 (dual-band) |
| 7 | E0:D3:62:98:FD:EC | 29% | 2.4 GHz | 11 | 802.11n | **Different vendor** — 2.4 only |

## AP Vendor Analysis

```
┌─────────────────────────────────────────────────────────────┐
│                 ACCESS POINT VENDORS                         │
│                                                             │
│  Primary Fleet (6 BSSIDs = 3 physical APs):                │
│  ┌───────────────────────────────────────────┐              │
│  │  OUI: 8E:DC:97                           │              │
│  │  Type: Locally Administered Address (LAA) │              │
│  │                                           │              │
│  │  The "8" in 8E means bit 1 of the first  │              │
│  │  octet is set → locally administered MAC. │              │
│  │  Enterprise APs (Aruba, Ruckus, Cisco,   │              │
│  │  Ubiquiti, FortiAP) commonly use LAA for │              │
│  │  virtual BSSIDs / SSIDs.                  │              │
│  │                                           │              │
│  │  Likely vendor: Unknown without the real  │              │
│  │  base MAC. Common in managed Wi-Fi.       │              │
│  └───────────────────────────────────────────┘              │
│                                                             │
│  Secondary AP (1 BSSID):                                    │
│  ┌───────────────────────────────────────────┐              │
│  │  OUI: E0:D3:62                           │              │
│  │  Type: Universally Administered (real MAC)│              │
│  │  Vendor lookup: Possibly TP-Link, Aruba   │              │
│  │  or other.                                │              │
│  │  Only 2.4 GHz / 802.11n = older or basic │              │
│  │  AP, possibly a range extender.           │              │
│  └───────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────┘
```

## Channel Allocation

```
           2.4 GHz Spectrum                    5 GHz Spectrum
    ┌─────┬─────┬─────┬─────┐          ┌─────────────────────┐
    │ Ch1 │     │     │Ch11 │          │      Channel 40     │
    │     │     │     │     │          │                     │
    │AP3  │     │     │AP1  │          │ AP1, AP2, AP3       │
    │(6b) │     │     │(9f) │          │ ALL on same channel │
    │     │     │     │AP2  │          │                     │
    │     │     │     │(3d) │          │ ⚠ Co-channel        │
    │     │     │     │AP4  │          │   interference      │
    │     │     │     │(fd) │          │   likely             │
    └─────┴─────┴─────┴─────┘          └─────────────────────┘
```

**Channel issue:** All three primary APs use the same 5 GHz channel (40). This causes co-channel interference and reduces throughput when clients are in overlapping coverage areas.

## Saved Wi-Fi Profiles

| Profile | Notes |
|---------|-------|
| Adami_Guest | Current — auto-connect enabled |
| montresor | Unknown network — possibly another company location, a home network, or a different building |

## Wi-Fi Security Assessment

| Check | Status | Notes |
|-------|--------|-------|
| Encryption | WPA3-Personal / CCMP | Strong — current best practice |
| H2E Support | **Not supported** | Dragonfly handshake lacks Hash-to-Element, vulnerable to side-channel |
| Enterprise Auth (802.1X) | **No** — PSK only | Shared password = if one device is compromised, all are |
| Client Isolation | Possibly enabled | Sparse ARP table suggests AP-level isolation |
| Hidden SSID | **Only Adami_Guest visible** | Corporate SSID likely exists but hidden/on different VLAN |
| Management Frame Protection | Unknown | WPA3 requires PMF but cannot verify from client side |
| QoS/MSCS | Not configured | No traffic prioritization |
