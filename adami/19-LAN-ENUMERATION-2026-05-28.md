# 19 — Main LAN Enumeration from Wired Connection

**Assessment Date:** 2026-05-28
**Machine:** renan's Linux workstation (Ubuntu 24.04)
**LAN IP:** 192.168.1.66/24 (DHCP via enp8s0 Ethernet)
**Gateway:** 192.168.1.146 (MAC: 80:61:5F:06:19:CB — same device as guest gateway)
**DNS:** 192.168.60.2 (DC01), 192.168.60.3 (DC02)
**Domain suffix:** adamitrasporti.local
**Method:** Active scanning — nmap, smbclient, LDAP, DNS, curl, FTP

---

## Part 1 — Network Position

Plugging into Ethernet landed us on the **main LAN (192.168.1.0/24)** — the same subnet observed via Delivery Optimization from guest.

| Property | Value |
|----------|-------|
| IP | 192.168.1.66/24 |
| Gateway | 192.168.1.146 (Unbound DNS, same MAC as guest gateway .192.1) |
| DNS | 192.168.60.2 (DC01), 192.168.60.3 (DC02) |
| DNS suffix | adamitrasporti.local |
| DHCP | Yes |

**Critical observation:** Gateway .1.146 has the same MAC (80:61:5F:06:19:CB) as guest gateway .192.1. This confirms a **single device routes ALL VLANs** — likely a pfSense/MikroTik/enterprise firewall.

---

## Part 2 — Active Directory Domain

### Domain Controllers

| Host | IP | Services Open | OS |
|------|---|----|---|
| **DC01** | 192.168.60.2 | DNS(53), Kerberos(88), RPC(135), NetBIOS(139), LDAP(389), SMB(445), Kpasswd(464), LDAPS(636), GC(3268), GCS(3269), RDP(3389), WinRM(5985), ADWS(9389) | Windows Server |
| **DC02** | 192.168.60.3 | Identical to DC01 | Windows Server |

### AD Forest Structure

```
NAMING CONTEXTS (from LDAP rootDSE):
├── DC=adamitrasporti,DC=local          (domain)
├── CN=Configuration,DC=adamitrasporti,DC=local
├── CN=Schema,CN=Configuration,DC=adamitrasporti,DC=local
├── DC=DomainDnsZones,DC=adamitrasporti,DC=local
└── DC=ForestDnsZones,DC=adamitrasporti,DC=local

Single-domain forest. No child domains or trusts detected.
```

### Authentication Security

| Test | Result |
|------|--------|
| LDAP anonymous bind | Rejected — requires auth |
| RPC null session (enumdomusers) | NT_STATUS_ACCESS_DENIED |
| SMB anonymous login | Accepted (no shares listed, SMB1 disabled) |
| DNS zone transfer (AXFR) | Denied |
| RDP | Open on both DCs (3389) |
| WinRM | Open on DC01 (5985) |

DCs are reasonably hardened — anonymous LDAP and RPC blocked. However, **RDP is exposed on both DCs** (finding) and **WinRM is open on DC01**.

---

## Part 3 — Multi-Company DNS Resolution

The DCs resolve multiple external domains, confirming Adami manages several companies:

| Domain | Resolves To | Hosting | Email | Notes |
|--------|-------------|---------|-------|-------|
| **adamitrasporti.local** | 192.168.60.2, .60.3 | Internal AD | — | Primary AD domain |
| **adamitrasporti.it** | 35.214.245.16 | SiteGround | Outlook (Microsoft 365) | Corporate website |
| **adami.it** | 46.28.0.29 | Artera/ServerDomus | Outlook (Microsoft 365) | Related company, SPF+DKIM |
| **montresor.it** | 194.244.27.106 | Interhost/DNSItalia | mx1.montresor.it (self-hosted) | The "montresor" WiFi SSID! |

**The WiFi network "montresor" (PSK: Htowermontresor) belongs to montresor.it** — another company in the Adami group.

---

## Part 4 — Main LAN Host Inventory (91 Hosts)

ARP sweep discovered **91 live hosts** on 192.168.1.0/24.

### Servers & Infrastructure

| IP | MAC | Vendor | Hostname | Services | Notes |
|----|-----|--------|----------|----------|-------|
| .6 | 00:D0:B8:24:EB:49 | Iomega | — | — | NAS/storage device |
| .8 | 90:09:D0:05:9E:2F | **Synology** | — | HTTP(80), HTTPS(443), SMB(139,445), DSM(5000,5001), WSD(5357) | NAS — Samba 4.6.2, nginx |
| .11 | 4C:E6:76:2E:4C:01 | **BUFFALO** | — | FTP(21), SSH(22), HTTP(80), HTTPS(443), SMB(139,445), LPR(515), rsync(873) | NAS — OpenSSH 3.7.1p2 (ANCIENT), lighttpd, workgroup "ADAMI" |
| .30 | 2C:56:DC:74:17:8A | ASUS | — | SMB with **null session shares**: ADMIN$, C$, D$, **DATI**, IPC$, print$, **Users** | **CRITICAL: data share open** |
| .31 | 00:0C:29:05:36:F4 | **VMware** | — | HTTP(80), HTTPS(443) — Apache | Virtual machine |
| .146 | 80:61:5F:06:19:CB | Beijing Sinead | — | DNS(53) — Unbound | **Gateway/firewall** for all VLANs |

### Industrial Control Systems

| IP | MAC | Vendor | Model | Services | Risk |
|----|-----|--------|-------|----------|------|
| .151 | 00:00:0A:31:83:E7 | **Omron** | **CJ1W-ETN11** | FTP(21) — PLC FTP v1.11 | **CRITICAL: PLC on flat LAN** |
| .152 | 00:A0:45:36:99:03 | **Phoenix Contact** | SpiderControl TM | FTP(21), HTTP(80), **Modbus(502)** — Phoenix-Contact/1.02 | **CRITICAL: Modbus unauthenticated** |
| .194 | 00:00:0A:3C:23:D1 | **Omron** | **CJ2M PLC** | FTP(21), **FINS(9600)**, **EtherNet/IP(44818)** — Omron CJ2M PLC ftpd 1.11 | **CRITICAL: Industrial protocols exposed** |

### Surveillance / Cameras

| IP | MAC | Vendor | Model | Services | Risk |
|----|-----|--------|-------|----------|------|
| .156 | F0:7D:68:00:54:B7 | D-Link | **NUUO NVR** | HTTP(80) — Boa 0.94.13, RTSP(554) — NUUO, UPnP(49152) — Linux 2.6.10 | **CRITICAL: ancient firmware, known CVEs** |
| .160 | 00:40:8C:C9:6B:EB | **AXIS** | **215 PTZ** | FTP(21), HTTP(80) — Boa, RTSP(554) — firmware 4.49 (2009!) | **HIGH: 17-year-old firmware** |

### Network Switches

| IP | MAC | Vendor | Model | Services |
|----|-----|--------|-------|----------|
| .25 | 94:A6:7E:7D:24:0C | **Netgear** | **GS324T** | HTTP(80) — managed switch web UI |
| .26 | 8C:3B:AD:69:94:0C | **Netgear** | **GS348T** | HTTP(80) — managed switch web UI |
| .156 | F0:7D:68:00:54:B7 | D-Link | (see cameras) | — |
| .158 | 1C:BD:B9:89:5D:AB | D-Link | **DGS-1210** ("dlink-895DAB") | HTTP(80) — GoAhead, HTTPS(443) |

### UPS / Power

| IP | MAC | Vendor | Model | Services |
|----|-----|--------|-------|----------|
| .37 | 00:20:85:C7:15:46 | **Eaton** | — | SSH(22) — Digi PortServer, HTTPS(443) — RomPager-Digi/4.01.1 |
| .38 | 00:20:85:D5:E8:3E | **Eaton** | — | SSH(22) — Digi PortServer, HTTPS(443) — RomPager-Digi/4.01.1 |

### Printers / MFPs

| IP | MAC | Vendor | Model | Services |
|----|-----|--------|-------|----------|
| .78 | 00:07:4D:FE:9A:1C | **Zebra** | **ZD230-203dpi ZPL** (S/N: D5J231501874) | FTP(21) **anon**, HTTP(80), LPR(515), JetDirect(9100) |
| .140 | F4:A9:97:AE:A0:0E | **Canon** | **iR-ADV C5560** | SMTP(25), HTTP(80), HTTPS(443), LPR(515), Catwalk(8000,8443), JetDirect(9100) |
| .141 | 9C:32:CE:00:5B:DD | **Canon** | **iR-ADV C3520 III** | HTTP(80), HTTPS(443), LPR(515), IPP(631), Catwalk(8000,8443), JetDirect(9100) |
| .242 | 8C:52:19:2B:C6:DD | **Sharp** | **BP-50C26** | FTP(21) **anon**, HTTP(80), HTTPS(443), LPR(515), IPP(631), VNC(5900), JetDirect(9100) |
| .243 | 34:9F:7B:CE:7F:8E | **Canon** | — | LPR(515), JetDirect(9100) |
| .244 | F4:A9:97:D6:56:AE | **Canon** | **iR-ADV C3530** | SMTP(25), HTTP(80), HTTPS(443), LPR(515), Catwalk(8000,8443), JetDirect(9100) |

### POS / Specialized

| IP | MAC | Vendor | Role |
|----|-----|--------|------|
| .42 | C8:40:52:08:47:CB | **PAX Technology** | POS terminal |
| .45 | C8:40:52:08:47:CB | **PAX Technology** | POS terminal (same MAC = same device or bridged) |
| .12, .36, .98, .99, .196 | 00:15:39:* | **Technodrive srl** | Transport/logistics terminals |
| .32, .33 | 04:91:62:* | **Microchip Technology** | Embedded/IoT devices |
| .39 | D4:AD:20:* | **USR IOT** | IoT gateway |

### Telephony

| IP | MAC | Vendor |
|----|-----|--------|
| .50, .72 | 00:13:D1:* | **Kirk telecom** — DECT base stations |
| .61, .71, .102, .115, .121, .130, .159, .167, .186 | 00:E0:C5:* | **Bcom Electronics** — VoIP phones (9 units) |

### Workstations (HP)

| IP | MAC | Vendor |
|----|-----|--------|
| .4, .5 | D0:7E:28:*, 78:48:59:* | Hewlett Packard |
| .27, .28 | 2C:23:3A:* | Hewlett Packard |
| .58 | C8:D9:D2:* | Hewlett Packard |
| .75 | BC:E9:2F:* | HP |
| .79 | 6C:02:E0:* | HP |
| .94 | C8:D9:D2:* | Hewlett Packard |
| .101 | 6C:02:E0:* | HP |
| .104 | 38:CA:84:* | HP |
| .147 | 30:24:A9:* | HP |
| .173 | 50:81:40:* | HP |
| .177 | C0:18:03:* | HP |
| .184 | BC:E9:2F:* | HP |
| .198 | A8:B1:3B:* | HP |

---

## Part 5 — Credential & Access Findings

### F-LAN-01: DATI Share on .30 — Null Session Full Access (CRITICAL)

```
\\192.168.1.30\DATI — accessible WITHOUT authentication

Contents include:
├── cassaAdami*.exe         — Cash register software (multiple versions)
├── cassaTceRelayUSBnew.exe — TCE relay controller
├── AnyDesk (1).exe         — Remote access installer
├── avast_business_agent_setup_online*.exe — Security agent installer
├── DhcpExplorer.exe        — Network discovery tool
├── cpub-TERMINAL-TERMINAL-CmsRdsh (1).rdp — RDP config file
├── DB PROGRAMMI/           — Database programs
├── DATI1/                  — Sub-data folder
├── Documentale SIMA/       — Document management system
├── FATTURE AMAZON X PAOLO/ — Amazon invoices for employee "Paolo"
├── indirizzi utili/        — Useful addresses / contacts
├── ControlloKmMezziPropri/ — Vehicle fleet km tracking
├── Copia di 04.2025*.xls  — Financial spreadsheets
├── Configurazione_CartellaMacro_Personal_Simone.docx — IT config doc
└── ...many more sensitive files

⚠ Anyone on the LAN can read and WRITE to this share
⚠ Contains executables that could be trojaned
⚠ Contains financial data and employee information
⚠ RDP configuration files could contain saved credentials
```

### F-LAN-02: Zebra Printer Anonymous FTP (HIGH)

```
192.168.1.78 — Zebra ZD230 label printer
FTP: anonymous login accepted
Files readable: fonts, firmware files
Model: ZTC ZD230-203dpi ZPL
Firmware: V89.21.16Z
Serial: D5J231501874
Web admin: requires auth (username + password form)
```

### F-LAN-03: Sharp MFP Anonymous FTP with Write Access (HIGH)

```
192.168.1.242 — Sharp BP-50C26
FTP: anonymous login accepted
Directory listing: "lp" folder (print spooler)
Permissions: d-w--w--w- (WRITE access!)
VNC port 5900 also open

⚠ Write access to print spooler = potential for malicious print jobs
⚠ VNC could allow remote desktop of MFP control panel
```

### F-LAN-04: AXIS Camera RTSP Stream Accessible (HIGH)

```
192.168.1.160 — AXIS 215 PTZ Network Camera
Firmware: 4.49 (August 2009 — 17 YEARS OLD)
RTSP stream: HTTP 200 (accessible)
MJPEG stream: 401 (requires auth)
FTP: open (anonymous status unknown)
HTTP operator page: 401

⚠ RTSP live video feed may be viewable without auth
⚠ Firmware from 2009 — dozens of known CVEs
⚠ PTZ = Pan-Tilt-Zoom — attacker can control camera direction
```

### F-LAN-05: NUUO NVR on Ancient Linux (CRITICAL)

```
192.168.1.156 — NUUO IP Surveillance System
Server: Boa HTTPd 0.94.13
RTSP: NUUO IP Surveillance rtpsd
UPnP: Linux 2.6.10 (circa 2004!)
HTTP: 401 Unauthorized (basic auth)

⚠ NUUO NVR has CRITICAL known vulnerabilities:
  CVE-2018-15716: Remote Code Execution (no auth)
  CVE-2022-23227: Authentication bypass
  CVE-2023-49593: Additional RCE
⚠ Running on Linux 2.6.10 — kernel from 2004
⚠ Boa web server has not been maintained since 2005
```

### F-LAN-06: Omron PLCs on Flat Corporate LAN (CRITICAL)

```
192.168.1.151 — Omron CJ1W-ETN11 (Ethernet module for CJ1 PLC)
  FTP server v1.11 — PLC programming/config interface
  No segmentation from corporate workstations

192.168.1.194 — Omron CJ2M PLC
  FTP server v1.11 — PLC programming/config interface
  No segmentation from corporate workstations

⚠ PLCs control physical processes (manufacturing, logistics)
⚠ FTP access to PLC = ability to modify ladder logic
⚠ No OT/IT segmentation — any workstation can reach PLCs
⚠ CJ1W-ETN11 and CJ2M have known vulnerabilities
```

### F-LAN-07: Phoenix Contact Industrial Controller (CRITICAL)

```
192.168.1.152 — Phoenix Contact with SpiderControl HMI
  FTP(21) + HTTP(80) — Phoenix-Contact/1.02
  SpiderControl TM = HMI/SCADA web interface

⚠ Industrial HMI accessible from corporate LAN
⚠ No OT network segmentation
```

### F-LAN-08: Canon Printers with SMTP (MEDIUM)

```
192.168.1.140 — Canon iR-ADV C5560 (SMTP + web admin)
192.168.1.141 — Canon iR-ADV C3520 III (web admin)
192.168.1.244 — Canon iR-ADV C3530 (SMTP + web admin)

Canon Catwalk admin on port 8000/8443 — requires user auth
SMTP on .140 and .244 — printers can send email (scan-to-email)
⚠ Scan-to-email credentials often stored in printer config
⚠ Catwalk admin could expose address books with email/domain creds
```

### F-LAN-09: Buffalo NAS with Ancient SSH (HIGH)

```
192.168.1.11 — BUFFALO NAS
  OpenSSH 3.7.1p2 — released 2003 (23 YEARS OLD!)
  lighttpd 1.4.23
  Samba 3.x-4.x (workgroup: ADAMI)
  FTP, rsync also open
  SMB protocol negotiation fails (only supports SMBv1?)

⚠ OpenSSH 3.7.1 has dozens of critical CVEs
⚠ Likely cannot be patched — EOL hardware
```

### F-LAN-10: RDP Exposed on Domain Controllers (HIGH)

```
DC01 (192.168.60.2): RDP port 3389 OPEN
DC02 (192.168.60.3): RDP port 3389 OPEN
DC01: WinRM port 5985 OPEN

⚠ RDP on DCs from any host on the LAN
⚠ WinRM on DC01 = PowerShell remoting accessible
⚠ Should be restricted to admin jump box / management VLAN
```

### F-LAN-11: All Devices on Flat /24 — No Segmentation (CRITICAL)

```
SINGLE FLAT NETWORK: 192.168.1.0/24

  Contains ALL of these on the SAME subnet:
  ├── Domain controllers (AD, Kerberos, LDAP)
  ├── File servers / NAS (Synology, Buffalo, ASUS)
  ├── Industrial PLCs (Omron × 2, Phoenix Contact)
  ├── Surveillance cameras/NVR (AXIS, NUUO)
  ├── POS terminals (PAX × 2)
  ├── UPS management (Eaton × 2)
  ├── Network switches (Netgear × 2, D-Link × 2)
  ├── Printers/MFPs (Canon × 4, Sharp, Zebra)
  ├── VoIP phones (Bcom × 9, Kirk DECT × 2)
  ├── Transport/logistics terminals (Technodrive × 5)
  ├── IoT devices (Microchip × 2, USR IOT × 1)
  ├── VMware VM
  └── ~13 HP workstations

  ⚠ ANY compromised workstation can reach PLCs, cameras, NVR, DCs
  ⚠ Ransomware on one host can spread to ALL 91 hosts
  ⚠ No OT/IT separation — violation of IEC 62443
```

---

## Part 6 — Web Interface Inventory

| IP | Device | Port | URL | Auth Required | Model |
|----|--------|------|-----|---------------|-------|
| .8 | Synology NAS | 80, 443, 5000, 5001 | http(s)://ip/ | Yes (DSM login) | Synology DSM, nginx |
| .11 | Buffalo NAS | 80, 443 | http://ip/ | Unknown | lighttpd 1.4.23 |
| .25 | Netgear switch | 80 | http://ip/ | Yes (web login) | GS324T |
| .26 | Netgear switch | 80 | http://ip/ | Yes (web login) | GS348T |
| .31 | VMware VM | 80, 443 | http(s)://ip/ | Unknown | Apache |
| .37 | Eaton UPS | 443 | https://ip/ | Yes (login form) | RomPager-Digi/4.01.1 |
| .38 | Eaton UPS | 443 | https://ip/ | Yes (login form) | RomPager-Digi/4.01.1 |
| .78 | Zebra printer | 80 | http://ip/ | Config view: No, Settings: Yes | ZD230 ZPL |
| .140 | Canon printer | 80, 8000 | http://ip:8000/ | Yes (user auth) | iR-ADV C5560 |
| .141 | Canon printer | 80, 8000 | http://ip:8000/ | Yes (user auth) | iR-ADV C3520 III |
| .152 | Phoenix Contact | 80 | http://ip/ | Unknown | SpiderControl TM |
| .156 | NUUO NVR | 80 | http://ip/ | Yes (basic auth, 401) | Boa 0.94.13 |
| .158 | D-Link switch | 80, 443 | http://ip/web/login.asp | Yes (login page) | DGS-1210 ("dlink-895DAB") |
| .160 | AXIS camera | 80 | http://ip/ | Mixed (RTSP=no, MJPEG=yes) | 215 PTZ, fw 4.49 (2009) |
| .242 | Sharp MFP | 80, 443 | http://ip/main.html | Unknown | BP-50C26, RapidLogic/1.1 |
| .244 | Canon printer | 80, 8000 | http://ip:8000/ | Yes (user auth) | iR-ADV C3530 |

---

## Part 7 — 4th Subnet: 192.168.6.0/x

IT reported a file server at **192.168.6.1** (SMB shares, credentials: `adminada`). Testing from LAN:

| Test | Result |
|------|--------|
| Route | Via 192.168.1.146 (gateway) |
| TCP 445 | Timeout |
| TCP 139 | Timeout |
| TCP 80 | Timeout |
| All 10 common ports | Timeout |

**192.168.6.1 is unreachable from both guest WiFi AND main LAN.** This subnet requires either:
- A different VLAN (possibly accessible only from specific ports/hosts)
- VPN access
- Specific firewall rules not applicable to our host

---

## Part 8 — Summary of New LAN Findings

| ID | Severity | Finding |
|----|----------|---------|
| F-LAN-01 | **CRITICAL** | .30 DATI share open to null session — corporate data exposed |
| F-LAN-02 | **HIGH** | Zebra printer anonymous FTP |
| F-LAN-03 | **HIGH** | Sharp MFP anonymous FTP with write access + VNC |
| F-LAN-04 | **HIGH** | AXIS camera RTSP stream accessible, firmware from 2009 |
| F-LAN-05 | **CRITICAL** | NUUO NVR on Linux 2.6.10 — known critical RCE CVEs |
| F-LAN-06 | **CRITICAL** | Omron PLCs on flat corporate LAN — no OT segmentation |
| F-LAN-07 | **CRITICAL** | Phoenix Contact HMI on flat corporate LAN |
| F-LAN-08 | **MEDIUM** | Canon printers with SMTP — scan-to-email creds exposure risk |
| F-LAN-09 | **HIGH** | Buffalo NAS with OpenSSH 3.7.1 from 2003 |
| F-LAN-10 | **HIGH** | RDP + WinRM exposed on Domain Controllers |
| F-LAN-11 | **CRITICAL** | ALL devices on flat /24 — zero network segmentation |
| F-LAN-12 | **MEDIUM** | 4th subnet (192.168.6.x) unreachable — investigate access path |
| F-LAN-13 | **HIGH** | 91 hosts on single broadcast domain — massive blast radius |
| F-LAN-14 | INFO | Multi-company infrastructure — adamitrasporti.it, adami.it, montresor.it all managed from same AD |
