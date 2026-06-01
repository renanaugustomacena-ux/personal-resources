# 15 — Attack Surface Map

## Full Attack Surface Diagram

```
═══════════════════════════════════════════════════════════════════
                    PCFRANCESCA — ATTACK SURFACE MAP
                    192.168.192.61 (Adami_Guest Wi-Fi)
═══════════════════════════════════════════════════════════════════

                         ┌──────────────────────┐
                         │    PHYSICAL LAYER     │
                         │                      │
                         │  ● Wi-Fi radio (5GHz)│
                         │  ● Ethernet (disconn)│
                         │  ● Bluetooth          │
                         │  ● USB ports          │
                         │  ● No BitLocker       │
                         │                      │
                         │  Risk: Physical theft │
                         │  = full data access   │
                         └──────────┬───────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              │                     │                     │
    ┌─────────┴──────────┐ ┌───────┴────────┐  ┌─────────┴──────────┐
    │  INBOUND SURFACE   │ │ LOCAL SURFACE  │  │  OUTBOUND SURFACE  │
    │  (from network)    │ │ (on-machine)   │  │  (to internet)     │
    └─────────┬──────────┘ └───────┬────────┘  └─────────┬──────────┘
              │                    │                      │
    ┌─────────┴──────────┐        │           ┌──────────┴─────────┐
    │                    │        │           │                    │
    │ TCP LISTENERS:     │        │           │ OUTBOUND:          │
    │                    │        │           │                    │
    │ :135  RPC Mapper   │        │           │ → Avast Cloud      │
    │ :139  NetBIOS      │        │           │   (7500, 443)      │
    │ :445  SMB ★★★      │        │           │                    │
    │ :2000 WUDFHost     │        │           │ → AnyDesk Relay    │
    │ :5040 svchost      │        │           │   (443)            │
    │ :7070 AnyDesk ★★   │        │           │                    │
    │ :7680 Delivery Opt │        │           │ → Microsoft Cloud  │
    │ :49664 LSASS ★★    │        │           │   (OneDrive, Teams)│
    │ :49665 wininit     │        │           │                    │
    │ :49666-68 RPC svcs │        │           │ → ISP DNS          │
    │ :55204 services    │        │           │   (unencrypted)    │
    │                    │        │           │                    │
    │ UDP LISTENERS:     │        │           │ → Windows telemetry│
    │                    │        │           │                    │
    │ :123  NTP          │        │           │ No egress filtering│
    │ :137  NBT-NS ★★    │        │           │ No proxy           │
    │ :138  NBT-DG       │        │           │ All outbound allowed│
    │ :500  IKE/IPSec    │        │           │                    │
    │ :1900 SSDP/UPnP   │        │           └────────────────────┘
    │ :4500 NAT-T        │        │
    │ :5050 svchost      │        │
    │ :5353 mDNS ★       │  ┌─────┴──────────────────┐
    │ :5355 LLMNR ★★     │  │                        │
    │ :50001 AnyDesk     │  │ LOCAL ATTACK SURFACE:  │
    │                    │  │                        │
    └────────────────────┘  │ ● No password (admin)  │
                            │ ● ASPNET acct enabled  │
                            │ ● PS Bypass policy     │
                            │ ● Avast TLS MITM       │
                            │ ● Avast email proxy    │
                            │ ● Admin shares (C$)    │
                            │ ● Users share (Everyone)│
                            │ ● SMBv1 enabled        │
                            │ ● No SMB signing       │
                            │ ● No disk encryption   │
                            │ ● WHEA hw errors       │
                            │ ● Intel ME active      │
                            │ ● Stale root CAs       │
                            │                        │
                            └────────────────────────┘

★★★ = Critical      ★★ = High      ★ = Medium
```

## Attack Chains

### Chain 1: Network → Full Compromise (No Authentication Required)

```
ATTACKER ON GUEST WI-FI
         │
         ▼
    ┌────────────┐
    │ Port Scan  │  Discover SMB (445) + AnyDesk (7070)
    │ .192.61    │
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ SMB Auth   │  Try sandro / (empty password)
    │ Attempt    │  → SUCCESS (no password!)
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ PsExec or  │  Execute commands as SYSTEM
    │ WMI Exec   │  via admin share (C$, ADMIN$)
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ FULL       │  Access all data, install backdoor,
    │ COMPROMISE │  pivot to main LAN via port 7680
    └────────────┘

    TOTAL TIME: < 60 seconds
    TOOLS NEEDED: Metasploit / Impacket / manual SMB
    SKILL LEVEL: Script kiddie
```

### Chain 2: LLMNR Poisoning → Credential Capture

```
ATTACKER ON GUEST WI-FI
         │
         ▼
    ┌────────────┐
    │ Run        │  Listen for LLMNR/NBT-NS broadcasts
    │ Responder  │
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ Victim     │  User tries to access \\fileserver
    │ queries    │  DNS fails → LLMNR broadcast
    │ a name     │
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ Poison     │  Attacker responds "I am fileserver"
    │ response   │  Victim sends NTLM auth
    └────┬───────┘
         │
         ├──► Crack NTLMv2 hash offline (no password = instant)
         │
         └──► Relay auth to another host (no SMB signing)
              → Authenticated access on target
```

### Chain 3: AnyDesk Exploitation

```
ATTACKER (REMOTE/INTERNET)
         │
         ▼
    ┌────────────┐
    │ AnyDesk    │  Relay is always connected
    │ relay      │  If unattended password is weak/known
    │ access     │  → interactive desktop session
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ Desktop    │  As sandro (admin, no password)
    │ control    │  Full GUI access to everything
    └────────────┘
```

### Chain 4: Physical Access

```
PHYSICAL ACCESS TO LAPTOP
         │
         ▼
    ┌────────────┐
    │ No BitLocker│  Boot from USB → access disk
    │ No BIOS pwd │  Or: just login (no password!)
    └────┬───────┘
         │
         ▼
    ┌────────────┐
    │ Extract:   │  SAM database (local hashes)
    │            │  Browser saved passwords
    │            │  OneDrive cached files
    │            │  Email (Outlook profile)
    │            │  VPN credentials (if any)
    │            │  Wi-Fi passwords
    └────────────┘
```

## Attack Surface Score

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  OVERALL SECURITY POSTURE:  2/10  ██░░░░░░░░                │
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ Network Security:       2/10  ██░░░░░░░░          │     │
│  │ Authentication:         1/10  █░░░░░░░░░          │     │
│  │ Data Protection:        2/10  ██░░░░░░░░          │     │
│  │ Endpoint Protection:    4/10  ████░░░░░░          │     │
│  │ Monitoring/Visibility:  1/10  █░░░░░░░░░          │     │
│  │ Encryption:             2/10  ██░░░░░░░░          │     │
│  │ Access Control:         2/10  ██░░░░░░░░          │     │
│  │ Patch Management:       5/10  █████░░░░░          │     │
│  └────────────────────────────────────────────────────┘     │
│                                                              │
│  The primary concern is that MULTIPLE critical findings     │
│  chain together to create trivially exploitable paths.       │
│  No single finding in isolation would be as dangerous as     │
│  the combination of: no password + SMBv1 + exposed shares   │
│  + no signing + broadcast poisoning + no segmentation.       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

## What An Attacker Sees

```
nmap -sV 192.168.192.61

PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds  Windows 11 Pro (SMBv1 enabled!)
2000/tcp  open  cisco-sccp?   
5040/tcp  open  unknown
7070/tcp  open  anydesk       AnyDesk remote desktop
7680/tcp  open  pando-pub?    Windows Delivery Optimization
49664/tcp open  msrpc         LSASS
...

enum4linux 192.168.192.61
  [+] Server allows NULL sessions
  [+] Username: sandro (RID 1003) - Admin
  [+] Share: Users (Everyone:Full)
  [+] Share: C$ (Admins only)
  [+] Share: ADMIN$ (Admins only)

smbclient //192.168.192.61/Users -U sandro -N
  smb: \> ls
  sandro\         ← Full access to all user data
```
