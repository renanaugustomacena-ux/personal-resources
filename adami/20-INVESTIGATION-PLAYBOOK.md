# 20 — Investigation Playbook: Access, Verify, Investigate

**Date:** 2026-05-28
**Classification:** CONFIDENTIAL — IT Security Use Only
**Purpose:** Step-by-step procedures to access, investigate, and assess each vulnerable system. This is NOT a vulnerability list — it's an operational investigation guide.

---

## EMERGENCY FINDING: Previous Ransomware Attack (Phobos, 2022-04-08)

```
FILE: \\192.168.1.30\DATI\DATI1\Thumbs.db.id[8217DA68-3230].[Decepticon@cock.li].eking

ANALYSIS:
├── Extension .eking = Phobos ransomware family
├── Contact: Decepticon@cock.li (known Phobos operator)
├── ID tag: 8217DA68-3230 (victim identifier)
├── File date: 2022-04-08 01:18:20
├── Original file (Thumbs.db) exists alongside encrypted copy
│   → Partial recovery was performed, but encrypted artifact remains
├── Location: DATI1 subfolder = employee personal data area
│
└── IMPLICATIONS:
    ├── This network was BREACHED by ransomware operators in April 2022
    ├── The same open shares, flat network, and no-password accounts
    │   that enabled the 2022 attack are STILL present in 2026
    ├── Phobos typically enters via exposed RDP or phishing
    ├── The attacker had access to the DATI share (where this file lives)
    └── No forensic cleanup was completed — artifact left for 4+ years
```

**IMMEDIATE INVESTIGATION:**
1. Search ALL shares and workstations for `.eking`, `.phobos`, `.Deceptive` files
2. Check Windows Event Logs on .30 for April 2022 (if retained)
3. Check AnyDesk logs for unauthorized connections around that date
4. Verify no active persistence mechanisms remain (scheduled tasks, services, registry run keys)

```bash
# Search for more ransomware artifacts across accessible shares
smbclient //192.168.1.30/DATI -N -c 'recurse on; ls' 2>&1 | grep -iE '\.eking|\.phobos|\.lock|ransom|decrypt|readme.*txt'
```

---

## EMERGENCY FINDING: 32 Domain Credentials in Plaintext on Open Share

```
FILE: \\192.168.1.30\DATI\RDP\RDP SGA nuovo server\RD SGA ADAMI.txt
ACCESS: NULL SESSION (no auth required)

CREDENTIALS FOUND (32 accounts):
──────────────────────────────────────────────────────────────────
adamitrasporti\AdamiRemote1  (Lucia)              Wsert1Yq22
adamitrasporti\AdamiRemote2  (Magda)              QzZews91a
adamitrasporti\AdamiRemote3  (Beppe)              Xa84Erf2i
adamitrasporti\AdamiRemote4  (Olivio)             Pa56ygfg3
adamitrasporti\AdamiRemote5  (Sofia Cavallini)    Yf28JkZ1pf
adamitrasporti\AdamiRemote6  (Maicol)             Prt2854dF1d
adamitrasporti\AdamiRemote7  (Marco - Bianchi)    RvBe3L4uW
adamitrasporti\AdamiRemote8  (Luca - Bianchi)     YuHpvrE3
adamitrasporti\AdamiRemote9  (Filippo)            Tag1dj3Bgh9
adamitrasporti\AdamiRemote10 (Marzia)             45HjrtyKhj98xQhH6
adamitrasporti\AdamiRemote11 (Davide - Bianchi)   Xy31Pf2GZt3
adamitrasporti\AdamiRemote12 (Francesco Grazioso) Sqw2Km678Kp
adamitrasporti\AdamiRemote14 (Damiano Bianchi)    1RgHjk54k2P
adamitrasporti\AdamiRemote15 (Andrea Giardini)    27FgJkr89Kj
adamitrasporti\AdamiRemote16 (Vojkan)             43ErfVb1QP45
adamitrasporti\AdamiRemote17 (Daniela)            1AsdGvb34Kj9u
adamitrasporti\AdamiRemote18 (Paolo)              1KFgn43Eds345
adamitrasporti\AdamiRemote19 (Michele Bonomi)     S2dU2Km975Kw
adamitrasporti\AdamiRemote20 (Monica Bonvicini)   1WsdFgn4567W
adamitrasporti\AdamiRemote21 (Roberta Maistri)    4T56Kng7854W
adamitrasporti\AdamiRemote22 (Francesco Olivieri) 5GK6Pmr9213W
adamitrasporti\AdamiRemote23 (Nicola Bonomi)      7fK6Tkd7483W
adamitrasporti\AdamiRemote24 (Vinicio Locatelli)  maverick65
adamitrasporti\AdamiRemote25 (Simone Zambaldo)    1WeFgtRj345A9
adamitrasporti\AdamiRemote26 (Umberto Pase)       Scfg!Gk45PScfg!Gk45P
adamitrasporti\AdamiRemote27 (Robert slovensko)   4TeFLtzj345X8
adamitrasporti\AdamiRemote28 (Stefano Adami)      1WerFgjk12LVb
adamitrasporti\AdamiRemote31 (Enzo Benetti)       Rghr!Us87HSwer!Vk83P
adamitrasporti\AdamiRemote32 (Oppeano)            KerT4$12Sxz6g

Also found:
  filippo / 1filippoada2
  marzia buganza / 12345678

RDS GATEWAY: rdweb.adamitrasporti.com
RDS SERVER:  RDS-SCB.ADAMITRASPORTI.LOCAL (192.168.60.8)
APPLICATION: SGA (transport management)
```

**HOW TO VERIFY THESE CREDENTIALS ARE STILL ACTIVE:**
```bash
# Test each account against RDP gateway (from LAN or VPN)
xfreerdp /v:RDS-SCB.ADAMITRASPORTI.LOCAL /u:adamitrasporti\\AdamiRemote1 /p:Wsert1Yq22 /cert:ignore

# Test via SMB authentication against DC
smbclient //192.168.60.2/IPC$ -U 'adamitrasporti\AdamiRemote1%Wsert1Yq22'

# Bulk test all accounts (script at ~/Desktop/adami-assessment/scripts/test-domain-creds.sh)
```

---

## EMERGENCY FINDING: Surveillance Camera Credentials on Open Share

```
FILE: \\192.168.1.30\DATI\IVMS - 4200 con backup\Credenziali Client Telecamere.txt
ACCESS: NULL SESSION

CREDENTIALS:
  Username: superuser
  Password: 12Sdght$jkN
  Security Q1: Your favorite game → Doom
  Security Q2: Who influences you most → DarthVader
  Security Q3: Your favorite book → Hey

SYSTEM: Hikvision iVMS-4200 surveillance platform
ALSO ON SHARE: iVMS-4200 installer + config backup ZIP
```

**HOW TO VERIFY:**
```bash
# Access Hikvision NVR/cameras via web
# The NUUO NVR at .156 might also accept these creds
curl -sk -u superuser:12Sdght\$jkN http://192.168.1.156/ 2>&1 | head -20

# Access AXIS camera with same creds
curl -sk -u superuser:12Sdght\$jkN http://192.168.1.160/mjpg/video.mjpg -o /dev/null -w "%{http_code}"
curl -sk -u root:12Sdght\$jkN http://192.168.1.160/mjpg/video.mjpg -o /dev/null -w "%{http_code}"

# Extract iVMS config backup for more camera IPs and credentials
# File: \\192.168.1.30\DATI\IVMS - 4200 con backup\Configurazione IVMS-4200.zip
```

---

## EMERGENCY FINDING: VPN CA Private Key on Open Share

```
FILE: \\192.168.1.30\DATI\OpenVpn Giuseppe Prova\ca.key
ACCESS: NULL SESSION

This is the CERTIFICATE AUTHORITY PRIVATE KEY for the OpenVPN infrastructure.
With this key, anyone can:
├── Generate valid VPN client certificates for ANY user
├── Impersonate the VPN server (MITM all VPN traffic)
├── Create backdoor VPN accounts that bypass all access controls
└── Sign certificates that the pfSense VPN server will trust

Also on share:
├── ca.crt           — CA certificate (public)
├── ta.key           — TLS auth key (shared secret)
├── techpagiuseppe1.key — Client private key for user Giuseppe
├── techpagiuseppe1.crt — Client certificate for user Giuseppe
└── BianchiGiuseppeTechpa1.ovpn — Full VPN config
```

**HOW TO VERIFY CA KEY IS THE REAL ONE:**
```bash
# Compare CA cert modulus on share vs what the VPN server presents
openssl x509 -in ca.crt -noout -modulus | md5sum
openssl rsa -in ca.key -noout -modulus | md5sum
# If both MD5 match → this IS the CA key

# Generate a rogue VPN certificate (DO NOT DO THIS — just documenting the risk)
# openssl req -new -key rogue.key -out rogue.csr -subj "/CN=rogueuser"
# openssl x509 -req -in rogue.csr -CA ca.crt -CAkey ca.key -out rogue.crt -days 3650
```

---

## EMERGENCY FINDING: MySQL Credentials on Open Share

```
FILE: \\192.168.1.30\DATI\pw Simone Mysql.txt
ACCESS: NULL SESSION

Username: simone
Password: wErFvbn$_2
```

**HOW TO INVESTIGATE:**
```bash
# Find MySQL servers on the network
sudo nmap -sS -n -p 3306 --open 192.168.1.0/24 192.168.60.0/24

# Test credentials against found MySQL servers
mysql -h <IP> -u simone -p'wErFvbn$_2' -e "SHOW DATABASES;"

# The SGA application likely uses this database
# Check RDS-SCB server (192.168.60.8) and SGA server (192.168.60.6)
```

---

## INVESTIGATION: cassaAdami (Cash Register Software)

### What It Is
cassaAdami is custom cash register / POS software (PE32 executable, GUI). Multiple versions exist on the DATI share, actively evolving (Cassa.exe from 2014 through cassaAdami NewSafe8sec3sec.exe from April 2025).

### Integrity Check

SHA256 baselines captured 2026-05-28:
```
8ef536007ad0129dc1b7151d59e1da6779545e3a75c4ddef7b83ecbc84d908eb  cassaAdami Last.exe
9bf09e20753ccee756a79e39054a515fafe6a5747ddd0afe55d41f5a817a6436  cassaAdami NewSafe8sec3sec.exe
f280b7557046b707df205c2e395a501602c478312314e9a99220894bda0b8d26  cassaAdami NewSafe8sec.exe
f4c5fa76ad15e2133292a97b09bbcd948c0cb66f5e1e31dc66dc684cebf4f393  cassaAdami NewSafe.exe
5fd8fec51c132451423a234f289b1b3a965e4ffd3f171c560273ef09c0aeb8e7  Cassa.exe
d1880beaa1ca45ca3d7152cac856b289ad3b4bd309dafb1dda7a448154f76cbd  cassaTceRelayUSBnew.exe
```

### Suspicious Indicators Found
- All cassaAdami variants contain `txtPassword` string — handles password input
- `Cassa.exe` v1.7.0 shows `&Password:` label and `comando serratura` (lock command) — controls physical door lock
- All are PE32 (32-bit), no code signing, no version info embedded
- Adobe XAP metadata present in all — built with a visual form designer
- **The DATI share is writable** — anyone on the LAN could replace these executables with trojaned versions

### How to Investigate Further
```bash
# 1. Check if the same executable runs on POS terminals (.42, .45)
# Connect to .42 or .45 and compare hashes

# 2. Check the Access databases for transaction integrity
# DB PROGRAMMI\cassa.mdb is the live database (lock file from TODAY)
# Download and inspect:
smbclient //192.168.1.30/DATI -N -c 'cd "DB PROGRAMMI"; get cassa.mdb /tmp/cassa.mdb'
# Open with mdbtools:
sudo apt install mdbtools
mdb-tables /tmp/cassa.mdb
mdb-export /tmp/cassa.mdb <table_name>

# 3. Check for unauthorized modifications
# Compare timestamps — if an exe was modified between ransomware date (2022-04-08)
# and now without a corresponding IT change, it may be compromised

# 4. Monitor the share for live modifications
inotifywait -m -r /mnt/adami/dati --format '%T %w %f %e' --timefmt '%Y-%m-%d %H:%M:%S'

# 5. Static analysis (safe — no execution)
strings cassaAdami*.exe | grep -iE 'connect|server|database|sql|password|http|ftp|tcp|socket|cmd|shell|exec|download'
```

---

## INVESTIGATION: Live Access Databases

### What's There
```
\\192.168.1.30\DATI\DB PROGRAMMI\
├── adami.mdb      107 MB  (LIVE — lock file from TODAY 13:02)
├── adami_o.mdb    174 MB  (LIVE — lock file from TODAY 12:29)
├── cassa.mdb        2.5 MB (LIVE — lock file from TODAY 09:51)
├── bolle.mdb        6.8 MB (last modified 2026-05-15)
├── ordini.mdb       2.4 MB (last modified 2022-08-23)
├── Note.mdb         320 KB (last modified 2014-09-18)
└── Multiple backups (adami - Copia*.mdb)
```

### How to Investigate
```bash
# Install Access database tools
sudo apt install mdbtools

# Download a backup (not the live file — don't disrupt operations)
smbclient //192.168.1.30/DATI -N -c 'cd "DB PROGRAMMI"; get "adami - Copia (2).mdb" /tmp/adami-backup.mdb'

# List all tables
mdb-tables -1 /tmp/adami-backup.mdb

# Export specific tables
mdb-export /tmp/adami-backup.mdb Users
mdb-export /tmp/adami-backup.mdb Clienti
mdb-export /tmp/adami-backup.mdb Fatture

# Search for credentials in the database
mdb-tables -1 /tmp/adami-backup.mdb | while read t; do
  mdb-export /tmp/adami-backup.mdb "$t" 2>/dev/null | grep -iE 'password|pwd|pass|credential|secret|token' && echo "  ^ found in table: $t"
done
```

---

## INVESTIGATION: Omron PLCs (.151, .194)

### How to Access
```bash
# FTP to PLC (may accept anonymous or default creds)
ftp 192.168.1.151
# Try: anonymous / (blank), admin / admin, ADMIN / ADMIN

# CJ2M (.194) has FINS protocol on port 9600 and EtherNet/IP on 44818
# FINS = Factory Interface Network Service — Omron proprietary
# EtherNet/IP = Common Industrial Protocol

# Read PLC status using Python (pycomm3 library)
pip install pycomm3
python3 -c "
from pycomm3 import CIPDriver
with CIPDriver('192.168.1.194') as plc:
    print(plc.get_plc_name())
    print(plc.get_plc_info())
"
```

### What to Look For
- Unauthorized program modifications (compare ladder logic to last known-good backup)
- Unexpected outputs being activated
- Timer/counter values outside normal ranges
- Any network connections to unusual IPs from the PLC

### Risk Assessment
```
If an attacker modifies PLC logic:
├── Physical process disruption (manufacturing line, conveyor, sorting)
├── Safety system bypass
├── Product damage or loss
├── Environmental or physical safety incidents
└── No authentication required — FINS and EtherNet/IP have no auth by default
```

---

## INVESTIGATION: Phoenix Contact HMI/SCADA (.152)

### How to Access
```bash
# Web HMI (SpiderControl)
xdg-open http://192.168.1.152/

# Modbus TCP (port 502) — no authentication
# Read holding registers:
pip install pymodbus
python3 -c "
from pymodbus.client import ModbusTcpClient
client = ModbusTcpClient('192.168.1.152')
client.connect()
result = client.read_holding_registers(0, 10, slave=1)
print(result.registers)
client.close()
"
```

### What to Look For
- Unexpected register values
- HMI screens showing abnormal process states
- Web interface access logs (if any)
- Network connections from the controller to unexpected IPs

---

## INVESTIGATION: Surveillance System

### Access Points
```bash
# AXIS 215 PTZ Camera (.160) — firmware from 2009
xdg-open http://192.168.1.160/
# Try creds: root/root, root/pass, admin/admin, superuser/12Sdght\$jkN

# RTSP stream (may work without auth):
vlc rtsp://192.168.1.160/mpeg4/media.amp
vlc rtsp://192.168.1.160/axis-media/media.amp

# NUUO NVR (.156) — known critical CVEs
xdg-open http://192.168.1.156/
# Try creds: admin/admin, admin/123456, superuser/12Sdght\$jkN

# Hikvision iVMS-4200 config
# Download and extract:
smbclient //192.168.1.30/DATI -N -c 'cd "IVMS - 4200 con backup"; get "Configurazione IVMS-4200.zip" /tmp/ivms-config.zip'
unzip /tmp/ivms-config.zip -d /tmp/ivms-config/
# Look for device list, camera IPs, additional credentials
grep -riE 'password|credential|ip|address' /tmp/ivms-config/
```

### What to Look For
- Camera footage gaps (evidence of tampering)
- Unknown users in NVR access logs
- Cameras pointing in unexpected directions (PTZ manipulation)
- NVR recording status — is it actually recording?
- Network connections from NVR to external IPs

---

## INVESTIGATION: Lenovo NAS (.6) — 80+ Shares

### How to Access
```bash
# Shares are LISTED via null session but CONTENTS require auth
smbclient -L //192.168.1.6/ -N

# Try common NAS credentials:
smbclient //192.168.1.6/ITfolder -U admin -p 'admin'
smbclient //192.168.1.6/ITfolder -U admin -p 'password'
smbclient //192.168.1.6/ITfolder -U admin -p ''

# Try domain credentials from the RD SGA ADAMI.txt file:
smbclient //192.168.1.6/ITfolder -U 'adamitrasporti\AdamiRemote1' -p 'Wsert1Yq22'

# Web interface:
xdg-open http://192.168.1.6/
```

### Critical Shares to Investigate
```
ITfolder            — IT department files, configs, tools
BackupServer        — Backup repository
ZimbraBackup        — Email server backup (Zimbra)
Amministrazione Adami — Financial/admin data
Documentale         — Document management system
filmati             — Videos (surveillance footage?)
D2D                 — Disk-to-disk backup?
COMMERCIALE         — Commercial/sales data
TruckController     — Fleet management data
```

---

## INVESTIGATION: Remote Desktop Services

### How to Access
```bash
# Internal (from LAN or VPN):
xfreerdp /v:192.168.60.8 /u:adamitrasporti\\AdamiRemote1 /p:Wsert1Yq22 /cert:ignore

# External (via RD Web):
xdg-open https://rdweb.adamitrasporti.com/rdweb
# Credentials from RD SGA ADAMI.txt

# SGA application launches via RemoteApp
# RDP file: SGANuovoServer.rdp
# Gateway: rdweb.adamitrasporti.com
# Server: RDS-SCB.ADAMITRASPORTI.LOCAL (192.168.60.8)
```

### What to Look For
- Login history (Event Viewer → Security → 4624/4625)
- Active sessions from unexpected users
- RemoteApp usage logs
- Check if any AdamiRemote accounts have elevated privileges
- Password age for all 32 accounts — were they ever changed?

---

## INVESTIGATION: Network Switch Configuration

### How to Access
```bash
# Netgear GS324T (.25)
xdg-open http://192.168.1.25/
# Default: admin / password (not confirmed — 404 on standard paths)

# Netgear GS348T (.26)
xdg-open http://192.168.1.26/

# D-Link DGS-1210 (.158)
xdg-open http://192.168.1.158/web/login.asp
# Default: admin / (blank) or admin / admin
```

### What to Look For
- VLAN configuration — are VLANs actually configured?
- Port mirroring — is anyone tapping traffic?
- MAC address tables — map physical ports to devices
- Spanning tree — any unexpected topology changes
- Firmware versions — are they current?

---

## HOW TO VERIFY: Can cassaAdami Be Trojaned?

```bash
# 1. The DATI share is writable via null session
# Test write access (create and immediately delete a test file):
smbclient //192.168.1.30/DATI -N -c 'put /dev/null .writetest; del .writetest'

# 2. If writable, an attacker could:
#    a) Replace cassaAdami.exe with a trojan
#    b) The trojan runs on all POS terminals next time they launch
#    c) The trojan could capture credit card data, modify transactions, or pivot

# 3. Verify current integrity:
# Compare hashes against known-good backups
# Check digital signatures (likely unsigned — no code signing found)
# Compare file sizes against the version history:
#   Cassa.exe        647168  2014-04-03 (original)
#   cassaAdami Last  696320  2024-09-27
#   cassaAdami NewSafe 696320 2025-04-09
#   cassaAdami NewSafe8sec 696320 2025-04-11
#   cassaAdami NewSafe8sec3sec 696320 2025-04-11
# All NewSafe variants are exactly 696320 bytes — suspicious uniform size
```

---

## PERSISTENT ACCESS SETUP (for remote investigation)

### VPN Connection (works from anywhere)
```bash
# Split tunnel (recommended — keeps your internet working)
sudo ~/Desktop/adami-assessment/vpn/connect-adami-vpn.sh

# Routes added: 192.168.1.0/24, 192.168.6.0/24, 192.168.60.0/24, 192.168.192.0/24
# You'll be prompted for VPN username and password
```

### Quick Access Toolkit
```bash
# Master toolkit with reachability check and quick actions
~/Desktop/adami-assessment/scripts/adami-access.sh

# Mount all available SMB shares
sudo ~/Desktop/adami-assessment/scripts/mount-shares.sh
```

### All Web Interfaces
```
~/Desktop/adami-assessment/web-shortcuts/
├── 18 .desktop files — double-click to open in browser
└── Covers: NAS, cameras, NVR, switches, UPS, printers, HMI, DCs, VPN
```

---

## TOTAL CREDENTIALS FOUND IN THIS ASSESSMENT

| Source | Type | Count | Location |
|--------|------|-------|----------|
| RD SGA ADAMI.txt | Domain accounts (RDP) | 32 | \\\\192.168.1.30\DATI\RDP\ |
| pw Simone Mysql.txt | MySQL credentials | 1 | \\\\192.168.1.30\DATI\ |
| Credenziali Client Telecamere.txt | Surveillance admin | 1 | \\\\192.168.1.30\DATI\IVMS\ |
| OpenVPN CA key | VPN CA private key | 1 (generates unlimited) | \\\\192.168.1.30\DATI\OpenVpn\ |
| OpenVPN Giuseppe | VPN client cert+key | 1 | \\\\192.168.1.30\DATI\OpenVpn\ |
| Wi-Fi PSKs (PCFRANCESCA) | Wi-Fi passwords | 2 | Doc 17 |
| AnyDesk hash (PCFRANCESCA) | Remote desktop | 1 | Doc 17 |
| VPN cert francescav (PCFRANCESCA) | VPN client cert | 1 | Doc 17 |
| Windows Credential Manager | Various SSO tokens | 5 | Doc 17 |
| Browser databases | Saved passwords | 7 DBs | Doc 17 |
| sandro account | Local admin, no password | 1 | Doc 12 |
| ASPNET account | Local user, no password | 1 | Doc 12 |
| File server .6.1 | SMB credentials | 1 (adminada) | IT-provided |
| **TOTAL** | | **55+ credentials** | |
