# 08 — Outbound Connections

## Active Established Connections (Snapshot)

### Connection Map

```
                          PCFRANCESCA
                         192.168.192.61
                              │
            ┌─────────────────┼─────────────────────┐
            │                 │                     │
      ┌─────┴─────┐    ┌─────┴─────┐    ┌─────────┴──────────┐
      │  Anthropic │    │  Microsoft │    │ Security / Remote  │
      │  (Claude)  │    │  Cloud     │    │                    │
      │            │    │            │    │                    │
      │ 160.79.104 │    │ 13.107.   │    │ Avast:             │
      │ .10:443    │    │ 137.11    │    │ 34.73.71.173:7500  │
      │            │    │           │    │ 34.98.110.65:443   │
      │ 34.149.66  │    │ 52.104.   │    │ 23.202.156.252:443 │
      │ .137:443   │    │ 126.53   │    │ 34.140.178.115     │
      │            │    │           │    │                    │
      │ 35.190.46  │    │ 108.142.  │    │ AnyDesk:           │
      │ .17:443    │    │ 58.42    │    │ 162.19.204.173:443 │
      │            │    │           │    │ (relay-83fd48c2    │
      │ PID: 7184  │    │ 20.189.   │    │  .net.anydesk.com) │
      │  + 16448   │    │ 173.7    │    │                    │
      │            │    │           │    │ PID: 4740, 8428,   │
      └────────────┘    │ 4.207.247 │    │      8216          │
                        │ .138/.139 │    └────────────────────┘
                        │           │
                        │ 52.123.   │
                        │ 242.227  │
                        │           │
                        │ PID: 17352│
                        │ (OneDrive)│
                        │ 15560    │
                        │ (EdgeWV2) │
                        │ 14692    │
                        │ (Teams)  │
                        └───────────┘
```

## Connection Inventory

| Source Port | Remote IP | Remote Port | Process | PID | Purpose |
|-------------|-----------|-------------|---------|-----|---------|
| 49701 | 4.207.247.138 | 443 | svchost | 8516 | Windows telemetry (Azure) |
| 49703 | 34.73.71.173 | 7500 | AvastSvc | 4740 | Avast cloud backend |
| 49725 | 162.19.204.173 | 443 | **AnyDesk** | 8216 | AnyDesk relay server |
| 49825 | 52.123.242.227 | 443 | msedgewebview2 | 15560 | Microsoft Edge services |
| 50485 | 34.98.110.65 | 443 | AvastSvc | 4740 | Avast cloud |
| 50486 | 13.107.137.11 | 443 | OneDrive | 17352 | OneDrive sync (Microsoft) |
| 50487 | 52.104.126.53 | 443 | OneDrive | 17352 | OneDrive API |
| 50494 | 34.149.66.137 | 443 | claude | 7184 | Claude AI (Anthropic/GCP) |
| 50967 | 160.79.104.10 | 443 | claude | 16448 | Claude AI (Anthropic) |
| 50989 | 160.79.104.10 | 443 | claude | 16448 | Claude AI (Anthropic) |
| 50990 | 34.149.66.137 | 443 | claude | 16448 | Claude AI (GCP) |
| 51005 | 160.79.104.10 | 443 | claude | 7184 | Claude AI (Anthropic) |
| 51006 | 160.79.104.10 | 443 | claude | 7184 | Claude AI (Anthropic) |
| 51008 | 160.79.104.10 | 443 | claude | 7184 | Claude AI (Anthropic) |
| 51011 | 35.190.46.17 | 443 | claude | 7184 | Claude AI (GCP LB) |
| 51018 | 20.189.173.7 | 443 | OneDrive | 17352 | Microsoft notification |
| 56162 | 23.202.156.252 | 443 | AvastSvc | 4740 | Avast (Akamai CDN) |
| 58018 | 4.207.247.139 | 443 | OneDrive | 17352 | Microsoft Azure |
| 62097 | 34.74.148.245 | 7500 | agentsvc | 8428 | Avast Business Console |
| 64407 | 20.33.3.2 | 443 | aswToolsSvc | 4128 | Avast Tools service |
| 64657 | 108.142.58.42 | 443 | msedgewebview2 | 15560 | Microsoft services |
| 65482 | 108.142.58.42 | 443 | ms-teams | 14692 | Microsoft Teams |

## Outbound Traffic Categories

```
┌─────────────────────────────────────────────────────────┐
│         OUTBOUND TRAFFIC BREAKDOWN BY CATEGORY            │
│                                                          │
│  Microsoft Cloud (OneDrive, Teams, Edge, Telemetry)      │
│  ████████████████████████████████  8 connections (36%)   │
│                                                          │
│  Claude / Anthropic (GCP)                                │
│  █████████████████████████████  7 connections (32%)      │
│                                                          │
│  Avast Security                                          │
│  ██████████████████  5 connections (23%)                 │
│                                                          │
│  AnyDesk                                                 │
│  ███  1 connection (4.5%)                                │
│                                                          │
│  Windows Telemetry                                       │
│  ███  1 connection (4.5%)                                │
└─────────────────────────────────────────────────────────┘
```

## Cross-Subnet Traffic (Delivery Optimization)

Windows Delivery Optimization (port 7680) was serving updates to hosts on a different subnet. These connections were in TIME_WAIT state (recently completed):

| Remote Host | Subnet | Status |
|-------------|--------|--------|
| 192.168.1.56 | Main LAN | 3 connections |
| 192.168.1.58 | Main LAN | 6 connections |
| 192.168.1.75 | Main LAN | 3 connections |
| 192.168.1.76 | Main LAN | 3 connections |
| 192.168.1.77 | Main LAN | 4 connections |
| 192.168.1.79 | Main LAN | 6 connections |
| 192.168.1.81 | Main LAN | 6 connections |
| 192.168.1.103 | Main LAN | 3 connections |
| 192.168.1.144 | Main LAN | 3 connections |
| 192.168.1.147 | Main LAN | 3 connections |
| 192.168.1.155 | Main LAN | 5 connections |
| 192.168.1.162 | Main LAN | 3 connections |
| 192.168.1.193 | Main LAN | 2 connections |

**Total: 50+ recent connections to 13 unique hosts on 192.168.1.0/24**

This confirms the guest network has bidirectional TCP connectivity to the main LAN on specific ports.

## Protocols In Use

| Protocol | Port | Encrypted | Notes |
|----------|------|-----------|-------|
| HTTPS | 443 | TLS (Avast MITM) | All major services |
| Custom | 7500 | Unknown | Avast cloud protocol |
| HTTPS | 443 | TLS | AnyDesk relay |
| DO | 7680 | Partial | Windows Update peering |

## Egress Security Concerns

1. **No egress filtering** — any process can reach any external IP on any port
2. **AnyDesk maintains persistent relay** — always connected to OVH-hosted relay server in EU
3. **Avast Business Console** uses port 7500 (non-standard) — could bypass port-based filtering
4. **All HTTPS traffic is MITM'd by Avast** — Avast sees all encrypted web/email content
5. **No proxy server** — direct internet access without content filtering
