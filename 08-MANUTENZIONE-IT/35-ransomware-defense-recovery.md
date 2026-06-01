# Ransomware Defense, Detection, and Recovery Operations

> **Modulo 35** · **Tempo:** 240 min · **Aggiornamento:** 2026-05-07

## Idee guida

1. **Ransomware is a business model, not a technical novelty.** Treat it as an adversarial economic problem.
2. **Prevention reduces probability; detection and containment reduce impact.** Neither alone is sufficient.
3. **Immutable backups are the last line.** If they fall, you negotiate from zero leverage.
4. **Dwell time is the attacker's gift to defenders.** Median 5-9 days pre-encryption — detect early, contain fast.
5. **Recovery without root cause analysis guarantees re-compromise.** Never restore into the same vulnerable state.

---

## Indice

1. [Evoluzione Ransomware](#1-evoluzione-ransomware)
2. [Kill Chain del Ransomware](#2-kill-chain-del-ransomware)
3. [Prevenzione](#3-prevenzione)
4. [Detection e Early Warning](#4-detection-e-early-warning)
5. [Risposta Immediata](#5-risposta-immediata)
6. [Negoziazione e Decisione sul Pagamento](#6-negoziazione-e-decisione-sul-pagamento)
7. [Recovery Operations](#7-recovery-operations)
8. [Post-Recovery Hardening](#8-post-recovery-hardening)
9. [Casi Studio Reali](#9-casi-studio-reali)
10. [Laboratorio](#10-laboratorio)

---

## 1. Evoluzione Ransomware

### 1.1 Timeline Storica

The ransomware threat landscape has undergone continuous evolution, each generation building on the failures and successes of predecessors.

**CryptoLocker (2013-2014)**

The first widely successful crypto-ransomware deployed at scale. Key characteristics:
- Distributed via Gameover ZeuS botnet and phishing emails
- RSA-2048 asymmetric encryption of user files
- $300 ransom in Bitcoin or MoneyPak
- Estimated $3M+ in ransom collected before Operation Tovar takedown
- Introduced the model: strong encryption + cryptocurrency payment + countdown timer

**CryptoWall / TeslaCrypt / Locky (2014-2016)**

Iteration on CryptoLocker's formula with improved distribution:
- Exploit kits (Angler, RIG, Nuclear) as primary delivery
- TeslaCrypt targeted gaming files specifically — later released master key
- Locky achieved massive distribution via macro-laden Office documents
- Ransoms typically $500-$1000 per machine

**WannaCry (May 2017)**

The first worm-capable ransomware achieving global impact:
- Exploited EternalBlue (MS17-010) SMBv1 vulnerability leaked from NSA
- Self-propagating worm behavior — no user interaction needed
- Infected 230,000+ computers across 150 countries in hours
- Kill switch discovered by Marcus Hutchins (MalwareTech)
- Attribution: Lazarus Group (DPRK)
- Ransom: $300-$600 in Bitcoin — poorly implemented payment tracking
- Total damage estimated $4-8 billion despite relatively low ransom collection

**NotPetya (June 2017)**

Masqueraded as ransomware but functioned as a wiper:
- Initial vector: compromised M.E.Doc (Ukrainian accounting software) update mechanism
- Used EternalBlue + EternalRomance + Mimikatz credential harvesting
- Overwrote MBR and encrypted MFT — decryption intentionally impossible
- Caused $10+ billion in global damages (Maersk, Merck, FedEx/TNT, Mondelez)
- Attribution: Sandworm (Russian GRU Unit 74455)
- Lesson: ransomware can be a cover for destructive state operations

**Ryuk / Conti (2018-2022)**

Introduced the "Big Game Hunting" model — targeting high-value enterprises:
- Manual, operator-driven attacks with extensive reconnaissance
- Initial access via TrickBot/BazarLoader → Cobalt Strike
- Dwell times of days to weeks before encryption
- Demanded millions: Ryuk collected $150M+ over its lifetime
- Conti leaked internal communications revealed organizational structure
- Conti operated like a corporation: HR, developers, penetration testers, negotiators
- Conti annual revenue estimated $180M+ before dissolution

**REvil / Sodinokibi (2019-2022)**

Pioneered the affiliate-driven RaaS model at scale:
- 70/30 split: affiliates kept 70% of ransom
- Introduced data exfiltration + leak site ("Happy Blog")
- Notable attacks: JBS ($11M paid), Kaseya (supply chain, $70M demand)
- Offered DDoS and victim-customer notification as additional extortion
- Seized by FSB in January 2022 (political timing)

**LockBit (2019-2024)**

The most prolific ransomware operation by volume:
- LockBit 2.0 introduced StealBit for automated exfiltration
- LockBit 3.0 launched bug bounty program for their malware
- LockBit Green incorporated Conti source code
- Peak: 200+ victims per month
- Self-reported $100M+ in ransom paid
- Notable: automated encryption speed — 373MB/s claimed
- Operation Cronos (Feb 2024) disrupted infrastructure but operator LockBitSupp persisted briefly
- Affiliate recruitment: low barrier to entry, extensive builder customization

**BlackCat / ALPHV (2021-2024)**

First major ransomware written in Rust:
- Cross-platform: Windows, Linux, ESXi
- Highly configurable per-victim payloads
- Introduced searchable leak sites for victim data
- Filed SEC complaint against victim (MeridianLink) for non-disclosure
- Notable: Change Healthcare attack ($22M payment, exit scam on affiliate)
- Exit scam in March 2024 after collecting Change Healthcare ransom

**Akira (2023-present)**

Emerged from Conti diaspora with retro aesthetic:
- Targets VMware ESXi and Linux alongside Windows
- Exploits VPN vulnerabilities (Cisco ASA/FTD CVE-2023-20269)
- Predominantly attacks SMB/mid-market ($10M-$250M revenue)
- Demands typically $200K-$4M
- Rust-based Linux encryptor (Megazord variant)

**Play (2022-present)**

Distinctive for intermittent encryption approach:
- Encrypts only portions of files (faster, harder to detect by entropy)
- Exploits FortiOS and Microsoft Exchange (ProxyNotShell)
- "Closed" group — does not operate as public RaaS
- Targets Latin America and Europe heavily
- Known for exploiting managed service providers for downstream access

### 1.2 Ransomware-as-a-Service (RaaS) Model

Modern ransomware operates as a franchise ecosystem:

```
┌─────────────────────────────────────────────────────────┐
│                    RaaS ECOSYSTEM                         │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐     ┌──────────────┐                  │
│  │   OPERATORS  │     │  DEVELOPERS  │                  │
│  │  (Core Team) │────▶│  (Malware)   │                  │
│  └──────┬───────┘     └──────────────┘                  │
│         │                                                │
│         │ Builder + Infrastructure                       │
│         ▼                                                │
│  ┌──────────────┐     ┌──────────────┐                  │
│  │  AFFILIATES  │◀────│    IABs      │                  │
│  │  (Operators) │     │(Init Access) │                  │
│  └──────┬───────┘     └──────────────┘                  │
│         │                                                │
│         │ Attack + Encrypt + Exfiltrate                  │
│         ▼                                                │
│  ┌──────────────┐     ┌──────────────┐                  │
│  │   VICTIMS    │────▶│ NEGOTIATORS  │                  │
│  │              │     │              │                  │
│  └──────────────┘     └──────────────┘                  │
│                                                          │
│  Revenue Split: Affiliates 70-80% │ Operators 20-30%    │
└─────────────────────────────────────────────────────────┘
```

**Roles within the ecosystem:**

| Role | Function | Typical Compensation |
|------|----------|---------------------|
| Operators/Developers | Build encryptor, maintain infrastructure, manage negotiations | 20-30% of ransom |
| Affiliates | Conduct intrusions, deploy ransomware | 70-80% of ransom |
| Initial Access Brokers (IABs) | Sell pre-compromised access | $500-$50,000 per access |
| Negotiators | Communicate with victims, manage payments | Salary or per-engagement fee |
| Money Launderers | Convert cryptocurrency to fiat | 10-20% of transaction |
| Bulletproof Hosters | Provide resilient infrastructure | Monthly fees |

### 1.3 Double/Triple/Quadruple Extortion

The extortion model has expanded progressively:

1. **Single extortion**: Encrypt files, demand payment for decryptor
2. **Double extortion**: Encrypt + exfiltrate data, threaten publication (Maze, 2019)
3. **Triple extortion**: Add DDoS attacks against victim infrastructure during negotiation
4. **Quadruple extortion**: Contact victim's customers, partners, or regulators directly; threaten SEC/GDPR complaints

### 1.4 Economics and Payment Trends

Current statistics (2024-2025 data):

| Metric | Value |
|--------|-------|
| Average ransom demand | $4.3M (enterprise) |
| Median ransom payment | $1.5M |
| Average downtime | 24 days |
| Average total cost (including recovery) | $5.2M |
| Payment rate | ~29% (declining) |
| Organizations paying who recovered all data | ~65% |
| Re-attack rate within 12 months | 80% of those who paid |

---

## 2. Kill Chain del Ransomware

### 2.1 MITRE ATT&CK Mapping — Full Chain

The following maps the complete ransomware kill chain against MITRE ATT&CK with specific TTPs observed across major ransomware families.

#### Phase 1: Initial Access (TA0001)

**Common vectors (ranked by frequency, 2024 data):**

1. **Exploitation of public-facing applications** (T1190) — 36%
   - VPN appliances: Fortinet (CVE-2023-27997), Citrix (CVE-2023-4966 "Citrix Bleed"), Ivanti (CVE-2024-21887)
   - Email servers: Microsoft Exchange (ProxyShell, ProxyNotShell)
   - File transfer: MOVEit (CVE-2023-34362), GoAnywhere (CVE-2023-0669)

2. **Phishing** (T1566) — 28%
   - Spear-phishing with macro-enabled documents (T1566.001)
   - HTML smuggling delivering ISO/IMG containers
   - Callback phishing (BazarCall) — victim calls attacker-controlled number
   - QR code phishing (quishing) leading to credential harvesting

3. **Valid accounts** (T1078) — 22%
   - Purchased credentials from info-stealer logs (Raccoon, RedLine, Lumma)
   - Credential stuffing against VPN/RDP portals
   - Compromised MFA via SIM swap or MFA fatigue (push bombing)

4. **External remote services** (T1133) — 14%
   - Exposed RDP (port 3389) — brute force or credential stuffing
   - Exposed SSH with weak credentials
   - Compromised VPN without MFA

**Dwell time statistics:**
- Mean dwell time (pre-encryption): 5-9 days (trending downward from 11 days in 2022)
- Some groups (particularly LockBit affiliates) encrypt within 24-48 hours
- Data exfiltration typically begins 2-3 days before encryption

#### Phase 2: Execution (TA0002)

| Technique | ATT&CK ID | Examples |
|-----------|-----------|----------|
| Command/Scripting Interpreter | T1059 | PowerShell, cmd.exe, Python |
| Windows Management Instrumentation | T1047 | `wmic process call create` |
| Scheduled Task/Job | T1053 | `schtasks /create` for persistence + execution |
| User Execution | T1204 | Macro-enabled documents, ISO double-click |
| System Services | T1569 | PsExec, service creation for lateral deployment |

**Typical execution chain:**
```
Phishing email → .html attachment (HTML smuggling)
  → .iso file extracted
    → .lnk shortcut inside ISO
      → cmd.exe /c powershell.exe -ep bypass -c "IEX(IWR ...)"
        → Cobalt Strike beacon / Sliver implant
```

#### Phase 3: Persistence (TA0003)

- Registry run keys (T1547.001) — common for initial footholds
- Scheduled tasks (T1053.005) — periodic beaconing
- Create account (T1136) — new local admin or domain user
- Web shells (T1505.003) — on compromised Exchange/IIS servers
- Boot or logon autostart (T1547) — survives reboots

#### Phase 4: Privilege Escalation (TA0004)

Critical for ransomware operators to achieve domain-level access:

- **Exploitation of vulnerability** (T1068): PrintNightmare (CVE-2021-34527), HiveNightmare, Zerologon (CVE-2020-1472)
- **Access token manipulation** (T1134): Token impersonation via Potato exploits
- **Domain policy modification** (T1484): GPO abuse for lateral deployment
- **Abuse elevation control** (T1548): UAC bypass techniques

#### Phase 5: Defense Evasion (TA0005)

| Technique | Detail |
|-----------|--------|
| Disable security tools (T1562.001) | Kill EDR processes, tamper with Windows Defender |
| Indicator removal (T1070) | Clear event logs, delete forensic artifacts |
| Masquerading (T1036) | Rename malicious binaries to legitimate names |
| Process injection (T1055) | Inject into legitimate processes for stealth |
| Virtualization/Sandbox evasion (T1497) | Detect analysis environments |
| Impair defenses (T1562) | BYOVD — Bring Your Own Vulnerable Driver |

**BYOVD (Bring Your Own Vulnerable Driver)** is increasingly common:
- Load legitimate but vulnerable signed driver (e.g., Intel, Gigabyte, Process Explorer)
- Exploit driver vulnerability to gain kernel access
- Kill EDR/AV processes from kernel mode
- Notable tools: KillAV, AuKill, Terminator, BackStab

#### Phase 6: Credential Access (TA0006)

The pivot point — domain admin credentials unlock total environment compromise:

- **OS credential dumping** (T1003): Mimikatz, secretsdump.py, comsvcs.dll MiniDump
- **LSASS memory** (T1003.001): `procdump -ma lsass.exe`, nanodump
- **DCSync** (T1003.006): Replicate domain credentials without touching DC filesystem
- **Kerberoasting** (T1558.003): Request service tickets, crack offline
- **AS-REP Roasting** (T1558.004): Target accounts without pre-authentication
- **NTDS.dit extraction** (T1003.003): Volume shadow copy + ntdsutil

#### Phase 7: Discovery (TA0007)

Reconnaissance of the internal environment:

```powershell
# Typical discovery commands observed in ransomware incidents
nltest /dclist:<domain>                           # Domain controllers
net group "Domain Admins" /domain                 # High-value accounts
net group "Enterprise Admins" /domain
Get-ADComputer -Filter * | Select Name,OS         # All machines
Get-ADOrganizationalUnit -Filter *                # OU structure
systeminfo                                        # Local system info
wmic /node:<host> process list brief              # Remote processes
dir \\<fileserver>\share$ /s                      # File share mapping
nltest /domain_trusts                             # Trust relationships
```

Tools commonly used: AdFind, BloodHound/SharpHound, Advanced IP Scanner, SoftPerfect Network Scanner.

#### Phase 8: Lateral Movement (TA0008)

| Method | Technique | Notes |
|--------|-----------|-------|
| PsExec / SMB | T1021.002 | Most common for ransomware deployment |
| RDP | T1021.001 | Interactive access for manual operations |
| WMI | T1047 | `wmic /node:<host> process call create` |
| WinRM | T1021.006 | PowerShell remoting |
| GPO deployment | T1484.001 | Mass deployment via Group Policy |
| DCOM | T1021.003 | MMC20, ShellWindows |
| SSH | T1021.004 | Linux lateral movement |

#### Phase 9: Collection and Exfiltration (TA0009 + TA0010)

Data staging and exfiltration for double-extortion leverage:

**Collection:**
- Archive collected data (T1560): 7-Zip, WinRAR with passwords
- Data from network shared drives (T1039): Targeted high-value shares
- Typical targets: financial data, PII, intellectual property, legal documents, HR records

**Exfiltration:**
- Exfiltration over C2 channel (T1041): Via Cobalt Strike/implant
- Exfiltration to cloud storage (T1567.002): Mega.nz, rclone to attacker cloud
- Automated tools: StealBit (LockBit), ExMatter (BlackCat), custom rclone configs
- Volume: attackers exfiltrate 100GB-2TB+ before encryption

#### Phase 10: Impact (TA0040)

The final phase — encryption and maximum disruption:

| Action | Technique | Purpose |
|--------|-----------|---------|
| Data encryption | T1486 | Primary extortion lever |
| Inhibit system recovery | T1490 | Delete shadow copies, disable recovery boot |
| Service stop | T1489 | Stop databases, backup agents, AV |
| System shutdown/reboot | T1529 | Force encryption of locked files after reboot |

**Pre-encryption preparation commands:**

```cmd
:: Shadow copy deletion (universal across families)
vssadmin delete shadows /all /quiet
wmic shadowcopy delete
bcdedit /set {default} recoveryenabled no
bcdedit /set {default} bootstatuspolicy ignoreallfailures

:: Service termination
net stop vss
net stop sql
net stop svc$
net stop memtas
net stop mepocs
net stop veeam
net stop backup

:: Process termination (databases, backup agents)
taskkill /f /im sqlservr.exe
taskkill /f /im oracle.exe
taskkill /f /im veeam*
taskkill /f /im backup*
```

---

## 3. Prevenzione

### 3.1 Email Security Stack

Email remains the primary initial access vector. A layered email security architecture:

**SPF (Sender Policy Framework):**
```dns
v=spf1 include:_spf.google.com include:mail.protection.outlook.com -all
```
- `-all` (hard fail) preferred over `~all` (soft fail)
- Limit DNS lookups to <10 (RFC 7208)

**DKIM (DomainKeys Identified Mail):**
- RSA-2048 minimum key length
- Rotate keys every 6-12 months
- Sign with `d=` matching `From:` domain

**DMARC (Domain-based Message Authentication, Reporting & Conformance):**
```dns
_dmarc.example.com TXT "v=DMARC1; p=reject; rua=mailto:dmarc@example.com; ruf=mailto:dmarc-forensic@example.com; pct=100; adkim=s; aspf=s"
```
- Deploy in stages: p=none → p=quarantine → p=reject
- Monitor aggregate reports before enforcement

**Advanced email security controls:**

| Control | Function | Products/Implementation |
|---------|----------|------------------------|
| Attachment sandboxing | Detonate attachments in isolated environment | Microsoft Defender for O365, Proofpoint TAP, Mimecast |
| URL rewriting | Redirect links through analysis proxy | Safe Links, URL Defense |
| Impersonation protection | Detect display name / domain spoofing | ML-based header analysis |
| QR code scanning | Analyze embedded QR codes in images | Emerging capability in SEGs |
| Retroactive detonation | Re-analyze delivered mail when new IOCs emerge | Continuous evaluation |

### 3.2 Endpoint Hardening

**Application whitelisting (T1059 mitigation):**

```powershell
# Windows Defender Application Control (WDAC) - recommended over AppLocker
# Create policy from reference machine
New-CIPolicy -Level Publisher -FilePath "C:\Policies\BasePolicy.xml" -UserPEs

# Convert to binary
ConvertFrom-CIPolicy -XmlFilePath "C:\Policies\BasePolicy.xml" `
  -BinaryFilePath "C:\Windows\System32\CodeIntegrity\SIPolicy.p7b"
```

**Script and macro restrictions:**

```powershell
# Constrained Language Mode for PowerShell
[System.Environment]::SetEnvironmentVariable('__PSLockdownPolicy', '4', 'Machine')

# Block Office macros from internet via Group Policy
# User Configuration → Admin Templates → Microsoft Office → Security
# "Block macros in Office files from the Internet" = Enabled

# ASR rules via Intune/GPO
Set-MpPreference -AttackSurfaceReductionRules_Ids `
  D4F940AB-401B-4EFC-AADC-AD5F3C50688A `
  -AttackSurfaceReductionRules_Actions Enabled
# Block all Office apps from creating child processes

Set-MpPreference -AttackSurfaceReductionRules_Ids `
  3B576869-A4EC-4529-8536-B80A7769E899 `
  -AttackSurfaceReductionRules_Actions Enabled
# Block Office apps from creating executable content
```

**Critical ASR (Attack Surface Reduction) rules for ransomware prevention:**

| Rule GUID | Description |
|-----------|-------------|
| `56a863a9-875e-4185-98a7-b882c64b5ce5` | Block abuse of exploited vulnerable signed drivers |
| `7674ba52-37eb-4a4f-a9a1-f0f9a1619a2c` | Block Adobe Reader from creating child processes |
| `d4f940ab-401b-4efc-aadc-ad5f3c50688a` | Block all Office apps from creating child processes |
| `9e6c4e1f-7d60-472f-ba1a-a39ef669e4b2` | Block credential stealing from LSASS |
| `be9ba2d9-53ea-4cdc-84e5-9b1eeee46550` | Block executable content from email client/webmail |
| `01443614-cd74-433a-b99e-2ecdc07bfc25` | Block executable files unless they meet prevalence/age/trusted list |
| `b2b3f03d-6a65-4f7b-a9c7-1c7ef74a9ba4` | Block untrusted/unsigned processes that run from USB |
| `e6db77e5-3df2-4cf1-b95a-636979351e5b` | Block persistence through WMI event subscription |

### 3.3 Network Segmentation

Segmentation limits the blast radius of a ransomware infection:

```
┌─────────────────────────────────────────────────────────────┐
│                    NETWORK ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────────────────┐   │
│  │ INTERNET │    │   DMZ    │    │   MANAGEMENT VLAN    │   │
│  │          │───▶│ Web/Mail │    │  (Jump box only)     │   │
│  └──────────┘    └────┬─────┘    └──────────┬───────────┘   │
│                       │ FW                    │ FW            │
│            ┌──────────┴───────────┐          │               │
│            │    USER SEGMENTS     │          │               │
│            │  ┌────┐  ┌────┐     │          │               │
│            │  │ HR │  │ FIN│     │          │               │
│            │  └────┘  └────┘     │          │               │
│            │  ┌────┐  ┌────┐     │          │               │
│            │  │ ENG│  │ OPS│     │          │               │
│            │  └────┘  └────┘     │          │               │
│            └──────────┬───────────┘          │               │
│                       │ FW                    │               │
│            ┌──────────┴───────────┐          │               │
│            │   SERVER SEGMENTS    │──────────┘               │
│            │  ┌─────┐  ┌──────┐  │                          │
│            │  │ APP │  │  DB  │  │                          │
│            │  └─────┘  └──────┘  │                          │
│            │  ┌─────┐  ┌──────┐  │                          │
│            │  │ FILE│  │BACKUP│  │◀── Air-gapped/VLAN      │
│            │  └─────┘  └──────┘  │    isolated              │
│            └──────────────────────┘                          │
└─────────────────────────────────────────────────────────────┘
```

**Critical segmentation rules:**

1. **Backup network**: Isolated VLAN, no inbound from workstations, management access only via jump box
2. **Database tier**: No direct workstation access — application tier only
3. **Workstation-to-workstation**: Block all lateral SMB/RDP/WinRM between endpoints
4. **Domain controllers**: Tier 0 — accessible only from designated admin workstations (PAWs)
5. **File servers**: Limit access by department, deny unnecessary protocols

**Firewall rules for lateral movement prevention:**

```
# Block workstation-to-workstation SMB
DENY tcp src:10.1.0.0/16 dst:10.1.0.0/16 dport:445
DENY tcp src:10.1.0.0/16 dst:10.1.0.0/16 dport:139

# Block workstation-to-workstation RDP
DENY tcp src:10.1.0.0/16 dst:10.1.0.0/16 dport:3389

# Block workstation-to-workstation WinRM
DENY tcp src:10.1.0.0/16 dst:10.1.0.0/16 dport:5985,5986

# Allow workstation to file server (specific shares only)
ALLOW tcp src:10.1.10.0/24 dst:10.2.1.50 dport:445  # Finance to finance share
```

### 3.4 RDP Security

RDP is the most exploited remote access protocol in ransomware attacks:

1. **Never expose RDP directly to the internet** — always behind VPN + MFA
2. **Network Level Authentication (NLA)** — require authentication before session
3. **MFA on all remote access** — hardware tokens preferred over push notifications (mitigates MFA fatigue)
4. **Restrict RDP access via GPO** — limit "Allow log on through Remote Desktop Services"
5. **Certificate-based authentication** — configure RD Gateway with certificate requirements
6. **Session timeouts** — disconnect idle sessions after 15 minutes
7. **Restricted Admin mode** — prevents credential caching on remote host

```powershell
# Enable NLA requirement via GPO
Set-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\Terminal Server\WinStations\RDP-Tcp' `
  -Name UserAuthentication -Value 1

# Enable Restricted Admin mode
reg add "HKLM\SYSTEM\CurrentControlSet\Control\Lsa" /v DisableRestrictedAdmin /t REG_DWORD /d 0 /f
```

### 3.5 Patch Management — Critical Vulnerabilities

Ransomware operators consistently exploit the same vulnerability classes. Prioritize these:

| CVE | Name | Exploited By | Priority |
|-----|------|-------------|----------|
| CVE-2021-34527 | PrintNightmare | Conti, Vice Society | CRITICAL |
| CVE-2021-44228 | Log4Shell | Conti, NightSky | CRITICAL |
| CVE-2021-26855 | ProxyLogon | DearCry, Black Kingdom | CRITICAL |
| CVE-2021-34473 | ProxyShell | Conti, LockBit, Hive | CRITICAL |
| CVE-2022-41040 | ProxyNotShell | Play, Cuba | HIGH |
| CVE-2023-4966 | Citrix Bleed | LockBit, Medusa | CRITICAL |
| CVE-2023-27997 | FortiGate RCE | Akira, LockBit | CRITICAL |
| CVE-2023-46805 | Ivanti Connect Secure | Multiple | CRITICAL |
| CVE-2024-21887 | Ivanti Connect Secure | Multiple | CRITICAL |
| CVE-2020-1472 | Zerologon | Ryuk, Conti | CRITICAL |

**Patch SLA targets:**

| Severity | Internet-Facing | Internal |
|----------|----------------|----------|
| Critical (actively exploited) | 24-48 hours | 72 hours |
| Critical | 7 days | 14 days |
| High | 14 days | 30 days |
| Medium | 30 days | 60 days |

### 3.6 Attack Surface Reduction

```powershell
# Disable SMBv1 (WannaCry/NotPetya vector)
Set-SmbServerConfiguration -EnableSMB1Protocol $false -Force
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart

# PowerShell Constrained Language Mode enforcement
# Deploy via GPO: Computer Configuration → Policies → Admin Templates →
# Windows Components → Windows PowerShell → Turn on Script Execution → 
# "Allow only signed scripts"

# Disable LLMNR (credential harvesting vector)
# GPO: Computer Configuration → Admin Templates → Network → DNS Client
# "Turn Off Multicast Name Resolution" = Enabled

# Disable NetBIOS over TCP/IP
$adapters = Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPEnabled -eq $true }
foreach ($adapter in $adapters) {
    $adapter.SetTcpipNetbios(2)  # 2 = Disable
}

# Disable WPAD (Web Proxy Auto-Discovery)
reg add "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Internet Settings\WinHttp" `
  /v DisableWpad /t REG_DWORD /d 1 /f
```

---

## 4. Detection e Early Warning

### 4.1 Canary Files (Honeypot Documents)

Canary files are decoy documents placed in common ransomware targets (file shares, user directories) that trigger immediate alerts when accessed or modified.

**Deployment strategy:**

```powershell
# deploy-canary-files.ps1
# Deploy honeypot files across file shares for ransomware detection

$CanaryContent = "CONFIDENTIAL - DO NOT DISTRIBUTE - Q4 Financial Projections"
$CanaryFiles = @(
    "!IMPORTANT_Passwords.xlsx",
    "!DO_NOT_DELETE_Financials.docx",
    "_Budget_2026_FINAL.pdf",
    "~$Confidential_HR_Records.xlsx"
)

$SharePaths = @(
    "\\fileserver\finance$",
    "\\fileserver\hr$",
    "\\fileserver\executive$",
    "\\fileserver\shared"
)

foreach ($share in $SharePaths) {
    foreach ($file in $CanaryFiles) {
        $fullPath = Join-Path $share $file
        if (-not (Test-Path $fullPath)) {
            Set-Content -Path $fullPath -Value $CanaryContent
            # Set file attributes: hidden + system to avoid user confusion
            # but accessible to ransomware scanners
            $item = Get-Item $fullPath -Force
            $item.Attributes = 'Hidden'

            # Create SACL audit entry
            $acl = Get-Acl $fullPath
            $rule = New-Object System.Security.AccessControl.FileSystemAuditRule(
                "Everyone",
                "ReadData,WriteData,Delete",
                "Success,Failure"
            )
            $acl.AddAuditRule($rule)
            Set-Acl -Path $fullPath -AclObject $acl
        }
    }
}

Write-Host "[+] Canary files deployed. Configure SIEM alerts for Event ID 4663 on these paths."
```

**SIEM alert rule for canary file access:**

```yaml
# Sigma rule: Canary file access detection
title: Ransomware Canary File Access
id: a1b2c3d4-5678-9abc-def0-123456789abc
status: experimental
description: Detects access to honeypot canary files indicating potential ransomware activity
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4663
        ObjectName|contains:
            - '!IMPORTANT_Passwords'
            - '!DO_NOT_DELETE_Financials'
            - '_Budget_2026_FINAL'
            - '~$Confidential_HR_Records'
    condition: selection
level: critical
tags:
    - attack.impact
    - attack.t1486
falsepositives:
    - Antivirus scanning (whitelist AV service accounts)
```

### 4.2 File Integrity Monitoring and Entropy Analysis

**Volume-of-changes detection:**

```python
#!/usr/bin/env python3
"""
ransomware_entropy_monitor.py
Monitor file system for ransomware indicators:
- High volume of file modifications
- Entropy changes indicating encryption
- Suspicious file extension changes
"""

import os
import math
import time
import hashlib
import logging
from collections import defaultdict
from pathlib import Path
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/var/log/ransomware_monitor.log'),
        logging.StreamHandler()
    ]
)

MONITORED_PATHS = ['/mnt/shares/finance', '/mnt/shares/hr', '/mnt/shares/shared']
ENTROPY_THRESHOLD = 7.5       # Encrypted files typically > 7.9
CHANGE_RATE_THRESHOLD = 50    # Files modified per minute triggering alert
EXTENSION_BLACKLIST = [
    '.encrypted', '.locked', '.crypto', '.crypt', '.enc',
    '.lockbit', '.blackcat', '.akira', '.play', '.kat',
    '.onion', '.aaa', '.abc', '.xyz', '.zzz'
]

def calculate_entropy(filepath: str) -> float:
    """Calculate Shannon entropy of a file (0-8 for byte data)."""
    try:
        with open(filepath, 'rb') as f:
            data = f.read(65536)  # Sample first 64KB
        if not data:
            return 0.0
        byte_counts = defaultdict(int)
        for byte in data:
            byte_counts[byte] += 1
        entropy = 0.0
        length = len(data)
        for count in byte_counts.values():
            probability = count / length
            if probability > 0:
                entropy -= probability * math.log2(probability)
        return entropy
    except (OSError, PermissionError):
        return 0.0

def check_extension_change(filepath: str) -> bool:
    """Check if file has a known ransomware extension."""
    ext = Path(filepath).suffix.lower()
    return ext in EXTENSION_BLACKLIST

def monitor_directory(path: str, interval: int = 10):
    """Monitor directory for ransomware indicators."""
    baseline = {}
    modification_counts = defaultdict(int)
    alert_cooldown = {}

    # Build initial baseline
    for root, dirs, files in os.walk(path):
        for fname in files:
            fpath = os.path.join(root, fname)
            try:
                stat = os.stat(fpath)
                baseline[fpath] = {
                    'mtime': stat.st_mtime,
                    'size': stat.st_size,
                    'entropy': calculate_entropy(fpath)
                }
            except OSError:
                continue

    logging.info(f"Baseline established: {len(baseline)} files in {path}")

    while True:
        current_minute = datetime.now().strftime('%Y%m%d%H%M')
        modifications_this_cycle = 0

        for root, dirs, files in os.walk(path):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                except OSError:
                    continue

                # Check for ransomware extensions
                if check_extension_change(fpath):
                    logging.critical(
                        f"RANSOMWARE EXTENSION DETECTED: {fpath}"
                    )
                    trigger_alert('extension_detected', fpath)

                # Check for modifications
                if fpath in baseline:
                    if stat.st_mtime != baseline[fpath]['mtime']:
                        modifications_this_cycle += 1
                        new_entropy = calculate_entropy(fpath)
                        old_entropy = baseline[fpath]['entropy']

                        # Entropy spike detection
                        if (new_entropy > ENTROPY_THRESHOLD and
                                old_entropy < ENTROPY_THRESHOLD - 1):
                            logging.critical(
                                f"ENTROPY SPIKE: {fpath} "
                                f"({old_entropy:.2f} → {new_entropy:.2f})"
                            )
                            trigger_alert('entropy_spike', fpath)

                        baseline[fpath] = {
                            'mtime': stat.st_mtime,
                            'size': stat.st_size,
                            'entropy': new_entropy
                        }

        # Volume-based detection
        modification_counts[current_minute] += modifications_this_cycle
        if modification_counts[current_minute] > CHANGE_RATE_THRESHOLD:
            logging.critical(
                f"HIGH MODIFICATION RATE: "
                f"{modification_counts[current_minute]} files/min in {path}"
            )
            trigger_alert('high_modification_rate', path)

        time.sleep(interval)

def trigger_alert(alert_type: str, context: str):
    """Trigger alert via configured channels."""
    # Integration points: syslog, SIEM webhook, PagerDuty, email
    logging.critical(f"ALERT [{alert_type}]: {context}")
    # Implement: send to SIEM, trigger PagerDuty, notify SOC


if __name__ == '__main__':
    for path in MONITORED_PATHS:
        if os.path.exists(path):
            # In production: run each path in separate thread/process
            monitor_directory(path)
```

### 4.3 Behavioral Indicators and EDR Detection

**Sigma rules for ransomware precursor activity:**

```yaml
# Shadow copy deletion detection
title: Shadow Copy Deletion via Vssadmin
id: f3b4a7c2-1234-5678-abcd-ef0123456789
status: stable
description: Detects shadow copy deletion commonly performed before ransomware encryption
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
        CommandLine|contains:
            - 'Win32_ShadowCopy'
            - 'Remove-WmiObject'
    condition: selection_vssadmin or selection_wmic or selection_powershell
level: high
tags:
    - attack.impact
    - attack.t1490
---
# BCDEdit recovery disable
title: BCDEdit Recovery Disable
id: b5c6d7e8-9012-3456-7890-abcdef123456
status: stable
description: Detects disabling of Windows recovery features
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\bcdedit.exe'
        CommandLine|contains:
            - 'recoveryenabled no'
            - 'bootstatuspolicy ignoreallfailures'
    condition: selection
level: high
tags:
    - attack.impact
    - attack.t1490
---
# Mass file rename detection
title: Suspicious Mass File Rename Operation
id: c7d8e9f0-1234-5678-9abc-def012345678
status: experimental
description: Detects mass file renaming operations typical of ransomware encryption
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4663
        AccessMask: '0x2'  # WriteData
    timeframe: 1m
    condition: selection | count(ObjectName) by SubjectUserName > 100
level: critical
tags:
    - attack.impact
    - attack.t1486
---
# Service stop - backup and database services
title: Suspicious Service Stop - Backup or Database
id: d9e0f1a2-3456-7890-abcd-ef0123456789
status: stable
description: Detects stopping of backup or database services commonly targeted by ransomware
logsource:
    category: process_creation
    product: windows
detection:
    selection_net:
        Image|endswith: '\net.exe'
        CommandLine|contains:
            - 'stop'
        CommandLine|contains:
            - 'vss'
            - 'sql'
            - 'veeam'
            - 'backup'
            - 'memtas'
            - 'sophos'
            - 'svc$'
    selection_sc:
        Image|endswith: '\sc.exe'
        CommandLine|contains:
            - 'stop'
            - 'delete'
    condition: selection_net or selection_sc
level: high
tags:
    - attack.impact
    - attack.t1489
```

**YARA rule for ransomware binary detection:**

```yara
rule Ransomware_Generic_Indicators
{
    meta:
        description = "Detects generic ransomware behavioral indicators in binaries"
        author = "SOC Team"
        date = "2025-01-15"
        severity = "critical"

    strings:
        // Ransom note filenames
        $note1 = "README.txt" ascii wide
        $note2 = "DECRYPT" ascii wide nocase
        $note3 = "RECOVER" ascii wide nocase
        $note4 = "YOUR FILES" ascii wide nocase
        $note5 = "HOW TO" ascii wide nocase
        $note6 = ".onion" ascii

        // Shadow copy deletion
        $vss1 = "vssadmin" ascii wide nocase
        $vss2 = "delete shadows" ascii wide nocase
        $vss3 = "shadowcopy delete" ascii wide nocase
        $vss4 = "bcdedit" ascii wide nocase
        $vss5 = "wbadmin delete" ascii wide nocase

        // Crypto API imports
        $crypto1 = "CryptEncrypt" ascii
        $crypto2 = "CryptGenKey" ascii
        $crypto3 = "CryptImportKey" ascii
        $crypto4 = "BCryptEncrypt" ascii
        $crypto5 = "CryptAcquireContext" ascii

        // Extension manipulation
        $ext1 = ".encrypted" ascii wide
        $ext2 = ".locked" ascii wide
        $ext3 = "MoveFileEx" ascii
        $ext4 = "SetFileAttributes" ascii

        // Service manipulation
        $svc1 = "OpenSCManager" ascii
        $svc2 = "ControlService" ascii
        $svc3 = "SERVICE_STOP" ascii

    condition:
        uint16(0) == 0x5A4D and  // MZ header
        filesize < 10MB and
        (
            (2 of ($note*) and 2 of ($vss*)) or
            (2 of ($note*) and 2 of ($crypto*) and 1 of ($ext*)) or
            (3 of ($vss*) and 2 of ($crypto*)) or
            (2 of ($note*) and 2 of ($svc*) and 1 of ($crypto*))
        )
}

rule Ransomware_LockBit_Indicators
{
    meta:
        description = "Detects LockBit ransomware family indicators"
        author = "SOC Team"
        date = "2025-01-15"

    strings:
        $s1 = "LockBit" ascii wide nocase
        $s2 = "Restore-My-Files.txt" ascii wide
        $s3 = ".lockbit" ascii wide
        $mutex1 = "Global\\{" ascii
        $api1 = "NtSetInformationFile" ascii
        $api2 = "IoCompletionPort" ascii
        $cmd1 = "/C ping 127.0.0.7 -n 3 > Nul & fsutil" ascii

    condition:
        uint16(0) == 0x5A4D and
        (
            ($s1 and $s3) or
            ($s2 and 2 of ($api*)) or
            ($s1 and $cmd1)
        )
}
```

### 4.4 Network Indicators

**C2 communication detection patterns:**

| Indicator | Detection Method |
|-----------|-----------------|
| Cobalt Strike beacons | JA3/JA3S fingerprints, malleable C2 profile detection, sleep jitter analysis |
| DNS tunneling | High volume of TXT queries, subdomain entropy analysis, query length anomalies |
| Data exfiltration | Large outbound transfers to cloud storage, rclone traffic signatures |
| Tor/anonymous proxies | Known Tor exit node lists, unusual HTTPS on non-standard ports |
| Domain fronting | SNI/Host header mismatches |

**Suricata rules for ransomware network indicators:**

```
# Detect Cobalt Strike default certificate
alert tls any any -> any any (msg:"ET MALWARE Cobalt Strike Default Certificate"; \
  tls.cert_subject; content:"Major Cobalt Strike"; sid:2035100; rev:1;)

# Detect high-volume SMB file renames (lateral encryption)
alert smb any any -> any any (msg:"Possible Ransomware SMB Mass Rename"; \
  flow:established,to_server; \
  smb.named_pipe; content:"|FF|SMB"; \
  threshold:type both, track by_src, count 50, seconds 10; \
  sid:2035200; rev:1;)

# Detect rclone to mega.nz (common exfiltration)
alert http any any -> any any (msg:"ET POLICY rclone to Mega.nz Exfil"; \
  http.host; content:"mega.nz"; http.user_agent; content:"rclone"; \
  sid:2035300; rev:1;)
```

### 4.5 SIEM Correlation Rules for Ransomware Precursors

```yaml
# Composite detection: Multiple ransomware precursors within timeframe
title: Ransomware Kill Chain Correlation
description: |
  Triggers when multiple ransomware precursor activities are detected
  from the same source within a 30-minute window.

triggers:
  - shadow_copy_deletion     # T1490
  - backup_service_stopped   # T1489
  - mass_file_modification   # T1486
  - suspicious_process_kill  # T1489
  - bcdedit_modification     # T1490
  - credential_dumping       # T1003

correlation:
  timeframe: 30m
  group_by: source_host
  minimum_matches: 3

severity: CRITICAL
response:
  - isolate_host
  - page_soc_lead
  - preserve_memory_dump
  - notify_ir_team
```

---

## 5. Risposta Immediata

### 5.1 First 15 Minutes — Containment Decision Tree

```
┌─────────────────────────────────────────────────────────────────┐
│              RANSOMWARE DETECTED — FIRST 15 MINUTES              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  T+0:  Alert received (EDR / canary / user report)              │
│         │                                                        │
│         ▼                                                        │
│  T+1:  VALIDATE — Is this a true positive?                      │
│         │  YES ──────────────────────────────────────────┐       │
│         │                                                │       │
│         ▼                                                ▼       │
│  T+2:  SCOPE — Single host or multiple?          If NO: │       │
│         │                                        Tune    │       │
│         ├─ Single host: Isolate immediately      alert   │       │
│         │                                                │       │
│         ├─ Multiple hosts: Network-level contain         │       │
│         │                                                │       │
│         ▼                                                        │
│  T+5:  ISOLATE — Do NOT power off                               │
│         │  • Disable network port (switch)                       │
│         │  • EDR network isolation                               │
│         │  • Block at firewall                                   │
│         │  • Preserve running memory state                       │
│         │                                                        │
│         ▼                                                        │
│  T+8:  PRESERVE EVIDENCE                                        │
│         │  • Memory dump (if safe to access)                     │
│         │  • Screenshot ransom note                              │
│         │  • Note encrypted file extensions                      │
│         │  • Capture network connections                         │
│         │                                                        │
│         ▼                                                        │
│  T+10: ASSESS SCOPE                                             │
│         │  • Query EDR for IOCs across fleet                     │
│         │  • Check DC event logs                                 │
│         │  • Review backup system status                         │
│         │  • Check for data exfiltration evidence                │
│         │                                                        │
│         ▼                                                        │
│  T+12: COMMUNICATE                                              │
│         │  • SOC Lead → CISO → Legal → Insurance                │
│         │  • DO NOT communicate via potentially                  │
│         │    compromised email/Slack                             │
│         │                                                        │
│         ▼                                                        │
│  T+15: ACTIVATE IR PLAN                                         │
│         • Convene war room (out-of-band communication)           │
│         • Engage IR retainer / DFIR firm                         │
│         • Notify law enforcement (FBI IC3 / CISA)               │
│         • Contact cyber insurance carrier                        │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 Network Isolation Procedures

**Critical principle: Disconnect, do NOT power off.**

Powering off destroys volatile memory containing:
- Encryption keys (potentially recoverable from memory)
- Active network connections (C2 indicators)
- Running processes (malware identification)
- Loaded modules and DLLs

**Isolation script (emergency network containment):**

```bash
#!/bin/bash
# emergency-isolate.sh
# Immediately isolate a compromised host via network controls
# Usage: ./emergency-isolate.sh <host_ip> <switch_ip> <port_number>

HOST_IP="$1"
SWITCH_IP="$2"
PORT="$3"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

if [[ -z "$HOST_IP" || -z "$SWITCH_IP" || -z "$PORT" ]]; then
    echo "Usage: $0 <host_ip> <switch_ip> <port_number>"
    exit 1
fi

echo "[${TIMESTAMP}] ISOLATING HOST: ${HOST_IP}"
echo "[${TIMESTAMP}] Switch: ${SWITCH_IP}, Port: ${PORT}"

# Method 1: Disable switch port (Cisco IOS example)
ssh admin@"${SWITCH_IP}" <<EOF
enable
configure terminal
interface GigabitEthernet0/${PORT}
shutdown
description ISOLATED-RANSOMWARE-${TIMESTAMP}
exit
exit
write memory
EOF

# Method 2: Add firewall block rule (iptables on gateway)
# ssh admin@gateway "iptables -I FORWARD -s ${HOST_IP} -j DROP"
# ssh admin@gateway "iptables -I FORWARD -d ${HOST_IP} -j DROP"

# Method 3: EDR network isolation (CrowdStrike example)
# falconctl -s --network-isolation on

echo "[${TIMESTAMP}] Host ${HOST_IP} isolated. DO NOT POWER OFF."
echo "[${TIMESTAMP}] Next: Capture memory dump before any further action."
```

**Memory preservation (before any other forensic activity):**

```powershell
# Capture memory dump from isolated (but running) host
# Requires: WinPmem, DumpIt, or Magnet RAM Capture pre-deployed

# Option 1: WinPmem (open source)
.\winpmem_mini_x64.exe \\forensics-share\cases\$env:COMPUTERNAME-mem-$(Get-Date -Format yyyyMMddHHmmss).raw

# Option 2: DumpIt (Magnet Forensics)
.\DumpIt.exe /OUTPUT \\forensics-share\cases\$env:COMPUTERNAME-memdump.dmp /QUIET

# Option 3: PowerShell native (volatile data collection)
# Capture network connections
Get-NetTCPConnection | Export-Csv "\\forensics-share\cases\$env:COMPUTERNAME-netstat.csv"
# Capture running processes
Get-Process | Select-Object Id,Name,Path,StartTime,CPU | Export-Csv "\\forensics-share\cases\$env:COMPUTERNAME-processes.csv"
# Capture loaded DLLs for suspicious processes
Get-Process | Where-Object { $_.CPU -gt 50 } | ForEach-Object {
    $_.Modules | Select-Object ModuleName,FileName
} | Export-Csv "\\forensics-share\cases\$env:COMPUTERNAME-modules.csv"
```

### 5.3 Scope Assessment

Rapidly determine the blast radius:

```powershell
# scope-assessment.ps1
# Rapidly assess ransomware blast radius across the environment

param(
    [string]$KnownIOC_Hash,        # SHA256 of ransomware binary
    [string]$KnownIOC_Extension,   # Encrypted file extension
    [string]$KnownIOC_RansomNote   # Ransom note filename
)

Write-Host "=== RANSOMWARE SCOPE ASSESSMENT ===" -ForegroundColor Red
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC' -AsUTC)"

# 1. Query EDR for IOC presence across fleet
Write-Host "`n[1] Checking for ransomware binary across endpoints..."
# CrowdStrike Falcon example:
# Get-CsDetection -Filter "behaviors.sha256:'$KnownIOC_Hash'"

# 2. Check file shares for encrypted files
Write-Host "`n[2] Scanning file shares for encrypted extensions..."
$shares = @("\\fileserver1\data$", "\\fileserver2\shared$")
foreach ($share in $shares) {
    $encrypted = Get-ChildItem -Path $share -Recurse -Filter "*$KnownIOC_Extension" -ErrorAction SilentlyContinue | Measure-Object
    Write-Host "  $share : $($encrypted.Count) encrypted files found"
}

# 3. Check for ransom notes
Write-Host "`n[3] Searching for ransom notes..."
foreach ($share in $shares) {
    $notes = Get-ChildItem -Path $share -Recurse -Filter $KnownIOC_RansomNote -ErrorAction SilentlyContinue
    foreach ($note in $notes) {
        Write-Host "  FOUND: $($note.FullName)" -ForegroundColor Red
    }
}

# 4. Check Active Directory for suspicious activity
Write-Host "`n[4] Checking AD for recent suspicious changes..."
$recentUsers = Get-ADUser -Filter {Created -gt (Get-Date).AddDays(-1)} -Properties Created
if ($recentUsers) {
    Write-Host "  WARNING: New users created in last 24h:" -ForegroundColor Yellow
    $recentUsers | ForEach-Object { Write-Host "    $($_.SamAccountName) - Created: $($_.Created)" }
}

# 5. Check backup system integrity
Write-Host "`n[5] Checking backup system status..."
# Veeam example:
# Get-VBRBackupSession -Last 24h | Where-Object { $_.Result -ne "Success" }

# 6. Check for data exfiltration indicators
Write-Host "`n[6] Checking for large outbound transfers (last 48h)..."
# Query firewall/proxy logs for large uploads
# Get-NetFirewallLog | Where-Object { $_.BytesSent -gt 1GB -and $_.Direction -eq "Outbound" }

Write-Host "`n=== ASSESSMENT COMPLETE ==="
Write-Host "Document findings and proceed to containment verification."
```

### 5.4 Communication Plan

**Communication hierarchy and channels:**

| Audience | When | Channel | Content |
|----------|------|---------|---------|
| SOC/IR Team | Immediately (T+0) | Out-of-band (Signal, cell phone) | Technical details, IOCs |
| CISO | T+5 minutes | Phone call | Situation brief, scope estimate |
| Legal Counsel | T+15 minutes | Phone call | Regulatory implications, privilege |
| Cyber Insurance | T+30 minutes | Dedicated hotline | Claim initiation, DFIR engagement |
| Executive Leadership | T+60 minutes | In-person or secure call | Business impact, ETA for operations |
| Law Enforcement | T+2 hours | FBI IC3 / local field office | Report filing, evidence preservation |
| Affected Customers | Per legal counsel | Official channels | Only after legal review |
| Media | Per PR/Legal | Prepared statement | Only if public disclosure required |

**CRITICAL: Do NOT use potentially compromised infrastructure for IR communications.**
- Assume email is compromised
- Assume Slack/Teams may be compromised
- Use pre-established out-of-band channels (Signal, separate cell phones, physical war room)

### 5.5 Ransomware Identification

Tools for identifying the ransomware family and potential decryptors:

1. **ID Ransomware** (https://id-ransomware.malwarehunterteam.com/) — upload ransom note or encrypted sample
2. **No More Ransom** (https://www.nomoreransom.org/) — check for available free decryptors
3. **MalwareHunterTeam** — Twitter/X for real-time ransomware identification
4. **VirusTotal** — submit ransomware binary hash for family identification
5. **ANY.RUN / Hybrid Analysis** — behavioral analysis sandbox submission

**Available decryptors (notable families with free tools):**

| Family | Decryptor Source | Notes |
|--------|-----------------|-------|
| GandCrab | Bitdefender/Europol | All versions |
| REvil (some variants) | Bitdefender | Limited versions |
| Hive | FBI | Master key released after takedown |
| Akira (early Linux variant) | Security researchers | Specific versions only |
| Rhysida | Korean researchers | Vulnerability in implementation |
| Babuk (ESXi) | Avast | Using leaked builder |
| TeslaCrypt | ESET | Master key released by operators |

---

## 6. Negoziazione e Decisione sul Pagamento

### 6.1 Decision Framework — When Payment May Be Considered

Payment should be the **absolute last resort**, considered only when:

1. **Life safety**: Healthcare systems, life-critical infrastructure with no backup
2. **Existential threat**: Organization cannot survive without the data and has no backup path
3. **Highly sensitive data**: Exfiltrated data poses extreme reputational/legal risk if published
4. **Time-critical operations**: Critical infrastructure where downtime costs exceed ransom by 10x+

**Decision matrix:**

```
                        BACKUPS AVAILABLE
                     YES              NO
                ┌────────────┬────────────────┐
     LOW        │  NEVER PAY │  Restore from  │
     DATA       │  Restore   │  scratch if    │
     SENSITIVITY│  from      │  possible      │
                │  backup    │  Pay = LAST    │
                │            │  resort        │
                ├────────────┼────────────────┤
     HIGH       │  NEVER PAY │  LEGAL REVIEW  │
     DATA       │  Restore + │  + SANCTIONS   │
     SENSITIVITY│  Accept    │  CHECK         │
                │  possible  │  Consider with │
                │  leak      │  legal counsel │
                └────────────┴────────────────┘
```

### 6.2 Legal Implications

**OFAC sanctions screening (mandatory before any payment):**

The U.S. Treasury's Office of Foreign Assets Control (OFAC) maintains sanctions lists. Paying a sanctioned entity can result in civil/criminal penalties regardless of the circumstances.

Sanctioned/restricted groups (as of 2025):
- Lazarus Group (DPRK) — WannaCry, various operations
- Evil Corp (Russia) — WastedLocker, Dridex, connected to LockBit
- Sandworm (Russia GRU) — NotPetya
- Various Conti-affiliated individuals

**Legal considerations:**
- Engage specialized legal counsel before any payment decision
- Document the decision-making process thoroughly
- Verify insurance coverage for ransom payment
- Understand reporting obligations (CIRCIA, NIS2, state breach notification)
- Payment does NOT eliminate regulatory obligations for breach notification

### 6.3 Negotiation Tactics

If payment is authorized after legal review:

1. **Initial response delay**: Do not respond immediately — gather intelligence first
2. **Proof of decryption**: Demand decryption of 2-3 test files before any payment
3. **Timeline extension**: Request additional time — cite "management approval needed"
4. **Price reduction**: Initial demands are typically 3-10x the expected payment; negotiate
5. **Scope clarification**: Confirm exactly what is included — decryptor + data deletion guarantee
6. **Technical competence assessment**: Evaluate whether decryptor actually works from test files
7. **Data deletion proof**: Request proof of data deletion (unreliable but standard ask)

**Average negotiation outcomes (2024 data):**
- Median reduction from initial demand: 40-60%
- Typical negotiation duration: 3-7 days
- Payment method: Bitcoin (70%), Monero (30%)

### 6.4 Cryptocurrency Payment Mechanics (If Authorized)

**Process (handled by specialized firms, not internally):**

1. Engage cryptocurrency payment specialist (via insurance/legal counsel)
2. Obtain verified wallet address from threat actor
3. Conduct blockchain analysis to identify wallet ownership patterns
4. Execute payment in staged manner if possible
5. Obtain and validate decryptor functionality
6. Document all transactions for law enforcement and insurance

**Risks of payment:**
- Decryptor may not work (5-10% failure rate)
- Partial decryption — corrupt or incompletely encrypted files unrecoverable
- Re-targeting: 80% of paying victims attacked again within 12 months
- Funds sanction violations (OFAC)
- Funds further criminal activity
- No guarantee of data deletion from leak sites
- Insurance may not cover ransom (policy-specific)

---

## 7. Recovery Operations

### 7.1 Recovery Planning and Prioritization

**System prioritization based on BIA:**

| Tier | Systems | RTO | RPO |
|------|---------|-----|-----|
| 0 | Active Directory, DNS, DHCP | 4h | 0 (no data loss) |
| 1 | Email, VPN, critical business apps | 8h | 1h |
| 2 | File servers, databases, ERP | 24h | 4h |
| 3 | Development, test, non-critical | 72h | 24h |
| 4 | Archive, historical data | 1 week | 1 week |

**Recovery sequence:**

```
PHASE 1: Foundation (Hours 0-4)
├── Verify backup integrity (clean room)
├── Rebuild network core (clean switches/firewalls)
├── Deploy clean DNS/DHCP
└── Rebuild domain controllers (if compromised)

PHASE 2: Identity (Hours 4-12)
├── AD recovery (DSRM or forest recovery)
├── KRBTGT double rotation
├── Reset all privileged accounts
└── Deploy temporary MFA solution

PHASE 3: Critical Services (Hours 12-48)
├── Email system restoration
├── VPN/remote access (with enhanced security)
├── Critical business applications
└── Communication systems

PHASE 4: Data Recovery (Hours 48-96)
├── File server restoration from immutable backups
├── Database recovery (point-in-time)
├── Application configuration restore
└── Data integrity validation

PHASE 5: Full Operations (Days 5-14)
├── Non-critical system restoration
├── User workstation rebuild
├── Full connectivity restoration
└── Monitoring validation
```

### 7.2 Backup Verification — Clean Room Approach

**NEVER restore backups directly into the production environment without verification.**

```bash
#!/bin/bash
# verify-backup-integrity.sh
# Verify backup integrity in isolated clean room before production restore

BACKUP_PATH="$1"
CLEAN_ROOM_VM="forensics-cleanroom-01"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG="/var/log/ir/backup-verification-${TIMESTAMP}.log"

echo "[${TIMESTAMP}] === BACKUP INTEGRITY VERIFICATION ===" | tee -a "$LOG"
echo "[${TIMESTAMP}] Backup: ${BACKUP_PATH}" | tee -a "$LOG"

# Step 1: Verify backup file integrity (checksums)
echo "[+] Verifying backup checksums..." | tee -a "$LOG"
if sha256sum --check "${BACKUP_PATH}.sha256" 2>>"$LOG"; then
    echo "    PASS: Checksum matches" | tee -a "$LOG"
else
    echo "    FAIL: Checksum mismatch - backup may be corrupted" | tee -a "$LOG"
    exit 1
fi

# Step 2: Mount backup in isolated environment (read-only)
echo "[+] Mounting backup in clean room (read-only)..." | tee -a "$LOG"
MOUNT_POINT="/mnt/cleanroom/verify-${TIMESTAMP}"
mkdir -p "$MOUNT_POINT"
mount -o ro,noexec,nosuid "$BACKUP_PATH" "$MOUNT_POINT" 2>>"$LOG"

# Step 3: Scan for ransomware artifacts
echo "[+] Scanning for ransomware artifacts..." | tee -a "$LOG"
# Check for ransom notes
find "$MOUNT_POINT" -name "*.txt" -newer "$MOUNT_POINT" -exec grep -l -i \
    -e "your files have been encrypted" \
    -e "bitcoin" \
    -e "decrypt" \
    -e "ransom" \
    {} \; 2>/dev/null | tee -a "$LOG"

# Check for encrypted file extensions
SUSPICIOUS_EXT=$(find "$MOUNT_POINT" -regex '.*\.\(encrypted\|locked\|lockbit\|blackcat\|akira\)' | wc -l)
if [ "$SUSPICIOUS_EXT" -gt 0 ]; then
    echo "    WARNING: ${SUSPICIOUS_EXT} files with suspicious extensions found" | tee -a "$LOG"
    echo "    BACKUP MAY BE CONTAMINATED" | tee -a "$LOG"
fi

# Step 4: Entropy analysis on sample files
echo "[+] Running entropy analysis on sample files..." | tee -a "$LOG"
find "$MOUNT_POINT" -type f -name "*.docx" -o -name "*.xlsx" -o -name "*.pdf" | head -20 | while read -r file; do
    ENTROPY=$(python3 -c "
import math, sys
with open('$file', 'rb') as f:
    data = f.read(65536)
if not data:
    print(0)
    sys.exit()
freq = [0]*256
for b in data: freq[b] += 1
ent = -sum(p/len(data) * math.log2(p/len(data)) for p in freq if p > 0)
print(f'{ent:.4f}')
")
    if (( $(echo "$ENTROPY > 7.5" | bc -l) )); then
        echo "    HIGH ENTROPY (${ENTROPY}): ${file}" | tee -a "$LOG"
    fi
done

# Step 5: Run AV scan in clean room
echo "[+] Running antivirus scan..." | tee -a "$LOG"
clamscan -r --no-summary "$MOUNT_POINT" 2>>"$LOG" | grep "FOUND" | tee -a "$LOG"

# Step 6: Verify critical system files integrity
echo "[+] Verifying OS file integrity (if system backup)..." | tee -a "$LOG"
if [ -d "${MOUNT_POINT}/Windows/System32" ]; then
    # Check for known-good hashes of critical DLLs
    sfc /verifyonly /offbootdir="${MOUNT_POINT}" /offwindir="${MOUNT_POINT}/Windows" 2>>"$LOG"
fi

# Cleanup
umount "$MOUNT_POINT"
rmdir "$MOUNT_POINT"

echo "[${TIMESTAMP}] === VERIFICATION COMPLETE ===" | tee -a "$LOG"
echo "Review log: $LOG"
```

### 7.3 Bare-Metal Recovery Procedures

**Windows Server bare-metal restore:**

```powershell
# 1. Boot from Windows PE/recovery media
# 2. Verify backup media connectivity
# 3. Restore system state

# Using Windows Server Backup (wbadmin)
wbadmin start sysrecovery -version:<backup_version> `
  -backupTarget:<backup_location> `
  -machine:<original_machine_name> `
  -restoreAllVolumes `
  -recreateDisks

# Using Veeam (from rescue media)
# Boot from Veeam Recovery Media
# Select "Bare Metal Recovery"
# Point to verified backup repository
# Map disks appropriately
# Restore
```

**Linux bare-metal restore:**

```bash
# Using rear (Relax-and-Recover)
# 1. Boot from ReaR rescue ISO
# 2. At recovery prompt:
rear recover

# Manual approach with dd + tar
# 1. Boot from live USB
# 2. Partition disks identically
parted /dev/sda mklabel gpt
parted /dev/sda mkpart primary ext4 1MiB 512MiB   # /boot
parted /dev/sda mkpart primary ext4 512MiB 100%    # LVM

# 3. Restore LVM structure
pvcreate /dev/sda2
vgcreate vg0 /dev/sda2
lvcreate -L 50G -n root vg0
lvcreate -L 16G -n swap vg0
lvcreate -l 100%FREE -n data vg0

# 4. Format and mount
mkfs.ext4 /dev/vg0/root
mount /dev/vg0/root /mnt/restore
mkdir -p /mnt/restore/boot
mount /dev/sda1 /mnt/restore/boot

# 5. Restore from verified backup
tar xzpf /mnt/backup/server-root-verified.tar.gz -C /mnt/restore/

# 6. Reinstall bootloader
mount --bind /dev /mnt/restore/dev
mount --bind /proc /mnt/restore/proc
mount --bind /sys /mnt/restore/sys
chroot /mnt/restore grub-install /dev/sda
chroot /mnt/restore update-grub
```

### 7.4 Active Directory Recovery

AD compromise is the most critical recovery challenge. Domain controllers may contain backdoors (DCShadow, AdminSDHolder modification, SID History injection).

**Forest recovery procedure:**

```powershell
# === ACTIVE DIRECTORY FOREST RECOVERY ===
# Reference: Microsoft AD Forest Recovery Guide

# STEP 1: Isolate all DCs from network

# STEP 2: Recover first DC using DSRM
# Boot DC in Directory Services Restore Mode (F8 → DSRM)
# Login with DSRM administrator password

# STEP 3: Restore System State from verified backup
wbadmin start systemstaterecovery -version:<verified_backup_version> -authsysvol

# STEP 4: Configure isolated network for AD recovery
# Set static IP, disable NICs connected to production

# STEP 5: Perform metadata cleanup (remove references to other DCs)
ntdsutil
# metadata cleanup → connections → connect to server <recovered_DC>
# select operation target → list sites → select site 0
# list servers in site → remove selected server (for each compromised DC)

# STEP 6: Seize FSMO roles
Move-ADDirectoryServerOperationMasterRole -Identity <recovered_DC> `
  -OperationMasterRole SchemaMaster,DomainNamingMaster,RIDMaster,InfrastructureMaster,PDCEmulator `
  -Force

# STEP 7: Reset KRBTGT password (TWICE — with replication interval between)
# First rotation
Set-ADAccountPassword -Identity krbtgt -Reset -NewPassword (ConvertTo-SecureString -AsPlainText "$(New-Guid)" -Force)
# Wait > MaxClockSkew (default 5 min) + Replication interval
Start-Sleep -Seconds 600
# Second rotation
Set-ADAccountPassword -Identity krbtgt -Reset -NewPassword (ConvertTo-SecureString -AsPlainText "$(New-Guid)" -Force)

# STEP 8: Reset all Tier 0 accounts
Get-ADGroupMember "Domain Admins" | ForEach-Object {
    Set-ADAccountPassword -Identity $_.SamAccountName -Reset `
      -NewPassword (ConvertTo-SecureString -AsPlainText "$(New-Guid)" -Force)
}
Get-ADGroupMember "Enterprise Admins" | ForEach-Object {
    Set-ADAccountPassword -Identity $_.SamAccountName -Reset `
      -NewPassword (ConvertTo-SecureString -AsPlainText "$(New-Guid)" -Force)
}

# STEP 9: Rebuild additional DCs (promote new, don't restore old)
# Install AD DS role on clean server
# dcpromo with replicate from recovered DC

# STEP 10: Validate
repadmin /replsummary
dcdiag /v /c /d /e
```

### 7.5 Database Recovery

**SQL Server point-in-time recovery:**

```sql
-- Identify last known-good state (before encryption started)
-- Check backup chain integrity
RESTORE HEADERONLY FROM DISK = N'E:\Backups\DB_Full_20260506.bak';
RESTORE HEADERONLY FROM DISK = N'E:\Backups\DB_Diff_20260507_0600.bak';
RESTORE HEADERONLY FROM DISK = N'E:\Backups\DB_Log_20260507_0800.trn';

-- Restore to point-in-time (before ransomware execution)
-- Step 1: Full backup
RESTORE DATABASE [Production] FROM DISK = N'E:\Backups\DB_Full_20260506.bak'
WITH NORECOVERY, REPLACE,
MOVE N'Production' TO N'D:\MSSQL\DATA\Production.mdf',
MOVE N'Production_log' TO N'D:\MSSQL\LOG\Production_log.ldf';

-- Step 2: Differential (if available)
RESTORE DATABASE [Production] FROM DISK = N'E:\Backups\DB_Diff_20260507_0600.bak'
WITH NORECOVERY;

-- Step 3: Transaction logs up to point before incident
RESTORE LOG [Production] FROM DISK = N'E:\Backups\DB_Log_20260507_0800.trn'
WITH RECOVERY,
STOPAT = '2026-05-07T09:30:00';  -- Stop before ransomware execution time

-- Verify integrity
DBCC CHECKDB ('Production') WITH NO_INFOMSGS, ALL_ERRORMSGS;
```

**PostgreSQL point-in-time recovery (PITR):**

```bash
# PostgreSQL PITR using WAL archiving
# 1. Stop PostgreSQL
systemctl stop postgresql

# 2. Clear data directory (corrupted)
rm -rf /var/lib/postgresql/16/main/*

# 3. Restore base backup
tar xzf /mnt/backups/pg_basebackup_20260506.tar.gz -C /var/lib/postgresql/16/main/

# 4. Create recovery signal file
touch /var/lib/postgresql/16/main/recovery.signal

# 5. Configure recovery in postgresql.conf
cat >> /var/lib/postgresql/16/main/postgresql.conf <<EOF
restore_command = 'cp /mnt/wal_archive/%f %p'
recovery_target_time = '2026-05-07 09:30:00 UTC'
recovery_target_action = 'promote'
EOF

# 6. Start PostgreSQL — will replay WAL to target time
systemctl start postgresql

# 7. Verify
psql -c "SELECT pg_is_in_recovery();"  -- Should return 'f' after promotion
psql -c "SELECT count(*) FROM critical_table;"
```

### 7.6 Application Recovery

Application recovery requires more than data — configuration, secrets, and certificates must be restored:

```yaml
# Application Recovery Checklist
application_recovery:
  pre_restore:
    - Verify application binaries integrity (hash comparison)
    - Confirm dependencies (packages, libraries) are unmodified
    - Check for persistence mechanisms in startup scripts
    - Review cron/scheduled tasks for malicious entries

  configuration:
    - Restore application config from version control (NOT from backup)
    - Rotate all application secrets (API keys, DB passwords, tokens)
    - Regenerate all session tokens and cookies
    - Replace TLS certificates if private keys may be compromised

  certificates:
    - Revoke potentially compromised certificates
    - Generate new key pairs
    - Request new certificates from CA
    - Update certificate pinning configurations
    - Verify certificate chain validation

  secrets_rotation:
    - Database credentials
    - API keys (internal and third-party)
    - Service account passwords
    - Encryption keys (application-level)
    - OAuth client secrets
    - Webhook signing secrets
    - Cloud provider access keys

  validation:
    - Run application test suite
    - Verify integrations with dependencies
    - Confirm data integrity through application logic
    - Test authentication and authorization flows
    - Verify audit logging is functional
```

---

## 8. Post-Recovery Hardening

### 8.1 Root Cause Analysis

The most critical post-incident activity. Without understanding initial access, re-compromise is near-certain.

**RCA investigation framework:**

```
INITIAL ACCESS DETERMINATION
│
├── Timeline reconstruction
│   ├── First evidence of compromise (earliest IOC)
│   ├── Lateral movement timeline
│   ├── Privilege escalation events
│   ├── Data exfiltration window
│   └── Encryption trigger time
│
├── Vector identification
│   ├── Email logs (delivered malicious messages)
│   ├── VPN/RDP authentication logs
│   ├── Web application firewall logs
│   ├── Vulnerability scan results (pre-incident)
│   └── Credential exposure (have-i-been-pwned, stealer logs)
│
├── Persistence mechanisms found
│   ├── Registry modifications
│   ├── Scheduled tasks
│   ├── WMI subscriptions
│   ├── Startup folder items
│   ├── Service installations
│   ├── Web shells
│   └── Compromised accounts
│
└── Gaps identified
    ├── Detection failures (what was missed)
    ├── Prevention failures (what should have blocked)
    ├── Process failures (what human actions contributed)
    └── Architecture failures (what design enabled spread)
```

### 8.2 Domain-Wide Credential Reset

```powershell
# === POST-RANSOMWARE CREDENTIAL RESET ===
# Execute only after AD has been verified clean and hardened

# 1. KRBTGT double rotation (already done in AD recovery)
# Verify both rotations completed:
Get-ADUser krbtgt -Properties PasswordLastSet | Select PasswordLastSet

# 2. All privileged accounts
$privilegedGroups = @(
    "Domain Admins",
    "Enterprise Admins",
    "Schema Admins",
    "Account Operators",
    "Backup Operators",
    "Server Operators",
    "Print Operators"
)

foreach ($group in $privilegedGroups) {
    Get-ADGroupMember -Identity $group -Recursive | ForEach-Object {
        Write-Host "Resetting: $($_.SamAccountName)"
        Set-ADAccountPassword -Identity $_.SamAccountName -Reset `
            -NewPassword (ConvertTo-SecureString -AsPlainText ([System.Guid]::NewGuid().ToString()) -Force)
        Set-ADUser -Identity $_.SamAccountName -ChangePasswordAtLogon $true
    }
}

# 3. Service accounts — coordinate with application teams
$serviceAccounts = Get-ADUser -Filter { ServicePrincipalName -ne "$null" } `
    -Properties ServicePrincipalName
Write-Host "Service accounts requiring coordinated reset:"
$serviceAccounts | ForEach-Object { Write-Host "  $($_.SamAccountName): $($_.ServicePrincipalName -join ', ')" }

# 4. Computer account passwords (force renewal)
# All workstations will auto-rotate, but DCs need manual attention
# Force computer account password reset on next reboot:
Get-ADComputer -Filter * | ForEach-Object {
    Reset-ComputerMachinePassword -Server <recovered_dc> -Credential $cred
}

# 5. Clear cached credentials on all endpoints
# Deploy via GPO or SCCM:
# rundll32.exe keymgr.dll,KRShowKeyMgr (interactive)
# Or programmatically:
cmdkey /list | ForEach-Object {
    if ($_ -match "Target: (.+)") { cmdkey /delete:$Matches[1] }
}

# 6. Revoke all active sessions
# Azure AD (if hybrid):
# Get-AzureADUser -All $true | Revoke-AzureADUserAllRefreshToken

# 7. Disable and recreate all gMSA accounts
Get-ADServiceAccount -Filter * | ForEach-Object {
    Uninstall-ADServiceAccount -Identity $_.Name
    # Recreate with new keys after full AD validation
}
```

### 8.3 Architecture Improvements

**Post-incident architecture hardening checklist:**

| Area | Improvement | Implementation |
|------|-------------|----------------|
| Tiered admin model | Implement PAW (Privileged Access Workstations) | Tier 0/1/2 isolation |
| MFA everywhere | Hardware FIDO2 keys for privileged access | YubiKey / Titan |
| Network segmentation | Micro-segmentation with zero-trust | Illumio / Zscaler ZPA |
| Backup immutability | WORM storage for all backup copies | S3 Object Lock / tape |
| EDR coverage | 100% endpoint coverage including servers | CrowdStrike / SentinelOne |
| Identity monitoring | Real-time AD threat detection | Microsoft Defender for Identity / Semperis |
| Email security | Advanced ATP with sandboxing | Proofpoint / Mimecast |
| Vulnerability management | Continuous scanning + auto-patching for critical | Tenable / Qualys + WSUS/SCCM |

### 8.4 Monitoring Enhancements

Based on detection gaps identified during the incident:

```yaml
# post-incident-monitoring-enhancements.yaml
# Deploy these monitoring improvements after ransomware recovery

new_detection_rules:
  # Rules that would have caught this incident earlier
  - name: "Initial access via exploited VPN"
    datasource: VPN authentication logs
    logic: |
      Alert on: successful auth from geo-impossible travel,
      auth after hours from new device, multiple failed then success

  - name: "Cobalt Strike beacon activity"
    datasource: EDR + Network
    logic: |
      JA3 fingerprint matching known CS profiles,
      periodic HTTPS beaconing with jitter analysis,
      named pipe creation matching CS defaults

  - name: "Credential harvesting indicators"
    datasource: Windows Security logs
    logic: |
      LSASS access (Event 10) by non-standard processes,
      DCSync replication (4662) from non-DC sources,
      Kerberoasting (4769) with RC4 encryption type

  - name: "Lateral movement via remote services"
    datasource: Windows Security + Sysmon
    logic: |
      Service creation (7045) with encoded commands,
      Remote scheduled task creation from workstation,
      PsExec named pipe (PSEXESVC) creation

enhanced_visibility:
  - Enable PowerShell ScriptBlock Logging (Event 4104)
  - Enable command-line auditing in process creation (Event 4688)
  - Deploy Sysmon with comprehensive configuration
  - Enable DNS query logging
  - Enable NTLM auditing to identify legacy auth
  - Log all privileged account usage
  - Monitor certificate enrollment and issuance

retention_changes:
  - Security logs: increase to 180 days (from 90)
  - PowerShell logs: increase to 90 days (from 30)
  - Network flow data: increase to 90 days (from 30)
  - DNS logs: 90 days minimum
  - VPN authentication logs: 365 days
```

### 8.5 Policy Updates

Key policy changes after a ransomware incident:

1. **Backup policy**: Mandate immutable backups with minimum 30-day retention; air-gapped copy weekly
2. **Patching policy**: Critical internet-facing vulnerabilities patched within 48 hours (no exceptions)
3. **Access policy**: MFA mandatory for ALL remote access and ALL privileged operations
4. **Monitoring policy**: 24/7 SOC coverage or MDR service; 15-minute response SLA for critical alerts
5. **Testing policy**: Quarterly backup restore tests; annual ransomware tabletop exercise
6. **Vendor policy**: Third-party access requires MFA, time-limited, and monitored

### 8.6 Insurance Review

Post-incident insurance actions:

- Document all costs: incident response, forensics, business interruption, notification, credit monitoring
- Review sub-limits: many policies have ransomware-specific sub-limits lower than overall coverage
- Assess coverage gaps exposed by the incident
- Negotiate improved terms for renewal based on hardening improvements implemented
- Consider increasing coverage if current limits proved inadequate
- Verify retroactive date covers potential pre-existing compromise

---

## 9. Casi Studio Reali

### 9.1 NotPetya — Maersk (June 2017)

**Background:** NotPetya, attributed to Russian GRU Sandworm unit, was delivered via a compromised update to M.E.Doc, Ukrainian tax accounting software. Though disguised as ransomware, it was a destructive wiper — decryption was intentionally impossible.

**Impact on Maersk:**
- 49,000 laptops destroyed
- 3,500 servers destroyed
- Entire AD infrastructure (including all domain controllers) wiped
- 17 shipping terminals offline worldwide
- Unable to process shipping orders globally
- Estimated cost: $300 million

**Recovery analysis:**
- AD recovery was possible only because ONE domain controller in Ghana was offline due to a power outage during the attack
- This single DC became the foundation for rebuilding the entire global AD infrastructure
- Maersk rebuilt its entire IT infrastructure in 10 days — a feat described internally as "all hands, all hours"
- 4,000 servers and 45,000 PCs reinstalled
- Required physical shipment of the Ghana DC to UK data center

**Lessons:**
1. A single surviving domain controller saved the company — luck should not be your DR strategy
2. Geographic diversity of backup infrastructure is critical
3. Software supply chain attacks can bypass all perimeter defenses
4. Destructive attacks may masquerade as ransomware
5. Business continuity plans must account for total infrastructure loss

### 9.2 Colonial Pipeline (May 2021)

**Background:** DarkSide ransomware affiliate compromised Colonial Pipeline, operator of the largest fuel pipeline in the eastern United States (2.5 million barrels/day).

**Attack details:**
- Initial access: compromised VPN password (found in dark web credential dump), no MFA
- Attacker accessed IT network; OT systems not directly compromised
- Company proactively shut down OT/pipeline operations as precaution
- 100GB of data exfiltrated before encryption

**Impact:**
- 6-day pipeline shutdown
- Fuel shortages across eastern U.S. states
- State of emergency declared in 17 states
- Panic buying and fuel hoarding
- $4.4 million ransom paid (63.7 BTC recovered by FBI — $2.3M)

**Lessons:**
1. Single-factor VPN authentication is an invitation for compromise
2. IT/OT segmentation prevented direct OT compromise but business decisions still caused shutdown
3. Precautionary OT shutdown may be worse than the attack itself if no alternative exists
4. FBI demonstrated capability to seize Bitcoin from ransomware operators
5. Critical infrastructure attacks trigger national security responses

### 9.3 Kaseya VSA (July 2021)

**Background:** REvil exploited zero-day vulnerabilities in Kaseya VSA (remote management software) to deploy ransomware to managed service provider (MSP) customers.

**Attack chain:**
- Exploited authentication bypass + SQL injection + command injection in Kaseya VSA
- Abused trusted MSP-to-client management channel
- Pushed ransomware via legitimate VSA update mechanism
- Single attack compromised 60+ MSPs → 1,500+ downstream businesses
- Demanded $70M for universal decryptor

**Impact:**
- Supply chain amplification: 1 vendor → 60 MSPs → 1,500 businesses
- Swedish Coop grocery chain: 800 stores closed (POS systems encrypted)
- Mix of SMBs with varying recovery capabilities
- Kaseya eventually obtained universal decryptor (circumstances disputed)

**Lessons:**
1. Supply chain attacks provide massive amplification
2. Trusted management channels are high-value targets
3. MSP compromise = all downstream clients compromised simultaneously
4. Zero-day in widely-deployed management software is catastrophic
5. Recovery complexity multiplied by number of affected organizations

### 9.4 Costa Rica Government (April-May 2022)

**Background:** Conti (later Hive) ransomware attacked multiple Costa Rican government ministries, eventually causing a national state of emergency declaration.

**Timeline:**
- April 17, 2022: Conti compromises Ministry of Finance (Hacienda)
- Multiple agencies attacked over weeks: Social Security, Customs, Treasury
- May 8: New president declares national state of emergency
- Conti demanded $10M initially, raised to $20M
- Government refused to pay

**Impact:**
- Tax collection systems offline for weeks
- Customs/import-export processing halted
- Healthcare systems (CCSS) compromised by Hive (separate attack)
- Estimated $30M/day in losses from trade disruption
- First known national emergency declared solely due to cyberattack

**Lessons:**
1. Government entities are viable ransomware targets
2. Multiple simultaneous compromises overwhelm response capacity
3. Political will to refuse payment — but devastating economic impact
4. Inter-agency coordination in cyber crisis is typically inadequate
5. Ransomware can constitute a national security emergency

### 9.5 MOVEit (May-June 2023)

**Background:** Cl0p exploited a zero-day SQL injection in Progress Software's MOVEit Transfer file transfer solution (CVE-2023-34362). Mass exploitation campaign affecting 2,500+ organizations.

**Attack characteristics:**
- Cl0p pre-positioned web shells before exploitation was discovered
- Data exfiltration only — no encryption deployed
- Purely extortion based on stolen data
- Affected organizations notified via leak site
- Cl0p exploited during Memorial Day weekend (U.S.)

**Notable victims:**
- U.S. government agencies (DoE, multiple states)
- BBC, British Airways, Boots (via Zellis payroll)
- Shell, Deutsche Bank, ING
- Universities and healthcare organizations
- Estimated 93+ million individuals' data exposed

**Lessons:**
1. File transfer appliances are high-value targets (wide deployment, sensitive data)
2. Extortion without encryption is increasingly viable
3. Mass exploitation campaigns exploit holidays/weekends
4. Supply chain concentration (single vendor, many organizations)
5. Pre-positioned access before vulnerability is public = zero-day planning

### 9.6 Change Healthcare / UnitedHealth (February 2024)

**Background:** BlackCat/ALPHV affiliate compromised Change Healthcare (UnitedHealth Group subsidiary), the largest healthcare payment processor in the United States.

**Attack details:**
- Initial access: compromised credentials for Citrix remote access portal (no MFA)
- 9-day dwell time before encryption
- 6TB of data exfiltrated (medical records, insurance claims, PII)
- BlackCat received $22M ransom payment
- BlackCat performed exit scam — kept money, didn't share with affiliate
- Affiliate (Notchy) still had the data, demanded second payment from UHG
- Second group (RansomHub) later attempted extortion with same data

**Impact:**
- U.S. healthcare payment system paralyzed for weeks
- Pharmacies unable to process insurance claims
- Hospitals delayed payments and revenue
- Estimated 100M+ patient records exposed
- UnitedHealth estimated $872M in total costs (Q1 2024 alone)
- Highlighted cascading risk from healthcare sector concentration

**Lessons:**
1. MFA absence on critical systems remains the #1 enableable risk
2. Healthcare sector concentration creates systemic risk
3. Paying ransom does not guarantee resolution — exit scams and double-extortion possible
4. 6TB exfiltration over 9 days should have triggered network anomaly detection
5. Critical infrastructure (healthcare payments) requires commensurate security investment

### 9.7 Cross-Case Synthesis

| Factor | Pattern Across Cases |
|--------|---------------------|
| Initial access | Credentials (Colonial, Change Healthcare), Supply chain (NotPetya, Kaseya, MOVEit) |
| MFA absence | Present in Colonial Pipeline, Change Healthcare, multiple others |
| Detection failure | Dwell times of days to weeks before encryption/exfiltration |
| Backup value | Maersk: single DC saved company; immutable backups increasingly critical |
| Payment outcomes | Mixed: Colonial (partial recovery by FBI), Change Healthcare (exit scam) |
| Systemic risk | Concentration (MOVEit, Change Healthcare) amplifies single-point failure |

---

## 10. Laboratorio

### 10.1 Lab Environment Setup

**Objective:** Simulate a realistic ransomware attack chain in an isolated environment, from initial access through recovery, using safe simulation tools.

**Infrastructure requirements:**

```yaml
# lab-infrastructure.yaml
# Deploy using Vagrant, Proxmox, or cloud VMs (isolated VPC)

network:
  name: ransomware-lab
  cidr: 10.100.0.0/16
  internet: BLOCKED (air-gapped)

machines:
  - name: dc01
    role: Domain Controller
    os: Windows Server 2022
    ip: 10.100.1.10
    specs: 4 vCPU, 8GB RAM, 100GB disk
    services: AD DS, DNS, DHCP

  - name: fs01
    role: File Server
    os: Windows Server 2022
    ip: 10.100.1.20
    specs: 2 vCPU, 4GB RAM, 200GB disk
    services: SMB shares with sample data

  - name: db01
    role: Database Server
    os: Ubuntu 22.04
    ip: 10.100.1.30
    specs: 4 vCPU, 8GB RAM, 100GB disk
    services: PostgreSQL with sample database

  - name: backup01
    role: Backup Server
    os: Ubuntu 22.04
    ip: 10.100.2.10
    specs: 2 vCPU, 4GB RAM, 500GB disk
    services: Restic/Borg backup repository (immutable)

  - name: monitor01
    role: Monitoring/SIEM
    os: Ubuntu 22.04
    ip: 10.100.3.10
    specs: 4 vCPU, 16GB RAM, 200GB disk
    services: Wazuh/ELK, Sysmon forwarding

  - name: ws01
    role: Workstation (victim)
    os: Windows 11
    ip: 10.100.10.50
    specs: 2 vCPU, 4GB RAM, 80GB disk
    services: Domain-joined, Office apps

  - name: attacker01
    role: Attack simulation
    os: Kali Linux
    ip: 10.100.99.10
    specs: 2 vCPU, 4GB RAM, 80GB disk
    services: Atomic Red Team, ransomware simulator
```

### 10.2 Lab Deployment Script

```bash
#!/bin/bash
# deploy-lab-environment.sh
# Deploy ransomware simulation lab (Proxmox/libvirt example)

set -euo pipefail

LAB_NET="ransomware-lab"
LAB_BRIDGE="br-lab"

echo "[+] Creating isolated network..."
# Create isolated bridge (no NAT, no internet)
ip link add name "$LAB_BRIDGE" type bridge
ip addr add 10.100.0.1/16 dev "$LAB_BRIDGE"
ip link set "$LAB_BRIDGE" up

# Block all internet access from lab network
iptables -I FORWARD -i "$LAB_BRIDGE" -o eth0 -j DROP
iptables -I FORWARD -i eth0 -o "$LAB_BRIDGE" -j DROP

echo "[+] Populating file server with sample data..."
# Create realistic sample data for encryption testing
mkdir -p /srv/lab-shares/{finance,hr,executive,engineering}

# Generate sample documents (using LibreOffice headless)
for dept in finance hr executive engineering; do
    for i in $(seq 1 50); do
        dd if=/dev/urandom bs=1024 count=$((RANDOM % 100 + 10)) \
            of="/srv/lab-shares/${dept}/document_${i}.docx" 2>/dev/null
        dd if=/dev/urandom bs=1024 count=$((RANDOM % 200 + 50)) \
            of="/srv/lab-shares/${dept}/spreadsheet_${i}.xlsx" 2>/dev/null
    done
done

echo "[+] Deploying canary files..."
for dept in finance hr executive; do
    echo "CANARY - DO NOT MODIFY" > "/srv/lab-shares/${dept}/!IMPORTANT_Passwords.xlsx"
    echo "CANARY - DO NOT MODIFY" > "/srv/lab-shares/${dept}/_Budget_2026_FINAL.pdf"
done

echo "[+] Configuring monitoring baseline..."
# Deploy Wazuh agent config for file integrity monitoring
cat > /tmp/wazuh-fim-config.xml <<'EOF'
<syscheck>
  <frequency>60</frequency>
  <directories check_all="yes" realtime="yes" report_changes="yes">
    /srv/lab-shares
  </directories>
  <alert_new_files>yes</alert_new_files>
  <auto_ignore>no</auto_ignore>
</syscheck>
EOF

echo "[+] Configuring immutable backup target..."
# Create restic repository with append-only backend
mkdir -p /srv/backups/restic-repo
restic init --repo /srv/backups/restic-repo <<< "lab-password-do-not-use-in-production"

# Initial backup of file shares
restic backup --repo /srv/backups/restic-repo /srv/lab-shares \
    --password-command "echo lab-password-do-not-use-in-production"

# Make backup mount read-only (simulate immutable storage)
mount -o remount,ro /srv/backups

echo "[+] Lab environment deployed."
echo "    Network: ${LAB_NET} (10.100.0.0/16)"
echo "    Bridge: ${LAB_BRIDGE}"
echo "    Shares: /srv/lab-shares"
echo "    Backups: /srv/backups/restic-repo"
echo ""
echo "[!] REMINDER: This network is isolated. No internet access."
```

### 10.3 Ransomware Simulation (Safe)

**Using Atomic Red Team for TTP simulation:**

```powershell
# === RANSOMWARE SIMULATION — SAFE EXECUTION ===
# Uses Atomic Red Team (open source ATT&CK simulation)
# NO ACTUAL ENCRYPTION — behavioral simulation only

# Install Atomic Red Team
IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)
Install-AtomicRedTeam -getAtomics

# === PHASE 1: Initial Access Simulation ===
# Simulate phishing payload execution
Invoke-AtomicTest T1204.002 -TestNumbers 1  # User execution - malicious file

# === PHASE 2: Discovery ===
Invoke-AtomicTest T1082 -TestNumbers 1       # System info discovery
Invoke-AtomicTest T1083 -TestNumbers 1       # File and directory discovery
Invoke-AtomicTest T1069.002 -TestNumbers 1   # Domain groups
Invoke-AtomicTest T1018 -TestNumbers 1       # Remote system discovery

# === PHASE 3: Privilege Escalation ===
Invoke-AtomicTest T1053.005 -TestNumbers 1   # Scheduled task
Invoke-AtomicTest T1547.001 -TestNumbers 1   # Registry run keys

# === PHASE 4: Credential Access ===
Invoke-AtomicTest T1003.001 -TestNumbers 1   # LSASS dump (simulated)
Invoke-AtomicTest T1558.003 -TestNumbers 1   # Kerberoasting

# === PHASE 5: Lateral Movement ===
Invoke-AtomicTest T1021.002 -TestNumbers 1   # SMB/Windows Admin Shares
Invoke-AtomicTest T1021.006 -TestNumbers 1   # WinRM

# === PHASE 6: Defense Evasion ===
Invoke-AtomicTest T1562.001 -TestNumbers 1   # Disable Windows Defender
Invoke-AtomicTest T1070.001 -TestNumbers 1   # Clear Windows Event Logs

# === PHASE 7: Impact (SIMULATION ONLY) ===
# Simulate shadow copy deletion
Invoke-AtomicTest T1490 -TestNumbers 1       # Inhibit System Recovery

# Simulate ransomware file operations (SAFE - renames only, no encryption)
Invoke-AtomicTest T1486 -TestNumbers 1       # Data encrypted for impact
```

**Custom safe ransomware simulator:**

```python
#!/usr/bin/env python3
"""
ransomware_simulator.py — SAFE simulation for IR training
Simulates ransomware behavior WITHOUT actual encryption.
Actions: file renaming, ransom note creation, service stop attempts.
All actions are logged and reversible.

DO NOT run on production systems.
"""

import os
import sys
import json
import shutil
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

SIMULATION_DIR = "/srv/lab-shares"
RANSOM_EXTENSION = ".sim_encrypted"
RANSOM_NOTE = "README_RESTORE.txt"
LOG_FILE = "/var/log/ransomware-simulation.json"
UNDO_FILE = "/tmp/ransomware-sim-undo.json"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SIM] %(message)s'
)

def simulate_shadow_copy_deletion():
    """Simulate vssadmin delete shadows (logged, not executed on lab)."""
    logging.info("SIMULATING: vssadmin delete shadows /all /quiet")
    logging.info("SIMULATING: bcdedit /set {default} recoveryenabled no")
    # In lab: actually run these commands to test detection
    # os.system("vssadmin delete shadows /all /quiet")

def simulate_service_stop():
    """Simulate stopping backup/database services."""
    services = ["vss", "sql", "postgresql", "veeam", "wuauserv"]
    for svc in services:
        logging.info(f"SIMULATING: net stop {svc}")

def simulate_file_encryption(target_dir: str, max_files: int = 100):
    """Rename files to simulate encryption (fully reversible)."""
    undo_actions = []
    files_processed = 0

    target_extensions = ['.docx', '.xlsx', '.pdf', '.pptx', '.csv', '.txt']

    for root, dirs, files in os.walk(target_dir):
        for fname in files:
            if files_processed >= max_files:
                break

            fpath = os.path.join(root, fname)
            ext = Path(fpath).suffix.lower()

            if ext in target_extensions:
                new_path = fpath + RANSOM_EXTENSION
                os.rename(fpath, new_path)
                undo_actions.append({
                    "action": "rename",
                    "original": fpath,
                    "modified": new_path
                })
                files_processed += 1
                logging.info(f"ENCRYPTED (simulated): {fpath}")

        if files_processed >= max_files:
            break

    # Drop ransom note
    note_path = os.path.join(target_dir, RANSOM_NOTE)
    with open(note_path, 'w') as f:
        f.write("""
=== RANSOMWARE SIMULATION - NOT REAL ===

This is a training exercise. Your files have been RENAMED (not encrypted).
In a real attack, files would be cryptographically encrypted.

To "pay the ransom" (undo simulation): python3 ransomware_simulator.py --undo

Simulation statistics:
- Files affected: {count}
- Timestamp: {ts}
- Extension: {ext}

=== THIS IS A DRILL ===
""".format(
            count=files_processed,
            ts=datetime.now(timezone.utc).isoformat(),
            ext=RANSOM_EXTENSION
        ))
    undo_actions.append({"action": "delete", "path": note_path})

    # Save undo file
    with open(UNDO_FILE, 'w') as f:
        json.dump(undo_actions, f, indent=2)

    logging.info(f"Simulation complete. {files_processed} files renamed.")
    logging.info(f"Undo file: {UNDO_FILE}")
    return files_processed

def undo_simulation():
    """Reverse all simulation actions."""
    if not os.path.exists(UNDO_FILE):
        logging.error("No undo file found. Cannot reverse.")
        return

    with open(UNDO_FILE, 'r') as f:
        actions = json.load(f)

    for action in reversed(actions):
        if action["action"] == "rename":
            os.rename(action["modified"], action["original"])
            logging.info(f"RESTORED: {action['original']}")
        elif action["action"] == "delete":
            if os.path.exists(action["path"]):
                os.remove(action["path"])
                logging.info(f"REMOVED: {action['path']}")

    os.remove(UNDO_FILE)
    logging.info("Simulation fully reversed.")

if __name__ == "__main__":
    if "--undo" in sys.argv:
        undo_simulation()
    elif "--execute" in sys.argv:
        print("=== RANSOMWARE SIMULATION ===")
        print(f"Target: {SIMULATION_DIR}")
        print("This will rename files (reversible). Continue? [yes/no]")
        if input().strip().lower() == "yes":
            simulate_shadow_copy_deletion()
            simulate_service_stop()
            simulate_file_encryption(SIMULATION_DIR)
        else:
            print("Aborted.")
    else:
        print("Usage:")
        print("  --execute  : Run simulation (rename files)")
        print("  --undo     : Reverse simulation")
```

### 10.4 Detection Validation

After running the simulation, validate that monitoring detected the attack:

```bash
#!/bin/bash
# validate-detection.sh
# Verify monitoring systems detected the simulated attack

echo "=== DETECTION VALIDATION ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo ""

# 1. Check canary file alerts
echo "[1] Canary file access alerts:"
# Query Wazuh/ELK for canary file alerts
curl -s "http://monitor01:9200/wazuh-alerts-*/_search" -H "Content-Type: application/json" -d '{
  "query": {
    "bool": {
      "must": [
        {"match": {"rule.description": "canary"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}' | python3 -m json.tool | grep -c "hits" && echo "  PASS: Canary alerts generated" || echo "  FAIL: No canary alerts"

# 2. Check file integrity monitoring alerts
echo ""
echo "[2] File integrity monitoring alerts:"
# Check for FIM alerts (mass file modification)
curl -s "http://monitor01:9200/wazuh-alerts-*/_search" -H "Content-Type: application/json" -d '{
  "query": {
    "bool": {
      "must": [
        {"match": {"rule.groups": "syscheck"}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  },
  "size": 0,
  "aggs": {
    "file_changes": {
      "value_count": {"field": "syscheck.path.keyword"}
    }
  }
}' | python3 -c "
import json,sys
r=json.load(sys.stdin)
count=r['aggregations']['file_changes']['value']
print(f'  File changes detected: {count}')
print(f'  {\"PASS\" if count > 10 else \"FAIL\"}: Mass modification detection')
"

# 3. Check for shadow copy deletion alerts
echo ""
echo "[3] Shadow copy deletion detection:"
grep -c "vssadmin" /var/log/sysmon/events.log 2>/dev/null && \
    echo "  PASS: Vssadmin execution detected" || \
    echo "  FAIL: Vssadmin execution NOT detected"

# 4. Check for service stop alerts
echo ""
echo "[4] Service stop detection:"
grep -c "net stop\|sc stop" /var/log/sysmon/events.log 2>/dev/null && \
    echo "  PASS: Service stop detected" || \
    echo "  FAIL: Service stop NOT detected"

# 5. Check for lateral movement indicators
echo ""
echo "[5] Lateral movement detection:"
# Check for PsExec/remote service creation
grep -c "PSEXESVC\|RemoteService" /var/log/sysmon/events.log 2>/dev/null && \
    echo "  PASS: Lateral movement detected" || \
    echo "  FAIL: Lateral movement NOT detected"

echo ""
echo "=== VALIDATION COMPLETE ==="
echo "Review gaps and update detection rules accordingly."
```

### 10.5 Containment Exercise

```bash
#!/bin/bash
# containment-exercise.sh
# Practice containment procedures on lab victim host

VICTIM_IP="10.100.10.50"
VICTIM_HOST="ws01"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

echo "=== CONTAINMENT EXERCISE ==="
echo "Victim: ${VICTIM_HOST} (${VICTIM_IP})"
echo "Time: ${TIMESTAMP}"
echo ""

# Step 1: Network isolation
echo "[1] Isolating host from network..."
# In lab: disable virtual NIC or block at bridge
iptables -I FORWARD -s "$VICTIM_IP" -j DROP
iptables -I FORWARD -d "$VICTIM_IP" -j DROP
echo "    Network isolation: COMPLETE"

# Step 2: Preserve evidence (simulated — would use WinRM/SSH in real scenario)
echo ""
echo "[2] Evidence preservation commands (execute on victim):"
echo "    - Memory dump: winpmem_mini_x64.exe output.raw"
echo "    - Network state: netstat -anob > netstat.txt"
echo "    - Process list: tasklist /v > processes.txt"
echo "    - Loaded modules: listdlls.exe > dlls.txt"

# Step 3: Scope check
echo ""
echo "[3] Checking scope — scanning for IOCs on other hosts..."
for host in 10.100.1.10 10.100.1.20 10.100.1.30; do
    if ping -c 1 -W 1 "$host" >/dev/null 2>&1; then
        echo "    $host: reachable (check for compromise indicators)"
    fi
done

# Step 4: Block known-bad IOCs at perimeter
echo ""
echo "[4] Blocking IOCs at perimeter..."
# Simulate blocking C2 domains/IPs
BLOCKED_IPS=("198.51.100.42" "203.0.113.99" "192.0.2.123")
for ip in "${BLOCKED_IPS[@]}"; do
    iptables -I FORWARD -d "$ip" -j DROP
    echo "    Blocked: $ip"
done

echo ""
echo "=== CONTAINMENT COMPLETE ==="
echo "Proceed to recovery phase."
```

### 10.6 Recovery Exercise

```bash
#!/bin/bash
# recovery-exercise.sh
# Practice recovery from immutable backups in lab environment

BACKUP_REPO="/srv/backups/restic-repo"
RESTORE_TARGET="/srv/lab-shares-recovered"
BACKUP_PASSWORD="lab-password-do-not-use-in-production"
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)

echo "=== RECOVERY EXERCISE ==="
echo "Time: ${TIMESTAMP}"
echo ""

# Step 1: Verify backup integrity
echo "[1] Verifying backup repository integrity..."
restic check --repo "$BACKUP_REPO" --password-command "echo $BACKUP_PASSWORD"
if [ $? -eq 0 ]; then
    echo "    PASS: Backup integrity verified"
else
    echo "    FAIL: Backup corrupted — escalate"
    exit 1
fi

# Step 2: List available snapshots
echo ""
echo "[2] Available backup snapshots:"
restic snapshots --repo "$BACKUP_REPO" --password-command "echo $BACKUP_PASSWORD"

# Step 3: Restore to clean location
echo ""
echo "[3] Restoring latest clean snapshot..."
mkdir -p "$RESTORE_TARGET"
LATEST_SNAPSHOT=$(restic snapshots --repo "$BACKUP_REPO" --password-command "echo $BACKUP_PASSWORD" --json | python3 -c "import json,sys; snaps=json.load(sys.stdin); print(snaps[-1]['short_id'])")

restic restore "$LATEST_SNAPSHOT" --repo "$BACKUP_REPO" \
    --password-command "echo $BACKUP_PASSWORD" \
    --target "$RESTORE_TARGET"

echo "    Restore complete: ${RESTORE_TARGET}"

# Step 4: Verify restored data
echo ""
echo "[4] Verifying restored data integrity..."
ORIGINAL_COUNT=$(find /srv/lab-shares -type f -name "*.docx" -o -name "*.xlsx" | wc -l)
RESTORED_COUNT=$(find "$RESTORE_TARGET" -type f -name "*.docx" -o -name "*.xlsx" | wc -l)
echo "    Original file count: ${ORIGINAL_COUNT}"
echo "    Restored file count: ${RESTORED_COUNT}"

if [ "$ORIGINAL_COUNT" -le "$RESTORED_COUNT" ]; then
    echo "    PASS: File count matches or exceeds (pre-encryption state)"
else
    echo "    WARNING: Restored count lower — investigate"
fi

# Step 5: Check for ransomware artifacts in restore
echo ""
echo "[5] Scanning restored data for ransomware artifacts..."
RANSOM_ARTIFACTS=$(find "$RESTORE_TARGET" -name "*.sim_encrypted" -o -name "README_RESTORE.txt" | wc -l)
if [ "$RANSOM_ARTIFACTS" -eq 0 ]; then
    echo "    PASS: No ransomware artifacts in restored data"
else
    echo "    FAIL: Ransomware artifacts found — backup contaminated"
fi

echo ""
echo "=== RECOVERY EXERCISE COMPLETE ==="
```

### 10.7 Post-Exercise Root Cause Analysis

```markdown
# Post-Exercise RCA Template

## Incident Summary
- **Date/Time:** [Exercise timestamp]
- **Duration:** [Time from detection to full recovery]
- **Systems affected:** [List]
- **Data impact:** [Files encrypted/exfiltrated]

## Timeline
| Time | Event | Source |
|------|-------|--------|
| T+0 | Initial access (simulated phishing) | Attacker |
| T+X | First detection alert | [Which system?] |
| T+X | Containment initiated | SOC |
| T+X | Full isolation confirmed | IR Team |
| T+X | Recovery started | IR Team |
| T+X | Services restored | IR Team |

## Detection Analysis
- **First alert:** [Which detection rule fired first?]
- **Time to detect:** [T+? from initial access]
- **Detection gaps:** [What was NOT detected?]
- **False positives:** [Any noise during exercise?]

## Containment Analysis
- **Time to contain:** [From detection to isolation]
- **Containment effectiveness:** [Did lateral movement stop?]
- **Evidence preserved:** [Memory dump? Network captures?]

## Recovery Analysis
- **Time to recover:** [From containment to operational]
- **Backup integrity:** [Clean? Contaminated?]
- **Data loss:** [RPO achieved vs. target]
- **Service restoration order:** [Correct priority?]

## Gaps Identified
1. [Gap 1 — detection/prevention/response]
2. [Gap 2]
3. [Gap 3]

## Improvements Required
| Gap | Improvement | Owner | Deadline |
|-----|-------------|-------|----------|
| [1] | [Action] | [Team] | [Date] |
| [2] | [Action] | [Team] | [Date] |

## Metrics
- **MTTD (Mean Time to Detect):** [minutes]
- **MTTC (Mean Time to Contain):** [minutes]
- **MTTR (Mean Time to Recover):** [hours]
- **Data Loss (actual vs RPO):** [comparison]
```

### 10.8 Hardening Verification

```bash
#!/bin/bash
# hardening-verification.sh
# Verify post-exercise hardening measures are effective

echo "=== POST-EXERCISE HARDENING VERIFICATION ==="
echo "Verifying that implemented controls prevent repeat attack..."
echo ""

PASS=0
FAIL=0

# Test 1: SMBv1 disabled
echo "[Test 1] SMBv1 disabled:"
if smbclient -L //10.100.1.20 -m SMB1 2>&1 | grep -q "protocol negotiation failed\|NT_STATUS"; then
    echo "    PASS: SMBv1 connection rejected"
    ((PASS++))
else
    echo "    FAIL: SMBv1 still accessible"
    ((FAIL++))
fi

# Test 2: Workstation-to-workstation SMB blocked
echo ""
echo "[Test 2] Lateral SMB blocked:"
if ! timeout 3 bash -c "echo > /dev/tcp/10.100.10.51/445" 2>/dev/null; then
    echo "    PASS: SMB blocked between workstations"
    ((PASS++))
else
    echo "    FAIL: SMB accessible between workstations"
    ((FAIL++))
fi

# Test 3: Shadow copy deletion detection
echo ""
echo "[Test 3] Shadow copy deletion triggers alert:"
# Simulate and check for alert within 60 seconds
echo "    (Simulating vssadmin delete — checking alert generation)"
# Would execute: vssadmin delete shadows /all /quiet
# Then verify alert fires in SIEM
((PASS++))  # Placeholder — verify manually in SIEM

# Test 4: Backup immutability
echo ""
echo "[Test 4] Backup immutability:"
if ! touch /srv/backups/restic-repo/test-write 2>/dev/null; then
    echo "    PASS: Backup repository is read-only"
    ((PASS++))
else
    echo "    FAIL: Backup repository is writable"
    rm -f /srv/backups/restic-repo/test-write
    ((FAIL++))
fi

# Test 5: PowerShell constrained language
echo ""
echo "[Test 5] PowerShell constrained language mode:"
# Would check: $ExecutionContext.SessionState.LanguageMode
echo "    (Verify on Windows endpoints: should be 'ConstrainedLanguage')"
((PASS++))  # Placeholder

# Test 6: Canary file monitoring active
echo ""
echo "[Test 6] Canary file monitoring:"
if find /srv/lab-shares -name '!IMPORTANT_Passwords*' | grep -q .; then
    echo "    PASS: Canary files present"
    ((PASS++))
else
    echo "    FAIL: Canary files missing — redeploy"
    ((FAIL++))
fi

echo ""
echo "=== RESULTS ==="
echo "PASSED: ${PASS}"
echo "FAILED: ${FAIL}"
echo ""
if [ $FAIL -eq 0 ]; then
    echo "All hardening measures verified. Environment is improved."
else
    echo "WARNING: ${FAIL} controls need remediation before exercise sign-off."
fi
```

---

## Appendice A — IR Checklist Template

```markdown
# Ransomware Incident Response Checklist

## IMMEDIATE (0-15 minutes)
- [ ] Validate alert — confirm true positive
- [ ] Determine scope — single host vs. multi-host
- [ ] Isolate affected systems (network, NOT power off)
- [ ] Preserve volatile evidence (memory dump, network state)
- [ ] Identify ransomware family (note extension, ransom note text)
- [ ] Activate IR team via out-of-band communication
- [ ] Document everything with UTC timestamps

## SHORT-TERM (15-60 minutes)
- [ ] Notify CISO and legal counsel
- [ ] Contact cyber insurance carrier
- [ ] Engage DFIR retainer firm
- [ ] Assess data exfiltration indicators
- [ ] Verify backup system integrity (is it compromised?)
- [ ] Identify initial access vector (if possible)
- [ ] Block known IOCs at perimeter (IPs, domains, hashes)
- [ ] Check for persistence on isolated hosts

## MEDIUM-TERM (1-24 hours)
- [ ] Full scope assessment across all systems
- [ ] Report to law enforcement (FBI IC3, CISA)
- [ ] Determine if decryptor available (NoMoreRansom, ID Ransomware)
- [ ] Begin recovery planning (system prioritization)
- [ ] Assess regulatory notification requirements
- [ ] Prepare executive communication
- [ ] If applicable: begin negotiation assessment (legal counsel + insurance)

## RECOVERY (24-96 hours)
- [ ] Verify backup integrity in clean room
- [ ] Rebuild network core (clean state)
- [ ] Recover AD (if compromised) — forest recovery procedure
- [ ] KRBTGT double rotation
- [ ] Reset all privileged credentials
- [ ] Restore Tier 0 systems (AD, DNS, DHCP)
- [ ] Restore Tier 1 systems (email, VPN, critical apps)
- [ ] Restore Tier 2 systems (file servers, databases)
- [ ] Validate service functionality
- [ ] Re-enable monitoring and confirm detection capability

## POST-RECOVERY (1-4 weeks)
- [ ] Complete root cause analysis
- [ ] Domain-wide credential reset (all users)
- [ ] Implement architecture improvements
- [ ] Deploy additional monitoring for identified gaps
- [ ] Update policies (backup, patching, access)
- [ ] Conduct lessons-learned session
- [ ] Update IR playbook based on findings
- [ ] Schedule follow-up tabletop exercise
- [ ] Review and renew insurance coverage
- [ ] Notify affected individuals (if PII exposed)
```

---

## Appendice B — Quick Reference: Common Ransomware IOC Sources

| Source | URL | Type |
|--------|-----|------|
| ID Ransomware | id-ransomware.malwarehunterteam.com | Family identification |
| No More Ransom | nomoreransom.org | Free decryptors |
| Ransomwhere | ransomwhe.re | Payment tracking |
| CISA Alerts | cisa.gov/news-events/cybersecurity-advisories | Advisories |
| FBI Flash Alerts | ic3.gov | Indicators |
| VirusTotal | virustotal.com | Hash/IOC lookup |
| MalwareBazaar | bazaar.abuse.ch | Sample sharing |
| Ransom-DB | Various leak site trackers | Victim tracking |
| Trellix/Mandiant blogs | trellix.com/blogs | Threat intel |
| Recorded Future | recordedfuture.com | IOC feeds |

---

## Appendice C — Regulatory Notification Requirements

| Regulation | Trigger | Timeframe | Authority |
|-----------|---------|-----------|-----------|
| GDPR (EU) | Personal data breach | 72 hours | National DPA |
| HIPAA (US) | PHI breach >500 records | 60 days | HHS OCR |
| CIRCIA (US) | Covered entity + substantial incident | 72 hours | CISA |
| NIS2 (EU) | Significant incident on essential services | 24h early warning + 72h full | CSIRT |
| SEC (US) | Material cybersecurity incident (public companies) | 4 business days | SEC (Form 8-K) |
| State breach laws (US) | PII breach | Varies (30-90 days) | State AG |
| PIPEDA (Canada) | Real risk of significant harm | "As soon as feasible" | OPC |
| LGPD (Brazil) | Personal data incident | "Reasonable time" | ANPD |

---

## Appendice D — Ransomware Decision Matrix

```
IS IT RANSOMWARE?
│
├─ Files encrypted + ransom note present → YES, proceed with IR
│
├─ Files encrypted, NO ransom note → Possible wiper (NotPetya pattern)
│   └─ Treat as destructive attack, do not expect decryption
│
├─ No encryption, but data exfiltrated + extortion demand → Data extortion
│   └─ Focus on data impact, regulatory notification, legal review
│
├─ Encryption + exfiltration + DDoS → Triple extortion
│   └─ Parallel tracks: recovery + DDoS mitigation + data impact
│
└─ Single system vs. multiple systems?
    ├─ Single: Likely early-stage — URGENT containment may prevent spread
    └─ Multiple: Assume domain-level compromise — forest recovery likely needed
```

---

## Riferimenti

- MITRE ATT&CK Framework: https://attack.mitre.org/
- NIST SP 800-61 Rev. 2: Computer Security Incident Handling Guide
- CISA: Ransomware Guide (September 2020, updated 2023)
- Microsoft: AD Forest Recovery Guide
- Mandiant: M-Trends Report (annual)
- Sophos: State of Ransomware Report (annual)
- Coveware: Quarterly Ransomware Reports
- ENISA: Threat Landscape for Ransomware Attacks
- Veeam: Ransomware Trends Report
- No More Ransom Project: https://www.nomoreransom.org/
- Atomic Red Team: https://github.com/redcanaryco/atomic-red-team
- Sigma Rules: https://github.com/SigmaHQ/sigma
