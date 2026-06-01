# 13 — Installed Software Inventory

## Third-Party Software (Non-Microsoft)

| Software | Vendor | Category | Security Notes |
|----------|--------|----------|----------------|
| Avast Business Antivirus | Avast | Security | Primary AV — TLS interception active |
| Avast Business Agent | Avast | Security | Managed deployment client |
| AnyDesk | AnyDesk Software | Remote Access | **Auto-start, always-on relay** |
| Adobe Acrobat (64-bit) | Adobe | Document | PDF reader/editor |
| Adobe Refresh Manager | Adobe | Update | Auto-updater |
| Python 3.12.10 (64-bit) | Python Software Foundation | Development | Full dev environment installed |
| OpenOffice 4.1.11 | Apache | Productivity | Alternative office suite |
| PDFCreator | pdfforge GmbH | Document | PDF printer driver |
| PDF Architect 8 + 9 | pdfforge / Avanquest | Document | PDF editor (2 versions) |
| PDF-XChange (TrackerUpdate) | Tracker Software | Document | PDF tools |
| ZebraDesigner 3 | Zebra Technologies | Printing | **Label printer software** (logistics) |
| Sga Setup 4.0 | SimaSoftware | Business | **Italian business/transport software** |
| SAP Crystal Reports Runtime | SAP | Reporting | Business reporting engine (.NET) |
| HP Support Assistant | HP | System | OEM diagnostics |
| HP PC Hardware Diagnostics UEFI | HP | System | Hardware testing |
| Intel ME Components | Intel | System | Management Engine (×2 entries) |
| Intel Chipset Device Software | Intel | System | Chipset drivers |
| Intel RST Middleware | Intel | Storage | Rapid Storage Technology |
| Intel Dynamic Tuning | Intel | Performance | Thermal/power management |
| Intel Graphics Command Center | Intel | Display | GPU management |
| FortMedia APO | FortMedia | Audio | Audio processing |
| Realtek Audio Universal Service | Realtek | Audio | Audio driver service |
| Sound Research SECOMN | Sound Research | Audio | Audio enhancement |
| XTU3SERVICE | Intel | Performance | Extreme Tuning Utility |

## Business-Specific Software

```
┌──────────────────────────────────────────────────────┐
│         ADAMI TRASPORTI — BUSINESS SOFTWARE           │
│                                                      │
│  ┌─────────────────────────────────────┐            │
│  │  ZebraDesigner 3                    │            │
│  │  Vendor: Zebra Technologies         │            │
│  │                                     │            │
│  │  Purpose: Design and print barcode  │            │
│  │  labels for shipping/logistics      │            │
│  │                                     │            │
│  │  Implies: Zebra label printers      │            │
│  │  connected to network or USB        │            │
│  └─────────────────────────────────────┘            │
│                                                      │
│  ┌─────────────────────────────────────┐            │
│  │  Sga Setup 4.0                      │            │
│  │  Vendor: SimaSoftware               │            │
│  │                                     │            │
│  │  Purpose: Italian transport/         │            │
│  │  logistics management software      │            │
│  │                                     │            │
│  │  Likely connects to internal DB     │            │
│  │  or server (unreachable from guest) │            │
│  └─────────────────────────────────────┘            │
│                                                      │
│  ┌─────────────────────────────────────┐            │
│  │  SAP Crystal Reports Runtime        │            │
│  │  Vendor: SAP                        │            │
│  │                                     │            │
│  │  Purpose: Business report generation│            │
│  │  (.NET 32-bit runtime)              │            │
│  │                                     │            │
│  │  Used by: Sga or other business app │            │
│  └─────────────────────────────────────┘            │
└──────────────────────────────────────────────────────┘
```

## Communication Software

| Software | Type | Firewall Rules |
|----------|------|---------------|
| Microsoft Teams | Chat/Video | Inbound allow (Public) |
| Skype | Chat/Video | Multiple inbound rules |
| WhatsApp | Messaging | Inbound allow |
| OneDrive | File Sync | Active sync to Microsoft cloud |
| Microsoft Outlook | Email | Inbound allow (via Avast proxy) |

## Scheduled Tasks (Non-Microsoft)

| Task | Schedule | Binary | Risk |
|------|----------|--------|------|
| Adobe Acrobat Update Task | Daily 09:00 | Adobe updater | LOW |
| TrackerAutoUpdate | Every 14 days | TrackerUpdate.exe | LOW |
| PDF Architect 9 Update | Periodic | pdfforge updater | LOW |
| PDF Architect 9 Notification | Periodic | pdfforge notification | LOW |
| SoftLandingCreativeManagement | Daily (24h) | TwinUI.dll (COM) | LOW (Windows built-in) |
| OneDrive tasks | Various | OneDrive | LOW |
| HP tasks | Various | HP diagnostics | LOW |

## Software Version Concerns

| Concern | Details |
|---------|---------|
| OpenOffice 4.1.11 | Apache OpenOffice has had limited security updates since 2023. Consider switching to LibreOffice. |
| Multiple PDF tools | PDFCreator + PDF Architect 8 + PDF Architect 9 + PDF-XChange = 4 overlapping PDF tools. Reduces attack surface by removing unused ones. |
| Python 3.12.10 | Development environment on a business workstation. Verify this is needed. |
| Intel ME | Active — hardware-level management interface. Known to have had vulnerabilities (INTEL-SA-00086, etc.) |

## Software Relevant to Network

```
SOFTWARE WITH NETWORK CONNECTIVITY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
├── AnyDesk          → Persistent outbound to relay.anydesk.com
├── Avast Business   → Outbound to Avast cloud (multiple IPs)
├── OneDrive         → Outbound to Microsoft 365
├── Teams            → Outbound to Microsoft, inbound UDP
├── Outlook          → Proxied through Avast (localhost ports)
├── Adobe products   → Outbound to Adobe telemetry
├── Intel ME/JHI     → Local port 49672 (management)
└── Delivery Optim.  → Cross-subnet peering (7680)
```
