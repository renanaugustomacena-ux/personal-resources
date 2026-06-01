# 07 — Listening Services (Attack Surface)

## TCP Listening Ports

### Network-Exposed (bound to 0.0.0.0 or specific IP)

These ports are accessible from the network:

```
┌────────────────────────────────────────────────────────────────┐
│              NETWORK-EXPOSED TCP SERVICES                       │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Port 135 │  │ Port 139 │  │ Port 445 │  │ Port 7070│     │
│  │ RPC      │  │ NetBIOS  │  │ SMB      │  │ AnyDesk  │     │
│  │ Endpoint │  │ Session  │  │          │  │          │     │
│  │ Mapper   │  │ Service  │  │          │  │          │     │
│  │          │  │          │  │          │  │          │     │
│  │ svchost  │  │ System   │  │ System   │  │ AnyDesk  │     │
│  │ PID 1440 │  │ PID 4    │  │ PID 4    │  │ PID 8216 │     │
│  │          │  │          │  │          │  │          │     │
│  │ Risk: MED│  │ Risk:HIGH│  │ Risk:CRIT│  │ Risk:HIGH│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ Port 2000│  │ Port 5040│  │ Port 7680│  │ Port     │     │
│  │ WUDFHost │  │ svchost  │  │ Delivery │  │ 49664-68 │     │
│  │          │  │          │  │ Optimiz. │  │ Dynamic  │     │
│  │ Driver   │  │ Windows  │  │          │  │ RPC      │     │
│  │ Framework│  │ service  │  │ svchost  │  │          │     │
│  │ PID 1336 │  │ PID 7356 │  │ PID 3500 │  │ Various  │     │
│  │          │  │          │  │          │  │          │     │
│  │ Risk: LOW│  │ Risk: LOW│  │ Risk: MED│  │ Risk: MED│     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                │
│  ┌──────────┐  ┌──────────┐                                   │
│  │ Port     │  │ Port     │                                   │
│  │ 55204    │  │ 49664    │                                   │
│  │ services │  │ lsass    │                                   │
│  │ .exe     │  │          │                                   │
│  │ SCM      │  │ Auth svc │                                   │
│  │ PID 1108 │  │ PID 1124 │                                   │
│  │          │  │          │                                   │
│  │ Risk: MED│  │ Risk:HIGH│                                   │
│  └──────────┘  └──────────┘                                   │
└────────────────────────────────────────────────────────────────┘
```

### Localhost-Only (bound to 127.0.0.1 / ::1)

These ports are only accessible locally:

| Port | Process | PID | Purpose |
|------|---------|-----|---------|
| 10107 | bcc (Avast Business Console Client) | 8368 | Local management |
| 12025 | AvastSvc | 4740 | SMTP proxy (intercepting port 25) |
| 12110 | AvastSvc | 4740 | POP3 proxy (intercepting port 110) |
| 12119 | AvastSvc | 4740 | NNTP proxy (intercepting port 119) |
| 12143 | AvastSvc | 4740 | IMAP proxy (intercepting port 143) |
| 12465 | AvastSvc | 4740 | SMTPS proxy (intercepting port 465) |
| 12563 | AvastSvc | 4740 | NNTPS proxy (intercepting port 563) |
| 12993 | AvastSvc | 4740 | IMAPS proxy (intercepting port 993) |
| 12995 | AvastSvc | 4740 | POP3S proxy (intercepting port 995) |
| 14108 | agentsvc (Avast Business Agent) | 8428 | Agent communication |
| 19293 | AdobeCollabSync | 15916 | Adobe collaboration |
| 27275 | AvastSvc | 4740 | Internal Avast communication |
| 42050 | OneDrive.Sync.Service | 15696 | OneDrive sync |
| 49672 | jhi_service (Intel ME) | 8640 | Intel Management Engine |

### Avast Email Interception Map

```
┌─────────────────────────────────────────────────────────┐
│             AVAST EMAIL PROXY ARCHITECTURE                │
│                                                          │
│  Email Client                    Remote Mail Server      │
│  ┌──────┐                        ┌──────────────┐       │
│  │Outlook│ ──── localhost:12143 ──► Avast scans  │       │
│  │      │ ◄─── (IMAP proxy)  ◄── mail content   │       │
│  │      │                        │              │       │
│  │      │ ──── localhost:12025 ──► then forwards │       │
│  │      │ ◄─── (SMTP proxy)  ◄── to/from real   │       │
│  └──────┘                        │ mail server  │       │
│                                  └──────────────┘       │
│                                                          │
│  Intercepted Protocols:                                  │
│  ├── SMTP    (25)  → localhost:12025                    │
│  ├── POP3    (110) → localhost:12110                    │
│  ├── NNTP    (119) → localhost:12119                    │
│  ├── IMAP    (143) → localhost:12143                    │
│  ├── SMTPS   (465) → localhost:12465                    │
│  ├── NNTPS   (563) → localhost:12563                    │
│  ├── IMAPS   (993) → localhost:12993                    │
│  └── POP3S   (995) → localhost:12995                    │
└─────────────────────────────────────────────────────────┘
```

## UDP Endpoints

| Port | Address | Process | PID | Purpose |
|------|---------|---------|-----|---------|
| 123 | 0.0.0.0 / :: | svchost (W32Time) | 13652 | NTP time sync |
| 137 | 192.168.192.61 | System | 4 | NetBIOS Name Service |
| 138 | 192.168.192.61 | System | 4 | NetBIOS Datagram |
| 500 | 0.0.0.0 / :: | svchost (IKEEXT) | 8268 | IKE (IPSec VPN) |
| 1900 | Multiple | svchost (SSDP) | 16316 | UPnP/SSDP discovery |
| 4500 | 0.0.0.0 / :: | svchost (IKEEXT) | 8268 | NAT-T IPSec |
| 5050 | 0.0.0.0 | svchost | 7356 | Windows service |
| 5353 | 0.0.0.0 / :: | svchost (Dnscache) | 2124 | mDNS |
| 5355 | 0.0.0.0 / :: | svchost (Dnscache) | 2124 | LLMNR |
| 50001 | 0.0.0.0 | AnyDesk | 8216 | AnyDesk UDP |
| 50070 | :: | ms-teams | 14692 | Teams media |

## Connection State Summary

| State | Count | Notes |
|-------|-------|-------|
| Listen | 44 | Active listening sockets |
| TimeWait | 37 | Recently closed (mostly DO peers) |
| Bound | 22 | Bound but not listening |
| Established | 15 | Active connections |
| CloseWait | 6 | Waiting for local close |

## Total Attack Surface Summary

```
NETWORK-EXPOSED ATTACK SURFACE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TCP ports reachable from network:  12+
UDP ports reachable from network:  11
Critical services exposed:         SMB, NetBIOS, AnyDesk, RPC, LSASS
```
