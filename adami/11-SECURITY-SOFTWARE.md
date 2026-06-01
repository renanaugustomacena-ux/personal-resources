# 11 — Security Software & Certificates

## Security Software Stack

```
┌──────────────────────────────────────────────────────────────┐
│                  SECURITY SOFTWARE STACK                       │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  AVAST BUSINESS (Primary AV)                       │     │
│  │                                                    │     │
│  │  ┌──────────────┐  ┌──────────────────────────┐   │     │
│  │  │ AvastSvc     │  │ Avast Business Agent     │   │     │
│  │  │ PID 4740     │  │ (ClientManager)          │   │     │
│  │  │              │  │                          │   │     │
│  │  │ - AV Engine  │  │ - Managed deployment     │   │     │
│  │  │ - Email proxy│  │ - Central console        │   │     │
│  │  │ - Web shield │  │ - Policy enforcement     │   │     │
│  │  │ - TLS MITM   │  │                          │   │     │
│  │  └──────────────┘  └──────────────────────────┘   │     │
│  │                                                    │     │
│  │  ┌──────────────┐  ┌──────────────────────────┐   │     │
│  │  │ aswbIDSAgent │  │ Avast Firewall Service   │   │     │
│  │  │              │  │                          │   │     │
│  │  │ - IDS/IPS    │  │ - Network firewall       │   │     │
│  │  │ - Behavioral │  │ - Alongside Windows FW   │   │     │
│  │  │   detection  │  │                          │   │     │
│  │  └──────────────┘  └──────────────────────────┘   │     │
│  │                                                    │     │
│  │  ┌──────────────┐  ┌──────────────────────────┐   │     │
│  │  │ bcc          │  │ agentsvc                 │   │     │
│  │  │ PID 8368     │  │ PID 8428                 │   │     │
│  │  │ Port 10107   │  │ Port 14108               │   │     │
│  │  │              │  │                          │   │     │
│  │  │ Business     │  │ Agent service            │   │     │
│  │  │ Console      │  │ → 34.74.148.245:7500    │   │     │
│  │  │ Client       │  │                          │   │     │
│  │  └──────────────┘  └──────────────────────────┘   │     │
│  │                                                    │     │
│  │  Services: 8 Avast-related services running       │     │
│  │  Install: C:\Program Files\Avast Software\        │     │
│  │           + C:\Program Files\Avast Software\      │     │
│  │             Business Agent\                        │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  WINDOWS DEFENDER (Disabled)                       │     │
│  │                                                    │     │
│  │  AntivirusEnabled:          FALSE                 │     │
│  │  AntispywareEnabled:        FALSE                 │     │
│  │  RealTimeProtectionEnabled: FALSE                 │     │
│  │  BehaviorMonitorEnabled:    FALSE                 │     │
│  │  IoavProtectionEnabled:     FALSE                 │     │
│  │  NISEnabled:                FALSE                 │     │
│  │  AMServiceEnabled:          FALSE                 │     │
│  │  SignatureAge:              65535 (never updated)  │     │
│  │  QuickScanAge:             4294967295 (never run) │     │
│  │                                                    │     │
│  │  ⚠ ALL features disabled (Avast takes over)      │     │
│  │  ⚠ No fallback if Avast fails or is disabled     │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │  BITLOCKER                                         │     │
│  │                                                    │     │
│  │  Status: NOT CONFIGURED / NOT AVAILABLE            │     │
│  │                                                    │     │
│  │  ⚠ Disk is NOT encrypted                          │     │
│  │  Physical theft = full data access                 │     │
│  └────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

## Avast TLS Interception

```
┌──────────────────────────────────────────────────────────────┐
│              AVAST TLS/SSL INTERCEPTION                        │
│                                                              │
│    Browser/App                    Remote Server              │
│    ┌──────┐                       ┌──────────┐              │
│    │      │ ── TLS ──► ┌──────┐  │          │              │
│    │      │            │ AVAST│  │          │              │
│    │      │            │      │  │          │              │
│    │      │            │ Root │  │          │              │
│    │      │            │  CA  │──►│  HTTPS  │              │
│    │      │ ◄── TLS ── │      │  │  Server │              │
│    │      │  (re-signed│      │◄──│         │              │
│    │      │   with     └──────┘  │          │              │
│    │      │   Avast CA)          │          │              │
│    └──────┘                       └──────────┘              │
│                                                              │
│  Root CA Installed:                                          │
│  ┌────────────────────────────────────────────────┐         │
│  │ CN=Avast Web/Mail Shield Root                  │         │
│  │ O=Avast Web/Mail Shield                        │         │
│  │ OU=generated by Avast Antivirus for            │         │
│  │    SSL/TLS scanning                            │         │
│  │                                                │         │
│  │ Location: Cert:\LocalMachine\Root              │         │
│  │ Trusted: YES (machine-wide)                    │         │
│  └────────────────────────────────────────────────┘         │
│                                                              │
│  Impact:                                                     │
│  - ALL HTTPS traffic decrypted and re-encrypted             │
│  - ALL email (IMAPS, POP3S, SMTPS) intercepted             │
│  - Certificate pinning bypassed                             │
│  - Avast can read ALL encrypted content                     │
│  - If Avast CA key is compromised → full MITM              │
│  - Breaks client certificate authentication                 │
└──────────────────────────────────────────────────────────────┘
```

## Root Certificate Store Audit

### Non-Standard Certificates

| Certificate | Concern Level |
|-------------|---------------|
| **Avast Web/Mail Shield Root** | **HIGH** — TLS interception CA |
| WoSign CA (CN) | **MEDIUM** — Distrusted by browsers since 2016 |
| StartCom CA (IL) | **MEDIUM** — Distrusted by browsers since 2016 |
| DST Root CA X3 | LOW — Expired Let's Encrypt cross-sign (legacy) |
| Hotspot 2.0 Trust Root CA - 03 | LOW — Passpoint/Wi-Fi authentication |

### Distrusted CAs Still Present

The store contains root CAs that major browsers have distrusted:

```
⚠ WoSign (CN=Certification Authority of WoSign)
  - Distrusted by Chrome, Firefox, Apple since 2016
  - Caught issuing unauthorized certificates
  - Should be REMOVED from the trust store

⚠ StartCom (CN=StartCom Certification Authority)
  - Same company as WoSign (discovered in 2016)
  - Distrusted by all major browsers
  - Should be REMOVED from the trust store
```

## Avast Service Inventory

| Service Name | Display Name | Start Type |
|-------------|-------------|------------|
| avast! Antivirus | Avast Antivirus | Automatic |
| avast! Firewall | Avast Firewall Service | Automatic |
| avast! Tools | Avast Tools | Automatic |
| aswbIDSAgent | aswbIDSAgent (IDS) | Manual |
| aswBcc | Avast Business Console Client | Automatic |
| ClientManager | Avast Business Agent | Automatic |
| AvastWscReporter | AvastWscReporter | Automatic |
| Avast Business Console Client AV | Avast Business Console Client AV Service | Automatic |

## PowerShell Execution Policy

| Scope | Policy |
|-------|--------|
| MachinePolicy | Undefined |
| UserPolicy | Undefined |
| Process | **Bypass** (current session) |
| CurrentUser | Undefined |
| LocalMachine | Undefined |

No execution policy restrictions at any level. Any PowerShell script can run without prompting.
