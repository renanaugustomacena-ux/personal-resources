# 10 — Broadcast Name Resolution Protocols

## Overview

Broadcast name resolution protocols are mechanisms Windows uses when standard DNS fails. They broadcast queries on the local network, and **any host can respond** — making them prime targets for man-in-the-middle attacks.

## Protocol Status

```
┌──────────────────────────────────────────────────────────┐
│          BROADCAST PROTOCOL ATTACK SURFACE                │
│                                                          │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   LLMNR    │  │  NetBIOS   │  │    mDNS    │        │
│  │            │  │  Name Svc  │  │            │        │
│  │ UDP 5355   │  │  UDP 137   │  │  UDP 5353  │        │
│  │            │  │            │  │            │        │
│  │ STATUS:    │  │ STATUS:    │  │ STATUS:    │        │
│  │ ██ ENABLED │  │ ██ ENABLED │  │ ██ ENABLED │        │
│  │            │  │            │  │            │        │
│  │ GPO:       │  │ Node Type: │  │ Registry:  │        │
│  │ NOT SET    │  │ Hybrid     │  │ EnableMDNS │        │
│  │ (=enabled) │  │ (P+B node) │  │ not set    │        │
│  │            │  │            │  │ (=enabled) │        │
│  │ FW Rule:   │  │ LMHOSTS:   │  │            │        │
│  │ Inbound ✓  │  │ Enabled    │  │            │        │
│  │ (Public)   │  │            │  │            │        │
│  └────────────┘  └────────────┘  └────────────┘        │
│                                                          │
│  ALL THREE PROTOCOLS = POISONABLE                       │
│  Combined with no SMB signing = full relay capability    │
└──────────────────────────────────────────────────────────┘
```

## Resolution Order (Windows Name Resolution)

```
┌──────────────────────────────────────────────────────────┐
│            WINDOWS NAME RESOLUTION ORDER                  │
│                                                          │
│  1. Local hosts file          C:\Windows\...\hosts       │
│     └── Status: DEFAULT (no custom entries)              │
│                                                          │
│  2. DNS query                 → 80.93.143.42 (ISP)      │
│     └── Cannot resolve *.adamitrasporti.local            │
│                                                          │
│  3. LLMNR multicast           → 224.0.0.252 (UDP 5355)  │
│     └── ⚠ ANY host on subnet can respond                │
│                                                          │
│  4. NetBIOS Name Service      → broadcast (UDP 137)     │
│     └── ⚠ ANY host on subnet can respond                │
│                                                          │
│  5. mDNS multicast            → 224.0.0.251 (UDP 5353)  │
│     └── ⚠ ANY host on subnet can respond                │
│                                                          │
│  Because DNS CANNOT resolve internal names               │
│  (ISP DNS doesn't know adamitrasporti.local),           │
│  Windows ALWAYS falls through to LLMNR/NetBIOS           │
│  for any internal hostname lookup.                        │
│                                                          │
│  This makes poisoning attacks HIGHLY EFFECTIVE.           │
└──────────────────────────────────────────────────────────┘
```

## Attack Scenario: Responder

```
    ATTACK FLOW: LLMNR/NBT-NS Poisoning + SMB Relay

    ┌──────────┐                    ┌──────────┐
    │ VICTIM   │                    │ ATTACKER │
    │ (this PC)│                    │ (on same │
    │          │                    │  subnet) │
    └────┬─────┘                    └────┬─────┘
         │                               │
         │ 1. User types \\server1       │
         │    DNS fails (ISP DNS)        │
         │                               │
         │ 2. LLMNR broadcast:           │
         │    "Who is server1?"          │
         ├──────────────────────────────►│
         │                               │
         │ 3. Attacker responds:         │
         │    "I am server1!"            │
         │◄──────────────────────────────┤
         │                               │
         │ 4. Victim sends NTLM auth    │
         │    to attacker's SMB server   │
         ├──────────────────────────────►│
         │                               │
         │                    5. Attacker│
         │                    captures   │
         │                    NTLMv2 hash│
         │                    OR relays  │
         │                    to real    │
         │                    server     │
         │                               │
    Result: Credential theft or          │
    authenticated access to other hosts  │
```

## NetBIOS Configuration Detail

| Parameter | Value | Meaning |
|-----------|-------|---------|
| NodeType | Hybrid (H-node) | Uses both point-to-point (P) and broadcast (B) |
| EnableLMHOSTS | 1 (Enabled) | Reads LMHOSTS file for name resolution |
| BcastNameQueryCount | 3 | Sends 3 broadcast queries before timeout |
| BcastQueryTimeout | 750ms | Waits 750ms per query |
| NameServerPort | 137 | Standard NBT-NS port |
| CacheTimeout | 600000ms (10 min) | Caches responses for 10 minutes |
| UseNewSmb | 1 | Uses SMB2+ when possible |

## WPAD (Web Proxy Auto-Discovery)

| Check | Status |
|-------|--------|
| Proxy configured | No (direct access) |
| WinHTTP proxy | Not configured |
| IE/Edge proxy | Not configured |
| WPAD registry key | Not found |

WPAD is not actively configured, but Windows will still attempt WPAD discovery via DNS/DHCP by default, creating another poisoning opportunity.

## Remediation

### Disable LLMNR (via Group Policy or Registry)
```powershell
# Registry method (immediate):
New-Item -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Force
Set-ItemProperty -Path "HKLM:\SOFTWARE\Policies\Microsoft\Windows NT\DNSClient" -Name "EnableMulticast" -Value 0 -Type DWord
```

### Disable NetBIOS over TCP/IP
```powershell
# Per-adapter via WMI:
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration -Filter "IPEnabled=True"
$adapters | ForEach-Object { $_.SetTcpipNetbios(2) }  # 2 = Disable
```

### Disable mDNS
```powershell
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters" -Name "EnableMDNS" -Value 0 -Type DWord
```
