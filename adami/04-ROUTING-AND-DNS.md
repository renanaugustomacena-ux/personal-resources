# 04 — Routing & DNS Configuration

## IPv4 Routing Table

```
┌────────────────────────────────────────────────────────────────┐
│                     IPv4 ROUTING TABLE                          │
├───────────────────┬───────────────┬──────────┬────────────────┤
│ Destination       │ Next Hop      │ Metric   │ Interface      │
├───────────────────┼───────────────┼──────────┼────────────────┤
│ 0.0.0.0/0         │ 192.168.192.1 │ 35       │ Wi-Fi          │
│ (default route)   │               │          │                │
├───────────────────┼───────────────┼──────────┼────────────────┤
│ 127.0.0.0/8       │ On-link       │ 331      │ Loopback       │
├───────────────────┼───────────────┼──────────┼────────────────┤
│ 192.168.192.0/24  │ On-link       │ 291      │ Wi-Fi          │
│ (local subnet)    │               │          │                │
├───────────────────┼───────────────┼──────────┼────────────────┤
│ 192.168.192.61/32 │ On-link       │ 291      │ Wi-Fi          │
│ (local host)      │               │          │                │
├───────────────────┼───────────────┼──────────┼────────────────┤
│ 224.0.0.0/4       │ On-link       │ 291/331  │ Wi-Fi/Loopback │
│ (multicast)       │               │          │                │
└───────────────────┴───────────────┴──────────┴────────────────┘
```

**Key observations:**
- Only one default route exists → all non-local traffic goes through 192.168.192.1
- No static routes to other subnets (192.168.1.x or 192.168.60.x)
- No VPN tunnel routes
- Route metric of 35 for Wi-Fi is standard

## DNS Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   DNS RESOLUTION FLOW                        │
│                                                             │
│  ┌──────────────┐                                          │
│  │  Application │                                          │
│  │  (browser,   │                                          │
│  │   etc.)      │                                          │
│  └──────┬───────┘                                          │
│         │ 1. Query                                         │
│         ▼                                                  │
│  ┌──────────────┐     ┌─────────────────────────────┐     │
│  │  Local DNS   │ 2.  │  Broadcast Resolution       │     │
│  │  Client      ├────►│  (PARALLEL - INSECURE)      │     │
│  │  Cache       │     │                             │     │
│  │  (Dnscache)  │     │  ┌──────┐  ┌──────┐  ┌───┐│     │
│  └──────┬───────┘     │  │LLMNR │  │NBT-NS│  │mDNS││     │
│         │             │  │:5355 │  │:137  │  │:5353││     │
│         │             │  │  ✓   │  │  ✓   │  │ ✓  ││     │
│         │ 3. Cache    │  └──────┘  └──────┘  └───┘│     │
│         │    miss     │  ALL ENABLED = POISONABLE   │     │
│         ▼             └─────────────────────────────┘     │
│  ┌──────────────┐                                          │
│  │  ISP DNS     │  ◄── NOT internal DNS!                  │
│  │              │                                          │
│  │  Primary:    │                                          │
│  │  80.93.143.42│  dnsunico.welcomeitalia.it              │
│  │              │                                          │
│  │  Secondary:  │                                          │
│  │  80.93.143.44│  Welcome Italia ISP                     │
│  └──────────────┘                                          │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │  DORMANT CONFIG (Ethernet - disconnected)        │      │
│  │  DNS: 192.168.60.2, 192.168.60.3                │      │
│  │  These would resolve adamitrasporti.local         │      │
│  │  (AD domain) but are UNREACHABLE from guest Wi-Fi│      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## DNS Configuration Per Interface

| Interface | Address Family | DNS Servers |
|-----------|---------------|-------------|
| Wi-Fi | IPv4 | 80.93.143.42, 80.93.143.44 |
| Ethernet | IPv4 | 192.168.60.2, 192.168.60.3 |
| Wi-Fi Direct #3 | IPv6 | fec0:0:0:ffff::1, ::2, ::3 |
| Wi-Fi Direct #4 | IPv6 | fec0:0:0:ffff::1, ::2, ::3 |
| Bluetooth | IPv6 | fec0:0:0:ffff::1, ::2, ::3 |
| Loopback | IPv6 | fec0:0:0:ffff::1, ::2, ::3 |

**Note:** The IPv6 DNS servers use `fec0::/10` (site-local, deprecated since RFC 3879). These are default Windows placeholders and not real DNS servers.

## DNS Cache Snapshot

Recently resolved names at time of assessment:

| Entry | Type | TTL (sec) | Resolved IP | Notes |
|-------|------|-----------|-------------|-------|
| crs.cr.adobe.com | A | 1564 | 192.147.130.166 | Adobe telemetry |
| raw.githubusercontent.com | A | 1769 | 185.199.108-111.133 | GitHub CDN (4 IPs) |
| bconsole-avm-prod-prg.ff.avast.com | A | 35 | 34.140.178.115 | Avast Business Console |
| relay-83fd48c2.net.anydesk.com | A | 5618 | 162.19.204.173 | AnyDesk relay server |

## DNS Security Assessment

| Check | Status | Risk |
|-------|--------|------|
| Using internal DNS | **NO** — ISP DNS | Cannot resolve internal resources |
| DNS over HTTPS (DoH) | Not configured | Queries visible to ISP |
| DNS over TLS (DoT) | Not configured | Queries visible on network |
| DNSSEC validation | Not configured | No protection against spoofing |
| LLMNR (local fallback) | **ENABLED** | Poisoning via Responder |
| NetBIOS Name Service | **ENABLED** | Poisoning via Responder |
| mDNS | **ENABLED** | Local name spoofing |
| WPAD (auto-proxy) | Not explicitly configured | Default Windows behavior |

## DNS Suffix Search List

The DHCP server pushes `adamitrasporti.local` as the DNS suffix. This means:
- Short name lookups (e.g., `nslookup server1`) append `.adamitrasporti.local`
- But the ISP DNS (80.93.143.42) **cannot resolve** `*.adamitrasporti.local`
- This creates a **name resolution black hole** for all internal hostnames
