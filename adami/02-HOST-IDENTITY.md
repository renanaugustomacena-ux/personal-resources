# 02 — Host Identity & System Profile

## Machine Identity

```
┌─────────────────────────────────────────────────────┐
│                  PCFRANCESCA                         │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  OS: Windows 11 Pro (10.0.26200)           │    │
│  │  Build: 26200                               │    │
│  │  Platform: x64                              │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Hostname:    PCFRANCESCA                   │    │
│  │  Domain:      WORKGROUP (NOT joined)        │    │
│  │  PartOfDomain: FALSE                        │    │
│  │  User:        sandro                        │    │
│  │  User SID:    S-1-5-21-872622826-           │    │
│  │               2128076652-1825121607-1003    │    │
│  │  Privilege:   Local Administrator           │    │
│  └─────────────────────────────────────────────┘    │
│                                                     │
│  ┌─────────────────────────────────────────────┐    │
│  │  Hardware:                                  │    │
│  │  - HP laptop (HP bloatware + diagnostics)   │    │
│  │  - Intel Wi-Fi 6 AX201 160MHz              │    │
│  │  - Realtek PCIe GbE Family Controller       │    │
│  │  - Bluetooth 5.x                           │    │
│  │  - Intel HD Graphics                       │    │
│  │  - Intel ME (Management Engine) active     │    │
│  └─────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
```

## Domain Status

| Property | Value | Security Impact |
|----------|-------|-----------------|
| Domain Membership | **WORKGROUP** | No GPO enforcement, no centralized management |
| PartOfDomain | False | No AD authentication, no Kerberos |
| DNS Suffix | adamitrasporti.local | Pushed via DHCP, not from AD join |
| DNS SRV Records | None resolvable | ISP DNS cannot resolve internal AD records |

**Implication:** This machine operates as a standalone workstation with no Group Policy, no centralized authentication, and no domain-level security controls. All security configuration is local.

## System Health

The system event log is flooded with WHEA (Windows Hardware Error Architecture) events:

```
WHEA-Logger Event ID 17 — Repeated every 5-30 seconds
"Si è verificato un errore hardware" (A hardware error occurred)
```

| Metric | Detail |
|--------|--------|
| Event Frequency | Every 5-30 seconds (continuous) |
| Event Source | Microsoft-Windows-WHEA-Logger |
| Event ID | 17 |
| Impact | Potential system instability, data corruption risk |
| Possible Causes | Failing SSD/RAM, thermal throttling, firmware bug |

## Naming Convention Analysis

The hostname "PCFRANCESCA" suggests this machine was originally assigned to a user named "Francesca" and has been repurposed or shared. The current user is "sandro," indicating either:
- Machine reassignment without rename
- Multiple users sharing the machine
- The original setup was not cleaned up
