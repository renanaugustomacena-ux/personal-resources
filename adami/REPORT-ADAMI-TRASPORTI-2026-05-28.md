# SECURITY ASSESSMENT REPORT — ADAMI TRASPORTI SPA

```
════════════════════════════════════════════════════════════════
  CLASSIFICATION:  CONFIDENTIAL — IT Security Use Only
  CLIENT:          Adami Trasporti SPA
  DOMAIN:          adamitrasporti.local
  ASSESSMENT TYPE: Internal Network Security Audit
  DATES:           2026-05-19 (Pass 1), 2026-05-26 (Pass 2),
                   2026-05-28 (Pass 3 — Guest WiFi + Wired LAN)
  ASSESSOR:        macena IT Security
  REPORT DATE:     2026-05-28
  POSTURE SCORE:   2 / 10
════════════════════════════════════════════════════════════════
```

---

# PART I — EXECUTIVE BRIEFING

## 1. Executive Summary

Adami Trasporti's network is critically compromised. The assessment found **65+ vulnerabilities**, **55+ credentials exposed in plaintext on open file shares**, **2 ransomware artifacts** proving at least one previous breach in 2022, and **zero network segmentation** — industrial control systems (PLCs), surveillance cameras, POS terminals, domain controllers, and employee workstations all share the same flat network.

### Key Numbers

| Metric | Value |
|--------|-------|
| Overall security posture | **2 / 10** |
| Network segments discovered | 5 |
| Total hosts discovered | 160+ (91 LAN + 16 guest + 55 domain computers + servers) |
| Domain users | 172 |
| Domain computers | 55 |
| Infrastructure servers | 12 (all Windows Server 2022 Datacenter) |
| Credentials found in plaintext | **55+** (32 domain RDP accounts, MySQL, camera admin, VPN CA key, Wi-Fi PSKs, AnyDesk, local admin with no password) |
| Ransomware artifacts | **2** (Phobos 2022-04-08, Locky historical) |
| Industrial control systems on flat LAN | **3** (2 Omron PLCs + 1 Phoenix Contact with Modbus) |
| Critical findings | 14 |
| High findings | 18 |
| Medium findings | 19 |
| Total findings | 65+ |
| Companies managed from same infrastructure | 6+ (Adami Trasporti, Adami, Bianchi, TCE, Alfa, Montresor) |
| Time to full compromise from guest WiFi | **< 60 seconds** (if PCFRANCESCA is online) |

### Top 5 Risks in Plain Language

1. **32 employee passwords are stored in a text file that anyone on the network can read without logging in.** These passwords give access to the company's transport management system (SGA) and remote desktops. An attacker — or a disgruntled employee — can access all corporate systems.

2. **The company was hit by ransomware (Phobos) in April 2022, and the same vulnerabilities that enabled that attack are still present.** Open file shares, no passwords on admin accounts, remote access tools running with no security. The encrypted file is still on the share, never cleaned up.

3. **The VPN master key is stored on an open file share.** Anyone who copies this key can generate their own VPN credentials and access the corporate network from anywhere in the world, forever, without detection.

4. **Industrial PLCs that control physical processes (manufacturing, logistics) are on the same network as employee laptops and guest WiFi devices.** There is no segmentation. An attacker on any workstation can reprogram PLCs using completely unauthenticated industrial protocols (FINS, EtherNet/IP, Modbus).

5. **91 devices on one flat network with no segmentation.** Surveillance cameras, POS terminals, printers, NAS devices, domain controllers, PLCs, and workstations are all on the same subnet. One compromised device = access to everything.

---

## 2. Scope & Methodology

### Pass 1 — 2026-05-19 (PCFRANCESCA, Guest WiFi, Passive)
- **Machine:** PCFRANCESCA (HP ProBook 450 G7, Windows 11 Pro)
- **IP:** 192.168.192.61 on Adami_Guest WiFi
- **Method:** Passive observation, PowerShell enumeration, no active scanning
- **Produced:** Documents 01-15

### Pass 2 — 2026-05-26 (PCFRANCESCA, Guest WiFi, Expanded)
- **Same machine and position**
- **Method:** Live data extraction, credential inventory, methodology documentation
- **Produced:** Documents 16-17
- **Key additions:** VPN discovery, AnyDesk extraction, Wi-Fi PSKs, browser credential DB inventory, ghost user profiles

### Pass 3 — 2026-05-28 (Linux, Guest WiFi + Wired LAN)
- **Machine:** Linux workstation (Ubuntu 24.04)
- **Guest WiFi IP:** 192.168.192.129 | **Wired LAN IP:** 192.168.1.66
- **Tools:** nmap 7.94SVN, smbclient, rpcclient, ldapsearch, dig, curl, tcpdump, python3
- **Method:** Active scanning — ARP sweeps, SYN scans, full 65535-port scans, SMB enumeration, LDAP with captured creds, FTP probing, web fingerprinting
- **Produced:** Documents 18-20
- **Key additions:** 91-host LAN inventory, LDAP full dump (172 users, 55 computers), 32 plaintext domain passwords, VPN CA private key, MySQL creds, camera creds, ransomware artifacts, ICS/SCADA exposure, FILESERVER01 shares

### What Was NOT Done
- No exploitation or code execution
- No password cracking
- No traffic interception / MITM
- No modification of any system
- All scanning was non-destructive

---

# PART II — NETWORK ARCHITECTURE

## 3. Complete Topology

```
═══════════════════════════════════════════════════════════════════════════
                              INTERNET
                         Welcome Italia ISP
                       ┌───────────────────┐
                       │ DNS: 80.93.143.42 │
                       │       80.93.143.44│
                       └─────────┬─────────┘
                                 │
                    ┌────────────┤           VPN: 45.151.15.58
                    │            │           HAProxy :80 (503)
                    │  ┌─────────┴─────────┐ OpenVPN UDP :1194
                    │  │                   │
                    │  │  EDGE GATEWAY     │
                    │  │  Guest: .192.1    │
                    │  │  LAN:   .1.146    │
                    │  │  MAC: 80:61:5f:   │
                    │  │       06:19:cb    │
                    │  │  DNS: Unbound     │
                    │  │  Likely pfSense   │
                    │  │                   │
                    │  └─┬────┬────┬────┬──┘
                    │    │    │    │    │
          ┌─────────┘    │    │    │    └──────────────┐
          │              │    │    │                   │
          ▼              ▼    │    ▼                   ▼
   ┌────────────┐ ┌──────────┐│┌──────────────┐ ┌──────────────┐
   │GUEST WIFI  │ │ MAIN LAN ││ │INFRASTRUCTURE│ │FILE SERVER   │
   │.192.0/24   │ │ .1.0/24  ││ │.60.0/24      │ │.6.0/x        │
   │            │ │          ││ │              │ │              │
   │16 devices  │ │91 hosts  ││ │12 servers    │ │.6.1 (SMB)    │
   │NO client   │ │FLAT /24  ││ │Win Srv 2022  │ │Unreachable   │
   │isolation   │ │NO segm.  ││ │              │ │from LAN+guest│
   │            │ │          ││ │DC01    .60.2 │ │              │
   │PSK:        │ │PLCs,cams,││ │DC02    .60.3 │ │Auth:         │
   │1DfGhYu53   │ │POS,DCs,  ││ │ADCONNECT .4  │ │adminada /    │
   │            │ │printers, ││ │FILESVR01 .5  │ │Q-2!?H.)S5_  │
   │            │ │NAS,UPS,  ││ │SGA       .6  │ │t8$Y          │
   │            │ │switches  ││ │SGA-DB    .7  │ │              │
   └────────────┘ └──────────┘│ │RDS-SCB   .8  │ └──────────────┘
                              │ │RDS-HOST1 .9  │
                     ┌────────┘ │RDS-HOST2 .10 │
                     ▼          │THINMAN01 .12 │
              ┌────────────┐   └──────────────┘
              │VPN TUNNEL  │
              │10.37.169.0 │
              │/24         │
              │DNS: .1.146 │
              │Full tunnel │
              └────────────┘
```

## 4. Inter-VLAN Reachability Matrix

```
                  Guest (.192)     Main LAN (.1)    Infra (.60)      FileServer (.6)
                ┌────────────────┬────────────────┬────────────────┬────────────────┐
Guest           │     N/A        │ ALL TCP ✗      │ ALL TCP ✗      │ ALL TCP ✗      │
(.192)          │                │ 65535 verified │ 65535 verified │                │
                ├────────────────┼────────────────┼────────────────┼────────────────┤
Main LAN        │ TCP 7680 ✓     │     N/A        │ ALL ✓          │ ALL ✗          │
(.1)            │ (inbound DO)   │                │ full access    │ (timeout)      │
                ├────────────────┼────────────────┼────────────────┼────────────────┤
Infra           │ TCP 7680 ✓     │ ALL ✓          │     N/A        │ Unknown        │
(.60)           │ (inbound DO)   │ (likely)       │                │                │
                └────────────────┴────────────────┴────────────────┴────────────────┘
```

## 5. VPN Infrastructure

**Endpoint:** 45.151.15.58 (pfSense), HAProxy on :80 returning 503, OpenVPN on UDP :1194

**Config:** AES-128-CBC (deprecated) / AES-128-GCM, SHA256, full tunnel, OpenVPN 2.5.0 (2020 — outdated)

**VPN CA PRIVATE KEY ON OPEN SHARE:** `\\192.168.1.30\DATI\OpenVpn Giuseppe Prova\ca.key`

Also on share: ca.crt, ta.key, techpagiuseppe1.key/crt/csr, full .ovpn config

**TLS Auth Key (extracted from PCFRANCESCA):**
```
-----BEGIN OpenVPN Static key V1-----
5cb2b9b85248a553ade0bad460d01467
7fede77530494e7432ebf13578815d2d
ef11ec8297c27bf7ca57341695ea0575
4dcfca1ef3820860c1a4d022abd455a3
52889408d38012501fddc83b4c42da15
7fe7b2954346c607bae4fb60847a58ec
42579ce5d2b049420f2a1e7ca2554782
9dd8fe9b7ff341aa7dbcfba7046ec45f
a5ad3a2cdbf97c5844e11f9ab770f7fa
31eb3168945933079140eef7cd87b7b9
b5e9d2f09dc12f8140ed56e827cdbfd9
b0250a36dc645aa66f27d8a8e44908fa
b397cb610b7d06ef192f602ab81ea97f
05587ae9e0c07a77a98c8e0f03ebb16c
a40b46ac8e7355e824457d36d50f5720
ee02cf5b74a0dfa5482c1a760c58db42
-----END OpenVPN Static key V1-----
```

## 6. Multi-Company DNS

| Domain | IP | Hosting | Email |
|--------|-----|---------|-------|
| adamitrasporti.local | 192.168.60.2/3 | Internal AD | — |
| adamitrasporti.it | 35.214.245.16 | SiteGround | Outlook 365 |
| adami.it | 46.28.0.29 | Artera | Outlook 365 |
| montresor.it | 194.244.27.106 | Interhost | mx1.montresor.it |

Companies from NAS share names: **Adami Trasporti, Bianchi, TCE, Alfa, Frenocar, Montresor**

---

# PART III — ASSET INVENTORY

## 7. Infrastructure Servers

| Hostname | IP | OS | Role | Open Ports |
|----------|----|----|------|------------|
| DC01 | .60.2 | Win 2022 DC | Domain Controller | 53,88,135,139,389,445,464,636,3268,3269,3389,5985,9389 |
| DC02 | .60.3 | Win 2022 DC | Domain Controller | (identical) |
| ADCONNECT | .60.4 | Win 2022 DC | Azure AD Connect | 3389,5985 |
| FILESERVER01 | .60.5 | Win 2022 DC | File Server | 445,3389,5985 |
| SGA | .60.6 | Win 2022 DC | Transport App | 445,3389,5985 |
| SGA-DB | .60.7 | Win 2022 DC | SQL Server | 445,**1433**,3389,5985 |
| RDS-SCB | .60.8 | Win 2022 DC | RD Broker | **80,443**,445,3389,5985 |
| RDS-HOST01 | .60.9 | Win 2022 DC | RD Session Host | 445,3389,5985 |
| RDS-HOST02 | .60.10 | Win 2022 DC | RD Session Host | — |
| THINMAN01 | .60.12 | Win 2022 DC | Thin Client Mgmt | — |
| RDS-HOSTMAG01 | — | Win **2016** Std | RD Host (warehouse) | — |

## 8. Main LAN — 91 Hosts (192.168.1.0/24)

### ICS/SCADA (CRITICAL — no segmentation)

| IP | MAC | Model | Protocols |
|----|-----|-------|-----------|
| .151 | 00:00:0A:31:83:E7 | **Omron CJ1W-ETN11** | FTP(21) |
| .152 | 00:A0:45:36:99:03 | **Phoenix Contact SpiderControl** | FTP(21), HTTP(80), **Modbus(502)** |
| .194 | 00:00:0A:3C:23:D1 | **Omron CJ2M** | FTP(21), **FINS(9600)**, **EtherNet/IP(44818)** |

### Surveillance

| IP | MAC | Model | Services |
|----|-----|-------|----------|
| .156 | F0:7D:68:00:54:B7 | **NUUO NVR** | HTTP(80) Boa 0.94.13, RTSP(554), UPnP — **Linux 2.6.10 (2004!)** |
| .160 | 00:40:8C:C9:6B:EB | **AXIS 215 PTZ** | FTP(21), HTTP(80), RTSP(554) — **firmware 4.49 (2009, 17 years old)** |

### NAS / Storage

| IP | MAC | Device | Services | Notes |
|----|-----|--------|----------|-------|
| .6 | 00:D0:B8:24:EB:49 | **Lenovo ix4-300d** | SMB (80+ shares) | Null session lists shares, contents need auth |
| .8 | 90:09:D0:05:9E:2F | **Synology** | HTTP, HTTPS, SMB (Samba 4.6.2), DSM | Rejects anonymous |
| .11 | 4C:E6:76:2E:4C:01 | **BUFFALO** | FTP, **SSH 3.7.1 (2003!)**, HTTP, SMB, rsync | **Ancient SSH — dozens of CVEs** |
| .30 | 2C:56:DC:74:17:8A | **ASUS** | **SMB null session: DATI share open** | CRITICAL — corporate data exposed |

### Switches

| IP | Model | Web Admin |
|----|-------|-----------|
| .25 | Netgear **GS324T** | http://192.168.1.25/ |
| .26 | Netgear **GS348T** | http://192.168.1.26/ |
| .158 | D-Link **DGS-1210** | http://192.168.1.158/web/login.asp |

### UPS

| IP | Model | Services |
|----|-------|----------|
| .37 | **Eaton** | SSH (Digi PortServer), HTTPS (RomPager-Digi/4.01.1) |
| .38 | **Eaton** | SSH (Digi PortServer), HTTPS (RomPager-Digi/4.01.1) |

### Printers

| IP | Model | FTP Anon | Key Services |
|----|-------|----------|-------------|
| .78 | **Zebra ZD230** (S/N D5J231501874) | **YES** | FTP, HTTP, LPR, JetDirect |
| .140 | **Canon iR-ADV C5560** | No | SMTP(25), HTTP, Catwalk(8000) |
| .141 | **Canon iR-ADV C3520 III** | No | HTTP, IPP(631), Catwalk(8000) |
| .242 | **Sharp BP-50C26** | **YES (writable!)** | FTP, HTTP, HTTPS, **VNC(5900)**, JetDirect |
| .243 | Canon (unknown) | — | LPR, JetDirect |
| .244 | **Canon iR-ADV C3530** | No | SMTP(25), HTTP, Catwalk(8000) |

### Other Key Devices

| IP | MAC | Type |
|----|-----|------|
| .42, .45 | C8:40:52:* | **PAX POS terminals** (same MAC) |
| .12, .36, .98, .99, .196 | 00:15:39:* | **Technodrive** logistics terminals |
| .50, .72 | 00:13:D1:* | **Kirk** DECT phones |
| .61, .71, .102, .115, .121, .130, .159, .167, .186 | 00:E0:C5:* | **Bcom** VoIP phones (9 units) |
| .31 | 00:0C:29:* | **VMware** VM (Apache) |
| .146 | 80:61:5F:* | **Gateway/firewall** (Unbound DNS) |

### HP Workstations (16)
.4, .5, .27, .28, .58, .75, .79, .94, .101, .104, .147, .173, .177, .184, .198, and more

## 9. Active Directory — 172 Users, 55 Computers

**Domain Admins:** Administrator, adm.cesare.calza (Cesare Calzà)

**All domain users (75 named + 45 AdamiRemote + service accounts):**
```
acs.test, AdamiRemote1-45, adm.cesare.calza, Administrator,
adm.stefanobonomi, alessio.ballarini, andrea.franzoia,
andrea.giardini, andrea.guandalini, andrea.morelli, andreea.pal,
anmoldeep.kaur, cassa, cassa1.adami, cassa.adami,
cristina.adami, daniela.bellorio, dejan.vucenovic, elena.lacatus,
elena.malini, enzo.benetti, fabrizio.martinelli, ferruccio.cerri,
filippo.adami, filippo.morocutti, francesca.varalta,
francesco.olivieri, frenocartv, giorgio.adami, giorgio.zanella,
greta.bozzini, guardiania.adami, Guest, krbtgt, lavaggio1,
lorella.zuanazzi, marco.iavarone, mario.rossi, massimo.mele,
massimo.prova, matteo.brugnoli, mattia.soprana, michele.bonomi,
monica.bonvicini, MSOL_6a6fc6a0da26, nemanja.milovanovic,
nicola.bonomi, nicole.speri, officina1, paolo.fantoni,
paolo.robbi, patrizia.adami, rf1, rf3, rf6, rf9,
riccardo.olivieri, riccardo.stabellini, roberta.maistri,
sanjiv.kumar, sara.silvestri, scanner, service.adami,
simone.severino, stage, stefano.adami, stefano.bonomi,
tea.vejinovic, thinman, tommaso.cordano, umberto.pase,
vinicio.locatelli, viviana.cortesi, vojkan.sebic, xlog1, xlog2
```

**All 55 domain computers** — 12 servers (Win 2022), 1 server (Win 2016), 42 workstations (Win 11/10)

---

# PART IV — CREDENTIAL EXPOSURE

## 10. Domain RDP Credentials (32 Accounts)

**Source:** `\\192.168.1.30\DATI\RDP\RDP SGA nuovo server\RD SGA ADAMI.txt`
**Access:** NULL SESSION | **RDS Gateway:** rdweb.adamitrasporti.com | **Server:** RDS-SCB (192.168.60.8)

| Account | Employee | Password |
|---------|----------|----------|
| AdamiRemote1 | Lucia | `Wsert1Yq22` |
| AdamiRemote2 | Magda | `QzZews91a` |
| AdamiRemote3 | Beppe | `Xa84Erf2i` |
| AdamiRemote4 | Olivio | `Pa56ygfg3` |
| AdamiRemote5 | Sofia Cavallini | `Yf28JkZ1pf` |
| AdamiRemote6 | Maicol | `Prt2854dF1d` |
| AdamiRemote7 | Marco (Bianchi) | `RvBe3L4uW` |
| AdamiRemote8 | Luca (Bianchi) | `YuHpvrE3` |
| AdamiRemote9 | Filippo | `Tag1dj3Bgh9` |
| AdamiRemote10 | Marzia | `45HjrtyKhj98xQhH6` |
| AdamiRemote11 | Davide (Bianchi) | `Xy31Pf2GZt3` |
| AdamiRemote12 | Francesco Grazioso | `Sqw2Km678Kp` |
| AdamiRemote14 | Damiano Bianchi | `1RgHjk54k2P` |
| AdamiRemote15 | Andrea Giardini | `27FgJkr89Kj` |
| AdamiRemote16 | Vojkan | `43ErfVb1QP45` |
| AdamiRemote17 | Daniela | `1AsdGvb34Kj9u` |
| AdamiRemote18 | Paolo | `1KFgn43Eds345` |
| AdamiRemote19 | Michele Bonomi | `S2dU2Km975Kw` |
| AdamiRemote20 | Monica Bonvicini | `1WsdFgn4567W` |
| AdamiRemote21 | Roberta Maistri | `4T56Kng7854W` |
| AdamiRemote22 | Francesco Olivieri | `5GK6Pmr9213W` |
| AdamiRemote23 | Nicola Bonomi | `7fK6Tkd7483W` |
| AdamiRemote24 | Vinicio Locatelli | `maverick65` |
| AdamiRemote25 | Simone Zambaldo | `1WeFgtRj345A9` |
| AdamiRemote26 | Umberto Pase | `Scfg!Gk45PScfg!Gk45P` |
| AdamiRemote27 | Robert slovensko | `4TeFLtzj345X8` |
| AdamiRemote28 | Stefano Adami | `1WerFgjk12LVb` |
| AdamiRemote31 | Enzo Benetti | `Rghr!Us87HSwer!Vk83P` |
| AdamiRemote32 | Oppeano | `KerT4$12Sxz6g` |
| filippo | — | `1filippoada2` |
| marzia buganza | — | `12345678` |

**Verification:** `smbclient //192.168.60.2/IPC$ -U 'adamitrasporti\AdamiRemote1%Wsert1Yq22'` — confirmed active

## 11. Other Credentials

| Type | Username | Password/Key | Source |
|------|----------|-------------|--------|
| MySQL | simone | `wErFvbn$_2` | `\\192.168.1.30\DATI\pw Simone Mysql.txt` (null session) |
| Surveillance | superuser | `12Sdght$jkN` (Q: Doom, DarthVader, Hey) | `\\192.168.1.30\DATI\IVMS\Credenziali Client Telecamere.txt` (null session) |
| VPN CA | — | **PRIVATE KEY** (generates unlimited certs) | `\\192.168.1.30\DATI\OpenVpn Giuseppe Prova\ca.key` (null session) |
| VPN client | Giuseppe Bianchi | Full cert chain + config | Same folder (null session) |
| VPN client | francescav | PKCS12 (no p12 password) | PCFRANCESCA disk (doc 17) |
| WiFi | Adami_Guest | `1DfGhYu53` | PCFRANCESCA (doc 17) |
| WiFi | montresor | `Htowermontresor` | PCFRANCESCA (doc 17) |
| AnyDesk | ID 325232966 | Hash: `68d71c8c...f601f8` Salt: `ced3b533...e06c1` | PCFRANCESCA (doc 17) |
| Local admin | sandro | **NO PASSWORD** | PCFRANCESCA (doc 12) |
| Local user | ASPNET | **NO PASSWORD** | PCFRANCESCA (doc 12) |
| File server | adminada | `Q-2!?H.)S5_t8$Y` | IT-provided (192.168.6.1) |
| Credential Mgr | itgroup@adamitrasporti.com | SSO token cached | PCFRANCESCA (doc 17) |
| GitHub PAT | renanaugustomacena-ux | Token cached | PCFRANCESCA (doc 17) |
| Browser DBs | 3 users × 2-3 browsers | 7 SQLite databases (383 KB total) | PCFRANCESCA (doc 17) |
| Domain cached | elena.malini | DCC2 hash in registry | PCFRANCESCA (doc 17) |

---

# PART V — RANSOMWARE HISTORY

## 12. Phobos Ransomware — 2022-04-08

```
ARTIFACT: Thumbs.db.id[8217DA68-3230].[Decepticon@cock.li].eking
LOCATION: \\192.168.1.30\DATI\DATI1\
DATE:     2022-04-08 01:18:20
SIZE:     262,914 bytes
FAMILY:   Phobos (.eking variant)
CONTACT:  Decepticon@cock.li
VICTIM ID: 8217DA68-3230
```

**The same vulnerabilities that enabled this 2022 attack are still present in 2026:** open shares, no passwords, AnyDesk always-on, no segmentation, no auditing.

## 13. Locky Ransomware Artifact

```
ARTIFACT: 5692F05274A79443E9CDA63C11741BBF.locky
LOCATION: \\192.168.1.30\DATI\DATI1\
DATE:     2005-07-27 (file timestamp — likely from old backup)
SIZE:     86,528 bytes
```

---

# PART VI — ATTACK CHAINS

## 14. Chain 1: Guest WiFi → SMB → Full Compromise (< 60 seconds)
Guest PSK `1DfGhYu53` → scan .192.61 → SMB auth sandro (no password) → PsExec → SYSTEM

## 15. Chain 2: LLMNR Poisoning → Credential Capture
Responder on guest → victim queries internal name → DNS fails → LLMNR → attacker captures NTLM → relay (no SMB signing)

## 16. Chain 3: AnyDesk Remote (from internet)
ID 325232966 → relay always connected → brute-force unattended password → desktop as admin

## 17. Chain 4: Physical Access
No BitLocker → boot USB → full disk → SAM, browser passwords, VPN certs, WiFi keys

## 18. Chain 5: Guest WiFi → Bticino Building Automation
No client isolation → ARP scan → Bticino at .149 → exploit IoT → control building systems

## 19. Chain 6: LAN → PLC/SCADA
Any workstation → Omron CJ2M FINS(9600) / EtherNet/IP(44818) → reprogram PLC. Or Phoenix Contact Modbus(502) → read/write registers. **No authentication.**

## 20. Chain 7: Trojan cassaAdami
Null session → write to DATI share → replace cassaAdami.exe → POS terminals run trojan → capture transactions

## 21. Chain 8: VPN CA Key → Persistent Access
Null session → copy ca.key → generate rogue VPN cert → connect from anywhere forever

## 22. Chain 9: Domain Creds → RDWeb → Corporate Access
Null session → read RD SGA ADAMI.txt → login rdweb.adamitrasporti.com → SGA access → pivot

---

# PART VII — INVESTIGATION PLAYBOOKS

## 23. cassaAdami Integrity

SHA256 baselines (2026-05-28):
```
8ef536007ad...  cassaAdami Last.exe (696,320 B)
9bf09e20753...  cassaAdami NewSafe8sec3sec.exe (696,320 B)
f280b755704...  cassaAdami NewSafe8sec.exe (696,320 B)
f4c5fa76ad1...  cassaAdami NewSafe.exe (696,320 B)
5fd8fec51c1...  Cassa.exe (647,168 B) — v1.7.0, "comando serratura"
d1880beaa1c...  cassaTceRelayUSBnew.exe (720,896 B)
```

Contains `txtPassword`, `&Password:`, `comando serratura` (door lock control). All PE32, no code signing. **Share is writable — verify write test:** `smbclient //192.168.1.30/DATI -N -c 'put /dev/null .writetest; del .writetest'`

## 24. PLC/SCADA Investigation

```bash
# Omron CJ2M — EtherNet/IP
pip install pycomm3
python3 -c "from pycomm3 import CIPDriver; d=CIPDriver('192.168.1.194'); d.open(); print(d.get_plc_info())"

# Phoenix Contact — Modbus
pip install pymodbus
python3 -c "from pymodbus.client import ModbusTcpClient; c=ModbusTcpClient('192.168.1.152'); c.connect(); print(c.read_holding_registers(0,10).registers)"
```

## 25. Surveillance Investigation

```bash
# Try extracted credentials against cameras
curl -sk -u superuser:12Sdght\$jkN http://192.168.1.156/
curl -sk -u root:12Sdght\$jkN http://192.168.1.160/mjpg/video.mjpg
vlc rtsp://192.168.1.160/axis-media/media.amp

# Extract camera IPs from iVMS config
unzip Configurazione-IVMS-4200.zip -d /tmp/ivms/
strings /tmp/ivms/DeviceManagement.S/Device | grep -oE '192\.168\.[0-9]+\.[0-9]+'
```

## 26. Ransomware Artifact Investigation

```bash
# Search all shares for more artifacts
smbclient //192.168.1.30/DATI -N -c 'recurse on; ls' 2>&1 | grep -iE '\.eking|\.phobos|\.lock|ransom|decrypt|readme'

# Check persistence on accessible machines
# Scheduled tasks, services, registry run keys, startup folder
```

---

# PART VIII — REMEDIATION

## 27. EMERGENCY — Do Today

```powershell
# 1. Remove credentials from DATI share (on 192.168.1.30)
Remove-Item "D:\DATI\RDP\RDP SGA nuovo server\RD SGA ADAMI.txt" -Force
Remove-Item "D:\DATI\pw Simone Mysql.txt" -Force
Remove-Item "D:\DATI\IVMS - 4200 con backup\Credenziali Client Telecamere.txt" -Force
Remove-Item "D:\DATI\OpenVpn Giuseppe Prova" -Recurse -Force

# 2. Reset ALL 32 AdamiRemote passwords (on DC01)
# Set-ADAccountPassword -Identity "AdamiRemoteN" -Reset -NewPassword (ConvertTo-SecureString "..." -AsPlainText -Force)

# 3. Remove null session access
Revoke-SmbShareAccess -Name "DATI" -AccountName "Everyone" -Force

# 4. Revoke VPN CA on pfSense, regenerate, re-issue ALL client certs

# 5. Set password on sandro (PCFRANCESCA)
net user sandro NewStrongPassword!

# 6. Change MySQL (simone) and surveillance (superuser) passwords
```

## 28. This Week

```powershell
# Disable SMBv1, enable signing/encryption, disable LLMNR/NetBIOS
# Disable ASPNET account, remove Users share, enable logon auditing
# Enable AP client isolation, move Bticino off guest WiFi
# Restrict DC RDP to management VLAN
# Rotate Adami_Guest WiFi PSK
# Delete CHIARA and elena.malini profiles on PCFRANCESCA
```

## 29. Short-Term (1-4 Weeks)

- Audit gateway inter-VLAN ACLs
- Replace free AnyDesk with enterprise solution
- Upgrade OpenVPN to 2.6.x
- Deploy BitLocker on all laptops
- Replace Buffalo NAS (OpenSSH 3.7.1 EOL)
- Update AXIS camera firmware
- Investigate/replace NUUO NVR (critical CVEs)
- Identify Tenda device on guest WiFi
- Configure password policy (complexity, lockout, history)

## 30. Architecture (Requires Planning)

- **Network segmentation:** Separate VLANs for corporate, servers, ICS/SCADA, surveillance, VoIP, printers, IoT, POS, guest
- **ICS firewall:** Industrial firewall between IT and OT (IEC 62443)
- **Monitoring:** IDS/IPS with industrial protocol signatures
- **Centralized logging:** SIEM for all machines
- **Vulnerability management:** Regular scanning program
- **Incident response:** IR plan, especially for ransomware
- **Security awareness:** Anti-phishing training (Phobos entry vector)

---

# APPENDICES

## A. Assessment Toolkit Location

`~/Desktop/adami-assessment/` — scripts, VPN configs, web shortcuts, evidence, RDP configs, SHA256 hashes

## B. Evidence SHA256 Hashes

```
d7b9f114...  AnyDesk (1).exe
258676f9...  avast_business_agent_setup.exe
8ef53600...  cassaAdami Last.exe
9bf09e20...  cassaAdami NewSafe8sec3sec.exe
f280b755...  cassaAdami NewSafe8sec.exe
f4c5fa76...  cassaAdami NewSafe.exe
5fd8fec5...  Cassa.exe
d1880bea...  cassaTceRelayUSBnew.exe
c0168607...  zebra.exe
```

## C. Lenovo NAS (.6) — 80+ Shares

```
kumar, COMMERCIALE, ROBBI & friends, ADAMI SLOVENSKO, lorella,
StefanoAdami, TOMMASO, FERRUCCIO, PAOLO ROBBI, CMR, sara,
michele, nicola, Tea, log2boxbackup, Frenocar fatture,
MAGAZZINO OPPEANO, ENZO, Daniela, Mattia, FV TCE, FV Bianchi,
FV Adami, Filippo, Documentazione Fornitori, Operativo Bianchi,
personale Bianchi, Amministrazione Bianchi, FRANCESCA, ITfolder,
Massimo, ErrorAttivaBianchi, DoneAttivaBianchi, Tce/Bianchi/Alfa/
Adami fatture passive import, Damiano, Fabrizio, paolo, filmati,
ExportFattureAttive, Tokheim, Stato pratiche assicurative, D2D,
TruckController, Amministrazione Adami, Monica, Riccardo,
Briefing, Documentale, patrizia, Dati TCE, ZimbraBackup,
BackupServer, StefanoBonomi, QuikTransfer, Pictures, Backups...
```

---

**END OF REPORT**

Report date: 2026-05-28 | Assessor: macena IT Security | Classification: CONFIDENTIAL
