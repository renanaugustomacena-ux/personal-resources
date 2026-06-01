# 39 — Network Traffic Analysis, Network Detection and Response (NDR), and Deep Packet Inspection

---

## Indice

1. [Fondamenti Network Traffic Analysis](#1-fondamenti-network-traffic-analysis)
2. [Strumenti di Cattura e Analisi](#2-strumenti-di-cattura-e-analisi)
3. [Network Detection and Response NDR](#3-network-detection-and-response-ndr)
4. [Protocolli e Analisi Specifica](#4-protocolli-e-analisi-specifica)
5. [Deep Packet Inspection](#5-deep-packet-inspection)
6. [Zeek Deep Dive](#6-zeek-deep-dive)
7. [Suricata per Network Security](#7-suricata-per-network-security)
8. [Threat Detection Patterns](#8-threat-detection-patterns)
9. [Encrypted Traffic Analysis](#9-encrypted-traffic-analysis)
10. [Laboratorio](#10-laboratorio)
11. [Arkime — Cattura e Indicizzazione Pacchetti](#11-arkime--cattura-e-indicizzazione-pacchetti)
12. [NetFlow sFlow IPFIX — Analisi Avanzata dei Flussi](#12-netflow-sflow-ipfix--analisi-avanzata-dei-flussi)
13. [NDR nel Cloud — AWS Azure GCP](#13-ndr-nel-cloud--aws-azure-gcp)
14. [Mappatura MITRE ATT&CK per Detection di Rete](#14-mappatura-mitre-attck-per-detection-di-rete)
15. [eBPF e XDP per Monitoraggio di Rete](#15-ebpf-e-xdp-per-monitoraggio-di-rete)

---

## 1. Fondamenti Network Traffic Analysis

### 1.1 Superficie d'Attacco per Layer OSI

Network traffic analysis operates across the entire OSI stack. Understanding where threats manifest at each layer determines which inspection technique and tooling applies.

| OSI Layer | Attack Surface | Example Attacks | Capture Method |
|-----------|---------------|-----------------|----------------|
| L1 Physical | Cable taps, rogue devices | Vampire taps, rogue APs, HID implants | Physical audit, RF scanning |
| L2 Data Link | ARP, MAC, VLAN | ARP spoofing, MAC flooding, VLAN hopping, STP manipulation | SPAN port mirroring, tap |
| L3 Network | IP, ICMP, routing | IP spoofing, ICMP tunneling, BGP hijacking, fragmentation attacks | NetFlow/sFlow, pcap |
| L4 Transport | TCP, UDP | SYN floods, TCP reset attacks, UDP amplification, port scanning | pcap, flow data |
| L5 Session | RPC, NetBIOS, SOCKS | Session hijacking, NTLM relay, SOCKS proxy abuse | Full packet capture |
| L6 Presentation | TLS/SSL, encoding | Downgrade attacks, certificate spoofing, encoding bypass | TLS metadata, JA3 |
| L7 Application | HTTP, DNS, SMB, SMTP | SQLi, XSS, DNS tunneling, C2 over HTTP, phishing payloads | DPI, protocol dissection |

The critical insight: most enterprise detection focuses on L3-L4 (firewalls, flow analysis) and L7 (IDS/IPS signatures), leaving L2 and L5-L6 as a blind spot that adversaries actively exploit.

### 1.2 Fondamenti Packet Capture

Traffic capture is the foundational capability for all network security analysis. Three primary methods exist for getting packets off the wire.

**Promiscuous Mode**

A network interface in promiscuous mode processes all frames arriving on the wire segment, not just those destined for its own MAC address. On switched networks, this only captures broadcast/multicast traffic and traffic destined for the host unless combined with port mirroring.

```bash
# Enable promiscuous mode on Linux
ip link set eth0 promisc on
# Verify
ip link show eth0 | grep PROMISC
```

**SPAN Ports (Switched Port Analyzer)**

SPAN mirrors traffic from one or more source ports/VLANs to a designated monitor port. The monitoring port connects to the capture system.

```
! Cisco IOS SPAN configuration
monitor session 1 source interface Gi0/1 - Gi0/24
monitor session 1 destination interface Gi0/48
monitor session 1 filter vlan 10, 20, 30

! Verify
show monitor session 1
```

Limitations of SPAN:

- SPAN ports saturate under load — a mirroring session of 24x1Gbps ports to a single 1Gbps destination drops packets
- CPU impact on the switch — mirroring is not free
- SPAN may not capture errored frames, Layer 2 control protocols (STP, CDP), or VLAN tags depending on switch vendor and configuration
- Bidirectional mirroring of a full-duplex port can oversubscribe the monitor port at 2x the port speed

**TAP Devices (Test Access Points)**

TAPs are passive hardware devices inserted inline on a network segment that copy traffic to a monitoring port without introducing delay, packet loss, or a point of failure.

Types of TAPs:

| TAP Type | Behavior | Failure Mode | Use Case |
|----------|----------|--------------|----------|
| Passive copper TAP | Splits electrical signal optically | Link stays up (no electronics) | 10/100/1000 copper links |
| Passive fiber TAP | Splits light via beam splitter | No failure mode possible | Fiber backbone monitoring |
| Active/Regeneration TAP | Regenerates signal to monitor ports | Bypass relay on power failure | High-speed 10G/40G/100G |
| Aggregation TAP | Merges bidirectional traffic to one output | Bypass relay | Feeding single-NIC sensors |

TAPs are always preferred over SPAN for security-critical monitoring because they guarantee no packet loss, no timing alterations, and no switch CPU dependency.

### 1.3 Capture vs Flow Data — pcap vs NetFlow/sFlow/IPFIX

Two fundamentally different data types underpin traffic analysis, and confusing their capabilities is a common operational mistake.

**Full Packet Capture (pcap)**

Captures the complete packet including all headers and payload. Stored in pcap (libpcap) or pcapng format. Provides maximum forensic value — you can reconstruct files, read cleartext credentials, follow protocol conversations, extract malware payloads.

Cost: 1 Gbps sustained = ~450 GB/hour of raw pcap. At 10 Gbps, that is ~4.5 TB/hour, or ~108 TB/day. Storage becomes the dominant cost and the primary engineering challenge.

**Flow Data (NetFlow v5/v9, sFlow, IPFIX)**

Flow records summarize conversations as metadata tuples: source/destination IP, ports, protocol, byte/packet counts, timestamps, TCP flags, AS numbers. No payload is captured.

| Attribute | pcap | NetFlow v9/IPFIX | sFlow |
|-----------|------|-----------------|-------|
| Payload visibility | Full | None | Sampled headers |
| Storage cost per Gbps/day | ~10 TB | ~1-5 GB | ~0.5-2 GB |
| Forensic value | Maximum | Metadata only | Limited |
| Legal sensitivity | High (content) | Lower (metadata) | Lower |
| Latency to analysis | Post-capture | Near real-time | Real-time |
| Sampling | None (full capture) | Optional | 1-in-N packet sampling |
| Protocol detail | Complete | 5-tuple + counters | Sampled packet header |

**Pragmatic architecture:** Use flow data for baseline visibility, anomaly detection, and capacity planning across the entire network. Deploy full packet capture at strategic chokepoints — DMZ ingress/egress, inter-segment boundaries, and high-value asset segments — where forensic fidelity is required.

### 1.4 Storage e Retention

Retention planning for packet capture requires balancing forensic requirements against storage economics.

**Sizing formula:**

```
Daily storage (bytes) = average_throughput_bps × 86400 / 8
```

| Link Speed | Daily pcap (100% utilization) | 30-Day Retention |
|-----------|------------------------------|------------------|
| 100 Mbps | ~1.08 TB | ~32 TB |
| 1 Gbps | ~10.8 TB | ~324 TB |
| 10 Gbps | ~108 TB | ~3.24 PB |

Real-world utilization averages 20-40% of link capacity, reducing these figures significantly but still producing substantial volumes. Techniques to manage storage:

- **Rolling capture:** Circular buffer that overwrites oldest data when disk fills (most packet capture appliances support this natively)
- **Tiered retention:** Hot storage (NVMe/SSD) for 24-72 hours of full pcap, warm storage (HDD arrays) for 7-30 days, cold storage (object store) for flow data extending to 90-365 days
- **Selective capture:** BPF filters to exclude known-good high-volume traffic (video streaming, CDN, Windows Update) while capturing everything else
- **Compression:** pcap compresses well with zstd/lz4, typically achieving 2:1 to 4:1 ratios on mixed traffic

### 1.5 Considerazioni Legali

Capturing network traffic intersects with multiple legal frameworks depending on jurisdiction.

**EU/GDPR (Regolamento UE 2016/679):** Packet capture containing personal data (email content, browsing history, authentication data) falls under GDPR processing. Lawful basis typically relies on Art. 6(1)(f) — legitimate interest for network security — but requires a documented Data Protection Impact Assessment (DPIA), data minimization (capture only what is necessary), and defined retention periods.

**Italian D.Lgs. 196/2003 (Codice Privacy) + D.Lgs. 101/2018:** Italian privacy law supplements GDPR. Employee monitoring requires compliance with Art. 4 of the Workers' Statute (L. 300/1970), which mandates union agreement or authorization from the Ispettorato Territoriale del Lavoro before deploying monitoring tools that could track worker activity.

**Key operational requirements:**

- Document the legal basis before deploying capture infrastructure
- Implement access controls limiting who can access captured content
- Define and enforce retention periods with automated purge
- Anonymize or pseudonymize captured data where feasible
- Maintain audit logs of all access to captured traffic
- Notify employees via acceptable use policy that network traffic may be monitored for security purposes

---

## 2. Strumenti di Cattura e Analisi

### 2.1 tcpdump — Cattura da Linea di Comando

tcpdump is the fundamental packet capture tool on Unix-like systems, using libpcap for packet acquisition and Berkeley Packet Filter (BPF) for kernel-level filtering. Every network security professional must be fluent in tcpdump syntax.

**Basic capture operations:**

```bash
# Capture on interface eth0, write to file
tcpdump -i eth0 -w /tmp/capture.pcap

# Capture with timestamp precision (nanosecond), snaplen, and packet count
tcpdump -i eth0 -w /tmp/capture.pcap --time-stamp-precision=nano -s 0 -c 10000

# Read and display a pcap file
tcpdump -r /tmp/capture.pcap -nn -tttt

# Capture on all interfaces
tcpdump -i any -w /tmp/all_interfaces.pcap
```

**BPF expression syntax — complete reference:**

BPF expressions use primitives combined with logical operators (`and`, `or`, `not`) and grouped with parentheses.

```bash
# Protocol filters
tcpdump -i eth0 tcp
tcpdump -i eth0 udp
tcpdump -i eth0 icmp
tcpdump -i eth0 arp

# Host filters
tcpdump -i eth0 host 192.168.1.100
tcpdump -i eth0 src host 10.0.0.5
tcpdump -i eth0 dst host 203.0.113.50

# Port filters
tcpdump -i eth0 port 443
tcpdump -i eth0 src port 53
tcpdump -i eth0 portrange 8000-9000

# Network filters
tcpdump -i eth0 net 10.0.0.0/8
tcpdump -i eth0 src net 172.16.0.0/12

# TCP flag filters (critical for attack detection)
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0'          # SYN packets
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-ack) == tcp-syn'  # SYN only (no SYN-ACK)
tcpdump -i eth0 'tcp[tcpflags] & tcp-rst != 0'          # RST packets
tcpdump -i eth0 'tcp[tcpflags] & tcp-fin != 0'          # FIN packets
tcpdump -i eth0 'tcp[13] == 0'                           # NULL scan (no flags)
tcpdump -i eth0 'tcp[13] == 0x29'                        # XMAS scan (FIN+PSH+URG)

# Combined expressions — real-world examples
# Capture DNS queries to non-standard resolvers
tcpdump -i eth0 'dst port 53 and not dst host 10.0.0.1 and not dst host 10.0.0.2'

# Capture HTTP POST requests (byte offset inspection)
tcpdump -i eth0 'tcp dst port 80 and tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x504f5354'

# Capture large DNS responses (potential tunneling)
tcpdump -i eth0 'udp src port 53 and udp[10:2] > 512'

# Capture ICMP type 8 (echo request) with large payload (potential exfiltration)
tcpdump -i eth0 'icmp[0] == 8 and len > 100'
```

**Advanced usage patterns:**

```bash
# Rotating captures — new file every 100MB, keep last 50 files
tcpdump -i eth0 -w /capture/traffic.pcap -C 100 -W 50 -z gzip

# Capture with ring buffer — time-based rotation every 3600 seconds
tcpdump -i eth0 -w /capture/traffic.pcap -G 3600 -Z root

# Capture only packet headers (first 96 bytes) to save storage
tcpdump -i eth0 -s 96 -w /capture/headers_only.pcap

# Display hex and ASCII dump
tcpdump -r capture.pcap -XX -c 5

# Extract unique destination IPs from a capture
tcpdump -r capture.pcap -nn 'tcp' | awk '{print $5}' | cut -d. -f1-4 | sort -u
```

### 2.2 Wireshark — Analisi Visuale Avanzata

Wireshark provides deep protocol dissection with a powerful display filter language that operates on decoded protocol fields — fundamentally different from tcpdump's BPF which works on raw bytes.

**Display filter syntax (distinct from capture filters):**

```
# Protocol filters
http
dns
tls
smb2
kerberos

# Field comparison operators
ip.addr == 192.168.1.100
ip.src == 10.0.0.0/8
tcp.port == 443
tcp.dstport in {80, 443, 8080, 8443}
frame.len > 1500
http.response.code >= 400

# String matching
http.host contains "evil"
http.request.uri matches "\\.(exe|dll|scr|ps1)$"
dns.qry.name contains "tunnel"
tls.handshake.extensions_server_name == "malicious.com"

# Logical operators
ip.src == 10.0.0.50 && tcp.dstport == 445
(http.request.method == "POST") || (http.request.method == "PUT")
!arp && !dns && !icmp

# TCP analysis filters (invaluable for troubleshooting and attack detection)
tcp.analysis.retransmission
tcp.analysis.duplicate_ack
tcp.analysis.zero_window
tcp.analysis.lost_segment
tcp.analysis.out_of_order

# TLS-specific filters
tls.handshake.type == 1                          # ClientHello
tls.handshake.type == 2                          # ServerHello
tls.handshake.type == 11                         # Certificate
tls.handshake.extensions.supported_versions == 0x0304  # TLS 1.3

# DNS analysis
dns.flags.response == 1 && dns.flags.rcode != 0  # Failed DNS responses
dns.qry.type == 16                                # TXT record queries
dns.resp.len > 512                                # Large DNS responses

# SMB/CIFS
smb2.cmd == 5                                     # Create (file open)
smb2.cmd == 8                                     # Read
smb2.cmd == 9                                     # Write
ntlmssp.auth.username                             # NTLM auth events
```

**Follow Stream analysis:** Right-click any packet in a TCP conversation and select "Follow > TCP Stream" to reconstruct the full conversation. This immediately reveals HTTP request/response pairs, SMTP email content, cleartext credentials, and C2 command sequences. Available for TCP, UDP, TLS (if keys loaded), and HTTP/2.

**Expert Info (Analyze > Expert Information):** Wireshark's expert system flags protocol anomalies categorized by severity — Chat, Note, Warn, Error. Critical indicators:

- TCP Retransmissions above baseline suggest network congestion or packet manipulation
- Malformed packets indicate fuzzing, exploit attempts, or tunneling
- Zero window conditions reveal DoS or resource exhaustion
- Out-of-order segments can indicate packet injection or race conditions

**IO Graphs (Statistics > IO Graphs):** Plot packet rate, byte rate, or filtered traffic over time. Overlay multiple filters to correlate events — e.g., plot DNS queries alongside HTTP connections to visualize DNS-based C2 beaconing followed by payload retrieval.

**Conversation tracking (Statistics > Conversations):** Shows top talkers per protocol layer (Ethernet, IPv4, TCP, UDP). Immediately highlights unexpected internal hosts communicating externally, high-volume sessions between internal hosts (lateral movement), or single hosts connecting to many destinations (scanning).

### 2.3 tshark — Analisi Scriptata

tshark is Wireshark's command-line equivalent, essential for scripted analysis pipelines and processing pcap files on headless servers.

```bash
# Extract HTTP host headers and URIs from pcap
tshark -r capture.pcap -Y "http.request" \
  -T fields -e ip.src -e http.host -e http.request.uri -E separator=,

# DNS query analysis — extract all queried domains
tshark -r capture.pcap -Y "dns.flags.response == 0" \
  -T fields -e ip.src -e dns.qry.name | sort | uniq -c | sort -rn | head -50

# TLS SNI extraction — identify all TLS destinations by hostname
tshark -r capture.pcap -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e ip.dst -e tls.handshake.extensions_server_name

# Connection statistics
tshark -r capture.pcap -q -z conv,tcp

# Protocol hierarchy statistics
tshark -r capture.pcap -q -z io,phs

# Export HTTP objects (files downloaded over HTTP)
tshark -r capture.pcap --export-objects http,/tmp/http_objects/

# Extract all x509 certificates from TLS handshakes
tshark -r capture.pcap -Y "tls.handshake.type == 11" \
  -T fields -e tls.handshake.certificate \
  -E separator=, > certificates.txt
```

**tshark + jq for JSON pipeline analysis:**

```bash
# Export to JSON and extract specific fields with jq
tshark -r capture.pcap -Y "http.request" -T json | \
  jq -r '.[] | .["_source"].layers | 
    "\(.ip["ip.src"])|\(.http["http.host"])|\(.http["http.request.method"])|\(.http["http.request.uri"])"'

# Analyze DNS response times
tshark -r capture.pcap -Y "dns.flags.response == 1" -T json | \
  jq '[.[] | .["_source"].layers.dns["dns.time"] | tonumber] | 
    {min: min, max: max, avg: (add / length)}'

# Group connections by destination country (requires GeoIP)
tshark -r capture.pcap -Y "tcp.flags.syn == 1 && tcp.flags.ack == 0" \
  -T json | jq -r '.[] | .["_source"].layers.ip["ip.geoip.dst_country"]' | \
  sort | uniq -c | sort -rn
```

### 2.4 NetworkMiner — Estrazione Artefatti

NetworkMiner is a passive network forensics tool that reconstructs artifacts from pcap files:

- Extracts transferred files (images, documents, executables) and reconstructs them from packet data
- Identifies operating systems via passive OS fingerprinting (TCP window size, TTL, options)
- Extracts credentials from cleartext protocols (HTTP Basic, FTP, SMTP, POP3, Telnet)
- Builds host inventory with hostnames, MAC addresses, open ports
- Parses DNS queries to build domain resolution timeline
- Extracts images inline for rapid visual triage

Usage workflow: load a pcap, switch to the "Files" tab to see extracted objects, check "Credentials" tab for cleartext auth, review "Hosts" tab for network mapping.

---

## 3. Network Detection and Response NDR

### 3.1 Architettura NDR

NDR platforms provide continuous network visibility with automated threat detection and response. The architecture comprises three layers.

```
 ┌─────────────────────────────────────────────────────────┐
 │                  RESPONSE LAYER                         │
 │  Automated containment ─ Firewall API integration       │
 │  SOAR playbooks ─ Analyst workflows ─ Case management   │
 ├─────────────────────────────────────────────────────────┤
 │                  ANALYSIS ENGINE                         │
 │  Signature matching ─ Behavioral baseline               │
 │  ML anomaly detection ─ Protocol analysis               │
 │  Encrypted traffic analytics ─ Threat intel correlation  │
 ├─────────────────────────────────────────────────────────┤
 │                  SENSOR LAYER                            │
 │  Network TAPs ─ SPAN ports ─ Cloud VPC mirrors          │
 │  pcap ingestion ─ Flow collectors ─ Proxy logs          │
 └─────────────────────────────────────────────────────────┘
         |              |                |
    ┌────┴────┐   ┌────┴────┐    ┌─────┴─────┐
    │ North/  │   │ East/   │    │  Cloud    │
    │ South   │   │ West    │    │ Workloads │
    │ Traffic │   │ Traffic │    │ VPC/VNET  │
    └─────────┘   └─────────┘    └───────────┘
```

**Sensor placement strategy:**

- **North-South (perimeter):** TAP/SPAN on internet egress captures all external communications. Traditional deployment, but misses lateral movement entirely.
- **East-West (internal):** TAP/SPAN on inter-segment links, core switch uplinks, and datacenter spine. This is where post-compromise activity occurs — lateral movement, privilege escalation pivots, internal reconnaissance. Requires significantly more sensor capacity than perimeter-only.
- **Cloud:** VPC Traffic Mirroring (AWS), Virtual Network TAP (Azure), Packet Mirroring (GCP). Each cloud provider has distinct limitations on mirroring throughput and supported instance types.

### 3.2 Piattaforme NDR

**Open-Source NDR Stack:**

| Component | Role | Strength |
|-----------|------|----------|
| Zeek | Protocol analysis, metadata generation | Deep protocol logs, scriptable detection |
| Suricata | Signature-based IDS/IPS, protocol detection | Fast pattern matching, EVE JSON output |
| Arkime (Moloch) | Full packet capture and retrieval | Indexed pcap storage, session search |
| Elasticsearch + Kibana | Log storage, visualization, hunting | Scalable search, dashboard creation |

**Commercial NDR Platforms:**

| Platform | Detection Approach | Differentiator |
|----------|-------------------|----------------|
| Corelight | Zeek-based with ML enrichment | Enterprise Zeek with cloud sensors, Suricata integration |
| ExtraHop Reveal(x) | Real-time wire-data analytics | Decrypts internal TLS via key forwarding, auto-discovery |
| Darktrace | Unsupervised ML, self-learning AI | No baseline training period, autonomous response |
| Vectra AI | Behavioral detection, AI-driven | Attack signal intelligence, cloud coverage, prioritized alerts |
| Cisco Secure Network Analytics (Stealthwatch) | NetFlow-based analytics | Integrates with Cisco ecosystem, encrypted traffic analytics |

### 3.3 Approcci di Detection

**Signature-Based Detection:** Pattern matching against known attack indicators. Suricata/Snort rules match byte patterns, protocol fields, flow characteristics. Strengths: precise, fast, low false positives for known threats. Weakness: zero detection capability for novel attacks.

**Behavioral/Baseline Detection:** Establish normal behavior profiles per host, user, subnet, and application, then alert on deviations. Effective for: anomalous data volumes, unusual protocol usage, off-hours activity, communication with new external destinations. Requires a learning period and generates false positives during legitimate business changes.

**Machine Learning Detection:** Supervised models trained on labeled attack/benign data (classification), unsupervised models clustering traffic to find outliers, and deep learning on raw packet/flow features. ML excels at detecting subtle beaconing, domain generation algorithms (DGAs), and encrypted C2 channels where signatures fail.

### 3.4 East-West Traffic Monitoring

East-west traffic monitoring is architecturally harder than perimeter monitoring and operationally more critical for detecting post-compromise activity.

Challenges:

- **Volume:** Internal traffic often exceeds external traffic by 10:1 or more. A single datacenter core switch may handle 40-100 Gbps aggregate.
- **Visibility:** Virtualized workloads communicating within the same hypervisor never cross a physical switch — vSwitch or kernel-level capture is required (VMware NSX, Open vSwitch mirroring, eBPF capture).
- **Baseline complexity:** Internal traffic patterns are diverse and dynamic — database replication, backup systems, management traffic, service mesh communication all create high-volume legitimate flows.
- **Encryption:** Internal TLS adoption (mTLS in microservices, TLS for database connections) reduces payload visibility for traditional IDS.

### 3.5 Encrypted Traffic Analysis — Introduzione

With 95%+ of web traffic encrypted via TLS, network security must extract detection value without decryption. Key techniques (detailed in section 9):

- **JA3/JA4 fingerprinting:** Hash the TLS ClientHello parameters to identify the client application. Malware frameworks produce distinctive fingerprints.
- **HASSH:** SSH client/server fingerprinting using key exchange parameters.
- **Certificate analysis:** Self-signed certs, expired certs, mismatched CNs, and Let's Encrypt certificates on non-web services are strong anomaly indicators.
- **Flow metadata:** Encrypted sessions still reveal timing patterns, byte volumes, and connection frequency.

---

## 4. Protocolli e Analisi Specifica

This section covers how key protocols appear on the wire and what to capture for security analysis. The attacker behavioral patterns using these protocols are covered in section 8.

### 4.1 HTTP/HTTPS — Request e Response

HTTP analysis reveals web application attacks, C2 communication, and data exfiltration.

**Wire-level structure:**

```
GET /api/v2/config?id=ae32f HTTP/1.1\r\n
Host: legitimate-cdn.com\r\n
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)...\r\n
Accept: */*\r\n
Cookie: session=base64encodedpayload\r\n
\r\n
```

**Key fields for security analysis:**

| Header/Field | Normal | Suspicious |
|-------------|--------|------------|
| User-Agent | Standard browser/app string | Empty, custom, or uncommon strings; known malware UAs |
| Host | Matches destination IP/DNS | Mismatched host header (domain fronting) |
| Content-Type | Matches actual payload | Mismatch (binary in text/plain) |
| Content-Length | Reasonable for the endpoint | Very large POST to API endpoint |
| Cookie | Session tokens | Encoded C2 commands |
| URL path | Application routes | Long base64 strings, encoded payloads |
| Response code pattern | Mixed 200/30x/40x | Exclusively 200 (C2 always succeeds) |

**Wireshark filters for HTTP analysis:**

```
http.request.method == "POST" && http.content_length > 1000000
http.response.code == 200 && http.content_type contains "octet-stream"
http.user_agent == "" || http.user_agent contains "python" || http.user_agent contains "curl"
http.request.uri contains ".php?" && ip.dst != 10.0.0.0/8
```

### 4.2 DNS — Query Patterns e Tunneling

DNS is a favored exfiltration and C2 channel because it is almost never blocked and rarely inspected.

**Normal DNS characteristics:**

- Queries to configured resolvers (usually 1-3 internal DNS servers)
- Query names matching legitimate domain patterns
- Response sizes under 512 bytes (UDP) or under 4096 bytes (EDNS0)
- TXT record queries are infrequent in normal enterprise traffic

**DNS tunneling indicators:**

| Indicator | Threshold | Rationale |
|-----------|-----------|-----------|
| Query length | > 50 characters in subdomain | Encoded data in query labels |
| Unique subdomain ratio | > 100 unique subdomains per hour to one domain | Data exfiltration encoding |
| TXT record frequency | > 10 TXT queries/min from one host | C2 response channel |
| NULL/CNAME record abuse | Any NULL queries, high CNAME volume | Uncommon record types for tunneling |
| Query entropy | Shannon entropy > 3.5 in subdomain labels | Random-looking encoded data |
| Response size | Consistently > 512 bytes | Data smuggled in responses |

**tcpdump filters for DNS anomaly capture:**

```bash
# Capture DNS to non-standard resolvers
tcpdump -i eth0 'dst port 53 and not dst host 10.0.0.1' -w dns_anomaly.pcap

# Capture large DNS responses (possible tunneling)
tcpdump -i eth0 'udp src port 53 and udp[10:2] > 512' -w dns_large.pcap

# Capture TXT record queries (byte offset for QTYPE)
tcpdump -i eth0 'udp dst port 53 and udp[10:2] = 0x0010'
```

### 4.3 SMB/CIFS — Struttura del Protocollo

SMB (Server Message Block) is the primary file-sharing protocol in Windows environments and a critical vector for lateral movement.

**SMB2/3 commands relevant to security monitoring:**

| Command (opcode) | Operation | Security Relevance |
|------------------|-----------|-------------------|
| Negotiate (0x00) | Protocol version negotiation | Downgrade attacks (SMBv1 forced) |
| Session Setup (0x01) | Authentication | Credential capture, NTLM relay |
| Tree Connect (0x03) | Share access | Mapping admin shares (C$, ADMIN$, IPC$) |
| Create (0x05) | File/pipe open | Service binary upload, named pipe access |
| Read (0x08) | File read | Data staging |
| Write (0x09) | File write | Payload delivery, lateral movement tools |
| IOCTL (0x0B) | Control operations | Named pipe transactions (PsExec) |

**Wireshark filters for SMB security analysis:**

```
smb2.tree contains "ADMIN$" || smb2.tree contains "C$" || smb2.tree contains "IPC$"
smb2.filename contains ".exe" || smb2.filename contains ".dll" || smb2.filename contains ".ps1"
ntlmssp.auth.username && ntlmssp.auth.domain
```

### 4.4 Kerberos — Ticket Analysis

Kerberos is the authentication backbone of Active Directory. Traffic analysis reveals credential attacks.

**Key Kerberos message types:**

| Message | Purpose | Attack Indicator |
|---------|---------|-----------------|
| AS-REQ (type 10) | Initial auth, request TGT | AS-REP Roasting (RC4 requested for non-standard accounts) |
| AS-REP (type 11) | TGT response | Pre-auth disabled accounts |
| TGS-REQ (type 12) | Service ticket request | Kerberoasting (many SPN requests from one account) |
| TGS-REP (type 13) | Service ticket response | Contains encrypted data for offline cracking |
| AP-REQ (type 14) | Service authentication | Ticket reuse, golden ticket usage |

**Wireshark filters:**

```
kerberos.msg_type == 10 && kerberos.etype == 23    # AS-REQ with RC4 (AS-REP Roast target)
kerberos.msg_type == 12                             # TGS-REQ (Kerberoasting candidates)
kerberos.error_code == 6                            # Principal unknown
kerberos.error_code == 24                           # Pre-auth failed (brute force)
```

### 4.5 TLS — Struttura Handshake

TLS handshake inspection is possible without decryption and reveals substantial metadata.

**ClientHello fields visible in the clear:**

- Supported cipher suites (ordered by preference)
- TLS version
- SNI (Server Name Indication) — the hostname the client is connecting to
- Supported extensions (ALPN, signature algorithms, supported groups)
- Session ID / PSK identity (TLS 1.3 resumption)

**ServerHello fields:**

- Selected cipher suite
- Selected TLS version
- Certificate chain (in TLS 1.2; encrypted in TLS 1.3)

**Certificate analysis fields:**

```
tls.handshake.certificate
x509ce.dNSName                        # Subject Alternative Names
x509af.utcTime                        # Validity period
x509af.rdnSequence                    # Subject/Issuer DN
tls.handshake.sig_hash_alg            # Signature algorithm
```

### 4.6 SMTP/IMAP — Indicatori di Phishing

Email protocol analysis reveals phishing campaigns and spam infrastructure.

**SMTP indicators of compromise:**

- Mismatched MAIL FROM envelope and From header (spoofing)
- Missing or failing SPF/DKIM/DMARC in headers
- Encoded attachments with executable extensions
- Embedded URLs pointing to recently registered domains
- SMTP AUTH from unusual source IPs (compromised accounts)

**Wireshark filters:**

```
smtp.req.command == "MAIL" && smtp.req.parameter contains "@"
smtp.response.code >= 400                    # SMTP errors
imaps || smtp.starttls                       # TLS-upgraded sessions
```

### 4.7 QUIC/HTTP3 — Analisi e Monitoraggio

QUIC (Quick UDP Internet Connections) is a transport protocol built on top of UDP, designed by Google and standardized as RFC 9000 (2021). HTTP/3 uses QUIC as its transport layer, replacing TCP+TLS with a single encrypted UDP-based protocol. As of 2025, over 30% of web traffic uses QUIC (Cloudflare estimates), and adoption is growing steadily year-over-year.

**Security monitoring challenges with QUIC:**

QUIC encrypts almost everything — not just the payload but most of the transport-layer metadata that was previously visible in TCP. Connection IDs, packet numbers (after the handshake), and stream framing are all encrypted. This fundamentally changes what network security tools can observe.

| Observable | TCP+TLS | QUIC |
|-----------|---------|------|
| Connection establishment | TCP SYN/ACK visible | Initial packet visible, but handshake encrypted after Initial |
| SNI (Server Name Indication) | Visible in ClientHello | Visible in Initial CRYPTO frames (unless ECH) |
| Certificate chain | Visible in TLS 1.2, encrypted in TLS 1.3 | Always encrypted |
| Stream boundaries | TCP segments visible | Encrypted |
| Connection migration | New TCP 4-tuple = new connection | Same Connection ID, different IP/port |
| Spin bit | N/A | 1-bit RTT estimation signal, only signal available |
| Retry mechanism | TCP SYN retransmission | QUIC Retry token (anti-amplification) |

**Detection approaches for QUIC traffic:**

1. **Initial packet analysis:** The QUIC Initial packet contains the ClientHello in the CRYPTO frame. Extract SNI, ALPN (h3), and TLS fingerprint data from this packet. JA3/JA4 fingerprinting works on the QUIC ClientHello — JA4 explicitly supports QUIC with a "q" prefix instead of "t" in the fingerprint string (e.g., `q13d1516h3_...`).

2. **Connection ID tracking:** QUIC Connection IDs allow connection migration between IP addresses. A single logical session can span multiple source IPs — traditional flow-based tracking breaks. NDR tools must correlate connections by Connection ID rather than 5-tuple alone.

3. **Version negotiation visibility:** The QUIC version field in the long header is unencrypted. Version negotiation packets are also unencrypted and reveal supported versions. Unusual or deprecated QUIC versions may indicate tunneling or evasion tools.

4. **Block-and-fallback strategy:** Some enterprises block UDP/443 (QUIC) at the firewall to force browsers to fall back to TCP/TLS, restoring traditional inspection capability. This is operationally simple but degrades performance for users and becomes less viable as services increasingly require QUIC.

**Suricata QUIC detection (Suricata 7+):**

Suricata 7 introduced native QUICv1 and GQUIC protocol analyzers. QUIC traffic is parsed and fields are available for rule matching:

```yaml
# Detect QUIC connection to suspicious SNI
alert quic $HOME_NET any -> $EXTERNAL_NET any (
    msg:"POLICY QUIC Connection to Suspicious Domain";
    flow:to_server;
    quic.sni;
    content:"malicious-domain.com";
    classtype:policy-violation;
    sid:2030200; rev:1;
)

# Detect QUIC on non-standard ports (not 443)
alert quic $HOME_NET any -> $EXTERNAL_NET !443 (
    msg:"ANOMALY QUIC on Non-Standard Port";
    flow:to_server;
    threshold:type limit, track by_src, count 1, seconds 3600;
    classtype:policy-violation;
    sid:2030201; rev:1;
)
```

**Zeek QUIC analysis (Zeek 7+):**

Zeek 7 introduced a Spicy-based QUIC analyzer that parses Initial packets and generates structured logs. QUIC connections appear in `conn.log` with service field `quic` and additional metadata in the QUIC-specific log. The JA3/JA4 package computes fingerprints for QUIC ClientHello messages identically to TCP TLS.

**QUIC-Exfil — emerging threat vector:** Recent research (ACM CCS 2025) demonstrated that QUIC's Server Preferred Address feature can be exploited for data exfiltration. An attacker-controlled server sends a preferred address in the TLS handshake, causing the client to migrate the connection to an attacker-chosen IP — effectively redirecting traffic flow without application awareness.

---

## 5. Deep Packet Inspection

### 5.1 Architettura DPI

Deep Packet Inspection examines packet payloads beyond Layer 3/4 headers to identify applications, extract content, and detect threats. DPI operates at L7 and requires significantly more processing resources than header-only inspection.

```
 Packet Flow Through DPI Pipeline:
 ┌──────┐    ┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌──────────┐
 │Packet│───>│Reassembly│───>│Protocol     │───>│Payload   │───>│Policy    │
 │Input │    │Engine    │    │Identification│   │Inspection│    │Action    │
 └──────┘    └──────────┘    └─────────────┘    └──────────┘    └──────────┘
                 │                  │                  │               │
            TCP stream         Heuristic          Signature       Allow/
            reassembly,        protocol ID,       matching,       Block/
            IP defrag,         beyond port        regex,          Alert/
            UDP session        numbers            ML classify     Rate-limit
            tracking
```

**Hardware vs Software DPI:**

| Aspect | Hardware (FPGA/ASIC) | Software (CPU) |
|--------|---------------------|----------------|
| Throughput | 10-400 Gbps | 1-40 Gbps (varies with rule count) |
| Latency | Microseconds | Milliseconds |
| Flexibility | Firmware update required | Instant rule/code updates |
| Cost | $50k-$500k appliance | Commodity server + open-source |
| Pattern capacity | Limited by TCAM/memory | Limited by CPU/RAM |
| Use case | ISP/carrier inline inspection | Enterprise IDS/IPS, research |

### 5.2 Tecniche di Ispezione

**Pattern matching:** Aho-Corasick and Hyperscan are the dominant multi-pattern matching algorithms. Suricata uses Hyperscan (Intel) for matching thousands of signatures simultaneously against reassembled streams.

**Protocol identification beyond port numbers:** Modern DPI does not rely on port numbers for protocol identification. Instead it uses:

- **Protocol signatures:** First-byte patterns (SSH begins with "SSH-2.0-", HTTP with "GET /", "POST /", "HTTP/1.", TLS ClientHello with 0x16 0x03, DNS queries with identifiable structure)
- **Heuristic analysis:** Payload entropy, byte distribution, packet size patterns
- **Behavioral classification:** Connection patterns (number of flows, timing, directionality) identify protocols even without recognizable byte patterns

**Application identification (NBAR, AppID):** Next-generation firewalls use proprietary DPI engines to identify ~3000-5000 applications regardless of port, encryption, or evasion. Palo Alto's App-ID, Cisco's NBAR2, and Fortinet's application control all implement this.

### 5.3 Content Extraction

DPI engines can extract specific content from inspected traffic:

- **File carving:** Reconstruct files from HTTP, FTP, SMB, and SMTP sessions. Compare hashes against known-bad databases.
- **URL extraction:** Build browsing history from HTTP/HTTPS (SNI) traffic.
- **Credential capture:** Extract cleartext credentials from FTP, HTTP Basic, LDAP simple bind, Telnet.
- **Metadata extraction:** Document metadata (EXIF, Office properties), email headers, certificate details.

### 5.4 DPI Bypass Techniques

Adversaries employ multiple techniques to evade DPI:

**Encryption:** TLS/SSL renders payload-based DPI ineffective. Post-quantum TLS 1.3 with ESNI/ECH eliminates even metadata visibility. This is the dominant bypass method.

**Tunneling:** Encapsulate prohibited protocols inside allowed ones — DNS tunneling (iodine, dnscat2), ICMP tunneling (ptunnel), HTTP tunneling (Chisel, reGeorg), WebSocket tunneling.

**Fragmentation and segmentation:** Split malicious payloads across multiple IP fragments or TCP segments. Naive DPI that inspects individual packets without reassembly misses split signatures. Most modern DPI performs stream reassembly, but edge cases persist with overlapping fragments and TTL-based evasion (Ptacek & Newsham, 1998).

**Protocol confusion:** Use one protocol's structure on another protocol's port (HTTPS on port 53, SSH on port 443) to exploit port-based allow rules. Port-independent protocol detection defeats this.

---

## 6. Zeek Deep Dive

### 6.1 Architettura Zeek

Zeek (formerly Bro) is a passive network traffic analyzer that generates rich, structured protocol logs and supports custom scripting for detection logic. Zeek does not block traffic — it observes and records.

```
 Zeek Cluster Architecture:
 ┌──────────────────────────────────────────────┐
 │                  MANAGER                      │
 │  Receives logs from proxies                   │
 │  Runs manager-level scripts                   │
 │  Manages cluster state                        │
 ├──────────────────────────────────────────────┤
 │          PROXY (1-2 instances)                │
 │  Distributes state across workers             │
 │  Handles data synchronization                 │
 │  Connection summary tables                    │
 ├──────────────────────────────────────────────┤
 │  WORKER 1  │  WORKER 2  │  WORKER 3  │ ...  │
 │  (CPU core)│  (CPU core)│  (CPU core)│       │
 │  Protocol  │  Protocol  │  Protocol  │       │
 │  parsing   │  parsing   │  parsing   │       │
 │  Script    │  Script    │  Script    │       │
 │  execution │  execution │  execution │       │
 └────────────┴────────────┴────────────┴───────┘
        ↑              ↑              ↑
 ┌──────────────────────────────────────────────┐
 │              PACKET SOURCE                    │
 │  TAP/SPAN ──> af_packet / PF_RING / DPDK     │
 │  Load-balanced across workers                 │
 └──────────────────────────────────────────────┘
```

**Worker sizing:** Each Zeek worker handles approximately 250-400 Mbps of traffic depending on protocol complexity. A 10 Gbps link requires 25-40 workers. Each worker is pinned to a CPU core.

**Packet acquisition frameworks:**

| Framework | Performance | Kernel Bypass | Recommendation |
|-----------|------------|---------------|----------------|
| af_packet | Good (up to ~5 Gbps) | No | Default for <5 Gbps deployments |
| PF_RING ZC | Excellent (10+ Gbps) | Yes | Production high-speed monitoring |
| DPDK | Maximum (40-100 Gbps) | Yes | Carrier-grade deployments |

### 6.2 Log Types

Zeek generates structured TSV (or JSON) log files, each documenting a specific protocol or activity. Key log files:

| Log File | Content | Security Value |
|----------|---------|---------------|
| conn.log | All connections (5-tuple, bytes, duration, state) | Baseline, anomaly detection, beaconing |
| dns.log | DNS queries and responses | Tunneling, DGA, C2 domains |
| http.log | HTTP requests with headers, URIs, status codes | Web attacks, C2, exfiltration |
| ssl.log | TLS handshake metadata (SNI, cipher, cert chain) | Encrypted C2, cert anomalies |
| files.log | Files transferred over any protocol | Malware delivery, exfiltration |
| notice.log | Alerts generated by Zeek scripts | Detection events |
| weird.log | Protocol violations and anomalies | Evasion attempts, malformed traffic |
| x509.log | Certificate details | Self-signed certs, expired certs |
| smtp.log | Email transactions | Phishing, spam relay |
| kerberos.log | Kerberos authentication events | Ticket attacks, auth anomalies |
| smb_files.log | SMB file access events | Lateral movement, data staging |
| pe.log | Portable Executable file analysis | Malware download detection |
| dpd.log | Dynamic protocol detection | Protocol evasion |

### 6.3 Zeek Scripting Language

Zeek's scripting language is event-driven and Turing-complete. Scripts define handlers for protocol events that Zeek raises as it processes traffic.

**Event handler fundamentals:**

```zeek
# Basic HTTP request monitoring — log suspicious user agents
event http_request(c: connection, method: string, original_URI: string,
                   unescaped_URI: string, version: string)
    {
    if ( c$http?$user_agent )
        {
        if ( /powershell|wget|curl|python-requests/ in c$http$user_agent )
            {
            NOTICE([$note=Weird::Activity,
                    $msg=fmt("Suspicious User-Agent: %s", c$http$user_agent),
                    $conn=c,
                    $identifier=cat(c$id$orig_h, c$http$user_agent)]);
            }
        }
    }
```

**Tracking connections with global state:**

```zeek
# Detect hosts performing port scans (>50 unique ports in 5 minutes)
module PortScanDetector;

export {
    redef enum Notice::Type += { Port_Scan_Detected };
    const scan_threshold = 50 &redef;
    const scan_interval = 5min &redef;
}

global scan_tracker: table[addr] of set[port] &create_expire=scan_interval;

event connection_attempt(c: connection)
    {
    local scanner = c$id$orig_h;
    local target_port = c$id$resp_p;

    if ( scanner !in scan_tracker )
        scan_tracker[scanner] = set();

    add scan_tracker[scanner][target_port];

    if ( |scan_tracker[scanner]| > scan_threshold )
        {
        NOTICE([$note=Port_Scan_Detected,
                $msg=fmt("Host %s scanned %d unique ports",
                         scanner, |scan_tracker[scanner]|),
                $src=scanner,
                $identifier=cat(scanner)]);
        delete scan_tracker[scanner];
        }
    }
```

**Custom protocol detection script — DNS tunneling:**

```zeek
# Detect DNS tunneling via high-entropy subdomain labels
module DNSTunnel;

export {
    redef enum Notice::Type += { DNS_Tunnel_Detected };
    const entropy_threshold = 3.5 &redef;
    const query_len_threshold = 50 &redef;
}

function calculate_entropy(s: string): double
    {
    local freq: table[string] of count;
    local total = |s|;

    for ( i in s )
        {
        if ( s[i] !in freq )
            freq[s[i]] = 0;
        ++freq[s[i]];
        }

    local entropy = 0.0;
    for ( ch, cnt in freq )
        {
        local p = cnt * 1.0 / total;
        entropy -= p * log2(p);
        }

    return entropy;
    }

event dns_request(c: connection, msg: dns_msg, query: string, qtype: count,
                  qclass: count)
    {
    # Extract subdomain portion (everything before the registered domain)
    local parts = split_string(query, /\./);
    if ( |parts| < 3 )
        return;

    local subdomain = parts[0];

    if ( |subdomain| > query_len_threshold )
        {
        local ent = calculate_entropy(subdomain);
        if ( ent > entropy_threshold )
            {
            NOTICE([$note=DNS_Tunnel_Detected,
                    $msg=fmt("Possible DNS tunnel: query=%s entropy=%.2f len=%d",
                             query, ent, |subdomain|),
                    $conn=c,
                    $identifier=cat(c$id$orig_h, query)]);
            }
        }
    }
```

### 6.4 Zeek Packages

The Zeek package manager (`zkg`) provides community and enterprise detection packages.

| Package | Purpose | Installation |
|---------|---------|-------------|
| ja3 | TLS client fingerprinting | `zkg install ja3` |
| hassh | SSH client/server fingerprinting | `zkg install hassh` |
| community-id | Cross-tool flow correlation ID | `zkg install community-id` |
| zeek-long-connections | Detect persistent connections (C2) | `zkg install zeek-long-connections` |
| bzar | MITRE ATT&CK-based SMB/DCE-RPC detection | `zkg install bzar` |
| icannTLD | Domain categorization via ICANN TLD list | `zkg install icannTLD` |

### 6.5 Zeek Cluster Deployment

Production Zeek deployment for a 10 Gbps link:

```ini
# /opt/zeek/etc/node.cfg
[manager]
type=manager
host=10.0.1.10

[proxy-1]
type=proxy
host=10.0.1.10

[worker-1]
type=worker
host=10.0.1.10
interface=af_packet::eth1
lb_method=custom
lb_procs=8
pin_cpus=0,1,2,3,4,5,6,7

[worker-2]
type=worker
host=10.0.1.10
interface=af_packet::eth1
lb_method=custom
lb_procs=8
pin_cpus=8,9,10,11,12,13,14,15
```

```ini
# /opt/zeek/etc/zeekctl.cfg
LogDir = /data/zeek/logs
LogRotationInterval = 3600
CompressLogs = 1
CompressCmd = zstd
MailTo = soc@example.com
```

```bash
# Deploy and manage
zeekctl deploy
zeekctl status
zeekctl diag worker-1    # Diagnostics for a specific worker
```

### 6.6 Novità Zeek 7 e 7.2

Zeek 7 (released August 2024) introduced a major architectural overhaul, modernizing core subsystems and adding significant new capabilities. Zeek 7.2 (released May 2025) is the current LTS release.

**Zeek Abstract Machine (ZAM) — Script Optimization:**

ZAM is an optional script optimization engine that compiles Zeek's abstract syntax trees into a low-level intermediate representation for more efficient execution. For detection-heavy deployments with complex custom scripts, ZAM can reduce script execution CPU overhead by 20-40%.

```bash
# Enable ZAM optimization
zeek -O ZAM -r capture.pcap local.zeek

# Or configure in zeekctl.cfg for permanent use
# ZeekArgs = -O ZAM
```

**Spicy 1.11 — Faster Protocol Parsers:**

Zeek 7 ships with Spicy 1.11, which includes a simplified compiler pipeline that produces parsers up to 30% faster at runtime for certain protocols. The Spicy framework allows writing custom protocol analyzers in a high-level grammar that Zeek compiles into native C++ — making it practical to add parsers for proprietary or uncommon protocols without modifying Zeek's core.

**New Protocol Analyzers:**

| Protocol | Analyzer Type | Security Value |
|----------|--------------|----------------|
| QUIC | Spicy-based | HTTP/3 monitoring, JA4 fingerprinting over QUIC |
| LDAP | Spicy-based | Active Directory reconnaissance detection, credential monitoring |
| WebSocket | Enhanced HTTP upgrade | C2 communication over WebSocket, interactive shell detection |

The LDAP analyzer is particularly valuable for enterprise security — it logs LDAP search operations, bind attempts, and modify operations, enabling detection of Active Directory enumeration (BloodHound, ADExplorer) and LDAP-based credential attacks.

```zeek
# Zeek 7 LDAP event handler — detect AD enumeration
event ldap_search_request(c: connection, message_id: int,
                          base_object: string, scope: count,
                          deref: count, size_limit: count,
                          time_limit: count, types_only: bool,
                          filter: string, attributes: vector of string)
    {
    # BloodHound-style LDAP queries target specific objectClass filters
    if ( /objectClass=computer/ in filter ||
         /objectClass=group/ in filter ||
         /objectClass=trustedDomain/ in filter )
        {
        if ( size_limit == 0 )  # Unbounded query = enumeration
            {
            NOTICE([$note=Weird::Activity,
                    $msg=fmt("Potential AD enumeration via LDAP: filter=%s base=%s",
                             filter, base_object),
                    $conn=c,
                    $identifier=cat(c$id$orig_h, filter)]);
            }
        }
    }
```

**Telemetry Framework (Prometheus Integration):**

Zeek 7 integrates prometheus-cpp and civetweb directly, exposing Zeek performance metrics via an HTTP endpoint for Prometheus scraping. This enables real-time monitoring of Zeek cluster health — packet drops, script execution time, memory usage, connection table size — through Grafana dashboards. Each worker exposes its own metrics endpoint, and the manager aggregates cluster-wide statistics.

```bash
# Query Zeek telemetry endpoint
curl http://zeek-manager:9911/metrics

# Key metrics to monitor
# zeek_connections_active       — current connection table size
# zeek_packets_dropped          — kernel packet drops per worker
# zeek_event_handler_invocations — script engine performance
# zeek_memory_rss_bytes         — per-worker memory usage
```

**Storage Framework (Zeek 7.2):**

Zeek 7.2 introduced the Storage Framework for persisting key/value data to external stores. This enables detection scripts to maintain state across Zeek restarts and share state between cluster nodes. Supported backends include SQLite (local persistence) and Redis (distributed state). Use cases include persistent reputation tables, cross-restart threat intelligence lookups, and distributed rate limiting across a Zeek cluster.

---

## 7. Suricata per Network Security

### 7.1 Architettura Suricata

Suricata is a high-performance network IDS/IPS and network security monitoring engine. Unlike Snort (single-threaded in v2), Suricata was designed from the ground up for multi-threaded operation.

**Threading model:**

```
 ┌─────────────────────────────────────────────────────────┐
 │  Capture Thread (af_packet/PF_RING/DPDK)                │
 │  Reads packets from NIC, distributes to detect threads  │
 ├─────────────────────────────────────────────────────────┤
 │  Detect Thread 1 │ Detect Thread 2 │ Detect Thread N    │
 │  Stream assembly │ Stream assembly │ Stream assembly    │
 │  Rule matching   │ Rule matching   │ Rule matching      │
 │  Protocol parse  │ Protocol parse  │ Protocol parse     │
 ├─────────────────────────────────────────────────────────┤
 │  Output Thread                                          │
 │  EVE JSON logging ─ alert output ─ pcap logging         │
 └─────────────────────────────────────────────────────────┘
```

**Capture modes:**

| Mode | Use Case | Performance |
|------|----------|-------------|
| af_packet | Linux default, good to ~5 Gbps | Kernel network stack |
| af_packet with fanout | Load-balance across threads | Better multi-core utilization |
| PF_RING ZC | High-speed (10+ Gbps) | Kernel bypass |
| DPDK | Maximum throughput (40-100 Gbps) | Full kernel bypass |
| pcap | Reading pcap files offline | N/A (file processing) |
| nfqueue | Inline IPS mode via netfilter | Moderate (kernel-user transitions) |

### 7.2 Rule Writing

Suricata rules consist of a header (action, protocol, source, destination, direction) and options (detection keywords).

**Rule structure:**

```
action protocol source_ip source_port -> dest_ip dest_port (options;)
```

**Basic signature examples:**

```yaml
# Detect Cobalt Strike default HTTP beacon
alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"ET MALWARE Cobalt Strike Beacon Activity";
    flow:established,to_server;
    http.uri;
    content:"/visit.js"; endswith;
    http.header;
    content:"Cookie:"; nocase;
    pcre:"/Cookie:\s*[a-zA-Z0-9+\/]{60,}/";
    classtype:trojan-activity;
    sid:2030000; rev:1;
)

# Detect PsExec service installation via SMB
alert smb any any -> $HOME_NET any (
    msg:"ATTACK PsExec Service Installation";
    flow:established,to_server;
    smb.named_pipe;
    content:"svcctl"; nocase;
    content:"PSEXESVC"; nocase;
    classtype:attempted-admin;
    sid:2030001; rev:1;
)

# Detect DNS tunneling — long subdomain labels
alert dns $HOME_NET any -> any any (
    msg:"POLICY Potential DNS Tunnel - Long Query";
    flow:to_server;
    dns.query;
    content:".";
    pcre:"/^[a-z0-9]{30,}\./i";
    threshold:type threshold, track by_src, count 10, seconds 60;
    classtype:policy-violation;
    sid:2030002; rev:1;
)
```

**Advanced keywords:**

```yaml
# Flowbits — stateful detection across multiple packets
# Stage 1: Mark SMB tree connect to ADMIN$
alert smb $HOME_NET any -> $HOME_NET any (
    msg:"LATERAL SMB ADMIN$ Access Stage 1";
    flow:established,to_server;
    smb.share; content:"ADMIN$";
    flowbits:set,smb_admin_access;
    flowbits:noalert;
    sid:2030010; rev:1;
)

# Stage 2: Alert on file write after ADMIN$ access
alert smb $HOME_NET any -> $HOME_NET any (
    msg:"LATERAL SMB ADMIN$ File Write Detected";
    flow:established,to_server;
    flowbits:isset,smb_admin_access;
    smb.filename; pcre:"/\.(exe|dll|bat|ps1|vbs|js)$/i";
    classtype:attempted-admin;
    sid:2030011; rev:1;
)

# Dataset — match against a list of known-bad JA3 hashes
alert tls $HOME_NET any -> $EXTERNAL_NET any (
    msg:"MALWARE Known Bad JA3 Fingerprint";
    flow:established,to_server;
    ja3.hash;
    dataset:isset,malicious-ja3,type string,load:/etc/suricata/datasets/bad-ja3.lst;
    classtype:trojan-activity;
    sid:2030020; rev:1;
)

# Lua scripting — complex detection logic
alert http any any -> any any (
    msg:"CUSTOM Suspicious Base64 in URL";
    flow:established,to_server;
    luajit:detect_b64_url.lua;
    classtype:policy-violation;
    sid:2030030; rev:1;
)
```

### 7.3 EVE JSON Output e Elasticsearch Integration

Suricata's EVE (Extensible Event Format) JSON output is the primary log format for SIEM integration.

```yaml
# suricata.yaml — EVE output configuration
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: eve.json
      types:
        - alert:
            payload: yes
            payload-buffer-size: 4096
            payload-printable: yes
            packet: yes
            metadata: yes
            tagged-packets: yes
        - dns:
            version: 2
            requests: yes
            responses: yes
        - http:
            extended: yes
            custom: [Host, User-Agent, Content-Type, Referer, X-Forwarded-For]
        - tls:
            extended: yes
        - files:
            force-magic: yes
            force-hash: [md5, sha256]
        - smtp:
            extended: yes
        - flow
        - stats:
            threads: yes
```

**Filebeat to Elasticsearch pipeline:**

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/suricata/eve.json
    json.keys_under_root: true
    json.add_error_key: true
    json.overwrite_keys: true

output.elasticsearch:
  hosts: ["https://es-node:9200"]
  index: "suricata-%{+yyyy.MM.dd}"
  ssl.certificate_authorities: ["/etc/pki/ca.pem"]
```

### 7.4 File Extraction e YARA

Suricata can extract files from monitored traffic and match them against YARA rules and hash lists.

```yaml
# suricata.yaml — file extraction
file-store:
  version: 2
  enabled: yes
  dir: /data/suricata/filestore
  write-fileinfo: yes
  force-hash: [md5, sha256]
  force-magic: yes
  force-filestore: no

# YARA rules integration (Suricata 7+)
# Match extracted files against YARA rules
datasets:
  - malware-hashes:
      type: md5
      load: /etc/suricata/datasets/malware-md5.lst
```

### 7.5 Suricata vs Snort 3

| Feature | Suricata | Snort 3 |
|---------|----------|---------|
| Threading | Native multi-threaded | Multi-threaded (redesigned from Snort 2) |
| Protocol parsers | Rust-based (robust, memory safe) | C++-based |
| Output format | EVE JSON (native structured logging) | JSON via plugins, unified2 legacy |
| File extraction | Built-in with YARA, hash matching | Via inspectors |
| Lua scripting | Supported in rules | Supported via inspectors |
| JA3/JA4 | Built-in | Via OpenAppID/inspectors |
| Community rules | ET Open, ET Pro, Snort rules compatible | Snort Subscriber, Community |
| GPU acceleration | Experimental | Not available |
| IPS mode | nfqueue, af_packet, DPDK | DAQ abstraction |
| License | GPLv2 | GPLv2 |

### 7.6 Performance Tuning

```yaml
# suricata.yaml — performance-critical settings

# Detection engine
detect-engine:
  - profile: high
    sgh-mpm-context: auto
    inspection-recursion-limit: 3000

# Stream reassembly
stream:
  memcap: 8gb
  reassembly:
    memcap: 16gb
    depth: 1mb
    toserver-chunk-size: 2560
    toclient-chunk-size: 2560

# Pattern matching algorithm
mpm-algo: hs    # Hyperscan (Intel) — fastest multi-pattern matcher

# Threading — pin to CPU cores
threading:
  set-cpu-affinity: yes
  cpu-affinity:
    - management-cpu-set:
        cpu: [0]
    - receive-cpu-set:
        cpu: [1, 2]
    - detect-cpu-set:
        cpu: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        mode: exclusive

# Ring buffer sizing
af-packet:
  - interface: eth1
    threads: 2
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes
    ring-size: 200000
    block-size: 262144
```

---

## 8. Threat Detection Patterns

This section covers what attacker behavior looks like in network traffic. Section 4 covers the normal protocol structure; here we focus on adversary techniques and the signatures they produce.

### 8.1 Rilevamento Comunicazioni C2

Command-and-Control (C2) communication is the most valuable detection target because it is present in nearly every attack lifecycle and persists throughout the compromise.

**Beaconing analysis:**

C2 frameworks (Cobalt Strike, Sliver, Mythic, Havoc) configure implants to "beacon" — periodically connect to the C2 server at configured intervals. Even with jitter, beaconing produces detectable patterns.

```python
#!/usr/bin/env python3
"""
Beaconing detector — analyzes Zeek conn.log for periodic connections.
Identifies hosts with regular connection intervals to external destinations.
"""

import csv
import sys
from collections import defaultdict
from statistics import stdev, mean

JITTER_THRESHOLD = 0.20   # 20% coefficient of variation
MIN_CONNECTIONS = 20       # Minimum connections to analyze
MIN_INTERVAL = 10          # Minimum average interval (seconds)
MAX_INTERVAL = 3600        # Maximum average interval (seconds)

def load_conn_log(filepath):
    """Parse Zeek conn.log TSV format."""
    connections = defaultdict(list)
    with open(filepath, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            fields = line.strip().split('\t')
            if len(fields) < 9:
                continue
            ts = float(fields[0])
            src_ip = fields[2]
            dst_ip = fields[4]
            dst_port = fields[5]
            proto = fields[6]

            # Only track outbound TCP/UDP to external IPs
            if proto in ('tcp', 'udp') and not dst_ip.startswith(('10.', '172.16.', '192.168.')):
                key = (src_ip, dst_ip, dst_port)
                connections[key].append(ts)
    return connections

def detect_beaconing(connections):
    """Identify connection pairs with periodic timing."""
    results = []
    for (src, dst, port), timestamps in connections.items():
        if len(timestamps) < MIN_CONNECTIONS:
            continue

        timestamps.sort()
        intervals = [timestamps[i+1] - timestamps[i] for i in range(len(timestamps)-1)]

        avg_interval = mean(intervals)
        if avg_interval < MIN_INTERVAL or avg_interval > MAX_INTERVAL:
            continue

        std_interval = stdev(intervals) if len(intervals) > 1 else 0
        cv = std_interval / avg_interval if avg_interval > 0 else float('inf')

        if cv < JITTER_THRESHOLD:
            results.append({
                'src': src,
                'dst': dst,
                'port': port,
                'count': len(timestamps),
                'avg_interval': round(avg_interval, 2),
                'std_dev': round(std_interval, 2),
                'cv': round(cv, 4),
                'first_seen': timestamps[0],
                'last_seen': timestamps[-1],
            })

    return sorted(results, key=lambda x: x['cv'])

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <conn.log>", file=sys.stderr)
        sys.exit(1)

    connections = load_conn_log(sys.argv[1])
    beacons = detect_beaconing(connections)

    print(f"{'Source':<18} {'Destination':<18} {'Port':<8} {'Count':<8} "
          f"{'Avg(s)':<10} {'StdDev':<10} {'CV':<8}")
    print("-" * 90)
    for b in beacons:
        print(f"{b['src']:<18} {b['dst']:<18} {b['port']:<8} {b['count']:<8} "
              f"{b['avg_interval']:<10} {b['std_dev']:<10} {b['cv']:<8}")
```

**JA3 fingerprint matching for known C2:**

Known JA3 hashes for common C2 frameworks:

| Framework | JA3 Hash | Notes |
|-----------|----------|-------|
| Cobalt Strike (default) | `72a589da586844d7f0818ce684948eea` | Default Java client |
| Metasploit Meterpreter | `5d65ea3fb1d4aa7d826733d2f2cbbb1d` | Default Meterpreter HTTP/S |
| Empire (Python) | `8916410db5a64b365e5fae5a49e4e809` | Python requests library |
| Sliver | Varies | Go TLS stack, rotating fingerprints |

### 8.2 Rilevamento Lateral Movement

Lateral movement produces distinctive patterns in east-west traffic.

**SMB-based movement indicators:**

```
# Zeek conn.log pattern: single host connecting to multiple internal hosts on port 445
# in a short time window — typical of automated tooling

# Wireshark filter for PsExec activity
smb2.tree contains "ADMIN$" && smb2.filename contains "PSEXESVC"

# Filter for WMI-based execution
dcerpc.cn_bind_to_uuid == "8BC3F05E-D86B-11D0-A075-00C04FB68820"
```

**RDP anomaly indicators:**

- RDP (3389) from workstation to workstation (unusual — normally workstation to server)
- RDP originating from a server (servers rarely initiate RDP)
- RDP sessions at unusual hours
- Multiple concurrent RDP sessions from a single source

**SSH lateral movement:**

```bash
# Detect SSH from internal non-jump-host sources
tcpdump -i eth0 'tcp dst port 22 and src net 10.0.0.0/8 and not src host 10.0.0.5'
```

### 8.3 Rilevamento Data Exfiltration

Data exfiltration detection targets anomalous outbound data volumes, protocol abuse, and covert channels.

**Volume anomaly detection:**

```python
#!/usr/bin/env python3
"""
Exfiltration detector — identifies hosts with anomalous outbound data volume.
Uses Zeek conn.log to calculate per-host daily upload volumes and flags outliers.
"""

import sys
from collections import defaultdict
from statistics import mean, stdev

def analyze_upload_volume(conn_log_path):
    """Calculate per-host outbound byte volumes."""
    host_bytes = defaultdict(int)

    with open(conn_log_path, 'r') as f:
        for line in f:
            if line.startswith('#'):
                continue
            fields = line.strip().split('\t')
            if len(fields) < 17:
                continue

            src_ip = fields[2]
            dst_ip = fields[4]
            orig_bytes = fields[16]  # orig_ip_bytes

            # Only count outbound traffic from internal to external
            if src_ip.startswith(('10.', '172.16.', '192.168.')) and \
               not dst_ip.startswith(('10.', '172.16.', '192.168.')):
                if orig_bytes != '-':
                    host_bytes[src_ip] += int(orig_bytes)

    return host_bytes

def find_anomalies(host_bytes, sigma_threshold=3.0):
    """Flag hosts with upload volume exceeding N standard deviations above mean."""
    if len(host_bytes) < 5:
        return []

    volumes = list(host_bytes.values())
    avg = mean(volumes)
    std = stdev(volumes) if len(volumes) > 1 else 0
    threshold = avg + (sigma_threshold * std)

    anomalies = []
    for host, vol in host_bytes.items():
        if vol > threshold:
            anomalies.append({
                'host': host,
                'bytes': vol,
                'mb': round(vol / (1024 * 1024), 2),
                'sigma': round((vol - avg) / std, 2) if std > 0 else 0,
            })

    return sorted(anomalies, key=lambda x: x['bytes'], reverse=True)

if __name__ == '__main__':
    host_bytes = analyze_upload_volume(sys.argv[1])
    anomalies = find_anomalies(host_bytes)

    for a in anomalies:
        print(f"ANOMALY: {a['host']} uploaded {a['mb']} MB ({a['sigma']} sigma above mean)")
```

**Protocol abuse indicators:**

| Channel | Normal | Exfiltration |
|---------|--------|-------------|
| DNS | Short queries, small responses | Long TXT queries, high query volume to single domain |
| ICMP | Small echo req/reply | Large ICMP payloads (>100 bytes), high frequency |
| HTTP | Mixed methods, varied destinations | Large POST to single destination, encoded payloads |
| HTTPS | Normal browsing patterns | Extended sessions, high upload volume |
| NTP | 48-byte packets to known NTP servers | Variable-size packets to unknown servers |

### 8.4 Rilevamento Scanning e Reconnaissance

**Port scan detection patterns in Zeek conn.log:**

- Single source IP connecting to many destination ports on one host (vertical scan)
- Single source IP connecting to one port across many destination IPs (horizontal scan)
- High ratio of connection attempts with RST or no response (SYN scan, connect scan)
- Unusual TCP flag combinations (NULL scan: no flags; XMAS scan: FIN+PSH+URG; ACK scan)

**Suricata rule for horizontal port scan:**

```yaml
alert tcp $EXTERNAL_NET any -> $HOME_NET any (
    msg:"SCAN Potential Horizontal Port Scan";
    flow:stateless;
    flags:S,12;
    threshold:type both, track by_src, count 50, seconds 30;
    classtype:attempted-recon;
    sid:2030040; rev:1;
)
```

### 8.5 Rilevamento Credential Theft

**Cleartext credential detection:**

```yaml
# Suricata rule: detect cleartext FTP credentials
alert ftp $HOME_NET any -> any any (
    msg:"POLICY FTP Cleartext Login Detected";
    flow:established,to_server;
    content:"USER "; depth:5;
    classtype:policy-violation;
    sid:2030050; rev:1;
)

# Detect NTLM authentication over HTTP (credential relay risk)
alert http $HOME_NET any -> any any (
    msg:"POLICY NTLM Authentication over HTTP";
    flow:established,to_server;
    http.header;
    content:"Authorization:"; nocase;
    content:"NTLM"; nocase; distance:0;
    classtype:policy-violation;
    sid:2030051; rev:1;
)
```

### 8.6 Rilevamento Malware Download

**Detecting PE/ELF downloads via HTTP:**

```yaml
# Detect Windows executable download
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"MALWARE Windows Executable Download via HTTP";
    flow:established,to_client;
    file_data;
    content:"MZ"; offset:0; depth:2;
    content:"PE|00 00|"; distance:0;
    classtype:trojan-activity;
    sid:2030060; rev:1;
)

# Detect ELF binary download
alert http $EXTERNAL_NET any -> $HOME_NET any (
    msg:"MALWARE ELF Binary Download via HTTP";
    flow:established,to_client;
    file_data;
    content:"|7f|ELF"; offset:0; depth:4;
    classtype:trojan-activity;
    sid:2030061; rev:1;
)
```

---

## 9. Encrypted Traffic Analysis

### 9.1 TLS Metadata Analysis Senza Decryption

Even without breaking encryption, TLS connections expose substantial metadata that enables detection.

**Observable TLS metadata:**

| Metadata | Visibility | Detection Value |
|----------|-----------|-----------------|
| ClientHello cipher suites | Always visible | Client application fingerprinting |
| SNI (Server Name Indication) | Visible in TLS 1.2/1.3 (unless ECH) | Destination identification |
| Certificate chain | Visible in TLS 1.2 (encrypted in 1.3) | CA validation, self-signed detection |
| ALPN extension | Always visible | Protocol negotiation (h2, http/1.1) |
| Session ticket / PSK | Visible | Session resumption patterns |
| Record sizes and timing | Always visible | Behavioral fingerprinting |
| Handshake duration | Always visible | Connection pattern analysis |

### 9.2 JA3, JA3S, JA4, JA4+ Fingerprinting

**JA3 (Client Fingerprint):**

JA3 creates an MD5 hash from the ClientHello fields: TLS version, cipher suites, extensions, elliptic curves, and elliptic curve point formats. Each unique TLS client implementation produces a distinctive hash.

```
JA3 hash computation:
  input = TLSVersion,Ciphers,Extensions,EllipticCurves,EllipticCurveFormats
  ja3 = md5(input)

Example:
  769,47-53-5-10-49161-49162-49171-49172-50-56-19-4,0-10-11,23-24-25,0
  → MD5 → 72a589da586844d7f0818ce684948eea  (Cobalt Strike default)
```

**JA3S (Server Fingerprint):**

JA3S fingerprints the ServerHello: TLS version, selected cipher, and extensions. The server response changes based on the client's offered parameters, so JA3+JA3S together provide a more specific fingerprint than either alone.

**JA4 (Next Generation):**

JA4 improves on JA3 with a more readable, version-independent format. The JA4 string is human-parseable:

```
JA4 format: ProtocolVersion_CipherCount_ExtensionCount_ALPNfirst_SNI_hash

Example: t13d1516h2_8daaf6152771_b0da82dd1658

Breaking down:
  t     = TLS (q for QUIC)
  13    = TLS 1.3
  d     = destination (client hello)
  15    = number of cipher suites
  16    = number of extensions
  h2    = first ALPN value
  _     = separator
  8daaf6152771  = truncated SHA256 of sorted cipher suites
  _     = separator
  b0da82dd1658  = truncated SHA256 of sorted extensions + signature algorithms
```

**JA4+ extensions:** JA4S (server fingerprint), JA4H (HTTP client fingerprint), JA4X (X.509 certificate fingerprint), JA4T (TCP client fingerprint via TCP options/window size/TTL). Together they form a comprehensive passive fingerprinting suite.

**Matching known malware with JA3:**

```bash
# Zeek — extract JA3 hashes (requires ja3 package)
# Output appears in ssl.log with ja3 and ja3s fields

# Query Zeek ssl.log for known bad JA3 hashes
cat ssl.log | zeek-cut ja3 server_name id.orig_h id.resp_h | \
  grep -f known_bad_ja3.txt

# tshark — extract JA3 from pcap
tshark -r capture.pcap -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e ip.dst -e ja3.hash -e tls.handshake.extensions_server_name
```

### 9.3 Certificate Anomaly Detection

Certificate-based anomaly detection catches poorly configured C2 infrastructure.

**Red flags in certificates:**

| Anomaly | Indicator | C2 Likelihood |
|---------|-----------|--------------|
| Self-signed | Issuer == Subject | High for external connections |
| Expired | NotAfter in the past | Medium (lazy C2 operator) |
| Short validity | < 30 days and not Let's Encrypt | High |
| Mismatched CN/SAN | CN doesn't match SNI | High |
| Default/generic CN | "localhost", "server", random string | Very high |
| Issuer in untrusted CA list | Unknown or revoked CA | High |
| Unusual key size | 1024-bit RSA or non-standard | Medium |
| Certificate on unusual port | TLS on port 53, 8080, or custom | Medium-High |

**Zeek script for certificate anomaly alerting:**

```zeek
module CertAnomalyDetector;

export {
    redef enum Notice::Type += {
        Self_Signed_Cert_External,
        Expired_Cert,
        Short_Lived_Cert,
    };
}

event ssl_established(c: connection)
    {
    if ( ! c$ssl?$cert_chain || |c$ssl$cert_chain| == 0 )
        return;

    local cert = c$ssl$cert_chain[0]$x509$certificate;

    # Self-signed certificate to external destination
    if ( cert$issuer == cert$subject &&
         ! Site::is_local_addr(c$id$resp_h) )
        {
        NOTICE([$note=Self_Signed_Cert_External,
                $msg=fmt("Self-signed cert to external host: %s (CN=%s)",
                         c$id$resp_h, cert$subject),
                $conn=c,
                $identifier=cat(c$id$resp_h, cert$subject)]);
        }

    # Expired certificate
    if ( cert?$not_valid_after && cert$not_valid_after < network_time() )
        {
        NOTICE([$note=Expired_Cert,
                $msg=fmt("Expired certificate: %s (expired %s)",
                         cert$subject, cert$not_valid_after),
                $conn=c,
                $identifier=cat(c$id$resp_h, cert$subject)]);
        }

    # Short-lived certificate (less than 7 days validity)
    if ( cert?$not_valid_before && cert?$not_valid_after )
        {
        local validity = cert$not_valid_after - cert$not_valid_before;
        if ( validity < 7 days && cert$issuer == cert$subject )
            {
            NOTICE([$note=Short_Lived_Cert,
                    $msg=fmt("Short-lived self-signed cert: %s (validity: %s)",
                             cert$subject, validity),
                    $conn=c,
                    $identifier=cat(c$id$resp_h, cert$subject)]);
            }
        }
    }
```

### 9.4 ESNI/ECH — Implicazioni per la Sicurezza

Encrypted Client Hello (ECH, formerly ESNI) encrypts the SNI field in the ClientHello, eliminating the last major piece of plaintext metadata in TLS 1.3. This has profound implications for network security monitoring:

- **Before ECH:** The SNI reveals which domain the client is connecting to, even over TLS. This enables domain-based blocking, category filtering, and C2 domain detection.
- **After ECH:** The outer ClientHello contains a generic "public name" (typically the CDN's hostname), while the actual destination is encrypted. The inner SNI is only readable by the server behind the CDN.

**Impact on NDR:**

- Domain-based detection rules become ineffective for ECH-protected connections
- JA3/JA4 fingerprinting remains functional (cipher suites and extensions are still visible in the outer ClientHello)
- Certificate-based detection is already limited in TLS 1.3 (certs encrypted); ECH compounds this
- Network defenders must rely more heavily on flow-level behavioral analysis and endpoint telemetry

### 9.5 TLS Interception Architecture

For environments where decryption is legally permitted and operationally required, TLS interception provides full visibility.

**Forward proxy (MITM):**

```
 Client ──TLS──> Proxy ──TLS──> Destination
                  │
                  ├── Decrypts client traffic using proxy CA cert
                  ├── Inspects cleartext payload
                  ├── Re-encrypts to destination using real server cert
                  └── Proxy CA must be trusted by all clients
```

Tools: Squid with ssl-bump, Blue Coat/Symantec ProxySG, Palo Alto SSL decryption, Zscaler cloud proxy.

**Key forwarding (passive):**

For internal servers: forward the TLS session keys to the monitoring tool (Zeek, ExtraHop) via key logging (SSLKEYLOGFILE) or API. No MITM required, works passively.

```bash
# Enable TLS key logging in applications (debug/monitoring only)
export SSLKEYLOGFILE=/tmp/tls-keys.log

# Use with Wireshark/tshark
tshark -r capture.pcap -o "tls.keylog_file:/tmp/tls-keys.log" -Y "http2"
```

### 9.6 Privacy vs Security

TLS interception creates a tension between security visibility and privacy rights:

- **Legal constraints:** GDPR Art. 5 requires data minimization. Intercepting all TLS traffic captures far more personal data than necessary for security monitoring.
- **Banking/healthcare exceptions:** Many jurisdictions prohibit intercepting financial and medical TLS connections even for security purposes.
- **Certificate pinning:** Applications with certificate pinning (banking apps, Signal, corporate MDM agents) will reject intercepting proxy certificates, breaking functionality.
- **Operational risk:** The intercepting proxy becomes a high-value target — compromise of the proxy CA key allows network-wide MITM.

**Pragmatic approach:** Use metadata-based detection (JA3/JA4, certificate analysis, behavioral analytics) as the primary encrypted traffic analysis method. Reserve TLS interception for specific, justified use cases with documented legal basis and limited scope.

---

## 10. Laboratorio

### 10.1 Deploy: Zeek + Suricata + ELK su Sensore Dedicato

**Hardware requirements for a 1 Gbps sensor:**

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 8 cores | 16 cores (for Zeek workers + Suricata detect threads) |
| RAM | 32 GB | 64 GB |
| Storage (pcap) | 2 TB HDD | 4 TB SSD |
| Storage (logs/ELK) | 500 GB SSD | 1 TB NVMe |
| NICs | 2x 1GbE (1 mgmt + 1 monitor) | 2x 10GbE |

**Installation sequence (Ubuntu 22.04 LTS):**

```bash
# 1. System preparation
apt update && apt upgrade -y
apt install -y build-essential cmake libpcap-dev libjansson-dev \
  libyaml-dev libmagic-dev liblz4-dev zstd wget curl gnupg apt-transport-https

# 2. Install Zeek from official repository
echo 'deb http://download.opensuse.org/repositories/security:/zeek/xUbuntu_22.04/ /' | \
  tee /etc/apt/sources.list.d/zeek.list
wget -qO - 'https://download.opensuse.org/repositories/security:/zeek/xUbuntu_22.04/Release.key' | \
  gpg --dearmor -o /etc/apt/trusted.gpg.d/zeek.gpg
apt update && apt install -y zeek-lts

# Configure Zeek
cat > /opt/zeek/etc/node.cfg << 'NODEEOF'
[zeek]
type=standalone
host=localhost
interface=eth1
NODEEOF

# Install Zeek packages
/opt/zeek/bin/zkg install ja3 hassh community-id

# 3. Install Suricata
add-apt-repository -y ppa:oisf/suricata-stable
apt update && apt install -y suricata suricata-update

# Update Suricata rules
suricata-update
suricata-update enable-source et/open
suricata-update enable-source oisf/trafficid

# Configure Suricata interface
sed -i 's/interface: eth0/interface: eth1/' /etc/suricata/suricata.yaml

# 4. Install Elasticsearch + Kibana
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | \
  gpg --dearmor -o /usr/share/keyrings/elasticsearch-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] \
  https://artifacts.elastic.co/packages/8.x/apt stable main" | \
  tee /etc/apt/sources.list.d/elastic-8.x.list
apt update && apt install -y elasticsearch kibana filebeat

# 5. Configure Filebeat to ingest Zeek and Suricata logs
filebeat modules enable zeek suricata

# 6. Start services
systemctl enable --now elasticsearch kibana zeek suricata filebeat

# 7. Deploy Zeek
/opt/zeek/bin/zeekctl deploy
```

### 10.2 Cattura Traffico da TAP/SPAN

**Configure monitoring interface (no IP, promiscuous, no offloading):**

```bash
# Disable all hardware offloading on the monitor interface
ethtool -K eth1 gro off lro off tso off gso off rx off tx off sg off

# Bring interface up without IP address
ip link set eth1 up promisc on
ip addr flush dev eth1

# Verify — interface should show PROMISC flag, no IP
ip addr show eth1

# Optional: increase ring buffer for high-throughput capture
ethtool -G eth1 rx 4096

# Verify no packet drops
ethtool -S eth1 | grep -i drop
```

### 10.3 Analisi Dataset PCAP

Practice datasets for malware C2, lateral movement, and exfiltration analysis:

| Dataset | Source | Content |
|---------|--------|---------|
| Malware Traffic Analysis exercises | malware-traffic-analysis.net | Real-world malware pcaps with guided analysis |
| CICIDS2017 | University of New Brunswick | Labeled intrusion detection dataset |
| UNSW-NB15 | UNSW Canberra | Modern attack traffic dataset |
| Stratosphere IPS datasets | stratosphereips.org | C2 botnet traffic captures |
| Zeek exercise pcaps | zeek.org/community | Protocol analysis training |

**Guided analysis workflow — C2 detection in a PCAP:**

```bash
# Step 1: Get connection overview
tshark -r malware.pcap -q -z conv,tcp | sort -t'<' -k5 -rn | head -20

# Step 2: Identify external destinations
tshark -r malware.pcap -Y "tcp.flags.syn == 1 && tcp.flags.ack == 0" \
  -T fields -e ip.dst -e tcp.dstport | sort | uniq -c | sort -rn | head -20

# Step 3: Extract JA3 fingerprints
tshark -r malware.pcap -Y "tls.handshake.type == 1" \
  -T fields -e ip.src -e ip.dst -e ja3.hash

# Step 4: Analyze HTTP traffic
tshark -r malware.pcap -Y "http.request" \
  -T fields -e ip.src -e http.host -e http.request.method -e http.request.uri \
  -e http.user_agent

# Step 5: Check DNS for DGA or tunneling
tshark -r malware.pcap -Y "dns.flags.response == 0" \
  -T fields -e ip.src -e dns.qry.name | \
  awk '{print length($2), $0}' | sort -rn | head -30

# Step 6: Run Zeek against the pcap for structured logs
/opt/zeek/bin/zeek -r malware.pcap /opt/zeek/share/zeek/site/local.zeek

# Step 7: Analyze Zeek output
cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p duration orig_bytes resp_bytes | \
  sort -t$'\t' -k4 -rn | head -20

cat dns.log | zeek-cut query answers | sort | uniq -c | sort -rn | head -30

cat ssl.log | zeek-cut server_name ja3 validation_status | sort | uniq -c | sort -rn

# Step 8: Run Suricata against the pcap
suricata -r malware.pcap -l /tmp/suricata-output/ -k none

# Check alerts
cat /tmp/suricata-output/eve.json | \
  python3 -c "import sys,json; [print(json.dumps(json.loads(l),indent=2)) \
  for l in sys.stdin if json.loads(l).get('event_type')=='alert']" | head -100
```

### 10.4 Scrittura Detection Personalizzate

**Exercise 1 — Zeek script for beaconing detection:**

Create the following file as `/opt/zeek/share/zeek/site/beacon-detect.zeek`:

```zeek
@load base/frameworks/notice
@load base/protocols/conn

module BeaconDetector;

export {
    redef enum Notice::Type += {
        Beacon_Detected
    };

    ## Number of connections before checking interval regularity
    const min_conn_count = 15 &redef;

    ## Maximum coefficient of variation to consider as beaconing
    const max_cv = 0.25 &redef;

    ## Observation window
    const window = 30min &redef;
}

# Track connection timestamps per source-destination pair
global conn_history: table[addr, addr, port] of vector of time
    &create_expire=window;

event connection_state_remove(c: connection)
    {
    if ( Site::is_local_addr(c$id$resp_h) )
        return;  # Only track outbound connections

    local key = [c$id$orig_h, c$id$resp_h, c$id$resp_p];

    if ( key !in conn_history )
        conn_history[key] = vector();

    conn_history[key] += network_time();

    if ( |conn_history[key]| < min_conn_count )
        return;

    # Calculate intervals
    local intervals: vector of interval = vector();
    local times = conn_history[key];

    local i = 1;
    while ( i < |times| )
        {
        intervals += times[i] - times[i - 1];
        ++i;
        }

    # Calculate mean and standard deviation
    local sum_val = 0.0;
    for ( idx in intervals )
        sum_val += interval_to_double(intervals[idx]);

    local mean_val = sum_val / |intervals|;

    local sum_sq = 0.0;
    for ( idx in intervals )
        {
        local diff = interval_to_double(intervals[idx]) - mean_val;
        sum_sq += diff * diff;
        }

    local std_val = (sum_sq / |intervals|) ** 0.5;
    local cv = std_val / mean_val;

    if ( cv < max_cv && mean_val > 5.0 )
        {
        NOTICE([$note=Beacon_Detected,
                $msg=fmt("Beaconing: %s -> %s:%s interval=%.1fs cv=%.3f count=%d",
                         key[0], key[1], key[2], mean_val, cv, |times|),
                $src=key[0],
                $identifier=cat(key[0], key[1], key[2])]);

        delete conn_history[key];
        }
    }
```

**Exercise 2 — Suricata rule for protocol anomaly:**

```yaml
# Detect TLS on non-standard ports (potential C2)
alert tls $HOME_NET any -> $EXTERNAL_NET !443 (
    msg:"ANOMALY TLS on Non-Standard Port";
    flow:established,to_server;
    tls.sni;
    content:".";   # Ensure SNI is present
    threshold:type limit, track by_src, count 1, seconds 3600;
    classtype:policy-violation;
    sid:2030100; rev:1;
)

# Detect HTTP on port 443 (expected TLS, got HTTP — misconfiguration or evasion)
alert http $HOME_NET any -> $EXTERNAL_NET 443 (
    msg:"ANOMALY HTTP on Port 443 (Expected TLS)";
    flow:established,to_server;
    classtype:policy-violation;
    sid:2030101; rev:1;
)

# Detect DNS over TCP to external resolvers (potential tunneling)
alert tcp $HOME_NET any -> !$DNS_SERVERS 53 (
    msg:"ANOMALY DNS TCP to External Resolver";
    flow:established,to_server;
    classtype:policy-violation;
    sid:2030102; rev:1;
)

# Detect SSH on non-standard port
alert ssh $HOME_NET any -> $EXTERNAL_NET !22 (
    msg:"ANOMALY SSH on Non-Standard Port";
    flow:established;
    classtype:policy-violation;
    sid:2030103; rev:1;
)
```

### 10.5 Threat Hunting negli Artefatti Catturati

**Structured hunting process using captured traffic:**

```
 Hunting Hypothesis Workflow:
 ┌───────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────┐
 │ 1. Hypothesis │───>│ 2. Data      │───>│ 3. Analysis  │───>│ 4. Result│
 │               │    │ Collection   │    │              │    │          │
 │ "Adversary is │    │ Query Zeek   │    │ Statistical  │    │ True     │
 │ using DNS     │    │ dns.log for  │    │ analysis of  │    │ positive │
 │ tunneling for │    │ TXT queries, │    │ query length,│    │ or       │
 │ exfiltration" │    │ long queries │    │ entropy,     │    │ refined  │
 │               │    │ to single    │    │ frequency    │    │ hypothesis│
 │               │    │ domains      │    │ patterns     │    │          │
 └───────────────┘    └──────────────┘    └──────────────┘    └──────────┘
```

**Hunt 1 — Find beaconing in conn.log:**

```bash
# Extract connections to external hosts, grouped by pair, sorted by count
cat conn.log | zeek-cut id.orig_h id.resp_h id.resp_p proto | \
  grep -v '^#' | \
  sort | uniq -c | sort -rn | head -30

# For suspicious pairs, extract timestamps and check interval regularity
cat conn.log | zeek-cut ts id.orig_h id.resp_h id.resp_p | \
  grep "10.0.1.50.*203.0.113.100.*443" | \
  awk '{print $1}' | \
  awk 'NR>1{print $1-prev} {prev=$1}'
```

**Hunt 2 — Find IOCs in DNS queries:**

```bash
# Search for known malicious domains
cat dns.log | zeek-cut query | grep -if ioc_domains.txt

# Find high-entropy domain queries (DGA detection)
cat dns.log | zeek-cut query | \
  python3 -c "
import sys, math
for line in sys.stdin:
    q = line.strip().split('.')[0]
    if len(q) < 5: continue
    freq = {}
    for c in q:
        freq[c] = freq.get(c, 0) + 1
    ent = -sum((v/len(q)) * math.log2(v/len(q)) for v in freq.values())
    if ent > 3.5 and len(q) > 15:
        print(f'{ent:.2f} {line.strip()}')
" | sort -rn | head -20

# Find domains with high unique subdomain count (exfiltration indicator)
cat dns.log | zeek-cut query | \
  awk -F. '{
    n = NF;
    domain = $(n-1)"."$n;
    sub_count[domain]++
  } END {
    for (d in sub_count)
      if (sub_count[d] > 100)
        print sub_count[d], d
  }' | sort -rn
```

**Hunt 3 — Find lateral movement in SMB logs:**

```bash
# Identify admin share access
cat smb_mapping.log | zeek-cut id.orig_h id.resp_h path | \
  grep -E '(ADMIN\$|C\$|IPC\$)'

# Identify executable files transferred via SMB
cat smb_files.log | zeek-cut id.orig_h id.resp_h name action size | \
  grep -iE '\.(exe|dll|ps1|bat|vbs|js|hta)' | \
  sort -t$'\t' -k5 -rn

# Cross-reference with authentication events
cat ntlm.log | zeek-cut id.orig_h id.resp_h username domainname success
```

**Hunt 4 — Find suspicious TLS certificates:**

```bash
# List all self-signed certificates seen
cat ssl.log | zeek-cut server_name validation_status ja3 | \
  grep "self signed"

# Find certificates with unusual validity periods
cat x509.log | zeek-cut certificate.subject certificate.issuer \
  certificate.not_valid_before certificate.not_valid_after | \
  awk -F'\t' '{
    split($3, start, "T");
    split($4, end, "T");
    # Flag if validity < 7 days or issuer == subject
    if ($2 == $1) print "SELF-SIGNED:", $0
  }'

# Find TLS on unusual ports
cat ssl.log | zeek-cut id.resp_p server_name ja3 | \
  grep -v "^443" | grep -v "^8443" | sort | uniq -c | sort -rn
```

---

## 11. Arkime — Cattura e Indicizzazione Pacchetti

### 11.1 Architettura e Componenti

Arkime (precedentemente noto come Moloch) è un sistema open-source progettato per la cattura, l'indicizzazione e la ricerca di pacchetti di rete su larga scala. A differenza di semplici strumenti di cattura come tcpdump, Arkime è concepito per gestire volumi di traffico dell'ordine di centinaia di gigabit al secondo in ambienti enterprise distribuiti.

L'architettura di Arkime si compone di tre elementi fondamentali:

```
 ┌────────────────────────────────────────────────────────────────┐
 │                    ARKIME VIEWER (Web UI)                       │
 │  Interfaccia web per ricerca sessioni, download PCAP,          │
 │  visualizzazione timeline, statistiche protocolli               │
 ├────────────────────────────────────────────────────────────────┤
 │                    OPENSEARCH / ELASTICSEARCH                   │
 │  Indicizzazione metadata sessioni (5-tuple, protocollo,        │
 │  domini, JA3/JA4, certificati, file hash, tag utente)          │
 ├────────────────────────────────────────────────────────────────┤
 │               ARKIME CAPTURE (uno o più nodi)                   │
 │  Cattura pacchetti da TAP/SPAN ─ Scrive PCAP su disco          │
 │  Genera metadata sessione ─ Invia ad OpenSearch                 │
 │  File extraction ─ YARA matching ─ Tagging automatico           │
 └────────────────────────────────────────────────────────────────┘
        ↑                    ↑                    ↑
   ┌────┴────┐          ┌────┴────┐          ┌────┴────┐
   │  TAP 1  │          │  TAP 2  │          │  TAP N  │
   │ Segment │          │ Segment │          │ Segment │
   └─────────┘          └─────────┘          └─────────┘
```

**Arkime Capture** è il processo che legge i pacchetti dall'interfaccia di rete, li scrive in file PCAP su disco locale e genera i record di sessione indicizzati. Ogni istanza di capture gestisce un'interfaccia di monitoraggio ed è ottimizzata per scrivere su disco con il minimo overhead.

**OpenSearch/Elasticsearch** riceve i metadata delle sessioni e li indicizza per la ricerca rapida. Ogni sessione contiene centinaia di campi estratti: indirizzi IP, porte, protocolli applicativi identificati, hostname DNS, SNI TLS, hash JA3/JA4, certificati X.509, user-agent HTTP, hash dei file trasferiti e molto altro.

**Arkime Viewer** è l'interfaccia web che permette agli analisti di cercare sessioni, visualizzare timeline di connessioni, scaricare i PCAP originali associati a sessioni specifiche, e costruire query complesse basate su qualsiasi campo indicizzato.

### 11.2 Arkime 6 — Novità e Miglioramenti

Arkime 6, rilasciato nel 2025, introduce miglioramenti significativi in termini di prestazioni e funzionalità:

- **Download PCAP 5x più veloci** rispetto ad Arkime 5, grazie alla riscrittura del motore di estrazione PCAP
- **Hunt 2x più rapidi**, con ottimizzazione delle query di ricerca su grandi volumi di sessioni indicizzate
- **Arkime Tab**: una nuova vista nella UI che offre visibilità istantanea sui top talker, protocolli predominanti e metriche chiave, completamente personalizzabile dall'utente con grafici temporali, tabelle e grafici a torta
- **Role Inheritance**: il sistema di gestione utenti introduce l'ereditarietà dei ruoli, permettendo una gestione dei permessi più flessibile dove gli amministratori possono creare ruoli che ereditano permessi da altri ruoli
- **Container ufficiali**: immagini container preconfigurate per semplificare il deployment in ambienti Kubernetes e Docker
- **Supporto FreeBSD**: pacchetti con supporto netmap e bpf per ambienti BSD

### 11.3 Deployment Multi-Nodo

Per ambienti enterprise con traffico distribuito su più segmenti di rete, Arkime supporta il deployment distribuito con più nodi di cattura che condividono un cluster OpenSearch comune.

```bash
# /opt/arkime/etc/config.ini — configurazione nodo di cattura
[default]
elasticsearch=https://opensearch-node1:9200,https://opensearch-node2:9200
rotateIndex=daily
pcapDir=/data/arkime/pcap
maxFileSizeG=2
maxFileTimeM=30
freeSpaceG=10%
compressES=true

# Tagging automatico basato su subnet
rulesFiles=/opt/arkime/etc/arkime.rules

# Plugin per JA4 fingerprinting
plugins=ja4.so

# Interfaccia di cattura
interface=eth1
bpf=not port 9200

# Packet processing
snapLen=0
pcapBufferSize=1073741824
tpacketv3BlockSize=2097152

[headers-http-request]
authorization=type:notindex

[headers-http-response]
set-cookie=type:notindex
```

**Regole di tagging automatico (arkime.rules):**

```yaml
---
version: 1
rules:
  # Tag traffico verso reti note di C2
  - name: "Known C2 Infrastructure"
    when: "fieldSet"
    fields:
      ip.dst:
        - 203.0.113.0/24
        - 198.51.100.0/24
    ops:
      _tag:
        - "known-c2"
        - "high-priority"

  # Tag traffico con certificati self-signed
  - name: "Self-Signed Certificates"
    when: "fieldSet"
    fields:
      cert.issuer.cn:
        - "localhost"
        - "server"
    ops:
      _tag:
        - "self-signed-cert"

  # Tag download di eseguibili
  - name: "Executable Downloads"
    when: "fieldSet"
    fields:
      http.md5:
        - "*"
    ops:
      _tag:
        - "file-download"
```

### 11.4 Smart PCAP e Workflow Investigativo

Il concetto di Smart PCAP, introdotto dalla piattaforma Corelight e adottabile anche con Arkime tramite integrazioni personalizzate, collega i log Zeek, i file estratti e le detection con i pacchetti specifici necessari per l'investigazione, invece di conservare l'intero flusso PCAP. Questo approccio riduce drasticamente i costi di storage mantenendo la capacità forense.

**Workflow investigativo tipico con Arkime:**

1. **Ricezione allarme**: Un alert Suricata o una notice Zeek segnala attività sospetta
2. **Ricerca sessione**: L'analista cerca in Arkime per IP sorgente, timestamp e porta coinvolti
3. **Analisi contesto**: Esame dei campi indicizzati — JA3 hash, SNI, certificati, user-agent
4. **Download PCAP selettivo**: Scaricamento del PCAP relativo solo alle sessioni di interesse
5. **Analisi profonda in Wireshark**: Apertura del PCAP scaricato per ispezione a livello di pacchetto
6. **Correlazione temporale**: Utilizzo della timeline Arkime per identificare sessioni correlate nello stesso intervallo temporale
7. **Pivoting**: Ricerca su altri campi estratti (domini, hash, certificati) per identificare attività correlata

```
# Query Arkime — esempi di ricerca avanzata

# Sessioni con certificati self-signed verso destinazioni esterne
cert.issuer.cn == cert.subject.cn && ip.dst != 10.0.0.0/8

# Connessioni HTTP con user-agent sospetti
http.user-agent == *powershell* || http.user-agent == *wget* || http.user-agent == ""

# Download di file PE (eseguibili Windows) nelle ultime 24 ore
file.md5 == EXISTS! && protocols == http && http.content-type == *octet-stream*

# Sessioni TLS con JA3 noto per Cobalt Strike
tls.ja3 == 72a589da586844d7f0818ce684948eea

# Sessioni con alto volume di upload verso singola destinazione
databytes > 100000000 && ip.dst == 203.0.113.50
```

### 11.5 Integrazione con Zeek e Suricata

Arkime si integra nativamente con Zeek e Suricata per creare un NDR stack open-source completo:

- **Zeek** genera log strutturati di protocollo (conn.log, dns.log, ssl.log, http.log) con metadata ricchi
- **Suricata** fornisce detection basata su signature con output EVE JSON e file extraction
- **Arkime** indicizza il PCAP completo e fornisce l'interfaccia di ricerca e retrieval

Il Community ID (un hash deterministico basato sulla 5-tupla della connessione) permette la correlazione incrociata tra i log di tutti e tre gli strumenti. Una sessione identificata come sospetta in Zeek può essere localizzata immediatamente in Arkime per il download PCAP e in Suricata per verificare se ha generato alert.

```bash
# Correlazione tramite Community ID
# 1. Trovare il community_id in Zeek
cat conn.log | zeek-cut community_id id.orig_h id.resp_h | grep "1:abc123..."

# 2. Cercare lo stesso community_id in Arkime
# Nella barra di ricerca Arkime: communityId == "1:abc123..."

# 3. Verificare alert Suricata correlati
cat eve.json | jq 'select(.community_id == "1:abc123...")'
```

---

## 12. NetFlow sFlow IPFIX — Analisi Avanzata dei Flussi

### 12.1 Confronto Dettagliato dei Protocolli di Flusso

I protocolli di flusso rappresentano il metodo più scalabile per ottenere visibilità sulla totalità del traffico di rete. A differenza del full packet capture, i dati di flusso consumano una frazione minima dello storage ma forniscono comunque informazioni sufficienti per la detection di anomalie, il capacity planning e il troubleshooting di rete.

**NetFlow v5** è il formato originale sviluppato da Cisco negli anni '90. Utilizza un formato di record fisso con 7 campi chiave (source/dest IP, source/dest port, protocol, ToS, input interface). Limitazioni: supporta solo IPv4, formato rigido non estensibile, nessun supporto per MPLS o VLAN tagging. Ancora diffuso in infrastrutture legacy.

**NetFlow v9** introduce i template, permettendo record flessibili con campi personalizzabili. Supporta IPv6, MPLS, BGP next-hop e altri campi. I template vengono inviati periodicamente dal router al collector, e i record di flusso si riferiscono al template per la decodifica.

**IPFIX (IP Flow Information Export)** è lo standard IETF basato su NetFlow v9 (RFC 7011-7015). Aggiunge campi enterprise-specific, supporto per record di lunghezza variabile, trasporto su TCP/SCTP (oltre a UDP), e un registro IANA standardizzato di information element. IPFIX è il protocollo raccomandato per nuovi deployment.

**sFlow** (RFC 3176) opera diversamente: campiona 1 pacchetto ogni N (tipicamente 1:1000 o 1:4096) e invia il campione completo (header + porzione di payload) al collector. Vantaggi: overhead minimo sul device di rete, visibilità immediata senza attendere la scadenza del flusso. Svantaggi: il campionamento introduce imprecisione statistica, specialmente per flussi a basso volume.

| Caratteristica | NetFlow v5 | NetFlow v9 | IPFIX | sFlow |
|----------------|-----------|-----------|-------|-------|
| Formato record | Fisso | Template-based | Template-based | Campione pacchetto |
| IPv6 | No | Sì | Sì | Sì |
| Campionamento | Opzionale | Opzionale | Opzionale | Obbligatorio (1:N) |
| Trasporto | UDP | UDP | UDP/TCP/SCTP | UDP |
| Campi custom | No | Sì (via template) | Sì (enterprise IE) | Limitati |
| Latenza dati | Alta (attende scadenza flusso) | Media | Media | Bassa (real-time) |
| Vendor support | Solo Cisco | Multi-vendor | Standard IETF | Multi-vendor |
| Payload visibility | Nessuna | Nessuna | Nessuna | Header campionato |

### 12.2 Architettura di Raccolta e Analisi

Un'infrastruttura di flow analysis enterprise comprende generatori (router, switch, firewall), collector/aggregatori e piattaforme di analisi.

```
 ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
 │ Router  │  │ Switch  │  │Firewall │  │  vSwitch│
 │ NetFlow │  │ sFlow   │  │ IPFIX   │  │  IPFIX  │
 └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘
      │            │            │             │
      └────────────┴────────────┴─────────────┘
                         │
                    ┌────┴─────┐
                    │Flow      │
                    │Collector │
                    │(nfdump,  │
                    │GoFlow2,  │
                    │Logstash) │
                    └────┬─────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────┴─────┐       ┌──────┴──────┐
         │OpenSearch │       │ Grafana /   │
         │Indicizzaz.│       │ Kibana      │
         │e ricerca  │       │ Dashboard   │
         └──────────┘       └─────────────┘
```

**Strumenti di collection open-source:**

- **nfdump/nfcapd**: collector tradizionale per NetFlow/IPFIX, salva in formato binario proprietario, query via nfdump CLI. Robusto e maturo, ideale per ambienti con volumi moderati.
- **GoFlow2**: collector moderno scritto in Go, supporta NetFlow v5/v9, IPFIX e sFlow. Output in JSON, Kafka o protobuf. Progettato per ambienti cloud-native e pipeline Kafka.
- **pmacct**: collector flessibile che supporta tutti i protocolli di flusso e può scrivere direttamente in database SQL, Kafka o file.

### 12.3 Detection Basata su Flussi

I dati di flusso, pur mancando di visibilità sul payload, permettono detection efficaci basate su pattern di connettività e volumi.

**Anomalie rilevabili con flow data:**

| Anomalia | Indicatore nel Flusso | Soglia Tipica |
|----------|----------------------|---------------|
| Port scan orizzontale | Singolo source IP, molti dest IP, stessa porta | >50 dest IP in 60s |
| Port scan verticale | Singolo source IP, singolo dest IP, molte porte | >30 porte in 60s |
| DDoS volumetrico | Alto volume di pacchetti/byte verso singolo dest | >10x baseline |
| Beaconing C2 | Connessioni periodiche verso dest esterno | Intervallo regolare, basso CV |
| Data exfiltration | Alto volume upload verso singola destinazione | >3 sigma sopra media |
| DNS tunneling | Alto numero di query DNS verso singolo dominio | >100 query/min per dominio |
| Lateral movement | Connessioni interne anomale (workstation→workstation) | Nuove coppie src/dst non nella baseline |
| Brute force | Molte connessioni brevi verso stessa porta | >20 connessioni fallite in 60s |

```bash
# Esempio nfdump — identificare top talker per volume
nfdump -r /data/nfcapd.202601240000 -s srcip/bytes -n 20

# Identificare connessioni su porte non standard
nfdump -r /data/nfcapd.202601240000 'dst port > 1024 and proto tcp and flags S \
  and not dst port in [8080, 8443, 3389, 5900]' -s dstport/flows

# Identificare flussi con durata anomala (beaconing persistente)
nfdump -r /data/nfcapd.202601240000 'duration > 3600' -o extended \
  -s record/bytes -n 50

# Identificare asymmetric flows (upload >> download, possibile exfiltration)
nfdump -r /data/nfcapd.202601240000 -A srcip,dstip \
  'src net 10.0.0.0/8 and not dst net 10.0.0.0/8 and bytes > 100M' \
  -o 'fmt:%sa,%da,%ibyt,%obyt' | \
  awk -F, '$3 > $4 * 5 {print "ANOMALY: "$1" -> "$2" upload="$3" download="$4}'
```

### 12.4 Combinare Flow Data e Full Packet Capture

La strategia ottimale combina flow data su tutta la rete con packet capture selettivo nei punti strategici:

1. **Flow data ovunque**: Abilitare NetFlow/IPFIX/sFlow su tutti i router, switch e firewall. Costo storage minimo, copertura totale. Utilizzare per baseline, anomaly detection, capacity planning.
2. **Full pcap ai chokepoint**: Deployare Arkime/Zeek/Suricata agli ingressi/uscite della rete, ai confini tra segmenti ad alto valore (DMZ, server farm, database tier), e ai punti di interconnessione con partner/fornitori.
3. **Trigger-based capture**: Configurare cattura PCAP automatica quando i flow data rilevano anomalie — un flusso sospetto rilevato via NetFlow triggera la cattura full-packet per i successivi 5 minuti su quel segmento.

---

## 13. NDR nel Cloud — AWS Azure GCP

### 13.1 Sfide del Monitoraggio di Rete nel Cloud

Il monitoraggio del traffico di rete in ambienti cloud presenta sfide fondamentalmente diverse rispetto agli ambienti on-premise:

- **Nessun accesso fisico**: Non è possibile installare TAP hardware o configurare SPAN port su switch fisici. Tutto il mirroring del traffico dipende dalle funzionalità native del cloud provider.
- **Traffico est-ovest invisibile**: Il traffico tra istanze nella stessa subnet o nello stesso VPC spesso non attraversa un punto di ispezione. Le comunicazioni intra-host (tra container sullo stesso nodo) sono completamente invisibili ai metodi tradizionali.
- **Costi di mirroring**: Il traffic mirroring nel cloud genera costi significativi sia per l'elaborazione che per il trasferimento dati, specialmente cross-availability-zone.
- **Ambienti effimeri**: Container, funzioni serverless e istanze auto-scaling appaiono e scompaiono in secondi. L'infrastruttura di monitoraggio deve adattarsi dinamicamente.
- **Encryption pervasiva**: mTLS tra microservizi, TLS per database gestiti, HTTPS per API interne — la percentuale di traffico cifrato in ambienti cloud è tipicamente superiore al 95%.

### 13.2 AWS — VPC Flow Logs e Traffic Mirroring

**VPC Flow Logs** catturano metadata di connessione (simili a NetFlow) per ogni interfaccia di rete elastica (ENI) nel VPC. Campi disponibili: account-id, interface-id, srcaddr, dstaddr, srcport, dstport, protocol, packets, bytes, start, end, action (ACCEPT/REJECT), log-status.

A partire dalla versione 5, i VPC Flow Logs supportano campi aggiuntivi: vpc-id, subnet-id, instance-id, tcp-flags, type (IPv4/IPv6), pkt-srcaddr, pkt-dstaddr, region, az-id, sublocation-type, sublocation-id. Questi campi estesi permettono analisi più granulari come l'identificazione di traffico cross-AZ anomalo.

```bash
# Query Athena per identificare top talker con traffico rifiutato
# Indicativo di scanning o tentativi di accesso non autorizzato
SELECT srcaddr, dstaddr, dstport, SUM(packets) as total_packets,
       SUM(bytes) as total_bytes, COUNT(*) as flow_count
FROM vpc_flow_logs
WHERE action = 'REJECT'
  AND start > to_unixtime(current_timestamp - interval '24' hour)
GROUP BY srcaddr, dstaddr, dstport
HAVING COUNT(*) > 100
ORDER BY flow_count DESC
LIMIT 50;

# Identificare comunicazioni verso porte non standard
SELECT srcaddr, dstaddr, dstport, protocol, SUM(bytes) as total_bytes
FROM vpc_flow_logs
WHERE action = 'ACCEPT'
  AND dstport NOT IN (80, 443, 22, 53, 123, 8080, 8443)
  AND protocol = 6  -- TCP
  AND start > to_unixtime(current_timestamp - interval '24' hour)
GROUP BY srcaddr, dstaddr, dstport, protocol
ORDER BY total_bytes DESC
LIMIT 100;
```

**VPC Traffic Mirroring** fornisce una copia completa del traffico (full packet capture) reindirizzata verso un target di monitoraggio (ENI o Network Load Balancer). Limitazioni: non disponibile su tutti i tipi di istanza (limitato a istanze basate su Nitro), costo aggiuntivo per ogni ENI monitorata, impatto sulle prestazioni dell'istanza sorgente.

**Corelight Flow Monitoring per AWS** (annunciato ottobre 2025) normalizza i dati AWS VPC Flow Logs nel formato Zeek, permettendo l'applicazione di logiche di detection uniformi tra ambienti on-premise e cloud. Questo approccio elimina la necessità di parsing personalizzato e consente ai SOC di utilizzare gli stessi dashboard e workflow investigativi.

### 13.3 Azure — NSG Flow Logs e Virtual Network TAP

**NSG Flow Logs** (Network Security Group) registrano informazioni sui flussi IP in ingresso e uscita attraverso un NSG. I log vengono salvati in Azure Storage e possono essere analizzati con Azure Traffic Analytics, che fornisce visualizzazioni su mappa geografica, top talker e anomalie di traffico.

Azure NSG Flow Logs versione 2 aggiunge informazioni sullo stato del flusso (begin/continuing/end) e sul throughput (bytes e pacchetti per direzione), fornendo una granularità maggiore per l'analisi delle sessioni rispetto alla versione 1.

**Azure Virtual Network TAP** permette il mirroring del traffico verso un'appliance di monitoraggio. A differenza del traffic mirroring AWS, Azure vTAP opera a livello di interfaccia di rete virtuale e supporta il mirroring bidirezionale.

### 13.4 GCP — Packet Mirroring e VPC Flow Logs

**GCP Packet Mirroring** crea una copia del traffico di rete e la invia a un collector (tipicamente un gruppo di istanze con Zeek/Suricata). Supporta filtri basati su protocollo, direzione e subnet per limitare il volume di traffico duplicato.

**GCP VPC Flow Logs** campionano i flussi di rete a livello di VM e forniscono metadata di connessione. Il tasso di campionamento è configurabile (da 1.0 = tutti i flussi a 0.1 = 10% dei flussi), permettendo un bilanciamento tra costo e visibilità.

### 13.5 NDR Cloud-Native — Strategie di Deployment

L'implementazione di un NDR stack nel cloud richiede un approccio stratificato:

```
 Strategia NDR Multi-Cloud:

 ┌──────────────────────────────────────────────────────────┐
 │              SIEM / SOAR CENTRALIZZATO                    │
 │   Correlazione cross-cloud, incident response             │
 ├──────────────────────────────────────────────────────────┤
 │  AWS Region      │  Azure Region    │  GCP Region         │
 │                  │                  │                     │
 │  VPC Flow Logs   │  NSG Flow Logs   │  VPC Flow Logs     │
 │  → S3 → Athena   │  → Storage →     │  → BigQuery        │
 │                  │  Traffic Analytics│                     │
 │  Traffic Mirror  │  vTAP            │  Packet Mirroring  │
 │  → Zeek/Suricata │  → Zeek/Suricata │  → Zeek/Suricata   │
 │  (EC2 fleet)     │  (VM fleet)      │  (GCE fleet)       │
 │                  │                  │                     │
 │  GuardDuty       │  Defender for    │  Security Command   │
 │  (AWS NDR)       │  Cloud (Azure    │  Center + Chronicle │
 │                  │  NDR nativo)     │  (GCP NDR nativo)   │
 └──────────────────┴──────────────────┴─────────────────────┘
```

**Considerazioni chiave per il deployment cloud:**

1. **Costi di data transfer**: Il traffico cross-AZ e cross-region per il mirroring genera costi significativi. Posizionare i sensori nella stessa AZ delle risorse monitorate.
2. **Auto-scaling dei sensori**: I sensori NDR devono scalare automaticamente con il traffico cloud. Utilizzare Auto Scaling Group (AWS), VMSS (Azure) o Managed Instance Group (GCP).
3. **Integrazione con servizi nativi**: Combinare NDR open-source (Zeek, Suricata) con servizi di sicurezza nativi del cloud (GuardDuty, Defender, Security Command Center) per massimizzare la copertura.
4. **Pipeline di log unificata**: Normalizzare tutti i log di rete (VPC Flow Logs, Zeek logs, Suricata EVE JSON) in un formato comune e inviarli a un SIEM centralizzato per la correlazione cross-cloud.

---

## 14. Mappatura MITRE ATT&CK per Detection di Rete

### 14.1 Tecniche Rilevabili via Traffico di Rete

Il framework MITRE ATT&CK cataloga le tattiche, tecniche e procedure (TTP) utilizzate dagli avversari. Molte di queste tecniche generano artefatti osservabili nel traffico di rete, rendendo l'NDR uno strumento fondamentale per la detection basata su ATT&CK. Nel 2025, la tecnica T1071 (Application Layer Protocol) ha rappresentato il 19% di tutti i campioni malware analizzati, confermandosi come la tecnica C2 più diffusa.

### 14.2 Mappatura Tactic-Technique-Detection

La tabella seguente mappa le principali tattiche ATT&CK alle tecniche rilevabili tramite analisi del traffico di rete, con gli strumenti e i data source specifici.

| Tactic | Technique ID | Tecnica | Artefatto di Rete | Strumento di Detection |
|--------|-------------|---------|-------------------|----------------------|
| Reconnaissance | T1046 | Network Service Discovery | SYN scan, connessioni a molte porte | Zeek conn.log, Suricata rule |
| Reconnaissance | T1018 | Remote System Discovery | Query DNS/LDAP massive, ARP sweep | Zeek dns.log, Zeek ldap.log |
| Initial Access | T1566.002 | Spearphishing Link | URL verso domini registrati di recente | Zeek http.log, DNS age check |
| Execution | T1059.001 | PowerShell | HTTP con User-Agent PowerShell | Zeek http.log user_agent field |
| Persistence | T1133 | External Remote Services | VPN/RDP da IP insoliti | Flow data, Zeek conn.log |
| Lateral Movement | T1021.002 | SMB/Windows Admin Shares | Accesso a ADMIN$, C$, IPC$ | Zeek smb_mapping.log |
| Lateral Movement | T1021.001 | Remote Desktop Protocol | RDP workstation→workstation | Flow data porta 3389 |
| C2 | T1071.001 | Application Layer Protocol: Web | HTTP/S beaconing periodico | Zeek conn.log, beaconing analysis |
| C2 | T1071.004 | Application Layer Protocol: DNS | DNS tunneling, DGA | Zeek dns.log, entropia query |
| C2 | T1573 | Encrypted Channel | TLS con JA3 anomalo, cert self-signed | Zeek ssl.log, JA3/JA4 matching |
| C2 | T1572 | Protocol Tunneling | ICMP tunneling, DNS over TCP | Suricata, payload size analysis |
| Exfiltration | T1048 | Exfiltration Over Alternative Protocol | Dati su DNS, ICMP, NTP | Zeek, anomalia dimensione pacchetti |
| Exfiltration | T1041 | Exfiltration Over C2 Channel | Alto upload su sessione C2 | Zeek conn.log orig_bytes |
| Defense Evasion | T1001.003 | Protocol Impersonation | HTTP su porta 53, SSH su 443 | Suricata protocol detection |
| Credential Access | T1110 | Brute Force | Molti tentativi auth falliti | Zeek kerberos.log, ssh.log |
| Discovery | T1082 | System Information Discovery | Query LDAP specifiche | Zeek ldap.log |

### 14.3 Regole di Detection Allineate ad ATT&CK

**T1071.001 — Web Protocol C2 (HTTP/S Beaconing):**

```yaml
# Suricata — detection di beaconing HTTP con intervallo regolare
alert http $HOME_NET any -> $EXTERNAL_NET any (
    msg:"ATT&CK T1071.001 Potential HTTP C2 Beaconing";
    flow:established,to_server;
    http.method; content:"GET";
    http.uri; content:"/"; depth:1;
    threshold:type both, track by_src, count 50, seconds 300;
    reference:url,attack.mitre.org/techniques/T1071/001;
    classtype:trojan-activity;
    sid:2030200; rev:1;
    metadata:mitre_attack T1071.001;
)
```

**T1048.001 — Exfiltration Over Symmetric Encrypted Protocol:**

```zeek
# Zeek — detection di upload anomalo su canale cifrato
module ExfilDetector;

export {
    redef enum Notice::Type += { Large_Encrypted_Upload };
    const upload_threshold = 50000000 &redef;  # 50 MB
}

event connection_state_remove(c: connection)
    {
    if ( ! Site::is_local_addr(c$id$orig_h) )
        return;
    if ( Site::is_local_addr(c$id$resp_h) )
        return;

    # Connessione TLS con alto volume di upload
    if ( c$conn?$orig_ip_bytes &&
         c$conn$orig_ip_bytes > upload_threshold &&
         "SSL" in c$conn$service )
        {
        NOTICE([$note=Large_Encrypted_Upload,
                $msg=fmt("T1048.001: Large encrypted upload: %s -> %s:%s (%d bytes)",
                         c$id$orig_h, c$id$resp_h, c$id$resp_p,
                         c$conn$orig_ip_bytes),
                $conn=c,
                $identifier=cat(c$id$orig_h, c$id$resp_h)]);
        }
    }
```

**T1021.002 — Lateral Movement via SMB Admin Shares:**

```zeek
# Zeek — detection di accesso a share amministrative da workstation
module LateralMovementDetector;

export {
    redef enum Notice::Type += { Admin_Share_Access };
}

event smb2_tree_connect_request(c: connection, hdr: SMB2::Header,
                                 path: string)
    {
    if ( /ADMIN\$|C\$|IPC\$/ in path )
        {
        # Verificare se la sorgente è una workstation (non un server noto)
        if ( Site::is_local_addr(c$id$orig_h) &&
             Site::is_local_addr(c$id$resp_h) )
            {
            NOTICE([$note=Admin_Share_Access,
                    $msg=fmt("T1021.002: Admin share access: %s -> %s path=%s",
                             c$id$orig_h, c$id$resp_h, path),
                    $conn=c,
                    $identifier=cat(c$id$orig_h, c$id$resp_h, path)]);
            }
        }
    }
```

### 14.4 Dashboard ATT&CK per Network Detection

Un dashboard efficace per la detection basata su ATT&CK dovrebbe mappare ogni alert NDR alla tecnica ATT&CK corrispondente, fornendo:

- **Copertura ATT&CK**: Matrice visuale che mostra quali tecniche sono coperte dalle regole NDR attive e dove esistono lacune
- **Detection per Tactic**: Conteggio degli alert raggruppati per tactic (Reconnaissance, Lateral Movement, C2, Exfiltration) per identificare le fasi dell'attacco in corso
- **Timeline correlata**: Visualizzazione temporale degli alert ATT&CK per ricostruire la kill chain dell'avversario
- **Confidence scoring**: Ogni detection ha un livello di confidenza (High/Medium/Low) basato sulla specificità della regola e il contesto

### 14.5 Integrazione NDR-SIEM-SOAR

Le piattaforme NDR moderne non operano in isolamento ma si integrano nell'ecosistema SOC più ampio tramite integrazioni con SIEM, SOAR, EDR e XDR.

**NDR → SIEM:** I log Zeek e gli alert Suricata vengono ingestiti nel SIEM (Splunk, Elastic SIEM, Microsoft Sentinel, Google SecOps) dove vengono correlati con log da endpoint, identità, cloud e applicazioni. La correlazione cross-source è fondamentale per ridurre i falsi positivi e aumentare la confidenza delle detection.

**NDR → SOAR:** Le detection NDR ad alta confidenza triggerano playbook SOAR automatizzati. Un alert di beaconing C2 confermato può automaticamente:
1. Bloccare l'IP di destinazione sul firewall perimetrale
2. Isolare l'endpoint compromesso tramite API EDR
3. Creare un ticket di incident nel sistema di case management
4. Notificare il team di incident response
5. Avviare la raccolta forense sull'endpoint

**NDR + EDR = XDR:** La convergenza tra NDR ed EDR è il fondamento dell'Extended Detection and Response (XDR). Il mercato SIEM globale, che incorpora funzionalità XDR, è previsto raggiungere i 13,55 miliardi di dollari entro il 2029 con un CAGR del 13,7%. Piattaforme come Microsoft Sentinel, Palo Alto XSIAM e Google SecOps stanno convergendo SIEM, SOAR e XDR in piattaforme unificate.

---

## 15. eBPF e XDP per Monitoraggio di Rete

### 15.1 Fondamenti eBPF per Network Security

eBPF (extended Berkeley Packet Filter) è una tecnologia del kernel Linux che permette l'esecuzione di programmi verificati e sandboxed direttamente nel kernel, senza modificare il codice sorgente del kernel o caricare moduli kernel. Per il monitoraggio di rete, eBPF offre vantaggi fondamentali rispetto agli approcci tradizionali basati su libpcap.

**Vantaggi di eBPF rispetto alla cattura tradizionale:**

| Aspetto | libpcap/af_packet | eBPF |
|---------|-------------------|------|
| Punto di hook | Post-networking stack | Pre o post stack (configurabile) |
| Overhead | Copia pacchetto user→kernel | Elaborazione in-kernel, zero-copy |
| Filtraggio | BPF classico (limitato) | Programmi arbitrari con mappe |
| Stato | Stateless per pacchetto | State persistente tramite eBPF maps |
| Aggregazione | In userspace | In-kernel (riduce dati verso userspace) |
| Visibilità | Solo pacchetti di rete | Rete + syscall + stack traces |

**Hook points eBPF rilevanti per il monitoraggio di rete:**

```
 Pacchetto in ingresso → percorso nel kernel:

 ┌──────┐    ┌───────┐    ┌──────────┐    ┌────────┐    ┌──────────┐
 │  NIC │───>│  XDP  │───>│  TC      │───>│Netfilter│───>│ Socket  │
 │      │    │ (pre- │    │ (traffic │    │(iptables│    │ (app    │
 │      │    │  stack)│    │  control)│    │/nftables│    │  layer) │
 └──────┘    └───────┘    └──────────┘    └────────┘    └──────────┘
              eBPF          eBPF            eBPF          eBPF
              hook 1        hook 2          hook 3        hook 4

 XDP: massima performance, prima del networking stack
 TC:  dopo allocazione sk_buff, pieno accesso ai metadati L2-L4
 Socket: visibilità a livello applicativo, con contesto processo
```

**XDP (eXpress Data Path)** è il punto di hook più precoce nel percorso di ricezione dei pacchetti, operando direttamente sul driver di rete prima che il pacchetto entri nel networking stack del kernel. Azioni disponibili in XDP:

- `XDP_PASS`: Passare il pacchetto allo stack di rete normale
- `XDP_DROP`: Scartare il pacchetto immediatamente (anti-DDoS)
- `XDP_TX`: Ritrasmettere il pacchetto sulla stessa interfaccia
- `XDP_REDIRECT`: Reindirizzare verso altra interfaccia o CPU
- `XDP_ABORTED`: Scartare con errore (debug)

### 15.2 Cilium e Hubble — Osservabilità Kubernetes

Cilium è una piattaforma di networking, sicurezza e osservabilità per Kubernetes basata interamente su eBPF. Hubble è il componente di osservabilità di Cilium che fornisce visibilità profonda sul traffico di rete tra i servizi Kubernetes.

**Architettura Cilium/Hubble:**

```
 ┌──────────────────────────────────────────────────────────┐
 │                    HUBBLE UI                              │
 │  Service map ─ Flow visualization ─ Policy verdicts       │
 ├──────────────────────────────────────────────────────────┤
 │                  HUBBLE RELAY                             │
 │  Aggrega dati da tutti i nodi ─ API gRPC                  │
 ├──────────────────────────────────────────────────────────┤
 │  Nodo K8s 1           │  Nodo K8s 2          │  Nodo N   │
 │  ┌─────────────────┐  │  ┌─────────────────┐ │          │
 │  │ Cilium Agent     │  │  │ Cilium Agent     │ │          │
 │  │ + Hubble Server  │  │  │ + Hubble Server  │ │          │
 │  │                  │  │  │                  │ │          │
 │  │ eBPF programs:   │  │  │ eBPF programs:   │ │          │
 │  │ - TC classifiers │  │  │ - TC classifiers │ │          │
 │  │ - Socket hooks   │  │  │ - Socket hooks   │ │          │
 │  │ - XDP programs   │  │  │ - XDP programs   │ │          │
 │  └─────────────────┘  │  └─────────────────┘ │          │
 └──────────────────────────────────────────────────────────┘
```

Hubble registra metadata per ogni flusso di rete: source/destination pod, namespace, service, IP, porta, protocollo applicativo (HTTP, gRPC, DNS, Kafka), latenza, codice di risposta, e il verdetto della network policy Cilium (FORWARDED, DROPPED, AUDIT).

```bash
# Hubble CLI — osservare i flussi in tempo reale
hubble observe --namespace production --protocol http

# Filtrare traffico DNS con risposte fallite
hubble observe --protocol dns --verdict DROPPED

# Visualizzare flussi verso servizi esterni (egress)
hubble observe --to-identity world --namespace production

# Esportare flussi per analisi offline
hubble observe --output json --last 1h > hubble_flows.json

# Metriche Prometheus esposte da Hubble
# hubble_flows_processed_total
# hubble_drop_total{reason="POLICY_DENIED"}
# hubble_dns_queries_total
# hubble_http_requests_total{method="POST", code="200"}
```

### 15.3 Pixie — Osservabilità Applicativa senza Instrumentazione

Pixie è uno strumento open-source di osservabilità per Kubernetes che utilizza eBPF per catturare automaticamente telemetria a livello applicativo senza richiedere instrumentazione del codice, sidecar proxy o modifiche alle applicazioni.

**Protocolli automaticamente rilevati e parsati da Pixie:**

| Protocollo | Dati Estratti |
|-----------|--------------|
| HTTP/1.1 e HTTP/2 | Request/response completi, latenza, status code |
| gRPC | Metodo, latenza, codice di errore |
| DNS | Query, risposta, latenza di risoluzione |
| MySQL | Query SQL, latenza, righe restituite |
| PostgreSQL | Query, latenza, errori |
| Redis | Comandi, latenza |
| Kafka | Topic, partition, offset, latenza |
| AMQP | Exchange, routing key, payload |

La differenza fondamentale tra Pixie e Hubble è il livello di osservabilità: Hubble opera principalmente a livello di rete (L3/L4 con protocollo L7 parziale), mentre Pixie opera a livello applicativo completo, catturando il contenuto delle request/response e le metriche di performance per-query. Pixie raggiunge questa visibilità tramite hook eBPF sulle syscall di rete (read, write, send, recv) e sulle funzioni delle librerie TLS (OpenSSL, BoringSSL, Go crypto/tls) per decifrare il traffico TLS senza certificati o chiavi.

### 15.4 eBPF per Network Security Monitoring

Oltre alle piattaforme Kubernetes, eBPF viene utilizzato direttamente per il network security monitoring su host Linux tradizionali tramite strumenti specializzati.

**Tracee (Aqua Security)** è un runtime security tool basato su eBPF che monitora syscall, eventi del kernel e attività di rete. Per il network monitoring, Tracee cattura eventi DNS, connessioni di rete e attività di socket, correlandoli con il contesto del processo (PID, container ID, immagine container).

**bpftrace** permette di scrivere programmi eBPF ad-hoc per il monitoraggio e il troubleshooting di rete:

```bash
# bpftrace — tracciare tutte le connessioni TCP
bpftrace -e 'kprobe:tcp_connect {
    $sk = (struct sock *)arg0;
    $daddr = ntop($sk->__sk_common.skc_daddr);
    $dport = $sk->__sk_common.skc_dport;
    printf("%-6d %-16s %-16s %-5d\n",
           pid, comm, $daddr, $dport);
}'

# Tracciare accept() per nuove connessioni in ingresso
bpftrace -e 'kretprobe:inet_csk_accept {
    $sk = (struct sock *)retval;
    $saddr = ntop($sk->__sk_common.skc_rcv_saddr);
    $sport = $sk->__sk_common.skc_num;
    printf("%-6d %-16s accepted from %s:%d\n",
           pid, comm, $saddr, $sport);
}'

# Misurare latenza DNS per query
bpftrace -e 'kprobe:udp_sendmsg /comm == "systemd-resolve"/ {
    @start[tid] = nsecs;
}
kprobe:udp_recvmsg /comm == "systemd-resolve" && @start[tid]/ {
    printf("DNS latency: %d us\n", (nsecs - @start[tid]) / 1000);
    delete(@start[tid]);
}'
```

### 15.5 XDP per Mitigazione DDoS e Filtraggio ad Alta Velocità

XDP opera al livello più basso del networking stack Linux, permettendo il filtraggio dei pacchetti a velocità di linea (10-100 Gbps) con latenza nell'ordine dei microsecondi. Questo lo rende ideale per la mitigazione DDoS in-kernel senza richiedere hardware dedicato.

```c
/* Programma XDP per mitigazione SYN flood — esempio semplificato */
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>

/* Mappa per contare SYN per source IP */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 100000);
    __type(key, __u32);      /* source IP */
    __type(value, __u64);    /* SYN count */
} syn_count SEC(".maps");

/* Soglia SYN per IP al secondo */
#define SYN_THRESHOLD 100

SEC("xdp")
int xdp_syn_flood_mitigate(struct xdp_md *ctx)
{
    void *data_end = (void *)(long)ctx->data_end;
    void *data = (void *)(long)ctx->data;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;

    if (eth->h_proto != __constant_htons(ETH_P_IP))
        return XDP_PASS;

    struct iphdr *iph = (void *)(eth + 1);
    if ((void *)(iph + 1) > data_end)
        return XDP_PASS;

    if (iph->protocol != IPPROTO_TCP)
        return XDP_PASS;

    struct tcphdr *tcph = (void *)iph + (iph->ihl * 4);
    if ((void *)(tcph + 1) > data_end)
        return XDP_PASS;

    /* Solo SYN puri (no SYN-ACK) */
    if (!(tcph->syn) || tcph->ack)
        return XDP_PASS;

    __u32 src_ip = iph->saddr;
    __u64 *count = bpf_map_lookup_elem(&syn_count, &src_ip);

    if (count) {
        (*count)++;
        if (*count > SYN_THRESHOLD) {
            /* Drop — troppe SYN da questo IP */
            return XDP_DROP;
        }
    } else {
        __u64 init_count = 1;
        bpf_map_update_elem(&syn_count, &src_ip, &init_count, BPF_ANY);
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

```bash
# Caricare il programma XDP
ip link set dev eth0 xdp obj xdp_syn_flood.o sec xdp

# Verificare lo stato
ip link show dev eth0
# output include: prog/xdp id 42

# Monitorare i contatori XDP
bpftool map dump id 15  # dump della mappa syn_count

# Statistiche XDP
bpftool prog show id 42

# Rimuovere il programma XDP
ip link set dev eth0 xdp off
```

### 15.6 Confronto eBPF vs Approcci Tradizionali per NDR

| Criterio | libpcap/SPAN tradizionale | eBPF/XDP |
|----------|--------------------------|----------|
| Deployment | Hardware TAP + server dedicato | Software su host esistenti |
| Visibilità container | Limitata (solo traffico che esce dal nodo) | Completa (incluso traffico intra-nodo) |
| Contesto processo | Assente (solo dati di rete) | Disponibile (PID, container, binary) |
| Scalabilità cloud | Dipende dal provider (VPC mirroring) | Nativo su ogni nodo Linux |
| Performance overhead | Moderato (copia pacchetti in userspace) | Basso (elaborazione in-kernel) |
| Capacità di risposta | Passivo (solo monitoraggio) | Attivo (XDP_DROP per mitigazione) |
| Maturità | 30+ anni, estremamente stabile | In rapida evoluzione, API meno stabili |
| Visibilità TLS | Richiede chiavi o MITM proxy | Può hookare librerie TLS per decifrare |
| Supporto OS | Linux, BSD, Windows | Solo Linux (kernel 4.15+) |

eBPF non sostituisce l'approccio TAP/SPAN tradizionale ma lo complementa. La combinazione ideale per un NDR enterprise moderno utilizza TAP/SPAN per la cattura full-packet ai chokepoint di rete con Arkime/Zeek/Suricata, e eBPF sui singoli host e nodi Kubernetes per la visibilità est-ovest, il contesto applicativo e la mitigazione automatica.

---

> **Riferimenti principali:**
>
> - Ptacek, T. & Newsham, T. (1998). *Insertion, Evasion, and Denial of Service: Eluding Network Intrusion Detection.* Secure Networks.
> - Zeek Documentation — https://docs.zeek.org/
> - Suricata Documentation — https://docs.suricata.io/
> - Wireshark Display Filter Reference — https://www.wireshark.org/docs/dfref/
> - JA3 — https://github.com/salesforce/ja3
> - JA4+ — https://github.com/FoxIO-LLC/ja4
> - MITRE ATT&CK Network-Based Techniques — https://attack.mitre.org/
> - RFC 8446 — The Transport Layer Security (TLS) Protocol Version 1.3
> - RFC 9261 — TLS Encrypted Client Hello
> - ET Open Ruleset — https://rules.emergingthreats.net/
> - malware-traffic-analysis.net — Brad Duncan's PCAP exercises
